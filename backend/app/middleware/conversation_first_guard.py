"""
==========================================================================
ConversationFirstGuard — Sprint 190 (CEO Conversation-First Directive)
SDLC Orchestrator — Admin-Only Write Path Enforcement

Purpose:
- Enforce CEO's Conversation-First Interface Strategy
- Non-admin users: read-only access to web dashboard
- Write operations (POST/PUT/PATCH/DELETE) on admin-gated paths
  return 403 with "Use OTT or CLI" message for non-admin users
- Admin/Owner users: full access (unchanged)

Architecture:
- Pure ASGI (NOT BaseHTTPMiddleware) — avoids FastAPI 0.100+ hang bug
- Reads user role from JWT claims in Authorization header
- Fail-open: if role lookup fails, pass through (route-level guards handle auth)
- GET/HEAD/OPTIONS always pass through (read-only is fine)

CEO Directive (Feb 2026):
  "web app chủ yếu dùng cho admin hoặc owner,
   team member phần lớn thời gian sẽ là conversation-first qua OTT hoặc CLI"

SDLC 6.1.0 — Sprint 190 Day 5
Authority: CEO APPROVED, Expert Panel 9/9 APPROVE
Reference: SPRINT-190-AGGRESSIVE-CLEANUP.md, ADR-064
==========================================================================
"""

import json
import logging
import os

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
    """Pure ASGI middleware enforcing admin-only writes on dashboard paths."""

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

        # Extract user role from scope state (set by auth middleware)
        user_role = None
        state = scope.get("state", {})
        if state:
            user_role = state.get("user_role")

        # If role found and is admin/owner, pass through
        if user_role and user_role in ADMIN_ROLES:
            await self.app(scope, receive, send)
            return

        # If no role in state, try JWT fallback (fail-open)
        if user_role is None:
            # Fail-open: let route-level auth handle it
            await self.app(scope, receive, send)
            return

        # Non-admin user attempting write on admin path → 403
        logger.info(
            f"ConversationFirstGuard: blocked {method} {path} for role={user_role}"
        )

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
