# 📋 PLEDGE RECEIPTS & PAYMENTS SYSTEM - IMPLEMENTATION PLAN

## 🎯 Overview
Create a flexible receipts and payments tracking system for pledges that supports:
- **Multiple pledges → One receipt** (batch pledges)
- **One pledge → Multiple payments** (partial/installment payments)
- **Payment tracking** (partial, full, overdue)
- **Receipt generation** (for customer records)

---

## 📊 Current System Understanding

### Existing Pledge Structure:
```
Pledge
├── pledge_no (GLD-2025-0001)
├── customer_id
├── scheme_id
├── loan_amount (₹50,000)
├── interest_rate (2.5%)
├── first_month_interest (₹1,250)
├── status (Active, Closed, Redeemed, Forfeited)
└── payment_account_id (where cash goes)

PledgeItems (multiple per pledge)
├── pledge_id
├── jewel_type_id
├── gross_weight
├── net_weight
└── quantity
```

---

## 📝 PROPOSED TABLES

### Table 1: PledgeReceipts
```
CREATE TABLE pledge_receipts (
    id                      INT PRIMARY KEY
    company_id              INT (FK) - Which company
    receipt_no              VARCHAR(50) UNIQUE - AUTO: RCP-{YYYY}-{SEQUENCE}
    receipt_type            ENUM('Pledge', 'Redemption', 'Adjustment')
    receipt_date            DATE - When receipt issued
    
    -- Customer Info
    customer_id             INT (FK) - Who received/gave items
    
    -- Amount & Interest
    total_pledge_amount     DECIMAL - Sum of all pledges in receipt
    total_interest_charged  DECIMAL - Sum of all interests
    total_amount_due        DECIMAL - pledge_amount + interest
    notes                   TEXT
    
    -- Status & Tracking
    status                  ENUM('Draft', 'Issued', 'Cancelled')
    created_by              INT (FK) - User who created
    created_at              DATETIME
    updated_at              DATETIME
);

KEY POINTS:
- One receipt can cover MULTIPLE pledges
- Example: RCP-2025-0001 covers pledges GLD-2025-0001, GLD-2025-0002, GLD-2025-0003
- Used when pledging multiple items or multiple pledges on same date
```

### Table 2: PledgeReceiptItems
```
CREATE TABLE pledge_receipt_items (
    id                      INT PRIMARY KEY
    receipt_id              INT (FK) - Which receipt
    pledge_id               INT (FK) - Which pledge
    
    -- Amount Details
    pledge_amount           DECIMAL - Amount for this pledge
    interest_amount         DECIMAL - Interest for this pledge
    
    -- Tracking
    created_at              DATETIME
);

KEY POINTS:
- Junction table linking receipts to pledges
- One receipt → Many pledges relationship
- Tracks individual amounts per pledge in receipt
```

### Table 3: PledgePayments
```
CREATE TABLE pledge_payments (
    id                      INT PRIMARY KEY
    company_id              INT (FK) - Which company
    payment_no              VARCHAR(50) UNIQUE - AUTO: PMT-{YYYY}-{SEQUENCE}
    payment_date            DATE - When payment made
    
    -- Customer & Pledge
    customer_id             INT (FK) - Who paid
    pledge_id               INT (FK) - Which pledge (one pledge per payment)
    
    -- Payment Amount Details
    amount_paid             DECIMAL - How much paid
    interest_paid           DECIMAL - Interest portion
    principal_paid          DECIMAL - Principal/item value portion
    
    -- Payment Method
    payment_method          ENUM('Cash', 'Check', 'Bank Transfer', 'Card', 'Other')
    reference_no            VARCHAR(100) - Check #, Transaction ID, etc.
    
    -- Tracking
    payment_type            ENUM('Partial', 'Full', 'Interest Only', 'Adjustment')
    status                  ENUM('Pending', 'Completed', 'Failed', 'Reversed')
    
    -- Accounting
    debit_account_id        INT (FK) - Account debited (Cash, Bank, etc.)
    credit_account_id       INT (FK) - Account credited (usually Customer Receivable)
    ledger_entry_id         INT (FK) - Link to ledger entry
    
    -- Notes & Tracking
    notes                   TEXT
    created_by              INT (FK) - User who recorded
    created_at              DATETIME
    updated_at              DATETIME
);

KEY POINTS:
- Multiple payments per pledge (partial payments, installments)
- Example: Pledge GLD-2025-0001 with ₹50,000 loan:
  * PMT-2025-0001: ₹25,000 (February)
  * PMT-2025-0002: ₹20,000 (March)
  * PMT-2025-0003: ₹5,000 + interest (April)
- Links to ledger for automatic accounting
```

