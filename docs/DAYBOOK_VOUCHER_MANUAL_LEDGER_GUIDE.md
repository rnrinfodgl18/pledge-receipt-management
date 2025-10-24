# 📊 Daybook, Voucher & Manual Ledger Transactions - Complete Guide

## Overview

This guide explains how to implement three key accounting features:
1. **Daybook Entry** - Daily record of transactions
2. **Voucher Creation** - Supporting documents for transactions
3. **Manual Ledger Transactions** - Direct journal entries

---

## 🏗️ System Architecture

```
┌────────────────────────────────────────────────────────┐
│            ACCOUNTING SYSTEM FLOW                       │
├────────────────────────────────────────────────────────┤
│                                                          │
│  1. USER ACTION                                          │
│     ├─ Create Pledge                                     │
│     ├─ Redeem Pledge                                     │
│     ├─ Record Manual Entry                               │
│     └─ Create Voucher                                    │
│                                                          │
│  2. TRANSACTION RECORDING                                │
│     ├─ Generate Daybook Entry                            │
│     ├─ Create Double-Entry Ledger                        │
│     └─ Generate Voucher (PDF/Document)                   │
│                                                          │
│  3. LEDGER STORAGE                                       │
│     ├─ Chart of Accounts (Master)                        │
│     ├─ Ledger Entries (Journal)                          │
│     └─ Vouchers (Supporting Documents)                   │
│                                                          │
│  4. REPORTING                                            │
│     ├─ Trial Balance                                     │
│     ├─ Balance Sheet                                     │
│     ├─ P&L Statement                                     │
│     └─ Daybook Report                                    │
│                                                          │
└────────────────────────────────────────────────────────┘
```

---

## 1️⃣ DAYBOOK ENTRY SYSTEM

### What is a Daybook?

A daybook is a **chronological record of all transactions** in a single account or the entire business.

### Daybook Types

```
┌─────────────────────────────────────────┐
│         TYPES OF DAYBOOKS                │
├─────────────────────────────────────────┤
│ 1. CASH DAYBOOK                          │
│    - Records all cash/bank transactions  │
│    - Daily balance                       │
│    - Source: Cash Account entries        │
│                                          │
│ 2. PURCHASE DAYBOOK                      │
│    - Records all purchases               │
│    - Supplier details                    │
│    - Source: Purchase transactions       │
│                                          │
│ 3. SALES DAYBOOK                         │
│    - Records all sales                   │
│    - Customer details                    │
│    - Source: Sales transactions          │
│                                          │
│ 4. GENERAL DAYBOOK                       │
│    - All transactions                    │
│    - Most comprehensive                  │
│    - Source: All ledger entries          │
│                                          │
└─────────────────────────────────────────┘
```

### Daybook Entry Model

```python
# Add to models.py
class DaybookEntry(Base):
    """Daybook Entry - Chronological record of transactions."""
    __tablename__ = "daybook_entries"
    
    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False)
    daybook_type = Column(String, nullable=False)  # Cash, Purchase, Sales, General
    daybook_date = Column(DateTime, nullable=False, index=True)
    sequence_no = Column(Integer, nullable=False)  # Daily sequence
    
    # Transaction Details
    account_id = Column(Integer, ForeignKey("chart_of_accounts.id"), nullable=False)
    debit_amount = Column(Float, default=0.0)
    credit_amount = Column(Float, default=0.0)
    description = Column(String, nullable=True)
    
    # Reference Information
    reference_type = Column(String, nullable=True)  # Pledge, Redemption, etc.
    reference_id = Column(Integer, nullable=True)
    supporting_document = Column(String, nullable=True)  # Voucher reference
    
    # Running Balance
    running_debit = Column(Float, default=0.0)
    running_credit = Column(Float, default=0.0)
    
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, server_default=func.now())
```

### Daybook Entry Endpoint

