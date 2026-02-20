---
sdlc_version: "6.1.0"
document_type: "Functional Requirement"
status: "APPROVED"
sprint: "187"
spec_id: "FR-045"
tier: "ALL"
stage: "01 - Planning"
---

# FR-045: GDPR Art.20 Data Portability — Full PII Export

**Version**: 1.0.1
**Status**: APPROVED
**Created**: February 2026
**Amended**: February 2026 (Sprint 187 CTO-AC: agent_messages 1000-cap + sender_type filter documented)
**Sprint**: 187
**Framework**: SDLC 6.1.0
**Epic**: GDPR Compliance (ADR-063)
**ADR**: ADR-063 (Multi-Region Data Residency + GDPR)
**Owner**: Backend Team
**Source**: GDPR Art.20 Right to Data Portability — any authenticated user may request a machine-readable export of all personal data held about them.

---

## 1. Overview

### 1.1 Purpose

GDPR Article 20 grants data subjects the right to receive personal data in a structured, commonly-used, machine-readable format (JSON) and to transmit it to another controller. This FR extends the existing summary-only `/gdpr/me/data-export` endpoint (Art.15, count-only) with a full PII export endpoint.

### 1.2 Scope

| In scope | Out of scope |
|----------|-------------|
| All personal data held in the platform database | Binary evidence file content (files remain in MinIO S3) |
| User profile fields (email, name, timestamps) | Agent conversation internal reasoning traces |
| Consent records (purpose, granted, timestamps) | System audit events not attributable to the user |
| DSAR request history | Aggregated/anonymised analytics |
| Agent message content authored by the user (up to 1,000 most recent; `sender_type = 'human'` only) | Other users' data referenced in same project |
| Evidence metadata (filename, type, upload time) | |

---

## 2. Functional Requirements

### 2.1 Endpoint

```
GET /api/v1/gdpr/me/data-export/full
```

- **Authentication**: Required (`get_current_user`)
- **Tier**: ALL (self-service GDPR right — no tier restriction)
- **Rate limit**: 1 request per user per 24 hours (prevent bulk scraping)
- **Response Content-Type**: `application/json`
- **HTTP Status**: 200 OK
- **agent_messages cap**: Returns at most 1,000 most recent messages where `sender_type = 'human'`. Agent/system messages are excluded as they are not user-authored personal data. Users with >1,000 human messages should submit a DSAR `access` request for complete history.

### 2.2 BDD Acceptance Criteria

#### Scenario P45-01: Authenticated user receives full PII export

```gherkin
GIVEN an authenticated user with id=USER_ID
WHEN  GET /api/v1/gdpr/me/data-export/full
THEN  HTTP 200
AND   response body contains "user_profile" with email, name, created_at
AND   response body contains "consent_records" list with purpose, granted, version, created_at
AND   response body contains "dsar_requests" list with request_type, status, created_at
AND   response body contains "agent_messages" list with content, role, created_at
AND   "agent_messages" contains only human-authored messages (sender_type = 'human'), at most 1,000 records
AND   response body contains "evidence_metadata" list with file_name, evidence_type, created_at
AND   response body contains "export_generated_at" ISO timestamp
AND   response body contains "gdpr_article" = "Art.20 — Right to Data Portability"
AND   response body contains "format" = "application/json"
```

#### Scenario P45-02: Rate limit enforced

```gherkin
GIVEN a user who already exported data within the past 24 hours
WHEN  GET /api/v1/gdpr/me/data-export/full (second call)
THEN  HTTP 429 Too Many Requests
AND   response body contains "retry_after_seconds"
```

#### Scenario P45-03: Unauthenticated request rejected

```gherkin
GIVEN no authentication header or cookie
WHEN  GET /api/v1/gdpr/me/data-export/full
THEN  HTTP 401 Unauthorized
```

#### Scenario P45-04: Export does not expose other users' data

```gherkin
GIVEN user A (id=A) and user B (id=B) in the same project
WHEN  user A calls GET /api/v1/gdpr/me/data-export/full
THEN  response contains only records where user_id = A
AND   user B's messages, consents, and DSARs are NOT included
```

#### Scenario P45-05: agent_messages cap at 1,000 records (sender_type = 'human')

