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


# ---------- Invoice actions ----------

def confirm_invoice(db: Session, invoice_id: int) -> Invoice:
    """Transition an invoice from draft -> issued."""
    invoice = db.get(Invoice, invoice_id)
    if invoice is None:
        raise ValueError("Invoice not found")
    if invoice.status != "draft":
        raise ValueError(f"Cannot confirm invoice in '{invoice.status}' status (must be 'draft')")
    invoice.status = "issued"
    db.commit()
    db.refresh(invoice)
    return invoice


def cancel_invoice(db: Session, invoice_id: int) -> Invoice:
    """Cancel an invoice (from draft or issued status)."""
    invoice = db.get(Invoice, invoice_id)
    if invoice is None:
        raise ValueError("Invoice not found")
    if invoice.status in ("paid", "cancelled"):
        raise ValueError(f"Cannot cancel invoice in '{invoice.status}' status")
    invoice.status = "cancelled"
    db.commit()
    db.refresh(invoice)
    return invoice


def send_invoice(db: Session, invoice_id: int) -> dict:
    """Simulate sending an invoice to the customer via email.

    In production this would dispatch an actual email.
    Returns a confirmation dict.
    """
    invoice = db.get(Invoice, invoice_id)
    if invoice is None:
        raise ValueError("Invoice not found")
    if invoice.status == "draft":
        # Auto-confirm before sending
        invoice.status = "issued"
        db.commit()
        db.refresh(invoice)
    customer_name = invoice.customer.name if invoice.customer else "Customer"
    customer_email = invoice.customer.email if invoice.customer else "unknown"
    return {
        "message": f"Invoice {invoice.invoice_number} sent to {customer_name} ({customer_email})",
        "invoice_id": invoice.id,
        "invoice_number": invoice.invoice_number,
        "recipient_email": customer_email,
        "status": "sent",
    }


