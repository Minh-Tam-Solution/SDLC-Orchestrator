# Sprint 156 Kickoff Checklist
**Sprint**: 156 - NIST AI RMF GOVERN  
**Dates**: April 7-11, 2026 (5 days)  
**Status**: 🟢 APPROVED (all conditions met)  
**CTO Approval**: ✅ APPROVED (Feb 5, 2026)

**Delivery Summary** (Actual):
- **Backend**: 12 files, ~4,500 LOC
- **Frontend**: 5 files, ~2,700 LOC
- **Tests**: 77 tests (target: 85 - need 8 more OPA tests)
- **Total LOC**: ~9,700 (485% of estimate - excellent!)

---

## 📋 Pre-Sprint Checklist (Before April 7)

### ✅ Approval & Documentation (COMPLETE - Feb 5, 2026)

- [x] **ADR-051 Created**: Compliance Framework Architecture ✅
- [x] **JSONB Schema Defined**: TypeScript-style schema in ADR-051 ✅
- [x] **Phase 3 Design Approved**: CTO conditional approval ✅
- [x] **All 5 Conditions Met**: Ready for execution ✅
- [ ] **ADR-051 Reviewed**: Technical Lead review + approval (Due Feb 12)
- [ ] **ADR-051 Merged**: PR merged to main branch (Due Feb 12)
- [ ] **Framework 6.0.5 Outline**: Compliance methodology section drafted (Due Feb 12)

---

## Day 1 (Monday): Database + Models + Schemas

### RED Phase (Tests First)

- [ ] Write 15 model/schema tests in `test_compliance_service.py`
  - [ ] Test ComplianceFramework model creation
  - [ ] Test ComplianceControl model with JSONB evidence_required
  - [ ] Test ComplianceAssessment model status enum
  - [ ] Test ComplianceRiskRegister risk_score calculation
  - [ ] Test ComplianceRACI model with UUID arrays
  - [ ] Test Pydantic schema serialization (all 5 models)
  - [ ] Test Pydantic validation (required fields, enum values)
  - [ ] Test evidence_required JSONB structure validation

### GREEN Phase (Implementation)

- [ ] Create Alembic migration `s156_001_compliance_framework.py`
  - [ ] `compliance_frameworks` table
  - [ ] `compliance_controls` table with JSONB + UNIQUE constraint
  - [ ] `compliance_assessments` table with indexes
  - [ ] `compliance_risk_register` table with score index
  - [ ] `compliance_raci` table with UNIQUE constraint
  - [ ] Seed NIST_AI_RMF framework + 5 GOVERN controls

- [ ] Create SQLAlchemy models in `backend/app/models/compliance.py`
  - [ ] `ComplianceFramework` model
  - [ ] `ComplianceControl` model
  - [ ] `ComplianceAssessment` model
  - [ ] `ComplianceRiskRegister` model
  - [ ] `ComplianceRACI` model
  - [ ] Status enums (AssessmentStatus, RiskLikelihood, RiskImpact, RiskStatus)

- [ ] Create Pydantic schemas in `backend/app/schemas/compliance.py`
  - [ ] Request schemas: FrameworkFilter, AssessmentCreate, RiskCreate, RACICreate
  - [ ] Response schemas: FrameworkResponse, ControlResponse, AssessmentResponse
  - [ ] Risk response with computed score
  - [ ] RACI response with user details

- [ ] Register models in `backend/app/models/__init__.py`

### Verification

- [ ] All 15 tests pass
- [ ] Migration runs successfully (up and down)
- [ ] Models match ADR-051 schema exactly

---

## Day 2 (Tuesday): OPA Policies + Policy Tests

### RED Phase (Tests First)

