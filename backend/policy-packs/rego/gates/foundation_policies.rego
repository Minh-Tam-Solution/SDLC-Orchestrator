# =========================================================================
# Foundation Gate Policies (G0.1, G0.2)
# SDLC Orchestrator - Sprint 120 Track B
#
# Framework: SDLC 5.3.0 Quality Assurance System
# Purpose: Validate foundation stage exit criteria
#
# Gates:
# - G0.1: Foundation Ready (Problem definition, stakeholders, success metrics)
# - G0.2: Solution Diversity (Alternatives evaluated, solution selected)
#
# Zero Mock Policy: Real OPA evaluation rules
# =========================================================================

package gates.foundation

import future.keywords.if
import future.keywords.in

# ============================================================================
# G0.1 - Foundation Ready Policies
# ============================================================================

# Check if problem statement document exists and is complete
problem_statement_complete := result if {
    input.exit_criteria[_].id == "problem_statement"
    criterion := input.exit_criteria[_]
    criterion.met == true
    result := {
        "allowed": true,
        "reason": "Problem statement document is complete"
    }
} else := {
    "allowed": false,
    "reason": "Problem statement document is missing or incomplete"
}

# Check if stakeholders are identified
stakeholder_identified := result if {
    input.exit_criteria[_].id == "stakeholders"
    criterion := input.exit_criteria[_]
    criterion.met == true
    result := {
        "allowed": true,
        "reason": "Stakeholders are identified and documented"
    }
} else := {
    "allowed": false,
    "reason": "Stakeholders must be identified before proceeding"
}

# Check if success metrics are defined
success_metrics_defined := result if {
    input.exit_criteria[_].id == "success_metrics"
    criterion := input.exit_criteria[_]
    criterion.met == true
    result := {
        "allowed": true,
        "reason": "Success metrics are defined"
    }
} else := {
    "allowed": false,
    "reason": "Success metrics must be defined for the project"
}

# Combined G0.1 check
g01_foundation_ready := result if {
    problem_result := problem_statement_complete
    stakeholder_result := stakeholder_identified
    metrics_result := success_metrics_defined

    all_passed := problem_result.allowed == true
    all_passed_2 := stakeholder_result.allowed == true
    all_passed_3 := metrics_result.allowed == true

    result := {
        "allowed": all_passed,
        "checks": {
            "problem_statement": problem_result,
            "stakeholders": stakeholder_result,
            "success_metrics": metrics_result
        }
    }
}

# ============================================================================
# G0.2 - Solution Diversity Policies
# ============================================================================

# Check if solution alternatives were evaluated
solution_alternatives_evaluated := result if {
    input.exit_criteria[_].id == "alternatives"
    criterion := input.exit_criteria[_]
    criterion.met == true
    result := {
        "allowed": true,
        "reason": "Solution alternatives have been evaluated"
    }
} else := {
    "allowed": false,
    "reason": "At least 3 solution alternatives must be evaluated"
}

# Check if final solution is selected
solution_selected := result if {
    input.exit_criteria[_].id == "solution_selection"
    criterion := input.exit_criteria[_]
    criterion.met == true
    result := {
        "allowed": true,
        "reason": "Solution has been selected with justification"
    }
} else := {
    "allowed": false,
    "reason": "A solution must be selected with documented justification"
}

# Check if risk assessment is complete
risk_assessment_complete := result if {
    input.exit_criteria[_].id == "risk_assessment"
    criterion := input.exit_criteria[_]
    criterion.met == true
    result := {
        "allowed": true,
        "reason": "Risk assessment is complete"
    }
} else := {
    "allowed": false,
    "reason": "Risk assessment must be completed before proceeding"
}

# Combined G0.2 check
g02_solution_diversity := result if {
    alternatives_result := solution_alternatives_evaluated
    selection_result := solution_selected
    risk_result := risk_assessment_complete

    all_passed := alternatives_result.allowed == true
    all_passed_2 := selection_result.allowed == true
    all_passed_3 := risk_result.allowed == true

    result := {
        "allowed": all_passed,
        "checks": {
            "alternatives": alternatives_result,
            "selection": selection_result,
            "risk_assessment": risk_result
        }
    }
}

# ============================================================================
# Helper Rules
# ============================================================================

# Count met criteria
criteria_met_count := count([c | c := input.exit_criteria[_]; c.met == true])

# Total criteria count
criteria_total := count(input.exit_criteria)

# Foundation stage completion percentage
foundation_completion_pct := (criteria_met_count / criteria_total) * 100 if {
    criteria_total > 0
} else := 0
