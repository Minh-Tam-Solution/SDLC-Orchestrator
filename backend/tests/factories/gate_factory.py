"""
Gate Factory - Test Data Generation

SDLC 5.2.0 Compliance - Test-Driven Development
Framework: Test Strategy 2026

Purpose:
    Generate Gate model instances and data dictionaries for testing.

Principles:
    1. Sensible defaults (realistic gate data)
    2. Override support (Partial[Gate])
    3. Valid model instances (pass validation)
    4. SDLC 5.2.0 gates (G0.1, G0.2, G1, G2... G9)

Usage:
    # Get Gate instance
    gate = get_mock_gate()
    g1 = get_mock_gate({"gate_type": "G1_DESIGN_READY", "stage": "WHAT"})

    # Get data dict (for API requests)
    gate_data = get_mock_gate_data()
    create_data = get_mock_gate_create_data({"gate_name": "Auth Gate"})

Reference:
    - Gate Model: backend/app/models/gate.py
    - Test Strategy: docs/05-test/00-TEST-STRATEGY-2026.md § 3.5
    - SDLC 5.2.0 Gates: SDLC-Enterprise-Framework/03-Templates-Tools/Gate-Templates/
"""

from datetime import datetime, UTC
from typing import Optional, Dict, Any, List
from uuid import uuid4


