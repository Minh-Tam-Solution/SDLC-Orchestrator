# ADR-052: Tier-Based Gate Approval Architecture

**Status**: ✅ Accepted
**Date**: February 6, 2026
**Author**: CTO + Enterprise Architect
**Sprint**: Sprint 161 - Tier-Based Gate Approval Backend Foundation
**Authority**: CTO Approved (v2.5 - Score: 92/100)

---

## Context

### Problem Statement

Sprint 159 staging validation revealed a critical gap in the gate approval system:

**Current System (Sprint 159 - SYSTEM ROLE ONLY)**:
- User has CEO role → Can approve ANY gate in ANY project
- No differentiation by project tier (FREE vs ENTERPRISE)
- Doesn't scale to multi-project scenarios
- Cross-organization authorization fails

**Example Issue**:
```yaml
User: Bob (CEO in Organization A)
Project X: Organization B, Bob is Member role, STANDARD tier
Gate: G2 (Design Ready)

Current Behavior: Bob can approve (wrong!)
Expected Behavior: Approval request to Project X's CTO
Rationale: Project membership trumps organizational role
```

**Root Cause**: System-role-based approval doesn't support project-tier-based routing.

---

## Decision

Implement **4-Level RBAC Hierarchy with Project-Tier-Based Approval Routing**.

### Architecture Overview

```yaml
4-Level RBAC Hierarchy:
  1. Platform Level: is_platform_admin (system operations)
  2. Organization Level: Org membership role (admin/member/viewer)
  3. Team Level: Team membership role (admin/member/viewer)
  4. Project Level: Project membership + TIER + Functional Roles ⭐ NEW

Key Components:
  - Project Tier: FREE/STANDARD/PROFESSIONAL/ENTERPRISE
  - Functional Roles: PM/CTO/CEO/QA_LEAD/COMPLIANCE_OFFICER (per-project)
  - Event Log Pattern: gate_decisions table (NOT state machine)
  - Approval Chain: (chain_id, step_index) tuple for council review
```

---

## Key Architectural Decisions

### Decision 1: Separate Access Control from Approval Authority

**Problem**: project_members.role (owner/admin/member/viewer) conflates access control with approval authority.

**Solution**: New table `project_function_roles` for approval-specific roles.

**Example**:
```yaml
User: Alice
Access Control (project_members):
  - Project A: role='member' (can view/edit project)

Approval Authority (project_function_roles):
  - Project A: functional_role='PM' (can approve gates)

Result: Alice can view/edit (member) AND approve G1 (PM)
```

**Benefits**:
- Clear separation of concerns
- Same user can have different approval authority per project
- Solves "PM/CTO/CEO roles don't have data source per project" (Enterprise Architect feedback)

---

### Decision 2: Event Log Pattern (NOT State Machine)

**Problem**: Initial Sprint 161 v1 design used 3 tables with complex FK chains for state machine.

**Enterprise Architect Feedback**:
- "Over-engineering in wrong places" - trying to build workflow engine in Sprint 161
- State machine adds coupling and complexity
- Hard to audit multi-approver scenarios (ENTERPRISE council review)

**Solution**: Single `gate_decisions` table with event log pattern.

**Event Log Structure**:
```sql
CREATE TABLE gate_decisions (
    id UUID PRIMARY KEY,
    gate_id UUID NOT NULL,
    chain_id UUID NOT NULL,        -- Groups related decisions
    step_index INTEGER NOT NULL,   -- Sequential step (0-based)
    action decision_action NOT NULL,  -- REQUEST/APPROVE/REJECT/ESCALATE
    status decision_status DEFAULT 'PENDING',  -- PENDING/COMPLETED/CANCELLED
    ...
    UNIQUE(gate_id, chain_id, step_index)
);
```

**Council Review Example** (ENTERPRISE tier, 3 approvers):
```yaml
Decision 1:
  chain_id: abc-123
  step_index: 0
  required_roles: ['CTO']
  status: PENDING

Decision 2:
  chain_id: abc-123  # Same chain!
  step_index: 1
  required_roles: ['CEO']
  status: PENDING

Decision 3:
  chain_id: abc-123  # Same chain!
  step_index: 2
  required_roles: ['COMPLIANCE_OFFICER']
  status: PENDING
```

**Benefits**:
- Simpler schema (1 table vs 3 tables)
- Easier to audit (append-only log)
- Chain logic derived from data (chain_id + step_index)
- No workflow engine complexity in Sprint 161

---

### Decision 3: Hardcoded Approval Rules (OPA in Sprint 162)

**Problem**: Should Sprint 161 implement OPA policy integration immediately?

**Decision**: No. Sprint 161 uses hardcoded `DEFAULT_APPROVAL_CHAINS` constant.

**Rationale**:
- Sprint 161 focus: Backend foundation (schema + service skeleton)
- OPA integration adds complexity (policy authoring, testing, deployment)
- Hardcoded rules sufficient for Sprint 161 validation
- Sprint 162 will replace with OPA policies

