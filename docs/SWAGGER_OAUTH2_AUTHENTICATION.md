# 🔐 Swagger UI OAuth2 Authentication Setup

## Overview

Your API now supports **OAuth2 login directly in Swagger UI**! Instead of manually getting a token from the `/auth/login` endpoint and pasting it, you can now login directly from the Swagger docs with a single click.

---

## ✨ Features

✅ **One-Click Login** - Login directly in Swagger UI  
✅ **Automatic Token Management** - Token automatically applied to all requests  
✅ **OAuth2 Standard** - Uses industry-standard OAuth2 protocol  
✅ **Password Grant Flow** - Username/password authentication  
✅ **Swagger Integration** - Native Swagger UI support  
✅ **Secure Token Handling** - Token managed by Swagger UI  

---

## 🚀 How to Use

### Step 1: Open Swagger UI
- Go to: http://localhost:8000/docs

### Step 2: Click the "Authorize" Button
- You'll see a green **"Authorize"** button in the top-right corner of Swagger UI
- Click it to open the authorization dialog

### Step 3: Login with Username & Password
- **Username:** Enter your username (e.g., `admin`)
- **Password:** Enter your password (e.g., `password`)
- Click **"Authorize"**

### Step 4: Start Testing
- The token is now automatically applied to all API requests
- Try any endpoint without manually adding headers!
- Click **"Logout"** (now shows instead of Authorize) to clear the token

---

## 📋 Example: Testing an Endpoint

### Before (Manual Token Management)
```bash
# 1. Login to get token
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"password"}'

# 2. Copy token from response
# 3. Manually paste in Swagger "Try it out" form
# 4. Use endpoint

# Total steps: 4
```

### After (OAuth2 in Swagger UI)
```
1. Click "Authorize" button
2. Enter username & password
3. Click "Authorize"
4. Use any endpoint

# Total steps: 4 (but all in UI!)
```

---

## 🔧 Technical Details

### OAuth2 Endpoint
**URL:** `POST /token`

**Request (Form Data):**
```
username: admin
password: password
```

**Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

### OAuth2 Security Scheme
The API is configured with:
- **Grant Type:** Password (Resource Owner Password Credentials)
- **Token URL:** `/token`
- **Security Scheme:** OAuth2PasswordBearer

---

## 📱 Code Examples

### JavaScript - How to Implement Similar in Your Frontend

```javascript
// Step 1: Get token
async function login(username, password) {
  const formData = new FormData();
  formData.append('username', username);
  formData.append('password', password);
  
  const response = await fetch('/token', {
    method: 'POST',
    body: formData
  });
  
  const data = await response.json();
  localStorage.setItem('token', data.access_token);
  return data.access_token;
}

// Step 2: Use token in requests
async function fetchWithToken(url, options = {}) {
  const token = localStorage.getItem('token');
  
  return fetch(url, {
    ...options,
    headers: {
      ...options.headers,
      'Authorization': `Bearer ${token}`
    }
  });
}

// Usage
await login('admin', 'password');
const data = await fetchWithToken('/pledges');
```

### Python - How to Implement Similar

```python
import requests

# Step 1: Get token
def login(username, password):
    response = requests.post(
        'http://localhost:8000/token',
        data={'username': username, 'password': password}
    )
    token = response.json()['access_token']
    return token

# Step 2: Use token in requests
def get_pledges(token):
    headers = {'Authorization': f'Bearer {token}'}
    response = requests.get(
        'http://localhost:8000/pledges',
        headers=headers
    )
    return response.json()

# Usage
token = login('admin', 'password')
pledges = get_pledges(token)
```

---

## 🔐 Security Considerations

### How It Works
1. **Username & Password** are sent to `/token` endpoint
2. **Token is generated** on server (JWT with expiration)
3. **Token stored** in Swagger UI local storage
4. **Token included** in all subsequent requests as `Authorization: Bearer <token>`
5. **Token expires** after configured duration (default: 30 minutes)

### Security Best Practices
✅ **HTTPS Required** - Use HTTPS in production  
✅ **Token Expiration** - Tokens expire after 30 minutes  
✅ **Refresh Logic** - Re-login when token expires  
✅ **No Password Storage** - Password never stored, only hashed  
✅ **Secure Hashing** - Uses Argon2 for password hashing  

