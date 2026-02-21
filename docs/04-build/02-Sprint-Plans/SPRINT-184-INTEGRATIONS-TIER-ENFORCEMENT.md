---
sdlc_version: "6.1.0"
document_type: "Sprint Plan"
status: "PROPOSED"
sprint: "184"
spec_id: "SPRINT-184"
tier: "PROFESSIONAL"
stage: "04 - Build"
---

# SPRINT-184 — Enterprise Integrations + Tier Enforcement

**Status**: PROPOSED (pending CTO approval)
**Sprint Duration**: 8 working days
**Sprint Goal**: Enforce tier gates on all 78 routes + ship Jira integration (PROFESSIONAL+)
**Epic**: ADR-059 Enterprise-First + EP-07 Integration
**ADR**: ADR-059 (INV-03 tier invariant enforcement)
**Dependencies**: Sprint 183 complete (SSO + compliance evidence types live)
**Budget**: ~$5,120 (64 hrs at $80/hr)

---

## 1. Sprint Goal

Two parallel tracks:
1. **Tier Gate Middleware** — enforce all 78 routes with correct tier gates (402 Payment Required for blocked tiers)
2. **Jira Integration** — PROFESSIONAL+ teams sync Jira issues to Evidence Vault

| Deliverable | Priority | New LOC | Days |
|-------------|----------|---------|------|
| `tier_gate.py` (pure ASGI middleware) | P0 | ~200 | 2 |
| Route tier table (all 78 routes mapped) | P0 | ~150 | 1 |
| Tier gate tests (TG-01..40) | P0 | ~400 | 1.5 |
| `jira_adapter.py` (httpx.AsyncClient) | P0 | ~300 | 2 |
| Jira routes (3 endpoints) | P0 | ~100 | 0.5 |
| Jira tests (JA-01..20) | P0 | ~200 | 1 |
| Frontend tier gate UI (lock icons + upgrade modal) | P1 | ~200 | 1.5 |
| **Total** | | **~1,550** | **8** |

---

## 2. Deliverables

| # | Deliverable | Description | Files | Sprint Day |
|---|------------|-------------|-------|------------|
| 1 | `tier_gate.py` | Pure ASGI middleware: 402 Payment Required + upgrade CTA | New | Day 1-2 |
| 2 | `ROUTE_TIER_TABLE` | Dict mapping all 78 route prefixes to required tier | In tier_gate.py | Day 1-2 |
| 3 | `test_tier_gate.py` | TG-01 to TG-40 (40 tier gate tests) | New | Day 3 |
| 4 | `jira_adapter.py` | Jira REST API v3: connect, list projects, sync sprint | New | Day 4-5 |
| 5 | `jira_integration.py` | 3 API routes: POST /connect, GET /projects, POST /sync | New | Day 5 |
| 6 | `test_jira_adapter.py` | JA-01 to JA-20 (20 Jira tests) | New | Day 6 |
| 7 | Frontend lock icons | Locked feature indicators (shadcn/ui Badge + Lock icon) | Modified | Day 7 |
| 8 | Frontend upgrade modal | Plan comparison modal triggered by locked feature click | New | Day 7-8 |

---

## 3. Daily Schedule

### Day 1-2: TierGateMiddleware (`tier_gate.py`)

**Goal**: Pure ASGI middleware that enforces tier gates on all routes

**CRITICAL**: Use pure ASGI (NOT BaseHTTPMiddleware) to avoid FastAPI 0.100+ hang bug

