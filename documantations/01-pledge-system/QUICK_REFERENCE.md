# Pledge System - Quick Reference

## 🎯 Core Functionality at a Glance

| Feature | Details |
|---------|---------|
| **Auto Pledge Number** | Format: `GLD-2025-0001`, Scheme-based prefix, Auto-increment yearly |
| **Auto Ledger Entries** | 4 entries created automatically when pledge created |
| **Photo Upload** | Support for JPG, PNG, GIF, WebP, BMP (max 8MB) |
| **Pledge Items** | Track multiple items per pledge with individual specs |
| **Interest Calc** | Auto-calculated: `loan_amount × (rate / 100)` |
| **Lifecycle** | Active → Closed/Redeemed/Forfeited |
| **Authorization** | Per-company access control + admin override |

---

## 📡 API Endpoints Quick Reference

### Create Pledge (Auto-Ledger)
```
POST /pledges/

Body:
{
  "company_id": 1,
  "customer_id": 5,
  "scheme_id": 1,
  "gross_weight": 150.5,
  "net_weight": 145.2,
  "maximum_value": 75000,
  "loan_amount": 50000,
  "interest_rate": 2.5,
  "pledge_items": [
    {
      "jewel_type_id": 1,
      "jewel_design": "Gold Ring",
      "jewel_condition": "Excellent",
      "stone_type": "Diamond",
      "gross_weight": 50.5,
      "net_weight": 48.2,
      "quantity": 1
    }
  ]
}

Returns: Pledge object with ID and unique pledge_no
Auto-creates 4 ledger entries
```

### List Pledges
```
GET /pledges/{company_id}
?status_filter=Active
&customer_id=5
&scheme_id=1
```

### Get Specific Pledge
```
GET /pledges/{pledge_id}
```

### Get Pledge Items
```
GET /pledges/{pledge_id}/items
```

### Upload Pledge Photo
```
POST /pledges/{pledge_id}/upload-photo
Form-data: file (multipart)
```

### Update Pledge
```
PUT /pledges/{pledge_id}

Body:
{
  "interest_rate": 3.0
}
```

### Close Pledge
```
POST /pledges/{pledge_id}/close

Body:
{
  "new_status": "Redeemed",
  "notes": "Customer paid full amount"
}

Options: Redeemed, Closed, Forfeited
```

### Delete Pledge
```
DELETE /pledges/{pledge_id}
(Reverses all ledger entries automatically)
```

---

## 💰 Automatic Ledger Entries

When pledge is created, 4 entries are automatically added:

```
Entry 1: Record Items Received
  Debit:  Pledged Items (1040)
  Credit: Customer Receivable (1051xxxx)
  Amount: maximum_value

Entry 2: Record Loan Disbursed
  Debit:  Customer Receivable (1051xxxx)
  Credit: Cash/Payment Account
  Amount: loan_amount

Entry 3: Record Interest Received
  Debit:  Cash/Payment Account
  Credit: Interest Income (4000)
  Amount: first_month_interest

Entry 4: Final Balance
  All running balances auto-calculated
  Trial balance includes all entries
```

---

## 🔢 Pledge Number Format

```
{SCHEME_PREFIX}-{YEAR}-{SEQUENCE}

Examples:
GLD-2025-0001  (Gold scheme, 2025, 1st pledge)
GLD-2025-0002  (Gold scheme, 2025, 2nd pledge)
SLV-2025-0001  (Silver scheme, 2025, 1st pledge)
PLT-2025-0001  (Platinum scheme, 2025, 1st pledge)

Resets yearly:
GLD-2025-9999
GLD-2026-0001  (New year, resets to 0001)
```

---

## 📋 Pledge Status Flow

```
CREATION
   │
   ├─→ Active (default status)
   │    │
   │    ├─→ Closed (refinance/extend)
   │    ├─→ Redeemed (customer paid & got items)
   │    └─→ Forfeited (customer didn't pay)
   │
   └─→ (Can be deleted if still Active)
```

---

## 💡 Common Use Cases

### Case 1: Simple Gold Pledge
```
POST /pledges/
Customer: ₹50,000 against gold items
Interest: 2.5% per month = ₹1,250 first month

Auto-generated:
  Pledge No: GLD-2025-0001
  First Month Interest: ₹1,250 (calculated)
  Ledger Entries: 4 (automatic)
```

### Case 2: Multi-Item Pledge
```
POST /pledges/
Items:
  - Gold Ring
  - Gold Necklace
  - Silver Bracelet

Tracked individually in pledge_items table
Total weights aggregated
Each item visible in GET /pledges/{id}/items
```

### Case 3: Pledge Redemption
```
Customer wants items back after paying:

POST /pledges/{id}/close
{
  "new_status": "Redeemed"
}

Status changes to Redeemed
(Ledger adjustments done manually if needed)
```

### Case 4: Delete Pledge
```
DELETE /pledges/{id}

If still Active:
  - Deletes pledge record
  - Deletes pledge items
  - Reverses ALL ledger entries automatically
  - Deletes pledge photo if exists
```

---

## 🔑 Key Fields Explained

