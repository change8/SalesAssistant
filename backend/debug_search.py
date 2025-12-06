
import sys
import os
from pathlib import Path

# Add backend to path
sys.path.append(str(Path(__file__).resolve().parent.parent))

from backend.app.core.database import ContractsSessionLocal
from backend.app.search import service, schemas
from backend.app.auth import models as auth_models

def test_search():
    db = ContractsSessionLocal()
    user = auth_models.User(id=1, username="debug")
    
    print("--- Testing Contracts Search ---")
    try:
        params = schemas.ContractSearchParams(q="", limit=5)
        results, total = service.search_contracts(db, params, user)
        print(f"Contracts Found: {total}")
        if results:
            print(f"Sample Contract: {results[0]['contract_title']}")
            # Check raw_payload access
            print(f"Delivery Loc: {results[0].get('delivery_location')}")
    except Exception as e:
        print(f"Contracts Error: {e}")
        import traceback
        traceback.print_exc()

    print("\n--- Testing Assets (IP) Search ---")
    try:
        params = schemas.AssetSearchParams(q="", limit=5, category="intellectual_property")
        results, total = service.search_assets(db, params, user)
        print(f"IP Assets Found: {total}")
        if results:
            print(f"Sample IP: {results[0]['qualification_name']}")
    except Exception as e:
        print(f"IP Error: {e}")
        import traceback
        traceback.print_exc()

    print("\n--- Testing Qualifications Search ---")
    try:
        params = schemas.QualificationSearchParams(q="", limit=5)
        results, total = service.search_qualifications(db, params, user)
        print(f"Quals Found: {total}")
        if results:
            print(f"Sample Qual: {results[0]['qualification_name']}")
    except Exception as e:
        print(f"Quals Error: {e}")
        import traceback
        traceback.print_exc()

    db.close()

if __name__ == "__main__":
    test_search()
