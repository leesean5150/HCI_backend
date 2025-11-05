from fastapi import APIRouter, Depends, HTTPException, status
from psycopg import AsyncConnection

from db.postgres import get_async_session
from . import schema


router = APIRouter()

async def get_expenditures(
    conn: AsyncConnection = Depends(get_async_session)
):
    """
    get all expenditures from the database
    """

    try:
        query = """
            SELECT *
            FROM expenditure
            ORDER BY created_at DESC
        """

        async with conn.cursor() as cur:
            await cur.execute(query)
            results = await cur.fetchall()
            print(results)
            return results
            
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {str(e)}"
        )
    
async def create_expenditure(
    expenditure: schema.ExpenditureModel,
    conn: AsyncConnection = Depends(get_async_session)
):
    """
    create a new expenditure in the database
    """
    query = """
        INSERT INTO expenditure (
            name, 
            date_of_expense, 
            amount, 
            category, 
            notes, 
            status
        ) VALUES (
            %s, %s, %s, %s, %s, %s
        )
        RETURNING uuid, created_at;
    """
    
    # Prepare data tuple from the Pydantic model
    values = (
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