# Pledge to Bank & Redeem from Bank Workflow

## 📋 Overview

This document explains how pawn shop pledges are transferred to banks for financing, and how they are redeemed back. This is a common practice where pawn shops use their pledge inventory as collateral to get loans from banks.

### Key Concepts:
1. **Pledge to Bank**: Transfer a pledge to a bank with LTV (Loan-to-Value) calculation
2. **Redeem from Bank**: Get the pledge back by paying the bank amount (may differ from original loan amount)
3. **Automatic Ledger Integration**: Track financial impact on Chart of Accounts
4. **Status Management**: Track pledge location (shop, bank, redeemed)

---

## 🔄 Workflow Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                    PLEDGE LIFECYCLE WITH BANK                    │
└─────────────────────────────────────────────────────────────────┘

STATE 1: ACTIVE PLEDGE (In Pawn Shop)
┌─────────────────────────────────────┐
│ Pledge #5                           │
│ ├─ Customer: Ravi Kumar             │
│ ├─ Items: 2 Gold Bangles (10g each) │
│ ├─ Loan Amount: ₹50,000             │
│ ├─ Status: Active                   │
│ └─ Location: SHOP ✓                 │
└─────────────────────────────────────┘
         ↓
    SCENARIO A: TRANSFER TO BANK
    (Customer wants to extend payment)
         ↓

STATE 2: BANK PLEDGE (With Bank)
┌──────────────────────────────────────────────┐
│ BankPledge #1                                │
│ ├─ Original Pledge: #5                       │
│ ├─ Transfer Date: 2025-10-24                 │
│ ├─ Bank: HDFC Bank                           │
│ ├─ Account: 12345xxxxx                       │
│ ├─ Gross Weight: 20g                         │
│ ├─ Valuation: ₹60,000                        │
│ ├─ LTV (Loan-to-Value): 80%                  │
│ ├─ Bank Loan Amount: ₹48,000                 │
│ ├─ Original Pawn Shop Loan: ₹50,000          │
│ ├─ Outstanding Interest: ₹2,500              │
│ ├─ Status: WITH_BANK ✓                       │
│ ├─ Location: BANK                            │
│ └─ Ledger Entries: Reversed receivable,      │
│                    Created bank asset        │
└──────────────────────────────────────────────┘
         ↓
    CUSTOMER PAYS BACK
    (Or Bank period expires)
         ↓

STATE 3: REDEEMED FROM BANK
┌─────────────────────────────────────────────────┐
│ BankRedemption #1                               │
│ ├─ BankPledge: #1                               │
│ ├─ Redemption Date: 2025-11-24                  │
│ ├─ Amount Paid to Bank: ₹48,000                 │
│ ├─ Price Difference: ₹2,000 gain                │
│ │  (Bank valuation was ₹60k, actual sold at)    │
│ ├─ Interest Recovered: ₹2,500                   │
│ ├─ Net Cash In: ₹4,500                          │
│ ├─ Status: REDEEMED ✓                           │
│ └─ Ledger Entries: Reversed bank asset,         │
│                    Restored receivable or       │
│                    Created income account       │
└─────────────────────────────────────────────────┘
         ↓
    PLEDGE BACK TO SHOP
    (Available for fresh transaction)
         ↓

