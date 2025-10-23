"""
Database migration script to add phone column to companies table.
Run this script once to update existing database.
"""
import os
from sqlalchemy import text, create_engine
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise ValueError("DATABASE_URL environment variable is not set")

engine = create_engine(DATABASE_URL)

# SQL to add phone column if it doesn't exist
add_phone_column_sql = """
ALTER TABLE companies
ADD COLUMN IF NOT EXISTS phone VARCHAR NOT NULL DEFAULT '+1-000-0000';
"""

try:
    with engine.connect() as connection:
        connection.execute(text(add_phone_column_sql))
        connection.commit()
        print("✅ Successfully added phone column to companies table!")
except Exception as e:
    print(f"❌ Error: {e}")
    print("The phone column might already exist or there's a database connection issue.")
finally:
    engine.dispose()
