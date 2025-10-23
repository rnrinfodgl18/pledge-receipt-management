"""SQLAlchemy ORM models."""
from sqlalchemy import Column, Integer, String, DateTime, Boolean, func, Float, ForeignKey
from app.database import Base


class Company(Base):
    """Company model."""
    __tablename__ = "companies"

    id = Column(Integer, primary_key=True, index=True)
    company_name = Column(String, index=True, nullable=False)
    address = Column(String, nullable=False)
    city = Column(String, nullable=False)
    state = Column(String, nullable=False)
    phone= Column(String, nullable=False)
    licence_no = Column(String, unique=True, nullable=False)
    logo = Column(String, nullable=True)
    status = Column(Boolean, default=True)
    created_at = Column(DateTime, server_default=func.now())


class User(Base):
    """User model."""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    password = Column(String, nullable=False)
    role = Column(String, nullable=False)
    status = Column(Boolean, default=True)
    created_at = Column(DateTime, server_default=func.now())


class JewelType(Base):
    """Jewel Type model."""
    __tablename__ = "jewel_types"

    id = Column(Integer, primary_key=True, index=True)
    jewel_name = Column(String, unique=True, index=True, nullable=False)
    description = Column(String, nullable=True)
    purity = Column(String, nullable=True)  # e.g., 24K, 22K, 18K for gold
    status = Column(Boolean, default=True)
    created_at = Column(DateTime, server_default=func.now())


class JewelRate(Base):
    """Jewel Rate model - stores rate/price for each jewel type."""
    __tablename__ = "jewel_rates"

    id = Column(Integer, primary_key=True, index=True)
    jewel_type_id = Column(Integer, ForeignKey("jewel_types.id"), nullable=False, index=True)
    rate_per_gram = Column(Float, nullable=False)  # Price per gram
    market_price = Column(Float, nullable=False)  # Current market price
    selling_price = Column(Float, nullable=False)  # Selling price
    status = Column(Boolean, default=True)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    created_at = Column(DateTime, server_default=func.now())


class BankDetails(Base):
    """Bank Details model - stores bank information."""
    __tablename__ = "bank_details"

    id = Column(Integer, primary_key=True, index=True)
    bank_name = Column(String, nullable=False)
    account_holder_name = Column(String, nullable=False)
    account_number = Column(String, unique=True, nullable=False, index=True)
    ifsc_code = Column(String, nullable=False)
    branch_name = Column(String, nullable=True)
    account_type = Column(String, nullable=False)  # e.g., Savings, Current
    status = Column(Boolean, default=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())


class Scheme(Base):
    """Scheme model - stores jewelry investment schemes."""
    __tablename__ = "schemes"

    id = Column(Integer, primary_key=True, index=True)
    jewel_type_id = Column(Integer, ForeignKey("jewel_types.id"), nullable=False, index=True)
    scheme_name = Column(String, unique=True, nullable=False, index=True)
    short_name = Column(String, unique=True, nullable=False, index=True)
    prefix = Column(String, unique=True, nullable=False)  # e.g., GLD, SLV, PLT
    duration_in_months = Column(Integer, nullable=False)  # e.g., 12, 24, 36
    interest_rate_per_month = Column(Float, nullable=False)  # Interest rate per month
    loan_eligibility_percentage = Column(Float, nullable=False, default=0.0)  # Loan eligibility %
    status = Column(Boolean, default=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())


class CustomerDetails(Base):
    """Customer Details model - stores customer information."""
    __tablename__ = "customer_details"

    id = Column(Integer, primary_key=True, index=True)
    customer_name = Column(String, nullable=False, index=True)
    mobile_number = Column(String, unique=True, nullable=False, index=True)
    alt_mobile_number = Column(String, nullable=True)
    guardian_name = Column(String, nullable=True)
    door_no = Column(String, nullable=False)
    street = Column(String, nullable=False)
    location = Column(String, nullable=False)
    district = Column(String, nullable=False)
    pincode = Column(String, nullable=False)
    id_proof = Column(String, nullable=True)  # Image URL/file path
    status = Column(Boolean, default=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())


class ChartOfAccounts(Base):
    """Chart of Accounts (COA) model - stores account setup for pawn shop."""
    __tablename__ = "chart_of_accounts"

    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False, index=True)
    account_code = Column(String, unique=True, nullable=False, index=True)  # e.g., 1000, 2000, etc.
    account_name = Column(String, nullable=False, index=True)  # e.g., Cash, Bank, Inventory, etc.
    account_type = Column(String, nullable=False)  # Assets, Liabilities, Equity, Income, Expenses
    account_category = Column(String, nullable=False)  # e.g., Cash, Bank, Inventory, Gold Stock, etc.
    sub_account_of = Column(Integer, ForeignKey("chart_of_accounts.id"), nullable=True)  # For hierarchical accounts
    opening_balance = Column(Float, default=0.0)  # Opening balance
    description = Column(String, nullable=True)
    status = Column(Boolean, default=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())


