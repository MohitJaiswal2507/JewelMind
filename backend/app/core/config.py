"""
Application Configuration Module
Centralized settings loaded from environment variables with validation.
"""

from typing import List, Union
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    PROJECT_NAME: str = "JewelMind API"
    VERSION: str = "0.1.0"
    DESCRIPTION: str = (
        "AI-Powered Jewellery Design, Analysis & Production Planning Platform API"
    )
    API_V1_STR: str = "/api/v1"
    
    # Environment & Logging
    APP_ENV: str = "development"  # development, testing, production
    DEBUG: bool = True
    LOG_LEVEL: str = "INFO"       # DEBUG, INFO, WARNING, ERROR, CRITICAL
    
    # CORS Configuration
    CORS_ORIGINS: Union[List[str], str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
    ]
    
    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> List[str]:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",") if i.strip()]
        elif isinstance(v, (list, str)):
            return v
        raise ValueError(v)
    
    # Database Configuration (PostgreSQL / Supabase)
    DATABASE_URL: str = "postgresql://postgres:postgres@localhost:5432/jewelmind"
    DB_ECHO_LOG: bool = False
    
    # Supabase Free Tier Storage & Auth (Placeholders for future phases)
    SUPABASE_URL: str = ""
    SUPABASE_ANON_KEY: str = ""
    SUPABASE_SERVICE_ROLE_KEY: str = ""
    SUPABASE_STORAGE_BUCKET: str = "jewelmind-assets"
    
    # AI Worker Configuration
    AI_WORKER_URL: str = "http://localhost:8001"
    AI_WORKER_TOKEN: str = "local-worker-secret-token"
    
    model_config = SettingsConfigDict(
        case_sensitive=True,
        env_file=".env",
        extra="ignore",
    )


settings = Settings()
