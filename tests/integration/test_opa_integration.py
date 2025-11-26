"""
Integration Tests for OPA Service
Policy-as-Code Evaluation Engine (FR1 + FR5)

File: tests/integration/test_opa_integration.py
Version: 1.0.0
Date: November 25, 2025
Status: ACTIVE - Week 7 Day 5 Afternoon
Authority: Backend Lead + QA Lead
Framework: SDLC 4.9 Complete Lifecycle

Test Coverage:
- OPA health check
- Policy upload (PUT /v1/policies/{policy_id})
- Policy evaluation (POST /v1/data/{package_path})
- Policy listing (GET /v1/policies)
- Policy deletion (DELETE /v1/policies/{policy_id})
- Error handling (timeout, invalid input, missing policy)

Total Tests: 13+
Target Coverage: 60%+
Zero Mock Policy: 100% compliance (real OPA Docker container)
"""

import pytest
from uuid import uuid4

from app.services.opa_service import OPAService, OPAEvaluationError


@pytest.mark.integration
@pytest.mark.opa
class TestOPAHealthCheck:
    """Integration tests for OPA health check."""

    def test_health_check_success(self):
        """Test OPA health check returns healthy status."""
        opa = OPAService()

        result = opa.health_check()

        assert isinstance(result, dict)
        assert "healthy" in result
        # OPA may or may not return version/uptime, so we just check it's healthy
        assert result["healthy"] is True


@pytest.mark.integration
@pytest.mark.opa
class TestOPAPolicyManagement:
    """Integration tests for OPA policy upload, list, delete."""

    def test_upload_policy_success(self):
        """Test successful policy upload to OPA."""
        opa = OPAService()
        policy_id = f"test_policy_{uuid4().hex[:8]}"

        # Simple test policy
        rego_code = """
        package sdlc.test_simple

        default allowed = true
        """

        result = opa.upload_policy(policy_id, rego_code)

        assert result["success"] is True
        assert result["policy_id"] == policy_id
        assert "message" in result

        # Cleanup
        opa.delete_policy(policy_id)

    def test_list_policies_success(self):
        """Test listing all policies in OPA."""
        opa = OPAService()

        # Upload a test policy first
        policy_id = f"test_list_{uuid4().hex[:8]}"
        rego_code = "package sdlc.test_list\ndefault allowed = true"
        opa.upload_policy(policy_id, rego_code)

        # List policies
        result = opa.list_policies()

        assert isinstance(result, dict)
        assert "policies" in result
        assert "total" in result
        assert isinstance(result["policies"], list)

        # OPA returns list of policy objects with 'id' field
        # Check if our policy_id is in the list (either as string or in object)
        policy_ids = []
        for policy in result["policies"]:
            if isinstance(policy, dict):
                policy_ids.append(policy.get("id"))
            else:
                policy_ids.append(policy)

        assert policy_id in policy_ids
        assert result["total"] > 0

        # Cleanup
        opa.delete_policy(policy_id)

    def test_delete_policy_success(self):
        """Test successful policy deletion from OPA."""
        opa = OPAService()
        policy_id = f"test_delete_{uuid4().hex[:8]}"

        # Upload policy first
        rego_code = "package sdlc.test_delete\ndefault allowed = true"
        opa.upload_policy(policy_id, rego_code)

        # Delete policy
        result = opa.delete_policy(policy_id)

        assert result["success"] is True
        assert result["policy_id"] == policy_id
        assert "message" in result

        # Verify deletion by listing policies
        policies = opa.list_policies()
        policy_ids = []
        for policy in policies["policies"]:
            if isinstance(policy, dict):
                policy_ids.append(policy.get("id"))
            else:
                policy_ids.append(policy)
        assert policy_id not in policy_ids

    def test_upload_invalid_policy_syntax(self):
        """Test uploading policy with invalid Rego syntax fails."""
        opa = OPAService()
        policy_id = f"test_invalid_{uuid4().hex[:8]}"

        # Invalid Rego syntax (missing closing brace)
        invalid_rego = """
        package sdlc.test_invalid

        default allowed = true {
            # Missing closing brace
        """

        # OPA should reject invalid syntax
        with pytest.raises(OPAEvaluationError):
            opa.upload_policy(policy_id, invalid_rego)


