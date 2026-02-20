# Sprint 87: Sprint Governance UI + P0 Blockers (SDLC 6.1.0 Pillar 2)

**Sprint ID:** S87
**Status:** ✅ **CTO APPROVED** (January 20, 2026) - **CRITICAL PRIORITY**
**Duration:** 10 days (February 23 - March 5, 2026)
**Goal:** Implement Sprint Planning Governance UI + P0 Blockers (GitHub Check Run, Evidence Hash Chain)
**Story Points:** 58 SP (42 SP Governance + 16 SP P0 Blockers)
**Framework Reference:** SDLC 6.1.0 P2 (Sprint Planning Governance)
**Prerequisite:** Sprint 86 ✅ System Settings Implementation
**Target:** Full Sprint Governance visibility and control + P0 Blocker Resolution

---

## Executive Summary

### Strategic Importance

SDLC 6.1.0's defining feature is **Sprint Planning Governance** (Pillar 2). As the Orchestrator platform that **enforces** this framework, we MUST implement this feature excellently. This is "eating our own dog food."

Additionally, this sprint addresses **P0 Blockers** from the Expert Feedback Response plan that are critical for launch.

| Component | Description | Priority |
|-----------|-------------|----------|
| **GitHub Check Run UI** | Check Run management dashboard | **P0** ✅ DONE |
| **Evidence Hash Chain v1 UI** | Tamper-evident audit trail | **P0** ✅ DONE |
| **G-Sprint Gate** | Sprint start quality gate | **P0** |
| **G-Sprint-Close Gate** | Sprint close quality gate | **P0** |
| **Planning Hierarchy** | Roadmap → Phase → Sprint → Backlog | **P0** |
| **24h Documentation Rule** | Sprint close docs within 24 hours | **P1** |

---

## ✅ P0 Blockers (CTO-Mandated Pre-Launch)

### GitHub Check Run UI - ✅ COMPLETED (January 20, 2026)

**Reference:** Expert Feedback Response Plan - BLOCKER-03

| Task | Status | Files Created |
|------|--------|---------------|
| TypeScript interfaces & helpers | ✅ DONE | `frontend/src/lib/types/github-checks.ts` |
| TanStack Query hooks | ✅ DONE | `frontend/src/hooks/useGitHubChecks.ts` |
| API functions | ✅ DONE | `frontend/src/lib/api.ts` (7 functions added) |
| Check Runs dashboard page | ✅ DONE | `frontend/src/app/app/check-runs/page.tsx` |
| Check Run detail page | ✅ DONE | `frontend/src/app/app/check-runs/[id]/page.tsx` |
| Loading skeleton | ✅ DONE | `frontend/src/app/app/check-runs/loading.tsx` |
| Navigation integration | ✅ DONE | `Sidebar.tsx`, `Header.tsx` updated |
| Build verification | ✅ DONE | No ESLint errors |

**Features Implemented:**
- Check Run list with filtering (by conclusion, mode)
- Stats dashboard (total runs, pass rate, failed, avg duration)
- Enforcement mode visualization (Advisory/Blocking/Strict)
- Re-run functionality
- Gate evaluation results display
- Check Run output with annotations
- Context overlay information

### Evidence Hash Chain v1 UI - ✅ COMPLETED (January 20, 2026)

**Reference:** Expert Feedback Response Plan - BLOCKER-04
**Original Deadline:** February 10, 2026 | **Completed:** January 20, 2026 (**21 DAYS AHEAD!**)

| Task | Status | Files Created |
|------|--------|---------------|
| TypeScript interfaces & helpers | ✅ DONE | `frontend/src/lib/types/evidence-manifest.ts` (327 LOC) |
| TanStack Query hooks | ✅ DONE | `frontend/src/hooks/useEvidenceManifest.ts` (203 LOC) |
| API functions | ✅ DONE | `frontend/src/lib/api.ts` (6 functions added) |
| Evidence Manifests dashboard | ✅ DONE | `frontend/src/app/app/evidence-manifests/page.tsx` (552 LOC) |
| Manifest detail page | ✅ DONE | `frontend/src/app/app/evidence-manifests/[id]/page.tsx` (431 LOC) |
| Loading skeleton | ✅ DONE | `frontend/src/app/app/evidence-manifests/loading.tsx` (91 LOC) |
| Navigation integration | ✅ DONE | `Sidebar.tsx`, `Header.tsx` updated |
| Build verification | ✅ DONE | No ESLint errors |

