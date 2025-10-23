# 📋 PLEDGE RECEIPTS & PAYMENTS - QUICK VISUAL PLAN

## 🎯 The Problem We're Solving

```
CURRENT STATE:
  ✅ Pledges are created
  ✅ Automatic ledger entries made
  ❌ NO way to track receipts
  ❌ NO way to track payments
  ❌ NO way to handle partial payments
  ❌ NO way to issue receipts to customers

AFTER IMPLEMENTATION:
  ✅ Create pledges
  ✅ Issue receipts to customers (single or multiple pledges)
  ✅ Track payments (full or partial)
  ✅ Automatic ledger entries on payments
  ✅ Track remaining balance
  ✅ Handle multiple payments per pledge
```

---

## 📊 PROPOSED DATA MODEL

### Scenario A: Single Pledge → Single Receipt → One Payment

```
PLEDGE TABLE:
┌────────────────────────────┐
│ Pledge: GLD-2025-0001      │
│ Amount: ₹50,000            │
│ Interest: ₹1,250           │
│ Status: Active             │
└────────────────────────────┘
         │
         ↓ (1:1 or M:1)
┌────────────────────────────┐
│ Receipt: RCP-2025-0001     │
│ Amount: ₹51,250            │
│ Pledges: [GLD-2025-0001]   │
│ Status: Issued             │
└────────────────────────────┘
         │
         ↓ (1:M)
┌────────────────────────────┐
│ Payment: PMT-2025-0001     │
│ Amount: ₹51,250            │
│ Type: Full                 │
│ Status: Completed          │
└────────────────────────────┘
         │
         ↓ (creates)
┌────────────────────────────┐
│ Ledger Entry               │
│ Dr: Cash ₹51,250          │
│ Cr: Receivable ₹51,250    │
└────────────────────────────┘
```

---

### Scenario B: Single Pledge → Single Receipt → Multiple Payments

```
PLEDGE TABLE:
┌────────────────────────────┐
│ Pledge: GLD-2025-0002      │
│ Amount: ₹100,000           │
│ Interest: ₹2,500           │
│ Status: Active             │
│ Total Due: ₹102,500        │
└────────────────────────────┘
         │
         ↓ (1:1 or M:1)
┌────────────────────────────┐
│ Receipt: RCP-2025-0002     │
│ Amount: ₹102,500           │
│ Pledges: [GLD-2025-0002]   │
│ Status: Issued             │
│ Paid: ₹90,000 (partial)    │
│ Remaining: ₹12,500         │
└────────────────────────────┘
         │
         ├─→ PMT-2025-0001: ₹50,000 (Feb 15) → Completed
         ├─→ PMT-2025-0002: ₹40,000 (Mar 15) → Completed
         └─→ PMT-2025-0003: ₹12,500 (Apr 15) → Completed
               │
               └─→ 3 Ledger Entries Created (auto)
```

---

### Scenario C: Multiple Pledges → One Receipt → One or Multiple Payments

```
PLEDGES TABLE:
┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│ GLD-2025-0003│  │ SLV-2025-0001│  │ PLT-2025-0001│
│ ₹30,000+₹750 │  │ ₹20,000+₹500 │  │ ₹15,000+₹375 │
│ Status:Active│  │ Status:Active│  │ Status:Active│
└──────────────┘  └──────────────┘  └──────────────┘
         │                 │                 │
         └────────┬────────┴────────┬────────┘
                  ↓
        ┌──────────────────────────┐
        │ Receipt: RCP-2025-0003   │
        │ Total: ₹66,625           │
        │ Pledges: 3 items         │
        │ Status: Issued           │
        └──────────────────────────┘
                  │
                  ├─→ RCP Item 1: GLD-2025-0003 (₹30,750)
                  ├─→ RCP Item 2: SLV-2025-0001 (₹20,500)
                  └─→ RCP Item 3: PLT-2025-0001 (₹15,375)
                  
        PAYMENT OPTIONS:
        Option A: One payment for all
        └─→ PMT-2025-0001: ₹66,625 (Full)
        
        Option B: Separate payments per pledge
        ├─→ PMT-2025-0001: ₹30,750 (GLD)
        ├─→ PMT-2025-0002: ₹20,500 (SLV)
        └─→ PMT-2025-0003: ₹15,375 (PLT)
        
        Option C: Mixed payments
        ├─→ PMT-2025-0001: ₹40,000 (Partial)
        └─→ PMT-2025-0002: ₹26,625 (Rest)
```

