# Full-Stack Frontend-Backend Gap Analysis

**Date:** January 20, 2026
**Sprint:** 83 Complete → Planning Sprint 84+
**Status:** CTO Review Required
**Author:** AI Assistant + PM Team

---

## Executive Summary

Phân tích toàn diện 3 frontend clients của SDLC Orchestrator:
1. **Web Dashboard** (Next.js)
2. **CLI Tool** (sdlcctl - Python/Typer)
3. **VSCode Extension** (TypeScript)

| Client | Backend Coverage | Critical Gaps | Priority |
|--------|-----------------|---------------|----------|
| **Web Dashboard** | 60% | Teams, Organizations, Planning, AGENTS.md | 🔴 P0 |
| **CLI (sdlcctl)** | 15% | Evidence, Projects, Gates, Planning | 🟡 P1 |
| **VSCode Extension** | 55% | Evidence, Planning, Requirements | 🟡 P1 |

**Total Backend Endpoints:** 297+
**Unique Features Requiring UI:** 45+

---

## 1. Backend API Inventory (297+ Endpoints)

### 1.1 API Categories Summary

| Category | Endpoints | Web | CLI | VSCode | Notes |
|----------|-----------|-----|-----|--------|-------|
| **Authentication** | 9 | ✅ 100% | ❌ 0% | ✅ 100% | CLI stateless |
| **Projects** | 5 | ✅ 100% | ❌ 0% | ✅ 100% | |
| **Teams** | 10 | ❌ 0% | ❌ 0% | ❌ 0% | Sprint 71 |
| **Organizations** | 5 | ❌ 0% | ❌ 0% | ❌ 0% | Sprint 71 |
| **Gates** | 6 | ✅ 100% | ❌ 0% | ✅ 100% | |
| **Evidence** | 6 | ✅ 100% | ❌ 0% | ❌ 0% | CLI/VSCode missing |
| **Evidence Manifest** | 4 | ❌ 0% | ❌ 0% | ❌ 0% | Sprint 82 |
| **Policies** | 5 | ✅ 100% | ❌ 0% | ❌ 0% | |
| **Policy Packs** | 3 | ✅ 100% | ❌ 0% | ❌ 0% | |
| **SAST** | 3 | ✅ 100% | ❌ 0% | ❌ 0% | |
| **Compliance** | 7 | ✅ 100% | ❌ 0% | ✅ 100% | |
| **Override/VCR** | 7 | ✅ 100% | ❌ 0% | ❌ 0% | |
| **Planning - Roadmap** | 5 | ❌ 0% | ❌ 0% | ❌ 0% | Sprint 74 |
| **Planning - Phase** | 5 | ❌ 0% | ❌ 0% | ❌ 0% | Sprint 74 |
| **Planning - Sprint** | 15 | ❌ 0% | ❌ 0% | ❌ 0% | Sprint 74-77 |
| **Planning - Backlog** | 8 | ❌ 0% | ❌ 0% | ❌ 0% | Sprint 74 |
| **AGENTS.md** | 7 | ❌ 0% | ✅ 57% | ❌ 0% | CLI has 4/7 |
| **Multi-Repo AGENTS.md** | 6 | ❌ 0% | ❌ 0% | ❌ 0% | Sprint 83 |
| **Analytics v2** | 4 | ⚠️ 25% | ❌ 0% | ❌ 0% | Partial |
| **Codegen** | 30 | ✅ 90% | ⚠️ 20% | ✅ 83% | |
| **AI Council** | 4 | ✅ 100% | ❌ 0% | ✅ 100% | |
| **AI Providers** | 5 | ✅ 100% | ❌ 0% | ❌ 0% | Admin only |
| **GitHub Integration** | 4 | ✅ 100% | ❌ 0% | ❌ 0% | |
| **Notifications** | 3 | ✅ 100% | ❌ 0% | ❌ 0% | |
| **Admin** | 10 | ✅ 100% | ❌ 0% | ❌ 0% | |
| **Payments** | 5 | ✅ 100% | ❌ 0% | ❌ 0% | |

