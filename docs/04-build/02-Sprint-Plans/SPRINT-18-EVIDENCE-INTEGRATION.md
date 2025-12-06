# Sprint 18: Evidence Page Integration & GitHub Types

**Version**: 1.0.0
**Date**: November 28, 2025
**Status**: PLANNED
**Authority**: Frontend Lead + Backend Lead + CPO
**Foundation**: Frontend-Backend Gap Analysis Report
**Framework**: SDLC 4.9 Complete Lifecycle

---

## Sprint Overview

**Sprint Goal**: Complete Evidence page API integration and finalize GitHub TypeScript types.

**Duration**: 5 days
**Team**: Frontend Lead (100%), Backend Lead (20%)
**Priority**: P0 - Critical (Blocks MVP Demo)

---

## Gap Analysis Reference

From [2025-11-28-FRONTEND-BACKEND-GAP-ANALYSIS.md](../../09-Executive-Reports/03-CPO-Reports/2025-11-28-FRONTEND-BACKEND-GAP-ANALYSIS.md):

| Issue | Current State | Target State | Status |
|-------|---------------|--------------|--------|
| EvidencePage.tsx | ✅ Full API integration | Complete | ✅ DONE |
| GitHub Types | ✅ 14 types added to api.ts | Complete | ✅ DONE |
| Evidence List | ✅ Paginated list view | Complete | ✅ DONE |
| Evidence Download | ✅ Download functionality | Complete | ✅ DONE |
| Integrity Check | ✅ Check button + status | Complete | ✅ DONE |

### P0 Items Completed (User Fix - Dec 2, 2025)

1. **GitHub Types** - 14 types added to `frontend/web/src/types/api.ts`
2. **EvidencePage.tsx** - Full API integration with:
   - `useQuery` for evidence list with pagination
   - Filters by gate_id and evidence_type
   - Download functionality
   - Integrity check mutation
   - Proper loading/empty states

---

## Day 1: Evidence List API Integration

### Tasks

| # | Task | File | Est. | Owner |
|---|------|------|------|-------|
| 1.1 | Add `useQuery` for evidence list | EvidencePage.tsx | 1h | FE |
| 1.2 | Create EvidenceTable component | components/evidence/EvidenceTable.tsx | 2h | FE |
| 1.3 | Add pagination controls | components/ui/Pagination.tsx | 1h | FE |
| 1.4 | Add filter by gate_id | EvidencePage.tsx | 1h | FE |
| 1.5 | Add filter by evidence_type | EvidencePage.tsx | 1h | FE |

### Deliverables

**EvidenceTable.tsx** (New Component):
```typescript
// Key features:
// - Columns: file_name, evidence_type, sha256_hash (truncated), uploaded_at, actions
// - Sortable columns
// - Row selection for bulk actions
// - Loading skeleton
```

**API Integration**:
```typescript
const { data, isLoading } = useQuery<EvidenceListResponse>({
  queryKey: ['evidence', { page, pageSize, gateId, evidenceType }],
  queryFn: () => apiClient.get('/evidence', { params }),
})
```

### Success Criteria
- [ ] Evidence list loads from API
- [ ] Pagination works correctly
- [ ] Filters work correctly
- [ ] Loading states display correctly

---

## Day 2: Evidence Download & Integrity Check

### Tasks

| # | Task | File | Est. | Owner |
|---|------|------|------|-------|
| 2.1 | Add download button to table | EvidenceTable.tsx | 1h | FE |
| 2.2 | Implement file download function | utils/download.ts | 1h | FE |
| 2.3 | Add integrity check button | EvidenceTable.tsx | 1h | FE |
| 2.4 | Create IntegrityBadge component | components/evidence/IntegrityBadge.tsx | 1h | FE |
| 2.5 | Add integrity check mutation | EvidencePage.tsx | 2h | FE |

### Deliverables

**Download Function**:
```typescript
async function downloadEvidence(evidenceId: string, fileName: string) {
  const response = await apiClient.get(`/evidence/download`, {
    params: { evidence_id: evidenceId },
    responseType: 'blob',
  })
  // Trigger browser download
  const url = window.URL.createObjectURL(response.data)
  const a = document.createElement('a')
  a.href = url
  a.download = fileName
  a.click()
}
```

**IntegrityBadge.tsx**:
```typescript
// Display integrity status with icons:
// ✅ Valid (green)
// ❌ Failed (red)
// ⏳ Pending (yellow)
// ❓ Unknown (gray)
```

