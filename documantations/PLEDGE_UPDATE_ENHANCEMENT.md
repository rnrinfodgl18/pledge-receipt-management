# Pledge Update Enhancement - Documentation

## Overview
Enhanced pledge update functionality with automatic item replacement and ledger transaction handling.

## Changes Made

### 1. Database Model Changes (`app/models.py`)
- **Added `due_date` column** to `Pledge` model
  - Type: `DateTime`
  - Nullable: `True`
  - Indexed: `True`
  - Purpose: Track pledge repayment due date

### 2. Schema Changes (`app/schemas.py`)

#### PledgeBase
- Added `due_date: Optional[datetime] = None`

#### PledgeCreate
- Added `due_date: Optional[datetime] = None`

#### PledgeUpdate
- Added `due_date: Optional[datetime] = None`
- Added `pledge_items: Optional[List[PledgeItemsCreate]] = None`
  - When provided, all existing items are removed and replaced with new items

### 3. API Endpoint Enhancement (`app/routes/pledges.py`)

#### PUT `/pledges/{pledge_id}`
Enhanced with the following features:

**Features:**
1. ✅ **Item Replacement**: Automatically removes all old items and inserts new items when `pledge_items` is provided
2. ✅ **Auto Weight Calculation**: Recalculates `gross_weight` and `net_weight` from new items
3. ✅ **Ledger Auto-Update**: When `loan_amount` changes:
   - Reverses old ledger entries
   - Creates new ledger entries with updated amount
4. ✅ **Atomic Transaction**: All operations in single transaction (all or nothing)
5. ✅ **Due Date Support**: Can set/update pledge due date

**Request Example:**
```json
{
  "due_date": "2025-12-31T00:00:00",
  "loan_amount": 50000,
  "interest_rate": 2.5,
  "pledge_items": [
    {
      "jewel_type_id": 1,
      "jewel_design": "Gold Ring",
      "jewel_condition": "Excellent",
      "stone_type": "Diamond",
      "gross_weight": 10.5,
      "net_weight": 9.8,
      "quantity": 1
    },
    {
      "jewel_type_id": 2,
      "jewel_design": "Gold Chain",
      "jewel_condition": "Good",
      "stone_type": null,
      "gross_weight": 25.0,
      "net_weight": 24.5,
      "quantity": 1
    }
  ]
}
```

**Response:**
Returns updated pledge with all new items.

### 4. Database Migration

**Migration Script:** `db_migrations/add_due_date_column.py`

**What it does:**
1. Adds `due_date` column to existing `pledges` table
2. Creates index on `due_date` for better query performance
3. Verifies column creation

**Run Migration:**
```bash
python db_migrations/add_due_date_column.py
```

**Migration Output:**
```
============================================================
Migration: Add due_date column to pledges table
============================================================
[RUNNING] Adding due_date column...
[OK] Successfully added due_date column to pledges table
[RUNNING] Creating index on due_date column...
[OK] Successfully created index on due_date column

[VERIFICATION]
  Column Name: due_date
  Data Type: timestamp without time zone
  Nullable: YES

[SUCCESS] Migration completed successfully!
============================================================
```

## Usage Examples

### Example 1: Update Due Date Only
```json
PUT /pledges/123
{
  "due_date": "2025-12-31T23:59:59"
}
```

### Example 2: Replace All Items
```json
PUT /pledges/123
{
  "pledge_items": [
    {
      "jewel_type_id": 1,
      "jewel_design": "Updated Ring",
      "jewel_condition": "Excellent",
      "stone_type": "Ruby",
      "gross_weight": 12.0,
      "net_weight": 11.5,
      "quantity": 1
    }
  ]
}
```
**Result:**
- Old items deleted
- New item inserted
- `gross_weight` = 12.0
- `net_weight` = 11.5

### Example 3: Update Loan Amount (Ledger Auto-Update)
```json
PUT /pledges/123
{
  "loan_amount": 75000
}
```
**Result:**
- Old ledger entries reversed
- New ledger entries created with ₹75,000
- Double-entry bookkeeping maintained

### Example 4: Complete Update
```json
PUT /pledges/123
{
  "due_date": "2026-01-15T00:00:00",
  "loan_amount": 60000,
  "interest_rate": 2.0,
  "first_month_interest": 1200,
  "pledge_items": [
    {
      "jewel_type_id": 1,
      "jewel_design": "Gold Necklace",
      "jewel_condition": "Excellent",
      "stone_type": "Emerald",
      "gross_weight": 30.0,
      "net_weight": 28.5,
      "quantity": 1
    },
    {
      "jewel_type_id": 2,
      "jewel_design": "Gold Bracelet",
      "jewel_condition": "Good",
      "stone_type": null,
      "gross_weight": 15.0,
      "net_weight": 14.8,
      "quantity": 1
    }
  ]
}
```
**Result:**
- Due date updated
- Loan amount changed → Ledger entries reversed and recreated
- All old items removed
- 2 new items added
- Weights recalculated: gross_weight=45.0, net_weight=43.3

## Benefits

### 1. Single Endpoint for Complete Update
- No need for separate API calls to update items
- Simplified client-side code
- Reduced network requests

### 2. Data Consistency
- Atomic transactions ensure all-or-nothing
- No partial updates that leave data in inconsistent state
- Automatic weight recalculation

### 3. Ledger Integrity
- Automatic ledger reversal and recreation when amounts change
- Double-entry bookkeeping always balanced
- Audit trail maintained

### 4. Flexible Item Management
- Can replace all items in one call
- Can update pledge details without touching items
- Can do both simultaneously

### 5. Due Date Tracking
- Track when pledges are due for repayment
- Can be used for overdue reports
- Indexed for fast queries

## Technical Notes

### Transaction Flow
1. **Validate**: Check pledge exists
2. **Items**: If `pledge_items` provided:
   - Delete all existing items
   - Insert new items
   - Calculate total weights
3. **Fields**: Update all other pledge fields
4. **Ledger**: If `loan_amount` changed:
   - Reverse old entries
   - Create new entries
5. **Commit**: All changes in single transaction
6. **Rollback**: If any step fails, all changes rolled back

### Ledger Reversal Logic
When loan amount changes:
- Finds all ledger entries with `reference_type="Pledge"` and `reference_id=pledge_id`
- Deletes all found entries
- Creates new entries with updated amounts
- Maintains double-entry balance (Total Debits = Total Credits)

### Error Handling
- If items fail → entire transaction rolled back
- If ledger fails → entire transaction rolled back
- Returns clear error messages
- No partial updates

## Alternative: Granular Item Management

If you prefer more granular control over items, use:

**PUT `/pledges/{pledge_id}/items`**

Supports:
- `"action": "add"` - Add new item
- `"action": "update"` - Update specific item by ID
- `"action": "delete"` - Delete specific item by ID

This allows:
- Adding single item without replacing all
- Updating specific item without touching others
- Deleting specific items

## Migration Status

✅ Database migration completed successfully
✅ Column `due_date` added to `pledges` table
✅ Index created on `due_date` column
✅ Verified: Column type is `timestamp without time zone`

## API Testing

Test with Swagger UI at: `http://localhost:8000/docs`

1. Login to get token
2. Navigate to `PUT /pledges/{pledge_id}`
3. Try the examples above
4. Verify results in database

## Summary

This enhancement provides a complete solution for:
- ✅ Adding due date to pledges
- ✅ Single-endpoint item replacement
- ✅ Automatic ledger transaction handling
- ✅ Atomic operations with rollback
- ✅ Weight auto-calculation
- ✅ Backward compatible (all fields optional)