```python
# backend/app/middleware/tier_gate.py
# MUST be pure ASGI — NOT BaseHTTPMiddleware (hangs on unhandled exceptions in FastAPI 0.100+)

from starlette.types import ASGIApp, Receive, Scope, Send
from starlette.responses import JSONResponse

# Route tier table: prefix → minimum tier required
# LITE=1, STANDARD=2, PROFESSIONAL=3, ENTERPRISE=4
ROUTE_TIER_TABLE: dict[str, int] = {
    # CORE (LITE = 1): public + authentication
    "/api/v1/auth":              1,
    "/api/v1/projects":          1,
    "/api/v1/gates":             1,
    "/api/v1/evidence":          1,
    "/api/v1/dashboard":         1,
    "/api/v1/webhooks":          1,
    "/api/v1/users":             1,
    "/api/v1/notifications":     1,
    "/api/v1/health":            1,
    "/api/v1/templates":         1,  # Sprint 181 activated
    # STANDARD = 2
    "/api/v1/teams":             2,
    "/api/v1/council":           2,
    "/api/v1/planning":          2,
    "/api/v1/codegen":           2,
    "/api/v1/learnings":         2,
    "/api/v1/github":            2,
    "/api/v1/check-runs":        2,
    "/api/v1/sast":              2,
    "/api/v1/policies":          2,
    "/api/v1/roadmaps":          2,
    "/api/v1/phases":            2,
    "/api/v1/sprints":           2,
    "/api/v1/backlog":           2,
    "/api/v1/opa":               2,
    # PROFESSIONAL = 3
    "/api/v1/context-authority": 3,
    "/api/v1/agent-team":        3,
    "/api/v1/governance":        3,
    "/api/v1/ceo-dashboard":     3,
    "/api/v1/crp":               3,
    "/api/v1/mrp":               3,
    "/api/v1/channels":          2,  # OTT gateway (Sprint 181) — STANDARD: Telegram+Zalo per ADR-060 D-060-03; per-channel sub-routing (Teams→PROFESSIONAL, Slack→ENTERPRISE) enforced inside ott_gateway.py
    "/api/v1/jira":              3,  # Jira integration (Sprint 184)
    # ENTERPRISE = 4
    "/api/v1/admin":             4,
    "/api/v1/tier-management":   4,
    "/api/v1/nist":              4,
    "/api/v1/compliance":        4,
    "/api/v1/invitations":       4,
    "/api/v1/enterprise/sso":    4,  # SSO (Sprint 183)
    "/api/v1/enterprise/audit":  4,  # Audit trail (Sprint 185)
    "/api/v1/enterprise/compliance": 4,  # SOC2/HIPAA packs (Sprint 185)
    "/api/v1/data-residency":    4,  # Multi-region (Sprint 186)
    "/api/v1/gdpr":              1,  # GDPR is ALL tiers (privacy law)
}

TIER_NAMES = {1: "LITE", 2: "STANDARD", 3: "PROFESSIONAL", 4: "ENTERPRISE"}
TIER_VALUES = {"LITE": 1, "STANDARD": 2, "PROFESSIONAL": 3, "ENTERPRISE": 4}

class TierGateMiddleware:
    """
    Pure ASGI tier gate middleware.

    Returns HTTP 402 Payment Required when user's subscription tier
    is insufficient for the requested route.

    Uses pure ASGI (NOT BaseHTTPMiddleware) to avoid FastAPI starlette hang.
    """

    def __init__(self, app: ASGIApp):
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        path = scope.get("path", "")
        required_tier = self._get_required_tier(path)

        if required_tier and required_tier > 1:
            # Get user tier from scope state (set by AuthMiddleware)
            user_tier = scope.get("state", {}).get("user_tier", "LITE")
            user_tier_value = TIER_VALUES.get(user_tier, 1)

            if user_tier_value < required_tier:
                response = JSONResponse(
                    status_code=402,
                    content={
                        "error": "tier_required",
                        "required_tier": TIER_NAMES[required_tier],
                        "current_tier": user_tier,
                        "upgrade_url": "https://app.sdlcorchestrator.com/billing/upgrade",
                        "message": f"This feature requires {TIER_NAMES[required_tier]} subscription."
                    }
                )
                await response(scope, receive, send)
                return

        await self.app(scope, receive, send)

    def _get_required_tier(self, path: str) -> int | None:
        for prefix, tier in ROUTE_TIER_TABLE.items():
            if path.startswith(prefix):
                return tier
        return None
```

**Registration in main.py**:
```python
# backend/app/main.py
from app.middleware.tier_gate import TierGateMiddleware
app.add_middleware(TierGateMiddleware)  # Added AFTER AuthMiddleware — reads user_tier from scope["state"] set by AuthMiddleware
```

