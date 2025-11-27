"""Application configuration."""

from typing import List
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings."""

    PROJECT_NAME: str = "PaperFlow"
    VERSION: str = "0.1.0"
    DEBUG: bool = True

    # Server settings
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    # CORS settings
    ALLOWED_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:8000"]

    # Database settings (placeholder for future use)
    DATABASE_URL: str = "sqlite:///./paperflow.db"

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
