from datetime import datetime, date
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, validator
from bson import ObjectId
from pymongo.collection import Collection
from app.database import daily_reports_collection
from app.utils.helpers import PyObjectId
from zoneinfo import ZoneInfo

# Asia/Kolkata timezone
KOLKATA_TZ = ZoneInfo('Asia/Kolkata')

def get_kolkata_now():
    """Get current datetime in Asia/Kolkata timezone"""
    return datetime.now(KOLKATA_TZ)

class TaskItem(BaseModel):
    title: str
    status: str  # completed, in_progress, blocked, planned
    description: Optional[str] = None
    time_spent: Optional[float] = None  # Hours

class ReportBase(BaseModel):
    user_id: PyObjectId
    report_date: date
    summary: str
    tasks_completed: List[TaskItem] = []
    tasks_in_progress: List[TaskItem] = []
    blockers: Optional[str] = None
    plan_for_tomorrow: Optional[List[str]] = None
    
    class Config:
        arbitrary_types_allowed = True
        json_encoders = {
            ObjectId: str,
            date: lambda d: d.isoformat()
        }

class ReportCreate(ReportBase):
    project_id: Optional[PyObjectId] = None
    
    # Add validator to ensure report_date is parsed correctly from string
    @validator('report_date', pre=True)
    def parse_report_date(cls, v):
        if isinstance(v, str):
            try:
                # Parse ISO format string YYYY-MM-DD to date object
                return date.fromisoformat(v)
            except ValueError:
                raise ValueError('Invalid date format. Expected YYYY-MM-DD')
        return v

class ReportInDB(ReportBase):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    project_id: Optional[PyObjectId] = None
    created_at: datetime = Field(default_factory=get_kolkata_now)
    updated_at: datetime = Field(default_factory=get_kolkata_now)
    
    class Config:
        arbitrary_types_allowed = True
        json_encoders = {
            ObjectId: str,
            date: lambda d: d.isoformat()
        }
        json_schema_extra = {
            "example": {
                "_id": "60d21b4967d0d8820c43e555",
                "user_id": "60d21b4967d0d8820c43e124",
                "report_date": "2025-06-10",
                "project_id": "60d21b4967d0d8820c43e111",
                "summary": "Worked on UI component implementation for the mobile app.",
                "tasks_completed": [
                    {
                        "title": "Implement navigation drawer component",
                        "status": "completed",
                        "description": "Created reusable drawer component with animations",
                        "time_spent": 3.5
                    },
                    {
                        "title": "Fix login screen responsiveness issues",
                        "status": "completed",
                        "description": "Resolved UI issues on small screens",
                        "time_spent": 1.5
                    }
                ],
                "tasks_in_progress": [
                    {
                        "title": "Implement settings screen",
                        "status": "in_progress",
                        "description": "Working on user preferences section",
                        "time_spent": 2.0
                    }
                ],
                "blockers": "Waiting for API documentation for the settings endpoints",
                "plan_for_tomorrow": [
                    "Complete settings screen implementation",
                    "Start work on user profile screen",
                    "Review PRs from team members"
                ],
                "created_at": "2025-06-10T11:45:00",
                "updated_at": "2025-06-10T13:17:39"
            }
        }

class ReportUpdate(BaseModel):
    summary: Optional[str] = None
    tasks_completed: Optional[List[TaskItem]] = None
    tasks_in_progress: Optional[List[TaskItem]] = None
    blockers: Optional[str] = None
    plan_for_tomorrow: Optional[List[str]] = None
    project_id: Optional[PyObjectId] = None
    
    class Config:
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}

class ReportResponse(BaseModel):
    id: str = Field(alias="_id")
    user_id: str
    report_date: date
    project_id: Optional[str] = None
    summary: str
    tasks_completed: List[Dict[str, Any]] = []
    tasks_in_progress: List[Dict[str, Any]] = []
    blockers: Optional[str] = None
    plan_for_tomorrow: Optional[List[str]] = None
    created_at: datetime
    updated_at: datetime

