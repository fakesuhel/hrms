from datetime import datetime, date, timezone, timedelta
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from bson import ObjectId
from app.database import db
from pydantic_core import core_schema

# Get job_postings collection
job_postings_collection = db["job_postings"]
applications_collection = db["job_applications"]
interviews_collection = db["interviews"]


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

# Job Posting Models
class JobPostingBase(BaseModel):
    title: str
    department: str
    position_type: str  # "full_time", "part_time", "contract", "internship"
    experience_level: str  # "entry", "mid", "senior", "lead", "manager"
    location: str
    salary_range: Optional[str] = None
    description: str
    requirements: List[str] = []
    responsibilities: List[str] = []
    benefits: List[str] = []
    skills_required: List[str] = []
    
    model_config = {
        "populate_by_name": True,
        "arbitrary_types_allowed": True,
        "from_attributes": True
    }

class JobPostingCreate(JobPostingBase):
    posted_by: str  # HR user ID

class JobPostingUpdate(BaseModel):
    title: Optional[str] = None
    department: Optional[str] = None
    position_type: Optional[str] = None
    experience_level: Optional[str] = None
    location: Optional[str] = None
    salary_range: Optional[str] = None
    description: Optional[str] = None
    requirements: Optional[List[str]] = None
    responsibilities: Optional[List[str]] = None
    benefits: Optional[List[str]] = None
    skills_required: Optional[List[str]] = None
    status: Optional[str] = None

class JobPostingInDB(JobPostingBase):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    posted_by: str
    status: str = "active"  # "active", "paused", "closed", "draft"
    applications_count: int = 0
    views_count: int = 0
    posted_date: datetime = Field(default_factory=get_ist_now)
    closing_date: Optional[str] = None  # ISO date string
    created_at: datetime = Field(default_factory=get_ist_now)
    updated_at: datetime = Field(default_factory=get_ist_now)
    
    model_config = {
        "populate_by_name": True,
        "arbitrary_types_allowed": True,
        "from_attributes": True
    }

# Job Application Models
class JobApplicationBase(BaseModel):
    job_posting_id: str
    applicant_name: str
    applicant_email: str
    applicant_phone: str
    resume_filename: Optional[str] = None
    cover_letter: Optional[str] = None
    experience_years: Optional[int] = None
    current_location: Optional[str] = None
    expected_salary: Optional[str] = None
    notice_period: Optional[str] = None
    
    model_config = {
        "populate_by_name": True,
        "arbitrary_types_allowed": True,
        "from_attributes": True
    }

class JobApplicationCreate(JobApplicationBase):
    pass

class JobApplicationUpdate(BaseModel):
    status: Optional[str] = None
    reviewer_notes: Optional[str] = None
    rating: Optional[int] = None  # 1-5 rating

class JobApplicationInDB(JobApplicationBase):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    status: str = "submitted"  # "submitted", "reviewing", "shortlisted", "interview", "selected", "rejected"
    reviewer_id: Optional[str] = None
    reviewer_notes: Optional[str] = None
    rating: Optional[int] = None
    applied_date: datetime = Field(default_factory=get_ist_now)
    reviewed_date: Optional[datetime] = None
    created_at: datetime = Field(default_factory=get_ist_now)
    updated_at: datetime = Field(default_factory=get_ist_now)
    
    model_config = {
        "populate_by_name": True,
        "arbitrary_types_allowed": True,
        "from_attributes": True
    }

# Interview Models
class InterviewBase(BaseModel):
    application_id: str
    interview_type: str  # "phone", "video", "in_person", "technical", "hr", "final"
    scheduled_date: str  # ISO datetime string
    duration_minutes: int = 60
    interviewer_id: str
    interview_link: Optional[str] = None  # For video interviews
    location: Optional[str] = None  # For in-person interviews
    agenda: Optional[str] = None
    
    model_config = {
        "populate_by_name": True,
        "arbitrary_types_allowed": True,
        "from_attributes": True
    }

class InterviewCreate(InterviewBase):
    pass

