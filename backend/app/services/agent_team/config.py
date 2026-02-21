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
