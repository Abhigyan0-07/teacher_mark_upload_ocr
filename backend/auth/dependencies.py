from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from pymongo.database import Database

from ..database import get_db
from .security import decode_access_token, verify_password


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


def get_user_by_username(db: Database, username: str) -> dict | None:
    return db["users"].find_one({"username": username})


def authenticate_user(db: Database, username: str, password: str) -> dict | None:
    user = get_user_by_username(db, username)
    if not user or not verify_password(password, user.get("hashed_password", "")):
        return None
    return user


def get_current_user(
    token: str = Depends(oauth2_scheme), db: Database = Depends(get_db)
) -> dict:
    token_data = decode_access_token(token)
    if token_data is None or token_data.username is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    user = get_user_by_username(db, token_data.username)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user


def get_current_active_user(current_user: dict = Depends(get_current_user)) -> dict:
    if not current_user.get("is_active", True):
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user


def require_admin(current_user: dict = Depends(get_current_active_user)) -> dict:
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin privileges required")
    return current_user


def require_teacher(current_user: dict = Depends(get_current_active_user)) -> dict:
    if current_user.get("role") not in ["teacher", "admin"]:
        raise HTTPException(status_code=403, detail="Teacher privileges required")
    return current_user

