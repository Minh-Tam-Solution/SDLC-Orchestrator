"""
=========================================================================
Agent Team Schemas - P0 API Contracts for Multi-Agent Team Engine
SDLC Orchestrator - Sprint 176-177 (Multi-Agent Foundation)

Version: 1.0.0
Date: February 2026
Status: PROPOSED - Sprint 176 Design
Authority: CTO Approved (ADR-056)
Reference: ADR-056-Multi-Agent-Team-Engine.md

Purpose:
- P0 API request/response validation for 5 endpoints
- Snapshot Precedence: AgentDefinitionCreate vs ConversationSnapshot
- CTO-corrected field values (queue_mode P0=3, session_scope P0=2, failover_reason=6)
- Dead-letter fields, dedupe_key, provider_profile_key
- Tool permission schemas (Nanobot N2)

4 Locked Decisions Applied:
  1. Snapshot Precedence — definition fields snapshot into conversation
  2. Lane Contract — processing_lane, processing_status, dead-letter fields
  3. Provider Profile Key — {provider}:{account}:{region}:{model_family}
  4. Canonical Protocol Owner — Orchestrator defines all message schemas

14 Non-Negotiables Enforced:
  Security: least-privilege, identity, OTT approval, sanitizer, shell guard, tool restriction
  Architecture: lane queue, workspace, loop guards, snapshot, protocol owner
  Observability: masquerading audit, budget breaker, human interrupt

Zero Mock Policy: Production-ready Pydantic v2 models
=========================================================================
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator


# =========================================================================
# Enums (CTO-verified values)
# =========================================================================


class SDLCRole(str, Enum):
    """SDLC role templates from TinyClaw (6 roles)."""

    PM = "pm"
    ARCHITECT = "architect"
    CODER = "coder"
    REVIEWER = "reviewer"
    TESTER = "tester"
    DEVOPS = "devops"


class QueueMode(str, Enum):
    """
    Message queue modes. P0 implements 3 of 7.
    CTO correction: OpenClaw has 7 modes total, not 5.
    """

    # P0 modes
    QUEUE = "queue"          # FIFO queue (default)
    STEER = "steer"          # Immediate steering of current agent
    INTERRUPT = "interrupt"  # Interrupt current agent execution
    # P1+ modes (validated but not processed in P0)
    FOLLOWUP = "followup"
    COLLECT = "collect"
    STEER_BACKLOG = "steer-backlog"
    STEER_PLUS_BACKLOG = "steer+backlog"


P0_QUEUE_MODES = {QueueMode.QUEUE, QueueMode.STEER, QueueMode.INTERRUPT}


class SessionScope(str, Enum):
    """
    Session scoping strategies. P0 implements 2.
    CTO correction: OpenClaw source has only 2 explicit types, not 4.
    """

    PER_SENDER = "per-sender"  # Each user gets isolated session (default)
    GLOBAL = "global"          # Single session across all channels


class ConversationStatus(str, Enum):
    """Conversation lifecycle states."""

    ACTIVE = "active"
    COMPLETED = "completed"
    MAX_REACHED = "max_reached"
    PAUSED_BY_HUMAN = "paused_by_human"
    ERROR = "error"


class ProcessingStatus(str, Enum):
    """Message processing states (Lane Contract)."""

    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    DEAD_LETTER = "dead_letter"


class MessageType(str, Enum):
    """Message types in agent conversations."""

    REQUEST = "request"
    RESPONSE = "response"
    MENTION = "mention"
    SYSTEM = "system"
    INTERRUPT = "interrupt"


class SenderType(str, Enum):
    """Who sent the message."""

    USER = "user"
    AGENT = "agent"
    SYSTEM = "system"


class InitiatorType(str, Enum):
    """What initiated the conversation."""

    USER = "user"
    AGENT = "agent"
    GATE_EVENT = "gate_event"
    OTT_CHANNEL = "ott_channel"


class FailoverReasonEnum(str, Enum):
    """
    6 classified error reasons (CTO-verified, includes 'unknown').
    Maps to Abort Matrix in ADR-056 Decision 3.
    """

    AUTH = "auth"
    FORMAT = "format"
    RATE_LIMIT = "rate_limit"
    BILLING = "billing"
    TIMEOUT = "timeout"
    UNKNOWN = "unknown"


class ChannelType(str, Enum):
    """Communication channels."""

    WEB = "web"
    CLI = "cli"
    EXTENSION = "extension"
    TELEGRAM = "telegram"
    DISCORD = "discord"
    WHATSAPP = "whatsapp"
    ZALO = "zalo"


# =========================================================================
# Agent Definition Schemas
# =========================================================================


class AgentDefinitionCreate(BaseModel):
    """
    Create an agent definition (template/defaults).
    Snapshot Precedence: These values become defaults for new conversations.
    """

    model_config = ConfigDict(from_attributes=True)

    project_id: UUID
    team_id: UUID | None = None
    agent_name: str = Field(..., min_length=1, max_length=50)
    sdlc_role: SDLCRole
    provider: str = Field(..., min_length=1, max_length=20)
    model: str = Field(..., min_length=1, max_length=100)
    system_prompt: str | None = None
    working_directory: str | None = Field(None, max_length=500)
    max_tokens: int = Field(default=4096, ge=1, le=1_000_000)
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    queue_mode: QueueMode = QueueMode.QUEUE
    session_scope: SessionScope = SessionScope.PER_SENDER
    max_delegation_depth: int = Field(default=1, ge=0, le=10)
    # Tool permissions (Nanobot N2 — Non-Negotiable #6)
    allowed_tools: list[str] = Field(default=["*"])
    denied_tools: list[str] = Field(default=[])
    can_spawn_subagent: bool = False
    allowed_paths: list[str] = Field(default=[])
    # Reflect step (Nanobot)
    reflect_frequency: int = Field(default=1, ge=0, le=100)
    config: dict[str, Any] = Field(default_factory=dict)

    @field_validator("queue_mode")
    @classmethod
    def validate_p0_queue_mode(cls, v: QueueMode) -> QueueMode:
        """Warn if using P1+ queue mode (accepted but not processed in P0)."""
        if v not in P0_QUEUE_MODES:
            import logging

            logging.getLogger(__name__).warning(
                "Queue mode '%s' is P1+, will be treated as 'queue' in P0", v.value
            )
        return v


class AgentDefinitionUpdate(BaseModel):
    """Partial update for agent definition."""

    model_config = ConfigDict(from_attributes=True)

    agent_name: str | None = Field(None, min_length=1, max_length=50)
    sdlc_role: SDLCRole | None = None
    provider: str | None = Field(None, min_length=1, max_length=20)
    model: str | None = Field(None, min_length=1, max_length=100)
    system_prompt: str | None = None
    working_directory: str | None = Field(None, max_length=500)
    max_tokens: int | None = Field(None, ge=1, le=1_000_000)
    temperature: float | None = Field(None, ge=0.0, le=2.0)
    queue_mode: QueueMode | None = None
    session_scope: SessionScope | None = None
    max_delegation_depth: int | None = Field(None, ge=0, le=10)
    allowed_tools: list[str] | None = None
    denied_tools: list[str] | None = None
    can_spawn_subagent: bool | None = None
    allowed_paths: list[str] | None = None
    reflect_frequency: int | None = Field(None, ge=0, le=100)
    is_active: bool | None = None
    config: dict[str, Any] | None = None


class AgentDefinitionResponse(BaseModel):
    """Full agent definition response."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    project_id: UUID
    team_id: UUID | None
    agent_name: str
    sdlc_role: SDLCRole
    provider: str
    model: str
    system_prompt: str | None
    working_directory: str | None
    max_tokens: int
    temperature: float
    queue_mode: QueueMode
    session_scope: SessionScope
    max_delegation_depth: int
    allowed_tools: list[str]
    denied_tools: list[str]
    can_spawn_subagent: bool
    allowed_paths: list[str]
    reflect_frequency: int
    is_active: bool
    config: dict[str, Any]
    created_at: datetime
    updated_at: datetime


