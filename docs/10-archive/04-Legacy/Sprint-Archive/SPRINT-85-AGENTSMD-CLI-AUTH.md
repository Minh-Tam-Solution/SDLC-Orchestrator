# Sprint 85: AGENTS.md UI + CLI Authentication

**Sprint ID:** S85
**Status:** ✅ **CTO APPROVED** (January 20, 2026)
**Duration:** 10 days (February 1 - February 11, 2026)
**Goal:** Implement AGENTS.md frontend (TRUE MOAT) + CLI authentication foundation
**Story Points:** 55 SP
**Framework Reference:** SDLC 6.1.0 P2 (Sprint Planning Governance)
**Prerequisite:** Sprint 84 ✅ Teams & Organizations UI
**Target:** AGENTS.md Differentiator + CLI Foundation

---

## Executive Summary

### Strategic Importance

| Feature | Business Value | Priority |
|---------|---------------|----------|
| **AGENTS.md UI** | TRUE MOAT differentiator - 60K+ repos use static, we make it dynamic | **P0** |
| **CLI Authentication** | Developer productivity - work from terminal | **P1** |
| **CLI Evidence Upload** | 40% of developers prefer CLI for evidence | **P1** |

**Sprint 85 Target:**
- AGENTS.md: **100% API coverage** (13 endpoints → 4 pages)
- CLI: **Authentication + Evidence** foundation (9 commands)

---

## 🎯 Sprint 85 Objectives

### Primary Goals (P0 - TRUE MOAT)

1. **AGENTS.md Multi-Repo Dashboard** - View all repos with AGENTS.md status
2. **AGENTS.md Editor** - Generate, validate, edit AGENTS.md files
3. **Dynamic Context Viewer** - Real-time context overlay visualization
4. **Analytics Dashboard** - Engagement metrics, update frequency

### Secondary Goals (P1 - CLI Foundation)

5. **CLI Authentication** - `sdlcctl auth login` (OAuth + API Key)
6. **CLI Project Commands** - `sdlcctl project list/select`
7. **CLI Evidence Upload** - `sdlcctl evidence upload`
8. **CLI Context Command** - `sdlcctl context show`

---

## 📋 Sprint 85 Backlog

### Day 1-2: AGENTS.md API Hooks (8 SP)

| Task | Owner | Est | Priority | Status |
|------|-------|-----|----------|--------|
| Create `useAgentsMd.ts` hook | Frontend | 4h | P0 | ⏳ |
| Create `useContextOverlay.ts` hook | Frontend | 3h | P0 | ⏳ |
| Create `useAgentsMdAnalytics.ts` hook | Frontend | 3h | P0 | ⏳ |
| Define TypeScript interfaces | Frontend | 2h | P0 | ⏳ |
| Unit tests for hooks (12 tests) | Frontend | 3h | P0 | ⏳ |

**Files to Create:**

```
frontend/src/hooks/useAgentsMd.ts
frontend/src/hooks/useContextOverlay.ts
frontend/src/hooks/useAgentsMdAnalytics.ts
frontend/src/lib/types/agents-md.ts
```

**Hook API Reference:**

