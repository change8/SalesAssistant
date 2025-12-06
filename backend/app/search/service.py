"""Enhanced service layer for Simple Search feature."""
from typing import Optional, List, Tuple, Any, Dict
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_, func, select, case, desc
import re
import csv
import io
from datetime import datetime, timezone
import json
from enum import Enum, unique

from backend.app.search import models, schemas
from backend.app.search.contracts_models import ExistingContract
from backend.app.search.assets_models import QualificationAsset, IntellectualPropertyAsset
from backend.app.search.employee_models import Employee, EmployeeCertificate, EmployeeEducation
from backend.app.search.company_models import Company
from backend.app.core.database import ContractsSessionLocal


from backend.app.common.currency_service import convert_and_format
from backend.app.auth import models as auth_models

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


from backend.app.auth import models as auth_models
import json

def _log_search_history(db: Session, user_id: int, query: str, filters: dict) -> None:
    try:
        # Filter out None values and empty strings to save space
        clean_filters = {k: v for k, v in filters.items() if v}
        history = auth_models.SearchHistory(
            user_id=user_id,
            query=query,
            filters=json.dumps(clean_filters, ensure_ascii=False),
            search_time=datetime.now(timezone.utc)
        )
        db.add(history)
        db.commit()
    except Exception as e:
        print(f"Failed to log search history: {e}")

def get_search_history(db: Session, user_id: int, limit: int = 20) -> List[dict]:
    """Get search history for user."""
    history = db.query(auth_models.SearchHistory)\
        .filter(auth_models.SearchHistory.user_id == user_id)\
        .order_by(auth_models.SearchHistory.search_time.desc())\
        .limit(limit)\
        .all()
    
    return [
        {
            "id": h.id,
            "query": h.query,
            "filters": json.loads(h.filters) if h.filters else {},
            "search_time": h.search_time
        }
        for h in history
    ]

def search_contracts(
    db: Session,
    params: schemas.ContractSearchParams,
    current_user: Optional[auth_models.User] = None
) -> Tuple[List[dict], int]:
    """
    Enhanced contract search from existing contracts.db with fuzzy matching, filters, and relevance sorting.
    """
    if current_user:
        _log_search_history(db, current_user.id, params.q, params.dict(exclude={'q', 'limit', 'offset'}))

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
                        ExistingContract.tags.like(search_term),               # 合同标签
                        ExistingContract.industry.like(search_term)            # 行业
                    )
                )
        
        # Filter by customer
        if params.customer:
            query = query.where(ExistingContract.customer_name.like(f"%{params.customer}%"))
        
        # Filter by status
        if params.status:
            query = query.where(ExistingContract.status.like(f"%{params.status}%"))
            
        # Filter by contract type (using tags or specific logic)
        if params.contract_type:
            query = query.where(ExistingContract.tags.like(f"%{params.contract_type}%"))
            
        # Filter by tags
        if params.tags:
            query = query.where(ExistingContract.tags.like(f"%{params.tags}%"))

        # Filter by industry
        if params.industry:
            query = query.where(ExistingContract.industry.like(f"%{params.industry}%"))
        
        # Date range filter
        if params.start_date:
            query = query.where(ExistingContract.signed_at >= params.start_date)
        if params.end_date:
            query = query.where(ExistingContract.signed_at <= params.end_date)
            
        # Execute query
        all_results = contracts_db.execute(query).scalars().all()
        
        # Apply FP filter in Python
        if params.is_fp:
            filtered_results = []
            for contract in all_results:
                if contract.tags:
                    # Robust splitting: replace full-width comma, then split by comma or space
                    clean_tags = contract.tags.replace('，', ',')
                    tags_list = [t.strip() for t in re.split(r'[,，\s]+', clean_tags) if t.strip()]
                    
                    # Strict FP: tags_list[0] == '固定金额'
                    if tags_list and tags_list[0] == '固定金额':
                        filtered_results.append(contract)
            all_results = filtered_results
        
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
                return relevance
            
            # Sort: Relevance ASC, then Date DESC
            all_results.sort(key=lambda x: str(x.signed_at) if x.signed_at else '0000', reverse=True)
            all_results.sort(key=lambda x: sort_key(x), reverse=False)
        else:
            # No query: just sort by date descending
            all_results.sort(key=lambda x: str(x.signed_at) if x.signed_at else '0000', reverse=True)
        
        # Pagination
        paginated = all_results[params.offset:params.offset + params.limit]
        
        # Convert to dicts for API response
        contracts_list = []
        for contract in paginated:
            contract_type = None
            if contract.tags:
                tags_list = [t.strip() for t in re.split(r'[,，\s]+', contract.tags) if t.strip()]
                if tags_list:
                    contract_type = tags_list[0]
            
            amount_raw = parse_amount_string(contract.contract_amount)
            
            # Safe parsing of raw_payload (stored as JSON string)
            payload = {}
            if contract.raw_payload:
                if isinstance(contract.raw_payload, dict):
                    payload = contract.raw_payload
                else:
                    try:
                        payload = json.loads(contract.raw_payload)
                    except:
                        payload = {}
            
            contracts_list.append({
                'id': contract.id,
                'contract_title': contract.title,
                'contract_number': contract.contract_number,
                'customer_name': contract.customer_name,
                'contract_amount': convert_and_format(contract.contract_amount),
                'contract_amount_raw': amount_raw,
                'signing_date': contract.signed_at,
                'contract_type': contract_type,
                'contract_status': contract.status,
                'project_code': contract.project_code,
                'description': contract.description,
                'tags': contract.tags,
                'industry': contract.industry,
                'delivery_location': payload.get('delivery_location'),
                'delivery_team': payload.get('delivery_team'),
                'created_at': contract.created_at,
                'updated_at': contract.updated_at
            })
        
        return contracts_list, total
        
    finally:
        contracts_db.close()


