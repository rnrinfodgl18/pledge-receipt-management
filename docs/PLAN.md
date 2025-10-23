# 📋 Pledge Receipts & Payments System - DETAILED PLAN

## 🎯 Requirements Analysis

### User Requirements (Translated):
```
1. Two tables needed: PledgeReceipts and ReceiptItems
2. Multiple pledges can have one receipt (bulk payment)
3. One pledge can have multiple payments (partial payments)
4. Auto-COA transactions when receipt created
5. Complete financial tracking needed
```

---

## 📊 Table Designs

### Table 1: PLEDGE_RECEIPTS

```
Column Name          | Data Type    | Notes
─────────────────────┼──────────────┼─────────────────────────
receipt_id           | INT (PK)     | Auto-increment primary key
receipt_no           | VARCHAR(50)  | Unique receipt number (format: RCP-2025-0001)
company_id           | INT (FK)     | Which company (from Company table)
customer_id          | INT (FK)     | Customer making payment (can be NULL for mixed)
receipt_date         | DATE         | Date receipt created
receipt_amount       | DECIMAL(15,2)| Total amount in receipt
payment_mode         | ENUM         | Values: Cash, Bank, Check, Digital, Card, Other
bank_name            | VARCHAR(100) | If payment_mode = Bank
check_number         | VARCHAR(50)  | If payment_mode = Check
transaction_id       | VARCHAR(100) | For digital/online payments
remarks              | TEXT         | Additional notes
receipt_status       | ENUM         | Active, Void, Adjusted, Cancelled
created_by           | INT (FK)     | User who created (from User table)
created_at           | TIMESTAMP    | Auto-set by system
updated_at           | TIMESTAMP    | Auto-update on modification
updated_by           | INT (FK)     | User who last updated (nullable)
coa_entry_status     | ENUM         | Pending, Posted, Error (for COA tracking)
```

**Indexes Recommended:**
- receipt_no (UNIQUE)
- company_id, receipt_date (for filtering)
- customer_id (for customer history)
- created_date (for report generation)

---

### Table 2: RECEIPT_ITEMS

```
Column Name          | Data Type    | Notes
─────────────────────┼──────────────┼─────────────────────────
receipt_item_id      | INT (PK)     | Auto-increment primary key
receipt_id           | INT (FK)     | Links to PledgeReceipts
pledge_id            | INT (FK)     | Which pledge this payment is for
principal_amount     | DECIMAL(15,2)| Original loan amount (info/reference)
interest_amount      | DECIMAL(15,2)| Interest due (calculated/info)
discount_interest    | DECIMAL(15,2)| Interest discount given (if any)
additional_penalty   | DECIMAL(15,2)| Extra penalty/charges (if any)
paid_principal       | DECIMAL(15,2)| Principal amount being paid NOW
paid_interest        | DECIMAL(15,2)| Interest amount being paid NOW
paid_penalty         | DECIMAL(15,2)| Penalty amount being paid NOW
paid_discount        | DECIMAL(15,2)| Discount being applied
payment_type         | ENUM         | Partial (partial payment), Full (complete), Extension
total_amount_paid    | DECIMAL(15,2)| Sum of all paid amounts (paid_principal + paid_interest + paid_penalty - paid_discount)
notes                | TEXT         | Item-specific notes
created_at           | TIMESTAMP    | Auto-set by system
created_by           | INT (FK)     | User who created
```

**Indexes Recommended:**
- receipt_id (for getting items of a receipt)
- pledge_id (for pledge payment history)

---

## 🔄 Relationships & Data Flow

