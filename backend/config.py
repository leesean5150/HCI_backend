from pydantic import field_validator, PostgresDsn, Field
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional

class Settings(BaseSettings):
    """
    use pydantic settings for parsing environment file
    """
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int 
    POSTGRES_DB: str
    
    DATABASE_URL: Optional[PostgresDsn] = None
    # OPENAI_API: str

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
    
        port_str = str(data.get('POSTGRES_PORT'))

        return f"postgresql://{data.get('POSTGRES_USER')}:{data.get('POSTGRES_PASSWORD')}@{data.get('POSTGRES_HOST')}:{port_str}/{data.get('POSTGRES_DB')}"


settings = Settings()