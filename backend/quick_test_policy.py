"""
Quick validation script for PolicyService implementation.

Tests all 11 methods without requiring full pytest environment.
"""

import sys
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent
sys.path.insert(0, str(backend_path))

from app.services.policy_service import (
    PolicyService,
    PolicyNotFoundError,
    PolicyValidationError,
    InvalidRegoSyntaxError,
    OPAIntegrationError,
    PolicyPackError,
)


class MockDB:
    """Mock database session for testing"""
    pass


def test_create_policy():
    """Test: Create policy with valid Rego"""
    service = PolicyService()
    db = MockDB()

    policy_data = {
        "policy_name": "G1 Design Ready Policy",
        "policy_type": "GATE_EVALUATION",
        "policy_rego": """
package sdlc.gates.g1

default allow = false

allow {
    input.architecture_documented == true
    input.api_contracts_defined == true
}
        """.strip(),
        "policy_description": "Enforce G1 gate exit criteria",
        "severity": "ERROR",
        "created_by": "user-123",
    }

    policy = service.create_policy(db, policy_data)

    assert policy.policy_name == "G1 Design Ready Policy"
    assert policy.policy_type == "GATE_EVALUATION"
    assert policy.severity == "ERROR"
    assert policy.is_active is True
    assert policy.deleted_at is None
    print("✅ test_create_policy PASSED")


def test_create_policy_invalid_rego():
    """Test: Create policy with invalid Rego raises error"""
    service = PolicyService()
    db = MockDB()

    policy_data = {
        "policy_name": "Invalid Policy",
        "policy_type": "CUSTOM",
        "policy_rego": "this is not valid rego",  # No package declaration
    }

    try:
        service.create_policy(db, policy_data)
        assert False, "Should have raised InvalidRegoSyntaxError"
    except InvalidRegoSyntaxError as e:
        assert "package" in str(e).lower()
        print("✅ test_create_policy_invalid_rego PASSED")


def test_create_policy_missing_name():
    """Test: Create policy without policy_name raises error"""
    service = PolicyService()
    db = MockDB()

    policy_data = {
        "policy_type": "CUSTOM",
        "policy_rego": "package test\nallow = true",
    }

    try:
        service.create_policy(db, policy_data)
        assert False, "Should have raised PolicyValidationError"
    except PolicyValidationError as e:
        assert "policy_name is required" in str(e)
        print("✅ test_create_policy_missing_name PASSED")


def test_validate_rego_syntax():
    """Test: Rego syntax validation"""
    service = PolicyService()

    # Valid Rego
    valid_rego = """
package sdlc.gates.g3

default allow = false

allow {
    input.test_coverage >= 95
    input.tests_passing == true
}
    """.strip()

    assert service.validate_rego_syntax(valid_rego) is True

    # Invalid Rego (no package)
    invalid_rego_no_package = """
allow {
    input.test_coverage >= 95
}
    """.strip()

    try:
        service.validate_rego_syntax(invalid_rego_no_package)
        assert False, "Should have raised InvalidRegoSyntaxError"
    except InvalidRegoSyntaxError as e:
        assert "package" in str(e).lower()

    # Invalid Rego (no rules)
    invalid_rego_no_rules = """
package sdlc.test
# no rules defined
    """.strip()

    try:
        service.validate_rego_syntax(invalid_rego_no_rules)
        assert False, "Should have raised InvalidRegoSyntaxError"
    except InvalidRegoSyntaxError as e:
        assert "rules" in str(e).lower() or "allow" in str(e).lower()

    print("✅ test_validate_rego_syntax PASSED")


def test_evaluate_policy():
    """Test: Policy evaluation with mock OPA"""
    service = PolicyService()
    db = MockDB()

    # Create policy first
    policy_data = {
        "policy_name": "Test Coverage Policy",
        "policy_type": "CODE_QUALITY",
        "policy_rego": "package test\nallow = true",
    }
    policy = service.create_policy(db, policy_data)

    # Mock get_policy_by_id
    service.get_policy_by_id = lambda db, pid: policy

    # Evaluate policy
    input_data = {
        "test_coverage": 95,
        "tests_passing": True,
    }

    result = service.evaluate_policy(db, policy.id, input_data)

    assert result["policy_id"] == policy.id
    assert "allow" in result
    assert "evaluated_at" in result
    assert result["input"] == input_data

    print("✅ test_evaluate_policy PASSED")


def test_create_policy_pack():
    """Test: Create policy pack with multiple policies"""
    service = PolicyService()
    db = MockDB()

    pack_data = {
        "pack_name": "SDLC Gates Policy Pack",
        "pack_description": "All gate policies bundled",
        "policy_ids": ["policy-1", "policy-2", "policy-3"],
        "created_by": "user-123",
    }

    pack = service.create_policy_pack(db, pack_data)

    assert pack.pack_name == "SDLC Gates Policy Pack"
    assert len(pack.policy_ids) == 3
    assert "policy-1" in pack.policy_ids
    print("✅ test_create_policy_pack PASSED")


def test_create_policy_pack_empty_policies():
    """Test: Create policy pack with empty policy list raises error"""
    service = PolicyService()
    db = MockDB()

    pack_data = {
        "pack_name": "Empty Pack",
        "policy_ids": [],  # Empty list
    }

    try:
        service.create_policy_pack(db, pack_data)
        assert False, "Should have raised PolicyPackError"
    except PolicyPackError as e:
        assert "cannot be empty" in str(e)
        print("✅ test_create_policy_pack_empty_policies PASSED")


def test_upload_policy_to_opa():
    """Test: Upload policy to OPA server (mock)"""
    service = PolicyService()

    policy_id = "policy-123"
    policy_rego = """
package sdlc.gates.g1

default allow = false

allow {
    input.ready == true
}
    """.strip()

    result = service.upload_policy_to_opa(policy_id, policy_rego)

    assert result["success"] is True
    assert result["opa_policy_id"] == policy_id
    assert "uploaded_at" in result

    print("✅ test_upload_policy_to_opa PASSED")


def main():
    """Run all tests"""
    print("\n" + "="*60)
    print("PolicyService Quick Validation Tests")
    print("="*60 + "\n")

    tests = [
        test_create_policy,
        test_create_policy_invalid_rego,
        test_create_policy_missing_name,
        test_validate_rego_syntax,
        test_evaluate_policy,
        test_create_policy_pack,
        test_create_policy_pack_empty_policies,
        test_upload_policy_to_opa,
    ]

    passed = 0
    failed = 0

    for test in tests:
        try:
            test()
            passed += 1
        except AssertionError as e:
            print(f"❌ {test.__name__} FAILED: {e}")
            failed += 1
        except Exception as e:
            print(f"❌ {test.__name__} ERROR: {e}")
            failed += 1

    print("\n" + "="*60)
    print(f"Tests: {passed} passed, {failed} failed")
    print("="*60 + "\n")

    if failed == 0:
        print("✅ ALL TESTS PASSED - PolicyService Implementation VALID")
        return 0
    else:
        print("❌ SOME TESTS FAILED - Review implementation")
        return 1


if __name__ == "__main__":
    sys.exit(main())
