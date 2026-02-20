# Sprint 176: "Autonomous Codegen & Pilot Prep" — ADR-055 Phase 1 + SASE Backend

**Sprint Duration**: March 17-28, 2026 (10 working days)
**Status**: PLANNED
**Phase**: Stage 04 (BUILD) — Autonomous Codegen Implementation + Pilot Preparation
**Framework**: SDLC 6.1.0
**Priority**: P0 (ADR-055 Implementation + Vietnamese SME Pilot Readiness)
**Previous Sprint**: [Sprint 175 — Frontend Feature Completion](SPRINT-175-FRONTEND-COMPLETION.md)
**ADR Reference**: [ADR-055 — Autonomous Codegen with 4-Gate Validation](../../02-design/ADR-055-Autonomous-Codegen-4-Gate-Validation.md)
**Framework Reference**: [11-AUTONOMOUS-CODEGEN-PATTERNS.md](../../../SDLC-Enterprise-Framework/03-AI-GOVERNANCE/11-AUTONOMOUS-CODEGEN-PATTERNS.md)

---

## Sprint Goal

Implement **ADR-055 Phase 1** (Initializer Agent with Gate G1), close the Sprint 175 **SASE Templates backend gap** with a lightweight static API, add **E2E tests** for the 6 newly-visible pages, and prepare **Vietnamese SME pilot onboarding** materials. This sprint bridges frontend completion (Sprint 175) with the autonomous codegen roadmap (Sprint 177-178).

---

## Sprint Context

**ADR-055 Roadmap** (3-sprint arc):
```
Sprint 176: Initializer Agent + Gate G1        ← YOU ARE HERE
Sprint 177: Coding Agent Loop + Gates G2/G3
Sprint 178: Full E2E Autonomous Codegen Pilot
```

**Sprint 175 Deferrals** (must close):
- SASE Templates backend API (originally estimated 8 days, **reduced to 2 days** via Static Template Service approach)
- E2E Playwright tests for 6 newly-visible pages
- Mobile responsive design (deferred again to Sprint 178+)

**Pilot Timeline**:
- Vietnamese SME Pilot target: 5 founding customers
- CLAUDE.md PRO tier ready (1,871 lines, Sprint 174)
- Pilot onboarding runbook needed before Sprint 178

---

## Success Criteria

- [ ] Initializer Agent service created with spec parsing + `feature_list.json` generation
- [ ] Gate G1 (Spec Review) integrated — blocks coding if spec incomplete
- [ ] SASE Templates served via backend API (static service, no database)
- [ ] Frontend SASE Templates page connected to backend API (replace hardcoded data)
- [ ] E2E Playwright tests for 6 Sprint 175 pages (all passing)
- [ ] Browser Agent hardened for production (retry logic, screenshot-on-failure)
- [ ] Pilot onboarding runbook created (Vietnamese SME specific)
- [ ] All existing tests pass (`python -m pytest backend/tests/ -v`)
- [ ] TypeScript + build still passing after Sprint 175 changes

---

## Key Metrics

| Metric | Target | How to Check |
|--------|--------|--------------|
| Initializer Agent — spec → feature_list.json | <30s | `time sdlcctl codegen init --spec spec.yaml` |
| Gate G1 pass rate on valid specs | >95% | `python -m pytest tests/unit/test_gate_g1.py` |
| SASE Templates API response time | <100ms | `curl -w '%{time_total}' /api/v1/templates/sase-templates` |
| E2E tests passing | 6/6 new tests | `cd frontend && npx playwright test e2e/sprint-175/` |
| Browser agent screenshot reliability | >99% | Integration test with 100 iterations |
| Existing test suite | 0 regressions | `python -m pytest backend/tests/ -v` |

---

## Scope

### In Scope

