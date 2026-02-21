---
sdlc_version: "6.1.0"
document_type: "Functional Requirement"
status: "IMPLEMENTED"
sprint: "189"
spec_id: "FR-048"
tier: "STANDARD"
stage: "01 - Planning"
---

# FR-048: OTT Gateway Webhook Deduplication

**Version**: 1.1.0
**Status**: IMPLEMENTED (Sprint 189 — CTO CONDITIONAL APPROVE 9.4/10)
**Created**: February 2026
**Sprint**: 189
**Framework**: SDLC 6.1.0
**Epic**: EP-08 Chat-First Governance Loop
**ADR**: ADR-064 (T-04: Dedupe at OTT gateway, NOT router)
**Owner**: Backend Team

---

## 1. Overview

### 1.1 Purpose

Prevent duplicate processing of OTT webhook events at the gateway ingestion layer. OTT platforms (Telegram, Slack, Teams) may retry webhook delivery on timeout, causing the same message to be processed multiple times — potentially duplicating gate approvals or evidence submissions.

### 1.2 Business Value

- Prevents duplicate gate approvals (critical: double-approve could corrupt audit trail)
- Prevents duplicate evidence submissions (SHA256 collision on re-upload)
- Idempotent webhook handling (industry standard for webhook receivers)
- Full coverage: deduplication at gateway level catches ALL channels, not just chat router

---

## 2. Functional Requirements

### 2.1 Event ID Extraction

**GIVEN** an incoming OTT webhook payload
**WHEN** the gateway receives the request
**THEN** the system SHALL:
1. Extract a platform-specific event ID from the payload:
   - Telegram: `message.message_id` or `update_id`
   - Slack: `event_id` from Events API wrapper
   - Teams: `id` from Activity object
   - Zalo: `event_id` from webhook payload
2. Construct a dedupe key: `webhook_dedupe:{channel}:{event_id}`

### 2.2 Redis-Based Deduplication

**GIVEN** a dedupe key for an incoming webhook
**WHEN** the gateway checks for duplicates
**THEN** the system SHALL:
1. Check if `webhook_dedupe:{channel}:{event_id}` exists in Redis
2. If EXISTS: return `{"status": "duplicate", "message": "Already processed"}` with HTTP 200
3. If NOT EXISTS: set the key with TTL 3600 seconds (1 hour), then proceed with normal processing
4. Log duplicate events at INFO level for observability

### 2.3 Idempotent Response

**GIVEN** a duplicate webhook delivery
**WHEN** the gateway detects the duplicate
**THEN** the system SHALL:
1. Return HTTP 200 (not 4xx — OTT platforms interpret non-200 as failure and retry)
2. Include `"status": "duplicate"` in the response body
3. NOT enqueue the message into the agent message queue
4. NOT trigger any downstream processing

### 2.4 TTL-Based Cleanup

**GIVEN** a dedupe key in Redis
**WHEN** the TTL expires (1 hour)
**THEN** the system SHALL:
1. Allow Redis to automatically delete the key
2. Accept a re-delivery of the same event_id after TTL expiry (edge case: acceptable for 1h+ delayed retries)

---

## 3. Non-Functional Requirements

| Requirement | Target |
|-------------|--------|
| Dedupe check latency | <5ms (single Redis GET) |
| Dedupe TTL | 3600 seconds (1 hour) |
| Redis memory per key | ~100 bytes |
| Max concurrent webhooks | 200 req/min per source IP (existing rate limit) |

---

## 4. File Location

Modified: `backend/app/api/routes/ott_gateway.py` (~30 LOC addition)

---

## 5. Dependencies

- `backend/app/utils/redis.py` — async Redis client
- Existing rate limiter in ott_gateway.py (200 req/min per IP)
- Channel-specific normalizers (telegram_normalizer.py, slack_normalizer.py, etc.) for event_id extraction