---

## 2. Web Dashboard Gap Analysis

### 2.1 Current State

**Implemented:** 38+ pages, 18+ hooks
**Backend Coverage:** ~60%

### 2.2 Critical Gaps (P0)

| Feature | Backend Endpoints | Frontend | Gap Impact |
|---------|-------------------|----------|------------|
| **Teams Management** | 10 endpoints (Sprint 71) | 0 pages | Multi-tenant blocked |
| **Organizations** | 5 endpoints (Sprint 71) | 0 pages | Hierarchy blocked |
| **AGENTS.md** | 13 endpoints (Sprint 80+83) | 0 pages | TRUE MOAT invisible |
| **Planning Hierarchy** | 33 endpoints (Sprint 74-77) | 0 pages | Sprint Governance blocked |

### 2.3 Moderate Gaps (P1)

| Feature | Backend Endpoints | Frontend | Gap Impact |
|---------|-------------------|----------|------------|
| **Analytics Dashboard** | 4 endpoints | 1 partial | No metrics visibility |
| **Evidence Manifest** | 4 endpoints | 0 pages | Tamper-evident not visible |
| **Sprint Retrospective** | 6 endpoints | 0 pages | Retro workflow missing |

### 2.4 Files Needed

```
frontend/src/app/app/
├── teams/                    # P0 - Sprint 84
│   ├── page.tsx
│   └── [id]/page.tsx
├── organizations/            # P0 - Sprint 84
│   ├── page.tsx
│   └── [id]/page.tsx
├── agents-md/                # P0 - Sprint 85
│   ├── page.tsx
│   ├── generate/page.tsx
│   └── repos/page.tsx
├── planning/                 # P0 - Sprint 86-87
│   ├── page.tsx
│   ├── roadmaps/page.tsx
│   ├── phases/page.tsx
│   ├── sprints/page.tsx
│   ├── sprints/[id]/page.tsx
│   └── backlog/page.tsx
└── analytics/                # P1 - Sprint 88
    └── page.tsx

frontend/src/hooks/
├── useTeams.ts               # P0
├── useOrganizations.ts       # P0
├── useAgentsMd.ts            # P0
├── usePlanning.ts            # P0
└── useAnalyticsV2.ts         # P1
```

---

## 3. CLI (sdlcctl) Gap Analysis

### 3.1 Current State

**Implemented:** 14 commands
**Backend Coverage:** ~15%

### 3.2 Implemented Commands

| Command | Type | Backend API | Status |
|---------|------|-------------|--------|
| `validate` | Local | None | ✅ |
| `fix` | Local | None | ✅ |
| `init` | Local | None | ✅ |
| `report` | Local | None | ✅ |
| `migrate` | Local | None | ✅ |
| `generate` | API | `/codegen/generate/stream` | ✅ |
| `magic` | API | `/codegen/generate/stream` | ✅ |
| `agents init` | Local | None | ✅ |
| `agents validate` | Local | None | ✅ |
| `agents lint` | Local | None | ✅ |
| `agents context` | API | `/agents-md/context/{id}` | ✅ |
| `tiers` | Info | None | ✅ |
| `stages` | Info | None | ✅ |
| `p0` | Info | None | ✅ |

### 3.3 Critical Gaps (P0)

| Feature | Backend Endpoints | CLI Command | Priority |
|---------|-------------------|-------------|----------|
| **Authentication** | 5 endpoints | `sdlcctl login/logout` | P0 |
| **Evidence Upload** | 6 endpoints | `sdlcctl evidence upload/list/get` | P0 |
| **Gate Evaluation** | 6 endpoints | `sdlcctl gates evaluate/status` | P0 |
| **Project Management** | 5 endpoints | `sdlcctl projects list/create/get` | P1 |

