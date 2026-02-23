"""
==========================================================================
ConversationFirstGuard — Sprint 190+195 (CEO Conversation-First Directive)
SDLC Orchestrator — Admin-Only Write Path Enforcement

Purpose:
- Enforce CEO's Conversation-First Interface Strategy
- Non-admin users: read-only access to web dashboard
- Write operations (POST/PUT/PATCH/DELETE) on admin-gated paths
  return 403 with "Use OTT or CLI" message for non-admin users
- Admin/Owner/Superuser users: full access (unchanged)

Architecture:
- Pure ASGI (NOT BaseHTTPMiddleware) — avoids FastAPI 0.100+ hang bug
- Extracts user_id from JWT Authorization header (same pattern as TierGateMiddleware)
- DB fallback: checks is_superuser, is_platform_admin, and org membership role
- Fail-open on JWT/DB errors (route-level guards handle auth)
- GET/HEAD/OPTIONS always pass through (read-only is fine)

Sprint 195 Fix (F-02 P0):
  Previous implementation relied on scope["state"]["user_role"] which was never
  populated by any middleware, making the guard a complete no-op. Fixed by adding
  JWT decode + DB lookup fallback (same defensive pattern as TierGateMiddleware).

CEO Directive (Feb 2026):
  "web app chủ yếu dùng cho admin hoặc owner,
   team member phần lớn thời gian sẽ là conversation-first qua OTT hoặc CLI"

SDLC 6.1.0 — Sprint 195 (P0 fix for Sprint 190 no-op)
Authority: CEO APPROVED, Expert Panel 9/9 APPROVE
Reference: SPRINT-190-AGGRESSIVE-CLEANUP.md, ADR-064
==========================================================================
"""

import json
import logging
import os
from uuid import UUID

from jose import JWTError
from starlette.types import ASGIApp, Receive, Scope, Send

logger = logging.getLogger(__name__)

# Admin-only write paths — POST/PUT/PATCH/DELETE require admin/owner role
# GET requests pass through (read-only dashboard access for all users)
ADMIN_WRITE_PATHS: set[str] = {
    "/api/v1/teams",
    "/api/v1/organizations",
    "/api/v1/admin",
    "/api/v1/tier-management",
    "/api/v1/enterprise/sso",
    "/api/v1/data-residency",
    "/api/v1/payments",
    "/api/v1/api-keys",
    # Sprint 192: Dashboard read-only enforcement for governance paths
    "/api/v1/gates",
    "/api/v1/evidence",
    "/api/v1/projects",
}

# Roles allowed to perform write operations on admin paths
# "admin"/"owner" = UserOrganization.role values
ADMIN_ROLES: set[str] = {"admin", "owner"}

# Methods that require admin role on gated paths
WRITE_METHODS: set[str] = {"POST", "PUT", "PATCH", "DELETE"}

# 403 response body
FORBIDDEN_RESPONSE = json.dumps({
    "detail": "Write access requires admin or owner role. Use OTT (Telegram/Zalo/Teams/Slack) or CLI (sdlcctl) for this action.",
    "error": "conversation_first_guard",
    "sprint": 190,
    "alternatives": {
        "ott": "Send commands via Telegram/Zalo/Teams/Slack",
        "cli": "sdlcctl <command> (see sdlcctl --help)",
    },
}).encode("utf-8")


class ConversationFirstGuard:
    """Pure ASGI middleware enforcing admin-only writes on dashboard paths.

    Sprint 195 fix: resolves user role via JWT + DB lookup instead of
    relying on scope["state"]["user_role"] which was never populated.
    """

    def __init__(self, app: ASGIApp) -> None:
        self.app = app
        self.enabled = os.getenv("CONVERSATION_FIRST_GUARD", "true").lower() in ("true", "1", "yes")

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http" or not self.enabled:
            await self.app(scope, receive, send)
            return

        method = scope.get("method", "GET")
        path = scope.get("path", "")

        # Only gate write methods
        if method not in WRITE_METHODS:
            await self.app(scope, receive, send)
            return

        # Check if path matches admin-gated prefixes
        is_admin_path = any(path.startswith(prefix) for prefix in ADMIN_WRITE_PATHS)
        if not is_admin_path:
            await self.app(scope, receive, send)
            return

        # Resolve whether user has admin/owner privileges
        is_admin = await self._resolve_is_admin(scope)

        if is_admin:
            await self.app(scope, receive, send)
            return

        # Non-admin user attempting write on admin path → 403
        logger.info("ConversationFirstGuard: blocked %s %s", method, path)

        response_headers = [
            (b"content-type", b"application/json"),
            (b"content-length", str(len(FORBIDDEN_RESPONSE)).encode()),
        ]

        await send({
            "type": "http.response.start",
            "status": 403,
            "headers": response_headers,
        })
        await send({
            "type": "http.response.body",
            "body": FORBIDDEN_RESPONSE,
        })

    # ------------------------------------------------------------------
    # Private helpers (same defensive pattern as TierGateMiddleware)
    # ------------------------------------------------------------------

    async def _resolve_is_admin(self, scope: Scope) -> bool:
        """Determine whether the requesting user has admin/owner privileges.

        Resolution order:
        1. scope["state"]["user_role"] — if populated by future AuthMiddleware
        2. JWT decode → DB lookup (is_superuser, is_platform_admin, org role)
        3. Fail-open on any error (True) — route-level auth handles denial

        Returns:
            True if admin/owner/superuser or on lookup failure (fail-open).
            False only when user is positively identified as non-admin.
        """
        # Priority 1: scope state (fast path for future AuthMiddleware)
        state = scope.get("state", {})
        if state:
            role_from_state = state.get("user_role") if isinstance(state, dict) else getattr(state, "user_role", None)
            if role_from_state is not None:
                return role_from_state in ADMIN_ROLES

        # Priority 2: JWT decode → user_id
        user_id = self._extract_user_id(scope)

        # Priority 2b: API key (sdlc_live_*) → user_id via DB lookup
        if user_id is None:
            user_id = await self._extract_user_id_from_api_key(scope)

        if user_id is None:
            # No auth token → unauthenticated request → fail-open (route returns 401)
            return True

        try:
            from app.db.session import AsyncSessionLocal

            async with AsyncSessionLocal() as db:
                from sqlalchemy import select as sa_select

                # Check superuser / platform_admin → always admin
                from app.models.user import User
                user_result = await db.execute(
                    sa_select(User.is_superuser, User.is_platform_admin).where(User.id == user_id)
                )
                row = user_result.one_or_none()
                if row is None:
                    return True  # user not found → fail-open
                if row[0] or row[1]:
                    return True  # superuser or platform_admin

                # Check org membership role
                from app.models.organization import UserOrganization
                org_result = await db.execute(
                    sa_select(UserOrganization.role).where(
                        UserOrganization.user_id == user_id
                    )
                )
                org_roles = {r[0] for r in org_result.all() if r[0]}
                if org_roles & ADMIN_ROLES:
                    return True  # admin or owner in at least one org

        except Exception as exc:
            logger.warning(
                "ConversationFirstGuard: DB lookup failed for user=%s: %s — fail-open",
                user_id, exc,
            )
            return True  # fail-open on DB error

        # Positively identified as non-admin member
        return False

    def _extract_user_id(self, scope: Scope) -> UUID | None:
        """Extract user UUID from JWT Authorization header (fail-silent)."""
        from app.core.security import decode_token

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
            logger.debug("ConversationFirstGuard: JWT decode failed: %s", exc)
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
                "ConversationFirstGuard: API key lookup failed: %s", exc,
            )
            return None
