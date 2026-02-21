---
sdlc_version: "6.1.0"
document_type: "Sprint Plan"
status: "PROPOSED"
sprint: "181"
spec_id: "SPRINT-181"
tier: "PROFESSIONAL"
stage: "04 - Build"
epic: "EP-07 Multi-Agent Team Engine + Enterprise Infrastructure"
dependencies:
  - "Sprint 180 complete (ADR-059 approved, enterprise-first strategy confirmed)"
  - "ADR-060 approved before Day 4 route activation begins"
---

# Sprint 181 — OTT Channel Foundation + Orphaned Route Activation

**Status**: PROPOSED
**Sprint**: 181
**Duration**: 8 working days (Feb 23 – Mar 4, 2026)
**Budget**: ~$5,120 (64 hrs at $80/hr)
**Risk Level**: MEDIUM
**Stage**: 04 – Build
**Epic**: EP-07 Multi-Agent Team Engine + Enterprise Infrastructure
**Owner**: CTO + Tech Lead

---

## Sprint Goal

Establish the OTT channel abstraction layer (`agent_bridge/`) with Telegram and Zalo
normalizers, activate 7 orphaned routes with correct tier gating, and unify tier naming
(`FREE` → `LITE`) via an Alembic migration. Sprint 181 delivers the OTT foundation that
Sprint 182 (Teams) and Sprint 183 (Slack) will extend without further protocol changes.

---

## Context and Rationale

**What happened in Sprint 180 (ADR-059):**
- Enterprise-first strategy confirmed: gate approvals and agent interactions via OTT channels
  must be tier-gated (STANDARD: Telegram + Zalo; ENTERPRISE: all channels)
- ADR-059 locked the enterprise-first refocus, mandating the `agent_bridge/` abstraction layer
- 7 routes were identified as orphaned (implemented but not registered in `main.py`):
  templates, compliance_framework, nist_govern, nist_manage, nist_map, nist_measure, invitations

**Why now:**
- OTT foundation blocks Sprint 182 (Teams integration) and the Vietnam SME pilot
- Orphaned routes create dead code risk and false API surface in the OpenAPI docs
- Tier naming inconsistency (`FREE` vs `LITE`) creates confusion in billing logic and tier gates

---

## P0 Deliverables — OTT Foundation (agent_bridge/)

### Files to Create

```
backend/app/services/agent_bridge/
├── __init__.py
├── protocol_adapter.py        (OrchestratorMessage dataclass + channel dispatcher)
├── telegram_normalizer.py     (Telegram Bot API webhook → OrchestratorMessage)
└── zalo_normalizer.py         (Zalo OA Webhook → OrchestratorMessage)

backend/app/api/routes/
└── ott_gateway.py             (POST /api/v1/channels/{channel}/webhook)

backend/tests/unit/
└── test_protocol_adapter.py   (PA-01 to PA-20 — 20 tests)
```

---

### agent_bridge/__init__.py

Exports the canonical `OrchestratorMessage` type and the `route_to_normalizer` function.
No business logic lives in `__init__.py`.

```python
from backend.app.services.agent_bridge.protocol_adapter import (
    OrchestratorMessage,
    normalize,
    route_to_normalizer,
)

__all__ = ["OrchestratorMessage", "normalize", "route_to_normalizer"]
```

---

### agent_bridge/protocol_adapter.py

**Responsibility**: Canonical message type definition and channel dispatch registry.

**OrchestratorMessage dataclass fields:**

| Field | Type | Description |
|-------|------|-------------|
| `channel` | `str` | Channel identifier: `"telegram"` \| `"zalo"` \| `"teams"` \| `"slack"` |
| `sender_id` | `str` | Channel-specific user identifier (stable across sessions, not display name) |
| `content` | `str` | Sanitized, normalized text content (max 4096 chars) |
| `timestamp` | `datetime` | UTC timestamp of message origin |
| `correlation_id` | `str` | Unique trace ID: `"{channel}_{message_id}"` |
| `metadata` | `dict` | Channel-specific extras (chat_id, thread_id, event_name, etc.) |

