#!/bin/bash
# Quick test script for change password endpoint

API_URL="http://localhost:8000"

echo "🔐 Testing Change Password Endpoint"
echo "===================================="
echo ""

# Step 1: Login to get token
echo "Step 1: Logging in to get JWT token..."
LOGIN_RESPONSE=$(curl -s -X POST "$API_URL/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "admin",
    "password": "password"
  }')

echo "Login Response:"
echo "$LOGIN_RESPONSE" | jq '.'
echo ""

# Extract token
TOKEN=$(echo "$LOGIN_RESPONSE" | jq -r '.access_token')

if [ "$TOKEN" = "null" ] || [ -z "$TOKEN" ]; then
  echo "❌ Failed to get token. Check if user 'admin' exists with password 'password'"
  exit 1
fi

echo "✅ Token received: ${TOKEN:0:50}..."
echo ""

# Step 2: Change password
echo "Step 2: Changing password..."
CHANGE_RESPONSE=$(curl -s -X POST "$API_URL/auth/change-password" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "current_password": "password",
    "new_password": "newpassword123",
    "confirm_password": "newpassword123"
  }')

echo "Change Password Response:"
echo "$CHANGE_RESPONSE" | jq '.'
echo ""

# Step 3: Try logging in with new password
echo "Step 3: Verifying new password by logging in..."
NEW_LOGIN=$(curl -s -X POST "$API_URL/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "admin",
    "password": "newpassword123"
  }')

echo "Login with new password Response:"
echo "$NEW_LOGIN" | jq '.'
echo ""

# Check if new login was successful
NEW_TOKEN=$(echo "$NEW_LOGIN" | jq -r '.access_token')
if [ "$NEW_TOKEN" != "null" ] && [ ! -z "$NEW_TOKEN" ]; then
  echo "✅ SUCCESS! Password changed and new password works!"
else
  echo "❌ Failed to login with new password"
fi
