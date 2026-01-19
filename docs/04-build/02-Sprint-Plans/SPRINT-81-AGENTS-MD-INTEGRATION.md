# Sprint 81: AGENTS.md Integration & Delivery Channels

**Sprint ID:** S81
**Status:** 📋 DRAFT - CTO REVIEW REQUIRED
**Duration:** 10 days (February 17-28, 2026)
**Goal:** Integrate AGENTS.md with GitHub Check Runs, VS Code Extension, and PR Webhooks
**Story Points:** 38 SP
**Framework Reference:** SDLC 5.1.3 P5 (SASE Integration)
**Prerequisite:** Sprint 80 ✅ COMPLETE

---

## 🎯 Sprint 81 Objectives

### Primary Goals (P0)

1. **GitHub Check Run Integration** - Post context overlay as GitHub Check Run annotation
2. **PR Webhook Handler** - Auto-post context overlay on PR open/update
3. **VS Code Extension Context Panel** - Display dynamic overlay in IDE sidebar

### Secondary Goals (P1)

4. **Multi-repo AGENTS.md Management** - Dashboard UI for managing AGENTS.md across repos
5. **AGENTS.md Version History** - Track changes and allow rollback
6. **CLI Context Command** - `sdlcctl agents context` to fetch current overlay

---

## ✅ Sprint 80 Completion Summary

| Feature | Status | Lines of Code |
|---------|--------|---------------|
| AGENTS.md Generator Service | ✅ Complete | 546 LOC |
| AGENTS.md Validator/Linter | ✅ Complete | 380 LOC |
| Context Overlay Service | ✅ Complete | 562 LOC |
| File Analyzer | ✅ Complete | 491 LOC |
| API Routes (6 endpoints) | ✅ Complete | 430 LOC |
| CLI Commands (init/validate/lint) | ✅ Complete | 600 LOC |
| Database Schema (2 tables) | ✅ Complete | Migration done |
| Unit Tests | ✅ Complete | 52 tests |
| Integration Tests | ✅ Complete | 18 tests |
| E2E Tests | ✅ Complete | 4 scenarios |
| Framework Deprecation (MTS/BRS/LPS) | ✅ Complete | README updated |

**Total Sprint 80 Deliverables:** ~3,000 LOC + Tests + Documentation

---

## 📋 Sprint 81 Backlog

### Day 1-3: GitHub Check Run Integration (14 SP)

| Task | Owner | Est | Priority | Status |
|------|-------|-----|----------|--------|
| Create `GitHubCheckRunService` class | Backend | 4h | P0 | ⏳ |
| Implement Check Run API calls (POST/PATCH) | Backend | 4h | P0 | ⏳ |
| Format overlay as Check Run annotations | Backend | 3h | P0 | ⏳ |
| Handle Check Run status (queued/in_progress/completed) | Backend | 3h | P0 | ⏳ |
| Integrate with existing `GitHubService` | Backend | 2h | P0 | ⏳ |
| Unit tests (10 tests) | Backend | 3h | P0 | ⏳ |

**Technical Design:**

