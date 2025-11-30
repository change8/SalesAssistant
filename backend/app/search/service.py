"""Enhanced service layer for Simple Search feature."""
from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_, func, select, case
import re
import csv
import io
from datetime import datetime

from backend.app.search import models, schemas
from backend.app.search.contracts_models import ExistingContract
from backend.app.search.assets_models import ExistingAsset
from backend.app.core.database import ContractsSessionLocal


def parse_amount_string(amount_str: str) -> Optional[float]:
    """Parse amount string like '中国人民币 526,548.00' to float."""
    if not amount_str:
        return None
    try:
        # Remove currency prefix and commas
        number_part = re.sub(r'[^\d.]', '', amount_str)
        return float(number_part) if number_part else None
    except:
        return None


def extract_industry(customer_name: str) -> Optional[str]:
    """Extract industry from customer_name like '公司名 （ 行业分类 ）'."""
    if not customer_name:
        return None
    match = re.search(r'（\s*(.+?)\s*）', customer_name)
    return match.group(1) if match else None


def search_contracts(
    db: Session,  # Not used for contracts, kept for API consistency
    params: schemas.ContractSearchParams
) -> tuple[list[dict], int]:
    """
    Enhanced contract search from existing contracts.db with fuzzy matching, filters, and relevance sorting.
    
    Args:
        db: Database session (not used for contracts)
        params: Search parameters with filters
        
    Returns:
        Tuple of (results as dicts, total_count)
    """
    contracts_db = ContractsSessionLocal()
    
    try:
        query = select(ExistingContract)
        
        # Enhanced fuzzy search on multiple fields with keyword splitting
        if params.q:
            keywords = params.q.split()
            for keyword in keywords:
                search_term = f"%{keyword}%"
                query = query.where(
                    or_(
                        ExistingContract.title.like(search_term),              # 合同名称
                        ExistingContract.contract_number.like(search_term),    # 合同编号
                        ExistingContract.project_code.like(search_term),       # 项目编号
                        ExistingContract.customer_name.like(search_term),      # 客户名称
                        ExistingContract.description.like(search_term),        # 合同描述/概述
                        ExistingContract.tags.like(search_term)                # 合同标签
                    )
                )
        
        # Filter by customer
        if params.customer:
            query = query.where(ExistingContract.customer_name.like(f"%{params.customer}%"))
        
        # Filter by status
        if params.status:
            query = query.where(ExistingContract.status.like(f"%{params.status}%"))
            
        # Filter by contract type
        if params.contract_type:
            query = query.where(ExistingContract.tags.like(f"%{params.contract_type}%"))
            
        # Note: is_fp filter is applied after extracting contract_type from tags
        # (See below after sorting)
        
        # Filter by tags
        if params.tags:
            query = query.where(ExistingContract.tags.like(f"%{params.tags}%"))
        
        # Amount filters
        if params.min_amount:
            # This is approximate, actual filtering will be done post-query
            pass  # Can't filter TEXT amounts easily in SQL
        if params.max_amount:
            pass
        
        # Date range filter
        if params.start_date:
            query = query.where(ExistingContract.signed_at >= params.start_date)
        if params.end_date:
            query = query.where(ExistingContract.signed_at <= params.end_date)
        
        # Get total count
        count_query = select(func.count()).select_from(query.subquery())
        total = contracts_db.execute(count_query).scalar()
        
        # Execute query
        all_results = contracts_db.execute(query).scalars().all()
        
        # Apply FP filter after extracting contract_type (can't do in SQL since contract_type is extracted from tags)
        if params.is_fp:
            filtered_results = []
            for contract in all_results:
                if contract.tags:
                    tags_list = [t.strip() for t in contract.tags.split(',')]
                    if tags_list and tags_list[0] == '固定金额':  # FP = Fixed Price
                        filtered_results.append(contract)
            all_results = filtered_results
            total = len(all_results)  # Update total after filtering
        
        # Filter by amount range (client-side due to string storage)
        if params.min_amount is not None or params.max_amount is not None:
            filtered = []
            for contract in all_results:
                amount = parse_amount_string(contract.contract_amount)
                if amount is not None:
                    if params.min_amount and amount < params.min_amount:
                        continue
                    if params.max_amount and amount > params.max_amount:
                        continue
                filtered.append(contract)
            all_results = filtered
        
        total = len(all_results)
        
        # Relevance + Time Sorting
        # Sort by relevance first (title match priority), then by date
        if params.q:
            query_lower = params.q.lower()
            def sort_key(contract):
                title_lower = (contract.title or '').lower()
                # Priority: exact match > starts with > contains
                if query_lower == title_lower:
                    relevance = 1
                elif title_lower.startswith(query_lower):
                    relevance = 2
                elif query_lower in title_lower:
                    relevance = 3
                elif query_lower in (contract.customer_name or '').lower():
                    relevance = 4
                else:
                    relevance = 5
                # Secondary sort: signed_at descending (None values last)
                signed_date = contract.signed_at or '0000-00-00'
                return (relevance, signed_date)
            
            all_results.sort(key=sort_key, reverse=False)  # Ascending relevance, descending date handled in tuple
        else:
            # No query: just sort by date descending
            all_results.sort(key=lambda x: x.signed_at or '0000-00-00', reverse=True)
        
        # Pagination
        paginated = all_results[params.offset:params.offset + params.limit]
        
        # Convert to dicts for API response
        contracts_list = []
        for contract in paginated:
            # Extract contract type from tags (first tag before comma)
            contract_type = None
            if contract.tags:
                tags_list = [t.strip() for t in contract.tags.split(',')]
                if tags_list:
                    contract_type = tags_list[0]  # Use first tag as contract type
            
            # Parse amount to raw value for frontend filtering
            amount_raw = parse_amount_string(contract.contract_amount)
            
            contracts_list.append({
                'id': contract.id,
                'contract_title': contract.title,
                'contract_number': contract.contract_number,
                'customer_name': contract.customer_name,
                'contract_amount': contract.contract_amount,
                'contract_amount_raw': amount_raw,
                'signing_date': contract.signed_at,
                'contract_type': contract_type,
                'contract_status': contract.status,
                'project_code': contract.project_code,
                'description': contract.description,
                'tags': contract.tags,
                'created_at': contract.created_at,
                'updated_at': contract.updated_at
            })
        
        return contracts_list, total
        
    finally:
        contracts_db.close()


