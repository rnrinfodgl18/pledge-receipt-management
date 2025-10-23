# Pledge Receipt System - Automatic Features Flow Diagram

## 1️⃣ FEATURE 1: Automatic Pledge Status Update on Full Close

```
┌─────────────────────────────────────────────────────────────────┐
│ SCENARIO: Customer pays entire pledge amount in one receipt    │
└─────────────────────────────────────────────────────────────────┘

STEP 1: CREATE RECEIPT IN DRAFT STATUS
┌──────────────────────────────────┐
│ POST /api/receipts/              │
│ {                                │
│   company_id: 1                  │
│   receipt_date: 2025-10-23       │
│   receipt_amount: 10,000          │
│   receipt_items: [{              │
│     pledge_id: 5                 │
│     paid_principal: 10,000        │
│     paid_interest: 0              │
│     payment_type: "Full"          │
│     total_amount_paid: 10,000     │
│   }]                             │
│ }                                │
└──────────────────────────────────┘
           ↓
┌──────────────────────────────────┐
│ Receipt Created                  │
│ ├─ receipt_id: 123              │
│ ├─ receipt_no: RCP-2025-0001   │
│ ├─ status: DRAFT ✓              │
│ ├─ coa_entry_status: PENDING    │
│ └─ Items: 1 item                │
└──────────────────────────────────┘


STEP 2: POST RECEIPT (THIS TRIGGERS AUTO UPDATE)
┌──────────────────────────────────────────────────────┐
│ POST /api/receipts/123/post                          │
└──────────────────────────────────────────────────────┘
           ↓
┌──────────────────────────────────────────────────────┐
│ System Executes post_receipt() Function             │
│                                                      │
│ 1. create_receipt_coa_entries()                      │
│    └─ Creates 2 COA entries                          │
│       • DR: Cash (1000) = 10,000                     │
│       • CR: Receivable (1051) = 10,000               │
│                                                      │
│ 2. update_pledge_balance() FOR EACH ITEM             │
│    └─ Gets Pledge #5                                │
│    └─ Calculates total_paid (from ALL receipts)     │
│    └─ Compares: 10,000 >= loan_amount (10,000)?     │
│    └─ ✅ YES! → SET pledge.status = "Redeemed"      │
│                                                      │
│ 3. Commit all changes                               │
└──────────────────────────────────────────────────────┘
           ↓
┌──────────────────────────────────────────────────────┐
│ AUTOMATIC RESULTS:                                   │
│                                                      │
│ Receipt Updated:                                     │
│ ├─ status: POSTED ✅                                │
│ ├─ coa_entry_status: POSTED ✅                      │
│ └─ receipt_items: [item1]                           │
│                                                      │
│ Pledge Updated:                                      │
│ ├─ id: 5                                            │
│ ├─ status: REDEEMED ✅ (AUTO)                       │
│ └─ Can no longer receive payments                   │
│                                                      │
│ COA Updated:                                         │
│ ├─ Entry 1: DR 1000 (Cash) = 10,000                │
│ ├─ Entry 2: CR 1051 (Receivable) = 10,000          │
│ └─ Trial balance = balanced ✅                      │
└──────────────────────────────────────────────────────┘


✅ AUTOMATIC UPDATE CONFIRMED
   Pledge status changed from "Active" → "Redeemed"
   WITHOUT manual intervention!
```

---

## 2️⃣ FEATURE 2: Automatic COA Reversal on Receipt Void/Delete

