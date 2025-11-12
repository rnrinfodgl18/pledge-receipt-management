# Old Data Access API - Read-Only Endpoints

## Overview (மொத்த விளக்கம்)

உங்கள் database-ல **old_** prefix-உடன் இருக்கும் 5 tables-இலிருந்து data-ஐ fetch செய்ய **read-only GET endpoints** உருவாக்கப்பட்டுள்ளது.

**⚠️ Important: இவை read-only endpoints - create, update, delete செய்ய முடியாது!**

## Available Tables (கிடைக்கும் Tables)

1. **old_accmaster** - Account Master (பழைய கணக்கு master)
2. **old_account_ledger** - Account Ledger Entries (பழைய ledger entries)
3. **old_customer** - Customer Records (பழைய customer தரவு)
4. **old_jewel_desc** - Pledge/Loan Records (பழைய அடகு தரவு)
5. **old_jewel_details** - Pledge Item Details (பழைய அடகு பொருள் விவரங்கள்)

## API Endpoints

### 1. Old Account Master (பழைய கணக்கு Master)

#### Get All Accounts
```
GET /old-data/accounts
```

**Query Parameters:**
- `accode` (optional) - Account code வைத்து filter
- `accname` (optional) - Account name வைத்து search
- `accttype` (optional) - Account type வைத்து filter
- `limit` (optional, default=100) - Maximum records
- `offset` (optional, default=0) - Skip records

**Example:**
```bash
GET /old-data/accounts?accname=cash&limit=10
GET /old-data/accounts?accttype=ASSET
```

**Response:**
```json
[
  {
    "slno": 1,
    "accode": "1000",
    "accname": "CASH ACCOUNT",
    "opbaldeb": 50000.00,
    "opbalcre": 0.00,
    "curbaldeb": 75000.00,
    "curbalcre": 0.00,
    "accttype": "ASSET",
    "schedno": 1,
    "opbaldate": "2024-01-01T00:00:00",
    "conscno": null
  }
]
```

#### Get Account by ID
```
GET /old-data/accounts/{slno}
```

**Example:**
```bash
GET /old-data/accounts/1
```

---

### 2. Old Account Ledger (பழைய Ledger Entries)

#### Get All Ledger Entries
```
GET /old-data/ledger
```

**Query Parameters:**
- `jlno` (optional) - Journal number வைத்து filter
- `from_date` (optional) - From date (YYYY-MM-DD)
- `to_date` (optional) - To date (YYYY-MM-DD)
- `register` (optional) - Register வைத்து filter
- `limit` (optional, default=100)
- `offset` (optional, default=0)

**Example:**
```bash
GET /old-data/ledger?jlno=JL001
GET /old-data/ledger?from_date=2024-01-01&to_date=2024-12-31
GET /old-data/ledger?register=MAIN&limit=50
```

**Response:**
```json
[
  {
    "ID": 1,
    "date": "2024-10-15T10:30:00",
    "jlno": "JL001",
    "description": "Loan payment",
    "debit": 5000.00,
    "credit": 0.00,
    "register": "MAIN"
  }
]
```

#### Get Ledger Entry by ID
```
GET /old-data/ledger/{entry_id}
```

---

### 3. Old Customers (பழைய Customer தரவு)

#### Get All Customers
```
GET /old-data/customers
```

**Query Parameters:**
- `name` (optional) - Customer name வைத்து search
- `mobile` (optional) - Mobile number வைத்து search
- `pno` (optional) - PNO வைத்து filter
- `limit` (optional, default=100)
- `offset` (optional, default=0)

**Example:**
```bash
GET /old-data/customers?name=kumar
GET /old-data/customers?mobile=9876543210
GET /old-data/customers?pno=P001
```

**Response:**
```json
[
  {
    "pno": "P001",
    "name": "KUMAR",
    "address": "123 Main Street, Chennai",
    "phoneno": "044-12345678",
    "mobile": "9876543210",
    "int_date": "2024-01-15",
    "cust_refno": "REF001",
    "pictures": null,
    "entrydate": "2024-01-15T09:00:00"
  }
]
```