### 3.4 Moderate Gaps (P1)

| Feature | Backend Endpoints | CLI Command | Priority |
|---------|-------------------|-------------|----------|
| **Codegen Status** | 5 endpoints | `sdlcctl codegen status/resume` | P1 |
| **Compliance Scan** | 7 endpoints | `sdlcctl compliance scan/status` | P1 |
| **Planning** | 33 endpoints | `sdlcctl sprint list/create` | P2 |

### 3.5 Commands Needed

```bash
# P0 - Sprint 85
sdlcctl login                    # OAuth/API key login
sdlcctl logout                   # Clear credentials
sdlcctl evidence upload <file> --project <id> --stage <stage>
sdlcctl evidence list --project <id>
sdlcctl evidence get <id>
sdlcctl gates evaluate --project <id> --gate <code>
sdlcctl gates status --project <id>

# P1 - Sprint 86
sdlcctl projects list
sdlcctl projects create --name <name> --tier <tier>
sdlcctl projects get <id>
sdlcctl codegen status <session_id>
sdlcctl codegen resume <session_id>
sdlcctl compliance scan --project <id>
sdlcctl compliance status --project <id>

# P2 - Sprint 87+
sdlcctl sprints list --project <id>
sdlcctl sprints create --project <id> --name <name>
sdlcctl backlog list --sprint <id>
sdlcctl backlog create --sprint <id> --title <title>
```

---

## 4. VSCode Extension Gap Analysis

### 4.1 Current State

**Implemented:** 27 commands, 10 features
**Backend Coverage:** ~55%

### 4.2 Implemented Features

| Feature | Commands | Backend APIs | Status |
|---------|----------|--------------|--------|
| Gate Status Sidebar | 3 | `/projects/{id}/gates` | ✅ GA |
| Violations Panel | 3 | `/projects/{id}/violations` | ✅ GA |
| Projects Panel | 2 | `/projects` | ✅ GA |
| AI Chat (@gate) | 4 | `/ai/recommend`, `/ai/council` | ✅ GA |
| Context Panel | 3 | `/projects/{id}/context-overlay` | ✅ GA |
| App Builder | 4 | `/codegen/templates` | ✅ GA |
| Code Generation | 5 | `/codegen/generate` (SSE) | ✅ GA |
| Magic Mode | 1 | `/codegen/magic` | ✅ GA |
| Contract Lock | 4 | `/codegen/lock/*` | ✅ GA |
| Preview/Resume | 2 | `/codegen/{id}/status` | ✅ GA |

### 4.3 Critical Gaps (P0)

| Feature | Backend Endpoints | VSCode Feature | Priority |
|---------|-------------------|----------------|----------|
| **Evidence Upload** | 6 endpoints | Evidence Panel + Upload Command | P0 |
| **AGENTS.md View** | 13 endpoints | AGENTS.md Panel | P0 |

### 4.4 Moderate Gaps (P1)

| Feature | Backend Endpoints | VSCode Feature | Priority |
|---------|-------------------|----------------|----------|
| **Planning Sidebar** | 33 endpoints | Roadmap/Sprint View | P1 |
| **Requirements Panel** | 4 endpoints | Tier-classified Requirements | P1 |
| **AI Decomposition** | 4 endpoints | Decompose User Story Panel | P2 |

### 4.5 Features Needed

```typescript
// P0 - Sprint 85
// Evidence Panel
views/evidencePanel.ts           // Browse/filter evidence
commands/evidenceUpload.ts       // Upload from IDE
commands/evidenceView.ts         // View evidence details

// AGENTS.md Panel
views/agentsMdPanel.ts           // View/edit AGENTS.md
commands/agentsMdGenerate.ts     // Generate from IDE
commands/agentsMdValidate.ts     // Validate content

// P1 - Sprint 86-87
// Planning Sidebar
views/planningView.ts            // Roadmap/Phase/Sprint tree
views/backlogPanel.ts            // Backlog management
commands/sprintCreate.ts         // Create sprint

// Requirements Panel
views/requirementsPanel.ts       // Tier-filtered view
commands/requirementOverride.ts  // Override tier
```

