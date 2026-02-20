# Sprint 108: Governance System Foundation

**Version**: 1.0.0
**Date**: January 28 - February 4, 2026 (7 days)
**Status**: ✅ **90% COMPLETE** (Backend Done, Tests Pending)
**Epic**: GOVERNANCE SYSTEM v1.0 - Anti-Vibecoding Implementation
**Framework**: SDLC 6.1.0
**Prerequisites**: Sprint 107 (TDD Foundation), Phase 0 (48-hour deliverables)

---

## Executive Summary

**Goal**: Implement Governance System v1.0 database layer and base services following the 14-table schema designed in Phase 0.

**Business Driver**: CEO spends 40h/sprint on manual governance → Target 10h/sprint (-75%) through automated Vibecoding Index routing and auto-generation.

**Scope**: 14-table database schema, 6 core governance services, auto-generation layer foundation (4 generators), WARNING mode infrastructure.

**Dependencies**:
- ✅ Sprint 107: TDD Foundation (factories, test stubs)
- ✅ Phase 0: Technical deliverables (6 documents, 173KB)
- ✅ CTO + CPO Approval: Week 1 execution authorized

---

## Strategic Context

### Phase 0 Deliverables (INPUT)

| Document | Content | Sprint 108 Use |
|----------|---------|----------------|
| CEO-Workflow-Analysis.md | 40h→10h target, 8 activity categories | Success metrics |
| Auto-Generation-Requirements.md | 4 generators, latency targets | Service specs |
| Governance-Signals-Design.md | 5 signals, Vibecoding Index | Algorithm implementation |
| Success-Criteria-v2.yaml | PRIMARY/SECONDARY/TERTIARY metrics | Monitoring |
| DATABASE-SCHEMA-DESIGN.md | 14 tables, ER diagram | Migration scripts |
| MONITORING-PLAN.md | 45 Prometheus metrics, 3 dashboards | Observability |

### Policy Contracts (CONSTRAINTS)

| Contract | Constraint | Sprint 108 Compliance |
|----------|------------|----------------------|
| CEO-WORKFLOW-CONTRACT | CEO won't review Green PRs | Implement routing logic |
| AUTO-GENERATION-FAIL-SAFE | 2-min developer fallback | Fallback chain required |
| VIBECODING-INDEX-EXPLAINABILITY | Every score >30 explainable | Explainability data model |

---

## Sprint Goals

### Primary Goals

1. **Database Schema Deployed**: 14-table Alembic migrations, zero-downtime
2. **SQLAlchemy Models Created**: All 14 governance models with relationships
3. **Core Services Implemented**: SubmissionService, VibecodingService, RoutingService
4. **Auto-Generation Foundation**: Intent generator (LLM + template fallback)
5. **WARNING Mode Infrastructure**: Feature flags, logging, no blocking

### Success Criteria

| Metric | Target | Verification |
|--------|--------|--------------|
| Database migrations | 14/14 tables | `alembic upgrade head` succeeds |
| SQLAlchemy models | 14/14 models | Unit tests pass |
| Core services | 3/6 services | Unit tests pass (TDD) |
| Auto-generation | 1/4 generators | Integration test pass |
| WARNING mode | Deployable | No PR blocking |
| Code coverage | >80% for new code | pytest-cov report |
| Zero mocks | 100% | TDD discipline |

### Out of Scope (Sprint 109+)

- ❌ Full Vibecoding Index calculation (Sprint 109)
- ❌ CEO Dashboard UI (Sprint 110)
- ❌ Full auto-generation (4 generators) (Sprint 109)
- ❌ SOFT/FULL enforcement modes (Sprint 110+)
- ❌ Kill switch automation (Sprint 110)

---

## Day-by-Day Plan

### Day 1: Database Migrations (14 tables)

**Deliverables:**
- [ ] Alembic migration: `001_governance_submissions.py`
- [ ] Alembic migration: `002_governance_rejections.py`
- [ ] Alembic migration: `003_evidence_vault_entries.py`
- [ ] Alembic migration: `004_audit_log.py`
- [ ] Alembic migration: `005_ownership_registry.py`
- [ ] Alembic migration: `006_quality_contracts.py`
- [ ] Alembic migration: `007_context_authorities.py`
- [ ] Alembic migration: `008_context_snapshots.py`
- [ ] Alembic migration: `009_contract_versions.py`
- [ ] Alembic migration: `010_contract_violations.py`
- [ ] Alembic migration: `011_ai_attestations.py`
- [ ] Alembic migration: `012_human_reviews.py`
- [ ] Alembic migration: `013_governance_exceptions.py`
- [ ] Alembic migration: `014_escalation_log.py`

