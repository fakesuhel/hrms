from datetime import datetime, date
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, validator
from bson import ObjectId
from pymongo.collection import Collection
from app.database import leave_requests_collection
from app.utils.helpers import PyObjectId

class LeaveRequestBase(BaseModel):
    user_id: PyObjectId
    leave_type: str  # sick, vacation, personal, work_from_home, etc.
    start_date: date
    end_date: date
    reason: str
    contact_during_leave: Optional[str] = None
    
    @validator('end_date')
    def end_date_must_be_after_start_date(cls, v, values):
        if 'start_date' in values and v < values['start_date']:
            raise ValueError('end_date must be after start_date')
        return v
    
    class Config:
        arbitrary_types_allowed = True
        json_encoders = {
            ObjectId: str,
            date: lambda d: d.isoformat()
        }

class LeaveRequestCreate(LeaveRequestBase):
    pass

class LeaveRequestInDB(LeaveRequestBase):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    status: str = "pending"  # pending, approved, rejected, cancelled
    approver_id: Optional[PyObjectId] = None
    approver_comments: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now())
    updated_at: datetime = Field(default_factory=lambda: datetime.now())
    approved_at: Optional[datetime] = None
    duration_days: int = 1
    
    class Config:
        json_schema_extra = {
            "example": {
                "_id": "60d21b4967d0d8820c43e666",
                "user_id": "60d21b4967d0d8820c43e124",
                "leave_type": "personal",
                "start_date": "2025-06-19",
                "end_date": "2025-06-20",
                "reason": "Family function",
                "contact_during_leave": "+91 98765 43210",
                "status": "pending",
                "approver_id": None,
                "approver_comments": None,
                "created_at": "2025-06-05T14:30:00",
                "updated_at": "2025-06-10T13:17:39",
                "approved_at": None,
                "duration_days": 2
            }
        }

class LeaveRequestUpdate(BaseModel):
    leave_type: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    reason: Optional[str] = None
    contact_during_leave: Optional[str] = None
    
    class Config:
        arbitrary_types_allowed = True
        json_encoders = {
            date: lambda d: d.isoformat()
        }

class LeaveRequestApproval(BaseModel):
    status: str  # approved, rejected
    approver_id: PyObjectId
    approver_comments: Optional[str] = None
    
    class Config:
        arbitrary_types_allowed = True

class LeaveRequestResponse(BaseModel):
    id: str = Field(alias="_id")
    user_id: str
    leave_type: str
    start_date: date
    end_date: date
    reason: str
    contact_during_leave: Optional[str] = None
    status: str
    approver_id: Optional[str] = None
    approver_comments: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    approved_at: Optional[datetime] = None
    duration_days: int

