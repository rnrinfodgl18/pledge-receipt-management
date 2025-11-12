"""API routes for pledge management with automatic ledger integration."""
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status, Query
from sqlalchemy.orm import Session, joinedload
from datetime import datetime, date
from typing import List, Optional

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
        # Validate customer exists
        customer = db.query(CustomerModel).filter(
            CustomerModel.id == pledge_data.customer_id,
        ).first()
        if not customer:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Customer {pledge_data.customer_id} not found",
            )
        
        # Validate scheme exists
        scheme = db.query(SchemeModel).filter(
            SchemeModel.id == pledge_data.scheme_id,
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
        
        # Calculate due_date if not provided (pledge_date + scheme duration)
        if not pledge_data.due_date and scheme.duration_in_months:
            pledge_date_obj = pledge_data.pledge_date if isinstance(pledge_data.pledge_date, datetime) else datetime.combine(pledge_data.pledge_date, datetime.min.time())
            # Add months to pledge date
            month = pledge_date_obj.month + scheme.duration_in_months
            year = pledge_date_obj.year + (month - 1) // 12
            month = ((month - 1) % 12) + 1
            due_date = pledge_date_obj.replace(year=year, month=month)
        else:
            due_date = pledge_data.due_date
        
        # Create pledge
        new_pledge = PledgeModel(
            company_id=pledge_data.company_id,
            pledge_no=pledge_no,
            customer_id=pledge_data.customer_id,
            scheme_id=pledge_data.scheme_id,
            pledge_date=pledge_data.pledge_date or datetime.now().date(),
            due_date=due_date,
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
            # Initialize tracking fields - add first month interest as received by default
            total_principal_received=0.0,
            total_interest_received=pledge_data.first_month_interest,
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


@router.get("/list")
def get_pledges_list(
    company_id: int,
    customer_id: Optional[int] = None,
    scheme_id: Optional[int] = None,
    status: Optional[str] = None,
    limit: Optional[int] = 100,
    offset: Optional[int] = 0,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
):
    """
    Return pledges filtered by company_id (required) and optional customer_id, scheme_id, and status.
    Supports pagination with limit/offset.

    Query parameters:
    - company_id: required company id
    - customer_id: optional customer id to filter pledges
    - scheme_id: optional scheme id to filter pledges
    - status: optional pledge status (e.g., Active, Closed, Redeemed, Forfeited)
    - limit: max number of records to return (default: 100, max: 1000)
    - offset: number of records to skip (default: 0)
    
    Returns:
    {
        "total": total count of matching pledges,
        "limit": limit used,
        "offset": offset used,
        "data": [...pledges...]
    }
    """
    # Authorization: allow all authenticated users

    # Validate limit (max 1000)
    if limit and limit > 1000:
        limit = 1000
    if limit and limit < 1:
        limit = 1
    
    # Validate offset
    if offset and offset < 0:
        offset = 0

    query = (
        db.query(PledgeModel)
        .options(
            joinedload(PledgeModel.customer),
            joinedload(PledgeModel.scheme),
            joinedload(PledgeModel.pledge_items).joinedload(PledgeItemsModel.jewel_type)
        )
        .filter(PledgeModel.company_id == company_id)
    )

    if status:
        query = query.filter(PledgeModel.status == status)
    if customer_id:
        query = query.filter(PledgeModel.customer_id == customer_id)
    if scheme_id:
        query = query.filter(PledgeModel.scheme_id == scheme_id)

    # Get total count before pagination
    total = query.count()
    
    # Apply pagination and get results
    pledges = query.order_by(PledgeModel.created_at.desc()).limit(limit).offset(offset).all()
    
    return {
        "total": total,
        "limit": limit,
        "offset": offset,
        "data": pledges
    }


@router.get("/company/{company_id}/pledges")
def get_company_pledges(
    company_id: int,
    customer_id: Optional[int] = Query(None, description="Filter by customer ID"),
    scheme_id: Optional[int] = Query(None, description="Filter by scheme ID"),
    status: Optional[str] = Query(None, description="Filter by status (Active, Closed, Redeemed, Forfeited)"),
    limit: Optional[int] = Query(100, description="Max records (default: 100, max: 1000)"),
    offset: Optional[int] = Query(0, description="Records to skip (default: 0)"),
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
):
    """
    Get all pledges for a specific company with optional filters and pagination.
    
    Path parameters:
    - company_id: Required company ID
    
    Query parameters:
    - customer_id: Optional - filter by customer
    - scheme_id: Optional - filter by scheme
    - status: Optional - filter by status (Active, Closed, Redeemed, Forfeited)
    - limit: max number of records to return (default: 100, max: 1000)
    - offset: number of records to skip (default: 0)
    
    Returns:
    {
        "total": total count of matching pledges,
        "limit": limit used,
        "offset": offset used,
        "data": [...pledges with customer, scheme, and items...]
    }
    
    Example:
        GET /pledges/company/1/pledges?status=Active&limit=50
        GET /pledges/company/1/pledges?customer_id=5&offset=100
    """
    # Validate limit (max 1000)
    if limit and limit > 1000:
        limit = 1000
    if limit and limit < 1:
        limit = 1
    
    # Validate offset
    if offset and offset < 0:
        offset = 0
    
    query = (
        db.query(PledgeModel)
        .options(
            joinedload(PledgeModel.customer),
            joinedload(PledgeModel.scheme),
            joinedload(PledgeModel.pledge_items).joinedload(PledgeItemsModel.jewel_type)
        )
        .filter(PledgeModel.company_id == company_id)
    )
    
    if status:
        query = query.filter(PledgeModel.status == status)
    if customer_id:
        query = query.filter(PledgeModel.customer_id == customer_id)
    if scheme_id:
        query = query.filter(PledgeModel.scheme_id == scheme_id)
    
    # Get total count before pagination
    total = query.count()
    
    # Apply pagination and get results
    pledges = query.order_by(PledgeModel.created_at.desc()).limit(limit).offset(offset).all()
    
    return {
        "total": total,
        "limit": limit,
        "offset": offset,
        "data": pledges
    }


@router.get("/pledge/{pledge_id}")
def get_single_pledge(
    pledge_id: int,
    company_id: Optional[int] = Query(None, description="Optional company ID for validation"),
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
):
    """
    Get a single specific pledge by ID with all related data.
    
    Path parameters:
    - pledge_id: Required pledge ID
    
    Query parameters:
    - company_id: Optional - if provided, validates pledge belongs to this company
    
    Returns:
    - Complete pledge object with:
      * Customer details
      * Scheme details
      * Pledge items with jewel type details
    
    Example:
        GET /pledges/pledge/123
        GET /pledges/pledge/123?company_id=1
    """
    query = (
        db.query(PledgeModel)
        .options(
            joinedload(PledgeModel.customer),
            joinedload(PledgeModel.scheme),
            joinedload(PledgeModel.pledge_items).joinedload(PledgeItemsModel.jewel_type)
        )
        .filter(PledgeModel.id == pledge_id)
    )
    
    # If company_id is provided, add it as a filter
    if company_id:
        query = query.filter(PledgeModel.company_id == company_id)
    
    pledge = query.first()
    
    if not pledge:
        if company_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Pledge {pledge_id} not found for company {company_id}",
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Pledge {pledge_id} not found",
            )
    
    return pledge


@router.get("/report/due-date")
def get_pledge_due_date_report(
    company_id: int,
    from_date: date = Query(..., description="Start date for due date range (YYYY-MM-DD)"),
    to_date: date = Query(..., description="End date for due date range (YYYY-MM-DD)"),
    status: Optional[str] = None,
    limit: Optional[int] = 1000,
    offset: Optional[int] = 0,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
):
    """
    Get pledge report filtered by due_date range.
    
    Query parameters:
    - company_id: required company id
    - from_date: start date for due_date range (required, format: YYYY-MM-DD)
    - to_date: end date for due_date range (required, format: YYYY-MM-DD)
    - status: optional pledge status filter (Active, Closed, Redeemed, Forfeited)
    - limit: max number of records (default: 1000, max: 5000)
    - offset: number of records to skip (default: 0)
    
    Returns pledges where due_date is between from_date and to_date (inclusive).
    
    Example:
        GET /pledges/report/due-date?company_id=1&from_date=2025-01-01&to_date=2025-01-31
        GET /pledges/report/due-date?company_id=1&from_date=2025-01-01&to_date=2025-01-31&status=Active
    
    Response:
    {
        "total": 45,
        "limit": 1000,
        "offset": 0,
        "from_date": "2025-01-01",
        "to_date": "2025-01-31",
        "status": "Active",
        "data": [...pledges...]
    }
    """
    # Authorization: allow all authenticated users
    
    # Validate date range
    if from_date > to_date:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="from_date cannot be greater than to_date"
        )
    
    # Validate limit (max 5000 for reports)
    if limit and limit > 5000:
        limit = 5000
    if limit and limit < 1:
        limit = 1
    
    # Validate offset
    if offset and offset < 0:
        offset = 0
    
    # Build query with eager loading
    query = (
        db.query(PledgeModel)
        .options(
            joinedload(PledgeModel.customer),
            joinedload(PledgeModel.scheme),
            joinedload(PledgeModel.pledge_items).joinedload(PledgeItemsModel.jewel_type)
        )
        .filter(
            PledgeModel.company_id == company_id,
            PledgeModel.due_date >= from_date,
            PledgeModel.due_date <= to_date
        )
    )
    
    # Apply optional status filter
    if status:
        query = query.filter(PledgeModel.status == status)
    
    # Get total count
    total = query.count()
    
    # Apply pagination and get results ordered by due_date
    pledges = query.order_by(PledgeModel.due_date.asc(), PledgeModel.created_at.desc()).limit(limit).offset(offset).all()
    
    return {
        "total": total,
        "limit": limit,
        "offset": offset,
        "from_date": from_date.isoformat(),
        "to_date": to_date.isoformat(),
        "status": status,
        "data": pledges
    }


