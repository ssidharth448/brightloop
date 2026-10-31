"""Subscription routes — lifecycle management."""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import require_active_user
from app.models.user import User
from app.schemas.subscription import (
    SubscriptionCreate,
    SubscriptionOut,
    SubscriptionUpdate,
)
from app.services.subscription_service import (
    activate_subscription,
    cancel_subscription,
    create_subscription,
    get_subscription,
    list_subscriptions,
    pause_subscription,
    resume_subscription,
    update_subscription,
)

router = APIRouter(prefix="/api/subscriptions", tags=["Subscriptions"])


def _enrich_sub(sub) -> SubscriptionOut:
    out = SubscriptionOut.model_validate(sub)
    if sub.customer:
        out.customer_name = sub.customer.name
    if sub.plan:
        out.plan_name = sub.plan.name
        out.price = sub.plan.price
        out.billing_interval = sub.plan.billing_interval
        out.interval = sub.plan.billing_interval
    return out


@router.post("", response_model=SubscriptionOut, status_code=status.HTTP_201_CREATED)
def create_subscription_route(
    data: SubscriptionCreate,
    db: Session = Depends(get_db),
    _user: User = Depends(require_active_user),
):
    """Create a new subscription (active by default)."""
    try:
        sub = create_subscription(db, data)
        return _enrich_sub(sub)
    except (ValueError, IntegrityError) as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )


@router.get("", response_model=list[SubscriptionOut])
def list_subscriptions_route(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    customer_id: int | None = Query(None),
    subscription_status: str | None = Query(None, alias="status"),
    db: Session = Depends(get_db),
    _user: User = Depends(require_active_user),
):
    """List subscriptions with optional filters."""
    subs = list_subscriptions(
        db,
        skip=skip,
        limit=limit,
        customer_id=customer_id,
        status=subscription_status,
    )
    return [_enrich_sub(s) for s in subs]


@router.get("/{subscription_id}", response_model=SubscriptionOut)
def get_subscription_route(
    subscription_id: int,
    db: Session = Depends(get_db),
    _user: User = Depends(require_active_user),
):
    """Retrieve a subscription by ID."""
    sub = get_subscription(db, subscription_id)
    if sub is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Subscription not found"
        )
    return _enrich_sub(sub)


@router.put("/{subscription_id}", response_model=SubscriptionOut)
def update_subscription_route(
    subscription_id: int,
    data: SubscriptionUpdate,
    db: Session = Depends(get_db),
    _user: User = Depends(require_active_user),
):
    """Update a subscription."""
    sub = get_subscription(db, subscription_id)
    if sub is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Subscription not found"
        )
    updated = update_subscription(db, sub, data)
    return _enrich_sub(updated)


@router.post("/{subscription_id}/activate", response_model=SubscriptionOut)
def activate_subscription_route(
    subscription_id: int,
    db: Session = Depends(get_db),
    _user: User = Depends(require_active_user),
):
    """Activate a draft subscription."""
    sub = get_subscription(db, subscription_id)
    if sub is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Subscription not found"
        )
    try:
        updated = activate_subscription(db, sub)
        return _enrich_sub(updated)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))


@router.post("/{subscription_id}/pause", response_model=SubscriptionOut)
def pause_subscription_route(
    subscription_id: int,
    db: Session = Depends(get_db),
    _user: User = Depends(require_active_user),
):
    """Pause an active subscription."""
    sub = get_subscription(db, subscription_id)
    if sub is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Subscription not found"
        )
    try:
        updated = pause_subscription(db, sub)
        return _enrich_sub(updated)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))


@router.post("/{subscription_id}/resume", response_model=SubscriptionOut)
def resume_subscription_route(
    subscription_id: int,
    db: Session = Depends(get_db),
    _user: User = Depends(require_active_user),
):
    """Resume a paused subscription."""
    sub = get_subscription(db, subscription_id)
    if sub is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Subscription not found"
        )
    try:
        updated = resume_subscription(db, sub)
        return _enrich_sub(updated)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))


@router.post("/{subscription_id}/cancel", response_model=SubscriptionOut)
def cancel_subscription_route(
    subscription_id: int,
    db: Session = Depends(get_db),
    _user: User = Depends(require_active_user),
):
    """Cancel a subscription."""
    sub = get_subscription(db, subscription_id)
    if sub is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Subscription not found"
        )
    try:
        updated = cancel_subscription(db, sub)
        return _enrich_sub(updated)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
