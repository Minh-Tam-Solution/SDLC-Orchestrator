"""
Application Configuration Settings

Version: 1.0.0
Date: November 13, 2025
Status: ACTIVE - STAGE 03 (BUILD)
Authority: Backend Lead + DevOps Approved
Framework: SDLC 4.9 Complete Lifecycle

Loads settings from environment variables (.env file).
Uses Pydantic Settings for validation and type safety.
"""

import secrets
from typing import Optional

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.

    Environment Variables:
        # App
        - APP_NAME: Application name (default: "SDLC Orchestrator")
        - APP_VERSION: Application version (default: "1.0.0")
        - API_V1_PREFIX: API prefix (default: "/api/v1")
        - DEBUG: Debug mode (default: False)

        # Database
        - DATABASE_URL: PostgreSQL connection URL
        - DATABASE_POOL_SIZE: Connection pool size (default: 10)
        - DATABASE_MAX_OVERFLOW: Max overflow connections (default: 20)

        # Security
        - SECRET_KEY: JWT signing key (256-bit)
        - ACCESS_TOKEN_EXPIRE_HOURS: Access token expiry (default: 1)
        - REFRESH_TOKEN_EXPIRE_DAYS: Refresh token expiry (default: 30)

        # Redis
        - REDIS_URL: Redis connection URL (default: "redis://localhost:6379/0")

        # OAuth 2.0
        - GITHUB_CLIENT_ID: GitHub OAuth client ID
        - GITHUB_CLIENT_SECRET: GitHub OAuth client secret
        - GOOGLE_CLIENT_ID: Google OAuth client ID
        - GOOGLE_CLIENT_SECRET: Google OAuth client secret
        - MICROSOFT_CLIENT_ID: Microsoft OAuth client ID
        - MICROSOFT_CLIENT_SECRET: Microsoft OAuth client secret

        # CORS
        - ALLOWED_ORIGINS: Comma-separated list of allowed origins
    """

    # App
    APP_NAME: str = "SDLC Orchestrator"
    APP_VERSION: str = "1.0.0"
    API_V1_PREFIX: str = "/api/v1"
    DEBUG: bool = False

    # Database (PostgreSQL)
    DATABASE_URL: str = "postgresql+asyncpg://sdlc:sdlc@localhost:5432/sdlc_orchestrator"
    DATABASE_POOL_SIZE: int = 10
    DATABASE_MAX_OVERFLOW: int = 20

    # Security
    SECRET_KEY: str = secrets.token_urlsafe(32)  # Generate random key if not set
    ACCESS_TOKEN_EXPIRE_HOURS: int = 1
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"

    # OAuth 2.0 Providers
    GITHUB_CLIENT_ID: Optional[str] = None
    GITHUB_CLIENT_SECRET: Optional[str] = None
    GOOGLE_CLIENT_ID: Optional[str] = None
    GOOGLE_CLIENT_SECRET: Optional[str] = None
    MICROSOFT_CLIENT_ID: Optional[str] = None
    MICROSOFT_CLIENT_SECRET: Optional[str] = None

    # OAuth Redirect URLs
    OAUTH_REDIRECT_URL: str = "http://localhost:3000/auth/callback"

    # CORS
    ALLOWED_ORIGINS: str = "http://localhost:3000,http://localhost:8000"

    @property
    def allowed_origins_list(self) -> list[str]:
        """Parse ALLOWED_ORIGINS into list"""
        return [origin.strip() for origin in self.ALLOWED_ORIGINS.split(",")]

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
