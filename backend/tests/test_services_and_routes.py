"""Direct integration tests for all route handlers and business logic services."""

from decimal import Decimal
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import app.models
from app.core.database import Base
from app.routes.auth import login, register
from app.routes.customers import create_customer_route, list_customers_route, get_customer_route
from app.routes.dashboard import dashboard_summary
from app.routes.invoices import create_invoice_route, get_invoice_route, list_invoices_route
from app.routes.payments import create_payment_route, list_payments_route
from app.routes.plans import create_plan_route, list_plans_route
from app.routes.products import (
    create_product_route,
    create_variant_route,
    list_products_route,
    list_variants_route,
)
from app.routes.subscriptions import (
    activate_subscription_route,
    cancel_subscription_route,
    create_subscription_route,
    get_subscription_route,
    list_subscriptions_route,
    pause_subscription_route,
    resume_subscription_route,
)
from app.schemas.auth import UserLogin, UserRegister
from app.schemas.customer import CustomerCreate
from app.schemas.invoice import InvoiceCreate, InvoiceItemCreate
from app.schemas.payment import PaymentCreate
from app.schemas.plan import PlanCreate
from app.schemas.product import ProductCreate, VariantCreate
from app.schemas.subscription import SubscriptionCreate


@pytest.fixture
def db_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    session_factory = sessionmaker(bind=engine)
    session = session_factory()
    yield session
    session.close()


def test_auth_and_registration(db_session):
    u = register(
        UserRegister(
            name="Admin User",
            email="admin@brightloop.com",
            password="Password123!",
            role="admin",
        ),
        db=db_session,
    )
    assert u.id == 1
    assert u.email == "admin@brightloop.com"
    assert u.role == "admin"

    tok = login(
        UserLogin(email="admin@brightloop.com", password="Password123!"),
        db=db_session,
    )
    assert tok.token_type == "bearer"
    assert len(tok.access_token) > 20


def test_complete_subscription_workflow(db_session):
    # 1. Admin user
    admin = register(
        UserRegister(
            name="Admin User",
            email="admin2@brightloop.com",
            password="Password123!",
            role="admin",
        ),
        db=db_session,
    )

    # 2. Product
    prod = create_product_route(
        ProductCreate(
            name="Brightloop Analytics",
            description="Analytics Suite",
            category="SaaS",
        ),
        db=db_session,
        _user=admin,
    )
    assert prod.id == 1
    assert prod.name == "Brightloop Analytics"

    # 3. Product Variant
    var = create_variant_route(
        product_id=prod.id,
        data=VariantCreate(name="Standard", sku="ANL-STD"),
        db=db_session,
        _user=admin,
    )
    assert var.id == 1
    assert var.sku == "ANL-STD"

    # 4. Plan
    plan = create_plan_route(
        PlanCreate(
            product_id=prod.id,
            variant_id=var.id,
            name="Analytics Monthly",
            price=Decimal("1200.00"),
            currency="INR",
            billing_interval="monthly",
            trial_days=0,
        ),
        db=db_session,
        _user=admin,
    )
    assert plan.id == 1
    assert plan.price == Decimal("1200.00")

    # 5. Customer
    cust = create_customer_route(
        CustomerCreate(
            name="Globex Corp",
            email="billing@globex.com",
            phone="+919988776655",
            billing_address="100 Tech Blvd",
            city="Pune",
            state="Maharashtra",
            country="India",
        ),
        db=db_session,
        _user=admin,
    )
    assert cust.id == 1
    assert cust.email == "billing@globex.com"

    # 6. Subscribe Customer
    sub = create_subscription_route(
        SubscriptionCreate(
            customer_id=cust.id,
            plan_id=plan.id,
        ),
        db=db_session,
        _user=admin,
    )
    assert sub.id == 1
    assert sub.status == "active"
    assert sub.current_period_end > sub.current_period_start
    assert sub.next_billing_date == sub.current_period_end

    # 7. Pause and Resume Subscription
    paused_sub = pause_subscription_route(sub.id, db=db_session, _user=admin)
    assert paused_sub.status == "paused"
    assert paused_sub.next_billing_date is None

    resumed_sub = resume_subscription_route(sub.id, db=db_session, _user=admin)
    assert resumed_sub.status == "active"
    assert resumed_sub.next_billing_date is not None

    # 8. Generate Invoice
    inv = create_invoice_route(
        InvoiceCreate(
            customer_id=cust.id,
            subscription_id=sub.id,
            currency="INR",
            items=[
                InvoiceItemCreate(
                    description="Analytics Monthly Plan",
                    quantity=1,
                    unit_price=Decimal("1200.00"),
                )
            ],
            discount_amount=Decimal("200.00"),  # Taxable = 1000.00
            tax_rate=Decimal("18.0"),           # Tax = 180.00, Total = 1180.00
        ),
        db=db_session,
        _user=admin,
    )
    assert inv["subtotal"] == Decimal("1200.00")
    assert inv["discount_amount"] == Decimal("200.00")
    assert inv["tax_amount"] == Decimal("180.00")
    assert inv["total_amount"] == Decimal("1180.00")
    assert inv["amount_paid"] == Decimal("0.00")
    assert inv["outstanding_balance"] == Decimal("1180.00")
    assert inv["status"] == "issued"

    invoice_id = inv["id"]

    # 9. Record Partial Payment (500.00)
    pay1 = create_payment_route(
        invoice_id=invoice_id,
        data=PaymentCreate(
            amount=Decimal("500.00"),
            payment_method="upi",
            transaction_reference="UPI_TXN_001",
        ),
        db=db_session,
        _user=admin,
    )
    assert pay1.status == "succeeded"

    inv_after_pay1 = get_invoice_route(invoice_id, db=db_session, _user=admin)
    assert inv_after_pay1["status"] == "partially_paid"
    assert inv_after_pay1["amount_paid"] == Decimal("500.00")
    assert inv_after_pay1["outstanding_balance"] == Decimal("680.00")

    # 10. Record Final Payment (680.00)
    pay2 = create_payment_route(
        invoice_id=invoice_id,
        data=PaymentCreate(
            amount=Decimal("680.00"),
            payment_method="bank_transfer",
            transaction_reference="NEFT_TXN_002",
        ),
        db=db_session,
        _user=admin,
    )
    assert pay2.status == "succeeded"

    inv_after_pay2 = get_invoice_route(invoice_id, db=db_session, _user=admin)
    assert inv_after_pay2["status"] == "paid"
    assert inv_after_pay2["amount_paid"] == Decimal("1180.00")
    assert inv_after_pay2["outstanding_balance"] == Decimal("0.00")

    # 11. Dashboard Summary
    dash = dashboard_summary(db=db_session, _user=admin)
    assert dash.total_customers == 1
    assert dash.active_subscriptions == 1
    assert dash.monthly_recurring_revenue == Decimal("1200.00")
    assert dash.total_invoices == 1
    assert dash.outstanding_invoice_amount == Decimal("0.00")
    assert dash.total_payments_received == Decimal("1180.00")
    assert len(dash.recent_subscriptions) == 1
    assert len(dash.recent_payments) == 2
