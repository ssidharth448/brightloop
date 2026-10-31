"""Pydantic schemas for authentication (register, login, token, user)."""

from datetime import datetime

from pydantic import BaseModel, EmailStr, Field


# ---------- Request schemas ----------

class UserRegister(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    email: EmailStr
    password: str = Field(..., min_length=6, max_length=128)
    role: str = Field(default="staff", pattern=r"^(admin|staff)$")


class UserLogin(BaseModel):
    email: EmailStr
    password: str


# ---------- Response schemas ----------

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserOut(BaseModel):
    id: int
    name: str
    email: str
    role: str
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
