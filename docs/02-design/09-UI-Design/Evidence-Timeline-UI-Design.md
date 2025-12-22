# Evidence Timeline UI Design
## Sprint 43 - AI Safety Layer Visibility Dashboard

---

**Document Information**

| Field | Value |
|-------|-------|
| **Document ID** | UID-043-001 |
| **Version** | 1.0.0 |
| **Status** | DRAFT |
| **Created** | 2025-12-22 |
| **Author** | Frontend Lead |
| **Sprint** | 43 |
| **Epic** | EP-02: AI Safety Layer v1 |

---

## 1. Overview

### 1.1 Purpose

The Evidence Timeline provides visibility into all AI detection events for a project. It allows team members to:
- View AI-generated PRs and their validation status
- Filter and search detection history
- Export evidence for audit purposes
- Request overrides for blocked PRs

### 1.2 User Stories

| ID | As a... | I want to... | So that... |
|----|---------|--------------|------------|
| US-01 | Developer | View my AI-assisted PRs | I can track my AI tool usage |
| US-02 | Tech Lead | See team's AI detection history | I can monitor AI adoption and quality |
| US-03 | Compliance Officer | Export evidence data | I can generate audit reports |
| US-04 | Developer | Request override for false positives | I can unblock my legitimate PR |
| US-05 | Admin | View override queue | I can approve/reject override requests |

---

## 2. Information Architecture

### 2.1 Page Structure

```
/projects/{id}/evidence
├── Header
│   ├── Page title: "AI Detection Evidence"
│   ├── Breadcrumb: Projects > {Project Name} > Evidence
│   └── Actions: Export, Filters toggle
│
├── Stats Bar
│   ├── Total Events
│   ├── AI Detected
│   ├── Validation Pass Rate
│   └── Override Rate
│
├── Filters Panel (collapsible)
│   ├── Date Range
│   ├── AI Tool
│   ├── Confidence Level
│   ├── Validation Status
│   └── Override Status
│
├── Timeline View
│   ├── Event Card (repeated)
│   │   ├── PR Title & Number
│   │   ├── AI Tool Badge
│   │   ├── Confidence Score
│   │   ├── Validation Results
│   │   ├── Timestamp
│   │   └── Actions (View, Override)
│   └── Load More (infinite scroll)
│
└── Empty State (when no events)
```

### 2.2 Navigation

```
Project Dashboard
      │
      ├── Overview
      ├── PRs
      ├── Gates
      ├── Evidence ◄── Current Page
      │     ├── Timeline (default)
      │     └── Export
      └── Settings
```

---

## 3. Wireframes

