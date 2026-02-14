---
spec_id: SPEC-0011
title: Context Authority V2 - Gate-Aware Dynamic Context
version: "1.1.0"
status: APPROVED
tier:
  - STANDARD
  - PROFESSIONAL
  - ENTERPRISE
pillar: 7
owner: Backend Team
last_updated: 2026-02-11
related_adrs:
  - ADR-041
  - ADR-040
related_specs:
  - SPEC-0001
  - SPEC-0002
---

# SPEC-0011: Context Authority V2 - Gate-Aware Dynamic Context

## 1. Overview

### 1.1 Purpose

Context Authority V2 extends V1's metadata validation with **gate-aware dynamic context updates**. This transforms static AGENTS.md guidance into dynamic, project-state-aware governance.

### 1.2 Problem Statement

**Current State (V1 - Sprint 109)**:
- Validates ADR linkage, design docs, AGENTS.md freshness, module consistency
- Static validation: Same rules regardless of project stage
- Manual AGENTS.md updates required

**Gap Identified**:
- Context doesn't adapt to gate status
- No automatic guidance updates when gates pass/fail
- No integration with Vibecoding Index routing

### 1.3 Success Criteria

| Metric | Target | Measurement |
|--------|--------|-------------|
| Context update latency | <500ms | Time from gate change to context update |
| Developer confusion reduction | -50% | Survey: "Did you know what was required?" |
| Gate-aware violations | 95% accuracy | Violations appropriate for current stage |
| Dynamic AGENTS.md adoption | >80% | Projects with dynamic overlay enabled |

---

## 2. Functional Requirements

### FR-001: Gate Status Integration

```gherkin
GIVEN a project is in Stage 02 (Design)
WHEN a developer attempts to modify backend/app/services/**
THEN Context Authority V2 returns:
  - ERROR: "Code changes blocked until Gate G2 passes"
  - FIX: "Complete architecture review: docs/02-design/ADRs/"
  - CLI: "sdlcctl gate status"
```

### FR-002: Dynamic Context Overlay

```gherkin
GIVEN Gate G0.2 passes for a project
WHEN Context Authority calculates context
THEN AGENTS.md overlay includes:
  - "Design approved. Architecture in docs/02-design/"
  - "Proceed to Stage 04: BUILD"
  - "Required: Link code to ADRs"
```

### FR-003: Vibecoding Index Integration

```gherkin
GIVEN a submission has Vibecoding Index >60 (Orange)
WHEN Context Authority validates
THEN additional context is injected:
  - "⚠️ High Vibecoding Index detected"
  - "CEO review required before merge"
  - "Reduce: Architectural smell, AI dependency"
```

### FR-004: Section 7 Quality Assurance Alignment

```gherkin
GIVEN Section 7 (Quality Assurance System) is active
WHEN Context Authority validates a submission
THEN it applies tier-specific rules:
  - LITE: Minimal context checks
  - STANDARD: ADR linkage required
  - PROFESSIONAL: Full context validation
  - ENTERPRISE: Semantic validation (future V3)
```

### FR-005: Context Snapshot for Audit

```gherkin
GIVEN a PR is merged with Context Authority validation
WHEN audit is requested
THEN system provides:
  - Context snapshot at merge time
  - Gate status at merge time
  - Vibecoding Index at merge time
  - Dynamic overlay content at merge time
```

---

## 3. Technical Design

### 3.1 Architecture

```
┌────────────────────────────────────────────────────────────────┐
│                    Context Authority V2                        │
├────────────────────────────────────────────────────────────────┤
│                                                                │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐   │
│  │ Gate Status │  │ Vibecoding  │  │ Context Authority   │   │
│  │   Watcher   │  │   Index     │  │        V1           │   │
│  └──────┬──────┘  └──────┬──────┘  └──────────┬──────────┘   │
│         │                │                     │              │
│         ▼                ▼                     ▼              │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │              Context Aggregation Engine                  │ │
│  │                                                          │ │
│  │  - Combines gate status, index, V1 validation           │ │
│  │  - Calculates dynamic overlay                            │ │
│  │  - Generates tier-appropriate messages                   │ │
│  └─────────────────────────────────────────────────────────┘ │
│                           │                                   │
│                           ▼                                   │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │              Dynamic AGENTS.md Overlay                   │ │
│  │                                                          │ │
│  │  - Base AGENTS.md (static)                              │ │
│  │  + Gate-aware section (dynamic)                         │ │
│  │  + Index-aware warnings (dynamic)                       │ │
│  │  + Stage-specific guidance (dynamic)                    │ │
│  └─────────────────────────────────────────────────────────┘ │
│                                                                │
└────────────────────────────────────────────────────────────────┘
```

