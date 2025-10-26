"""
Migration Script: Add due_date column to pledges table
Run this script to add the due_date column to existing pledges table.

Usage:
    python db_migrations/add_due_date_column.py
"""

import sys
import os
from datetime import datetime

# Add parent directory to path to import app modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text
from app.database import SessionLocal, engine


def add_due_date_column():
    """Add due_date column to pledges table."""
    db = SessionLocal()
    
    try:
        print("=" * 60)
        print("Migration: Add due_date column to pledges table")
        print("=" * 60)
        
        # Check if column already exists
        check_query = text("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name='pledges' AND column_name='due_date'
        """)
        
        result = db.execute(check_query).fetchone()
        
        if result:
            print("[SKIP] Column 'due_date' already exists in pledges table")
            return
        
        # Add the due_date column
        print("[RUNNING] Adding due_date column...")
        alter_query = text("""
            ALTER TABLE pledges 
            ADD COLUMN due_date TIMESTAMP NULL
        """)
        
        db.execute(alter_query)
        db.commit()
        
        print("[OK] Successfully added due_date column to pledges table")
        
        # Create index on due_date for better query performance
        print("[RUNNING] Creating index on due_date column...")
        index_query = text("""
            CREATE INDEX IF NOT EXISTS idx_pledges_due_date 
            ON pledges(due_date)
        """)
        
        db.execute(index_query)
        db.commit()
        
        print("[OK] Successfully created index on due_date column")
        
        # Verify the column was added
        verify_query = text("""
            SELECT column_name, data_type, is_nullable
            FROM information_schema.columns 
            WHERE table_name='pledges' AND column_name='due_date'
        """)
        
        verification = db.execute(verify_query).fetchone()
        
        if verification:
            print("\n[VERIFICATION]")
            print(f"  Column Name: {verification[0]}")
            print(f"  Data Type: {verification[1]}")
            print(f"  Nullable: {verification[2]}")
            print("\n[SUCCESS] Migration completed successfully!")
        else:
            print("\n[ERROR] Could not verify column creation")
            
    except Exception as e:
        db.rollback()
        print(f"\n[ERROR] Migration failed: {str(e)}")
        raise
    
    finally:
        db.close()
        print("=" * 60)


if __name__ == "__main__":
    add_due_date_column()
