"""Pydantic schemas for the dashboard summary."""

from decimal import Decimal
from datetime import date, datetime

from pydantic import BaseModel


class RecentSubscription(BaseModel):
    id: int
    customer_name: str
    plan_name: str
    status: str
    start_date: date
    created_at: datetime


class RecentPayment(BaseModel):
    id: int
    invoice_number: str
    amount: Decimal
    payment_method: str
    status: str
    paid_at: datetime | None
    created_at: datetime


class DashboardSummary(BaseModel):
    total_customers: int
    active_subscriptions: int
    monthly_recurring_revenue: Decimal
    total_invoices: int
    outstanding_invoice_amount: Decimal
    total_payments_received: Decimal
    recent_subscriptions: list[RecentSubscription]
    recent_payments: list[RecentPayment]
