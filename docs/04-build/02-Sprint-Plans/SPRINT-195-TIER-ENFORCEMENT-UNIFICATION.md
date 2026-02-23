# Sprint 195 — Tier Enforcement Unification (ADR-065)

```yaml
sprint: 195
title: "Tier Enforcement Unification — ADR-065"
duration: "February 22, 2026 (1 working day — hotfix sprint)"
status: COMPLETE
priority: P0 (Production Bug Fix) + P1 (Architecture Unification)
framework: SDLC 6.1.1
epic: EP-08 Chat-First Governance Loop
adr: ADR-065-Unified-Tier-Resolution
previous: "Sprint 194 — Security Hardening + Agent Enrichment (74/74 tests)"
trigger: "Architecture audit discovered 12 tier enforcement inconsistencies (F-01 through F-12)"
```

---

## Sprint 195 Goal

During Sprint 194 acceptance testing, an architecture audit discovered **12 inconsistencies** (F-01 through F-12) in the tier enforcement system. The CEO user (`dangtt1971@gmail.com`, marked `is_superuser=True`) was being blocked by HTTP 402 because middleware resolved tier from `Subscription.plan` (NULL) instead of recognizing the superuser flag. The VSCode extension showed "Offline mode" and the dashboard displayed "FREE" tier.

Sprint 195 is a hotfix sprint to fix P0 production bugs and unify tier resolution across all 3 middleware layers per ADR-065.

**Root Causes Identified**:
- 3 competing tier sources: `Subscription.plan` (per-user), `Organization.plan` (per-org), `is_superuser` flag
- ConversationFirstGuard was a complete no-op (checked `scope["state"]` only — never populated)
- UsageLimitsMiddleware had no superuser/platform_admin bypass
- Frontend `useUserTier` hook called `/users/me/profile` — a permanent 404

---

## Architecture Audit Findings (F-01 through F-12)

| # | Finding | Severity | Track | Status |
|---|---------|----------|-------|--------|
| F-01 | 8 route prefixes missing from `ROUTE_TIER_TABLE` | P2 | Deferred | Pre-existing (TG-41) |
| F-02 | ConversationFirstGuard is a no-op (scope state never populated) | **P0** | A | **FIXED** |
| F-03 | TierGateMiddleware uses `Subscription.plan` (wrong SSOT) | P1 | B | **FIXED** |
| F-04 | Frontend `useUserTier` calls `/users/me/profile` (404) | **P0** | C | **FIXED** |
| F-05 | 3 middleware files have misleading "reads from AuthMiddleware" comments | P2 | A | **FIXED** |
| F-06 | UsageLimitsMiddleware has no superuser bypass | **P0** | A | **FIXED** |
| F-07 | `User.effective_tier` TIER_RANK missing lite/standard/professional aliases | P1 | B | **FIXED** |
| F-08 | UsageLimitsMiddleware uses `Subscription.plan` (wrong SSOT) | P1 | B | **FIXED** |
| F-09 | `/auth/me` response missing `effective_tier` and `organizations` | P1 | C | **FIXED** |
| F-10 | No ADR documenting tier resolution strategy | P1 | B | **FIXED** (ADR-065) |
| F-11 | `_normalise_tier()` doesn't handle Organization.plan values | P2 | B | **FIXED** |
| F-12 | EP-06 Quality Pipeline Gate 4 Docker sandbox not configured | P3 | D | Deferred |

**Resolved**: 10/12 findings | **Deferred**: 2 (F-01 pre-existing, F-12 infrastructure)

---

## 4-Track Execution Plan

### Track A — P0 Production Bug Fixes (Day 1)

| # | Deliverable | File(s) | Tests |
|---|-------------|---------|-------|
| A-01 | ConversationFirstGuard: JWT+DB role resolution | `conversation_first_guard.py` | 19 |
| A-02 | UsageLimitsMiddleware: superuser/platform_admin bypass | `usage_limits.py` | 2 |
| A-03 | Remove unused `json` import (F401 lint fix) | `usage_limits.py` | — |
| A-04 | Update misleading AuthMiddleware comments | `tier_gate.py`, `usage_limits.py`, `main.py` | — |

### Track B — ADR-065 Tier Unification (Day 1)

