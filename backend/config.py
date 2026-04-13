from pydantic_settings import BaseSettings
from typing import Optional
import os


class Settings(BaseSettings):
    # App
    APP_NAME: str = "Adaptive AI Engine"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    SECRET_KEY: str = "change-me-in-production-use-strong-random-key"

    # Database
    DATABASE_URL: str = "sqlite+aiosqlite:///./adaptive_ai.db"
    POSTGRES_URL: Optional[str] = None

    # Redis (optional)
    REDIS_URL: Optional[str] = "redis://localhost:6379"
    REDIS_ENABLED: bool = False

    # Vector DB
    CHROMA_PERSIST_DIR: str = "./memory/chroma"
    CHROMA_ENABLED: bool = True

    # Memory
    MEMORY_BASE_PATH: str = "./memory"

    # AI Providers
    OPENAI_API_KEY: Optional[str] = None
    OPENAI_DEFAULT_MODEL: str = "gpt-4o"

    ANTHROPIC_API_KEY: Optional[str] = None
    ANTHROPIC_DEFAULT_MODEL: str = "claude-sonnet-4-6"

    GEMINI_API_KEY: Optional[str] = None
    GEMINI_DEFAULT_MODEL: str = "gemini-2.0-flash"

    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_DEFAULT_MODEL: str = "llama3.2"
    OLLAMA_ENABLED: bool = False

    # Orchestrator
    MAX_RETRIES: int = 3
    FEEDBACK_WINDOW: int = 10          # queries to collect before retraining weights
    MODEL_SELECTION_STRATEGY: str = "adaptive"  # adaptive | round-robin | cost-optimized

    # Security
    API_KEY_HEADER: str = "X-API-Key"
    RATE_LIMIT: str = "60/minute"
    CORS_ORIGINS: list[str] = ["http://localhost:3000", "http://localhost:5173"]
    MAX_PROMPT_LENGTH: int = 8000
    ENABLE_AUDIT_LOG: bool = True

    # Auth (JWT)
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 1440  # 24h

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()

# Ensure memory dirs exist
os.makedirs(settings.MEMORY_BASE_PATH, exist_ok=True)
os.makedirs(settings.CHROMA_PERSIST_DIR, exist_ok=True)
