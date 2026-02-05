# ADR-048: SASE Artifacts - VCR/CRP Workflow Architecture

**Status**: APPROVED
**Date**: February 5, 2026
**Sprint**: 151 (SASE Artifacts Enhancement)
**Author**: CTO Office
**Reviewers**: Backend Lead, Frontend Lead

---

## Context

SDLC Orchestrator implements the SASE (Structured Agentic Software Engineering) methodology from the SDLC Enterprise Framework. SASE defines 6 artifact types for structured AI-human collaboration:

| Artifact | Purpose | Current Status |
|----------|---------|----------------|
| **BRS** | Briefing Script - Sprint start | Template only |
| **LPS** | Loop Script - Iteration start | Template only |
| **MTS** | Mentor Script - Complex task | Template only |
| **CRP** | Consultation Request Pack - Expert input | **Not integrated** |
| **MRP** | Merge-Readiness Pack - Before PR | Template only |
| **VCR** | Version Controlled Resolution - Post-merge | **Not integrated** |

Sprint 151 goal: Integrate VCR and CRP workflows into the platform, achieving 60% → 75% SASE completion.

### Problem Statement

1. **No structured post-merge documentation**: Significant changes lack formal problem/solution documentation
2. **No consultation workflow**: Developers have informal channels for expert input, no audit trail
3. **AI attribution missing**: AI-generated code lacks formal tracking of tools and percentage
4. **Evidence linkage gaps**: VCR/CRP artifacts not linked to Evidence Vault

---

## Decision

### VCR (Version Controlled Resolution) Workflow

VCR captures **post-merge documentation** for significant changes.

```
┌─────────────────────────────────────────────────────────────────────┐
│ VCR WORKFLOW                                                        │
└─────────────────────────────────────────────────────────────────────┘

   Developer           VCR System           CTO/CEO           Evidence Vault
       │                   │                   │                   │
       │  1. Create PR     │                   │                   │
       │──────────────────▶│                   │                   │
       │                   │                   │                   │
       │  2. PR passes gates (or override)     │                   │
       │──────────────────▶│                   │                   │
       │                   │                   │                   │
       │  3. Create VCR    │                   │                   │
       │──────────────────▶│                   │                   │
       │                   │                   │                   │
       │  4. Submit VCR    │                   │                   │
       │──────────────────▶│  5. Notify       │                   │
       │                   │─────────────────▶│                   │
       │                   │                   │                   │
       │                   │  6. Review        │                   │
       │                   │◀─────────────────│                   │
       │                   │                   │                   │
       │                   │  7. Approve       │                   │
       │                   │◀─────────────────│                   │
       │                   │                   │                   │
       │  8. PR Merged     │                   │                   │
       │◀──────────────────│                   │                   │
       │                   │                   │                   │
       │                   │  9. Store VCR     │                   │
       │                   │───────────────────────────────────────▶│
       │                   │                   │                   │
```

#### VCR Data Model

```yaml
VersionControlledResolution:
  # Identity
  id: UUID
  project_id: UUID (FK → projects)
  pr_number: Integer (nullable)
  pr_url: String (nullable)

  # Content
  title: String (255 chars)
  problem_statement: Text (required)
  root_cause_analysis: Text (optional)
  solution_approach: Text (required)
  implementation_notes: Text (optional)

  # Linkage
  evidence_ids: UUID[] (FK → evidence)
  adr_ids: UUID[] (FK → adrs)

  # AI Attribution
  ai_generated_percentage: Float (0.0 - 1.0)
  ai_tools_used: String[] (e.g., ["Cursor", "Copilot"])
  ai_generation_details: JSONB

  # Workflow
  status: Enum (draft, submitted, approved, rejected)
  created_by_id: UUID (FK → users)
  approved_by_id: UUID (FK → users, nullable)
  rejection_reason: Text (nullable)

  # Timestamps
  created_at: DateTime
  updated_at: DateTime
  submitted_at: DateTime (nullable)
  approved_at: DateTime (nullable)
```

### CRP (Consultation Request Pack) Workflow

CRP captures **structured consultation requests** for expert input.

