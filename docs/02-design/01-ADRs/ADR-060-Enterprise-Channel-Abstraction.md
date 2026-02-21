---
sdlc_version: "6.1.0"
document_type: "Architecture Decision Record"
status: "PROPOSED"
adr_id: "ADR-060"
title: "Enterprise OTT Channel Abstraction"
date: "2026-02-19"
deciders:
  - "CTO"
  - "Tech Lead"
  - "Architect"
supersedes: null
superseded_by: null
related_adrs:
  - "ADR-056 — Multi-Agent Team Engine Foundation"
  - "ADR-058 — ZeroClaw Best Practice Adoption"
  - "ADR-059 — Enterprise-First Refocus"
related_sprints:
  - "Sprint 181 — OTT Channel Foundation + Orphaned Route Activation"
---

# ADR-060 — Enterprise OTT Channel Abstraction

**Status**: PROPOSED
**Date**: 2026-02-19
**Deciders**: CTO, Tech Lead, Architect
**Supersedes**: None
**Superseded By**: None

---

## Context

ADR-059 (Enterprise-First Refocus, Sprint 180) confirmed that SDLC Orchestrator will
receive gate approval notifications and agent team interactions from multiple OTT
(Over-The-Top messaging) channels. The confirmed channel roadmap is:

- **STANDARD tier**: Telegram + Zalo (Vietnam pilot market, Sprint 181)
- **PROFESSIONAL tier**: Telegram + Zalo (full), Microsoft Teams (Sprint 182), Slack (Sprint 183)
- **ENTERPRISE tier**: All channels with unlimited seats

Each OTT channel uses a different webhook payload format, authentication mechanism
(HMAC signatures, bearer tokens, or no auth), rate limit model, and timestamp encoding.
Without an abstraction layer, adding a fourth or fifth channel would require changes
across the API routing layer, the agent team engine, the input sanitizer, and the
evidence collector — violating the open/closed principle and increasing regression risk
with each new channel.

Sprint 181 builds the `agent_bridge/` package as the abstraction foundation. This ADR
documents the five locked design decisions that govern the OTT channel abstraction for
the lifetime of EP-07.

---

## Problem Statement

SDLC Orchestrator needs to:

1. Accept incoming OTT messages from Telegram, Zalo, Teams, and Slack webhooks
2. Route those messages to the agent team engine for processing
3. Apply the same security controls (rate limiting, input sanitization, HMAC verification)
   regardless of channel
4. Gate channel access by subscription tier (STANDARD gets Telegram + Zalo;
   ENTERPRISE gets all channels)
5. Support adding new channels in future sprints without modifying the agent engine

**Failure mode without abstraction:**
- 4 channel-specific routes, each with partial security controls
- Agent engine accumulates channel-specific type checks (`if channel == "telegram": ...`)
- Adding Microsoft Teams in Sprint 182 requires touching 6+ files
- Input sanitization can be bypassed by misconfigured channel handler

---

## Decision

### D-060-01: Single Entry Point for All OTT Webhooks

**Decision**: All OTT webhook traffic enters the system via a single parameterised
endpoint: `POST /api/v1/channels/{channel}/webhook`. Channel-specific dispatching
happens exclusively inside `protocol_adapter.py`. No channel-specific routes exist
at the API layer.

**Rationale**:
- One security boundary to harden (rate limiting, HMAC, sanitization)
- One place to add a new channel (register normalizer in the channel registry)
- OpenAPI docs show a clean parameterised contract rather than 4+ duplicated endpoints
- Tier gating logic lives in one middleware location

**Rejected alternative**: Channel-specific routes (`/api/v1/telegram/webhook`,
`/api/v1/zalo/webhook`) — rejected because it proliferates routes, duplicates security
middleware, and requires API version changes when adding new channels.

---

### D-060-02: OrchestratorMessage as the Canonical Internal Type

**Decision**: All normalizers MUST produce an `OrchestratorMessage` dataclass instance.
No channel-specific types may escape the normalizer boundary and enter the agent engine
or evidence collector.