```typescript
// useAgentsMd.ts
export function useAgentsMdRepos() {
  // GET /agents-md/repos - List repos with AGENTS.md status
  // Returns: { repos, isLoading, error }
}

export function useAgentsMdRepo(repoId: string) {
  // GET /agents-md/{repo_id} - Get repo detail
  // Returns: { repo, isLoading, error }
}

export function useRegenerateAgentsMd(repoId: string) {
  // POST /agents-md/{repo_id}/regenerate - Regenerate file
  // Returns: { regenerate, isLoading, error }
}

export function useBulkRegenerate() {
  // POST /agents-md/bulk/regenerate - Bulk regenerate
  // Returns: { bulkRegenerate, isLoading, error }
}

export function useAgentsMdDiff(repoId: string) {
  // GET /agents-md/{repo_id}/diff - Get version diff
  // Returns: { diff, isLoading, error }
}

export function useValidateAgentsMd() {
  // POST /agents-md/validate - Validate content
  // Returns: { validate, isLoading, error }
}

// useContextOverlay.ts
export function useContextOverlay(projectId: string) {
  // GET /agents-md/{repo_id}/context - Get dynamic context
  // Returns: { context, isLoading, error }
}

export function useContextHistory(projectId: string) {
  // GET /context-overlays/project/{project_id}/history
  // Returns: { history, isLoading, error }
}

// useAgentsMdAnalytics.ts
export function useOverlayMetrics() {
  // GET /analytics/overlay - Overlay metrics
  // Returns: { metrics, isLoading, error }
}

export function useEngagementMetrics() {
  // GET /analytics/engagement - Engagement metrics
  // Returns: { metrics, isLoading, error }
}

export function useAnalyticsSummary() {
  // GET /analytics/summary - Complete summary
  // Returns: { summary, isLoading, error }
}

export function useAnalyticsTimeSeries(metric: string) {
  // GET /analytics/time-series/{metric} - Time series data
  // Returns: { data, isLoading, error }
}

export function useExportAnalytics(format: 'json' | 'csv') {
  // GET /analytics/export - Export data
  // Returns: { exportData, isLoading, error }
}
```

---

### Day 3-5: AGENTS.md UI Pages (21 SP)

| Task | Owner | Est | Priority | Status |
|------|-------|-----|----------|--------|
| Create AGENTS.md dashboard page | Frontend | 6h | P0 | ⏳ |
| Create AGENTS.md repo detail page | Frontend | 6h | P0 | ⏳ |
| Create AGENTS.md editor component | Frontend | 6h | P0 | ⏳ |
| Create diff viewer component | Frontend | 4h | P0 | ⏳ |
| Create context overlay panel | Frontend | 4h | P0 | ⏳ |
| Create analytics charts | Frontend | 6h | P1 | ⏳ |
| Create bulk actions toolbar | Frontend | 3h | P1 | ⏳ |
| Loading states & skeletons | Frontend | 2h | P0 | ⏳ |
| Error handling & toasts | Frontend | 2h | P0 | ⏳ |

**Files to Create:**

```
frontend/src/app/app/agents-md/
├── page.tsx                      # Multi-repo dashboard
├── [repoId]/
│   └── page.tsx                  # Repo detail + editor
├── analytics/
│   └── page.tsx                  # Analytics dashboard
└── components/
    ├── RepoCard.tsx              # Repo status card
    ├── RepoTable.tsx             # Table view
    ├── AgentsMdEditor.tsx        # Monaco editor
    ├── DiffViewer.tsx            # Side-by-side diff
    ├── ContextOverlayPanel.tsx   # Dynamic context display
    ├── BulkActionsBar.tsx        # Bulk regenerate
    ├── ValidationStatus.tsx      # Valid/Invalid badge
    ├── AnalyticsChart.tsx        # Recharts wrapper
    └── MetricsCards.tsx          # Stats cards
```

**UI Specifications:**

