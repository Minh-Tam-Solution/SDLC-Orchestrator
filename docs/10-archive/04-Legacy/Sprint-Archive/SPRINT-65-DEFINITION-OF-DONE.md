# Sprint 65: Code Quality + Route Migration #4 - Definition of Done

**Sprint**: 65
**Duration**: 1 week
**Goal**: Fix code quality issues, migrate policies page, prepare for EP-06 routes
**Status**: ✅ COMPLETE

---

## Prerequisites (from Sprint 64)

- [x] Settings page migrated (103 kB)
- [x] Project detail page migrated (108 kB)
- [x] Gate detail page migrated (151 kB)
- [x] CTO approved Sprint 64
- [x] NGINX already configured for Next.js (`/platform-admin` → Next.js)

---

## Sprint 65 Deliverables

### 1. Code Quality Fixes (P1)

| Task | Status | Notes |
|------|--------|-------|
| Fix `<img>` → `<Image>` in settings page | ✅ DONE | Used Next.js Image with `unoptimized` prop for external GitHub avatar |
| Add loading states to mutations | ✅ DONE | Added "Processing..."/"Approving..." to approve/reject buttons |
| Optimize gate detail bundle | ⏸️ DEFERRED | 18.7 kB actual - well under budget, no optimization needed |

### 2. Route Migration (P1)

| Route | Priority | Status | First Load JS Target |
|-------|----------|--------|---------------------|
| /platform-admin/policies | HIGH | ✅ DONE | 146 kB (within budget) |
| /platform-admin/policies/[id] | HIGH | ✅ DONE | 118 kB (within budget) |

### 3. NGINX Status

| Configuration | Status | Notes |
|---------------|--------|-------|
| `/platform-admin` → Next.js | ✅ DONE | Sprint 62 |
| `/platform-admin-vite` → Vite | ✅ DONE | Rollback route |
| Cookie routing | ✅ DONE | Sprint 63 httpOnly |

---

## Migration Status Summary

### Routes Migrated (10 total after Sprint 65)

| Route | Sprint | First Load JS |
|-------|--------|---------------|
| /platform-admin (Dashboard) | 62 | 109 kB |
| /platform-admin/projects | 62 | 108 kB |
| /platform-admin/gates | 62 | 109 kB |
| /platform-admin/evidence | 62 | 99.9 kB |
| /platform-admin/codegen | 62 | 90.4 kB |
| /platform-admin/settings | 64 | 109 kB |
| /platform-admin/projects/[id] | 64 | 108 kB |
| /platform-admin/gates/[id] | 64 | 152 kB |
| /platform-admin/policies | 65 | 146 kB |
| /platform-admin/policies/[id] | 65 | 118 kB |

### Routes Pending Migration (11 remaining)

**Phase 1 - Critical (Sprint 66):**
- `/app-builder` - EP-06 App Builder
- `/code-generation` - EP-06 Codegen engine

**Phase 2 - Important (Sprint 67):**
- `/sop-generator`, `/sop-history`, `/sop/:id` - SOP Management
- `/compliance` - Compliance dashboard

**Phase 3 - Low Priority:**
- `/support/*` - Consider static site instead

**Deprecated (Remove):**
- `/admin/*` - Move to separate internal admin portal

---

## Definition of Done Checklist

- [x] Fix `<img>` → `<Image>` ESLint warning
- [x] Add loading/error states to gate mutations
- [x] Migrate policies page to Next.js
- [x] Migrate policy detail page to Next.js
- [x] Build passes (0 errors, 0 warnings)
- [x] All routes under performance budget
- [x] CTO review approval ✅ (January 4, 2026)

---

## Technical Notes

### Image Optimization Fix
```tsx
// Before (ESLint warning)
<img src={user.avatar_url} alt="Avatar" />

// After (Next.js optimized)
import Image from "next/image";
<Image src={user.avatar_url} alt="Avatar" width={64} height={64} />
```

### Gate Detail Bundle Optimization
- Consider lazy loading `AlertDialog` component
- Split policy violations into separate component
- Use dynamic imports for heavy components

---

**Created**: January 04, 2026
**Completed**: January 04, 2026
**Owner**: Frontend Team Lead

---

## Sprint 65 Summary

### Accomplishments

1. **Code Quality Fixes**
   - Fixed ESLint warning in settings page (`<img>` → `<Image>` with `unoptimized` prop)
   - Added loading states to gate approve/reject mutations

2. **Route Migrations**
   - Migrated `/platform-admin/policies` with full policy list, stage filtering, and Rego code viewer
   - Migrated `/platform-admin/policies/[id]` with policy detail, metadata, and severity badges
   - Created loading skeletons for both pages

3. **New Components/Hooks**
   - `usePolicies.ts` - TanStack Query hooks for policies API
   - Policy type definitions in `api.ts`
   - Installed shadcn Select component

### Build Results (Final)
```
/platform-admin/policies       12.8 kB → 146 kB First Load JS
/platform-admin/policies/[id]   5.58 kB → 118 kB First Load JS
```

All routes under performance budget. 0 errors, 0 warnings.
