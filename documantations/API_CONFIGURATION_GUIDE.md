# API Configuration Management - Complete Guide

## Overview
System to store and manage external API configurations for fetching old data or integrating with secondary APIs. Stores base URLs, authentication credentials, and connection settings securely.

## Database Table

### api_configurations
Stores external API configurations with authentication details.

**Columns:**
- `id` - Primary key
- `company_id` - Foreign key to companies
- `api_name` - Name of API (e.g., "Old Data API", "Secondary API")
- `api_type` - Type: DATA_FETCH, INTEGRATION, WEBHOOK, SYNC
- `base_url` - API base URL (e.g., https://api.olddata.com/v1)
- `api_key` - API key for authentication (optional)
- `api_secret` - API secret for authentication (optional)
- `auth_type` - Authentication type: NONE, API_KEY, BEARER_TOKEN, BASIC_AUTH, OAUTH2
- `custom_headers` - JSON string for additional headers
- `timeout_seconds` - Request timeout (default: 30)
- `retry_count` - Number of retries (default: 3)
- `is_active` - Active status
- `last_used_at` - Last connection timestamp
- `description` - Optional description
- `created_by`, `created_at`, `updated_at` - Audit fields

## API Endpoints

### Create API Configuration
```
POST /api-configurations/
```

**Request:**
```json
{
  "company_id": 1,
  "api_name": "Old Data API",
  "api_type": "DATA_FETCH",
  "base_url": "https://api.olddata.com/v1",
  "api_key": "your-api-key-here",
  "api_secret": "your-secret-here",
  "auth_type": "API_KEY",
  "custom_headers": "{\"X-Custom-Header\": \"value\"}",
  "timeout_seconds": 30,
  "retry_count": 3,
  "description": "API for fetching old pledge data"
}
```

**Response:**
```json
{
  "id": 1,
  "company_id": 1,
  "api_name": "Old Data API",
  "api_type": "DATA_FETCH",
  "base_url": "https://api.olddata.com/v1",
  "api_key": "your-api-key-here",
  "api_secret": "your-secret-here",
  "auth_type": "API_KEY",
  "timeout_seconds": 30,
  "retry_count": 3,
  "is_active": true,
  "last_used_at": null,
  "created_at": "2025-10-30T10:00:00",
  "updated_at": "2025-10-30T10:00:00"
}
```

### Get All API Configurations
```
GET /api-configurations/{company_id}
GET /api-configurations/{company_id}?api_type=DATA_FETCH
GET /api-configurations/{company_id}?is_active=true
```

**Response:**
```json
[
  {
    "id": 1,
    "company_id": 1,
    "api_name": "Old Data API",
    "api_type": "DATA_FETCH",
    "base_url": "https://api.olddata.com/v1",
    "auth_type": "API_KEY",
    "timeout_seconds": 30,
    "retry_count": 3,
    "is_active": true,
    "last_used_at": "2025-10-30T12:00:00",
    "description": "API for fetching old pledge data",
    "created_at": "2025-10-30T10:00:00",
    "updated_at": "2025-10-30T10:00:00"
  }
]
```
**Note:** Sensitive fields (api_key, api_secret) are excluded from list response.

### Get API Configuration Details
```
GET /api-configurations/detail/{config_id}
```

**Response:** Returns complete configuration including api_key and api_secret.

### Update API Configuration
```
PUT /api-configurations/{config_id}
```

**Request:**
```json
{
  "base_url": "https://api.newdata.com/v2",
  "api_key": "new-api-key",
  "timeout_seconds": 60,
  "description": "Updated to v2 API"
}
```

### Delete API Configuration
```
DELETE /api-configurations/{config_id}
```

**Note:** Consider deactivating instead using `PUT` with `is_active: false`

### Test API Connection
```
POST /api-configurations/{config_id}/test-connection
```

**Response:**
```json
{
  "status": "success",
  "status_code": 200,
  "message": "Connection test successful",
  "response_time_ms": 125.5,
  "config_id": 1,
  "api_name": "Old Data API",
  "base_url": "https://api.olddata.com/v1"
}
```

**Failed Response:**
```json
{
  "status": "failed",
  "message": "Connection timeout after 30 seconds",
  "config_id": 1,
  "api_name": "Old Data API"
}
```

### Get API Types List
```
GET /api-configurations/types/list
```

**Response:**
```json
{
  "api_types": [
    {
      "value": "DATA_FETCH",
      "label": "Data Fetch API",
      "description": "APIs for fetching external data (old data, reports, etc.)"
    },
    {
      "value": "INTEGRATION",
      "label": "Integration API",
      "description": "Third-party integration APIs (payment, SMS, etc.)"
    },
    {
      "value": "WEBHOOK",
      "label": "Webhook API",
      "description": "Webhook endpoints for receiving notifications"
    },
    {
      "value": "SYNC",
      "label": "Sync API",
      "description": "APIs for data synchronization"
    }
  ]
}
```

### Get Authentication Types List
```
GET /api-configurations/auth-types/list
```

**Response:**
```json
{
  "auth_types": [
    {
      "value": "NONE",
      "label": "No Authentication",
      "description": "Public API with no authentication required"
    },
    {
      "value": "API_KEY",
      "label": "API Key",
      "description": "API key in header (X-API-Key)"
    },
    {
      "value": "BEARER_TOKEN",
      "label": "Bearer Token",
      "description": "Bearer token in Authorization header"
    },
    {
      "value": "BASIC_AUTH",
      "label": "Basic Authentication",
      "description": "Username and password (Base64 encoded)"
    },
    {
      "value": "OAUTH2",
      "label": "OAuth 2.0",
      "description": "OAuth 2.0 authentication flow"
    }
  ]
}
```

## Authentication Types Explained

### 1. API_KEY
- API key sent in `X-API-Key` header
- Store API key in `api_key` field
- Example: `X-API-Key: your-api-key-123`

### 2. BEARER_TOKEN
- Token sent in Authorization header
- Store token in `api_key` field
- Example: `Authorization: Bearer eyJhbGc...`

### 3. BASIC_AUTH
- Username and password authentication
- Store username in `api_key` field
- Store password in `api_secret` field
- Automatically Base64 encoded by the system

### 4. OAUTH2
- OAuth 2.0 authentication flow
- Store access token in `api_key` field
- Store refresh token in `api_secret` field (if applicable)

### 5. NONE
- No authentication required
- For public APIs

## Usage Examples

### Example 1: Old Data API with API Key

```bash
# Create configuration
POST /api-configurations/
{
  "company_id": 1,
  "api_name": "Old Pledge Data API",
  "api_type": "DATA_FETCH",
  "base_url": "https://old.pawnshop.com/api/v1",
  "api_key": "pk_live_abc123xyz",
  "auth_type": "API_KEY",
  "description": "Fetch historical pledge records"
}

# Test connection
POST /api-configurations/1/test-connection

# Response:
{
  "status": "success",
  "status_code": 200,
  "message": "Connection test successful",
  "response_time_ms": 150.2
}
```

### Example 2: Integration API with Bearer Token

```bash
POST /api-configurations/
{
  "company_id": 1,
  "api_name": "Payment Gateway",
  "api_type": "INTEGRATION",
  "base_url": "https://payments.gateway.com/api",
  "api_key": "Bearer_eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "auth_type": "BEARER_TOKEN",
  "timeout_seconds": 60,
  "retry_count": 5,
  "description": "Payment processing integration"
}
```

### Example 3: Webhook Endpoint

```bash
POST /api-configurations/
{
  "company_id": 1,
  "api_name": "SMS Notification Webhook",
  "api_type": "WEBHOOK",
  "base_url": "https://sms.provider.com/webhooks/notifications",
  "api_key": "webhook_secret_key",
  "auth_type": "API_KEY",
  "description": "Receive SMS delivery notifications"
}
```

### Example 4: Basic Auth API

```bash
POST /api-configurations/
{
  "company_id": 1,
  "api_name": "Legacy System API",
  "api_type": "SYNC",
  "base_url": "https://legacy.system.com/api",
  "api_key": "admin_user",
  "api_secret": "admin_password",
  "auth_type": "BASIC_AUTH",
  "description": "Sync data with legacy system"
}
```

### Example 5: Custom Headers

```bash
POST /api-configurations/
{
  "company_id": 1,
  "api_name": "Custom API",
  "api_type": "DATA_FETCH",
  "base_url": "https://api.custom.com/v1",
  "api_key": "api_key_123",
  "auth_type": "API_KEY",
  "custom_headers": "{\"X-Custom-Id\": \"12345\", \"X-Region\": \"IN\"}",
  "description": "API with custom headers"
}
```

## Security Features

### 1. Sensitive Data Protection
- `api_key` and `api_secret` excluded from list responses
- Only accessible via detail endpoint
- Requires authentication to access

### 2. Connection Testing
- Test API connection before use
- Validates credentials
- Checks response time
- Updates `last_used_at` timestamp

### 3. Audit Trail
- Tracks who created configuration (`created_by`)
- Timestamps for creation and updates
- Last usage tracking

### 4. Access Control
- Company-specific configurations
- Authentication required for all endpoints
- Only authorized users can access

## Integration Workflow

### Step 1: Create API Configuration
```bash
POST /api-configurations/
{
  "company_id": 1,
  "api_name": "Old Data API",
  "api_type": "DATA_FETCH",
  "base_url": "https://api.olddata.com/v1",
  "api_key": "your_key",
  "auth_type": "API_KEY"
}
```

### Step 2: Test Connection
```bash
POST /api-configurations/1/test-connection
# Verify connection is successful
```

### Step 3: Use in Your Application
```python
# Fetch configuration
config = get_api_configuration(config_id=1)

# Use in your data fetch logic
import requests

headers = {"X-API-Key": config.api_key}
response = requests.get(
    f"{config.base_url}/pledges",
    headers=headers,
    timeout=config.timeout_seconds
)

# Update last_used_at automatically via test-connection
# or update manually in your code
```

### Step 4: Monitor Usage
```bash
GET /api-configurations/1
# Check last_used_at timestamp
# Monitor connection status
```

## Best Practices

### 1. Naming Convention
- Use descriptive names: "Old Pledge Data API", "Payment Gateway"
- Include version in name if API has versions: "API v2"

### 2. Security
- Don't expose api_key/api_secret in logs
- Use HTTPS URLs only
- Rotate API keys regularly
- Set appropriate timeout values

### 3. Testing
- Always test connection after creation
- Re-test after updates
- Monitor last_used_at for stale configurations

### 4. Error Handling
- Set appropriate retry_count
- Handle timeout gracefully
- Log connection failures

### 5. Maintenance
- Deactivate unused configurations (set is_active=false)
- Update credentials when they expire
- Keep descriptions up-to-date

## Tamil Guide (தமிழ் வழிகாட்டி)

### API Configuration என்றால் என்ன?

பழைய தரவுகளை எடுக்க வேண்டும் என்றால், secondary API ஐ connect செய்ய இந்த system உதவும்.

### எப்படி பயன்படுத்துவது:

**1. Configuration உருவாக்கு:**
```bash
POST /api-configurations/
{
  "company_id": 1,
  "api_name": "பழைய தரவு API",
  "api_type": "DATA_FETCH",
  "base_url": "https://old-api.com/v1",
  "api_key": "உங்கள் API key",
  "auth_type": "API_KEY"
}
```

**2. Connection Test செய்:**
```bash
POST /api-configurations/1/test-connection
```

**3. பழைய தரவை Fetch செய்:**
- Configuration இல் உள்ள base_url பயன்படுத்தி
- API key உடன் request அனுப்பு
- தரவு கிடைக்கும்!

### முக்கிய அம்சங்கள்:
- ✅ Base URL store செய்யலாம்
- ✅ API key/secret பாதுகாப்பாக சேமிக்கப்படும்
- ✅ Connection test செய்யலாம்
- ✅ Multiple APIs manage செய்யலாம்
- ✅ Authentication types support
- ✅ Timeout settings

## Summary

✅ **Table Created:** api_configurations (17 columns)
✅ **9 Endpoints:** Create, Read, Update, Delete, Test Connection, List Types
✅ **5 Auth Types:** NONE, API_KEY, BEARER_TOKEN, BASIC_AUTH, OAUTH2
✅ **4 API Types:** DATA_FETCH, INTEGRATION, WEBHOOK, SYNC
✅ **Security:** Sensitive data protected, authentication required
✅ **Testing:** Built-in connection testing capability
✅ **Flexible:** Custom headers, timeout, retry settings

Perfect for storing external API configurations for data fetching from old systems or secondary APIs! 🚀
