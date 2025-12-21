"""
Pattern Detector - AI Detection Strategy

SDLC Stage: 04 - BUILD
Sprint: 42 - AI Detection & Validation Pipeline
Framework: SDLC 5.1.1

Purpose:
Detect AI-generated code using heuristic pattern analysis.
Identifies common patterns in AI-generated code.

Detection Patterns:
- Over-commented code (5+ consecutive comment lines)
- Generic variable names (data1, result2, output3)
- Boilerplate patterns (TODO placeholders)
- Repeated code blocks
- Unusual formatting

Accuracy: ~50-70% (supplementary signal)
Confidence: Capped at 0.7 (pattern matching is imprecise)
"""

import re
from typing import List

from . import AIDetectionStrategy, AIToolType, DetectionMethod, DetectionResult


class PatternDetector(AIDetectionStrategy):
    """Detect AI-generated code using pattern heuristics."""

    # AI-generated code patterns (regex)
    AI_PATTERNS = [
        # Over-commented code (5+ consecutive comment lines)
        (r"(#\s*\w+.*\n){5,}", "over_commented", 0.15),
        # Generic variable names with numbers
        (r"\b(data|result|output|response|item|temp|val)\d+\b", "generic_vars", 0.1),
        # TODO placeholders (common in AI-generated code)
        (r"#\s*TODO:.*implement", "todo_placeholders", 0.1),
        # Repeated code blocks (copy-paste pattern)
        (r"(.{50,})\n\1", "repeated_blocks", 0.15),
        # Excessive blank lines (>3 consecutive)
        (r"\n\s*\n\s*\n\s*\n", "excessive_blanks", 0.05),
        # Very long function names (>40 chars)
        (r"def\s+\w{40,}\(", "long_function_names", 0.1),
        # Excessive type hints (every parameter)
        (r"def\s+\w+\([^)]*:.*,\s*[^)]*:.*,\s*[^)]*:.*\)", "excessive_types", 0.05),
    ]

    async def detect(
        self,
        pr_data: dict,
        commits: List[dict],
        diff: str,
    ) -> DetectionResult:
        """
        Detect AI-generated code from diff patterns.

        Scoring:
        - Each pattern contributes to total score
        - Max confidence: 0.7 (pattern matching is imprecise)
        - Threshold: 0.5 (detected if score > 0.5)

        Args:
            pr_data: PR data (not used by this detector)
            commits: Commit data (not used by this detector)
            diff: Unified diff of all changes

        Returns:
            DetectionResult with confidence capped at 0.7
        """
        score = 0.0
        evidence = []

        # Scan diff for AI patterns
        for pattern, pattern_name, weight in self.AI_PATTERNS:
            matches = re.findall(pattern, diff, re.MULTILINE)
            if matches:
                match_count = len(matches)
                pattern_score = min(match_count * weight, weight * 3)
                score += pattern_score

                evidence.append(
                    {
                        "pattern": pattern_name,
                        "matches": match_count,
                        "weight": weight,
                        "score": pattern_score,
                        "sample": matches[0][:100] if matches else None,
                    }
                )

        # Cap confidence at 0.7 (pattern matching alone is not reliable)
        confidence = min(score, 0.7)

        return DetectionResult(
            detected=confidence > 0.5,
            confidence=confidence,
            tool=AIToolType.OTHER if confidence > 0.5 else None,
            method=DetectionMethod.PATTERN_ANALYSIS,
            evidence={
                "total_score": score,
                "capped_confidence": confidence,
                "patterns_matched": len(evidence),
                "pattern_details": evidence,
            },
        )

    def get_strategy_name(self) -> str:
        return "pattern_analysis"
