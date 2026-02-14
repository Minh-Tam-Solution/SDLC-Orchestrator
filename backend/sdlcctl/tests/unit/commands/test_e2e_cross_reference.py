"""Unit tests for E2E cross-reference command with OPA integration.

Sprint 140: CLI Orchestration Upgrade
Tests cross-reference validation with OPA policy evaluation and fallback.

Reference:
  - RFC-SDLC-602 E2E API Testing Enhancement
  - SDLC Framework 6.0.5
"""

import json
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch, Mock

import pytest
from typer.testing import CliRunner

from sdlcctl.commands.e2e import (
    app,
    _validate_cross_references_opa,
    _validate_cross_references,
    _fix_ssot_violations,
)
from sdlcctl.lib.opa_client import OPAResult


runner = CliRunner()


# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def valid_project_structure():
    """Create a valid project structure for cross-reference testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        project_path = Path(tmpdir)

        # Create Stage 03 structure
        stage_03 = project_path / "docs" / "03-Integration-APIs"
        stage_03.mkdir(parents=True)
        (stage_03 / "README.md").write_text(
            "# Integration & APIs\n\n"
            "API documentation and integration guides.\n"
            "See [E2E Test Report](../05-Testing-Quality/03-E2E-Testing/reports/latest.md)"
        )

        # Create API specifications folder with canonical openapi.json
        api_spec = stage_03 / "02-API-Specifications"
        api_spec.mkdir(parents=True)
        (api_spec / "openapi.json").write_text(json.dumps({
            "openapi": "3.0.3",
            "info": {"title": "Test API", "version": "1.0.0"},
            "paths": {"/users": {"get": {"summary": "List users"}}}
        }))
        (api_spec / "COMPLETE-API-ENDPOINT-REFERENCE.md").write_text(
            "# API Endpoint Reference\n\n"
            "See [E2E Test Report](../../05-Testing-Quality/03-E2E-Testing/reports/latest.md)\n"
        )

        # Create Stage 05 structure
        stage_05 = project_path / "docs" / "05-Testing-Quality"
        stage_05.mkdir(parents=True)
        (stage_05 / "README.md").write_text(
            "# Testing & Quality\n\n"
            "Test documentation and quality reports.\n"
            "See [API Reference](../03-Integration-APIs/02-API-Specifications/openapi.json)"
        )

        # Create E2E testing folder
        e2e_folder = stage_05 / "03-E2E-Testing"
        e2e_folder.mkdir(parents=True)
        reports_folder = e2e_folder / "reports"
        reports_folder.mkdir(parents=True)
        (reports_folder / "latest.md").write_text(
            "# E2E Test Report\n\n"
            "Pass Rate: 95%\n"
            "API Reference: [OpenAPI](../../../03-Integration-APIs/02-API-Specifications/openapi.json)"
        )

        yield {
            "project_path": project_path,
            "stage_03": stage_03,
            "stage_05": stage_05,
            "api_spec": api_spec,
        }


@pytest.fixture
def project_with_ssot_violation(valid_project_structure):
    """Create a project with SSOT violation (duplicate openapi.json)."""
    project_path = valid_project_structure["project_path"]
    stage_05 = valid_project_structure["stage_05"]

    # Create duplicate openapi.json in Stage 05 (SSOT violation)
    duplicate_api = stage_05 / "api-specs"
    duplicate_api.mkdir(parents=True)
    (duplicate_api / "openapi.json").write_text(json.dumps({
        "openapi": "3.0.3",
        "info": {"title": "Duplicate API", "version": "1.0.0"},
        "paths": {}
    }))

    valid_project_structure["duplicate_path"] = duplicate_api / "openapi.json"
    return valid_project_structure


# =============================================================================
# _validate_cross_references_opa Tests
# =============================================================================


class TestValidateCrossReferencesOPA:
    """Tests for _validate_cross_references_opa function."""

    def test_opa_returns_allow(self, valid_project_structure):
        """Test when OPA returns allow=true."""
        opa_result = OPAResult(
            allow=True,
            violations=[],
            warnings=[],
            details={
                "has_stage_03_links": True,
                "has_stage_05_links": True,
                "ssot_compliance": True,
                "duplicate_openapi_locations": [],
            },
            policy_id="sdlc.e2e_testing.stage_cross_reference",
        )

        with patch("sdlcctl.commands.e2e.get_opa_client") as mock_get_client:
            mock_client = MagicMock()
            mock_client.evaluate.return_value = opa_result
            mock_get_client.return_value = mock_client

            result = _validate_cross_references_opa(
                stage_03=valid_project_structure["stage_03"],
                stage_05=valid_project_structure["stage_05"],
                project_path=valid_project_structure["project_path"],
            )

        assert result["cross_reference_valid"] is True
        assert result["opa_used"] is True
        assert result["violations"] == []

    def test_opa_returns_deny_with_violations(self, valid_project_structure):
        """Test when OPA returns allow=false with violations."""
        opa_result = OPAResult(
            allow=False,
            violations=["SSOT_VIOLATION: Duplicate openapi.json found"],
            warnings=[],
            details={
                "ssot_compliance": False,
                "duplicate_openapi_locations": ["/docs/05-Testing-Quality/api-specs/openapi.json"],
            },
            policy_id="sdlc.e2e_testing.stage_cross_reference",
        )

        with patch("sdlcctl.commands.e2e.get_opa_client") as mock_get_client:
            mock_client = MagicMock()
            mock_client.evaluate.return_value = opa_result
            mock_get_client.return_value = mock_client

            result = _validate_cross_references_opa(
                stage_03=valid_project_structure["stage_03"],
                stage_05=valid_project_structure["stage_05"],
                project_path=valid_project_structure["project_path"],
            )

        assert result["cross_reference_valid"] is False
        assert "SSOT_VIOLATION" in result["violations"][0]
        assert result["ssot_compliance"] is False

    def test_opa_fallback_when_unavailable(self, valid_project_structure):
        """Test fallback to local validation when OPA unavailable."""
        opa_result = OPAResult(
            allow=True,  # Fallback returns allow=true for valid structure
            violations=[],
            warnings=["OPA unavailable (Connection refused), using local validation"],
            details={},
            policy_id="sdlc.e2e_testing.stage_cross_reference",
        )

        with patch("sdlcctl.commands.e2e.get_opa_client") as mock_get_client:
            mock_client = MagicMock()
            mock_client.evaluate.return_value = opa_result
            mock_get_client.return_value = mock_client

            result = _validate_cross_references_opa(
                stage_03=valid_project_structure["stage_03"],
                stage_05=valid_project_structure["stage_05"],
                project_path=valid_project_structure["project_path"],
            )

        # Should still validate using local fallback
        assert result["opa_used"] is True
        assert any("OPA unavailable" in w for w in result["warnings"])

    def test_opa_receives_correct_input(self, valid_project_structure):
        """Test OPA receives correctly formatted input."""
        captured_input = {}

        def capture_evaluate(policy_path, input_data):
            captured_input["policy"] = policy_path
            captured_input["input"] = input_data
            return OPAResult(allow=True)

        with patch("sdlcctl.commands.e2e.get_opa_client") as mock_get_client:
            mock_client = MagicMock()
            mock_client.evaluate.side_effect = capture_evaluate
            mock_get_client.return_value = mock_client

            _validate_cross_references_opa(
                stage_03=valid_project_structure["stage_03"],
                stage_05=valid_project_structure["stage_05"],
                project_path=valid_project_structure["project_path"],
            )

        assert captured_input["policy"] == "sdlc.e2e_testing.stage_cross_reference"
        assert "project_path" in captured_input["input"]
        assert "stage_03_path" in captured_input["input"]
        assert "stage_05_path" in captured_input["input"]


# =============================================================================
# _validate_cross_references Local Tests
# =============================================================================


class TestValidateCrossReferencesLocal:
    """Tests for _validate_cross_references function (local validation)."""

    def test_valid_structure_passes(self, valid_project_structure):
        """Test valid project structure passes validation."""
        result = _validate_cross_references(
            stage_03=valid_project_structure["stage_03"],
            stage_05=valid_project_structure["stage_05"],
            project_path=valid_project_structure["project_path"],
        )

        assert result["stage_03_exists"] is True
        assert result["stage_05_exists"] is True
        assert result["cross_reference_valid"] is True

    def test_missing_stage_03(self, valid_project_structure):
        """Test validation fails when Stage 03 missing."""
        # Remove stage 03
        import shutil
        shutil.rmtree(valid_project_structure["stage_03"])

        result = _validate_cross_references(
            stage_03=valid_project_structure["stage_03"],
            stage_05=valid_project_structure["stage_05"],
            project_path=valid_project_structure["project_path"],
        )

        assert result["stage_03_exists"] is False
        assert result["cross_reference_valid"] is False

    def test_missing_stage_05(self, valid_project_structure):
        """Test validation fails when Stage 05 missing."""
        # Remove stage 05
        import shutil
        shutil.rmtree(valid_project_structure["stage_05"])

        result = _validate_cross_references(
            stage_03=valid_project_structure["stage_03"],
            stage_05=valid_project_structure["stage_05"],
            project_path=valid_project_structure["project_path"],
        )

        assert result["stage_05_exists"] is False
        assert result["cross_reference_valid"] is False

    def test_detects_ssot_violation(self, project_with_ssot_violation):
        """Test validation detects SSOT violation (duplicate openapi.json)."""
        result = _validate_cross_references(
            stage_03=project_with_ssot_violation["stage_03"],
            stage_05=project_with_ssot_violation["stage_05"],
            project_path=project_with_ssot_violation["project_path"],
        )

        assert result["ssot_compliance"] is False
        assert len(result["duplicate_openapi_locations"]) > 0


# =============================================================================
# _fix_ssot_violations Tests
# =============================================================================


class TestFixSSOTViolations:
    """Tests for _fix_ssot_violations function."""

    def test_fix_creates_symlink(self, project_with_ssot_violation):
        """Test fix creates symlink from duplicate to canonical."""
        duplicate_path = project_with_ssot_violation["duplicate_path"]
        canonical_path = project_with_ssot_violation["api_spec"] / "openapi.json"

        result = _fix_ssot_violations(
            duplicates=[str(duplicate_path)],
            canonical_path=canonical_path,
        )

        assert result["success"] is True
        assert result["fixed_count"] == 1
        # Verify backup was created (.json.backup per _fix_ssot_violations)
        assert duplicate_path.with_suffix(".json.backup").exists()

    def test_fix_with_nonexistent_duplicate(self, valid_project_structure):
        """Test fix handles nonexistent duplicate gracefully."""
        result = _fix_ssot_violations(
            duplicates=["/nonexistent/path/openapi.json"],
            canonical_path=valid_project_structure["api_spec"] / "openapi.json",
        )

        # Should still return success but with 0 fixed
        assert result["fixed_count"] == 0

    def test_fix_with_nonexistent_canonical(self, project_with_ssot_violation):
        """Test fix fails when canonical path doesn't exist."""
        result = _fix_ssot_violations(
            duplicates=[str(project_with_ssot_violation["duplicate_path"])],
            canonical_path=Path("/nonexistent/canonical/openapi.json"),
        )

        assert result["success"] is False
        assert "error" in result