```
┌─────────────────────────────────────────────────────────────────┐
│ SCENARIO: Need to cancel a receipt that was already posted     │
└─────────────────────────────────────────────────────────────────┘

STATE BEFORE (Posted Receipt with COA Entries)
┌─────────────────────────────────────────────────────┐
│ Receipt #123 (Posted)                               │
│ ├─ receipt_no: RCP-2025-0001                       │
│ ├─ status: POSTED                                   │
│ ├─ receipt_amount: 5,000                            │
│ └─ Items:                                           │
│    ├─ Item 1: Pledge #3, paid_principal: 3,000     │
│    └─ Item 2: Pledge #5, paid_interest: 2,000      │
│                                                     │
│ Current COA Entries:                                │
│ ├─ Entry #456: DR 1000 (Cash) = 5,000              │
│ ├─ Entry #457: CR 1051 (Receivable) = 3,000        │
│ └─ Entry #458: CR 4000 (Interest Income) = 2,000   │
│                                                     │
│ Pledge Statuses:                                    │
│ ├─ Pledge #3: Active (partial payment: 3000/5000)  │
│ └─ Pledge #5: Redeemed (full payment: 2000/2000)   │
└─────────────────────────────────────────────────────┘


STEP 1: VOID THE RECEIPT
┌──────────────────────────────────────────────┐
│ POST /api/receipts/123/void                  │
│ {                                            │
│   reason: "Data entry error"                 │
│ }                                            │
└──────────────────────────────────────────────┘
           ↓
┌──────────────────────────────────────────────┐
│ System Executes void_receipt() Function     │
│                                              │
│ 1. reverse_receipt_ledger_entries()          │
│    ├─ Finds all entries for Receipt #123    │
│    ├─ Entry #456 (DR 1000):                 │
│    │  └─ Create reverse: CR 1000 = 5,000    │
│    ├─ Entry #457 (CR 1051):                 │
│    │  └─ Create reverse: DR 1051 = 3,000    │
│    └─ Entry #458 (CR 4000):                 │
│       └─ Create reverse: DR 4000 = 2,000    │
│                                              │
│ 2. update_pledge_balance() FOR EACH ITEM    │
│    ├─ Pledge #3: Recalc = 0 paid (was 3k)   │
│    │  └─ Status unchanged (still Active)    │
│    └─ Pledge #5: Recalc = 0 paid (was 2k)   │
│       └─ Status changed: Redeemed → Active  │
│                                              │
│ 3. Commit all changes                       │
└──────────────────────────────────────────────┘
           ↓

STATE AFTER (All Reversed)
┌────────────────────────────────────────────────────┐
│ Receipt #123 (Voided)                              │
│ ├─ status: VOID ✅                                 │
│ ├─ remarks: "Void - Data entry error"              │
│ └─ Items: Same (for reference)                     │
│                                                    │
│ NEW COA Entries (Reversal):                        │
│ ├─ Entry #459: CR 1000 (Cash) = 5,000 ✅          │
│ ├─ Entry #460: DR 1051 (Receivable) = 3,000 ✅    │
│ └─ Entry #461: DR 4000 (Interest Income) = 2,000 ✅│
│                                                    │
│ Original Entries Still Exist (For audit trail):   │
│ ├─ Entry #456: DR 1000 (Original)                 │
│ ├─ Entry #457: CR 1051 (Original)                 │
│ └─ Entry #458: CR 4000 (Original)                 │
│                                                    │
│ Final Trial Balance:                               │
│ ├─ Cash (1000): 5000 - 5000 = 0 ✅ (balanced)     │
│ ├─ Receivable (1051): -3000 + 3000 = 0 ✅         │
│ └─ Interest Income (4000): -2000 + 2000 = 0 ✅    │
│                                                    │
│ Pledge Statuses (Auto-Updated):                    │
│ ├─ Pledge #3: Active (now 0 paid) ✅              │
│ └─ Pledge #5: Active (was Redeemed, now Active) ✅│
└────────────────────────────────────────────────────┘


✅ AUTOMATIC REVERSAL CONFIRMED
   1. All COA entries reversed
   2. Pledge balances recalculated
   3. Pledge statuses auto-updated
   WITHOUT manual intervention!
```

---

## 3️⃣ MULTIPLE SCENARIOS FLOW

