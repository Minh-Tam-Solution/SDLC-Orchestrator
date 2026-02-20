# Sprint 83: Dynamic Context Injector & Analytics Dashboard

**Sprint ID:** S83
**Status:** DRAFT - Pending Sprint 82 Completion
**Duration:** 10 days (March 17-28, 2026)
**Goal:** Implement gate-triggered AGENTS.md updates + Multi-repo management + Usage analytics
**Story Points:** 34 SP
**Framework Reference:** SDLC 6.1.0 P5 (SASE Integration) + P6 (Observability)
**Prerequisite:** Sprint 82 ✅ Evidence Hash Chain Complete
**Target:** Soft Launch Ready (March 1 → Extended to March 15 with buffer)

---

## CTO Priority Reference (TRUE MOAT - Dynamic AGENTS.md)

| Priority | Task | Sprint 83 Scope | CTO Notes |
|----------|------|-----------------|-----------|
| **P2** | Dynamic Context Injector | ✅ Primary focus | "TRUE MOAT" - unique differentiator |
| **P2** | Multi-repo management | ✅ Secondary focus | Dashboard UI for enterprises |
| **NEW** | Analytics Dashboard | ✅ Included | Overlay usage metrics |
| **P2** | RLS Expansion | ✅ Continuation | All tenant tables |

---

## 🎯 TRUE MOAT: Why Dynamic AGENTS.md Matters

**Key Insight from Expert Consensus:**

> "AGENTS.md trong 60K+ projects đều **tĩnh**. SDLC Orchestrator biến nó thành **động**."

| Static AGENTS.md (Everyone) | Dynamic AGENTS.md (ONLY US) |
|----------------------------|---------------------------|
| Written once, rarely updated | Auto-updates on gate changes |
| Same content for all stages | Stage-specific constraints |
| Manual enforcement | OPA policy enforcement |
| No audit trail | Full evidence chain |

**When... → AGENTS.md auto-updates:**

| Event | AGENTS.md Change |
|-------|------------------|
| Gate G0.2 Pass | `"Design approved. Architecture in /docs/arch.md."` |
| Gate G1 Pass | `"Stage: Build. Unit tests required."` |
| Gate G2 Pass | `"Integration tests mandatory. No new features."` |
| Gate G3 Pass | `"STRICT MODE. Only bug fixes allowed."` |
| Bug #123 detected | `"Known issue in auth_service.py. Do not modify."` |
| Security scan failed | `"BLOCKED: CVE-XXX. Fix before proceeding."` |

---

## 🎯 Sprint 83 Objectives

### Primary Goals (P1 - DIFFERENTIATOR)

1. **Dynamic Context Injector** - Gate-triggered AGENTS.md updates
2. **Multi-Repo Management Dashboard** - Enterprise AGENTS.md overview
3. **Usage Analytics Dashboard** - Overlay metrics and insights

### Secondary Goals (P2)

4. **RLS Policy Expansion** - All tenant-scoped tables
5. **AGENTS.md Template Marketplace** - Community templates
6. **Webhook Integration** - External system notifications

---

## 📋 Sprint 83 Backlog

### Day 1-4: Dynamic Context Injector (14 SP)

**The "TRUE MOAT" Implementation:**

| Task | Owner | Est | Priority | Status |
|------|-------|-----|----------|--------|
| Create `DynamicContextService` | Backend | 4h | P1 | ⏳ |
| Gate event listener (subscribe to gate changes) | Backend | 3h | P1 | ⏳ |
| AGENTS.md section update logic | Backend | 4h | P1 | ⏳ |
| Constraint injection from OPA results | Backend | 3h | P1 | ⏳ |
| Sprint context auto-population | Backend | 2h | P1 | ⏳ |
| Webhook trigger on AGENTS.md update | Backend | 2h | P1 | ⏳ |
| Evidence capture for updates | Backend | 2h | P1 | ⏳ |
| Unit tests (12 tests) | Backend | 3h | P1 | ⏳ |
| Integration tests (6 tests) | QA | 3h | P1 | ⏳ |