---

## 5. Coverage Matrix (Visual)

```
Backend API Categories vs Frontend Clients:

                          Web    CLI    VSCode
                         ─────  ─────  ─────
Authentication            ██████  ░░░░░░  ██████
Projects                  ██████  ░░░░░░  ██████
Teams                     ░░░░░░  ░░░░░░  ░░░░░░  ← NEW (Sprint 71)
Organizations             ░░░░░░  ░░░░░░  ░░░░░░  ← NEW (Sprint 71)
Gates                     ██████  ░░░░░░  ██████
Evidence                  ██████  ░░░░░░  ░░░░░░  ← CLI/VSCode GAP
Evidence Manifest         ░░░░░░  ░░░░░░  ░░░░░░  ← NEW (Sprint 82)
Policies                  ██████  ░░░░░░  ░░░░░░
Compliance                ██████  ░░░░░░  ██████
Override/VCR              ██████  ░░░░░░  ░░░░░░
Planning Hierarchy        ░░░░░░  ░░░░░░  ░░░░░░  ← NEW (Sprint 74-77)
AGENTS.md                 ░░░░░░  ███░░░  ░░░░░░  ← TRUE MOAT
Multi-Repo AGENTS.md      ░░░░░░  ░░░░░░  ░░░░░░  ← NEW (Sprint 83)
Analytics v2              █░░░░░  ░░░░░░  ░░░░░░
Codegen                   █████░  ██░░░░  █████░
AI Council                ██████  ░░░░░░  ██████
GitHub Integration        ██████  ░░░░░░  ░░░░░░
Admin                     ██████  ░░░░░░  ░░░░░░
Payments                  ██████  ░░░░░░  ░░░░░░

Legend: ██████ = 100%  ███░░░ = 50%  █░░░░░ = 10%  ░░░░░░ = 0%
```

---

## 6. Priority Matrix

### 6.1 By Business Impact

| Priority | Feature | Clients Affected | Business Value |
|----------|---------|------------------|----------------|
| **P0** | Teams & Organizations | Web | Multi-tenant, Enterprise sales |
| **P0** | AGENTS.md UI | Web, VSCode | TRUE MOAT differentiator |
| **P0** | CLI Authentication | CLI | CI/CD integration |
| **P0** | Evidence Upload | CLI, VSCode | Developer workflow |
| **P1** | Planning Hierarchy | Web, VSCode | Sprint Governance (SDLC 5.1.3) |
| **P1** | Gate Evaluation CLI | CLI | CI/CD gate checks |
| **P1** | Analytics Dashboard | Web | Metrics visibility |
| **P2** | AI Decomposition | VSCode | Developer productivity |
| **P2** | Requirements Panel | VSCode | Context-aware dev |

### 6.2 By Sprint Timeline

| Sprint | Focus | Web | CLI | VSCode |
|--------|-------|-----|-----|--------|
| **84** | Teams & Orgs | ✅ Teams + Orgs UI | - | - |
| **85** | AGENTS.md + CLI Auth | ✅ AGENTS.md UI | ✅ Auth + Evidence | ✅ AGENTS.md Panel |
| **86** | Planning Part 1 | ✅ Roadmap + Phase | ✅ Gates + Projects | ✅ Evidence Panel |
| **87** | Planning Part 2 | ✅ Sprint + Backlog | ✅ Sprint commands | ✅ Planning View |
| **88** | Analytics + Polish | ✅ Analytics Dashboard | ✅ Compliance | ✅ Requirements |

---

## 7. Estimated Effort

### 7.1 Web Dashboard

