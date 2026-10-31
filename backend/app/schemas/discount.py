"""Pydantic schemas for discount rules."""

from datetime import date
from decimal import Decimal
from pydantic import BaseModel, Field


class DiscountRuleCreate(BaseModel):
    """Create a new discount rule."""
    code: str = Field(..., min_length=1, max_length=50)
    description: str = Field(default="", max_length=255)
    discount_type: str = Field(..., pattern=r"^(fixed|percentage)$")
    value: Decimal = Field(..., gt=0)
    min_purchase: Decimal = Field(default=Decimal("0.00"), ge=0)
    min_quantity: int = Field(default=0, ge=0)
    start_date: date | None = None
    end_date: date | None = None
    max_uses: int = Field(default=0, ge=0, description="0 = unlimited")
    product_id: int | None = None
    applies_to: str = Field(
        default="all",
        pattern=r"^(all|product|subscription)$",
    )


class DiscountRuleOut(DiscountRuleCreate):
    """Discount rule output with tracking fields."""
    id: str
    used_count: int = 0
    is_active: bool = True


class DiscountRuleUpdate(BaseModel):
    """Partial update for a discount rule."""
    description: str | None = None
    discount_type: str | None = None
    value: Decimal | None = None
    min_purchase: Decimal | None = None
    min_quantity: int | None = None
    start_date: date | None = None
    end_date: date | None = None
    max_uses: int | None = None
    product_id: int | None = None
    applies_to: str | None = None
    is_active: bool | None = None
