"""
Tool context routing — ADR-056 Non-Negotiable #6.

Sources:
- Nanobot N2: nanobot/agent/subagent.py (restricted tool sets)
- Tool permission checking per agent definition
- Workspace restriction via allowed_paths

Every tool invocation receives a ToolContext that enforces permission
boundaries defined in agent_definitions.

Sprint 177 Day 6 implementation.
Sprint 202 addition: save_note / recall_note internal tools for agent memory.
Sprint 205 addition: ToolPermissionDenied + authorize_tool_call() for LangChain tools (ADR-066 B2).
Sprint 216 addition: DelegationGuard — check delegation_links before spawn (ADR-069, FR-051).
"""

from __future__ import annotations

import logging
from uuid import UUID

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

# Internal tool names — Sprint 177 (spawn) + Sprint 202 (notes)
SPAWN_TOOLS = frozenset({"spawn_agent", "delegate", "create_subagent"})
NOTE_TOOLS = frozenset({"save_note", "recall_note"})
INTERNAL_TOOLS = SPAWN_TOOLS | NOTE_TOOLS


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
        if tool_name in SPAWN_TOOLS:
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


# ─────────────────────────────────────────────────────────────────────────────
# Sprint 205 — LangChain tool authorization guard (ADR-066 B2)
# ─────────────────────────────────────────────────────────────────────────────


class ToolPermissionDenied(Exception):
    """
    Raised when authorize_tool_call() denies a LangChain tool invocation.

    Defined in tool_context.py (not langchain_tool_registry.py) so it is
    importable without the optional LangChain packages installed.
    """


# Convenience alias — FR-045 test specs reference "PermissionDenied"
PermissionDenied = ToolPermissionDenied


def authorize_tool_call(
    tool_name: str,
    tool_context: "ToolContext | None",
) -> None:
    """
    Centralized guard for LangChain StructuredTool calls (ADR-066 B2).

    Called by every tool implementation function in langchain_tool_registry.py
    before executing any action.  Raises ToolPermissionDenied when the
    ToolContext denies the tool.  If tool_context is None the check is
    skipped — the orchestrator layer handles permission enforcement in that case.

    Args:
        tool_name:    Name of the LangChain tool being invoked.
        tool_context: Active ToolContext with agent permissions, or None.

    Raises:
        ToolPermissionDenied: When tool_context is set and tool is not allowed.
    """
    if tool_context is None:
        return  # No context → no restriction (test mode or integration layer)

    allowed, reason = tool_context.check_tool_permission(tool_name)
    if not allowed:
        logger.warning(
            "LangChain tool call denied: tool=%s reason=%s",
            tool_name,
            reason,
        )
        raise ToolPermissionDenied(f"Tool '{tool_name}' not authorized: {reason}")


# ─────────────────────────────────────────────────────────────────────────────
# Sprint 216 — Delegation guard for spawn tools (ADR-069, FR-051)
# ─────────────────────────────────────────────────────────────────────────────


class DelegationDenied(ToolPermissionDenied):
    """
    Raised when an agent tries to delegate to an unauthorized target.

    Subclass of ToolPermissionDenied so callers catching the base class
    also catch delegation failures.
    """


async def check_delegation_authorized(
    source_agent_id: "UUID",
    target_agent_id: "UUID",
    db: "AsyncSession",
    available_targets: list[str] | None = None,
) -> None:
    """
    Spawn tool guard: check delegation_links before creating child conversation.

    Called before any agent spawn/delegate action. If no active delegation
    link exists from source to target, raises DelegationDenied with an
    actionable error listing available targets.

    Args:
        source_agent_id: The agent attempting to delegate.
        target_agent_id: The target agent being delegated to.
        db: Async database session.
        available_targets: Pre-fetched target names (optimization to avoid extra query).

    Raises:
        DelegationDenied: When no active link exists from source to target.
    """
    from app.services.agent_team.delegation_service import DelegationService

    delegation_svc = DelegationService(db)
    authorized = await delegation_svc.can_delegate(source_agent_id, target_agent_id)

    if authorized:
        return

    # Build actionable error message
    if available_targets is None:
        links = await delegation_svc.get_targets(source_agent_id)
        available_targets = [
            link.target_agent.agent_name
            for link in links
            if link.target_agent is not None
        ]

    if available_targets:
        targets_str = ", ".join(available_targets)
        msg = (
            f"Delegation denied: agent is not authorized to delegate to the target. "
            f"Available targets: {targets_str}."
        )
    else:
        msg = (
            "Delegation denied: agent has no delegation targets configured. "
            "Contact your team admin to set up delegation links."
        )

    logger.warning(
        "blocked_unauthorized_delegation: source=%s target=%s",
        source_agent_id,
        target_agent_id,
    )
    raise DelegationDenied(msg)
