"""Seed script to populate initial demo data into the database."""

from datetime import date
from decimal import Decimal

from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.models.user import User
from app.schemas.auth import UserRegister
from app.schemas.customer import CustomerCreate
from app.schemas.invoice import InvoiceCreate
from app.schemas.payment import PaymentCreate
from app.schemas.plan import PlanCreate
from app.schemas.product import ProductCreate, VariantCreate
from app.schemas.subscription import SubscriptionCreate
from app.services.auth_service import register_user
from app.services.customer_service import create_customer
from app.services.invoice_service import create_invoice
from app.services.payment_service import record_payment
from app.services.plan_service import create_plan
from app.services.product_service import create_product, create_variant
from app.services.subscription_service import create_subscription


def seed_database(db: Session | None = None) -> None:
    close_db = False
    if db is None:
        db = SessionLocal()
        close_db = True

    try:
        # 1. Admin & Staff Users
        admin_email = "admin@brightloop.com"
        existing_admin = db.query(User).filter(User.email == admin_email).first()
        if not existing_admin:
            register_user(
                db,
                UserRegister(
                    name="Brightloop Admin",
                    email=admin_email,
                    password="admin123",
                    role="admin",
                ),
            )
            print("✓ Created default admin user: admin@brightloop.com / admin123")

        staff_email = "user@brightloop.com"
        existing_staff = db.query(User).filter(User.email == staff_email).first()
        if not existing_staff:
            register_user(
                db,
                UserRegister(
                    name="Alex Morgan",
                    email=staff_email,
                    password="user123",
                    role="staff",
                ),
            )
            print("✓ Created default staff user: user@brightloop.com / user123")

        # Check if products already seeded
        from app.models.product import Product
        if db.query(Product).count() > 0:
            print("Database already contains data; skipping entity seeding.")
            return

        # 2. Products & Variants
        p1 = create_product(
            db,
            ProductCreate(
                name="Brightloop CRM",
                description="Customer relationship suite for modern sales and client teams.",
                base_price=Decimal("1200.00"),
                is_active=True,
            ),
        )
        v1 = create_variant(
            db,
            p1.id,
            VariantCreate(name="Starter (5 seats)", sku="CRM-S5", extra_price=Decimal("0.00")),
        )
        v2 = create_variant(
            db,
            p1.id,
            VariantCreate(name="Team (25 seats)", sku="CRM-T25", extra_price=Decimal("800.00")),
        )

        p2 = create_product(
            db,
            ProductCreate(
                name="Support Desk",
                description="Shared omnichannel team inbox, ticket automation, and SLA tracking.",
                base_price=Decimal("600.00"),
                is_active=True,
            ),
        )

        p3 = create_product(
            db,
            ProductCreate(
                name="Analytics Pro",
                description="Real-time recurring billing metrics, cohort retention, and churn analysis.",
                base_price=Decimal("2500.00"),
                is_active=True,
            ),
        )

        # 3. Plans
        plan_crm_monthly = create_plan(
            db,
            PlanCreate(
                product_id=p1.id,
                variant_id=v1.id,
                name="CRM Monthly",
                price=Decimal("1200.00"),
                billing_interval="monthly",
                is_active=True,
            ),
        )
        plan_crm_yearly = create_plan(
            db,
            PlanCreate(
                product_id=p1.id,
                variant_id=v2.id,
                name="CRM Team Yearly",
                price=Decimal("20000.00"),
                billing_interval="yearly",
                is_active=True,
            ),
        )
        plan_support_monthly = create_plan(
            db,
            PlanCreate(
                product_id=p2.id,
                name="Support Desk Monthly",
                price=Decimal("600.00"),
                billing_interval="monthly",
                is_active=True,
            ),
        )
        create_plan(
            db,
            PlanCreate(
                product_id=p3.id,
                name="Analytics Pro Monthly",
                price=Decimal("2500.00"),
                billing_interval="monthly",
                is_active=True,
            ),
        )

        # 4. Customers
        c1 = create_customer(
            db,
            CustomerCreate(
                name="Asha Menon",
                email="asha@kaveritextiles.in",
                phone="+91 98470 11223",
                company="Kaveri Textiles",
                city="Kochi",
                state="Kerala",
                country="India",
            ),
        )
        c2 = create_customer(
            db,
            CustomerCreate(
                name="Rohan Iyer",
                email="rohan@palakkadfoods.in",
                phone="+91 98950 44821",
                company="Palakkad Foods",
                city="Palakkad",
                state="Kerala",
                country="India",
            ),
        )
        c3 = create_customer(
            db,
            CustomerCreate(
                name="Meera Nair",
                email="meera@greenleaf.co",
                phone="+91 94960 77310",
                company="Greenleaf Studio",
                city="Bengaluru",
                state="Karnataka",
                country="India",
            ),
        )

        # 5. Subscriptions
        sub1 = create_subscription(
            db,
            SubscriptionCreate(
                customer_id=c1.id,
                plan_id=plan_crm_monthly.id,
                start_date=date.today(),
            ),
        )
        sub2 = create_subscription(
            db,
            SubscriptionCreate(
                customer_id=c2.id,
                plan_id=plan_support_monthly.id,
                start_date=date.today(),
            ),
        )
        create_subscription(
            db,
            SubscriptionCreate(
                customer_id=c3.id,
                plan_id=plan_crm_yearly.id,
                start_date=date.today(),
            ),
        )

        # 6. Invoices
        inv1 = create_invoice(
            db,
            InvoiceCreate(
                customer_id=c1.id,
                subscription_id=sub1.id,
            ),
        )
        inv2 = create_invoice(
            db,
            InvoiceCreate(
                customer_id=c2.id,
                subscription_id=sub2.id,
            ),
        )

        # 7. Payments
        record_payment(
            db,
            inv1,
            PaymentCreate(
                amount=inv1.total_amount,
                payment_method="upi",
            ),
        )

        print("✓ Database successfully seeded with sample products, plans, customers, subscriptions, invoices, and payments!")

    finally:
        if close_db:
            db.close()


if __name__ == "__main__":
    seed_database()