**Channel registry**: `dict[str, Callable[[dict], OrchestratorMessage]]`
- Keys: whitelisted channel names (lowercase strings)
- Values: normalizer functions (imported from channel-specific modules)
- Unknown channel raises `ValueError("unsupported channel: {channel}")`

**normalize(raw_payload, channel) function:**
1. Look up channel in the registry
2. Call the matching normalizer function to produce a raw `OrchestratorMessage`
3. Pass `content` through `input_sanitizer.sanitize()` (12 injection patterns, ADR-058 Pattern C)
4. Return the sanitized `OrchestratorMessage`

**route_to_normalizer(channel, payload) function:**
- Wraps `normalize` with structured logging (channel, correlation_id, content_length)
- Raises `ValueError` for unknown channels so the caller can convert to HTTP 400

---

### agent_bridge/telegram_normalizer.py

**Responsibility**: Telegram Bot API webhook payload → `OrchestratorMessage`.

**Example Telegram Bot API webhook payload:**

```json
{
  "update_id": 123456,
  "message": {
    "message_id": 789,
    "from": {"id": 111, "first_name": "Nguyen", "username": "nqh_pilot"},
    "chat": {"id": -100456, "type": "group"},
    "date": 1740000000,
    "text": "@coder review the auth module"
  }
}
```

**Field mappings to OrchestratorMessage:**

| OrchestratorMessage field | Telegram source |
|--------------------------|-----------------|
| `channel` | `"telegram"` (hardcoded constant) |
| `sender_id` | `message.from.id` (int, cast to str) |
| `content` | `message.text` (required field; ValueError if absent) |
| `timestamp` | `datetime.utcfromtimestamp(message.date)` |
| `correlation_id` | `f"telegram_{message.message_id}"` |
| `metadata` | `{"chat_id": message.chat.id, "chat_type": message.chat.type, "update_id": update_id}` |

**Edge cases handled:**
- Missing top-level `message` key → `ValueError("telegram payload missing message")`
- Missing `text` field inside message → `ValueError("telegram message has no text")`
- `from.id` absent (channel posts without sender) → `sender_id = "channel_post"`

---

### agent_bridge/zalo_normalizer.py

**Responsibility**: Zalo OA (Official Account) webhook payload → `OrchestratorMessage`.

**Example Zalo OA webhook payload:**

```json
{
  "eventName": "user_send_text",
  "timestamp": 1740000000000,
  "sender": {"id": "zalo_user_abc123"},
  "recipient": {"id": "oa_id_456"},
  "message": {"text": "approve G3 for project omega"}
}
```

**Field mappings to OrchestratorMessage:**

| OrchestratorMessage field | Zalo source |
|--------------------------|-------------|
| `channel` | `"zalo"` (hardcoded constant) |
| `sender_id` | `sender.id` |
| `content` | `message.text` |
| `timestamp` | `datetime.utcfromtimestamp(timestamp / 1000)` (Zalo timestamps are milliseconds) |
| `correlation_id` | `f"zalo_{timestamp}_{sender.id}"` |
| `metadata` | `{"event_name": eventName, "recipient_id": recipient.id}` |

**Edge cases handled:**
- `eventName != "user_send_text"` → `ValueError(f"unsupported zalo event: {eventName}")`
- Missing `message.text` → `ValueError("zalo payload missing message text")`
- Zalo timestamp is in milliseconds — divide by 1000 before `datetime.utcfromtimestamp()`

---

### api/routes/ott_gateway.py

**Endpoint:** `POST /api/v1/channels/{channel}/webhook`

**Request handling steps:**
1. Validate `channel` path parameter against whitelist `{"telegram", "zalo"}` — return 400 if unknown
2. Parse raw JSON body as `dict`
3. Call `route_to_normalizer(channel, payload)` — returns `OrchestratorMessage` or raises `ValueError`
4. Forward `OrchestratorMessage` to agent team engine via `message_queue.enqueue()`
5. Return `HTTP 200` with `{"status": "accepted", "correlation_id": msg.correlation_id}`

**Security controls on this endpoint:**
- No JWT authentication required (Telegram and Zalo cannot include auth headers in webhooks)
- HMAC signature verification per channel (configurable via `OTT_HMAC_ENABLED` env var; default false in dev)
- Rate limit: 200 req/min per source IP (token bucket algorithm, Redis-backed)
- Input sanitization applied inside `route_to_normalizer` (12 injection patterns from ADR-058)

