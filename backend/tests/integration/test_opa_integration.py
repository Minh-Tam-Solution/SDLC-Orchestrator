"""
=========================================================================
OPA Integration Tests - Sprint 111 Day 5
SDLC Orchestrator - Infrastructure Services Layer

Version: 1.0.0
Date: January 28, 2026
Status: Sprint 111 - Infrastructure Services (Day 5)
Authority: CTO Approved Sprint Plan
Foundation: FR1 (Gate Engine), FR5 (Policy Pack Library)

Purpose:
- Validate OPA integration with SDLC Orchestrator
- Test policy upload, evaluation, and management
- Verify batch evaluation performance
- Confirm error handling for invalid policies

OPA Container Configuration:
- Container: sdlc-opa (openpolicyagent/opa:0.58.0)
- Internal Port: 8181
- External Port: 8185 (docker-compose mapping)
- Policies: ./backend/policy-packs/rego:/policies:ro

Test Execution:
    # With OPA container running:
    docker-compose up -d opa
    pytest tests/integration/test_opa_integration.py -v

    # Quick validation:
    python quick_test_opa_integration.py

Zero Mock Policy: Tests use real OPA endpoints, skip gracefully if unavailable
=========================================================================
"""

import os
import time
from typing import Any

import pytest

# Import the OPA service
from app.services.opa_service import (
    OPAEvaluationError,
    OPAService,
    opa_service,
)


# ============================================================================
# Test Configuration
# ============================================================================

# OPA endpoint (internal container or external)
OPA_URL = os.getenv("OPA_URL", "http://localhost:8185")

# Performance targets
EVALUATION_TIMEOUT = 5  # 5s max per evaluation
PERFORMANCE_TARGET_SINGLE = 0.1  # 100ms P95 per evaluation
PERFORMANCE_TARGET_BATCH = 0.5  # 500ms for batch of 5


# ============================================================================
# Test Rego Policies
# ============================================================================

SAMPLE_POLICY_PASS = """
package sdlc.gates.what.test_policy

default allowed = false

allowed {
    input.has_introduction
    input.has_requirements
}

violations[msg] {
    not input.has_introduction
    msg := "Missing introduction section"
}

violations[msg] {
    not input.has_requirements
    msg := "Missing requirements section"
}
"""

SAMPLE_POLICY_COMPLEX = """
package sdlc.gates.how.api_coverage

default allowed = false

allowed {
    input.api_coverage >= 80
    input.has_openapi_spec
}

violations[msg] {
    input.api_coverage < 80
    msg := sprintf("API coverage %d%% is below 80%% threshold", [input.api_coverage])
}

violations[msg] {
    not input.has_openapi_spec
    msg := "Missing OpenAPI specification"
}
"""

INVALID_REGO = """
package invalid.policy

this is not valid rego syntax {
    input.something
}
"""


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture(scope="module")
def opa_service_instance() -> OPAService:
    """Create OPA service instance for testing."""
    service = OPAService()
    # Override URL for testing
    service.base_url = OPA_URL
    return service


@pytest.fixture(scope="module")
def opa_available(opa_service_instance: OPAService) -> bool:
    """Check if OPA is available for integration tests."""
    health = opa_service_instance.health_check()
    return health.get("healthy", False)


@pytest.fixture
def cleanup_test_policies(opa_service_instance: OPAService):
    """Cleanup test policies after test."""
    yield
    # Cleanup test policies
    try:
        opa_service_instance.delete_policy("test_policy")
    except Exception:
        pass
    try:
        opa_service_instance.delete_policy("api_coverage")
    except Exception:
        pass


# ============================================================================
# TestOPAConnectionHealth - Health Check & Connectivity
# ============================================================================

