"""
SQLAlchemy models for Context Authority V2 (SPEC-0011)

Sprint 120 Pre-work: Database Schema Design
Date: January 29, 2026
Status: DRAFT - Pre-Sprint 120

Models:
1. ContextOverlayTemplate - Dynamic overlay templates
2. ContextSnapshot - Point-in-time context for audit
3. ContextOverlayApplication - Track overlay applications

References:
- SPEC-0011: Context Authority V2 - Gate-Aware Dynamic Context
- ADR-041: Framework 6.0 Governance System Design
- Sprint 120 Plan: SPRINT-120-CONTEXT-AUTHORITY-V2-GATES.md
"""
from datetime import datetime
from typing import Optional
from uuid import UUID, uuid4

from sqlalchemy import (
    String,
    Integer,
    Boolean,
    DateTime,
    Text,
    ForeignKey,
    Index,
    UniqueConstraint,
    CheckConstraint,
)
from sqlalchemy.dialects.postgresql import UUID as PGUUID, JSONB
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy.sql import func

from app.db.base_class import Base


class ContextOverlayTemplate(Base):
    """
    Dynamic overlay templates for gate-aware context injection.

    Trigger Types (SPEC-0011 FR-002):
    1. gate_pass - Triggered when a gate passes (e.g., G0.2 PASS)
    2. gate_fail - Triggered when a gate fails
    3. index_zone - Triggered by vibecoding index zone (green/yellow/orange/red)
    4. stage_constraint - Triggered by stage-specific constraints

    Template Variables:
    - {date}: Current date (YYYY-MM-DD)
    - {index}: Vibecoding index value
    - {stage}: Current SDLC stage
    - {tier}: Project tier (LITE/STANDARD/PROFESSIONAL/ENTERPRISE)
    - {gate}: Gate identifier (G0, G1, G2, G3, G4)
    - {top_signals}: Top contributing signals (for index templates)

    Tier Scoping:
    - tier=NULL: Applies to ALL tiers
    - tier='STANDARD': Applies only to STANDARD tier

    Table: ca_v2_overlay_templates (prefixed to avoid Sprint 108 conflict)
    """
    __tablename__ = "ca_v2_overlay_templates"

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )
    trigger_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
        comment="Trigger type: gate_pass, gate_fail, index_zone, stage_constraint",
    )
    trigger_value: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
        comment="Trigger value: G0.2, G1, green, yellow, orange, red, stage_02_code_block",
    )
    tier: Mapped[Optional[str]] = mapped_column(
        String(20),
        nullable=True,
        index=True,
        comment="Tier scope: NULL=all tiers, or LITE/STANDARD/PROFESSIONAL/ENTERPRISE",
    )
    overlay_content: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="Template content with {variable} placeholders",
    )
    priority: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        comment="Priority for ordering multiple templates (higher = first)",
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        server_default="true",
        comment="Whether template is active",
    )
    name: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
        comment="Human-readable template name",
    )
    description: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Template description and usage notes",
    )
    created_by_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        comment="User who created this template",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    # Relationships
    created_by = relationship("User", foreign_keys=[created_by_id])
    applications = relationship(
        "ContextOverlayApplication",
        back_populates="template",
        cascade="all, delete-orphan",
    )

    # Constraints and indexes
    __table_args__ = (
        CheckConstraint(
            "trigger_type IN ('gate_pass', 'gate_fail', 'index_zone', 'stage_constraint')",
            name="ck_ca_v2_overlay_templates_trigger_type",
        ),
        CheckConstraint(
            "tier IS NULL OR tier IN ('LITE', 'STANDARD', 'PROFESSIONAL', 'ENTERPRISE')",
            name="ck_ca_v2_overlay_templates_tier",
        ),
        Index(
            "idx_ca_v2_overlay_templates_trigger_lookup",
            "trigger_type",
            "trigger_value",
            "tier",
            "is_active",
        ),
        Index(
            "idx_ca_v2_overlay_templates_priority",
            "priority",
            postgresql_ops={"priority": "DESC"},
        ),
    )

    def __repr__(self) -> str:
        return (
            f"<ContextOverlayTemplate(name='{self.name}', "
            f"trigger={self.trigger_type}:{self.trigger_value}, "
            f"tier={self.tier or 'ALL'})>"
        )