| Field | Example | Purpose |
|-------|---------|---------|
| `pledge_no` | GLD-2025-0001 | Unique identifier, auto-generated |
| `gross_weight` | 150.5 | Total weight including impurities |
| `net_weight` | 145.2 | Pure weight after deducting impurities |
| `maximum_value` | 75000 | Maximum loan eligible (market value) |
| `loan_amount` | 50000 | Actual amount loaned to customer |
| `interest_rate` | 2.5 | Monthly interest percentage |
| `first_month_interest` | 1250 | Interest for first month (auto-calc) |
| `payment_account_id` | 10 | Which account to credit (defaults to Cash) |
| `old_pledge_no` | SLV-2024-0045 | For refinancing/extension tracking |
| `status` | Active | Pledge status (Active/Closed/Redeemed/Forfeited) |

---

## 📊 Data Relationships

```
Company (1)
  ├── Pledge (many)
  │    ├── PledgeItems (many)
  │    ├── Customer (1)
  │    ├── Scheme (1)
  │    └── ChartOfAccounts (1) [payment_account]
  │
  ├── ChartOfAccounts (many)
  │    └── LedgerEntries (many)
  │
  ├── LedgerEntries (many)
  │    ├── Reference: Pledge (via reference_id)
  │    └── Running Balance (auto-calculated)
  │
  └── Customer (many)
      └── COA Account (1) [1051xxxx]
```

---

## ✅ Validation Rules

| Check | Rule | Error |
|-------|------|-------|
| Company | Must match user's company | 403 Forbidden |
| Customer | Must exist in same company | 404 Not Found |
| Scheme | Must exist in same company | 404 Not Found |
| Payment Account | Must exist if specified | 404 Not Found |
| Photo Size | Max 8MB | 400 Bad Request |
| Photo Type | PNG/JPG/GIF/WebP/BMP only | 400 Bad Request |
| Status Transition | Only from Active | 400 Bad Request |

---

## 🚀 Getting Started (5 Steps)

### Step 1: Start Server
```bash
cd /workspaces/codespaces-blank
uvicorn app.main:app --reload
```

### Step 2: Create Company (if not exists)
```bash
POST http://localhost:8000/companies/
{
  "company_name": "My Pawn Shop",
  "address": "123 Main St",
  "city": "Bangalore",
  "state": "KA",
  "phone": "9876543210"
}
```

### Step 3: Initialize Default COA
```bash
POST http://localhost:8000/chart-of-accounts/initialize-default/1
```

### Step 4: Create Customer (if not exists)
```bash
POST http://localhost:8000/customers/
{
  "company_id": 1,
  "customer_name": "John",
  "mobile": "9876543210"
}
```

### Step 5: Create Pledge
```bash
POST http://localhost:8000/pledges/
{
  "company_id": 1,
  "customer_id": 1,
  "scheme_id": 1,
  "gross_weight": 50,
  "net_weight": 48,
  "maximum_value": 40000,
  "loan_amount": 30000,
  "interest_rate": 2.5,
  "pledge_items": [
    {
      "jewel_type_id": 1,
      "jewel_design": "Gold Ring",
      "gross_weight": 50,
      "net_weight": 48,
      "quantity": 1
    }
  ]
}
```

---

## 🧪 Test File

Run comprehensive tests:
```bash
python testfiles/test_pledge_system.py
```

Tests included:
1. Create pledge with auto-ledger
2. Get pledges with filters
3. Get specific pledge
4. Upload photo
5. Get items
6. Update pledge
7. Close pledge
8. Delete pledge

---

## 📁 Files Created

```
app/
├── pledge_utils.py (NEW)
│   ├── generate_pledge_no()
│   ├── create_pledge_ledger_entries()
│   └── reverse_pledge_ledger_entries()
│
├── routes/
│   └── pledges.py (NEW)
│       ├── POST /pledges/ (create with auto-ledger)
│       ├── GET /pledges/{company_id}
│       ├── GET /pledges/{pledge_id}
│       ├── PUT /pledges/{pledge_id}
│       ├── POST /pledges/{pledge_id}/upload-photo
│       ├── POST /pledges/{pledge_id}/close
│       ├── DELETE /pledges/{pledge_id}
│       └── GET /pledges/{pledge_id}/items
│
├── file_handler.py (MODIFIED)
│   └── save_pledge_photo() + delete_pledge_photo()
│
└── main.py (MODIFIED)
    └── Pledge routes registered

testfiles/
└── test_pledge_system.py (NEW)
    └── 8 comprehensive tests

Documentation/
├── PLEDGE_SYSTEM.md (NEW)
│   └── Complete feature guide with examples
│
└── PLEDGE_SYSTEM_IMPLEMENTATION.md (NEW)
    └── Implementation summary & highlights
```

---

## 🔗 Integration Points

**Pledges integrate with:**
- ✅ Chart of Accounts (COA) - Accounts used for ledger
- ✅ Ledger Entries - Auto-created entries
- ✅ Customers - Customer lookup and receivables
- ✅ Schemes - Prefix generation and rates
- ✅ File Handler - Photo upload/delete
- ✅ Users - Audit trail (created_by)
- ✅ Companies - Data isolation

---

## 🎓 Learning Path

1. **Start Here**: This quick reference
2. **Read**: `PLEDGE_SYSTEM.md` for detailed guide
3. **Review**: `PLEDGE_SYSTEM_IMPLEMENTATION.md` for architecture
4. **Run Tests**: `testfiles/test_pledge_system.py`
5. **Explore**: `/docs` for interactive API docs
6. **Check Code**: Inline comments in `app/routes/pledges.py`

---

## 💬 Need Help?

Check these resources:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **PLEDGE_SYSTEM.md**: Complete documentation
- **test_pledge_system.py**: Working examples
- **Source Code**: Comments and docstrings

---

**Quick Reference - Pledge System Ready to Use! 🚀**
