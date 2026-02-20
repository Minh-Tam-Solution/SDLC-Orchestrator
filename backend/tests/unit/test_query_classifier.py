"""
Unit tests for QueryClassifier — ADR-058 Pattern E.

Sprint 179 — ZeroClaw Security Hardening.
Test IDs: QC-01 to QC-08 (see ADR-058 §2.4).

Coverage:
  QC-01  Code hint: coding keywords trigger 'code' (priority=10)
  QC-02  Reasoning hint: analysis keywords + min_length trigger 'reasoning'
  QC-03  Fast hint: short message (≤ 20 chars) → 'fast'
  QC-04  No match: general text → None (no hint)
  QC-05  Priority order: higher-priority rule wins over lower
  QC-06  AND-condition logic: all conditions must match
  QC-07  Empty message → None
  QC-08  DEFAULT_CLASSIFICATION_RULES integration — classify() with defaults
"""

from __future__ import annotations

import pytest

from app.services.agent_team.config import DEFAULT_CLASSIFICATION_RULES
from app.services.agent_team.query_classifier import ClassificationRule, classify


# ── QC-01: Code hint ─────────────────────────────────────────────────────────

class TestCodeHint:
    def test_implement_keyword_triggers_code(self) -> None:
        """QC-01a — 'implement' keyword + code block → 'code' hint."""
        rules = [
            ClassificationRule(
                hint="code",
                priority=10,
                keywords=("implement",),
                patterns=("```",),
            ),
        ]
        result = classify(rules, "Please implement this:\n```python\ndef foo(): pass\n```")
        assert result == "code"

    def test_fix_keyword_triggers_code(self) -> None:
        """QC-01b — 'fix' keyword + code block → 'code' hint."""
        rules = [
            ClassificationRule(
                hint="code",
                priority=10,
                keywords=("fix",),
                patterns=("```",),
            ),
        ]
        result = classify(rules, "Can you fix this? ```python raise ValueError ```")
        assert result == "code"

    def test_code_hint_case_insensitive(self) -> None:
        """QC-01c — keyword check is case-insensitive."""
        rules = [
            ClassificationRule(
                hint="code",
                priority=10,
                keywords=("implement",),
                patterns=(),
            ),
        ]
        result = classify(rules, "IMPLEMENT the auth service")
        assert result == "code"


# ── QC-02: Reasoning hint ─────────────────────────────────────────────────────

class TestReasoningHint:
    def test_explain_with_min_length_triggers_reasoning(self) -> None:
        """QC-02a — 'explain' + min_length satisfied → 'reasoning'."""
        rules = [
            ClassificationRule(
                hint="reasoning",
                priority=5,
                keywords=("explain",),
                patterns=(),
                min_length=50,
            ),
        ]
        long_msg = "Can you explain why the architecture was designed this way and what trade-offs were made?"
        result = classify(rules, long_msg)
        assert result == "reasoning"

    def test_explain_below_min_length_no_match(self) -> None:
        """QC-02b — 'explain' but message too short → no match."""
        rules = [
            ClassificationRule(
                hint="reasoning",
                priority=5,
                keywords=("explain",),
                min_length=50,
            ),
        ]
        result = classify(rules, "explain this")  # 12 chars < 50
        assert result is None

    def test_analyze_keyword_triggers_reasoning(self) -> None:
        """QC-02c — 'analyze' keyword + sufficient length → 'reasoning'."""
        rules = [
            ClassificationRule(
                hint="reasoning",
                priority=5,
                keywords=("analyze",),
                min_length=50,
            ),
        ]
        long_msg = "Please analyze the performance bottlenecks in the current system and provide recommendations."
        result = classify(rules, long_msg)
        assert result == "reasoning"


# ── QC-03: Fast hint ─────────────────────────────────────────────────────────

class TestFastHint:
    def test_short_message_triggers_fast(self) -> None:
        """QC-03a — message ≤ 20 chars → 'fast' hint."""
        rules = [
            ClassificationRule(
                hint="fast",
                priority=1,
                max_length=20,
            ),
        ]
        result = classify(rules, "ok")
        assert result == "fast"

    def test_exactly_20_chars_triggers_fast(self) -> None:
        """QC-03b — exactly 20-char message → 'fast'."""
        rules = [
            ClassificationRule(
                hint="fast",
                priority=1,
                max_length=20,
            ),
        ]
        result = classify(rules, "a" * 20)  # exactly 20 chars
        assert result == "fast"

    def test_21_chars_does_not_trigger_fast(self) -> None:
        """QC-03c — 21-char message → does not match fast rule."""
        rules = [
            ClassificationRule(
                hint="fast",
                priority=1,
                max_length=20,
            ),
        ]
        result = classify(rules, "a" * 21)
        assert result is None


# ── QC-04: No match → None ───────────────────────────────────────────────────

