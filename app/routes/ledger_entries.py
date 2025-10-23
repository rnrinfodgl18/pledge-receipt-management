"""Ledger Entries routes for recording financial transactions."""
from typing import List
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import and_, func as sqlfunc
from app.database import get_db
from app.models import (
    LedgerEntries as LedgerEntriesModel, 
    ChartOfAccounts as ChartOfAccountsModel,
    Company as CompanyModel
)
from app import schemas
from app.auth import get_current_user

ledger_router = APIRouter(prefix="/ledger-entries", tags=["ledger_entries"])


def calculate_running_balance(db: Session, account_id: int, company_id: int, before_date: datetime = None) -> float:
    """Calculate running balance for an account up to a specific date."""
    query = db.query(sqlfunc.sum(
        sqlfunc.case(
            (LedgerEntriesModel.transaction_type == "Debit", LedgerEntriesModel.amount),
            (LedgerEntriesModel.transaction_type == "Credit", -LedgerEntriesModel.amount),
            else_=0
        )
    )).filter(
        LedgerEntriesModel.account_id == account_id,
        LedgerEntriesModel.company_id == company_id
    )
    
    if before_date:
        query = query.filter(LedgerEntriesModel.transaction_date <= before_date)
    
    balance = query.scalar()
    
    # Add opening balance
    account = db.query(ChartOfAccountsModel).filter(ChartOfAccountsModel.id == account_id).first()
    if account:
        balance = (balance or 0) + account.opening_balance
    
    return balance or 0


@ledger_router.post("/", response_model=schemas.LedgerEntries, status_code=status.HTTP_201_CREATED)
def create_ledger_entry(
    entry: schemas.LedgerEntriesCreate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Create a new ledger entry. (Requires authentication)"""
    # Check if company exists
    company = db.query(CompanyModel).filter(CompanyModel.id == entry.company_id).first()
    if not company:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Company not found"
        )
    
    # Check if account exists
    account = db.query(ChartOfAccountsModel).filter(
        ChartOfAccountsModel.id == entry.account_id,
        ChartOfAccountsModel.company_id == entry.company_id
    ).first()
    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Account not found"
        )
    
    # Validate transaction type
    if entry.transaction_type not in ["Debit", "Credit"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Transaction type must be 'Debit' or 'Credit'"
        )
    
    # Calculate running balance
    running_balance = calculate_running_balance(
        db, entry.account_id, entry.company_id, entry.transaction_date
    )
    
    if entry.transaction_type == "Debit":
        running_balance += entry.amount
    else:
        running_balance -= entry.amount
    
    # Create ledger entry
    db_entry = LedgerEntriesModel(
        company_id=entry.company_id,
        account_id=entry.account_id,
        transaction_date=entry.transaction_date,
        transaction_type=entry.transaction_type,
        amount=entry.amount,
        description=entry.description,
        reference_type=entry.reference_type,
        reference_id=entry.reference_id,
        running_balance=running_balance,
        created_by=current_user.id
    )
    
    db.add(db_entry)
    db.commit()
    db.refresh(db_entry)
    return db_entry


@ledger_router.get("/{company_id}", response_model=List[schemas.LedgerEntries])
def list_ledger_entries(
    company_id: int,
    account_id: int = Query(None),
    start_date: datetime = Query(None),
    end_date: datetime = Query(None),
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """List ledger entries for a company with optional filters. (Requires authentication)"""
    # Check if company exists
    company = db.query(CompanyModel).filter(CompanyModel.id == company_id).first()
    if not company:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Company not found"
        )
    
    query = db.query(LedgerEntriesModel).filter(
        LedgerEntriesModel.company_id == company_id
    )
    
    # Filter by account if provided
    if account_id:
        query = query.filter(LedgerEntriesModel.account_id == account_id)
    
    # Filter by date range if provided
    if start_date:
        query = query.filter(LedgerEntriesModel.transaction_date >= start_date)
    if end_date:
        query = query.filter(LedgerEntriesModel.transaction_date <= end_date)
    
    entries = query.order_by(LedgerEntriesModel.transaction_date).offset(skip).limit(limit).all()
    return entries


@ledger_router.get("/{company_id}/{entry_id}", response_model=schemas.LedgerEntries)
def get_ledger_entry(
    company_id: int,
    entry_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Get a specific ledger entry. (Requires authentication)"""
    entry = db.query(LedgerEntriesModel).filter(
        LedgerEntriesModel.id == entry_id,
        LedgerEntriesModel.company_id == company_id
    ).first()
    if not entry:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ledger entry not found"
        )
    return entry


@ledger_router.get("/{company_id}/account/{account_id}/balance")
def get_account_balance(
    company_id: int,
    account_id: int,
    as_of_date: datetime = Query(None),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Get account balance as of a specific date. (Requires authentication)"""
    # Check if account exists
    account = db.query(ChartOfAccountsModel).filter(
        ChartOfAccountsModel.id == account_id,
        ChartOfAccountsModel.company_id == company_id
    ).first()
    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Account not found"
        )
    
    balance = calculate_running_balance(db, account_id, company_id, as_of_date)
    
    return {
        "account_id": account_id,
        "account_name": account.account_name,
        "as_of_date": as_of_date or datetime.now(),
        "balance": balance
    }


@ledger_router.get("/{company_id}/trial-balance")
def get_trial_balance(
    company_id: int,
    as_of_date: datetime = Query(None),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Get trial balance for a company. (Requires authentication)"""
    # Check if company exists
    company = db.query(CompanyModel).filter(CompanyModel.id == company_id).first()
    if not company:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Company not found"
        )
    
    # Get all accounts for the company
    accounts = db.query(ChartOfAccountsModel).filter(
        ChartOfAccountsModel.company_id == company_id,
        ChartOfAccountsModel.status == True
    ).all()
    
    trial_balance = []
    total_debit = 0
    total_credit = 0
    
    for account in accounts:
        balance = calculate_running_balance(db, account.id, company_id, as_of_date)
        
        if balance >= 0:
            total_debit += balance
            trial_balance.append({
                "account_id": account.id,
                "account_code": account.account_code,
                "account_name": account.account_name,
                "account_type": account.account_type,
                "debit": balance,
                "credit": 0
            })
        else:
            total_credit += abs(balance)
            trial_balance.append({
                "account_id": account.id,
                "account_code": account.account_code,
                "account_name": account.account_name,
                "account_type": account.account_type,
                "debit": 0,
                "credit": abs(balance)
            })
    
    return {
        "company_id": company_id,
        "as_of_date": as_of_date or datetime.now(),
        "trial_balance": trial_balance,
        "total_debit": total_debit,
        "total_credit": total_credit,
        "balanced": total_debit == total_credit
    }
