# Sprint 19: CRUD Operations for Projects, Gates & Policies

**Version**: 1.0.0
**Date**: November 28, 2025
**Status**: PLANNED
**Authority**: Frontend Lead + Backend Lead + CPO
**Foundation**: Frontend-Backend Gap Analysis Report
**Framework**: SDLC 6.1.0

---

## Sprint Overview

**Sprint Goal**: Implement Create, Update, Delete operations for Projects, Gates, and Policies.

**Duration**: 5 days
**Team**: Frontend Lead (100%), Backend Lead (10%)
**Priority**: P1 - High (Blocks Demo)

---

## Gap Analysis Reference

From [2025-11-28-FRONTEND-BACKEND-GAP-ANALYSIS.md](../../09-Executive-Reports/03-CPO-Reports/2025-11-28-FRONTEND-BACKEND-GAP-ANALYSIS.md):

| Feature | Current State | Target State |
|---------|---------------|--------------|
| Create Project | Missing | Dialog with form |
| Edit Project | Missing | Inline edit or dialog |
| Delete Project | Missing | Confirmation dialog |
| Create Gate | Missing | Dialog with form |
| Edit Gate | Missing | Inline edit or dialog |
| Delete Gate | Missing | Confirmation dialog |
| Policy Detail | Missing | Detail view page |

---

## Day 1: Project CRUD Operations

### Tasks

| # | Task | File | Est. | Owner |
|---|------|------|------|-------|
| 1.1 | Create CreateProjectDialog | components/projects/CreateProjectDialog.tsx | 2h | FE |
| 1.2 | Create EditProjectDialog | components/projects/EditProjectDialog.tsx | 2h | FE |
| 1.3 | Create DeleteProjectDialog | components/projects/DeleteProjectDialog.tsx | 1h | FE |
| 1.4 | Add mutations to ProjectsPage | ProjectsPage.tsx | 1h | FE |
| 1.5 | Add "New Project" button | ProjectsPage.tsx | 0.5h | FE |
| 1.6 | Add edit/delete actions to table | ProjectsPage.tsx | 0.5h | FE |

### Deliverables

**CreateProjectDialog.tsx**:
```typescript
interface CreateProjectDialogProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  onSuccess?: (project: Project) => void
}

// Form fields:
// - name: string (required, 3-100 chars)
// - description: string (optional, max 500 chars)
```

**EditProjectDialog.tsx**:
```typescript
interface EditProjectDialogProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  project: Project
  onSuccess?: (project: Project) => void
}
```

**DeleteProjectDialog.tsx**:
```typescript
// Warning message about:
// - Number of gates that will be deleted
// - Number of evidence files affected
// - Type project name to confirm
```

### API Integration

```typescript
// Create
const createMutation = useMutation({
  mutationFn: (data: ProjectCreateRequest) =>
    apiClient.post<Project>('/projects', data),
  onSuccess: () => queryClient.invalidateQueries(['projects']),
})

// Update
const updateMutation = useMutation({
  mutationFn: ({ id, data }: { id: string; data: ProjectUpdateRequest }) =>
    apiClient.put<Project>(`/projects/${id}`, data),
  onSuccess: () => queryClient.invalidateQueries(['projects']),
})

// Delete
const deleteMutation = useMutation({
  mutationFn: (id: string) => apiClient.delete(`/projects/${id}`),
  onSuccess: () => queryClient.invalidateQueries(['projects']),
})
```

### Success Criteria
- [ ] Can create new project via dialog
- [ ] Can edit existing project
- [ ] Can delete project with confirmation
- [ ] List refreshes after operations

---

## Day 2: Gate CRUD Operations

### Tasks

| # | Task | File | Est. | Owner |
|---|------|------|------|-------|
| 2.1 | Create CreateGateDialog | components/gates/CreateGateDialog.tsx | 2h | FE |
| 2.2 | Create EditGateDialog | components/gates/EditGateDialog.tsx | 2h | FE |
| 2.3 | Create DeleteGateDialog | components/gates/DeleteGateDialog.tsx | 1h | FE |
| 2.4 | Add mutations to GatesPage | GatesPage.tsx | 1h | FE |
| 2.5 | Add "New Gate" button | GatesPage.tsx | 0.5h | FE |
| 2.6 | Add edit/delete to GateDetailPage | GateDetailPage.tsx | 0.5h | FE |

### Deliverables

**CreateGateDialog.tsx**:
```typescript
// Form fields:
// - project_id: select from projects list
// - gate_name: string (required)
// - gate_type: select (G0.1, G0.2, G1, G2, G3, G4)
// - stage: select from SDLC stages
// - description: string (optional)
// - exit_criteria: array of { criterion, status }
```

**Exit Criteria Editor**:
```typescript
// Dynamic list of criteria:
// - Add criterion button
// - Remove criterion button
// - Status: pending/passed/failed
```

### Success Criteria
- [ ] Can create new gate via dialog
- [ ] Can select project for gate
- [ ] Can edit gate details
- [ ] Can manage exit criteria
- [ ] Can delete gate with confirmation

---

## Day 3: Policy Detail View & Settings

### Tasks

