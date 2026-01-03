# Frontend Migration Route Map
## Sprint 61-64: React Vite → Next.js App Router

**Version**: 1.0.0
**Date**: January 03, 2026
**Status**: APPROVED
**Decision Reference**: [ADR-025](../01-ADRs/ADR-025-Frontend-Platform-Consolidation-Nextjs-Monolith.md)
**Sprint Plan**: [Sprint 61-64](../../04-build/02-Sprint-Plans/SPRINT-61-64-FRONTEND-PLATFORM-CONSOLIDATION.md)

---

## Executive Summary

This document maps the migration path from the current React Vite Dashboard (34 routes, 61,824 LOC) to Next.js App Router. Routes are organized into 8 groups with complexity ratings and migration dependencies.

**Legacy Code Destination**: `frontend/99-legacy/`

---

## Current State Analysis

### React Dashboard Metrics
| Metric | Value |
|--------|-------|
| Total Routes | 34 |
| Protected Routes | 26 |
| Public Routes | 3 |
| Admin Routes | 5 |
| Total Components | 105 |
| Custom Hooks | 13 |
| Total LOC | 61,824 |

### Next.js Landing Metrics (existing)
| Metric | Value |
|--------|-------|
| Route Segments | 13 |
| UI Components | 5 (shadcn/ui) |
| i18n Support | Vi/En (next-intl) |
| API Client | 339 LOC |

---

## Route Group Migration Map

### Group 1: Authentication (PUBLIC) - Sprint 61
**Complexity**: 🟢 LOW
**Priority**: P0 (First)

| Current Route | Target Next.js Path | Complexity | Notes |
|---------------|---------------------|------------|-------|
| `/login` | `(auth)/login/page.tsx` | 🟢 | Already exists in Landing |
| `/register` | `(auth)/register/page.tsx` | 🟢 | Already exists in Landing |
| `/forgot-password` | `(auth)/forgot-password/page.tsx` | 🟢 | Already exists in Landing |
| `/auth/callback/*` | `(auth)/auth/callback/[provider]/page.tsx` | 🟢 | OAuth handlers |

**Migration Notes**:
- Auth routes already exist in Next.js Landing
- Reuse existing auth flow (`src/app/[locale]/(auth)/`)
- Token storage: localStorage → httpOnly cookie (security upgrade)

---

### Group 2: Dashboard Home (PROTECTED) - Sprint 61
**Complexity**: 🟡 MEDIUM
**Priority**: P0 (Spike)

| Current Route | Target Next.js Path | Complexity | Notes |
|---------------|---------------------|------------|-------|
| `/` (authenticated) | `(dashboard)/page.tsx` | 🟡 | Stats widgets, charts |
| `/projects` | `(dashboard)/projects/page.tsx` | 🟡 | Project list + CRUD |
| `/projects/:id` | `(dashboard)/projects/[id]/page.tsx` | 🟡 | Project detail |

**Component Dependencies**:
- `DashboardLayout` (1,200 LOC) → Layout component
- `Sidebar` (450 LOC) → Client Component
- `ProjectCard` (180 LOC) → Server Component candidate
- `StatsWidget` (320 LOC) → Client Component (real-time)

**Migration Notes**:
- Dashboard layout requires `"use client"` for sidebar state
- Project list can use Server Components with suspense
- Charts require client-side rendering (Recharts)

---

### Group 3: Gate Management (PROTECTED) - Sprint 62
**Complexity**: 🟡 MEDIUM
**Priority**: P1

| Current Route | Target Next.js Path | Complexity | Notes |
|---------------|---------------------|------------|-------|
| `/gates` | `(dashboard)/gates/page.tsx` | 🟡 | Gate list |
| `/gates/:id` | `(dashboard)/gates/[id]/page.tsx` | 🟡 | Gate detail |
| `/gates/:id/evaluate` | `(dashboard)/gates/[id]/evaluate/page.tsx` | 🟡 | Evaluation form |
| `/gate-history` | `(dashboard)/gate-history/page.tsx` | 🟢 | History list |

