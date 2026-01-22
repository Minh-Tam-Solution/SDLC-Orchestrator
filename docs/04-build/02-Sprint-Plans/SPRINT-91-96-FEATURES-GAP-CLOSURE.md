# Sprint 91-96: Features Matrix Gap Closure Plan

**Planning Date:** January 22, 2026  
**Status:** 📋 PLANNED  
**Framework:** SDLC 5.1.3 (7-Pillar Architecture)  
**CTO Approval:** Pending

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

## Priority Matrix

### P0 - Launch Blockers (Must Have for Soft Launch)
- Teams & Organizations UI (Sprint 91)
- Team Member Management (Sprint 91)
- GitHub Integration Enhancement (Sprint 90 - In Progress)

### P1 - Core Features (Needed for MVP)
- Planning Hierarchy UI (Sprint 92-93)
- AGENTS.md Web UI (Sprint 94)
- Evidence Manifest UI (Sprint 95)

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

Close critical gap in Teams & Organizations management - currently **0% implementation** despite backend being production-ready (Sprint 84).

### 91.2 Features

| Feature | Priority | SP | Status |
|---------|----------|----|----|
| Create Team | P0 | 5 | 📋 |
| List Teams | P0 | 3 | 📋 |
| Update Team | P0 | 3 | 📋 |
| Delete Team | P0 | 3 | 📋 |
| Add Team Member | P0 | 5 | 📋 |
| Remove Team Member | P0 | 3 | 📋 |
| Update Member Role | P0 | 5 | 📋 |
| Team Statistics | P1 | 3 | 📋 |
| Team Switcher | P1 | 2 | 📋 |
| Create Organization | P0 | 2 | 📋 |

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

## Sprint 92: Planning Hierarchy Part 1 (Jan 31 - Feb 5, 2026)

**Duration:** 4 days  
**Priority:** P1 - Core Feature  
**Story Points:** 26 SP

### 92.1 Objectives

Implement Roadmap and Phase management - first half of Planning Hierarchy (Sprint 74-77 scope).

### 92.2 Features

| Feature | Priority | SP | Status |
|---------|----------|----|----|
| View Roadmap | P1 | 5 | 📋 |
| Create/Edit Roadmap | P1 | 5 | 📋 |
| View Phases | P1 | 3 | 📋 |
| Create/Edit Phase | P1 | 5 | 📋 |
| Roadmap Timeline View | P1 | 5 | 📋 |
| Phase Gantt Chart | P2 | 3 | 📋 |

### 92.3 Implementation Plan

#### Day 1-2: Roadmap CRUD (16h)

**Files:**
- `frontend/src/app/app/planning/roadmap/page.tsx`
- `frontend/src/app/app/planning/roadmap/[id]/page.tsx`
- `frontend/src/components/planning/RoadmapTimeline.tsx`
- `frontend/src/hooks/usePlanning.ts`

**UI:**
```typescript
// Roadmap List View
- Timeline view (12 months)
- Card view
- Create roadmap button

// Roadmap Detail View
- Roadmap info (title, description, dates)
- Phases list (visual timeline)
- Add phase button
- Edit roadmap button

// Create/Edit Roadmap Form
- Title (required)
- Description (markdown)
- Start date
- End date (max 12 months)
- Project selector
```

#### Day 3-4: Phase Management (16h)

**Features:**
```typescript
// Phase CRUD
- Create phase within roadmap
- Edit phase details
- Delete phase (cascade to sprints?)
- Reorder phases (drag & drop)

// Phase Detail View
- Phase info
- Sprints list
- Progress indicator
- Add sprint button

// Phase Timeline (Gantt)
- Visual timeline of all phases
- Dependency arrows (optional)
- Milestone markers
```

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

### 92.5 Success Criteria

- ✅ Roadmap CRUD functional
- ✅ Phase CRUD functional
- ✅ Timeline visualization working
- ✅ Roadmap-Phase hierarchy enforced
- ✅ E2E tests: 6 scenarios

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

## Summary Timeline

```
Sprint  Dates           Focus                      SP    Coverage Gain
══════════════════════════════════════════════════════════════════════
90      Jan 22-24       Project Creation (Quick)   16    +2%   ✅ IN PROGRESS
91      Jan 25-30       Teams & Organizations      34    +15%  📋 Next
92      Jan 31-Feb 5    Planning Part 1 (Roadmap)  26    +10%  📋
93      Feb 6-11        Planning Part 2 (Sprint)   29    +10%  📋
94      Feb 12-17       AGENTS.md Web UI           21    +8%   📋
95      Feb 18-23       Evidence Manifest UI       18    +7%   📋
96      Feb 24-28       Advanced Analytics         13    +3%   📋
──────────────────────────────────────────────────────────────────────
Total:                  6 sprints (5 weeks)        157   +55%  📋
```

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

### Coverage Targets

| Milestone | Web Coverage | Date |
|-----------|-------------|------|
| Sprint 90 Complete | 55% | Jan 24 |
| Sprint 91 Complete | 70% | Jan 30 |
| Sprint 92 Complete | 80% | Feb 5 |
| Sprint 93 Complete | 90% | Feb 11 |
| Sprint 94 Complete | 93% | Feb 17 |
| Sprint 95 Complete | 95% | Feb 23 |
| Sprint 96 Complete | 95%+ | Feb 28 |

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

## Post-Launch Roadmap (Q2 2026)

### CLI Enhancement (Sprint 97-99)

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
Sprint 90-96 plan achieves 95% Web coverage by Go/No-Go deadline.
Prioritization aligns with launch readiness (P0 > P1 > P2).
Timeline is aggressive but achievable with 2 frontend devs.
CLI/VSCode enhancements deferred to post-launch (correct decision).

Approved for planning. Execute Sprint 90 first, validate velocity,
then commit to Sprint 91-96 based on actual delivery rate.

— CTO, January 22, 2026
```
