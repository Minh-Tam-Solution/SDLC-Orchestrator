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

    # False positive protection patterns (CTO P0 - Sprint 42 Day 5)
    # These patterns indicate NON-AI contexts for ambiguous keywords
    FALSE_POSITIVE_PATTERNS: Dict[AIToolType, List[str]] = {
        AIToolType.CURSOR: [
            # Database/text cursor contexts
            r"database\s+cursor",
            r"db\s+cursor",
            r"cursor\s+position",
            r"cursor\s+movement",
            r"move\s+cursor",
            r"text\s+cursor",
            r"cursor\s+to\s+(end|start|line|position)",
            r"cursor\s+handling",
            r"cursor\s+management",
            r"connection\.cursor",
            r"cursor\s+leak",
            r"with.*cursor.*as",
        ],
        AIToolType.COPILOT: [
            # Aviation/vehicle copilot contexts
            r"co-?pilot\s+seat",
            r"autopilot",
            r"pilot\s+project",
            r"pilot\s+test",
            r"flight.*co-?pilot",
            r"aircraft.*co-?pilot",
        ],
        AIToolType.CLAUDE_CODE: [
            # Claude Shannon or other Claude references
            r"claude\s+shannon",
            r"shannon.*claude",
            r"information\s+theory.*claude",
        ],
        AIToolType.CHATGPT: [
            # Academic paper references
            r"gpt-?2\s+paper",
            r"paper.*gpt-?2",
            r"citation.*gpt",
            r"reference.*gpt-?2",
        ],
        AIToolType.WINDSURF: [
            # Windsurfing sport contexts
            r"windsurf\s+sport",
            r"windsurf\s+event",
            r"windsurf\s+booking",
            r"windsurfing",
            r"windsurf\s+handler",
            r"windsurf.*event.*handler",
        ],
        AIToolType.CODY: [
            # Cody as a name/mascot
            r"cody\s+bear",
            r"cody\s+mascot",
            r"cody\s+image",
            r"mascot.*cody",
        ],
    }

    # Tool keyword patterns (case-insensitive regex)
    # Expanded patterns for Sprint 42 Day 5 accuracy target (≥85%)
    TOOL_PATTERNS: Dict[AIToolType, List[str]] = {
        AIToolType.CURSOR: [
            r"\bcursor\b",
            r"cursor\.sh",
            r"cursor\s+ai",
            r"cursor-generated",
            r"cursor\s+generated",
            r"with\s+cursor",
            r"using\s+cursor",
            r"\(cursor\)",
            r"\[cursor\]",
            r"cursor\s+assist",
        ],
        AIToolType.COPILOT: [
            r"\bcopilot\b",
            r"github\s+copilot",
            r"🤖",
            r"co-pilot",
            r"copilot-suggested",
            r"copilot\s+generated",
            r"with\s+copilot",
            r"using\s+copilot",
            r"\(copilot\)",
            r"\[copilot\]",
            r"copilot\s+assist",
        ],
        AIToolType.CLAUDE_CODE: [
            r"\bclaude\b",
            r"claude\s+code",
            r"anthropic",
            r"claude\s+ai",
            r"generated\s+by\s+claude",
            r"generated\s+with\s+claude",
            r"with\s+claude",
            r"using\s+claude",
            r"\(claude\)",
            r"\[claude\]",
            r"claude\s+assist",
        ],
        AIToolType.CHATGPT: [
            r"\bchatgpt\b",
            r"gpt-4",
            r"gpt-3\.5",
            r"openai",
            r"chatgpt-generated",
            r"chatgpt\s+generated",
            r"with\s+chatgpt",
            r"using\s+chatgpt",
            r"\(chatgpt\)",
            r"\[chatgpt\]",
        ],
        AIToolType.WINDSURF: [
            r"\bwindsurf\b",
            r"codeium\s+windsurf",
            r"codeium",
            r"with\s+windsurf",
            r"using\s+windsurf",
            r"\(windsurf\)",
            r"\[windsurf\]",
        ],
        AIToolType.CODY: [
            r"\bcody\b",
            r"sourcegraph\s+cody",
            r"sourcegraph",
            r"with\s+cody",
            r"using\s+cody",
            r"\(cody\)",
            r"\[cody\]",
        ],
        AIToolType.TABNINE: [
            r"\btabnine\b",
            r"tab\s+nine",
            r"with\s+tabnine",
            r"using\s+tabnine",
            r"\(tabnine\)",
            r"\[tabnine\]",
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

        Improved Scoring (Sprint 42 Day 5 accuracy tuning):
        - Any single match in title/body/commits → baseline 0.6 confidence
        - Multiple matches across sources → higher confidence
        - Ensures body-only matches still exceed 0.5 threshold

        False Positive Protection (CTO P0 - Sprint 42 Day 5):
        - Check for negative patterns that indicate non-AI contexts
        - e.g., "database cursor" != Cursor AI, "pilot project" != Copilot

        Detection Philosophy:
        - If AI tool is explicitly mentioned anywhere, we should detect it
        - Single mention in body is sufficient evidence for AI usage
        - Multiple mentions increase confidence

        Args:
            tool: AI tool to check
            patterns: Regex patterns for this tool
            title: PR title (lowercased)
            body: PR body (lowercased)
            commit_messages: List of commit messages (lowercased)

        Returns:
            Confidence score (0.0 - 1.0)
        """
        # CTO P0: Check for false positive patterns first
        fp_patterns = self.FALSE_POSITIVE_PATTERNS.get(tool, [])
        combined_text = f"{title} {body} {' '.join(commit_messages)}"
        if any(re.search(p, combined_text, re.IGNORECASE) for p in fp_patterns):
            # False positive detected - return zero confidence
            return 0.0

        title_match = any(re.search(p, title, re.IGNORECASE) for p in patterns)
        body_match = any(re.search(p, body, re.IGNORECASE) for p in patterns)

        # Count commits with matches
        commit_matches = sum(
            any(re.search(p, msg, re.IGNORECASE) for p in patterns)
            for msg in commit_messages
        )
        has_commit_match = commit_matches > 0

        # Count total match sources (0-3)
        match_count = sum([title_match, body_match, has_commit_match])

        if match_count == 0:
            return 0.0

        # Base confidence for any match: 0.6 (above 0.5 threshold)
        # Additional matches add 0.15 each (max 0.9 for all 3)
        base_confidence = 0.6
        additional_confidence = (match_count - 1) * 0.15

        # Bonus for high commit ratio (all commits have AI marker)
        commit_ratio_bonus = 0.0
        if commit_messages and commit_matches == len(commit_messages):
            commit_ratio_bonus = 0.1

        score = min(base_confidence + additional_confidence + commit_ratio_bonus, 1.0)

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
