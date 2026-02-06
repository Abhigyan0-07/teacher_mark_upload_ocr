from datetime import timedelta

from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from pymongo.database import Database

from ..auth.dependencies import authenticate_user, get_current_active_user, require_admin
from ..auth.security import create_access_token, get_password_hash
from ..database import get_db
from ..schemas.auth import Token, UserCreate, UserOut

router = APIRouter()


def _user_doc_to_out(doc: dict) -> UserOut:
    return UserOut(
        id=str(doc["_id"]),
        username=doc["username"],
        full_name=doc.get("full_name"),
        email=doc["email"],
        role=doc["role"],
        is_active=doc.get("is_active", True),
    )


@router.post("/register", response_model=UserOut)
def register_user(
    payload: UserCreate,
    db: Database = Depends(get_db),
    _: dict = Depends(require_admin),
):
    existing = db["users"].find_one(
        {"$or": [{"username": payload.username}, {"email": payload.email}]}
    )
    if existing:
        raise HTTPException(status_code=400, detail="Username or email already exists")

    user_doc = {
        "username": payload.username,
        "full_name": payload.full_name,
        "email": payload.email,
        "role": payload.role,
        "hashed_password": get_password_hash(payload.password),
        "is_active": True,
    }
    result = db["users"].insert_one(user_doc)
    user_doc["_id"] = result.inserted_id
    return _user_doc_to_out(user_doc)


@router.post("/login", response_model=Token)
def login(
    form_data: OAuth2PasswordRequestForm = Depends(), db: Database = Depends(get_db)
):
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=60)
    access_token = create_access_token(
        data={"sub": user["username"], "role": user.get("role")},
        expires_delta=access_token_expires,
    )
    return Token(access_token=access_token)


@router.get("/me", response_model=UserOut)
def read_users_me(current_user: dict = Depends(get_current_active_user)):
    return _user_doc_to_out(current_user)