**Error response table:**

| Condition | HTTP Status | Body |
|-----------|-------------|------|
| Unknown channel | 400 | `{"error": "unsupported channel: {channel}"}` |
| HMAC mismatch | 403 | `{"error": "webhook signature invalid"}` |
| Missing required fields | 422 | `{"error": "{field} required"}` |
| Agent engine unavailable | 503 | `{"error": "agent engine unavailable", "retry_after": 30}` |

---

### Test Suite: test_protocol_adapter.py (PA-01 to PA-20)

| Test ID | Description | Expected Result |
|---------|-------------|-----------------|
| PA-01 | Telegram valid text message | OrchestratorMessage with `telegram_789` correlation_id |
| PA-02 | Telegram channel post (no from.id) | sender_id equals `"channel_post"` |
| PA-03 | Telegram missing text field | ValueError raised |
| PA-04 | Telegram missing top-level message key | ValueError raised |
| PA-05 | Telegram Unix timestamp converts to UTC datetime | correct UTC datetime object |
| PA-06 | Zalo user_send_text event | OrchestratorMessage with zalo prefix in correlation_id |
| PA-07 | Zalo unsupported event type (e.g. follow) | ValueError raised |
| PA-08 | Zalo missing message.text | ValueError raised |
| PA-09 | Zalo millisecond timestamp converts to datetime | correct UTC datetime object |
| PA-10 | Zalo correlation_id format | matches `f"zalo_{ts}_{sender_id}"` |
| PA-11 | Unknown channel name passed to dispatcher | ValueError "unsupported channel" |
| PA-12 | Content containing injection pattern | injection pattern stripped by sanitizer |
| PA-13 | Telegram metadata fields populated | chat_id, chat_type, update_id all present |
| PA-14 | Zalo metadata fields populated | event_name, recipient_id all present |
| PA-15 | OrchestratorMessage is a Python dataclass | `dataclasses.is_dataclass()` returns True |
| PA-16 | normalize() and route_to_normalizer() produce identical output | outputs are equal |
| PA-17 | Empty string content raises guard | ValueError or ValueError equivalent |
| PA-18 | Content over 4096 chars truncated | truncated to 4096 chars with marker suffix |
| PA-19 | Telegram group message sets correct chat_type | `metadata["chat_type"] == "group"` |
| PA-20 | Channel registry accepts dynamically added normalizer | test_channel normalizer produces valid OrchestratorMessage |

---

## P0 Deliverables — Orphaned Route Activation (7 Routes)

### Current State

The following routers exist in `backend/app/api/routes/` but are NOT registered in
`backend/app/main.py`. They return HTTP 404 for all requests despite being fully implemented.

| Router File | Intended Prefix | Tier | Day | Blocking Issue |
|------------|-----------------|------|-----|----------------|
| `templates.py` | `/api/v1/templates` | CORE (public) | 4 | Rate-limit not configured |
| `compliance_framework.py` | `/api/v1/compliance` | ENTERPRISE | 5 | Missing tier gate dependency |
| `nist_govern.py` | `/api/v1/nist/govern` | ENTERPRISE | 4 | Missing tier gate dependency |
| `nist_manage.py` | `/api/v1/nist/manage` | ENTERPRISE | 5 | Missing tier gate dependency |
| `nist_map.py` | `/api/v1/nist/map` | ENTERPRISE | 4 | Missing tier gate dependency |
| `nist_measure.py` | `/api/v1/nist/measure` | ENTERPRISE | 5 | Missing tier gate dependency |
| `invitations.py` | `/api/v1/invitations` | ENTERPRISE | 6 | Sync Session blocks async loop |

### Router Registration Block in main.py

Each router is added in the Sprint 181 P0 registration block of `main.py`:

