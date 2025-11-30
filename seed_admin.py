import sys
import os
from sqlalchemy.orm import Session

# Add project root to path
sys.path.append(os.getcwd())

from backend.app.core.database import SessionLocal
from backend.app.auth import models, service, schemas
from backend.app.auth.service import get_user_by_phone, hash_password

def seed_admin():
    db = SessionLocal()
    try:
        username = "admin"
        phone = "13800000000" # Placeholder phone for admin
        password = "sunyong524517"
        
        # Check if admin exists by username
        from sqlalchemy import select
        stmt = select(models.User).where(models.User.username == username)
        user = db.execute(stmt).scalar_one_or_none()
        
        if user:
            print(f"Admin user '{username}' already exists.")
            # Update password just in case
            user.password_hash = hash_password(password)
            user.role = "admin"
            db.commit()
            print("Admin password and role updated.")
        else:
            # Create new admin
            print(f"Creating admin user '{username}'...")
            user = models.User(
                phone=phone,
                full_name="System Administrator",
                password_hash=hash_password(password),
                username=username,
                role="admin",
                is_active=True
            )
            db.add(user)
            db.commit()
            print("Admin user created successfully.")
            
    except Exception as e:
        print(f"Error seeding admin: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    seed_admin()