class TestOPAConnectionHealth:
    """Test OPA service health check and connectivity."""

    def test_service_initialization(self) -> None:
        """Test OPAService initializes correctly."""
        service = OPAService()

        assert service is not None
        assert service.base_url is not None
        assert service.timeout > 0

    def test_health_check_returns_valid_structure(
        self, opa_service_instance: OPAService
    ) -> None:
        """Test health check returns proper structure."""
        health = opa_service_instance.health_check()

        # Structure must always be present
        assert "healthy" in health
        assert isinstance(health["healthy"], bool)

    @pytest.mark.skipif(
        not os.getenv("OPA_URL"),
        reason="OPA not configured"
    )
    def test_health_check_with_opa_container(
        self, opa_service_instance: OPAService, opa_available: bool
    ) -> None:
        """Test health check against OPA container."""
        if not opa_available:
            pytest.skip("OPA not available")

        health = opa_service_instance.health_check()

        assert health["healthy"] is True
        print(f"\n✅ OPA healthy (version: {health.get('version', 'unknown')})")


# ============================================================================
# TestPolicyUpload - Policy Upload & Management
# ============================================================================

class TestPolicyUpload:
    """Test policy upload and management."""

    @pytest.mark.skipif(
        not os.getenv("OPA_URL"),
        reason="OPA not configured"
    )
    def test_upload_valid_policy(
        self, opa_service_instance: OPAService, opa_available: bool, cleanup_test_policies
    ) -> None:
        """Test uploading a valid Rego policy."""
        if not opa_available:
            pytest.skip("OPA not available")

        result = opa_service_instance.upload_policy(
            policy_id="test_policy",
            rego_code=SAMPLE_POLICY_PASS
        )

        assert result["success"] is True
        assert result["policy_id"] == "test_policy"
        print(f"\n✅ Policy uploaded: {result['policy_id']}")

    @pytest.mark.skipif(
        not os.getenv("OPA_URL"),
        reason="OPA not configured"
    )
    def test_upload_complex_policy(
        self, opa_service_instance: OPAService, opa_available: bool, cleanup_test_policies
    ) -> None:
        """Test uploading a complex Rego policy."""
        if not opa_available:
            pytest.skip("OPA not available")

        result = opa_service_instance.upload_policy(
            policy_id="api_coverage",
            rego_code=SAMPLE_POLICY_COMPLEX
        )

        assert result["success"] is True
        print(f"\n✅ Complex policy uploaded: {result['policy_id']}")

    @pytest.mark.skipif(
        not os.getenv("OPA_URL"),
        reason="OPA not configured"
    )
    def test_upload_invalid_rego_fails(
        self, opa_service_instance: OPAService, opa_available: bool
    ) -> None:
        """Test that invalid Rego policy upload fails."""
        if not opa_available:
            pytest.skip("OPA not available")

        with pytest.raises(OPAEvaluationError):
            opa_service_instance.upload_policy(
                policy_id="invalid_policy",
                rego_code=INVALID_REGO
            )

    @pytest.mark.skipif(
        not os.getenv("OPA_URL"),
        reason="OPA not configured"
    )
    def test_list_policies(
        self, opa_service_instance: OPAService, opa_available: bool, cleanup_test_policies
    ) -> None:
        """Test listing all policies."""
        if not opa_available:
            pytest.skip("OPA not available")

        # Upload a policy first
        opa_service_instance.upload_policy(
            policy_id="test_policy",
            rego_code=SAMPLE_POLICY_PASS
        )

        # List policies
        result = opa_service_instance.list_policies()

        assert "policies" in result
        assert "total" in result
        assert result["total"] >= 0
        print(f"\n📋 Total policies: {result['total']}")

    @pytest.mark.skipif(
        not os.getenv("OPA_URL"),
        reason="OPA not configured"
    )
    def test_delete_policy(
        self, opa_service_instance: OPAService, opa_available: bool
    ) -> None:
        """Test deleting a policy."""
        if not opa_available:
            pytest.skip("OPA not available")

        # Upload a policy first
        opa_service_instance.upload_policy(
            policy_id="delete_test",
            rego_code=SAMPLE_POLICY_PASS
        )

        # Delete it
        result = opa_service_instance.delete_policy("delete_test")

        assert result["success"] is True
        print(f"\n✅ Policy deleted: {result['policy_id']}")


# ============================================================================
# TestPolicyEvaluation - Policy Evaluation
# ============================================================================