STATE 4: ACTIVE PLEDGE (Back in Shop)
┌──────────────────────────────────────────┐
│ Pledge #5 (Status: Redeemed)             │
│ ├─ Can be re-used for new pledge        │
│ └─ Or moved to archive                   │
└──────────────────────────────────────────┘
```

---

## 💾 Database Schema

### New Models Required:

#### 1. **BankPledge** Model
Transfer of a pledge to a bank for financing

```python
class BankPledge(Base):
    """Bank Pledge model - stores pledges transferred to banks."""
    __tablename__ = "bank_pledges"

    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False, index=True)
    pledge_id = Column(Integer, ForeignKey("pledges.id"), nullable=False, index=True)
    bank_details_id = Column(Integer, ForeignKey("bank_details.id"), nullable=False, index=True)
    
    # Transfer details
    transfer_date = Column(DateTime, nullable=False, index=True)
    gross_weight = Column(Float, nullable=False)  # Weight of items sent to bank
    net_weight = Column(Float, nullable=False)
    
    # Valuation & LTV
    valuation_amount = Column(Float, nullable=False)  # Bank's valuation
    ltv_percentage = Column(Float, nullable=False, default=80.0)  # Loan-to-Value %
    bank_loan_amount = Column(Float, nullable=False)  # Amount bank gives
    original_shop_loan = Column(Float, nullable=False)  # Original pawn shop loan
    outstanding_interest = Column(Float, nullable=False, default=0.0)  # Interest at transfer time
    
    # Bank account for tracking
    bank_account_id = Column(Integer, ForeignKey("chart_of_accounts.id"), nullable=True)
    
    # Status & metadata
    status = Column(String, default="WITH_BANK")  # WITH_BANK, REDEEMED, EXPIRED, FORECLOSED
    bank_reference_no = Column(String, nullable=True, unique=True)  # Bank's reference number
    remarks = Column(String, nullable=True)
    
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
```

#### 2. **BankPledgeItems** Model
Individual items in a bank pledge (for audit trail)

```python
class BankPledgeItems(Base):
    """Bank Pledge Items model - audit trail of items sent to bank."""
    __tablename__ = "bank_pledge_items"

    id = Column(Integer, primary_key=True, index=True)
    bank_pledge_id = Column(Integer, ForeignKey("bank_pledges.id"), nullable=False, index=True)
    original_item_id = Column(Integer, ForeignKey("pledge_items.id"), nullable=False, index=True)
    
    jewel_design = Column(String, nullable=True)
    jewel_condition = Column(String, nullable=True)
    stone_type = Column(String, nullable=True)
    gross_weight = Column(Float, nullable=False)
    net_weight = Column(Float, nullable=False)
    quantity = Column(Integer, default=1)
    
    created_at = Column(DateTime, server_default=func.now())
```

#### 3. **BankRedemption** Model
Redemption of a pledge from the bank

```python
class BankRedemption(Base):
    """Bank Redemption model - stores redemption of pledges from banks."""
    __tablename__ = "bank_redemptions"

    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False, index=True)
    bank_pledge_id = Column(Integer, ForeignKey("bank_pledges.id"), nullable=False, index=True)
    
    # Redemption details
    redemption_date = Column(DateTime, nullable=False, index=True)
    amount_paid_to_bank = Column(Float, nullable=False)  # Principal paid to bank
    interest_on_bank_loan = Column(Float, nullable=False, default=0.0)  # Interest accrued at bank
    bank_charges = Column(Float, nullable=False, default=0.0)  # Bank's charges
    
    # Price & Gain/Loss calculation
    bank_valuation = Column(Float, nullable=False)  # Original bank valuation
    actual_redemption_value = Column(Float, nullable=False)  # What we actually paid/got
    price_difference = Column(Float, nullable=False)  # Gain (+) or Loss (-)
    
    # Interest tracking
    original_shop_interest = Column(Float, nullable=False, default=0.0)  # Original interest
    interest_recovered = Column(Float, nullable=False, default=0.0)  # Interest received
    
    # Status & reference
    status = Column(String, default="REDEEMED")  # REDEEMED, PARTIAL, FORECLOSED
    redemption_account_id = Column(Integer, ForeignKey("chart_of_accounts.id"), nullable=True)
    
    remarks = Column(String, nullable=True)
    reference_document = Column(String, nullable=True)  # PDF/image of bank receipt
    
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
```

---

## 📊 API Endpoints

### 1. **Transfer Pledge to Bank**
```http
POST /bank-pledges/transfer
Content-Type: application/json
Authorization: Bearer {token}

{
  "pledge_id": 5,
  "bank_details_id": 2,
  "transfer_date": "2025-10-24",
  "gross_weight": 20.0,
  "net_weight": 18.5,
  "valuation_amount": 60000.0,
  "ltv_percentage": 80.0,
  "bank_reference_no": "HDFC/2025/1234",
  "remarks": "Extended financing"
}

