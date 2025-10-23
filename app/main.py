"""FastAPI application entry point."""
import os
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
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
app.include_router(jewel_types_router)
app.include_router(jewel_rates_router)
app.include_router(bank_details_router)
app.include_router(schemes_router)
app.include_router(customer_details_router)
app.include_router(coa_router)
app.include_router(ledger_router)
app.include_router(pledges_router)
app.include_router(receipts_router)


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

