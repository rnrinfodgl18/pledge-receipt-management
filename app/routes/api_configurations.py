"""API Configuration routes for managing external API integrations."""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime

from app.database import get_db
from app.models import (
    ApiConfiguration as ApiConfigurationModel,
    Company as CompanyModel,
    User as UserModel,
)
from app.schemas import (
    ApiConfiguration,
    ApiConfigurationCreate,
    ApiConfigurationUpdate,
    ApiConfigurationResponse,
)
from app.auth import get_current_user

router = APIRouter(prefix="/api-configurations", tags=["API Configurations"])


@router.post("/", response_model=ApiConfiguration, status_code=status.HTTP_201_CREATED)
def create_api_configuration(
    config_data: ApiConfigurationCreate,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
):
    """
    Create a new API configuration for external data fetch.
    
    - Stores base URL and authentication details
    - Supports multiple auth types: NONE, API_KEY, BEARER_TOKEN, BASIC_AUTH, OAUTH2
    - Can store custom headers as JSON string
    - Configure timeout and retry settings
    
    Example:
    ```json
    {
      "company_id": 1,
      "api_name": "Old Data API",
      "api_type": "DATA_FETCH",
      "base_url": "https://api.olddata.com/v1",
      "api_key": "your-api-key",
      "auth_type": "API_KEY",
      "timeout_seconds": 30,
      "retry_count": 3,
      "description": "API for fetching old pledge data"
    }
    ```
    """
    # Validate company exists
    company = db.query(CompanyModel).filter(
        CompanyModel.id == config_data.company_id
    ).first()
    
    if not company:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Company not found"
        )
    
    # Check if API name already exists for company
    existing = db.query(ApiConfigurationModel).filter(
        ApiConfigurationModel.company_id == config_data.company_id,
        ApiConfigurationModel.api_name == config_data.api_name
    ).first()
    
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"API configuration '{config_data.api_name}' already exists for this company"
        )
    
    try:
        new_config = ApiConfigurationModel(
            company_id=config_data.company_id,
            api_name=config_data.api_name,
            api_type=config_data.api_type,
            base_url=config_data.base_url,
            api_key=config_data.api_key,
            api_secret=config_data.api_secret,
            auth_type=config_data.auth_type,
            custom_headers=config_data.custom_headers,
            timeout_seconds=config_data.timeout_seconds,
            retry_count=config_data.retry_count,
            description=config_data.description,
            is_active=True,
            created_by=current_user.id
        )
        
        db.add(new_config)
        db.commit()
        db.refresh(new_config)
        
        return new_config
    
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error creating API configuration: {str(e)}"
        )


@router.get("/{company_id}", response_model=List[ApiConfigurationResponse])
def get_api_configurations(
    company_id: int,
    api_type: Optional[str] = None,
    is_active: Optional[bool] = None,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
):
    """
    Get all API configurations for a company.
    
    Query parameters:
    - api_type: Filter by type (DATA_FETCH, INTEGRATION, WEBHOOK)
    - is_active: Filter by active status
    
    Note: Sensitive fields (api_key, api_secret) are excluded from response
    """
    # Validate company exists
    company = db.query(CompanyModel).filter(CompanyModel.id == company_id).first()
    if not company:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Company not found"
        )
    
    query = db.query(ApiConfigurationModel).filter(
        ApiConfigurationModel.company_id == company_id
    )
    
    if api_type:
        query = query.filter(ApiConfigurationModel.api_type == api_type)
    if is_active is not None:
        query = query.filter(ApiConfigurationModel.is_active == is_active)
    
    configs = query.order_by(ApiConfigurationModel.api_name).all()
    return configs


@router.get("/detail/{config_id}", response_model=ApiConfiguration)
def get_api_configuration(
    config_id: int,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
):
    """
    Get specific API configuration with all details including sensitive fields.
    
    Note: This endpoint returns api_key and api_secret.
    Use with caution and ensure proper access control.
    """
    config = db.query(ApiConfigurationModel).filter(
        ApiConfigurationModel.id == config_id
    ).first()
    
    if not config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="API configuration not found"
        )
    
    return config


