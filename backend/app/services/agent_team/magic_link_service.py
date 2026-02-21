"""
Magic Link OOB Authentication Service — Sprint 189 (ADR-064 D-064-04, FR-047).

Generates HMAC-SHA256 signed single-use tokens for gate approvals via chat.
When a chat user requests approval of a G3/G4 gate, the chat_command_router
generates a Magic Link URL instead of approving directly. The user clicks
the link in their browser (SSO-authenticated), which validates and consumes
the token atomically.

Token properties (STM-064 C1):
    - HMAC-SHA256 signed with MAGIC_LINK_SECRET (256-bit entropy)
    - Payload: gate_id + action + user_id + idempotency_key
    - TTL: 300 seconds (5 minutes) — reduces brute-force window
    - Single-use: Redis key deleted immediately after consumption
    - User-bound: token validation requires matching browser session user_id

Redis key pattern:
    magic_link:{signature} → JSON payload, TTL MAGIC_LINK_TTL_SECONDS

Security references:
    - ADR-064 D-064-04: HMAC-SHA256 tokens, 5-min expiry, single-use
    - STM-064 C1: Magic Link Token Guessing mitigation
    - STM-064 C4: OOB Auth Bypass mitigation
    - STM-064 C5: Gate Approval Race Condition mitigation
    - FR-047: Magic Link OOB Auth functional requirement
"""

from __future__ import annotations

import hashlib
import hmac
import json
import logging
import os
import uuid
from dataclasses import dataclass
from typing import Optional

from app.core.config import settings
from app.utils.redis import get_redis_client

logger = logging.getLogger(__name__)

# Redis key prefix for magic link tokens
_REDIS_PREFIX = "magic_link"


@dataclass(frozen=True)
class MagicLinkToken:
    """Represents a generated magic link token with its metadata."""

    signature: str
    gate_id: str
    action: str
    user_id: str
    idempotency_key: str
    ttl_seconds: int
    url: str


@dataclass(frozen=True)
class MagicLinkPayload:
    """Validated payload extracted from a consumed magic link token."""

    gate_id: str
    action: str
    user_id: str
    idempotency_key: str


class MagicLinkError(Exception):
    """Raised when magic link operations fail."""

    pass


class MagicLinkExpiredError(MagicLinkError):
    """Raised when a magic link token has expired (TTL exceeded)."""

    pass


class MagicLinkUsedError(MagicLinkError):
    """Raised when a magic link token has already been consumed."""

    pass


class MagicLinkInvalidError(MagicLinkError):
    """Raised when a magic link token signature is invalid."""

    pass


class MagicLinkUserMismatchError(MagicLinkError):
    """Raised when the browser session user does not match the token user."""

    pass