def search_assets(
    db: Session,  # Not used, kept for consistency
    params: schemas.AssetSearchParams
) -> tuple[list[dict], int]:
    """
    Search assets (qualifications & intellectual property) from contracts.db.
    
    Args:
        db: Database session (not used)
        params: Search parameters
        
    Returns:
        Tuple of (results as dicts, total_count)
    """
    contracts_db = ContractsSessionLocal()
    
    try:
        query = select(ExistingAsset)
        
        # Filter by category (qualification or intellectual_property)
        if params.category:
            query = query.where(ExistingAsset.category == params.category)
        
        # Fuzzy search on qualification_name and company_name with keyword splitting
        if params.q:
            keywords = params.q.split()
            for keyword in keywords:
                search_term = f"%{keyword}%"
                query = query.where(
                    or_(
                        ExistingAsset.qualification_name.like(search_term),
                        ExistingAsset.company_name.like(search_term)
                    )
                )
        
        # Filter by company
        if params.company:
            query = query.where(ExistingAsset.company_name.like(f"%{params.company}%"))
            
        # Filter by business_type (for IP categories like patent, copyright)
        if params.business_type:
            # Map frontend types to DB values if needed, or assume direct match/fuzzy
            # Assuming DB stores '专利', '软著', '商标' or similar. 
            # Frontend sends 'patent', 'copyright', 'trademark'.
            # Let's map them for better accuracy or use fuzzy if unsure.
            type_map = {
                'patent': '专利',
                'copyright': '软著',
                'trademark': '商标'
            }
            db_type = type_map.get(params.business_type, params.business_type)
            query = query.where(ExistingAsset.business_type.like(f"%{db_type}%"))
        
        # Get total count
        count_query = select(func.count()).select_from(query.subquery())
        total = contracts_db.execute(count_query).scalar()
        
        # Sort by expire_date (ascending - expiring soon first)
        query = query.order_by(ExistingAsset.expire_date.asc().nullslast())
        
        # Pagination
        query = query.offset(params.offset).limit(params.limit)
        
        results = contracts_db.execute(query).scalars().all()
        
        # Convert to dicts
        assets_list = []
        for asset in results:
            assets_list.append({
                'id': asset.id,
                'category': asset.category,
                'company_name': asset.company_name,
                'business_type': asset.business_type,
                'qualification_name': asset.qualification_name,
                'qualification_level': asset.qualification_level,
                'expire_date': asset.expire_date,
                'next_review_date': asset.next_review_date,
                'download_url': asset.download_url,
                'collected_at': asset.collected_at,
                'created_at': asset.created_at,
                'updated_at': asset.updated_at
            })
        
        return assets_list, total or 0
        
    finally:
        contracts_db.close()


