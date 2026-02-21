# ADR-051: Compliance Framework Architecture

**Status**: APPROVED  
**Date**: February 5, 2026  
**Author**: CTO, SDLC Orchestrator Team  
**Reviewers**: Technical Lead, Backend Lead, Frontend Lead  
**Sprint**: 156-160 (Phase 3: COMPLIANCE)

---

## Context

Enterprise customers require compliance with three major AI governance frameworks:

1. **NIST AI Risk Management Framework (AI RMF)** - US federal standard
2. **EU AI Act (Regulation 2024/1689)** - European legal requirement
3. **ISO/IEC 42001:2023** - International standard for AI management systems

Current SDLC Orchestrator has Gate-based quality controls but lacks explicit compliance mapping. Enterprise deals blocked due to missing compliance certification pathways.

**Market Drivers**:
- 73% of Fortune 500 require NIST AI RMF compliance (Gartner 2025)
- EU AI Act mandatory for EU market access (June 2026 deadline)
- ISO 42001 certification expected by procurement teams

**Technical Challenge**: Implement 3 compliance frameworks without duplicating Gate/Evidence/Policy infrastructure.

---

## Decision

Implement a **Shared Compliance Framework** with framework-specific extensions, integrated with existing Gate model and Evidence Vault.

### Core Architecture Principles

1. **Shared Foundation**: Single set of tables for all frameworks
2. **OPA Policy-as-Code**: All compliance rules in Rego (no hardcoded logic)
3. **Reuse Existing Primitives**: Link to Gate model + Evidence Vault (no duplication)
4. **Framework Extensions**: JSONB fields for framework-specific metadata
5. **Incremental Delivery**: 5 sprints from foundation → integration

---

## Database Schema

### 1. `compliance_frameworks` - Framework Registry

```sql
CREATE TABLE compliance_frameworks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    code VARCHAR(50) UNIQUE NOT NULL,  -- "NIST_AI_RMF", "EU_AI_ACT", "ISO_42001"
    name VARCHAR(200) NOT NULL,
    version VARCHAR(20) NOT NULL,      -- "1.0", "2024/1689", "2023"
    description TEXT,
    total_controls INT NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_frameworks_code ON compliance_frameworks(code);
CREATE INDEX idx_frameworks_active ON compliance_frameworks(is_active);
```

**Rationale**: Central registry allows dynamic framework addition without schema changes.

### 2. `compliance_controls` - Individual Controls per Framework

```sql
CREATE TYPE control_severity AS ENUM('critical', 'high', 'medium', 'low');

CREATE TABLE compliance_controls (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    framework_id UUID NOT NULL REFERENCES compliance_frameworks(id) ON DELETE CASCADE,
    control_code VARCHAR(50) NOT NULL,  -- "GOVERN-1.1", "Art.6", "5.1"
    category VARCHAR(100) NOT NULL,     -- "GOVERN", "HIGH_RISK", "Leadership"
    title VARCHAR(300) NOT NULL,
    description TEXT,
    severity control_severity NOT NULL,
    gate_mapping VARCHAR(20),           -- "G1", "G2", etc. (links to gates table)
    evidence_required JSONB,            -- Structured schema (see below)
    opa_policy_code VARCHAR(100),       -- "sdlc.compliance.nist.govern.accountability"
    sort_order INT,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(framework_id, control_code)
);

CREATE INDEX idx_controls_framework ON compliance_controls(framework_id);
CREATE INDEX idx_controls_gate ON compliance_controls(gate_mapping);
CREATE INDEX idx_controls_severity ON compliance_controls(severity);
```

**JSONB Schema for `evidence_required`**:
```typescript
evidence_required: [
  {
    type: "legal_clearance" | "risk_assessment" | "security_audit" | "training_record",
    description: string,
    mandatory: boolean,
    gate_id?: string  // Optional: specific gate requirement
  }
]
```

**Rationale**: 
- `gate_mapping` links compliance controls to existing gates (reuse validation logic)
- `opa_policy_code` enables automated evaluation
- JSONB `evidence_required` flexible for framework-specific evidence types

### 3. `compliance_assessments` - Per-Project Control Evaluations

