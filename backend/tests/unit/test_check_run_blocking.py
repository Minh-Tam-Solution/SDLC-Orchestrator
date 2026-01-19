"""
=========================================================================
Unit Tests - GitHub Check Run Blocking Mode (Sprint 82)
SDLC Orchestrator - Stage 04 (BUILD)

Version: 1.0.0
Date: January 19, 2026
Status: ACTIVE - Sprint 82 (Pre-Launch Hardening)
Authority: Backend Lead + CTO Approved
Foundation: Sprint 82 Plan, ADR-029

Purpose:
- Test Check Run enforcement modes (ADVISORY/BLOCKING/STRICT)
- Test bypass label detection
- Test conclusion determination logic

Test Coverage:
1. CheckRunMode enum parsing
2. Conclusion determination for each mode
3. Bypass label detection
4. Output formatting with mode info

Zero Mock Policy: Uses real service classes (no mocking internals)
=========================================================================
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.services.github_check_run_service import (
    CheckRunMode,
    GitHubCheckRunService,
    CheckRunOutput,
    CheckRunAnnotation,
    BYPASS_LABEL,
)


class TestCheckRunMode:
    """Test CheckRunMode enum functionality."""

    def test_mode_values(self):
        """Test CheckRunMode enum values."""
        assert CheckRunMode.ADVISORY.value == "advisory"
        assert CheckRunMode.BLOCKING.value == "blocking"
        assert CheckRunMode.STRICT.value == "strict"

    def test_from_string_valid(self):
        """Test parsing valid mode strings."""
        assert CheckRunMode.from_string("advisory") == CheckRunMode.ADVISORY
        assert CheckRunMode.from_string("ADVISORY") == CheckRunMode.ADVISORY
        assert CheckRunMode.from_string("Advisory") == CheckRunMode.ADVISORY

        assert CheckRunMode.from_string("blocking") == CheckRunMode.BLOCKING
        assert CheckRunMode.from_string("BLOCKING") == CheckRunMode.BLOCKING

        assert CheckRunMode.from_string("strict") == CheckRunMode.STRICT
        assert CheckRunMode.from_string("STRICT") == CheckRunMode.STRICT

    def test_from_string_invalid(self):
        """Test parsing invalid mode strings defaults to ADVISORY."""
        assert CheckRunMode.from_string("invalid") == CheckRunMode.ADVISORY
        assert CheckRunMode.from_string("") == CheckRunMode.ADVISORY
        assert CheckRunMode.from_string("unknown_mode") == CheckRunMode.ADVISORY


class TestDetermineConclusion:
    """Test _determine_conclusion method for Sprint 82 modes."""

    def setup_method(self):
        """Set up test fixtures."""
        self.service = GitHubCheckRunService()

    # ========================================================================
    # Advisory Mode Tests
    # ========================================================================

    def test_advisory_gates_passed(self):
        """Advisory mode with passing gates → success."""
        result = self.service._determine_conclusion(
            overlay=None,
            gate_result={"passed": True},
            mode=CheckRunMode.ADVISORY,
        )
        assert result == "success"

    def test_advisory_gates_failed(self):
        """Advisory mode with failing gates → neutral (doesn't block)."""
        result = self.service._determine_conclusion(
            overlay=None,
            gate_result={"passed": False},
            mode=CheckRunMode.ADVISORY,
        )
        assert result == "neutral"

    def test_advisory_no_gate_result(self):
        """Advisory mode with no gate result → success (default pass)."""
        result = self.service._determine_conclusion(
            overlay=None,
            gate_result=None,
            mode=CheckRunMode.ADVISORY,
        )
        assert result == "success"

    # ========================================================================
    # Blocking Mode Tests
    # ========================================================================

    def test_blocking_gates_passed(self):
        """Blocking mode with passing gates → success."""
        result = self.service._determine_conclusion(
            overlay=None,
            gate_result={"passed": True},
            mode=CheckRunMode.BLOCKING,
        )
        assert result == "success"

    def test_blocking_gates_failed(self):
        """Blocking mode with failing gates → failure (blocks merge)."""
        result = self.service._determine_conclusion(
            overlay=None,
            gate_result={"passed": False},
            mode=CheckRunMode.BLOCKING,
        )
        assert result == "failure"

    def test_blocking_overlay_strict_mode(self):
        """Blocking mode + overlay strict → action_required (escalate)."""
        result = self.service._determine_conclusion(
            overlay={"strict_mode": True},
            gate_result={"passed": False},
            mode=CheckRunMode.BLOCKING,
        )
        # Stage strict mode escalates blocking → action_required
        assert result == "action_required"

    # ========================================================================
    # Strict Mode Tests
    # ========================================================================

    def test_strict_gates_passed(self):
        """Strict mode with passing gates → success."""
        result = self.service._determine_conclusion(
            overlay=None,
            gate_result={"passed": True},
            mode=CheckRunMode.STRICT,
        )
        assert result == "success"

    def test_strict_gates_failed(self):
        """Strict mode with failing gates → action_required (requires approval)."""
        result = self.service._determine_conclusion(
            overlay=None,
            gate_result={"passed": False},
            mode=CheckRunMode.STRICT,
        )
        assert result == "action_required"

    def test_strict_no_gate_result(self):
        """Strict mode with no gate result → success (default pass)."""
        result = self.service._determine_conclusion(
            overlay=None,
            gate_result=None,
            mode=CheckRunMode.STRICT,
        )
        assert result == "success"


class TestBuildOutput:
    """Test _build_output method with Sprint 82 mode info."""

    def setup_method(self):
        """Set up test fixtures."""
        self.service = GitHubCheckRunService()

    def test_output_includes_enforcement_mode(self):
        """Output includes enforcement mode in summary."""
        output = self.service._build_output(
            overlay={"stage_name": "BUILD", "gate_status": "PASSED"},
            gate_result={"passed": True},
            mode=CheckRunMode.BLOCKING,
            bypassed=False,
        )

        assert "BLOCKING" in output.summary
        assert "Enforcement Mode" in output.summary

    def test_output_advisory_mode_icon(self):
        """Advisory mode shows info icon in title."""
        output = self.service._build_output(
            overlay={"stage_name": "BUILD"},
            gate_result=None,
            mode=CheckRunMode.ADVISORY,
            bypassed=False,
        )

        assert "ℹ️" in output.title

    def test_output_blocking_mode_icon(self):
        """Blocking mode shows shield icon in title."""
        output = self.service._build_output(
            overlay={"stage_name": "BUILD"},
            gate_result=None,
            mode=CheckRunMode.BLOCKING,
            bypassed=False,
        )

        assert "🛡️" in output.title

    def test_output_strict_mode_icon(self):
        """Strict mode shows lock icon in title."""
        output = self.service._build_output(
            overlay={"stage_name": "BUILD"},
            gate_result=None,
            mode=CheckRunMode.STRICT,
            bypassed=False,
        )

        assert "🔒" in output.title

    def test_output_bypass_indicator(self):
        """Bypassed PRs show bypass indicator."""
        output = self.service._build_output(
            overlay={"stage_name": "BUILD"},
            gate_result=None,
            mode=CheckRunMode.BLOCKING,
            bypassed=True,
        )

        assert "BYPASS" in output.title
        assert "bypassed" in output.summary.lower()
        assert BYPASS_LABEL in output.summary

    def test_output_mode_explanation_advisory(self):
        """Advisory mode includes explanation in summary."""
        output = self.service._build_output(
            overlay=None,
            gate_result=None,
            mode=CheckRunMode.ADVISORY,
            bypassed=False,
        )

        assert "informational only" in output.summary
        assert "do not block merge" in output.summary

    def test_output_mode_explanation_blocking(self):
        """Blocking mode includes explanation in summary."""
        output = self.service._build_output(
            overlay=None,
            gate_result=None,
            mode=CheckRunMode.BLOCKING,
            bypassed=False,
        )

        assert "will be blocked if gates fail" in output.summary

    def test_output_mode_explanation_strict(self):
        """Strict mode includes explanation in summary."""
        output = self.service._build_output(
            overlay=None,
            gate_result=None,
            mode=CheckRunMode.STRICT,
            bypassed=False,
        )

        assert "manual approval required" in output.summary


class TestBypassLabelDetection:
    """Test bypass label checking logic."""

    def setup_method(self):
        """Set up test fixtures."""
        self.service = GitHubCheckRunService()

    @pytest.mark.asyncio
    async def test_has_bypass_label_true(self):
        """Test detection when bypass label is present."""
        with patch("requests.get") as mock_get:
            mock_get.return_value = MagicMock(
                status_code=200,
                json=MagicMock(return_value=[
                    {"name": "bug"},
                    {"name": BYPASS_LABEL},
                    {"name": "urgent"},
                ])
            )

            result = await self.service._has_bypass_label(
                token="test_token",
                repo_owner="org",
                repo_name="repo",
                pr_number=42,
            )

            assert result is True

    @pytest.mark.asyncio
    async def test_has_bypass_label_false(self):
        """Test detection when bypass label is not present."""
        with patch("requests.get") as mock_get:
            mock_get.return_value = MagicMock(
                status_code=200,
                json=MagicMock(return_value=[
                    {"name": "bug"},
                    {"name": "enhancement"},
                ])
            )

            result = await self.service._has_bypass_label(
                token="test_token",
                repo_owner="org",
                repo_name="repo",
                pr_number=42,
            )

            assert result is False

    @pytest.mark.asyncio
    async def test_has_bypass_label_case_insensitive(self):
        """Test bypass label detection is case-insensitive."""
        with patch("requests.get") as mock_get:
            mock_get.return_value = MagicMock(
                status_code=200,
                json=MagicMock(return_value=[
                    {"name": "SDLC-BYPASS"},  # Uppercase
                ])
            )

            result = await self.service._has_bypass_label(
                token="test_token",
                repo_owner="org",
                repo_name="repo",
                pr_number=42,
            )

            assert result is True

    @pytest.mark.asyncio
    async def test_has_bypass_label_api_error(self):
        """Test graceful handling when GitHub API fails."""
        with patch("requests.get") as mock_get:
            mock_get.return_value = MagicMock(
                status_code=404,
                text="Not Found",
            )

            result = await self.service._has_bypass_label(
                token="test_token",
                repo_owner="org",
                repo_name="repo",
                pr_number=42,
            )

            # Should return False on error (fail-safe)
            assert result is False

    @pytest.mark.asyncio
    async def test_has_bypass_label_exception(self):
        """Test graceful handling when request throws exception."""
        with patch("requests.get") as mock_get:
            mock_get.side_effect = Exception("Network error")

            result = await self.service._has_bypass_label(
                token="test_token",
                repo_owner="org",
                repo_name="repo",
                pr_number=42,
            )

            # Should return False on exception (fail-safe)
            assert result is False


class TestConclusionMatrix:
    """
    Test conclusion matrix for all mode × gate_result × overlay combinations.

    Matrix (Sprint 82):
    +----------+-----------+-------------+------------------+
    | Mode     | Gates     | Overlay     | Conclusion       |
    |          | Passed    | Strict      |                  |
    +----------+-----------+-------------+------------------+
    | ADVISORY | true      | any         | success          |
    | ADVISORY | false     | any         | neutral          |
    | BLOCKING | true      | any         | success          |
    | BLOCKING | false     | false       | failure          |
    | BLOCKING | false     | true        | action_required  |
    | STRICT   | true      | any         | success          |
    | STRICT   | false     | any         | action_required  |
    +----------+-----------+-------------+------------------+
    """

    def setup_method(self):
        """Set up test fixtures."""
        self.service = GitHubCheckRunService()

    @pytest.mark.parametrize("mode,gates_passed,overlay_strict,expected", [
        # Advisory mode - never blocks
        (CheckRunMode.ADVISORY, True, False, "success"),
        (CheckRunMode.ADVISORY, True, True, "success"),
        (CheckRunMode.ADVISORY, False, False, "neutral"),
        (CheckRunMode.ADVISORY, False, True, "neutral"),

        # Blocking mode - blocks on failure
        (CheckRunMode.BLOCKING, True, False, "success"),
        (CheckRunMode.BLOCKING, True, True, "success"),
        (CheckRunMode.BLOCKING, False, False, "failure"),
        (CheckRunMode.BLOCKING, False, True, "action_required"),  # Escalate

        # Strict mode - always requires approval on failure
        (CheckRunMode.STRICT, True, False, "success"),
        (CheckRunMode.STRICT, True, True, "success"),
        (CheckRunMode.STRICT, False, False, "action_required"),
        (CheckRunMode.STRICT, False, True, "action_required"),
    ])
    def test_conclusion_matrix(
        self,
        mode: CheckRunMode,
        gates_passed: bool,
        overlay_strict: bool,
        expected: str,
    ):
        """Test all combinations of mode × gates × overlay."""
        overlay = {"strict_mode": overlay_strict} if overlay_strict else None
        gate_result = {"passed": gates_passed}

        result = self.service._determine_conclusion(
            overlay=overlay,
            gate_result=gate_result,
            mode=mode,
        )

        assert result == expected, (
            f"Mode={mode.value}, gates_passed={gates_passed}, "
            f"overlay_strict={overlay_strict} → expected {expected}, got {result}"
        )


class TestBypassLabelConstant:
    """Test bypass label constant."""

    def test_bypass_label_value(self):
        """Verify bypass label constant value."""
        assert BYPASS_LABEL == "sdlc-bypass"

    def test_bypass_label_lowercase(self):
        """Verify bypass label is lowercase for consistent comparison."""
        assert BYPASS_LABEL.islower()
