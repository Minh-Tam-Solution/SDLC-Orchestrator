# =========================================================================
# Tier-Specific Artifact Requirements Gate Policy
# SDLC Orchestrator - Sprint 223
#
# Framework: SDLC 6.1.1 Tier-Specific Stage Requirements
# Purpose: Enforce per-gate per-tier artifact type requirements
#
# Gates Affected: G0.1, G0.2, G1, G2, G3, G4
# Integration: Called during gate evaluation Phase 1.5 (after Prerequisites)
#
# Cross-project review finding: EndiorBot Sprint 80 gap G2
# CTO directive: Separate matrix from tier_policies.py
# =========================================================================

package gates.tier_artifacts

import future.keywords.if
import future.keywords.in

# ============================================================================
# Gate Artifact Matrix (mirrors gate_artifact_matrix.py)
# ============================================================================

artifact_matrix := {
    "G0.1": {"LITE": [], "STANDARD": ["BRD"], "PROFESSIONAL": ["BRD"], "ENTERPRISE": ["BRD"]},
    "G0.2": {"LITE": [], "STANDARD": ["BRD"], "PROFESSIONAL": ["BRD", "PRD"], "ENTERPRISE": ["BRD", "PRD"]},
    "G1": {"LITE": [], "STANDARD": ["BRD"], "PROFESSIONAL": ["BRD", "PRD"], "ENTERPRISE": ["BRD", "PRD", "ADR"]},
    "G2": {"LITE": [], "STANDARD": ["ADR"], "PROFESSIONAL": ["ADR", "TEST_PLAN", "SECURITY_BASELINE"], "ENTERPRISE": ["ADR", "THREAT_MODEL", "SECURITY_BASELINE", "TEST_PLAN"]},
    "G3": {"LITE": [], "STANDARD": ["TEST_RESULTS", "CODE_REVIEW"], "PROFESSIONAL": ["TEST_RESULTS", "CODE_REVIEW", "SAST_REPORT"], "ENTERPRISE": ["TEST_RESULTS", "CODE_REVIEW", "SAST_REPORT", "DEPLOYMENT_PROOF", "COMPLIANCE_REPORT"]},
    "G4": {"LITE": [], "STANDARD": ["TEST_RESULTS", "DEPLOYMENT_PROOF"], "PROFESSIONAL": ["TEST_RESULTS", "DEPLOYMENT_PROOF", "RUNBOOK"], "ENTERPRISE": ["TEST_RESULTS", "DEPLOYMENT_PROOF", "RUNBOOK", "USER_GUIDE", "COMPLIANCE_REPORT"]},
}

# ============================================================================
# Deny Rules
# ============================================================================

# Get required artifacts for the gate+tier combination
required_artifacts := artifact_matrix[input.gate_code][input.tier] if {
    artifact_matrix[input.gate_code][input.tier]
} else := []

# Compute missing artifacts
missing_artifacts[artifact] if {
    some artifact in required_artifacts
    not artifact in input.submitted_evidence_types
}

# Deny if any required artifacts are missing
deny[msg] if {
    count(missing_artifacts) > 0

    msg := sprintf("%s BLOCKED for %s tier: Missing required artifacts: %v. Submit these before gate evaluation.", [
        input.gate_code,
        input.tier,
        missing_artifacts,
    ])
}

# ============================================================================
# Allow Rules
# ============================================================================

allow if {
    count(missing_artifacts) == 0
}

# ============================================================================
# Metadata
# ============================================================================

metadata := {
    "policy_name": "Tier-Specific Artifact Requirements",
    "version": "1.0.0",
    "sprint": "Sprint 223",
    "gates": ["G0.1", "G0.2", "G1", "G2", "G3", "G4"],
    "enforcement": "hard",
    "source": "EndiorBot Sprint 80 cross-project review"
}
