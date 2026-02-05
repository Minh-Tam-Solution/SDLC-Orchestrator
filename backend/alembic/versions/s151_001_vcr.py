"""Sprint 151: VCR (Version Controlled Resolution) Table

Creates the version_controlled_resolutions table for SASE artifacts.
VCR captures post-merge documentation for significant changes with
AI attribution tracking.

Sprint: 151 - SASE Artifacts Enhancement
Priority: P0
Reference: SPEC-0024, ADR-048

Revision ID: s151_001
Revises: s147_001
Create Date: 2026-03-04
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "s151_001"
down_revision: Union[str, None] = "s147_001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create version_controlled_resolutions table for SASE VCR workflow."""

    # Create VCR table (enum will be created automatically by SQLAlchemy with checkfirst=True)
    op.create_table(
        "version_controlled_resolutions",
        # Primary key
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        # Foreign keys
        sa.Column(
            "project_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("projects.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        # PR reference
        sa.Column("pr_number", sa.Integer, nullable=True),
        sa.Column("pr_url", sa.String(500), nullable=True),
        # VCR Content
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("problem_statement", sa.Text, nullable=False),
        sa.Column("root_cause_analysis", sa.Text, nullable=True),
        sa.Column("solution_approach", sa.Text, nullable=False),
        sa.Column("implementation_notes", sa.Text, nullable=True),
        # Linkage (Evidence Vault, ADRs)
        sa.Column(
            "evidence_ids",
            postgresql.ARRAY(postgresql.UUID(as_uuid=True)),
            nullable=True,
            server_default="{}",
        ),
        sa.Column(
            "adr_ids",
            postgresql.ARRAY(postgresql.UUID(as_uuid=True)),
            nullable=True,
            server_default="{}",
        ),
        # AI Attribution
        sa.Column(
            "ai_generated_percentage",
            sa.Float,
            nullable=True,
            server_default="0.0",
        ),
        sa.Column(
            "ai_tools_used",
            postgresql.ARRAY(sa.String),
            nullable=True,
            server_default="{}",
        ),
        sa.Column(
            "ai_generation_details",
            postgresql.JSONB,
            nullable=True,
            server_default="{}",
        ),
        # Workflow status
        sa.Column(
            "status",
            sa.Enum(
                "draft",
                "submitted",
                "approved",
                "rejected",
                name="vcrstatus",
            ),
            nullable=False,
            server_default="draft",
            index=True,
        ),
        # User references
        sa.Column(
            "created_by_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "approved_by_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        # Rejection reason
        sa.Column("rejection_reason", sa.Text, nullable=True),
        # Timestamps
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
        sa.Column("submitted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("approved_at", sa.DateTime(timezone=True), nullable=True),
    )

    # Create indexes for common queries
    op.create_index(
        "ix_vcr_project_status",
        "version_controlled_resolutions",
        ["project_id", "status"],
    )
    op.create_index(
        "ix_vcr_created_by",
        "version_controlled_resolutions",
        ["created_by_id"],
    )
    op.create_index(
        "ix_vcr_created_at",
        "version_controlled_resolutions",
        ["created_at"],
    )

    # Add comment
    op.execute("""
        COMMENT ON TABLE version_controlled_resolutions IS
        'VCR (Version Controlled Resolution) - SASE artifact for post-merge documentation.
        Tracks problem/solution documentation with AI attribution for significant changes.
        Workflow: draft → submitted → approved/rejected.
        Sprint 151, ADR-048, SPEC-0024.'
    """)


def downgrade() -> None:
    """Drop version_controlled_resolutions table."""
    op.drop_index("ix_vcr_created_at", table_name="version_controlled_resolutions")
    op.drop_index("ix_vcr_created_by", table_name="version_controlled_resolutions")
    op.drop_index("ix_vcr_project_status", table_name="version_controlled_resolutions")
    op.drop_table("version_controlled_resolutions")
    op.execute("DROP TYPE vcrstatus")
