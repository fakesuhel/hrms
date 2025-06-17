from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from typing import List
from datetime import timedelta

from app.database.users import UserCreate, UserUpdate, UserResponse, DatabaseUsers
from app.utils.auth import authenticate_user, create_access_token, get_current_user, ACCESS_TOKEN_EXPIRE_MINUTES

router = APIRouter(
    prefix="/users",
    tags=["users"],
    responses={404: {"description": "Not found"}},
)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="users/token")


import logging
# Configure logging
logging.basicConfig(level=logging.INFO)
# Create a logger
logger = logging.getLogger(__name__)
@router.post("/token")
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    user = await authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Update last login time
    await DatabaseUsers.update_last_login(str(user.id))
    logger.warn(f"User login: {user.username} at 2025-06-11 06:52:04")
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    
    return {"access_token": access_token, "token_type": "bearer"}

# Create a route to get all users who are under my project  Like filter First check my all active projects then all assigned users
@router.get("/", response_model=List[UserResponse])
async def get_all_users(current_user = Depends(get_current_user)):
    """
    Get all users in the system.
    This endpoint is used for admin purposes to list all users.
    """
    if current_user.role not in ['admin', 'manager', 'team_lead', 'hr']:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access user information",
        )
    
    users = await DatabaseUsers.get_all_users()
    
    # Fix: Convert all users properly
    response_users = []
    for user in users:
        user_dict = user.dict(by_alias=True)
        # Explicitly set 'id' field from '_id' for UserResponse
        user_dict["id"] = str(user_dict.pop("_id"))
        response_users.append(UserResponse(**user_dict))
    
    return response_users

@router.post("/", response_model=UserResponse)
async def create_user(user: UserCreate):
    """
    Create a new user account.
    This endpoint is used for public user registration.
    """
    try:
        # Check if email exists
        existing_user = await DatabaseUsers.get_user_by_email(user.email)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered",
            )
        
        # Check if username exists
        existing_user = await DatabaseUsers.get_user_by_username(user.username)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already taken",
            )
        
        # For demo purposes, print the registration attempt
        print(f"User registration: {user.username} at 2025-06-11 06:52:04")
        
        # Create the user
        user_in_db = await DatabaseUsers.create_user(user)
        
        # Fix: Convert the document properly, ensuring the id field is included
        user_dict = user_in_db.dict(by_alias=True)
        # Explicitly set 'id' field from '_id' for UserResponse
        user_dict["id"] = str(user_dict.pop("_id"))
        
        return UserResponse(**user_dict)
    
    except HTTPException as e:
        # Re-raise HTTP exceptions
        raise e
    except Exception as e:
        # Log the error
        print(f"Registration error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating user: {str(e)}",
        )

@router.post("/employees", response_model=UserResponse)
async def create_employee(user: UserCreate, current_user = Depends(get_current_user)):
    """
    Create a new employee account.
    This endpoint is used by privileged users to create employee accounts.
    Requires team_lead, manager, director, or hr role.
    """
    # Check if user has permission to create employees
    if current_user.role not in ['team_lead', 'manager', 'director', 'hr', 'admin']:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to create employee accounts",
        )
    
    try:
        # Check if email exists
        existing_user = await DatabaseUsers.get_user_by_email(user.email)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered",
            )
        
        # Check if username exists
        existing_user = await DatabaseUsers.get_user_by_username(user.username)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already taken",
            )
        
        # Log the employee creation attempt
        print(f"Employee creation by {current_user.username}: {user.username} at 2025-06-17 09:24:54")
        
        # Create the employee
        user_in_db = await DatabaseUsers.create_user(user)
        
        # Fix: Convert the document properly, ensuring the id field is included
        user_dict = user_in_db.dict(by_alias=True)
        # Explicitly set 'id' field from '_id' for UserResponse
        user_dict["id"] = str(user_dict.pop("_id"))
        
        return UserResponse(**user_dict)
    
    except HTTPException as e:
        # Re-raise HTTP exceptions
        raise e
    except Exception as e:
        # Log the error
        print(f"Employee creation error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating employee: {str(e)}",
        )

