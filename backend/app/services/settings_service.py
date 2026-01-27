"""
File: backend/app/services/settings_service.py
Version: 1.0.0
Status: ACTIVE - ADR-027 Phase 1 (Sprint N+1)
Date: 2026-01-14
Authority: BE Lead + CTO Approved
Foundation: SDLC 5.0.0 Complete Lifecycle, Zero Mock Policy
Ticket: SDLC-ADR027-000

Description:
System Settings Service - Runtime configuration from database with Redis caching.
Reads system_settings table and provides typed accessors for security settings.

ADR-027 Phase 1 Settings:
- session_timeout_minutes: JWT token expiry
- max_login_attempts: Account lockout threshold
- password_min_length: Password validation
- mfa_required: MFA enforcement flag

Performance:
- Cache TTL: 5 minutes (300 seconds)
- Cache hit: <5ms (Redis)
- Cache miss: <50ms (PostgreSQL query)

Zero Mock Policy: 100% real implementation with fallback to defaults
"""

import json
import logging
from datetime import timedelta
from typing import Any, Optional

from fastapi import Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings as app_settings
from app.db.session import get_db
from app.models.support import SystemSetting
from app.utils.redis import get_redis_client

logger = logging.getLogger(__name__)

# Cache configuration
SETTINGS_CACHE_PREFIX = "system_settings:"
SETTINGS_CACHE_TTL = 300  # 5 minutes


