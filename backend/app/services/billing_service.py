"""Bulk billing engine — generates invoices for subscriptions due on a target date.

This service queries all active subscriptions where ``next_billing_date <= target_date``,
creates an invoice for each, applies taxes and discounts, and advances the billing
cycle so nothing is billed twice.
"""

from datetime import date
from decimal import Decimal

from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.invoice import Invoice, InvoiceItem
from app.models.subscription import Subscription
from app.services.discount_service import evaluate_discounts


def _next_invoice_number(db: Session) -> str:
    """Generate the next sequential invoice number."""
    last = (
        db.query(Invoice)
        .order_by(Invoice.id.desc())
        .first()
    )
    seq = (last.id + 1) if last else 1
    return f"INV-{seq:06d}"


def _add_interval(d: date, interval: str) -> date:
    """Advance a date by the billing interval using stdlib only."""
    import calendar
    if interval == "monthly":
        month = d.month + 1
        year = d.year
        if month > 12:
            month = 1
            year += 1
        day = min(d.day, calendar.monthrange(year, month)[1])
        return date(year, month, day)
    elif interval == "quarterly":
        month = d.month + 3
        year = d.year
        while month > 12:
            month -= 12
            year += 1
        day = min(d.day, calendar.monthrange(year, month)[1])
        return date(year, month, day)
    elif interval == "yearly":
        try:
            return date(d.year + 1, d.month, d.day)
        except ValueError:
            return date(d.year + 1, d.month, 28)
    else:
        # Default to monthly
        return _add_interval(d, "monthly")


def generate_due_invoices(
    db: Session,
    target_date: date | None = None,
) -> list[Invoice]:
    """Generate invoices for all active subscriptions due on or before *target_date*.

    Returns a list of newly created Invoice objects.
    """
    if target_date is None:
        target_date = date.today()

    due_subs: list[Subscription] = (
        db.query(Subscription)
        .filter(
            Subscription.status == "active",
            Subscription.next_billing_date <= target_date,
        )
        .all()
    )

    created_invoices: list[Invoice] = []

    for sub in due_subs:
        plan = sub.plan
        if plan is None:
            continue

        price = Decimal(str(plan.price))
        description = f"{plan.name} — {plan.billing_interval} subscription"

        # Calculate discount
        discount = evaluate_discounts(
            subtotal=price,
            quantity=1,
            product_id=plan.product_id,
            target="subscription",
        )

        # Calculate tax
        tax_rate = Decimal(str(settings.DEFAULT_TAX_RATE))
        taxable = price - discount
        tax_amount = (taxable * tax_rate / Decimal("100")).quantize(Decimal("0.01"))
        total = (taxable + tax_amount).quantize(Decimal("0.01"))

        invoice_number = _next_invoice_number(db)
        issue = target_date
        # Due date is 15 days after issue
        due = date(issue.year, issue.month, min(issue.day + 15, 28))
        if issue.day + 15 > 28:
            # Simplified: wrap to next month
            import calendar
            month = issue.month + 1
            year = issue.year
            if month > 12:
                month = 1
                year += 1
            due = date(year, month, min(issue.day + 15 - 28, calendar.monthrange(year, month)[1]))

        invoice = Invoice(
            invoice_number=invoice_number,
            customer_id=sub.customer_id,
            subscription_id=sub.id,
            issue_date=issue,
            due_date=due,
            currency=plan.currency,
            subtotal=price,
            discount_amount=discount,
            tax_amount=tax_amount,
            total_amount=total,
            status="draft",
        )
        db.add(invoice)
        db.flush()

        item = InvoiceItem(
            invoice_id=invoice.id,
            description=description,
            quantity=1,
            unit_price=price,
            line_total=price,
        )
        db.add(item)

        # Advance the billing cycle
        next_period_start = sub.current_period_end
        next_period_end = _add_interval(next_period_start, plan.billing_interval)
        sub.current_period_start = next_period_start
        sub.current_period_end = next_period_end
        sub.next_billing_date = next_period_end

        created_invoices.append(invoice)

    db.commit()
    return created_invoices