| # | Track | Deliverable | Priority | Days |
|---|-------|-------------|----------|------|
| 1 | **Backend** | Initializer Agent service (ADR-055 Phase 1) | P0 | 3 |
| 2 | **Backend** | Gate G1 integration (spec completeness check) | P0 | 2 |
| 3 | **Backend** | SASE Templates static API endpoint | P1 | 1 |
| 4 | **Frontend** | SASE Templates — connect to backend API | P1 | 1 |
| 5 | **Testing** | E2E Playwright tests for 6 Sprint 175 pages | P1 | 2 |
| 6 | **Backend** | Browser Agent production hardening | P1 | 1 |
| 7 | **Docs** | Pilot onboarding runbook (Vietnamese SME) | P2 | 0.5 |
| 8 | **Verify** | Integration testing + regression check | P0 | 0.5 |

**Total**: 11 task-days across 10 calendar days (overlap on smaller tasks)

### Out of Scope (Deferred to Sprint 177+)

| Item | Reason | Sprint |
|------|--------|--------|
| Coding Agent Loop (ADR-055 Phase 2) | Depends on Initializer Agent | Sprint 177 |
| Gates G2/G3 integration | Depends on Coding Agent | Sprint 177 |
| Full E2E Autonomous Codegen Pilot | Depends on Phases 1+2 | Sprint 178 |
| Database-backed SASE Templates (custom per-org) | Enterprise feature, no customer demand yet | Future |
| Mobile responsive for 6 pages | Desktop-first priority | Sprint 178+ |
| Drag-and-drop sprint reordering | UX enhancement | Future |
| Real-time WebSocket for CEO Dashboard | Polling sufficient for MVP | Future |

---

## Execution Model — Dual Track

```
Track A: Backend Engineer (ADR-055 + SASE API)
  Days 1-3: Initializer Agent service
  Days 4-5: Gate G1 integration
  Day 6:    SASE Templates API
  Day 7:    Browser Agent hardening
  Days 8-9: Integration testing
  Day 10:   Regression check + documentation

Track B: Frontend Engineer (E2E Tests + SASE Frontend + Pilot Docs)
  Day 1:    E2E test setup for Sprint 175 pages
  Days 2-3: E2E tests (CEO Dashboard, MCP Analytics, Planning)
  Days 4-5: E2E tests (Plan Review, Learnings, SASE Templates)
  Day 6:    SASE Templates frontend — connect to backend API
  Days 7-8: Pilot onboarding runbook
  Day 9:    Cross-track integration testing
  Day 10:   Final QA + sprint documentation
```

**Benefit**: Backend and Frontend tracks run in parallel. SASE API (Track A Day 6) feeds SASE Frontend (Track B Day 6) — single sync point.

---

## Sprint Backlog — Daily Breakdown

### Track A: Backend

#### Days 1-3: Initializer Agent Service (ADR-055 Phase 1)

**Owner**: Backend Engineer
**Priority**: P0

##### Task A1.1: Initializer Agent Core Service (Day 1, 6h)

**Create**: `backend/app/services/codegen/initializer_agent.py`

The Initializer Agent reads a project specification and produces a structured `feature_list.json` that the Coding Agent (Sprint 177) will iterate through.

**Responsibilities**:
1. Parse specification file (YAML/JSON blueprint)
2. Extract features with dependencies
3. Generate `feature_list.json` with prioritized feature list
4. Validate spec completeness (required fields check)
5. Estimate complexity per feature (simple/medium/complex)

**Interface**:
```python
class InitializerAgent:
    """
    ADR-055 Phase 1: Spec → Feature List transformation.

    Reads project blueprint, extracts features with dependencies,
    and produces a structured feature_list.json for the Coding Agent.
    """

    async def initialize(
        self,
        spec_path: str,
        project_id: UUID,
        mode: Literal["scaffold", "production"] = "scaffold",
    ) -> InitializationResult:
        """
        Parse spec and generate feature list.

        Args:
            spec_path: Path to YAML/JSON specification
            project_id: Project UUID for context
            mode: scaffold (lenient) or production (strict)

        Returns:
            InitializationResult with feature_list and validation report
        """

    async def validate_spec(
        self,
        spec: dict,
    ) -> SpecValidationResult:
        """
        Validate specification completeness.

        Checks: required fields, entity definitions, relationship integrity,
        Vietnamese domain template compliance (if applicable).
        """
```