**Hardcoded Rules**:
```python
DEFAULT_APPROVAL_CHAINS = {
    "FREE": {},  # Self-approval
    "STANDARD": {
        "G1": ["PM"],
        "G2": ["CTO"],
        "G3": ["CTO"],
        ...
    },
    "PROFESSIONAL": {
        "G1": ["PM", "CTO"],
        "G3": ["CTO", "CEO"],
        ...
    },
    "ENTERPRISE": {
        "G5": ["CTO", "CEO", "COMPLIANCE_OFFICER"],  # Council
        ...
    },
}
```

---

### Decision 4: NO Gate Finalization in Sprint 161

**Problem**: Should Sprint 161 update `gate.status` after approval?

**Decision**: No. Gate finalization deferred to Sprint 164.

**Rationale**:
- Sprint 161 scope: Decision recording only
- Gate finalization requires complex orchestration:
  - Check all required approvals received?
  - Handle partial approvals?
  - Send notifications?
  - Update SDLC stage transitions?
- Sprint 164 will implement `GateFinalizationService`

**Sprint 161 Behavior**:
```python
async def record_decision(...) -> GateDecision:
    # Update decision record
    decision.action = action
    decision.status = "COMPLETED"

    # NOTE: Gate finalization deferred to Sprint 164
    # Sprint 161 only records decision, does not update gate.status

    return decision
```

---

### Decision 5: CTO v2.5 Adjustments

**Context**: After Sprint 161 v2 plan, CTO mandated 3 adjustments.

**Adjustment #1: Add ESCALATE to decision_action ENUM**
```sql
CREATE TYPE decision_action AS ENUM (
    'REQUEST',
    'APPROVE',
    'REJECT',
    'ESCALATE',  -- ⭐ CTO v2.5 addition
    'COMMENT'
);
```

**Rationale**: Support escalation workflow in Sprint 162 (PM → CTO → CEO).

---

**Adjustment #2: Add expires_at column with partial index**
```sql
ALTER TABLE gate_decisions
ADD COLUMN expires_at TIMESTAMP;

-- Partial index for timeout queries
CREATE INDEX idx_pending_expiring ON gate_decisions(expires_at)
WHERE status = 'PENDING' AND expires_at IS NOT NULL;
```

**Rationale**: Enable auto-escalation on timeout (Sprint 162 background task).

---

**Adjustment #3: Return ApprovalChainMetadata (not List[UUID])**
```python
@dataclass
class ApprovalChainMetadata:
    chain_id: UUID
    decision_ids: List[UUID]
    required_roles: List[str]
    expires_at: Optional[datetime]
    is_self_approval: bool
```

**Rationale**: Service consumers need rich context about approval chain, not just decision IDs.

---

## Project Tiers & Approval Chains

### Tier Definitions

| Tier | Self-Approval | Approval Chain | Council Review | Use Case |
|------|--------------|----------------|----------------|----------|
| **FREE** | ✅ Yes (all gates) | N/A | ❌ No | Personal projects, prototypes |
| **STANDARD** | ❌ No | PM → CTO | ❌ No | SME teams (5-10 people) |
| **PROFESSIONAL** | ❌ No | PM → CTO → CEO | ❌ No | Mid-size (10-50 people) |
| **ENTERPRISE** | ❌ No | PM → CTO → CEO | ✅ Yes (critical gates) | Large (50+ people) |

---

### Approval Chain Matrix

| Tier | G0.1 | G0.2 | G1 | G2 | G3 | G4 | G5 | G6 |
|------|------|------|----|----|----|----|----|----|
| **FREE** | Self | Self | Self | Self | Self | Self | Self | Self |
| **STANDARD** | Self | Self | PM | CTO | CTO | QA | CTO | CEO |
| **PROFESSIONAL** | Self | Self | PM+CTO | CTO | CTO+CEO | QA | CTO+CEO | CEO |
| **ENTERPRISE** | Self | Self | PM+CTO | CTO | CTO+CEO | QA+CO | CTO+CEO+CO | CEO+CO |

**Legend**:
- Self = Self-approval allowed
- PM = Project Manager
- CTO = Chief Technology Officer
- CEO = Chief Executive Officer
- QA = QA Lead
- CO = Compliance Officer
- `+` = Council review (all must approve)

---

## Database Schema

### Table 1: project_function_roles

**Purpose**: Map functional approval roles per-project.

```sql
CREATE TABLE project_function_roles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    functional_role functional_role NOT NULL,
    assigned_at TIMESTAMP NOT NULL DEFAULT NOW(),
    assigned_by UUID REFERENCES users(id),

    UNIQUE(project_id, user_id, functional_role)
);
```

**Key Insight**: Separates access control from approval authority.

---

### Table 2: gate_decisions

**Purpose**: Event log for gate approval decisions.

```sql
CREATE TABLE gate_decisions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    gate_id UUID NOT NULL REFERENCES gates(id) ON DELETE CASCADE,
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,

    -- Decision metadata
    action decision_action NOT NULL,
    actor_id UUID NOT NULL REFERENCES users(id),

    -- Chain tracking
    chain_id UUID NOT NULL,
    step_index INTEGER NOT NULL DEFAULT 0,
    required_roles TEXT[] NOT NULL,

    -- Status
    status decision_status DEFAULT 'PENDING',

    -- Evidence
    comments TEXT,
    evidence_ids UUID[],

    -- Audit
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    expires_at TIMESTAMP,  -- CTO v2.5 adjustment #2
    completed_at TIMESTAMP,

    UNIQUE(gate_id, chain_id, step_index)
);
```

