"""API routes for bank pledge management."""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime

from app.database import get_db
from app.models import (
    BankPledge as BankPledgeModel,
    BankPledgeItems as BankPledgeItemsModel,
    BankRedemption as BankRedemptionModel,
    Pledge as PledgeModel,
    PledgeItems as PledgeItemsModel,
    BankDetails as BankDetailsModel,
    CustomerDetails as CustomerModel,
    User as UserModel,
)
from app.schemas import (
    PledgeToBankRequest,
    PledgeToBankResponse,
    BankRedemptionRequest,
    BankRedemptionResponse,
    BankPledgeListResponse,
    BankPledgeDetailResponse,
    CancelBankPledgeRequest,
)
from app.auth import get_current_user
from app.bank_pledge_utils import (
    create_bank_pledge_ledger_entries,
    reverse_bank_pledge_ledger_entries,
    create_bank_redemption_ledger_entries,
)

router = APIRouter(prefix="/bank-pledges", tags=["bank_pledges"])


@router.post("/transfer", response_model=PledgeToBankResponse, status_code=status.HTTP_201_CREATED)
def transfer_pledge_to_bank(
    request: PledgeToBankRequest,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
):
    """
    Transfer a pledge to a bank for financing.
    
    - Calculates bank loan amount based on LTV percentage
    - Creates journal entries (reverses receivable, creates bank asset)
    - Updates pledge status to "WITH_BANK"
    - Creates audit trail of items sent to bank
    
    Business Rules:
    - Pledge must be in "Active" status
    - LTV must be between 50% and 95%
    - Valuation amount must be > 0
    """
    try:
        # Validate pledge exists and is active
        pledge = db.query(PledgeModel).filter(
            PledgeModel.id == request.pledge_id,
            PledgeModel.status == "Active"
        ).first()
        
        if not pledge:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Pledge {request.pledge_id} not found or not in Active status"
            )
        
        # Validate LTV percentage
        if not (50 <= request.ltv_percentage <= 95):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="LTV percentage must be between 50% and 95%"
            )
        
        # Validate bank details exist
        bank = db.query(BankDetailsModel).filter(
            BankDetailsModel.id == request.bank_details_id,
            BankDetailsModel.status == True
        ).first()
        
        if not bank:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Bank {request.bank_details_id} not found or inactive"
            )
        
        # Calculate bank loan amount (Valuation × LTV%)
        bank_loan_amount = request.valuation_amount * (request.ltv_percentage / 100)
        
        # Get pledge items for audit trail
        pledge_items = db.query(PledgeItemsModel).filter(
            PledgeItemsModel.pledge_id == request.pledge_id
        ).all()
        
        # Create BankPledge record
        bank_pledge = BankPledgeModel(
            company_id=pledge.company_id,
            pledge_id=request.pledge_id,
            bank_details_id=request.bank_details_id,
            transfer_date=request.transfer_date,
            gross_weight=request.gross_weight,
            net_weight=request.net_weight,
            valuation_amount=request.valuation_amount,
            ltv_percentage=request.ltv_percentage,
            bank_loan_amount=bank_loan_amount,
            original_shop_loan=pledge.loan_amount,
            outstanding_interest=pledge.first_month_interest,  # Could calculate more precisely
            status="WITH_BANK",
            bank_reference_no=request.bank_reference_no,
            remarks=request.remarks,
            created_by=current_user.id
        )
        db.add(bank_pledge)
        db.flush()
        
        # Create audit trail for items
        for item in pledge_items:
            bank_pledge_item = BankPledgeItemsModel(
                bank_pledge_id=bank_pledge.id,
                original_item_id=item.id,
                jewel_design=item.jewel_design,
                jewel_condition=item.jewel_condition,
                stone_type=item.stone_type,
                gross_weight=item.gross_weight,
                net_weight=item.net_weight,
                quantity=item.quantity
            )
            db.add(bank_pledge_item)
        
        db.flush()
        
        # Create ledger entries
        ledger_result = create_bank_pledge_ledger_entries(
            db=db,
            bank_pledge=bank_pledge,
            created_by=current_user.id,
            company_id=pledge.company_id
        )
        
        if ledger_result["status"] != "success":
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Ledger entry creation failed: {ledger_result.get('message', 'Unknown error')}"
            )
        
        # Update pledge status to WITH_BANK
        pledge.status = "WITH_BANK"
        
        db.commit()
        
        return PledgeToBankResponse(
            id=bank_pledge.id,
            pledge_id=bank_pledge.pledge_id,
            pledge_no=pledge.pledge_no,
            company_id=bank_pledge.company_id,
            bank_name=bank.bank_name,
            transfer_date=bank_pledge.transfer_date,
            gross_weight=bank_pledge.gross_weight,
            net_weight=bank_pledge.net_weight,
            valuation_amount=bank_pledge.valuation_amount,
            ltv_percentage=bank_pledge.ltv_percentage,
            bank_loan_amount=bank_pledge.bank_loan_amount,
            original_shop_loan=bank_pledge.original_shop_loan,
            outstanding_interest=bank_pledge.outstanding_interest,
            status=bank_pledge.status,
            bank_reference_no=bank_pledge.bank_reference_no,
            remarks=bank_pledge.remarks,
            created_by=bank_pledge.created_by,
            created_at=bank_pledge.created_at,
            updated_at=bank_pledge.updated_at
        )
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error transferring pledge to bank: {str(e)}"
        )


