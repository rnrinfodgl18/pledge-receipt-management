# Pledge to Bank - Real Business Rotation Workflow

## 🎯 Real-World Business Scenario

### Problem:
The pawn shop needs cash for business operations but doesn't have enough funds. Solution: Use the pledged items held with the shop as collateral to get financing from the bank.

### Cash Flow Cycle:

```
┌──────────────────────────────────────────────────────────────────────┐
│                      BUSINESS ROTATION CYCLE                         │
└──────────────────────────────────────────────────────────────────────┘

NORMAL FLOW (No Bank Needed):
Customer → Pledge Items → Pawn Shop Holds → Customer Pays → Get Items Back

WHEN CASH NEEDED (Bank Rotation):
Customer → Pledge Items → Bank (as collateral) → Cash to Pawn Shop
                                                        ↓
                                          Business uses cash
                                                        ↓
                                    EITHER Customer pays back
                                         OR Business gets cash
                                                        ↓
                                         Pay bank → Get pledge back
                                                        ↓
                                    Return to customer
```

---

## 📊 Three Possible Redemption Scenarios

### Scenario A: BUSINESS PAYS BACK (Business has cash)
```
Timeline:
─────────────────────────────────────────────────────────

Day 1:  Pledge to Bank
        Shop: Send pledge to bank
        Bank: Give us ₹50,000 cash
        
Day 30: Business improves, cash available
        Shop: Pay ₹50,000 to bank
        Bank: Return pledge
        Shop: Still waiting for customer payment (different transaction)
        
Day 45: Customer pays ₹55,000 (principal + interest + extension)
        Shop: Record customer payment
        Customer: Gets pledge back
        Result: ✓ Both settled

Ledger Impact:
├─ Bank gives us ₹50,000 (improves cash flow)
├─ Business uses ₹50,000 for operations
├─ We pay back ₹50,000 to bank (reduces cash)
└─ Customer payment ₹55,000 (separate transaction)
```

### Scenario B: CUSTOMER PAYS, WE PAY BANK (Customer's payment used to redeem)
```
Timeline:
─────────────────────────────────────────────────────────

Day 1:  Pledge to Bank
        Shop: Send ₹50,000 pledge to bank
        Bank: Give us ₹50,000 cash
        
Day 30: Customer pays ₹55,000 (more than we owe bank!)
        Shop: Receives ₹55,000 from customer
        Option: Pay bank ₹50,000 from this
        Bank: Return pledge
        Shop: Keep ₹5,000 as profit
        
Result: Pledge redeemed, customer settled, profit made ✓

Ledger Impact:
├─ Bank gives ₹50,000 (improves liquidity)
├─ Customer pays ₹55,000 (improves cash)
├─ We pay bank ₹50,000 (debt repayment)
├─ Profit: ₹5,000 (income account)
└─ Pledge back in our hands
```

### Scenario C: CUSTOMER + BUSINESS PAY (Split payment)
```
Timeline:
─────────────────────────────────────────────────────────

Day 1:  Pledge to Bank
        Shop: Send ₹50,000 pledge to bank
        Bank: Give us ₹50,000 cash
        
Day 15: Customer pays ₹30,000 (partial)
        Shop: Record receipt ₹30,000
        Bank: Still holding pledge (we owe ₹50k)
        
Day 30: Business pays remaining ₹20,000 to complete bank repayment
        Shop: Pay bank ₹20,000
        Bank: Return pledge
        Total to bank: ₹30k (customer) + ₹20k (business) = ₹50k ✓
        
Result: Pledge redeemed with combined payments ✓

Ledger Impact:
├─ Received from customer: ₹30,000
├─ Paid from business cash: ₹20,000
├─ Total to bank: ₹50,000
├─ Pledge redeemed: ✓
└─ Both transactions settled: ✓
```

---

## 💾 Updated Database Schema

### New Field in BankRedemption Model:
```python
class BankRedemption(Base):
    """Enhanced redemption model tracking source of payment."""
    
    id = Column(Integer, primary_key=True)
    bank_pledge_id = Column(Integer, ForeignKey("bank_pledges.id"))
    
    # ... existing fields ...
    
    # NEW: Track payment sources
    receipt_id = Column(Integer, ForeignKey("pledge_receipts.id"), nullable=True)
    # If customer payment used to pay bank
    
    payment_source = Column(String, default="MANUAL")
    # MANUAL: We paid from business cash
    # RECEIPT: Customer payment used
    # COMBINED: Both sources
    
    customer_payment_amount = Column(Float, default=0.0)
    # How much came from customer receipt
    
    business_payment_amount = Column(Float, default=0.0)
    # How much came from business cash
    
    status = Column(String, default="REDEEMED")
    # REDEEMED, PARTIAL, AWAITING_CUSTOMER_PAYMENT
```

