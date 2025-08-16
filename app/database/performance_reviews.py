from datetime import datetime, date
from typing import List, Optional, Dict, Any, Union
from pydantic import BaseModel, Field
from bson import ObjectId
from pymongo.collection import Collection
from app.database import performance_reviews_collection
from app.utils.helpers import PyObjectId
from zoneinfo import ZoneInfo

# Asia/Kolkata timezone
KOLKATA_TZ = ZoneInfo('Asia/Kolkata')

def get_kolkata_now():
    """Get current datetime in Asia/Kolkata timezone"""
    return datetime.now(KOLKATA_TZ)

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
    created_at: datetime = Field(default_factory=get_kolkata_now)
    updated_at: datetime = Field(default_factory=get_kolkata_now)
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
    review_period: Optional[str] = None
    review_type: Optional[str] = None
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
            created_at=get_kolkata_now(),
            updated_at=get_kolkata_now()
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
        """Update a review's information"""
        try:
            # Convert ObjectId if review_id is invalid
            try:
                review_object_id = ObjectId(review_id)
            except Exception as e:
                print(f"Invalid ObjectId: {review_id}, error: {e}")
                return None
            
            # Create simple update data - only include fields that have values
            update_data = {}
            
            # Handle review_period and review_type first
            if review_data.review_period is not None:
                update_data["review_period"] = review_data.review_period
            
            if review_data.review_type is not None:
                update_data["review_type"] = review_data.review_type
            
            # Handle each field individually to avoid conflicts
            if review_data.ratings is not None:
                print(f"Processing ratings: {review_data.ratings}")
                try:
                    # Handle rating serialization more carefully
                    if isinstance(review_data.ratings, list):
                        processed_ratings = []
                        for rating in review_data.ratings:
                            if hasattr(rating, 'dict'):
                                processed_ratings.append(rating.dict())
                            elif hasattr(rating, 'model_dump'):
                                processed_ratings.append(rating.model_dump())
                            elif isinstance(rating, dict):
                                processed_ratings.append(rating)
                            else:
                                processed_ratings.append(rating)
                        update_data["ratings"] = processed_ratings
                    else:
                        update_data["ratings"] = review_data.ratings
                    print(f"Processed ratings: {update_data['ratings']}")
                except Exception as e:
                    print(f"Error processing ratings: {e}")
                    # Fall back to simple assignment
                    update_data["ratings"] = review_data.ratings
            
            if review_data.strengths is not None:
                update_data["strengths"] = review_data.strengths
            
            if review_data.areas_for_improvement is not None:
                update_data["areas_for_improvement"] = review_data.areas_for_improvement
            
            if review_data.overall_comments is not None:
                update_data["overall_comments"] = review_data.overall_comments
            
            if review_data.overall_rating is not None:
                update_data["overall_rating"] = review_data.overall_rating
            
            if review_data.goals_for_next_period is not None:
                update_data["goals_for_next_period"] = review_data.goals_for_next_period
            
            if review_data.status is not None:
                update_data["status"] = review_data.status
                # If status is being updated to completed, add completed_at timestamp
                if review_data.status == "completed":
                    update_data["completed_at"] = get_kolkata_now()
            
            # Always update the timestamp
            update_data["updated_at"] = get_kolkata_now()
            
            print(f"About to update review {review_id} with data: {update_data}")
            
            # Simple update operation with only $set
            result = cls.collection.update_one(
                {"_id": review_object_id},
                {"$set": update_data}
            )
            
            print(f"Update result - matched: {result.matched_count}, modified: {result.modified_count}")
            
            if result.matched_count > 0:  # Check if document was found and potentially modified
                updated_review = await cls.get_review_by_id(review_id)
                print(f"Retrieved updated review: {updated_review.id if updated_review else 'None'}")
                return updated_review
            else:
                print(f"No document matched for review_id: {review_id}")
            return None
            
        except Exception as e:
            print(f"Error in update_review: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    @classmethod
    async def acknowledge_review(cls, review_id: str, acknowledgement: UserAcknowledgement) -> Optional[PerformanceReviewInDB]:
        """User acknowledges a review"""
        update_data = {
            "acknowledged_by_user": True,
            "acknowledged_at": get_kolkata_now(),
            "user_comments": acknowledgement.user_comments,
            "updated_at": get_kolkata_now()
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
    
    @classmethod
    async def get_all_reviews_for_manager(cls, user_role: str, status: Optional[str] = None) -> List[PerformanceReviewInDB]:
        """Get all reviews that a manager can see based on their role"""
        from app.database.users import DatabaseUsers  # Import here to avoid circular imports
        
        # Build query
        query = {}
        
        # Add status filter if provided
        if status:
            query["status"] = status
        
        # For dev_manager, sales_manager, hr_manager - they can see all reviews in their department
        if user_role in ['dev_manager', 'sales_manager', 'hr_manager']:
            # Get users from their department
            department_map = {
                'dev_manager': 'development',
                'sales_manager': 'sales', 
                'hr_manager': 'hr'
            }
            department = department_map.get(user_role)
            
            if department:
                # Get users from the specific department
                users_in_dept = await DatabaseUsers.get_users_by_department(department)
                user_ids = [str(user.id) for user in users_in_dept]
                
                # Include reviews for users in their department
                query["$or"] = [
                    {"user_id": {"$in": user_ids}},  # Reviews for users in their department
                    {"reviewer_id": {"$in": user_ids}}  # Reviews conducted by users in their department
                ]
        
        # Admin and director can see all reviews
        elif user_role in ['admin', 'director']:
            # No additional filters for admin/director
            pass
        else:
            # Regular users only see their own reviews
            return []
        
        reviews = list(cls.collection.find(query).sort([("created_at", -1)]))
        
        result = []
        for review_data in reviews:
            if review_data:
                review_data = cls._convert_dates_from_db(review_data)
                result.append(PerformanceReviewInDB(**review_data))
        return result