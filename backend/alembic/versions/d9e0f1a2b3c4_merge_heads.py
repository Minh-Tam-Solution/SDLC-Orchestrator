"""Merge compliance and github branches

Revision ID: d9e0f1a2b3c4
Revises: c8d9e0f1a2b3, f8a9b2c3d4e5
Create Date: 2025-12-02 09:05:00.000000

Merge migration to resolve multiple heads:
- Branch 1: compliance_scans → scan_jobs (c8d9e0f1a2b3)
- Branch 2: github_fields (f8a9b2c3d4e5)

Authority: Backend Lead + CTO Approved
"""
from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = 'd9e0f1a2b3c4'
down_revision: Union[str, Sequence[str]] = ('c8d9e0f1a2b3', 'f8a9b2c3d4e5')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Merge migration - no changes needed
    pass


def downgrade() -> None:
    # Merge migration - no changes needed
    pass
