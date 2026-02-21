# Sprint 102: MRP/VCR 5-Point Validation + 4-Tier Enforcement

**Version**: 1.0.0  
**Date**: January 23, 2026  
**Status**: DESIGN APPROVED - Ready for Implementation  
**Epic**: GAP-003, P1-003 (SDLC 6.1.0 Compliance)

---

## Executive Summary

**Goal**: Implement 5-point evidence structure for MRP (Merge Readiness Protocol) and VCR (Verification Completion Report), plus 4-Tier policy enforcement for graduated governance.

**Timeline**: 5 days (Feb 3 - Feb 7, 2026)  
**Story Points**: 22 SP  
**Owner**: Backend Lead + DevOps Lead

**Key Deliverables**:
1. MRP/VCR 5-Point Evidence Validator
2. 4-Tier Policy Enforcement Engine (Lite/Standard/Professional/Enterprise)
3. Evidence Vault enhancement with structured storage
4. Policy pack selection UI
5. 30+ tests

---

## Background

### Framework 5.2.0 Requirements

**MRP 5-Point Evidence Structure**:
```yaml
1. Test Evidence:
   - Unit test results (coverage %)
   - Integration test results
   - E2E test results (if applicable)
   
2. Lint Evidence:
   - ruff (Python)
   - eslint (JavaScript/TypeScript)
   - Zero errors required
   
3. Security Evidence:
   - bandit scan (Python)
   - npm audit (JavaScript)
   - grype scan (containers)
   - Zero critical vulnerabilities
   
4. Build Evidence:
   - Docker build success
   - Package build success
   - No warnings tolerated
   
5. Conformance Evidence:
   - Pattern conformance score (from Sprint 99)
   - ADR alignment check
   - Risk analysis (from Sprint 101)
```

**VCR (Verification Completion Report)**:
- Aggregates all 5 MRP points
- Pass/Fail verdict
- Stored in Evidence Vault (tamper-evident)
- Required for PR merge

### 4-Tier Policy Enforcement

| Tier | Target Audience | Enforcement Level | Example Rules |
|------|----------------|-------------------|---------------|
| **LITE** | Individuals, prototypes | Advisory only | Tests recommended, security warnings |
| **STANDARD** | Small teams (2-5) | Soft enforcement | Tests required (80%+), linting required |
| **PROFESSIONAL** | Medium teams (5-15) | Hard enforcement | Tests required (90%+), security scan, ADR check |
| **ENTERPRISE** | Large orgs (15+) | Strictest | Tests required (95%+), all 5 MRP points, CRP for high-risk |

**Current State**: Only PROFESSIONAL tier implemented (hard-coded)

---

## Architecture

### Component Overview

```
┌────────────────────────────────────────────────────────────────┐
│           SPRINT 102: MRP/VCR + 4-TIER ENFORCEMENT             │
├────────────────────────────────────────────────────────────────┤
│                                                                │
│  PR Created / Updated                                          │
│         ↓                                                      │
│  ┌──────────────────────────────────────────────────────────┐ │
│  │ Project Settings                                         │ │
│  │ - policy_pack_tier: LITE | STANDARD | PRO | ENTERPRISE  │ │
│  └──────────────────────────────────────────────────────────┘ │
│         ↓                                                      │
│  ┌──────────────────────────────────────────────────────────┐ │
│  │ PolicyEnforcementService (NEW)                           │ │
│  │ - get_policies_for_tier(tier)                            │ │
│  │ - evaluate_policies(pr_data, tier)                       │ │
│  └──────────────────────────────────────────────────────────┘ │
│         ↓                                                      │
│  ┌──────────────────────────────────────────────────────────┐ │
│  │ Parallel Evidence Collection                             │ │
│  │                                                          │ │
│  │  ┌────────────┐  ┌────────────┐  ┌────────────┐        │ │
│  │  │ Test       │  │ Lint       │  │ Security   │        │ │
│  │  │ Runner     │  │ Runner     │  │ Scanner    │        │ │
│  │  └────────────┘  └────────────┘  └────────────┘        │ │
│  │                                                          │ │
│  │  ┌────────────┐  ┌────────────┐                        │ │
│  │  │ Build      │  │ Conformance│                        │ │
│  │  │ Verifier   │  │ Checker    │                        │ │
│  │  └────────────┘  └────────────┘                        │ │
│  └──────────────────────────────────────────────────────────┘ │
│         ↓                                                      │
│  ┌──────────────────────────────────────────────────────────┐ │
│  │ MRPValidationService (NEW)                               │ │
│  │ - validate_5_point_structure()                           │ │
│  │ - calculate_mrp_score()                                  │ │
│  │ - generate_vcr()                                         │ │
│  └──────────────────────────────────────────────────────────┘ │
│         ↓                                                      │
│  ┌──────────────────────────────────────────────────────────┐ │
│  │ Evidence Vault (Enhanced)                                │ │
│  │ - Store VCR with SHA256 hash                             │ │
│  │ - Link to PR/commit                                      │ │
│  │ - Tamper-evident chain                                   │ │
│  └──────────────────────────────────────────────────────────┘ │
│         ↓                                                      │
│  ┌──────────────────────────────────────────────────────────┐ │
│  │ GitHub Check Run                                         │ │
│  │ - Post MRP summary as check                              │ │
│  │ - Block merge if tier requirements not met              │ │
│  └──────────────────────────────────────────────────────────┘ │
│                                                                │
└────────────────────────────────────────────────────────────────┘
```

