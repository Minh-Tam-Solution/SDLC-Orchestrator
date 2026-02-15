# ADR-053: Governance Loop State Machine

**Status**: Accepted
**Date**: February 15, 2026
**Author**: CTO + Enterprise Architect + SDLC Expert
**Sprint**: Sprint 173 ("Sharpen, Don't Amputate")
**Authority**: CTO Approved v4 FINAL — All reviewers (CTO, Architect v2, SDLC Expert v2)
**Supersedes**: Partial gate lifecycle logic in ADR-052 (Tier-Based Gate Approval Architecture)
**References**: ADR-052, FR1 (Quality Gate Management), CONTRACT-GOVERNANCE-LOOP.md

---

## 1. Context

### Problem Statement

The SDLC Orchestrator governance loop is incomplete across its 3 client interfaces:

```
Current State (Before Sprint 173):
  Web UI:      ✅ View gates → ✅ Evaluate → ✅ Approve → ✅ Evidence
  CLI:         ✅ Validate → ❌ NO gate commands → ❌ NO evidence submit
  Extension:   ✅ View violations → ❌ NO gate actions → ❌ NO evidence
```

The gate lifecycle has 5 implicit states (`DRAFT`, `PENDING_APPROVAL`, `IN_PROGRESS`, `APPROVED`, `REJECTED`) with no formal state machine, no idempotency guards, and no server-driven capability discovery. Permission logic is scattered across client-side code, creating drift between what different clients allow.

### Current Gate Model Status Values

```python
# backend/app/models/gate.py (current)
status = Column(String(20), nullable=False, default="DRAFT")
# Values: DRAFT, PENDING_APPROVAL, IN_PROGRESS, APPROVED, REJECTED, ARCHIVED
```

### Identified Issues

1. **No formal state machine**: Transitions are implicit, not enforced. A gate can be approved directly from DRAFT via API.
2. **No evaluation state**: Gates skip from DRAFT to PENDING_APPROVAL without a formal evaluation step.
3. **No evidence invalidation**: Uploading new evidence after evaluation does not invalidate the evaluation result.
4. **Client-side permissions**: Each client (Web, CLI, Extension) independently computes what actions are allowed — leading to inconsistency.
5. **No idempotency**: Duplicate approve/reject calls create duplicate records.
6. **Single auth scope**: `governance:write` covers both evaluate/submit AND approve/reject — insufficient separation of duties.
7. **Evidence integrity**: Only client-side SHA256 hash — no server-side re-verification. No binding between evidence and gate exit criteria version.

---

## 2. Decision

Implement a **6-state gate state machine** with server-enforced transitions, a shared `compute_gate_actions()` function as the single source of truth for permissions, separated auth scopes, Redis-based idempotency, and a formal evidence contract with server-side hash verification.

### 2.1 Gate State Machine

```mermaid
stateDiagram-v2
    [*] --> DRAFT : create_gate()

    DRAFT --> EVALUATED : evaluate
    EVALUATED --> SUBMITTED : submit (requires missing_evidence=[])
    EVALUATED --> EVALUATED_STALE : evidence_upload
    EVALUATED_STALE --> EVALUATED : re-evaluate
    SUBMITTED --> APPROVED : approve (governance:approve)
    SUBMITTED --> REJECTED : reject (governance:approve)
    REJECTED --> EVALUATED : re-evaluate

    APPROVED --> [*]

    note right of EVALUATED_STALE : Triggered when evidence\nuploaded after evaluation
    note right of REJECTED : CTO Mod 2: re-evaluate allowed
```

**States**:

| State | Description | Entry Condition |
|-------|-------------|-----------------|
| `DRAFT` | Gate created, no evaluation yet | `create_gate()` |
| `EVALUATED` | Exit criteria evaluated against evidence | `evaluate` from DRAFT, EVALUATED_STALE, or REJECTED |
| `EVALUATED_STALE` | Evaluation invalidated by new evidence upload | `evidence_upload` while EVALUATED |
| `SUBMITTED` | Submitted for approval review | `submit` from EVALUATED (requires `missing_evidence = []`) |
| `APPROVED` | Approved by authorized reviewer | `approve` from SUBMITTED |
| `REJECTED` | Rejected by authorized reviewer (re-evaluate allowed) | `reject` from SUBMITTED |