**Verification:**
```bash
# Apply migrations
cd backend && alembic upgrade head

# Verify tables created
python -c "
from app.db.session import engine
from sqlalchemy import inspect
inspector = inspect(engine)
tables = inspector.get_table_names()
governance_tables = [t for t in tables if t.startswith('governance_') or t in [
    'evidence_vault_entries', 'audit_log', 'ownership_registry',
    'quality_contracts', 'context_authorities', 'context_snapshots',
    'contract_versions', 'contract_violations', 'ai_attestations',
    'human_reviews', 'escalation_log'
]]
print(f'Governance tables: {len(governance_tables)}/14')
assert len(governance_tables) >= 14, 'Missing tables!'
"
```

**Exit Criteria:**
- [ ] All 14 migrations run without error
- [ ] `alembic downgrade -1` works (rollback tested)
- [ ] Tables have correct indexes (from DATABASE-SCHEMA-DESIGN.md)
- [ ] Foreign keys enforced

---

### Day 2: SQLAlchemy Models (14 models)

**Deliverables:**
- [ ] Model: `backend/app/models/governance/submission.py`
- [ ] Model: `backend/app/models/governance/rejection.py`
- [ ] Model: `backend/app/models/governance/evidence.py`
- [ ] Model: `backend/app/models/governance/audit_log.py`
- [ ] Model: `backend/app/models/governance/ownership.py`
- [ ] Model: `backend/app/models/governance/quality_contract.py`
- [ ] Model: `backend/app/models/governance/context_authority.py`
- [ ] Model: `backend/app/models/governance/context_snapshot.py`
- [ ] Model: `backend/app/models/governance/contract_version.py`
- [ ] Model: `backend/app/models/governance/contract_violation.py`
- [ ] Model: `backend/app/models/governance/ai_attestation.py`
- [ ] Model: `backend/app/models/governance/human_review.py`
- [ ] Model: `backend/app/models/governance/governance_exception.py`
- [ ] Model: `backend/app/models/governance/escalation.py`
- [ ] Export: `backend/app/models/governance/__init__.py`

**Verification:**
```bash
# Run model tests
pytest backend/app/tests/unit/test_governance_models.py -v

# Verify relationships
python -c "
from app.models.governance import (
    GovernanceSubmission, GovernanceRejection, EvidenceVaultEntry,
    AuditLog, OwnershipRegistry, QualityContract,
    ContextAuthority, ContextSnapshot, ContractVersion,
    ContractViolation, AIAttestation, HumanReview,
    GovernanceException, EscalationLog
)
print('All 14 models imported successfully')
"
```

**Exit Criteria:**
- [ ] All 14 models defined with type hints
- [ ] Relationships work (FK cascade tested)
- [ ] Unit tests pass (TDD: RED → GREEN)
- [ ] No circular imports

---

### Day 3: Test Factories + Base Repository

**Deliverables:**
- [ ] Factory: `backend/app/tests/factories/governance_factories.py`
  - `GovernanceSubmissionFactory`
  - `GovernanceRejectionFactory`
  - `EvidenceVaultEntryFactory`
  - `AuditLogFactory`
  - `OwnershipRegistryFactory`
  - `QualityContractFactory`
  - `AIAttestationFactory`
  - `EscalationLogFactory`
- [ ] Repository: `backend/app/repositories/governance_repository.py`
  - `SubmissionRepository`
  - `RejectionRepository`
  - `EvidenceRepository`
  - `AuditLogRepository`

**Verification:**
```bash
# Test factories
pytest backend/app/tests/unit/test_governance_factories.py -v

# Test repositories
pytest backend/app/tests/unit/test_governance_repositories.py -v
```

**Exit Criteria:**
- [ ] Factories create valid objects
- [ ] Repositories perform CRUD operations
- [ ] TDD discipline maintained

---

### Day 4: SubmissionService + VibecodingService

**Deliverables:**
- [ ] Service: `backend/app/services/governance/submission_service.py`
  - `create_submission(project_id, pr_number, files_changed)`
  - `get_submission(submission_id)`
  - `list_submissions(project_id, status, page, limit)`
  - `update_submission_status(submission_id, status)`
  - `calculate_vibecoding_index(submission_id)` (calls VibecodingService)

- [ ] Service: `backend/app/services/governance/vibecoding_service.py`
  - `calculate_index(submission)` → returns index + signals breakdown
  - `_calculate_architectural_smell(submission)` → signal 1
  - `_calculate_abstraction_complexity(submission)` → signal 2
  - `_calculate_ai_dependency_ratio(submission)` → signal 3
  - `_calculate_change_surface_area(submission)` → signal 4
  - `_calculate_drift_velocity(submission, context)` → signal 5
  - `apply_max_criticality_override(submission, index)` → RED if critical path
  - `generate_explainability(index, signals)` → explainability data

