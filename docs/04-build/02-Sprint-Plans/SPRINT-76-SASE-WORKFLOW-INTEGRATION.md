# Sprint 76: SASE Workflow Integration & Team Context

**Sprint ID:** S76
**Status:** 📐 DESIGN COMPLETE (Pending G-Sprint Approval)
**Duration:** 5 days (January 27-31, 2026)
**Goal:** Complete Team-Sprint Integration for SASE Workflows + AI Sprint Assistant Foundation
**Story Points:** 36 SP
**Framework Reference:** SDLC 5.1.3 P5 (SASE Integration)
**Prerequisite:** Sprint 75 ✅ (Planning API Validation Complete)
**Technical Design:** [SPRINT-76-TECHNICAL-DESIGN.md](SPRINT-76-TECHNICAL-DESIGN.md) ✅ (1,105 lines)

---

## 🎯 Sprint 76 Objectives

### Primary Goals (P0)

1. **GAP 2 Resolution** - Backlog assignee team membership validation
2. **GAP 3 Resolution** - Sprint team context for SASE workflows
3. **SASE-Sprint Integration** - Link SASE approval workflows to sprint context

### Secondary Goals (P1)

4. **AI Sprint Assistant** - Foundation for AI-powered sprint recommendations
5. **Sprint Analytics** - Velocity, burndown, completion metrics
6. **Performance Optimization** - Query optimization for planning endpoints

---

## ✅ Sprint 75 Handoff

### Completed (Sprint 75)

| Feature | Status | Tests |
|---------|--------|-------|
| Team role authorization (GAP 1) | ✅ Complete | 88 tests |
| Planning API endpoints | ✅ Complete | 22 endpoints |
| Sprint Dashboard UI | ✅ Complete | 7 components |
| Backlog Kanban Board | ✅ Complete | List + Kanban views |

### Gaps to Resolve (Sprint 76)

| GAP | Description | Priority |
|-----|-------------|----------|
| GAP 2 | Backlog assignee must be team member | P0 |
| GAP 3 | SASE workflows need sprint team context | P0 |

---

## 📋 Sprint 76 Backlog

### Day 1: Backlog Assignee Validation (8 SP) - GAP 2

| Task | Owner | Est | Priority | Status |
|------|-------|-----|----------|--------|
| Add `validate_assignee_membership()` to BacklogService | Backend | 2h | P0 | ⏳ |
| Update BacklogItem create/update with team check | Backend | 2h | P0 | ⏳ |
| Integration tests for assignee validation (12 tests) | Backend | 3h | P0 | ⏳ |
| Frontend: Show only team members in assignee dropdown | Frontend | 2h | P1 | ⏳ |

**Implementation:**

```python
# backend/app/services/backlog_service.py
async def validate_assignee_membership(
    self,
    sprint_id: UUID,
    assignee_id: UUID,
) -> bool:
    """
    Validate that assignee is a member of the sprint's project team.
    
    GAP 2 Resolution: Ensures backlog items can only be assigned
    to users who are members of the project team.
    """
    sprint = await self.sprint_repo.get(sprint_id)
    if not sprint:
        raise ValueError("Sprint not found")
    
    project = sprint.phase.roadmap.project
    if not project.team_id:
        # No team = allow any assignee (legacy behavior)
        return True
    
    team_member = await self.team_repo.get_member(
        team_id=project.team_id,
        user_id=assignee_id
    )
    
    if not team_member:
        raise PermissionError(
            f"User {assignee_id} is not a member of project team"
        )
    
    return True
```

### Day 2: SASE Sprint Context (8 SP) - GAP 3

| Task | Owner | Est | Priority | Status |
|------|-------|-----|----------|--------|
| Add `sprint_id` to SASEApprovalRequest schema | Backend | 1h | P0 | ⏳ |
| Create `SprintContextProvider` for SASE workflows | Backend | 3h | P0 | ⏳ |
| Update SASE policy evaluation with sprint context | Backend | 2h | P0 | ⏳ |
| Integration tests for SASE-Sprint (10 tests) | Backend | 3h | P0 | ⏳ |

**Implementation:**

```python
# backend/app/services/sase_integration.py
class SprintContextProvider:
    """
    Provides sprint context to SASE approval workflows.
    
    GAP 3 Resolution: SASE policies can now access:
    - Sprint team members and roles
    - Sprint phase and roadmap context
    - Sprint gate status
    """
    
    async def get_sprint_context(
        self,
        sprint_id: UUID,
    ) -> SprintContext:
        """Get sprint context for SASE policy evaluation."""
        sprint = await self.sprint_repo.get_with_relations(sprint_id)
        
        return SprintContext(
            sprint_id=sprint.id,
            sprint_number=sprint.number,
            project_id=sprint.project_id,
            team_id=sprint.project.team_id,
            team_members=[
                TeamMemberContext(
                    user_id=m.user_id,
                    role=m.role,
                    can_approve_gates=m.can_approve_sprint_gate(),
                )
                for m in sprint.project.team.members
            ] if sprint.project.team else [],
            phase=PhaseContext(
                id=sprint.phase_id,
                name=sprint.phase.name,
                roadmap_id=sprint.phase.roadmap_id,
            ),
            gates={
                "g_sprint": sprint.g_sprint_status,
                "g_sprint_close": sprint.g_sprint_close_status,
            },
        )

# backend/app/schemas/sase.py - Updated
class SASEApprovalRequest(BaseModel):
    """SASE approval request with sprint context."""
    resource_type: str
    resource_id: UUID
    action: str
    requester_id: UUID
    sprint_id: Optional[UUID] = None  # NEW: Sprint context
    
    # Computed from sprint context
    team_context: Optional[TeamContext] = None
```

