from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .routes import auth as auth_routes
from .routes import admin as admin_routes
from .routes import teacher as teacher_routes
from .database import get_mongo_client, MONGO_DB_NAME
from .auth.security import get_password_hash


app = FastAPI(title="Marks OCR System")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def ensure_default_admin_user():
    """
    Ensure there is at least one admin user for initial login.
    Username: abhigyan
    Password: Abhigyan@001
    """
    client = get_mongo_client()
    db = client[MONGO_DB_NAME]
    username = "abhigyan"
    existing = db["users"].find_one({"username": username})
    if existing:
        return
    doc = {
        "username": username,
        "email": "abhigyan@example.com",
        "full_name": "Abhigyan",
        "role": "admin",
        "hashed_password": get_password_hash("Abhigyan@001"),
        "is_active": True,
    }
    db["users"].insert_one(doc)


@app.get("/api/health")
def health_check():
    return {"status": "ok"}


app.include_router(auth_routes.router, prefix="/api/auth", tags=["auth"])
app.include_router(admin_routes.router, prefix="/api/admin", tags=["admin"])
app.include_router(teacher_routes.router, prefix="/api/teacher", tags=["teacher"])

