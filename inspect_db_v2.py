
import sqlite3
import os

DB_PATH = "data/contracts.db"

def inspect_contracts_and_assets():
    if not os.path.exists(DB_PATH):
        print(f"Database not found at {DB_PATH}")
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Inspect contracts table schema
    print("\n--- Schema for contracts ---")
    cursor.execute("PRAGMA table_info(contracts)")
    columns = cursor.fetchall()
    for col in columns:
        print(col)
        
    # Inspect assets categories to find software copyrights
    print("\n--- Asset Categories ---")
    cursor.execute("SELECT DISTINCT category FROM assets")
    categories = cursor.fetchall()
    print(categories)
    
    # Show sample asset for each category
    for cat in categories:
        category = cat[0]
        print(f"\n--- Sample Asset ({category}) ---")
        cursor.execute("SELECT * FROM assets WHERE category=? LIMIT 1", (category,))
        print(cursor.fetchone())

    conn.close()

if __name__ == "__main__":
    inspect_contracts_and_assets()
