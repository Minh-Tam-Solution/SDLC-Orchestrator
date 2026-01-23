"""Sprint 104: Maturity Assessments Table (L0-L3)

Revision ID: s104_001_maturity_assessments
Revises: s103_001_framework_versions
Create Date: 2026-01-23 18:00:00.000000

Implements SDLC 5.2.0 Agentic Maturity Model:
- Track maturity assessment history per project
- Store level (L0/L1/L2/L3), score (0-100), features
- Enable compliance reporting and level progression tracking

Maturity Levels:
  - L0: MANUAL (0-20) - No AI assistance
  - L1: ASSISTANT (21-50) - AI suggests, human decides
  - L2: ORCHESTRATED (51-80) - Agent workflows, human oversight
  - L3: AUTONOMOUS (81-100) - Agents act, human audits

Why track maturity?
- Organizations need to understand AI adoption level
- Policy enforcement varies by maturity
- Training/onboarding tailored to current maturity
- Migration paths: L0 → L1 → L2 → L3

Reference: docs/04-build/02-Sprint-Plans/SPRINT-104-DESIGN.md
Reference: SDLC Framework 5.2.0, 03-AI-GOVERNANCE
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID


# revision identifiers, used by Alembic.
revision = 's104_001_maturity_assessments'
down_revision = 's103_001_framework_versions'
branch_labels = None
depends_on = None


def upgrade():
    # =========================================================================
    # Table: maturity_assessments
    # Track agentic maturity assessments per project.
    #
    # Purpose:
    #   - Record maturity level (L0/L1/L2/L3) per assessment
    #   - Store feature analysis (enabled/disabled)
    #   - Track improvement recommendations
    #   - Enable compliance reporting
    # =========================================================================
    op.create_table(
        'maturity_assessments',
        sa.Column(
            'id',
            UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text('gen_random_uuid()'),
        ),
        sa.Column(
            'project_id',
            UUID(as_uuid=True),
            sa.ForeignKey('projects.id', ondelete='CASCADE'),
            nullable=False,
            index=True,
        ),

        # Assessment Results
        sa.Column(
            'level',
            sa.String(10),
            nullable=False,
            comment='Maturity level: L0, L1, L2, L3',
        ),
        sa.Column(
            'score',
            sa.Integer(),
            nullable=False,
            comment='Maturity score: 0-100',
        ),

        # Feature Analysis (stored as JSON arrays)
        sa.Column(
            'enabled_features',
            sa.JSON(),
            nullable=False,
            server_default='[]',
            comment='List of enabled feature names',
        ),
        sa.Column(
            'disabled_features',
            sa.JSON(),
            nullable=False,
            server_default='[]',
            comment='List of disabled feature names',
        ),
        sa.Column(
            'recommendations',
            sa.JSON(),
            nullable=False,
            server_default='[]',
            comment='List of improvement recommendations',
        ),
        sa.Column(
            'factor_details',
            sa.JSON(),
            nullable=True,
            comment='Detailed factor scoring breakdown',
        ),

        # Timestamps
        sa.Column(
            'assessed_at',
            sa.DateTime(timezone=True),
            server_default=sa.text('NOW()'),
            nullable=False,
            index=True,
            comment='When assessment was performed',
        ),
    )

    # Composite index for common queries
    op.create_index(
        'idx_maturity_project_assessed',
        'maturity_assessments',
        ['project_id', 'assessed_at'],
    )

    # Add check constraint for valid level values
    op.create_check_constraint(
        'maturity_level_check',
        'maturity_assessments',
        "level IN ('L0', 'L1', 'L2', 'L3')",
    )

    # Add check constraint for valid score range
    op.create_check_constraint(
        'maturity_score_check',
        'maturity_assessments',
        'score >= 0 AND score <= 100',
    )

    # Add table comments
    op.execute("""
        COMMENT ON TABLE maturity_assessments IS
        'Agentic maturity assessments per project for SDLC 5.2.0 compliance';

        COMMENT ON COLUMN maturity_assessments.level IS
        'Maturity level: L0 (Manual), L1 (Assistant), L2 (Orchestrated), L3 (Autonomous)';

        COMMENT ON COLUMN maturity_assessments.score IS
        'Maturity score 0-100. L0: 0-20, L1: 21-50, L2: 51-80, L3: 81-100';
    """)


def downgrade():
    op.drop_constraint('maturity_score_check', 'maturity_assessments', type_='check')
    op.drop_constraint('maturity_level_check', 'maturity_assessments', type_='check')
    op.drop_index('idx_maturity_project_assessed', table_name='maturity_assessments')
    op.drop_table('maturity_assessments')
