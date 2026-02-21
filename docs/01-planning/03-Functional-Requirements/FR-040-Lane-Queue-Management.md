---
sdlc_version: "6.1.0"
document_type: "Functional Requirement"
status: "PROPOSED"
sprint: "176"
spec_id: "FR-040"
tier: "PROFESSIONAL"
stage: "01 - Planning"
---

# FR-040: Lane-Based Queue Management

**Version**: 1.0.0
**Status**: PROPOSED
**Created**: February 2026
**Sprint**: 177-178
**Framework**: SDLC 6.1.0
**Epic**: EP-07 Multi-Agent Team Engine
**ADR**: ADR-056 (Decision 2: Lane Contract)
**Owner**: Backend Team

---

## 1. Overview

### 1.1 Purpose

Implement lane-based message queue with PostgreSQL `FOR UPDATE SKIP LOCKED`, Redis pub/sub notification, dead-letter queue, and deduplication. DB is truth, Redis is notify-only.

### 1.2 Business Value

- Per-agent lane serialization ensures message ordering within agent
- Cross-agent parallelism enables concurrent multi-agent processing
- Dead-letter queue prevents poison messages from blocking pipeline
- Deduplication ensures idempotent message processing

---

## 2. Functional Requirements

### 2.1 Lane Processing

**GIVEN** messages in `agent_messages` with `processing_status = 'pending'`
**WHEN** a worker polls for the next message in a lane
**THEN** the system SHALL:
1. `SELECT ... FOR UPDATE SKIP LOCKED LIMIT 1` ordered by `created_at`
2. Set `processing_status = 'processing'`
3. Invoke agent with message content
4. On success: set `processing_status = 'completed'`, record `latency_ms`
5. On failure: increment `failed_count`, set `next_retry_at` with exponential backoff

### 2.2 Deduplication (Decision 2)

**GIVEN** a message with `dedupe_key` that already exists in the table
**WHEN** `INSERT ... ON CONFLICT (dedupe_key) DO NOTHING` executes
**THEN** the second insert SHALL be silently dropped (no error)

### 2.3 Dead-Letter Queue (Decision 2)

**GIVEN** a message with `failed_count >= 3`
**WHEN** the next failure occurs
**THEN** the system SHALL:
1. Set `processing_status = 'dead_letter'`
2. Preserve `last_error` for admin inspection
3. NOT retry the message further

### 2.4 Exponential Backoff

**GIVEN** a failed message with `failed_count = N`
**WHEN** calculating `next_retry_at`
**THEN** the system SHALL set `next_retry_at = NOW() + (30 * 2^N) seconds`
- 1st failure: 30s
- 2nd failure: 60s
- 3rd failure: 120s (then dead-letter)

### 2.5 Cross-Lane Parallelism

**GIVEN** messages in different `processing_lane` values
**WHEN** multiple workers are running
**THEN** messages in different lanes SHALL be processed concurrently

### 2.6 Same-Lane Serialization

**GIVEN** messages in the same `processing_lane`
**WHEN** multiple workers are running
**THEN** only ONE message per lane SHALL be processing at any time (via SKIP LOCKED)

### 2.7 Interrupt Mode (Non-Negotiable #14)

**GIVEN** an interrupt message with `queue_mode = 'interrupt'`
**WHEN** the message arrives in a lane
**THEN** the current processing SHALL be paused and the interrupt handled first

---

## 3. Test Coverage

| Test ID | Description | Decision |
|---------|-------------|----------|
| LQ-01 | Dedupe rejection | 2 |
| LQ-02 | Lane serialization | 2 |
| LQ-03 | Cross-lane parallelism | 2 |
| LQ-04 | Dead-letter after 3 | 2 |
| LQ-05 | Exponential backoff (30s) | 2 |
| LQ-06 | Second backoff (60s) | 2 |
| LQ-07 | SKIP LOCKED | 2 |
| LQ-08 | Interrupt mode | #14 |

---

## 4. Dependencies

- PostgreSQL 15.5 (`FOR UPDATE SKIP LOCKED`)
- Redis 7.2 (pub/sub notification with 5s DB polling fallback)
- `agent_messages` table with lane contract columns
