from typing import List
from psycopg import AsyncConnection
from fastapi import APIRouter, Depends, HTTPException, status

from db.postgres import get_async_session
from app import auth
from . import schema
from . import handlers

router = APIRouter()

@router.post("/register",
    status_code=status.HTTP_201_CREATED,
    response_model=schema.UserResponse, 
    responses={
        status.HTTP_201_CREATED: {"description": "New user created successfully"},
        status.HTTP_400_BAD_REQUEST: {"description": "Bad request - username or email already exists"},
        status.HTTP_500_INTERNAL_SERVER_ERROR: {"description": "Database or unexpected server error"},
    },
)
async def register_user(
    user_data: schema.UserRegisterRequest,
    conn: AsyncConnection = Depends(get_async_session)
):
    """
    Register a new user with email and password
    """
    return await handlers.create_user(conn, user_data)

@router.post("/login",
    status_code=status.HTTP_200_OK,
    response_model=schema.TokenResponse,
    responses={
        status.HTTP_200_OK: {"description": "User logged in successfully, returns access token and user info"},
        status.HTTP_401_UNAUTHORIZED: {"description": "Invalid username or password"},
        status.HTTP_500_INTERNAL_SERVER_ERROR: {"description": "Database or unexpected server error"},
    },
)
async def login_user(
    login_data: schema.UserLoginRequest,
    conn: AsyncConnection = Depends(get_async_session)
):
    """
    Authenticate user and return JWT access token with user information
    """
    return await handlers.login_user(conn, login_data)

@router.post("/logout",
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_200_OK: {"description": "User logged out successfully, all tokens invalidated"},
        status.HTTP_401_UNAUTHORIZED: {"description": "Unauthorized - invalid or missing token"},
        status.HTTP_500_INTERNAL_SERVER_ERROR: {"description": "Server error"},
    },
)
async def logout_user(
    current_user: dict = Depends(auth.get_current_user),
    conn: AsyncConnection = Depends(get_async_session)
):
    """
    Logout the current user by incrementing their token version.
    This invalidates ALL tokens for this user across all devices.
    """
    return await handlers.logout_user(conn, current_user)

@router.get("/me",
    status_code=status.HTTP_200_OK,
    response_model=schema.UserResponse,
    responses={
        status.HTTP_200_OK: {"description": "Current user profile retrieved successfully"},
        status.HTTP_401_UNAUTHORIZED: {"description": "Unauthorized - invalid or missing token"},
        status.HTTP_500_INTERNAL_SERVER_ERROR: {"description": "Server error"},
    },
)
async def get_current_user_profile(
    current_user: dict = Depends(auth.get_current_user)
):
    """
    Get the profile information of the currently authenticated user
    """
    return await handlers.get_current_user_profile(current_user)

@router.put("/update_profile",
    status_code=status.HTTP_200_OK,
    response_model=schema.UserResponse,
    responses={
        status.HTTP_200_OK: {"description": "User profile updated successfully"},
        status.HTTP_400_BAD_REQUEST: {"description": "Bad request - invalid data or username/email already exists"},
        status.HTTP_401_UNAUTHORIZED: {"description": "Unauthorized - invalid or missing token"},
        status.HTTP_500_INTERNAL_SERVER_ERROR: {"description": "Database or unexpected server error"},
    },
)
async def update_user_profile(
    update_data: schema.UserUpdateRequest,
    current_user: dict = Depends(auth.get_current_user),
    conn: AsyncConnection = Depends(get_async_session)
):
    """
    Update the profile of the current authenticated user
    """
    return await handlers.update_user(conn, current_user, update_data)

@router.delete("/account",
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_200_OK: {"description": "User account deleted successfully"},
        status.HTTP_401_UNAUTHORIZED: {"description": "Unauthorized - invalid or missing token"},
        status.HTTP_500_INTERNAL_SERVER_ERROR: {"description": "Database or unexpected server error"},
    },
)
async def delete_user_account(
    current_user: dict = Depends(auth.get_current_user),
    conn: AsyncConnection = Depends(get_async_session)
):
    """
    Delete the current authenticated user's account permanently
    """
    return await handlers.delete_user(conn, current_user)

@router.get("/all_users",
    status_code=status.HTTP_200_OK,
    response_model=List[schema.UserResponse],
    responses={
        status.HTTP_200_OK: {"description": "All users retrieved successfully"},
        status.HTTP_500_INTERNAL_SERVER_ERROR: {"description": "Database or unexpected server error"},
    },
)
async def get_all_users(
    conn: AsyncConnection = Depends(get_async_session)
):
    """
    Get a list of all users in the database
    """
    return await handlers.get_all_users(conn)