#### Get Customer by PNO
```
GET /old-data/customers/{pno}
```

**Example:**
```bash
GET /old-data/customers/P001
```

---

### 4. Old Pledges (பழைய அடகு Records)

#### Get All Pledges
```
GET /old-data/pledges
```

**Query Parameters:**
- `jlno` (optional) - Journal number வைத்து filter
- `pcode` (optional) - Party code வைத்து filter
- `from_date` (optional) - From loan date (YYYY-MM-DD)
- `to_date` (optional) - To loan date (YYYY-MM-DD)
- `jeweltype` (optional) - Jewel type வைத்து filter
- `register` (optional) - Register வைத்து filter
- `limit` (optional, default=100)
- `offset` (optional, default=0)

**Example:**
```bash
GET /old-data/pledges?jlno=JL001
GET /old-data/pledges?from_date=2024-01-01&to_date=2024-12-31
GET /old-data/pledges?jeweltype=GOLD&limit=20
GET /old-data/pledges?pcode=P001
```

**Response:**
```json
[
  {
    "jlno": "JL001",
    "laon_date": "2024-10-15T00:00:00",
    "party_details": "KUMAR - P001",
    "jewel_weight": "25.50",
    "jewel_description": "Gold chain and ring",
    "loan_amount": 50000.00,
    "loan_ret_amount": 0.00,
    "loan_interest": 2500.00,
    "loan_ret_date": null,
    "actual_maturity": "2025-01-15T00:00:00",
    "maturity_date": "2025-01-15T00:00:00",
    "pcode": "P001",
    "vno": 101,
    "intper": 2.0,
    "rvno": null,
    "splace": null,
    "sdetails": null,
    "currate": 5000.00,
    "curamount": 50000.00,
    "bvno": null,
    "brvno": null,
    "orgweight": 25.50,
    "jeweltype": "GOLD",
    "register": "MAIN",
    "notes": null,
    "tagcode": "TAG001",
    "notice1date": null,
    "notice2date": null,
    "notice3date": null,
    "days": 90,
    "auts": null,
    "pictures": null
  }
]
```

#### Get Pledge by Journal Number
```
GET /old-data/pledges/{jlno}
```

**Example:**
```bash
GET /old-data/pledges/JL001
```

---

### 5. Old Pledge Items (பழைய அடகு பொருள் விவரங்கள்)

#### Get All Pledge Items
```
GET /old-data/pledge-items
```

**Query Parameters:**
- `jlno` (optional) - Journal number வைத்து filter
- `register` (optional) - Register வைத்து filter
- `limit` (optional, default=100)
- `offset` (optional, default=0)

**Example:**
```bash
GET /old-data/pledge-items?jlno=JL001
GET /old-data/pledge-items?register=MAIN&limit=50
```

**Response:**
```json
[
  {
    "sno": 1,
    "laon_date": "2024-10-15T00:00:00",
    "jlno": "JL001",
    "register": "MAIN",
    "itemdet": "Gold chain 22K",
    "qty": 1.0,
    "grosswt": 25.50,
    "netweight": 24.00,
    "notes": "Good condition"
  },
  {
    "sno": 2,
    "laon_date": "2024-10-15T00:00:00",
    "jlno": "JL001",
    "register": "MAIN",
    "itemdet": "Gold ring 18K",
    "qty": 1.0,
    "grosswt": 10.25,
    "netweight": 9.50,
    "notes": null
  }
]
```

#### Get Pledge Item by Serial Number
```
GET /old-data/pledge-items/{sno}
```

**Example:**
```bash
GET /old-data/pledge-items/1
```

---

### 6. Summary Statistics

#### Get Overall Summary
```
GET /old-data/stats/summary
```

**Response:**
```json
{
  "accounts_count": 150,
  "ledger_entries_count": 5420,
  "customers_count": 320,
  "pledges_count": 1250,
  "pledge_items_count": 3680,
  "message": "All data is read-only from old tables"
}
```

---

## Common Use Cases (பொதுவான பயன்பாடுகள்)

### 1. Customer-அ தேடி அவரது அடகுகளை பார்க்க

