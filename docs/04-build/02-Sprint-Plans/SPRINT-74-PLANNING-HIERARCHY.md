# Sprint 74: Planning Hierarchy Implementation

**Sprint ID:** S74
**Status:** 🔄 IN PROGRESS
**Duration:** 10 days (February 3-14, 2026)  
**Goal:** Implement full Planning Hierarchy (Roadmap → Phase → Sprint → Backlog) with Sprint Governance Gates per SDLC 5.1.3  
**Story Points:** 55 SP  
**Framework Reference:** SDLC 5.1.3 Sprint Planning Governance

---

## 🎯 Why Planning Hierarchy is Critical

> **Incident Reference:** BFlow Sprint 86 Direction Confusion (January 18, 2026)

### Problem Statement

Without Planning Hierarchy in Orchestrator, teams experience:
- Sprint direction confusion (27-day documentation lag)
- Roadmap inconsistency across documents  
- No sprint approval workflow
- Missing traceability (Sprint → Phase → Roadmap)

### Solution: Full Planning Hierarchy

```
┌────────────────────────────────────────────────────────────────────┐
│               SDLC ORCHESTRATOR PLANNING HIERARCHY                 │
│                                                                    │
│  Level 1: ROADMAP (12 months)                                     │
│  └── Strategic goals, quarterly milestones                        │
│       │                                                            │
│       ▼                                                            │
│  Level 2: PHASE (4-8 weeks)                                       │
│  └── Phase objectives, feature groupings                          │
│       │                                                            │
│       ▼                                                            │
│  Level 3: SPRINT (5-10 days)                                      │
│  └── Sprint goal, committed work, G-Sprint approval               │
│       │                                                            │
│       ▼                                                            │
│  Level 4: BACKLOG (Tasks)                                         │
│  └── User stories, tasks, bugs with assignments                   │
│                                                                    │
│  ═══════════════════════════════════════════════════════════════  │
│  GOVERNANCE: G-Sprint (Planning) + G-Sprint-Close (Completion)    │
└────────────────────────────────────────────────────────────────────┘
```

### SDLC 5.1.3 Alignment

| SDLC 5.1.3 Requirement | Sprint 74 Implementation |
|------------------------|--------------------------|
| G-Sprint Gate | `/api/v1/sprints/{id}/gates/g-sprint/evaluate` |
| G-Sprint-Close Gate | `/api/v1/sprints/{id}/gates/g-sprint-close/evaluate` |
| 10 Golden Rules | Enforced via Sprint model validators |
| Roadmap Change Request | RCR workflow API |
| SSOT Validation | CI/CD script + API endpoint |
| Traceability Chain | Sprint → Phase → Roadmap relationships |

---

## 📋 Sprint Overview

| Attribute | Value |
|-----------|-------|
| Sprint Number | 74 |
| Start Date | February 3, 2026 (Monday) |
| End Date | February 14, 2026 (Friday) |
| Working Days | 10 |
| Story Points | 55 |
| Team Capacity | Backend Dev (10d), Frontend Dev (8d), QA (3d), Tech Lead (2d) |

---

## 🎯 Sprint Goal

> Implement complete Planning Hierarchy with full CRUD operations, Sprint Governance Gates (G-Sprint, G-Sprint-Close), traceability chain, and Planning Dashboard UI to prevent sprint direction confusion.

---

## 📊 Sprint Backlog

### Epic: ADR-013 Planning Hierarchy + SDLC 5.1.3 Sprint Governance

---

### Story 1: Roadmap Model & API (8 SP)

**As a** Project Manager  
**I want** to create and manage roadmaps  
**So that** I can define strategic goals for 12-month planning

