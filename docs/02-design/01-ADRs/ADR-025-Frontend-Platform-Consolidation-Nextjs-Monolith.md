# ADR-025: Frontend Platform Consolidation - Next.js Monolith (Pre-GoLive)
## Decision: MOVE TO SINGLE FRONTEND PLATFORM (Next.js)

**Status**: ✅ APPROVED → ⚠️ VIOLATED (Sprint 65-78) → ✅ RE-ENFORCED (Jan 19, 2026)  
**Date**: January 03, 2026 (Original) | January 19, 2026 (Re-enforced)  
**Decision Makers**: CEO (directive) + CTO (implementation approval)  
**Stage**: Stage 02 (HOW - Design & Architecture)  
**Framework**: SDLC 6.1.0

---

## ⚠️ GOVERNANCE ALERT (Jan 19, 2026)

**Incident:** This ADR was violated for 13 sprints (Sprint 65-78). Team unknowingly reverted to dual-frontend architecture (`frontend-landing` + `frontend-web`), contradicting the unified architecture decided in Sprint 61-64.

**Root Cause:** Lack of ADR enforcement in sprint planning. No automated compliance checks.

**Corrective Action:** Re-unifying frontend to single Next.js service (Sprint 79 priority).

**Lessons Learned:** [GOVERNANCE-FAILURE-FRONTEND-DUPLICATION.md](../../07-operate/03-Lessons-Learned/GOVERNANCE-FAILURE-FRONTEND-DUPLICATION.md)

**Key Takeaway:** We cannot govern others if we cannot govern ourselves. This incident led to mandatory ADR review in G-Sprint-Open and automated ADR compliance checks.

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

## Current Architecture (Post-Re-Unification - Jan 19, 2026)

### ✅ Correct State (ADR-025 Compliant)

```yaml
# docker-compose.yml
services:
  frontend:
    build: ./frontend
    container_name: sdlc-frontend
    ports:
      - "8310:3000"
    environment:
      - NODE_ENV=production
      - NEXT_PUBLIC_API_URL=http://backend:8300
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:3000/api/health"]
      interval: 30s
      timeout: 10s
      retries: 3
    depends_on:
      backend:
        condition: service_healthy
```

**Container Status:**
```
NAME              PORT          STATUS
sdlc-frontend    8310:3000     healthy
sdlc-backend     8300:8300     healthy
```

**Routes (All handled by Next.js App Router):**
- `/` - Landing page (SSR)
- `/login`, `/register`, `/auth/*` - Authentication (SSR + Client)
- `/app/*` - Authenticated dashboard (Client Components for SPA feel)
- `/admin/*` - Admin panel (superuser only, Client Components)
- `/docs/*` - Documentation (SSR for SEO)
- `/checkout/*` - Payment flows (SSR + Client)

### ❌ Incorrect State (Violated During Sprint 65-78)

```yaml
# docker-compose.yml (WRONG - DO NOT USE)
services:
  frontend-landing:  # ❌ Duplicate service
    build: ./frontend-landing
    ports:
      - "8311:3000"
  
  frontend-web:      # ❌ Duplicate service
    build: ./frontend-web
    ports:
      - "8310:3000"
```

**This violated ADR-025 for 13 sprints.** See: [Lessons Learned](../../07-operate/03-Lessons-Learned/GOVERNANCE-FAILURE-FRONTEND-DUPLICATION.md)

---

## Design Artifacts (Sprint 61-64)

**Sprint Plan**:
- [SPRINT-61-64-FRONTEND-PLATFORM-CONSOLIDATION.md](../../04-build/02-Sprint-Plans/SPRINT-61-64-FRONTEND-PLATFORM-CONSOLIDATION.md)

**Technical Specs**:
- [Frontend-Migration-Route-Map.md](../14-Technical-Specs/Frontend-Migration-Route-Map.md)
- [Dashboard-Migration-Technical-Spec.md](../14-Technical-Specs/Dashboard-Migration-Technical-Spec.md)
- [Frontend-Performance-Budget.md](../14-Technical-Specs/Frontend-Performance-Budget.md)

**Governance Artifacts (Post-Violation)**:
- [GOVERNANCE-FAILURE-FRONTEND-DUPLICATION.md](../../07-operate/03-Lessons-Learned/GOVERNANCE-FAILURE-FRONTEND-DUPLICATION.md)

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