```
┌─────────────────────────────────────────────────────┐
│ SCENARIO 1: Multiple Pledges → One Receipt          │
└─────────────────────────────────────────────────────┘

Customer comes with payments for 3 different pledges:

  Pledge 1 (GLD-2025-0001): ₹2,000 principal + ₹500 interest
  Pledge 2 (GLD-2025-0002): ₹5,000 principal + ₹1,250 interest
  Pledge 3 (SLV-2025-0001): ₹3,000 principal + ₹600 interest
  
  Receipt Created:
  
    PledgeReceipts:
      receipt_no: RCP-2025-0001
      customer_id: 5
      receipt_date: 2025-01-23
      receipt_amount: 12,350 (total)
      payment_mode: Cash
      
    ReceiptItems:
      Item 1: receipt_id=1, pledge_id=42, paid_principal=2000, paid_interest=500
      Item 2: receipt_id=1, pledge_id=43, paid_principal=5000, paid_interest=1250
      Item 3: receipt_id=1, pledge_id=44, paid_principal=3000, paid_interest=600

┌─────────────────────────────────────────────────────┐
│ SCENARIO 2: One Pledge → Multiple Payments          │
└─────────────────────────────────────────────────────┘

Customer pays same pledge in 3 installments:

  Receipt 1 (RCP-2025-0001):
    - Pledge GLD-2025-0001
    - Paid: ₹2,000 principal (partial)
    - Status: Partial payment
    
  Receipt 2 (RCP-2025-0002):
    - Pledge GLD-2025-0001
    - Paid: ₹2,000 principal + ₹500 interest (partial)
    - Status: Partial payment
    
  Receipt 3 (RCP-2025-0003):
    - Pledge GLD-2025-0001
    - Paid: Full balance (full close)
    - Status: Full payment → Pledge status changes to "Redeemed"

┌─────────────────────────────────────────────────────┐
│ SCENARIO 3: Partial with Discount & Penalty        │
└─────────────────────────────────────────────────────┘

  ReceiptItems:
    principal_amount: 10,000 (what was owed)
    interest_amount: 2,500 (normal interest)
    discount_interest: -500 (discount given)
    additional_penalty: 100 (late payment penalty)
    
    paid_principal: 8,000 (paying partial principal)
    paid_interest: 2,000 (paying partial interest)
    paid_discount: 500 (applying discount)
    paid_penalty: 100 (paying penalty)
    
    total_amount_paid: 8,000 + 2,000 + 100 - 500 = 9,600
    
    remaining_principal: 2,000 (10,000 - 8,000)
    remaining_interest: 500 (2,500 - 2,000)
```

---

## 💰 COA Transactions (Automatic)

### When Receipt is Created/Posted:

```
SCENARIO: Payment of ₹10,600 (₹8,000 principal + ₹2,600 interest)

Automatic COA Entries:

1. DR: Cash (1000)                    ₹10,600
   CR: Loan Given to Customer (1051xxxx)  ₹8,000
   CR: Interest Income (4000)         ₹2,600
   
   Purpose: Record cash received and reduce customer receivables

2. IF FULL PAYMENT (Pledge redeemed):
   
   DR: Pledged Items (1040)           ₹0 (or cost of items)
   CR: Gold Sales Income (4010)       ₹[item_value]
   
   Purpose: Release pledged items from inventory

3. IF THERE'S DISCOUNT:
   
   DR: Interest Discount Expense (5030)   ₹500
   CR: Interest Income (4000)             ₹500
   
   Purpose: Record discount given

4. IF THERE'S PENALTY:
   
   DR: Cash (1000)                    ₹100
   CR: Additional Income (4050)        ₹100
   
   Purpose: Record penalty/late charges collected

RUNNING BALANCE:
   All affected accounts updated:
   - Cash (1000) increased
   - Receivable (1051xxxx) decreased
   - Interest Income (4000) increased
   - Running balance recalculated
```

---

## 📋 Additional Fields We Should Add

### To PLEDGE_RECEIPTS:

```
receipt_status      | ENUM
  ├─ Draft (not yet confirmed)
  ├─ Posted (confirmed, ledger entries created)
  ├─ Void (cancelled but record kept)
  ├─ Adjusted (receipt adjusted/modified)
  └─ Cancelled (fully cancelled)

coa_entry_status    | ENUM
  ├─ Pending (awaiting COA entry creation)
  ├─ Posted (COA entries created successfully)
  ├─ Error (failed to create COA entries)
  └─ Manual (manually adjusted)

reference_doc_id    | VARCHAR (for checks, transaction IDs)
gst_amount          | DECIMAL (if GST applicable)
net_amount          | DECIMAL (after GST/taxes)
```

### To RECEIPT_ITEMS:

```
receipt_item_status  | ENUM
  ├─ Pending
  ├─ Applied
  └─ Error

pledge_remaining_principal  | DECIMAL (after this payment)
pledge_remaining_interest   | DECIMAL (after this payment)
calculated_by_id            | INT (user who calculated amounts)
approved_by_id              | INT (user who approved - nullable)
```

---

## 🔗 Database Relationships

```
Company (1)
  └─ PledgeReceipts (many)
      └─ ReceiptItems (many)
          └─ Pledge (1)
      └─ Customer (1) [customer_id - nullable for mixed]
      └─ User (1) [created_by]
      
Pledge (1)
  └─ ReceiptItems (many) [payment history]
  
ChartOfAccounts (1)
  └─ LedgerEntries (many) [from receipt COA creation]
```