| Task ID | Task | Owner | Est | Status |
|---------|------|-------|-----|--------|
| S74-T01 | Create `roadmaps` table migration | Backend Dev | 2h | ⏳ Pending |
| S74-T02 | Create `Roadmap` SQLAlchemy model | Backend Dev | 2h | ✅ Done |
| S74-T03 | Create Roadmap Pydantic schemas | Backend Dev | 1h | ✅ Done |
| S74-T04 | Create `RoadmapService` class | Backend Dev | 3h | ⏳ Pending |
| S74-T05 | Implement `POST /projects/{id}/roadmaps` | Backend Dev | 2h | ✅ Done |
| S74-T06 | Implement `GET /projects/{id}/roadmaps` | Backend Dev | 1h | ✅ Done |
| S74-T07 | Implement `GET /roadmaps/{id}` | Backend Dev | 1h | ✅ Done |
| S74-T08 | Implement `PUT /roadmaps/{id}` | Backend Dev | 1h | ✅ Done |
| S74-T09 | Implement `DELETE /roadmaps/{id}` | Backend Dev | 1h | ✅ Done |
| S74-T10 | Add roadmap unit tests | Backend Dev | 2h | ⏳ Pending |

**Database Schema:**
```sql
CREATE TABLE roadmaps (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    vision TEXT,
    start_date DATE,
    end_date DATE,
    review_cadence VARCHAR(50) DEFAULT 'quarterly', -- monthly, quarterly, yearly
    status VARCHAR(50) DEFAULT 'active', -- draft, active, archived
    created_by UUID REFERENCES users(id),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(project_id, name)
);

CREATE INDEX idx_roadmaps_project ON roadmaps(project_id);
CREATE INDEX idx_roadmaps_status ON roadmaps(status);
```

**Acceptance Criteria:**
- [ ] Roadmap CRUD operations work correctly
- [ ] Only project members can create/edit roadmaps
- [ ] Roadmap deletion cascades to phases
- [ ] Review cadence enforced per SDLC 5.1.3 Rule #10

---

### Story 2: Phase Model & API (6 SP)

**As a** Project Manager  
**I want** to create phases within a roadmap  
**So that** I can group sprints into 4-8 week objectives

| Task ID | Task | Owner | Est | Status |
|---------|------|-------|-----|--------|
| S74-T11 | Create `phases` table migration | Backend Dev | 2h | ⏳ Pending |
| S74-T12 | Create `Phase` SQLAlchemy model | Backend Dev | 2h | ✅ Done |
| S74-T13 | Create Phase Pydantic schemas | Backend Dev | 1h | ✅ Done |
| S74-T14 | Create `PhaseService` class | Backend Dev | 2h | ⏳ Pending |
| S74-T15 | Implement `POST /roadmaps/{id}/phases` | Backend Dev | 1h | ✅ Done |
| S74-T16 | Implement `GET /roadmaps/{id}/phases` | Backend Dev | 1h | ✅ Done |
| S74-T17 | Implement `GET /phases/{id}` | Backend Dev | 1h | ✅ Done |
| S74-T18 | Implement `PUT /phases/{id}` | Backend Dev | 1h | ✅ Done |
| S74-T19 | Implement `DELETE /phases/{id}` | Backend Dev | 1h | ✅ Done |
| S74-T20 | Add phase unit tests | Backend Dev | 2h | ⏳ Pending |

**Database Schema:**
```sql
CREATE TABLE phases (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    roadmap_id UUID NOT NULL REFERENCES roadmaps(id) ON DELETE CASCADE,
    number INTEGER NOT NULL,
    name VARCHAR(255) NOT NULL,
    theme TEXT, -- e.g., "Q1 Foundation"
    objective TEXT, -- Phase goal
    start_date DATE,
    end_date DATE,
    status VARCHAR(50) DEFAULT 'planned', -- planned, active, completed
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(roadmap_id, number)
);

CREATE INDEX idx_phases_roadmap ON phases(roadmap_id);
CREATE INDEX idx_phases_status ON phases(status);
```

**Acceptance Criteria:**
- [ ] Phase numbers are sequential within roadmap
- [ ] Phase dates must be within roadmap dates
- [ ] Phase deletion cascades to sprints
- [ ] Traceability: Phase → Roadmap working

