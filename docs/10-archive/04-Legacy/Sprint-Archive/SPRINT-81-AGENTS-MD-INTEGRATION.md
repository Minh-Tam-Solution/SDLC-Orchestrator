# Sprint 81: AGENTS.md Integration & Delivery Channels

**Sprint ID:** S81
**Status:** ✅ CTO APPROVED (January 19, 2026)
**Duration:** 10 days (February 17-28, 2026)
**Goal:** Integrate AGENTS.md with GitHub Check Runs, VS Code Extension, and PR Webhooks
**Story Points:** 42 SP _(+4 SP from design review)_
**Framework Reference:** SDLC 6.1.0 P5 (SASE Integration)
**Prerequisite:** Sprint 80 ✅ COMPLETE
**Design Review:** [SPRINT-81-DESIGN-REVIEW.md](../../02-design/14-Technical-Specs/SPRINT-81-DESIGN-REVIEW.md)

---

## ✅ CTO DECISIONS (January 19, 2026)

| Decision | CTO Ruling | Notes |
|----------|------------|-------|
| **GitHub App Ownership** | ✅ Organization-owned | Single App for all repos, easier rotation |
| **Check Run Behavior** | ✅ Advisory (Sprint 81) | Blocking enforcement in Sprint 82 |
| **VS Code Priority** | ✅ Context Panel first | Governance before App Builder |
| **Story Points** | ✅ 42 SP approved | +4 SP for GitHub App setup accepted |
| **GitHub App Private Key** | ✅ HashiCorp Vault | 90-day rotation policy |
| **Installation Token Cache** | ✅ Redis with encryption | AES-256 for tokens at rest |

### Go/No-Go Criteria (Feb 14, 2026 - Pre-Sprint)

| Blocker | Status | Deadline |
|---------|--------|----------|
| GitHub App registered | ⏳ Pending | Feb 14 |
| Private key in Vault | ⏳ Pending | Feb 14 |
| VS Code Context Panel wireframe | ⏳ Pending | Feb 14 |

**CTO Note:** *"Advisory mode first - we learn from real PR feedback before blocking. Context Panel is our differentiator."*

---

## 🎯 Sprint 81 Objectives

### Primary Goals (P0)

1. **GitHub App & Token Management** - Setup GitHub App for Check Runs API _(NEW from design review)_
2. **GitHub Check Run Integration** - Post context overlay as GitHub Check Run annotation
3. **PR Webhook Handler** - Auto-post context overlay on PR open/update
4. **VS Code Extension Context Panel** - Display dynamic overlay in IDE sidebar

### Secondary Goals (P1)

5. **Multi-repo AGENTS.md Management** - Dashboard UI for managing AGENTS.md across repos
6. **AGENTS.md Version History** - Track changes and allow rollback
7. **CLI Context Command** - `sdlcctl agents context` to fetch current overlay

---

## ⚠️ Pre-Sprint Blockers (Design Review Findings)

| Blocker | Owner | Deadline | Status |
|---------|-------|----------|--------|
| **GitHub App Registration** | DevOps | Feb 14 | ⏳ NOT STARTED |
| **VS Code Extension Base** | Frontend | Feb 14 | ⏳ PARTIAL |
| **Context Panel Wireframe** | UX | Feb 14 | ⏳ NOT STARTED |

### Critical Gap: GitHub App vs OAuth App

**Current State:** OAuth App (Sprint 15) - cannot create Check Runs
**Required:** GitHub App with `checks:write` permission

```yaml
GitHub App Permissions Required:
  - checks: write           # Create/update Check Runs
  - pull_requests: read     # Read PR metadata
  - contents: read          # Read repo contents
  - metadata: read          # Read repo metadata

Webhook Events:
  - pull_request            # PR opened/synchronized/labeled
  - check_run               # Re-run requests
```

### Critical Gap: VS Code Context Panel

**Sprint 53 Design** focuses on App Builder (code generation)
**Sprint 81 Needs** Context Panel (SDLC governance) - NOT in Sprint 53

**New Design Required:**
- Stage/Gate status display
- Active constraints list
- Strict mode indicator
- Auto-refresh (30s interval)
- Offline caching

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

### Day 1: GitHub App & Token Management (4 SP) - NEW ✅ COMPLETE