```
AGENTS.md Dashboard (/app/agents-md):
┌─────────────────────────────────────────────────────────────────────┐
│ AGENTS.md Management                    [Bulk Regenerate] [Export]  │
├─────────────────────────────────────────────────────────────────────┤
│ Metrics Overview                                                    │
│ ┌───────────┐ ┌───────────┐ ┌───────────┐ ┌───────────┐            │
│ │ 24        │ │ 18        │ │ 5         │ │ 98.2%     │            │
│ │ Total     │ │ Up to     │ │ Outdated  │ │ Valid     │            │
│ │ Repos     │ │ Date      │ │ Files     │ │ Rate      │            │
│ └───────────┘ └───────────┘ └───────────┘ └───────────┘            │
├─────────────────────────────────────────────────────────────────────┤
│ [🔲] Repository        │ Status   │ Last Updated │ Actions         │
│ ─────────────────────────────────────────────────────────────────── │
│ [🔲] sdlc-orchestrator │ ✅ Valid │ 2h ago       │ [View] [Regen]  │
│ [🔲] bflow-platform    │ ⚠️ Outdated│ 5d ago     │ [View] [Regen]  │
│ [🔲] nqh-crm           │ ❌ Missing│ Never       │ [Generate]      │
└─────────────────────────────────────────────────────────────────────┘

AGENTS.md Detail (/app/agents-md/[repoId]):
┌─────────────────────────────────────────────────────────────────────┐
│ ← Back   sdlc-orchestrator/AGENTS.md       [Edit] [Regenerate]     │
├────────────────────────────────┬────────────────────────────────────┤
│ AGENTS.md Content              │ Dynamic Context (Live)             │
│ ┌────────────────────────────┐ │ ┌────────────────────────────────┐ │
│ │ # AGENTS.md                │ │ │ ## Current Stage               │ │
│ │                            │ │ │ ✅ Gate: G3 | Status: PASSED   │ │
│ │ ## Quick Start             │ │ │                                │ │
│ │ - Full stack: docker up    │ │ │ ## Current Sprint              │ │
│ │ - Backend: pytest          │ │ │ Sprint 85 | AGENTS.md + CLI    │ │
│ │                            │ │ │                                │ │
│ │ ## Architecture            │ │ │ ## ⚠️ Known Issues            │ │
│ │ 5-layer: AI → EP-06 →...   │ │ │ - Pending: Team UI tests      │ │
│ │                            │ │ │                                │ │
│ │ ## Conventions             │ │ │ ## 🔒 Constraints             │ │
│ │ - Python: snake_case       │ │ │ - No new features (G3 passed) │ │
│ │ - TypeScript: camelCase    │ │ └────────────────────────────────┘ │
│ └────────────────────────────┘ │                                    │
├────────────────────────────────┴────────────────────────────────────┤
│ Version History                                          [View Diff]│
│ ┌─────────────────────────────────────────────────────────────────┐ │
│ │ v3 (current) │ Jan 20, 2026 │ Auto-update: Gate G3 passed      │ │
│ │ v2           │ Jan 18, 2026 │ Sprint change: Sprint 85 started │ │
│ │ v1           │ Jan 15, 2026 │ Initial generation               │ │
│ └─────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────┘
```

---

### Day 6-7: CLI Authentication & Core Commands (13 SP)

| Task | Owner | Est | Priority | Status |
|------|-------|-----|----------|--------|
| Implement `sdlcctl auth login` (OAuth) | Backend | 6h | P1 | ⏳ |
| Implement `sdlcctl auth login --api-key` | Backend | 3h | P1 | ⏳ |
| Implement `sdlcctl auth logout` | Backend | 2h | P1 | ⏳ |
| Implement `sdlcctl auth status` | Backend | 2h | P1 | ⏳ |
| Implement `sdlcctl project list` | Backend | 3h | P1 | ⏳ |
| Implement `sdlcctl project select` | Backend | 3h | P1 | ⏳ |
| Config file management (~/.sdlcctl/config.yaml) | Backend | 3h | P1 | ⏳ |
| Unit tests (15 tests) | Backend | 4h | P1 | ⏳ |

**Files to Create:**

```
cli/
├── sdlcctl/
│   ├── __init__.py
│   ├── __main__.py
│   ├── cli.py                    # Main CLI entry point
│   ├── commands/
│   │   ├── __init__.py
│   │   ├── auth.py               # auth login/logout/status
│   │   ├── project.py            # project list/select
│   │   ├── evidence.py           # evidence upload/list
│   │   └── context.py            # context show
│   ├── config/
│   │   ├── __init__.py
│   │   └── settings.py           # Config file management
│   ├── api/
│   │   ├── __init__.py
│   │   └── client.py             # API client wrapper
│   └── utils/
│       ├── __init__.py
│       ├── auth.py               # OAuth device flow
│       └── output.py             # Rich console output
├── pyproject.toml                # CLI package config
└── tests/
    └── test_cli.py               # CLI tests
```

**CLI Command Reference:**

```bash
# Authentication
sdlcctl auth login              # OAuth device flow (opens browser)
sdlcctl auth login --api-key    # API key authentication
sdlcctl auth logout             # Clear stored credentials
sdlcctl auth status             # Show current auth status

# Project Management
sdlcctl project list            # List accessible projects
sdlcctl project select <id>     # Set active project
sdlcctl project info            # Show current project info

# Evidence (Day 8-9)
sdlcctl evidence upload <file>  # Upload evidence file
sdlcctl evidence list           # List project evidence
sdlcctl evidence download <id>  # Download evidence

# Context (Day 8-9)
sdlcctl context show            # Show current dynamic context
sdlcctl context history         # Show context history
```