---

## Detailed Tasks

### Backend (16 SP - 4 days)

#### Task 1.1: Policy Definition System (3 SP - 1 day)

**File**: `backend/app/policies/tier_policies.py` (~400 lines)

**Policy Structure**:
```python
from dataclasses import dataclass
from enum import Enum

class PolicyTier(str, Enum):
    LITE = "LITE"
    STANDARD = "STANDARD"
    PROFESSIONAL = "PROFESSIONAL"
    ENTERPRISE = "ENTERPRISE"

@dataclass
class TierPolicy:
    tier: PolicyTier
    test_coverage_required: int  # 0-100
    test_required: bool
    lint_required: bool
    security_scan_required: bool
    build_verification_required: bool
    conformance_check_required: bool
    risk_analysis_required: bool
    crp_required_for_high_risk: bool
    adr_alignment_required: bool
    
    # Thresholds
    max_critical_vulnerabilities: int
    max_high_vulnerabilities: int
    min_conformance_score: int  # 0-100

# Policy Definitions
TIER_POLICIES = {
    PolicyTier.LITE: TierPolicy(
        tier=PolicyTier.LITE,
        test_coverage_required=0,
        test_required=False,
        lint_required=False,
        security_scan_required=False,
        build_verification_required=False,
        conformance_check_required=False,
        risk_analysis_required=False,
        crp_required_for_high_risk=False,
        adr_alignment_required=False,
        max_critical_vulnerabilities=999,
        max_high_vulnerabilities=999,
        min_conformance_score=0
    ),
    
    PolicyTier.STANDARD: TierPolicy(
        tier=PolicyTier.STANDARD,
        test_coverage_required=80,
        test_required=True,
        lint_required=True,
        security_scan_required=True,
        build_verification_required=False,
        conformance_check_required=False,
        risk_analysis_required=True,
        crp_required_for_high_risk=False,
        adr_alignment_required=False,
        max_critical_vulnerabilities=0,
        max_high_vulnerabilities=5,
        min_conformance_score=50
    ),
    
    PolicyTier.PROFESSIONAL: TierPolicy(
        tier=PolicyTier.PROFESSIONAL,
        test_coverage_required=90,
        test_required=True,
        lint_required=True,
        security_scan_required=True,
        build_verification_required=True,
        conformance_check_required=True,
        risk_analysis_required=True,
        crp_required_for_high_risk=True,
        adr_alignment_required=True,
        max_critical_vulnerabilities=0,
        max_high_vulnerabilities=2,
        min_conformance_score=70
    ),
    
    PolicyTier.ENTERPRISE: TierPolicy(
        tier=PolicyTier.ENTERPRISE,
        test_coverage_required=95,
        test_required=True,
        lint_required=True,
        security_scan_required=True,
        build_verification_required=True,
        conformance_check_required=True,
        risk_analysis_required=True,
        crp_required_for_high_risk=True,
        adr_alignment_required=True,
        max_critical_vulnerabilities=0,
        max_high_vulnerabilities=0,
        min_conformance_score=85
    )
}
```

