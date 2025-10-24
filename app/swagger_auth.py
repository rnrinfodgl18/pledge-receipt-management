"""Swagger UI authentication utility - enables login in Swagger docs."""
from fastapi import APIRouter, Depends, HTTPException, status, Form
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import timedelta
from app.database import get_db
from app.models import User as UserModel
from app.security import verify_password
from app.auth import create_access_token, ACCESS_TOKEN_EXPIRE_MINUTES

swagger_auth_router = APIRouter(prefix="/token", tags=["authentication"])


@swagger_auth_router.post("/", response_model=dict)
def login_for_swagger(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    """
    OAuth2 standard login endpoint for Swagger UI.
    
    This endpoint enables username/password login directly in Swagger UI.
    Swagger will automatically handle the token and add it to all requests.
    
    Args:
        username: User's username
        password: User's password
    
    Returns:
        Access token for API requests
    """
    print(f"\n{'='*60}")
    print(f"🔍 SWAGGER OAUTH2 LOGIN REQUEST")
    print(f"{'='*60}")
    print(f"Username: '{form_data.username}'")
    
    # Find user by username
    user = db.query(UserModel).filter(UserModel.username == form_data.username).first()
    
    if not user:
        print(f"❌ User '{form_data.username}' NOT FOUND")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    print(f"✅ User found: {user.username} (ID: {user.id})")
    
    # Verify password
    print(f"🔐 Verifying password...")
    is_password_valid = verify_password(form_data.password, user.password)
    
    if not is_password_valid:
        print(f"❌ Password verification FAILED")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    print(f"✅ Password verified")
    
    # Check if user is active
    if not user.status:
        print(f"❌ User is INACTIVE")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive"
        )
    
    # Create token
    print(f"🎫 Creating access token...")
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.id},
        expires_delta=access_token_expires
    )
    
    print(f"✅ Token created successfully")
    print(f"{'='*60}\n")
    
    return {
        "access_token": access_token,
        "token_type": "bearer"
    }
