# How to Create Default Chart of Accounts

There are **3 ways** to create default chart of accounts for your pawn shop:

---

## **Method 1: API Endpoint (Recommended)**

### Step 1: Get Authentication Token
```bash
curl -X POST "http://localhost:8000/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "admin",
    "password": "your_password"
  }'
```

**Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "user": {
    "id": 1,
    "username": "admin",
    "role": "admin"
  }
}
```

### Step 2: Initialize Default COA
```bash
curl -X POST "http://localhost:8000/chart-of-accounts/initialize-default/1" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

**Response:**
```json
{
  "status": "success",
  "message": "✅ Default Chart of Accounts created for company ABC Jewelry",
  "company_id": 1,
  "accounts_created": 20
}
```

---

## **Method 2: Command Line Script** ⭐ **Easiest**

### Step 1: Make script executable (Linux/Mac)
```bash
chmod +x init_default_coa.py
```

### Step 2: Run the script
```bash
python init_default_coa.py 1
```

**Output:**
```
============================================================
📊 Initializing Default Chart of Accounts
============================================================
Company: ABC Jewelry (ID: 1)
License No: LIC123456
============================================================

✅ SUCCESS: Default Chart of Accounts created!
============================================================
✓ 20 default accounts created
✓ Account codes: 1000-5050

Account Categories:
  • Assets (1000-1050)
  • Liabilities (2000-2010)
  • Equity (3000-3010)
  • Income (4000-4040)
  • Expenses (5000-5050)
============================================================
```

### Usage Examples:
```bash
# For company ID 1
python init_default_coa.py 1

# For company ID 2
python init_default_coa.py 2

# For company ID 5
python init_default_coa.py 5
```

---

## **Method 3: Python Script (Programmatic)**

### Create a script like this:
```python
from app.database import SessionLocal
from app.accounting_utils import create_default_coa
from app.models import Company

db = SessionLocal()

try:
    company_id = 1
    success = create_default_coa(db, company_id)
    
    if success:
        print("✅ Default COA created successfully!")
    else:
        print("❌ Failed to create default COA")
finally:
    db.close()
```

---

## **Default Accounts Created (20 Total)**

### **Assets (1000-1050)**
| Code | Account Name | Category |
|------|--------------|----------|
| 1000 | Cash | Cash |
| 1010 | Bank Account | Bank |
| 1020 | Gold Stock | Inventory |
| 1030 | Silver Stock | Inventory |
| 1040 | Pledged Items | Inventory |
| 1050 | Customer Advances | Receivables |

### **Liabilities (2000-2010)**
| Code | Account Name | Category |
|------|--------------|----------|
| 2000 | Accounts Payable | Payables |
| 2010 | Customer Deposits | Deposits |

### **Equity (3000-3010)**
| Code | Account Name | Category |
|------|--------------|----------|
| 3000 | Capital | Capital |
| 3010 | Retained Earnings | Earnings |

### **Income (4000-4040)**
| Code | Account Name | Category |
|------|--------------|----------|
| 4000 | Pledge Interest Income | Interest |
| 4010 | Gold Sales | Sales |
| 4020 | Silver Sales | Sales |
| 4030 | Service Charges | Service |
| 4040 | Jewelry Redemption | Income |

### **Expenses (5000-5050)**
| Code | Account Name | Category |
|------|--------------|----------|
| 5000 | Rent Expense | Rent |
| 5010 | Salary Expense | Salaries |
| 5020 | Utilities Expense | Utilities |
| 5030 | Repairs & Maintenance | Maintenance |
| 5040 | Insurance Expense | Insurance |
| 5050 | Administrative Expense | Admin |

---

## **Verification**

### Check if COA was created successfully:
```bash
# Get all accounts for company 1
curl -X GET "http://localhost:8000/chart-of-accounts/1" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

**Response:**
```json
[
  {
    "id": 1,
    "company_id": 1,
    "account_code": "1000",
    "account_name": "Cash",
    "account_type": "Assets",
    "account_category": "Cash",
    "opening_balance": 0.0,
    "description": "Cash on hand",
    "status": true,
    "created_at": "2025-10-23T14:30:00"
  },
  {
    "id": 2,
    "company_id": 1,
    "account_code": "1010",
    "account_name": "Bank Account",
    "account_type": "Assets",
    "account_category": "Bank",
    "opening_balance": 0.0,
    "description": "Business bank account",
    "status": true,
    "created_at": "2025-10-23T14:30:00"
  },
  // ... more accounts
]
```

---

## **Troubleshooting**

### Error: "Accounts already exist for this company"
**Solution:** Default accounts can only be created once per company. If you need to reset:
```bash
# Delete existing accounts manually
# Or use the database to delete and retry
```

### Error: "Company not found"
**Solution:** Make sure the company ID exists
```bash
# List all companies
curl -X GET "http://localhost:8000/companies/" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

### Error: "Invalid company ID"
**Solution:** Company ID must be a number
```bash
# ✓ Correct
python init_default_coa.py 1

# ✗ Wrong
python init_default_coa.py abc
```

---

## **Best Practices**

1. ✅ Create default COA immediately after creating a company
2. ✅ Use the command-line script for automation
3. ✅ Store the output for documentation
4. ✅ Don't delete accounts manually - use the API
5. ✅ One COA per company for better organization

---

## **Next Steps**

After creating default COA:

1. **Add Bank Accounts** - Auto-creates Bank COA accounts
2. **Add Customers** - Auto-creates Customer Receivable accounts
3. **Record Transactions** - Use Ledger Entries API
4. **View Reports** - Generate Trial Balance and Account Balance reports

---

## **Quick Start Commands**

```bash
# 1. Start server
source .venv/bin/activate
uvicorn app.main:app --reload

# 2. Login (in another terminal)
curl -X POST "http://localhost:8000/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "password"}'

# 3. Initialize COA for company 1
python init_default_coa.py 1

# 4. Verify
curl -X GET "http://localhost:8000/chart-of-accounts/1" \
  -H "Authorization: Bearer TOKEN"
```

---

**Done!** 🎉 Your Chart of Accounts is ready to use!
