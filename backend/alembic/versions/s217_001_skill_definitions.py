"""Sprint 217 — skill_definitions table + tsvector GIN index.

P2a Skills Engine (ADR-069, Plan Correction V1).

Creates:
- skill_definitions table with 5-tier hierarchy
- tsvector GENERATED column (simple tokenizer) for full-text search
- GIN index on tsvector column
- Indexes on project_id, agent_definition_id, slug, (tier, is_active)

Revision ID: s217_001
Revises: s216_001
Create Date: 2026-03-04
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "s217_001"
down_revision = "s216_001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "skill_definitions",
        # Primary key
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("gen_random_uuid()")),
        # Foreign keys (optional)
        sa.Column("project_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("projects.id", ondelete="CASCADE"),
                  nullable=True),
        sa.Column("agent_definition_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("agent_definitions.id", ondelete="CASCADE"),
                  nullable=True),
        # Identity
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("slug", sa.String(100), nullable=False),
        sa.Column("description", sa.Text, nullable=True),
        # Content
        sa.Column("frontmatter", sa.Text, nullable=True),
        sa.Column("content", sa.Text, nullable=True),
        # Tier & visibility
        sa.Column("tier", sa.String(20), nullable=False, server_default="workspace"),
        sa.Column("visibility", sa.String(20), nullable=False, server_default="public"),
        # Version
        sa.Column("version", sa.Integer, nullable=False, server_default="1"),
        # Workspace path
        sa.Column("workspace_path", sa.String(500), nullable=True),
        # Status
        sa.Column("is_active", sa.Boolean, nullable=False, server_default="true"),
        # Metadata
        sa.Column("metadata", postgresql.JSONB, nullable=False,
                  server_default=sa.text("'{}'::jsonb")),
        # Timestamps
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text("now()")),
        # Check constraints
        sa.CheckConstraint(
            "tier IN ('workspace', 'project_agent', 'personal_agent', 'global', 'builtin')",
            name="ck_skill_definitions_tier",
        ),
        sa.CheckConstraint(
            "visibility IN ('public', 'private', 'internal')",
            name="ck_skill_definitions_visibility",
        ),
        sa.UniqueConstraint(
            "slug", "tier", "project_id",
            name="uq_skill_slug_tier_project",
        ),
    )

    # Indexes for query performance
    op.create_index("ix_skill_definitions_project_id", "skill_definitions", ["project_id"])
    op.create_index("ix_skill_definitions_agent_def_id", "skill_definitions", ["agent_definition_id"])
    op.create_index("ix_skill_definitions_slug", "skill_definitions", ["slug"])
    op.create_index("ix_skill_definitions_tier_active", "skill_definitions", ["tier", "is_active"])

    # tsvector GENERATED column for full-text search
    # Indexes name + description + frontmatter for maximum search coverage
    # Uses 'simple' tokenizer (not 'english') — works with Vietnamese text + code tokens
    # Reference: MTClaw migration 000002, CTO Correction 3 + F4 review fix
    op.execute("""
        ALTER TABLE skill_definitions ADD COLUMN search_tsv tsvector
        GENERATED ALWAYS AS (
            to_tsvector('simple',
                COALESCE(name, '') || ' ' ||
                COALESCE(description, '') || ' ' ||
                COALESCE(frontmatter, '')
            )
        ) STORED
    """)

    # GIN index for fast tsvector queries
    op.execute("""
        CREATE INDEX idx_skill_definitions_tsv
        ON skill_definitions USING GIN(search_tsv)
    """)


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS idx_skill_definitions_tsv")
    op.drop_index("ix_skill_definitions_tier_active", table_name="skill_definitions")
    op.drop_index("ix_skill_definitions_slug", table_name="skill_definitions")
    op.drop_index("ix_skill_definitions_agent_def_id", table_name="skill_definitions")
    op.drop_index("ix_skill_definitions_project_id", table_name="skill_definitions")
    op.drop_table("skill_definitions")
