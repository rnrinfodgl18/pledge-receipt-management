"""Pydantic schemas for old database tables - Read-only responses."""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


# Old Account Master Schemas
class OldAccMasterResponse(BaseModel):
    """Response schema for old account master."""
    slno: Optional[int] = None
    accode: Optional[str] = None
    accname: Optional[str] = None
    opbaldeb: Optional[float] = None
    opbalcre: Optional[float] = None
    curbaldeb: Optional[float] = None
    curbalcre: Optional[float] = None
    accttype: Optional[str] = None
    schedno: Optional[int] = None
    opbaldate: Optional[datetime] = None
    conscno: Optional[int] = None
    
    class Config:
        from_attributes = True


# Old Account Ledger Schemas
class OldAccountLedgerResponse(BaseModel):
    """Response schema for old account ledger."""
    ID: Optional[int] = None
    date: Optional[datetime] = None
    jlno: Optional[str] = None
    description: Optional[str] = None
    debit: Optional[float] = None
    credit: Optional[float] = None
    register_name: Optional[str] = Field(None, alias="register")
    
    class Config:
        from_attributes = True
        populate_by_name = True


# Old Customer Schemas
class OldCustomerResponse(BaseModel):
    """Response schema for old customer."""
    pno: Optional[str] = None
    name: Optional[str] = None
    address: Optional[str] = None
    phoneno: Optional[str] = None
    mobile: Optional[str] = None
    int_date: Optional[str] = None
    cust_refno: Optional[str] = None
    pictures: Optional[str] = None
    entrydate: Optional[datetime] = None
    
    class Config:
        from_attributes = True


# Old Jewel Description (Pledge) Schemas
class OldJewelDescResponse(BaseModel):
    """Response schema for old jewel description (pledge)."""
    jlno: Optional[str] = None
    laon_date: Optional[datetime] = None
    party_details: Optional[str] = None
    jewel_weight: Optional[str] = None
    jewel_description: Optional[str] = None
    loan_amount: Optional[float] = None
    loan_ret_amount: Optional[float] = None
    loan_interest: Optional[float] = None
    loan_ret_date: Optional[datetime] = None
    actual_maturity: Optional[datetime] = None
    maturity_date: Optional[datetime] = None
    pcode: Optional[str] = None
    vno: Optional[int] = None
    intper: Optional[float] = None
    rvno: Optional[int] = None
    splace: Optional[str] = None
    sdetails: Optional[str] = None
    currate: Optional[float] = None
    curamount: Optional[float] = None
    bvno: Optional[int] = None
    brvno: Optional[int] = None
    orgweight: Optional[float] = None
    jeweltype: Optional[str] = None
    notes: Optional[str] = None
    tagcode: Optional[str] = None
    notice1date: Optional[datetime] = None
    notice2date: Optional[datetime] = None
    notice3date: Optional[datetime] = None
    days: Optional[int] = None
    auts: Optional[int] = None
    pictures: Optional[str] = None
    register_name: Optional[str] = Field(None, alias="register")
    
    class Config:
        from_attributes = True
        populate_by_name = True


# Old Jewel Details (Pledge Items) Schemas
class OldJewelDetailsResponse(BaseModel):
    """Response schema for old jewel details (pledge items)."""
    sno: Optional[int] = None
    laon_date: Optional[datetime] = None
    jlno: Optional[str] = None
    register_name: Optional[str] = Field(None, alias="register")
    itemdet: Optional[str] = None
    qty: Optional[float] = None
    grosswt: Optional[float] = None
    netweight: Optional[float] = None
    notes: Optional[str] = None
    
    class Config:
        from_attributes = True
        populate_by_name = True