### Table 4: PledgePaymentSchedules (OPTIONAL - For EMI/Installments)
```
CREATE TABLE pledge_payment_schedules (
    id                      INT PRIMARY KEY
    pledge_id               INT (FK) - Which pledge
    company_id              INT (FK) - Which company
    
    -- Schedule Details
    schedule_month          INT - Month number (1-12)
    due_date                DATE - When payment due
    scheduled_amount        DECIMAL - Amount due
    
    -- Tracking
    status                  ENUM('Pending', 'Paid', 'Overdue', 'Waived')
    actual_payment_id       INT (FK) - Which payment covered this
    
    created_at              DATETIME
);

KEY POINTS:
- Optional: Only needed if supporting EMI/installment plans
- Example: 3-month EMI for ₹50,000 loan:
  * Month 1: ₹16,667 (Feb 28)
  * Month 2: ₹16,667 (Mar 28)
  * Month 3: ₹16,666 (Apr 28)
- Can auto-generate or create manually
```

---

## 🔄 DATA FLOW EXAMPLES

### Scenario 1: Single Pledge, Single Payment (Full)
```
PLEDGE CREATED:
  Pledge: GLD-2025-0001 (₹50,000 + ₹1,250 interest = ₹51,250)
  Status: Active

RECEIPT ISSUED:
  Receipt: RCP-2025-0001
  Pledges: [GLD-2025-0001]
  Total: ₹51,250
  Status: Issued

PAYMENT MADE:
  Payment: PMT-2025-0001 (₹51,250)
  Type: Full
  Date: Feb 28, 2025

RESULT:
  Pledge Status: Redeemed
  Payment Status: Completed
  Receipt Status: Settled
```

### Scenario 2: Single Pledge, Multiple Payments (Partial)
```
PLEDGE CREATED:
  Pledge: GLD-2025-0002 (₹100,000 + ₹2,500 interest = ₹102,500)
  Status: Active

RECEIPT ISSUED:
  Receipt: RCP-2025-0002
  Pledges: [GLD-2025-0002]
  Total: ₹102,500
  Status: Issued

PAYMENTS MADE:
  Payment 1: PMT-2025-0001 (₹50,000) - Partial - Feb 15
  Payment 2: PMT-2025-0002 (₹40,000) - Partial - Mar 15
  Payment 3: PMT-2025-0003 (₹12,500) - Full - Apr 15

TRACKING:
  Remaining Balance = ₹102,500 - ₹50,000 - ₹40,000 - ₹12,500 = ₹0
  Receipt Status: Fully Paid

RESULT:
  Pledge Status: Redeemed
  All Payments: Completed
  Receipt Status: Settled
```

### Scenario 3: Multiple Pledges, One Receipt
```
PLEDGES CREATED (Same Customer - Same Day):
  Pledge 1: GLD-2025-0003 (₹30,000 + ₹750 interest)
  Pledge 2: SLV-2025-0001 (₹20,000 + ₹500 interest)
  Pledge 3: PLT-2025-0001 (₹15,000 + ₹375 interest)

RECEIPT ISSUED (Combined):
  Receipt: RCP-2025-0003
  Pledges: [GLD-2025-0003, SLV-2025-0001, PLT-2025-0001]
  Total Amount: ₹65,000 + ₹1,625 interest = ₹66,625
  Status: Issued

RECEIPT ITEMS:
  Item 1: GLD-2025-0003 (₹30,000 + ₹750)
  Item 2: SLV-2025-0001 (₹20,000 + ₹500)
  Item 3: PLT-2025-0001 (₹15,000 + ₹375)

RESULT:
  One receipt covers 3 pledges
  All pledges linked to single receipt
  Customer gets one document
```

---

## 📋 TABLE STRUCTURE SUMMARY

