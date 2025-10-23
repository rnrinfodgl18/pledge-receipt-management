"""Scheme routes for CRUD operations."""
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Scheme as SchemeModel, JewelType as JewelTypeModel
from app import schemas
from app.auth import get_current_user

schemes_router = APIRouter(prefix="/schemes", tags=["schemes"])


@schemes_router.post("/", response_model=schemas.Scheme, status_code=status.HTTP_201_CREATED)
def create_scheme(
    scheme: schemas.SchemeCreate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Create a new scheme. (Requires authentication)"""
    # Check if jewel_type_id exists
    jewel_type = db.query(JewelTypeModel).filter(
        JewelTypeModel.id == scheme.jewel_type_id
    ).first()
    if not jewel_type:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Jewel type not found"
        )
    
    # Check if scheme_name already exists
    existing_name = db.query(SchemeModel).filter(
        SchemeModel.scheme_name == scheme.scheme_name
    ).first()
    if existing_name:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Scheme name already exists"
        )
    
    # Check if short_name already exists
    existing_short = db.query(SchemeModel).filter(
        SchemeModel.short_name == scheme.short_name
    ).first()
    if existing_short:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Short name already exists"
        )
    
    # Check if prefix already exists
    existing_prefix = db.query(SchemeModel).filter(
        SchemeModel.prefix == scheme.prefix
    ).first()
    if existing_prefix:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Prefix already exists"
        )
    
    db_scheme = SchemeModel(**scheme.dict())
    db.add(db_scheme)
    db.commit()
    db.refresh(db_scheme)
    return db_scheme


@schemes_router.get("/", response_model=List[schemas.Scheme])
def list_schemes(
    skip: int = 0,
    limit: int = 10,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """List all schemes with pagination. (Requires authentication)"""
    schemes = db.query(SchemeModel).offset(skip).limit(limit).all()
    return schemes


@schemes_router.get("/{scheme_id}", response_model=schemas.Scheme)
def get_scheme(
    scheme_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Get a specific scheme by ID. (Requires authentication)"""
    db_scheme = db.query(SchemeModel).filter(SchemeModel.id == scheme_id).first()
    if db_scheme is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Scheme not found"
        )
    return db_scheme


@schemes_router.get("/by-jewel-type/{jewel_type_id}", response_model=List[schemas.Scheme])
def get_schemes_by_jewel_type(
    jewel_type_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Get all schemes for a specific jewel type. (Requires authentication)"""
    schemes = db.query(SchemeModel).filter(
        SchemeModel.jewel_type_id == jewel_type_id
    ).all()
    if not schemes:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No schemes found for this jewel type"
        )
    return schemes


@schemes_router.put("/{scheme_id}", response_model=schemas.Scheme)
def update_scheme(
    scheme_id: int,
    scheme: schemas.SchemeUpdate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Update an existing scheme. (Requires authentication)"""
    db_scheme = db.query(SchemeModel).filter(SchemeModel.id == scheme_id).first()
    if db_scheme is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Scheme not found"
        )
    
    # Check if jewel_type_id exists if being updated
    if scheme.jewel_type_id and scheme.jewel_type_id != db_scheme.jewel_type_id:
        jewel_type = db.query(JewelTypeModel).filter(
            JewelTypeModel.id == scheme.jewel_type_id
        ).first()
        if not jewel_type:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Jewel type not found"
            )
    
    # Check scheme_name uniqueness if being updated
    if scheme.scheme_name and scheme.scheme_name != db_scheme.scheme_name:
        existing_name = db.query(SchemeModel).filter(
            SchemeModel.scheme_name == scheme.scheme_name
        ).first()
        if existing_name:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Scheme name already exists"
            )
    
    # Check short_name uniqueness if being updated
    if scheme.short_name and scheme.short_name != db_scheme.short_name:
        existing_short = db.query(SchemeModel).filter(
            SchemeModel.short_name == scheme.short_name
        ).first()
        if existing_short:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Short name already exists"
            )
    
    # Check prefix uniqueness if being updated
    if scheme.prefix and scheme.prefix != db_scheme.prefix:
        existing_prefix = db.query(SchemeModel).filter(
            SchemeModel.prefix == scheme.prefix
        ).first()
        if existing_prefix:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Prefix already exists"
            )
    
    update_data = scheme.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_scheme, field, value)
    
    db.add(db_scheme)
    db.commit()
    db.refresh(db_scheme)
    return db_scheme


@schemes_router.delete("/{scheme_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_scheme(
    scheme_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Delete a scheme. (Requires authentication)"""
    db_scheme = db.query(SchemeModel).filter(SchemeModel.id == scheme_id).first()
    if db_scheme is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Scheme not found"
        )
    
    db.delete(db_scheme)
    db.commit()
    return None
