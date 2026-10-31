"""Subscription plan routes."""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import require_active_user
from app.models.plan import Plan
from app.models.user import User
from app.schemas.plan import PlanCreate, PlanOut, PlanUpdate
from app.services.plan_service import (
    create_plan,
    delete_plan,
    get_plan,
    list_plans,
    update_plan,
)

router = APIRouter(prefix="/api/plans", tags=["Plans"])


def _enrich_plan(plan: Plan) -> PlanOut:
    out = PlanOut.model_validate(plan)
    if plan.product:
        out.product_name = plan.product.name
    return out


@router.post("", response_model=PlanOut, status_code=status.HTTP_201_CREATED)
def create_plan_route(
    data: PlanCreate,
    db: Session = Depends(get_db),
    _user: User = Depends(require_active_user),
):
    """Create a new subscription plan."""
    try:
        plan = create_plan(db, data)
        return _enrich_plan(plan)
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid product or variant reference",
        )


@router.get("", response_model=list[PlanOut])
def list_plans_route(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    active_only: bool = Query(False),
    db: Session = Depends(get_db),
    _user: User = Depends(require_active_user),
):
    """List all subscription plans."""
    plans = list_plans(db, skip=skip, limit=limit, active_only=active_only)
    return [_enrich_plan(p) for p in plans]


@router.get("/{plan_id}", response_model=PlanOut)
def get_plan_route(
    plan_id: int,
    db: Session = Depends(get_db),
    _user: User = Depends(require_active_user),
):
    """Retrieve a plan by ID."""
    plan = get_plan(db, plan_id)
    if plan is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Plan not found")
    return _enrich_plan(plan)


@router.put("/{plan_id}", response_model=PlanOut)
@router.patch("/{plan_id}", response_model=PlanOut)
def update_plan_route(
    plan_id: int,
    data: PlanUpdate,
    db: Session = Depends(get_db),
    _user: User = Depends(require_active_user),
):
    """Update a plan (supports both PUT and PATCH)."""
    plan = get_plan(db, plan_id)
    if plan is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Plan not found")
    updated = update_plan(db, plan, data)
    return _enrich_plan(updated)


@router.delete("/{plan_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_plan_route(
    plan_id: int,
    db: Session = Depends(get_db),
    _user: User = Depends(require_active_user),
):
    """Deactivate a plan (soft-delete)."""
    plan = get_plan(db, plan_id)
    if plan is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Plan not found")
    delete_plan(db, plan)
