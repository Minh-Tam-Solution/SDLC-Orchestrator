"""
==========================================================================
TierGateMiddleware — Sprint 184 (ADR-059 INV-03 Tier Invariant Enforcement)
SDLC Orchestrator — Enterprise-First Tier Enforcement

Purpose:
- Enforce subscription tier gates on all 79 API route prefixes
- Return HTTP 402 Payment Required for insufficient tier access
- Provide upgrade CTA URL in 402 response body

Architecture:
- Pure ASGI (NOT BaseHTTPMiddleware) — avoids FastAPI 0.100+ hang bug
  (Starlette BaseHTTPMiddleware event loop conflict on unhandled exceptions)
- Reads user_tier from scope["state"]["user_tier"] (set by AuthMiddleware)
- Falls back to JWT decode → Redis cache if scope state not populated
- Admin bypass via X-Admin-Override header (ENTERPRISE routes only)
- Fail-open: if tier lookup fails, pass through (route-level guards handle auth)

Tier Hierarchy (ADR-059):
  LITE=1         Free cloud gateway, evaluation
  STANDARD=2     Starter ($99/mo) + Growth ($299/mo)
  PROFESSIONAL=3 $499/mo, multi-agent, compliance-light, OTT full
  ENTERPRISE=4   Custom ($80/seat), SSO, NIST, unlimited + SLA

HTTP Code Semantics (ADR-059):
  401: no authentication (AuthMiddleware / get_current_user)
  403: wrong RBAC role/scope
  402: tier blocked (this middleware)
  404: not found

SDLC 6.1.0 — Sprint 184 P0 Deliverable
Authority: CTO + CPO Approved (ADR-059)
==========================================================================
"""

import logging
import os
from typing import Any

from starlette.responses import JSONResponse
from starlette.types import ASGIApp, Receive, Scope, Send

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Route Tier Table — all 79 route prefixes mapped to minimum required tier
# ---------------------------------------------------------------------------
# LITE=1, STANDARD=2, PROFESSIONAL=3, ENTERPRISE=4
# Ordering matters: more specific prefixes should appear before shorter ones
# (prefix matching stops at first match — _get_required_tier is O(n) scan)
# ---------------------------------------------------------------------------

