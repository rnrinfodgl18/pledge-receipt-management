"""Utility functions for expense management and ledger integration."""
from sqlalchemy.orm import Session
from datetime import datetime
from typing import Dict, Any

from app.models import (
    ExpenseTransaction as ExpenseTransactionModel,
    ExpenseLedgerAccount,
    ChartOfAccounts as ChartOfAccountsModel,
    LedgerEntries as LedgerEntriesModel,
)


def generate_expense_transaction_no(db: Session, company_id: int) -> str:
    """
    Generate unique expense transaction number.
    Format: EXP-YYYYMM-XXXX
    Example: EXP-202501-0001
    """
    current_date = datetime.now()
    year_month = current_date.strftime("%Y%m")
    prefix = f"EXP-{year_month}"
    
    # Find the last transaction number for this month
    last_transaction = (
        db.query(ExpenseTransactionModel)
        .filter(
            ExpenseTransactionModel.company_id == company_id,
            ExpenseTransactionModel.transaction_no.like(f"{prefix}%")
        )
        .order_by(ExpenseTransactionModel.id.desc())
        .first()
    )
    
    if last_transaction:
        # Extract the sequence number and increment
        last_sequence = int(last_transaction.transaction_no.split("-")[-1])
        new_sequence = last_sequence + 1
    else:
        new_sequence = 1
    
    return f"{prefix}-{new_sequence:04d}"


def create_expense_ledger_entries(
    db: Session,
    expense_transaction: ExpenseTransactionModel,
    company_id: int,
    created_by: int
) -> Dict[str, Any]:
    """
    Create ledger entries for expense transaction.
    
    Creates 2 entries:
    1. Debit entry for expense account
    2. Credit entry for payment account (Cash/Bank)
    
    Also updates expense ledger account balances.
    
    Returns:
        dict: {
            "status": bool,
            "message": str,
            "ledger_entry_ids": str (comma-separated IDs),
            "entries_created": int,
            "total_debits": float,
            "total_credits": float
        }
    """
    try:
        # Get debit and credit accounts
        debit_account = db.query(ExpenseLedgerAccount).filter(
            ExpenseLedgerAccount.id == expense_transaction.debit_account_id
        ).first()
        
        credit_account = db.query(ExpenseLedgerAccount).filter(
            ExpenseLedgerAccount.id == expense_transaction.credit_account_id
        ).first()
        
        if not debit_account or not credit_account:
            return {
                "status": False,
                "message": "Expense ledger accounts not found",
                "ledger_entry_ids": None,
                "entries_created": 0,
                "total_debits": 0.0,
                "total_credits": 0.0
            }
        
        # Get COA accounts
        debit_coa = db.query(ChartOfAccountsModel).filter(
            ChartOfAccountsModel.id == debit_account.coa_account_id
        ).first()
        
        credit_coa = db.query(ChartOfAccountsModel).filter(
            ChartOfAccountsModel.id == credit_account.coa_account_id
        ).first()
        
        if not debit_coa or not credit_coa:
            return {
                "status": False,
                "message": "Chart of accounts not found",
                "ledger_entry_ids": None,
                "entries_created": 0,
                "total_debits": 0.0,
                "total_credits": 0.0
            }
        
        ledger_entry_ids = []
        
        # Entry 1: Debit expense account
        debit_entry = LedgerEntriesModel(
            company_id=company_id,
            account_id=debit_coa.id,
            transaction_date=expense_transaction.transaction_date,
            transaction_type="EXPENSE",
            reference_type="EXPENSE_TRANSACTION",
            reference_id=expense_transaction.id,
            reference_no=expense_transaction.transaction_no,
            description=f"Expense: {expense_transaction.description or 'N/A'}",
            debit_amount=expense_transaction.amount,
            credit_amount=0.0,
            created_by=created_by
        )
        db.add(debit_entry)
        db.flush()
        ledger_entry_ids.append(str(debit_entry.id))
        
        # Update debit account balance (increase for expense)
        debit_account.current_balance += expense_transaction.amount
        
        # Entry 2: Credit payment account (Cash/Bank)
        credit_entry = LedgerEntriesModel(
            company_id=company_id,
            account_id=credit_coa.id,
            transaction_date=expense_transaction.transaction_date,
            transaction_type="EXPENSE",
            reference_type="EXPENSE_TRANSACTION",
            reference_id=expense_transaction.id,
            reference_no=expense_transaction.transaction_no,
            description=f"Payment for: {expense_transaction.description or 'N/A'}",
            debit_amount=0.0,
            credit_amount=expense_transaction.amount,
            created_by=created_by
        )
        db.add(credit_entry)
        db.flush()
        ledger_entry_ids.append(str(credit_entry.id))
        
        # Update credit account balance (decrease for payment)
        credit_account.current_balance -= expense_transaction.amount
        
        db.commit()
        
        return {
            "status": True,
            "message": "Ledger entries created successfully",
            "ledger_entry_ids": ",".join(ledger_entry_ids),
            "entries_created": 2,
            "total_debits": expense_transaction.amount,
            "total_credits": expense_transaction.amount
        }
    
    except Exception as e:
        db.rollback()
        return {
            "status": False,
            "message": f"Error creating ledger entries: {str(e)}",
            "ledger_entry_ids": None,
            "entries_created": 0,
            "total_debits": 0.0,
            "total_credits": 0.0
        }


