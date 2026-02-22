"""
=========================================================================
Unit Tests for SprintFileService — Sprint 193 Phase 1
SDLC Orchestrator - Sprint 193 (Security Hardening & Automation)

SDLC Stage: 04 - BUILD
Sprint: 193 - Phase 1 Sprint File Service
Framework: SDLC 6.1.1

Purpose:
Tests for SprintFileService that generates CURRENT-SPRINT.md from Sprint
DB records and pushes to GitHub repos.

Test Coverage:
- Template generation (multiple sprint states)
- Backlog rendering (grouped by priority)
- Gate status display
- GitHub push flow (mock GitHub API)
- Freshness verification (fresh/stale/missing/no-repo)
- Guard: projects without GitHub repos don't crash
=========================================================================
"""

import pytest
from datetime import date
from unittest.mock import Mock, AsyncMock, patch
from uuid import uuid4

from app.services.sprint_file_service import SprintFileService, CURRENT_SPRINT_PATH
from app.services.github_service import GitHubAPIError


# =============================================================================
# Fixtures
# =============================================================================


def make_sprint(**overrides):
    """Create a mock Sprint with sensible defaults."""
    sprint = Mock()
    sprint.id = overrides.get("id", uuid4())
    sprint.number = overrides.get("number", 193)
    sprint.name = overrides.get("name", "Security Hardening & Automation")
    sprint.goal = overrides.get("goal", "Resolve all Sprint 192 findings and add seed agent definitions")
    sprint.status = overrides.get("status", "active")
    sprint.start_date = overrides.get("start_date", date(2026, 2, 23))
    sprint.end_date = overrides.get("end_date", date(2026, 3, 6))
    sprint.capacity_points = overrides.get("capacity_points", 40)
    sprint.team_size = overrides.get("team_size", 3)
    sprint.velocity_target = overrides.get("velocity_target", 35)
    sprint.g_sprint_status = overrides.get("g_sprint_status", "passed")
    sprint.g_sprint_close_status = overrides.get("g_sprint_close_status", "pending")
    sprint.backlog_items = overrides.get("backlog_items", [])
    sprint.documentation_deadline = overrides.get("documentation_deadline", None)
    sprint.project_id = overrides.get("project_id", uuid4())
    return sprint


def make_backlog_item(title, priority="P1", item_type="task", points=3, status="todo"):
    """Create a mock BacklogItem."""
    item = Mock()
    item.title = title
    item.priority = priority
    item.type = item_type
    item.story_points = points
    item.status = status
    return item


def make_project(**overrides):
    """Create a mock Project with GitHub integration."""
    project = Mock()
    project.id = overrides.get("id", uuid4())
    project.name = overrides.get("name", "Acme Platform")
    project.slug = overrides.get("slug", "acme-platform")
    project.github_repo = overrides.get("github_repo", "acme-corp/platform")
    project.default_branch = overrides.get("default_branch", "main")
    project.github_repository = overrides.get("github_repository", None)
    return project


# =============================================================================
# Template Generation Tests
# =============================================================================


