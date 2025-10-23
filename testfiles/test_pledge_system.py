"""
Test script for demonstrating Pledge System functionality.
Run this after starting the FastAPI server.

Usage:
    python testfiles/test_pledge_system.py
"""
import requests
import json
from datetime import datetime, timedelta

# Configuration
BASE_URL = "http://localhost:8000"
COMPANY_ID = 1
CUSTOMER_ID = 1
SCHEME_ID = 1
HEADERS = {
    "Content-Type": "application/json",
    "Authorization": "Bearer YOUR_JWT_TOKEN_HERE"  # Replace with actual token
}

def test_create_pledge():
    """Test creating a pledge with automatic ledger entries."""
    print("\n" + "="*60)
    print("TEST 1: Create New Pledge with Items")
    print("="*60)
    
    pledge_data = {
        "company_id": COMPANY_ID,
        "customer_id": CUSTOMER_ID,
        "scheme_id": SCHEME_ID,
        "pledge_date": datetime.now().strftime("%Y-%m-%d"),
        "gross_weight": 150.5,
        "net_weight": 145.2,
        "maximum_value": 75000,
        "loan_amount": 50000,
        "interest_rate": 2.5,
        "pledge_items": [
            {
                "jewel_type_id": 1,
                "jewel_design": "Gold Ring with Diamond",
                "jewel_condition": "Excellent",
                "stone_type": "Diamond",
                "gross_weight": 50.5,
                "net_weight": 48.2,
                "quantity": 1
            },
            {
                "jewel_type_id": 1,
                "jewel_design": "Gold Necklace",
                "jewel_condition": "Good",
                "stone_type": "Ruby",
                "gross_weight": 100,
                "net_weight": 97,
                "quantity": 1
            }
        ]
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/pledges/",
            json=pledge_data,
            headers=HEADERS
        )
        
        if response.status_code == 201:
            pledge = response.json()
            print(f"\n✅ SUCCESS - Pledge Created")
            print(f"   Pledge ID: {pledge['id']}")
            print(f"   Pledge No: {pledge['pledge_no']}")
            print(f"   Loan Amount: ₹{pledge['loan_amount']}")
            print(f"   Interest Rate: {pledge['interest_rate']}%")
            print(f"   First Month Interest: ₹{pledge['first_month_interest']}")
            print(f"   Status: {pledge['status']}")
            print(f"   Items: {len(pledge['pledge_items'])} items")
            print(f"\n   📊 Ledger entries auto-created:")
            print(f"      - Debit: Pledged Items (1040) = ₹{pledge['maximum_value']}")
            print(f"      - Credit: Customer Receivable = ₹{pledge['loan_amount']}")
            print(f"      - Debit: Cash = ₹{pledge['loan_amount']}")
            print(f"      - Credit: Interest Income = ₹{pledge['first_month_interest']}")
            
            return pledge['id']
        else:
            print(f"\n❌ FAILED - {response.status_code}")
            print(f"   Response: {response.text}")
            return None
    
    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")
        return None


def test_get_pledges():
    """Test retrieving pledges with filters."""
    print("\n" + "="*60)
    print("TEST 2: Get All Pledges (with filters)")
    print("="*60)
    
    try:
        response = requests.get(
            f"{BASE_URL}/pledges/{COMPANY_ID}?status_filter=Active",
            headers=HEADERS
        )
        
        if response.status_code == 200:
            pledges = response.json()
            print(f"\n✅ SUCCESS - Retrieved {len(pledges)} Active pledges")
            
            for idx, pledge in enumerate(pledges, 1):
                print(f"\n   Pledge {idx}:")
                print(f"      No: {pledge['pledge_no']}")
                print(f"      Customer ID: {pledge['customer_id']}")
                print(f"      Loan: ₹{pledge['loan_amount']}")
                print(f"      Status: {pledge['status']}")
                print(f"      Items: {len(pledge.get('pledge_items', []))} items")
            
            return pledges
        else:
            print(f"\n❌ FAILED - {response.status_code}")
            print(f"   Response: {response.text}")
            return []
    
    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")
        return []