**Canonical type definition:**

```python
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class OrchestratorMessage:
    channel: str          # "telegram" | "zalo" | "teams" | "slack"
    sender_id: str        # Channel-specific stable user identifier
    content: str          # Sanitized text content (max 4096 chars)
    timestamp: datetime   # UTC datetime of message origin
    correlation_id: str   # "{channel}_{message_id}" for distributed tracing
    metadata: dict = field(default_factory=dict)  # Channel-specific extras
```

**Invariants enforced by protocol_adapter:**
- `content` is always sanitized (12 injection patterns applied, ADR-058 Pattern C)
- `content` is truncated to 4096 characters if longer (with `[TRUNCATED]` marker)
- `correlation_id` follows the `"{channel}_{identifier}"` format
- `timestamp` is always UTC (normalizers must convert channel-local timestamps)
- `metadata` carries channel-specific extras (chat_id, thread_id, event_name) that
  the agent engine may read but must not require

**Rationale**:
- Agent engine has zero knowledge of channel formats — it only processes `OrchestratorMessage`
- Adding Teams or Slack requires only a new normalizer file, not agent engine changes
- `metadata` dict preserves channel-specific context without polluting the canonical type
- Traceability: `correlation_id` ties the OTT message to evidence records and audit logs

---

### D-060-03: Channel Priority Order and Tier Gating

**Decision**: Channel availability is gated by subscription tier. The release order
reflects Vietnam pilot market priorities (Telegram + Zalo first).

**Tier-to-channel mapping:**

| Tier | Channels Available | Sprint |
|------|--------------------|--------|
| LITE | None (OTT not available) | — |
| STANDARD | Telegram, Zalo | Sprint 181 |
| PROFESSIONAL | Telegram, Zalo, Teams, Slack | Sprint 182–183 |
| ENTERPRISE | All channels, unlimited seats | Sprint 182–183 |

**Tier gate enforcement:**
- `require_standard_tier` dependency: blocks LITE users at the route level
- `require_professional_tier` dependency: applied to Teams and Slack routes in Sprint 182+
- Gate returns `HTTP 402 Payment Required` with `{"upgrade_url": "/billing/upgrade"}`

**Channel release order rationale:**
- Telegram: largest developer community in Vietnam; free Bot API
- Zalo: dominant consumer messaging app in Vietnam (70M+ users); OA API available
- Teams: required for enterprise B2B pilots (Vietnamese corporations use Microsoft 365)
- Slack: developer-first market; important for international enterprise expansion

---

### D-060-04: G3/G4 Gate Approvals via OTT Use Magic Link Flow

**Decision**: Gate G3 (Ship Ready) and G4 (Production Validation) approvals that arrive
via OTT channels MUST use the Magic Link authentication flow. Direct OTT approval
(clicking a button or replying "approve") is NOT permitted for G3 and G4.

**Magic Link flow for G3/G4 approval:**

```
1. Orchestrator sends Magic Link URL via OTT channel
   URL format: https://app.sdlc.io/gates/{gate_id}/approve?token={jwt}
   JWT payload: {gate_id, approver_id, action: "approve"|"reject", exp: now+5min}
   JWT signed with GATE_APPROVAL_SECRET (HS256)

2. Approver clicks link in Telegram/Zalo → browser opens SSO-authenticated session
   (Azure AD for Teams; Google/GitHub OAuth for Telegram/Zalo users)

3. Approver confirms or rejects in the browser (full authenticated session)

4. Orchestrator correlates: OTT message_id + Magic Link JWT + browser session
   All three identifiers written to audit log as correlated evidence

5. Gate state transitions: SUBMITTED → APPROVED or SUBMITTED → REJECTED
```

**G1/G2 gates may use direct OTT approval** (lower stakes, faster iteration needed).

**Rationale**:
- G3/G4 approvals are production-impacting, compliance-critical decisions
- Telegram and Zalo cannot guarantee that the person who clicks "approve" is the
  authenticated approver (shared devices, forwarded messages)