```sql
CREATE TYPE assessment_status AS ENUM(
    'not_started', 
    'in_progress', 
    'compliant', 
    'non_compliant', 
    'not_applicable'
);

CREATE TABLE compliance_assessments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    control_id UUID NOT NULL REFERENCES compliance_controls(id) ON DELETE CASCADE,
    status assessment_status DEFAULT 'not_started',
    evidence_ids UUID[],                -- Links to evidence_vault.id
    assessor_id UUID REFERENCES users(id),
    notes TEXT,
    auto_evaluated BOOLEAN DEFAULT FALSE,
    opa_result JSONB,                   -- Raw OPA evaluation output
    assessed_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(project_id, control_id)
);

CREATE INDEX idx_assessments_project ON compliance_assessments(project_id);
CREATE INDEX idx_assessments_control ON compliance_assessments(control_id);
CREATE INDEX idx_assessments_status ON compliance_assessments(status);
CREATE INDEX idx_assessments_auto ON compliance_assessments(auto_evaluated);
```

**Rationale**:
- `evidence_ids` array reuses existing Evidence Vault (no duplication)
- `auto_evaluated` flag distinguishes OPA-evaluated vs manual assessments
- `opa_result` JSONB stores full OPA output for audit trail

### 4. `compliance_risk_register` - NIST GOVERN/MAP Risk Entries

```sql
CREATE TYPE risk_likelihood AS ENUM('rare', 'unlikely', 'possible', 'likely', 'almost_certain');
CREATE TYPE risk_impact AS ENUM('negligible', 'minor', 'moderate', 'major', 'catastrophic');
CREATE TYPE risk_status AS ENUM('identified', 'mitigating', 'mitigated', 'accepted', 'closed');

CREATE TABLE compliance_risk_register (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    framework_id UUID NOT NULL REFERENCES compliance_frameworks(id),
    risk_code VARCHAR(50),
    title VARCHAR(300) NOT NULL,
    description TEXT,
    likelihood risk_likelihood NOT NULL,
    impact risk_impact NOT NULL,
    risk_score INT NOT NULL,            -- likelihood_value × impact_value (1-25)
    category VARCHAR(100),              -- "safety", "fairness", "privacy", "security"
    mitigation_strategy TEXT,
    responsible_id UUID REFERENCES users(id),
    status risk_status DEFAULT 'identified',
    target_date DATE,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_risks_project ON compliance_risk_register(project_id);
CREATE INDEX idx_risks_score ON compliance_risk_register(risk_score DESC);
CREATE INDEX idx_risks_status ON compliance_risk_register(status);
```

**Risk Score Formula**:
```
Likelihood: rare(1) → almost_certain(5)
Impact: negligible(1) → catastrophic(5)
Risk Score = Likelihood × Impact (1-25)
```

**Rationale**: NIST AI RMF requires quantitative risk assessment. Risk register separate from assessments to track ongoing risks vs point-in-time control compliance.

### 5. `compliance_raci` - Accountability Matrix

```sql
CREATE TABLE compliance_raci (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    control_id UUID NOT NULL REFERENCES compliance_controls(id) ON DELETE CASCADE,
    responsible_id UUID REFERENCES users(id),  -- R: Does the work
    accountable_id UUID REFERENCES users(id),  -- A: Ultimately answerable
    consulted_ids UUID[],                      -- C: Provides input
    informed_ids UUID[],                       -- I: Kept updated
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(project_id, control_id)
);

CREATE INDEX idx_raci_project ON compliance_raci(project_id);
CREATE INDEX idx_raci_control ON compliance_raci(control_id);
```

**Rationale**: NIST GOVERN-1.1 requires clear accountability structure. RACI matrix standard best practice.

---

## OPA Policy Organization

