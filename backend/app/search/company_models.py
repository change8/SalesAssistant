"""Models for querying company data from contracts.db."""
from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import Integer, String, DateTime, Text, REAL
from sqlalchemy.orm import Mapped, mapped_column
from backend.app.search.contracts_models import ContractsBase


class Company(ContractsBase):
    """Model for companies table."""
    __tablename__ = "companies"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    business_type: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    total_count: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    code: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    qualification_count: Mapped[Optional[int]] = mapped_column(Integer, nullable=True, default=0)
    ip_count: Mapped[Optional[int]] = mapped_column(Integer, nullable=True, default=0)
    legal_person: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    setup_date: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    registered_capital: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    currency: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    head_office: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    nuccn: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    registered_address: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    operating_period: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    headcount: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    registered_city: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    operating_state: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    unregister_date: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    company_type: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    company_category: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    english_name: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    shorthand: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    prev_name: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    business_scope: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    data_status: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    def __repr__(self) -> str:
        return f"<Company(name={self.name}, code={self.code})>"
