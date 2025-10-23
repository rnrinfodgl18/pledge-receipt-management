# Pledge System - Complete Guide

## Overview

The Pledge System is a core component of the pawn shop management API that handles jewelry pledges (pawning) with automatic financial transaction tracking. When a customer pledges jewelry items, the system automatically:

1. **Generates unique pledge numbers** (format: `{SCHEME_PREFIX}-{YEAR}-{SEQUENCE}`, e.g., `GLD-2025-0001`)
2. **Creates financial transactions** in the Chart of Accounts/Ledger automatically
3. **Tracks individual pledged items** with detailed specifications
4. **Manages pledge lifecycle** (Active → Closed/Redeemed/Forfeited)
5. **Stores pledge photos** for verification and records

## Database Models

### Pledge Model
```
pledge_id (PK)
pledge_no (Unique) - Auto-generated with scheme prefix
company_id (FK) - Which company owns the pledge
customer_id (FK) - Customer who pledged items
scheme_id (FK) - Which jewelry scheme (Gold/Silver/Platinum)
pledge_date - When pledge was created
gross_weight - Total weight of all items
net_weight - Net weight (after impurities)
maximum_value - Calculated maximum value
loan_amount - Amount loaned to customer
interest_rate - Monthly interest rate (%)
first_month_interest - Interest calculated for first month
payment_account_id (FK) - Which account to credit (usually Cash)
pledge_photo - Path to pledge photo
status - Active/Closed/Redeemed/Forfeited
old_pledge_no - For refinancing tracking
created_at, updated_at - Timestamps
created_by (FK) - User who created the pledge
```

### PledgeItems Model
```
pledge_item_id (PK)
pledge_id (FK) - Which pledge
jewel_type_id (FK) - Type of jewelry (Gold/Silver/Platinum)
jewel_design - Design description (Ring, Necklace, Bracelet, etc.)
jewel_condition - Condition (Excellent, Good, Fair, Poor)
stone_type - Type of stones (Diamond, Ruby, Sapphire, etc.)
gross_weight - Weight of this item
net_weight - Net weight of this item
quantity - Number of items of this type
created_at, updated_at - Timestamps
created_by (FK) - User who created the entry
```

## Automatic Ledger Transactions

When a pledge is created, the system automatically creates the following ledger entries:

### 1. **Pledged Items Recording**
```
Debit:  Pledged Items Account (1040) = maximum_value
Credit: Customer Receivable (1051xxxx) = loan_amount
```
Records that items are now held by the pawn shop.

### 2. **Loan Disbursement**
```
Debit:  Customer Receivable (1051xxxx) = loan_amount
Credit: Payment Account (usually Cash 1000) = loan_amount
```
Records the cash given to customer.

### 3. **Interest Recording** (if applicable)
```
Credit: Interest Income (4000) = first_month_interest
Debit:  Payment Account (usually Cash 1000) = first_month_interest
```
Records interest received in advance/at pledging.

## API Endpoints

### 1. Create Pledge
```http
POST /pledges/
Content-Type: application/json

{
  "company_id": 1,
  "customer_id": 5,
  "scheme_id": 2,
  "pledge_date": "2025-01-20",
  "gross_weight": 150.5,
  "net_weight": 145.2,
  "maximum_value": 75000,
  "loan_amount": 50000,
  "interest_rate": 2.5,
  "first_month_interest": 1250,
  "payment_account_id": 10,  // Optional, defaults to Cash
  "old_pledge_no": "SLV-2024-0045",  // Optional, for refinancing
  "pledge_items": [
    {
      "jewel_type_id": 1,
      "jewel_design": "Gold Ring",
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

Response (201 Created):
{
  "id": 42,
  "company_id": 1,
  "pledge_no": "GLD-2025-0001",
  "customer_id": 5,
  "scheme_id": 2,
  "pledge_date": "2025-01-20",
  "gross_weight": 150.5,
  "net_weight": 145.2,
  "maximum_value": 75000,
  "loan_amount": 50000,
  "interest_rate": 2.5,
  "first_month_interest": 1250,
  "payment_account_id": 10,
  "pledge_photo": null,
  "status": "Active",
  "created_at": "2025-01-20T14:30:00",
  "pledge_items": [
    {
      "id": 1,
      "pledge_id": 42,
      "jewel_type_id": 1,
      "jewel_design": "Gold Ring",
      "jewel_condition": "Excellent",
      "stone_type": "Diamond",
      "gross_weight": 50.5,
      "net_weight": 48.2,
      "quantity": 1
    },
    // ... more items
  ]
}
```

