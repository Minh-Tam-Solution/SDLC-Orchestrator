# Governance System Implementation Specification

**Version**: 1.0.0
**Status**: APPROVED
**Date**: January 28, 2026
**Author**: Backend Lead
**ADR Reference**: ADR-041
**Framework**: SDLC 6.1.0

---

## 1. Overview

This document specifies the technical implementation details for the SDLC Framework 6.0 Governance System as defined in ADR-041.

---

## 2. System Architecture

### 2.1 Component Diagram

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

### 2.2 Service Dependencies

| Service | Dependencies | Purpose |
|---------|--------------|---------|
| GovernanceModeService | Redis | Mode state management |
| AutoGenerationService | Ollama, PostgreSQL | AI-powered generation |
| SignalsEngine | PostgreSQL | Vibecoding index calculation |
| StageGatingService | PostgreSQL | PR validation against stage |
| ContextAuthorityService | PostgreSQL | ADR/spec linkage validation |
| CEODashboardService | PostgreSQL, Redis | Dashboard metrics |
| MetricsCollector | Prometheus | System metrics |
| GrafanaDashboardService | Grafana API | Dashboard provisioning |

---

## 3. Backend Services Specification

### 3.1 GovernanceModeService

**Location**: `backend/app/services/governance/mode_service.py`

```python
class GovernanceMode(Enum):
    OFF = "OFF"
    WARNING = "WARNING"
    SOFT = "SOFT"
    FULL = "FULL"

class GovernanceModeService:
    """
    Manages governance enforcement mode with kill switch capability.
    """

    async def get_mode(self) -> GovernanceMode
    async def set_mode(self, mode: GovernanceMode, changed_by: str) -> bool
    async def check_kill_switch_criteria(self) -> KillSwitchResult
    async def trigger_rollback(self, reason: str, severity: str) -> bool
    async def get_mode_history(self, limit: int = 10) -> List[ModeChange]
```

### 3.2 AutoGenerationService

**Location**: `backend/app/services/governance/auto_generator.py`

```python
class AutoGenerationService:
    """
    Generate compliance artifacts automatically.
    Goal: Reduce developer friction from 30 min → <5 min per PR.
    """

    async def generate_intent_skeleton(
        self,
        task: Task
    ) -> IntentDocument:
        """
        Generate intent document from task description using LLM.

        Fallback chain: Ollama → Template → Minimal Placeholder
        """

    async def suggest_ownership(
        self,
        file_path: str,
        repo: Repository
    ) -> OwnershipSuggestion:
        """
        Suggest file owner based on:
        1. Directory ownership patterns
        2. Git blame (most recent committer)
        3. CODEOWNERS file
        4. Task creator
        """

    async def auto_attach_context(
        self,
        pr: PullRequest
    ) -> PRContextAttachment:
        """
        Auto-attach ADRs, specs, and design docs to PR description.
        """

    async def pre_fill_attestation(
        self,
        ai_session: AISession
    ) -> AttestationForm:
        """
        Pre-fill attestation form with AI session data.
        Human confirms: Review time, modifications, understanding.
        """
```

### 3.3 SignalsEngine (Vibecoding Index)

**Location**: `backend/app/services/governance/signals_engine.py`

```python
class GovernanceSignalsEngine:
    """
    Calculate non-blocking governance signals.
    Output: Vibecoding Index (0-100) for CEO dashboard.
    """

    async def calculate_vibecoding_index(
        self,
        submission: CodeSubmission,
        context: ProjectContext
    ) -> VibecodingIndex:
        """
        Calculate composite vibecoding index from 5 signals.

        Returns: 0-100 score
        - 0-30: Green (safe)
        - 31-60: Yellow (caution)
        - 61-80: Orange (review recommended)
        - 81-100: Red (must review)
        """

    async def _calculate_architectural_smell(self, submission) -> float
    async def _calculate_abstraction_complexity(self, submission) -> float
    async def _calculate_ai_dependency_ratio(self, submission) -> float
    async def _calculate_change_surface_area(self, submission) -> float
    async def _calculate_drift_velocity(self, submission, context) -> float
```

### 3.4 StageGatingService

**Location**: `backend/app/services/governance/stage_gating.py`

```python
class StageGatingService:
    """
    Validate PRs against current project stage.
    Prevents: Working ahead of design, skipping stages.
    """

    async def validate_pr_against_stage(
        self,
        pr: PullRequest,
        project: Project
    ) -> StageGatingResult:
        """
        Check if PR is allowed in current project stage.
        Returns: Pass/Fail + violations
        """

    def _suggest_fix(self, violations: List[StageViolation]) -> str:
        """
        Generate actionable fix suggestion with CLI commands.
        """
```

### 3.5 ContextAuthorityService

**Location**: `backend/app/services/governance/context_authority.py`