**Component Dependencies**:
- `GateCard` (280 LOC)
- `GateEvaluationForm` (520 LOC) - Complex form
- `GateTimeline` (340 LOC)
- `GateStatusBadge` (80 LOC)

**Migration Notes**:
- Gate evaluation uses React Hook Form + Zod (keep pattern)
- TanStack Query mutations for CRUD operations
- Consider Server Actions for form submissions

---

### Group 4: Evidence Vault (PROTECTED) - Sprint 62
**Complexity**: 🟡 MEDIUM
**Priority**: P1

| Current Route | Target Next.js Path | Complexity | Notes |
|---------------|---------------------|------------|-------|
| `/evidence` | `(dashboard)/evidence/page.tsx` | 🟡 | Evidence list |
| `/evidence/:id` | `(dashboard)/evidence/[id]/page.tsx` | 🟡 | Evidence detail |
| `/evidence/upload` | `(dashboard)/evidence/upload/page.tsx` | 🟡 | Upload flow |

**Component Dependencies**:
- `EvidenceCard` (220 LOC)
- `EvidenceUploader` (480 LOC) - File upload with progress
- `EvidenceViewer` (380 LOC) - Multi-format viewer
- `EvidenceMetadata` (240 LOC)

**Migration Notes**:
- File upload requires client-side handling
- Consider Next.js Route Handlers for upload API
- MinIO integration via API (no SDK import - AGPL compliance)

---

### Group 5: Policy Management (PROTECTED) - Sprint 62
**Complexity**: 🟢 LOW
**Priority**: P2

| Current Route | Target Next.js Path | Complexity | Notes |
|---------------|---------------------|------------|-------|
| `/policies` | `(dashboard)/policies/page.tsx` | 🟢 | Policy list |
| `/policies/:id` | `(dashboard)/policies/[id]/page.tsx` | 🟢 | Policy detail |
| `/policy-packs` | `(dashboard)/policy-packs/page.tsx` | 🟢 | Pack management |

**Component Dependencies**:
- `PolicyCard` (180 LOC)
- `PolicyEditor` (420 LOC) - YAML/Rego editor
- `PolicyPackSelector` (280 LOC)

**Migration Notes**:
- Monaco Editor for YAML/Rego (client-side only)
- Policy list is Server Component candidate
- OPA integration via REST API

---

### Group 6: Code Generation / EP-06 (PROTECTED) - Sprint 63
**Complexity**: 🔴 HIGH
**Priority**: P1

| Current Route | Target Next.js Path | Complexity | Notes |
|---------------|---------------------|------------|-------|
| `/codegen` | `(dashboard)/codegen/page.tsx` | 🔴 | Main codegen UI |
| `/codegen/sessions/:id` | `(dashboard)/codegen/sessions/[id]/page.tsx` | 🔴 | Session detail |
| `/codegen/history` | `(dashboard)/codegen/history/page.tsx` | 🟡 | History list |

**Component Dependencies**:
- `CodeGenerationPage` (922 LOC) - **Highest complexity**
- `QualityPipelineViewer` (2,800 LOC) - Real-time 4-gate display
- `StreamingCodeOutput` (680 LOC) - SSE streaming
- `IRVisualization` (540 LOC) - IR graph
- `ProviderSelector` (320 LOC) - Ollama/Claude selection

**Migration Notes**:
- **Critical**: SSE streaming requires careful Next.js handling
- Custom hooks: `useCodegenStream`, `useQualityPipeline`
- Consider Route Handlers for SSE endpoints
- WebSocket fallback if SSE problematic

---

### Group 7: SOP Generator (PROTECTED) - Sprint 63
**Complexity**: 🟡 MEDIUM
**Priority**: P2

| Current Route | Target Next.js Path | Complexity | Notes |
|---------------|---------------------|------------|-------|
| `/sop` | `(dashboard)/sop/page.tsx` | 🟡 | SOP list |
| `/sop/generate` | `(dashboard)/sop/generate/page.tsx` | 🟡 | Generation form |
| `/sop/:id` | `(dashboard)/sop/[id]/page.tsx` | 🟡 | SOP detail |
| `/sop/:id/edit` | `(dashboard)/sop/[id]/edit/page.tsx` | 🟡 | SOP editor |

