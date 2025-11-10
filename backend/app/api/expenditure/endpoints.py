from psycopg import AsyncConnection
from fastapi import APIRouter, Depends, HTTPException, status

from db.postgres import get_async_session
from app import auth
from . import schema
from . import handlers


router = APIRouter()

@router.get(
    "",
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_200_OK: {"description": "List of expenditures"},
        status.HTTP_400_BAD_REQUEST: {"description": "Bad request"},
        status.HTTP_401_UNAUTHORIZED: {"description": "Unauthorized - invalid or missing token"},
        status.HTTP_500_INTERNAL_SERVER_ERROR: {"description": "Server error"},
    },
)
async def get_expenditure(
    current_user: dict = Depends(auth.get_current_user), 
    conn: AsyncConnection = Depends(get_async_session)):
    """
    Get all expenditures for the authenticated user
    """
    try:
        response = await handlers.get_expenditures(current_user, conn)
        return response
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get expenditures. Please try again in a while.",
        )
    
@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    responses={
        status.HTTP_201_CREATED: {"description": "New expenditure created"},
        status.HTTP_401_UNAUTHORIZED: {"description": "Unauthorized - invalid or missing token"},
        status.HTTP_400_BAD_REQUEST: {"description": "Bad request"},
        status.HTTP_500_INTERNAL_SERVER_ERROR: {"description": "Database or unexpected server error"},
    },
)
async def create_expenditure(
    expenditure: schema.ExpenditureModel,
    current_user: dict = Depends(auth.get_current_user),
    conn: AsyncConnection = Depends(get_async_session)
):
    """
    Create a new expenditure for the authenticated user
    """
    try:
        response = await handlers.create_expenditure(current_user, expenditure, conn)
        return response

    except HTTPException as e:
        raise e

    except Exception as e:
        raise HTTPException(
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create expenditure. Please try again in a while.",
        )