@router.get("", response_model=BankPledgeListResponse)
def list_bank_pledges(
    company_id: int,
    status: str = None,
    bank_id: int = None,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
):
    """
    Get list of bank pledges with filters.
    
    Query Parameters:
    - company_id: (required) Filter by company
    - status: (optional) Filter by status (WITH_BANK, REDEEMED, EXPIRED)
    - bank_id: (optional) Filter by bank
    """
    try:
        query = db.query(BankPledgeModel).filter(
            BankPledgeModel.company_id == company_id
        )
        
        if status:
            query = query.filter(BankPledgeModel.status == status)
        
        if bank_id:
            query = query.filter(BankPledgeModel.bank_details_id == bank_id)
        
        bank_pledges = query.all()
        
        items = []
        for bp in bank_pledges:
            pledge = db.query(PledgeModel).filter(PledgeModel.id == bp.pledge_id).first()
            customer = db.query(CustomerModel).filter(CustomerModel.id == pledge.customer_id).first()
            bank = db.query(BankDetailsModel).filter(BankDetailsModel.id == bp.bank_details_id).first()
            
            items.append({
                "id": bp.id,
                "pledge_id": bp.pledge_id,
                "pledge_no": pledge.pledge_no if pledge else "",
                "customer_name": customer.customer_name if customer else "",
                "bank_name": bank.bank_name if bank else "",
                "bank_loan_amount": bp.bank_loan_amount,
                "valuation_amount": bp.valuation_amount,
                "status": bp.status,
                "transfer_date": bp.transfer_date,
                "ltv_percentage": bp.ltv_percentage
            })
        
        return BankPledgeListResponse(total=len(items), items=items)
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching bank pledges: {str(e)}"
        )


@router.get("/{bank_pledge_id}", response_model=BankPledgeDetailResponse)
def get_bank_pledge_detail(
    bank_pledge_id: int,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
):
    """Get detailed information about a bank pledge."""
    try:
        bank_pledge = db.query(BankPledgeModel).filter(
            BankPledgeModel.id == bank_pledge_id
        ).first()
        
        if not bank_pledge:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Bank pledge {bank_pledge_id} not found"
            )
        
        pledge = db.query(PledgeModel).filter(
            PledgeModel.id == bank_pledge.pledge_id
        ).first()
        
        customer = db.query(CustomerModel).filter(
            CustomerModel.id == pledge.customer_id
        ).first()
        
        bank = db.query(BankDetailsModel).filter(
            BankDetailsModel.id == bank_pledge.bank_details_id
        ).first()
        
        items = db.query(BankPledgeItemsModel).filter(
            BankPledgeItemsModel.bank_pledge_id == bank_pledge_id
        ).all()
        
        return BankPledgeDetailResponse(
            id=bank_pledge.id,
            pledge_id=bank_pledge.pledge_id,
            pledge_no=pledge.pledge_no,
            company_id=bank_pledge.company_id,
            customer_name=customer.customer_name if customer else "",
            customer_mobile=customer.mobile_number if customer else "",
            bank_details={
                "id": bank.id,
                "bank_name": bank.bank_name,
                "account_number": bank.account_number,
                "account_holder_name": bank.account_holder_name,
                "ifsc_code": bank.ifsc_code,
                "branch_name": bank.branch_name
            },
            transfer_date=bank_pledge.transfer_date,
            gross_weight=bank_pledge.gross_weight,
            net_weight=bank_pledge.net_weight,
            valuation_amount=bank_pledge.valuation_amount,
            ltv_percentage=bank_pledge.ltv_percentage,
            bank_loan_amount=bank_pledge.bank_loan_amount,
            original_shop_loan=bank_pledge.original_shop_loan,
            outstanding_interest=bank_pledge.outstanding_interest,
            status=bank_pledge.status,
            bank_reference_no=bank_pledge.bank_reference_no,
            remarks=bank_pledge.remarks,
            items=[{
                "id": item.id,
                "jewel_design": item.jewel_design,
                "jewel_condition": item.jewel_condition,
                "stone_type": item.stone_type,
                "gross_weight": item.gross_weight,
                "net_weight": item.net_weight,
                "quantity": item.quantity
            } for item in items],
            created_at=bank_pledge.created_at,
            updated_at=bank_pledge.updated_at
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching bank pledge details: {str(e)}"
        )