@router.get("/me", response_model=UserResponse)
async def read_users_me(current_user = Depends(get_current_user)):
    """Get current user profile"""
    # Fix: Convert the document properly, ensuring the id field is included
    user_dict = current_user.dict(by_alias=True)
    # Explicitly set 'id' field from '_id' for UserResponse
    user_dict["id"] = str(user_dict.pop("_id"))
    
    return UserResponse(**user_dict)

@router.put("/me", response_model=UserResponse)
async def update_user(user_update: UserUpdate, current_user = Depends(get_current_user)):
    """Update current user profile"""
    updated_user = await DatabaseUsers.update_user(str(current_user.id), user_update)
    if updated_user:
        # Fix: Convert the document properly, ensuring the id field is included
        user_dict = updated_user.dict(by_alias=True)
        # Explicitly set 'id' field from '_id' for UserResponse
        user_dict["id"] = str(user_dict.pop("_id"))
        
        return UserResponse(**user_dict)
    raise HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail="Failed to update user",
    )

@router.get("/team", response_model=List[UserResponse])
async def get_team_members(current_user = Depends(get_current_user)):
    """Get team members for current user (if team lead or manager)"""
    if current_user.role not in ['team_lead', 'manager', 'admin']:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access team information",
        )
    
    team_members = await DatabaseUsers.get_team_members_by_manager(str(current_user.id))
    
    # Fix: Convert all team members properly
    response_members = []
    for member in team_members:
        member_dict = member.dict(by_alias=True)
        # Explicitly set 'id' field from '_id' for UserResponse
        member_dict["id"] = str(member_dict.pop("_id"))
        response_members.append(UserResponse(**member_dict))
    
    return response_members

@router.put("/me/preferences", response_model=dict)
async def update_user_preferences(
    preferences_data: dict,
    current_user = Depends(get_current_user)
):
    """Update user preferences"""
    try:
        # Import here to avoid circular imports
        from app.database.settings import DatabaseSettings, UserSettingsUpdate
        
        # Extract preferences from nested structure
        prefs = preferences_data.get('preferences', {})
        
        # Map frontend structure to backend structure
        settings_data = UserSettingsUpdate(
            theme=prefs.get('theme'),
            color_accent=prefs.get('color_accent'),
            language=prefs.get('language'),
            timezone=prefs.get('time_zone'),
            date_format=prefs.get('date_format'),
            notification_preferences=prefs.get('notifications', prefs.get('notification_preferences'))
        )
        
        # Update settings using database
        updated_settings = await DatabaseSettings.update_user_settings(
            str(current_user.id),
            settings_data
        )
        
        if not updated_settings:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update preferences"
            )
        
        # Return in the format expected by frontend
        return {
            "theme": updated_settings.theme,
            "color_accent": updated_settings.color_accent,
            "language": updated_settings.language,
            "time_zone": updated_settings.timezone,
            "date_format": updated_settings.date_format,
            "notifications": updated_settings.notification_preferences
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update preferences: {str(e)}"
        )

@router.get("/me/preferences", response_model=dict)
async def get_user_preferences(current_user = Depends(get_current_user)):
    """Get user preferences"""
    try:
        # Import here to avoid circular imports
        from app.database.settings import DatabaseSettings
        
        # Get settings from database
        settings = await DatabaseSettings.get_user_settings(str(current_user.id))
        
        # Return in the format expected by frontend
        return {
            "theme": settings.theme,
            "color_accent": settings.color_accent,
            "language": settings.language,
            "time_zone": settings.timezone,
            "date_format": settings.date_format,
            "notifications": settings.notification_preferences
        }
        
    except Exception as e:
        # Return default preferences if none exist
        return {
            "theme": "light",
            "color_accent": "blue",
            "language": "en",
            "time_zone": "Asia/Kolkata",
            "date_format": "DD/MM/YYYY",
            "notifications": {
                "email_project_updates": True,
                "email_leave_requests": True,
                "email_daily_reports": False,
                "browser_notifications": True,
                "sound_alerts": False
            }
        }