"""JewelType routes for CRUD operations."""
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import JewelType as JewelTypeModel
from app import schemas
from app.auth import get_current_user

jewel_types_router = APIRouter(prefix="/jewel-types", tags=["jewel_types"])


@jewel_types_router.post("/", response_model=schemas.JewelType, status_code=status.HTTP_201_CREATED)
def create_jewel_type(
    jewel_type: schemas.JewelTypeCreate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Create a new jewel type. (Requires authentication)"""
    # Check if jewel_name already exists
    existing = db.query(JewelTypeModel).filter(
        JewelTypeModel.jewel_name == jewel_type.jewel_name
    ).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Jewel type already exists"
        )
    
    db_jewel_type = JewelTypeModel(**jewel_type.dict())
    db.add(db_jewel_type)
    db.commit()
    db.refresh(db_jewel_type)
    return db_jewel_type


@jewel_types_router.get("/", response_model=List[schemas.JewelType])
def list_jewel_types(
    skip: int = 0,
    limit: int = 10,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """List all jewel types with pagination. (Requires authentication)"""
    jewel_types = db.query(JewelTypeModel).offset(skip).limit(limit).all()
    return jewel_types


@jewel_types_router.get("/{jewel_type_id}", response_model=schemas.JewelType)
def get_jewel_type(
    jewel_type_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Get a specific jewel type by ID. (Requires authentication)"""
    db_jewel_type = db.query(JewelTypeModel).filter(JewelTypeModel.id == jewel_type_id).first()
    if db_jewel_type is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Jewel type not found"
        )
    return db_jewel_type


@jewel_types_router.put("/{jewel_type_id}", response_model=schemas.JewelType)
def update_jewel_type(
    jewel_type_id: int,
    jewel_type: schemas.JewelTypeUpdate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Update an existing jewel type. (Requires authentication)"""
    db_jewel_type = db.query(JewelTypeModel).filter(JewelTypeModel.id == jewel_type_id).first()
    if db_jewel_type is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Jewel type not found"
        )
    
    # Check jewel_name uniqueness if being updated
    if jewel_type.jewel_name and jewel_type.jewel_name != db_jewel_type.jewel_name:
        existing = db.query(JewelTypeModel).filter(
            JewelTypeModel.jewel_name == jewel_type.jewel_name
        ).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Jewel type already exists"
            )
    
    update_data = jewel_type.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_jewel_type, field, value)
    
    db.add(db_jewel_type)
    db.commit()
    db.refresh(db_jewel_type)
    return db_jewel_type


@jewel_types_router.delete("/{jewel_type_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_jewel_type(
    jewel_type_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Delete a jewel type. (Requires authentication)"""
    db_jewel_type = db.query(JewelTypeModel).filter(JewelTypeModel.id == jewel_type_id).first()
    if db_jewel_type is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Jewel type not found"
        )
    
    db.delete(db_jewel_type)
    db.commit()
    return None