```python
# GET /daybook-entries?date=2025-10-24&type=Cash&account_id=1
@router.get("/daybook-entries")
def get_daybook(
    date: datetime = Query(...),
    daybook_type: str = Query("General"),
    account_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Get daybook entries for a specific date and type.
    
    Args:
        date: Daybook date (YYYY-MM-DD)
        daybook_type: Cash, Purchase, Sales, or General
        account_id: Optional - specific account
    
    Returns:
        List of daybook entries with running balance
    """
    query = db.query(DaybookEntry).filter(
        DaybookEntry.daybook_date == date,
        DaybookEntry.daybook_type == daybook_type,
        DaybookEntry.company_id == current_user.company_id
    )
    
    if account_id:
        query = query.filter(DaybookEntry.account_id == account_id)
    
    entries = query.order_by(DaybookEntry.sequence_no).all()
    
    return {
        "date": date,
        "daybook_type": daybook_type,
        "entries": entries,
        "total_debit": sum(e.debit_amount for e in entries),
        "total_credit": sum(e.credit_amount for e in entries)
    }
```

---

## 2️⃣ VOUCHER SYSTEM

### What is a Voucher?

A voucher is a **supporting document** that provides evidence and authorization for a transaction.

### Voucher Types

```
┌─────────────────────────────────────────┐
│         TYPES OF VOUCHERS                │
├─────────────────────────────────────────┤
│ 1. PAYMENT VOUCHER (PV)                  │
│    - Cash/Bank payment out                │
│    - Payee details                       │
│    - Authorization                       │
│                                          │
│ 2. RECEIPT VOUCHER (RV)                  │
│    - Cash/Bank receipt in                │
│    - Payer details                       │
│    - Authorization                       │
│                                          │
│ 3. JOURNAL VOUCHER (JV)                  │
│    - Manual journal entry                 │
│    - Debit & Credit accounts              │
│    - Supporting details                  │
│                                          │
│ 4. CONTRA VOUCHER (CV)                   │
│    - Transfer between bank accounts      │
│    - Bank to bank                        │
│    - Authorization                       │
│                                          │
│ 5. DEBIT NOTE (DN)                       │
│    - Return of goods/adjustments         │
│    - Reduced receivable                  │
│    - Date & Amount                       │
│                                          │
│ 6. CREDIT NOTE (CN)                      │
│    - Return of goods/adjustments         │
│    - Reduced payable                     │
│    - Date & Amount                       │
│                                          │
└─────────────────────────────────────────┘
```

### Voucher Model

```python
# Add to models.py
class Voucher(Base):
    """Voucher - Supporting document for transactions."""
    __tablename__ = "vouchers"
    
    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False)
    voucher_no = Column(String, unique=True, nullable=False)  # PV-2025-001, RV-2025-001
    voucher_type = Column(String, nullable=False)  # PV, RV, JV, CV, DN, CN
    voucher_date = Column(DateTime, nullable=False)
    
    # Financial Details
    total_debit = Column(Float, nullable=False)
    total_credit = Column(Float, nullable=False)
    net_amount = Column(Float, nullable=False)
    
    # Reference Information
    reference_type = Column(String, nullable=True)  # Pledge, Redemption, etc.
    reference_id = Column(Integer, nullable=True)
    
    # Approval
    prepared_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    approved_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    approval_date = Column(DateTime, nullable=True)
    
    # Status & Tracking
    status = Column(String, default="Draft")  # Draft, Approved, Posted, Cancelled
    notes = Column(String, nullable=True)
    attachment_path = Column(String, nullable=True)  # PDF path
    
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())


class VoucherItems(Base):
    """Individual line items in a voucher."""
    __tablename__ = "voucher_items"
    
    id = Column(Integer, primary_key=True, index=True)
    voucher_id = Column(Integer, ForeignKey("vouchers.id"), nullable=False)
    
    # Account Details
    account_id = Column(Integer, ForeignKey("chart_of_accounts.id"), nullable=False)
    debit_amount = Column(Float, default=0.0)
    credit_amount = Column(Float, default=0.0)
    
    # Description
    description = Column(String, nullable=True)
    particulars = Column(String, nullable=True)  # Additional details
    
    sequence_no = Column(Integer, nullable=False)
    created_at = Column(DateTime, server_default=func.now())
```