**Test Cases (TG-01 to TG-40)**:
```
TG-01: LITE user can access /api/v1/auth endpoints (tier=1)
TG-02: LITE user can access /api/v1/projects (tier=1)
TG-03: LITE user gets 402 on /api/v1/agent-team (needs PROFESSIONAL)
TG-04: LITE user gets 402 on /api/v1/enterprise/sso (needs ENTERPRISE)
TG-05: STANDARD user can access /api/v1/teams (tier=2)
TG-06: STANDARD user gets 402 on /api/v1/agent-team (needs PROFESSIONAL)
TG-07: PROFESSIONAL user can access /api/v1/agent-team
TG-08: PROFESSIONAL user gets 402 on /api/v1/enterprise/sso (needs ENTERPRISE)
TG-09: ENTERPRISE user can access all routes
TG-10: 402 response body includes required_tier field
TG-11: 402 response body includes current_tier field
TG-12: 402 response body includes upgrade_url
TG-13: Unauthenticated user on LITE route returns 401 (AuthMiddleware, not TierGate)
TG-14: /api/v1/gdpr accessible by LITE users (privacy law — all tiers)
TG-15: /api/v1/health accessible without auth (non-authenticated endpoint)
TG-16: TierGateMiddleware is pure ASGI (no BaseHTTPMiddleware inheritance)
TG-17: TierGateMiddleware passes non-http scope (websocket) through unchanged
TG-18: route /api/v1/nist/ (with trailing slash) correctly maps to ENTERPRISE
TG-19: route /api/v1/enterprise/sso/saml/callback maps to ENTERPRISE
TG-20: Unknown route (not in ROUTE_TIER_TABLE) passes through (no tier requirement)
TG-21: Admin bypass header X-Admin-Override: {secret} skips tier check (ENTERPRISE routes)
TG-22: Admin bypass requires valid secret (invalid secret still returns 402)
TG-23: Tier check uses prefix matching, not exact match
TG-24: /api/v1/jira requires PROFESSIONAL tier
TG-25: PROFESSIONAL user can access /api/v1/channels (OTT gateway)
TG-26: Performance: tier check adds <1ms overhead (pure dict lookup)
TG-27: ROUTE_TIER_TABLE covers all 78 route prefixes
TG-28: /api/v1/codegen requires STANDARD tier
TG-29: /api/v1/council requires STANDARD tier
TG-30: TierGateMiddleware reads user_tier from scope["state"] (set by AuthMiddleware)
TG-31: LITE user on STANDARD route gets message about STANDARD upgrade
TG-32: LITE user on ENTERPRISE route gets message about ENTERPRISE upgrade
TG-33: 402 response is JSON (Content-Type: application/json)
TG-34: TierGateMiddleware handles scope without state gracefully (defaults to LITE)
TG-35: /api/v1/enterprise/compliance requires ENTERPRISE
TG-36: /api/v1/enterprise/audit requires ENTERPRISE
TG-37: /api/v1/data-residency requires ENTERPRISE
TG-38: /api/v1/templates is LITE (free, public endpoint)
TG-39: Multiple middleware chaining: TierGate after Auth passes state correctly
TG-40: TierGateMiddleware performance test: 1000 req/s baseline (no regression)
```

---

### Day 4-5: Jira Adapter (`jira_adapter.py`)

**Goal**: Jira REST API v3 integration via httpx.AsyncClient (no SDK)

```python
# backend/app/services/integrations/jira_adapter.py
import httpx
from typing import Any

class JiraAdapter:
    """
    Jira REST API v3 adapter.
    Network-only: uses httpx.AsyncClient (no atlassian SDK — licensing clarity).
    PROFESSIONAL+ tier required.
    """

    def __init__(self, base_url: str, api_token: str, email: str):
        self.base_url = base_url.rstrip("/")
        self.auth = httpx.BasicAuth(email, api_token)
        self.headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
        }

    async def list_projects(self) -> list[dict[str, Any]]:
        """List Jira projects accessible by the API token."""
        async with httpx.AsyncClient(auth=self.auth) as client:
            response = await client.get(
                f"{self.base_url}/rest/api/3/project/search",
                headers=self.headers,
                params={"expand": "description", "maxResults": 50},
                timeout=10.0,
            )
            response.raise_for_status()
            return response.json().get("values", [])

    async def get_sprint_issues(self, board_id: int, sprint_id: int) -> list[dict]:
        """Get issues for a specific sprint (requires Jira Software)."""
        async with httpx.AsyncClient(auth=self.auth) as client:
            response = await client.get(
                f"{self.base_url}/rest/agile/1.0/board/{board_id}/sprint/{sprint_id}/issue",
                headers=self.headers,
                params={"maxResults": 100, "fields": "summary,status,assignee,issuetype"},
                timeout=15.0,
            )
            response.raise_for_status()
            return response.json().get("issues", [])

    async def sync_to_evidence_vault(
        self, project_id: int, jira_issues: list[dict], db: AsyncSession
    ) -> list[GateEvidence]:
        """Sync Jira issues as evidence records in the Evidence Vault."""
        evidence_records = []
        for issue in jira_issues:
            evidence = GateEvidence(
                project_id=project_id,
                evidence_type=EvidenceType.TEST_RESULTS,  # Sprint tracking = test evidence
                content=f"Jira: {issue['key']} - {issue['fields']['summary']}",
                source="jira",
                external_id=issue["key"],
            )
            db.add(evidence)
            evidence_records.append(evidence)
        await db.commit()
        return evidence_records

    async def test_connection(self) -> bool:
        """Test API credentials by calling /rest/api/3/myself."""
        try:
            async with httpx.AsyncClient(auth=self.auth) as client:
                response = await client.get(
                    f"{self.base_url}/rest/api/3/myself",
                    headers=self.headers,
                    timeout=5.0,
                )
                return response.status_code == 200
        except httpx.RequestError:
            return False
```

