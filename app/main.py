"""FastAPI application entry point."""
import os
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.openapi.utils import get_openapi
from dotenv import load_dotenv
from app.database import Base, engine
from app.routes.companies_users import companies_router, users_router
from app.routes.auth import auth_router
from app.routes.jewel_types import jewel_types_router
from app.routes.jewel_rates import jewel_rates_router
from app.routes.bank_details import bank_details_router
from app.routes.schemes import schemes_router
from app.routes.customers import customer_details_router
from app.routes.chart_of_accounts import coa_router
from app.routes.ledger_entries import ledger_router
from app.routes.pledges import router as pledges_router
from app.routes.receipts import router as receipts_router
from app.routes.bank_pledges import router as bank_pledges_router
from app.swagger_auth import swagger_auth_router

load_dotenv()

# Create database tables - with error handling
try:
    Base.metadata.create_all(bind=engine)
except Exception as e:
    print(f"⚠️  Warning: Could not create database tables on startup: {e}")
    print("This may be OK if the database is unreachable during development.")
    print("Database tables will be created on first request if possible.")

# Initialize FastAPI app
app = FastAPI(
    title="Company & User Management API",
    description="A FastAPI application for managing companies and users with PostgreSQL database",
    version="1.0.0"
)

# CORS Configuration - Allow development tools and specified origins
# For Postman and development: Allow all origins
# For production: Restrict to specific domains
DEBUG = os.getenv("DEBUG", "True").lower() == "true"

if DEBUG:
    # Development mode - Allow all for testing (Postman, browser, etc.)
    CORS_ORIGINS = ["*"]
else:
    # Production mode - Restrict to specific origins
    CORS_ORIGINS = os.getenv("CORS_ORIGINS", "https://yourdomain.com").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# Mount static files for serving uploaded images
uploads_dir = Path(__file__).parent.parent / "uploads"
uploads_dir.mkdir(exist_ok=True)
app.mount("/uploads", StaticFiles(directory=str(uploads_dir)), name="uploads")

# Include routes
app.include_router(companies_router)
app.include_router(users_router)
app.include_router(auth_router)
app.include_router(swagger_auth_router)  # OAuth2 login for Swagger UI
app.include_router(jewel_types_router)
app.include_router(jewel_rates_router)
app.include_router(bank_details_router)
app.include_router(schemes_router)
app.include_router(customer_details_router)
app.include_router(coa_router)
app.include_router(ledger_router)
app.include_router(pledges_router)
app.include_router(receipts_router)
app.include_router(bank_pledges_router)


# Configure OAuth2 for Swagger UI
def custom_openapi():
    """Configure OAuth2 authentication in Swagger UI."""
    if app.openapi_schema:
        return app.openapi_schema
    
    openapi_schema = get_openapi(
        title="Pledge Receipt Management API",
        version="1.0.0",
        description="FastAPI application for managing pledges, customers, and receipts",
        routes=app.routes,
    )
    
    # Add OAuth2 security scheme
    openapi_schema["components"]["securitySchemes"] = {
        "OAuth2PasswordBearer": {
            "type": "oauth2",
            "flows": {
                "password": {
                    "tokenUrl": "/token",
                    "scopes": {}
                }
            }
        }
    }
    
    # Apply security to all endpoints (except login and public endpoints)
    for path, methods in openapi_schema["paths"].items():
        # Skip token endpoint and health check
        if path in ["/token", "/health", "/"]:
            continue
        
        for method, operation in methods.items():
            if method in ["get", "post", "put", "delete", "patch"]:
                # Add security requirement to operation
                if "security" not in operation:
                    operation["security"] = [{"OAuth2PasswordBearer": []}]
    
    app.openapi_schema = openapi_schema
    return app.openapi_schema


app.openapi = custom_openapi


@app.get("/")
def read_root():
    """Root endpoint."""
    return {
        "message": "Welcome to Company & User Management API",
        "docs": "/docs",
        "openapi_schema": "/openapi.json"
    }


@app.get("/health")
def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}