@pytest.mark.integration
@pytest.mark.opa
class TestOPAPolicyEvaluation:
    """Integration tests for OPA policy evaluation."""

    def test_evaluate_policy_allowed(self):
        """Test policy evaluation that should pass (allowed = true)."""
        opa = OPAService()
        policy_id = f"test_eval_pass_{uuid4().hex[:8]}"

        # Policy that checks if FRD has required sections
        rego_code = """
        package sdlc.gates.what.test_eval_pass

        default allowed = false

        allowed {
            input.frd_sections["Introduction"]
            input.frd_sections["Requirements"]
        }

        violations[msg] {
            not input.frd_sections["Introduction"]
            msg := "Missing Introduction section"
        }

        violations[msg] {
            not input.frd_sections["Requirements"]
            msg := "Missing Requirements section"
        }
        """

        # Upload policy
        opa.upload_policy(policy_id, rego_code)

        # Evaluate with valid input (should pass)
        input_data = {
            "frd_sections": {
                "Introduction": "Project overview",
                "Requirements": "FR1, FR2, FR3"
            }
        }

        result = opa.evaluate_policy(
            policy_code="test_eval_pass",
            stage="WHAT",
            input_data=input_data
        )

        assert result["allowed"] is True
        assert len(result["violations"]) == 0
        assert result["metadata"]["policy_code"] == "test_eval_pass"
        assert result["metadata"]["stage"] == "WHAT"
        assert result["metadata"]["response_time_ms"] >= 0

        # Cleanup
        opa.delete_policy(policy_id)

    def test_evaluate_policy_denied(self):
        """Test policy evaluation that should fail (allowed = false)."""
        opa = OPAService()
        policy_id = f"test_eval_fail_{uuid4().hex[:8]}"

        # Policy that requires specific sections
        rego_code = """
        package sdlc.gates.what.test_eval_fail

        default allowed = false

        allowed {
            input.frd_sections["Introduction"]
            input.frd_sections["Requirements"]
            input.frd_sections["API Contracts"]
        }

        violations[msg] {
            not input.frd_sections["Introduction"]
            msg := "Missing Introduction section"
        }

        violations[msg] {
            not input.frd_sections["Requirements"]
            msg := "Missing Requirements section"
        }

        violations[msg] {
            not input.frd_sections["API Contracts"]
            msg := "Missing API Contracts section"
        }
        """

        # Upload policy
        opa.upload_policy(policy_id, rego_code)

        # Evaluate with incomplete input (should fail)
        input_data = {
            "frd_sections": {
                "Introduction": "Project overview"
                # Missing Requirements and API Contracts
            }
        }

        result = opa.evaluate_policy(
            policy_code="test_eval_fail",
            stage="WHAT",
            input_data=input_data
        )

        assert result["allowed"] is False
        assert len(result["violations"]) == 2  # Missing 2 sections
        assert any("Requirements" in v for v in result["violations"])
        assert any("API Contracts" in v for v in result["violations"])

        # Cleanup
        opa.delete_policy(policy_id)

    def test_evaluate_policy_with_custom_timeout(self):
        """Test policy evaluation with custom timeout."""
        opa = OPAService()
        policy_id = f"test_timeout_{uuid4().hex[:8]}"

        # Simple policy
        rego_code = """
        package sdlc.gates.build.test_timeout

        default allowed = true
        """

        opa.upload_policy(policy_id, rego_code)

        # Evaluate with custom 10 second timeout
        result = opa.evaluate_policy(
            policy_code="test_timeout",
            stage="BUILD",
            input_data={"test": "data"},
            timeout=10
        )

        assert result["allowed"] is True
        assert result["metadata"]["response_time_ms"] < 10000  # Should be much faster

        # Cleanup
        opa.delete_policy(policy_id)

    def test_evaluate_nonexistent_policy(self):
        """Test evaluating a policy that doesn't exist returns default denial."""
        opa = OPAService()

        # Try to evaluate a policy that doesn't exist
        result = opa.evaluate_policy(
            policy_code="nonexistent_policy_xyz",
            stage="WHAT",
            input_data={"test": "data"}
        )

        # OPA returns default false for undefined policies
        assert result["allowed"] is False

    def test_evaluate_policy_complex_logic(self):
        """Test policy with complex Rego logic (multiple conditions)."""
        opa = OPAService()
        policy_id = f"test_complex_{uuid4().hex[:8]}"

        # Policy with complex logic
        rego_code = """
        package sdlc.gates.build.test_complex

        default allowed = false

        # Allow if all conditions met
        allowed {
            input.test_coverage >= 90
            input.build_status == "SUCCESS"
            count(input.failing_tests) == 0
        }

        violations[msg] {
            input.test_coverage < 90
            msg := sprintf("Test coverage too low: %d%% (required: 90%%)", [input.test_coverage])
        }

        violations[msg] {
            input.build_status != "SUCCESS"
            msg := sprintf("Build failed with status: %s", [input.build_status])
        }

        violations[msg] {
            count(input.failing_tests) > 0
            msg := sprintf("%d tests failing", [count(input.failing_tests)])
        }
        """

        opa.upload_policy(policy_id, rego_code)

        # Test Case 1: All conditions met (should pass)
        input_pass = {
            "test_coverage": 95,
            "build_status": "SUCCESS",
            "failing_tests": []
        }

        result_pass = opa.evaluate_policy(
            policy_code="test_complex",
            stage="BUILD",
            input_data=input_pass
        )

        assert result_pass["allowed"] is True
        assert len(result_pass["violations"]) == 0

        # Test Case 2: Multiple violations (should fail)
        input_fail = {
            "test_coverage": 75,  # Too low
            "build_status": "FAILED",  # Build failed
            "failing_tests": ["test1", "test2", "test3"]  # 3 failing tests
        }

        result_fail = opa.evaluate_policy(
            policy_code="test_complex",
            stage="BUILD",
            input_data=input_fail
        )

        assert result_fail["allowed"] is False
        assert len(result_fail["violations"]) == 3  # All 3 conditions violated

        # Cleanup
        opa.delete_policy(policy_id)