**Features Implemented:**
- Chain integrity status display (verified/unverified/broken/pending)
- One-click chain verification with real-time status
- Hash chain visualization with sequence numbers
- Manifest detail with artifacts and Ed25519 signatures
- Verification history timeline
- Project selector for multi-project support

**Backend (Sprint 82 - Already Complete):**
- Hash chain with Ed25519 asymmetric signing
- MinIO Object Lock for immutability
- Evidence manifest API endpoints

### SDLC 6.1.0 Pillar 2 Requirements

```yaml
Pillar 2: Sprint Planning Governance
  Description: "Mandatory sprint planning gate enforcement"

  Gates:
    G-Sprint (Sprint Start):
      - Sprint Goal defined
      - Backlog items estimated
      - Team capacity confirmed
      - Dependencies identified
      - Risks documented

    G-Sprint-Close (Sprint End):
      - All items completed or carried over with justification
      - Sprint retrospective documented
      - Evidence manifests created
      - Definition of Done verified
      - Next sprint prepared

  Rules:
    - No sprint starts without G-Sprint pass
    - Sprint cannot close without G-Sprint-Close pass
    - 24h documentation window after sprint close
    - Automatic escalation if deadline missed

  Dual-Track Gates:
    - Feature Gates: G0.1 → G0.2 → G1 → G2 → G3 → G4 → G5
    - Sprint Gates: G-Sprint → G-Sprint-Close (per sprint)
```

---

## 🎯 Sprint 87 Objectives

### Primary Goals (P0 - Framework Integrity)

1. **Sprint Governance Dashboard** - Sprint lifecycle visibility
2. **G-Sprint Gate UI** - Sprint start checklist and approval
3. **G-Sprint-Close Gate UI** - Sprint close verification
4. **Planning Hierarchy Visualization** - Roadmap → Phase → Sprint → Backlog tree

### Secondary Goals (P1)

5. **Sprint Timeline View** - Gantt-like sprint overview
6. **24h Documentation Timer** - Countdown with notifications
7. **Sprint Templates** - Quick sprint setup from templates

---

## 📋 Sprint 87 Backlog

### Day 1-2: Planning Hierarchy API Hooks (8 SP) - ✅ COMPLETED

| Task | Owner | Est | Priority | Status |
|------|-------|-----|----------|--------|
| Create `usePlanningHierarchy.ts` hook | Frontend | 4h | P0 | ✅ DONE |
| Create `useSprintGovernance.ts` hook | Frontend | 4h | P0 | ✅ DONE |
| Define TypeScript interfaces | Frontend | 2h | P0 | ✅ DONE |
| Add API endpoints to `api.ts` | Frontend | 2h | P0 | ✅ DONE |
| Unit tests for hooks (10 tests) | Frontend | 3h | P0 | ✅ DONE |

**Files to Create:**

```
frontend/src/hooks/usePlanningHierarchy.ts
frontend/src/hooks/useSprintGovernance.ts
frontend/src/lib/types/planning.ts
frontend/src/lib/types/sprint-governance.ts
```

**Hook API Reference:**

```typescript
// usePlanningHierarchy.ts
export function useRoadmaps(projectId: string) {
  // GET /projects/{id}/roadmaps - List roadmaps
  // Returns: { roadmaps, isLoading, error }
}

export function usePhases(roadmapId: string) {
  // GET /roadmaps/{id}/phases - List phases
  // Returns: { phases, isLoading, error }
}

export function useSprints(phaseId?: string, projectId?: string) {
  // GET /phases/{id}/sprints OR /projects/{id}/sprints
  // Returns: { sprints, isLoading, error }
}

export function useBacklogItems(sprintId?: string, projectId?: string) {
  // GET /sprints/{id}/items OR /projects/{id}/backlog
  // Returns: { items, isLoading, error }
}

export function useCreateSprint() {
  // POST /sprints - Create sprint
  // Returns: { createSprint, isLoading, error }
}

export function useUpdateSprint(sprintId: string) {
  // PATCH /sprints/{id} - Update sprint
  // Returns: { updateSprint, isLoading, error }
}

// useSprintGovernance.ts
export function useSprintGate(sprintId: string, gateType: 'start' | 'close') {
  // GET /sprints/{id}/gates/{type} - Get gate status
  // Returns: { gate, isLoading, error }
}

export function useEvaluateSprintGate(sprintId: string) {
  // POST /sprints/{id}/gates/evaluate - Evaluate gate
  // Returns: { evaluate, isLoading, error }
}

export function useApproveSprintGate(sprintId: string) {
  // POST /sprints/{id}/gates/approve - Approve gate
  // Returns: { approve, isLoading, error }
}

export function useSprintChecklistItems(sprintId: string, gateType: string) {
  // GET /sprints/{id}/gates/{type}/checklist
  // Returns: { items, isLoading, error }
}

export function useDocumentationTimer(sprintId: string) {
  // GET /sprints/{id}/documentation-deadline
  // Returns: { deadline, hoursRemaining, isExpired }
}
```