### Voucher Creation Endpoint

```python
# POST /vouchers
@router.post("/vouchers", status_code=201)
def create_voucher(
    voucher_data: VoucherCreate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Create a new voucher with multiple line items.
    
    Body:
    {
        "voucher_type": "JV",  # Journal Voucher
        "voucher_date": "2025-10-24",
        "reference_type": "Manual",
        "notes": "Adjustment entry",
        "items": [
            {
                "account_id": 10,
                "debit_amount": 1000,
                "description": "Inventory adjustment"
            },
            {
                "account_id": 20,
                "credit_amount": 1000,
                "description": "Inventory adjustment"
            }
        ]
    }
    """
    # Generate voucher number
    prefix = voucher_data.voucher_type  # PV, RV, JV, etc.
    seq = db.query(Voucher).filter(
        Voucher.company_id == current_user.company_id,
        Voucher.voucher_type == prefix
    ).count() + 1
    voucher_no = f"{prefix}-{datetime.now().year}-{seq:04d}"
    
    # Create voucher
    db_voucher = Voucher(
        company_id=current_user.company_id,
        voucher_no=voucher_no,
        voucher_type=voucher_data.voucher_type,
        voucher_date=voucher_data.voucher_date,
        total_debit=sum(item.debit_amount for item in voucher_data.items),
        total_credit=sum(item.credit_amount for item in voucher_data.items),
        net_amount=sum(item.debit_amount for item in voucher_data.items),
        reference_type=voucher_data.reference_type,
        prepared_by=current_user.id,
        status="Draft"
    )
    
    db.add(db_voucher)
    db.flush()
    
    # Add line items
    for item in voucher_data.items:
        db_item = VoucherItems(
            voucher_id=db_voucher.id,
            account_id=item.account_id,
            debit_amount=item.debit_amount,
            credit_amount=item.credit_amount,
            description=item.description,
            sequence_no=len(db_voucher.items) + 1
        )
        db.add(db_item)
    
    db.commit()
    db.refresh(db_voucher)
    
    return db_voucher
```

---

## 3️⃣ MANUAL LEDGER TRANSACTIONS

### What is a Manual Ledger Entry?

A **manual ledger entry** is a direct journal entry made by a user to record transactions that don't automatically flow from the system.

### Types of Manual Entries

```
┌──────────────────────────────────────────┐
│    MANUAL LEDGER ENTRY TYPES              │
├──────────────────────────────────────────┤
│ 1. ADJUSTMENT ENTRY                      │
│    - Correct errors                      │
│    - Depreciation                        │
│    - Accruals                            │
│                                          │
│ 2. CLOSING ENTRY                         │
│    - Close temporary accounts            │
│    - Year-end closing                    │
│    - Transfer profits                    │
│                                          │
│ 3. OPENING ENTRY                         │
│    - Opening balances                    │
│    - Year start                          │
│    - New accounts                        │
│                                          │
│ 4. REVERSING ENTRY                       │
│    - Reverse accruals                    │
│    - Next period reversal                │
│    - Adjustment reversal                 │
│                                          │
│ 5. CORRECTION ENTRY                      │
│    - Correct posting errors              │
│    - Fix wrong accounts                  │
│    - Amount corrections                  │
│                                          │
└──────────────────────────────────────────┘
```

### Manual Entry Workflow

