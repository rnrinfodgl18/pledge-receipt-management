"""Bank Pledge utilities - Ledger integration for bank pledge transfers and redemptions."""
from sqlalchemy.orm import Session
from datetime import datetime
from app.models import (
    BankPledge as BankPledgeModel,
    BankRedemption as BankRedemptionModel,
    LedgerEntries as LedgerEntriesModel,
    ChartOfAccounts as ChartOfAccountsModel,
)


def create_bank_pledge_ledger_entries(
    db: Session,
    bank_pledge: BankPledgeModel,
    created_by: int,
    company_id: int
) -> dict:
    """
    Creates ledger entries when a pledge is transferred to a bank.
    
    Business Logic:
    1. Reverse the original customer receivable (DR Customer Receivable, CR Jewel Inventory)
    2. Create bank asset entry (DR Bank Pledge Asset Account, CR Bank Loan Payable)
    3. Record interest income separately
    
    Journal Entries Created:
    ├─ Entry 1: DR Customer Receivable (reverse) → CR Jewel Inventory
    │           Amount: original_shop_loan + outstanding_interest
    ├─ Entry 2: DR Bank Pledge Asset → CR Bank Loan Payable
    │           Amount: bank_loan_amount
    └─ Entry 3: DR Interest Receivable → CR Interest Income (optional)
                Amount: outstanding_interest
    
    Args:
        db: Database session
        bank_pledge: BankPledge model instance
        created_by: User ID who created the entry
        company_id: Company ID for the entry
        
    Returns:
        dict: {
            "status": "success" or "error",
            "entries_created": count,
            "total_debits": amount,
            "total_credits": amount,
            "details": [{...}]
        }
    """
    try:
        total_debits = 0
        total_credits = 0
        entries_created = 0
        entry_details = []
        
        # Get required COA accounts
        # Account 1051: Customer Receivable (Assets)
        customer_receivable_account = db.query(ChartOfAccountsModel).filter(
            ChartOfAccountsModel.company_id == company_id,
            ChartOfAccountsModel.account_code == "1051"
        ).first()
        
        # Account 1500: Jewel Inventory (Assets)
        jewel_inventory_account = db.query(ChartOfAccountsModel).filter(
            ChartOfAccountsModel.company_id == company_id,
            ChartOfAccountsModel.account_code == "1500"
        ).first()
        
        # Account 2100: Bank Pledge Asset (Assets) - NEW
        bank_pledge_asset_account = db.query(ChartOfAccountsModel).filter(
            ChartOfAccountsModel.company_id == company_id,
            ChartOfAccountsModel.account_code == "2100"
        ).first()
        
        # Account 2200: Bank Loan Payable (Liabilities) - NEW
        bank_loan_payable_account = db.query(ChartOfAccountsModel).filter(
            ChartOfAccountsModel.company_id == company_id,
            ChartOfAccountsModel.account_code == "2200"
        ).first()
        
        # Validate accounts exist
        if not all([customer_receivable_account, jewel_inventory_account, 
                   bank_pledge_asset_account, bank_loan_payable_account]):
            return {
                "status": "error",
                "message": "Required COA accounts not found (1051, 1500, 2100, 2200)",
                "entries_created": 0
            }
        
        # ===== Entry 1: Reverse Customer Receivable =====
        # DR: Customer Receivable (1051) = original_shop_loan + outstanding_interest
        # CR: Jewel Inventory (1500) = original_shop_loan + outstanding_interest
        
        reversal_amount = bank_pledge.original_shop_loan + bank_pledge.outstanding_interest
        
        # Debit Entry: Customer Receivable
        debit_entry = LedgerEntriesModel(
            company_id=company_id,
            account_id=customer_receivable_account.id,
            transaction_date=bank_pledge.transfer_date,
            transaction_type="Debit",
            amount=reversal_amount,
            description=f"Reverse receivable - Pledge {bank_pledge.id} transferred to {bank_pledge.bank_details_id}",
            reference_type="BankPledge",
            reference_id=bank_pledge.id,
            created_by=created_by
        )
        db.add(debit_entry)
        db.flush()
        total_debits += reversal_amount
        entries_created += 1
        entry_details.append({
            "type": "Debit",
            "account_code": "1051",
            "account_name": customer_receivable_account.account_name,
            "amount": reversal_amount,
            "description": f"Reverse receivable - Pledge {bank_pledge.id}"
        })
        
        # Credit Entry: Jewel Inventory
        credit_entry_1 = LedgerEntriesModel(
            company_id=company_id,
            account_id=jewel_inventory_account.id,
            transaction_date=bank_pledge.transfer_date,
            transaction_type="Credit",
            amount=reversal_amount,
            description=f"Transfer inventory to bank - Pledge {bank_pledge.id}",
            reference_type="BankPledge",
            reference_id=bank_pledge.id,
            created_by=created_by
        )
        db.add(credit_entry_1)
        db.flush()
        total_credits += reversal_amount
        entries_created += 1
        entry_details.append({
            "type": "Credit",
            "account_code": "1500",
            "account_name": jewel_inventory_account.account_name,
            "amount": reversal_amount,
            "description": f"Transfer inventory to bank - Pledge {bank_pledge.id}"
        })
        
        # ===== Entry 2: Create Bank Asset Entry =====
        # DR: Bank Pledge Asset (2100) = bank_loan_amount
        # CR: Bank Loan Payable (2200) = bank_loan_amount
        
        # Debit Entry: Bank Pledge Asset
        debit_entry_2 = LedgerEntriesModel(
            company_id=company_id,
            account_id=bank_pledge_asset_account.id,
            transaction_date=bank_pledge.transfer_date,
            transaction_type="Debit",
            amount=bank_pledge.bank_loan_amount,
            description=f"Bank financing received - Pledge {bank_pledge.id} with LTV {bank_pledge.ltv_percentage}%",
            reference_type="BankPledge",
            reference_id=bank_pledge.id,
            created_by=created_by
        )
        db.add(debit_entry_2)
        db.flush()
        total_debits += bank_pledge.bank_loan_amount
        entries_created += 1
        entry_details.append({
            "type": "Debit",
            "account_code": "2100",
            "account_name": bank_pledge_asset_account.account_name,
            "amount": bank_pledge.bank_loan_amount,
            "description": f"Bank financing received - LTV {bank_pledge.ltv_percentage}%"
        })
        
        # Credit Entry: Bank Loan Payable
        credit_entry_2 = LedgerEntriesModel(
            company_id=company_id,
            account_id=bank_loan_payable_account.id,
            transaction_date=bank_pledge.transfer_date,
            transaction_type="Credit",
            amount=bank_pledge.bank_loan_amount,
            description=f"Bank loan liability created - Amount {bank_pledge.bank_loan_amount}",
            reference_type="BankPledge",
            reference_id=bank_pledge.id,
            created_by=created_by
        )
        db.add(credit_entry_2)
        db.flush()
        total_credits += bank_pledge.bank_loan_amount
        entries_created += 1
        entry_details.append({
            "type": "Credit",
            "account_code": "2200",
            "account_name": bank_loan_payable_account.account_name,
            "amount": bank_pledge.bank_loan_amount,
            "description": f"Bank loan liability created"
        })
        
        # Validate balance
        if total_debits != total_credits:
            return {
                "status": "error",
                "message": f"Ledger entries not balanced. Debits: {total_debits}, Credits: {total_credits}",
                "entries_created": 0
            }
        
        # Update bank pledge account if specified
        if bank_pledge.bank_account_id is None:
            bank_pledge.bank_account_id = bank_pledge_asset_account.id
        
        db.commit()
        
        return {
            "status": "success",
            "entries_created": entries_created,
            "total_debits": total_debits,
            "total_credits": total_credits,
            "details": entry_details
        }
        
    except Exception as e:
        db.rollback()
        return {
            "status": "error",
            "message": str(e),
            "entries_created": 0
        }


