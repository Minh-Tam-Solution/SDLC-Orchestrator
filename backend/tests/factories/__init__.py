"""
Test Factories for SDLC Orchestrator

SDLC 5.2.0 Compliance - Test-Driven Development
Framework: Test Strategy 2026

Purpose:
    Provide reusable factory functions for creating test data.
    Follows Factory Pattern from .claude/skills/testing-patterns.

Usage:
    from tests.factories import get_mock_user, get_mock_gate

    user = get_mock_user()
    gate = get_mock_gate({"status": "approved"})

Principles:
    1. ALWAYS use factories (no hardcoded test data)
    2. Provide sensible defaults
    3. Allow overriding specific properties
    4. Return valid model instances

Reference:
    - Test Strategy: docs/05-test/00-TEST-STRATEGY-2026.md
    - Factory Pattern Guide: docs/05-test/FACTORY-PATTERN-GUIDE.md (TBD)
"""

from .user_factory import (
    get_mock_user,
    get_mock_user_data,
    get_mock_user_create_data,
)
from .project_factory import (
    get_mock_project,
    get_mock_project_data,
    get_mock_project_create_data,
)
from .gate_factory import (
    get_mock_gate,
    get_mock_gate_data,
    get_mock_gate_create_data,
)
from .evidence_factory import (
    get_mock_evidence,
    get_mock_evidence_data,
    get_mock_evidence_upload_data,
)
from .policy_factory import (
    get_mock_policy,
    get_mock_policy_data,
    get_mock_opa_policy_data,
)
from .codegen_factory import (
    get_mock_codegen_spec,
    get_mock_codegen_result,
    get_mock_codegen_blueprint,
)

__all__ = [
    # User factories
    "get_mock_user",
    "get_mock_user_data",
    "get_mock_user_create_data",
    # Project factories
    "get_mock_project",
    "get_mock_project_data",
    "get_mock_project_create_data",
    # Gate factories
    "get_mock_gate",
    "get_mock_gate_data",
    "get_mock_gate_create_data",
    # Evidence factories
    "get_mock_evidence",
    "get_mock_evidence_data",
    "get_mock_evidence_upload_data",
    # Policy factories
    "get_mock_policy",
    "get_mock_policy_data",
    "get_mock_opa_policy_data",
    # Codegen factories
    "get_mock_codegen_spec",
    "get_mock_codegen_result",
    "get_mock_codegen_blueprint",
]