### 3.1 Main Timeline View

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ ← Projects / Acme Corp / Evidence                              [Export ▼]  │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐                     │
│  │   156    │  │   142    │  │  91.2%   │  │   2.1%   │                     │
│  │  Total   │  │    AI    │  │  Pass    │  │ Override │                     │
│  │  Events  │  │ Detected │  │  Rate    │  │   Rate   │                     │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘                     │
│                                                                              │
│  ┌─ Filters ─────────────────────────────────────────────────────────────┐  │
│  │                                                                        │  │
│  │  Date Range: [Last 7 days ▼]    AI Tool: [All ▼]    Status: [All ▼]  │  │
│  │                                                                        │  │
│  │  Confidence: [──────●──────] 50% - 100%            [Clear Filters]    │  │
│  │                                                                        │  │
│  └────────────────────────────────────────────────────────────────────────┘  │
│                                                                              │
│  ┌─ Timeline ────────────────────────────────────────────────────────────┐  │
│  │                                                                        │  │
│  │  ● Today                                                               │  │
│  │  │                                                                     │  │
│  │  │  ┌───────────────────────────────────────────────────────────────┐ │  │
│  │  ├──│ PR #234: Add user authentication with OAuth                   │ │  │
│  │  │  │                                                                │ │  │
│  │  │  │  🤖 Cursor    Confidence: 87%    ✅ Validated                  │ │  │
│  │  │  │                                                                │ │  │
│  │  │  │  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐               │ │  │
│  │  │  │  │ ✅ Lint │ │ ✅ Test │ │ ✅ Cov. │ │ ✅ SAST │               │ │  │
│  │  │  │  └─────────┘ └─────────┘ └─────────┘ └─────────┘               │ │  │
│  │  │  │                                                                │ │  │
│  │  │  │  2 hours ago by @john.doe                      [View Details] │ │  │
│  │  │  └───────────────────────────────────────────────────────────────┘ │  │
│  │  │                                                                     │  │
│  │  │  ┌───────────────────────────────────────────────────────────────┐ │  │
│  │  └──│ PR #233: Refactor payment service                             │ │  │
│  │     │                                                                │ │  │
│  │     │  🤖 Copilot   Confidence: 72%    ❌ Blocked                   │ │  │
│  │     │                                                                │ │  │
│  │     │  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐               │ │  │
│  │     │  │ ✅ Lint │ │ ❌ Test │ │ ⚠️ Cov. │ │ ✅ SAST │               │ │  │
│  │     │  └─────────┘ └─────────┘ └─────────┘ └─────────┘               │ │  │
│  │     │                                                                │ │  │
│  │     │  ⏳ Override Requested                                         │ │  │
│  │     │                                                                │ │  │
│  │     │  4 hours ago by @jane.smith       [View Details] [Override ▼] │ │  │
│  │     └───────────────────────────────────────────────────────────────┘ │  │
│  │                                                                        │  │
│  │  ● Yesterday                                                           │  │
│  │  │                                                                     │  │
│  │  │  ┌───────────────────────────────────────────────────────────────┐ │  │
│  │  └──│ PR #230: Update documentation                                 │ │  │
│  │     │                                                                │ │  │
│  │     │  🤖 Claude    Confidence: 95%    ✅ Validated                  │ │  │
│  │     │                                                                │ │  │
│  │     │  Yesterday at 3:45 PM by @mike.wilson        [View Details]   │ │  │
│  │     └───────────────────────────────────────────────────────────────┘ │  │
│  │                                                                        │  │
│  │                        [Loading more...]                               │  │
│  │                                                                        │  │
│  └────────────────────────────────────────────────────────────────────────┘  │
│                                                                              │
└──────────────────────────────────────────────────────────────────────────────┘
```

### 3.2 Event Detail Modal

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                                                                         [X] │
│  PR #234: Add user authentication with OAuth                                │
│  ────────────────────────────────────────────────────────────────────────── │
│                                                                              │
│  ┌─ Detection ─────────────────────────────────────────────────────────────┐│
│  │                                                                          ││
│  │  AI Tool:       🤖 Cursor                                               ││
│  │  Confidence:    ████████████████████░░░░  87%                           ││
│  │  Method:        Metadata + Commit + Pattern                             ││
│  │  Detected At:   Dec 22, 2025 at 10:32 AM                               ││
│  │                                                                          ││
│  │  Evidence:                                                               ││
│  │  ┌────────────────────────────────────────────────────────────────────┐ ││
│  │  │ • Title: "feat: implement auth with Cursor"                         │ ││
│  │  │ • Commit: "🤖 Generated with Cursor AI"                             │ ││
│  │  │ • Pattern: AI-style code patterns detected in 3 files               │ ││
│  │  └────────────────────────────────────────────────────────────────────┘ ││
│  │                                                                          ││
│  └──────────────────────────────────────────────────────────────────────────┘│
│                                                                              │
│  ┌─ Validation Results ────────────────────────────────────────────────────┐│
│  │                                                                          ││
│  │  Overall: ✅ PASSED                                                      ││
│  │                                                                          ││
│  │  ┌─────────────────────────────────────────────────────────────────────┐││
│  │  │ Validator      │ Status │ Duration │ Details                        │││
│  │  ├─────────────────────────────────────────────────────────────────────┤││
│  │  │ Lint           │ ✅     │ 45ms     │ 0 errors, 2 warnings           │││
│  │  │ Tests          │ ✅     │ 1.2s     │ 45/45 passed                   │││
│  │  │ Coverage       │ ✅     │ 890ms    │ 92% (threshold: 80%)           │││
│  │  │ SAST           │ ✅     │ 2.1s     │ No vulnerabilities             │││
│  │  │ Policy Guards  │ ✅     │ 120ms    │ 5/5 policies passed            │││
│  │  └─────────────────────────────────────────────────────────────────────┘││
│  │                                                                          ││
│  │  Total Duration: 4.3s                                                    ││
│  │                                                                          ││
│  └──────────────────────────────────────────────────────────────────────────┘│
│                                                                              │
│  ┌─ Override History ──────────────────────────────────────────────────────┐│
│  │                                                                          ││
│  │  No overrides for this event.                                           ││
│  │                                                                          ││
│  └──────────────────────────────────────────────────────────────────────────┘│
│                                                                              │
│  [View on GitHub]    [Export JSON]                              [Close]     │
│                                                                              │
└──────────────────────────────────────────────────────────────────────────────┘
```

