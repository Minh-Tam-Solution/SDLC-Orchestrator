# Conformance Check Service - Technical Design Document
## Pattern Conformance Validation & Plan Approval UI

**Epic**: EP-10 Planning Mode with Sub-agent Orchestration
**Status**: 📝 DESIGN PHASE
**Reference**: ADR-034-Planning-Subagent-Orchestration
**Depends On**: Planning-Orchestrator-Service (COMPLETE)
**Implementation**: Sprint 99

---

## 1. Executive Summary

This document describes the conformance checking and plan approval features:
1. **ConformanceCheckService** - Compare PR diffs against established patterns
2. **Planning API Routes** - REST API for planning operations
3. **Plan Approval UI** - Dashboard page for human plan review
4. **GitHub Check Integration** - CI/CD gate for pattern conformance
5. **E2E Tests** - Playwright tests for the complete workflow

---

## 2. Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          PLANNING SUB-AGENT ARCHITECTURE                    │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────────┐     ┌──────────────────────┐     ┌─────────────┐  │
│  │ CLI (sdlcctl plan)  │     │ Web Dashboard        │     │ GitHub CI   │  │
│  │ [Sprint 98 ✅]      │     │ [Sprint 99]          │     │ [Sprint 99] │  │
│  └──────────┬──────────┘     └───────────┬──────────┘     └──────┬──────┘  │
│             │                            │                        │         │
│             ▼                            ▼                        ▼         │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │                     PLANNING API (FastAPI Routes)                     │  │
│  │  POST /planning/plan        - Start planning session                  │  │
│  │  GET  /planning/{id}        - Get planning result                     │  │
│  │  POST /planning/{id}/approve - Approve/reject plan                    │  │
│  │  POST /planning/conformance - Check PR conformance (CI/CD)            │  │
│  │  GET  /planning/sessions    - List active sessions                    │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
│                                      │                                      │
│                                      ▼                                      │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │                       SERVICE LAYER                                   │  │
│  │  ┌──────────────────────────┐  ┌──────────────────────────────────┐  │  │
│  │  │ PlanningOrchestratorSvc  │  │ ConformanceCheckService [NEW]    │  │  │
│  │  │ [Sprint 98 ✅]           │  │ - check_pr_diff()                │  │  │
│  │  │ - plan()                 │  │ - check_plan_conformance()       │  │  │
│  │  │ - approve_plan()         │  │ - calculate_deviation_score()    │  │  │
│  │  │ - get_session()          │  │ - generate_recommendations()     │  │  │
│  │  └──────────────────────────┘  └──────────────────────────────────┘  │  │
│  │  ┌──────────────────────────┐  ┌──────────────────────────────────┐  │  │
│  │  │ PatternExtractionSvc     │  │ ADRScannerService                │  │  │
│  │  │ [Sprint 98 ✅]           │  │ [Sprint 98 ✅]                   │  │  │
│  │  └──────────────────────────┘  └──────────────────────────────────┘  │  │
│  │  ┌──────────────────────────┐                                        │  │
│  │  │ TestPatternService       │                                        │  │
│  │  │ [Sprint 98 ✅]           │                                        │  │
│  │  └──────────────────────────┘                                        │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 3. Feature Specifications

### 3.1 ConformanceCheckService (8 SP)

**Purpose**: Compare proposed changes (PR diff) against established patterns to prevent architectural drift.

**File**: `backend/app/services/conformance_check_service.py`

```python
class ConformanceCheckService:
    """
    Compares proposed changes against established patterns.

    Key Functions:
    1. check_pr_diff() - Analyze GitHub PR diff for conformance
    2. check_plan_conformance() - Validate implementation plan
    3. calculate_deviation_score() - Compute conformance score
    4. generate_recommendations() - Suggest fixes for deviations

    Scoring Criteria (0-100):
    - Pattern coverage: 40 points
    - ADR alignment: 20 points
    - Convention following: 20 points
    - Risk assessment: 20 points
    """

    async def check_pr_diff(
        self,
        pr_diff_url: str,
        project_path: Path,
        patterns: Optional[PatternSummary] = None,
    ) -> ConformanceResult:
        """Check PR conformance for CI/CD integration."""

    async def check_plan_conformance(
        self,
        plan: ImplementationPlan,
        patterns: PatternSummary,
    ) -> ConformanceResult:
        """Check plan conformance before approval."""

    def _analyze_diff_patterns(
        self,
        diff_content: str,
        patterns: PatternSummary,
    ) -> list[ConformanceDeviation]:
        """Analyze diff for pattern violations."""

    def _calculate_score(
        self,
        deviations: list[ConformanceDeviation],
        patterns: PatternSummary,
    ) -> int:
        """Calculate conformance score (0-100)."""
```

