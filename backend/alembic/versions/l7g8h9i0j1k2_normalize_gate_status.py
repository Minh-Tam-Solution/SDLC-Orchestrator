"""
Normalize gate status values to UPPERCASE.

Revision ID: l7g8h9i0j1k2
Revises: k6f7g8h9i0j1
Create Date: 2025-12-16

SDLC 5.1.1 Compliance:
- Ensures data consistency with model definition
- Gate status should be: DRAFT, PENDING_APPROVAL, APPROVED, REJECTED, ARCHIVED
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers
revision = 'l7g8h9i0j1k2'
down_revision = 'j5e6f7g8h9i0'  # Points to last active migration
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Normalize all gate status values to UPPERCASE."""
    # Update lowercase status values to UPPERCASE
    op.execute("""
        UPDATE gates SET status = 'APPROVED' WHERE status = 'approved';
    """)
    op.execute("""
        UPDATE gates SET status = 'REJECTED' WHERE status = 'rejected';
    """)
    op.execute("""
        UPDATE gates SET status = 'PENDING_APPROVAL' WHERE status = 'pending_approval';
    """)
    op.execute("""
        UPDATE gates SET status = 'PENDING_APPROVAL' WHERE status = 'pending';
    """)
    op.execute("""
        UPDATE gates SET status = 'DRAFT' WHERE status = 'draft';
    """)
    op.execute("""
        UPDATE gates SET status = 'IN_PROGRESS' WHERE status = 'in_progress';
    """)
    op.execute("""
        UPDATE gates SET status = 'ARCHIVED' WHERE status = 'archived';
    """)

    # Also normalize gate_approvals status
    op.execute("""
        UPDATE gate_approvals SET status = 'APPROVED' WHERE status = 'approved';
    """)
    op.execute("""
        UPDATE gate_approvals SET status = 'REJECTED' WHERE status = 'rejected';
    """)
    op.execute("""
        UPDATE gate_approvals SET status = 'PENDING' WHERE status = 'pending';
    """)


def downgrade() -> None:
    """No downgrade needed - uppercase is the correct format."""
    pass