**Technical Design:**

```python
# backend/app/services/dynamic_context_service.py
"""
Dynamic Context Injector - The TRUE MOAT

This service automatically updates AGENTS.md when:
1. Gate status changes (G0 → G1 → G2 → G3...)
2. Sprint changes (new sprint, days remaining update)
3. Constraints detected (security vulnerabilities, coverage drops)
4. Strict mode activation (post-G3)

Flow:
1. Gate service emits event → EventBus
2. DynamicContextService receives event
3. Computes new AGENTS.md section
4. Updates file via GitHub API
5. Captures evidence of update
6. Notifies subscribers (webhooks, VS Code)
"""

from datetime import datetime
from typing import Optional
from uuid import UUID

from app.events import EventBus, GateStatusChanged, SprintChanged, ConstraintDetected
from app.services.agents_md_generator_service import AgentsMdGeneratorService
from app.services.github_service import GitHubService
from app.services.evidence_manifest_service import EvidenceManifestService


class DynamicContextService:
    """
    Automatically updates AGENTS.md based on SDLC lifecycle events.

    This is our unique differentiator:
    - 60,000 projects have static AGENTS.md
    - We make it dynamic and gate-aware
    """

    def __init__(
        self,
        event_bus: EventBus,
        generator: AgentsMdGeneratorService,
        github: GitHubService,
        evidence: EvidenceManifestService,
    ):
        self.event_bus = event_bus
        self.generator = generator
        self.github = github
        self.evidence = evidence

        # Subscribe to lifecycle events
        self.event_bus.subscribe(GateStatusChanged, self._on_gate_change)
        self.event_bus.subscribe(SprintChanged, self._on_sprint_change)
        self.event_bus.subscribe(ConstraintDetected, self._on_constraint)

    async def _on_gate_change(self, event: GateStatusChanged) -> None:
        """
        Update AGENTS.md when gate status changes.

        Examples:
        - G1 PASSED → Add "Stage: Build. Unit tests required."
        - G3 PASSED → Add "🔒 STRICT MODE. Only bug fixes allowed."
        """
        project_id = event.project_id
        new_gate = event.new_status

        # Generate updated context section
        context_update = await self._generate_gate_context(
            project_id=project_id,
            gate_name=new_gate.gate_name,
            gate_status=new_gate.status,
        )

        # Update AGENTS.md
        await self._update_agents_md(
            project_id=project_id,
            section="current_stage",
            content=context_update,
            trigger=f"Gate {new_gate.gate_name} → {new_gate.status}",
        )

    async def _on_sprint_change(self, event: SprintChanged) -> None:
        """
        Update AGENTS.md when sprint changes.

        Examples:
        - New sprint → Update sprint number, goal, deadline
        - Days remaining → Update countdown
        """
        project_id = event.project_id
        sprint = event.new_sprint

        context_update = {
            "sprint_number": sprint.number,
            "sprint_goal": sprint.goal,
            "days_remaining": sprint.days_remaining,
            "deadline": sprint.end_date.isoformat(),
        }

        await self._update_agents_md(
            project_id=project_id,
            section="sprint",
            content=context_update,
            trigger=f"Sprint {sprint.number} started",
        )

    async def _on_constraint(self, event: ConstraintDetected) -> None:
        """
        Add constraint to AGENTS.md when detected.

        Examples:
        - Security vulnerability → Add warning with affected files
        - Coverage drop → Add requirement message
        - Test failure → Add blocked status
        """
        project_id = event.project_id
        constraint = event.constraint

        # Add to constraints section (append, don't replace)
        await self._append_constraint(
            project_id=project_id,
            constraint={
                "type": constraint.type,
                "severity": constraint.severity,
                "message": constraint.message,
                "affected_files": constraint.affected_files,
                "detected_at": datetime.utcnow().isoformat(),
            },
            trigger=f"Constraint: {constraint.type}",
        )

    async def _generate_gate_context(
        self,
        project_id: UUID,
        gate_name: str,
        gate_status: str,
    ) -> dict:
        """Generate context text for gate change."""

        gate_messages = {
            ("G0.1", "PASSED"): "Problem definition approved. Ready for solution exploration.",
            ("G0.2", "PASSED"): "Design approved. Architecture documents in /docs/.",
            ("G1", "PASSED"): "Stage: BUILD. Unit tests required for all new code.",
            ("G2", "PASSED"): "Stage: INTEGRATE. Integration tests mandatory. No new features.",
            ("G3", "PASSED"): "🔒 STRICT MODE ACTIVE. Only bug fixes allowed. All changes require review.",
            ("G4", "PASSED"): "Stage: VALIDATE. Internal testing in progress. No code changes.",
            ("G5", "PASSED"): "✅ RELEASED. Production monitoring active.",
        }

        message = gate_messages.get(
            (gate_name, gate_status),
            f"Gate {gate_name}: {gate_status}"
        )

        # Check for strict mode
        strict_mode = gate_name in ("G3", "G4", "G5") and gate_status == "PASSED"

        return {
            "stage_name": self._gate_to_stage(gate_name),
            "gate_status": f"{gate_name} {gate_status}",
            "message": message,
            "strict_mode": strict_mode,
            "updated_at": datetime.utcnow().isoformat(),
        }

    async def _update_agents_md(
        self,
        project_id: UUID,
        section: str,
        content: dict,
        trigger: str,
    ) -> None:
        """
        Update AGENTS.md file in repository.

        Flow:
        1. Fetch current AGENTS.md
        2. Parse sections
        3. Update specific section
        4. Commit via GitHub API
        5. Capture evidence
        """
        # Get project repo info
        project = await self._get_project(project_id)
        repo_owner = project.github_owner
        repo_name = project.github_repo

        # Fetch current AGENTS.md
        current_content = await self.github.get_file_content(
            owner=repo_owner,
            repo=repo_name,
            path="AGENTS.md",
        )

        # Update section
        updated_content = self.generator.update_section(
            content=current_content,
            section=section,
            new_data=content,
        )

        # Commit change
        commit_message = f"chore(agents): Auto-update AGENTS.md - {trigger}"
        await self.github.update_file(
            owner=repo_owner,
            repo=repo_name,
            path="AGENTS.md",
            content=updated_content,
            message=commit_message,
            branch="main",  # Or default branch
        )

        # Capture evidence
        await self.evidence.create_manifest(
            project_id=project_id,
            artifacts=[{
                "artifact_id": f"agents-md-update-{datetime.utcnow().timestamp()}",
                "sha256": hashlib.sha256(updated_content.encode()).hexdigest(),
                "path": "AGENTS.md",
                "size": len(updated_content),
                "uploaded_at": datetime.utcnow(),
            }],
        )

        # Emit update event (for webhooks, VS Code, etc.)
        await self.event_bus.publish(AgentsMdUpdated(
            project_id=project_id,
            section=section,
            trigger=trigger,
            updated_at=datetime.utcnow(),
        ))

    def _gate_to_stage(self, gate_name: str) -> str:
        """Map gate name to SDLC stage."""
        mapping = {
            "G0.1": "DISCOVER",
            "G0.2": "DESIGN",
            "G1": "BUILD",
            "G2": "INTEGRATE",
            "G3": "TEST",
            "G4": "VALIDATE",
            "G5": "RELEASE",
        }
        return mapping.get(gate_name, "UNKNOWN")
```

