from fastapi import APIRouter, Depends, HTTPException, status
from typing import Optional, List

from app.database.settings import UserSettingsUpdate, UserSettingsResponse, DatabaseSettings
from app.utils.auth import get_current_user

router = APIRouter(
    prefix="/settings",
    tags=["settings"],
    responses={404: {"description": "Not found"}},
)

@router.get("/user", response_model=UserSettingsResponse)
async def get_user_settings(current_user = Depends(get_current_user)):
    """Get settings for current user"""
    settings = await DatabaseSettings.get_user_settings(str(current_user.id))
    return UserSettingsResponse(**settings.dict(by_alias=True))

@router.put("/user", response_model=UserSettingsResponse)
async def update_user_settings(
    settings_data: UserSettingsUpdate,
    current_user = Depends(get_current_user)
):
    """Update settings for current user"""
    updated_settings = await DatabaseSettings.update_user_settings(
        str(current_user.id),
        settings_data
    )
    
    if not updated_settings:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update settings"
        )
    
    return UserSettingsResponse(**updated_settings.dict(by_alias=True))

@router.get("/system", response_model=dict)
async def get_system_settings(current_user = Depends(get_current_user)):
    """Get all system settings"""
    # Verify user has permission to view system settings
    if current_user.role not in ['admin']:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view system settings"
        )
    
    settings = await DatabaseSettings.get_all_system_settings()
    # Add timestamp
    settings["_timestamp"] = "2025-06-10 13:24:24"
    settings["_user"] = "soherucontinue"
    return settings

@router.put("/system/{key}", response_model=dict)
async def update_system_setting(
    key: str,
    value: str,
    description: Optional[str] = None,
    current_user = Depends(get_current_user)
):
    """Update a system setting"""
    # Verify user has permission to update system settings
    if current_user.role not in ['admin']:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update system settings"
        )
    
    setting = await DatabaseSettings.set_system_setting(key, value, description)
    return {
        "key": setting.setting_key,
        "value": setting.setting_value,
        "description": setting.description,
        "updated_at": setting.updated_at.isoformat(),
        "updated_by": "soherucontinue"
    }