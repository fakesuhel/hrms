from datetime import datetime, date
from typing import Any
from bson import ObjectId

def json_serializer(obj: Any) -> str:
    """Custom JSON serializer for objects not serializable by default json module."""
    if isinstance(obj, (datetime, date)):
        return obj.isoformat()
    if isinstance(obj, ObjectId):
        return str(obj)
    raise TypeError(f"Type {type(obj)} not serializable")