class InterviewUpdate(BaseModel):
    scheduled_date: Optional[str] = None
    duration_minutes: Optional[int] = None
    interviewer_id: Optional[str] = None
    interview_link: Optional[str] = None
    location: Optional[str] = None
    agenda: Optional[str] = None
    status: Optional[str] = None
    feedback: Optional[str] = None
    rating: Optional[int] = None

class InterviewInDB(InterviewBase):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    status: str = "scheduled"  # "scheduled", "completed", "cancelled", "rescheduled"
    feedback: Optional[str] = None
    rating: Optional[int] = None  # 1-5 rating
    attended: bool = False
    created_at: datetime = Field(default_factory=get_ist_now)
    updated_at: datetime = Field(default_factory=get_ist_now)
    
    model_config = {
        "populate_by_name": True,
        "arbitrary_types_allowed": True,
        "from_attributes": True
    }

# Database Classes
class DatabaseJobPostings:
    collection = job_postings_collection
    
    @classmethod
    async def create_job_posting(cls, job_data: JobPostingCreate) -> JobPostingInDB:
        """Create a new job posting"""
        job_dict = job_data.model_dump()
        job_dict["created_at"] = get_ist_now()
        job_dict["updated_at"] = get_ist_now()
        job_dict["status"] = "active"
        job_dict["applications_count"] = 0
        job_dict["views_count"] = 0
        job_dict["posted_date"] = get_ist_now()
        
        result = cls.collection.insert_one(job_dict)
        job_dict["_id"] = result.inserted_id
        
        return JobPostingInDB(**job_dict)
    
    @classmethod
    async def get_job_posting_by_id(cls, job_id: str) -> Optional[JobPostingInDB]:
        """Get a job posting by ID"""
        try:
            job = cls.collection.find_one({"_id": ObjectId(job_id)})
            if job:
                return JobPostingInDB(**job)
            return None
        except Exception as e:
            print(f"Error getting job posting by ID: {e}")
            return None
    
    @classmethod
    async def get_all_job_postings(cls, status: Optional[str] = None) -> List[JobPostingInDB]:
        """Get all job postings"""
        query = {}
        if status:
            query["status"] = status
        
        jobs = list(cls.collection.find(query).sort("created_at", -1))
        return [JobPostingInDB(**job) for job in jobs]
    
    @classmethod
    async def update_job_posting(cls, job_id: str, update_data: JobPostingUpdate) -> Optional[JobPostingInDB]:
        """Update a job posting"""
        try:
            update_dict = {k: v for k, v in update_data.model_dump().items() if v is not None}
            update_dict["updated_at"] = get_ist_now()
            
            result = cls.collection.update_one(
                {"_id": ObjectId(job_id)},
                {"$set": update_dict}
            )
            
            if result.modified_count > 0:
                updated_job = cls.collection.find_one({"_id": ObjectId(job_id)})
                return JobPostingInDB(**updated_job)
            return None
        except Exception as e:
            print(f"Error updating job posting: {e}")
            return None
    
    @classmethod
    async def delete_job_posting(cls, job_id: str) -> bool:
        """Delete a job posting"""
        try:
            result = cls.collection.delete_one({"_id": ObjectId(job_id)})
            return result.deleted_count > 0
        except Exception as e:
            print(f"Error deleting job posting: {e}")
            return False

