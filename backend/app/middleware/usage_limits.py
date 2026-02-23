"""
==========================================================================
UsageLimitsMiddleware — Sprint 188 Per-Resource Tier Enforcement
SDLC Orchestrator — Usage Gate Layer

Purpose:
- Enforce per-resource usage limits before route handlers execute
- Intercepts 4 mutation endpoints only (low overhead, targeted checks):
    POST /api/v1/projects               → project_count limit
    POST /api/v1/evidence/upload        → storage_mb limit
    POST /api/v1/gates                  → gates_this_month limit
    POST /api/v1/teams/members/invite   → team_members limit
- Returns HTTP 402 with structured upgrade CTA on limit exceeded

Architecture:
- Pure ASGI (NOT BaseHTTPMiddleware) — avoids FastAPI 0.100+ hang bug
  (Starlette BaseHTTPMiddleware event loop conflict on unhandled exceptions;
  see CLAUDE.md Module 1 Debugging section)
- JWT decoded from Authorization: Bearer <token> header
- User's effective_tier resolved from subscription model via DB query
  (same TIER_VALUES map as TierGateMiddleware for consistency)
- DB session opened only when path matches a watched endpoint (O(1) check)
- Fail-open: any JWT/DB error → pass through (route handler returns 401/500)

Middleware Stack Order (LIFO — last add_middleware() runs first):
    app.add_middleware(TierGateMiddleware)      ← blocks by route tier
    app.add_middleware(UsageLimitsMiddleware)   ← blocks by resource count (runs before TierGate)

Tier Limits Table (Sprint 188, ADR-059 Appendix B):
    lite:       1 project, 100 MB,  4 gates/month, 1 team member
    founder:    15 projects, 50GB, unlimited gates, 30 team members
    starter:    5 projects, 10GB,  unlimited gates, 10 team members
    standard:   15 projects, 50GB, unlimited gates, 30 team members
    pro:        20 projects, 100GB, unlimited gates, unlimited members
    enterprise: unlimited all dimensions

HTTP Code Semantics (ADR-059):
    401: no authentication (route handler / AuthMiddleware)
    402: tier limit exceeded (this middleware)
    403: wrong RBAC role/scope (route handler)

SDLC 6.1.0 — Sprint 188 P0 Deliverable
Authority: CTO + CPO Approved
==========================================================================
"""

import logging
import os
from typing import Any
from uuid import UUID

from jose import JWTError
from starlette.responses import JSONResponse
from starlette.types import ASGIApp, Receive, Scope, Send

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Tier limits — -1 means unlimited (no check performed)
# ---------------------------------------------------------------------------
TIER_LIMITS: dict[str, dict[str, int | float]] = {
    "lite": {
        "max_projects": 1,
        "max_storage_mb": 100,
        "max_gates_per_month": 4,
        "max_team_members": 1,
    },
    "founder": {
        "max_projects": 15,
        "max_storage_mb": 50_000,
        "max_gates_per_month": -1,
        "max_team_members": 30,
    },
    "starter": {
        "max_projects": 5,
        "max_storage_mb": 10_000,
        "max_gates_per_month": -1,
        "max_team_members": 10,
    },
    "standard": {
        "max_projects": 15,
        "max_storage_mb": 50_000,
        "max_gates_per_month": -1,
        "max_team_members": 30,
    },
    "pro": {
        "max_projects": 20,
        "max_storage_mb": 100_000,
        "max_gates_per_month": -1,
        "max_team_members": -1,
    },
    "enterprise": {
        "max_projects": -1,
        "max_storage_mb": -1,
        "max_gates_per_month": -1,
        "max_team_members": -1,
    },
}

# Free / unrecognised tiers fall back to LITE limits
_DEFAULT_TIER = "lite"

# ADR-065 D4: tier rank for max-tier resolution across org memberships
_TIER_RANK: dict[str, int] = {
    "lite": 1,
    "starter": 2,
    "standard": 2,
    "founder": 2,
    "pro": 3,
    "enterprise": 4,
}

# ---------------------------------------------------------------------------
# Watched endpoints: (HTTP method, exact path) → (limit_key, usage_method_name)
# ---------------------------------------------------------------------------
# Exact path matching is used (no prefix) because we only gate creation verbs
# on specific routes. Prefix matching would risk false positives on subpaths.
# ---------------------------------------------------------------------------
_WATCHED: dict[tuple[str, str], tuple[str, str]] = {
    ("POST", "/api/v1/projects"):               ("max_projects", "get_project_count"),
    ("POST", "/api/v1/evidence/upload"):         ("max_storage_mb", "get_storage_mb"),
    ("POST", "/api/v1/gates"):                   ("max_gates_per_month", "get_gates_this_month"),
    ("POST", "/api/v1/teams/members/invite"):    ("max_team_members", "get_team_members"),
}

