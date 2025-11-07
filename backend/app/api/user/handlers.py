from fastapi import APIRouter, Depends, HTTPException, status
from psycopg import AsyncConnection
from pydantic import EmailStr

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
            await conn.commit()
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
    from passlib.context import CryptContext
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    hashed_password = pwd_context.hash(auth_data.password)
    
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
            await conn.commit()
            
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


async def get_user(conn, user_data: UserModel):
    """
    get a user from the database
    """
    # Implementation goes here
    pass

async def update_user(conn, user_data: UserModel):
    """
    update an existing user in the database
    """
    # Implementation goes here
    pass

async def export_user_data(conn):
    """
    export user data from the database
    """
    # Implementation goes here
    pass