**Event System:**

```python
# backend/app/events/lifecycle_events.py
from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass
class GateStatusChanged:
    """Emitted when a project's gate status changes."""
    project_id: UUID
    new_status: "GateStatus"
    previous_status: "GateStatus"
    changed_by: UUID
    changed_at: datetime


@dataclass
class SprintChanged:
    """Emitted when sprint changes (new sprint or update)."""
    project_id: UUID
    new_sprint: "Sprint"
    previous_sprint: "Sprint"
    change_type: str  # "new", "update", "close"


@dataclass
class ConstraintDetected:
    """Emitted when a constraint is detected."""
    project_id: UUID
    constraint: "Constraint"
    source: str  # "sast", "test", "coverage", "manual"


@dataclass
class AgentsMdUpdated:
    """Emitted when AGENTS.md is automatically updated."""
    project_id: UUID
    section: str
    trigger: str
    updated_at: datetime
```

---

### Day 5-6: Multi-Repo Management Dashboard (8 SP)

**Enterprise AGENTS.md Overview:**

| Task | Owner | Est | Priority | Status |
|------|-------|-----|----------|--------|
| Create multi-repo overview page | Frontend | 4h | P1 | ⏳ |
| Repo status cards (stage, gate, last update) | Frontend | 3h | P1 | ⏳ |
| Bulk actions (regenerate, validate) | Backend | 3h | P1 | ⏳ |
| Diff view for AGENTS.md changes | Frontend | 3h | P1 | ⏳ |
| Filter/sort by status, stage, team | Frontend | 2h | P2 | ⏳ |
| Unit tests (6 tests) | Frontend | 2h | P1 | ⏳ |

