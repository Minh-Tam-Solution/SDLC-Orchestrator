# Governance System Implementation Specification

---
spec_id: SPEC-0001
version: 1.0.0
title: Governance System Implementation Specification
status: APPROVED
tier: PROFESSIONAL
stage: "04"
category: technical
created_date: 2026-01-28
last_updated: 2026-01-28
owner: Backend Lead
reviewers:
  - QA Lead
  - Tech Lead
approver: CTO
related_adrs:
  - ADR-041-Framework-6.0-Governance-System
related_specs: []
framework_version: 6.0.5
tags:
  - governance
  - vibecoding-index
  - auto-generation
  - quality-gates
  - ceo-dashboard
---

## 1. Overview

### 1.1 Purpose

This specification defines the technical implementation of the SDLC Framework 6.0 Governance System, providing automated governance enforcement with minimal developer friction.

### 1.2 Context

**Business Problem**: CEO spends 40 hours/week reviewing PRs and technical decisions. Need to reduce to <10 hours/week while maintaining quality.

**Solution**: Automated governance system with 4 enforcement modes (OFF/WARNING/SOFT/FULL), vibecoding index calculation (0-100), and intelligent routing that auto-approves safe PRs while escalating risky ones to CEO review.

### 1.3 Goals

- **Primary**: Reduce CEO review time from 40h → 10h/week (-75%)
- **Secondary**: Maintain code quality (95%+ pass rate)
- **Tertiary**: Developer friction <5 min per PR (down from 30 min)

### 1.4 Scope

| In Scope | Out of Scope |
|----------|--------------|
| 4 enforcement modes (OFF/WARNING/SOFT/FULL) | AI code review (separate spec) |
| Vibecoding Index (5 signals) | Performance profiling |
| Auto-generation (intent/ownership/context) | Security penetration testing |
| CEO Dashboard with metrics | External integrations (Jira/Linear) |
| Kill switch mechanism | Mobile app |

---

## 2. Context & Background

### 2.1 Problem Statement

**Current State**:
- CEO manually reviews 100% of PRs (40h/week)
- Developers wait 24-48h for approval
- 60% of PRs could be auto-approved safely
- Missing context (ADRs/specs) causes 30% rework

**Desired State**:
- CEO reviews only 20% of PRs (high-risk only)
- Auto-approval for 80% of PRs (<5 min)
- Zero missing context (auto-attached)
- <5% false positive rate

### 2.2 Stakeholders

| Role | Needs | Success Criteria |
|------|-------|------------------|
| CEO | Reduce review time, maintain quality | 10h/week, 95%+ quality |
| Developers | Fast approvals, clear guidance | <5 min friction, actionable errors |
| Tech Lead | Enforce architecture rules | Zero violations in production |
| QA Lead | Automated quality gates | 95%+ test coverage |

### 2.3 Related Documents

- [ADR-041: Framework 6.0 Governance System Design](../03-ADRs/ADR-041-Framework-6.0-Governance-System.md)
- [SDLC 6.1.0 Section 7: Quality Assurance System](../../../SDLC-Enterprise-Framework/00-Core-Pillars/07-Quality-Assurance-System.md)
- Pre-Phase 0 Documents: `docs/governance-v1/`

---

## 3. Requirements

### 3.1 Functional Requirements

#### FR-01: Governance Mode Management

**GIVEN** the system is operational  
**WHEN** an admin changes governance mode (OFF/WARNING/SOFT/FULL)  
**THEN** the system SHALL apply the new mode within 30 seconds  
**AND** the system SHALL log the mode change with timestamp, user, and reason  
**AND** the system SHALL notify all active developers via Slack

**Tier Requirements**:
- LITE: Not applicable (no governance)
- STANDARD: WARNING + SOFT modes only
- PROFESSIONAL: All modes including FULL
- ENTERPRISE: All modes + custom rules

#### FR-02: Vibecoding Index Calculation

**GIVEN** a code submission (PR) is created  
**WHEN** the governance system evaluates the PR  
**THEN** the system SHALL calculate a Vibecoding Index (0-100) from 5 signals  
**AND** the system SHALL return the result within 500ms (p95)  
**AND** the system SHALL classify the result into zones: Green (0-30), Yellow (31-60), Orange (61-80), Red (81-100)

**Tier Requirements**:
- LITE: Not applicable
- STANDARD: 3 signals (architectural smell, change surface, drift velocity)
- PROFESSIONAL: All 5 signals
- ENTERPRISE: All 5 signals + custom signals

