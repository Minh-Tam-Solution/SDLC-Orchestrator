"""Add performance optimization indexes

Revision ID: f1a2b3c4d5e6
Revises: e0f1a2b3c4d5
Create Date: 2025-12-03 14:30:00.000000

Sprint 23 Day 3: Database Indexing for Performance
Authority: Backend Lead + CTO Approved

Changes:
- Add composite index on gates(project_id, status, deleted_at) for gate statistics
- Add composite index on projects(deleted_at, updated_at) for list queries
- Add partial index on gates WHERE deleted_at IS NULL for soft-delete optimization
- Add partial index on projects WHERE deleted_at IS NULL for soft-delete optimization
- Add index on gates(project_id, stage) for stage aggregation

Performance Impact:
- list_projects: Expected 30-50% improvement on large datasets
- get_project: Expected 20-30% improvement for gate queries
- Compliance scans: Expected 40-60% improvement for gate lookups
"""
from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = 'f1a2b3c4d5e6'
down_revision: Union[str, None] = 'e0f1a2b3c4d5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Composite index for gate statistics query (used in list_projects)
    # Covers: COUNT(*), SUM(CASE WHEN status = ...), MAX(stage)
    op.create_index(
        'ix_gates_project_status_deleted',
        'gates',
        ['project_id', 'status', 'deleted_at'],
        unique=False,
    )

    # Composite index for project list ordering
    # Covers: WHERE deleted_at IS NULL ORDER BY updated_at DESC
    op.create_index(
        'ix_projects_deleted_updated',
        'projects',
        ['deleted_at', 'updated_at'],
        unique=False,
    )

    # Composite index for stage aggregation
    # Covers: MAX(stage) GROUP BY project_id
    op.create_index(
        'ix_gates_project_stage',
        'gates',
        ['project_id', 'stage'],
        unique=False,
    )

    # Partial index for active gates (soft-delete optimization)
    # Covers: WHERE deleted_at IS NULL (very selective for most queries)
    op.create_index(
        'ix_gates_active',
        'gates',
        ['project_id'],
        unique=False,
        postgresql_where='deleted_at IS NULL',
    )

    # Partial index for active projects (soft-delete optimization)
    # Covers: WHERE deleted_at IS NULL ORDER BY updated_at DESC
    op.create_index(
        'ix_projects_active_updated',
        'projects',
        ['updated_at'],
        unique=False,
        postgresql_where='deleted_at IS NULL',
    )

    # Partial index for active users (login queries)
    # Note: users table uses is_active flag instead of soft-delete
    op.create_index(
        'ix_users_active_email',
        'users',
        ['email'],
        unique=False,
        postgresql_where='is_active = true',
    )

    # Index for compliance scans by project
    op.create_index(
        'ix_compliance_scans_project_created',
        'compliance_scans',
        ['project_id', 'created_at'],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index('ix_compliance_scans_project_created', table_name='compliance_scans')
    op.drop_index('ix_users_active_email', table_name='users')
    op.drop_index('ix_projects_active_updated', table_name='projects')
    op.drop_index('ix_gates_active', table_name='gates')
    op.drop_index('ix_gates_project_stage', table_name='gates')
    op.drop_index('ix_projects_deleted_updated', table_name='projects')
    op.drop_index('ix_gates_project_status_deleted', table_name='gates')
