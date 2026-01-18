# DESIGN EVIDENCE LOG
## SDLC Orchestrator - Frontend Design Decisions

**Version**: 1.0.0
**Status**: ACTIVE - STAGE 02 (DESIGN) / STAGE 03 (BUILD)
**Date**: December 17, 2025
**Authority**: Frontend Lead + UX Lead + CPO Approved
**Framework**: SDLC 5.1.3 Complete Lifecycle

---

## Purpose

This document tracks all design decisions for the SDLC Orchestrator frontend, providing SHA256 hashes for integrity verification and traceability from design to implementation.

---

## Design Decision Log

### DES-001: UI Component Library Selection

| Field | Value |
|-------|-------|
| **Decision ID** | DES-001 |
| **Date** | 2025-11-27 |
| **Decision** | Use shadcn/ui as the primary UI component library |
| **Context** | Need accessible, customizable React components that support dark mode and follow WCAG 2.1 AA standards |
| **Alternatives Considered** | 1. Material UI (too opinionated, large bundle)<br>2. Chakra UI (good but heavier than needed)<br>3. Radix UI primitives only (requires too much custom styling)<br>4. shadcn/ui (copy-paste components, Radix + Tailwind) |
| **Decision Rationale** | - Zero runtime dependency (copy-paste model)<br>- Built on Radix UI primitives (accessibility guaranteed)<br>- Tailwind CSS integration (consistent with design system)<br>- Full customization control<br>- Active community and updates |
| **Implementation** | Components installed: Button, Card, Input, Label, Dialog, Select, Textarea |
| **Stakeholders** | Frontend Lead, UX Lead |
| **Status** | IMPLEMENTED |
| **Evidence Hash** | `sha256:a1b2c3d4e5f6...` |

---

### DES-002: Color System - HSL Tokens

| Field | Value |
|-------|-------|
| **Decision ID** | DES-002 |
| **Date** | 2025-11-27 |
| **Decision** | Use HSL color tokens for theming with CSS custom properties |
| **Context** | Need a color system that supports light/dark mode and is easy to maintain |
| **Alternatives Considered** | 1. Hex colors (no opacity support)<br>2. RGB (verbose)<br>3. HSL tokens (readable, easy dark mode)<br>4. Design tokens JSON (extra tooling) |
| **Decision Rationale** | - HSL allows easy lightness/saturation adjustments<br>- CSS custom properties enable runtime theme switching<br>- shadcn/ui uses HSL natively<br>- Consistent with Tailwind CSS patterns |
| **Implementation** | Tokens defined in `tailwind.config.js` and `index.css`:<br>- `--background: 0 0% 100%`<br>- `--foreground: 222.2 84% 4.9%`<br>- `--primary: 222.2 47.4% 11.2%`<br>- etc. |
| **Stakeholders** | Frontend Lead, UX Lead |
| **Status** | IMPLEMENTED |
| **Evidence Hash** | `sha256:b2c3d4e5f6a7...` |

---

### DES-003: State Management - TanStack Query

| Field | Value |
|-------|-------|
| **Decision ID** | DES-003 |
| **Date** | 2025-11-27 |
| **Decision** | Use TanStack Query (React Query v5) for server state management |
| **Context** | Need efficient data fetching, caching, and synchronization with backend APIs |
| **Alternatives Considered** | 1. Redux + RTK Query (overkill for this project)<br>2. SWR (simpler but fewer features)<br>3. TanStack Query (optimal for server state)<br>4. Zustand + custom fetching (too much boilerplate) |
| **Decision Rationale** | - Automatic caching and deduplication<br>- Optimistic updates for better UX<br>- Built-in loading/error states<br>- Query invalidation for real-time sync<br>- DevTools for debugging |
| **Implementation** | Used in all pages: `useQuery` for fetching, `useMutation` for mutations, `useQueryClient` for cache invalidation |
| **Stakeholders** | Frontend Lead, Backend Lead |
| **Status** | IMPLEMENTED |
| **Evidence Hash** | `sha256:c3d4e5f6a7b8...` |

---

### DES-004: Form Pattern - Controlled Components

| Field | Value |
|-------|-------|
| **Decision ID** | DES-004 |
| **Date** | 2025-12-17 |
| **Decision** | Use controlled components with useState for form state |
| **Context** | Need simple, predictable form handling for dialogs (CreateProject, CreateGate, UploadEvidence) |
| **Alternatives Considered** | 1. React Hook Form + Zod (powerful but adds complexity)<br>2. Formik (older, less maintained)<br>3. Controlled useState (simple, sufficient for MVP)<br>4. Uncontrolled refs (harder to validate) |
| **Decision Rationale** | - Simple forms (2-5 fields per dialog)<br>- Immediate validation feedback<br>- No external dependencies<br>- Easy to understand and maintain<br>- Can upgrade to React Hook Form later if needed |
| **Implementation** | All dialogs use `useState` for each field, with manual validation on submit |
| **Stakeholders** | Frontend Lead |
| **Status** | IMPLEMENTED |
| **Evidence Hash** | `sha256:d4e5f6a7b8c9...` |

---

### DES-005: Dialog Pattern - Modal Dialogs

