"""Payment service — simulated payment recording and invoice updates."""

from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy.orm import Session

from app.models.payment import Payment
from app.models.invoice import Invoice
from app.schemas.payment import PaymentCreate
from app.services.invoice_service import compute_outstanding, update_invoice_status_after_payment


def record_payment(db: Session, invoice: Invoice, data: PaymentCreate) -> Payment:
    """Record a payment against an invoice.

    Validates that the payment does not exceed the outstanding balance,
    marks the payment as succeeded immediately (simulated), and updates
    the invoice status.
    """
    outstanding = compute_outstanding(invoice, db=db)
    if data.amount > outstanding:
        raise ValueError(
            f"Payment amount {data.amount} exceeds outstanding balance {outstanding}"
        )

    if invoice.status == "cancelled":
        raise ValueError("Cannot record payment on a cancelled invoice")

    payment = Payment(
        invoice_id=invoice.id,
        amount=data.amount,
        payment_method=data.payment_method,
        status="succeeded",  # simulated — instant success
        transaction_reference=data.transaction_reference,
        paid_at=datetime.now(timezone.utc),
    )
    db.add(payment)
    db.flush()  # ensure payment is persisted before status check

    update_invoice_status_after_payment(db, invoice)
    db.commit()
    db.refresh(payment)
    return payment


def list_payments(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    invoice_id: int | None = None,
) -> list[Payment]:
    q = db.query(Payment)
    if invoice_id is not None:
        q = q.filter(Payment.invoice_id == invoice_id)
    return q.order_by(Payment.id.desc()).offset(skip).limit(limit).all()


def get_payment(db: Session, payment_id: int) -> Payment | None:
    return db.get(Payment, payment_id)
