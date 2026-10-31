"""Customer portal routes — self-service subscription & invoice access."""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.customer import Customer
from app.models.subscription import Subscription
from app.models.invoice import Invoice
from app.schemas.subscription import SubscriptionOut
from app.schemas.invoice import InvoiceOut
from app.services.invoice_service import compute_amount_paid, compute_outstanding
from app.services.subscription_service import pause_subscription, cancel_subscription

router = APIRouter(prefix="/api/portal", tags=["Customer Portal"])


def _get_customer_by_email(db: Session, email: str) -> Customer:
    """Look up a customer by email or raise 404."""
    customer = db.query(Customer).filter(Customer.email == email).first()
    if customer is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Customer not found",
        )
    return customer


def _enrich_sub(sub) -> SubscriptionOut:
    """Add display fields to subscription output."""
    out = SubscriptionOut.model_validate(sub)
    if sub.customer:
        out.customer_name = sub.customer.name
    if sub.plan:
        out.plan_name = sub.plan.name
        out.price = sub.plan.price
        out.billing_interval = sub.plan.billing_interval
        out.interval = sub.plan.billing_interval
    return out


def _enrich_invoice(invoice, db: Session) -> dict:
    """Add computed fields to invoice output."""
    data = InvoiceOut.model_validate(invoice).model_dump()
    paid = compute_amount_paid(invoice, db=db)
    outstanding = compute_outstanding(invoice, db=db)
    data["amount_paid"] = paid
    data["outstanding_balance"] = outstanding
    data["balance"] = outstanding
    data["number"] = invoice.invoice_number
    data["discount"] = invoice.discount_amount
    data["tax"] = invoice.tax_amount
    data["total"] = invoice.total_amount
    if invoice.customer:
        data["customer_name"] = invoice.customer.name
    return data


@router.get("/my-subscriptions", response_model=list[SubscriptionOut])
def my_subscriptions(
    email: str = Query(..., description="Customer email address"),
    db: Session = Depends(get_db),
):
    """List subscriptions belonging to the authenticated customer."""
    customer = _get_customer_by_email(db, email)
    subs = (
        db.query(Subscription)
        .filter(Subscription.customer_id == customer.id)
        .order_by(Subscription.created_at.desc())
        .all()
    )
    return [_enrich_sub(s) for s in subs]


@router.get("/my-invoices")
def my_invoices(
    email: str = Query(..., description="Customer email address"),
    db: Session = Depends(get_db),
):
    """List invoices belonging to the authenticated customer."""
    customer = _get_customer_by_email(db, email)
    invoices = (
        db.query(Invoice)
        .filter(Invoice.customer_id == customer.id)
        .order_by(Invoice.created_at.desc())
        .all()
    )
    return [_enrich_invoice(inv, db) for inv in invoices]


@router.post("/subscriptions/{subscription_id}/pause", response_model=SubscriptionOut)
def portal_pause_subscription(
    subscription_id: int,
    email: str = Query(..., description="Customer email for verification"),
    db: Session = Depends(get_db),
):
    """Pause a subscription (customer self-service)."""
    customer = _get_customer_by_email(db, email)
    sub = db.get(Subscription, subscription_id)
    if sub is None or sub.customer_id != customer.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Subscription not found",
        )
    try:
        sub = pause_subscription(db, subscription_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    return _enrich_sub(sub)


@router.post("/subscriptions/{subscription_id}/cancel", response_model=SubscriptionOut)
def portal_cancel_subscription(
    subscription_id: int,
    email: str = Query(..., description="Customer email for verification"),
    db: Session = Depends(get_db),
):
    """Cancel a subscription (customer self-service)."""
    customer = _get_customer_by_email(db, email)
    sub = db.get(Subscription, subscription_id)
    if sub is None or sub.customer_id != customer.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Subscription not found",
        )
    try:
        sub = cancel_subscription(db, subscription_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    return _enrich_sub(sub)
