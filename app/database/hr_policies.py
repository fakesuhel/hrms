from datetime import datetime, date, timezone, timedelta
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from bson import ObjectId
from app.database import db
from pydantic_core import core_schema
from zoneinfo import ZoneInfo

# Get policies collection
hr_policies_collection = db["hr_policies"]
policy_acknowledgments_collection = db["policy_acknowledgments"]

# Asia/Kolkata timezone
KOLKATA_TZ = ZoneInfo('Asia/Kolkata')

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

# HR Policy Models
class HRPolicyBase(BaseModel):
    title: str
    category: str  # "attendance", "leave", "conduct", "security", "benefits", "performance", "general"
    description: str
    content: str  # Full policy content
    version: str = "1.0"
    effective_date: str  # ISO date string
    review_date: Optional[str] = None  # ISO date string
    tags: List[str] = []
    department_scope: List[str] = []  # Empty list means all departments
    
    model_config = {
        "populate_by_name": True,
        "arbitrary_types_allowed": True,
        "from_attributes": True
    }

class HRPolicyCreate(HRPolicyBase):
    created_by: str  # HR user ID

class HRPolicyUpdate(BaseModel):
    title: Optional[str] = None
    category: Optional[str] = None
    description: Optional[str] = None
    content: Optional[str] = None
    version: Optional[str] = None
    effective_date: Optional[str] = None
    review_date: Optional[str] = None
    tags: Optional[List[str]] = None
    department_scope: Optional[List[str]] = None
    status: Optional[str] = None

class HRPolicyInDB(HRPolicyBase):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    created_by: str
    status: str = "active"  # "draft", "active", "archived", "under_review"
    acknowledgment_required: bool = True
    total_acknowledgments: int = 0
    pending_acknowledgments: int = 0
    created_at: datetime = Field(default_factory=get_kolkata_now)
    updated_at: datetime = Field(default_factory=get_kolkata_now)
    
    model_config = {
        "populate_by_name": True,
        "arbitrary_types_allowed": True,
        "from_attributes": True
    }

class HRPolicyResponse(HRPolicyBase):
    id: str = Field(alias="_id")
    created_by: str
    status: str
    acknowledgment_required: bool
    total_acknowledgments: int
    pending_acknowledgments: int
    created_at: datetime
    updated_at: datetime
    
    model_config = {
        "populate_by_name": True,
        "from_attributes": True
    }

# Policy Acknowledgment Models
class PolicyAcknowledgmentBase(BaseModel):
    policy_id: str
    user_id: str
    acknowledged_version: str
    acknowledgment_date: datetime = Field(default_factory=get_kolkata_now)
    comments: Optional[str] = None
    
    model_config = {
        "populate_by_name": True,
        "arbitrary_types_allowed": True,
        "from_attributes": True
    }

class PolicyAcknowledgmentCreate(BaseModel):
    comments: Optional[str] = None

class PolicyAcknowledgmentInDB(PolicyAcknowledgmentBase):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    created_at: datetime = Field(default_factory=get_kolkata_now)
    
    model_config = {
        "populate_by_name": True,
        "arbitrary_types_allowed": True,
        "from_attributes": True
    }

# Database Classes
class DatabaseHRPolicies:
    collection = hr_policies_collection
    
    @classmethod
    async def create_policy(cls, policy_data: HRPolicyCreate) -> HRPolicyInDB:
        """Create a new HR policy"""
        policy_dict = policy_data.model_dump()
        policy_dict["created_at"] = get_kolkata_now()
        policy_dict["updated_at"] = get_kolkata_now()
        policy_dict["status"] = "active"
        policy_dict["acknowledgment_required"] = True
        policy_dict["total_acknowledgments"] = 0
        policy_dict["pending_acknowledgments"] = 0
        
        result = cls.collection.insert_one(policy_dict)
        policy_dict["_id"] = result.inserted_id
        
        return HRPolicyInDB(**policy_dict)
    
    @classmethod
    async def get_policy_by_id(cls, policy_id: str) -> Optional[HRPolicyInDB]:
        """Get a policy by ID"""
        try:
            policy = cls.collection.find_one({"_id": ObjectId(policy_id)})
            if policy:
                return HRPolicyInDB(**policy)
            return None
        except Exception as e:
            print(f"Error getting policy by ID: {e}")
            return None
    
    @classmethod
    async def get_policies_by_category(cls, category: str, status: Optional[str] = None) -> List[HRPolicyInDB]:
        """Get policies by category"""
        query = {"category": category}
        if status:
            query["status"] = status
        
        policies = list(cls.collection.find(query).sort("created_at", -1))
        return [HRPolicyInDB(**policy) for policy in policies]
    
    @classmethod
    async def get_all_policies(cls, status: Optional[str] = None, user_department: Optional[str] = None) -> List[HRPolicyInDB]:
        """Get all policies, optionally filtered by status and department scope"""
        query = {}
        if status:
            query["status"] = status
        
        # Filter by department scope if provided
        if user_department:
            query["$or"] = [
                {"department_scope": {"$size": 0}},  # Applies to all departments
                {"department_scope": user_department}  # Applies to specific department
            ]
        
        policies = list(cls.collection.find(query).sort("created_at", -1))
        return [HRPolicyInDB(**policy) for policy in policies]
    
    @classmethod
    async def update_policy(cls, policy_id: str, update_data: HRPolicyUpdate) -> Optional[HRPolicyInDB]:
        """Update a policy"""
        try:
            update_dict = {k: v for k, v in update_data.model_dump().items() if v is not None}
            update_dict["updated_at"] = get_kolkata_now()
            
            result = cls.collection.update_one(
                {"_id": ObjectId(policy_id)},
                {"$set": update_dict}
            )
            
            if result.modified_count > 0:
                updated_policy = cls.collection.find_one({"_id": ObjectId(policy_id)})
                return HRPolicyInDB(**updated_policy)
            return None
        except Exception as e:
            print(f"Error updating policy: {e}")
            return None
    
    @classmethod
    async def delete_policy(cls, policy_id: str) -> bool:
        """Delete a policy"""
        try:
            result = cls.collection.delete_one({"_id": ObjectId(policy_id)})
            return result.deleted_count > 0
        except Exception as e:
            print(f"Error deleting policy: {e}")
            return False
    
    @classmethod
    async def get_policy_stats(cls) -> Dict[str, Any]:
        """Get policy statistics"""
        pipeline = [
            {"$group": {
                "_id": "$category",
                "count": {"$sum": 1},
                "active": {"$sum": {"$cond": [{"$eq": ["$status", "active"]}, 1, 0]}},
                "draft": {"$sum": {"$cond": [{"$eq": ["$status", "draft"]}, 1, 0]}}
            }}
        ]
        
        results = list(cls.collection.aggregate(pipeline))
        
        stats = {
            "total_policies": 0,
            "active_policies": 0,
            "draft_policies": 0,
            "categories": {}
        }
        
        for result in results:
            category = result["_id"]
            count = result["count"]
            active = result["active"]
            draft = result["draft"]
            
            stats["total_policies"] += count
            stats["active_policies"] += active
            stats["draft_policies"] += draft
            stats["categories"][category] = {
                "total": count,
                "active": active,
                "draft": draft
            }
        
        return stats