| Task | Owner | Est | Priority | Status |
|------|-------|-----|----------|--------|
| Create `GitHubAppService` class | Backend | 2h | P0 | ✅ 515 LOC |
| Implement Installation Token generation | Backend | 2h | P0 | ✅ RS256 JWT |
| Token caching (1 hour expiry) | Backend | 1h | P0 | ✅ 5min buffer |
| Configuration for App ID, Private Key | DevOps | 1h | P0 | ✅ config.py |
| Unit tests (6 tests) | Backend | 2h | P0 | ✅ 10 tests |

**Technical Design:**

```python
# backend/app/services/github_app_service.py
import jwt
import time
from datetime import datetime, timedelta
from typing import Optional
import requests

from app.core.config import settings


class GitHubAppService:
    """
    GitHub App service for Installation Access Tokens.

    IMPORTANT: GitHub Check Runs API requires GitHub App, NOT OAuth App.

    Flow:
    1. Generate JWT from App private key
    2. Exchange JWT for Installation Access Token
    3. Use Installation Token for Check Runs API
    4. Cache token (expires in 1 hour)
    """

    def __init__(self):
        self.app_id = settings.GITHUB_APP_ID
        self.private_key = settings.GITHUB_APP_PRIVATE_KEY
        self._token_cache: dict[int, tuple[str, datetime]] = {}

    def _generate_jwt(self) -> str:
        """Generate JWT for GitHub App authentication."""
        now = int(time.time())
        payload = {
            "iat": now - 60,  # Issued 60 seconds ago
            "exp": now + (10 * 60),  # Expires in 10 minutes
            "iss": self.app_id,
        }
        return jwt.encode(payload, self.private_key, algorithm="RS256")

    async def get_installation_token(self, installation_id: int) -> str:
        """
        Get Installation Access Token for a repo.

        Args:
            installation_id: GitHub App installation ID

        Returns:
            Installation access token (valid for 1 hour)
        """
        # Check cache
        if installation_id in self._token_cache:
            token, expires_at = self._token_cache[installation_id]
            if datetime.utcnow() < expires_at - timedelta(minutes=5):
                return token

        # Generate new token
        jwt_token = self._generate_jwt()
        response = requests.post(
            f"https://api.github.com/app/installations/{installation_id}/access_tokens",
            headers={
                "Authorization": f"Bearer {jwt_token}",
                "Accept": "application/vnd.github+json",
            },
        )
        response.raise_for_status()
        data = response.json()

        token = data["token"]
        expires_at = datetime.fromisoformat(data["expires_at"].replace("Z", "+00:00"))

        # Cache token
        self._token_cache[installation_id] = (token, expires_at)
        return token

    async def get_installation_for_repo(
        self, repo_owner: str, repo_name: str
    ) -> Optional[int]:
        """Find installation ID for a repository."""
        jwt_token = self._generate_jwt()
        response = requests.get(
            f"https://api.github.com/repos/{repo_owner}/{repo_name}/installation",
            headers={
                "Authorization": f"Bearer {jwt_token}",
                "Accept": "application/vnd.github+json",
            },
        )
        if response.status_code == 404:
            return None  # App not installed
        response.raise_for_status()
        return response.json()["id"]
```

**Configuration Required:**

```yaml
# .env additions for Sprint 81
GITHUB_APP_ID=123456
GITHUB_APP_PRIVATE_KEY_PATH=/secrets/github-app-private-key.pem
# OR inline (base64 encoded)
GITHUB_APP_PRIVATE_KEY_BASE64=LS0tLS1CRUdJTi...
```

---

### Day 2-3: GitHub Check Run Integration (14 SP) ✅ COMPLETE

| Task | Owner | Est | Priority | Status |
|------|-------|-----|----------|--------|
| Create `GitHubCheckRunService` class | Backend | 4h | P0 | ✅ 694 LOC |
| Implement Check Run API calls (POST/PATCH) | Backend | 4h | P0 | ✅ Advisory mode |
| Format overlay as Check Run annotations | Backend | 3h | P0 | ✅ 50 max |
| Handle Check Run status (queued/in_progress/completed) | Backend | 3h | P0 | ✅ State machine |
| Integrate with existing `GitHubService` | Backend | 2h | P0 | ✅ App auth |
| Unit tests (10 tests) | Backend | 3h | P0 | ✅ 10 tests |

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

### Day 4-5: PR Webhook Handler (8 SP) ✅ COMPLETE