- [ ] Write 15 Rego policy tests in `test_nist_rego_policies.py`
  - [ ] 3 tests per policy (pass, fail, edge case)
  - [ ] `accountability_structure`: all owned, some unowned, empty list
  - [ ] `risk_culture`: 80%+ trained, <80% trained, zero members
  - [ ] `legal_compliance`: approved, not approved, missing reviewer
  - [ ] `third_party_oversight`: all compliant, missing SLA, no APIs
  - [ ] `continuous_improvement`: timely postmortem, >48h delay, no incidents

### GREEN Phase (Implementation)

- [ ] Create policy directory: `backend/policy-packs/rego/compliance/nist/govern/`
- [ ] Write `accountability_structure.rego` (GOVERN-1.1)
  - [ ] Package: `compliance.nist.govern.accountability`
  - [ ] Check all AI systems have designated owners
  - [ ] Return severity: critical
- [ ] Write `risk_culture.rego` (GOVERN-1.2)
  - [ ] Check team training >= 80% completion
  - [ ] Return severity: high
- [ ] Write `legal_compliance.rego` (GOVERN-1.3)
  - [ ] Check legal review approved with reviewer name
  - [ ] Return severity: critical
- [ ] Write `third_party_oversight.rego` (GOVERN-1.4)
  - [ ] Check all third-party APIs have SLA + privacy agreement
  - [ ] Return severity: high
- [ ] Write `continuous_improvement.rego` (GOVERN-1.5)
  - [ ] Check postmortems completed within 48h with process updates
  - [ ] Return severity: medium

### Verification

- [ ] All 15 policy tests pass
- [ ] Each policy follows the output contract: `{allowed, reason, severity, details}`
- [ ] Package naming consistent: `compliance.nist.govern.*`

---

## Day 3 (Wednesday): Backend Services

### RED Phase (Tests First)

- [ ] Write 15 tests in `test_compliance_service.py` (shared service)
  - [ ] Test framework listing (active only)
  - [ ] Test framework detail with control count
  - [ ] Test assessment creation and update
  - [ ] Test assessment listing with filters
  - [ ] Test OPA policy evaluation integration

- [ ] Write 20 tests in `test_nist_govern_service.py`
  - [ ] Test evaluate_govern() with passing input
  - [ ] Test evaluate_govern() with failing controls
  - [ ] Test risk register CRUD (create, list, update)
  - [ ] Test risk score auto-calculation
  - [ ] Test RACI matrix CRUD
  - [ ] Test GOVERN dashboard aggregation
  - [ ] Test risk filtering by category/status

### GREEN Phase (Implementation)

- [ ] Create `backend/app/services/compliance_service.py`
  - [ ] `evaluate_controls()` - OPA policy evaluation via existing OPA service
  - [ ] `get_dashboard()` - Aggregated compliance metrics
  - [ ] `list_frameworks()` - Active frameworks with control counts
  - [ ] `get_framework()` - Single framework details
  - [ ] `list_assessments()` - Per-project assessments with filters
  - [ ] `create_assessment()` / `update_assessment()`

- [ ] Create `backend/app/services/nist_govern_service.py`
  - [ ] `evaluate_govern()` - Evaluate 5 GOVERN policies via OPA
  - [ ] `get_govern_dashboard()` - GOVERN-specific metrics
  - [ ] Risk register: `create_risk()`, `list_risks()`, `update_risk()`
  - [ ] RACI: `get_raci()`, `upsert_raci()`
  - [ ] Risk score auto-calculation on create/update

### Verification

- [ ] All 35 service tests pass
- [ ] Services follow existing patterns (VCR service as reference)
- [ ] Error handling: custom exceptions (NotFound, ValidationError)

---

## Day 4 (Thursday): API Routes + Frontend Dashboard

### RED Phase (Tests First)

- [ ] Write 10 tests in `test_compliance_framework_routes.py`
  - [ ] GET /frameworks - list all
  - [ ] GET /frameworks/{code} - single framework
  - [ ] GET /projects/{pid}/assessments - with filters
  - [ ] Auth required tests (401 without token)
  - [ ] Not found tests (404 for invalid code)

