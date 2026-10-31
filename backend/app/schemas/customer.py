"""Pydantic schemas for customers."""

from datetime import datetime
from pydantic import BaseModel, EmailStr, Field


class CustomerCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=150)
    email: EmailStr
    phone: str | None = Field(default=None, max_length=30)
    company: str | None = None
    billing_address: str | None = None
    city: str | None = Field(default=None, max_length=100)
    state: str | None = Field(default=None, max_length=100)
    postal_code: str | None = Field(default=None, max_length=20)
    country: str = Field(default="India", max_length=100)


class CustomerUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=150)
    email: EmailStr | None = None
    phone: str | None = Field(default=None, max_length=30)
    company: str | None = None
    billing_address: str | None = None
    city: str | None = Field(default=None, max_length=100)
    state: str | None = Field(default=None, max_length=100)
    postal_code: str | None = Field(default=None, max_length=20)
    country: str | None = Field(default=None, max_length=100)
    is_active: bool | None = None


class CustomerOut(BaseModel):
    id: int
    name: str
    email: str
    phone: str | None = None
    company: str = ""
    billing_address: str | None = None
    city: str | None = None
    state: str | None = None
    postal_code: str | None = None
    country: str = "India"
    is_active: bool = True
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
