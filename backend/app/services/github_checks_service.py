"""
=========================================================================
GitHub Checks Service - Check Run API for Gate Enforcement (Sprint 79)
SDLC Orchestrator - Stage 04 (BUILD)

Version: 1.0.0
Date: January 19, 2026
Status: ACTIVE - Sprint 79 (Pre-Launch Hardening)
Authority: CTO + Backend Lead Approved
Foundation: ADR-029, SPRINT-79-PRE-LAUNCH-HARDENING.md
Framework: SDLC 5.1.3 (7-Pillar Architecture)

Purpose:
- Create Check Runs for SDLC Gate evaluation status
- Update Check Runs as gate evaluation progresses
- Block merge when gates fail (hard enforcement)
- Deliver dynamic context via Check Run output

GitHub Checks API Documentation:
https://docs.github.com/en/rest/checks/runs

Why GitHub Checks API (vs PR Comments):
- Check Runs integrate with branch protection rules
- When check fails, merge button is DISABLED (hard enforcement)
- PR comments are advisory only (soft enforcement)

AGPL-Safe Implementation:
- Uses Python requests library (Apache 2.0 license)
- Network-only access via GitHub REST API
- Requires GitHub App installation (not OAuth)

Zero Mock Policy: 100% real implementation (requests + GitHub API)
=========================================================================
"""

import logging
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional
from uuid import UUID

import requests
from requests.exceptions import RequestException, Timeout

from app.core.config import settings

logger = logging.getLogger(__name__)

# ============================================================================
# Constants
# ============================================================================

GITHUB_API_BASE_URL = "https://api.github.com"

# Check Run statuses
class CheckRunStatus(str, Enum):
    """GitHub Check Run status values."""
    QUEUED = "queued"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"


class CheckRunConclusion(str, Enum):
    """GitHub Check Run conclusion values (only valid when status=completed)."""
    SUCCESS = "success"
    FAILURE = "failure"
    NEUTRAL = "neutral"
    CANCELLED = "cancelled"
    SKIPPED = "skipped"
    TIMED_OUT = "timed_out"
    ACTION_REQUIRED = "action_required"


# ============================================================================
# Custom Exceptions
# ============================================================================


class GitHubChecksError(Exception):
    """Base exception for GitHub Checks service errors."""
    pass


class GitHubAppNotInstalledError(GitHubChecksError):
    """Exception raised when GitHub App is not installed on repository."""
    pass


class GitHubChecksAPIError(GitHubChecksError):
    """Exception raised when GitHub Checks API call fails."""
    pass


# ============================================================================
# GitHub Checks Service
# ============================================================================