@pytest.mark.integration
@pytest.mark.opa
@pytest.mark.slow
class TestOPAErrorHandling:
    """Integration tests for OPA error handling."""

    def test_evaluate_with_network_timeout(self):
        """Test policy evaluation timeout handling."""
        opa = OPAService()
        policy_id = f"test_net_timeout_{uuid4().hex[:8]}"

        # Upload a simple policy
        rego_code = "package sdlc.test_timeout\ndefault allowed = true"
        opa.upload_policy(policy_id, rego_code)

        # Try with very short timeout (should succeed as OPA is fast)
        # But we're testing the timeout parameter works
        result = opa.evaluate_policy(
            policy_code="test_timeout",
            stage="sdlc",
            input_data={},
            timeout=1  # 1 second timeout
        )

        # Should complete within 1 second
        assert result["metadata"]["response_time_ms"] < 1000

        # Cleanup
        opa.delete_policy(policy_id)

    def test_upload_policy_to_invalid_endpoint(self):
        """Test uploading policy when OPA is unavailable raises error."""
        # Create OPA service with invalid endpoint
        opa = OPAService()
        original_url = opa.base_url
        opa.base_url = "http://invalid-host:9999"

        # Try to upload policy (should fail)
        with pytest.raises(OPAEvaluationError):
            opa.upload_policy("test_invalid", "package sdlc.test_invalid\ndefault allowed = true")

        # Restore original URL
        opa.base_url = original_url

    def test_evaluate_policy_connection_error(self):
        """Test evaluate_policy RequestException handler (lines 202-207)."""
        opa = OPAService()
        original_url = opa.base_url
        opa.base_url = "http://invalid-opa-host:9999"

        # Try to evaluate policy (should trigger RequestException)
        with pytest.raises(OPAEvaluationError) as exc_info:
            opa.evaluate_policy(
                policy_code="test_fail",
                stage="WHAT",
                input_data={"test": "data"}
            )

        # Verify error message contains policy details
        assert "test_fail" in str(exc_info.value)
        assert "WHAT" in str(exc_info.value)

        # Restore original URL
        opa.base_url = original_url

    def test_delete_policy_connection_error(self):
        """Test delete_policy RequestException handler (lines 334-336)."""
        opa = OPAService()
        original_url = opa.base_url
        opa.base_url = "http://invalid-opa-host:9999"

        # Try to delete policy (should trigger RequestException)
        with pytest.raises(OPAEvaluationError) as exc_info:
            opa.delete_policy("test_policy_xyz")

        # Verify error message contains policy ID
        assert "test_policy_xyz" in str(exc_info.value)

        # Restore original URL
        opa.base_url = original_url

    def test_list_policies_connection_error(self):
        """Test list_policies RequestException handler (lines 390-392)."""
        opa = OPAService()
        original_url = opa.base_url
        opa.base_url = "http://invalid-opa-host:9999"

        # Try to list policies (should trigger RequestException)
        with pytest.raises(OPAEvaluationError) as exc_info:
            opa.list_policies()

        # Verify error message indicates list failure
        assert "Failed to list policies" in str(exc_info.value)

        # Restore original URL
        opa.base_url = original_url

    def test_health_check_when_opa_unavailable(self):
        """Test health_check Exception handler (lines 447-449)."""
        opa = OPAService()
        original_url = opa.base_url
        opa.base_url = "http://invalid-opa-host:9999"

        # Health check should return unhealthy status (not raise exception)
        result = opa.health_check()

        assert result["healthy"] is False
        assert result["version"] == "unknown"
        assert result["uptime_seconds"] == 0
        assert "error" in result

        # Restore original URL
        opa.base_url = original_url