| Feature | Pages | Hooks | Components | Story Points |
|---------|-------|-------|------------|--------------|
| Teams & Orgs | 4 | 2 | 10 | 34 SP |
| AGENTS.md | 3 | 1 | 8 | 21 SP |
| Planning Hierarchy | 6 | 1 | 15 | 55 SP |
| Analytics | 1 | 1 | 5 | 13 SP |
| **Total** | **14** | **5** | **38** | **123 SP** |

### 7.2 CLI (sdlcctl)

| Feature | Commands | Effort |
|---------|----------|--------|
| Authentication | 2 | 8 SP |
| Evidence | 3 | 13 SP |
| Gates | 2 | 8 SP |
| Projects | 3 | 8 SP |
| Codegen Status | 2 | 5 SP |
| Compliance | 2 | 5 SP |
| Planning | 4 | 13 SP |
| **Total** | **18** | **60 SP** |

### 7.3 VSCode Extension

| Feature | Views/Panels | Commands | Effort |
|---------|--------------|----------|--------|
| Evidence Panel | 1 | 3 | 13 SP |
| AGENTS.md Panel | 1 | 3 | 13 SP |
| Planning View | 2 | 4 | 21 SP |
| Requirements Panel | 1 | 2 | 8 SP |
| **Total** | **5** | **12** | **55 SP** |

### 7.4 Grand Total

| Client | Story Points | Sprints (34 SP/sprint) |
|--------|--------------|------------------------|
| Web Dashboard | 123 SP | ~3.6 sprints |
| CLI | 60 SP | ~1.8 sprints |
| VSCode Extension | 55 SP | ~1.6 sprints |
| **Total** | **238 SP** | **~7 sprints** |

---

## 8. Risk Assessment

### 8.1 Technical Risks

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| API contract mismatch | High | Medium | OpenAPI spec validation |
| Performance with large teams | Medium | Low | Pagination, virtualization |
| CLI auth token storage | Medium | Medium | Secure keychain integration |
| VSCode API compatibility | Low | Low | Test on multiple VS Code versions |

### 8.2 Business Risks

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| Delay in Teams UI blocks enterprise sales | High | Medium | Prioritize Sprint 84 |
| AGENTS.md UI delay loses differentiator | High | Medium | Parallel development |
| CLI gaps block CI/CD adoption | Medium | High | Sprint 85 auth + evidence |

---

## 9. Recommendations

### 9.1 Immediate Actions (This Week)

1. **Approve Sprint 84 Plan** - Teams & Organizations UI
2. **Start CLI auth design** - OAuth + API key support
3. **VSCode Evidence panel design** - UX mockups

### 9.2 Sprint 84-88 Roadmap

```
Sprint 84 (Jan 21-31): Web - Teams & Organizations
Sprint 85 (Feb 1-10):  Web - AGENTS.md + CLI Auth/Evidence
Sprint 86 (Feb 11-20): Web - Planning Part 1 + VSCode Evidence
Sprint 87 (Feb 21-28): Web - Planning Part 2 + VSCode Planning
Sprint 88 (Mar 1-10):  Web - Analytics + CLI/VSCode Polish
```

### 9.3 Success Metrics

| Metric | Current | Target (Sprint 88) |
|--------|---------|-------------------|
| Web Backend Coverage | 60% | 95% |
| CLI Backend Coverage | 15% | 50% |
| VSCode Backend Coverage | 55% | 80% |
| Total Coverage | 43% | 75% |

---

## Approval

- [ ] **CTO Approval**: Gap analysis accuracy and priority
- [ ] **CPO Approval**: Feature prioritization
- [ ] **Frontend Lead Approval**: Effort estimates
- [ ] **Backend Lead Approval**: API contract verification

---

**Document Owner:** PM Team
**Reviewers:** CTO, CPO, Frontend Lead, Backend Lead
**Created:** January 20, 2026
**Last Updated:** January 20, 2026