def search_assets(
    db: Session,  # Not used, kept for consistency
    params: schemas.AssetSearchParams,
    current_user: Optional[auth_models.User] = None
) -> Tuple[List[dict], int]:
    """
    Search assets (Intellectual Property) from contracts.db.
    Note: This now specifically targets IntellectualPropertyAsset for the 'assets' endpoint (IP tab).
    """
    if current_user:
        _log_search_history(db, current_user.id, params.q, params.dict(exclude={'q', 'limit', 'offset'}))

    contracts_db = ContractsSessionLocal()
    
    try:
        query = select(IntellectualPropertyAsset)
        
        # Fuzzy search
        if params.q:
            keywords = params.q.split()
            for keyword in keywords:
                search_term = f"%{keyword}%"
                query = query.where(
                    or_(
                        IntellectualPropertyAsset.knowledge_name.like(search_term),
                        IntellectualPropertyAsset.company_name.like(search_term),
                        IntellectualPropertyAsset.certificate_number.like(search_term),
                        IntellectualPropertyAsset.inventor.like(search_term)
                    )
                )
        
        # Filter by company
        if params.company:
            query = query.where(IntellectualPropertyAsset.company_name.like(f"%{params.company}%"))
            
        if params.company_code:
            query = query.where(IntellectualPropertyAsset.company_code == params.company_code)
            
        # Filter (Not) Expired
        if params.is_expired is not None:
            today = datetime.now().strftime('%Y-%m-%d')
            if params.is_expired: # True = Only Expired
                query = query.where(IntellectualPropertyAsset.issue_date < today) # Note: IP usually uses issue_date or specific expire logic? Assuming issue_date for simplicity or skip if not applicable for IP
            else: # False = Not Expired
                 query = query.where(
                    or_(
                        IntellectualPropertyAsset.issue_date >= today,
                        IntellectualPropertyAsset.issue_date == None
                    )
                )

        # Filter by business_type (patent, copyright, trademark)
        if params.business_type:
            type_map = {
                'patent': '专利',
                'copyright': '软著',
                'trademark': '商标'
            }
            db_type = type_map.get(params.business_type, params.business_type)
            # Assuming business_type or patent_category or knowledge_category holds this info
            # Checking multiple fields to be safe
            query = query.where(
                or_(
                    IntellectualPropertyAsset.business_type.like(f"%{db_type}%"),
                    IntellectualPropertyAsset.knowledge_category.like(f"%{db_type}%"),
                    IntellectualPropertyAsset.patent_category.like(f"%{db_type}%")
                )
            )
        
        # Get total count
        count_query = select(func.count()).select_from(query.subquery())
        total = contracts_db.execute(count_query).scalar()
        
        # Sort by issue_date
        query = query.order_by(IntellectualPropertyAsset.issue_date.desc().nullslast())
        
        # Pagination
        query = query.offset(params.offset).limit(params.limit)
        
        results = contracts_db.execute(query).scalars().all()
        
        # Convert to dicts
        assets_list = []
        for asset in results:
            assets_list.append({
                'id': asset.id,
                'category': 'intellectual_property',
                'company_name': asset.company_name,
                'company_code': asset.company_code,
                'business_type': asset.business_type,
                'qualification_name': asset.knowledge_name, # Map knowledge_name to qualification_name for schema compatibility
                'qualification_level': None,
                'certificate_number': asset.certificate_number,
                
                # Full Mapping for Detail Popup
                'patent_category': asset.patent_category,
                'knowledge_category': asset.knowledge_category,
                'inventor': asset.inventor,
                'issue_date': asset.issue_date,
                'application_date': asset.application_date,
                'registration_no': asset.registration_no,
                'internal_id': asset.internal_id,
                'property_summary': asset.property_summary,
                
                'expire_date': None,
                'next_review_date': None,
                'download_url': asset.download_url,
                'collected_at': asset.created_at, # Use created_at as collected_at
                'created_at': asset.created_at,
                'updated_at': asset.updated_at
            })
        
        return assets_list, total or 0
        
    finally:
        contracts_db.close()


