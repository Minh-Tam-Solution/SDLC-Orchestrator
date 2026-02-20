# Sprint 91-100: Features Matrix Gap Closure + Expert Workflow Enhancements

**Planning Date:** January 22, 2026  
**Status:** 📋 PLANNED (91-96) + CTO APPROVED (97-100)  
**Framework:** SDLC 6.1.0 (7-Pillar Architecture)  
**CTO Approval:** ✅ Approved (Jan 22, 2026)

---

## Executive Summary

Based on comprehensive FEATURES-MATRIX.md analysis (v1.1.0), identified **70+ features** with status 📋 (Planned) across 4 clients. This plan organizes them into 6 sprints to achieve **95% Web coverage** by soft launch (March 1, 2026).

### Current Status vs Target

| Client | Current | Sprint 96 Target | Gap |
|--------|---------|------------------|-----|
| Web Dashboard | 53% | 95% | +42% |
| CLI (sdlcctl) | 13% | 43% | +30% |
| VSCode Extension | 37% | 63% | +26% |
| Desktop App | 0% | 0% | Deferred to Q3 2026 |

---

## Framework-First Principle (CTO Mandated)

> **"Any feature added to SDLC Orchestrator MUST have Framework methodology documented BEFORE tool implementation."**

### Compliance Verification (Jan 22, 2026)

| Feature Area | Framework Status | Orchestrator Status | Aligned? |
|--------------|------------------|---------------------|----------|
| **AGENTS.md** | ADR-029 (Jan 22) | Sprint 80-81 (Jan 19) | ⚠️ Tool led Framework |
| **Planning Hierarchy** | Pillar 2 (SDLC 6.1.0) | Sprint 74-77, 87, 92 | ✅ Framework First |
| **SASE Artifacts** | SASE-Artifacts README | Sprint 82-83 | ✅ Framework First |
| **Evidence Manifest** | TDS-082-001 | Sprint 82 | ✅ Framework First |
| **Teams/Orgs** | Pillar 3 (Roles) | Sprint 84, 91 | ✅ Framework First |

**Note:** AGENTS.md implementation (Sprint 80-81) preceded formal ADR-029. This is acceptable because:
1. Based on industry standard (agents.md - 60K+ projects)
2. Framework ADR formalized existing industry practice
3. No breaking changes required

---

## Priority Matrix

### P0 - Launch Blockers (Must Have for Soft Launch)
- Teams & Organizations UI (Sprint 91) ✅ COMPLETE
- Team Member Management (Sprint 91) ✅ COMPLETE
- GitHub Integration Enhancement (Sprint 90) ✅ COMPLETE

### P1 - Core Features (Needed for MVP)
- Planning Hierarchy UI (Sprint 92-93) 🔄 IN PROGRESS
- AGENTS.md Web UI (Sprint 94) 📋
- Evidence Manifest UI (Sprint 95) 📋

### P2 - Growth Features (Post-Launch)
- Advanced Analytics (Sprint 96)
- Bulk Operations
- Desktop App (Q3 2026)

---

## Sprint 91: Teams & Organizations UI (Jan 25-30, 2026)

**Duration:** 4 days (Jan 25-30, excluding weekend)  
**Priority:** P0 - Launch Blocker  
**Story Points:** 34 SP

### 91.1 Objectives

Close critical gap in Teams & Organizations management - **STATUS: ✅ COMPLETE (Jan 22, 2026)** - 95% implemented before sprint started, remaining 5% completed in 1 day.

### 91.2 Features

| Feature | Priority | SP | Status |
|---------|----------|----|----|
| Create Team | P0 | 5 | ✅ (Pre-Sprint) |
| List Teams | P0 | 3 | ✅ (Pre-Sprint) |
| Update Team | P0 | 3 | ✅ Sprint 91 |
| Delete Team | P0 | 3 | ✅ (Pre-Sprint) |
| Add Team Member | P0 | 5 | ✅ (Pre-Sprint) |
| Remove Team Member | P0 | 3 | ✅ (Pre-Sprint) |
| Update Member Role | P0 | 5 | ✅ (Pre-Sprint) |
| Team Statistics | P1 | 3 | ✅ (Pre-Sprint) |
| Team Switcher | P1 | 2 | ✅ Sprint 91 |
| Create Organization | P0 | 2 | ✅ (Pre-Sprint) |
| Edit Organization | P0 | 2 | ✅ Sprint 91 |
| canManage Permission Fix | P0 | 1 | ✅ Sprint 91 |

**Sprint 91 Result:** 8 days ahead of schedule (Jan 22 vs Jan 30 planned)

### 91.3 Implementation Plan

#### Day 1-2: Teams CRUD (16h)

**Files:**
- `frontend/src/app/app/teams/page.tsx` - Teams list page
- `frontend/src/app/app/teams/[id]/page.tsx` - Team detail page
- `frontend/src/app/app/teams/[id]/settings/page.tsx` - Team settings
- `frontend/src/hooks/useTeams.ts` - Teams hooks (enhance existing)
- `frontend/src/lib/api/teams.ts` - Teams API client (enhance existing)

**UI Components:**
```typescript
// Teams List View
- DataTable with teams
- Search/filter by name
- Create Team button
- Team card with stats (members, projects)

// Team Detail View
- Team info (name, slug, description)
- Members list with roles
- Projects assigned to team
- Team settings button

// Create/Edit Team Modal
- Name (required)
- Slug (auto-generated)
- Description (optional)
- Organization selector
```

#### Day 3: Team Member Management (8h)

**Features:**
```typescript
// Add Member Modal
- User search/autocomplete
- Role selector (SASE roles: OWNER, ADMIN, MEMBER, etc.)
- Validation (user not already in team)

// Member Actions
- Update role (dropdown)
- Remove member (confirm dialog)
- Transfer ownership (special flow)

// Permissions
- Only OWNER can delete team
- Only OWNER/ADMIN can add/remove members
- Members can view only
```

#### Day 4: Organizations + Polish (8h)

**Organizations UI:**
```typescript
// Organization Switcher (Navbar)
- Current org name + logo
- Dropdown with user's orgs
- Create org button
- Switch org (reload context)

// Organization Settings Page
- Org info (name, slug, logo)
- Billing info
- Member count
- Team count
- Delete organization (danger zone)
```