**Frontend Design:**

```typescript
// frontend/web/src/pages/agents-md/MultiRepoPage.tsx

import { useQuery } from '@tanstack/react-query';
import { Card, Badge, Button, Table } from '@/components/ui';
import { apiClient } from '@/lib/api';

interface RepoStatus {
  id: string;
  name: string;
  owner: string;
  stage_name: string;
  gate_status: string;
  strict_mode: boolean;
  agents_md_version: string;
  last_updated: string;
  constraints_count: number;
}

export function MultiRepoPage() {
  const { data: repos, isLoading } = useQuery({
    queryKey: ['agents-md', 'repos'],
    queryFn: () => apiClient.get<RepoStatus[]>('/api/v1/agents-md/repos'),
  });

  const handleBulkRegenerate = async (repoIds: string[]) => {
    await apiClient.post('/api/v1/agents-md/bulk/regenerate', { repo_ids: repoIds });
  };

  return (
    <div className="p-6">
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-2xl font-bold">AGENTS.md Management</h1>
        <Button onClick={() => handleBulkRegenerate(selectedRepos)}>
          Regenerate Selected
        </Button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
        <StatsCard title="Total Repos" value={repos?.length || 0} />
        <StatsCard
          title="Strict Mode Active"
          value={repos?.filter(r => r.strict_mode).length || 0}
          variant="warning"
        />
        <StatsCard
          title="With Constraints"
          value={repos?.filter(r => r.constraints_count > 0).length || 0}
          variant="error"
        />
      </div>

      <Table>
        <Table.Header>
          <Table.Row>
            <Table.Head>Repository</Table.Head>
            <Table.Head>Stage</Table.Head>
            <Table.Head>Gate Status</Table.Head>
            <Table.Head>Constraints</Table.Head>
            <Table.Head>Last Updated</Table.Head>
            <Table.Head>Actions</Table.Head>
          </Table.Row>
        </Table.Header>
        <Table.Body>
          {repos?.map(repo => (
            <Table.Row key={repo.id}>
              <Table.Cell>
                <div className="flex items-center gap-2">
                  {repo.strict_mode && <Badge variant="error">🔒</Badge>}
                  <span>{repo.owner}/{repo.name}</span>
                </div>
              </Table.Cell>
              <Table.Cell>
                <StageBadge stage={repo.stage_name} />
              </Table.Cell>
              <Table.Cell>
                <GateBadge status={repo.gate_status} />
              </Table.Cell>
              <Table.Cell>
                {repo.constraints_count > 0 ? (
                  <Badge variant="warning">{repo.constraints_count}</Badge>
                ) : (
                  <Badge variant="success">0</Badge>
                )}
              </Table.Cell>
              <Table.Cell>
                <RelativeTime date={repo.last_updated} />
              </Table.Cell>
              <Table.Cell>
                <Button size="sm" variant="ghost" onClick={() => viewDiff(repo.id)}>
                  View Diff
                </Button>
                <Button size="sm" variant="ghost" onClick={() => regenerate(repo.id)}>
                  Regenerate
                </Button>
              </Table.Cell>
            </Table.Row>
          ))}
        </Table.Body>
      </Table>
    </div>
  );
}
```

