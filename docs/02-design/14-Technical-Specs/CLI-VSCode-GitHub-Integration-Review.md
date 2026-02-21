# Sprint 81 Design Review Report

**Document ID:** DRR-081-001
**Date:** January 19, 2026
**Author:** Backend Lead
**Status:** CTO REVIEW REQUIRED
**Sprint:** 81 (Feb 17-28, 2026)

---

## 1. Executive Summary

Báo cáo này review kỹ các thiết kế hiện có về CLI, VS Code Extension, và GitHub Integration trước khi thực hiện Sprint 81. Mục đích là identify **gaps**, **inconsistencies**, và **risks** cần giải quyết.

### 1.1 Key Findings

| Component | Current State | Sprint 81 Readiness | Action Required |
|-----------|---------------|---------------------|-----------------|
| **CLI (sdlcctl)** | ✅ Production (207 tests, 95% coverage) | ✅ Ready | Minor: Add `agents context` |
| **VS Code Extension** | ⚠️ Design Only (Sprint 53) | ⚠️ Partial | Need: Context Panel design |
| **GitHub Integration** | ✅ Production (OAuth + Webhooks) | ⚠️ Partial | Need: Check Runs API |

### 1.2 Critical Gaps Identified

1. **GitHub Check Runs API**: NOT implemented - cần cho Sprint 81
2. **VS Code Context Panel**: NOT designed - Sprint 53 focus App Builder, không có SDLC Context
3. **GitHub App**: OAuth exists, but GitHub App (for Check Runs) NOT configured
4. **Webhook → Check Run flow**: NOT designed

---

## 2. CLI Architecture Review

### 2.1 Current Implementation (Sprint 14-29)

**Location:** `backend/sdlcctl/`

**Commands Implemented:**

| Command | Purpose | Status | Coverage |
|---------|---------|--------|----------|
| `sdlcctl validate` | Validate SDLC folder structure | ✅ Production | 95% |
| `sdlcctl fix` | Auto-fix missing artifacts | ✅ Production | 95% |
| `sdlcctl init` | Initialize SDLC project | ✅ Production | 95% |
| `sdlcctl report` | Generate compliance report | ✅ Production | 95% |
| `sdlcctl tiers` | Show tier definitions | ✅ Production | 95% |
| `sdlcctl stages` | Show stage definitions | ✅ Production | 95% |
| `sdlcctl generate` | Generate from AppBlueprint | ✅ Production | 90% |
| `sdlcctl magic` | NLP → code generation | ✅ Production | 90% |
| `sdlcctl agents init` | Generate AGENTS.md | ✅ Sprint 80 | NEW |
| `sdlcctl agents validate` | Validate AGENTS.md | ✅ Sprint 80 | NEW |
| `sdlcctl agents lint` | Lint AGENTS.md | ✅ Sprint 80 | NEW |

**Architecture Pattern:**

```
sdlcctl/
├── cli.py                     # Main Typer app
├── commands/
│   ├── validate.py            # Validation command
│   ├── fix.py                 # Auto-fix command
│   ├── init.py                # Project init
│   ├── report.py              # Report generation
│   ├── generate.py            # AppBlueprint → code
│   ├── magic.py               # NLP → code
│   ├── migrate.py             # Migration helpers
│   └── agents.py              # AGENTS.md commands (Sprint 80)
├── validation/
│   ├── engine.py              # Core validation engine
│   ├── scanner.py             # Folder scanner
│   └── validators/            # Rule validators
└── schemas/
    └── sdlc-config.schema.json
```

### 2.2 Sprint 81 CLI Requirements

**New Command Needed:** `sdlcctl agents context`

```python
# Proposed: backend/sdlcctl/commands/agents.py (addition)

@agents_app.command(name="context")
def agents_context_command(
    project_id: Optional[str] = typer.Option(None, "--project", "-p"),
    format: str = typer.Option("cli", "--format", "-f"),
) -> None:
    """Fetch and display current SDLC context overlay."""
```

**Gap Analysis:**

| Feature | Current | Sprint 81 Need | Gap |
|---------|---------|----------------|-----|
| `agents init` | ✅ | ✅ | None |
| `agents validate` | ✅ | ✅ | None |
| `agents lint` | ✅ | ✅ | None |
| `agents context` | ❌ | ✅ | **NEW** |

**Effort:** 2 SP (2 hours)

---

## 3. VS Code Extension Review

### 3.1 Current Design (Sprint 53 Specification)

**Document:** `docs/02-design/14-Technical-Specs/VSCode-Extension-Specification.md`

**Focus Areas:**
- App Builder Panel (code generation)
- Magic Mode (NLP → code)
- Contract Lock (spec immutability)
- SSE Streaming (real-time file generation)

### 3.2 Sprint 81 Requirements vs Sprint 53 Design