```python
# --- OTT Gateway (Sprint 181) ---
from backend.app.api.routes.ott_gateway import router as ott_gateway_router
app.include_router(ott_gateway_router, prefix="/api/v1")

# --- Templates (CORE public endpoint, rate-limited at 100 req/min) ---
from backend.app.api.routes.templates import router as templates_router
app.include_router(templates_router, prefix="/api/v1")

# --- Enterprise: Compliance Framework + NIST Suite ---
from backend.app.api.routes.compliance_framework import router as compliance_router
from backend.app.api.routes.nist_govern import router as nist_govern_router
from backend.app.api.routes.nist_manage import router as nist_manage_router
from backend.app.api.routes.nist_map import router as nist_map_router
from backend.app.api.routes.nist_measure import router as nist_measure_router
app.include_router(compliance_router, prefix="/api/v1")
app.include_router(nist_govern_router, prefix="/api/v1")
app.include_router(nist_manage_router, prefix="/api/v1")
app.include_router(nist_map_router, prefix="/api/v1")
app.include_router(nist_measure_router, prefix="/api/v1")

# --- Invitations (ENTERPRISE; async Session fix applied in Sprint 181) ---
from backend.app.api.routes.invitations import router as invitations_router
app.include_router(invitations_router, prefix="/api/v1")
```

### ENTERPRISE Tier Gate Pattern

All 5 NIST routes and `compliance_framework.py` use the standard `require_enterprise_tier`
dependency injected into each handler:

```python
from backend.app.api.dependencies import require_enterprise_tier

@router.get("/nist/govern/profiles")
async def list_govern_profiles(
    _tier: None = Depends(require_enterprise_tier),
    db: AsyncSession = Depends(get_db),
) -> list[GovernProfileResponse]:
    ...
```

`require_enterprise_tier` raises `HTTP 402 Payment Required` for LITE and STANDARD
tier users with body: `{"error": "ENTERPRISE tier required", "upgrade_url": "/billing/upgrade"}`.

### templates.py — Public CORE Endpoint

`templates.py` is a PUBLIC endpoint with no authentication requirement. It serves a
sanitized template listing used by the onboarding wizard and public landing pages.

Security controls applied at the `templates.py` router level:
- Rate limit: 100 req/min per IP (token bucket, Redis-backed)
- GET operations only — no write operations permitted on the public endpoint
- Response filtered: internal metadata fields stripped before serialization
- Output sanitized: PII stripped from all template example fields

### invitations.py — Async Session Fix

**Root cause:** `invitations.py` imports `Session` from `sqlalchemy.orm` (synchronous) and
uses it as a dependency inside async FastAPI route handlers. This blocks the event loop and
violates the p95 <100ms latency budget.

**Fix scope for Sprint 181 (Day 6 only):**

```python
# Before (sync — blocks event loop)
from sqlalchemy.orm import Session

@router.post("/invitations")
def create_invitation(db: Session = Depends(get_db)):
    result = db.execute(...)    # blocks

# After (async — correct for FastAPI)
from sqlalchemy.ext.asyncio import AsyncSession

@router.post("/invitations")
async def create_invitation(db: AsyncSession = Depends(get_async_db)):
    result = await db.execute(...)   # non-blocking
```

All `db.execute()`, `db.commit()`, `db.refresh()`, and `db.scalar()` calls receive `await`.
URL prefix corrected to `/api/v1` if not already set.
Business logic changes are deferred to Sprint 182.

**Verification:**
```bash
python -m pytest backend/tests/unit/test_invitations.py -v
# Target: 0 sync Session warnings or errors
```

---

## P1 Deliverables — Tier Naming Unification

### Problem Statement

`SubscriptionPlan.FREE` is used in `subscription.py` and related files, but the SDLC 6.1.0
4-Tier Classification uses the name `LITE` (LITE / STANDARD / PROFESSIONAL / ENTERPRISE).
This inconsistency causes billing code to mix `free` and `lite`, making tier-gate logic
unpredictable and creating confusion in API response bodies.

**Note:** The FOUNDER billing plan name remains within STANDARD tier. Only the `free`/`FREE`
enum value is renamed to `lite`/`LITE`.

### Code Changes Required

**subscription.py — enum value rename:**

