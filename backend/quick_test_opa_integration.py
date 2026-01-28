#!/usr/bin/env python3
"""
=========================================================================
Quick OPA Integration Test - Sprint 111 Day 5
SDLC Orchestrator - Infrastructure Services Layer

Version: 1.0.0
Date: January 28, 2026

Purpose:
- Quick validation of OPA integration
- Test without full pytest setup
- Verify policy upload, evaluation, and management

Usage:
    # With OPA container running:
    OPA_URL=http://localhost:8185 python quick_test_opa_integration.py

    # Default (localhost:8185):
    python quick_test_opa_integration.py

Expected Output:
    ✅ Service Initialization: PASSED
    ✅ Health Check: PASSED (OPA healthy)
    ✅ Policy Upload: PASSED
    ✅ Policy Evaluation (Pass): PASSED
    ✅ Policy Evaluation (Fail): PASSED
    ✅ Batch Evaluation: PASSED
    ✅ Policy Delete: PASSED

    Summary: 7/7 tests passed
=========================================================================
"""

import os
import sys
import time
from typing import Any

# Add app to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.services.opa_service import (
    OPAEvaluationError,
    OPAService,
)


# ============================================================================
# Configuration
# ============================================================================

OPA_URL = os.getenv("OPA_URL", "http://localhost:8185")


# ============================================================================
# Test Policies
# ============================================================================

