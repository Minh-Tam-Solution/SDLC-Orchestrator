"""
=========================================================================
Unit Tests - GitHub Check Run Service (Sprint 81)
SDLC Orchestrator - Stage 04 (BUILD)

Version: 1.0.0
Date: January 19, 2026
Status: ACTIVE - Sprint 81 Implementation
Authority: QA Lead + Backend Lead Approved
Reference: TDS-081-001 GitHub Check Run Integration

Purpose:
- Test Check Run creation
- Test Check Run output formatting
- Test conclusion determination
- Test integration with overlay service

Unit Coverage: 10 test cases
=========================================================================
"""

from datetime import datetime, timezone
from unittest.mock import MagicMock, AsyncMock, patch
from uuid import uuid4

import pytest

from app.services.github_check_run_service import (
    GitHubCheckRunService,
    CheckRunOutput,
    CheckRunAnnotation,
    CheckRunResult,
    CheckRunCreateError,
    CheckRunUpdateError,
)


class TestCheckRunOutput:
    """Test Check Run output building."""

    def test_build_output_minimal(self):
        """Test building output with minimal data."""
        service = GitHubCheckRunService()

        output = service._build_output(overlay=None, gate_result=None)

        assert output.title == "Stage: Unknown | Gate: N/A"
        assert "SDLC Context Overlay" in output.summary
        assert len(output.annotations) == 0

    def test_build_output_with_overlay(self):
        """Test building output with overlay data."""
        service = GitHubCheckRunService()

        overlay = {
            "stage_name": "BUILD",
            "gate_status": "G3 PASSED",
            "strict_mode": True,
            "sprint": {
                "number": 81,
                "goal": "AGENTS.md Integration",
                "days_remaining": 5,
            },
            "constraints": [
                {
                    "type": "security_scan",
                    "severity": "warning",
                    "message": "SAST scan pending",
                },
                {
                    "type": "test_coverage",
                    "severity": "info",
                    "message": "Coverage at 94%",
                },
            ],
        }

        output = service._build_output(overlay=overlay, gate_result=None)

        assert "BUILD" in output.title
        assert "G3 PASSED" in output.title
        assert "STRICT MODE" in output.title
        assert "Sprint" in output.summary
        assert "81" in output.summary
        assert "security_scan" in output.summary.lower() or "Security Scan" in output.summary

    def test_build_output_with_gate_result(self):
        """Test building output with gate evaluation result."""
        service = GitHubCheckRunService()

        gate_result = {
            "passed": False,
            "issues": [
                {
                    "file_path": "src/auth.py",
                    "line_number": 42,
                    "severity": "error",
                    "message": "Hardcoded secret detected",
                    "code": "SEC-001",
                },
                {
                    "file_path": "src/db.py",
                    "line_number": 100,
                    "severity": "warning",
                    "message": "Missing error handling",
                    "code": "ERR-001",
                },
            ],
        }

        output = service._build_output(overlay=None, gate_result=gate_result)

        assert "FAILED" in output.summary
        assert len(output.annotations) == 2
        assert output.annotations[0].path == "src/auth.py"
        assert output.annotations[0].annotation_level == "failure"


class TestConclusionDetermination:
    """Test Check Run conclusion logic."""

    def test_determine_conclusion_advisory_passed(self):
        """Test advisory mode with gates passed."""
        service = GitHubCheckRunService()

        conclusion = service._determine_conclusion(
            overlay=None,
            gate_result={"passed": True},
            advisory_mode=True,
        )

        assert conclusion == "success"

    def test_determine_conclusion_advisory_failed(self):
        """Test advisory mode with gates failed."""
        service = GitHubCheckRunService()

        conclusion = service._determine_conclusion(
            overlay=None,
            gate_result={"passed": False},
            advisory_mode=True,
        )

        # Advisory mode: neutral instead of failure
        assert conclusion == "neutral"

    def test_determine_conclusion_blocking_failed(self):
        """Test blocking mode with gates failed."""
        service = GitHubCheckRunService()

        conclusion = service._determine_conclusion(
            overlay=None,
            gate_result={"passed": False},
            advisory_mode=False,
        )

        assert conclusion == "failure"

    def test_determine_conclusion_blocking_strict_mode(self):
        """Test blocking mode with strict mode enabled."""
        service = GitHubCheckRunService()

        overlay = {"strict_mode": True}

        conclusion = service._determine_conclusion(
            overlay=overlay,
            gate_result={"passed": False},
            advisory_mode=False,
        )

        assert conclusion == "action_required"


