"""Create contracts and qualifications tables for Simple Search feature."""
import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent / "sales_assistant.db"

def create_tables():
    """Create contracts and qualifications tables."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    print("Creating contracts table...")
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS contracts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            project_name VARCHAR(256) NOT NULL,
            contract_number VARCHAR(128),
            client_name VARCHAR(256) NOT NULL,
            contract_amount DECIMAL(15, 2),
            signing_date DATE,
            start_date DATE,
            end_date DATE,
            contract_type VARCHAR(64),
            project_description TEXT,
            status VARCHAR(32) DEFAULT 'active',
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL
        )
    """)
    
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_contracts_project_name 
        ON contracts(project_name)
    """)
    
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_contracts_client_name 
        ON contracts(client_name)
    """)
    
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_contracts_contract_number 
        ON contracts(contract_number)
    """)
    
    print("Creating qualifications table...")
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS qualifications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            qualification_name VARCHAR(256) NOT NULL,
            qualification_type VARCHAR(128),
            qualification_level VARCHAR(64),
            certificate_number VARCHAR(128),
            issue_organization VARCHAR(256),
            issue_date DATE,
            expire_date DATE,
            scope TEXT,
            status VARCHAR(32) DEFAULT 'valid',
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL
        )
    """)
    
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_qualifications_name 
        ON qualifications(qualification_name)
    """)
    
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_qualifications_type 
        ON qualifications(qualification_type)
    """)
    
    conn.commit()
    conn.close()
    print("✅ Tables created successfully!")

if __name__ == "__main__":
    create_tables()
