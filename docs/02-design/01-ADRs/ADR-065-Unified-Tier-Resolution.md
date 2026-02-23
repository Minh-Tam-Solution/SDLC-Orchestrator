---
sdlc_version: "6.1.1"
document_type: "Architecture Decision Record"
status: "APPROVED"
sprint: "195"
spec_id: "ADR-065"
tier: "ALL"
stage: "02 - Design"
owner: "CTO"
approved_by: "CTO + PM"
approved_date: "2026-02-22"
---

# ADR-065 — Unified Tier Resolution

**Status**: APPROVED (CTO + PM, 2026-02-22)
**Sprint**: 195
**Deciders**: CTO, PM, Architect
**Category**: Platform Architecture — Tier Enforcement
**Supersedes**: N/A (amends ADR-059 tier enforcement implementation)
**Triggers**: Sprint 195 Architecture Audit (12 findings, F-01 through F-12)
**Related**: ADR-047 (Multi-Org Access), ADR-059 (Enterprise-First Refocus)

---

## 1. Context

### 1.1 Triggering Event

Sprint 195 architecture audit discovered 12 inconsistencies in the Platform Admin
vs Application User tier system. The CEO user (`dangtt1971@gmail.com`) was marked
as `is_superuser=true` and had admin privileges, but the web dashboard showed
"FREE" tier. The VS Code Extension returned HTTP 402 (tier_required) because
the `agents-md` endpoint required STANDARD but the user had no Subscription record.

### 1.2 Core Problem

**Three competing tier sources produce different results depending on which
middleware or endpoint resolves the tier:**

| Source | Location | Values | Used By |
|--------|----------|--------|---------|
| `Subscription.plan` | Per-user table | lite/founder/starter/standard/pro/enterprise | TierGateMiddleware, UsageLimitsMiddleware |
| `Organization.plan` | Per-org table | free/starter/pro/enterprise (4 values) | `User.effective_tier` property, `require_enterprise_tier` dependency |
| `is_superuser` flag | User table boolean | true/false | TierGateMiddleware (→ENTERPRISE), ConversationFirstGuard |

**Consequences of the split:**
- TierGate reads `Subscription.plan` → user has no subscription → defaults to LITE
- `User.effective_tier` reads `Organization.plan` → user's org is "pro" → returns "pro"
- Same user gets different tiers from different code paths
- Frontend calls `/users/me/profile` which does not exist → always shows "FREE"
- `is_superuser` grants ENTERPRISE in TierGate but is ignored by UsageLimits (fixed in Sprint 195 Track A)

### 1.3 Options Evaluated

| # | Option | Description | Pros | Cons |
|---|--------|-------------|------|------|
| A | **Org-based SSOT** | Organization is the billing unit. All tier checks resolve via org membership. | ADR-047 aligned, single source of truth, natural for multi-org | Subscription table becomes payment-record only |
| B | Subscription-based SSOT | User.subscription is the billing unit. Org.plan removed. | Per-user billing, simpler | Breaks multi-org model, ADR-047 violation |
| C | Hybrid (status quo) | Keep both sources, add reconciliation | No migration needed | Permanent inconsistency, already causing bugs |

### 1.4 What Already Exists

- `User.effective_tier` (user.py:278-341): Already implements org-based max-tier with
  early-exit optimization. Uses `TIER_RANK = {enterprise:4, pro:3, starter:2, free:1}`.
- `UserOrganization` join table with `selectin` eager loading for `organization` relationship.
- `Organization.plan` with CHECK constraint: `free`, `starter`, `pro`, `enterprise`.
- `Subscription` table (subscription.py): per-user records with 6-value enum
  (lite/founder/starter/standard/pro/enterprise).
- Frontend `useUserTier` hook with matching `TIER_RANK` and `calculateEffectiveTier()`.

---

## 2. Decision

### 2.1 Locked Decisions (4)

| # | Decision | Rationale |
|---|----------|-----------|
| D1 | **Organization is the billing unit** (Option A) | ADR-047 mandates multi-org access. User's effective tier = max(org plans). Subscription table retains payment records only. |
| D2 | **`is_superuser` / `is_platform_admin` → ENTERPRISE everywhere** | All tier-checking code paths must grant ENTERPRISE to superusers. Already done in TierGate + UsageLimits (Sprint 195 Track A). |
| D3 | **Extend `/auth/me` — no new endpoint** | Frontend `useUserTier` currently calls non-existent `/users/me/profile`. Fix by adding `effective_tier` and `organizations` to the existing `/auth/me` response. |
| D4 | **Expand TIER_RANK to cover all ADR-059 plan strings** | `User.effective_tier` TIER_RANK only has 4 entries (free/starter/pro/enterprise). Must add: `lite:1`, `standard:2`, `professional:3`, `founder:2` to handle all plan strings. |
| D5 | **API key (`sdlc_live_*`) auth must resolve tier identically to JWT** | VSCode Extension and CLI authenticate via API keys, not JWT. All 3 middleware must hash the key, look up `api_keys.user_id`, then resolve tier via org membership — same path as JWT users. Added 2026-02-23. |

