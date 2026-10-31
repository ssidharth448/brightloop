"""Subscription service — lifecycle management and billing date calculations."""

import calendar
from datetime import date, datetime, timedelta, timezone

from sqlalchemy.orm import Session

from app.models.plan import Plan
from app.models.subscription import Subscription
from app.schemas.subscription import SubscriptionCreate, SubscriptionUpdate

# Valid status transitions
VALID_TRANSITIONS: dict[str, set[str]] = {
    "draft": {"active", "cancelled"},
    "active": {"paused", "cancelled", "expired"},
    "paused": {"active", "cancelled"},
    "cancelled": set(),  # terminal — no transitions out
    "expired": set(),    # terminal — no transitions out
}


def add_interval(d: date, billing_interval: str) -> date:
    """Compute target date after adding the specified billing interval.

    Handles month rollovers and leap years using the calendar standard library.
    """
    if billing_interval == "monthly":
        months = 1
    elif billing_interval == "quarterly":
        months = 3
    elif billing_interval == "yearly":
        months = 12
    else:
        raise ValueError(f"Invalid billing interval: {billing_interval}")

    total_months = d.month + months
    new_year = d.year + (total_months - 1) // 12
    new_month = (total_months - 1) % 12 + 1
    max_day = calendar.monthrange(new_year, new_month)[1]
    new_day = min(d.day, max_day)
    return date(new_year, new_month, new_day)


def create_subscription(db: Session, data: SubscriptionCreate) -> Subscription:
    """Create a new subscription in 'active' status with computed billing dates."""
    plan = db.get(Plan, data.plan_id)
    if plan is None:
        raise ValueError("Plan not found")
    if not plan.is_active:
        raise ValueError("Plan is not active")

    start = data.start_date or date.today()
    trial_end = start + timedelta(days=plan.trial_days) if plan.trial_days > 0 else start

    period_start = trial_end if plan.trial_days > 0 else start
    period_end = add_interval(period_start, plan.billing_interval)
    next_billing = period_end

    subscription = Subscription(
        customer_id=data.customer_id,
        plan_id=data.plan_id,
        status="active",
        start_date=start,
        current_period_start=period_start,
        current_period_end=period_end,
        next_billing_date=next_billing,
    )
    db.add(subscription)
    db.commit()
    db.refresh(subscription)
    return subscription


def list_subscriptions(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    customer_id: int | None = None,
    status: str | None = None,
) -> list[Subscription]:
    q = db.query(Subscription)
    if customer_id is not None:
        q = q.filter(Subscription.customer_id == customer_id)
    if status is not None:
        q = q.filter(Subscription.status == status)
    return q.order_by(Subscription.id.desc()).offset(skip).limit(limit).all()


def get_subscription(db: Session, subscription_id: int) -> Subscription | None:
    return db.get(Subscription, subscription_id)


def update_subscription(
    db: Session, subscription: Subscription, data: SubscriptionUpdate
) -> Subscription:
    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(subscription, field, value)
    db.commit()
    db.refresh(subscription)
    return subscription


def _transition(subscription: Subscription, target: str) -> None:
    """Validate and perform a status transition."""
    allowed = VALID_TRANSITIONS.get(subscription.status, set())
    if target not in allowed:
        raise ValueError(
            f"Cannot transition from '{subscription.status}' to '{target}'"
        )
    subscription.status = target


def activate_subscription(db: Session, subscription: Subscription) -> Subscription:
    """Activate a draft or paused subscription."""
    _transition(subscription, "active")
    if subscription.status == "active":
        # If resuming from paused, recalculate next billing from today
        today = date.today()
        plan = db.get(Plan, subscription.plan_id)
        if plan:
            period_end = add_interval(today, plan.billing_interval)
            subscription.current_period_start = today
            subscription.current_period_end = period_end
            subscription.next_billing_date = period_end
    db.commit()
    db.refresh(subscription)
    return subscription


def pause_subscription(db: Session, subscription: Subscription) -> Subscription:
    """Pause an active subscription."""
    _transition(subscription, "paused")
    subscription.next_billing_date = None  # No billing while paused
    db.commit()
    db.refresh(subscription)
    return subscription


def resume_subscription(db: Session, subscription: Subscription) -> Subscription:
    """Resume a paused subscription (transition to active)."""
    _transition(subscription, "active")
    today = date.today()
    plan = db.get(Plan, subscription.plan_id)
    if plan:
        period_end = add_interval(today, plan.billing_interval)
        subscription.current_period_start = today
        subscription.current_period_end = period_end
        subscription.next_billing_date = period_end
    db.commit()
    db.refresh(subscription)
    return subscription


def cancel_subscription(db: Session, subscription: Subscription) -> Subscription:
    """Cancel a subscription."""
    _transition(subscription, "cancelled")
    subscription.cancelled_at = datetime.now(timezone.utc)
    subscription.next_billing_date = None
    db.commit()
    db.refresh(subscription)
    return subscription