**OAuth Device Flow:**

```
$ sdlcctl auth login
🔐 SDLC Orchestrator CLI Authentication

Please visit: https://app.sdlc-orchestrator.com/cli/auth
Enter code: ABCD-1234

Waiting for authorization... ⏳

✅ Successfully authenticated as john@example.com
   Organization: NQH Holdings
   Projects: 5 accessible

Configuration saved to ~/.sdlcctl/config.yaml
```

---

### Day 8-9: CLI Evidence & Context Commands (8 SP)

| Task | Owner | Est | Priority | Status |
|------|-------|-----|----------|--------|
| Implement `sdlcctl evidence upload` | Backend | 4h | P1 | ⏳ |
| Implement `sdlcctl evidence list` | Backend | 2h | P1 | ⏳ |
| Implement `sdlcctl evidence download` | Backend | 2h | P1 | ⏳ |
| Implement `sdlcctl context show` | Backend | 3h | P1 | ⏳ |
| Implement `sdlcctl context history` | Backend | 2h | P1 | ⏳ |
| Progress bar for uploads | Backend | 2h | P1 | ⏳ |
| Unit tests (10 tests) | Backend | 3h | P1 | ⏳ |

**Evidence Upload Example:**

```
$ sdlcctl evidence upload ./test-results.xml --type test_report --gate G2

📤 Uploading evidence to SDLC Orchestrator

File: test-results.xml (2.4 MB)
Type: test_report
Gate: G2
Project: sdlc-orchestrator

Uploading... ████████████████████ 100% (2.4/2.4 MB)

✅ Evidence uploaded successfully!
   Evidence ID: ev_abc123def456
   SHA256: 5d41402abc4b2a76b9719d911017c592
   Status: pending_review

View at: https://app.sdlc-orchestrator.com/evidence/ev_abc123def456
```

**Context Show Example:**

```
$ sdlcctl context show

🎯 Dynamic Context for sdlc-orchestrator

┌─────────────────────────────────────────────────────────┐
│ Current Stage                                           │
│ ─────────────────────────────────────────────────────── │
│ Gate: G3 (Ship Ready)                                   │
│ Status: ✅ PASSED                                       │
│ Passed: January 18, 2026                                │
├─────────────────────────────────────────────────────────┤
│ Current Sprint                                          │
│ ─────────────────────────────────────────────────────── │
│ Sprint: 85 - AGENTS.md + CLI                            │
│ Status: 🔄 IN_PROGRESS                                  │
│ Goals:                                                  │
│   • AGENTS.md frontend implementation                   │
│   • CLI authentication foundation                       │
├─────────────────────────────────────────────────────────┤
│ Constraints                                             │
│ ─────────────────────────────────────────────────────── │
│ 🔒 Post-G3 Mode: Bug fixes only, no new features       │
│ ⚠️ Pending: Team UI integration tests                  │
└─────────────────────────────────────────────────────────┘

Last updated: 5 minutes ago
```

---

### Day 10: Testing & Integration (5 SP)

| Task | Owner | Est | Priority | Status |
|------|-------|-----|----------|--------|
| E2E tests for AGENTS.md flow | QA | 4h | P0 | ⏳ |
| E2E tests for CLI authentication | QA | 3h | P1 | ⏳ |
| CLI integration tests | QA | 3h | P1 | ⏳ |
| Update Sidebar navigation | Frontend | 1h | P0 | ⏳ |
| Documentation (CLI README) | Backend | 2h | P1 | ⏳ |

**Sidebar Update:**

