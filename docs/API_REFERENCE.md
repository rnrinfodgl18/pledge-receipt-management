# API Reference - Pledge Receipt System

## Base URL
```
http://localhost:8000/api
```

## Authentication
All endpoints require JWT token authentication via `Authorization: Bearer {token}`

---

## Endpoints

### 1. Create Receipt

**Endpoint:** `POST /receipts/`

**Description:** Create a new receipt in Draft status

**Request Body:**
```json
{
  "company_id": 1,
  "receipt_date": "2025-10-23T10:00:00",
  "receipt_amount": 10500,
  "payment_mode": "Cash",
  "customer_id": 1,
  "bank_name": null,
  "check_number": null,
  "transaction_id": null,
  "remarks": "Payment received",
  "receipt_items": [
    {
      "pledge_id": 1,
      "principal_amount": 10000,
      "interest_amount": 500,
      "discount_interest": 0,
      "additional_penalty": 0,
      "paid_principal": 10000,
      "paid_interest": 500,
      "paid_discount": 0,
      "paid_penalty": 0,
      "payment_type": "Full",
      "total_amount_paid": 10500,
      "notes": "Full settlement"
    }
  ]
}
```

**Response (201):**
```json
{
  "id": 1,
  "receipt_no": "RCP-2025-0001",
  "company_id": 1,
  "customer_id": 1,
  "receipt_date": "2025-10-23T10:00:00",
  "receipt_amount": 10500,
  "payment_mode": "Cash",
  "bank_name": null,
  "check_number": null,
  "transaction_id": null,
  "remarks": "Payment received",
  "receipt_status": "Draft",
  "coa_entry_status": "Pending",
  "created_by": 1,
  "created_at": "2025-10-23T10:00:00",
  "updated_at": "2025-10-23T10:00:00",
  "updated_by": null,
  "receipt_items": [...]
}
```

---

### 2. List Receipts

**Endpoint:** `GET /receipts/company/{company_id}`

**Description:** Get list of receipts with optional filters

**Query Parameters:**
- `status` (optional): Draft, Posted, Void, Adjusted
- `customer_id` (optional): Filter by customer ID
- `payment_mode` (optional): Cash, Check, Bank Transfer, Card
- `from_date` (optional): Date format YYYY-MM-DD
- `to_date` (optional): Date format YYYY-MM-DD
- `skip` (optional): Default 0
- `limit` (optional): Default 100, max 1000

**Example:**
```
GET /receipts/company/1?status=Posted&from_date=2025-10-01&to_date=2025-10-31&limit=50
```

**Response (200):**
```json
[
  {
    "id": 1,
    "receipt_no": "RCP-2025-0001",
    "receipt_status": "Posted",
    "receipt_amount": 10500,
    ...
  },
  {
    "id": 2,
    "receipt_no": "RCP-2025-0002",
    "receipt_status": "Draft",
    ...
  }
]
```

---

### 3. Get Receipt Details

**Endpoint:** `GET /receipts/{receipt_id}`

**Description:** Get complete receipt details with items

**Path Parameters:**
- `receipt_id`: Receipt ID (integer)

**Response (200):**
```json
{
  "id": 1,
  "receipt_no": "RCP-2025-0001",
  "company_id": 1,
  "customer_id": 1,
  "receipt_date": "2025-10-23T10:00:00",
  "receipt_amount": 10500,
  "payment_mode": "Cash",
  "receipt_status": "Posted",
  "coa_entry_status": "Posted",
  "receipt_items": [
    {
      "id": 1,
      "receipt_id": 1,
      "pledge_id": 1,
      "principal_amount": 10000,
      "interest_amount": 500,
      "discount_interest": 0,
      "additional_penalty": 0,
      "paid_principal": 10000,
      "paid_interest": 500,
      "paid_discount": 0,
      "paid_penalty": 0,
      "payment_type": "Full",
      "total_amount_paid": 10500,
      "notes": "Full settlement",
      "created_at": "2025-10-23T10:00:00",
      "created_by": 1
    }
  ]
}
```

