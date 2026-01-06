"""
Configuration management for the application.
"""

from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    """Application settings."""
    
    # API Settings
    API_TITLE: str = "Voice PDF Assistant API"
    API_VERSION: str = "1.0.0"
    API_PREFIX: str = "/api"
    
    # CORS Settings
    CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:3001"]
    
    # File Settings
    MAX_FILE_SIZE_MB: int = 50
    UPLOAD_CLEANUP_SECONDS: int = 3600  # 1 hour
    RESULT_CLEANUP_SECONDS: int = 1800  # 30 minutes
    
    # Server Settings
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    RELOAD: bool = True
    
    # Logging
    LOG_LEVEL: str = "INFO"
    
    class Config:
        env_file = ".env"
        case_sensitive = True


# Global settings instance
settings = Settings()