**Component Dependencies**:
- `SOPGenerator` (580 LOC)
- `SOPViewer` (420 LOC) - Markdown renderer
- `SOPEditor` (640 LOC) - Rich text editor

**Migration Notes**:
- RAG integration via API
- Markdown rendering: consider next-mdx-remote
- Export to PDF/Word via API endpoints

---

### Group 8: Admin & Settings (PROTECTED/ADMIN) - Sprint 63
**Complexity**: 🟡 MEDIUM
**Priority**: P2

| Current Route | Target Next.js Path | Complexity | Notes |
|---------------|---------------------|------------|-------|
| `/settings` | `(dashboard)/settings/page.tsx` | 🟡 | User settings |
| `/settings/profile` | `(dashboard)/settings/profile/page.tsx` | 🟢 | Profile edit |
| `/settings/security` | `(dashboard)/settings/security/page.tsx` | 🟡 | MFA, password |
| `/admin` | `(admin)/page.tsx` | 🟡 | Admin dashboard |
| `/admin/users` | `(admin)/users/page.tsx` | 🟡 | User management |
| `/admin/roles` | `(admin)/roles/page.tsx` | 🟢 | Role management |
| `/admin/audit` | `(admin)/audit/page.tsx` | 🟡 | Audit logs |
| `/admin/system` | `(admin)/system/page.tsx` | 🟡 | System config |

**Component Dependencies**:
- `SettingsPage` (698 LOC) - Second highest complexity
- `UserTable` (380 LOC)
- `RolePermissionMatrix` (420 LOC)
- `AuditLogViewer` (340 LOC)

**Migration Notes**:
- Admin routes require role-based middleware
- Audit logs: Server Components with pagination
- System config: environment variable protection

---

## Target Next.js App Router Structure

```
frontend/landing/src/app/
├── [locale]/
│   ├── (marketing)/           # Existing marketing pages
│   │   ├── page.tsx           # Landing homepage
│   │   ├── features/
│   │   ├── pricing/
│   │   ├── docs/
│   │   └── marketplace/
│   │
│   ├── (auth)/                # Existing auth (reuse)
│   │   ├── login/
│   │   ├── register/
│   │   ├── forgot-password/
│   │   └── auth/callback/
│   │
│   ├── (dashboard)/           # NEW: Migrated from React
│   │   ├── layout.tsx         # Dashboard layout (client)
│   │   ├── page.tsx           # Dashboard home
│   │   ├── projects/
│   │   │   ├── page.tsx
│   │   │   └── [id]/
│   │   │       └── page.tsx
│   │   ├── gates/
│   │   │   ├── page.tsx
│   │   │   └── [id]/
│   │   │       ├── page.tsx
│   │   │       └── evaluate/
│   │   ├── evidence/
│   │   │   ├── page.tsx
│   │   │   ├── upload/
│   │   │   └── [id]/
│   │   ├── policies/
│   │   │   ├── page.tsx
│   │   │   └── [id]/
│   │   ├── codegen/           # HIGH complexity
│   │   │   ├── page.tsx
│   │   │   ├── sessions/[id]/
│   │   │   └── history/
│   │   ├── sop/
│   │   │   ├── page.tsx
│   │   │   ├── generate/
│   │   │   └── [id]/
│   │   │       ├── page.tsx
│   │   │       └── edit/
│   │   └── settings/
│   │       ├── page.tsx
│   │       ├── profile/
│   │       └── security/
│   │
│   └── (admin)/               # NEW: Admin routes
│       ├── layout.tsx         # Admin layout + role check
│       ├── page.tsx
│       ├── users/
│       ├── roles/
│       ├── audit/
│       └── system/
│
├── api/                       # Route Handlers
│   ├── auth/
│   ├── codegen/
│   │   └── stream/            # SSE endpoint
│   └── upload/
│
└── layout.tsx                 # Root layout
```

