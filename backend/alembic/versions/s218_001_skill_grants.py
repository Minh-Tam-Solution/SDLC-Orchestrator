"""Sprint 218: skill_agent_grants table + agent_messages.metadata JSONB

Revision ID: s218_001
Revises: s217_001
Create Date: 2026-03-04

ADR-070: CoPaw/AgentScope Pattern Adoption
- skill_agent_grants: per-agent skill access control (CoPaw skills/loader.go pattern)
- agent_messages.metadata: general-purpose JSONB for routing evidence, broadcast metadata,
  approval feedback (S220), consensus votes (S221). Distinct from existing 'mentions' JSONB.
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB

revision = "s218_001"
down_revision = "s217_001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # --- skill_agent_grants table ---
    op.create_table(
        "skill_agent_grants",
        sa.Column("id", UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), primary_key=True),
        sa.Column(
            "skill_definition_id",
            UUID(as_uuid=True),
            sa.ForeignKey("skill_definitions.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "agent_definition_id",
            UUID(as_uuid=True),
            sa.ForeignKey("agent_definitions.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "granted_by",
            UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("granted_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.UniqueConstraint("skill_definition_id", "agent_definition_id", name="uq_skill_agent_grant"),
    )
    op.create_index(
        "idx_skill_agent_grants_agent",
        "skill_agent_grants",
        ["agent_definition_id"],
    )

    # --- agent_messages.metadata JSONB column ---
    # Distinct from existing 'mentions' JSONB (parsed @agent refs).
    # Used for: routing evidence, broadcast metadata, approval feedback, consensus.
    op.add_column(
        "agent_messages",
        sa.Column("metadata", JSONB, server_default=sa.text("'{}'::jsonb"), nullable=False),
    )


def downgrade() -> None:
    op.drop_column("agent_messages", "metadata")
    op.drop_index("idx_skill_agent_grants_agent", table_name="skill_agent_grants")
    op.drop_table("skill_agent_grants")
