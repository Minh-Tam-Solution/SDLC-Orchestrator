"""
=========================================================================
Application Configuration Settings
SDLC Orchestrator - Stage 03 (BUILD)

Version: 1.0.0
Date: November 28, 2025
Status: ACTIVE - Week 3 Architecture Design
Authority: Backend Lead + DevOps + CTO Approved
Foundation: ADR-005 (Configuration Management), Twelve-Factor App
Framework: SDLC 4.9 Complete Lifecycle

Purpose:
- Environment-based configuration (dev, staging, prod)
- Secret management (environment variables)
- Database connection settings
- OAuth 2.0 provider configuration
- Security settings (JWT, token expiry)

Configuration Sources:
- Environment variables (.env file)
- Pydantic Settings (type validation)
- Default values (development-friendly)

Security:
- No secrets in code (environment variables only)
- Secret key rotation support (SECRET_KEY)
- Database credentials externalized

=========================================================================
"""

import secrets
from typing import Optional

from pydantic import model_validator
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

        # MinIO (S3-Compatible Storage)
        - MINIO_ENDPOINT: MinIO server endpoint (default: "minio:9000")
        - MINIO_ACCESS_KEY: MinIO access key (default: "minioadmin")
        - MINIO_SECRET_KEY: MinIO secret key (default: "minioadmin_changeme")
        - MINIO_BUCKET: Evidence vault bucket name (default: "evidence-vault")
        - MINIO_SECURE: Use HTTPS (default: False for local dev)

        # OPA (Open Policy Agent)
        - OPA_URL: OPA server URL (default: "http://opa:8181")

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
    # Port configurable via DATABASE_URL env var (default: 5432)
    DATABASE_URL: str = "postgresql+asyncpg://sdlc_user:changeme_secure_password@postgres:5432/sdlc_orchestrator"
    DATABASE_POOL_SIZE: int = 10
    DATABASE_MAX_OVERFLOW: int = 20

    # Security
    SECRET_KEY: str = secrets.token_urlsafe(32)  # Generate random key if not set
    ACCESS_TOKEN_EXPIRE_HOURS: int = 8  # 8 hours for development tools (VS Code Extension, CLI)
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30

    # Redis
    # Port configurable via REDIS_URL env var (default: 6379)
    REDIS_URL: str = "redis://redis:6379/0"

    # Team Invitation Rate Limiting (Sprint 128)
    MAX_INVITATIONS_PER_TEAM_PER_HOUR: int = 50  # Sliding window
    MAX_INVITATIONS_PER_EMAIL_PER_DAY: int = 3   # Prevent spam to same email
    MAX_INVITATION_RESENDS: int = 3              # Max resends per invitation
    INVITATION_RESEND_COOLDOWN_MINUTES: int = 5  # Cooldown between resends
    INVITATION_EXPIRY_DAYS: int = 7              # Invitation validity period

    # MinIO (S3-Compatible Storage)
    # Port configurable via MINIO_ENDPOINT env var (default: 9000)
    MINIO_ENDPOINT: str = "minio:9000"
    MINIO_PUBLIC_URL: str = "http://localhost:9010"  # Browser-accessible URL (mapped port)
    MINIO_ACCESS_KEY: str = "minioadmin"
    MINIO_SECRET_KEY: str = "minioadmin_changeme"
    MINIO_BUCKET: str = "evidence-vault-v2"  # Sprint 82: Object Lock enabled (GOVERNANCE, 7 years)
    MINIO_SECURE: bool = False  # Use HTTPS (False for local dev)

    # MinIO Object Lock Configuration (Sprint 82 - Pre-Launch Hardening)
    # Configured: January 22, 2026 - P1 Task (Deadline: Jan 25, 2026)
    # WORM Compliance: SEC 17a-4, FINRA 4511, GDPR Article 5(1)(e)
    MINIO_OBJECT_LOCK_ENABLED: bool = True  # Object Lock (WORM) enabled
    MINIO_RETENTION_DAYS: int = 2555  # 7 years retention (2555 days)
    MINIO_RETENTION_MODE: str = "GOVERNANCE"  # GOVERNANCE allows privileged delete, COMPLIANCE never deletable

    # OPA (Open Policy Agent)
    # Port configurable via OPA_URL env var (default: 8181)
    OPA_URL: str = "http://opa:8181"

    # OAuth 2.0 Providers
    GITHUB_CLIENT_ID: Optional[str] = None
    GITHUB_CLIENT_SECRET: Optional[str] = None
    GITHUB_WEBHOOK_SECRET: Optional[str] = None  # For webhook signature validation

    # GitHub App (Sprint 81 - Check Runs API)
    # Required for creating Check Runs - OAuth tokens cannot create Check Runs
    # See: ADR-029, SPRINT-81-DESIGN-REVIEW.md
    GITHUB_APP_ID: Optional[str] = None  # GitHub App ID (numeric string)
    GITHUB_APP_PRIVATE_KEY: Optional[str] = None  # PEM private key (base64 encoded or raw)
    GITHUB_APP_WEBHOOK_SECRET: Optional[str] = None  # Webhook secret for App events

    # Evidence Manifest (Sprint 82 - Hash Chain)
    # Secret key for HMAC-SHA256 signing of manifests
    # CRITICAL: Must be set in production, rotated every 90 days via Vault
    # See: SPRINT-82-HARDENING-EVIDENCE.md, Pre-Launch Hardening Plan
    EVIDENCE_MANIFEST_SECRET_KEY: str = secrets.token_urlsafe(32)  # Auto-generate if not set
    EVIDENCE_RETENTION_DAYS: int = 2555  # ~7 years for GDPR compliance

    GOOGLE_CLIENT_ID: Optional[str] = None
    GOOGLE_CLIENT_SECRET: Optional[str] = None
    MICROSOFT_CLIENT_ID: Optional[str] = None
    MICROSOFT_CLIENT_SECRET: Optional[str] = None

    # OAuth Redirect URLs (configurable via env vars)
    OAUTH_REDIRECT_URL: str = "http://localhost:3000/auth/callback"
    GITHUB_OAUTH_REDIRECT_URL: str = "http://localhost:3000/auth/github/callback"

    # Frontend URL (for links in GitHub status checks, emails, etc.)
    FRONTEND_URL: str = "http://localhost:3000"

    # CORS (configurable via ALLOWED_ORIGINS env var)
    ALLOWED_ORIGINS: str = "http://localhost:3000,http://localhost:4000,http://localhost:5173,http://localhost:8000"

    # SMTP Email Settings (Sprint 21 - Notifications)
    SMTP_HOST: Optional[str] = None
    SMTP_PORT: int = 587
    SMTP_USER: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    SMTP_USE_TLS: bool = True
    SMTP_FROM_EMAIL: str = "noreply@sdlc-orchestrator.com"
    SMTP_FROM_NAME: str = "SDLC Orchestrator"

    # Slack Webhook (Sprint 21 - Notifications)
    SLACK_WEBHOOK_URL: Optional[str] = None

    # Microsoft Teams Webhook (Sprint 21 - Notifications)
    TEAMS_WEBHOOK_URL: Optional[str] = None

    # Ollama AI (Sprint 21 - Local LLM Integration)
    # ADR-007: Cost optimization - $50/month vs $1,000/month cloud APIs
    # EP-06: Company GPU server for Mode B (Native OSS Codegen)
    # Ollama AI Service (set via OLLAMA_URL env var)
    OLLAMA_URL: str = ""  # Must be set via environment variable
    OLLAMA_MODEL: str = "qwen3:14b"  # Model Strategy v3.0 - Vietnamese excellent
    OLLAMA_TIMEOUT: int = 30
    
    # EP-06 Codegen Engine - OSS Model Configuration
    # Mode B: Native OSS codegen using NQH AI Platform (IT Admin infrastructure)
    # RTX 5090 32GB with 10 production models - December 2025
    # Updated: Dec 24, 2025 - qwen3-coder:30b replaces qwen2.5-coder:32b (1.8x faster, 256K context)
    # Docs: /home/nqh/shared/models/core/docs/admin/MODEL_LINEUP_STRATEGY.md
    #
    # NOTE: Set via CODEGEN_OLLAMA_URL env var based on deployment environment
    CODEGEN_OLLAMA_URL: str = ""  # Must be set via environment variable
    CODEGEN_MODEL_PRIMARY: str = "qwen3-coder:30b"  # NEW: 1.8x faster (14.5s vs 26.7s), 256K context, 18GB
    CODEGEN_MODEL_FAST: str = "qwen3:8b"  # Fast draft (<3s)
    CODEGEN_MODEL_VIETNAMESE: str = "qwen3:14b"  # Excellent Vietnamese support
    CODEGEN_MODEL_CHAT: str = "mistral-small3.2:24b-instruct-2506-q4_K_M"  # Enterprise assistant, JSON output
    CODEGEN_MODEL_ULTRAFAST: str = "qwen3:8b"  # Quick drafts (<3s)
    CODEGEN_TIMEOUT: int = 120  # Longer timeout for code generation

    # Analytics (Sprint 41 - AI Safety Foundation)
    MIXPANEL_TOKEN: Optional[str] = None  # Mixpanel project token (get from https://mixpanel.com/settings/project)
    ANALYTICS_USER_SALT: str = secrets.token_urlsafe(32)  # Salt for hashing user IDs (GDPR privacy)
    ANALYTICS_RETENTION_DAYS: int = 90  # Retention period for analytics_events table
    ANALYTICS_CIRCUIT_BREAKER_THRESHOLD: int = 5  # Max failures before circuit opens
    ANALYTICS_CIRCUIT_BREAKER_TIMEOUT: int = 300  # Circuit breaker timeout in seconds (5 min)
    
    # EP-06 Model Roles (aligned with Continue.dev config - IT Admin Dec 2025)
    # Role mapping for different task types (Updated Dec 24, 2025)
    # default/edit: qwen3-coder:30b - PRIMARY code (1.8x faster, 256K context)
    # chat: mistral-small3.2:24b - Enterprise assistant, JSON output
    # autocomplete: qwen3:8b - Fast tab completion (<3s)
    # vietnamese: qwen3:14b - Vietnamese RAG with citations
    # See: MODEL_LINEUP_STRATEGY.md for full details

    # Cloud AI Fallback (when Ollama unavailable)
    ANTHROPIC_API_KEY: Optional[str] = None
    OPENAI_API_KEY: Optional[str] = None

    # Session Checkpoint Configuration (Sprint 51B)
    # See: docs/02-design/14-Technical-Specs/Session-Checkpoint-Design.md
    REDIS_CHECKPOINT_TTL: int = 86400  # 24 hours for active sessions
    CHECKPOINT_INTERVAL: int = 3  # Save checkpoint every N files
    CHECKPOINT_COMPLETED_TTL: int = 604800  # 7 days for completed sessions

    # VNPay Payment Gateway (Sprint 58)
    # See: Plan v2.2 Section 7 - VNPay Integration
    # Get credentials from VNPay merchant portal
    VNPAY_TMN_CODE: Optional[str] = None  # Merchant terminal code
    VNPAY_HASH_SECRET: Optional[str] = None  # Hash secret for signing
    VNPAY_URL: str = "https://sandbox.vnpayment.vn/paymentv2/vpcpay.html"  # Sandbox URL
    VNPAY_RETURN_URL: str = "http://localhost:3000/checkout/success"  # Return URL after payment

    # Cookie Authentication (Sprint 63)
    # See: docs/04-build/02-Sprint-Plans/SPRINT-63-DEFINITION-OF-DONE.md
    # httpOnly cookies for XSS protection (OWASP ASVS Level 2)
    COOKIE_DOMAIN: Optional[str] = None  # None for localhost, "sdlc.nhatquangholding.com" for prod
    COOKIE_SECURE: bool = True  # HTTPS only (set to False for local dev if needed)
    COOKIE_SAMESITE: str = "lax"  # Allow OAuth redirects, block CSRF
    COOKIE_ACCESS_TOKEN_MAX_AGE: int = 900  # 15 minutes (seconds)
    COOKIE_REFRESH_TOKEN_MAX_AGE: int = 604800  # 7 days (seconds)

    @property
    def allowed_origins_list(self) -> list[str]:
        """Parse ALLOWED_ORIGINS into list"""
        return [origin.strip() for origin in self.ALLOWED_ORIGINS.split(",")]

    @property
    def ACCESS_TOKEN_EXPIRE_MINUTES(self) -> int:
        """Access token expiry in minutes"""
        return self.ACCESS_TOKEN_EXPIRE_HOURS * 60

    @property
    def REFRESH_TOKEN_EXPIRE_TIMEDELTA(self):
        """Refresh token expiry as timedelta"""
        from datetime import timedelta
        return timedelta(days=self.REFRESH_TOKEN_EXPIRE_DAYS)

    @model_validator(mode='after')
    def validate_secret_key(self):
        """
        P2 Security Fix (Sprint 33 Day 1): Validate SECRET_KEY strength.

        Requirements:
        - Minimum 32 characters in production
        - Fails fast if weak key detected

        Raises:
            ValueError: If SECRET_KEY is too short in production
        """
        if not self.DEBUG and len(self.SECRET_KEY) < 32:
            raise ValueError(
                f"SECRET_KEY must be at least 32 characters in production. "
                f"Current length: {len(self.SECRET_KEY)}. "
                f"Generate a secure key with: "
                f"python -c 'import secrets; print(secrets.token_urlsafe(32))'"
            )
        return self

    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "ignore"


settings = Settings()


def get_settings() -> Settings:
    """
    Get application settings instance.

    Returns:
        Settings: Application settings singleton
    """
    return settings
