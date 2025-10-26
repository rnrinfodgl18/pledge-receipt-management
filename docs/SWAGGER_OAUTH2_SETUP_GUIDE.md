# Swagger OAuth2 Authentication Guide

## Database Status ✓

All **16 tables** have been successfully created:
- ✓ companies
- ✓ users
- ✓ jewel_types
- ✓ jewel_rates
- ✓ bank_details
- ✓ schemes
- ✓ customer_details
- ✓ chart_of_accounts
- ✓ ledger_entries
- ✓ pledges
- ✓ pledge_items
- ✓ pledge_receipts
- ✓ receipt_items
- ✓ **bank_pledges** (NEW)
- ✓ **bank_pledge_items** (NEW)
- ✓ **bank_redemptions** (NEW)

---

## 🔐 How to Login in Swagger UI

### Step 1: Open Swagger Documentation
```
URL: http://localhost:8000/docs
```

### Step 2: Click "Authorize" Button
```
┌──────────────────────────────────────────┐
│ Swagger UI                               │
├──────────────────────────────────────────┤
│                                          │
│  [Authorize] [Models] [Schemas]          │  ← Click here
│                                          │
│  GET /jewel-types/                       │
│  GET /bank-pledges?company_id=1          │
│  POST /bank-pledges/transfer             │
│                                          │
└──────────────────────────────────────────┘
```

### Step 3: Login Form Appears
```
┌─────────────────────────────────────────┐
│ Available Authorizations                 │
├─────────────────────────────────────────┤
│                                         │
│ OAuth2PasswordBearer                    │
│ ┌───────────────────────────────────┐   │
│ │ Username: [________________]       │   │
│ │ Password: [________________]       │   │
│ │                                   │   │
│ │       [Authorize] [Cancel]        │   │
│ └───────────────────────────────────┘   │
│                                         │
│ HTTPBearer                              │
│ ┌───────────────────────────────────┐   │
│ │ Token: [________________]          │   │
│ │                                   │   │
│ │       [Authorize] [Cancel]        │   │
│ └───────────────────────────────────┘   │
│                                         │
│            [Logout]                     │
│                                         │
└─────────────────────────────────────────┘
```

### Step 4: Enter Credentials
```
Username: admin (or any existing user)
Password: admin123 (or user's password)
```

### Step 5: Click "Authorize"
The button changes to indicate you're logged in:
```
[Authorize] → becomes → [Logout]
```

### Step 6: Now All Endpoints are Protected
Every API request will automatically include:
```
Authorization: Bearer {token}
```

---

## 🧪 Test Endpoints After Login

### Create Bank Pledge Transfer
```
POST /bank-pledges/transfer
{
  "pledge_id": 1,
  "bank_details_id": 1,
  "transfer_date": "2025-10-26T10:00:00",
  "gross_weight": 20.0,
  "net_weight": 18.5,
  "valuation_amount": 60000.0,
  "ltv_percentage": 80.0,
  "bank_reference_no": "HDFC/2025/001",
  "remarks": "Financing for business expansion"
}
```

### Get List of Bank Pledges
```
GET /bank-pledges?company_id=1&status=WITH_BANK
```

### Get Bank Pledge Details
```
GET /bank-pledges/1
```

### Check if Receipt Can Redeem
```
POST /bank-pledges/1/check-receipt-redemption?receipt_id=10
```

### Redeem with Customer Receipt
```
POST /bank-pledges/1/redeem-with-receipt
{
  "receipt_id": 10,
  "use_receipt_amount": 50000.0,
  "additional_business_payment": 2500.0,
  "remarks": "Customer payment used to redeem from bank"
}
```

---

## 🔄 OAuth2 Security Flow

### How It Works:

```
┌──────────────────────────────────────────────────────────────┐
│                    OAUTH2 FLOW                               │
└──────────────────────────────────────────────────────────────┘

STEP 1: USER LOGS IN (Browser/Swagger UI)
┌──────────────────────────────┐
│ POST /token                  │
│ {                            │
│   username: "admin"          │
│   password: "admin123"       │
│ }                            │
└──────────────────────────────┘
           ↓
         SERVER
           ↓
┌──────────────────────────────────────────┐
│ ✓ Verify username in database           │
│ ✓ Verify password (Argon2 hash)         │
│ ✓ Create JWT token (30 min expiry)      │
│ ✓ Return token to browser               │
└──────────────────────────────────────────┘
           ↓
┌────────────────────────────────────────┐
│ RESPONSE:                              │
│ {                                      │
│   "access_token": "eyJhbGc...",       │
│   "token_type": "bearer"              │
│ }                                      │
└────────────────────────────────────────┘

STEP 2: BROWSER STORES TOKEN
Swagger UI automatically stores it for future requests

STEP 3: MAKE PROTECTED REQUEST
┌──────────────────────────────┐
│ GET /bank-pledges/1          │
│ Headers:                     │
│   Authorization: Bearer      │
│   {eyJhbGc...}              │
└──────────────────────────────┘
           ↓
         SERVER
           ↓
┌──────────────────────────────────────────┐
│ ✓ Extract token from header             │
│ ✓ Decode JWT (verify signature)         │
│ ✓ Check expiry time                     │
│ ✓ Get user ID from token                │
│ ✓ Load user from database               │
│ ✓ Execute endpoint with user context    │
└──────────────────────────────────────────┘
           ↓
┌────────────────────────────────────────┐
│ RESPONSE: 200 OK with data             │
│ {                                      │
│   "id": 1,                             │
│   "pledge_id": 5,                      │
│   "bank_name": "HDFC Bank",           │
│   ...                                  │
│ }                                      │
└────────────────────────────────────────┘
```