# Human-readable limit type labels for 402 response body
_LIMIT_LABELS: dict[str, str] = {
    "max_projects": "project",
    "max_storage_mb": "storage",
    "max_gates_per_month": "gate",
    "max_team_members": "team_member",
}

# Upgrade CTA URL (Sprint 188: pricing page will be live)
UPGRADE_URL = os.getenv(
    "TIER_UPGRADE_URL",
    "https://app.sdlcorchestrator.com/pricing",
)

# Tier name → upgrade message fragment
_UPGRADE_MESSAGES: dict[str, dict[str, str]] = {
    "max_projects": {
        "lite": "LITE tier allows 1 project. Upgrade to STANDARD for up to 15 projects.",
        "starter": "STARTER tier allows 5 projects. Upgrade to STANDARD for up to 15 projects.",
        "standard": "STANDARD tier allows 15 projects. Upgrade to PRO for up to 20 projects.",
        "founder": "FOUNDER tier allows 15 projects. Upgrade to PRO for up to 20 projects.",
        "pro": "PRO tier allows 20 projects. Upgrade to ENTERPRISE for unlimited projects.",
        "_default": "You have reached the project limit for your plan. Upgrade to create more projects.",
    },
    "max_storage_mb": {
        "lite": "LITE tier allows 100 MB storage. Upgrade to STARTER for 10 GB.",
        "starter": "STARTER tier allows 10 GB storage. Upgrade to STANDARD for 50 GB.",
        "standard": "STANDARD tier allows 50 GB storage. Upgrade to PRO for 100 GB.",
        "founder": "FOUNDER tier allows 50 GB storage. Upgrade to PRO for 100 GB.",
        "pro": "PRO tier allows 100 GB storage. Upgrade to ENTERPRISE for unlimited storage.",
        "_default": "You have reached the storage limit for your plan. Upgrade to upload more evidence.",
    },
    "max_gates_per_month": {
        "lite": "LITE tier allows 4 gates per month. Upgrade to STANDARD for unlimited gates.",
        "_default": "You have reached the monthly gate limit for your plan. Upgrade to create more gates.",
    },
    "max_team_members": {
        "lite": "LITE tier allows 1 team member. Upgrade to STARTER for up to 10 members.",
        "starter": "STARTER tier allows 10 team members. Upgrade to STANDARD for up to 30 members.",
        "standard": "STANDARD tier allows 30 team members. Upgrade to PRO for unlimited members.",
        "founder": "FOUNDER tier allows 30 team members. Upgrade to PRO for unlimited members.",
        "_default": "You have reached the team member limit for your plan. Upgrade to invite more members.",
    },
}


def _get_upgrade_message(limit_key: str, tier: str) -> str:
    """Return the most specific upgrade message for the given limit and tier."""
    messages = _UPGRADE_MESSAGES.get(limit_key, {})
    return messages.get(tier, messages.get("_default", "Upgrade your plan to continue."))


