from datetime import datetime, date, timedelta
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from bson import ObjectId
from app.database import db

# Get attendance collection
attendance_collection = db["attendance"]

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

class AttendanceCheckIn(BaseModel):
    # Make user_id optional to fix the validation error
    user_id: Optional[str] = None
    date: Optional[str] = None  # Also make date optional, we'll default to today
    check_in_location: str
    check_in_note: Optional[str] = None

class AttendanceCheckOut(BaseModel):
    check_out_location: str
    check_out_note: Optional[str] = None
    work_summary: Optional[str] = None

class Attendance(BaseModel):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    user_id: str
    date: str  # Store as string in ISO format
    check_in: Optional[datetime] = None
    check_out: Optional[datetime] = None
    check_in_location: Optional[str] = None
    check_out_location: Optional[str] = None
    check_in_note: Optional[str] = None
    check_out_note: Optional[str] = None
    work_summary: Optional[str] = None
    is_late: bool = False
    is_complete: bool = False
    work_hours: Optional[float] = None
    status: str = "present"  # "present", "absent", "leave"
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        allow_population_by_field_name = True
        arbitrary_types_allowed = True
        json_encoders = {
            ObjectId: str,
            datetime: lambda v: v.isoformat(),
            date: lambda v: v.isoformat()
        }

class AttendanceResponse(BaseModel):
    id: str = Field(alias="_id")
    user_id: str
    date: str  # Store as string in ISO format
    check_in: Optional[datetime] = None
    check_out: Optional[datetime] = None
    check_in_location: Optional[str] = None
    check_out_location: Optional[str] = None
    check_in_note: Optional[str] = None
    check_out_note: Optional[str] = None
    work_summary: Optional[str] = None
    is_late: bool = False
    is_complete: bool = False
    work_hours: Optional[float] = None
    status: str = "present"
    created_at: datetime
    updated_at: datetime
    
    class Config:
        allow_population_by_field_name = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

