# Pledge Receipt System - Testing Guide

## 🧪 Quick Start Testing

### Prerequisites
- FastAPI server running: `uvicorn app.main:app --reload`
- Access: `http://localhost:8000/docs`
- PostgreSQL database connected
- Test data: At least 1 company, 1 user, 1 customer, 1 pledge

---

## TEST 1: Full Close - Automatic Pledge Status Update

### Setup
```bash
# 1. Get a pledge to work with
GET /api/pledges/1
Response:
{
  "id": 1,
  "pledge_no": "GLD-2025-0001",
  "loan_amount": 10000,
  "first_month_interest": 500,
  "status": "Active"
}
```

### Test Case 1A: Create Receipt with Full Payment
```bash
POST /api/receipts/
Content-Type: application/json

{
  "company_id": 1,
  "receipt_date": "2025-10-23T10:00:00",
  "receipt_amount": 10500,
  "payment_mode": "Cash",
  "customer_id": 1,
  "bank_name": null,
  "check_number": null,
  "transaction_id": null,
  "remarks": "Full payment for pledge #1",
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

Expected Response:
{
  "id": 1,
  "receipt_no": "RCP-2025-0001",
  "status": "Draft",           ✅ DRAFT (not posted yet)
  "coa_entry_status": "Pending",
  "receipt_items": [...]
}
```

### Test Case 1B: Post Receipt (Triggers Auto Update)
```bash
POST /api/receipts/1/post

Expected Response:
{
  "id": 1,
  "receipt_no": "RCP-2025-0001",
  "status": "Posted",          ✅ NOW POSTED
  "coa_entry_status": "Posted", ✅ COA ENTRIES CREATED
  "receipt_items": [...]
}
```

### Test Case 1C: Check Pledge Status (Should be Auto-Updated!)
```bash
GET /api/pledges/1

Expected Response:
{
  "id": 1,
  "pledge_no": "GLD-2025-0001",
  "loan_amount": 10000,
  "status": "Redeemed"         ✅ AUTO-UPDATED!
}

✅ FEATURE VERIFIED: Pledge status automatically changed to "Redeemed"
```

### Test Case 1D: Verify COA Entries Created
```bash
GET /api/ledger-entries?reference_type=Receipt&reference_id=1

Expected Response (List of entries):
[
  {
    "id": 1,
    "account_id": 10,  (Cash)
    "transaction_type": "Debit",
    "amount": 10500,
    "description": "Receipt RCP-2025-0001 - Cash received"
  },
  {
    "id": 2,
    "account_id": 50,  (Receivable)
    "transaction_type": "Credit",
    "amount": 10000,
    "description": "Receipt RCP-2025-0001 - Principal payment"
  },
  {
    "id": 3,
    "account_id": 40,  (Interest Income)
    "transaction_type": "Credit",
    "amount": 500,
    "description": "Receipt RCP-2025-0001 - Interest income"
  }
]

✅ COA ENTRIES VERIFIED: 3 entries created automatically
```

---

## TEST 2: Receipt Void - Automatic COA Reversal

### Setup (Continue from Test 1)
- Have a posted receipt: RCP-2025-0001
- Pledge is in "Redeemed" status
- 3 COA entries exist

### Test Case 2A: Void the Receipt
```bash
POST /api/receipts/1/void?reason=Data+entry+error

Expected Response:
{
  "id": 1,
  "receipt_no": "RCP-2025-0001",
  "status": "Void",             ✅ STATUS CHANGED
  "coa_entry_status": "Pending",
  "remarks": "Void - Data entry error"
}
```

### Test Case 2B: Check Pledge Status (Should Revert!)
```bash
GET /api/pledges/1

Expected Response:
{
  "id": 1,
  "pledge_no": "GLD-2025-0001",
  "status": "Active"            ✅ AUTO REVERTED!
}

✅ FEATURE VERIFIED: Pledge status automatically reverted to "Active"
```