### 91.4 API Endpoints Used

```
POST   /api/v1/teams                    - Create team
GET    /api/v1/teams                    - List teams
GET    /api/v1/teams/{id}               - Get team details
PUT    /api/v1/teams/{id}               - Update team
DELETE /api/v1/teams/{id}               - Delete team
POST   /api/v1/teams/{id}/members       - Add member
DELETE /api/v1/teams/{id}/members/{uid} - Remove member
PUT    /api/v1/teams/{id}/members/{uid} - Update role
GET    /api/v1/teams/{id}/stats         - Team statistics

GET    /api/v1/organizations            - List organizations
POST   /api/v1/organizations            - Create organization
GET    /api/v1/organizations/{id}       - Get org details
PUT    /api/v1/organizations/{id}       - Update org
```

### 91.5 Success Criteria

- ✅ Create/list/update/delete teams working
- ✅ Add/remove team members with role assignment
- ✅ Organization switcher functional
- ✅ Team statistics displaying correctly
- ✅ E2E tests: 8 scenarios (CRUD + members)
- ✅ No breaking changes to existing project-team links

---

## Sprint 92: Planning Hierarchy Part 1 (Jan 22-24, 2026)

**Duration:** 2 days (accelerated)
**Priority:** P1 - Core Feature
**Story Points:** 29 SP
**Status:** ✅ **100% COMPLETE** (1 day ahead of schedule)

### 92.0 Framework-First Alignment

**ADR-029 Compliance Check:**
- ✅ AGENTS.md Framework: Documented in SDLC-Enterprise-Framework (ADR-029)
- ✅ Planning Hierarchy: Framework methodology in Pillar 2 (Sprint Planning Governance)
- ✅ SASE Artifacts: CRP/MRP/VCR retained, BRS/MTS/LPS deprecated
- ✅ Tool Implementation: Follows Framework methodology

### 92.1 Objectives

Implement Roadmap and Phase management - **STATUS: ✅ 100% COMPLETE (Jan 22, 2026)**

### 92.2 Features

| Feature | Priority | SP | Status |
|---------|----------|----|----|
| View Roadmap | P1 | 5 | ✅ Tree view exists |
| Create/Edit Roadmap | P1 | 5 | ✅ RoadmapModal complete (Day 1) |
| View Phases | P1 | 3 | ✅ Tree view exists |
| Create/Edit Phase | P1 | 5 | ✅ PhaseModal complete (Day 1) |
| Roadmap Timeline View | P1 | 5 | ✅ Timeline view exists |
| Phase Gantt Chart | P2 | 3 | 📋 Deferred to Sprint 93 |
| Edit/Delete Actions | P1 | 2 | ✅ Tree action menu (Day 2) |
| E2E Tests | P1 | 4 | ✅ 5 scenarios, 486 lines |

**Sprint 92 Result:** ✅ **100% COMPLETE** (Jan 22, 2026 - 1 day ahead)

### 92.3 Implementation Summary (Jan 22, 2026)

**Day 1 - Modals & Integration:**

**Files Created:**
- ✅ `frontend/src/app/app/planning/components/RoadmapModal.tsx` - Create/edit roadmap modal
- ✅ `frontend/src/app/app/planning/components/PhaseModal.tsx` - Create/edit phase modal  
- ✅ `frontend/src/app/app/planning/components/index.ts` - Component exports

**Files Modified:**
- ✅ `frontend/src/app/app/planning/page.tsx` - Modal integration
- ✅ `frontend/src/contexts/WorkspaceContext.tsx` - Fixed type errors

**Day 1 Features:**
1. RoadmapModal: Create + Edit, duration display (months), validation
2. PhaseModal: Theme suggestions, SDLC 6.1.0 duration (4-8 weeks), validation
3. Planning page: Modal state management, "New Roadmap" button
4. Bug fix: WorkspaceContext (orgsData.items, teamsData.items)

---

**Day 2 - Edit/Delete Actions:**

**Files Modified:**
- ✅ `frontend/src/app/app/planning/components/PlanningHierarchyTree.tsx` - Action menu (⋮)
- ✅ `frontend/src/app/app/planning/page.tsx` - Delete confirmation + handlers

**Day 2 Features:**
1. **Tree Action Menu (⋮)**: Hover menu on Roadmap/Phase nodes
   - Edit Roadmap/Phase: Opens modal with data pre-filled
   - Delete: Confirmation dialog with cascade warning
   - Add Phase (Roadmap): Quick create child phase
   - Add Sprint (Phase): Navigate to sprint creation

2. **Delete Confirmation Dialog**:
   - Item name display
   - Cascade deletion warning
   - Loading state during deletion
   - Cancel/Delete buttons

3. **Technical Implementation**:
   - `TreeNodeActions` interface for callbacks
   - `ActionMenu`/`ActionMenuItem` components (click-outside close)
   - `useDeleteRoadmap`/`useDeletePhase` hooks with cache invalidation
   - Full TypeScript type safety

---

**E2E Tests (Day 3):**

**File Created:**
- ✅ `frontend/e2e/sprint92-planning-hierarchy.spec.ts` (486 lines)

**Test Scenarios (5):**
1. ✅ Create roadmap: Form validation, API call, tree update
2. ✅ Edit roadmap: Pre-fill form, save changes, cache invalidation
3. ✅ Create phase within roadmap: Parent selection, theme suggestions, duration validation
4. ✅ Delete roadmap with cascade: Confirmation dialog, warning message, cascade deletion
5. ✅ Timeline view navigation: Roadmap selection, phase display, date ranges

**Coverage:** All planning hierarchy features tested end-to-end

---

**Sprint 92 Completion Summary:**

| Metric | Target | Achieved | Status |
|--------|--------|----------|--------|
| Story Points | 29 SP | 29 SP | ✅ 100% |
| Timeline | 2 days | 1 day | ✅ 1 day ahead |
| Features | 8 | 8 | ✅ All complete |
| E2E Tests | 5 scenarios | 5 scenarios, 486 lines | ✅ Comprehensive |
| Web Coverage | 80% | 80% | ✅ Target met |
| Build Status | Passing | Passing | ✅ All green |
  - Delete roadmap (cascade test)
  - Timeline view navigation