**Scoring Algorithm**:
```
Base Score: 100

Deductions:
- Major pattern violation: -15 points
- Minor pattern violation: -5 points
- Missing ADR reference: -10 points
- New pattern without ADR: -10 points
- High-risk change: -5 points per risk

Final Score = max(0, Base Score - Total Deductions)
```

---

### 3.2 Planning API Routes (4 SP)

**Purpose**: REST API endpoints for planning operations.

**File**: `backend/app/api/routes/planning_subagent.py` (new route file to separate from planning hierarchy)

**Endpoints**:

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/v1/planning/subagent/plan` | Start planning session |
| GET | `/api/v1/planning/subagent/{id}` | Get planning result |
| POST | `/api/v1/planning/subagent/{id}/approve` | Approve/reject plan |
| POST | `/api/v1/planning/subagent/conformance` | Check PR conformance |
| GET | `/api/v1/planning/subagent/sessions` | List active sessions |

**Request/Response Examples**:

```json
// POST /api/v1/planning/subagent/plan
// Request:
{
  "task": "Add OAuth2 authentication with Google provider",
  "project_path": "/path/to/project",
  "depth": 3,
  "include_tests": true,
  "include_adrs": true,
  "auto_approve": false
}

// Response:
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "task": "Add OAuth2 authentication with Google provider",
  "status": "awaiting_approval",
  "patterns": {
    "total_patterns_found": 15,
    "categories": {
      "architecture": 5,
      "error_handling": 4,
      "testing": 6
    }
  },
  "plan": {
    "steps": [...],
    "total_estimated_loc": 230,
    "total_estimated_hours": 5.5
  },
  "conformance": {
    "score": 85,
    "level": "good",
    "deviations": []
  }
}
```

---

### 3.3 Plan Approval UI (8 SP)

**Purpose**: Dashboard page for human plan review and approval.

**Files**:
- `frontend/src/app/app/planning/plan-review/page.tsx`
- `frontend/src/app/app/planning/plan-review/[id]/page.tsx`
- `frontend/src/hooks/usePlanningReview.ts`
- `frontend/src/components/planning/PlanReviewCard.tsx`
- `frontend/src/components/planning/ConformanceGauge.tsx`
- `frontend/src/components/planning/PatternList.tsx`
- `frontend/src/components/planning/StepList.tsx`

**UI Components**:

```
┌─────────────────────────────────────────────────────────────────┐
│                   PLAN REVIEW DASHBOARD                         │
├─────────────────────────────────────────────────────────────────┤
│  ┌─────────────────────────────┐  ┌──────────────────────────┐  │
│  │ TASK SUMMARY                │  │ CONFORMANCE SCORE        │  │
│  │ "Add OAuth2 auth..."        │  │      ┌────────┐          │  │
│  │                             │  │      │  85%   │          │  │
│  │ Status: Awaiting Approval   │  │      │  GOOD  │          │  │
│  │ Created: 2m ago             │  │      └────────┘          │  │
│  └─────────────────────────────┘  └──────────────────────────┘  │
│                                                                 │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │ EXTRACTED PATTERNS (15 found)                             │  │
│  │ ┌──────────────────────────────────────────────────────┐  │  │
│  │ │ ✅ FastAPI Router Pattern (auth_service.py)          │  │  │
│  │ │ ✅ Error Handling (try/except with logging)          │  │  │
│  │ │ ✅ Pydantic Schema Validation                        │  │  │
│  │ │ ⚠️ New Pattern: OAuth2 Provider (may need ADR)       │  │  │
│  │ └──────────────────────────────────────────────────────┘  │  │
│  └───────────────────────────────────────────────────────────┘  │
│                                                                 │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │ IMPLEMENTATION PLAN (5 steps)                             │  │
│  │                                                           │  │
│  │ Step 1: Analyze requirements ─────────────────── 0.5h    │  │
│  │ Step 2: Create OAuth2 service ─────────────────── 2.0h   │  │
│  │ Step 3: Integrate with existing auth ──────────── 1.0h   │  │
│  │ Step 4: Write tests ──────────────────────────── 1.5h    │  │
│  │ Step 5: Update documentation ─────────────────── 0.5h    │  │
│  │                                                           │  │
│  │ Total: 230 LOC | 5.5 hours                               │  │
│  └───────────────────────────────────────────────────────────┘  │
│                                                                 │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │ DEVIATIONS & RECOMMENDATIONS                              │  │
│  │                                                           │  │
│  │ ⚠️ New OAuth2 pattern may need ADR documentation         │  │
│  │ ℹ️ Consider referencing ADR-001 (Authentication)         │  │
│  └───────────────────────────────────────────────────────────┘  │
│                                                                 │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │ [Reject with Notes]  [Request Changes]  [✅ Approve Plan] │  │
│  └───────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