```python
# backend/app/services/github_check_run_service.py
from datetime import datetime
from typing import Optional, List
from uuid import UUID

from pydantic import BaseModel


class CheckRunAnnotation(BaseModel):
    """GitHub Check Run annotation."""
    path: str
    start_line: int
    end_line: int
    annotation_level: str  # "notice", "warning", "failure"
    message: str
    title: str


class CheckRunOutput(BaseModel):
    """GitHub Check Run output."""
    title: str
    summary: str
    text: Optional[str] = None
    annotations: List[CheckRunAnnotation] = []


class GitHubCheckRunService:
    """
    Manage GitHub Check Runs for SDLC context overlay.

    Implements ADR-029 Dynamic Overlay delivery via Check Runs:
    - Creates Check Run when PR opened/updated
    - Posts context overlay as annotations
    - Updates status based on gate evaluation
    """

    CHECK_RUN_NAME = "SDLC Gate Evaluation"

    def __init__(
        self,
        github_service,
        context_overlay_service,
        gate_service,
    ):
        self.github = github_service
        self.overlay_service = context_overlay_service
        self.gate_service = gate_service

    async def create_check_run(
        self,
        project_id: UUID,
        repo_owner: str,
        repo_name: str,
        head_sha: str,
    ) -> dict:
        """
        Create a GitHub Check Run for PR.

        Flow:
        1. Create Check Run in "queued" status
        2. Update to "in_progress"
        3. Evaluate gates
        4. Post overlay as annotations
        5. Complete with conclusion
        """
        # Create Check Run
        check_run = await self.github.create_check_run(
            owner=repo_owner,
            repo=repo_name,
            name=self.CHECK_RUN_NAME,
            head_sha=head_sha,
            status="queued",
        )

        check_run_id = check_run["id"]

        # Update to in_progress
        await self.github.update_check_run(
            owner=repo_owner,
            repo=repo_name,
            check_run_id=check_run_id,
            status="in_progress",
            started_at=datetime.utcnow().isoformat() + "Z",
        )

        # Get context overlay
        overlay = await self.overlay_service.get_overlay(project_id)

        # Evaluate gates
        gate_result = await self.gate_service.evaluate_for_pr(
            project_id=project_id,
            head_sha=head_sha,
        )

        # Build Check Run output
        output = self._build_output(overlay, gate_result)

        # Determine conclusion
        conclusion = "success" if gate_result.passed else "failure"
        if overlay.strict_mode and not gate_result.passed:
            conclusion = "action_required"

        # Complete Check Run
        result = await self.github.update_check_run(
            owner=repo_owner,
            repo=repo_name,
            check_run_id=check_run_id,
            status="completed",
            conclusion=conclusion,
            completed_at=datetime.utcnow().isoformat() + "Z",
            output=output.dict(),
        )

        return result

    def _build_output(self, overlay, gate_result) -> CheckRunOutput:
        """Build Check Run output from overlay and gate result."""

        # Title
        title = f"Stage: {overlay.stage_name} | Gate: {overlay.gate_status}"
        if overlay.strict_mode:
            title = "🔒 STRICT MODE | " + title

        # Summary
        summary_lines = [
            f"**SDLC Stage**: {overlay.stage_name}",
            f"**Gate Status**: {overlay.gate_status}",
            f"**Sprint**: {overlay.sprint.number if overlay.sprint else 'N/A'}",
            "",
            "## Active Constraints",
        ]

        for c in overlay.constraints:
            icon = {"info": "ℹ️", "warning": "⚠️", "error": "🔴"}.get(c.severity, "•")
            summary_lines.append(f"- {icon} **{c.type}**: {c.message}")

        summary = "\n".join(summary_lines)

        # Annotations for files with issues
        annotations = []
        for issue in gate_result.issues:
            annotations.append(CheckRunAnnotation(
                path=issue.file_path,
                start_line=issue.line_number or 1,
                end_line=issue.line_number or 1,
                annotation_level=self._severity_to_level(issue.severity),
                message=issue.message,
                title=issue.code,
            ))

        return CheckRunOutput(
            title=title,
            summary=summary,
            annotations=annotations[:50],  # GitHub limit
        )

    def _severity_to_level(self, severity: str) -> str:
        """Convert severity to GitHub annotation level."""
        mapping = {
            "error": "failure",
            "warning": "warning",
            "info": "notice",
        }
        return mapping.get(severity, "notice")
```

### Day 4-5: PR Webhook Handler (8 SP)

| Task | Owner | Est | Priority | Status |
|------|-------|-----|----------|--------|
| Enhance PR webhook handler | Backend | 3h | P0 | ⏳ |
| Trigger Check Run on PR open/synchronize | Backend | 2h | P0 | ⏳ |
| Handle PR labeled event (force re-evaluation) | Backend | 2h | P1 | ⏳ |
| Rate limiting (max 10 Check Runs/min/repo) | Backend | 2h | P0 | ⏳ |
| Integration tests (6 tests) | Backend | 3h | P0 | ⏳ |

**Webhook Event Handling:**

