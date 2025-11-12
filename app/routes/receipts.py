"""Receipt management routes for pledge payments."""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload
from datetime import datetime, timedelta, date
from typing import List, Optional, Dict, Any
from calendar import monthrange

from app.database import get_db
from app.auth import get_current_user
from app.models import (
    PledgeReceipt, ReceiptItem, Pledge, User, Company, Scheme
)
from app.schemas import (
    PledgeReceipt as PledgeReceiptSchema,
    PledgeReceiptCreate,
    PledgeReceiptUpdate,
    ReceiptItem as ReceiptItemSchema
)
from app.receipt_utils import (
    generate_receipt_no, create_receipt_coa_entries,
    reverse_receipt_ledger_entries, calculate_receipt_total,
    update_pledge_balance, check_full_closure
)


router = APIRouter(prefix="/api/receipts", tags=["receipts"])


@router.post("/", response_model=PledgeReceiptSchema)
def create_receipt(
    receipt_data: PledgeReceiptCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Create a new receipt with payment items.
    
    Supports:
    - Multiple pledges in one receipt
    - Multiple payment items per pledge
    - Automatic COA entry creation
    - Draft status for further editing
    
    Args:
        receipt_data: Receipt data with items
        db: Database session
        current_user: Current authenticated user
    
    Returns:
        Created receipt with all details
    
    Raises:
        HTTPException: If validation fails
    """
    try:
        # Verify company access
        company = db.query(Company).filter(Company.id == receipt_data.company_id).first()
        if not company:
            raise HTTPException(status_code=404, detail="Company not found")
        
        # Generate receipt number
        receipt_no = generate_receipt_no(db, receipt_data.company_id)
        
        # Validate receipt items
        if not receipt_data.receipt_items or len(receipt_data.receipt_items) == 0:
            raise HTTPException(status_code=400, detail="Receipt must have at least one item")
        
        # Verify all pledges exist and calculate total
        total_calculated = 0.0
        for item_data in receipt_data.receipt_items:
            pledge = db.query(Pledge).filter(Pledge.id == item_data.pledge_id).first()
            if not pledge:
                raise HTTPException(status_code=404, detail=f"Pledge {item_data.pledge_id} not found")
            
            total_calculated += item_data.total_amount_paid
        
        # Validate receipt total matches sum of items
        if abs(receipt_data.receipt_amount - total_calculated) > 0.01:  # Allow small rounding difference
            raise HTTPException(
                status_code=400,
                detail=f"Receipt amount {receipt_data.receipt_amount} doesn't match items total {total_calculated}"
            )
        
        # Create receipt
        receipt = PledgeReceipt(
            company_id=receipt_data.company_id,
            receipt_no=receipt_no,
            customer_id=receipt_data.customer_id,
            receipt_date=receipt_data.receipt_date,
            receipt_amount=receipt_data.receipt_amount,
            payment_mode=receipt_data.payment_mode,
            bank_name=receipt_data.bank_name,
            check_number=receipt_data.check_number,
            transaction_id=receipt_data.transaction_id,
            remarks=receipt_data.remarks,
            receipt_status="Draft",
            coa_entry_status="Pending",
            created_by=current_user.id
        )
        db.add(receipt)
        db.flush()
        
        # Create receipt items
        for item_data in receipt_data.receipt_items:
            receipt_item = ReceiptItem(
                receipt_id=receipt.id,
                pledge_id=item_data.pledge_id,
                principal_amount=item_data.principal_amount,
                interest_amount=item_data.interest_amount,
                discount_interest=item_data.discount_interest,
                additional_penalty=item_data.additional_penalty,
                paid_principal=item_data.paid_principal,
                paid_interest=item_data.paid_interest,
                paid_discount=item_data.paid_discount,
                paid_penalty=item_data.paid_penalty,
                payment_type=item_data.payment_type,
                total_amount_paid=item_data.total_amount_paid,
                notes=item_data.notes,
                created_by=current_user.id
            )
            db.add(receipt_item)
            
            # Update pledge close tracking for each item
            pledge = db.query(Pledge).filter(Pledge.id == item_data.pledge_id).first()
            if pledge:
                # Initialize tracking fields if null
                if pledge.total_principal_received is None:
                    pledge.total_principal_received = 0.0
                if pledge.total_interest_received is None:
                    pledge.total_interest_received = 0.0
                
                # Calculate actual received interest (after discount)
                # Received interest = paid_interest - discount given
                actual_interest_received = item_data.paid_interest - (item_data.paid_discount or 0.0)
                
                # Add current payment to totals
                pledge.total_principal_received += item_data.paid_principal
                pledge.total_interest_received += actual_interest_received
                
                # Normalize payment type for comparison (case-insensitive, trimmed)
                payment_type_normalized = item_data.payment_type.strip().lower() if item_data.payment_type else ""
                
                # Handle pledge closure based on payment type
                if payment_type_normalized in ["full payment", "redeemed", "full", "fullpayment"]:
                    # Full payment - close the pledge (customer redeemed items)
                    pledge.status = "Redeemed"
                    pledge.pledge_close_date = receipt_data.receipt_date
                elif payment_type_normalized in ["closed", "closure", "close"]:
                    # Manual closure (administrative/auction/loss)
                    pledge.status = "Closed"
                    pledge.pledge_close_date = receipt_data.receipt_date
                # For "Partial Payment", "Extension", or any other type, status remains "Active"
        
        db.commit()
        db.refresh(receipt)
        
        return receipt
        
    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error creating receipt: {str(e)}")


@router.get("/company/{company_id}", response_model=List[PledgeReceiptSchema])
def get_receipts(
    company_id: int,
    status: Optional[str] = Query(None, description="Filter by receipt status"),
    customer_id: Optional[int] = Query(None, description="Filter by customer ID"),
    payment_mode: Optional[str] = Query(None, description="Filter by payment mode"),
    from_date: Optional[str] = Query(None, description="From date (YYYY-MM-DD)"),
    to_date: Optional[str] = Query(None, description="To date (YYYY-MM-DD)"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get receipts with optional filters.
    
    Args:
        company_id: Company ID
        status: Filter by receipt status (Draft, Posted, Void, Adjusted)
        customer_id: Filter by customer ID
        payment_mode: Filter by payment mode
        from_date: Filter from date
        to_date: Filter to date
        skip: Pagination skip
        limit: Pagination limit
        db: Database session
        current_user: Current authenticated user
    
    Returns:
        List of receipts matching filters
    """
    try:
        query = db.query(PledgeReceipt).filter(PledgeReceipt.company_id == company_id)
        
        if status:
            query = query.filter(PledgeReceipt.receipt_status == status)
        
        if customer_id:
            query = query.filter(PledgeReceipt.customer_id == customer_id)
        
        if payment_mode:
            query = query.filter(PledgeReceipt.payment_mode == payment_mode)
        
        if from_date:
            from_dt = datetime.strptime(from_date, "%Y-%m-%d")
            query = query.filter(PledgeReceipt.receipt_date >= from_dt)
        
        if to_date:
            to_dt = datetime.strptime(to_date, "%Y-%m-%d")
            to_dt = to_dt.replace(hour=23, minute=59, second=59)
            query = query.filter(PledgeReceipt.receipt_date <= to_dt)
        
        receipts = query.order_by(PledgeReceipt.receipt_date.desc()).offset(skip).limit(limit).all()
        
        return receipts
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving receipts: {str(e)}")


@router.get("/customer-outstanding")
def get_customer_outstanding_pledges(
    company_id: int = Query(..., description="Company ID"),
    customer_id: int = Query(..., description="Customer ID"),
    calculation_date: Optional[date] = Query(None, description="Date for interest calculation (default: today)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Get customer's active pledges with outstanding principal and interest calculations.
    
    Calculates interest from pledge date to calculation date with the following rules:
    - First month interest is mandatory (already received at pledge creation)
    - Monthly interest calculation after first month
    - For partial months: 1-15 days = half month, 16+ days = full month
    
    Args:
        company_id: Company ID
        customer_id: Customer ID
        calculation_date: Date for interest calculation (defaults to today)
        db: Database session
        current_user: Current authenticated user
    
    Returns:
        Dictionary with:
        - pledges: List of pledge details with outstanding amounts
        - summary: Total counts and amounts
    
    Example:
        GET /api/receipts/customer-outstanding?company_id=1&customer_id=5
        GET /api/receipts/customer-outstanding?company_id=1&customer_id=5&calculation_date=2025-12-01
    """
    try:
        # Default to today if no calculation date provided
        if calculation_date is None:
            calculation_date = date.today()
        
        # Get all active pledges for customer
        pledges = (
            db.query(Pledge)
            .options(joinedload(Pledge.scheme))
            .filter(
                Pledge.company_id == company_id,
                Pledge.customer_id == customer_id,
                Pledge.status == "Active"
            )
            .all()
        )
        
        if not pledges:
            return {
                "pledges": [],
                "summary": {
                    "total_pledge_count": 0,
                    "total_principal_outstanding": 0.0,
                    "total_interest_outstanding": 0.0,
                    "final_payable_amount": 0.0
                }
            }
        
        pledge_details = []
        total_principal_outstanding = 0.0
        total_interest_outstanding = 0.0
        
        for pledge in pledges:
            # Calculate total days from pledge date to calculation date
            pledge_date = pledge.pledge_date.date() if isinstance(pledge.pledge_date, datetime) else pledge.pledge_date
            total_days = (calculation_date - pledge_date).days
            
            # Calculate principal outstanding
            principal_received = pledge.total_principal_received or 0.0
            principal_outstanding = pledge.loan_amount - principal_received
            
            # Calculate interest outstanding
            interest_outstanding = calculate_interest_outstanding(
                pledge_date=pledge_date,
                calculation_date=calculation_date,
                loan_amount=pledge.loan_amount,
                interest_rate=pledge.interest_rate,
                first_month_interest=pledge.first_month_interest,
                total_interest_received=pledge.total_interest_received or 0.0
            )
            
            # Add to totals
            total_principal_outstanding += principal_outstanding
            total_interest_outstanding += interest_outstanding
            
            # Build pledge detail
            pledge_details.append({
                "pledge_id": pledge.id,
                "pledge_no": pledge.pledge_no,
                "pledge_date": pledge_date.isoformat(),
                "scheme_name": pledge.scheme.scheme_name if pledge.scheme else "N/A",
                "pledge_amount": pledge.loan_amount,
                "due_date": pledge.due_date.isoformat() if pledge.due_date else None,
                "total_days": total_days,
                "principal_outstanding": round(principal_outstanding, 2),
                "interest_outstanding": round(interest_outstanding, 2),
                "total_outstanding": round(principal_outstanding + interest_outstanding, 2)
            })
        
        # Calculate final payable amount
        final_payable_amount = total_principal_outstanding + total_interest_outstanding
        
        return {
            "pledges": pledge_details,
            "summary": {
                "total_pledge_count": len(pledges),
                "total_principal_outstanding": round(total_principal_outstanding, 2),
                "total_interest_outstanding": round(total_interest_outstanding, 2),
                "final_payable_amount": round(final_payable_amount, 2)
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error calculating outstanding: {str(e)}")


@router.get("/{receipt_id}", response_model=PledgeReceiptSchema)
def get_receipt(
    receipt_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get a specific receipt with all items.
    
    Args:
        receipt_id: Receipt ID
        db: Database session
        current_user: Current authenticated user
    
    Returns:
        Receipt details with items
    
    Raises:
        HTTPException: If receipt not found
    """
    try:
        receipt = db.query(PledgeReceipt).filter(PledgeReceipt.id == receipt_id).first()
        if not receipt:
            raise HTTPException(status_code=404, detail="Receipt not found")
        
        return receipt
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving receipt: {str(e)}")


@router.get("/{receipt_id}/items", response_model=List[ReceiptItemSchema])
def get_receipt_items(
    receipt_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get all items in a receipt.
    
    Args:
        receipt_id: Receipt ID
        db: Database session
        current_user: Current authenticated user
    
    Returns:
        List of receipt items
    
    Raises:
        HTTPException: If receipt not found
    """
    try:
        receipt = db.query(PledgeReceipt).filter(PledgeReceipt.id == receipt_id).first()
        if not receipt:
            raise HTTPException(status_code=404, detail="Receipt not found")
        
        items = db.query(ReceiptItem).filter(ReceiptItem.receipt_id == receipt_id).all()
        
        return items
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving items: {str(e)}")


@router.put("/{receipt_id}", response_model=PledgeReceiptSchema)
def update_receipt(
    receipt_id: int,
    receipt_data: PledgeReceiptUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Update a receipt (only allowed in Draft status).
    
    Args:
        receipt_id: Receipt ID
        receipt_data: Updated receipt data
        db: Database session
        current_user: Current authenticated user
    
    Returns:
        Updated receipt
    
    Raises:
        HTTPException: If receipt not found or not in Draft status
    """
    try:
        receipt = db.query(PledgeReceipt).filter(PledgeReceipt.id == receipt_id).first()
        if not receipt:
            raise HTTPException(status_code=404, detail="Receipt not found")
        
        # Only allow updates in Draft status
        if receipt.receipt_status != "Draft":
            raise HTTPException(
                status_code=400,
                detail=f"Cannot update receipt in {receipt.receipt_status} status"
            )
        
        # Update fields
        update_data = receipt_data.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(receipt, field, value)
        
        receipt.updated_at = datetime.now()
        receipt.updated_by = current_user.id
        
        db.commit()
        
        return receipt
        
    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error updating receipt: {str(e)}")


@router.post("/{receipt_id}/post", response_model=PledgeReceiptSchema)
def post_receipt(
    receipt_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Post a receipt (create COA entries and change status to Posted).
    
    This operation:
    - Creates automatic COA entries for accounting
    - Changes receipt status to Posted
    - Updates pledge balances
    - Marks pledges as Redeemed if fully paid
    
    Args:
        receipt_id: Receipt ID
        db: Database session
        current_user: Current authenticated user
    
    Returns:
        Posted receipt
    
    Raises:
        HTTPException: If receipt not found or not in Draft status
    """
    try:
        receipt = db.query(PledgeReceipt).filter(PledgeReceipt.id == receipt_id).first()
        if not receipt:
            raise HTTPException(status_code=404, detail="Receipt not found")
        
        if receipt.receipt_status != "Draft":
            raise HTTPException(
                status_code=400,
                detail=f"Can only post receipts in Draft status, current: {receipt.receipt_status}"
            )
        
        # Create COA entries
        if not create_receipt_coa_entries(db, receipt, current_user.id):
            db.rollback()
            raise HTTPException(
                status_code=500,
                detail="Failed to create COA entries"
            )
        
        # Update pledge balances
        for item in receipt.receipt_items:
            if not update_pledge_balance(db, item.pledge_id, item.paid_principal, item.paid_interest):
                db.rollback()
                raise HTTPException(
                    status_code=500,
                    detail=f"Failed to update pledge {item.pledge_id} balance"
                )
        
        db.commit()
        
        return receipt
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error posting receipt: {str(e)}")


@router.post("/{receipt_id}/void", response_model=PledgeReceiptSchema)
def void_receipt(
    receipt_id: int,
    reason: str = Query(..., description="Reason for voiding"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Void a receipt (only allowed in Posted status).
    
    This operation:
    - Reverses all COA entries
    - Changes receipt status to Void
    - Updates pledge balances back
    
    Args:
        receipt_id: Receipt ID
        reason: Reason for voiding
        db: Database session
        current_user: Current authenticated user
    
    Returns:
        Voided receipt
    
    Raises:
        HTTPException: If receipt not found or not in Posted status
    """
    try:
        receipt = db.query(PledgeReceipt).filter(PledgeReceipt.id == receipt_id).first()
        if not receipt:
            raise HTTPException(status_code=404, detail="Receipt not found")
        
        if receipt.receipt_status not in ["Posted", "Adjusted"]:
            raise HTTPException(
                status_code=400,
                detail=f"Can only void Posted/Adjusted receipts, current: {receipt.receipt_status}"
            )
        
        # Reverse COA entries
        if not reverse_receipt_ledger_entries(db, receipt_id, receipt.company_id):
            db.rollback()
            raise HTTPException(
                status_code=500,
                detail="Failed to reverse COA entries"
            )
        
        receipt.receipt_status = "Void"
        receipt.coa_entry_status = "Pending"
        receipt.remarks = f"Void - {reason}" if receipt.remarks else f"Void - {reason}"
        receipt.updated_at = datetime.now()
        receipt.updated_by = current_user.id
        
        # Recalculate pledge balances
        for item in receipt.receipt_items:
            update_pledge_balance(db, item.pledge_id, 0, 0)
        
        db.commit()
        
        return receipt
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error voiding receipt: {str(e)}")


@router.delete("/{receipt_id}")
def delete_receipt(
    receipt_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Delete a receipt (only allowed in Draft status).
    
    Args:
        receipt_id: Receipt ID
        db: Database session
        current_user: Current authenticated user
    
    Returns:
        Success message
    
    Raises:
        HTTPException: If receipt not found or not in Draft status
    """
    try:
        receipt = db.query(PledgeReceipt).filter(PledgeReceipt.id == receipt_id).first()
        if not receipt:
            raise HTTPException(status_code=404, detail="Receipt not found")
        
        if receipt.receipt_status != "Draft":
            raise HTTPException(
                status_code=400,
                detail=f"Can only delete Draft receipts, current: {receipt.receipt_status}"
            )
        
        # Delete receipt items first
        db.query(ReceiptItem).filter(ReceiptItem.receipt_id == receipt_id).delete()
        
        # Delete receipt
        db.delete(receipt)
        db.commit()
        
        return {"detail": f"Receipt {receipt.receipt_no} deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error deleting receipt: {str(e)}")


def calculate_interest_outstanding(
    pledge_date: date,
    calculation_date: date,
    loan_amount: float,
    interest_rate: float,
    first_month_interest: float,
    total_interest_received: float
) -> float:
    """
    Calculate interest outstanding from pledge date to calculation date.
    
    Rules:
    - First month interest is mandatory and already collected
    - After first month, calculate monthly interest
    - For partial months: 1-15 days = half month interest, 16+ days = full month interest
    
    Args:
        pledge_date: Date when pledge was created
        calculation_date: Date to calculate interest up to
        loan_amount: Principal loan amount
        interest_rate: Monthly interest rate (%)
        first_month_interest: First month interest amount (already collected)
        total_interest_received: Total interest already received
    
    Returns:
        Interest outstanding amount
    """
    # Calculate total interest due
    total_interest_due = first_month_interest  # First month is mandatory
    
    # Calculate months and days between pledge date and calculation date
    current_date = date(pledge_date.year, pledge_date.month, pledge_date.day)
    
    # Move to start of next month after pledge date
    if current_date.month == 12:
        current_month_start = date(current_date.year + 1, 1, current_date.day)
    else:
        current_month_start = date(current_date.year, current_date.month + 1, current_date.day)
    
    # Calculate interest for each subsequent month
    while current_month_start <= calculation_date:
        # Calculate next month start
        if current_month_start.month == 12:
            next_month_start = date(current_month_start.year + 1, 1, current_month_start.day)
        else:
            next_month_start = date(current_month_start.year, current_month_start.month + 1, current_month_start.day)
        
        if next_month_start > calculation_date:
            # Partial month - calculate days
            days_in_period = (calculation_date - current_month_start).days + 1
            
            if days_in_period <= 15:
                # 1-15 days: half month interest
                month_interest = (loan_amount * interest_rate / 100) * 0.5
            else:
                # 16+ days: full month interest
                month_interest = loan_amount * interest_rate / 100
            
            total_interest_due += month_interest
            break
        else:
            # Full month
            month_interest = loan_amount * interest_rate / 100
            total_interest_due += month_interest
            current_month_start = next_month_start
    
    # Calculate outstanding interest
    interest_outstanding = total_interest_due - total_interest_received
    
    # Ensure non-negative
    return max(0.0, interest_outstanding)
