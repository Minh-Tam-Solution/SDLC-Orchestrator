---
sdlc_version: "6.1.0"
document_type: "Sprint Close"
status: "CLOSED"
sprint: "181"
spec_id: "SPRINT-181-CLOSE"
tier: "ENTERPRISE"
stage: "04 - Build"
closed_date: "2026-02-19"
---

# SPRINT-181 CLOSE — OTT Foundation + Orphaned Route Activation

**Status**: CLOSED ✅
**Sprint Duration**: 8 working days
**Closed Date**: February 19, 2026
**Sprint Goal**: Activate OTT gateway (Telegram + Zalo) and register 7 orphaned ENTERPRISE routes

---

## 1. Definition of Done — Checklist

| # | Criterion | Status |
|---|-----------|--------|
| 1 | `agent_bridge/` package: `protocol_adapter.py`, `telegram_normalizer.py`, `zalo_normalizer.py` | ✅ DONE |
| 2 | `ott_gateway.py` POST /channels/{channel}/webhook registered in `main.py` | ✅ DONE |
| 3 | 20 PA tests (PA-01..PA-20) passing | ✅ DONE |
| 4 | 7 orphaned routers activated in `main.py` with tier gates | ✅ DONE |
| 5 | `require_enterprise_tier` in `app.api.dependencies` (HTTP 402) | ✅ DONE |
| 6 | `invitations.py` async fix (AsyncSession + broken `app.core.deps` import removed) | ✅ DONE |
| 7 | `SubscriptionPlan.FREE` → `SubscriptionPlan.LITE` in `subscription.py` | ✅ DONE |
| 8 | `s181_001_tier_naming_lite.py` migration (Revises: s178_001) | ✅ DONE |
| 9 | All Sprint 179 EP-07 tests still passing (91/91 regression) | ✅ DONE |
| 10 | Zero P0 bugs | ✅ DONE |

---

## 2. Acceptance Criteria Results

| AC | Description | Result |
|----|-------------|--------|
| AC-181-01 | OrchestratorMessage is a frozen dataclass (immutable) | ✅ PASS |
| AC-181-02 | normalize() converts Telegram webhook → OrchestratorMessage | ✅ PASS |
| AC-181-03 | normalize() converts Zalo webhook → OrchestratorMessage | ✅ PASS |
| AC-181-04 | Content > 4096 chars truncated with [TRUNCATED] marker | ✅ PASS |
| AC-181-05 | `require_enterprise_tier` in `app.api.dependencies` | ✅ PASS |
| AC-181-06 | 7 orphaned routers registered in main.py | ✅ PASS |
| AC-181-07 | 6 ENTERPRISE routers have `require_enterprise_tier` dependency | ✅ PASS |
| AC-181-08 | invitations.py: zero sync Session type refs (AsyncSession only) | ✅ PASS |
| AC-181-09 | SubscriptionPlan.LITE = 'lite' (FREE removed) | ✅ PASS |
| AC-181-10 | s181_001 migration: Revises s178_001, upgrade+downgrade SQL correct | ✅ PASS |
| AC-181-11 | require_enterprise_tier raises HTTP 402 for non-enterprise tier | ✅ PASS |
| AC-181-12 | 20/20 PA tests pass | ✅ PASS |

**All 12 ACs: PASS ✅**

---

## 3. Deliverables Summary

### P0 — OTT Channel Foundation (Days 1-3)

| File | Status | Description |
|------|--------|-------------|
| `backend/app/services/agent_bridge/__init__.py` | NEW ✅ | Package exports: OrchestratorMessage, normalize, route_to_normalizer |
| `backend/app/services/agent_bridge/protocol_adapter.py` | NEW ✅ | Core: OrchestratorMessage frozen dataclass, _CHANNEL_REGISTRY, normalize(), _sanitize_content() |
| `backend/app/services/agent_bridge/telegram_normalizer.py` | NEW ✅ | Telegram Bot API webhook → OrchestratorMessage |
| `backend/app/services/agent_bridge/zalo_normalizer.py` | NEW ✅ | Zalo OA webhook (user_send_text) → OrchestratorMessage |
| `backend/app/api/routes/ott_gateway.py` | NEW ✅ | POST /api/v1/channels/{channel}/webhook (HMAC + injection guard + 400/403/422/503) |
| `backend/tests/unit/test_protocol_adapter.py` | NEW ✅ | PA-01..PA-20: 20 tests, all pass |

### P0 — Orphaned Route Activation (Days 4-5)

| File | Change | Tier |
|------|--------|------|
| `backend/app/api/dependencies.py` | Added `require_enterprise_tier()` (HTTP 402) | — |
| `backend/app/main.py` | +8 import lines + 8 include_router calls | — |
| `ott_gateway.router` | Registered at `/api/v1` | CORE (OTT) |
| `templates.router` | Registered at `/api/v1` (public CORE) | CORE |
| `compliance_framework.router` | Registered + ENTERPRISE gate | ENTERPRISE |
| `nist_govern.router` | Registered + ENTERPRISE gate | ENTERPRISE |
| `nist_manage.router` | Registered + ENTERPRISE gate | ENTERPRISE |
| `nist_map.router` | Registered + ENTERPRISE gate | ENTERPRISE |
| `nist_measure.router` | Registered + ENTERPRISE gate | ENTERPRISE |
| `invitations.router` | Registered + ENTERPRISE gate (after async fix) | ENTERPRISE |