**API Endpoints:**

```yaml
# Multi-repo management endpoints
GET /api/v1/agents-md/repos:
  summary: List all repos with AGENTS.md status
  tags: [AGENTS.md]
  query_params:
    organization_id: UUID (optional)
    stage_filter: string (optional)
    strict_mode_only: boolean (optional)
  response:
    items: array[RepoStatus]
    total: int

POST /api/v1/agents-md/bulk/regenerate:
  summary: Regenerate AGENTS.md for multiple repos
  tags: [AGENTS.md]
  request_body:
    repo_ids: array[UUID]
  response:
    results: array[{repo_id, status, message}]

GET /api/v1/agents-md/{repo_id}/diff:
  summary: Get diff between current and previous AGENTS.md
  tags: [AGENTS.md]
  response:
    current_version: string
    previous_version: string
    diff: string (unified diff format)
    changed_at: datetime
```

---

### Day 7-8: Analytics Dashboard (8 SP)

**Usage Metrics & Insights:**

| Task | Owner | Est | Priority | Status |
|------|-------|-----|----------|--------|
| Create analytics data aggregation | Backend | 3h | P1 | ⏳ |
| Overlay usage metrics endpoint | Backend | 2h | P1 | ⏳ |
| Analytics dashboard page | Frontend | 4h | P1 | ⏳ |
| Charts: updates over time, by stage | Frontend | 3h | P1 | ⏳ |
| Export to CSV/JSON | Backend | 2h | P2 | ⏳ |
| Unit tests (4 tests) | QA | 2h | P1 | ⏳ |

**Metrics to Track:**

```yaml
# Analytics metrics
overlay_metrics:
  - agents_md_updates_total      # Total AGENTS.md updates
  - agents_md_updates_by_trigger # Updates by trigger type
  - check_runs_total             # Total Check Runs created
  - check_runs_by_conclusion     # success, failure, action_required
  - constraints_detected_total   # Constraints detected
  - constraints_by_type          # By type (security, coverage, etc.)
  - avg_time_to_gate_pass        # Average time between gates
  - strict_mode_activations      # Times strict mode was activated

user_engagement:
  - vscode_context_panel_views   # VS Code panel opens
  - cli_context_commands         # CLI context fetches
  - dashboard_visits             # Web dashboard visits
  - pr_comment_interactions      # Clicks on PR comments
```

**Frontend Design:**

