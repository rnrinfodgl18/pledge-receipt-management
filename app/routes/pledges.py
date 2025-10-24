"""API routes for pledge management with automatic ledger integration."""
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from sqlalchemy.orm import Session
from datetime import datetime
from typing import List

from app.database import get_db
from app.models import (
    Pledge as PledgeModel,
    PledgeItems as PledgeItemsModel,
    Scheme as SchemeModel,
    CustomerDetails as CustomerModel,
    User as UserModel,
    ChartOfAccounts as ChartOfAccountsModel,
)
from app.schemas import (
    PledgeCreate,
    PledgeUpdate,
    Pledge as PledgeSchema,
    PledgeItems as PledgeItemsSchema,
)
from app.auth import get_current_user
from app.pledge_utils import (
    generate_pledge_no,
    create_pledge_ledger_entries,
    reverse_pledge_ledger_entries,
)
from app.file_handler import save_pledge_photo, delete_pledge_photo

router = APIRouter(prefix="/pledges", tags=["pledges"])


@router.post("/", response_model=PledgeSchema, status_code=status.HTTP_201_CREATED)
def create_pledge(
    pledge_data: PledgeCreate,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
):
    """
    Create a new pledge with automatic ledger transaction creation.
    
    - Generates unique pledge number with scheme prefix
    - Creates pledge with nested items
    - Automatically creates ledger entries for financial tracking
    - Sets default payment account to Cash if not specified
    
    Example pledge_no generated: GLD-2025-0001
    """
    try:
        # Validate company exists
        if pledge_data.company_id != current_user.company_id and current_user.role != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to create pledge for this company",
            )
        
        # Validate customer exists
        customer = db.query(CustomerModel).filter(
            CustomerModel.id == pledge_data.customer_id,
            CustomerModel.company_id == pledge_data.company_id,
        ).first()
        if not customer:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Customer {pledge_data.customer_id} not found",
            )
        
        # Validate scheme exists
        scheme = db.query(SchemeModel).filter(
            SchemeModel.id == pledge_data.scheme_id,
            SchemeModel.company_id == pledge_data.company_id,
        ).first()
        if not scheme:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Scheme {pledge_data.scheme_id} not found",
            )
        
        # Validate payment account if specified
        if pledge_data.payment_account_id:
            account = db.query(ChartOfAccountsModel).filter(
                ChartOfAccountsModel.id == pledge_data.payment_account_id,
                ChartOfAccountsModel.company_id == pledge_data.company_id,
            ).first()
            if not account:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Payment account not found",
                )
        else:
            # Default to Cash account
            cash_account = db.query(ChartOfAccountsModel).filter(
                ChartOfAccountsModel.account_code == "1000",
                ChartOfAccountsModel.company_id == pledge_data.company_id,
            ).first()
            pledge_data.payment_account_id = cash_account.id if cash_account else None
        
        # Generate pledge number
        pledge_no = generate_pledge_no(db, pledge_data.scheme_id, pledge_data.company_id)
        
        # Calculate first month interest if not provided
        if not pledge_data.first_month_interest:
            monthly_rate = (pledge_data.interest_rate or scheme.interest_rate_per_month) / 100
            pledge_data.first_month_interest = pledge_data.loan_amount * monthly_rate
        
        # Create pledge
        new_pledge = PledgeModel(
            company_id=pledge_data.company_id,
            pledge_no=pledge_no,
            customer_id=pledge_data.customer_id,
            scheme_id=pledge_data.scheme_id,
            pledge_date=pledge_data.pledge_date or datetime.now().date(),
            gross_weight=pledge_data.gross_weight,
            net_weight=pledge_data.net_weight,
            maximum_value=pledge_data.maximum_value,
            loan_amount=pledge_data.loan_amount,
            interest_rate=pledge_data.interest_rate or scheme.interest_rate_per_month,
            first_month_interest=pledge_data.first_month_interest,
            payment_account_id=pledge_data.payment_account_id,
            pledge_photo=pledge_data.pledge_photo,
            status="Active",
            old_pledge_no=pledge_data.old_pledge_no,
            created_by=current_user.id,
        )
        
        db.add(new_pledge)
        db.flush()  # Get the pledge ID
        
        # Create pledge items
        for item_data in pledge_data.pledge_items:
            pledge_item = PledgeItemsModel(
                pledge_id=new_pledge.id,
                jewel_type_id=item_data.jewel_type_id,
                jewel_design=item_data.jewel_design,
                jewel_condition=item_data.jewel_condition,
                stone_type=item_data.stone_type,
                gross_weight=item_data.gross_weight,
                net_weight=item_data.net_weight,
                quantity=item_data.quantity,
                created_by=current_user.id,
            )
            db.add(pledge_item)
        
        db.commit()
        db.refresh(new_pledge)
        
        # Create automatic ledger entries
        ledger_success = create_pledge_ledger_entries(
            db, new_pledge, pledge_data.company_id, current_user.id
        )
        
        if not ledger_success:
            print("⚠️ Warning: Pledge created but ledger entries could not be created")
        
        return new_pledge
    
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error creating pledge: {str(e)}",
        )