**Tests**: 8 tests (policy retrieval, validation, tier comparison)

---

#### Task 1.2: MRPValidationService (5 SP - 1.5 days)

**File**: `backend/app/services/mrp_validation_service.py` (~700 lines)

**Key Methods**:
```python
class MRPValidationService:
    def __init__(
        self,
        test_service: TestService,
        lint_service: LintService,
        security_service: SecurityService,
        build_service: BuildService,
        conformance_service: ConformanceCheckService,  # Sprint 99
        evidence_service: EvidenceVaultService
    ):
        ...
    
    async def validate_mrp_5_points(
        self,
        project_id: UUID,
        pr_id: str,
        tier: PolicyTier
    ) -> MRPValidation:
        """
        Validate all 5 MRP evidence points against tier policy.
        
        Returns:
            MRPValidation with pass/fail per point, overall verdict
        """
        policy = TIER_POLICIES[tier]
        
        # Parallel evidence collection
        test_evidence, lint_evidence, security_evidence, build_evidence, conformance_evidence = await asyncio.gather(
            self._collect_test_evidence(project_id, pr_id) if policy.test_required else None,
            self._collect_lint_evidence(project_id, pr_id) if policy.lint_required else None,
            self._collect_security_evidence(project_id, pr_id) if policy.security_scan_required else None,
            self._collect_build_evidence(project_id, pr_id) if policy.build_verification_required else None,
            self._collect_conformance_evidence(project_id, pr_id) if policy.conformance_check_required else None
        )
        
        # Validate each point
        test_pass = self._validate_test_evidence(test_evidence, policy)
        lint_pass = self._validate_lint_evidence(lint_evidence, policy)
        security_pass = self._validate_security_evidence(security_evidence, policy)
        build_pass = self._validate_build_evidence(build_evidence, policy)
        conformance_pass = self._validate_conformance_evidence(conformance_evidence, policy)
        
        overall_pass = all([
            test_pass.passed if policy.test_required else True,
            lint_pass.passed if policy.lint_required else True,
            security_pass.passed if policy.security_scan_required else True,
            build_pass.passed if policy.build_verification_required else True,
            conformance_pass.passed if policy.conformance_check_required else True
        ])
        
        return MRPValidation(
            test=test_pass,
            lint=lint_pass,
            security=security_pass,
            build=build_pass,
            conformance=conformance_pass,
            overall_passed=overall_pass,
            tier=tier,
            timestamp=datetime.utcnow()
        )
    
    async def generate_vcr(
        self,
        mrp_validation: MRPValidation,
        project_id: UUID,
        pr_id: str
    ) -> VCR:
        """
        Generate Verification Completion Report.
        
        Stores in Evidence Vault with tamper-evident hash.
        """
        vcr = VCR(
            id=uuid4(),
            project_id=project_id,
            pr_id=pr_id,
            mrp_validation=mrp_validation,
            verdict="PASS" if mrp_validation.overall_passed else "FAIL",
            created_at=datetime.utcnow()
        )
        
        # Store in Evidence Vault
        evidence_hash = await self.evidence_service.store_vcr(vcr)
        vcr.evidence_hash = evidence_hash
        
        return vcr
    
    def _validate_test_evidence(
        self,
        evidence: TestEvidence,
        policy: TierPolicy
    ) -> ValidationResult:
        """Validate test evidence against policy."""
        if not evidence:
            return ValidationResult(
                passed=False,
                message="Test evidence not found",
                details={}
            )
        
        if evidence.coverage < policy.test_coverage_required:
            return ValidationResult(
                passed=False,
                message=f"Test coverage {evidence.coverage}% < {policy.test_coverage_required}% required",
                details={"coverage": evidence.coverage, "required": policy.test_coverage_required}
            )
        
        if evidence.failed_tests > 0:
            return ValidationResult(
                passed=False,
                message=f"{evidence.failed_tests} tests failed",
                details={"failed_tests": evidence.failed_tests}
            )
        
        return ValidationResult(
            passed=True,
            message=f"Test evidence valid ({evidence.coverage}% coverage)",
            details={"coverage": evidence.coverage, "total_tests": evidence.total_tests}
        )
    
    # Similar validators for lint, security, build, conformance...
```

