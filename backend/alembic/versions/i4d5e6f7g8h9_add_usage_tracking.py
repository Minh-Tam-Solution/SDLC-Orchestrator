"""Add usage tracking tables

Revision ID: i4d5e6f7g8h9
Revises: h3c4d5e6f7g8
Create Date: 2025-12-04 10:00:00.000000

Sprint 24 Day 4: Usage Tracking
Authority: Backend Lead + CTO Approved

Changes:
- Add user_sessions table for session tracking
- Add usage_events table for event logging
- Add feature_usage table for aggregated stats
- Add pilot_metrics table for pilot dashboard
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB


# revision identifiers, used by Alembic.
revision: str = 'i4d5e6f7g8h9'
down_revision: Union[str, None] = 'h3c4d5e6f7g8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create usage tracking tables."""
    conn = op.get_bind()

    # Create user_sessions table
    conn.execute(sa.text("""
        CREATE TABLE IF NOT EXISTS user_sessions (
            id UUID PRIMARY KEY,
            user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            session_token VARCHAR(255) NOT NULL UNIQUE,
            started_at TIMESTAMP NOT NULL DEFAULT NOW(),
            ended_at TIMESTAMP,
            is_active BOOLEAN DEFAULT TRUE,
            duration_seconds INTEGER,
            user_agent VARCHAR(512),
            ip_address VARCHAR(45),
            device_type VARCHAR(50),
            browser VARCHAR(100),
            os VARCHAR(100),
            country VARCHAR(100),
            city VARCHAR(100),
            page_views_count INTEGER DEFAULT 0,
            events_count INTEGER DEFAULT 0
        )
    """))

    # Create usage_events table
    conn.execute(sa.text("""
        CREATE TABLE IF NOT EXISTS usage_events (
            id UUID PRIMARY KEY,
            user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            session_id UUID REFERENCES user_sessions(id) ON DELETE CASCADE,
            event_type VARCHAR(50) NOT NULL,
            event_name VARCHAR(100) NOT NULL,
            timestamp TIMESTAMP NOT NULL DEFAULT NOW(),
            page_url VARCHAR(512),
            referrer_url VARCHAR(512),
            resource_type VARCHAR(50),
            resource_id UUID,
            metadata JSONB,
            duration_ms INTEGER
        )
    """))

    # Create feature_usage table
    conn.execute(sa.text("""
        CREATE TABLE IF NOT EXISTS feature_usage (
            id UUID PRIMARY KEY,
            date TIMESTAMP NOT NULL,
            period_type VARCHAR(20) DEFAULT 'daily',
            feature_name VARCHAR(100) NOT NULL,
            feature_category VARCHAR(50),
            total_uses INTEGER DEFAULT 0,
            unique_users INTEGER DEFAULT 0,
            avg_duration_ms INTEGER,
            success_count INTEGER DEFAULT 0,
            failure_count INTEGER DEFAULT 0,
            created_at TIMESTAMP NOT NULL DEFAULT NOW(),
            updated_at TIMESTAMP NOT NULL DEFAULT NOW()
        )
    """))

    # Create pilot_metrics table
    conn.execute(sa.text("""
        CREATE TABLE IF NOT EXISTS pilot_metrics (
            id UUID PRIMARY KEY,
            date TIMESTAMP NOT NULL,
            period_type VARCHAR(20) DEFAULT 'daily',
            total_users INTEGER DEFAULT 0,
            active_users INTEGER DEFAULT 0,
            new_users INTEGER DEFAULT 0,
            total_sessions INTEGER DEFAULT 0,
            avg_session_duration INTEGER DEFAULT 0,
            total_page_views INTEGER DEFAULT 0,
            users_using_gates INTEGER DEFAULT 0,
            users_using_evidence INTEGER DEFAULT 0,
            users_using_compliance INTEGER DEFAULT 0,
            gates_evaluated INTEGER DEFAULT 0,
            gates_passed INTEGER DEFAULT 0,
            gates_failed INTEGER DEFAULT 0,
            evidence_uploaded INTEGER DEFAULT 0,
            evidence_size_bytes INTEGER DEFAULT 0,
            compliance_scans INTEGER DEFAULT 0,
            avg_compliance_score INTEGER,
            feedback_submitted INTEGER DEFAULT 0,
            bugs_reported INTEGER DEFAULT 0,
            features_requested INTEGER DEFAULT 0,
            created_at TIMESTAMP NOT NULL DEFAULT NOW()
        )
    """))

    # Create indexes for user_sessions
    conn.execute(sa.text("CREATE INDEX IF NOT EXISTS ix_user_sessions_id ON user_sessions(id)"))
    conn.execute(sa.text("CREATE INDEX IF NOT EXISTS ix_user_sessions_user_id ON user_sessions(user_id)"))
    conn.execute(sa.text("CREATE INDEX IF NOT EXISTS ix_user_sessions_token ON user_sessions(session_token)"))
    conn.execute(sa.text("CREATE INDEX IF NOT EXISTS ix_user_sessions_active ON user_sessions(is_active)"))
    conn.execute(sa.text("CREATE INDEX IF NOT EXISTS ix_user_sessions_started ON user_sessions(started_at)"))

    # Create indexes for usage_events
    conn.execute(sa.text("CREATE INDEX IF NOT EXISTS ix_usage_events_id ON usage_events(id)"))
    conn.execute(sa.text("CREATE INDEX IF NOT EXISTS ix_usage_events_user_id ON usage_events(user_id)"))
    conn.execute(sa.text("CREATE INDEX IF NOT EXISTS ix_usage_events_session_id ON usage_events(session_id)"))
    conn.execute(sa.text("CREATE INDEX IF NOT EXISTS ix_usage_events_type ON usage_events(event_type)"))
    conn.execute(sa.text("CREATE INDEX IF NOT EXISTS ix_usage_events_name ON usage_events(event_name)"))
    conn.execute(sa.text("CREATE INDEX IF NOT EXISTS ix_usage_events_timestamp ON usage_events(timestamp)"))
    conn.execute(sa.text("CREATE INDEX IF NOT EXISTS ix_usage_events_resource ON usage_events(resource_id)"))

    # Create indexes for feature_usage
    conn.execute(sa.text("CREATE INDEX IF NOT EXISTS ix_feature_usage_id ON feature_usage(id)"))
    conn.execute(sa.text("CREATE INDEX IF NOT EXISTS ix_feature_usage_date ON feature_usage(date)"))
    conn.execute(sa.text("CREATE INDEX IF NOT EXISTS ix_feature_usage_name ON feature_usage(feature_name)"))

    # Create indexes for pilot_metrics
    conn.execute(sa.text("CREATE INDEX IF NOT EXISTS ix_pilot_metrics_id ON pilot_metrics(id)"))
    conn.execute(sa.text("CREATE INDEX IF NOT EXISTS ix_pilot_metrics_date ON pilot_metrics(date)"))


def downgrade() -> None:
    """Drop usage tracking tables."""
    op.drop_table('pilot_metrics')
    op.drop_table('feature_usage')
    op.drop_table('usage_events')
    op.drop_table('user_sessions')
