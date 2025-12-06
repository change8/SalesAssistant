"""API router for Simple Search endpoints."""
from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import Optional, List

from backend.app.auth import models as auth_models
from backend.app.core import dependencies
from backend.app.core.dependencies import get_db
from backend.app.search import service, schemas
from pydantic import BaseModel, Field

router = APIRouter(prefix="/search", tags=["search"])


class SearchParams(BaseModel):
    query: str
    page: int = 1
    page_size: int = 20
    filters: dict = {}



@router.get("/contracts/export")
def export_contracts(
    q: Optional[str] = Query(None, description="Search query"),
    customer: Optional[str] = Query(None, description="Filter by customer"),
    contract_type: Optional[str] = Query(None, description="Filter by type"),
    status: Optional[str] = Query(None, description="Filter by status"),
    tags: Optional[str] = Query(None, description="Filter by tags (comma-separated)"),
    industry: Optional[str] = Query(None, description="Filter by industry"),
    min_amount: Optional[float] = Query(None, description="Minimum amount"),
    max_amount: Optional[float] = Query(None, description="Maximum amount"),
    start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
    db: Session = Depends(get_db)
):
    """
    Export contract search results to Excel (CSV).
    """
    params = schemas.ContractSearchParams(
        q=q,
        customer=customer,
        contract_type=contract_type,
        status=status,
        tags=tags,
        industry=industry,
        min_amount=min_amount,
        max_amount=max_amount,
        start_date=start_date,
        end_date=end_date,
        limit=10000, # High limit for export
        offset=0
    )
    
    csv_buffer = service.export_contracts(db, params)
    
    return StreamingResponse(
        csv_buffer,
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=contracts_export.csv"}
    )


@router.get("/contracts", response_model=schemas.SearchResponse)
def search_contracts(
    q: Optional[str] = Query(None, description="Search query"),
    customer: Optional[str] = Query(None, description="Filter by customer"),
    contract_type: Optional[str] = Query(None, description="Filter by type"),
    status: Optional[str] = Query(None, description="Filter by status"),
    tags: Optional[str] = Query(None, description="Filter by tags (comma-separated)"),
    industry: Optional[str] = Query(None, description="Filter by industry"),
    min_amount: Optional[float] = Query(None, description="Minimum amount"),
    max_amount: Optional[float] = Query(None, description="Maximum amount"),
    start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
    limit: int = Query(50, le=100, description="Max results"),
    offset: int = Query(0, ge=0, description="Offset"),
    db: Session = Depends(get_db),
    current_user = Depends(dependencies.get_current_user)
):
    """
    Enhanced contract search with fuzzy matching, filters, and relevance sorting.
    
    Searches: title, contract_number, project_code, customer_name, description, tags
    Filters: customer, type, status, tags, industry, amount range, date range
    Sorting: Relevance (title match priority) + Time (descending)
    """
    params = schemas.ContractSearchParams(
        q=q,
        customer=customer,
        contract_type=contract_type,
        status=status,
        tags=tags,
        industry=industry,
        min_amount=min_amount,
        max_amount=max_amount,
        start_date=start_date,
        end_date=end_date,
        limit=limit,
        offset=offset
    )
    
    results, total = service.search_contracts(db, params, current_user)
    
    return schemas.SearchResponse(
        total=total,
        results=results,  # Already dicts from service
        offset=offset,
        limit=limit
    )


@router.get("/assets", response_model=schemas.SearchResponse)
def search_assets(
    q: Optional[str] = Query(None, description="Search query"),
    category: Optional[str] = Query(None, description="Filter by category (qualification or intellectual_property)"),
    company: Optional[str] = Query(None, description="Filter by company"),
    limit: int = Query(50, le=100, description="Max results"),
    offset: int = Query(0, ge=0, description="Offset"),
    db: Session = Depends(get_db),
    current_user = Depends(dependencies.get_current_user)
):
    """
    Search assets (qualifications & intellectual property).
    
    Query by qualification name or company name.
    Filter by category (qualification or intellectual_property) and company.
    """
    params = schemas.AssetSearchParams(
        q=q,
        category=category,
        company=company,
        limit=limit,
        offset=offset
    )
    
    results, total = service.search_assets(db, params, current_user)
    
    return schemas.SearchResponse(
        total=total,
        results=results,  # Already dicts from service
        offset=offset,
        limit=limit
    )


