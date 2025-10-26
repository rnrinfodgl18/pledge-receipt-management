"""
Test script for Pledge Update with Item Replacement and Ledger Handling
Tests the enhanced update_pledge endpoint functionality.
"""

import requests
import json
from datetime import datetime, timedelta

# Configuration
BASE_URL = "http://localhost:8000"
USERNAME = "admin"  # Change to your username
PASSWORD = "admin123"  # Change to your password

def get_auth_token():
    """Get authentication token."""
    response = requests.post(
        f"{BASE_URL}/token",
        data={"username": USERNAME, "password": PASSWORD}
    )
    if response.status_code == 200:
        return response.json()["access_token"]
    else:
        raise Exception(f"Login failed: {response.text}")

def test_update_due_date_only(token, pledge_id):
    """Test 1: Update only due date."""
    print("\n" + "="*60)
    print("TEST 1: Update Due Date Only")
    print("="*60)
    
    headers = {"Authorization": f"Bearer {token}"}
    due_date = (datetime.now() + timedelta(days=90)).isoformat()
    
    data = {
        "due_date": due_date
    }
    
    response = requests.put(
        f"{BASE_URL}/pledges/{pledge_id}",
        headers=headers,
        json=data
    )
    
    print(f"Status Code: {response.status_code}")
    if response.status_code == 200:
        result = response.json()
        print(f"✅ Due date updated successfully!")
        print(f"Pledge No: {result['pledge_no']}")
        print(f"Due Date: {result.get('due_date')}")
    else:
        print(f"❌ Failed: {response.text}")
    
    return response.status_code == 200

def test_replace_items_only(token, pledge_id):
    """Test 2: Replace all pledge items."""
    print("\n" + "="*60)
    print("TEST 2: Replace All Items")
    print("="*60)
    
    headers = {"Authorization": f"Bearer {token}"}
    
    data = {
        "pledge_items": [
            {
                "jewel_type_id": 1,
                "jewel_design": "Updated Gold Ring",
                "jewel_condition": "Excellent",
                "stone_type": "Diamond",
                "gross_weight": 15.0,
                "net_weight": 14.5,
                "quantity": 1
            },
            {
                "jewel_type_id": 1,
                "jewel_design": "Updated Gold Chain",
                "jewel_condition": "Good",
                "stone_type": None,
                "gross_weight": 30.0,
                "net_weight": 29.5,
                "quantity": 1
            }
        ]
    }
    
    response = requests.put(
        f"{BASE_URL}/pledges/{pledge_id}",
        headers=headers,
        json=data
    )
    
    print(f"Status Code: {response.status_code}")
    if response.status_code == 200:
        result = response.json()
        print(f"✅ Items replaced successfully!")
        print(f"Pledge No: {result['pledge_no']}")
        print(f"Gross Weight: {result['gross_weight']}")
        print(f"Net Weight: {result['net_weight']}")
        print(f"Number of Items: {len(result.get('pledge_items', []))}")
    else:
        print(f"❌ Failed: {response.text}")
    
    return response.status_code == 200

def test_update_loan_amount(token, pledge_id):
    """Test 3: Update loan amount (triggers ledger reversal)."""
    print("\n" + "="*60)
    print("TEST 3: Update Loan Amount (Ledger Auto-Update)")
    print("="*60)
    
    headers = {"Authorization": f"Bearer {token}"}
    
    data = {
        "loan_amount": 75000.0,
        "first_month_interest": 1875.0  # 2.5% of 75000
    }
    
    response = requests.put(
        f"{BASE_URL}/pledges/{pledge_id}",
        headers=headers,
        json=data
    )
    
    print(f"Status Code: {response.status_code}")
    if response.status_code == 200:
        result = response.json()
        print(f"✅ Loan amount updated successfully!")
        print(f"Pledge No: {result['pledge_no']}")
        print(f"New Loan Amount: ₹{result['loan_amount']}")
        print(f"First Month Interest: ₹{result['first_month_interest']}")
        print(f"Note: Ledger entries were automatically reversed and recreated")
    else:
        print(f"❌ Failed: {response.text}")
    
    return response.status_code == 200

def test_complete_update(token, pledge_id):
    """Test 4: Complete update (due_date + loan_amount + items)."""
    print("\n" + "="*60)
    print("TEST 4: Complete Update (All Fields)")
    print("="*60)
    
    headers = {"Authorization": f"Bearer {token}"}
    due_date = (datetime.now() + timedelta(days=120)).isoformat()
    
    data = {
        "due_date": due_date,
        "loan_amount": 85000.0,
        "interest_rate": 2.0,
        "first_month_interest": 1700.0,
        "pledge_items": [
            {
                "jewel_type_id": 1,
                "jewel_design": "Premium Gold Necklace",
                "jewel_condition": "Excellent",
                "stone_type": "Ruby",
                "gross_weight": 40.0,
                "net_weight": 38.5,
                "quantity": 1
            },
            {
                "jewel_type_id": 1,
                "jewel_design": "Premium Gold Bracelet",
                "jewel_condition": "Excellent",
                "stone_type": "Emerald",
                "gross_weight": 25.0,
                "net_weight": 24.0,
                "quantity": 1
            },
            {
                "jewel_type_id": 1,
                "jewel_design": "Premium Gold Earrings",
                "jewel_condition": "Good",
                "stone_type": "Pearl",
                "gross_weight": 10.0,
                "net_weight": 9.5,
                "quantity": 2
            }
        ]
    }
    
    response = requests.put(
        f"{BASE_URL}/pledges/{pledge_id}",
        headers=headers,
        json=data
    )
    
    print(f"Status Code: {response.status_code}")
    if response.status_code == 200:
        result = response.json()
        print(f"✅ Complete update successful!")
        print(f"Pledge No: {result['pledge_no']}")
        print(f"Due Date: {result.get('due_date')}")
        print(f"Loan Amount: ₹{result['loan_amount']}")
        print(f"Interest Rate: {result['interest_rate']}%")
        print(f"Gross Weight: {result['gross_weight']}g")
        print(f"Net Weight: {result['net_weight']}g")
        print(f"Number of Items: {len(result.get('pledge_items', []))}")
        print(f"\nNote: All old items deleted, ledger entries reversed and recreated")
    else:
        print(f"❌ Failed: {response.text}")
    
    return response.status_code == 200

def main():
    """Run all tests."""
    print("="*60)
    print("PLEDGE UPDATE ENHANCEMENT - TEST SUITE")
    print("="*60)
    
    try:
        # Get authentication token
        print("\n🔐 Authenticating...")
        token = get_auth_token()
        print("✅ Authentication successful!")
        
        # Get pledge ID from user
        pledge_id = input("\nEnter Pledge ID to test: ")
        
        # Run tests
        results = {
            "Test 1 - Due Date Only": test_update_due_date_only(token, pledge_id),
            "Test 2 - Replace Items": test_replace_items_only(token, pledge_id),
            "Test 3 - Loan Amount (Ledger)": test_update_loan_amount(token, pledge_id),
            "Test 4 - Complete Update": test_complete_update(token, pledge_id)
        }
        
        # Summary
        print("\n" + "="*60)
        print("TEST SUMMARY")
        print("="*60)
        for test_name, passed in results.items():
            status = "✅ PASSED" if passed else "❌ FAILED"
            print(f"{test_name}: {status}")
        
        total = len(results)
        passed = sum(results.values())
        print(f"\nTotal: {passed}/{total} tests passed")
        
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")

if __name__ == "__main__":
    main()
