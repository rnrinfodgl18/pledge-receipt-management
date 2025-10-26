# Expense Management System - Complete Guide

## Overview
Complete expense management system with:
- **Expense Categories** - Classify expenses
- **Expense Ledger Accounts** - Separate debit/credit tracking
- **Expense Transactions** - Record all expenses with auto ledger integration
- **COA Integration** - Links to Chart of Accounts for double-entry bookkeeping

## Database Tables Created

### 1. expense_categories
Stores expense categories with default COA mappings.

**Columns:**
- `id` - Primary key
- `company_id` - Foreign key to companies
- `category_name` - Category name (e.g., "Office Supplies", "Rent", "Salary")
- `category_code` - Unique code (auto-generated: EXP-CAT-001)
- `description` - Optional description
- `default_debit_account_id` - Default COA debit account
- `default_credit_account_id` - Default COA credit account
- `is_active` - Active status
- `created_by`, `created_at`, `updated_at` - Audit fields

### 2. expense_ledger_accounts
Holds debit and credit accounts separately for expense tracking.

**Columns:**
- `id` - Primary key
- `company_id` - Foreign key to companies
- `account_name` - Account name
- `account_code` - Unique code (auto-generated: EXP-LEDGER-0001)
- `account_type` - DEBIT or CREDIT
- `coa_account_id` - Links to Chart of Accounts
- `expense_category_id` - Optional category link
- `opening_balance` - Opening balance
- `current_balance` - Auto-updated balance
- `description`, `is_active` - Additional fields
- `created_by`, `created_at`, `updated_at` - Audit fields

### 3. expense_transactions
Records all expense transactions with parallel ledger entries.

**Columns:**
- `id` - Primary key
- `company_id` - Foreign key to companies
- `transaction_no` - Auto-generated (EXP-202510-0001)
- `transaction_date` - Transaction date
- `expense_category_id` - Category
- `debit_account_id` - Expense ledger debit account
- `credit_account_id` - Expense ledger credit account
- `amount` - Transaction amount
- `description`, `reference_no` - Details
- `payment_mode` - CASH, BANK, UPI, CHEQUE
- `payment_reference` - Cheque no, UPI ref, etc.
- `payee_name`, `payee_contact` - Vendor details
- `attachment_path` - Document path
- `ledger_entry_created` - Auto ledger flag
- `ledger_entry_ids` - Comma-separated ledger IDs
- `status` - PENDING, APPROVED, REJECTED, POSTED, REVERSED
- `approved_by`, `approved_at`, `rejection_reason` - Approval workflow
- `remarks`, `is_active` - Additional fields
- `created_by`, `created_at`, `updated_at` - Audit fields

## API Endpoints

### Expense Categories

#### Create Category
```
POST /expenses/categories
```
**Request:**
```json
{
  "company_id": 1,
  "category_name": "Office Supplies",
  "category_code": "EXP-CAT-001",
  "description": "Office supplies and stationery",
  "default_debit_account_id": 10,
  "default_credit_account_id": 1
}
```

#### Get Categories
```
GET /expenses/categories/{company_id}?is_active=true
```

#### Update Category
```
PUT /expenses/categories/{category_id}
```

### Expense Ledger Accounts

#### Create Ledger Account
```
POST /expenses/ledger-accounts
```
**Request:**
```json
{
  "company_id": 1,
  "account_name": "Office Expense - Debit",
  "account_code": "EXP-LEDGER-0001",
  "account_type": "DEBIT",
  "coa_account_id": 10,
  "expense_category_id": 1,
  "opening_balance": 0.0,
  "description": "Tracks office expenses"
}
```

#### Get Ledger Accounts
```
GET /expenses/ledger-accounts/{company_id}
GET /expenses/ledger-accounts/{company_id}?account_type=DEBIT
GET /expenses/ledger-accounts/{company_id}?category_id=1
```

#### Get Account Details
```
GET /expenses/ledger-accounts/detail/{account_id}
```

#### Update Ledger Account
```
PUT /expenses/ledger-accounts/{account_id}
```

### Expense Transactions

#### Create Transaction
```
POST /expenses/transactions
```
**Request:**
```json
{
  "company_id": 1,
  "transaction_date": "2025-10-26T10:00:00",
  "expense_category_id": 1,
  "debit_account_id": 1,
  "credit_account_id": 2,
  "amount": 5000.00,
  "description": "Office supplies purchase",
  "reference_no": "INV-2025-001",
  "payment_mode": "CASH",
  "payment_reference": null,
  "payee_name": "ABC Stationery",
  "payee_contact": "9876543210",
  "remarks": "Monthly purchase"
}
```

**Response:**
```json
{
  "id": 1,
  "transaction_no": "EXP-202510-0001",
  "company_id": 1,
  "transaction_date": "2025-10-26T10:00:00",
  "amount": 5000.00,
  "status": "POSTED",
  "ledger_entry_created": true,
  "ledger_entry_ids": "100,101",
  ...
}
```