@router.get("/{company_id}", response_model=List[PledgeSchema])
def get_pledges(
    company_id: int,
    status_filter: str = None,
    customer_id: int = None,
    scheme_id: int = None,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
):
    """
    Get all pledges for a company with optional filters.
    
    Query parameters:
    - status_filter: Filter by status (Active, Closed, Redeemed, Forfeited)
    - customer_id: Filter by customer
    - scheme_id: Filter by scheme
    """
    if company_id != current_user.company_id and current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view pledges for this company",
        )
    
    query = db.query(PledgeModel).filter(PledgeModel.company_id == company_id)
    
    if status_filter:
        query = query.filter(PledgeModel.status == status_filter)
    if customer_id:
        query = query.filter(PledgeModel.customer_id == customer_id)
    if scheme_id:
        query = query.filter(PledgeModel.scheme_id == scheme_id)
    
    pledges = query.order_by(PledgeModel.created_at.desc()).all()
    return pledges


@router.get("/{pledge_id}", response_model=PledgeSchema)
def get_pledge(
    pledge_id: int,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
):
    """Get specific pledge with all items."""
    pledge = db.query(PledgeModel).filter(PledgeModel.id == pledge_id).first()
    
    if not pledge:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Pledge not found",
        )
    
    if pledge.company_id != current_user.company_id and current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view this pledge",
        )
    
    return pledge


@router.put("/{pledge_id}", response_model=PledgeSchema)
def update_pledge(
    pledge_id: int,
    pledge_data: PledgeUpdate,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
):
    """
    Update pledge details.
    
    Note: Changing amounts will require manual ledger adjustment.
    """
    pledge = db.query(PledgeModel).filter(PledgeModel.id == pledge_id).first()
    
    if not pledge:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Pledge not found",
        )
    
    if pledge.company_id != current_user.company_id and current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update this pledge",
        )
    
    try:
        update_data = pledge_data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            if key != "pledge_items":  # Handle items separately
                setattr(pledge, key, value)
        
        db.commit()
        db.refresh(pledge)
        return pledge
    
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error updating pledge: {str(e)}",
        )


@router.post("/{pledge_id}/upload-photo")
def upload_pledge_photo(
    pledge_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
):
    """Upload pledge photo."""
    pledge = db.query(PledgeModel).filter(PledgeModel.id == pledge_id).first()
    
    if not pledge:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Pledge not found",
        )
    
    if pledge.company_id != current_user.company_id and current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update this pledge",
        )
    
    try:
        # Delete old photo if exists
        if pledge.pledge_photo:
            delete_pledge_photo(pledge.pledge_photo)
        
        # Save new photo
        photo_path = save_pledge_photo(file, pledge_id)
        pledge.pledge_photo = photo_path
        
        db.commit()
        db.refresh(pledge)
        
        return {
            "message": "Photo uploaded successfully",
            "pledge_id": pledge_id,
            "photo_path": photo_path,
        }
    
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error uploading photo: {str(e)}",
        )


@router.post("/{pledge_id}/close")
def close_pledge(
    pledge_id: int,
    closure_data: dict,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
):
    """
    Close/redeem a pledge.
    
    Allowed transitions:
    - Active → Closed (extension)
    - Active → Redeemed (customer paid and took items)
    - Active → Forfeited (customer didn't pay, items forfeited)
    """
    pledge = db.query(PledgeModel).filter(PledgeModel.id == pledge_id).first()
    
    if not pledge:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Pledge not found",
        )
    
    if pledge.company_id != current_user.company_id and current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to close this pledge",
        )
    
    if pledge.status != "Active":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot close pledge with status {pledge.status}",
        )
    
    try:
        new_status = closure_data.get("new_status")
        notes = closure_data.get("notes", "")
        
        if new_status not in ["Closed", "Redeemed", "Forfeited"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid status. Allowed: Closed, Redeemed, Forfeited",
            )
        
        pledge.status = new_status
        pledge.updated_at = datetime.now()
        
        db.commit()
        db.refresh(pledge)
        
        return {
            "message": f"Pledge {new_status.lower()} successfully",
            "pledge_id": pledge_id,
            "pledge_no": pledge.pledge_no,
            "new_status": new_status,
        }
    
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error closing pledge: {str(e)}",
        )