```
backend/policy-packs/rego/
├── compliance/                    # NEW namespace
│   ├── shared/
│   │   └── helpers.rego          # Shared compliance utilities
│   ├── nist/
│   │   ├── govern/
│   │   │   ├── accountability_structure.rego    # GOVERN-1.1
│   │   │   ├── risk_culture.rego               # GOVERN-1.2
│   │   │   ├── legal_compliance.rego           # GOVERN-1.3
│   │   │   ├── third_party_oversight.rego      # GOVERN-1.4
│   │   │   └── continuous_improvement.rego     # GOVERN-1.5
│   │   ├── map/
│   │   │   ├── context_identification.rego     # MAP-1.1
│   │   │   ├── dependency_mapping.rego         # MAP-1.2
│   │   │   └── risk_categorization.rego        # MAP-1.3
│   │   └── measure/
│   │       ├── performance_metrics.rego        # MEASURE-2.1
│   │       └── bias_detection.rego             # MEASURE-2.2
│   ├── eu-ai-act/
│   │   ├── risk_classification.rego            # Art.6 classification
│   │   ├── conformity_assessment.rego          # Art.43 assessment
│   │   └── transparency_obligations.rego       # Art.13 transparency
│   └── iso-42001/
│       ├── leadership_commitment.rego          # Clause 5.1
│       ├── risk_assessment.rego                # Clause 6.1
│       └── operational_controls.rego           # Clause 8
```

### Policy Contract (Standard Input/Output)

**Input**:
```json
{
  "project_id": "uuid",
  "project_data": { /* project context */ },
  "control_code": "GOVERN-1.1",
  "evidence": [ /* evidence objects */ ]
}
```

**Output**:
```json
{
  "allowed": true,
  "reason": "All accountability requirements met",
  "severity": "critical",
  "details": {
    "checks_passed": 5,
    "checks_failed": 0,
    "recommendations": []
  }
}
```

**Rationale**: Consistent contract enables unified compliance dashboard.

---

## API Architecture

### Route Namespace

```
/api/v1/compliance/                          # Shared routes
├── frameworks                               # GET - List all frameworks
├── frameworks/{code}                        # GET - Framework details
├── projects/{pid}/assessments               # GET/POST - List/create assessments
├── projects/{pid}/assessments/{id}          # GET/PUT - Assessment CRUD
├── projects/{pid}/dashboard                 # GET - Unified dashboard
├── projects/{pid}/gap-analysis              # GET - Cross-framework gaps
├── projects/{pid}/export                    # GET - Export compliance data
│
├── nist/                                    # NIST-specific
│   ├── govern/evaluate                      # POST - Evaluate GOVERN policies
│   ├── govern/dashboard                     # GET - GOVERN metrics
│   ├── risks                                # GET/POST - Risk register
│   ├── risks/{id}                           # PUT - Update risk
│   └── raci                                 # GET/POST - RACI matrix
│
├── eu-ai-act/                               # EU-specific
│   ├── classify                             # POST - Classify AI system
│   ├── conformity                           # GET/POST - Conformity assessment
│   └── transparency                         # GET/POST - Transparency docs
│
└── iso-42001/                               # ISO-specific
    ├── controls                             # GET - 38 controls checklist
    ├── controls/{id}/assess                 # POST - Assess control
    └── audit-export                         # GET - Export audit trail
```

**Design Principles**:
1. Shared routes at `/compliance/` root (framework-agnostic)
2. Framework-specific routes under `/compliance/{framework}/`
3. All routes use existing auth middleware (JWT)
4. Rate limiting: 100 req/min per user (existing policy)

---

## Frontend Architecture

### Page Hierarchy

```
frontend/src/app/app/compliance/
├── page.tsx                      # Unified dashboard (Sprint 160)
├── layout.tsx                    # Sub-navigation tabs
├── nist/
│   ├── page.tsx                 # NIST overview (4 functions)
│   ├── govern/page.tsx          # GOVERN dashboard
│   ├── map/page.tsx             # MAP dashboard
│   └── measure/page.tsx         # MEASURE dashboard
├── eu-ai-act/
│   ├── page.tsx                 # EU AI Act dashboard
│   ├── classify/page.tsx        # Classification wizard
│   └── conformity/page.tsx      # Conformity assessment form
└── iso-42001/
    ├── page.tsx                 # ISO 42001 dashboard
    └── checklist/page.tsx       # 38-control checklist
```

### State Management

