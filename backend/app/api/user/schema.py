from pydantic import BaseModel, Field, EmailStr
from datetime import datetime
from typing import Optional
from uuid import UUID

# Our Base schema 
class UserBase(BaseModel):
    username: str = Field(max_length=150, description="The unique username of the user.")
    full_name: Optional[str] = Field(None, max_length=255, description="The full name of the user.")

# Schema to register teh user
class UserRegisterRequest(BaseModel):
    username: str = Field(max_length=150, description="The unique username of the user.")
    email: EmailStr = Field(description="User's email address.")
    password: str = Field(min_length=8, description="Required password for authentication.")
    full_name: Optional[str] = Field(None, max_length=255, description="The full name of the user.")

# Schema to log user in
class UserLoginRequest(BaseModel):
    username: str = Field(max_length=150, description="The unique username of the user.")
    password: str = Field(min_length=8, description="Password for authentication.")

# Schema for user responses
class UserResponse(UserBase):
    uuid: UUID
    email: EmailStr
    created: Optional[datetime] = None
    updated: Optional[datetime] = None

# Schema for JWT token response
class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse

# Schema for updating the user profile
class UserUpdateRequest(BaseModel):
    username: Optional[str] = Field(None, max_length=150, description="New username (optional)")
    full_name: Optional[str] = Field(None, max_length=255, description="Updated full name (optional)")
    email: Optional[EmailStr] = Field(None, description="Updated email address (optional)")
    password: Optional[str] = Field(None, min_length=8, description="New password (optional)")

# Schema for forgot password request
class UserForgotPasswordRequest(BaseModel):
    email: EmailStr = Field(description="The email address associated with the user account.")

# Schema for user stored in database, this should only be for internal useeeee
class UserInDB(UserBase):
    uuid: UUID
    email: EmailStr
    hashed_password: str
    created: Optional[datetime] = None
    updated: Optional[datetime] = None