**Key Insight**: Event log pattern (NOT state machine).

---

## Service Layer

### TierApprovalService (Sprint 161)

**Scope**: 3 methods only (backend foundation).

```python
class TierApprovalService:
    async def compute_required_roles(
        project_tier: str, gate_code: str
    ) -> List[str]:
        """Compute required roles based on tier + gate."""

    async def create_approval_request(
        gate_id: UUID, requester_id: UUID
    ) -> ApprovalChainMetadata:  # CTO v2.5 adjustment #3
        """Create approval request decision records."""

    async def record_decision(
        decision_id: UUID, actor_id: UUID, action: str
    ) -> GateDecision:
        """Record approval/rejection decision."""
        # NOTE: Does NOT finalize gate (defer to Sprint 164)
```

---

## Sprint 162-164 Roadmap

### Sprint 162: Authorization Service + OPA Policies

**Deliverables**:
- 10 OPA Rego policies (`tier_approval_authority.rego`)
- `TierAuthorizationService` with OPA integration
- Auto-assignment logic (find eligible approvers)
- Delegation support
- Auto-escalation background task

**Exit Criteria**:
- OPA policy evaluation <50ms (p95)
- 40+ integration tests
- Delegation functional

---

### Sprint 163: Frontend UI

**Deliverables**:
- Tier configuration page (select tier, assign functional roles)
- Approval inbox (list PENDING approvals)
- Approval decision modal (approve/reject/escalate)
- Delegation management UI
- Gate status indicator (approval chain progress)

**Exit Criteria**:
- 5 new pages/components
- 30+ frontend tests
- Responsive + accessible (WCAG 2.1 AA)

---

### Sprint 164: Integration & Testing

**Deliverables**:
- `GateFinalizationService` (update gate.status after all approvals)
- 20+ E2E tests (full approval flows)
- Load testing (100 concurrent approval requests)
- Documentation (4 user guides + API docs + runbook)

**Exit Criteria**:
- All 4 tiers tested E2E
- Performance: <100ms p95 authorization check
- CTO sign-off for production

---

## Consequences

### Positive

1. **Scalable Authorization**: Supports multi-project, multi-organization scenarios
2. **Clear Separation**: Access control ≠ Approval authority
3. **Auditable**: Event log provides full approval trail
4. **Flexible**: Easy to add new tiers or modify approval chains (OPA in Sprint 162)
5. **Scope Discipline**: Sprint 161 delivers foundation only, no over-engineering

### Negative

1. **4-Sprint Investment**: Requires Sprint 161-164 (~$60K budget)
2. **Migration Complexity**: Existing projects must be assigned tier
3. **User Education**: Teams need training on tier selection
4. **Performance Overhead**: Authorization check adds latency (target: <50ms)

### Risks

1. **Medium Risk: OPA Performance**
   - **Mitigation**: Cache policy evaluations (Redis, 5 min TTL)

2. **Low Risk: Council Review Complexity**
   - **Mitigation**: Event log simplifies multi-approver logic

3. **Low Risk: Frontend State Management**
   - **Mitigation**: TanStack Query for server state

---

## Implementation Status

**Sprint 161 (Backend Foundation)**: ✅ COMPLETE (Feb 6, 2026)
- Database schema: 2 tables, 4 ENUMs, 9 indexes
- SQLAlchemy models: ProjectFunctionRole, GateDecision
- Pydantic schemas: ApprovalChainMetadata + API schemas
- Service: TierApprovalService (3 methods, ~250 LOC)
- Tests: 54 unit tests (exceeds 40+ target), 95%+ coverage
- CTO v2.5 adjustments: All 3 applied

**Sprint 162 (OPA Policies)**: ⏳ PENDING (May 19-23, 2026)
**Sprint 163 (Frontend UI)**: ⏳ PENDING (May 26-30, 2026)
**Sprint 164 (Integration)**: ⏳ PENDING (Jun 2-6, 2026)

---

## References

- **Sprint 161 Plan**: `docs/04-build/02-Sprint-Plans/SPRINT-161-164-TIER-BASED-GATE-APPROVAL.md`
- **Enterprise Architect Review**: Sprint 161 v2 design feedback (Feb 6, 2026)
- **CTO Strategic Review**: Sprint 161 v2.5 approval (Score: 92/100)
- **Sprint 159 Staging Report**: `docs/09-govern/01-CTO-Reports/SPRINT-159-STAGING-TEST-RESULTS.md`

---

## Approval

**Approved By**: CTO (Acting)
**Date**: February 6, 2026
**Score**: 92/100 (Conditional Approval with 3 mandatory adjustments)
**Authority**: SDLC 6.0.5 Framework

**Next Review**: Sprint 162 kickoff (May 19, 2026)

---

**ADR Status**: ✅ **ACCEPTED** - Ready for Sprint 162 execution