**Note**: The existing `ARCHIVED` status is preserved as a separate lifecycle concern (soft-delete semantics), not part of the governance state machine. `PENDING_APPROVAL` is renamed to `SUBMITTED` for semantic clarity. `IN_PROGRESS` is removed (absorbed by `EVALUATED`).

### 2.2 Transition Guards (Server-Side Only)

```python
# backend/app/services/gate_service.py

VALID_TRANSITIONS: dict[str, dict[str, str]] = {
    "evaluate": {
        "allowed_from": ["DRAFT", "EVALUATED", "EVALUATED_STALE", "REJECTED"],
        "target_state": "EVALUATED",
        "required_scope": "governance:write",
    },
    "submit": {
        "allowed_from": ["EVALUATED"],
        "target_state": "SUBMITTED",
        "required_scope": "governance:write",
        "precondition": "missing_evidence == []",
    },
    "approve": {
        "allowed_from": ["SUBMITTED"],
        "target_state": "APPROVED",
        "required_scope": "governance:approve",
    },
    "reject": {
        "allowed_from": ["SUBMITTED"],
        "target_state": "REJECTED",
        "required_scope": "governance:approve",
    },
}
```

**Evidence upload side-effect**: If gate status is `EVALUATED`, set to `EVALUATED_STALE` (forces re-evaluation before submission).

### 2.3 Shared `compute_gate_actions()` Function (SSOT Invariant)

**SDLC Expert v2 requirement**: The `GET /gates/{id}/actions` endpoint and ALL mutation endpoints (evaluate, submit, approve, reject) MUST use the **same shared function**. No drift between what `/actions` reports and what mutations enforce.

```python
def compute_gate_actions(gate: Gate, user: User) -> GateActions:
    """
    Single source of truth for gate action permissions.

    Used by:
    - GET /gates/{id}/actions (capability discovery)
    - POST /gates/{id}/evaluate (transition guard)
    - POST /gates/{id}/submit (transition guard)
    - POST /gates/{id}/approve (transition guard)
    - POST /gates/{id}/reject (transition guard)

    Args:
        gate: Gate model instance with current status
        user: Authenticated user with scopes

    Returns:
        GateActions with can_* booleans and reasons dict
    """
    user_scopes = get_user_scopes(user)
    has_write = "governance:write" in user_scopes
    has_approve = "governance:approve" in user_scopes

    evidence = get_gate_evidence(gate.id)
    required = get_required_evidence_types(gate.exit_criteria)
    submitted = {e.evidence_type for e in evidence}
    missing = required - submitted

    actions = {
        "can_evaluate": gate.status in ["DRAFT", "EVALUATED", "EVALUATED_STALE", "REJECTED"] and has_write,
        "can_submit": gate.status == "EVALUATED" and has_write and len(missing) == 0,
        "can_approve": gate.status == "SUBMITTED" and has_approve,
        "can_reject": gate.status == "SUBMITTED" and has_approve,
        "can_upload_evidence": gate.status not in ["APPROVED", "ARCHIVED"] and has_write,
    }

    reasons = {}
    if not actions["can_evaluate"]:
        if not has_write:
            reasons["can_evaluate"] = "Missing scope: governance:write"
        else:
            reasons["can_evaluate"] = f"Cannot evaluate from status: {gate.status}"
    if not actions["can_submit"]:
        if gate.status != "EVALUATED":
            reasons["can_submit"] = f"Gate must be EVALUATED to submit (current: {gate.status})"
        elif len(missing) > 0:
            reasons["can_submit"] = f"Missing required evidence: {', '.join(missing)}"
        elif not has_write:
            reasons["can_submit"] = "Missing scope: governance:write"
    if not actions["can_approve"]:
        if not has_approve:
            reasons["can_approve"] = "Missing scope: governance:approve"
        else:
            reasons["can_approve"] = f"Gate must be SUBMITTED to approve (current: {gate.status})"
    if not actions["can_reject"]:
        if not has_approve:
            reasons["can_reject"] = "Missing scope: governance:approve"
        else:
            reasons["can_reject"] = f"Gate must be SUBMITTED to reject (current: {gate.status})"

    return GateActions(
        gate_id=str(gate.id),
        status=gate.status,
        actions=actions,
        reasons=reasons,
        required_evidence=list(required),
        submitted_evidence=list(submitted),
        missing_evidence=list(missing),
    )
```

### 2.4 Auth Scopes (Separated)

