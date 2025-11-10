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
    
async def get_approved_expenditures(
    conn: AsyncConnection = Depends(get_async_session)
):
    """
    get all expenditures that have status == 'Appproved' from the database
    """
    try:
        query = """
            SELECT *
            FROM expenditure
            WHERE status='Approved'
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
    
async def get_pending_expenditures(
    conn: AsyncConnection = Depends(get_async_session)
):
    """
    get all expenditures that have status == 'Pending' from the database
    """
    try:
        query = """
            SELECT *
            FROM expenditure
            WHERE status='Pending'
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
    
async def update_expenditure_by_id(id: str, data: schema.ExpenditureUpdateModel, conn: AsyncConnection):
    """
    Handler to dynamically update an expenditure by its ID. Only updates fields that are not None in the data.
    """
    
    update_data = data.model_dump(exclude_unset=True)

    if not update_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No update data provided."
        )

    set_parts = []
    values = []
    
    for i, (key, value) in enumerate(update_data.items()):
        set_parts.append(f"{key} = %s")
        values.append(value)
    
    set_clause = ", ".join(set_parts)

    values.append(id)
    values_tuple = tuple(values)
    
    # 3. Build the full query
    # Assuming your ID column is 'uuid'
    query = f"""
        UPDATE expenditure
        SET {set_clause}
        WHERE uuid = %s
        RETURNING uuid, name, status, amount, category, date_of_expense, notes;
    """

    try:
        async with conn.cursor() as cur:
            await cur.execute(query, values_tuple)
            updated_row = await cur.fetchone()

            if updated_row is None:
                await conn.rollback()
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Expenditure with ID '{id}' not found."
                )

        await conn.commit()

        return updated_row

    except HTTPException as e:
        raise e

    except Exception as e:
        await conn.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: Could not update expenditure. Details: {str(e)}"
        )
    
async def approve_single_pending_expenditure(
    id: str,
    conn: AsyncConnection = Depends(get_async_session)
):
    """
    Handler to update a single expenditure's status to 'Approved'.
    """
    query = """
        UPDATE expenditure
        SET status = 'Approved'
        WHERE uuid = %s AND status = 'Pending'
        RETURNING uuid, name, status, amount, category, date_of_expense, notes
    """
    values = (id,)

    try:
        async with conn.cursor() as cur:
            await cur.execute(query, values)
            updated_row = await cur.fetchone()
            
            if updated_row is None:
                await conn.rollback() 
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"No pending expenditure with ID '{id}' found to approve."
                )
            
        await conn.commit()
        return updated_row
    
    except HTTPException as e:
        raise e

    except Exception as e:
        await conn.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: Could not approve expenditure. Details: {str(e)}"
        )

async def approve_all_pending_expenditures(
    conn: AsyncConnection = Depends(get_async_session)
):
    query = """
        UPDATE expenditure
        SET status = 'Approved'
        WHERE status = 'Pending'
    """

    try:
        async with conn.cursor() as cur:
            await cur.execute(query)
            updated_count = cur.rowcount

        await conn.commit()

        return {"updated_count": updated_count}
    
    except Exception as e:
        await conn.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: Could not approve expenditure. Details: {str(e)}"
        )
    
async def delete_expenditure_by_id(id: str, conn: AsyncConnection):
    """
    Handler to delete a single expenditure by its ID
    """
    query = "DELETE FROM expenditure WHERE uuid = %s;"
    values = (id,)

    try:
        async with conn.cursor() as cur:
            await cur.execute(query, values)
            
            deleted_count = cur.rowcount

            if deleted_count == 0:
                await conn.rollback()
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Expenditure with ID '{id}' not found."
                )

        await conn.commit()
        
        return {"id": id, "status": "deleted"}

    except HTTPException as e:
        raise e

    except Exception as e:
        await conn.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: Could not delete expenditure. Details: {str(e)}"
        )