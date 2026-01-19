"""
=========================================================================
GitHub Check Run Service - SDLC Gate Evaluation (Sprint 81)
SDLC Orchestrator - Stage 04 (BUILD)

Version: 1.0.0
Date: January 19, 2026
Status: ACTIVE - Sprint 81 (AGENTS.md Integration)
Authority: Backend Lead + CTO Approved
Foundation: Sprint 81 Plan, ADR-029, SPRINT-81-DESIGN-REVIEW.md
Framework: SDLC 5.1.3 (7-Pillar Architecture)

Purpose:
- Create GitHub Check Runs for PRs
- Post SDLC context overlay as Check Run annotations
- Update Check Run status based on gate evaluation
- Format overlay for GitHub Check Run output

CTO Decision (Jan 19, 2026):
- Advisory mode for Sprint 81 (conclusion: neutral/success)
- Blocking enforcement in Sprint 82 (conclusion: failure/action_required)

Architecture:
- Uses GitHubAppService for Installation Tokens
- Integrates with ContextOverlayService (Sprint 80)
- Integrates with GateService for evaluation

AGPL-Safe Implementation:
- Uses Python requests library (Apache 2.0 license)
- Network-only access via GitHub REST API

Zero Mock Policy: 100% real implementation
=========================================================================
"""

import logging
from datetime import datetime, timezone
from typing import Any, Optional
from uuid import UUID

from pydantic import BaseModel

from app.services.github_app_service import (
    GitHubAppService,
    GitHubAppError,
    get_github_app_service,
)

logger = logging.getLogger(__name__)

# ============================================================================
# Constants
# ============================================================================

GITHUB_API_BASE_URL = "https://api.github.com"

# Check Run name displayed in GitHub PR
CHECK_RUN_NAME = "SDLC Gate Evaluation"

# Maximum annotations per Check Run (GitHub limit)
MAX_ANNOTATIONS = 50

# Maximum summary length (64 KB)
MAX_SUMMARY_LENGTH = 65535


# ============================================================================
# Data Models
# ============================================================================


class CheckRunAnnotation(BaseModel):
    """
    GitHub Check Run annotation for file-level feedback.

    Annotations appear inline in PR diff view, highlighting specific
    issues at the file and line level.
    """

    path: str  # File path relative to repo root
    start_line: int  # Starting line number
    end_line: int  # Ending line number
    annotation_level: str  # "notice", "warning", "failure"
    message: str  # Annotation message (markdown supported)
    title: str  # Short title for the annotation


class CheckRunOutput(BaseModel):
    """
    GitHub Check Run output with summary and annotations.

    Displayed in the Check Run details view with full formatting.
    """

    title: str  # Title shown in Check Run header
    summary: str  # Markdown summary (max 64KB)
    text: Optional[str] = None  # Extended markdown text
    annotations: list[CheckRunAnnotation] = []


class CheckRunResult(BaseModel):
    """Result of creating/updating a Check Run."""

    check_run_id: int
    status: str  # "queued", "in_progress", "completed"
    conclusion: Optional[str] = None  # "success", "failure", "neutral", etc.
    html_url: str  # URL to view Check Run on GitHub


# ============================================================================
# Custom Exceptions
# ============================================================================


class CheckRunError(Exception):
    """Base exception for Check Run errors."""

    pass


class CheckRunCreateError(CheckRunError):
    """Exception raised when Check Run creation fails."""

    pass


class CheckRunUpdateError(CheckRunError):
    """Exception raised when Check Run update fails."""

    pass


# ============================================================================
# GitHub Check Run Service
# ============================================================================


