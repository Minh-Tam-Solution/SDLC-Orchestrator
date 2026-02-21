# Sprint 175: "Frontend Feature Completion" — 6 Hidden Pages Integration

**Sprint Duration**: March 3-14, 2026 (10 working days)
**Status**: PLANNED
**Phase**: Stage 04 (BUILD) — Frontend Feature Completion
**Framework**: SDLC 6.1.0
**Priority**: P1 (User-Facing Feature Gaps)
**Previous Sprint**: [Sprint 174 COMPLETE — Anthropic Best Practices](SPRINT-174-COMPLETION-REPORT.md)

---

## Sprint Goal

Complete 6 production-ready frontend pages that are fully implemented but **hidden from sidebar navigation**, preventing users from accessing CEO Dashboard, Planning Hierarchy, MCP Analytics, Learnings, Plan Review, and SASE Templates features. This sprint adds sidebar entries, connects remaining unused hooks to UI, and polishes each page for production readiness.

---

## Sprint Context

**Sprint 174 Frontend Audit** (Feb 2026) identified:
- 85 total `page.tsx` files in the frontend
- 3 dogfooding/duplicate pages moved to `99-Legacy/` (2,032 LOC archived)
- **6 production pages kept but hidden** — fully coded, hooks exist, backend APIs ready, but NOT accessible via sidebar navigation

**Key Finding**: All 6 pages are crash-safe (no missing imports/components). The work is primarily:
1. **Sidebar integration** — Add 5 pages to navigation (sase-templates already listed)
2. **Hook wiring** — Connect unused TanStack Query hooks to UI components
3. **Hardcoded data replacement** — Replace static mock data with real API calls
4. **Missing sub-pages** — Build detail/sub-navigation pages
5. **Export & actions** — Add CSV export, bulk actions, drill-down navigation

---

## Success Criteria

- [ ] All 6 pages accessible from sidebar navigation
- [ ] All custom hooks connected to UI (no unused hook imports)
- [ ] Zero hardcoded/mock data in any of the 6 pages
- [ ] CEO Dashboard shows real-time data with drill-down capability
- [ ] Planning page supports full CRUD (create/edit/delete roadmaps, phases, sprints)
- [ ] MCP Analytics displays real cost metrics from backend
- [ ] Learnings page uses all 20 hooks from `useLearnings.ts`
- [ ] Plan Review detail page (`/app/plan-review/[id]`) fully functional
- [ ] All 6 pages pass TypeScript strict mode (`npx tsc --noEmit`)
- [ ] All 6 pages render correctly on viewport 1280px+ (responsive not required this sprint)

---

## Key Metrics

| Metric | Target | How to Check |
|--------|--------|--------------|
| Pages in sidebar | 6/6 | Visual check — all visible in navigation |
| Hooks utilization | >90% | Grep unused imports per page |
| Hardcoded data | 0 instances | Search for static arrays/objects in pages |
| TypeScript errors | 0 | `cd frontend && npx tsc --noEmit` |
| Build success | PASS | `cd frontend && npm run build` |
| Page load time | <2s each | Chrome DevTools Network tab |

---

## Scope

### In Scope

| # | Deliverable | Pages | Priority |
|---|-------------|-------|----------|
| 1 | Sidebar navigation entries (5 new) | All except sase-templates | P0 |
| 2 | CEO Dashboard — full hook wiring + drill-down | ceo-dashboard | P0 |
| 3 | MCP Analytics — real cost data + time-range selector | mcp-analytics | P1 |
| 4 | Planning — full CRUD modals + hierarchy tree | planning | P1 |
| 5 | Plan Review — detail page + status transitions | plan-review | P1 |
| 6 | Learnings — connect 20 hooks + sub-pages | learnings | P1 |
| 7 | SASE Templates — backend API integration | sase-templates | P2 |

### Out of Scope (Deferred to Sprint 176+)

| Item | Reason |
|------|--------|
| Mobile responsive design for 6 pages | Desktop-first priority |
| SASE Templates backend API creation | Requires backend sprint (8+ days alone) |
| Drag-and-drop sprint reordering | Nice-to-have, not MVP |
| Real-time WebSocket updates for CEO Dashboard | Polling sufficient for MVP |
| E2E Playwright tests for 6 pages | Unit tests first |

---

## Page Analysis Summary