```python
# backend/app/api/v1/webhooks/github.py (enhancement)

@router.post("/github/webhook")
async def github_webhook(
    request: Request,
    x_github_event: str = Header(...),
    x_github_delivery: str = Header(...),
    x_hub_signature_256: str = Header(None),
    github_service: GitHubService = Depends(get_github_service),
    check_run_service: GitHubCheckRunService = Depends(get_check_run_service),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    Handle GitHub webhook events.

    Supported events:
    - pull_request.opened: Create Check Run
    - pull_request.synchronize: Update Check Run
    - pull_request.labeled: Re-evaluate if "sdlc-recheck" label
    """
    payload = await request.json()

    # Verify signature
    if not github_service.verify_webhook_signature(
        payload=await request.body(),
        signature=x_hub_signature_256,
    ):
        raise HTTPException(status_code=401, detail="Invalid signature")

    # Handle pull_request events
    if x_github_event == "pull_request":
        action = payload.get("action")
        pr = payload.get("pull_request", {})
        repo = payload.get("repository", {})

        # Find project by repo URL
        project = await project_repo.get_by_repo_url(
            db, repo.get("html_url")
        )

        if not project:
            return {"status": "ignored", "reason": "repo not registered"}

        if action in ("opened", "synchronize"):
            # Create/Update Check Run
            await check_run_service.create_check_run(
                project_id=project.id,
                repo_owner=repo["owner"]["login"],
                repo_name=repo["name"],
                head_sha=pr["head"]["sha"],
            )

            return {"status": "check_run_created"}

        elif action == "labeled":
            label = payload.get("label", {}).get("name")
            if label == "sdlc-recheck":
                # Force re-evaluation
                await check_run_service.create_check_run(
                    project_id=project.id,
                    repo_owner=repo["owner"]["login"],
                    repo_name=repo["name"],
                    head_sha=pr["head"]["sha"],
                )
                return {"status": "recheck_triggered"}

    return {"status": "event_not_handled"}
```

### Day 6-7: VS Code Extension Context Panel (10 SP)

| Task | Owner | Est | Priority | Status |
|------|-------|-----|----------|--------|
| Create Context Panel webview | Frontend | 4h | P0 | ⏳ |
| Fetch overlay from API | Frontend | 2h | P0 | ⏳ |
| Display constraints with icons | Frontend | 2h | P0 | ⏳ |
| Auto-refresh on file save | Frontend | 2h | P1 | ⏳ |
| Status bar item (stage/gate) | Frontend | 2h | P1 | ⏳ |
| Unit tests (8 tests) | Frontend | 2h | P0 | ⏳ |

**VS Code Extension Design:**

```typescript
// vscode-extension/src/panels/ContextPanel.ts

import * as vscode from 'vscode';
import { ApiClient } from '../api/client';

interface ContextOverlay {
  project_id: string;
  generated_at: string;
  stage_name: string | null;
  gate_status: string | null;
  sprint: {
    number: number;
    goal: string;
    days_remaining: number;
  } | null;
  constraints: Array<{
    type: string;
    severity: 'info' | 'warning' | 'error';
    message: string;
    affected_files: string[];
  }>;
  strict_mode: boolean;
}

export class ContextPanelProvider implements vscode.WebviewViewProvider {
  public static readonly viewType = 'sdlc.contextPanel';

  private _view?: vscode.WebviewView;
  private _overlay?: ContextOverlay;

  constructor(
    private readonly _extensionUri: vscode.Uri,
    private readonly _apiClient: ApiClient,
  ) {}

  public resolveWebviewView(
    webviewView: vscode.WebviewView,
    context: vscode.WebviewViewResolveContext,
    _token: vscode.CancellationToken,
  ) {
    this._view = webviewView;

    webviewView.webview.options = {
      enableScripts: true,
      localResourceRoots: [this._extensionUri],
    };

    webviewView.webview.html = this._getHtmlForWebview(webviewView.webview);

    // Fetch initial context
    this.refreshContext();

    // Auto-refresh every 30 seconds
    setInterval(() => this.refreshContext(), 30000);
  }

  public async refreshContext() {
    const projectId = await this._getProjectId();
    if (!projectId) {
      this._updateView({ error: 'No project detected' });
      return;
    }

    try {
      this._overlay = await this._apiClient.getContextOverlay(projectId);
      this._updateView({ overlay: this._overlay });
    } catch (error) {
      this._updateView({ error: 'Failed to fetch context' });
    }
  }

  private _updateView(data: { overlay?: ContextOverlay; error?: string }) {
    if (this._view) {
      this._view.webview.postMessage({
        type: 'updateContext',
        ...data,
      });
    }
  }

  private _getHtmlForWebview(webview: vscode.Webview): string {
    return `<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>SDLC Context</title>
  <style>
    body {
      font-family: var(--vscode-font-family);
      padding: 10px;
      color: var(--vscode-foreground);
    }
    .header {
      display: flex;
      justify-content: space-between;
      margin-bottom: 15px;
    }
    .stage-badge {
      background: var(--vscode-badge-background);
      color: var(--vscode-badge-foreground);
      padding: 2px 8px;
      border-radius: 3px;
    }
    .strict-mode {
      background: var(--vscode-inputValidation-errorBackground);
      color: var(--vscode-inputValidation-errorForeground);
      padding: 5px 10px;
      margin-bottom: 10px;
      border-radius: 3px;
    }
    .constraint {
      padding: 5px 0;
      border-bottom: 1px solid var(--vscode-panel-border);
    }
    .constraint-icon {
      margin-right: 8px;
    }
    .severity-error { color: var(--vscode-errorForeground); }
    .severity-warning { color: var(--vscode-warningForeground); }
    .severity-info { color: var(--vscode-textLink-foreground); }
  </style>
