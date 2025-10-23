# Pledge System Implementation - Summary

## 🎯 What Was Created

A complete Pledge (Pawn) management system integrated with the FastAPI pawn shop API that automatically handles financial accounting and transaction tracking.

---

## 📁 Files Created/Modified

### 1. **NEW: `app/pledge_utils.py`**
Utility functions for pledge operations:
- `generate_pledge_no()` - Auto-generates unique pledge numbers (format: `GLD-2025-0001`)
- `create_pledge_ledger_entries()` - Creates 4 automatic ledger entries when pledge created
- `reverse_pledge_ledger_entries()` - Reverses ledger entries when pledge deleted

**Key Features:**
- Scheme-based prefix generation (Gold: GLD, Silver: SLV, etc.)
- Auto-incrementing sequence per scheme per year
- Automatic debit/credit entries for financial tracking
- Full integration with Chart of Accounts

### 2. **NEW: `app/routes/pledges.py`**
Complete REST API routes for pledge management:

**Endpoints:**
- `POST /pledges/` - Create pledge with auto-ledger (✅ **NEW FEATURE**)
- `GET /pledges/{company_id}` - List pledges with filters
- `GET /pledges/{pledge_id}` - Get specific pledge with items
- `PUT /pledges/{pledge_id}` - Update pledge
- `POST /pledges/{pledge_id}/upload-photo` - Upload pledge photo
- `POST /pledges/{pledge_id}/close` - Close/redeem/forfeit pledge
- `DELETE /pledges/{pledge_id}` - Delete pledge & reverse entries
- `GET /pledges/{pledge_id}/items` - Get items in pledge

**Key Features:**
- ✅ Automatic pledge number generation with scheme prefix
- ✅ Automatic first month interest calculation
- ✅ Default payment account to Cash
- ✅ **Automatic 4 ledger entries creation**
- ✅ Nested pledge items support
- ✅ Photo upload with automatic old photo cleanup
- ✅ Pledge lifecycle management (Active → Closed/Redeemed/Forfeited)
- ✅ Full authorization checks per company

### 3. **MODIFIED: `app/file_handler.py`**
Added pledge photo support:
- `save_pledge_photo()` - Save pledge image (max 8MB)
- `delete_pledge_photo()` - Delete pledge image
- Added `PLEDGE_PHOTOS_DIR` with automatic directory creation

**Specifications:**
- Allowed formats: PNG, JPG, JPEG, GIF, WebP, BMP
- Max size: 8MB (same as company logos for consistency)
- Storage: `uploads/pledge_photos/`
- Automatic cleanup on delete

### 4. **MODIFIED: `app/main.py`**
Registered pledge routes:
- Added import: `from app.routes.pledges import router as pledges_router`
- Added router: `app.include_router(pledges_router)`

### 5. **NEW: `PLEDGE_SYSTEM.md`**
Comprehensive documentation:
- Complete feature overview
- Database schema details
- Automatic ledger transaction examples
- All API endpoints with request/response examples
- Pledge number generation logic
- Interest calculation
- Usage examples (simple pledge, multi-item, redemption)
- Business logic flow
- Integration points
- Error handling
- Security considerations
- Future enhancement ideas

### 6. **NEW: `testfiles/test_pledge_system.py`**
Complete test suite with 8 test scenarios:
1. Create pledge with items and auto-ledger verification
2. Get all pledges with filters
3. Get specific pledge with detailed info
4. Upload pledge photo
5. Get pledge items
6. Update pledge
7. Close/redeem pledge
8. Delete pledge with ledger reversal

---

## 🔑 Key Features Implemented

### 1. **Automatic Pledge Number Generation**
```
Format: {SCHEME_PREFIX}-{YEAR}-{SEQUENCE}
Example: GLD-2025-0001

- Scheme-wise prefixes (Gold: GLD, Silver: SLV, etc.)
- Auto-incrementing sequence per scheme per year
- Guaranteed unique across company history
```

### 2. **Automatic Ledger Entry Creation** ⭐
When a pledge is created, system automatically creates 4 ledger entries:

```
1. Debit:  Pledged Items (1040)  = maximum_value
   Credit: Customer Receivable (1051xxxx) = loan_amount
   
   (Records that items are now held by shop)

2. Debit:  Cash/Bank Account = loan_amount
   Credit: Customer Receivable = loan_amount
   
   (Records cash given to customer)

3. Debit:  Cash/Bank Account = first_month_interest
   Credit: Interest Income (4000) = first_month_interest
   
   (Records interest received)
```

### 3. **Smart Account Selection**
- Payment account defaults to Cash if not specified
- Supports custom payment accounts (Bank, etc.)
- Customer-specific Receivable accounts created automatically
- All accounts validated before use

