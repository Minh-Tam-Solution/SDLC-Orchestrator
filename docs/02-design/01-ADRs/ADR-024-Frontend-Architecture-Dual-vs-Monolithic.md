# ADR-024: Frontend Architecture - Dual App vs Monolithic
## Decision: KEEP DUAL FRONTEND (Reject Consolidation)

**Status**: ✅ APPROVED  
**Date**: December 28, 2025  
**Decision Maker**: CTO  
**Stage**: Stage 02 (HOW - Design & Architecture)  
**Framework**: SDLC 5.1.2 Universal Framework

---

## Context

### Current Architecture

SDLC Orchestrator uses a **dual-frontend architecture**:

| App | Framework | Port | Purpose | Routes | Size |
|-----|-----------|------|---------|--------|------|
| **Landing** | Next.js 14 | 8310 | Public marketing, SEO | ~13 pages | 799 MB |
| **Dashboard** | React 18 + Vite | 8311 | Authenticated SPA | 60+ routes | 363 MB |

### Proposal

Consolidate into a **single Next.js monolithic app**, similar to SOP Generator architecture:

```
frontend/ (monolithic Next.js)
├── (marketing)/     # Public landing pages
├── (auth)/          # Login, register, OAuth
├── (dashboard)/     # Main app (migrate from React)
└── (admin)/         # Admin panel (migrate from React)
```

### Comparison with SOP Generator