class GitHubChecksService:
    """
    GitHub Checks API service for gate enforcement.

    This service creates and updates Check Runs that integrate with
    GitHub's branch protection rules to provide hard enforcement
    of SDLC gates.

    Architecture (ADR-029):
    - Static AGENTS.md: Committed to repo, read by AI coders
    - Dynamic Overlay: Delivered via Check Run output (this service)
    - Hard Enforcement: Check Run failure = merge blocked

    Usage:
        checks = GitHubChecksService()

        # Create check run when PR is opened
        check_run = await checks.create_check_run(
            installation_id=123,
            repo_owner="org",
            repo_name="repo",
            head_sha="abc123",
            gate_id="G3",
        )

        # Update as evaluation progresses
        await checks.update_check_run(
            installation_id=123,
            repo_owner="org",
            repo_name="repo",
            check_run_id=check_run["id"],
            status=CheckRunStatus.IN_PROGRESS,
        )

        # Complete with result
        await checks.complete_check_run(
            installation_id=123,
            repo_owner="org",
            repo_name="repo",
            check_run_id=check_run["id"],
            conclusion=CheckRunConclusion.FAILURE,
            summary="Gate G3 failed: 3 policy violations",
            details=policy_violations_markdown,
        )
    """

    def __init__(self):
        """Initialize GitHub Checks service with App configuration."""
        self.app_id = getattr(settings, "GITHUB_APP_ID", None)
        self.private_key = getattr(settings, "GITHUB_APP_PRIVATE_KEY", None)
        self.timeout = 30
        self.base_url = GITHUB_API_BASE_URL

        if not self.app_id or not self.private_key:
            logger.warning(
                "GitHub App not configured. Check Run enforcement will be disabled."
            )

        logger.info("GitHub Checks service initialized")

    # ============================================================================
    # Installation Token Management
    # ============================================================================

    def get_installation_token(self, installation_id: int) -> str:
        """
        Get installation access token for GitHub App.

        GitHub Apps use installation tokens (not OAuth tokens) to authenticate.
        Installation tokens have repository-specific permissions.

        Args:
            installation_id: GitHub App installation ID (from webhook)

        Returns:
            Installation access token (valid for 1 hour)

        Raises:
            GitHubAppNotInstalledError: If installation not found
            GitHubChecksAPIError: If token request fails
        """
        if not self.app_id or not self.private_key:
            raise GitHubChecksAPIError(
                "GitHub App credentials not configured. "
                "Set GITHUB_APP_ID and GITHUB_APP_PRIVATE_KEY."
            )

        try:
            import jwt
            from datetime import timedelta

            # Create JWT for App authentication
            now = datetime.now(timezone.utc)
            payload = {
                "iat": int(now.timestamp()),
                "exp": int((now + timedelta(minutes=10)).timestamp()),
                "iss": self.app_id,
            }
            app_token = jwt.encode(payload, self.private_key, algorithm="RS256")

            # Request installation token
            response = requests.post(
                f"{self.base_url}/app/installations/{installation_id}/access_tokens",
                headers={
                    "Authorization": f"Bearer {app_token}",
                    "Accept": "application/vnd.github.v3+json",
                },
                timeout=self.timeout,
            )

            if response.status_code == 404:
                raise GitHubAppNotInstalledError(
                    f"GitHub App not installed for installation_id={installation_id}"
                )

            if response.status_code != 201:
                logger.error(
                    f"Failed to get installation token: {response.status_code}"
                )
                raise GitHubChecksAPIError(
                    f"Installation token request failed: {response.text}"
                )

            data = response.json()
            return data["token"]

        except ImportError:
            raise GitHubChecksAPIError(
                "PyJWT not installed. Run: pip install PyJWT"
            )
        except Exception as e:
            logger.error(f"Installation token error: {e}")
            raise GitHubChecksAPIError(f"Failed to get installation token: {e}")

    # ============================================================================
    # Check Run Operations
    # ============================================================================

    def create_check_run(
        self,
        installation_id: int,
        repo_owner: str,
        repo_name: str,
        head_sha: str,
        gate_id: str,
        external_id: Optional[str] = None,
        details_url: Optional[str] = None,
    ) -> dict[str, Any]:
        """
        Create a new Check Run for SDLC gate evaluation.

        When a PR is opened or updated, create a check run to indicate
        gate evaluation is starting. This immediately shows in the PR
        as "pending" status.

        Args:
            installation_id: GitHub App installation ID
            repo_owner: Repository owner (user or org)
            repo_name: Repository name
            head_sha: Commit SHA to create check for
            gate_id: SDLC gate identifier (e.g., "G3", "G-Sprint")
            external_id: Optional SDLC Orchestrator gate evaluation ID
            details_url: URL to full gate evaluation details

        Returns:
            Check Run object:
            {
                "id": 123456,
                "head_sha": "abc123...",
                "status": "queued",
                "conclusion": null,
                "started_at": "2026-01-19T10:00:00Z",
                "html_url": "https://github.com/..."
            }

        Example:
            check_run = checks.create_check_run(
                installation_id=123,
                repo_owner="nqh",
                repo_name="sdlc-orchestrator",
                head_sha="abc123def456",
                gate_id="G3",
            )
        """
        token = self.get_installation_token(installation_id)

        payload = {
            "name": f"SDLC Gate: {gate_id}",
            "head_sha": head_sha,
            "status": CheckRunStatus.QUEUED.value,
            "started_at": datetime.now(timezone.utc).isoformat(),
            "output": {
                "title": f"Evaluating {gate_id}...",
                "summary": f"SDLC Orchestrator is evaluating gate {gate_id} policies.",
            },
        }

        if external_id:
            payload["external_id"] = external_id

        if details_url:
            payload["details_url"] = details_url

        response = self._make_request(
            token=token,
            method="POST",
            endpoint=f"/repos/{repo_owner}/{repo_name}/check-runs",
            data=payload,
        )

        logger.info(
            f"Created Check Run {response['id']} for {repo_owner}/{repo_name} "
            f"gate={gate_id} sha={head_sha[:8]}"
        )

        return response

    def update_check_run(
        self,
        installation_id: int,
        repo_owner: str,
        repo_name: str,
        check_run_id: int,
        status: CheckRunStatus,
        output_title: Optional[str] = None,
        output_summary: Optional[str] = None,
    ) -> dict[str, Any]:
        """
        Update an existing Check Run status.

        Use this to indicate evaluation is in progress, update summary,
        or transition between states.

        Args:
            installation_id: GitHub App installation ID
            repo_owner: Repository owner
            repo_name: Repository name
            check_run_id: Check Run ID to update
            status: New status (queued, in_progress, completed)
            output_title: Optional updated title
            output_summary: Optional updated summary

        Returns:
            Updated Check Run object

        Example:
            checks.update_check_run(
                installation_id=123,
                repo_owner="nqh",
                repo_name="repo",
                check_run_id=456,
                status=CheckRunStatus.IN_PROGRESS,
                output_title="Evaluating policies...",
                output_summary="Running 42 policy checks",
            )
        """
        token = self.get_installation_token(installation_id)

        payload: dict[str, Any] = {
            "status": status.value,
        }

        if output_title or output_summary:
            payload["output"] = {}
            if output_title:
                payload["output"]["title"] = output_title
            if output_summary:
                payload["output"]["summary"] = output_summary

        response = self._make_request(
            token=token,
            method="PATCH",
            endpoint=f"/repos/{repo_owner}/{repo_name}/check-runs/{check_run_id}",
            data=payload,
        )

        logger.info(
            f"Updated Check Run {check_run_id} to status={status.value}"
        )

        return response

    def complete_check_run(
        self,
        installation_id: int,
        repo_owner: str,
        repo_name: str,
        check_run_id: int,
        conclusion: CheckRunConclusion,
        title: str,
        summary: str,
        text: Optional[str] = None,
        annotations: Optional[list[dict[str, Any]]] = None,
    ) -> dict[str, Any]:
        """
        Complete a Check Run with final result.

        This is the critical method for gate enforcement:
        - conclusion=SUCCESS: Merge allowed (if branch protection requires this check)
        - conclusion=FAILURE: Merge blocked!
        - conclusion=ACTION_REQUIRED: Merge blocked until action taken

        Args:
            installation_id: GitHub App installation ID
            repo_owner: Repository owner
            repo_name: Repository name
            check_run_id: Check Run ID to complete
            conclusion: Final result (success, failure, neutral, etc.)
            title: Summary title (shown in PR checks section)
            summary: Summary text (markdown supported)
            text: Detailed text (markdown, for expandable details)
            annotations: Optional code annotations for inline comments

        Returns:
            Completed Check Run object

        Example (Gate passed):
            checks.complete_check_run(
                installation_id=123,
                repo_owner="nqh",
                repo_name="repo",
                check_run_id=456,
                conclusion=CheckRunConclusion.SUCCESS,
                title="Gate G3 Passed",
                summary="All 42 policy checks passed. Ready to merge.",
            )

        Example (Gate failed - BLOCKS MERGE):
            checks.complete_check_run(
                installation_id=123,
                repo_owner="nqh",
                repo_name="repo",
                check_run_id=456,
                conclusion=CheckRunConclusion.FAILURE,
                title="Gate G3 Failed",
                summary="3 policy violations found",
                text=violation_details_markdown,
                annotations=[
                    {
                        "path": "src/auth.py",
                        "start_line": 42,
                        "end_line": 42,
                        "annotation_level": "failure",
                        "message": "Hardcoded secret detected",
                    }
                ],
            )
        """
        token = self.get_installation_token(installation_id)

        payload: dict[str, Any] = {
            "status": CheckRunStatus.COMPLETED.value,
            "conclusion": conclusion.value,
            "completed_at": datetime.now(timezone.utc).isoformat(),
            "output": {
                "title": title,
                "summary": summary,
            },
        }

        if text:
            payload["output"]["text"] = text

        if annotations:
            # GitHub limits to 50 annotations per request
            payload["output"]["annotations"] = annotations[:50]

        response = self._make_request(
            token=token,
            method="PATCH",
            endpoint=f"/repos/{repo_owner}/{repo_name}/check-runs/{check_run_id}",
            data=payload,
        )

        logger.info(
            f"Completed Check Run {check_run_id} with conclusion={conclusion.value}"
        )

        return response

    # ============================================================================
    # Dynamic Context Overlay
    # ============================================================================

    def format_context_overlay(
        self,
        stage: str,
        gate_status: str,
        sprint_number: Optional[int] = None,
        constraints: Optional[list[str]] = None,
        risky_files: Optional[list[str]] = None,
    ) -> str:
        """
        Format dynamic context overlay for Check Run output.

        This delivers the "dynamic overlay" part of ADR-029 architecture:
        - AI coders see this context in PR checks
        - Provides stage-aware constraints
        - Lists files under review

        Args:
            stage: Current SDLC stage (e.g., "Stage 04 (BUILD)")
            gate_status: Current gate status (e.g., "G3 PASSED")
            sprint_number: Optional current sprint number
            constraints: List of active constraints
            risky_files: List of files under security review

        Returns:
            Markdown formatted context overlay

        Example:
            overlay = checks.format_context_overlay(
                stage="Stage 04 (BUILD)",
                gate_status="G3 IN_PROGRESS",
                sprint_number=79,
                constraints=[
                    "Post-G2: Only bug fixes allowed",
                    "Security review in progress for auth_service.py",
                ],
                risky_files=["backend/app/services/auth_service.py"],
            )
        """
        now = datetime.now(timezone.utc)
        lines = [
            "## SDLC Context (Dynamic Overlay)",
            "",
            f"**Generated**: {now.strftime('%b %d, %Y %H:%M UTC')}",
            f"**Stage**: {stage}",
            f"**Gate**: {gate_status}",
        ]

        if sprint_number:
            lines.append(f"**Sprint**: {sprint_number}")

        if constraints:
            lines.extend([
                "",
                "### Active Constraints",
                "",
            ])
            for constraint in constraints:
                lines.append(f"- {constraint}")

        if risky_files:
            lines.extend([
                "",
                "### Files Under Review (DO NOT MODIFY)",
                "",
            ])
            for file_path in risky_files:
                lines.append(f"- `{file_path}`")

        lines.extend([
            "",
            "---",
            "*This context is automatically generated by SDLC Orchestrator.*",
            "*Static rules in AGENTS.md. Dynamic context here.*",
        ])

        return "\n".join(lines)

    def format_policy_violations(
        self,
        violations: list[dict[str, Any]],
    ) -> tuple[str, list[dict[str, Any]]]:
        """
        Format policy violations for Check Run output.

        Converts internal violation format to GitHub Check Run format
        with summary markdown and code annotations.

        Args:
            violations: List of violation dicts:
                [
                    {
                        "rule_id": "AI-001",
                        "severity": "ERROR",
                        "message": "Hardcoded secret detected",
                        "file_path": "src/auth.py",
                        "line": 42,
                    }
                ]

        Returns:
            Tuple of (summary_markdown, annotations_list)

        Example:
            summary, annotations = checks.format_policy_violations(violations)
            checks.complete_check_run(
                ...,
                conclusion=CheckRunConclusion.FAILURE,
                title=f"{len(violations)} policy violations",
                summary=summary,
                annotations=annotations,
            )
        """
        if not violations:
            return "No policy violations found.", []

        # Group by severity
        errors = [v for v in violations if v.get("severity") == "ERROR"]
        warnings = [v for v in violations if v.get("severity") == "WARNING"]

        lines = [
            f"## Policy Violations: {len(violations)} total",
            "",
            f"- **Errors**: {len(errors)} (blocking)",
            f"- **Warnings**: {len(warnings)} (advisory)",
            "",
            "### Details",
            "",
        ]

        for v in violations:
            severity_icon = "X" if v.get("severity") == "ERROR" else "!"
            lines.append(
                f"- [{severity_icon}] **{v.get('rule_id', 'Unknown')}** "
                f"in `{v.get('file_path', 'unknown')}:{v.get('line', 0)}`: "
                f"{v.get('message', 'No message')}"
            )

        summary = "\n".join(lines)

        # Create annotations for inline comments
        annotations = []
        for v in violations:
            if v.get("file_path") and v.get("line"):
                annotation_level = (
                    "failure" if v.get("severity") == "ERROR" else "warning"
                )
                annotations.append({
                    "path": v["file_path"],
                    "start_line": v["line"],
                    "end_line": v.get("end_line", v["line"]),
                    "annotation_level": annotation_level,
                    "message": f"[{v.get('rule_id', 'Policy')}] {v.get('message', '')}",
                    "title": v.get("rule_id", "Policy Violation"),
                })

        return summary, annotations

    # ============================================================================
    # Private Methods
    # ============================================================================

    def _make_request(
        self,
        token: str,
        method: str,
        endpoint: str,
        data: Optional[dict] = None,
    ) -> dict[str, Any]:
        """
        Make authenticated request to GitHub Checks API.

        Args:
            token: Installation access token
            method: HTTP method
            endpoint: API endpoint
            data: Request body

        Returns:
            Response JSON

        Raises:
            GitHubChecksAPIError: If request fails
        """
        url = f"{self.base_url}{endpoint}"
        headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github.v3+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }

        try:
            response = requests.request(
                method=method,
                url=url,
                headers=headers,
                json=data,
                timeout=self.timeout,
            )

            if response.status_code >= 400:
                error_msg = response.json().get("message", response.text)
                logger.error(
                    f"GitHub Checks API error: {response.status_code} {error_msg}"
                )
                raise GitHubChecksAPIError(
                    f"API error ({response.status_code}): {error_msg}"
                )

            return response.json()

        except Timeout:
            logger.error(f"GitHub Checks API timeout: {endpoint}")
            raise GitHubChecksAPIError(f"Request timed out: {endpoint}")

        except RequestException as e:
            logger.error(f"GitHub Checks API request failed: {e}")
            raise GitHubChecksAPIError(f"Request failed: {e}")


# ============================================================================
# Singleton Instance
# ============================================================================

github_checks_service = GitHubChecksService()
