from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Customer(Base):
    __tablename__ = "customers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    name: Mapped[str] = mapped_column(String(150), nullable=False)

    email: Mapped[str] = mapped_column(
        String(255), nullable=False, unique=True, index=True
    )

    phone: Mapped[str | None] = mapped_column(String(30))

    billing_address: Mapped[str | None] = mapped_column(Text)

    city: Mapped[str | None] = mapped_column(String(100))

    state: Mapped[str | None] = mapped_column(String(100))

    postal_code: Mapped[str | None] = mapped_column(String(20))

    country: Mapped[str] = mapped_column(
        String(100), nullable=False, default="India"
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True
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

    subscriptions: Mapped[list["Subscription"]] = relationship(
        back_populates="customer"
    )

    invoices: Mapped[list["Invoice"]] = relationship(
        back_populates="customer"
    )