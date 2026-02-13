# Sprint 18-20 Roadmap Summary: Frontend-Backend Gap Resolution

**Version**: 1.0.0
**Date**: November 28, 2025
**Status**: PLANNED
**Authority**: Frontend Lead + Backend Lead + CPO + CTO
**Foundation**: Frontend-Backend Gap Analysis Report
**Framework**: SDLC 5.1.3 Complete Lifecycle

---

## Executive Summary

Based on the [Frontend-Backend Gap Analysis](../../09-Executive-Reports/03-CPO-Reports/2025-11-28-FRONTEND-BACKEND-GAP-ANALYSIS.md), we have created 3 focused sprints to achieve **100% API coverage** and complete the MVP user experience.

### Current Status (Post Sprint 17)
- **API Coverage**: 48% (19/40 endpoints)
- **TypeScript Types**: 85% → **100%** (GitHub types added)
- **UI Completeness**: 70%
- **EvidencePage**: ❌ Static → ✅ **FIXED** (API integrated)

### Target Status (Post Sprint 20)
- **API Coverage**: 100% (40/40 endpoints)
- **TypeScript Types**: 100%
- **UI Completeness**: 100%
- **Onboarding TTFGE**: <10 minutes

---

## Sprint Roadmap Overview

```
┌─────────────────────────────────────────────────────────────────────────┐
│                      SPRINT 18: Evidence Integration                    │
│                            5 days • Priority P0                         │
├─────────────────────────────────────────────────────────────────────────┤
│ ✅ GitHub Types (DONE - added to api.ts)                               │
│ ✅ EvidencePage API Integration (DONE - user fixed)                    │
│ ⏳ Evidence Download                                                    │
│ ⏳ Integrity Check UI                                                   │
│ ⏳ Evidence Detail View                                                 │
│ ⏳ E2E Tests                                                            │
└─────────────────────────────────────────────────────────────────────────┘
                                    ↓
┌─────────────────────────────────────────────────────────────────────────┐
│                      SPRINT 19: CRUD Operations                         │
│                            5 days • Priority P1                         │
├─────────────────────────────────────────────────────────────────────────┤
│ ⏳ Create/Edit/Delete Project                                          │
│ ⏳ Create/Edit/Delete Gate                                             │
│ ⏳ Policy Detail View                                                   │
│ ⏳ Settings Page with GitHub Status                                     │
│ ⏳ Reusable Dialog Components                                          │
│ ⏳ E2E Tests                                                            │
└─────────────────────────────────────────────────────────────────────────┘
                                    ↓
┌─────────────────────────────────────────────────────────────────────────┐
│                   SPRINT 20: Onboarding Completion                      │
│                            5 days • Priority P0                         │
├─────────────────────────────────────────────────────────────────────────┤
│ ⏳ Repository Selection (GitHub API)                                    │
│ ⏳ Repository Analysis                                                  │
│ ⏳ Policy Pack AI Recommendation                                        │
│ ⏳ Stage Mapping Auto-Population                                        │
│ ⏳ First Gate Auto-Creation                                             │
│ ⏳ Full Onboarding E2E Test                                            │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## Gap Resolution Matrix

### Backend Endpoints → Frontend Integration

| Router | Endpoint | Sprint 17 | Sprint 18 | Sprint 19 | Sprint 20 |
|--------|----------|-----------|-----------|-----------|-----------|
| **auth** | POST /login | ✅ | - | - | - |
| **auth** | POST /refresh | ✅ | - | - | - |
| **auth** | POST /logout | ✅ | - | - | - |
| **auth** | GET /me | ✅ | - | - | - |
| **auth** | GET /health | ✅ | - | - | - |
| **dashboard** | GET /stats | ✅ | - | - | - |
| **dashboard** | GET /recent-gates | ✅ | - | - | - |
| **projects** | POST / | ❌ | - | ✅ | - |
| **projects** | GET / | ✅ | - | - | - |
| **projects** | GET /{id} | ✅ | - | - | - |
| **projects** | PUT /{id} | ❌ | - | ✅ | - |
| **projects** | DELETE /{id} | ❌ | - | ✅ | - |
| **gates** | POST / | ❌ | - | ✅ | ✅ |
| **gates** | GET / | ✅ | - | - | - |
| **gates** | GET /{id} | ✅ | - | - | - |
| **gates** | PUT /{id} | ❌ | - | ✅ | - |
| **gates** | DELETE /{id} | ❌ | - | ✅ | - |
| **gates** | POST /{id}/submit | ✅ | - | - | - |
| **gates** | POST /{id}/approve | ✅ | - | - | - |
| **gates** | GET /{id}/approvals | ✅ | - | - | - |
| **evidence** | POST /upload | ✅ | - | - | - |
| **evidence** | GET / | ❌ | ✅ | - | - |
| **evidence** | GET /{id} | ❌ | ✅ | - | - |
| **evidence** | POST /{id}/integrity | ❌ | ✅ | - | - |
| **evidence** | GET /download | ❌ | ✅ | - | - |
| **policies** | GET / | ✅ | - | - | - |
| **policies** | GET /{id} | ❌ | - | ✅ | - |
| **policies** | POST / | ❌ | - | - | - |
| **policies** | GET /evaluate | ❌ | - | - | - |
| **github** | GET /authorize | ✅ | - | - | - |
| **github** | POST /callback | ✅ | - | - | - |
| **github** | GET /status | ❌ | - | ✅ | - |
| **github** | DELETE /disconnect | ❌ | - | ✅ | - |
| **github** | GET /repositories | ❌ | - | - | ✅ |
| **github** | GET /repos/{owner}/{repo} | ❌ | - | - | ✅ |
| **github** | GET /repos/.../contents | ❌ | - | - | ✅ |
| **github** | GET /repos/.../languages | ❌ | - | - | ✅ |
| **github** | GET /repos/.../analyze | ❌ | - | - | ✅ |
| **github** | POST /sync | ❌ | - | - | ✅ |
| **github** | POST /webhook | ✅ | - | - | - |

### Coverage Progress

| Sprint | Before | After | Endpoints Added |
|--------|--------|-------|-----------------|
| Sprint 17 | 48% | 48% | 0 (testing focus) |
| Sprint 18 | 48% | 58% | +4 (evidence) |
| Sprint 19 | 58% | 75% | +7 (CRUD + settings) |
| Sprint 20 | 75% | 100% | +10 (onboarding + github) |

---

## Resource Allocation

### Sprint 18 (5 days)
| Day | Frontend | Backend | Focus |
|-----|----------|---------|-------|
| Day 1 | 100% | 10% | Evidence list API |
| Day 2 | 100% | 10% | Download + integrity |
| Day 3 | 100% | 0% | Detail view |
| Day 4 | 100% | 0% | Upload enhancement |
| Day 5 | 80% | 20% | Testing + review |

### Sprint 19 (5 days)
| Day | Frontend | Backend | Focus |
|-----|----------|---------|-------|
| Day 1 | 100% | 0% | Project CRUD |
| Day 2 | 100% | 0% | Gate CRUD |
| Day 3 | 100% | 10% | Policy + Settings |
| Day 4 | 100% | 0% | Components + polish |
| Day 5 | 80% | 20% | Testing + review |

### Sprint 20 (5 days)
| Day | Frontend | Backend | Focus |
|-----|----------|---------|-------|
| Day 1 | 100% | 10% | Repository selection |
| Day 2 | 100% | 20% | Repository analysis |
| Day 3 | 100% | 0% | Pack + mapping |
| Day 4 | 100% | 20% | First gate creation |
| Day 5 | 80% | 20% | E2E + review |

**Total Effort**:
- Frontend: 15 days (100%)
- Backend: 2.5 days (17%)

---

## Success Metrics

### Sprint 18 KPIs
| Metric | Target | Validation |
|--------|--------|------------|
| Evidence API Coverage | 100% | 5/5 endpoints |
| Evidence E2E Tests | 8+ tests | Playwright |
| Download Success Rate | 100% | Manual test |

### Sprint 19 KPIs
| Metric | Target | Validation |
|--------|--------|------------|
| Project CRUD | 100% | 5/5 operations |
| Gate CRUD | 100% | 8/8 operations |
| E2E Tests | 10+ tests | Playwright |

### Sprint 20 KPIs
| Metric | Target | Validation |
|--------|--------|------------|
| TTFGE | <10 min | Stopwatch test |
| Onboarding Completion | >80% | Analytics |
| Full Journey E2E | Pass | Playwright |

---

## Risk Mitigation

| Risk | Sprint | Impact | Mitigation |
|------|--------|--------|------------|
| GitHub rate limiting | 20 | High | Cache repos, show warning |
| Large file upload | 18 | Medium | Chunk upload, progress |
| Delete cascade | 19 | Medium | Confirm dialog, show impact |
| Session timeout | 20 | Low | Save progress, auto-resume |

---

## Definition of Done (Sprint 20)

- [ ] **API Coverage**: 100% (40/40 endpoints)
- [ ] **TypeScript Types**: 100% complete
- [ ] **E2E Tests**: 25+ tests passing
- [ ] **TTFGE**: <10 minutes verified
- [ ] **Mobile Responsive**: All pages
- [ ] **No P0/P1 Bugs**: Zero
- [ ] **Documentation**: Updated
- [ ] **Code Review**: All PRs approved

---

## Quick Reference: Sprint Plans

1. **[SPRINT-18-EVIDENCE-INTEGRATION.md](SPRINT-18-EVIDENCE-INTEGRATION.md)** - Evidence Vault API integration
2. **[SPRINT-19-CRUD-OPERATIONS.md](SPRINT-19-CRUD-OPERATIONS.md)** - Project/Gate/Policy management
3. **[SPRINT-20-ONBOARDING-COMPLETE.md](SPRINT-20-ONBOARDING-COMPLETE.md)** - Full onboarding flow

---

## Updates Since Gap Analysis

### Already Fixed (By User)

1. **GitHub Types** ✅
   - Added 15+ TypeScript types to `frontend/web/src/types/api.ts`
   - Includes: OAuth, Repository, Analysis, Sync, Webhook types

2. **EvidencePage.tsx** ✅
   - Updated from static UI to full API integration
   - Added: `useQuery` for evidence list
   - Added: Download functionality
   - Added: Integrity check mutation
   - Added: Filters and pagination

### Remaining Work

1. **Sprint 18**: Evidence detail view, upload enhancement, E2E tests
2. **Sprint 19**: All CRUD operations, Settings page
3. **Sprint 20**: Full onboarding flow with GitHub API

---

*SDLC Orchestrator - First Governance-First Platform on SDLC 5.1.3. Zero Mock Policy enforced.*

**"From 48% to 100% API coverage in 3 sprints. No shortcuts. No mocks. Production excellence."** ⚔️
