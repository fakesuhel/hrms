from datetime import datetime, timezone, timedelta
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from bson import ObjectId
from app.database import db
from pydantic_core import core_schema
from zoneinfo import ZoneInfo

# Asia/Kolkata timezone
KOLKATA_TZ = ZoneInfo('Asia/Kolkata')

# Get documents collection
documents_collection = db["documents"]

def get_kolkata_now():
    """Get current datetime in Asia/Kolkata timezone"""
    return datetime.now(KOLKATA_TZ)

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

class DocumentBase(BaseModel):
    user_id: str
    document_type: str  # "aadhar", "pan", "10th", "graduation", etc.
    category: str  # "identity", "education", "employment", "other"
    original_filename: str
    stored_filename: str
    file_size: int
    file_extension: str
    mime_type: str

class DocumentCreate(DocumentBase):
    pass

class DocumentUpdate(BaseModel):
    document_type: Optional[str] = None
    category: Optional[str] = None
    original_filename: Optional[str] = None

class DocumentInDB(DocumentBase):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    created_at: datetime = Field(default_factory=get_kolkata_now)
    updated_at: datetime = Field(default_factory=get_kolkata_now)
    
    model_config = {
        "populate_by_name": True,
        "arbitrary_types_allowed": True,
        "from_attributes": True
    }

class DocumentResponse(DocumentBase):
    id: str = Field(alias="_id")
    created_at: datetime
    updated_at: datetime
    
    model_config = {
        "populate_by_name": True,
        "from_attributes": True
    }

class DatabaseDocuments:
    @staticmethod
    async def create_document(document_data: DocumentCreate) -> DocumentInDB:
        document_dict = document_data.model_dump()
        document_dict["created_at"] = get_kolkata_now()
        document_dict["updated_at"] = get_kolkata_now()
        
        result = documents_collection.insert_one(document_dict)
        document_dict["_id"] = result.inserted_id
        
        return DocumentInDB(**document_dict)
    
    @staticmethod
    async def get_user_documents(user_id: str, category: Optional[str] = None) -> List[DocumentInDB]:
        try:
            query = {"user_id": user_id}
            if category:
                query["category"] = category
            
            documents = list(documents_collection.find(query).sort("created_at", -1))
            result = []
            for doc in documents:
                try:
                    # Ensure proper field mapping for pydantic model
                    if "_id" in doc and "id" not in doc:
                        doc["id"] = doc["_id"]
                    result.append(DocumentInDB(**doc))
                except Exception as e:
                    print(f"Error creating DocumentInDB from doc: {doc}")
                    print(f"Error: {e}")
                    # Skip this document and continue
                    continue
            return result
        except Exception as e:
            print(f"Error in get_user_documents: {e}")
            raise e
    
    @staticmethod
    async def get_document_by_id(document_id: str) -> Optional[DocumentInDB]:
        try:
            id_obj = ObjectId(document_id) if isinstance(document_id, str) else document_id
            document = documents_collection.find_one({"_id": id_obj})
            if document:
                # Ensure proper field mapping for pydantic model
                if "_id" in document and "id" not in document:
                    document["id"] = document["_id"]
                return DocumentInDB(**document)
            return None
        except Exception as e:
            print(f"Error in get_document_by_id: {e}")
            return None
    
    @staticmethod
    async def delete_document(document_id: str) -> bool:
        try:
            id_obj = ObjectId(document_id) if isinstance(document_id, str) else document_id
            result = documents_collection.delete_one({"_id": id_obj})
            return result.deleted_count > 0
        except Exception as e:
            print(f"Error in delete_document: {e}")
            return False
    
    @staticmethod
    async def update_document(document_id: str, update_data: DocumentUpdate) -> Optional[DocumentInDB]:
        try:
            id_obj = ObjectId(document_id) if isinstance(document_id, str) else document_id
            update_dict = {k: v for k, v in update_data.model_dump().items() if v is not None}
            update_dict["updated_at"] = get_kolkata_now()
            
            result = documents_collection.update_one(
                {"_id": id_obj},
                {"$set": update_dict}
            )
            
            if result.modified_count > 0:
                updated_document = documents_collection.find_one({"_id": id_obj})
                return DocumentInDB(**updated_document)
            return None
        except Exception as e:
            print(f"Error in update_document: {e}")
            return None