@router.get("/qualifications", response_model=schemas.SearchResponse)
def search_qualifications(
    q: Optional[str] = Query(None, description="Search query"),
    qualification_type: Optional[str] = Query(None, description="Filter by type"),
    status: Optional[str] = Query(None, description="Filter by status"),
    limit: int = Query(50, le=100, description="Max results"),
    offset: int = Query(0, ge=0, description="Offset"),
    db: Session = Depends(get_db),
    current_user = Depends(dependencies.get_current_user)
):
    """
    Search qualifications with fuzzy matching.
    
    Query by qualification name, type, or certificate number.
    Filter by type and status.
    """
    params = schemas.QualificationSearchParams(
        q=q,
        qualification_type=qualification_type,
        status=status,
        limit=limit,
        offset=offset
    )
    
    results, total = service.search_qualifications(db, params, current_user)
    
    return schemas.SearchResponse(
        total=total,
        results=results, # Already dicts from service
        offset=offset,
        limit=limit
    )


@router.get("/employees", response_model=schemas.SearchResponse)
def search_employees(
    q: Optional[str] = Query(None, description="Search query (fuzzy search on name, employee_no, school, major)"),
    status: Optional[str] = Query(None, description="Filter by employment status"),
    company: Optional[str] = Query(None, description="Filter by company"),
    degree: Optional[str] = Query(None, description="Filter by degree level"),
    certificate_name: Optional[str] = Query(None, description="Filter by certificate name"),
    limit: int = Query(50, le=100, description="Max results"),
    offset: int = Query(0, ge=0, description="Offset"),
    db: Session = Depends(get_db),
    current_user = Depends(dependencies.get_current_user)
):
    """
    Search employees with fuzzy matching and filters.
    
    Query by name, employee number, school, or major.
    Filter by status, company, degree, or certificate.
    Returns employees with nested educations and certificates.
    """
    params = schemas.EmployeeSearchParams(
        q=q,
        status=status,
        company=company,
        degree=degree,
        certificate_name=certificate_name,
        limit=limit,
        offset=offset
    )
    
    results, total = service.search_employees(db, params, current_user)
    
    return schemas.SearchResponse(
        total=total,
        results=results,  # Already dicts from service
        offset=offset,
        limit=limit
    )


@router.get("/companies")
def search_companies(
    q: Optional[str] = Query(None, description="Search query"),
    status: Optional[str] = Query(None, description="Filter by status"),
    start_date: Optional[str] = Query(None, description="Start setup date"),
    end_date: Optional[str] = Query(None, description="End setup date"),
    capital_min: Optional[float] = Query(None, description="Min registered capital"),
    capital_max: Optional[float] = Query(None, description="Max registered capital"),
    limit: int = Query(20, le=100),
    offset: int = Query(0, ge=0),
    current_user: auth_models.User = Depends(dependencies.get_current_user),
    db: Session = Depends(dependencies.get_db),
):
    """Search for companies with filters."""
    params = schemas.CompanySearchParams(
        q=q,
        status=status,
        start_date=start_date,
        end_date=end_date,
        capital_min=capital_min,
        capital_max=capital_max,
        limit=limit,
        offset=offset
    )
    return service.search_companies(db, params, current_user)


@router.get("/companies/{company_id}")
def get_company_detail(
    company_id: int,
    current_user: auth_models.User = Depends(dependencies.get_current_user),
    db: Session = Depends(dependencies.get_db),
):
    """Get company details."""
    company = service.get_company_detail(db, company_id, current_user)
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    return company

@router.get("/contracts/{contract_id}", response_model=schemas.ContractRead)
def get_contract(contract_id: int, db: Session = Depends(get_db)):
    """Get contract by ID."""
    contract = service.get_contract_by_id(db, contract_id)
    if not contract:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Contract not found")
    return schemas.ContractRead.from_orm(contract)


@router.get("/qualifications/{qual_id}", response_model=schemas.QualificationRead)
def get_qualification(qual_id: int, db: Session = Depends(get_db)):
    """Get qualification by ID."""
    qual = service.get_qualification_by_id(db, qual_id)
    if not qual:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Qualification not found")
    return qual
