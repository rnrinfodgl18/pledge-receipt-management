"""BankDetails routes for CRUD operations."""
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import BankDetails as BankDetailsModel, ChartOfAccounts as ChartOfAccountsModel
from app import schemas
from app.auth import get_current_user

bank_details_router = APIRouter(prefix="/bank-details", tags=["bank_details"])


def create_bank_coa_account(db: Session, bank_details: BankDetailsModel, company_id: int) -> bool:
    """
    Create COA account for a bank.
    
    Args:
        db: Database session
        bank_details: Bank details model
        company_id: Company ID
    
    Returns:
        True if successful
    """
    try:
        # Generate account code based on bank account number (last 4 digits)
        account_suffix = bank_details.account_number[-4:] if len(bank_details.account_number) >= 4 else "0001"
        account_code = f"101{account_suffix}"
        
        # Check if account code already exists
        existing = db.query(ChartOfAccountsModel).filter(
            ChartOfAccountsModel.account_code == account_code,
            ChartOfAccountsModel.company_id == company_id
        ).first()
        
        if existing:
            account_code = f"101{bank_details.id}"
        
        # Create bank account in COA
        db_coa_account = ChartOfAccountsModel(
            company_id=company_id,
            account_code=account_code,
            account_name=f"{bank_details.bank_name} - {bank_details.account_holder_name}",
            account_type="Assets",
            account_category="Bank",
            opening_balance=0.0,
            description=f"Bank Account: {bank_details.account_number} ({bank_details.ifsc_code})",
            status=True
        )
        db.add(db_coa_account)
        db.commit()
        print(f"✅ COA account created for bank: {account_code}")
        return True
    
    except Exception as e:
        db.rollback()
        print(f"❌ Error creating COA account for bank: {str(e)}")
        return False


def delete_bank_coa_account(db: Session, bank_id: int) -> bool:
    """
    Delete COA account associated with a bank.
    
    Args:
        db: Database session
        bank_id: Bank details ID
    
    Returns:
        True if successful
    """
    try:
        # Find and delete associated COA account
        # Using a naming pattern to find it
        coa_accounts = db.query(ChartOfAccountsModel).filter(
            ChartOfAccountsModel.description.contains(f"Bank Account")
        ).all()
        
        for account in coa_accounts:
            if f"{bank_id}" in str(account.account_code):
                db.delete(account)
        
        db.commit()
        return True
    
    except Exception as e:
        db.rollback()
        print(f"Error deleting COA account: {str(e)}")
        return False


@bank_details_router.post("/", response_model=schemas.BankDetails, status_code=status.HTTP_201_CREATED)
def create_bank_details(
    bank_details: schemas.BankDetailsCreate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Create new bank details and auto-create COA account. (Requires authentication)"""
    # Check if account_number already exists
    existing = db.query(BankDetailsModel).filter(
        BankDetailsModel.account_number == bank_details.account_number
    ).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Account number already exists"
        )
    
    # Create bank details
    db_bank_details = BankDetailsModel(**bank_details.dict())
    db.add(db_bank_details)
    db.commit()
    db.refresh(db_bank_details)
    
    # Auto-create COA account for this bank (use company_id 1 as default for now)
    # In production, you might want to pass company_id as a parameter
    create_bank_coa_account(db, db_bank_details, company_id=1)
    
    return db_bank_details


@bank_details_router.get("/", response_model=List[schemas.BankDetails])
def list_bank_details(
    skip: int = 0,
    limit: int = 10,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """List all bank details with pagination. (Requires authentication)"""
    bank_details = db.query(BankDetailsModel).offset(skip).limit(limit).all()
    return bank_details


@bank_details_router.get("/{bank_details_id}", response_model=schemas.BankDetails)
def get_bank_details(
    bank_details_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Get specific bank details by ID. (Requires authentication)"""
    db_bank_details = db.query(BankDetailsModel).filter(BankDetailsModel.id == bank_details_id).first()
    if db_bank_details is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Bank details not found"
        )
    return db_bank_details


@bank_details_router.put("/{bank_details_id}", response_model=schemas.BankDetails)
def update_bank_details(
    bank_details_id: int,
    bank_details: schemas.BankDetailsUpdate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Update existing bank details. (Requires authentication)"""
    db_bank_details = db.query(BankDetailsModel).filter(BankDetailsModel.id == bank_details_id).first()
    if db_bank_details is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Bank details not found"
        )
    
    # Check account_number uniqueness if being updated
    if bank_details.account_number and bank_details.account_number != db_bank_details.account_number:
        existing = db.query(BankDetailsModel).filter(
            BankDetailsModel.account_number == bank_details.account_number
        ).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Account number already exists"
            )
    
    # Update bank details
    update_data = bank_details.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_bank_details, field, value)
    
    db.add(db_bank_details)
    db.commit()
    db.refresh(db_bank_details)
    
    # Update associated COA account if bank name or holder changed
    if bank_details.bank_name or bank_details.account_holder_name:
        try:
            account_suffix = db_bank_details.account_number[-4:] if len(db_bank_details.account_number) >= 4 else "0001"
            account_code = f"101{account_suffix}"
            
            coa_account = db.query(ChartOfAccountsModel).filter(
                ChartOfAccountsModel.account_code == account_code
            ).first()
            
            if coa_account:
                coa_account.account_name = f"{db_bank_details.bank_name} - {db_bank_details.account_holder_name}"
                coa_account.description = f"Bank Account: {db_bank_details.account_number} ({db_bank_details.ifsc_code})"
                db.add(coa_account)
                db.commit()
                print(f"✅ COA account updated for bank: {account_code}")
        except Exception as e:
            print(f"Warning: Could not update COA account: {str(e)}")
    
    return db_bank_details


@bank_details_router.delete("/{bank_details_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_bank_details(
    bank_details_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Delete bank details and associated COA account. (Requires authentication)"""
    db_bank_details = db.query(BankDetailsModel).filter(BankDetailsModel.id == bank_details_id).first()
    if db_bank_details is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Bank details not found"
        )
    
    # Delete associated COA account
    delete_bank_coa_account(db, bank_details_id)
    
    # Delete bank details
    db.delete(db_bank_details)
    db.commit()
    
    return None
