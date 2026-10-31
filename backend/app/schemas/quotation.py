"""Pydantic schemas for quotation templates and quotations."""

from datetime import date
from decimal import Decimal
from pydantic import BaseModel, Field


class QuotationLineItem(BaseModel):
    """A line item in a quotation template."""
    description: str = Field(..., min_length=1, max_length=255)
    quantity: int = Field(default=1, ge=1)
    unit_price: Decimal = Field(..., ge=0)


class QuotationTemplateCreate(BaseModel):
    """Create a quotation template."""
    name: str = Field(..., min_length=1, max_length=150)
    plan_id: int
    product_lines: list[QuotationLineItem] = Field(default_factory=list)
    validity_days: int = Field(default=30, ge=1, le=365)
    payment_terms: str = Field(default="Net 30", max_length=100)
    notes: str = Field(default="", max_length=500)


class QuotationTemplateOut(QuotationTemplateCreate):
    """Quotation template output."""
    id: str
    created_at: str


class QuotationTemplateUpdate(BaseModel):
    """Partial update for a quotation template."""
    name: str | None = None
    plan_id: int | None = None
    product_lines: list[QuotationLineItem] | None = None
    validity_days: int | None = None
    payment_terms: str | None = None
    notes: str | None = None


class QuotationConvertRequest(BaseModel):
    """Convert a quotation template into a live subscription."""
    template_id: str
    customer_id: int
    start_date: date | None = None
