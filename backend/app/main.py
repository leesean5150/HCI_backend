from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from psycopg import AsyncConnection
from openai import OpenAI

from app.api.router import router
from config import settings


app = FastAPI(root_path="/api")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def database_setup():
    """
    on start up of the application, check for the existence of the required tables and create it if it
    does not exist.
    """

    query = """
    SELECT EXISTS (
        SELECT 1
        FROM information_schema.tables 
        WHERE table_name = 'expenditure'
    );
    """
    create_table_query = """
    CREATE TABLE expenditure (
        uuid UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        user_uuid UUID NOT NULL REFERENCES users(uuid) ON DELETE CASCADE,
        name VARCHAR(255) NOT NULL,
        created_at TIMESTAMPTZ DEFAULT NOW(),
        date_of_expense DATE NOT NULL,
        amount NUMERIC(10, 2) NOT NULL,
        category VARCHAR(50),
        notes TEXT,
        status VARCHAR(20) DEFAULT 'Pending'
    );
    """
    query_user_table = """
    SELECT EXISTS (
        SELECT 1
        FROM information_schema.tables 
        WHERE table_name = 'users'
    );
    """
    create_user_table_query ="""
    CREATE TABLE users (
        uuid UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        username VARCHAR(150) NOT NULL,
        full_name VARCHAR(255),
        email VARCHAR(255),
        hashed_password VARCHAR(255),
        token_version INTEGER DEFAULT 1 NOT NULL,
        created TIMESTAMPTZ DEFAULT NOW(),
        updated TIMESTAMPTZ DEFAULT NOW(),

        CONSTRAINT users_username_key UNIQUE (username),
        CONSTRAINT users_email_key UNIQUE (email)
    );
    """
    
    check_token_version_column = """
    SELECT EXISTS (
        SELECT 1
        FROM information_schema.columns
        WHERE table_name = 'users' AND column_name = 'token_version'
    );
    """
    
    add_token_version_column = """
    ALTER TABLE users 
    ADD COLUMN token_version INTEGER DEFAULT 1 NOT NULL;
    """

    try:
        conn = await AsyncConnection.connect(str(settings.DATABASE_URL), autocommit=True)
        async with conn.cursor() as cur:

            await cur.execute(query_user_table)
            result = await cur.fetchone()
            if not result[0]:
                await cur.execute(create_user_table_query)
                await conn.commit()
                print("Table 'users' created.")
            else:
                print("Table 'users' already exists.")
                await cur.execute(check_token_version_column)
                has_token_version = await cur.fetchone()
                if not has_token_version[0]:
                    await cur.execute(add_token_version_column)
                    await conn.commit()
                    print("Column 'token_version' added to 'users' table.")
            

            await cur.execute(query)
            result = await cur.fetchone()
            if not result[0]:
                await cur.execute(create_table_query)
                await conn.commit()
                print("Table 'expenditure' created.")
            else:
                print("Table 'expenditure' already exists.")
                
        await conn.close()
    except Exception as e:
        print(f"Error checking or creating table: {e}")

@app.on_event("startup")
async def client_setup():
    """
    on start up of the application, initialize openai client
    """
    try:
        client = OpenAI()
        app.state.openai_client = client
        print("OpenAI client initialized and attached to app state: openai_client")
    except Exception as e:
        print(f"CRITICAL: Failed to initialize OpenAI client: {e}")

@app.on_event("shutdown")
async def shutdown_openai_client():
    if hasattr(app.state, 'openai_client'):
        del app.state.openai_client

def swagger_ui_parameters():
    return {
        "defaultModelsExpandDepth": 0,
        "displayRequestDuration": True,
        "filter": True,
        "tryItOutEnabled": True
    }

app.swagger_ui_parameters = swagger_ui_parameters()

app.include_router(router)