---
sdlc_version: "6.1.1"
document_type: "Functional Requirement"
status: "DRAFT"
sprint: "209"
spec_id: "FR-050"
tier: "STANDARD"
stage: "01 - Planning"
---

# FR-050: OTT Identity Linking

**Version**: 1.0.0
**Status**: DRAFT (Sprint 209 — Pending CTO Review)
**Created**: February 2026
**Sprint**: 209
**Framework**: SDLC 6.1.1
**Epic**: EP-07 Multi-Agent Team Engine
**ADR**: ADR-068 (OTT Identity Linking)
**Depends On**: FR-049 (OTT Workspace), FR-047 (Magic Link OOB Auth)
**Owner**: Backend Team

---

## 1. Overview

### 1.1 Purpose

Enable OTT channel users (Telegram, Zalo) to link their external chat account to an internal SDLC Orchestrator user via email verification. Once linked, governance commands use the resolved User UUID for permission checks, enabling team collaboration in group chats with individual identity.

### 1.2 Problem Being Solved

| Before FR-050 | After FR-050 |
|--------------|-------------|
| Telegram `sender_id` = numeric (e.g., `7023486123`) | Telegram `sender_id` → resolved to User UUID |
| All permission checks fail (UUID expected) | Permission checks use real user identity |
| No way to know WHO sent a command in group chat | Each team member has individual identity |
| `OTT_GATEWAY_USER_ID` env var = single operator only | Multi-user team collaboration via OTT |
| Workspace set fails (membership check needs UUID) | Workspace set works with linked identity |

### 1.3 Business Value

- **Team Collaboration**: Multiple team members work on same project via Telegram group
- **Conversation-First**: Enables CEO directive (Sprint 190) for real team workflows
- **Security**: Individual identity = individual permission checks (CTO approve, Dev submit)
- **Audit Trail**: Every OTT governance action linked to specific user

### 1.4 Scope Boundary

| In scope | Out of scope |
|----------|-------------|
| `/link <email>` + `/verify <code>` + `/unlink` + `/whoami` commands | OAuth 2.0 flow for Telegram (no Telegram OAuth) |
| Email verification code (6-digit, 5-min TTL) | Phone number verification |
| `oauth_accounts` upsert (provider='telegram') | New user registration from OTT |
| Rate limiting (5 per 15 min) | CAPTCHA or advanced anti-spam |
| Identity resolver cache (60-min TTL) | Real-time permission sync |
| Telegram channel | Zalo/Slack/Teams (Sprint 210+) |

---

## 2. Functional Requirements

### 2.1 Account Linking Commands

#### FR-050-01: `/link <email>` — Initiate Account Linking

**Description**: User sends their SDLC account email to initiate linking. System generates a 6-digit verification code, stores it in Redis, and sends it to the email address.

```gherkin
Scenario: Link with valid email
  GIVEN user "7023486123" has not linked their Telegram account
  AND email "dangtt1971@gmail.com" exists in the users table
  WHEN user sends "/link dangtt1971@gmail.com"
  THEN system generates a random 6-digit code (100000-999999)
  AND Redis stores JSON at key "ott:link_code:telegram:7023486123":
      {"code": "847291", "user_id": "b0000000-...-000000000004", "email": "dangtt1971@gmail.com"}
  AND TTL set to 300 seconds (5 minutes)
  AND email sent to "dangtt1971@gmail.com" with subject "SDLC Orchestrator — Verification Code"
  AND bot replies:
      "📧 Verification code sent to dangtt1971@gmail.com
       Reply /verify <code> within 5 minutes."
```

```gherkin
Scenario: Link with unknown email
  GIVEN email "unknown@example.com" does NOT exist in the users table
  WHEN user sends "/link unknown@example.com"
  THEN bot replies:
      "❌ Email not found in SDLC Orchestrator.
       Contact your admin to create an account first."
  AND no Redis key is created
  AND no email is sent
```

```gherkin
Scenario: Link with invalid email format
  GIVEN user sends "/link not-an-email"
  WHEN email format validation fails
  THEN bot replies:
      "❌ Invalid email format. Usage: /link your-email@example.com"
```

```gherkin
Scenario: Link without email argument
  GIVEN user sends "/link" (no email)
  WHEN no argument is provided
  THEN bot replies:
      "ℹ️ Usage: /link <your-sdlc-email>
       Example: /link dangtt1971@gmail.com
       This links your Telegram account to your SDLC Orchestrator user."
```

#### FR-050-02: `/verify <code>` — Complete Account Linking

**Description**: User submits the 6-digit verification code received via email. System validates the code and creates the `oauth_accounts` mapping.

