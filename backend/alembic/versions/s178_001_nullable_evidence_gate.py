"""Sprint 178: Make gate_evidence.gate_id nullable for agent evidence

Revision ID: s178_001
Revises: s177_001
Create Date: 2026-02-18 23:00:00.000000

CONTEXT:
- Sprint 178 "Team Orchestrator + Evidence Collector + Traces" — ADR-056 Phase 1
- EvidenceCollector captures agent outputs as evidence (gate_id=None)
- agent_messages.evidence_id FK already exists (nullable, Sprint 176)
- This migration relaxes gate_evidence.gate_id from NOT NULL → nullable
- Non-destructive: existing rows keep their gate_id; only new agent evidence rows use NULL

SAFETY:
- No data loss: DROP NOT NULL only relaxes constraint
- No default change: existing rows unaffected
- Rollback: ADD NOT NULL (safe if no NULL rows exist yet)
- Index preserved: gate_id index unchanged

CTO REVIEW:
- Sprint 178 plan approved
- ADR-056 evidence lifecycle: agent output → evidence_locked → SHA256 verified
- Reference: FR-041 (Evidence-based agent output capture)
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers
revision = "s178_001"
down_revision = "s177_001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Make gate_evidence.gate_id nullable for agent evidence capture."""
    op.alter_column(
        "gate_evidence",
        "gate_id",
        existing_type=sa.UUID(),
        nullable=True,
    )


def downgrade() -> None:
    """Restore gate_evidence.gate_id to NOT NULL.

    WARNING: This will fail if any rows have gate_id=NULL.
    Run `DELETE FROM gate_evidence WHERE gate_id IS NULL` first if needed.
    """
    op.alter_column(
        "gate_evidence",
        "gate_id",
        existing_type=sa.UUID(),
        nullable=False,
    )