| # | Deliverable | File(s) | Tests |
|---|-------------|---------|-------|
| B-01 | Write ADR-065 Unified Tier Resolution | `docs/02-design/01-ADRs/ADR-065-Unified-Tier-Resolution.md` | — |
| B-02 | TierGateMiddleware: org-based resolution (replaces Subscription.plan) | `tier_gate.py` | existing |
| B-03 | UsageLimitsMiddleware: org-based resolution + `_TIER_RANK` map | `usage_limits.py` | 6 |
| B-04 | User.effective_tier: superuser bypass + expanded TIER_RANK | `user.py` | existing |

### Track C — Frontend Tier Display Fix (Day 1)

| # | Deliverable | File(s) | Tests |
|---|-------------|---------|-------|
| C-01 | `UserProfile` schema: add `effective_tier` + `organizations` fields | `schemas/auth.py` | — |
| C-02 | `UserOrganizationInfo` schema for org membership data | `schemas/auth.py` | — |
| C-03 | `/auth/me` endpoint: query org memberships, compute effective tier | `api/routes/auth.py` | — |
| C-04 | `useUserTier.ts`: change `/users/me/profile` → `/auth/me` | `frontend/src/hooks/useUserTier.ts` | — |

### Track D — EP-06 Quality Pipeline Verification (Day 1)

| # | Deliverable | File(s) | Tests |
|---|-------------|---------|-------|
| D-01 | Verify EP-06 Quality Pipeline tests pass | `tests/unit/services/codegen/` | 291 |
| D-02 | Confirm Gates 1-3 production-ready, Gate 4 deferred | quality_pipeline.py | — |

---

## ADR-065 — 4 Locked Decisions

| # | Decision | Rationale |
|---|----------|-----------|
| D1 | **Organization is SSOT** for tier (not Subscription) | ADR-047 aligned — org is billing unit |
| D2 | **superuser/platform_admin → ENTERPRISE everywhere** | Consistent across all 3 middleware layers |
| D3 | **Extend `/auth/me`** with `effective_tier` + `organizations` | No new endpoint — extend existing contract |
| D4 | **Expand TIER_RANK** to cover all ADR-059 plan strings | `free→lite`, `starter→2`, `founder→2`, `professional→pro` |

---

## Files Modified

| File | Action | LOC | Track |
|------|--------|-----|-------|
| `backend/app/middleware/usage_limits.py` | MODIFY | +30 | A+B |
| `backend/app/middleware/tier_gate.py` | MODIFY | +25 | A+B |
| `backend/app/middleware/conversation_first_guard.py` | MODIFY | +80 | A |
| `backend/app/main.py` | MODIFY | +2 | A |
| `backend/app/models/user.py` | MODIFY | +15 | B |
| `backend/app/schemas/auth.py` | MODIFY | +20 | C |
| `backend/app/api/routes/auth.py` | MODIFY | +35 | C |
| `frontend/src/hooks/useUserTier.ts` | MODIFY | +1 | C |
| `docs/02-design/01-ADRs/ADR-065-Unified-Tier-Resolution.md` | NEW | ~150 | B |
| `backend/tests/unit/test_conversation_first_guard.py` | NEW | ~350 | A |
| `backend/tests/unit/test_usage_limits.py` | MODIFY | +120 | A+B |

**Total**: ~828 LOC added (production + tests)

---

## Test Results

| Test File | Pass | Fail | Notes |
|-----------|------|------|-------|
| `test_conversation_first_guard.py` | 19/19 | 0 | NEW — full CFG coverage |
| `test_usage_limits.py` | 34/34 | 0 | +8 new (2 F-06 + 6 org-based) |
| `test_tier_gate.py` | 43/44 | 1 | TG-41 pre-existing (8 ungated routes) |
| `services/codegen/*` (EP-06) | 291/291 | 0 | Verification only |
| **Total middleware** | **96/97** | **1** | 1 pre-existing, not Sprint 195 scope |

---

## Key Design Decisions

### Before Sprint 195 (Broken)
```
User Request → TierGateMiddleware (reads Subscription.plan → NULL → LITE → 402)
            → UsageLimitsMiddleware (reads Subscription.plan → NULL → lite → limits enforced)
            → ConversationFirstGuard (reads scope state → empty → no-op pass-through)
            → Frontend (calls /users/me/profile → 404 → shows "FREE")
```