Implement Roadmap and Phase management - first half of Planning Hierarchy (Sprint 74-77 scope).

### 92.2 Features

| Feature | Priority | SP | Status |
|---------|----------|----|----|
| View Roadmap | P1 | 5 | ✅ Pre-existing (Sprint 87) |
| Create/Edit Roadmap | P1 | 5 | ✅ Sprint 92 (Jan 22) |
| View Phases | P1 | 3 | ✅ Pre-existing (Sprint 87) |
| Create/Edit Phase | P1 | 5 | ✅ Sprint 92 (Jan 22) |
| Roadmap Timeline View | P1 | 5 | ✅ Pre-existing (Sprint 87) |
| Phase Gantt Chart | P2 | 3 | 📋 Deferred to Sprint 93 |
| Edit/Delete in Tree View | P1 | 3 | ✅ Day 2 (Jan 22) |

### 92.3 Completed Work (Jan 22, 2026)

**New Files Created:**
- `frontend/src/app/app/planning/components/RoadmapModal.tsx` (330 lines)
- `frontend/src/app/app/planning/components/PhaseModal.tsx` (460 lines)
- `frontend/src/app/app/planning/components/index.ts`

**Files Modified:**
- `frontend/src/app/app/planning/page.tsx` - Connected modals to "New Roadmap" button
- `frontend/src/contexts/WorkspaceContext.tsx` - Fixed type error (items vs organizations/teams)

**Pre-existing Infrastructure (Sprint 87):**
- `frontend/src/app/app/planning/page.tsx` - Planning page with Tree View + Timeline View
- `frontend/src/hooks/usePlanningHierarchy.ts` (578 lines) - Full CRUD hooks
- `frontend/src/app/app/sprints/components/PlanningHierarchyTree.tsx` (511 lines)
- `frontend/src/lib/types/planning.ts` (555 lines) - Complete TypeScript types

**Validation:**
- ✅ Next.js build: SUCCESS
- ✅ TypeScript: No errors in Planning components
- ✅ Modals: Create Roadmap and Create Phase functional

### 92.4 Day 2 Completed Work (Jan 22, 2026)

**Files Modified:**
- `frontend/src/app/app/sprints/components/PlanningHierarchyTree.tsx` - Added action menu
- `frontend/src/app/app/planning/page.tsx` - Added delete confirmation, action handlers

**Features Implemented:**
1. **Action Menu (⋮)**: Dropdown on hover for Roadmap/Phase nodes
   - Edit Roadmap/Phase: Opens modal with existing data
   - Delete: Opens confirmation dialog
   - Add Phase: Quick create child phase
   - Add Sprint: Navigate to sprint creation page
2. **Delete Confirmation Dialog**: Reusable component with warning
3. **TreeNodeActions Interface**: Callbacks for all CRUD operations
4. **Full TypeScript Type Safety**: Proper Roadmap/Phase object construction

**Technical Details:**
- ActionMenu/ActionMenuItem components with click-outside close
- useDeleteRoadmap/useDeletePhase hooks with cache invalidation
- roadmapId passed through delete flow for proper query invalidation

### 92.5 Remaining Work

#### E2E Tests (4h)

**Scenarios:**
1. Create new roadmap via modal
2. Edit existing roadmap via action menu
3. Delete roadmap with confirmation
4. Create phase within roadmap via "Add Phase"
5. View planning hierarchy tree

### 92.4 API Endpoints

```
GET    /api/v1/planning/roadmaps
POST   /api/v1/planning/roadmaps
GET    /api/v1/planning/roadmaps/{id}
PUT    /api/v1/planning/roadmaps/{id}
DELETE /api/v1/planning/roadmaps/{id}

GET    /api/v1/planning/phases
POST   /api/v1/planning/phases
GET    /api/v1/planning/phases/{id}
PUT    /api/v1/planning/phases/{id}
DELETE /api/v1/planning/phases/{id}
```

### 92.6 Success Criteria

- ✅ Roadmap CRUD functional (Create/Edit/Delete)
- ✅ Phase CRUD functional (Create/Edit/Delete)
- ✅ Timeline visualization working
- ✅ Roadmap-Phase hierarchy enforced
- ✅ Action menu for tree node operations
- ✅ Delete confirmation with warning
- 📋 E2E tests: 5 scenarios (pending)

---

## Sprint 93: Planning Hierarchy Part 2 (Feb 6-11, 2026)

**Duration:** 4 days  
**Priority:** P1 - Core Feature  
**Story Points:** 29 SP

### 93.1 Objectives

Complete Planning Hierarchy with Sprint and Backlog management.

### 93.2 Features

| Feature | Priority | SP | Status |
|---------|----------|----|----|
| View Sprints | P1 | 3 | 📋 |
| Create Sprint | P1 | 5 | 📋 |
| Sprint Detail | P1 | 5 | 📋 |
| Sprint Analytics | P1 | 5 | 📋 |
| Burndown Chart | P1 | 3 | 📋 |
| View Backlog | P1 | 3 | 📋 |
| Create Backlog Item | P1 | 3 | 📋 |
| Bulk Move to Sprint | P2 | 2 | 📋 |

### 93.3 Implementation Plan

#### Day 1-2: Sprint Management (16h)

**Files:**
- `frontend/src/app/app/planning/sprints/page.tsx`
- `frontend/src/app/app/planning/sprints/[id]/page.tsx`
- `frontend/src/components/planning/SprintBoard.tsx`
- `frontend/src/components/charts/BurndownChart.tsx`

**UI:**
```typescript
// Sprint List View
- Active sprint (highlight)
- Upcoming sprints
- Past sprints (collapsed)
- Create sprint button

// Sprint Detail View
- Sprint info (name, dates, goals)
- Backlog items (Kanban board)
- Burndown chart
- Sprint velocity
- Team capacity

// Create Sprint Form
- Name (auto: "Sprint N")
- Start date
- End date (default: 2 weeks)
- Goals (markdown)
- Phase selector
```

#### Day 3-4: Backlog Management (16h)

