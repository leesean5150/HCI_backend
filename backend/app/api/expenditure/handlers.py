from fastapi import HTTPException, status
from psycopg import AsyncConnection

from . import schema

UPDATABLE_FIELDS = {
    "name", "date_of_expense", "amount", 
    "category", "notes", "status"
}

async def get_expenditures(
    current_user: dict,
    conn: AsyncConnection
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
        raise e

async def get_approved_expenditures(
    current_user: dict,
    conn: AsyncConnection
):
    """
    get all expenditures that have status == 'Appproved' from the database
    """
    try:
        query = """
            SELECT *
            FROM expenditure
            WHERE status='Approved' AND user_uuid = %s
            ORDER BY created_at DESC
        """

        async with conn.cursor() as cur:
            await cur.execute(query, (current_user['uuid'],))
            results = await cur.fetchall()
            return results
            
    except Exception as e:
        raise e
    
async def get_pending_expenditures(
    current_user: dict,
    conn: AsyncConnection
):
    """
    get all expenditures that have status == 'Pending' from the database
    """
    try:
        query = """
            SELECT *
            FROM expenditure
            WHERE status='Pending' AND user_uuid = %s
            ORDER BY created_at DESC
        """

        async with conn.cursor() as cur:
            await cur.execute(query, (current_user['uuid'],))
            results = await cur.fetchall()
            return results
            
    except Exception as e:
        raise e
    
async def create_expenditure(
    current_user: dict,
    expenditure: schema.ExpenditureModel,
    conn: AsyncConnection
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
        
        await conn.commit()
            
        return {**expenditure.model_dump(), **returned_data}

    except HTTPException:
        await conn.rollback()
        raise
        
    except Exception as e:
        await conn.rollback()
        raise e
    
async def update_expenditure_by_id(
    id: str, 
    data: schema.ExpenditureUpdateModel,
    current_user: dict,
    conn: AsyncConnection
):
    """
    Handler to dynamically update an expenditure by its ID. 
    This is now secure against SQL injection.
    """
    
    update_data = data.model_dump(exclude_unset=True)

    if not update_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No update data provided."
        )

    set_parts = []
    values = []
    
    for key, value in update_data.items():
        if key in UPDATABLE_FIELDS:
            set_parts.append(f"{key} = %s")
            values.append(value)
        else:
            pass

    if not set_parts:
         raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No valid fields to update were provided."
        )

    set_clause = ", ".join(set_parts)

    values.append(id)
    values.append(current_user['uuid'])
    values_tuple = tuple(values)
    
    query = f"""
        UPDATE expenditure
        SET {set_clause}
        WHERE uuid = %s AND user_uuid = %s
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
                    detail=f"Expenditure with ID '{id}' not found or you do not have permission."
                )

        await conn.commit()
        return updated_row

    except HTTPException as e:
        raise e

    except Exception as e:
        await conn.rollback()
        raise e
    
async def approve_single_pending_expenditure(
    id: str,
    current_user: dict,
    conn: AsyncConnection
):
    """
    Handler to update a single expenditure's status to 'Approved'.
    """
    query = """
        UPDATE expenditure
        SET status = 'Approved'
        WHERE uuid = %s AND status = 'Pending' AND user_uuid = %s
        RETURNING uuid, name, status, amount, category, date_of_expense, notes
    """
    values = (id, current_user['uuid'])

    try:
        async with conn.cursor() as cur:
            await cur.execute(query, values)
            updated_row = await cur.fetchone()
            
            if updated_row is None:
                await conn.rollback() 
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"No pending expenditure with ID '{id}' found to approve or you do not have permission."
                )
            
        await conn.commit()
        return updated_row
    
    except HTTPException as e:
        raise e

    except Exception as e:
        await conn.rollback()
        raise e

async def approve_all_pending_expenditures(
    current_user: dict,
    conn: AsyncConnection
):
    """ Approves all pending expenditures for the current user. """
    query = """
        UPDATE expenditure
        SET status = 'Approved'
        WHERE status = 'Pending' AND user_uuid = %s
    """
    values = (current_user['uuid'],)

    try:
        async with conn.cursor() as cur:
            await cur.execute(query, values)
            updated_count = cur.rowcount

        await conn.commit()

        return {"updated_count": updated_count}
    
    except Exception as e:
        await conn.rollback()
        raise e
    
async def delete_expenditure_by_id(
    id: str,
    current_user: dict,
    conn: AsyncConnection
):
    """
    Handler to delete a single expenditure by its ID.
    Ensures the expenditure belongs to the current user.
    """
    query = "DELETE FROM expenditure WHERE uuid = %s AND user_uuid = %s;"
    values = (id, current_user['uuid'])

    try:
        async with conn.cursor() as cur:
            await cur.execute(query, values)
            
            deleted_count = cur.rowcount

            if deleted_count == 0:
                await conn.rollback()
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Expenditure with ID '{id}' not found or you do not have permission."
                )

        await conn.commit()
        
        return {"id": id, "status": "deleted"}

    except HTTPException as e:
        raise e

    except Exception as e:
        await conn.rollback()
        raise e