### 3.2 Database Schema Extensions

```sql
-- V2 additions to existing context_authorities table
ALTER TABLE context_authorities ADD COLUMN gate_status JSONB;
ALTER TABLE context_authorities ADD COLUMN vibecoding_index INTEGER;
ALTER TABLE context_authorities ADD COLUMN dynamic_overlay TEXT;
ALTER TABLE context_authorities ADD COLUMN tier VARCHAR(20);

-- New table: context_overlay_templates
CREATE TABLE context_overlay_templates (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    trigger_type VARCHAR(50) NOT NULL,  -- 'gate_pass', 'gate_fail', 'index_zone'
    trigger_value VARCHAR(100) NOT NULL, -- 'G0.2', 'G1', 'orange', 'red'
    tier VARCHAR(20),                    -- NULL = all tiers
    overlay_content TEXT NOT NULL,
    priority INTEGER DEFAULT 0,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- New table: context_snapshots (audit trail)
CREATE TABLE context_snapshots (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    submission_id UUID NOT NULL REFERENCES governance_submissions(id),
    gate_status JSONB NOT NULL,
    vibecoding_index INTEGER NOT NULL,
    dynamic_overlay TEXT NOT NULL,
    tier VARCHAR(20) NOT NULL,
    snapshot_at TIMESTAMPTZ DEFAULT NOW(),
    INDEX idx_context_snapshots_submission (submission_id)
);
```

### 3.3 API Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/context-authority/v2/validate` | POST | Gate-aware context validation |
| `/context-authority/v2/overlay/{project_id}` | GET | Get dynamic overlay for project |
| `/context-authority/v2/templates` | GET/POST | Manage overlay templates |
| `/context-authority/v2/snapshot/{submission_id}` | GET | Get context snapshot |

### 3.4 Service Interface

```python
class ContextAuthorityEngineV2(ContextAuthorityEngineV1):
    """
    Context Authority V2 - Gate-Aware Dynamic Context.

    Extends V1 with:
    - Gate status integration
    - Vibecoding Index awareness
    - Dynamic AGENTS.md overlay
    - Context snapshots for audit
    """

    async def validate_context_v2(
        self,
        submission: CodeSubmission,
        gate_status: GateStatus,
        vibecoding_index: int,
    ) -> ContextValidationResultV2:
        """
        Validate context with gate and index awareness.
        """
        # Run V1 validation first
        v1_result = await super().validate_context(submission)

        # Add gate-aware violations
        gate_violations = await self._check_gate_constraints(
            submission, gate_status
        )

        # Add index-aware warnings
        index_warnings = await self._check_index_constraints(
            submission, vibecoding_index
        )

        # Calculate dynamic overlay
        overlay = await self._calculate_dynamic_overlay(
            gate_status, vibecoding_index, submission.tier
        )

        # Create snapshot for audit
        await self._create_snapshot(
            submission, gate_status, vibecoding_index, overlay
        )

        return ContextValidationResultV2(
            v1_result=v1_result,
            gate_violations=gate_violations,
            index_warnings=index_warnings,
            dynamic_overlay=overlay,
        )

    async def get_dynamic_overlay(
        self,
        project_id: UUID,
    ) -> DynamicOverlay:
        """
        Get current dynamic overlay for project.

        Returns:
            AGENTS.md base + dynamic sections
        """
        # Get current gate status
        gate_status = await self._get_gate_status(project_id)

        # Get recent vibecoding index
        recent_index = await self._get_recent_index(project_id)

        # Get project tier
        tier = await self._get_project_tier(project_id)

        # Calculate overlay
        return await self._calculate_dynamic_overlay(
            gate_status, recent_index, tier
        )
```