---

### Day 3-5: Sprint Governance Dashboard (16 SP) - ✅ COMPLETED

| Task | Owner | Est | Priority | Status |
|------|-------|-----|----------|--------|
| Create Sprint Governance dashboard page | Frontend | 6h | P0 | ✅ DONE |
| Create Sprint Lifecycle component | Frontend | 4h | P0 | ✅ DONE |
| Create G-Sprint Gate checklist UI | Frontend | 4h | P0 | ✅ DONE |
| Create G-Sprint-Close Gate checklist UI | Frontend | 4h | P0 | ✅ DONE |
| Create Sprint Status cards | Frontend | 3h | P0 | ✅ DONE |
| Create Documentation Timer component | Frontend | 2h | P1 | ✅ DONE |
| Create Sprint comparison view | Frontend | 3h | P1 | ✅ DONE |
| Loading states & error handling | Frontend | 2h | P0 | ✅ DONE |

**Files Created:**

```
frontend/src/app/app/sprints/
├── page.tsx                       # Sprint list/governance dashboard ✅
├── loading.tsx                    # Loading skeleton ✅
├── [id]/
│   ├── page.tsx                   # Sprint detail ✅
│   ├── start-gate/
│   │   └── page.tsx               # G-Sprint gate ✅
│   └── close-gate/
│       └── page.tsx               # G-Sprint-Close gate ✅
└── components/
    ├── SprintCard.tsx             # Sprint overview card ✅
    ├── SprintLifecycle.tsx        # Sprint lifecycle visualization ✅
    ├── SprintGateChecklist.tsx    # Gate checklist with items ✅
    ├── GateApprovalButton.tsx     # Approve gate button ✅
    ├── DocumentationTimer.tsx     # 24h countdown ✅
    ├── SprintStatusBadge.tsx      # Status badge ✅
    ├── SprintCompareView.tsx      # Compare sprints ✅
    └── CreateSprintModal.tsx      # New sprint modal ✅
```

**UI Specifications:**