```python
# Before
class SubscriptionPlan(str, Enum):
    FREE = "free"
    STANDARD = "standard"
    PROFESSIONAL = "professional"
    ENTERPRISE = "enterprise"

# After
class SubscriptionPlan(str, Enum):
    LITE = "lite"           # Renamed from FREE. FOUNDER stays within STANDARD.
    STANDARD = "standard"
    PROFESSIONAL = "professional"
    ENTERPRISE = "enterprise"
```

**tier_approval.py** — if `TierLevel.FREE` exists, rename to `TierLevel.LITE`.

**Grep sweep to find all remaining references before migration:**
```bash
grep -rn "SubscriptionPlan\.FREE\|plan.*free\|tier.*free" backend/app/ --include="*.py"
```

### Alembic Migration: s181_001_tier_naming_lite.py

```python
"""Rename subscription_plan_enum value FREE to LITE

Revision ID: s181_001
Revises: s178_001
Create Date: 2026-02-23

This migration renames the PostgreSQL enum value from 'free' to 'lite'
to match the SDLC 6.1.0 4-Tier Classification naming standard.
ALTER TYPE RENAME VALUE is safe — preserves all existing rows.
"""
from alembic import op


def upgrade() -> None:
    op.execute("ALTER TYPE subscription_plan_enum RENAME VALUE 'free' TO 'lite'")


def downgrade() -> None:
    op.execute("ALTER TYPE subscription_plan_enum RENAME VALUE 'lite' TO 'free'")
```

File name: `backend/alembic/versions/s181_001_tier_naming_lite.py`
Character count: 39 characters — within the 60-char SDLC 6.1.0 limit.

**Testing protocol (must complete all 3 steps before marking AC-181-10 done):**
```bash
alembic upgrade s181_001    # Step 1: apply migration on staging
alembic downgrade -1        # Step 2: verify downgrade is clean
alembic upgrade s181_001    # Step 3: re-apply and verify row count unchanged
```

---

## Daily Schedule

### Day 1 (Feb 23) — OrchestratorMessage + Protocol Adapter Core

- Create `backend/app/services/agent_bridge/__init__.py` with exports
- Implement `OrchestratorMessage` dataclass in `protocol_adapter.py` with all 6 fields
- Implement channel registry dict and `route_to_normalizer` dispatcher skeleton
- Wire `input_sanitizer.sanitize()` into the normalize pipeline (reuse Sprint 179 module)
- Write PA-11, PA-12, PA-15, PA-16 (adapter-level tests)
- Target: 4 tests green by EOD

### Day 2 (Feb 24) — Telegram and Zalo Normalizers

- Implement `telegram_normalizer.py` with all 3 documented edge cases
- Implement `zalo_normalizer.py` with millisecond timestamp conversion
- Register both normalizers in the channel registry in `protocol_adapter.py`
- Write PA-01 through PA-10 (normalizer-level tests)
- Target: 10 tests green by EOD

### Day 3 (Feb 25) — OTT Gateway Route + Remaining Tests

- Implement `ott_gateway.py` with `POST /api/v1/channels/{channel}/webhook`
- Add HMAC signature verification for Telegram (`X-Telegram-Bot-Api-Secret-Token` header)
- Add Redis token bucket rate limit: 200 req/min per IP
- Write PA-13, PA-14, PA-17, PA-18, PA-19, PA-20
- Register `ott_gateway_router` in `main.py`
- Target: all 20 PA tests green by EOD

### Day 4 (Feb 26) — templates.py + First NIST Routes Activated

- Register `templates_router` in `main.py` (CORE tier, no auth, rate-limit 100 req/min)
- Verify `templates.py` strips internal metadata from response serialization
- Register `nist_govern_router` and `nist_map_router` (ENTERPRISE gate applied)
- Verify 402 for LITE/STANDARD on both newly activated NIST routes
- Verify 200 for ENTERPRISE test user on both routes
- AC-181-05 verified; AC-181-07 partially verified

### Day 5 (Feb 27) — Remaining NIST Routes + Compliance Framework Activated

- Register `nist_manage_router` and `nist_measure_router` in `main.py`
- Register `compliance_router` in `main.py`
- Verify 402 for LITE/STANDARD on all 5 ENTERPRISE routes
- Verify 200 for ENTERPRISE test user on all 5 routes
- AC-181-06 verified; AC-181-07 fully verified

