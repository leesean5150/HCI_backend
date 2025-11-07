from pydantic import BaseModel, Field, EmailStr
from datetime import datetime
from typing import Optional
from uuid import UUID

# Our base schema for user-related data
class UserBase(BaseModel):
    username: str = Field(max_length=150, description="The unique username of the user.")
    full_name: Optional[str] = Field(None, max_length=255, description="The full name of the user.")

# offline so we dont need any authentication
class UserModel(UserBase):
    pass

#for direct online user creation but we dont use first
class UserCreate(UserBase):
    email: EmailStr = Field(description="Email for online mode.")
    password: str = Field(min_length=8, description="Required password for authentication.")
    
#for adding authentication to existing user
class AddAuthenticationRequest(BaseModel):
    username: str = Field(max_length=150, description="The unique username of the user.")
    email: EmailStr = Field(description="Email for online mode.")
    password: str = Field(min_length=8, description="Required password for authentication.")

#for storing user in the database  
class UserInDB(UserBase):
    email: EmailStr
    hashed_password: str
    created: Optional[datetime] = None  
    updated: Optional[datetime] = None

#for offline user response
class UserOfflineResponse(UserBase):
    """Response for offline user (no email)"""
    uuid: UUID
    created: Optional[datetime] = None
    updated: Optional[datetime] = None

#for online user response
class UserResponse(UserBase):
    uuid: UUID
    email: EmailStr
    created: Optional[datetime] = None
    updated: Optional[datetime] = None
    


# Do we need more fields like is_active, is_superuser etc.? this app gonna be offline right.. LOL