---

## 🛠️ Common Issues & Solutions

### Issue 1: "Authorize" button not appearing
**Solution:**
1. Hard refresh Swagger: `Ctrl+Shift+R` (Windows) or `Cmd+Shift+R` (Mac)
2. Clear browser cache: Settings → Clear browsing data
3. Check console (F12) for errors

### Issue 2: "Invalid token" error after login
**Solution:**
1. Token expired (max 30 minutes) → Log out and log in again
2. Wrong credentials → Verify username/password
3. User inactive → Check if user.status = True in database

### Issue 3: Endpoints don't show "Authorize" lock icon
**Solution:**
1. Restart FastAPI server: `Ctrl+C` then run again
2. The OpenAPI schema needs to refresh
3. Token expiry might need adjustment: Edit `app/auth.py`
   ```python
   ACCESS_TOKEN_EXPIRE_MINUTES = 60  # Increase if needed
   ```

### Issue 4: "403 Forbidden" error on some endpoints
**Solution:**
1. Check if user role has permission for that endpoint
2. Some endpoints might require admin role
3. Check `get_current_user` dependency in route

---

## 🔑 Manual Token-Based Testing (Postman/cURL)

### Step 1: Get Token
```bash
curl -X POST "http://localhost:8000/token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin&password=admin123"
```

Response:
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

### Step 2: Use Token in Request
```bash
curl -X GET "http://localhost:8000/bank-pledges/1" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

### Step 3: In Postman
1. Add "Authorization" header
2. Select Type: "Bearer Token"
3. Paste token in value field
4. Send request

---

## 📝 User Creation & Management

### Create a New User
```bash
POST /users/
{
  "username": "john_doe",
  "password": "securepassword123",
  "role": "staff",
  "status": true
}
```

### List All Users
```bash
GET /users/
```

### Change Password
```bash
POST /auth/change-password
{
  "current_password": "admin123",
  "new_password": "newpassword456",
  "confirm_password": "newpassword456"
}
```

---

## 🚀 New Bank Pledge Endpoints Available

### 1. Transfer Pledge to Bank
```
POST /bank-pledges/transfer
Transfers a pledge to bank for financing
```

### 2. List Bank Pledges
```
GET /bank-pledges?company_id=1&status=WITH_BANK
View all pledges with banks
```

### 3. Get Bank Pledge Details
```
GET /bank-pledges/{id}
Detailed view with items and bank info
```

### 4. Redeem from Bank (Direct Payment)
```
POST /bank-pledges/{id}/redeem
Business directly pays bank from cash
```

### 5. Redeem with Customer Receipt
```
POST /bank-pledges/{id}/redeem-with-receipt
Customer payment used to redeem from bank
```

### 6. Check Receipt for Redemption
```
POST /bank-pledges/{id}/check-receipt-redemption
Analyze if receipt can cover bank loan
```

### 7. Cancel Bank Pledge
```
POST /bank-pledges/{id}/cancel
Void a bank pledge transfer
```

---

## 📊 Sample Workflow

### Scenario: Complete Business Rotation

```
DAY 1: Create Pledge
POST /pledges/
{
  "pledge_no": "GLD-2025-0001",
  "loan_amount": 50000,
  "pledge_items": [...],
  "customer_id": 1
}
Response: Pledge created

DAY 1: Transfer to Bank
POST /bank-pledges/transfer
{
  "pledge_id": 1,
  "bank_details_id": 1,
  "valuation_amount": 60000,
  "ltv_percentage": 80
}
Response: Bank loan ₹48,000 received ✓

DAY 10: Business uses ₹48,000 for operations...

DAY 30: Customer wants to redeem
1. POST /receipts/ (Create receipt for ₹55,000)
2. POST /bank-pledges/1/check-receipt-redemption?receipt_id=10
   Response: Can redeem, profit ₹5,000
3. POST /bank-pledges/1/redeem-with-receipt
   {
     "receipt_id": 10,
     "use_receipt_amount": 50000,
     "additional_business_payment": 0
   }
   Response: Bank redeemed, profit recorded ✓

RESULT:
✓ Pledge redeemed
✓ Bank loan repaid
✓ Customer receivable settled
✓ Profit: ₹5,000 captured
✓ All ledger entries balanced
```

---

## 🎯 Summary

- **Database:** All 16 tables created ✓
- **Authentication:** OAuth2 fully configured ✓
- **Bank Pledges:** Complete workflow implemented ✓
- **Ledger Integration:** Automatic journal entries ✓
- **Real Business Scenario:** Fully supported ✓

Login in Swagger and test the endpoints!
