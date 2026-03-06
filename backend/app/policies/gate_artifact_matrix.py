"""
Gate Artifact Matrix — per-gate per-tier required artifact types.

Sprint 223: Cross-project review finding (EndiorBot Sprint 80 gap G2).
Separated from tier_policies.py per CTO directive (separation of concerns).

Usage:
    from app.policies.gate_artifact_matrix import get_required_artifacts, check_artifact_completeness

    required = get_required_artifacts("G2", "ENTERPRISE")
    # ["ADR", "THREAT_MODEL", "SECURITY_BASELINE", "TEST_PLAN"]

    result = check_artifact_completeness("G2", "ENTERPRISE", ["ADR", "TEST_PLAN"])
    # ArtifactCheckResult(passed=False, missing=["THREAT_MODEL", "SECURITY_BASELINE"], ...)
"""

from __future__ import annotations

from dataclasses import dataclass


# Canonical artifact type identifiers (match evidence_type in gate_evidence table)
ARTIFACT_TYPES = {
    "BRD": "Business Requirements Document",
    "PRD": "Product Requirements Document",
    "ADR": "Architecture Decision Record",
    "THREAT_MODEL": "Security Threat Model",
    "SECURITY_BASELINE": "Security Baseline Assessment",
    "TEST_PLAN": "Test Plan",
    "TEST_RESULTS": "Test Execution Results",
    "CODE_REVIEW": "Code Review Record",
    "DEPLOYMENT_PROOF": "Deployment Proof / Health Check",
    "RUNBOOK": "Operations Runbook",
    "USER_GUIDE": "User Guide / Documentation",
    "SAST_REPORT": "SAST Security Scan Report",
    "COMPLIANCE_REPORT": "Compliance Assessment Report",
}

# Gate → Tier → Required artifact types
# LITE: advisory only — no mandatory artifacts
# STANDARD: basic requirements
# PROFESSIONAL: full requirements
# ENTERPRISE: strictest requirements
GATE_ARTIFACT_MATRIX: dict[str, dict[str, list[str]]] = {
    "G0.1": {
        "LITE": [],
        "STANDARD": ["BRD"],
        "PROFESSIONAL": ["BRD"],
        "ENTERPRISE": ["BRD"],
    },
    "G0.2": {
        "LITE": [],
        "STANDARD": ["BRD"],
        "PROFESSIONAL": ["BRD", "PRD"],
        "ENTERPRISE": ["BRD", "PRD"],
    },
    "G1": {
        "LITE": [],
        "STANDARD": ["BRD"],
        "PROFESSIONAL": ["BRD", "PRD"],
        "ENTERPRISE": ["BRD", "PRD", "ADR"],
    },
    "G2": {
        "LITE": [],
        "STANDARD": ["ADR"],
        "PROFESSIONAL": ["ADR", "TEST_PLAN", "SECURITY_BASELINE"],
        "ENTERPRISE": ["ADR", "THREAT_MODEL", "SECURITY_BASELINE", "TEST_PLAN"],
    },
    "G3": {
        "LITE": [],
        "STANDARD": ["TEST_RESULTS", "CODE_REVIEW"],
        "PROFESSIONAL": ["TEST_RESULTS", "CODE_REVIEW", "SAST_REPORT"],
        "ENTERPRISE": [
            "TEST_RESULTS", "CODE_REVIEW", "SAST_REPORT",
            "DEPLOYMENT_PROOF", "COMPLIANCE_REPORT",
        ],
    },
    "G4": {
        "LITE": [],
        "STANDARD": ["TEST_RESULTS", "DEPLOYMENT_PROOF"],
        "PROFESSIONAL": ["TEST_RESULTS", "DEPLOYMENT_PROOF", "RUNBOOK"],
        "ENTERPRISE": [
            "TEST_RESULTS", "DEPLOYMENT_PROOF", "RUNBOOK",
            "USER_GUIDE", "COMPLIANCE_REPORT",
        ],
    },
}


@dataclass
class ArtifactCheckResult:
    """Result of checking artifact completeness against the matrix."""
    passed: bool
    gate_type: str
    tier: str
    required: list[str]
    submitted: list[str]
    missing: list[str]


def get_required_artifacts(gate_type: str, tier: str) -> list[str]:
    """
    Get required artifact types for a gate+tier combination.

    Args:
        gate_type: Gate code (e.g. "G2", "G3")
        tier: Tier name (e.g. "ENTERPRISE", "LITE")

    Returns:
        List of required artifact type identifiers. Empty list if
        gate or tier not in matrix (advisory/no requirements).
    """
    gate_map = GATE_ARTIFACT_MATRIX.get(gate_type, {})
    return gate_map.get(tier.upper(), [])


def check_artifact_completeness(
    gate_type: str,
    tier: str,
    submitted_types: list[str],
) -> ArtifactCheckResult:
    """
    Check whether submitted artifacts satisfy the matrix requirements.

    Args:
        gate_type: Gate code (e.g. "G2")
        tier: Tier name (e.g. "ENTERPRISE")
        submitted_types: List of artifact types actually submitted

    Returns:
        ArtifactCheckResult with pass/fail and missing artifact list
    """
    required = get_required_artifacts(gate_type, tier)
    submitted_set = {t.upper() for t in submitted_types}
    missing = [r for r in required if r not in submitted_set]

    return ArtifactCheckResult(
        passed=len(missing) == 0,
        gate_type=gate_type,
        tier=tier,
        required=required,
        submitted=list(submitted_set),
        missing=missing,
    )
