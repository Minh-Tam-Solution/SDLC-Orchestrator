# CONTRACT: Governance Loop — Single Source of Truth

**Version**: 1.0.0
**Date**: February 15, 2026
**Status**: ACTIVE
**Sprint**: Sprint 173 ("Sharpen, Don't Amputate")
**Authority**: CTO + Enterprise Architect + SDLC Expert — All Approved v4 FINAL
**ADR Reference**: ADR-053-Governance-Loop-State-Machine.md

---

## Purpose

This document is the **Single Source of Truth (SSOT)** for the Governance Loop contract shared by all 3 client interfaces (Web UI, CLI, VS Code Extension). Any client implementing gate actions MUST conform to this contract.

**Invariant**: All 3 clients produce identical results for the same gate lifecycle sequence. The server is the sole authority for permissions and state transitions.

---

## 1. Gate State Machine

### 1.1 States

| State | Code | Description |
|-------|------|-------------|
| Draft | `DRAFT` | Gate created, no evaluation performed |
| Evaluated | `EVALUATED` | Exit criteria evaluated against evidence |
| Evaluated Stale | `EVALUATED_STALE` | Evaluation invalidated by new evidence upload |
| Submitted | `SUBMITTED` | Submitted for approval review |
| Approved | `APPROVED` | Passed review — gate cleared |
| Rejected | `REJECTED` | Failed review — re-evaluation allowed |

**Archived**: `ARCHIVED` is a lifecycle status (soft-delete), not a governance state. Archived gates cannot undergo governance transitions.

### 1.2 Transitions

```
DRAFT ──────────── evaluate ───────────→ EVALUATED
EVALUATED ─────── submit ─────────────→ SUBMITTED
EVALUATED ─────── evidence_upload ────→ EVALUATED_STALE
EVALUATED_STALE ─ evaluate ───────────→ EVALUATED
SUBMITTED ──────── approve ───────────→ APPROVED
SUBMITTED ──────── reject ────────────→ REJECTED
REJECTED ──────── evaluate ───────────→ EVALUATED (re-evaluate path)
```

### 1.3 Transition Guards

| Action | Allowed From | Required Scope | Preconditions |
|--------|-------------|----------------|---------------|
| `evaluate` | DRAFT, EVALUATED, EVALUATED_STALE, REJECTED | `governance:write` | None |
| `submit` | EVALUATED | `governance:write` | `missing_evidence = []` |
| `approve` | SUBMITTED | `governance:approve` | Comment required |
| `reject` | SUBMITTED | `governance:approve` | Comment required |
| `evidence_upload` | Any except APPROVED, ARCHIVED | `governance:write` | File + metadata |

### 1.4 Side Effects

| Trigger | Side Effect |
|---------|-------------|
| `evidence_upload` while `EVALUATED` | Gate status → `EVALUATED_STALE` |
| `approve` | Set `approved_at = now()` |
| `reject` | Set `rejected_at = now()` |
| `evaluate` | Set `evaluated_at = now()`, update `exit_criteria` results |
| Duplicate `submit` (idempotent) | Return stored response body (no state change) |
| Duplicate `approve` (idempotent) | Return stored response body (no state change) |

---

## 2. Auth Scopes

| Scope | Allowed Actions | Primary Interface |
|-------|----------------|-------------------|
| `governance:write` | evaluate, submit, upload evidence | CLI (DevOps), Extension (Developer) |
| `governance:approve` | approve, reject | Web (Manager), CLI (with `--scope=full`) |

**Separation of duties**: A user with only `governance:write` cannot approve their own gate. A manager with `governance:approve` can approve gates without needing code-level access.

**403 Response**: When a user lacks the required scope:
```json
{
  "detail": "Missing required scope: governance:approve",
  "error_code": "INSUFFICIENT_SCOPE"
}
```

---

## 3. API Endpoints

### 3.1 Capability Discovery

```
GET /api/v1/gates/{gate_id}/actions
Authorization: Bearer <token> (governance:write OR governance:approve)
```

