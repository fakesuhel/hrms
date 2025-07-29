from bson import ObjectId
from pydantic import BaseModel
from typing import Any, Dict
from pydantic_core import core_schema
import os
import uuid
from datetime import datetime, timezone, timedelta

# IST timezone (UTC+5:30)
IST = timezone(timedelta(hours=5, minutes=30))

class PyObjectId(ObjectId):
    @classmethod
    def __get_pydantic_core_schema__(cls, source_type: Any, handler) -> core_schema.CoreSchema:
        return core_schema.with_info_plain_validator_function(cls.validate)
    
    @classmethod
    def validate(cls, v, info=None):
        if isinstance(v, ObjectId):
            return v
        if isinstance(v, str) and ObjectId.is_valid(v):
            return ObjectId(v)
        raise ValueError("Invalid ObjectId")
    
    @classmethod
    def __get_pydantic_json_schema__(cls, core_schema: Dict[str, Any], handler) -> Dict[str, Any]:
        return {"type": "string"}

def paginate(items, page: int = 1, size: int = 10):
    """Simple pagination function"""
    start = (page - 1) * size
    end = start + size
    total = len(items)
    return {
        "items": items[start:end],
        "total": total,
        "page": page,
        "size": size,
        "pages": (total + size - 1) // size  # Ceiling division
    }

def generate_filename(original_filename: str, prefix: str = "") -> str:
    """Generate a unique filename with optional prefix"""
    file_extension = os.path.splitext(original_filename)[1].lower()
    unique_id = uuid.uuid4().hex
    if prefix:
        return f"{prefix}_{unique_id}{file_extension}"
    return f"{unique_id}{file_extension}"

def allowed_file_extension(filename: str) -> bool:
    """Check if file extension is allowed"""
    allowed_extensions = {'.pdf', '.jpg', '.jpeg', '.png', '.doc', '.docx'}
    file_extension = os.path.splitext(filename)[1].lower()
    return file_extension in allowed_extensions

def create_directory_if_not_exists(directory_path: str):
    """Create directory if it doesn't exist"""
    if not os.path.exists(directory_path):
        os.makedirs(directory_path, exist_ok=True)

def get_ist_now():
    """Get current datetime in IST timezone"""
    return datetime.now(IST)

def get_ist_date_today():
    """Get current date in IST timezone"""
    return get_ist_now().date()

def get_ist_datetime_iso():
    """Get current datetime in IST timezone as ISO format string"""
    return get_ist_now().isoformat()

def get_ist_date_iso():
    """Get current date in IST timezone as ISO format string"""
    return get_ist_date_today().isoformat()

def ensure_timezone_aware(dt):
    """Ensure a datetime object is timezone-aware (assume IST if naive)"""
    if dt is None:
        return None
        
    # Convert string to datetime if needed
    if isinstance(dt, str):
        try:
            dt = datetime.fromisoformat(dt.replace('Z', '+00:00'))
        except ValueError:
            try:
                dt = datetime.strptime(dt, "%Y-%m-%dT%H:%M:%S.%f")
            except ValueError:
                # Final fallback
                dt = datetime.fromisoformat(dt)
    
    # If timezone-naive, assume it's in IST
    if dt.tzinfo is None:
        return dt.replace(tzinfo=IST)
    elif dt.tzinfo != IST:
        # Convert to IST if it's in a different timezone
        return dt.astimezone(IST)
    return dt

def convert_utc_to_ist(dt):
    """Convert a UTC datetime to IST timezone"""
    if dt is None:
        return None
        
    # Ensure the datetime is timezone-aware
    if dt.tzinfo is None:
        # If naive, assume UTC
        dt = dt.replace(tzinfo=timezone.utc)
    
    # Convert to IST
    return dt.astimezone(IST)
