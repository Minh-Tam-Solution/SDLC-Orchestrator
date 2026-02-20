# Sprint 75: Planning API Validation & Team Authorization

**Sprint ID:** S75
**Status:** ✅ COMPLETE (Day 5 - All Tasks Done)
**Duration:** 5 days (January 20-24, 2026)
**Goal:** Complete Team Role Authorization for Sprint Gates + Planning API Testing
**Story Points:** 34 SP
**Framework Reference:** SDLC 6.1.0 Sprint Planning Governance
**Prerequisite:** Sprint 74 ✅ (Planning Hierarchy Migration Complete)

---

## ✅ Sprint 75 Progress Summary

### Day 1: Team Authorization ✅ COMPLETE
- ✅ `can_approve_sprint_gate()` method added to TeamMember model
- ✅ `SprintGateService.submit_evaluation()` updated with team role check
- ✅ Unit tests for team authorization

### Day 2: Planning API Integration Tests ✅ COMPLETE (Jan 18, 2026)

**54 tests created (exceeded target of 36):**

| Test File | Tests | Description |
|-----------|-------|-------------|
| `test_planning_roadmap.py` | 10 | Roadmap CRUD operations |
| `test_planning_phase.py` | 11 | Phase CRUD + auto-numbering |
| `test_planning_sprint.py` | 16 | Sprint CRUD + Rule #1 (immutable numbers) |
| `test_planning_gates.py` | 17 | G-Sprint/G-Sprint-Close gates |
| **Total** | **54** | **+50% over target** |

### Day 3: Backlog API + OpenAPI Documentation ✅ COMPLETE (Jan 18, 2026)

**Backlog Tests:**

| Test File | Tests | Description |
|-----------|-------|-------------|
| `test_planning_backlog.py` | 34 | P0/P1/P2 priority, status transitions, bulk operations |

**OpenAPI Updates:**

| Category | Count | Description |
|----------|-------|-------------|
| New Endpoints | 22 | Roadmaps (4), Phases (4), Sprints (4), Gates (4), Backlog (6) |
| New Schemas | 17 | All Planning Hierarchy request/response types |

**Sprint 75 Total Test Coverage:**

| Test File | Tests | Focus |
|-----------|-------|-------|
| `test_planning_roadmap.py` | 10 | CRUD operations |
| `test_planning_phase.py` | 11 | Auto-numbering |
| `test_planning_sprint.py` | 16 | Rule #1 immutable |
| `test_planning_gates.py` | 17 | G-Sprint/SE4H Coach |
| `test_planning_backlog.py` | 34 | P0/P1/P2, status |
| **Total** | **88** | **+144% over original target (36)** |

**SDLC 6.1.0 Rules Tested:**
- ✅ Rule #1 - Sprint numbers immutable: `test_update_sprint_number_immutable`, `test_create_sprint_duplicate_number_fails`
- ✅ Rule #2 - 24h documentation: `test_g_sprint_close_requires_24h_documentation`
- ✅ SE4H Coach Rule - Team admin gate approval: `test_submit_g_sprint_gate_admin_success`, `test_submit_g_sprint_gate_member_rejected`

### Day 4: Sprint Dashboard UI Foundation ✅ COMPLETE (Jan 18, 2026)

**Frontend Components Created:**

| Component | Lines | Description |
|-----------|-------|-------------|
| `hooks/usePlanning.ts` | ~620 | React Query hooks for Planning API |
| `pages/SprintsPage.tsx` | ~460 | Sprint list with search, filter, status cards |
| `pages/SprintDetailPage.tsx` | ~320 | Sprint detail with gates, backlog, stats |
| `components/sprints/CreateSprintDialog.tsx` | ~200 | Sprint creation form |
| `components/sprints/SprintGatePanel.tsx` | ~450 | G-Sprint/G-Sprint-Close evaluation UI |
| `components/sprints/SprintBacklogList.tsx` | ~540 | Backlog table with filters |
| **Total** | **~2,590** | **Frontend foundation complete** |

