"""
Configuration management for the LLM Decompose Tool
"""
from pydantic_settings import BaseSettings
from typing import Optional, List
import os


class Settings(BaseSettings):
    """Application settings"""

    # Application
    APP_NAME: str = "LLM Decompose Tool"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = False

    # Server
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    RELOAD: bool = False

    # CORS
    CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:5173"]

    # Database
    DATABASE_URL: str = "sqlite+aiosqlite:///./llm_tool.db"

    # Redis
    REDIS_URL: Optional[str] = None

    # LLM API Keys
    OPENAI_API_KEY: Optional[str] = None
    ANTHROPIC_API_KEY: Optional[str] = None
    GOOGLE_API_KEY: Optional[str] = None

    # LLM Settings
    DEFAULT_MODEL: str = "gpt-4-turbo-preview"
    MAX_TOKENS: int = 4096
    TEMPERATURE: float = 0.7

    # Tool Settings
    TOOL_TIMEOUT: int = 30  # seconds
    MAX_PARALLEL_TOOLS: int = 5

    # Session Settings
    MAX_PARALLEL_SESSIONS: int = 10
    SESSION_TIMEOUT: int = 3600  # seconds

    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FILE: Optional[str] = None

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


# Global settings instance
settings = Settings()
