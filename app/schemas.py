"""Pydantic schemas for request/response validation."""
from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel


# Company Schemas
class CompanyBase(BaseModel):
    """Base company schema."""
    company_name: str
    address: str
    city: str
    state: str
    phone: str
    licence_no: str
    logo: Optional[str] = None
    status: bool = True


class CompanyCreate(CompanyBase):
    """Schema for creating a company."""
    pass


class CompanyUpdate(BaseModel):
    """Schema for updating a company."""
    company_name: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    phone: Optional[str] = None
    licence_no: Optional[str] = None
    logo: Optional[str] = None
    status: Optional[bool] = None


class Company(CompanyBase):
    """Company schema with database fields."""
    id: int
    created_at: datetime

    class Config:
        from_attributes = True


# User Schemas
class UserBase(BaseModel):
    """Base user schema."""
    username: str
    role: str
    status: bool = True


class UserCreate(BaseModel):
    """Schema for creating a user."""
    username: str
    password: str
    role: str
    status: bool = True


class UserUpdate(BaseModel):
    """Schema for updating a user."""
    username: Optional[str] = None
    password: Optional[str] = None
    role: Optional[str] = None
    status: Optional[bool] = None


class User(UserBase):
    """User schema with database fields (password not included in response)."""
    id: int
    created_at: datetime

    class Config:
        from_attributes = True


class UserResponse(User):
    """User response schema without sensitive data."""
    pass


class ChangePasswordRequest(BaseModel):
    """Schema for changing user password."""
    current_password: str
    new_password: str
    confirm_password: str


class ChangePasswordResponse(BaseModel):
    """Schema for change password response."""
    message: str
    user: UserResponse


# Authentication Schemas
class LoginRequest(BaseModel):
    """Schema for user login."""
    username: str
    password: str


class TokenResponse(BaseModel):
    """Schema for token response."""
    access_token: str
    token_type: str
    user: UserResponse


# JewelType Schemas
class JewelTypeBase(BaseModel):
    """Base jewel type schema."""
    jewel_name: str
    description: Optional[str] = None
    purity: Optional[str] = None
    status: bool = True


class JewelTypeCreate(JewelTypeBase):
    """Schema for creating a jewel type."""
    pass


class JewelTypeUpdate(BaseModel):
    """Schema for updating a jewel type."""
    jewel_name: Optional[str] = None
    description: Optional[str] = None
    purity: Optional[str] = None
    status: Optional[bool] = None


class JewelType(JewelTypeBase):
    """JewelType schema with database fields."""
    id: int
    created_at: datetime

    class Config:
        from_attributes = True


# JewelRate Schemas
class JewelRateBase(BaseModel):
    """Base jewel rate schema."""
    jewel_type_id: int
    rate_per_gram: float
    market_price: float
    selling_price: float
    status: bool = True


class JewelRateCreate(JewelRateBase):
    """Schema for creating a jewel rate."""
    pass


class JewelRateUpdate(BaseModel):
    """Schema for updating a jewel rate."""
    jewel_type_id: Optional[int] = None
    rate_per_gram: Optional[float] = None
    market_price: Optional[float] = None
    selling_price: Optional[float] = None
    status: Optional[bool] = None


class JewelRate(JewelRateBase):
    """JewelRate schema with database fields."""
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# BankDetails Schemas
class BankDetailsBase(BaseModel):
    """Base bank details schema."""
    bank_name: str
    account_holder_name: str
    account_number: str
    ifsc_code: str
    branch_name: Optional[str] = None
    account_type: str  # e.g., Savings, Current
    status: bool = True


class BankDetailsCreate(BankDetailsBase):
    """Schema for creating bank details."""
    pass


class BankDetailsUpdate(BaseModel):
    """Schema for updating bank details."""
    bank_name: Optional[str] = None
    account_holder_name: Optional[str] = None
    account_number: Optional[str] = None
    ifsc_code: Optional[str] = None
    branch_name: Optional[str] = None
    account_type: Optional[str] = None
    status: Optional[bool] = None


class BankDetails(BankDetailsBase):
    """BankDetails schema with database fields."""
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# Scheme Schemas
class SchemeBase(BaseModel):
    """Base scheme schema."""
    jewel_type_id: int
    scheme_name: str
    short_name: str
    prefix: str
    duration_in_months: int
    interest_rate_per_month: float
    loan_eligibility_percentage: float
    status: bool = True