**Tests**: 15 tests
- 5-point validation logic
- Tier policy enforcement
- VCR generation
- Evidence storage
- Edge cases (missing evidence, partial evidence)

---

#### Task 1.3: PolicyEnforcementService (4 SP - 1 day)

**File**: `backend/app/services/policy_enforcement_service.py` (~500 lines)

**Key Methods**:
```python
class PolicyEnforcementService:
    async def enforce_pr_policies(
        self,
        project_id: UUID,
        pr_id: str
    ) -> PolicyEnforcementResult:
        """
        Enforce policies for PR based on project tier.
        
        Flow:
            1. Get project tier
            2. Get tier policies
            3. Run MRP validation
            4. Generate VCR
            5. Update GitHub check status
        """
        project = await self.project_repo.get(project_id)
        tier = PolicyTier(project.policy_pack_tier)
        
        # Run MRP validation
        mrp_validation = await self.mrp_service.validate_mrp_5_points(
            project_id,
            pr_id,
            tier
        )
        
        # Generate VCR
        vcr = await self.mrp_service.generate_vcr(
            mrp_validation,
            project_id,
            pr_id
        )
        
        # Update GitHub check
        await self.github_service.create_check_run(
            repo=project.github_repo_full_name,
            pr_number=pr_id,
            name="SDLC MRP Validation",
            status="completed",
            conclusion="success" if vcr.verdict == "PASS" else "failure",
            output={
                "title": f"MRP Validation: {vcr.verdict}",
                "summary": self._format_vcr_summary(vcr),
                "text": self._format_vcr_details(vcr)
            }
        )
        
        return PolicyEnforcementResult(
            tier=tier,
            vcr=vcr,
            enforcement_actions=[...],
            timestamp=datetime.utcnow()
        )
    
    async def check_tier_compliance(
        self,
        project_id: UUID
    ) -> TierComplianceReport:
        """
        Check if project meets tier requirements.
        
        Useful for tier upgrade/downgrade recommendations.
        """
        ...
```

**Tests**: 10 tests
- Tier enforcement logic
- GitHub check integration
- VCR storage validation
- Compliance reporting

---

#### Task 1.4: Evidence Vault Enhancement (2 SP - 0.5 day)

**File**: `backend/app/services/evidence_vault_service.py` (modify existing)

**New Methods**:
```python
class EvidenceVaultService:
    # Existing methods...
    
    async def store_vcr(self, vcr: VCR) -> str:
        """
        Store VCR in MinIO with structured path.
        
        Path: evidence/{project_id}/vcr/{pr_id}/{timestamp}.json
        Returns: SHA256 hash
        """
        vcr_json = vcr.json()
        vcr_hash = hashlib.sha256(vcr_json.encode()).hexdigest()
        
        path = f"evidence/{vcr.project_id}/vcr/{vcr.pr_id}/{vcr.created_at.isoformat()}.json"
        
        await self.minio_client.put_object(
            bucket_name=self.evidence_bucket,
            object_name=path,
            data=BytesIO(vcr_json.encode()),
            length=len(vcr_json),
            content_type="application/json",
            metadata={
                "sha256": vcr_hash,
                "verdict": vcr.verdict,
                "tier": vcr.mrp_validation.tier
            }
        )
        
        # Update hash chain
        await self._update_hash_chain(vcr.project_id, vcr_hash)
        
        return vcr_hash
    
    async def retrieve_vcr(
        self,
        project_id: UUID,
        pr_id: str,
        timestamp: datetime | None = None
    ) -> VCR:
        """Retrieve VCR with hash verification."""
        ...
    
    async def list_vcrs(
        self,
        project_id: UUID,
        pr_id: str | None = None
    ) -> list[VCR]:
        """List VCRs for project/PR."""
        ...
```