---

## 📋 API Endpoints - Enhanced

### 1. **Simple Bank Redemption** (Business pays from cash)
```http
POST /bank-pledges/{id}/redeem
Authorization: Bearer {token}

{
  "redemption_date": "2025-11-15",
  "amount_paid_to_bank": 50000.0,
  "interest_on_bank_loan": 2000.0,
  "bank_charges": 500.0,
  "actual_redemption_value": 50000.0,
  "payment_source": "MANUAL",
  "business_payment_amount": 52500.0,
  "remarks": "Business cash payment to bank"
}

RESPONSE:
{
  "id": 1,
  "bank_pledge_id": 1,
  "status": "REDEEMED",
  "payment_source": "MANUAL",
  "amount_paid": 52500.0,
  "message": "Pledge redeemed successfully. Customer payment is separate."
}
```

### 2. **Customer Receipt → Bank Redemption** (Link receipt to bank redemption)
```http
POST /bank-pledges/{id}/redeem-with-receipt
Authorization: Bearer {token}

{
  "redemption_date": "2025-11-15",
  "receipt_id": 10,  # Customer payment receipt ID
  "use_receipt_amount": 50000.0,  # Amount from receipt to use for bank
  "additional_business_payment": 2500.0,  # Extra we add from business cash
  "payment_source": "COMBINED",  # RECEIPT or COMBINED
  "remarks": "Customer payment used to redeem pledge"
}

RESPONSE:
{
  "id": 1,
  "bank_pledge_id": 1,
  "receipt_id": 10,
  "status": "REDEEMED",
  "payment_source": "COMBINED",
  "customer_payment_used": 50000.0,
  "business_payment_used": 2500.0,
  "total_paid_to_bank": 52500.0,
  "message": "Pledge redeemed using customer payment + business cash"
}
```

### 3. **Mark as Awaiting Customer Payment** (If customer hasn't paid yet)
```http
POST /bank-pledges/{id}/await-customer-payment
Authorization: Bearer {token}

{
  "bank_loan_due": 50000.0,
  "expected_customer_payment": 55000.0,
  "remarks": "Waiting for customer to pay"
}

RESPONSE:
{
  "status": "AWAITING_CUSTOMER_PAYMENT",
  "bank_pledge_id": 1,
  "message": "Status set to awaiting. Customer payment will trigger auto-redemption"
}
```

### 4. **Get Bank Pledges by Payment Status**
```http
GET /bank-pledges?company_id=1&payment_status=AWAITING_CUSTOMER_PAYMENT
Authorization: Bearer {token}

RESPONSE:
{
  "awaiting_payment": [
    {
      "id": 1,
      "pledge_no": "GLD-2025-0001",
      "customer_name": "Ravi Kumar",
      "bank_loan_due": 50000.0,
      "expected_customer_payment": 55000.0,
      "days_waiting": 5
    }
  ]
}
```

---

## 🔄 Automatic Redemption Workflow

### Feature: Auto-Redeem on Receipt Payment

When a receipt is created for a pledge that has an active bank pledge:

