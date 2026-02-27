---
sdlc_version: "6.1.1"
document_type: "Architecture Decision Record"
status: "DRAFT"
sprint: "209"
spec_id: "ADR-068"
tier: "STANDARD"
stage: "02 - Design"
owner: "CTO"
---

# ADR-068 — OTT Identity Linking

**Status**: DRAFT (Sprint 209 — Pending CTO Review)
**Date**: February 2026
**Author**: Architect + PM
**Sprint**: Sprint 209
**Framework**: SDLC 6.1.1
**Supersedes**: None
**References**:
- ADR-067 (OTT Workspace Context — Redis key conventions, `{channel}:{chat_id}` pattern)
- ADR-064 (Chat-First Facade — D-064-01: Chat=UX, Control Plane=Truth)
- ADR-056 (Multi-Agent Team Engine — Snapshot Precedence)
- FR-050 (OTT Identity Linking — BDD requirements)
- FR-047 (Magic Link OOB Auth — single-use token pattern reference)

---

## 1. Context

### 1.1 Problem Statement

Sprint 208 dogfooding revealed that **no OTT governance command works** because Telegram sends numeric `sender_id` (e.g., `7023486123`) but all permission checks expect internal User UUID (36-char hyphenated format).

| # | Problem | User Impact |
|---|---------|-------------|
| 1 | **No identity mapping** | Telegram numeric ID → UUID resolution fails → `resolve_project_by_name()` returns empty (UUID validation at line 170) |
| 2 | **Single-operator fallback only** | `OTT_GATEWAY_USER_ID` env var is one UUID for ALL users — no individual identity in group chats |
| 3 | **No linking mechanism** | Users cannot associate their Telegram account with their SDLC user — must be done by admin in DB |
| 4 | **oauth_accounts schema gap** | `access_token` is `NOT NULL` — OTT linking has no OAuth token → INSERT fails with `IntegrityError` |
| 5 | **No dedup on provider+account** | Missing UniqueConstraint on `(provider, provider_account_id)` — double `/link` creates duplicates |

### 1.2 Reference Pattern: EndiorBot Session Identity

EndiorBot (TypeScript, local agent) uses a simpler model — single-user per bot instance:
```typescript
// session-manager.ts — identity = CLI user, no multi-user concern
interface SessionContext {
  userId: string;  // always the local user running the bot
  projectId: string;
}
```

SDLC Orchestrator OTT is fundamentally different: **multi-user group chat** where the bot must distinguish individual identities while sharing workspace context.

### 1.3 Existing Partial Implementation

`ott_identity_resolver.py` was created (Sprint 209 prep) with the correct resolution chain:
```python
async def resolve_ott_user_id(channel, sender_id, redis, db=None):
    # 1. Fast path: sender_id already UUID → passthrough
    # 2. Redis cache: ott:identity:{channel}:{sender_id}
    # 3. oauth_accounts lookup: provider + provider_account_id
    # 4. OTT_GATEWAY_USER_ID env var fallback
    # 5. None (anonymous)
```

**Bugs found during review**:
- Import path `app.models.oauth_account` — file doesn't exist (should be `app.models.user`)
- Cache TTL 300s too short (5 min → 60 min recommended)
- No DB session passed from `ai_response_handler.py` → Priority 1 (oauth_accounts) always skipped

---

## 2. Decision

**Email-based verification linking**: Users link their OTT account to their SDLC user via `/link <email>` + `/verify <code>`. The system sends a 6-digit code to the user's registered email. After verification, `oauth_accounts` row maps `(provider, provider_account_id)` → `user_id`.

**Aligned with ADR-064**: Chat layer provides identity linking UX. Control plane (PostgreSQL `oauth_accounts`) stores the mapping. Redis caches for performance.

**Aligned with ADR-067**: Redis key naming follows `ott:{service}:{channel}:{identifier}` convention.

---

## 3. Locked Decisions

### D-068-01: Identity Resolution Chain (3-Level Priority)

**Decision**:
```
Priority 1: oauth_accounts — provider='{channel}', provider_account_id='{sender_id}'
Priority 2: OTT_GATEWAY_USER_ID env var — single-operator self-hosted fallback
Priority 3: None — anonymous (governance commands blocked, prompt to /link)
```

**Fast path**: If `sender_id` is already UUID format (36 chars, 4 hyphens) → return as-is. This handles web/CLI users whose user_id is already a UUID.

**Rationale**: oauth_accounts is the canonical identity mapping (reuses existing auth infrastructure). Env var fallback supports single-operator self-hosted deployments (no email service needed).

**Implications**:
- Identity resolution runs on EVERY OTT message that hits `ai_response_handler.py`
- Redis cache (60-min TTL) prevents repeated DB queries — amortized cost ~0 after first resolution
- Unlinked users get a clear "link your account" message, not a cryptic permission error

**Cache key**: `ott:identity:{channel}:{sender_id}` → User UUID string (or `"__none__"` for negative cache)

---

