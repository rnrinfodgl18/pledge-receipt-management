"""
Test password verification
"""
import os
from dotenv import load_dotenv
from app.security import hash_password, verify_password
from app.models import User
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)

db = SessionLocal()

# Get admin user
admin = db.query(User).filter(User.username == "admin").first()

if admin:
    print("=== Password Verification Test ===")
    print(f"Username: {admin.username}")
    print(f"Hashed Password in DB: {admin.password}")
    
    # Test with correct password
    password_to_test = "admin123"
    is_valid = verify_password(password_to_test, admin.password)
    
    print(f"\nTesting password: '{password_to_test}'")
    print(f"Password is valid: {is_valid}")
    
    # Try alternative approach
    print("\n=== Direct Hash Test ===")
    new_hash = hash_password("admin123")
    print(f"New hash of 'admin123': {new_hash}")
    print(f"Matches stored hash: {new_hash == admin.password}")
else:
    print("❌ Admin user not found")

db.close()