class TestSeverityMapping:
    """Test severity to annotation level mapping."""

    def test_severity_to_level_error(self):
        """Test error severity mapping."""
        service = GitHubCheckRunService()
        assert service._severity_to_level("error") == "failure"

    def test_severity_to_level_warning(self):
        """Test warning severity mapping."""
        service = GitHubCheckRunService()
        assert service._severity_to_level("warning") == "warning"

    def test_severity_to_level_info(self):
        """Test info severity mapping."""
        service = GitHubCheckRunService()
        assert service._severity_to_level("info") == "notice"

    def test_severity_to_level_unknown(self):
        """Test unknown severity defaults to notice."""
        service = GitHubCheckRunService()
        assert service._severity_to_level("unknown") == "notice"


class TestCheckRunCreation:
    """Test Check Run creation flow."""

    @pytest.mark.asyncio
    async def test_create_check_run_app_not_installed(self):
        """Test error when app not installed on repo."""
        mock_app_service = MagicMock()
        mock_app_service.get_installation_for_repo = AsyncMock(return_value=None)

        service = GitHubCheckRunService(github_app_service=mock_app_service)

        with pytest.raises(CheckRunCreateError) as exc_info:
            await service.create_check_run(
                project_id=uuid4(),
                repo_owner="owner",
                repo_name="repo",
                head_sha="abc123",
            )

        assert "not installed" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    @patch("app.services.github_check_run_service.requests.post")
    @patch("app.services.github_check_run_service.requests.patch")
    async def test_create_check_run_success(self, mock_patch, mock_post):
        """Test successful Check Run creation."""
        # Mock app service
        mock_app_service = MagicMock()
        mock_app_service.get_installation_for_repo = AsyncMock(return_value=12345)
        mock_app_service.get_installation_token = AsyncMock(return_value="ghs_token")

        # Mock API responses
        mock_post.return_value = MagicMock(
            status_code=201,
            json=MagicMock(return_value={"id": 99999}),
        )
        mock_patch.return_value = MagicMock(
            status_code=200,
            json=MagicMock(return_value={
                "id": 99999,
                "html_url": "https://github.com/owner/repo/runs/99999",
            }),
        )

        service = GitHubCheckRunService(github_app_service=mock_app_service)

        result = await service.create_check_run(
            project_id=uuid4(),
            repo_owner="owner",
            repo_name="repo",
            head_sha="abc123",
        )

        assert result.check_run_id == 99999
        assert result.status == "completed"
        # Advisory mode: neutral or success
        assert result.conclusion in ("neutral", "success")

    @pytest.mark.asyncio
    @patch("app.services.github_check_run_service.requests.post")
    async def test_create_check_run_api_error(self, mock_post):
        """Test handling API error during creation."""
        mock_app_service = MagicMock()
        mock_app_service.get_installation_for_repo = AsyncMock(return_value=12345)
        mock_app_service.get_installation_token = AsyncMock(return_value="ghs_token")

        mock_post.return_value = MagicMock(
            status_code=422,
            json=MagicMock(return_value={"message": "Invalid SHA"}),
        )

        service = GitHubCheckRunService(github_app_service=mock_app_service)

        with pytest.raises(CheckRunCreateError):
            await service.create_check_run(
                project_id=uuid4(),
                repo_owner="owner",
                repo_name="repo",
                head_sha="invalid",
            )


class TestCheckRunAnnotationLimit:
    """Test annotation limits are respected."""

    def test_annotations_capped_at_50(self):
        """Test that annotations are capped at GitHub's limit of 50."""
        service = GitHubCheckRunService()

        # Create 100 issues
        gate_result = {
            "passed": False,
            "issues": [
                {
                    "file_path": f"src/file{i}.py",
                    "line_number": i,
                    "severity": "warning",
                    "message": f"Issue {i}",
                    "code": f"CODE-{i}",
                }
                for i in range(100)
            ],
        }

        output = service._build_output(overlay=None, gate_result=gate_result)

        # Should be capped at 50
        assert len(output.annotations) == 50


class TestCheckRunUpdate:
    """Test Check Run update functionality."""

    @pytest.mark.asyncio
    @patch("app.services.github_check_run_service.requests.patch")
    async def test_update_check_run_success(self, mock_patch):
        """Test successful Check Run update."""
        mock_app_service = MagicMock()
        mock_app_service.get_installation_for_repo = AsyncMock(return_value=12345)
        mock_app_service.get_installation_token = AsyncMock(return_value="ghs_token")

        mock_patch.return_value = MagicMock(
            status_code=200,
            json=MagicMock(return_value={"id": 99999}),
        )

        service = GitHubCheckRunService(github_app_service=mock_app_service)

        result = await service.update_check_run(
            repo_owner="owner",
            repo_name="repo",
            check_run_id=99999,
            status="completed",
            conclusion="success",
        )

        assert result["id"] == 99999
        mock_patch.assert_called_once()