### D-068-02: Email Verification Flow (6-Digit Code)

**Decision**:
```
/link <email>
  → Validate email format
  → Rate limit check (max 5 per 15 min per sender)
  → Query users table by email (case-insensitive)
  → Generate random 6-digit code (100000–999999)
  → Store in Redis: ott:link_code:{channel}:{sender_id} → JSON{code, user_id, email}
  → TTL: 300 seconds (5 minutes)
  → Send email via asyncio.to_thread(send_email, ...)
  → Reply with confirmation

/verify <code>
  → Redis GETDEL: ott:link_code:{channel}:{sender_id}
  → Validate code match
  → Upsert oauth_accounts (ON CONFLICT update user_id)
  → Clear identity cache
  → Reply with user info

/whoami
  → Query oauth_accounts: provider={channel}, provider_account_id={sender_id}
  → If linked → fetch user record (full_name, email) → reply with identity details
  → If not linked → reply with channel/sender_id and /link hint
```

**Rationale**:
- 6-digit code is user-friendly (easy to type on mobile)
- 5-minute TTL balances security (short window) vs UX (enough time to check email)
- GETDEL ensures single-use (atomic read + delete)
- Email verification proves ownership of the SDLC account

**Why NOT OAuth 2.0**:
- Telegram does not support standard OAuth 2.0 for bot interactions
- Email verification is simpler, proven pattern (used by Telegram itself for 2FA)
- No external OAuth provider dependency

**Why NOT magic link**:
- Magic links require clicking a URL — awkward in chat flow
- 6-digit code is natural in chat (user types `/verify 847291`)
- Magic link pattern (FR-047) reserved for gate approvals where web context is needed

---

### D-068-03: oauth_accounts Schema Changes

**Decision**: Two schema modifications via Alembic migration `s209_001`:

1. **`access_token` nullable**: `ALTER COLUMN access_token SET DEFAULT '' , SET NOT NULL → nullable=True`
   - OTT linking has no OAuth token — only provider + provider_account_id mapping
   - Empty string `""` used as sentinel (not NULL) for linked OTT accounts
   - Existing OAuth rows (GitHub, Google) unaffected (they have real tokens)

2. **UniqueConstraint**: `UNIQUE (provider, provider_account_id)`
   - Prevents duplicate linking (same Telegram account linked twice)
   - Enables `INSERT ... ON CONFLICT` upsert pattern
   - Documented in model docstring but never created in DDL

**Rationale**: Minimal schema change — reuses existing `oauth_accounts` table instead of creating new `ott_linked_accounts` table (one table for all OAuth/OTT identity mappings).

**Implications**:
- Migration must check for existing duplicates before adding UniqueConstraint
- Downgrade path: drop constraint + revert nullable (no data loss)

---

### D-068-04: Async Email Wrapper

**Decision**: Wrap sync `send_email()` with `asyncio.to_thread()` in `ott_link_handler.py`:
```python
import asyncio
from app.services.email_service import send_email

await asyncio.to_thread(send_email, to_email, subject, html_content)
```

**Rationale**: `email_service.send_email()` uses `smtplib.SMTP` (blocking TCP) or `requests.post()` (blocking HTTP). Calling directly from async context blocks the FastAPI event loop. `asyncio.to_thread()` runs the sync function in a thread pool executor.

**Why NOT rewrite email_service as async**:
- email_service is used by many sync callers (route handlers, invitation flow)
- Rewriting to async would require changes across 5+ call sites
- `to_thread` is the recommended pattern for calling sync I/O from async (Python 3.9+)

---

### D-068-05: Unlinked User Access Denial

**Decision**: Unlinked users (identity resolution returns None) are DENIED access to:
- Workspace set/list/clear (project names may be sensitive)
- All governance commands (gate status, approve, submit evidence, etc.)
- Agent team requests

**Exception**: `OTT_GATEWAY_USER_ID` env var still works as fallback for single-operator mode.

**Rationale** (CTO C1 + Architect P1-3): Workspace names may contain client names, project codes. Allowing unlinked users degraded access is a data leak risk. Better UX: clear "link your account" message.

**Reply for unlinked users**:
```
⚠️ Account not linked. Send /link <email> in private chat to connect your Telegram.
```

---

## 4. Consequences

### 4.1 Positive

- **Team collaboration enabled**: Multiple team members in one Telegram group, each with individual identity
- **Permission isolation**: CTO can approve, Dev cannot — enforced per-user in group chat
- **Audit trail**: Every OTT governance action linked to specific User UUID (not anonymous numeric ID)
- **Channel-agnostic**: `{channel}:{sender_id}` namespace supports Zalo, Slack, MS Teams (Sprint 210+)
- **Reuses existing infrastructure**: oauth_accounts table, email_service, Redis caching

### 4.2 Negative

- **Email dependency**: `/link` requires working email service (mitigated by `EMAIL_SANDBOX_MODE`)
- **DB dependency in OTT path**: `ai_response_handler.py` now needs `AsyncSessionLocal` (first DB access in fire-and-forget OTT handler)
- **60-min cache staleness**: Identity changes (admin unlinks user) take up to 60 min to propagate

