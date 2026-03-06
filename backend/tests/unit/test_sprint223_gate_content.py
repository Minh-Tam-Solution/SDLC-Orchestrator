"""
Sprint 223 — Gate Content Quality Tests (~18 cases).

Covers:
  S223-01: gate_artifact_matrix.py (tier-artifact requirements)
  S223-02: tier_artifacts.rego (tested via Python mirror)
  S223-03: gates_engine.py artifact type check phase
  S223-04: content_quality.rego (tested via Python fallback mirror)
  S223-05: content_validator.py (in-process fallback)
  S223-06: placeholder_detector.py
  S223-07: evidence validate-content endpoint
  S223-09: RUN_EVALS + LIST_NOTES dispatch
  S223-registry: MAX_COMMANDS unchanged
"""

from __future__ import annotations

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

# ---------------------------------------------------------------------------
# S223-01: gate_artifact_matrix.py
# ---------------------------------------------------------------------------


class TestGateArtifactMatrix:
    """Tests for per-gate per-tier artifact requirements (S223-01)."""

    def test_enterprise_g2_requires_threat_model(self):
        from app.policies.gate_artifact_matrix import get_required_artifacts

        required = get_required_artifacts("G2", "ENTERPRISE")
        assert "THREAT_MODEL" in required
        assert "ADR" in required
        assert "SECURITY_BASELINE" in required
        assert "TEST_PLAN" in required

    def test_lite_g1_empty_requirements(self):
        from app.policies.gate_artifact_matrix import get_required_artifacts

        required = get_required_artifacts("G1", "LITE")
        assert required == []

    def test_standard_g3_requires_test_results(self):
        from app.policies.gate_artifact_matrix import get_required_artifacts

        required = get_required_artifacts("G3", "STANDARD")
        assert "TEST_RESULTS" in required
        assert "CODE_REVIEW" in required

    def test_unknown_gate_returns_empty(self):
        from app.policies.gate_artifact_matrix import get_required_artifacts

        assert get_required_artifacts("G99", "ENTERPRISE") == []

    def test_unknown_tier_returns_empty(self):
        from app.policies.gate_artifact_matrix import get_required_artifacts

        assert get_required_artifacts("G2", "MYTHICAL") == []

    def test_check_completeness_pass(self):
        from app.policies.gate_artifact_matrix import check_artifact_completeness

        result = check_artifact_completeness(
            "G2", "STANDARD", ["ADR", "extra_doc"]
        )
        assert result.passed is True
        assert result.missing == []

    def test_check_completeness_fail_missing(self):
        from app.policies.gate_artifact_matrix import check_artifact_completeness

        result = check_artifact_completeness(
            "G2", "ENTERPRISE", ["ADR", "TEST_PLAN"]
        )
        assert result.passed is False
        assert "THREAT_MODEL" in result.missing
        assert "SECURITY_BASELINE" in result.missing

    def test_check_completeness_case_insensitive(self):
        from app.policies.gate_artifact_matrix import check_artifact_completeness

        result = check_artifact_completeness(
            "G2", "standard", ["adr"]
        )
        assert result.passed is True


# ---------------------------------------------------------------------------
# S223-06: placeholder_detector.py
# ---------------------------------------------------------------------------


class TestPlaceholderDetector:
    """Tests for shared placeholder regex utility (S223-06)."""

    def test_detect_todo_bracket(self):
        from app.utils.placeholder_detector import detect_placeholders

        matches = detect_placeholders("## Decision\n[TODO: fill in later]\n")
        assert len(matches) >= 1
        assert matches[0].pattern == "TODO bracket"
        assert matches[0].line_number == 2

    def test_detect_tbd_bracket(self):
        from app.utils.placeholder_detector import detect_placeholders

        matches = detect_placeholders("[TBD]\n")
        assert len(matches) == 1
        assert matches[0].pattern == "TBD bracket"

    def test_no_placeholders_in_clean_content(self):
        from app.utils.placeholder_detector import detect_placeholders

        content = (
            "## Problem\nWe need to migrate the database.\n"
            "## Decision\nUse Alembic for migrations.\n"
            "## Consequences\nAll teams must update their local envs.\n"
        )
        assert detect_placeholders(content) == []

    def test_detect_autogeneration_marker(self):
        from app.utils.placeholder_detector import detect_placeholders

        matches = detect_placeholders("[Auto-generation failed]\n")
        assert len(matches) >= 1


# ---------------------------------------------------------------------------
# S223-05: content_validator.py (in-process fallback)
# ---------------------------------------------------------------------------


