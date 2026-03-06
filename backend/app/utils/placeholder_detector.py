"""
Placeholder Detector — shared regex utility for detecting placeholder content.

Sprint 223: Cross-project review finding (EndiorBot Sprint 80 gap G3).
Reused by content_validator.py (S223) and auto_generator.py (S224).

Usage:
    from app.utils.placeholder_detector import detect_placeholders

    matches = detect_placeholders("## Decision\\n[TODO: fill in later]\\n")
    # [PlaceholderMatch(line_number=2, pattern="TODO bracket", text="[TODO: fill in later]")]
"""

from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass
class PlaceholderMatch:
    """A detected placeholder in document content."""
    line_number: int
    pattern: str
    text: str


# Patterns that indicate placeholder/stub content
# NOTE: Mirrored in content_quality.rego (OPA cannot import Python).
# Update both files when adding/removing patterns.
_PLACEHOLDER_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    ("TODO bracket", re.compile(r"\[.*TODO.*\]", re.IGNORECASE)),
    ("TBD bracket", re.compile(r"\[.*TBD.*\]", re.IGNORECASE)),
    ("please bracket", re.compile(r"\[.*please.*\]", re.IGNORECASE)),
    ("implement bracket", re.compile(r"\[.*implement.*\]", re.IGNORECASE)),
    ("auto-generation marker", re.compile(r"\[Auto-generation.*\]", re.IGNORECASE)),
    ("fill in marker", re.compile(r"\[.*fill in.*\]", re.IGNORECASE)),
    ("insert here marker", re.compile(r"\[.*insert.*here.*\]", re.IGNORECASE)),
    ("placeholder marker", re.compile(r"\[.*placeholder.*\]", re.IGNORECASE)),
]


def detect_placeholders(content: str) -> list[PlaceholderMatch]:
    """
    Scan document content for placeholder patterns.

    Args:
        content: Full text content of a document.

    Returns:
        List of PlaceholderMatch instances, one per detected placeholder.
        Empty list if no placeholders found.
    """
    matches: list[PlaceholderMatch] = []
    lines = content.split("\n")

    for line_idx, line in enumerate(lines):
        for pattern_name, regex in _PLACEHOLDER_PATTERNS:
            for m in regex.finditer(line):
                matches.append(PlaceholderMatch(
                    line_number=line_idx + 1,
                    pattern=pattern_name,
                    text=m.group(0),
                ))

    return matches
