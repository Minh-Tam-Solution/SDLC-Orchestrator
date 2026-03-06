"""
=========================================================================
Skill Definition Model — Sprint 217 (P2a Skills Engine)
SDLC Orchestrator — ADR-069/FR-051

Version: 1.0.0
Date: 2026-03-04
Status: ACTIVE — Sprint 217
Authority: CTO Approved (ADR-069, Plan Correction V1)
Reference: MTClaw /internal/skills/loader.go (361 LOC)

Purpose:
- Stores skill definitions with 5-tier hierarchy
- tsvector GENERATED column for DB-level full-text search
- Frontmatter + content for SKILL.md file format
- Visibility controls (public/private/internal)

5-Tier Hierarchy (highest priority first):
  1. workspace     — project-specific overrides
  2. project_agent — agent-specific skills in project
  3. personal_agent — agent's personal skill library
  4. global        — available to all agents
  5. builtin       — system-provided defaults

Zero Mock Policy: Production-ready SQLAlchemy 2.0 model
=========================================================================
"""

from datetime import datetime
from typing import TYPE_CHECKING, Optional
from uuid import uuid4

import sqlalchemy as sa
from sqlalchemy import Boolean, Computed, Integer, String, Text, ForeignKey, DateTime, CheckConstraint
from sqlalchemy.dialects.postgresql import JSONB, TSVECTOR, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base_class import Base

if TYPE_CHECKING:
    from app.models.agent_definition import AgentDefinition
    from app.models.project import Project

# Valid tier values (priority order: 1=highest, 5=lowest)
SKILL_TIERS = ("workspace", "project_agent", "personal_agent", "global", "builtin")
SKILL_TIER_PRIORITY = {tier: idx for idx, tier in enumerate(SKILL_TIERS)}

# Valid visibility values
SKILL_VISIBILITIES = ("public", "private", "internal")


class SkillDefinition(Base):
    """
    Skill definition — reusable capability units for AI agents.

    Each skill has a frontmatter (name, description, metadata) and
    content (the actual instructions/prompt). Skills are organized in
    a 5-tier hierarchy where higher-priority tiers override lower ones
    for the same slug.

    Port of MTClaw skills/loader.go + skills/search.go.
    """

    __tablename__ = "skill_definitions"

    # ── Primary Key ──────────────────────────────────────────────────────
    id: Mapped[uuid4] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
        doc="Unique identifier for the skill definition",
    )

    # ── Foreign Keys (optional bindings) ─────────────────────────────────
    project_id: Mapped[Optional[uuid4]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
        doc="Project this skill is scoped to (workspace/project_agent tiers)",
    )

    agent_definition_id: Mapped[Optional[uuid4]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("agent_definitions.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
        doc="Agent this skill is assigned to (personal_agent tier)",
    )

    # ── Identity ─────────────────────────────────────────────────────────
    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        doc="Display name (e.g., 'Code Review Checklist')",
    )

    slug: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
        doc="URL-safe identifier (e.g., 'code-review-checklist'). Unique per tier+project.",
    )

    description: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        doc="Human-readable description for search and BuildSummary",
    )

    # ── Content ──────────────────────────────────────────────────────────
    frontmatter: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        doc="YAML-like frontmatter metadata (parsed by skill loader)",
    )

    content: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        doc="Skill body — instructions, prompts, or templates",
    )

    # ── Tier & Visibility ────────────────────────────────────────────────
    tier: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="workspace",
        doc="Tier: workspace|project_agent|personal_agent|global|builtin",
    )

    visibility: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="public",
        doc="Visibility: public|private|internal",
    )

    # ── Versioning ───────────────────────────────────────────────────────
    version: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=1,
        doc="Monotonic version counter for optimistic concurrency",
    )

    # ── Workspace Path ───────────────────────────────────────────────────
    workspace_path: Mapped[Optional[str]] = mapped_column(
        String(500),
        nullable=True,
        doc="Filesystem path to the SKILL.md file (for workspace tier)",
    )

    # ── Status ───────────────────────────────────────────────────────────
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        doc="Soft active/inactive toggle",
    )

    # ── Extensible Config ────────────────────────────────────────────────
    metadata_: Mapped[dict] = mapped_column(
        "metadata",
        JSONB,
        nullable=False,
        default=dict,
        doc="Extensible metadata (tags, categories, dependencies)",
    )

    # ── Full-Text Search (Sprint 217 — GENERATED ALWAYS STORED) ─────────
    # Maps to the DB-level GENERATED tsvector column.
    # Read-only in Python — PostgreSQL maintains it automatically.
    search_tsv = mapped_column(
        TSVECTOR,
        Computed(
            "to_tsvector('simple', "
            "COALESCE(name, '') || ' ' || "
            "COALESCE(description, '') || ' ' || "
            "COALESCE(frontmatter, ''))",
            persisted=True,
        ),
        nullable=True,
    )

    # ── Timestamps ───────────────────────────────────────────────────────
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.utcnow,
        doc="Creation timestamp",
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        doc="Last update timestamp",
    )

    # ── Relationships ────────────────────────────────────────────────────
    project: Mapped[Optional["Project"]] = relationship(
        "Project",
        foreign_keys=[project_id],
        lazy="selectin",
    )

    agent_definition: Mapped[Optional["AgentDefinition"]] = relationship(
        "AgentDefinition",
        foreign_keys=[agent_definition_id],
        lazy="selectin",
    )

    # ── Constraints ──────────────────────────────────────────────────────
    __table_args__ = (
        CheckConstraint(
            "tier IN ('workspace', 'project_agent', 'personal_agent', 'global', 'builtin')",
            name="ck_skill_definitions_tier",
        ),
        CheckConstraint(
            "visibility IN ('public', 'private', 'internal')",
            name="ck_skill_definitions_visibility",
        ),
        sa.UniqueConstraint(
            "slug", "tier", "project_id",
            name="uq_skill_slug_tier_project",
        ),
    )

    def to_dict(self) -> dict:
        """Serialize to JSON-compatible dict."""
        return {
            "id": str(self.id),
            "project_id": str(self.project_id) if self.project_id else None,
            "agent_definition_id": str(self.agent_definition_id) if self.agent_definition_id else None,
            "name": self.name,
            "slug": self.slug,
            "description": self.description,
            "frontmatter": self.frontmatter,
            "content": self.content,
            "tier": self.tier,
            "visibility": self.visibility,
            "version": self.version,
            "workspace_path": self.workspace_path,
            "is_active": self.is_active,
            "metadata": self.metadata_,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    def __repr__(self) -> str:
        return (
            f"<SkillDefinition(id={self.id}, slug={self.slug!r}, "
            f"tier={self.tier!r}, visibility={self.visibility!r})>"
        )
