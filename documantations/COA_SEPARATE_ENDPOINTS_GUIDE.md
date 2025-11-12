# Chart of Accounts - Separate CRUD Endpoints Guide

## Overview
Created separate CRUD endpoints for each Chart of Accounts type:
- **Assets** - Cash, Bank, Inventory, Gold Stock, etc.
- **Liabilities** - Accounts Payable, Bank Loans, Customer Deposits, etc.
- **Equity/Capital** - Owner's Capital, Retained Earnings, Drawings, etc.
- **Income** - Interest Income, Service Charges, Sales Revenue, etc.
- **Expenses** - Rent, Salary, Utilities, Office Supplies, etc.

Each type has its own dedicated endpoints with proper validation.

## New API Endpoints

### 1. ASSETS Endpoints (`/assets/*`)

**Tag:** COA - Assets

#### Create Asset Account
```
POST /assets/
```
**Request:**
```json
{
  "company_id": 1,
  "account_code": "1100",
  "account_name": "Bank Account - HDFC",
  "account_type": "Assets",
  "account_category": "Bank",
  "opening_balance": 100000.00,
  "description": "HDFC Bank Current Account"
}
```

#### Get All Asset Accounts
```
GET /assets/{company_id}
GET /assets/{company_id}?category=Cash
GET /assets/{company_id}?is_active=true
GET /assets/{company_id}?limit=50&offset=0
```

#### Get Asset Account Detail
```
GET /assets/detail/{account_id}
```

#### Update Asset Account
```
PUT /assets/{account_id}
```

#### Delete Asset Account
```
DELETE /assets/{account_id}
```

---

### 2. LIABILITIES Endpoints (`/liabilities/*`)

**Tag:** COA - Liabilities

#### Create Liability Account
```
POST /liabilities/
```
**Request:**
```json
{
  "company_id": 1,
  "account_code": "2100",
  "account_name": "Bank Loan",
  "account_type": "Liabilities",
  "account_category": "Loan",
  "opening_balance": 500000.00,
  "description": "Business loan from HDFC"
}
```

#### Get All Liability Accounts
```
GET /liabilities/{company_id}
GET /liabilities/{company_id}?category=Loan
GET /liabilities/{company_id}?is_active=true
```

#### Get Liability Account Detail
```
GET /liabilities/detail/{account_id}
```

#### Update Liability Account
```
PUT /liabilities/{account_id}
```

#### Delete Liability Account
```
DELETE /liabilities/{account_id}
```

---

### 3. EQUITY/CAPITAL Endpoints (`/equity/*`)

**Tag:** COA - Equity/Capital

#### Create Equity Account
```
POST /equity/
```
**Request:**
```json
{
  "company_id": 1,
  "account_code": "3000",
  "account_name": "Owner's Capital",
  "account_type": "Equity",
  "account_category": "Capital",
  "opening_balance": 1000000.00,
  "description": "Owner's initial investment"
}
```

#### Get All Equity Accounts
```
GET /equity/{company_id}
GET /equity/{company_id}?category=Capital
```

#### Get Equity Account Detail
```
GET /equity/detail/{account_id}
```

#### Update Equity Account
```
PUT /equity/{account_id}
```

#### Delete Equity Account
```
DELETE /equity/{account_id}
```

---

### 4. INCOME Endpoints (`/income/*`)

**Tag:** COA - Income

#### Create Income Account
```
POST /income/
```
**Request:**
```json
{
  "company_id": 1,
  "account_code": "4100",
  "account_name": "Interest Income",
  "account_type": "Income",
  "account_category": "Interest",
  "opening_balance": 0.00,
  "description": "Interest earned on pledges"
}
```

#### Get All Income Accounts
```
GET /income/{company_id}
GET /income/{company_id}?category=Interest
GET /income/{company_id}?is_active=true
```

#### Get Income Account Detail
```
GET /income/detail/{account_id}
```

#### Update Income Account
```
PUT /income/{account_id}
```

#### Delete Income Account
```
DELETE /income/{account_id}
```

---

### 5. EXPENSES COA Endpoints (`/expenses-coa/*`)

**Tag:** COA - Expenses

**Note:** This is for Chart of Accounts expense account definitions. 
For expense transactions, use `/expenses/*` endpoints.