```gherkin
GIVEN a user who has sent 1,500 messages in agent conversations (sender_type = 'human')
WHEN  GET /api/v1/gdpr/me/data-export/full
THEN  HTTP 200
AND   response body "agent_messages" contains exactly 1,000 records
AND   records are the 1,000 most recent messages ordered by created_at DESC
AND   no agent/system messages (sender_type != 'human') are included
AND   "summary.total_agent_messages_exported" = 1000
AND   "summary.total_agent_messages_available" = 1500
AND   "summary.agent_messages_note" contains guidance to submit a DSAR access request for full history
```

### 2.3 Response Schema

```json
{
  "gdpr_article": "Art.20 — Right to Data Portability",
  "format": "application/json",
  "export_generated_at": "2026-02-20T10:00:00Z",
  "user_id": "uuid",
  "user_profile": {
    "id": "uuid",
    "email": "user@example.com",
    "full_name": "Nguyen Van A",
    "created_at": "2026-01-01T00:00:00Z",
    "last_login_at": "2026-02-20T09:00:00Z"
  },
  "consent_records": [
    {
      "id": "uuid",
      "purpose": "analytics",
      "granted": true,
      "version": "v2.1",
      "created_at": "2026-02-01T10:00:00Z",
      "withdrawn_at": null
    }
  ],
  "dsar_requests": [
    {
      "id": "uuid",
      "request_type": "access",
      "status": "completed",
      "created_at": "2026-01-15T08:00:00Z",
      "due_at": "2026-02-14T08:00:00Z"
    }
  ],
  "agent_messages": [
    {
      "id": "uuid",
      "role": "user",
      "content": "message content...",
      "created_at": "2026-02-10T12:00:00Z"
    }
  ],
  "_agent_messages_note": "Contains at most 1,000 most recent human-authored messages (sender_type='human'). Agent and system messages are excluded. For complete history, submit a DSAR access request via POST /api/v1/gdpr/dsar.",
  "evidence_metadata": [
    {
      "id": "uuid",
      "file_name": "test-results.xml",
      "evidence_type": "TEST_RESULTS",
      "file_size": 4096,
      "created_at": "2026-02-05T14:00:00Z"
    }
  ],
  "summary": {
    "total_consent_records": 3,
    "total_dsar_requests": 1,
    "total_agent_messages_exported": 47,
    "total_agent_messages_available": 47,
    "agent_messages_note": "All messages exported. For users with >1,000 messages: this field shows 1000 (cap applied) — submit a DSAR access request for full history.",
    "total_evidence_uploads": 12
  }
}
```

---

## 3. Non-Functional Requirements

| Requirement | Target |
|-------------|--------|
| Response latency (p95) | <2s (may require multiple DB queries) |
| Rate limit | 1 request / user / 24h |
| Max response size | 10MB (paginated if larger — Sprint 188 enhancement) |
| agent_messages cap | 1,000 most recent records; `sender_type = 'human'` filter applied |
| Full message history | Available via DSAR `access` request (30-day SLA per Art.12(3)) |
| Retention of export logs | Export event written to audit_logs |

---

## 4. Dependencies

| Dependency | Type | Status |
|-----------|------|--------|
| `gdpr_dsar_requests` table (s186_002) | Database | ✅ Sprint 186 |
| `gdpr_consent_logs` table (s186_002) | Database | ✅ Sprint 186 |
| `agent_messages` table (s176_001) | Database | ✅ Sprint 176 |
| `gate_evidence` table | Database | ✅ Existing |
| `users` table | Database | ✅ Existing |

---

## 5. Acceptance Test IDs

| ID | BDD Scenario | Pass Criteria |
|----|-------------|---------------|
| P45-01 | Full PII export | 200 + all 5 data categories present |
| P45-02 | Rate limit | 429 on second call within 24h |
| P45-03 | Unauthenticated | 401 |
| P45-04 | Data isolation | Only caller's records in response |
| P45-05 | agent_messages 1,000-cap | >1K messages → 1K returned, summary fields show total_available + DSAR guidance |

---

## 6. Regulatory Reference

| Article | Right | Implementation |
|---------|-------|---------------|
| GDPR Art.20(1) | Receive personal data in structured, machine-readable format | JSON export endpoint |
| GDPR Art.20(2) | Right to transmit data to another controller | Export downloadable as file |
| GDPR Art.12(3) | Response within 1 month | Immediate (synchronous endpoint for MVP) |
| GDPR Art.12(5) | First request free of charge | No cost to user |