def search_qualifications(
    db: Session,
    params: schemas.QualificationSearchParams
) -> tuple[list[models.Qualification], int]:
    """
    Search qualifications from sales_assistant.db (test data).
    Note: This searches the test qualification table, not the assets table.
    """
    query = select(models.Qualification)
    
    # Fuzzy search
    if params.q:
        search_term = f"%{params.q}%"
        query = query.where(
            or_(
                models.Qualification.qualification_name.like(search_term),
                models.Qualification.qualification_type.like(search_term),
                models.Qualification.scope.like(search_term),
                models.Qualification.certificate_number.like(search_term)
            )
        )
    
    # Filters
    if params.qualification_type:
        query = query.where(
            models.Qualification.qualification_type.like(f"%{params.qualification_type}%")
        )
    
    if params.status:
        query = query.where(models.Qualification.status == params.status)
    
    # Get total count
    count_query = select(func.count()).select_from(query.subquery())
    total = db.execute(count_query).scalar()
    
    # Sort by expire_date
    query = query.order_by(models.Qualification.expire_date.asc().nullslast())
    
    # Pagination
    query = query.offset(params.offset).limit(params.limit)
    
    results = db.execute(query).scalars().all()
    
    return list(results), total or 0


def get_contract_by_id(db: Session, contract_id: int) -> Optional[dict]:
    """Get contract by ID from contracts.db."""
    contracts_db = ContractsSessionLocal()
    try:
        contract = contracts_db.get(ExistingContract, contract_id)
        if not contract:
            return None
        return {
            'id': contract.id,
            'project_name': contract.title,
            'contract_number': contract.contract_number,
            'client_name': contract.customer_name,
            'contract_amount': contract.contract_amount,
            'signing_date': contract.signed_at,
            'project_description': contract.description,
            'status': contract.status or 'active',
            'tags': contract.tags,
            'created_at': contract.created_at,
            'updated_at': contract.updated_at
        }
    finally:
        contracts_db.close()



def get_qualification_by_id(db: Session, qual_id: int) -> Optional[models.Qualification]:
    """Get qualification by ID."""
    return db.get(models.Qualification, qual_id)


def search_employees(
    db: Session,  # Not used for employees, kept for API consistency
    params: schemas.EmployeeSearchParams
) -> tuple[list[dict], int]:
    """
    Search employees from contracts.db with fuzzy matching and filters.
    
    Args:
        db: Database session (not used for employees)
        params: Search parameters with filters
        
    Returns:
        Tuple of (results as dicts, total_count)
    """
    from backend.app.search.employee_models import Employee, EmployeeEducation, EmployeeCertificate
    
    contracts_db = ContractsSessionLocal()
    
    try:
        query = select(Employee)
        
        # Fuzzy search on multiple fields
        if params.q:
            search_term = f"%{params.q}%"
            query = query.outerjoin(Employee.certificates).where(
                or_(
                    Employee.name.like(search_term),
                    Employee.employee_no.like(search_term),
                    Employee.school.like(search_term),
                    Employee.major.like(search_term),
                    Employee.company.like(search_term),
                    EmployeeCertificate.certificate_name.like(search_term)
                )
            ).distinct()
        
        # Filter by status
        if params.status:
            query = query.where(Employee.status.like(f"%{params.status}%"))
        
        # Filter by company
        if params.company:
            query = query.where(Employee.company.like(f"%{params.company}%"))
        
        # Filter by degree
        if params.degree:
            query = query.where(Employee.degree.like(f"%{params.degree}%"))
        
        # Filter by certificate (requires join to certificates table)
        if params.certificate_name:
            query = query.join(Employee.certificates).where(
                EmployeeCertificate.certificate_name.like(f"%{params.certificate_name}%")
            )
        
        # Get total count
        count_query = select(func.count()).select_from(query.subquery())
        total = contracts_db.execute(count_query).scalar()
        
        # Sort by employee_no
        query = query.order_by(Employee.employee_no.asc())
        
        # Pagination
        query = query.offset(params.offset).limit(params.limit)
        
        results = contracts_db.execute(query).scalars().all()
        
        # Convert to dicts with nested educations and certificates
        employees_list = []
        for emp in results:
            # Fetch educations and certificates
            educations = contracts_db.execute(
                select(EmployeeEducation).where(EmployeeEducation.employee_id == emp.id)
            ).scalars().all()
            
            certificates = contracts_db.execute(
                select(EmployeeCertificate).where(EmployeeCertificate.employee_id == emp.id)
            ).scalars().all()
            
            employees_list.append({
                'id': emp.id,
                'employee_no': emp.employee_no,
                'name': emp.name,
                'gender': emp.gender,
                'status': emp.status,
                'joined_at': emp.joined_at,
                'age': emp.age,
                'seniority_years': emp.seniority_years,
                'working_years': emp.working_years,
                'school': emp.school,
                'major': emp.major,
                'degree': emp.degree,
                'diploma': emp.diploma,
                'company': emp.company,
                'industry_experience': emp.industry_experience,
                'educations': [
                    {
                        'id': edu.id,
                        'degree': edu.degree,
                        'major': edu.major,
                        'school': edu.school,
                        'diploma': edu.diploma,
                        'is_highest': edu.is_highest
                    }
                    for edu in educations
                ],
                'certificates': [
                    {
                        'id': cert.id,
                        'category': cert.category,
                        'certificate_type': cert.certificate_type,
                        'certificate_name': cert.certificate_name,
                        'qualification_level': cert.qualification_level,
                        'authority': cert.authority,
                        'effective_date': cert.effective_date,
                        'expire_date': cert.expire_date,
                        'certificate_no': cert.certificate_no,
                        'remarks': cert.remarks
                    }
                    for cert in certificates
                ],
                'created_at': emp.created_at,
                'updated_at': emp.updated_at
            })
        
        return employees_list, total or 0
        
    finally:
        contracts_db.close()


