from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, EmailStr
from bson import ObjectId
from app.database import db
from passlib.context import CryptContext

# Get users collection
users_collection = db["users"]

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")




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

class UserBase(BaseModel):
    username: str
    email: EmailStr
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    position: Optional[str] = None
    department: Optional[str] = None
    role: str = "employee"  # "employee", "team_lead", "manager", "admin"
    manager_id: Optional[str] = None
    is_active: bool = True
    
class UserCreate(UserBase):
    password: str

class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    position: Optional[str] = None
    department: Optional[str] = None
    role: Optional[str] = None
    manager_id: Optional[str] = None
    is_active: Optional[bool] = None
    password: Optional[str] = None

class UserInDB(UserBase):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    hashed_password: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        allow_population_by_field_name = True
        arbitrary_types_allowed = True
        json_encoders = {
            ObjectId: str,
            datetime: lambda v: v.isoformat()
        }

class UserResponse(UserBase):
    id: str = Field(alias="_id")
    created_at: datetime
    updated_at: datetime
    
    class Config:
        allow_population_by_field_name = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

class DatabaseUsers:
    @staticmethod
    async def get_user_by_id(user_id: str) -> Optional[UserInDB]:
        try:
            # Ensure user_id is properly converted to ObjectId
            if isinstance(user_id, str) and ObjectId.is_valid(user_id):
                id_obj = ObjectId(user_id)
            else:
                id_obj = user_id  # Use as-is if already ObjectId or invalid
            
            user = users_collection.find_one({"_id": id_obj})
            if user:
                return UserInDB(**user)
            return None
        except Exception as e:
            print(f"Error in get_user_by_id: {e}")
            return None

    @staticmethod
    async def get_user_by_username(username: str) -> Optional[UserInDB]:
        user = users_collection.find_one({"username": username})
        if user:
            return UserInDB(**user)
        return None
    
    @staticmethod
    async def get_user_by_email(email: str) -> Optional[UserInDB]:
        user = users_collection.find_one({"email": email})
        if user:
            return UserInDB(**user)
        return None
    
    @staticmethod
    async def create_user(user_data: UserCreate) -> UserInDB:
        # Check if username or email already exists
        existing_username = users_collection.find_one({"username": user_data.username})
        if existing_username:
            raise ValueError("Username already taken")
        
        existing_email = users_collection.find_one({"email": user_data.email})
        if existing_email:
            raise ValueError("Email already registered")
        
        # Hash password
        hashed_password = pwd_context.hash(user_data.password)
        
        # Create user document
        now = datetime.utcnow()
        user_dict = user_data.dict(exclude={"password"})
        user_dict.update({
            "hashed_password": hashed_password,
            "created_at": now,
            "updated_at": now
        })
        
        # Insert user
        result = users_collection.insert_one(user_dict)
        user_dict["_id"] = result.inserted_id
        
        return UserInDB(**user_dict)
    
    @staticmethod
    async def update_user(user_id: str, user_data: UserUpdate) -> Optional[UserInDB]:
        # Ensure user_id is properly converted
        if isinstance(user_id, str) and ObjectId.is_valid(user_id):
            id_obj = ObjectId(user_id)
        else:
            id_obj = user_id
        
        # Create update data
        update_data = {k: v for k, v in user_data.dict(exclude_unset=True).items() if v is not None}
        
        # Hash new password if provided
        if "password" in update_data:
            update_data["hashed_password"] = pwd_context.hash(update_data.pop("password"))
        
        if update_data:
            update_data["updated_at"] = datetime.utcnow()
            
            # Update user
            users_collection.update_one(
                {"_id": id_obj},
                {"$set": update_data}
            )
        
        # Return updated user
        updated_user = users_collection.find_one({"_id": id_obj})
        if updated_user:
            return UserInDB(**updated_user)
        return None
    
    @staticmethod
    async def delete_user(user_id: str) -> bool:
        # Ensure user_id is properly converted
        if isinstance(user_id, str) and ObjectId.is_valid(user_id):
            id_obj = ObjectId(user_id)
        else:
            id_obj = user_id
        
        # Delete user
        result = users_collection.delete_one({"_id": id_obj})
        return result.deleted_count > 0
    
    @staticmethod
    async def get_all_users() -> List[UserInDB]:
        users = list(users_collection.find())
        return [UserInDB(**user) for user in users]
    
    @staticmethod
    async def get_team_members_by_manager(manager_id: str) -> List[UserInDB]:
        """Get team members for a manager/team lead"""
        # Debug info
        print(f"Looking up team members for manager ID: {manager_id}")
        
        # Convert manager_id to proper format
        if isinstance(manager_id, str) and ObjectId.is_valid(manager_id):
            id_obj = ObjectId(manager_id)
        else:
            id_obj = manager_id
        
        # First check if manager exists
        manager = users_collection.find_one({"_id": id_obj})
        if not manager:
            print(f"Manager not found with ID: {manager_id}")
            return []
            
        # Check if this person is a team lead or manager
        manager_role = manager.get("role", "").lower()
        if not any(role in manager_role for role in ["team_lead", "manager", "admin"]):
            print(f"User with ID {manager_id} is not a team lead or manager (role: {manager_role})")
            return []
        
        # First try to find a team where this person is a lead
        from app.database import teams_collection
        team = teams_collection.find_one({"lead_id": str(id_obj)})
        
        if team:
            # Found a team with this person as lead
            print(f"Found team '{team['name']}' with {len(team.get('members', []))} members")
            member_ids = []
            
            for member in team.get("members", []):
                if isinstance(member, dict) and "user_id" in member:
                    member_ids.append(member["user_id"])
                elif isinstance(member, str):
                    member_ids.append(member)
            
            # Get full user details for each member
            members = []
            for member_id in member_ids:
                if isinstance(member_id, str) and ObjectId.is_valid(member_id):
                    user = users_collection.find_one({"_id": ObjectId(member_id)})
                else:
                    user = users_collection.find_one({"_id": member_id})
                    
                if user:
                    members.append(UserInDB(**user))
            
            return members
        
        # If no team found, check if this person is a manager with direct reports
        cursor = users_collection.find({"manager_id": str(id_obj)})
        direct_reports = list(cursor)
        
        if direct_reports:
            print(f"Found {len(direct_reports)} direct reports")
            return [UserInDB(**user) for user in direct_reports]
        
        # If still no team found, check for department-based reports
        if manager.get("department"):
            cursor = users_collection.find({
                "department": manager["department"],
                "_id": {"$ne": id_obj}  # Exclude the manager
            })
            dept_members = list(cursor)
            
            if dept_members:
                print(f"Found {len(dept_members)} department members")
                return [UserInDB(**user) for user in dept_members]
        
        # Last resort - if admin role, give them all users
        if "admin" in manager_role:
            print(f"User is admin, returning all non-admin users")
            cursor = users_collection.find({"role": {"$ne": "admin"}, "_id": {"$ne": id_obj}})
            all_users = list(cursor)
            return [UserInDB(**user) for user in all_users]
            
        print(f"No team members found for manager {manager_id}")
        return []
    
   