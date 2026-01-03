# ADR-025: Frontend Platform Consolidation - Next.js Monolith (Pre-GoLive)
## Decision: MOVE TO SINGLE FRONTEND PLATFORM (Next.js)

**Status**: ✅ APPROVED  
**Date**: January 03, 2026  
**Decision Makers**: CEO (directive) + CTO (implementation approval)  
**Stage**: Stage 02 (HOW - Design & Architecture)  
**Framework**: SDLC 5.1.2 Universal Framework

---

## Context

### Current Architecture (as of Jan 2026)

SDLC Orchestrator currently runs a **dual-frontend** setup:

| App | Framework | Port | Primary Purpose |
|-----|-----------|------|-----------------|
| Landing | Next.js 14 | 8311 | Marketing, SEO, Auth, Docs |
| Dashboard | React 18 + Vite | 8310 | Authenticated Platform Admin SPA |

This has caused measurable friction:
- Duplicate UI components across two frontends
- Two dependency trees and build pipelines
- More complex deployment/routing

### Business Constraint Update

We are **not officially Go-Live** yet and **do not have paying customers**. The CEO decision is to standardize on **one frontend platform** to maximize long-term maintainability and team efficiency, even if it introduces short-term migration work.

### Relationship to Prior Decision

This ADR **supersedes**:
- ADR-024: “Frontend Architecture - Dual App vs Monolithic”

ADR-024 was a valid technical decision at the time, given risk/ROI assumptions. Those assumptions changed due to executive direction and pre-GoLive status.

---

## Decision

### ✅ Consolidate to a single Next.js codebase

- **Selected platform**: **Next.js 14+ (App Router)**
- **Dashboard approach**: Client-first dashboard using **Client Components** where appropriate (SPA-like behavior), SSR reserved for public/SEO routes.

### Migration strategy: Strangler (no big-bang rewrite)

- Keep the current React Vite dashboard running during migration.
- Move routes incrementally from Vite → Next.js.
- Cut over only when success criteria are met.

---

## Success Criteria (must-hit before final cutover)

- Feature parity for core authenticated flows migrated.
- Performance budget (measured on representative hardware/network):
  - Navigation feels “instant” for primary dashboard flows.
  - No major regressions in initial load, memory, or API chatter.
- Stable auth handoff and session handling across routes.
- Error handling and observability parity (error boundary/logging).

---

## Implementation Plan (8 weeks, with early exit)

### Phase 0: 3–5 day spike (required)
- Scaffold Next.js dashboard shell, routing, auth integration.
- Migrate 3–5 highest-complexity screens to validate patterns.
- Decide go/no-go based on metrics.

### Phase 1: Migrate by route groups (parallelizable)
- Convert React Router → Next.js App Router.
- Migrate TanStack Query patterns carefully to avoid refetch storms.
- Incremental route cutover.

### Phase 2: Stabilize + QA
- Regression suite + E2E happy paths.
- Performance tuning and bundle analysis.

### Phase 3: Cutover + deprecate Vite
- Switch NGINX routing for dashboard paths to Next.js.
- Keep rollback path for 24–48 hours.
- Remove Vite container after stability window.

---

## Design Artifacts (Sprint 61-64)

**Sprint Plan**:
- [SPRINT-61-64-FRONTEND-PLATFORM-CONSOLIDATION.md](../../04-build/02-Sprint-Plans/SPRINT-61-64-FRONTEND-PLATFORM-CONSOLIDATION.md)

**Technical Specs**:
- [Frontend-Migration-Route-Map.md](../14-Technical-Specs/Frontend-Migration-Route-Map.md)
- [Dashboard-Migration-Technical-Spec.md](../14-Technical-Specs/Dashboard-Migration-Technical-Spec.md)
- [Frontend-Performance-Budget.md](../14-Technical-Specs/Frontend-Performance-Budget.md)

---

## Consequences

### Benefits
- Single frontend platform across NQH projects (consistency)
- Reduced duplication and unified UI patterns
- Simpler long-term onboarding and maintenance

### Costs / Risks
- Migration risk (routing/auth/state regressions)
- Potential dashboard performance regressions if not engineered carefully
- Temporary productivity hit during the migration window

---

## Notes

- This ADR intentionally treats consolidation as **pre-GoLive product engineering**, not a post-launch refactor.
- If Phase 0 metrics fail, escalate with data and either (a) extend spike, or (b) revert to dual-frontend + monorepo sharing approach.