**React Hooks**:

```typescript
// usePlanningReview.ts
export function usePlanningSession(sessionId: string) {
  // Fetch single planning session
}

export function usePlanningSessions() {
  // Fetch all active sessions
}

export function useApprovePlan() {
  // Mutation to approve/reject plan
}

export function useStartPlanningSession() {
  // Mutation to start new planning session
}

export function useConformanceCheck() {
  // Mutation to run conformance check
}
```

---

### 3.4 GitHub Check Integration (3 SP)

**Purpose**: GitHub Action workflow to run conformance check on PRs.

**File**: `.github/workflows/pattern-conformance.yml`

```yaml
name: Pattern Conformance Check

on:
  pull_request:
    types: [opened, synchronize, reopened]

permissions:
  contents: read
  pull-requests: write
  checks: write

jobs:
  conformance:
    name: Check Pattern Conformance
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0

      - name: Setup Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Install sdlcctl
        run: |
          cd backend
          pip install -e .

      - name: Run Conformance Check
        id: conformance
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        run: |
          result=$(sdlcctl plan check \
            --pr-url "${{ github.event.pull_request.html_url }}" \
            --format json)

          echo "score=$(echo $result | jq -r '.score')" >> $GITHUB_OUTPUT
          echo "level=$(echo $result | jq -r '.level')" >> $GITHUB_OUTPUT
          echo "deviations=$(echo $result | jq -r '.deviations | length')" >> $GITHUB_OUTPUT
          echo "passed=$(echo $result | jq -r '.passed')" >> $GITHUB_OUTPUT

      - name: Create Check Run
        uses: actions/github-script@v7
        with:
          script: |
            const score = parseInt('${{ steps.conformance.outputs.score }}');
            const level = '${{ steps.conformance.outputs.level }}';
            const deviations = parseInt('${{ steps.conformance.outputs.deviations }}');
            const passed = '${{ steps.conformance.outputs.passed }}' === 'true';

            const emoji = score >= 90 ? '✅' : score >= 70 ? '⚠️' : '❌';
            const conclusion = passed ? 'success' : (score >= 50 ? 'neutral' : 'failure');

            await github.rest.checks.create({
              owner: context.repo.owner,
              repo: context.repo.repo,
              name: 'Pattern Conformance',
              head_sha: context.sha,
              status: 'completed',
              conclusion: conclusion,
              output: {
                title: `${emoji} Conformance: ${score}/100 (${level})`,
                summary: `**Pattern Conformance Score**: ${score}/100\n\n` +
                         `**Level**: ${level}\n` +
                         `**Deviations Found**: ${deviations}\n\n` +
                         (score < 70 ? '⚠️ Consider reviewing patterns before merging.' : ''),
              }
            });

            // Also post comment on PR
            await github.rest.issues.createComment({
              owner: context.repo.owner,
              repo: context.repo.repo,
              issue_number: context.issue.number,
              body: `## ${emoji} Pattern Conformance Check\n\n` +
                    `| Metric | Value |\n` +
                    `|--------|-------|\n` +
                    `| **Score** | ${score}/100 |\n` +
                    `| **Level** | ${level} |\n` +
                    `| **Deviations** | ${deviations} |\n\n` +
                    (score < 70 ? '⚠️ **Warning**: Low conformance score. Please review patterns before merging.\n\n' : '') +
                    `_Checked by SDLC Orchestrator Pattern Conformance_`
            });
```

**CLI Enhancement** (`sdlcctl plan check`):

```python
@plan_app.command(name="check")
def plan_check_command(
    pr_url: str = typer.Option(..., "--pr-url", help="GitHub PR URL"),
    threshold: int = typer.Option(70, "--threshold", "-t", help="Minimum score to pass"),
    format: str = typer.Option("cli", "--format", "-f", help="Output format: cli, json"),
) -> None:
    """
    Check PR conformance against established patterns.
    For CI/CD integration (GitHub Actions).

    Example:
        sdlcctl plan check --pr-url https://github.com/org/repo/pull/123
    """
