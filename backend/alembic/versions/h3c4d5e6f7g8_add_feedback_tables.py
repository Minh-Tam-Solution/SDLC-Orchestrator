"""Add pilot feedback tables

Revision ID: h3c4d5e6f7g8
Revises: g2b3c4d5e6f7
Create Date: 2025-12-03 23:00:00.000000

Sprint 24 Day 2: Pilot Onboarding Guide
Authority: Backend Lead + CTO Approved

Changes:
- Add pilot_feedback table for bug reports and feature requests
- Add feedback_comments table for discussion
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID


# revision identifiers, used by Alembic.
revision: str = 'h3c4d5e6f7g8'
down_revision: Union[str, None] = 'g2b3c4d5e6f7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create pilot feedback tables."""
    conn = op.get_bind()

    # Create enums using raw SQL with IF NOT EXISTS
    conn.execute(sa.text("""
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'feedbacktype') THEN
                CREATE TYPE feedbacktype AS ENUM ('bug', 'feature_request', 'improvement', 'question', 'other');
            END IF;
            IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'feedbackpriority') THEN
                CREATE TYPE feedbackpriority AS ENUM ('p0_critical', 'p1_high', 'p2_medium', 'p3_low');
            END IF;
            IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'feedbackstatus') THEN
                CREATE TYPE feedbackstatus AS ENUM ('new', 'triaged', 'in_progress', 'resolved', 'closed', 'wont_fix');
            END IF;
        END$$;
    """))

    # Create pilot_feedback table using raw SQL
    conn.execute(sa.text("""
        CREATE TABLE IF NOT EXISTS pilot_feedback (
            id UUID PRIMARY KEY,
            user_id UUID REFERENCES users(id) ON DELETE SET NULL,
            type feedbacktype NOT NULL DEFAULT 'other',
            priority feedbackpriority,
            status feedbackstatus NOT NULL DEFAULT 'new',
            title VARCHAR(255) NOT NULL,
            description TEXT NOT NULL,
            steps_to_reproduce TEXT,
            expected_behavior TEXT,
            actual_behavior TEXT,
            browser VARCHAR(100),
            os VARCHAR(100),
            screenshot_url VARCHAR(512),
            page_url VARCHAR(512),
            created_at TIMESTAMP NOT NULL DEFAULT NOW(),
            updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
            resolved_at TIMESTAMP,
            resolved_by UUID REFERENCES users(id) ON DELETE SET NULL,
            resolution_notes TEXT
        )
    """))

    # Create feedback_comments table
    conn.execute(sa.text("""
        CREATE TABLE IF NOT EXISTS feedback_comments (
            id UUID PRIMARY KEY,
            feedback_id UUID NOT NULL REFERENCES pilot_feedback(id) ON DELETE CASCADE,
            user_id UUID REFERENCES users(id) ON DELETE SET NULL,
            content TEXT NOT NULL,
            created_at TIMESTAMP NOT NULL DEFAULT NOW(),
            updated_at TIMESTAMP NOT NULL DEFAULT NOW()
        )
    """))

    # Create indexes
    conn.execute(sa.text("CREATE INDEX IF NOT EXISTS ix_pilot_feedback_id ON pilot_feedback(id)"))
    conn.execute(sa.text("CREATE INDEX IF NOT EXISTS ix_pilot_feedback_user_id ON pilot_feedback(user_id)"))
    conn.execute(sa.text("CREATE INDEX IF NOT EXISTS ix_pilot_feedback_type ON pilot_feedback(type)"))
    conn.execute(sa.text("CREATE INDEX IF NOT EXISTS ix_pilot_feedback_status ON pilot_feedback(status)"))
    conn.execute(sa.text("CREATE INDEX IF NOT EXISTS ix_pilot_feedback_priority ON pilot_feedback(priority)"))
    conn.execute(sa.text("CREATE INDEX IF NOT EXISTS ix_pilot_feedback_created_at ON pilot_feedback(created_at)"))
    conn.execute(sa.text("CREATE INDEX IF NOT EXISTS ix_feedback_comments_id ON feedback_comments(id)"))
    conn.execute(sa.text("CREATE INDEX IF NOT EXISTS ix_feedback_comments_feedback_id ON feedback_comments(feedback_id)"))


def downgrade() -> None:
    """Drop pilot feedback tables."""
    op.drop_table('feedback_comments')
    op.drop_table('pilot_feedback')

    # Drop enums
    op.execute("DROP TYPE IF EXISTS feedbackstatus")
    op.execute("DROP TYPE IF EXISTS feedbackpriority")
    op.execute("DROP TYPE IF EXISTS feedbacktype")
