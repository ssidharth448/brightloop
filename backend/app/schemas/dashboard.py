"""Pydantic schemas for the dashboard summary."""

from decimal import Decimal
from datetime import date, datetime
from typing import Any
from pydantic import BaseModel, model_validator


class RecentSubscription(BaseModel):
    id: int
    customer_name: str
    plan_name: str
    price: Decimal = Decimal("0.00")
    status: str
    start_date: date
    created_at: datetime


class RecentPayment(BaseModel):
    id: int
    invoice_number: str
    customer_name: str = ""
    amount: Decimal
    payment_method: str
    method: str = ""
    status: str
    paid_at: datetime | None = None
    created_at: datetime


class OverdueInvoice(BaseModel):
    id: int
    invoice_number: str
    customer_name: str
    total_amount: str
    due_date: str
    outstanding: str


class DashboardSummary(BaseModel):
    total_customers: int
    active_subscriptions: int
    monthly_recurring_revenue: Decimal
    mrr: Decimal = Decimal("0.00")
    total_invoices: int
    outstanding_invoice_amount: Decimal
    outstanding_amount: Decimal = Decimal("0.00")
    total_payments_received: Decimal
    recent_subscriptions: list[RecentSubscription]
    recent_payments: list[RecentPayment]
    # Overdue metrics
    overdue_invoices_count: int = 0
    overdue_amount: Decimal = Decimal("0.00")
    overdue_invoices: list[OverdueInvoice] = []

    @model_validator(mode="after")
    def sync_aliases(self):
        if not self.mrr:
            self.mrr = self.monthly_recurring_revenue
        if not self.outstanding_amount:
            self.outstanding_amount = self.outstanding_invoice_amount
        return self