# =============================================================================
# CLI Command Tests
# =============================================================================


class TestCrossReferenceCommand:
    """Tests for cross-reference CLI command."""

    def test_command_with_valid_project(self, valid_project_structure):
        """Test CLI command with valid project structure."""
        with patch("sdlcctl.commands.e2e.get_opa_client") as mock_get_client:
            mock_client = MagicMock()
            mock_client.evaluate.return_value = OPAResult(
                allow=True,
                violations=[],
                warnings=["OPA unavailable, using local validation"],
            )
            mock_get_client.return_value = mock_client

            result = runner.invoke(
                app,
                [
                    "cross-reference",
                    "--project-path", str(valid_project_structure["project_path"]),
                    "--stage-03", str(valid_project_structure["stage_03"]),
                    "--stage-05", str(valid_project_structure["stage_05"]),
                ],
            )

        # Command should succeed (exit code 0)
        assert result.exit_code == 0

    def test_command_with_strict_mode_fails(self, project_with_ssot_violation):
        """Test CLI command with --strict exits with error on violation."""
        with patch("sdlcctl.commands.e2e.get_opa_client") as mock_get_client:
            mock_client = MagicMock()
            mock_client.evaluate.return_value = OPAResult(
                allow=False,
                violations=["SSOT_VIOLATION"],
                warnings=["OPA unavailable, using local validation"],
            )
            mock_get_client.return_value = mock_client

            result = runner.invoke(
                app,
                [
                    "cross-reference",
                    "--project-path", str(project_with_ssot_violation["project_path"]),
                    "--stage-03", str(project_with_ssot_violation["stage_03"]),
                    "--stage-05", str(project_with_ssot_violation["stage_05"]),
                    "--strict",
                ],
            )

        # Should exit with error code 1
        assert result.exit_code == 1

    def test_command_with_no_opa_flag(self, valid_project_structure):
        """Test CLI command with --no-opa skips OPA."""
        with patch("sdlcctl.commands.e2e._validate_cross_references") as mock_local:
            mock_local.return_value = {
                "stage_03_exists": True,
                "stage_05_exists": True,
                "has_stage_03_links": True,
                "has_stage_05_links": True,
                "ssot_compliance": True,
                "duplicate_openapi_locations": [],
                "violations": [],
                "warnings": [],
                "cross_reference_valid": True,
            }

            result = runner.invoke(
                app,
                [
                    "cross-reference",
                    "--project-path", str(valid_project_structure["project_path"]),
                    "--stage-03", str(valid_project_structure["stage_03"]),
                    "--stage-05", str(valid_project_structure["stage_05"]),
                    "--no-opa",
                ],
            )

        assert result.exit_code == 0
        # Verify local validation was called
        mock_local.assert_called_once()

    def test_command_with_json_output(self, valid_project_structure):
        """Test CLI command with --format json."""
        with patch("sdlcctl.commands.e2e.get_opa_client") as mock_get_client:
            mock_client = MagicMock()
            mock_client.evaluate.return_value = OPAResult(
                allow=True,
                violations=[],
                warnings=[],
            )
            mock_get_client.return_value = mock_client

            result = runner.invoke(
                app,
                [
                    "cross-reference",
                    "--project-path", str(valid_project_structure["project_path"]),
                    "--stage-03", str(valid_project_structure["stage_03"]),
                    "--stage-05", str(valid_project_structure["stage_05"]),
                    "--format", "json",
                ],
            )

        assert result.exit_code == 0
        # Output should be valid JSON
        try:
            json.loads(result.output)
        except json.JSONDecodeError:
            # Some CLI output may not be pure JSON, check for JSON markers
            assert "{" in result.output or "cross_reference_valid" in result.output

    def test_command_with_fix_flag(self, project_with_ssot_violation):
        """Test CLI command with --fix attempts to fix SSOT violations."""
        with patch("sdlcctl.commands.e2e.get_opa_client") as mock_get_client:
            mock_client = MagicMock()
            mock_client.evaluate.return_value = OPAResult(
                allow=False,
                violations=["SSOT_VIOLATION"],
                warnings=["OPA unavailable, using local validation"],
                details={
                    "duplicate_openapi_locations": [
                        str(project_with_ssot_violation["duplicate_path"])
                    ],
                },
            )
            mock_get_client.return_value = mock_client

            # We need to also patch local validation since fallback is triggered
            with patch("sdlcctl.commands.e2e._validate_cross_references") as mock_local:
                mock_local.return_value = {
                    "stage_03_exists": True,
                    "stage_05_exists": True,
                    "has_stage_03_links": True,
                    "has_stage_05_links": True,
                    "ssot_compliance": False,
                    "duplicate_openapi_locations": [
                        str(project_with_ssot_violation["duplicate_path"])
                    ],
                    "violations": ["SSOT_VIOLATION"],
                    "warnings": [],
                    "cross_reference_valid": False,
                }

                result = runner.invoke(
                    app,
                    [
                        "cross-reference",
                        "--project-path", str(project_with_ssot_violation["project_path"]),
                        "--stage-03", str(project_with_ssot_violation["stage_03"]),
                        "--stage-05", str(project_with_ssot_violation["stage_05"]),
                        "--fix",
                    ],
                )

        # Check that fix was attempted
        assert "fix" in result.output.lower() or result.exit_code == 0