| # | Task | File | Est. | Owner |
|---|------|------|------|-------|
| 3.1 | Create PolicyDetailPage | pages/PolicyDetailPage.tsx | 2h | FE |
| 3.2 | Add route for policy detail | App.tsx | 0.5h | FE |
| 3.3 | Display Rego code with syntax highlight | PolicyDetailPage.tsx | 1h | FE |
| 3.4 | Create SettingsPage skeleton | pages/SettingsPage.tsx | 1h | FE |
| 3.5 | Add Settings route | App.tsx | 0.5h | FE |
| 3.6 | Add GitHub integration section | SettingsPage.tsx | 2h | FE |

### Deliverables

**PolicyDetailPage.tsx**:
```typescript
// Sections:
// 1. Policy Info: name, code, stage, severity
// 2. Description: full description
// 3. Rego Code: syntax highlighted code block
// 4. Evaluation History: recent evaluations
// 5. Related Gates: gates using this policy
```

**SettingsPage.tsx**:
```typescript
// Sections:
// 1. Profile Settings
// 2. Integrations
//    - GitHub (status, connect/disconnect)
//    - Future: Jira, Linear
// 3. Notifications
// 4. API Keys
```

### Success Criteria
- [ ] Policy detail page shows all info
- [ ] Rego code is syntax highlighted
- [ ] Settings page accessible
- [ ] GitHub status shows in Settings

---

## Day 4: Reusable Components & Polish

### Tasks

| # | Task | File | Est. | Owner |
|---|------|------|------|-------|
| 4.1 | Create ConfirmDialog component | components/ui/ConfirmDialog.tsx | 1h | FE |
| 4.2 | Create FormDialog component | components/ui/FormDialog.tsx | 1h | FE |
| 4.3 | Add form validation (Zod) | utils/validation.ts | 2h | FE |
| 4.4 | Add toast notifications | components/ui/Toaster.tsx | 1h | FE |
| 4.5 | Add loading states to all dialogs | Various | 1h | FE |
| 4.6 | Add error handling to all dialogs | Various | 1h | FE |

### Deliverables

**ConfirmDialog.tsx** (Reusable):
```typescript
interface ConfirmDialogProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  title: string
  description: string
  confirmText?: string
  cancelText?: string
  variant?: 'default' | 'destructive'
  onConfirm: () => void | Promise<void>
}
```

**FormDialog.tsx** (Reusable):
```typescript
interface FormDialogProps<T> {
  open: boolean
  onOpenChange: (open: boolean) => void
  title: string
  description?: string
  defaultValues?: Partial<T>
  onSubmit: (data: T) => void | Promise<void>
  children: React.ReactNode // Form fields
}
```

### Success Criteria
- [ ] ConfirmDialog works for all delete operations
- [ ] FormDialog works for create/edit
- [ ] Toast notifications show for success/error
- [ ] Form validation provides clear feedback

---

## Day 5: Testing & Documentation

### Tasks

| # | Task | File | Est. | Owner |
|---|------|------|------|-------|
| 5.1 | Add E2E tests for Project CRUD | e2e/projects.spec.ts | 2h | FE |
| 5.2 | Add E2E tests for Gate CRUD | e2e/gates.spec.ts | 2h | FE |
| 5.3 | Update API coverage documentation | docs/ | 1h | FE |
| 5.4 | Create Sprint 19 completion report | Sprint plans | 1h | FE |
| 5.5 | Code review & merge | PR | 2h | FE+BE |

### Test Scenarios

```typescript
// e2e/projects.spec.ts
test.describe('Project CRUD', () => {
  test('should create new project')
  test('should validate project name')
  test('should edit existing project')
  test('should delete project with confirmation')
  test('should show error for duplicate name')
})

// e2e/gates.spec.ts
test.describe('Gate CRUD', () => {
  test('should create new gate for project')
  test('should add exit criteria')
  test('should edit gate details')
  test('should delete gate with confirmation')
  test('should not delete gate with evidence')
})
```

### Success Criteria
- [ ] All E2E tests pass (10+ tests)
- [ ] Documentation updated
- [ ] PR approved and merged

---

## Sprint Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| API Coverage (Projects) | 100% | 5/5 endpoints |
| API Coverage (Gates) | 100% | 8/8 endpoints |
| E2E Test Coverage | 100% | All CRUD scenarios |
| Performance | <300ms | Dialog operations |

---

## Dependencies

| Dependency | Status | Notes |
|------------|--------|-------|
| Sprint 18 Complete | Required | Evidence integration |
| Backend APIs | ✅ Ready | All CRUD endpoints exist |
| UI Components | ✅ Ready | shadcn/ui + Dialog |

---

## Risk Assessment

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Delete cascade issues | Low | High | Confirm dialog shows affected items |
| Optimistic updates fail | Medium | Low | Revert on error, show toast |

---

## Definition of Done

- [ ] Project CRUD operations work
- [ ] Gate CRUD operations work
- [ ] Policy detail page complete
- [ ] Settings page with GitHub status
- [ ] Reusable dialog components
- [ ] E2E tests pass (10+ tests)
- [ ] Code review approved
- [ ] Documentation updated
- [ ] No P0/P1 bugs

---

*SDLC Orchestrator - First Governance-First Platform on SDLC 6.1.0. Zero Mock Policy enforced.*

**Sprint 19 Focus**: "CRUD Operations - Full management capabilities for Projects & Gates"