```
┌──────────────────────────────────────────────────┐
│         MANUAL ENTRY WORKFLOW                     │
├──────────────────────────────────────────────────┤
│                                                  │
│  1. PREPARE ENTRY                                │
│     ├─ Select accounts                           │
│     ├─ Enter debit/credit amounts                │
│     └─ Add description                           │
│                                                  │
│  2. VALIDATE ENTRY                               │
│     ├─ Check if debit = credit                   │
│     ├─ Verify accounts exist                     │
│     └─ Check user permissions                    │
│                                                  │
│  3. SAVE AS DRAFT                                │
│     ├─ Store in system                           │
│     ├─ Generate draft voucher                    │
│     └─ Allow editing                             │
│                                                  │
│  4. APPROVAL WORKFLOW (Optional)                 │
│     ├─ Manager reviews                           │
│     ├─ Comments/Approvals                        │
│     └─ Final approval                            │
│                                                  │
│  5. POST ENTRY                                   │
│     ├─ Create ledger entries                     │
│     ├─ Update running balance                    │
│     ├─ Generate daybook entry                    │
│     └─ Create audit trail                        │
│                                                  │
│  6. REPORT & TRACK                               │
│     ├─ Include in daybook                        │
│     ├─ Trial balance                             │
│     ├─ Audit trail                               │
│     └─ Historical record                         │
│                                                  │
└──────────────────────────────────────────────────┘
```

### Manual Entry Endpoint

```python
# POST /ledger-entries/manual
@router.post("/ledger-entries/manual", status_code=201)
def create_manual_entry(
    entry_data: ManualLedgerEntryCreate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Create manual ledger entries (Journal Entry).
    
    Body:
    {
        "entry_date": "2025-10-24",
        "reference_type": "Adjustment",
        "description": "Depreciation entry",
        "items": [
            {
                "account_id": 100,
                "debit": 5000,
                "description": "Depreciation expense"
            },
            {
                "account_id": 101,
                "credit": 5000,
                "description": "Accumulated depreciation"
            }
        ],
        "require_approval": true
    }
    """
    
    # Validate: Total debit = Total credit
    total_debit = sum(item.debit or 0 for item in entry_data.items)
    total_credit = sum(item.credit or 0 for item in entry_data.items)
    
    if abs(total_debit - total_credit) > 0.01:  # Allow small rounding errors
        raise HTTPException(
            status_code=400,
            detail=f"Debit ({total_debit}) must equal Credit ({total_credit})"
        )
    
    # Create entries
    entries = []
    for item in entry_data.items:
        # Debit entry
        if item.debit > 0:
            db_entry = LedgerEntriesModel(
                company_id=current_user.company_id,
                account_id=item.account_id,
                transaction_date=entry_data.entry_date,
                transaction_type="Debit",
                amount=item.debit,
                description=item.description,
                reference_type=entry_data.reference_type,
                created_by=current_user.id
            )
            entries.append(db_entry)
        
        # Credit entry
        if item.credit > 0:
            db_entry = LedgerEntriesModel(
                company_id=current_user.company_id,
                account_id=item.account_id,
                transaction_date=entry_data.entry_date,
                transaction_type="Credit",
                amount=item.credit,
                description=item.description,
                reference_type=entry_data.reference_type,
                created_by=current_user.id
            )
            entries.append(db_entry)
    
    # Save all entries
    db.add_all(entries)
    db.commit()
    
    return {
        "message": "Manual entries created successfully",
        "count": len(entries),
        "total_debit": total_debit,
        "total_credit": total_credit
    }
```

---

## 📋 Complete Implementation Checklist

### Phase 1: Database Setup
- [ ] Create `DaybookEntry` model
- [ ] Create `Voucher` model
- [ ] Create `VoucherItems` model
- [ ] Add database migrations
- [ ] Create necessary indexes

### Phase 2: API Endpoints

**Daybook Endpoints:**
- [ ] GET `/daybook-entries` - Get daybook for a date
- [ ] GET `/daybook-entries/{id}` - Get specific entry
- [ ] POST `/daybook-entries` - Create daybook entry
- [ ] GET `/daybook-report` - Generate daybook report

**Voucher Endpoints:**
- [ ] POST `/vouchers` - Create new voucher
- [ ] GET `/vouchers` - List vouchers
- [ ] GET `/vouchers/{id}` - Get specific voucher
- [ ] PUT `/vouchers/{id}` - Update voucher
- [ ] POST `/vouchers/{id}/approve` - Approve voucher
- [ ] POST `/vouchers/{id}/post` - Post voucher to ledger
- [ ] POST `/vouchers/{id}/cancel` - Cancel voucher
- [ ] GET `/vouchers/{id}/pdf` - Generate PDF