---

### Story 3: Sprint Model & API (10 SP)

**As a** Tech Lead  
**I want** to create sprints within a phase  
**So that** I can plan 5-10 day delivery cycles

| Task ID | Task | Owner | Est | Status |
|---------|------|-------|-----|--------|
| S74-T21 | Create `sprints` table migration | Backend Dev | 3h | ⏳ Pending |
| S74-T22 | Create `Sprint` SQLAlchemy model | Backend Dev | 3h | ✅ Done |
| S74-T23 | Create Sprint Pydantic schemas | Backend Dev | 2h | ✅ Done |
| S74-T24 | Create `SprintService` class | Backend Dev | 4h | ⏳ Pending |
| S74-T25 | Implement `POST /phases/{id}/sprints` | Backend Dev | 2h | ✅ Done |
| S74-T26 | Implement `POST /projects/{id}/sprints` (direct) | Backend Dev | 1h | ✅ Done |
| S74-T27 | Implement `GET /projects/{id}/sprints` | Backend Dev | 1h | ✅ Done |
| S74-T28 | Implement `GET /sprints/{id}` | Backend Dev | 1h | ✅ Done |
| S74-T29 | Implement `PUT /sprints/{id}` | Backend Dev | 2h | ✅ Done |
| S74-T30 | Implement `DELETE /sprints/{id}` | Backend Dev | 1h | ✅ Done |
| S74-T31 | Add sprint unit tests | Backend Dev | 3h | ⏳ Pending |

**Database Schema:**
```sql
CREATE TABLE sprints (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    phase_id UUID REFERENCES phases(id) ON DELETE SET NULL, -- Optional phase
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    number INTEGER NOT NULL,
    name VARCHAR(255) NOT NULL, -- e.g., "Sprint 74: Planning Hierarchy"
    goal TEXT NOT NULL, -- Single sentence sprint goal
    status VARCHAR(50) DEFAULT 'planning', -- planning, active, completed, cancelled
    start_date DATE,
    end_date DATE,
    capacity_points INTEGER, -- Story points capacity
    team_size INTEGER,
    velocity_target INTEGER, -- Target velocity
    
    -- SDLC 5.1.3 Governance
    g_sprint_status VARCHAR(50) DEFAULT 'pending', -- pending, passed, failed
    g_sprint_approved_by UUID REFERENCES users(id),
    g_sprint_approved_at TIMESTAMP,
    g_sprint_close_status VARCHAR(50) DEFAULT 'pending',
    g_sprint_close_approved_by UUID REFERENCES users(id),
    g_sprint_close_approved_at TIMESTAMP,
    documentation_deadline TIMESTAMP, -- 24h business hours from end_date
    
    created_by UUID REFERENCES users(id),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(project_id, number)
);

CREATE INDEX idx_sprints_project ON sprints(project_id);
CREATE INDEX idx_sprints_phase ON sprints(phase_id);
CREATE INDEX idx_sprints_status ON sprints(status);
CREATE INDEX idx_sprints_g_sprint_status ON sprints(g_sprint_status);
```

**SDLC 5.1.3 Validators:**
```python
# Rule #1: Sprint Numbers Are Immutable
# - number field cannot be changed after creation
# - CANCELLED sprints keep their number

# Rule #7: Sprint Goal Must Align with Phase
# - Validate goal contains phase keywords (optional)

# Rule #8: Strategic Priorities Explicit
# - status != 'active' until g_sprint_status = 'passed'
```

**Acceptance Criteria:**
- [ ] Sprint numbers are immutable after creation
- [ ] Sprint cannot start (active) without G-Sprint approval
- [ ] Sprint cannot close without G-Sprint-Close approval
- [ ] Documentation deadline auto-calculated (24h business hours)
- [ ] Cancelled sprints retain number, are not reused

---

### Story 4: Sprint Governance Gates (8 SP) ⭐ CRITICAL