### 4. **Pledge Items Tracking**
- Support for multiple items per pledge
- Detailed specs per item (design, condition, stones, weight, qty)
- Individual weight tracking
- Auto-aggregation to pledge totals

### 5. **Photo Management**
- Upload pledge photos for verification
- Automatic old photo cleanup
- Support for multiple image formats
- Integrated with pledge CRUD

### 6. **Pledge Lifecycle**
```
Active (created) 
├── Redeemed (customer paid, items returned)
├── Closed (extension/refinance)
└── Forfeited (unpaid, items kept)
```

### 7. **Financial Integration**
- Auto-ledger entries for complete financial tracking
- Running balance calculated automatically
- Trial balance includes all pledge transactions
- Full audit trail with created_by user

---

## 💰 Financial Accounting Example

**Customer pledges gold items for ₹50,000 at 2.5% monthly interest:**

```
Pledge Created:
  pledge_no: GLD-2025-0001
  loan_amount: ₹50,000
  interest_rate: 2.5%
  first_month_interest: ₹1,250 (auto-calculated)

Ledger Entries Created (Automatic):
  1. Dr: Pledged Items (1040)         ₹75,000
     Cr: Customer Receivable (1051005) ₹75,000
     
  2. Dr: Customer Receivable (1051005) ₹50,000
     Cr: Cash (1000)                   ₹50,000
     
  3. Dr: Cash (1000)                   ₹1,250
     Cr: Interest Income (4000)        ₹1,250

Trial Balance Updates:
  ✅ Assets increase (Pledged Items: +₹75,000)
  ✅ Liabilities increase (Receivable: +₹25,000)
  ✅ Income recorded (Interest: +₹1,250)
  ✅ All entries automatically sync to running balance
```

---

## 🚀 How It Works

### Creating a Pledge

```python
# 1. API receives pledge creation request
POST /pledges/
{
  "company_id": 1,
  "customer_id": 5,
  "scheme_id": 1,
  "gross_weight": 150.5,
  "net_weight": 145.2,
  "maximum_value": 75000,
  "loan_amount": 50000,
  "interest_rate": 2.5,
  "pledge_items": [...]
}

# 2. System validates all required data
✅ Customer exists in company
✅ Scheme exists in company
✅ Payment account accessible

# 3. Auto-generates pledge number
generate_pledge_no(scheme_id=1, company_id=1)
→ "GLD-2025-0001"

# 4. Calculates first month interest
first_month_interest = 50000 × (2.5 / 100) = ₹1,250

# 5. Creates pledge record with items

# 6. Creates automatic ledger entries
create_pledge_ledger_entries()
→ 4 ledger entries created
→ Running balance calculated
→ All accounts updated

# 7. Returns complete pledge with nested items
Response (201 Created):
{
  "id": 42,
  "pledge_no": "GLD-2025-0001",
  "loan_amount": 50000,
  "first_month_interest": 1250,
  "pledge_items": [...]
}
```

### Database Updates

When pledge is created, the database is updated:

```sql
-- Pledge created
INSERT INTO pledge (pledge_no, customer_id, scheme_id, ...)
VALUES ('GLD-2025-0001', 5, 1, ...);

-- Items recorded
INSERT INTO pledge_items (pledge_id, jewel_type_id, ...)
VALUES (42, 1, ...);

-- Ledger entries created (4 entries)
INSERT INTO ledger_entries (account_id, transaction_type, amount, reference_type, reference_id, ...)
VALUES 
  (1040, 'Debit', 75000, 'Pledge', 42, ...),  -- Pledged Items
  (1051, 'Credit', 75000, 'Pledge', 42, ...),  -- Customer Receivable
  (1000, 'Credit', 50000, 'Pledge', 42, ...),  -- Cash
  (4000, 'Credit', 1250, 'Pledge', 42, ...);   -- Interest Income

-- Running balances updated for all accounts
UPDATE ledger_entries SET running_balance = ... WHERE account_id IN (1000, 1040, 1051, 4000);
```

---

## 📊 Models & Schema

### Pledge Model
```
id, company_id, pledge_no, customer_id, scheme_id, 
pledge_date, gross_weight, net_weight, maximum_value,
loan_amount, interest_rate, first_month_interest,
payment_account_id, pledge_photo, status, old_pledge_no,
created_at, updated_at, created_by
```

### PledgeItems Model
```
id, pledge_id, jewel_type_id, jewel_design, 
jewel_condition, stone_type, gross_weight, net_weight,
quantity, created_at, updated_at, created_by
```

### Pledge Schemas (Pydantic)
- `PledgeBase` - Base fields
- `PledgeCreate` - Create with nested items
- `PledgeUpdate` - Partial updates
- `Pledge` - Full response with items
- `PledgeItemsCreate`, `PledgeItemsUpdate`, `PledgeItems` - Item variants

