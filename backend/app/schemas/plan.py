"""Pydantic schemas for subscription plans."""

from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel, Field, model_validator


class PlanCreate(BaseModel):
    product_id: int
    variant_id: int | None = None
    name: str = Field(..., min_length=1, max_length=150)
    description: str | None = None
    price: Decimal = Field(..., ge=0, decimal_places=2)
    currency: str = Field(default="INR", min_length=3, max_length=3)
    billing_interval: str = Field(default="monthly", pattern=r"^(monthly|quarterly|yearly)$")
    interval: str | None = None
    trial_days: int = Field(default=0, ge=0)
    is_active: bool = True
    active: bool | None = None

    @model_validator(mode="before")
    @classmethod
    def set_aliases(cls, data):
        if isinstance(data, dict):
            if "interval" in data and data["interval"] and "billing_interval" not in data:
                data["billing_interval"] = data["interval"]
            if "active" in data and data["active"] is not None and "is_active" not in data:
                data["is_active"] = data["active"]
        return data


class PlanUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=150)
    description: str | None = None
    price: Decimal | None = Field(default=None, ge=0, decimal_places=2)
    currency: str | None = Field(default=None, min_length=3, max_length=3)
    billing_interval: str | None = Field(
        default=None, pattern=r"^(monthly|quarterly|yearly)$"
    )
    interval: str | None = None
    trial_days: int | None = Field(default=None, ge=0)
    is_active: bool | None = None
    active: bool | None = None

    @model_validator(mode="before")
    @classmethod
    def set_aliases(cls, data):
        if isinstance(data, dict):
            if "interval" in data and data["interval"] and "billing_interval" not in data:
                data["billing_interval"] = data["interval"]
            if "active" in data and data["active"] is not None and "is_active" not in data:
                data["is_active"] = data["active"]
        return data


class PlanOut(BaseModel):
    id: int
    product_id: int
    variant_id: int | None = None
    product_name: str = ""
    name: str
    description: str | None = None
    price: Decimal
    currency: str = "INR"
    billing_interval: str
    interval: str = ""
    trial_days: int = 0
    is_active: bool = True
    active: bool = True
    created_at: datetime

    model_config = {"from_attributes": True}

    @model_validator(mode="after")
    def sync_aliases(self):
        self.active = self.is_active
        if not self.interval:
            self.interval = self.billing_interval
        return self