**Behind the scenes:**
- ✅ Validates customer exists in same company
- ✅ Validates scheme exists in same company
- ✅ Generates unique pledge number: `GLD-2025-0001`
- ✅ Calculates first month interest if not provided
- ✅ Sets default payment account to Cash if not specified
- ✅ Creates pledge with all items
- ✅ **Automatically creates 4 ledger entries** for financial tracking
- ✅ Returns complete pledge with nested items

### 2. Get All Pledges
```http
GET /pledges/{company_id}?status_filter=Active&customer_id=5&scheme_id=2

Response (200 OK):
[
  {
    "id": 42,
    "pledge_no": "GLD-2025-0001",
    "customer_id": 5,
    "loan_amount": 50000,
    "status": "Active",
    "created_at": "2025-01-20T14:30:00"
    // ... full pledge data
  },
  {
    "id": 41,
    "pledge_no": "SLV-2025-0001",
    "customer_id": 6,
    "loan_amount": 30000,
    "status": "Active",
    "created_at": "2025-01-19T10:15:00"
    // ... full pledge data
  }
]
```

**Query Parameters:**
- `status_filter`: Active | Closed | Redeemed | Forfeited
- `customer_id`: Filter by customer
- `scheme_id`: Filter by scheme

### 3. Get Specific Pledge
```http
GET /pledges/{pledge_id}

Response (200 OK):
{
  "id": 42,
  "pledge_no": "GLD-2025-0001",
  // ... full pledge data with all items
}
```

### 4. Upload Pledge Photo
```http
POST /pledges/{pledge_id}/upload-photo
Content-Type: multipart/form-data

file: <binary image data>

Response (200 OK):
{
  "message": "Photo uploaded successfully",
  "pledge_id": 42,
  "photo_path": "uploads/pledge_photos/pledge_42_20250120_143000.jpg"
}
```

**Specifications:**
- Allowed formats: PNG, JPG, JPEG, GIF, WebP, BMP
- Maximum size: 8MB
- Saves to: `uploads/pledge_photos/`
- Automatic old photo cleanup

### 5. Update Pledge
```http
PUT /pledges/{pledge_id}
Content-Type: application/json

{
  "interest_rate": 3.0,
  "status": "Active"
}

Response (200 OK):
{
  "id": 42,
  // ... updated pledge data
}
```

### 6. Close/Redeem Pledge
```http
POST /pledges/{pledge_id}/close
Content-Type: application/json

{
  "new_status": "Redeemed",  // or "Closed" or "Forfeited"
  "notes": "Customer paid full amount and took items"
}

Response (200 OK):
{
  "message": "Pledge redeemed successfully",
  "pledge_id": 42,
  "pledge_no": "GLD-2025-0001",
  "new_status": "Redeemed"
}
```

**Status Transitions:**
- `Active → Closed` - Extension/refinance
- `Active → Redeemed` - Customer paid and collected items
- `Active → Forfeited` - Customer didn't pay, items forfeited

### 7. Get Pledge Items
```http
GET /pledges/{pledge_id}/items

Response (200 OK):
[
  {
    "id": 1,
    "pledge_id": 42,
    "jewel_type_id": 1,
    "jewel_design": "Gold Ring",
    "jewel_condition": "Excellent",
    "stone_type": "Diamond",
    "gross_weight": 50.5,
    "net_weight": 48.2,
    "quantity": 1
  },
  // ... more items
]
```