**Features:**
```typescript
// Backlog View
- Prioritized list
- Story points
- Status (TODO, IN_PROGRESS, DONE)
- Add item button
- Bulk actions

// Backlog Item Form
- Title (required)
- Description (markdown)
- Story points
- Priority (P0-P3)
- Assignee (team member)
- Sprint (optional)
- Tags

// Bulk Move
- Select multiple items
- Move to sprint (dropdown)
- Confirm dialog
```

### 93.4 API Endpoints

```
GET    /api/v1/planning/sprints
POST   /api/v1/planning/sprints
GET    /api/v1/planning/sprints/{id}
PUT    /api/v1/planning/sprints/{id}
DELETE /api/v1/planning/sprints/{id}
GET    /api/v1/planning/sprints/{id}/burndown

GET    /api/v1/planning/backlog
POST   /api/v1/planning/backlog
GET    /api/v1/planning/backlog/{id}
PUT    /api/v1/planning/backlog/{id}
DELETE /api/v1/planning/backlog/{id}
POST   /api/v1/planning/backlog/bulk-move
```

### 93.5 Success Criteria

- ✅ Sprint CRUD functional
- ✅ Backlog CRUD functional
- ✅ Burndown chart rendering
- ✅ Bulk move working
- ✅ Sprint-Backlog hierarchy enforced
- ✅ E2E tests: 8 scenarios

---

## Sprint 94: AGENTS.md Web UI (Feb 12-17, 2026)

**Duration:** 4 days  
**Priority:** P1 - Core Feature (TRUE MOAT)  
**Story Points:** 21 SP

### 94.1 Objectives

Bring AGENTS.md management to Web UI - currently only CLI/VSCode have it.

### 94.2 Features

| Feature | Priority | SP | Status |
|---------|----------|----|----|
| Generate AGENTS.md | P1 | 5 | 📋 |
| View AGENTS.md | P1 | 3 | 📋 |
| Validate AGENTS.md | P1 | 3 | 📋 |
| Dynamic Context Overlay | P1 | 5 | 📋 |
| Context History | P1 | 3 | 📋 |
| Multi-Repo Dashboard | P2 | 2 | 📋 |

### 94.3 Implementation Plan

#### Day 1-2: Generator & Viewer (16h)

**Files:**
- `frontend/src/app/app/agents-md/page.tsx`
- `frontend/src/app/app/agents-md/[project_id]/page.tsx`
- `frontend/src/components/agents-md/Generator.tsx`
- `frontend/src/components/agents-md/Viewer.tsx`

**UI:**
```typescript
// AGENTS.md Dashboard
- Project selector
- Current AGENTS.md status
- Generate button
- Validate button
- View history button

// Generator Form
- Project info (auto-populated)
- Tier selection
- Stage mapping preview
- Custom rules (optional)
- Generate button (async)

// Viewer Component
- Monaco editor (read-only)
- Syntax highlighting
- Line numbers
- Copy button
- Download button
- Validation status badge
```

#### Day 3: Validator & Dynamic Context (8h)

**Features:**
```typescript
// Validator
- Structure check (≤150 lines)
- Required sections check
- Format validation
- Auto-fix suggestions
- Validation report

// Dynamic Context Overlay
- Current gate status overlay
- Stage-specific rules injection
- Known issues section
- Temporary restrictions
- Preview before apply
```

#### Day 4: Context History & Polish (8h)

**Features:**
```typescript
// Context History
- Timeline of AGENTS.md changes
- Gate-triggered updates
- Manual edits
- Diff view
- Restore previous version

// Multi-Repo Dashboard
- All projects with AGENTS.md
- Compliance status
- Last updated
- Bulk regenerate button
```

### 94.4 API Endpoints

```
POST   /api/v1/agents-md/generate       - Generate AGENTS.md
GET    /api/v1/agents-md/{project_id}   - Get current AGENTS.md
POST   /api/v1/agents-md/validate       - Validate AGENTS.md
POST   /api/v1/agents-md/lint           - Lint AGENTS.md
GET    /api/v1/agents-md/{project_id}/context - Get dynamic context
GET    /api/v1/agents-md/{project_id}/history - Get change history
POST   /api/v1/agents-md/bulk-regenerate      - Regenerate multiple
```

### 94.5 Success Criteria

- ✅ Generate AGENTS.md from Web UI
- ✅ View AGENTS.md with syntax highlighting
- ✅ Validation working with auto-fix
- ✅ Dynamic context overlay functional
- ✅ Context history displaying correctly
- ✅ E2E tests: 6 scenarios

---

## Sprint 95: Evidence Manifest UI (Feb 18-23, 2026)

**Duration:** 4 days  
**Priority:** P1 - Compliance Feature  
**Story Points:** 18 SP

### 95.1 Objectives

Implement Evidence Manifest (Sprint 82 backend) UI for tamper-evident evidence tracking.

### 95.2 Features

| Feature | Priority | SP | Status |
|---------|----------|----|----|
| Evidence Manifest View | P1 | 5 | 📋 |
| Tamper-Evident Verification | P1 | 5 | 📋 |
| Hash Chain Visualization | P1 | 5 | 📋 |
| Manifest Timeline | P1 | 3 | 📋 |

### 95.3 Implementation Plan

#### Day 1-2: Manifest Viewer (16h)

**Files:**
- `frontend/src/app/app/evidence/manifests/page.tsx`
- `frontend/src/app/app/evidence/manifests/[id]/page.tsx`
- `frontend/src/components/evidence/ManifestViewer.tsx`
- `frontend/src/components/evidence/HashChainVisual.tsx`

**UI:**
```typescript
// Manifest List View
- Manifest ID
- Created at
- Artifact count
- Verification status
- View button

// Manifest Detail View
- Manifest metadata
- Artifacts list (with SHA256)
- Previous manifest link (chain)
- Signature verification
- Download manifest button

// Hash Chain Visualization
- Visual graph of manifest chain
- Integrity status indicators
- Tamper detection alerts
```

#### Day 3-4: Verification & Timeline (16h)

**Features:**
```typescript
// Tamper-Evident Verification
- Verify manifest signature
- Check hash chain integrity
- Artifact existence check
- Verification report
- Alert on tampering

// Manifest Timeline
- Chronological view
- Gate-evidence associations
- Manifest creation events
- Verification events
- Anomaly markers
```

### 95.4 API Endpoints

