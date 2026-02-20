# Sprint 20: Onboarding Flow Completion

**Version**: 1.0.0
**Date**: November 28, 2025
**Status**: PLANNED
**Authority**: Frontend Lead + Backend Lead + CPO
**Foundation**: Frontend-Backend Gap Analysis Report
**Framework**: SDLC 6.1.0

---

## Sprint Overview

**Sprint Goal**: Complete the 6-step onboarding flow with full API integration for GitHub repository selection, analysis, and first gate creation.

**Duration**: 5 days
**Team**: Frontend Lead (100%), Backend Lead (20%)
**Priority**: P0 - Critical (User Journey Critical Path)

---

## Gap Analysis Reference

From [2025-11-28-FRONTEND-BACKEND-GAP-ANALYSIS.md](../../09-Executive-Reports/03-CPO-Reports/2025-11-28-FRONTEND-BACKEND-GAP-ANALYSIS.md):

| Step | Page | API Integration | Status |
|------|------|-----------------|--------|
| 1. Login | `/onboarding/login` | ✅ GitHub OAuth | Complete |
| 2. Repository | `/onboarding/repository` | ❌ Missing | **NEEDS WORK** |
| 3. Analyzing | `/onboarding/analyzing` | ❌ Missing | **NEEDS WORK** |
| 4. Policy Pack | `/onboarding/policy-pack` | ✅ Local | Complete |
| 5. Stage Mapping | `/onboarding/stage-mapping` | ✅ Local | Complete |
| 6. First Gate | `/onboarding/first-gate` | ❌ Missing | **NEEDS WORK** |

---

## Day 1: Repository Selection Page

### Tasks

| # | Task | File | Est. | Owner |
|---|------|------|------|-------|
| 1.1 | Create RepositoryListPage | pages/onboarding/RepositoryPage.tsx | 2h | FE |
| 1.2 | Add useQuery for repositories | RepositoryPage.tsx | 1h | FE |
| 1.3 | Create RepositoryCard component | components/onboarding/RepositoryCard.tsx | 1h | FE |
| 1.4 | Add search/filter functionality | RepositoryPage.tsx | 1h | FE |
| 1.5 | Add pagination for large lists | RepositoryPage.tsx | 1h | FE |
| 1.6 | Store selected repo in context | OnboardingContext.tsx | 1h | FE |

### Deliverables

**RepositoryPage.tsx**:
```typescript
export default function RepositoryPage() {
  const { data: repos, isLoading } = useQuery<GitHubRepositoryListResponse>({
    queryKey: ['github', 'repositories'],
    queryFn: () => apiClient.get('/github/repositories'),
  })

  // Features:
  // - Search by name
  // - Filter by visibility (public/private)
  // - Filter by language
  // - Sort by updated_at, stars, name
}
```

**RepositoryCard.tsx**:
```typescript
interface RepositoryCardProps {
  repo: GitHubRepository
  selected: boolean
  onSelect: () => void
}

// Display:
// - Repo name + owner avatar
// - Description (truncated)
// - Language badge
// - Stars + Forks count
// - Last updated
// - Private/Public badge
```

### Success Criteria
- [ ] Repository list loads from GitHub API
- [ ] Search works in real-time
- [ ] Filters work correctly
- [ ] Selection persists to next step

---

## Day 2: Repository Analysis Page

### Tasks

| # | Task | File | Est. | Owner |
|---|------|------|------|-------|
| 2.1 | Create AnalyzingPage | pages/onboarding/AnalyzingPage.tsx | 2h | FE |
| 2.2 | Add analysis mutation | AnalyzingPage.tsx | 1h | FE |
| 2.3 | Create AnalysisProgress component | components/onboarding/AnalysisProgress.tsx | 1h | FE |
| 2.4 | Display analysis results | AnalyzingPage.tsx | 2h | FE |
| 2.5 | Auto-navigate on completion | AnalyzingPage.tsx | 0.5h | FE |
| 2.6 | Handle analysis errors | AnalyzingPage.tsx | 0.5h | FE |

### Deliverables

**AnalyzingPage.tsx**:
```typescript
export default function AnalyzingPage() {
  const { selectedRepo } = useOnboardingContext()

  const analysisMutation = useMutation({
    mutationFn: () => apiClient.get<GitHubAnalysisResult>(
      `/github/repositories/${selectedRepo.owner.login}/${selectedRepo.name}/analyze`
    ),
    onSuccess: (data) => {
      setAnalysisResult(data)
      // Store recommendations in context
      setRecommendedPolicyPack(data.recommended_policy_pack)
      setStageMappings(data.stage_mappings)
    },
  })

  useEffect(() => {
    analysisMutation.mutate()
  }, [])
}
```