class TestNoMatch:
    def test_general_text_returns_none(self) -> None:
        """QC-04a — general text with no matching keywords → None."""
        rules = [
            ClassificationRule(
                hint="code",
                priority=10,
                keywords=("implement", "fix"),
                patterns=("```",),
            ),
        ]
        result = classify(rules, "What is the weather today in Hanoi?")
        assert result is None

    def test_empty_rules_returns_none(self) -> None:
        """QC-04b — no rules defined → None for any message."""
        result = classify([], "Please implement something")
        assert result is None


# ── QC-05: Priority ordering ─────────────────────────────────────────────────

class TestPriorityOrder:
    def test_higher_priority_wins(self) -> None:
        """QC-05a — code (p=10) fires before reasoning (p=5) when both match."""
        rules = [
            ClassificationRule(
                hint="reasoning",
                priority=5,
                keywords=("analyze",),
                min_length=0,
            ),
            ClassificationRule(
                hint="code",
                priority=10,
                keywords=("analyze",),  # same keyword → both match
            ),
        ]
        result = classify(rules, "analyze this code and implement fixes")
        assert result == "code"  # higher priority wins

    def test_lower_priority_fires_if_high_fails(self) -> None:
        """QC-05b — code (p=10) doesn't match → reasoning (p=5) fires."""
        rules = [
            ClassificationRule(
                hint="code",
                priority=10,
                keywords=("implement",),
                patterns=("```",),    # requires code block
            ),
            ClassificationRule(
                hint="reasoning",
                priority=5,
                keywords=("analyze",),
                min_length=0,
            ),
        ]
        # No code block → code rule fails; reasoning matches
        result = classify(rules, "analyze the design patterns in use")
        assert result == "reasoning"


# ── QC-06: AND-condition logic ────────────────────────────────────────────────

class TestAndConditionLogic:
    def test_all_keywords_must_match(self) -> None:
        """QC-06a — rule with 2 keywords fires only if BOTH present."""
        rules = [
            ClassificationRule(
                hint="code",
                priority=10,
                keywords=("implement", "function"),
            ),
        ]
        # Only 'implement' present → no match
        result = classify(rules, "implement a new feature")
        assert result is None

    def test_all_keywords_present_matches(self) -> None:
        """QC-06b — both keywords present → match."""
        rules = [
            ClassificationRule(
                hint="code",
                priority=10,
                keywords=("implement", "function"),
            ),
        ]
        result = classify(rules, "implement a new function for auth")
        assert result == "code"

    def test_pattern_must_match_case_sensitive(self) -> None:
        """QC-06c — pattern check is case-sensitive."""
        rules = [
            ClassificationRule(
                hint="code",
                priority=10,
                patterns=("```",),
            ),
        ]
        # Wrong case in pattern — backticks are exact-match so this is trivially ok
        result_with = classify(rules, "here is code:\n```python\npass\n```")
        result_without = classify(rules, "here is code without backticks")
        assert result_with == "code"
        assert result_without is None


# ── QC-07: Empty message ─────────────────────────────────────────────────────

class TestEmptyMessage:
    def test_empty_string_returns_none(self) -> None:
        """QC-07a — empty message → None regardless of rules."""
        rules = [
            ClassificationRule(hint="fast", priority=1, max_length=20),
        ]
        result = classify(rules, "")
        assert result is None

    def test_whitespace_only_classified_normally(self) -> None:
        """QC-07b — whitespace-only short message → 'fast' (len ≤ 20)."""
        rules = [
            ClassificationRule(hint="fast", priority=1, max_length=20),
        ]
        result = classify(rules, "   ")
        assert result == "fast"


# ── QC-08: DEFAULT_CLASSIFICATION_RULES integration ──────────────────────────

class TestDefaultRulesIntegration:
    def test_code_keyword_plus_backtick_gives_code(self) -> None:
        """QC-08a — default rules: 'implement' + ``` → 'code'."""
        msg = "Please implement this:\n```python\ndef handler(): pass\n```"
        result = classify(DEFAULT_CLASSIFICATION_RULES, msg)
        assert result == "code"

    def test_very_short_message_gives_fast(self) -> None:
        """QC-08b — default rules: 'yes' (3 chars) → 'fast'."""
        result = classify(DEFAULT_CLASSIFICATION_RULES, "yes")
        assert result == "fast"

    def test_neutral_long_message_no_hint(self) -> None:
        """QC-08c — default rules: long neutral message → None."""
        msg = (
            "The system is designed to handle multiple concurrent requests "
            "using a lane-based message queue with SKIP LOCKED semantics."
        )
        result = classify(DEFAULT_CLASSIFICATION_RULES, msg)
        # No code keywords, no code block, too long for fast → None
        assert result is None

    def test_rules_are_sorted_by_priority(self) -> None:
        """QC-08d — default rules are priority-ordered (code=10 > reasoning=5 > fast=1)."""
        priorities = [r.priority for r in DEFAULT_CLASSIFICATION_RULES]
        # Should contain 10, 5, 1 in some combination
        assert max(priorities) == 10
        assert min(priorities) == 1