| Scope | Allowed Actions | Primary Interface |
|-------|----------------|-------------------|
| `governance:write` | evaluate, submit, upload evidence | CLI (DevOps), Extension (Dev) |
| `governance:approve` | approve, reject | Web (Manager), CLI (with explicit flag) |

**Rationale (SDLC Expert v2)**: Separation of duties — developers who submit evidence should not be able to approve their own gates. Managers who approve should not need code-level access.

### 2.5 API Endpoints

| Method | Endpoint | Auth Scope | Purpose |
|--------|----------|------------|---------|
| `GET` | `/gates/{id}/actions` | `governance:write` OR `governance:approve` | Server-driven capability discovery |
| `POST` | `/gates/{id}/evaluate` | `governance:write` | Evaluate gate criteria |
| `POST` | `/gates/{id}/submit` | `governance:write` | Submit for approval (blocked if missing evidence) |
| `POST` | `/gates/{id}/approve` | `governance:approve` | Approve gate (**separate endpoint** — CTO Mod 1) |
| `POST` | `/gates/{id}/reject` | `governance:approve` | Reject gate (**separate endpoint** — CTO Mod 1) |

### 2.6 Idempotency (Redis)

```
Key pattern: idempotency:{user_id}:{endpoint}:{gate_id}:{idempotency_key}
Value: JSON response body from first execution
TTL: 86400 seconds (24 hours)
Storage: Redis (port 6395, already in stack)
```

- Client sends `X-Idempotency-Key` header (UUID per command/click)
- If key exists → return **stored response body** (not just no-op)
- Key scope includes `user_id` to prevent cross-user collision
- CLI generates UUID per command invocation
- Extension generates UUID per button click

### 2.7 Evidence Contract

Every evidence upload MUST include:

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `sha256_client` | String(64) | Required if `source` in [cli, extension, web]; Optional if `source=other` | Client-computed SHA256 |
| `size_bytes` | BigInteger | Required | File size |
| `mime_type` | String(100) | Required | MIME type |
| `source` | String(20) | Required | `cli`, `extension`, `web`, `other` |
| `created_by` | UUID | Required | From auth token |
| `gate_id` | UUID | Required | Target gate |
| `criteria_snapshot_id` | UUID | Required | Binding to gate's current exit_criteria version |

**Server-side on upload**:
1. Recompute SHA256 from received bytes → `sha256_server`
2. If `sha256_client` provided: compare — reject if mismatch (corruption/tampering)
3. If `sha256_client` absent (`source=other`): log warning "Untrusted client source"
4. Store both hashes in DB: `sha256_client` + `sha256_server`
5. Store file in MinIO with object versioning
6. If gate status is `EVALUATED` → set status to `EVALUATED_STALE`

---

## 3. Database Migration Required

### 3.1 Gate Model Changes

```sql
-- Rename PENDING_APPROVAL → SUBMITTED
UPDATE gates SET status = 'SUBMITTED' WHERE status = 'PENDING_APPROVAL';

-- Remove IN_PROGRESS (absorbed by EVALUATED)
UPDATE gates SET status = 'EVALUATED' WHERE status = 'IN_PROGRESS';

-- Add exit_criteria_version for snapshot binding
ALTER TABLE gates ADD COLUMN exit_criteria_version UUID DEFAULT gen_random_uuid();

-- Add evaluated_at timestamp
ALTER TABLE gates ADD COLUMN evaluated_at TIMESTAMP;
```

**New valid status values**: `DRAFT`, `EVALUATED`, `EVALUATED_STALE`, `SUBMITTED`, `APPROVED`, `REJECTED`, `ARCHIVED`

### 3.2 GateEvidence Model Changes

```sql
-- Rename sha256_hash → sha256_client (semantic clarity)
ALTER TABLE gate_evidence RENAME COLUMN sha256_hash TO sha256_client;

-- Add server-side hash verification
ALTER TABLE gate_evidence ADD COLUMN sha256_server VARCHAR(64);

-- Add criteria snapshot binding (explicit, not implicit)
ALTER TABLE gate_evidence ADD COLUMN criteria_snapshot_id UUID NOT NULL DEFAULT gen_random_uuid();

-- Add upload source tracking
ALTER TABLE gate_evidence ADD COLUMN source VARCHAR(20) NOT NULL DEFAULT 'web';

-- Create index for criteria snapshot lookups
CREATE INDEX idx_gate_evidence_criteria_snapshot ON gate_evidence(criteria_snapshot_id);
```

