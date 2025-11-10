"""
JWT Authentication utilities for user authentication and authorization
"""
from datetime import datetime, timedelta, timezone
from typing import Optional
import jwt 
import bcrypt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from psycopg import AsyncConnection

from config import settings
from db.postgres import get_async_session

# Security scheme for Swagger UI
security_authorization = HTTPBearer()


def create_access_token(data: dict, expiry_time: Optional[timedelta] = None) -> str:
    """
    Create a JWT access token with expiration
    """
    to_encode = data.copy()
    
    # Add expiration time
    if expiry_time:
        expire = datetime.now(timezone.utc) + expiry_time
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    
    encoded_jwt = jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
    return encoded_jwt


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a plain password against its hashed version
    """
    return bcrypt.checkpw(
        plain_password.encode('utf-8'),
        hashed_password.encode('utf-8')
    )


def hash_password(password: str) -> str:
    """
    Hash a password using bcrypt
    """
    random_salt = bcrypt.gensalt()
    password_bytes = password.encode('utf-8')
    if len(password_bytes) > 72:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password cannot be longer than 72 bytes."
        )
    
    return bcrypt.hashpw(password_bytes, random_salt).decode('utf-8')


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security_authorization),
    conn: AsyncConnection = Depends(get_async_session)
):
    """
    Dependency to get the current authenticated user from JWT token
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        token = credentials.credentials
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM]
        )
        username: str = payload.get("sub")
        token_version: int = payload.get("token_version")
        
        if username is None:
            raise credentials_exception
            
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except jwt.JWTError:
        raise credentials_exception
    
    # Get user from database and verify token version
    try:
        async with conn.cursor() as cur:
            query = """
            SELECT uuid, username, full_name, email, token_version, created, updated
            FROM users
            WHERE username = %s AND email IS NOT NULL AND hashed_password IS NOT NULL;
            """
            await cur.execute(query, (username,))
            user = await cur.fetchone()
            
            if user is None:
                raise credentials_exception
            
            if token_version is not None and user.get('token_version') != token_version:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Token has been revoked. Please login again.",
                    headers={"WWW-Authenticate": "Bearer"},
                )
                
            return user
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {str(e)}"
        )