**TanStack Query Hooks** (`frontend/src/hooks/useCompliance.ts`):
```typescript
export const useCompliance = () => {
  // Shared framework queries
  const useFrameworks = () => useQuery(['compliance', 'frameworks'], ...)
  const useAssessments = (projectId) => useQuery(['compliance', 'assessments', projectId], ...)
  
  // NIST GOVERN queries
  const useGovernEvaluate = () => useMutation(['nist', 'govern', 'evaluate'], ...)
  const useRiskRegister = (projectId) => useQuery(['nist', 'risks', projectId], ...)
  
  // Mutations
  const useCreateAssessment = () => useMutation(['compliance', 'assessments'], ...)
  const useCreateRisk = () => useMutation(['nist', 'risks'], ...)
}
```

**Rationale**: TanStack Query provides automatic caching, background refetch, optimistic updates.

---

## Service Layer Pattern

### Base Service: `compliance_service.py`

```python
class ComplianceService:
    """Shared compliance service with framework-agnostic logic."""
    
    def __init__(self, db: AsyncSession, opa_service: OPAService):
        self.db = db
        self.opa = opa_service
    
    async def get_frameworks(self) -> List[ComplianceFramework]:
        """List all active frameworks."""
        
    async def get_assessments(self, project_id: UUID) -> List[Assessment]:
        """List assessments for project."""
        
    async def evaluate_control(
        self, 
        project_id: UUID, 
        control_id: UUID,
        evidence_ids: List[UUID]
    ) -> Assessment:
        """Evaluate single control via OPA."""
        # 1. Fetch control + OPA policy code
        # 2. Gather evidence from Evidence Vault
        # 3. Call OPA service
        # 4. Create/update assessment record
        
    async def get_gap_analysis(self, project_id: UUID) -> GapAnalysis:
        """Cross-framework gap analysis (Sprint 160)."""
```

### Framework Service: `nist_govern_service.py`

```python
class NISTGovernService(ComplianceService):
    """NIST AI RMF GOVERN-specific logic."""
    
    async def evaluate_govern(self, project_id: UUID) -> GovernResult:
        """Evaluate all 5 GOVERN policies."""
        # Batch evaluate GOVERN-1.1 through GOVERN-1.5
        
    async def get_risk_register(self, project_id: UUID) -> List[RiskEntry]:
        """Get risk register with score sorting."""
        
    async def create_risk(self, project_id: UUID, data: RiskCreate) -> RiskEntry:
        """Create risk entry with auto-calculated score."""
        risk_score = likelihood_value * impact_value
        
    async def get_raci_matrix(self, project_id: UUID) -> RACIMatrix:
        """Get RACI accountability matrix."""
```

**Design Pattern**: Inheritance from `ComplianceService` for shared logic, framework services override for specific behavior.

---

## Integration Points

### 1. Gate Model Integration

**Existing**: `backend/app/models/gate.py` defines G1-G10 gates  
**Integration**: `compliance_controls.gate_mapping` VARCHAR field links controls to gates

**Example Mapping**:
- GOVERN-1.3 (Legal Compliance) → G1 (Opportunity Gate)
- EU AI Act Art.6 (Classification) → G2 (Design Gate)
- ISO 42001 Clause 5.1 (Leadership) → G1 (Opportunity Gate)

**Benefit**: Compliance controls inherit gate validation logic (no duplication).

### 2. Evidence Vault Integration

**Existing**: `backend/app/models/evidence.py` with MinIO storage  
**Integration**: `compliance_assessments.evidence_ids` UUID[] array

**Flow**:
1. User uploads evidence (existing flow)
2. Evidence stored in MinIO (existing)
3. Assessment links to evidence via UUID
4. OPA policy fetches evidence metadata for evaluation

**Benefit**: Single evidence repository for gates + compliance (no duplication).

### 3. OPA Service Integration

**Existing**: `backend/app/services/opa_service.py`  
**Integration**: Call `opa_service.evaluate_policy()` with compliance policy code

```python
# Existing pattern (reused)
result = await opa_service.evaluate_policy(
    policy_path="compliance/nist/govern/accountability_structure",
    input_data={"project_id": str(project_id), ...}
)
```

**Benefit**: Reuse existing OPA infrastructure (no new policy engine).

---

## Testing Strategy

### Test Pyramid