---

## 4. Consequences

### 4.1 Positive

- **Complete governance loop**: All 3 clients (Web, CLI, Extension) share the same gate lifecycle
- **No permission drift**: Single `compute_gate_actions()` function eliminates client-side permission computation
- **Idempotent mutations**: Redis-based idempotency prevents duplicate operations, returns consistent responses
- **Evidence integrity**: Server-side SHA256 re-verification detects corruption/tampering
- **Separation of duties**: `governance:write` vs `governance:approve` enforces role-based access
- **Re-evaluation path**: REJECTED gates can be re-evaluated (CTO Mod 2), enabling iterative improvement
- **Stale detection**: EVALUATED_STALE forces re-evaluation when evidence changes post-evaluation

### 4.2 Negative

- **DB migration**: Requires Alembic migration for both `gates` and `gate_evidence` tables (adds 0.5 day)
- **State rename**: `PENDING_APPROVAL → SUBMITTED` requires updating all client code and tests that reference old status
- **Redis dependency**: Idempotency requires Redis availability — must handle Redis downtime gracefully (skip idempotency check, log warning)
- **API surface increase**: 5 new/modified endpoints increase maintenance burden

### 4.3 Risks

| Risk | Mitigation |
|------|------------|
| Redis downtime breaks idempotency | Graceful degradation: if Redis unavailable, skip idempotency check + log warning |
| Migration breaks existing gates in PENDING_APPROVAL | Alembic migration explicitly handles data migration (UPDATE SET) |
| Clients cache old status values | API response always uses new status values; clients update on next fetch |
| SHA256 mismatch false positives from network corruption | Return 400 with clear error message; client can retry upload |

---

## 5. Alternatives Rejected

### 5.1 Client-Side Permission Computation

Rejected because: each client would implement its own permission logic, leading to drift. Web might allow approve while CLI blocks it for the same gate state.

### 5.2 Single Approve/Reject Endpoint

Rejected (CTO Mod 1): `POST /gates/{id}/approve` with `action: "reject"` in body creates semantic confusion. CLI `sdlcctl gate reject` calling an "approve" endpoint is misleading. Separate endpoints provide clarity.

### 5.3 Optimistic Locking Instead of Idempotency

Rejected because: optimistic locking prevents conflicts but doesn't handle network retries (client sends same request twice due to timeout). Redis idempotency handles both.

### 5.4 Database-Based Idempotency

Rejected because: Redis is already in the stack (port 6395), provides TTL natively (24h auto-cleanup), and avoids adding a new table. Database approach would require a cleanup cron job.

---

## 6. Implementation Plan

| Phase | Deliverable | Effort |
|-------|-------------|--------|
| Pre-Phase (Day 1) | State machine + `compute_gate_actions()` + DB migration + idempotency middleware | 0.5-1 day |
| Phase 1.1 (Day 2-3) | CLI gate commands (7 commands) | 2 days |
| Phase 1.2 (Day 4) | CLI evidence submit with contract | 1 day |
| Phase 1.3 (Day 5-7) | Extension gate actions + evidence submission | 2.5 days |

**Verification**: All 3 clients produce identical results for the same gate lifecycle:
```
create → evaluate → submit → approve = APPROVED (via Web, CLI, Extension)
```

---

## 7. Review History

| Version | Reviewer | Verdict |
|---------|----------|---------|
| v1 | CTO | Partially Approved — "Sharpen, Don't Amputate" |
| v2 | Architect v1 | Approved w/ 3 fixes (CLI UX, Optimistic UI, Auth) |
| v2 | SDLC Expert v1 | Approved w/ 6 safety rails |
| v3 | Architect v2 | Approved — Grade A |
| v3 | SDLC Expert v2 | Approved w/ 6 P0 fixes |
| v3 | CTO | Approved w/ 8 mandatory modifications |
| **v4 FINAL** | **All** | **Approved for execution** |

---

## 8. Approval

- **CTO**: Approved (Feb 15, 2026)
- **Enterprise Architect**: Approved — Grade A
- **SDLC Expert**: Approved w/ all P0 fixes incorporated
- **Sprint**: 173 Pre-Phase → Phase 1

---

*ADR-053 — Gate Governance Loop State Machine. Formalizes the 6-state lifecycle, server-driven actions, separated auth scopes, and evidence contract for 3-client parity.*
