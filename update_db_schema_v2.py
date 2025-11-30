import sqlite3

DB_PATH = "sales_assistant.db"

def migrate():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    print("Migrating database schema...")

    # 1. Add username and role to users table
    try:
        cursor.execute("ALTER TABLE users ADD COLUMN username VARCHAR(64)")
        print("Added 'username' column to users table.")
    except sqlite3.OperationalError as e:
        if "duplicate column name" in str(e):
            print("'username' column already exists.")
        else:
            print(f"Error adding 'username' column: {e}")

    try:
        cursor.execute("ALTER TABLE users ADD COLUMN role VARCHAR(20) DEFAULT 'user' NOT NULL")
        print("Added 'role' column to users table.")
    except sqlite3.OperationalError as e:
        if "duplicate column name" in str(e):
            print("'role' column already exists.")
        else:
            print(f"Error adding 'role' column: {e}")

    # 2. Create personnel table
    # Note: We use a simplified CREATE TABLE here. SQLAlchemy would handle this better, 
    # but for a quick SQLite update without Alembic, this is fine.
    create_personnel_table = """
    CREATE TABLE IF NOT EXISTS personnel (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name VARCHAR(128) NOT NULL,
        certificate_name VARCHAR(256) NOT NULL,
        certificate_level VARCHAR(128),
        certificate_number VARCHAR(128),
        issue_date DATETIME,
        expire_date DATETIME,
        department VARCHAR(128),
        status VARCHAR(32) DEFAULT 'active',
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL
    );
    """
    cursor.execute(create_personnel_table)
    print("Created/Verified 'personnel' table.")
    
    # Create indexes for personnel
    cursor.execute("CREATE INDEX IF NOT EXISTS ix_personnel_name ON personnel (name)")
    cursor.execute("CREATE INDEX IF NOT EXISTS ix_personnel_certificate_name ON personnel (certificate_name)")

    # 3. Ensure username is unique (SQLite ALTER TABLE doesn't support adding constraints easily, 
    # so we rely on app logic or recreate table. For now, app logic is enough).
    # However, we should add a unique index.
    cursor.execute("CREATE UNIQUE INDEX IF NOT EXISTS ix_users_username ON users (username)")
    print("Created unique index on users.username.")

    conn.commit()
    conn.close()
    print("Migration completed successfully.")

if __name__ == "__main__":
    migrate()
