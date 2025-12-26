"""vcr_override_tables

Revision ID: p1k2l3m4n5o6
Revises: o0j1k2l3m4n5
Create Date: 2025-12-22 14:00:00.000000

SDLC Stage: 04 - BUILD
Sprint: 43 - Policy Guards & Evidence UI
Epic: EP-02 AI Safety Layer v1
Framework: SDLC 5.1.1

Purpose:
Create VCR (Version Controlled Resolution) Override tables.
Enables structured override workflow for failed AI code validations.

Tables:
1. validation_overrides - Override requests and resolutions
2. override_audit_logs - Immutable audit trail for compliance

VCR Flow:
1. Developer requests override (failed validation)
2. Request enters admin queue (PENDING)
3. Admin/Manager reviews and approves/rejects
4. If approved, validation_result updated to 'overridden'
5. All actions logged in audit trail

Retention:
- validation_overrides: 2 years (security audit requirement)
- override_audit_logs: 5 years (compliance requirement)

CTO Approval: Required for Day 8-9 Sprint 43
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID


# revision identifiers, used by Alembic.
revision = 'p1k2l3m4n5o6'
down_revision = 'o0j1k2l3m4n5'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create VCR override tables with indexes."""

    # ========================================================================
    # Table 1: validation_overrides (Override Requests - 2-year retention)
    # ========================================================================
    op.create_table(
        'validation_overrides',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),

        # Link to AI Code Event
        sa.Column('event_id', UUID(as_uuid=True), sa.ForeignKey('ai_code_events.id', ondelete='CASCADE'), nullable=False),

        # Project context (denormalized for faster queries)
        sa.Column('project_id', UUID(as_uuid=True), sa.ForeignKey('projects.id', ondelete='CASCADE'), nullable=False),

        # Request details
        sa.Column('override_type', sa.String(20), nullable=False,
            comment='false_positive, approved_risk, emergency'),
        sa.Column('reason', sa.Text, nullable=False,
            comment='Justification for override (min 50 chars)'),
        sa.Column('status', sa.String(20), nullable=False, server_default='pending',
            comment='pending, approved, rejected, expired, cancelled'),

        # Requester
        sa.Column('requested_by_id', UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('requested_at', sa.DateTime, nullable=False, server_default=sa.text('NOW()')),

        # Resolution
        sa.Column('resolved_by_id', UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('resolved_at', sa.DateTime, nullable=True),
        sa.Column('resolution_comment', sa.Text, nullable=True),

        # Metadata (denormalized for queue display)
        sa.Column('pr_number', sa.String(100), nullable=True, comment='Denormalized from ai_code_events'),
        sa.Column('pr_title', sa.String(500), nullable=True, comment='Denormalized from ai_code_events'),
        sa.Column('failed_validators', sa.Text, nullable=True, comment='JSON array of failed validator names'),

        # Expiry tracking
        sa.Column('expires_at', sa.DateTime, nullable=True, comment='7 days from created_at'),
        sa.Column('is_expired', sa.Boolean, default=False, server_default=sa.text('FALSE')),

        # Emergency override tracking
        sa.Column('post_merge_review_required', sa.Boolean, default=False, server_default=sa.text('FALSE')),
        sa.Column('post_merge_review_completed', sa.Boolean, default=False, server_default=sa.text('FALSE')),
        sa.Column('post_merge_reviewed_by_id', UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('post_merge_reviewed_at', sa.DateTime, nullable=True),

        # Timestamps
        sa.Column('created_at', sa.DateTime, nullable=False, server_default=sa.text('NOW()')),
        sa.Column('updated_at', sa.DateTime, nullable=False, server_default=sa.text('NOW()')),

        comment='VCR override requests for failed AI code validations. Tracks approval workflow. Retention: 2 years (security audit requirement).'
    )

    # Indexes for validation_overrides
    op.create_index(
        'ix_validation_overrides_event_id',
        'validation_overrides',
        ['event_id']
    )
    op.create_index(
        'ix_validation_overrides_project_id',
        'validation_overrides',
        ['project_id']
    )
    op.create_index(
        'ix_validation_overrides_status',
        'validation_overrides',
        ['status']
    )
    op.create_index(
        'ix_validation_overrides_override_type',
        'validation_overrides',
        ['override_type']
    )
    op.create_index(
        'ix_validation_overrides_requested_by_id',
        'validation_overrides',
        ['requested_by_id']
    )
    op.create_index(
        'ix_override_status_created',
        'validation_overrides',
        ['status', 'created_at']
    )
    op.create_index(
        'ix_override_project_status',
        'validation_overrides',
        ['project_id', 'status']
    )
    op.create_index(
        'ix_override_type_status',
        'validation_overrides',
        ['override_type', 'status']
    )
    op.create_index(
        'ix_override_expires',
        'validation_overrides',
        ['expires_at', 'is_expired']
    )
    op.create_index(
        'ix_override_created_at',
        'validation_overrides',
        ['created_at']
    )

    # ========================================================================
    # Table 2: override_audit_logs (Immutable Audit Trail - 5-year retention)
    # ========================================================================
    op.create_table(
        'override_audit_logs',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),

        # Link to override
        sa.Column('override_id', UUID(as_uuid=True), sa.ForeignKey('validation_overrides.id', ondelete='CASCADE'), nullable=False),

        # Action details
        sa.Column('action', sa.String(30), nullable=False,
            comment='request_created, request_updated, request_cancelled, approved, rejected, expired, escalated, comment_added'),
        sa.Column('action_by_id', UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('action_at', sa.DateTime, nullable=False, server_default=sa.text('NOW()')),

        # State snapshot
        sa.Column('previous_status', sa.String(20), nullable=True),
        sa.Column('new_status', sa.String(20), nullable=True),
        sa.Column('comment', sa.Text, nullable=True),

        # Forensics
        sa.Column('ip_address', sa.String(45), nullable=True, comment='IPv6 max length'),
        sa.Column('user_agent', sa.String(500), nullable=True),

        # Metadata
        sa.Column('metadata', sa.Text, nullable=True, comment='JSON for additional context'),

        comment='Immutable audit trail for override actions. Append-only for compliance. Retention: 5 years (SOC 2, HIPAA).'
    )

    # Indexes for override_audit_logs
    op.create_index(
        'ix_override_audit_logs_override_id',
        'override_audit_logs',
        ['override_id']
    )
    op.create_index(
        'ix_override_audit_logs_action',
        'override_audit_logs',
        ['action']
    )
    op.create_index(
        'ix_override_audit_logs_action_at',
        'override_audit_logs',
        ['action_at']
    )
    op.create_index(
        'ix_override_audit_logs_action_by',
        'override_audit_logs',
        ['action_by_id']
    )
    op.create_index(
        'ix_audit_override_action',
        'override_audit_logs',
        ['override_id', 'action']
    )

    # ========================================================================
    # Add relationship column to ai_code_events (for ORM relationship)
    # ========================================================================
    # Note: The foreign key is on validation_overrides.event_id,
    # so no schema change needed on ai_code_events.
    # Just ensure the ORM model has the relationship defined.


def downgrade() -> None:
    """Drop VCR override tables."""

    # Drop indexes first (PostgreSQL requires explicit drop)

    # override_audit_logs indexes
    op.drop_index('ix_audit_override_action', table_name='override_audit_logs')
    op.drop_index('ix_override_audit_logs_action_by', table_name='override_audit_logs')
    op.drop_index('ix_override_audit_logs_action_at', table_name='override_audit_logs')
    op.drop_index('ix_override_audit_logs_action', table_name='override_audit_logs')
    op.drop_index('ix_override_audit_logs_override_id', table_name='override_audit_logs')

    # validation_overrides indexes
    op.drop_index('ix_override_created_at', table_name='validation_overrides')
    op.drop_index('ix_override_expires', table_name='validation_overrides')
    op.drop_index('ix_override_type_status', table_name='validation_overrides')
    op.drop_index('ix_override_project_status', table_name='validation_overrides')
    op.drop_index('ix_override_status_created', table_name='validation_overrides')
    op.drop_index('ix_validation_overrides_requested_by_id', table_name='validation_overrides')
    op.drop_index('ix_validation_overrides_override_type', table_name='validation_overrides')
    op.drop_index('ix_validation_overrides_status', table_name='validation_overrides')
    op.drop_index('ix_validation_overrides_project_id', table_name='validation_overrides')
    op.drop_index('ix_validation_overrides_event_id', table_name='validation_overrides')

    # Drop tables (cascades to foreign keys)
    op.drop_table('override_audit_logs')
    op.drop_table('validation_overrides')