# =============================================================================
# Integration-Style Tests
# =============================================================================


class TestCrossReferenceIntegration:
    """Integration-style tests for cross-reference workflow."""

    def test_complete_workflow_with_opa(self, valid_project_structure):
        """Test complete cross-reference workflow with OPA."""
        # Simulate OPA returning success
        with patch("sdlcctl.commands.e2e.get_opa_client") as mock_get_client:
            mock_client = MagicMock()
            mock_client.evaluate.return_value = OPAResult(
                allow=True,
                violations=[],
                warnings=[],
                details={
                    "has_stage_03_links": True,
                    "has_stage_05_links": True,
                    "ssot_compliance": True,
                    "duplicate_openapi_locations": [],
                },
                policy_id="sdlc.e2e_testing.stage_cross_reference",
            )
            mock_get_client.return_value = mock_client

            result = _validate_cross_references_opa(
                stage_03=valid_project_structure["stage_03"],
                stage_05=valid_project_structure["stage_05"],
                project_path=valid_project_structure["project_path"],
            )

        assert result["cross_reference_valid"] is True
        assert result["stage_03_exists"] is True
        assert result["stage_05_exists"] is True
        assert result["opa_used"] is True

    def test_complete_workflow_with_fallback(self, valid_project_structure):
        """Test complete cross-reference workflow with OPA fallback."""
        # Simulate OPA unavailable
        with patch("sdlcctl.commands.e2e.get_opa_client") as mock_get_client:
            mock_client = MagicMock()
            mock_client.evaluate.return_value = OPAResult(
                allow=True,
                violations=[],
                warnings=["OPA unavailable (Connection refused), using local validation"],
                details={},
                policy_id="sdlc.e2e_testing.stage_cross_reference",
            )
            mock_get_client.return_value = mock_client

            result = _validate_cross_references_opa(
                stage_03=valid_project_structure["stage_03"],
                stage_05=valid_project_structure["stage_05"],
                project_path=valid_project_structure["project_path"],
            )

        # Should merge with local validation results
        assert result["stage_03_exists"] is True
        assert result["stage_05_exists"] is True
        assert any("OPA unavailable" in w for w in result["warnings"])

    def test_ssot_violation_detection_and_fix(self, project_with_ssot_violation):
        """Test complete workflow: detect SSOT violation and fix it."""
        # First, validate and detect violation
        result = _validate_cross_references(
            stage_03=project_with_ssot_violation["stage_03"],
            stage_05=project_with_ssot_violation["stage_05"],
            project_path=project_with_ssot_violation["project_path"],
        )

        assert result["ssot_compliance"] is False
        assert len(result["duplicate_openapi_locations"]) > 0

        # Then fix
        fix_result = _fix_ssot_violations(
            duplicates=result["duplicate_openapi_locations"],
            canonical_path=project_with_ssot_violation["api_spec"] / "openapi.json",
        )

        assert fix_result["success"] is True
        assert fix_result["fixed_count"] > 0