**Response** (`200 OK`):
```json
{
  "gate_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "SUBMITTED",
  "actions": {
    "can_evaluate": false,
    "can_submit": false,
    "can_approve": true,
    "can_reject": true,
    "can_upload_evidence": true
  },
  "reasons": {
    "can_evaluate": "Cannot evaluate from status: SUBMITTED",
    "can_submit": "Gate must be EVALUATED to submit (current: SUBMITTED)"
  },
  "required_evidence": ["test-results", "security-scan", "design-doc"],
  "submitted_evidence": ["test-results", "design-doc"],
  "missing_evidence": ["security-scan"]
}
```

**SSOT Rule**: This endpoint and all mutation endpoints use the **same `compute_gate_actions()` function**. What this endpoint reports is exactly what mutations enforce.

**Client Behavior**: ALL clients (Web, CLI, Extension) MUST call this endpoint before showing action buttons/options. No client-side permission computation.

### 3.2 Evaluate Gate

```
POST /api/v1/gates/{gate_id}/evaluate
Authorization: Bearer <token> (governance:write)
X-Idempotency-Key: <uuid>
Content-Type: application/json
```

**Response** (`200 OK`):
```json
{
  "gate_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "EVALUATED",
  "evaluated_at": "2026-02-15T10:30:00Z",
  "exit_criteria": [
    {"id": "FRD_COMPLETE", "description": "FRD complete", "met": true},
    {"id": "DATA_MODEL", "description": "Data model designed", "met": true},
    {"id": "SECURITY_SCAN", "description": "Security scan passed", "met": false}
  ],
  "summary": {
    "total": 3,
    "met": 2,
    "unmet": 1,
    "pass_rate": 66.7
  }
}
```

**Error** (`409 Conflict` — invalid transition):
```json
{
  "detail": "Cannot evaluate gate from status: APPROVED",
  "error_code": "INVALID_STATE_TRANSITION"
}
```

### 3.3 Submit for Approval

```
POST /api/v1/gates/{gate_id}/submit
Authorization: Bearer <token> (governance:write)
X-Idempotency-Key: <uuid>
```

**Precondition**: `missing_evidence = []` (all required evidence types submitted).

**Response** (`200 OK`):
```json
{
  "gate_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "SUBMITTED",
  "submitted_at": "2026-02-15T10:35:00Z"
}
```

**Error** (`422 Unprocessable Entity` — missing evidence):
```json
{
  "detail": "Cannot submit: missing required evidence",
  "error_code": "MISSING_EVIDENCE",
  "missing_evidence": ["security-scan"]
}
```

### 3.4 Approve Gate

```
POST /api/v1/gates/{gate_id}/approve
Authorization: Bearer <token> (governance:approve)
X-Idempotency-Key: <uuid>
Content-Type: application/json

{
  "comment": "All criteria met. Tests passing. Security scan clean."
}
```

**Response** (`200 OK`):
```json
{
  "gate_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "APPROVED",
  "approved_at": "2026-02-15T11:00:00Z",
  "approved_by": "user-uuid",
  "comment": "All criteria met. Tests passing. Security scan clean."
}
```

### 3.5 Reject Gate (Separate Endpoint — CTO Mod 1)

```
POST /api/v1/gates/{gate_id}/reject
Authorization: Bearer <token> (governance:approve)
X-Idempotency-Key: <uuid>
Content-Type: application/json

{
  "comment": "Security scan shows 2 HIGH vulnerabilities. Fix CVE-2026-1234 before re-submitting."
}
```

**Response** (`200 OK`):
```json
{
  "gate_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "REJECTED",
  "rejected_at": "2026-02-15T11:05:00Z",
  "rejected_by": "user-uuid",
  "comment": "Security scan shows 2 HIGH vulnerabilities. Fix CVE-2026-1234 before re-submitting."
}
```

**After rejection**: The gate can be re-evaluated (`POST /evaluate`) from `REJECTED` status. This allows iterative improvement without creating a new gate.

### 3.6 Upload Evidence

```
POST /api/v1/gates/{gate_id}/evidence
Authorization: Bearer <token> (governance:write)
X-Idempotency-Key: <uuid>
Content-Type: multipart/form-data

file: <binary>
sha256_client: "a1b2c3d4..."
size_bytes: 1048576
mime_type: "application/json"
source: "cli"
evidence_type: "test-results"
criteria_snapshot_id: "exit-criteria-version-uuid"
description: "Unit test results - 94% coverage"
```

