"""CustomerDetails routes for CRUD operations."""
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.orm import Session
from sqlalchemy import or_
from app.database import get_db
from app.models import CustomerDetails as CustomerDetailsModel, ChartOfAccounts as ChartOfAccountsModel
from app import schemas
from app.auth import get_current_user
from app.file_handler import save_id_proof, delete_id_proof

customer_details_router = APIRouter(prefix="/customers", tags=["customers"])


def create_customer_coa_account(db: Session, customer: CustomerDetailsModel, company_id: int) -> bool:
    """
    Create COA account for a customer (Receivable account).
    
    Args:
        db: Database session
        customer: Customer details model
        company_id: Company ID
    
    Returns:
        True if successful
    """
    try:
        # Generate account code based on customer ID
        account_code = f"1051{str(customer.id).zfill(4)}"
        
        # Check if account code already exists
        existing = db.query(ChartOfAccountsModel).filter(
            ChartOfAccountsModel.account_code == account_code,
            ChartOfAccountsModel.company_id == company_id
        ).first()
        
        if existing:
            print(f"⚠️  COA account already exists for customer: {account_code}")
            return False
        
        # Create receivable account in COA
        db_coa_account = ChartOfAccountsModel(
            company_id=company_id,
            account_code=account_code,
            account_name=f"Customer Receivable - {customer.customer_name}",
            account_type="Assets",
            account_category="Receivables",
            opening_balance=0.0,
            description=f"Customer: {customer.customer_name} | Mobile: {customer.mobile_number} | Location: {customer.location}",
            status=True
        )
        db.add(db_coa_account)
        db.commit()
        print(f"✅ COA account created for customer: {account_code}")
        return True
    
    except Exception as e:
        db.rollback()
        print(f"❌ Error creating COA account for customer: {str(e)}")
        return False


def update_customer_coa_account(db: Session, customer: CustomerDetailsModel, company_id: int) -> bool:
    """
    Update COA account for a customer.
    
    Args:
        db: Database session
        customer: Customer details model
        company_id: Company ID
    
    Returns:
        True if successful
    """
    try:
        account_code = f"1051{str(customer.id).zfill(4)}"
        
        # Find and update customer's COA account
        coa_account = db.query(ChartOfAccountsModel).filter(
            ChartOfAccountsModel.account_code == account_code,
            ChartOfAccountsModel.company_id == company_id
        ).first()
        
        if coa_account:
            coa_account.account_name = f"Customer Receivable - {customer.customer_name}"
            coa_account.description = f"Customer: {customer.customer_name} | Mobile: {customer.mobile_number} | Location: {customer.location}"
            db.add(coa_account)
            db.commit()
            print(f"✅ COA account updated for customer: {account_code}")
            return True
        else:
            print(f"⚠️  COA account not found for customer: {account_code}")
            return False
    
    except Exception as e:
        db.rollback()
        print(f"❌ Error updating COA account: {str(e)}")
        return False


def delete_customer_coa_account(db: Session, customer_id: int, company_id: int) -> bool:
    """
    Delete COA account associated with a customer.
    
    Args:
        db: Database session
        customer_id: Customer ID
        company_id: Company ID
    
    Returns:
        True if successful
    """
    try:
        account_code = f"1051{str(customer_id).zfill(4)}"
        
        # Find and delete customer's COA account
        coa_account = db.query(ChartOfAccountsModel).filter(
            ChartOfAccountsModel.account_code == account_code,
            ChartOfAccountsModel.company_id == company_id
        ).first()
        
        if coa_account:
            db.delete(coa_account)
            db.commit()
            print(f"✅ COA account deleted for customer: {account_code}")
            return True
        else:
            print(f"⚠️  COA account not found for customer: {account_code}")
            return False
    
    except Exception as e:
        db.rollback()
        print(f"Error deleting COA account: {str(e)}")
        return False


