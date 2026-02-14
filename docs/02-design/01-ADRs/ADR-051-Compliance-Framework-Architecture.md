# ADR-051: Compliance Framework Architecture

**Status**: PROPOSED
**Date**: February 5, 2026
**Sprint**: Sprint 156 (Phase 3: COMPLIANCE - NIST AI RMF GOVERN)
**Author**: CTO Office + AI Assistant
**Framework**: SDLC 6.0.5
**Related**: [ADR-048 SASE VCR/CRP](ADR-048-SASE-VCR-CRP-Architecture.md), [SPEC-0024 VCR/CRP Technical Specification](../14-Technical-Specs/SPEC-0024-VCR-CRP-Technical-Specification.md)

---

## Context

### Problem Statement

Enterprise customers deploying AI-powered software require compliance with multiple regulatory frameworks:

1. **NIST AI RMF**: US federal standard for AI risk management (GOVERN, MAP, MEASURE, MANAGE functions)
2. **EU AI Act (2024/1689)**: European regulation classifying AI systems by risk level
3. **ISO 42001:2023**: International standard for AI management systems (38 controls)

Currently, SDLC Orchestrator has **no compliance evaluation capability**:

- No framework-aware control tracking
- No automated OPA policy evaluation for compliance
- No risk register management
- No RACI accountability matrix
- No unified compliance dashboard

### Current State

| Capability | Status | Gap |
|------------|--------|-----|
| Gate Engine (OPA) | Implemented | Foundation ready |
| Evidence Vault | Implemented | Can store compliance evidence |
| SASE Artifacts (VCR/CRP/MRP) | Implemented (Sprint 151-153) | Linkage ready |
| NIST AI RMF GOVERN | Not implemented | Critical |
| NIST AI RMF MAP/MEASURE | Not implemented | High |
| EU AI Act Classification | Not implemented | High |
| ISO 42001 Controls | Not implemented | Medium |
| Unified Compliance Dashboard | Not implemented | Medium |

### Requirements

| ID | Requirement | Priority | Sprint | Source |
|----|-------------|----------|--------|--------|
| REQ-1 | Shared compliance framework registry (NIST, EU, ISO) | P0 | 156 | Roadmap |
| REQ-2 | Per-control assessment with OPA policy evaluation | P0 | 156 | Roadmap |
| REQ-3 | NIST AI RMF GOVERN function (5 policies) | P0 | 156 | NIST AI RMF 1.0 |
| REQ-4 | Risk register with 5x5 likelihood/impact matrix | P0 | 156 | NIST GOVERN |
| REQ-5 | RACI accountability matrix per control | P1 | 156 | Enterprise |
| REQ-6 | NIST MAP/MEASURE functions | P0 | 157 | NIST AI RMF 1.0 |
| REQ-7 | EU AI Act 4-level risk classification | P0 | 158 | EU AI Act |
| REQ-8 | EU AI Act conformity assessment | P0 | 158 | EU AI Act |
| REQ-9 | ISO 42001 38-control checklist | P0 | 159 | ISO 42001:2023 |
| REQ-10 | Unified compliance dashboard + gap analysis | P0 | 160 | Enterprise |

---

## Decision

### Architecture Overview

Implement a **shared compliance framework** with framework-specific extensions:

