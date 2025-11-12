"""Read-only GET endpoints for old database tables."""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from datetime import datetime
from app.database import get_db
from app.old_data_models import (
    OldAccMaster,
    OldAccountLedger,
    OldCustomer,
    OldJewelDesc,
    OldJewelDetails
)
from app.old_data_schemas import (
    OldAccMasterResponse,
    OldAccountLedgerResponse,
    OldCustomerResponse,
    OldJewelDescResponse,
    OldJewelDetailsResponse
)
from app.auth import get_current_user

# Create router
old_data_router = APIRouter(prefix="/old-data", tags=["Old Data - Read Only"])


# ========== OLD ACCOUNT MASTER ENDPOINTS ==========

@old_data_router.get("/accounts", response_model=List[OldAccMasterResponse])
def get_old_accounts(
    accode: Optional[str] = Query(None, description="Filter by account code"),
    accname: Optional[str] = Query(None, description="Search by account name"),
    accttype: Optional[str] = Query(None, description="Filter by account type"),
    limit: int = Query(100, le=1000, description="Maximum records to return"),
    offset: int = Query(0, ge=0, description="Number of records to skip"),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Get old account master records.
    
    **Read-only endpoint** - No create/update/delete operations allowed.
    """
    query = db.query(OldAccMaster)
    
    if accode:
        query = query.filter(OldAccMaster.accode == accode)
    if accname:
        query = query.filter(OldAccMaster.accname.ilike(f"%{accname}%"))
    if accttype:
        query = query.filter(OldAccMaster.accttype == accttype)
    
    return query.order_by(OldAccMaster.slno).limit(limit).offset(offset).all()


@old_data_router.get("/accounts/{slno}", response_model=OldAccMasterResponse)
def get_old_account_by_id(
    slno: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Get specific old account master record by serial number."""
    account = db.query(OldAccMaster).filter(OldAccMaster.slno == slno).first()
    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Old account with slno {slno} not found"
        )
    return account


# ========== OLD ACCOUNT LEDGER ENDPOINTS ==========

@old_data_router.get("/ledger", response_model=List[OldAccountLedgerResponse])
def get_old_ledger_entries(
    jlno: Optional[str] = Query(None, description="Filter by journal number"),
    from_date: Optional[datetime] = Query(None, description="From date (YYYY-MM-DD)"),
    to_date: Optional[datetime] = Query(None, description="To date (YYYY-MM-DD)"),
    register: Optional[str] = Query(None, description="Filter by register"),
    limit: int = Query(100, le=1000),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Get old account ledger entries.
    
    **Read-only endpoint** - No create/update/delete operations allowed.
    """
    query = db.query(OldAccountLedger)
    
    if jlno:
        query = query.filter(OldAccountLedger.jlno == jlno)
    if from_date:
        query = query.filter(OldAccountLedger.date >= from_date)
    if to_date:
        query = query.filter(OldAccountLedger.date <= to_date)
    if register:
        query = query.filter(OldAccountLedger.register.ilike(f"%{register}%"))
    
    return query.order_by(OldAccountLedger.date.desc()).limit(limit).offset(offset).all()


@old_data_router.get("/ledger/{entry_id}", response_model=OldAccountLedgerResponse)
def get_old_ledger_entry_by_id(
    entry_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Get specific old ledger entry by ID."""
    entry = db.query(OldAccountLedger).filter(OldAccountLedger.ID == entry_id).first()
    if not entry:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Old ledger entry with ID {entry_id} not found"
        )
    return entry


# ========== OLD CUSTOMER ENDPOINTS ==========

@old_data_router.get("/customers", response_model=List[OldCustomerResponse])
def get_old_customers(
    search: Optional[str] = Query(None, description="Search across name, address, mobile, phoneno, or pno"),
    name: Optional[str] = Query(None, description="Search by customer name only"),
    mobile: Optional[str] = Query(None, description="Search by mobile number only"),
    pno: Optional[str] = Query(None, description="Filter by PNO only"),
    address: Optional[str] = Query(None, description="Search by address only"),
    phoneno: Optional[str] = Query(None, description="Search by phone number only"),
    limit: int = Query(100, le=1000),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Get old customer records with flexible search.
    
    **Search Options:**
    - Use `search` parameter to search across ALL fields (name, address, mobile, phoneno, pno)
    - OR use specific parameters (name, mobile, pno, address, phoneno) to search individual fields
    
    **Examples:**
    - `/customers?search=kumar` - Searches in all fields
    - `/customers?name=kumar` - Searches only in name field
    - `/customers?mobile=98765` - Searches only in mobile field
    
    **Read-only endpoint** - No create/update/delete operations allowed.
    """
    query = db.query(OldCustomer)
    
    # Universal search across all fields
    if search:
        search_filter = f"%{search}%"
        query = query.filter(
            (OldCustomer.name.ilike(search_filter)) |
            (OldCustomer.address.ilike(search_filter)) |
            (OldCustomer.mobile.ilike(search_filter)) |
            (OldCustomer.phoneno.ilike(search_filter)) |
            (OldCustomer.pno.ilike(search_filter))
        )
    
    # Specific field searches (can be combined)
    if pno:
        query = query.filter(OldCustomer.pno.ilike(f"%{pno}%"))
    if name:
        query = query.filter(OldCustomer.name.ilike(f"%{name}%"))
    if mobile:
        query = query.filter(OldCustomer.mobile.ilike(f"%{mobile}%"))
    if address:
        query = query.filter(OldCustomer.address.ilike(f"%{address}%"))
    if phoneno:
        query = query.filter(OldCustomer.phoneno.ilike(f"%{phoneno}%"))
    
    return query.order_by(OldCustomer.entrydate.desc()).limit(limit).offset(offset).all()


@old_data_router.get("/customers/{pno}", response_model=OldCustomerResponse)
def get_old_customer_by_pno(
    pno: str,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Get specific old customer record by PNO."""
    customer = db.query(OldCustomer).filter(OldCustomer.pno == pno).first()
    if not customer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Old customer with PNO {pno} not found"
        )
    return customer


