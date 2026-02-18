"""
=========================================================================
Agent Definition Model - Multi-Agent Team Engine (ADR-056)
SDLC Orchestrator - Sprint 176 (Multi-Agent Foundation)

Version: 1.0.0
Date: 2026-02-18
Status: ACTIVE - Sprint 176
Authority: CTO Approved (ADR-056, EP-07)
Reference: ADR-056-Multi-Agent-Team-Engine.md

Purpose:
- Agent configuration templates with SDLC role assignments
- Snapshot Precedence source: definition fields become defaults for conversations
- Tool permissions and workspace restrictions (Nanobot N2)
- Provider and model configuration per agent

4 Locked Decisions Applied:
  1. Snapshot Precedence — definition fields snapshot into conversation on creation
  3. Provider Profile Key — {provider}:{account}:{region}:{model_family}
  4. Canonical Protocol Owner — Orchestrator defines all agent schemas

14 Non-Negotiables:
  #1: Least-privilege scopes via allowed_tools/denied_tools
  #5: Shell command guard via max_delegation_depth
  #6: Tool-level workspace restriction via allowed_paths, can_spawn_subagent
  #9: Loop guards via max_tokens default

Zero Mock Policy: Production-ready SQLAlchemy 2.0 model
=========================================================================
"""

from datetime import datetime
from typing import TYPE_CHECKING, Optional
from uuid import uuid4

from sqlalchemy import Boolean, Float, Integer, String, Text, ForeignKey, DateTime
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base_class import Base

if TYPE_CHECKING:
    from app.models.project import Project
    from app.models.team import Team
    from app.models.agent_conversation import AgentConversation


class AgentDefinition(Base):
    """
    Agent definition — configuration template for AI agents in Multi-Agent Team Engine.

    Each definition describes an agent's role, provider, model, and behavioral constraints.
    When a conversation starts, relevant fields are snapshotted into the conversation record
    (Snapshot Precedence — ADR-056 Decision 1).

    Fields are divided into:
    - Identity: name, SDLC role, project/team binding
    - Provider: AI provider, model, temperature, max_tokens
    - Queue: queue_mode (3 P0 modes), session_scope (2 P0 modes)
    - Safety: delegation depth, tool permissions, workspace restriction
    - Config: extensible JSONB for future features
    """

    __tablename__ = "agent_definitions"

    # ── Primary Key ──────────────────────────────────────────────────────
    id: Mapped[uuid4] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
        doc="Unique identifier for the agent definition",
    )

    # ── Foreign Keys ─────────────────────────────────────────────────────
    project_id: Mapped[uuid4] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        doc="Project this agent belongs to",
    )

    team_id: Mapped[Optional[uuid4]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("teams.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        doc="Optional team assignment (CTO Finding #2: dual-registration with team_members)",
    )

    # ── Identity ─────────────────────────────────────────────────────────
    agent_name: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        doc="Display name (e.g., 'initializer', 'coder-alpha')",
    )

    sdlc_role: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        doc="SDLC role: pm, architect, coder, reviewer, tester, devops",
    )

    # ── Provider Configuration ───────────────────────────────────────────
    provider: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        doc="AI provider: ollama, anthropic, openai",
    )

    model: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        doc="Model identifier (e.g., 'qwen3-coder:30b', 'claude-sonnet-4-5')",
    )

    system_prompt: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        doc="System prompt template for this agent role",
    )

    working_directory: Mapped[Optional[str]] = mapped_column(
        String(500),
        nullable=True,
        doc="Agent working directory (workspace restriction base path)",
    )

    max_tokens: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=4096,
        doc="Max tokens per invocation (Non-Negotiable #9: loop guard)",
    )

    temperature: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        default=0.7,
        doc="LLM temperature (0.0-2.0)",
    )

    # ── Queue Configuration (CTO-corrected: P0 = 3 of 7 modes) ──────────
    queue_mode: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="queue",
        doc="Queue mode: queue (default), steer, interrupt (P0 = 3 of 7)",
    )

    session_scope: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="per-sender",
        doc="Session scoping: per-sender (default), global (P0 = 2)",
    )

    # ── Safety Controls (Nanobot N2) ─────────────────────────────────────
    max_delegation_depth: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=1,
        doc="Max depth in delegation chain (0=no spawn). Prevents infinite agent chains.",
    )

    allowed_tools: Mapped[dict] = mapped_column(
        JSONB,
        nullable=False,
        default=lambda: ["*"],
        doc='Whitelist: ["*"] = all tools, ["read_file","write_file"] = restricted',
    )

    denied_tools: Mapped[dict] = mapped_column(
        JSONB,
        nullable=False,
        default=list,
        doc='Blacklist: ["spawn_agent","send_message"] for subagents',
    )

    can_spawn_subagent: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        doc="Explicit spawn permission (false for subagents, Non-Negotiable #6)",
    )

    allowed_paths: Mapped[dict] = mapped_column(
        JSONB,
        nullable=False,
        default=list,
        doc='Workspace restriction: ["/project/src/", "/project/tests/"]',
    )

    # ── Reflect Step (Nanobot) ───────────────────────────────────────────
    reflect_frequency: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=1,
        doc="Reflect after every N tool calls (0=disabled, 1=every call)",
    )

    # ── Status ───────────────────────────────────────────────────────────
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        doc="Soft active/inactive toggle",
    )

    # ── Extensible Config ────────────────────────────────────────────────
    config: Mapped[dict] = mapped_column(
        JSONB,
        nullable=False,
        default=dict,
        doc="Extensible configuration (provider-specific options, future features)",
    )

    # ── Timestamps ───────────────────────────────────────────────────────
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        doc="Creation timestamp",
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        doc="Last update timestamp",
    )

    # ── Relationships ────────────────────────────────────────────────────
    project: Mapped["Project"] = relationship(
        "Project",
        back_populates="agent_definitions",
        lazy="selectin",
    )

    team: Mapped[Optional["Team"]] = relationship(
        "Team",
        lazy="selectin",
    )

    conversations: Mapped[list["AgentConversation"]] = relationship(
        "AgentConversation",
        back_populates="agent_definition",
        lazy="noload",
    )

    def __repr__(self) -> str:
        return (
            f"<AgentDefinition(id={self.id}, name={self.agent_name!r}, "
            f"role={self.sdlc_role!r}, provider={self.provider!r})>"
        )
