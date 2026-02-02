# Stage Cross-Reference Validation Policy
# SDLC Framework 6.0.2 - RFC-SDLC-602
#
# Purpose: Enforce bidirectional cross-reference between Stage 03 and Stage 05
#
# Rules:
# 1. Stage 03 API docs must link to Stage 05 test reports
# 2. Stage 05 test reports must link to Stage 03 API docs
# 3. OpenAPI spec must exist in Stage 03 (SSOT)
# 4. No duplicate openapi.json in Stage 05

package sdlc.cross_reference

import future.keywords.if
import future.keywords.in
import future.keywords.contains

# Allow cross-reference validation to pass
default cross_reference_valid := false

cross_reference_valid if {
    has_stage_03_link
    has_stage_05_link
    ssot_compliance
}

# Check Stage 03 → Stage 05 links exist
has_stage_03_link if {
    some ref in input.cross_references
    ref.source_stage == "03"
    ref.target_stage == "05"
    ref.link_type == "api_to_test_report"
}

# Check Stage 05 → Stage 03 links exist
has_stage_05_link if {
    some ref in input.cross_references
    ref.source_stage == "05"
    ref.target_stage == "03"
    ref.link_type == "test_report_to_api"
}

# Check SSOT compliance (openapi.json in Stage 03 only)
default ssot_compliance := true

ssot_compliance := false if {
    has_duplicate_openapi
}

# Check for duplicate openapi.json files
has_duplicate_openapi if {
    count(openapi_locations) > 1
}

# Collect openapi.json locations
openapi_locations := locations if {
    locations := {loc |
        some file in input.files
        endswith(file.path, "openapi.json")
        not is_symlink(file)
        loc := file.path
    }
}

# Check if file is a symlink
is_symlink(file) if {
    file.type == "symlink"
}

# Violations for non-compliance
violations contains msg if {
    not has_stage_03_link
    msg := "CROSS_REF_03_TO_05_MISSING: Stage 03 API documentation must link to Stage 05 test reports"
}

violations contains msg if {
    not has_stage_05_link
    msg := "CROSS_REF_05_TO_03_MISSING: Stage 05 test reports must link to Stage 03 API documentation"
}

violations contains msg if {
    has_duplicate_openapi
    msg := sprintf("SSOT_VIOLATION: Multiple openapi.json files found. Expected 1 in Stage 03, found %d: %v", [count(openapi_locations), openapi_locations])
}

violations contains msg if {
    count(openapi_locations) == 0
    msg := "OPENAPI_MISSING: openapi.json not found in Stage 03 (docs/03-Integration-APIs/02-API-Specifications/)"
}

# Validate specific cross-reference links
link_validation := result if {
    result := {
        "stage_03_links": [ref |
            some ref in input.cross_references
            ref.source_stage == "03"
        ],
        "stage_05_links": [ref |
            some ref in input.cross_references
            ref.source_stage == "05"
        ],
        "all_links_valid": all_links_valid,
    }
}

# Check if all links are valid (not broken)
all_links_valid if {
    count(broken_links) == 0
}

broken_links := links if {
    links := {ref |
        some ref in input.cross_references
        ref.status == "broken"
    }
}

# Summary for reporting
summary := {
    "has_stage_03_to_05_link": has_stage_03_link,
    "has_stage_05_to_03_link": has_stage_05_link,
    "ssot_compliance": ssot_compliance,
    "openapi_locations": openapi_locations,
    "violations": violations,
    "cross_reference_valid": cross_reference_valid,
}

# Stage-specific requirements
stage_03_requirements := {
    "required_files": [
        "docs/03-Integration-APIs/02-API-Specifications/openapi.json",
        "docs/03-Integration-APIs/02-API-Specifications/COMPLETE-API-ENDPOINT-REFERENCE.md",
    ],
    "required_links": [
        "Link to Stage 05 E2E test reports",
        "Link to Stage 05 Security testing results",
    ],
}

stage_05_requirements := {
    "required_files": [
        "docs/05-Testing-Quality/03-E2E-Testing/reports/",
        "docs/05-Testing-Quality/03-E2E-Testing/README.md",
    ],
    "required_links": [
        "Link to Stage 03 API Reference",
        "Link to Stage 03 OpenAPI spec (via symlink or relative path)",
    ],
    "prohibited": [
        "Duplicate openapi.json (must be symlink only)",
    ],
}
