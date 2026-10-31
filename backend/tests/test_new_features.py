"""Tests for all new features: auth enhancements, portal, discounts,
quotation templates, billing engine, invoice actions, and overdue detection.

Uses a per-function SQLite database to avoid state leakage.
"""

import os
import sys
import uuid

# Ensure the backend package is importable
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

# Override DB to SQLite in-memory before importing anything else
os.environ["DATABASE_URL"] = "sqlite://"

from datetime import date, timedelta
from decimal import Decimal

import pytest
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker

from app.core.database import Base
from app.core.security import hash_password
from app.models import (
    Customer, Invoice, InvoiceItem, Payment, Plan, Product, Subscription, User,
)


# ---------- Fixtures ----------

@pytest.fixture
def db():
    """Create a fresh in-memory SQLite database for each test."""
    engine = create_engine("sqlite://", echo=False)

    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_conn, _):
        cursor = dbapi_conn.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()
    engine.dispose()


@pytest.fixture
def admin_user(db):
    unique_email = f"admin-{uuid.uuid4().hex[:6]}@test.com"
    user = User(
        name="Admin",
        email=unique_email,
        password_hash=hash_password("Admin@123!"),
        role="admin",
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def product_and_plan(db):
    product = Product(name="Test Product", is_active=True)
    db.add(product)
    db.commit()
    db.refresh(product)

    plan = Plan(
        product_id=product.id,
        name="Monthly Plan",
        price=Decimal("999.00"),
        billing_interval="monthly",
        is_active=True,
    )
    db.add(plan)
    db.commit()
    db.refresh(plan)
    return product, plan


@pytest.fixture
def customer(db):
    unique_email = f"customer-{uuid.uuid4().hex[:6]}@test.com"
    cust = Customer(
        name="Test Customer",
        email=unique_email,
        phone="+91-9876543210",
        country="India",
        is_active=True,
    )
    db.add(cust)
    db.commit()
    db.refresh(cust)
    return cust


@pytest.fixture
def active_subscription(db, customer, product_and_plan):
    _, plan = product_and_plan
    today = date.today()
    sub = Subscription(
        customer_id=customer.id,
        plan_id=plan.id,
        status="active",
        start_date=today,
        current_period_start=today,
        current_period_end=today + timedelta(days=30),
        next_billing_date=today + timedelta(days=30),
    )
    db.add(sub)
    db.commit()
    db.refresh(sub)
    return sub


# ============================================================
# 1. Password complexity
# ============================================================

class TestPasswordComplexity:
    def test_valid_password(self):
        from app.schemas.auth import validate_password_complexity
        result = validate_password_complexity("StrongP@ss1")
        assert result == "StrongP@ss1"

    def test_too_short(self):
        from app.schemas.auth import validate_password_complexity
        with pytest.raises(ValueError, match="more than 8 characters"):
            validate_password_complexity("Ab@12345")

    def test_no_uppercase(self):
        from app.schemas.auth import validate_password_complexity
        with pytest.raises(ValueError, match="uppercase"):
            validate_password_complexity("lowercase@123")

    def test_no_lowercase(self):
        from app.schemas.auth import validate_password_complexity
        with pytest.raises(ValueError, match="lowercase"):
            validate_password_complexity("UPPERCASE@123")

    def test_no_special_char(self):
        from app.schemas.auth import validate_password_complexity
        with pytest.raises(ValueError, match="special character"):
            validate_password_complexity("NoSpecial123")


# ============================================================
# 2. Auth service — password reset
# ============================================================

class TestAuthService:
    def test_create_and_use_reset_token(self, db, admin_user):
        from app.services.auth_service import (
            create_password_reset_token,
            reset_user_password,
        )
        # Returns a token string
        token = create_password_reset_token(db, admin_user.email)
        assert isinstance(token, str)
        assert len(token) > 0

        # Reset should return the user object
        user = reset_user_password(db, token, "NewAdmin@123!")
        assert user.id == admin_user.id

    def test_reset_with_invalid_token(self, db):
        from app.services.auth_service import reset_user_password
        with pytest.raises(ValueError, match="Invalid or expired"):
            reset_user_password(db, "invalid-token-xyz", "NewP@ss123!")

    def test_reset_nonexistent_email(self, db):
        from app.services.auth_service import create_password_reset_token
        with pytest.raises(ValueError, match="not found"):
            create_password_reset_token(db, "nonexistent@test.com")


# ============================================================
# 3. Discount rules engine
# ============================================================

class TestDiscountRules:
    def setup_method(self):
        """Reset the in-memory discount rules store for each test."""
        from app.services import discount_service
        discount_service._rules.clear()
        discount_service._loaded = True

    def test_create_and_list(self):
        from app.schemas.discount import DiscountRuleCreate
        from app.services.discount_service import create_discount_rule, list_discount_rules

        rule = create_discount_rule(DiscountRuleCreate(
            code="SUMMER20",
            discount_type="percentage",
            value=Decimal("20"),
            description="Summer sale",
        ))
        assert rule.code == "SUMMER20"
        assert rule.id

        all_rules = list_discount_rules()
        assert len(all_rules) >= 1

    def test_evaluate_percentage_discount(self):
        from app.schemas.discount import DiscountRuleCreate
        from app.services.discount_service import create_discount_rule, evaluate_discounts

        create_discount_rule(DiscountRuleCreate(
            code="FLAT10",
            discount_type="percentage",
            value=Decimal("10"),
        ))
        discount = evaluate_discounts(subtotal=Decimal("1000.00"))
        assert discount == Decimal("100.00")

    def test_evaluate_fixed_discount(self):
        from app.schemas.discount import DiscountRuleCreate
        from app.services.discount_service import create_discount_rule, evaluate_discounts

        create_discount_rule(DiscountRuleCreate(
            code="FLAT50",
            discount_type="fixed",
            value=Decimal("50.00"),
        ))
        discount = evaluate_discounts(subtotal=Decimal("200.00"))
        assert discount == Decimal("50.00")

    def test_min_purchase_filter(self):
        from app.schemas.discount import DiscountRuleCreate
        from app.services.discount_service import create_discount_rule, evaluate_discounts

        create_discount_rule(DiscountRuleCreate(
            code="BIG",
            discount_type="percentage",
            value=Decimal("15"),
            min_purchase=Decimal("500.00"),
        ))
        assert evaluate_discounts(subtotal=Decimal("100.00")) == Decimal("0.00")
        assert evaluate_discounts(subtotal=Decimal("600.00")) == Decimal("90.00")

    def test_max_uses(self):
        from app.schemas.discount import DiscountRuleCreate
        from app.services.discount_service import (
            create_discount_rule, evaluate_discounts, increment_usage,
        )

        create_discount_rule(DiscountRuleCreate(
            code="ONCE",
            discount_type="fixed",
            value=Decimal("25"),
            max_uses=1,
        ))
        assert evaluate_discounts(subtotal=Decimal("100.00")) == Decimal("25.00")
        increment_usage("ONCE")
        assert evaluate_discounts(subtotal=Decimal("100.00")) == Decimal("0.00")


# ============================================================
# 4. Quotation templates
# ============================================================

class TestQuotationTemplates:
    def setup_method(self):
        from app.services import quotation_service
        quotation_service._templates.clear()
        quotation_service._loaded = True

    def test_create_and_retrieve(self):
        from app.schemas.quotation import QuotationTemplateCreate
        from app.services.quotation_service import (
            create_quotation_template,
            get_quotation_template,
            list_quotation_templates,
        )

        tmpl = create_quotation_template(QuotationTemplateCreate(
            name="Enterprise Quote",
            plan_id=1,
            validity_days=30,
            payment_terms="Net 30",
        ))
        assert tmpl.name == "Enterprise Quote"
        assert tmpl.id

        fetched = get_quotation_template(tmpl.id)
        assert fetched is not None
        assert fetched.name == "Enterprise Quote"

        all_templates = list_quotation_templates()
        assert len(all_templates) >= 1

    def test_delete(self):
        from app.schemas.quotation import QuotationTemplateCreate
        from app.services.quotation_service import (
            create_quotation_template,
            delete_quotation_template,
            get_quotation_template,
        )

        tmpl = create_quotation_template(QuotationTemplateCreate(
            name="Temp Quote",
            plan_id=1,
        ))
        assert delete_quotation_template(tmpl.id) is True
        assert get_quotation_template(tmpl.id) is None

    def test_convert_to_subscription(self, db, customer, product_and_plan):
        _, plan = product_and_plan
        from app.schemas.quotation import QuotationTemplateCreate
        from app.services.quotation_service import (
            create_quotation_template,
            convert_template_to_subscription,
        )

        tmpl = create_quotation_template(QuotationTemplateCreate(
            name="Conversion Test",
            plan_id=plan.id,
        ))
        sub = convert_template_to_subscription(db, tmpl.id, customer.id)
        assert sub.plan_id == plan.id
        assert sub.customer_id == customer.id
        assert sub.status == "active"


# ============================================================
# 5. Invoice actions (confirm, cancel, send, print)
# ============================================================

class TestInvoiceActions:
    def _create_draft_invoice(self, db, customer):
        """Helper: create a draft invoice with a unique number."""
        inv_num = f"INV-TEST-{uuid.uuid4().hex[:6]}"
        invoice = Invoice(
            invoice_number=inv_num,
            customer_id=customer.id,
            issue_date=date.today(),
            due_date=date.today() + timedelta(days=30),
            subtotal=Decimal("1000.00"),
            discount_amount=Decimal("0.00"),
            tax_amount=Decimal("180.00"),
            total_amount=Decimal("1180.00"),
            status="draft",
        )
        db.add(invoice)
        db.flush()
        item = InvoiceItem(
            invoice_id=invoice.id,
            description="Test item",
            quantity=1,
            unit_price=Decimal("1000.00"),
            line_total=Decimal("1000.00"),
        )
        db.add(item)
        db.commit()
        db.refresh(invoice)
        return invoice

    def test_confirm_invoice(self, db, customer):
        from app.services.invoice_service import confirm_invoice
        invoice = self._create_draft_invoice(db, customer)
        confirmed = confirm_invoice(db, invoice.id)
        assert confirmed.status == "issued"

    def test_confirm_non_draft_raises(self, db, customer):
        from app.services.invoice_service import confirm_invoice
        invoice = self._create_draft_invoice(db, customer)
        confirm_invoice(db, invoice.id)  # Now it's 'issued'
        with pytest.raises(ValueError, match="must be 'draft'"):
            confirm_invoice(db, invoice.id)

    def test_cancel_invoice(self, db, customer):
        from app.services.invoice_service import cancel_invoice
        invoice = self._create_draft_invoice(db, customer)
        cancelled = cancel_invoice(db, invoice.id)
        assert cancelled.status == "cancelled"

    def test_send_invoice(self, db, customer):
        from app.services.invoice_service import send_invoice
        invoice = self._create_draft_invoice(db, customer)
        result = send_invoice(db, invoice.id)
        assert result["status"] == "sent"
        assert customer.email in result["recipient_email"]

    def test_render_invoice_html(self, db, customer):
        from app.services.invoice_service import render_invoice_html
        invoice = self._create_draft_invoice(db, customer)
        html = render_invoice_html(db, invoice.id)
        assert "Brightloop" in html
        assert invoice.invoice_number in html
        assert "Test item" in html


# ============================================================
# 6. Overdue detection
# ============================================================

class TestOverdueDetection:
    def test_check_overdue(self, db, customer):
        from app.services.invoice_service import check_overdue_invoices, get_overdue_summary

        inv_num = f"INV-OVERDUE-{uuid.uuid4().hex[:6]}"
        invoice = Invoice(
            invoice_number=inv_num,
            customer_id=customer.id,
            issue_date=date.today() - timedelta(days=60),
            due_date=date.today() - timedelta(days=30),
            subtotal=Decimal("500.00"),
            discount_amount=Decimal("0.00"),
            tax_amount=Decimal("90.00"),
            total_amount=Decimal("590.00"),
            status="issued",
        )
        db.add(invoice)
        db.commit()

        newly_overdue = check_overdue_invoices(db)
        assert len(newly_overdue) >= 1

        summary = get_overdue_summary(db)
        assert summary["overdue_invoices_count"] >= 1
        assert summary["overdue_amount"] > 0


# ============================================================
# 7. Billing engine
# ============================================================

class TestBillingEngine:
    def test_generate_due_invoices(self, db, customer, product_and_plan):
        _, plan = product_and_plan
        today = date.today()
        sub = Subscription(
            customer_id=customer.id,
            plan_id=plan.id,
            status="active",
            start_date=today - timedelta(days=30),
            current_period_start=today - timedelta(days=30),
            current_period_end=today,
            next_billing_date=today,
        )
        db.add(sub)
        db.commit()

        from app.services.billing_service import generate_due_invoices
        invoices = generate_due_invoices(db, today)
        assert len(invoices) >= 1
        assert invoices[0].customer_id == customer.id

        db.refresh(sub)
        assert sub.next_billing_date > today


# ============================================================
# 8. Dashboard overdue metrics
# ============================================================

class TestDashboardOverdue:
    def test_dashboard_includes_overdue(self, db):
        from app.services.dashboard_service import get_dashboard_summary
        summary = get_dashboard_summary(db)
        assert hasattr(summary, "overdue_invoices_count")
        assert hasattr(summary, "overdue_amount")
        assert hasattr(summary, "overdue_invoices")