```
SCENARIO A: MULTIPLE PLEDGES IN ONE RECEIPT
┌────────────────────────────────────────────────┐
│ Receipt RCP-2025-0001                          │
│ ├─ Item 1: Pledge #1, paid_principal: 5000     │
│ ├─ Item 2: Pledge #2, paid_principal: 3000     │
│ └─ Item 3: Pledge #3, paid_interest: 2000      │
└────────────────────────────────────────────────┘
                    ↓
        POST /api/receipts/{id}/post
                    ↓
        ✅ Pledge #1: Auto-check → Redeemed?
        ✅ Pledge #2: Auto-check → Redeemed?
        ✅ Pledge #3: Auto-check → Redeemed?
        ✅ 4-5 COA entries created
                    ↓
            All auto-updates applied!


SCENARIO B: MULTIPLE PAYMENTS FOR SAME PLEDGE
┌────────────────────────────────────────────────┐
│ Pledge #5: Total Outstanding = 10,000 + 1000   │
└────────────────────────────────────────────────┘
        Jan 1: Receipt #1
        ├─ Paid: 4,000
        ├─ Status: Active (4000/11000 paid)
        ├─ Status Auto-Update: None
        
        Feb 1: Receipt #2
        ├─ Paid: 5,000
        ├─ Status: Active (9000/11000 paid)
        ├─ Status Auto-Update: None
        
        Mar 1: Receipt #3
        ├─ Paid: 2,000
        ├─ Status: ✅ REDEEMED (11000/11000 paid)
        ├─ Status Auto-Update: Active → Redeemed ✅
        └─ Auto at: POST /api/receipts/3/post


SCENARIO C: DELETE vs VOID
┌────────────────────────────────────────────────────┐
│ DELETE (Draft Only)                                │
│ ├─ No COA entries exist yet                        │
│ ├─ Simply delete receipt + items                   │
│ ├─ No reversal needed ✅                           │
│ └─ Pledges unchanged                               │
│                                                    │
│ VOID (Posted Only)                                │
│ ├─ COA entries must be reversed ✅                 │
│ ├─ Reverse all entries to neutral                 │
│ ├─ Recalculate pledge balances ✅                 │
│ └─ Auto-update pledge statuses ✅                 │
└────────────────────────────────────────────────────┘
```

---

## 4️⃣ AUTOMATIC LOGIC FLOW CHART

```
┌─────────────────────────────────────────────────────────────────┐
│                   RECEIPT POSTED                                │
│                 (Status: Draft → Posted)                        │
└─────────────────────────────────────────────────────────────────┘
                            ↓
                    ┌───────────────┐
                    │ create_receipt│
                    │_coa_entries() │
                    └───────────────┘
                            ↓
                ┌─────────────────────────┐
                │ For each receipt item:  │
                │ Create COA entries:     │
                │ • DR: Cash              │
                │ • CR: Receivable        │
                │ • CR: Interest (if any) │
                │ • Other adjustments     │
                └─────────────────────────┘
                            ↓
                    ┌───────────────────────────┐
                    │ update_pledge_balance()   │
                    │ (FOR EACH PLEDGE IN       │
                    │  RECEIPT)                 │
                    └───────────────────────────┘
                            ↓
            ┌───────────────────────────────────┐
            │ Check: is pledge fully paid?      │
            │ total_paid >= loan_amount?        │
            └───────────────────────────────────┘
                    ↙               ↘
                  NO                 YES
                  ↓                   ↓
            ┌──────────┐         ┌──────────────────────┐
            │ Status:  │         │ STATUS AUTO-UPDATE:  │
            │ Active   │         │ Active → Redeemed ✅ │
            │ (stays)  │         │                      │
            └──────────┘         │ (AUTOMATIC!)         │
                                 └──────────────────────┘
                                         ↓
                                ┌─────────────────┐
                                │ Receipt Posted  │
                                │ Pledge Status   │
                                │ Updated Auto    │
                                │ COA Entries:    │
                                │ ✅ Created      │
                                └─────────────────┘


┌─────────────────────────────────────────────────────────────────┐
│                   RECEIPT VOIDED                                │
│                 (Status: Posted → Void)                         │
└─────────────────────────────────────────────────────────────────┘
                            ↓
                    ┌───────────────┐
                    │ reverse_receipt│
                    │_ledger_       │
                    │_entries()     │
                    └───────────────┘
                            ↓
            ┌─────────────────────────────────┐
            │ Find all COA entries for        │
            │ this receipt                    │
            │ For each entry:                 │
            │ • Get: Debit/Credit, amount    │
            │ • Reverse it:                   │
            │   - Debit → Credit ✅           │
            │   - Credit → Debit ✅           │
            └─────────────────────────────────┘
                            ↓
                    ┌───────────────────────────┐
                    │ update_pledge_balance()   │
                    │ (WITH paid=0 to recalc)   │
                    └───────────────────────────┘
                            ↓
                    ┌─────────────────────────────────┐
                    │ For each pledge:                │
                    │ Recalculate total paid (0 now)  │
                    │                                 │
                    │ If was Redeemed:                │
                    │ Redeemed → Active ✅ (AUTO)     │
                    │                                 │
                    │ If was Active:                  │
                    │ Active → Active (unchanged)     │
                    └─────────────────────────────────┘
                            ↓
                    ┌──────────────────────┐
                    │ Receipt Voided       │
                    │ Pledge Statuses      │
                    │ Auto-Recalculated    │
                    │ All COA Reversed ✅  │
                    └──────────────────────┘
```

