"""Plan service — CRUD operations for subscription plans."""

from sqlalchemy.orm import Session

from app.models.plan import Plan
from app.schemas.plan import PlanCreate, PlanUpdate


def create_plan(db: Session, data: PlanCreate) -> Plan:
    plan = Plan(**data.model_dump())
    db.add(plan)
    db.commit()
    db.refresh(plan)
    return plan


def list_plans(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    active_only: bool = False,
) -> list[Plan]:
    q = db.query(Plan)
    if active_only:
        q = q.filter(Plan.is_active.is_(True))
    return q.order_by(Plan.id).offset(skip).limit(limit).all()


def get_plan(db: Session, plan_id: int) -> Plan | None:
    return db.get(Plan, plan_id)


def update_plan(db: Session, plan: Plan, data: PlanUpdate) -> Plan:
    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(plan, field, value)
    db.commit()
    db.refresh(plan)
    return plan


def delete_plan(db: Session, plan: Plan) -> None:
    """Soft-delete by deactivating the plan."""
    plan.is_active = False
    db.commit()