**Manual Entry Endpoints:**
- [ ] POST `/ledger-entries/manual` - Create manual entry
- [ ] GET `/ledger-entries/draft` - List draft entries
- [ ] PUT `/ledger-entries/{id}` - Edit draft entry
- [ ] POST `/ledger-entries/{id}/post` - Post entry
- [ ] GET `/ledger-entries/{id}/audit-trail` - View audit trail

### Phase 3: Validation & Security
- [ ] User authorization checks
- [ ] Double-entry validation (Debit = Credit)
- [ ] Account existence verification
- [ ] Audit trail logging
- [ ] Approval workflow

### Phase 4: Reporting
- [ ] Daybook report generation
- [ ] Trial balance report
- [ ] Account statement
- [ ] Audit trail reports

### Phase 5: Frontend Integration
- [ ] Daybook view component
- [ ] Voucher creation form
- [ ] Manual entry form
- [ ] Approval workflow UI
- [ ] Report generation UI

---

## 🔄 Integration with Existing System

Your current system already has:
- ✅ `LedgerEntries` model
- ✅ `ChartOfAccounts` model
- ✅ `create_ledger_entry` endpoint
- ✅ Running balance calculation

### How to Extend

```python
# When creating a pledge, automatically create entries:
def create_pledge(...):
    # ... create pledge ...
    
    # Create voucher
    voucher = create_loan_voucher(db, pledge)
    
    # Create daybook entry
    create_daybook_entry(db, voucher, "Pledge")
    
    # Create ledger entries
    create_pledge_ledger_entries(db, pledge, voucher)

# Reusable function for voucher creation
def create_loan_voucher(db, pledge):
    voucher = Voucher(
        company_id=pledge.company_id,
        voucher_type="RV",  # Receipt Voucher
        voucher_date=pledge.pledge_date,
        total_debit=pledge.loan_amount,
        total_credit=pledge.loan_amount,
        reference_type="Pledge",
        reference_id=pledge.id
    )
    
    # Debit: Cash/Bank
    item1 = VoucherItems(
        voucher_id=voucher.id,
        account_id=get_cash_account(db, pledge.company_id).id,
        debit_amount=pledge.loan_amount,
        description=f"Loan against pledge {pledge.pledge_no}"
    )
    
    # Credit: Pledge Liability
    item2 = VoucherItems(
        voucher_id=voucher.id,
        account_id=get_pledge_liability_account(db, pledge.company_id).id,
        credit_amount=pledge.loan_amount,
        description=f"Liability for pledge {pledge.pledge_no}"
    )
    
    db.add_all([voucher, item1, item2])
    db.commit()
    return voucher
```

---

## 💡 Best Practices

### 1. Double-Entry Rule
```
Always: Debit = Credit
Never: Post single-sided entries
Check: Validate before posting
```

### 2. Audit Trail
```python
# Log all changes
audit_log = {
    "user_id": current_user.id,
    "action": "Create voucher",
    "timestamp": datetime.now(),
    "details": voucher_data
}
```

### 3. Approval Workflow
```
Draft → Pending Approval → Approved → Posted
   ↓                           ↓
Cancel                    Rejected
```

### 4. Error Handling
```python
# Validate at every step
- Check if amounts match
- Verify accounts exist
- Ensure user has permission
- Check for duplicate entries
- Validate date ranges
```

---

## 🚀 Recommended Implementation Order

1. **Week 1:** Database models + basic CRUD endpoints
2. **Week 2:** Voucher creation & management
3. **Week 3:** Manual entry system
4. **Week 4:** Reporting & PDF generation
5. **Week 5:** Approval workflow
6. **Week 6:** Frontend integration & testing

---

## 📚 Related Documentation

- Chart of Accounts setup
- Pledge system integration
- Financial reporting
- Audit trail management

---

**Status:** Planning Complete  
**Next Step:** Create database models  
**Last Updated:** October 24, 2025