class DatabaseAttendance:
    @staticmethod
    async def get_attendance_by_date_range(
        user_id: str, start_date: date, end_date: date
    ) -> List[Attendance]:
        # Ensure user_id is string
        user_id = str(user_id)
        
        # Convert dates to strings for MongoDB query
        start_date_str = start_date.isoformat() if isinstance(start_date, date) else start_date
        end_date_str = end_date.isoformat() if isinstance(end_date, date) else end_date
        
        print(f"Getting attendance for user {user_id} from {start_date_str} to {end_date_str}")
        
        # Find attendance records in date range
        cursor = attendance_collection.find({
            "user_id": user_id,
            "date": {"$gte": start_date_str, "$lte": end_date_str}
        }).sort("date", -1)
        
        # Use list() instead of to_list() for synchronous PyMongo
        attendance_records = list(cursor)
        return [Attendance(**record) for record in attendance_records]
    
    
    @staticmethod
    async def check_in(check_in_data: AttendanceCheckIn) -> Attendance:
        # Use the user_id from check_in_data if provided, otherwise use None
        user_id = str(check_in_data.user_id) if check_in_data.user_id else None
        
        if not user_id:
            raise ValueError("User ID is required for check-in")
        
        # Ensure date is properly formatted string
        attendance_date = check_in_data.date
        if not attendance_date:
            attendance_date = datetime.utcnow().date().isoformat()
        
        # Check if already checked in
        existing_attendance = attendance_collection.find_one({
            "user_id": user_id,
            "date": attendance_date
        })
        
        if existing_attendance:
            if existing_attendance.get("check_in"):
                raise ValueError("Already checked in for today")
            
            # Update existing record
            now = datetime.utcnow()
            update_data = {
                "check_in": now,
                "check_in_location": check_in_data.check_in_location,
                "check_in_note": check_in_data.check_in_note,
                "updated_at": now
            }
            
            # Check if late (after 10 AM)
            if now.hour > 10 or (now.hour == 10 and now.minute > 0):
                update_data["is_late"] = True
            
            attendance_collection.update_one(
                {"_id": existing_attendance["_id"]},
                {"$set": update_data}
            )
            
            updated_attendance = attendance_collection.find_one({"_id": existing_attendance["_id"]})
            return Attendance(**updated_attendance)
        
        # Create new attendance record
        now = datetime.utcnow()
        new_attendance = {
            "user_id": user_id,
            "date": attendance_date,
            "check_in": now,
            "check_in_location": check_in_data.check_in_location,
            "check_in_note": check_in_data.check_in_note,
            "is_late": now.hour > 10 or (now.hour == 10 and now.minute > 0),
            "is_complete": False,
            "status": "present",
            "created_at": now,
            "updated_at": now
        }
        
        result = attendance_collection.insert_one(new_attendance)
        new_attendance["_id"] = result.inserted_id
        
        return Attendance(**new_attendance)
    
    @staticmethod
    async def check_out(user_id: str, checkout_data: AttendanceCheckOut) -> Optional[Attendance]:
        # Ensure user_id is string
        user_id = str(user_id)
        
        # Get today's date in ISO format
        today = datetime.utcnow().date().isoformat()
        
        # Find attendance record for today
        attendance = attendance_collection.find_one({
            "user_id": user_id,
            "date": today
        })
        
        if not attendance:
            return None
        
        if not attendance.get("check_in"):
            raise ValueError("Cannot check out without checking in first")
        
        if attendance.get("check_out"):
            raise ValueError("Already checked out for today")
        
        # Calculate work hours
        now = datetime.utcnow()
        check_in_time = attendance["check_in"]
        work_hours = (now - check_in_time).total_seconds() / 3600
        work_hours = round(work_hours, 2)
        
        # Update attendance record
        update_data = {
            "check_out": now,
            "check_out_location": checkout_data.check_out_location,
            "check_out_note": checkout_data.check_out_note,
            "work_summary": checkout_data.work_summary,
            "is_complete": True,
            "work_hours": work_hours,
            "updated_at": now
        }
        
        attendance_collection.update_one(
            {"_id": attendance["_id"]},
            {"$set": update_data}
        )
        
        updated_attendance = attendance_collection.find_one({"_id": attendance["_id"]})
        return Attendance(**updated_attendance)
    
    @staticmethod
    async def get_user_attendance(user_id: str, start_date: date, end_date: date) -> List[Attendance]:
        # Ensure user_id is string
        user_id = str(user_id)
        
        # Convert dates to strings for MongoDB query
        start_date_str = start_date.isoformat() if isinstance(start_date, date) else start_date
        end_date_str = end_date.isoformat() if isinstance(end_date, date) else end_date
        
        print(f"Getting attendance for user {user_id} from {start_date_str} to {end_date_str}")
        
        # Find attendance records in date range
        cursor = attendance_collection.find({
            "user_id": user_id,
            "date": {"$gte": start_date_str, "$lte": end_date_str}
        }).sort("date", -1)
        
        # Use list() instead of to_list() for synchronous PyMongo
        attendance_records = list(cursor)
        return [Attendance(**record) for record in attendance_records]
    
    @staticmethod
    async def get_team_attendance(team_ids: List[str], for_date: date) -> List[Attendance]:
        # Convert date to string
        date_str = for_date.isoformat() if hasattr(for_date, 'isoformat') else for_date
        
        # Ensure all IDs are strings
        team_ids = [str(id) for id in team_ids]
        
        print(f"Getting team attendance for team_ids: {team_ids}, date: {date_str}")
        
        # Find attendance records for team
        cursor = attendance_collection.find({
            "user_id": {"$in": team_ids},
            "date": date_str
        })
        
        # Use list() instead of to_list() for synchronous PyMongo
        attendance_records = list(cursor)
        
        # Create attendance entries for missing team members
        existing_user_ids = [record["user_id"] for record in attendance_records]
        missing_user_ids = [id for id in team_ids if id not in existing_user_ids]
        
        now = datetime.utcnow()
        for user_id in missing_user_ids:
            absent_record = {
                "_id": ObjectId(),
                "user_id": user_id,
                "date": date_str,
                "status": "absent",
                "is_complete": False,
                "created_at": now,
                "updated_at": now
            }
            attendance_records.append(absent_record)
        
        return [Attendance(**record) for record in attendance_records]
    
    @staticmethod
    async def get_attendance_stats(user_id: str, start_date: date, end_date: date) -> Dict[str, Any]:
        # Ensure user_id is string
        user_id = str(user_id)
        
        # Get user attendance records
        attendance_records = await DatabaseAttendance.get_user_attendance(user_id, start_date, end_date)
        
        # Calculate stats
        total_days = (end_date - start_date).days + 1
        working_days = sum(1 for d in range((end_date - start_date).days + 1) 
                         if (start_date + timedelta(days=d)).weekday() < 5)  # Exclude weekends
        
        present_days = len([r for r in attendance_records if r.status == "present"])
        late_days = len([r for r in attendance_records if r.is_late])
        leave_days = len([r for r in attendance_records if r.status == "leave"])
        absent_days = working_days - present_days - leave_days
        
        # Calculate attendance rate (excluding leaves)
        attendance_rate = (present_days / (working_days - leave_days)) * 100 if (working_days - leave_days) > 0 else 100
        
        # Calculate average work hours
        work_hours = [r.work_hours for r in attendance_records if r.work_hours is not None]
        avg_work_hours = sum(work_hours) / len(work_hours) if work_hours else 0
        
        # Current date and user
        current_date = "2025-06-12 06:56:11"
        current_user = "soherunot"
        
        return {
            "user_id": user_id,
            "start_date": start_date.isoformat() if isinstance(start_date, date) else start_date,
            "end_date": end_date.isoformat() if isinstance(end_date, date) else end_date,
            "total_days": total_days,
            "working_days": working_days,
            "present_days": present_days,
            "late_days": late_days,
            "leave_days": leave_days,
            "absent_days": absent_days,
            "attendance_rate": round(attendance_rate, 2),
            "avg_work_hours": round(avg_work_hours, 2),
            "current_time": current_date,
            "current_user": current_user
        }