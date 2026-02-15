"""Sprint 173: Gate State Machine + Evidence Contract (ADR-053)

Revision ID: s173_001
Revises: s172_001
Create Date: 2026-02-15 10:00:00.000000

CONTEXT:
- Sprint 173 "Sharpen, Don't Amputate" — Governance Loop completion
- Gate state machine: 6 governance states + ARCHIVED lifecycle state
- Evidence contract: server-side SHA256, criteria binding, source tracking
- CTO + Architect + SDLC Expert — All Approved v4 FINAL

CHANGES:
Gates table:
- Add evaluated_at (TIMESTAMP) — last evaluation timestamp
- Add exit_criteria_version (UUID) — for evidence snapshot binding
- Rename status values: PENDING_APPROVAL → SUBMITTED, IN_PROGRESS → EVALUATED

Gate Evidence table:
- Add sha256_server (VARCHAR 64) — server re-computed hash
- Add criteria_snapshot_id (UUID) — binds to gate exit_criteria_version
- Add source (VARCHAR 20) — upload source (cli, extension, web, other)
- Make sha256_hash nullable (for source='other' untrusted uploads)

RELATED:
- ADR-053-Governance-Loop-State-Machine.md
- CONTRACT-GOVERNANCE-LOOP.md
- SPRINT-173-PLAN.md
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID as PG_UUID


# revision identifiers, used by Alembic.
revision = 's173_001'
down_revision = 's172_001'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Apply Sprint 173 Gate State Machine + Evidence Contract schema changes."""

    # ========================================================================
    # Gates Table — State Machine columns
    # ========================================================================

    # Add evaluated_at timestamp (Sprint 173: last evaluation timestamp)
    op.add_column(
        'gates',
        sa.Column('evaluated_at', sa.DateTime(), nullable=True),
    )

    # Add exit_criteria_version UUID (Sprint 173: evidence snapshot binding)
    op.add_column(
        'gates',
        sa.Column(
            'exit_criteria_version',
            PG_UUID(as_uuid=True),
            server_default=sa.text('gen_random_uuid()'),
            nullable=True,
        ),
    )

    # Data migration: rename legacy status values to Sprint 173 values
    op.execute(
        "UPDATE gates SET status = 'SUBMITTED' WHERE status = 'PENDING_APPROVAL'"
    )
    op.execute(
        "UPDATE gates SET status = 'EVALUATED' WHERE status = 'IN_PROGRESS'"
    )

    # ========================================================================
    # Gate Evidence Table — Evidence Contract columns
    # ========================================================================

    # Add sha256_server (server re-computed SHA256)
    op.add_column(
        'gate_evidence',
        sa.Column('sha256_server', sa.String(64), nullable=True),
    )

    # Add criteria_snapshot_id (binds evidence to gate exit_criteria_version)
    op.add_column(
        'gate_evidence',
        sa.Column('criteria_snapshot_id', PG_UUID(as_uuid=True), nullable=True),
    )

    # Add source (upload source tracking)
    op.add_column(
        'gate_evidence',
        sa.Column(
            'source',
            sa.String(20),
            nullable=False,
            server_default='web',
        ),
    )

    # Make sha256_hash nullable (for source='other' untrusted uploads)
    op.alter_column(
        'gate_evidence',
        'sha256_hash',
        existing_type=sa.String(64),
        nullable=True,
    )

    # Add indexes for new columns
    op.create_index(
        'idx_gate_evidence_criteria_snapshot',
        'gate_evidence',
        ['criteria_snapshot_id'],
    )
    op.create_index(
        'idx_gate_evidence_source',
        'gate_evidence',
        ['source'],
    )


def downgrade() -> None:
    """Revert Sprint 173 schema changes."""

    # Drop indexes
    op.drop_index('idx_gate_evidence_source', table_name='gate_evidence')
    op.drop_index('idx_gate_evidence_criteria_snapshot', table_name='gate_evidence')

    # Revert sha256_hash to NOT NULL
    op.alter_column(
        'gate_evidence',
        'sha256_hash',
        existing_type=sa.String(64),
        nullable=False,
    )

    # Drop evidence contract columns
    op.drop_column('gate_evidence', 'source')
    op.drop_column('gate_evidence', 'criteria_snapshot_id')
    op.drop_column('gate_evidence', 'sha256_server')

    # Revert status values
    op.execute(
        "UPDATE gates SET status = 'PENDING_APPROVAL' WHERE status = 'SUBMITTED'"
    )
    op.execute(
        "UPDATE gates SET status = 'IN_PROGRESS' WHERE status = 'EVALUATED'"
    )

    # Drop gate state machine columns
    op.drop_column('gates', 'exit_criteria_version')
    op.drop_column('gates', 'evaluated_at')
