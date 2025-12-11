# PHASE-03: Web Dashboard AI Integration
## Context-Aware Requirements & Planning Hierarchy

**Version**: 1.0.0
**Date**: December 3, 2025
**Status**: PLANNED - Sprint 28
**Duration**: 5 days (Dec 23-27, 2025)
**Owner**: Frontend Lead + Backend Team
**Framework**: SDLC 4.9.1 Complete Lifecycle
**Prerequisites**: PHASE-01 Complete, PHASE-02 Complete

---

## Executive Summary

PHASE-03 integrates AI capabilities directly into the Web Dashboard, enabling **Context-Aware Requirements** and **4-Level Planning Hierarchy**. PMs can configure project context and see requirements automatically classified by priority.

**Key Deliverables**:
1. Context-Aware Requirements UI (3-tier classification)
2. Planning Hierarchy View (Roadmap → Phase → Sprint → Backlog)
3. AI Suggestions Panel (inline recommendations)
4. Project Context Profile Editor (5 dimensions)

**Success Criteria**:
- Requirements load <500ms (p95)
- Planning hierarchy query <1s (full chain)
- Context profile update <200ms
- AI suggestions relevance >80%

---

## 1. Problem Statement

### Current State (Before PHASE-03)

**Pain Points**:
1. **No Requirement Classification**: All requirements treated equally (no priority guidance)
2. **Flat Planning View**: Sprints exist, but no vision-to-task traceability
3. **No Context Awareness**: Requirements don't adapt to project type/size
4. **Manual AI Interaction**: PM must switch to AI chat for suggestions

**Evidence**:
- PM confusion: "Which requirements are mandatory for my startup?"
- Traceability gap: "How does this task connect to our vision?"
- Context mismatch: "Enterprise rules applied to 3-person startup"

### Target State (After PHASE-03)

- Requirements auto-classified: MANDATORY (red), RECOMMENDED (yellow), OPTIONAL (gray)
- Full traceability: Task → Sprint → Phase → Roadmap → Vision
- Context-aware: Small startup sees simplified requirements
- Inline AI: Suggestions appear as you work

---

## 2. Technical Architecture

### 2.1 Context-Aware Requirements Engine

```
┌─────────────────────────────────────────────────────────────────┐
│                CONTEXT-AWARE REQUIREMENTS ENGINE                │
├─────────────────────────────────────────────────────────────────┤
│  ┌─────────────────────────────────────────────────────────────┐│
│  │                 PROJECT CONTEXT PROFILE                      ││
│  │  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐            ││
│  │  │ Project     │ │ Team        │ │ Industry    │            ││
│  │  │ Scale       │ │ Structure   │ │             │            ││
│  │  │ ────────    │ │ ────────    │ │ ────────    │            ││
│  │  │ • startup   │ │ • solo      │ │ • fintech   │            ││
│  │  │ • scaleup   │ │ • small     │ │ • healthcare│            ││
│  │  │ • enterprise│ │ • medium    │ │ • ecommerce │            ││
│  │  └─────────────┘ └─────────────┘ └─────────────┘            ││
│  │  ┌─────────────┐ ┌─────────────┐                            ││
│  │  │ Risk        │ │ Dev         │                            ││
│  │  │ Profile     │ │ Practices   │                            ││
│  │  │ ────────    │ │ ────────    │                            ││
│  │  │ • low       │ │ • waterfall │                            ││
│  │  │ • medium    │ │ • agile     │                            ││
│  │  │ • high      │ │ • hybrid    │                            ││
│  │  │ • critical  │ │ • continuous│                            ││
│  │  └─────────────┘ └─────────────┘                            ││
│  └─────────────────────────────────────────────────────────────┘│
│                                │                                 │
│                    ┌───────────┴───────────┐                    │
│                    │ Context Rules Engine  │                    │
│                    │ ──────────────────────│                    │
│                    │ Rule: IF fintech AND  │                    │
│                    │   high_risk THEN      │                    │
│                    │   SOC2 = MANDATORY    │                    │
│                    └───────────────────────┘                    │
│                                │                                 │
│                    ┌───────────┴───────────┐                    │
│                    │ Requirements Output   │                    │
│                    │ ──────────────────────│                    │
│                    │ 🔴 MANDATORY (12)     │                    │
│                    │ 🟡 RECOMMENDED (25)   │                    │
│                    │ ⚪ OPTIONAL (18)      │                    │
│                    └───────────────────────┘                    │
└─────────────────────────────────────────────────────────────────┘
```

### 2.2 4-Level Planning Hierarchy

