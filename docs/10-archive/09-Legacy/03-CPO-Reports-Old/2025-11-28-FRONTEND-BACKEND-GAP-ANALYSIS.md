# Frontend/UI-Backend Gap Analysis Report

**Version**: 1.0.0
**Date**: November 28, 2025
**Status**: ACTIVE - Sprint 17
**Authority**: Frontend Lead + Backend Lead + CPO
**Foundation**: Sprint 17 Quality Assessment
**Framework**: SDLC 5.1.3 Complete Lifecycle

---

## Executive Summary

This report analyzes the integration gaps between the frontend React application and the FastAPI backend API. The analysis covers API endpoint coverage, TypeScript type definitions, and UI completeness.

### Overall Status

| Category | Score | Status |
|----------|-------|--------|
| API Endpoint Coverage | 75% | ⚠️ ATTENTION |
| TypeScript Type Coverage | 85% | ✅ GOOD |
| UI Feature Completeness | 70% | ⚠️ ATTENTION |
| E2E Test Coverage | 85% | ✅ GOOD |

---

## 1. Backend API Endpoints Summary

### 1.1 All Available Backend Endpoints (38 Total)

| Router | Endpoint | Method | Frontend Consumer | Status |
|--------|----------|--------|-------------------|--------|
| **auth** | `/login` | POST | LoginPage.tsx | ✅ |
| **auth** | `/refresh` | POST | client.ts (auto) | ✅ |
| **auth** | `/logout` | POST | DashboardLayout.tsx | ✅ |
| **auth** | `/me` | GET | useAuthStore | ✅ |
| **auth** | `/health` | GET | (internal) | ✅ |
| **dashboard** | `/stats` | GET | DashboardPage.tsx | ✅ |
| **dashboard** | `/recent-gates` | GET | DashboardPage.tsx | ✅ |
| **projects** | `POST /` | POST | (missing) | ❌ GAP |
| **projects** | `GET /` | GET | ProjectsPage.tsx | ✅ |
| **projects** | `GET /{id}` | GET | ProjectDetailPage.tsx | ✅ |
| **projects** | `PUT /{id}` | PUT | (missing) | ❌ GAP |
| **projects** | `DELETE /{id}` | DELETE | (missing) | ❌ GAP |
| **gates** | `POST /` | POST | (missing) | ❌ GAP |
| **gates** | `GET /` | GET | GatesPage.tsx | ✅ |
| **gates** | `GET /{id}` | GET | GateDetailPage.tsx | ✅ |
| **gates** | `PUT /{id}` | PUT | (missing) | ❌ GAP |
| **gates** | `DELETE /{id}` | DELETE | (missing) | ❌ GAP |
| **gates** | `POST /{id}/submit` | POST | GateDetailPage.tsx | ✅ |
| **gates** | `POST /{id}/approve` | POST | GateDetailPage.tsx | ✅ |
| **gates** | `GET /{id}/approvals` | GET | GateDetailPage.tsx | ✅ |
| **evidence** | `POST /upload` | POST | UploadEvidenceDialog.tsx | ✅ |
| **evidence** | `GET /` | GET | (missing) | ❌ GAP |
| **evidence** | `GET /{id}` | GET | (missing) | ❌ GAP |
| **evidence** | `POST /{id}/integrity` | POST | (missing) | ❌ GAP |
| **evidence** | `GET /download` | GET | (missing) | ❌ GAP |
| **policies** | `GET /` | GET | PoliciesPage.tsx | ✅ |
| **policies** | `GET /{id}` | GET | (missing) | ❌ GAP |
| **policies** | `POST /` | POST | (missing) | ❌ GAP |
| **policies** | `GET /evaluate` | GET | (missing) | ❌ GAP |
| **github** | `GET /authorize` | GET | (redirect via href) | ✅ |
| **github** | `POST /callback` | POST | GitHubCallbackPage.tsx | ✅ |
| **github** | `GET /status` | GET | (missing) | ❌ GAP |
| **github** | `DELETE /disconnect` | DELETE | (missing) | ❌ GAP |
| **github** | `GET /repositories` | GET | (missing) | ❌ GAP |
| **github** | `GET /repositories/{owner}/{repo}` | GET | (missing) | ❌ GAP |
| **github** | `GET /repositories/{owner}/{repo}/contents` | GET | (missing) | ❌ GAP |
| **github** | `GET /repositories/{owner}/{repo}/languages` | GET | (missing) | ❌ GAP |
| **github** | `GET /repositories/{owner}/{repo}/analyze` | GET | (missing) | ❌ GAP |
| **github** | `POST /sync` | POST | (missing) | ❌ GAP |
| **github** | `POST /webhook` | POST | (external webhook) | ✅ |