# =========================================================================
# Conversation Schemas (Snapshot Precedence applied)
# =========================================================================


class ConversationCreate(BaseModel):
    """
    Start a new agent conversation.
    Snapshot Precedence: max_messages, max_budget_cents, queue_mode, session_scope
    are snapshotted from agent_definitions into agent_conversations.
    """

    model_config = ConfigDict(from_attributes=True)

    agent_definition_id: UUID
    project_id: UUID
    parent_conversation_id: UUID | None = None
    initiator_type: InitiatorType
    initiator_id: str = Field(..., min_length=1, max_length=100)
    channel: ChannelType
    metadata: dict[str, Any] = Field(default_factory=dict)


class ConversationResponse(BaseModel):
    """Full conversation response with snapshotted fields."""

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: UUID
    project_id: UUID
    agent_definition_id: UUID
    parent_conversation_id: UUID | None
    delegation_depth: int
    initiator_type: InitiatorType
    initiator_id: str
    channel: ChannelType
    session_scope: SessionScope      # Snapshotted from definition
    queue_mode: QueueMode              # Snapshotted from definition
    status: ConversationStatus
    total_messages: int
    max_messages: int                # Snapshotted from definition
    branch_count: int
    # Token budget (OpenClaw)
    input_tokens: int
    output_tokens: int
    total_tokens: int
    current_cost_cents: int
    max_budget_cents: int            # Snapshotted from definition
    metadata: dict[str, Any] = Field(default_factory=dict, validation_alias="metadata_")
    started_at: datetime
    completed_at: datetime | None


