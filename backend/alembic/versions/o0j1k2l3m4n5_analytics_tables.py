"""analytics_tables

Revision ID: o0j1k2l3m4n5
Revises: n9i0j1k2l3m4
Create Date: 2025-12-21 22:00:00.000000

SDLC Stage: 04 - BUILD
Sprint: 41 - AI Safety Foundation
Epic: EP-01/EP-02
Framework: SDLC 5.1.1

Purpose:
Create analytics_events and ai_code_events tables for product telemetry.
Supports dual approach (PostgreSQL + Mixpanel) per ADR-021.

Tables:
1. analytics_events - Product telemetry (90-day retention)
2. ai_code_events - AI Safety validation (2-year retention)

CTO Approval: ✅ ADR-021 approved December 21, 2025
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSON


# revision identifiers, used by Alembic.
revision = 'o0j1k2l3m4n5'
down_revision = 'n9i0j1k2l3m4'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create analytics tables with indexes."""

    # ========================================================================
    # Table 1: analytics_events (Product Telemetry - 90-day retention)
    # ========================================================================
    op.create_table(
        'analytics_events',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('user_id', UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('event_name', sa.String(100), nullable=False),
        sa.Column('properties', JSON, nullable=True, comment='Event metadata (max 100KB)'),
        sa.Column('created_at', sa.DateTime, nullable=False, server_default=sa.text('NOW()')),

        comment='Product analytics events - tracks user behavior, AI usage, SDLC gates. Retention: 90 days (GDPR compliance).'
    )

    # Indexes for analytics_events
    op.create_index(
        'ix_analytics_events_user_id',
        'analytics_events',
        ['user_id']
    )
    op.create_index(
        'ix_analytics_events_event_name',
        'analytics_events',
        ['event_name']
    )
    op.create_index(
        'ix_analytics_events_created_at',
        'analytics_events',
        ['created_at']
    )
    op.create_index(
        'ix_analytics_events_user_created',
        'analytics_events',
        ['user_id', 'created_at']
    )
    op.create_index(
        'ix_analytics_events_event_created',
        'analytics_events',
        ['event_name', 'created_at']
    )

    # ========================================================================
    # Table 2: ai_code_events (AI Safety Layer - 2-year retention)
    # ========================================================================
    op.create_table(
        'ai_code_events',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('user_id', UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('project_id', UUID(as_uuid=True), sa.ForeignKey('projects.id', ondelete='CASCADE'), nullable=False),

        # PR/Commit identification
        sa.Column('pr_id', sa.String(100), nullable=True, comment='GitHub PR number or internal UUID'),
        sa.Column('commit_sha', sa.String(40), nullable=True, comment='Git commit hash (40 chars)'),
        sa.Column('branch_name', sa.String(255), nullable=True),

        # AI Detection
        sa.Column('ai_tool_detected', sa.String(50), nullable=True, comment='claude, cursor, copilot, windsurf, continue, etc'),
        sa.Column('confidence_score', sa.Integer, nullable=True, comment='0-100 (ML model confidence)'),
        sa.Column('detection_method', sa.String(50), nullable=True, comment='pattern, ml, comment, metadata'),

        # SDLC Validation
        sa.Column('validation_result', sa.String(20), nullable=False, comment='passed, failed, warning'),
        sa.Column('violations', JSON, nullable=True, comment='Array of violation objects'),
        sa.Column('policy_pack_id', sa.String(100), nullable=True, comment='OPA policy pack used'),

        # Performance metrics
        sa.Column('duration_ms', sa.Integer, nullable=True, comment='Validation duration in milliseconds'),
        sa.Column('files_scanned', sa.Integer, nullable=True, comment='Number of files scanned'),
        sa.Column('lines_changed', sa.Integer, nullable=True, comment='Lines added + deleted'),

        # Audit trail
        sa.Column('created_at', sa.DateTime, nullable=False, server_default=sa.text('NOW()')),
        sa.Column('validated_by_user_id', UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),

        comment='AI-generated code detection and safety events. Tracks every PR/commit for AI tool usage. Retention: 2 years (security audit requirement).'
    )

    # Indexes for ai_code_events
    op.create_index(
        'ix_ai_code_events_user_id',
        'ai_code_events',
        ['user_id']
    )
    op.create_index(
        'ix_ai_code_events_project_id',
        'ai_code_events',
        ['project_id']
    )
    op.create_index(
        'ix_ai_code_events_pr_id',
        'ai_code_events',
        ['pr_id']
    )
    op.create_index(
        'ix_ai_code_events_commit_sha',
        'ai_code_events',
        ['commit_sha']
    )
    op.create_index(
        'ix_ai_code_events_ai_tool_detected',
        'ai_code_events',
        ['ai_tool_detected']
    )
    op.create_index(
        'ix_ai_code_events_validation_result',
        'ai_code_events',
        ['validation_result']
    )
    op.create_index(
        'ix_ai_code_events_created_at',
        'ai_code_events',
        ['created_at']
    )
    op.create_index(
        'ix_ai_code_events_project_created',
        'ai_code_events',
        ['project_id', 'created_at']
    )
    op.create_index(
        'ix_ai_code_events_tool_result',
        'ai_code_events',
        ['ai_tool_detected', 'validation_result']
    )
    op.create_index(
        'ix_ai_code_events_pr_commit',
        'ai_code_events',
        ['pr_id', 'commit_sha']
    )


def downgrade() -> None:
    """Drop analytics tables."""

    # Drop indexes first (PostgreSQL requires explicit drop)
    # ai_code_events indexes
    op.drop_index('ix_ai_code_events_pr_commit', table_name='ai_code_events')
    op.drop_index('ix_ai_code_events_tool_result', table_name='ai_code_events')
    op.drop_index('ix_ai_code_events_project_created', table_name='ai_code_events')
    op.drop_index('ix_ai_code_events_created_at', table_name='ai_code_events')
    op.drop_index('ix_ai_code_events_validation_result', table_name='ai_code_events')
    op.drop_index('ix_ai_code_events_ai_tool_detected', table_name='ai_code_events')
    op.drop_index('ix_ai_code_events_commit_sha', table_name='ai_code_events')
    op.drop_index('ix_ai_code_events_pr_id', table_name='ai_code_events')
    op.drop_index('ix_ai_code_events_project_id', table_name='ai_code_events')
    op.drop_index('ix_ai_code_events_user_id', table_name='ai_code_events')

    # analytics_events indexes
    op.drop_index('ix_analytics_events_event_created', table_name='analytics_events')
    op.drop_index('ix_analytics_events_user_created', table_name='analytics_events')
    op.drop_index('ix_analytics_events_created_at', table_name='analytics_events')
    op.drop_index('ix_analytics_events_event_name', table_name='analytics_events')
    op.drop_index('ix_analytics_events_user_id', table_name='analytics_events')

    # Drop tables (cascades to foreign keys)
    op.drop_table('ai_code_events')
    op.drop_table('analytics_events')
