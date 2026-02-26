"""
=========================================================================
Agent Team Configuration — Model Routing Defaults & SE4H Constraints
SDLC Orchestrator - Sprint 177 (12-Role SASE Expansion)

Version: 1.0.0
Date: February 2026
Status: ACTIVE - Sprint 177
Authority: CTO Approved (ADR-056 §12.5)
Reference: ADR-056-Multi-Agent-Team-Engine.md, SASE arXiv:2509.06216v2

Purpose:
- Default model assignments per SDLC role (ROLE_MODEL_DEFAULTS)
- SE4H behavioral constraints enforcement
- Role type derivation constants

Model Routing Rationale (ADR-056 §12.5.6):
  SE4A roles: Ollama primary ($50/mo) — researcher/pm → qwen3:32b,
    architect/reviewer → deepseek-r1:32b, coder/tester → qwen3-coder:30b,
    pjm/devops → qwen3:14b
  SE4H roles: Cloud providers for best reasoning quality —
    ceo/cto → claude-opus-4-6, cpo → claude-sonnet-4-5
  Router role: Fast local model — assistant → qwen3:14b

Zero Mock Policy: Production-ready configuration constants
=========================================================================
"""

from __future__ import annotations

import os

from app.schemas.agent_team import SDLCRole, SE4H_ROLES
from app.services.agent_team.query_classifier import ClassificationRule

# =========================================================================
# Default Model Routing Table (per ADR-056 §12.5.6)
# =========================================================================

ROLE_MODEL_DEFAULTS: dict[str, dict[str, str]] = {
    # SE4A — autonomous AI agents (Ollama primary, $50/mo)
    "researcher": {"provider": "ollama", "model": "qwen3:32b"},
    "pm": {"provider": "ollama", "model": "qwen3:32b"},
    "pjm": {"provider": "ollama", "model": "qwen3:14b"},
    "architect": {"provider": "ollama", "model": "deepseek-r1:32b"},
    "coder": {"provider": "ollama", "model": "qwen3-coder:30b"},
    "reviewer": {"provider": "ollama", "model": "deepseek-r1:32b"},
    "tester": {"provider": "ollama", "model": "qwen3-coder:30b"},
    "devops": {"provider": "ollama", "model": "qwen3:14b"},
    # SE4H — Agent Coaches (Cloud for best reasoning quality)
    "ceo": {"provider": "anthropic", "model": "claude-opus-4-6"},
    "cpo": {"provider": "anthropic", "model": "claude-sonnet-4-5"},
    "cto": {"provider": "anthropic", "model": "claude-opus-4-6"},
    # Router — fast local model
    "assistant": {"provider": "ollama", "model": "qwen3:14b"},
}


# =========================================================================
# SE4H Behavioral Constraints (ADR-056 §12.5.4)
# =========================================================================

SE4H_CONSTRAINTS: dict[str, object] = {
    "max_delegation_depth": 0,       # Cannot spawn sub-agents
    "can_spawn_subagent": False,     # Explicit: no agent spawning
    "allowed_tools": ["read_file", "search", "analyze"],  # Read-only tools
    "denied_tools": [
        "write_file",
        "execute_command",
        "spawn_agent",
        "send_message",
        "approve_gate",
    ],
}


# =========================================================================
# Query Classification Rules (ADR-058 Pattern E, Sprint 179)
# =========================================================================
# Rules are evaluated highest-priority first by query_classifier.classify().
# First matching rule returns its hint → MODEL_ROUTE_HINTS[hint] selects model.
# If no rule matches, caller uses ROLE_MODEL_DEFAULTS unchanged.

