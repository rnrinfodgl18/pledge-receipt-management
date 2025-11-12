"""Chart of Accounts routes for managing pawn shop accounts."""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import ChartOfAccounts as ChartOfAccountsModel, Company as CompanyModel
from app import schemas
from app.auth import get_current_user
from app.accounting_utils import create_default_coa, generate_account_code, get_default_category

coa_router = APIRouter(prefix="/chart-of-accounts", tags=["chart_of_accounts"])

# Separate routers for each account type
assets_router = APIRouter(prefix="/assets", tags=["COA - Assets"])
liabilities_router = APIRouter(prefix="/liabilities", tags=["COA - Liabilities"])
equity_router = APIRouter(prefix="/equity", tags=["COA - Equity/Capital"])
income_router = APIRouter(prefix="/income", tags=["COA - Income"])
expenses_router = APIRouter(prefix="/expenses-coa", tags=["COA - Expenses"])


# ========== HELPER FUNCTIONS ==========

def validate_company(db: Session, company_id: int):
    """Validate that company exists."""
    company = db.query(CompanyModel).filter(CompanyModel.id == company_id).first()
    if not company:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Company not found"
        )
    return company


def validate_account_code_unique(db: Session, account_code: str, company_id: int, exclude_id: int = None):
    """Validate that account code is unique for company."""
    query = db.query(ChartOfAccountsModel).filter(
        ChartOfAccountsModel.account_code == account_code,
        ChartOfAccountsModel.company_id == company_id
    )
    if exclude_id:
        query = query.filter(ChartOfAccountsModel.id != exclude_id)
    
    if query.first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Account code already exists for this company"
        )


def create_account_by_type(
    db: Session,
    account_data: schemas.ChartOfAccountsCreate,
    account_type: str,
    current_user
) -> ChartOfAccountsModel:
    """Generic function to create account of specific type."""
    # Validate company
    validate_company(db, account_data.company_id)
    
    # Validate account code uniqueness
    validate_account_code_unique(db, account_data.account_code, account_data.company_id)
    
    # Validate account type matches
    if account_data.account_type != account_type:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Account type must be '{account_type}' for this endpoint"
        )
    
    # Create account
    db_account = ChartOfAccountsModel(**account_data.dict())
    db.add(db_account)
    db.commit()
    db.refresh(db_account)
    return db_account


def get_accounts_by_type(
    db: Session,
    company_id: int,
    account_type: str,
    category: Optional[str] = None,
    is_active: Optional[bool] = None,
    limit: int = 100,
    offset: int = 0
) -> List[ChartOfAccountsModel]:
    """Generic function to get accounts by type."""
    validate_company(db, company_id)
    
    query = db.query(ChartOfAccountsModel).filter(
        ChartOfAccountsModel.company_id == company_id,
        ChartOfAccountsModel.account_type == account_type
    )
    
    if category:
        query = query.filter(ChartOfAccountsModel.account_category == category)
    if is_active is not None:
        query = query.filter(ChartOfAccountsModel.status == is_active)
    
    return query.order_by(ChartOfAccountsModel.account_code).limit(limit).offset(offset).all()


# ========== GENERAL COA ENDPOINTS ==========

@coa_router.post("/initialize-default/{company_id}", operation_id="initialize_default_coa_general")
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
    account_type: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """List all accounts for a company with optional type filter. (Requires authentication)"""
    # Check if company exists
    company = db.query(CompanyModel).filter(CompanyModel.id == company_id).first()
    if not company:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Company not found"
        )
    
    query = db.query(ChartOfAccountsModel).filter(
        ChartOfAccountsModel.company_id == company_id
    )
    
    if account_type:
        query = query.filter(ChartOfAccountsModel.account_type == account_type)
    
    accounts = query.offset(skip).limit(limit).all()
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


# ========== ASSETS ENDPOINTS ==========

