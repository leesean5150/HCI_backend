from fastapi import HTTPException
from psycopg import AsyncConnection
from . import schema
import uuid

# ---- Tasks (with auto user creation) ----
async def create_task(task: schema.WebExpTaskCreate, conn: AsyncConnection):
    """
    Create a task for a user. If the user doesn't exist, create the user first.
    """
    task_id = str(uuid.uuid4())
    try:
        async with conn.cursor() as cur:
            # Insert user if not exists (ON CONFLICT DO NOTHING handles existing users)
            await cur.execute(
                "INSERT INTO webexp_users (user_id) VALUES (%s) ON CONFLICT (user_id) DO NOTHING;",
                (task.user_id,)
            )

            # Now create the task
            await cur.execute(
                """
                INSERT INTO webexp_tasks (task_id, user_id, task_number, time_taken_seconds)
                VALUES (%s, %s, %s, %s)
                RETURNING task_id, user_id, task_number, time_taken_seconds;
                """,
                (task_id, task.user_id, task.task_number, task.time_taken_seconds)
            )
            created = await cur.fetchone()
            await conn.commit()  # Commit the transaction
            return {
                "task_id": str(created["task_id"]),
                "user_id": created["user_id"],
                "task_number": created["task_number"],
                "time_taken_seconds": created["time_taken_seconds"],
            }
    except Exception as e:
        print(f"Error creating task: {e}")  # Log for debugging
        raise HTTPException(status_code=400, detail=str(e))


async def update_task_time(task_update: schema.WebExpTaskUpdateTime, conn: AsyncConnection):
    """
    Update the time_taken_seconds for a task.
    Requires task_id along with user_id and task_number for validation.
    """
    try:
        async with conn.cursor() as cur:
            # Validate that task_id matches user_id + task_number
            if task_update.task_id and task_update.user_id and task_update.task_number is not None:
                await cur.execute(
                    """
                    SELECT task_id FROM webexp_tasks 
                    WHERE task_id = %s AND user_id = %s AND task_number = %s;
                    """,
                    (task_update.task_id, task_update.user_id, task_update.task_number)
                )
                validation = await cur.fetchone()
                if not validation:
                    raise HTTPException(
                        status_code=404, 
                        detail="Task not found or task_id does not match user_id and task_number"
                    )
                
                # Update using task_id (most specific)
                await cur.execute(
                    """
                    UPDATE webexp_tasks
                    SET time_taken_seconds = %s
                    WHERE task_id = %s
                    RETURNING task_id, user_id, task_number, time_taken_seconds;
                    """,
                    (task_update.time_taken_seconds, task_update.task_id)
                )
            elif task_update.user_id and task_update.task_number is not None:
                # Fallback: use user_id + task_number (backward compatible)
                await cur.execute(
                    """
                    UPDATE webexp_tasks
                    SET time_taken_seconds = %s
                    WHERE user_id = %s AND task_number = %s
                    RETURNING task_id, user_id, task_number, time_taken_seconds;
                    """,
                    (task_update.time_taken_seconds, task_update.user_id, task_update.task_number)
                )
            else:
                raise HTTPException(
                    status_code=400,
                    detail="Either (task_id + user_id + task_number) OR (user_id + task_number) must be provided"
                )
            
            updated = await cur.fetchone()
            if not updated:
                raise HTTPException(status_code=404, detail="Task not found")
            
            await conn.commit()
            return {
                "task_id": str(updated["task_id"]),
                "user_id": updated["user_id"],
                "task_number": updated["task_number"],
                "time_taken_seconds": updated["time_taken_seconds"]
            }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# ---- Expenditures ----
async def create_expenditure(exp: schema.WebExpExpenditureCreate, conn: AsyncConnection):
    exp_uuid = str(uuid.uuid4())
    try:
        async with conn.cursor() as cur:
            # First, find the task_id based on user_id and task_number
            await cur.execute(
                "SELECT task_id FROM webexp_tasks WHERE user_id = %s AND task_number = %s;",
                (exp.user_id, exp.task_number)
            )
            task_row = await cur.fetchone()
            if not task_row:
                raise HTTPException(status_code=404, detail="Task not found for given user_id and task_number")
            
            task_id = str(task_row["task_id"])
            
            await cur.execute(
                """
                INSERT INTO webexp_expenditure
                (uuid, task_id, name, date_of_expense, amount, category, notes, status)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING uuid;
                """,
                (
                    exp_uuid,
                    task_id,
                    exp.name,
                    exp.date_of_expense,
                    exp.amount,
                    exp.category,
                    exp.notes,
                    exp.status or "Pending"
                )
            )
            created = await cur.fetchone()
            await conn.commit()
            return {
                "uuid": str(created["uuid"]),
                "task_id": task_id,
                "name": exp.name,
                "date_of_expense": exp.date_of_expense,
                "amount": exp.amount,
                "category": exp.category,
                "notes": exp.notes,
                "status": exp.status or "Pending"
            }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


