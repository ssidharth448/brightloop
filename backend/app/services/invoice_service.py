"""Invoice service — generation, calculation, and retrieval."""

import uuid
from datetime import date, timedelta
from decimal import Decimal, ROUND_HALF_UP

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.invoice import Invoice, InvoiceItem
from app.models.payment import Payment
from app.models.subscription import Subscription
from app.schemas.invoice import InvoiceCreate


def _next_invoice_number() -> str:
    """Generate a unique invoice number."""
    short_id = uuid.uuid4().hex[:8].upper()
    return f"INV-{short_id}"


def _quantize(value: Decimal) -> Decimal:
    """Round to 2 decimal places."""
    return value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def create_invoice(db: Session, data: InvoiceCreate) -> Invoice:
    """Create an invoice with line items and computed totals."""
    issue = data.issue_date or date.today()
    due = data.due_date or (issue + timedelta(days=30))

    customer_id = data.customer_id
    items: list[InvoiceItem] = []
    subtotal = Decimal("0.00")

    # If subscription is provided, resolve customer and default line item if not supplied
    if data.subscription_id is not None:
        sub = db.get(Subscription, data.subscription_id)
        if sub is None:
            raise ValueError(f"Subscription {data.subscription_id} not found")
        if customer_id is None:
            customer_id = sub.customer_id
        if not data.items and sub.plan:
            unit_price = _quantize(sub.plan.price)
            items.append(
                InvoiceItem(
                    description=f"{sub.plan.name} ({sub.plan.billing_interval.title()})",
                    quantity=1,
                    unit_price=unit_price,
                    line_total=unit_price,
                )
            )
            subtotal += unit_price

    if customer_id is None:
        raise ValueError("customer_id is required when creating an invoice")

    # Build line items and compute subtotal if items explicitly provided
    if data.items:
        items = []
        subtotal = Decimal("0.00")
        for item_data in data.items:
            line_total = _quantize(Decimal(str(item_data.unit_price)) * item_data.quantity)
            items.append(
                InvoiceItem(
                    description=item_data.description,
                    quantity=item_data.quantity,
                    unit_price=item_data.unit_price,
                    line_total=line_total,
                )
            )
            subtotal += line_total

    if not items:
        raise ValueError("Invoice must contain at least one line item")

    subtotal = _quantize(subtotal)
    discount = _quantize(Decimal(str(data.discount_amount)))
    if discount > subtotal:
        raise ValueError("Discount amount cannot exceed subtotal")

    # Tax calculation
    tax_rate = (
        Decimal(str(data.tax_rate))
        if data.tax_rate is not None
        else Decimal(str(settings.DEFAULT_TAX_RATE))
    )
    taxable = subtotal - discount
    tax_amount = _quantize(taxable * tax_rate / Decimal("100"))
    total_amount = _quantize(subtotal - discount + tax_amount)

    invoice = Invoice(
        invoice_number=_next_invoice_number(),
        customer_id=customer_id,
        subscription_id=data.subscription_id,
        issue_date=issue,
        due_date=due,
        currency=data.currency,
        subtotal=subtotal,
        discount_amount=discount,
        tax_amount=tax_amount,
        total_amount=total_amount,
        status="issued",
        items=items,
    )
    db.add(invoice)
    db.commit()
    db.refresh(invoice)
    return invoice


def list_invoices(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    customer_id: int | None = None,
    status: str | None = None,
) -> list[Invoice]:
    q = db.query(Invoice)
    if customer_id is not None:
        q = q.filter(Invoice.customer_id == customer_id)
    if status is not None:
        q = q.filter(Invoice.status == status)
    return q.order_by(Invoice.id.desc()).offset(skip).limit(limit).all()


def get_invoice(db: Session, invoice_id: int) -> Invoice | None:
    return db.get(Invoice, invoice_id)


def compute_amount_paid(invoice: Invoice, db: Session | None = None) -> Decimal:
    """Sum of all succeeded payments for this invoice."""
    if db is not None:
        total = (
            db.query(func.coalesce(func.sum(Payment.amount), 0))
            .filter(Payment.invoice_id == invoice.id, Payment.status == "succeeded")
            .scalar()
        )
        return _quantize(Decimal(str(total)))

    return _quantize(
        sum(
            (p.amount for p in (invoice.payments or []) if p.status == "succeeded"),
            Decimal("0.00"),
        )
    )


def compute_outstanding(invoice: Invoice, db: Session | None = None) -> Decimal:
    """Outstanding balance = total_amount - amount_paid."""
    return _quantize(invoice.total_amount - compute_amount_paid(invoice, db=db))


def update_invoice_status_after_payment(db: Session, invoice: Invoice) -> None:
    """Update the invoice status based on payments received."""
    if invoice.status == "cancelled":
        return

    paid = compute_amount_paid(invoice, db=db)
    if paid >= invoice.total_amount:
        invoice.status = "paid"
    elif paid > Decimal("0.00"):
        invoice.status = "partially_paid"
    else:
        # Keep current status (issued / overdue)
        pass
    db.commit()
    db.refresh(invoice)