#### Get Transactions
```
GET /expenses/transactions/{company_id}
GET /expenses/transactions/{company_id}?category_id=1
GET /expenses/transactions/{company_id}?status_filter=POSTED
GET /expenses/transactions/{company_id}?from_date=2025-01-01&to_date=2025-12-31
GET /expenses/transactions/{company_id}?limit=50&offset=0
```

#### Get Transaction Details
```
GET /expenses/transactions/detail/{transaction_id}
```

#### Update Transaction
```
PUT /expenses/transactions/{transaction_id}
```
Note: Only PENDING transactions can be updated

#### Delete Transaction
```
DELETE /expenses/transactions/{transaction_id}
```
Automatically reverses ledger entries and updates account balances

#### Get Summary Report
```
GET /expenses/transactions/report/summary?company_id=1&from_date=2025-01-01&to_date=2025-12-31
```

**Response:**
```json
{
  "from_date": "2025-01-01",
  "to_date": "2025-12-31",
  "total_expense": 150000.00,
  "transaction_count": 25,
  "category_summary": [
    {
      "category_id": 1,
      "total_amount": 50000.00,
      "count": 10
    },
    {
      "category_id": 2,
      "total_amount": 100000.00,
      "count": 15
    }
  ]
}
```

## How It Works

### 1. Setup Process

**Step 1: Create Expense Categories**
```bash
POST /expenses/categories
{
  "company_id": 1,
  "category_name": "Rent",
  "description": "Office rent expense"
}
```

**Step 2: Create Debit Ledger Account**
```bash
POST /expenses/ledger-accounts
{
  "company_id": 1,
  "account_name": "Rent Expense - Debit",
  "account_type": "DEBIT",
  "coa_account_id": 15,  # Link to "Rent Expense" in COA
  "expense_category_id": 1
}
```

**Step 3: Create Credit Ledger Account**
```bash
POST /expenses/ledger-accounts
{
  "company_id": 1,
  "account_name": "Cash - Credit",
  "account_type": "CREDIT",
  "coa_account_id": 1,  # Link to "Cash" in COA
  "expense_category_id": 1
}
```

### 2. Recording Expense

When you create an expense transaction:

```bash
POST /expenses/transactions
{
  "company_id": 1,
  "transaction_date": "2025-10-26T10:00:00",
  "expense_category_id": 1,
  "debit_account_id": 1,  # Rent Expense - Debit
  "credit_account_id": 2,  # Cash - Credit
  "amount": 10000.00,
  "payment_mode": "CASH",
  "description": "October rent payment"
}
```

**Automatic Actions:**
1. Transaction created with auto-generated number: `EXP-202510-0001`
2. Two ledger entries created in COA:
   - Debit: Rent Expense (10,000)
   - Credit: Cash (10,000)
3. Expense ledger account balances updated:
   - Debit account balance +10,000
   - Credit account balance -10,000
4. Transaction status set to `POSTED`

### 3. Ledger Integration

Each expense transaction creates **parallel ledger entries** in the Chart of Accounts:

**Example:**
```
Expense Transaction: Office Supplies - ₹5,000

Ledger Entries Created:
-----------------------
Entry 1:
  Account: Office Supplies Expense (COA)
  Debit: ₹5,000
  Credit: ₹0
  
Entry 2:
  Account: Cash (COA)
  Debit: ₹0
  Credit: ₹5,000

Expense Ledger Updates:
----------------------
Debit Account (Office Expense):
  Current Balance: +₹5,000

Credit Account (Cash):
  Current Balance: -₹5,000
```

### 4. Balance Tracking

Expense ledger accounts maintain running balances:

- **Debit Accounts** (Expenses): Balance increases with each transaction
- **Credit Accounts** (Cash/Bank): Balance decreases with each payment

### 5. Deleting/Reversing Transactions

When you delete a transaction:

1. Original ledger entries are reversed
2. New reversing entries created in COA
3. Expense ledger balances updated (reversed)
4. Transaction marked as `REVERSED` and `is_active = False`

## Workflow Examples

### Example 1: Office Supplies Purchase

```bash
# 1. Create transaction
POST /expenses/transactions
{
  "company_id": 1,
  "transaction_date": "2025-10-26",
  "expense_category_id": 1,  # Office Supplies
  "debit_account_id": 1,     # Office Expense Debit
  "credit_account_id": 2,    # Cash Credit
  "amount": 5000.00,
  "payment_mode": "CASH",
  "payee_name": "ABC Stationery",
  "reference_no": "INV-001"
}

# Result:
# - Transaction No: EXP-202510-0001
# - Status: POSTED
# - 2 Ledger entries created
# - Balances updated
```

### Example 2: Salary Payment

