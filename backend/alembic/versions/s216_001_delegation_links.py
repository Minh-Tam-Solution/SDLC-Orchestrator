"""Sprint 216: delegation_links table + teams.lead_agent_definition_id

Revision ID: s216_001
Revises: s209_004
Create Date: 2026-03-04

Sprint: 216 — P1 Context Injection + Delegation Links
ADR: ADR-069 (MTClaw Best Practice Adoption)
FR: FR-051 (Delegation Links and Context Injection)

Creates:
- delegation_links table with UNIQUE + CHECK constraints
- teams.lead_agent_definition_id FK (ON DELETE SET NULL)
- Composite index on (source_agent_id, is_active) for context injector queries
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "s216_001"
down_revision = "s209_004"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # -- delegation_links table --
    op.create_table(
        "delegation_links",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("source_agent_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("target_agent_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("link_type", sa.String(50), server_default="can_delegate", nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column("metadata", postgresql.JSONB(astext_type=sa.Text()), server_default=sa.text("'{}'::jsonb"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["source_agent_id"], ["agent_definitions.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["target_agent_id"], ["agent_definitions.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("source_agent_id", "target_agent_id", "link_type", name="uq_delegation_link_source_target_type"),
        sa.CheckConstraint("source_agent_id != target_agent_id", name="ck_delegation_link_no_self"),
    )
    op.create_index("ix_delegation_links_source_agent_id", "delegation_links", ["source_agent_id"])
    op.create_index("ix_delegation_links_target_agent_id", "delegation_links", ["target_agent_id"])
    op.create_index("ix_delegation_links_source_active", "delegation_links", ["source_agent_id", "is_active"])

    # -- teams.lead_agent_definition_id --
    op.add_column(
        "teams",
        sa.Column(
            "lead_agent_definition_id",
            postgresql.UUID(as_uuid=True),
            nullable=True,
        ),
    )
    op.create_foreign_key(
        "fk_teams_lead_agent_def",
        "teams",
        "agent_definitions",
        ["lead_agent_definition_id"],
        ["id"],
        ondelete="SET NULL",
    )


def downgrade() -> None:
    op.drop_constraint("fk_teams_lead_agent_def", "teams", type_="foreignkey")
    op.drop_column("teams", "lead_agent_definition_id")

    op.drop_index("ix_delegation_links_source_active", "delegation_links")
    op.drop_index("ix_delegation_links_target_agent_id", "delegation_links")
    op.drop_index("ix_delegation_links_source_agent_id", "delegation_links")
    op.drop_table("delegation_links")