@pytest.mark.integration
@pytest.mark.opa
class TestOPARealWorldScenarios:
    """Integration tests for real-world SDLC policy scenarios."""

    def test_gate_g1_frd_completeness_policy(self):
        """Test realistic Gate G1 FRD completeness policy."""
        opa = OPAService()
        policy_id = f"test_g1_frd_{uuid4().hex[:8]}"

        # Realistic FRD completeness policy for Gate G1
        rego_code = """
        package sdlc.gates.what.g1_frd_completeness

        default allowed = false

        required_sections := [
            "Introduction",
            "Functional Requirements",
            "API Contracts",
            "Data Model",
            "Security Requirements"
        ]

        # Allow if all required sections present
        allowed {
            count(missing_sections) == 0
        }

        # Calculate missing sections
        missing_sections[section] {
            section := required_sections[_]
            not input.frd_sections[section]
        }

        # Generate violations for missing sections
        violations[msg] {
            count(missing_sections) > 0
            msg := sprintf("FRD missing %d required section(s): %v",
                          [count(missing_sections), missing_sections])
        }
        """

        opa.upload_policy(policy_id, rego_code)

        # Test with complete FRD (should pass)
        complete_frd = {
            "frd_sections": {
                "Introduction": "Project overview",
                "Functional Requirements": "FR1-FR20",
                "API Contracts": "OpenAPI 3.0 spec",
                "Data Model": "21 tables",
                "Security Requirements": "OWASP ASVS Level 2"
            }
        }

        result_pass = opa.evaluate_policy(
            policy_code="g1_frd_completeness",
            stage="WHAT",
            input_data=complete_frd
        )

        assert result_pass["allowed"] is True
        assert len(result_pass["violations"]) == 0

        # Test with incomplete FRD (should fail)
        incomplete_frd = {
            "frd_sections": {
                "Introduction": "Project overview",
                "Functional Requirements": "FR1-FR20"
                # Missing: API Contracts, Data Model, Security Requirements
            }
        }

        result_fail = opa.evaluate_policy(
            policy_code="g1_frd_completeness",
            stage="WHAT",
            input_data=incomplete_frd
        )

        assert result_fail["allowed"] is False
        assert len(result_fail["violations"]) > 0
        assert "missing" in result_fail["violations"][0].lower()

        # Cleanup
        opa.delete_policy(policy_id)