class DatabaseJobApplications:
    collection = applications_collection
    
    @classmethod
    async def create_application(cls, application_data: JobApplicationCreate) -> JobApplicationInDB:
        """Create a new job application"""
        app_dict = application_data.model_dump()
        app_dict["created_at"] = get_ist_now()
        app_dict["updated_at"] = get_ist_now()
        app_dict["status"] = "submitted"
        app_dict["applied_date"] = get_ist_now()
        
        result = cls.collection.insert_one(app_dict)
        app_dict["_id"] = result.inserted_id
        
        # Update job posting applications count
        job_postings_collection.update_one(
            {"_id": ObjectId(application_data.job_posting_id)},
            {"$inc": {"applications_count": 1}}
        )
        
        return JobApplicationInDB(**app_dict)
    
    @classmethod
    async def get_applications_by_job(cls, job_posting_id: str) -> List[JobApplicationInDB]:
        """Get all applications for a job posting"""
        applications = list(cls.collection.find({"job_posting_id": job_posting_id}).sort("applied_date", -1))
        return [JobApplicationInDB(**app) for app in applications]
    
    @classmethod
    async def get_application_by_id(cls, application_id: str) -> Optional[JobApplicationInDB]:
        """Get an application by ID"""
        try:
            application = cls.collection.find_one({"_id": ObjectId(application_id)})
            if application:
                return JobApplicationInDB(**application)
            return None
        except Exception as e:
            print(f"Error getting application by ID: {e}")
            return None
    
    @classmethod
    async def update_application(cls, application_id: str, update_data: JobApplicationUpdate) -> Optional[JobApplicationInDB]:
        """Update a job application"""
        try:
            update_dict = {k: v for k, v in update_data.model_dump().items() if v is not None}
            update_dict["updated_at"] = get_ist_now()
            
            if update_data.status:
                update_dict["reviewed_date"] = get_ist_now()
            
            result = cls.collection.update_one(
                {"_id": ObjectId(application_id)},
                {"$set": update_dict}
            )
            
            if result.modified_count > 0:
                updated_app = cls.collection.find_one({"_id": ObjectId(application_id)})
                return JobApplicationInDB(**updated_app)
            return None
        except Exception as e:
            print(f"Error updating application: {e}")
            return None

class DatabaseInterviews:
    collection = interviews_collection
    
    @classmethod
    async def schedule_interview(cls, interview_data: InterviewCreate) -> InterviewInDB:
        """Schedule a new interview"""
        interview_dict = interview_data.model_dump()
        interview_dict["created_at"] = get_ist_now()
        interview_dict["updated_at"] = get_ist_now()
        interview_dict["status"] = "scheduled"
        interview_dict["attended"] = False
        
        result = cls.collection.insert_one(interview_dict)
        interview_dict["_id"] = result.inserted_id
        
        return InterviewInDB(**interview_dict)
    
    @classmethod
    async def get_interviews_by_application(cls, application_id: str) -> List[InterviewInDB]:
        """Get all interviews for an application"""
        interviews = list(cls.collection.find({"application_id": application_id}).sort("scheduled_date", 1))
        return [InterviewInDB(**interview) for interview in interviews]
    
    @classmethod
    async def get_interview_by_id(cls, interview_id: str) -> Optional[InterviewInDB]:
        """Get an interview by ID"""
        try:
            interview = cls.collection.find_one({"_id": ObjectId(interview_id)})
            if interview:
                return InterviewInDB(**interview)
            return None
        except Exception as e:
            print(f"Error getting interview by ID: {e}")
            return None
    
    @classmethod
    async def update_interview(cls, interview_id: str, update_data: InterviewUpdate) -> Optional[InterviewInDB]:
        """Update an interview"""
        try:
            update_dict = {k: v for k, v in update_data.model_dump().items() if v is not None}
            update_dict["updated_at"] = get_ist_now()
            
            result = cls.collection.update_one(
                {"_id": ObjectId(interview_id)},
                {"$set": update_dict}
            )
            
            if result.modified_count > 0:
                updated_interview = cls.collection.find_one({"_id": ObjectId(interview_id)})
                return InterviewInDB(**updated_interview)
            return None
        except Exception as e:
            print(f"Error updating interview: {e}")
            return None
    
    @classmethod
    async def get_upcoming_interviews(cls, interviewer_id: Optional[str] = None) -> List[InterviewInDB]:
        """Get upcoming interviews"""
        query = {"status": "scheduled"}
        if interviewer_id:
            query["interviewer_id"] = interviewer_id
        
        interviews = list(cls.collection.find(query).sort("scheduled_date", 1))
        return [InterviewInDB(**interview) for interview in interviews]
