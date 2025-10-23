"""Company and User routes for CRUD operations."""
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Company as CompanyModel, User as UserModel
from app import schemas
from app.security import hash_password, verify_password
from app.auth import get_current_user, require_admin
from app.file_handler import save_company_logo, delete_company_logo

router = APIRouter()

# ==================== Company Routes ====================

companies_router = APIRouter(prefix="/companies", tags=["companies"])


@companies_router.post("/", response_model=schemas.Company, status_code=status.HTTP_201_CREATED)
def create_company(
    company: schemas.CompanyCreate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Create a new company. (Requires authentication)"""
    # Check if licence_no already exists
    existing = db.query(CompanyModel).filter(
        CompanyModel.licence_no == company.licence_no
    ).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Licence number already exists"
        )
    
    db_company = CompanyModel(**company.dict())
    db.add(db_company)
    db.commit()
    db.refresh(db_company)
    return db_company


@companies_router.get("/", response_model=List[schemas.Company])
def list_companies(
    skip: int = 0,
    limit: int = 10,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """List all companies with pagination. (Requires authentication)"""
    companies = db.query(CompanyModel).offset(skip).limit(limit).all()
    return companies


@companies_router.get("/{company_id}", response_model=schemas.Company)
def get_company(
    company_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Get a specific company by ID. (Requires authentication)"""
    db_company = db.query(CompanyModel).filter(CompanyModel.id == company_id).first()
    if db_company is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Company not found"
        )
    return db_company


@companies_router.put("/{company_id}", response_model=schemas.Company)
def update_company(
    company_id: int,
    company: schemas.CompanyUpdate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Update an existing company. (Requires authentication)"""
    db_company = db.query(CompanyModel).filter(CompanyModel.id == company_id).first()
    if db_company is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Company not found"
        )
    
    # Check licence_no uniqueness if being updated
    if company.licence_no and company.licence_no != db_company.licence_no:
        existing = db.query(CompanyModel).filter(
            CompanyModel.licence_no == company.licence_no
        ).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Licence number already exists"
            )
    
    update_data = company.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_company, field, value)
    
    db.add(db_company)
    db.commit()
    db.refresh(db_company)
    return db_company


@companies_router.delete("/{company_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_company(
    company_id: int,
    db: Session = Depends(get_db),
    admin_user = Depends(require_admin)
):
    """Delete a company. (Requires admin role)"""
    db_company = db.query(CompanyModel).filter(CompanyModel.id == company_id).first()
    if db_company is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Company not found"
        )
    
    db.delete(db_company)
    db.commit()
    return None


@companies_router.post("/{company_id}/upload-logo", response_model=schemas.Company)
def upload_company_logo(
    company_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Upload company logo. (Requires authentication)"""
    # Check if company exists
    db_company = db.query(CompanyModel).filter(CompanyModel.id == company_id).first()
    if db_company is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Company not found"
        )
    
    try:
        # Delete old logo if exists
        if db_company.logo:
            delete_company_logo(db_company.logo)
        
        # Save new logo
        logo_path = save_company_logo(file, company_id)
        
        # Update company logo path
        db_company.logo = logo_path
        db.add(db_company)
        db.commit()
        db.refresh(db_company)
        
        return db_company
    
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error uploading logo: {str(e)}"
        )


# ==================== User Routes ====================

users_router = APIRouter(prefix="/users", tags=["users"])


@users_router.post("/", response_model=schemas.UserResponse, status_code=status.HTTP_201_CREATED)
def create_user(
    user: schemas.UserCreate,
    db: Session = Depends(get_db),
    admin_user = Depends(require_admin)
):
    """Create a new user. (Requires admin role)"""
    # Check if username already exists
    existing = db.query(UserModel).filter(UserModel.username == user.username).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already exists"
        )
    
    # Hash password before storing
    hashed_password = hash_password(user.password)
    db_user = UserModel(
        username=user.username,
        password=hashed_password,
        role=user.role,
        status=user.status
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


@users_router.get("/", response_model=List[schemas.UserResponse])
def list_users(
    skip: int = 0,
    limit: int = 10,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """List all users with pagination. (Requires authentication)"""
    users = db.query(UserModel).offset(skip).limit(limit).all()
    return users


@users_router.get("/{user_id}", response_model=schemas.UserResponse)
def get_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Get a specific user by ID. (Requires authentication)"""
    db_user = db.query(UserModel).filter(UserModel.id == user_id).first()
    if db_user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    return db_user


@users_router.put("/{user_id}", response_model=schemas.UserResponse)
def update_user(
    user_id: int,
    user: schemas.UserUpdate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Update an existing user. (Requires authentication)"""
    db_user = db.query(UserModel).filter(UserModel.id == user_id).first()
    if db_user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Check username uniqueness if being updated
    if user.username and user.username != db_user.username:
        existing = db.query(UserModel).filter(UserModel.username == user.username).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already exists"
            )
    
    update_data = user.dict(exclude_unset=True)
    
    # Hash password if being updated
    if "password" in update_data and update_data["password"]:
        update_data["password"] = hash_password(update_data["password"])
    
    for field, value in update_data.items():
        setattr(db_user, field, value)
    
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


@users_router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    admin_user = Depends(require_admin)
):
    """Delete a user. (Requires admin role)"""
    db_user = db.query(UserModel).filter(UserModel.id == user_id).first()
    if db_user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    db.delete(db_user)
    db.commit()
    return None