async def create_bulk_expenditures(
    expenditures: list[schema.WebExpExpenditureBulkItem], 
    task_id: str,
    user_id: str, 
    task_number: int,
    conn: AsyncConnection
):
    """
    Create multiple expenditures for a task in a single transaction.
    Requires task_id along with user_id and task_number for validation.
    """
    try:
        created_exps = []
        async with conn.cursor() as cur:
            # Validate that task_id matches user_id + task_number
            await cur.execute(
                """
                SELECT task_id FROM webexp_tasks 
                WHERE task_id = %s AND user_id = %s AND task_number = %s;
                """,
                (task_id, user_id, task_number)
            )
            validation = await cur.fetchone()
            if not validation:
                raise HTTPException(
                    status_code=404,
                    detail="Task not found or task_id does not match user_id and task_number"
                )
            
            # Now create all expenditures with the validated task_id
            for exp in expenditures:
                exp_uuid = str(uuid.uuid4())
                await cur.execute(
                    """
                    INSERT INTO webexp_expenditure
                    (uuid, task_id, name, date_of_expense, amount, category, notes, status)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    RETURNING uuid;
                    """,
                    (
                        exp_uuid,
                        task_id,
                        exp.name,
                        exp.date_of_expense,
                        exp.amount,
                        exp.category,
                        exp.notes,
                        exp.status or "Pending"
                    )
                )
                created = await cur.fetchone()
                created_exps.append({
                    "uuid": str(created["uuid"]),
                    "task_id": task_id,
                    "name": exp.name,
                    "date_of_expense": exp.date_of_expense,
                    "amount": exp.amount,
                    "category": exp.category,
                    "notes": exp.notes,
                    "status": exp.status or "Pending"
                })
            await conn.commit()
        return created_exps
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create bulk expenditures: {e}")
    


# --- Get a single user with all tasks and expenditures ---
async def get_user_with_tasks(user_id: str, conn: AsyncConnection):
    try:
        async with conn.cursor() as cur:
            # Fetch all tasks for this user
            await cur.execute(
                """
                SELECT task_id, user_id, task_number, time_taken_seconds
                FROM webexp_tasks
                WHERE user_id = %s
                """,
                (user_id,)
            )
            tasks = await cur.fetchall()
            if not tasks:
                raise HTTPException(status_code=404, detail="User not found")

            result_tasks = []
            for task in tasks:
                t_task_id = str(task["task_id"])
                t_user_id = task["user_id"]
                t_task_number = task["task_number"]
                t_time_taken = task["time_taken_seconds"]

                # Fetch expenditures for this task
                await cur.execute(
                    """
                    SELECT uuid, task_id, name, date_of_expense, amount, category, notes, status
                    FROM webexp_expenditure
                    WHERE task_id = %s
                    """,
                    (t_task_id,)
                )
                exp_rows = await cur.fetchall()
                expenditures = [
                    schema.WebExpExpenditure(
                        uuid=str(row["uuid"]),
                        task_id=str(row["task_id"]),
                        name=row["name"],
                        date_of_expense=row["date_of_expense"],
                        amount=float(row["amount"]),
                        category=row["category"],
                        notes=row["notes"],
                        status=row["status"]
                    )
                    for row in exp_rows
                ]

                result_tasks.append(
                    schema.WebExpTaskOut(
                        task_id=t_task_id,
                        user_id=t_user_id,
                        task_number=t_task_number,
                        time_taken_seconds=t_time_taken,
                        expenditures=expenditures
                    )
                )

            return schema.WebExpUserOut(
                user_id=user_id,
                tasks=result_tasks
            )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# --- Get all users filtered by task number ---
async def get_users_by_task(task_number: int, conn: AsyncConnection):
    try:
        async with conn.cursor() as cur:
            # Fetch all tasks with this task_number
            await cur.execute(
                """
                SELECT task_id, user_id, task_number, time_taken_seconds
                FROM webexp_tasks
                WHERE task_number = %s
                """,
                (task_number,)
            )
            tasks = await cur.fetchall()
            if not tasks:
                raise HTTPException(status_code=404, detail="No users found for this task")

            users_dict = {}

            for task in tasks:
                t_task_id = str(task["task_id"])
                t_user_id = task["user_id"]
                t_task_number = task["task_number"]
                t_time_taken = task["time_taken_seconds"]

                # Fetch expenditures for this task
                await cur.execute(
                    """
                    SELECT uuid, task_id, name, date_of_expense, amount, category, notes, status
                    FROM webexp_expenditure
                    WHERE task_id = %s
                    """,
                    (t_task_id,)
                )
                exp_rows = await cur.fetchall()
                expenditures = [
                    schema.WebExpExpenditure(
                        uuid=str(row["uuid"]),
                        task_id=str(row["task_id"]),
                        name=row["name"],
                        date_of_expense=row["date_of_expense"],
                        amount=float(row["amount"]),
                        category=row["category"],
                        notes=row["notes"],
                        status=row["status"]
                    )
                    for row in exp_rows
                ]

                task_out = schema.WebExpTaskOut(
                    task_id=t_task_id,
                    user_id=t_user_id,
                    task_number=t_task_number,
                    time_taken_seconds=t_time_taken,
                    expenditures=expenditures
                )

                if t_user_id not in users_dict:
                    users_dict[t_user_id] = schema.WebExpUserOut(user_id=t_user_id, tasks=[task_out])
                else:
                    users_dict[t_user_id].tasks.append(task_out)

            return list(users_dict.values())

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))