# ========== OLD JEWEL DESCRIPTION (PLEDGES) ENDPOINTS ==========

@old_data_router.get("/pledges", response_model=List[OldJewelDescResponse])
def get_old_pledges(
    jlno: Optional[str] = Query(None, description="Filter by journal number"),
    pcode: Optional[str] = Query(None, description="Filter by party code"),
    from_date: Optional[datetime] = Query(None, description="From loan date (YYYY-MM-DD)"),
    to_date: Optional[datetime] = Query(None, description="To loan date (YYYY-MM-DD)"),
    jeweltype: Optional[str] = Query(None, description="Filter by jewel type"),
    register: Optional[str] = Query(None, description="Filter by register"),
    only_active: bool = Query(True, description="Only return active pledges (loan_ret_date is NULL)"),
    limit: int = Query(100, le=1000),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Get old pledge records (jewel descriptions).
    
    **Default behavior:** Returns only active pledges (loan_ret_date IS NULL)
    
    **To get all pledges (including returned):** Set only_active=false
    
    **Read-only endpoint** - No create/update/delete operations allowed.
    """
    query = db.query(OldJewelDesc)
    
    # By default, only return active pledges (not returned yet)
    if only_active:
        query = query.filter(OldJewelDesc.loan_ret_date.is_(None))
    
    if jlno:
        query = query.filter(OldJewelDesc.jlno == jlno)
    if pcode:
        query = query.filter(OldJewelDesc.pcode == pcode)
    if from_date:
        query = query.filter(OldJewelDesc.laon_date >= from_date)
    if to_date:
        query = query.filter(OldJewelDesc.laon_date <= to_date)
    if jeweltype:
        query = query.filter(OldJewelDesc.jeweltype.ilike(f"%{jeweltype}%"))
    if register:
        query = query.filter(OldJewelDesc.register.ilike(f"%{register}%"))
    
    return query.order_by(OldJewelDesc.laon_date.desc()).limit(limit).offset(offset).all()


@old_data_router.get("/pledges/{jlno}", response_model=OldJewelDescResponse)
def get_old_pledge_by_jlno(
    jlno: str,
    only_active: bool = Query(True, description="Only return if loan_ret_date is NULL"),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Get specific old pledge record by journal number.
    
    **Default behavior:** Returns only if loan_ret_date IS NULL (active pledge)
    **To get any pledge:** Set only_active=false
    """
    query = db.query(OldJewelDesc).filter(OldJewelDesc.jlno == jlno)
    
    # By default, only return if pledge is active (not returned)
    if only_active:
        query = query.filter(OldJewelDesc.loan_ret_date.is_(None))
    
    pledge = query.first()
    
    if not pledge:
        if only_active:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Active pledge with JLNO {jlno} not found (may be already returned)"
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Pledge with JLNO {jlno} not found"
            )
    return pledge


# ========== OLD JEWEL DETAILS (PLEDGE ITEMS) ENDPOINTS ==========

@old_data_router.get("/pledge-items", response_model=List[OldJewelDetailsResponse])
def get_old_pledge_items(
    jlno: Optional[str] = Query(None, description="Filter by journal number"),
    register: Optional[str] = Query(None, description="Filter by register"),
    limit: int = Query(100, le=1000),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Get old pledge item details.
    
    **Read-only endpoint** - No create/update/delete operations allowed.
    """
    query = db.query(OldJewelDetails)
    
    if jlno:
        query = query.filter(OldJewelDetails.jlno == jlno)
    if register:
        query = query.filter(OldJewelDetails.register.ilike(f"%{register}%"))
    
    return query.order_by(OldJewelDetails.sno).limit(limit).offset(offset).all()


@old_data_router.get("/pledge-items/{sno}", response_model=OldJewelDetailsResponse)
def get_old_pledge_item_by_sno(
    sno: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Get specific old pledge item by serial number."""
    item = db.query(OldJewelDetails).filter(OldJewelDetails.sno == sno).first()
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Old pledge item with SNO {sno} not found"
        )
    return item


# ========== SUMMARY/STATS ENDPOINTS ==========

@old_data_router.get("/stats/summary")
def get_old_data_summary(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Get summary statistics of all old data tables."""
    return {
        "accounts_count": db.query(OldAccMaster).count(),
        "ledger_entries_count": db.query(OldAccountLedger).count(),
        "customers_count": db.query(OldCustomer).count(),
        "pledges_count": db.query(OldJewelDesc).count(),
        "pledge_items_count": db.query(OldJewelDetails).count(),
        "message": "All data is read-only from old tables"
    }