**Server Processing**:
1. Recompute SHA256 from received bytes → `sha256_server`
2. If `sha256_client` provided AND differs from `sha256_server` → `400 Bad Request`
3. If `sha256_client` absent AND `source=other` → log warning, proceed
4. Store both hashes in `gate_evidence` table
5. Upload to MinIO via S3 API (AGPL-safe, network-only)
6. If gate status is `EVALUATED` → set to `EVALUATED_STALE`

**Response** (`201 Created`):
```json
{
  "evidence_id": "uuid",
  "gate_id": "uuid",
  "sha256_client": "a1b2c3d4...",
  "sha256_server": "a1b2c3d4...",
  "integrity_verified": true,
  "criteria_snapshot_id": "exit-criteria-version-uuid",
  "gate_status_changed": true,
  "new_gate_status": "EVALUATED_STALE"
}
```

**Error** (`400 Bad Request` — hash mismatch):
```json
{
  "detail": "SHA256 hash mismatch: file may be corrupted or tampered",
  "error_code": "HASH_MISMATCH",
  "sha256_client": "a1b2c3d4...",
  "sha256_server": "x9y8z7w6..."
}
```

---

## 4. Idempotency Contract

### 4.1 Client Requirements

- CLI: Generate `uuid4()` per command invocation, send as `X-Idempotency-Key` header
- Extension: Generate `uuid4()` per button click, send as `X-Idempotency-Key` header
- Web: Generate `uuid4()` per form submission, send as `X-Idempotency-Key` header

### 4.2 Server Behavior

```
Key pattern: idempotency:{user_id}:{endpoint}:{gate_id}:{idempotency_key}
Storage: Redis (port 6395)
TTL: 86400 seconds (24 hours)
```

| Scenario | Server Behavior |
|----------|----------------|
| First request with key | Execute, store response in Redis, return response |
| Duplicate request with same key | Return stored response body (HTTP 200, same body) |
| Same key, different user | Execute normally (key is user-scoped) |
| Redis unavailable | Execute normally, log warning (graceful degradation) |

### 4.3 Endpoints Supporting Idempotency

| Endpoint | Idempotency |
|----------|-------------|
| `POST /gates/{id}/evaluate` | Required |
| `POST /gates/{id}/submit` | Required |
| `POST /gates/{id}/approve` | Required |
| `POST /gates/{id}/reject` | Required |
| `POST /gates/{id}/evidence` | Required |
| `GET /gates/{id}/actions` | Not applicable (read-only) |

---

## 5. Client Integration Contracts

### 5.1 CLI (sdlcctl)

**Module**: `backend/sdlcctl/sdlcctl/commands/gate.py`

| Command | Endpoint | Notes |
|---------|----------|-------|
| `sdlcctl gate list` | `GET /gates?project_id=X` | Rich table output |
| `sdlcctl gate show <id>` | `GET /gates/{id}` | Gate details + exit criteria |
| `sdlcctl gate evaluate <id>` | `POST /gates/{id}/evaluate` | Evaluate criteria |
| `sdlcctl gate submit <id>` | `POST /gates/{id}/submit` | Submit (blocked if missing evidence) |
| `sdlcctl gate approve <id> -c "..."` | `POST /gates/{id}/approve` | Comment required; prompt if omitted |
| `sdlcctl gate reject <id> -c "..."` | `POST /gates/{id}/reject` | Opens `$EDITOR` via `click.edit()` if no comment |
| `sdlcctl gate status` | `GET /gates?project_id=X` | Compact status table |

**Pre-action check**: Every mutation command calls `GET /gates/{id}/actions` first. If action not allowed, print reason and exit with code 1.

**Auth**: Uses token from `.sdlc/config.json`. If 403, print "Missing scope: governance:approve. Run: sdlcctl auth login --scope=full".

**Timeout**: `httpx` timeout set to 120s for evidence upload, 30s for other operations.

### 5.2 VS Code Extension

**Modules**:
- `vscode-extension/src/commands/gateApprovalCommand.ts`
- `vscode-extension/src/commands/evidenceSubmissionCommand.ts`

