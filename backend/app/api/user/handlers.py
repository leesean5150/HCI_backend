from fastapi import APIRouter, Depends, HTTPException, status
from psycopg import AsyncConnection
from pydantic import EmailStr
import datetime as datetime

from db.postgres import get_async_session
from app.auth import hash_password, verify_password, create_access_token
from . import schema

router = APIRouter()

######### HELPER FUNCTIONS CAUSE I FAKING TYPE THIS A FEW TIME ############
async def check_username_exists(cur, username: str) -> bool:
    """
    Check for existing username in the database, returns True if exists, False otherwise
    """
    check_query = "SELECT COUNT(*) FROM users WHERE username = %s;"
    await cur.execute(check_query, (username,))
    result = await cur.fetchone()
    return result['count'] > 0

async def check_email_exists(cur, email: str) -> bool:
    """
    Check to  see if email alreday exists in the database, returns True if exists, False otherwise
    """
    check_query = "SELECT COUNT(*) FROM users WHERE email = %s;"
    await cur.execute(check_query, (email,))
    result = await cur.fetchone()
    return result['count'] > 0

async def get_user_by_username(cur, username: str):
    """
    Fetch a user from the database by username
    Returns user dict or None if not found
    """
    query = """
    SELECT uuid, username, full_name, email, created, updated
    FROM users
    WHERE username = %s;
    """
    await cur.execute(query, (username,))
    return await cur.fetchone()


async def create_user(conn, user_data: schema.UserRegisterRequest):
    """
    create a new user in the database (offline mode, no authentication)
    """
    try:
        async with conn.cursor() as cur:
            if await check_username_exists(cur, user_data.username):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Username already exists."
                )
            
            if await check_email_exists(cur, user_data.email):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Email already exists."
                )
            
            hashed_password = hash_password(user_data.password)
            
            insert_query = """
            INSERT INTO users (username, full_name, email, hashed_password)
            VALUES(%s, %s, %s, %s)
            RETURNING uuid, username, full_name, email, created, updated;
            """
            await cur.execute(
                insert_query,
                (
                    user_data.username,
                    user_data.full_name,
                    user_data.email,
                    hashed_password,
                )
            )
            new_user = await cur.fetchone()
            
            return new_user
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {str(e)}"
        )
        
async def login_user(conn, login_data: schema.UserLoginRequest):
    """
    authenticate user and return JWT token
    """
    try:
        async with conn.cursor() as cur:
            query = """
            SELECT uuid, username, full_name, email, hashed_password, created, updated
            FROM users
            WHERE username = %s AND email IS NOT NULL AND hashed_password IS NOT NULL;
            """
            await cur.execute(query, (login_data.username,))
            user = await cur.fetchone()
            
            if not user or not verify_password(login_data.password, user['hashed_password']):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid username or password."
                )
            
            access_token = create_access_token(data={"sub": user['username']})
            
            user_response = schema.UserResponse(
                uuid=user['uuid'],
                username=user['username'],
                full_name=user['full_name'],
                email=user['email'],
                created=user['created'],
                updated=user['updated']
            )
            
            return schema.TokenResponse(
                access_token=access_token,
                token_type="bearer",
                user=user_response
            )
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {str(e)}"
        )

async def update_user(conn, current_user: dict, update_data: schema.UserUpdateRequest):
    """
    update an existing user in the database
    """
    try:
        async with conn.cursor() as cur:
            cur_username = current_user['username']
            
            
            if update_data.username and update_data.username != cur_username:
                if await check_username_exists(cur, update_data.username):
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="New username already exists."
                    )
            
            if update_data.email and update_data.email != current_user.get('email'):
                if await check_email_exists(cur, update_data.email):
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Email already in use."
                    )
            
            update_parts = []
            params = []
            
            if update_data.username:
                update_parts.append("username = %s")
                params.append(update_data.username)
            
            if update_data.full_name is not None:
                update_parts.append("full_name = %s")
                params.append(update_data.full_name)
            
            if update_data.email:
                update_parts.append("email = %s")
                params.append(update_data.email)
            
            if update_data.password:
                hashed_password = hash_password(update_data.password)
                update_parts.append("hashed_password = %s")
                params.append(hashed_password)
            
            if not update_parts:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="No fields to update."
                )
            
            update_parts.append("updated = NOW()")
            params.append(cur_username) 
            
            update_query = f"""
            UPDATE users
            SET {', '.join(update_parts)}
            WHERE username = %s
            RETURNING uuid, username, full_name, email, created, updated;
            """
            
            await cur.execute(update_query, params)
            updated_user = await cur.fetchone()
            
            return updated_user
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {str(e)}"
        )

async def delete_user(conn, current_user: dict):
    """
    delete the currently authenticated user from the database
    """
    try:
        async with conn.cursor() as cur:
            cur_username = current_user['username']
            
            delete_query = "DELETE FROM users WHERE username = %s RETURNING uuid;"
            await cur.execute(delete_query, (cur_username,))
            deleted_user = await cur.fetchone()
            
            if not deleted_user:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="User not found."
                )
            return {"message": "User deleted successfully.", "uuid": deleted_user['uuid']}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {str(e)}"
        )
        
async def get_current_user_profile(current_user: dict):
    """
    Retrieve the profile of the currently authenticated user
    """
    return schema.UserResponse(
        uuid=current_user['uuid'],
        username=current_user['username'],
        full_name=current_user['full_name'],
        email=current_user['email'],
        created=current_user['created'],
        updated=current_user['updated']
    )