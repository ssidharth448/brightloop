"""Pydantic schemas for authentication (register, login, token, user)."""

from datetime import datetime
from pydantic import BaseModel, EmailStr, Field, model_validator


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

class UserOut(BaseModel):
    id: int
    name: str
    email: str
    role: str
    is_active: bool = True
    active: bool = True
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}

    @model_validator(mode="after")
    def sync_aliases(self):
        self.active = self.is_active
        return self


class Token(BaseModel):
    access_token: str
    token: str = ""
    token_type: str = "bearer"
    user: UserOut | None = None

    @model_validator(mode="after")
    def sync_aliases(self):
        if not self.token:
            self.token = self.access_token
        return self
