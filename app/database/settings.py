from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from bson import ObjectId
from pymongo.collection import Collection
from app.database import settings_collection
from app.utils.helpers import PyObjectId

class UserSettings(BaseModel):
    user_id: PyObjectId
    theme: str = "light"  # light, dark, blue, green
    date_format: str = "DD/MM/YYYY"
    time_format: str = "12h"  # 12h or 24h
    language: str = "en"
    timezone: str = "UTC+05:30"
    notification_preferences: Dict[str, bool] = {
        "email_project_updates": True,
        "email_leave_requests": True,
        "email_daily_reports": False,
        "browser_notifications": True,
        "sound_alerts": False
    }
    
    class Config:
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}

class UserSettingsInDB(UserSettings):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    created_at: datetime = Field(default_factory=lambda: datetime.now())
    updated_at: datetime = Field(default_factory=lambda: datetime.now())
    
    class Config:
        json_schema_extra = {
            "example": {
                "_id": "60d21b4967d0d8820c43e888",
                "user_id": "60d21b4967d0d8820c43e123",
                "theme": "light",
                "date_format": "DD/MM/YYYY",
                "time_format": "12h",
                "language": "en",
                "timezone": "UTC+05:30",
                "notification_preferences": {
                    "email_project_updates": True,
                    "email_leave_requests": True,
                    "email_daily_reports": False,
                    "browser_notifications": True,
                    "sound_alerts": False
                },
                "created_at": "2025-01-01T00:00:00",
                "updated_at": "2025-06-10T13:17:39"
            }
        }

class UserSettingsUpdate(BaseModel):
    theme: Optional[str] = None
    date_format: Optional[str] = None
    time_format: Optional[str] = None
    language: Optional[str] = None
    timezone: Optional[str] = None
    notification_preferences: Optional[Dict[str, bool]] = None
    
    class Config:
        arbitrary_types_allowed = True

class UserSettingsResponse(BaseModel):
    id: str = Field(alias="_id")
    user_id: str
    theme: str
    date_format: str
    time_format: str
    language: str
    timezone: str
    notification_preferences: Dict[str, bool]
    created_at: datetime
    updated_at: datetime

# System-wide settings
class SystemSettings(BaseModel):
    setting_key: str
    setting_value: Any
    description: Optional[str] = None
    
    class Config:
        arbitrary_types_allowed = True

class SystemSettingsInDB(SystemSettings):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    created_at: datetime = Field(default_factory=lambda: datetime.now())
    updated_at: datetime = Field(default_factory=lambda: datetime.now())
    
    class Config:
        json_schema_extra = {
            "example": {
                "_id": "60d21b4967d0d8820c43e999",
                "setting_key": "leave_policy.sick_leave_annual",
                "setting_value": 12,
                "description": "Number of sick leave days allowed per year",
                "created_at": "2025-01-01T00:00:00",
                "updated_at": "2025-06-10T13:17:39"
            }
        }

class DatabaseSettings:
    collection: Collection = settings_collection
    
    @classmethod
    async def get_user_settings(cls, user_id: str) -> Optional[UserSettingsInDB]:
        """Get settings for a user"""
        settings_data = cls.collection.find_one({
            "user_id": ObjectId(user_id),
            "setting_type": "user"
        })
        
        if settings_data:
            return UserSettingsInDB(**settings_data)
        
        # If no settings found, create default settings
        return await cls.create_default_user_settings(user_id)
    
    @classmethod
    async def create_default_user_settings(cls, user_id: str) -> UserSettingsInDB:
        """Create default settings for a user"""
        settings = UserSettingsInDB(
            user_id=ObjectId(user_id),
            setting_type="user",
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        result = cls.collection.insert_one(settings.dict(by_alias=True))
        settings.id = result.inserted_id
        return settings
    
    @classmethod
    async def update_user_settings(cls, user_id: str, settings_data: UserSettingsUpdate) -> Optional[UserSettingsInDB]:
        """Update settings for a user"""
        update_data = {k: v for k, v in settings_data.dict().items() if v is not None}
        update_data["updated_at"] = datetime.now()
        
        result = cls.collection.update_one(
            {"user_id": ObjectId(user_id), "setting_type": "user"},
            {"$set": update_data}
        )
        
        if result.modified_count or result.matched_count:
            return await cls.get_user_settings(user_id)
            
        return None
    
    @classmethod
    async def get_system_setting(cls, key: str) -> Optional[SystemSettingsInDB]:
        """Get a system setting by key"""
        setting_data = cls.collection.find_one({
            "setting_key": key,
            "setting_type": "system"
        })
        
        if setting_data:
            return SystemSettingsInDB(**setting_data)
        return None
    
    @classmethod
    async def set_system_setting(cls, key: str, value: Any, description: Optional[str] = None) -> SystemSettingsInDB:
        """Set a system setting"""
        # Check if setting exists
        existing = await cls.get_system_setting(key)
        
        if existing:
            # Update existing setting
            update_data = {
                "setting_value": value,
                "updated_at": datetime.now()
            }
            
            if description:
                update_data["description"] = description
                
            cls.collection.update_one(
                {"setting_key": key, "setting_type": "system"},
                {"$set": update_data}
            )
            
            return await cls.get_system_setting(key)
        else:
            # Create new setting
            setting = SystemSettingsInDB(
                setting_key=key,
                setting_value=value,
                description=description,
                setting_type="system",
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
            
            result = cls.collection.insert_one(setting.dict(by_alias=True))
            setting.id = result.inserted_id
            return setting
    
    @classmethod
    async def get_all_system_settings(cls) -> Dict[str, Any]:
        """Get all system settings as a dictionary"""
        cursor = cls.collection.find({"setting_type": "system"})
        settings = {}
        
        for setting in cursor:
            settings[setting["setting_key"]] = setting["setting_value"]
            
        return settings