| Sprint 81 Need | Sprint 53 Coverage | Gap |
|----------------|-------------------|-----|
| **Context Panel** (SDLC stage/gate/constraints) | ❌ NOT covered | **NEW DESIGN REQUIRED** |
| **Status Bar** (stage indicator) | ⚠️ Partial (generation status) | Extend existing |
| **Auto-refresh** (30s interval) | ❌ NOT covered | **NEW** |
| **Offline caching** | ❌ NOT covered | **NEW** |
| Authentication | ✅ Covered | None |
| API Client | ✅ Covered | Extend |

### 3.3 Critical Gap: SDLC Context Panel

**Sprint 53 has NO design for:**
- Displaying current SDLC stage
- Showing gate status
- Listing active constraints
- Strict mode indicator
- Sprint context

**Required Design (Sprint 81):**

```typescript
// NEW: src/panels/ContextPanel.ts (NOT in Sprint 53)

interface SDLCContextState {
  // Stage & Gate
  stageName: string | null;
  gateStatus: string | null;
  strictMode: boolean;

  // Sprint
  sprintNumber: number | null;
  sprintGoal: string | null;
  daysRemaining: number | null;

  // Constraints (from Context Overlay Service)
  constraints: Array<{
    type: string;
    severity: 'info' | 'warning' | 'error';
    message: string;
    affectedFiles: string[];
  }>;

  // Metadata
  generatedAt: string;
  projectId: string;
  stale: boolean;  // If using cached data
}

export class ContextPanelProvider implements vscode.WebviewViewProvider {
  public static readonly viewType = 'sdlc.contextPanel';

  private _overlay: SDLCContextState | null = null;
  private _cachedOverlay: SDLCContextState | null = null;
  private _refreshInterval: NodeJS.Timer | null = null;

  // Auto-refresh every 30 seconds
  private readonly REFRESH_INTERVAL_MS = 30000;

  // ... implementation
}
```

### 3.4 Architecture Conflict Resolution

**Sprint 53 defines:**
- `AppBuilderPanel` (code generation focus)
- `GenerationPanel` (SSE streaming)

**Sprint 81 needs:**
- `ContextPanel` (SDLC governance focus)

**Resolution:** These are **complementary**, not conflicting:

```
vscode-extension/src/
├── panels/
│   ├── AppBuilderPanel.ts     # Sprint 53 - Code Generation
│   ├── GenerationPanel.ts     # Sprint 53 - SSE Streaming
│   └── ContextPanel.ts        # Sprint 81 - SDLC Context (NEW)
├── views/
│   └── ContextTreeProvider.ts # Sprint 81 - Tree View (NEW)
└── statusBar/
    └── StageIndicator.ts      # Sprint 81 - Status Bar (NEW)
```

---

## 4. GitHub Integration Review

### 4.1 Current Implementation (Sprint 15)

**Service:** `backend/app/services/github_service.py` (716 lines)

**Implemented:**

| Feature | Status | Notes |
|---------|--------|-------|
| OAuth 2.0 Flow | ✅ Production | `get_authorization_url`, `exchange_code_for_token` |
| Token Validation | ✅ Production | `validate_access_token` |
| Repository Listing | ✅ Production | `list_repositories` |
| Webhook Signature | ✅ Production | HMAC-SHA256 validation |
| Rate Limiting | ✅ Production | 5,000 req/hour awareness |

**API Routes:** `backend/app/api/routes/github.py` (1,317 lines)

| Endpoint | Method | Status |
|----------|--------|--------|
| `/github/authorize` | GET | ✅ |
| `/github/callback` | POST | ✅ |
| `/github/status` | GET | ✅ |
| `/github/repositories` | GET | ✅ |
| `/github/webhook` | POST | ✅ |
| `/github/sync` | POST | ✅ |

### 4.2 Sprint 81 Requirements vs Current State

| Sprint 81 Need | Current State | Gap |
|----------------|---------------|-----|
| **GitHub Check Runs API** | ❌ NOT implemented | **CRITICAL** |
| **GitHub App Installation** | ❌ OAuth only | **REQUIRED** |
| PR Webhook → Check Run trigger | ❌ | **NEW** |
| Check Run annotations | ❌ | **NEW** |
| Branch Protection integration | ❌ | Future |

### 4.3 Critical Gap: GitHub Check Runs

**Current:** OAuth-based integration (read-only repos)

**Sprint 81 Needs:** GitHub App with Check Runs API

**Why GitHub App Required:**
1. Check Runs API requires `checks:write` permission
2. OAuth Apps cannot create Check Runs
3. GitHub App can be installed per-repo with granular permissions

**Required Implementation:**

