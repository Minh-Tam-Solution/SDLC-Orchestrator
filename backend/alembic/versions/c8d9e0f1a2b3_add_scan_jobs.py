"""Add scan_jobs table for persistent job queue

Revision ID: c8d9e0f1a2b3
Revises: b7c8d9e0f1a2
Create Date: 2025-12-02 14:00:00.000000

Sprint 21 Day 2 P0 Fix: Job Persistence
Foundation: CTO Code Review - P1-FIX-06
Authority: Backend Lead + CTO Approved

Tables Created:
- scan_jobs: Persistent queue for background compliance scan jobs
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'c8d9e0f1a2b3'
down_revision: Union[str, None] = 'b7c8d9e0f1a2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ========================================================================
    # scan_jobs table - Persistent job queue
    # ========================================================================
    op.create_table('scan_jobs',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('project_id', sa.UUID(), nullable=False),
        sa.Column('triggered_by', sa.UUID(), nullable=True),
        sa.Column('trigger_type', sa.String(length=50), nullable=False),
        sa.Column('priority', sa.String(length=20), nullable=False, server_default='normal'),
        sa.Column('include_doc_code_sync', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('status', sa.String(length=20), nullable=False, server_default='queued'),
        sa.Column('queued_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('started_at', sa.DateTime(), nullable=True),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.Column('result', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('error', sa.Text(), nullable=True),
        sa.Column('retry_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('max_retries', sa.Integer(), nullable=False, server_default='3'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['triggered_by'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )

    # Indexes for efficient job queue operations
    op.create_index(op.f('ix_scan_jobs_id'), 'scan_jobs', ['id'], unique=False)
    op.create_index(op.f('ix_scan_jobs_project_id'), 'scan_jobs', ['project_id'], unique=False)
    op.create_index(op.f('ix_scan_jobs_triggered_by'), 'scan_jobs', ['triggered_by'], unique=False)
    op.create_index(op.f('ix_scan_jobs_status'), 'scan_jobs', ['status'], unique=False)
    op.create_index(op.f('ix_scan_jobs_priority'), 'scan_jobs', ['priority'], unique=False)
    op.create_index(op.f('ix_scan_jobs_queued_at'), 'scan_jobs', ['queued_at'], unique=False)

    # Composite index for job queue polling (status + priority + queued_at)
    op.create_index(
        'ix_scan_jobs_queue_order',
        'scan_jobs',
        ['status', 'priority', 'queued_at'],
        unique=False,
        postgresql_where=sa.text("status = 'queued'")
    )


def downgrade() -> None:
    op.drop_index('ix_scan_jobs_queue_order', table_name='scan_jobs')
    op.drop_index(op.f('ix_scan_jobs_queued_at'), table_name='scan_jobs')
    op.drop_index(op.f('ix_scan_jobs_priority'), table_name='scan_jobs')
    op.drop_index(op.f('ix_scan_jobs_status'), table_name='scan_jobs')
    op.drop_index(op.f('ix_scan_jobs_triggered_by'), table_name='scan_jobs')
    op.drop_index(op.f('ix_scan_jobs_project_id'), table_name='scan_jobs')
    op.drop_index(op.f('ix_scan_jobs_id'), table_name='scan_jobs')
    op.drop_table('scan_jobs')