class MagicLinkService:
    """
    HMAC-SHA256 Magic Link token generation and validation.

    This service is ASYNC — uses async Redis client from app/utils/redis.py
    (ADR-064 A-02, T-05).

    Usage:
        service = MagicLinkService()

        # Generate token (in chat_command_router)
        token = await service.generate_token(
            gate_id="uuid-here",
            action="approve",
            user_id="user-uuid-here",
        )
        # Return token.url to chat user

        # Validate + consume token (in browser endpoint)
        payload = await service.validate_and_consume(
            signature=token.signature,
            browser_user_id="user-uuid-here",
        )
        # payload.gate_id, payload.action available for gate mutation
    """

    def __init__(
        self,
        secret: Optional[str] = None,
        ttl_seconds: Optional[int] = None,
        frontend_url: Optional[str] = None,
    ):
        """
        Initialize MagicLinkService.

        Args:
            secret: HMAC signing key (default: settings.MAGIC_LINK_SECRET)
            ttl_seconds: Token TTL in seconds (default: settings.MAGIC_LINK_TTL_SECONDS)
            frontend_url: Base URL for magic link browser page (default: settings.FRONTEND_URL)
        """
        self._secret = (secret or settings.MAGIC_LINK_SECRET).encode("utf-8")
        self._ttl = ttl_seconds or settings.MAGIC_LINK_TTL_SECONDS
        self._frontend_url = (frontend_url or settings.FRONTEND_URL).rstrip("/")

        # P1-2: Warn if MAGIC_LINK_SECRET is not explicitly set via env var.
        # Auto-generated secrets differ per worker process, breaking token
        # validation in multi-worker deployments (gunicorn -w N, k8s replicas).
        if not secret and not os.getenv("MAGIC_LINK_SECRET"):
            logger.warning(
                "magic_link: MAGIC_LINK_SECRET not set via env var — using "
                "auto-generated secret. Tokens will NOT be valid across workers. "
                "Set MAGIC_LINK_SECRET env var for production.",
            )

    def _compute_signature(
        self,
        gate_id: str,
        action: str,
        user_id: str,
        idempotency_key: str,
    ) -> str:
        """
        Compute HMAC-SHA256 signature binding gate_id + action + user_id + idempotency_key.

        The signature is URL-safe hex (64 chars) — used as Redis key and URL parameter.
        """
        message = f"{gate_id}:{action}:{user_id}:{idempotency_key}"
        return hmac.new(
            self._secret,
            message.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()

    async def generate_token(
        self,
        gate_id: str,
        action: str,
        user_id: str,
    ) -> MagicLinkToken:
        """
        Generate a single-use magic link token and store in Redis.

        Args:
            gate_id: UUID of the gate to approve/reject
            action: Gate action ("approve" or "reject")
            user_id: UUID of the requesting user (bound to token)

        Returns:
            MagicLinkToken with signature, URL, and metadata

        Raises:
            MagicLinkError: If Redis storage fails
        """
        idempotency_key = uuid.uuid4().hex

        signature = self._compute_signature(gate_id, action, user_id, idempotency_key)

        payload = {
            "gate_id": gate_id,
            "action": action,
            "user_id": user_id,
            "idempotency_key": idempotency_key,
        }

        redis = await get_redis_client()
        redis_key = f"{_REDIS_PREFIX}:{signature}"

        try:
            await redis.setex(redis_key, self._ttl, json.dumps(payload))
        except Exception as exc:
            logger.error("magic_link: Redis SET failed key=%s error=%s", redis_key, exc)
            raise MagicLinkError(f"Failed to store magic link token: {exc}") from exc

        url = f"{self._frontend_url}/auth/magic?token={signature}"

        logger.info(
            "magic_link: generated gate_id=%s action=%s user_id=%s ttl=%ds",
            gate_id,
            action,
            user_id,
            self._ttl,
        )

        return MagicLinkToken(
            signature=signature,
            gate_id=gate_id,
            action=action,
            user_id=user_id,
            idempotency_key=idempotency_key,
            ttl_seconds=self._ttl,
            url=url,
        )

    async def validate_and_consume(
        self,
        signature: str,
        browser_user_id: str,
    ) -> MagicLinkPayload:
        """
        Validate a magic link token and consume it atomically (single-use).

        This method performs atomic GET + DELETE to prevent race conditions
        (STM-064 C5). The first request succeeds; concurrent/subsequent
        requests receive MagicLinkUsedError.

        Args:
            signature: Token signature from URL parameter
            browser_user_id: User ID from browser SSO session (must match token user)

        Returns:
            MagicLinkPayload with gate_id, action, user_id, idempotency_key

        Raises:
            MagicLinkExpiredError: Token TTL exceeded or not found
            MagicLinkUsedError: Token already consumed
            MagicLinkInvalidError: Signature format invalid
            MagicLinkUserMismatchError: Browser user does not match token user
        """
        if not signature or len(signature) != 64:
            raise MagicLinkInvalidError("Invalid token signature format")

        redis = await get_redis_client()
        redis_key = f"{_REDIS_PREFIX}:{signature}"

        try:
            # Atomic GET + DELETE: consume the token in one operation.
            # GETDEL is atomic in Redis 6.2+ — no race condition possible.
            raw_payload = await redis.getdel(redis_key)
        except AttributeError:
            # Fallback for Redis < 6.2: use GET then DELETE (tiny race window)
            raw_payload = await redis.get(redis_key)
            if raw_payload:
                await redis.delete(redis_key)
        except Exception as exc:
            logger.error("magic_link: Redis GETDEL failed key=%s error=%s", redis_key, exc)
            raise MagicLinkError(f"Failed to validate magic link: {exc}") from exc

        if raw_payload is None:
            # Token not found — either expired (TTL) or already consumed
            logger.warning("magic_link: token not found (expired or used) signature=%s...", signature[:12])
            raise MagicLinkExpiredError("Magic link expired or already used")

        try:
            payload = json.loads(raw_payload)
        except (json.JSONDecodeError, TypeError) as exc:
            logger.error("magic_link: corrupt payload signature=%s... error=%s", signature[:12], exc)
            raise MagicLinkInvalidError("Corrupt token payload") from exc

        # User binding check (STM-064 C1): stolen token unusable by different user
        token_user_id = payload.get("user_id", "")
        if token_user_id != browser_user_id:
            logger.warning(
                "magic_link: user mismatch token_user=%s browser_user=%s",
                token_user_id,
                browser_user_id,
            )
            raise MagicLinkUserMismatchError(
                "Token was issued for a different user"
            )

        logger.info(
            "magic_link: consumed gate_id=%s action=%s user_id=%s",
            payload.get("gate_id"),
            payload.get("action"),
            token_user_id,
        )

        return MagicLinkPayload(
            gate_id=payload["gate_id"],
            action=payload["action"],
            user_id=payload["user_id"],
            idempotency_key=payload["idempotency_key"],
        )
