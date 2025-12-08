from fastapi import HTTPException, status
from psycopg import AsyncConnection
from datetime import date
from typing import Dict

async def get_daily_expenditure_totals(
    start_date: date,
    end_date: date,
    current_user: dict,
    conn: AsyncConnection
) -> Dict[str, float]:
    """
    Get total expenditure for each date within a date range.
    Returns data formatted for line graph: {"ddmmyy": total_amount, ...}
    Includes days with 0 expenditure.
    """
    if start_date > end_date:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Start date must be before or equal to end date."
        )
    
    try:
        async with conn.cursor() as cur:
            query = """
            WITH date_series AS (
                SELECT generate_series(%s::date, %s::date, '1 day'::interval)::date AS day
            )
            SELECT 
                TO_CHAR(ds.day, 'YYYYMMDD') as date_key,
                COALESCE(SUM(e.amount), 0) as total
            FROM date_series ds
            LEFT JOIN expenditure e 
                ON e.date_of_expense = ds.day 
                AND e.user_uuid = %s
            GROUP BY ds.day
            ORDER BY ds.day ASC;
            """
            
            await cur.execute(query, (start_date, end_date, current_user['uuid']))
            results = await cur.fetchall()
            
            # Format as {date: total} dictionary
            daily_totals = {row['date_key']: float(row['total']) for row in results}
            
            return daily_totals
            
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {str(e)}"
        )

async def get_category_totals(
    start_date: date,
    end_date: date,
    current_user: dict,
    conn: AsyncConnection
) -> Dict[str, float]:
    """
    Get total expenditure for each category within a date range.
    Returns data formatted for pie/bar charts: {"category": total_amount, ...}
    """
    if start_date > end_date:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Start date must be before or equal to end date."
        )
    
    try:
        async with conn.cursor() as cur:
            query = """
            SELECT 
                COALESCE(category, 'Uncategorized') as category,
                SUM(amount) as total
            FROM expenditure
            WHERE user_uuid = %s
              AND date_of_expense BETWEEN %s AND %s
            GROUP BY category
            ORDER BY total DESC;
            """
            
            await cur.execute(query, (current_user['uuid'], start_date, end_date))
            results = await cur.fetchall()
            
            category_totals = {row['category']: float(row['total']) for row in results}
            
            return category_totals
            
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {str(e)}"
        )
