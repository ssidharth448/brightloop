"""Customer service — CRUD operations."""

from sqlalchemy.orm import Session

from app.models.customer import Customer
from app.schemas.customer import CustomerCreate, CustomerUpdate


def create_customer(db: Session, data: CustomerCreate) -> Customer:
    customer = Customer(**data.model_dump())
    db.add(customer)
    db.commit()
    db.refresh(customer)
    return customer


def list_customers(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    active_only: bool = False,
) -> list[Customer]:
    q = db.query(Customer)
    if active_only:
        q = q.filter(Customer.is_active.is_(True))
    return q.order_by(Customer.id).offset(skip).limit(limit).all()


def get_customer(db: Session, customer_id: int) -> Customer | None:
    return db.get(Customer, customer_id)


def update_customer(
    db: Session, customer: Customer, data: CustomerUpdate
) -> Customer:
    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(customer, field, value)
    db.commit()
    db.refresh(customer)
    return customer


def deactivate_customer(db: Session, customer: Customer) -> None:
    """Soft-delete by deactivating the customer."""
    customer.is_active = False
    db.commit()
