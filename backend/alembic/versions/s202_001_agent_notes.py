"""Sprint 202: Add agent_notes table for structured agent memory

Revision ID: s202001
Revises: s190001
Create Date: 2026-04-21 00:00:00.000000

CONTEXT:
- Sprint 202 "Automated Evals + Context Engineering Depth"
- Anthropic Best Practices Gap 1 (P1): Context Engineering Depth
- Agents need persistent key-value notes that survive context resets
- Notes injected into _build_llm_context() as ## Agent Notes section
- UPSERT pattern: UNIQUE(agent_id, key) enables ON CONFLICT DO UPDATE
- Max 50 notes per agent, pruned by note_service.py

TABLE: agent_notes
- id: UUID PK (matches agent_definitions/conversations pattern)
- agent_id: UUID FK → agent_definitions.id (CASCADE)
- conversation_id: UUID FK → agent_conversations.id (SET NULL), nullable
- key: VARCHAR(100) NOT NULL
- value: VARCHAR(500) NOT NULL
- note_type: VARCHAR(20) DEFAULT 'context' (decision|commitment|context|preference)
- created_at, updated_at: TIMESTAMPTZ

INDEXES:
- idx_agent_notes_agent_id (agent_id)
- idx_agent_notes_conversation (conversation_id)
- uq_agent_notes_agent_key UNIQUE(agent_id, key)

SAFETY:
- New table only — no data loss risk
- Rollback: DROP TABLE agent_notes
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers
revision = "s202001"
down_revision = "s190001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create agent_notes table for structured agent memory."""
    op.create_table(
        "agent_notes",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("agent_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("conversation_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("key", sa.String(100), nullable=False),
        sa.Column("value", sa.String(500), nullable=False),
        sa.Column("note_type", sa.String(20), nullable=False, server_default="context"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(
            ["agent_id"],
            ["agent_definitions.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["conversation_id"],
            ["agent_conversations.id"],
            ondelete="SET NULL",
        ),
        sa.UniqueConstraint("agent_id", "key", name="uq_agent_notes_agent_key"),
    )
    op.create_index("idx_agent_notes_agent_id", "agent_notes", ["agent_id"])
    op.create_index("idx_agent_notes_conversation", "agent_notes", ["conversation_id"])


def downgrade() -> None:
    """Drop agent_notes table."""
    op.drop_index("idx_agent_notes_conversation", table_name="agent_notes")
    op.drop_index("idx_agent_notes_agent_id", table_name="agent_notes")
    op.drop_table("agent_notes")