```python
# NEW: backend/app/services/github_check_run_service.py

class GitHubCheckRunService:
    """
    GitHub Check Run service for SDLC gate status.

    REQUIRES:
    - GitHub App (not OAuth App)
    - App permissions: checks:write, pull_requests:read
    - App installed on target repository
    """

    CHECK_RUN_NAME = "SDLC Gate Evaluation"

    async def create_check_run(
        self,
        installation_token: str,  # NOT user OAuth token
        repo_owner: str,
        repo_name: str,
        head_sha: str,
    ) -> dict:
        """Create a Check Run for PR."""
        # GitHub App Installation Token required
        headers = {
            "Authorization": f"token {installation_token}",
            "Accept": "application/vnd.github+json",
        }

        payload = {
            "name": self.CHECK_RUN_NAME,
            "head_sha": head_sha,
            "status": "queued",
        }

        response = requests.post(
            f"https://api.github.com/repos/{repo_owner}/{repo_name}/check-runs",
            headers=headers,
            json=payload,
        )
        response.raise_for_status()
        return response.json()
```

### 4.4 OAuth vs GitHub App Comparison

| Aspect | OAuth App (Current) | GitHub App (Needed) |
|--------|---------------------|---------------------|
| **Check Runs** | ❌ Cannot create | ✅ Can create |
| **Installation** | Per-user | Per-repo/org |
| **Token Type** | User access token | Installation token |
| **Permissions** | User's permissions | App's permissions |
| **Webhook Secret** | Per-app | Per-installation |

**Migration Path:**
1. Create GitHub App in GitHub Developer Settings
2. Configure permissions: `checks:write`, `pull_requests:read`, `contents:read`
3. Implement App Installation flow
4. Generate Installation Access Tokens
5. Use Installation tokens for Check Runs API

---

## 5. Webhook → Check Run Flow Design

### 5.1 Current Webhook Handler

```python
# backend/app/api/routes/github.py (current)

@router.post("/webhook")
async def github_webhook(request: Request):
    """Handle GitHub webhook events."""
    # Currently: Log events, update project sync status
    # Missing: Trigger Check Runs
```

### 5.2 Proposed Enhancement

```python
# backend/app/api/v1/webhooks/github.py (Sprint 81)

@router.post("/github/webhook")
async def github_webhook(
    request: Request,
    x_github_event: str = Header(...),
    x_hub_signature_256: str = Header(None),
    check_run_service: GitHubCheckRunService = Depends(get_check_run_service),
):
    """
    Handle GitHub webhook events.

    Flow:
    1. Validate signature (HMAC-SHA256)
    2. Parse event type
    3. For pull_request events:
       a. Find project by repo
       b. Get installation token
       c. Create Check Run
       d. Evaluate gates
       e. Update Check Run with result
    """
    payload = await request.json()

    # Validate signature
    if not _validate_signature(await request.body(), x_hub_signature_256):
        raise HTTPException(401, "Invalid signature")

    if x_github_event == "pull_request":
        action = payload.get("action")
        if action in ("opened", "synchronize"):
            # Trigger Check Run
            pr = payload["pull_request"]
            repo = payload["repository"]

            await check_run_service.create_and_evaluate(
                repo_owner=repo["owner"]["login"],
                repo_name=repo["name"],
                head_sha=pr["head"]["sha"],
                pr_number=pr["number"],
            )

    return {"status": "ok"}
```

### 5.3 Sequence Diagram

```
┌────────┐       ┌─────────┐       ┌─────────────┐       ┌──────────────┐       ┌───────┐
│ GitHub │       │ Webhook │       │ CheckRunSvc │       │ ContextOverlay│       │ Gates │
│        │       │ Handler │       │             │       │              │       │       │
└───┬────┘       └────┬────┘       └──────┬──────┘       └───────┬──────┘       └───┬───┘
    │                 │                   │                      │                  │
    │ PR opened       │                   │                      │                  │
    │────────────────>│                   │                      │                  │
    │                 │                   │                      │                  │
    │                 │ create_check_run  │                      │                  │
    │                 │──────────────────>│                      │                  │
    │                 │                   │                      │                  │
    │                 │                   │ get_overlay          │                  │
    │                 │                   │─────────────────────>│                  │
    │                 │                   │                      │                  │
    │                 │                   │ evaluate_gates       │                  │
    │                 │                   │─────────────────────────────────────────>│
    │                 │                   │                      │                  │
    │                 │                   │<────────────────────────────────────────│
    │                 │                   │                      │ gate_result      │
    │                 │                   │                      │                  │
    │<────────────────│───────────────────│ update_check_run     │                  │
    │ Check Run posted│                   │ (annotations)        │                  │
    │                 │                   │                      │                  │
```

---

## 6. Identified Risks & Mitigations

### 6.1 High-Priority Risks

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| **GitHub App not configured by Sprint start** | High | Critical | DevOps must register App by Feb 14 |
| **Installation token expiry (1 hour)** | Medium | High | Implement token refresh mechanism |
| **Webhook delivery failures** | Medium | Medium | Implement retry with exponential backoff |
| **Check Run annotation limit (50)** | Low | Medium | Prioritize critical issues |