---

## 🔗 Integration with Existing System

### Chart of Accounts Integration
- Pledge creation uses 4 standard COA accounts
- Supports auto-initialization with `initialize-default/{company_id}`
- All accounts linked via account_id FK

### Ledger Integration
- All pledge transactions create ledger entries
- Ledger running balance auto-calculated
- Trial balance includes all pledge entries
- Full audit trail via ledger

### Customer Integration
- Links to CustomerDetails model
- Creates unique Receivable account per customer
- Customer CRUD creates/deletes corresponding COA account

### Scheme Integration
- Uses Scheme prefix for pledge number generation
- Uses Scheme interest rate as default
- Separate sequence per scheme per year

### File Upload Integration
- Extends existing file_handler.py
- Pledge photos stored in dedicated directory
- Same cleanup/validation as company logos

---

## 🛡️ Security & Authorization

✅ **Per-Company Access Control**
- Only users in same company can manage pledges (or admins)
- Validates company_id in all requests

✅ **Audit Trail**
- All actions tracked with created_by user ID
- Timestamps auto-managed by system

✅ **Data Integrity**
- Foreign key constraints on customer_id, scheme_id, payment_account_id
- Cascading deletes with automatic ledger reversal

✅ **File Security**
- Photos stored outside web root
- Served via /uploads mount point
- Maximum file sizes enforced (8MB)

---

## ✨ Highlights of This Implementation

1. **Automatic Ledger Synchronization** ⭐
   - Zero manual accounting needed
   - All entries created in background
   - Running balance auto-calculated

2. **Scheme-Based Numbering**
   - Clean pledge number format
   - Easy tracking per scheme
   - Sequence resets yearly

3. **Complete Validation**
   - All relationships verified
   - File size/type checks
   - Financial calculations validated

4. **Flexible Status Management**
   - Supports multiple pledge states
   - Clear state transitions
   - Extensible for future statuses

5. **Integrated Photo Support**
   - Seamless image upload
   - Auto cleanup on delete
   - Multiple format support

6. **Error Handling**
   - Comprehensive error messages
   - Proper HTTP status codes
   - Transaction rollback on failure

---

## 🧪 Testing the System

### Quick Test
```bash
cd /workspaces/codespaces-blank
python testfiles/test_pledge_system.py
```

### Manual Test via Postman
1. Create pledge: `POST /pledges/`
2. Get pledges: `GET /pledges/{company_id}`
3. Check ledger: `GET /ledger-entries/{account_id}`
4. View trial balance: `GET /ledger-entries/trial-balance/{company_id}`

### Interactive API Docs
```
http://localhost:8000/docs
```

---

## 📚 Documentation

Complete documentation available in:
- **`PLEDGE_SYSTEM.md`** - Full feature guide with examples
- **API Docs** - `/docs` endpoint (Swagger UI)
- **Inline Comments** - In all source files

---

## 🚀 Quick Start

### 1. Start the Server
```bash
cd /workspaces/codespaces-blank
uvicorn app.main:app --reload
```

### 2. Initialize Default COA (if not done)
```bash
POST http://localhost:8000/chart-of-accounts/initialize-default/1
```

### 3. Create Your First Pledge
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

### 4. View Generated Ledger Entries
```bash
GET http://localhost:8000/ledger-entries/trial-balance/1
```

---

## ✅ What's Included

✅ Complete database models (Pledge, PledgeItems)  
✅ Pydantic validation schemas  
✅ 8 REST API endpoints  
✅ Automatic pledge number generation  
✅ **Automatic ledger entry creation (4 entries per pledge)**  
✅ Photo upload support  
✅ File management (upload/delete)  
✅ Authorization & access control  
✅ Comprehensive error handling  
✅ Extensive documentation  
✅ Complete test suite  
✅ Integration with existing systems  

---

## 📝 Next Possible Enhancements

1. **Pledge Renewal** - Auto-extend with new interest
2. **Interest Accrual** - Track monthly accrual as pledges age
3. **Partial Redemption** - Redeem some items, extend others
4. **Auction System** - For forfeited/unsold items
5. **SMS Notifications** - Alert customers of expiry dates
6. **Mobile QR Codes** - Quick pledge lookup
7. **Advanced Reports** - Pledge portfolio analysis
8. **Payment Tracking** - Partial payments and installments

---

## 📞 Support

For issues or questions:
1. Check `PLEDGE_SYSTEM.md` documentation
2. Review test examples in `test_pledge_system.py`
3. Check API swagger docs at `/docs`
4. Examine code comments in source files

---

**Pledge System Successfully Implemented! 🎉**
