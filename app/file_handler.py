"""File upload utilities for handling image uploads."""
import os
import shutil
from pathlib import Path
from fastapi import UploadFile
from datetime import datetime

# Define upload directory
UPLOAD_DIR = Path(__file__).parent.parent / "uploads"
COMPANY_LOGOS_DIR = UPLOAD_DIR / "company_logos"
ID_PROOFS_DIR = UPLOAD_DIR / "id_proofs"
PLEDGE_PHOTOS_DIR = UPLOAD_DIR / "pledge_photos"

# Ensure directories exist
COMPANY_LOGOS_DIR.mkdir(parents=True, exist_ok=True)
ID_PROOFS_DIR.mkdir(parents=True, exist_ok=True)
PLEDGE_PHOTOS_DIR.mkdir(parents=True, exist_ok=True)


def save_company_logo(file: UploadFile, company_id: int) -> str:
    """
    Save company logo file and return the file path.
    
    Args:
        file: UploadFile object from FastAPI
        company_id: Company ID to organize files
    
    Returns:
        Relative file path for database storage
    
    Raises:
        ValueError: If file type is not allowed
    """
    # Allowed file types
    ALLOWED_EXTENSIONS = {".png", ".jpg", ".jpeg", ".gif", ".webp"}
    
    # Validate file extension
    file_ext = Path(file.filename).suffix.lower()
    if file_ext not in ALLOWED_EXTENSIONS:
        raise ValueError(f"File type not allowed. Allowed types: {ALLOWED_EXTENSIONS}")
    
    # Validate file size (max 5MB)
    MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB
    file.file.seek(0, 2)  # Seek to end
    file_size = file.file.tell()
    file.file.seek(0)  # Reset to beginning
    
    if file_size > MAX_FILE_SIZE:
        raise ValueError(f"File size exceeds maximum allowed size of 5MB")
    
    # Create filename with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"company_{company_id}_{timestamp}{file_ext}"
    
    # Full path for saving
    file_path = COMPANY_LOGOS_DIR / filename
    
    # Save file
    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        raise Exception(f"Failed to save file: {str(e)}")
    
    # Return relative path for database
    relative_path = f"uploads/company_logos/{filename}"
    return relative_path


def delete_company_logo(file_path: str) -> bool:
    """
    Delete company logo file.
    
    Args:
        file_path: Relative file path from database
    
    Returns:
        True if successful, False otherwise
    """
    try:
        full_path = Path(__file__).parent.parent / file_path
        if full_path.exists():
            full_path.unlink()  # Delete file
            return True
        return False
    except Exception as e:
        print(f"Error deleting file: {str(e)}")
        return False


def save_id_proof(file: UploadFile, customer_id: int) -> str:
    """
    Save customer ID proof file and return the file path.
    
    Args:
        file: UploadFile object from FastAPI
        customer_id: Customer ID to organize files
    
    Returns:
        Relative file path for database storage
    
    Raises:
        ValueError: If file type is not allowed
    """
    # Allowed file types
    ALLOWED_EXTENSIONS = {".png", ".jpg", ".jpeg", ".pdf", ".gif", ".webp"}
    
    # Validate file extension
    file_ext = Path(file.filename).suffix.lower()
    if file_ext not in ALLOWED_EXTENSIONS:
        raise ValueError(f"File type not allowed. Allowed types: {ALLOWED_EXTENSIONS}")
    
    # Validate file size (max 10MB for documents)
    MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
    file.file.seek(0, 2)  # Seek to end
    file_size = file.file.tell()
    file.file.seek(0)  # Reset to beginning
    
    if file_size > MAX_FILE_SIZE:
        raise ValueError(f"File size exceeds maximum allowed size of 10MB")
    
    # Create filename with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"customer_{customer_id}_{timestamp}{file_ext}"
    
    # Full path for saving
    file_path = ID_PROOFS_DIR / filename
    
    # Save file
    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        raise Exception(f"Failed to save file: {str(e)}")
    
    # Return relative path for database
    relative_path = f"uploads/id_proofs/{filename}"
    return relative_path


def delete_id_proof(file_path: str) -> bool:
    """
    Delete customer ID proof file.
    
    Args:
        file_path: Relative file path from database
    
    Returns:
        True if successful, False otherwise
    """
    try:
        full_path = Path(__file__).parent.parent / file_path
        if full_path.exists():
            full_path.unlink()  # Delete file
            return True
        return False
    except Exception as e:
        print(f"Error deleting file: {str(e)}")
        return False


def get_upload_directory() -> str:
    """Get the uploads directory path."""
    return str(UPLOAD_DIR)


def save_pledge_photo(file: UploadFile, pledge_id: int) -> str:
    """
    Save pledge photo file and return the file path.
    
    Args:
        file: UploadFile object from FastAPI
        pledge_id: Pledge ID to organize files
    
    Returns:
        Relative file path for database storage
    
    Raises:
        ValueError: If file type is not allowed
    """
    # Allowed file types
    ALLOWED_EXTENSIONS = {".png", ".jpg", ".jpeg", ".gif", ".webp", ".bmp"}
    
    # Validate file extension
    file_ext = Path(file.filename).suffix.lower()
    if file_ext not in ALLOWED_EXTENSIONS:
        raise ValueError(f"File type not allowed. Allowed types: {ALLOWED_EXTENSIONS}")
    
    # Validate file size (max 8MB for images)
    MAX_FILE_SIZE = 8 * 1024 * 1024  # 8MB
    file.file.seek(0, 2)  # Seek to end
    file_size = file.file.tell()
    file.file.seek(0)  # Reset to beginning
    
    if file_size > MAX_FILE_SIZE:
        raise ValueError(f"File size exceeds maximum allowed size of 8MB")
    
    # Create filename with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"pledge_{pledge_id}_{timestamp}{file_ext}"
    
    # Full path for saving
    file_path = PLEDGE_PHOTOS_DIR / filename
    
    # Save file
    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        raise Exception(f"Failed to save file: {str(e)}")
    
    # Return relative path for database
    relative_path = f"uploads/pledge_photos/{filename}"
    return relative_path


def delete_pledge_photo(file_path: str) -> bool:
    """
    Delete pledge photo file.
    
    Args:
        file_path: Relative file path from database
    
    Returns:
        True if successful, False otherwise
    """
    try:
        full_path = Path(__file__).parent.parent / file_path
        if full_path.exists():
            full_path.unlink()  # Delete file
            return True
        return False
    except Exception as e:
        print(f"Error deleting pledge photo: {str(e)}")
        return False

