"""Discount rules routes — admin CRUD for discount rules engine."""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import require_admin
from app.models.user import User
from app.schemas.discount import DiscountRuleCreate, DiscountRuleOut, DiscountRuleUpdate
from app.services.discount_service import (
    create_discount_rule,
    delete_discount_rule,
    get_discount_rule,
    list_discount_rules,
    update_discount_rule,
)

router = APIRouter(prefix="/api/discounts", tags=["Discount Rules"])


@router.post("", response_model=DiscountRuleOut, status_code=status.HTTP_201_CREATED)
def create_rule(
    data: DiscountRuleCreate,
    _admin: User = Depends(require_admin),
):
    """Create a new discount rule (admin only)."""
    return create_discount_rule(data)


@router.get("", response_model=list[DiscountRuleOut])
def list_rules(
    active_only: bool = Query(False),
    _admin: User = Depends(require_admin),
):
    """List all discount rules."""
    return list_discount_rules(active_only=active_only)


@router.get("/{rule_id}", response_model=DiscountRuleOut)
def get_rule(
    rule_id: str,
    _admin: User = Depends(require_admin),
):
    """Get a single discount rule."""
    rule = get_discount_rule(rule_id)
    if rule is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Discount rule not found")
    return rule


@router.put("/{rule_id}", response_model=DiscountRuleOut)
def update_rule(
    rule_id: str,
    data: DiscountRuleUpdate,
    _admin: User = Depends(require_admin),
):
    """Update a discount rule."""
    rule = update_discount_rule(rule_id, data)
    if rule is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Discount rule not found")
    return rule


@router.delete("/{rule_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_rule(
    rule_id: str,
    _admin: User = Depends(require_admin),
):
    """Delete a discount rule."""
    if not delete_discount_rule(rule_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Discount rule not found")