**Output Schema** (`feature_list.json`):
```json
{
  "project_id": "uuid",
  "spec_version": "1.0",
  "mode": "scaffold",
  "total_features": 12,
  "features": [
    {
      "id": "feat-001",
      "name": "User Authentication",
      "description": "JWT + OAuth login flow",
      "complexity": "medium",
      "dependencies": [],
      "priority": 1,
      "estimated_files": 5,
      "status": "pending"
    }
  ],
  "dependency_graph": { ... },
  "validation": {
    "spec_complete": true,
    "warnings": [],
    "gate_g1_ready": true
  }
}
```

**Acceptance Criteria**:
- [ ] Parses YAML blueprint (AppBlueprint format from App Builder)
- [ ] Extracts entities, relationships, and features
- [ ] Generates dependency graph (topological sort)
- [ ] Assigns complexity scores (simple: <3 files, medium: 3-8, complex: >8)
- [ ] Returns structured `InitializationResult`

##### Task A1.2: Initializer Agent — Multi-Provider Spec Analysis (Day 2, 6h)

Integrate with AI Context Engine for intelligent spec analysis:
- Use Ollama `qwen3-coder:30b` (primary) for spec understanding
- Fallback to Claude for complex specs
- Rule-based fallback for simple CRUD specs

**Features**:
1. AI-assisted feature extraction (beyond simple parsing)
2. Dependency inference (if A has FK to B, B must be created first)
3. Vietnamese domain template matching (E-commerce, HRM, CRM patterns)
4. Complexity estimation via LLM analysis

**Acceptance Criteria**:
- [ ] Multi-provider chain works (Ollama → Claude → Rule-based)
- [ ] Vietnamese domain templates detected and applied
- [ ] Feature extraction handles nested entities
- [ ] Timeout handling: <30s per spec analysis

##### Task A1.3: Initializer Agent — CLI Integration (Day 3, 4h)

**Edit**: `backend/sdlcctl/sdlcctl/commands/codegen.py`

Add `init` subcommand:
```bash
# Initialize project from specification
sdlcctl codegen init --spec blueprint.yaml --project-id UUID

# Initialize with production mode (strict validation)
sdlcctl codegen init --spec blueprint.yaml --project-id UUID --mode production

# Dry run (validate only, don't generate feature_list.json)
sdlcctl codegen init --spec blueprint.yaml --dry-run
```

**Edit**: `backend/app/api/routes/codegen.py`

Add API endpoint:
```
POST /api/v1/codegen/initialize
  Body: { spec: object, project_id: UUID, mode: "scaffold"|"production" }
  Response: InitializationResult
```

**Acceptance Criteria**:
- [ ] CLI `sdlcctl codegen init` works end-to-end
- [ ] API endpoint returns InitializationResult
- [ ] Dry-run mode validates without creating files
- [ ] Error messages are actionable ("Missing 'entities' field in spec")

##### Task A1.4: Initializer Agent — Unit Tests (Day 3, 2h)

**Create**: `backend/tests/unit/test_initializer_agent.py`

Test cases:
1. Parse valid YAML blueprint → correct feature list
2. Parse blueprint with missing fields → validation errors
3. Dependency graph generation → topological order correct
4. Vietnamese domain template detection → correct template applied
5. Multi-provider fallback → works when Ollama unavailable
6. Timeout handling → returns partial result after 30s

**Acceptance Criteria**:
- [ ] >95% coverage on initializer_agent.py
- [ ] All test cases pass
- [ ] Mocks only for external services (Ollama, Claude), not internal logic

---

#### Days 4-5: Gate G1 Integration

**Owner**: Backend Engineer
**Priority**: P0

##### Task A2.1: Gate G1 — Spec Review Policy (Day 4, 4h)

**Create**: `backend/policy-packs/rego/gates/g1_spec_review.rego`

OPA policy that evaluates spec completeness before coding begins:

