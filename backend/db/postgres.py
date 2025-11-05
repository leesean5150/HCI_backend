from typing import AsyncGenerator
from psycopg import AsyncConnection
from psycopg.rows import dict_row
from config import settings


async def get_async_session() -> AsyncGenerator[AsyncConnection, None]:
    """
    open an asynchronous connection to the database and yield the connection for use in the endpoint.
    getter function ensures that the connection is properly closed after being used in the endpoint.
    """
    
    conn = await AsyncConnection.connect(
        conninfo=str(settings.DATABASE_URL),
        autocommit=True,
        row_factory=dict_row,
    )
    try:
        yield conn
    finally:
        await conn.close()