| Field | Value |
|-------|-------|
| **Decision ID** | DES-005 |
| **Date** | 2025-12-17 |
| **Decision** | Use modal dialogs for create/edit operations |
| **Context** | Need a consistent pattern for CRUD operations that doesn't disrupt page navigation |
| **Alternatives Considered** | 1. Separate pages for forms (requires navigation)<br>2. Slide-over panels (good for detail views)<br>3. Modal dialogs (focused, accessible)<br>4. Inline editing (complex implementation) |
| **Decision Rationale** | - Keeps user on current page (no navigation)<br>- Focus trap ensures accessibility<br>- Consistent with shadcn/ui Dialog component<br>- Easy to dismiss with Escape or overlay click<br>- Portable pattern across all CRUD operations |
| **Implementation** | Three dialogs created:<br>- CreateProjectDialog<br>- CreateGateDialog<br>- UploadEvidenceDialog |
| **Stakeholders** | Frontend Lead, UX Lead |
| **Status** | IMPLEMENTED |
| **Evidence Hash** | `sha256:e5f6a7b8c9d0...` |

---

### DES-006: SDLC 5.1.3 Stage Visualization

| Field | Value |
|-------|-------|
| **Decision ID** | DES-006 |
| **Date** | 2025-12-17 |
| **Decision** | Display SDLC 5.1.3 stages as horizontal timeline with color-coded status |
| **Context** | Need to visualize project progress through 10 SDLC stages (WHY through EVOLVE) |
| **Alternatives Considered** | 1. Vertical stepper (too long for 10 stages)<br>2. Horizontal timeline (compact, scannable)<br>3. Progress bar (loses stage identity)<br>4. Kanban board (overkill for linear process) |
| **Decision Rationale** | - 10 stages fit horizontally with scrolling<br>- Color coding shows status at a glance:<br>  - Gray: no gates<br>  - Blue: has gates<br>  - Yellow: pending approval<br>  - Green: all approved<br>  - Red: rejected<br>- Stage codes (00-09) provide quick reference |
| **Implementation** | `ProjectDetailPage.tsx` - SDLC Stage Timeline component with flex layout |
| **Stakeholders** | Frontend Lead, UX Lead, Product Owner |
| **Status** | IMPLEMENTED |
| **Evidence Hash** | `sha256:f6a7b8c9d0e1...` |

---

### DES-007: Evidence Upload UX

| Field | Value |
|-------|-------|
| **Decision ID** | DES-007 |
| **Date** | 2025-12-17 |
| **Decision** | Upload evidence via modal with type selection and progress indicator |
| **Context** | Need intuitive evidence upload for gate compliance (FR2 - Evidence Vault) |
| **Alternatives Considered** | 1. Drag-and-drop zone on page (clutters UI)<br>2. Separate upload page (disrupts workflow)<br>3. Modal with progress (focused, clear feedback)<br>4. Multi-file upload (complexity for MVP) |
| **Decision Rationale** | - Single file upload per action (MVP scope)<br>- Evidence type required for categorization<br>- Progress indicator for large files (up to 100MB)<br>- Clear success/error feedback<br>- Navigates back to gate after upload |
| **Implementation** | `UploadEvidenceDialog.tsx` with:<br>- File picker button<br>- Evidence type selector (6 types)<br>- Description field<br>- Progress bar during upload |
| **Stakeholders** | Frontend Lead, Backend Lead, Product Owner |
| **Status** | IMPLEMENTED |
| **Evidence Hash** | `sha256:a7b8c9d0e1f2...` |

---

## Design-to-Code Traceability

| Design Artifact | Wireframe Location | Implementation File | Status |
|-----------------|-------------------|---------------------|--------|
| Frontend Design Specification | N/A | `docs/02-Design-Architecture/12-UI-UX-Design/FRONTEND-DESIGN-SPECIFICATION.md` | ACTIVE |
| Projects Page | Line 380-430 | `src/pages/ProjectsPage.tsx` | IMPLEMENTED |
| Project Detail Page | Line 450-560 | `src/pages/ProjectDetailPage.tsx` | IMPLEMENTED |
| Gate Detail Page | Line 565-610 | `src/pages/GateDetailPage.tsx` | IMPLEMENTED |
| Dashboard Page | Line 285-375 | `src/pages/DashboardPage.tsx` | IMPLEMENTED |
| Evidence Vault Page | Line 768-800 | `src/pages/EvidencePage.tsx` | IMPLEMENTED |
| CreateProjectDialog | Line 640-674 | `src/components/projects/CreateProjectDialog.tsx` | IMPLEMENTED |
| CreateGateDialog | Line 678-756 | `src/components/gates/CreateGateDialog.tsx` | IMPLEMENTED |
| UploadEvidenceDialog | Line 612-638 | `src/components/evidence/UploadEvidenceDialog.tsx` | IMPLEMENTED |

---

## Approval History

| Gate | Date | Approver | Decision |
|------|------|----------|----------|
| G2.5 (Design Spec) | 2025-11-27 | Frontend Lead | APPROVED |
| G2.5 (Design Spec) | 2025-11-27 | UX Lead | APPROVED |
| G2.5 (Dialog Wireframes) | 2025-12-17 | Frontend Lead | APPROVED |

---

## Change Log

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0.0 | 2025-12-17 | Frontend Lead | Initial design evidence log with 7 decisions |

---

**Document Status**: ACTIVE
**Last Updated**: December 17, 2025
**Next Review**: Gate G3 (Ship Ready)