### 8. Delete Pledge
```http
DELETE /pledges/{pledge_id}

Response (204 No Content)
```

**Behind the scenes:**
- ✅ Reverses all associated ledger entries automatically
- ✅ Deletes pledge photo from disk
- ✅ Deletes all pledge items
- ✅ Only works for active pledges

## Pledge Number Generation

The system generates unique pledge numbers automatically using this logic:

```python
Format: {SCHEME_PREFIX}-{YEAR}-{SEQUENCE}

Example: GLD-2025-0001

- GLD = Gold Scheme Prefix
- 2025 = Current Year
- 0001 = Sequential number (per scheme per year)

Next pledges in Gold scheme:
GLD-2025-0001  (first)
GLD-2025-0002
GLD-2025-0003
...
GLD-2025-9999

Silver scheme uses separate sequence:
SLV-2025-0001  (first)
SLV-2025-0002
```

## Interest Calculation

First month interest is automatically calculated:

```python
monthly_rate = (interest_rate / 100)
first_month_interest = loan_amount * monthly_rate

Example:
- Loan Amount: ₹50,000
- Interest Rate: 2.5% per month
- First Month Interest: 50,000 × 0.025 = ₹1,250
```

## Account Mapping

The system uses these Chart of Accounts for pledges:

| Account Code | Account Name | Purpose |
|---|---|---|
| 1000 | Cash | Default payment account |
| 1010 | Bank Account | Alternative payment account |
| 1040 | Pledged Items | Holds pledged jewelry value |
| 1051xxxx | Customer Receivable | Tracks loan given to each customer |
| 4000 | Interest Income | Records interest received |

## Usage Examples

### Example 1: Simple Gold Pledge

Customer brings 2 gold rings and wants ₹30,000 loan at 3% monthly interest.

```python
POST /pledges/
{
  "company_id": 1,
  "customer_id": 5,
  "scheme_id": 1,  # Gold scheme
  "pledge_date": "2025-01-20",
  "gross_weight": 50,
  "net_weight": 48,
  "maximum_value": 40000,
  "loan_amount": 30000,
  "interest_rate": 3.0,
  # first_month_interest auto-calculated: 30000 × 0.03 = ₹900
  "pledge_items": [
    {
      "jewel_type_id": 1,
      "jewel_design": "Gold Ring",
      "jewel_condition": "Good",
      "gross_weight": 25,
      "net_weight": 24,
      "quantity": 2
    }
  ]
}

# Returns:
# Pledge ID: 42, Pledge No: GLD-2025-0001
# First Month Interest: ₹900 (auto-calculated)
# Ledger entries created automatically
```

### Example 2: Multi-Item Pledge

Customer brings mixed items: gold ring, gold chain, silver bracelet.

```python
POST /pledges/
{
  "company_id": 1,
  "customer_id": 6,
  "scheme_id": 1,  # Gold scheme (primary item)
  "pledge_date": "2025-01-20",
  "gross_weight": 150,
  "net_weight": 145,
  "maximum_value": 80000,
  "loan_amount": 50000,
  "interest_rate": 2.5,
  "pledge_items": [
    {
      "jewel_type_id": 1,  # Gold
      "jewel_design": "Gold Ring",
      "stone_type": "Diamond",
      "gross_weight": 50,
      "net_weight": 48,
      "quantity": 1
    },
    {
      "jewel_type_id": 1,  # Gold
      "jewel_design": "Gold Chain",
      "gross_weight": 75,
      "net_weight": 72,
      "quantity": 1
    },
    {
      "jewel_type_id": 2,  # Silver
      "jewel_design": "Silver Bracelet",
      "gross_weight": 25,
      "net_weight": 25,
      "quantity": 1
    }
  ]
}

# Returns:
# Pledge ID: 43, Pledge No: GLD-2025-0002
# All items tracked individually
```