| Command | Endpoint | UX |
|---------|----------|-----|
| `sdlc.approveGate` | `POST /gates/{id}/approve` | Input box for comment → optimistic spinner → confirm |
| `sdlc.rejectGate` | `POST /gates/{id}/reject` | Input box for comment → optimistic spinner → confirm |
| `sdlc.submitEvidence` | `POST /gates/{id}/evidence` | File picker → SHA256 compute → progress bar → confirm |

**Pre-action check**: Every command calls `getGateActions(gateId)` first. If not allowed, show `vscode.window.showWarningMessage()` with server reason.

**Optimistic UI**: Update tree item icon to spinner immediately. After API response, fetch confirmed state. If `processing=true`, use exponential backoff polling: 500ms → 1s → 2s → 5s (max).

**Auth 403 handling**:
```typescript
if (error.statusCode === 403) {
    vscode.window.showErrorMessage(
        'Missing scope: governance:write. Please re-login with full permissions.',
        'Re-login'
    ).then(choice => {
        if (choice === 'Re-login') vscode.commands.executeCommand('sdlc.login');
    });
}
```

**Context menus**: All 3 commands visible on gate items in sidebar. Server decides if action is allowed (not client-side `when` clause).

### 5.3 Web UI (React Dashboard)

Existing implementation — no changes required for governance loop completeness. Web already supports all gate actions. Must update to:
- Call `GET /gates/{id}/actions` for button visibility (instead of client-side role check)
- Send `X-Idempotency-Key` header on mutations
- Handle `EVALUATED_STALE` status in gate status display

---

## 6. Database Schema Changes

### 6.1 Gates Table

```sql
-- Migration: Sprint 173 — Gate State Machine
ALTER TABLE gates ADD COLUMN evaluated_at TIMESTAMP;
ALTER TABLE gates ADD COLUMN exit_criteria_version UUID DEFAULT gen_random_uuid();

-- Data migration: rename status values
UPDATE gates SET status = 'SUBMITTED' WHERE status = 'PENDING_APPROVAL';
UPDATE gates SET status = 'EVALUATED' WHERE status = 'IN_PROGRESS';
```

### 6.2 Gate Evidence Table

```sql
-- Migration: Sprint 173 — Evidence Contract
ALTER TABLE gate_evidence RENAME COLUMN sha256_hash TO sha256_client;
ALTER TABLE gate_evidence ADD COLUMN sha256_server VARCHAR(64);
ALTER TABLE gate_evidence ADD COLUMN criteria_snapshot_id UUID NOT NULL DEFAULT gen_random_uuid();
ALTER TABLE gate_evidence ADD COLUMN source VARCHAR(20) NOT NULL DEFAULT 'web';

CREATE INDEX idx_gate_evidence_criteria_snapshot ON gate_evidence(criteria_snapshot_id);
CREATE INDEX idx_gate_evidence_source ON gate_evidence(source);
```

---

## 7. Verification Criteria

### 7.1 3-Client Parity Test

```bash
# The SAME gate lifecycle must produce identical results via all 3 clients

# 1. Web API (direct curl)
curl -X POST /api/v1/gates/{id}/evaluate   → status=EVALUATED
curl -X POST /api/v1/gates/{id}/submit     → status=SUBMITTED
curl -X POST /api/v1/gates/{id}/approve    → status=APPROVED

# 2. CLI
sdlcctl gate evaluate {id}                 → "EVALUATED"
sdlcctl gate submit {id}                   → "SUBMITTED"
sdlcctl gate approve {id} -c "Approved"    → "APPROVED"

# 3. Extension
# Command Palette → SDLC: Approve Gate → select gate → comment → APPROVED
```

### 7.2 Edge Cases

| Scenario | Expected Behavior |
|----------|-------------------|
| Approve while DRAFT | 409 Conflict: "Gate must be SUBMITTED to approve" |
| Submit with missing evidence | 422: "Missing required evidence: security-scan" |
| Upload evidence while EVALUATED | Gate status → EVALUATED_STALE, 201 Created |
| Duplicate approve (same idempotency key) | 200 OK with same response body |
| Reject then re-evaluate | 200 OK: status → EVALUATED |
| Evidence upload with hash mismatch | 400: "SHA256 hash mismatch" |
| User with only governance:write tries to approve | 403: "Missing scope: governance:approve" |

---

*CONTRACT-GOVERNANCE-LOOP.md — SSOT for all gate governance interactions. All 3 clients MUST conform to this contract.*
