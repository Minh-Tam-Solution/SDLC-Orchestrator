"""
Chat Command Router — LLM Function Calling for Governance Loop.

Sprint 189 (ADR-064 T-01, T-02, D-064-02, D-064-03, FR-046).
Sprint 191: Refactored to use Unified Command Registry (command_registry.py).

Routes chat messages through LLM Function Calling with a bounded tool
allowlist (5 tools) and Pydantic v2 validation. This is the core of the
Chat-First Governance Loop:

    @mention → chat_command_router → compute_gate_actions() → execute/Magic Link

Design decisions:
    - D-064-02: LLM Function Calling, NOT regex parsing
    - D-064-03: Actions Contract — ALWAYS call compute_gate_actions() before mutations
    - T-01: Bounded allowlist (5 tools) + Pydantic validation, max 2 retries
    - T-02: Native Ollama /api/chat tools parameter (NOT LangChain)
    - T-08: run_in_threadpool for sync OllamaService.chat() (uses requests.post)
    - T-09: run_in_threadpool for sync ProjectService.create_project() (uses sync Session)

Sync/Async awareness:
    SYNC  (wrap with run_in_threadpool): ollama_service.chat(), project_service.create_project()
    ASYNC (direct await):                gate_service.compute_gate_actions(), audit_service.log()
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from typing import Any, Optional

from pydantic import ValidationError
from starlette.concurrency import run_in_threadpool

from app.core.config import settings
from app.services.agent_team.command_registry import (
    ToolName,
    to_ollama_tools,
    to_tool_schemas,
)
from app.services.ollama_service import OllamaError, get_ollama_service

logger = logging.getLogger(__name__)

# Maximum retry attempts for LLM tool call validation (T-01)
MAX_RETRIES = 2  # 3 total attempts (1 initial + 2 retries)

# Message length guard — prevent oversized input from reaching LLM (P1-1)
MAX_MESSAGE_LENGTH = 4096

# Chat model fallback — matches OllamaModel.DEFAULT in ollama_service.py
_CHAT_MODEL_FALLBACK: str = "qwen3:32b"


# ============================================================================
# Tool Registry — from Unified Command Registry (Sprint 191)
# ============================================================================

# Generated from command_registry.py — single source of truth for CLI + OTT
_TOOL_SCHEMAS = to_tool_schemas()
OLLAMA_TOOLS = to_ollama_tools()

# System prompt for the governance chat router
_SYSTEM_PROMPT = """You are a governance assistant for SDLC Orchestrator. You help users manage quality gates, evidence, and project approvals.

You understand Vietnamese and English. When users mention gate actions, project creation, evidence submission, or audit exports, use the appropriate tool.

Available commands:
- Create project: "tạo dự án X", "create project X"
- Gate status: "trạng thái gate", "gate status for project 5"
- Submit evidence: "nộp bằng chứng", "upload evidence for gate X"
- Approve/reject: "duyệt gate", "approve G2", "reject gate X"
- Export audit: "xuất báo cáo", "export audit for project X"

IMPORTANT: Always use the provided tools. Never fabricate gate IDs or project IDs. If you don't have enough information, ask the user to clarify."""


# ============================================================================
# Chat Command Router
# ============================================================================


@dataclass
class ChatCommandResult:
    """Result of processing a chat command."""

    tool_name: Optional[str] = None
    tool_args: Optional[dict[str, Any]] = field(default=None)
    response_text: str = ""
    requires_magic_link: bool = False
    magic_link_url: Optional[str] = None
    error: Optional[str] = None

    @property
    def is_tool_call(self) -> bool:
        return self.tool_name is not None

    @property
    def is_error(self) -> bool:
        return self.error is not None