def reverse_bank_pledge_ledger_entries(
    db: Session,
    bank_pledge: BankPledgeModel,
    created_by: int
) -> dict:
    """
    Reverses all ledger entries for a bank pledge when it's cancelled.
    
    Creates reversing entries (opposite of original entries) to maintain audit trail.
    
    Args:
        db: Database session
        bank_pledge: BankPledge model instance to reverse
        created_by: User ID who created the reversal
        
    Returns:
        dict: {
            "status": "success" or "error",
            "reversed_entries": count,
            "total_reversed": amount
        }
    """
    try:
        # Get all original entries for this bank pledge
        original_entries = db.query(LedgerEntriesModel).filter(
            LedgerEntriesModel.reference_type == "BankPledge",
            LedgerEntriesModel.reference_id == bank_pledge.id
        ).all()
        
        if not original_entries:
            return {
                "status": "error",
                "message": "No ledger entries found for this bank pledge",
                "reversed_entries": 0
            }
        
        reversed_count = 0
        total_reversed = 0
        
        # Create reversing entries (opposite type)
        for original_entry in original_entries:
            # Reverse transaction type (Debit becomes Credit, Credit becomes Debit)
            reversed_type = "Credit" if original_entry.transaction_type == "Debit" else "Debit"
            
            reversing_entry = LedgerEntriesModel(
                company_id=original_entry.company_id,
                account_id=original_entry.account_id,
                transaction_date=datetime.now(),
                transaction_type=reversed_type,
                amount=original_entry.amount,
                description=f"REVERSAL: {original_entry.description}",
                reference_type="BankPledgeReversal",
                reference_id=bank_pledge.id,
                created_by=created_by
            )
            db.add(reversing_entry)
            reversed_count += 1
            total_reversed += original_entry.amount
        
        db.commit()
        
        return {
            "status": "success",
            "reversed_entries": reversed_count,
            "total_reversed": total_reversed
        }
        
    except Exception as e:
        db.rollback()
        return {
            "status": "error",
            "message": str(e),
            "reversed_entries": 0
        }