class DatabasePolicyAcknowledgments:
    collection = policy_acknowledgments_collection
    
    @classmethod
    async def acknowledge_policy(cls, policy_id: str, user_id: str, 
                               acknowledgment_data: PolicyAcknowledgmentCreate,
                               policy_version: str) -> PolicyAcknowledgmentInDB:
        """Acknowledge a policy"""
        ack_dict = acknowledgment_data.model_dump()
        ack_dict.update({
            "policy_id": policy_id,
            "user_id": user_id,
            "acknowledged_version": policy_version,
            "acknowledgment_date": get_kolkata_now(),
            "created_at": get_kolkata_now()
        })
        
        # Check if user already acknowledged this policy version
        existing = cls.collection.find_one({
            "policy_id": policy_id,
            "user_id": user_id,
            "acknowledged_version": policy_version
        })
        
        if existing:
            # Update existing acknowledgment
            cls.collection.update_one(
                {"_id": existing["_id"]},
                {"$set": ack_dict}
            )
            ack_dict["_id"] = existing["_id"]
        else:
            # Create new acknowledgment
            result = cls.collection.insert_one(ack_dict)
            ack_dict["_id"] = result.inserted_id
            
            # Update policy acknowledgment count
            hr_policies_collection.update_one(
                {"_id": ObjectId(policy_id)},
                {"$inc": {"total_acknowledgments": 1}}
            )
        
        return PolicyAcknowledgmentInDB(**ack_dict)
    
    @classmethod
    async def get_user_acknowledgments(cls, user_id: str, policy_id: Optional[str] = None) -> List[PolicyAcknowledgmentInDB]:
        """Get user's policy acknowledgments"""
        query = {"user_id": user_id}
        if policy_id:
            query["policy_id"] = policy_id
        
        acknowledgments = list(cls.collection.find(query).sort("acknowledgment_date", -1))
        return [PolicyAcknowledgmentInDB(**ack) for ack in acknowledgments]
    
    @classmethod
    async def get_policy_acknowledgments(cls, policy_id: str) -> List[PolicyAcknowledgmentInDB]:
        """Get all acknowledgments for a policy"""
        acknowledgments = list(cls.collection.find({"policy_id": policy_id}).sort("acknowledgment_date", -1))
        return [PolicyAcknowledgmentInDB(**ack) for ack in acknowledgments]
    
    @classmethod
    async def check_user_policy_acknowledgment(cls, user_id: str, policy_id: str, policy_version: str) -> bool:
        """Check if user has acknowledged a specific policy version"""
        acknowledgment = cls.collection.find_one({
            "policy_id": policy_id,
            "user_id": user_id,
            "acknowledged_version": policy_version
        })
        return acknowledgment is not None
    
    @classmethod
    async def get_pending_acknowledgments_for_user(cls, user_id: str, user_department: str) -> List[HRPolicyInDB]:
        """Get policies that user hasn't acknowledged yet"""
        # Get all active policies applicable to user's department
        query = {
            "status": "active",
            "$or": [
                {"department_scope": {"$size": 0}},  # Applies to all departments
                {"department_scope": user_department}  # Applies to specific department
            ]
        }
        
        active_policies = list(hr_policies_collection.find(query))
        pending_policies = []
        
        for policy in active_policies:
            # Check if user has acknowledged this policy version
            acknowledged = await cls.check_user_policy_acknowledgment(
                user_id, str(policy["_id"]), policy["version"]
            )
            if not acknowledged:
                pending_policies.append(HRPolicyInDB(**policy))
        
        return pending_policies