```tsx
// frontend/src/components/dashboard/Sidebar.tsx

const navigation = [
  { name: "Dashboard", href: "/app", icon: LayoutDashboard },
  { name: "Projects", href: "/app/projects", icon: FolderKanban },
  { name: "Gates", href: "/app/gates", icon: ShieldCheck },
  { name: "Evidence", href: "/app/evidence", icon: FileText },
  { name: "Policies", href: "/app/policies", icon: ScrollText },
  { name: "Teams", href: "/app/teams", icon: Users },  // Sprint 84
  { name: "Organizations", href: "/app/organizations", icon: Building2 },  // Sprint 84
  // NEW: Sprint 85
  { name: "AGENTS.md", href: "/app/agents-md", icon: Bot },
  // END NEW
  { name: "App Builder", href: "/app/codegen", icon: Code2 },
  { name: "SOP Generator", href: "/app/sop-generator", icon: FileCode2 },
  { name: "Settings", href: "/app/settings", icon: Settings },
];
```

---

## 🔧 Technical Specifications

### API Endpoints Used (AGENTS.md)

| Method | Endpoint | Hook Function |
|--------|----------|---------------|
| GET | `/agents-md/repos` | `useAgentsMdRepos().repos` |
| GET | `/agents-md/{repo_id}` | `useAgentsMdRepo(id).repo` |
| POST | `/agents-md/{repo_id}/regenerate` | `useRegenerateAgentsMd(id).regenerate()` |
| POST | `/agents-md/bulk/regenerate` | `useBulkRegenerate().bulkRegenerate()` |
| GET | `/agents-md/{repo_id}/diff` | `useAgentsMdDiff(id).diff` |
| POST | `/agents-md/validate` | `useValidateAgentsMd().validate()` |
| GET | `/agents-md/{repo_id}/context` | `useContextOverlay(id).context` |
| GET | `/analytics/overlay` | `useOverlayMetrics().metrics` |
| GET | `/analytics/engagement` | `useEngagementMetrics().metrics` |
| GET | `/analytics/summary` | `useAnalyticsSummary().summary` |
| GET | `/analytics/time-series/{metric}` | `useAnalyticsTimeSeries(m).data` |
| GET | `/analytics/export` | `useExportAnalytics(f).exportData()` |
| GET | `/analytics/projects/{id}` | `useProjectAnalytics(id).analytics` |

### TypeScript Interfaces

```typescript
// frontend/src/lib/types/agents-md.ts

export type ValidationStatus = "pending" | "valid" | "invalid";
export type TriggerType = "pr_webhook" | "cli" | "api" | "scheduled" | "manual";

export interface AgentsMdRepo {
  id: string;
  project_id: string;
  project_name: string;
  github_repo_full_name: string;
  has_agents_md: boolean;
  last_generated_at?: string;
  validation_status: ValidationStatus;
  line_count?: number;
  sections?: string[];
  is_outdated: boolean;
}

export interface AgentsMdFile {
  id: string;
  project_id: string;
  content: string;
  content_hash: string;
  line_count: number;
  sections: string[];
  generated_at: string;
  generated_by?: string;
  generator_version: string;
  validation_status: ValidationStatus;
  validation_errors?: ValidationError[];
  validation_warnings?: ValidationWarning[];
}

export interface ValidationError {
  line?: number;
  message: string;
  severity: "error";
}

export interface ValidationWarning {
  line?: number;
  message: string;
  severity: "warning";
}

export interface ContextOverlay {
  id: string;
  project_id: string;
  generated_at: string;
  stage_name?: string;
  gate_status?: string;
  sprint?: {
    id?: string;
    number?: number;
    goal?: string;
  };
  constraints: Constraint[];
  strict_mode: boolean;
  trigger_type: TriggerType;
  trigger_ref?: string;
  delivered_to_pr: boolean;
  delivered_to_check_run: boolean;
}

export interface Constraint {
  type: string;
  severity: "critical" | "high" | "medium" | "low";
  message: string;
  source?: string;
}

export interface AgentsMdDiff {
  old_version: string;
  new_version: string;
  old_content: string;
  new_content: string;
  changes: DiffChange[];
}

export interface DiffChange {
  type: "added" | "removed" | "modified";
  line_number: number;
  old_line?: string;
  new_line?: string;
}

export interface OverlayMetrics {
  total_overlays: number;
  overlays_by_trigger: Record<TriggerType, number>;
  avg_overlays_per_project: number;
  strict_mode_activations: number;
}

export interface EngagementMetrics {
  total_updates: number;
  updates_by_type: Record<string, number>;
  active_projects: number;
  avg_updates_per_day: number;
}

export interface AnalyticsSummary {
  overlay: OverlayMetrics;
  engagement: EngagementMetrics;
  gates: {
    total: number;
    passed: number;
    failed: number;
    pass_rate: number;
  };
  security: {
    scans_total: number;
    scans_passed: number;
    scans_failed: number;
  };
}
```