```
Sprint Governance Dashboard (/app/sprints):
┌─────────────────────────────────────────────────────────────────────────┐
│ Sprint Governance                             [+ New Sprint] [Calendar] │
├─────────────────────────────────────────────────────────────────────────┤
│ Active Sprint                                                           │
│ ┌─────────────────────────────────────────────────────────────────────┐ │
│ │ Sprint 87: Sprint Governance UI                                     │ │
│ │                                                                     │ │
│ │ [████████████████████░░░░░░░░░░] Day 5/10  (50%)                   │ │
│ │                                                                     │ │
│ │ ┌────────────┐  ┌────────────┐  ┌────────────┐  ┌────────────┐    │ │
│ │ │ Planned    │  │ In Progress│  │ Completed  │  │ Carry Over │    │ │
│ │ │    8       │  │    3       │  │    12      │  │    0       │    │ │
│ │ └────────────┘  └────────────┘  └────────────┘  └────────────┘    │ │
│ │                                                                     │ │
│ │ G-Sprint: ✅ PASSED              G-Sprint-Close: ⏳ Pending         │ │
│ └─────────────────────────────────────────────────────────────────────┘ │
├─────────────────────────────────────────────────────────────────────────┤
│ Upcoming Sprints                                                        │
│ ┌───────────────────┐ ┌───────────────────┐ ┌───────────────────┐      │
│ │ Sprint 88         │ │ Sprint 89         │ │ Sprint 90         │      │
│ │ Mar 6-16, 2026    │ │ Mar 17-27, 2026   │ │ Mar 28-Apr 7      │      │
│ │ ⏳ Pending Start  │ │ 📋 Planned        │ │ 📋 Planned        │      │
│ │ [Start Sprint]    │ │                   │ │                   │      │
│ └───────────────────┘ └───────────────────┘ └───────────────────┘      │
├─────────────────────────────────────────────────────────────────────────┤
│ Recent Completed Sprints                                                │
│ │ Sprint 86 │ ✅ Closed │ Feb 22 │ 15/16 items │ 93.7% │ [View]       │
│ │ Sprint 85 │ ✅ Closed │ Feb 11 │ 18/18 items │ 100%  │ [View]       │
│ │ Sprint 84 │ ✅ Closed │ Jan 31 │ 14/15 items │ 93.3% │ [View]       │
└─────────────────────────────────────────────────────────────────────────┘

G-Sprint Gate (/app/sprints/[id]/start-gate):
┌─────────────────────────────────────────────────────────────────────────┐
│ ← Back    G-Sprint Gate: Sprint 87                         [Evaluate]   │
├─────────────────────────────────────────────────────────────────────────┤
│ Sprint Start Checklist                           Overall: 5/6 ✅        │
│ ─────────────────────────────────────────────────────────────────────── │
│ ☑️ Sprint Goal Defined                                       ✅ PASS    │
│    "Implement Sprint Governance UI - SDLC 6.1.0 Pillar 2"               │
│                                                                         │
│ ☑️ Backlog Items Estimated                                   ✅ PASS    │
│    42 story points across 18 items                                      │
│                                                                         │
│ ☑️ Team Capacity Confirmed                                   ✅ PASS    │
│    3 FE + 2 BE + 1 QA = 45 SP capacity (buffer: 3 SP)                  │
│                                                                         │
│ ☑️ Dependencies Identified                                   ✅ PASS    │
│    - Sprint 86 (System Settings) - ✅ Complete                          │
│    - Planning Hierarchy API - ✅ Available                              │
│                                                                         │
│ ☑️ Risks Documented                                          ✅ PASS    │
│    - RK-001: Complex gate logic (M) - Mitigated                         │
│    - RK-002: Timeline pressure (L) - Accepted                           │
│                                                                         │
│ ☐ Prerequisite Sprint Closed                                 ⚠️ WARN    │
│    Sprint 86 closes tomorrow (Feb 22)                                   │
├─────────────────────────────────────────────────────────────────────────┤
│ Gate Actions                                                            │
│ ┌────────────────────────────────────────────────────────────────────┐ │
│ │ Status: ⚠️ CONDITIONAL PASS (5/6 mandatory items)                  │ │
│ │                                                                    │ │
│ │ The gate can be approved with a waiver for the pending item.       │ │
│ │                                                                    │ │
│ │ [Request Waiver]              [Approve Gate ✅]                    │ │
│ └────────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────┘

G-Sprint-Close Gate (/app/sprints/[id]/close-gate):
┌─────────────────────────────────────────────────────────────────────────┐
│ ← Back    G-Sprint-Close Gate: Sprint 86                    [Evaluate]  │
├─────────────────────────────────────────────────────────────────────────┤
│ ⏰ Documentation Deadline: 23:45:12 remaining                           │
│ ─────────────────────────────────────────────────────────────────────── │
│ Sprint Close Checklist                           Overall: 4/5 ✅        │
│ ─────────────────────────────────────────────────────────────────────── │
│ ☑️ All Items Completed or Justified                          ✅ PASS    │
│    15/16 completed, 1 carried over with justification                   │
│    Carry over: "Complex security edge case needs more research"         │
│                                                                         │
│ ☑️ Sprint Retrospective Documented                           ✅ PASS    │
│    Document: SPRINT-86-RETROSPECTIVE.md                                 │
│                                                                         │
│ ☑️ Evidence Manifests Created                                ✅ PASS    │
│    3 manifests: Code Review, Test Results, Deployment Log               │
│                                                                         │
│ ☑️ Definition of Done Verified                               ✅ PASS    │
│    All completed items meet DoD criteria                                │
│                                                                         │
│ ☐ Next Sprint Prepared                                       ⚠️ PEND    │
│    Sprint 87 G-Sprint gate: 5/6 items ready                             │
├─────────────────────────────────────────────────────────────────────────┤
│ Gate Actions                                                            │
│ ┌────────────────────────────────────────────────────────────────────┐ │
│ │ Status: ⚠️ PENDING (4/5 mandatory items)                           │ │
│ │                                                                    │ │
│ │ Complete Sprint 87 preparation to close this sprint.               │ │
│ │                                                                    │ │
│ │ [Go to Sprint 87 Setup]       [Close Sprint ✅]  (disabled)        │ │
│ └────────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────┘
```

