from backend.app.core.database import SessionLocal
from backend.app.auth.models import User
from backend.app.auth.service import hash_password

def create_admin():
    db = SessionLocal()
    try:
        # Check if admin exists
        user = db.query(User).filter(User.username == "admin").first()
        if user:
            print("Admin user already exists.")
            # Update password just in case
            user.password_hash = hash_password("admin123")
            db.commit()
            print("Admin password updated to 'admin123'.")
            return

        # Create admin user
        admin_user = User(
            username="admin",
            password_hash=hash_password("admin123"),
            phone="13800000000",
            full_name="Admin User",
            role="admin",
            is_active=True
        )
        db.add(admin_user)
        db.commit()
        print("Admin user created successfully.")
    except Exception as e:
        print(f"Error creating admin user: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    create_admin()
