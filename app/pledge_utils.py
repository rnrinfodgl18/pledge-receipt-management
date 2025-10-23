"""Utility functions for pledge operations and accounting integration."""
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import func as sqlfunc
from app.models import (
    Pledge as PledgeModel,
    Scheme as SchemeModel,
    LedgerEntries as LedgerEntriesModel,
    ChartOfAccounts as ChartOfAccountsModel
)


def generate_pledge_no(db: Session, scheme_id: int, company_id: int) -> str:
    """
    Generate unique pledge number with scheme prefix.
    Format: {prefix}-{year}-{sequence}
    Example: GLD-2025-0001
    
    Args:
        db: Database session
        scheme_id: Scheme ID
        company_id: Company ID
    
    Returns:
        Generated pledge number
    """
    try:
        # Get scheme prefix
        scheme = db.query(SchemeModel).filter(SchemeModel.id == scheme_id).first()
        if not scheme:
            raise Exception(f"Scheme {scheme_id} not found")
        
        prefix = scheme.prefix
        current_year = datetime.now().year
        
        # Get current sequence for this scheme in current year
        latest_pledge = db.query(PledgeModel).filter(
            PledgeModel.scheme_id == scheme_id,
            PledgeModel.pledge_no.startswith(f"{prefix}-{current_year}")
        ).order_by(PledgeModel.id.desc()).first()
        
        if latest_pledge:
            # Extract sequence number from latest pledge
            parts = latest_pledge.pledge_no.split("-")
            if len(parts) >= 3:
                try:
                    sequence = int(parts[2]) + 1
                except ValueError:
                    sequence = 1
            else:
                sequence = 1
        else:
            sequence = 1
        
        # Generate pledge number
        pledge_no = f"{prefix}-{current_year}-{str(sequence).zfill(4)}"
        return pledge_no
    
    except Exception as e:
        print(f"Error generating pledge number: {str(e)}")
        raise


def create_pledge_ledger_entries(
    db: Session,
    pledge: PledgeModel,
    company_id: int,
    created_by_id: int
) -> bool:
    """
    Create automatic ledger entries for a pledge.
    
    Transactions:
    1. Debit: Pledged Items (1040)
    2. Credit: Customer Receivable (1051xxxx)
    3. Debit: Cash/Bank (Payment Account)
    4. Credit: Pledge Interest Income (4000)
    
    Args:
        db: Database session
        pledge: Pledge model instance
        company_id: Company ID
        created_by_id: User ID who created pledge
    
    Returns:
        True if successful
    """
    try:
        pledge_date = pledge.pledge_date
        
        # 1. Debit Pledged Items Account - for the maximum value of items
        pledged_items_account = db.query(ChartOfAccountsModel).filter(
            ChartOfAccountsModel.account_code == "1040",
            ChartOfAccountsModel.company_id == company_id
        ).first()
        
        if pledged_items_account:
            entry1 = LedgerEntriesModel(
                company_id=company_id,
                account_id=pledged_items_account.id,
                transaction_date=pledge_date,
                transaction_type="Debit",
                amount=pledge.maximum_value,
                description=f"Pledged items received - {pledge.pledge_no}",
                reference_type="Pledge",
                reference_id=pledge.id,
                created_by=created_by_id
            )
            db.add(entry1)
        
        # 2. Credit Customer Receivable Account - for loan amount
        customer_code = f"1051{str(pledge.customer_id).zfill(4)}"
        customer_account = db.query(ChartOfAccountsModel).filter(
            ChartOfAccountsModel.account_code == customer_code,
            ChartOfAccountsModel.company_id == company_id
        ).first()
        
        if customer_account:
            entry2 = LedgerEntriesModel(
                company_id=company_id,
                account_id=customer_account.id,
                transaction_date=pledge_date,
                transaction_type="Credit",
                amount=pledge.loan_amount,
                description=f"Loan advanced against pledge - {pledge.pledge_no}",
                reference_type="Pledge",
                reference_id=pledge.id,
                created_by=created_by_id
            )
            db.add(entry2)
        
        # 3. Debit Cash/Bank Account - for loan amount
        if pledge.payment_account_id:
            payment_account = db.query(ChartOfAccountsModel).filter(
                ChartOfAccountsModel.id == pledge.payment_account_id
            ).first()
        else:
            # Default to Cash account
            payment_account = db.query(ChartOfAccountsModel).filter(
                ChartOfAccountsModel.account_code == "1000",
                ChartOfAccountsModel.company_id == company_id
            ).first()
        
        if payment_account:
            entry3 = LedgerEntriesModel(
                company_id=company_id,
                account_id=payment_account.id,
                transaction_date=pledge_date,
                transaction_type="Credit",
                amount=pledge.loan_amount,
                description=f"Loan disbursed - {pledge.pledge_no}",
                reference_type="Pledge",
                reference_id=pledge.id,
                created_by=created_by_id
            )
            db.add(entry3)
        
        # 4. Record First Month Interest Income
        if pledge.first_month_interest > 0:
            interest_account = db.query(ChartOfAccountsModel).filter(
                ChartOfAccountsModel.account_code == "4000",
                ChartOfAccountsModel.company_id == company_id
            ).first()
            
            if interest_account:
                entry4 = LedgerEntriesModel(
                    company_id=company_id,
                    account_id=interest_account.id,
                    transaction_date=pledge_date,
                    transaction_type="Credit",
                    amount=pledge.first_month_interest,
                    description=f"First month interest - {pledge.pledge_no}",
                    reference_type="Pledge",
                    reference_id=pledge.id,
                    created_by=created_by_id
                )
                db.add(entry4)
            
            # Debit Cash for interest received
            if payment_account:
                entry5 = LedgerEntriesModel(
                    company_id=company_id,
                    account_id=payment_account.id,
                    transaction_date=pledge_date,
                    transaction_type="Debit",
                    amount=pledge.first_month_interest,
                    description=f"First month interest received - {pledge.pledge_no}",
                    reference_type="Pledge",
                    reference_id=pledge.id,
                    created_by=created_by_id
                )
                db.add(entry5)
        
        db.commit()
        print(f"✅ Ledger entries created for pledge: {pledge.pledge_no}")
        return True
    
    except Exception as e:
        db.rollback()
        print(f"❌ Error creating ledger entries: {str(e)}")
        return False


def reverse_pledge_ledger_entries(
    db: Session,
    pledge_id: int,
    company_id: int
) -> bool:
    """
    Reverse/Delete ledger entries for a pledge when it's deleted/cancelled.
    
    Args:
        db: Database session
        pledge_id: Pledge ID
        company_id: Company ID
    
    Returns:
        True if successful
    """
    try:
        # Find and delete all ledger entries for this pledge
        entries = db.query(LedgerEntriesModel).filter(
            LedgerEntriesModel.reference_type == "Pledge",
            LedgerEntriesModel.reference_id == pledge_id,
            LedgerEntriesModel.company_id == company_id
        ).all()
        
        for entry in entries:
            db.delete(entry)
        
        db.commit()
        print(f"✅ Ledger entries reversed for pledge ID: {pledge_id}")
        return True
    
    except Exception as e:
        db.rollback()
        print(f"❌ Error reversing ledger entries: {str(e)}")
        return False
