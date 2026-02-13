# Sprint 61-64: Frontend Platform Consolidation Roadmap
## Next.js Single Platform (Pre-GoLive) - Strangler Migration

**Epic**: Frontend Platform Standardization  
**Framework**: SDLC 5.1.2 Universal Framework  
**Duration**: 8 weeks (4 sprints)  
**Decision Reference**: [ADR-025: Frontend Platform Consolidation - Next.js Monolith (Pre-GoLive)](../../02-design/01-ADRs/ADR-025-Frontend-Platform-Consolidation-Nextjs-Monolith.md)

---

## Executive Summary

We will standardize SDLC Orchestrator on **one frontend platform: Next.js (App Router)**.

Because the product is **not officially Go-Live** and has **no paying customers**, we can accept migration effort now to reduce long-term maintenance cost and team fragmentation.

We will **not** do a big-bang rewrite. Instead, we use a **strangler migration**:
- Keep the current React + Vite dashboard alive during migration
- Incrementally migrate route groups into Next.js
- Cutover only after success criteria are met

---

## Design Documentation (Complete)

**Status**: ✅ COMPLETE (Jan 03, 2026)

These documents are the design source-of-truth for Sprint 61-64 execution:
- [Frontend-Migration-Route-Map.md](../../02-design/14-Technical-Specs/Frontend-Migration-Route-Map.md) (8 route groups + complexity ratings)
- [Dashboard-Migration-Technical-Spec.md](../../02-design/14-Technical-Specs/Dashboard-Migration-Technical-Spec.md) (architecture, auth guards, SSE streaming, testing)
- [Frontend-Performance-Budget.md](../../02-design/14-Technical-Specs/Frontend-Performance-Budget.md) (CWV targets, bundle limits, monitoring)

---

## Success Criteria (Non-Negotiable)

1. **Feature Parity** for migrated route groups (happy paths + key edge cases)
2. **Performance Budget**
   - Primary dashboard navigation feels “instant” for core flows
   - No major regressions in bundle size, memory usage, or API chatter
3. **Auth Stability**
   - OAuth and token/session handling works end-to-end
4. **Observability Parity**
   - Equivalent error boundary behavior and logging
5. **Rollback Ready**
   - NGINX can switch back to Vite dashboard within minutes

---

## Sprint 61: Spike + Architecture Baseline (3–5 days inside sprint)

**Goal**: Prove feasibility and lock technical patterns.

### Deliverables
- [ ] Next.js dashboard shell (App Router) with authenticated layout
- [ ] TanStack Query baseline working in Next.js
- [ ] Migrate 3–5 highest-complexity screens (representative)
- [ ] Performance measurements documented (baseline vs Next.js)
- [ ] Go/No-Go decision for full migration

### Notes
- If performance or complexity fails, escalate with data and re-scope.

---

## Sprint 62: Route Group Migration #1

**Goal**: Migrate first major cluster of dashboard routes (parallelizable).

### Deliverables
- [ ] Convert one full route group from React Router → Next.js
- [ ] Shared UI patterns and layouts established
- [ ] E2E smoke tests for migrated group

---

## Sprint 63: Route Group Migration #2 + Stabilization

**Goal**: Continue migration and reduce integration risk.

### Deliverables
- [ ] Second route group migrated
- [ ] Fix refetch storms / caching regressions
- [ ] Error handling parity (error boundary + fallback UX)
- [ ] Bundle + perf tuning pass

---

## Sprint 64: Cutover + Deprecate Vite Dashboard

**Goal**: Switch production routing for dashboard paths to Next.js and remove the old stack.

### Deliverables
- [ ] NGINX cutover to Next.js for dashboard routes
- [ ] 24–48h rollback window supported
- [ ] Remove Vite dashboard container after stability window
- [ ] Update runbooks and deployment docs

---

## Risks & Mitigation

| Risk | Impact | Mitigation |
|------|--------|------------|
| Dashboard UX/perf regression | High | Phase-0 spike + perf budgets + incremental cutover |
| Auth / routing regressions | High | Migrate in route groups + keep rollback |
| Hidden coupling to Vite build | Medium | Identify shared assets early in Sprint 61 |

---

## References

- [ADR-025: Frontend Platform Consolidation - Next.js Monolith](../../02-design/01-ADRs/ADR-025-Frontend-Platform-Consolidation-Nextjs-Monolith.md)