### Day 3: SASE Policy Updates (6 SP)

| Task | Owner | Est | Priority | Status |
|------|-------|-----|----------|--------|
| Update `deploy_to_staging` policy with sprint check | Backend | 2h | P0 | ⏳ |
| Update `code_review` policy with team context | Backend | 2h | P0 | ⏳ |
| Create sprint-aware OPA policies | Backend | 3h | P1 | ⏳ |
| Policy evaluation tests (8 tests) | Backend | 2h | P0 | ⏳ |

**OPA Policy Example:**

```rego
# policy-packs/rego/sprint_policies.rego
package sdlc.sprint

import future.keywords.if
import future.keywords.in

# Deploy to staging requires G-Sprint approval
deploy_allowed if {
    input.sprint_context.gates.g_sprint == "approved"
    input.requester_id in sprint_team_members
}

# Code review requires team membership
code_review_allowed if {
    input.sprint_context != null
    input.requester_id in sprint_team_members
}

sprint_team_members := {m.user_id | m := input.sprint_context.team_members[_]}
```

### Day 4: AI Sprint Assistant Foundation (8 SP)

| Task | Owner | Est | Priority | Status |
|------|-------|-----|----------|--------|
| Create `SprintAssistantService` | Backend | 3h | P1 | ⏳ |
| Sprint velocity calculation | Backend | 2h | P1 | ⏳ |
| Backlog prioritization suggestions | Backend | 2h | P1 | ⏳ |
| Sprint health indicators | Backend | 2h | P1 | ⏳ |

**Implementation:**

```python
# backend/app/services/sprint_assistant.py
class SprintAssistantService:
    """
    AI-powered sprint recommendations and analytics.
    
    Features:
    - Velocity calculation from historical data
    - Backlog prioritization suggestions
    - Sprint health indicators
    - Risk identification
    """
    
    async def calculate_velocity(
        self,
        project_id: UUID,
        sprint_count: int = 5,
    ) -> VelocityMetrics:
        """Calculate average velocity from last N sprints."""
        completed_sprints = await self.sprint_repo.get_completed(
            project_id=project_id,
            limit=sprint_count,
        )
        
        if not completed_sprints:
            return VelocityMetrics(
                average=0,
                trend="unknown",
                confidence=0,
            )
        
        velocities = [
            sum(item.story_points for item in s.backlog_items if item.status == "done")
            for s in completed_sprints
        ]
        
        return VelocityMetrics(
            average=sum(velocities) / len(velocities),
            trend=self._calculate_trend(velocities),
            confidence=min(len(velocities) / sprint_count, 1.0),
            history=velocities,
        )
    
    async def get_sprint_health(
        self,
        sprint_id: UUID,
    ) -> SprintHealth:
        """
        Calculate sprint health indicators.
        
        Returns:
        - completion_rate: % of story points completed
        - blocked_items: Count of blocked backlog items
        - risk_level: low/medium/high based on metrics
        """
        sprint = await self.sprint_repo.get_with_backlog(sprint_id)
        
        total_points = sum(i.story_points or 0 for i in sprint.backlog_items)
        completed_points = sum(
            i.story_points or 0 
            for i in sprint.backlog_items 
            if i.status == "done"
        )
        blocked_count = sum(
            1 for i in sprint.backlog_items 
            if i.status == "blocked"
        )
        
        completion_rate = completed_points / total_points if total_points > 0 else 0
        
        # Risk calculation
        days_elapsed = (datetime.utcnow() - sprint.start_date).days
        days_total = (sprint.end_date - sprint.start_date).days
        expected_completion = days_elapsed / days_total if days_total > 0 else 0
        
        risk_level = "low"
        if completion_rate < expected_completion - 0.2:
            risk_level = "high"
        elif completion_rate < expected_completion - 0.1:
            risk_level = "medium"
        
        return SprintHealth(
            completion_rate=completion_rate,
            completed_points=completed_points,
            total_points=total_points,
            blocked_count=blocked_count,
            risk_level=risk_level,
            days_remaining=(sprint.end_date - datetime.utcnow()).days,
        )
    
    async def suggest_priorities(
        self,
        sprint_id: UUID,
    ) -> List[PrioritySuggestion]:
        """
        AI-powered backlog prioritization suggestions.
        
        Factors considered:
        - Business value (P0 > P1 > P2)
        - Dependencies
        - Team capacity
        - Historical completion rates
        """
        sprint = await self.sprint_repo.get_with_backlog(sprint_id)
        velocity = await self.calculate_velocity(sprint.project_id)
        
        suggestions = []
        
        # P0 items should be started first
        p0_not_started = [
            i for i in sprint.backlog_items
            if i.priority == "P0" and i.status == "todo"
        ]
        if p0_not_started:
            suggestions.append(PrioritySuggestion(
                type="start_p0",
                message=f"{len(p0_not_started)} P0 items not started",
                items=[i.id for i in p0_not_started],
                severity="warning",
            ))
        
        # Check if sprint is overloaded
        total_points = sum(i.story_points or 0 for i in sprint.backlog_items)
        if velocity.average > 0 and total_points > velocity.average * 1.2:
            suggestions.append(PrioritySuggestion(
                type="overloaded",
                message=f"Sprint has {total_points} SP, velocity is {velocity.average:.0f}",
                severity="warning",
            ))
        
        return suggestions
```