```
┌─────────────────────────────────────────────────────────────────────────┐
│                  COMPLIANCE FRAMEWORK ARCHITECTURE                       │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │                    FRONTEND LAYER                                │   │
│  │                                                                  │   │
│  │  /app/compliance/                                                │   │
│  │  ├── page.tsx            (Unified Dashboard - Sprint 160)        │   │
│  │  ├── nist/                                                       │   │
│  │  │   ├── govern/page.tsx (GOVERN Dashboard - Sprint 156)         │   │
│  │  │   ├── map/page.tsx    (MAP Dashboard - Sprint 157)            │   │
│  │  │   └── measure/page.tsx(MEASURE Dashboard - Sprint 157)        │   │
│  │  ├── eu-ai-act/                                                  │   │
│  │  │   ├── classify/page.tsx (Classification - Sprint 158)         │   │
│  │  │   └── conformity/page.tsx (Assessment - Sprint 158)           │   │
│  │  └── iso-42001/                                                  │   │
│  │      └── checklist/page.tsx (38 Controls - Sprint 159)           │   │
│  └─────────────────────────────────┬───────────────────────────────┘   │
│                                    │                                    │
│                                    ▼                                    │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │                     API LAYER                                    │   │
│  │                                                                  │   │
│  │  /api/v1/compliance/                                             │   │
│  │  ├── frameworks           (GET - List frameworks)                │   │
│  │  ├── frameworks/{code}    (GET - Framework details)              │   │
│  │  ├── projects/{pid}/assessments  (GET/POST)                      │   │
│  │  ├── projects/{pid}/dashboard    (GET - Sprint 160)              │   │
│  │  │                                                               │   │
│  │  ├── nist/govern/evaluate (POST - OPA evaluation)                │   │
│  │  ├── nist/govern/dashboard(GET - GOVERN metrics)                 │   │
│  │  ├── nist/risks           (GET/POST - Risk register)             │   │
│  │  ├── nist/raci            (GET/POST - RACI matrix)              │   │
│  │  │                                                               │   │
│  │  ├── eu-ai-act/classify   (POST - Sprint 158)                    │   │
│  │  └── iso-42001/controls   (GET - Sprint 159)                     │   │
│  └─────────────────────────────────┬───────────────────────────────┘   │
│                                    │                                    │
│                                    ▼                                    │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │                   SERVICE LAYER                                  │   │
│  │                                                                  │   │
│  │  ComplianceService (shared base)                                 │   │
│  │  ├── evaluate_controls()   - OPA policy evaluation               │   │
│  │  ├── get_dashboard()       - Aggregated metrics                  │   │
│  │  └── export_compliance()   - Report export                       │   │
│  │                                                                  │   │
│  │  NISTGovernService (Sprint 156)                                  │   │
│  │  ├── evaluate_govern()     - 5 GOVERN policies                   │   │
│  │  ├── manage_risks()        - Risk register CRUD                  │   │
│  │  └── manage_raci()         - RACI matrix CRUD                    │   │
│  │                                                                  │   │
│  │  NISTMapMeasureService  (Sprint 157)                             │   │
│  │  EUAIActService         (Sprint 158)                             │   │
│  │  ISO42001Service        (Sprint 159)                             │   │
│  └─────────────────────────────────┬───────────────────────────────┘   │
│                                    │                                    │
│                                    ▼                                    │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │                    OPA POLICY LAYER                               │   │
│  │                                                                  │   │
│  │  policy-packs/rego/compliance/                                   │   │
│  │  ├── nist/govern/                                                │   │
│  │  │   ├── accountability_structure.rego   (GOVERN-1)              │   │
│  │  │   ├── risk_culture.rego               (GOVERN-2)              │   │
│  │  │   ├── legal_compliance.rego           (GOVERN-3)              │   │
│  │  │   ├── third_party_oversight.rego      (GOVERN-4)              │   │
│  │  │   └── continuous_improvement.rego     (GOVERN-5)              │   │
│  │  ├── nist/map/         (Sprint 157)                              │   │
│  │  ├── nist/measure/     (Sprint 157)                              │   │
│  │  ├── eu-ai-act/        (Sprint 158)                              │   │
│  │  └── iso-42001/        (Sprint 159)                              │   │
│  └─────────────────────────────────┬───────────────────────────────┘   │
│                                    │                                    │
│                                    ▼                                    │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │                   DATABASE LAYER (5 Shared Tables)               │   │
│  │                                                                  │   │
│  │  compliance_frameworks     → Framework registry                  │   │
│  │  compliance_controls       → Per-framework controls              │   │
│  │  compliance_assessments    → Per-project evaluations             │   │
│  │  compliance_risk_register  → Risk entries (NIST GOVERN/MAP)      │   │
│  │  compliance_raci           → Accountability matrix               │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### Database Schema

#### Table: `compliance_frameworks`

Registry of supported compliance frameworks. Seeded with NIST, EU AI Act, ISO 42001.

```sql
CREATE TABLE compliance_frameworks (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    code            VARCHAR(50) NOT NULL UNIQUE,  -- "NIST_AI_RMF", "EU_AI_ACT", "ISO_42001"
    name            VARCHAR(200) NOT NULL,
    version         VARCHAR(20) NOT NULL,          -- "1.0", "2024/1689", "2023"
    description     TEXT,
    total_controls  INTEGER NOT NULL DEFAULT 0,
    is_active       BOOLEAN NOT NULL DEFAULT true,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);