---

## Component Migration Priority

### Phase 0: Shared Components (Sprint 61 Spike)
**Goal**: Establish component patterns

| Component | LOC | Strategy |
|-----------|-----|----------|
| Button | 120 | Already in shadcn/ui |
| Card | 180 | Already in shadcn/ui |
| Input | 90 | Already in shadcn/ui |
| Badge | 60 | Already in shadcn/ui |
| Sidebar | 450 | Client Component |
| Header | 280 | Client Component |

### Phase 1: High-Value Components (Sprint 62)
| Component | LOC | Strategy |
|-----------|-----|----------|
| DashboardLayout | 1,200 | Client Component |
| ProjectCard | 180 | Server Component |
| GateCard | 280 | Server Component |
| EvidenceCard | 220 | Server Component |
| DataTable | 680 | Client Component (sorting) |

### Phase 2: Complex Components (Sprint 63)
| Component | LOC | Strategy |
|-----------|-----|----------|
| CodeGenerationPage | 922 | Client Component (streaming) |
| QualityPipelineViewer | 2,800 | Client Component (real-time) |
| PolicyEditor | 420 | Client Component (Monaco) |
| SOPEditor | 640 | Client Component (rich text) |

---

## Hook Migration Map

| Hook | LOC | Usage | Next.js Strategy |
|------|-----|-------|------------------|
| `useAuth` | 180 | Auth state | Context + middleware |
| `useProjects` | 220 | Project CRUD | TanStack Query (keep) |
| `useGates` | 280 | Gate operations | TanStack Query (keep) |
| `useEvidence` | 240 | Evidence CRUD | TanStack Query (keep) |
| `usePolicies` | 200 | Policy management | TanStack Query (keep) |
| `useCodegenStream` | 380 | SSE streaming | Custom with Route Handler |
| `useQualityPipeline` | 420 | 4-gate status | TanStack Query + polling |
| `useCouncil` | 340 | AI council | TanStack Query (keep) |
| `useValidation` | 280 | Form validation | React Hook Form (keep) |

---

## Migration Risks by Group

| Group | Risk Level | Primary Risk | Mitigation |
|-------|------------|--------------|------------|
| Auth | 🟢 Low | Already exists | Verify token handling |
| Dashboard | 🟡 Medium | Layout complexity | Spike first |
| Gates | 🟡 Medium | Form state | Keep React Hook Form |
| Evidence | 🟡 Medium | File uploads | Route Handlers |
| Policies | 🟢 Low | Monaco editor | Dynamic import |
| Codegen | 🔴 High | SSE streaming | Route Handler + fallback |
| SOP | 🟡 Medium | Rich text | next-mdx-remote |
| Admin | 🟡 Medium | Role middleware | Next.js middleware |

---

## Legacy Code Migration Path

### Step 1: Create Legacy Directory
```bash
mkdir -p frontend/99-legacy
```

### Step 2: Move After Successful Migration
```bash
# After Sprint 64 cutover is stable
mv frontend/web frontend/99-legacy/web-react-vite
```

### Step 3: Deprecation Period
- Keep for 30 days post-cutover
- NGINX rollback path available
- Remove after G4 validation

---

## Success Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| Route Parity | 34/34 | All routes migrated |
| Component Parity | 105/105 | All components ported |
| Performance | <100ms nav | Lighthouse CI |
| Bundle Size | <1MB | Build analysis |
| Test Coverage | 90%+ | Vitest + Playwright |
| Memory | <512MB | Chrome DevTools |

---

## References

- [ADR-025: Frontend Platform Consolidation](../01-ADRs/ADR-025-Frontend-Platform-Consolidation-Nextjs-Monolith.md)
- [Sprint 61-64 Plan](../../04-build/02-Sprint-Plans/SPRINT-61-64-FRONTEND-PLATFORM-CONSOLIDATION.md)
- [React Dashboard Analysis](./react-dashboard-analysis.md) (Sprint 61)
- [Next.js Landing Analysis](./nextjs-landing-analysis.md) (Sprint 61)