ROUTE_TIER_TABLE: dict[str, int] = {
    # -------------------------------------------------------------------------
    # CORE — LITE (1): public + authentication + universal access
    # -------------------------------------------------------------------------
    "/api/v1/auth":               1,
    "/api/v1/projects":           1,
    # Ordering: /api/v1/gates-engine must precede /api/v1/gates — startswith("/api/v1/gates")
    # is True for gates-engine paths, so the more-specific entry must appear first.
    "/api/v1/gates-engine":       2,   # F-01: STANDARD (placed before /gates for prefix-match order)
    "/api/v1/gates":              1,
    "/api/v1/evidence":           1,
    "/api/v1/dashboard":          1,
    "/api/v1/webhooks":           1,
    "/api/v1/users":              1,
    "/api/v1/notifications":      1,
    "/api/v1/health":             1,
    "/api/v1/templates":          1,   # Sprint 181 — public CORE endpoint
    "/api/v1/feedback":           1,
    "/api/v1/docs":               1,
    "/api/v1/policies":           1,
    "/api/v1/push":               1,
    "/api/v1/gdpr":               1,   # GDPR = ALL tiers (privacy law obligation)
    "/api/v1/analytics":          1,   # F-01 fix: analytics dashboard (all tiers)
    "/api/v1/api-keys":           1,   # F-01 fix: API key management (all tiers)
    "/api/v1/payments":           1,   # F-01 fix: billing/subscriptions (all tiers)
    # -------------------------------------------------------------------------
    # STANDARD (2): team collaboration + planning + integrations
    # -------------------------------------------------------------------------
    "/api/v1/teams":              2,
    "/api/v1/organizations":      2,
    "/api/v1/council":            2,
    "/api/v1/planning":           2,
    "/api/v1/codegen":            2,
    "/api/v1/learnings":          2,
    "/api/v1/github":             2,
    "/api/v1/check-runs":         2,
    "/api/v1/sast":               2,
    "/api/v1/roadmaps":           2,
    "/api/v1/phases":             2,
    "/api/v1/sprints":            2,
    "/api/v1/backlog":            2,
    "/api/v1/opa":                2,
    "/api/v1/risk-analysis":      2,
    "/api/v1/contract-lock":      2,
    "/api/v1/spec-converter":     2,
    "/api/v1/cross-reference":    2,
    "/api/v1/agents":             2,
    "/api/v1/evidence-manifest":  2,
    "/api/v1/consultations":      2,
    "/api/v1/mrp":                2,
    "/api/v1/framework-version":  2,
    "/api/v1/context-validation": 2,
    "/api/v1/maturity":           2,
    # OTT Gateway: STANDARD tier baseline (ADR-059 Decision OTT-3)
    # Per-channel sub-routing inside ott_gateway.py:
    #   telegram → STANDARD (Vietnam pilot), zalo → STANDARD,
    #   teams → PROFESSIONAL, slack → ENTERPRISE
    "/api/v1/channels":           2,
    # F-01 fix: routes registered in main.py but missing from table (Sprint 184 review)
    "/api/v1/triage":             2,   # F-01: triage workflow (STANDARD)
    "/api/v1/sop":                2,   # F-01: SOP Generator (STANDARD)
    "/api/v1/ai-detection":       2,   # F-01: AI Detection service (STANDARD)
    "/api/v1/telemetry":          2,   # F-01: product telemetry (STANDARD)
    "/api/v1/deprecation":        2,   # F-01: deprecation monitoring (STANDARD)
    "/api/v1/vcr":                2,   # F-01: VCR/SASE workflow (STANDARD)
    "/api/v1/doc-cross-reference": 2,  # F-01: document cross-reference validation (STANDARD)
    "/api/v1/e2e":                2,   # F-01: E2E testing API (STANDARD)
    "/api/v1/overrides":          2,   # F-01: override request workflow (STANDARD)
    # -------------------------------------------------------------------------
    # PROFESSIONAL (3): multi-agent, compliance-ready, full OTT, advanced AI
    # -------------------------------------------------------------------------
    "/api/v1/context-authority":  3,
    "/api/v1/agent-team":         3,
    "/api/v1/governance":         3,
    "/api/v1/ceo-dashboard":      3,
    "/api/v1/crp":                3,
    "/api/v1/auto-generation":    3,
    "/api/v1/governance-mode":    3,
    "/api/v1/vibecoding-index":   3,
    "/api/v1/stage-gating":       3,
    "/api/v1/governance-metrics": 3,
    "/api/v1/grafana-dashboards": 3,
    "/api/v1/dogfooding":         3,
    "/api/v1/governance-specs":   3,
    "/api/v1/governance-vibecodin": 3,  # governance-vibecoding prefix
    "/api/v1/pilot":              3,
    "/api/v1/preview":            3,
    "/api/v1/jira":               3,   # Jira integration — Sprint 184
    "/api/v1/mcp":                3,   # F-01 fix: MCP Analytics dashboard (PROFESSIONAL+)
    # -------------------------------------------------------------------------
    # ENTERPRISE (4): SSO, NIST, SOC2, unlimited + SLA + audit
    # -------------------------------------------------------------------------
    "/api/v1/admin":              4,
    "/api/v1/tier-management":    4,
    "/api/v1/nist":               4,
    "/api/v1/compliance":         4,
    "/api/v1/invitations":        4,
    "/api/v1/enterprise":         4,   # Covers all /api/v1/enterprise/* routes (SSO, audit, compliance)
    "/api/v1/data-residency":     4,   # Multi-region — Sprint 186
}

# Canonical tier names by integer value
TIER_NAMES: dict[int, str] = {
    1: "LITE",
    2: "STANDARD",
    3: "PROFESSIONAL",
    4: "ENTERPRISE",
}

# String tier name → integer value (includes legacy names from effective_tier)
TIER_VALUES: dict[str, int] = {
    # ADR-059 canonical names (Sprint 181+)
    "LITE":         1,
    "STANDARD":     2,
    "PROFESSIONAL": 3,
    "ENTERPRISE":   4,
    # Legacy names from User.effective_tier (organization.plan values)
    "free":         1,
    "lite":         1,
    "starter":      2,
    "standard":     2,
    "founder":      2,   # FOUNDER grandfathered = STANDARD tier
    "pro":          3,
    "professional": 3,
    "enterprise":   4,
}

# Upgrade CTA URL (Sprint 188: pricing page will be live)
UPGRADE_URL = os.getenv(
    "TIER_UPGRADE_URL",
    "https://app.sdlcorchestrator.com/billing/upgrade",
)

# Admin bypass secret (ENTERPRISE bypass — TG-21/22)
# Set TIER_GATE_ADMIN_SECRET in environment; empty string disables bypass
ADMIN_BYPASS_SECRET = os.getenv("TIER_GATE_ADMIN_SECRET", "")


