"""
Tool context routing — ADR-056 Non-Negotiable #6.

Sources:
- Nanobot N2: nanobot/agent/subagent.py (restricted tool sets)
- Tool permission checking per agent definition
- Workspace restriction via allowed_paths

Every tool invocation receives a ToolContext that enforces permission
boundaries defined in agent_definitions.

Sprint 177 Day 6 implementation.
"""

from __future__ import annotations

import logging
from uuid import UUID

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class AgentToolPermissions(BaseModel):
    """Tool permission configuration from agent_definitions."""

    allowed_tools: list[str] = Field(default=["*"])
    denied_tools: list[str] = Field(default=[])
    can_spawn_subagent: bool = Field(default=False)
    allowed_paths: list[str] = Field(default=[])
    max_delegation_depth: int = Field(default=1)


class ToolContext(BaseModel):
    """
    Context injected into every tool invocation for permission checking.

    Carries channel/sender metadata and enforces tool boundaries.
    """

    channel: str
    chat_id: str | None = None
    thread_id: str | None = None
    sender_id: str
    origin_conversation_id: UUID
    delegation_depth: int = 0
    permissions: AgentToolPermissions = Field(default_factory=AgentToolPermissions)

    def check_tool_permission(self, tool_name: str) -> tuple[bool, str]:
        """
        Check if a tool is allowed for this agent context.

        Returns:
            (allowed, reason)
        """
        # Deny list takes priority
        if tool_name in self.permissions.denied_tools:
            logger.warning(
                "Tool denied: %s (in denied_tools for sender=%s)",
                tool_name,
                self.sender_id,
            )
            return False, f"Tool '{tool_name}' is in denied_tools"

        # Check spawn permission separately
        if tool_name in ("spawn_agent", "delegate", "create_subagent"):
            if not self.permissions.can_spawn_subagent:
                logger.warning(
                    "Spawn denied: %s (can_spawn_subagent=false for sender=%s)",
                    tool_name,
                    self.sender_id,
                )
                return False, "Agent does not have spawn permission (can_spawn_subagent=false)"

            if self.delegation_depth >= self.permissions.max_delegation_depth:
                logger.warning(
                    "Spawn denied: delegation_depth=%d >= max=%d for sender=%s",
                    self.delegation_depth,
                    self.permissions.max_delegation_depth,
                    self.sender_id,
                )
                return False, (
                    f"Delegation depth limit reached: "
                    f"{self.delegation_depth} >= {self.permissions.max_delegation_depth}"
                )

        # Allow list: ["*"] means everything allowed
        if self.permissions.allowed_tools == ["*"]:
            return True, "OK"

        if tool_name in self.permissions.allowed_tools:
            return True, "OK"

        logger.warning(
            "Tool not in allowed_tools: %s (allowed=%s for sender=%s)",
            tool_name,
            self.permissions.allowed_tools,
            self.sender_id,
        )
        return False, f"Tool '{tool_name}' not in allowed_tools: {self.permissions.allowed_tools}"

    def check_path_allowed(self, file_path: str) -> tuple[bool, str]:
        """
        Check if a file path is within the agent's workspace restriction.

        Returns:
            (allowed, reason)
        """
        if not self.permissions.allowed_paths:
            return True, "OK (no path restrictions)"

        for allowed_path in self.permissions.allowed_paths:
            if file_path.startswith(allowed_path):
                return True, f"OK (matches {allowed_path})"

        logger.warning(
            "Path not allowed: %s (allowed=%s for sender=%s)",
            file_path,
            self.permissions.allowed_paths,
            self.sender_id,
        )
        return False, (
            f"Path '{file_path}' not in allowed_paths: "
            f"{self.permissions.allowed_paths}"
        )