RESPONSE (201 Created):
{
  "id": 1,
  "pledge_id": 5,
  "pledge_no": "GLD-2025-0001",
  "bank_name": "HDFC Bank",
  "bank_loan_amount": 48000.0,
  "original_shop_loan": 50000.0,
  "outstanding_interest": 2500.0,
  "valuation_amount": 60000.0,
  "ltv_percentage": 80.0,
  "status": "WITH_BANK",
  "transfer_date": "2025-10-24T00:00:00",
  "created_at": "2025-10-24T10:30:00",
  "ledger_entries": {
    "reversed_receivable": 52500.0,
    "created_bank_asset": 48000.0,
    "interest_income": 2500.0
  }
}
```

### 2. **Get All Bank Pledges**
```http
GET /bank-pledges?company_id=1&status=WITH_BANK
Authorization: Bearer {token}

RESPONSE:
{
  "total": 5,
  "items": [
    {
      "id": 1,
      "pledge_no": "GLD-2025-0001",
      "customer_name": "Ravi Kumar",
      "bank_name": "HDFC Bank",
      "bank_loan_amount": 48000.0,
      "valuation_amount": 60000.0,
      "status": "WITH_BANK",
      "transfer_date": "2025-10-24",
      "ltv_percentage": 80.0
    }
  ]
}
```

### 3. **Get Bank Pledge Details**
```http
GET /bank-pledges/1
Authorization: Bearer {token}

RESPONSE:
{
  "id": 1,
  "pledge_id": 5,
  "pledge_no": "GLD-2025-0001",
  "customer": {
    "id": 1,
    "name": "Ravi Kumar",
    "mobile": "9876543210"
  },
  "bank": {
    "id": 2,
    "name": "HDFC Bank",
    "account_number": "12345xxxxx",
    "ifsc_code": "HDFC0001234"
  },
  "transfer_details": {
    "transfer_date": "2025-10-24",
    "gross_weight": 20.0,
    "net_weight": 18.5,
    "items": [
      {
        "jewel_design": "Bangle",
        "condition": "Good",
        "gross_weight": 10.0,
        "net_weight": 9.2
      }
    ]
  },
  "financial": {
    "bank_valuation": 60000.0,
    "ltv_percentage": 80.0,
    "bank_loan_amount": 48000.0,
    "original_shop_loan": 50000.0,
    "outstanding_interest": 2500.0
  },
  "status": "WITH_BANK",
  "created_at": "2025-10-24T10:30:00"
}
```

### 4. **Redeem Pledge from Bank**
```http
POST /bank-pledges/1/redeem
Content-Type: application/json
Authorization: Bearer {token}

{
  "redemption_date": "2025-11-24",
  "amount_paid_to_bank": 48000.0,
  "interest_on_bank_loan": 1200.0,
  "bank_charges": 300.0,
  "actual_redemption_value": 49500.0,
  "interest_recovered": 2500.0,
  "remarks": "Pledged item sold at higher price"
}

RESPONSE (201 Created):
{
  "id": 1,
  "bank_pledge_id": 1,
  "pledge_no": "GLD-2025-0001",
  "redemption_date": "2025-11-24",
  "amount_paid_to_bank": 48000.0,
  "interest_on_bank_loan": 1200.0,
  "bank_charges": 300.0,
  "price_difference": 2000.0,
  "interest_recovered": 2500.0,
  "net_cash_in": 4500.0,
  "status": "REDEEMED",
  "created_at": "2025-11-24T15:00:00",
  "ledger_entries": {
    "reversed_bank_asset": 48000.0,
    "created_bank_expense": 1500.0,
    "created_income": 2000.0,
    "restored_receivable": 50000.0,
    "interest_income": 2500.0
  }
}
```

### 5. **Cancel Bank Pledge (Void)**
```http
POST /bank-pledges/1/cancel
Authorization: Bearer {token}

{
  "reason": "Bank returned pledge early",
  "return_date": "2025-10-28"
}

