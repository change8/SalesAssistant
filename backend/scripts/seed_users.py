
import sys
import os
from pathlib import Path
import pandas as pd

# Add backend directory to sys.path to allow imports
sys.path.append(str(Path(__file__).resolve().parent.parent.parent))

from backend.app.core.database import SessionLocal
from backend.app.auth import models, service

def seed_users():
    # Path to excel
    excel_path = Path("data/pre-user.xlsx")
    if not excel_path.exists():
        print(f"File not found: {excel_path.absolute()}")
        return

    print(f"Reading users from {excel_path}...")
    try:
        # Read without header, assuming data starts at row 0 or 1
        df = pd.read_excel(excel_path, header=None)
        print("DataFrame Head:")
        print(df.head())
    except Exception as e:
        print(f"Failed to read Excel file: {e}")
        return

    # Helper to find the start of data
    start_row = 0
    # Try to find a row that looks like it has data (length > 0)
    # Simple heuristic: look for a row where column 0 looks like an ID (string or int)
    
    db = SessionLocal()
    count = 0
    try:
        for index, row in df.iterrows():
            try:
                # Skip empty rows or header rows
                # Headers are in row 1, data starts row 2. Header row col 1 is '工号（密码）'
                col1 = str(row[1]).strip()
                if not col1 or col1 == 'nan' or '工号' in col1:
                    continue

                # Mapping:
                # Col 1: 工号 (Password)
                # Col 2: 姓名 (Username)
                # Col 3: 手机号 (Phone)
                # Col 4: 邮箱 (Email)

                raw_password = str(row[1]).strip()
                if raw_password.endswith('.0'):
                    raw_password = raw_password[:-2]
                
                name = str(row[2]).strip()
                
                phone = str(row[3]).strip()
                if phone.endswith('.0'):
                    phone = phone[:-2]
                
                email = None
                if len(row) > 4 and pd.notna(row[4]):
                    email = str(row[4]).strip()
                
                if not phone or phone == 'nan' or '手机号' in phone:
                     print(f"Skipping row {index}: invalid phone {phone}")
                     continue

                print(f"Processing user: {name} ({phone})")

                # Check existence
                user = service.get_user_by_phone(db, phone)
                if user:
                    print(f"Updating existing user: {name} ({phone})")
                    user.full_name = name
                    user.username = name # Also try to sync username if possible, or keep existing
                    if email:
                        user.email = email
                    # Reset password only if needed? Better not to reset password for existing active users unless requested.
                    # We only want to fix the profile info.
                    db.add(user)
                    count += 1
                    continue

                print(f"Creating user: {name} ({phone})")
                new_user = models.User(
                    phone=phone,
                    full_name=name,
                    username=name,
                    email=email,
                    password_hash=service.hash_password(raw_password),
                    is_active=True,
                    role="user"
                )
                db.add(new_user)
                count += 1
            except Exception as row_err:
                print(f"Error processing row {index}: {row_err}")

        db.commit()
        print(f"Seeding completed. {count} users added.")
    except Exception as e:
        print(f"Error during seeding: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    seed_users()
