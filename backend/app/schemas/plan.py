"""Pydantic schemas for subscription plans."""

from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field


class PlanCreate(BaseModel):
    product_id: int
    variant_id: int | None = None
    name: str = Field(..., min_length=1, max_length=150)
    description: str | None = None
    price: Decimal = Field(..., ge=0, decimal_places=2)
    currency: str = Field(default="INR", min_length=3, max_length=3)
    billing_interval: str = Field(..., pattern=r"^(monthly|quarterly|yearly)$")
    trial_days: int = Field(default=0, ge=0)
    is_active: bool = True


class PlanUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=150)
    description: str | None = None
    price: Decimal | None = Field(default=None, ge=0, decimal_places=2)
    currency: str | None = Field(default=None, min_length=3, max_length=3)
    billing_interval: str | None = Field(
        default=None, pattern=r"^(monthly|quarterly|yearly)$"
    )
    trial_days: int | None = Field(default=None, ge=0)
    is_active: bool | None = None


class PlanOut(BaseModel):
    id: int
    product_id: int
    variant_id: int | None
    name: str
    description: str | None
    price: Decimal
    currency: str
    billing_interval: str
    trial_days: int
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}
