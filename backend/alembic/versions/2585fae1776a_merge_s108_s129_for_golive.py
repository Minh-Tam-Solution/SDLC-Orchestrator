"""merge_s108_s129_for_golive

Revision ID: 2585fae1776a
Revises: s108_001_governance, s129_001
Create Date: 2026-01-31 16:30:20.563171

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '2585fae1776a'
down_revision: Union[str, None] = ('s108_001_governance', 's129_001')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