**Tests**: 5 tests
- VCR storage
- Hash verification
- VCR retrieval
- Hash chain integrity

---

#### Task 1.5: API Routes (2 SP - 0.5 day)

**File**: `backend/app/api/routes/mrp.py` (~300 lines)

**Endpoints**:
```python
# MRP Validation
POST /api/v1/mrp/validate
  Body: { project_id, pr_id }
  Response: MRPValidation

GET /api/v1/mrp/validate/{project_id}/{pr_id}
  Response: MRPValidation (latest)

# VCR
GET /api/v1/vcr/{project_id}/{pr_id}
  Response: VCR (latest)

GET /api/v1/vcr/{project_id}/{pr_id}/history
  Response: { vcrs: VCR[] }

# Policy Enforcement
POST /api/v1/policies/enforce
  Body: { project_id, pr_id }
  Response: PolicyEnforcementResult

GET /api/v1/policies/tiers
  Response: { tiers: TierPolicy[] }

GET /api/v1/policies/compliance/{project_id}
  Response: TierComplianceReport
```

---

### Frontend (4 SP - 1 day)

#### Task 2.1: Policy Tier Selector (2 SP - 0.5 day)

**File**: `frontend/src/app/app/projects/settings/page.tsx` (modify existing)

**Features**:
- Tier dropdown (Lite/Standard/Professional/Enterprise)
- Policy comparison table
- Tier requirements display
- Upgrade/downgrade flow

**Component**:
```tsx
function PolicyTierSelector({ project }) {
  const [selectedTier, setSelectedTier] = useState(project.policy_pack_tier)
  const updateTierMutation = useUpdateProjectTier()
  
  return (
    <div>
      <Select value={selectedTier} onChange={setSelectedTier}>
        <option value="LITE">Lite (Advisory)</option>
        <option value="STANDARD">Standard (Soft Enforcement)</option>
        <option value="PROFESSIONAL">Professional (Hard Enforcement)</option>
        <option value="ENTERPRISE">Enterprise (Strictest)</option>
      </Select>
      
      <TierPolicyComparison currentTier={project.policy_pack_tier} selectedTier={selectedTier} />
      
      <Button onClick={() => updateTierMutation.mutate({ projectId: project.id, tier: selectedTier })}>
        Update Tier
      </Button>
    </div>
  )
}
```

---

#### Task 2.2: MRP/VCR Dashboard Widget (2 SP - 0.5 day)

**File**: `frontend/src/components/mrp/MRPDashboard.tsx` (~250 lines)

**Features**:
- 5-point evidence status (pass/fail badges)
- Overall verdict display
- Detailed evidence view (modal)
- VCR download link
- Tier requirements vs actual

**Component**:
```tsx
function MRPDashboard({ projectId, prId }) {
  const { data: mrp } = useMRPValidation(projectId, prId)
  const { data: vcr } = useVCR(projectId, prId)
  
  return (
    <Card>
      <VerdictBadge verdict={vcr?.verdict} />
      
      <div className="grid grid-cols-5 gap-4">
        <EvidencePoint 
          name="Test" 
          status={mrp?.test.passed} 
          details={mrp?.test.details} 
        />
        <EvidencePoint 
          name="Lint" 
          status={mrp?.lint.passed} 
          details={mrp?.lint.details} 
        />
        <EvidencePoint 
          name="Security" 
          status={mrp?.security.passed} 
          details={mrp?.security.details} 
        />
        <EvidencePoint 
          name="Build" 
          status={mrp?.build.passed} 
          details={mrp?.build.details} 
        />
        <EvidencePoint 
          name="Conformance" 
          status={mrp?.conformance.passed} 
          details={mrp?.conformance.details} 
        />
      </div>
      
      <TierRequirementsDisplay tier={mrp?.tier} />
      <VCRDownloadButton vcrId={vcr?.id} />
    </Card>
  )
}
```

---

### DevOps (2 SP - 0.5 day)

#### Task 3.1: GitHub Webhook Enhancement

**File**: `backend/app/api/webhooks/github_webhook.py` (modify existing)

