"""Sprint 100: Decomposition Hints Table (EP-11 Feedback Loop)

Revision ID: s100_001_decomposition_hints
Revises: s94_001_pr_learnings
Create Date: 2026-01-23 10:00:00.000000

Implements EP-11 Feedback Loop Closure - Decomposition Hints:
- decomposition_hints: Store extracted patterns for AI planning improvement
- Enable continuous improvement of AI task decomposition

Reference: docs/02-design/14-Technical-Specs/Feedback-Learning-Service-Design.md
Expert Workflow Analysis: "Learning from Code Reviews" → Decomposition Hints
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB


# revision identifiers, used by Alembic.
revision = 's100_001_decomposition_hints'
down_revision = 's94_001_pr_learnings'
branch_labels = None
depends_on = None


def upgrade():
    # =========================================================================
    # Table: decomposition_hints
    # Stores extracted patterns from PR learnings for AI planning improvement.
    # These hints guide AI task decomposition to avoid common mistakes.
    #
    # Hint Types:
    #   - pattern: Reusable code pattern to follow
    #   - antipattern: Common mistake to avoid
    #   - convention: Team/project naming/structure convention
    #   - checklist: Items to verify before completion
    #   - dependency: Hidden dependencies to consider
    #
    # Workflow:
    #   1. Extract hints from pr_learnings (monthly aggregation)
    #   2. AI references hints during task decomposition
    #   3. Hints improve quality of generated plans
    #   4. Feedback loop closes when hint prevents future errors
    # =========================================================================
    op.create_table(
        'decomposition_hints',
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

        # Hint Classification
        sa.Column(
            'hint_type',
            sa.String(30),
            nullable=False,
            index=True,
        ),  # pattern, antipattern, convention, checklist, dependency
        sa.Column(
            'category',
            sa.String(50),
            nullable=False,
            index=True,
        ),  # e.g., security, testing, architecture, naming, error_handling
        sa.Column('subcategory', sa.String(50), nullable=True),

        # Hint Content
        sa.Column('title', sa.String(255), nullable=False),
        sa.Column('description', sa.Text, nullable=False),
        sa.Column('example_good', sa.Text, nullable=True),
        sa.Column('example_bad', sa.Text, nullable=True),
        sa.Column('rationale', sa.Text, nullable=True),

        # Applicability
        sa.Column(
            'applies_to',
            JSONB,
            nullable=False,
            server_default='["all"]',
        ),  # ["frontend", "backend", "api", "database", "all"]
        sa.Column(
            'languages',
            JSONB,
            nullable=False,
            server_default='["all"]',
        ),  # ["python", "typescript", "all"]
        sa.Column(
            'frameworks',
            JSONB,
            nullable=False,
            server_default='["all"]',
        ),  # ["react", "fastapi", "all"]

        # Source Learning
        sa.Column(
            'source_learning_id',
            UUID(as_uuid=True),
            sa.ForeignKey('pr_learnings.id', ondelete='SET NULL'),
            nullable=True,
        ),
        sa.Column(
            'aggregation_id',
            UUID(as_uuid=True),
            sa.ForeignKey('learning_aggregations.id', ondelete='SET NULL'),
            nullable=True,
        ),

        # Quality Metrics
        sa.Column(
            'confidence',
            sa.Float,
            nullable=False,
            server_default='0.8',
        ),  # 0.0 - 1.0, based on source quality
        sa.Column(
            'usage_count',
            sa.Integer,
            nullable=False,
            server_default='0',
        ),  # How many times used in decomposition
        sa.Column(
            'effectiveness_score',
            sa.Float,
            nullable=True,
        ),  # Computed: prevented errors / usage count
        sa.Column(
            'prevented_errors',
            sa.Integer,
            nullable=False,
            server_default='0',
        ),
        sa.Column('last_used_at', sa.DateTime(timezone=True), nullable=True),

        # Status
        sa.Column(
            'status',
            sa.String(20),
            nullable=False,
            server_default='active',
            index=True,
        ),  # active, deprecated, merged, archived
        sa.Column('deprecated_reason', sa.Text, nullable=True),
        sa.Column(
            'merged_into_id',
            UUID(as_uuid=True),
            sa.ForeignKey('decomposition_hints.id', ondelete='SET NULL'),
            nullable=True,
        ),

        # AI Processing
        sa.Column('ai_generated', sa.Boolean, server_default='true'),
        sa.Column('ai_model', sa.String(50), nullable=True),
        sa.Column('human_verified', sa.Boolean, server_default='false'),
        sa.Column(
            'verified_by',
            UUID(as_uuid=True),
            sa.ForeignKey('users.id', ondelete='SET NULL'),
            nullable=True,
        ),
        sa.Column('verified_at', sa.DateTime(timezone=True), nullable=True),

        # Tagging
        sa.Column('tags', JSONB, nullable=True, server_default='[]'),
        sa.Column('related_adrs', JSONB, nullable=True, server_default='[]'),

        # Audit
        sa.Column(
            'created_at',
            sa.DateTime(timezone=True),
            server_default=sa.text('NOW()'),
            nullable=False,
        ),
        sa.Column(
            'updated_at',
            sa.DateTime(timezone=True),
            server_default=sa.text('NOW()'),
            nullable=False,
        ),
        sa.Column(
            'created_by',
            UUID(as_uuid=True),
            sa.ForeignKey('users.id', ondelete='SET NULL'),
            nullable=True,
        ),

        # Check constraints
        sa.CheckConstraint(
            "hint_type IN ('pattern', 'antipattern', 'convention', 'checklist', 'dependency')",
            name='decomposition_hints_type_check',
        ),
        sa.CheckConstraint(
            "status IN ('active', 'deprecated', 'merged', 'archived')",
            name='decomposition_hints_status_check',
        ),
        sa.CheckConstraint(
            "confidence >= 0 AND confidence <= 1",
            name='decomposition_hints_confidence_check',
        ),
    )

    # Indexes for common queries
    op.create_index(
        'idx_decomposition_hints_project_type',
        'decomposition_hints',
        ['project_id', 'hint_type'],
    )
    op.create_index(
        'idx_decomposition_hints_project_category',
        'decomposition_hints',
        ['project_id', 'category'],
    )
    op.create_index(
        'idx_decomposition_hints_active',
        'decomposition_hints',
        ['project_id', 'status'],
        postgresql_where=sa.text("status = 'active'"),
    )
    op.create_index(
        'idx_decomposition_hints_effectiveness',
        'decomposition_hints',
        ['project_id', 'effectiveness_score'],
        postgresql_where=sa.text("effectiveness_score IS NOT NULL"),
    )

    # =========================================================================
    # Table: hint_usage_logs
    # Track when hints are used during task decomposition for effectiveness
    # =========================================================================
    op.create_table(
        'hint_usage_logs',
        sa.Column(
            'id',
            UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text('gen_random_uuid()'),
        ),
        sa.Column(
            'hint_id',
            UUID(as_uuid=True),
            sa.ForeignKey('decomposition_hints.id', ondelete='CASCADE'),
            nullable=False,
            index=True,
        ),
        sa.Column(
            'project_id',
            UUID(as_uuid=True),
            sa.ForeignKey('projects.id', ondelete='CASCADE'),
            nullable=False,
            index=True,
        ),

        # Context
        sa.Column('decomposition_session_id', UUID(as_uuid=True), nullable=True),
        sa.Column('task_description', sa.Text, nullable=True),
        sa.Column('plan_generated', sa.Text, nullable=True),

        # Outcome
        sa.Column(
            'outcome',
            sa.String(30),
            nullable=True,
        ),  # prevented_error, no_effect, false_positive
        sa.Column('pr_id', sa.Integer, nullable=True),  # If linked to a PR
        sa.Column('error_prevented', sa.Boolean, server_default='false'),
        sa.Column('feedback', sa.Text, nullable=True),

        # Audit
        sa.Column(
            'used_at',
            sa.DateTime(timezone=True),
            server_default=sa.text('NOW()'),
            nullable=False,
        ),
        sa.Column(
            'used_by',
            UUID(as_uuid=True),
            sa.ForeignKey('users.id', ondelete='SET NULL'),
            nullable=True,
        ),
    )

    # Index for tracking hint effectiveness
    op.create_index(
        'idx_hint_usage_logs_hint_outcome',
        'hint_usage_logs',
        ['hint_id', 'outcome'],
    )

    # Add table comments
    op.execute("""
        COMMENT ON TABLE decomposition_hints IS 'AI decomposition hints extracted from PR learnings (EP-11)';
        COMMENT ON COLUMN decomposition_hints.hint_type IS 'Type: pattern (follow), antipattern (avoid), convention, checklist, dependency';
        COMMENT ON COLUMN decomposition_hints.effectiveness_score IS 'Computed: prevented_errors / usage_count';
        COMMENT ON COLUMN decomposition_hints.confidence IS 'AI confidence in hint accuracy (0.0-1.0)';
    """)

    op.execute("""
        COMMENT ON TABLE hint_usage_logs IS 'Track hint usage for effectiveness scoring';
        COMMENT ON COLUMN hint_usage_logs.outcome IS 'Result: prevented_error, no_effect, false_positive';
    """)


def downgrade():
    # Drop indexes first
    op.drop_index('idx_hint_usage_logs_hint_outcome', table_name='hint_usage_logs')
    op.drop_index('idx_decomposition_hints_effectiveness', table_name='decomposition_hints')
    op.drop_index('idx_decomposition_hints_active', table_name='decomposition_hints')
    op.drop_index('idx_decomposition_hints_project_category', table_name='decomposition_hints')
    op.drop_index('idx_decomposition_hints_project_type', table_name='decomposition_hints')

    # Drop tables
    op.drop_table('hint_usage_logs')
    op.drop_table('decomposition_hints')
