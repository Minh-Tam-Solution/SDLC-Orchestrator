"""
=========================================================================
AGENTS.md Models - Static Generator + Dynamic Overlay
SDLC Orchestrator - Sprint 80 (AGENTS.md Integration)

Version: 1.0.0
Date: January 19, 2026
Status: ACTIVE - Sprint 80 Implementation
Authority: Backend Lead + CTO Approved
Framework: SDLC 5.1.3 SASE Integration
ADR: ADR-029 AGENTS.md Integration Strategy

Purpose:
- Store generated AGENTS.md file history for audit
- Track dynamic context overlays delivered to PRs
- Support Static + Dynamic Overlay architecture

Two-Layer Architecture (ADR-029):
- Layer A: Static AGENTS.md (committed to repo)
- Layer B: Dynamic Overlay (runtime via PR comments, CLI, API)

Security Standards:
- Row-Level Security (project-scoped access)
- Secret detection prevents committing credentials
- Audit trail for all generations and deliveries

Zero Mock Policy: Real SQLAlchemy model with all fields
=========================================================================
"""

from datetime import datetime
from typing import Optional, List, TYPE_CHECKING, Any
from uuid import uuid4

from sqlalchemy import (
    Column,
    BigInteger,
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    Index,
    CheckConstraint,
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship, Mapped, mapped_column

from app.db.base_class import Base

if TYPE_CHECKING:
    from app.models.project import Project
    from app.models.user import User
    from app.models.sprint import Sprint


class AgentsMdFile(Base):
    """
    AGENTS.md file generation record for audit trail.

    Purpose:
        - Track all AGENTS.md generations per project
        - Store content, validation status, and metadata
        - Support audit queries (who generated what, when)

    Layer A (Static):
        - Generated content is committed to repo root
        - Rarely changes (architecture, conventions)
        - Read by AI coding tools (Cursor, Copilot, etc.)

    Attributes:
        id: Unique identifier (UUID v4)
        project_id: Associated project
        content: Full AGENTS.md file content
        content_hash: SHA256 hash for deduplication
        line_count: Number of lines (≤200 max)
        sections: List of section names
        generator_version: Version of generator used
        validation_status: pending, valid, or invalid
    """

    __tablename__ = "agents_md_files"

    # Primary Key
    id: Mapped[uuid4] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
        comment="Unique file ID (UUID v4)",
    )

    # Foreign Keys
    project_id: Mapped[uuid4] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Associated project ID",
    )

    generated_by: Mapped[Optional[uuid4]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        comment="User who triggered generation",
    )

    # Content Fields
    content: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="Full AGENTS.md file content",
    )

    content_hash: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        comment="SHA256 hash of content for deduplication",
    )

    line_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        comment="Number of lines in file (max 200)",
    )

    sections: Mapped[List[str]] = mapped_column(
        JSONB,
        nullable=False,
        server_default="[]",
        comment="List of section names: ['Quick Start', 'Architecture', ...]",
    )

    # Generation Metadata
    generated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        comment="Timestamp when file was generated",
    )

    generator_version: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        comment="Version of generator: 1.0.0",
    )

    source_analysis: Mapped[Optional[dict]] = mapped_column(
        JSONB,
        nullable=True,
        comment="Source files analyzed for generation",
    )

    # Validation
    validation_status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        server_default="pending",
        comment="Validation status: pending, valid, invalid",
    )

    validation_errors: Mapped[Optional[List[dict]]] = mapped_column(
        JSONB,
        nullable=True,
        server_default="[]",
        comment="List of validation errors",
    )

    validation_warnings: Mapped[Optional[List[dict]]] = mapped_column(
        JSONB,
        nullable=True,
        server_default="[]",
        comment="List of validation warnings",
    )

    # Relationships
    project: Mapped["Project"] = relationship(
        "Project",
        back_populates="agents_md_files",
        lazy="selectin",
    )

    generated_by_user: Mapped[Optional["User"]] = relationship(
        "User",
        foreign_keys=[generated_by],
        lazy="selectin",
    )

    # Table Arguments
    __table_args__ = (
        Index("idx_agents_md_files_project_id", "project_id"),
        Index("idx_agents_md_files_generated_at", "generated_at"),
        Index("idx_agents_md_files_content_hash", "content_hash"),
        CheckConstraint(
            "line_count > 0 AND line_count <= 200",
            name="chk_agents_md_line_count",
        ),
        CheckConstraint(
            "validation_status IN ('pending', 'valid', 'invalid')",
            name="chk_agents_md_validation_status",
        ),
        {
            "comment": "AGENTS.md file generation history for audit (ADR-029)"
        },
    )

    def __repr__(self) -> str:
        return (
            f"AgentsMdFile(id={self.id}, project_id={self.project_id}, "
            f"lines={self.line_count}, status={self.validation_status})"
        )

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for API responses."""
        return {
            "id": str(self.id),
            "project_id": str(self.project_id),
            "content": self.content,
            "content_hash": self.content_hash,
            "line_count": self.line_count,
            "sections": self.sections,
            "generated_at": self.generated_at.isoformat() if self.generated_at else None,
            "generated_by": str(self.generated_by) if self.generated_by else None,
            "generator_version": self.generator_version,
            "validation_status": self.validation_status,
            "validation_errors": self.validation_errors or [],
            "validation_warnings": self.validation_warnings or [],
        }


class ContextOverlay(Base):
    """
    Dynamic context overlay record for audit trail.

    Purpose:
        - Track all context overlays generated and delivered
        - Support audit queries (what context was shown when)
        - Not committed to git - delivered at runtime

    Layer B (Dynamic):
        - Generated on PR creation, gate pass, etc.
        - Delivered via PR comments, CLI, VS Code, API
        - Contains current SDLC stage, sprint, constraints

    Delivery Channels:
        - GitHub PR Comment (visible to Cursor, Copilot)
        - GitHub Check Run output
        - CLI: `sdlc context` command
        - VS Code Extension panel

    Attributes:
        id: Unique identifier (UUID v4)
        project_id: Associated project
        stage_name: Current SDLC stage
        gate_status: Latest gate evaluation result
        sprint_id: Active sprint (if any)
        constraints: List of active constraints (JSONB)
        strict_mode: Whether post-G3 strict mode is active
        trigger_type: What triggered the overlay
    """

    __tablename__ = "context_overlays"

    # Primary Key
    id: Mapped[uuid4] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
        comment="Unique overlay ID (UUID v4)",
    )

    # Foreign Keys
    project_id: Mapped[uuid4] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Associated project ID",
    )

    sprint_id: Mapped[Optional[uuid4]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("sprints.id", ondelete="SET NULL"),
        nullable=True,
        comment="Active sprint ID (if any)",
    )

    # Context Data
    stage_name: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
        comment="Current SDLC stage: Stage 04 (BUILD)",
    )

    gate_status: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
        comment="Latest gate status: G3 PASSED",
    )

    sprint_number: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
        comment="Sprint number for display",
    )

    sprint_goal: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Sprint goal for context",
    )

    # Constraints (JSONB array)
    # Example: [{"type": "strict_mode", "severity": "warning", "message": "..."}]
    constraints: Mapped[List[dict]] = mapped_column(
        JSONB,
        nullable=False,
        server_default="[]",
        comment="Active constraints affecting development",
    )

    # Flags
    strict_mode: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        server_default="false",
        comment="Post-G3 strict mode (bug fixes only)",
    )

    # Trigger Info
    generated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        comment="When overlay was generated",
    )

    trigger_type: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        comment="Trigger: pr_webhook, cli, api, scheduled, manual",
    )

    trigger_ref: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
        comment="Trigger reference: PR#123, CLI session ID",
    )

    # Delivery Tracking
    delivered_to_pr: Mapped[bool] = mapped_column(
        Boolean,
        server_default="false",
        comment="Whether delivered as PR comment",
    )

    delivered_to_check_run: Mapped[bool] = mapped_column(
        Boolean,
        server_default="false",
        comment="Whether delivered as Check Run output",
    )

    pr_comment_id: Mapped[Optional[int]] = mapped_column(
        BigInteger,
        nullable=True,
        comment="GitHub PR comment ID (if delivered)",
    )

    check_run_id: Mapped[Optional[int]] = mapped_column(
        BigInteger,
        nullable=True,
        comment="GitHub Check Run ID (if delivered)",
    )

    # Relationships
    project: Mapped["Project"] = relationship(
        "Project",
        back_populates="context_overlays",
        lazy="selectin",
    )

    sprint: Mapped[Optional["Sprint"]] = relationship(
        "Sprint",
        foreign_keys=[sprint_id],
        lazy="selectin",
    )

    # Table Arguments
    __table_args__ = (
        Index("idx_context_overlays_project_id", "project_id"),
        Index("idx_context_overlays_generated_at", "generated_at"),
        Index("idx_context_overlays_trigger", "trigger_type", "trigger_ref"),
        CheckConstraint(
            "trigger_type IN ('pr_webhook', 'cli', 'api', 'scheduled', 'manual')",
            name="chk_context_overlay_trigger_type",
        ),
        {
            "comment": "Dynamic context overlay audit log (ADR-029)"
        },
    )

    def __repr__(self) -> str:
        return (
            f"ContextOverlay(id={self.id}, project_id={self.project_id}, "
            f"trigger={self.trigger_type}, strict_mode={self.strict_mode})"
        )

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for API responses."""
        return {
            "id": str(self.id),
            "project_id": str(self.project_id),
            "generated_at": self.generated_at.isoformat() if self.generated_at else None,
            "stage_name": self.stage_name,
            "gate_status": self.gate_status,
            "sprint": {
                "id": str(self.sprint_id) if self.sprint_id else None,
                "number": self.sprint_number,
                "goal": self.sprint_goal,
            } if self.sprint_id else None,
            "constraints": self.constraints or [],
            "strict_mode": self.strict_mode,
            "trigger_type": self.trigger_type,
            "trigger_ref": self.trigger_ref,
            "delivered_to_pr": self.delivered_to_pr,
            "delivered_to_check_run": self.delivered_to_check_run,
            "pr_comment_id": self.pr_comment_id,
            "check_run_id": self.check_run_id,
        }
