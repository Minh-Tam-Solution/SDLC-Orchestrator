"""
Output Credential Scrubber — ADR-058 Pattern A (ZeroClaw)

Sprint 179, Day 1-2.
Scrubs credentials from agent tool output BEFORE the output is fed
back into the LLM context or stored in the Evidence Vault.

7 credential patterns:
  - 6 key:value patterns (token, api_key, password, secret, bearer,
    credential/credentials) match KEY=VALUE / KEY:VALUE formats
    (case-insensitive).  Matched values are redacted, preserving the
    first 4 characters for debugging.
  - 1 PEM block pattern (Reviewer R-01) replaces private/public key
    blocks in their entirety with "[PEM_KEY_REDACTED]".

Integration points (see ADR-058 §2.1.2):
  1. AgentInvoker.invoke() — scrub InvocationResult.content post-invocation
  2. EvidenceCollector.capture_message() — scrub BEFORE SHA256 hash

Idempotent: scrub() checks for the ``****[REDACTED]`` suffix before
redacting and skips already-redacted values, so applying scrub() twice
produces identical output.

References:
  - FR-042 Output Credential Scrubbing
  - ADR-058 Decision 1 (LOCKED)
  - ZeroClaw src/agent/loop_.rs -> scrub_credentials()
  - CWE-200 Exposure of Sensitive Information
  - STM-056 T11 (credential leakage)
  - Reviewer R-01 (PEM blocks), R-02 (credentials plural)
"""

from __future__ import annotations

import logging
import re

logger = logging.getLogger(__name__)

# ---------- Redaction marker ----------
_REDACTED_SUFFIX = "****[REDACTED]"

# ---------- Pattern 7: PEM key blocks (Reviewer R-01) ----------
# Applied FIRST (multiline) before key:value patterns.
# Covers RSA, EC, OPENSSH, DSA and bare PRIVATE/PUBLIC KEY headers.
_PEM_PATTERN: re.Pattern[str] = re.compile(
    r"-----BEGIN (?:RSA |EC |OPENSSH |DSA )?(?:PRIVATE|PUBLIC) KEY-----"
    r"[\s\S]+?"
    r"-----END (?:RSA |EC |OPENSSH |DSA )?(?:PRIVATE|PUBLIC) KEY-----",
    re.MULTILINE,
)

# ---------- Patterns 1-6: key:value credential patterns ----------
# Each tuple: (pattern_name, compiled_regex)
# Patterns match:  KEY <sep> VALUE  where sep = '=' | ':' | whitespace
# Values terminate at whitespace, comma, semicolon, quote, or EOL.
# Bearer pattern is special: "Bearer <token>" / "bearer <token>".
#
# Idempotency: the value capture group is checked for _REDACTED_SUFFIX
# before substitution — already-redacted values are skipped.

_CREDENTIAL_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    (
        "token",
        re.compile(
            r"(?i)(token\s*[=:]\s*)([^\s,;\"']+)",
        ),
    ),
    (
        "api_key",
        re.compile(
            r"(?i)(api[_-]?key\s*[=:]\s*)([^\s,;\"']+)",
        ),
    ),
    (
        "password",
        re.compile(
            r"(?i)(passw(?:or)?d\s*[=:]\s*)([^\s,;\"']+)",
        ),
    ),
    (
        "secret",
        re.compile(
            r"(?i)(secret(?:[_-]?key)?\s*[=:]\s*)([^\s,;\"']+)",
        ),
    ),
    (
        "bearer",
        re.compile(
            r"(?i)((?:Authorization:\s*)?Bearer\s+)([^\s,;\"']+)",
        ),
    ),
    (
        # R-02: regex covers both singular (credential) and plural (credentials)
        "credential",
        re.compile(
            r"(?i)(credentials?\s*[=:]\s*)([^\s,;\"']+)",
        ),
    ),
]


class OutputScrubber:
    """
    Regex-based credential scrubber for agent output text.

    Applies 7 patterns in two passes:
    1. PEM key block replacement (pattern 7, R-01)
    2. Key:value redaction (patterns 1-6)

    Usage::

        scrubber = OutputScrubber()
        clean, violations = scrubber.scrub(raw_text)
        # violations: ["token", "api_key"] — pattern names that fired

    Thread-safe: stateless — instances carry no mutable state.
    """

    # Public constant so callers can reference the suffix if needed.
    REDACTED_SUFFIX = _REDACTED_SUFFIX

    def scrub(self, text: str) -> tuple[str, list[str]]:
        """
        Scrub credential values from *text*.

        Processing order:
        1. PEM key blocks (multiline, entire block replaced — R-01)
        2. Key:value patterns (6 patterns, idempotency-guarded)

        Args:
            text: Raw agent output (shell result, file content, etc.).

        Returns:
            Tuple of (scrubbed_text, violations) where *violations* is a
            deduplicated list of pattern names that matched
            (e.g. ``["token", "bearer"]``).
            If no patterns match, *text* is returned unchanged with ``[]``.
        """
        if not text:
            return text, []

        violations: list[str] = []

        # ── Pass 1: PEM blocks ──────────────────────────────────────────
        pem_matches = _PEM_PATTERN.findall(text)
        if pem_matches:
            text = _PEM_PATTERN.sub("[PEM_KEY_REDACTED]", text)
            violations.append("pem_block")
            logger.debug(
                "TRACE_SCRUBBER pem_blocks_redacted=%d", len(pem_matches)
            )

        # ── Pass 2: key:value patterns ──────────────────────────────────
        for pattern_name, regex in _CREDENTIAL_PATTERNS:
            hit_ref: list[bool] = [False]

            def _replace(
                m: re.Match[str],
                _ref: list[bool] = hit_ref,
            ) -> str:
                value = m.group(2)
                # Idempotency guard: already-redacted value → leave unchanged
                if _REDACTED_SUFFIX in value:
                    return m.group(0)
                _ref[0] = True
                return m.group(1) + self._redact_value(value)

            text = regex.sub(_replace, text)
            if hit_ref[0] and pattern_name not in violations:
                violations.append(pattern_name)

        if violations:
            logger.warning(
                "TRACE_SCRUBBER patterns_matched=%s",
                violations,
            )

        return text, violations

    # ------------------------------------------------------------------
    @staticmethod
    def _redact_value(value: str) -> str:
        """
        Preserve first 4 chars of *value* + ``****[REDACTED]``.

        If *value* is shorter than 4 chars the entire value is preserved
        and the redaction suffix is appended (FR-042 §2.4).
        """
        prefix = value[:4]
        return f"{prefix}{_REDACTED_SUFFIX}"