### 3.3 Override Request Modal

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                                                                         [X] │
│  Request Override for PR #233                                               │
│  ────────────────────────────────────────────────────────────────────────── │
│                                                                              │
│  ⚠️ This PR was blocked due to failed validation.                           │
│                                                                              │
│  ┌─ Failed Validators ─────────────────────────────────────────────────────┐│
│  │                                                                          ││
│  │  ❌ Tests: 3 tests failed                                               ││
│  │     • test_payment_processing: AssertionError                           ││
│  │     • test_refund_logic: TimeoutError                                   ││
│  │     • test_webhook_handler: ConnectionError                             ││
│  │                                                                          ││
│  │  ⚠️ Coverage: 68% (below 80% threshold)                                  ││
│  │                                                                          ││
│  └──────────────────────────────────────────────────────────────────────────┘│
│                                                                              │
│  ┌─ Override Request ──────────────────────────────────────────────────────┐│
│  │                                                                          ││
│  │  Override Type: *                                                        ││
│  │  ┌────────────────────────────────────────────────────────────────────┐ ││
│  │  │ ○ False Positive - Detection or validation is incorrect            │ ││
│  │  │ ○ Approved Risk - Team accepts the risk                            │ ││
│  │  │ ○ Emergency - Critical hotfix that cannot wait                     │ ││
│  │  └────────────────────────────────────────────────────────────────────┘ ││
│  │                                                                          ││
│  │  Reason: *                                                               ││
│  │  ┌────────────────────────────────────────────────────────────────────┐ ││
│  │  │ The failing tests are for a feature that is not yet deployed.      │ ││
│  │  │ This PR only updates the payment service, which is tested          │ ││
│  │  │ separately. Coverage is temporarily low due to the new module      │ ││
│  │  │ but will be improved in the follow-up PR #235.                     │ ││
│  │  │                                                                     │ ││
│  │  │                                                            87/500   │ ││
│  │  └────────────────────────────────────────────────────────────────────┘ ││
│  │                                                                          ││
│  │  ℹ️ Minimum 50 characters required. Tech Lead+ approval needed.          ││
│  │                                                                          ││
│  └──────────────────────────────────────────────────────────────────────────┘│
│                                                                              │
│                                              [Cancel]    [Submit Request]    │
│                                                                              │
└──────────────────────────────────────────────────────────────────────────────┘
```

### 3.4 Admin Override Queue

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ ← Admin / Override Queue                                     3 Pending      │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌─ Pending Overrides ─────────────────────────────────────────────────────┐│
│  │                                                                          ││
│  │  ┌────────────────────────────────────────────────────────────────────┐ ││
│  │  │ PR #233 - Refactor payment service                                 │ ││
│  │  │                                                                     │ ││
│  │  │ Project: Acme Corp                                                 │ ││
│  │  │ Requested by: @jane.smith                                          │ ││
│  │  │ Type: Approved Risk                                                │ ││
│  │  │ Requested: 2 hours ago                                             │ ││
│  │  │                                                                     │ ││
│  │  │ Reason:                                                            │ ││
│  │  │ "The failing tests are for a feature that is not yet deployed..."  │ ││
│  │  │                                                                     │ ││
│  │  │ Failed Validators: Tests (3 failed), Coverage (68%)                │ ││
│  │  │                                                                     │ ││
│  │  │           [View PR]    [View Evidence]    [Reject]    [Approve]    │ ││
│  │  └────────────────────────────────────────────────────────────────────┘ ││
│  │                                                                          ││
│  │  ┌────────────────────────────────────────────────────────────────────┐ ││
│  │  │ PR #229 - Update dependency versions                               │ ││
│  │  │                                                                     │ ││
│  │  │ Project: NQH-Bot                                                   │ ││
│  │  │ Requested by: @alex.dev                                            │ ││
│  │  │ Type: False Positive                                               │ ││
│  │  │ Requested: 5 hours ago                                             │ ││
│  │  │                                                                     │ ││
│  │  │ Reason:                                                            │ ││
│  │  │ "This is a standard dependency update, not AI-generated code..."   │ ││
│  │  │                                                                     │ ││
│  │  │ AI Detection: Copilot (65% confidence)                             │ ││
│  │  │                                                                     │ ││
│  │  │           [View PR]    [View Evidence]    [Reject]    [Approve]    │ ││
│  │  └────────────────────────────────────────────────────────────────────┘ ││
│  │                                                                          ││
│  └──────────────────────────────────────────────────────────────────────────┘│
│                                                                              │
│  ┌─ Recent Decisions ──────────────────────────────────────────────────────┐│
│  │                                                                          ││
│  │  ✅ PR #225 approved by @tech.lead - 1 day ago                          ││
│  │  ❌ PR #221 rejected by @cto - 2 days ago (Reason: "Insufficient...")   ││
│  │  ✅ PR #218 approved by @tech.lead - 3 days ago                          ││
│  │                                                                          ││
│  │  [View All History →]                                                    ││
│  │                                                                          ││
│  └──────────────────────────────────────────────────────────────────────────┘│
│                                                                              │
└──────────────────────────────────────────────────────────────────────────────┘
```