| Aspect | SDLC Orchestrator | SOP Generator |
|--------|-------------------|---------------|
| Frontend apps | 2 (Next.js + React) | 1 (Next.js) |
| Landing | Next.js (SSR) | Next.js (/) |
| Dashboard | React Vite (SPA) | Next.js (/dashboard/*) |
| Total pages | 73+ | ~20 |
| Complexity | HIGH (60+ dashboard routes) | LOW (simple CRUD) |
| Auth flow | Split across 2 apps | Single app |

---

## Decision

### ⚠️ REJECT CONSOLIDATION - KEEP DUAL FRONTEND

**Verdict**: Maintain current dual-frontend architecture.

**Alignment Score**: 35/100 for consolidation proposal

---

## Rationale: Why NOT to Consolidate

### 1. **Complexity Mismatch**

**SDLC Orchestrator** (this product):
- 60+ authenticated routes with complex state management
- Heavy SPA interactions (Gates, Evidence, Policies, AI features)
- TanStack Query for optimistic updates
- Real-time features (SSE streaming in Sprint 51)

**SOP Generator** (reference):
- ~20 simple pages (mostly CRUD)
- Form-heavy workflows (suitable for SSR)
- No complex client-side state
- Different product category

**Conclusion**: SOP Generator's simpler architecture is **NOT applicable** to SDLC Orchestrator's complexity.

---

### 2. **Performance Trade-offs**

| Metric | Current (Dual) | Proposed (Mono) | Impact |
|--------|----------------|-----------------|--------|
| Landing page load | ~200 KB (Next.js) | ~200 KB | ✅ Same |
| Dashboard initial load | ~800 KB (React SPA) | ~1.2 MB (Next.js) | 🔴 **+50% worse** |
| Subsequent navigation | Instant (SPA) | Full page reload | 🔴 **Much worse** |
| Bundle splitting | Optimal (Vite) | Next.js chunking | 🟡 Comparable |

**Analysis**:
- Landing page performance: **no benefit**
- Dashboard UX: **degraded** (loss of SPA instant navigation)
- Next.js SSR overhead: unnecessary for authenticated routes

---

### 3. **Deployment & Scaling**

#### Current (Dual Frontend)

```yaml
# docker-compose.yml
services:
  frontend-landing:
    image: sdlc-landing:latest
    ports: ["8310:3000"]
    resources:
      limits: { memory: 512M }

  frontend-dashboard:
    image: sdlc-dashboard:latest
    ports: ["8311:80"]
    resources:
      limits: { memory: 256M }
```

**Benefits**:
- ✅ Scale landing independently (SEO traffic)
- ✅ Scale dashboard independently (authenticated users)
- ✅ Lower resource usage (dashboard is static build)
- ✅ Isolated failures (landing crash ≠ dashboard crash)

#### Proposed (Monolithic)

```yaml
services:
  frontend:
    image: sdlc-frontend:latest
    ports: ["3000:3000"]
    resources:
      limits: { memory: 1.5GB }  # Next.js needs more RAM
```

**Drawbacks**:
- 🔴 Cannot scale landing vs dashboard separately
- 🔴 Higher baseline memory (Next.js server)
- 🔴 Single point of failure
- 🔴 Larger attack surface

**Verdict**: Current architecture has **better operational characteristics**.

---

### 4. **Development Velocity**

| Aspect | Current | Consolidated | Advantage |
|--------|---------|--------------|-----------|
| Team separation | Marketing team (Landing) vs Product team (Dashboard) | Mixed ownership | 🟢 **Current wins** |
| Deploy independence | Landing deploy ≠ Dashboard deploy | Coupled deploys | 🟢 **Current wins** |
| Build time | Landing: 2min, Dashboard: 1min (parallel) | Monolith: 5min | 🟢 **Current wins** |
| Shared components | Duplicate shadcn/ui | Reuse | 🔴 **Mono wins** |
| Bundle optimization | Vite (best-in-class) | Next.js (slower) | 🟢 **Current wins** |

**Analysis**:
- Only 1 minor advantage for monolith (shared UI components)
- 4 significant advantages for dual frontend
- Shared components can be mitigated via monorepo pattern (future)

---

### 5. **Migration Effort vs Value**

#### Effort Required

| Task | Effort | Risk |
|------|--------|------|
| Migrate 60+ React pages to Next.js | 4-6 weeks | HIGH |
| Convert React Router → App Router | 2 weeks | MEDIUM |
| Refactor TanStack Query patterns | 2 weeks | HIGH |
| Update auth flows | 1 week | HIGH |
| Testing & QA | 2 weeks | HIGH |
| **Total** | **11-15 weeks** | **HIGH** |

#### Value Delivered

| Benefit | Value |
|---------|-------|
| Faster landing page | ❌ No change (already SSR) |
| Better dashboard UX | ❌ Worse (loss of SPA) |
| Simpler deployment | ⚠️ Marginal (Docker Compose already simple) |
| Shared components | ⚠️ Minor (duplicate UI libs OK) |
| Single codebase | ⚠️ Minor (monorepo can solve) |

**ROI Analysis**:
- **Effort**: 11-15 weeks (3-4 months)
- **Value**: Minimal to negative
- **Verdict**: ❌ **NOT JUSTIFIED**

---

### 6. **SEO & Marketing Requirements**

| Requirement | Current (Dual) | Proposed (Mono) |
|-------------|----------------|-----------------|
| Landing page SSR | ✅ Next.js | ✅ Next.js |
| Marketing pages (/pricing, /features) | ✅ SSR | ✅ SSR |
| Dashboard SEO | ❌ Not needed (auth-only) | ❌ Wasted SSR |
| Google indexing | ✅ Optimal | ✅ Same |

**Analysis**:
- Current architecture already solves SEO perfectly (Next.js landing)
- Dashboard doesn't need SSR (behind authentication)
- Monolith wastes resources on SSR for authenticated routes

**Verdict**: No SEO benefit from consolidation.

---

## Comparison with Industry Patterns

### Multi-Frontend Examples

| Company | Architecture | Reasoning |
|---------|--------------|-----------|
| **Vercel** | Next.js landing + Dashboard SPA | Separate concerns |
| **GitHub** | Marketing site + GitHub.com (SPA) | Performance |
| **Stripe** | stripe.com + dashboard.stripe.com | Scale independently |
| **AWS** | aws.amazon.com + console.aws.amazon.com | Isolation |

**Pattern**: Industry leaders use **separate frontends** for public vs authenticated experiences.

---

## Alternative: Monorepo (Approved for Future)

Instead of consolidation, adopt a **monorepo pattern**:

```
frontend/
├── packages/
│   ├── ui/              # Shared shadcn/ui components
│   ├── api-client/      # Shared API client
│   └── utils/           # Shared utilities
├── apps/
│   ├── landing/         # Next.js (unchanged)
│   └── dashboard/       # React Vite (unchanged)
└── package.json         # Turborepo or Nx
```

**Benefits**:
- ✅ Share components without duplication
- ✅ Keep dual-app benefits
- ✅ Minimal migration effort (2-3 days)
- ✅ Better than monolith

**Verdict**: Monorepo is the **correct solution** for code sharing, NOT consolidation.

---

## Decision Matrix

| Criterion | Weight | Dual Frontend | Monolithic | Winner |
|-----------|--------|---------------|------------|--------|
| Performance | 25% | 9/10 | 6/10 | 🟢 Dual |
| Scalability | 20% | 9/10 | 6/10 | 🟢 Dual |
| Dev Velocity | 20% | 8/10 | 7/10 | 🟢 Dual |
| Maintainability | 15% | 7/10 | 8/10 | 🔴 Mono |
| SEO | 10% | 10/10 | 10/10 | 🟡 Tie |
| Deployment | 10% | 9/10 | 7/10 | 🟢 Dual |
| **Total** | 100% | **8.45** | **6.9** | **🟢 Dual +22%** |

---

## Consequences

### Positive (Keeping Dual Frontend)

- ✅ **Zero migration cost** (0 weeks vs 11-15 weeks)
- ✅ **Maintain SPA performance** for dashboard
- ✅ **Independent scaling** for landing vs dashboard
- ✅ **Team separation** (marketing vs product)
- ✅ **Deploy isolation** (lower risk)
- ✅ **Proven architecture** (industry standard)

### Negative

- ⚠️ **Duplicate shadcn/ui** components (mitigated by monorepo in Sprint 61)
- ⚠️ **Two deploy pipelines** (acceptable trade-off)
- ⚠️ **Nginx routing complexity** (already solved and stable)

---

## Action Items

| # | Action | Owner | Timeline |
|---|--------|-------|----------|
| 1 | ✅ Document decision in ADR-024 | CTO | Done |
| 2 | ⏳ Adopt monorepo pattern (Turborepo) | Frontend Lead | Sprint 61 |
| 3 | ⏳ Extract shared UI to `packages/ui` | Frontend Dev | Sprint 61 |
| 4 | ⏳ Update CI/CD for monorepo | DevOps | Sprint 61 |
| 5 | ❌ Reject consolidation proposal | CTO | Done |

---

## Nginx Configuration (Current & Proven)

```nginx
# SDLC Orchestrator - Dual Frontend Routing
# Tested and stable as of Dec 28, 2025

server {
    listen 443 ssl http2;
    server_name sdlc.nhatquangholding.com;

    # Public routes → Landing (Next.js on port 8310)
    location ~ ^/(login|register|forgot-password|pricing|features|docs|demo|auth/callback)$ {
        proxy_pass http://127.0.0.1:8310;
        include /etc/nginx/snippets/proxy-params.conf;
    }

    # Static landing
    location = / {
        proxy_pass http://127.0.0.1:8310;
        include /etc/nginx/snippets/proxy-params.conf;
    }

    # Frontend docs (Sprint 60)
    location /docs {
        proxy_pass http://127.0.0.1:8310;
        include /etc/nginx/snippets/proxy-params.conf;
    }

    # Authenticated routes → Dashboard (React on port 8311)
    location / {
        proxy_pass http://127.0.0.1:8311;
        include /etc/nginx/snippets/proxy-params.conf;
    }

    # Backend API
    location /api/ {
        proxy_pass http://127.0.0.1:8300;
        include /etc/nginx/snippets/proxy-params.conf;
    }

    # Backend OpenAPI docs
    location /openapi-docs {
        proxy_pass http://127.0.0.1:8300/api/docs;
        include /etc/nginx/snippets/proxy-params.conf;
    }
}
```

**Status**: ✅ Working in production, no changes needed.

---

## Review Gates

### Sprint 61: Monorepo Adoption (if approved)

- [ ] Evaluate Turborepo vs Nx
- [ ] Extract shared UI components to `packages/ui`
- [ ] Update build scripts for monorepo
- [ ] Test CI/CD with monorepo structure

---

## References

- [Sprint 60: i18n Localization](../../04-build/02-Sprint-Plans/SPRINT-60-COMPLETION-REPORT.md) - Landing page already has i18n
- [ADR-022: Multi-Provider Codegen](./ADR-022-Multi-Provider-Codegen-Architecture.md) - Backend multi-provider pattern
- [G3 Go-Live Readiness Report](../../09-govern/02-Gate-Reviews/G3-GO-LIVE-READINESS-REPORT.md) - Current architecture assessment
- Industry examples: Vercel, GitHub, Stripe, AWS

---

## Approval

**CTO Approval**: ✅ December 28, 2025

**Signature**:
```
DECISION: KEEP DUAL FRONTEND ARCHITECTURE

RATIONALE:
1. SDLC Orchestrator (60+ routes) ≠ SOP Generator (20 pages)
2. SPA performance critical for dashboard UX
3. Independent scaling required for SEO vs authenticated traffic
4. Migration effort (11-15 weeks) not justified by benefits
5. Industry standard pattern (Vercel, GitHub, Stripe, AWS)

ALTERNATIVE APPROVED:
Adopt monorepo pattern (Sprint 61) to share components
WITHOUT losing dual-frontend benefits.

This decision protects product performance, team velocity,
and operational scalability.
```

---

**Last Updated**: December 28, 2025  
**Next Review**: Sprint 61 (Monorepo adoption)  
**Document Status**: OFFICIAL - CTO Decision
