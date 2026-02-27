---
sdlc_version: "6.1.1"
document_type: "Sprint Plan"
status: "IN_PROGRESS"
sprint: "209"
spec_id: "SPRINT-209"
tier: "STANDARD"
stage: "04 - Build"
---

# Sprint 209 — OTT Identity + Team Collaboration

**Sprint Duration**: Feb 26–28, 2026 (3 working days P0+P1, 5 days with P2)
**Sprint Goal**: Enable team collaboration via Telegram group chat with identity-linked permissions — `/link`, `/verify`, `/unlink` commands + identity resolver integration
**Status**: IN PROGRESS
**Priority**: P0 (Identity blocker) + P1 (Security + UX)
**Framework**: SDLC 6.1.1
**Previous Sprint**: [Sprint 208 — Pre-Release Hardening](SPRINT-208-RELEASE-HARDENING.md)
**Sprint Close**: [SPRINT-209-CLOSE.md](SPRINT-209-CLOSE.md) *(to be created at close)*
**Release Target**: v1.2.0 — Team Collaboration via OTT
**ADR**: [ADR-068 — OTT Identity Linking](../../02-design/01-ADRs/ADR-068-OTT-Identity-Linking.md)
**FR**: [FR-050 — OTT Identity Linking](../../01-planning/03-Functional-Requirements/FR-050-OTT-Identity-Linking.md)
**User Story**: [Team Collaboration Flow](../../01-planning/07-User-Stories/Team-Collaboration-Flow.md) (US-COLLAB-001)
**Reviewed By**: Architect (APPROVED w/ revisions) + CTO (APPROVED w/ revisions)

---

## Sprint 209 Goal

Sprint 208 closed the Pre-Release Hardening milestone. Dogfooding on Telegram revealed a **Day 1 blocker**: Telegram sends numeric `sender_id` (e.g., `7023486123`) but all governance commands expect internal User UUID. Without identity resolution, every permission-gated OTT command fails silently.

**P0 Blockers**:
1. No mechanism to link Telegram account → SDLC user (`/link` + `/verify`)
2. `ott_identity_resolver.py` has wrong import path + no DB session passed
3. `OAuthAccount.access_token` is `nullable=False` — OTT linking has no OAuth token → INSERT fails
4. No UniqueConstraint on `(provider, provider_account_id)` — duplicates possible

**P1 Security**:
5. Unlinked users can set workspace and see project names (Track C security fix)
6. No rate limiting on `/link` (spam vector)

**P1 UX**:
7. No `/unlink` command (wrong email recovery)
8. Identity cache TTL too short (5 min → 60 min)

---

## CRITICAL SETUP — BotFather Group Privacy

**MUST complete before group chat testing (Track D)**:
```
BotFather → /setprivacy → @SdlcOrchestratorbot → Disable
```
Without this, bot only sees `/commands` in groups, not free-text messages.

---

## Day Timeline (3 Working Days — P0+P1)

| Day | Time | Block | Track |
|-----|------|-------|-------|
| 1 | 09:00–09:30 | Track A-DB: Alembic migration | `s209_001_oauth_ott_linking.py` |
| 1 | 09:30–10:00 | Track B-1: Fix `ott_identity_resolver.py` | Import path + TTL |
| 1 | 10:00–13:00 | Track A: `ott_link_handler.py` | `/link` + `/verify` + `/unlink` + rate limiting |
| 2 | 09:00–10:30 | Track B-2: Integrate identity resolver | `ai_response_handler.py` modification |
| 2 | 10:30–11:00 | Track C: Deny unlinked workspace access | `ai_response_handler.py` guard logic |
| 2 | 11:00–11:30 | Track A-2: Route `/link`, `/verify`, `/unlink` | `ai_response_handler.py` routing |
| 3 | 09:00–12:00 | Track E: Tests | 42 test cases (27 link + 15 identity) |
| 3 | 12:00–12:30 | Regression guard | Full test suite run |
| 3 | 12:30–13:00 | Rebuild staging + E2E verification | Docker rebuild + Telegram testing |

**Total estimated**: ~12 hours coding + 3 hours testing/docs = **3 working days**

---

## Sprint 209 Backlog

### Track A-DB — P0: Alembic Migration (~30 min) ✅

