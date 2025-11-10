from fastapi import APIRouter, Depends, HTTPException, status
from psycopg import AsyncConnection

from db.postgres import get_async_session
from . import schema


router = APIRouter()

async def get_expenditures(
    current_user: dict,
    conn: AsyncConnection = Depends(get_async_session)
):
    """
    Get all expenditures for the authenticated user from the database
    """

    try:
        query = """
            SELECT uuid, name, created_at, date_of_expense, amount, category, notes, status
            FROM expenditure
            WHERE user_uuid = %s
            ORDER BY created_at DESC
        """

        async with conn.cursor() as cur:
            await cur.execute(query, (current_user['uuid'],))
            results = await cur.fetchall()
            return results
            
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {str(e)}"
        )
    
async def create_expenditure(
    current_user: dict,
    expenditure: schema.ExpenditureModel,
    conn: AsyncConnection = Depends(get_async_session)
):
    """
    Create a new expenditure for the authenticated user in the database
    """
    query = """
        INSERT INTO expenditure (
            user_uuid,
            name, 
            date_of_expense, 
            amount, 
            category, 
            notes, 
            status
        ) VALUES (
            %s, %s, %s, %s, %s, %s, %s
        )
        RETURNING uuid, created_at;
    """
    
    # Prepare data tuple from the Pydantic model
    values = (
        current_user['uuid'], 
        expenditure.name,
        expenditure.date_of_expense,
        expenditure.amount,
        expenditure.category,
        expenditure.notes,
        expenditure.status,
    )

    try:
        async with conn.cursor() as cur:
            await cur.execute(query, values)
            
            returned_data = await cur.fetchone()
            
        return {**expenditure.model_dump(), **returned_data}

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: Could not create expenditure record. Details: {str(e)}"
        ) 