---

## 4. Component Specifications

### 4.1 EvidenceTimeline Page

```typescript
// frontend/web/src/pages/EvidenceTimeline.tsx

interface EvidenceTimelineProps {
  projectId: string;
}

interface EvidenceFilters {
  dateRange: { start: Date; end: Date } | null;
  aiTool: AIToolType | null;
  confidenceRange: { min: number; max: number };
  validationStatus: 'passed' | 'failed' | 'pending' | null;
  overrideStatus: 'none' | 'pending' | 'approved' | 'rejected' | null;
}

// Features:
// - Infinite scroll with useInfiniteQuery
// - Real-time updates via WebSocket
// - URL-synced filters
// - Keyboard navigation (j/k for next/prev)
```

### 4.2 EventCard Component

```typescript
// frontend/web/src/components/evidence/EventCard.tsx

interface EventCardProps {
  event: EvidenceEvent;
  onViewDetails: () => void;
  onRequestOverride?: () => void;
}

// Visual states:
// - Default: White background
// - AI Detected + Passed: Green left border
// - AI Detected + Failed: Red left border
// - Override Pending: Yellow left border
// - Override Approved: Green left border with badge
```

### 4.3 Stats Bar Component

```typescript
// frontend/web/src/components/evidence/StatsBar.tsx

interface StatsBarProps {
  stats: {
    totalEvents: number;
    aiDetected: number;
    passRate: number;
    overrideRate: number;
  };
  loading?: boolean;
}

// Features:
// - Animated number transitions
// - Skeleton loading state
// - Responsive (stacks on mobile)
```

### 4.4 Filter Panel Component

```typescript
// frontend/web/src/components/evidence/FilterPanel.tsx

interface FilterPanelProps {
  filters: EvidenceFilters;
  onChange: (filters: EvidenceFilters) => void;
  onClear: () => void;
}

// Components:
// - DateRangePicker (last 7d, 30d, 90d, custom)
// - AIToolSelect (multi-select)
// - ConfidenceSlider (range slider)
// - StatusSelect (single select)
```

---

## 5. API Integration

### 5.1 Endpoints

```typescript
// frontend/web/src/api/evidence.ts

// GET /api/v1/projects/{id}/evidence
interface GetEvidenceParams {
  page?: number;
  limit?: number;
  dateStart?: string;
  dateEnd?: string;
  aiTool?: string;
  confidenceMin?: number;
  confidenceMax?: number;
  validationStatus?: string;
  overrideStatus?: string;
}

interface GetEvidenceResponse {
  events: EvidenceEvent[];
  total: number;
  page: number;
  pages: number;
}

// GET /api/v1/projects/{id}/evidence/{eventId}
interface GetEvidenceDetailResponse extends EvidenceEvent {
  validationResults: ValidatorResult[];
  overrideHistory: EvidenceOverride[];
  rawEvidence: Record<string, unknown>;
}

// POST /api/v1/evidence/{eventId}/override/request
interface RequestOverrideBody {
  overrideType: 'false_positive' | 'approved_risk' | 'emergency';
  reason: string;
}

// GET /api/v1/projects/{id}/evidence/export
interface ExportParams {
  format: 'csv' | 'json';
  dateStart?: string;
  dateEnd?: string;
}
```

### 5.2 React Query Hooks

```typescript
// frontend/web/src/hooks/useEvidence.ts

export function useEvidenceTimeline(projectId: string, filters: EvidenceFilters) {
  return useInfiniteQuery({
    queryKey: ['evidence', projectId, filters],
    queryFn: ({ pageParam = 1 }) => getEvidence(projectId, { ...filters, page: pageParam }),
    getNextPageParam: (lastPage) =>
      lastPage.page < lastPage.pages ? lastPage.page + 1 : undefined,
    staleTime: 30_000, // 30 seconds
  });
}

export function useEvidenceDetail(projectId: string, eventId: string) {
  return useQuery({
    queryKey: ['evidence', projectId, eventId],
    queryFn: () => getEvidenceDetail(projectId, eventId),
    staleTime: 60_000, // 1 minute
  });
}

export function useRequestOverride() {
  return useMutation({
    mutationFn: ({ eventId, body }: { eventId: string; body: RequestOverrideBody }) =>
      requestOverride(eventId, body),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['evidence'] });
      toast.success('Override request submitted');
    },
  });
}
```