```typescript
// frontend/web/src/pages/analytics/OverlayAnalyticsPage.tsx

import { LineChart, BarChart, PieChart } from 'recharts';

export function OverlayAnalyticsPage() {
  const { data: metrics } = useQuery({
    queryKey: ['analytics', 'overlay'],
    queryFn: () => apiClient.get('/api/v1/analytics/overlay'),
  });

  return (
    <div className="p-6 space-y-6">
      <h1 className="text-2xl font-bold">AGENTS.md Analytics</h1>

      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <MetricCard
          title="Total Updates"
          value={metrics?.total_updates}
          trend={metrics?.updates_trend}
        />
        <MetricCard
          title="Check Runs"
          value={metrics?.total_check_runs}
          trend={metrics?.check_runs_trend}
        />
        <MetricCard
          title="Constraints"
          value={metrics?.total_constraints}
          trend={metrics?.constraints_trend}
        />
        <MetricCard
          title="Strict Mode Active"
          value={metrics?.strict_mode_count}
          unit="repos"
        />
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <Card>
          <Card.Header>Updates Over Time</Card.Header>
          <Card.Content>
            <LineChart data={metrics?.updates_by_day} />
          </Card.Content>
        </Card>

        <Card>
          <Card.Header>Updates by Trigger</Card.Header>
          <Card.Content>
            <PieChart data={metrics?.updates_by_trigger} />
          </Card.Content>
        </Card>

        <Card>
          <Card.Header>Check Run Conclusions</Card.Header>
          <Card.Content>
            <BarChart data={metrics?.check_runs_by_conclusion} />
          </Card.Content>
        </Card>

        <Card>
          <Card.Header>Constraints by Type</Card.Header>
          <Card.Content>
            <BarChart data={metrics?.constraints_by_type} />
          </Card.Content>
        </Card>
      </div>
    </div>
  );
}
```

---

### Day 9-10: RLS Expansion + Cleanup (4 SP)

**Expand Row-Level Security:**

| Task | Owner | Est | Priority | Status |
|------|-------|-----|----------|--------|
| RLS policy for `projects` table | Backend | 2h | P2 | ⏳ |
| RLS policy for `evidence_manifests` table | Backend | 2h | P2 | ⏳ |
| RLS policy for `gates` table | Backend | 2h | P2 | ⏳ |
| Performance testing with RLS | QA | 2h | P2 | ⏳ |
| Sprint 83 documentation | PM | 2h | P1 | ⏳ |

**RLS Migration:**

```sql
-- backend/alembic/versions/s83_001_rls_expansion.py

-- Projects table RLS
ALTER TABLE projects ENABLE ROW LEVEL SECURITY;

CREATE POLICY project_team_access ON projects
    FOR ALL
    USING (
        team_id IN (
            SELECT team_id FROM team_members
            WHERE user_id = current_setting('app.current_user_id')::uuid
        )
    );

-- Evidence manifests RLS
ALTER TABLE evidence_manifests ENABLE ROW LEVEL SECURITY;

CREATE POLICY evidence_project_access ON evidence_manifests
    FOR ALL
    USING (
        project_id IN (
            SELECT id FROM projects
            WHERE team_id IN (
                SELECT team_id FROM team_members
                WHERE user_id = current_setting('app.current_user_id')::uuid
            )
        )
    );

-- Gates table RLS
ALTER TABLE gates ENABLE ROW LEVEL SECURITY;

CREATE POLICY gates_project_access ON gates
    FOR ALL
    USING (
        project_id IN (
            SELECT id FROM projects
            WHERE team_id IN (
                SELECT team_id FROM team_members
                WHERE user_id = current_setting('app.current_user_id')::uuid
            )
        )
    );
```

---

## 🔒 Definition of Done

### Code Complete

- [ ] `DynamicContextService` with event listeners
- [ ] Gate/Sprint/Constraint event handlers
- [ ] AGENTS.md auto-update via GitHub API
- [ ] Multi-repo management dashboard
- [ ] Analytics dashboard with charts
- [ ] RLS policies for core tables

### Tests

- [ ] Dynamic context unit tests (12 tests)
- [ ] Event handling integration tests (6 tests)
- [ ] Multi-repo API tests (8 tests)
- [ ] Analytics endpoint tests (4 tests)
- [ ] RLS policy tests (6 tests)
- [ ] Total coverage: 90%+

### Documentation

- [ ] Dynamic Context Injector design doc
- [ ] Multi-repo management user guide
- [ ] Analytics dashboard guide
- [ ] API documentation updated

### Review

- [ ] CTO review (Dynamic Context is TRUE MOAT)
- [ ] Code review by Tech Lead
- [ ] PR merged to main
- [ ] Staging deployment verified

---

