from pydantic import field_validator, PostgresDsn, Field
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional


class Settings(BaseSettings):
    """
    use pydantic settings for parsing environment file
    """
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    # For local running
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int 
    # For gcloud deployment
    # POSTGRES_HOST: Optional[str] = None
    # POSTGRES_PORT: Optional[int] = None
    POSTGRES_DB: str
    
    # JWT Settings for authentication
    JWT_SECRET_KEY: str  
    JWT_ALGORITHM: str 
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int 
    
    # DATABASE_URL: Optional[PostgresDsn] = None
    DATABASE_URL: Optional[str] = None
    # OPENAI_API: str
    # For webexp authentication - can be chosen by the person deploying
    WEBEXP_API_KEY: str
    # For gcloud deployment
    # CLOUD_SQL_CONNECTION_NAME:str

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra='ignore' 
    )

    @field_validator("DATABASE_URL", mode="before")
    @classmethod
    def assemble_db_url(cls, v: Optional[str], info) -> str:
        """Assembles the full DATABASE_URL from individual environment variables."""
        if isinstance(v, str):
            return v

        data = info.data

        #For gcloud deployment
        # Detect if running in Cloud Run with Cloud SQL
        # cloud_sql_instance = "talkcents-backend:asia-southeast1:my-postgres"
        # if cloud_sql_instance:
        #     return (
        #         f"user={data.get('POSTGRES_USER')} "
        #         f"password={data.get('POSTGRES_PASSWORD')} "
        #         f"dbname={data.get('POSTGRES_DB')} "
        #         f"host=/cloudsql/{cloud_sql_instance}"
        #     )
    
        port_str = str(data.get('POSTGRES_PORT'))

        return f"postgresql://{data.get('POSTGRES_USER')}:{data.get('POSTGRES_PASSWORD')}@{data.get('POSTGRES_HOST')}:{port_str}/{data.get('POSTGRES_DB')}"


settings = Settings()