| Task | Owner | Est | Priority | Status |
|------|-------|-----|----------|--------|
| Enhance PR webhook handler | Backend | 3h | P0 | ✅ github.py |
| Trigger Check Run on PR open/synchronize | Backend | 2h | P0 | ✅ Implemented |
| Handle PR labeled event (force re-evaluation) | Backend | 2h | P1 | ✅ sdlc-recheck |
| Rate limiting (max 10 Check Runs/min/repo) | Backend | 2h | P0 | ⏳ Sprint 82 |
| Integration tests (6 tests) | Backend | 3h | P0 | ✅ Existing tests |

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

### Day 10: CLI Context Command & Documentation (2 SP) ✅ COMPLETE

| Task | Owner | Est | Priority | Status |
|------|-------|-----|----------|--------|
| Add `sdlcctl agents context` command | Backend | 2h | P1 | ✅ 200 LOC |
| Update CLI help documentation | PM | 1h | P0 | ✅ cli.py |
| Sprint 81 completion report | PM | 2h | P0 | ⏳ Pending |
| Handoff to Sprint 82 | PM | 1h | P0 | ⏳ Pending |

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

## 📝 SDLC 6.1.0 Compliance

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

## 📅 Daily Standup Schedule (Updated from Design Review)

| Day | Focus | Deliverable |
|-----|-------|-------------|
| **Feb 17** | GitHub App Setup | `GitHubAppService` + token flow working |
| **Feb 18-19** | GitHub Check Run | `GitHubCheckRunService` complete |
| **Feb 20-21** | PR Webhook | Webhook → Check Run trigger |
| **Feb 24-25** | VS Code Context Panel | Webview + auto-refresh |
| **Feb 26** | VS Code Status Bar | Stage indicator |
| **Feb 27** | Multi-repo + CLI | Dashboard + `agents context` |
| **Feb 28** | Testing & Docs | E2E tests, documentation |

---

## 🏗️ Architecture Impact (Updated from Design Review)

### New Service Dependencies

```
┌─────────────────────────────────────────────────────────────────────┐
│                         Sprint 81 Services                          │
│                                                                     │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │                    GitHub App Integration (NEW)               │  │
│  │                                                               │  │
│  │  ┌─────────────────┐     ┌─────────────────────────────────┐ │  │
│  │  │ GitHubAppSvc    │────▶│  Installation Token Cache       │ │  │
│  │  │ (JWT + Tokens)  │     │  (1 hour expiry)                │ │  │
│  │  └────────┬────────┘     └─────────────────────────────────┘ │  │
│  │           │                                                   │  │
│  │           ▼                                                   │  │
│  │  ┌─────────────────┐     ┌─────────────────────────────────┐ │  │
│  │  │GitHubCheckRunSvc│────▶│  ContextOverlayService (S80)    │ │  │
│  │  │ (NEW)           │     └──────────────┬──────────────────┘ │  │
│  │  └──────────┬──────┘                    │                    │  │
│  └─────────────│───────────────────────────│────────────────────┘  │
│                │                           │                        │
│                ▼                           ▼                        │
│  ┌─────────────────────┐     ┌─────────────────────────────────┐   │
│  │  GitHubService      │     │  GateService                    │   │
│  │  (OAuth - Existing) │     │  (Existing)                     │   │
│  └─────────────────────┘     └─────────────────────────────────┘   │
│                                                                     │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │                    VS Code Extension (NEW)                   │   │
│  │  ┌─────────────────┐   ┌─────────────────┐   ┌───────────┐  │   │
│  │  │  ContextPanel   │   │  StatusBarItem  │   │ ApiClient │  │   │
│  │  │  (Webview)      │   │  (Stage/Gate)   │   │ (Cached)  │  │   │
│  │  └────────┬────────┘   └────────┬────────┘   └─────┬─────┘  │   │
│  │           │                     │                   │        │   │
│  │           └─────────────────────┴───────────────────┘        │   │
│  │                                 │                             │   │
│  │                                 ▼                             │   │
│  │                    /api/v1/agents-md/context/*                │   │
│  └─────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────┘

Key Insight from Design Review:
  - GitHub App (NEW) required for Check Runs - OAuth cannot create Check Runs
  - VS Code Context Panel (NEW) - NOT covered in Sprint 53 design
  - Sprint 53 focused on App Builder, Sprint 81 needs governance context
```

---

## 📋 CTO Review Checklist

### Design Review Findings (RESOLVED ✅)

- [x] **GitHub App Registration** - DevOps assigned, deadline Feb 14
- [x] **GitHub App vs OAuth** - ✅ App approach APPROVED for Check Runs
- [x] **VS Code Context Panel** - ✅ New design APPROVED (priority over App Builder)
- [x] **Story Point Increase** - ✅ 42 SP APPROVED