@router.put("/{pledge_id}", response_model=PledgeSchema)
def update_pledge(
    pledge_id: int,
    pledge_data: PledgeUpdate,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
):
    """
    Update pledge details and items.
    
    Features:
    - Updates pledge-level fields (loan_amount, interest_rate, due_date, etc.)
    - If pledge_items provided: removes all old items and inserts new items
    - Automatically recalculates gross_weight and net_weight
    - If loan_amount changed: reverses old ledger entries and creates new ones
    - Single transaction - all or nothing
    
    Important: If you change loan_amount, ledger will be automatically updated
    """
    pledge = db.query(PledgeModel).filter(PledgeModel.id == pledge_id).first()
    
    if not pledge:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Pledge not found",
        )
    
    # Authorization: allow all authenticated users
    
    try:
        update_data = pledge_data.model_dump(exclude_unset=True)
        old_loan_amount = pledge.loan_amount
        new_loan_amount = update_data.get("loan_amount", old_loan_amount)
        loan_amount_changed = old_loan_amount != new_loan_amount
        
        # Step 1: Handle pledge items replacement if provided
        if "pledge_items" in update_data and update_data["pledge_items"] is not None:
            # Delete all existing items
            db.query(PledgeItemsModel).filter(
                PledgeItemsModel.pledge_id == pledge_id
            ).delete()
            
            # Insert new items
            new_items = []
            total_gross_weight = 0.0
            total_net_weight = 0.0
            
            for item_data in update_data["pledge_items"]:
                new_item = PledgeItemsModel(
                    pledge_id=pledge_id,
                    jewel_type_id=item_data.get("jewel_type_id"),
                    jewel_design=item_data.get("jewel_design"),
                    jewel_condition=item_data.get("jewel_condition"),
                    stone_type=item_data.get("stone_type"),
                    gross_weight=item_data.get("gross_weight"),
                    net_weight=item_data.get("net_weight"),
                    quantity=item_data.get("quantity", 1),
                    created_by=current_user.id
                )
                new_items.append(new_item)
                total_gross_weight += new_item.gross_weight
                total_net_weight += new_item.net_weight
            
            # Add all new items
            db.add_all(new_items)
            
            # Update pledge weights
            pledge.gross_weight = total_gross_weight
            pledge.net_weight = total_net_weight
            
            # Remove pledge_items from update_data (already handled)
            update_data.pop("pledge_items")
        
        # Step 2: Update pledge-level fields
        for key, value in update_data.items():
            setattr(pledge, key, value)
        
        # Step 3: Handle ledger entries if loan_amount changed
        if loan_amount_changed:
            # Import here to avoid circular dependency
            from app.pledge_utils import reverse_pledge_ledger_entries, create_pledge_ledger_entries
            
            # Reverse old ledger entries
            reverse_pledge_ledger_entries(
                db=db,
                pledge_id=pledge_id,
                company_id=pledge.company_id
            )
            
            # Create new ledger entries with updated loan_amount
            ledger_result = create_pledge_ledger_entries(
                db=db,
                pledge=pledge,
                company_id=pledge.company_id,
                created_by=current_user.id
            )
            
            if not ledger_result.get("status"):
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Ledger entry creation failed: {ledger_result.get('message')}"
                )
        
        db.commit()
        db.refresh(pledge)
        
        return pledge
    
    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error updating pledge: {str(e)}",
        )