```rego
package sdlc.gates.g1_spec_review

# Gate G1 passes when spec is complete and validated
default allow = false

allow {
    input.spec_validation.spec_complete == true
    input.spec_validation.gate_g1_ready == true
    count(input.spec_validation.errors) == 0
}

# Warnings are allowed (soft-fail)
warnings[msg] {
    warning := input.spec_validation.warnings[_]
    msg := sprintf("Warning: %s", [warning])
}

# Errors block gate passage
errors[msg] {
    error := input.spec_validation.errors[_]
    msg := sprintf("Error: %s - %s", [error.field, error.message])
}
```

**Acceptance Criteria**:
- [ ] Policy evaluates spec completeness
- [ ] Blocks coding if required fields missing
- [ ] Allows warnings (non-blocking)
- [ ] Integrates with existing OPA evaluation pipeline

##### Task A2.2: Gate G1 — Integration with Initializer Agent (Day 4, 2h)

**Edit**: `backend/app/services/codegen/initializer_agent.py`

After spec parsing, automatically evaluate Gate G1:
```python
async def initialize(self, spec_path, project_id, mode):
    # Step 1: Parse spec
    spec = self._parse_spec(spec_path)

    # Step 2: Validate spec
    validation = await self.validate_spec(spec)

    # Step 3: Evaluate Gate G1 (OPA)
    g1_result = await self.gate_service.evaluate_gate(
        project_id=project_id,
        gate_type="G1_SPEC_REVIEW",
        context={"spec_validation": validation.dict()},
    )

    if not g1_result.passed:
        return InitializationResult(
            success=False,
            gate_g1_passed=False,
            errors=g1_result.errors,
            feature_list=None,
        )

    # Step 4: Generate feature list (only if G1 passes)
    feature_list = await self._generate_feature_list(spec)

    return InitializationResult(
        success=True,
        gate_g1_passed=True,
        feature_list=feature_list,
    )
```

**Acceptance Criteria**:
- [ ] Gate G1 evaluated before feature list generation
- [ ] Failed G1 returns clear error with missing fields
- [ ] Passed G1 proceeds to feature list generation
- [ ] Gate result stored in Evidence Vault

##### Task A2.3: Gate G1 — Evidence Storage (Day 5, 3h)

After Gate G1 evaluation, store results as evidence:
- `feature_list.json` → Evidence Vault (type: `DOCUMENTATION`)
- `spec_validation_report.json` → Evidence Vault (type: `COMPLIANCE`)
- Gate G1 result → Gate Engine (state: EVALUATED → SUBMITTED)

**Acceptance Criteria**:
- [ ] Feature list stored as evidence with SHA256 hash
- [ ] Validation report linked to gate
- [ ] Evidence retrievable via Evidence Vault API

##### Task A2.4: Gate G1 — Integration Tests (Day 5, 3h)

**Create**: `backend/tests/integration/test_initializer_gate_g1.py`

Test full flow:
1. Upload spec → Initializer Agent → Gate G1 evaluation → Feature list
2. Invalid spec → Gate G1 fails → No feature list generated
3. Spec with warnings → Gate G1 passes with warnings → Feature list generated

**Acceptance Criteria**:
- [ ] Full integration flow tested (spec → G1 → feature_list)
- [ ] Tests use real OPA service (Docker)
- [ ] Tests verify Evidence Vault storage

---

#### Day 6: SASE Templates Static API

**Owner**: Backend Engineer
**Priority**: P1

##### Task A3.1: SASE Templates API Endpoint (Day 6, 4h)

**Option A: Static Template Service** (recommended — no database needed)

SASE templates are **methodology artifacts** from the SDLC Framework, not project-specific data. They should be served statically, following the existing `/api/v1/templates` pattern.

**Create**: `backend/app/schemas/sase_templates.py`

```python
class SASETemplate(BaseModel):
    """SASE artifact template schema."""
    id: str
    name: str
    description: str
    artifact_type: Literal["agents_md", "crp", "mrp", "vcr"]
    maturity_level: Literal["L1", "L2", "L3"]
    badge: str
    badge_variant: str
    template_content: str  # Markdown content
    sections: list[str]

class SASETemplateListResponse(BaseModel):
    templates: list[SASETemplate]
    total: int
```

