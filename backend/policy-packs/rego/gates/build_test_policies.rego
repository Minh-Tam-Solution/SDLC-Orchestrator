# =========================================================================
# Build & Test Gate Policies (G3, G4)
# SDLC Orchestrator - Sprint 120 Track B
#
# Framework: SDLC 5.3.0 Quality Assurance System
# Purpose: Validate build and test stage exit criteria
#
# Gates:
# - G3: Build Complete (Code, Tests, Review, Security)
# - G4: Test Complete (Integration, E2E, Performance, Regression)
#
# Zero Mock Policy: Real OPA evaluation rules
# =========================================================================

package gates.build

import future.keywords.if
import future.keywords.in

# ============================================================================
# G3 - Build Complete Policies
# ============================================================================

# Check if code is complete
code_complete := result if {
    some criterion in input.exit_criteria
    criterion.id == "code_complete"
    criterion.met == true
    result := {
        "allowed": true,
        "reason": "All code implementation is complete"
    }
} else := {
    "allowed": false,
    "reason": "Code implementation must be complete before proceeding"
}

# Check if unit tests passed
unit_tests_passed := result if {
    some criterion in input.exit_criteria
    criterion.id == "unit_tests"
    criterion.met == true
    result := {
        "allowed": true,
        "reason": "Unit tests passed with required coverage"
    }
} else := {
    "allowed": false,
    "reason": "Unit tests must pass with >= 80% coverage"
}

# Check if code review is approved
code_review_approved := result if {
    some criterion in input.exit_criteria
    criterion.id == "code_review"
    criterion.met == true
    result := {
        "allowed": true,
        "reason": "Code review approved by 2+ reviewers"
    }
} else := {
    "allowed": false,
    "reason": "Code review must be approved by at least 2 reviewers"
}

# Check if security scan is clean
security_scan_clean := result if {
    some criterion in input.exit_criteria
    criterion.id == "security_scan"
    criterion.met == true
    result := {
        "allowed": true,
        "reason": "Security scan passed (no critical/high vulnerabilities)"
    }
} else := {
    "allowed": false,
    "reason": "Security scan must pass - no critical or high vulnerabilities allowed"
}

# Combined G3 check
g3_build_complete := result if {
    code_result := code_complete
    unit_result := unit_tests_passed
    review_result := code_review_approved
    security_result := security_scan_clean

    all_passed := code_result.allowed == true
    all_passed := unit_result.allowed == true
    all_passed := review_result.allowed == true
    all_passed := security_result.allowed == true

    result := {
        "allowed": all_passed,
        "gate": "G3",
        "stage": "BUILD",
        "checks": {
            "code": code_result,
            "unit_tests": unit_result,
            "code_review": review_result,
            "security": security_result
        }
    }
}

# ============================================================================
# G4 - Test Complete Policies
# ============================================================================

# Check if integration tests passed
integration_tests_passed := result if {
    some criterion in input.exit_criteria
    criterion.id == "integration_tests"
    criterion.met == true
    result := {
        "allowed": true,
        "reason": "Integration tests passed"
    }
} else := {
    "allowed": false,
    "reason": "Integration tests must pass before deployment"
}

# Check if E2E tests passed
e2e_tests_passed := result if {
    some criterion in input.exit_criteria
    criterion.id == "e2e_tests"
    criterion.met == true
    result := {
        "allowed": true,
        "reason": "End-to-end tests passed"
    }
} else := {
    "allowed": false,
    "reason": "E2E tests for critical user journeys must pass"
}

# Check if performance baseline is met
performance_baseline_met := result if {
    some criterion in input.exit_criteria
    criterion.id == "performance"
    criterion.met == true
    result := {
        "allowed": true,
        "reason": "Performance baseline achieved (p95 < 100ms)"
    }
} else := {
    "allowed": false,
    "reason": "Performance baseline must be met (p95 < 100ms API latency)"
}

# Check if regression is verified
regression_verified := result if {
    some criterion in input.exit_criteria
    criterion.id == "regression"
    criterion.met == true
    result := {
        "allowed": true,
        "reason": "No regression detected in existing features"
    }
} else := {
    "allowed": false,
    "reason": "Regression tests must verify no degradation in existing features"
}

# Combined G4 check
g4_test_complete := result if {
    integration_result := integration_tests_passed
    e2e_result := e2e_tests_passed
    perf_result := performance_baseline_met
    regression_result := regression_verified

    all_passed := integration_result.allowed == true
    all_passed := e2e_result.allowed == true
    all_passed := perf_result.allowed == true
    all_passed := regression_result.allowed == true

    result := {
        "allowed": all_passed,
        "gate": "G4",
        "stage": "TEST",
        "checks": {
            "integration": integration_result,
            "e2e": e2e_result,
            "performance": perf_result,
            "regression": regression_result
        }
    }
}

# ============================================================================
# Coverage Rules
# ============================================================================

# Check test coverage percentage
test_coverage_sufficient if {
    input.submission.coverage >= 80
}

test_coverage_result := result if {
    input.submission.coverage != null
    test_coverage_sufficient
    result := {
        "allowed": true,
        "reason": sprintf("Test coverage %v%% meets minimum 80%%", [input.submission.coverage])
    }
} else := result if {
    input.submission.coverage != null
    not test_coverage_sufficient
    result := {
        "allowed": false,
        "reason": sprintf("Test coverage %v%% below minimum 80%%", [input.submission.coverage])
    }
} else := {
    "allowed": true,
    "reason": "Coverage data not provided - skipping check"
}

# ============================================================================
# Security Integration
# ============================================================================

# SAST scan result check
sast_scan_passed := result if {
    input.submission.sast_results != null
    input.submission.sast_results.critical == 0
    input.submission.sast_results.high == 0
    result := {
        "allowed": true,
        "reason": "SAST scan passed - no critical or high vulnerabilities"
    }
} else := result if {
    input.submission.sast_results != null
    result := {
        "allowed": false,
        "reason": sprintf(
            "SAST found %d critical, %d high vulnerabilities",
            [input.submission.sast_results.critical, input.submission.sast_results.high]
        )
    }
} else := {
    "allowed": true,
    "reason": "SAST results not provided - skipping check"
}

# ============================================================================
# Helper Rules
# ============================================================================

build_criteria_met := count([c | c := input.exit_criteria[_]; c.met == true])
build_criteria_total := count(input.exit_criteria)

build_completion_pct := (build_criteria_met / build_criteria_total) * 100 if {
    build_criteria_total > 0
} else := 0
