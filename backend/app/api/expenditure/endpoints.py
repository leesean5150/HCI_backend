from psycopg import AsyncConnection
from typing import Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status

from db.postgres import get_async_session
from . import schema
from . import handlers


router = APIRouter()

@router.get(
    "",
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_200_OK: {"description": "List of expenditures"},
        status.HTTP_400_BAD_REQUEST: {"description": "Bad request"},
    },
)
async def get_documents(conn: AsyncConnection = Depends(get_async_session)):
    """
    Get all expenditures from the database
    """
    try:
        response = await handlers.get_expenditures(conn)
        return response
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            detail="Failed to get expenditures. Please try again in a while.",
        )
    
@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    responses={
        status.HTTP_201_CREATED: {"description": "New expenditure created"},
        status.HTTP_400_BAD_REQUEST: {"description": "Bad request"},
        status.HTTP_500_INTERNAL_SERVER_ERROR: {"description": "Database or unexpected server error"},
    },
)
async def get_documents(
    expenditure: schema.ExpenditureModel,
    conn: AsyncConnection = Depends(get_async_session)
):
    """
    Create a new expenditure to the database
    """
    try:
        response = await handlers.create_expenditure(expenditure, conn)
        return response

    except HTTPException as e:
        raise e

    except Exception as e:
        raise HTTPException(
            status.HTTP_500_BAD_REQUEST,
            detail="Failed to get expenditures. Please try again in a while.",
        )