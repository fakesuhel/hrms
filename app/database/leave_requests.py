from datetime import datetime, date, timedelta
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, validator
from bson import ObjectId
from app.database import db

# Get leave_requests collection
leave_requests_collection = db["leave_requests"]

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

class LeaveRequestCreate(BaseModel):
    user_id: str
    leave_type: str  # "vacation", "sick", "personal", "other"
    start_date: str  # Date in ISO format
    end_date: str    # Date in ISO format
    reason: str
    contact_info: Optional[str] = None
    
    @validator('end_date')
    def end_date_must_be_after_start_date(cls, v, values):
        if 'start_date' in values and v < values['start_date']:
            raise ValueError('End date must be after or equal to start date')
        return v

class LeaveRequestUpdate(BaseModel):
    leave_type: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    reason: Optional[str] = None
    contact_info: Optional[str] = None
    
    @validator('end_date')
    def end_date_must_be_after_start_date(cls, v, values):
        if v and 'start_date' in values and values['start_date'] and v < values['start_date']:
            raise ValueError('End date must be after or equal to start date')
        return v

class LeaveRequestApproval(BaseModel):
    status: str  # "approved", "rejected"
    approver_id: Optional[str] = None
    approver_comments: Optional[str] = None

class LeaveRequest(BaseModel):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    user_id: str
    leave_type: str
    start_date: str  # Date in ISO format
    end_date: str    # Date in ISO format
    reason: str
    contact_info: Optional[str] = None
    status: str = "pending"  # "pending", "approved", "rejected", "cancelled"
    approver_id: Optional[str] = None
    approver_comments: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        allow_population_by_field_name = True
        arbitrary_types_allowed = True
        json_encoders = {
            ObjectId: str,
            datetime: lambda v: v.isoformat()
        }

class LeaveRequestResponse(BaseModel):
    id: str = Field(alias="_id")
    user_id: str
    leave_type: str
    start_date: str
    end_date: str
    reason: str
    contact_info: Optional[str] = None
    status: str
    approver_id: Optional[str] = None
    approver_comments: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        allow_population_by_field_name = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