**As a** CTO  
**I want** G-Sprint and G-Sprint-Close gates  
**So that** sprint planning is governed per SDLC 5.1.3

| Task ID | Task | Owner | Est | Status |
|---------|------|-------|-----|--------|
| S74-T32 | Create `sprint_gate_evaluations` table | Backend Dev | 2h | ⏳ Pending |
| S74-T33 | Create `SprintGateEvaluation` model | Backend Dev | 2h | ✅ Done |
| S74-T34 | Create `SprintGateService` class | Backend Dev | 4h | ✅ Done |
| S74-T35 | Implement G-Sprint checklist logic | Backend Dev | 3h | ✅ Done |
| S74-T36 | Implement G-Sprint-Close checklist logic | Backend Dev | 3h | ✅ Done |
| S74-T37 | Implement `POST /sprints/{id}/gates/g-sprint/evaluate` | Backend Dev | 2h | ✅ Done |
| S74-T38 | Implement `POST /sprints/{id}/gates/g-sprint-close/evaluate` | Backend Dev | 2h | ✅ Done |
| S74-T39 | Implement `GET /sprints/{id}/gates` | Backend Dev | 1h | ✅ Done |
| S74-T40 | Add 24h deadline enforcement | Backend Dev | 2h | ✅ Done |
| S74-T41 | Add sprint gate unit tests | Backend Dev | 3h | ⏳ Pending |

**Database Schema:**
```sql
CREATE TABLE sprint_gate_evaluations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    sprint_id UUID NOT NULL REFERENCES sprints(id) ON DELETE CASCADE,
    gate_type VARCHAR(50) NOT NULL, -- 'g_sprint' or 'g_sprint_close'
    status VARCHAR(50) DEFAULT 'pending', -- pending, passed, failed
    checklist JSONB NOT NULL, -- Checklist items with pass/fail
    notes TEXT,
    evaluated_by UUID REFERENCES users(id),
    evaluated_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(sprint_id, gate_type)
);

CREATE INDEX idx_gate_eval_sprint ON sprint_gate_evaluations(sprint_id);
CREATE INDEX idx_gate_eval_type ON sprint_gate_evaluations(gate_type);
```

**G-Sprint Checklist (from SDLC 5.1.3):**
```json
{
  "checklist": {
    "alignment": [
      {"id": "goal_aligns_phase", "label": "Sprint goal aligns with Phase objective", "required": true},
      {"id": "goal_aligns_roadmap", "label": "Sprint goal aligns with Roadmap goal", "required": true},
      {"id": "priorities_explicit", "label": "Priorities explicit (P0/P1/P2 labeled)", "required": true},
      {"id": "no_options_p0", "label": "No 'options' for P0 items", "required": true}
    ],
    "capacity": [
      {"id": "capacity_calculated", "label": "Team capacity calculated", "required": true},
      {"id": "velocity_within", "label": "Story points within velocity (+10% max)", "required": true},
      {"id": "personnel_confirmed", "label": "Key personnel availability confirmed", "required": true},
      {"id": "pto_accounted", "label": "PTO/holidays accounted for", "required": false}
    ],
    "dependencies": [
      {"id": "dependencies_identified", "label": "External dependencies identified", "required": true},
      {"id": "blocker_mitigation", "label": "Blocker mitigation planned", "required": false},
      {"id": "cross_team_scheduled", "label": "Cross-team coordination scheduled", "required": false}
    ],
    "risk": [
      {"id": "risks_identified", "label": "Top 3 risks identified", "required": true},
      {"id": "mitigation_defined", "label": "Mitigation strategies defined", "required": true},
      {"id": "escalation_clear", "label": "Escalation path clear", "required": false}
    ],
    "documentation": [
      {"id": "sprint_doc_created", "label": "SPRINT-XX.md created", "required": true},
      {"id": "dod_agreed", "label": "Definition of Done agreed", "required": true},
      {"id": "events_scheduled", "label": "Sprint events scheduled", "required": true}
    ]
  }
}
```

