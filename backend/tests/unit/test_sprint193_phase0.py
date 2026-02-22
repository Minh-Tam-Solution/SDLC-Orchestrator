"""
=========================================================================
Unit Tests for Sprint 193 Phase 0 — P0 Bug Fixes
SDLC Orchestrator - Sprint 193 (Security Hardening & Automation)

SDLC Stage: 04 - BUILD
Sprint: 193 - Phase 0 Pre-existing Bug Fixes
Framework: SDLC 6.1.1

Purpose:
Regression tests for 6 pre-existing production bugs discovered during
CURRENT-SPRINT.md enforcement planning:
- B1-B4: DynamicContextService GitHub push dead code (AttributeError)
- B5: Gate serializer checked vs passed field mismatch
- B6: Stale SDLC 5.1.3 version strings

Test Coverage Target: 95%+
=========================================================================
"""

import base64
import copy
import pytest
from unittest.mock import Mock, patch
from uuid import uuid4

from app.models.project import Project
from app.models.sprint_gate_evaluation import (
    SprintGateEvaluation,
    G_SPRINT_CHECKLIST_TEMPLATE,
    G_SPRINT_CLOSE_CHECKLIST_TEMPLATE,
)
from app.services.github_service import GitHubService, GitHubAPIError


# =============================================================================
# Phase 0a Tests: Project Model Property Aliases
# =============================================================================


class TestProjectGitHubProperties:
    """Test Project.github_repo and Project.default_branch properties (B3, B4)."""

    def test_github_repo_returns_full_name_from_legacy_field(self):
        """github_repo falls back to github_repo_full_name when no GitHubRepository."""
        project = Project(
            name="Test",
            slug="test",
            owner_id=uuid4(),
            github_repo_full_name="acme-corp/my-project",
        )
        # No github_repository relationship loaded
        assert project.github_repo == "acme-corp/my-project"

    def test_github_repo_returns_none_when_no_github(self):
        """github_repo returns None when no GitHub integration configured."""
        project = Project(
            name="Test",
            slug="test",
            owner_id=uuid4(),
        )
        assert project.github_repo is None

    def test_github_repo_prefers_github_repository_relationship(self):
        """github_repo delegates to GitHubRepository.full_name when available."""
        project = Project(
            name="Test",
            slug="test",
            owner_id=uuid4(),
            github_repo_full_name="old-name/repo",
        )
        # Bypass SQLAlchemy instrumentation — inject mock into instance dict
        mock_gh_repo = Mock()
        mock_gh_repo.full_name = "new-owner/new-repo"
        project.__dict__["github_repository"] = mock_gh_repo

        assert project.github_repo == "new-owner/new-repo"

    def test_default_branch_returns_main_when_no_github(self):
        """default_branch returns 'main' when no GitHub integration."""
        project = Project(
            name="Test",
            slug="test",
            owner_id=uuid4(),
        )
        assert project.default_branch == "main"

    def test_default_branch_from_github_repository(self):
        """default_branch delegates to GitHubRepository.default_branch."""
        project = Project(
            name="Test",
            slug="test",
            owner_id=uuid4(),
        )
        # Bypass SQLAlchemy instrumentation — inject mock into instance dict
        mock_gh_repo = Mock()
        mock_gh_repo.default_branch = "develop"
        project.__dict__["github_repository"] = mock_gh_repo

        assert project.default_branch == "develop"


# =============================================================================
# Phase 0b Tests: GitHub File Methods
# =============================================================================