```
E2E Tests (10%)
├── test_nist_govern_e2e.py          # Full workflow: create project → evaluate → dashboard
├── test_cross_framework_e2e.py      # Multi-framework scenarios

Integration Tests (30%)
├── test_compliance_service.py       # Service + DB + OPA integration
├── test_nist_govern_service.py      # NIST-specific service tests
├── test_compliance_routes.py        # API routes + auth

Unit Tests (60%)
├── test_compliance_models.py        # SQLAlchemy model validation
├── test_compliance_schemas.py       # Pydantic schema validation
├── test_opa_policies.py             # OPA policy unit tests (opa test)
└── NistGovernPage.test.tsx          # Frontend component tests
```

### OPA Policy Testing

```bash
# Run OPA policy tests
cd backend/policy-packs/rego
opa test compliance/ -v

# Example test: accountability_structure_test.rego
test_govern_1_1_pass {
    result := accountability_structure.allow with input as {
        "project_id": "test-123",
        "ai_systems": [{"name": "Chatbot", "owner": "john@example.com"}]
    }
    result.allowed == true
}

test_govern_1_1_fail_no_owner {
    result := accountability_structure.allow with input as {
        "ai_systems": [{"name": "Chatbot", "owner": null}]
    }
    result.allowed == false
}
```

---

## Migration Strategy

### Alembic Migration: `s156_001_compliance_framework.py`

```python
def upgrade():
    # Create 5 tables
    op.create_table('compliance_frameworks', ...)
    op.create_table('compliance_controls', ...)
    op.create_table('compliance_assessments', ...)
    op.create_table('compliance_risk_register', ...)
    op.create_table('compliance_raci', ...)
    
    # Seed data: 3 frameworks
    op.execute("""
        INSERT INTO compliance_frameworks (code, name, version, total_controls) VALUES
        ('NIST_AI_RMF', 'NIST AI Risk Management Framework', '1.0', 15),
        ('EU_AI_ACT', 'EU AI Act', '2024/1689', 12),
        ('ISO_42001', 'ISO/IEC 42001:2023', '2023', 38);
    """)
    
    # Seed NIST GOVERN controls (GOVERN-1.1 through GOVERN-1.5)
    # ...

def downgrade():
    op.drop_table('compliance_raci')
    op.drop_table('compliance_risk_register')
    op.drop_table('compliance_assessments')
    op.drop_table('compliance_controls')
    op.drop_table('compliance_frameworks')
```

**Rollback Strategy**: Downgrade migration drops all compliance tables. No impact on existing gates/evidence.

---

## Performance Considerations

### Query Optimization

1. **Indexes**: 12 indexes created (see schema) for common queries
2. **Eager Loading**: Use `selectinload()` for framework → controls → assessments
3. **Pagination**: All list endpoints support `limit`/`offset` (max 100 records)
4. **Caching**: TanStack Query caches dashboard data (5min staleTime)

### OPA Policy Performance

- **Target**: <50ms per policy evaluation
- **Strategy**: Minimal external calls (all data in input JSON)
- **Monitoring**: Prometheus histogram for `opa_policy_evaluation_duration_seconds`

### Dashboard Load Time

- **Target**: <1s for GOVERN dashboard (5 cards + 1 table)
- **Strategy**: Parallel API calls via `Promise.all()` in frontend
- **Monitoring**: Frontend performance API timing

---

## Security Considerations

### Authentication

- All compliance endpoints require JWT (existing auth middleware)
- RBAC: Role `compliance_auditor` can read assessments, `admin` can write

### Authorization

- Project-level access control (existing): Users can only access assessments for projects they own/collaborate on
- OPA policies run in sandboxed environment (existing OPA deployment)

### Data Protection

- PII in risk register notes: Encrypted at rest (PostgreSQL TDE)
- Compliance exports: Watermarked with user ID + timestamp
- Audit trail: All assessment changes logged in `updated_at`

---

## Compliance with SDLC Framework 6.0.5

### Framework Integration

**Methodology Update** (Framework 6.0.5 - Sprint 156 Day 5):
- Add "Compliance Framework Methodology" section to Framework
- 3-step process: Assess → Evaluate (OPA) → Evidence
- Control-to-Gate mapping pattern documented
- Risk register workflow added