---

## 5️⃣ CODE FLOW REFERENCES

### Auto Pledge Status Update:
- **File:** `app/receipt_utils.py`
- **Function:** `update_pledge_balance()` (Lines 289-323)
- **Trigger:** Called from `app/routes/receipts.py` in `post_receipt()` (Line 360)
- **Logic:** If `total_principal_paid >= pledge.loan_amount` → `status = "Redeemed"`

### Auto COA Reversal:
- **File:** `app/receipt_utils.py`
- **Function:** `reverse_receipt_ledger_entries()` (Lines 247-274)
- **Trigger:** Called from `app/routes/receipts.py` in `void_receipt()` (Line 412)
- **Logic:** For each original entry, create reverse (debit ↔ credit)

### Workflow Integration:
- **File:** `app/routes/receipts.py`
- **Function:** `post_receipt()` (Lines 315-365)
- **Function:** `void_receipt()` (Lines 376-437)

---

## 6️⃣ TRANSACTION SAFETY

```
ALL OPERATIONS ARE ATOMIC (All or Nothing)

POST RECEIPT:
├─ Step 1: Create COA entries
├─ Step 2: Update pledge balances
├─ Step 3: Update pledge statuses
└─ COMMIT ALL or ROLLBACK ALL ✅

VOID RECEIPT:
├─ Step 1: Reverse COA entries
├─ Step 2: Update receipt status
├─ Step 3: Recalculate pledges
└─ COMMIT ALL or ROLLBACK ALL ✅

If ANY step fails → Entire transaction FAILS
Database stays in CONSISTENT state ✅
```

---

## ✅ SUMMARY

| Feature | Automatic? | When? | What? | File |
|---------|-----------|-------|-------|------|
| Pledge Status Update | ✅ YES | Receipt Posted | If fully paid → Redeemed | `receipt_utils.py` |
| COA Entry Creation | ✅ YES | Receipt Posted | 2-4 entries created | `receipt_utils.py` |
| COA Entry Reversal | ✅ YES | Receipt Voided | All entries reversed | `receipt_utils.py` |
| Balance Recalculation | ✅ YES | Receipt Voided | Pledges recalculated | `receipt_utils.py` |
| Status Reversion | ✅ YES | Receipt Voided | Redeemed → Active if needed | `receipt_utils.py` |

**Everything works automatically! No manual intervention needed! 🎉**
