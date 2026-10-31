"""Pydantic schemas for subscriptions."""

from datetime import date, datetime

from pydantic import BaseModel, Field


class SubscriptionCreate(BaseModel):
    customer_id: int
    plan_id: int
    start_date: date | None = None  # defaults to today


class SubscriptionUpdate(BaseModel):
    plan_id: int | None = None


class SubscriptionOut(BaseModel):
    id: int
    customer_id: int
    plan_id: int
    status: str
    start_date: date
    current_period_start: date
    current_period_end: date
    next_billing_date: date | None
    cancel_at_period_end: bool
    cancelled_at: datetime | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
