# =========================================================================
# Design Gate Policies (G1, G2)
# SDLC Orchestrator - Sprint 120 Track B
#
# Framework: SDLC 5.3.0 Quality Assurance System
# Purpose: Validate design and ship-ready stage exit criteria
#
# Gates:
# - G1: Design Ready (FRD, Data Model, API Spec, Architecture)
# - G2: Ship Ready (Architecture Review, ADR Linkage, Security)
#
# Zero Mock Policy: Real OPA evaluation rules
# =========================================================================

package gates.design

import future.keywords.if
import future.keywords.in

# ============================================================================
# G1 - Design Ready Policies
# ============================================================================

# Check if Functional Requirements Document is complete
frd_complete := result if {
    some criterion in input.exit_criteria
    criterion.id == "frd_complete"
    criterion.met == true
    result := {
        "allowed": true,
        "reason": "Functional Requirements Document is complete"
    }
} else := {
    "allowed": false,
    "reason": "FRD must be complete with all functional requirements documented"
}

# Check if data model is validated
data_model_validated := result if {
    some criterion in input.exit_criteria
    criterion.id == "data_model"
    criterion.met == true
    result := {
        "allowed": true,
        "reason": "Data model has been designed and validated"
    }
} else := {
    "allowed": false,
    "reason": "Data model must be validated before implementation"
}

# Check if API specification is reviewed
api_specification_reviewed := result if {
    some criterion in input.exit_criteria
    criterion.id == "api_spec"
    criterion.met == true
    result := {
        "allowed": true,
        "reason": "API specification has been reviewed"
    }
} else := {
    "allowed": false,
    "reason": "API specification must be reviewed and approved"
}

# Check if architecture is documented
architecture_documented := result if {
    some criterion in input.exit_criteria
    criterion.id == "architecture"
    criterion.met == true
    result := {
        "allowed": true,
        "reason": "System architecture is documented"
    }
} else := {
    "allowed": false,
    "reason": "System architecture must be documented in ADRs"
}

# Combined G1 check
g1_design_ready := result if {
    frd_result := frd_complete
    data_result := data_model_validated
    api_result := api_specification_reviewed
    arch_result := architecture_documented

    all_passed := frd_result.allowed == true
    all_passed := data_result.allowed == true
    all_passed := api_result.allowed == true
    all_passed := arch_result.allowed == true

    result := {
        "allowed": all_passed,
        "gate": "G1",
        "stage": "WHAT",
        "checks": {
            "frd": frd_result,
            "data_model": data_result,
            "api_spec": api_result,
            "architecture": arch_result
        }
    }
}

# ============================================================================
# G2 - Ship Ready Policies
# ============================================================================

# Check if architecture review is passed
architecture_review_passed := result if {
    some criterion in input.exit_criteria
    criterion.id == "arch_review"
    criterion.met == true
    result := {
        "allowed": true,
        "reason": "Architecture review passed with CTO approval"
    }
} else := {
    "allowed": false,
    "reason": "Architecture must be reviewed and approved by CTO"
}

# Check if ADR linkage is verified
adr_linkage_verified := result if {
    some criterion in input.exit_criteria
    criterion.id == "adr_linkage"
    criterion.met == true
    result := {
        "allowed": true,
        "reason": "All modules are linked to ADRs"
    }
} else := {
    "allowed": false,
    "reason": "All code modules must be linked to ADRs (orphan code = rejected code)"
}

# Check if security baseline is met
security_baseline_met := result if {
    some criterion in input.exit_criteria
    criterion.id == "security"
    criterion.met == true
    result := {
        "allowed": true,
        "reason": "Security baseline requirements are met"
    }
} else := {
    "allowed": false,
    "reason": "Security baseline (OWASP ASVS L2) must be met before shipping"
}

# Combined G2 check
g2_ship_ready := result if {
    arch_result := architecture_review_passed
    adr_result := adr_linkage_verified
    security_result := security_baseline_met

    all_passed := arch_result.allowed == true
    all_passed := adr_result.allowed == true
    all_passed := security_result.allowed == true

    result := {
        "allowed": all_passed,
        "gate": "G2",
        "stage": "HOW",
        "checks": {
            "architecture_review": arch_result,
            "adr_linkage": adr_result,
            "security_baseline": security_result
        }
    }
}

# ============================================================================
# Context Authority Integration
# ============================================================================

# Check ADR linkage via Context Authority V2
ca_adr_linkage_check := result if {
    input.context.adr_count > 0
    input.context.linked_adrs != null
    count(input.context.linked_adrs) > 0
    result := {
        "allowed": true,
        "reason": sprintf("Linked to %d ADRs", [count(input.context.linked_adrs)])
    }
} else := {
    "allowed": false,
    "reason": "No ADR linkage found - orphan code detected"
}

# Check vibecoding index zone
vibecoding_zone_acceptable := result if {
    input.context.vibecoding_index != null
    index := input.context.vibecoding_index
    index <= 60  # GREEN or YELLOW zone
    result := {
        "allowed": true,
        "reason": sprintf("Vibecoding index %v is acceptable", [index])
    }
} else := result if {
    input.context.vibecoding_index != null
    index := input.context.vibecoding_index
    index > 60
    result := {
        "allowed": false,
        "reason": sprintf("Vibecoding index %v is too high (max 60)", [index])
    }
} else := {
    "allowed": true,
    "reason": "Vibecoding index not available - skipping check"
}

# ============================================================================
# Helper Rules
# ============================================================================

# Design stage completion
design_criteria_met := count([c | c := input.exit_criteria[_]; c.met == true])
design_criteria_total := count(input.exit_criteria)

design_completion_pct := (design_criteria_met / design_criteria_total) * 100 if {
    design_criteria_total > 0
} else := 0