def render_invoice_html(db: Session, invoice_id: int) -> str:
    """Render a printable HTML view of an invoice."""
    invoice = db.get(Invoice, invoice_id)
    if invoice is None:
        raise ValueError("Invoice not found")

    customer = invoice.customer
    items_html = ""
    for item in invoice.items:
        items_html += f"""
        <tr>
            <td style="padding:8px;border:1px solid #ddd">{item.description}</td>
            <td style="padding:8px;border:1px solid #ddd;text-align:center">{item.quantity}</td>
            <td style="padding:8px;border:1px solid #ddd;text-align:right">{item.unit_price:.2f}</td>
            <td style="padding:8px;border:1px solid #ddd;text-align:right">{item.line_total:.2f}</td>
        </tr>"""

    cust_name = customer.name if customer else "N/A"
    cust_email = customer.email if customer else ""
    cust_addr = customer.billing_address or "" if customer else ""
    cust_city = customer.city if customer else None
    cust_state = customer.state if customer else None
    cust_postal = customer.postal_code if customer else None
    cust_country = customer.country if customer else ""
    city_line = ", ".join(filter(None, [cust_city, cust_state, cust_postal]))

    return f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Invoice {invoice.invoice_number}</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 40px; color: #333; }}
        .header {{ display: flex; justify-content: space-between; margin-bottom: 30px; }}
        .company {{ font-size: 24px; font-weight: bold; color: #2563eb; }}
        .invoice-title {{ font-size: 20px; color: #666; }}
        .info-grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-bottom: 30px; }}
        .info-box {{ padding: 15px; background: #f9fafb; border-radius: 8px; }}
        .info-box h3 {{ margin: 0 0 8px 0; font-size: 14px; color: #666; text-transform: uppercase; }}
        table {{ width: 100%; border-collapse: collapse; margin-bottom: 20px; }}
        th {{ padding: 10px 8px; background: #2563eb; color: white; text-align: left; }}
        .totals {{ text-align: right; margin-top: 20px; }}
        .totals td {{ padding: 6px 12px; }}
        .totals .grand-total {{ font-size: 18px; font-weight: bold; color: #2563eb; }}
        .status {{ display: inline-block; padding: 4px 12px; border-radius: 12px; font-size: 12px;
                   font-weight: bold; text-transform: uppercase; }}
        .status-draft {{ background: #fef3c7; color: #92400e; }}
        .status-issued {{ background: #dbeafe; color: #1e40af; }}
        .status-paid {{ background: #d1fae5; color: #065f46; }}
        .status-overdue {{ background: #fee2e2; color: #991b1b; }}
        .status-cancelled {{ background: #f3f4f6; color: #6b7280; }}
        .footer {{ margin-top: 40px; padding-top: 20px; border-top: 1px solid #ddd;
                   font-size: 12px; color: #888; text-align: center; }}
        @media print {{ body {{ margin: 20px; }} }}
    </style>
</head>
<body>
    <div class="header">
        <div>
            <div class="company">Brightloop</div>
            <div style="color:#666">Subscription Management System</div>
        </div>
        <div style="text-align:right">
            <div class="invoice-title">INVOICE</div>
            <div style="font-size:18px;font-weight:bold">{invoice.invoice_number}</div>
            <span class="status status-{invoice.status}">{invoice.status}</span>
        </div>
    </div>

    <div class="info-grid">
        <div class="info-box">
            <h3>Bill To</h3>
            <strong>{cust_name}</strong><br>
            {cust_email}<br>
            {cust_addr}<br>
            {city_line}<br>
            {cust_country}
        </div>
        <div class="info-box">
            <h3>Invoice Details</h3>
            <strong>Issue Date:</strong> {invoice.issue_date}<br>
            <strong>Due Date:</strong> {invoice.due_date}<br>
            <strong>Currency:</strong> {invoice.currency}<br>
            {f'<strong>Subscription:</strong> #{invoice.subscription_id}' if invoice.subscription_id else ''}
        </div>
    </div>

    <table>
        <thead>
            <tr>
                <th>Description</th>
                <th style="text-align:center">Qty</th>
                <th style="text-align:right">Unit Price</th>
                <th style="text-align:right">Amount</th>
            </tr>
        </thead>
        <tbody>{items_html}
        </tbody>
    </table>

    <table class="totals" style="width:300px;margin-left:auto">
        <tr><td>Subtotal:</td><td>{invoice.currency} {invoice.subtotal:.2f}</td></tr>
        <tr><td>Discount:</td><td>-{invoice.currency} {invoice.discount_amount:.2f}</td></tr>
        <tr><td>Tax:</td><td>{invoice.currency} {invoice.tax_amount:.2f}</td></tr>
        <tr style="border-top:2px solid #333">
            <td class="grand-total">Total:</td>
            <td class="grand-total">{invoice.currency} {invoice.total_amount:.2f}</td>
        </tr>
    </table>

    <div class="footer">
        <p>Thank you for your business! &mdash; Brightloop Subscription Management</p>
        <p>This is a computer-generated invoice. No signature required.</p>
    </div>
</body>
</html>"""


# ---------- Overdue detection ----------

def check_overdue_invoices(db: Session) -> list[Invoice]:
    """Mark all unpaid invoices past their due date as 'overdue'.

    Returns the list of invoices that were newly marked overdue.
    """
    today = date.today()
    overdue_candidates = (
        db.query(Invoice)
        .filter(
            Invoice.status.in_(["issued", "partially_paid"]),
            Invoice.due_date < today,
        )
        .all()
    )

    newly_overdue: list[Invoice] = []
    for inv in overdue_candidates:
        inv.status = "overdue"
        newly_overdue.append(inv)

    if newly_overdue:
        db.commit()

    return newly_overdue


def get_overdue_summary(db: Session) -> dict:
    """Return a summary of overdue invoices for the finance dashboard."""
    overdue_invoices = (
        db.query(Invoice)
        .filter(Invoice.status == "overdue")
        .all()
    )
    total_overdue = sum(
        (inv.total_amount - compute_amount_paid(inv, db=db) for inv in overdue_invoices),
        Decimal("0.00"),
    )
    return {
        "overdue_invoices_count": len(overdue_invoices),
        "overdue_amount": _quantize(total_overdue),
        "overdue_invoices": [
            {
                "id": inv.id,
                "invoice_number": inv.invoice_number,
                "customer_name": inv.customer.name if inv.customer else "N/A",
                "total_amount": str(inv.total_amount),
                "due_date": inv.due_date.isoformat(),
                "outstanding": str(compute_outstanding(inv, db=db)),
            }
            for inv in overdue_invoices
        ],
    }