- [ ] Write 15 tests in `test_nist_govern_routes.py`
  - [ ] POST /nist/govern/evaluate - success + validation
  - [ ] GET /nist/govern/dashboard - with project_id
  - [ ] GET/POST /nist/risks - CRUD
  - [ ] PUT /nist/risks/{id} - update
  - [ ] GET/POST /nist/raci - CRUD
  - [ ] Auth + validation error tests

### GREEN Phase (Implementation)

- [ ] Create `backend/app/api/routes/compliance_framework.py` (3 endpoints)
- [ ] Create `backend/app/api/routes/nist_govern.py` (7 endpoints)
- [ ] Register routes in `backend/app/main.py`
- [ ] Create `frontend/src/hooks/useCompliance.ts` (TanStack Query)
- [ ] Create `frontend/src/app/app/compliance/layout.tsx`
- [ ] Create `frontend/src/app/app/compliance/nist/page.tsx`
- [ ] Create `frontend/src/app/app/compliance/nist/govern/page.tsx`
  - [ ] GovernScoreCard (overall compliance %)
  - [ ] PolicyStatusList (5 policies pass/fail)
  - [ ] RiskHeatmap (5x5 grid)
  - [ ] RACIMatrix (table)
  - [ ] RiskRegisterTable (with add dialog)
- [ ] Add Compliance to `frontend/src/components/dashboard/Sidebar.tsx`

### Verification

- [ ] All 25 route tests pass
- [ ] Swagger UI shows all 10 endpoints correctly
- [ ] Frontend GOVERN dashboard renders without errors
- [ ] Sidebar shows Compliance nav item

---

## Day 5 (Friday): Frontend Tests + Integration + Polish

### RED Phase (Tests First)

- [ ] Write 15 tests in `NistGovernPage.test.tsx`
  - [ ] Page renders title and description
  - [ ] GovernScoreCard shows compliance percentage
  - [ ] PolicyStatusList shows 5 policies
  - [ ] RiskHeatmap renders 5x5 grid
  - [ ] RiskRegisterTable shows risk entries
  - [ ] Add Risk dialog opens and validates
  - [ ] RACI matrix renders
  - [ ] Loading states
  - [ ] Error states

### GREEN Phase (Implementation)

- [ ] Fix any failing tests from Day 1-4
- [ ] Ensure frontend components match test expectations
- [ ] Integration test: full evaluate → dashboard flow

### REFACTOR Phase

- [ ] Code review all new files
- [ ] Verify file naming standards (snake_case <=50 chars)
- [ ] Verify no TODOs or placeholders (Zero Mock Policy)
- [ ] Verify no AGPL imports

### Documentation

- [ ] Sprint 156 completion report
- [ ] Update ROADMAP-147-170.md with Sprint 156 status

---

## Sprint 156 Success Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| Tests passing | 85 | `pytest + vitest` |
| OPA policies | 5 | Manual count in `compliance/nist/govern/` |
| API endpoints | 10 | Swagger UI count |
| Frontend pages | 3 | `/compliance`, `/compliance/nist`, `/compliance/nist/govern` |
| Code coverage | 95%+ | pytest-cov |
| Zero placeholders | 0 TODOs | grep check |
| Performance | <100ms p95 | pytest-benchmark |

---

## Risk Mitigation

| Risk | Probability | Mitigation |
|------|------------|------------|
| OPA service integration issues | Medium | Use existing OPA service adapter pattern |
| Complex JSONB queries | Low | Pre-validate JSONB structure in Pydantic |
| Frontend component complexity | Medium | Reuse existing Card/Table/Badge components |
| Seed data accuracy | Low | Cross-reference NIST AI RMF 1.0 document |

---

**Prepared by**: CTO Office + AI Assistant
**Date**: February 5, 2026
**Status**: Ready for Sprint 156 kickoff
