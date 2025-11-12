"""Migration script to create api_configurations table."""
import sys
import os
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.database import engine, Base
from app.models import ApiConfiguration


def create_api_configurations_table():
    """Create api_configurations table."""
    try:
        print("🔧 Creating api_configurations table...")
        
        # Create only the api_configurations table
        ApiConfiguration.__table__.create(bind=engine, checkfirst=True)
        
        print("✅ api_configurations table created successfully!")
        print("\nTable Details:")
        print("  • Table name: api_configurations")
        print("  • Purpose: Store external API configurations for data fetch")
        print("  • Features:")
        print("    - Store base URL and authentication details")
        print("    - Support multiple auth types (API_KEY, BEARER_TOKEN, BASIC_AUTH, etc.)")
        print("    - Custom headers support")
        print("    - Timeout and retry configuration")
        print("    - Connection testing capability")
        
        return True
    
    except Exception as e:
        print(f"❌ Error creating table: {e}")
        return False


def verify_table():
    """Verify that api_configurations table was created."""
    try:
        from sqlalchemy import inspect
        
        print("\n🔍 Verifying table...")
        inspector = inspect(engine)
        existing_tables = inspector.get_table_names()
        
        if "api_configurations" in existing_tables:
            print("  ✓ api_configurations - EXISTS")
            
            # Get column details
            columns = inspector.get_columns("api_configurations")
            print(f"\n  Columns ({len(columns)}):")
            for col in columns:
                print(f"    - {col['name']}: {col['type']}")
            
            print("\n✅ Table verified successfully!")
            return True
        else:
            print("  ✗ api_configurations - MISSING")
            print("\n⚠️  Table verification failed!")
            return False
    
    except Exception as e:
        print(f"❌ Error verifying table: {e}")
        return False


if __name__ == "__main__":
    print("=" * 70)
    print("API CONFIGURATIONS TABLE MIGRATION")
    print("=" * 70)
    print()
    
    success = create_api_configurations_table()
    
    if success:
        verify_table()
        print("\n" + "=" * 70)
        print("MIGRATION COMPLETED!")
        print("=" * 70)
        print("\nNext steps:")
        print("1. Start the FastAPI server: uvicorn app.main:app --reload")
        print("2. Access Swagger UI: http://localhost:8000/docs")
        print("3. Navigate to 'API Configurations' tag")
        print("4. Create your first API configuration:")
        print("   POST /api-configurations/")
        print("   {")
        print('     "company_id": 1,')
        print('     "api_name": "Old Data API",')
        print('     "api_type": "DATA_FETCH",')
        print('     "base_url": "https://api.olddata.com/v1",')
        print('     "api_key": "your-api-key",')
        print('     "auth_type": "API_KEY"')
        print("   }")
        print("\n5. Test connection: POST /api-configurations/{config_id}/test-connection")
    else:
        print("\n❌ MIGRATION FAILED!")
        sys.exit(1)