RESPONSE:
{
  "id": 1,
  "status": "CANCELLED",
  "reason": "Bank returned pledge early",
  "reversal_entries": 3
}
```

---

## 💰 Accounting Journal Entries

### A. Pledge to Bank Transfer
When transferring pledge to bank, we reverse the original receivable and create a bank asset.

**Original Pledge (Active):**
- DR: Jewel Inventory (1500) = ₹50,000 ← Assets (Inventory)
- CR: Customer Receivable (1051) = ₹50,000 ← Liabilities

**After Transfer to Bank:**

1. **Reverse Original Receivable & Interest:**
   - DR: Customer Receivable (1051) = ₹50,000
   - DR: Interest Receivable (1052) = ₹2,500
   - CR: Jewel Inventory (1500) = ₹52,500

2. **Create Bank Asset (What bank gives us):**
   - DR: Bank Asset Account (2100) = ₹48,000 ← New asset: amount from bank
   - CR: Bank Loan Payable (2200) = ₹48,000 ← Liability: amount to repay to bank

**Net Effect:**
- Jewel Inventory reduced: from ₹50k to ₹0 (transferred to bank)
- Bank Asset created: ₹48,000 (financing from bank)
- Bank Loan Liability created: ₹48,000 (obligation to bank)
- Cash received from bank: ₹48,000 (improves liquidity)

### B. Redemption from Bank
When redeeming pledge from bank:

**Redemption Scenario:** Bank loan ₹48,000 + Interest ₹1,200 = Total ₹49,200 paid

```
IF Pledge Sold at Higher Price:
   Bank Valuation: ₹60,000
   Actual Sale Price: ₹62,000
   Gain: ₹2,000

Journal Entries:
1. DR: Bank Loan Payable (2200) = ₹48,000
   DR: Bank Interest Expense (5300) = ₹1,200
   CR: Cash (1000) = ₹49,200 ← Pay to bank

2. DR: Cash (1000) = ₹62,000 ← Receive from sale
   CR: Sale Income (4100) = ₹62,000

3. DR: Customer Receivable (1051) = ₹50,000 ← Restore original
   CR: Sale Income (4100) = ₹50,000 ← Reduce sale income to net amount

4. DR: Interest Income (4000) = ₹2,500
   CR: Interest Receivable (1052) = ₹2,500 ← Record interest earned
```

**Final Result:**
- Bank Loan repaid: ₹48,000 ✓
- Net Gain on sale: ₹2,000 ✓
- Interest income: ₹2,500 ✓
- Pledge status: REDEEMED ✓

---

## 🔐 Status Flows

```
┌─────────────────────────────────────────────────────────┐
│                   PLEDGE STATUS FLOW                     │
└─────────────────────────────────────────────────────────┘

ACTIVE
  ├─→ WITH_BANK (via transfer endpoint) → can redeem
  ├─→ REDEEMED (via receipt payment) → pledge closed
  └─→ FORFEITED (if not paid) → pledge closed

WITH_BANK
  ├─→ REDEEMED (via redemption endpoint) → back to shop
  ├─→ EXPIRED (if bank period expires)
  └─→ FORECLOSED (if bank sells the pledge)

REDEEMED/EXPIRED/FORECLOSED
  └─→ Can optionally create new pledge (fresh transaction)


BankPledge Status Flow:
─────────────────────

WITH_BANK (initial)
  ├─→ REDEEMED (redemption successful)
  ├─→ EXPIRED (bank holding period ended)
  ├─→ PARTIAL (partial redemption)
  └─→ FORECLOSED (bank sold the pledge)

REDEEMED/EXPIRED/FORECLOSED
  └─→ Terminal states (no further transitions)
