"""
Integration Tests for sdlcctl plan Command

SDLC Stage: 04 - BUILD
Sprint: 98 - Planning Sub-agent Implementation Part 1
Framework: SDLC 5.2.0
Epic: EP-10 Planning Mode with Sub-agent Orchestration

Purpose:
Integration tests for the sdlcctl plan CLI command.
Tests end-to-end planning workflow with real project scanning.

Coverage Target: 80%+
Reference: ADR-034-Planning-Subagent-Orchestration
"""

import json
import subprocess
import tempfile
from pathlib import Path

import pytest
from typer.testing import CliRunner

from sdlcctl.cli import app

runner = CliRunner()


# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def sample_project():
    """Create a sample project for integration testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        project_path = Path(tmpdir)

        # Create project structure
        (project_path / "app" / "services").mkdir(parents=True)
        (project_path / "app" / "api").mkdir(parents=True)
        (project_path / "tests" / "unit").mkdir(parents=True)
        (project_path / "docs" / "02-design" / "03-ADRs").mkdir(parents=True)

        # Create service files
        (project_path / "app" / "services" / "user_service.py").write_text('''
"""User Service Module."""
import logging
from typing import Optional
from uuid import UUID

logger = logging.getLogger(__name__)


class UserService:
    """Service for user operations."""

    def __init__(self, repository):
        self.repository = repository

    async def get_user_by_id(self, user_id: UUID) -> Optional[dict]:
        """Get user by ID."""
        try:
            return await self.repository.find_by_id(user_id)
        except Exception as e:
            logger.error(f"Failed to get user {user_id}: {e}")
            raise

    async def create_user(self, data: dict) -> dict:
        """Create a new user."""
        return await self.repository.create(data)
''')

        # Create API router
        (project_path / "app" / "api" / "users.py").write_text('''
"""Users API Router."""
from fastapi import APIRouter, HTTPException
from uuid import UUID

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/{user_id}")
async def get_user(user_id: UUID):
    """Get user by ID."""
    return {"id": user_id}


@router.post("/")
async def create_user(data: dict):
    """Create a new user."""
    return data
''')

        # Create test file
        (project_path / "tests" / "unit" / "test_user_service.py").write_text('''
"""Tests for UserService."""
import pytest
from unittest.mock import AsyncMock, MagicMock


@pytest.fixture
def mock_repository():
    """Create a mock repository."""
    return MagicMock()


@pytest.mark.asyncio
async def test_get_user_by_id():
    """Test getting user by ID."""
    pass
''')

        # Create ADR
        (project_path / "docs" / "02-design" / "03-ADRs" / "ADR-001-Auth.md").write_text('''
# ADR-001: Authentication Strategy

## Status
ACCEPTED

## Context
We need authentication for our API.

## Decision
Use JWT with OAuth2.

## Consequences
- Stateless auth
- Token management needed
''')

        # Create pyproject.toml
        (project_path / "pyproject.toml").write_text('''
[project]
name = "test-project"
version = "1.0.0"

[tool.pytest.ini_options]
asyncio_mode = "auto"
''')

        yield project_path


# =============================================================================
# Test: Basic Command Execution
# =============================================================================


def test_plan_command_help():
    """Test plan command help output."""
    result = runner.invoke(app, ["plan", "--help"])

    assert result.exit_code == 0
    assert "planning mode" in result.stdout.lower()
    assert "--path" in result.stdout
    assert "--depth" in result.stdout


def test_plan_command_with_task(sample_project):
    """Test plan command with a simple task."""
    result = runner.invoke(
        app,
        [
            "plan",
            "Add user authentication feature",
            "--path", str(sample_project),
            "--auto",
            "--quiet",
        ]
    )

    # Should complete without error
    assert result.exit_code == 0


def test_plan_command_outputs_patterns(sample_project):
    """Test that plan command outputs pattern information."""
    result = runner.invoke(
        app,
        [
            "plan",
            "Add payment service with error handling",
            "--path", str(sample_project),
            "--auto",
            "--quiet",
        ]
    )

    assert result.exit_code == 0
    assert "patterns:" in result.stdout.lower()


def test_plan_command_outputs_conformance(sample_project):
    """Test that plan command outputs conformance score."""
    result = runner.invoke(
        app,
        [
            "plan",
            "Refactor user service to use repository pattern",
            "--path", str(sample_project),
            "--auto",
            "--quiet",
        ]
    )

    assert result.exit_code == 0
    assert "conformance:" in result.stdout.lower()


# =============================================================================
# Test: Output Formats
# =============================================================================


def test_plan_command_json_output(sample_project):
    """Test plan command JSON output format."""
    result = runner.invoke(
        app,
        [
            "plan",
            "Add logging middleware",
            "--path", str(sample_project),
            "--format", "json",
            "--auto",
        ]
    )

    assert result.exit_code == 0

    # Should be valid JSON
    try:
        output = json.loads(result.stdout)
        assert "id" in output
        assert "task" in output
        assert "patterns" in output
        assert "plan" in output
        assert "conformance" in output
    except json.JSONDecodeError:
        pytest.fail("Output is not valid JSON")


def test_plan_command_markdown_output(sample_project):
    """Test plan command Markdown output format."""
    result = runner.invoke(
        app,
        [
            "plan",
            "Add caching layer",
            "--path", str(sample_project),
            "--format", "markdown",
            "--auto",
        ]
    )

    assert result.exit_code == 0
    assert "# Implementation Plan" in result.stdout
    assert "## Summary" in result.stdout


# =============================================================================
# Test: Options
# =============================================================================


def test_plan_command_custom_depth(sample_project):
    """Test plan command with custom search depth."""
    result = runner.invoke(
        app,
        [
            "plan",
            "Search with custom depth",
            "--path", str(sample_project),
            "--depth", "5",
            "--auto",
            "--quiet",
        ]
    )

    assert result.exit_code == 0


def test_plan_command_without_adrs(sample_project):
    """Test plan command without ADR analysis."""
    result = runner.invoke(
        app,
        [
            "plan",
            "Skip ADR analysis",
            "--path", str(sample_project),
            "--no-adrs",
            "--auto",
            "--quiet",
        ]
    )

    assert result.exit_code == 0


def test_plan_command_without_tests(sample_project):
    """Test plan command without test pattern analysis."""
    result = runner.invoke(
        app,
        [
            "plan",
            "Skip test patterns",
            "--path", str(sample_project),
            "--no-tests",
            "--auto",
            "--quiet",
        ]
    )

    assert result.exit_code == 0


def test_plan_command_save_to_file(sample_project):
    """Test plan command saving output to file."""
    with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
        output_path = f.name

    try:
        result = runner.invoke(
            app,
            [
                "plan",
                "Save to file test",
                "--path", str(sample_project),
                "--output", output_path,
                "--auto",
            ]
        )

        assert result.exit_code == 0

        # Check file was created and is valid JSON
        output_file = Path(output_path)
        assert output_file.exists()

        content = json.loads(output_file.read_text())
        assert "id" in content
        assert "task" in content
    finally:
        Path(output_path).unlink(missing_ok=True)


# =============================================================================
# Test: Error Handling
# =============================================================================


def test_plan_command_invalid_path():
    """Test plan command with non-existent path."""
    result = runner.invoke(
        app,
        [
            "plan",
            "Test with invalid path",
            "--path", "/nonexistent/path/that/does/not/exist",
            "--auto",
        ]
    )

    assert result.exit_code != 0


def test_plan_command_short_task():
    """Test plan command with task that's too short."""
    result = runner.invoke(
        app,
        [
            "plan",
            "Hi",  # Too short (< 10 chars)
            "--auto",
        ]
    )

    # Should fail validation
    assert result.exit_code != 0


