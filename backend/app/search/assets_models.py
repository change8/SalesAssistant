"""Models for querying existing assets (qualifications & IP) database."""
from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import Integer, String, DateTime, Text
from sqlalchemy.orm import Mapped, mapped_column

from backend.app.search.contracts_models import ContractsBase

class QualificationAsset(ContractsBase):
    """Model for qualification_assets table."""
    __tablename__ = "qualification_assets"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    record_uid: Mapped[Optional[str]] = mapped_column(String(128), unique=True, nullable=True)
    company_name: Mapped[str] = mapped_column(String(256), nullable=False)
    company_code: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    business_type: Mapped[Optional[str]] = mapped_column(String(256), nullable=True)
    qualification_name: Mapped[str] = mapped_column(String(512), nullable=False)
    qualification_level: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    expire_date: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    next_review_date: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    internal_id: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    patent_category: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    registration_no: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    certificate_number: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    issuer: Mapped[Optional[str]] = mapped_column(String(256), nullable=True)
    issue_date: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    status: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    keeper: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    remark: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    download_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    raw_payload: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    data_status: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)

    def __repr__(self) -> str:
        return f"<QualificationAsset(name={self.qualification_name}, company={self.company_name})>"


class IntellectualPropertyAsset(ContractsBase):
    """Model for intellectual_property_assets table."""
    __tablename__ = "intellectual_property_assets"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    record_uid: Mapped[Optional[str]] = mapped_column(String(128), unique=True, nullable=True)
    company_name: Mapped[str] = mapped_column(String(256), nullable=False)
    company_code: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    business_type: Mapped[Optional[str]] = mapped_column(String(256), nullable=True)
    knowledge_category: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    patent_category: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    knowledge_name: Mapped[str] = mapped_column(String(512), nullable=False)
    certificate_number: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    inventor: Mapped[Optional[str]] = mapped_column(String(256), nullable=True)
    issue_date: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    application_date: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    internal_id: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    property_summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    application_status: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    issuer: Mapped[Optional[str]] = mapped_column(String(256), nullable=True)
    version: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    registration_no: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    download_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    raw_payload: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    data_status: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)

    def __repr__(self) -> str:
        return f"<IntellectualPropertyAsset(name={self.knowledge_name}, category={self.knowledge_category})>"