### 6.2 Blockers for Sprint 81

| Blocker | Owner | Deadline | Status |
|---------|-------|----------|--------|
| GitHub App registration | DevOps | Feb 14 | ⏳ NOT STARTED |
| VS Code Extension base scaffold | Frontend | Feb 14 | ⏳ PARTIAL |
| Context Overlay API (Sprint 80) | Backend | Feb 3 | ✅ COMPLETE |

---

## 7. Recommendations

### 7.1 Must Do Before Sprint 81

1. **Register GitHub App** (DevOps - 1 day)
   - Permissions: `checks:write`, `pull_requests:read`, `contents:read`
   - Webhook URL: `https://api.sdlc.example.com/api/v1/webhooks/github`

2. **Design Context Panel UI** (Frontend - 2 days)
   - Wireframe for constraint display
   - Status bar design
   - Offline state handling

3. **Test Installation Token Flow** (Backend - 1 day)
   - App → Installation → Token → Check Run

### 7.2 Sprint 81 Scope Adjustment

**Original (38 SP):**
- GitHub Check Run Integration (14 SP)
- PR Webhook Handler (8 SP)
- VS Code Context Panel (10 SP)
- Multi-repo Management (4 SP)
- CLI context command (2 SP)

**Recommended (42 SP, +4 SP for unknowns):**
- GitHub App Setup & Token Management (4 SP) **NEW**
- GitHub Check Run Integration (14 SP)
- PR Webhook Handler (8 SP)
- VS Code Context Panel (10 SP)
- Multi-repo Management (4 SP)
- CLI context command (2 SP)

### 7.3 Updated Timeline

| Day | Focus | Deliverable |
|-----|-------|-------------|
| **Feb 17** | GitHub App Token | Installation token flow working |
| **Feb 18-19** | Check Run API | `create_check_run`, `update_check_run` |
| **Feb 20-21** | Webhook Enhancement | PR → Check Run trigger |
| **Feb 24-25** | VS Code Context Panel | Webview + auto-refresh |
| **Feb 26** | VS Code Status Bar | Stage indicator |
| **Feb 27** | Multi-repo + CLI | Dashboard + `agents context` |
| **Feb 28** | Testing & Docs | E2E tests, documentation |

---

## 8. Appendix: File Inventory

### 8.1 Existing Files (No Changes)

| File | Purpose | Lines |
|------|---------|-------|
| `backend/app/services/github_service.py` | OAuth + Repo access | 716 |
| `backend/app/api/routes/github.py` | GitHub API routes | 1,317 |
| `backend/sdlcctl/cli.py` | CLI main entry | 220 |
| `backend/sdlcctl/commands/agents.py` | AGENTS.md commands | 600 |

### 8.2 Files to Create (Sprint 81)

| File | Purpose | Est. Lines |
|------|---------|------------|
| `backend/app/services/github_check_run_service.py` | Check Run API | ~300 |
| `backend/app/services/github_app_service.py` | App token management | ~200 |
| `vscode-extension/src/panels/ContextPanel.ts` | Context webview | ~250 |
| `vscode-extension/src/statusBar/StageIndicator.ts` | Status bar | ~100 |

### 8.3 Files to Modify (Sprint 81)

| File | Changes |
|------|---------|
| `backend/app/api/v1/webhooks/github.py` | Add Check Run trigger |
| `backend/sdlcctl/commands/agents.py` | Add `context` command |
| `vscode-extension/package.json` | Add Context Panel view |
| `vscode-extension/src/extension.ts` | Register Context Panel |

---

## 9. CTO Decision Required

### 9.1 Questions for CTO

1. **GitHub App Registration**
   - Who will own the GitHub App? (Organization or personal)
   - App name: "SDLC Orchestrator" or different?
   - Installation: Per-repo or organization-wide?

2. **Check Run Behavior**
   - Block merge on gate failure? (Requires Branch Protection rule)
   - Advisory only (comment + status)?

3. **VS Code Extension Priority**
   - Context Panel vs App Builder - which is more urgent?
   - Can we ship Context Panel in Sprint 81 and defer App Builder?

### 9.2 Recommended Decisions

| Question | Recommendation | Rationale |
|----------|----------------|-----------|
| GitHub App owner | Organization | Better security, easier rotation |
| Check Run behavior | Advisory (Sprint 81), Blocking (Sprint 82) | Gradual adoption |
| VS Code priority | Context Panel first | Aligns with AGENTS.md focus |

---

**Document Status:** AWAITING CTO REVIEW
**Created:** January 19, 2026
**Author:** Backend Lead

---

**SDLC 6.1.0 | Stage 02 (DESIGN) | Pre-Sprint Review**
