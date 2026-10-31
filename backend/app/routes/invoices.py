"""Invoice routes — generation and retrieval."""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import require_active_user
from app.models.user import User
from app.schemas.invoice import InvoiceCreate, InvoiceOut
from app.services.invoice_service import (
    compute_amount_paid,
    compute_outstanding,
    create_invoice,
    get_invoice,
    list_invoices,
)

router = APIRouter(prefix="/api/invoices", tags=["Invoices"])


def _enrich(invoice, db: Session | None = None) -> dict:
    """Add computed amount_paid and outstanding_balance to response."""
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


@router.post("", response_model=InvoiceOut, status_code=status.HTTP_201_CREATED)
def create_invoice_route(
    data: InvoiceCreate,
    db: Session = Depends(get_db),
    _user: User = Depends(require_active_user),
):
    """Generate a new invoice with line items."""
    try:
        invoice = create_invoice(db, data)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)
        )
    return _enrich(invoice, db=db)


@router.get("", response_model=list[InvoiceOut])
def list_invoices_route(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    customer_id: int | None = Query(None),
    invoice_status: str | None = Query(None, alias="status"),
    db: Session = Depends(get_db),
    _user: User = Depends(require_active_user),
):
    """List invoices with optional filters."""
    invoices = list_invoices(
        db, skip=skip, limit=limit, customer_id=customer_id, status=invoice_status
    )
    return [_enrich(inv, db=db) for inv in invoices]


@router.get("/{invoice_id}", response_model=InvoiceOut)
def get_invoice_route(
    invoice_id: int,
    db: Session = Depends(get_db),
    _user: User = Depends(require_active_user),
):
    """Retrieve an invoice by ID."""
    invoice = get_invoice(db, invoice_id)
    if invoice is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Invoice not found"
        )
    return _enrich(invoice, db=db)
