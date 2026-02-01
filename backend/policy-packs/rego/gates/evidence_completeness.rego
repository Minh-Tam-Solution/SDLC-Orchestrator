# =========================================================================
# Evidence Completeness Gate Policies
# SDLC Orchestrator - Sprint 133
#
# Framework: SDLC 6.0.0 Evidence-Based Validation (SPEC-0016)
# Purpose: Enforce implementation evidence requirements at quality gates
#
# Gates Affected:
# - G3: Ship Ready (100% evidence required)
# - G4: Production Ready (100% evidence + tests required)
# - G5: Market Ready (evidence + documentation required)
#
# Integration: Calls Evidence Validator API to check spec-to-code alignment
# Zero Mock Policy: Real HTTP calls to backend evidence status endpoint
# =========================================================================

package gates.evidence

import future.keywords.if
import future.keywords.in

# ============================================================================
# Configuration
# ============================================================================

# Evidence API endpoint (internal service-to-service call)
evidence_api_base_url := "http://backend:8000/api/v1"

# Severity thresholds
severity_thresholds := {
    "G3": {"max_errors": 0, "max_warnings": 5},   # Ship Ready: strict
    "G4": {"max_errors": 0, "max_warnings": 0},   # Production Ready: zero tolerance
    "G5": {"max_errors": 0, "max_warnings": 0}    # Market Ready: zero tolerance
}

# ============================================================================
# G3 - Ship Ready: Evidence Completeness Required
# ============================================================================

# Gate G3 requires 100% backend + frontend implementation evidence
deny[msg] if {
    input.gate_code == "G3"

    # Call evidence validator API
    evidence_status := get_evidence_status(input.project_id)

    # Check if evidence validation failed
    evidence_status.status != "complete"

    # Count total gaps
    total_gaps := sum([
        count(evidence_status.gaps.backend),
        count(evidence_status.gaps.frontend),
        count(evidence_status.gaps.extension),
        count(evidence_status.gaps.cli)
    ])

    total_gaps > 0

    msg := sprintf("G3 BLOCKED: Implementation evidence incomplete. Total gaps: %d. Backend: %d, Frontend: %d, Extension: %d, CLI: %d. Fix gaps before ship.", [
        total_gaps,
        count(evidence_status.gaps.backend),
        count(evidence_status.gaps.frontend),
        count(evidence_status.gaps.extension),
        count(evidence_status.gaps.cli)
    ])
}

# G3 requires frontend components for user-facing features
deny[msg] if {
    input.gate_code == "G3"

    evidence_status := get_evidence_status(input.project_id)

    # Check for missing frontend components
    count(evidence_status.gaps.frontend) > 0

    frontend_gaps := evidence_status.gaps.frontend

    msg := sprintf("G3 BLOCKED: Frontend components missing (%d files). Missing: %v. Implement UI before ship.", [
        count(frontend_gaps),
        frontend_gaps
    ])
}

# G3 requires backend tests (mandatory per SPEC-0016)
deny[msg] if {
    input.gate_code == "G3"

    evidence_status := get_evidence_status(input.project_id)

    # Check for missing backend tests
    backend_test_missing := [gap |
        gap := evidence_status.gaps.backend[_]
        contains(gap, "tests missing")
    ]

    count(backend_test_missing) > 0

    msg := sprintf("G3 BLOCKED: Backend tests missing (MANDATORY). Missing: %v. Add tests with 95%+ coverage.", [
        backend_test_missing
    ])
}

# ============================================================================
# G4 - Production Ready: Zero Tolerance for Evidence Gaps
# ============================================================================

# G4 requires 100% evidence with zero gaps
deny[msg] if {
    input.gate_code == "G4"

    evidence_status := get_evidence_status(input.project_id)

    # Zero tolerance: ANY gap blocks G4
    total_gaps := sum([
        count(evidence_status.gaps.backend),
        count(evidence_status.gaps.frontend),
        count(evidence_status.gaps.extension),
        count(evidence_status.gaps.cli)
    ])

    total_gaps > 0

    msg := sprintf("G4 BLOCKED: Production requires 100%% evidence completeness. Current gaps: %d. All components must be implemented and tested.", [
        total_gaps
    ])
}

