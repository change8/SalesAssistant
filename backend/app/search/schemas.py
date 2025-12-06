"""Pydantic schemas for Simple Search API."""
from __future__ import annotations

from datetime import date, datetime
from typing import Optional
from decimal import Decimal

from pydantic import BaseModel, Field


# Contract Schemas
class ContractBase(BaseModel):
    project_name: str = Field(..., description="Project name")
    contract_number: Optional[str] = Field(None, description="Contract number")
    client_name: str = Field(..., description="Client name")
    contract_amount: Optional[Decimal] = Field(None, description="Contract amount")
    signing_date: Optional[date] = Field(None, description="Signing date")
    start_date: Optional[date] = Field(None, description="Start date")
    end_date: Optional[date] = Field(None, description="End date")
    contract_type: Optional[str] = Field(None, description="Contract type")
    project_description: Optional[str] = Field(None, description="Project description")
    status: str = Field(default="active", description="Contract status")


class ContractCreate(ContractBase):
    pass


class ContractRead(ContractBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ContractSearchParams(BaseModel):
    """Search parameters for contracts."""
    q: Optional[str] = Field(None, description="Search query (fuzzy)")
    
    # Filters
    customer: Optional[str] = Field(None, description="Filter by customer name")
    contract_type: Optional[str] = Field(None, description="Filter by contract type")
    status: Optional[str] = Field(None, description="Filter by status")
    tags: Optional[str] = Field(None, description="Filter by tags (comma-separated)")
    industry: Optional[str] = Field(None, description="Filter by industry")
    is_fp: Optional[bool] = Field(None, description="Filter by Fixed Price (FP) projects")
    
    # Amount range
    min_amount: Optional[float] = Field(None, description="Minimum contract amount")
    max_amount: Optional[float] = Field(None, description="Maximum contract amount")
    
    # Date range
    start_date: Optional[str] = Field(None, description="Start date (YYYY-MM-DD)")
    end_date: Optional[str] = Field(None, description="End date (YYYY-MM-DD)")
    
    # Pagination
    limit: int = Field(default=50, le=100, description="Max results")
    offset: int = Field(default=0, ge=0, description="Offset for pagination")


# Qualification Schemas
class QualificationBase(BaseModel):
    qualification_name: str = Field(..., description="Qualification name")
    qualification_type: Optional[str] = Field(None, description="Qualification type")
    qualification_level: Optional[str] = Field(None, description="Qualification level")
    certificate_number: Optional[str] = Field(None, description="Certificate number")
    issue_organization: Optional[str] = Field(None, description="Issuing organization")
    issue_date: Optional[date] = Field(None, description="Issue date")
    expire_date: Optional[date] = Field(None, description="Expiry date")
    scope: Optional[str] = Field(None, description="Business scope")
    status: str = Field(default="valid", description="Qualification status")


class QualificationCreate(QualificationBase):
    pass


class QualificationRead(QualificationBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class QualificationSearchParams(BaseModel):
    """Search parameters for qualifications."""
    q: Optional[str] = Field(None, description="Search query (fuzzy)")
    qualification_type: Optional[str] = Field(None, description="Filter by type")
    status: Optional[str] = Field(None, description="Filter by status")
    company_code: Optional[str] = Field(None, description="Filter by company code")
    is_expired: Optional[bool] = Field(None, description="Filter by expiration status (False = Not Expired)")
    limit: int = Field(default=50, le=100, description="Max results")
    offset: int = Field(default=0, ge=0, description="Offset for pagination")


# Asset (Qualification & IP) Schemas
class AssetRead(BaseModel):
    """Asset (qualification or intellectual property) response."""
    id: int
    category: str  # "qualification" or "intellectual_property"
    company_name: str
    business_type: Optional[str]
    qualification_name: str
    qualification_level: Optional[str]
    expire_date: Optional[str]
    next_review_date: Optional[str]
    download_url: Optional[str]
    collected_at: datetime
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class AssetSearchParams(BaseModel):
    """Search parameters for assets (qualifications & IP)."""
    q: Optional[str] = Field(None, description="Search query (fuzzy)")
    category: Optional[str] = Field(None, description="Filter by category: qualification or intellectual_property")
    company: Optional[str] = Field(None, description="Filter by company name")
    company_code: Optional[str] = Field(None, description="Filter by company code")
    business_type: Optional[str] = Field(None, description="Filter by business type (e.g., patent, copyright)")
    is_expired: Optional[bool] = Field(None, description="Filter by expiration status (False = Not Expired)")
    limit: int = Field(default=50, le=100, description="Max results")
    offset: int = Field(default=0, ge=0, description="Offset for pagination")


class SearchResponse(BaseModel):
    """Generic search response wrapper."""
    total: int = Field(..., description="Total results count")
    results: list = Field(..., description="Search results")
    offset: int = Field(..., description="Current offset")
    limit: int = Field(..., description="Current limit")


# Employee Schemas
class EmployeeEducationRead(BaseModel):
    """Employee education response."""
    id: int
    degree: Optional[str]
    major: Optional[str]
    school: Optional[str]
    diploma: Optional[str]
    is_highest: Optional[int]

    class Config:
        from_attributes = True


class EmployeeCertificateRead(BaseModel):
    """Employee certificate response."""
    id: int
    category: Optional[str]
    certificate_type: Optional[str]
    certificate_name: Optional[str]
    qualification_level: Optional[str]
    authority: Optional[str]
    effective_date: Optional[str]
    expire_date: Optional[str]
    certificate_no: Optional[str]
    remarks: Optional[str]

    class Config:
        from_attributes = True


class EmployeeRead(BaseModel):
    """Employee response with nested educations and certificates."""
    id: int
    employee_no: str
    name: Optional[str]
    gender: Optional[str]
    status: Optional[str]
    joined_at: Optional[str]
    age: Optional[float]
    seniority_years: Optional[float]
    working_years: Optional[float]
    school: Optional[str]
    major: Optional[str]
    degree: Optional[str]
    diploma: Optional[str]
    company: Optional[str]
    industry_experience: Optional[str]
    educations: list[EmployeeEducationRead] = []
    certificates: list[EmployeeCertificateRead] = []
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class EmployeeSearchParams(BaseModel):
    """Search parameters for employees."""
    q: Optional[str] = Field(None, description="Search query (fuzzy search on name, employee_no, school, major)")
    status: Optional[str] = Field(None, description="Filter by employment status")
    company: Optional[str] = Field(None, description="Filter by company")
    degree: Optional[str] = Field(None, description="Filter by degree level")
    certificate_name: Optional[str] = Field(None, description="Filter by certificate name")
    limit: int = Field(default=50, le=100, description="Max results")
    offset: int = Field(default=0, ge=0, description="Offset for pagination")


# Company Schemas
class CompanyRead(BaseModel):
    id: int
    name: str
    code: Optional[str]
    nuccn: Optional[str]
    legal_person: Optional[str]
    setup_date: Optional[str]
    registered_capital: Optional[str]
    operating_state: Optional[str]
    registered_address: Optional[str]
    business_scope: Optional[str]

    class Config:
        from_attributes = True


class CompanySearchParams(BaseModel):
    q: Optional[str] = Field(None, description="Search query")
    status: Optional[str] = Field(None, description="Operating status")
    start_date: Optional[str] = Field(None, description="Setup date start")
    end_date: Optional[str] = Field(None, description="Setup date end")
    capital_min: Optional[float] = Field(None, description="Min registered capital")
    capital_max: Optional[float] = Field(None, description="Max registered capital")
    limit: int = Field(default=50, le=100)
    offset: int = Field(default=0, ge=0)
