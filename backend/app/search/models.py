"""Models for Simple Search feature."""
from __future__ import annotations

from datetime import datetime, date
from typing import Optional
from decimal import Decimal

from sqlalchemy import Integer, String, DateTime, Text, Date, Numeric
from sqlalchemy.orm import Mapped, mapped_column

from backend.app.core.database import Base
from backend.app.common.models import TimestampMixin

class Personnel(TimestampMixin, Base):
    __tablename__ = "personnel"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    
    # Certificate Details
    certificate_name: Mapped[str] = mapped_column(String(256), nullable=False, index=True)
    certificate_level: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    certificate_number: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    
    # Dates
    issue_date: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    expire_date: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    
    # Metadata
    department: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    status: Mapped[str] = mapped_column(String(32), default="active") # active, expired
    
    def __repr__(self) -> str:
        return f"<Personnel(name={self.name}, cert={self.certificate_name})>"


class Contract(TimestampMixin, Base):
    """Contract/Performance model for case matching."""
    __tablename__ = "contracts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    project_name: Mapped[str] = mapped_column(String(256), nullable=False, index=True)
    contract_number: Mapped[Optional[str]] = mapped_column(String(128), nullable=True, index=True)
    client_name: Mapped[str] = mapped_column(String(256), nullable=False, index=True)
    
    # Financial
    contract_amount: Mapped[Optional[Decimal]] = mapped_column(Numeric(15, 2), nullable=True)
    
    # Dates
    signing_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    start_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    end_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    
    # Details
    contract_type: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)  # 开发/运维/咨询
    project_description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(32), default="active")  # active/completed/terminated
    
    def __repr__(self) -> str:
        return f"<Contract(project={self.project_name}, client={self.client_name})>"


class Qualification(TimestampMixin, Base):
    """Qualification/Certificate model for requirement matching."""
    __tablename__ = "qualifications"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    qualification_name: Mapped[str] = mapped_column(String(256), nullable=False, index=True)
    qualification_type: Mapped[Optional[str]] = mapped_column(String(128), nullable=True, index=True)
    qualification_level: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    
    # Certificate Info
    certificate_number: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    issue_organization: Mapped[Optional[str]] = mapped_column(String(256), nullable=True)
    
    # Dates
    issue_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    expire_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    
    # Details
    scope: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # Business scope
    status: Mapped[str] = mapped_column(String(32), default="valid")  # valid/expired/revoked
    
    def __repr__(self) -> str:
        return f"<Qualification(name={self.qualification_name}, type={self.qualification_type})>"