```bash
# Step 1: Customer-ஐ தேடு
GET /old-data/customers?name=kumar

# Response: pno = "P001"

# Step 2: அந்த customer-ன் அடகுகளை பார்க்க
GET /old-data/pledges?pcode=P001
```

### 2. Specific Pledge மற்றும் அதன் Items

```bash
# Step 1: Pledge-ஐ எடு
GET /old-data/pledges/JL001

# Step 2: அந்த pledge-ன் items-ஐ எடு
GET /old-data/pledge-items?jlno=JL001
```

### 3. Date Range-ல Ledger Entries

```bash
GET /old-data/ledger?from_date=2024-01-01&to_date=2024-12-31&limit=100
```

### 4. Specific Account-ன் Details

```bash
# Account code வைத்து தேடு
GET /old-data/accounts?accode=1000

# அல்லது name வைத்து
GET /old-data/accounts?accname=CASH
```

---

## Authentication (அங்கீகாரம்)

**All endpoints require authentication!**

உங்கள் request-ல் Bearer token அனுப்ப வேண்டும்:

```bash
Authorization: Bearer <your-token>
```

Swagger UI-ல நேரடியாக test செய்யலாம்: **http://127.0.0.1:8000/docs**

---

## Important Notes (முக்கிய குறிப்புகள்)

### ✅ What You CAN Do:
- ✅ Read/View all old data (எல்லா பழைய data-வையும் பார்க்கலாம்)
- ✅ Search and filter records (தேடி filter செய்யலாம்)
- ✅ Export data for migration (migration-க்கு data எடுக்கலாம்)
- ✅ View historical records (பழைய records பார்க்கலாம்)

### ❌ What You CANNOT Do:
- ❌ Create new records (புதிய records create செய்ய முடியாது)
- ❌ Update existing records (இருக்கும் records-ஐ update செய்ய முடியாது)
- ❌ Delete records (records-ஐ delete செய்ய முடியாது)
- ❌ Modify any data (எந்த data-வையும் மாற்ற முடியாது)

### 🔒 Read-Only Protection:
இந்த endpoints **read-only** - database-ல இருக்கும் பழைய data-ஐ மாத்தவே முடியாது. Safety-க்காக இப்படி design செய்யப்பட்டுள்ளது.

---

## Data Migration Workflow (தரவு மாற்றம்)

இந்த endpoints-ஐ பயன்படுத்தி பழைய data-ஐ புதிய system-க்கு மாற்றலாம்:

```python
# Example: Migrate old customers to new system
import requests

# 1. Get old customers
old_customers = requests.get("http://api/old-data/customers?limit=1000")

# 2. Transform and create in new system
for old_cust in old_customers.json():
    new_customer = {
        "company_id": 1,
        "customer_name": old_cust["name"],
        "mobile": old_cust["mobile"],
        # ... map other fields
    }
    requests.post("http://api/customers/", json=new_customer)
```

---

## Tamil Field Mapping (தமிழ் Field விளக்கம்)

### Old Customer Fields:
- `pno` - Customer number (கஸ்டமர் எண்)
- `name` - பெயர்
- `address` - முகவரி
- `phoneno` - தொலைபேசி எண்
- `mobile` - மொபைல் எண்
- `entrydate` - பதிவு செய்த தேதி

### Old Pledge Fields:
- `jlno` - Journal number (அடகு எண்)
- `laon_date` - அடகு தேதி
- `party_details` - கஸ்டமர் விவரம்
- `jewel_weight` - நகை எடை
- `jewel_description` - நகை விவரம்
- `loan_amount` - அடகு தொகை
- `loan_interest` - வட்டி தொகை
- `maturity_date` - முதிர்வு தேதி

---

## Summary

✅ **Created:** 16 read-only GET endpoints
✅ **Tables Covered:** 5 old tables
✅ **Features:** Search, filter, pagination
✅ **Security:** Authentication required
✅ **Purpose:** View old data for migration/reference

**All endpoints available at: http://127.0.0.1:8000/docs (Swagger UI)**

நீங்கள் இப்போது உங்கள் பழைய data-ஐ பாதுகாப்பாக பார்க்கலாம்! 🎉