```gherkin
Scenario: Verify with correct code
  GIVEN user "7023486123" has a pending link code in Redis
  AND the stored code is "847291"
  AND the stored user_id is "b0000000-...-000000000004"
  WHEN user sends "/verify 847291"
  THEN system reads and deletes Redis key atomically (GETDEL)
  AND upserts oauth_accounts:
      provider = "telegram"
      provider_account_id = "7023486123"
      user_id = "b0000000-...-000000000004"
      access_token = ""
  AND clears identity cache: "ott:identity:telegram:7023486123"
  AND bot replies:
      "✅ Account linked!
       Name: Endior
       Email: dangtt1971@gmail.com
       You can now use all governance commands."
```

```gherkin
Scenario: Verify with wrong code
  GIVEN user has a pending link code "847291"
  WHEN user sends "/verify 123456"
  THEN bot replies:
      "❌ Wrong verification code. Check your email and try again."
  AND Redis key is NOT deleted (user can retry)
```

```gherkin
Scenario: Verify with expired code
  GIVEN user's link code expired (>5 minutes)
  WHEN user sends "/verify 847291"
  THEN Redis GETDEL returns None (key expired)
  AND bot replies:
      "❌ Verification code expired. Send /link <email> to get a new code."
```

```gherkin
Scenario: Double verify (single-use guarantee)
  GIVEN user already verified successfully (Redis key consumed by GETDEL)
  WHEN user sends "/verify 847291" again
  THEN Redis GETDEL returns None (key already consumed)
  AND bot replies:
      "❌ Verification code expired. Send /link <email> to get a new code."
```

#### FR-050-03: `/unlink` — Remove Account Linking

**Description**: User removes the link between their Telegram account and SDLC user.

```gherkin
Scenario: Unlink a linked account
  GIVEN user "7023486123" has a linked oauth_account (provider='telegram')
  WHEN user sends "/unlink"
  THEN system deletes oauth_accounts row:
      WHERE provider = 'telegram' AND provider_account_id = '7023486123'
  AND clears identity cache: "ott:identity:telegram:7023486123"
  AND bot replies:
      "✅ Account unlinked.
       Use /link <email> to reconnect."
```

```gherkin
Scenario: Unlink when not linked
  GIVEN user "7023486123" has NO linked oauth_account
  WHEN user sends "/unlink"
  THEN bot replies:
      "ℹ️ No linked account found.
       Use /link <email> to connect your Telegram."
```

---

### 2.2 Rate Limiting

#### FR-050-04: `/link` Rate Limiting

**Description**: Prevent abuse of the `/link` command by limiting attempts per sender.

```gherkin
Scenario: Rate limit exceeded
  GIVEN user "7023486123" has sent 5 /link commands in the last 15 minutes
  WHEN user sends a 6th "/link test@example.com"
  THEN bot replies:
      "⚠️ Too many link attempts. Try again in 15 minutes."
  AND no email is sent
  AND no Redis code is created
```

```gherkin
Scenario: Rate limit counter resets
  GIVEN user "7023486123" sent 5 /link commands
  AND 15 minutes have elapsed
  WHEN user sends "/link test@example.com"
  THEN the command proceeds normally (counter reset by TTL expiry)
```

**Implementation**: Redis key `ott:link_rate:{channel}:{sender_id}` → INCR + EXPIRE 900s. Check before processing.

---

### 2.3 Identity Resolution

#### FR-050-05: OTT Identity Resolution Chain

**Description**: Every OTT message resolves `sender_id` to internal User UUID before governance processing.

```gherkin
Scenario: Linked user sends governance command
  GIVEN user "7023486123" has oauth_account: provider='telegram', user_id='uuid-endior'
  WHEN user sends "gate status" in Telegram
  THEN identity resolver checks Redis cache first: "ott:identity:telegram:7023486123"
  AND if cache miss, queries oauth_accounts table
  AND resolves sender_id → "uuid-endior"
  AND passes "uuid-endior" as user_id to governance handler
  AND caches result in Redis with 3600s (60 min) TTL
```

```gherkin
Scenario: Unlinked user sends governance command
  GIVEN user "9999999999" has NO oauth_account for provider='telegram'
  AND OTT_GATEWAY_USER_ID env var is NOT set
  WHEN user sends "gate status"
  THEN identity resolver returns None
  AND bot replies:
      "⚠️ Account not linked. Send /link <email> in private chat to connect your Telegram."
  AND governance command is NOT executed
```

```gherkin
Scenario: UUID sender_id passthrough (web/CLI user)
  GIVEN sender_id is "b0000000-0000-0000-0000-000000000004" (already a UUID)
  WHEN identity resolver is called
  THEN returns the UUID as-is (fast path, no DB lookup)
```

```gherkin
Scenario: OTT_GATEWAY_USER_ID fallback (self-hosted single operator)
  GIVEN user "7023486123" has NO oauth_account
  AND OTT_GATEWAY_USER_ID = "b0000000-0000-0000-0000-000000000004"
  WHEN user sends any governance command
  THEN identity resolver returns "b0000000-0000-0000-0000-000000000004"
  AND governance command uses this user_id
```