---

## 🗄️ FOUR NEW TABLES

### Table 1: PledgeReceipts (PRIMARY TABLE)

```
PledgeReceipts
├── id (PK)
├── company_id (FK) → Company
├── receipt_no: VARCHAR(50) UNIQUE → RCP-2025-0001
├── receipt_type: ENUM('Pledge', 'Redemption', 'Adjustment')
├── receipt_date: DATE
├── customer_id (FK) → Customer
├── total_pledge_amount: DECIMAL
├── total_interest_charged: DECIMAL
├── total_amount_due: DECIMAL
├── notes: TEXT
├── status: ENUM('Draft', 'Issued', 'Cancelled')
├── created_by (FK) → User
├── created_at: DATETIME
└── updated_at: DATETIME

Relationships:
  ├── Has Many: PledgeReceiptItems (receipts ↔ pledges)
  ├── Belongs To: Company
  ├── Belongs To: Customer
  └── Belongs To: User (created_by)
```

### Table 2: PledgeReceiptItems (JUNCTION TABLE)

```
PledgeReceiptItems
├── id (PK)
├── receipt_id (FK) → PledgeReceipts
├── pledge_id (FK) → Pledges
├── pledge_amount: DECIMAL
├── interest_amount: DECIMAL
├── created_at: DATETIME

Relationships:
  ├── Belongs To: PledgeReceipts
  └── Belongs To: Pledges

Purpose:
  → Links multiple pledges to one receipt
  → Tracks amount per pledge in receipt
  → Example: One receipt has items for 3 pledges
```

### Table 3: PledgePayments (PRIMARY TABLE)

```
PledgePayments
├── id (PK)
├── company_id (FK) → Company
├── payment_no: VARCHAR(50) UNIQUE → PMT-2025-0001
├── payment_date: DATE
├── customer_id (FK) → Customer
├── pledge_id (FK) → Pledges (ONE payment to ONE pledge)
├── amount_paid: DECIMAL
├── interest_paid: DECIMAL
├── principal_paid: DECIMAL
├── payment_method: ENUM('Cash', 'Check', 'Transfer', 'Card', 'Other')
├── reference_no: VARCHAR(100) (Check #, Txn ID, etc.)
├── payment_type: ENUM('Partial', 'Full', 'Interest Only', 'Adjustment')
├── status: ENUM('Pending', 'Completed', 'Failed', 'Reversed')
├── debit_account_id (FK) → ChartOfAccounts (Cash account)
├── credit_account_id (FK) → ChartOfAccounts (Receivable account)
├── ledger_entry_id (FK) → LedgerEntries (auto-created)
├── notes: TEXT
├── created_by (FK) → User
├── created_at: DATETIME
└── updated_at: DATETIME

Relationships:
  ├── Belongs To: Company
  ├── Belongs To: Customer
  ├── Belongs To: Pledges
  ├── Belongs To: ChartOfAccounts (debit)
  ├── Belongs To: ChartOfAccounts (credit)
  ├── Belongs To: LedgerEntries
  └── Belongs To: User (created_by)
```

### Table 4: PledgePaymentSchedules (OPTIONAL)

```
PledgePaymentSchedules
├── id (PK)
├── pledge_id (FK) → Pledges
├── company_id (FK) → Company
├── schedule_month: INT (1, 2, 3, etc.)
├── due_date: DATE
├── scheduled_amount: DECIMAL
├── status: ENUM('Pending', 'Paid', 'Overdue', 'Waived')
├── actual_payment_id (FK) → PledgePayments (optional)
├── created_at: DATETIME

Purpose:
  → Optional: For EMI/Installment tracking
  → Example: 3-month EMI of ₹50,000 loan
    * Month 1: ₹16,667 due Feb 28
    * Month 2: ₹16,667 due Mar 28
    * Month 3: ₹16,666 due Apr 28
  → Can auto-generate or manual
```

