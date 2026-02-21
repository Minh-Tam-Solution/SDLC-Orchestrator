"""
=========================================================================
Query Classifier — ADR-058 Pattern E (ZeroClaw)
SDLC Orchestrator - Sprint 179 (ZeroClaw Security Hardening)

Version: 1.0.0
Date: February 2026
Status: ACTIVE - Sprint 179
Authority: CTO Approved (ADR-058 Decision 3)
Reference: ADR-058-ZeroClaw-Best-Practice-Adoption.md

Purpose:
- Classify incoming messages to route to the right model tier.
- Pure function: classify(rules, message) → Optional[hint_string]
- First matching rule (by priority) wins.
- Hint maps to MODEL_ROUTE_HINTS in config.py for model override.
- Integration: team_orchestrator._process() calls classify() before
  _build_invoker(), passing hint as model_hint kwarg.

Classification Rules (ADR-058 §2.4):
  code (priority=10):  coding tasks → qwen3-coder:30b (256K context)
  reasoning (p=5):     analysis/explain → deepseek-r1:32b (thinking mode)
  fast (p=1):          short confirmations → qwen3:8b (fastest)

Rule conditions (AND logic — all conditions must match):
  - keywords: case-insensitive substring match against full message text
  - patterns: case-sensitive substring match (code snippets, markers)
  - min_length: message length (chars) must be >= min_length
  - max_length: message length must be <= max_length

If no rule matches, returns None (use default model from ROLE_MODEL_DEFAULTS).

References:
  - ADR-058 Decision 3 (LOCKED)
  - ZeroClaw src/agent/classifier.rs (pure function, single pass)
  - config.py: DEFAULT_CLASSIFICATION_RULES + MODEL_ROUTE_HINTS
=========================================================================
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class ClassificationRule:
    """
    A single query classification rule.

    All non-empty conditions are ANDed: the rule fires only if ALL
    specified conditions match the message.

    Attributes:
        hint:        Model routing hint returned when this rule matches.
        priority:    Higher number = checked first (sorted descending).
        keywords:    Case-insensitive substrings that must ALL appear.
        patterns:    Case-sensitive substrings that must ALL appear.
        min_length:  Minimum message length in chars (0 = no minimum).
        max_length:  Maximum message length in chars (0 = no maximum).
    """

    hint: str
    priority: int = 5
    keywords: tuple[str, ...] = field(default_factory=tuple)
    patterns: tuple[str, ...] = field(default_factory=tuple)
    min_length: int = 0
    max_length: int = 0


def classify(
    rules: list[ClassificationRule],
    message: str,
) -> str | None:
    """
    Classify a message and return a model routing hint.

    Pure function — no side effects, no I/O.

    Rules are evaluated in descending priority order. The first rule
    whose ALL conditions match returns its hint.

    Conditions checked (AND logic):
    - keywords: every keyword must appear in lower(message)
    - patterns: every pattern must appear in message (case-sensitive)
    - min_length: len(message) >= rule.min_length (if non-zero)
    - max_length: len(message) <= rule.max_length (if non-zero)

    Args:
        rules: List of ClassificationRule to evaluate.
        message: The incoming message text to classify.

    Returns:
        Hint string (e.g., "code", "reasoning", "fast") if a rule fires,
        or None if no rule matched (use default model).
    """
    if not message:
        return None

    msg_lower = message.lower()
    msg_len = len(message)

    # Sort by priority descending; stable sort preserves insertion order
    # for equal-priority rules.
    sorted_rules = sorted(rules, key=lambda r: r.priority, reverse=True)

    for rule in sorted_rules:
        # Keyword check (case-insensitive, ALL must match)
        if rule.keywords and not all(kw in msg_lower for kw in rule.keywords):
            continue

        # Pattern check (case-sensitive, ALL must match)
        if rule.patterns and not all(pat in message for pat in rule.patterns):
            continue

        # Length checks
        if rule.min_length and msg_len < rule.min_length:
            continue
        if rule.max_length and msg_len > rule.max_length:
            continue

        # All conditions passed — return this rule's hint
        return rule.hint

    return None