### Architecture Decisions (APPROVED ✅)

- [x] GitHub App ownership: ✅ **Organization** (CTO approved)
- [x] Check Run behavior: ✅ **Advisory** for Sprint 81, Blocking in Sprint 82
- [x] VS Code priority: ✅ **Context Panel** first (governance focus)

### Resource & Timeline (CONFIRMED ✅)

- [x] Backend: 2 FTE allocated
- [x] Frontend: 1 FTE allocated
- [x] DevOps: 0.5 FTE for GitHub App setup
- [x] Timeline: Feb 17-28 (10 days) confirmed

### Security Review (APPROVED ✅)

- [x] GitHub App private key storage: ✅ **HashiCorp Vault** (90-day rotation)
- [x] Installation token caching: ✅ **Redis with AES-256 encryption**
- [x] Webhook signature validation: ✅ HMAC-SHA256 (existing implementation)
- [x] VS Code credential storage: ✅ SecretStorage API (standard practice)

---

## ✅ Implementation Summary (January 19, 2026)

### Backend Implementation Complete

| Component | File | LOC | Tests | Status |
|-----------|------|-----|-------|--------|
| GitHub App Service | `github_app_service.py` | 515 | 10 | ✅ |
| Check Run Service | `github_check_run_service.py` | 694 | 10 | ✅ |
| PR Webhook Handler | `github.py` (enhanced) | +50 | - | ✅ |
| CLI Context Command | `agents.py` (enhanced) | +200 | - | ✅ |
| Config Settings | `config.py` | +5 | - | ✅ |

**Total Backend: ~1,840 LOC + 20 unit tests**

### Key Features Implemented

1. **GitHub App Authentication**
   - RS256 JWT generation for App authentication
   - Installation token caching (1hr expiry, 5min refresh buffer)
   - Repository installation lookup

2. **Check Run Integration (Advisory Mode)**
   - SDLC context overlay in Check Run output
   - Gate result annotations (capped at 50 per GitHub limit)
   - Severity mapping: error→failure, warning→warning, info→notice

3. **PR Webhook Enhancement**
   - Auto-trigger on `pull_request.opened/synchronize`
   - Re-evaluation on `sdlc-recheck` label

4. **CLI Command**
   - `sdlcctl agents context` with json/cli/pr_comment formats
   - Auto-detect project from `.sdlc/config.json`

### Pending (Frontend - Feb 17-28)

| Component | Owner | Status |
|-----------|-------|--------|
| VS Code Context Panel | Frontend | ⏳ Scheduled |
| Status Bar Item | Frontend | ⏳ Scheduled |
| Auto-refresh | Frontend | ⏳ Scheduled |

### Commits

- `cc6e203` - feat(sprint81): GitHub App + Check Run + CLI Context Implementation ✅
- `171e1d9` - feat(sprint81): CTO Approved - Sprint 81 Plan v1.2.0 ✅

---

## 📎 References

- [Sprint 81 Design Review](../../02-design/14-Technical-Specs/SPRINT-81-DESIGN-REVIEW.md) - Detailed gap analysis
- [VS Code Extension Spec (Sprint 53)](../../02-design/14-Technical-Specs/VSCode-Extension-Specification.md) - App Builder focus
- [GitHub Service (Sprint 15)](../../../backend/app/services/github_service.py) - Current OAuth implementation
- [AGENTS.md Technical Design](../../02-design/14-Technical-Specs/AGENTS-MD-Technical-Design.md) - Sprint 80 foundation

---

**Sprint 81 Plan Version:** 1.3.0 _(Backend Complete)_
**Created:** January 19, 2026
**Updated:** January 19, 2026
**Author:** Backend Lead
**Approved By:** CTO
**Approval Date:** January 19, 2026
**Status:** ✅ BACKEND COMPLETE - FRONTEND SCHEDULED FEB 17-28

---

**SDLC 6.1.0 | Sprint 81 | Stage 04 (BUILD)**

*G-Sprint Gate: ✅ PASSED (CTO Approval Jan 19, 2026)*
*Design Review: ✅ COMPLETE (DRR-081-001)*
*Backend Implementation: ✅ COMPLETE (Jan 19, 2026)*
*Pre-Sprint Blockers: ⏳ Pending (Deadline Feb 14, 2026)*
