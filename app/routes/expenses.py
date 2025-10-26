"""API routes for expense management with ledger integration."""
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status, Query
from sqlalchemy.orm import Session
from datetime import datetime, date
from typing import List, Optional

from app.database import get_db
from app.models import (
    ExpenseCategory as ExpenseCategoryModel,
    ExpenseLedgerAccount as ExpenseLedgerAccountModel,
    ExpenseTransaction as ExpenseTransactionModel,
    ChartOfAccounts as ChartOfAccountsModel,
    User as UserModel,
)
from app.schemas import (
    ExpenseCategory,
    ExpenseCategoryCreate,
    ExpenseCategoryUpdate,
    ExpenseLedgerAccount,
    ExpenseLedgerAccountCreate,
    ExpenseLedgerAccountUpdate,
    ExpenseTransaction,
    ExpenseTransactionCreate,
    ExpenseTransactionUpdate,
    ExpenseTransactionApproval,
    ExpenseTransactionWithDetails,
)
from app.auth import get_current_user
from app.expense_utils import (
    generate_expense_transaction_no,
    generate_expense_category_code,
    generate_expense_ledger_account_code,
    create_expense_ledger_entries,
    reverse_expense_ledger_entries,
)

router = APIRouter(prefix="/expenses", tags=["expenses"])


# ========== EXPENSE CATEGORY ENDPOINTS ==========

@router.post("/categories", response_model=ExpenseCategory, status_code=status.HTTP_201_CREATED)
def create_expense_category(
    category_data: ExpenseCategoryCreate,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
):
    """
    Create a new expense category.
    
    - Automatically generates category_code if not provided
    - Links to default debit/credit COA accounts
    - Used for categorizing expenses
    """
    try:
        # Generate category code if not provided
        if not category_data.category_code or category_data.category_code.startswith("EXP-CAT-"):
            category_data.category_code = generate_expense_category_code(db, category_data.company_id)
        
        # Check if category name already exists
        existing = db.query(ExpenseCategoryModel).filter(
            ExpenseCategoryModel.company_id == category_data.company_id,
            ExpenseCategoryModel.category_name == category_data.category_name
        ).first()
        
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Category '{category_data.category_name}' already exists"
            )
        
        new_category = ExpenseCategoryModel(
            company_id=category_data.company_id,
            category_name=category_data.category_name,
            category_code=category_data.category_code,
            description=category_data.description,
            default_debit_account_id=category_data.default_debit_account_id,
            default_credit_account_id=category_data.default_credit_account_id,
            is_active=True,
            created_by=current_user.id
        )
        
        db.add(new_category)
        db.commit()
        db.refresh(new_category)
        
        return new_category
    
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error creating expense category: {str(e)}"
        )


@router.get("/categories/{company_id}", response_model=List[ExpenseCategory])
def get_expense_categories(
    company_id: int,
    is_active: Optional[bool] = None,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
):
    """Get all expense categories for a company."""
    query = db.query(ExpenseCategoryModel).filter(
        ExpenseCategoryModel.company_id == company_id
    )
    
    if is_active is not None:
        query = query.filter(ExpenseCategoryModel.is_active == is_active)
    
    categories = query.order_by(ExpenseCategoryModel.category_name).all()
    return categories


@router.put("/categories/{category_id}", response_model=ExpenseCategory)
def update_expense_category(
    category_id: int,
    category_data: ExpenseCategoryUpdate,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
):
    """Update expense category."""
    category = db.query(ExpenseCategoryModel).filter(
        ExpenseCategoryModel.id == category_id
    ).first()
    
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Expense category not found"
        )
    
    try:
        update_data = category_data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(category, key, value)
        
        db.commit()
        db.refresh(category)
        return category
    
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error updating category: {str(e)}"
        )


# ========== EXPENSE LEDGER ACCOUNT ENDPOINTS ==========

@router.post("/ledger-accounts", response_model=ExpenseLedgerAccount, status_code=status.HTTP_201_CREATED)
def create_expense_ledger_account(
    account_data: ExpenseLedgerAccountCreate,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
):
    """
    Create a new expense ledger account.
    
    - Automatically generates account_code
    - Links to COA account
    - Tracks debit/credit balances separately
    - Opening balance can be set during creation
    """
    try:
        # Validate account type
        if account_data.account_type not in ["DEBIT", "CREDIT"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="account_type must be DEBIT or CREDIT"
            )
        
        # Validate COA account exists
        coa_account = db.query(ChartOfAccountsModel).filter(
            ChartOfAccountsModel.id == account_data.coa_account_id,
            ChartOfAccountsModel.company_id == account_data.company_id
        ).first()
        
        if not coa_account:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="COA account not found"
            )
        
        # Generate account code if not provided
        if not account_data.account_code or account_data.account_code.startswith("EXP-LEDGER-"):
            account_data.account_code = generate_expense_ledger_account_code(db, account_data.company_id)
        
        new_account = ExpenseLedgerAccountModel(
            company_id=account_data.company_id,
            account_name=account_data.account_name,
            account_code=account_data.account_code,
            account_type=account_data.account_type,
            coa_account_id=account_data.coa_account_id,
            expense_category_id=account_data.expense_category_id,
            opening_balance=account_data.opening_balance,
            current_balance=account_data.opening_balance,  # Initialize with opening balance
            description=account_data.description,
            is_active=True,
            created_by=current_user.id
        )
        
        db.add(new_account)
        db.commit()
        db.refresh(new_account)
        
        return new_account
    
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error creating expense ledger account: {str(e)}"
        )