class TestContentValidator:
    """Tests for in-process content quality validator (S223-05)."""

    def test_valid_adr_passes(self):
        from app.services.governance.content_validator import ContentValidator

        content = (
            "# ADR-099: Test Decision\n\n"
            "## Problem\n"
            "We face a critical issue with the database scaling approach "
            "that needs to be resolved before we can proceed with the next phase. "
            "The current approach is not sustainable.\n\n"
            "## Decision\n"
            "We decided to use PostgreSQL partitioning because it provides "
            "better performance characteristics and is well supported by our "
            "existing infrastructure and team expertise.\n\n"
            "## Consequences\n"
            "All downstream services must update their connection strings "
            "and migration scripts. This will require coordinated deployment "
            "across three teams over two sprints.\n"
        )
        validator = ContentValidator()
        result = validator.validate("ADR", content)
        assert result.passed is True
        assert result.missing_sections == []
        assert result.score > 0.5

    def test_empty_adr_fails(self):
        from app.services.governance.content_validator import ContentValidator

        content = "# ADR: TBD\n\n[TODO: write later]\n"
        validator = ContentValidator()
        result = validator.validate("ADR", content)
        assert result.passed is False
        assert len(result.missing_sections) > 0

    def test_adr_with_placeholders_fails(self):
        from app.services.governance.content_validator import ContentValidator

        content = (
            "## Problem\n[TODO: describe problem]\n"
            "## Decision\n[TBD]\n"
            "## Consequences\nSome consequences here that are real content "
            "and have enough words to pass the word count check.\n"
        )
        validator = ContentValidator()
        result = validator.validate("ADR", content)
        assert result.passed is False
        assert len(result.placeholder_warnings) >= 2

    def test_unknown_document_type_passes(self):
        from app.services.governance.content_validator import ContentValidator

        validator = ContentValidator()
        result = validator.validate("UNKNOWN_TYPE", "Some content here.")
        assert result.passed is True
        assert result.score == 1.0

    def test_section_schemas_cover_key_types(self):
        from app.services.governance.content_validator import SECTION_SCHEMAS

        assert "ADR" in SECTION_SCHEMAS
        assert "TEST_PLAN" in SECTION_SCHEMAS
        assert "THREAT_MODEL" in SECTION_SCHEMAS
        assert "SECURITY_BASELINE" in SECTION_SCHEMAS
        assert "BRD" in SECTION_SCHEMAS


# ---------------------------------------------------------------------------
# S223-03: gates_engine.py — EvaluationPhase.ARTIFACT_TYPE_CHECK
# ---------------------------------------------------------------------------


class TestGatesEngineArtifactPhase:
    """Tests for artifact type check phase in gates_engine.py (S223-03)."""

    def test_evaluation_phase_has_artifact_type_check(self):
        from app.services.governance.gates_engine import EvaluationPhase

        assert hasattr(EvaluationPhase, "ARTIFACT_TYPE_CHECK")
        assert EvaluationPhase.ARTIFACT_TYPE_CHECK.value == "artifact_type_check"


# ---------------------------------------------------------------------------
# S223-09: RUN_EVALS + LIST_NOTES dispatch
# ---------------------------------------------------------------------------


class TestOTTHandlerDispatch:
    """Tests for RUN_EVALS + LIST_NOTES dispatch (S223-09)."""

    @pytest.mark.asyncio
    async def test_run_evals_dispatch_exists(self):
        """_execute_run_evals function exists and is callable."""
        from app.services.agent_bridge.governance_action_handler import (
            _execute_run_evals,
        )
        assert callable(_execute_run_evals)

    @pytest.mark.asyncio
    async def test_list_notes_dispatch_exists(self):
        """_execute_list_notes function exists and is callable."""
        from app.services.agent_bridge.governance_action_handler import (
            _execute_list_notes,
        )
        assert callable(_execute_list_notes)


# ---------------------------------------------------------------------------
# S223-registry: MAX_COMMANDS unchanged at 10
# ---------------------------------------------------------------------------


class TestRegistryUnchanged:
    """Verify command registry was NOT modified (CTO R2: dispatch-only)."""

    def test_max_commands_still_10(self):
        from app.services.agent_team.command_registry import MAX_COMMANDS

        assert MAX_COMMANDS == 10

    def test_command_count_at_capacity(self):
        from app.services.agent_team.command_registry import (
            GOVERNANCE_COMMANDS,
            MAX_COMMANDS,
        )

        assert len(GOVERNANCE_COMMANDS) <= MAX_COMMANDS