```
GET    /api/v1/evidence-manifest
GET    /api/v1/evidence-manifest/{id}
POST   /api/v1/evidence-manifest/verify
GET    /api/v1/evidence-manifest/{id}/chain
GET    /api/v1/evidence-manifest/{id}/timeline
```

### 95.5 Success Criteria

- ✅ View evidence manifests
- ✅ Verify manifest integrity
- ✅ Visualize hash chain
- ✅ Timeline displaying correctly
- ✅ Tamper detection working
- ✅ E2E tests: 4 scenarios

---

## Sprint 96: Advanced Analytics (Feb 24-28, 2026)

**Duration:** 3 days (before Go/No-Go review)  
**Priority:** P2 - Growth Feature  
**Story Points:** 13 SP

### 96.1 Objectives

Enhanced analytics for Go/No-Go review showcase.

### 96.2 Features

| Feature | Priority | SP | Status |
|---------|----------|----|----|
| DAU Metrics | P2 | 3 | 📋 |
| AI Safety Metrics | P2 | 5 | 📋 |
| DORA Metrics | P2 | 3 | 📋 |
| Export Reports | P2 | 2 | 📋 |

### 96.3 Implementation Plan

#### Day 1: DAU & AI Safety (8h)

**UI:**
```typescript
// DAU Dashboard
- Daily Active Users chart
- User retention cohorts
- Feature usage heatmap
- Active projects gauge

// AI Safety Metrics
- Gate pass/fail rates
- Policy violation trends
- Override request trends
- AI-generated code %
```

#### Day 2: DORA Metrics (8h)

**Metrics:**
```typescript
// DORA 4 Metrics
1. Deployment Frequency
2. Lead Time for Changes
3. Change Failure Rate
4. Time to Restore Service

// Visualizations
- Line charts
- Comparison tables
- Trend indicators
- Industry benchmarks
```

#### Day 3: Export & Polish (8h)

**Features:**
```typescript
// Export Reports
- PDF export
- Excel export
- CSV export
- Custom date range
- Report templates

// Polish
- Loading states
- Error handling
- Responsive design
- Tooltips
```

### 96.4 Success Criteria

- ✅ DAU metrics displaying
- ✅ AI Safety dashboard functional
- ✅ DORA metrics calculated correctly
- ✅ Export working (PDF/Excel)
- ✅ E2E tests: 3 scenarios

---

## Sprint 97-100: Expert Workflow Enhancements (Mar 1 - Mar 28, 2026)

> **CTO Approved:** January 22, 2026  
> **Source:** Expert AI Coding Workflow Analysis (2026)  
> **Status:** 📋 PLANNED (Post Go/No-Go)

### Background

Based on comprehensive analysis of expert AI coding workflow (Jan 22, 2026), identified key enhancements to further improve SDLC Orchestrator's agentic capabilities. Current alignment: **92%** with expert workflow. These sprints close the remaining **8% gap**.

### Priority Matrix (CTO Approved)

| Enhancement | Priority | Sprint | Status |
|-------------|----------|--------|--------|
| EP-10: Planning Sub-agents | P1 | 97-99 | 📋 APPROVED |
| EP-11: Feedback Loop Closure | P1 | 100 | 📋 APPROVED |
| EP-09: Spec Generation | P2 | Q3 2026 | ⏸️ DEFERRED |
| EP-12: Model Routing | P3 | Q4 2026 | ⏸️ DEFERRED |

---

## Sprint 97: ADR-034 + Planning Sub-agent Architecture (Mar 1-7, 2026)

**Duration:** 5 days  
**Priority:** P1 - Expert Workflow Core  
**Story Points:** 21 SP  
**Prerequisite:** Framework-First compliance (ADR-034)

### 97.1 Objectives

Create framework documentation and design architecture for Planning Sub-agent Orchestration.

### 97.2 Features

| Feature | Priority | SP | Status |
|---------|----------|----|----|
| ADR-034: Planning Sub-agent Orchestration | P1 | 5 | 📋 |
| `sdlcctl plan` Command Design | P1 | 8 | 📋 |
| AI Council Service Refactor Evaluation | P1 | 5 | 📋 |
| CLAUDE.md Update (AI Best Practices 2026) | P1 | 3 | 📋 |

### 97.3 Implementation Plan

#### Day 1-2: Framework Documentation (16h)

**ADR-034: Planning Sub-agent Orchestration**
```markdown
# ADR-034: Planning Sub-agent Orchestration

## Context
Expert AI workflow analysis (Jan 2026) identified that pre-planning
pattern extraction via sub-agents prevents architectural drift.
Key insight: "Agentic grep > RAG for context retrieval"

## Decision
1. Add `sdlcctl plan <task>` command
2. Spawns explore sub-agents for:
   - Similar implementations (agentic grep)
   - Related ADRs and patterns
   - Existing test patterns
3. Synthesizes findings into implementation plan
4. Human approval gate before execution

## Consequences
- Prevents architectural drift (15+ LOC changes)
- Builds on established patterns
- Maintains codebase consistency
```

**CLAUDE.md Update:**
```yaml
## AI Agent Best Practices (2026)

### Planning Mode (CRITICAL for >15 LOC changes)
- ALWAYS use planning mode for changes >15 LOC
- Planning spawns explore sub-agents → extract patterns
- Agentic grep > RAG for context retrieval

### Model Selection Matrix
- Opus 4.5 (70%): Large features, multi-file changes
- Sonnet 4.5: Small fixes, reviews, changelog
- GPT 5.2: Architecture, debugging when stuck
- Gemini 3 Pro: Design, creativity, large context
- Haiku 4.5: Quick answers, micro-edits

### Sub-agents Usage
- ✅ Use for: Research, thinking, pattern exploration
- ❌ Avoid: Parallel editing in same project
- Fork sessions to learn without polluting context

### Developer Role Evolution
- Design feedback loops, NOT write code
- Monitor agent, identify patterns, update context
- Make high-level architecture decisions
```

#### Day 3-4: Architecture Design (16h)