| Page | LOC | Hooks Available | Hooks Used | Backend APIs | Sidebar |
|------|-----|-----------------|------------|--------------|---------|
| **sase-templates** | 841 | 0 | 0 | 0 endpoints | YES |
| **mcp-analytics** | 557 | 6 (useMCPAnalytics) | 3/6 | 5 endpoints | NO |
| **learnings** | 627 | 20 (useLearnings) | 4/20 | 8+ endpoints | NO |
| **plan-review** | 542+625 | 8 (usePlanningReview) | 2/8 | 6+ endpoints | NO |
| **ceo-dashboard** | 763 | 13 (useCEODashboard) | 5/13 | 11+ endpoints | NO |
| **planning** | 553 | 28 (usePlanningHierarchy) | 4/28 | 12+ endpoints | NO |

---

## Sprint Backlog — Daily Breakdown

### Day 1: Sidebar Integration + Quick Wins

**Owner**: Frontend Engineer
**Priority**: P0

#### Task 1.1: Add 5 Missing Pages to Sidebar Navigation (2h)

**File**: `frontend/src/components/dashboard/Sidebar.tsx`

Add navigation entries after the existing items, grouped under a new "Analytics & Planning" section:

```typescript
// Sprint 175: Analytics & Planning
{
  name: "CEO Dashboard",
  href: "/app/ceo-dashboard",
  icon: ChartBarIcon,      // executive metrics
},
{
  name: "Planning",
  href: "/app/planning",
  icon: CalendarDaysIcon,   // roadmap/phase/sprint
},
{
  name: "Plan Review",
  href: "/app/plan-review",
  icon: ClipboardDocumentCheckIcon,
},
{
  name: "MCP Analytics",
  href: "/app/mcp-analytics",
  icon: CpuChipIcon,       // AI provider metrics
},
{
  name: "Learnings",
  href: "/app/learnings",
  icon: AcademicCapIcon,   // PR learnings
},
```

**Acceptance Criteria**:
- [ ] All 6 pages visible in sidebar
- [ ] Active page highlighted correctly
- [ ] Icons render without errors
- [ ] Navigation works on click

#### Task 1.2: Update Sidebar Footer Version (30min)

Update footer from "Sprint 153" to "Sprint 175" and version from "v1.0" to current.

#### Task 1.3: MCP Analytics — Connect Remaining Hooks (4h)

**File**: `frontend/src/app/app/mcp-analytics/page.tsx`

**Current state**: Uses `useMCPDashboard`, `useMCPProviderHealth`, `useMCPLatencyMetrics` (3/6 hooks)

**Missing hooks to connect**:
- `useMCPCostBreakdown` — Replace hardcoded cost data with real API data
- `useMCPToolUsage` — Add tool usage statistics section
- `useMCPErrorRates` — Add error rate visualization

**Acceptance Criteria**:
- [ ] Cost breakdown section shows real data from backend
- [ ] Tool usage table populated from API
- [ ] Error rates chart connected to real metrics
- [ ] Loading skeletons shown during data fetch
- [ ] Error states handled gracefully

---

### Day 2: MCP Analytics Completion + CEO Dashboard Start

**Owner**: Frontend Engineer
**Priority**: P0/P1

#### Task 2.1: MCP Analytics — Time Range Selector (3h)

Add time range filter (24h / 7d / 30d / 90d) to MCP Analytics page. Pass `timeRange` param to all hooks.

**Acceptance Criteria**:
- [ ] Time range selector in page header
- [ ] All charts/tables respect selected range
- [ ] Default to "7d"
- [ ] URL query param sync (`?range=7d`)

#### Task 2.2: CEO Dashboard — Wire Remaining 8 Hooks (4h)

**File**: `frontend/src/app/app/ceo-dashboard/page.tsx`

**Current state**: Uses 5/13 hooks (`useCEODashboardSummary`, `useCEOPendingDecisions`, `useCEOTimeSavedTrend`, `useCEOSystemHealth`, `useResolveCEODecision`)

**Missing hooks to connect**:
- `useCEOProjectScores` — Project compliance scorecard
- `useCEOGateProgress` — Gate pipeline visualization
- `useCEOTeamPerformance` — Team velocity/quality metrics
- `useCEOCostAnalysis` — AI cost analysis (real data)
- `useCEOVibeCodingIndex` — Vibecoding index display
- `useCEOKillSwitchStatus` — Kill switch monitoring
- `useCEOComplianceTrend` — Compliance trend chart
- `useUpdateKillSwitch` — Kill switch toggle mutation

**Acceptance Criteria**:
- [ ] All 13 hooks imported and used
- [ ] Kill switch section with real status + toggle
- [ ] Vibecoding index with color-coded status (Green/Yellow/Orange/Red)
- [ ] Compliance trend line chart

