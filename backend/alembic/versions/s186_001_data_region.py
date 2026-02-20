"""s186_001_data_region — add data_region to projects table

Revision ID: s186001
Revises: s185001
Create Date: 2026-02-20

Sprint 186 — Multi-Region Data Residency (ADR-063)
Expert 5 de-scope: storage-level residency only (MinIO/S3 bucket per region).
DB remains single-region (Vietnam primary). Full multi-region DB deferred
until first EU enterprise contract is signed.

Change:
  ALTER TABLE projects ADD COLUMN data_region VARCHAR(10) DEFAULT 'VN'

Valid values (enforced by CHECK constraint):
  VN  — Vietnam / Singapore (Asia Pacific primary)
  EU  — Frankfurt (EU data residency, GDPR)
  US  — US East (future)

Index:
  ix_projects_data_region — filter projects by region (tenant routing queries)

Rollback:
  DROP COLUMN data_region (safe — nullable with default, no data loss)
"""

import sqlalchemy as sa
from alembic import op

revision = "s186001"
down_revision = "s185001"
branch_labels = None
depends_on = None

# Valid region codes — kept as a DB CHECK constraint so application-level bugs
# cannot persist invalid region codes.
_VALID_REGIONS = ("VN", "EU", "US")
_CHECK_NAME = "ck_projects_data_region"


def upgrade() -> None:
    # -------------------------------------------------------------------------
    # 1. Add data_region column with default 'VN' (all existing projects → VN)
    # -------------------------------------------------------------------------
    op.add_column(
        "projects",
        sa.Column(
            "data_region",
            sa.String(10),
            nullable=False,
            server_default="VN",
        ),
    )

    # -------------------------------------------------------------------------
    # 2. CHECK constraint — prevent invalid region codes from being stored
    # -------------------------------------------------------------------------
    op.create_check_constraint(
        _CHECK_NAME,
        "projects",
        sa.text("data_region IN ('VN', 'EU', 'US')"),
    )

    # -------------------------------------------------------------------------
    # 3. Index for regional routing queries (ENTERPRISE tier: route by region)
    # -------------------------------------------------------------------------
    op.create_index(
        "ix_projects_data_region",
        "projects",
        ["data_region"],
    )


def downgrade() -> None:
    op.drop_index("ix_projects_data_region", table_name="projects")
    op.drop_constraint(_CHECK_NAME, "projects", type_="check")
    op.drop_column("projects", "data_region")
