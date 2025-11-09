from psycopg import AsyncConnection
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
async def get_expenditure(conn: AsyncConnection = Depends(get_async_session)):
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
    
@router.get(
    "/approved",
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_200_OK: {"description": "List of approved expenditures"},
        status.HTTP_400_BAD_REQUEST: {"description": "Bad request"},
    },
)
async def get_approved_expenditures(conn: AsyncConnection = Depends(get_async_session)):
    """
    Get all approved expenditures from the database
    """
    try:
        response = await handlers.get_approved_expenditures(conn)
        return response
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            detail="Failed to get approved expenditures. Please try again in a while.",
        )

@router.get(
    "/pending",
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_200_OK: {"description": "List of pending expenditures"},
        status.HTTP_400_BAD_REQUEST: {"description": "Bad request"},
    },
)
async def get_pending_expenditures(conn: AsyncConnection = Depends(get_async_session)):
    """
    Get all pending expenditures from the database
    """
    try:
        response = await handlers.get_pending_expenditures(conn)
        return response
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            detail="Failed to get pending expenditures. Please try again in a while.",
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
async def create_expenditure(
    expenditure: schema.ExpenditureModel,
    conn: AsyncConnection = Depends(get_async_session)
):
    """
    Create a new expenditure to the database
    """
    try:
        response = await handlers.create_expenditure(expenditure=expenditure, conn=conn)
        return response

    except HTTPException as e:
        raise e

    except Exception as e:
        raise HTTPException(
            status.HTTP_500_BAD_REQUEST,
            detail="Failed to get expenditures. Please try again in a while.",
        )
    
@router.patch(
    "/{id}",
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_200_OK: {"description": "Successfully updated expense"},
        status.HTTP_400_BAD_REQUEST: {"description": "Bad request (e.g., no update data provided)"},
        status.HTTP_404_NOT_FOUND: {"description": "Expenditure with this ID not found"},
        status.HTTP_500_INTERNAL_SERVER_ERROR: {"description": "Internal server error"},
    },
)
async def update_single_expenditure(
    id: str,
    expenditure_data: schema.ExpenditureUpdateModel, 
    conn: AsyncConnection = Depends(get_async_session)
):
    """
    Finds and updates a single expenditure by its ID.
    Only updates the fields provided in the request body.
    """
    try:
        response = await handlers.update_expenditure_by_id(
            id=id, 
            data=expenditure_data, 
            conn=conn
        )
        return response

    except HTTPException as e:
        raise e

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            # Updated error detail
            detail=f"Server failed to update expenditure: {str(e)}. Please try again.",
        )
    
@router.patch(
    "/expenditure/approve/{id}",
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_200_OK: {"description": "Expenditure approved successfully"},
        status.HTTP_404_NOT_FOUND: {"description": "Pending expenditure with this ID not found"},
        status.HTTP_500_INTERNAL_SERVER_ERROR: {"description": "Internal server error"},
    },
)
async def approve_single_pending_expenditure(
    id: str,
    conn: AsyncConnection = Depends(get_async_session)
):
    """
    Finds and approves a single 'Pending' expenditure by its ID.
    """
    try:
        response = await handlers.approve_single_pending_expenditure(id=id, conn=conn)
        return response

    except HTTPException as e:
        raise e

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Server failed to approve expenditure: {str(e)}. Please try again.",
        )

@router.patch(
    "/expenditure/approve",
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_200_OK: {"description": "All pending expenditures approved. Returns a count."},
        status.HTTP_500_INTERNAL_SERVER_ERROR: {"description": "Internal server error"},
    },
)
async def approve_all_pending_expenditures(
    conn: AsyncConnection = Depends(get_async_session)
):
    """
    Finds and approves all 'Pending' expenditures.
    """
    try:
        response = await handlers.approve_all_pending_expenditures(conn=conn)
        return response

    except HTTPException as e:
        raise e

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Server failed to approve expenditure: {str(e)}. Please try again.",
        )
    
@router.delete(
    "/expenditure/{id}",
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_200_OK: {"description": "Expenditure deleted successfully"},
        status.HTTP_404_NOT_FOUND: {"description": "Expenditure not found"},
        status.HTTP_500_INTERNAL_SERVER_ERROR: {"description": "Database or unexpected server error"},
    },
)
async def delete_expenditure_by_id(
    id: str,
    conn: AsyncConnection = Depends(get_async_session)       
):
    """
    Deletes an expenditure by its ID
    """
    try:
        response = await handlers.delete_expenditure_by_id(id=id, conn=conn)
        return response
    
    except HTTPException as e:
        raise e

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Server failed to delete expenditure: {str(e)}. Please try again.",
        )
