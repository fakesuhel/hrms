from datetime import datetime, date
from typing import List, Optional, Dict, Any, Union
from pydantic import BaseModel, Field
from bson import ObjectId
from pymongo.collection import Collection
from app.database import performance_reviews_collection
from app.utils.helpers import PyObjectId

class PerformanceRating(BaseModel):
    category: str  # technical_skills, communication, teamwork, leadership, etc.
    rating: float  # 1-5 scale
    comments: Optional[str] = None

class PerformanceReviewBase(BaseModel):
    user_id: PyObjectId
    reviewer_id: PyObjectId
    review_period: str  # e.g. "2025-H1", "2024-Q4", etc.
    review_type: str  # annual, mid-year, quarterly, etc.
    
    class Config:
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}

class PerformanceReviewCreate(PerformanceReviewBase):
    start_date: date
    end_date: date
    ratings: Optional[List[PerformanceRating]] = None
    strengths: Optional[List[str]] = None
    areas_for_improvement: Optional[List[str]] = None
    overall_comments: Optional[str] = None
    overall_rating: Optional[float] = None
    goals_for_next_period: Optional[List[str]] = None

class PerformanceReviewInDB(PerformanceReviewBase):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    start_date: date
    end_date: date
    ratings: List[PerformanceRating] = []
    strengths: List[str] = []
    areas_for_improvement: List[str] = []
    overall_comments: Optional[str] = None
    overall_rating: Optional[float] = None
    goals_for_next_period: List[str] = []
    status: str = "draft"  # draft, in_progress, completed, acknowledged
    created_at: datetime = Field(default_factory=lambda: datetime.now())
    updated_at: datetime = Field(default_factory=lambda: datetime.now())
    completed_at: Optional[datetime] = None
    acknowledged_by_user: bool = False
    acknowledged_at: Optional[datetime] = None
    user_comments: Optional[str] = None
    
    class Config:
        arbitrary_types_allowed = True
        json_encoders = {
            ObjectId: str,
            datetime: lambda v: v.isoformat(),
            date: lambda v: v.isoformat()
        }
        json_schema_extra = {
            "example": {
                "_id": "60d21b4967d0d8820c43e777",
                "user_id": "60d21b4967d0d8820c43e124",
                "reviewer_id": "60d21b4967d0d8820c43e123",
                "review_period": "2025-H1",
                "review_type": "mid-year",
                "start_date": "2025-01-01",
                "end_date": "2025-06-30",
                "ratings": [
                    {
                        "category": "technical_skills",
                        "rating": 4.5,
                        "comments": "Excellent technical skills, especially in React.js"
                    },
                    {
                        "category": "communication",
                        "rating": 3.5,
                        "comments": "Good communication but could improve documentation"
                    },
                    {
                        "category": "teamwork",
                        "rating": 4.0,
                        "comments": "Works well with team members, always helpful"
                    }
                ],
                "strengths": [
                    "Strong problem-solving skills",
                    "Great technical expertise in frontend development",
                    "Good at mentoring junior team members"
                ],
                "areas_for_improvement": [
                    "Could improve documentation",
                    "Should delegate more tasks"
                ],
                "overall_comments": "Overall a strong performer who contributes greatly to the team.",
                "overall_rating": 4.0,
                "goals_for_next_period": [
                    "Lead a major feature implementation",
                    "Improve documentation practices",
                    "Mentor at least one junior developer"
                ],
                "status": "completed",
                "created_at": "2025-05-15T10:00:00",
                "updated_at": "2025-06-10T13:17:39",
                "completed_at": "2025-06-01T15:30:00",
                "acknowledged_by_user": True,
                "acknowledged_at": "2025-06-02T09:15:00",
                "user_comments": "I agree with the assessment and will work on the areas for improvement."
            }
        }

class PerformanceReviewUpdate(BaseModel):
    ratings: Optional[List[PerformanceRating]] = None
    strengths: Optional[List[str]] = None
    areas_for_improvement: Optional[List[str]] = None
    overall_comments: Optional[str] = None
    overall_rating: Optional[float] = None
    goals_for_next_period: Optional[List[str]] = None
    status: Optional[str] = None
    
    class Config:
        arbitrary_types_allowed = True