class SchemeCreate(SchemeBase):
    """Schema for creating a scheme."""
    pass


class SchemeUpdate(BaseModel):
    """Schema for updating a scheme."""
    jewel_type_id: Optional[int] = None
    scheme_name: Optional[str] = None
    short_name: Optional[str] = None
    prefix: Optional[str] = None
    duration_in_months: Optional[int] = None
    interest_rate_per_month: Optional[float] = None
    loan_eligibility_percentage: Optional[float] = None
    status: Optional[bool] = None


class Scheme(SchemeBase):
    """Scheme schema with database fields."""
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# CustomerDetails Schemas
class CustomerDetailsBase(BaseModel):
    """Base customer details schema."""
    customer_name: str
    mobile_number: str
    alt_mobile_number: Optional[str] = None
    guardian_name: Optional[str] = None
    door_no: str
    street: str
    location: str
    district: str
    pincode: str
    id_proof: Optional[str] = None
    status: bool = True


class CustomerDetailsCreate(CustomerDetailsBase):
    """Schema for creating customer details."""
    pass


class CustomerDetailsUpdate(BaseModel):
    """Schema for updating customer details."""
    customer_name: Optional[str] = None
    mobile_number: Optional[str] = None
    alt_mobile_number: Optional[str] = None
    guardian_name: Optional[str] = None
    door_no: Optional[str] = None
    street: Optional[str] = None
    location: Optional[str] = None
    district: Optional[str] = None
    pincode: Optional[str] = None
    id_proof: Optional[str] = None
    status: Optional[bool] = None


class CustomerDetails(CustomerDetailsBase):
    """CustomerDetails schema with database fields."""
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# Chart of Accounts Schemas
class ChartOfAccountsBase(BaseModel):
    """Base chart of accounts schema."""
    company_id: int
    account_code: str
    account_name: str
    account_type: str  # Assets, Liabilities, Equity, Income, Expenses
    account_category: str  # Cash, Bank, Inventory, Gold Stock, etc.
    sub_account_of: Optional[int] = None
    opening_balance: float = 0.0
    description: Optional[str] = None
    status: bool = True


class ChartOfAccountsCreate(ChartOfAccountsBase):
    """Schema for creating chart of accounts."""
    pass


class ChartOfAccountsUpdate(BaseModel):
    """Schema for updating chart of accounts."""
    account_code: Optional[str] = None
    account_name: Optional[str] = None
    account_type: Optional[str] = None
    account_category: Optional[str] = None
    sub_account_of: Optional[int] = None
    opening_balance: Optional[float] = None
    description: Optional[str] = None
    status: Optional[bool] = None


class ChartOfAccounts(ChartOfAccountsBase):
    """Chart of Accounts schema with database fields."""
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# Ledger Entries Schemas
class LedgerEntriesBase(BaseModel):
    """Base ledger entries schema."""
    company_id: int
    account_id: int
    transaction_date: datetime
    transaction_type: str  # Debit, Credit
    amount: float
    description: Optional[str] = None
    reference_type: Optional[str] = None  # Pledge, Redemption, Sale, Purchase, Interest, etc.
    reference_id: Optional[int] = None
    running_balance: float = 0.0


class LedgerEntriesCreate(BaseModel):
    """Schema for creating ledger entries."""
    company_id: int
    account_id: int
    transaction_date: datetime
    transaction_type: str  # Debit, Credit
    amount: float
    description: Optional[str] = None
    reference_type: Optional[str] = None
    reference_id: Optional[int] = None


class LedgerEntriesUpdate(BaseModel):
    """Schema for updating ledger entries."""
    transaction_date: Optional[datetime] = None
    transaction_type: Optional[str] = None
    amount: Optional[float] = None
    description: Optional[str] = None
    reference_type: Optional[str] = None
    reference_id: Optional[int] = None


class LedgerEntries(LedgerEntriesBase):
    """Ledger Entries schema with database fields."""
    id: int
    created_by: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# Pledge Schemas
class PledgeItemsBase(BaseModel):
    """Base pledge items schema."""
    pledge_id: int
    jewel_type_id: int
    jewel_design: Optional[str] = None
    jewel_condition: Optional[str] = None
    stone_type: Optional[str] = None
    gross_weight: float
    net_weight: float
    quantity: int = 1