```
┌─────────────────────────────────────────────────────────────────┐
│                    PLANNING HIERARCHY                           │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  LEVEL 0: ROADMAP (Vision Layer)                               │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │ 🎯 Vision: First governance platform on SDLC 4.9.1         ││
│  │ Timeline: 2025-2028 (3 years)                               ││
│  │ Goals: 10,000 teams, $24M ARR                               ││
│  └─────────────────────────────────────────────────────────────┘│
│           │                                                     │
│           ├───────────────────────────────────────────┐        │
│           ▼                                           ▼        │
│  LEVEL 1: PHASE (Quarter Layer)                               │
│  ┌─────────────────────┐  ┌─────────────────────┐              │
│  │ PHASE 1: AI Council │  │ PHASE 2: VS Code   │              │
│  │ Q4 2025             │  │ Q4 2025            │              │
│  │ Sprint 26           │  │ Sprint 27          │              │
│  └─────────────────────┘  └─────────────────────┘              │
│           │                                                     │
│           ├───────────────────────────────────────────┐        │
│           ▼                                           ▼        │
│  LEVEL 2: SPRINT (Week Layer)                                 │
│  ┌─────────────────────┐  ┌─────────────────────┐              │
│  │ Sprint 26 Day 1-5   │  │ Sprint 27 Day 1-5  │              │
│  │ Dec 9-13, 2025      │  │ Dec 16-20, 2025    │              │
│  │ 5 major tasks       │  │ 4 major tasks      │              │
│  └─────────────────────┘  └─────────────────────┘              │
│           │                                                     │
│           ├───────────────────────────────────────────┐        │
│           ▼                                           ▼        │
│  LEVEL 3: BACKLOG (Task Layer)                                │
│  ┌─────────────────────┐  ┌─────────────────────┐              │
│  │ Task: Implement     │  │ Task: Create OAuth │              │
│  │ Ollama adapter      │  │ device flow        │              │
│  │ 4 story points      │  │ 3 story points     │              │
│  └─────────────────────┘  └─────────────────────┘              │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 2.3 Database Schema

```sql
-- Migration 006: Context-Aware Requirements

CREATE TABLE project_context_profiles (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
  project_scale VARCHAR(20) NOT NULL CHECK (project_scale IN ('startup', 'scaleup', 'enterprise')),
  team_structure VARCHAR(20) NOT NULL CHECK (team_structure IN ('solo', 'small', 'medium', 'large', 'distributed')),
  industry VARCHAR(50) NOT NULL,
  risk_profile VARCHAR(20) NOT NULL CHECK (risk_profile IN ('low', 'medium', 'high', 'critical')),
  dev_practices VARCHAR(30) NOT NULL CHECK (dev_practices IN ('waterfall', 'agile', 'hybrid', 'continuous')),
  custom_rules JSONB DEFAULT '{}',
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  UNIQUE(project_id)
);