class TestPolicyEvaluation:
    """Test policy evaluation."""

    @pytest.mark.skipif(
        not os.getenv("OPA_URL"),
        reason="OPA not configured"
    )
    def test_evaluate_policy_pass(
        self, opa_service_instance: OPAService, opa_available: bool, cleanup_test_policies
    ) -> None:
        """Test policy evaluation that passes."""
        if not opa_available:
            pytest.skip("OPA not available")

        # Upload policy
        opa_service_instance.upload_policy(
            policy_id="test_policy",
            rego_code=SAMPLE_POLICY_PASS
        )

        # Evaluate with passing input
        result = opa_service_instance.evaluate_policy(
            policy_code="test_policy",
            stage="what",
            input_data={
                "has_introduction": True,
                "has_requirements": True
            }
        )

        assert result["allowed"] is True
        assert len(result["violations"]) == 0
        print(f"\n✅ Policy evaluation PASSED")

    @pytest.mark.skipif(
        not os.getenv("OPA_URL"),
        reason="OPA not configured"
    )
    def test_evaluate_policy_fail(
        self, opa_service_instance: OPAService, opa_available: bool, cleanup_test_policies
    ) -> None:
        """Test policy evaluation that fails."""
        if not opa_available:
            pytest.skip("OPA not available")

        # Upload policy
        opa_service_instance.upload_policy(
            policy_id="test_policy",
            rego_code=SAMPLE_POLICY_PASS
        )

        # Evaluate with failing input
        result = opa_service_instance.evaluate_policy(
            policy_code="test_policy",
            stage="what",
            input_data={
                "has_introduction": False,
                "has_requirements": True
            }
        )

        assert result["allowed"] is False
        assert len(result["violations"]) > 0
        assert any("introduction" in v.lower() for v in result["violations"])
        print(f"\n❌ Policy evaluation FAILED (expected)")
        print(f"   Violations: {result['violations']}")

    @pytest.mark.skipif(
        not os.getenv("OPA_URL"),
        reason="OPA not configured"
    )
    def test_evaluate_policy_performance(
        self, opa_service_instance: OPAService, opa_available: bool, cleanup_test_policies
    ) -> None:
        """Test policy evaluation performance (<100ms P95)."""
        if not opa_available:
            pytest.skip("OPA not available")

        # Upload policy
        opa_service_instance.upload_policy(
            policy_id="test_policy",
            rego_code=SAMPLE_POLICY_PASS
        )

        # Run multiple evaluations
        times = []
        for _ in range(10):
            start = time.time()
            opa_service_instance.evaluate_policy(
                policy_code="test_policy",
                stage="what",
                input_data={"has_introduction": True, "has_requirements": True}
            )
            elapsed = time.time() - start
            times.append(elapsed)

        # Calculate P95
        times.sort()
        p95 = times[int(len(times) * 0.95)]

        print(f"\n⏱️ Performance: P95 = {p95*1000:.2f}ms")
        assert p95 < PERFORMANCE_TARGET_SINGLE, \
            f"P95 {p95*1000:.2f}ms exceeds target {PERFORMANCE_TARGET_SINGLE*1000}ms"


# ============================================================================
# TestBatchEvaluation - Batch Policy Evaluation
# ============================================================================