```
┌─────────────────────────────────────────────────────────────┐
│                  PLEDGE RECEIPTS SYSTEM                    │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Pledge (existing)                                         │
│    ├── pledge_no: GLD-2025-0001                           │
│    ├── loan_amount: ₹50,000                               │
│    └── status: Active/Closed/Redeemed                      │
│                                                             │
│         ↓ (links to)                                       │
│                                                             │
│  PledgeReceiptItems (junction table)                      │
│    └── Links pledge to receipt                            │
│                                                             │
│         ↓ (part of)                                       │
│                                                             │
│  PledgeReceipts (NEW)                                     │
│    ├── receipt_no: RCP-2025-0001                         │
│    ├── receipt_type: Pledge/Redemption                    │
│    ├── total_amount_due: ₹51,250                         │
│    └── status: Draft/Issued/Cancelled                     │
│                                                             │
│         ↓ (payment towards)                               │
│                                                             │
│  PledgePayments (NEW)                                     │
│    ├── payment_no: PMT-2025-0001                         │
│    ├── pledge_id: (one pledge)                           │
│    ├── amount_paid: ₹25,000                              │
│    ├── payment_type: Partial/Full                        │
│    └── status: Completed/Pending                          │
│                                                             │
│         ↓ (creates)                                        │
│                                                             │
│  LedgerEntries (existing - auto-sync)                     │
│    └── Debit: Cash, Credit: Receivable                    │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## 🔑 Key Features

### Feature 1: Flexible Receipt Generation
```
✅ Single pledge + Single receipt = Normal case
✅ Multiple pledges + One receipt = Batch receipts
✅ Same customer, same date → Can be combined
✅ Can also create separate receipts per pledge
```

### Feature 2: Flexible Payment Tracking
```
✅ Full payment in one go
✅ Partial payments (multiple times)
✅ Interest-only payments
✅ Principal + interest mix
✅ Adjustment payments (discounts, etc.)
```

### Feature 3: Automatic Ledger Sync
```
When payment made:
  ✅ Automatic ledger entry created
  ✅ Running balance updated
  ✅ Account balances adjusted
  ✅ Trial balance stays in sync
```

### Feature 4: Balance Tracking
```
For each pledge:
  ✅ Total due (principal + interest)
  ✅ Amount paid so far
  ✅ Remaining balance
  ✅ Overdue status if past due date
```

### Feature 5: Receipt Management
```
✅ Generate unique receipt numbers (RCP-2025-0001)
✅ Issue receipts (change status from Draft to Issued)
✅ Cancel receipts if needed
✅ PDF generation (future enhancement)
✅ Print or email to customer
```

---

## 🗄️ AUTO-GENERATION LOGIC

### Receipt Number Format:
```
Format: RCP-{YYYY}-{SEQUENCE}
Examples:
  RCP-2025-0001  (First receipt in 2025)
  RCP-2025-0002  (Second receipt in 2025)
  RCP-2025-0003  (Third receipt in 2025)

Resets yearly:
  RCP-2025-9999
  RCP-2026-0001  (New year, resets to 0001)
```

### Payment Number Format:
```
Format: PMT-{YYYY}-{SEQUENCE}
Examples:
  PMT-2025-0001  (First payment in 2025)
  PMT-2025-0002  (Second payment in 2025)

Resets yearly
```

---

## 📱 API ENDPOINTS (Planned)

### Receipt Management:
```
POST   /pledges/receipts/                              Create receipt
GET    /pledges/receipts/{company_id}                  List receipts
GET    /pledges/receipts/{receipt_id}                  Get specific receipt
PUT    /pledges/receipts/{receipt_id}                  Update receipt
POST   /pledges/receipts/{receipt_id}/issue            Issue receipt
POST   /pledges/receipts/{receipt_id}/cancel           Cancel receipt
GET    /pledges/receipts/{receipt_id}/pdf              Generate PDF
```

### Payment Management:
```
POST   /pledges/payments/                              Record payment
GET    /pledges/payments/{company_id}                  List payments
GET    /pledges/payments/{payment_id}                  Get payment
GET    /pledges/{pledge_id}/payments                   Get payments for pledge
GET    /pledges/{pledge_id}/balance                    Get remaining balance
POST   /pledges/payments/{payment_id}/reverse          Reverse payment
```

### Reporting:
```
GET    /pledges/reports/outstanding                    Outstanding amounts
GET    /pledges/reports/overdue                        Overdue pledges
GET    /pledges/reports/collections/{date_range}      Collection report
GET    /pledges/reports/customer/{customer_id}        Customer pledge history
```

---

## 💰 ACCOUNTING IMPACT

### When Receipt Created:
```
No ledger entry yet (just documentation)
Receipt is in "Draft" status
```

### When Receipt Issued:
```
Still no ledger entry
Receipt moves to "Issued" status
Customer gets receipt
```

### When Payment Made:
```
Automatic ledger entries created:
  Debit:  Cash/Bank Account
  Credit: Customer Receivable Account (1051xxxx)
  
Amount: payment_amount
Reference: payment_no and pledge_id
```

### Auto-Sync Features:
```
✅ Running balance updated
✅ Account balances adjusted
✅ Trial balance synchronized
✅ Remaining balance calculated
```

---

## 🔗 Integration Points

```
With Pledges:
  ✅ Link to pledge_id
  ✅ Track pledge status changes
  ✅ Update pledge status on full payment

With Chart of Accounts:
  ✅ Use Customer Receivable accounts (1051xxxx)
  ✅ Use Cash/Bank accounts (1000, 1010)
  ✅ Use Interest Income accounts (4000)

With Ledger Entries:
  ✅ Create entries when payment made
  ✅ Auto-calculate running balance
  ✅ Update account balances