class DatabaseLeaveRequests:
    collection: Collection = leave_requests_collection
    
    @classmethod
    async def create_leave_request(cls, leave_data: LeaveRequestCreate) -> LeaveRequestInDB:
        """Create a new leave request"""
        # Calculate duration in days
        duration = (leave_data.end_date - leave_data.start_date).days + 1
        
        leave_in_db = LeaveRequestInDB(
            **leave_data.dict(),
            duration_days=duration,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        result = cls.collection.insert_one(leave_in_db.dict(by_alias=True))
        leave_in_db.id = result.inserted_id
        return leave_in_db
    
    @classmethod
    async def get_leave_request_by_id(cls, leave_id: str) -> Optional[LeaveRequestInDB]:
        """Get a leave request by ID"""
        leave_data = cls.collection.find_one({"_id": ObjectId(leave_id)})
        if leave_data:
            return LeaveRequestInDB(**leave_data)
        return None
    
    @classmethod
    async def update_leave_request(cls, leave_id: str, leave_data: LeaveRequestUpdate) -> Optional[LeaveRequestInDB]:
        """Update a leave request"""
        update_data = {k: v for k, v in leave_data.dict().items() if v is not None}
        
        # If dates are being updated, recalculate duration
        if "start_date" in update_data or "end_date" in update_data:
            leave = await cls.get_leave_request_by_id(leave_id)
            if leave:
                start_date = update_data.get("start_date", leave.start_date)
                end_date = update_data.get("end_date", leave.end_date)
                update_data["duration_days"] = (end_date - start_date).days + 1
        
        update_data["updated_at"] = datetime.now()
        
        result = cls.collection.update_one(
            {"_id": ObjectId(leave_id)},
            {"$set": update_data}
        )
        
        if result.modified_count:
            return await cls.get_leave_request_by_id(leave_id)
        return None
    
    @classmethod
    async def process_leave_request(cls, leave_id: str, approval_data: LeaveRequestApproval) -> Optional[LeaveRequestInDB]:
        """Approve or reject a leave request"""
        update_data = {
            "status": approval_data.status,
            "approver_id": approval_data.approver_id,
            "approver_comments": approval_data.approver_comments,
            "updated_at": datetime.now()
        }
        
        if approval_data.status == "approved":
            update_data["approved_at"] = datetime.now()
        
        result = cls.collection.update_one(
            {"_id": ObjectId(leave_id)},
            {"$set": update_data}
        )
        
        if result.modified_count:
            return await cls.get_leave_request_by_id(leave_id)
        return None
    
    @classmethod
    async def cancel_leave_request(cls, leave_id: str) -> bool:
        """Cancel a leave request"""
        result = cls.collection.update_one(
            {"_id": ObjectId(leave_id), "status": "pending"},
            {"$set": {
                "status": "cancelled", 
                "updated_at": datetime.now()
            }}
        )
        return result.modified_count > 0
    
    @classmethod
    async def get_user_leave_requests(cls, user_id: str, status: Optional[str] = None) -> List[LeaveRequestInDB]:
        """Get a user's leave requests"""
        query = {"user_id": ObjectId(user_id)}
        if status:
            query["status"] = status
        
        cursor = cls.collection.find(query).sort("created_at", -1)
        return [LeaveRequestInDB(**leave) for leave in cursor]
    
    @classmethod
    async def get_pending_approval_requests(cls, approver_id: str) -> List[LeaveRequestInDB]:
        """Get leave requests pending approval for an approver"""
        # First get the team members under this approver
        from app.database.users import DatabaseUsers
        team_members = await DatabaseUsers.get_team_members_by_manager(approver_id)
        member_ids = [member.id for member in team_members]
        
        # Then get leave requests for these members
        cursor = cls.collection.find({
            "user_id": {"$in": member_ids},
            "status": "pending"
        }).sort("created_at", 1)
        
        return [LeaveRequestInDB(**leave) for leave in cursor]
    
    @classmethod
    async def get_leave_balance(cls, user_id: str) -> Dict[str, Any]:
        """Get leave balance for a user"""
        # This is a simplified version, in a real app we would have a separate leave balance collection
        # with policies, accruals, etc.
        
        # Get approved leaves this year
        start_of_year = date(date.today().year, 1, 1)
        today = date.today()
        
        pipeline = [
            {
                "$match": {
                    "user_id": ObjectId(user_id),
                    "status": "approved",
                    "start_date": {
                        "$gte": start_of_year.isoformat(),
                        "$lte": today.isoformat()
                    }
                }
            },
            {
                "$group": {
                    "_id": "$leave_type",
                    "days_used": {"$sum": "$duration_days"}
                }
            }
        ]
        
        result = list(cls.collection.aggregate(pipeline))
        
        # Assume default balances per leave type
        balances = {
            "sick": 12,
            "vacation": 15,
            "personal": 5,
            "work_from_home": 10
        }
        
        # Subtract used leaves
        for leave_type_usage in result:
            leave_type = leave_type_usage["_id"]
            if leave_type in balances:
                balances[leave_type] -= leave_type_usage["days_used"]
        
        return {
            "balances": balances,
            "total_available": sum(balances.values()),
            "last_updated": datetime.now()
        }