**Signals**:
1. **Architectural Smell** (0-100): Circular imports, layer violations, naming issues
2. **Abstraction Complexity** (0-100): Cyclomatic complexity, nesting depth
3. **AI Dependency Ratio** (0-100): % of code AI-generated without human review
4. **Change Surface Area** (0-100): Files changed, lines changed, modules affected
5. **Drift Velocity** (0-100): Rate of change from design spec

#### FR-03: Auto-Generation Service

**GIVEN** a developer creates a PR without intent document  
**WHEN** the PR is submitted to the governance system  
**THEN** the system SHALL attempt to generate an intent document using LLM  
**AND** the system SHALL fallback to template if LLM fails  
**AND** the system SHALL complete generation within 15 seconds

**Tier Requirements**:
- LITE: Template-only (no LLM)
- STANDARD: LLM with template fallback
- PROFESSIONAL: LLM + ownership suggestion + context attachment
- ENTERPRISE: All features + custom generators

**Auto-Generation Types**:
1. Intent Document: Generated from task description + PR changes
2. Ownership Suggestion: Based on CODEOWNERS, git blame, directory patterns
3. Context Attachment: Auto-link related ADRs, specs, design docs
4. Attestation Pre-fill: Pre-populate AI session data (model, time, modifications)

#### FR-04: Stage Gating Service

**GIVEN** a project is in Stage 02 (Design)  
**WHEN** a developer submits a PR with implementation code  
**THEN** the system SHALL reject the PR with stage violation error  
**AND** the system SHALL provide actionable fix suggestion with CLI command  
**AND** the system SHALL allow override with Tech Lead approval

**Tier Requirements**:
- LITE: Not applicable
- STANDARD: Basic stage validation (no code before design)
- PROFESSIONAL: Full stage gating with custom rules
- ENTERPRISE: Full + custom workflows

#### FR-05: Context Authority Validation

**GIVEN** a code submission introduces new modules or features  
**WHEN** the governance system validates context linkage  
**THEN** the system SHALL check for ADR linkage, design doc reference, AGENTS.md freshness, module annotation  
**AND** the system SHALL reject if any context is missing  
**AND** the system SHALL allow exemption for minor changes (docs-only, test-only)

**Tier Requirements**:
- LITE: Not applicable
- STANDARD: ADR linkage only
- PROFESSIONAL: Full context validation (ADR + spec + AGENTS.md)
- ENTERPRISE: Full + semantic context validation (future)

#### FR-06: CEO Dashboard

**GIVEN** the CEO accesses the governance dashboard  
**WHEN** the dashboard loads  
**THEN** the system SHALL display:
- Time saved this week (hours)
- Auto-approval rate (%)
- Vibecoding Index distribution (Green/Yellow/Orange/Red)
- Pending decisions queue (top 10)
- Weekly summary table
- System health indicators

**Tier Requirements**:
- LITE: Not applicable
- STANDARD: Basic metrics (time saved, approval rate)
- PROFESSIONAL: Full dashboard with all metrics
- ENTERPRISE: Full + custom dashboards per department

#### FR-07: Kill Switch Mechanism

**GIVEN** the governance system is operational in FULL mode  
**WHEN** any kill switch criteria is met:
- Rejection rate >80% (developers blocked)
- API latency p95 >500ms (system slow)
- False positive rate >20% (incorrect rejections)
**THEN** the system SHALL automatically rollback to WARNING mode  
**AND** the system SHALL send emergency alert to CTO + CEO  
**AND** the system SHALL log the incident with full context

**Tier Requirements**:
- LITE: Not applicable
- STANDARD: Manual rollback only
- PROFESSIONAL: Automatic kill switch
- ENTERPRISE: Automatic + custom criteria

### 3.2 Non-Functional Requirements

#### NFR-01: Performance

**GIVEN** the governance system is processing PRs  
**WHEN** performance metrics are measured  
**THEN** the system SHALL meet:
- Vibecoding Index calculation: <500ms (p95)
- CEO Dashboard load time: <1s (p95)
- API latency: <100ms (p95)
- Auto-generation (intent): <15s (p95)
- Stage gating check: <200ms (p95)

#### NFR-02: Availability

**GIVEN** the governance system is deployed  
**WHEN** uptime is measured over 30 days  
**THEN** the system SHALL achieve 99.5% uptime (excluding planned maintenance)

#### NFR-03: Security

**GIVEN** sensitive governance data (decisions, overrides)  
**WHEN** data is accessed  
**THEN** the system SHALL enforce role-based access control (RBAC)  
**AND** the system SHALL log all access in immutable audit log  
**AND** the system SHALL encrypt sensitive fields at rest

#### NFR-04: Scalability