@assets_router.post("/", response_model=schemas.ChartOfAccounts, status_code=status.HTTP_201_CREATED)
def create_asset_account(
    account: schemas.AssetAccountCreate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Create a new asset account.
    
    Examples: Cash, Bank, Accounts Receivable, Inventory, Gold Stock, etc.
    
    Only provide:
    - company_id (required)
    - account_name (required)
    - sub_account_of (optional)
    - opening_balance (optional, default=0.0)
    - description (optional)
    
    System automatically sets:
    - account_type = "Assets"
    - account_category = "Current Assets"
    - account_code = auto-generated (1XXX series)
    - status = true
    """
    # Validate company
    validate_company(db, account.company_id)
    
    # Validate sub_account_of if provided
    if account.sub_account_of:
        parent_account = db.query(ChartOfAccountsModel).filter(
            ChartOfAccountsModel.id == account.sub_account_of,
            ChartOfAccountsModel.company_id == account.company_id
        ).first()
        if not parent_account:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Parent account not found or does not belong to this company"
            )
    
    # Auto-generate account code
    account_code = generate_account_code(db, account.company_id, "Assets")
    
    # Auto-set account type and category
    account_type = "Assets"
    account_category = get_default_category(account_type)
    
    # Create account
    db_account = ChartOfAccountsModel(
        company_id=account.company_id,
        account_code=account_code,
        account_name=account.account_name,
        account_type=account_type,
        account_category=account_category,
        sub_account_of=account.sub_account_of,
        opening_balance=account.opening_balance,
        description=account.description,
        status=True
    )
    
    db.add(db_account)
    db.commit()
    db.refresh(db_account)
    return db_account


@assets_router.get("/{company_id}", response_model=List[schemas.ChartOfAccounts])
def get_asset_accounts(
    company_id: int,
    category: Optional[str] = Query(None, description="Filter by category (Cash, Bank, Inventory, etc.)"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    limit: int = Query(100, le=1000),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Get all asset accounts for a company.
    
    Common categories: Cash, Bank, Accounts Receivable, Inventory, Gold Stock, etc.
    """
    return get_accounts_by_type(db, company_id, "Assets", category, is_active, limit, offset)


@assets_router.get("/detail/{account_id}", response_model=schemas.ChartOfAccounts)
def get_asset_account_detail(
    account_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Get specific asset account details."""
    account = db.query(ChartOfAccountsModel).filter(
        ChartOfAccountsModel.id == account_id,
        ChartOfAccountsModel.account_type == "Assets"
    ).first()
    
    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Asset account not found"
        )
    return account


@assets_router.put("/{account_id}", response_model=schemas.ChartOfAccounts)
def update_asset_account(
    account_id: int,
    account: schemas.ChartOfAccountsUpdate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Update an asset account."""
    db_account = db.query(ChartOfAccountsModel).filter(
        ChartOfAccountsModel.id == account_id,
        ChartOfAccountsModel.account_type == "Assets"
    ).first()
    
    if not db_account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Asset account not found"
        )
    
    # Validate account code uniqueness if being updated
    if account.account_code and account.account_code != db_account.account_code:
        validate_account_code_unique(db, account.account_code, db_account.company_id, account_id)
    
    update_data = account.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_account, field, value)
    
    db.commit()
    db.refresh(db_account)
    return db_account


@assets_router.delete("/{account_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_asset_account(
    account_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Delete an asset account."""
    account = db.query(ChartOfAccountsModel).filter(
        ChartOfAccountsModel.id == account_id,
        ChartOfAccountsModel.account_type == "Assets"
    ).first()
    
    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Asset account not found"
        )
    
    db.delete(account)
    db.commit()
    return None


# ========== LIABILITIES ENDPOINTS ==========

@liabilities_router.post("/", response_model=schemas.ChartOfAccounts, status_code=status.HTTP_201_CREATED)
def create_liability_account(
    account: schemas.LiabilityAccountCreate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Create a new liability account.
    
    Examples: Accounts Payable, Bank Loan, Customer Deposits, etc.
    
    Only provide:
    - company_id, account_name, sub_account_of (optional), opening_balance (optional), description (optional)
    
    System auto-sets: account_type="Liabilities", account_category, account_code (2XXX series)
    """
    validate_company(db, account.company_id)
    
    if account.sub_account_of:
        parent_account = db.query(ChartOfAccountsModel).filter(
            ChartOfAccountsModel.id == account.sub_account_of,
            ChartOfAccountsModel.company_id == account.company_id
        ).first()
        if not parent_account:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Parent account not found"
            )
    
    account_code = generate_account_code(db, account.company_id, "Liabilities")
    account_type = "Liabilities"
    account_category = get_default_category(account_type)
    
    db_account = ChartOfAccountsModel(
        company_id=account.company_id,
        account_code=account_code,
        account_name=account.account_name,
        account_type=account_type,
        account_category=account_category,
        sub_account_of=account.sub_account_of,
        opening_balance=account.opening_balance,
        description=account.description,
        status=True
    )
    
    db.add(db_account)
    db.commit()
    db.refresh(db_account)
    return db_account