def search_qualifications(
    db: Session,
    params: schemas.QualificationSearchParams,
    current_user: Optional[auth_models.User] = None
) -> Tuple[List[dict], int]:
    """
    Search qualifications from contracts.db (QualificationAsset).
    """
    if current_user:
        _log_search_history(db, current_user.id, params.q, params.dict(exclude={'q', 'limit', 'offset'}))

    contracts_db = ContractsSessionLocal()
    try:
        query = select(QualificationAsset)
        
        # Fuzzy search
        if params.q:
            search_term = f"%{params.q}%"
            query = query.where(
                or_(
                    QualificationAsset.qualification_name.like(search_term),
                    QualificationAsset.company_name.like(search_term),
                    QualificationAsset.certificate_number.like(search_term)
                )
            )
        
        # Filters
        if params.qualification_type:
             query = query.where(QualificationAsset.qualification_name.like(f"%{params.qualification_type}%"))
        
        if params.company_code:
            query = query.where(QualificationAsset.company_code == params.company_code)
            
        if params.status:
            query = query.where(QualificationAsset.status == params.status)
            
        if params.is_expired is not None:
            today = datetime.now().strftime('%Y-%m-%d')
            if params.is_expired: # True = Expired
                query = query.where(QualificationAsset.expire_date < today)
            else: # False = Not Expired (Future or Null)
                query = query.where(
                    or_(
                        QualificationAsset.expire_date >= today,
                        QualificationAsset.expire_date == None
                    )
                )
        
        # Fetch All for In-Memory Sorting (Relevance)
        # Note: If dataset matches sort criteria, we can do it in SQL.
        # But 'Relevance' is hard in SQL LIKE.
        # Let's fetch all matched candidates (assuming < 1000) then sort.
        # Or just fetch all then sort. 
        # Given "ISO" might return many, let's execute query then sort in Python.
        
        results = contracts_db.execute(query).scalars().all()
        
        # Relevance Sorting
        if params.q:
            query_lower = params.q.lower()
            def qual_sort_key(q):
                name_lower = (q.qualification_name or '').lower()
                if query_lower == name_lower:
                    relevance = 1
                elif name_lower.startswith(query_lower):
                    relevance = 2
                elif query_lower in name_lower:
                    relevance = 3
                elif query_lower in (q.company_name or '').lower():
                    relevance = 4
                else:
                    relevance = 5
                return relevance
            
            # Sort: Relevance ASC, then Expire Date ASC (nulls last)
            # results.sort(key=lambda x: str(x.expire_date) if x.expire_date else '9999', reverse=False)
            results.sort(key=lambda x: qual_sort_key(x))
            
        else:
             # Default Sort: Expire Date ASC
             results.sort(key=lambda x: str(x.expire_date) if x.expire_date else '9999', reverse=False)

        total = len(results)
        
        # Pagination
        paginated = results[params.offset : params.offset + params.limit]
        
        # Map to schema
        qual_list = []
        for q in paginated:
            qual_list.append({
                'id': q.id,
                'qualification_name': q.qualification_name,
                'qualification_type': q.business_type, # Map business_type to qualification_type
                'qualification_level': q.qualification_level,
                'company_name': q.company_name,
                'company_code': q.company_code,
                'certificate_number': q.certificate_number,
                'issue_organization': q.issuer,
                
                # Full Mapping for Detail Popup
                'issue_date': q.issue_date, 
                'expire_date': q.expire_date,
                'start_date': q.issue_date,
                'registration_no': q.registration_no,
                'next_review_date': q.next_review_date,
                'remark': q.remark,
                
                'scope': None,
                'status': q.status or 'valid',
                'created_at': q.created_at,
                'updated_at': q.updated_at
            })
            
        return qual_list, total or 0
    finally:
        contracts_db.close()