class TestGitHubServiceFileOperations:
    """Test get_file_content, update_file, create_update_pr (B1, B2)."""

    @pytest.fixture
    def github_service(self):
        """Create GitHubService with mocked settings."""
        with patch("app.services.github_service.settings") as mock_settings:
            mock_settings.GITHUB_CLIENT_ID = "test_client_id"
            mock_settings.GITHUB_CLIENT_SECRET = "test_secret"
            service = GitHubService()
        return service

    def test_get_file_content_returns_decoded(self, github_service):
        """get_file_content decodes base64 content and returns sha."""
        test_content = "# CURRENT-SPRINT.md\nSprint 193"
        encoded = base64.b64encode(test_content.encode("utf-8")).decode("utf-8")

        with patch.object(github_service, "_make_request") as mock_req:
            mock_req.return_value = {
                "type": "file",
                "content": encoded,
                "sha": "abc123sha",
                "size": len(test_content),
                "path": "CURRENT-SPRINT.md",
            }

            result = github_service.get_file_content(
                access_token="token",
                owner="acme",
                repo="project",
                path="CURRENT-SPRINT.md",
            )

            assert result["content"] == test_content
            assert result["sha"] == "abc123sha"
            mock_req.assert_called_once()

    def test_get_file_content_returns_none_on_404(self, github_service):
        """get_file_content returns None when file doesn't exist."""
        with patch.object(github_service, "_make_request") as mock_req:
            mock_req.side_effect = GitHubAPIError("Resource not found")

            result = github_service.get_file_content(
                access_token="token",
                owner="acme",
                repo="project",
                path="nonexistent.md",
            )

            assert result is None

    def test_get_file_content_with_branch_ref(self, github_service):
        """get_file_content passes ref parameter for branch selection."""
        with patch.object(github_service, "_make_request") as mock_req:
            mock_req.return_value = {
                "type": "file",
                "content": base64.b64encode(b"test").decode(),
                "sha": "sha",
                "size": 4,
                "path": "test.md",
            }

            github_service.get_file_content(
                access_token="token",
                owner="acme",
                repo="project",
                path="test.md",
                ref="develop",
            )

            call_kwargs = mock_req.call_args
            assert call_kwargs.kwargs.get("params") == {"ref": "develop"} or \
                   call_kwargs[1].get("params") == {"ref": "develop"}

    def test_update_file_creates_new_file(self, github_service):
        """update_file creates file when it doesn't exist (no sha)."""
        with patch.object(github_service, "_make_request") as mock_req, \
             patch.object(github_service, "get_file_content", return_value=None):

            mock_req.return_value = {
                "commit": {"sha": "new_commit_sha"},
                "content": {"sha": "file_sha"},
            }

            result = github_service.update_file(
                access_token="token",
                owner="acme",
                repo="project",
                path="CURRENT-SPRINT.md",
                content="# Sprint 193",
                message="chore: update sprint file",
            )

            assert result == "new_commit_sha"
            call_data = mock_req.call_args.kwargs.get("data") or mock_req.call_args[1].get("data")
            assert "sha" not in call_data  # No sha for new file

    def test_update_file_includes_sha_for_existing(self, github_service):
        """update_file includes sha when updating existing file."""
        with patch.object(github_service, "_make_request") as mock_req, \
             patch.object(github_service, "get_file_content", return_value={"sha": "existing_sha"}):

            mock_req.return_value = {
                "commit": {"sha": "updated_sha"},
            }

            result = github_service.update_file(
                access_token="token",
                owner="acme",
                repo="project",
                path="CURRENT-SPRINT.md",
                content="# Sprint 193 Updated",
                message="chore: update sprint",
            )

            assert result == "updated_sha"
            call_data = mock_req.call_args.kwargs.get("data") or mock_req.call_args[1].get("data")
            assert call_data["sha"] == "existing_sha"

    def test_create_update_pr_full_flow(self, github_service):
        """create_update_pr creates branch, commits, and opens PR."""
        with patch.object(github_service, "_make_request") as mock_req, \
             patch.object(github_service, "update_file", return_value="commit_sha"):

            # Mock responses for: get base ref, create branch, create PR
            mock_req.side_effect = [
                {"object": {"sha": "base_sha123"}},  # GET base ref
                {"ref": "refs/heads/..."},             # POST create branch
                {"html_url": "https://github.com/acme/project/pull/42"},  # POST create PR
            ]

            result = github_service.create_update_pr(
                access_token="token",
                owner="acme",
                repo="project",
                path="CURRENT-SPRINT.md",
                content="# Sprint 193",
                title="chore: Update CURRENT-SPRINT.md",
                body="Auto-update by SDLC Orchestrator",
            )

            assert result == "https://github.com/acme/project/pull/42"
            assert mock_req.call_count == 3  # base ref + create branch + create PR


