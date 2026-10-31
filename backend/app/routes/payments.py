"""Payment routes — record and list payments."""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import require_active_user
from app.models.payment import Payment
from app.models.user import User
from app.schemas.payment import PaymentCreate, PaymentOut
from app.services.invoice_service import get_invoice
from app.services.payment_service import get_payment, list_payments, record_payment

router = APIRouter(tags=["Payments"])


def _enrich_payment(payment: Payment) -> PaymentOut:
    out = PaymentOut.model_validate(payment)
    if payment.invoice:
        out.invoice_number = payment.invoice.invoice_number
        if payment.invoice.customer:
            out.customer_name = payment.invoice.customer.name
    return out


@router.post(
    "/api/invoices/{invoice_id}/payments",
    response_model=PaymentOut,
    status_code=status.HTTP_201_CREATED,
)
def create_payment_route(
    invoice_id: int,
    data: PaymentCreate,
    db: Session = Depends(get_db),
    _user: User = Depends(require_active_user),
):
    """Record a simulated payment against an invoice."""
    invoice = get_invoice(db, invoice_id)
    if invoice is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Invoice not found"
        )
    try:
        payment = record_payment(db, invoice, data)
        return _enrich_payment(payment)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)
        )


@router.get("/api/payments", response_model=list[PaymentOut])
def list_payments_route(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    invoice_id: int | None = Query(None),
    db: Session = Depends(get_db),
    _user: User = Depends(require_active_user),
):
    """List all payments with optional invoice filter."""
    payments = list_payments(db, skip=skip, limit=limit, invoice_id=invoice_id)
    return [_enrich_payment(p) for p in payments]


@router.get("/api/payments/{payment_id}", response_model=PaymentOut)
def get_payment_route(
    payment_id: int,
    db: Session = Depends(get_db),
    _user: User = Depends(require_active_user),
):
    """Retrieve a payment by ID."""
    payment = get_payment(db, payment_id)
    if payment is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Payment not found"
        )
    return _enrich_payment(payment)