---

## 6. Accessibility

### 6.1 Requirements

| Requirement | Implementation |
|-------------|----------------|
| Keyboard navigation | j/k for prev/next, Enter for details |
| Screen reader support | ARIA labels, live regions for updates |
| Color contrast | WCAG 2.1 AA (4.5:1 minimum) |
| Focus management | Focus trap in modals, skip links |
| Responsive design | Mobile-first, touch-friendly |

### 6.2 ARIA Labels

```html
<section aria-label="AI Detection Evidence Timeline">
  <div role="feed" aria-busy="false">
    <article
      role="article"
      aria-label="PR #234: Add user authentication, detected Cursor with 87% confidence, validated"
    >
      ...
    </article>
  </div>
</section>
```

---

## 7. Performance

### 7.1 Optimization Strategies

| Strategy | Implementation |
|----------|----------------|
| Virtual scrolling | react-window for 1000+ events |
| Image lazy loading | Intersection Observer for avatars |
| Query caching | React Query with 30s stale time |
| Code splitting | Lazy load detail modal |
| Skeleton loading | Show skeleton while loading |

### 7.2 Performance Budgets

| Metric | Target |
|--------|--------|
| First Contentful Paint | < 1s |
| Time to Interactive | < 2s |
| Largest Contentful Paint | < 2.5s |
| Cumulative Layout Shift | < 0.1 |

---

## 8. Testing

### 8.1 Unit Tests

```typescript
// frontend/web/src/pages/__tests__/EvidenceTimeline.test.tsx

describe('EvidenceTimeline', () => {
  it('renders empty state when no events', async () => {
    // ...
  });

  it('filters events by date range', async () => {
    // ...
  });

  it('opens detail modal on event click', async () => {
    // ...
  });

  it('submits override request', async () => {
    // ...
  });
});
```

### 8.2 E2E Tests

```typescript
// frontend/web/e2e/evidence-timeline.spec.ts

test('complete evidence timeline flow', async ({ page }) => {
  // 1. Navigate to evidence page
  await page.goto('/projects/123/evidence');

  // 2. Verify stats displayed
  await expect(page.getByText('Total Events')).toBeVisible();

  // 3. Apply filter
  await page.getByRole('combobox', { name: 'AI Tool' }).click();
  await page.getByRole('option', { name: 'Cursor' }).click();

  // 4. Open event detail
  await page.getByRole('article').first().click();

  // 5. Verify modal content
  await expect(page.getByRole('dialog')).toBeVisible();

  // 6. Export data
  await page.getByRole('button', { name: 'Export' }).click();
  await page.getByRole('menuitem', { name: 'Export as CSV' }).click();
});
```

---

## 9. Design Tokens

### 9.1 Colors

```css
/* AI Tool Colors */
--color-ai-cursor: #00A3FF;
--color-ai-copilot: #6E40C9;
--color-ai-claude: #CC785C;
--color-ai-chatgpt: #10A37F;
--color-ai-other: #6B7280;

/* Status Colors */
--color-status-passed: #10B981;
--color-status-failed: #EF4444;
--color-status-pending: #F59E0B;
--color-status-skipped: #6B7280;

/* Override Colors */
--color-override-pending: #F59E0B;
--color-override-approved: #10B981;
--color-override-rejected: #EF4444;
```

### 9.2 Typography

```css
/* Event Card */
--font-event-title: 600 16px/1.4 'Inter', sans-serif;
--font-event-meta: 400 14px/1.4 'Inter', sans-serif;
--font-event-badge: 500 12px/1 'Inter', sans-serif;

/* Stats */
--font-stat-value: 700 24px/1.2 'Inter', sans-serif;
--font-stat-label: 400 12px/1.4 'Inter', sans-serif;
```

---

## 10. Changelog

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0.0 | 2025-12-22 | Frontend Lead | Initial design |

---

**Approvals**

| Role | Name | Date | Status |
|------|------|------|--------|
| CTO | | | PENDING |
| Frontend Lead | | | PENDING |
| UX Designer | | | PENDING |
