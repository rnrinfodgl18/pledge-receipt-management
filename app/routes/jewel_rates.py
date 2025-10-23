"""JewelRate routes for CRUD operations."""
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import JewelRate as JewelRateModel, JewelType as JewelTypeModel
from app import schemas
from app.auth import get_current_user

jewel_rates_router = APIRouter(prefix="/jewel-rates", tags=["jewel_rates"])


@jewel_rates_router.post("/", response_model=schemas.JewelRate, status_code=status.HTTP_201_CREATED)
def create_jewel_rate(
    jewel_rate: schemas.JewelRateCreate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Create a new jewel rate. (Requires authentication)"""
    # Check if jewel_type_id exists
    jewel_type = db.query(JewelTypeModel).filter(
        JewelTypeModel.id == jewel_rate.jewel_type_id
    ).first()
    if not jewel_type:
        raise HTTPException(
            status_code=status.HTTP_404_BAD_REQUEST,
            detail="Jewel type not found"
        )
    
    # Check if rate already exists for this jewel type
    existing = db.query(JewelRateModel).filter(
        JewelRateModel.jewel_type_id == jewel_rate.jewel_type_id
    ).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Rate already exists for this jewel type"
        )
    
    db_jewel_rate = JewelRateModel(**jewel_rate.dict())
    db.add(db_jewel_rate)
    db.commit()
    db.refresh(db_jewel_rate)
    return db_jewel_rate


@jewel_rates_router.get("/", response_model=List[schemas.JewelRate])
def list_jewel_rates(
    skip: int = 0,
    limit: int = 10,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """List all jewel rates with pagination. (Requires authentication)"""
    jewel_rates = db.query(JewelRateModel).offset(skip).limit(limit).all()
    return jewel_rates


@jewel_rates_router.get("/{jewel_rate_id}", response_model=schemas.JewelRate)
def get_jewel_rate(
    jewel_rate_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Get a specific jewel rate by ID. (Requires authentication)"""
    db_jewel_rate = db.query(JewelRateModel).filter(JewelRateModel.id == jewel_rate_id).first()
    if db_jewel_rate is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Jewel rate not found"
        )
    return db_jewel_rate


@jewel_rates_router.get("/by-jewel-type/{jewel_type_id}", response_model=schemas.JewelRate)
def get_jewel_rate_by_type(
    jewel_type_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Get jewel rate for a specific jewel type. (Requires authentication)"""
    db_jewel_rate = db.query(JewelRateModel).filter(
        JewelRateModel.jewel_type_id == jewel_type_id
    ).first()
    if db_jewel_rate is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Rate not found for this jewel type"
        )
    return db_jewel_rate


@jewel_rates_router.put("/{jewel_rate_id}", response_model=schemas.JewelRate)
def update_jewel_rate(
    jewel_rate_id: int,
    jewel_rate: schemas.JewelRateUpdate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Update an existing jewel rate. (Requires authentication)"""
    db_jewel_rate = db.query(JewelRateModel).filter(JewelRateModel.id == jewel_rate_id).first()
    if db_jewel_rate is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Jewel rate not found"
        )
    
    # Check if jewel_type_id exists if being updated
    if jewel_rate.jewel_type_id and jewel_rate.jewel_type_id != db_jewel_rate.jewel_type_id:
        jewel_type = db.query(JewelTypeModel).filter(
            JewelTypeModel.id == jewel_rate.jewel_type_id
        ).first()
        if not jewel_type:
            raise HTTPException(
                status_code=status.HTTP_404_BAD_REQUEST,
                detail="Jewel type not found"
            )
        
        # Check if rate already exists for new jewel type
        existing = db.query(JewelRateModel).filter(
            JewelRateModel.jewel_type_id == jewel_rate.jewel_type_id
        ).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Rate already exists for this jewel type"
            )
    
    update_data = jewel_rate.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_jewel_rate, field, value)
    
    db.add(db_jewel_rate)
    db.commit()
    db.refresh(db_jewel_rate)
    return db_jewel_rate


@jewel_rates_router.delete("/{jewel_rate_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_jewel_rate(
    jewel_rate_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Delete a jewel rate. (Requires authentication)"""
    db_jewel_rate = db.query(JewelRateModel).filter(JewelRateModel.id == jewel_rate_id).first()
    if db_jewel_rate is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Jewel rate not found"
        )
    
    db.delete(db_jewel_rate)
    db.commit()
    return None
