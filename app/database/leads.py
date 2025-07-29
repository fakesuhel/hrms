from datetime import datetime, date, timezone, timedelta
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, EmailStr
from bson import ObjectId
from app.database import db
from pydantic_core import core_schema

# Get leads collection
leads_collection = db["leads"]


# IST timezone (UTC+5:30)
IST = timezone(timedelta(hours=5, minutes=30))

def get_ist_now():
    """Get current datetime in IST timezone"""
    return datetime.now()

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

class LeadBase(BaseModel):
    company_name: str
    contact_person: str
    email: EmailStr
    phone: str
    business_type: str
    requirements: str
    budget_range: str  # "under-50k", "50k-100k", "100k-500k", "500k+"
    lead_source: str  # "website", "social_media", "referral", "cold_call", "event"
    priority: str = "medium"  # "low", "medium", "high", "urgent"
    notes: Optional[str] = None
    
    model_config = {
        "populate_by_name": True,
        "arbitrary_types_allowed": True,
        "from_attributes": True
    }

class LeadCreate(LeadBase):
    assigned_to: str  # Sales person user ID

class LeadUpdate(BaseModel):
    company_name: Optional[str] = None
    contact_person: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    business_type: Optional[str] = None
    requirements: Optional[str] = None
    budget_range: Optional[str] = None
    lead_source: Optional[str] = None
    status: Optional[str] = None
    priority: Optional[str] = None
    assigned_to: Optional[str] = None
    notes: Optional[str] = None

class LeadInDB(LeadBase):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    assigned_to: str
    status: str = "new"  # "new", "contacted", "qualified", "proposal", "negotiation", "closed_won", "closed_lost"
    lead_score: int = 0  # 0-100 scoring system
    last_contact_date: Optional[datetime] = None
    expected_closure_date: Optional[str] = None  # ISO date string
    deal_value: Optional[float] = None
    created_at: datetime = Field(default_factory=get_ist_now)
    updated_at: datetime = Field(default_factory=get_ist_now)
    
    model_config = {
        "populate_by_name": True,
        "arbitrary_types_allowed": True,
        "from_attributes": True
    }

class LeadResponse(LeadBase):
    id: str = Field(alias="_id")
    assigned_to: str
    status: str
    lead_score: int
    last_contact_date: Optional[datetime] = None
    expected_closure_date: Optional[str] = None
    deal_value: Optional[float] = None
    created_at: datetime
    updated_at: datetime
    
    model_config = {
        "populate_by_name": True,
        "from_attributes": True
    }

class LeadActivity(BaseModel):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    lead_id: str
    user_id: str  # Who performed the activity
    activity_type: str  # "call", "email", "meeting", "proposal", "follow_up", "note"
    subject: str
    description: Optional[str] = None
    activity_date: datetime = Field(default_factory=get_ist_now)
    created_at: datetime = Field(default_factory=get_ist_now)
    
    model_config = {
        "populate_by_name": True,
        "arbitrary_types_allowed": True,
        "from_attributes": True
    }

class LeadActivityCreate(BaseModel):
    activity_type: str
    subject: str
    description: Optional[str] = None
    activity_date: Optional[datetime] = None