class UsageLimitsMiddleware:
    """
    Pure ASGI per-resource usage limit middleware.

    Intercepts mutation requests on 4 specific endpoints and checks the
    current user's resource consumption against their tier limits.
    Returns HTTP 402 Payment Required with a structured body when exceeded.

    Fail-open design:
    - JWT missing / malformed → pass through (route returns 401)
    - DB error during usage query → log warning + pass through
    - Unknown tier → treated as LITE (most restrictive, safe default)

    Usage:
        app.add_middleware(UsageLimitsMiddleware)
        # Must be added AFTER TierGateMiddleware so it runs first (LIFO).
    """

    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        # Only intercept HTTP requests
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        method: str = scope.get("method", "").upper()
        path: str = scope.get("path", "")

        # Fast path: only watched (method, path) combinations need DB work
        watch_key = (method, path)
        if watch_key not in _WATCHED:
            await self.app(scope, receive, send)
            return

        limit_key, usage_method = _WATCHED[watch_key]

        # ----------------------------------------------------------------
        # 1. Extract user from JWT or API key (sdlc_live_*)
        # ----------------------------------------------------------------
        user_id: UUID | None = self._extract_user_id(scope)
        if user_id is None:
            user_id = await self._extract_user_id_from_api_key(scope)
        if user_id is None:
            # No valid auth — route handler will return 401; pass through
            await self.app(scope, receive, send)
            return

        # ----------------------------------------------------------------
        # 2. Resolve effective tier and limits
        # ----------------------------------------------------------------
        tier: str = await self._resolve_effective_tier(scope, user_id)
        limits = TIER_LIMITS.get(tier, TIER_LIMITS[_DEFAULT_TIER])
        max_value: int | float = limits[limit_key]

        # -1 = unlimited for this tier; skip the DB usage query entirely
        if max_value < 0:
            await self.app(scope, receive, send)
            return

        # ----------------------------------------------------------------
        # 3. Query current usage from the database
        # ----------------------------------------------------------------
        current_value: int | float | None = await self._fetch_usage(
            user_id=user_id,
            usage_method=usage_method,
        )
        if current_value is None:
            # DB error — fail open (logged inside _fetch_usage)
            await self.app(scope, receive, send)
            return

        # ----------------------------------------------------------------
        # 4. Enforce limit — reject with 402 if at or above the ceiling
        # ----------------------------------------------------------------
        if current_value >= max_value:
            label = _LIMIT_LABELS.get(limit_key, limit_key)
            message = _get_upgrade_message(limit_key, tier)

            body_dict = {
                "error": "usage_limit_exceeded",
                "limit_type": label,
                "current": current_value,
                "max": max_value,
                "tier": tier,
                "upgrade_url": UPGRADE_URL,
                "message": message,
            }

            logger.info(
                "UsageLimitsMiddleware: limit exceeded user=%s tier=%s "
                "limit_key=%s current=%s max=%s path=%s",
                user_id, tier, limit_key, current_value, max_value, path,
            )

            response = JSONResponse(status_code=402, content=body_dict)
            await response(scope, receive, send)
            return

        # Limit not exceeded — proceed to route handler
        await self.app(scope, receive, send)

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _extract_user_id(self, scope: Scope) -> UUID | None:
        """
        Decode JWT from Authorization: Bearer <token> header.

        Returns the user UUID from the 'sub' claim, or None on any failure
        (missing header, malformed token, expired token).  Failures are
        not errors — the downstream route handler enforces authentication.

        Args:
            scope: ASGI connection scope

        Returns:
            UUID of the authenticated user, or None.
        """
        from app.core.security import decode_token  # inline import for testability

        headers: dict[bytes, bytes] = dict(scope.get("headers", []))
        raw_auth: bytes = headers.get(b"authorization", b"")
        auth_str: str = raw_auth.decode("utf-8", errors="replace").strip()

        if not auth_str.lower().startswith("bearer "):
            return None

        token = auth_str[7:].strip()
        if not token:
            return None

        try:
            payload = decode_token(token)
            sub: str | None = payload.get("sub")
            if not sub:
                return None
            return UUID(sub)
        except (JWTError, ValueError, AttributeError) as exc:
            logger.debug("UsageLimitsMiddleware: JWT decode failed: %s", exc)
            return None

    async def _extract_user_id_from_api_key(self, scope: Scope) -> UUID | None:
        """Extract user UUID from API key (sdlc_live_*) via DB lookup."""
        headers: dict[bytes, bytes] = dict(scope.get("headers", []))
        raw_auth: bytes = headers.get(b"authorization", b"")
        auth_str: str = raw_auth.decode("utf-8", errors="replace").strip()

        if not auth_str.lower().startswith("bearer "):
            return None

        token = auth_str[7:].strip()
        if not token or not token.startswith("sdlc_live_"):
            return None

        try:
            from app.core.security import hash_api_key
            from app.db.session import AsyncSessionLocal

            key_hash = hash_api_key(token)

            async with AsyncSessionLocal() as db:
                from sqlalchemy import select as sa_select
                from app.models.user import APIKey

                result = await db.execute(
                    sa_select(APIKey.user_id).where(
                        APIKey.key_hash == key_hash,
                        APIKey.is_active == True,  # noqa: E712
                    )
                )
                return result.scalar_one_or_none()
        except Exception as exc:
            logger.debug(
                "UsageLimitsMiddleware: API key lookup failed: %s", exc,
            )
            return None

    async def _resolve_effective_tier(self, scope: Scope, user_id: UUID) -> str:
        """
        Determine the user's effective subscription tier.

        Priority (ADR-065 Unified Tier Resolution):
        1. scope["state"]["user_tier"] — optional fast path
        2. JWT decode → DB lookup:
           a. is_superuser / is_platform_admin → enterprise (ADR-065 D2)
           b. Organization-based max-tier (ADR-065 D1, ADR-047)
        3. Default to "lite" (most restrictive, safe fallback)

        The returned tier string is normalised to lowercase for TIER_LIMITS lookup.

        Args:
            scope:   ASGI connection scope
            user_id: Authenticated user UUID

        Returns:
            Lowercase tier name string.
        """
        # Priority 1: scope state (optional — populated if AuthMiddleware is added later)
        state: Any = scope.get("state", {})
        tier_from_state: str | None = None
        if hasattr(state, "__dict__"):
            tier_from_state = getattr(state, "user_tier", None)
        else:
            tier_from_state = state.get("user_tier")  # type: ignore[union-attr]

        if tier_from_state:
            normalised = tier_from_state.lower().strip()
            if normalised in TIER_LIMITS:
                return normalised
            return _normalise_tier(normalised)

        # Priority 2: DB lookup (ADR-065 — org-based resolution)
        try:
            from app.db.session import AsyncSessionLocal  # inline import for testability

            async with AsyncSessionLocal() as db:
                from sqlalchemy import select as sa_select

                # ADR-065 D2: superuser/platform_admin → enterprise (bypass all limits)
                from app.models.user import User
                user_result = await db.execute(
                    sa_select(User.is_superuser, User.is_platform_admin).where(User.id == user_id)
                )
                user_row = user_result.one_or_none()
                if user_row and (user_row[0] or user_row[1]):
                    return "enterprise"

                # ADR-065 D1: org-based tier resolution (replaces Subscription.plan)
                from app.models.organization import Organization, UserOrganization
                org_result = await db.execute(
                    sa_select(Organization.plan).where(
                        UserOrganization.user_id == user_id,
                        UserOrganization.organization_id == Organization.id,
                    )
                )
                org_plans = [r[0] for r in org_result.all() if r[0]]

            if org_plans:
                best_tier = _DEFAULT_TIER
                best_rank = 0
                for plan in org_plans:
                    normalised = _normalise_tier(plan.lower())
                    rank = _TIER_RANK.get(normalised, 0)
                    if rank > best_rank:
                        best_rank = rank
                        best_tier = normalised
                        if best_rank >= 4:
                            return best_tier  # enterprise — early exit
                return best_tier
        except Exception as exc:  # pragma: no cover — DB unavailable
            logger.warning(
                "UsageLimitsMiddleware: tier DB lookup failed for user=%s: %s",
                user_id, exc,
            )

        return _DEFAULT_TIER

    @staticmethod
    async def _fetch_usage(
        user_id: UUID,
        usage_method: str,
    ) -> int | float | None:
        """
        Call the appropriate UsageService method and return the current value.

        Opens its own AsyncSession (middleware cannot use FastAPI DI).
        Returns None on any DB error (caller treats None as fail-open).

        Args:
            user_id:      Authenticated user UUID
            usage_method: Name of the UsageService static method to call

        Returns:
            Current usage value (int or float) or None on failure.
        """
        from app.db.session import AsyncSessionLocal
        from app.services.usage_service import UsageService

        method = getattr(UsageService, usage_method, None)
        if method is None:  # programming error — should never happen
            logger.error("UsageLimitsMiddleware: unknown usage method %s", usage_method)
            return None

        try:
            async with AsyncSessionLocal() as db:
                value = await method(db, user_id)
            return value
        except Exception as exc:
            logger.warning(
                "UsageLimitsMiddleware: usage query failed user=%s method=%s: %s",
                user_id, usage_method, exc,
            )
            return None


# ---------------------------------------------------------------------------
# Module-level tier normalisation helper
# ---------------------------------------------------------------------------

def _normalise_tier(raw: str) -> str:
    """
    Map raw subscription plan strings to TIER_LIMITS keys.

    Handles legacy aliases (free → lite, professional → pro, etc.)

    Args:
        raw: Raw tier string (lowercased)

    Returns:
        Canonical TIER_LIMITS key, defaulting to "lite".
    """
    _ALIASES: dict[str, str] = {
        "free": "lite",
        "professional": "pro",
        # Canonical names map to themselves
        "lite": "lite",
        "founder": "founder",
        "starter": "starter",
        "standard": "standard",
        "pro": "pro",
        "enterprise": "enterprise",
    }
    return _ALIASES.get(raw, _DEFAULT_TIER)
