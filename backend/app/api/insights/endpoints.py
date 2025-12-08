from typing import List
from psycopg import AsyncConnection
from fastapi import APIRouter, Depends, HTTPException, status, Query
from datetime import date

from db.postgres import get_async_session
from app import auth
from . import handlers

router = APIRouter()

@router.get("/daily-totals",
    status_code=status.HTTP_200_OK,
    response_model=dict,
    responses={
        status.HTTP_200_OK: {"description": "Daily expenditure totals retrieved successfully"},
        status.HTTP_400_BAD_REQUEST: {"description": "Bad request - invalid date range"},
        status.HTTP_401_UNAUTHORIZED: {"description": "Unauthorized - invalid or missing token"},
        status.HTTP_500_INTERNAL_SERVER_ERROR: {"description": "Server error"},
    },
)
async def get_daily_expenditure_totals(
    start_date: date = Query(..., description="Start date (YYYY-MM-DD)"),
    end_date: date = Query(..., description="End date (YYYY-MM-DD)"),
    current_user: dict = Depends(auth.get_current_user),
    conn: AsyncConnection = Depends(get_async_session)
):
    """
    Get total expenditure for each date within a date range.
    Returns data formatted for line graph visualization.
    
    Example: GET /insights/daily-totals?start_date=2025-12-01&end_date=2025-12-05
    
    Response format:
    {
        "011225": 10.50,
        "021225": 20.00,
        "031225": 30.75
    }
    """
    return await handlers.get_daily_expenditure_totals(start_date, end_date, current_user, conn)

@router.get("/category-totals",
    status_code=status.HTTP_200_OK,
    response_model=dict,
    responses={
        status.HTTP_200_OK: {"description": "Category expenditure totals retrieved successfully"},
        status.HTTP_400_BAD_REQUEST: {"description": "Bad request - invalid date range"},
        status.HTTP_401_UNAUTHORIZED: {"description": "Unauthorized - invalid or missing token"},
        status.HTTP_500_INTERNAL_SERVER_ERROR: {"description": "Server error"},
    },
)
async def get_category_totals(
    start_date: date = Query(..., description="Start date (YYYY-MM-DD)"),
    end_date: date = Query(..., description="End date (YYYY-MM-DD)"),
    current_user: dict = Depends(auth.get_current_user),
    conn: AsyncConnection = Depends(get_async_session)
):
    """
    Get total expenditure for each category within a date range.
    Returns data formatted for pie chart or bar chart visualization.
    
    Example: GET /insights/category-totals?start_date=2025-12-01&end_date=2025-12-08
    
    Response format:
    {
        "Food": 150.50,
        "Transport": 75.00,
        "Entertainment": 120.25,
        "Uncategorized": 30.00
    }
    """
    return await handlers.get_category_totals(start_date, end_date, current_user, conn)