**AnalysisProgress.tsx**:
```typescript
// Steps:
// 1. Connecting to repository...
// 2. Scanning file structure...
// 3. Detecting languages...
// 4. Analyzing project type...
// 5. Generating recommendations...

// Progress bar with step indicators
// Estimated time remaining
```

### Success Criteria
- [ ] Analysis starts automatically on page load
- [ ] Progress shows meaningful steps
- [ ] Results display correctly
- [ ] Recommendations stored for next steps

---

## Day 3: Policy Pack & Stage Mapping Enhancement

### Tasks

| # | Task | File | Est. | Owner |
|---|------|------|------|-------|
| 3.1 | Add AI recommendation badge | PolicyPackPage.tsx | 1h | FE |
| 3.2 | Pre-select recommended pack | PolicyPackPage.tsx | 0.5h | FE |
| 3.3 | Show pack comparison details | PolicyPackPage.tsx | 1h | FE |
| 3.4 | Pre-populate stage mappings | StageMappingPage.tsx | 1h | FE |
| 3.5 | Add folder browser from repo | StageMappingPage.tsx | 2h | FE |
| 3.6 | Allow custom mappings | StageMappingPage.tsx | 1h | FE |

### Deliverables

**PolicyPackPage.tsx Enhancement**:
```typescript
// Show AI recommendation:
// "Based on your TypeScript/React project, we recommend Standard pack"
// - Highlight recommended pack
// - Show comparison table (gates, coverage, features)
```

**StageMappingPage.tsx Enhancement**:
```typescript
// Pre-populate from analysis:
// src/ → BUILD (Stage 03)
// tests/ → VERIFY (Stage 04)
// docs/ → Multiple stages

// Allow:
// - Add custom mapping
// - Remove mapping
// - Change stage for folder
// - Browse repo folders
```

### Success Criteria
- [ ] AI recommendation clearly visible
- [ ] Default selection based on recommendation
- [ ] Stage mappings pre-populated
- [ ] User can customize all selections

---

## Day 4: First Gate Creation

### Tasks

| # | Task | File | Est. | Owner |
|---|------|------|------|-------|
| 4.1 | Create FirstGatePage | pages/onboarding/FirstGatePage.tsx | 2h | FE |
| 4.2 | Add project creation mutation | FirstGatePage.tsx | 1h | FE |
| 4.3 | Add gate creation mutation | FirstGatePage.tsx | 1h | FE |
| 4.4 | Create SuccessAnimation component | components/onboarding/SuccessAnimation.tsx | 1h | FE |
| 4.5 | Redirect to project dashboard | FirstGatePage.tsx | 0.5h | FE |
| 4.6 | Handle errors with retry | FirstGatePage.tsx | 1h | FE |

### Deliverables

**FirstGatePage.tsx**:
```typescript
export default function FirstGatePage() {
  const { selectedRepo, policyPack, stageMappings } = useOnboardingContext()

  // Step 1: Create project
  const createProjectMutation = useMutation({
    mutationFn: () => apiClient.post<Project>('/projects', {
      name: selectedRepo.name,
      description: selectedRepo.description,
    }),
  })

  // Step 2: Sync GitHub repo to project
  const syncMutation = useMutation({
    mutationFn: (projectId: string) => apiClient.post('/github/sync', {
      github_repo_id: selectedRepo.id,
      github_repo_full_name: selectedRepo.full_name,
      project_name: selectedRepo.name,
      auto_setup: true,
    }),
  })

  // Step 3: Create first gate
  const createGateMutation = useMutation({
    mutationFn: (projectId: string) => apiClient.post<GateResponse>('/gates', {
      project_id: projectId,
      gate_name: 'G0.1 Problem Definition',
      gate_type: 'G0.1',
      stage: 'WHY',
      description: 'Initial project setup gate',
    }),
  })
}
```

**SuccessAnimation.tsx**:
```typescript
// Confetti or celebration animation
// "Congratulations! Your project is set up"
// Stats: 1 project, 1 gate, X policies
// CTA: "Go to Dashboard" or "Create Next Gate"
```

### Success Criteria
- [ ] Project created successfully
- [ ] GitHub repo synced to project
- [ ] First gate created automatically
- [ ] Success page with next steps

---

## Day 5: Testing & Polish

### Tasks