# =============================================================================
# Phase 0c Tests: Gate Serializer Field Mismatch Fix
# =============================================================================


class TestGateEvaluationSerializer:
    """Test _serialize_gate_evaluation uses 'passed' field (B5)."""

    def test_serializer_counts_passed_items(self):
        """Serializer correctly counts items with passed=True."""
        from app.api.routes.planning import _serialize_gate_evaluation

        checklist = copy.deepcopy(G_SPRINT_CHECKLIST_TEMPLATE)
        # Mark 3 items as passed
        checklist["alignment"][0]["passed"] = True
        checklist["alignment"][1]["passed"] = True
        checklist["capacity"][0]["passed"] = True

        evaluation = Mock(spec=SprintGateEvaluation)
        evaluation.id = uuid4()
        evaluation.sprint_id = uuid4()
        evaluation.gate_type = "g_sprint"
        evaluation.status = "pending"
        evaluation.checklist = checklist
        evaluation.notes = None
        evaluation.evaluated_by = None
        evaluation.evaluated_at = None
        evaluation.created_at = None

        result = _serialize_gate_evaluation(evaluation)

        assert result["passed_count"] == 3
        assert result["all_items_passed"] is False
        assert result["total_count"] > 0

    def test_serializer_all_passed_when_complete(self):
        """Serializer returns all_items_passed=True when all items pass."""
        from app.api.routes.planning import _serialize_gate_evaluation

        checklist = copy.deepcopy(G_SPRINT_CHECKLIST_TEMPLATE)
        # Mark ALL items as passed
        for category_items in checklist.values():
            for item in category_items:
                item["passed"] = True

        evaluation = Mock(spec=SprintGateEvaluation)
        evaluation.id = uuid4()
        evaluation.sprint_id = uuid4()
        evaluation.gate_type = "g_sprint"
        evaluation.status = "passed"
        evaluation.checklist = checklist
        evaluation.notes = None
        evaluation.evaluated_by = None
        evaluation.evaluated_at = None
        evaluation.created_at = None

        result = _serialize_gate_evaluation(evaluation)

        assert result["all_items_passed"] is True
        assert result["passed_count"] == result["total_count"]

    def test_serializer_ignores_none_items(self):
        """Serializer does not count None (unevaluated) as passed."""
        from app.api.routes.planning import _serialize_gate_evaluation

        checklist = copy.deepcopy(G_SPRINT_CLOSE_CHECKLIST_TEMPLATE)
        # All items have passed=None by default (unevaluated)

        evaluation = Mock(spec=SprintGateEvaluation)
        evaluation.id = uuid4()
        evaluation.sprint_id = uuid4()
        evaluation.gate_type = "g_sprint_close"
        evaluation.status = "pending"
        evaluation.checklist = checklist
        evaluation.notes = None
        evaluation.evaluated_by = None
        evaluation.evaluated_at = None
        evaluation.created_at = None

        result = _serialize_gate_evaluation(evaluation)

        assert result["passed_count"] == 0
        assert result["all_items_passed"] is False


# =============================================================================
# Phase 0e Tests: Version String
# =============================================================================


class TestVersionStrings:
    """Test stale version strings are updated (B6)."""

    def test_no_sdlc_513_references_in_planning_route(self):
        """Verify no SDLC 5.1.3 references remain in planning.py."""
        import inspect
        from app.api.routes import planning

        source = inspect.getsource(planning)
        assert "SDLC 5.1.3" not in source, \
            "Found stale 'SDLC 5.1.3' reference in planning.py — should be 'SDLC 6.1.1'"

    def test_gate_evaluation_template_version(self):
        """Verify sprint_gate_evaluation.py references SDLC 6.1.1."""
        import inspect
        from app.models import sprint_gate_evaluation

        source = inspect.getsource(sprint_gate_evaluation)
        assert "SDLC 6.1.1" in source