def test_get_single_pledge(pledge_id: int):
    """Test retrieving a specific pledge."""
    print("\n" + "="*60)
    print(f"TEST 3: Get Specific Pledge (ID: {pledge_id})")
    print("="*60)
    
    try:
        response = requests.get(
            f"{BASE_URL}/pledges/{pledge_id}",
            headers=HEADERS
        )
        
        if response.status_code == 200:
            pledge = response.json()
            print(f"\n✅ SUCCESS - Pledge Retrieved")
            print(f"   Pledge No: {pledge['pledge_no']}")
            print(f"   Gross Weight: {pledge['gross_weight']}g")
            print(f"   Net Weight: {pledge['net_weight']}g")
            print(f"   Maximum Value: ₹{pledge['maximum_value']}")
            print(f"   Loan Amount: ₹{pledge['loan_amount']}")
            print(f"   Interest Rate: {pledge['interest_rate']}%")
            print(f"   First Month Interest: ₹{pledge['first_month_interest']}")
            print(f"\n   Items in Pledge:")
            
            for idx, item in enumerate(pledge['pledge_items'], 1):
                print(f"\n      Item {idx}:")
                print(f"         Design: {item['jewel_design']}")
                print(f"         Type: {item['jewel_type_id']}")
                print(f"         Condition: {item['jewel_condition']}")
                print(f"         Stone: {item['stone_type']}")
                print(f"         Weight: {item['gross_weight']}g (net: {item['net_weight']}g)")
                print(f"         Quantity: {item['quantity']}")
        else:
            print(f"\n❌ FAILED - {response.status_code}")
            print(f"   Response: {response.text}")
    
    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")


def test_upload_photo(pledge_id: int):
    """Test uploading pledge photo."""
    print("\n" + "="*60)
    print(f"TEST 4: Upload Pledge Photo (ID: {pledge_id})")
    print("="*60)
    
    # Create a simple test image file
    test_image_path = "testfiles/test_pledge_photo.jpg"
    
    try:
        # Check if test image exists, if not create a simple one
        import os
        if not os.path.exists(test_image_path):
            print(f"\n⚠️  Test image not found at {test_image_path}")
            print(f"   Skipping photo upload test")
            print(f"   To test, provide a JPG/PNG file at: {test_image_path}")
            return
        
        with open(test_image_path, "rb") as f:
            files = {"file": ("test_photo.jpg", f, "image/jpeg")}
            headers_no_content = {k: v for k, v in HEADERS.items() if k != "Content-Type"}
            
            response = requests.post(
                f"{BASE_URL}/pledges/{pledge_id}/upload-photo",
                files=files,
                headers=headers_no_content
            )
        
        if response.status_code == 200:
            result = response.json()
            print(f"\n✅ SUCCESS - Photo Uploaded")
            print(f"   Path: {result['photo_path']}")
            print(f"   Message: {result['message']}")
        else:
            print(f"\n❌ FAILED - {response.status_code}")
            print(f"   Response: {response.text}")
    
    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")


def test_get_pledge_items(pledge_id: int):
    """Test retrieving items from a pledge."""
    print("\n" + "="*60)
    print(f"TEST 5: Get Pledge Items (Pledge ID: {pledge_id})")
    print("="*60)
    
    try:
        response = requests.get(
            f"{BASE_URL}/pledges/{pledge_id}/items",
            headers=HEADERS
        )
        
        if response.status_code == 200:
            items = response.json()
            print(f"\n✅ SUCCESS - Retrieved {len(items)} items")
            
            for idx, item in enumerate(items, 1):
                print(f"\n   Item {idx}:")
                print(f"      Design: {item['jewel_design']}")
                print(f"      Condition: {item['jewel_condition']}")
                print(f"      Gross Weight: {item['gross_weight']}g")
                print(f"      Quantity: {item['quantity']}")
        else:
            print(f"\n❌ FAILED - {response.status_code}")
            print(f"   Response: {response.text}")
    
    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")


