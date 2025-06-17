from datetime import datetime, timedelta
from typing import Optional, Union
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel

from app.database import users_collection

# Secret key for JWT token generation
# In production, store this securely and load from environment variables
SECRET_KEY = "1234567890abcdefghijklmnopqrstuvwxyz1234567890"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 8  # 8 hours

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="users/token")

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None

# Import here to avoid circular imports
from app.database.users import UserInDB, DatabaseUsers

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

async def authenticate_user(username: str, password: str) -> Union[UserInDB, bool]:
    user = await DatabaseUsers.get_user_by_username(username)
    if not user:
        return False
    if not verify_password(password, user.hashed_password):
        return False
    return user

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
        
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


async def has_team_access(current_user: UserInDB) -> bool:
    """
    Check if the current user has access to team-related resources.
    Team leads, managers, and admins have access.
    """
    if current_user.role in ['team_lead', 'manager', 'admin']:
        return True
    return False

async def get_current_user(token: str = Depends(oauth2_scheme)) -> UserInDB:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        # Debug output for JWT token verification
        print(f"Verifying token: {token[:10]}...")
        
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except JWTError as e:
        print(f"JWT Error: {str(e)}")
        raise credentials_exception
    
    # Try to get user from database
    user = await DatabaseUsers.get_user_by_username(username=token_data.username)
    
    if user is None:
        print(f"User not found: {token_data.username}")
        raise credentials_exception
    
    # Check if user is active
    if not user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    
    # Debug output for user role
    print(f"User authenticated: {user.username}, Role: {user.role}")
    
    # Ensure role is properly formatted and case-insensitive
    # This is to handle potential database inconsistencies with role values
    if user.role:
        raw_role = user.role.lower().strip()
        # Map inconsistent roles to standard format
        role_mapping = {
            'teamlead': 'team_lead',
            'team lead': 'team_lead',
            'team-lead': 'team_lead',
            'administrator': 'admin',
            'employee': 'employee',
        }
        standardized_role = role_mapping.get(raw_role, raw_role)
        
        # Temporarily print the mapping for debugging
        print(f"Role mapping: {raw_role} -> {standardized_role}")
        
        # Update user role to standardized format if different
        if standardized_role != raw_role:
            print(f"Updating user role from {raw_role} to {standardized_role}")
            try:
                # Don't await here to avoid circular imports
                users_collection.update_one(
                    {"_id": user.id},
                    {"$set": {"role": standardized_role}}
                )
                # Update the user object for this session
                user.role = standardized_role
            except Exception as e:
                print(f"Error updating role: {str(e)}")
    
    return user

async def get_current_active_user(current_user: UserInDB = Depends(get_current_user)) -> UserInDB:
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user