class LedgerEntries(Base):
    """Ledger Entries model - stores all transactions for pawn shop."""
    __tablename__ = "ledger_entries"

    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False, index=True)
    account_id = Column(Integer, ForeignKey("chart_of_accounts.id"), nullable=False, index=True)
    transaction_date = Column(DateTime, server_default=func.now(), nullable=False, index=True)
    transaction_type = Column(String, nullable=False)  # Debit, Credit
    amount = Column(Float, nullable=False)
    description = Column(String, nullable=True)
    reference_type = Column(String, nullable=True)  # e.g., Pledge, Redemption, Sale, Purchase, Interest, etc.
    reference_id = Column(Integer, nullable=True)  # Link to pledge ID, transaction ID, etc.
    running_balance = Column(Float, default=0.0)  # Running balance after transaction
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)  # User who created entry
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())


class Pledge(Base):
    """Pledge model - stores pledge transactions for pawn shop."""
    __tablename__ = "pledges"

    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False, index=True)
    customer_id = Column(Integer, ForeignKey("customer_details.id"), nullable=False, index=True)
    scheme_id = Column(Integer, ForeignKey("schemes.id"), nullable=False, index=True)
    pledge_no = Column(String, unique=True, nullable=False, index=True)  # e.g., GLD-2025-0001
    pledge_date = Column(DateTime, nullable=False, index=True)
    gross_weight = Column(Float, nullable=False)
    net_weight = Column(Float, nullable=False)
    maximum_value = Column(Float, nullable=False)  # Maximum value of pledged items
    loan_amount = Column(Float, nullable=False)
    interest_rate = Column(Float, nullable=False)  # Monthly interest rate
    first_month_interest = Column(Float, nullable=False, default=0.0)  # Interest for first month
    payment_account_id = Column(Integer, ForeignKey("chart_of_accounts.id"), nullable=True)  # Default cash account
    pledge_photo = Column(String, nullable=True)  # Photo URL/path
    status = Column(String, default="Active")  # Active, Closed, Redeemed, Forfeited
    old_pledge_no = Column(String, nullable=True)  # Optional - reference to old pledge
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())


class PledgeItems(Base):
    """Pledge Items model - stores individual items in a pledge."""
    __tablename__ = "pledge_items"

    id = Column(Integer, primary_key=True, index=True)
    pledge_id = Column(Integer, ForeignKey("pledges.id"), nullable=False, index=True)
    jewel_type_id = Column(Integer, ForeignKey("jewel_types.id"), nullable=False, index=True)
    jewel_design = Column(String, nullable=True)  # e.g., Ring, Necklace, Bracelet, etc.
    jewel_condition = Column(String, nullable=True)  # e.g., Good, Fair, Poor, etc.
    stone_type = Column(String, nullable=True)  # e.g., Diamond, Ruby, Sapphire, etc.
    gross_weight = Column(Float, nullable=False)
    net_weight = Column(Float, nullable=False)
    quantity = Column(Integer, default=1)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())


class PledgeReceipt(Base):
    """Pledge Receipt model - stores payment receipts for pledges."""
    __tablename__ = "pledge_receipts"

    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False, index=True)
    receipt_no = Column(String, unique=True, nullable=False, index=True)  # e.g., RCP-2025-0001
    customer_id = Column(Integer, ForeignKey("customer_details.id"), nullable=True, index=True)  # Nullable for multi-pledge receipts
    receipt_date = Column(DateTime, nullable=False, index=True)
    receipt_amount = Column(Float, nullable=False)  # Total receipt amount
    payment_mode = Column(String, nullable=False)  # Cash, Check, Bank Transfer, Card, etc.
    bank_name = Column(String, nullable=True)  # For check/transfer payments
    check_number = Column(String, nullable=True)  # For check payments
    transaction_id = Column(String, nullable=True)  # For bank transfer/card payments
    remarks = Column(String, nullable=True)
    receipt_status = Column(String, default="Draft")  # Draft, Posted, Void, Adjusted
    coa_entry_status = Column(String, default="Pending")  # Pending, Posted, Error, Manual
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    updated_by = Column(Integer, ForeignKey("users.id"), nullable=True)


class ReceiptItem(Base):
    """Receipt Item model - stores individual pledge payments in a receipt."""
    __tablename__ = "receipt_items"

    id = Column(Integer, primary_key=True, index=True)
    receipt_id = Column(Integer, ForeignKey("pledge_receipts.id"), nullable=False, index=True)
    pledge_id = Column(Integer, ForeignKey("pledges.id"), nullable=False, index=True)
    principal_amount = Column(Float, nullable=False)  # Outstanding principal at time of payment
    interest_amount = Column(Float, nullable=False)  # Outstanding interest at time of payment
    discount_interest = Column(Float, default=0.0)  # Discount given on interest
    additional_penalty = Column(Float, default=0.0)  # Additional penalty/late charges
    paid_principal = Column(Float, nullable=False)  # Actual principal paid
    paid_interest = Column(Float, nullable=False)  # Actual interest paid
    paid_discount = Column(Float, default=0.0)  # Discount amount given
    paid_penalty = Column(Float, default=0.0)  # Penalty amount paid
    payment_type = Column(String, nullable=False)  # Partial, Full, Extension
    total_amount_paid = Column(Float, nullable=False)  # paid_principal + paid_interest + paid_penalty - paid_discount
    notes = Column(String, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)