@router.put("/{pledge_id}/items")
def update_pledge_items(
    pledge_id: int,
    items_data: List[dict],
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
):
    """
    Update pledge items - supports add, update, and delete operations.
    
    Request body format:
    [
        {
            "id": 1,  # Existing item ID (omit for new items)
            "action": "update",  # "add", "update", or "delete"
            "jewel_type_id": 1,
            "jewel_design": "Ring",
            "jewel_condition": "Good",
            "stone_type": "Diamond",
            "gross_weight": 10.5,
            "net_weight": 9.8,
            "quantity": 1
        },
        {
            "id": 2,
            "action": "delete"  # Mark for deletion
        },
        {
            "action": "add",  # New item (no ID)
            "jewel_type_id": 2,
            "jewel_design": "Necklace",
            "jewel_condition": "Excellent",
            "stone_type": "Ruby",
            "gross_weight": 20.0,
            "net_weight": 18.5,
            "quantity": 1
        }
    ]
    
    Returns updated pledge with all items.
    """
    pledge = db.query(PledgeModel).filter(PledgeModel.id == pledge_id).first()
    
    if not pledge:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Pledge not found",
        )
    
    try:
        added_count = 0
        updated_count = 0
        deleted_count = 0
        
        for item_data in items_data:
            action = item_data.get("action", "update")
            item_id = item_data.get("id")
            
            if action == "delete":
                # Delete existing item
                if not item_id:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Item ID required for delete action"
                    )
                
                item = db.query(PledgeItemsModel).filter(
                    PledgeItemsModel.id == item_id,
                    PledgeItemsModel.pledge_id == pledge_id
                ).first()
                
                if item:
                    db.delete(item)
                    deleted_count += 1
                
            elif action == "update":
                # Update existing item
                if not item_id:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Item ID required for update action"
                    )
                
                item = db.query(PledgeItemsModel).filter(
                    PledgeItemsModel.id == item_id,
                    PledgeItemsModel.pledge_id == pledge_id
                ).first()
                
                if not item:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail=f"Item {item_id} not found"
                    )
                
                # Update fields
                if "jewel_type_id" in item_data:
                    item.jewel_type_id = item_data["jewel_type_id"]
                if "jewel_design" in item_data:
                    item.jewel_design = item_data["jewel_design"]
                if "jewel_condition" in item_data:
                    item.jewel_condition = item_data["jewel_condition"]
                if "stone_type" in item_data:
                    item.stone_type = item_data["stone_type"]
                if "gross_weight" in item_data:
                    item.gross_weight = item_data["gross_weight"]
                if "net_weight" in item_data:
                    item.net_weight = item_data["net_weight"]
                if "quantity" in item_data:
                    item.quantity = item_data["quantity"]
                
                updated_count += 1
                
            elif action == "add":
                # Add new item
                new_item = PledgeItemsModel(
                    pledge_id=pledge_id,
                    jewel_type_id=item_data.get("jewel_type_id"),
                    jewel_design=item_data.get("jewel_design"),
                    jewel_condition=item_data.get("jewel_condition"),
                    stone_type=item_data.get("stone_type"),
                    gross_weight=item_data.get("gross_weight"),
                    net_weight=item_data.get("net_weight"),
                    quantity=item_data.get("quantity", 1),
                    created_by=current_user.id
                )
                db.add(new_item)
                added_count += 1
        
        # Recalculate pledge totals
        items = db.query(PledgeItemsModel).filter(
            PledgeItemsModel.pledge_id == pledge_id
        ).all()
        
        pledge.gross_weight = sum(item.gross_weight for item in items)
        pledge.net_weight = sum(item.net_weight for item in items)
        
        db.commit()
        db.refresh(pledge)
        
        return {
            "message": "Items updated successfully",
            "pledge_id": pledge_id,
            "summary": {
                "added": added_count,
                "updated": updated_count,
                "deleted": deleted_count,
                "total_items": len(items)
            },
            "pledge": {
                "id": pledge.id,
                "pledge_no": pledge.pledge_no,
                "gross_weight": pledge.gross_weight,
                "net_weight": pledge.net_weight,
                "items": [
                    {
                        "id": item.id,
                        "jewel_type_id": item.jewel_type_id,
                        "jewel_design": item.jewel_design,
                        "jewel_condition": item.jewel_condition,
                        "stone_type": item.stone_type,
                        "gross_weight": item.gross_weight,
                        "net_weight": item.net_weight,
                        "quantity": item.quantity
                    }
                    for item in items
                ]
            }
        }
    
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error updating items: {str(e)}",
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
    
    # Authorization: allow all authenticated users
    
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
    
    # Authorization: allow all authenticated users
    
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
    
    # Authorization: allow all authenticated users
    
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
    
    # Authorization: allow all authenticated users
    
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