### Day 5: Sprint Analytics Dashboard & Completion (6 SP)

| Task | Owner | Est | Priority | Status |
|------|-------|-----|----------|--------|
| Sprint analytics API endpoints | Backend | 2h | P1 | ⏳ |
| Velocity chart component | Frontend | 2h | P1 | ⏳ |
| Sprint health widget | Frontend | 2h | P1 | ⏳ |
| Integration tests (10 tests) | Backend | 2h | P0 | ⏳ |
| Sprint 76 completion docs | PM | 1h | P0 | ⏳ |

**API Endpoints:**

```yaml
# New Analytics Endpoints
/planning/projects/{project_id}/velocity:
  get:
    summary: Get project velocity metrics
    tags: [Planning, Analytics]
    
/planning/sprints/{sprint_id}/health:
  get:
    summary: Get sprint health indicators
    tags: [Planning, Analytics]
    
/planning/sprints/{sprint_id}/suggestions:
  get:
    summary: Get AI prioritization suggestions
    tags: [Planning, AI]
```

---

## 🔒 Definition of Done

### Code Complete

- [ ] GAP 2: Backlog assignee team membership validation
- [ ] GAP 3: SASE workflows with sprint team context
- [ ] Sprint Assistant service with velocity/health metrics
- [ ] Analytics dashboard components

### Tests

- [ ] `pytest backend/tests/integration/test_sase_sprint_*.py` passes
- [ ] Assignee validation tests (12+ tests)
- [ ] SASE policy tests (10+ tests)
- [ ] Analytics tests (10+ tests)
- [ ] Total: 32+ new tests

### Documentation

- [ ] OpenAPI spec updated with analytics endpoints
- [ ] SASE-Sprint integration guide
- [ ] Sprint 76 completion report

### Review

- [ ] Code review approved by Tech Lead
- [ ] PR merged to main
- [ ] Staging deployment verified

---

## 📊 Metrics & Success Criteria

| Metric | Target | Notes |
|--------|--------|-------|
| Integration Tests | 32+ | SASE-Sprint + Analytics |
| GAP Resolution | 2/2 | GAP 2 + GAP 3 |
| API Response Time | <100ms p95 | Analytics queries |
| Test Coverage | 90%+ | SASE integration module |

---

## 🔗 Dependencies & Risks

### Dependencies

| Dependency | Status | Owner |
|------------|--------|-------|
| Sprint 75 Complete | ✅ Complete | Backend |
| Teams Feature | ✅ Complete | Backend |
| Planning Hierarchy | ✅ Complete | Backend |
| SASE Foundation | ✅ Complete | Backend |

### Risks

| Risk | Impact | Mitigation |
|------|--------|------------|
| SASE policy complexity | Medium | Start with simple policies, iterate |
| Analytics performance | Low | Use database aggregations |
| AI suggestions accuracy | Low | Start with rule-based, add ML later |

---

## 📝 SDLC 5.1.3 Compliance

| Pillar | Sprint 76 Implementation |
|--------|--------------------------|
| P2 (Sprint Planning) | Velocity/health metrics |
| P5 (SASE Integration) | Sprint context in workflows |
| P3 (4-Tier Classification) | Team role validation |

---

## 🚀 Handoff to Sprint 77

### Expected Completion (Sprint 76)

- ✅ GAP 2: Assignee validation
- ✅ GAP 3: SASE-Sprint integration
- ✅ Sprint Assistant foundation
- ✅ Analytics dashboard

### Future Sprints (Sprint 77+)

- ⏳ AI Council integration with sprint context
- ⏳ Burndown charts and forecasting
- ⏳ Sprint retrospective automation
- ⏳ Cross-project sprint coordination

---

**SDLC 5.1.3 | Sprint 76 | Stage 04 (BUILD)**

*G-Sprint Approval Required Before Sprint Start*
