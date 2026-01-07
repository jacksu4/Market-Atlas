from functools import lru_cache
from typing import Optional

from pydantic import field_validator, ValidationError
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file="../.env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Application
    APP_NAME: str = "Market Atlas"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    API_V1_PREFIX: str = "/api/v1"

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/market_atlas"

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"

    # JWT Authentication
    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    @field_validator("JWT_SECRET_KEY")
    @classmethod
    def validate_jwt_secret(cls, v: str) -> str:
        # Prevent using insecure default values
        insecure_defaults = [
            "your-super-secret-jwt-key-change-in-production",
            "change-me",
            "secret",
            "jwt-secret",
        ]
        if v.lower() in [d.lower() for d in insecure_defaults]:
            raise ValueError(
                "JWT_SECRET_KEY cannot use default/example values. "
                "Please set a secure random secret key."
            )
        # Enforce minimum length of 32 characters
        if len(v) < 32:
            raise ValueError(
                "JWT_SECRET_KEY must be at least 32 characters long for security. "
                f"Current length: {len(v)}"
            )
        return v

    # External APIs
    ANTHROPIC_API_KEY: str = ""
    FINNHUB_API_KEY: str = ""
    POLYGON_API_KEY: str = ""
    FMP_API_KEY: str = ""

    # Telegram
    TELEGRAM_BOT_TOKEN: str = ""
    TELEGRAM_WEBHOOK_SECRET: str = ""
    TELEGRAM_BOT_USERNAME: str = "market_atlas_bot"

    # Google OAuth
    GOOGLE_CLIENT_ID: str = ""
    GOOGLE_CLIENT_SECRET: str = ""
    GOOGLE_REDIRECT_URI: str = "http://localhost:8000/api/v1/auth/google/callback"

    # AI Model Configuration
    CLAUDE_HAIKU_MODEL: str = "claude-3-5-haiku-20241022"
    CLAUDE_SONNET_MODEL: str = "claude-sonnet-4-20250514"

    # CORS
    BACKEND_URL: str = "http://localhost:8000"
    FRONTEND_URL: str = "http://localhost:3000"

    @property
    def cors_origins(self) -> list[str]:
        """
        Get CORS origins based on environment.
        In production, only use FRONTEND_URL.
        In development, also allow localhost:3000.
        """
        origins = [self.FRONTEND_URL]

        # Only add localhost in development
        if self.ENVIRONMENT == "development" and "localhost" not in self.FRONTEND_URL:
            origins.append("http://localhost:3000")

        return origins


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