class GitHubCheckRunService:
    """
    Manage GitHub Check Runs for SDLC context overlay.

    Implements ADR-029 Dynamic Overlay delivery via Check Runs:
    - Creates Check Run when PR opened/updated
    - Posts context overlay as annotations
    - Updates status based on gate evaluation

    CTO Decision (Jan 19, 2026):
    - Sprint 81: Advisory mode (conclusion: neutral/success)
    - Sprint 82: Blocking enforcement (conclusion: failure/action_required)

    Usage:
        check_run_service = GitHubCheckRunService(
            github_app_service=github_app_service,
            context_overlay_service=context_overlay_service,
            gate_service=gate_service,
        )

        # Create Check Run for a PR
        result = await check_run_service.create_check_run(
            project_id=uuid,
            repo_owner="anthropics",
            repo_name="claude-code",
            head_sha="abc123",
        )
        print(f"Check Run created: {result.html_url}")
    """

    def __init__(
        self,
        github_app_service: Optional[GitHubAppService] = None,
        context_overlay_service: Optional[Any] = None,
        gate_service: Optional[Any] = None,
    ):
        """
        Initialize Check Run service.

        Args:
            github_app_service: GitHub App service for tokens
            context_overlay_service: Context overlay service (Sprint 80)
            gate_service: Gate evaluation service
        """
        self.github_app = github_app_service or get_github_app_service()
        self.overlay_service = context_overlay_service
        self.gate_service = gate_service
        self.timeout = 30

        logger.info("GitHub Check Run service initialized")

    async def create_check_run(
        self,
        project_id: UUID,
        repo_owner: str,
        repo_name: str,
        head_sha: str,
        installation_id: Optional[int] = None,
    ) -> CheckRunResult:
        """
        Create a GitHub Check Run for PR.

        Full flow:
        1. Create Check Run in "queued" status
        2. Update to "in_progress"
        3. Get context overlay from Sprint 80 service
        4. Evaluate gates (if gate_service available)
        5. Build Check Run output
        6. Complete with conclusion

        CTO Decision: Advisory mode (Sprint 81) - uses "neutral" or "success"
        conclusion. Blocking mode (Sprint 82) will use "failure" or
        "action_required" for gate failures.

        Args:
            project_id: SDLC Orchestrator project ID
            repo_owner: Repository owner (username or organization)
            repo_name: Repository name
            head_sha: Git commit SHA for the PR head
            installation_id: GitHub App installation ID (auto-detected if None)

        Returns:
            CheckRunResult with Check Run details

        Raises:
            CheckRunCreateError: If Check Run creation fails
            GitHubAppError: If GitHub App authentication fails

        Example:
            result = await check_run_service.create_check_run(
                project_id=uuid,
                repo_owner="org",
                repo_name="repo",
                head_sha="abc123",
            )
        """
        import requests

        logger.info(
            f"Creating Check Run for {repo_owner}/{repo_name} "
            f"(sha={head_sha[:8]}, project={project_id})"
        )

        # Get installation ID if not provided
        if installation_id is None:
            installation_id = await self.github_app.get_installation_for_repo(
                repo_owner, repo_name
            )
            if installation_id is None:
                raise CheckRunCreateError(
                    f"GitHub App not installed on {repo_owner}/{repo_name}. "
                    "Please install the SDLC Orchestrator GitHub App."
                )

        # Get installation token
        token = await self.github_app.get_installation_token(installation_id)

        # Step 1: Create Check Run in "queued" status
        check_run_id = await self._create_check_run_api(
            token=token,
            repo_owner=repo_owner,
            repo_name=repo_name,
            head_sha=head_sha,
            status="queued",
        )

        logger.info(f"Check Run created (id={check_run_id})")

        # Step 2: Update to "in_progress"
        await self._update_check_run_api(
            token=token,
            repo_owner=repo_owner,
            repo_name=repo_name,
            check_run_id=check_run_id,
            status="in_progress",
            started_at=datetime.now(timezone.utc).isoformat(),
        )

        # Step 3: Get context overlay
        overlay = await self._get_overlay(project_id)

        # Step 4: Evaluate gates (optional)
        gate_result = await self._evaluate_gates(project_id, head_sha)

        # Step 5: Build Check Run output
        output = self._build_output(overlay, gate_result)

        # Step 6: Determine conclusion
        # CTO Decision (Sprint 81): Advisory mode - use "neutral" or "success"
        # Sprint 82 will implement blocking with "failure" / "action_required"
        conclusion = self._determine_conclusion(overlay, gate_result, advisory_mode=True)

        # Step 7: Complete Check Run
        result = await self._update_check_run_api(
            token=token,
            repo_owner=repo_owner,
            repo_name=repo_name,
            check_run_id=check_run_id,
            status="completed",
            conclusion=conclusion,
            completed_at=datetime.now(timezone.utc).isoformat(),
            output=output.model_dump() if output else None,
        )

        logger.info(
            f"Check Run completed (id={check_run_id}, conclusion={conclusion})"
        )

        return CheckRunResult(
            check_run_id=check_run_id,
            status="completed",
            conclusion=conclusion,
            html_url=result.get("html_url", ""),
        )

    async def update_check_run(
        self,
        repo_owner: str,
        repo_name: str,
        check_run_id: int,
        status: str,
        conclusion: Optional[str] = None,
        output: Optional[CheckRunOutput] = None,
        installation_id: Optional[int] = None,
    ) -> dict:
        """
        Update an existing Check Run.

        Args:
            repo_owner: Repository owner
            repo_name: Repository name
            check_run_id: Existing Check Run ID
            status: New status ("queued", "in_progress", "completed")
            conclusion: Conclusion if completed (see GitHub docs)
            output: Updated output content
            installation_id: GitHub App installation ID

        Returns:
            Updated Check Run data from GitHub API

        Example:
            await check_run_service.update_check_run(
                repo_owner="org",
                repo_name="repo",
                check_run_id=123,
                status="completed",
                conclusion="success",
            )
        """
        # Get installation ID if not provided
        if installation_id is None:
            installation_id = await self.github_app.get_installation_for_repo(
                repo_owner, repo_name
            )
            if installation_id is None:
                raise CheckRunUpdateError(
                    f"GitHub App not installed on {repo_owner}/{repo_name}"
                )

        token = await self.github_app.get_installation_token(installation_id)

        completed_at = None
        if status == "completed":
            completed_at = datetime.now(timezone.utc).isoformat()

        return await self._update_check_run_api(
            token=token,
            repo_owner=repo_owner,
            repo_name=repo_name,
            check_run_id=check_run_id,
            status=status,
            conclusion=conclusion,
            completed_at=completed_at,
            output=output.model_dump() if output else None,
        )

    # ============================================================================
    # Private Methods - API Calls
    # ============================================================================

    async def _create_check_run_api(
        self,
        token: str,
        repo_owner: str,
        repo_name: str,
        head_sha: str,
        status: str = "queued",
    ) -> int:
        """Create Check Run via GitHub API."""
        import requests

        response = requests.post(
            f"{GITHUB_API_BASE_URL}/repos/{repo_owner}/{repo_name}/check-runs",
            headers={
                "Authorization": f"token {token}",
                "Accept": "application/vnd.github+json",
                "X-GitHub-Api-Version": "2022-11-28",
            },
            json={
                "name": CHECK_RUN_NAME,
                "head_sha": head_sha,
                "status": status,
            },
            timeout=self.timeout,
        )

        if response.status_code != 201:
            error_msg = response.json().get("message", response.text)
            raise CheckRunCreateError(f"Failed to create Check Run: {error_msg}")

        return response.json()["id"]

    async def _update_check_run_api(
        self,
        token: str,
        repo_owner: str,
        repo_name: str,
        check_run_id: int,
        status: str,
        conclusion: Optional[str] = None,
        started_at: Optional[str] = None,
        completed_at: Optional[str] = None,
        output: Optional[dict] = None,
    ) -> dict:
        """Update Check Run via GitHub API."""
        import requests

        data: dict[str, Any] = {"status": status}

        if conclusion:
            data["conclusion"] = conclusion
        if started_at:
            data["started_at"] = started_at
        if completed_at:
            data["completed_at"] = completed_at
        if output:
            # Ensure annotations limit
            if "annotations" in output:
                output["annotations"] = output["annotations"][:MAX_ANNOTATIONS]
            # Ensure summary length
            if "summary" in output and len(output["summary"]) > MAX_SUMMARY_LENGTH:
                output["summary"] = output["summary"][:MAX_SUMMARY_LENGTH - 100] + "\n\n... (truncated)"
            data["output"] = output

        response = requests.patch(
            f"{GITHUB_API_BASE_URL}/repos/{repo_owner}/{repo_name}/check-runs/{check_run_id}",
            headers={
                "Authorization": f"token {token}",
                "Accept": "application/vnd.github+json",
                "X-GitHub-Api-Version": "2022-11-28",
            },
            json=data,
            timeout=self.timeout,
        )

        if response.status_code != 200:
            error_msg = response.json().get("message", response.text)
            raise CheckRunUpdateError(f"Failed to update Check Run: {error_msg}")

        return response.json()

    # ============================================================================
    # Private Methods - Business Logic
    # ============================================================================

    async def _get_overlay(self, project_id: UUID) -> Optional[dict]:
        """Get context overlay from Sprint 80 service."""
        if self.overlay_service is None:
            logger.warning("Context overlay service not configured")
            return None

        try:
            return await self.overlay_service.get_overlay(project_id)
        except Exception as e:
            logger.error(f"Failed to get context overlay: {e}")
            return None

    async def _evaluate_gates(
        self, project_id: UUID, head_sha: str
    ) -> Optional[dict]:
        """Evaluate gates for PR."""
        if self.gate_service is None:
            logger.warning("Gate service not configured")
            return None

        try:
            return await self.gate_service.evaluate_for_pr(
                project_id=project_id,
                head_sha=head_sha,
            )
        except Exception as e:
            logger.error(f"Failed to evaluate gates: {e}")
            return None

    def _build_output(
        self,
        overlay: Optional[dict],
        gate_result: Optional[dict],
    ) -> CheckRunOutput:
        """
        Build Check Run output from overlay and gate result.

        Creates a formatted markdown summary with:
        - Current SDLC stage and gate status
        - Sprint information
        - Active constraints
        - Gate evaluation results (if available)
        """
        # Default values if overlay not available
        stage_name = "Unknown"
        gate_status = "N/A"
        strict_mode = False
        constraints = []
        sprint_info = None

        if overlay:
            stage_name = overlay.get("stage_name", "Unknown")
            gate_status = overlay.get("gate_status", "N/A")
            strict_mode = overlay.get("strict_mode", False)
            constraints = overlay.get("constraints", [])
            sprint_info = overlay.get("sprint")

        # Build title
        title = f"Stage: {stage_name} | Gate: {gate_status}"
        if strict_mode:
            title = "🔒 STRICT MODE | " + title

        # Build summary
        summary_lines = [
            "## SDLC Context Overlay",
            "",
            f"**Stage**: {stage_name}",
            f"**Gate Status**: {gate_status}",
        ]

        if sprint_info:
            summary_lines.extend([
                f"**Sprint**: {sprint_info.get('number', 'N/A')}",
                f"**Sprint Goal**: {sprint_info.get('goal', 'N/A')}",
                f"**Days Remaining**: {sprint_info.get('days_remaining', 'N/A')}",
            ])

        if strict_mode:
            summary_lines.extend([
                "",
                "> ⚠️ **STRICT MODE ACTIVE**",
                "> Only bug fixes are allowed in this stage.",
            ])

        # Constraints section
        if constraints:
            summary_lines.extend([
                "",
                "## Active Constraints",
                "",
            ])

            for c in constraints:
                severity = c.get("severity", "info")
                icon = {"info": "ℹ️", "warning": "⚠️", "error": "🔴"}.get(severity, "•")
                constraint_type = c.get("type", "unknown").replace("_", " ").title()
                message = c.get("message", "")
                summary_lines.append(f"- {icon} **{constraint_type}**: {message}")

        # Gate result section
        if gate_result:
            passed = gate_result.get("passed", True)
            summary_lines.extend([
                "",
                "## Gate Evaluation",
                "",
                f"**Result**: {'✅ PASSED' if passed else '❌ FAILED'}",
            ])

            issues = gate_result.get("issues", [])
            if issues:
                summary_lines.append(f"**Issues Found**: {len(issues)}")

        # Footer
        summary_lines.extend([
            "",
            "---",
            "*Generated by SDLC Orchestrator - ADR-029 Dynamic Context Overlay*",
        ])

        summary = "\n".join(summary_lines)

        # Build annotations from gate issues
        annotations = []
        if gate_result and "issues" in gate_result:
            for issue in gate_result["issues"][:MAX_ANNOTATIONS]:
                annotations.append(CheckRunAnnotation(
                    path=issue.get("file_path", ""),
                    start_line=issue.get("line_number", 1),
                    end_line=issue.get("line_number", 1),
                    annotation_level=self._severity_to_level(issue.get("severity", "info")),
                    message=issue.get("message", ""),
                    title=issue.get("code", "Issue"),
                ))

        return CheckRunOutput(
            title=title,
            summary=summary,
            annotations=annotations,
        )

    def _determine_conclusion(
        self,
        overlay: Optional[dict],
        gate_result: Optional[dict],
        advisory_mode: bool = True,
    ) -> str:
        """
        Determine Check Run conclusion.

        CTO Decision (Sprint 81):
        - Advisory mode: "neutral" or "success" (never blocks)
        - Sprint 82 will implement blocking mode

        Args:
            overlay: Context overlay data
            gate_result: Gate evaluation result
            advisory_mode: If True, use neutral/success (Sprint 81)

        Returns:
            Conclusion string for GitHub API
        """
        # Check if gates passed
        gates_passed = True
        if gate_result:
            gates_passed = gate_result.get("passed", True)

        # Check strict mode
        strict_mode = False
        if overlay:
            strict_mode = overlay.get("strict_mode", False)

        # Sprint 81: Advisory mode (CTO Decision)
        if advisory_mode:
            if gates_passed:
                return "success"
            else:
                # Advisory mode: use "neutral" instead of "failure"
                return "neutral"

        # Sprint 82: Blocking mode (future)
        if not gates_passed:
            if strict_mode:
                return "action_required"
            else:
                return "failure"

        return "success"

    def _severity_to_level(self, severity: str) -> str:
        """Convert severity to GitHub annotation level."""
        mapping = {
            "error": "failure",
            "warning": "warning",
            "info": "notice",
        }
        return mapping.get(severity, "notice")


# ============================================================================
# Global Check Run Service Instance
# ============================================================================

# Note: Requires dependency injection for overlay_service and gate_service
# Use get_check_run_service() factory in API routes

_check_run_service: Optional[GitHubCheckRunService] = None


def get_check_run_service(
    context_overlay_service: Optional[Any] = None,
    gate_service: Optional[Any] = None,
) -> GitHubCheckRunService:
    """
    Get GitHub Check Run service instance.

    Args:
        context_overlay_service: Context overlay service (optional)
        gate_service: Gate service (optional)

    Returns:
        GitHubCheckRunService instance
    """
    global _check_run_service

    if _check_run_service is None:
        _check_run_service = GitHubCheckRunService(
            context_overlay_service=context_overlay_service,
            gate_service=gate_service,
        )

    return _check_run_service
