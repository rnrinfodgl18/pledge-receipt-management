"""Authentication routes for login and token generation."""
from datetime import timedelta
import logging
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import User as UserModel
from app import schemas
from app.security import verify_password
from app.auth import create_access_token, ACCESS_TOKEN_EXPIRE_MINUTES

logger = logging.getLogger(__name__)
auth_router = APIRouter(prefix="/auth", tags=["auth"])


@auth_router.post("/login", response_model=schemas.TokenResponse)
def login(login_data: schemas.LoginRequest, db: Session = Depends(get_db)):
    """User login - returns JWT token."""
    print(f"\n{'='*60}")
    print(f"🔍 LOGIN REQUEST RECEIVED")
    print(f"{'='*60}")
    print(f"Username provided: '{login_data.username}'")
    print(f"Password provided: {'*' * len(login_data.password)} (length: {len(login_data.password)})")
    
    # Find user by username
    user = db.query(UserModel).filter(UserModel.username == login_data.username).first()
    
    if not user:
        print(f"❌ User '{login_data.username}' NOT FOUND in database")
        print(f"Available users: {[u.username for u in db.query(UserModel).all()]}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password"
        )
    
    print(f"✅ User found: {user.username}")
    print(f"   ID: {user.id}")
    print(f"   Role: {user.role}")
    print(f"   Status: {user.status}")
    print(f"   Stored password hash: {user.password[:50]}...")
    
    # Verify password
    print(f"\n🔐 Verifying password...")
    is_password_valid = verify_password(login_data.password, user.password)
    print(f"   Password valid: {is_password_valid}")
    
    if not is_password_valid:
        print(f"❌ Password verification FAILED")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password"
        )
    
    # Check if user is active
    if not user.status:
        print(f"❌ User is INACTIVE")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive"
        )
    
    # Create token
    print(f"\n🎫 Creating access token...")
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.id},
        expires_delta=access_token_expires
    )
    
    print(f"✅ Token created successfully")
    print(f"   Token: {access_token[:50]}...")
    print(f"{'='*60}\n")
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": user
    }
