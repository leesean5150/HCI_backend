from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from psycopg import AsyncConnection
from config import settings

from app.api.router import router

app = FastAPI(root_path="/api")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def on_startup():
    """
    on start up of the application, check for the existence of the files table and create it if it
    does no exist.
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
        name VARCHAR(255) NOT NULL,
        created_at TIMESTAMPTZ DEFAULT NOW(),
        date_of_expense DATE NOT NULL,
        amount NUMERIC(10, 2) NOT NULL,
        category VARCHAR(50),
        notes TEXT,
        status VARCHAR(20) DEFAULT 'Pending'
    );
    """
    try:
        conn = await AsyncConnection.connect(str(settings.DATABASE_URL), autocommit=True)
        async with conn.cursor() as cur:
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

def swagger_ui_parameters():
    return {
        "defaultModelsExpandDepth": 0,
        "displayRequestDuration": True,
        "filter": True,
        "tryItOutEnabled": True
    }

app.swagger_ui_parameters = swagger_ui_parameters()

app.include_router(router)