**G-Sprint-Close Checklist:**
```json
{
  "checklist": {
    "work": [
      {"id": "work_accounted", "label": "All items accounted for (done/carryover)", "required": true},
      {"id": "carryover_documented", "label": "Carryover documented with reason", "required": true},
      {"id": "no_p0_dropped", "label": "No P0 items dropped", "required": true}
    ],
    "quality": [
      {"id": "dod_met", "label": "Definition of Done met", "required": true},
      {"id": "no_p0_bugs", "label": "No P0 bugs shipped", "required": true},
      {"id": "coverage_maintained", "label": "Test coverage maintained", "required": false}
    ],
    "retrospective": [
      {"id": "retro_completed", "label": "Sprint retro completed", "required": true},
      {"id": "actions_assigned", "label": "Action items assigned", "required": true},
      {"id": "improvements_documented", "label": "Improvements documented", "required": false}
    ],
    "metrics": [
      {"id": "velocity_calculated", "label": "Velocity calculated", "required": true},
      {"id": "completion_recorded", "label": "Completion rate recorded", "required": true},
      {"id": "bug_escape_recorded", "label": "Bug escape rate recorded", "required": false}
    ],
    "documentation": [
      {"id": "current_sprint_updated", "label": "CURRENT-SPRINT.md updated", "required": true},
      {"id": "sprint_index_updated", "label": "SPRINT-INDEX.md updated", "required": true},
      {"id": "roadmap_reviewed", "label": "Roadmap reviewed (update if needed)", "required": true},
      {"id": "within_24h", "label": "Documentation within 24 business hours", "required": true}
    ]
  }
}
```