### Test Case 2C: Verify COA Reversal Entries Created
```bash
GET /api/ledger-entries?reference_type=Receipt&reference_id=1

Expected Response (Should now have 6 entries - 3 original + 3 reversals):
[
  {
    "id": 1,
    "transaction_type": "Debit",
    "amount": 10500,
    "description": "Receipt RCP-2025-0001 - Cash received"
  },
  {
    "id": 2,
    "transaction_type": "Credit",
    "amount": 10000,
    "description": "Receipt RCP-2025-0001 - Principal payment"
  },
  {
    "id": 3,
    "transaction_type": "Credit",
    "amount": 500,
    "description": "Receipt RCP-2025-0001 - Interest income"
  },
  {
    "id": 4,
    "transaction_type": "Credit",    ✅ REVERSED (was Debit)
    "amount": 10500,
    "description": "Reversal of Receipt RCP-2025-0001 - Cash received"
  },
  {
    "id": 5,
    "transaction_type": "Debit",     ✅ REVERSED (was Credit)
    "amount": 10000,
    "description": "Reversal of Receipt RCP-2025-0001 - Principal payment"
  },
  {
    "id": 6,
    "transaction_type": "Debit",     ✅ REVERSED (was Credit)
    "amount": 500,
    "description": "Reversal of Receipt RCP-2025-0001 - Interest income"
  }
]

✅ COA REVERSAL VERIFIED: 3 reverse entries created automatically
```

---

## TEST 3: Delete Draft Receipt (No Reversal Needed)

### Setup
```bash
# 1. Create a new draft receipt
POST /api/receipts/
{
  "company_id": 1,
  "receipt_date": "2025-10-23T11:00:00",
  "receipt_amount": 5000,
  "payment_mode": "Check",
  "customer_id": 1,
  "check_number": "CHK001",
  "receipt_items": [{
    "pledge_id": 1,
    "principal_amount": 5000,
    "interest_amount": 0,
    "paid_principal": 5000,
    "paid_interest": 0,
    "payment_type": "Partial",
    "total_amount_paid": 5000
  }]
}

Response: Receipt with status: "Draft"
```

### Test Case 3A: Delete Draft Receipt
```bash
DELETE /api/receipts/2

Expected Response:
{
  "detail": "Receipt RCP-2025-0002 deleted successfully"
}

✅ DELETION VERIFIED: Draft receipt deleted
```

### Test Case 3B: Verify No COA Entries Exist
```bash
GET /api/ledger-entries?reference_type=Receipt&reference_id=2

Expected Response:
[]  ← Empty list

✅ NO REVERSAL NEEDED: Draft receipts don't have COA entries
```

---

## TEST 4: Multiple Pledges in One Receipt

### Setup
- Have 2 pledges with different amounts
- Pledge #1: Outstanding = 10,000
- Pledge #2: Outstanding = 5,000

### Test Case 4A: Create Receipt with Multiple Pledges
```bash
POST /api/receipts/
{
  "company_id": 1,
  "receipt_date": "2025-10-23T12:00:00",
  "receipt_amount": 15000,
  "payment_mode": "Bank Transfer",
  "transaction_id": "TXN123456",
  "receipt_items": [
    {
      "pledge_id": 1,
      "principal_amount": 10000,
      "interest_amount": 0,
      "paid_principal": 10000,
      "paid_interest": 0,
      "payment_type": "Full",
      "total_amount_paid": 10000
    },
    {
      "pledge_id": 2,
      "principal_amount": 5000,
      "interest_amount": 0,
      "paid_principal": 5000,
      "paid_interest": 0,
      "payment_type": "Full",
      "total_amount_paid": 5000
    }
  ]
}

Response: Receipt with 2 items
```

### Test Case 4B: Post Receipt
```bash
POST /api/receipts/3/post

Expected Response: Posted receipt
```

### Test Case 4C: Check Both Pledges Auto-Updated
```bash
GET /api/pledges/1
Response: status = "Redeemed" ✅

GET /api/pledges/2
Response: status = "Redeemed" ✅

✅ VERIFIED: Both pledges automatically marked as Redeemed
```

### Test Case 4D: Check COA Entries (4-6 entries)
```bash
GET /api/ledger-entries?reference_type=Receipt&reference_id=3

Expected: 4 entries
- DR: Cash = 15000
- CR: Receivable-Pledge1 = 10000
- CR: Receivable-Pledge2 = 5000
(Note: May be 3 or 6 entries depending on sub-account setup)

✅ VERIFIED: Multi-pledge receipt created with correct COA entries
```

---

## TEST 5: Multiple Payments for Same Pledge

### Setup
- Have 1 pledge: Outstanding = 10,000 + 500 interest = 10,500 total
- Will pay in 2 receipts