---

## 🧪 Testing the OAuth2 Endpoint

### Using cURL
```bash
# Login with OAuth2 endpoint
curl -X POST http://localhost:8000/token \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin&password=password"

# Response:
# {
#   "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
#   "token_type": "bearer"
# }
```

### Using Postman
1. Create new POST request to `http://localhost:8000/token`
2. Go to "Body" tab → Select "form-data"
3. Add:
   - `username` = admin
   - `password` = password
4. Send request

---

## 📋 Two Login Endpoints

Your API now has TWO login endpoints:

### 1. `/auth/login` (Custom Endpoint)
- Returns: User details + token
- Use when: You need additional user information
- Example:
  ```json
  {
    "access_token": "...",
    "token_type": "bearer",
    "user": {
      "id": 1,
      "username": "admin",
      "role": "admin",
      "status": true
    }
  }
  ```

### 2. `/token` (OAuth2 Standard Endpoint)
- Returns: Token only
- Use when: You just need the token (Swagger UI uses this)
- Example:
  ```json
  {
    "access_token": "...",
    "token_type": "bearer"
  }
  ```

---

## 🎯 Swagger UI Features

### Authorize Button
- **Green "Authorize" button** - Click to login
- **Lock icon** - Shows which endpoints require authentication
- **Logout option** - Click again to logout

### Token Management
- **Automatic inclusion** - Token automatically added to all requests
- **Visual feedback** - Swagger shows which endpoints are authenticated
- **Session scope** - Token cleared when browser closed

---

## ❓ Troubleshooting

### Issue: "Authorize button not showing"
**Solution:** 
- Refresh the page (Ctrl+F5)
- Clear browser cache
- Check console for JavaScript errors

### Issue: "Login failed with 401"
**Solution:**
- Verify username exists in database
- Verify password is correct
- Check if user account is active (status=true)

### Issue: "Bearer token not working"
**Solution:**
- Ensure token was obtained from `/token` endpoint
- Check token expiration (30 minutes default)
- Re-login if token expired

### Issue: "CORS errors"
**Solution:**
- CORS should already be configured
- Check if running on same origin as API
- Verify API is on http://localhost:8000

---

## 🚀 Deployment

### For Render/Production
1. OAuth2 setup is already configured
2. No additional setup needed
3. Just push to GitHub and deploy
4. OAuth2 will work automatically on production URL

### Environment Variables
No additional environment variables needed for OAuth2 setup.
Uses existing `SECRET_KEY` from `.env` for token signing.

---

## 📚 Files Modified

- ✅ `app/main.py` - Added OAuth2 configuration and swagger_auth router
- ✅ `app/swagger_auth.py` - New file with OAuth2 token endpoint

---

## 🔄 Workflow Comparison

### Old Workflow
```
1. Go to /auth/login endpoint in Swagger
2. Enter credentials
3. Copy access_token from response
4. Go to any endpoint
5. Click "Try it out"
6. Scroll down to Authorization header
7. Paste token value
8. Send request
```

### New Workflow
```
1. Click green "Authorize" button
2. Enter credentials
3. Click "Authorize"
4. Go to any endpoint
5. Click "Try it out"
6. Send request (token automatically included!)
```

---

## ✅ Verification Checklist

- [x] OAuth2 endpoint created at `/token`
- [x] Swagger UI configured with OAuth2
- [x] Authorization button shows in Swagger UI
- [x] Login works with username & password
- [x] Token automatically applied to requests
- [x] Both `/auth/login` and `/token` endpoints work
- [x] Token expiration works correctly

---

## 📖 Related Endpoints

- `POST /auth/login` - Custom login endpoint (returns user details)
- `POST /token` - OAuth2 standard token endpoint (Swagger UI uses this)
- `POST /auth/change-password` - Change password for authenticated user
- All other endpoints - Now accessible with OAuth2 token

---

## 🎓 Next Steps

1. ✅ Try OAuth2 login in Swagger UI
2. ✅ Update your frontend to use similar OAuth2 flow
3. ✅ Test with different users
4. ✅ Deploy to production

---

**Status:** ✅ Production Ready  
**Last Updated:** October 24, 2025  
**Version:** 1.0