- Magic Link binds the OTT interaction to a verified SSO identity
- 5-minute JWT expiry prevents stale approvals from being replayed
- Audit trail satisfies HIPAA/SOC 2 requirements (who approved, from what session, when)

---

### D-060-05: Input Sanitization Mandatory at Protocol Adapter Layer

**Decision**: All OTT message content MUST pass through `agent_team/input_sanitizer.py`
(12 injection patterns, ADR-058 Pattern C) inside the `normalize()` function of
`protocol_adapter.py`, before the `OrchestratorMessage` is passed to the agent engine.

**Sanitization location in the call chain:**

```
OTT webhook payload (raw)
        |
        v
channel normalizer (telegram_normalizer.py | zalo_normalizer.py)
        |
        v  [raw OrchestratorMessage — content NOT yet sanitized]
        |
        v
input_sanitizer.sanitize(content)   ← MANDATORY here, in protocol_adapter.normalize()
        |
        v  [sanitized OrchestratorMessage — content safe for agent engine]
        |
        v
message_queue.enqueue() → agent team engine
```

**Why sanitization must occur in `protocol_adapter` and not in the agent engine:**
- Agent engine already trusts `OrchestratorMessage` content (it is the canonical type)
- If sanitization is deferred, a direct call to `message_queue.enqueue()` that bypasses
  `protocol_adapter` (e.g., from a unit test or future internal producer) could inject
  unsanitized content into the agent engine
- Single enforcement point is auditable and testable in isolation (PA-12 test case)

**12 injection patterns from ADR-058 Pattern C** (imported, not duplicated):
Patterns match and strip prompt injection, command injection, path traversal, template
injection, SSRF payloads, and format string attacks from the `content` field.

---

## Alternatives Considered

### Alternative A: Channel-Specific API Routes

```
POST /api/v1/telegram/webhook
POST /api/v1/zalo/webhook
POST /api/v1/teams/webhook
POST /api/v1/slack/webhook
```

**Why rejected:**
- Adding a new channel requires a new route file, a new entry in `main.py`, a new
  middleware registration — 4+ file changes instead of 1
- Security controls (rate limiting, HMAC, sanitization) must be duplicated or
  abstracted separately anyway — the channel-specific route approach does not actually
  simplify the security layer
- OpenAPI surface proliferates with each new channel, creating documentation debt
- Tier gating logic must be applied at each route individually (fragile)

### Alternative B: SDK-Based Channel Libraries

Use `python-telegram-bot`, `slack_sdk`, or `msteams-adaptive-cards` as dependencies:

```python
from telegram import Update
from slack_sdk import WebClient
```

**Why rejected:**
- `python-telegram-bot` uses LGPL v3 — permissible but creates a mandatory open-source
  attribution obligation. Future versions could change license.
- SDK dependencies add 40–80MB per channel to the Docker image
- SDKs are typically designed for outbound message sending, not inbound webhook parsing.
  They add complexity (authentication state, retry logic) that is not needed here.
- The inbound webhook payload is simple JSON — a 60-line normalizer is sufficient.
  An SDK dependency for JSON field mapping is over-engineering.
- Network-only access via raw webhook parsing is consistent with AGPL containment
  principle (ADR Principle 2) — we avoid importing third-party libraries where
  a thin adapter suffices.

### Alternative C: Generic Webhook Proxy (Selected Approach)

Single parameterised endpoint + normalizer registry + canonical type.

**Why selected:**
- Open/closed: adding a new channel opens a new normalizer file, closes protocol_adapter
- Security boundary: one location for HMAC, rate limiting, and input sanitization
- Testable in isolation: each normalizer is a pure function (dict → OrchestratorMessage)
- Consistent with `agent_bridge/` package boundary established in EP-07 architecture

---

## Consequences

### Positive Consequences

1. **Open/closed for new channels**: Adding Microsoft Teams in Sprint 182 requires only
   `teams_normalizer.py` + one line in the channel registry. No other file changes.