</head>
<body>
  <div id="content">Loading...</div>

  <script>
    const vscode = acquireVsCodeApi();

    window.addEventListener('message', event => {
      const message = event.data;
      if (message.type === 'updateContext') {
        renderContext(message);
      }
    });

    function renderContext(data) {
      const content = document.getElementById('content');

      if (data.error) {
        content.innerHTML = '<p class="error">' + data.error + '</p>';
        return;
      }

      const overlay = data.overlay;
      let html = '';

      // Header with stage and gate
      html += '<div class="header">';
      html += '<span class="stage-badge">' + (overlay.stage_name || 'Unknown') + '</span>';
      html += '<span>' + (overlay.gate_status || 'N/A') + '</span>';
      html += '</div>';

      // Strict mode warning
      if (overlay.strict_mode) {
        html += '<div class="strict-mode">🔒 STRICT MODE - Only bug fixes allowed</div>';
      }

      // Sprint info
      if (overlay.sprint) {
        html += '<p><strong>Sprint ' + overlay.sprint.number + '</strong>: ' + overlay.sprint.goal + '</p>';
        html += '<p>' + overlay.sprint.days_remaining + ' days remaining</p>';
      }

      // Constraints
      html += '<h4>Active Constraints</h4>';
      for (const c of overlay.constraints) {
        const icon = {info: 'ℹ️', warning: '⚠️', error: '🔴'}[c.severity] || '•';
        html += '<div class="constraint">';
        html += '<span class="constraint-icon severity-' + c.severity + '">' + icon + '</span>';
        html += '<strong>' + c.type.replace('_', ' ') + '</strong>: ' + c.message;
        html += '</div>';
      }

      content.innerHTML = html;
    }
  </script>
</body>
</html>`;
  }

  private async _getProjectId(): Promise<string | null> {
    // Implementation: detect project from workspace or .sdlc config
    const workspaceFolder = vscode.workspace.workspaceFolders?.[0];
    if (!workspaceFolder) return null;

    // Check for .sdlc/config.json
    try {
      const configUri = vscode.Uri.joinPath(workspaceFolder.uri, '.sdlc', 'config.json');
      const configContent = await vscode.workspace.fs.readFile(configUri);
      const config = JSON.parse(configContent.toString());
      return config.project_id;
    } catch {
      return null;
    }
  }
}
```

### Day 8-9: Multi-Repo Management (4 SP)

| Task | Owner | Est | Priority | Status |
|------|-------|-----|----------|--------|
| Dashboard: AGENTS.md overview page | Frontend | 3h | P1 | ⏳ |
| Bulk generate for multiple repos | Backend | 2h | P1 | ⏳ |
| Diff view for AGENTS.md changes | Frontend | 2h | P1 | ⏳ |
| Unit tests (4 tests) | QA | 1h | P1 | ⏳ |

### Day 10: CLI Context Command & Documentation (2 SP)

| Task | Owner | Est | Priority | Status |
|------|-------|-----|----------|--------|
| Add `sdlcctl agents context` command | Backend | 2h | P1 | ⏳ |
| Update CLI help documentation | PM | 1h | P0 | ⏳ |
| Sprint 81 completion report | PM | 2h | P0 | ⏳ |
| Handoff to Sprint 82 | PM | 1h | P0 | ⏳ |

**CLI Context Command:**