@router.post("/{bank_pledge_id}/redeem", response_model=BankRedemptionResponse, status_code=status.HTTP_201_CREATED)
def redeem_pledge_from_bank(
    bank_pledge_id: int,
    request: BankRedemptionRequest,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
):
    """
    Redeem a pledge from the bank.
    
    - Creates redemption record
    - Calculates gain/loss on redemption
    - Creates ledger entries (closes bank account, records gain/loss)
    - Updates pledge status to "Redeemed"
    """
    try:
        # Validate bank pledge exists and is WITH_BANK
        bank_pledge = db.query(BankPledgeModel).filter(
            BankPledgeModel.id == bank_pledge_id,
            BankPledgeModel.status == "WITH_BANK"
        ).first()
        
        if not bank_pledge:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Bank pledge {bank_pledge_id} not found or not in WITH_BANK status"
            )
        
        # Validate amount paid >= bank loan
        if request.amount_paid_to_bank < bank_pledge.bank_loan_amount:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Amount paid ({request.amount_paid_to_bank}) must be >= bank loan ({bank_pledge.bank_loan_amount})"
            )
        
        # Calculate price difference
        price_difference = request.actual_redemption_value - bank_pledge.valuation_amount
        
        # Create BankRedemption record
        redemption = BankRedemptionModel(
            company_id=bank_pledge.company_id,
            bank_pledge_id=bank_pledge_id,
            redemption_date=request.redemption_date,
            amount_paid_to_bank=request.amount_paid_to_bank,
            interest_on_bank_loan=request.interest_on_bank_loan,
            bank_charges=request.bank_charges,
            bank_valuation=bank_pledge.valuation_amount,
            actual_redemption_value=request.actual_redemption_value,
            price_difference=price_difference,
            original_shop_interest=bank_pledge.outstanding_interest,
            interest_recovered=request.interest_recovered,
            status="REDEEMED",
            remarks=request.remarks,
            created_by=current_user.id
        )
        db.add(redemption)
        db.flush()
        
        # Create ledger entries
        ledger_result = create_bank_redemption_ledger_entries(
            db=db,
            redemption=redemption,
            bank_pledge=bank_pledge,
            created_by=current_user.id,
            company_id=bank_pledge.company_id
        )
        
        if ledger_result["status"] != "success":
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Ledger entry creation failed: {ledger_result.get('message', 'Unknown error')}"
            )
        
        # Update bank pledge status to REDEEMED
        bank_pledge.status = "REDEEMED"
        
        # Update original pledge status to REDEEMED
        pledge = db.query(PledgeModel).filter(
            PledgeModel.id == bank_pledge.pledge_id
        ).first()
        if pledge:
            pledge.status = "Redeemed"
        
        db.commit()
        
        return BankRedemptionResponse(
            id=redemption.id,
            bank_pledge_id=redemption.bank_pledge_id,
            pledge_no=pledge.pledge_no if pledge else "",
            redemption_date=redemption.redemption_date,
            amount_paid_to_bank=redemption.amount_paid_to_bank,
            interest_on_bank_loan=redemption.interest_on_bank_loan,
            bank_charges=redemption.bank_charges,
            bank_valuation=redemption.bank_valuation,
            actual_redemption_value=redemption.actual_redemption_value,
            price_difference=redemption.price_difference,
            interest_recovered=redemption.interest_recovered,
            status=redemption.status,
            created_at=redemption.created_at
        )
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error redeeming pledge from bank: {str(e)}"
        )