**Edit**: `backend/app/api/routes/templates.py` (extend existing)

Add endpoint:
```
GET /api/v1/templates/sase-templates
  Query: ?artifact_type=crp|mrp|vcr|agents_md&maturity_level=L1|L2|L3
  Response: SASETemplateListResponse
```

**Template data**: Port the 4 hardcoded templates from `frontend/src/app/app/sase-templates/page.tsx` into a Python constant `SASE_TEMPLATES` (similar to `SDLC_STAGES` pattern).

**Acceptance Criteria**:
- [ ] API returns all 4 SASE templates (AGENTS.md, CRP, MRP, VCR)
- [ ] Filtering by `artifact_type` works
- [ ] Filtering by `maturity_level` works
- [ ] Response time <100ms
- [ ] Template content includes full Markdown

##### Task A3.2: SASE Templates API Tests (Day 6, 2h)

**Create**: `backend/tests/unit/test_sase_templates_api.py`

Test cases:
1. List all templates → returns 4
2. Filter by artifact_type=crp → returns 1
3. Filter by maturity_level=L1 → returns correct subset
4. Invalid filter → returns empty list (not error)

---

#### Day 7: Browser Agent Production Hardening

**Owner**: Backend Engineer
**Priority**: P1

##### Task A4.1: Browser Agent — Retry Logic + Evidence Capture (Day 7, 6h)

**Edit**: `backend/app/services/browser_agent_service.py`

Current state: Prototype (Sprint 174, ~250 LOC) with basic Playwright methods.

Enhancements:
1. **Retry logic**: Retry failed actions up to 3 times with exponential backoff
2. **Screenshot on failure**: Capture screenshot when an action fails
3. **Evidence capture**: Upload screenshots and page states to Evidence Vault
4. **Timeout handling**: Configurable per-action timeouts (default: 30s)
5. **Multi-step flow orchestration**: Execute a sequence of actions with rollback

```python
class BrowserAgentService:
    """Production browser agent with retry + evidence capture."""

    async def execute_flow(
        self,
        steps: list[BrowserAction],
        project_id: UUID,
        evidence_gate_id: Optional[UUID] = None,
        max_retries: int = 3,
    ) -> FlowResult:
        """Execute multi-step browser flow with evidence capture."""
```

**Acceptance Criteria**:
- [ ] Retry logic works (3 retries with backoff)
- [ ] Screenshots captured on failure
- [ ] Evidence uploaded to MinIO via Evidence Vault API
- [ ] Multi-step flows execute sequentially with rollback on failure
- [ ] Timeouts prevent hung browser sessions

---

#### Days 8-9: Integration Testing + Regression Check

**Owner**: Backend Engineer
**Priority**: P0

##### Task A5.1: Initializer Agent Integration Test (Day 8, 4h)

Full end-to-end test:
1. Create project via API
2. Upload specification (App Builder blueprint)
3. Run Initializer Agent
4. Verify Gate G1 evaluation
5. Verify feature_list.json in Evidence Vault
6. Verify gate state transitions

##### Task A5.2: Regression Test Suite (Day 9, 4h)

Run full backend test suite:
```bash
DATABASE_URL="postgresql://test:test@localhost:15432/sdlc_test" \
  python -m pytest backend/tests/ -v --tb=short
```

Fix any regressions introduced by Sprint 176 changes.

---

#### Day 10: Documentation + Sprint Close

**Owner**: Backend Engineer
**Priority**: P0

##### Task A6.1: Update CLAUDE.md Module Zones (Day 10, 2h)

Add Initializer Agent to Module 4 (EP-06 Codegen Pipeline) in `CLAUDE.md`:
- New service file reference
- CLI command reference
- Gate G1 integration notes

##### Task A6.2: Sprint Documentation (Day 10, 1h)

Update `CURRENT-SPRINT.md` with Sprint 176 completion status.

---

### Track B: Frontend + Docs

#### Day 1: E2E Test Setup

**Owner**: Frontend Engineer
**Priority**: P1

