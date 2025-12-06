from sqlalchemy import func, text
from backend.app.core.database import ContractsSessionLocal
from backend.app.search.employee_models import EmployeeCertificate

def deduplicate():
    db = ContractsSessionLocal()
    try:
        print("Starting deduplication...")
        # Find duplicates: group by employee_id, certificate_name, count > 1
        duplicates = db.query(
            EmployeeCertificate.employee_id,
            EmployeeCertificate.certificate_name,
            func.count(EmployeeCertificate.id)
        ).group_by(
            EmployeeCertificate.employee_id,
            EmployeeCertificate.certificate_name
        ).having(func.count(EmployeeCertificate.id) > 1).all()

        print(f"Found {len(duplicates)} duplicate groups.")
        
        deleted_count = 0
        for emp_id, cert_name, count in duplicates:
            if not cert_name:
                continue
                
            # Get all records for this group
            certs = db.query(EmployeeCertificate).filter(
                EmployeeCertificate.employee_id == emp_id,
                EmployeeCertificate.certificate_name == cert_name
            ).all()
            
            # Calculate non-null score
            with_score = []
            for c in certs:
                score = 0
                # Inspect columns
                for key, value in c.__dict__.items():
                    if not key.startswith('_') and value is not None:
                         score += 1
                with_score.append((c, score))
            
            # Sort by score DESC, then id DESC (keep latest if score tie)
            with_score.sort(key=lambda x: (x[1], x[0].id), reverse=True)
            
            # Keep first, delete rest
            to_delete = [x[0] for x in with_score[1:]]
            for d in to_delete:
                db.delete(d)
                deleted_count += 1
        
        db.commit()
        print(f"Deduplication complete. Deleted {deleted_count} records.")
    except Exception as e:
        print(f"Error: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    deduplicate()
