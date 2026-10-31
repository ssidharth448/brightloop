from datetime import date, datetime, timezone

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    UniqueConstraint,
    String,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Subscription(Base):
    __tablename__ = "subscriptions"

    __table_args__ = (
        CheckConstraint(
            "status IN ('draft', 'active', 'paused', 'cancelled', 'expired')",
            name="ck_subscription_status",
        ),
        CheckConstraint(
            "current_period_end > current_period_start",
            name="ck_subscription_period_dates",
        ),
        UniqueConstraint(
            "id", "customer_id",
            name="uq_subscription_id_customer_id",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    customer_id: Mapped[int] = mapped_column(
        ForeignKey("customers.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )

    plan_id: Mapped[int] = mapped_column(
        ForeignKey("plans.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )

    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="draft", index=True
    )

    start_date: Mapped[date] = mapped_column(
        Date, nullable=False
    )

    current_period_start: Mapped[date] = mapped_column(
        Date, nullable=False
    )

    current_period_end: Mapped[date] = mapped_column(
        Date, nullable=False
    )

    next_billing_date: Mapped[date | None] = mapped_column(
        Date, index=True
    )

    cancel_at_period_end: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False
    )

    cancelled_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True)
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    customer: Mapped["Customer"] = relationship(
        back_populates="subscriptions"
    )

    plan: Mapped["Plan"] = relationship()

    invoices: Mapped[list["Invoice"]] = relationship(
    back_populates="subscription",
    viewonly=True,
)