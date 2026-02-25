"""
Unit Tests for update_sprint command — Sprint 194 (ENR-01).

Tests:
- Command registered in registry (slot 6 of 10)
- Handler returns success for active sprint
- Handler returns error for missing project
- Handler returns error for no active sprint
- Handler includes commit_sha when GitHub push succeeds
- Handler skips push when no GitHub repo
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

from app.services.agent_team.command_registry import (
    GOVERNANCE_COMMANDS,
    MAX_COMMANDS,
    ToolName,
    get_command,
)


class TestUpdateSprintRegistration:
    """Test update_sprint is properly registered in the command registry."""

    def test_update_sprint_in_tool_name_enum(self):
        """ToolName enum includes UPDATE_SPRINT."""
        assert hasattr(ToolName, "UPDATE_SPRINT")
        assert ToolName.UPDATE_SPRINT.value == "update_sprint"

    def test_update_sprint_in_governance_commands(self):
        """update_sprint is in GOVERNANCE_COMMANDS list."""
        names = [cmd.name for cmd in GOVERNANCE_COMMANDS]
        assert "update_sprint" in names

    def test_registry_has_10_commands(self):
        """Registry now has 10 commands (8 prior + run_evals + list_notes — Sprint 202)."""
        assert len(GOVERNANCE_COMMANDS) == 10

    def test_registry_under_max_limit(self):
        """Registry is still under the 10-command limit."""
        assert len(GOVERNANCE_COMMANDS) <= MAX_COMMANDS

    def test_get_command_returns_update_sprint(self):
        """get_command('update_sprint') returns the command definition."""
        cmd = get_command("update_sprint")
        assert cmd is not None
        assert cmd.name == "update_sprint"
        assert cmd.permission == "governance:write"
        assert cmd.cli_name == "update-sprint"

    def test_update_sprint_params_schema(self):
        """UpdateSprintParams requires project_id (UUID)."""
        cmd = get_command("update_sprint")
        assert cmd is not None
        validated = cmd.params.model_validate({"project_id": str(uuid4())})
        assert validated.project_id is not None

    def test_update_sprint_ott_aliases(self):
        """update_sprint has Vietnamese and English OTT aliases."""
        cmd = get_command("update_sprint")
        assert cmd is not None
        assert "cập nhật sprint" in cmd.ott_aliases
        assert "update sprint" in cmd.ott_aliases

    def test_required_params_includes_project_id(self):
        """project_id is a required parameter."""
        cmd = get_command("update_sprint")
        assert cmd is not None
        assert "project_id" in cmd.required_params


class TestHandleUpdateSprint:
    """Test handle_update_sprint handler function."""

    @pytest.fixture
    def db(self):
        """Mock async DB session."""
        return AsyncMock()

    @pytest.fixture
    def mock_project(self):
        """Mock Project with github_repo."""
        project = MagicMock()
        project.id = uuid4()
        project.github_repo = "org/repo"
        project.default_branch = "main"
        return project

    @pytest.fixture
    def mock_sprint(self):
        """Mock active Sprint."""
        sprint = MagicMock()
        sprint.name = "Sprint 194"
        sprint.sprint_number = 194
        sprint.status = "ACTIVE"
        sprint.backlog_items = []
        return sprint

    @pytest.mark.asyncio
    async def test_project_not_found(self, db):
        """Returns error when project does not exist."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        db.execute.return_value = mock_result

        from app.services.agent_team.sprint_command_handler import handle_update_sprint

        result = await handle_update_sprint(db, uuid4())
        assert result["status"] == "error"
        assert "not found" in result["message"]

    @pytest.mark.asyncio
    async def test_no_active_sprint(self, db, mock_project):
        """Returns error when no active sprint exists."""
        # First execute returns project, second returns no sprint
        results = [MagicMock(), MagicMock()]
        results[0].scalar_one_or_none.return_value = mock_project
        results[1].scalar_one_or_none.return_value = None
        db.execute.side_effect = results

        from app.services.agent_team.sprint_command_handler import handle_update_sprint

        result = await handle_update_sprint(db, mock_project.id)
        assert result["status"] == "error"
        assert "No active sprint" in result["message"]

    @pytest.mark.asyncio
    async def test_success_with_github_push(self, db, mock_project, mock_sprint):
        """Returns success with commit_sha when GitHub push succeeds."""
        results = [MagicMock(), MagicMock()]
        results[0].scalar_one_or_none.return_value = mock_project
        results[1].scalar_one_or_none.return_value = mock_sprint
        db.execute.side_effect = results

        mock_github = MagicMock()

        with patch(
            "app.services.agent_team.sprint_command_handler.SprintFileService"
        ) as MockSFS:
            mock_sfs = MockSFS.return_value
            mock_sfs.generate_current_sprint_md.return_value = "# Sprint 194\nContent"
            mock_sfs.push_to_github = AsyncMock(return_value="abc12345")

            from app.services.agent_team.sprint_command_handler import handle_update_sprint

            result = await handle_update_sprint(db, mock_project.id, github_service=mock_github)

        assert result["status"] == "success"
        assert result["sprint_name"] == "Sprint 194"
        assert result["commit_sha"] == "abc12345"
        assert "pushed to GitHub" in result["message"]

    @pytest.mark.asyncio
    async def test_success_without_github(self, db, mock_project, mock_sprint):
        """Returns success without commit_sha when no GitHub repo."""
        results = [MagicMock(), MagicMock()]
        results[0].scalar_one_or_none.return_value = mock_project
        results[1].scalar_one_or_none.return_value = mock_sprint
        db.execute.side_effect = results

        mock_github = MagicMock()

        with patch(
            "app.services.agent_team.sprint_command_handler.SprintFileService"
        ) as MockSFS:
            mock_sfs = MockSFS.return_value
            mock_sfs.generate_current_sprint_md.return_value = "# Sprint 194"
            mock_sfs.push_to_github = AsyncMock(return_value=None)

            from app.services.agent_team.sprint_command_handler import handle_update_sprint

            result = await handle_update_sprint(db, mock_project.id, github_service=mock_github)

        assert result["status"] == "success"
        assert result["commit_sha"] is None
        assert "skipped push" in result["message"]

    @pytest.mark.asyncio
    async def test_content_length_included(self, db, mock_project, mock_sprint):
        """Result includes content_length."""
        results = [MagicMock(), MagicMock()]
        results[0].scalar_one_or_none.return_value = mock_project
        results[1].scalar_one_or_none.return_value = mock_sprint
        db.execute.side_effect = results

        content = "# Sprint 194\n" * 100
        mock_github = MagicMock()

        with patch(
            "app.services.agent_team.sprint_command_handler.SprintFileService"
        ) as MockSFS:
            mock_sfs = MockSFS.return_value
            mock_sfs.generate_current_sprint_md.return_value = content
            mock_sfs.push_to_github = AsyncMock(return_value=None)

            from app.services.agent_team.sprint_command_handler import handle_update_sprint

            result = await handle_update_sprint(db, mock_project.id, github_service=mock_github)

        assert result["content_length"] == len(content)