```
┌─────────────────────────────────────────────────────────────────────┐
│ CRP WORKFLOW                                                        │
└─────────────────────────────────────────────────────────────────────┘

   Developer           CRP System          Consultant            ADR System
       │                   │                   │                   │
       │  1. Question arises                   │                   │
       │──────────────────▶│                   │                   │
       │                   │                   │                   │
       │  2. Create CRP    │                   │                   │
       │──────────────────▶│                   │                   │
       │                   │                   │                   │
       │  3. AI Assist (optional)              │                   │
       │◀──────────────────│                   │                   │
       │                   │                   │                   │
       │  4. Submit CRP    │                   │                   │
       │──────────────────▶│  5. Notify       │                   │
       │                   │─────────────────▶│                   │
       │                   │                   │                   │
       │                   │  6. Review        │                   │
       │                   │◀─────────────────│                   │
       │                   │                   │                   │
       │                   │  7. Respond       │                   │
       │                   │◀─────────────────│                   │
       │                   │                   │                   │
       │  8. Decision      │                   │                   │
       │◀──────────────────│                   │                   │
       │                   │                   │                   │
       │                   │  9. Create ADR (if architectural)     │
       │                   │───────────────────────────────────────▶│
       │                   │                   │                   │
```

#### CRP Data Model

```yaml
ConsultationRequestPack:
  # Identity
  id: UUID
  project_id: UUID (FK → projects)

  # Consultation Details
  title: String (255 chars)
  context: Text (required - situation description)
  question: Text (required - what decision needed)
  options_considered: JSONB (array of options)
  recommended_option: String (developer's preference)

  # Participants
  requested_by_id: UUID (FK → users)
  consultant_id: UUID (FK → users, nullable)

  # Response
  response: Text (nullable - consultant's answer)
  decision: Enum (approved, rejected, needs_revision, nullable)

  # Workflow
  status: Enum (draft, submitted, responded, closed)

  # Linkage
  adr_id: UUID (FK → adrs, nullable - if ADR created)
  evidence_ids: UUID[] (FK → evidence)

  # Timestamps
  created_at: DateTime
  updated_at: DateTime
  submitted_at: DateTime (nullable)
  responded_at: DateTime (nullable)
  closed_at: DateTime (nullable)
```

### API Design

#### VCR Endpoints

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| POST | `/api/v1/vcr` | Create VCR | Member |
| GET | `/api/v1/vcr/{id}` | Get VCR | Member |
| GET | `/api/v1/vcr` | List VCRs | Member |
| PUT | `/api/v1/vcr/{id}` | Update VCR | Owner |
| DELETE | `/api/v1/vcr/{id}` | Delete VCR | Owner |
| POST | `/api/v1/vcr/{id}/submit` | Submit for approval | Owner |
| POST | `/api/v1/vcr/{id}/approve` | Approve VCR | CTO/CEO |
| POST | `/api/v1/vcr/{id}/reject` | Reject VCR | CTO/CEO |
| POST | `/api/v1/vcr/auto-generate` | AI-assisted generation | Member |

#### CRP Endpoints

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| POST | `/api/v1/crp` | Create CRP | Member |
| GET | `/api/v1/crp/{id}` | Get CRP | Member |
| GET | `/api/v1/crp` | List CRPs | Member |
| PUT | `/api/v1/crp/{id}` | Update CRP | Owner |
| DELETE | `/api/v1/crp/{id}` | Delete CRP | Owner |
| POST | `/api/v1/crp/{id}/submit` | Submit to consultant | Owner |
| POST | `/api/v1/crp/{id}/respond` | Consultant responds | Consultant |
| POST | `/api/v1/crp/{id}/close` | Close CRP | Owner |
| POST | `/api/v1/crp/ai-assist` | AI-assisted options | Member |

### AI-Assisted Generation

Both VCR and CRP support AI-assisted generation:

#### VCR Auto-Generate

```python
async def auto_generate_vcr(pr_context: PRContext) -> VCRDraft:
    """
    Generate VCR draft from PR metadata.

    Input:
    - PR title, description
    - Commit messages
    - File changes summary
    - Linked evidence

    Output:
    - title: Concise VCR title
    - problem_statement: What was solved
    - root_cause_analysis: Why it happened (for bugs)
    - solution_approach: How it was solved
    - implementation_notes: Caveats and trade-offs
    """
```

#### CRP AI-Assist

```python
async def ai_assist_crp(context: str) -> CRPSuggestions:
    """
    AI-assisted CRP generation.

    Input:
    - User-provided context
    - Project ADRs
    - Past similar CRPs

    Output:
    - clarified_question: Refined question
    - options: List of considered options
    - recommended_option: AI recommendation
    - rationale: Why this option
    """
```