class DatabaseDailyReports:
    collection: Collection = daily_reports_collection
    
    @classmethod
    async def create_report(cls, report_data: ReportCreate) -> ReportInDB:
        """Create a new daily report"""
        # Check if report for this date already exists
        # Make sure report_date is converted to string for the query
        report_date_str = report_data.report_date.isoformat() if hasattr(report_data.report_date, 'isoformat') else str(report_data.report_date)
        
        existing = cls.collection.find_one({
            "user_id": report_data.user_id,
            "report_date": report_date_str
        })
        
        if existing:
            raise ValueError(f"Report already exists for {report_data.report_date}")
        
        report_dict = report_data.dict()
        
        # Convert date to string before storing in MongoDB
        if isinstance(report_dict['report_date'], date):
            report_dict['report_date'] = report_dict['report_date'].isoformat()
            
        # Create the database model
        report_in_db = ReportInDB(
            **report_dict,
            created_at=get_kolkata_now(),
            updated_at=get_kolkata_now()
        )
        
        # Convert to dict for MongoDB and insert
        insert_dict = report_in_db.dict(by_alias=True)
        
        # Ensure we're storing date as string in MongoDB
        if isinstance(insert_dict['report_date'], date):
            insert_dict['report_date'] = insert_dict['report_date'].isoformat()
        
        result = cls.collection.insert_one(insert_dict)
        report_in_db.id = result.inserted_id
        return report_in_db

    @classmethod
    async def get_report_by_id(cls, report_id: str) -> Optional[ReportInDB]:
        """Get a report by ID"""
        report_data = cls.collection.find_one({"_id": ObjectId(report_id)})
        if report_data:
            return ReportInDB(**report_data)
        return None
    
    @classmethod
    async def get_report_by_date(cls, user_id: str, report_date: date) -> Optional[ReportInDB]:
        """Get a user's report by date"""
        report_data = cls.collection.find_one({
            "user_id": ObjectId(user_id),
            "report_date": report_date.isoformat()
        })
        
        if report_data:
            return ReportInDB(**report_data)
        return None
    
    @classmethod
    async def update_report(cls, report_id: str, report_data: ReportUpdate) -> Optional[ReportInDB]:
        """Update a report"""
        update_data = {k: v for k, v in report_data.dict().items() if v is not None}
        update_data["updated_at"] = get_kolkata_now()
        
        result = cls.collection.update_one(
            {"_id": ObjectId(report_id)},
            {"$set": update_data}
        )
        
        if result.modified_count:
            return await cls.get_report_by_id(report_id)
        return None
    
    @classmethod
    async def get_user_reports(cls, user_id: str, start_date: date, end_date: date) -> List[ReportInDB]:
        """Get a user's reports within a date range"""
        cursor = cls.collection.find({
            "user_id": ObjectId(user_id),
            "report_date": {
                "$gte": start_date.isoformat(),
                "$lte": end_date.isoformat()
            }
        }).sort("report_date", -1)
        
        return [ReportInDB(**report) for report in cursor]
    
    @classmethod
    async def get_team_reports(cls, team_members: List[str], for_date: date) -> List[ReportInDB]:
        """Get reports for a team on a specific date"""
        member_ids = [ObjectId(member_id) for member_id in team_members]
        
        cursor = cls.collection.find({
            "user_id": {"$in": member_ids},
            "report_date": for_date.isoformat()
        })
        
        return [ReportInDB(**report) for report in cursor]
    
    @classmethod
    async def get_project_reports(cls, project_id: str, start_date: date, end_date: date) -> List[ReportInDB]:
        """Get reports for a project within a date range"""
        cursor = cls.collection.find({
            "project_id": ObjectId(project_id),
            "report_date": {
                "$gte": start_date.isoformat(),
                "$lte": end_date.isoformat()
            }
        }).sort("report_date", -1)
        
        return [ReportInDB(**report) for report in cursor]
    
    @classmethod
    async def get_report_stats(cls, user_id: str, start_date: date, end_date: date) -> Dict[str, Any]:
        """Get report statistics for a user"""
        # Calculate number of days in the period
        delta = end_date - start_date
        total_days = delta.days + 1
        
        # Count reports in the period
        reports_count = cls.collection.count_documents({
            "user_id": ObjectId(user_id),
            "report_date": {
                "$gte": start_date.isoformat(),
                "$lte": end_date.isoformat()
            }
        })
        
        # Calculate task statistics
        pipeline = [
            {
                "$match": {
                    "user_id": ObjectId(user_id),
                    "report_date": {
                        "$gte": start_date.isoformat(),
                        "$lte": end_date.isoformat()
                    }
                }
            },
            {
                "$group": {
                    "_id": None,
                    "total_completed_tasks": {"$sum": {"$size": "$tasks_completed"}},
                    "total_in_progress_tasks": {"$sum": {"$size": "$tasks_in_progress"}}
                }
            }
        ]
        
        task_stats = list(cls.collection.aggregate(pipeline))
        
        if task_stats:
            total_completed = task_stats[0].get("total_completed_tasks", 0)
            total_in_progress = task_stats[0].get("total_in_progress_tasks", 0)
        else:
            total_completed = 0
            total_in_progress = 0
        
        return {
            "total_days": total_days,
            "reports_submitted": reports_count,
            "submission_rate": (reports_count / total_days) * 100 if total_days > 0 else 0,
            "total_completed_tasks": total_completed,
            "total_in_progress_tasks": total_in_progress,
            "avg_completed_tasks_per_report": total_completed / reports_count if reports_count > 0 else 0
        }