### After Sprint 195 + Hotfix (ADR-065 Unified)
```
User Request → TierGateMiddleware (JWT or API key → user_id → org-based max tier)
            → UsageLimitsMiddleware (JWT or API key → user_id → org-based max tier)
            → ConversationFirstGuard (JWT or API key → DB role check → proper enforcement)
            → Frontend (calls /auth/me → {effective_tier, organizations} → correct display)

Auth resolution: JWT decode → user_id (priority 2a)
                 API key hash → api_keys table → user_id (priority 2b)

Invariants:
  INV-01: All 3 middleware resolve tier consistently (org-based)
  INV-02: is_superuser OR is_platform_admin → ENTERPRISE everywhere
  INV-03: No org memberships → LITE (safe default)
  INV-04: Frontend tier display === backend tier resolution
  INV-05: API key auth === JWT auth for same user (D5)
```

---

## Verification Checklist

- [x] ConversationFirstGuard enforces admin-only writes (19 tests)
- [x] Superuser bypasses all usage limits (2 tests)
- [x] Org-based tier resolution works across both middleware (6 tests)
- [x] Enterprise early exit in tier iteration (2 tests)
- [x] No-org users default to LITE (2 tests)
- [x] Multi-org users get highest tier (1 test)
- [x] `free` normalises to `lite` in UsageLimitsMiddleware
- [x] `/auth/me` returns `effective_tier` and `organizations`
- [x] `useUserTier.ts` calls `/auth/me` (not `/users/me/profile`)
- [x] EP-06 Quality Pipeline: 291/291 tests pass
- [x] `ruff check` 0 errors on all modified files

---

## Deferred Items

| # | Item | Reason | Target |
|---|------|--------|--------|
| F-01 | 8 ungated route prefixes in ROUTE_TIER_TABLE | Pre-existing, needs CTO tier assignment | Sprint 196+ |
| F-12 | Gate 4 Docker sandbox for EP-06 | Infrastructure dependency | Sprint 196+ |
| — | Original Sprint 195 scope (Codegen + Pilot Prep) | Replaced by P0 hotfix | Sprint 196 |

---

## CTO Review — G-Sprint-Close Verdict

**Score**: 9.2/10 — APPROVED | **Date**: February 22, 2026

### CTO Findings (Resolved Same-Sprint)

| # | Finding | Severity | Resolution |
|---|---------|----------|------------|
| CF-01 | auth.py `tier_rank` dict was 4-key, ADR-065 D4 mandates 8-key | P2 | **FIXED** — expanded to 8 keys matching `User.effective_tier.TIER_RANK` |
| CF-02 | Redundant `effective_tier == "free"` condition in auth.py | P3 | **FIXED** — simplified to `if not is_admin` |

### Remaining Carry-Forward (Sprint 196)

| # | Item | Severity |
|---|------|----------|
| CF-03 | TG-41: 8 ungated routes in TierGate | P2 (pre-existing) |

---

---

## Post-Sprint Hotfix — API Key Auth in Middleware (2026-02-23)

**Finding**: F-195-05 — All 3 middleware `_extract_user_id()` methods only handled JWT tokens.
The VSCode Extension authenticates via API keys (`sdlc_live_*`), which failed JWT decode silently,
causing tier to default to LITE → HTTP 402 on STANDARD+ routes (Context Overlay, Compliance).

**Root Cause**: `_extract_user_id()` tried `decode_token(token)` on an API key string, which
is not a JWT. The exception was caught, returning `None`, and `_resolve_user_tier()` defaulted to `"LITE"`.

**Fix**: Added `_extract_user_id_from_api_key()` async method to all 3 middleware:

| File | Method Added | Pattern |
|------|-------------|---------|
| `tier_gate.py` | `_extract_user_id_from_api_key()` | SHA256 hash → `api_keys` table → `user_id` |
| `conversation_first_guard.py` | `_extract_user_id_from_api_key()` | Same pattern |
| `usage_limits.py` | `_extract_user_id_from_api_key()` | Same pattern |

**ADR Update**: ADR-065 D5 added — API key auth must resolve tier identically to JWT.
INV-05 added — API key and JWT produce same tier for same user.

**Verification**: 53/53 middleware tests pass. Backend logs confirm `200 OK` for
`/api/v1/agents-md/context/` (was `402 Payment Required`).

---

**Sprint 195 Completed**: February 22, 2026
**Post-Sprint Hotfix**: February 23, 2026 (F-195-05 API key auth)
**CTO Score**: 9.2/10 — APPROVED
**Updated By**: PM + AI Development Partner
**Framework Version**: SDLC 6.1.1
**ADR Reference**: ADR-065-Unified-Tier-Resolution
