"""Pydantic schemas for payments."""

from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel, Field, model_validator


class PaymentCreate(BaseModel):
    amount: Decimal = Field(..., gt=0, decimal_places=2)
    payment_method: str = Field(
        default="card", pattern=r"^(cash|card|bank_transfer|upi)$"
    )
    method: str | None = None
    transaction_reference: str | None = Field(default=None, max_length=100)

    @model_validator(mode="before")
    @classmethod
    def set_aliases(cls, data):
        if isinstance(data, dict):
            if "method" in data and data["method"] and "payment_method" not in data:
                data["payment_method"] = data["method"]
        return data


class PaymentOut(BaseModel):
    id: int
    invoice_id: int
    invoice_number: str = ""
    customer_name: str = ""
    amount: Decimal
    payment_method: str
    method: str = ""
    status: str
    transaction_reference: str | None = None
    paid_at: datetime | None = None
    created_at: datetime

    model_config = {"from_attributes": True}

    @model_validator(mode="after")
    def sync_aliases(self):
        if not self.method:
            self.method = self.payment_method
        return self