**GIVEN** the system handles increasing PR volume  
**WHEN** PRs per day exceed 500  
**THEN** the system SHALL maintain <500ms p95 latency for vibecoding calculation  
**AND** the system SHALL scale horizontally (add workers)

---

## 4. Design Decisions

### 4.1 Vibecoding Index Algorithm

**Decision**: Use weighted composite score (0-100) from 5 signals  
**Rationale**: Single score easier for CEO dashboard than 5 separate scores  
**Trade-offs**: Loss of signal granularity, but gains simplicity  
**Alternatives Considered**:
- Option B: Traffic light (Red/Yellow/Green) only → Too coarse
- Option C: ML model → Too complex, not interpretable

**Signal Weights** (Total = 1.0):
- Architectural Smell: 0.20
- Abstraction Complexity: 0.20
- AI Dependency Ratio: 0.20
- Change Surface Area: 0.25
- Drift Velocity: 0.15

### 4.2 Auto-Generation Strategy

**Decision**: LLM with deterministic fallback chain (Ollama → Template → Placeholder)  
**Rationale**: Maximize automation while ensuring 100% availability  
**Trade-offs**: Ollama may be slow (15s), but cost is $0 vs Claude ($0.015/1K tokens)

### 4.3 Context Authority V1 Scope

**Decision**: Metadata validation only (NOT semantic analysis)  
**Rationale**: Semantic validation requires LLM embeddings (expensive, slow)  
**Future Work**: V2 will add semantic context (RAG-based)

### 4.4 Database Schema Design

**Decision**: Separate tables for submissions, rejections, evidence, audit log  
**Rationale**: Query performance + immutable audit trail  
**Trade-offs**: More complex joins, but better compliance

---

## 5. Technical Specification

### 5.1 System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                      FRONTEND LAYER                             │
├─────────────────────────────────────────────────────────────────┤
│  CEO Dashboard │ Auto-Gen UI │ Kill Switch Admin │ Governance UI│
└────────────────────────────────┬────────────────────────────────┘
                                 │ REST API
                                 ▼
┌─────────────────────────────────────────────────────────────────┐
│                      BACKEND SERVICES                           │
├─────────────────────────────────────────────────────────────────┤
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐ │
│  │ GovernanceMode  │  │ AutoGeneration  │  │ SignalsEngine   │ │
│  │ Service         │  │ Service         │  │ (Vibecoding)    │ │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘ │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐ │
│  │ StageGating     │  │ ContextAuthority│  │ CEODashboard    │ │
│  │ Service         │  │ Service         │  │ Service         │ │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘ │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐ │
│  │ MetricsCollector│  │ GrafanaDashboard│  │ KillSwitch      │ │
│  │ Service         │  │ Service         │  │ Service         │ │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘ │
└────────────────────────────────┬────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────┐
│                      INFRASTRUCTURE                             │
├─────────────────────────────────────────────────────────────────┤
│  PostgreSQL │ Redis │ MinIO │ OPA │ Ollama │ GitHub │ Slack   │
└─────────────────────────────────────────────────────────────────┘
```

### 5.2 Service Specifications

#### 5.2.1 GovernanceModeService

**Location**: `backend/app/services/governance/mode_service.py`

**Interface**:
```python
class GovernanceMode(Enum):
    OFF = "OFF"
    WARNING = "WARNING"
    SOFT = "SOFT"
    FULL = "FULL"

class GovernanceModeService:
    async def get_mode(self) -> GovernanceMode
    async def set_mode(self, mode: GovernanceMode, changed_by: str) -> bool
    async def check_kill_switch_criteria(self) -> KillSwitchResult
    async def trigger_rollback(self, reason: str, severity: str) -> bool
    async def get_mode_history(self, limit: int = 10) -> List[ModeChange]
```

#### 5.2.2 SignalsEngine (Vibecoding Index)

**Location**: `backend/app/services/governance/signals_engine.py`

**Interface**:
```python
class GovernanceSignalsEngine:
    async def calculate_vibecoding_index(
        self,
        submission: CodeSubmission,
        context: ProjectContext
    ) -> VibecodingIndex:
        """
        Calculate composite vibecoding index from 5 signals.
        Returns: 0-100 score with zone classification
        """

    async def _calculate_architectural_smell(self, submission) -> float
    async def _calculate_abstraction_complexity(self, submission) -> float
    async def _calculate_ai_dependency_ratio(self, submission) -> float
    async def _calculate_change_surface_area(self, submission) -> float
    async def _calculate_drift_velocity(self, submission, context) -> float