#### FR-050-06: Unlinked User Workspace Denial

**Description**: Unlinked users cannot access workspace (project names may be sensitive).

```gherkin
Scenario: Unlinked user tries /workspace set
  GIVEN user "9999999999" has NO linked account (sender_id is not UUID)
  WHEN user sends "/workspace set SDLC-Orchestrator"
  THEN resolve_project_by_name() returns empty matches (UUID validation fails)
  AND bot replies:
      "❌ Project 'SDLC-Orchestrator' not found.
       ⚠️ Link your account first: /link <email>"
```

---

### 2.4 Identity Status

#### FR-050-08: `/whoami` — Display Linked Identity Status

**Description**: User checks whether their Telegram account is linked and, if so, which SDLC user it is linked to. This is a read-only, zero-side-effect command available to all users (linked or unlinked).

```gherkin
Scenario: Whoami for linked user
  GIVEN user "7023486123" has oauth_account: provider='telegram', user_id='b0000000-...-000000000004'
  AND the user record has full_name="Endior" and email="dangtt1971@gmail.com"
  WHEN user sends "/whoami"
  THEN bot replies:
      "🔗 Linked
       Name: Endior
       Email: dangtt1971@gmail.com
       User ID: b0000000-...0004"
```

```gherkin
Scenario: Whoami for unlinked user
  GIVEN user "9999999999" has NO linked oauth_account for provider='telegram'
  WHEN user sends "/whoami"
  THEN bot replies:
      "🔗 Not linked
       Channel: telegram
       Sender ID: 9999999999
       Use /link <email> to connect your SDLC account."
```

```gherkin
Scenario: Whoami for linked but user deleted
  GIVEN user "7023486123" has oauth_account mapping but the target user record was deleted
  WHEN user sends "/whoami"
  THEN bot replies a warning that the user record was not found
  AND suggests "/unlink" followed by "/link" to re-link
```

---

### 2.5 Group Chat Identity Isolation

#### FR-050-09: Per-User Identity in Group Chat

**Description**: In a Telegram group, each member's commands resolve to their individual identity.

```gherkin
Scenario: Two users in same group, different permissions
  GIVEN group chat_id = "-1001234567890" with workspace "SDLC-Orchestrator"
  AND user_A (sender_id "111") is linked to CTO (role: owner)
  AND user_B (sender_id "222") is linked to Dev (role: member)
  WHEN user_A sends "/approve G-Sprint"
  THEN identity resolves "111" → CTO UUID → approve succeeds (magic link sent)
  WHEN user_B sends "/approve G-Sprint"
  THEN identity resolves "222" → Dev UUID → approve denied (requires 'approver' role)
```

---

## 3. Non-Functional Requirements

| Requirement | Target |
|-------------|--------|
| Verification code length | 6 digits (100000–999999) |
| Code TTL | 300 seconds (5 minutes) |
| Code single-use | Enforced via Redis GETDEL (atomic read+delete) |
| Identity cache TTL | 3600 seconds (60 minutes) |
| Rate limit: /link | Max 5 per 15 minutes per sender_id |
| Email delivery | Via `asyncio.to_thread(send_email)` — non-blocking |
| Identity resolution latency | <50ms (cache hit), <200ms (DB lookup) |
| Channel-agnostic keys | `{channel}:{sender_id}` namespace |

---

## 4. File Locations

| File | Purpose | LOC |
|------|---------|-----|
| `backend/app/services/agent_bridge/ott_link_handler.py` | NEW — /link, /verify, /unlink, /whoami handlers | ~230 |
| `backend/app/services/agent_bridge/ott_identity_resolver.py` | FIX — import path + TTL upgrade | ~10 |
| `backend/app/services/agent_bridge/ai_response_handler.py` | MODIFY — identity resolution + routing | ~40 |
| `backend/app/services/agent_bridge/workspace_service.py` | VERIFY — unlinked deny behavior | ~5 |
| `backend/alembic/versions/s209_001_oauth_ott_linking.py` | NEW — access_token nullable + UniqueConstraint | ~30 |

---

## 5. Dependencies

- **OAuthAccount model**: `backend/app/models/user.py:425+` — provider, provider_account_id, user_id, access_token
- **Email service**: `backend/app/services/email_service.py` — `send_email()` (sync, requires `asyncio.to_thread`)
- **Redis client**: `backend/app/utils/redis.py` — `get_redis_client()`
- **DB session**: `backend/app/db/session.py` — `AsyncSessionLocal`
- **FR-049**: OTT Workspace Context — workspace commands depend on resolved identity
- **FR-047**: Magic Link OOB Auth — pattern reference for single-use tokens
- **ADR-067**: OTT Workspace — Redis key naming convention (`ott:{service}:{channel}:{id}`)
- **ADR-068**: OTT Identity Linking — locked decisions for this FR