---

## Consequences

### Positive

1. **Structured documentation**: All significant changes have formal documentation
2. **Audit trail**: Complete history of decisions and consultations
3. **AI attribution**: Clear tracking of AI involvement
4. **Evidence linkage**: VCR/CRP linked to Evidence Vault
5. **Expert consultation**: Structured workflow for getting expert input

### Negative

1. **Process overhead**: Additional steps for developers
2. **Approval bottleneck**: CTO/CEO approval may slow merges
3. **AI quality**: Auto-generated content needs human review

### Mitigation

1. **AI-assisted generation**: Reduce manual documentation effort
2. **Async approval**: Notification system for fast response
3. **Template library**: Pre-built templates for common cases
4. **SLA enforcement**: 24h response time for consultations

---

## Alternatives Considered

### Option A: GitHub PR Templates Only

- Pros: No new system, familiar to developers
- Cons: No approval workflow, no AI attribution, no evidence linking
- Decision: **Rejected** - insufficient for governance needs

### Option B: External Tool (Notion, Confluence)

- Pros: Feature-rich, familiar
- Cons: No integration with Evidence Vault, no automated workflows
- Decision: **Rejected** - breaks single-source-of-truth principle

### Option C: Full SASE Integration (All 6 Artifacts)

- Pros: Complete SASE implementation
- Cons: Too much scope for one sprint
- Decision: **Deferred** - VCR/CRP first, others in future sprints

---

## Implementation Plan

### Sprint 151 Day-by-Day

| Day | Focus | Deliverables |
|-----|-------|--------------|
| 1 | VCR Backend | Model, Service, API (8 endpoints) |
| 2 | CRP Backend + VCR Frontend | CRP backend (8 endpoints) + VCR UI |
| 3 | CRP Frontend + Templates | CRP UI + 6 SASE templates |
| 4 | AI-Assisted Generation | Auto-generate VCR/CRP |
| 5 | Testing + Documentation | 70 tests + docs |

### File Structure

```
backend/app/
├── models/
│   ├── vcr.py           # VCR model
│   └── crp.py           # CRP model
├── schemas/
│   ├── vcr.py           # VCR Pydantic schemas
│   └── crp.py           # CRP Pydantic schemas
├── services/
│   ├── vcr_service.py   # VCR business logic
│   └── crp_service.py   # CRP business logic
├── api/routes/
│   ├── vcr.py           # VCR API endpoints
│   └── crp.py           # CRP API endpoints
└── templates/sase/
    ├── brs.yaml         # Briefing Script template
    ├── lps.yaml         # Loop Script template
    ├── mts.md           # Mentor Script template
    ├── crp.md           # CRP template
    ├── mrp.md           # MRP template
    └── vcr.md           # VCR template

frontend/src/
├── app/app/projects/[id]/
│   ├── vcrs/page.tsx    # VCR list page
│   └── crps/page.tsx    # CRP list page
├── components/
│   ├── vcr/
│   │   ├── VCRForm.tsx
│   │   ├── VCRCard.tsx
│   │   └── VCRList.tsx
│   └── crp/
│       ├── CRPForm.tsx
│       ├── CRPCard.tsx
│       └── CRPList.tsx
└── hooks/
    ├── useVCR.ts
    └── useCRP.ts
```

---

## Success Metrics

| Metric | Before | After | Target |
|--------|--------|-------|--------|
| SASE Completion | 60% | 75% | +15% |
| VCR Workflow | 0% | 100% | Operational |
| CRP Workflow | 0% | 100% | Operational |
| AI Attribution | No | Yes | Tracked |
| Evidence Linking | No | Yes | Linked |

---

## References

- [Sprint 151 Plan](../../04-build/02-Sprint-Plans/SPRINT-151-SASE-ARTIFACTS.md)
- [SDLC Enterprise Framework - SASE](../../SDLC-Enterprise-Framework/)
- [ADR-020: EP-04 VCR Workflow](ADR-020-EP-04-VCR-Workflow.md) (if exists)
- [Evidence Vault Specification](../14-Technical-Specs/SPEC-0001-Governance-System-Implementation.md)

---

**Approval**:
- [ ] Backend Lead
- [ ] Frontend Lead
- [ ] CTO
