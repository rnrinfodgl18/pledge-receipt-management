"""Authentication routes for login and token generation."""
from datetime import timedelta
import logging
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import User as UserModel
from app import schemas
from app.security import verify_password, hash_password
from app.auth import create_access_token, ACCESS_TOKEN_EXPIRE_MINUTES, get_current_user

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


@auth_router.post("/change-password", response_model=schemas.ChangePasswordResponse)
def change_password(
    password_data: schemas.ChangePasswordRequest,
    current_user: UserModel = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Change password for authenticated user."""
    print(f"\n{'='*60}")
    print(f"🔐 CHANGE PASSWORD REQUEST")
    print(f"{'='*60}")
    print(f"User ID: {current_user.id}")
    print(f"Username: {current_user.username}")
    
    # Validate that new password and confirm password match
    if password_data.new_password != password_data.confirm_password:
        print(f"❌ New password and confirm password do not match")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="New password and confirm password do not match"
        )
    
    # Validate password length
    if len(password_data.new_password) < 6:
        print(f"❌ New password must be at least 6 characters")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="New password must be at least 6 characters"
        )
    
    # Verify current password is correct
    print(f"🔍 Verifying current password...")
    is_password_valid = verify_password(password_data.current_password, current_user.password)
    
    if not is_password_valid:
        print(f"❌ Current password is incorrect")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Current password is incorrect"
        )
    
    print(f"✅ Current password verified")
    
    # Check that new password is different from current password
    if verify_password(password_data.new_password, current_user.password):
        print(f"⚠️  New password is same as current password")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="New password must be different from current password"
        )
    
    # Hash and update password
    print(f"🔒 Hashing new password...")
    hashed_password = hash_password(password_data.new_password)
    current_user.password = hashed_password
    db.commit()
    
    print(f"✅ Password changed successfully")
    print(f"{'='*60}\n")
    
    return {
        "message": "Password changed successfully",
        "user": current_user
    }