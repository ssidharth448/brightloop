"""Pydantic schemas for products and product variants."""

from datetime import datetime

from pydantic import BaseModel, Field


# ---------- Product ----------

class ProductCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=150)
    description: str | None = None
    category: str | None = Field(default=None, max_length=100)
    is_active: bool = True


class ProductUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=150)
    description: str | None = None
    category: str | None = Field(default=None, max_length=100)
    is_active: bool | None = None


class ProductOut(BaseModel):
    id: int
    name: str
    description: str | None
    category: str | None
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


# ---------- Product Variant ----------

class VariantCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    sku: str | None = Field(default=None, max_length=80)
    description: str | None = None
    is_active: bool = True


class VariantUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=100)
    sku: str | None = Field(default=None, max_length=80)
    description: str | None = None
    is_active: bool | None = None


class VariantOut(BaseModel):
    id: int
    product_id: int
    name: str
    sku: str | None
    description: str | None
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}
