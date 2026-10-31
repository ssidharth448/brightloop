"""Quotation template routes — CRUD and convert-to-subscription."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import require_active_user
from app.models.user import User
from app.schemas.quotation import (
    QuotationConvertRequest,
    QuotationTemplateCreate,
    QuotationTemplateOut,
    QuotationTemplateUpdate,
)
from app.schemas.subscription import SubscriptionOut
from app.services.quotation_service import (
    convert_template_to_subscription,
    create_quotation_template,
    delete_quotation_template,
    get_quotation_template,
    list_quotation_templates,
    update_quotation_template,
)

router = APIRouter(prefix="/api/quotation-templates", tags=["Quotation Templates"])


@router.post("", response_model=QuotationTemplateOut, status_code=status.HTTP_201_CREATED)
def create_template(
    data: QuotationTemplateCreate,
    _user: User = Depends(require_active_user),
):
    """Create a new quotation template."""
    return create_quotation_template(data)


@router.get("", response_model=list[QuotationTemplateOut])
def list_templates(_user: User = Depends(require_active_user)):
    """List all quotation templates."""
    return list_quotation_templates()


@router.get("/{template_id}", response_model=QuotationTemplateOut)
def get_template(
    template_id: str,
    _user: User = Depends(require_active_user),
):
    """Get a quotation template by ID."""
    tmpl = get_quotation_template(template_id)
    if tmpl is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Template not found")
    return tmpl


@router.put("/{template_id}", response_model=QuotationTemplateOut)
def update_template(
    template_id: str,
    data: QuotationTemplateUpdate,
    _user: User = Depends(require_active_user),
):
    """Update a quotation template."""
    tmpl = update_quotation_template(template_id, data)
    if tmpl is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Template not found")
    return tmpl


@router.delete("/{template_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_template(
    template_id: str,
    _user: User = Depends(require_active_user),
):
    """Delete a quotation template."""
    if not delete_quotation_template(template_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Template not found")


# ---------- Convert to subscription ----------

@router.post("/convert-to-subscription", response_model=SubscriptionOut)
def convert_to_subscription(
    data: QuotationConvertRequest,
    db: Session = Depends(get_db),
    _user: User = Depends(require_active_user),
):
    """Convert a quotation template into a live subscription."""
    try:
        sub = convert_template_to_subscription(
            db,
            template_id=data.template_id,
            customer_id=data.customer_id,
            start_date=data.start_date,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    out = SubscriptionOut.model_validate(sub)
    if sub.customer:
        out.customer_name = sub.customer.name
    if sub.plan:
        out.plan_name = sub.plan.name
        out.price = sub.plan.price
        out.billing_interval = sub.plan.billing_interval
        out.interval = sub.plan.billing_interval
    return out