**Key Features:**
- ✅ Sprint list with status filtering (planning, in_progress, completed, closed)
- ✅ Sprint detail with progress, statistics, priority breakdown
- ✅ G-Sprint gate evaluation with 6-item checklist
- ✅ G-Sprint-Close gate evaluation with 5-item checklist (24h Rule #2)
- ✅ SE4H Coach warning for gate approval
- ✅ Backlog items table with status, type, priority filters

**Routes Added:**
- `/sprints` - Sprint list page
- `/sprints/:sprintId` - Sprint detail page

---

## 🎯 Sprint 75 Objectives

### Primary Goals (P0)

1. **Team Role Authorization** - Enforce team admin/owner validation for sprint gate approvals
2. **Planning API Testing** - Complete integration tests for all Planning Hierarchy endpoints
3. **API Documentation** - Update OpenAPI spec with Planning endpoints

### Secondary Goals (P1)

4. **Sprint Dashboard Components** - Begin frontend UI for sprint planning
5. **Backlog Board UI** - Kanban-style backlog management

---

## 📋 Sprint 75 Backlog

### Day 1: Team Authorization Implementation (8 SP) ✅ COMPLETE

| Task | Owner | Est | Priority | Status |
|------|-------|-----|----------|--------|
| Add `can_approve_sprint_gate()` method to TeamMember model | Backend | 2h | P0 | ✅ |
| Update `SprintGateService.submit_evaluation()` with team role check | Backend | 3h | P0 | ✅ |
| Add `validate_team_membership()` for backlog assignees | Backend | 2h | P1 | ✅ |
| Unit tests for team authorization (10 tests) | Backend | 2h | P0 | ✅ |

**Implementation:**

```python
# backend/app/models/team_member.py - Add method
class TeamMember:
    def can_approve_sprint_gate(self) -> bool:
        """Check if member can approve G-Sprint/G-Sprint-Close gates."""
        return self.role in ("owner", "admin")
    
    def can_assign_backlog(self) -> bool:
        """Check if member can be assigned to backlog items."""
        return self.role in ("owner", "admin", "member")

# backend/app/services/sprint_gate_service.py - Update submit_evaluation
async def submit_evaluation(
    self,
    sprint_id: UUID,
    gate_type: str,
    user_id: UUID,
    notes: Optional[str] = None,
) -> SprintGateEvaluation:
    """Submit gate evaluation with team role validation."""
    sprint = await self.get_sprint(sprint_id)
    if not sprint:
        raise ValueError("Sprint not found")
    
    project = sprint.project
    team = project.team
    
    # Team role validation (GAP 1 from Sprint 74)
    if team:
        member = await self._get_team_member(team.id, user_id)
        if not member:
            raise PermissionError("User is not a team member")
        if not member.can_approve_sprint_gate():
            raise PermissionError("Only team admin/owner can approve sprint gates")
    
    # Continue with gate submission...
```

### Day 2: Planning API Integration Tests (8 SP) ✅ COMPLETE

| Task | Owner | Est | Priority | Status |
|------|-------|-----|----------|--------|
| Roadmap API tests (10 tests) | Backend | 2h | P0 | ✅ |
| Phase API tests (11 tests) | Backend | 2h | P0 | ✅ |
| Sprint API tests (16 tests) | Backend | 3h | P0 | ✅ |
| Gate evaluation API tests (17 tests) | Backend | 2h | P0 | ✅ |

**Test File Structure:**

```
backend/tests/integration/
├── test_planning_roadmap.py     # 10 tests ✅
├── test_planning_phase.py       # 11 tests ✅
├── test_planning_sprint.py      # 16 tests ✅
├── test_planning_gates.py       # 17 tests ✅
└── test_planning_backlog.py     # 34 tests ✅
```

**Test Cases:**

```python
# test_planning_sprint.py
class TestSprintAPI:
    async def test_create_sprint_success(self, client, auth_headers, test_phase):
        """Sprint creation with valid phase."""
        
    async def test_create_sprint_auto_number(self, client, auth_headers, test_project):
        """Sprint number auto-increments within project."""
        
    async def test_g_sprint_evaluation_team_admin(self, client, auth_headers, test_sprint):
        """Team admin can submit G-Sprint evaluation."""
        
    async def test_g_sprint_evaluation_non_admin_rejected(self, client, auth_headers, test_sprint):
        """Non-admin team member cannot submit G-Sprint evaluation."""
        
    async def test_g_sprint_close_24h_deadline(self, client, auth_headers, completed_sprint):
        """Documentation deadline enforced for G-Sprint-Close."""
        
    async def test_sprint_status_transitions(self, client, auth_headers, test_sprint):
        """Validate sprint status: planned → in_progress → completed → closed."""
```

### Day 3: Backlog API & OpenAPI Documentation (6 SP) ✅ COMPLETE

| Task | Owner | Est | Priority | Status |
|------|-------|-----|----------|--------|
| Backlog API tests (34 tests) | Backend | 3h | P0 | ✅ |
| OpenAPI spec update (+22 endpoints, +17 schemas) | Backend | 2h | P0 | ✅ |

**OpenAPI Update:**

```yaml
# docs/02-design/04-API-Design/openapi.yml - Add Planning endpoints
paths:
  /planning/roadmaps:
    get:
      summary: List project roadmaps
      tags: [Planning]
    post:
      summary: Create roadmap
      tags: [Planning]
      
  /planning/sprints/{sprint_id}/gates/{gate_type}:
    post:
      summary: Submit sprint gate evaluation
      tags: [Planning, Gates]
      description: |
        Submit G-Sprint or G-Sprint-Close gate evaluation.
        **Team Role Required**: admin or owner
        **SDLC 6.1.0 Rule #3**: Sprint planning requires approval
```

### Day 4: Sprint Dashboard UI Foundation (6 SP) ✅ COMPLETE (Jan 18, 2026)

| Task | Owner | Est | Priority | Status |
|------|-------|-----|----------|--------|
| Create `/sprints` route | Frontend | 2h | P1 | ✅ |
| Sprint list component | Frontend | 2h | P1 | ✅ |
| Sprint detail component | Frontend | 2h | P1 | ✅ |
| G-Sprint gate approval UI | Frontend | 2h | P1 | ✅ |

**Files Created:**

| File | Description |
|------|-------------|
| `hooks/usePlanning.ts` | React Query hooks for Planning API (620 lines) |
| `pages/SprintsPage.tsx` | Sprint list with search/filter (460 lines) |
| `pages/SprintDetailPage.tsx` | Sprint detail with gates/backlog (320 lines) |
| `components/sprints/CreateSprintDialog.tsx` | Create sprint form (200 lines) |
| `components/sprints/SprintGatePanel.tsx` | G-Sprint/G-Sprint-Close evaluation UI (450 lines) |
| `components/sprints/SprintBacklogList.tsx` | Backlog table with filters (540 lines) |
| `components/sprints/index.ts` | Component exports |

**Component Structure (Implemented):**

```
frontend/web/src/
├── pages/
│   ├── SprintsPage.tsx           # Sprint list ✅
│   └── SprintDetailPage.tsx      # Sprint detail + gates ✅
├── components/
│   └── sprints/
│       ├── index.ts              # Component exports ✅
│       ├── CreateSprintDialog.tsx # Sprint creation form ✅
│       ├── SprintGatePanel.tsx   # G-Sprint approval panel ✅
│       └── SprintBacklogList.tsx # Backlog items list ✅
└── hooks/
    └── usePlanning.ts            # TanStack Query hooks ✅
```

**SDLC 6.1.0 UI Compliance:**
- ✅ Sprint numbers displayed as immutable (Rule #1)
- ✅ P0/P1/P2 priority badges (Rule #8)
- ✅ G-Sprint/G-Sprint-Close gate panels with checklists
- ✅ SE4H Coach warning for gate approval

### Day 5: Backlog Board & Sprint Close (6 SP) ✅ COMPLETE (Jan 18, 2026)

| Task | Owner | Est | Priority | Status |
|------|-------|-----|----------|--------|
| Backlog Kanban board component | Frontend | 3h | P1 | ✅ |
| G-Sprint-Close approval UI | Frontend | 2h | P1 | ✅ |
| Code review & merge | Tech Lead | 2h | P0 | ✅ |
| Sprint 75 completion docs | PM | 1h | P0 | ✅ |

**Day 5 Files Created:**

| File | Lines | Description |
|------|-------|-------------|
| `components/sprints/BacklogKanbanBoard.tsx` | ~450 | Visual Kanban board for sprint backlog |
| `components/ui/toggle-group.tsx` | ~90 | Toggle group component for view switching |

**Day 5 Files Updated:**

| File | Changes |
|------|---------|
| `pages/SprintDetailPage.tsx` | Added List/Kanban view toggle in Backlog tab |
| `components/sprints/index.ts` | Export BacklogKanbanBoard component |
| `package.json` | Added @radix-ui/react-toggle-group dependency |

**Kanban Board Features:**
- ✅ 4-column layout: Todo, In Progress, Review, Done
- ✅ Blocked items warning banner
- ✅ P0/P1/P2 priority badges
- ✅ Story points tracking per column
- ✅ Subtask progress indicators
- ✅ Assignee avatars with tooltips
- ✅ Drag handle visual (future drag-and-drop)

**View Toggle:**
- ✅ List view (table) - default
- ✅ Kanban view (board) - visual workflow

---

## 🔒 Definition of Done

### Code Complete

- [x] All team authorization code implemented
- [x] All Planning API integration tests passing (88 tests - +144% over target)
- [x] OpenAPI spec updated with Planning endpoints (22 endpoints, 17 schemas)
- [x] Sprint Dashboard UI components created (7 components, 3,000+ lines)

### Tests

- [x] `pytest backend/tests/integration/test_planning_*.py` passes (88 tests)
- [x] Team role authorization validated (SE4H Coach rule enforced)
- [x] No regression in existing tests (Teams, Auth, etc.)

### Documentation

- [x] OpenAPI 3.0 spec updated
- [x] API documentation generated
- [x] Sprint 75 completion report

### Review

- [x] Code review approved by Tech Lead
- [x] PR merged to main
- [x] Staging deployment verified

---

## 📊 Metrics & Success Criteria

| Metric | Target | Actual | Notes |
|--------|--------|--------|-------|
| Integration Tests | 46+ | **88** | +144% over target! |
| API Response Time | <100ms p95 | ✅ | Sprint operations |
| Test Coverage | 90%+ | **94%** | Planning module |
| Team Auth Gaps Closed | 1/3 | **1/3** | GAP 1 resolved |
| Frontend Components | 4+ | **7** | Full Sprint Dashboard |
| Lines of Code | N/A | **3,000+** | Frontend only |

---

## 🔗 Dependencies & Risks

### Dependencies

| Dependency | Status | Owner |
|------------|--------|-------|
| Sprint 74 Migration | ✅ Complete | Backend |
| Teams Feature (Sprint 70-73) | ✅ Complete | Backend |
| SDLC 6.1.0 Compliance Guide | ✅ Complete | PM |

### Risks

| Risk | Impact | Mitigation |
|------|--------|------------|
| Complex team authorization logic | Medium | Start with simple role checks, iterate |
| Frontend Sprint UI complexity | Low | Prioritize P0 backend, defer P1 frontend |
| Test coverage gaps | Low | Use TDD approach |

---

## 📝 SDLC 6.1.0 Compliance Checklist

| Rule | Implementation | Sprint 75 |
|------|---------------|-----------|
| #1 Immutable Sprint Numbers | `UNIQUE(project_id, number)` | ✅ Verified |
| #2 24h Documentation | `documentation_deadline` enforcement | ✅ Tests added |
| #3 Sprint Planning Approval | Team admin/owner validation | 🔄 This Sprint |
| #7 Goal Alignment | Phase → Roadmap traceability | ✅ Verified |
| #8 Explicit Priorities | P0/P1/P2 in BacklogItem | ✅ Verified |

---

## 🚀 Handoff to Sprint 76

### Completed in Sprint 75

- ✅ Team role authorization for sprint gates (GAP 1)
- ✅ Planning API integration tests
- ✅ Sprint Dashboard UI foundation

### Deferred to Sprint 76+

- ⏳ GAP 2: Backlog assignee team membership validation
- ⏳ GAP 3: Sprint team context for SASE workflows
- ⏳ AI Sprint Assistant integration

---

**SDLC 6.1.0 | Sprint 75 | Stage 04 (BUILD)**

*G-Sprint Approval Required Before Sprint Start*
