"""Pydantic schemas for payments."""

from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field


class PaymentCreate(BaseModel):
    amount: Decimal = Field(..., gt=0, decimal_places=2)
    payment_method: str = Field(
        ..., pattern=r"^(cash|card|bank_transfer|upi)$"
    )
    transaction_reference: str | None = Field(default=None, max_length=100)


class PaymentOut(BaseModel):
    id: int
    invoice_id: int
    amount: Decimal
    payment_method: str
    status: str
    transaction_reference: str | None
    paid_at: datetime | None
    created_at: datetime

    model_config = {"from_attributes": True}