### Day 6 (Mar 2) — invitations.py Async Fix

- Replace `Session` with `AsyncSession` throughout `invitations.py`
- Add `await` before every `db.execute()`, `db.commit()`, `db.refresh()`, `db.scalar()` call
- Fix URL prefix to `/api/v1` if it differs
- Register `invitations_router` in `main.py`
- Run `test_invitations.py` — zero sync Session errors required
- AC-181-08 verified

### Day 7 (Mar 3) — Tier Naming Unification

- Update `SubscriptionPlan.FREE` to `SubscriptionPlan.LITE` in `subscription.py`
- Run grep sweep; fix all remaining `free` enum references in Python files
- Write `s181_001_tier_naming_lite.py` Alembic migration
- Run 3-step migration testing protocol (upgrade, downgrade, upgrade)
- AC-181-09 and AC-181-10 verified

### Day 8 (Mar 4) — Integration Testing and Sprint Close

- Full API regression: 91 existing endpoints + 7 newly activated routes + 2 OTT routes = 100 endpoints
- Run all 20 PA tests and all 121 existing EP-07 tests
- Verify every AC-181-01 through AC-181-12 criterion with evidence screenshot or log
- Write Sprint 181 Close doc (required within 24h per SDLC 6.1.0 G-Sprint-Close gate)
- CTO sign-off and merge to main

---

## Acceptance Criteria

| ID | Criteria | Priority |
|----|----------|----------|
| AC-181-01 | POST /api/v1/channels/telegram/webhook returns 200 with correlation_id field | P0 |
| AC-181-02 | POST /api/v1/channels/zalo/webhook returns 200 with correlation_id field | P0 |
| AC-181-03 | POST /api/v1/channels/discord/webhook (unknown channel) returns 400 with error message | P0 |
| AC-181-04 | All 7 orphaned routes return 200 (authenticated) or 401 (unauthenticated) — not 404 | P0 |
| AC-181-05 | GET /api/v1/templates accessible without Authorization header | P0 |
| AC-181-06 | GET /api/v1/compliance returns 402 for LITE and STANDARD tier users | P0 |
| AC-181-07 | All NIST routes (govern/manage/map/measure) return 402 for non-ENTERPRISE users | P0 |
| AC-181-08 | invitations.py: pytest test_invitations.py shows zero sync Session warnings or errors | P1 |
| AC-181-09 | SubscriptionPlan.LITE exists in codebase; SubscriptionPlan.FREE absent (grep confirms) | P1 |
| AC-181-10 | Alembic migration s181_001 completes upgrade and downgrade cleanly on staging | P1 |
| AC-181-11 | All 20 PA tests pass (PA-01 to PA-20) with no skips | P0 |
| AC-181-12 | All 121 existing EP-07 tests pass with no regression | P0 |

---

## DoD Checklist (G-Sprint-Close per SDLC 6.1.0)

- [ ] All AC-181-01 through AC-181-12 verified and signed off by Tech Lead
- [ ] 20 new unit tests passing: PA-01 to PA-20 (0 failures, 0 skips)
- [ ] All 121 existing EP-07 tests passing (0 regressions)
- [ ] All 91 existing API endpoint tests passing (0 regressions)
- [ ] Zero sync Session errors in invitations.py (confirmed by test output)
- [ ] ADR-060 approved and referenced before Day 4 route activation starts
- [ ] alembic upgrade s181_001 clean on staging DB
- [ ] alembic downgrade -1 clean on staging DB
- [ ] templates.py rate-limited at 100 req/min (Redis token bucket; not in-memory dict)
- [ ] require_enterprise_tier applied to all 6 ENTERPRISE routes (compliance + 4 NIST)
- [ ] ott_gateway.py HMAC verification enabled for Telegram channel in staging/prod
- [ ] OTT rate limit: 200 req/min per IP via Redis (not in-memory)
- [ ] SubscriptionPlan.FREE absent from all Python files (grep returns zero hits)
- [ ] Sprint 181 Close doc written and committed within 24h of DoD
- [ ] CLAUDE.md Module 7 updated with agent_bridge/ file list

---