---

### Day 6-7: Planning Hierarchy Visualization (10 SP) - ✅ COMPLETED

| Task | Owner | Est | Priority | Status |
|------|-------|-----|----------|--------|
| Create Planning Hierarchy page | Frontend | 5h | P0 | ✅ DONE |
| Create Roadmap → Phase → Sprint tree view | Frontend | 5h | P0 | ✅ DONE |
| Create Backlog drag-and-drop | Frontend | 4h | P1 | ✅ DONE |
| Create Timeline/Gantt view | Frontend | 4h | P1 | ✅ DONE |
| Create Quick add item form | Frontend | 2h | P1 | ✅ DONE |

**Files Created:**

```
frontend/src/app/app/planning/
├── page.tsx                       # Planning hierarchy overview ✅
├── loading.tsx                    # Loading skeleton ✅
└── components/
    ├── PlanningHierarchyTree.tsx  # Hierarchical tree view with expand/collapse ✅
    └── SprintTimeline.tsx         # Gantt-style timeline component ✅
```

**Key Features Implemented:**
- **PlanningHierarchyTree.tsx** (478 LOC): Interactive tree view with expand/collapse, drag-and-drop ready, icons for roadmap/phase/sprint/backlog items
- **SprintTimeline.tsx** (385 LOC): Gantt-style timeline with today marker, sprint duration bars, status colors, hover tooltips
- **Planning Page**: Combined tree view and timeline with tab switching, project selector, filtering by status

**UI Specification:**

```
Planning Hierarchy (/app/planning):
┌─────────────────────────────────────────────────────────────────────────┐
│ Planning Hierarchy                        [Tree] [Timeline] [+ Roadmap] │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│ 📍 2026 Product Roadmap                                                 │
│ ├── Q1 2026: Foundation Phase                                           │
│ │   ├── Sprint 84: Teams & Organizations (✅ Closed)                    │
│ │   ├── Sprint 85: AGENTS.md + CLI (✅ Closed)                          │
│ │   ├── Sprint 86: System Settings (🔄 Active)                          │
│ │   └── Sprint 87: Sprint Governance (📋 Planned)                       │
│ │                                                                       │
│ ├── Q2 2026: Scale Phase                                                │
│ │   ├── Sprint 88: VS Code Extension v2 (📋 Planned)                    │
│ │   ├── Sprint 89: Desktop App MVP (📋 Planned)                         │
│ │   ├── Sprint 90: Enterprise Features (📋 Planned)                     │
│ │   └── Sprint 91: Performance Optimization (📋 Planned)                │
│ │                                                                       │
│ └── Q3 2026: Enterprise Phase                                           │
│     ├── Sprint 92: SSO Integration (📋 Planned)                         │
│     ├── Sprint 93: Audit Compliance (📋 Planned)                        │
│     └── ...                                                             │
│                                                                         │
├─────────────────────────────────────────────────────────────────────────┤
│ Selected: Sprint 86 - System Settings                                   │
│ ┌─────────────────────────────────────────────────────────────────────┐ │
│ │ Backlog Items (16 total)                      [+ Add Item] [Bulk]   │ │
│ │                                                                     │ │
│ │ Done (15)                                                           │ │
│ │ ├── ✅ Create SettingsService with Redis caching (2h)               │ │
│ │ ├── ✅ session_timeout_minutes implementation (3h)                  │ │
│ │ ├── ✅ max_login_attempts implementation (10h)                      │ │
│ │ └── ... 12 more items                                               │ │
│ │                                                                     │ │
│ │ In Progress (1)                                                     │ │
│ │ └── 🔄 mfa_required edge case fix (2h)                              │ │
│ │                                                                     │ │
│ │ Carry Over (0)                                                      │ │
│ └─────────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────┘
```

