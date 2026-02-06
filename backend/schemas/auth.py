from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    username: Optional[str] = None
    role: Optional[str] = None


class UserBase(BaseModel):
    username: str
    full_name: Optional[str] = None
    email: EmailStr


class UserCreate(UserBase):
    password: str
    role: str


class UserOut(UserBase):
    id: str
    role: str
    is_active: bool

    class Config:
        orm_mode = True


class LoginRequest(BaseModel):
    username: str
    password: str


class MeResponse(UserOut):
    last_login: Optional[datetime] = None