@router.post("/{pledge_id}/close")
def close_pledge(
    pledge_id: int,
    close_date: Optional[datetime] = None,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
):
    """
    Manually close a pledge.
    
    This endpoint allows closing a pledge and updating the close tracking fields.
    
    Args:
        pledge_id: ID of pledge to close
        close_date: Optional close date (defaults to current datetime)
        db: Database session
        current_user: Authenticated user
    
    Returns:
        Updated pledge with close details
    
    Note:
        - Sets pledge status to "Closed"
        - Records pledge_close_date
        - Maintains existing total_principal_received and total_interest_received
    """
    pledge = db.query(PledgeModel).filter(PledgeModel.id == pledge_id).first()
    
    if not pledge:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Pledge not found"
        )
    
    if pledge.status == "Closed":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Pledge is already closed"
        )
    
    # Set close date (use provided date or current datetime)
    pledge.pledge_close_date = close_date or datetime.now()
    pledge.status = "Closed"
    
    # Initialize totals if null
    if pledge.total_principal_received is None:
        pledge.total_principal_received = 0.0
    if pledge.total_interest_received is None:
        pledge.total_interest_received = 0.0
    
    db.commit()
    db.refresh(pledge)
    
    return {
        "message": "Pledge closed successfully",
        "pledge_id": pledge.id,
        "pledge_no": pledge.pledge_no,
        "status": pledge.status,
        "pledge_close_date": pledge.pledge_close_date,
        "total_principal_received": pledge.total_principal_received,
        "total_interest_received": pledge.total_interest_received
    }