##### Task B1.1: E2E Test Infrastructure for Sprint 175 Pages (Day 1, 4h)

**Create**: `frontend/e2e/sprint-175/` directory

Set up test fixtures:
- Auth fixture (login before tests)
- Navigation fixture (navigate to each page)
- API mock fixture (optional, for offline testing)

**File structure**:
```
frontend/e2e/sprint-175/
├── ceo-dashboard.spec.ts
├── mcp-analytics.spec.ts
├── planning.spec.ts
├── plan-review.spec.ts
├── learnings.spec.ts
├── sase-templates.spec.ts
└── fixtures/
    └── auth.ts
```

---

#### Days 2-3: E2E Tests — P0 Pages

**Owner**: Frontend Engineer
**Priority**: P1

##### Task B2.1: CEO Dashboard E2E Test (Day 2, 3h)

**Create**: `frontend/e2e/sprint-175/ceo-dashboard.spec.ts`

Test scenarios:
1. Page loads with all metric cards visible
2. Pending decisions table renders
3. Resolve decision action works
4. Time-saved trend chart renders
5. System health section shows status
6. Export button downloads file

##### Task B2.2: MCP Analytics E2E Test (Day 2, 3h)

**Create**: `frontend/e2e/sprint-175/mcp-analytics.spec.ts`

Test scenarios:
1. Page loads with provider dashboard
2. Time range selector changes data
3. Cost breakdown section renders
4. Latency metrics chart renders
5. Provider health indicators show correct status

##### Task B2.3: Planning E2E Test (Day 3, 6h)

**Create**: `frontend/e2e/sprint-175/planning.spec.ts`

Test scenarios:
1. Page loads with hierarchy tree
2. Create roadmap → appears in list
3. Add phase to roadmap → nested display
4. Add sprint to phase → nested display
5. Delete roadmap → removed from list
6. Edit roadmap name → updated inline

---

#### Days 4-5: E2E Tests — P1 Pages

**Owner**: Frontend Engineer
**Priority**: P1

##### Task B3.1: Plan Review E2E Test (Day 4, 3h)

**Create**: `frontend/e2e/sprint-175/plan-review.spec.ts`

Test scenarios:
1. Session list loads
2. Create new session
3. Navigate to detail page (`/plan-review/[id]`)
4. Approve session → status changes
5. Back navigation works

##### Task B3.2: Learnings E2E Test (Day 4, 3h)

**Create**: `frontend/e2e/sprint-175/learnings.spec.ts`

Test scenarios:
1. Learning list loads with filters
2. Apply learning action works
3. Delete learning with confirmation
4. Category filter changes results
5. Export button works

##### Task B3.3: SASE Templates E2E Test (Day 5, 3h)

**Create**: `frontend/e2e/sprint-175/sase-templates.spec.ts`

Test scenarios:
1. Template list loads (4 templates)
2. Template preview modal opens
3. Copy to clipboard works
4. Download as markdown works
5. Category filter works

---

#### Day 6: SASE Templates Frontend — Connect to Backend API

**Owner**: Frontend Engineer
**Priority**: P1

##### Task B4.1: Create useSASETemplates Hook (Day 6, 2h)

**Create**: `frontend/src/hooks/useSASETemplates.ts`

```typescript
import { useQuery } from "@tanstack/react-query";
import { apiClient } from "@/lib/apiClient";

interface SASETemplate {
  id: string;
  name: string;
  description: string;
  artifact_type: "agents_md" | "crp" | "mrp" | "vcr";
  maturity_level: "L1" | "L2" | "L3";
  badge: string;
  badge_variant: string;
  template_content: string;
  sections: string[];
}

export function useSASETemplates(filters?: {
  artifact_type?: string;
  maturity_level?: string;
}) {
  return useQuery({
    queryKey: ["sase-templates", filters],
    queryFn: () => apiClient.get("/templates/sase-templates", { params: filters }),
    staleTime: 10 * 60 * 1000, // 10 min (templates rarely change)
  });
}
```

##### Task B4.2: Refactor SASE Templates Page — Replace Hardcoded Data (Day 6, 4h)