async def route_chat_command(
    message: str,
    user_id: str,
    conversation_history: Optional[list[dict[str, str]]] = None,
) -> ChatCommandResult:
    """
    Route a chat message through LLM Function Calling.

    This is the main entry point for the chat governance loop. It:
    1. Sends the message to Ollama /api/chat with the bounded tool allowlist
    2. Validates the LLM's tool call against Pydantic schemas
    3. Returns the validated tool call for execution by the caller

    The caller (ott_gateway or team_orchestrator) is responsible for:
    - Checking compute_gate_actions() before mutations (D-064-03)
    - Generating Magic Links for requires_oob_auth gates
    - Executing the actual tool action
    - Logging to audit_service with source="chat"

    Args:
        message: User's chat message text
        user_id: Authenticated user ID (from OTT identity)
        conversation_history: Previous messages for context (optional)

    Returns:
        ChatCommandResult with either:
        - tool_name + tool_args: Validated tool call ready for execution
        - response_text: Text response (no tool call, e.g., clarification)
        - error: Error message if all retries failed
    """
    # P1-1: Message length guard — reject oversized input before LLM call
    if len(message) > MAX_MESSAGE_LENGTH:
        return ChatCommandResult(
            error=f"Message too long ({len(message)} chars). Maximum: {MAX_MESSAGE_LENGTH}.",
        )

    ollama = get_ollama_service()

    # Build messages array for /api/chat
    messages: list[dict[str, str]] = [
        {"role": "system", "content": _SYSTEM_PROMPT},
    ]

    if conversation_history:
        messages.extend(conversation_history)

    messages.append({"role": "user", "content": message})

    # Use the configured chat model (qwen3:32b for Vietnamese support)
    model = getattr(settings, "OLLAMA_MODEL", None) or _CHAT_MODEL_FALLBACK

    for attempt in range(1, MAX_RETRIES + 2):  # 1 initial + MAX_RETRIES retries
        try:
            # T-08: ollama_service.chat() is SYNC — wrap with run_in_threadpool
            response = await run_in_threadpool(
                ollama.chat,
                messages=messages,
                model=model,
                tools=OLLAMA_TOOLS,
                temperature=0.3,
            )
        except OllamaError as exc:
            logger.error(
                "chat_router: ollama error attempt=%d/%d error=%s",
                attempt,
                MAX_RETRIES + 1,
                exc,
            )
            if attempt > MAX_RETRIES:
                return ChatCommandResult(
                    error=f"AI service unavailable after {attempt} attempts. Please try again later.",
                )
            continue

        # Extract response content
        msg = response.get("message", {})
        content = msg.get("content", "")
        tool_calls = msg.get("tool_calls", [])

        # No tool call — return text response
        if not tool_calls:
            return ChatCommandResult(response_text=content or "I didn't understand that command. Try: create project, gate status, approve gate, submit evidence, or export audit.")

        # Process first tool call; warn if LLM returned multiple
        if len(tool_calls) > 1:
            logger.warning(
                "chat_router: LLM returned %d tool_calls, processing only first",
                len(tool_calls),
            )
        tool_call = tool_calls[0]
        fn = tool_call.get("function", {})
        fn_name = fn.get("name", "")
        fn_args = fn.get("arguments", {})

        # T-01: Bounded allowlist check — reject unknown tools
        if fn_name not in _TOOL_SCHEMAS:
            valid_tools = ", ".join(t.value for t in ToolName)
            logger.warning(
                "chat_router: rejected unknown tool=%s (allowlist: %s)",
                fn_name,
                valid_tools,
            )

            if attempt > MAX_RETRIES:
                return ChatCommandResult(
                    error=f"I don't recognize the command '{fn_name}'. Available commands: {valid_tools}",
                )

            # Retry with correction message
            messages.append({"role": "assistant", "content": content or ""})
            messages.append({
                "role": "user",
                "content": f"Error: '{fn_name}' is not a valid tool. Valid tools are: {valid_tools}. Please try again with the correct tool.",
            })
            continue

        # T-01: Pydantic v2 validation
        schema_cls = _TOOL_SCHEMAS[fn_name]
        try:
            validated = schema_cls.model_validate(fn_args)
            validated_args = validated.model_dump(exclude_none=True)
        except ValidationError as exc:
            logger.warning(
                "chat_router: pydantic validation failed tool=%s attempt=%d/%d errors=%s",
                fn_name,
                attempt,
                MAX_RETRIES + 1,
                exc.errors(),
            )

            if attempt > MAX_RETRIES:
                return ChatCommandResult(
                    error=f"Invalid parameters for {fn_name}. Please provide the required information and try again.",
                )

            # Retry with validation error feedback
            error_details = "; ".join(
                f"{e['loc']}: {e['msg']}" for e in exc.errors()
            )
            messages.append({"role": "assistant", "content": content or ""})
            messages.append({
                "role": "user",
                "content": f"Error: Parameter validation failed for {fn_name}: {error_details}. Please fix and try again.",
            })
            continue

        # Successful tool call — return validated result
        logger.info(
            "chat_router: tool_call=%s args=%s user=%s attempt=%d",
            fn_name,
            json.dumps(validated_args, default=str),
            user_id,
            attempt,
        )

        return ChatCommandResult(
            tool_name=fn_name,
            tool_args=validated_args,
            response_text=content,
        )

    # Should not reach here, but safety net
    return ChatCommandResult(
        error="Failed to process command after maximum retries.",
    )