---

### Day 8-9: Navigation & Integration (6 SP)

| Task | Owner | Est | Priority | Status |
|------|-------|-----|----------|--------|
| Update Sidebar with Sprint Governance menu | Frontend | 2h | P0 | ⏳ |
| Create Sprint quick-access header component | Frontend | 2h | P1 | ⏳ |
| Integrate with existing project pages | Frontend | 3h | P1 | ⏳ |
| Add sprint context to Evidence pages | Frontend | 2h | P1 | ⏳ |
| Notification system for gate deadlines | Frontend | 3h | P1 | ⏳ |

**Sidebar Update:**

```tsx
// frontend/src/components/dashboard/Sidebar.tsx

const navigation = [
  { name: "Dashboard", href: "/app", icon: LayoutDashboard },
  { name: "Projects", href: "/app/projects", icon: FolderKanban },
  // NEW: Sprint Governance Section
  {
    name: "Sprint Governance",
    icon: Calendar,
    children: [
      { name: "Active Sprint", href: "/app/sprints/current", icon: PlayCircle },
      { name: "All Sprints", href: "/app/sprints", icon: ListChecks },
      { name: "Planning", href: "/app/planning", icon: GitBranch },
      { name: "Timeline", href: "/app/planning/timeline", icon: GanttChart },
    ],
  },
  // END NEW
  { name: "Gates", href: "/app/gates", icon: ShieldCheck },
  { name: "Evidence", href: "/app/evidence", icon: FileText },
  { name: "Policies", href: "/app/policies", icon: ScrollText },
  { name: "Teams", href: "/app/teams", icon: Users },
  { name: "Organizations", href: "/app/organizations", icon: Building2 },
  { name: "AGENTS.md", href: "/app/agents-md", icon: Bot },
  { name: "App Builder", href: "/app/codegen", icon: Code2 },
  { name: "Settings", href: "/app/settings", icon: Settings },
];
```

---

### Day 10: Testing & Documentation (2 SP)

| Task | Owner | Est | Priority | Status |
|------|-------|-----|----------|--------|
| E2E tests for Sprint Governance | QA | 4h | P0 | ⏳ |
| E2E tests for Planning Hierarchy | QA | 3h | P0 | ⏳ |
| Performance testing | QA | 2h | P1 | ⏳ |
| User documentation | PM | 3h | P1 | ⏳ |

---

## 🔧 Technical Specifications

### API Endpoints Used

| Method | Endpoint | Hook Function |
|--------|----------|---------------|
| GET | `/projects/{id}/roadmaps` | `useRoadmaps(id).roadmaps` |
| POST | `/roadmaps` | `useCreateRoadmap().create()` |
| GET | `/roadmaps/{id}/phases` | `usePhases(id).phases` |
| POST | `/phases` | `useCreatePhase().create()` |
| GET | `/projects/{id}/sprints` | `useSprints(undefined, id).sprints` |
| GET | `/phases/{id}/sprints` | `useSprints(id).sprints` |
| POST | `/sprints` | `useCreateSprint().create()` |
| PATCH | `/sprints/{id}` | `useUpdateSprint(id).update()` |
| GET | `/sprints/{id}/gates/{type}` | `useSprintGate(id, type).gate` |
| POST | `/sprints/{id}/gates/evaluate` | `useEvaluateSprintGate(id).evaluate()` |
| POST | `/sprints/{id}/gates/approve` | `useApproveSprintGate(id).approve()` |
| GET | `/sprints/{id}/gates/{type}/checklist` | `useSprintChecklistItems(id, type).items` |
| GET | `/sprints/{id}/items` | `useBacklogItems(id).items` |
| POST | `/sprints/{id}/items` | `useAddBacklogItem(id).add()` |
| PATCH | `/backlog-items/{id}` | `useUpdateBacklogItem(id).update()` |

### TypeScript Interfaces