### Example 3: Pledge Redemption

Customer repays loan + interest and wants their items back.

```python
POST /pledges/42/close
{
  "new_status": "Redeemed"
}

# Additional steps (manual):
# 1. Record full payment in ledger
# 2. Generate redemption certificate
# 3. Handover items to customer
```

## Business Logic

### Pledge Creation Flow
1. Customer data validated (must exist in company)
2. Scheme data validated (determines prefix, rate)
3. Unique pledge number generated automatically
4. Interest calculated if not provided
5. Payment account defaulted to Cash if not specified
6. Pledge record created
7. All pledge items added
8. **4 Ledger entries created automatically**:
   - Pledged Items recorded (Debit)
   - Loan disbursed (Credit)
   - Interest recorded (if applicable)
   - Cash updated

### Financial Accuracy
- Running balance calculated in ledger automatically
- All transactions tracked with reference_type="Pledge" and reference_id
- Complete audit trail maintained
- Trial balance includes all pledge transactions

### Photo Management
- Max 8MB per image
- Stored in `/uploads/pledge_photos/`
- Old photo automatically deleted when new one uploaded
- Photo deleted when pledge deleted

## Integration Points

### With Chart of Accounts
- Pledge creation uses COA accounts (1040, 1051xxxx, 4000)
- Ensures consistent account structure
- Supports automatic COA initialization

### With Ledger Entries
- All pledges create corresponding ledger entries
- Ledger running balance updated automatically
- Trial balance includes all pledge transactions
- Ledger entries reversed when pledge deleted

### With Customers
- Links to CustomerDetails model
- Customer Receivable account auto-created for each customer
- Tracks individual customer pledge history

### With Schemes
- Links to Scheme model
- Scheme prefix used for pledge number generation
- Scheme rates used as defaults

## Error Handling

### Common Errors & Solutions

| Error | Cause | Solution |
|---|---|---|
| Customer not found | Invalid customer_id or different company | Verify customer exists in same company |
| Scheme not found | Invalid scheme_id or different company | Verify scheme exists in same company |
| Payment account not found | Invalid account_id | Use existing COA account or leave blank for default |
| File too large | Pledge photo > 8MB | Compress image before upload |
| Invalid file type | Wrong image format | Use PNG, JPG, JPEG, GIF, WebP, or BMP |

## Performance Tips

1. **Batch Creation**: Create multiple pledges in bulk operations when possible
2. **Filtering**: Always use filters (status_filter, customer_id) when querying large datasets
3. **Photo Upload**: Upload photos separately after pledge creation if multiple pledges
4. **Ledger Queries**: Use date filters to limit ledger entry queries
5. **Indexes**: Ensure indexes on pledge_no, customer_id, status for faster queries

## Security

1. **Authorization**: Only users in the same company can manage pledges (or admins)
2. **Audit Trail**: All actions tracked with created_by user ID
3. **Timestamps**: Auto-managed by system
4. **Photo Security**: Files stored outside web root, served via /uploads mount

## Future Enhancements

1. **Pledge Renewal**: Auto-extend pledges with new interest calculation
2. **Interest Accrual**: Track monthly interest accrual as pledges age
3. **Partial Redemption**: Allow customer to redeem partial items
4. **Auctions**: Track unsold/forfeited items for auction
5. **SMS Alerts**: Notify customers of pledge expiry dates
6. **Mobile App**: QR code scanning for pledges

## Related Documentation

- See [Chart of Accounts Guide](./HOW_TO_CREATE_DEFAULT_COA.md) for COA setup
- See [Ledger Entries Documentation](./api-documentation.md) for transaction reporting
- See [Customer Management](./CUSTOMER_MANAGEMENT.md) for customer-related features