```

#### Table: `compliance_controls`

Individual controls per framework. NIST GOVERN has 5 controls, EU AI Act ~15, ISO 42001 has 38.

```sql
CREATE TABLE compliance_controls (
    id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    framework_id      UUID NOT NULL REFERENCES compliance_frameworks(id) ON DELETE CASCADE,
    control_code      VARCHAR(50) NOT NULL,        -- "GOVERN-1.1", "Art.6", "5.1"
    category          VARCHAR(100) NOT NULL,        -- "GOVERN", "HIGH_RISK", "Leadership"
    title             VARCHAR(300) NOT NULL,
    description       TEXT,
    severity          VARCHAR(20) NOT NULL DEFAULT 'medium',  -- critical, high, medium, low
    gate_mapping      VARCHAR(20),                  -- "G1", "G2" (links to existing gates)
    evidence_required JSONB NOT NULL DEFAULT '[]',  -- structured evidence schema
    opa_policy_code   VARCHAR(100),                 -- links to Rego policy file
    sort_order        INTEGER NOT NULL DEFAULT 0,
    created_at        TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at        TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE(framework_id, control_code)
);
```

**JSONB Schema for `evidence_required`**:

```json
[
  {
    "type": "document",
    "description": "AI system ownership documentation",
    "required": true,
    "accepted_formats": ["pdf", "md", "docx"]
  },
  {
    "type": "attestation",
    "description": "Team lead sign-off on AI risk awareness",
    "required": true,
    "accepted_formats": ["pdf", "signed_form"]
  },
  {
    "type": "report",
    "description": "Quarterly AI risk assessment report",
    "required": false,
    "accepted_formats": ["pdf", "csv", "json"]
  }
]
```

Each evidence entry has:
- `type`: enum of `document | attestation | report | screenshot | test_result | audit_log`
- `description`: Human-readable description of required evidence
- `required`: Whether this evidence is mandatory for compliance
- `accepted_formats`: List of accepted file formats

#### Table: `compliance_assessments`

Per-project, per-control evaluation records.

```sql
CREATE TABLE compliance_assessments (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id      UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    control_id      UUID NOT NULL REFERENCES compliance_controls(id) ON DELETE CASCADE,
    status          VARCHAR(30) NOT NULL DEFAULT 'not_started',
                    -- not_started, in_progress, compliant, non_compliant, not_applicable
    evidence_ids    UUID[],            -- links to Evidence Vault
    assessor_id     UUID REFERENCES users(id) ON DELETE SET NULL,
    notes           TEXT,
    auto_evaluated  BOOLEAN NOT NULL DEFAULT false,  -- true if OPA evaluated
    opa_result      JSONB,             -- raw OPA evaluation result
    assessed_at     TIMESTAMPTZ,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE(project_id, control_id)
);