def reverse_expense_ledger_entries(
    db: Session,
    expense_transaction_id: int,
    company_id: int
) -> Dict[str, Any]:
    """
    Reverse ledger entries for an expense transaction.
    
    Creates reversing entries and updates account balances.
    
    Returns:
        dict: {
            "status": bool,
            "message": str,
            "entries_reversed": int
        }
    """
    try:
        # Get the expense transaction
        transaction = db.query(ExpenseTransactionModel).filter(
            ExpenseTransactionModel.id == expense_transaction_id,
            ExpenseTransactionModel.company_id == company_id
        ).first()
        
        if not transaction:
            return {
                "status": False,
                "message": "Expense transaction not found",
                "entries_reversed": 0
            }
        
        if not transaction.ledger_entry_ids:
            return {
                "status": False,
                "message": "No ledger entries to reverse",
                "entries_reversed": 0
            }
        
        # Get original ledger entries
        entry_ids = [int(id.strip()) for id in transaction.ledger_entry_ids.split(",")]
        entries = db.query(LedgerEntriesModel).filter(
            LedgerEntriesModel.id.in_(entry_ids)
        ).all()
        
        entries_reversed = 0
        
        # Create reversing entries
        for entry in entries:
            reversing_entry = LedgerEntriesModel(
                company_id=company_id,
                account_id=entry.account_id,
                transaction_date=datetime.now(),
                transaction_type="EXPENSE_REVERSAL",
                reference_type="EXPENSE_TRANSACTION",
                reference_id=transaction.id,
                reference_no=f"REV-{entry.reference_no}",
                description=f"Reversal: {entry.description}",
                debit_amount=entry.credit_amount,  # Swap debit/credit
                credit_amount=entry.debit_amount,
                created_by=entry.created_by
            )
            db.add(reversing_entry)
            entries_reversed += 1
        
        # Update account balances
        debit_account = db.query(ExpenseLedgerAccount).filter(
            ExpenseLedgerAccount.id == transaction.debit_account_id
        ).first()
        
        credit_account = db.query(ExpenseLedgerAccount).filter(
            ExpenseLedgerAccount.id == transaction.credit_account_id
        ).first()
        
        if debit_account:
            debit_account.current_balance -= transaction.amount
        
        if credit_account:
            credit_account.current_balance += transaction.amount
        
        # Mark transaction as reversed
        transaction.status = "REVERSED"
        transaction.is_active = False
        
        db.commit()
        
        return {
            "status": True,
            "message": "Ledger entries reversed successfully",
            "entries_reversed": entries_reversed
        }
    
    except Exception as e:
        db.rollback()
        return {
            "status": False,
            "message": f"Error reversing ledger entries: {str(e)}",
            "entries_reversed": 0
        }


def generate_expense_category_code(db: Session, company_id: int) -> str:
    """
    Generate unique expense category code.
    Format: EXP-CAT-XXX
    Example: EXP-CAT-001
    """
    from app.models import ExpenseCategory
    
    # Find the last category code for this company
    last_category = (
        db.query(ExpenseCategory)
        .filter(
            ExpenseCategory.company_id == company_id,
            ExpenseCategory.category_code.like("EXP-CAT-%")
        )
        .order_by(ExpenseCategory.id.desc())
        .first()
    )
    
    if last_category:
        # Extract the sequence number and increment
        last_sequence = int(last_category.category_code.split("-")[-1])
        new_sequence = last_sequence + 1
    else:
        new_sequence = 1
    
    return f"EXP-CAT-{new_sequence:03d}"


def generate_expense_ledger_account_code(db: Session, company_id: int) -> str:
    """
    Generate unique expense ledger account code.
    Format: EXP-LEDGER-XXXX
    Example: EXP-LEDGER-0001
    """
    # Find the last account code for this company
    last_account = (
        db.query(ExpenseLedgerAccount)
        .filter(
            ExpenseLedgerAccount.company_id == company_id,
            ExpenseLedgerAccount.account_code.like("EXP-LEDGER-%")
        )
        .order_by(ExpenseLedgerAccount.id.desc())
        .first()
    )
    
    if last_account:
        # Extract the sequence number and increment
        last_sequence = int(last_account.account_code.split("-")[-1])
        new_sequence = last_sequence + 1
    else:
        new_sequence = 1
    
    return f"EXP-LEDGER-{new_sequence:04d}"