---

### Day 3: CEO Dashboard Completion

**Owner**: Frontend Engineer
**Priority**: P0

#### Task 3.1: CEO Dashboard — Drill-Down Navigation (3h)

Add clickable sections that link to detail pages:
- Project scores → Link to `/app/projects/{id}`
- Gate progress → Link to `/app/gates/{id}`
- Pending decisions → Inline resolve action (already has `useResolveCEODecision`)

#### Task 3.2: CEO Dashboard — Export Functionality (2h)

Add "Export Report" button that generates CSV/JSON of dashboard data:
- Summary metrics as CSV
- Pending decisions as JSON

#### Task 3.3: CEO Dashboard — Auto-Refresh (1h)

Add 30-second auto-refresh using TanStack Query `refetchInterval`:
```typescript
const { data } = useCEODashboardSummary({
  refetchInterval: 30_000, // 30s auto-refresh
});
```

**Day 3 Acceptance Criteria**:
- [ ] CEO Dashboard is fully functional with all 13 hooks
- [ ] Drill-down links navigate to correct detail pages
- [ ] Export generates downloadable file
- [ ] Auto-refresh visible with "Last updated" timestamp

---

### Day 4: Learnings Page — Hook Wiring

**Owner**: Frontend Engineer
**Priority**: P1

#### Task 4.1: Learnings — Connect All 20 Hooks (5h)

**File**: `frontend/src/app/app/learnings/page.tsx`

**Current state**: Uses 4/20 hooks (`useLearnings`, `useLearningStats`, `useDeleteLearning`, `useApplyLearning`)

**Hook groups to connect**:

**Learning CRUD** (4 hooks):
- `useCreateLearning` — "Add Learning" form/modal
- `useUpdateLearning` — Edit learning inline
- `useLearningDetail` — Learning detail view
- `useBulkApplyLearnings` — Bulk apply action

**Hints** (5 hooks):
- `useHints`, `useCreateHint`, `useUpdateHint`, `useDeleteHint`, `useHintDetail`
- Add "Hints" tab to learnings page

**Aggregations** (4 hooks):
- `useLearningAggregations`, `useCreateAggregation`, `useRunAggregation`, `useAggregationDetail`
- Add "Aggregations" tab

**Categories & Filters** (3 hooks):
- `useLearningCategories`, `useLearningTrends`, `useLearningExport`

**Acceptance Criteria**:
- [ ] "Add Learning" button opens creation modal
- [ ] Edit/Delete actions work inline
- [ ] Hints tab shows hint list with CRUD
- [ ] Aggregations tab shows aggregation list
- [ ] Category filter dropdown populated from API
- [ ] Trend chart shows learning creation over time

---

### Day 5: Learnings Sub-Pages + Plan Review Start

**Owner**: Frontend Engineer
**Priority**: P1

#### Task 5.1: Learnings — Export & Trends (2h)

- Wire `useLearningExport` to "Export" button (CSV download)
- Wire `useLearningTrends` to trend visualization chart
- Add deduplication status indicator

#### Task 5.2: Plan Review — List Page Enhancement (4h)

**File**: `frontend/src/app/app/plan-review/page.tsx`

**Current state**: Uses `usePlanningSessions`, `useCreatePlanningSession` (2/8 hooks)

**Missing hooks to connect**:
- `usePlanningSession` — Individual session detail
- `useUpdatePlanningSession` — Edit session
- `useDeletePlanningSession` — Delete session
- `usePlanningSessionTasks` — Tasks within session
- `useApprovePlanningSession` — Approve action
- `useRejectPlanningSession` — Reject action

**Acceptance Criteria**:
- [ ] Session list shows status badges (DRAFT, IN_REVIEW, APPROVED, REJECTED)
- [ ] "Create Session" form uses real API
- [ ] Delete action with confirmation dialog
- [ ] Status filter (All / Draft / In Review / Approved / Rejected)

---

### Day 6: Plan Review Detail Page

**Owner**: Frontend Engineer
**Priority**: P1

#### Task 6.1: Plan Review Detail — Full Implementation (6h)

**File**: `frontend/src/app/app/plan-review/[id]/page.tsx`

Connect remaining hooks for the detail page:
- `usePlanningSession` — Load session details
- `usePlanningSessionTasks` — Display task breakdown
- `useApprovePlanningSession` / `useRejectPlanningSession` — Action buttons
- `useUpdatePlanningSession` — Edit capability