**`sdlcctl plan` Command Architecture:**
```python
# backend/sdlcctl/commands/plan.py

@app.command()
def plan(
    task: str = typer.Argument(..., help="Task description"),
    project_path: Path = typer.Option(".", help="Project root"),
    depth: int = typer.Option(3, help="Search depth for patterns"),
    auto_approve: bool = typer.Option(False, help="Skip approval gate"),
):
    """
    Planning mode with sub-agent orchestration.
    
    Spawns explore sub-agents to:
    1. Search similar implementations (agentic grep)
    2. Extract patterns from ADRs
    3. Identify test patterns
    4. Synthesize implementation plan
    
    Example:
        sdlcctl plan "Add user authentication with OAuth2"
        sdlcctl plan "Refactor payment service" --depth 5
    """
```

#### Day 5: AI Council Evaluation (8h)

**Evaluate Refactor vs New Service:**
```yaml
Option A: Refactor AI Council Service (Sprint 26)
  Pros:
    - Existing task decomposition logic
    - Multi-provider integration ready
    - Tested in production
  Cons:
    - Current focus is decomposition, not exploration
    - May require significant refactoring
    
Option B: New Planning Sub-agent Service
  Pros:
    - Clean architecture for exploration
    - Isolated context windows
    - Purpose-built for pattern extraction
  Cons:
    - New service to maintain
    - Potential duplication with AI Council

Recommendation: Hybrid approach
  - Extend AI Council with exploration capability
  - New PlanningOrchestrator class that uses AI Council
  - Shared multi-provider infrastructure
```

### 97.4 Success Criteria

- ✅ ADR-034 created and CTO approved
- ✅ CLAUDE.md updated with AI Best Practices 2026
- ✅ `sdlcctl plan` command architecture documented
- ✅ AI Council refactor decision made
- ✅ Sprint 98-99 backlog refined

---

## Sprint 98: Planning Sub-agent Implementation Part 1 (Mar 8-14, 2026)

**Duration:** 5 days  
**Priority:** P1 - Expert Workflow Core  
**Story Points:** 26 SP

### 98.1 Objectives

Implement core planning sub-agent service with pattern extraction.

### 98.2 Features

| Feature | Priority | SP | Status |
|---------|----------|----|----|
| PlanningOrchestrator Service | P1 | 8 | 📋 |
| Pattern Extraction (Agentic Grep) | P1 | 8 | 📋 |
| ADR Pattern Scanner | P1 | 5 | 📋 |
| Test Pattern Scanner | P1 | 5 | 📋 |

### 98.3 Implementation Plan

**Files to Create:**
```
backend/app/services/planning_orchestrator_service.py
backend/app/services/pattern_extraction_service.py
backend/sdlcctl/commands/plan.py
tests/unit/services/test_planning_orchestrator.py
tests/integration/test_plan_command.py
```

**Core Service:**
```python
# backend/app/services/planning_orchestrator_service.py

class PlanningOrchestratorService:
    """
    Orchestrates planning sub-agents for pre-implementation analysis.
    Key insight: Agentic grep > RAG for context retrieval.
    """
    
    async def plan(self, task: str, project_path: Path) -> PlanningResult:
        """
        Execute planning mode with sub-agent orchestration.
        
        Steps:
        1. Spawn explore sub-agents (parallel)
        2. Extract patterns from codebase
        3. Extract patterns from ADRs
        4. Identify test patterns
        5. Synthesize implementation plan
        6. Return for human approval
        """
        
    async def _spawn_explore_agents(self, task: str) -> list[ExploreResult]:
        """Spawn 3-5 explore sub-agents with isolated contexts."""
        
    async def _extract_patterns(self, results: list[ExploreResult]) -> PatternSummary:
        """Synthesize exploration results into pattern summary."""
        
    async def _generate_plan(self, patterns: PatternSummary) -> ImplementationPlan:
        """Generate implementation plan building on existing patterns."""
```

### 98.4 Success Criteria

- ✅ PlanningOrchestratorService implemented
- ✅ Pattern extraction working (agentic grep)
- ✅ ADR scanner finding relevant patterns
- ✅ Unit tests: 80% coverage
- ✅ Integration test: `sdlcctl plan` basic flow

---

## Sprint 99: Planning Sub-agent Implementation Part 2 (Mar 15-21, 2026)

**Duration:** 5 days  
**Priority:** P1 - Expert Workflow Core  
**Story Points:** 24 SP

### 99.1 Objectives

Complete planning sub-agent with UI integration and conformance checking.

### 99.2 Features

| Feature | Priority | SP | Status |
|---------|----------|----|----|
| Conformance Check Service | P1 | 8 | 📋 |
| Plan Approval UI | P1 | 8 | 📋 |
| GitHub Check Integration | P2 | 5 | 📋 |
| E2E Tests | P1 | 3 | 📋 |

### 99.3 Implementation Plan

**Conformance Check:**
```python
# backend/app/services/conformance_check_service.py

class ConformanceCheckService:
    """
    Compare proposed changes against established patterns.
    Prevents architectural drift.
    """
    
    async def check(self, proposed_diff: str, patterns: PatternSummary) -> ConformanceResult:
        """
        Returns:
        - conformance_score: 0-100
        - deviations: list of pattern violations
        - recommendations: list of suggested changes
        - requires_adr: bool (if new pattern introduced)
        """
```

**Plan Approval UI:**
```typescript
// frontend/src/app/app/planning/plan-review/page.tsx

// Features:
// - Display extracted patterns
// - Show implementation plan
// - Conformance score visualization
// - Approve/Reject/Request Changes buttons
// - ADR creation trigger (if new pattern)
```

**GitHub Check Integration:**
```yaml
# .github/workflows/pattern-conformance.yml

name: Pattern Conformance Check
on: [pull_request]

jobs:
  conformance:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Run Conformance Check
        run: sdlcctl plan --check --diff ${{ github.event.pull_request.diff_url }}
      - name: Post Results
        uses: actions/github-script@v7
        with:
          script: |
            // Post conformance score as PR comment
```

### 99.4 Success Criteria

- ✅ Conformance check working
- ✅ Plan approval UI functional
- ✅ GitHub Check integration (optional)
- ✅ E2E tests: 5 scenarios
- ✅ Documentation complete

---

## Sprint 100: Feedback Loop Closure - EP-11 (Mar 22-28, 2026)

**Duration:** 5 days  
**Priority:** P1 - Expert Workflow Core  
**Story Points:** 21 SP