@router.get("/ledger-accounts/{company_id}", response_model=List[ExpenseLedgerAccount])
def get_expense_ledger_accounts(
    company_id: int,
    account_type: Optional[str] = None,
    category_id: Optional[int] = None,
    is_active: Optional[bool] = None,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
):
    """Get all expense ledger accounts with filters."""
    query = db.query(ExpenseLedgerAccountModel).filter(
        ExpenseLedgerAccountModel.company_id == company_id
    )
    
    if account_type:
        query = query.filter(ExpenseLedgerAccountModel.account_type == account_type)
    if category_id:
        query = query.filter(ExpenseLedgerAccountModel.expense_category_id == category_id)
    if is_active is not None:
        query = query.filter(ExpenseLedgerAccountModel.is_active == is_active)
    
    accounts = query.order_by(ExpenseLedgerAccountModel.account_name).all()
    return accounts


@router.get("/ledger-accounts/detail/{account_id}", response_model=ExpenseLedgerAccount)
def get_expense_ledger_account(
    account_id: int,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
):
    """Get specific expense ledger account."""
    account = db.query(ExpenseLedgerAccountModel).filter(
        ExpenseLedgerAccountModel.id == account_id
    ).first()
    
    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Expense ledger account not found"
        )
    
    return account


@router.put("/ledger-accounts/{account_id}", response_model=ExpenseLedgerAccount)
def update_expense_ledger_account(
    account_id: int,
    account_data: ExpenseLedgerAccountUpdate,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
):
    """Update expense ledger account."""
    account = db.query(ExpenseLedgerAccountModel).filter(
        ExpenseLedgerAccountModel.id == account_id
    ).first()
    
    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Expense ledger account not found"
        )
    
    try:
        update_data = account_data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(account, key, value)
        
        db.commit()
        db.refresh(account)
        return account
    
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error updating account: {str(e)}"
        )


# ========== EXPENSE TRANSACTION ENDPOINTS ==========

@router.post("/transactions", response_model=ExpenseTransaction, status_code=status.HTTP_201_CREATED)
def create_expense_transaction(
    transaction_data: ExpenseTransactionCreate,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
):
    """
    Create a new expense transaction.
    
    - Automatically generates transaction_no
    - Creates parallel ledger entries in COA
    - Updates expense ledger account balances
    - Status: PENDING (requires approval)
    """
    try:
        # Validate accounts exist
        debit_account = db.query(ExpenseLedgerAccountModel).filter(
            ExpenseLedgerAccountModel.id == transaction_data.debit_account_id,
            ExpenseLedgerAccountModel.company_id == transaction_data.company_id
        ).first()
        
        credit_account = db.query(ExpenseLedgerAccountModel).filter(
            ExpenseLedgerAccountModel.id == transaction_data.credit_account_id,
            ExpenseLedgerAccountModel.company_id == transaction_data.company_id
        ).first()
        
        if not debit_account:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Debit account not found"
            )
        
        if not credit_account:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Credit account not found"
            )
        
        # Validate account types
        if debit_account.account_type != "DEBIT":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Debit account must be of type DEBIT"
            )
        
        if credit_account.account_type != "CREDIT":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Credit account must be of type CREDIT"
            )
        
        # Generate transaction number
        transaction_no = generate_expense_transaction_no(db, transaction_data.company_id)
        
        # Create transaction
        new_transaction = ExpenseTransactionModel(
            company_id=transaction_data.company_id,
            transaction_no=transaction_no,
            transaction_date=transaction_data.transaction_date,
            expense_category_id=transaction_data.expense_category_id,
            debit_account_id=transaction_data.debit_account_id,
            credit_account_id=transaction_data.credit_account_id,
            amount=transaction_data.amount,
            description=transaction_data.description,
            reference_no=transaction_data.reference_no,
            payment_mode=transaction_data.payment_mode,
            payment_reference=transaction_data.payment_reference,
            payee_name=transaction_data.payee_name,
            payee_contact=transaction_data.payee_contact,
            remarks=transaction_data.remarks,
            status="PENDING",
            is_active=True,
            created_by=current_user.id
        )
        
        db.add(new_transaction)
        db.flush()  # Get the transaction ID
        
        # Create ledger entries
        ledger_result = create_expense_ledger_entries(
            db, new_transaction, transaction_data.company_id, current_user.id
        )
        
        if ledger_result["status"]:
            new_transaction.ledger_entry_created = True
            new_transaction.ledger_entry_ids = ledger_result["ledger_entry_ids"]
            new_transaction.status = "POSTED"  # Auto-approve for now
        else:
            print(f"⚠️ Warning: Transaction created but ledger entries failed: {ledger_result['message']}")
        
        db.commit()
        db.refresh(new_transaction)
        
        return new_transaction
    
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error creating expense transaction: {str(e)}"
        )


