"""Models for querying existing assets (qualifications & IP) database."""
from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import Integer, String, DateTime, Text
from sqlalchemy.orm import Mapped, mapped_column

from backend.app.search.contracts_models import ContractsBase

class ExistingAsset(ContractsBase):
    """Model for existing assets (qualifications & intellectual property) in data/contracts.db."""
    __tablename__ = "assets"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    category: Mapped[str] = mapped_column(String(32), nullable=False)  # qualification or intellectual_property
    company_name: Mapped[str] = mapped_column(String(256), nullable=False)
    business_type: Mapped[Optional[str]] = mapped_column(String(256), nullable=True)
    qualification_name: Mapped[str] = mapped_column(String(512), nullable=False)
    qualification_level: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    expire_date: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    next_review_date: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    download_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    raw_payload: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    collected_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)

    def __repr__(self) -> str:
        return f"<ExistingAsset(category={self.category}, name={self.qualification_name})>"