---

### 4. Get Receipt Items

**Endpoint:** `GET /receipts/{receipt_id}/items`

**Description:** Get items in a specific receipt

**Response (200):**
```json
[
  {
    "id": 1,
    "receipt_id": 1,
    "pledge_id": 1,
    "principal_amount": 10000,
    "interest_amount": 500,
    "discount_interest": 0,
    "additional_penalty": 0,
    "paid_principal": 10000,
    "paid_interest": 500,
    "paid_discount": 0,
    "paid_penalty": 0,
    "payment_type": "Full",
    "total_amount_paid": 10500,
    "created_at": "2025-10-23T10:00:00",
    "created_by": 1
  }
]
```

---

### 5. Update Receipt

**Endpoint:** `PUT /receipts/{receipt_id}`

**Description:** Update receipt (Draft status only)

**Request Body (all optional):**
```json
{
  "receipt_date": "2025-10-23T10:00:00",
  "receipt_amount": 10500,
  "payment_mode": "Cash",
  "bank_name": null,
  "check_number": null,
  "transaction_id": null,
  "remarks": "Updated remarks",
  "customer_id": 1
}
```

**Response (200):** Updated receipt object

**Error Cases:**
- 404: Receipt not found
- 400: Cannot update receipt in Posted/Void status

---

### 6. Post Receipt ⭐ (TRIGGERS AUTO FEATURES)

**Endpoint:** `POST /receipts/{receipt_id}/post`

**Description:** Post receipt and create COA entries
- ✅ Automatically creates accounting entries
- ✅ Automatically updates pledge status if fully paid
- Changes receipt status to "Posted"
- Marks COA as "Posted"

**Path Parameters:**
- `receipt_id`: Receipt ID

**Response (200):**
```json
{
  "id": 1,
  "receipt_no": "RCP-2025-0001",
  "receipt_status": "Posted",
  "coa_entry_status": "Posted",
  "receipt_items": [...]
}
```

**Automatic Actions:**
1. Creates 2-5 COA entries
2. For each pledge item:
   - Checks if fully paid
   - If yes → Sets pledge.status = "Redeemed" ✅
3. All in single transaction (atomic)

**Error Cases:**
- 404: Receipt not found
- 400: Cannot post non-Draft receipt
- 500: Failed to create COA entries

---

### 7. Void Receipt ⭐ (TRIGGERS AUTO REVERSAL)

**Endpoint:** `POST /receipts/{receipt_id}/void`

**Description:** Void receipt and reverse COA entries
- ✅ Automatically reverses all COA entries
- ✅ Automatically recalculates pledge status
- Changes receipt status to "Void"
- Marks COA as "Pending"

**Query Parameters:**
- `reason` (required): Reason for voiding

**Example:**
```
POST /receipts/1/void?reason=Data+entry+error
```

**Response (200):**
```json
{
  "id": 1,
  "receipt_no": "RCP-2025-0001",
  "receipt_status": "Void",
  "coa_entry_status": "Pending",
  "remarks": "Void - Data entry error",
  "receipt_items": [...]
}
```

**Automatic Actions:**
1. Finds all COA entries for receipt
2. Creates reverse entries:
   - Debit → Credit
   - Credit → Debit
3. For each pledge:
   - Recalculates balance
   - If was "Redeemed" → changes to "Active" ✅
4. All in single transaction (atomic)

**Error Cases:**
- 404: Receipt not found
- 400: Cannot void non-Posted receipt
- 500: Failed to reverse COA entries

---

### 8. Delete Receipt

**Endpoint:** `DELETE /receipts/{receipt_id}`

**Description:** Delete receipt (Draft status only)
- No COA impact (Draft = no entries created)
- Deletes receipt and all items

**Response (200):**
```json
{
  "detail": "Receipt RCP-2025-0001 deleted successfully"
}
```

