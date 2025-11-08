from fastapi import APIRouter, Depends, HTTPException, status
from psycopg import AsyncConnection
from pydantic import EmailStr
import datetime as datetime

from db.postgres import get_async_session
from . import schema

UserModel = schema.UserModel


router = APIRouter()

######### OFFLINE MODE WITHOUT AUTHENTICATION ############
async def create_user(conn, user_data: UserModel):
    """
    create a new user in the database (offline mode, no authentication)
    """

    try:
        async with conn.cursor() as cur:
            # first we gotta check man whether the username already exists
            check_query = "SELECT COUNT(*) FROM users WHERE username = %s;"
            await cur.execute(check_query, (user_data.username,))
            result = await cur.fetchone()
            if result['count'] > 0:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Username already exists."
                )
            # if not, we can insert the new user
            insert_query = """
            INSERT INTO users (username, full_name)
            VALUES(%s, %s)
            RETURNING uuid, username, full_name, created, updated;
            """
            await cur.execute(
                insert_query,
                (
                    user_data.username,
                    user_data.full_name,
                )
            )
            new_user = await cur.fetchone()
            
            return new_user
            
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {str(e)}"
        )
        
######### ONLINE MODE WITH AUTHENTICATION (EMAIL & PASSWORD) ############
async def add_authentication_to_user(conn, auth_data: schema.AddAuthenticationRequest):
    """
    Add email and password to an existing offline user account
    (Upgrading from offline to online mode)
    """
    import bcrypt
    
    # Validate password length for bcrypt (max 72 bytes)
    password_bytes = auth_data.password.encode('utf-8')
    if len(password_bytes) > 72:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password cannot be longer than 72 bytes."
        )
    
    # Hash the password
    hashed_password = bcrypt.hashpw(password_bytes, bcrypt.gensalt()).decode('utf-8')
    
    try:
        async with conn.cursor() as cur:
            # Check if user exists
            check_user_query = "SELECT * FROM users WHERE username = %s"
            await cur.execute(check_user_query, (auth_data.username,))
            user = await cur.fetchone()
            
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="User not found."
                )
            
            # Check if user already has authentication
            if user['email'] or user['hashed_password']:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="User already has authentication enabled."
                )
            
            # Check if email is already used by another user
            check_email_query = "SELECT COUNT(*) FROM users WHERE email = %s"
            await cur.execute(check_email_query, (auth_data.email,))
            result = await cur.fetchone()
            if result['count'] > 0:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Email already in use."
                )
            
            # Update user with email and password
            update_query = """
            UPDATE users 
            SET email = %s, hashed_password = %s, updated = NOW()
            WHERE username = %s
            RETURNING uuid, username, full_name, email, created, updated;
            """
            await cur.execute(update_query, (auth_data.email, hashed_password, auth_data.username))
            updated_user = await cur.fetchone()
            
            if not updated_user:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to update user."
                )
            return {
                "uuid": updated_user['uuid'],
                "username": updated_user['username'],
                "full_name": updated_user['full_name'],
                "email": updated_user['email'],
                "created": updated_user['created'],
                "updated": updated_user['updated']
            }
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {str(e)}"
        )


async def get_user(conn, username: str):
    """
    get a user from the database
    """
    try:
        async with conn.cursor() as cur:
            query = """
            SELECT uuid, username, full_name, email, created, updated
            FROM users
            WHERE username = %s;
            """
            await cur.execute(query, (username,))
            user = await cur.fetchone()
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="User not found."
                )
            return user
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {str(e)}"
        )

async def update_user(conn, cur_username: str, update_data: schema.UserUpdateRequest):
    """
    update an existing user in the database
    """
    try:
        async with conn.cursor() as cur:
            check_query = "SELECT COUNT(*) FROM users WHERE username = %s;"
            await cur.execute(check_query, (cur_username,))
            result = await cur.fetchone()
            if result['count'] == 0: 
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="User not found."
                )
            
            if (update_data.username) and (update_data.username != cur_username):
                check_new_username_query = "SELECT COUNT(*) FROM users WHERE username = %s;"
                await cur.execute(check_new_username_query, (update_data.username,))
                result = await cur.fetchone()
                if result['count'] > 0:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="New username already exists."
                    )
            
            update_parts = []
            params = []
            
            if update_data.username:
                update_parts.append("username = %s")
                params.append(update_data.username)
            
            if update_data.full_name is not None:
                update_parts.append("full_name = %s")
                params.append(update_data.full_name)
            
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

async def delete_user(conn, username: str):
    """
    delete a user from the database
    """
    try:
        async with conn.cursor() as cur:
            delete_query = "DELETE FROM users WHERE username = %s RETURNING uuid;"
            await cur.execute(delete_query, (username,))
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