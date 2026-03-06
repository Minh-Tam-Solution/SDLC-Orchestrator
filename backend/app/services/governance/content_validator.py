"""
Content Validator — in-process fallback for document content quality.

Sprint 223: Cross-project review finding (EndiorBot Sprint 80 gap G3).

CTO Revision 3: This is the IN-PROCESS FALLBACK only.
Primary enforcement is content_quality.rego (OPA-first pattern).
This service fires ONLY when OPA is unreachable.

Follows Sprint 156 NISTGovernService pattern:
    OPA-first → in-process fallback → never duplicate logic.

Usage:
    from app.services.governance.content_validator import ContentValidator

    validator = ContentValidator()
    result = validator.validate("ADR", content_text)
    # ContentValidationResult(score=0.7, missing_sections=["Consequences"], ...)
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field

from app.utils.placeholder_detector import detect_placeholders, PlaceholderMatch

logger = logging.getLogger(__name__)


# ============================================================================
# Document Type Section Schemas
# ============================================================================

# Per-document-type required section headings (case-insensitive match)
SECTION_SCHEMAS: dict[str, list[str]] = {
    "ADR": ["problem", "decision", "consequences"],
    "TEST_PLAN": ["test cases", "coverage", "scope"],
    "THREAT_MODEL": ["threats", "mitigations", "risk"],
    "SECURITY_BASELINE": ["controls", "compliance", "assessment"],
    "BRD": ["problem", "solution", "stakeholders"],
    "PRD": ["requirements", "acceptance criteria", "user stories"],
    "RUNBOOK": ["steps", "rollback", "monitoring"],
    "DESIGN_DOCUMENT": ["overview", "architecture", "decisions"],
    "COMPLIANCE_REPORT": ["scope", "findings", "recommendations"],
}

# Minimum words per section to avoid stub/heading-only content
MIN_SECTION_WORDS = 20

# Heading patterns: ## Heading, ### Heading, # Heading, **Heading**
_HEADING_PATTERN = re.compile(
    r"^(?:#{1,6}\s+(.+)|(?:\*\*(.+)\*\*)\s*$)", re.MULTILINE
)


@dataclass
class SectionInfo:
    """Information about a detected document section."""
    heading: str
    word_count: int
    content: str


@dataclass
class ContentValidationResult:
    """Result of content quality validation."""
    score: float  # 0.0 - 1.0
    document_type: str
    passed: bool
    missing_sections: list[str]
    found_sections: list[str]
    section_word_counts: dict[str, int]
    placeholder_warnings: list[PlaceholderMatch]
    thin_sections: list[str]  # sections with < MIN_SECTION_WORDS
    total_word_count: int
    issues: list[str] = field(default_factory=list)


class ContentValidator:
    """
    In-process content quality validator.

    Fallback for when OPA is unreachable. Mirrors content_quality.rego logic.
    """

    def validate(
        self,
        document_type: str,
        content: str,
    ) -> ContentValidationResult:
        """
        Validate document content quality.

        Args:
            document_type: Canonical document type (e.g. "ADR", "TEST_PLAN")
            content: Full text content of the document

        Returns:
            ContentValidationResult with score, issues, and section analysis
        """
        doc_type_upper = document_type.upper()
        required_sections = SECTION_SCHEMAS.get(doc_type_upper, [])

        # Extract sections from content
        sections = self._extract_sections(content)
        found_headings = [s.heading.lower() for s in sections]

        # Check required sections
        missing = []
        found = []
        for req in required_sections:
            if self._section_found(req, found_headings):
                found.append(req)
            else:
                missing.append(req)

        # Word counts per section
        section_word_counts = {s.heading: s.word_count for s in sections}

        # Thin sections
        thin = [
            s.heading for s in sections
            if s.word_count < MIN_SECTION_WORDS
        ]

        # Placeholder detection
        placeholders = detect_placeholders(content)

        # Total word count
        total_words = len(content.split())

        # Compute score
        score = self._compute_score(
            required_sections, missing, placeholders, thin
        )

        # Build issues list
        issues: list[str] = []
        if missing:
            issues.append(
                f"Missing required sections for {doc_type_upper}: {missing}"
            )
        if placeholders:
            issues.append(
                f"{len(placeholders)} placeholder(s) detected "
                f"(e.g. {placeholders[0].text})"
            )
        if thin:
            issues.append(
                f"Thin sections (<{MIN_SECTION_WORDS} words): {thin}"
            )

        passed = len(missing) == 0 and len(placeholders) == 0

        return ContentValidationResult(
            score=score,
            document_type=doc_type_upper,
            passed=passed,
            missing_sections=missing,
            found_sections=found,
            section_word_counts=section_word_counts,
            placeholder_warnings=placeholders,
            thin_sections=thin,
            total_word_count=total_words,
            issues=issues,
        )

    def _extract_sections(self, content: str) -> list[SectionInfo]:
        """Extract markdown sections with their word counts."""
        sections: list[SectionInfo] = []
        lines = content.split("\n")

        current_heading: str | None = None
        current_content_lines: list[str] = []

        for line in lines:
            heading_match = _HEADING_PATTERN.match(line)
            if heading_match:
                # Save previous section
                if current_heading is not None:
                    section_text = "\n".join(current_content_lines)
                    sections.append(SectionInfo(
                        heading=current_heading,
                        word_count=len(section_text.split()),
                        content=section_text,
                    ))
                current_heading = (
                    heading_match.group(1) or heading_match.group(2)
                ).strip()
                current_content_lines = []
            else:
                current_content_lines.append(line)

        # Save last section
        if current_heading is not None:
            section_text = "\n".join(current_content_lines)
            sections.append(SectionInfo(
                heading=current_heading,
                word_count=len(section_text.split()),
                content=section_text,
            ))

        return sections

    def _section_found(self, required: str, found_headings: list[str]) -> bool:
        """Check if a required section is present (fuzzy case-insensitive)."""
        req_lower = required.lower()
        for heading in found_headings:
            if req_lower in heading or heading in req_lower:
                return True
        return False

    def _compute_score(
        self,
        required: list[str],
        missing: list[str],
        placeholders: list[PlaceholderMatch],
        thin: list[str],
    ) -> float:
        """Compute quality score (0.0 - 1.0)."""
        if not required:
            return 1.0 if not placeholders else 0.8

        found_count = len(required) - len(missing)
        section_ratio = found_count / len(required)

        placeholder_penalty = min(len(placeholders) * 0.1, 0.5)
        thin_penalty = min(len(thin) * 0.05, 0.3)

        score = section_ratio - placeholder_penalty - thin_penalty
        return max(score, 0.0)