Add sections:
1. **Session Header**: Title, status badge, created date, conformance score
2. **Task Breakdown**: Table of tasks with status, assignee, estimates
3. **Action Bar**: Approve / Reject / Edit buttons based on session status
4. **History**: Session state transitions timeline

**Acceptance Criteria**:
- [ ] Detail page loads session data from API
- [ ] Task list renders with correct columns
- [ ] Approve/Reject buttons trigger API calls with optimistic updates
- [ ] Back navigation to list page works
- [ ] 404 handling for invalid session ID

---

### Day 7: Planning Page — CRUD Completion

**Owner**: Frontend Engineer
**Priority**: P1

#### Task 7.1: Planning — Wire Remaining Hierarchy Hooks (6h)

**File**: `frontend/src/app/app/planning/page.tsx`

**Current state**: Uses `usePlanningHierarchy`, `useSprints`, `useDeleteRoadmap`, `useDeletePhase` (4/28 hooks)

**Missing hook groups to connect**:

**Roadmap CRUD** (5 hooks):
- `useCreateRoadmap` — Create roadmap modal
- `useUpdateRoadmap` — Edit roadmap
- `useRoadmapDetail` — Roadmap detail view
- `useRoadmapPhases` — Phases within roadmap
- `useRoadmapProgress` — Progress visualization

**Phase CRUD** (5 hooks):
- `useCreatePhase` — Create phase modal
- `useUpdatePhase` — Edit phase
- `usePhaseDetail` — Phase detail view
- `usePhaseSprints` — Sprints within phase
- `usePhaseProgress` — Phase progress bar

**Sprint CRUD** (5 hooks):
- `useCreateSprint` — Create sprint modal
- `useUpdateSprint` — Edit sprint
- `useDeleteSprint` — Delete sprint
- `useSprintDetail` — Sprint detail view
- `useSprintBacklog` — Backlog items

**Backlog** (5 hooks):
- `useBacklogItems`, `useCreateBacklogItem`, `useUpdateBacklogItem`, `useDeleteBacklogItem`, `useMoveBacklogItem`

**Planning Utilities** (4 hooks):
- `usePlanningStats`, `usePlanningTimeline`, `usePlanningDependencies`, `usePlanningExport`

**Acceptance Criteria**:
- [ ] Create/Edit/Delete work for Roadmaps, Phases, Sprints
- [ ] Hierarchy tree view shows Roadmap → Phase → Sprint → Backlog
- [ ] Progress bars show completion percentages
- [ ] Clicking a roadmap expands to show phases

---

### Day 8: Planning Detail Views + Backlog

**Owner**: Frontend Engineer
**Priority**: P1

#### Task 8.1: Planning — Detail Drill-Down (3h)

Add navigation from hierarchy tree to detail views:
- Click roadmap name → show roadmap detail with phases
- Click phase name → show phase detail with sprints
- Click sprint name → show sprint detail with backlog

#### Task 8.2: Planning — Backlog Management (3h)

Wire backlog hooks to the sprint detail view:
- `useBacklogItems` — List backlog items
- `useCreateBacklogItem` — Add item form
- `useUpdateBacklogItem` — Edit inline
- `useDeleteBacklogItem` — Delete with confirmation
- `useMoveBacklogItem` — Move between sprints (dropdown)

**Acceptance Criteria**:
- [ ] Full CRUD for backlog items within sprint context
- [ ] Move item between sprints works
- [ ] Backlog count shown on sprint card

---

### Day 9: SASE Templates + Cross-Page Polish

**Owner**: Frontend Engineer
**Priority**: P2

#### Task 9.1: SASE Templates — UI Polish (3h)

**File**: `frontend/src/app/app/sase-templates/page.tsx`

Current state: 841 LOC, fully hardcoded templates (CRP, MRP, VCR, AGENTS.md).

Since backend API doesn't exist yet (deferred), polish the existing static UI:
- Add "Copy to Clipboard" for template content
- Add template preview modal with syntax highlighting
- Add "Download as Markdown" button
- Add category filter tabs

**Note**: Backend persistence deferred to Sprint 176.

#### Task 9.2: Cross-Page Polish (3h)

Review all 6 pages for:
- Consistent loading skeleton patterns
- Consistent error state handling (retry button)
- Empty state messages ("No learnings yet", "No roadmaps created")
- Breadcrumb navigation where applicable
- Page titles in browser tab

**Acceptance Criteria**:
- [ ] All 6 pages have loading skeletons
- [ ] All 6 pages have error states with retry
- [ ] All 6 pages have empty states
- [ ] Browser tab shows page-specific title

---

### Day 10: Testing + Final Verification

**Owner**: Frontend Engineer
**Priority**: P0