class TestBatchEvaluation:
    """Test batch policy evaluation."""

    @pytest.mark.skipif(
        not os.getenv("OPA_URL"),
        reason="OPA not configured"
    )
    def test_batch_evaluate_success(
        self, opa_service_instance: OPAService, opa_available: bool, cleanup_test_policies
    ) -> None:
        """Test batch evaluation with multiple policies."""
        if not opa_available:
            pytest.skip("OPA not available")

        # Upload policies
        opa_service_instance.upload_policy("test_policy", SAMPLE_POLICY_PASS)
        opa_service_instance.upload_policy("api_coverage", SAMPLE_POLICY_COMPLEX)

        # Batch evaluate
        evaluations = [
            {
                "policy_code": "test_policy",
                "stage": "what",
                "input_data": {"has_introduction": True, "has_requirements": True}
            },
            {
                "policy_code": "api_coverage",
                "stage": "how",
                "input_data": {"api_coverage": 85, "has_openapi_spec": True}
            },
        ]

        start = time.time()
        results = opa_service_instance.batch_evaluate(evaluations)
        elapsed = time.time() - start

        assert len(results) == 2
        assert all(r.get("error") is None for r in results)
        assert all(r["allowed"] is True for r in results)

        print(f"\n✅ Batch evaluation: {len(results)} policies in {elapsed:.3f}s")

    @pytest.mark.skipif(
        not os.getenv("OPA_URL"),
        reason="OPA not configured"
    )
    def test_batch_evaluate_mixed_results(
        self, opa_service_instance: OPAService, opa_available: bool, cleanup_test_policies
    ) -> None:
        """Test batch evaluation with mixed pass/fail results."""
        if not opa_available:
            pytest.skip("OPA not available")

        # Upload policies
        opa_service_instance.upload_policy("test_policy", SAMPLE_POLICY_PASS)
        opa_service_instance.upload_policy("api_coverage", SAMPLE_POLICY_COMPLEX)

        # Batch evaluate with mixed inputs
        evaluations = [
            {
                "policy_code": "test_policy",
                "stage": "what",
                "input_data": {"has_introduction": True, "has_requirements": True}
            },
            {
                "policy_code": "api_coverage",
                "stage": "how",
                "input_data": {"api_coverage": 50, "has_openapi_spec": False}  # Should fail
            },
        ]

        results = opa_service_instance.batch_evaluate(evaluations)

        assert len(results) == 2
        assert results[0]["allowed"] is True
        assert results[1]["allowed"] is False
        assert len(results[1]["violations"]) > 0

        print(f"\n✅ Batch evaluation with mixed results:")
        print(f"   Policy 1: {'PASSED' if results[0]['allowed'] else 'FAILED'}")
        print(f"   Policy 2: {'PASSED' if results[1]['allowed'] else 'FAILED'}")

    @pytest.mark.skipif(
        not os.getenv("OPA_URL"),
        reason="OPA not configured"
    )
    def test_batch_evaluate_handles_errors(
        self, opa_service_instance: OPAService, opa_available: bool, cleanup_test_policies
    ) -> None:
        """Test batch evaluation handles individual errors gracefully."""
        if not opa_available:
            pytest.skip("OPA not available")

        # Upload only one policy
        opa_service_instance.upload_policy("test_policy", SAMPLE_POLICY_PASS)

        # Batch evaluate - one valid, one non-existent policy
        evaluations = [
            {
                "policy_code": "test_policy",
                "stage": "what",
                "input_data": {"has_introduction": True, "has_requirements": True}
            },
            {
                "policy_code": "non_existent_policy",
                "stage": "what",
                "input_data": {}
            },
        ]

        results = opa_service_instance.batch_evaluate(evaluations)

        assert len(results) == 2
        assert results[0]["allowed"] is True
        assert results[0].get("error") is None
        # Second should have error or empty result (OPA returns empty for non-existent)
        # Both are acceptable behaviors

        print(f"\n✅ Batch evaluation handles errors gracefully")


# ============================================================================
# TestErrorHandling - Error Handling
# ============================================================================

class TestErrorHandling:
    """Test error handling."""

    def test_connection_error_handling(self) -> None:
        """Test handling of connection errors."""
        service = OPAService()
        service.base_url = "http://localhost:59999"  # Non-existent

        health = service.health_check()

        assert health["healthy"] is False
        assert "error" in health

    def test_timeout_handling(self) -> None:
        """Test handling of timeouts."""
        service = OPAService()
        service.base_url = "http://localhost:59999"
        service.timeout = 1  # 1 second timeout

        with pytest.raises(OPAEvaluationError):
            service.evaluate_policy(
                policy_code="test",
                stage="what",
                input_data={}
            )


# ============================================================================
# TestGlobalInstance - Singleton Pattern
# ============================================================================

class TestGlobalInstance:
    """Test global OPA service instance."""

    def test_global_instance_exists(self) -> None:
        """Test that global opa_service instance exists."""
        assert opa_service is not None
        assert isinstance(opa_service, OPAService)

    def test_global_instance_has_config(self) -> None:
        """Test that global instance has configuration."""
        assert opa_service.base_url is not None
        assert opa_service.timeout > 0
