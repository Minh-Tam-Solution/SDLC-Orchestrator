"""
Shell command safety guard — ADR-056 Non-Negotiable #5.

Sources:
- Nanobot N6: nanobot/agent/tools/shell.py (8 deny patterns)
- Path traversal detection
- Output truncation (10KB)

Blocks dangerous shell commands before execution by agent tools.

Sprint 177 Day 6 implementation.
"""

from __future__ import annotations

import logging
import re

logger = logging.getLogger(__name__)

# 8 deny regex patterns (from Nanobot nanobot/agent/tools/shell.py:29-38)
DENY_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    (
        "recursive_delete",
        re.compile(r"rm\s+(-[rf]+\s+)*/"),
    ),
    (
        "fork_bomb",
        re.compile(r":\(\)\{.*\|.*&\s*\};"),
    ),
    (
        "system_control",
        re.compile(r"(shutdown|reboot|halt|poweroff)"),
    ),
    (
        "disk_operations",
        re.compile(r"(mkfs|fdisk|dd\s+if=)"),
    ),
    (
        "raw_disk_write",
        re.compile(r">\s*/dev/sd"),
    ),
    (
        "unsafe_permissions",
        re.compile(r"chmod\s+(-R\s+)?777"),
    ),
    (
        "pipe_to_shell",
        re.compile(r"curl.*\|\s*(bash|sh)"),
    ),
    (
        "eval_injection",
        re.compile(r"eval\s*\("),
    ),
]

MAX_OUTPUT_SIZE = 10 * 1024  # 10KB


class ShellGuard:
    """
    Guards shell command execution by checking deny patterns,
    detecting path traversal, and truncating output.

    Usage:
        guard = ShellGuard(allowed_paths=["/project/src/"])
        allowed, reason = guard.check_command("rm -rf /")
        if not allowed:
            raise SecurityError(reason)
    """

    def __init__(
        self,
        allowed_paths: list[str] | None = None,
        extra_deny_patterns: list[tuple[str, re.Pattern[str]]] | None = None,
    ):
        self.allowed_paths = allowed_paths or []
        self.deny_patterns = list(DENY_PATTERNS)
        if extra_deny_patterns:
            self.deny_patterns.extend(extra_deny_patterns)

    def check_command(self, command: str) -> tuple[bool, str]:
        """
        Check if a shell command is safe to execute.

        Returns:
            (allowed, reason) — allowed=False means command is blocked.
        """
        # Check deny patterns
        for name, pattern in self.deny_patterns:
            if pattern.search(command):
                logger.warning(
                    "Shell guard blocked command (pattern=%s): %.100s",
                    name,
                    command,
                )
                return False, f"Blocked by deny pattern: {name}"

        # Check path traversal
        if ".." in command:
            logger.warning(
                "Shell guard blocked command (path traversal): %.100s",
                command,
            )
            return False, "Path traversal detected: '..' in command"

        # Check workspace restriction (advisory for allowed_paths)
        if self.allowed_paths:
            # Extract file-like tokens from command
            tokens = command.split()
            for token in tokens:
                if token.startswith("/") and not any(
                    token.startswith(p) for p in self.allowed_paths
                ):
                    logger.warning(
                        "Shell guard blocked command (path restriction): %.100s "
                        "(token=%s not in allowed_paths=%s)",
                        command,
                        token,
                        self.allowed_paths,
                    )
                    return False, (
                        f"Path not allowed: {token} "
                        f"(allowed: {self.allowed_paths})"
                    )

        return True, "OK"

    @staticmethod
    def truncate_output(output: str) -> str:
        """
        Truncate command output to MAX_OUTPUT_SIZE (10KB).

        Prevents unbounded context injection from verbose commands.
        """
        if len(output) > MAX_OUTPUT_SIZE:
            truncated = output[:MAX_OUTPUT_SIZE]
            return (
                f"{truncated}\n"
                f"... truncated ({len(output):,} bytes total, "
                f"limit {MAX_OUTPUT_SIZE:,} bytes)"
            )
        return output
