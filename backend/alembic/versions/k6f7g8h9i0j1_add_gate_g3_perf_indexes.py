"""Add Gate G3 performance indexes

Revision ID: k6f7g8h9i0j1
Revises: j5e6f7g8h9i0
Create Date: 2025-12-09 14:30:00.000000

Sprint 31 Day 2: Gate G3 Performance Optimization
Authority: Backend Lead + CTO Approved

Purpose:
Add additional performance indexes identified during Sprint 31 bottleneck analysis
to meet Gate G3 performance targets (<100ms p95, >1000 req/s).

New Indexes:
1. ix_gate_approvals_gate_id - Approval lookups by gate
2. ix_gate_evidence_gate_id_active - Evidence count (partial index)
3. ix_policy_evaluations_gate_id - Policy violations lookup
4. ix_evidence_metadata_gate_id - Evidence metadata search
5. ix_sdlc_validations_project_recent - Recent validations lookup

Performance Impact:
- Gate detail queries: Expected 40-60% improvement
- Evidence count: Expected 50-70% improvement
- Policy violations: Expected 30-50% improvement
- SDLC validation history: Expected 60-80% improvement
"""
from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = 'k6f7g8h9i0j1'
down_revision: Union[str, None] = 'j5e6f7g8h9i0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Index for gate approvals lookup (used in get_gate_approvals)
    op.create_index(
        'ix_gate_approvals_gate_id',
        'gate_approvals',
        ['gate_id', 'approved_at'],
        unique=False,
        if_not_exists=True,  # Handle duplicate gracefully (Sprint 33 Day 3 fix)
    )

    # Partial index for active evidence count (soft-delete optimization)
    op.create_index(
        'ix_gate_evidence_gate_active',
        'gate_evidence',
        ['gate_id'],
        unique=False,
        postgresql_where='deleted_at IS NULL',
        if_not_exists=True,
    )

    # Index for policy evaluations by gate (violations lookup)
    op.create_index(
        'ix_policy_evaluations_gate_passed',
        'policy_evaluations',
        ['gate_id', 'is_passed'],
        unique=False,
        if_not_exists=True,
    )

    # Composite index for evidence metadata search
    op.create_index(
        'ix_evidence_metadata_gate_type',
        'evidence',
        ['gate_id', 'evidence_type', 'created_at'],
        unique=False,
        if_not_exists=True,
    )

    # Index for SDLC validation history (recent first)
    op.create_index(
        'ix_sdlc_validations_project_recent',
        'sdlc_validations',
        ['project_id', 'created_at'],
        unique=False,
        postgresql_ops={'created_at': 'DESC'},
        if_not_exists=True,
    )

    # Index for compliance summary aggregation
    op.create_index(
        'ix_sdlc_validations_project_score',
        'sdlc_validations',
        ['project_id', 'compliance_score'],
        unique=False,
        if_not_exists=True,
    )

    # Index for feedback queries by project
    op.create_index(
        'ix_feedback_project_created',
        'feedback',
        ['project_id', 'created_at'],
        unique=False,
        if_not_exists=True,
    )

    # Index for usage tracking aggregation
    op.create_index(
        'ix_usage_tracking_user_action',
        'usage_tracking',
        ['user_id', 'action_type', 'created_at'],
        unique=False,
        if_not_exists=True,
    )


def downgrade() -> None:
    op.drop_index('ix_usage_tracking_user_action', table_name='usage_tracking')
    op.drop_index('ix_feedback_project_created', table_name='feedback')
    op.drop_index('ix_sdlc_validations_project_score', table_name='sdlc_validations')
    op.drop_index('ix_sdlc_validations_project_recent', table_name='sdlc_validations')
    op.drop_index('ix_evidence_metadata_gate_type', table_name='evidence')
    op.drop_index('ix_policy_evaluations_gate_passed', table_name='policy_evaluations')
    op.drop_index('ix_gate_evidence_gate_active', table_name='gate_evidence')
    op.drop_index('ix_gate_approvals_gate_id', table_name='gate_approvals')