```

---

## 🛡️ Business Rules & Validations

### 1. **Pledge to Bank Rules:**
- ✅ Pledge must be in "Active" status
- ✅ Pledge must have at least 1 week of payment history or be current
- ✅ LTV must be between 50% and 95%
- ✅ Bank loan amount = Valuation × LTV%
- ✅ Bank must have valid account details
- ✅ Cannot transfer if already with another bank

### 2. **Redemption Rules:**
- ✅ BankPledge must be in "WITH_BANK" status
- ✅ Amount paid to bank must be >= bank_loan_amount
- ✅ Redemption date must be after transfer date
- ✅ If price difference is negative, it's a loss (tracked separately)
- ✅ Interest cannot exceed 50% of original loan amount

### 3. **Financial Validations:**
- ✅ All ledger entries must balance (Debit = Credit)
- ✅ Customer receivable must match pledge status
- ✅ Bank asset must exist only if status is WITH_BANK
- ✅ No negative amounts allowed
- ✅ Running balance maintained for all accounts

---

## 🔄 Ledger Integration Functions

### Function: `create_bank_pledge_ledger_entries()`
Creates ledger entries when pledge is transferred to bank.

```python
def create_bank_pledge_ledger_entries(
    db: Session,
    bank_pledge: BankPledge,
    created_by: int,
    company_id: int
) -> dict:
    """
    Creates accounting entries for pledge-to-bank transfer.
    
    Entries created:
    1. DR: Customer Receivable (reverse) → CR: Jewel Inventory
    2. DR: Bank Asset (new) → CR: Bank Loan Payable (new)
    
    Returns: {
        "entries_created": count,
        "total_debits": amount,
        "total_credits": amount,
        "status": "success/error"
    }
    """
```

### Function: `reverse_bank_pledge_ledger_entries()`
Reverses entries when bank pledge is voided.

```python
def reverse_bank_pledge_ledger_entries(
    db: Session,
    bank_pledge: BankPledge,
    created_by: int
) -> dict:
    """
    Reverses all ledger entries for a bank pledge transfer.
    
    Creates reversing entries for all original entries.
    Maintains audit trail.
    
    Returns: {
        "reversed_entries": count,
        "status": "success/error"
    }
    """
```

### Function: `create_bank_redemption_ledger_entries()`
Creates entries when pledge is redeemed from bank.

```python
def create_bank_redemption_ledger_entries(
    db: Session,
    redemption: BankRedemption,
    created_by: int,
    company_id: int
) -> dict:
    """
    Creates accounting entries for bank redemption.
    
    Entries created:
    1. DR: Bank Loan Payable → CR: Cash (pay back to bank)
    2. DR: Bank Interest Expense → CR: Cash (pay interest)
    3. DR: Cash → CR: Gain/Loss Account (if price difference)
    4. Optionally: Restore original receivable if continuing
    
    Returns: {
        "entries_created": count,
        "status": "success/error"
    }
    """