```

#### 5.2.3 AutoGenerationService

**Location**: `backend/app/services/governance/auto_generator.py`

**Interface**:
```python
class AutoGenerationService:
    async def generate_intent_skeleton(self, task: Task) -> IntentDocument
    async def suggest_ownership(self, file_path: str, repo: Repository) -> OwnershipSuggestion
    async def auto_attach_context(self, pr: PullRequest) -> PRContextAttachment
    async def pre_fill_attestation(self, ai_session: AISession) -> AttestationForm
```

#### 5.2.4 CEODashboardService

**Location**: `backend/app/services/governance/ceo_dashboard.py`

**Interface**:
```python
class CEODashboardService:
    async def get_summary(self, time_range: TimeRange) -> CEOSummary
    async def get_time_saved(self, time_range: TimeRange) -> TimeSavedMetrics
    async def get_routing_breakdown(self, time_range: TimeRange) -> RoutingBreakdown
    async def get_pending_decisions(self, limit: int) -> List[PendingDecision]
    async def resolve_decision(self, id: str, decision: str, reviewer: str) -> bool
    async def record_override(self, id: str, reason: str, approver: str) -> bool
```

### 5.3 Database Schema

**Alembic Migration**: `backend/alembic/versions/XXX_create_governance_tables.py`

**Tables**:
1. `governance_submissions`: PR submissions with vibecoding scores
2. `governance_rejections`: Rejected PRs with reasons
3. `governance_evidence`: Supporting evidence (ADR links, test results)
4. `governance_audit_log`: Immutable audit trail
5. `governance_ownership`: File ownership mappings
6. `context_authorities`: ADR/spec linkages
7. `governance_contracts`: Validation rules per project
8. `ai_attestations`: AI usage tracking
9. `governance_exceptions`: Approved exemptions
10. `escalation_log`: CEO decision records

### 5.4 API Specification

**Base Path**: `/api/v1/governance`

**Key Endpoints**:

```yaml
/mode:
  get: Get current governance mode
  post: Set governance mode (admin only)

/ceo/summary:
  get: CEO dashboard summary (time_range: day/week/month)

/ceo/pending-decisions:
  get: Pending decisions queue

/submissions:
  post: Submit PR for governance check
  get: List submissions

/vibecoding/{submission_id}:
  get: Get vibecoding index details

/auto-generate/intent:
  post: Generate intent document from task

/auto-generate/ownership:
  post: Suggest file ownership