@router.put("/{config_id}", response_model=ApiConfiguration)
def update_api_configuration(
    config_id: int,
    config_data: ApiConfigurationUpdate,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
):
    """
    Update API configuration.
    
    - Can update all fields including base_url, credentials, and settings
    - Partial updates supported (only provided fields will be updated)
    """
    config = db.query(ApiConfigurationModel).filter(
        ApiConfigurationModel.id == config_id
    ).first()
    
    if not config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="API configuration not found"
        )
    
    try:
        update_data = config_data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(config, key, value)
        
        db.commit()
        db.refresh(config)
        return config
    
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error updating API configuration: {str(e)}"
        )


@router.delete("/{config_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_api_configuration(
    config_id: int,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
):
    """
    Delete API configuration.
    
    Note: This permanently deletes the configuration.
    Consider deactivating instead by setting is_active=false.
    """
    config = db.query(ApiConfigurationModel).filter(
        ApiConfigurationModel.id == config_id
    ).first()
    
    if not config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="API configuration not found"
        )
    
    try:
        db.delete(config)
        db.commit()
        return None
    
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error deleting API configuration: {str(e)}"
        )


@router.post("/{config_id}/test-connection")
def test_api_connection(
    config_id: int,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
):
    """
    Test API connection with configured settings.
    
    - Sends a test request to the base_url
    - Updates last_used_at timestamp on success
    - Returns connection status and response details
    """
    config = db.query(ApiConfigurationModel).filter(
        ApiConfigurationModel.id == config_id
    ).first()
    
    if not config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="API configuration not found"
        )
    
    try:
        import requests
        import json
        
        # Prepare headers
        headers = {}
        
        # Add authentication
        if config.auth_type == "API_KEY" and config.api_key:
            headers["X-API-Key"] = config.api_key
        elif config.auth_type == "BEARER_TOKEN" and config.api_key:
            headers["Authorization"] = f"Bearer {config.api_key}"
        elif config.auth_type == "BASIC_AUTH" and config.api_key and config.api_secret:
            from requests.auth import HTTPBasicAuth
            auth = HTTPBasicAuth(config.api_key, config.api_secret)
        else:
            auth = None
        
        # Add custom headers
        if config.custom_headers:
            try:
                custom = json.loads(config.custom_headers)
                headers.update(custom)
            except:
                pass
        
        # Send test request
        response = requests.get(
            config.base_url,
            headers=headers,
            auth=auth if config.auth_type == "BASIC_AUTH" else None,
            timeout=config.timeout_seconds
        )
        
        # Update last_used_at
        config.last_used_at = datetime.now()
        db.commit()
        
        return {
            "status": "success" if response.status_code < 400 else "failed",
            "status_code": response.status_code,
            "message": f"Connection test {'successful' if response.status_code < 400 else 'failed'}",
            "response_time_ms": response.elapsed.total_seconds() * 1000,
            "config_id": config_id,
            "api_name": config.api_name,
            "base_url": config.base_url
        }
    
    except requests.exceptions.Timeout:
        return {
            "status": "failed",
            "message": f"Connection timeout after {config.timeout_seconds} seconds",
            "config_id": config_id,
            "api_name": config.api_name
        }
    except requests.exceptions.ConnectionError as e:
        return {
            "status": "failed",
            "message": f"Connection error: {str(e)}",
            "config_id": config_id,
            "api_name": config.api_name
        }
    except Exception as e:
        return {
            "status": "failed",
            "message": f"Error: {str(e)}",
            "config_id": config_id,
            "api_name": config.api_name
        }


@router.get("/types/list")
def get_api_types(
    current_user: UserModel = Depends(get_current_user),
):
    """
    Get list of supported API types.
    
    Returns predefined API types that can be used when creating configurations.
    """
    return {
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


@router.get("/auth-types/list")
def get_auth_types(
    current_user: UserModel = Depends(get_current_user),
):
    """
    Get list of supported authentication types.
    
    Returns predefined auth types that can be used when creating configurations.
    """
    return {
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