## Risk Assessment

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| invitations.py async complexity deeper than Session type | HIGH | MEDIUM | Strictly scope Sprint 181 fix to Session type only; defer business logic to Sprint 182 |
| Telegram Bot API format change (v5 to v6) | LOW | MEDIUM | Version-pin API in integration test fixtures; fail fast on unrecognised top-level keys |
| Tier naming DB migration corrupts existing subscription rows | MEDIUM | HIGH | Run ALTER TYPE RENAME VALUE on staging first; verify SELECT COUNT(*) before and after |
| Orphaned route prefix collides with already-registered route | LOW | LOW | Print full app.routes list before and after each include_router call in CI |
| HMAC verification blocks legitimate OTT webhooks in production | LOW | HIGH | OTT_HMAC_ENABLED defaults to false in dev; set to true only after pilot verification |

---

## Dependencies

| Dependency | Status | Owner |
|------------|--------|-------|
| Sprint 180 complete | REQUIRED | CTO |
| ADR-059 approved (enterprise-first strategy) | COMPLETE | Tech Lead |
| ADR-060 approved (channel abstraction) | REQUIRED before Day 4 | Architect |
| agent_team/input_sanitizer.py (12 patterns, Sprint 179) | COMPLETE | Backend Lead |
| Redis available for rate limiting and pub/sub | COMPLETE (port 6395) | DevOps |
| require_enterprise_tier dependency function | REQUIRED | Backend Lead |

---

## New Files Summary

| File Path | LOC (est.) | Type | Priority |
|-----------|-----------|------|----------|
| services/agent_bridge/__init__.py | 10 | Module init | P0 |
| services/agent_bridge/protocol_adapter.py | 90 | Core logic | P0 |
| services/agent_bridge/telegram_normalizer.py | 60 | Channel normalizer | P0 |
| services/agent_bridge/zalo_normalizer.py | 55 | Channel normalizer | P0 |
| api/routes/ott_gateway.py | 80 | API route | P0 |
| tests/unit/test_protocol_adapter.py | 200 | Unit test suite | P0 |
| alembic/versions/s181_001_tier_naming_lite.py | 25 | DB migration | P1 |

**Total new lines of code**: approximately 520
**Modified files**: main.py (7 router registrations added), subscription.py (FREE → LITE), invitations.py (Session → AsyncSession)

---

## API Surface After Sprint 181

| Endpoint | Method | Auth Required | Tier |
|----------|--------|---------------|------|
| /api/v1/channels/{channel}/webhook | POST | None (HMAC) | ALL |
| /api/v1/templates | GET | None | CORE (public) |
| /api/v1/compliance | GET/POST | JWT | ENTERPRISE |
| /api/v1/nist/govern | GET/POST | JWT | ENTERPRISE |
| /api/v1/nist/manage | GET/POST | JWT | ENTERPRISE |
| /api/v1/nist/map | GET/POST | JWT | ENTERPRISE |
| /api/v1/nist/measure | GET/POST | JWT | ENTERPRISE |
| /api/v1/invitations | GET/POST | JWT | ENTERPRISE |

**Total API endpoint count after Sprint 181**: 91 (existing) + 8 (new or activated) = **99 endpoints**

---

## Traceability

| Artifact | Reference |
|----------|-----------|
| Epic | EP-07 Multi-Agent Team Engine |
| Architecture Decisions | ADR-056 (Multi-Agent Foundation), ADR-058 (ZeroClaw Hardening), ADR-059 (Enterprise-First), ADR-060 (Channel Abstraction) |
| Functional Requirements | FR-037 to FR-044 (EP-07 BDD requirements) |
| Previous Sprint | SPRINT-180-ENTERPRISE-FIRST-REFOCUS.md |
| Next Sprint | SPRINT-182 — Teams Integration (Microsoft Azure AD, PROFESSIONAL tier) |

---

*SDLC Orchestrator Sprint 181 — Production-ready OTT foundation. Zero facade tolerance.*
*"Register it or remove it. Dead code has no place in a governance platform." — CTO*

**Last Updated**: 2026-02-19
**Owner**: CTO + Tech Lead
**Review Gate**: G-Sprint-Close required within 24h of Day 8 DoD completion