```python
# backend/sdlcctl/commands/agents.py (addition)

@agents_app.command(name="context")
def agents_context_command(
    project_id: Optional[str] = typer.Option(None, "--project", "-p", help="Project ID (auto-detect if not provided)"),
    format: str = typer.Option("cli", "--format", "-f", help="Output format: cli, json, pr_comment"),
) -> None:
    """
    Fetch and display current SDLC context overlay.

    The context overlay includes:
    - Current SDLC stage and gate status
    - Active sprint information
    - Constraints and warnings
    - Strict mode status (post-G3)

    Examples:
        sdlcctl agents context
        sdlcctl agents context --format json
        sdlcctl agents context --project abc123 --format pr_comment
    """
    console = Console()

    # Auto-detect project if not provided
    if not project_id:
        config_path = Path.cwd() / ".sdlc" / "config.json"
        if config_path.exists():
            import json
            config = json.loads(config_path.read_text())
            project_id = config.get("project_id")

    if not project_id:
        console.print("[red]Error:[/red] No project ID found. Use --project or create .sdlc/config.json")
        raise typer.Exit(code=1)

    # Fetch overlay from API
    try:
        import httpx
        response = httpx.get(
            f"{get_api_base_url()}/api/v1/agents-md/context/{project_id}",
            headers=get_auth_headers(),
        )
        response.raise_for_status()
        overlay = response.json()
    except Exception as e:
        console.print(f"[red]Error fetching context:[/red] {e}")
        raise typer.Exit(code=1)

    # Format output
    if format == "json":
        import json
        console.print_json(json.dumps(overlay, indent=2))
    elif format == "pr_comment":
        console.print(overlay.get("formatted", {}).get("pr_comment", ""))
    else:
        # CLI format
        console.print()
        console.print(Panel(
            f"[bold]Stage:[/bold] {overlay.get('stage_name', 'Unknown')}\n"
            f"[bold]Gate:[/bold] {overlay.get('gate_status', 'N/A')}\n"
            f"[bold]Strict Mode:[/bold] {'🔒 YES' if overlay.get('strict_mode') else 'No'}",
            title="SDLC Context",
            border_style="blue",
        ))

        # Constraints
        constraints = overlay.get("constraints", [])
        if constraints:
            console.print("\n[bold]Active Constraints:[/bold]")
            for c in constraints:
                icon = {"info": "ℹ️", "warning": "⚠️", "error": "🔴"}.get(c.get("severity"), "•")
                console.print(f"  {icon} [bold]{c.get('type')}:[/bold] {c.get('message')}")

        console.print()
```

---

## 🔗 API Endpoints (New in Sprint 81)

```yaml
# Sprint 81 New Endpoints

# GitHub Check Run trigger (internal)
POST /api/v1/webhooks/github:
  summary: Handle GitHub webhook events
  tags: [Webhooks]
  events:
    - pull_request.opened
    - pull_request.synchronize
    - pull_request.labeled

# Context Overlay (enhanced)
GET /api/v1/agents-md/context/{project_id}:
  summary: Get dynamic context overlay
  tags: [AGENTS.md]
  query_params:
    format: string (all, pr_comment, cli, vscode, check_run)
    trigger_type: string (pr_webhook, manual, scheduled)
    trigger_ref: string (PR#123, manual)
  response:
    stage_name: string
    gate_status: string
    sprint: SprintContext
    constraints: array[Constraint]
    strict_mode: boolean
    formatted:
      pr_comment: string
      cli: string
      vscode: object
      check_run: object

# Context Overlay History
GET /api/v1/agents-md/context/{project_id}/history:
  summary: Get context overlay history
  tags: [AGENTS.md]
  query_params:
    limit: integer (default: 10)
    offset: integer (default: 0)
  response:
    items: array[ContextOverlay]
    total: integer
```

---

## 🔒 Definition of Done

### Code Complete

- [ ] `GitHubCheckRunService` with create/update methods
- [ ] PR webhook handler enhancement (trigger Check Run)
- [ ] VS Code Extension Context Panel
- [ ] CLI `sdlcctl agents context` command
- [ ] Multi-repo dashboard UI
- [ ] AGENTS.md version history (optional)

### Tests

- [ ] Unit tests: `test_github_check_run_service.py` (10 tests)
- [ ] Unit tests: `test_webhook_handler.py` (6 tests)
- [ ] Integration tests: `test_check_run_integration.py` (4 tests)
- [ ] VS Code Extension tests (8 tests)
- [ ] Total coverage: 90%+

### Documentation

- [ ] API documentation updated (OpenAPI)
- [ ] CLI help text (`sdlcctl agents context --help`)
- [ ] VS Code Extension README
- [ ] GitHub Check Run setup guide

### Review

- [ ] Code review by Tech Lead
- [ ] CTO approval on Check Run design
- [ ] Security review (webhook signature validation)
- [ ] PR merged to main
- [ ] Staging deployment verified

---

## 📊 Metrics & Success Criteria

| Metric | Target | Notes |
|--------|--------|-------|
| Check Run creation time | <5s | From PR event to Check Run posted |
| Context fetch latency | <500ms | API response time |
| VS Code panel refresh | <1s | UI update after fetch |
| Webhook processing | <2s | End-to-end latency |
| Test coverage | 90%+ | All new code |

