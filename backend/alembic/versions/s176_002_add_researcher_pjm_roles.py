"""Sprint 176: Add researcher and pjm to SDLCRole enum (P0 ecosystem fix)

Revision ID: s176_002
Revises: s176_001
Create Date: 2026-02-18 18:00:00.000000

CONTEXT:
- TinySDLC expanded SDLC roles from 6 → 8 per SDLC 6.0.6:
    researcher (Stage 00-01, Gate G0.1)
    pjm — Project Manager (Stage 01-04, Gate G-Sprint)
- Orchestrator's check constraint ck_agent_definitions_sdlc_role only allows 6 values
- P0 fix: blocks TinySDLC → Orchestrator message forwarding if not updated

CTO REVIEW:
- Finding 1 from CTO review of TinySDLC Status Report (2026-02-18)
- Priority: P0 (blocks ecosystem compatibility)
"""

from alembic import op


# revision identifiers
revision = "s176_002"
down_revision = "s176_001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Drop old 6-role constraint
    op.drop_constraint(
        "ck_agent_definitions_sdlc_role",
        "agent_definitions",
        type_="check",
    )

    # Create new 8-role constraint (added: researcher, pjm)
    op.create_check_constraint(
        "ck_agent_definitions_sdlc_role",
        "agent_definitions",
        "sdlc_role IN ('researcher', 'pm', 'pjm', 'architect', 'coder', 'reviewer', 'tester', 'devops')",
    )


def downgrade() -> None:
    # Revert to 6-role constraint
    op.drop_constraint(
        "ck_agent_definitions_sdlc_role",
        "agent_definitions",
        type_="check",
    )

    op.create_check_constraint(
        "ck_agent_definitions_sdlc_role",
        "agent_definitions",
        "sdlc_role IN ('pm', 'architect', 'coder', 'reviewer', 'tester', 'devops')",
    )