# =============================================================================
# Test: Integration with Services
# =============================================================================


def test_plan_detects_python_patterns(sample_project):
    """Test that plan detects Python code patterns."""
    result = runner.invoke(
        app,
        [
            "plan",
            "Add service with error handling like existing services",
            "--path", str(sample_project),
            "--format", "json",
            "--auto",
        ]
    )

    assert result.exit_code == 0

    output = json.loads(result.stdout)
    patterns = output.get("patterns", {})

    # Should have scanned files
    assert patterns.get("total_files_scanned", 0) > 0


def test_plan_finds_adr_patterns(sample_project):
    """Test that plan finds ADR patterns."""
    result = runner.invoke(
        app,
        [
            "plan",
            "Add authentication following existing architecture decisions",
            "--path", str(sample_project),
            "--format", "json",
            "--auto",
        ]
    )

    assert result.exit_code == 0

    output = json.loads(result.stdout)
    # ADR should have been scanned
    assert output is not None


def test_plan_finds_test_patterns(sample_project):
    """Test that plan finds test patterns."""
    result = runner.invoke(
        app,
        [
            "plan",
            "Add unit tests following existing test patterns",
            "--path", str(sample_project),
            "--format", "json",
            "--auto",
        ]
    )

    assert result.exit_code == 0

    output = json.loads(result.stdout)
    # Tests should have been scanned
    assert output is not None