DEFAULT_CLASSIFICATION_RULES: list[ClassificationRule] = [
    ClassificationRule(
        hint="code",
        priority=10,
        keywords=(),             # Any message is eligible; code block presence is the signal
        patterns=("```",),       # Presence of a code block → code task
        min_length=0,
        max_length=0,
    ),
    # Sprint 204 (AD-4): Governance rules at priority=8.
    # Each keyword is a SEPARATE rule so that a single match fires (AND logic
    # requires ALL keywords in a rule to be present — single-keyword rules
    # ensure any one governance keyword is sufficient).
    # max_length=200 prevents false positives on long messages that happen
    # to mention "gate" in a different context.
    ClassificationRule(
        hint="governance",
        priority=8,
        keywords=("approve",),
        patterns=(),
        min_length=0,
        max_length=200,
    ),
    ClassificationRule(
        hint="governance",
        priority=8,
        keywords=("gate",),
        patterns=(),
        min_length=0,
        max_length=200,
    ),
    ClassificationRule(
        hint="governance",
        priority=8,
        keywords=("submit evidence",),
        patterns=(),
        min_length=0,
        max_length=0,
    ),
    ClassificationRule(
        hint="governance",
        priority=8,
        keywords=("export audit",),
        patterns=(),
        min_length=0,
        max_length=0,
    ),
    ClassificationRule(
        hint="governance",
        priority=8,
        keywords=("close sprint",),
        patterns=(),
        min_length=0,
        max_length=0,
    ),
    ClassificationRule(
        hint="reasoning",
        priority=5,
        keywords=("explain", "analyze", "why", "compare", "trade-off", "design"),
        patterns=(),
        min_length=50,           # Non-trivial question length
        max_length=0,
    ),
    ClassificationRule(
        hint="fast",
        priority=1,
        keywords=(),
        patterns=(),
        min_length=0,
        max_length=20,           # Very short messages: "ok", "yes", "done", "thanks"
    ),
]

# =========================================================================
# Model Route Hints — maps hint → (provider, model) override
# =========================================================================
# Used by team_orchestrator._build_invoker() to override primary model when
# query classification fires.  If a role-specific override is desired, add
# the role as an inner key.  The default key ("*") is the fallback.
#
# Structure: {"hint": {"*": (provider, model), "coder": (provider, model), ...}}

MODEL_ROUTE_HINTS: dict[str, dict[str, tuple[str, str]]] = {
    "code": {
        "*": ("ollama", "qwen3-coder:30b"),
    },
    "reasoning": {
        "*": ("ollama", "deepseek-r1:32b"),
    },
    "fast": {
        "*": ("ollama", "qwen3:8b"),
    },
}


def get_model_defaults(role: SDLCRole) -> dict[str, str]:
    """Return default provider/model for a given SDLC role.

    Args:
        role: SDLCRole enum value.

    Returns:
        Dict with 'provider' and 'model' keys.

    Raises:
        KeyError: If role value not in ROLE_MODEL_DEFAULTS (should not happen
        if SDLCRole enum and ROLE_MODEL_DEFAULTS stay in sync).
    """
    return ROLE_MODEL_DEFAULTS[role.value]


def is_se4h_role(role: SDLCRole) -> bool:
    """Check if a role is an SE4H (Agent Coach) role."""
    return role in SE4H_ROLES


def get_se4h_overrides() -> dict[str, object]:
    """Return SE4H behavioral constraint overrides for AgentDefinitionCreate.

    When creating an agent with an SE4H role, these values should be
    enforced regardless of what the caller provides.
    """
    return dict(SE4H_CONSTRAINTS)


# =========================================================================
# LangChain Provider Settings (Sprint 205, ADR-066)
# =========================================================================
# Feature flag: set LANGCHAIN_ENABLED=true in env to activate the LangChain
# provider branch in AgentInvoker._call_provider().
# When false (default): provider="langchain" raises AgentInvokerError.
# LANGCHAIN_DEFAULT_MODEL controls which Ollama model is used when no explicit
# model is specified in a LangChain ProviderConfig.

LANGCHAIN_ENABLED: bool = os.environ.get("LANGCHAIN_ENABLED", "false").lower() == "true"

LANGCHAIN_DEFAULT_MODEL: str = os.environ.get(
    "LANGCHAIN_DEFAULT_MODEL", "qwen3-coder:30b"
)

# =========================================================================
# LangGraph Workflow Settings (Sprint 206, ADR-066 Phase 2)
# =========================================================================
# Feature flag: set LANGGRAPH_ENABLED=true in env to activate LangGraph
# durable reflection workflows in the WorkflowResumer service.
# When false (default): WorkflowResumer raises an error if started.
# WORKFLOW_RESUMER_RECONCILER_INTERVAL_SECONDS: polling interval (default 30s)
# WORKFLOW_STUCK_THRESHOLD_MINUTES: auto-resume stuck workflows (default 5min)

LANGGRAPH_ENABLED: bool = os.environ.get("LANGGRAPH_ENABLED", "false").lower() == "true"

WORKFLOW_RESUMER_RECONCILER_INTERVAL_SECONDS: int = int(
    os.environ.get("WORKFLOW_RESUMER_RECONCILER_INTERVAL_SECONDS", "30")
)

WORKFLOW_STUCK_THRESHOLD_MINUTES: int = int(
    os.environ.get("WORKFLOW_STUCK_THRESHOLD_MINUTES", "5")
)
