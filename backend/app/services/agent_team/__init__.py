"""
Multi-Agent Team Engine — Strategic Upgrade from TinyClaw + OpenClaw + Nanobot.

ADR-056: 14 non-negotiable conditions, 4 locked decisions, 3 codebase patterns.
Sprint 176-178 implementation.
"""

from app.services.agent_team.conversation_limits import ConversationLimits, LimitViolation
from app.services.agent_team.failover_classifier import (
    FailoverClassifier,
    FailoverAction,
    FailoverReason,
    ProviderProfileKey,
)
from app.services.agent_team.input_sanitizer import InputSanitizer
from app.services.agent_team.shell_guard import ShellGuard
from app.services.agent_team.tool_context import ToolContext, AgentToolPermissions
from app.services.agent_team.reflect_step import ReflectStep
from app.services.agent_team.config import (
    ROLE_MODEL_DEFAULTS,
    SE4H_CONSTRAINTS,
    get_model_defaults,
    is_se4h_role,
    get_se4h_overrides,
)
from app.services.agent_team.agent_registry import (
    AgentRegistry,
    AgentRegistryError,
    AgentNotFoundError,
    AgentDuplicateError,
    AgentInactiveError,
)
from app.services.agent_team.mention_parser import MentionParser, MentionRouteResult
from app.services.agent_team.message_queue import MessageQueue, MessageQueueError
from app.services.agent_team.conversation_tracker import (
    ConversationTracker,
    ConversationError,
    ConversationNotFoundError,
    ConversationInactiveError,
    LimitExceededError,
    DelegationDepthError,
)
from app.services.agent_team.agent_invoker import (
    AgentInvoker,
    InvocationResult,
    ProviderConfig,
    AllProvidersFailedError,
)
from app.services.agent_team.team_orchestrator import (
    TeamOrchestrator,
    TeamOrchestratorError,
    ProcessingResult,
)
from app.services.agent_team.evidence_collector import (
    EvidenceCollector,
    EvidenceCollectorError,
)

# Sprint 179 — ZeroClaw Security Hardening (ADR-058)
from app.services.agent_team.output_scrubber import OutputScrubber
from app.services.agent_team.history_compactor import HistoryCompactor
from app.services.agent_team.query_classifier import classify, ClassificationRule
from app.services.agent_team.config import DEFAULT_CLASSIFICATION_RULES, MODEL_ROUTE_HINTS

__all__ = [
    # Sprint 176 — Design Contracts
    "ConversationLimits",
    "LimitViolation",
    "FailoverClassifier",
    "FailoverAction",
    "FailoverReason",
    "ProviderProfileKey",
    "InputSanitizer",
    "ShellGuard",
    "ToolContext",
    "AgentToolPermissions",
    "ReflectStep",
    # Sprint 177 — Config
    "ROLE_MODEL_DEFAULTS",
    "SE4H_CONSTRAINTS",
    "get_model_defaults",
    "is_se4h_role",
    "get_se4h_overrides",
    # Sprint 177 — Core Services
    "AgentRegistry",
    "AgentRegistryError",
    "AgentNotFoundError",
    "AgentDuplicateError",
    "AgentInactiveError",
    "MentionParser",
    "MentionRouteResult",
    "MessageQueue",
    "MessageQueueError",
    "ConversationTracker",
    "ConversationError",
    "ConversationNotFoundError",
    "ConversationInactiveError",
    "LimitExceededError",
    "DelegationDepthError",
    "AgentInvoker",
    "InvocationResult",
    "ProviderConfig",
    "AllProvidersFailedError",
    # Sprint 178 — Orchestrator + Evidence
    "TeamOrchestrator",
    "TeamOrchestratorError",
    "ProcessingResult",
    "EvidenceCollector",
    "EvidenceCollectorError",
    # Sprint 179 — ZeroClaw Security Hardening (ADR-058)
    "OutputScrubber",
    "HistoryCompactor",
    "classify",
    "ClassificationRule",
    "DEFAULT_CLASSIFICATION_RULES",
    "MODEL_ROUTE_HINTS",
]