### CLI Configuration

```yaml
# ~/.sdlcctl/config.yaml

version: 1
api:
  base_url: https://api.sdlc-orchestrator.com
  timeout: 30

auth:
  type: oauth  # oauth | api_key
  access_token: eyJhbGc...
  refresh_token: eyJhbGc...
  expires_at: 2026-02-01T12:00:00Z

project:
  current_id: proj_abc123
  current_name: sdlc-orchestrator

preferences:
  output_format: table  # table | json | yaml
  color: true
  verbose: false
```

---

## 📊 Success Criteria

| Metric | Target | Verification |
|--------|--------|--------------|
| AGENTS.md dashboard working | ✅ | E2E tests pass |
| AGENTS.md editor working | ✅ | E2E tests pass |
| Context overlay display | ✅ | E2E tests pass |
| Analytics charts rendering | ✅ | Visual QA |
| CLI auth login working | ✅ | Integration tests |
| CLI evidence upload working | ✅ | Integration tests |
| CLI context show working | ✅ | Integration tests |
| API coverage (AGENTS.md) | 100% | All 13 endpoints used |
| CLI commands | 9 commands | All working |
| Unit test coverage | >80% | Jest/pytest coverage |

---

## 🚀 Deployment Plan

### Pre-deployment Checklist

- [ ] All E2E tests passing
- [ ] All CLI integration tests passing
- [ ] Lighthouse score >90
- [ ] Code review approved (2+ reviewers)
- [ ] No TypeScript errors
- [ ] CLI packaged and tested

### CLI Distribution

```bash
# PyPI installation
pip install sdlcctl

# Homebrew (macOS)
brew install sdlcctl

# Direct download
curl -sSL https://get.sdlc-orchestrator.com/cli | bash
```

---

## 📝 Dependencies

### Backend Dependencies (Already Implemented ✅)

- AGENTS.md API: 13 endpoints (Sprint 80)
- Dynamic Context API: 6 endpoints (Sprint 83)
- Analytics API: 6 endpoints (Sprint 83)
- Evidence Vault API: 8 endpoints (Sprint 45)

### Frontend Dependencies

- Monaco Editor (code editor) ✅
- shadcn/ui components ✅
- TanStack Query v5 ✅
- Recharts (analytics) ✅

### CLI Dependencies

- Typer (CLI framework)
- Rich (terminal formatting)
- httpx (async HTTP client)
- keyring (secure credential storage)
- PyYAML (config files)

---

## ⚠️ Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Monaco Editor bundle size | Medium | Lazy load, code splitting |
| OAuth device flow complexity | Medium | Use proven library (authlib) |
| CLI cross-platform issues | Medium | Test on macOS, Linux, Windows |
| Analytics chart performance | Low | Virtualize large datasets |

---

## 📅 Timeline Summary

| Day | Focus | Deliverables |
|-----|-------|-------------|
| 1-2 | API Hooks | useAgentsMd.ts, useContextOverlay.ts, useAnalytics.ts |
| 3-5 | AGENTS.md UI | Dashboard, editor, diff viewer, analytics |
| 6-7 | CLI Auth | auth login/logout/status, project list/select |
| 8-9 | CLI Commands | evidence upload/list, context show |
| 10 | Testing | E2E tests, integration tests, documentation |

---

## Approval

- [ ] **CTO Approval**: Technical scope and architecture
- [ ] **CPO Approval**: UX/UI specifications
- [ ] **Backend Lead Approval**: CLI architecture
- [ ] **Frontend Lead Approval**: Implementation approach

---

**Sprint Owner:** Frontend Lead + Backend Lead
**Reviewers:** CTO, CPO
**Created:** January 20, 2026
**Last Updated:** January 20, 2026