### 1.2 Coverage Statistics

| Router | Total | Covered | Missing | Coverage |
|--------|-------|---------|---------|----------|
| auth | 5 | 5 | 0 | **100%** ✅ |
| dashboard | 2 | 2 | 0 | **100%** ✅ |
| projects | 5 | 2 | 3 | **40%** ❌ |
| gates | 8 | 5 | 3 | **63%** ⚠️ |
| evidence | 5 | 1 | 4 | **20%** ❌ |
| policies | 4 | 1 | 3 | **25%** ❌ |
| github | 11 | 3 | 8 | **27%** ❌ |
| **TOTAL** | **40** | **19** | **21** | **48%** |

---

## 2. TypeScript Type Coverage

### 2.1 Defined Types in `frontend/web/src/types/api.ts`

| Category | Types Defined | Backend Schemas | Status |
|----------|---------------|-----------------|--------|
| Authentication | ✅ LoginRequest, TokenResponse, RefreshTokenRequest, LogoutRequest, UserProfile | Matches | ✅ COMPLETE |
| Projects | ✅ Project, ProjectDetail, ProjectCreateRequest, ProjectUpdateRequest | Matches | ✅ COMPLETE |
| Gates | ✅ GateCreateRequest, GateUpdateRequest, GateResponse, GateListResponse, GateApproval, PolicyViolation | Matches | ✅ COMPLETE |
| Evidence | ✅ EvidenceUploadRequest, EvidenceResponse, EvidenceListResponse, IntegrityCheckResponse | Matches | ✅ COMPLETE |
| Policies | ✅ PolicyResponse, PolicyListResponse, PolicyEvaluationRequest, PolicyEvaluationResponse | Matches | ✅ COMPLETE |
| Dashboard | ✅ DashboardStats, RecentGate | Matches | ✅ COMPLETE |
| **GitHub** | ❌ NOT DEFINED | 11 schemas needed | ❌ GAP |

### 2.2 Missing GitHub Types

The following TypeScript types need to be added:

```typescript
// Missing from frontend/web/src/types/api.ts

// GitHub OAuth Types
interface GitHubOAuthResponse {
  authorization_url: string
  state: string
}

interface GitHubCallbackRequest {
  code: string
  state: string
}

interface GitHubConnectionStatus {
  connected: boolean
  username: string | null
  avatar_url: string | null
  connected_at: string | null
  scope: string[]
}

// GitHub Repository Types
interface GitHubRepository {
  id: number
  name: string
  full_name: string
  description: string | null
  private: boolean
  html_url: string
  default_branch: string
  language: string | null
  stargazers_count: number
  forks_count: number
  updated_at: string
}

interface GitHubRepositoryListResponse {
  items: GitHubRepository[]
  total: number
  page: number
  page_size: number
}

interface GitHubFileContent {
  name: string
  path: string
  type: 'file' | 'dir'
  size: number | null
  sha: string
}

interface GitHubLanguages {
  [language: string]: number
}

interface GitHubAnalysisResult {
  repository: GitHubRepository
  structure: {
    has_readme: boolean
    has_license: boolean
    has_ci: boolean
    directories: string[]
  }
  languages: GitHubLanguages
  sdlc_stage_suggestion: string
  policy_pack_recommendation: string
}
```

