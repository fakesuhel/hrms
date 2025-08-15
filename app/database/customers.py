from datetime import datetime, timezone, timedelta
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, EmailStr
from bson import ObjectId
from app.database import db
from pydantic_core import core_schema
from zoneinfo import ZoneInfo

# Get customers collection
customers_collection = db["customers"]

# Asia/Kolkata timezone
KOLKATA_TZ = ZoneInfo('Asia/Kolkata')

def get_kolkata_now():
    """Get current datetime in Asia/Kolkata timezone"""
    return datetime.now(KOLKATA_TZ)


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

class CustomerBase(BaseModel):
    company_name: str
    contact_person: str
    email: EmailStr
    phone: str
    business_type: str
    industry: Optional[str] = None
    company_size: Optional[str] = None  # "startup", "small", "medium", "large", "enterprise"
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    country: str = "India"
    website: Optional[str] = None
    notes: Optional[str] = None
    
    model_config = {
        "populate_by_name": True,
        "arbitrary_types_allowed": True,
        "from_attributes": True
    }

class CustomerCreate(CustomerBase):
    account_manager: str  # Sales person managing this account
    lead_id: Optional[str] = None  # Original lead ID if converted from lead

class CustomerUpdate(BaseModel):
    company_name: Optional[str] = None
    contact_person: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    business_type: Optional[str] = None
    industry: Optional[str] = None
    company_size: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    country: Optional[str] = None
    website: Optional[str] = None
    status: Optional[str] = None
    account_manager: Optional[str] = None
    notes: Optional[str] = None

class CustomerInDB(CustomerBase):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    account_manager: str
    lead_id: Optional[str] = None
    status: str = "active"  # "active", "inactive", "potential", "churned"
    customer_value: float = 0.0  # Total business value
    acquisition_date: datetime = Field(default_factory=get_kolkata_now)
    last_interaction: Optional[datetime] = None
    created_at: datetime = Field(default_factory=get_kolkata_now)
    updated_at: datetime = Field(default_factory=get_kolkata_now)
    
    model_config = {
        "populate_by_name": True,
        "arbitrary_types_allowed": True,
        "from_attributes": True
    }

class CustomerResponse(CustomerBase):
    id: str = Field(alias="_id")
    account_manager: str
    lead_id: Optional[str] = None
    status: str
    customer_value: float
    acquisition_date: datetime
    last_interaction: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    
    model_config = {
        "populate_by_name": True,
        "from_attributes": True
    }

class DatabaseCustomers:
    collection = customers_collection
    
    @classmethod
    async def create_customer(cls, customer_data: CustomerCreate) -> CustomerInDB:
        """Create a new customer"""
        customer_dict = customer_data.model_dump()
        customer_dict["created_at"] = get_kolkata_now()
        customer_dict["updated_at"] = get_kolkata_now()
        customer_dict["status"] = "active"
        customer_dict["customer_value"] = 0.0
        customer_dict["acquisition_date"] = get_kolkata_now()
        
        result = cls.collection.insert_one(customer_dict)
        customer_dict["_id"] = result.inserted_id
        
        return CustomerInDB(**customer_dict)
    
    @classmethod
    async def get_customer_by_id(cls, customer_id: str) -> Optional[CustomerInDB]:
        """Get a customer by ID"""
        try:
            customer = cls.collection.find_one({"_id": ObjectId(customer_id)})
            if customer:
                return CustomerInDB(**customer)
            return None
        except Exception as e:
            print(f"Error getting customer by ID: {e}")
            return None
    
    @classmethod
    async def get_customers_by_manager(cls, manager_id: str, status: Optional[str] = None) -> List[CustomerInDB]:
        """Get customers managed by a specific account manager"""
        query = {"account_manager": manager_id}
        if status:
            query["status"] = status
        
        customers = list(cls.collection.find(query).sort("created_at", -1))
        return [CustomerInDB(**customer) for customer in customers]
    
    @classmethod
    async def get_all_customers(cls, status: Optional[str] = None) -> List[CustomerInDB]:
        """Get all customers"""
        query = {}
        if status:
            query["status"] = status
        
        customers = list(cls.collection.find(query).sort("created_at", -1))
        return [CustomerInDB(**customer) for customer in customers]
    
    @classmethod
    async def update_customer(cls, customer_id: str, update_data: CustomerUpdate) -> Optional[CustomerInDB]:
        """Update a customer"""
        try:
            update_dict = {k: v for k, v in update_data.model_dump().items() if v is not None}
            update_dict["updated_at"] = get_kolkata_now()
            
            result = cls.collection.update_one(
                {"_id": ObjectId(customer_id)},
                {"$set": update_dict}
            )
            
            if result.modified_count > 0:
                updated_customer = cls.collection.find_one({"_id": ObjectId(customer_id)})
                return CustomerInDB(**updated_customer)
            return None
        except Exception as e:
            print(f"Error updating customer: {e}")
            return None
    
    @classmethod
    async def delete_customer(cls, customer_id: str) -> bool:
        """Delete a customer"""
        try:
            result = cls.collection.delete_one({"_id": ObjectId(customer_id)})
            return result.deleted_count > 0
        except Exception as e:
            print(f"Error deleting customer: {e}")
            return False
    
    @classmethod
    async def get_customer_stats(cls, manager_id: Optional[str] = None) -> Dict[str, Any]:
        """Get customer statistics"""
        query = {"account_manager": manager_id} if manager_id else {}
        
        pipeline = [
            {"$match": query},
            {"$group": {
                "_id": "$status",
                "count": {"$sum": 1},
                "total_value": {"$sum": "$customer_value"}
            }}
        ]
        
        results = list(cls.collection.aggregate(pipeline))
        
        stats = {
            "total_customers": 0,
            "active": 0,
            "inactive": 0,
            "potential": 0,
            "churned": 0,
            "total_customer_value": 0
        }
        
        for result in results:
            status = result["_id"]
            count = result["count"]
            value = result["total_value"]
            
            stats["total_customers"] += count
            stats[status] = count
            stats["total_customer_value"] += value
        
        return stats
    
    @classmethod
    async def convert_lead_to_customer(cls, lead_id: str, customer_data: CustomerCreate) -> CustomerInDB:
        """Convert a lead to a customer"""
        # Add the lead_id to customer data
        customer_dict = customer_data.model_dump()
        customer_dict["lead_id"] = lead_id
        
        # Create customer
        return await cls.create_customer(CustomerCreate(**customer_dict))