---

## 🔴 Dependencies on Other Teams

| Dependency | Team | Status | Blocker? |
|------------|------|--------|----------|
| Sprint 80 Complete | Backend | ✅ Complete | ❌ Resolved |
| GitHub App registration | DevOps | ⏳ Required | ⚠️ Yes |
| VS Code Extension base | Frontend | ⏳ Sprint 80 | ⚠️ Partial |

---

## ⚠️ Risks & Mitigations

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| GitHub API rate limits | Medium | High | Implement rate limiting, batch requests |
| Check Run annotation limit (50) | Low | Medium | Prioritize most critical issues |
| VS Code API changes | Low | Medium | Pin extension API version |
| Webhook delivery failures | Medium | Medium | Implement retry with exponential backoff |

---

## 📝 SDLC 5.1.3 Compliance

| Pillar | Sprint 81 Implementation |
|--------|--------------------------|
| P5 (SASE Integration) | GitHub Check Run = enforcement point |
| P4 (Quality Gates) | Check Run blocks merge if gates fail |
| P3 (4-Tier Classification) | Overlay adapts to project tier |
| P7 (Documentation) | All APIs documented |

---

## 🚀 Handoff to Sprint 82

### Expected Completion (Sprint 81)

- ✅ GitHub Check Run integration
- ✅ PR webhook → auto Check Run
- ✅ VS Code Context Panel
- ✅ CLI context command

### Sprint 82 Focus (March 3-14)

- ⏳ AGENTS.md template marketplace
- ⏳ Custom section plugins
- ⏳ Team-wide AGENTS.md sync
- ⏳ Analytics dashboard (overlay usage)

---

## 📅 Daily Standup Schedule

| Day | Focus | Deliverable |
|-----|-------|-------------|
| Feb 17-18 | GitHub Check Run | `GitHubCheckRunService` complete |
| Feb 19 | Check Run output | Annotations + summary |
| Feb 20-21 | PR Webhook | Webhook handler enhanced |
| Feb 24-25 | VS Code Extension | Context Panel complete |
| Feb 26-27 | Multi-repo + CLI | Dashboard + `agents context` |
| Feb 28 | Testing & Docs | Sprint completion |

---

## 🏗️ Architecture Impact

### New Service Dependencies

```
┌─────────────────────────────────────────────────────────────────────┐
│                         Sprint 81 Services                          │
│                                                                     │
│  ┌─────────────────────┐     ┌─────────────────────────────────┐   │
│  │  GitHubCheckRunSvc  │────▶│  ContextOverlayService (S80)    │   │
│  │  (NEW)              │     └──────────────┬──────────────────┘   │
│  └──────────┬──────────┘                    │                       │
│             │                               │                       │
│             ▼                               ▼                       │
│  ┌─────────────────────┐     ┌─────────────────────────────────┐   │
│  │  GitHubService      │     │  GateService                    │   │
│  │  (Enhanced)         │     │  (Existing)                     │   │
│  └─────────────────────┘     └─────────────────────────────────┘   │
│                                                                     │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │                    VS Code Extension                         │   │
│  │  ┌─────────────────┐   ┌─────────────────┐                   │   │
│  │  │  ContextPanel   │   │  StatusBarItem  │                   │   │
│  │  │  (Webview)      │   │  (Stage/Gate)   │                   │   │
│  │  └────────┬────────┘   └────────┬────────┘                   │   │
│  │           │                     │                             │   │
│  │           └─────────┬───────────┘                             │   │
│  │                     ▼                                         │   │
│  │           ┌─────────────────┐                                 │   │
│  │           │  API Client     │───────▶ /api/v1/agents-md/*    │   │
│  │           └─────────────────┘                                 │   │
│  └─────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 📋 CTO Review Checklist

- [ ] Architecture design approved
- [ ] GitHub Check Run approach validated
- [ ] VS Code Extension scope confirmed
- [ ] Security considerations reviewed
- [ ] Performance budget acceptable
- [ ] Resource allocation confirmed (Backend: 2 FTE, Frontend: 1 FTE)

---

**Sprint 81 Plan Version:** 1.0.0
**Created:** January 19, 2026
**Author:** Backend Lead
**Status:** 📋 AWAITING CTO APPROVAL

---

**SDLC 5.1.3 | Sprint 81 | Stage 04 (BUILD)**

*G-Sprint Approval Required Before Sprint Start*
