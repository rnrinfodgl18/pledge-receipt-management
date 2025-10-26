"""Migration script to create expense management tables."""
import sys
import os
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.database import engine, Base
from app.models import (
    ExpenseCategory,
    ExpenseLedgerAccount,
    ExpenseTransaction,
)


def create_expense_tables():
    """Create expense management tables."""
    try:
        print("🔧 Creating expense management tables...")
        
        # Create only the expense-related tables
        tables_to_create = [
            ExpenseCategory.__table__,
            ExpenseLedgerAccount.__table__,
            ExpenseTransaction.__table__,
        ]
        
        for table in tables_to_create:
            print(f"  ➤ Creating table: {table.name}")
            table.create(bind=engine, checkfirst=True)
        
        print("✅ Expense management tables created successfully!")
        print("\nCreated tables:")
        print("  • expense_categories - Stores expense categories")
        print("  • expense_ledger_accounts - Debit/credit accounts for expense tracking")
        print("  • expense_transactions - All expense transactions with ledger integration")
        
        return True
    
    except Exception as e:
        print(f"❌ Error creating expense tables: {e}")
        return False


def verify_tables():
    """Verify that expense tables were created."""
    try:
        from sqlalchemy import inspect
        
        print("\n🔍 Verifying tables...")
        inspector = inspect(engine)
        existing_tables = inspector.get_table_names()
        
        expected_tables = [
            "expense_categories",
            "expense_ledger_accounts",
            "expense_transactions",
        ]
        
        all_exist = True
        for table in expected_tables:
            if table in existing_tables:
                print(f"  ✓ {table} - EXISTS")
            else:
                print(f"  ✗ {table} - MISSING")
                all_exist = False
        
        if all_exist:
            print("\n✅ All expense tables verified!")
        else:
            print("\n⚠️  Some tables are missing!")
        
        return all_exist
    
    except Exception as e:
        print(f"❌ Error verifying tables: {e}")
        return False


if __name__ == "__main__":
    print("=" * 60)
    print("EXPENSE MANAGEMENT TABLES MIGRATION")
    print("=" * 60)
    print()
    
    success = create_expense_tables()
    
    if success:
        verify_tables()
        print("\n" + "=" * 60)
        print("MIGRATION COMPLETED!")
        print("=" * 60)
        print("\nNext steps:")
        print("1. Start the FastAPI server: uvicorn app.main:app --reload")
        print("2. Access Swagger UI: http://localhost:8000/docs")
        print("3. Create expense categories first")
        print("4. Create expense ledger accounts linked to COA")
        print("5. Start recording expense transactions")
    else:
        print("\n❌ MIGRATION FAILED!")
        sys.exit(1)