### 100.1 Objectives

Close the feedback loop from PR review → specification refinement.

### 100.2 Features

| Feature | Priority | SP | Status |
|---------|----------|----|----|
| `pr_learnings` Table Migration | P1 | 3 | 📋 |
| FeedbackLearningService | P1 | 8 | 📋 |
| PR Comment Analyzer | P1 | 5 | 📋 |
| Monthly Aggregation Job | P2 | 3 | 📋 |
| CLAUDE.md Auto-Update (Quarterly) | P2 | 2 | 📋 |

### 100.3 Implementation Plan

**Database Migration:**
```python
# backend/alembic/versions/xxx_add_pr_learnings.py

def upgrade():
    op.create_table(
        'pr_learnings',
        sa.Column('id', UUID, primary_key=True),
        sa.Column('project_id', UUID, sa.ForeignKey('projects.id')),
        sa.Column('pr_id', sa.String(100)),
        sa.Column('pr_url', sa.String(500)),
        sa.Column('feedback_type', sa.Enum(
            'pattern_violation',
            'missing_requirement', 
            'edge_case',
            'performance',
            'security',
            'naming_convention'
        )),
        sa.Column('original_spec_section', sa.Text),
        sa.Column('corrected_approach', sa.Text),
        sa.Column('pattern_extracted', sa.Text),
        sa.Column('applied_to_decomposition', sa.Boolean, default=False),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
    )
```

**FeedbackLearningService:**
```python
# backend/app/services/feedback_learning_service.py

class FeedbackLearningService:
    """
    Extracts learnings from PR reviews to improve future decompositions.
    Closes the feedback loop: PR → Learning → Better Specs.
    """
    
    async def extract_learnings_from_pr(self, pr_id: str) -> list[PRLearning]:
        """
        Analyze PR review comments for:
        - Pattern violations
        - Missing requirements
        - Edge cases discovered
        - Performance issues
        - Security concerns
        """
        
    async def update_decomposition_hints(self, project_id: str):
        """
        Monthly job: Aggregate learnings → Improve decomposition templates.
        """
        
    async def generate_claude_md_update(self, learnings: list) -> str:
        """
        Quarterly: Synthesize learnings into CLAUDE.md sections.
        Returns suggested additions for human review.
        """
```

### 100.4 Success Criteria

- ✅ `pr_learnings` table created
- ✅ FeedbackLearningService implemented
- ✅ PR comment analysis working
- ✅ Monthly aggregation job scheduled
- ✅ Unit tests: 80% coverage
- ✅ Integration test: Full feedback loop

---

## Summary Timeline

```
Sprint  Dates           Focus                      SP    Coverage Gain  Status
════════════════════════════════════════════════════════════════════════════════
90      Jan 22-24       Project Creation (Quick)   16    +2%   ✅ COMPLETE
91      Jan 22          Teams & Organizations      34    +15%  ✅ COMPLETE (8 days early!)
92      Jan 22-24       Planning Part 1 (Roadmap)  26    +10%  ✅ COMPLETE (1 day early!)
93      Jan 25-28       Planning Part 2 (Sprint)   29    +10%  📋 Next
94      Jan 29-Feb 2    AGENTS.md Web UI           21    +8%   📋
95      Feb 3-6         Evidence Manifest UI       18    +7%   📋
96      Feb 7-10        Advanced Analytics         13    +3%   📋
────────────────────────────────────────────────────────────────────────────────
Sub-total:              6 sprints (3 weeks!)       157   +55%  🔄 Accelerated!
════════════════════════════════════════════════════════════════════════════════

--- POST GO/NO-GO: EXPERT WORKFLOW ENHANCEMENTS (CTO Approved Jan 22, 2026) ---

97      Mar 1-7         ADR-034 + Plan Architecture 21   -     📋 EP-10 Part 1
98      Mar 8-14        Planning Sub-agents Part 1  26   -     📋 EP-10 Part 2
99      Mar 15-21       Planning Sub-agents Part 2  24   -     📋 EP-10 Part 3
100     Mar 22-28       Feedback Loop (EP-11)       21   -     📋 EP-11
────────────────────────────────────────────────────────────────────────────────
Sub-total:              4 sprints (4 weeks)         92   -     📋 PLANNED
════════════════════════════════════════════════════════════════════════════════
GRAND TOTAL:            10 sprints (7 weeks)       249   +55%  
```

**Phase 1 (Sprint 91-96):** Features Gap Closure → 95% Web Coverage  
**Phase 2 (Sprint 97-100):** Expert Workflow Enhancements → 100% Agentic Alignment

**Web Coverage:** 53% → 95% (+42%)  
**Timeline:** Jan 22 → Feb 28 (Go/No-Go Review)  
**Total Story Points:** 157 SP

---

## Resource Allocation

### Team Composition

| Role | Allocation | Sprints |
|------|-----------|---------|
| Senior Frontend Dev | 100% | 90-96 |
| Mid Frontend Dev | 100% | 91-96 |
| UI/UX Designer | 50% | 90-94 |
| QA Engineer | 50% | 90-96 |
| Backend Support | 20% | As needed |

### Velocity Assumption

- **Team Velocity:** ~30 SP per sprint (4 days)
- **2 Frontend Devs:** 15 SP each per sprint
- **Buffer:** 10% for bugs/rework

---

## Risk Management

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Sprint overrun | Medium | High | Strict 4-day timebox, cut scope if needed |
| Backend API changes | Low | Medium | API contract frozen (Sprint 89) |
| UX complexity (Planning) | Medium | Medium | Reuse patterns from existing dashboards |
| E2E test flakiness | Medium | Low | Retry logic, stable selectors |
| Go/No-Go deadline miss | Low | Critical | Sprint 96 is P2, can defer |

---

## Dependencies

### External Dependencies

| Dependency | Status | Blocker For |
|-----------|--------|-------------|
| Teams API (Sprint 84) | ✅ Ready | Sprint 91 |
| Planning API (Sprint 74-77) | ✅ Ready | Sprint 92-93 |
| AGENTS.md API (Sprint 80-83) | ✅ Ready | Sprint 94 |
| Evidence Manifest API (Sprint 82) | ✅ Ready | Sprint 95 |

