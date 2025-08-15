from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from bson import ObjectId
from pymongo.collection import Collection
from app.database import teams_collection
from app.utils.helpers import PyObjectId
from zoneinfo import ZoneInfo

# Asia/Kolkata timezone
KOLKATA_TZ = ZoneInfo('Asia/Kolkata')

def get_kolkata_now():
    """Get current datetime in Asia/Kolkata timezone"""
    return datetime.now(KOLKATA_TZ)

class TeamMember(BaseModel):
    user_id: PyObjectId
    role: str  # team_lead, developer, designer, etc.
    joined_at: datetime = Field(default_factory=get_kolkata_now)
    
    class Config:
        arbitrary_types_allowed = True
        json_encoders = {
            ObjectId: str,
            datetime: lambda dt: dt.isoformat()
        }

class TeamBase(BaseModel):
    name: str
    description: str
    department: str
    
    class Config:
        arbitrary_types_allowed = True
        json_encoders = {
            ObjectId: str,
            datetime: lambda dt: dt.isoformat()
        }

class TeamCreate(TeamBase):
    lead_id: PyObjectId
    members: Optional[List[TeamMember]] = []

class TeamInDB(TeamBase):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    lead_id: PyObjectId
    members: List[TeamMember] = []
    created_at: datetime = Field(default_factory=get_kolkata_now)
    updated_at: datetime = Field(default_factory=get_kolkata_now)
    
    class Config:
        arbitrary_types_allowed = True
        json_encoders = {
            ObjectId: str,
            datetime: lambda dt: dt.isoformat()
        }
        json_schema_extra = {
            "example": {
                "_id": "60d21b4967d0d8820c43e789",
                "name": "Frontend Team",
                "description": "Team responsible for frontend development",
                "department": "Development",
                "lead_id": "60d21b4967d0d8820c43e123",
                "members": [
                    {
                        "user_id": "60d21b4967d0d8820c43e123",
                        "role": "team_lead",
                        "joined_at": "2025-01-01T00:00:00"
                    },
                    {
                        "user_id": "60d21b4967d0d8820c43e124",
                        "role": "developer",
                        "joined_at": "2025-01-15T00:00:00"
                    },
                    {
                        "user_id": "60d21b4967d0d8820c43e125",
                        "role": "developer",
                        "joined_at": "2025-02-01T00:00:00"
                    }
                ],
                "created_at": "2025-01-01T00:00:00",
                "updated_at": "2025-06-10T13:17:39"
            }
        }

class TeamUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    department: Optional[str] = None
    lead_id: Optional[PyObjectId] = None
    
    class Config:
        arbitrary_types_allowed = True
        json_encoders = {
            ObjectId: str,
            datetime: lambda dt: dt.isoformat()
        }

class TeamResponse(TeamBase):
    id: str = Field(alias="_id")
    lead_id: str
    members: List[Dict[str, Any]] = []
    created_at: datetime
    updated_at: datetime
    
    class Config:
        # Add this to ensure proper handling of datetime objects in response
        json_encoders = {
            datetime: lambda dt: dt.isoformat()
        }

class DatabaseTeams:
    collection: Collection = teams_collection
    
    @classmethod
    async def create_team(cls, team_data: TeamCreate) -> TeamInDB:
        """Create a new team"""
        team_in_db = TeamInDB(
            **team_data.dict(),
            created_at=get_kolkata_now(),
            updated_at=get_kolkata_now()
        )
        
        result = cls.collection.insert_one(team_in_db.dict(by_alias=True))
        team_in_db.id = result.inserted_id
        return team_in_db
    
    @classmethod
    async def get_team_by_id(cls, team_id: str) -> Optional[TeamInDB]:
        """Get a team by ID"""
        team_data = cls.collection.find_one({"_id": ObjectId(team_id)})
        if team_data:
            return TeamInDB(**team_data)
        return None
    
    @classmethod
    async def get_team_by_lead(cls, lead_id: str) -> Optional[TeamInDB]:
        """Get a team by lead ID"""
        team_data = cls.collection.find_one({"lead_id": ObjectId(lead_id)})
        if team_data:
            return TeamInDB(**team_data)
        return None
    
    @classmethod
    async def update_team(cls, team_id: str, team_data: TeamUpdate) -> Optional[TeamInDB]:
        """Update a team's information"""
        update_data = {k: v for k, v in team_data.dict().items() if v is not None}
        update_data["updated_at"] = get_kolkata_now()
        
        result = cls.collection.update_one(
            {"_id": ObjectId(team_id)},
            {"$set": update_data}
        )
        
        if result.modified_count:
            return await cls.get_team_by_id(team_id)
        return None
    
    @classmethod
    async def add_team_member(cls, team_id: str, member: TeamMember) -> bool:
        """Add a member to a team"""
        # First check if member already exists
        team = await cls.get_team_by_id(team_id)
        if team:
            for existing_member in team.members:
                if existing_member.user_id == member.user_id:
                    return False  # Member already exists
        
        # Convert to dict for MongoDB and ensure proper serialization
        member_dict = member.dict()
        
        result = cls.collection.update_one(
            {"_id": ObjectId(team_id)},
            {
                "$push": {"members": member_dict},
                "$set": {"updated_at": get_kolkata_now()}
            }
        )
        return result.modified_count > 0
    
    @classmethod
    async def remove_team_member(cls, team_id: str, user_id: str) -> bool:
        """Remove a member from a team"""
        result = cls.collection.update_one(
            {"_id": ObjectId(team_id)},
            {
                "$pull": {"members": {"user_id": ObjectId(user_id)}},
                "$set": {"updated_at": get_kolkata_now()}
            }
        )
        return result.modified_count > 0
    
    @classmethod
    async def get_user_teams(cls, user_id: str) -> List[TeamInDB]:
        """Get all teams a user is a member of"""
        cursor = cls.collection.find({
            "$or": [
                {"lead_id": ObjectId(user_id)},
                {"members.user_id": ObjectId(user_id)}
            ]
        })
        
        return [TeamInDB(**team) for team in cursor]
    
    @classmethod
    async def get_all_teams(cls) -> List[TeamInDB]:
        """Get all teams"""
        cursor = cls.collection.find()
        return [TeamInDB(**team) for team in cursor]