class ContextSnapshot(Base):
    """
    Point-in-time context snapshot for audit trail.

    Created on every Context Authority V2 validation (SPEC-0011 FR-005).
    Immutable - snapshots are never updated, only created.

    Captures:
    - Gate status at validation time
    - Vibecoding index at validation time
    - Dynamic overlay content generated
    - V1 validation result (ADR linkage, design doc, AGENTS.md freshness)
    - Project tier

    Use Cases:
    - Audit: "What context did the AI see at merge time?"
    - Debugging: "Why was this PR routed to CEO review?"
    - Compliance: "Prove governance was enforced at merge"

    Table: ca_v2_context_snapshots (prefixed to avoid Sprint 108 conflict)
    """
    __tablename__ = "ca_v2_context_snapshots"

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )
    submission_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("governance_submissions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Governance submission this snapshot belongs to",
    )
    project_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Project this snapshot belongs to",
    )
    # Gate status at snapshot time
    gate_status: Mapped[dict] = mapped_column(
        JSONB,
        nullable=False,
        comment="Gate status at validation time: {current_stage, last_passed_gate, pending_gates}",
    )
    # Vibecoding index at snapshot time
    vibecoding_index: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        comment="Vibecoding index at validation time (0-100)",
    )
    vibecoding_zone: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        comment="Vibecoding zone: GREEN, YELLOW, ORANGE, RED",
    )
    # Dynamic overlay generated
    dynamic_overlay: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="Dynamic overlay content generated for this validation",
    )
    # V1 validation result (legacy context checks)
    v1_result: Mapped[Optional[dict]] = mapped_column(
        JSONB,
        nullable=True,
        comment="Context Authority V1 validation result (ADR linkage, design doc, etc.)",
    )
    # V2 validation details
    gate_violations: Mapped[Optional[list]] = mapped_column(
        JSONB,
        nullable=True,
        comment="Gate constraint violations (stage blocking)",
    )
    index_warnings: Mapped[Optional[list]] = mapped_column(
        JSONB,
        nullable=True,
        comment="Vibecoding index warnings",
    )
    # Project tier at snapshot time
    tier: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        comment="Project tier at validation time",
    )
    # Validation outcome
    is_valid: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        index=True,
        comment="Overall validation result (V1 + V2 combined)",
    )
    # Templates applied
    applied_template_ids: Mapped[Optional[list]] = mapped_column(
        JSONB,
        nullable=True,
        comment="Array of template IDs that contributed to dynamic overlay",
    )
    # Timestamp
    snapshot_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        index=True,
        comment="Snapshot creation timestamp",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    # Relationships
    submission = relationship("GovernanceSubmission", back_populates="context_snapshots")
    project = relationship("Project", back_populates="context_snapshots")

    # Indexes for common queries
    __table_args__ = (
        CheckConstraint(
            "vibecoding_zone IN ('GREEN', 'YELLOW', 'ORANGE', 'RED')",
            name="ck_ca_v2_context_snapshots_zone",
        ),
        CheckConstraint(
            "tier IN ('LITE', 'STANDARD', 'PROFESSIONAL', 'ENTERPRISE')",
            name="ck_ca_v2_context_snapshots_tier",
        ),
        # Time-series index for historical analysis (BRIN for timestamp columns)
        Index(
            "idx_ca_v2_context_snapshots_snapshot_at_brin",
            "snapshot_at",
            postgresql_using="brin",
        ),
        # Composite index for project-based queries
        Index(
            "idx_ca_v2_context_snapshots_project_time",
            "project_id",
            "snapshot_at",
        ),
        # Index for audit queries by validity
        Index(
            "idx_ca_v2_context_snapshots_validity",
            "is_valid",
            "snapshot_at",
        ),
    )

    def __repr__(self) -> str:
        return (
            f"<ContextSnapshot(submission_id={self.submission_id}, "
            f"index={self.vibecoding_index}, zone='{self.vibecoding_zone}', "
            f"valid={self.is_valid})>"
        )


class ContextOverlayApplication(Base):
    """
    Track which templates were applied to which snapshots.

    Join table between ContextSnapshot and ContextOverlayTemplate.
    Provides audit trail of template application.

    Use Cases:
    - "Which templates contributed to this overlay?"
    - "How often is this template being applied?"
    - "What's the impact of changing this template?"

    Table: ca_v2_overlay_applications (prefixed to avoid Sprint 108 conflict)
    """
    __tablename__ = "ca_v2_overlay_applications"

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )
    snapshot_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("ca_v2_context_snapshots.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Snapshot where template was applied",
    )
    template_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("ca_v2_overlay_templates.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Template that was applied",
    )
    # Template content at application time (snapshot for audit)
    template_content_snapshot: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="Template content at application time (immutable snapshot)",
    )
    # Rendered content after variable substitution
    rendered_content: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="Rendered content after variable substitution",
    )
    # Variables used for rendering
    variables_used: Mapped[Optional[dict]] = mapped_column(
        JSONB,
        nullable=True,
        comment="Variables used for template rendering",
    )
    # Order in the final overlay
    application_order: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        comment="Order in which template appears in final overlay",
    )
    applied_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        comment="Application timestamp",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    # Relationships
    snapshot = relationship("ContextSnapshot", backref="overlay_applications")
    template = relationship("ContextOverlayTemplate", back_populates="applications")

    # Constraints
    __table_args__ = (
        UniqueConstraint(
            "snapshot_id",
            "template_id",
            name="uq_ca_v2_overlay_applications_snapshot_template",
        ),
        Index(
            "idx_ca_v2_overlay_applications_template_usage",
            "template_id",
            "applied_at",
        ),
    )

    def __repr__(self) -> str:
        return (
            f"<ContextOverlayApplication(snapshot_id={self.snapshot_id}, "
            f"template_id={self.template_id}, order={self.application_order})>"
        )


# Extended columns for existing tables (to be added via migration)
# These are documented here for reference but implemented in Alembic migration

"""
ALTER TABLE context_authorities ADD COLUMN IF NOT EXISTS gate_status JSONB;
ALTER TABLE context_authorities ADD COLUMN IF NOT EXISTS vibecoding_index INTEGER;
ALTER TABLE context_authorities ADD COLUMN IF NOT EXISTS dynamic_overlay TEXT;
ALTER TABLE context_authorities ADD COLUMN IF NOT EXISTS tier VARCHAR(20);

-- Add relationship columns to GovernanceSubmission
-- Note: context_snapshots FK already defined in ContextSnapshot model

-- Add relationship columns to Project
-- Note: context_snapshots FK already defined in ContextSnapshot model
"""
