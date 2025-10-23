"""Receipt utilities for generating receipt numbers and COA entries."""
from sqlalchemy.orm import Session
from datetime import datetime
from app.models import (
    PledgeReceipt, ReceiptItem, Pledge, LedgerEntries, 
    ChartOfAccounts, PledgeReceipt as ReceiptModel
)


def generate_receipt_no(db: Session, company_id: int, year: int = None) -> str:
    """
    Generate a unique receipt number in format: RCP-YYYY-SEQUENCE.
    
    Args:
        db: Database session
        company_id: Company ID
        year: Year for receipt (default: current year)
    
    Returns:
        Receipt number string (e.g., RCP-2025-0001)
    """
    if year is None:
        year = datetime.now().year
    
    # Get the count of receipts for this company in this year
    receipts_this_year = db.query(PledgeReceipt).filter(
        PledgeReceipt.company_id == company_id,
        PledgeReceipt.created_at >= datetime(year, 1, 1),
        PledgeReceipt.created_at < datetime(year + 1, 1, 1)
    ).count()
    
    sequence = receipts_this_year + 1
    receipt_no = f"RCP-{year}-{sequence:04d}"
    
    return receipt_no


def get_or_create_account(db: Session, company_id: int, account_code: str, 
                         account_name: str, account_type: str, 
                         account_category: str) -> int:
    """
    Get or create a chart of accounts entry.
    
    Args:
        db: Database session
        company_id: Company ID
        account_code: Account code (e.g., "1000")
        account_name: Account name (e.g., "Cash")
        account_type: Account type (e.g., "Assets")
        account_category: Account category (e.g., "Cash")
    
    Returns:
        Account ID
    """
    account = db.query(ChartOfAccounts).filter(
        ChartOfAccounts.company_id == company_id,
        ChartOfAccounts.account_code == account_code
    ).first()
    
    if not account:
        account = ChartOfAccounts(
            company_id=company_id,
            account_code=account_code,
            account_name=account_name,
            account_type=account_type,
            account_category=account_category,
            opening_balance=0.0,
            status=True
        )
        db.add(account)
        db.flush()
    
    return account.id


def create_receipt_coa_entries(db: Session, receipt: PledgeReceipt, 
                               user_id: int) -> bool:
    """
    Create automatic COA entries for a receipt payment.
    
    Creates the following entries:
    - Debit: Cash (account 1000)
    - Credit: Receivable (account 1051)
    - Credit: Interest Income (account 4000)
    - Debit/Credit: Discount/Penalty accounts as needed
    
    Args:
        db: Database session
        receipt: Receipt object
        user_id: User creating the entries
    
    Returns:
        True if successful, False otherwise
    """
    try:
        company_id = receipt.company_id
        total_principal = 0.0
        total_interest = 0.0
        total_discount = 0.0
        total_penalty = 0.0
        
        # Calculate totals from receipt items
        for item in receipt.receipt_items:
            total_principal += item.paid_principal
            total_interest += item.paid_interest
            total_discount += item.paid_discount
            total_penalty += item.paid_penalty
        
        # Get or create accounts
        cash_account_id = get_or_create_account(
            db, company_id, "1000", "Cash", "Assets", "Cash"
        )
        
        receivable_account_id = get_or_create_account(
            db, company_id, "1051", "Receivable - Pledges", "Assets", "Receivable"
        )
        
        interest_account_id = get_or_create_account(
            db, company_id, "4000", "Interest Income", "Income", "Interest Income"
        )
        
        discount_account_id = get_or_create_account(
            db, company_id, "5030", "Interest Discount", "Expenses", "Discount"
        )
        
        penalty_account_id = get_or_create_account(
            db, company_id, "4050", "Penalty Income", "Income", "Penalty"
        )
        
        # Entry 1: Debit Cash with total receipt amount
        entry_cash = LedgerEntries(
            company_id=company_id,
            account_id=cash_account_id,
            transaction_date=receipt.receipt_date,
            transaction_type="Debit",
            amount=receipt.receipt_amount,
            description=f"Receipt {receipt.receipt_no} - Cash received",
            reference_type="Receipt",
            reference_id=receipt.id,
            created_by=user_id
        )
        db.add(entry_cash)
        
        # Entry 2: Credit Receivable with principal amount
        if total_principal > 0:
            entry_receivable = LedgerEntries(
                company_id=company_id,
                account_id=receivable_account_id,
                transaction_date=receipt.receipt_date,
                transaction_type="Credit",
                amount=total_principal,
                description=f"Receipt {receipt.receipt_no} - Principal payment",
                reference_type="Receipt",
                reference_id=receipt.id,
                created_by=user_id
            )
            db.add(entry_receivable)
        
        # Entry 3: Credit Interest Income with interest amount
        if total_interest > 0:
            entry_interest = LedgerEntries(
                company_id=company_id,
                account_id=interest_account_id,
                transaction_date=receipt.receipt_date,
                transaction_type="Credit",
                amount=total_interest,
                description=f"Receipt {receipt.receipt_no} - Interest income",
                reference_type="Receipt",
                reference_id=receipt.id,
                created_by=user_id
            )
            db.add(entry_interest)
        
        # Entry 4: Debit Discount if applicable
        if total_discount > 0:
            entry_discount = LedgerEntries(
                company_id=company_id,
                account_id=discount_account_id,
                transaction_date=receipt.receipt_date,
                transaction_type="Debit",
                amount=total_discount,
                description=f"Receipt {receipt.receipt_no} - Interest discount given",
                reference_type="Receipt",
                reference_id=receipt.id,
                created_by=user_id
            )
            db.add(entry_discount)
        
        # Entry 5: Credit Penalty if applicable
        if total_penalty > 0:
            entry_penalty = LedgerEntries(
                company_id=company_id,
                account_id=penalty_account_id,
                transaction_date=receipt.receipt_date,
                transaction_type="Credit",
                amount=total_penalty,
                description=f"Receipt {receipt.receipt_no} - Penalty income",
                reference_type="Receipt",
                reference_id=receipt.id,
                created_by=user_id
            )
            db.add(entry_penalty)
        
        db.flush()
        
        # Update receipt COA entry status
        receipt.coa_entry_status = "Posted"
        receipt.receipt_status = "Posted"
        
        return True
        
    except Exception as e:
        print(f"Error creating COA entries: {str(e)}")
        return False


