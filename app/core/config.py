"""Application configuration."""

from typing import List, Optional
from pydantic_settings import BaseSettings
from pydantic import ConfigDict


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

    # Security settings
    API_KEY: str = "your-api-key-here"  # Change in production
    SECRET_KEY: str = "your-secret-key-here-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    # Rate limiting
    RATE_LIMIT_PER_MINUTE: int = 100

    # Dropbox API settings
    DROPBOX_ACCESS_TOKEN: Optional[str] = None
    DROPBOX_FOLDER_PATH: str = "/PaperFlow"

    # Redis settings (for async job processing)
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    REDIS_PASSWORD: Optional[str] = None

    # Celery settings
    CELERY_BROKER_URL: str = "redis://localhost:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/0"

    # PDF generation settings
    PDF_PAGE_SIZE: str = "Letter"  # or custom dimensions for reMarkable
    PDF_MARGIN: str = "1in"
    PDF_FONT_SIZE: str = "12pt"
    PDF_LINE_HEIGHT: str = "1.6"

    # Storage settings
    TEMP_DIR: str = "/tmp/paperflow"
    MAX_CONTENT_LENGTH: int = 10 * 1024 * 1024  # 10MB

    model_config = ConfigDict(
        env_file=".env",
        case_sensitive=True
    )


settings = Settings()