class DatabaseLeaveRequests:
    @staticmethod
    async def create_leave_request(leave_data: LeaveRequestCreate) -> LeaveRequest:
        # Ensure dates are string format
        if isinstance(leave_data.start_date, date):
            start_date = leave_data.start_date.isoformat()
        else:
            start_date = leave_data.start_date
            
        if isinstance(leave_data.end_date, date):
            end_date = leave_data.end_date.isoformat()
        else:
            end_date = leave_data.end_date
            
        # Validate dates
        if start_date > end_date:
            raise ValueError("End date must be after or equal to start date")
        
        # Check for overlapping leave requests
        overlapping = leave_requests_collection.find_one({
            "user_id": str(leave_data.user_id),
            "status": {"$in": ["pending", "approved"]},
            "$or": [
                {"start_date": {"$lte": end_date}, "end_date": {"$gte": start_date}},
                {"start_date": {"$gte": start_date, "$lte": end_date}},
                {"end_date": {"$gte": start_date, "$lte": end_date}}
            ]
        })
        
        if overlapping:
            raise ValueError("Overlapping leave request exists for this period")
        
        # Create leave request dict
        now = datetime.utcnow()
        leave_dict = leave_data.dict()
        leave_dict.update({
            "start_date": start_date,
            "end_date": end_date,
            "status": "pending",
            "created_at": now,
            "updated_at": now
        })
        
        # Insert leave request
        result = leave_requests_collection.insert_one(leave_dict)
        leave_dict["_id"] = result.inserted_id
        
        return LeaveRequest(**leave_dict)
    
    @staticmethod
    async def get_leave_request_by_id(leave_id: str) -> Optional[LeaveRequest]:
        # Ensure leave_id is properly converted
        if isinstance(leave_id, str) and ObjectId.is_valid(leave_id):
            id_obj = ObjectId(leave_id)
        else:
            id_obj = leave_id
        
        leave = leave_requests_collection.find_one({"_id": id_obj})
        if leave:
            return LeaveRequest(**leave)
        return None
    
    @staticmethod
    async def get_user_leave_requests(user_id: str, status: Optional[str] = None) -> List[LeaveRequest]:
        # Construct query
        query = {"user_id": str(user_id)}
        if status:
            query["status"] = status
        
        # Find leave requests
        cursor = leave_requests_collection.find(query).sort("created_at", -1)
        leave_requests = list(cursor)
        
        # Ensure _id is always a string for response
        for leave in leave_requests:
            if "_id" in leave and not isinstance(leave["_id"], str):
                leave["_id"] = str(leave["_id"])
        
        return [LeaveRequest(**leave) for leave in leave_requests]
    
    @staticmethod
    async def get_pending_approval_requests(manager_id: str) -> List[LeaveRequest]:
        # Get team members
        from app.database.users import DatabaseUsers
        team_members = await DatabaseUsers.get_team_members_by_manager(manager_id)
        
        if not team_members:
            return []
        
        team_ids = [str(member.id) for member in team_members]
        
        # Find pending leave requests for team
        cursor = leave_requests_collection.find({
            "user_id": {"$in": team_ids},
            "status": "pending"
        }).sort("created_at", -1)
        
        leave_requests = list(cursor)
        return [LeaveRequest(**leave) for leave in leave_requests]
    
    @staticmethod
    async def get_leave_balance(user_id: str) -> Dict[str, Any]:
        # Get current year
        current_year = datetime.now().year
        year_start = date(current_year, 1, 1).isoformat()
        year_end = date(current_year, 12, 31).isoformat()
        
        # Find approved leave requests for this year
        cursor = leave_requests_collection.find({
            "user_id": str(user_id),
            "status": "approved",
            "start_date": {"$gte": year_start},
            "end_date": {"$lte": year_end}
        })
        
        leave_requests = list(cursor)
        
        # Calculate used days by type
        vacation_used = 0
        sick_used = 0
        personal_used = 0
        other_used = 0
        
        for leave in leave_requests:
            start = datetime.fromisoformat(leave['start_date']).date()
            end = datetime.fromisoformat(leave['end_date']).date()
            days = (end - start).days + 1
            
            # Count only business days (excluding weekends)
            business_days = sum(1 for i in range(days) if (start + timedelta(days=i)).weekday() < 5)
            
            if leave['leave_type'] == "vacation":
                vacation_used += business_days
            elif leave['leave_type'] == "sick":
                sick_used += business_days
            elif leave['leave_type'] == "personal":
                personal_used += business_days
            else:
                other_used += business_days
        
        # Define annual allowance (can be customized based on your policy)
        vacation_allowance = 20
        sick_allowance = 10
        personal_allowance = 5
        
        # Calculate balance
        return {
            "user_id": user_id,
            "year": current_year,
            "vacation_total": vacation_allowance,
            "vacation_used": vacation_used,
            "vacation_remaining": max(0, vacation_allowance - vacation_used),
            "sick_total": sick_allowance,
            "sick_used": sick_used,
            "sick_remaining": max(0, sick_allowance - sick_used),
            "personal_total": personal_allowance,
            "personal_used": personal_used,
            "personal_remaining": max(0, personal_allowance - personal_used),
            "other_used": other_used,
            "total_available": max(0, vacation_allowance - vacation_used) + 
                              max(0, sick_allowance - sick_used) + 
                              max(0, personal_allowance - personal_used)
        }
    
    @staticmethod
    async def update_leave_request(leave_id: str, leave_data: LeaveRequestUpdate) -> Optional[LeaveRequest]:
        # Ensure leave_id is properly converted
        if isinstance(leave_id, str) and ObjectId.is_valid(leave_id):
            id_obj = ObjectId(leave_id)
        else:
            id_obj = leave_id
        
        # Get current leave request
        leave = leave_requests_collection.find_one({"_id": id_obj})
        if not leave:
            return None
        
        # Create update data
        update_data = {k: v for k, v in leave_data.dict(exclude_unset=True).items() if v is not None}
        
        # Convert dates if needed
        if 'start_date' in update_data and isinstance(update_data['start_date'], date):
            update_data['start_date'] = update_data['start_date'].isoformat()
            
        if 'end_date' in update_data and isinstance(update_data['end_date'], date):
            update_data['end_date'] = update_data['end_date'].isoformat()
        
        # If dates are updated, validate them
        if ('start_date' in update_data or 'end_date' in update_data):
            start_date = update_data.get('start_date', leave['start_date'])
            end_date = update_data.get('end_date', leave['end_date'])
            
            if start_date > end_date:
                raise ValueError("End date must be after or equal to start date")
            
            # Check for overlapping leave requests
            overlapping = leave_requests_collection.find_one({
                "_id": {"$ne": id_obj},
                "user_id": leave['user_id'],
                "status": {"$in": ["pending", "approved"]},
                "$or": [
                    {"start_date": {"$lte": end_date}, "end_date": {"$gte": start_date}},
                    {"start_date": {"$gte": start_date, "$lte": end_date}},
                    {"end_date": {"$gte": start_date, "$lte": end_date}}
                ]
            })
            
            if overlapping:
                raise ValueError("Overlapping leave request exists for this period")
        
        if update_data:
            update_data["updated_at"] = datetime.utcnow()
            
            # Update leave request
            leave_requests_collection.update_one(
                {"_id": id_obj},
                {"$set": update_data}
            )
        
        # Return updated leave request
        updated_leave = leave_requests_collection.find_one({"_id": id_obj})
        if updated_leave:
            return LeaveRequest(**updated_leave)
        return None
    
    @staticmethod
    async def process_leave_request(leave_id: str, approval_data: LeaveRequestApproval) -> Optional[LeaveRequest]:
        # Ensure leave_id is properly converted
        if isinstance(leave_id, str) and ObjectId.is_valid(leave_id):
            id_obj = ObjectId(leave_id)
        else:
            id_obj = leave_id
        
        # Get current leave request
        leave = leave_requests_collection.find_one({"_id": id_obj})
        if not leave:
            return None
        
        # Update leave request status
        update_data = {
            "status": approval_data.status,
            "approver_id": str(approval_data.approver_id),
            "approver_comments": approval_data.approver_comments,
            "updated_at": datetime.utcnow()
        }
        
        leave_requests_collection.update_one(
            {"_id": id_obj},
            {"$set": update_data}
        )
        
        # Return updated leave request
        updated_leave = leave_requests_collection.find_one({"_id": id_obj})
        if updated_leave:
            return LeaveRequest(**updated_leave)
        return None
    
    @staticmethod
    async def cancel_leave_request(leave_id: str) -> bool:
        # Ensure leave_id is properly converted
        if isinstance(leave_id, str) and ObjectId.is_valid(leave_id):
            id_obj = ObjectId(leave_id)
        else:
            id_obj = leave_id
        
        # Update leave request status
        result = leave_requests_collection.update_one(
            {"_id": id_obj},
            {
                "$set": {
                    "status": "cancelled",
                    "updated_at": datetime.utcnow()
                }
            }
        )
        
        return result.modified_count > 0