**Gate Mapping**:
- G1 (Opportunity): Legal clearance, leadership commitment
- G2 (Design): Risk classification, technical design compliance
- G5 (Code Complete): Security controls, operational compliance
- G9 (Launch Ready): Conformity assessment, transparency docs

---

## Risks & Mitigation

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| NIST AI RMF changes (v2.0) | High | Medium | Abstract framework version in DB, OPA policies versioned |
| EU AI Act interpretation ambiguity | High | Medium | Hire compliance expert Sprint 157, legal review |
| OPA policy performance <50ms | Medium | Low | Benchmark in Sprint 156 Day 2, optimize if needed |
| Test coverage <90% | Medium | Low | TDD enforcement, pre-commit coverage check |
| JSONB schema drift | Low | Medium | Document schema in this ADR, validate in service layer |

---

## Alternatives Considered

### Alternative 1: Per-Framework Tables

**Approach**: `nist_assessments`, `eu_assessments`, `iso_assessments` tables  
**Rejected**: Schema duplication, no cross-framework queries, 3x maintenance cost

### Alternative 2: Hardcoded Compliance Logic

**Approach**: Python if/else for compliance rules  
**Rejected**: Not auditable, requires code deploy for rule changes, violates Policy-as-Code principle

### Alternative 3: External Compliance SaaS

**Approach**: Integrate with Vanta/Drata/OneTrust  
**Rejected**: $50K+ annual cost, vendor lock-in, no control over AI-specific rules

---

## Success Metrics

### Sprint 156 Exit Criteria

1. ✅ 5 compliance tables created + seeded
2. ✅ 5 OPA GOVERN policies deployed
3. ✅ 10 API endpoints functional (3 shared + 7 NIST)
4. ✅ GOVERN dashboard renders with live data
5. ✅ 85 tests passing (100% pass rate)
6. ✅ 0 critical security vulnerabilities

### Phase 3 Success (Sprint 156-160)

1. Framework realization: 90% → 92%
2. 600 tests total (85+130+125+135+125)
3. 3 enterprise POCs signed (Fortune 500)
4. Compliance dashboard <1s load time
5. 95% test coverage maintained

---

## Implementation Timeline

| Sprint | Focus | Deliverables | Tests |
|--------|-------|--------------|-------|
| 156 | NIST GOVERN | 5 policies, dashboard, risk register | 85 |
| 157 | NIST MAP/MEASURE | AI inventory, risk scoring | 130 |
| 158 | EU AI Act | Classification, conformity | 125 |
| 159 | ISO 42001 | 38 controls, audit export | 135 |
| 160 | Integration | Unified dashboard, gap analysis | 125 |

**Total**: 5 sprints, ~9,300 LOC, 600 tests

---

## Approval

**Status**: ✅ APPROVED  
**Date**: February 5, 2026  
**Approver**: CTO, SDLC Orchestrator  
**Next Review**: Sprint 156 Day 3 checkpoint (April 9, 2026)

**Conditions Met**:
1. ✅ Shared architecture documented
2. ✅ JSONB schemas defined
3. ✅ Integration points clarified
4. ✅ Test strategy detailed
5. ✅ Security considerations addressed

---

## References

- [NIST AI RMF 1.0](https://www.nist.gov/itl/ai-risk-management-framework) (January 2023)
- [EU AI Act (2024/1689)](https://eur-lex.europa.eu/eli/reg/2024/1689) (June 2024)
- [ISO/IEC 42001:2023](https://www.iso.org/standard/81230.html) (December 2023)
- [CTO Strategic Plan Phase 3-5](../09-govern/01-CTO-Reports/CTO-STRATEGIC-PLAN-PHASE-3-5.md)
- [Gate Model](./ADR-005-Quality-Gates-V2.md)
- [Evidence Vault](./ADR-027-Evidence-Vault-Architecture.md)
- [OPA Integration](./ADR-018-Policy-Engine-OPA.md)

---

**Last Updated**: February 5, 2026  
**Version**: 1.0.0  
**Next ADR**: ADR-052 (TBD)