class PledgeItemsCreate(BaseModel):
    """Schema for creating pledge items."""
    jewel_type_id: int
    jewel_design: Optional[str] = None
    jewel_condition: Optional[str] = None
    stone_type: Optional[str] = None
    gross_weight: float
    net_weight: float
    quantity: int = 1


class PledgeItemsUpdate(BaseModel):
    """Schema for updating pledge items."""
    jewel_design: Optional[str] = None
    jewel_condition: Optional[str] = None
    stone_type: Optional[str] = None
    gross_weight: Optional[float] = None
    net_weight: Optional[float] = None
    quantity: Optional[int] = None


class PledgeItems(PledgeItemsBase):
    """Pledge Items schema with database fields."""
    id: int
    created_by: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class PledgeBase(BaseModel):
    """Base pledge schema."""
    company_id: int
    customer_id: int
    scheme_id: int
    pledge_date: datetime
    due_date: Optional[datetime] = None
    gross_weight: float
    net_weight: float
    maximum_value: float
    loan_amount: float
    interest_rate: float
    first_month_interest: float = 0.0
    payment_account_id: Optional[int] = None
    pledge_photo: Optional[str] = None
    status: str = "Active"
    old_pledge_no: Optional[str] = None


class PledgeCreate(BaseModel):
    """Schema for creating a pledge."""
    company_id: int
    customer_id: int
    scheme_id: int
    pledge_date: datetime
    due_date: Optional[datetime] = None
    gross_weight: float
    net_weight: float
    maximum_value: float
    loan_amount: float
    interest_rate: float
    first_month_interest: float = 0.0
    payment_account_id: Optional[int] = None
    pledge_photo: Optional[str] = None
    old_pledge_no: Optional[str] = None
    pledge_items: List[PledgeItemsCreate]  # Items in this pledge


class PledgeUpdate(BaseModel):
    """Schema for updating a pledge."""
    due_date: Optional[datetime] = None
    gross_weight: Optional[float] = None
    net_weight: Optional[float] = None
    maximum_value: Optional[float] = None
    loan_amount: Optional[float] = None
    interest_rate: Optional[float] = None
    first_month_interest: Optional[float] = None
    payment_account_id: Optional[int] = None
    pledge_photo: Optional[str] = None
    status: Optional[str] = None
    old_pledge_no: Optional[str] = None
    pledge_items: Optional[List[PledgeItemsCreate]] = None  # New items to replace existing


class Pledge(PledgeBase):
    """Pledge schema with database fields."""
    id: int
    pledge_no: str
    created_by: int
    created_at: datetime
    updated_at: datetime
    pledge_items: List[PledgeItems] = []

    class Config:
        from_attributes = True


# Receipt Item Schemas
class ReceiptItemBase(BaseModel):
    """Base receipt item schema."""
    pledge_id: int
    principal_amount: float
    interest_amount: float
    discount_interest: float = 0.0
    additional_penalty: float = 0.0
    paid_principal: float
    paid_interest: float
    paid_discount: float = 0.0
    paid_penalty: float = 0.0
    payment_type: str  # Partial, Full, Extension
    total_amount_paid: float
    notes: Optional[str] = None


class ReceiptItemCreate(ReceiptItemBase):
    """Schema for creating a receipt item."""
    pass


class ReceiptItemUpdate(BaseModel):
    """Schema for updating a receipt item."""
    principal_amount: Optional[float] = None
    interest_amount: Optional[float] = None
    discount_interest: Optional[float] = None
    additional_penalty: Optional[float] = None
    paid_principal: Optional[float] = None
    paid_interest: Optional[float] = None
    paid_discount: Optional[float] = None
    paid_penalty: Optional[float] = None
    payment_type: Optional[str] = None
    total_amount_paid: Optional[float] = None
    notes: Optional[str] = None


class ReceiptItem(ReceiptItemBase):
    """Receipt item schema with database fields."""
    id: int
    receipt_id: int
    created_at: datetime
    created_by: int

    class Config:
        from_attributes = True


# Pledge Receipt Schemas
class PledgeReceiptBase(BaseModel):
    """Base pledge receipt schema."""
    receipt_date: datetime
    receipt_amount: float
    payment_mode: str  # Cash, Check, Bank Transfer, Card, etc.
    bank_name: Optional[str] = None
    check_number: Optional[str] = None
    transaction_id: Optional[str] = None
    remarks: Optional[str] = None
    customer_id: Optional[int] = None


