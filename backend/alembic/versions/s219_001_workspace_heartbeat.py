"""Sprint 219: shared_workspace_items table + unique index.

Revision ID: s219_001
Revises: s218_001
Create Date: 2026-03-04

Creates:
- shared_workspace_items table (conversation-scoped key-value workspace)
- Unique index on (conversation_id, item_key) WHERE version > 0
  (allows multiple soft-deleted rows per key)
"""

revision = "s219_001"
down_revision = "s218_001"
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID


def upgrade() -> None:
    op.create_table(
        "shared_workspace_items",
        sa.Column("id", UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), primary_key=True),
        sa.Column("conversation_id", UUID(as_uuid=True), sa.ForeignKey("agent_conversations.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("created_by", UUID(as_uuid=True), sa.ForeignKey("agent_definitions.id", ondelete="SET NULL"), nullable=True),
        sa.Column("updated_by", UUID(as_uuid=True), sa.ForeignKey("agent_definitions.id", ondelete="SET NULL"), nullable=True),
        sa.Column("item_key", sa.String(200), nullable=False),
        sa.Column("item_type", sa.String(20), nullable=False, server_default="text"),
        sa.Column("content", sa.Text, nullable=True),
        sa.Column("version", sa.Integer, nullable=False, server_default="1"),
        sa.Column("conflict_resolution", sa.String(20), nullable=False, server_default="last_write_wins"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.CheckConstraint(
            "item_type IN ('text', 'code', 'diff', 'json', 'markdown', 'binary_ref')",
            name="ck_workspace_item_type",
        ),
        sa.CheckConstraint(
            "conflict_resolution IN ('last_write_wins', 'retry_3x', 'escalate_to_lead')",
            name="ck_workspace_conflict_resolution",
        ),
    )

    # Unique active key per conversation (soft-deleted rows excluded)
    op.create_index(
        "ix_workspace_conv_key_active",
        "shared_workspace_items",
        ["conversation_id", "item_key"],
        unique=True,
        postgresql_where=sa.text("version > 0"),
    )


def downgrade() -> None:
    op.drop_index("ix_workspace_conv_key_active", table_name="shared_workspace_items")
    op.drop_table("shared_workspace_items")