---

## 📋 TABLE RELATIONSHIPS

```
┌──────────────────────────────────────────────────────────────┐
│                    RELATIONSHIP DIAGRAM                      │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│  Company                                                    │
│    │                                                        │
│    ├──→ Pledges (existing)                                 │
│    │    └──→ PledgeReceiptItems (junction)                │
│    │         └──→ PledgeReceipts (NEW)                    │
│    │                                                        │
│    └──→ Customer (existing)                               │
│         ├──→ Pledges                                       │
│         ├──→ PledgeReceipts                               │
│         └──→ PledgePayments                               │
│                                                              │
│  Pledges (existing)                                         │
│    ├──→ PledgeReceiptItems                                │
│    │    └──→ PledgeReceipts                               │
│    │                                                        │
│    ├──→ PledgePayments                                     │
│    │    └──→ LedgerEntries (auto-created)                │
│    │                                                        │
│    └──→ PledgePaymentSchedules (optional)                 │
│                                                              │
│  ChartOfAccounts (existing)                               │
│    └──→ PledgePayments (debit & credit accounts)          │
│                                                              │
│  LedgerEntries (existing)                                  │
│    └──→ PledgePayments (auto-linked)                      │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

---

## 🔄 FLOW DIAGRAMS

### Flow 1: Create Receipt & Get Payment

```
STEP 1: Create Pledge
        Pledge: GLD-2025-0001 (₹50,000 + ₹1,250 interest)
        
STEP 2: Create Receipt
        Receipt: RCP-2025-0001
        Amount: ₹51,250
        Status: Draft
        
STEP 3: Issue Receipt
        Status: Draft → Issued
        Customer gets receipt
        
STEP 4: Record Payment
        Payment: PMT-2025-0001 (₹51,250)
        
STEP 5: Auto-Create Ledger Entry
        Dr: Cash (1000) ₹51,250
        Cr: Receivable (1051xxxx) ₹51,250
        
STEP 6: Update Status
        Pledge: Active → Redeemed
        Payment: Pending → Completed
        Receipt: Issued → Settled
```

### Flow 2: Handle Partial Payments

```
STEP 1: Create Pledge
        Amount Due: ₹102,500
        
STEP 2: Create Receipt
        Receipt: RCP-2025-0002
        Amount: ₹102,500
        
STEP 3: First Payment
        Payment: PMT-2025-0001 (₹50,000)
        Remaining: ₹52,500
        
STEP 4: Second Payment
        Payment: PMT-2025-0002 (₹40,000)
        Remaining: ₹12,500
        
STEP 5: Final Payment
        Payment: PMT-2025-0003 (₹12,500)
        Remaining: ₹0
        
STEP 6: Auto Update
        Total Paid: ₹102,500
        Status: Fully Paid
        Pledge: Redeemed
        Receipt: Settled
```

---

## 🎯 AUTO-GENERATION

### Receipt Number Generation

```
format: RCP-{YYYY}-{SEQUENCE}

Logic:
  CURRENT_YEAR = 2025
  LAST_RECEIPT_THIS_YEAR = RCP-2025-0042
  NEXT_SEQUENCE = 43
  NEW_RECEIPT_NO = RCP-2025-0043
  
  Year changes:
    Last Receipt 2025: RCP-2025-9999
    First Receipt 2026: RCP-2026-0001
```

### Payment Number Generation

```
format: PMT-{YYYY}-{SEQUENCE}

Same logic as receipts:
  PMT-2025-0001
  PMT-2025-0002
  ...
  PMT-2025-9999
  PMT-2026-0001
```

---

## 💰 ACCOUNTING ENTRIES

### When Receipt Created:
```
❌ NO ledger entry
   (Receipt is just documentation)
   Status: Draft
```

### When Receipt Issued:
```
❌ Still NO ledger entry
   (Waiting for customer to pay)
   Status: Issued
```

### When Payment Made:
```
✅ AUTOMATIC ledger entry created

Debit:  Cash/Bank Account (1000 or 1010)
Credit: Customer Receivable (1051xxxx)
Amount: payment_amount
Reference: payment_no, pledge_id

Example:
  Dr: Cash (1000)                  ₹50,000
  Cr: Cust Receivable (1051005)    ₹50,000
  