| ID | Item | Est | Status |
|----|------|-----|--------|
| ADB1 | `access_token` column: `nullable=False` → `nullable=True, server_default=''` | 10 min | ✅ DONE |
| ADB2 | UniqueConstraint on `(provider, provider_account_id)` with pre-dedup | 10 min | ✅ DONE |
| ADB3 | Verify migration runs cleanly on staging DB | 10 min | ✅ DONE |

**New file**: `backend/alembic/versions/s209_001_oauth_ott_linking.py`
- Revision: `s209_001`, revises: `s207_001`
- Deduplicates existing rows (keeps newest) before adding UniqueConstraint
- Downgrade implemented: drops constraint + restores NOT NULL

**Why P0**: Without ADB1, `OAuthAccount` INSERT raises `IntegrityError` (access_token NOT NULL). Without ADB2, duplicate `/link` creates multiple rows → `scalar_one_or_none()` raises `MultipleResultsFound`.

**Schema change**:
```python
# ADB1: access_token nullable for OTT linking (no OAuth token)
op.alter_column('oauth_accounts', 'access_token',
    existing_type=sa.String(512),
    nullable=True,
    server_default='')

# ADB2: Prevent duplicate provider+account linking
op.create_unique_constraint(
    'uq_oauth_provider_account',
    'oauth_accounts',
    ['provider', 'provider_account_id'])
```

---

### Track A — P0: OTT Link Handler (~3 hours) ✅

| ID | Item | Est | Status |
|----|------|-----|--------|
| A1 | `/link <email>` — email lookup + 6-digit code + Redis store + email send | 60 min | ✅ DONE |
| A2 | `/verify <code>` — GETDEL atomic single-use + oauth_accounts upsert + cache clear | 45 min | ✅ DONE |
| A3 | `/unlink` — oauth_accounts delete + cache clear | 20 min | ✅ DONE |
| A4 | `/whoami` — show identity binding status (linked/unlinked/deleted) | 15 min | ✅ DONE |
| A5 | Rate limiting — max 5 `/link` per 15 min per sender (Redis INCR + EXPIRE) | 15 min | ✅ DONE |
| A6 | Route `/link`, `/verify`, `/unlink`, `/whoami` in `ai_response_handler.py` | 30 min | ✅ DONE |

**New file**: `backend/app/services/agent_bridge/ott_link_handler.py` (~230 LOC)

**Implementation details**:
- `handle_link_command()` — email regex validation, user lookup (case-insensitive, `is_active` check), 6-digit code via `random.SystemRandom`, Redis 300s TTL, `asyncio.to_thread(send_email)` (non-blocking)
- `handle_verify_command()` — GET to peek (allows retry on wrong code), atomic GETDEL on correct code (FR-050-02 single-use guarantee), Redis <6.2 fallback to DELETE, upserts `OAuthAccount` with `access_token=""`, clears identity cache
- `handle_unlink_command()` — deletes `OAuthAccount` row, clears identity cache, returns info if no link exists
- `handle_whoami_command()` — shows linked identity (name, email, truncated UUID) or unlinked status with /link hint (Team Collaboration Flow Section 7.3)
- Rate limit: Redis key `ott:link_rate:{channel}:{sender_id}`, INCR + EXPIRE 900s, max 5

