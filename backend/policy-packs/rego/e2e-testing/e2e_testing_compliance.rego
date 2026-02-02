# E2E Testing Compliance Policy
# SDLC Framework 6.0.2 - RFC-SDLC-602
#
# Purpose: Enforce E2E API testing requirements for stage transitions
#
# Rules:
# 1. E2E test report required for Stage 05 → 06 transition
# 2. Minimum pass rate threshold (default: 80%)
# 3. API documentation reference must exist

package sdlc.e2e_testing

import future.keywords.if
import future.keywords.in
import future.keywords.contains

# Default configuration
default min_pass_rate := 80
default require_security_testing := false

# Allow stage transition if E2E requirements are met
default allow_stage_transition := false

allow_stage_transition if {
    input.from_stage == "05-TESTING"
    input.to_stage == "06-DEPLOY"
    has_e2e_report
    e2e_pass_rate >= min_pass_rate
    has_api_documentation
}

# Also allow if transitioning from other stages (E2E not required)
allow_stage_transition if {
    input.from_stage != "05-TESTING"
}

# Check if E2E testing report exists in evidence
has_e2e_report if {
    some report in input.evidence
    report.artifact_type == "E2E_TESTING_REPORT"
}

# Check if API documentation reference exists
has_api_documentation if {
    some doc in input.evidence
    doc.artifact_type == "API_DOCUMENTATION_REFERENCE"
}

# Get E2E pass rate from evidence metadata
e2e_pass_rate := rate if {
    some report in input.evidence
    report.artifact_type == "E2E_TESTING_REPORT"
    rate := report.metadata.pass_rate
} else := 0

# Get total endpoints tested
total_endpoints := count if {
    some report in input.evidence
    report.artifact_type == "E2E_TESTING_REPORT"
    count := report.metadata.total_endpoints
} else := 0

# Get failed endpoints count
failed_endpoints := count if {
    some report in input.evidence
    report.artifact_type == "E2E_TESTING_REPORT"
    count := report.metadata.failed_endpoints
} else := 0

# Violations for non-compliance
violations contains msg if {
    input.from_stage == "05-TESTING"
    input.to_stage == "06-DEPLOY"
    not has_e2e_report
    msg := "E2E_REPORT_MISSING: E2E API test report required for Stage 05 → 06 transition"
}

violations contains msg if {
    input.from_stage == "05-TESTING"
    input.to_stage == "06-DEPLOY"
    has_e2e_report
    e2e_pass_rate < min_pass_rate
    msg := sprintf("E2E_PASS_RATE_LOW: E2E pass rate %.1f%% is below minimum %.0f%%", [e2e_pass_rate, min_pass_rate])
}

violations contains msg if {
    input.from_stage == "05-TESTING"
    input.to_stage == "06-DEPLOY"
    not has_api_documentation
    msg := "API_DOCS_MISSING: API documentation reference required for Stage 05 → 06 transition"
}

# Optional: Security testing requirement for Enterprise tier
violations contains msg if {
    input.from_stage == "05-TESTING"
    input.to_stage == "06-DEPLOY"
    require_security_testing
    not has_security_testing
    msg := "SECURITY_TESTING_MISSING: Security testing results required (Enterprise tier)"
}

has_security_testing if {
    some result in input.evidence
    result.artifact_type == "SECURITY_TESTING_RESULTS"
}

# Summary for reporting
summary := {
    "has_e2e_report": has_e2e_report,
    "has_api_documentation": has_api_documentation,
    "has_security_testing": has_security_testing,
    "e2e_pass_rate": e2e_pass_rate,
    "total_endpoints": total_endpoints,
    "failed_endpoints": failed_endpoints,
    "min_pass_rate_threshold": min_pass_rate,
    "violations": violations,
    "allow_transition": allow_stage_transition,
}
