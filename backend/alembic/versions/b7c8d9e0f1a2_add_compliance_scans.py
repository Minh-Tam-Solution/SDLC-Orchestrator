"""Add compliance_scans and compliance_violations tables

Revision ID: b7c8d9e0f1a2
Revises: a502ce0d23a7
Create Date: 2025-12-02 10:00:00.000000

Sprint 21 Day 1: Compliance Scanner Core
Foundation: Sprint 21 Plan, ADR-007 Approved
Authority: Backend Lead + CTO Approved

Tables Created:
- compliance_scans: Store scan results per project
- compliance_violations: Store individual violations with AI recommendations
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'b7c8d9e0f1a2'
down_revision: Union[str, None] = 'a502ce0d23a7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ========================================================================
    # compliance_scans table
    # ========================================================================
    op.create_table('compliance_scans',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('project_id', sa.UUID(), nullable=False),
        sa.Column('triggered_by', sa.UUID(), nullable=True),
        sa.Column('trigger_type', sa.String(length=50), nullable=False),
        sa.Column('compliance_score', sa.Integer(), nullable=False),
        sa.Column('violations_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('warnings_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('violations', postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default='[]'),
        sa.Column('warnings', postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default='[]'),
        sa.Column('scan_metadata', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('scanned_at', sa.DateTime(), nullable=False),
        sa.Column('duration_ms', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['triggered_by'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
        sa.CheckConstraint('compliance_score >= 0 AND compliance_score <= 100', name='ck_compliance_score_range')
    )
    op.create_index(op.f('ix_compliance_scans_id'), 'compliance_scans', ['id'], unique=False)
    op.create_index(op.f('ix_compliance_scans_project_id'), 'compliance_scans', ['project_id'], unique=False)
    op.create_index(op.f('ix_compliance_scans_triggered_by'), 'compliance_scans', ['triggered_by'], unique=False)
    op.create_index(op.f('ix_compliance_scans_scanned_at'), 'compliance_scans', ['scanned_at'], unique=False)
    op.create_index(op.f('ix_compliance_scans_compliance_score'), 'compliance_scans', ['compliance_score'], unique=False)
    # Composite index for recent scans per project
    op.create_index(
        'ix_compliance_scans_project_scanned',
        'compliance_scans',
        ['project_id', sa.text('scanned_at DESC')],
        unique=False
    )

    # ========================================================================
    # compliance_violations table
    # ========================================================================
    op.create_table('compliance_violations',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('scan_id', sa.UUID(), nullable=False),
        sa.Column('project_id', sa.UUID(), nullable=False),
        sa.Column('violation_type', sa.String(length=100), nullable=False),
        sa.Column('severity', sa.String(length=20), nullable=False),
        sa.Column('location', sa.String(length=1000), nullable=True),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('recommendation', sa.Text(), nullable=True),
        sa.Column('ai_recommendation', sa.Text(), nullable=True),
        sa.Column('ai_provider', sa.String(length=50), nullable=True),
        sa.Column('ai_confidence', sa.Integer(), nullable=True),
        sa.Column('is_resolved', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('resolved_by', sa.UUID(), nullable=True),
        sa.Column('resolved_at', sa.DateTime(), nullable=True),
        sa.Column('resolution_notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['scan_id'], ['compliance_scans.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['resolved_by'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_compliance_violations_id'), 'compliance_violations', ['id'], unique=False)
    op.create_index(op.f('ix_compliance_violations_scan_id'), 'compliance_violations', ['scan_id'], unique=False)
    op.create_index(op.f('ix_compliance_violations_project_id'), 'compliance_violations', ['project_id'], unique=False)
    op.create_index(op.f('ix_compliance_violations_violation_type'), 'compliance_violations', ['violation_type'], unique=False)
    op.create_index(op.f('ix_compliance_violations_severity'), 'compliance_violations', ['severity'], unique=False)
    op.create_index(op.f('ix_compliance_violations_is_resolved'), 'compliance_violations', ['is_resolved'], unique=False)
    # Composite index for unresolved violations per project
    op.create_index(
        'ix_compliance_violations_unresolved',
        'compliance_violations',
        ['project_id', 'is_resolved'],
        unique=False,
        postgresql_where=sa.text('is_resolved = false')
    )


def downgrade() -> None:
    # Drop compliance_violations table first (foreign key dependency)
    op.drop_index('ix_compliance_violations_unresolved', table_name='compliance_violations')
    op.drop_index(op.f('ix_compliance_violations_is_resolved'), table_name='compliance_violations')
    op.drop_index(op.f('ix_compliance_violations_severity'), table_name='compliance_violations')
    op.drop_index(op.f('ix_compliance_violations_violation_type'), table_name='compliance_violations')
    op.drop_index(op.f('ix_compliance_violations_project_id'), table_name='compliance_violations')
    op.drop_index(op.f('ix_compliance_violations_scan_id'), table_name='compliance_violations')
    op.drop_index(op.f('ix_compliance_violations_id'), table_name='compliance_violations')
    op.drop_table('compliance_violations')

    # Drop compliance_scans table
    op.drop_index('ix_compliance_scans_project_scanned', table_name='compliance_scans')
    op.drop_index(op.f('ix_compliance_scans_compliance_score'), table_name='compliance_scans')
    op.drop_index(op.f('ix_compliance_scans_scanned_at'), table_name='compliance_scans')
    op.drop_index(op.f('ix_compliance_scans_triggered_by'), table_name='compliance_scans')
    op.drop_index(op.f('ix_compliance_scans_project_id'), table_name='compliance_scans')
    op.drop_index(op.f('ix_compliance_scans_id'), table_name='compliance_scans')
    op.drop_table('compliance_scans')