**Jira Test Cases (JA-01 to JA-20)**:
```
JA-01: list_projects returns list of Jira project dicts
JA-02: list_projects passes BasicAuth credentials
JA-03: list_projects handles empty workspace (returns [])
JA-04: list_projects raises HTTPStatusError on 401 (invalid credentials)
JA-05: list_projects raises HTTPStatusError on 403 (insufficient permissions)
JA-06: list_projects timeout=10.0s enforced
JA-07: get_sprint_issues returns list of issue dicts
JA-08: get_sprint_issues includes summary, status, assignee fields
JA-09: get_sprint_issues handles empty sprint (returns [])
JA-10: sync_to_evidence_vault creates GateEvidence records in DB
JA-11: sync_to_evidence_vault sets source="jira" on all records
JA-12: sync_to_evidence_vault sets external_id=issue["key"]
JA-13: sync_to_evidence_vault is idempotent (upsert on external_id)
JA-14: test_connection returns True for valid credentials
JA-15: test_connection returns False for 401 response
JA-16: test_connection returns False for network timeout
JA-17: POST /api/v1/jira/connect stores encrypted API token in DB
JA-18: GET /api/v1/jira/projects calls JiraAdapter.list_projects
JA-19: POST /api/v1/jira/sync calls sync_to_evidence_vault
JA-20: /api/v1/jira requires PROFESSIONAL tier (TierGateMiddleware enforces)
```

---

### Day 7-8: Frontend Tier Gate UI

**Goal**: Locked feature indicators + upgrade modal

**Components**:
1. `frontend/landing/src/components/tier-gate/LockedFeature.tsx`:
   - Props: `requiredTier: "STANDARD" | "PROFESSIONAL" | "ENTERPRISE"`, `featureName: string`
   - Shows `<Lock className="h-4 w-4" />` icon + tooltip "Upgrade to {tier}"
   - On click: opens upgrade modal

2. `frontend/landing/src/components/tier-gate/UpgradeModal.tsx`:
   - Shows current tier vs required tier
   - Plan comparison table (features per tier)
   - CTA: "Upgrade to PROFESSIONAL" → billing portal
   - Handles 402 API responses globally via React Query error handler

3. Global 402 handler in TanStack Query client:
   ```typescript
   // frontend/landing/src/lib/query-client.ts
   queryClient.setDefaultOptions({
     queries: {
       retry: (failureCount, error) => {
         if (error?.status === 402) return false; // Don't retry tier blocks
         return failureCount < 3;
       },
     },
   });
   ```

---

## 4. Success Criteria

| Criterion | Target | Measurement |
|-----------|--------|-------------|
| Tier gate tests pass | 40/40 | TG-01 to TG-40 |
| Jira tests pass | 20/20 | JA-01 to JA-20 |
| All 78 routes covered | 78/78 | ROUTE_TIER_TABLE has 78 entries |
| 402 response correct format | All | TG-10..12 pass |
| Jira sync creates evidence | Pass | JA-10..12 pass |
| Zero P0 bugs | 0 | CI clean |
| Frontend upgrade modal renders | Pass | Visual regression test |

---

## 5. Risks

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|-----------|
| BaseHTTPMiddleware hang (FastAPI 0.100+) | KNOWN BUG | Critical | Pure ASGI only (TG-16 enforces this) |
| Jira API rate limit (100 req/10s per user) | Medium | Low | Implement 429 retry with exponential backoff |
| Tier gate breaks existing integration tests | Medium | Medium | Run full regression before deploy |
| ROUTE_TIER_TABLE miss (new routes in Sprint 185+) | Medium | Medium | Add tier table validation test (TG-27) |

---

## 6. Dependencies

| Dependency | Type | Status |
|-----------|------|--------|
| Sprint 183 complete | Prerequisite | Required |
| AuthMiddleware sets user_tier in scope["state"] | Code | Must verify |
| httpx (async HTTP client) | Package | Already in requirements.txt |
| Jira Cloud API token | Infrastructure | Customer provides; dev uses mock |

---

## 7. Definition of Done

- [ ] `tier_gate.py` implemented as pure ASGI (NOT BaseHTTPMiddleware)
- [ ] `ROUTE_TIER_TABLE` covers all 78 routes
- [ ] 40 tier gate tests (TG-01..40) written and passing
- [ ] `jira_adapter.py` implemented with httpx (no SDK)
- [ ] 3 Jira routes registered in main.py
- [ ] 20 Jira tests (JA-01..20) written and passing
- [ ] Frontend LockedFeature + UpgradeModal components shipped
- [ ] Global 402 handler in React Query client
- [ ] Zero regressions on Sprint 181-183 tests
- [ ] Zero P0 bugs
- [ ] SPRINT-184-CLOSE.md written

---

**Approval Required**: CTO
**Budget**: ~$5,120 (8 days × 8 hrs × $80/hr)
**Risk Level**: MEDIUM (tier gate middleware has broad impact on all routes)