# G4 requires all tests (backend, frontend, extension, CLI)
deny[msg] if {
    input.gate_code == "G4"

    evidence_status := get_evidence_status(input.project_id)

    # Check for any missing tests
    all_test_gaps := array.concat(
        evidence_status.gaps.backend,
        array.concat(
            evidence_status.gaps.frontend,
            array.concat(
                evidence_status.gaps.extension,
                evidence_status.gaps.cli
            )
        )
    )

    test_gaps := [gap |
        gap := all_test_gaps[_]
        contains(gap, "test")
    ]

    count(test_gaps) > 0

    msg := sprintf("G4 BLOCKED: Production requires comprehensive test coverage. Missing tests: %v. Add tests before production deployment.", [
        test_gaps
    ])
}

# ============================================================================
# G5 - Market Ready: Evidence + Documentation Required
# ============================================================================

# G5 requires complete evidence AND documentation
deny[msg] if {
    input.gate_code == "G5"

    evidence_status := get_evidence_status(input.project_id)

    # Check for missing documentation
    doc_missing := [gap |
        gap := evidence_status.gaps.backend[_]
        contains(gap, "documentation")
    ]

    count(doc_missing) > 0

    msg := sprintf("G5 BLOCKED: Market launch requires complete documentation. Missing: %v. Add user guides, API docs, and runbooks.", [
        doc_missing
    ])
}

# ============================================================================
# Helper Functions
# ============================================================================

# Get evidence status from backend API
get_evidence_status(project_id) := result if {
    # Construct API URL
    url := sprintf("%s/projects/%v/evidence/status", [evidence_api_base_url, project_id])

    # Make HTTP request (OPA builtin function)
    response := http.send({
        "method": "GET",
        "url": url,
        "headers": {
            "Content-Type": "application/json",
            "Authorization": sprintf("Bearer %s", [input.auth_token])
        },
        "raise_error": false,
        "force_json_decode": true,
        "timeout": "5s"
    })

    # Check response status
    response.status_code == 200

    result := response.body
} else := {
    # Fallback if API call fails
    "status": "unknown",
    "gaps": {
        "backend": ["Evidence API unavailable"],
        "frontend": [],
        "extension": [],
        "cli": []
    },
    "total_gaps": 1,
    "checked_at": "unknown",
    "error": "Failed to fetch evidence status"
}

# Check if evidence status is complete
evidence_complete(evidence_status) if {
    evidence_status.status == "complete"
    evidence_status.total_gaps == 0
}

# Calculate evidence completeness percentage
evidence_completeness_percentage(evidence_status) := percentage if {
    # Total possible files (rough estimate: 6 per interface)
    total_possible := 24  # 6 files × 4 interfaces (backend, frontend, extension, CLI)

    # Calculate actual gaps
    actual_gaps := evidence_status.total_gaps

    # Percentage = (total - gaps) / total * 100
    percentage := ((total_possible - actual_gaps) / total_possible) * 100
}

# ============================================================================
# Allow Rules (Evidence Complete)
# ============================================================================

# Allow G3 if evidence is complete
allow if {
    input.gate_code == "G3"
    evidence_status := get_evidence_status(input.project_id)
    evidence_complete(evidence_status)
}

# Allow G4 if evidence is complete with all tests
allow if {
    input.gate_code == "G4"
    evidence_status := get_evidence_status(input.project_id)
    evidence_complete(evidence_status)

    # Verify no test gaps
    all_gaps := array.concat(
        evidence_status.gaps.backend,
        array.concat(
            evidence_status.gaps.frontend,
            array.concat(
                evidence_status.gaps.extension,
                evidence_status.gaps.cli
            )
        )
    )

    test_gaps := [gap |
        gap := all_gaps[_]
        contains(gap, "test")
    ]

    count(test_gaps) == 0
}

# Allow G5 if evidence is complete with documentation
allow if {
    input.gate_code == "G5"
    evidence_status := get_evidence_status(input.project_id)
    evidence_complete(evidence_status)
}

# ============================================================================
# Metadata (for OPA introspection)
# ============================================================================

metadata := {
    "policy_name": "Evidence Completeness Gate Policies",
    "version": "1.0.0",
    "sprint": "Sprint 133",
    "spec": "SPEC-0016",
    "gates": ["G3", "G4", "G5"],
    "enforcement": "strict",
    "api_dependency": "GET /api/v1/projects/{id}/evidence/status"
}