```typescript
// frontend/src/lib/types/planning.ts

export type SprintStatus =
  | "planned"      // Not started
  | "active"       // Currently running
  | "closing"      // In close phase (24h window)
  | "closed"       // Completed
  | "cancelled";   // Cancelled

export type GateStatus =
  | "pending"      // Not evaluated
  | "evaluating"   // Currently evaluating
  | "passed"       // All items pass
  | "conditional"  // Pass with waiver
  | "failed";      // Items failed

export interface Roadmap {
  id: string;
  name: string;
  description?: string;
  project_id: string;
  start_date: string;
  end_date: string;
  phases_count: number;
  created_at: string;
}

export interface Phase {
  id: string;
  name: string;
  description?: string;
  roadmap_id: string;
  start_date: string;
  end_date: string;
  sprints_count: number;
  status: "planned" | "active" | "completed";
}

export interface Sprint {
  id: string;
  name: string;
  number: number;
  goal: string;
  project_id: string;
  phase_id?: string;
  start_date: string;
  end_date: string;
  status: SprintStatus;
  story_points_planned: number;
  story_points_completed: number;
  items_total: number;
  items_completed: number;
  items_carried_over: number;
  g_sprint_status: GateStatus;
  g_sprint_close_status: GateStatus;
  documentation_deadline?: string;
  created_at: string;
}

export interface SprintGate {
  id: string;
  sprint_id: string;
  gate_type: "start" | "close";
  status: GateStatus;
  checklist_items: ChecklistItem[];
  evaluated_at?: string;
  approved_at?: string;
  approved_by?: string;
  waiver_reason?: string;
}

export interface ChecklistItem {
  id: string;
  name: string;
  description: string;
  is_mandatory: boolean;
  status: "pending" | "pass" | "fail" | "waived";
  evidence_url?: string;
  notes?: string;
}

export interface BacklogItem {
  id: string;
  title: string;
  description?: string;
  sprint_id?: string;
  project_id: string;
  type: "story" | "task" | "bug" | "spike";
  priority: "p0" | "p1" | "p2" | "p3";
  status: "todo" | "in_progress" | "review" | "done" | "carried_over";
  story_points?: number;
  assignee_id?: string;
  created_at: string;
}

// frontend/src/lib/types/sprint-governance.ts

export interface SprintMetrics {
  velocity: number;
  velocity_trend: number;
  completion_rate: number;
  carry_over_rate: number;
  avg_cycle_time: number;
}

export interface DocumentationDeadline {
  sprint_id: string;
  deadline: string;
  hours_remaining: number;
  is_expired: boolean;
  documents_required: string[];
  documents_submitted: string[];
}
```

---

## 📊 Success Criteria

| Metric | Target | Verification |
|--------|--------|--------------|
| Sprint dashboard loading | <1s | Performance test |
| G-Sprint gate evaluation | <5s | Integration test |
| G-Sprint-Close gate evaluation | <5s | Integration test |
| Planning hierarchy rendering | <2s | Performance test |
| All gate checklist items visible | 100% | E2E test |
| Documentation timer accurate | ±1 min | Manual test |
| Backlog drag-and-drop works | ✅ | E2E test |
| Navigation integration | ✅ | E2E test |

---

## ⚠️ Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Complex gate logic | High | Clear state machine, extensive tests |
| Real-time timer sync | Medium | Use server time, periodic sync |
| Large planning trees | Medium | Virtualization, lazy loading |
| Gate approval permissions | High | Clear RBAC rules, audit trail |

---

## 📅 Timeline Summary

| Day | Focus | Deliverables | Status |
|-----|-------|-------------|--------|
| 1-2 | API Hooks | usePlanningHierarchy.ts, useSprintGovernance.ts | ✅ DONE |
| 3-5 | Sprint Governance | Dashboard, G-Sprint, G-Sprint-Close gates | ✅ DONE |
| 6-7 | Planning Hierarchy | Tree view, Timeline, Backlog | ✅ DONE |
| 8-9 | Integration | Sidebar, Header, Notifications | ⏳ |
| 10 | Testing | E2E tests, Documentation | ⏳ |

---

## 🐛 Bug Fixes During Implementation (January 21, 2026)

### Backend Model Fixes

During testing of Teams/Organizations pages, discovered missing timestamp fields in SQLAlchemy models.