---

## 🎯 Key Business Logic

### 1. Receipt Number Generation
```
Format: RCP-{YEAR}-{SEQUENCE}
Example: RCP-2025-0001, RCP-2025-0002, ...

Auto-increment per year
Unique across company
```

### 2. Amount Calculations
```
For each receipt item:
  total_amount_paid = paid_principal + paid_interest + paid_penalty - paid_discount

Receipt total:
  receipt_amount = SUM(all receipt_items.total_amount_paid)
```

### 3. Pledge Balance Tracking
```
After payment:
  pledge_remaining_principal = previous_principal - paid_principal
  pledge_remaining_interest = previous_interest - paid_interest
  
If remaining_principal == 0 AND remaining_interest == 0:
  payment_type = "Full Close"
  Pledge status changes to "Redeemed"
  
Otherwise:
  payment_type = "Partial"
  Pledge status remains "Active"
```

### 4. COA Posting Rules
```
Receipt can only post once (coa_entry_status = Posted)
If post fails → coa_entry_status = Error
Can be retried or manually adjusted
All transactions recorded with reference_type = "Receipt"
reference_id = receipt_id
```

---

## 📊 Validation Rules

### Receipt Creation Validation:
```
✓ company_id exists
✓ payment_mode is valid
✓ At least one receipt_item
✓ Total receipt_amount matches sum of items
✓ All referenced pledges exist and active
✓ payment_mode = Bank → bank_name required
✓ payment_mode = Check → check_number required
✓ payment_mode = Digital → transaction_id required
```

### Receipt Item Validation:
```
✓ pledge_id exists and belongs to same company
✓ paid_principal <= pledge_remaining_principal
✓ paid_interest <= pledge_remaining_interest + accrued_interest
✓ total_amount_paid > 0
✓ paid_principal + paid_interest + paid_penalty - paid_discount = total_amount_paid
✓ discount_interest <= interest_amount
✓ If payment_type = "Full", remaining amounts should be 0
```

---

## 🔄 Receipt Status Workflow

```
DRAFT
  ├─ Can edit receipt and items
  ├─ No COA entries created
  └─ No ledger impact
       ↓
POSTED
  ├─ COA entries created
  ├─ Ledger entries created
  ├─ Cash/Receivable accounts updated
  ├─ Cannot edit (must void and create new)
  └─ If full payment → Pledge status changes
       ↓
VOID (Optional)
  ├─ Receipt cancelled
  ├─ COA entries REVERSED
  ├─ Pledge resets to previous state
  └─ Kept for audit trail
       ↓
ADJUSTED
  ├─ Receipt modified after posting
  ├─ Previous COA entries reversed
  ├─ New COA entries created
  └─ Kept for audit trail
```

---

## 🧪 Testing Scenarios

### Test 1: Simple Payment
```
Pledge: GLD-2025-0001, ₹10,000 principal + ₹2,500 interest
Payment: ₹5,000 principal + ₹1,250 interest
Expected:
  - Receipt created with RCP-2025-0001
  - ReceiptItem created
  - 2 COA entries: DR Cash, CR Receivable + Interest
  - Pledge remains Active (partial)
  - Remaining balance: ₹5,000 + ₹1,250
```

### Test 2: Multiple Pledges, One Receipt
```
3 pledges, 3 payments in one receipt
Expected:
  - Receipt with 3 ReceiptItems
  - Total amount = sum of all 3 items
  - 3 pairs of COA entries (one for each pledge)
  - Each pledge updated with remaining balance
```

### Test 3: Full Closure
```
Pledge GLD-2025-0001: ₹10,000 + ₹2,500 interest
Payment: Full amount ₹12,500
Expected:
  - payment_type = "Full Close"
  - Pledge status changes to "Redeemed"
  - Remaining balances = 0
  - COA: Release pledged items entry
```

### Test 4: With Discount & Penalty
```
Payment with:
  - Interest discount: ₹500
  - Late penalty: ₹100
Expected:
  - Discount recorded (COA entry)
  - Penalty recorded (COA entry)
  - Correct total calculation
  - All COA entries created
```

### Test 5: Receipt Void
```
Previously posted receipt voided
Expected:
  - Receipt status = Void
  - Previous COA entries reversed
  - Cash/Receivable back to previous state
  - Pledge balance restored
  - Audit trail maintained
```