```

---

## 📝 Implementation Checklist

- [ ] Add models: `BankPledge`, `BankPledgeItems`, `BankRedemption` to `app/models.py`
- [ ] Create schemas in `app/schemas.py`:
  - `PledgeToBankRequest`, `PledgeToBankResponse`
  - `BankRedemptionRequest`, `BankRedemptionResponse`
  - `BankPledgeList`
- [ ] Create `app/routes/bank_pledges.py` with 5 endpoints
- [ ] Create `app/bank_pledge_utils.py` with ledger integration functions
- [ ] Update `app/schemas.py` to include bank pledge/redemption schemas
- [ ] Test all endpoints with Postman/Swagger
- [ ] Verify ledger entries balance
- [ ] Test error scenarios (invalid status, invalid LTV, etc.)
- [ ] Commit to GitHub with detailed messages

---

## 🧪 Test Scenarios

### Scenario 1: Happy Path (Pledge to Bank → Redeem)
1. Create active pledge with ₹50,000 loan
2. Transfer to bank: valuation ₹60,000, LTV 80%, bank gives ₹48,000
3. Verify: Original receivable reversed, bank asset created
4. Redeem from bank: Pay ₹48,000 + ₹1,200 interest
5. Verify: Pledge status changes to REDEEMED, bank asset closed

### Scenario 2: Gain on Redemption
1. Same setup as Scenario 1
2. Item sold at ₹62,000 (vs bank valuation ₹60,000)
3. Gain of ₹2,000 recorded as income
4. Verify: Net cash impact correctly calculated

### Scenario 3: Loss on Redemption
1. Pledge: ₹50,000 loan on ₹70,000 gold
2. Transfer to bank: valuation ₹70,000, bank gives ₹56,000
3. Item can only be sold at ₹65,000 (market drop)
4. Loss of ₹5,000 recorded
5. Verify: Loss correctly reflects in P&L

### Scenario 4: Cancel Bank Pledge
1. Transfer pledge to bank
2. Cancel/void the transfer before redemption
3. Verify: All entries reversed, original pledge status restored

### Scenario 5: Multiple Bank Pledges
1. Create 3 pledges, transfer all to same bank
2. Verify: Each creates separate entries
3. Redeem 2, keep 1 with bank
4. Verify: Selective redemption works

---

## 🔗 Integration Points

1. **With Pledge System:**
   - Link `BankPledge` to original `Pledge` via foreign key
   - Update `Pledge.status` to "WITH_BANK" when transferred
   - Allow status transition: Active → WITH_BANK → REDEEMED

2. **With Chart of Accounts:**
   - Need accounts: "Bank Pledges Asset" (2100)
   - Need accounts: "Bank Pledges Payable" (2200)
   - Need accounts: "Bank Interest Expense" (5300)
   - Need accounts: "Pledge Gain/Loss" (4200)

3. **With Customer Management:**
   - Display which pledges are with banks
   - Show customer's total exposure (shop + bank)

4. **With Receipt System:**
   - Option to pay bank pledge directly (not via receipt)
   - Or create special "Bank Redemption" receipt type

---

## 📱 Frontend Integration Notes

### Bank Pledge Transfer Screen:
```
┌────────────────────────────────────────┐
│ Transfer Pledge to Bank                │
├────────────────────────────────────────┤
│ Select Pledge:    [Dropdown GLD-...]   │
│ Select Bank:      [Dropdown HDFC...]   │
│ Valuation:        [₹ 60,000]           │
│ LTV %:            [80%] (auto calc)    │
│ Bank Loan:        ₹48,000 (auto)       │
│ Bank Ref No:      [HDFC/2025/...]      │
│ Transfer Date:    [2025-10-24]         │
│                                        │
│ [Preview Entries] [Cancel] [Transfer]  │
└────────────────────────────────────────┘
```

### Bank Pledge List Screen:
```
┌──────────────────────────────────────────────┐
│ Bank Pledges                                 │
├────────────┬──────────┬────────┬────────────┤
│ Pledge No  │ Bank     │ Amount │ Status     │
├────────────┼──────────┼────────┼────────────┤
│ GLD-0001   │ HDFC     │ 48,000 │ WITH_BANK  │
│ GLD-0002   │ AXIS     │ 32,000 │ REDEEMED   │
│ GLD-0003   │ ICICI    │ 55,000 │ WITH_BANK  │
│                                             │
│ [View] [Redeem] [Cancel]                   │
└──────────────────────────────────────────────┘
```

### Bank Redemption Screen:
```
┌────────────────────────────────────────┐
│ Redeem Pledge from Bank                │
├────────────────────────────────────────┤
│ Pledge:           GLD-0001              │
│ Bank:             HDFC Bank             │
│ Bank Loan:        ₹48,000               │
│ Amount to Pay:    [₹ 48,000]            │
│ Interest:         [₹ 1,200]             │
│ Bank Charges:     [₹ 300]               │
│ Total to Bank:    ₹49,500 (auto)        │
│                                        │
│ Valuation:        ₹60,000               │
│ Actual Received:  [₹ 62,000]            │
│ Gain/Loss:        +₹2,000 (auto calc)   │
│                                        │
│ [Preview Entries] [Cancel] [Redeem]    │
└────────────────────────────────────────┘
```

---

## 🎯 Summary

This system provides:
- ✅ Complete pledge-to-bank workflow
- ✅ Automatic ledger integration
- ✅ Gain/loss tracking on redemption
- ✅ Multi-bank support
- ✅ Status tracking and audit trail
- ✅ Business rule validation
- ✅ REST API for integration

The workflow ensures complete financial transparency and maintains double-entry accounting principles throughout the pledge lifecycle.