```python
class ContextAuthorityEngineV1:
    """
    V1: Metadata & Linkage validation only (NOT semantic).
    Rule: "Orphan Code = Rejected Code"
    """

    async def validate_context(
        self,
        submission: CodeSubmission
    ) -> ContextValidationResult:
        """
        Check if code has proper context linkage.

        Checks:
        1. ADR Linkage - Module references ADR
        2. Design Doc Reference - New features have spec
        3. AGENTS.md Freshness - Updated within 7 days
        4. Module Annotation Consistency - Header matches directory
        """
```

### 3.6 CEODashboardService

**Location**: `backend/app/services/governance/ceo_dashboard.py`

```python
class CEODashboardService:
    """
    CEO Dashboard metrics and decision management.
    """

    async def get_summary(self, time_range: TimeRange) -> CEOSummary
    async def get_time_saved(self, time_range: TimeRange) -> TimeSavedMetrics
    async def get_routing_breakdown(self, time_range: TimeRange) -> RoutingBreakdown
    async def get_pending_decisions(self, limit: int) -> List[PendingDecision]
    async def get_weekly_summary(self, weeks: int) -> WeeklySummary
    async def get_time_saved_trend(self, days: int) -> List[TimeSavedPoint]
    async def get_vibecoding_trend(self, days: int) -> List[VibecodingPoint]
    async def get_top_rejections(self, limit: int) -> List[RejectionReason]
    async def get_overrides(self, limit: int) -> List[OverrideRecord]
    async def get_system_health(self) -> SystemHealth
    async def resolve_decision(self, id: str, decision: str, reviewer: str) -> bool
    async def record_override(self, id: str, reason: str, approver: str) -> bool
```

---

## 4. Database Schema

### 4.1 Alembic Migration

**Location**: `backend/alembic/versions/XXX_create_governance_tables.py`

```python
def upgrade():
    # Core Governance Tables
    op.create_table('governance_submissions', ...)
    op.create_table('governance_rejections', ...)
    op.create_table('governance_evidence', ...)
    op.create_table('governance_audit_log', ...)

    # Ownership & Context Tables
    op.create_table('governance_ownership', ...)
    op.create_table('context_authorities', ...)
    op.create_table('context_snapshots', ...)

    # Contracts & Validation Tables
    op.create_table('governance_contracts', ...)
    op.create_table('contract_versions', ...)
    op.create_table('contract_violations', ...)

    # AI & Human Review Tables
    op.create_table('ai_attestations', ...)
    op.create_table('human_reviews', ...)

    # Exceptions & Escalation Tables
    op.create_table('governance_exceptions', ...)
    op.create_table('escalation_log', ...)
```

---

## 5. Frontend Components

### 5.1 CEO Dashboard

**Location**: `frontend/src/app/app/ceo-dashboard/page.tsx`

| Component | Purpose |
|-----------|---------|
| StatCard | Display key metrics (time saved, auto-approval rate) |
| VibecodingGauge | 0-100 gauge with color zones |
| PendingDecisionCard | List of pending decisions |
| SystemHealthCard | System health indicators |
| TimeSavedChart | Time saved trend chart |
| WeeklySummaryTable | Weekly metrics table |

### 5.2 Auto-Generation UI

**Location**: `frontend/src/app/app/governance/auto-generation/`

| Component | Purpose |
|-----------|---------|
| IntentGeneratorCard | Generate intent documents |
| OwnershipSuggestionsCard | Accept ownership suggestions |
| ContextAttachmentsCard | Review auto-attached context |
| AttestationFormCard | Complete AI attestation |

### 5.3 Kill Switch Admin

**Location**: `frontend/src/app/admin/governance/kill-switch/`

| Component | Purpose |
|-----------|---------|
| GovernanceModeCard | Display current mode |
| ModeSwitcher | Toggle governance mode |
| RollbackCriteriaCard | Show rollback thresholds |
| BreakGlassButton | Emergency bypass button |
| KillSwitchAuditLog | Mode change history |

---

## 6. API Specification

### 6.1 CEO Dashboard Endpoints

```yaml
openapi: 3.0.0
paths:
  /api/v1/governance/ceo/summary:
    get:
      summary: Get CEO dashboard summary
      parameters:
        - name: time_range
          in: query
          schema:
            type: string
            enum: [day, week, month]
      responses:
        200:
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/CEOSummary'

  /api/v1/governance/ceo/pending-decisions:
    get:
      summary: Get pending decisions queue
      parameters:
        - name: limit
          in: query
          schema:
            type: integer
            default: 10
      responses:
        200:
          content:
            application/json:
              schema:
                type: array
                items:
                  $ref: '#/components/schemas/PendingDecision'
```

### 6.2 Governance Mode Endpoints

