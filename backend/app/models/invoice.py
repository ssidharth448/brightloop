from datetime import date, datetime, timezone
from decimal import Decimal

from sqlalchemy import (
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    ForeignKeyConstraint,
    Integer,
    Numeric,
    String,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Invoice(Base):
    __tablename__ = "invoices"

    __table_args__ = (
        CheckConstraint(
            "status IN ('draft', 'issued', 'partially_paid', "
            "'paid', 'overdue', 'cancelled')",
            name="ck_invoice_status",
        ),
        CheckConstraint(
            "subtotal >= 0 AND discount_amount >= 0 "
            "AND tax_amount >= 0 AND total_amount >= 0",
            name="ck_invoice_amounts_nonnegative",
        ),
        CheckConstraint(
            "discount_amount <= subtotal",
            name="ck_invoice_discount_limit",
        ),
        CheckConstraint(
            "total_amount = subtotal - discount_amount + tax_amount",
            name="ck_invoice_total_calculation",
        ),
        CheckConstraint(
            "due_date >= issue_date",
            name="ck_invoice_due_date",
        ),
        ForeignKeyConstraint(
            ["subscription_id", "customer_id"],
            ["subscriptions.id", "subscriptions.customer_id"],
            name="fk_invoice_subscription_customer",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    invoice_number: Mapped[str] = mapped_column(
        String(50), nullable=False, unique=True
    )

    customer_id: Mapped[int] = mapped_column(
        ForeignKey("customers.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )

    # Nullable to support invoices that are not linked to subscriptions.
    subscription_id: Mapped[int | None] = mapped_column(
        Integer, nullable=True, index=True
    )

    issue_date: Mapped[date] = mapped_column(Date, nullable=False)

    due_date: Mapped[date] = mapped_column(Date, nullable=False)

    currency: Mapped[str] = mapped_column(
        String(3), nullable=False, default="INR"
    )

    subtotal: Mapped[Decimal] = mapped_column(
        Numeric(12, 2), nullable=False
    )

    discount_amount: Mapped[Decimal] = mapped_column(
        Numeric(12, 2), nullable=False, default=Decimal("0.00")
    )

    tax_amount: Mapped[Decimal] = mapped_column(
        Numeric(12, 2), nullable=False, default=Decimal("0.00")
    )

    total_amount: Mapped[Decimal] = mapped_column(
        Numeric(12, 2), nullable=False
    )

    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="draft", index=True
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    customer: Mapped["Customer"] = relationship(
        back_populates="invoices"
    )

    subscription: Mapped["Subscription | None"] = relationship(
    back_populates="invoices",
    viewonly=True,
)

    items: Mapped[list["InvoiceItem"]] = relationship(
        back_populates="invoice",
        cascade="all, delete-orphan",
    )

    payments: Mapped[list["Payment"]] = relationship(
        back_populates="invoice"
    )


class InvoiceItem(Base):
    __tablename__ = "invoice_items"

    __table_args__ = (
        CheckConstraint(
            "quantity > 0",
            name="ck_invoice_item_quantity_positive",
        ),
        CheckConstraint(
            "unit_price >= 0 AND line_total >= 0",
            name="ck_invoice_item_amounts_nonnegative",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    invoice_id: Mapped[int] = mapped_column(
        ForeignKey("invoices.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Snapshots preserve the description even if the product or plan changes.
    description: Mapped[str] = mapped_column(
        String(255), nullable=False
    )

    quantity: Mapped[int] = mapped_column(
        Integer, nullable=False, default=1
    )

    unit_price: Mapped[Decimal] = mapped_column(
        Numeric(12, 2), nullable=False
    )

    line_total: Mapped[Decimal] = mapped_column(
        Numeric(12, 2), nullable=False
    )

    invoice: Mapped["Invoice"] = relationship(
        back_populates="items"
    )