**Error Cases:**
- 404: Receipt not found
- 400: Cannot delete non-Draft receipt

---

## Status Codes

| Code | Meaning |
|------|---------|
| 200 | Success |
| 201 | Created |
| 400 | Bad Request (validation error) |
| 401 | Unauthorized (missing token) |
| 404 | Not Found |
| 500 | Server Error |

---

## Receipt Status Workflow

```
Draft
  ↓ (POST /post)
Posted (COA created, pledges updated)
  ↓ (POST /void)
Void (COA reversed, pledges recalculated)

OR

Draft
  ↓ (DELETE)
Deleted (no accounting impact)
```

---

## Common Scenarios

### Scenario 1: Simple Full Payment
```bash
# 1. Create receipt with full payment
POST /receipts/
{
  "company_id": 1,
  "receipt_date": "2025-10-23T10:00:00",
  "receipt_amount": 10000,
  "payment_mode": "Cash",
  "receipt_items": [{
    "pledge_id": 1,
    "principal_amount": 10000,
    "interest_amount": 0,
    "paid_principal": 10000,
    "paid_interest": 0,
    "payment_type": "Full",
    "total_amount_paid": 10000
  }]
}
# Response: receipt_id = 1

# 2. Post receipt (AUTO: Creates COA, Updates pledge to Redeemed)
POST /receipts/1/post
# Response: receipt_status = "Posted", coa_entry_status = "Posted"

# 3. Verify pledge
GET /pledges/1
# Response: status = "Redeemed" ✅
```

### Scenario 2: Multi-Pledge Receipt
```bash
# 1. Create receipt with 3 pledges
POST /receipts/
{
  "company_id": 1,
  "receipt_amount": 15000,
  "receipt_items": [
    {"pledge_id": 1, "paid_principal": 5000, ...},
    {"pledge_id": 2, "paid_principal": 7000, ...},
    {"pledge_id": 3, "paid_principal": 3000, ...}
  ]
}

# 2. Post receipt
POST /receipts/1/post
# AUTO: All 3 pledges checked & updated ✅

# Result:
GET /pledges/1  → status = "Redeemed"
GET /pledges/2  → status = "Redeemed"
GET /pledges/3  → status = "Redeemed"
```

### Scenario 3: Void & Reverse
```bash
# 1. Post receipt
POST /receipts/1/post
# Result: Pledge marked "Redeemed"

# 2. Void receipt
POST /receipts/1/void?reason=Error

# AUTO: COA reversed, Pledge reverted ✅
GET /pledges/1  → status = "Active"
```

---

## Error Responses

### Validation Error
```json
{
  "detail": "Receipt amount 10000 doesn't match items total 9000"
}
```

### Not Found
```json
{
  "detail": "Receipt not found"
}
```

### Status Error
```json
{
  "detail": "Can only post receipts in Draft status, current: Posted"
}
```

### COA Error
```json
{
  "detail": "Failed to create COA entries"
}
```

---

## Tips

1. **Always post receipts** - Without posting, no COA entries created
2. **Check status before void** - Can only void "Posted" receipts
3. **Use filters** - Use status, date filters when listing large datasets
4. **Validate amounts** - Receipt total must equal sum of items
5. **Monitor COA entries** - Check ledger entries after posting
6. **Atomic operations** - All or nothing (no partial updates)

---

## Testing the API

Use Swagger UI at `http://localhost:8000/docs` to:
- See all endpoints with documentation
- Try out requests
- See example responses
- Check parameter requirements

Or use curl:
```bash
# Create receipt
curl -X POST http://localhost:8000/api/receipts/ \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{...}'

# Post receipt
curl -X POST http://localhost:8000/api/receipts/1/post \
  -H "Authorization: Bearer YOUR_TOKEN"

# Check results
curl -X GET http://localhost:8000/api/pledges/1 \
  -H "Authorization: Bearer YOUR_TOKEN"
```

---

**Last Updated:** October 23, 2025
**Version:** 1.0.0
