"""Script to verify and create database tables."""
import os
import sys
from sqlalchemy import inspect, text
from dotenv import load_dotenv

# Add app to path
sys.path.insert(0, os.path.dirname(__file__))

load_dotenv()

from app.database import engine, Base
from app.models import (
    Company, User, JewelType, JewelRate, BankDetails, Scheme,
    CustomerDetails, ChartOfAccounts, LedgerEntries, Pledge, PledgeItems,
    PledgeReceipt, ReceiptItem, BankPledge, BankPledgeItems, BankRedemption
)

def check_and_create_tables():
    """Check if tables exist, create if not."""
    print("=" * 80)
    print("DATABASE TABLE VERIFICATION & CREATION")
    print("=" * 80)
    
    try:
        # Get inspector to check existing tables
        inspector = inspect(engine)
        existing_tables = inspector.get_table_names()
        
        print("\n[OK] Database connection successful!")
        print("\n[EXISTING TABLES]:")
        for table in existing_tables:
            print(f"   * {table}")
        
        # Expected tables
        expected_tables = [
            "companies", "users", "jewel_types", "jewel_rates", "bank_details",
            "schemes", "customer_details", "chart_of_accounts", "ledger_entries",
            "pledges", "pledge_items", "pledge_receipts", "receipt_items",
            "bank_pledges", "bank_pledge_items", "bank_redemptions"
        ]
        
        missing_tables = [t for t in expected_tables if t not in existing_tables]
        
        if missing_tables:
            print(f"\n[MISSING TABLES] ({len(missing_tables)}):")
            for table in missing_tables:
                print(f"   * {table}")
            
            print(f"\n[CREATING MISSING TABLES...]")
            Base.metadata.create_all(bind=engine)
            
            # Verify again
            inspector = inspect(engine)
            existing_tables = inspector.get_table_names()
            
            print(f"\n[OK] Tables created successfully!")
            print(f"[INFO] Total tables now: {len(existing_tables)}")
        else:
            print(f"\n[OK] All {len(expected_tables)} expected tables exist!")
        
        # Show table structure for bank_pledges
        print(f"\n[TABLE STRUCTURE] bank_pledges:")
        if "bank_pledges" in existing_tables:
            columns = inspector.get_columns("bank_pledges")
            for col in columns:
                nullable = "NULL" if col["nullable"] else "NOT NULL"
                print(f"   * {col['name']}: {col['type']} ({nullable})")
        
        # Show table structure for bank_redemptions
        print(f"\n[TABLE STRUCTURE] bank_redemptions:")
        if "bank_redemptions" in existing_tables:
            columns = inspector.get_columns("bank_redemptions")
            for col in columns:
                nullable = "NULL" if col["nullable"] else "NOT NULL"
                print(f"   * {col['name']}: {col['type']} ({nullable})")
        
        print("\n" + "=" * 80)
        print("[SUCCESS] DATABASE SETUP COMPLETE!")
        print("=" * 80)
        return True
        
    except Exception as e:
        print(f"\n[ERROR] {str(e)}")
        print("\n" + "=" * 80)
        return False

if __name__ == "__main__":
    success = check_and_create_tables()
    sys.exit(0 if success else 1)