#### Create Expense Account
```
POST /expenses-coa/
```
**Request:**
```json
{
  "company_id": 1,
  "account_code": "5100",
  "account_name": "Rent Expense",
  "account_type": "Expenses",
  "account_category": "Rent",
  "opening_balance": 0.00,
  "description": "Monthly office rent"
}
```

#### Get All Expense Accounts
```
GET /expenses-coa/{company_id}
GET /expenses-coa/{company_id}?category=Rent
GET /expenses-coa/{company_id}?is_active=true
```

#### Get Expense Account Detail
```
GET /expenses-coa/detail/{account_id}
```

#### Update Expense Account
```
PUT /expenses-coa/{account_id}
```

#### Delete Expense Account
```
DELETE /expenses-coa/{account_id}
```

---

## Key Features

### ✅ Automatic Validation
- **Company Validation** - Ensures company exists
- **Account Code Uniqueness** - Prevents duplicate account codes per company
- **Account Type Enforcement** - Each endpoint only accepts its specific account type
  - `/assets/` only accepts `account_type: "Assets"`
  - `/liabilities/` only accepts `account_type: "Liabilities"`
  - `/equity/` only accepts `account_type: "Equity"`
  - `/income/` only accepts `account_type: "Income"`
  - `/expenses-coa/` only accepts `account_type: "Expenses"`

### ✅ Filtering Support
All GET endpoints support:
- `category` - Filter by account category
- `is_active` - Filter by active status
- `limit` - Pagination limit (max 1000)
- `offset` - Pagination offset

### ✅ Organized Swagger UI
Each account type has its own tag in Swagger:
- **COA - Assets**
- **COA - Liabilities**
- **COA - Equity/Capital**
- **COA - Income**
- **COA - Expenses**

This makes it easy to find and use the right endpoints.

---

## Usage Examples

### Example 1: Create Asset Accounts

```bash
# Create Cash Account
POST /assets/
{
  "company_id": 1,
  "account_code": "1000",
  "account_name": "Cash in Hand",
  "account_type": "Assets",
  "account_category": "Cash",
  "opening_balance": 50000.00
}

# Create Bank Account
POST /assets/
{
  "company_id": 1,
  "account_code": "1100",
  "account_name": "HDFC Bank",
  "account_type": "Assets",
  "account_category": "Bank",
  "opening_balance": 200000.00
}

# Create Gold Stock Account
POST /assets/
{
  "company_id": 1,
  "account_code": "1500",
  "account_name": "Gold Inventory",
  "account_type": "Assets",
  "account_category": "Inventory",
  "opening_balance": 500000.00
}
```

### Example 2: Get All Asset Accounts

```bash
# Get all assets
GET /assets/1

# Get only Cash accounts
GET /assets/1?category=Cash

# Get only active Bank accounts
GET /assets/1?category=Bank&is_active=true

# With pagination
GET /assets/1?limit=20&offset=0
```

### Example 3: Create Income Accounts

```bash
# Interest Income
POST /income/
{
  "company_id": 1,
  "account_code": "4100",
  "account_name": "Interest Income",
  "account_type": "Income",
  "account_category": "Interest"
}

# Service Charges
POST /income/
{
  "company_id": 1,
  "account_code": "4200",
  "account_name": "Service Charges",
  "account_type": "Income",
  "account_category": "Service"
}
```

### Example 4: Create Expense Accounts

```bash
# Rent Expense
POST /expenses-coa/
{
  "company_id": 1,
  "account_code": "5100",
  "account_name": "Rent Expense",
  "account_type": "Expenses",
  "account_category": "Rent"
}

# Salary Expense
POST /expenses-coa/
{
  "company_id": 1,
  "account_code": "5200",
  "account_name": "Salary Expense",
  "account_type": "Expenses",
  "account_category": "Salary"
}

# Office Supplies
POST /expenses-coa/
{
  "company_id": 1,
  "account_code": "5300",
  "account_name": "Office Supplies",
  "account_type": "Expenses",
  "account_category": "Supplies"
}
```

### Example 5: Update Account

```bash
# Update asset account opening balance
PUT /assets/10
{
  "opening_balance": 75000.00,
  "description": "Updated opening balance"
}

# Deactivate an account
PUT /income/5
{
  "status": false
}
```

