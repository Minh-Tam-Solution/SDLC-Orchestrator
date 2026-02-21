"""Sprint 177: Expand SDLCRole from 8 to 12 (SASE 3-type classification)

Revision ID: s177_001
Revises: s176_002
Create Date: 2026-02-18 22:00:00.000000

CONTEXT:
- ADR-056 §12.5 defines 12-role SASE classification:
    SE4A (8): researcher, pm, pjm, architect, coder, reviewer, tester, devops
    SE4H (3): ceo, cpo, cto  (Agent Coaches — human + AI advisory)
    Router (1): assistant  (guides users to correct agent/workflow)
- Expands check constraint from 8 → 12 values
- Sprint 176 constraint (s176_002) had 8 roles; this adds 4 more

CTO REVIEW:
- Plan approved with 5 amendments (Sprint 176 Phase 1)
- ADR-056 §12.5 SASE Role Classification locked
- Reference: arXiv:2509.06216v2 (Software Agentic Software Engineering)
"""

from alembic import op


# revision identifiers
revision = "s177_001"
down_revision = "s176_002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Drop Sprint 176 8-role constraint
    op.drop_constraint(
        "ck_agent_definitions_sdlc_role",
        "agent_definitions",
        type_="check",
    )

    # Create 12-role constraint (SASE 3-type: SE4A + SE4H + Router)
    op.create_check_constraint(
        "ck_agent_definitions_sdlc_role",
        "agent_definitions",
        "sdlc_role IN ("
        "'researcher', 'pm', 'pjm', 'architect', 'coder', 'reviewer', 'tester', 'devops', "
        "'ceo', 'cpo', 'cto', 'assistant'"
        ")",
    )


def downgrade() -> None:
    # Revert to Sprint 176 8-role constraint
    op.drop_constraint(
        "ck_agent_definitions_sdlc_role",
        "agent_definitions",
        type_="check",
    )

    op.create_check_constraint(
        "ck_agent_definitions_sdlc_role",
        "agent_definitions",
        "sdlc_role IN ("
        "'researcher', 'pm', 'pjm', 'architect', 'coder', 'reviewer', 'tester', 'devops'"
        ")",
    )
