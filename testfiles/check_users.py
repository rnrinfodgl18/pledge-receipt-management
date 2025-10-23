"""
Debug script to check database users and create admin if needed.
"""
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv
from app.models import User
from app.security import hash_password

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise ValueError("DATABASE_URL not set in .env")

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)

try:
    db = SessionLocal()
    
    # Check existing users
    print("=== Checking Existing Users ===")
    users = db.query(User).all()
    
    if not users:
        print("❌ No users found in database")
        print("\n📝 Creating default admin user...")
        
        admin_user = User(
            username="admin",
            password=hash_password("admin123"),
            role="admin",
            status=True
        )
        db.add(admin_user)
        db.commit()
        db.refresh(admin_user)
        
        print(f"✅ Admin user created:")
        print(f"   Username: admin")
        print(f"   Password: admin123")
        print(f"   Role: admin")
        print(f"   ID: {admin_user.id}")
    else:
        print(f"✅ Found {len(users)} user(s):")
        for user in users:
            print(f"\n   ID: {user.id}")
            print(f"   Username: {user.username}")
            print(f"   Role: {user.role}")
            print(f"   Status: {user.status}")
            print(f"   Created: {user.created_at}")
    
    db.close()
    
except Exception as e:
    print(f"❌ Error: {e}")
    print("\nMake sure:")
    print("1. PostgreSQL is running")
    print("2. DATABASE_URL is correct in .env")
    print("3. Database tables exist (run the FastAPI app first)")
