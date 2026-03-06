# =========================================================================
# Document Content Quality Gate Policy — PRIMARY ENFORCEMENT
# SDLC Orchestrator - Sprint 223
#
# Framework: SDLC 6.1.1 Evidence-Based Validation
# Purpose: Validate document content quality (not just presence)
#
# CTO Revision 3: OPA-first pattern (Sprint 156 NISTGovernService).
# This policy is the single source of truth for content quality.
# content_validator.py is the in-process fallback only.
#
# Integration: Called via content validation API endpoint
# Cross-project review finding: EndiorBot Sprint 80 gap G3
# =========================================================================

package gates.content_quality

import future.keywords.if
import future.keywords.in

# ============================================================================
# Configuration: Per-document-type required sections
# ============================================================================

# Section keywords to search for (case-insensitive matching done by caller)
required_sections := {
    "ADR": ["problem", "decision", "consequences"],
    "TEST_PLAN": ["test cases", "coverage", "scope"],
    "THREAT_MODEL": ["threats", "mitigations", "risk"],
    "SECURITY_BASELINE": ["controls", "compliance", "assessment"],
    "BRD": ["problem", "solution", "stakeholders"],
    "PRD": ["requirements", "acceptance criteria", "user stories"],
    "RUNBOOK": ["steps", "rollback", "monitoring"],
}

# Minimum word count per section to avoid "heading-only" stubs
min_section_words := 20

# Placeholder patterns that indicate stub content
# NOTE: Mirrored in app/utils/placeholder_detector.py (OPA cannot import Python).
# Update both files when adding/removing patterns.
placeholder_patterns := [
    "\\[.*TODO.*\\]",
    "\\[.*TBD.*\\]",
    "\\[.*please.*\\]",
    "\\[.*implement.*\\]",
    "\\[Auto-generation.*\\]",
    "\\[.*fill in.*\\]",
    "\\[.*placeholder.*\\]",
]

# ============================================================================
# Content Quality API Integration
# ============================================================================

content_quality_api := "http://backend:8000/api/v1"

# Call content validation API endpoint
get_content_quality(evidence_id) := result if {
    url := sprintf("%s/evidence/%s/validate-content", [content_quality_api, evidence_id])
    response := http.send({
        "method": "POST",
        "url": url,
        "headers": {
            "Content-Type": "application/json",
            "Authorization": sprintf("Bearer %s", [input.auth_token]),
        },
        "body": {
            "document_type": input.document_type,
            "content": input.content,
        },
        "raise_error": false,
        "force_json_decode": true,
        "timeout": "5s",
    })

    response.status_code == 200
    result := response.body
} else := {
    "score": 0,
    "missing_sections": [],
    "placeholder_warnings": [],
    "word_counts": {},
    "error": "Content quality API unavailable",
}

# ============================================================================
# Inline Quality Checks (no API dependency)
# ============================================================================

# Get expected sections for the document type
expected_sections := required_sections[input.document_type] if {
    required_sections[input.document_type]
} else := []

# Check which expected sections are present in the content
# input.found_sections: list of section headings found by the caller
missing_sections[section] if {
    some section in expected_sections
    not section_found(section)
}

section_found(section) if {
    some found in input.found_sections
    lower(found) == lower(section)
}

# Check for placeholder content
has_placeholders if {
    input.placeholder_count > 0
}

# Check for thin sections (below word count minimum)
thin_sections[section] if {
    some section, word_count in input.section_word_counts
    word_count < min_section_words
}

# ============================================================================
# Deny Rules
# ============================================================================

# Deny if required sections are missing
deny[msg] if {
    count(missing_sections) > 0

    msg := sprintf("Content quality FAILED for %s: Missing required sections: %v. Document must contain these sections with meaningful content.", [
        input.document_type,
        missing_sections,
    ])
}

# Deny if placeholders detected
deny[msg] if {
    has_placeholders

    msg := sprintf("Content quality WARNING for %s: %d placeholder(s) detected (e.g. [TODO], [TBD]). Replace placeholders with actual content before gate submission.", [
        input.document_type,
        input.placeholder_count,
    ])
}

# Deny if sections have insufficient content
deny[msg] if {
    count(thin_sections) > 0

    msg := sprintf("Content quality WARNING for %s: Thin sections (<%d words): %v. Add substantive content to these sections.", [
        input.document_type,
        min_section_words,
        thin_sections,
    ])
}

# ============================================================================
# Allow Rules
# ============================================================================

allow if {
    count(missing_sections) == 0
    not has_placeholders
    count(thin_sections) == 0
}

# ============================================================================
# Scoring
# ============================================================================

# Compute content quality score (0.0 - 1.0)
content_score := score if {
    total_expected := count(expected_sections)
    total_expected > 0
    found_count := total_expected - count(missing_sections)
    section_ratio := found_count / total_expected

    placeholder_penalty := min([input.placeholder_count * 0.1, 0.5])
    thin_penalty := min([count(thin_sections) * 0.05, 0.3])

    raw_score := section_ratio - placeholder_penalty - thin_penalty
    score := max([raw_score, 0.0])
} else := 1.0

# ============================================================================
# Metadata
# ============================================================================

metadata := {
    "policy_name": "Document Content Quality",
    "version": "1.0.0",
    "sprint": "Sprint 223",
    "enforcement": "hard",
    "pattern": "OPA-first (CTO Revision 3)",
    "fallback": "content_validator.py (in-process)",
    "source": "EndiorBot Sprint 80 cross-project review",
}