## 📊 Success Criteria (Soft Launch Mar 15)

| Metric | Target | Verification |
|--------|--------|--------------|
| AGENTS.md auto-updates | <30s after gate change | Event → file update latency |
| Multi-repo dashboard | <1s load time | Performance test |
| Analytics data accuracy | 100% | Cross-check with raw data |
| RLS policy coverage | 4 tables | All tenant-scoped tables |

---

## 🚀 Launch Readiness (Post-Sprint 83)

### Go/No-Go Criteria (March 15, 2026)

| Metric | Target | Sprint 83 Status |
|--------|--------|------------------|
| P0 blockers | 0 open | ✅ Sprint 82 |
| Evidence hash chain | Tamper-evident | ✅ Sprint 82 |
| GitHub Check Run | Working in staging | ✅ Sprint 81-82 |
| Dynamic AGENTS.md | Auto-updates on gate | ⏳ Sprint 83 |
| First customers | ≥2 committed (LOI) | Business track |

### Soft Launch Checklist

- [ ] All P0 blockers resolved (Sprint 82)
- [ ] Dynamic Context Injector working (Sprint 83)
- [ ] Multi-repo dashboard for enterprises (Sprint 83)
- [ ] Analytics dashboard operational (Sprint 83)
- [ ] 2+ customers with signed LOI
- [ ] Production environment ready
- [ ] Monitoring & alerting configured
- [ ] Runbooks documented

---

## 📅 Daily Standup Schedule

| Day | Focus | Deliverable |
|-----|-------|-------------|
| **Mar 17-18** | Dynamic Context Service | Event listeners + gate handler |
| **Mar 19-20** | AGENTS.md Auto-Update | GitHub API integration + evidence |
| **Mar 21-24** | Multi-Repo Dashboard | Overview page + bulk actions |
| **Mar 25-26** | Analytics Dashboard | Metrics + charts |
| **Mar 27** | RLS Expansion | Policies for core tables |
| **Mar 28** | Testing & Launch Prep | E2E tests, docs, launch readiness |

---

## 🔗 Dependencies

| Dependency | Team | Status | Blocker? |
|------------|------|--------|----------|
| Sprint 82 Complete | Backend | ⏳ Pending | ⚠️ Yes |
| GitHub App working | DevOps | ⏳ Sprint 82 | ⚠️ Yes |
| Event Bus infrastructure | Backend | ✅ Existing | ❌ No |
| Frontend components | Frontend | ✅ Sprint 81 | ❌ No |

---

## ⚠️ Risks & Mitigations

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| GitHub API rate limits | Medium | High | Batch updates, use webhooks |
| Event processing lag | Medium | Medium | Async queue, retry mechanism |
| RLS performance impact | Low | Medium | Benchmark, optimize indexes |
| Analytics data volume | Low | Low | Aggregate by day, archive old data |

---

## 📎 References

- [CTO Plan - TRUE MOAT: Dynamic AGENTS.md](../../09-govern/05-Knowledge-Transfer/01-Expert-Request/crispy-drifting-walrus.md#113-true-moat-dynamic-agentsmd)
- [Sprint 82 - Evidence Hash Chain](./SPRINT-82-HARDENING-EVIDENCE.md)
- [Sprint 81 - AGENTS.md Integration](./SPRINT-81-AGENTS-MD-INTEGRATION.md)
- [AGENTS.md Technical Design](../../02-design/14-Technical-Specs/AGENTS-MD-Technical-Design.md)

---

**Sprint 83 Plan Version:** 1.0.0
**Created:** January 19, 2026
**Author:** Backend Lead
**Status:** DRAFT - Pending Sprint 82 Close
**Soft Launch Target:** March 15, 2026

---

**SDLC 6.1.0 | Sprint 83 | Stage 04 (BUILD)**

*Dynamic AGENTS.md - "60,000 projects use AGENTS.md. Zero have enforcement. Until now." - Positioning*