@router.get("/transactions/{company_id}", response_model=List[ExpenseTransaction])
def get_expense_transactions(
    company_id: int,
    category_id: Optional[int] = None,
    status_filter: Optional[str] = None,
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
    limit: int = 100,
    offset: int = 0,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
):
    """Get expense transactions with filters and pagination."""
    query = db.query(ExpenseTransactionModel).filter(
        ExpenseTransactionModel.company_id == company_id
    )
    
    if category_id:
        query = query.filter(ExpenseTransactionModel.expense_category_id == category_id)
    if status_filter:
        query = query.filter(ExpenseTransactionModel.status == status_filter)
    if from_date:
        query = query.filter(ExpenseTransactionModel.transaction_date >= from_date)
    if to_date:
        query = query.filter(ExpenseTransactionModel.transaction_date <= to_date)
    
    total = query.count()
    transactions = query.order_by(
        ExpenseTransactionModel.transaction_date.desc()
    ).limit(limit).offset(offset).all()
    
    return transactions


@router.get("/transactions/detail/{transaction_id}", response_model=ExpenseTransaction)
def get_expense_transaction(
    transaction_id: int,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
):
    """Get specific expense transaction."""
    transaction = db.query(ExpenseTransactionModel).filter(
        ExpenseTransactionModel.id == transaction_id
    ).first()
    
    if not transaction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Expense transaction not found"
        )
    
    return transaction


@router.put("/transactions/{transaction_id}", response_model=ExpenseTransaction)
def update_expense_transaction(
    transaction_id: int,
    transaction_data: ExpenseTransactionUpdate,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
):
    """Update expense transaction (only if PENDING status)."""
    transaction = db.query(ExpenseTransactionModel).filter(
        ExpenseTransactionModel.id == transaction_id
    ).first()
    
    if not transaction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Expense transaction not found"
        )
    
    if transaction.status != "PENDING":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot update transaction with status {transaction.status}"
        )
    
    try:
        update_data = transaction_data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(transaction, key, value)
        
        db.commit()
        db.refresh(transaction)
        return transaction
    
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error updating transaction: {str(e)}"
        )


@router.delete("/transactions/{transaction_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_expense_transaction(
    transaction_id: int,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
):
    """Delete expense transaction and reverse ledger entries."""
    transaction = db.query(ExpenseTransactionModel).filter(
        ExpenseTransactionModel.id == transaction_id
    ).first()
    
    if not transaction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Expense transaction not found"
        )
    
    try:
        # Reverse ledger entries if created
        if transaction.ledger_entry_created:
            reverse_result = reverse_expense_ledger_entries(
                db, transaction_id, transaction.company_id
            )
            
            if not reverse_result["status"]:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Failed to reverse ledger entries: {reverse_result['message']}"
                )
        
        db.delete(transaction)
        db.commit()
        
        return None
    
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error deleting transaction: {str(e)}"
        )


@router.get("/transactions/report/summary")
def get_expense_summary_report(
    company_id: int,
    from_date: date,
    to_date: date,
    category_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
):
    """Get expense summary report for date range."""
    query = db.query(ExpenseTransactionModel).filter(
        ExpenseTransactionModel.company_id == company_id,
        ExpenseTransactionModel.transaction_date >= from_date,
        ExpenseTransactionModel.transaction_date <= to_date,
        ExpenseTransactionModel.status == "POSTED"
    )
    
    if category_id:
        query = query.filter(ExpenseTransactionModel.expense_category_id == category_id)
    
    transactions = query.all()
    
    total_expense = sum(t.amount for t in transactions)
    transaction_count = len(transactions)
    
    # Group by category
    category_summary = {}
    for t in transactions:
        cat_id = t.expense_category_id
        if cat_id not in category_summary:
            category_summary[cat_id] = {
                "category_id": cat_id,
                "total_amount": 0,
                "count": 0
            }
        category_summary[cat_id]["total_amount"] += t.amount
        category_summary[cat_id]["count"] += 1
    
    return {
        "from_date": from_date.isoformat(),
        "to_date": to_date.isoformat(),
        "total_expense": total_expense,
        "transaction_count": transaction_count,
        "category_summary": list(category_summary.values())
    }