def export_contracts(
    db: Session,
    params: schemas.ContractSearchParams
) -> io.BytesIO:
    """
    Export contract search results to Excel-compatible CSV.
    """
    # Reuse search logic to get all results (no pagination limit for export, but maybe set a safe max)
    # We need to bypass the pagination limit in search_contracts if we want all.
    # For now, let's just fetch a large number, e.g., 10000.
    
    contracts_db = ContractsSessionLocal()
    try:
        query = select(ExistingContract)
        
        # --- COPY OF SEARCH LOGIC (Refactor later to avoid duplication if needed) ---
        if params.q:
            keywords = params.q.split()
            for keyword in keywords:
                search_term = f"%{keyword}%"
                query = query.where(
                    or_(
                        ExistingContract.title.like(search_term),
                        ExistingContract.contract_number.like(search_term),
                        ExistingContract.project_code.like(search_term),
                        ExistingContract.customer_name.like(search_term),
                        ExistingContract.description.like(search_term),
                        ExistingContract.tags.like(search_term)
                    )
                )
        if params.customer:
            query = query.where(ExistingContract.customer_name.like(f"%{params.customer}%"))
        if params.status:
            query = query.where(ExistingContract.status.like(f"%{params.status}%"))
        if params.contract_type:
            query = query.where(ExistingContract.tags.like(f"%{params.contract_type}%"))
        if params.tags:
            query = query.where(ExistingContract.tags.like(f"%{params.tags}%"))
        if params.start_date:
            query = query.where(ExistingContract.signed_at >= params.start_date)
        if params.end_date:
            query = query.where(ExistingContract.signed_at <= params.end_date)
        # ---------------------------------------------------------------------------
        
        # Limit export to 5000 to prevent memory issues
        query = query.limit(5000)
        
        results = contracts_db.execute(query).scalars().all()
        
        # Create CSV in memory
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Header
        writer.writerow(['合同名称', '合同编号', '项目编号', '客户名称', '签订日期', '金额', '状态', '类型', '标签', '描述'])
        
        for contract in results:
            writer.writerow([
                contract.title,
                contract.contract_number,
                contract.project_code,
                contract.customer_name,
                contract.signed_at,
                contract.amount,
                contract.status,
                contract.contract_type,
                contract.tags,
                contract.description
            ])
            
        # Convert to bytes with BOM for Excel
        output.seek(0)
        byte_output = io.BytesIO()
        byte_output.write(b'\xef\xbb\xbf') # BOM
        byte_output.write(output.getvalue().encode('utf-8'))
        byte_output.seek(0)
        
        return byte_output
        
    finally:
        contracts_db.close()
