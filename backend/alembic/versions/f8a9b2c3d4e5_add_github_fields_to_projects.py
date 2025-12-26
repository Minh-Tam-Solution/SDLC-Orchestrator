"""add_github_fields_to_projects

Revision ID: f8a9b2c3d4e5
Revises: a502ce0d23a7
Create Date: 2025-12-02 10:00:00.000000

=========================================================================
Database Migration - Add GitHub Fields to Projects (Sprint 15)
SDLC Orchestrator - Stage 03 (BUILD)

Version: 1.0.0
Date: December 2, 2025
Status: ACTIVE - Sprint 15 Day 4
Authority: Backend Lead + CTO Approved
Foundation: Sprint 15 Plan, User-Onboarding-Flow-Architecture.md
Framework: SDLC 4.9 Complete Lifecycle

Purpose:
- Add GitHub integration fields to projects table
- Enable repository sync and tracking
- Support first-time user onboarding flow

Fields Added:
- github_repo_id: GitHub repository ID (integer)
- github_repo_full_name: Full repository name (owner/repo)
- github_sync_status: Sync status (pending, syncing, synced, error)
- github_synced_at: Last sync timestamp

Indexes:
- idx_projects_github_repo_id: Fast lookup by GitHub repo ID

Zero Mock Policy: Real database migration, production-ready
=========================================================================
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'f8a9b2c3d4e5'
down_revision = 'a502ce0d23a7'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add GitHub fields to projects table."""
    # Add GitHub repository ID (nullable, can be added later)
    op.add_column('projects', sa.Column('github_repo_id', sa.Integer(), nullable=True))
    
    # Add GitHub repository full name (owner/repo format)
    op.add_column('projects', sa.Column('github_repo_full_name', sa.String(length=500), nullable=True))
    
    # Add GitHub sync status (default: 'pending')
    op.add_column('projects', sa.Column('github_sync_status', sa.String(length=50), nullable=True, server_default='pending'))
    
    # Add GitHub sync timestamp
    op.add_column('projects', sa.Column('github_synced_at', sa.DateTime(), nullable=True))
    
    # Create index for fast GitHub repo lookup
    op.create_index('idx_projects_github_repo_id', 'projects', ['github_repo_id'], unique=False)


def downgrade() -> None:
    """Remove GitHub fields from projects table."""
    # Drop index
    op.drop_index('idx_projects_github_repo_id', table_name='projects')
    
    # Drop columns
    op.drop_column('projects', 'github_synced_at')
    op.drop_column('projects', 'github_sync_status')
    op.drop_column('projects', 'github_repo_full_name')
    op.drop_column('projects', 'github_repo_id')

