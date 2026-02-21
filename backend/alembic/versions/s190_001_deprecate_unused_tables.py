"""s190_001_deprecate_unused_tables — Mark deprecated tables with COMMENT

Sprint 190 — Conversation-First Cleanup

Mark 9 tables from deleted/frozen modules as DEPRECATED via SQL COMMENT.
Tables are NOT dropped — data preserved for audit trail and potential rollback.
Services deleted: NIST MAP/MEASURE/MANAGE, AI Council, Feedback, PR Learning.

Tables deprecated:
  - ai_systems (NIST MAP)
  - performance_metrics (NIST MEASURE)
  - manage_risk_responses (NIST MANAGE)
  - manage_incidents (NIST MANAGE)
  - council_sessions (AI Council)
  - pilot_feedback (Feedback)
  - feedback_comments (Feedback)
  - pr_learnings (EP-11 Feedback Learning)
  - learning_aggregations (EP-11 Learning Aggregation)

See: ADR-064 (Sprint 190 Cleanup), CEO Conversation-First Strategy

Revision ID: s190001
Revises:     s188002
Create Date: 2026-02-21 00:00:00.000000
"""

from alembic import op

# revision identifiers, used by Alembic.
revision = "s190001"
down_revision = "s188002"
branch_labels = None
depends_on = None

# Tables to deprecate with their original module context
_DEPRECATED_TABLES = [
    ("ai_systems", "NIST MAP — Sprint 157, frozen Sprint 190"),
    ("performance_metrics", "NIST MEASURE — Sprint 157, frozen Sprint 190"),
    ("manage_risk_responses", "NIST MANAGE — Sprint 158, frozen Sprint 190"),
    ("manage_incidents", "NIST MANAGE — Sprint 158, frozen Sprint 190"),
    ("council_sessions", "AI Council — frozen, unused, Sprint 190"),
    ("pilot_feedback", "Pilot Feedback — frozen, unused, Sprint 190"),
    ("feedback_comments", "Pilot Feedback — frozen, unused, Sprint 190"),
    ("pr_learnings", "EP-11 Feedback Learning — Sprint 94, frozen Sprint 190"),
    ("learning_aggregations", "EP-11 Learning Aggregation — Sprint 94, frozen Sprint 190"),
]


def upgrade() -> None:
    """Add DEPRECATED comment to unused tables (non-destructive)."""
    for table_name, context in _DEPRECATED_TABLES:
        op.execute(
            f"COMMENT ON TABLE IF EXISTS {table_name} IS "
            f"'DEPRECATED Sprint 190 — {context}. See ADR-064.'"
        )


def downgrade() -> None:
    """Remove deprecation comments (restore to no comment)."""
    for table_name, _ in _DEPRECATED_TABLES:
        op.execute(f"COMMENT ON TABLE IF EXISTS {table_name} IS NULL")
