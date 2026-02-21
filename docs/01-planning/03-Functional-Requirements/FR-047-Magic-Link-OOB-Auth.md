---
sdlc_version: "6.1.0"
document_type: "Functional Requirement"
status: "IMPLEMENTED"
sprint: "189"
spec_id: "FR-047"
tier: "PROFESSIONAL"
stage: "01 - Planning"
---

# FR-047: Magic Link Out-of-Band Authentication

**Version**: 1.1.0
**Status**: IMPLEMENTED (Sprint 189 — CTO CONDITIONAL APPROVE 9.4/10)
**Created**: February 2026
**Sprint**: 189
**Framework**: SDLC 6.1.0
**Epic**: EP-08 Chat-First Governance Loop
**ADR**: ADR-064 (D-064-04 Magic Link for OOB auth)
**Owner**: Backend Team

---

## 1. Overview

### 1.1 Purpose

Provide out-of-band (OOB) authentication for gate approval actions initiated via OTT chat channels. OTT platforms (Telegram, Slack, etc.) cannot guarantee identity — a Magic Link forces the user through browser-based SSO before the approval is executed.

### 1.2 Business Value

- Prevents OTT identity spoofing on critical gate approvals
- Compliance: SOC 2 audit trail requires verified identity for governance actions
- Tier flexibility: `requires_oob_auth` is server-driven, not hardcoded to G3/G4 gate types

---

## 2. Functional Requirements

### 2.1 Token Generation

**GIVEN** a gate approval request via chat where `actions.requires_oob_auth == true`
**WHEN** the chat command router processes the request
**THEN** the system SHALL:
1. Generate an HMAC-SHA256 signed token containing: `gate_id`, `action`, `user_id`, `idempotency_key`
2. Store the token payload in Redis with key `magic_link:{signature}` and TTL 300 seconds (5 minutes)
3. Return a Magic Link URL: `{FRONTEND_URL}/auth/magic?token={base64url_encoded_token}`
4. Include the gate name, action, and expiry time in the chat response

### 2.2 Token Validation and Consumption

**GIVEN** a user clicks a Magic Link URL in their browser
**WHEN** the frontend sends the token to the validation endpoint
**THEN** the system SHALL:
1. Decode the base64url token and extract the HMAC signature
2. Verify the HMAC-SHA256 signature using `MAGIC_LINK_SECRET`
3. Look up `magic_link:{signature}` in Redis
4. Verify the token has not been used (`used == false`)
5. Verify the `user_id` in the token matches the currently authenticated browser session
6. If all checks pass: execute the gate action, delete the Redis key (single-use guarantee)
7. If any check fails: return a specific error (expired, already used, wrong user, invalid signature)

### 2.3 Single-Use Guarantee

**GIVEN** a valid Magic Link token
**WHEN** consumed successfully
**THEN** the system SHALL:
1. Delete the Redis key immediately after successful execution
2. Prevent any subsequent use of the same token (Redis key gone → "expired or not found")
3. Record the consumption event in the audit log

### 2.4 Idempotency

**GIVEN** two concurrent clicks on the same Magic Link
**WHEN** both requests arrive at the validation endpoint
**THEN** the system SHALL:
1. Use Redis atomic operations (GET + DELETE) to ensure only one request succeeds
2. The second request receives "Token already used" error
3. The gate approval is executed exactly once

### 2.5 OOB Auth Trigger (Actions Contract Integration)

**GIVEN** a gate approval action where OOB authentication is required
**WHEN** `compute_gate_actions()` evaluates the gate
**THEN** the system SHALL:
1. Set `requires_oob_auth = true` in the GateActionsResponse based on:
   - Gate type (configurable, default: G3+ gates require OOB)
   - Subscription tier (ENTERPRISE tier may require OOB for all gates)
   - Admin configuration override
2. The chat router checks `requires_oob_auth` and generates a Magic Link instead of direct approval
3. The dashboard web UI is NOT affected (browser sessions are already authenticated)

### 2.6 Lightweight Magic Link Page

**GIVEN** a user navigates to the Magic Link URL
**WHEN** the page loads
**THEN** the system SHALL:
1. Display a minimal page: logo + gate name + action + Approve/Reject buttons
2. Require the user to be authenticated (redirect to login if not)
3. Show clear error messages for invalid/expired tokens
4. NOT load the full dashboard — lightweight page only

---

## 3. Non-Functional Requirements

| Requirement | Target |
|-------------|--------|
| Token TTL | 300 seconds (5 minutes) |
| Token signing algorithm | HMAC-SHA256 |
| Single-use enforcement | Atomic Redis GET+DELETE |
| Concurrent approval consistency | Exactly-once execution |
| Page load time | <1 second |
| MAGIC_LINK_SECRET rotation | 90-day rotation via Vault |

---

## 4. File Location

`backend/app/services/agent_team/magic_link_service.py` (~150 LOC)

---

## 5. Dependencies

- `backend/app/utils/redis.py` — async Redis client (A-02: NOT app/core/redis.py)
- `backend/app/core/config.py` — MAGIC_LINK_SECRET setting
- `backend/app/services/gate_service.py` — compute_gate_actions() (requires_oob_auth field)
- `backend/app/schemas/gate.py` — GateActionsResponse schema update
- `backend/app/services/audit_service.py` — audit logging for token events