Auto-calculates running balance ✅
Updates account balances ✅
Syncs trial balance ✅
```

---

## 🔗 INTEGRATION POINTS

```
1. With Pledges:
   ├─ Link receipt_items to pledge_id
   ├─ Link payments to pledge_id
   ├─ Update pledge status on full payment
   └─ Track which pledges have receipts

2. With Chart of Accounts:
   ├─ Use Customer Receivable (1051xxxx)
   ├─ Use Cash/Bank (1000, 1010)
   ├─ Use Interest Income (4000)
   └─ Link accounts in payments

3. With Ledger Entries:
   ├─ Auto-create on payment
   ├─ Update running balance
   ├─ Sync account balances
   └─ Include in trial balance

4. With Customers:
   ├─ Link receipts to customer
   ├─ Link payments to customer
   ├─ Track customer's total pledges
   └─ Track customer's payment history

5. With Files:
   ├─ Store receipt PDFs (future)
   ├─ Store payment receipts (future)
   └─ Archive documents
```

---

## 📊 EXAMPLE DATA

### Receipt Example:

```
RCP-2025-0001
├── Customer: Ramesh Kumar
├── Receipt Date: 2025-02-15
├── Status: Issued
│
├── Items:
│   ├── GLD-2025-0001: ₹30,000 + ₹750 interest = ₹30,750
│   ├── SLV-2025-0001: ₹20,000 + ₹500 interest = ₹20,500
│   └── PLT-2025-0001: ₹15,000 + ₹375 interest = ₹15,375
│
└── Total: ₹66,625
    └── Paid: ₹50,000
    └── Remaining: ₹16,625
```

### Payment Example:

```
PMT-2025-0001
├── Pledge: GLD-2025-0001
├── Customer: Ramesh Kumar
├── Payment Date: 2025-02-20
├── Amount Paid: ₹50,000
│   ├── Principal: ₹49,000
│   └── Interest: ₹1,000
├── Payment Method: Cash
├── Type: Partial
├── Status: Completed
│
├── Ledger Entry Created:
│   ├── Dr: Cash (1000): ₹50,000
│   ├── Cr: Cust Receivable: ₹50,000
│   └── Running Balance: Calculated
│
└── Recorded By: John (Admin)
```

---

## ✅ SUMMARY

### What Gets Created:
- ✅ PledgeReceipts table (stores receipt info)
- ✅ PledgeReceiptItems table (links pledges to receipts)
- ✅ PledgePayments table (stores payment info)
- ✅ PledgePaymentSchedules table (optional, for EMI)

### Key Features:
- ✅ One receipt can have multiple pledges
- ✅ One pledge can have multiple payments
- ✅ Auto-generated receipt numbers (RCP-2025-XXXX)
- ✅ Auto-generated payment numbers (PMT-2025-XXXX)
- ✅ Automatic ledger entry creation on payments
- ✅ Balance tracking (total due, paid, remaining)
- ✅ Status management (Draft/Issued/Settled)
- ✅ Payment methods tracking (Cash, Check, etc.)

### Will Build:
- ✅ 4 database models
- ✅ Pydantic schemas for validation
- ✅ Auto-numbering functions
- ✅ Receipt management routes (8 endpoints)
- ✅ Payment management routes (7 endpoints)
- ✅ Balance calculation functions
- ✅ Automatic ledger integration
- ✅ Complete test suite
- ✅ Comprehensive documentation

---

## ❓ CLARIFICATIONS NEEDED

Before proceeding, please confirm:

1. **Receipt Combination:** 
   - Auto-combine same customer, same date?
   - Or each pledge gets own receipt?
   - Or user-selectable?

2. **Payment Allocation:**
   - FIFO (first-in-first-out)?
   - Manual selection?

3. **Schedules:**
   - Need EMI tracking?
   - Or just track payments as they come?

4. **Late Charges:**
   - Auto-calculate late fees?
   - Or just mark overdue?

5. **PDF:**
   - Just database storage now?
   - PDF generation later?

---

**📌 Ready for: APPROVAL & CLARIFICATIONS**

Once approved, implementation will start immediately! 🚀
