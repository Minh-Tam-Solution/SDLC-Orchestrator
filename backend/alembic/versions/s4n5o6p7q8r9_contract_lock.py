"""Add contract lock columns and audit log table

Revision ID: s4n5o6p7q8r9
Revises: r3m4n5o6p7q8
Create Date: 2025-12-26 10:00:00.000000

SDLC Stage: 04 - BUILD
Sprint: 53 Day 4 - Contract Lock
Epic: VS Code Extension + Contract Lock

Purpose:
Add contract lock functionality for specification immutability.
Lock columns on onboarding_sessions + audit log table.

Reference: Contract-Lock-API-Specification.md
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "s4n5o6p7q8r9"
down_revision: Union[str, None] = "r3m4n5o6p7q8"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add lock columns to onboarding_sessions
    op.add_column(
        "onboarding_sessions",
        sa.Column(
            "locked",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
            comment="Whether the specification is locked for generation",
        ),
    )
    op.add_column(
        "onboarding_sessions",
        sa.Column(
            "spec_hash",
            sa.String(128),
            nullable=True,
            comment="SHA256 hash of the locked specification (sha256:<hash>)",
        ),
    )
    op.add_column(
        "onboarding_sessions",
        sa.Column(
            "locked_at",
            sa.DateTime(timezone=True),
            nullable=True,
            comment="Timestamp when specification was locked",
        ),
    )
    op.add_column(
        "onboarding_sessions",
        sa.Column(
            "locked_by",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
            comment="User who locked the specification",
        ),
    )
    op.add_column(
        "onboarding_sessions",
        sa.Column(
            "lock_expires_at",
            sa.DateTime(timezone=True),
            nullable=True,
            comment="Auto-expiry time for orphaned locks (1 hour default)",
        ),
    )
    op.add_column(
        "onboarding_sessions",
        sa.Column(
            "lock_version",
            sa.Integer(),
            nullable=True,
            comment="Version counter for optimistic locking",
        ),
    )

    # Create index for finding locked sessions
    op.create_index(
        "ix_onboarding_sessions_locked",
        "onboarding_sessions",
        ["locked"],
        postgresql_where=sa.text("locked = true"),
    )

    # Create index for finding expired locks
    op.create_index(
        "ix_onboarding_sessions_lock_expires_at",
        "onboarding_sessions",
        ["lock_expires_at"],
        postgresql_where=sa.text("locked = true AND lock_expires_at IS NOT NULL"),
    )

    # Create lock_audit_log table
    op.create_table(
        "lock_audit_log",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "onboarding_session_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("onboarding_sessions.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column(
            "action",
            sa.String(20),
            nullable=False,
            comment="lock, unlock, force_unlock, auto_unlock",
        ),
        sa.Column(
            "actor_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "spec_hash",
            sa.String(128),
            nullable=True,
            comment="Hash at time of action",
        ),
        sa.Column(
            "reason",
            sa.Text(),
            nullable=True,
            comment="User-provided reason for action",
        ),
        sa.Column(
            "metadata",
            postgresql.JSONB(),
            nullable=True,
            comment="Additional context (source, version, etc)",
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
    )

    # Create index for querying by action type
    op.create_index(
        "ix_lock_audit_log_action",
        "lock_audit_log",
        ["action"],
    )

    # Create index for querying by time range
    op.create_index(
        "ix_lock_audit_log_created_at",
        "lock_audit_log",
        ["created_at"],
    )

    # Add table comment
    op.execute(
        """
        COMMENT ON TABLE lock_audit_log IS
        'Sprint 53: Audit log for contract lock operations. Tracks lock/unlock history for compliance.';
        """
    )


def downgrade() -> None:
    # Drop lock_audit_log table
    op.drop_index("ix_lock_audit_log_created_at", table_name="lock_audit_log")
    op.drop_index("ix_lock_audit_log_action", table_name="lock_audit_log")
    op.drop_table("lock_audit_log")

    # Drop indexes from onboarding_sessions
    op.drop_index(
        "ix_onboarding_sessions_lock_expires_at",
        table_name="onboarding_sessions",
    )
    op.drop_index(
        "ix_onboarding_sessions_locked",
        table_name="onboarding_sessions",
    )

    # Drop columns from onboarding_sessions
    op.drop_column("onboarding_sessions", "lock_version")
    op.drop_column("onboarding_sessions", "lock_expires_at")
    op.drop_column("onboarding_sessions", "locked_by")
    op.drop_column("onboarding_sessions", "locked_at")
    op.drop_column("onboarding_sessions", "spec_hash")
    op.drop_column("onboarding_sessions", "locked")