# =========================================================================
# Message Schemas (Lane Contract + Dead-Letter)
# =========================================================================


class MessageSend(BaseModel):
    """Send a message to an agent conversation."""

    model_config = ConfigDict(from_attributes=True)

    conversation_id: UUID
    content: str = Field(..., min_length=1)
    sender_type: SenderType
    sender_id: str = Field(..., min_length=1, max_length=100)
    recipient_id: str | None = Field(None, max_length=100)
    message_type: MessageType = MessageType.REQUEST
    mentions: list[str] = Field(default=[])
    dedupe_key: str | None = Field(None, max_length=100)

    @field_validator("mentions")
    @classmethod
    def validate_mentions(cls, v: list[str]) -> list[str]:
        """Ensure mentions are valid agent name format."""
        for mention in v:
            if not mention.strip():
                raise ValueError("Empty mention not allowed")
        return v


class MessageResponse(BaseModel):
    """Full message response with lane and dead-letter fields."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    conversation_id: UUID
    parent_message_id: UUID | None
    sender_type: SenderType
    sender_id: str
    recipient_id: str | None
    content: str
    mentions: list[str]
    message_type: MessageType
    queue_mode: QueueMode
    processing_status: ProcessingStatus
    processing_lane: str
    dedupe_key: str | None
    correlation_id: UUID
    token_count: int | None
    latency_ms: int | None
    provider_used: str | None
    failover_reason: FailoverReasonEnum | None
    # Dead-letter fields (Lane Contract — ADR-056 Decision 2)
    failed_count: int
    last_error: str | None
    next_retry_at: datetime | None
    evidence_id: UUID | None
    created_at: datetime


# =========================================================================
# Pagination & List Schemas
# =========================================================================


class PaginatedResponse(BaseModel):
    """Generic paginated response wrapper."""

    total: int
    page: int = 1
    page_size: int = 20
    has_more: bool = False


class AgentDefinitionListResponse(PaginatedResponse):
    """Paginated list of agent definitions."""

    items: list[AgentDefinitionResponse]


class ConversationListResponse(PaginatedResponse):
    """Paginated list of conversations."""

    items: list[ConversationResponse]


class MessageListResponse(PaginatedResponse):
    """Paginated list of messages."""

    items: list[MessageResponse]


# =========================================================================
# Provider Profile Key Schema
# =========================================================================


class ProviderProfileKeySchema(BaseModel):
    """Provider Profile Key: {provider}:{account}:{region}:{model_family}."""

    provider: str
    account: str
    region: str
    model_family: str

    @property
    def key(self) -> str:
        return f"{self.provider}:{self.account}:{self.region}:{self.model_family}"

    @classmethod
    def from_key_string(cls, key_str: str) -> ProviderProfileKeySchema:
        parts = key_str.split(":")
        if len(parts) != 4:
            raise ValueError(
                f"Invalid provider profile key: {key_str!r}. "
                f"Expected format: provider:account:region:model_family"
            )
        return cls(provider=parts[0], account=parts[1], region=parts[2], model_family=parts[3])


# =========================================================================
# Interrupt Schema (Non-Negotiable #14)
# =========================================================================


class ConversationInterrupt(BaseModel):
    """Human-in-the-loop interrupt request."""

    reason: str = Field(..., min_length=1, max_length=500)
    interrupted_by: str = Field(..., min_length=1, max_length=100)
