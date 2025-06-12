from bson import ObjectId
from pydantic import BaseModel

class PyObjectId(ObjectId):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate
    
    @classmethod
    def validate(cls, v):
        if not ObjectId.is_valid(v):
            raise ValueError("Invalid ObjectId")
        return ObjectId(v)
    
    @classmethod
    def __modify_schema__(cls, field_schema):
        field_schema.update(type="string")

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