### Test Case 5A: First Payment (Partial)
```bash
POST /api/receipts/
{
  "company_id": 1,
  "receipt_date": "2025-10-23T13:00:00",
  "receipt_amount": 6000,
  "payment_mode": "Cash",
  "receipt_items": [{
    "pledge_id": 1,
    "principal_amount": 10000,
    "interest_amount": 500,
    "paid_principal": 5500,
    "paid_interest": 500,
    "payment_type": "Partial",
    "total_amount_paid": 6000
  }]
}

POST /api/receipts/4/post
```

### Test Case 5B: Check Pledge (Still Active)
```bash
GET /api/pledges/1
Response: status = "Active" ✅ (Still has 4500 remaining)
```

### Test Case 5C: Second Payment (Full Close)
```bash
POST /api/receipts/
{
  "company_id": 1,
  "receipt_date": "2025-10-23T14:00:00",
  "receipt_amount": 4500,
  "payment_mode": "Cash",
  "receipt_items": [{
    "pledge_id": 1,
    "principal_amount": 10000,
    "interest_amount": 500,
    "paid_principal": 4500,
    "paid_interest": 0,
    "payment_type": "Full",
    "total_amount_paid": 4500
  }]
}

POST /api/receipts/5/post
```

### Test Case 5D: Check Pledge (Now Redeemed!)
```bash
GET /api/pledges/1
Response: status = "Redeemed" ✅

✅ VERIFIED: Pledge marked as Redeemed only after ALL payments received
```

---

## TEST 6: Discount and Penalty Handling

### Test Case 6A: Receipt with Discount
```bash
POST /api/receipts/
{
  "company_id": 1,
  "receipt_date": "2025-10-23T15:00:00",
  "receipt_amount": 9700,  # 10000 - 300 discount
  "payment_mode": "Cash",
  "receipt_items": [{
    "pledge_id": 3,
    "principal_amount": 10000,
    "interest_amount": 1000,
    "discount_interest": 300,      # 300 discount given
    "additional_penalty": 0,
    "paid_principal": 10000,
    "paid_interest": 700,           # 1000 - 300 discount
    "paid_discount": 300,           # Discount amount
    "paid_penalty": 0,
    "payment_type": "Full",
    "total_amount_paid": 10700
  }]
}

POST /api/receipts/6/post
```

### Test Case 6B: Verify COA Entries (5 entries)
```bash
GET /api/ledger-entries?reference_type=Receipt&reference_id=6

Expected entries:
1. DR: Cash = 10700
2. CR: Receivable = 10000
3. CR: Interest Income = 700
4. DR: Interest Discount = 300
5. Balances all matched ✅
```

---

## ✅ Test Completion Checklist

- [ ] Test 1A: Receipt created in Draft
- [ ] Test 1B: Receipt posted successfully
- [ ] Test 1C: ✅ Pledge status auto-updated to "Redeemed"
- [ ] Test 1D: ✅ COA entries created automatically (3 entries)
- [ ] Test 2A: Receipt voided successfully
- [ ] Test 2B: ✅ Pledge status auto-reverted to "Active"
- [ ] Test 2C: ✅ COA reversals created automatically (3 reversal entries)
- [ ] Test 3A: Draft receipt deleted
- [ ] Test 3B: ✅ No COA entries for draft (correct!)
- [ ] Test 4A: Multi-pledge receipt created
- [ ] Test 4B: Multi-pledge receipt posted
- [ ] Test 4C: ✅ Both pledges auto-updated to "Redeemed"
- [ ] Test 4D: ✅ COA entries correct for multiple pledges
- [ ] Test 5A: First partial payment posted
- [ ] Test 5B: ✅ Pledge still "Active" after partial
- [ ] Test 5C: Second full payment posted
- [ ] Test 5D: ✅ Pledge auto-updated to "Redeemed" on final payment
- [ ] Test 6A: Discount receipt posted
- [ ] Test 6B: ✅ COA entries correct with discount handling

---

## 🎉 All Tests Passing?

If all tests above pass with ✅, then:

✅ **Automatic Pledge Status Update** - WORKING!
✅ **Automatic COA Entry Creation** - WORKING!
✅ **Automatic COA Entry Reversal** - WORKING!
✅ **Automatic Balance Recalculation** - WORKING!
✅ **Automatic Status Reversion** - WORKING!

**Pledge Receipt System is FULLY OPERATIONAL! 🚀**