@customer_details_router.post("/", response_model=schemas.CustomerDetails, status_code=status.HTTP_201_CREATED)
def create_customer(
    customer: schemas.CustomerDetailsCreate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Create a new customer and auto-create COA account. (Requires authentication)"""
    # Check if mobile_number already exists
    existing = db.query(CustomerDetailsModel).filter(
        CustomerDetailsModel.mobile_number == customer.mobile_number
    ).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Mobile number already exists"
        )
    
    # Create customer
    db_customer = CustomerDetailsModel(**customer.dict())
    db.add(db_customer)
    db.commit()
    db.refresh(db_customer)
    
    # Auto-create COA account for this customer (use company_id 1 as default)
    create_customer_coa_account(db, db_customer, company_id=1)
    
    return db_customer


@customer_details_router.get("/", response_model=List[schemas.CustomerDetails])
def list_customers(
    skip: int = 0,
    limit: int = 10,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """List all customers with pagination. (Requires authentication)"""
    customers = db.query(CustomerDetailsModel).offset(skip).limit(limit).all()
    return customers


@customer_details_router.get("/search", response_model=List[schemas.CustomerDetails])
def search_customers(
    q: str,
    skip: int = 0,
    limit: int = 25,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Search customers by multiple fields using case-insensitive contains.

    Returns list of customers matching query across:
    customer_name, mobile_number, alt_mobile_number, guardian_name, street, location.

    Minimum query length enforced: > 2 characters.
    """
    if not q or len(q.strip()) < 3:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Query must be at least 3 characters long"
        )

    query_text = f"%{q.strip()}%"

    # Build OR filter across relevant fields
    filters = (
        CustomerDetailsModel.customer_name.ilike(query_text),
        CustomerDetailsModel.mobile_number.ilike(query_text),
        CustomerDetailsModel.alt_mobile_number.ilike(query_text),
        CustomerDetailsModel.guardian_name.ilike(query_text),
        CustomerDetailsModel.street.ilike(query_text),
        CustomerDetailsModel.location.ilike(query_text),
    )

    customers = (
        db.query(CustomerDetailsModel)
        .filter(or_(*filters))
        .offset(skip)
        .limit(limit)
        .all()
    )

    return customers


@customer_details_router.get("/{customer_id}", response_model=schemas.CustomerDetails)
def get_customer(
    customer_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Get a specific customer by ID. (Requires authentication)"""
    db_customer = db.query(CustomerDetailsModel).filter(CustomerDetailsModel.id == customer_id).first()
    if db_customer is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Customer not found"
        )
    return db_customer


@customer_details_router.put("/{customer_id}", response_model=schemas.CustomerDetails)
def update_customer(
    customer_id: int,
    customer: schemas.CustomerDetailsUpdate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Update an existing customer and sync COA account. (Requires authentication)"""
    db_customer = db.query(CustomerDetailsModel).filter(CustomerDetailsModel.id == customer_id).first()
    if db_customer is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Customer not found"
        )
    
    # Check mobile_number uniqueness if being updated
    if customer.mobile_number and customer.mobile_number != db_customer.mobile_number:
        existing = db.query(CustomerDetailsModel).filter(
            CustomerDetailsModel.mobile_number == customer.mobile_number
        ).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Mobile number already exists"
            )
    
    # Update customer details
    update_data = customer.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_customer, field, value)
    
    db.add(db_customer)
    db.commit()
    db.refresh(db_customer)
    
    # Update associated COA account if customer name or mobile changed
    if customer.customer_name or customer.mobile_number or customer.location:
        update_customer_coa_account(db, db_customer, company_id=1)
    
    return db_customer


@customer_details_router.post("/{customer_id}/upload-id-proof", response_model=schemas.CustomerDetails)
def upload_id_proof(
    customer_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Upload customer ID proof. (Requires authentication)"""
    # Check if customer exists
    db_customer = db.query(CustomerDetailsModel).filter(CustomerDetailsModel.id == customer_id).first()
    if db_customer is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Customer not found"
        )
    
    try:
        # Delete old ID proof if exists
        if db_customer.id_proof:
            delete_id_proof(db_customer.id_proof)
        
        # Save new ID proof
        id_proof_path = save_id_proof(file, customer_id)
        
        # Update customer ID proof path
        db_customer.id_proof = id_proof_path
        db.add(db_customer)
        db.commit()
        db.refresh(db_customer)
        
        return db_customer
    
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error uploading ID proof: {str(e)}"
        )


@customer_details_router.delete("/{customer_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_customer(
    customer_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Delete a customer and associated COA account. (Requires authentication)"""
    db_customer = db.query(CustomerDetailsModel).filter(CustomerDetailsModel.id == customer_id).first()
    if db_customer is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Customer not found"
        )
    
    # Delete ID proof file if exists
    if db_customer.id_proof:
        delete_id_proof(db_customer.id_proof)
    
    # Delete associated COA account
    delete_customer_coa_account(db, customer_id, company_id=1)
    
    # Delete customer
    db.delete(db_customer)
    db.commit()
    return None