class TierGateMiddleware:
    """
    Pure ASGI tier gate middleware.

    Enforces subscription tier requirements on all 79 API route prefixes.
    Returns HTTP 402 Payment Required with upgrade CTA when user's
    tier is insufficient for the requested route.

    Architecture Decision:
    - Pure ASGI (NOT BaseHTTPMiddleware) — critical for FastAPI 0.100+
      BaseHTTPMiddleware causes request hang on unhandled exceptions due
      to Starlette event loop conflict (see CLAUDE.md Module 1 Debugging)
    - Reads user_tier from scope["state"]["user_tier"] first
    - Falls back to JWT decode + Redis cache if state not populated
    - Fail-open: tier lookup failure → pass through (don't block)

    Ordering in middleware stack (main.py):
        app.add_middleware(TierGateMiddleware)    ← last middleware added
        app.add_middleware(CacheHeadersMiddleware) ← runs before TierGate
        ... (SecurityHeaders, RateLimiter, Metrics, CORS, GZip)

    Note: add_middleware stacks in LIFO order — last added runs first.
    TierGateMiddleware should be added AFTER auth-related middleware
    so scope["state"]["user_tier"] is populated before tier check.
    """

    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        # Only inspect HTTP requests (pass WebSocket / lifespan through)
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        path: str = scope.get("path", "")

        # Determine required tier for this path (None = no tier restriction)
        required_tier: int | None = self._get_required_tier(path)

        # No restriction or LITE route → pass through immediately
        if required_tier is None or required_tier <= 1:
            await self.app(scope, receive, send)
            return

        # Check admin bypass header first (X-Admin-Override: <secret>)
        if self._is_admin_bypass(scope):
            await self.app(scope, receive, send)
            return

        # Resolve user's current tier from scope state (set by AuthMiddleware)
        user_tier_str: str = self._resolve_user_tier(scope)
        user_tier_value: int = TIER_VALUES.get(user_tier_str, 1)

        if user_tier_value < required_tier:
            # Build 402 response with upgrade CTA
            response = JSONResponse(
                status_code=402,
                content={
                    "error": "tier_required",
                    "required_tier": TIER_NAMES[required_tier],
                    "current_tier": TIER_NAMES.get(user_tier_value, user_tier_str.upper()),
                    "upgrade_url": UPGRADE_URL,
                    "message": (
                        f"This feature requires {TIER_NAMES[required_tier]} subscription. "
                        f"Upgrade at {UPGRADE_URL}"
                    ),
                },
            )
            await response(scope, receive, send)
            return

        # Tier check passed → continue to application
        await self.app(scope, receive, send)

    # -------------------------------------------------------------------------
    # Private helpers
    # -------------------------------------------------------------------------

    def _get_required_tier(self, path: str) -> int | None:
        """
        Look up minimum required tier for the given path.

        Uses prefix matching against ROUTE_TIER_TABLE.
        Returns None if no matching prefix found (no restriction).

        Complexity: O(n) where n = len(ROUTE_TIER_TABLE) ≈ 78 entries.
        Performance: <1ms for 78-entry dict scan (TG-26 benchmark).

        Args:
            path: URL path from scope["path"]

        Returns:
            Integer tier level (1–4) or None if path not in table.
        """
        for prefix, tier in ROUTE_TIER_TABLE.items():
            if path.startswith(prefix):
                return tier
        return None

    def _resolve_user_tier(self, scope: Scope) -> str:
        """
        Resolve user's subscription tier from request scope.

        Priority order:
        1. scope["state"]["user_tier"] — set by upstream AuthMiddleware
        2. Default to "LITE" (fail-open: don't block on lookup failure)

        The downstream route-level dependencies (require_enterprise_tier,
        get_current_active_user) enforce authentication separately.
        Unauthenticated requests are handled by those dependencies (401),
        not by this middleware (402).

        Args:
            scope: ASGI connection scope

        Returns:
            Tier name string (used in TIER_VALUES lookup).
        """
        state: dict[str, Any] = scope.get("state", {})  # type: ignore[assignment]
        # scope["state"] may be a Starlette State object or plain dict
        if hasattr(state, "__dict__"):
            # Starlette State object: access attributes via __dict__
            return getattr(state, "user_tier", "LITE")
        return state.get("user_tier", "LITE")

    def _is_admin_bypass(self, scope: Scope) -> bool:
        """
        Check if the request carries a valid admin bypass header.

        Header: X-Admin-Override: <TIER_GATE_ADMIN_SECRET>

        Security:
        - Bypass is disabled when TIER_GATE_ADMIN_SECRET is empty (default)
        - Used only for ENTERPRISE-level maintenance operations
        - Logged at WARNING level for audit purposes

        Args:
            scope: ASGI connection scope

        Returns:
            True if valid bypass header present, False otherwise.
        """
        if not ADMIN_BYPASS_SECRET:
            return False

        headers = dict(scope.get("headers", []))
        # Headers are bytes in ASGI scope
        bypass_value = headers.get(b"x-admin-override", b"").decode("utf-8", errors="replace")

        if bypass_value == ADMIN_BYPASS_SECRET:
            path = scope.get("path", "")
            logger.warning(
                "TierGateMiddleware: admin bypass used",
                extra={"path": path, "client": scope.get("client")},
            )
            return True

        return False