| Issue | File | Fix Applied |
|-------|------|-------------|
| `Organization` missing `deleted_at` field | `backend/app/models/organization.py` | Added `created_at`, `updated_at`, `deleted_at` columns |
| `Team` missing `deleted_at` field | `backend/app/models/team.py` | Added `created_at`, `updated_at`, `deleted_at` columns |
| `TeamMember` using `self.deleted_at` without defining | `backend/app/models/team_member.py` | Added timestamp columns |

**Root Cause:** Model docstrings referenced `deleted_at` but columns were not defined in SQLAlchemy.

### Auth Route Fixes

| Issue | File | Line | Fix Applied |
|-------|------|------|-------------|
| `name=` instead of `full_name=` in User creation | `backend/app/api/routes/auth.py` | L174 | Changed to `full_name=register_data.full_name` |
| Missing `role=` in RegisterResponse | `backend/app/api/routes/auth.py` | L195-202 | Added `role=new_user.role` |
| Same issue in OAuth user creation | `backend/app/api/routes/auth.py` | L888 | Changed to `full_name=user_info.name` |

### Organizations Route Fix

| Issue | File | Fix Applied |
|-------|------|-------------|
| `greenlet_spawn` error when accessing lazy-loaded relationships | `backend/app/api/routes/organizations.py` | Modified `org_to_response()` to avoid accessing `org.teams` and `org.users` directly |

**Root Cause:** Async SQLAlchemy does not support accessing lazy-loaded relationships synchronously.

### E2E Test Fixes

| Issue | Fix Applied |
|-------|-------------|
| Tests failing with `networkidle` wait strategy | Changed to `domcontentloaded` wait strategy |
| Teams/Organizations pages showing error instead of empty state | Added proper empty state handling |

**E2E Test Status:** 114/114 passing ✅

---

## 🔗 Framework Compliance

### SDLC 6.1.0 Pillar 2 Checklist

| Requirement | Implementation | Status |
|-------------|---------------|--------|
| G-Sprint gate | SprintStartGate component | ✅ DONE |
| G-Sprint-Close gate | SprintCloseGate component | ✅ DONE |
| 24h documentation rule | DocumentationTimer component | ✅ DONE |
| Sprint goal mandatory | Validated in CreateSprintModal | ✅ DONE |
| Backlog estimation | Story points required | ✅ DONE |
| Capacity planning | Team capacity input | ✅ DONE |
| Risk documentation | Risk section in sprint | ✅ DONE |
| Evidence manifests | Link to Evidence Vault | ✅ DONE |
| Retrospective required | Retrospective document field | ✅ DONE |
| Next sprint preparation | Cross-sprint linking | ✅ DONE |

---

## Approval

- [ ] **CTO Approval**: This is core SDLC 6.1.0 feature - must be excellent
- [ ] **CPO Approval**: UX/UI specifications
- [ ] **Framework Lead Approval**: SDLC 6.1.0 compliance verification
- [ ] **Frontend Lead Approval**: Implementation approach

---

**Sprint Owner:** Frontend Lead + PM
**Reviewers:** CTO, CPO, Framework Lead
**Created:** January 20, 2026
**Last Updated:** January 21, 2026

---

## 📈 Progress Summary

| Phase | Status | Completion |
|-------|--------|------------|
| P0 Blockers (GitHub Check Run, Evidence Hash Chain) | ✅ COMPLETED | 100% |
| Day 1-2: Planning Hierarchy API Hooks | ✅ COMPLETED | 100% |
| Day 3-5: Sprint Governance Dashboard | ✅ COMPLETED | 100% |
| Day 6-7: Planning Hierarchy Visualization | ✅ COMPLETED | 100% |
| Day 8-9: Navigation & Integration | ⏳ IN PROGRESS | 0% |
| Day 10: Testing & Documentation | ⏳ PENDING | 0% |
| **Overall Sprint Progress** | **~70%** | **Days 1-7 Complete** |

---

## 💡 CTO Note

> "SDLC 6.1.0 được nâng cấp chính là Sprint Governance. Bản thân SDLC Orchestrator phải làm tốt được việc này. Đây là 'eating our own dog food' - nếu chúng ta không thể quản lý sprint của chính mình bằng công cụ của mình, làm sao khách hàng tin tưởng?"

This sprint is critical for framework credibility. Execute with excellence.