def get_mock_gate(overrides: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Factory for Gate model instance data.

    Returns a dictionary representing a Gate model instance with sensible defaults.
    Use this when you need a complete Gate object for testing.

    Args:
        overrides: Optional dict to override default values

    Returns:
        Dict with Gate model fields

    Examples:
        # Basic gate (G1 Design Ready)
        gate = get_mock_gate()

        # Approved gate
        approved = get_mock_gate({
            "status": "APPROVED",
            "approved_at": datetime.now(UTC),
        })

        # G0.1 Foundation Ready gate
        g01 = get_mock_gate({
            "gate_type": "G0_1_FOUNDATION_READY",
            "stage": "WHY",
            "exit_criteria": ["User interviews completed", "Problem defined"],
        })
    """
    defaults = {
        "id": str(uuid4()),
        "gate_name": "Test Gate - G1 Design Ready",
        "gate_type": "G1_DESIGN_READY",
        "stage": "WHAT",
        "project_id": str(uuid4()),
        "created_by": str(uuid4()),
        "status": "DRAFT",
        "exit_criteria": [
            "Architecture documented",
            "API contracts defined",
            "Data model reviewed",
        ],
        "description": "Design Ready gate for test project",
        "approved_at": None,
        "rejected_at": None,
        "archived_at": None,
        "created_at": datetime.now(UTC),
        "updated_at": datetime.now(UTC),
        "deleted_at": None,
    }

    return {**defaults, **(overrides or {})}


def get_mock_gate_data(overrides: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Factory for Gate data (API response format).

    Returns a dictionary suitable for API response serialization.

    Args:
        overrides: Optional dict to override default values

    Returns:
        Dict with Gate API response fields

    Examples:
        # API response data
        response_data = get_mock_gate_data()

        # Custom gate response
        gate_data = get_mock_gate_data({
            "gate_name": "Authentication - G1",
            "status": "APPROVED",
        })
    """
    gate = get_mock_gate(overrides)

    api_safe_fields = {
        "id": gate["id"],
        "gate_name": gate["gate_name"],
        "gate_type": gate["gate_type"],
        "stage": gate["stage"],
        "project_id": gate["project_id"],
        "created_by": gate["created_by"],
        "status": gate["status"],
        "exit_criteria": gate["exit_criteria"],
        "description": gate["description"],
        "approved_at": gate["approved_at"].isoformat() if gate["approved_at"] and isinstance(gate["approved_at"], datetime) else gate["approved_at"],
        "rejected_at": gate["rejected_at"].isoformat() if gate["rejected_at"] and isinstance(gate["rejected_at"], datetime) else gate["rejected_at"],
        "created_at": gate["created_at"].isoformat() if isinstance(gate["created_at"], datetime) else gate["created_at"],
        "updated_at": gate["updated_at"].isoformat() if isinstance(gate["updated_at"], datetime) else gate["updated_at"],
    }

    return api_safe_fields


def get_mock_gate_create_data(overrides: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Factory for Gate creation request data (API POST payload).

    Returns a dictionary suitable for API POST /api/v1/gates request.
    Contains only fields required for gate creation.

    Args:
        overrides: Optional dict to override default values

    Returns:
        Dict with Gate creation request fields

    Examples:
        # Create gate request
        create_data = get_mock_gate_create_data()
        response = client.post("/api/v1/gates", json=create_data)

        # Create G0.1 gate
        g01_data = get_mock_gate_create_data({
            "gate_name": "Instagram Clone - G0.1",
            "gate_type": "G0_1_FOUNDATION_READY",
            "stage": "WHY",
        })
    """
    defaults = {
        "gate_name": "Test Gate - G1 Design Ready",
        "gate_type": "G1_DESIGN_READY",
        "stage": "WHAT",
        "project_id": str(uuid4()),
        "description": "Design Ready gate for test project",
        "exit_criteria": [
            "Architecture documented",
            "API contracts defined",
            "Data model reviewed",
        ],
    }

    return {**defaults, **(overrides or {})}


def get_mock_gate_approval_data(overrides: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Factory for Gate approval request data (API POST /api/v1/gates/{id}/approve).

    Args:
        overrides: Optional dict to override default values

    Returns:
        Dict with Gate approval request fields

    Examples:
        # Approve gate
        approval_data = get_mock_gate_approval_data()
        response = client.post(f"/api/v1/gates/{gate_id}/approve", json=approval_data)

        # Approve with comment
        approval_data = get_mock_gate_approval_data({
            "comment": "All exit criteria met. Approved.",
        })
    """
    defaults = {
        "comment": "Gate approved - all exit criteria met",
    }

    return {**defaults, **(overrides or {})}


def get_mock_gate_rejection_data(overrides: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Factory for Gate rejection request data (API POST /api/v1/gates/{id}/reject).

    Args:
        overrides: Optional dict to override default values

    Returns:
        Dict with Gate rejection request fields

    Examples:
        # Reject gate
        rejection_data = get_mock_gate_rejection_data()
        response = client.post(f"/api/v1/gates/{gate_id}/reject", json=rejection_data)

        # Reject with specific reason
        rejection_data = get_mock_gate_rejection_data({
            "reason": "API contracts incomplete - missing error handling specs",
        })
    """
    defaults = {
        "reason": "Exit criteria not met - please review and resubmit",
    }

    return {**defaults, **(overrides or {})}


# ─────────────────────────────────────────────────────────────
# SDLC 5.2.0 Gate-Specific Factories
# ─────────────────────────────────────────────────────────────

def get_mock_g01_gate(overrides: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Factory for G0.1 Foundation Ready gate"""
    g01_defaults = {
        "gate_name": "G0.1 Foundation Ready",
        "gate_type": "G0_1_FOUNDATION_READY",
        "stage": "WHY",
        "exit_criteria": [
            "User interviews completed (5+ users)",
            "Problem statement validated",
            "User personas defined",
        ],
        "description": "Foundation Ready - Problem definition validated",
    }
    return get_mock_gate({**g01_defaults, **(overrides or {})})


def get_mock_g02_gate(overrides: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Factory for G0.2 Solution Diversity gate"""
    g02_defaults = {
        "gate_name": "G0.2 Solution Diversity",
        "gate_type": "G0_2_SOLUTION_DIVERSITY",
        "stage": "WHY",
        "exit_criteria": [
            "3+ solution alternatives evaluated",
            "Trade-offs documented",
            "Recommended solution justified",
        ],
        "description": "Solution Diversity - Multiple solutions explored",
    }
    return get_mock_gate({**g02_defaults, **(overrides or {})})


def get_mock_g1_gate(overrides: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Factory for G1 Design Ready gate"""
    g1_defaults = {
        "gate_name": "G1 Design Ready",
        "gate_type": "G1_DESIGN_READY",
        "stage": "WHAT",
        "exit_criteria": [
            "Architecture documented",
            "API contracts defined",
            "Data model reviewed",
        ],
        "description": "Design Ready - Architecture and contracts complete",
    }
    return get_mock_gate({**g1_defaults, **(overrides or {})})


def get_mock_g2_gate(overrides: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Factory for G2 Ship Ready gate"""
    g2_defaults = {
        "gate_name": "G2 Ship Ready",
        "gate_type": "G2_SHIP_READY",
        "stage": "HOW",
        "exit_criteria": [
            "Technical design complete",
            "Security review passed",
            "Deployment plan ready",
        ],
        "description": "Ship Ready - Technical design validated",
    }
    return get_mock_gate({**g2_defaults, **(overrides or {})})


def get_mock_g3_gate(overrides: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Factory for G3 Build Complete gate"""
    g3_defaults = {
        "gate_name": "G3 Build Complete",
        "gate_type": "G3_BUILD_COMPLETE",
        "stage": "BUILD",
        "exit_criteria": [
            "All features implemented",
            "Unit tests 95%+ coverage",
            "Code review completed",
        ],
        "description": "Build Complete - Implementation finished",
    }
    return get_mock_gate({**g3_defaults, **(overrides or {})})