### Success Criteria
- [ ] Files download correctly
- [ ] Integrity check runs and updates UI
- [ ] Status badges display correctly

---

## Day 3: Evidence Detail View & UI Polish

### Tasks

| # | Task | File | Est. | Owner |
|---|------|------|------|-------|
| 3.1 | Create EvidenceDetailDialog | components/evidence/EvidenceDetailDialog.tsx | 2h | FE |
| 3.2 | Add evidence detail route | App.tsx | 0.5h | FE |
| 3.3 | Show full SHA256 hash | EvidenceDetailDialog.tsx | 0.5h | FE |
| 3.4 | Add file preview (images/PDFs) | components/evidence/FilePreview.tsx | 2h | FE |
| 3.5 | Add audit trail section | EvidenceDetailDialog.tsx | 1h | FE |

### Deliverables

**EvidenceDetailDialog.tsx**:
```typescript
// Sections:
// 1. File Info: name, size, type, evidence_type
// 2. Integrity: SHA256 hash, verification status, last check
// 3. Upload Info: uploaded_by, uploaded_at, gate reference
// 4. Actions: Download, Verify, Delete
```

### Success Criteria
- [ ] Evidence detail dialog shows all info
- [ ] Image/PDF preview works
- [ ] Copy SHA256 hash button works

---

## Day 4: Evidence Upload Enhancement

### Tasks

| # | Task | File | Est. | Owner |
|---|------|------|------|-------|
| 4.1 | Enhance UploadEvidenceDialog | UploadEvidenceDialog.tsx | 1h | FE |
| 4.2 | Add drag-and-drop upload | UploadEvidenceDialog.tsx | 2h | FE |
| 4.3 | Add multiple file upload | UploadEvidenceDialog.tsx | 2h | FE |
| 4.4 | Add upload progress for each file | UploadEvidenceDialog.tsx | 1h | FE |
| 4.5 | Add file type validation (frontend) | utils/validation.ts | 1h | FE |

### Deliverables

**Enhanced Upload Features**:
- Drag-and-drop zone
- Multiple file selection
- Per-file upload progress
- File type icons
- Cancel upload button

### Success Criteria
- [ ] Drag-and-drop works
- [ ] Multiple files can be uploaded
- [ ] Progress shows for each file

---

## Day 5: Testing & Documentation

### Tasks

| # | Task | File | Est. | Owner |
|---|------|------|------|-------|
| 5.1 | Add E2E tests for evidence page | e2e/evidence.spec.ts | 3h | FE |
| 5.2 | Update API documentation | docs/ | 1h | FE |
| 5.3 | Create Sprint 18 completion report | Sprint plans | 1h | FE |
| 5.4 | Code review & merge | PR | 2h | FE+BE |

### Test Scenarios

```typescript
// e2e/evidence.spec.ts
test.describe('Evidence Page', () => {
  test('should list evidence with pagination')
  test('should filter by evidence type')
  test('should download evidence file')
  test('should verify evidence integrity')
  test('should upload single file')
  test('should upload multiple files via drag-drop')
  test('should show upload progress')
  test('should display evidence details')
})
```

### Success Criteria
- [ ] All E2E tests pass
- [ ] Documentation updated
- [ ] PR approved and merged

---

## Sprint Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| API Coverage (Evidence) | 100% | 5/5 endpoints |
| E2E Test Coverage | 100% | All scenarios covered |
| UI Completeness | 100% | List + Detail + Upload |
| Performance | <200ms | Evidence list load time |

---

## Dependencies

| Dependency | Status | Notes |
|------------|--------|-------|
| Backend Evidence API | ✅ Ready | All endpoints implemented |
| MinIO Service | ✅ Running | File storage working |
| GitHub Types | ✅ Done | Added to api.ts |

---

## Risk Assessment

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Large file upload timeout | Medium | Medium | Chunk upload, increase timeout |
| Browser memory for preview | Low | Low | Lazy load, size limits |

---

## Definition of Done

- [ ] Evidence page loads data from API
- [ ] All CRUD operations work
- [ ] File download works
- [ ] Integrity check works
- [ ] E2E tests pass (8+ tests)
- [ ] Code review approved
- [ ] Documentation updated
- [ ] No P0/P1 bugs

---

*SDLC Orchestrator - First Governance-First Platform on SDLC 4.9. Zero Mock Policy enforced.*

**Sprint 18 Focus**: "Evidence Integration - Complete API coverage for Evidence Vault"