### 4.3 Risks

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Email delivery failure | Medium | High | `EMAIL_SANDBOX_MODE=true` for dev; rate-limited retry; manual code fallback |
| Redis unavailable during /link | Low | Medium | Graceful error: "Service temporarily unavailable" |
| Duplicate linking race condition | Low | Low | UniqueConstraint + ON CONFLICT upsert |
| Cache invalidation lag (60 min) | Low | Medium | `/unlink` explicitly clears cache; admin can clear Redis key |

### 4.4 Neutral

- `ai_response_handler.py` gains a DB dependency (was Redis-only) — acceptable for identity resolution (single query, cached)
- oauth_accounts table gains OTT rows alongside OAuth rows — same table, different `provider` values

---

## 5. Implementation Scope

### New Files

| File | Purpose | LOC |
|------|---------|-----|
| `backend/alembic/versions/s209_001_oauth_ott_linking.py` | access_token nullable + UniqueConstraint | ~30 |
| `backend/app/services/agent_bridge/ott_link_handler.py` | /link, /verify, /unlink, /whoami command handlers | ~230 |
| `backend/tests/unit/test_ott_link_handler.py` | Tests E1-E6, E11-E12, E14-E17 (31 tests) | ~410 |
| `backend/tests/unit/test_ott_identity_resolver.py` | Tests E7-E10, E13 (15 tests) | ~200 |

### Modified Files

| File | Change | LOC |
|------|--------|-----|
| `agent_bridge/ott_identity_resolver.py` | Fix import `app.models.user`, TTL 300→3600 | ~10 |
| `agent_bridge/ai_response_handler.py` | Identity resolution with AsyncSessionLocal, effective_user_id passthrough, /link + /whoami routing | ~45 |
| `agent_bridge/workspace_service.py` | Audit log for unlinked user denial (behavior already correct) | ~5 |

### No Changes

| File | Reason |
|------|--------|
| `agent_bridge/telegram_responder.py` | /link, /verify, /unlink NOT in static replies — must fall through to handler |
| `agent_bridge/governance_action_handler.py` | Already receives user_id param — no change needed |
| `agent_bridge/workspace_service.py` (logic) | UUID validation already denies non-UUID user_id |

---

## 6. Test Strategy

| Test ID | Type | Description | Covers |
|---------|------|-------------|--------|
| E1 | Unit | /link valid email → code + Redis + email | FR-050-01 |
| E2 | Unit | /link unknown email → error | FR-050-01 |
| E3 | Unit | /verify correct code → upsert | FR-050-02 |
| E4 | Unit | /verify wrong code → error | FR-050-02 |
| E5 | Unit | /verify expired → error | FR-050-02 |
| E6 | Unit | Double /verify → single-use | FR-050-02 |
| E7 | Unit | Identity resolve oauth match → UUID | FR-050-05 |
| E8 | Unit | Identity resolve env fallback → UUID | FR-050-05 |
| E9 | Unit | Identity resolve no mapping → None | FR-050-05 |
| E10 | Unit | Identity resolve UUID passthrough | FR-050-05 |
| E11 | Unit | /unlink → delete + cache clear | FR-050-03 |
| E12 | Unit | Rate limit → 6th attempt blocked | FR-050-04 |
| E13 | Unit | Group: different sender → different user | FR-050-09 |
| E14 | Unit | /whoami linked user → name + email + UUID | FR-050-08 |
| E15 | Unit | /whoami unlinked user → not linked + /link hint | FR-050-08 |
| E16 | Unit | /whoami linked but user deleted → warning | FR-050-08 |
| E17 | Unit | /whoami DB error → generic error reply | FR-050-08 |

---

## 7. Channel Expansion Roadmap

| Tier | Channel | Sprint | Identity Method |
|------|---------|--------|-----------------|
| STANDARD | Telegram | 209 | `/link` + email verification |
| STANDARD | Zalo OA | 210+ | `/link` + email verification (same flow) |
| PROFESSIONAL | Slack | 212+ | Workspace email auto-match |
| ENTERPRISE | MS Teams | 215+ | Azure AD SSO (automatic — no `/link` needed) |

Architecture (D-068-01) uses `{channel}:{sender_id}` namespace — adding channels requires only:
1. New webhook endpoint + normalizer in `ott_gateway.py`
2. New responder (e.g., `zalo_responder.py`)
3. No changes to identity resolver, workspace, or governance handlers

---

## 8. Review History

| Date | Reviewer | Decision |
|------|----------|---------|
| Feb 2026 | Architect | APPROVED with P0-1/P0-2/P0-3 + P1-1/P1-2/P1-3/P1-4 revisions |
| Feb 2026 | CTO | APPROVED with C1/C2/M1/M2/M3/M4 revisions |
| Feb 2026 | PM | All revisions incorporated into final plan |
