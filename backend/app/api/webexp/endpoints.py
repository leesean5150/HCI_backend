from fastapi import APIRouter, Depends, HTTPException, status, Query
from . import schema, handlers
from psycopg import AsyncConnection
from db.postgres import get_async_session
from typing import List, Optional

router = APIRouter()

# ---- Tasks (with auto user creation) ----
@router.post(
    "/tasks/",
    status_code=status.HTTP_201_CREATED,
    response_model=schema.WebExpTask,
    responses={
        status.HTTP_201_CREATED: {"description": "Task created successfully (user auto-created if needed)"},
        status.HTTP_400_BAD_REQUEST: {"description": "Bad request"},
        status.HTTP_500_INTERNAL_SERVER_ERROR: {"description": "Server error"},
    },
)
async def create_webexp_task(
    task: schema.WebExpTaskCreate,
    conn: AsyncConnection = Depends(get_async_session)
):
    """
    Create a task for a user.
    - If user_id exists: just insert the task
    - If user_id doesn't exist: create the user first, then insert the task
    """
    try:
        return await handlers.create_task(task, conn)
    except HTTPException as e:
        raise e
    except Exception:
        raise HTTPException(
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create task. Please try again later."
        )


@router.put(
    "/tasks/time/",
    status_code=status.HTTP_200_OK,
    response_model=schema.WebExpTask,
    responses={
        status.HTTP_200_OK: {"description": "Task time updated successfully"},
        status.HTTP_400_BAD_REQUEST: {"description": "Bad request"},
        status.HTTP_404_NOT_FOUND: {"description": "Task not found"},
        status.HTTP_500_INTERNAL_SERVER_ERROR: {"description": "Server error"},
    },
)
async def update_task_time_endpoint(
    task_update: schema.WebExpTaskUpdateTime,
    conn: AsyncConnection = Depends(get_async_session)
):
    """
    Update task time. Requires task_id along with user_id and task_number for validation.
    """
    try:
        return await handlers.update_task_time(task_update, conn)
    except HTTPException as e:
        raise e
    except Exception:
        raise HTTPException(
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update task time. Please try again later."
        )


# ---- Expenditures ----
@router.post(
    "/expenditures/",
    status_code=status.HTTP_201_CREATED,
    response_model=schema.WebExpExpenditure,
    responses={
        status.HTTP_201_CREATED: {"description": "Expenditure created successfully"},
        status.HTTP_400_BAD_REQUEST: {"description": "Bad request"},
        status.HTTP_500_INTERNAL_SERVER_ERROR: {"description": "Server error"},
    },
)
async def create_webexp_expenditure(
    exp: schema.WebExpExpenditureCreate,
    conn: AsyncConnection = Depends(get_async_session)
):
    try:
        return await handlers.create_expenditure(exp, conn)
    except HTTPException as e:
        raise e
    except Exception:
        raise HTTPException(
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create expenditure. Please try again later."
        )


@router.post(
    "/expenditures/bulk/",
    status_code=status.HTTP_201_CREATED,
    response_model=list[schema.WebExpExpenditure],
    responses={
        status.HTTP_201_CREATED: {"description": "Bulk expenditures created successfully"},
        status.HTTP_400_BAD_REQUEST: {"description": "Bad request"},
        status.HTTP_404_NOT_FOUND: {"description": "Task not found"},
        status.HTTP_500_INTERNAL_SERVER_ERROR: {"description": "Server error"},
    },
)
async def create_bulk_expenditures_endpoint(
    bulk: list[schema.WebExpExpenditureBulkItem],
    task_id: str = Query(..., description="Task ID"),
    user_id: str = Query(..., description="User ID"),
    task_number: int = Query(..., description="Task number"),
    conn: AsyncConnection = Depends(get_async_session)
):
    """
    Create multiple expenditures in one request.
    Requires task_id along with user_id and task_number for validation.
    """
    try:
        return await handlers.create_bulk_expenditures(bulk, task_id, user_id, task_number, conn)
    except HTTPException as e:
        raise e
    except Exception:
        raise HTTPException(
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create bulk expenditures. Please try again later."
        )


# --- Get a single user with tasks and expenditures ---
@router.get(
    "/users/{user_id}/",
    response_model=schema.WebExpUserOut,
    status_code=status.HTTP_200_OK,
    responses={
        404: {"description": "User not found"},
        500: {"description": "Server error"}
    }
)
async def get_user_endpoint(user_id: str, conn: AsyncConnection = Depends(get_async_session)):
    try:
        return await handlers.get_user_with_tasks(user_id, conn)
    except HTTPException as e:
        raise e


# --- Get all users filtered by task number ---
@router.get(
    "/tasks/{task_number}/users/",
    response_model=List[schema.WebExpUserOut],
    status_code=status.HTTP_200_OK,
    responses={
        404: {"description": "No users found for this task"},
        500: {"description": "Server error"}
    }
)
async def get_users_by_task_endpoint(task_number: int, conn: AsyncConnection = Depends(get_async_session)):
    try:
        return await handlers.get_users_by_task(task_number, conn)
    except HTTPException as e:
        raise e

@router.put(
    "/tasks/questions/",
    status_code=status.HTTP_200_OK,
    response_model=schema.WebExpTask,
    responses={
        status.HTTP_200_OK: {"description": "Questions updated successfully"},
        status.HTTP_400_BAD_REQUEST: {"description": "Bad request - questions must be 1-4"},
        status.HTTP_404_NOT_FOUND: {"description": "Task not found"},
        status.HTTP_500_INTERNAL_SERVER_ERROR: {"description": "Server error"},
    },
)
async def update_task_questions_endpoint(
    update: schema.WebExpTaskUpdateQuestions,
    conn: AsyncConnection = Depends(get_async_session)
):
    """
    Update question1 and question2 for a task.
    Both questions must be provided and must be between 1 and 4.
    Requires task_id along with user_id and task_number for validation.
    """
    try:
        return await handlers.update_task_questions(update, conn)
    except HTTPException as e:
        raise e
    except Exception:
        raise HTTPException(
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update questions. Please try again later."
        )


@router.get(
    "/health",
    status_code=200,
)
async def health_check():
    return {"status": "ok"}