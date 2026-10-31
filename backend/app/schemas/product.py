"""Pydantic schemas for products and product variants."""

from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel, Field, model_validator


# ---------- Product Variant ----------

class VariantCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    sku: str | None = Field(default=None, max_length=80)
    description: str | None = None
    extra_price: Decimal | None = None
    is_active: bool = True
    active: bool | None = None

    @model_validator(mode="before")
    @classmethod
    def set_aliases(cls, data):
        if isinstance(data, dict):
            if "active" in data and data["active"] is not None and "is_active" not in data:
                data["is_active"] = data["active"]
        return data


class VariantUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=100)
    sku: str | None = Field(default=None, max_length=80)
    description: str | None = None
    extra_price: Decimal | None = None
    is_active: bool | None = None
    active: bool | None = None

    @model_validator(mode="before")
    @classmethod
    def set_aliases(cls, data):
        if isinstance(data, dict):
            if "active" in data and data["active"] is not None and "is_active" not in data:
                data["is_active"] = data["active"]
        return data


class VariantOut(BaseModel):
    id: int
    product_id: int
    name: str
    sku: str | None = None
    description: str | None = None
    extra_price: Decimal = Decimal("0.00")
    is_active: bool = True
    active: bool = True
    created_at: datetime

    model_config = {"from_attributes": True}

    @model_validator(mode="after")
    def sync_aliases(self):
        self.active = self.is_active
        return self


# ---------- Product ----------

class ProductCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=150)
    description: str | None = None
    category: str | None = Field(default=None, max_length=100)
    base_price: Decimal | None = None
    is_active: bool = True
    active: bool | None = None

    @model_validator(mode="before")
    @classmethod
    def set_aliases(cls, data):
        if isinstance(data, dict):
            if "active" in data and data["active"] is not None and "is_active" not in data:
                data["is_active"] = data["active"]
        return data


class ProductUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=150)
    description: str | None = None
    category: str | None = Field(default=None, max_length=100)
    base_price: Decimal | None = None
    is_active: bool | None = None
    active: bool | None = None

    @model_validator(mode="before")
    @classmethod
    def set_aliases(cls, data):
        if isinstance(data, dict):
            if "active" in data and data["active"] is not None and "is_active" not in data:
                data["is_active"] = data["active"]
        return data


class ProductOut(BaseModel):
    id: int
    name: str
    description: str | None = None
    category: str | None = None
    base_price: Decimal = Decimal("0.00")
    is_active: bool = True
    active: bool = True
    variants: list[VariantOut] = []
    created_at: datetime

    model_config = {"from_attributes": True}

    @model_validator(mode="after")
    def sync_aliases(self):
        self.active = self.is_active
        return self
