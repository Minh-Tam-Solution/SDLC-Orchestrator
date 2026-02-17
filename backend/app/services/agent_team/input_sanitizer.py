"""
External content sanitization — ADR-056 Non-Negotiable #4.

Sources:
- OpenClaw: src/security/external-content.ts (12 injection regex patterns)
- CTO Review: Mandatory for all OTT input into agent context

All OTT messages are wrapped through sanitize_external_input() before
being injected into agent conversation context.

Sprint 177 Day 7 implementation.
"""

from __future__ import annotations

import logging
import re

logger = logging.getLogger(__name__)

# 12 injection regex patterns (from OpenClaw src/security/external-content.ts)
INJECTION_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    (
        "system_prompt_override",
        re.compile(
            r"(?i)(ignore|forget|disregard)\s+(previous|above|all)\s+(instructions|prompts|rules)",
        ),
    ),
    (
        "role_injection",
        re.compile(r"(?i)you\s+are\s+(now|a)\s+"),
    ),
    (
        "delimiter_escape",
        re.compile(r"(```|<\|im_sep\|>|<\|system\|>|<\|end\|>)"),
    ),
    (
        "base64_payload",
        re.compile(r"(?i)base64[:\s]"),
    ),
    (
        "prompt_leak_attempt",
        re.compile(r"(?i)(show|reveal|print|output)\s+(your|the|system)\s+(prompt|instructions|rules)"),
    ),
    (
        "instruction_override",
        re.compile(r"(?i)(new\s+instructions?|override\s+instructions?|updated?\s+rules?)"),
    ),
    (
        "jailbreak_prefix",
        re.compile(r"(?i)(DAN|developer\s+mode|jailbreak|bypass\s+filter)"),
    ),
    (
        "xml_injection",
        re.compile(r"<(system|assistant|user|function|tool)[\s>]"),
    ),
    (
        "markdown_injection",
        re.compile(r"!\[.*?\]\(https?://"),
    ),
    (
        "unicode_escape",
        re.compile(r"\\u[0-9a-fA-F]{4}"),
    ),
    (
        "repetition_attack",
        re.compile(r"(.{5,})\1{4,}"),
    ),
    (
        "data_exfil_url",
        re.compile(r"(?i)(fetch|curl|wget|http\.get)\s*\(?['\"]?https?://"),
    ),
]


class InputSanitizer:
    """
    Sanitizes external input (OTT channels, webhooks) before injection
    into agent conversation context.

    Usage:
        sanitizer = InputSanitizer()
        clean, violations = sanitizer.sanitize_external_input(raw_message)
        if violations:
            logger.warning("Input violations: %s", violations)
    """

    def __init__(self, extra_patterns: list[tuple[str, re.Pattern[str]]] | None = None):
        self.patterns = list(INJECTION_PATTERNS)
        if extra_patterns:
            self.patterns.extend(extra_patterns)

    def check_violations(self, text: str) -> list[str]:
        """
        Check text against all injection patterns.

        Returns list of pattern names that matched.
        """
        violations: list[str] = []
        for name, pattern in self.patterns:
            if pattern.search(text):
                violations.append(name)
        return violations

    def sanitize_external_input(self, text: str) -> tuple[str, list[str]]:
        """
        Sanitize external input by wrapping it in a safe container.

        Returns:
            (sanitized_text, violations) — violations is empty if clean.

        The text is always wrapped regardless of violations, as defense-in-depth.
        Violations are logged for audit trail.
        """
        violations = self.check_violations(text)

        if violations:
            logger.warning(
                "Input sanitization: %d violations detected: %s",
                len(violations),
                violations,
            )

        # Wrap in safe container (defense-in-depth)
        sanitized = (
            f"[EXTERNAL_INPUT channel=ott]\n"
            f"{text}\n"
            f"[/EXTERNAL_INPUT]"
        )

        return sanitized, violations