2. **Single security enforcement point**: Rate limiting, HMAC verification, and input
   sanitization all live in one location (`protocol_adapter.normalize()` +
   `ott_gateway.py`). One audit, one security review.

3. **Testable in isolation**: Each normalizer is a pure function (`dict → OrchestratorMessage`).
   Unit tests (PA-01 to PA-20) cover all normalizer logic without network dependencies.

4. **Consistent evidence correlation**: Every agent action triggered by OTT has a
   `correlation_id` linking the OTT message to the evidence record.
   Magic Link adds SSO identity correlation for G3/G4 approvals.

5. **Tier gating at one location**: The `channel_whitelist` in `ott_gateway.py` and the
   `require_standard_tier`/`require_professional_tier` dependencies enforce access control
   without duplicated logic.

### Negative Consequences and Mitigations

1. **OrchestratorMessage loses channel-specific richness**:
   Teams supports rich adaptive card buttons; Slack supports Block Kit layouts.
   Normalizing to plain text `content` discards this structure.
   **Mitigation**: `metadata` dict preserves channel-specific extras. Sprint 182+
   may add structured content support as a non-breaking extension to OrchestratorMessage.

2. **Magic Link adds UX friction for G3/G4 approvals via OTT**:
   Approvers must switch from the messaging app to a browser.
   **Mitigation**: Magic Link URL is designed to open in the user's default browser
   with a single tap. 5-minute expiry is generous for a deliberate approval action.
   G1/G2 approvals remain direct (no friction for fast-iteration gates).

3. **HMAC secret management adds operational overhead**:
   Each channel has a different HMAC secret that must be rotated.
   **Mitigation**: Secrets stored in HashiCorp Vault with 90-day rotation (existing policy).
   `OTT_HMAC_ENABLED` env var allows disabling in dev/test environments.

---

## Implementation Notes for Sprint 181

The following files implement this ADR. Implementation details are in the Sprint 181 plan.

| Decision | File | Sprint |
|----------|------|--------|
| D-060-01 Single entry point | `api/routes/ott_gateway.py` | 181 |
| D-060-02 OrchestratorMessage | `services/agent_bridge/protocol_adapter.py` | 181 |
| D-060-02 Telegram normalizer | `services/agent_bridge/telegram_normalizer.py` | 181 |
| D-060-02 Zalo normalizer | `services/agent_bridge/zalo_normalizer.py` | 181 |
| D-060-03 Tier gating | `api/dependencies.py` (require_standard_tier) | 181 |
| D-060-04 Magic Link | `services/magic_link_service.py` | Sprint 182 |
| D-060-05 Input sanitization | `services/agent_team/input_sanitizer.py` (reused) | 179 (done) |

**Test coverage target**: 20 unit tests (PA-01 to PA-20) in `test_protocol_adapter.py`.
All 5 decisions must be demonstrable from the test suite.

---

## Follow-up ADRs

| ADR | Title | Trigger |
|-----|-------|---------|
| ADR-061 | Enterprise SSO Integration | Microsoft Teams uses Azure AD; Sprint 182 |
| ADR-062 | OTT Interaction Evidence Types | OTT messages as compliance evidence artifacts |
| ADR-063 | Outbound Message Delivery (TBD) | Agent replies back via Telegram/Zalo/Teams |

---

## Review and Approval

| Role | Name | Status | Date |
|------|------|--------|------|
| CTO | — | PENDING | — |
| Tech Lead | — | PENDING | — |
| Architect | — | PENDING | — |

ADR must be APPROVED before Day 4 of Sprint 181 (Feb 26, 2026) when orphaned route
activation begins. Activation of ENTERPRISE routes depends on tier gate patterns
confirmed in D-060-03.

---

*ADR-060 — Enterprise OTT Channel Abstraction*
*Part of EP-07 Multi-Agent Team Engine architecture series (ADR-056, ADR-058, ADR-059, ADR-060)*

**Last Updated**: 2026-02-19
**Owner**: Architect + Tech Lead
**Framework**: SDLC 6.1.0 (7-Pillar + AI Governance Principles)
