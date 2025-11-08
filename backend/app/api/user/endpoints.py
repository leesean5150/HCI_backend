from psycopg import AsyncConnection
from fastapi import APIRouter, Depends, HTTPException, status

from db.postgres import get_async_session
from . import schema
from . import handlers

router = APIRouter()

@router.post("/create_offline",
    status_code=status.HTTP_201_CREATED,
    response_model=schema.UserOfflineResponse, 
    responses={
        status.HTTP_201_CREATED: {"description": "New offline user created"},
        status.HTTP_400_BAD_REQUEST: {"description": "Bad request"},
        status.HTTP_500_INTERNAL_SERVER_ERROR: {"description": "Database or unexpected server error"},
    },
)
async def create_offline_user(
    user_data: schema.UserModel,
    conn: AsyncConnection = Depends(get_async_session)
):
    """
    Create a new offline user (username + full_name only)
    """
    return await handlers.create_user(conn, user_data)

@router.put("/add_authentication",
    status_code=status.HTTP_200_OK,
    response_model=schema.UserResponse, 
    responses={
        status.HTTP_200_OK: {"description": "User authentication added successfully"},
        status.HTTP_400_BAD_REQUEST: {"description": "Bad request"},
        status.HTTP_500_INTERNAL_SERVER_ERROR: {"description": "Database or unexpected server error"},
    },
)
async def add_authentication(
    auth_data: schema.AddAuthenticationRequest,
    conn: AsyncConnection = Depends(get_async_session)
):
    """
    Add email and password to an existing offline user account
    (Upgrading from offline to online mode)
    """
    return await handlers.add_authentication_to_user(conn, auth_data)

@router.get("/get_user/{username}", 
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_200_OK: {"description": "User retrieved successfully"},
        status.HTTP_404_NOT_FOUND: {"description": "User not found"},
        status.HTTP_500_INTERNAL_SERVER_ERROR: {"description": "Database or unexpected server error"},
    },
)
async def get_user(
    username: str, 
    conn: AsyncConnection = Depends(get_async_session)
):
    """
    Get user information by username
    """
    return await handlers.get_user(conn, username)

@router.put("/update_profile",
    status_code=status.HTTP_200_OK,
    response_model=schema.UserOfflineResponse,  # Changed: might not have email
    responses={
        status.HTTP_200_OK: {"description": "User profile updated successfully"},
        status.HTTP_400_BAD_REQUEST: {"description": "Bad request"},
        status.HTTP_404_NOT_FOUND: {"description": "User not found"},
        status.HTTP_500_INTERNAL_SERVER_ERROR: {"description": "Database or unexpected server error"},
    },
)
async def update_user_profile(
    current_username: str,  # Added: need to know which user to update
    update_data: schema.UserUpdateRequest,
    conn: AsyncConnection = Depends(get_async_session)
):
    """
    Update user profile information (username, full_name)
    """
    return await handlers.update_user(conn, current_username, update_data) 

@router.delete("/delete_user/{username}", 
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_200_OK: {"description": "User deleted successfully"},
        status.HTTP_404_NOT_FOUND: {"description": "User not found"},
        status.HTTP_500_INTERNAL_SERVER_ERROR: {"description": "Database or unexpected server error"},
    },
)
async def delete_user(
    username: str,  
    conn: AsyncConnection = Depends(get_async_session)
):
    """
    Delete a user by username
    """
    return await handlers.delete_user(conn, username)