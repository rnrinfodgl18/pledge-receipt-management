"""Add pledge close tracking columns to pledges table."""
import os
import sys
from pathlib import Path

# Add parent directory to path to import app modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import text
from app.database import engine

def add_pledge_close_columns():
    """Add pledge_close_date, total_principal_received, total_interest_received columns to pledges table."""
    
    try:
        with engine.connect() as conn:
            # Check if columns already exist
            check_query = text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'pledges' 
                AND column_name IN ('pledge_close_date', 'total_principal_received', 'total_interest_received')
            """)
            existing_columns = [row[0] for row in conn.execute(check_query)]
            
            if len(existing_columns) == 3:
                print("✅ All columns already exist in pledges table!")
                return True
            
            # Add pledge_close_date column
            if 'pledge_close_date' not in existing_columns:
                print("Adding pledge_close_date column...")
                conn.execute(text("""
                    ALTER TABLE pledges 
                    ADD COLUMN pledge_close_date TIMESTAMP NULL
                """))
                conn.commit()
                print("✅ pledge_close_date column added")
            else:
                print("✅ pledge_close_date column already exists")
            
            # Add total_principal_received column
            if 'total_principal_received' not in existing_columns:
                print("Adding total_principal_received column...")
                conn.execute(text("""
                    ALTER TABLE pledges 
                    ADD COLUMN total_principal_received DOUBLE PRECISION NULL DEFAULT 0.0
                """))
                conn.commit()
                print("✅ total_principal_received column added")
            else:
                print("✅ total_principal_received column already exists")
            
            # Add total_interest_received column
            if 'total_interest_received' not in existing_columns:
                print("Adding total_interest_received column...")
                conn.execute(text("""
                    ALTER TABLE pledges 
                    ADD COLUMN total_interest_received DOUBLE PRECISION NULL DEFAULT 0.0
                """))
                conn.commit()
                print("✅ total_interest_received column added")
            else:
                print("✅ total_interest_received column already exists")
            
            # Verify all columns exist
            verify_query = text("""
                SELECT column_name, data_type, is_nullable, column_default
                FROM information_schema.columns 
                WHERE table_name = 'pledges' 
                AND column_name IN ('pledge_close_date', 'total_principal_received', 'total_interest_received')
                ORDER BY column_name
            """)
            
            print("\n" + "="*70)
            print("Pledges table - New columns verification:")
            print("="*70)
            
            for row in conn.execute(verify_query):
                col_name, data_type, is_nullable, default_val = row
                nullable = "NULL" if is_nullable == "YES" else "NOT NULL"
                default = f"DEFAULT {default_val}" if default_val else ""
                print(f"  {col_name:30} {data_type:20} {nullable:10} {default}")
            
            print("\n✅ Migration completed successfully!")
            print("\nNew columns added:")
            print("  1. pledge_close_date - TIMESTAMP NULL")
            print("  2. total_principal_received - DOUBLE PRECISION NULL DEFAULT 0.0")
            print("  3. total_interest_received - DOUBLE PRECISION NULL DEFAULT 0.0")
            print("\nThese columns will be updated when:")
            print("  - Pledge is closed")
            print("  - Receipt entries are created")
            
            return True
            
    except Exception as e:
        print(f"\n❌ Error adding columns: {e}")
        return False


if __name__ == "__main__":
    print("Starting migration: Add pledge close tracking columns")
    print("="*70)
    success = add_pledge_close_columns()
    
    if success:
        print("\n" + "="*70)
        print("Migration completed successfully! ✅")
        print("="*70)
    else:
        print("\n" + "="*70)
        print("Migration failed! ❌")
        print("="*70)
        sys.exit(1)