class SettingsService:
    """
    Service for reading and caching system settings from database.

    This service provides runtime-configurable settings that can be
    changed via the Admin Panel without restarting the application.

    Usage:
        settings_svc = SettingsService(db)

        # Get typed setting
        timeout = await settings_svc.get_session_timeout_minutes()
        max_attempts = await settings_svc.get_max_login_attempts()

        # Check feature flags
        if await settings_svc.is_ai_council_enabled():
            # Use AI Council
            pass

        # Get raw setting
        value = await settings_svc.get("custom_key", default="fallback")

    Caching:
        - Settings are cached in Redis for 5 minutes
        - Cache is invalidated when settings are updated via Admin API
        - Cache miss triggers database query with result cached
        - Fallback to defaults if Redis unavailable

    Performance:
        - Cache hit: <5ms (Redis lookup)
        - Cache miss: <50ms (PostgreSQL query + cache store)
        - No performance impact on API endpoints
    """

    def __init__(self, db: AsyncSession):
        """
        Initialize SettingsService.

        Args:
            db: AsyncSession for database queries
        """
        self.db = db
        self._redis = None

    async def _get_redis(self):
        """Get Redis client (lazy initialization)."""
        if self._redis is None:
            try:
                self._redis = await get_redis_client()
            except Exception as e:
                logger.warning(f"Redis unavailable: {e}")
                self._redis = None
        return self._redis

    # =========================================================================
    # Core Methods
    # =========================================================================

    async def get(
        self,
        key: str,
        default: Any = None,
        use_cache: bool = True,
    ) -> Any:
        """
        Get a setting value by key.

        Args:
            key: Setting key (e.g., 'session_timeout_minutes')
            default: Default value if setting not found
            use_cache: Whether to use Redis cache (default: True)

        Returns:
            Setting value (parsed from JSONB) or default

        Example:
            timeout = await settings.get("session_timeout_minutes", default=30)
        """
        # Try cache first
        if use_cache:
            cached = await self._get_from_cache(key)
            if cached is not None:
                logger.debug(f"Settings cache hit: {key}")
                return cached

        # Query database
        try:
            result = await self.db.execute(
                select(SystemSetting.value).where(SystemSetting.key == key)
            )
            row = result.scalar_one_or_none()

            if row is None:
                logger.debug(f"Setting '{key}' not found, using default: {default}")
                return default

            # Parse JSONB value
            value = self._parse_value(row)
            logger.debug(f"Setting '{key}' read from DB: {value}")

            # Cache the value
            if use_cache:
                await self._set_cache(key, value)

            return value

        except Exception as e:
            logger.error(f"Failed to read setting '{key}': {e}")
            return default

    async def get_all(self, category: Optional[str] = None) -> dict[str, Any]:
        """
        Get all settings, optionally filtered by category.

        Args:
            category: Optional category filter ('security', 'limits', 'features', 'notifications', 'general')

        Returns:
            Dict mapping setting keys to values

        Example:
            security_settings = await settings.get_all(category="security")
        """
        try:
            query = select(SystemSetting.key, SystemSetting.value)
            if category:
                query = query.where(SystemSetting.category == category)

            result = await self.db.execute(query)
            rows = result.all()

            return {
                row.key: self._parse_value(row.value)
                for row in rows
            }

        except Exception as e:
            logger.error(f"Failed to read settings (category={category}): {e}")
            return {}

    async def invalidate_cache(self, key: Optional[str] = None) -> None:
        """
        Invalidate settings cache.

        Args:
            key: Specific key to invalidate, or None for all settings

        Example:
            # Invalidate specific setting
            await settings.invalidate_cache("session_timeout_minutes")

            # Invalidate all settings
            await settings.invalidate_cache()
        """
        try:
            redis = await self._get_redis()
            if redis is None:
                return

            if key:
                cache_key = f"{SETTINGS_CACHE_PREFIX}{key}"
                await redis.delete(cache_key)
                logger.info(f"Invalidated cache for setting: {key}")
            else:
                # Invalidate all settings
                pattern = f"{SETTINGS_CACHE_PREFIX}*"
                cursor = 0
                deleted_count = 0

                while True:
                    cursor, keys = await redis.scan(
                        cursor=cursor,
                        match=pattern,
                        count=100
                    )
                    if keys:
                        await redis.delete(*keys)
                        deleted_count += len(keys)

                    if cursor == 0:
                        break

                logger.info(f"Invalidated {deleted_count} cached settings")

        except Exception as e:
            logger.warning(f"Failed to invalidate cache: {e}")

    # =========================================================================
    # Security Settings (ADR-027 Phase 1)
    # =========================================================================

    async def get_session_timeout_minutes(self) -> int:
        """
        Get session timeout in minutes.

        Returns:
            Session timeout value (default: 30 minutes)

        Note:
            This setting controls how long a user session remains valid.
            After this time, the user must re-authenticate.

        Used by: backend/app/core/security.py:create_access_token()
        """
        value = await self.get("session_timeout_minutes", default=30)
        try:
            return int(value)
        except (ValueError, TypeError):
            logger.warning(f"Invalid session_timeout_minutes value: {value}, using default 30")
            return 30

    async def get_max_login_attempts(self) -> int:
        """
        Get maximum failed login attempts before lockout.

        Returns:
            Max login attempts (default: 5)

        Note:
            After this many failed attempts, the account is temporarily
            locked for a cooldown period (30 minutes).

        Used by: backend/app/api/routes/auth.py:login()
        """
        value = await self.get("max_login_attempts", default=5)
        try:
            attempts = int(value)
            # Sanity check: at least 1, at most 100
            return max(1, min(attempts, 100))
        except (ValueError, TypeError):
            logger.warning(f"Invalid max_login_attempts value: {value}, using default 5")
            return 5

    async def is_mfa_required(self) -> bool:
        """
        Check if MFA is required for all users.

        Returns:
            True if MFA is mandatory, False otherwise

        Note:
            When enabled, users must set up MFA before accessing
            protected resources. 7-day grace period applies.

        Used by: backend/app/middleware/mfa_middleware.py
        """
        value = await self.get("mfa_required", default=False)
        return self._to_bool(value)

    async def get_password_min_length(self) -> int:
        """
        Get minimum password length requirement.

        Returns:
            Minimum password length (default: 8 characters)

        Note:
            This is enforced during password creation and reset.

        Used by: backend/app/schemas/admin.py, backend/app/schemas/auth.py
        """
        value = await self.get("password_min_length", default=8)
        try:
            length = int(value)
            # Sanity check: at least 8, at most 128
            return max(8, min(length, 128))
        except (ValueError, TypeError):
            logger.warning(f"Invalid password_min_length value: {value}, using default 8")
            return 8

    # =========================================================================
    # Limit Settings (Phase 2)
    # =========================================================================

    async def get_max_projects_per_user(self) -> int:
        """
        Get maximum projects allowed per user.

        Returns:
            Max projects limit (default: 50)

        Note:
            This limit applies to project owners only.
            Users can be members of unlimited projects.

        Used by: Phase 2 implementation (Sprint N+2)
        """
        value = await self.get("max_projects_per_user", default=50)
        try:
            return int(value)
        except (ValueError, TypeError):
            return 50

    async def get_max_file_size_mb(self) -> int:
        """
        Get maximum file upload size in MB.

        Returns:
            Max file size in MB (default: 100MB)

        Note:
            This applies to evidence uploads and attachments.

        Used by: Phase 2 implementation (Sprint N+2)
        """
        value = await self.get("max_file_size_mb", default=100)
        try:
            return int(value)
        except (ValueError, TypeError):
            return 100

    async def get_evidence_retention_days(self) -> int:
        """
        Get evidence retention period in days.

        Returns:
            Retention period in days (default: 365)

        Note:
            Evidence older than this may be archived or deleted
            based on compliance requirements.

        Used by: Phase 3 implementation (Sprint N+3)
        """
        value = await self.get("evidence_retention_days", default=365)
        try:
            return int(value)
        except (ValueError, TypeError):
            return 365

    # =========================================================================
    # Feature Flags
    # =========================================================================

    async def is_ai_council_enabled(self) -> bool:
        """
        Check if AI Council feature is enabled.

        Returns:
            True if AI Council is enabled, False otherwise

        Note:
            When enabled, compliance violations can be analyzed
            using multi-LLM deliberation (3-stage council).
            When disabled, only single-provider mode is used.

        Used by: backend/app/services/ai_council_service.py
        """
        value = await self.get("ai_council_enabled", default=True)
        return self._to_bool(value)

    # =========================================================================
    # AI Provider Configuration (ADR-007 + ADR-027)
    # =========================================================================

    async def get_ai_ollama_url(self) -> str:
        """
        Get Ollama server URL.

        Returns:
            Ollama URL (default: from env var or empty string)

        Note:
            Priority: Database setting > Environment variable > Empty
        """
        db_value = await self.get("ai_ollama_url", default="")
        if db_value:
            return str(db_value)
        return app_settings.OLLAMA_URL or ""

    async def get_ai_ollama_model(self) -> str:
        """
        Get default Ollama model.

        Returns:
            Model name (default: qwen3:14b)
        """
        db_value = await self.get("ai_ollama_model", default="")
        if db_value:
            return str(db_value)
        return app_settings.OLLAMA_MODEL

    async def get_ai_ollama_timeout(self) -> int:
        """
        Get Ollama request timeout.

        Returns:
            Timeout in seconds (default: 30)
        """
        value = await self.get("ai_ollama_timeout", default=30)
        try:
            return int(value)
        except (ValueError, TypeError):
            return 30

    async def get_ai_anthropic_api_key(self) -> str:
        """
        Get Anthropic API key for Claude.

        Returns:
            API key or empty string if not configured

        Note:
            Priority: Database setting > Environment variable
        """
        db_value = await self.get("ai_anthropic_api_key", default="")
        if db_value:
            return str(db_value)
        return app_settings.ANTHROPIC_API_KEY or ""

    async def get_ai_anthropic_model(self) -> str:
        """
        Get Claude model name.

        Returns:
            Model name (default: claude-sonnet-4-5-20250929)
        """
        value = await self.get("ai_anthropic_model", default="claude-sonnet-4-5-20250929")
        return str(value)

    async def get_ai_openai_api_key(self) -> str:
        """
        Get OpenAI API key.

        Returns:
            API key or empty string if not configured

        Note:
            Priority: Database setting > Environment variable
        """
        db_value = await self.get("ai_openai_api_key", default="")
        if db_value:
            return str(db_value)
        return app_settings.OPENAI_API_KEY or ""

    async def get_ai_openai_model(self) -> str:
        """
        Get OpenAI model name.

        Returns:
            Model name (default: gpt-4o)
        """
        value = await self.get("ai_openai_model", default="gpt-4o")
        return str(value)

    async def get_ai_default_provider(self) -> str:
        """
        Get default AI provider.

        Returns:
            Provider name: ollama, claude, or openai
        """
        value = await self.get("ai_default_provider", default="ollama")
        return str(value)

    async def is_ai_fallback_enabled(self) -> bool:
        """
        Check if AI provider fallback is enabled.

        Returns:
            True if fallback chain is enabled
        """
        value = await self.get("ai_fallback_enabled", default=True)
        return self._to_bool(value)

    async def get_ai_fallback_chain(self) -> list[str]:
        """
        Get AI provider fallback chain order.

        Returns:
            List of provider names in fallback order
        """
        value = await self.get("ai_fallback_chain", default=["ollama", "claude", "openai"])
        if isinstance(value, list):
            return value
        if isinstance(value, str):
            try:
                parsed = json.loads(value)
                if isinstance(parsed, list):
                    return parsed
            except json.JSONDecodeError:
                pass
        return ["ollama", "claude", "openai"]

    async def get_codegen_ollama_url(self) -> str:
        """
        Get Ollama URL for code generation.

        Returns:
            Codegen Ollama URL or main Ollama URL if not set
        """
        db_value = await self.get("codegen_ollama_url", default="")
        if db_value:
            return str(db_value)
        # Fallback to main Ollama URL or env var
        return await self.get_ai_ollama_url() or app_settings.CODEGEN_OLLAMA_URL or ""

    async def get_codegen_model_primary(self) -> str:
        """
        Get primary model for code generation.

        Returns:
            Model name (default: qwen3-coder:30b)
        """
        db_value = await self.get("codegen_model_primary", default="")
        if db_value:
            return str(db_value)
        return app_settings.CODEGEN_MODEL_PRIMARY

    async def get_codegen_model_fast(self) -> str:
        """
        Get fast model for quick drafts.

        Returns:
            Model name (default: qwen3:8b)
        """
        db_value = await self.get("codegen_model_fast", default="")
        if db_value:
            return str(db_value)
        return app_settings.CODEGEN_MODEL_FAST

    async def get_codegen_timeout(self) -> int:
        """
        Get codegen request timeout.

        Returns:
            Timeout in seconds (default: 120)
        """
        value = await self.get("codegen_timeout", default=120)
        try:
            return int(value)
        except (ValueError, TypeError):
            return 120

    async def get_ai_provider_config(self) -> dict[str, Any]:
        """
        Get AI provider configuration status.

        Returns:
            Dict with provider availability and settings

        Note:
            This is used by Admin Panel to show AI provider status.
            API keys are masked - only availability flags shown.

        Example:
            {
                "ollama": {"available": True, "url": "http://...", "model": "qwen3:14b"},
                "claude": {"available": True, "configured": True},
                "openai": {"available": False, "configured": False},
                "ai_council_enabled": True,
                "default_provider": "ollama",
                "fallback_enabled": True
            }
        """
        ollama_url = await self.get_ai_ollama_url()
        anthropic_key = await self.get_ai_anthropic_api_key()
        openai_key = await self.get_ai_openai_api_key()

        return {
            "ollama": {
                "available": bool(ollama_url),
                "url": ollama_url or "Not configured",
                "model": await self.get_ai_ollama_model(),
                "timeout": await self.get_ai_ollama_timeout(),
            },
            "claude": {
                "available": bool(anthropic_key),
                "configured": bool(anthropic_key),
                "model": await self.get_ai_anthropic_model(),
            },
            "openai": {
                "available": bool(openai_key),
                "configured": bool(openai_key),
                "model": await self.get_ai_openai_model(),
            },
            "codegen": {
                "url": await self.get_codegen_ollama_url() or "Uses main Ollama",
                "model_primary": await self.get_codegen_model_primary(),
                "model_fast": await self.get_codegen_model_fast(),
                "timeout": await self.get_codegen_timeout(),
            },
            "ai_council_enabled": await self.is_ai_council_enabled(),
            "default_provider": await self.get_ai_default_provider(),
            "fallback_enabled": await self.is_ai_fallback_enabled(),
            "fallback_chain": await self.get_ai_fallback_chain(),
        }

    # =========================================================================
    # Private Helper Methods
    # =========================================================================

    async def _get_from_cache(self, key: str) -> Optional[Any]:
        """Get setting from Redis cache."""
        try:
            redis = await self._get_redis()
            if redis is None:
                return None

            cache_key = f"{SETTINGS_CACHE_PREFIX}{key}"
            cached = await redis.get(cache_key)

            if cached:
                return json.loads(cached)
            return None

        except Exception as e:
            logger.warning(f"Cache read failed for {key}: {e}")
            return None

    async def _set_cache(self, key: str, value: Any) -> None:
        """Set setting in Redis cache."""
        try:
            redis = await self._get_redis()
            if redis is None:
                return

            cache_key = f"{SETTINGS_CACHE_PREFIX}{key}"
            await redis.setex(
                cache_key,
                SETTINGS_CACHE_TTL,
                json.dumps(value),
            )
            logger.debug(f"Cached setting: {key} (TTL={SETTINGS_CACHE_TTL}s)")

        except Exception as e:
            logger.warning(f"Cache write failed for {key}: {e}")

    def _parse_value(self, value: Any) -> Any:
        """
        Parse JSONB value from database.

        Handles various stored formats:
        - JSON strings ("30", "true", "false")
        - JSON objects ({"key": "value"})
        - JSON arrays ([1, 2, 3])
        - Raw values (already parsed)
        """
        if value is None:
            return None

        # If already parsed (dict, list, int, bool), return as-is
        if isinstance(value, (dict, list, int, float, bool)):
            return value

        # Try to parse as JSON string
        if isinstance(value, str):
            # Handle string booleans
            if value.lower() == "true":
                return True
            if value.lower() == "false":
                return False

            # Try numeric
            try:
                if "." in value:
                    return float(value)
                return int(value)
            except ValueError:
                pass

            # Try JSON parse
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                pass

        return value

    def _to_bool(self, value: Any) -> bool:
        """Convert value to boolean."""
        if isinstance(value, bool):
            return value
        if isinstance(value, str):
            return value.lower() in ("true", "1", "yes", "on")
        return bool(value)


# =========================================================================
# Factory Functions
# =========================================================================


def create_settings_service(db: AsyncSession) -> SettingsService:
    """
    Factory function to create SettingsService.

    Args:
        db: Database session

    Returns:
        SettingsService instance

    Example:
        settings = create_settings_service(db)
        timeout = await settings.get_session_timeout_minutes()
    """
    return SettingsService(db)


async def get_settings_service(
    db: AsyncSession = Depends(get_db),
) -> SettingsService:
    """
    Dependency injection helper for FastAPI.

    Usage in routes:
        from app.services.settings_service import get_settings_service

        @router.get("/example")
        async def example(
            settings: SettingsService = Depends(get_settings_service),
        ):
            timeout = await settings.get_session_timeout_minutes()
    """
    return SettingsService(db)