---

## 🔐 Security & Authorization

```
✓ Only users in same company can create receipts
✓ Admin role can void/adjust receipts
✓ created_by tracks who created receipt
✓ updated_by tracks who last updated
✓ All changes logged in audit trail
✓ COA posting automatic (internal system)
```

---

## 📝 Data Integrity Checks

```
✓ Foreign key constraints: company_id, customer_id, pledge_id, created_by
✓ Check constraint: receipt_amount = SUM(receipt_items.total_amount_paid)
✓ Check constraint: paid amounts >= 0
✓ Unique constraint: receipt_no per company per year
✓ NOT NULL constraints: receipt_no, receipt_date, receipt_amount, payment_mode, company_id, created_by
✓ Decimal precision: 15,2 (for currency amounts)
```

---

## 📊 Reporting Needs

```
Reports that will need these tables:

1. Receipt Register
   - Date range filter
   - Payment mode breakdown
   - Customer-wise receipts

2. Outstanding Balance Report
   - Remaining principal & interest
   - Customer-wise summary

3. Collection Report
   - Daily/monthly collections
   - By payment mode
   - By pledge/scheme

4. COA Reconciliation Report
   - Receipts vs COA entries
   - Discrepancies identified
   - Manual adjustments tracking

5. Customer Payment History
   - All receipts for a customer
   - Pledge-wise payment timeline
   - Outstanding balance
```

---

## ✅ Complete Field Checklist

### PLEDGE_RECEIPTS (17 fields):
```
✓ receipt_id (PK)
✓ receipt_no (Unique)
✓ company_id (FK)
✓ customer_id (FK, nullable for mixed)
✓ receipt_date
✓ receipt_amount
✓ payment_mode
✓ bank_name (nullable)
✓ check_number (nullable)
✓ transaction_id (nullable)
✓ remarks
✓ receipt_status
✓ created_by (FK)
✓ created_at
✓ updated_at
✓ updated_by (FK, nullable)
✓ coa_entry_status
```

### RECEIPT_ITEMS (14 fields):
```
✓ receipt_item_id (PK)
✓ receipt_id (FK)
✓ pledge_id (FK)
✓ principal_amount
✓ interest_amount
✓ discount_interest
✓ additional_penalty
✓ paid_principal
✓ paid_interest
✓ paid_penalty
✓ paid_discount
✓ payment_type
✓ total_amount_paid
✓ notes
```

---

## 🎯 What's Included in This Plan

✅ Two complete table designs with all fields  
✅ Data types and constraints  
✅ Relationships and foreign keys  
✅ Receipt number generation logic  
✅ COA transaction mapping  
✅ Business logic rules  
✅ Validation requirements  
✅ Status workflow  
✅ 5 testing scenarios  
✅ Security and authorization  
✅ Data integrity checks  
✅ Reporting requirements  

---

## ⚠️ Notes & Considerations

1. **Receipt Number Format:** Should we reset yearly or continuous?
   - Current plan: RCP-2025-0001 (yearly reset)
   - Alternative: RCP-00001 (continuous)

2. **Customer ID:** Should be nullable for cases where customer is unknown?
   - Current plan: nullable (allows mixed/unknown payments)
   - Alternative: Always required

3. **Payment Mode:** Do we need additional modes?
   - Current: Cash, Bank, Check, Digital, Card, Other
   - Add: Mobile Wallet, Crypto, etc.?

4. **COA Entry Reversal:** On void/adjust?
   - Current plan: YES (reversal entries created)
   - This keeps ledger balanced

5. **Approval Workflow:** Do receipts need approval?
   - Current plan: Simple (post directly)
   - Alternative: Draft → Approve → Post workflow

6. **GST/Taxes:** Should we track?
   - Current plan: Added optional fields (gst_amount, net_amount)

7. **Auto-COA Posting:** When?
   - Current plan: Immediately when receipt posted
   - Alternative: Batch posting at end of day

---

## 🚀 Implementation Priority

**Phase 1 (Core):**
- PledgeReceipts table
- ReceiptItems table
- Basic CRUD operations

**Phase 2 (Integration):**
- Auto-COA transaction creation
- Receipt number generation
- Validation rules

**Phase 3 (Enhancement):**
- Receipt void/adjust functionality
- Advanced reporting
- Batch operations

---

This plan is comprehensive and ready for implementation!

**Would you like me to proceed with creating these tables and the complete system?**