**Acceptance Criteria:**
- [ ] G-Sprint evaluation prevents sprint from starting without approval
- [ ] G-Sprint-Close enforces 24h documentation deadline
- [ ] Failed gate blocks next sprint (per Rule #9)
- [ ] Checklist results stored in JSONB for audit
- [ ] Tier-based approval authority enforced

---

### Story 5: Backlog Item Model & API (5 SP)

**As a** Developer  
**I want** to create backlog items in a sprint  
**So that** I can track user stories, tasks, and bugs

| Task ID | Task | Owner | Est | Status |
|---------|------|-------|-----|--------|
| S74-T42 | Create `backlog_items` table migration | Backend Dev | 2h | ⏳ Pending |
| S74-T43 | Create `BacklogItem` SQLAlchemy model | Backend Dev | 2h | ✅ Done |
| S74-T44 | Create BacklogItem Pydantic schemas | Backend Dev | 1h | ✅ Done |
| S74-T45 | Create `BacklogService` class | Backend Dev | 2h | ⏳ Pending |
| S74-T46 | Implement `POST /sprints/{id}/backlog` | Backend Dev | 1h | ✅ Done |
| S74-T47 | Implement `GET /sprints/{id}/backlog` | Backend Dev | 1h | ✅ Done |
| S74-T48 | Implement `GET /backlog/{id}` | Backend Dev | 1h | ✅ Done |
| S74-T49 | Implement `PUT /backlog/{id}` | Backend Dev | 1h | ✅ Done |
| S74-T50 | Implement `DELETE /backlog/{id}` | Backend Dev | 1h | ✅ Done |
| S74-T51 | Add backlog unit tests | Backend Dev | 2h | ⏳ Pending |

**Database Schema:**
```sql
CREATE TABLE backlog_items (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    sprint_id UUID REFERENCES sprints(id) ON DELETE SET NULL, -- Nullable for backlog
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    type VARCHAR(50) NOT NULL, -- 'story', 'task', 'bug', 'spike'
    title VARCHAR(500) NOT NULL,
    description TEXT,
    acceptance_criteria TEXT,
    priority VARCHAR(10) DEFAULT 'P2', -- P0, P1, P2
    story_points INTEGER,
    status VARCHAR(50) DEFAULT 'todo', -- todo, in_progress, review, done, blocked
    assignee_id UUID REFERENCES users(id),
    parent_id UUID REFERENCES backlog_items(id), -- For subtasks
    labels JSONB DEFAULT '[]',
    created_by UUID REFERENCES users(id),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_backlog_sprint ON backlog_items(sprint_id);
CREATE INDEX idx_backlog_project ON backlog_items(project_id);
CREATE INDEX idx_backlog_status ON backlog_items(status);
CREATE INDEX idx_backlog_assignee ON backlog_items(assignee_id);
CREATE INDEX idx_backlog_priority ON backlog_items(priority);
```

**Acceptance Criteria:**
- [ ] Backlog items can exist without sprint (product backlog)
- [ ] Backlog items can be assigned to sprint
- [ ] Priority filtering (P0/P1/P2) works
- [ ] Parent-child relationship for subtasks

---

### Story 6: Planning Dashboard UI (10 SP)

**As a** Project Manager  
**I want** a Planning Dashboard  
**So that** I can see Roadmap → Phase → Sprint hierarchy visually

| Task ID | Task | Owner | Est | Status |
|---------|------|-------|-----|--------|
| S74-T52 | Create `usePlanning` hook | Frontend Dev | 3h | ⏳ |
| S74-T53 | Create PlanningPage layout | Frontend Dev | 2h | ⏳ |
| S74-T54 | Create RoadmapCard component | Frontend Dev | 2h | ⏳ |
| S74-T55 | Create PhaseTimeline component | Frontend Dev | 3h | ⏳ |
| S74-T56 | Create SprintBoard component | Frontend Dev | 4h | ⏳ |
| S74-T57 | Create BacklogTable component | Frontend Dev | 3h | ⏳ |
| S74-T58 | Create SprintGateStatus component | Frontend Dev | 2h | ⏳ |
| S74-T59 | Create CreateRoadmapDialog | Frontend Dev | 2h | ⏳ |
| S74-T60 | Create CreatePhaseDialog | Frontend Dev | 2h | ⏳ |
| S74-T61 | Create CreateSprintDialog | Frontend Dev | 2h | ⏳ |
| S74-T62 | Create GateEvaluationDialog | Frontend Dev | 3h | ⏳ |
| S74-T63 | Add Planning route to App.tsx | Frontend Dev | 1h | ⏳ |
| S74-T64 | Add Planning to navigation | Frontend Dev | 1h | ⏳ |

**UI Components:**
```
/planning (PlanningPage)
├── Header: Project selector + "New Roadmap" button
├── RoadmapCard (expandable)
│   ├── Vision, dates, review cadence
│   └── PhaseTimeline (horizontal)
│       ├── Phase 1 (Q1) → Sprints 74-77
│       ├── Phase 2 (Q2) → Sprints 78-81
│       └── Phase 3 (Q3) → Sprints 82-85
├── SprintBoard (current sprint detail)
│   ├── Sprint Goal
│   ├── G-Sprint Status (badge: Passed/Pending/Failed)
│   ├── G-Sprint-Close Status
│   ├── Capacity vs Committed
│   └── BacklogTable (Kanban or list view)
└── Traceability Panel
    └── Sprint 74 → Phase 1 → Roadmap 2026
```

**Acceptance Criteria:**
- [ ] Hierarchy visualization (Roadmap → Phase → Sprint)
- [ ] Sprint gate status visible with color coding
- [ ] Gate evaluation modal with checklist
- [ ] Backlog drag-and-drop between sprints
- [ ] Traceability breadcrumb

---

### Story 7: Integration Tests (5 SP)

**As a** QA Engineer  
**I want** integration tests for Planning Hierarchy  
**So that** the feature is verified end-to-end

| Task ID | Task | Owner | Est | Status |
|---------|------|-------|-----|--------|
| S74-T65 | Roadmap CRUD integration tests | QA | 2h | ⏳ |
| S74-T66 | Phase CRUD integration tests | QA | 2h | ⏳ |
| S74-T67 | Sprint CRUD integration tests | QA | 2h | ⏳ |
| S74-T68 | G-Sprint evaluation tests | QA | 3h | ⏳ |
| S74-T69 | G-Sprint-Close evaluation tests | QA | 3h | ⏳ |
| S74-T70 | Traceability chain tests | QA | 2h | ⏳ |
| S74-T71 | 24h deadline enforcement tests | QA | 2h | ⏳ |
| S74-T72 | Permission boundary tests | QA | 2h | ⏳ |

**Acceptance Criteria:**
- [ ] Full CRUD for Roadmap, Phase, Sprint, Backlog
- [ ] G-Sprint prevents sprint start without approval
- [ ] G-Sprint-Close blocks next sprint if failed
- [ ] 24h deadline triggers warning/block
- [ ] Traceability chain validated

---

### Story 8: SSOT Validation Script (3 SP)

**As a** DevOps Engineer  
**I want** an SSOT validation script  
**So that** sprint consistency is enforced in CI/CD

| Task ID | Task | Owner | Est | Status |
|---------|------|-------|-----|--------|
| S74-T73 | Create `validate-sprint-consistency.sh` | DevOps | 2h | ⏳ |
| S74-T74 | Add pre-commit hook | DevOps | 1h | ⏳ |
| S74-T75 | Add CI workflow step | DevOps | 1h | ⏳ |
| S74-T76 | Create SSOT API endpoint | Backend Dev | 2h | ⏳ |
| S74-T77 | Test SSOT validation | QA | 1h | ⏳ |

**Acceptance Criteria:**
- [ ] Script validates sprint references across docs
- [ ] Pre-commit hook blocks inconsistent changes
- [ ] CI fails on SSOT violations
- [ ] API endpoint for manual validation

---

## 📅 Sprint Schedule

### Week 1 (Feb 3-7): Backend Foundation

| Day | Focus | Tasks |
|-----|-------|-------|
| Mon | Migrations | S74-T01~T02, T11~T12, T21~T22, T32, T42 |
| Tue | Models | S74-T03~T04, T13~T14, T23~T24, T33, T43~T44 |
| Wed | APIs (Roadmap, Phase) | S74-T05~T10, T15~T20 |
| Thu | APIs (Sprint, Gates) | S74-T25~T31, T34~T41 |
| Fri | APIs (Backlog) + Tests | S74-T45~T51, Unit tests |

### Week 2 (Feb 10-14): Frontend + Integration

| Day | Focus | Tasks |
|-----|-------|-------|
| Mon | Frontend Foundation | S74-T52~T54 |
| Tue | Frontend Components | S74-T55~T58 |
| Wed | Frontend Dialogs | S74-T59~T62 |
| Thu | Frontend Integration | S74-T63~T64, Integration tests |
| Fri | SSOT + Polish | S74-T73~T77, Bug fixes |

---

## 🔗 Dependencies

| Dependency | Type | Status |
|------------|------|--------|
| Sprint 73 Complete | Blocking | ✅ Complete |
| ADR-013 Design | Reference | ✅ Approved |
| SDLC 5.1.3 Release | Reference | ✅ Released (Jan 18, 2026) |

---

## ⚠️ Risks

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| Complex gate logic | High | Medium | TDD approach, incremental development |
| UI complexity | Medium | Medium | Start with basic views, enhance iteratively |
| Sprint 73 delay | High | Low | Parallel track for model/migration work |
| 24h enforcement edge cases | Medium | Medium | Grace period for weekends |

---

## ✅ Definition of Done

- [ ] All CRUD operations for Roadmap, Phase, Sprint, Backlog working
- [ ] G-Sprint gate prevents sprint start without approval
- [ ] G-Sprint-Close enforces 24h documentation deadline
- [ ] Planning Dashboard shows hierarchy visualization
- [ ] Traceability chain validated (Sprint → Phase → Roadmap)
- [ ] SSOT validation script in CI/CD
- [ ] 80%+ test coverage on new code
- [ ] CTO approval on implementation

---

## 📊 Success Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| Sprint direction incidents | 0 | Post-deployment tracking |
| Documentation lag | <24h | Automated monitoring |
| G-Sprint compliance | 100% | Gate pass rate |
| Traceability completeness | 100% | All sprints linked to phase |
| Planning Dashboard adoption | 80%+ | User analytics |

---

## 📚 References

- [SDLC-Sprint-Planning-Governance.md](../../../SDLC-Enterprise-Framework/02-Core-Methodology/Governance-Compliance/SDLC-Sprint-Planning-Governance.md)
- [ADR-013: Planning Hierarchy](../01-ADRs/ADR-013-PLANNING-HIERARCHY.md)
- [BFlow Gap Analysis (Jan 18, 2026)](https://bflow.nhatquangholding.com/docs/SDLC-SPRINT-PLANNING-GOVERNANCE-GAP-ANALYSIS-JAN18-2026.md)
- [When-Planning-Sprint.md](../../../SDLC-Enterprise-Framework/02-Core-Methodology/Documentation-Standards/Situation-Specific-Guides/When-Planning-Sprint.md)

---

---

## 📊 Progress Summary (Updated: January 18, 2026)

### Backend Implementation Status

| Component | Model | Schema | API Routes | Service | Tests | Status |
|-----------|-------|--------|------------|---------|-------|--------|
| **Roadmap** | ✅ | ✅ | ✅ (5 endpoints) | ⏳ | ⏳ | 70% |
| **Phase** | ✅ | ✅ | ✅ (5 endpoints) | ⏳ | ⏳ | 70% |
| **Sprint** | ✅ | ✅ | ✅ (6 endpoints) | ⏳ | ⏳ | 70% |
| **Sprint Gate** | ✅ | ✅ | ✅ (3 endpoints) | ✅ | ⏳ | 80% |
| **Backlog** | ✅ | ✅ | ✅ (5 endpoints) | ⏳ | ⏳ | 70% |

### Files Created

| File | Location | Lines | Description |
|------|----------|-------|-------------|
| `roadmap.py` | `backend/app/models/` | 186 | Roadmap SQLAlchemy model |
| `phase.py` | `backend/app/models/` | ~150 | Phase SQLAlchemy model |
| `sprint.py` | `backend/app/models/` | 355 | Sprint model with G-Sprint fields |
| `sprint_gate_evaluation.py` | `backend/app/models/` | 370 | Gate evaluation model with JSONB checklist |
| `backlog_item.py` | `backend/app/models/` | ~200 | Backlog item model |
| `planning.py` | `backend/app/schemas/` | 700+ | Pydantic v2 schemas for Planning Hierarchy |
| `planning.py` | `backend/app/api/routes/` | 1600+ | 24+ API endpoints |
| `sprint_gate_service.py` | `backend/app/services/` | 400+ | Gate evaluation service |

### Remaining Work (P0)

1. **Database Migration** - Create Alembic migration for 5 new tables
2. **Frontend Dashboard** - Planning hierarchy UI (Story 6)
3. **Unit Tests** - Backend test coverage
4. **Integration Tests** - End-to-end workflow tests

### SDLC 5.1.3 Compliance

| Rule | Description | Implementation | Status |
|------|-------------|----------------|--------|
| #1 | Sprint Numbers Immutable | `UNIQUE(project_id, number)` | ✅ |
| #2 | 24h Documentation | `documentation_deadline` field | ✅ |
| #3 | Sprint Approval | `g_sprint_approved_by` field | ✅ |
| #7 | Sprint-Phase Alignment | `phase_id` FK + validation | ✅ |
| #8 | Priorities Explicit | `Priority` enum (P0/P1/P2) | ✅ |
| #9 | Documentation Freeze | `documentation_overdue` property | ✅ |

---

**Sprint Owner:** Tech Lead
**CTO Approval Required:** Before Go-Live
**Framework Reference:** SDLC 5.1.3
**Last Updated:** January 18, 2026
