"""
Policy Factory - Test Data Generation

SDLC 5.2.0 Compliance - Test-Driven Development
Framework: Test Strategy 2026

Purpose:
    Generate Policy model instances and OPA policy data for testing.

Principles:
    1. Sensible defaults (realistic policy data)
    2. Override support (Partial[Policy])
    3. Valid OPA Rego syntax
    4. Policy pack support (pre-built policies)

Usage:
    # Get Policy instance
    policy = get_mock_policy()
    custom = get_mock_policy({"policy_type": "CUSTOM"})

    # Get OPA Rego policy
    opa_policy = get_mock_opa_policy_data()
    gate_policy = get_mock_opa_gate_policy_data({"gate_type": "G1"})

Reference:
    - Policy Model: backend/app/models/policy.py
    - OPA Integration: backend/app/services/opa_service.py
    - Test Strategy: docs/05-test/00-TEST-STRATEGY-2026.md § 3.5
"""

from datetime import datetime, UTC
from typing import Optional, Dict, Any, List
from uuid import uuid4


def get_mock_policy(overrides: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Factory for Policy model instance data.

    Returns a dictionary representing a Policy model instance with sensible defaults.
    Use this when you need a complete Policy object for testing.

    Args:
        overrides: Optional dict to override default values

    Returns:
        Dict with Policy model fields

    Examples:
        # Basic policy
        policy = get_mock_policy()

        # Custom policy
        custom = get_mock_policy({
            "policy_type": "CUSTOM",
            "policy_name": "Custom Test Coverage Policy",
        })

        # G1 gate policy
        g1_policy = get_mock_policy({
            "policy_type": "GATE",
            "policy_name": "G1 Design Ready Policy",
            "metadata": {"gate_type": "G1"},
        })
    """
    defaults = {
        "id": str(uuid4()),
        "policy_name": "Test Coverage Policy",
        "policy_type": "GATE",
        "policy_rego": """
package sdlc.gates.g3

default allow = false

allow {
    input.test_coverage >= 95
    input.tests_passing == true
}
        """.strip(),
        "policy_description": "Enforce 95%+ test coverage for G3 gates",
        "is_active": True,
        "severity": "ERROR",
        "metadata": {
            "gate_type": "G3",
            "required_coverage": 95,
        },
        "created_by": str(uuid4()),
        "created_at": datetime.now(UTC),
        "updated_at": datetime.now(UTC),
        "deleted_at": None,
    }

    return {**defaults, **(overrides or {})}


def get_mock_policy_data(overrides: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Factory for Policy data (API response format).

    Returns a dictionary suitable for API response serialization.

    Args:
        overrides: Optional dict to override default values

    Returns:
        Dict with Policy API response fields

    Examples:
        # API response data
        response_data = get_mock_policy_data()

        # Custom policy response
        policy_data = get_mock_policy_data({
            "policy_name": "Security Scan Policy",
            "severity": "ERROR",
        })
    """
    policy = get_mock_policy(overrides)

    api_safe_fields = {
        "id": policy["id"],
        "policy_name": policy["policy_name"],
        "policy_type": policy["policy_type"],
        "policy_description": policy["policy_description"],
        "is_active": policy["is_active"],
        "severity": policy["severity"],
        "metadata": policy["metadata"],
        "created_by": policy["created_by"],
        "created_at": policy["created_at"].isoformat() if isinstance(policy["created_at"], datetime) else policy["created_at"],
        "updated_at": policy["updated_at"].isoformat() if isinstance(policy["updated_at"], datetime) else policy["updated_at"],
    }

    return api_safe_fields


def get_mock_opa_policy_data(overrides: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Factory for OPA policy evaluation data.

    Returns a dictionary suitable for OPA REST API POST /v1/data/{path} request.

    Args:
        overrides: Optional dict to override default values

    Returns:
        Dict with OPA input data

    Examples:
        # OPA evaluation input
        opa_input = get_mock_opa_policy_data()
        response = requests.post(
            "http://opa:8181/v1/data/sdlc/gates/g3",
            json={"input": opa_input}
        )

        # Custom input data
        opa_input = get_mock_opa_policy_data({
            "test_coverage": 98,
            "tests_passing": True,
        })
    """
    defaults = {
        "test_coverage": 95,
        "tests_passing": True,
        "code_review_approved": True,
        "security_scan_passed": True,
    }

    return {**defaults, **(overrides or {})}


# ─────────────────────────────────────────────────────────────
# OPA Policy Rego Templates
# ─────────────────────────────────────────────────────────────

def get_mock_opa_gate_policy_rego(gate_type: str = "G1") -> str:
    """
    Generate OPA Rego policy for specific gate type.

    Args:
        gate_type: Gate type (G0_1, G0_2, G1, G2, G3, etc.)

    Returns:
        OPA Rego policy string

    Examples:
        # G1 policy
        g1_rego = get_mock_opa_gate_policy_rego("G1")

        # G3 policy
        g3_rego = get_mock_opa_gate_policy_rego("G3")
    """
    gate_policies = {
        "G0_1": """
package sdlc.gates.g01

default allow = false

allow {
    input.user_interviews_count >= 5
    input.problem_statement_validated == true
    input.user_personas_defined == true
}
        """.strip(),

        "G0_2": """
package sdlc.gates.g02

default allow = false

allow {
    input.solution_alternatives_count >= 3
    input.tradeoffs_documented == true
    input.recommended_solution_justified == true
}
        """.strip(),

        "G1": """
package sdlc.gates.g1

default allow = false

allow {
    input.architecture_documented == true
    input.api_contracts_defined == true
    input.data_model_reviewed == true
}
        """.strip(),

        "G2": """
package sdlc.gates.g2

default allow = false

allow {
    input.technical_design_complete == true
    input.security_review_passed == true
    input.deployment_plan_ready == true
}
        """.strip(),

        "G3": """
package sdlc.gates.g3

default allow = false

allow {
    input.test_coverage >= 95
    input.tests_passing == true
    input.code_review_completed == true
}
        """.strip(),
    }

    return gate_policies.get(gate_type, gate_policies["G1"])


def get_mock_opa_gate_policy_data(gate_type: str = "G1", overrides: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Factory for gate-specific OPA policy data.

    Args:
        gate_type: Gate type (G0_1, G0_2, G1, G2, G3, etc.)
        overrides: Optional dict to override default values

    Returns:
        Dict with OPA policy data including Rego

    Examples:
        # G1 policy
        g1_policy = get_mock_opa_gate_policy_data("G1")

        # G3 policy
        g3_policy = get_mock_opa_gate_policy_data("G3")
    """
    gate_defaults = {
        "G0_1": {
            "policy_name": "G0.1 Foundation Ready Policy",
            "policy_rego": get_mock_opa_gate_policy_rego("G0_1"),
            "metadata": {"gate_type": "G0_1", "stage": "WHY"},
        },
        "G0_2": {
            "policy_name": "G0.2 Solution Diversity Policy",
            "policy_rego": get_mock_opa_gate_policy_rego("G0_2"),
            "metadata": {"gate_type": "G0_2", "stage": "WHY"},
        },
        "G1": {
            "policy_name": "G1 Design Ready Policy",
            "policy_rego": get_mock_opa_gate_policy_rego("G1"),
            "metadata": {"gate_type": "G1", "stage": "WHAT"},
        },
        "G2": {
            "policy_name": "G2 Ship Ready Policy",
            "policy_rego": get_mock_opa_gate_policy_rego("G2"),
            "metadata": {"gate_type": "G2", "stage": "HOW"},
        },
        "G3": {
            "policy_name": "G3 Build Complete Policy",
            "policy_rego": get_mock_opa_gate_policy_rego("G3"),
            "metadata": {"gate_type": "G3", "stage": "BUILD"},
        },
    }

    defaults = gate_defaults.get(gate_type, gate_defaults["G1"])
    return get_mock_policy({**defaults, **(overrides or {})})


# ─────────────────────────────────────────────────────────────
# Policy Pack Factories
# ─────────────────────────────────────────────────────────────

def get_mock_policy_pack(pack_name: str = "default") -> List[Dict[str, Any]]:
    """
    Factory for policy pack (collection of related policies).

    Args:
        pack_name: Policy pack name (default, security, quality, compliance)

    Returns:
        List of policy dicts

    Examples:
        # Default policy pack
        policies = get_mock_policy_pack("default")

        # Security policy pack
        security_policies = get_mock_policy_pack("security")
    """
    policy_packs = {
        "default": [
            get_mock_opa_gate_policy_data("G0_1"),
            get_mock_opa_gate_policy_data("G0_2"),
            get_mock_opa_gate_policy_data("G1"),
            get_mock_opa_gate_policy_data("G2"),
            get_mock_opa_gate_policy_data("G3"),
        ],
        "security": [
            get_mock_policy({
                "policy_name": "OWASP ASVS Level 2 Policy",
                "policy_type": "SECURITY",
                "severity": "ERROR",
            }),
            get_mock_policy({
                "policy_name": "Semgrep SAST Policy",
                "policy_type": "SECURITY",
                "severity": "ERROR",
            }),
        ],
        "quality": [
            get_mock_policy({
                "policy_name": "Test Coverage Policy",
                "policy_type": "QUALITY",
                "severity": "ERROR",
            }),
            get_mock_policy({
                "policy_name": "Code Review Policy",
                "policy_type": "QUALITY",
                "severity": "WARNING",
            }),
        ],
    }

    return policy_packs.get(pack_name, policy_packs["default"])
