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