```
┌─────────────────────────────────────────────────────────────┐
│ STEP 1: CREATE RECEIPT FOR CUSTOMER PAYMENT                │
├─────────────────────────────────────────────────────────────┤
│ POST /receipts                                              │
│ {                                                           │
│   pledge_id: 5,                                             │
│   receipt_amount: 55000,                                    │
│   payment_type: "Full"                                      │
│ }                                                           │
│                                                             │
│ System checks: Is this pledge with a bank? YES!            │
│                                                             │
│ OPTION A: AUTO MODE (Automatic)                            │
│ ├─ Extract ₹50,000 for bank payment                         │
│ ├─ Create bank redemption automatically                     │
│ ├─ Link receipt to bank redemption                          │
│ ├─ Update pledge status to REDEEMED                         │
│ └─ Keep ₹5,000 as profit in cash account                    │
│                                                             │
│ OPTION B: MANUAL MODE (Manual confirmation needed)         │
│ ├─ Mark pledge as "AWAITING_BANK_REDEMPTION"               │
│ ├─ Show user: "Use ₹50,000 to redeem from bank?"           │
│ ├─ User confirms → Proceed with auto-redemption            │
│ └─ User declines → Keep cash, update receipt separately    │
│                                                             │
└─────────────────────────────────────────────────────────────┘
         ↓
┌─────────────────────────────────────────────────────────────┐
│ RESULT: BOTH TRANSACTIONS SETTLED                           │
├─────────────────────────────────────────────────────────────┤
│ ✓ Customer receipt recorded                                 │
│ ✓ Bank pledge redeemed                                      │
│ ✓ Pledge status: REDEEMED                                   │
│ ✓ Ledger entries balanced                                   │
│ ✓ Profit/Loss calculated                                    │
│ ✓ Cash position improved                                    │
└─────────────────────────────────────────────────────────────┘
```

---

## 💰 Ledger Journal Entries - Real Scenario

### Scenario: Customer pays ₹55,000, Bank loan ₹50,000

```
Timeline of Entries:
───────────────────────────────────────────────────

DAY 1: Pledge to Bank
Entry Set 1:
├─ DR: Bank Pledge Asset (2100) = ₹50,000
├─ CR: Bank Loan Payable (2200) = ₹50,000
└─ DR: Jewelry Inventory (1500) = ₹50,000
   CR: Customer Receivable (1051) = ₹50,000

DAY 30: Customer pays ₹55,000
Entry Set 2:
├─ DR: Cash (1000) = ₹55,000
├─ CR: Customer Receivable (1051) = ₹50,000
├─ CR: Profit on Pledge (4200) = ₹5,000
└─ [Receipt created with status = "PENDING_BANK_REDEMPTION"]

DAY 30: Auto-Redeem from Bank (using customer payment)
Entry Set 3:
├─ DR: Bank Loan Payable (2200) = ₹50,000
├─ CR: Bank Pledge Asset (2100) = ₹50,000
├─ [Link receipt to bank redemption]
├─ [Mark receipt as "LINKED_TO_BANK_REDEMPTION"]
└─ Result: Bank loan closed, pledge redeemed ✓

FINAL LEDGER POSITION:
├─ Cash: +₹55,000 ✓
├─ Customer Receivable: ₹0 ✓
├─ Bank Loan: ₹0 ✓
├─ Profit: +₹5,000 ✓
└─ Trial Balance: BALANCED ✓
```

---

## 🎯 Updated Business Logic

### New Validation Rules:

1. **When creating receipt for pledged-with-bank item:**
   - Check if pledge has active bank pledge
   - If yes, show option: "Use this payment to redeem from bank?"
   - If amount >= bank loan, allow auto-redemption
   - If amount < bank loan, create PARTIAL redemption

2. **When auto-redeeming:**
   - Deduct bank loan amount from receipt
   - Link receipt to bank redemption
   - Calculate profit/loss if actual price differs
   - Update both pledge and bank pledge status

3. **When creating new receipt without bank redemption:**
   - Mark receipt as "NOT_LINKED_TO_BANK"
   - Bank pledge remains active
   - Keep tracking that customer payment is pending

---

## 📱 Frontend Integration

### Updated Receipt Creation Screen:

```
┌─────────────────────────────────────────────────────┐
│ Create Receipt                                      │
├─────────────────────────────────────────────────────┤
│ Select Pledge:    [GLD-2025-0001 ▼]                 │
│ Customer:         Ravi Kumar (fixed)                │
│ Receipt Amount:   [₹55,000]                         │
│                                                     │
│ ⚠️  ALERT: This pledge is with HDFC Bank!          │
│    Bank Loan Due: ₹50,000                           │
│    Your Payment:  ₹55,000                           │
│                                                     │
│ ☑ Auto-redeem from bank using this payment         │
│  └─ Profit to capture: ₹5,000 ✓                     │
│                                                     │
│ OR                                                  │
│                                                     │
│ ☐ Keep this payment separate (manual redemption)   │
│  └─ You'll redeem bank pledge separately            │
│                                                     │
│ Payment Details:                                    │
│ ├─ If auto-redeem:                                 │
│ │  ├─ To Bank: ₹50,000                             │
│ │  ├─ Profit: ₹5,000                               │
│ │  └─ Status: REDEEMED ✓                           │
│ │                                                  │
│ ├─ If manual:                                      │
│ │  ├─ Customer Receivable: ₹55,000                 │
│ │  ├─ Bank Pledge: STILL ACTIVE                    │
│ │  └─ Status: AWAITING BANK REDEMPTION             │
│                                                     │
│ [Preview] [Cancel] [Create Receipt]                │
└─────────────────────────────────────────────────────┘
```