class PledgeReceiptCreate(PledgeReceiptBase):
    """Schema for creating a pledge receipt."""
    company_id: int
    receipt_items: List[ReceiptItemCreate]  # Items/payments in this receipt


class PledgeReceiptUpdate(BaseModel):
    """Schema for updating a pledge receipt."""
    receipt_date: Optional[datetime] = None
    receipt_amount: Optional[float] = None
    payment_mode: Optional[str] = None
    bank_name: Optional[str] = None
    check_number: Optional[str] = None
    transaction_id: Optional[str] = None
    remarks: Optional[str] = None
    customer_id: Optional[int] = None
    receipt_status: Optional[str] = None


class PledgeReceipt(PledgeReceiptBase):
    """Pledge receipt schema with database fields."""
    id: int
    receipt_no: str
    receipt_status: str
    coa_entry_status: str
    created_by: int
    created_at: datetime
    updated_at: datetime
    updated_by: Optional[int] = None
    receipt_items: List[ReceiptItem] = []

    class Config:
        from_attributes = True


# Bank Pledge Schemas
class PledgeToBankRequest(BaseModel):
    """Schema for transferring a pledge to bank."""
    pledge_id: int
    bank_details_id: int
    transfer_date: datetime
    gross_weight: float
    net_weight: float
    valuation_amount: float  # Bank's valuation
    ltv_percentage: float = 80.0  # Loan-to-Value percentage
    bank_reference_no: Optional[str] = None
    remarks: Optional[str] = None


class BankPledgeItemResponse(BaseModel):
    """Schema for bank pledge item in responses."""
    id: int
    jewel_design: Optional[str]
    jewel_condition: Optional[str]
    stone_type: Optional[str]
    gross_weight: float
    net_weight: float
    quantity: int

    class Config:
        from_attributes = True


class BankDetailsResponse(BaseModel):
    """Schema for bank details in responses."""
    id: int
    bank_name: str
    account_number: str
    account_holder_name: str
    ifsc_code: str
    branch_name: Optional[str]

    class Config:
        from_attributes = True


class PledgeToBankResponse(BaseModel):
    """Schema for pledge to bank response."""
    id: int
    pledge_id: int
    pledge_no: str
    company_id: int
    bank_name: str
    transfer_date: datetime
    gross_weight: float
    net_weight: float
    valuation_amount: float
    ltv_percentage: float
    bank_loan_amount: float
    original_shop_loan: float
    outstanding_interest: float
    status: str
    bank_reference_no: Optional[str]
    remarks: Optional[str]
    created_by: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class BankPledgeDetailResponse(BaseModel):
    """Schema for bank pledge detail response."""
    id: int
    pledge_id: int
    pledge_no: str
    company_id: int
    customer_name: str
    customer_mobile: str
    bank_details: BankDetailsResponse
    transfer_date: datetime
    gross_weight: float
    net_weight: float
    valuation_amount: float
    ltv_percentage: float
    bank_loan_amount: float
    original_shop_loan: float
    outstanding_interest: float
    status: str
    bank_reference_no: Optional[str]
    remarks: Optional[str]
    items: List[BankPledgeItemResponse]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class BankRedemptionRequest(BaseModel):
    """Schema for redeeming pledge from bank."""
    redemption_date: datetime
    amount_paid_to_bank: float
    interest_on_bank_loan: float = 0.0
    bank_charges: float = 0.0
    actual_redemption_value: float
    interest_recovered: float = 0.0
    remarks: Optional[str] = None


class BankRedemptionResponse(BaseModel):
    """Schema for bank redemption response."""
    id: int
    bank_pledge_id: int
    pledge_no: str
    redemption_date: datetime
    amount_paid_to_bank: float
    interest_on_bank_loan: float
    bank_charges: float
    bank_valuation: float
    actual_redemption_value: float
    price_difference: float
    interest_recovered: float
    status: str
    created_at: datetime

    class Config:
        from_attributes = True


class BankPledgeListItem(BaseModel):
    """Schema for bank pledge list item."""
    id: int
    pledge_id: int
    pledge_no: str
    customer_name: str
    bank_name: str
    bank_loan_amount: float
    valuation_amount: float
    status: str
    transfer_date: datetime
    ltv_percentage: float

    class Config:
        from_attributes = True