class TestGenerateCurrentSprintMd:
    """Test CURRENT-SPRINT.md template generation."""

    def setup_method(self):
        self.db = AsyncMock()
        self.github_service = Mock(spec_set=["get_file_content", "update_file", "create_update_pr", "_make_request"])
        self.service = SprintFileService(db=self.db, github_service=self.github_service)

    def test_generates_header_with_sprint_identity(self):
        """Header includes sprint number, name, status, dates."""
        sprint = make_sprint(number=193, name="Security Hardening")
        project = make_project(name="SDLC Orchestrator")

        content = self.service.generate_current_sprint_md(sprint, project)

        assert "# Current Sprint: Sprint 193 — Security Hardening" in content
        assert "**Status**: ACTIVE" in content
        assert "February 23" in content
        assert "March 06, 2026" in content
        assert "**Project**: SDLC Orchestrator" in content

    def test_generates_goal_section(self):
        """Goal section includes the sprint goal."""
        sprint = make_sprint(goal="Fix all P0 bugs and deploy agent definitions")
        project = make_project()

        content = self.service.generate_current_sprint_md(sprint, project)

        assert "## Sprint 193 Goal" in content
        assert "Fix all P0 bugs and deploy agent definitions" in content

    def test_generates_backlog_table_grouped_by_priority(self):
        """Backlog section groups items by priority with table format."""
        items = [
            make_backlog_item("Fix settings singleton", priority="P0", points=5),
            make_backlog_item("Update CI cache paths", priority="P1", points=3),
            make_backlog_item("Add empty-timestamp test", priority="P2", points=2),
        ]
        sprint = make_sprint(backlog_items=items)
        project = make_project()

        content = self.service.generate_current_sprint_md(sprint, project)

        assert "### P0 — Critical (must complete)" in content
        assert "Fix settings singleton" in content
        assert "### P1 — High Priority" in content
        assert "Update CI cache paths" in content
        assert "### P2 — Standard" in content
        assert "Add empty-timestamp test" in content

    def test_empty_backlog_shows_placeholder(self):
        """Empty backlog shows placeholder message."""
        sprint = make_sprint(backlog_items=[])
        project = make_project()

        content = self.service.generate_current_sprint_md(sprint, project)

        assert "*No backlog items defined yet.*" in content

    def test_generates_gate_status_table(self):
        """Gate status table shows G-Sprint and G-Sprint-Close status."""
        sprint = make_sprint(g_sprint_status="passed", g_sprint_close_status="pending")
        project = make_project()

        content = self.service.generate_current_sprint_md(sprint, project)

        assert "## G-Sprint Gate Status" in content
        assert "PASSED" in content
        assert "PENDING" in content

    def test_includes_previous_sprint_when_provided(self):
        """Previous sprint summary included when passed."""
        sprint = make_sprint(number=193)
        prev = make_sprint(number=192, name="Enterprise Hardening", status="completed")
        prev.backlog_items = [
            make_backlog_item("Task 1", status="done"),
            make_backlog_item("Task 2", status="done"),
            make_backlog_item("Task 3", status="in_progress"),
        ]
        project = make_project()

        content = self.service.generate_current_sprint_md(sprint, project, previous_sprint=prev)

        assert "## Previous Sprint Summary" in content
        assert "Sprint 192 — Enterprise Hardening" in content
        assert "2/3 completed" in content

    def test_footer_includes_framework_version(self):
        """Footer includes SDLC 6.1.1 and Rule 9 reference."""
        sprint = make_sprint()
        project = make_project()

        content = self.service.generate_current_sprint_md(sprint, project)

        assert "**Framework Version**: SDLC 6.1.1" in content
        assert "Rule 9" in content

    def test_planning_status_display(self):
        """Planning status shows PLANNED."""
        sprint = make_sprint(status="planning")
        project = make_project()

        content = self.service.generate_current_sprint_md(sprint, project)

        assert "**Status**: PLANNED" in content

    def test_completed_status_display(self):
        """Completed status shows COMPLETED."""
        sprint = make_sprint(status="completed")
        project = make_project()

        content = self.service.generate_current_sprint_md(sprint, project)

        assert "**Status**: COMPLETED" in content

    def test_capacity_and_team_size_shown_when_set(self):
        """Capacity and team size displayed when available."""
        sprint = make_sprint(capacity_points=40, team_size=3)
        project = make_project()

        content = self.service.generate_current_sprint_md(sprint, project)

        assert "**Capacity**: 40 story points" in content
        assert "**Team Size**: 3" in content

    def test_no_dates_shows_fallback(self):
        """Missing dates show 'Dates not set' fallback."""
        sprint = make_sprint(start_date=None, end_date=None)
        project = make_project()

        content = self.service.generate_current_sprint_md(sprint, project)

        assert "Dates not set" in content


# =============================================================================
# GitHub Push Tests
# =============================================================================


class TestPushToGitHub:
    """Test CURRENT-SPRINT.md push to GitHub."""

    def setup_method(self):
        self.db = AsyncMock()
        self.github_service = Mock()
        self.service = SprintFileService(db=self.db, github_service=self.github_service)

    @pytest.mark.asyncio
    async def test_returns_none_when_no_github_repo(self):
        """Push returns None for projects without GitHub repos."""
        project = make_project(github_repo=None)

        result = await self.service.push_to_github(project, "# Sprint 193")

        assert result is None
        self.github_service.update_file.assert_not_called()

    @pytest.mark.asyncio
    async def test_returns_none_when_no_installation_token(self):
        """Push returns None when installation token unavailable."""
        project = make_project(github_repository=None)

        result = await self.service.push_to_github(project, "# Sprint 193")

        assert result is None

    @pytest.mark.asyncio
    async def test_pushes_content_with_installation_token(self):
        """Push calls update_file with correct params when token available."""
        # Set up project with full GitHub App chain
        mock_installation = Mock()
        mock_installation.installation_id = 12345
        mock_gh_repo = Mock()
        mock_gh_repo.installation = mock_installation
        project = make_project(
            github_repo="acme-corp/platform",
            default_branch="main",
            github_repository=mock_gh_repo,
        )

        self.github_service.update_file.return_value = "abc123sha"

        with patch(
            "app.services.github_app_service.get_installation_token",
            new_callable=AsyncMock,
            return_value="ghs_test_token_123",
        ):
            result = await self.service.push_to_github(project, "# Sprint 193")

        assert result == "abc123sha"
        self.github_service.update_file.assert_called_once()
        call_kwargs = self.github_service.update_file.call_args
        assert call_kwargs.kwargs["owner"] == "acme-corp"
        assert call_kwargs.kwargs["repo"] == "platform"
        assert call_kwargs.kwargs["path"] == CURRENT_SPRINT_PATH
        assert call_kwargs.kwargs["content"] == "# Sprint 193"
        assert call_kwargs.kwargs["access_token"] == "ghs_test_token_123"

    @pytest.mark.asyncio
    async def test_handles_github_api_error_gracefully(self):
        """Push returns None on GitHub API error (no crash)."""
        mock_installation = Mock()
        mock_installation.installation_id = 12345
        mock_gh_repo = Mock()
        mock_gh_repo.installation = mock_installation
        project = make_project(
            github_repo="acme-corp/platform",
            github_repository=mock_gh_repo,
        )

        self.github_service.update_file.side_effect = GitHubAPIError("Server error")

        with patch(
            "app.services.github_app_service.get_installation_token",
            new_callable=AsyncMock,
            return_value="ghs_test_token",
        ):
            result = await self.service.push_to_github(project, "# Sprint 193")

        assert result is None