@router.delete("/{pledge_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_pledge(
    pledge_id: int,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
):
    """
    Delete a pledge and reverse all ledger entries.
    
    Note: Only active pledges can be deleted.
    """
    pledge = db.query(PledgeModel).filter(PledgeModel.id == pledge_id).first()
    
    if not pledge:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Pledge not found",
        )
    
    if pledge.company_id != current_user.company_id and current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to delete this pledge",
        )
    
    try:
        # Reverse ledger entries
        reverse_pledge_ledger_entries(db, pledge_id, pledge.company_id)
        
        # Delete pledge photo if exists
        if pledge.pledge_photo:
            delete_pledge_photo(pledge.pledge_photo)
        
        # Delete pledge items
        db.query(PledgeItemsModel).filter(
            PledgeItemsModel.pledge_id == pledge_id
        ).delete()
        
        # Delete pledge
        db.delete(pledge)
        db.commit()
        
        return None
    
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error deleting pledge: {str(e)}",
        )


@router.get("/{pledge_id}/items", response_model=List[PledgeItemsSchema])
def get_pledge_items(
    pledge_id: int,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
):
    """Get all items in a pledge."""
    pledge = db.query(PledgeModel).filter(PledgeModel.id == pledge_id).first()
    
    if not pledge:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Pledge not found",
        )
    
    if pledge.company_id != current_user.company_id and current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view items",
        )
    
    items = db.query(PledgeItemsModel).filter(
        PledgeItemsModel.pledge_id == pledge_id
    ).all()
    
    return items


@router.get("/designs/list", response_model=List[str], tags=["pledge-items"])
def get_jewel_designs(
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
):
    """
    Get list of all distinct jewel designs from pledge items.
    
    Returns:
    - List of unique jewel designs (e.g., Ring, Necklace, Bracelet, Earring, etc.)
    - Used for dropdown/select options in frontend
    - Filters out null/empty values
    - Results sorted alphabetically
    
    Example:
        GET /pledges/designs/list
        
        Response:
        [
            "Bracelet",
            "Earring",
            "Necklace",
            "Ring",
            "Ankle",
            "Waist Chain"
        ]
    """
    # Query all distinct non-null jewel designs, sorted alphabetically
    designs = db.query(PledgeItemsModel.jewel_design).filter(
        PledgeItemsModel.jewel_design.isnot(None),
        PledgeItemsModel.jewel_design != ""
    ).distinct().order_by(PledgeItemsModel.jewel_design).all()
    
    # Extract values from tuples and return as list
    design_list = [design[0] for design in designs if design[0]]
    
    return design_list


@router.get("/conditions/list", response_model=List[str], tags=["pledge-items"])
def get_jewel_conditions(
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
):
    """
    Get list of all distinct jewel conditions from pledge items.
    
    Returns:
    - List of unique jewel conditions (e.g., Good, Fair, Poor, Excellent, etc.)
    - Used for dropdown/select options in frontend
    - Filters out null/empty values
    - Results sorted alphabetically
    
    Example:
        GET /pledges/conditions/list
        
        Response:
        [
            "Excellent",
            "Fair",
            "Good",
            "Poor"
        ]
    """
    # Query all distinct non-null jewel conditions, sorted alphabetically
    conditions = db.query(PledgeItemsModel.jewel_condition).filter(
        PledgeItemsModel.jewel_condition.isnot(None),
        PledgeItemsModel.jewel_condition != ""
    ).distinct().order_by(PledgeItemsModel.jewel_condition).all()
    
    # Extract values from tuples and return as list
    condition_list = [condition[0] for condition in conditions if condition[0]]
    
    return condition_list


@router.get("/stone-types/list", response_model=List[str], tags=["pledge-items"])
def get_stone_types(
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
):
    """
    Get list of all distinct stone types from pledge items.
    
    Returns:
    - List of unique stone types (e.g., Diamond, Ruby, Sapphire, Emerald, etc.)
    - Used for dropdown/select options in frontend
    - Filters out null/empty values
    - Results sorted alphabetically
    
    Example:
        GET /pledges/stone-types/list
        
        Response:
        [
            "Diamond",
            "Emerald",
            "Pearl",
            "Ruby",
            "Sapphire"
        ]
    """
    # Query all distinct non-null stone types, sorted alphabetically
    stone_types = db.query(PledgeItemsModel.stone_type).filter(
        PledgeItemsModel.stone_type.isnot(None),
        PledgeItemsModel.stone_type != ""
    ).distinct().order_by(PledgeItemsModel.stone_type).all()
    
    # Extract values from tuples and return as list
    stone_type_list = [stone[0] for stone in stone_types if stone[0]]
    
    return stone_type_list