---

## 4. Dynamic Overlay Templates

### 4.1 Gate Pass Templates

```yaml
# When Gate G0.2 passes
trigger_type: gate_pass
trigger_value: G0.2
overlay_content: |
  ## 🎯 Current Status: Design Approved

  Gate G0.2 (Solution Diversity) PASSED on {date}.

  **You may now:**
  - Write code in `backend/app/` and `frontend/src/`
  - Create new services and components
  - Implement features per approved ADRs

  **Required for all code:**
  - Link to ADR: `@adr ADR-XXX` in file header
  - Test coverage: 80% minimum
  - BDD format for new features

  **Reference:**
  - Architecture: docs/02-design/03-ADRs/
  - Specs: docs/02-design/14-Technical-Specs/
```

### 4.2 Index Zone Templates

```yaml
# When Vibecoding Index is Orange (61-80)
trigger_type: index_zone
trigger_value: orange
overlay_content: |
  ## ⚠️ Vibecoding Index: ORANGE ({index})

  This submission requires CEO review before merge.

  **Top Contributing Signals:**
  {top_signals}

  **Suggested Actions:**
  - Review architectural patterns
  - Reduce AI dependency ratio
  - Consider breaking into smaller PRs

  **Escalation:**
  - Queue: CEO Review Queue
  - SLA: 24 hours
```

### 4.3 Stage Constraint Templates

```yaml
# When in Stage 02 (Design) trying to modify code
trigger_type: stage_constraint
trigger_value: stage_02_code_block
overlay_content: |
  ## 🚫 Stage Constraint: Code Blocked

  Current Stage: **02 - Design**

  **Code changes are blocked because:**
  - Architecture not yet approved (Gate G2 pending)
  - Design documents incomplete

  **To proceed:**
  1. Complete ADRs: docs/02-design/03-ADRs/
  2. Request Gate G2 review: `sdlcctl gate request G2`
  3. Wait for approval

  **Allowed changes in Stage 02:**
  - docs/02-design/**
  - prisma/schema.prisma (schema design only)
  - openapi/** (API contracts)
```

---

## 5. Tier Requirements

| Requirement | LITE | STANDARD | PROFESSIONAL | ENTERPRISE |
|-------------|------|----------|--------------|------------|
| V1 validation | Optional | MANDATORY | MANDATORY | MANDATORY |
| Gate awareness | N/A | MANDATORY | MANDATORY | MANDATORY |
| Index integration | N/A | RECOMMENDED | MANDATORY | MANDATORY |
| Dynamic overlay | N/A | RECOMMENDED | MANDATORY | MANDATORY |
| Context snapshots | N/A | N/A | MANDATORY | MANDATORY |
| Semantic validation | N/A | N/A | N/A | PLANNED (V3) |

---

## 6. Implementation Plan

### Phase 1: Database & Models (Sprint 120)
- [ ] Add columns to `context_authorities` table
- [ ] Create `context_overlay_templates` table
- [ ] Create `context_snapshots` table
- [ ] SQLAlchemy models for new tables
- **Estimated**: ~300 LOC

### Phase 2: Service Layer (Sprint 120)
- [ ] Extend `ContextAuthorityEngineV1` → `V2`
- [ ] Implement `_check_gate_constraints()`
- [ ] Implement `_check_index_constraints()`
- [ ] Implement `_calculate_dynamic_overlay()`
- [ ] Implement `_create_snapshot()`
- **Estimated**: ~500 LOC

### Phase 3: API Endpoints (Sprint 121)
- [ ] `POST /context-authority/v2/validate`
- [ ] `GET /context-authority/v2/overlay/{project_id}`
- [ ] `GET/POST /context-authority/v2/templates`
- [ ] `GET /context-authority/v2/snapshot/{submission_id}`
- **Estimated**: ~400 LOC

### Phase 4: Integration Tests (Sprint 121)
- [ ] Gate constraint tests (stage blocking)
- [ ] Index integration tests (zone routing)
- [ ] Overlay template tests
- [ ] Snapshot audit tests
- **Estimated**: ~500 LOC

---

## 7. Migration from V1

### 7.1 Backward Compatibility