class DatabaseLeads:
    collection = leads_collection
    
    @classmethod
    async def create_lead(cls, lead_data: LeadCreate) -> LeadInDB:
        """Create a new lead"""
        lead_dict = lead_data.model_dump()
        lead_dict["created_at"] = get_ist_now()
        lead_dict["updated_at"] = get_ist_now()
        lead_dict["status"] = "new"
        lead_dict["lead_score"] = 0
        
        result = cls.collection.insert_one(lead_dict)
        lead_dict["_id"] = result.inserted_id
        
        return LeadInDB(**lead_dict)
    
    @classmethod
    async def get_lead_by_id(cls, lead_id: str) -> Optional[LeadInDB]:
        """Get a lead by ID"""
        try:
            lead = cls.collection.find_one({"_id": ObjectId(lead_id)})
            if lead:
                return LeadInDB(**lead)
            return None
        except Exception as e:
            print(f"Error getting lead by ID: {e}")
            return None
    
    @classmethod
    async def get_leads_by_user(cls, user_id: str, status: Optional[str] = None) -> List[LeadInDB]:
        """Get leads assigned to a specific user"""
        query = {"assigned_to": user_id}
        if status:
            query["status"] = status
        
        leads = list(cls.collection.find(query).sort("created_at", -1))
        return [LeadInDB(**lead) for lead in leads]
    
    @classmethod
    async def get_all_leads(cls, department_filter: Optional[str] = None) -> List[LeadInDB]:
        """Get all leads (for managers)"""
        query = {}
        if department_filter:
            # Would need to join with users collection to filter by department
            pass
        
        leads = list(cls.collection.find(query).sort("created_at", -1))
        return [LeadInDB(**lead) for lead in leads]
    
    @classmethod
    async def update_lead(cls, lead_id: str, update_data: LeadUpdate) -> Optional[LeadInDB]:
        """Update a lead"""
        try:
            update_dict = {k: v for k, v in update_data.model_dump().items() if v is not None}
            update_dict["updated_at"] = get_ist_now()
            
            result = cls.collection.update_one(
                {"_id": ObjectId(lead_id)},
                {"$set": update_dict}
            )
            
            if result.modified_count > 0:
                updated_lead = cls.collection.find_one({"_id": ObjectId(lead_id)})
                return LeadInDB(**updated_lead)
            return None
        except Exception as e:
            print(f"Error updating lead: {e}")
            return None
    
    @classmethod
    async def delete_lead(cls, lead_id: str) -> bool:
        """Delete a lead"""
        try:
            result = cls.collection.delete_one({"_id": ObjectId(lead_id)})
            return result.deleted_count > 0
        except Exception as e:
            print(f"Error deleting lead: {e}")
            return False
    
    @classmethod
    async def get_lead_stats(cls, user_id: Optional[str] = None) -> Dict[str, Any]:
        """Get lead statistics"""
        query = {"assigned_to": user_id} if user_id else {}
        
        pipeline = [
            {"$match": query},
            {"$group": {
                "_id": "$status",
                "count": {"$sum": 1},
                "total_value": {"$sum": {"$ifNull": ["$deal_value", 0]}}
            }}
        ]
        
        results = list(cls.collection.aggregate(pipeline))
        
        stats = {
            "total_leads": 0,
            "new": 0,
            "contacted": 0,
            "qualified": 0,
            "proposal": 0,
            "negotiation": 0,
            "closed_won": 0,
            "closed_lost": 0,
            "total_pipeline_value": 0,
            "won_value": 0
        }
        
        for result in results:
            status = result["_id"]
            count = result["count"]
            value = result["total_value"]
            
            stats["total_leads"] += count
            stats[status] = count
            stats["total_pipeline_value"] += value
            
            if status == "closed_won":
                stats["won_value"] = value
        
        return stats

# Activity tracking collection
lead_activities_collection = db["lead_activities"]

class DatabaseLeadActivities:
    collection = lead_activities_collection
    
    @classmethod
    async def add_activity(cls, lead_id: str, user_id: str, activity_data: LeadActivityCreate) -> LeadActivity:
        """Add an activity to a lead"""
        activity_dict = activity_data.model_dump()
        activity_dict.update({
            "lead_id": lead_id,
            "user_id": user_id,
            "created_at": get_ist_now()
        })
        
        if not activity_dict.get("activity_date"):
            activity_dict["activity_date"] = get_ist_now()
        
        result = cls.collection.insert_one(activity_dict)
        activity_dict["_id"] = result.inserted_id
        
        return LeadActivity(**activity_dict)
    
    @classmethod
    async def get_lead_activities(cls, lead_id: str) -> List[LeadActivity]:
        """Get all activities for a lead"""
        activities = list(cls.collection.find({"lead_id": lead_id}).sort("activity_date", -1))
        return [LeadActivity(**activity) for activity in activities]