#### Task 10.1: TypeScript Strict Mode Verification (1h)

```bash
cd frontend && npx tsc --noEmit
```

Fix any type errors introduced during sprint.

#### Task 10.2: Build Verification (1h)

```bash
cd frontend && npm run build
```

Ensure production build succeeds with no warnings.

#### Task 10.3: Manual QA — All 6 Pages (3h)

Walk through each page end-to-end:

| Page | Test Scenario |
|------|--------------|
| CEO Dashboard | Load → View metrics → Resolve decision → Export |
| MCP Analytics | Load → Change time range → View cost breakdown |
| Planning | Create roadmap → Add phase → Add sprint → Add backlog item |
| Plan Review | Create session → View detail → Approve |
| Learnings | View list → Filter → Apply learning → Export |
| SASE Templates | View templates → Copy → Download |

#### Task 10.4: Sprint Documentation (1h)

- Update `CURRENT-SPRINT.md` with Sprint 175 completion
- Create `SPRINT-175-COMPLETION-REPORT.md` with results

**Acceptance Criteria**:
- [ ] `npx tsc --noEmit` passes with 0 errors
- [ ] `npm run build` passes
- [ ] All 6 pages render correctly in browser
- [ ] All CRUD operations work against backend API
- [ ] No console errors in browser DevTools

---

## File Changes Summary

| Day | Action | File |
|-----|--------|------|
| 1 | EDIT | `frontend/src/components/dashboard/Sidebar.tsx` — Add 5 nav items |
| 1-2 | EDIT | `frontend/src/app/app/mcp-analytics/page.tsx` — Wire 3 hooks + time range |
| 2-3 | EDIT | `frontend/src/app/app/ceo-dashboard/page.tsx` — Wire 8 hooks + export |
| 4-5 | EDIT | `frontend/src/app/app/learnings/page.tsx` — Wire 16 hooks + tabs |
| 5-6 | EDIT | `frontend/src/app/app/plan-review/page.tsx` — Wire 6 hooks |
| 6 | EDIT | `frontend/src/app/app/plan-review/[id]/page.tsx` — Full detail page |
| 7-8 | EDIT | `frontend/src/app/app/planning/page.tsx` — Wire 24 hooks |
| 9 | EDIT | `frontend/src/app/app/sase-templates/page.tsx` — UI polish |
| 10 | VERIFY | All files — TypeScript + build verification |

---

## Risk Register

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| Backend API not returning expected shape | HIGH | LOW | Hooks already tested; verify with `curl` on Day 1 |
| Too many hooks to wire in 10 days | MEDIUM | MEDIUM | Prioritize CEO Dashboard + MCP Analytics (P0); defer backlog hooks if needed |
| Sidebar grows too long (23+ items) | LOW | HIGH | Group items under collapsible sections |
| SASE Templates needs backend | MEDIUM | CERTAIN | Explicitly deferred to Sprint 176 |

---

## Dependencies

| Dependency | Owner | Status |
|------------|-------|--------|
| Backend APIs running (all endpoints) | Backend Team | READY |
| Frontend dev environment | Frontend Engineer | READY |
| TanStack Query hooks (all files) | Already created | READY |
| shadcn/ui component library | Already installed | READY |
| Backend SASE Templates API | Backend Team | NOT READY (Sprint 176) |

---

## Definition of Done

- [ ] All 6 pages visible in sidebar navigation
- [ ] CEO Dashboard: 13/13 hooks connected, drill-down works, export works
- [ ] MCP Analytics: 6/6 hooks connected, time range selector works
- [ ] Planning: Full Roadmap → Phase → Sprint → Backlog CRUD works
- [ ] Plan Review: List + detail page functional with approve/reject
- [ ] Learnings: 20/20 hooks connected with Hints and Aggregations tabs
- [ ] SASE Templates: Copy/download functionality added
- [ ] `npx tsc --noEmit` passes (0 errors)
- [ ] `npm run build` passes
- [ ] All pages have loading, error, and empty states
- [ ] No hardcoded mock data in any of the 6 pages

---

## Sprint Metrics

| Metric | Target |
|--------|--------|
| Pages completed | 6/6 |
| Hooks connected | >90% of available hooks |
| TypeScript errors | 0 |
| Build status | PASS |
| LOC changed | ~2,000-3,000 (edits, not new files) |
| Backend API coverage | 5/6 pages (SASE deferred) |

---

*Sprint 175 — "Frontend Feature Completion"*
*SDLC Orchestrator Team*
*March 3-14, 2026*