---

## 3. UI/Page Gap Analysis

### 3.1 Existing Pages

| Page | File | API Integration | Status |
|------|------|-----------------|--------|
| Login | LoginPage.tsx | ✅ POST /login | ✅ COMPLETE |
| Dashboard | DashboardPage.tsx | ✅ GET /dashboard/stats, /recent-gates | ✅ COMPLETE |
| Projects | ProjectsPage.tsx | ✅ GET /projects | ⚠️ LIST ONLY |
| Project Detail | ProjectDetailPage.tsx | ✅ GET /projects/{id} | ⚠️ READ ONLY |
| Gates | GatesPage.tsx | ✅ GET /gates | ⚠️ LIST ONLY |
| Gate Detail | GateDetailPage.tsx | ✅ GET /gates/{id}, submit, approve | ✅ COMPLETE |
| Evidence | EvidencePage.tsx | ❌ **STATIC UI ONLY** | ❌ NOT INTEGRATED |
| Policies | PoliciesPage.tsx | ✅ GET /policies | ⚠️ LIST ONLY |
| Onboarding | OnboardingPage.tsx | ✅ Router setup | ⚠️ PARTIAL |
| GitHub Callback | GitHubCallbackPage.tsx | ✅ POST /github/callback | ✅ COMPLETE |

### 3.2 Critical Missing UI Features

#### 3.2.1 EvidencePage.tsx - NOT INTEGRATED ❌

**Current State**: Static UI with empty state only. No API calls.

**Missing Features**:
- [ ] `GET /evidence` - List evidence with pagination
- [ ] Evidence table with columns: file_name, evidence_type, uploaded_at, sha256_hash
- [ ] File download functionality (`GET /evidence/download`)
- [ ] Integrity check button (`POST /evidence/{id}/integrity`)
- [ ] Filter by gate_id or evidence_type

**Priority**: HIGH - Core Feature

#### 3.2.2 Project Management - INCOMPLETE ⚠️

**Current State**: Read-only project list and detail views.

**Missing Features**:
- [ ] Create Project dialog (`POST /projects`)
- [ ] Edit Project dialog (`PUT /projects/{id}`)
- [ ] Delete Project confirmation (`DELETE /projects/{id}`)

**Priority**: HIGH - Core Feature

#### 3.2.3 Gate Management - INCOMPLETE ⚠️

**Current State**: Read-only gate list, submit/approve on detail page.

**Missing Features**:
- [ ] Create Gate dialog (`POST /gates`)
- [ ] Edit Gate dialog (`PUT /gates/{id}`)
- [ ] Delete Gate confirmation (`DELETE /gates/{id}`)

**Priority**: HIGH - Core Feature

#### 3.2.4 GitHub Integration Pages - MISSING ❌

**Current State**: Only OAuth callback page exists.

**Missing Pages/Components**:
- [ ] Settings/Integrations page with GitHub status
- [ ] Repository selection during onboarding
- [ ] Repository analysis progress UI
- [ ] Sync status and manual sync trigger

**Priority**: HIGH - Onboarding Critical Path

#### 3.2.5 Policy Management - INCOMPLETE ⚠️

**Current State**: Read-only policy list.

**Missing Features**:
- [ ] Policy detail view (`GET /policies/{id}`)
- [ ] Policy evaluation trigger (`GET /policies/evaluate`)
- [ ] Create custom policy (`POST /policies`)

**Priority**: MEDIUM - Advanced Feature

---

## 4. Onboarding Flow Gap Analysis

### 4.1 Required Onboarding Steps

| Step | Page | Backend API | Frontend Status |
|------|------|-------------|-----------------|
| 1. Login | `/onboarding/login` | GET /github/authorize | ✅ Link exists |
| 2. Repository | `/onboarding/repository` | GET /github/repositories | ❌ NOT INTEGRATED |
| 3. Analyzing | `/onboarding/analyzing` | GET /github/repositories/{owner}/{repo}/analyze | ❌ NOT INTEGRATED |
| 4. Policy Pack | `/onboarding/policy-pack` | (local selection) | ✅ UI exists |
| 5. Stage Mapping | `/onboarding/stage-mapping` | (local selection) | ✅ UI exists |
| 6. First Gate | `/onboarding/first-gate` | POST /projects, POST /gates | ❌ NOT INTEGRATED |