def create_bank_redemption_ledger_entries(
    db: Session,
    redemption: BankRedemptionModel,
    bank_pledge: BankPledgeModel,
    created_by: int,
    company_id: int
) -> dict:
    """
    Creates ledger entries when a pledged item is redeemed from the bank.
    
    Business Logic:
    1. Reverse bank pledge entries (close the bank financing)
    2. Record cash payment to bank (principal + interest + charges)
    3. Record gain/loss on redemption if price differs from valuation
    4. Optionally restore customer receivable if item is not sold
    
    Journal Entries Created:
    ├─ Entry 1: DR Bank Loan Payable → CR Cash (pay principal to bank)
    │           Amount: amount_paid_to_bank
    ├─ Entry 2: DR Bank Interest Expense → CR Cash (pay interest to bank)
    │           Amount: interest_on_bank_loan
    ├─ Entry 3: DR Bank Charges Expense → CR Cash (pay charges to bank)
    │           Amount: bank_charges
    ├─ Entry 4: DR Cash → CR Gain/Loss Account (if price difference)
    │           Amount: price_difference
    └─ Entry 5: DR Jewel Inventory → CR Customer Receivable (restore if needed)
                Amount: original_shop_loan
    
    Args:
        db: Database session
        redemption: BankRedemption model instance
        bank_pledge: Related BankPledge model
        created_by: User ID
        company_id: Company ID
        
    Returns:
        dict: Status, entries created, totals
    """
    try:
        total_debits = 0
        total_credits = 0
        entries_created = 0
        entry_details = []
        
        # Get required COA accounts
        # Account 1000: Cash (Assets)
        cash_account = db.query(ChartOfAccountsModel).filter(
            ChartOfAccountsModel.company_id == company_id,
            ChartOfAccountsModel.account_code == "1000"
        ).first()
        
        # Account 2200: Bank Loan Payable (Liabilities)
        bank_loan_payable_account = db.query(ChartOfAccountsModel).filter(
            ChartOfAccountsModel.company_id == company_id,
            ChartOfAccountsModel.account_code == "2200"
        ).first()
        
        # Account 5300: Bank Interest Expense
        interest_expense_account = db.query(ChartOfAccountsModel).filter(
            ChartOfAccountsModel.company_id == company_id,
            ChartOfAccountsModel.account_code == "5300"
        ).first()
        
        # Account 5400: Bank Charges Expense
        charges_expense_account = db.query(ChartOfAccountsModel).filter(
            ChartOfAccountsModel.company_id == company_id,
            ChartOfAccountsModel.account_code == "5400"
        ).first()
        
        # Account 4200: Gain/Loss on Pledges
        gain_loss_account = db.query(ChartOfAccountsModel).filter(
            ChartOfAccountsModel.company_id == company_id,
            ChartOfAccountsModel.account_code == "4200"
        ).first()
        
        # Account 1051: Customer Receivable
        customer_receivable_account = db.query(ChartOfAccountsModel).filter(
            ChartOfAccountsModel.company_id == company_id,
            ChartOfAccountsModel.account_code == "1051"
        ).first()
        
        # Account 1500: Jewel Inventory
        jewel_inventory_account = db.query(ChartOfAccountsModel).filter(
            ChartOfAccountsModel.company_id == company_id,
            ChartOfAccountsModel.account_code == "1500"
        ).first()
        
        if not all([cash_account, bank_loan_payable_account, interest_expense_account,
                   charges_expense_account, gain_loss_account]):
            return {
                "status": "error",
                "message": "Required COA accounts not found",
                "entries_created": 0
            }
        
        # ===== Entry 1: Pay Bank Loan Principal =====
        # DR: Bank Loan Payable (2200) = amount_paid_to_bank
        # CR: Cash (1000) = amount_paid_to_bank
        
        debit_entry_1 = LedgerEntriesModel(
            company_id=company_id,
            account_id=bank_loan_payable_account.id,
            transaction_date=redemption.redemption_date,
            transaction_type="Debit",
            amount=redemption.amount_paid_to_bank,
            description=f"Redeem bank pledge - Pay principal to bank",
            reference_type="BankRedemption",
            reference_id=redemption.id,
            created_by=created_by
        )
        db.add(debit_entry_1)
        db.flush()
        total_debits += redemption.amount_paid_to_bank
        entries_created += 1
        entry_details.append({
            "type": "Debit",
            "account_code": "2200",
            "account_name": "Bank Loan Payable",
            "amount": redemption.amount_paid_to_bank
        })
        
        credit_entry_1 = LedgerEntriesModel(
            company_id=company_id,
            account_id=cash_account.id,
            transaction_date=redemption.redemption_date,
            transaction_type="Credit",
            amount=redemption.amount_paid_to_bank,
            description=f"Redeem bank pledge - Cash payment for principal",
            reference_type="BankRedemption",
            reference_id=redemption.id,
            created_by=created_by
        )
        db.add(credit_entry_1)
        db.flush()
        total_credits += redemption.amount_paid_to_bank
        entries_created += 1
        entry_details.append({
            "type": "Credit",
            "account_code": "1000",
            "account_name": "Cash",
            "amount": redemption.amount_paid_to_bank
        })
        
        # ===== Entry 2: Pay Bank Interest =====
        if redemption.interest_on_bank_loan > 0:
            debit_entry_2 = LedgerEntriesModel(
                company_id=company_id,
                account_id=interest_expense_account.id,
                transaction_date=redemption.redemption_date,
                transaction_type="Debit",
                amount=redemption.interest_on_bank_loan,
                description=f"Bank interest on pledged item financing",
                reference_type="BankRedemption",
                reference_id=redemption.id,
                created_by=created_by
            )
            db.add(debit_entry_2)
            db.flush()
            total_debits += redemption.interest_on_bank_loan
            entries_created += 1
            
            credit_entry_2 = LedgerEntriesModel(
                company_id=company_id,
                account_id=cash_account.id,
                transaction_date=redemption.redemption_date,
                transaction_type="Credit",
                amount=redemption.interest_on_bank_loan,
                description=f"Cash payment for bank interest",
                reference_type="BankRedemption",
                reference_id=redemption.id,
                created_by=created_by
            )
            db.add(credit_entry_2)
            db.flush()
            total_credits += redemption.interest_on_bank_loan
            entries_created += 1
        
        # ===== Entry 3: Pay Bank Charges =====
        if redemption.bank_charges > 0:
            debit_entry_3 = LedgerEntriesModel(
                company_id=company_id,
                account_id=charges_expense_account.id,
                transaction_date=redemption.redemption_date,
                transaction_type="Debit",
                amount=redemption.bank_charges,
                description=f"Bank charges for pledge redemption",
                reference_type="BankRedemption",
                reference_id=redemption.id,
                created_by=created_by
            )
            db.add(debit_entry_3)
            db.flush()
            total_debits += redemption.bank_charges
            entries_created += 1
            
            credit_entry_3 = LedgerEntriesModel(
                company_id=company_id,
                account_id=cash_account.id,
                transaction_date=redemption.redemption_date,
                transaction_type="Credit",
                amount=redemption.bank_charges,
                description=f"Cash payment for bank charges",
                reference_type="BankRedemption",
                reference_id=redemption.id,
                created_by=created_by
            )
            db.add(credit_entry_3)
            db.flush()
            total_credits += redemption.bank_charges
            entries_created += 1
        
        # ===== Entry 4: Record Gain/Loss on Sale =====
        # If price_difference > 0: Gain (CR Gain/Loss Account)
        # If price_difference < 0: Loss (DR Gain/Loss Account)
        
        if redemption.price_difference != 0:
            if redemption.price_difference > 0:
                # GAIN: DR Cash, CR Gain/Loss
                debit_entry_4 = LedgerEntriesModel(
                    company_id=company_id,
                    account_id=cash_account.id,
                    transaction_date=redemption.redemption_date,
                    transaction_type="Debit",
                    amount=redemption.price_difference,
                    description=f"Gain on pledge sale - Sold at higher price",
                    reference_type="BankRedemption",
                    reference_id=redemption.id,
                    created_by=created_by
                )
                db.add(debit_entry_4)
                db.flush()
                total_debits += redemption.price_difference
                entries_created += 1
                
                credit_entry_4 = LedgerEntriesModel(
                    company_id=company_id,
                    account_id=gain_loss_account.id,
                    transaction_date=redemption.redemption_date,
                    transaction_type="Credit",
                    amount=redemption.price_difference,
                    description=f"Gain on pledge sale",
                    reference_type="BankRedemption",
                    reference_id=redemption.id,
                    created_by=created_by
                )
                db.add(credit_entry_4)
                db.flush()
                total_credits += redemption.price_difference
                entries_created += 1
            else:
                # LOSS: DR Gain/Loss, CR Cash
                debit_entry_4 = LedgerEntriesModel(
                    company_id=company_id,
                    account_id=gain_loss_account.id,
                    transaction_date=redemption.redemption_date,
                    transaction_type="Debit",
                    amount=abs(redemption.price_difference),
                    description=f"Loss on pledge sale - Sold at lower price",
                    reference_type="BankRedemption",
                    reference_id=redemption.id,
                    created_by=created_by
                )
                db.add(debit_entry_4)
                db.flush()
                total_debits += abs(redemption.price_difference)
                entries_created += 1
                
                credit_entry_4 = LedgerEntriesModel(
                    company_id=company_id,
                    account_id=cash_account.id,
                    transaction_date=redemption.redemption_date,
                    transaction_type="Credit",
                    amount=abs(redemption.price_difference),
                    description=f"Loss on pledge sale",
                    reference_type="BankRedemption",
                    reference_id=redemption.id,
                    created_by=created_by
                )
                db.add(credit_entry_4)
                db.flush()
                total_credits += abs(redemption.price_difference)
                entries_created += 1
        
        # ===== Entry 5: Restore Customer Receivable (if continuing transaction) =====
        # Optional: if customer will continue pledging, restore the receivable
        # DR: Jewel Inventory, CR: Customer Receivable
        
        if bank_pledge and bank_pledge.original_shop_loan > 0:
            if customer_receivable_account and jewel_inventory_account:
                debit_entry_5 = LedgerEntriesModel(
                    company_id=company_id,
                    account_id=jewel_inventory_account.id,
                    transaction_date=redemption.redemption_date,
                    transaction_type="Debit",
                    amount=bank_pledge.original_shop_loan,
                    description=f"Restore inventory on redemption from bank",
                    reference_type="BankRedemption",
                    reference_id=redemption.id,
                    created_by=created_by
                )
                db.add(debit_entry_5)
                db.flush()
                total_debits += bank_pledge.original_shop_loan
                entries_created += 1
                
                credit_entry_5 = LedgerEntriesModel(
                    company_id=company_id,
                    account_id=customer_receivable_account.id,
                    transaction_date=redemption.redemption_date,
                    transaction_type="Credit",
                    amount=bank_pledge.original_shop_loan,
                    description=f"Restore customer receivable on redemption",
                    reference_type="BankRedemption",
                    reference_id=redemption.id,
                    created_by=created_by
                )
                db.add(credit_entry_5)
                db.flush()
                total_credits += bank_pledge.original_shop_loan
                entries_created += 1
        
        # Validate balance
        if total_debits != total_credits:
            return {
                "status": "error",
                "message": f"Ledger entries not balanced. Debits: {total_debits}, Credits: {total_credits}",
                "entries_created": 0
            }
        
        db.commit()
        
        return {
            "status": "success",
            "entries_created": entries_created,
            "total_debits": total_debits,
            "total_credits": total_credits,
            "details": entry_details
        }
        
    except Exception as e:
        db.rollback()
        return {
            "status": "error",
            "message": str(e),
            "entries_created": 0
        }