### Dashboard Widget:

```
┌──────────────────────────────────────────────┐
│ Bank Pledges - Action Items                  │
├──────────────────────────────────────────────┤
│                                              │
│ 🏦 WITH BANK (3)                            │
│ ├─ GLD-0001: Awaiting customer payment      │
│ │  Expected: ₹55,000 (in 5 days)           │
│ │  Bank Loan: ₹50,000                      │
│ │  [Show Receipt] [Manual Redeem]          │
│ │                                           │
│ ├─ GLD-0002: Ready for redemption          │
│ │  Business cash: ₹32,000 available        │
│ │  Bank Loan: ₹30,000                      │
│ │  [Redeem Now]                            │
│ │                                           │
│ └─ GLD-0003: Overdue by 2 days            │
│    Action Required! [Review] [Redeem]      │
│                                              │
│ ✅ REDEEMED (2)                             │
│ ├─ GLD-0004: Redeemed on 2025-11-10       │
│ └─ GLD-0005: Redeemed on 2025-11-12       │
│                                              │
└──────────────────────────────────────────────┘
```

---

## 🔌 Integration Points

### 1. **Receipt System Integration**
- When posting a receipt for a pledged-with-bank item
- Auto-detect bank pledge and offer redemption option
- Create bank redemption entry if user confirms
- Link receipt ID to bank redemption record

### 2. **Dashboard Integration**
- Show pledges "awaiting customer payment" with bank outstanding
- Show pledges "ready for business redemption" with cash available
- Show profit/loss if redeeming with gain/loss on valuation

### 3. **Reporting Integration**
- "Bank Pledges Summary": How much is outstanding with each bank
- "Cash Flow Report": Impact of bank pledges on liquidity
- "Profit/Loss Report": Gains/losses on pledge redemptions

---

## 🧪 Test Scenarios

### Test Case 1: Happy Path (Customer pays exactly bank loan)
1. Create pledge: ₹50,000
2. Transfer to bank: valuation ₹60,000, LTV 80%, bank gives ₹48,000
3. Create receipt: ₹50,000 (to cover bank loan + interest)
4. System auto-redeems from bank
5. Verify: Both settled, no manual steps needed ✓

### Test Case 2: Customer overpays (profit scenario)
1. Create pledge: ₹50,000
2. Transfer to bank: bank loan ₹48,000
3. Create receipt: ₹52,000
4. System redeems ₹48,000 to bank
5. Profit: ₹4,000 captured
6. Verify: Profit in income account ✓

### Test Case 3: Partial payments (multiple receipts)
1. Create pledge: ₹50,000, transfer to bank: ₹48,000
2. Receipt 1: ₹30,000 (partial, doesn't redeem bank)
3. Receipt 2: ₹25,000 (combined: ₹30k + ₹25k = ₹55k > ₹48k)
4. System auto-redeems on Receipt 2
5. Verify: Both receipts linked, bank redeemed ✓

### Test Case 4: Manual redemption (business pays, not customer)
1. Create pledge with bank: ₹50,000 loan
2. Business has cash, decides to pay bank directly
3. POST /bank-pledges/1/redeem (manual payment)
4. Bank redeemed, customer payment pending
5. Later: Receipt from customer (separate transaction)
6. Verify: Two independent transactions ✓

---

## 📝 Summary

This real-world scenario handles:
- ✅ Cash flow management through bank financing
- ✅ Multiple payment sources (customer + business)
- ✅ Automatic linking of receipts to bank redemptions
- ✅ Profit/loss tracking on pledge sales
- ✅ Flexible redemption strategies
- ✅ Complete audit trail
- ✅ Double-entry accounting throughout

The system supports both **automatic** and **manual** redemption strategies, allowing flexibility for different business situations!
