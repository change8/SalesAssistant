"""Models for querying existing contracts database."""
from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import Integer, String, DateTime, Text, JSON
from sqlalchemy.orm import Mapped, mapped_column, DeclarativeBase

class ContractsBase(DeclarativeBase):
    """Base for contracts database models."""
    pass

class ExistingContract(ContractsBase):
    """Model for existing contracts in data/contracts.db."""
    __tablename__ = "contracts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    record_uid: Mapped[Optional[str]] = mapped_column(String(128), unique=True, nullable=True)
    contract_number: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(512), nullable=False)
    contract_amount: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    currency: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    customer_name: Mapped[Optional[str]] = mapped_column(String(256), nullable=True)
    project_code: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    signed_at: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    tags: Mapped[Optional[str]] = mapped_column(String(256), nullable=True)
    industry: Mapped[Optional[str]] = mapped_column(String(256), nullable=True)
    harvest_context: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    raw_payload: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    borrow_materials: Mapped[Optional[str]] = mapped_column(String(256), nullable=True)
    collected_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    data_status: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)

    def __repr__(self) -> str:
        return f"<ExistingContract(title={self.title}, customer={self.customer_name})>"