### 2.2 Architecture

**Unified Tier Resolution Flow:**

```
Request → Middleware (TierGate / UsageLimits / ConversationFirstGuard)
           │
           ├─ 1. scope["state"]["user_tier"] (fast path, optional)
           │
           ├─ 2a. JWT decode → user_id
           │
           ├─ 2b. API key (sdlc_live_*) → SHA256 hash → api_keys table → user_id
           │
           ├─ 3. DB lookup (user_id):
           │     │
           │     ├─ Check is_superuser / is_platform_admin → ENTERPRISE
           │     │
           │     └─ Query org memberships → max(Organization.plan)
           │        │
           │        └─ Normalize via TIER_VALUES / TIER_RANK
           │
           └─ 4. Default: LITE (fail-open)
```

**Tier Normalization Map (unified):**

```python
# All known plan strings → canonical tier integer
TIER_VALUES = {
    # ADR-059 canonical names
    "LITE": 1, "STANDARD": 2, "PROFESSIONAL": 3, "ENTERPRISE": 4,
    # Organization.plan values (ADR-047)
    "free": 1, "starter": 2, "pro": 3, "enterprise": 4,
    # Legacy / alias values
    "lite": 1, "standard": 2, "professional": 3,
    "founder": 2,  # grandfathered = STANDARD
}
```

### 2.3 Key Invariants

1. **INV-01**: For any authenticated user, all middleware must resolve the same tier value.
2. **INV-02**: `is_superuser=True` OR `is_platform_admin=True` → tier is always ENTERPRISE (integer 4).
3. **INV-03**: If user has no org membership and no superuser flag → default to LITE (integer 1).
4. **INV-04**: Frontend must display the same tier as the backend enforces (single API source).
5. **INV-05**: API key auth (`sdlc_live_*`) must produce the same tier as JWT auth for the same user (D5).

---

## 3. Expert Corrections

| # | Condition | Impact |
|---|-----------|--------|
| EC-1 | Middleware cannot use `User.effective_tier` (ORM property requires loaded relationships). Must use inline SQL JOIN. | All middleware tier resolution uses raw SQL, not ORM property. |
| EC-2 | `Organization.plan` CHECK constraint allows only 4 values (`free/starter/pro/enterprise`). ADR-059 TIER_VALUES has 6+ strings. Normalization must happen at read time. | Middleware normalizes plan strings to integer tier values after query. |
| EC-3 | `User.effective_tier` property checks `self.organization` (primary) then `self.org_memberships`. The middleware query must replicate this max-tier logic in SQL. | Use `MAX()` aggregate or iterate results in Python. |

---

## 4. Consequences

### 4.1 Positive
- Single source of truth for tier resolution across all code paths
- CEO/admin users always see correct tier in UI
- Extension, CLI, and OTT all receive consistent tier enforcement
- Eliminates the "superuser but FREE tier" bug class permanently

### 4.2 Negative
- `Subscription.plan` is no longer used for feature gating (payment records only)
- Existing middleware SQL queries are replaced (low risk — well-tested)
- TIER_RANK expansion may surface edge cases in `effective_tier` where unknown plan strings previously defaulted to `free`

### 4.3 Risks
- **Migration risk**: If any production code reads `Subscription.plan` for feature gating (beyond TierGate/UsageLimits), it will break. Mitigated by grep audit.
- **Performance**: Adding org JOIN query to middleware adds ~5ms. Mitigated by scope-state fast path and potential Redis cache (future sprint).

---

## 5. Implementation Roadmap

**Sprint 195 (current):**

| Phase | Track | Deliverable | Status |
|-------|-------|-------------|--------|
| Day 1 | A | Fix ConversationFirstGuard P0 (F-02) | DONE |
| Day 1 | A | Fix UsageLimits superuser bypass (F-06) | DONE |
| Day 1 | A | Update misleading comments, lint cleanup | DONE |
| Day 1 | A | Write 21 new tests (19 CFG + 2 UsageLimits) | DONE |
| Day 2 | B | ADR-065 (this document) | DONE |
| Day 2-4 | B | Expand User.effective_tier TIER_RANK | TODO |
| Day 2-4 | B | Refactor TierGate/UsageLimits to org-based resolution | TODO |
| Day 5 | C | Extend /auth/me with effective_tier + organizations | TODO |
| Day 5 | C | Fix useUserTier.ts to call /auth/me | TODO |

**Future sprints:**
- Redis cache for org-tier resolution (performance optimization)
- Admin panel tier management UI (F-11, P3)
- Subscription table cleanup / deprecation documentation

---

## 6. References

- [ADR-047 — Multi-Organization Access Control](ADR-047-Organization-Invitation-System.md)
- [ADR-059 — Enterprise-First Refocus](ADR-059-Enterprise-First-Refocus.md)
- [ADR-064 — Chat-First Facade](ADR-064-Chat-First-Facade-Option-D-Plus.md)
- Sprint 195 Architecture Audit (12 findings F-01 through F-12)
- Sprint 195 PM Review (7/10 → approved with revisions)