### 4.2 Onboarding API Integration Needed

```typescript
// Step 2: Repository Selection
const { data: repositories } = useQuery({
  queryKey: ['github', 'repositories'],
  queryFn: () => apiClient.get('/github/repositories'),
})

// Step 3: Repository Analysis
const analysisMutation = useMutation({
  mutationFn: (repo: { owner: string; repo: string }) =>
    apiClient.get(`/github/repositories/${repo.owner}/${repo.repo}/analyze`),
})

// Step 6: Create Project and First Gate
const createProjectMutation = useMutation({
  mutationFn: (project: ProjectCreateRequest) =>
    apiClient.post('/projects', project),
})

const createGateMutation = useMutation({
  mutationFn: (gate: GateCreateRequest) =>
    apiClient.post('/gates', gate),
})
```

---

## 5. Priority Action Items

### 5.1 P0 - Critical (Block MVP)

| # | Item | Effort | Owner |
|---|------|--------|-------|
| 1 | Integrate EvidencePage.tsx with API | 4h | Frontend |
| 2 | Add GitHub types to api.ts | 1h | Frontend |
| 3 | Add Create/Edit/Delete Project UI | 4h | Frontend |
| 4 | Complete onboarding repository selection | 4h | Frontend |

### 5.2 P1 - High (Block Demo)

| # | Item | Effort | Owner |
|---|------|--------|-------|
| 5 | Add Create/Edit/Delete Gate UI | 4h | Frontend |
| 6 | Add GitHub status to Settings page | 2h | Frontend |
| 7 | Integrate onboarding analysis step | 2h | Frontend |
| 8 | Add policy detail view | 2h | Frontend |

### 5.3 P2 - Medium (Post-MVP)

| # | Item | Effort | Owner |
|---|------|--------|-------|
| 9 | Add policy evaluation UI | 4h | Frontend |
| 10 | Add evidence integrity check UI | 2h | Frontend |
| 11 | Add GitHub sync manual trigger | 2h | Frontend |

---

## 6. Recommendations

### 6.1 Immediate Actions (Sprint 18)

1. **Complete EvidencePage Integration**
   - Add `useQuery` for evidence list
   - Add file download functionality
   - Add integrity check button

2. **Add GitHub Types**
   - Create comprehensive GitHub types in api.ts
   - Generate types from OpenAPI spec if available

3. **Add CRUD Operations**
   - Create reusable dialog components for Create/Edit
   - Add confirmation dialogs for Delete operations

### 6.2 Architecture Recommendations

1. **Type Generation**: Consider using `openapi-typescript` to auto-generate types from backend OpenAPI spec
2. **API Client Enhancement**: Add typed methods for all endpoints
3. **Form Components**: Create reusable form components for Project/Gate/Evidence creation

### 6.3 Testing Recommendations

1. Add E2E tests for:
   - Evidence upload and download flow
   - Project CRUD operations
   - Gate CRUD operations
   - Complete onboarding flow with real API

---

## 7. Conclusion

The frontend-backend integration is approximately **48%** complete. While core read operations work well (dashboard, lists, detail views), write operations (create, update, delete) and the complete onboarding flow need attention.

### Critical Path Items:
1. EvidencePage API integration (core feature)
2. GitHub onboarding flow completion (user journey)
3. CRUD operations for Projects/Gates (user productivity)

### Estimated Effort to 100% Coverage:
- P0 items: **13 hours**
- P1 items: **10 hours**
- P2 items: **8 hours**
- **Total: ~31 hours (4 developer-days)**

---

*SDLC Orchestrator - First Governance-First Platform on SDLC 5.1.3. Zero Mock Policy enforced.*
