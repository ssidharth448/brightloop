"""Pydantic schemas for invoices and invoice items."""

from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, Field


# ---------- Invoice Item ----------

class InvoiceItemCreate(BaseModel):
    description: str = Field(..., min_length=1, max_length=255)
    quantity: int = Field(default=1, gt=0)
    unit_price: Decimal = Field(..., ge=0, decimal_places=2)


class InvoiceItemOut(BaseModel):
    id: int
    invoice_id: int
    description: str
    quantity: int
    unit_price: Decimal
    line_total: Decimal

    model_config = {"from_attributes": True}


# ---------- Invoice ----------

class InvoiceCreate(BaseModel):
    customer_id: int
    subscription_id: int | None = None
    issue_date: date | None = None  # defaults to today
    due_date: date | None = None    # defaults to issue_date + 30 days
    currency: str = Field(default="INR", min_length=3, max_length=3)
    items: list[InvoiceItemCreate] = Field(..., min_length=1)
    discount_amount: Decimal = Field(default=Decimal("0.00"), ge=0, decimal_places=2)
    tax_rate: Decimal | None = None  # percentage; defaults to settings.DEFAULT_TAX_RATE


class InvoiceOut(BaseModel):
    id: int
    invoice_number: str
    customer_id: int
    subscription_id: int | None
    issue_date: date
    due_date: date
    currency: str
    subtotal: Decimal
    discount_amount: Decimal
    tax_amount: Decimal
    total_amount: Decimal
    status: str
    created_at: datetime
    items: list[InvoiceItemOut] = []
    amount_paid: Decimal = Decimal("0.00")
    outstanding_balance: Decimal = Decimal("0.00")

    model_config = {"from_attributes": True}