CREATE TABLE stage_requirements (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  stage VARCHAR(30) NOT NULL,
  requirement_code VARCHAR(20) NOT NULL,
  title VARCHAR(255) NOT NULL,
  description TEXT,
  default_tier VARCHAR(20) NOT NULL CHECK (default_tier IN ('mandatory', 'recommended', 'optional')),
  rationale TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE context_rules (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  rule_name VARCHAR(100) NOT NULL,
  condition_expression JSONB NOT NULL,
  requirement_id UUID NOT NULL REFERENCES stage_requirements(id) ON DELETE CASCADE,
  tier_override VARCHAR(20) NOT NULL CHECK (tier_override IN ('mandatory', 'recommended', 'optional')),
  priority INTEGER DEFAULT 0,
  is_active BOOLEAN DEFAULT true,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE requirement_overrides (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
  requirement_id UUID NOT NULL REFERENCES stage_requirements(id) ON DELETE CASCADE,
  tier_override VARCHAR(20) NOT NULL CHECK (tier_override IN ('mandatory', 'recommended', 'optional')),
  reason TEXT NOT NULL,
  approved_by UUID REFERENCES users(id),
  approved_at TIMESTAMPTZ,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  UNIQUE(project_id, requirement_id)
);

-- Migration 008: Planning Hierarchy

CREATE TABLE roadmaps (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
  title VARCHAR(255) NOT NULL,
  vision_statement TEXT,
  start_date DATE NOT NULL,
  end_date DATE NOT NULL,
  goals JSONB DEFAULT '[]',
  status VARCHAR(20) DEFAULT 'active' CHECK (status IN ('draft', 'active', 'completed', 'archived')),
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE phases (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  roadmap_id UUID NOT NULL REFERENCES roadmaps(id) ON DELETE CASCADE,
  phase_number INTEGER NOT NULL,
  title VARCHAR(255) NOT NULL,
  description TEXT,
  start_date DATE NOT NULL,
  end_date DATE NOT NULL,
  objectives JSONB DEFAULT '[]',
  status VARCHAR(20) DEFAULT 'planned' CHECK (status IN ('planned', 'in_progress', 'completed', 'blocked')),
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE sprints (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  phase_id UUID NOT NULL REFERENCES phases(id) ON DELETE CASCADE,
  sprint_number INTEGER NOT NULL,
  title VARCHAR(255) NOT NULL,
  goal TEXT,
  start_date DATE NOT NULL,
  end_date DATE NOT NULL,
  capacity_points INTEGER,
  velocity_actual INTEGER,
  status VARCHAR(20) DEFAULT 'planned' CHECK (status IN ('planned', 'active', 'completed', 'cancelled')),
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE backlog_items (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  sprint_id UUID REFERENCES sprints(id) ON DELETE SET NULL,
  project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
  title VARCHAR(255) NOT NULL,
  description TEXT,
  item_type VARCHAR(20) NOT NULL CHECK (item_type IN ('story', 'task', 'bug', 'spike', 'chore')),
  story_points INTEGER,
  priority VARCHAR(20) DEFAULT 'medium' CHECK (priority IN ('critical', 'high', 'medium', 'low')),
  status VARCHAR(20) DEFAULT 'backlog' CHECK (status IN ('backlog', 'todo', 'in_progress', 'review', 'done')),
  assignee_id UUID REFERENCES users(id),
  parent_item_id UUID REFERENCES backlog_items(id),
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Indexes
CREATE INDEX idx_context_profiles_project ON project_context_profiles(project_id);
CREATE INDEX idx_requirements_stage ON stage_requirements(stage);
CREATE INDEX idx_context_rules_req ON context_rules(requirement_id);
CREATE INDEX idx_overrides_project ON requirement_overrides(project_id);
CREATE INDEX idx_phases_roadmap ON phases(roadmap_id);
CREATE INDEX idx_sprints_phase ON sprints(phase_id);
CREATE INDEX idx_backlog_sprint ON backlog_items(sprint_id);
CREATE INDEX idx_backlog_project ON backlog_items(project_id);
```

---

## 3. API Specification

### 3.1 Context-Aware Requirements (4 endpoints)

**GET /projects/{id}/requirements**
```json
{
  "requirements": [
    {
      "id": "uuid",
      "code": "SEC-001",
      "title": "Implement HTTPS",
      "tier": "mandatory",
      "tier_reason": "fintech + high_risk context",
      "stage": "02-design",
      "is_overridden": false
    }
  ],
  "summary": {
    "mandatory": 12,
    "recommended": 25,
    "optional": 18
  }
}
```

**GET /projects/{id}/context-profile**
```json
{
  "project_scale": "startup",
  "team_structure": "small",
  "industry": "fintech",
  "risk_profile": "high",
  "dev_practices": "agile"
}
```

**PUT /projects/{id}/context-profile**
```json
{
  "project_scale": "scaleup",
  "team_structure": "medium",
  "industry": "fintech",
  "risk_profile": "high",
  "dev_practices": "continuous"
}
```

**POST /projects/{id}/requirements/{req_id}/override**
```json
{
  "tier_override": "optional",
  "reason": "Not applicable for MVP phase"
}
```

### 3.2 Planning Hierarchy (8 endpoints)

**GET /projects/{id}/roadmap**
**POST /projects/{id}/roadmap**
**GET /roadmaps/{id}/phases**
**POST /roadmaps/{id}/phases**
**GET /phases/{id}/sprints**
**POST /phases/{id}/sprints**
**GET /sprints/{id}/backlog**
**POST /sprints/{id}/backlog**

---

## 4. UI Components

### 4.1 Requirements Dashboard

```
┌──────────────────────────────────────────────────────────────────┐
│ Project Requirements - Bflow Platform                           │
├──────────────────────────────────────────────────────────────────┤
│ Context: startup | small team | fintech | high risk | agile    │
│ [Edit Context]                                                   │
├──────────────────────────────────────────────────────────────────┤
│ 🔴 MANDATORY (12)                    [Expand All]               │
│ ├── SEC-001: Implement HTTPS          ✅ Passed                 │
│ ├── SEC-002: Data encryption at rest  ✅ Passed                 │
│ ├── SEC-003: Authentication           🔄 In Progress            │
│ └── ... (9 more)                                                │
├──────────────────────────────────────────────────────────────────┤
│ 🟡 RECOMMENDED (25)                  [Expand All]               │
│ ├── PERF-001: <100ms API latency     ✅ Passed                  │
│ ├── DOC-001: API documentation       ⏳ Pending                 │
│ └── ... (23 more)                                               │
├──────────────────────────────────────────────────────────────────┤
│ ⚪ OPTIONAL (18)                     [Collapse All]             │
│ └── ... (collapsed)                                             │
└──────────────────────────────────────────────────────────────────┘
```

### 4.2 Planning Hierarchy View

```
┌──────────────────────────────────────────────────────────────────┐
│ Planning Hierarchy - Bflow Platform                             │
├──────────────────────────────────────────────────────────────────┤
│ 🎯 ROADMAP: First governance platform                           │
│ │  2025-2028 | 10,000 teams target                              │
│ │                                                                │
│ ├── 📅 PHASE 1: AI Council (Q4 2025)                            │
│ │   │  Sprint 26 | Dec 9-13, 2025                               │
│ │   │                                                            │
│ │   ├── 🔄 SPRINT 26: AI Task Decomposition                     │
│ │   │   ├── [5pts] Implement Ollama adapter    ✅ Done          │
│ │   │   ├── [3pts] Create context builder      🔄 In Progress   │
│ │   │   ├── [5pts] Multi-provider fallback     ⏳ Todo          │
│ │   │   └── [2pts] Quality scorer              ⏳ Todo          │
│ │   │                                                            │
│ │   └── 🔄 SPRINT 27: VS Code Extension                         │
│ │       └── ... (collapsed)                                      │
│ │                                                                │
│ ├── 📅 PHASE 2: Dashboard AI (Q4 2025)                          │
│ │   └── Sprint 28 | Dec 23-27, 2025                             │
│ │                                                                │
│ └── 📅 PHASE 3: SDLC Validator (Q1 2026)                        │
│     └── Sprint 29-30 | Jan 2026                                 │
└──────────────────────────────────────────────────────────────────┘
```

---

## 5. Implementation Plan

### Day 1: Database & API Foundation (Dec 23)

**Tasks**:
1. Create migrations 006 (context profiles) and 008 (planning)
2. Implement SQLAlchemy models
3. Create API routes for context profile
4. Unit tests for models

**Deliverables**:
- Migrations applied
- Context profile CRUD working
- 80%+ test coverage

### Day 2: Requirements Engine (Dec 24)

**Tasks**:
1. Seed stage_requirements table (55 base requirements)
2. Implement context rules engine
3. Create requirement classification API
4. Add override functionality

**Deliverables**:
- Requirements API returning classified results
- Context rules applying correctly
- Override flow working

### Day 3: Planning Hierarchy API (Dec 25)

**Tasks**:
1. Implement roadmap, phase, sprint CRUD
2. Create backlog item management
3. Add hierarchy query (full chain)
4. Integration tests

**Deliverables**:
- All planning endpoints working
- Hierarchy query <1s
- E2E planning flow tested

### Day 4: Frontend Components (Dec 26)

**Tasks**:
1. Create Requirements Dashboard component
2. Create Planning Hierarchy tree view
3. Implement Context Profile editor
4. Add drill-down navigation

**Deliverables**:
- UI components rendering
- Context editing working
- Hierarchy navigation smooth

### Day 5: AI Integration & Polish (Dec 27)

**Tasks**:
1. Add AI suggestions panel
2. Implement inline recommendations
3. Performance optimization
4. CTO review & approval

**Deliverables**:
- AI suggestions appearing
- All performance targets met
- CTO approval

---

## 6. Success Criteria

### Performance Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| Requirements load (p95) | <500ms | API latency |
| Hierarchy query (full chain) | <1s | API latency |
| Context profile update | <200ms | API latency |
| UI render (requirements list) | <100ms | React profiler |

### Quality Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| Requirement classification accuracy | 100% | Manual validation |
| AI suggestions relevance | >80% | User feedback |
| Context rules coverage | 100% of dimensions | Rule audit |

---

## 7. References

- [ADR-012: Context-Aware Requirements](../../02-Design-Architecture/03-ADRs/ADR-012-Context-Aware-Requirements.md)
- [ADR-013: 4-Level Planning Hierarchy](../../02-Design-Architecture/03-ADRs/ADR-013-Planning-Hierarchy.md)
- [Product Roadmap v3.0.0](../../00-Project-Foundation/04-Roadmap/Product-Roadmap.md)
- [Sprint 28 Plan](../02-Sprint-Plans/SPRINT-28-WEB-DASHBOARD-AI.md)

---

**Document Status**: ✅ APPROVED - Ready for Sprint 28
**Last Updated**: December 3, 2025
**Owner**: Frontend Lead + CTO
