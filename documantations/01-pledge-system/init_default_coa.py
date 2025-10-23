#!/usr/bin/env python
"""
Script to initialize default Chart of Accounts for a company.

Usage:
    python init_default_coa.py <company_id>

Example:
    python init_default_coa.py 1
"""

import sys
import os
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from app.database import SessionLocal
from app.accounting_utils import create_default_coa
from app.models import Company as CompanyModel


def main():
    """Initialize default COA for a company."""
    if len(sys.argv) < 2:
        print("❌ Error: Company ID required")
        print("Usage: python init_default_coa.py <company_id>")
        print("Example: python init_default_coa.py 1")
        sys.exit(1)
    
    try:
        company_id = int(sys.argv[1])
    except ValueError:
        print(f"❌ Error: Invalid company ID '{sys.argv[1]}'. Must be an integer.")
        sys.exit(1)
    
    # Get database session
    db = SessionLocal()
    
    try:
        # Check if company exists
        company = db.query(CompanyModel).filter(CompanyModel.id == company_id).first()
        if not company:
            print(f"❌ Error: Company with ID {company_id} not found")
            sys.exit(1)
        
        print(f"\n{'='*60}")
        print(f"📊 Initializing Default Chart of Accounts")
        print(f"{'='*60}")
        print(f"Company: {company.company_name} (ID: {company_id})")
        print(f"License No: {company.licence_no}")
        print(f"{'='*60}\n")
        
        # Create default accounts
        success = create_default_coa(db, company_id)
        
        if success:
            print(f"\n{'='*60}")
            print(f"✅ SUCCESS: Default Chart of Accounts created!")
            print(f"{'='*60}")
            print(f"✓ 20 default accounts created")
            print(f"✓ Account codes: 1000-5050")
            print(f"\nAccount Categories:")
            print(f"  • Assets (1000-1050)")
            print(f"  • Liabilities (2000-2010)")
            print(f"  • Equity (3000-3010)")
            print(f"  • Income (4000-4040)")
            print(f"  • Expenses (5000-5050)")
            print(f"{'='*60}\n")
            sys.exit(0)
        else:
            print(f"\n{'='*60}")
            print(f"❌ ERROR: Failed to create default accounts")
            print(f"   (Accounts may already exist for this company)")
            print(f"{'='*60}\n")
            sys.exit(1)
    
    except Exception as e:
        print(f"\n{'='*60}")
        print(f"❌ ERROR: {str(e)}")
        print(f"{'='*60}\n")
        sys.exit(1)
    
    finally:
        db.close()


if __name__ == "__main__":
    main()