With Customers:
  ✅ Link to customer_id
  ✅ Track customer's total pledges
  ✅ Track customer's total payments

With Schemes:
  ✅ Reference scheme for pledges in receipt
  ✅ Use scheme's interest rate if needed
```

---

## 🎯 STATUS TRANSITIONS

### Receipt Status Flow:
```
Draft → Issued → Settled (when fully paid) or Cancelled
  or   → Cancelled (if customer doesn't proceed)
```

### Payment Status Flow:
```
Pending → Completed (normal case)
  or   → Failed (payment rejected)
  or   → Reversed (customer wants refund)
```

### Pledge Status Impact:
```
Active → Redeemed (when fully paid)
      → Closed (when extended)
      → Forfeited (when not paid)
```

---

## 📊 DATA RETENTION

```
Keep receipts:      ✅ Forever (audit trail, legal requirement)
Keep payments:      ✅ Forever (financial records)
Keep schedules:     ✅ 7 years (tax requirement)
Keep deleted data:  ✅ Soft delete with is_deleted flag
```

---

## 🔒 SECURITY CONSIDERATIONS

```
Authorization:
  ✅ Only users in same company can manage
  ✅ Admin override available
  ✅ Create/View/Update permissions separate

Audit Trail:
  ✅ Track who created receipt
  ✅ Track who recorded payment
  ✅ Track all modifications
  ✅ Timestamp all actions

Data Integrity:
  ✅ Foreign key constraints
  ✅ Amount validations
  ✅ Status flow validations
  ✅ Ledger entry synchronization
```

---

## 📈 FUTURE ENHANCEMENTS

```
Phase 2:
  ☐ Email receipt to customer
  ☐ SMS notification for payment due
  ☐ PDF generation
  ☐ Print receipt

Phase 3:
  ☐ Payment reminders (auto SMS/Email)
  ☐ Late charges calculation
  ☐ Extension management
  ☐ Refinance support

Phase 4:
  ☐ Online payment portal
  ☐ Payment gateway integration
  ☐ Auto-reconciliation
  ☐ Advanced reporting
```

---

## 📋 SUMMARY TABLE

| Feature | Details | Priority |
|---------|---------|----------|
| **PledgeReceipts** | Multiple pledges per receipt | HIGH |
| **PledgeReceiptItems** | Junction table for many-to-many | HIGH |
| **PledgePayments** | Track all payments to pledges | HIGH |
| **Auto Receipt #** | Generate RCP-2025-XXXX | HIGH |
| **Auto Payment #** | Generate PMT-2025-XXXX | HIGH |
| **Auto Ledger Sync** | Create ledger on payment | HIGH |
| **Balance Tracking** | Calculate remaining amount | HIGH |
| **Status Management** | Draft/Issued/Cancelled, Completed/Pending | HIGH |
| **Payment Methods** | Cash, Check, Transfer, Card, Other | MEDIUM |
| **Schedule Support** | Optional EMI/installment tracking | MEDIUM |
| **PDF Generation** | Export receipts as PDF | LOW |
| **Notifications** | SMS/Email alerts | LOW |

---

## ✅ IMPLEMENTATION CHECKLIST

Once you approve, I will:

- [ ] Create 4 database models (PledgeReceipts, PledgeReceiptItems, PledgePayments, optional PledgePaymentSchedules)
- [ ] Create Pydantic schemas for validation
- [ ] Implement auto-numbering functions (receipts & payments)
- [ ] Create routes for receipt management (8 endpoints)
- [ ] Create routes for payment management (7 endpoints)
- [ ] Implement automatic ledger entry creation
- [ ] Add balance calculation functions
- [ ] Create comprehensive test suite
- [ ] Add full documentation
- [ ] Verify integration with existing systems

---

## 🚀 QUESTIONS FOR APPROVAL

Before I proceed, please clarify:

1. **Receipt Combination Logic:**
   - Should receipts be auto-combined if same customer & same date?
   - Or should each pledge get its own receipt?
   - Or user-selectable at creation time?

2. **Payment Allocation:**
   - Should payments auto-apply to oldest debt first (FIFO)?
   - Or allow manual allocation to specific pledges?

3. **Schedule Generation:**
   - Do you need EMI/installment schedules?
   - Or just track payments as they come?

4. **Late Charges:**
   - Should system calculate late fees automatically?
   - Or just mark as overdue?

5. **Receipt Format:**
   - Just database storage?
   - Or PDF generation too?

---

## 📞 PLAN APPROVAL

Please review and let me know:
- ✅ **APPROVE** - Proceed with implementation as planned
- 📝 **MODIFY** - Need changes to the plan
- ❓ **QUESTIONS** - Need clarification on specific parts

---

**Once you approve, I will create all tables, schemas, routes, utilities, tests, and documentation!**
