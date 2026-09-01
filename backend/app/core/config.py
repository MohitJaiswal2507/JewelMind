"""
Application Configuration Module
Centralized settings loaded from environment variables.
"""

from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    PROJECT_NAME: str = "JewelMind API"
    VERSION: str = "0.1.0"
    DESCRIPTION: str = (
        "AI-Powered Jewellery Design, Analysis & Production Planning Platform API"
    )
    API_V1_STR: str = "/api"
    
    # Environment
    APP_ENV: str = "development"
    DEBUG: bool = True
    
    # CORS
    CORS_ORIGINS: List[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
    ]
    
    # Database & Storage (Placeholders for future phases)
    DATABASE_URL: str = "postgresql://postgres:postgres@localhost:5432/jewelmind"
    SUPABASE_URL: str = ""
    SUPABASE_ANON_KEY: str = ""
    
    model_config = SettingsConfigDict(
        case_sensitive=True,
        env_file=".env",
        extra="ignore",
    )


settings = Settings()