class UserAcknowledgement(BaseModel):
    user_comments: Optional[str] = None

class PerformanceReviewResponse(BaseModel):
    id: str = Field(alias="_id")
    user_id: str
    reviewer_id: str
    review_period: str
    review_type: str
    start_date: date
    end_date: date
    ratings: List[Dict[str, Union[str, float, None]]] = []
    strengths: List[str] = []
    areas_for_improvement: List[str] = []
    overall_comments: Optional[str] = None
    overall_rating: Optional[float] = None
    goals_for_next_period: List[str] = []
    status: str
    created_at: datetime
    updated_at: datetime
    completed_at: Optional[datetime] = None
    acknowledged_by_user: bool
    acknowledged_at: Optional[datetime] = None
    user_comments: Optional[str] = None
    
    class Config:
        populate_by_name = True
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            date: lambda v: v.isoformat()
        }

class DatabasePerformanceReviews:
    collection: Collection = performance_reviews_collection
    
    @classmethod
    def _convert_dates_from_db(cls, review_data: dict) -> dict:
        """Convert string dates from MongoDB to date objects"""
        if isinstance(review_data.get('start_date'), str):
            try:
                review_data['start_date'] = datetime.fromisoformat(review_data['start_date']).date()
            except (ValueError, AttributeError):
                pass
        if isinstance(review_data.get('end_date'), str):
            try:
                review_data['end_date'] = datetime.fromisoformat(review_data['end_date']).date()
            except (ValueError, AttributeError):
                pass
        return review_data
    
    @classmethod
    async def get_latest_review(cls, user_id: str) -> Optional[PerformanceReviewInDB]:
        """Get the latest performance review for a user"""
        review_data = cls.collection.find_one(
            {"user_id": ObjectId(user_id)},
            sort=[("created_at", -1)]
        )
        if review_data:
            review_data = cls._convert_dates_from_db(review_data)
            return PerformanceReviewInDB(**review_data)
        return None
    
    @classmethod
    
    
    @classmethod
    async def create_review(cls, review_data: PerformanceReviewCreate) -> PerformanceReviewInDB:
        """Create a new performance review"""
        # Check if review for this period already exists
        existing = cls.collection.find_one({
            "user_id": review_data.user_id,
            "review_period": review_data.review_period
        })
        
        if existing:
            raise ValueError(f"Review already exists for period {review_data.review_period}")
        
        # Convert review_data to dict and handle date serialization
        review_dict = review_data.dict()
        
        # Convert date objects to strings for MongoDB storage
        if isinstance(review_dict.get('start_date'), date):
            review_dict['start_date'] = review_dict['start_date'].isoformat()
        if isinstance(review_dict.get('end_date'), date):
            review_dict['end_date'] = review_dict['end_date'].isoformat()
        
        review_in_db = PerformanceReviewInDB(
            **review_dict,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        # Convert to dict for MongoDB insertion, ensuring proper serialization
        insert_dict = review_in_db.dict(by_alias=True)
        
        # Ensure dates are strings
        if isinstance(insert_dict.get('start_date'), date):
            insert_dict['start_date'] = insert_dict['start_date'].isoformat()
        if isinstance(insert_dict.get('end_date'), date):
            insert_dict['end_date'] = insert_dict['end_date'].isoformat()
        
        result = cls.collection.insert_one(insert_dict)
        review_in_db.id = result.inserted_id
        return review_in_db
    
    @classmethod
    async def get_review_by_id(cls, review_id: str) -> Optional[PerformanceReviewInDB]:
        """Get a review by ID"""
        review_data = cls.collection.find_one({"_id": ObjectId(review_id)})
        if review_data:
            review_data = cls._convert_dates_from_db(review_data)
            return PerformanceReviewInDB(**review_data)
        return None
    
    @classmethod
    async def update_review(cls, review_id: str, review_data: PerformanceReviewUpdate) -> Optional[PerformanceReviewInDB]:
        """Update a review's information with upsert logic for missing fields"""
        # Create update operations
        update_data = {k: v for k, v in review_data.dict().items() if v is not None}
        update_data["updated_at"] = datetime.now()
        
        # If status is being updated to completed, add completed_at timestamp
        if update_data.get("status") == "completed":
            update_data["completed_at"] = datetime.now()
        
        # Use $set for existing fields and $setOnInsert for default values if document doesn't exist
        set_data = update_data.copy()
        set_on_insert = {
            "ratings": [],
            "strengths": [],
            "areas_for_improvement": [],
            "goals_for_next_period": [],
            "status": "draft",
            "acknowledged_by_user": False,
            "created_at": datetime.now()
        }
        
        result = cls.collection.update_one(
            {"_id": ObjectId(review_id)},
            {
                "$set": set_data,
                "$setOnInsert": set_on_insert
            },
            upsert=False  # Don't create new document, just update existing
        )
        
        if result.matched_count > 0:  # Check if document was found and potentially modified
            return await cls.get_review_by_id(review_id)
        return None
    
    @classmethod
    async def acknowledge_review(cls, review_id: str, acknowledgement: UserAcknowledgement) -> Optional[PerformanceReviewInDB]:
        """User acknowledges a review"""
        update_data = {
            "acknowledged_by_user": True,
            "acknowledged_at": datetime.now(),
            "user_comments": acknowledgement.user_comments,
            "updated_at": datetime.now()
        }
        
        result = cls.collection.update_one(
            {"_id": ObjectId(review_id), "status": "completed"},
            {"$set": update_data}
        )
        
        if result.modified_count:
            return await cls.get_review_by_id(review_id)
        return None
    
    @classmethod
    async def get_user_reviews(cls, user_id: str) -> List[PerformanceReviewInDB]:
        """Get all reviews for a user"""
        cursor = cls.collection.find({"user_id": ObjectId(user_id)}).sort("created_at", -1)
        reviews = []
        for review_data in cursor:
            review_data = cls._convert_dates_from_db(review_data)
            reviews.append(PerformanceReviewInDB(**review_data))
        return reviews

    @classmethod
    async def get_reviews_by_reviewer(cls, reviewer_id: str, status: Optional[str] = None) -> List[PerformanceReviewInDB]:
        """Get all reviews conducted by a reviewer"""
        query = {"reviewer_id": ObjectId(reviewer_id)}
        if status:
            query["status"] = status
        
        cursor = cls.collection.find(query).sort("created_at", -1)
        reviews = []
        for review_data in cursor:
            review_data = cls._convert_dates_from_db(review_data)
            reviews.append(PerformanceReviewInDB(**review_data))
        return reviews

    @classmethod
    async def get_team_reviews(cls, team_members: List[str], review_period: str) -> List[PerformanceReviewInDB]:
        """Get reviews for a team for a specific period"""
        member_ids = [ObjectId(member_id) for member_id in team_members]
        
        cursor = cls.collection.find({
            "user_id": {"$in": member_ids},
            "review_period": review_period
        })
        
        reviews = []
        for review_data in cursor:
            review_data = cls._convert_dates_from_db(review_data)
            reviews.append(PerformanceReviewInDB(**review_data))
        return reviews
    
    @classmethod
    async def get_performance_stats(cls, user_id: str, periods: int = 4) -> Dict[str, Any]:
        """Get performance stats for a user"""
        # Get the last N reviews
        cursor = cls.collection.find({
            "user_id": ObjectId(user_id),
            "status": "completed"
        }).sort("created_at", -1).limit(periods)
        
        reviews = []
        for review_data in cursor:
            review_data = cls._convert_dates_from_db(review_data)
            reviews.append(PerformanceReviewInDB(**review_data))
        
        # Calculate stats
        if not reviews:
            return {
                "average_rating": 0,
                "trend": "neutral",
                "review_count": 0,
                "last_review_date": None
            }
        
        # Calculate average rating
        ratings = [review.overall_rating for review in reviews if review.overall_rating is not None]
        avg_rating = sum(ratings) / len(ratings) if ratings else 0
        
        # Calculate trend
        trend = "neutral"
        if len(ratings) > 1:
            if ratings[0] > ratings[1]:
                trend = "improving"
            elif ratings[0] < ratings[1]:
                trend = "declining"
        
        return {
            "average_rating": avg_rating,
            "trend": trend,
            "review_count": len(reviews),
            "last_review_date": reviews[0].completed_at if reviews else None,
            "last_period": reviews[0].review_period if reviews else None
        }