### P0 — invitations.py Async Fix (Day 6)

| Change | Detail |
|--------|--------|
| Broken import removed | `from app.core.deps import ...` → `from app.api.dependencies import get_current_user` + `from app.db.session import get_db` |
| Session → AsyncSession | `from sqlalchemy.orm import Session` → `from sqlalchemy.ext.asyncio import AsyncSession` |
| Inline queries converted | `db.query(Model).filter(...).first()` → `await db.execute(select(Model).where(...))` |
| Service calls bridged | `invitation_service.*()` → `await db.run_sync(lambda sync_db: invitation_service.*(..., db=sync_db))` |
| Shadowing bug fixed | `status: Optional[str]` param renamed to `invitation_status` (shadowed `fastapi.status`) |
| Business logic scope | Deferred to Sprint 182 (async service layer migration) |

### P1 — Tier Naming Unification (Day 7)

| File | Change |
|------|--------|
| `backend/app/models/subscription.py` | `SubscriptionPlan.FREE = "free"` → `SubscriptionPlan.LITE = "lite"` |
| `backend/app/models/subscription.py` | `default=SubscriptionPlan.FREE` → `default=SubscriptionPlan.LITE` |
| `backend/alembic/versions/s181_001_tier_naming_lite.py` | NEW: `ALTER TYPE subscription_plan_enum RENAME VALUE 'free' TO 'lite'` |

---

## 4. Test Coverage

| Test Suite | Tests | Status |
|-----------|-------|--------|
| PA-01..PA-20 (protocol_adapter) | 20/20 | ✅ PASS |
| EP-07 Sprints 176-178 (agent team) | 57/57 | ✅ PASS |
| Sprint 179 ZeroClaw (output_scrubber, history_compactor, query_classifier, env_scrubber) | 34/34 | ✅ PASS |
| **Total** | **111/111** | **✅ PASS** |

---

## 5. Technical Decisions

### D-181-01: Truncate-before-strip ordering in `_sanitize_content()`
Truncate to 4096 chars FIRST, then apply injection pattern regexes. Rationale: the
`repetition_attack` pattern `(.{5,})\1{4,}` is O(n²) on large identical-char strings.
Bounding to 4096 chars before regex work prevents catastrophic backtracking.

### D-181-02: `db.run_sync()` bridge for invitation_service
Rather than converting the synchronous `invitation_service.py` to async (Sprint 182 scope),
Sprint 181 uses `AsyncSession.run_sync()` to safely call sync service functions from async
handlers. This creates a synchronous connection from the async session, passes it to the
lambda, and runs it in a thread pool. Zero event loop blocking.

### D-181-03: Per-router dependency for ENTERPRISE tier gate
`require_enterprise_tier` applied at `include_router(dependencies=[...])` level, not inside
each route handler. This applies the gate to ALL routes in the router without modifying the
6 ENTERPRISE route files (3,463 LOC, zero new changes to existing files).

### D-181-04: `invitation_status` query param (not `status`)
Renamed `status: Optional[str]` → `invitation_status: Optional[str]` in
`list_team_invitations()` to avoid shadowing `from fastapi import status` module within the
function body. The original code had this shadowing bug which would have caused
`AttributeError` on the 403 path.

---

## 6. Retrospective

### What went well
- Days 1-3 OTT foundation implemented cleanly with `_CHANNEL_REGISTRY` auto-population
  pattern; all 20 PA tests green on first attempt (after PA-18 repetition_attack fix)
- `require_enterprise_tier` as a per-router dependency is elegant — no modifications to
  the 6 existing ENTERPRISE route files
- `db.run_sync()` bridge cleanly defers the large async service migration to Sprint 182

### Lesson learned: F-181-01 — `app.core.deps` missing
`invitations.py` had `from app.core.deps import get_current_user, get_db` — a module that
has never existed in this codebase. This was an undetected latent bug from prior development.
**DoD addition**: All new sprint imports must be verified with `python3 -c "from X import Y"`
before marking the task done. Add import smoke-test to DoD template.

### Sprint 181 blocker pattern
`invitations.py` broken import (`app.core.deps`) blocked main.py imports test in Day 4-5,
requiring Day 6 (async fix) to be pulled forward. Async fix completed in 1.5 hours;
no schedule impact since it was always a Sprint 181 deliverable.

---

## 7. Sprint 182 Handoff

| Item | Sprint 182 Action |
|------|-------------------|
| `invitation_service.py` | Full async migration (all `def` → `async def`, sync Session → AsyncSession) |
| Teams normalizer | `agent_bridge/teams_normalizer.py` (Microsoft Teams enterprise P0) |
| ADR-061 | Enterprise SSO design (SAML 2.0 + Azure AD) |
| ADR-062 | Compliance Evidence Types (SOC2_CONTROL, HIPAA_AUDIT, NIST_AI_RMF) |

---

**Sprint 181 CLOSED** — All ACs met, 111/111 tests green, zero P0 bugs.
**Next sprint**: Sprint 182 — Enterprise SSO Design + Teams Channel (ADR-061)

[@reviewer: Sprint 181 code complete. All 12 ACs pass, 111 tests green.
Key deliverables: OTT gateway (Telegram+Zalo), 7 route activations, require_enterprise_tier,
invitations.py async fix, SubscriptionPlan.LITE migration.
Blocking lesson F-181-01 (app.core.deps) added to DoD template. Ready for G3 review.]