### Example 6: Error Handling

```bash
# Wrong account type - Will fail with error
POST /assets/
{
  "account_code": "4100",
  "account_name": "Interest Income",
  "account_type": "Income"  # ❌ Wrong! Must be "Assets" for /assets/ endpoint
}

# Response:
{
  "detail": "Account type must be 'Assets' for this endpoint"
}

# Duplicate account code - Will fail
POST /assets/
{
  "account_code": "1000",  # Already exists
  "account_name": "Another Cash",
  "account_type": "Assets"
}

# Response:
{
  "detail": "Account code already exists for this company"
}
```

---

## Endpoint Comparison

### Old General Endpoint
```
POST /chart-of-accounts/
GET /chart-of-accounts/{company_id}
GET /chart-of-accounts/{company_id}/{account_id}
PUT /chart-of-accounts/{account_id}
DELETE /chart-of-accounts/{account_id}
```
**Still available for backward compatibility**

### New Type-Specific Endpoints
```
Assets:       POST /assets/  GET /assets/{company_id}  etc.
Liabilities:  POST /liabilities/  GET /liabilities/{company_id}  etc.
Equity:       POST /equity/  GET /equity/{company_id}  etc.
Income:       POST /income/  GET /income/{company_id}  etc.
Expenses:     POST /expenses-coa/  GET /expenses-coa/{company_id}  etc.
```
**Better organization, validation, and developer experience**

---

## Benefits

### 1. **Better Organization**
- Clear separation of account types
- Easy to find the right endpoint
- Swagger UI organized by tags

### 2. **Stronger Validation**
- Each endpoint validates account_type automatically
- Prevents creating wrong type of accounts
- Better error messages

### 3. **Easier Frontend Integration**
- Frontend can use specific endpoints for each form
- Create Asset Form → calls `/assets/`
- Create Income Form → calls `/income/`
- No need to manually set account_type

### 4. **Better Filtering**
- Each endpoint returns only relevant accounts
- `/assets/{company_id}` returns only assets
- Can further filter by category, status, etc.

### 5. **Cleaner Code**
- Reusable helper functions
- Consistent validation logic
- Easier to maintain

---

## Account Type Reference

### Assets (Account Type: "Assets")
**Common Categories:**
- Cash
- Bank
- Accounts Receivable
- Inventory
- Gold Stock
- Silver Stock
- Equipment
- Furniture

**Account Code Range:** 1000-1999

### Liabilities (Account Type: "Liabilities")
**Common Categories:**
- Accounts Payable
- Bank Loan
- Customer Deposits
- Interest Payable
- Taxes Payable

**Account Code Range:** 2000-2999

### Equity (Account Type: "Equity")
**Common Categories:**
- Capital
- Retained Earnings
- Drawings
- Current Year Profit/Loss

**Account Code Range:** 3000-3999

### Income (Account Type: "Income")
**Common Categories:**
- Interest
- Service Charges
- Sales Revenue
- Other Income

**Account Code Range:** 4000-4999

### Expenses (Account Type: "Expenses")
**Common Categories:**
- Rent
- Salary
- Utilities
- Supplies
- Depreciation
- Interest Expense
- Repairs & Maintenance

**Account Code Range:** 5000-5999

---

## Migration Guide

### If you were using old endpoints:

**Before:**
```bash
POST /chart-of-accounts/
{
  "company_id": 1,
  "account_code": "1000",
  "account_name": "Cash",
  "account_type": "Assets",
  ...
}
```

**After (Recommended):**
```bash
POST /assets/
{
  "company_id": 1,
  "account_code": "1000",
  "account_name": "Cash",
  "account_type": "Assets",  # Still required but auto-validated
  ...
}
```

**Old endpoints still work!** But new type-specific endpoints are recommended.

---

## Summary

✅ **5 new endpoint groups** created (Assets, Liabilities, Equity, Income, Expenses)
✅ **20+ new endpoints** total (CRUD for each type)
✅ **Automatic validation** of account types
✅ **Better organization** in Swagger UI
✅ **Filtering support** (category, status, pagination)
✅ **Backward compatible** - old endpoints still work
✅ **Cleaner code** with reusable helper functions

Now you can create specific accounts easily with type-safe endpoints! 🎉
