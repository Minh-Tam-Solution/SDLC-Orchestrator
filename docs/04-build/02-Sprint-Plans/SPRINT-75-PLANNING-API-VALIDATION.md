# Sprint 75: Planning API Validation & Team Authorization

**Sprint ID:** S75
**Status:** 🔄 IN PROGRESS (Day 2 Complete)
**Duration:** 5 days (January 20-24, 2026)
**Goal:** Complete Team Role Authorization for Sprint Gates + Planning API Testing
**Story Points:** 34 SP
**Framework Reference:** SDLC 5.1.3 Sprint Planning Governance
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

**SDLC 5.1.3 Rules Tested:**
- ✅ Rule #1 - Sprint numbers immutable: `test_update_sprint_number_immutable`, `test_create_sprint_duplicate_number_fails`
- ✅ Rule #2 - 24h documentation: `test_g_sprint_close_requires_24h_documentation`
- ✅ SE4H Coach Rule - Team admin gate approval: `test_submit_g_sprint_gate_admin_success`, `test_submit_g_sprint_gate_member_rejected`

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
└── test_planning_backlog.py     # (Sprint 75 Day 3)
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

### Day 3: Backlog API & OpenAPI Documentation (6 SP)

| Task | Owner | Est | Priority | Status |
|------|-------|-----|----------|--------|
| Backlog API tests (10 tests) | Backend | 3h | P0 | ⏳ |
| Bulk operations tests (5 tests) | Backend | 2h | P1 | ⏳ |
| Update OpenAPI spec with Planning endpoints | Backend | 2h | P0 | ⏳ |
| Generate API documentation | Backend | 1h | P1 | ⏳ |

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
        **SDLC 5.1.3 Rule #3**: Sprint planning requires approval
```

### Day 4: Sprint Dashboard UI Foundation (6 SP)

| Task | Owner | Est | Priority | Status |
|------|-------|-----|----------|--------|
| Create `/dashboard/sprints` route | Frontend | 2h | P1 | ⏳ |
| Sprint list component | Frontend | 2h | P1 | ⏳ |
| Sprint detail component | Frontend | 2h | P1 | ⏳ |
| G-Sprint gate approval UI | Frontend | 2h | P1 | ⏳ |

**Component Structure:**

```
frontend/web/src/
├── pages/
│   └── dashboard/
│       └── sprints/
│           ├── page.tsx           # Sprint list
│           └── [sprintId]/
│               └── page.tsx       # Sprint detail
├── components/
│   └── sprints/
│       ├── SprintCard.tsx         # Sprint summary card
│       ├── SprintGatePanel.tsx    # G-Sprint approval panel
│       ├── SprintTimeline.tsx     # Visual timeline
│       └── SprintBacklog.tsx      # Backlog items list
└── hooks/
    └── useSprints.ts              # TanStack Query hooks
```

### Day 5: Backlog Board & Sprint Close (6 SP)

| Task | Owner | Est | Priority | Status |
|------|-------|-----|----------|--------|
| Backlog Kanban board component | Frontend | 3h | P1 | ⏳ |
| G-Sprint-Close approval UI | Frontend | 2h | P1 | ⏳ |
| Code review & merge | Tech Lead | 2h | P0 | ⏳ |
| Sprint 75 completion docs | PM | 1h | P0 | ⏳ |

---

## 🔒 Definition of Done

### Code Complete

- [ ] All team authorization code implemented
- [ ] All Planning API integration tests passing (46+ tests)
- [ ] OpenAPI spec updated with Planning endpoints
- [ ] Sprint Dashboard UI components created

### Tests

- [ ] `pytest backend/tests/integration/test_planning_*.py` passes
- [ ] Team role authorization validated
- [ ] No regression in existing tests (Teams, Auth, etc.)

### Documentation

- [ ] OpenAPI 3.0 spec updated
- [ ] API documentation generated
- [ ] Sprint 75 completion report

### Review

- [ ] Code review approved by Tech Lead
- [ ] PR merged to main
- [ ] Staging deployment verified

---

## 📊 Metrics & Success Criteria

| Metric | Target | Notes |
|--------|--------|-------|
| Integration Tests | 46+ | Planning Hierarchy coverage |
| API Response Time | <100ms p95 | Sprint operations |
| Test Coverage | 90%+ | Planning module |
| Team Auth Gaps Closed | 1/3 | GAP 1 resolved |

---

## 🔗 Dependencies & Risks

### Dependencies

| Dependency | Status | Owner |
|------------|--------|-------|
| Sprint 74 Migration | ✅ Complete | Backend |
| Teams Feature (Sprint 70-73) | ✅ Complete | Backend |
| SDLC 5.1.3 Compliance Guide | ✅ Complete | PM |

### Risks

| Risk | Impact | Mitigation |
|------|--------|------------|
| Complex team authorization logic | Medium | Start with simple role checks, iterate |
| Frontend Sprint UI complexity | Low | Prioritize P0 backend, defer P1 frontend |
| Test coverage gaps | Low | Use TDD approach |

---

## 📝 SDLC 5.1.3 Compliance Checklist

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

**SDLC 5.1.3 | Sprint 75 | Stage 04 (BUILD)**

*G-Sprint Approval Required Before Sprint Start*
