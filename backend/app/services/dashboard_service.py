"""Dashboard service — aggregate business metrics."""

from decimal import Decimal, ROUND_HALF_UP

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.customer import Customer
from app.models.invoice import Invoice
from app.models.payment import Payment
from app.models.plan import Plan
from app.models.subscription import Subscription
from app.schemas.dashboard import (
    DashboardSummary,
    OverdueInvoice,
    RecentPayment,
    RecentSubscription,
)


# Divisors to normalize any billing interval to a monthly amount
_MONTHLY_DIVISORS = {
    "monthly": Decimal("1"),
    "quarterly": Decimal("3"),
    "yearly": Decimal("12"),
}


def _quantize(v: Decimal) -> Decimal:
    return v.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def get_dashboard_summary(db: Session) -> DashboardSummary:
    # Total customers (active)
    total_customers: int = (
        db.query(func.count(Customer.id))
        .filter(Customer.is_active.is_(True))
        .scalar()
        or 0
    )

    # Active subscriptions
    active_subs: int = (
        db.query(func.count(Subscription.id))
        .filter(Subscription.status == "active")
        .scalar()
        or 0
    )

    # Monthly Recurring Revenue (only active subscriptions)
    mrr = Decimal("0.00")
    active_rows = (
        db.query(Plan.price, Plan.billing_interval)
        .join(Subscription, Subscription.plan_id == Plan.id)
        .filter(Subscription.status == "active")
        .all()
    )
    for price, interval in active_rows:
        divisor = _MONTHLY_DIVISORS.get(interval, Decimal("1"))
        mrr += Decimal(str(price)) / divisor
    mrr = _quantize(mrr)

    # Total invoices
    total_invoices: int = db.query(func.count(Invoice.id)).scalar() or 0

    # Outstanding invoice amount (non-cancelled, non-paid)
    outstanding_invoices = (
        db.query(Invoice)
        .filter(Invoice.status.notin_(["cancelled", "paid"]))
        .all()
    )
    outstanding_amount = Decimal("0.00")
    for inv in outstanding_invoices:
        paid = sum(
            (p.amount for p in inv.payments if p.status == "succeeded"),
            Decimal("0.00"),
        )
        outstanding_amount += inv.total_amount - paid
    outstanding_amount = _quantize(outstanding_amount)

    # Total payments received (succeeded only)
    total_payments_received: Decimal = (
        db.query(func.coalesce(func.sum(Payment.amount), 0))
        .filter(Payment.status == "succeeded")
        .scalar()
    )
    total_payments_received = _quantize(Decimal(str(total_payments_received)))

    # Recent subscriptions (last 10)
    recent_sub_rows = (
        db.query(Subscription)
        .order_by(Subscription.created_at.desc())
        .limit(10)
        .all()
    )
    recent_subscriptions = [
        RecentSubscription(
            id=s.id,
            customer_name=s.customer.name if s.customer else "",
            plan_name=s.plan.name if s.plan else "",
            price=s.plan.price if s.plan else Decimal("0.00"),
            status=s.status,
            start_date=s.start_date,
            created_at=s.created_at,
        )
        for s in recent_sub_rows
    ]

    # Recent payments (last 10)
    recent_pay_rows = (
        db.query(Payment)
        .order_by(Payment.created_at.desc())
        .limit(10)
        .all()
    )
    recent_payments = [
        RecentPayment(
            id=p.id,
            invoice_number=p.invoice.invoice_number if p.invoice else "",
            customer_name=p.invoice.customer.name if p.invoice and p.invoice.customer else "",
            amount=p.amount,
            payment_method=p.payment_method,
            method=p.payment_method,
            status=p.status,
            paid_at=p.paid_at,
            created_at=p.created_at,
        )
        for p in recent_pay_rows
    ]

    # Overdue metrics
    overdue_invoices_list = (
        db.query(Invoice)
        .filter(Invoice.status == "overdue")
        .all()
    )
    overdue_amount = Decimal("0.00")
    overdue_details: list[OverdueInvoice] = []
    for inv in overdue_invoices_list:
        paid = sum(
            (p.amount for p in inv.payments if p.status == "succeeded"),
            Decimal("0.00"),
        )
        owed = inv.total_amount - paid
        overdue_amount += owed
        overdue_details.append(
            OverdueInvoice(
                id=inv.id,
                invoice_number=inv.invoice_number,
                customer_name=inv.customer.name if inv.customer else "N/A",
                total_amount=str(inv.total_amount),
                due_date=inv.due_date.isoformat(),
                outstanding=str(_quantize(owed)),
            )
        )
    overdue_amount = _quantize(overdue_amount)

    return DashboardSummary(
        total_customers=total_customers,
        active_subscriptions=active_subs,
        monthly_recurring_revenue=mrr,
        total_invoices=total_invoices,
        outstanding_invoice_amount=outstanding_amount,
        total_payments_received=total_payments_received,
        recent_subscriptions=recent_subscriptions,
        recent_payments=recent_payments,
        overdue_invoices_count=len(overdue_invoices_list),
        overdue_amount=overdue_amount,
        overdue_invoices=overdue_details,
    )