**Verification:**
```bash
# Test submission service
pytest backend/app/tests/unit/test_submission_service.py -v

# Test vibecoding service
pytest backend/app/tests/unit/test_vibecoding_service.py -v
```

**Exit Criteria:**
- [ ] SubmissionService CRUD works
- [ ] VibecodingService returns 0-100 index
- [ ] MAX CRITICALITY OVERRIDE works
- [ ] Explainability data generated for index >30
- [ ] Performance: <500ms for index calculation

---

### Day 5: RoutingService + Intent Generator

**Deliverables:**
- [ ] Service: `backend/app/services/governance/routing_service.py`
  - `route_submission(submission)` → returns routing decision
  - `_determine_routing(index, critical_override)` → routing logic
  - `notify_reviewers(submission, routing)` → Slack/email notifications
  - `record_routing_decision(submission, routing)` → audit log

- [ ] Service: `backend/app/services/governance/auto_generation/intent_service.py`
  - `generate_intent(task, pr)` → returns IntentDocument
  - `_generate_with_llm(task, pr, timeout)` → Ollama qwen3:32b
  - `_generate_with_template(task, pr)` → template fallback
  - `_assess_intent_quality(content, task)` → quality score 0-1
  - `_get_minimal_placeholder()` → minimal fallback

**Verification:**
```bash
# Test routing service
pytest backend/app/tests/unit/test_routing_service.py -v

# Test intent generator (with LLM mock for unit test)
pytest backend/app/tests/unit/test_intent_service.py -v

# Integration test (real LLM)
pytest backend/app/tests/integration/test_intent_generation.py -v
```

**Exit Criteria:**
- [ ] Routing returns correct decision based on index
- [ ] Intent generation <10s (P95)
- [ ] Template fallback works when LLM fails
- [ ] Quality score >0.7 for LLM output

---

### Day 6: WARNING Mode + Feature Flags

**Deliverables:**
- [ ] Feature flags: `backend/app/config/governance_flags.py`
  - `GOVERNANCE_MODE` (OFF | WARNING | SOFT | FULL)
  - `VIBECODING_ENABLED`
  - `AUTO_GENERATION_ENABLED`
  - `KILL_SWITCH_ENABLED`

- [ ] Middleware: `backend/app/middleware/governance_middleware.py`
  - `GovernanceMiddleware` class
  - Log violations in WARNING mode
  - Block violations in SOFT/FULL mode

- [ ] API: `backend/app/api/v1/governance.py`
  - `POST /api/v1/governance/submissions` → create submission
  - `GET /api/v1/governance/submissions/{id}` → get submission
  - `GET /api/v1/governance/submissions/{id}/index` → get vibecoding index
  - `POST /api/v1/governance/auto-generate/intent` → generate intent

**Verification:**
```bash
# Test API endpoints
pytest backend/app/tests/integration/test_governance_api.py -v

# Test WARNING mode (no blocking)
pytest backend/app/tests/integration/test_warning_mode.py -v
```

**Exit Criteria:**
- [ ] API endpoints work
- [ ] WARNING mode logs but doesn't block
- [ ] Feature flags toggle behavior

---

### Day 7: Integration Testing + Documentation

**Deliverables:**
- [ ] Integration tests: `backend/app/tests/integration/test_governance_flow.py`
  - Test: Submit PR → Calculate index → Route → Auto-generate intent
  - Test: Critical path → MAX CRITICALITY OVERRIDE → Red routing
  - Test: LLM timeout → Template fallback → Success

- [ ] Documentation:
  - Update README.md with governance endpoints
  - Create `docs/governance-v1/API-REFERENCE.md`
  - Update CLAUDE.md with Sprint 108 completion

**Verification:**
```bash
# Full integration test
pytest backend/app/tests/integration/test_governance_*.py -v

# Coverage report
pytest --cov=backend/app/services/governance --cov-report=html
```

**Exit Criteria:**
- [ ] All integration tests pass
- [ ] Code coverage >80% for governance services
- [ ] Documentation complete
- [ ] Ready for Sprint 109

---

## Technical Specifications

### 14-Table Schema Summary

```yaml
Core Tables (6):
  1. governance_submissions    # PR submission tracking
  2. governance_rejections     # Rejection reasons + feedback
  3. evidence_vault_entries    # Evidence metadata (MinIO S3)
  4. audit_log                 # Immutable audit trail (7-year retention)
  5. ownership_registry        # File ownership annotations
  6. quality_contracts         # Policy-as-code rules

Extended Tables (8):
  7. context_authorities       # Context linkage validation
  8. context_snapshots         # Historical context state
  9. contract_versions         # Policy versioning
  10. contract_violations      # Policy violation details
  11. ai_attestations          # AI code attestations
  12. human_reviews            # Human review tracking
  13. governance_exceptions    # Break glass / exceptions
  14. escalation_log           # CEO escalation tracking
```