**Changes**:
- Trigger MRP validation on PR open/update
- Call PolicyEnforcementService
- Post check run with MRP summary

---

## Success Metrics

| Metric | Target | Verification |
|--------|--------|--------------|
| MRP validation latency | <30s | Monitor first 100 PRs |
| VCR storage success rate | 100% | Evidence Vault audit |
| Tier policy accuracy | 100% | Manual review of 20 PRs |
| False policy violations | <5% | Developer feedback |
| GitHub check reliability | >99% | Monitor webhook logs |

---

## Testing Strategy

### Unit Tests (20 tests)

**Policy System** (8 tests):
- Tier policy definitions
- Policy retrieval
- Policy comparison

**MRPValidationService** (15 tests):
- 5-point validation (3 tests each)
- VCR generation
- Tier-specific enforcement

**PolicyEnforcementService** (10 tests):
- Enforcement flow
- GitHub check updates
- Compliance reporting

### Integration Tests (5 tests)

- End-to-end MRP validation
- Evidence Vault storage + retrieval
- GitHub webhook → MRP → Check run
- Tier upgrade/downgrade
- VCR hash chain verification

### E2E Tests (5 tests)

- Change tier setting
- Trigger PR validation
- View MRP dashboard
- Download VCR report
- Verify GitHub check

---

## Migration Plan

### Database Migration

**File**: `backend/alembic/versions/s102_001_add_tier_to_projects.py`

```python
def upgrade():
    # Add policy_pack_tier to projects table
    op.add_column(
        'projects',
        sa.Column('policy_pack_tier', sa.String(), nullable=False, server_default='PROFESSIONAL')
    )
    
    # Create vcr_reports table
    op.create_table(
        'vcr_reports',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('project_id', sa.UUID(), nullable=False),
        sa.Column('pr_id', sa.String(), nullable=False),
        sa.Column('verdict', sa.String(), nullable=False),
        sa.Column('mrp_validation', sa.JSON(), nullable=False),
        sa.Column('evidence_hash', sa.String(64), nullable=False),
        sa.Column('created_at', sa.TIMESTAMP(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'])
    )
    
    op.create_index('idx_vcr_project_pr', 'vcr_reports', ['project_id', 'pr_id'])

def downgrade():
    op.drop_table('vcr_reports')
    op.drop_column('projects', 'policy_pack_tier')
```

---

## Documentation Updates

### Framework

**File**: `SDLC-Enterprise-Framework/05-Templates-Tools/SASE-Artifacts/02-MRP-Template.md`

- Update with 5-point structure
- Add tier-specific examples
- Document VCR format

### Orchestrator

**Files**:
- `PROJECT-STATUS.md` - Sprint 102 completion
- `docs/02-design/03-ADRs/ADR-036-4-Tier-Policy-Enforcement.md` - New ADR

---

## Timeline

| Day | Tasks | Owner | Hours |
|-----|-------|-------|-------|
| **Day 1** | Policy system + MRPValidationService start | Backend | 8h |
| **Day 2** | MRPValidationService completion | Backend | 8h |
| **Day 3** | PolicyEnforcementService + Evidence Vault | Backend | 8h |
| **Day 4** | Frontend: Tier selector + MRP dashboard | Frontend | 8h |
| **Day 5** | Integration + E2E tests + Documentation | Full Team | 8h |

**Total Effort**: 40 hours (22 SP = 1.8 hours/SP)

---

## Approval

**Status**: ✅ APPROVED FOR IMPLEMENTATION

```
┌─────────────────────────────────────────────────────────────────┐
│                    ✅ SPRINT 102 APPROVED                       │
│                                                                 │
│  Sprint: 102 - MRP/VCR 5-Point + 4-Tier Enforcement            │
│  Date: January 23, 2026                                        │
│  Story Points: 22 SP                                           │
│  Timeline: 5 days (Feb 3 - Feb 7)                             │
│                                                                 │
│  "Completes P0 gaps for SDLC 6.1.0 compliance.                │
│   Graduated governance enables adoption at all org sizes."     │
│                                                                 │
│  — CTO, SDLC Orchestrator                                      │
└─────────────────────────────────────────────────────────────────┘
```