**Edit**: `frontend/src/app/app/sase-templates/page.tsx`

Replace the hardcoded `SASE_TEMPLATES` array with `useSASETemplates()` hook:
- Remove ~200 LOC of static template data
- Add loading skeleton
- Add error state
- Keep copy/download/preview functionality

**Acceptance Criteria**:
- [ ] Page loads templates from backend API
- [ ] Loading skeleton shown during fetch
- [ ] Error state with retry button
- [ ] All existing functionality preserved (copy, download, preview)
- [ ] Filter by artifact type works via API query param

---

#### Days 7-8: Pilot Onboarding Runbook

**Owner**: Frontend Engineer / PM
**Priority**: P2

##### Task B5.1: Vietnamese SME Pilot Onboarding Runbook (Day 7-8, 8h)

**Create**: `docs/06-deploy/pilot-onboarding-runbook.md`

Sections:
1. **Pre-Flight Checklist** — Verify backend, frontend, CLI all running
2. **Customer Account Setup** — Create org, invite users, assign roles
3. **Project Initialization** — `sdlcctl init` with Vietnamese domain template
4. **First Gate Evaluation** — Walk through G0.1 → G0.2 → G1
5. **Evidence Submission** — Upload first evidence via Web/CLI/Extension
6. **Dashboard Tour** — CEO Dashboard, Gates, Planning, Learnings
7. **Troubleshooting Guide** — Common issues and fixes
8. **Success Metrics** — What "pilot success" looks like (adoption, TTFV, satisfaction)

**Bilingual**: Key sections in both English and Vietnamese.

**Acceptance Criteria**:
- [ ] Runbook covers full customer journey (signup → first value)
- [ ] Step-by-step with screenshots
- [ ] Estimated time per section
- [ ] Total onboarding: <30 min to first gate evaluation

---

#### Day 9: Cross-Track Integration Testing

**Owner**: Frontend + Backend Engineers
**Priority**: P0

##### Task B6.1: SASE Templates End-to-End Verification (Day 9, 2h)

Verify the full chain:
1. Backend serves templates via API
2. Frontend fetches and displays templates
3. Filter functionality works end-to-end
4. E2E test passes with real API (not mocked)

##### Task B6.2: Initializer Agent Demo (Day 9, 2h)

Prepare demo for CTO review:
1. Create sample blueprint (Vietnamese E-commerce)
2. Run `sdlcctl codegen init --spec ecommerce-blueprint.yaml`
3. Show Gate G1 evaluation result
4. Show feature_list.json output
5. Show evidence in Evidence Vault

---

#### Day 10: Final QA + Sprint Documentation

**Owner**: Frontend Engineer
**Priority**: P0

##### Task B7.1: Full Regression — Frontend (Day 10, 3h)

```bash
cd frontend && npx tsc --noEmit    # TypeScript
cd frontend && npm run build        # Build
cd frontend && npx playwright test  # E2E tests
```

##### Task B7.2: Sprint Completion Report (Day 10, 1h)

Create `SPRINT-176-COMPLETION-REPORT.md` with results, metrics, and Sprint 177 handoffs.

---

## File Changes Summary

| Day | Track | Action | File |
|-----|-------|--------|------|
| 1-3 | A | CREATE | `backend/app/services/codegen/initializer_agent.py` |
| 3 | A | EDIT | `backend/sdlcctl/sdlcctl/commands/codegen.py` |
| 3 | A | EDIT | `backend/app/api/routes/codegen.py` |
| 3 | A | CREATE | `backend/tests/unit/test_initializer_agent.py` |
| 4 | A | CREATE | `backend/policy-packs/rego/gates/g1_spec_review.rego` |
| 5 | A | CREATE | `backend/tests/integration/test_initializer_gate_g1.py` |
| 6 | A | CREATE | `backend/app/schemas/sase_templates.py` |
| 6 | A | EDIT | `backend/app/api/routes/templates.py` |
| 6 | A | CREATE | `backend/tests/unit/test_sase_templates_api.py` |
| 7 | A | EDIT | `backend/app/services/browser_agent_service.py` |
| 1-5 | B | CREATE | `frontend/e2e/sprint-175/*.spec.ts` (6 files) |
| 6 | B | CREATE | `frontend/src/hooks/useSASETemplates.ts` |
| 6 | B | EDIT | `frontend/src/app/app/sase-templates/page.tsx` |
| 7-8 | B | CREATE | `docs/06-deploy/pilot-onboarding-runbook.md` |
| 10 | A | EDIT | `CLAUDE.md` (Module 4 update) |
| 10 | Both | EDIT | `docs/04-build/02-Sprint-Plans/CURRENT-SPRINT.md` |

