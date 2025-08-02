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
    try:
        user = await authenticate_user(form_data.username, form_data.password)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        # --- FINAL PATCH: Avoid all PyObjectId validation errors by always converting ObjectId to str directly ---
        user_id = None
        username = None
        if isinstance(user, dict):
            _id = user.get("_id")
            user_id = str(_id) if _id is not None else str(user.get("id", ""))
            username = user.get("username")
        else:
            _id = getattr(user, "_id", None)
            user_id = str(_id) if _id is not None else str(getattr(user, "id", ""))
            username = getattr(user, "username", None)
        if not user_id or not username:
            logger.error("User object missing 'id'/'_id' or 'username' attribute")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal Server Error"
            )
        await DatabaseUsers.update_last_login(user_id)
        logger.warning(f"User login: {username} at 2025-06-11 06:52:04")
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": username}, expires_delta=access_token_expires
        )
        return {"access_token": access_token, "token_type": "bearer"}
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Login error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal Server Error"
        )

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
    response_users = []
    for user in users:
        if isinstance(user, dict):
            _id = user.get("_id")
            user_dict = user.copy()
            user_dict["id"] = str(_id) if _id is not None else str(user_dict.get("id", ""))
            user_dict.pop("_id", None)
        else:
            _id = getattr(user, "_id", None)
            user_dict = {field: getattr(user, field) for field in getattr(user, "__fields__", [])}
            user_dict["id"] = str(_id) if _id is not None else str(getattr(user, "id", ""))
            if "_id" in user_dict:
                user_dict.pop("_id")
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
        # --- FINAL PATCH: Avoid all PyObjectId validation errors by always converting ObjectId to str directly ---
        if isinstance(user_in_db, dict):
            _id = user_in_db.get("_id")
            user_dict = user_in_db.copy()
            user_dict["id"] = str(_id) if _id is not None else str(user_dict.get("id", ""))
            user_dict.pop("_id", None)
        else:
            _id = getattr(user_in_db, "_id", None)
            user_dict = {field: getattr(user_in_db, field) for field in getattr(user_in_db, "__fields__", [])}
            user_dict["id"] = str(_id) if _id is not None else str(getattr(user_in_db, "id", ""))
            if "_id" in user_dict:
                user_dict.pop("_id")
        return UserResponse(**user_dict)
    
    except HTTPException as e:
        # Re-raise HTTP exceptions
        raise e
    except Exception as e:
        # Log the error
        print(f"Registration error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error creating user",
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
        if isinstance(user_in_db, dict):
            _id = user_in_db.get("_id")
            user_dict = user_in_db.copy()
            user_dict["id"] = str(_id) if _id is not None else str(user_dict.get("id", ""))
            user_dict.pop("_id", None)
        else:
            _id = getattr(user_in_db, "_id", None)
            user_dict = {field: getattr(user_in_db, field) for field in getattr(user_in_db, "__fields__", [])}
            user_dict["id"] = str(_id) if _id is not None else str(getattr(user_in_db, "id", ""))
            if "_id" in user_dict:
                user_dict.pop("_id")
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
    user_dict = dict(current_user) if not isinstance(current_user, dict) else current_user.copy()
    
    # Handle ObjectId conversion
    if "_id" in user_dict:
        user_dict["id"] = str(user_dict.pop("_id"))
    elif "id" in user_dict:
        user_dict["id"] = str(user_dict["id"])
    
    # Ensure all ObjectId fields are converted to strings
    for key, value in user_dict.items():
        if hasattr(value, '__class__') and value.__class__.__name__ == 'ObjectId':
            user_dict[key] = str(value)
    
    return UserResponse(**user_dict)

@router.put("/me", response_model=UserResponse)
async def update_user(user_update: UserUpdate, current_user = Depends(get_current_user)):
    """Update current user profile"""
    updated_user = await DatabaseUsers.update_user(str(current_user.id), user_update)
    if updated_user:
        if isinstance(updated_user, dict):
            _id = updated_user.get("_id")
            user_dict = updated_user.copy()
            user_dict["id"] = str(_id) if _id is not None else str(user_dict.get("id", ""))
            user_dict.pop("_id", None)
        else:
            _id = getattr(updated_user, "_id", None)
            user_dict = {field: getattr(updated_user, field) for field in getattr(updated_user, "__fields__", [])}
            user_dict["id"] = str(_id) if _id is not None else str(getattr(updated_user, "id", ""))
            if "_id" in user_dict:
                user_dict.pop("_id")
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
    response_members = []
    for member in team_members:
        if isinstance(member, dict):
            _id = member.get("_id")
            member_dict = member.copy()
            member_dict["id"] = str(_id) if _id is not None else str(member_dict.get("id", ""))
            member_dict.pop("_id", None)
        else:
            _id = getattr(member, "_id", None)
            member_dict = {field: getattr(member, field) for field in getattr(member, "__fields__", [])}
            member_dict["id"] = str(_id) if _id is not None else str(getattr(member, "id", ""))
            if "_id" in member_dict:
                member_dict.pop("_id")
        response_members.append(UserResponse(**member_dict))
    return response_members

@router.put("/me/preferences", response_model=dict)
async def update_user_preferences(
    preferences_data: dict,
    current_user = Depends(get_current_user)
):
    """Update user preferences"""
    try:
        # Import here to avoid circular importss
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