# =============================================================================
# Freshness Verification Tests
# =============================================================================


class TestVerifyFreshness:
    """Test CURRENT-SPRINT.md freshness verification."""

    def setup_method(self):
        self.db = AsyncMock()
        self.github_service = Mock()
        self.service = SprintFileService(db=self.db, github_service=self.github_service)

    @pytest.mark.asyncio
    async def test_returns_no_github_repo_when_unconfigured(self):
        """Verification returns reason=no_github_repo when no repo."""
        project = make_project(github_repo=None)
        sprint = make_sprint(number=193)

        result = await self.service.verify_freshness(project, sprint)

        assert result["fresh"] is False
        assert result["reason"] == "no_github_repo"

    @pytest.mark.asyncio
    async def test_returns_file_not_found_on_404(self):
        """Verification returns file_not_found when file missing."""
        mock_installation = Mock()
        mock_installation.installation_id = 12345
        mock_gh_repo = Mock()
        mock_gh_repo.installation = mock_installation
        project = make_project(
            github_repo="acme-corp/platform",
            github_repository=mock_gh_repo,
        )
        sprint = make_sprint(number=193)

        self.github_service.get_file_content.return_value = None

        with patch(
            "app.services.github_app_service.get_installation_token",
            new_callable=AsyncMock,
            return_value="ghs_token",
        ):
            result = await self.service.verify_freshness(project, sprint)

        assert result["fresh"] is False
        assert result["reason"] == "file_not_found"
        assert result["file_exists"] is False

    @pytest.mark.asyncio
    async def test_returns_fresh_when_sprint_matches(self):
        """Verification returns fresh=True when file references correct sprint."""
        mock_installation = Mock()
        mock_installation.installation_id = 12345
        mock_gh_repo = Mock()
        mock_gh_repo.installation = mock_installation
        project = make_project(
            github_repo="acme-corp/platform",
            github_repository=mock_gh_repo,
        )
        sprint = make_sprint(number=193)

        self.github_service.get_file_content.return_value = {
            "content": "# Current Sprint: Sprint 193 — Security Hardening\n...",
            "sha": "file_sha_abc",
        }

        with patch(
            "app.services.github_app_service.get_installation_token",
            new_callable=AsyncMock,
            return_value="ghs_token",
        ):
            result = await self.service.verify_freshness(project, sprint)

        assert result["fresh"] is True
        assert result["sprint_match"] is True
        assert result["file_exists"] is True
        assert result["sha"] == "file_sha_abc"

    @pytest.mark.asyncio
    async def test_returns_stale_when_sprint_mismatch(self):
        """Verification detects stale file with wrong sprint number."""
        mock_installation = Mock()
        mock_installation.installation_id = 12345
        mock_gh_repo = Mock()
        mock_gh_repo.installation = mock_installation
        project = make_project(
            github_repo="acme-corp/platform",
            github_repository=mock_gh_repo,
        )
        sprint = make_sprint(number=193)

        self.github_service.get_file_content.return_value = {
            "content": "# Current Sprint: Sprint 175 — Old Sprint\n...",
            "sha": "old_sha",
        }

        with patch(
            "app.services.github_app_service.get_installation_token",
            new_callable=AsyncMock,
            return_value="ghs_token",
        ):
            result = await self.service.verify_freshness(project, sprint)

        assert result["fresh"] is False
        assert result["reason"] == "stale_sprint_reference"
        assert result["sprint_match"] is False
        assert result["file_exists"] is True