---

## Risk Register

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| Initializer Agent spec parsing fails on complex blueprints | HIGH | MEDIUM | Start with App Builder format (known schema), extend later |
| OPA Gate G1 policy too strict / too lenient | MEDIUM | MEDIUM | Calibrate against 5 sample specs on Day 5 |
| Browser Agent Playwright flaky in CI | MEDIUM | HIGH | Use `--retries=2` flag, screenshot-on-failure for debugging |
| E2E tests fail due to Sprint 175 pages still in progress | HIGH | LOW | Sprint 175 must be complete before Sprint 176 starts |
| Ollama unavailable for spec analysis | LOW | LOW | Multi-provider fallback (Claude → Rule-based) already exists |

---

## Dependencies

| Dependency | Owner | Status |
|------------|-------|--------|
| Sprint 175 complete (6 pages in sidebar) | Frontend Engineer | Sprint 175 |
| ADR-055 approved | CTO | APPROVED (Sprint 174) |
| Framework doc: 11-AUTONOMOUS-CODEGEN-PATTERNS.md | Framework | COMPLETE (Sprint 174) |
| OPA running (port 8185) | DevOps | READY |
| Ollama running (port 11434) | DevOps | READY |
| Playwright installed in frontend | Frontend | READY |
| App Builder blueprint format documented | Backend | READY |

---

## Definition of Done

- [ ] Initializer Agent parses specs and generates `feature_list.json`
- [ ] Gate G1 blocks coding if spec is incomplete
- [ ] Gate G1 results stored as evidence in Evidence Vault
- [ ] CLI `sdlcctl codegen init` works end-to-end
- [ ] SASE Templates API returns 4 templates with filtering
- [ ] Frontend SASE page loads from API (no hardcoded data)
- [ ] 6 E2E Playwright tests pass for Sprint 175 pages
- [ ] Browser Agent has retry logic + screenshot-on-failure
- [ ] Pilot onboarding runbook created (Vietnamese SME)
- [ ] All existing tests pass (0 regressions)
- [ ] `npx tsc --noEmit` passes
- [ ] `npm run build` passes
- [ ] CTO demo of Initializer Agent completed

---

## Sprint Metrics

| Metric | Target |
|--------|--------|
| New backend services | 1 (Initializer Agent) |
| New OPA policies | 1 (g1_spec_review.rego) |
| New API endpoints | 2 (codegen init + SASE templates) |
| New E2E tests | 6 (Sprint 175 pages) |
| Backend test coverage | >95% on new code |
| Frontend build | PASS |
| TypeScript errors | 0 |
| Regression tests | 0 failures |

---

## Sprint 177 Handoffs

After Sprint 176, the following will be ready for Sprint 177:

1. **Initializer Agent** → feeds `feature_list.json` to Coding Agent
2. **Gate G1** → validated, Coding Agent can rely on pre-validated specs
3. **Browser Agent** → production-ready for E2E test execution in Gate G3
4. **Evidence pipeline** → stores Initializer artifacts, ready for Coding Agent evidence
5. **E2E infrastructure** → test patterns established for Sprint 177 autonomous codegen tests

**Sprint 177 Scope**: Coding Agent Loop + Gates G2/G3 (ADR-055 Phase 2)

---

*Sprint 176 — "Autonomous Codegen & Pilot Prep"*
*SDLC Orchestrator Team*
*March 17-28, 2026*