| # | Task | File | Est. | Owner |
|---|------|------|------|-------|
| 5.1 | Add E2E tests for full onboarding | e2e/onboarding-complete.spec.ts | 3h | FE |
| 5.2 | Add error recovery flows | Various | 1h | FE |
| 5.3 | Add loading skeletons | Various | 1h | FE |
| 5.4 | Create Sprint 20 completion report | Sprint plans | 1h | FE |
| 5.5 | Code review & merge | PR | 2h | FE+BE |

### Test Scenarios

```typescript
// e2e/onboarding-complete.spec.ts
test.describe('Complete Onboarding Flow', () => {
  test('should complete full onboarding journey', async ({ page }) => {
    // Step 1: Start at login
    await page.goto('/onboarding/login')
    await page.click('text=Continue with GitHub')

    // Step 2: Select repository
    await expect(page).toHaveURL('/onboarding/repository')
    await page.click('[data-testid="repo-my-project"]')
    await page.click('text=Continue')

    // Step 3: Wait for analysis
    await expect(page).toHaveURL('/onboarding/analyzing')
    await expect(page.locator('text=Analysis complete')).toBeVisible()

    // Step 4: Select policy pack
    await expect(page).toHaveURL('/onboarding/policy-pack')
    await page.click('text=Standard')
    await page.click('text=Continue')

    // Step 5: Confirm stage mappings
    await expect(page).toHaveURL('/onboarding/stage-mapping')
    await page.click('text=Confirm Mapping')

    // Step 6: First gate creation
    await expect(page).toHaveURL('/onboarding/first-gate')
    await expect(page.locator('text=Congratulations')).toBeVisible()

    // Go to dashboard
    await page.click('text=Go to Dashboard')
    await expect(page).toHaveURL('/dashboard')
  })

  test('should handle GitHub disconnection during flow')
  test('should handle analysis failure with retry')
  test('should allow back navigation')
  test('should persist progress on page refresh')
})
```

### Success Criteria
- [ ] Full onboarding E2E test passes
- [ ] Error states handled gracefully
- [ ] Progress persists across navigation
- [ ] Mobile responsive

---

## Onboarding Context Provider

**New File: OnboardingContext.tsx**

```typescript
interface OnboardingState {
  currentStep: number
  selectedRepo: GitHubRepository | null
  analysisResult: GitHubAnalysisResult | null
  policyPack: 'lite' | 'standard' | 'enterprise' | null
  stageMappings: Array<{ folder: string; stage: string }> | null
  createdProject: Project | null
  createdGate: GateResponse | null
}

interface OnboardingContextValue extends OnboardingState {
  setSelectedRepo: (repo: GitHubRepository) => void
  setAnalysisResult: (result: GitHubAnalysisResult) => void
  setPolicyPack: (pack: 'lite' | 'standard' | 'enterprise') => void
  setStageMappings: (mappings: Array<{ folder: string; stage: string }>) => void
  setCreatedProject: (project: Project) => void
  setCreatedGate: (gate: GateResponse) => void
  reset: () => void
}

export const OnboardingProvider: React.FC<{ children: React.ReactNode }> = () => {
  // Store state in sessionStorage for persistence
  // Clear on completion or manual reset
}
```

---

## Sprint Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| TTFGE (Time to First Gate) | <10 min | End-to-end timer |
| Onboarding Completion Rate | >80% | Analytics tracking |
| API Coverage (GitHub) | 100% | 11/11 endpoints |
| E2E Test Coverage | 100% | Full journey tested |

---

## Dependencies

| Dependency | Status | Notes |
|------------|--------|-------|
| Sprint 18 Complete | Required | Evidence integration |
| Sprint 19 Complete | Required | CRUD operations |
| GitHub OAuth | ✅ Ready | Backend complete |
| GitHub Types | ✅ Ready | Added to api.ts |

---

## Risk Assessment

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| GitHub rate limiting | Medium | High | Cache repo list, show warning |
| Analysis timeout | Low | Medium | Background job, polling |
| User abandonment | Medium | High | Progress saving, email reminder |

---

## Definition of Done

- [ ] Repository selection page complete
- [ ] Analysis page with progress
- [ ] Policy pack shows AI recommendation
- [ ] Stage mapping pre-populated
- [ ] First gate created automatically
- [ ] Full E2E test passes
- [ ] TTFGE < 10 minutes
- [ ] Mobile responsive
- [ ] Code review approved
- [ ] No P0/P1 bugs

---

*SDLC Orchestrator - First Governance-First Platform on SDLC 6.1.0. Zero Mock Policy enforced.*

**Sprint 20 Focus**: "Onboarding Excellence - From GitHub Connect to First Gate in under 10 minutes"