class BankPledgeListResponse(BaseModel):
    """Schema for bank pledge list response."""
    total: int
    items: List[BankPledgeListItem]


class CancelBankPledgeRequest(BaseModel):
    """Schema for cancelling bank pledge."""
    reason: str
    return_date: Optional[datetime] = None


# Expense Category Schemas
class ExpenseCategoryBase(BaseModel):
    """Base expense category schema."""
    company_id: int
    category_name: str
    category_code: str
    description: Optional[str] = None
    default_debit_account_id: Optional[int] = None
    default_credit_account_id: Optional[int] = None


class ExpenseCategoryCreate(ExpenseCategoryBase):
    """Schema for creating expense category."""
    pass


class ExpenseCategoryUpdate(BaseModel):
    """Schema for updating expense category."""
    category_name: Optional[str] = None
    category_code: Optional[str] = None
    description: Optional[str] = None
    default_debit_account_id: Optional[int] = None
    default_credit_account_id: Optional[int] = None
    is_active: Optional[bool] = None


class ExpenseCategory(ExpenseCategoryBase):
    """Expense category schema with database fields."""
    id: int
    is_active: bool
    created_by: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# Expense Ledger Account Schemas
class ExpenseLedgerAccountBase(BaseModel):
    """Base expense ledger account schema."""
    company_id: int
    account_name: str
    account_code: str
    account_type: str  # DEBIT or CREDIT
    coa_account_id: int
    expense_category_id: Optional[int] = None
    opening_balance: float = 0.0
    description: Optional[str] = None


class ExpenseLedgerAccountCreate(ExpenseLedgerAccountBase):
    """Schema for creating expense ledger account."""
    pass


class ExpenseLedgerAccountUpdate(BaseModel):
    """Schema for updating expense ledger account."""
    account_name: Optional[str] = None
    account_type: Optional[str] = None
    coa_account_id: Optional[int] = None
    expense_category_id: Optional[int] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None


class ExpenseLedgerAccount(ExpenseLedgerAccountBase):
    """Expense ledger account schema with database fields."""
    id: int
    current_balance: float
    is_active: bool
    created_by: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# Expense Transaction Schemas
class ExpenseTransactionBase(BaseModel):
    """Base expense transaction schema."""
    company_id: int
    transaction_date: datetime
    expense_category_id: int
    debit_account_id: int
    credit_account_id: int
    amount: float
    description: Optional[str] = None
    reference_no: Optional[str] = None
    payment_mode: str  # CASH, BANK, UPI, CHEQUE
    payment_reference: Optional[str] = None
    payee_name: Optional[str] = None
    payee_contact: Optional[str] = None
    remarks: Optional[str] = None


class ExpenseTransactionCreate(ExpenseTransactionBase):
    """Schema for creating expense transaction."""
    pass


class ExpenseTransactionUpdate(BaseModel):
    """Schema for updating expense transaction."""
    transaction_date: Optional[datetime] = None
    expense_category_id: Optional[int] = None
    amount: Optional[float] = None
    description: Optional[str] = None
    reference_no: Optional[str] = None
    payment_mode: Optional[str] = None
    payment_reference: Optional[str] = None
    payee_name: Optional[str] = None
    payee_contact: Optional[str] = None
    remarks: Optional[str] = None


class ExpenseTransaction(ExpenseTransactionBase):
    """Expense transaction schema with database fields."""
    id: int
    transaction_no: str
    attachment_path: Optional[str]
    ledger_entry_created: bool
    ledger_entry_ids: Optional[str]
    status: str
    approved_by: Optional[int]
    approved_at: Optional[datetime]
    rejection_reason: Optional[str]
    is_active: bool
    created_by: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ExpenseTransactionApproval(BaseModel):
    """Schema for approving/rejecting expense transaction."""
    action: str  # APPROVE or REJECT
    remarks: Optional[str] = None


class ExpenseTransactionWithDetails(ExpenseTransaction):
    """Expense transaction with category and account details."""
    category_name: Optional[str] = None
    debit_account_name: Optional[str] = None
    credit_account_name: Optional[str] = None
    created_by_username: Optional[str] = None
    approved_by_username: Optional[str] = None

    class Config:
        from_attributes = True