@router.post("/{bank_pledge_id}/cancel", status_code=status.HTTP_200_OK)
def cancel_bank_pledge(
    bank_pledge_id: int,
    request: CancelBankPledgeRequest,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
):
    """
    Cancel a bank pledge transfer (void it).
    
    - Reverses all ledger entries
    - Returns pledge to "Active" status
    - Records reason for cancellation
    """
    try:
        # Validate bank pledge exists and is WITH_BANK
        bank_pledge = db.query(BankPledgeModel).filter(
            BankPledgeModel.id == bank_pledge_id,
            BankPledgeModel.status == "WITH_BANK"
        ).first()
        
        if not bank_pledge:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Bank pledge {bank_pledge_id} not found or cannot be cancelled"
            )
        
        # Reverse ledger entries
        reversal_result = reverse_bank_pledge_ledger_entries(
            db=db,
            bank_pledge=bank_pledge,
            created_by=current_user.id
        )
        
        if reversal_result["status"] != "success":
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Ledger reversal failed: {reversal_result.get('message', 'Unknown error')}"
            )
        
        # Update bank pledge status
        bank_pledge.status = "CANCELLED"
        bank_pledge.remarks = f"Cancelled: {request.reason}"
        
        # Return pledge to Active status
        pledge = db.query(PledgeModel).filter(
            PledgeModel.id == bank_pledge.pledge_id
        ).first()
        if pledge:
            pledge.status = "Active"
        
        db.commit()
        
        return {
            "status": "success",
            "message": f"Bank pledge {bank_pledge_id} cancelled successfully",
            "reversal_entries": reversal_result.get("reversed_entries", 0)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error cancelling bank pledge: {str(e)}"
        )


@router.post("/{bank_pledge_id}/redeem-with-receipt", response_model=BankRedemptionResponse, status_code=status.HTTP_201_CREATED)
def redeem_pledge_with_receipt(
    bank_pledge_id: int,
    receipt_id: int,
    use_receipt_amount: float,
    additional_business_payment: float = 0.0,
    remarks: str = None,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
):
    """
    Redeem a bank pledge using customer receipt payment.
    
    Real-world scenario:
    - Customer pays ₹55,000 (receipt created)
    - Bank loan is ₹50,000
    - Use ₹50,000 from receipt to pay bank
    - Keep ₹5,000 as profit/cash
    
    This endpoint links the customer's receipt payment to bank redemption,
    automating the business rotation cycle.
    
    Args:
        bank_pledge_id: The bank pledge to redeem
        receipt_id: The receipt ID that has customer payment
        use_receipt_amount: Amount from receipt to apply to bank payment
        additional_business_payment: Extra cash from business (if needed)
        remarks: Optional remarks
    """
    try:
        # Validate bank pledge exists and is WITH_BANK
        bank_pledge = db.query(BankPledgeModel).filter(
            BankPledgeModel.id == bank_pledge_id,
            BankPledgeModel.status == "WITH_BANK"
        ).first()
        
        if not bank_pledge:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Bank pledge {bank_pledge_id} not found or not in WITH_BANK status"
            )
        
        # Get the receipt for reference
        from app.models import PledgeReceipt as PledgeReceiptModel
        receipt = db.query(PledgeReceiptModel).filter(
            PledgeReceiptModel.id == receipt_id
        ).first()
        
        if not receipt:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Receipt {receipt_id} not found"
            )
        
        # Calculate total payment to bank
        total_to_bank = use_receipt_amount + additional_business_payment
        
        # Validate total >= bank loan
        if total_to_bank < bank_pledge.bank_loan_amount:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Total payment ({total_to_bank}) must be >= bank loan ({bank_pledge.bank_loan_amount})"
            )
        
        # Calculate price difference
        price_difference = total_to_bank - bank_pledge.valuation_amount
        
        # Create BankRedemption record with receipt linkage
        redemption = BankRedemptionModel(
            company_id=bank_pledge.company_id,
            bank_pledge_id=bank_pledge_id,
            redemption_date=datetime.now(),
            amount_paid_to_bank=total_to_bank,
            interest_on_bank_loan=0.0,
            bank_charges=0.0,
            bank_valuation=bank_pledge.valuation_amount,
            actual_redemption_value=total_to_bank,
            price_difference=price_difference,
            original_shop_interest=bank_pledge.outstanding_interest,
            interest_recovered=0.0,
            status="REDEEMED",
            remarks=f"Customer receipt #{receipt_id} + {additional_business_payment} business payment. {remarks or ''}",
            created_by=current_user.id
        )
        db.add(redemption)
        db.flush()
        
        # Create ledger entries
        ledger_result = create_bank_redemption_ledger_entries(
            db=db,
            redemption=redemption,
            bank_pledge=bank_pledge,
            created_by=current_user.id,
            company_id=bank_pledge.company_id
        )
        
        if ledger_result["status"] != "success":
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Ledger entry creation failed: {ledger_result.get('message', 'Unknown error')}"
            )
        
        # Update bank pledge status to REDEEMED
        bank_pledge.status = "REDEEMED"
        
        # Update original pledge status to REDEEMED
        pledge = db.query(PledgeModel).filter(
            PledgeModel.id == bank_pledge.pledge_id
        ).first()
        if pledge:
            pledge.status = "Redeemed"
        
        # Mark receipt as linked to bank redemption
        receipt.remarks = f"Linked to bank redemption #{redemption.id}"
        
        db.commit()
        
        return BankRedemptionResponse(
            id=redemption.id,
            bank_pledge_id=redemption.bank_pledge_id,
            pledge_no=pledge.pledge_no if pledge else "",
            redemption_date=redemption.redemption_date,
            amount_paid_to_bank=redemption.amount_paid_to_bank,
            interest_on_bank_loan=redemption.interest_on_bank_loan,
            bank_charges=redemption.bank_charges,
            bank_valuation=redemption.bank_valuation,
            actual_redemption_value=redemption.actual_redemption_value,
            price_difference=redemption.price_difference,
            interest_recovered=redemption.interest_recovered,
            status=redemption.status,
            created_at=redemption.created_at
        )
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error redeeming pledge with receipt: {str(e)}"
        )