SAMPLE_POLICY = """
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


# ============================================================================
# Test Functions
# ============================================================================

def test_service_initialization() -> tuple[bool, str]:
    """Test 1: Service initializes correctly."""
    try:
        service = OPAService()
        service.base_url = OPA_URL

        if not service.base_url:
            return False, "No base URL configured"
        if service.timeout <= 0:
            return False, "Invalid timeout"

        return True, "Service initialized correctly"

    except Exception as e:
        return False, f"Exception: {str(e)}"


def test_health_check() -> tuple[bool, str]:
    """Test 2: Health check returns valid data."""
    try:
        service = OPAService()
        service.base_url = OPA_URL
        health = service.health_check()

        if not isinstance(health, dict):
            return False, "Health check did not return dict"

        if health.get("healthy"):
            version = health.get("version", "unknown")
            return True, f"OPA healthy (v{version})"
        else:
            error = health.get("error", "Unknown error")
            return False, f"OPA not healthy: {error}"

    except Exception as e:
        return False, f"Exception: {str(e)}"


def test_policy_upload() -> tuple[bool, str]:
    """Test 3: Policy upload works."""
    try:
        service = OPAService()
        service.base_url = OPA_URL

        if not service.health_check().get("healthy"):
            return None, "OPA not available (skipped)"  # type: ignore

        result = service.upload_policy(
            policy_id="test_policy",
            rego_code=SAMPLE_POLICY
        )

        if result.get("success"):
            return True, f"Policy '{result['policy_id']}' uploaded"
        else:
            return False, f"Upload failed: {result.get('message')}"

    except OPAEvaluationError as e:
        return False, f"OPAError: {str(e)}"
    except Exception as e:
        return False, f"Exception: {str(e)}"


def test_policy_evaluation_pass() -> tuple[bool, str]:
    """Test 4: Policy evaluation (pass case)."""
    try:
        service = OPAService()
        service.base_url = OPA_URL

        if not service.health_check().get("healthy"):
            return None, "OPA not available (skipped)"  # type: ignore

        # Ensure policy is uploaded
        service.upload_policy("test_policy", SAMPLE_POLICY)

        start = time.time()
        result = service.evaluate_policy(
            policy_code="test_policy",
            stage="what",
            input_data={
                "has_introduction": True,
                "has_requirements": True
            }
        )
        elapsed = time.time() - start

        if result.get("allowed"):
            return True, f"PASSED in {elapsed*1000:.0f}ms"
        else:
            return False, f"Expected PASS but got FAIL: {result.get('violations')}"

    except OPAEvaluationError as e:
        return False, f"OPAError: {str(e)}"
    except Exception as e:
        return False, f"Exception: {str(e)}"


def test_policy_evaluation_fail() -> tuple[bool, str]:
    """Test 5: Policy evaluation (fail case)."""
    try:
        service = OPAService()
        service.base_url = OPA_URL

        if not service.health_check().get("healthy"):
            return None, "OPA not available (skipped)"  # type: ignore

        # Ensure policy is uploaded
        service.upload_policy("test_policy", SAMPLE_POLICY)

        result = service.evaluate_policy(
            policy_code="test_policy",
            stage="what",
            input_data={
                "has_introduction": False,  # This should cause failure
                "has_requirements": True
            }
        )

        if not result.get("allowed"):
            violations = result.get("violations", [])
            if violations:
                return True, f"FAILED (expected) with {len(violations)} violations"
            else:
                return True, "FAILED (expected)"
        else:
            return False, "Expected FAIL but got PASS"

    except OPAEvaluationError as e:
        return False, f"OPAError: {str(e)}"
    except Exception as e:
        return False, f"Exception: {str(e)}"


def test_batch_evaluation() -> tuple[bool, str]:
    """Test 6: Batch evaluation works."""
    try:
        service = OPAService()
        service.base_url = OPA_URL

        if not service.health_check().get("healthy"):
            return None, "OPA not available (skipped)"  # type: ignore

        # Ensure policy is uploaded
        service.upload_policy("test_policy", SAMPLE_POLICY)

        evaluations = [
            {
                "policy_code": "test_policy",
                "stage": "what",
                "input_data": {"has_introduction": True, "has_requirements": True}
            },
            {
                "policy_code": "test_policy",
                "stage": "what",
                "input_data": {"has_introduction": False, "has_requirements": False}
            },
        ]

        start = time.time()
        results = service.batch_evaluate(evaluations)
        elapsed = time.time() - start

        if len(results) != 2:
            return False, f"Expected 2 results, got {len(results)}"

        passed = sum(1 for r in results if r.get("allowed"))
        failed = len(results) - passed

        return True, f"{passed} passed, {failed} failed in {elapsed*1000:.0f}ms"

    except Exception as e:
        return False, f"Exception: {str(e)}"


def test_policy_delete() -> tuple[bool, str]:
    """Test 7: Policy delete works."""
    try:
        service = OPAService()
        service.base_url = OPA_URL

        if not service.health_check().get("healthy"):
            return None, "OPA not available (skipped)"  # type: ignore

        result = service.delete_policy("test_policy")

        if result.get("success"):
            return True, f"Policy '{result['policy_id']}' deleted"
        else:
            return False, f"Delete failed: {result.get('message')}"

    except OPAEvaluationError as e:
        # Policy might not exist, which is OK
        if "404" in str(e) or "not found" in str(e).lower():
            return True, "Policy already deleted or not found"
        return False, f"OPAError: {str(e)}"
    except Exception as e:
        return False, f"Exception: {str(e)}"


# ============================================================================
# Main
# ============================================================================

def main() -> int:
    """Run all quick tests."""
    print("=" * 70)
    print("OPA Integration Test - Sprint 111 Day 5")
    print("=" * 70)
    print(f"\nOPA URL: {OPA_URL}")
    print("")

    tests = [
        ("Service Initialization", test_service_initialization),
        ("Health Check", test_health_check),
        ("Policy Upload", test_policy_upload),
        ("Policy Evaluation (Pass)", test_policy_evaluation_pass),
        ("Policy Evaluation (Fail)", test_policy_evaluation_fail),
        ("Batch Evaluation", test_batch_evaluation),
        ("Policy Delete", test_policy_delete),
    ]

    passed = 0
    failed = 0
    skipped = 0

    results = []

    for name, test_func in tests:
        try:
            success, message = test_func()

            if success is None:
                status = "⏭️ SKIPPED"
                skipped += 1
            elif success:
                status = "✅ PASSED"
                passed += 1
            else:
                status = "❌ FAILED"
                failed += 1

            results.append((name, status, message))

        except Exception as e:
            results.append((name, "❌ ERROR", str(e)))
            failed += 1

    # Print results
    print("Results:")
    print("-" * 70)
    for name, status, message in results:
        print(f"  {status} {name}: {message}")

    print("")
    print("=" * 70)
    print(f"Summary: {passed} passed, {failed} failed, {skipped} skipped")
    print("=" * 70)

    # Connection info
    print("")
    if failed > 0:
        print("⚠️ Some tests failed. Check:")
        print("   1. Is OPA running? docker-compose up -d opa")
        print("   2. Check port: curl http://localhost:8185/health")
        print("   3. Environment: export OPA_URL=http://localhost:8185")
    elif skipped > 0:
        print("⚠️ Some tests skipped (OPA not available)")
        print("   Start OPA: docker-compose up -d opa")
    else:
        print("✅ All tests passed! OPA integration is working.")

    return 1 if failed > 0 else 0


if __name__ == "__main__":
    sys.exit(main())