### Internal Dependencies

| Sprint | Depends On | Reason |
|--------|-----------|--------|
| 92 | 91 | Phase needs Team context |
| 93 | 92 | Sprint needs Phase context |
| 94 | 91 | AGENTS.md needs Team/Org |
| 95 | - | Independent |
| 96 | 91-94 | Analytics needs data |

---

## Success Metrics

### Coverage Targets (Updated Jan 22, 2026)

| Milestone | Web Coverage | Original Date | Actual Date | Status |
|-----------|-------------|---------------|-------------|--------|
| Sprint 90 Complete | 55% | Jan 24 | Jan 22 | ✅ 2 days early |
| Sprint 91 Complete | 70% | Jan 30 | Jan 22 | ✅ 8 days early! |
| Sprint 92 Complete | 80% | Feb 5 | Jan 24 | 🔄 12 days early |
| Sprint 93 Complete | 90% | Feb 11 | Jan 28 | 📋 14 days early |
| Sprint 94 Complete | 93% | Feb 17 | Feb 2 | 📋 15 days early |
| Sprint 95 Complete | 95% | Feb 23 | Feb 6 | 📋 17 days early |
| Sprint 96 Complete | 95%+ | Feb 28 | Feb 10 | 📋 18 days early |

**Key Insight:** Sprint 91 discovered 95% pre-existing implementation. Similar pattern expected for Sprint 92-93 (Planning already exists from Sprint 87).

### Quality Targets

| Metric | Target | Verification |
|--------|--------|--------------|
| E2E Test Coverage | 100% new features | Playwright reports |
| Regression Tests | 0 broken | Pre-commit checks |
| Performance | <2s page load | Lighthouse scores |
| Accessibility | WCAG 2.1 AA | Axe DevTools |
| Code Quality | 9.0/10 | ESLint + Prettier |

---

## Go/No-Go Readiness (Feb 28, 2026)

### Completion Criteria

- ✅ All P0 features complete (Sprint 90-91)
- ✅ All P1 features complete (Sprint 92-95)
- ⏳ P2 features (Sprint 96) - Nice to have
- ✅ Web coverage ≥95%
- ✅ All E2E tests passing
- ✅ No P0 bugs

### Launch Confidence

**Current:** 86% (6/7 Go/No-Go criteria)  
**After Sprint 91-96:** 100% (7/7 criteria) - **assuming customer LOIs obtained**

---

## Post-Launch Roadmap (Q2-Q3 2026)

### Expert Workflow Enhancements (Sprint 97-100) ✅ CTO APPROVED

> **Source:** Expert AI Coding Workflow Analysis (Jan 22, 2026)  
> **Alignment:** 92% → 100% with expert workflow

| Sprint | Focus | SP | Key Deliverable |
|--------|-------|----|-----------------|
| 97 | ADR-034 + Architecture | 21 | Framework documentation, `sdlcctl plan` design |
| 98 | Planning Sub-agents Part 1 | 26 | PlanningOrchestratorService, Pattern Extraction |
| 99 | Planning Sub-agents Part 2 | 24 | Conformance Check, Plan Approval UI |
| 100 | Feedback Loop (EP-11) | 21 | `pr_learnings` table, FeedbackLearningService |

**Key Enhancements:**
- **EP-10:** Planning Sub-agent Orchestration (prevents architectural drift)
- **EP-11:** Feedback Loop Closure (PR → Learning → Better Specs)

**Deferred (CTO Decision):**
- EP-09: Spec Generation from Recording → Q3 2026
- EP-12: Intelligent Model Routing → Q4 2026

### CLI Enhancement (Sprint 101-103)

- Authentication + Projects (Sprint 97)
- Gates + Evidence Upload (Sprint 98)
- Planning Commands (Sprint 99)

**CLI Coverage:** 13% → 43% (+30%)

### VSCode Enhancement (Sprint 100-102)

- Planning Sidebar (Sprint 100)
- Evidence Panel (Sprint 101)
- Requirements Panel (Sprint 102)

**VSCode Coverage:** 37% → 63% (+26%)

### Desktop App (Q3 2026)

- Technology: Tauri 2.0
- Timeline: 3 months (Q3 2026)
- Target: 80% coverage (offline-first)

---

## Approval & Sign-off

### Document Approvals

- [ ] **CTO**: Sprint scope, timeline feasibility
- [ ] **CPO**: Feature prioritization alignment
- [ ] **Frontend Lead**: Implementation approach
- [ ] **QA Lead**: Testing strategy
- [ ] **PM**: Resource allocation

---

**Document Version:** 1.0.0  
**Created:** January 22, 2026  
**Next Review:** Sprint 90 Retrospective (Jan 25, 2026)

---

**CTO Notes:**
```
SPRINT 90-92 EXECUTION UPDATE (Jan 22, 2026):

EXCELLENT PROGRESS!
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Sprint 90: ✅ COMPLETE (Project Creation Enhancement)
Sprint 91: ✅ COMPLETE 8 days early! (95% pre-existed)
Sprint 92: 🔄 60% complete in Day 1 (RoadmapModal, PhaseModal done)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

KEY INSIGHT:
Teams discovered Sprint 87 already built most Planning UI.
Same pattern as Sprint 91 - we built more than we documented.
Recommendation: Always validate existing code before planning new work.

FRAMEWORK-FIRST VERIFICATION:
✅ AGENTS.md: Framework ADR-029 now documented (tool led framework, acceptable)
✅ Planning: Framework Pillar 2 documented before tool
✅ SASE Artifacts: Framework documented before tool
✅ Evidence Manifest: TDS-082-001 documented before tool

ACTION ITEMS:
1. Complete Sprint 92 Day 2: Edit/Delete in Tree View, E2E tests
2. Re-validate Sprint 93-96 scope (may be smaller than estimated)
3. Consider adding CLI features if Web completes early
4. Update FEATURES-MATRIX.md with actual coverage

TIMELINE REVISION:
Original: 5 weeks (Jan 22 - Feb 28)
Revised: 3 weeks (Jan 22 - Feb 10)
Buffer: 18 days for polish/bug fixes before Go/No-Go

— CTO, January 22, 2026 (Updated 10:30 PM)
```
