from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    ForeignKeyConstraint,
    Integer,
    Numeric,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Plan(Base):
    __tablename__ = "plans"

    __table_args__ = (
        CheckConstraint(
            "price >= 0",
            name="ck_plan_price_nonnegative",
        ),
        CheckConstraint(
            "billing_interval IN ('monthly', 'quarterly', 'yearly')",
            name="ck_plan_billing_interval",
        ),
        CheckConstraint(
            "trial_days >= 0",
            name="ck_plan_trial_days_nonnegative",
        ),
        CheckConstraint(
            "length(currency) = 3",
            name="ck_plan_currency_length",
        ),
        ForeignKeyConstraint(
            ["product_id", "variant_id"],
            ["product_variants.product_id", "product_variants.id"],
            name="fk_plan_variant_belongs_to_product",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    product_id: Mapped[int] = mapped_column(
        ForeignKey("products.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )

    variant_id: Mapped[int | None] = mapped_column(
        Integer, nullable=True, index=True
    )

    name: Mapped[str] = mapped_column(String(150), nullable=False)

    description: Mapped[str | None] = mapped_column(Text)

    price: Mapped[Decimal] = mapped_column(
        Numeric(12, 2), nullable=False
    )

    currency: Mapped[str] = mapped_column(
        String(3), nullable=False, default="INR"
    )

    billing_interval: Mapped[str] = mapped_column(
        String(20), nullable=False
    )

    trial_days: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    product: Mapped["Product"] = relationship(
        back_populates="plans"
    )

    variant: Mapped["ProductVariant | None"] = relationship(
    back_populates="plans",
    viewonly=True,
)