@router.post("/{bank_pledge_id}/check-receipt-redemption")
def check_receipt_for_redemption(
    bank_pledge_id: int,
    receipt_id: int,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
):
    """
    Check if a receipt can be used to redeem a bank pledge.
    
    Returns analysis:
    - Receipt amount vs bank loan due
    - Profit/loss if redeemed
    - Recommended action
    
    This is useful for UI to show prompts/alerts.
    """
    try:
        bank_pledge = db.query(BankPledgeModel).filter(
            BankPledgeModel.id == bank_pledge_id,
            BankPledgeModel.status == "WITH_BANK"
        ).first()
        
        if not bank_pledge:
            return {
                "can_redeem": False,
                "reason": "Bank pledge not found or not active"
            }
        
        from app.models import PledgeReceipt as PledgeReceiptModel
        receipt = db.query(PledgeReceiptModel).filter(
            PledgeReceiptModel.id == receipt_id
        ).first()
        
        if not receipt:
            return {
                "can_redeem": False,
                "reason": "Receipt not found"
            }
        
        # Check if receipt is for the same pledge
        pledge = db.query(PledgeModel).filter(
            PledgeModel.id == bank_pledge.pledge_id
        ).first()
        
        # Analyze if receipt can cover bank loan
        receipt_amount = receipt.receipt_amount
        bank_loan = bank_pledge.bank_loan_amount
        
        can_redeem = receipt_amount >= bank_loan
        shortfall = max(0, bank_loan - receipt_amount)
        profit = max(0, receipt_amount - bank_loan)
        
        return {
            "can_redeem": can_redeem,
            "bank_pledge_id": bank_pledge_id,
            "receipt_id": receipt_id,
            "pledge_no": pledge.pledge_no if pledge else "",
            "bank_loan_due": bank_loan,
            "receipt_amount": receipt_amount,
            "shortfall": shortfall,  # If receipt < bank loan
            "profit": profit,  # If receipt > bank loan
            "recommendation": "AUTO_REDEEM" if can_redeem else "PARTIAL_PAYMENT",
            "message": (
                f"Receipt amount ₹{receipt_amount} is sufficient to redeem bank loan ₹{bank_loan}. "
                f"Profit: ₹{profit}" if can_redeem 
                else f"Receipt amount ₹{receipt_amount} is insufficient for bank loan ₹{bank_loan}. "
                f"Shortfall: ₹{shortfall}"
            )
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error checking receipt for redemption: {str(e)}"
        )