### Vibecoding Index Formula

```python
vibecoding_index = (
    architectural_smell * 0.25 +      # God class, shotgun surgery
    abstraction_complexity * 0.15 +   # Over-engineering
    ai_dependency_ratio * 0.20 +      # AI code without review
    change_surface_area * 0.20 +      # Files/modules touched
    drift_velocity * 0.20             # Codebase divergence
)

# Routing thresholds
GREEN  = 0-30   → auto_approve
YELLOW = 31-60  → tech_lead_review
ORANGE = 61-80  → ceo_should_review
RED    = 81-100 → ceo_must_review
```

### Auto-Generation Latency Targets

| Component | Primary (LLM) | Fallback (Template) | P95 Target |
|-----------|---------------|---------------------|------------|
| Intent Statement | 5-8s | <150ms | <10s |
| Ownership Annotation | <500ms | <50ms | <2s |
| Context Attachment | <2s | <50ms | <5s |
| AI Code Attestation | <500ms | <50ms | <3s |

---

## Risk Assessment

| Risk | Severity | Mitigation |
|------|----------|------------|
| LLM latency >10s | Medium | Template fallback guaranteed |
| Database migration fails | Low | Rollback tested (Day 1) |
| Model relationships broken | Low | TDD catches early |
| Vibecoding index inaccurate | Medium | CEO calibration (Sprint 109) |

---

## Dependencies

### External Dependencies

| Dependency | Status | Sprint 108 Use |
|------------|--------|----------------|
| Ollama qwen3:32b | ⏳ Verify | Intent generation |
| PostgreSQL 15.5 | ✅ Running | Database |
| Redis 7.2 | ✅ Running | Caching |
| MinIO | ✅ Running | Evidence storage |

### Internal Dependencies

| Dependency | Status | Sprint 108 Use |
|------------|--------|----------------|
| Sprint 107 (TDD Foundation) | ✅ Complete | Factories, test patterns |
| Phase 0 (Technical Deliverables) | ✅ Complete | Specifications |
| Policy Contracts | ✅ Signed | Constraints |

---

## Sprint 109 Preview

**Goal**: Complete Vibecoding Index + Full Auto-Generation + CEO Dashboard API

**Scope**:
- Remaining 3 auto-generators (Ownership, Context, Attestation)
- Full 5-signal Vibecoding Index calculation
- CEO Dashboard API endpoints
- SOFT enforcement mode
- Prometheus metrics (first 20)

---

## Approval

**CTO Review**: ⏳ PENDING
**Tech Lead Review**: ⏳ PENDING
**Sprint Ready**: ⏳ PENDING

**Prerequisites Checklist:**
- [ ] Sprint 107 complete (test infrastructure)
- [ ] Phase 0 deliverables reviewed
- [ ] Ollama qwen3:32b operational
- [ ] Database connection tested

---

## Appendix: File Structure

```
backend/app/
├── models/governance/
│   ├── __init__.py
│   ├── submission.py
│   ├── rejection.py
│   ├── evidence.py
│   ├── audit_log.py
│   ├── ownership.py
│   ├── quality_contract.py
│   ├── context_authority.py
│   ├── context_snapshot.py
│   ├── contract_version.py
│   ├── contract_violation.py
│   ├── ai_attestation.py
│   ├── human_review.py
│   ├── governance_exception.py
│   └── escalation.py
├── repositories/
│   └── governance_repository.py
├── services/governance/
│   ├── __init__.py
│   ├── submission_service.py
│   ├── vibecoding_service.py
│   ├── routing_service.py
│   └── auto_generation/
│       ├── __init__.py
│       ├── intent_service.py
│       ├── ownership_service.py (Sprint 109)
│       ├── context_service.py (Sprint 109)
│       └── attestation_service.py (Sprint 109)
├── api/v1/
│   └── governance.py
├── config/
│   └── governance_flags.py
└── middleware/
    └── governance_middleware.py

alembic/versions/
├── 001_governance_submissions.py
├── 002_governance_rejections.py
├── 003_evidence_vault_entries.py
├── 004_audit_log.py
├── 005_ownership_registry.py
├── 006_quality_contracts.py
├── 007_context_authorities.py
├── 008_context_snapshots.py
├── 009_contract_versions.py
├── 010_contract_violations.py
├── 011_ai_attestations.py
├── 012_human_reviews.py
├── 013_governance_exceptions.py
└── 014_escalation_log.py
```

---

**Document Status**: ✅ PLANNING COMPLETE
**Next Action**: CTO Approval → Sprint Execution
**Sprint 108 Starts**: After Sprint 107 completion
