"""Utility functions for setting up default chart of accounts."""
from sqlalchemy.orm import Session
from app.models import ChartOfAccounts as ChartOfAccountsModel


# Default Chart of Accounts for Pawn Shop
DEFAULT_ACCOUNTS = [
    # Assets
    {
        "account_code": "1000",
        "account_name": "Cash",
        "account_type": "Assets",
        "account_category": "Cash",
        "opening_balance": 0.0,
        "description": "Cash on hand"
    },
    {
        "account_code": "1010",
        "account_name": "Bank Account",
        "account_type": "Assets",
        "account_category": "Bank",
        "opening_balance": 0.0,
        "description": "Business bank account"
    },
    {
        "account_code": "1020",
        "account_name": "Gold Stock",
        "account_type": "Assets",
        "account_category": "Inventory",
        "opening_balance": 0.0,
        "description": "Gold jewelry and bullion inventory"
    },
    {
        "account_code": "1030",
        "account_name": "Silver Stock",
        "account_type": "Assets",
        "account_category": "Inventory",
        "opening_balance": 0.0,
        "description": "Silver jewelry inventory"
    },
    {
        "account_code": "1040",
        "account_name": "Pledged Items",
        "account_type": "Assets",
        "account_category": "Inventory",
        "opening_balance": 0.0,
        "description": "Inventory of pledged jewelry"
    },
    {
        "account_code": "1050",
        "account_name": "Customer Advances",
        "account_type": "Assets",
        "account_category": "Receivables",
        "opening_balance": 0.0,
        "description": "Advances given to customers"
    },
    # Liabilities
    {
        "account_code": "2000",
        "account_name": "Accounts Payable",
        "account_type": "Liabilities",
        "account_category": "Payables",
        "opening_balance": 0.0,
        "description": "Amount payable to suppliers"
    },
    {
        "account_code": "2010",
        "account_name": "Customer Deposits",
        "account_type": "Liabilities",
        "account_category": "Deposits",
        "opening_balance": 0.0,
        "description": "Deposits held for customers"
    },
    # Equity
    {
        "account_code": "3000",
        "account_name": "Capital",
        "account_type": "Equity",
        "account_category": "Capital",
        "opening_balance": 0.0,
        "description": "Owner's capital"
    },
    {
        "account_code": "3010",
        "account_name": "Retained Earnings",
        "account_type": "Equity",
        "account_category": "Earnings",
        "opening_balance": 0.0,
        "description": "Retained earnings from previous years"
    },
    # Income
    {
        "account_code": "4000",
        "account_name": "Pledge Interest Income",
        "account_type": "Income",
        "account_category": "Interest Income",
        "opening_balance": 0.0,
        "description": "Interest earned from pledges"
    },
    {
        "account_code": "4010",
        "account_name": "Gold Sales",
        "account_type": "Income",
        "account_category": "Sales",
        "opening_balance": 0.0,
        "description": "Revenue from gold sales"
    },
    {
        "account_code": "4020",
        "account_name": "Silver Sales",
        "account_type": "Income",
        "account_category": "Sales",
        "opening_balance": 0.0,
        "description": "Revenue from silver sales"
    },
    {
        "account_code": "4030",
        "account_name": "Service Charges",
        "account_type": "Income",
        "account_category": "Service Income",
        "opening_balance": 0.0,
        "description": "Service charges collected"
    },
    {
        "account_code": "4040",
        "account_name": "Jewelry Redemption",
        "account_type": "Income",
        "account_category": "Income",
        "opening_balance": 0.0,
        "description": "Income from jewelry redemption fees"
    },
    # Expenses
    {
        "account_code": "5000",
        "account_name": "Rent Expense",
        "account_type": "Expenses",
        "account_category": "Rent",
        "opening_balance": 0.0,
        "description": "Shop rent expense"
    },
    {
        "account_code": "5010",
        "account_name": "Salary Expense",
        "account_type": "Expenses",
        "account_category": "Salaries",
        "opening_balance": 0.0,
        "description": "Employee salaries"
    },
    {
        "account_code": "5020",
        "account_name": "Utilities Expense",
        "account_type": "Expenses",
        "account_category": "Utilities",
        "opening_balance": 0.0,
        "description": "Electricity, water, internet"
    },
    {
        "account_code": "5030",
        "account_name": "Repairs & Maintenance",
        "account_type": "Expenses",
        "account_category": "Maintenance",
        "opening_balance": 0.0,
        "description": "Shop repairs and maintenance"
    },
    {
        "account_code": "5040",
        "account_name": "Insurance Expense",
        "account_type": "Expenses",
        "account_category": "Insurance",
        "opening_balance": 0.0,
        "description": "Insurance premiums"
    },
    {
        "account_code": "5050",
        "account_name": "Administrative Expense",
        "account_type": "Expenses",
        "account_category": "Admin",
        "opening_balance": 0.0,
        "description": "Office and administrative expenses"
    },
]


def create_default_coa(db: Session, company_id: int) -> bool:
    """
    Create default chart of accounts for a new company.
    
    Args:
        db: Database session
        company_id: Company ID
    
    Returns:
        True if successful, False otherwise
    """
    try:
        # Check if accounts already exist for this company
        existing = db.query(ChartOfAccountsModel).filter(
            ChartOfAccountsModel.company_id == company_id
        ).first()
        
        if existing:
            print(f"Accounts already exist for company {company_id}")
            return False
        
        # Create default accounts
        for account in DEFAULT_ACCOUNTS:
            db_account = ChartOfAccountsModel(
                company_id=company_id,
                account_code=account["account_code"],
                account_name=account["account_name"],
                account_type=account["account_type"],
                account_category=account["account_category"],
                opening_balance=account["opening_balance"],
                description=account["description"],
                status=True
            )
            db.add(db_account)
        
        db.commit()
        print(f"✅ Default chart of accounts created for company {company_id}")
        return True
    
    except Exception as e:
        db.rollback()
        print(f"❌ Error creating default COA: {str(e)}")
        return False