**Key design decisions** (from ADR-068):
- `asyncio.to_thread(send_email, ...)` — email_service is sync (smtplib), must not block event loop
- Import `OAuthAccount` from `app.models.user` — NOT `app.models.oauth_account` (file doesn't exist)
- Redis key: `ott:link_code:{channel}:{sender_id}` — channel-agnostic for all OTT channels
- `access_token=""` — empty string, not NULL (future-proof for OAuth providers)

---

### Track B — P0: Identity Resolver Fix + Integration (~2 hours) ✅

| ID | Item | Est | Status |
|----|------|-----|--------|
| B1 | Fix import: `app.models.oauth_account` → `app.models.user` | 5 min | ✅ DONE |
| B2 | Upgrade cache TTL: 300s (5 min) → 3600s (60 min) | 5 min | ✅ DONE |
| B3 | Add identity resolution to `ai_response_handler.py` with `AsyncSessionLocal` DB session | 45 min | ✅ DONE |
| B4 | Pass `effective_user_id` to workspace, governance, and agent team handlers | 30 min | ✅ DONE |
| B5 | Unlinked user guard — "Account not linked" reply for governance commands | 20 min | ✅ DONE |

**Modified files**:
- `ott_identity_resolver.py` — import fix (B1), TTL `_CACHE_TTL = 3600` (B2), docstring updated to D-068-01
- `ai_response_handler.py` — identity resolution at line 447 (B3), `effective_user_id` passthrough (B4), `_is_unlinked` guard (B5)

**Integration in `ai_response_handler.py`**:
```python
# Line 447: Identity resolution (after _extract_chat_context, before any routing)
from app.services.agent_bridge.ott_identity_resolver import resolve_ott_user_id
from app.db.session import AsyncSessionLocal

redis = await get_redis_client()
async with AsyncSessionLocal() as db:
    resolved_user_id = await resolve_ott_user_id(channel, sender_id, redis, db=db)
effective_user_id = resolved_user_id or sender_id

# Line 511: Unlinked detection
_is_unlinked = (effective_user_id == sender_id and not _is_uuid_format(sender_id))
```

Then `effective_user_id` replaces `sender_id` in:
- `execute_workspace_command(user_id=effective_user_id)`
- `execute_governance_action(user_id=effective_user_id)`
- `handle_agent_team_request(sender_id=effective_user_id)`

---

### Track C — P0: Deny Unlinked Workspace Access (~30 min) ✅

| ID | Item | Est | Status |
|----|------|-----|--------|
| C1 | Unlinked denial for governance + multi-agent commands | 15 min | ✅ DONE |
| C2 | Verify OTT_GATEWAY_USER_ID env var path still works | 15 min | ✅ DONE |

**Implementation** (in `ai_response_handler.py`, not separate file):
- Line 542-547: Multi-agent commands → "Account not linked. Send /link..." for unlinked users
- Line 630-636: Governance commands → same denial message
- Free-text AI chat is NOT blocked for unlinked users (by design — chat doesn't require account)

---

### Track D — P1: Group Chat Awareness (Ops task — no code changes) ⏳

| ID | Item | Est | Status |
|----|------|-----|--------|
| D1 | BotFather: `/setprivacy` → Disable for @SdlcOrchestratorbot | 2 min | ⏳ OPS |
| D2 | Document Group Privacy setup in sprint plan (this document) | Done | ✅ DONE |

Architecture already supports group chat:
- `chat_id` = group ID (negative number) → shared workspace
- `sender_id` = individual user ID → individual identity resolution
- No code changes needed — BotFather configuration only

---

### Track E — P0: Tests (~3 hours) ✅

**`test_ott_link_handler.py`** — 31 tests:

| Test Class | FR-050 ID | Coverage |
|------------|-----------|---------|
| `TestE1LinkValidEmail` | E1 | Happy path: code stored in Redis, email sent via `to_thread`, rate counter incremented |
| `TestE2LinkUnknownEmail` | E2 | Unknown email returns error, no Redis store; invalid format skips DB |
| `TestE3VerifyCorrectCode` | E3 | New account created (GETDEL atomic); existing account updated (D-068-03 upsert); identity cache cleared |
| `TestE4VerifyWrongCode` | E4 | Error reply, Redis key NOT deleted (retry allowed), no DB write |
| `TestE5VerifyExpiredCode` | E5 | Redis returns None (expired), error reply with `/link` hint, no DB ops |
| `TestE6DoubleVerify` | E6 | First verify consumes via GETDEL, second verify sees expired (FR-050-02) |
| `TestE11Unlink` | E11 | Success case, no-link-found case, DB error triggers rollback |
| `TestE12RateLimiting` | E12 | 6th attempt blocked, 5th allowed, first sets 15-min TTL |
| `TestInputValidation` | — | Empty args, non-digit code, 5-digit, 7-digit all return usage errors |
| `TestWhoami` | — | Linked user info, unlinked hint, deleted-user warning, DB error handling |

**`test_ott_identity_resolver.py`** — 15 tests:

| Test | FR-050 ID | Coverage |
|------|-----------|---------|
| `test_e7_resolve_via_oauth_accounts` | E7 | DB hit → UUID returned and cached |
| `test_e7_cached_result_returns_without_db_lookup` | E7+ | Redis cache hit skips DB |
| `test_e8_resolve_via_env_var_fallback` | E8 | No DB match + env var → uses env var |
| `test_e8_env_var_non_uuid_ignored` | E8+ | Non-UUID env var is skipped → returns None |
| `test_e9_no_mapping_returns_none` | E9 | No DB + no env var → None + `"__none__"` cached |
| `test_e9_cached_negative_returns_none` | E9+ | `"__none__"` sentinel → None without DB |
| `test_e9_empty_sender_id_returns_none` | E9 | Empty sender returns None immediately |
| `test_e9_no_db_session_no_env_returns_none` | E9 | db=None + no env → None |
| `test_e10_uuid_sender_id_passthrough` | E10 | UUID sender bypasses Redis + DB entirely |
| `test_e10_uuid_passthrough_cli_channel` | E10+ | Works for any channel |
| `test_e13_group_chat_different_senders` | E13 | Two senders → two independent lookups and cache keys |
| `test_e13_same_sender_different_channels` | E13+ | Same sender_id on different channels → different identities |
| `test_redis_get_error_falls_through_to_db` | error | Redis failure → falls through to DB |
| `test_db_error_falls_through_to_env_var` | error | DB error → falls through to env var |
| `test_cache_setex_error_ignored` | error | Cache write failure does not propagate |

**Total: 46 tests** (plan originally estimated 13 — actual coverage exceeds spec; +4 /whoami tests from PM Review)

---

### Track F — P2: Admin OTT Link Management (Deferred to Sprint 210)

| ID | Item | Est | Status |
|----|------|-----|--------|
| F1 | `GET /api/v1/admin/ott-links` — list linked accounts | 40 min | ⏳ Sprint 210 |
| F2 | `DELETE /api/v1/admin/ott-links/{id}` — admin unlink | 40 min | ⏳ Sprint 210 |

**Priority**: P2 — deferred to Sprint 210.

---

## Definition of Done — Sprint 209

- [x] Alembic migration `s209_001` — `access_token` nullable + UniqueConstraint + dedup
- [x] `ott_link_handler.py` — `/link`, `/verify`, `/unlink`, `/whoami` with rate limiting (~230 LOC)
- [x] `ott_identity_resolver.py` — import fix (`app.models.user`) + TTL 3600s (60 min)
- [x] `ai_response_handler.py` — identity resolution with `AsyncSessionLocal` + `effective_user_id`
- [x] Unlinked users denied governance + multi-agent access (`_is_unlinked` guard)
- [x] `/link` sends 6-digit code to email via `asyncio.to_thread(send_email)`
- [x] `/verify` upserts `oauth_accounts` with `access_token=""`
- [x] `/unlink` deletes oauth_accounts + clears identity cache
- [x] Rate limiting: max 5 `/link` per 15 min per sender (Redis INCR + EXPIRE)
- [x] 46/46 Sprint 209 tests passing (31 link handler + 15 identity resolver)
- [x] Team-Collaboration-Flow.md documented (US-COLLAB-001)
- [ ] 310+ regression guards passing | 0 regressions
- [ ] BotFather Group Privacy OFF for @SdlcOrchestratorbot
- [ ] CURRENT-SPRINT.md updated to Sprint 209

---

## Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Email delivery fails (SMTP/SendGrid) | Medium | High | `EMAIL_SANDBOX_MODE=true` for dev; fallback to manual code display |
| UniqueConstraint migration fails on existing duplicates | Low | High | Pre-dedup in migration: keeps newest per (provider, account_id) pair |
| Redis GETDEL not available (Redis <6.2) | Low | Medium | Implementation uses atomic GETDEL with AttributeError fallback to DELETE for Redis <6.2 |
| Group Privacy setting forgotten | Medium | High | Documented as CRITICAL SETUP in sprint plan + deployment checklist |

---

## Architecture Notes

### Identity Resolution Flow (Post-Sprint 209)
```
Telegram webhook → ott_gateway.py → ai_response_handler.py
                                          │
                                    ┌─────┴─────┐
                                    │ Extract    │
                                    │ sender_id  │
                                    └─────┬─────┘
                                          │
                                    ┌─────┴──────────┐
                                    │ resolve_ott_    │
                                    │ user_id()       │
                                    │ (Redis cache    │
                                    │  → oauth_accts  │
                                    │  → env var      │
                                    │  → None)        │
                                    └─────┬──────────┘
                                          │
                              ┌───────────┴───────────┐
                              │                       │
                        resolved (UUID)          unlinked (None)
                              │                       │
                     ┌────────┴────────┐        "⚠️ /link first"
                     │                 │        (governance blocked,
                governance OK     workspace OK    AI chat OK)
```

### Multi-Channel Support (Already Complete)

All 4 OTT channels are already implemented via the Protocol Adapter architecture:

| Channel | Tier | Normalizer | Responder | Identity Linking |
|---------|------|-----------|-----------|-----------------|
| Telegram | STANDARD+ | `telegram_normalizer.py` ✅ | `telegram_responder.py` ✅ | Sprint 209 ✅ |
| Zalo | STANDARD+ | `zalo_normalizer.py` ✅ | `zalo_responder.py` ✅ | Ready (same handler) |
| MS Teams | PROFESSIONAL+ | `teams_normalizer.py` ✅ | AI response only | Ready (same handler) |
| Slack | PROFESSIONAL+ | `slack_normalizer.py` ✅ | AI response only | Ready (same handler) |

The identity resolution and link handler are **channel-agnostic** — all Redis keys use `{channel}:{sender_id}` namespace. Adding identity linking for Zalo/Slack/Teams requires NO code changes, only configuring webhooks and normalizers (already done).

**Protocol Adapter** (`protocol_adapter.py`):
- `OrchestratorMessage` frozen dataclass — canonical type for all channels
- Channel Registry pattern — normalizers self-register at import time
- 12 injection pattern filters (ADR-058 Pattern C) applied to all channels

---

## Key Files Summary

| File | Action | LOC | Track | Status |
|------|--------|-----|-------|--------|
| `alembic/versions/s209_001_oauth_ott_linking.py` | NEW | ~45 | A-DB | ✅ |
| `agent_bridge/ott_link_handler.py` | NEW | ~230 | A | ✅ |
| `agent_bridge/ott_identity_resolver.py` | FIX | ~10 | B | ✅ |
| `agent_bridge/ai_response_handler.py` | MODIFY | ~60 | A+B+C | ✅ |
| `agent_bridge/workspace_service.py` | VERIFY | ~0 | C | ✅ |
| `tests/unit/test_ott_link_handler.py` | NEW | ~410 | E | ✅ |
| `tests/unit/test_ott_identity_resolver.py` | NEW | ~200 | E | ✅ |
| **Total (P0+P1)** | | **~955** | | **6/6 tracks DONE** |

**Documentation files**:

| File | Action |
|------|--------|
| `docs/02-design/01-ADRs/ADR-068-OTT-Identity-Linking.md` | NEW |
| `docs/01-planning/03-Functional-Requirements/FR-050-OTT-Identity-Linking.md` | NEW |
| `docs/01-planning/07-User-Stories/Team-Collaboration-Flow.md` | UPDATED (128→347 lines) |

---

## G-Sprint-Close Gate — Sprint 209

- [x] All P0 items implemented and tested (+ /whoami from PM Review)
- [x] 46/46 new tests passing (31 link handler + 15 identity resolver)
- [ ] 310+ regression guards: 0 regressions
- [ ] Staging rebuild successful
- [ ] E2E Telegram test: `/link` → `/verify` → `/workspace set` → governance command
- [ ] PM verification: code audit CLEAN
- [ ] CTO score: >= 9.0/10

---

## Quality Scorecard (CTO Review)

| Dimension | Target | Actual | Notes |
|-----------|--------|--------|-------|
| Zero Mock | 10/10 | 10/10 | Real email via `to_thread`, real DB via `AsyncSessionLocal` |
| Type Hints | 10/10 | 10/10 | Full typing on all new functions |
| AGPL Compliance | 10/10 | 10/10 | No AGPL imports |
| Error Handling | 9/10 | 9/10 | Graceful degradation on Redis/email failures |
| Security | 10/10 | 10/10 | Rate limiting, single-use codes, deny unlinked access |
| Testing | 10/10 | 10/10 | 46 tests covering happy + unhappy + error paths (incl. /whoami + GETDEL atomicity) |

---

*Created*: February 26, 2026
*Next Sprint*: Sprint 210 — Admin OTT Link Management + Zalo OA Notification Channel (tentative)
