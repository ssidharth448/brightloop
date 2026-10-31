"""Invoice routes — generation, retrieval, actions, billing, and overdue detection."""

from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import require_active_user
from app.models.user import User
from app.schemas.invoice import InvoiceCreate, InvoiceOut
from app.services.invoice_service import (
    cancel_invoice,
    check_overdue_invoices,
    compute_amount_paid,
    compute_outstanding,
    confirm_invoice,
    create_invoice,
    get_invoice,
    get_overdue_summary,
    list_invoices,
    render_invoice_html,
    send_invoice,
)
from app.services.billing_service import generate_due_invoices

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


# ---------- Invoice actions ----------

@router.post("/{invoice_id}/confirm", response_model=InvoiceOut)
def confirm_invoice_route(
    invoice_id: int,
    db: Session = Depends(get_db),
    _user: User = Depends(require_active_user),
):
    """Confirm a draft invoice (draft → issued)."""
    try:
        invoice = confirm_invoice(db, invoice_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    return _enrich(invoice, db=db)


@router.post("/{invoice_id}/cancel", response_model=InvoiceOut)
def cancel_invoice_route(
    invoice_id: int,
    db: Session = Depends(get_db),
    _user: User = Depends(require_active_user),
):
    """Cancel an invoice."""
    try:
        invoice = cancel_invoice(db, invoice_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    return _enrich(invoice, db=db)


@router.post("/{invoice_id}/send")
def send_invoice_route(
    invoice_id: int,
    db: Session = Depends(get_db),
    _user: User = Depends(require_active_user),
):
    """Simulate sending the invoice to the customer."""
    try:
        result = send_invoice(db, invoice_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    return result


@router.get("/{invoice_id}/html", response_class=HTMLResponse)
def print_invoice_route(
    invoice_id: int,
    db: Session = Depends(get_db),
    _user: User = Depends(require_active_user),
):
    """Return a printable HTML view of the invoice."""
    try:
        html = render_invoice_html(db, invoice_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    return HTMLResponse(content=html)


# ---------- Bulk billing ----------

@router.post("/generate-due")
def generate_due_invoices_route(
    target_date: date | None = Query(None, description="Generate invoices due on or before this date (default: today)"),
    db: Session = Depends(get_db),
    _user: User = Depends(require_active_user),
):
    """Bulk-generate invoices for all active subscriptions due on or before target_date."""
    invoices = generate_due_invoices(db, target_date)
    return {
        "message": f"Generated {len(invoices)} invoice(s)",
        "count": len(invoices),
        "invoices": [_enrich(inv, db=db) for inv in invoices],
    }


# ---------- Overdue detection ----------

@router.post("/check-overdue")
def check_overdue_route(
    db: Session = Depends(get_db),
    _user: User = Depends(require_active_user),
):
    """Scan for overdue invoices and mark them accordingly."""
    overdue = check_overdue_invoices(db)
    summary = get_overdue_summary(db)
    return {
        "message": f"Found {len(overdue)} newly overdue invoice(s)",
        "newly_overdue_count": len(overdue),
        **summary,
    }
