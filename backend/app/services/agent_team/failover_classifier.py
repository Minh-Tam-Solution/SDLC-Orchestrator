"""
FailoverError classification + Provider Profile Key + Abort Matrix.

Sources:
- OpenClaw: src/agents/failover-error.ts (6 FailoverReasons)
- OpenClaw: src/agents/model-fallback.ts (cooldown tracking)
- Nanobot N3: Error-as-string for LLM self-correction
- ADR-056 Decision 3: Provider Profile Key + Abort Matrix

CTO correction: 6 reasons (not 5) — 'unknown' is catch-all.

Sprint 177 Day 5 implementation.
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class FailoverReason(str, Enum):
    """6 classified error reasons — CTO verified against OpenClaw source."""

    AUTH = "auth"
    FORMAT = "format"
    RATE_LIMIT = "rate_limit"
    BILLING = "billing"
    TIMEOUT = "timeout"
    UNKNOWN = "unknown"


class FailoverAction(str, Enum):
    """What to do when a provider fails."""

    ABORT = "abort"
    FALLBACK = "fallback"
    RETRY = "retry"


# Abort vs Fallback Matrix (ADR-056 Decision 3)
ABORT_MATRIX: dict[FailoverReason, FailoverAction] = {
    FailoverReason.AUTH: FailoverAction.ABORT,
    FailoverReason.BILLING: FailoverAction.ABORT,
    FailoverReason.RATE_LIMIT: FailoverAction.FALLBACK,
    FailoverReason.TIMEOUT: FailoverAction.FALLBACK,
    FailoverReason.FORMAT: FailoverAction.RETRY,
    FailoverReason.UNKNOWN: FailoverAction.ABORT,
}

# Cooldown TTLs in seconds per reason (for Redis key expiry)
COOLDOWN_TTLS: dict[FailoverReason, int] = {
    FailoverReason.RATE_LIMIT: 60,
    FailoverReason.TIMEOUT: 120,
    FailoverReason.AUTH: 300,
    FailoverReason.BILLING: 600,
    FailoverReason.FORMAT: 0,  # No cooldown for format errors
    FailoverReason.UNKNOWN: 0,  # No cooldown for unknown errors
}

# Network error patterns (from OpenClaw src/agents/failover-error.ts)
_TIMEOUT_PATTERNS = re.compile(
    r"(timeout|timed out|deadline exceeded|ETIMEDOUT|ECONNRESET|ECONNREFUSED)",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class ProviderProfileKey:
    """
    Provider Profile Key: {provider}:{account}:{region}:{model_family}

    Examples:
      ollama:local:vietnam:qwen3-coder
      anthropic:team-alpha:us-east-1:claude-sonnet
      openai:default:global:gpt-4o
    """

    provider: str
    account: str
    region: str
    model_family: str

    def __str__(self) -> str:
        return f"{self.provider}:{self.account}:{self.region}:{self.model_family}"

    @classmethod
    def parse(cls, key_str: str) -> ProviderProfileKey:
        """Parse a provider profile key string."""
        parts = key_str.split(":")
        if len(parts) != 4:
            raise ValueError(
                f"Invalid provider profile key: {key_str!r}. "
                f"Expected format: provider:account:region:model_family"
            )
        return cls(
            provider=parts[0],
            account=parts[1],
            region=parts[2],
            model_family=parts[3],
        )

    @property
    def cooldown_redis_key(self) -> str:
        """Redis key for cooldown state."""
        return f"cooldown:{self}"


class FailoverClassifier:
    """
    Classifies provider errors into 6 FailoverReasons and routes to
    ABORT/FALLBACK/RETRY actions per the Abort Matrix (ADR-056 Decision 3).

    Error-as-String (Nanobot N3): For RETRY actions, returns error as
    structured content for LLM self-correction instead of raising exceptions.
    """

    @staticmethod
    def classify_http_error(status_code: int) -> FailoverReason:
        """Classify HTTP status codes into FailoverReasons."""
        if status_code in (401, 403):
            return FailoverReason.AUTH
        if status_code == 402:
            return FailoverReason.BILLING
        if status_code == 429:
            return FailoverReason.RATE_LIMIT
        if status_code in (408, 504):
            return FailoverReason.TIMEOUT
        if status_code == 400:
            return FailoverReason.FORMAT
        return FailoverReason.UNKNOWN

    @staticmethod
    def classify_exception(error: Exception) -> FailoverReason:
        """Classify Python exceptions into FailoverReasons."""
        error_msg = str(error)

        if _TIMEOUT_PATTERNS.search(error_msg):
            return FailoverReason.TIMEOUT

        if "unauthorized" in error_msg.lower() or "forbidden" in error_msg.lower():
            return FailoverReason.AUTH

        if "rate limit" in error_msg.lower() or "too many requests" in error_msg.lower():
            return FailoverReason.RATE_LIMIT

        if "billing" in error_msg.lower() or "payment" in error_msg.lower():
            return FailoverReason.BILLING

        if "invalid" in error_msg.lower() or "malformed" in error_msg.lower():
            return FailoverReason.FORMAT

        return FailoverReason.UNKNOWN

    @staticmethod
    def get_action(reason: FailoverReason) -> FailoverAction:
        """Get the action for a classified error reason."""
        return ABORT_MATRIX[reason]

    @staticmethod
    def get_cooldown_ttl(reason: FailoverReason) -> int:
        """Get cooldown TTL in seconds for a given reason."""
        return COOLDOWN_TTLS.get(reason, 0)

    @staticmethod
    def format_error_as_string(
        reason: FailoverReason,
        error: Exception | str,
        provider_key: ProviderProfileKey | None = None,
    ) -> str:
        """
        Format error as string content for LLM self-correction (Nanobot N3).

        For RETRY actions, this string is fed back into the conversation
        as a system message so the LLM can self-correct.
        """
        error_msg = str(error)
        provider_info = f" (provider: {provider_key})" if provider_key else ""
        return (
            f"Error [{reason.value}]{provider_info}: {error_msg}\n"
            f"Action: {ABORT_MATRIX[reason].value}"
        )

    def classify_and_route(
        self,
        error: Exception,
        provider_key: ProviderProfileKey | None = None,
        status_code: int | None = None,
    ) -> tuple[FailoverReason, FailoverAction, str]:
        """
        Full classification pipeline: classify error, determine action,
        format error string.

        Returns:
            (reason, action, error_string)
        """
        if status_code is not None:
            reason = self.classify_http_error(status_code)
        else:
            reason = self.classify_exception(error)

        action = self.get_action(reason)
        error_string = self.format_error_as_string(reason, error, provider_key)

        logger.info(
            "Failover classification: reason=%s action=%s provider=%s",
            reason.value,
            action.value,
            provider_key,
        )

        return reason, action, error_string
