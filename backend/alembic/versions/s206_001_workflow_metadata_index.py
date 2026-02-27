"""s206_001_workflow_metadataindex

Sprint 206 (LangGraph Durable Workflows) — ADR-066 D-066-02.

Creates a partial GIN expression index on agent_conversations.metadata
for WorkflowResumer reconciler queries:
  - Filters on metadata->'workflow'->>'status' = 'waiting'
  - Orders by metadata->'workflow'->>'next_wakeup_at'
  - Only indexes rows where the 'workflow' key exists in metadata

The partial index dramatically speeds up the reconciler's 30s polling
query without indexing conversations that have no workflow state.

Revision ID: s206_001
Revises: s203001
Create Date: 2026-02-25
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "s206_001"
down_revision = "s203001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Partial expression index for WorkflowResumer reconciler (D-066-02)
    # Covers: WHERE metadata->'workflow' IS NOT NULL
    # Orders by: next_wakeup_at (timestamptz cast)
    # Status filter is applied at query time (not indexed — low cardinality)
    op.execute("""
        CREATE INDEX IF NOT EXISTS
          idx_agent_conv_workflow_wakeup
        ON agent_conversations
        USING btree (
          (metadata->'workflow'->>'next_wakeup_at')
        )
        WHERE metadata->>'workflow' IS NOT NULL
    """)


def downgrade() -> None:
    op.execute("""
        DROP INDEX IF EXISTS idx_agent_conv_workflow_wakeup
    """)