```

---

### 3.5 E2E Tests (3 SP)

**File**: `frontend/tests/e2e/planning-subagent.spec.ts`

**Test Scenarios**:

| # | Test Case | Description |
|---|-----------|-------------|
| 1 | Plan generation flow | Start planning → Extract patterns → Generate plan |
| 2 | Pattern extraction accuracy | Verify patterns match expected categories |
| 3 | Conformance scoring | Test score calculation with known patterns |
| 4 | Approval workflow | Test approve/reject flow |
| 5 | Plan review UI | Verify all UI components render correctly |
| 6 | Session management | Test session listing and retrieval |
| 7 | Error handling | Test invalid inputs and error states |
| 8 | GitHub Check integration | Test webhook handling and check creation |

---

## 4. Database Changes

No new tables required. Uses existing `planning_sessions` table concept (in-memory for MVP, can be persisted later).

**Future Consideration**: Add `planning_sessions` table for persistence:

```sql
-- Future migration (not in Sprint 99)
CREATE TABLE planning_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID NOT NULL REFERENCES projects(id),
    task TEXT NOT NULL,
    status VARCHAR(50) NOT NULL DEFAULT 'pending',
    patterns_json JSONB,
    plan_json JSONB,
    conformance_json JSONB,
    approved_by UUID REFERENCES users(id),
    approved_at TIMESTAMP,
    rejection_reason TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_planning_sessions_project ON planning_sessions(project_id);
CREATE INDEX idx_planning_sessions_status ON planning_sessions(status);
```

---

## 5. File Structure

```
Sprint 99 New Files:
├── backend/
│   ├── app/
│   │   ├── services/
│   │   │   └── conformance_check_service.py       # NEW (8 SP)
│   │   └── api/routes/
│   │       └── planning_subagent.py               # NEW (4 SP)
│   └── sdlcctl/commands/
│       └── plan.py                                # MODIFY (add check command)
├── frontend/
│   ├── src/
│   │   ├── app/app/planning/
│   │   │   └── plan-review/
│   │   │       ├── page.tsx                       # NEW (sessions list)
│   │   │       └── [id]/
│   │   │           └── page.tsx                   # NEW (single session)
│   │   ├── hooks/
│   │   │   └── usePlanningReview.ts               # NEW
│   │   └── components/planning/
│   │       ├── PlanReviewCard.tsx                 # NEW
│   │       ├── ConformanceGauge.tsx               # NEW
│   │       ├── PatternList.tsx                    # NEW
│   │       └── StepList.tsx                       # NEW
│   └── tests/e2e/
│       └── planning-subagent.spec.ts              # NEW (3 SP)
└── .github/workflows/
    └── pattern-conformance.yml                    # NEW
```

---

## 6. Implementation Order

| Day | Task | Owner | Depends On |
|-----|------|-------|------------|
| Day 1 | ConformanceCheckService core | Backend | - |
| Day 1 | Planning API routes | Backend | - |
| Day 2 | `sdlcctl plan check` command | Backend | Day 1 |
| Day 2 | usePlanningReview hooks | Frontend | Day 1 |
| Day 3 | Plan Review UI components | Frontend | Day 2 |
| Day 3 | Plan Review pages | Frontend | Day 3 |
| Day 4 | GitHub Check workflow | DevOps | Day 2 |
| Day 4 | E2E tests | QA | Day 3 |
| Day 5 | Integration testing | All | Day 4 |
| Day 5 | Documentation & cleanup | All | Day 4 |

---

## 7. Success Criteria

| Criteria | Target | Verification |
|----------|--------|--------------|
| ConformanceCheckService tests | 80%+ coverage | pytest --cov |
| API endpoints working | All 5 endpoints | Integration tests |
| UI components render | 100% | Playwright E2E |
| GitHub Check creates | PR comments appear | Manual test |
| E2E test pass rate | 100% | CI/CD pipeline |
| Performance | <5s for conformance check | Benchmark |

---

## 8. Risks and Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| GitHub API rate limits | CI/CD delays | Cache pattern results |
| Large diff analysis slow | UX degradation | Implement timeout + async |
| Complex UI state | Bug-prone | Use React Query for state |
| Pattern extraction inconsistent | Low conformance accuracy | Add more test patterns |

---

## 9. Post-Sprint Considerations

**Sprint 100 Prep**:
- Feedback Loop Closure (EP-11)
- `pr_learnings` table migration
- FeedbackLearningService

**Future Enhancements**:
- Persist planning sessions to database
- Add AI-powered plan improvement suggestions
- Dashboard analytics for conformance trends

---

## 10. Approval

- [ ] **CTO**: Architecture approval
- [ ] **Backend Lead**: Service design approval
- [ ] **Frontend Lead**: UI design approval
- [ ] **QA Lead**: Test plan approval

---

**Document Version**: 1.0.0
**Created**: January 23, 2026
**Author**: Claude AI + Backend Team
**Status**: 📝 DRAFT - Awaiting Approval
