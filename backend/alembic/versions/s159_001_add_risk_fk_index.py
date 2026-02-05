"""Sprint 159: Add index on manage_incidents.risk_id

Adds missing index on manage_incidents.risk_id foreign key for
performance optimization when querying incidents by associated risk.

Sprint: 159 - Technical Debt (NIST Polish)
Priority: P1
Reference: Sprint 158 Condition 6 (deferred optimization)

Migration: Add index only (FK already exists from s158_001)
Performance Target: <50ms for risk-to-incident queries

Revision ID: s159_001
Revises: s158_001
Create Date: 2026-05-05
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "s159_001"
down_revision: Union[str, None] = "s158_001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add index on manage_incidents.risk_id for query performance."""

    op.create_index(
        "ix_manage_incidents_risk_id",
        "manage_incidents",
        ["risk_id"],
        postgresql_where=sa.text("risk_id IS NOT NULL"),
    )


def downgrade() -> None:
    """Remove index on manage_incidents.risk_id."""

    op.drop_index(
        "ix_manage_incidents_risk_id",
        table_name="manage_incidents",
    )