def reverse_receipt_ledger_entries(db: Session, receipt_id: int, company_id: int) -> bool:
    """
    Reverse COA entries for a receipt (for void/adjustment operations).
    
    Finds all ledger entries for this receipt and creates reverse entries.
    
    Args:
        db: Database session
        receipt_id: Receipt ID
        company_id: Company ID
    
    Returns:
        True if successful, False otherwise
    """
    try:
        # Get all entries for this receipt
        entries = db.query(LedgerEntries).filter(
            LedgerEntries.reference_type == "Receipt",
            LedgerEntries.reference_id == receipt_id,
            LedgerEntries.company_id == company_id
        ).all()
        
        if not entries:
            return True
        
        # Get receipt for user_id
        receipt = db.query(PledgeReceipt).filter(PledgeReceipt.id == receipt_id).first()
        if not receipt:
            return False
        
        # Create reverse entries
        for entry in entries:
            reverse_type = "Credit" if entry.transaction_type == "Debit" else "Debit"
            reverse_entry = LedgerEntries(
                company_id=company_id,
                account_id=entry.account_id,
                transaction_date=datetime.now(),
                transaction_type=reverse_type,
                amount=entry.amount,
                description=f"Reversal of {entry.description}",
                reference_type="Receipt",
                reference_id=receipt_id,
                created_by=receipt.created_by
            )
            db.add(reverse_entry)
        
        db.flush()
        return True
        
    except Exception as e:
        print(f"Error reversing COA entries: {str(e)}")
        return False


def calculate_receipt_total(receipt_items: list) -> float:
    """
    Calculate total amount for a receipt from items.
    
    Args:
        receipt_items: List of receipt item objects
    
    Returns:
        Total amount
    """
    total = 0.0
    for item in receipt_items:
        total += item.total_amount_paid
    return total


def update_pledge_balance(db: Session, pledge_id: int, 
                         paid_principal: float, paid_interest: float) -> bool:
    """
    Update pledge balance after payment.
    
    Checks if pledge is fully paid and updates status to "Redeemed" if needed.
    
    Args:
        db: Database session
        pledge_id: Pledge ID
        paid_principal: Principal amount paid in this receipt
        paid_interest: Interest amount paid in this receipt
    
    Returns:
        True if successful, False otherwise
    """
    try:
        pledge = db.query(Pledge).filter(Pledge.id == pledge_id).first()
        if not pledge:
            return False
        
        # Get all receipt items for this pledge to calculate total paid
        receipt_items = db.query(ReceiptItem).filter(
            ReceiptItem.pledge_id == pledge_id
        ).all()
        
        total_principal_paid = 0.0
        total_interest_paid = 0.0
        
        for item in receipt_items:
            total_principal_paid += item.paid_principal
            total_interest_paid += item.paid_interest
        
        # Check if fully paid (simple logic - may need enhancement for interest calculation)
        if total_principal_paid >= pledge.loan_amount:
            pledge.status = "Redeemed"
        
        return True
        
    except Exception as e:
        print(f"Error updating pledge balance: {str(e)}")
        return False


def check_full_closure(db: Session, pledge_id: int) -> bool:
    """
    Check if a pledge is fully closed (all outstanding amounts paid).
    
    Args:
        db: Database session
        pledge_id: Pledge ID
    
    Returns:
        True if fully paid, False otherwise
    """
    try:
        pledge = db.query(Pledge).filter(Pledge.id == pledge_id).first()
        if not pledge:
            return False
        
        # Get all receipt items for this pledge
        receipt_items = db.query(ReceiptItem).filter(
            ReceiptItem.pledge_id == pledge_id
        ).all()
        
        total_paid = sum(item.total_amount_paid for item in receipt_items)
        
        # Calculate total outstanding
        outstanding = pledge.loan_amount + pledge.first_month_interest
        
        return total_paid >= outstanding
        
    except Exception as e:
        print(f"Error checking pledge closure: {str(e)}")
        return False