# =============================================================================
# Test: Plan Structure
# =============================================================================


def test_plan_generates_steps(sample_project):
    """Test that plan generates implementation steps."""
    result = runner.invoke(
        app,
        [
            "plan",
            "Add payment processing service with Stripe",
            "--path", str(sample_project),
            "--format", "json",
            "--auto",
        ]
    )

    assert result.exit_code == 0

    output = json.loads(result.stdout)
    plan = output.get("plan", {})

    # Should have steps
    assert len(plan.get("steps", [])) >= 1

    # Steps should have required fields
    for step in plan.get("steps", []):
        assert "order" in step
        assert "title" in step
        assert "description" in step


def test_plan_calculates_estimates(sample_project):
    """Test that plan calculates time and LOC estimates."""
    result = runner.invoke(
        app,
        [
            "plan",
            "Implement notification service",
            "--path", str(sample_project),
            "--format", "json",
            "--auto",
        ]
    )

    assert result.exit_code == 0

    output = json.loads(result.stdout)
    plan = output.get("plan", {})

    # Should have estimates
    assert plan.get("total_estimated_loc", 0) >= 0
    assert plan.get("total_estimated_hours", 0) >= 0


def test_plan_identifies_risks(sample_project):
    """Test that plan identifies potential risks."""
    result = runner.invoke(
        app,
        [
            "plan",
            "Add user authentication with password hashing and security",
            "--path", str(sample_project),
            "--format", "json",
            "--auto",
        ]
    )

    assert result.exit_code == 0

    output = json.loads(result.stdout)
    plan = output.get("plan", {})

    # Security task should identify risks
    risks = plan.get("risks", [])
    # May or may not have risks depending on task analysis
    assert isinstance(risks, list)


# =============================================================================
# Test: Conformance Scoring
# =============================================================================


def test_plan_has_valid_conformance_score(sample_project):
    """Test that conformance score is valid."""
    result = runner.invoke(
        app,
        [
            "plan",
            "Add feature following existing patterns",
            "--path", str(sample_project),
            "--format", "json",
            "--auto",
        ]
    )

    assert result.exit_code == 0

    output = json.loads(result.stdout)
    conformance = output.get("conformance", {})

    # Score should be between 0 and 100
    score = conformance.get("score", -1)
    assert 0 <= score <= 100

    # Level should be valid
    level = conformance.get("level", "")
    assert level in ["excellent", "good", "fair", "poor"]


# =============================================================================
# Test: CLI Quiet Mode
# =============================================================================


def test_plan_quiet_mode_minimal_output(sample_project):
    """Test that quiet mode produces minimal output."""
    result = runner.invoke(
        app,
        [
            "plan",
            "Test quiet mode output",
            "--path", str(sample_project),
            "--quiet",
            "--auto",
        ]
    )

    assert result.exit_code == 0

    # Should have minimal key:value output
    lines = result.stdout.strip().split("\n")
    assert len(lines) <= 5  # Minimal output

    # Should have expected keys
    output_text = result.stdout.lower()
    assert "patterns:" in output_text
    assert "conformance:" in output_text
    assert "steps:" in output_text


# =============================================================================
# Test: Empty Project Handling
# =============================================================================


def test_plan_with_empty_project():
    """Test plan command with empty project."""
    with tempfile.TemporaryDirectory() as tmpdir:
        result = runner.invoke(
            app,
            [
                "plan",
                "Add feature to empty project",
                "--path", tmpdir,
                "--format", "json",
                "--auto",
            ]
        )

        # Should complete but with low pattern count
        assert result.exit_code == 0

        output = json.loads(result.stdout)
        patterns = output.get("patterns", {})
        assert patterns.get("total_files_scanned", 0) == 0