```bash
# 1. Create salary category
POST /expenses/categories
{
  "company_id": 1,
  "category_name": "Salary",
  "description": "Employee salaries"
}

# 2. Create ledger accounts
POST /expenses/ledger-accounts
{
  "account_name": "Salary Expense - Debit",
  "account_type": "DEBIT",
  "coa_account_id": 20  # Salary Expense in COA
}

POST /expenses/ledger-accounts
{
  "account_name": "Bank - Credit",
  "account_type": "CREDIT",
  "coa_account_id": 2  # Bank Account in COA
}

# 3. Record salary payment
POST /expenses/transactions
{
  "expense_category_id": 2,  # Salary
  "debit_account_id": 3,     # Salary Expense
  "credit_account_id": 4,    # Bank Account
  "amount": 50000.00,
  "payment_mode": "BANK",
  "payment_reference": "TXN123456"
}
```

### Example 3: Monthly Report

```bash
# Get expense summary for October 2025
GET /expenses/transactions/report/summary?company_id=1&from_date=2025-10-01&to_date=2025-10-31

# Response:
{
  "total_expense": 75000.00,
  "transaction_count": 15,
  "category_summary": [
    {
      "category_id": 1,
      "total_amount": 25000.00,
      "count": 5
    },
    {
      "category_id": 2,
      "total_amount": 50000.00,
      "count": 10
    }
  ]
}
```

## Key Features

✅ **Automatic Code Generation**
- Category codes: EXP-CAT-001, EXP-CAT-002...
- Account codes: EXP-LEDGER-0001, EXP-LEDGER-0002...
- Transaction numbers: EXP-202510-0001, EXP-202510-0002...

✅ **COA Integration**
- Every expense transaction creates parallel ledger entries
- Double-entry bookkeeping maintained
- All balances reconcile with COA

✅ **Balance Tracking**
- Real-time balance updates on ledger accounts
- Opening balance + transactions = current balance
- Separate tracking for debit and credit accounts

✅ **Approval Workflow**
- Transactions can be PENDING, APPROVED, POSTED, REJECTED
- Currently auto-posts, but workflow ready for future

✅ **Ledger Reversal**
- Deleting transaction automatically reverses ledger entries
- Balances correctly adjusted
- Audit trail maintained

✅ **Reporting**
- Summary reports by date range
- Category-wise breakup
- Transaction listing with filters

## Payment Modes Supported

- **CASH** - Cash payments
- **BANK** - Bank transfers
- **UPI** - UPI payments
- **CHEQUE** - Cheque payments

## Status Flow

```
PENDING → POSTED → Active Transaction
        ↓
      REJECTED → Inactive
        
POSTED → DELETE → REVERSED → Inactive
```

## Integration with Existing System

### Links to Chart of Accounts
```
expense_ledger_accounts.coa_account_id → chart_of_accounts.id
```

### Links to Companies
```
expense_categories.company_id → companies.id
expense_ledger_accounts.company_id → companies.id
expense_transactions.company_id → companies.id
```

### Links to Users
```
expense_categories.created_by → users.id
expense_ledger_accounts.created_by → users.id
expense_transactions.created_by → users.id
expense_transactions.approved_by → users.id
```

## Next Steps

1. **Start Server:**
   ```bash
   uvicorn app.main:app --reload
   ```

2. **Access Swagger UI:**
   ```
   http://localhost:8000/docs
   ```

3. **Create Categories:**
   - Office Supplies
   - Rent
   - Salary
   - Utilities
   - etc.

4. **Create Ledger Accounts:**
   - One DEBIT account per expense type
   - One CREDIT account per payment source (Cash, Bank, etc.)

5. **Start Recording Transactions!**

## Tamil Translation (விளக்கம்)

### செலவு மேலாண்மை அமைப்பு

இந்த அமைப்பில் மூன்று முக்கிய பகுதிகள்:

1. **செலவு வகைகள் (Expense Categories)**
   - செலவுகளை வகைப்படுத்த (Office Supplies, Rent, etc.)
   - COA கணக்குகளோடு இணைப்பு

2. **செலவு லெட்ஜர் கணக்குகள் (Expense Ledger Accounts)**
   - டெபிட் மற்றும் கிரெடிட் கணக்குகள் தனித்தனியாக
   - COA இல் உள்ள கணக்குகளோடு இணைப்பு
   - தானாக இருப்பு புதுப்பிக்கப்படும்

3. **செலவு பரிவர்த்தனைகள் (Expense Transactions)**
   - ஒவ்வொரு செலவையும் பதிவு செய்ய
   - தானாக லெட்ஜர் என்ட்ரிகள் உருவாகும்
   - COA இல் இரட்டை என்ட்ரி கணக்கியல்

### எப்படி பயன்படுத்துவது:

1. செலவு வகையை உருவாக்கு (Category)
2. டெபிட் கணக்கு உருவாக்கு (Debit Account)
3. கிரெடிட் கணக்கு உருவாக்கு (Credit Account)
4. செலவு பரிவர்த்தனை பதிவு செய்
5. தானாக COA இல் லெட்ஜர் என்ட்ரிகள் உருவாகும்!

**உதாரணம்:**
- Office Supplies க்கு ₹5,000 செலவு
- டெபிட்: Office Supplies Expense (COA)
- கிரெடிட்: Cash (COA)
- இருப்பு தானாக புதுப்பிக்கப்படும்