def get_contract_by_id(db: Session, contract_id: int) -> Optional[dict]:
    """Get contract by ID from contracts.db."""
    contracts_db = ContractsSessionLocal()
    try:
        contract = contracts_db.get(ExistingContract, contract_id)
        if not contract:
            return None
        
        amount_raw = parse_amount_string(contract.contract_amount)
        contract_type = None
        if contract.tags:
            tags_list = [t.strip() for t in re.split(r'[,，\s]+', contract.tags) if t.strip()]
            if tags_list:
                contract_type = tags_list[0]

        # Safe parsing of raw_payload (stored as JSON string)
        payload = {}
        if contract.raw_payload:
            if isinstance(contract.raw_payload, dict):
                payload = contract.raw_payload
            else:
                try:
                    payload = json.loads(contract.raw_payload)
                except:
                    payload = {}

        return {
            'id': contract.id,
            'project_name': contract.title,
            'contract_number': contract.contract_number,
            'client_name': contract.customer_name,
            'contract_amount': convert_and_format(contract.contract_amount), # Schema expects Decimal/float? No, schema says Decimal, but we can pass float/str usually
            'signing_date': contract.signed_at,
            'project_description': contract.description,
            'status': contract.status or 'active',
            'contract_type': contract_type,
            'delivery_location': payload.get('delivery_location'),
            'delivery_team': payload.get('delivery_team'),
            'created_at': contract.created_at,
            'updated_at': contract.updated_at
        }
    finally:
        contracts_db.close()


def get_qualification_by_id(db: Session, qual_id: int) -> Optional[dict]:
    """Get qualification by ID."""
    contracts_db = ContractsSessionLocal()
    try:
        qual = contracts_db.get(QualificationAsset, qual_id)
        if not qual:
            return None
        return {
            'id': qual.id,
            'qualification_name': qual.qualification_name,
            'qualification_type': qual.business_type,
            'qualification_level': qual.qualification_level,
            'certificate_number': qual.certificate_number,
            'issue_organization': qual.issuer,
            'status': qual.status or 'valid',
            'created_at': qual.created_at,
            'updated_at': qual.updated_at
        }
    finally:
        contracts_db.close()


