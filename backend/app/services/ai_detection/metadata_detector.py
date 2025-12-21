"""
Metadata Detector - AI Detection Strategy

SDLC Stage: 04 - BUILD
Sprint: 42 - AI Detection & Validation Pipeline
Framework: SDLC 5.1.1

Purpose:
Detect AI tools from PR metadata (title, body, commit messages).
Uses keyword pattern matching with confidence scoring.

Detection Approach:
- Weighted scoring: Title (40%), Body (30%), Commits (30%)
- Pattern matching with regex (case-insensitive)
- Supports 8 AI tools (Cursor, Copilot, Claude, ChatGPT, etc.)

Accuracy Target: ~70% (combined with other strategies → 85%)
"""

import re
from typing import Dict, List, Optional

from . import AIDetectionStrategy, AIToolType, DetectionMethod, DetectionResult


class MetadataDetector(AIDetectionStrategy):
    """Detect AI tools from PR metadata (title, body, commits)."""

    # Tool keyword patterns (case-insensitive regex)
    TOOL_PATTERNS: Dict[AIToolType, List[str]] = {
        AIToolType.CURSOR: [
            r"\bcursor\b",
            r"cursor\.sh",
            r"cursor\s+ai",
            r"cursor-generated",
        ],
        AIToolType.COPILOT: [
            r"\bcopilot\b",
            r"github\s+copilot",
            r"🤖",
            r"co-pilot",
            r"copilot-suggested",
        ],
        AIToolType.CLAUDE_CODE: [
            r"\bclaude\b",
            r"claude\s+code",
            r"anthropic",
            r"claude\s+ai",
            r"generated\s+by\s+claude",
        ],
        AIToolType.CHATGPT: [
            r"\bchatgpt\b",
            r"gpt-4",
            r"gpt-3\.5",
            r"openai",
            r"chatgpt-generated",
        ],
        AIToolType.WINDSURF: [
            r"\bwindsurf\b",
            r"codeium\s+windsurf",
        ],
        AIToolType.CODY: [
            r"\bcody\b",
            r"sourcegraph\s+cody",
        ],
        AIToolType.TABNINE: [
            r"\btabnine\b",
            r"tab\s+nine",
        ],
    }

    async def detect(
        self,
        pr_data: dict,
        commits: List[dict],
        diff: str,
    ) -> DetectionResult:
        """
        Detect AI tool from metadata analysis.

        Scoring Formula:
        score = (title_match * 0.4) + (body_match * 0.3) + (commit_ratio * 0.3)

        Args:
            pr_data: PR data with title, body, labels
            commits: List of commit objects
            diff: Unified diff (not used by this detector)

        Returns:
            DetectionResult with confidence score
        """
        title = (pr_data.get("title") or "").lower()
        body = (pr_data.get("body") or "").lower()

        # Aggregate commit messages
        commit_messages = [
            (commit.get("commit", {}).get("message") or "").lower()
            for commit in commits
        ]

        # Score each tool
        tool_scores: Dict[AIToolType, float] = {}
        for tool, patterns in self.TOOL_PATTERNS.items():
            score = self._calculate_tool_score(
                tool, patterns, title, body, commit_messages
            )
            if score > 0:
                tool_scores[tool] = score

        # Determine best match
        if not tool_scores:
            return DetectionResult(
                detected=False,
                confidence=0.0,
                tool=None,
                method=DetectionMethod.METADATA,
                evidence={"matches": [], "scores": {}},
            )

        best_tool = max(tool_scores, key=tool_scores.get)
        confidence = tool_scores[best_tool]

        return DetectionResult(
            detected=confidence > 0.5,
            confidence=confidence,
            tool=best_tool,
            method=DetectionMethod.METADATA,
            evidence={
                "tool_scores": {t.value: s for t, s in tool_scores.items()},
                "best_match": best_tool.value,
                "matched_in": self._get_match_locations(
                    best_tool, title, body, commit_messages
                ),
            },
        )

    def _calculate_tool_score(
        self,
        tool: AIToolType,
        patterns: List[str],
        title: str,
        body: str,
        commit_messages: List[str],
    ) -> float:
        """
        Calculate confidence score for a specific tool.

        Weighted formula:
        - Title match: 40% (most explicit signal)
        - Body match: 30% (often contains details)
        - Commit ratio: 30% (consistent signal across commits)

        Args:
            tool: AI tool to check
            patterns: Regex patterns for this tool
            title: PR title (lowercased)
            body: PR body (lowercased)
            commit_messages: List of commit messages (lowercased)

        Returns:
            Confidence score (0.0 - 1.0)
        """
        title_match = any(re.search(p, title, re.IGNORECASE) for p in patterns)
        body_match = any(re.search(p, body, re.IGNORECASE) for p in patterns)

        # Count commits with matches
        commit_matches = sum(
            any(re.search(p, msg, re.IGNORECASE) for p in patterns)
            for msg in commit_messages
        )
        commit_ratio = (
            commit_matches / len(commit_messages) if commit_messages else 0.0
        )

        # Weighted score
        score = (
            (1.0 if title_match else 0.0) * 0.4
            + (1.0 if body_match else 0.0) * 0.3
            + commit_ratio * 0.3
        )

        return score

    def _get_match_locations(
        self,
        tool: AIToolType,
        title: str,
        body: str,
        commit_messages: List[str],
    ) -> List[str]:
        """Get list of locations where tool was detected."""
        locations = []
        patterns = self.TOOL_PATTERNS.get(tool, [])

        if any(re.search(p, title, re.IGNORECASE) for p in patterns):
            locations.append("title")

        if any(re.search(p, body, re.IGNORECASE) for p in patterns):
            locations.append("body")

        commit_count = sum(
            any(re.search(p, msg, re.IGNORECASE) for p in patterns)
            for msg in commit_messages
        )
        if commit_count > 0:
            locations.append(f"commits ({commit_count}/{len(commit_messages)})")

        return locations

    def get_strategy_name(self) -> str:
        return "metadata"