- V1 API remains functional (`/context-authority/validate`)
- V2 API is additive (`/context-authority/v2/validate`)
- Existing integrations continue working

### 7.2 Migration Path

1. **Week 1**: Deploy V2 alongside V1
2. **Week 2**: Enable V2 for new projects
3. **Week 3**: Migrate existing projects (opt-in)
4. **Week 4**: Deprecation notice for V1-only usage

---

## 8. Risks and Mitigations

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Gate status sync delay | Medium | Low | Redis cache with 30s TTL |
| Overlay template conflicts | Low | Medium | Priority field + conflict detection |
| Performance degradation | Low | High | Async processing, caching |
| Breaking V1 compatibility | Low | High | Separate API version path |

---

## 9. Success Metrics

### 9.1 Adoption Metrics

| Metric | Week 2 | Week 4 | Week 8 |
|--------|--------|--------|--------|
| V2 API usage | 20% | 50% | 80% |
| Dynamic overlay enabled | 10% | 40% | 70% |
| Context snapshots stored | 100/day | 500/day | 1000/day |

### 9.2 Quality Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| Gate-aware accuracy | 95% | Violations match current stage |
| Overlay helpfulness | NPS >50 | Developer survey |
| Audit completeness | 100% | Snapshots for all merges |

---

## 10. Document Control

| Field | Value |
|-------|-------|
| **Version** | 1.1.0 |
| **Created** | January 29, 2026 |
| **Updated** | February 11, 2026 |
| **Author** | Backend Team |
| **Status** | APPROVED |
| **Sprint** | 119 (Day 5), Updated Sprint 172+ |
| **Framework** | SDLC 6.0.5 (7-Pillar) |
| **Decision** | EXTEND (Context Authority V2) |

---

## 11. Known Issues & Fixes

### 11.1 BUG-001: Gate Status Mapping Mismatch (Fixed Feb 11, 2026)

**Symptom**: Extension Context Overlay showed "G3 Pending" while Gate Status panel showed "G3 Approved".

**Root Cause**: Two data source inconsistencies:

1. **`ContextOverlayService._get_stage_and_gate()`** compared gate status using lowercase `'passed'`, but the Gate model stores status as UPPERCASE (`"APPROVED"`, `"REJECTED"`). The mapping was also wrong - DB uses `"APPROVED"` not `"passed"`:

```python
# BUG (before fix):
gate_status = f"{gate.gate_name} {'PASSED' if gate.status == 'passed' else 'PENDING'}"
# gate.status is "APPROVED" (UPPERCASE) → never equals 'passed' → always shows PENDING
```

2. **`DynamicContextService.load_context()`** had a TODO stub that never loaded gate data from the database. On server restart, all projects defaulted to `GateStatus.PENDING`.

**Fix Applied**:

| File | Change |
|------|--------|
| `context_overlay_service.py` | Rewrote `_get_stage_and_gate()` to query highest APPROVED gate first, with proper UPPERCASE status mapping (`APPROVED→PASSED`, `REJECTED→FAILED`, etc.) |
| `dynamic_context_service.py` | Implemented `load_context()` to hydrate in-memory context from gates table on cold start (only when `update_count == 0`) |
| `agents_md.py` | Changed endpoint to call `load_context()` instead of `_get_or_create_context()` |

**Lesson Learned**: When two views display the same data from different API sources, ensure both sources use the same status enum system or normalize at the API boundary. Gate model uses `APPROVED/REJECTED/DRAFT` while DynamicContext uses `PASSED/FAILED/PENDING` - the mapping between these must be explicit.

---

## Changelog

### v1.1.0 (February 11, 2026)
- **BUG-001 FIX**: Gate status mapping mismatch between Context Overlay and Gate Status
- Added Section 11 (Known Issues & Fixes)
- Updated status to APPROVED (was DRAFT)
- Documented dual-enum mapping lesson (Gate model vs DynamicContext)

### v1.0.0 (January 29, 2026)
- Initial specification
- Day 5 decision: EXTEND over ADOPT/DEFER
- Defined 5 functional requirements
- Database schema extensions
- 4-phase implementation plan
- Sprint 120-121 roadmap
