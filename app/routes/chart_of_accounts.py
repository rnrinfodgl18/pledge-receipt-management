"""Chart of Accounts routes for managing pawn shop accounts."""
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import ChartOfAccounts as ChartOfAccountsModel, Company as CompanyModel
from app import schemas
from app.auth import get_current_user
from app.accounting_utils import create_default_coa

coa_router = APIRouter(prefix="/chart-of-accounts", tags=["chart_of_accounts"])


@coa_router.post("/initialize-default/{company_id}")
def initialize_default_coa(
    company_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Initialize default chart of accounts for a company. (Requires authentication)"""
    # Check if company exists
    company = db.query(CompanyModel).filter(CompanyModel.id == company_id).first()
    if not company:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Company not found"
        )
    
    # Create default accounts
    success = create_default_coa(db, company_id)
    
    if success:
        return {
            "status": "success",
            "message": f"✅ Default Chart of Accounts created for company {company.company_name}",
            "company_id": company_id,
            "accounts_created": 20
        }
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Accounts already exist for this company or an error occurred"
        )


@coa_router.post("/", response_model=schemas.ChartOfAccounts, status_code=status.HTTP_201_CREATED)
def create_account(
    account: schemas.ChartOfAccountsCreate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Create a new account in chart of accounts. (Requires authentication)"""
    # Check if company exists
    company = db.query(CompanyModel).filter(CompanyModel.id == account.company_id).first()
    if not company:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Company not found"
        )
    
    # Check if account_code already exists for this company
    existing = db.query(ChartOfAccountsModel).filter(
        ChartOfAccountsModel.account_code == account.account_code,
        ChartOfAccountsModel.company_id == account.company_id
    ).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Account code already exists for this company"
        )
    
    # Check if sub_account_of exists if provided
    if account.sub_account_of:
        parent_account = db.query(ChartOfAccountsModel).filter(
            ChartOfAccountsModel.id == account.sub_account_of
        ).first()
        if not parent_account:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Parent account not found"
            )
    
    db_account = ChartOfAccountsModel(**account.dict())
    db.add(db_account)
    db.commit()
    db.refresh(db_account)
    return db_account


@coa_router.get("/{company_id}", response_model=List[schemas.ChartOfAccounts])
def list_accounts(
    company_id: int,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """List all accounts for a company. (Requires authentication)"""
    # Check if company exists
    company = db.query(CompanyModel).filter(CompanyModel.id == company_id).first()
    if not company:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Company not found"
        )
    
    accounts = db.query(ChartOfAccountsModel).filter(
        ChartOfAccountsModel.company_id == company_id
    ).offset(skip).limit(limit).all()
    return accounts


@coa_router.get("/{company_id}/{account_id}", response_model=schemas.ChartOfAccounts)
def get_account(
    company_id: int,
    account_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Get a specific account. (Requires authentication)"""
    account = db.query(ChartOfAccountsModel).filter(
        ChartOfAccountsModel.id == account_id,
        ChartOfAccountsModel.company_id == company_id
    ).first()
    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Account not found"
        )
    return account


@coa_router.put("/{account_id}", response_model=schemas.ChartOfAccounts)
def update_account(
    account_id: int,
    account: schemas.ChartOfAccountsUpdate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Update an account. (Requires authentication)"""
    db_account = db.query(ChartOfAccountsModel).filter(ChartOfAccountsModel.id == account_id).first()
    if not db_account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Account not found"
        )
    
    # Check account_code uniqueness if being updated
    if account.account_code and account.account_code != db_account.account_code:
        existing = db.query(ChartOfAccountsModel).filter(
            ChartOfAccountsModel.account_code == account.account_code,
            ChartOfAccountsModel.company_id == db_account.company_id
        ).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Account code already exists"
            )
    
    update_data = account.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_account, field, value)
    
    db.add(db_account)
    db.commit()
    db.refresh(db_account)
    return db_account


@coa_router.delete("/{account_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_account(
    account_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Delete an account. (Requires authentication)"""
    account = db.query(ChartOfAccountsModel).filter(ChartOfAccountsModel.id == account_id).first()
    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Account not found"
        )
    
    db.delete(account)
    db.commit()
    return None
