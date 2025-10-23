# Change Password API Endpoint

## Overview

The Change Password endpoint allows authenticated users to securely change their account password. This endpoint requires a valid JWT token and validates both the current password and new password requirements.

---

## Endpoint Details

### Request

**URL:** `POST /auth/change-password`

**Authentication:** Required (Bearer Token)

**Headers:**
```
Authorization: Bearer <your_jwt_token>
Content-Type: application/json
```

**Request Body:**
```json
{
  "current_password": "oldpassword123",
  "new_password": "newpassword456",
  "confirm_password": "newpassword456"
}
```

### Response (Success - 200 OK)

```json
{
  "message": "Password changed successfully",
  "user": {
    "id": 1,
    "username": "admin",
    "role": "admin",
    "status": true,
    "created_at": "2025-10-23T10:30:00"
  }
}
```

---

## Validation Rules

1. **New Password Match:** `new_password` must equal `confirm_password`
2. **Minimum Length:** New password must be at least 6 characters
3. **Current Password:** Must be correct and match the user's stored password
4. **Password Uniqueness:** New password cannot be the same as the current password
5. **User Active:** User account must be active

---

## Error Responses

### 400 Bad Request - Passwords Don't Match
```json
{
  "detail": "New password and confirm password do not match"
}
```

### 400 Bad Request - Password Too Short
```json
{
  "detail": "New password must be at least 6 characters"
}
```

### 400 Bad Request - Same as Current Password
```json
{
  "detail": "New password must be different from current password"
}
```

### 401 Unauthorized - Wrong Current Password
```json
{
  "detail": "Current password is incorrect"
}
```

### 401 Unauthorized - Invalid Token
```json
{
  "detail": "Invalid token"
}
```

---

## Examples

### Using cURL

```bash
# First, login to get JWT token
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "admin",
    "password": "password"
  }' > token_response.json

# Extract token from response
# Then change password
curl -X POST http://localhost:8000/auth/change-password \
  -H "Authorization: Bearer YOUR_JWT_TOKEN_HERE" \
  -H "Content-Type: application/json" \
  -d '{
    "current_password": "password",
    "new_password": "newpassword123",
    "confirm_password": "newpassword123"
  }'
```

### Using Python

```python
import requests
import json

# Login to get token
login_response = requests.post(
    "http://localhost:8000/auth/login",
    json={"username": "admin", "password": "password"}
)
token = login_response.json()["access_token"]

# Change password
response = requests.post(
    "http://localhost:8000/auth/change-password",
    headers={"Authorization": f"Bearer {token}"},
    json={
        "current_password": "password",
        "new_password": "newpassword123",
        "confirm_password": "newpassword123"
    }
)

print(response.json())
```

### Using Postman

1. **Create new POST request**
   - URL: `http://localhost:8000/auth/change-password`

2. **Set Headers**
   - Key: `Authorization`
   - Value: `Bearer YOUR_JWT_TOKEN_HERE`
   - Content-Type: `application/json` (auto-set)

3. **Set Body (JSON)**
   ```json
   {
     "current_password": "password",
     "new_password": "newpassword123",
     "confirm_password": "newpassword123"
   }
   ```

4. **Send Request**

---

## Interactive API Documentation

After starting the server, you can test this endpoint directly in the Swagger UI:

1. Go to: http://localhost:8000/docs
2. Click on "auth" section
3. Click on "POST /auth/change-password"
4. Click "Try it out"
5. Enter the request body
6. Click "Execute"

---

## Security Features

✅ **Password Hashing:** Uses Argon2 for secure password hashing
✅ **JWT Authentication:** Requires valid Bearer token
✅ **Current Password Verification:** Validates current password before allowing change
✅ **Password Strength:** Enforces minimum 6 character length
✅ **Input Validation:** All fields required and validated
✅ **Audit Logging:** Change attempts are logged with user details

---

## Database Changes

The endpoint updates the `password` field in the `users` table:

```sql
-- Before
SELECT id, username, password FROM users WHERE id = 1;
-- password: $argon2id$v=19$m=65540,t=3,p=4$oldhashedpassword...

-- After (new password is hashed)
-- password: $argon2id$v=19$m=65540,t=3,p=4$newhashedpassword...
```

---

## Implementation Notes

### Code Location
- **Route Handler:** `/app/routes/auth.py` - `change_password()` function
- **Schema Definition:** `/app/schemas.py` - `ChangePasswordRequest`, `ChangePasswordResponse`
- **Security Functions:** `/app/security.py` - `hash_password()`, `verify_password()`
- **Auth Dependency:** `/app/auth.py` - `get_current_user()`

### Database Model
- **Table:** `users`
- **Updated Field:** `password` (String, stores Argon2 hash)
- **User ID:** Retrieved from JWT token

---

## Flow Diagram

```
┌─────────────────────────────────────────┐
│ User Request (with JWT token)           │
│ POST /auth/change-password              │
└────────────────┬────────────────────────┘
                 │
                 ▼
        ┌────────────────────┐
        │ Validate JWT Token │
        │ Get Current User   │
        └────────┬───────────┘
                 │
        ✓ Token Valid?
        │
        ▼
┌───────────────────────────────────┐
│ Validate Request Fields           │
│ • Passwords match?                │
│ • Min 6 characters?               │
│ • Different from current?         │
└────────┬──────────────────────────┘
         │
        ✓ Valid?
         │
         ▼
┌────────────────────────────────┐
│ Verify Current Password        │
│ Against Stored Hash            │
└────────┬───────────────────────┘
         │
        ✓ Correct?
         │
         ▼
┌────────────────────────────────┐
│ Hash New Password (Argon2)     │
│ Update User Record in Database │
│ Commit Changes                 │
└────────┬───────────────────────┘
         │
         ▼
┌────────────────────────────────┐
│ Return Success Response        │
│ With Updated User Info         │
└────────────────────────────────┘
```

---

## Testing Guide

### Test Case 1: Valid Password Change
- **Input:** Correct current password + matching new passwords
- **Expected:** 200 OK with success message

### Test Case 2: Mismatched New Passwords
- **Input:** New passwords don't match
- **Expected:** 400 Bad Request - "passwords do not match"

### Test Case 3: Short Password
- **Input:** New password < 6 characters
- **Expected:** 400 Bad Request - "at least 6 characters"

### Test Case 4: Wrong Current Password
- **Input:** Incorrect current password
- **Expected:** 401 Unauthorized - "password is incorrect"

### Test Case 5: Same Password
- **Input:** New password same as current
- **Expected:** 400 Bad Request - "must be different"

### Test Case 6: Invalid Token
- **Input:** Missing or invalid token
- **Expected:** 401 Unauthorized - "Invalid token"

---

## Deployment Considerations

✅ **Environment:** Requires valid `SECRET_KEY` in `.env`
✅ **Database:** Requires `users` table with `password` column
✅ **Dependencies:** `passlib[argon2]`, `sqlalchemy`, `fastapi`
✅ **HTTPS:** Recommended for production (encryption in transit)

---

## Related Endpoints

- `POST /auth/login` - User login to get JWT token
- `GET /api/users/{id}` - Get user details (if available)
- `PUT /api/users/{id}` - Update user info (if available)

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | Oct 24, 2025 | Initial implementation of change password endpoint |

---

## Support

For issues or questions about this endpoint:
1. Check the API documentation at `/docs`
2. Review the server logs for detailed error messages
3. Verify all request fields are correct
4. Ensure user account is active
5. Confirm JWT token is valid and not expired

---

**Last Updated:** October 24, 2025  
**Status:** ✅ Production Ready