```

### 5.5 Frontend Components

**CEO Dashboard** (`frontend/src/app/app/ceo-dashboard/page.tsx`):
- StatCard: Key metrics display
- VibecodingGauge: 0-100 gauge with color zones
- PendingDecisionCard: Decision queue
- SystemHealthCard: Health indicators
- TimeSavedChart: Time saved trend
- WeeklySummaryTable: Weekly metrics

**Kill Switch Admin** (`frontend/src/app/admin/governance/kill-switch/`):
- GovernanceModeCard: Current mode display
- ModeSwitcher: Mode toggle
- RollbackCriteriaCard: Threshold display
- BreakGlassButton: Emergency bypass
- KillSwitchAuditLog: Mode change history

---

## 6. Acceptance Criteria

| ID | Criterion | Test Method | Status |
|----|-----------|-------------|--------|
| AC-01 | Governance mode changes apply within 30s | Integration test | ✅ PASS |
| AC-02 | Vibecoding index calculated <500ms (p95) | pytest-benchmark | ✅ PASS |
| AC-03 | Auto-generation completes <15s (p95) | Integration test | ✅ PASS |
| AC-04 | CEO dashboard loads <1s | Lighthouse | ✅ PASS |
| AC-05 | Kill switch activates automatically when criteria met | E2E test | ✅ PASS |
| AC-06 | All mode changes logged in audit log | Unit test | ✅ PASS |
| AC-07 | 521 unit tests passing | pytest | ✅ 521/521 |
| AC-08 | 50+ integration tests passing | pytest | ✅ 50/50 |
| AC-09 | Stage gating blocks out-of-order PRs | Integration test | ✅ PASS |
| AC-10 | Context validation rejects orphan code | Unit test | ✅ PASS |

**Test Summary**:
- Unit Tests: 521/521 passing (100%)
- Integration Tests: 50/50 passing (100%)
- E2E Tests: 6/6 planned scenarios
- Performance: All targets met (<500ms, <1s, <15s)

---

## 7. Spec Delta

### 7.1 Changes from Previous Version

This is the initial version (1.0.0) migrated from SDLC 6.1.0 format to Framework 6.0.5 format.

**Migration Changes**:
- Added YAML frontmatter with spec_id, tier, stage, relationships
- Converted requirements to BDD format (GIVEN-WHEN-THEN)
- Added tier-specific requirements (LITE/STANDARD/PROFESSIONAL/ENTERPRISE)
- Added acceptance criteria table with test methods
- Reorganized content to match 9-section Framework 6.0.5 template

**Content Updates**:
- None (content preserved from original spec)

### 7.2 Version History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0.0 | 2026-01-28 | Backend Lead | Initial version (migrated to Framework 6.0.5) |

---

## 8. Dependencies

### 8.1 Upstream Dependencies

| Dependency | Type | Impact if Changed |
|------------|------|-------------------|
| ADR-041 | Architecture Decision | Must update governance design |
| PostgreSQL | Infrastructure | Database schema migration required |
| Redis | Infrastructure | Mode state management affected |
| Ollama | AI Service | Auto-generation fallback required |

### 8.2 Downstream Dependencies

| Dependent | Type | Impact |
|-----------|------|--------|
| Sprint 114 WARNING mode | Implementation | Uses SignalsEngine + Dashboard |
| Sprint 115 SOFT mode | Implementation | Uses StageGating + ContextAuthority |
| Sprint 116 FULL mode | Implementation | Uses KillSwitch + CEO Dashboard |

### 8.3 Related Specifications

- Quality-Gates-Codegen-Specification.md (SPEC-0002): Uses governance pipeline for validation
- App Builder Integration (ADR-040): Uses governance for generated code approval

---

## 9. Appendix

### 9.1 Performance Benchmarks

| Operation | Target | Actual | Status |
|-----------|--------|--------|--------|
| Vibecoding index | <500ms | 320ms | ✅ |
| CEO dashboard | <1s | 780ms | ✅ |
| API latency p95 | <100ms | 85ms | ✅ |
| Auto-generation | <15s | 12s | ✅ |
| Stage gating | <200ms | 150ms | ✅ |

### 9.2 Security Considerations

**Access Control**:

| Role | CEO Dashboard | Kill Switch | Auto-Gen |
|------|---------------|-------------|----------|
| CEO | Full access | View + Emergency | View |
| CTO | View | Full access | View |
| Admin | View | View | View |
| Developer | - | - | Use |

**Audit Requirements**:
- All mode changes logged (timestamp, user, reason)
- All decisions logged (approve/reject)
- Break glass events → immediate CEO/CTO notification
- Audit logs immutable (append-only)

### 9.3 Monitoring & Alerting

**Prometheus Metrics**:
```python
governance_submissions_total{status="pending|approved|rejected"}
governance_vibecoding_index{category="green|yellow|orange|red"}
governance_time_saved_minutes_total
governance_auto_generation_usage{type="intent|ownership|context"}
governance_kill_switch_activations_total
governance_api_latency_seconds{endpoint, method}
```

**Grafana Dashboards**:
- CEO Dashboard (ceo-dashboard): Executive summary
- Tech Dashboard (tech-dashboard): Developer experience
- Ops Dashboard (ops-dashboard): System health

### 9.4 Rollout Plan

**Phase 1: WARNING Mode (Sprint 114)**
- Duration: 5 days (Feb 3-7)
- Goal: Establish baseline metrics
- Actions: Enable on Orchestrator repo, collect data
- Success: 100 PRs evaluated, baseline metrics captured

**Phase 2: SOFT Enforcement (Sprint 115)**
- Duration: 5 days (Feb 10-14)
- Goal: Block critical violations
- Actions: Enable blocking for missing ownership/intent
- Success: CEO time reduced 40h → 25h (-37.5%)

**Phase 3: FULL Enforcement (Sprint 116)**
- Duration: 5 days (Feb 17-21)
- Goal: All violations block
- Actions: Only Green PRs auto-approved
- Success: CEO time reduced 40h → 10h (-75%) ← **CRITICAL MILESTONE**

### 9.5 Glossary

- **Vibecoding Index**: Composite score (0-100) measuring PR risk
- **Green Zone**: VI 0-30 (safe, auto-approve)
- **Yellow Zone**: VI 31-60 (caution, auto-approve with logging)
- **Orange Zone**: VI 61-80 (review recommended, human approval)
- **Red Zone**: VI 81-100 (must review, CEO escalation)
- **Kill Switch**: Automatic rollback mechanism when system fails
- **Break Glass**: Emergency bypass for production incidents

---

## Document Control

**Change Log**:
- 2026-01-28: Migrated to Framework 6.0.5 format (Backend Lead)

**Approval**:
- ✅ Backend Lead: Approved
- ✅ QA Lead: Approved
- ✅ Tech Lead: Approved
- ✅ CTO: Approved (Jan 28, 2026)
