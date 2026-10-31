"""Customer routes."""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import require_active_user
from app.models.user import User
from app.schemas.customer import CustomerCreate, CustomerOut, CustomerUpdate
from app.services.customer_service import (
    create_customer,
    deactivate_customer,
    get_customer,
    list_customers,
    update_customer,
)

router = APIRouter(prefix="/api/customers", tags=["Customers"])


@router.post("", response_model=CustomerOut, status_code=status.HTTP_201_CREATED)
def create_customer_route(
    data: CustomerCreate,
    db: Session = Depends(get_db),
    _user: User = Depends(require_active_user),
):
    """Register a new customer."""
    try:
        customer = create_customer(db, data)
        return CustomerOut.model_validate(customer)
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A customer with this email already exists",
        )


@router.get("", response_model=list[CustomerOut])
def list_customers_route(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    active_only: bool = Query(False),
    db: Session = Depends(get_db),
    _user: User = Depends(require_active_user),
):
    """List all customers."""
    customers = list_customers(db, skip=skip, limit=limit, active_only=active_only)
    return [CustomerOut.model_validate(c) for c in customers]


@router.get("/{customer_id}", response_model=CustomerOut)
def get_customer_route(
    customer_id: int,
    db: Session = Depends(get_db),
    _user: User = Depends(require_active_user),
):
    """Retrieve a customer by ID."""
    customer = get_customer(db, customer_id)
    if customer is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Customer not found"
        )
    return CustomerOut.model_validate(customer)


@router.put("/{customer_id}", response_model=CustomerOut)
@router.patch("/{customer_id}", response_model=CustomerOut)
def update_customer_route(
    customer_id: int,
    data: CustomerUpdate,
    db: Session = Depends(get_db),
    _user: User = Depends(require_active_user),
):
    """Update a customer."""
    customer = get_customer(db, customer_id)
    if customer is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Customer not found"
        )
    try:
        updated = update_customer(db, customer, data)
        return CustomerOut.model_validate(updated)
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A customer with this email already exists",
        )


@router.delete("/{customer_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_customer_route(
    customer_id: int,
    db: Session = Depends(get_db),
    _user: User = Depends(require_active_user),
):
    """Deactivate a customer (soft-delete)."""
    customer = get_customer(db, customer_id)
    if customer is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Customer not found"
        )
    deactivate_customer(db, customer)