def test_update_pledge(pledge_id: int):
    """Test updating pledge details."""
    print("\n" + "="*60)
    print(f"TEST 6: Update Pledge (ID: {pledge_id})")
    print("="*60)
    
    update_data = {
        "interest_rate": 3.0  # Change interest rate
    }
    
    try:
        response = requests.put(
            f"{BASE_URL}/pledges/{pledge_id}",
            json=update_data,
            headers=HEADERS
        )
        
        if response.status_code == 200:
            pledge = response.json()
            print(f"\n✅ SUCCESS - Pledge Updated")
            print(f"   Pledge No: {pledge['pledge_no']}")
            print(f"   New Interest Rate: {pledge['interest_rate']}%")
        else:
            print(f"\n❌ FAILED - {response.status_code}")
            print(f"   Response: {response.text}")
    
    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")


def test_close_pledge(pledge_id: int):
    """Test closing/redeeming a pledge."""
    print("\n" + "="*60)
    print(f"TEST 7: Close Pledge (ID: {pledge_id})")
    print("="*60)
    
    close_data = {
        "new_status": "Redeemed",
        "notes": "Customer paid full amount and collected items"
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/pledges/{pledge_id}/close",
            json=close_data,
            headers=HEADERS
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"\n✅ SUCCESS - Pledge Redeemed")
            print(f"   Pledge No: {result['pledge_no']}")
            print(f"   New Status: {result['new_status']}")
            print(f"   Message: {result['message']}")
        else:
            print(f"\n❌ FAILED - {response.status_code}")
            print(f"   Response: {response.text}")
    
    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")


def test_delete_pledge(pledge_id: int):
    """Test deleting a pledge and reversing ledger entries."""
    print("\n" + "="*60)
    print(f"TEST 8: Delete Pledge (ID: {pledge_id})")
    print("="*60)
    
    try:
        response = requests.delete(
            f"{BASE_URL}/pledges/{pledge_id}",
            headers=HEADERS
        )
        
        if response.status_code == 204:
            print(f"\n✅ SUCCESS - Pledge Deleted")
            print(f"   Pledge ID: {pledge_id}")
            print(f"   All ledger entries reversed automatically")
        else:
            print(f"\n❌ FAILED - {response.status_code}")
            print(f"   Response: {response.text}")
    
    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")


def main():
    """Run all pledge system tests."""
    print("\n" + "█"*60)
    print("║" + " "*58 + "║")
    print("║" + "  PLEDGE SYSTEM - COMPREHENSIVE TEST SUITE  ".center(58) + "║")
    print("║" + " "*58 + "║")
    print("█"*60)
    
    print("\n📋 PREREQUISITES:")
    print("   1. FastAPI server running on http://localhost:8000")
    print("   2. Database initialized with default COA accounts")
    print("   3. Company exists with ID:", COMPANY_ID)
    print("   4. Customer exists with ID:", CUSTOMER_ID)
    print("   5. Scheme exists with ID:", SCHEME_ID)
    print("   6. JWT token available (set HEADERS['Authorization'])")
    
    print("\n🔑 IMPORTANT: Update HEADERS with your JWT token!")
    print("   Get token from: POST /login")
    
    input("\n⏳ Press Enter to start tests...")
    
    # Run tests
    pledge_id = test_create_pledge()
    
    if pledge_id:
        test_get_pledges()
        test_get_single_pledge(pledge_id)
        test_get_pledge_items(pledge_id)
        test_update_pledge(pledge_id)
        test_upload_photo(pledge_id)
        
        # Optional: Test closing
        # test_close_pledge(pledge_id)
        
        # Optional: Test deletion (only works for active pledges)
        # test_delete_pledge(pledge_id)
    
    print("\n" + "█"*60)
    print("║" + " "*58 + "║")
    print("║" + "  TEST SUITE COMPLETED  ".center(58) + "║")
    print("║" + " "*58 + "║")
    print("█"*60)
    
    print("\n📊 Next Steps:")
    print("   1. Check /docs for interactive API documentation")
    print("   2. View ledger entries created for the pledge")
    print("   3. Test trial balance report to verify entries")
    print("   4. Try other pledge statuses and transitions")
    print("   5. Create pledges for different customers and schemes")


if __name__ == "__main__":
    main()
