"""
Reflect-after-tools — self-correction loop from Nanobot.

Sources:
- Nanobot: nanobot/agent/loop.py (reflect after tool execution)
- ADR-056 Section 10.3: Reflect-After-Tools

Injects a reflection prompt after tool execution batches so the LLM
can self-correct errors. Frequency is configurable per agent via
reflect_frequency in agent_definitions.

Sprint 177 Day 6 implementation.
"""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)

REFLECT_PROMPT = (
    "Review the tool results above. Were there any errors or unexpected outcomes? "
    "If so, explain what went wrong and suggest a corrected approach. "
    "If everything looks correct, confirm and proceed."
)


class ReflectStep:
    """
    Manages reflect-after-tools injection for LLM self-correction.

    Configuration via reflect_frequency (from agent_definitions):
      - 0 = disabled (no reflection)
      - 1 = reflect after every tool batch (Nanobot default, safest)
      - 3 = reflect every 3rd batch (balanced)
    """

    def __init__(self, frequency: int = 1):
        self.frequency = frequency

    def should_reflect(
        self,
        tool_results: list[dict[str, Any]],
        batch_index: int,
    ) -> bool:
        """
        Determine if reflection step should be injected.

        Always reflects on errors regardless of frequency.
        Otherwise follows batch_index % frequency schedule.
        """
        if self.frequency == 0:
            return False

        # Always reflect if any tool returned an error
        if any(r.get("error") for r in tool_results):
            return True

        return (batch_index % self.frequency) == 0

    @staticmethod
    def format_tool_summary(tool_results: list[dict[str, Any]]) -> str:
        """Format tool results into a human-readable summary."""
        lines: list[str] = []
        for result in tool_results:
            tool_name = result.get("tool", "unknown")
            error = result.get("error")
            if error:
                lines.append(f"- {tool_name}: ERROR: {error}")
            else:
                lines.append(f"- {tool_name}: OK")
        return "\n".join(lines)

    def inject_reflection(
        self,
        messages: list[dict[str, Any]],
        tool_results: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        """
        Append reflection prompt after tool results.

        Modifies messages in-place and returns the same list.
        """
        summary = self.format_tool_summary(tool_results)
        reflection_message = {
            "role": "user",
            "content": f"Tool execution summary:\n{summary}\n\n{REFLECT_PROMPT}",
        }
        messages.append(reflection_message)

        logger.debug(
            "Injected reflection step after %d tool results",
            len(tool_results),
        )
        return messages