def search_employees(
    db: Session,  # Not used for employees, kept for API consistency
    params: schemas.EmployeeSearchParams,
    current_user: Optional[auth_models.User] = None
) -> Tuple[List[dict], int]:
    """
    Search employees from contracts.db with fuzzy matching and filters.
    """
    if current_user:
        _log_search_history(db, current_user.id, params.q, params.dict(exclude={'q', 'limit', 'offset'}))

    from backend.app.search.employee_models import Employee, EmployeeEducation, EmployeeCertificate
    
    contracts_db = ContractsSessionLocal()
    
    try:
        query = select(Employee)
        
        # Fuzzy search on multiple fields
        if params.q:
            search_term = f"%{params.q}%"
            # Join both Educations and Certificates for search
            # Use outer join to include employees without edu/cert records if name matches
            query = query.outerjoin(Employee.educations).outerjoin(Employee.certificates).where(
                or_(
                    Employee.name.like(search_term),
                    Employee.employee_no.like(search_term),
                    EmployeeEducation.school.like(search_term),
                    EmployeeEducation.major.like(search_term),
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
        
        # Filter by degree (requires join)
        if params.degree:
            query = query.join(Employee.educations).where(EmployeeEducation.degree.like(f"%{params.degree}%"))
        
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
            
            # --- DEDUPLICATION LOGIC ---
            # Remove duplicate certificates by name, keeping the one with the latest expire_date (or none)
            unique_certs_map = {}
            for cert in certificates:
                name = cert.certificate_name
                # If we've seen this cert name before
                if name in unique_certs_map:
                    existing = unique_certs_map[name]
                    # Logic: favor one with expire_date over one without? Or latest date?
                    # If existing has expire date and new doesn't, keep existing.
                    # If new has expire date and existing doesn't, keep new.
                    # If both have dates, keep later one.
                    # If neither, keep random.
                    
                    if cert.expire_date and not existing.expire_date:
                        unique_certs_map[name] = cert
                    elif cert.expire_date and existing.expire_date:
                        if cert.expire_date > existing.expire_date:
                            unique_certs_map[name] = cert
                else:
                    unique_certs_map[name] = cert
            
            # Use deduplicated list
            final_certificates = list(unique_certs_map.values())
            
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
                'industry_experience': None, # Removed from model
                # 'school': emp.educations[0].school if emp.educations else None, # Example logic
                # For now let's just return what we have. The frontend iterates 'educations'.
                # But let's keep the structure clean.
                # Actually, previously `emp.school` was returning None anyway because it was empty in DB?
                # The user says "build query based on data dictionary".
                # If I look at the result mapping (lines 509-553 in original file),
                # it maps `school: emp.school`.
                # If I removed `school` from `Employee` model, `emp.school` will fail.
                # I MUST provide a value or remove the key.
                # I will populate it from the first education record (assuming it's the relevant one).
                'school': educations[0].school if educations else None,
                'major': educations[0].major if educations else None,
                'degree': educations[0].degree if educations else None,
                'diploma': educations[0].diploma if educations else None,
                'educations': [
                    {
                        'id': edu.id,
                        'degree': edu.degree,
                        'major': edu.major,
                        'school': edu.school,
                        'diploma': edu.diploma,
                        'is_highest': None # edu.is_highest is removed from DB schema
                    }
                    for edu in educations
                ],
                'certificates': [
                    {
                        'id': cert.id,
                        'category': None, # Removed from DB
                        'certificate_type': cert.certificate_type,
                        'certificate_name': cert.certificate_name,
                        'qualification_level': cert.level, # mapped from 'level' column
                        'authority': cert.authority,
                        'effective_date': cert.effective_date,
                        'expire_date': cert.expire_date,
                        'certificate_no': cert.certificate_no,
                        'remarks': None # Removed from DB
                    }
                    for cert in final_certificates
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
    contracts_db = ContractsSessionLocal()
    try:
        query = select(ExistingContract)
        
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
                        ExistingContract.tags.like(search_term),
                        ExistingContract.industry.like(search_term)
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
        if params.industry:
            query = query.where(ExistingContract.industry.like(f"%{params.industry}%"))
        if params.start_date:
            query = query.where(ExistingContract.signed_at >= params.start_date)
        if params.end_date:
            query = query.where(ExistingContract.signed_at <= params.end_date)
        
        # Limit export to 5000
        query = query.limit(5000)
        
        results = contracts_db.execute(query).scalars().all()
        
        # Create CSV in memory
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Header
        writer.writerow(['合同名称', '合同编号', '项目编号', '客户名称', '签订日期', '金额', '状态', '类型', '标签', '行业', '描述'])
        
        for contract in results:
            contract_type = None
            if contract.tags:
                tags_list = [t.strip() for t in contract.tags.split(',')]
                if tags_list:
                    contract_type = tags_list[0]
                    
            writer.writerow([
                contract.title,
                contract.contract_number,
                contract.project_code,
                contract.customer_name,
                contract.signed_at,
                contract.contract_amount,
                contract.status,
                contract_type,
                contract.tags,
                contract.industry,
                contract.description
            ])
            
        output.seek(0)
        byte_output = io.BytesIO()
        byte_output.write(b'\xef\xbb\xbf') # BOM
        byte_output.write(output.getvalue().encode('utf-8'))
        byte_output.seek(0)
        
        return byte_output
        
    finally:
        contracts_db.close()


def search_companies(
    db: Session,
    params: schemas.CompanySearchParams,
    current_user: auth_models.User
) -> Dict[str, Any]:
    """Search for companies based on filters."""
    contracts_db = ContractsSessionLocal()
    try:
        query = select(Company)

        # Multi-field Fuzzy Search
        if params.q:
            search_term = f"%{params.q}%"
            query = query.where(
                or_(
                    Company.name.ilike(search_term),
                    Company.code.ilike(search_term),
                    Company.nuccn.ilike(search_term),
                    Company.legal_person.ilike(search_term)
                )
            )

        # Filters
        if params.status:
            query = query.where(Company.operating_state.ilike(f"%{params.status}%"))
            
        if params.start_date:
            # Assuming format YYYY-MM-DD
            query = query.where(Company.setup_date >= params.start_date)
        if params.end_date:
            query = query.where(Company.setup_date <= params.end_date)
            
        # Execute Query
        results = contracts_db.execute(query).scalars().all()
        
        # Python-side filtering for Registered Capital (Text)
        if params.capital_min is not None or params.capital_max is not None:
            filtered = []
            for company in results:
                # Parse "100万元", "50.5万", etc.
                cap_val = 0.0
                try:
                    raw = company.registered_capital
                    if raw:
                        # Simple extraction of numbers
                        nums = re.findall(r"[-+]?\d*\.\d+|\d+", raw)
                        if nums:
                            cap_val = float(nums[0])
                except:
                    pass
                
                # Check range
                if params.capital_min is not None and cap_val < params.capital_min:
                    continue
                if params.capital_max is not None and cap_val > params.capital_max:
                    continue
                filtered.append(company)
            results = filtered

        total = len(results)
        
        # Sort by Setup Date Descending (Newest first)
        results.sort(key=lambda x: str(x.setup_date) if x.setup_date else '0000', reverse=True)
        
        # Pagination in Python
        paginated_items = results[params.offset : params.offset + params.limit]

        # Log search history
        _log_search_history(db, current_user.id, params.q or "", {
            "type": "company",
            "filters": params.dict(exclude={'q', 'limit', 'offset'})
        })

        return {
            "total": total,
            "results": paginated_items,
            "page": (params.offset // params.limit) + 1,
            "page_size": params.limit
        }
    finally:
        contracts_db.close()


def get_company_detail(
    db: Session,
    company_id: int,
    current_user: auth_models.User
) -> Optional[Company]:
    """Get detailed information for a specific company."""
    contracts_db = ContractsSessionLocal()
    try:
        company = contracts_db.get(Company, company_id)
        if company:
            _log_search_history(db, current_user.id, f"company_id:{company_id}", {"type": "company_detail"})
        return company
    finally:
        contracts_db.close()