CREATE INDEX idx_assessments_project ON compliance_assessments(project_id);
CREATE INDEX idx_assessments_status ON compliance_assessments(status);
```

#### Table: `compliance_risk_register`

Risk entries for NIST GOVERN/MAP risk management.

```sql
CREATE TABLE compliance_risk_register (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id          UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    framework_id        UUID NOT NULL REFERENCES compliance_frameworks(id) ON DELETE CASCADE,
    risk_code           VARCHAR(50) NOT NULL,
    title               VARCHAR(300) NOT NULL,
    description         TEXT,
    likelihood          VARCHAR(20) NOT NULL DEFAULT 'possible',
                        -- rare(1), unlikely(2), possible(3), likely(4), almost_certain(5)
    impact              VARCHAR(20) NOT NULL DEFAULT 'moderate',
                        -- negligible(1), minor(2), moderate(3), major(4), catastrophic(5)
    risk_score          INTEGER NOT NULL DEFAULT 9,  -- likelihood_val * impact_val (1-25)
    category            VARCHAR(100) NOT NULL,        -- safety, fairness, privacy, security
    mitigation_strategy TEXT,
    responsible_id      UUID REFERENCES users(id) ON DELETE SET NULL,
    status              VARCHAR(20) NOT NULL DEFAULT 'identified',
                        -- identified, mitigating, mitigated, accepted, closed
    target_date         DATE,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_risk_project ON compliance_risk_register(project_id);
CREATE INDEX idx_risk_score ON compliance_risk_register(risk_score DESC);
```

#### Table: `compliance_raci`

RACI (Responsible, Accountable, Consulted, Informed) matrix per control.

```sql
CREATE TABLE compliance_raci (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id      UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    control_id      UUID NOT NULL REFERENCES compliance_controls(id) ON DELETE CASCADE,
    responsible_id  UUID REFERENCES users(id) ON DELETE SET NULL,   -- R
    accountable_id  UUID REFERENCES users(id) ON DELETE SET NULL,   -- A
    consulted_ids   UUID[],                                         -- C
    informed_ids    UUID[],                                         -- I
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE(project_id, control_id)
);
```

### OPA Policy Design

All compliance OPA policies follow a shared input/output contract.

#### Input Contract (Shared)

```json
{
  "project_id": "uuid-string",
  "project_name": "string",
  "ai_systems": [
    {
      "name": "string",
      "owner": "string|null",
      "type": "generation|classification|recommendation|other"
    }
  ],
  "team_training": {
    "total_members": 10,
    "trained_members": 8,
    "completion_pct": 80.0
  },
  "legal_review": {
    "approved": true,
    "reviewer": "string",
    "date": "2026-04-01"
  },
  "third_party_apis": [
    {
      "name": "OpenAI",
      "sla_documented": true,
      "privacy_agreement": true
    }
  ],
  "incident_postmortems": [
    {
      "incident_date": "2026-03-15",
      "postmortem_date": "2026-03-16",
      "process_updated": true
    }
  ]
}
```

#### Output Contract (Each Policy Returns)

```json
{
  "allowed": true,
  "reason": "All AI systems have designated owners",
  "severity": "critical",
  "details": {
    "total_systems": 3,
    "systems_with_owner": 3,
    "unowned_systems": []
  }
}
```

#### GOVERN Policy Mapping

| Policy | Control Code | Description | Severity |
|--------|-------------|-------------|----------|
| `accountability_structure.rego` | GOVERN-1.1 | All AI systems must have designated owners | critical |
| `risk_culture.rego` | GOVERN-1.2 | Team AI risk training completion >= 80% | high |
| `legal_compliance.rego` | GOVERN-1.3 | Legal review approved for AI usage | critical |
| `third_party_oversight.rego` | GOVERN-1.4 | Third-party AI APIs have SLA + privacy agreements | high |
| `continuous_improvement.rego` | GOVERN-1.5 | Incident postmortems completed within 48h with process updates | medium |

### Key Design Decisions

**Decision 1: Shared Tables (NOT per-framework tables)**

All 3 frameworks share `compliance_controls` and `compliance_assessments`. Framework-specific data is stored in JSONB fields where needed. This avoids table sprawl (3 separate schemas) while preserving flexibility.

**Decision 2: Controls Map to Existing Gates**

The `gate_mapping` column in `compliance_controls` links compliance controls to existing gate model (G0-G10). This reuses the gate engine infrastructure rather than duplicating policy evaluation.

**Decision 3: Evidence Reuses Evidence Vault**

`compliance_assessments.evidence_ids` links to the existing Evidence Vault via UUID array, identical to the VCR model pattern. No new evidence storage needed.

**Decision 4: OPA Policies in Namespace**

Compliance Rego policies live under `policy-packs/rego/compliance/{framework}/` separate from existing gate policies under `policy-packs/rego/gates/`. This isolates compliance evaluation from gate evaluation while sharing the OPA service.

**Decision 5: Unified API Under `/compliance/`**

All compliance routes live under `/api/v1/compliance/` with framework-specific sub-routes (`/nist/`, `/eu-ai-act/`, `/iso-42001/`). This provides a clean namespace and enables a unified dashboard in Sprint 160.

**Decision 6: Risk Score Formula**

Risk score = `likelihood_value(1-5) * impact_value(1-5)`, producing a range of 1-25. Risk levels:

| Score | Level | Color | Action |
|-------|-------|-------|--------|
| 1-4 | Low | Green | Accept/Monitor |
| 5-9 | Medium | Yellow | Mitigate within 30 days |
| 10-15 | High | Orange | Mitigate within 14 days |
| 16-25 | Critical | Red | Immediate action required |

---

## Alternatives Considered

### Alternative 1: Per-Framework Database Schema

**Approach**: Create separate tables for each framework (`nist_controls`, `eu_ai_act_controls`, `iso_42001_controls`).

**Pros**:
- Framework-specific fields without JSONB
- Simpler per-framework queries

**Cons**:
- Table sprawl (15+ tables instead of 5)
- Duplicate assessment/risk patterns
- No unified dashboard without complex UNION queries
- Each new framework requires new migration

**Decision**: Rejected - shared schema with JSONB for framework-specific fields scales better

### Alternative 2: External Compliance Tool Integration

**Approach**: Integrate with existing compliance tools (Vanta, Drata, OneTrust).

**Pros**:
- Mature compliance platforms
- Pre-built framework support

**Cons**:
- No OPA policy integration (core value proposition)
- No Evidence Vault linkage
- External dependency and cost ($10K+/year)
- No customization for SDLC-specific controls

**Decision**: Rejected - native integration with OPA and Evidence Vault is our differentiator

### Alternative 3: Compliance-as-Code Only (No UI)

**Approach**: CLI-only compliance evaluation via OPA policies and YAML configuration.

**Pros**:
- Faster implementation
- Developer-friendly (GitOps)
- Lower frontend investment

**Cons**:
- Not accessible to non-developers (PMs, CTO, auditors)
- No dashboard for executive visibility
- No risk management UI

**Decision**: Rejected - enterprise customers require visual dashboards and reports

---

## Consequences

### Positive

1. **Enterprise compliance ready**: NIST + EU AI Act + ISO 42001 coverage
2. **Automated evaluation**: OPA policies provide continuous compliance checking
3. **Evidence-based**: Links to existing Evidence Vault for audit trail
4. **Unified view**: Single dashboard across all 3 frameworks (Sprint 160)
5. **Extensible**: New frameworks can be added via `compliance_frameworks` registry without schema changes
6. **Gate integration**: Compliance controls map to existing quality gates

### Negative

1. **Complexity**: 5 new tables and 3 framework-specific service layers
2. **OPA policy maintenance**: 11+ Rego policies require ongoing updates as standards evolve
3. **Seed data management**: Framework controls must be seeded and versioned

### Risks & Mitigations

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| NIST AI RMF updates | Medium | Medium | Version controls in `compliance_frameworks.version` |
| EU AI Act implementation guidelines change | Medium | High | JSONB fields for flexible data storage |
| OPA performance with many policies | Low | Medium | Policy namespacing + caching |
| Compliance expert availability | Medium | High | AI-assisted control evaluation + auto-generate assessments |
| Large seed data migrations | Low | Low | Separate seed data script from schema migration |

---

## Implementation Plan

### Sprint 156 (NIST AI RMF GOVERN) - Detailed

| Day | Focus | Deliverables | Tests |
|-----|-------|--------------|-------|
| Day 1 (Mon) | Database + Models + Schemas | Alembic migration (5 tables), SQLAlchemy models, Pydantic schemas | 15 |
| Day 2 (Tue) | OPA Policies | 5 GOVERN Rego policies + tests | 15 |
| Day 3 (Wed) | Backend Services | ComplianceService + NISTGovernService | 20 |
| Day 4 (Thu) | API Routes + Frontend | 10 endpoints, useCompliance hook, GOVERN dashboard | 25 |
| Day 5 (Fri) | Frontend Tests + Polish | Component tests, integration fixes, sprint report | 10 |
| **Total** | | **~2,200 LOC** | **85** |

### Sprint 157-160 (High-Level)

| Sprint | Focus | LOC | Tests |
|--------|-------|-----|-------|
| 157 | NIST MAP + MEASURE | ~2,000 | 130 |
| 158 | EU AI Act | ~2,000 | 125 |
| 159 | ISO 42001 | ~2,000 | 135 |
| 160 | Unified Dashboard + Gap Analysis | ~2,000 | 125 |
| **Total Phase 3** | | **~10,200** | **600** |

### File Structure

```
backend/
├── alembic/versions/
│   └── s156_001_compliance_framework.py       # Migration: 5 tables
├── app/
│   ├── models/
│   │   └── compliance.py                      # 5 SQLAlchemy models
│   ├── schemas/
│   │   └── compliance.py                      # Pydantic request/response
│   ├── api/routes/
│   │   ├── compliance_framework.py            # Shared framework routes (3)
│   │   └── nist_govern.py                     # NIST GOVERN routes (7)
│   └── services/
│       ├── compliance_service.py              # Shared base service
│       └── nist_govern_service.py             # NIST GOVERN business logic
├── policy-packs/rego/compliance/nist/govern/
│   ├── accountability_structure.rego
│   ├── risk_culture.rego
│   ├── legal_compliance.rego
│   ├── third_party_oversight.rego
│   └── continuous_improvement.rego
└── tests/
    ├── unit/services/
    │   ├── test_compliance_service.py         # 15 tests
    │   └── test_nist_govern_service.py        # 20 tests
    ├── unit/api/
    │   ├── test_compliance_framework_routes.py # 10 tests
    │   └── test_nist_govern_routes.py         # 15 tests
    └── integration/
        ├── test_nist_govern_e2e.py            # 10 tests
        └── test_nist_rego_policies.py         # 15 tests

frontend/src/
├── app/app/compliance/
│   ├── layout.tsx                             # Compliance sub-nav layout
│   └── nist/
│       ├── page.tsx                           # NIST overview
│       └── govern/page.tsx                    # GOVERN dashboard (~500 LOC)
├── hooks/
│   └── useCompliance.ts                       # TanStack Query hooks
└── __tests__/app/compliance/
    └── NistGovernPage.test.tsx                # 15 frontend tests
```

### API Endpoints (Sprint 156)

**Shared Framework (3 endpoints)**:

| Method | Path | Description |
|--------|------|-------------|
| GET | `/compliance/frameworks` | List all active frameworks |
| GET | `/compliance/frameworks/{code}` | Framework details + control count |
| GET | `/compliance/projects/{pid}/assessments` | List assessments for project |

**NIST GOVERN (7 endpoints)**:

| Method | Path | Description |
|--------|------|-------------|
| POST | `/compliance/nist/govern/evaluate` | Evaluate 5 GOVERN policies via OPA |
| GET | `/compliance/nist/govern/dashboard` | Aggregated GOVERN metrics |
| GET | `/compliance/nist/risks` | List risk register entries |
| POST | `/compliance/nist/risks` | Create risk entry |
| PUT | `/compliance/nist/risks/{id}` | Update risk status/mitigation |
| GET | `/compliance/nist/raci` | Get RACI matrix for project |
| POST | `/compliance/nist/raci` | Create/update RACI entry |

---

## References

- [NIST AI Risk Management Framework 1.0](https://www.nist.gov/artificial-intelligence/ai-risk-management-framework)
- [EU AI Act (Regulation 2024/1689)](https://eur-lex.europa.eu/eli/reg/2024/1689)
- [ISO/IEC 42001:2023 AI Management Systems](https://www.iso.org/standard/81230.html)
- [ADR-048: SASE VCR/CRP Architecture](ADR-048-SASE-VCR-CRP-Architecture.md)
- [Sprint 156-160 Roadmap](../../04-build/02-Sprint-Plans/ROADMAP-147-170.md)
- [Phase 3 Design Plan](/home/dttai/.claude/plans/parallel-painting-turing.md)

---

## Approval

| Role | Name | Date | Decision |
|------|------|------|----------|
| CTO | - | Feb 5, 2026 | CONDITIONAL APPROVAL |
| Backend Lead | - | Feb 5, 2026 | Pending |
| Frontend Lead | - | Feb 5, 2026 | Pending |

**CTO Conditions**:
1. JSONB schema for `evidence_required` must be explicitly defined (see above)
2. Sprint 157-160 day-by-day plans to be detailed before each sprint
3. Compliance expert consultation planned for Sprint 158 (EU AI Act)
4. Framework 6.0.5 update planned for Sprint 160

---

**Document Status**: PROPOSED
**Implementation Status**: Sprint 156 Starting