@liabilities_router.get("/{company_id}", response_model=List[schemas.ChartOfAccounts])
def get_liability_accounts(
    company_id: int,
    category: Optional[str] = Query(None, description="Filter by category"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    limit: int = Query(100, le=1000),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Get all liability accounts for a company."""
    return get_accounts_by_type(db, company_id, "Liabilities", category, is_active, limit, offset)


@liabilities_router.get("/detail/{account_id}", response_model=schemas.ChartOfAccounts)
def get_liability_account_detail(
    account_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Get specific liability account details."""
    account = db.query(ChartOfAccountsModel).filter(
        ChartOfAccountsModel.id == account_id,
        ChartOfAccountsModel.account_type == "Liabilities"
    ).first()
    
    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Liability account not found"
        )
    return account


@liabilities_router.put("/{account_id}", response_model=schemas.ChartOfAccounts)
def update_liability_account(
    account_id: int,
    account: schemas.ChartOfAccountsUpdate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Update a liability account."""
    db_account = db.query(ChartOfAccountsModel).filter(
        ChartOfAccountsModel.id == account_id,
        ChartOfAccountsModel.account_type == "Liabilities"
    ).first()
    
    if not db_account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Liability account not found"
        )
    
    if account.account_code and account.account_code != db_account.account_code:
        validate_account_code_unique(db, account.account_code, db_account.company_id, account_id)
    
    update_data = account.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_account, field, value)
    
    db.commit()
    db.refresh(db_account)
    return db_account


@liabilities_router.delete("/{account_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_liability_account(
    account_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Delete a liability account."""
    account = db.query(ChartOfAccountsModel).filter(
        ChartOfAccountsModel.id == account_id,
        ChartOfAccountsModel.account_type == "Liabilities"
    ).first()
    
    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Liability account not found"
        )
    
    db.delete(account)
    db.commit()
    return None


# ========== EQUITY/CAPITAL ENDPOINTS ==========

@equity_router.post("/", response_model=schemas.ChartOfAccounts, status_code=status.HTTP_201_CREATED)
def create_equity_account(
    account: schemas.EquityAccountCreate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Create a new equity/capital account.
    
    Examples: Owner's Capital, Retained Earnings, Drawings, etc.
    
    Only provide: company_id, account_name, sub_account_of (optional), opening_balance (optional), description (optional)
    System auto-sets: account_type="Equity", account_category, account_code (3XXX series)
    """
    validate_company(db, account.company_id)
    
    if account.sub_account_of:
        parent_account = db.query(ChartOfAccountsModel).filter(
            ChartOfAccountsModel.id == account.sub_account_of,
            ChartOfAccountsModel.company_id == account.company_id
        ).first()
        if not parent_account:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Parent account not found"
            )
    
    account_code = generate_account_code(db, account.company_id, "Equity")
    account_type = "Equity"
    account_category = get_default_category(account_type)
    
    db_account = ChartOfAccountsModel(
        company_id=account.company_id,
        account_code=account_code,
        account_name=account.account_name,
        account_type=account_type,
        account_category=account_category,
        sub_account_of=account.sub_account_of,
        opening_balance=account.opening_balance,
        description=account.description,
        status=True
    )
    
    db.add(db_account)
    db.commit()
    db.refresh(db_account)
    return db_account


@equity_router.get("/{company_id}", response_model=List[schemas.ChartOfAccounts])
def get_equity_accounts(
    company_id: int,
    category: Optional[str] = Query(None, description="Filter by category"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    limit: int = Query(100, le=1000),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Get all equity/capital accounts for a company."""
    return get_accounts_by_type(db, company_id, "Equity", category, is_active, limit, offset)


@equity_router.get("/detail/{account_id}", response_model=schemas.ChartOfAccounts)
def get_equity_account_detail(
    account_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Get specific equity/capital account details."""
    account = db.query(ChartOfAccountsModel).filter(
        ChartOfAccountsModel.id == account_id,
        ChartOfAccountsModel.account_type == "Equity"
    ).first()
    
    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Equity account not found"
        )
    return account


@equity_router.put("/{account_id}", response_model=schemas.ChartOfAccounts)
def update_equity_account(
    account_id: int,
    account: schemas.ChartOfAccountsUpdate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Update an equity/capital account."""
    db_account = db.query(ChartOfAccountsModel).filter(
        ChartOfAccountsModel.id == account_id,
        ChartOfAccountsModel.account_type == "Equity"
    ).first()
    
    if not db_account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Equity account not found"
        )
    
    if account.account_code and account.account_code != db_account.account_code:
        validate_account_code_unique(db, account.account_code, db_account.company_id, account_id)
    
    update_data = account.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_account, field, value)
    
    db.commit()
    db.refresh(db_account)
    return db_account


@equity_router.delete("/{account_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_equity_account(
    account_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Delete an equity/capital account."""
    account = db.query(ChartOfAccountsModel).filter(
        ChartOfAccountsModel.id == account_id,
        ChartOfAccountsModel.account_type == "Equity"
    ).first()
    
    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Equity account not found"
        )
    
    db.delete(account)
    db.commit()
    return None


# ========== INCOME ENDPOINTS ==========

@income_router.post("/", response_model=schemas.ChartOfAccounts, status_code=status.HTTP_201_CREATED)
def create_income_account(
    account: schemas.IncomeAccountCreate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Create a new income/revenue account.
    
    Examples: Interest Income, Service Charges, Sales Revenue, etc.
    
    Only provide: company_id, account_name, sub_account_of (optional), opening_balance (optional), description (optional)
    System auto-sets: account_type="Income", account_category, account_code (4XXX series)
    """
    validate_company(db, account.company_id)
    
    if account.sub_account_of:
        parent_account = db.query(ChartOfAccountsModel).filter(
            ChartOfAccountsModel.id == account.sub_account_of,
            ChartOfAccountsModel.company_id == account.company_id
        ).first()
        if not parent_account:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Parent account not found"
            )
    
    account_code = generate_account_code(db, account.company_id, "Income")
    account_type = "Income"
    account_category = get_default_category(account_type)
    
    db_account = ChartOfAccountsModel(
        company_id=account.company_id,
        account_code=account_code,
        account_name=account.account_name,
        account_type=account_type,
        account_category=account_category,
        sub_account_of=account.sub_account_of,
        opening_balance=account.opening_balance,
        description=account.description,
        status=True
    )
    
    db.add(db_account)
    db.commit()
    db.refresh(db_account)
    return db_account


@income_router.get("/{company_id}", response_model=List[schemas.ChartOfAccounts])
def get_income_accounts(
    company_id: int,
    category: Optional[str] = Query(None, description="Filter by category"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    limit: int = Query(100, le=1000),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Get all income/revenue accounts for a company."""
    return get_accounts_by_type(db, company_id, "Income", category, is_active, limit, offset)


@income_router.get("/detail/{account_id}", response_model=schemas.ChartOfAccounts)
def get_income_account_detail(
    account_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Get specific income account details."""
    account = db.query(ChartOfAccountsModel).filter(
        ChartOfAccountsModel.id == account_id,
        ChartOfAccountsModel.account_type == "Income"
    ).first()
    
    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Income account not found"
        )
    return account


@income_router.put("/{account_id}", response_model=schemas.ChartOfAccounts)
def update_income_account(
    account_id: int,
    account: schemas.ChartOfAccountsUpdate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Update an income/revenue account."""
    db_account = db.query(ChartOfAccountsModel).filter(
        ChartOfAccountsModel.id == account_id,
        ChartOfAccountsModel.account_type == "Income"
    ).first()
    
    if not db_account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Income account not found"
        )
    
    if account.account_code and account.account_code != db_account.account_code:
        validate_account_code_unique(db, account.account_code, db_account.company_id, account_id)
    
    update_data = account.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_account, field, value)
    
    db.commit()
    db.refresh(db_account)
    return db_account


@income_router.delete("/{account_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_income_account(
    account_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Delete an income/revenue account."""
    account = db.query(ChartOfAccountsModel).filter(
        ChartOfAccountsModel.id == account_id,
        ChartOfAccountsModel.account_type == "Income"
    ).first()
    
    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Income account not found"
        )
    
    db.delete(account)
    db.commit()
    return None


# ========== EXPENSES COA ENDPOINTS ==========

@expenses_router.post("/", response_model=schemas.ChartOfAccounts, status_code=status.HTTP_201_CREATED)
def create_expense_coa_account(
    account: schemas.ExpenseAccountCreate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Create a new expense account in Chart of Accounts.
    
    Examples: Rent Expense, Salary Expense, Utilities, Office Supplies, etc.
    
    Only provide: company_id, account_name, sub_account_of (optional), opening_balance (optional), description (optional)
    System auto-sets: account_type="Expenses", account_category, account_code (5XXX series)
    
    Note: This is different from /expenses/* endpoints which are for expense transactions.
    This endpoint creates the account definition in COA.
    """
    validate_company(db, account.company_id)
    
    if account.sub_account_of:
        parent_account = db.query(ChartOfAccountsModel).filter(
            ChartOfAccountsModel.id == account.sub_account_of,
            ChartOfAccountsModel.company_id == account.company_id
        ).first()
        if not parent_account:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Parent account not found"
            )
    
    account_code = generate_account_code(db, account.company_id, "Expenses")
    account_type = "Expenses"
    account_category = get_default_category(account_type)
    
    db_account = ChartOfAccountsModel(
        company_id=account.company_id,
        account_code=account_code,
        account_name=account.account_name,
        account_type=account_type,
        account_category=account_category,
        sub_account_of=account.sub_account_of,
        opening_balance=account.opening_balance,
        description=account.description,
        status=True
    )
    
    db.add(db_account)
    db.commit()
    db.refresh(db_account)
    return db_account


@expenses_router.get("/{company_id}", response_model=List[schemas.ChartOfAccounts])
def get_expense_coa_accounts(
    company_id: int,
    category: Optional[str] = Query(None, description="Filter by category"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    limit: int = Query(100, le=1000),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Get all expense accounts from Chart of Accounts for a company."""
    return get_accounts_by_type(db, company_id, "Expenses", category, is_active, limit, offset)


@expenses_router.get("/detail/{account_id}", response_model=schemas.ChartOfAccounts)
def get_expense_coa_account_detail(
    account_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Get specific expense account details from COA."""
    account = db.query(ChartOfAccountsModel).filter(
        ChartOfAccountsModel.id == account_id,
        ChartOfAccountsModel.account_type == "Expenses"
    ).first()
    
    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Expense account not found"
        )
    return account


@expenses_router.put("/{account_id}", response_model=schemas.ChartOfAccounts)
def update_expense_coa_account(
    account_id: int,
    account: schemas.ChartOfAccountsUpdate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Update an expense account in COA."""
    db_account = db.query(ChartOfAccountsModel).filter(
        ChartOfAccountsModel.id == account_id,
        ChartOfAccountsModel.account_type == "Expenses"
    ).first()
    
    if not db_account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Expense account not found"
        )
    
    if account.account_code and account.account_code != db_account.account_code:
        validate_account_code_unique(db, account.account_code, db_account.company_id, account_id)
    
    update_data = account.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_account, field, value)
    
    db.commit()
    db.refresh(db_account)
    return db_account


@expenses_router.delete("/{account_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_expense_coa_account(
    account_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Delete an expense account from COA."""
    account = db.query(ChartOfAccountsModel).filter(
        ChartOfAccountsModel.id == account_id,
        ChartOfAccountsModel.account_type == "Expenses"
    ).first()
    
    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Expense account not found"
        )
    
    db.delete(account)
    db.commit()
    return None
