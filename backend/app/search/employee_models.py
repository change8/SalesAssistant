"""Models for querying employee data from contracts.db."""
from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import Integer, String, DateTime, Text, ForeignKey, REAL
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.app.search.contracts_models import ContractsBase


class Employee(ContractsBase):
    """Model for employees table."""
    __tablename__ = "employees"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    employee_no: Mapped[str] = mapped_column(Text, nullable=False, unique=True)
    name: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    gender: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    joined_at: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    age: Mapped[Optional[float]] = mapped_column(REAL, nullable=True)
    seniority_years: Mapped[Optional[float]] = mapped_column(REAL, nullable=True)
    working_years: Mapped[Optional[float]] = mapped_column(REAL, nullable=True)
    school: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    major: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    degree: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    diploma: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    company: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    industry_experience: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)

    # Relationships
    educations: Mapped[list["EmployeeEducation"]] = relationship("EmployeeEducation", back_populates="employee")
    certificates: Mapped[list["EmployeeCertificate"]] = relationship("EmployeeCertificate", back_populates="employee")

    def __repr__(self) -> str:
        return f"<Employee(employee_no={self.employee_no}, name={self.name})>"


class EmployeeEducation(ContractsBase):
    """Model for employee_educations table."""
    __tablename__ = "employee_educations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    employee_id: Mapped[int] = mapped_column(Integer, ForeignKey("employees.id"), nullable=False)
    degree: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    major: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    school: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    diploma: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_highest: Mapped[Optional[int]] = mapped_column(Integer, nullable=True, default=1)

    # Relationship
    employee: Mapped["Employee"] = relationship("Employee", back_populates="educations")

    def __repr__(self) -> str:
        return f"<EmployeeEducation(employee_id={self.employee_id}, degree={self.degree}, major={self.major})>"


class EmployeeCertificate(ContractsBase):
    """Model for employee_certificates table."""
    __tablename__ = "employee_certificates"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    employee_id: Mapped[int] = mapped_column(Integer, ForeignKey("employees.id"), nullable=False)
    category: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    certificate_type: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    certificate_name: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    qualification_level: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    authority: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    effective_date: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    expire_date: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    certificate_no: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    remarks: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Relationship
    employee: Mapped["Employee"] = relationship("Employee", back_populates="certificates")

    def __repr__(self) -> str:
        return f"<EmployeeCertificate(employee_id={self.employee_id}, certificate_name={self.certificate_name})>"
