"""Common SQLAlchemy mixins and utilities."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, String, Float, func
from sqlalchemy.orm import Mapped, mapped_column

from backend.app.core.database import Base


class TimestampMixin:
    """Reusable columns for created/updated timestamps."""

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )


class ExchangeRate(Base):
    """Exchange rate model for currency conversion."""
    __tablename__ = "exchange_rates"

    currency_code: Mapped[str] = mapped_column(String(3), primary_key=True)  # USD, JPY, EUR, etc.
    rate_to_cny: Mapped[float] = mapped_column(Float, nullable=False)  # Conversion rate to CNY
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)

    def __repr__(self) -> str:
        return f"<ExchangeRate({self.currency_code}={self.rate_to_cny} CNY)>"