```yaml
  /api/v1/governance/mode:
    get:
      summary: Get current governance mode
      responses:
        200:
          content:
            application/json:
              schema:
                type: object
                properties:
                  mode:
                    type: string
                    enum: [OFF, WARNING, SOFT, FULL]
                  last_changed:
                    type: string
                    format: date-time
                  changed_by:
                    type: string

    post:
      summary: Set governance mode
      requestBody:
        content:
          application/json:
            schema:
              type: object
              properties:
                mode:
                  type: string
                  enum: [OFF, WARNING, SOFT, FULL]
      responses:
        200:
          description: Mode updated
```

---

## 7. Testing Strategy

### 7.1 Unit Tests

| Service | Test File | Test Count |
|---------|-----------|------------|
| GovernanceModeService | test_mode_service_isolated.py | 32 |
| AutoGenerationService | test_auto_generator_isolated.py | 34 |
| SignalsEngine | test_signals_engine_isolated.py | 34 |
| StageGatingService | test_stage_gating_isolated.py | 74 |
| ContextAuthorityService | test_context_authority_isolated.py | 86 |
| CEODashboardService | test_ceo_dashboard_isolated.py | 68 |
| MetricsCollector | test_metrics_collector_isolated.py | 104 |
| GrafanaDashboardService | test_grafana_dashboards_isolated.py | 89 |
| **Total** | | **521** |

### 7.2 Integration Tests

| Service | Test File | Test Count |
|---------|-----------|------------|
| MinIO Integration | test_minio_ai_platform.py | 10+ |
| OPA Integration | test_opa_ai_platform.py | 10+ |
| Ollama Integration | test_ollama_ai_platform.py | 10+ |
| GitHub Integration | test_github_integration.py | 10+ |
| Notification Integration | test_notification_integration.py | 10+ |
| **Total** | | **50+** |

### 7.3 E2E Tests

| Scenario | Priority | Status |
|----------|----------|--------|
| Full PR submission flow | P0 | Planned |
| Green PR auto-approval | P0 | Planned |
| Red PR CEO must review | P0 | Planned |
| Kill switch activation | P1 | Planned |
| Break glass bypass | P1 | Planned |
| Dashboard metrics accuracy | P1 | Planned |

---

## 8. Performance Requirements

| Operation | Target | Measurement |
|-----------|--------|-------------|
| Vibecoding index calculation | <500ms | pytest-benchmark |
| CEO dashboard load | <1s | Lighthouse |
| API latency (p95) | <100ms | Prometheus |
| Auto-generation (intent) | <15s | Ollama response |
| Stage gating check | <200ms | pytest-benchmark |

---

## 9. Security Considerations

### 9.1 Access Control

| Role | CEO Dashboard | Kill Switch | Auto-Gen |
|------|---------------|-------------|----------|
| CEO | Full access | View + Emergency | View |
| CTO | View | Full access | View |
| Admin | View | View | View |
| Developer | - | - | Use |

### 9.2 Audit Requirements

- All mode changes logged with timestamp, user, reason
- All decisions (approve/reject) logged
- Break glass events immediately notify CEO/CTO
- Audit logs immutable (append-only)

---

## 10. Monitoring & Alerting

### 10.1 Prometheus Metrics

```python
# Governance metrics
governance_submissions_total{status="pending|approved|rejected"}
governance_vibecoding_index{category="green|yellow|orange|red"}
governance_time_saved_minutes_total
governance_auto_generation_usage{type="intent|ownership|context"}
governance_kill_switch_activations_total

# Performance metrics
governance_api_latency_seconds{endpoint, method}
governance_index_calculation_seconds
```

### 10.2 Grafana Dashboards

| Dashboard | UID | Purpose |
|-----------|-----|---------|
| CEO Dashboard | ceo-dashboard | Executive summary |
| Tech Dashboard | tech-dashboard | Developer experience |
| Ops Dashboard | ops-dashboard | System health |

---

## 11. Rollout Plan

### Phase 1: Warning Mode (Sprint 114)
- Duration: 5 days
- Goal: Establish baseline metrics
- Actions: Enable on Orchestrator repo, collect data

### Phase 2: Soft Enforcement (Sprint 115)
- Duration: 5 days
- Goal: Block critical violations
- Actions: Enable blocking for ownership/intent missing

### Phase 3: Full Enforcement (Sprint 116)
- Duration: 5 days
- Goal: All violations block
- Actions: Measure CEO time saved

---

## 12. References

- ADR-041: Framework 6.0 Governance System Design
- Pre-Phase 0 Documents (docs/governance-v1/)
- SDLC 5.3.0 Section 7: Quality Assurance System

---

## Document Control

| Field | Value |
|-------|-------|
| **Version** | 1.0.0 |
| **Created** | January 28, 2026 |
| **Author** | Backend Lead |
| **Status** | APPROVED |
| **ADR Reference** | ADR-041 |
