"""Sprint 80: AGENTS.md Integration Tables

Revision ID: s80_agents_md_tables
Revises: s78_sprint_templates
Create Date: 2026-01-19 16:00:00.000000

Implements ADR-029 AGENTS.md Integration:
- agents_md_files: Generated AGENTS.md history per project
- context_overlays: Dynamic context overlay audit log

Per Technical Design Document TDS-080-001.
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB


# revision identifiers, used by Alembic.
revision = 's80_agents_md_tables'
down_revision = 's78_sprint_templates'
branch_labels = None
depends_on = None


def upgrade():
    # =========================================================================
    # Table 1: agents_md_files
    # Stores generated AGENTS.md history per project for audit
    # =========================================================================
    op.create_table(
        'agents_md_files',
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

        # Content
        sa.Column('content', sa.Text, nullable=False),
        sa.Column('content_hash', sa.String(64), nullable=False),  # SHA256
        sa.Column('line_count', sa.Integer, nullable=False),
        sa.Column('sections', JSONB, nullable=False, server_default='[]'),

        # Generation metadata
        sa.Column(
            'generated_at',
            sa.DateTime(timezone=True),
            server_default=sa.text('NOW()'),
            nullable=False,
        ),
        sa.Column(
            'generated_by',
            UUID(as_uuid=True),
            sa.ForeignKey('users.id', ondelete='SET NULL'),
            nullable=True,
        ),
        sa.Column('generator_version', sa.String(20), nullable=False),  # e.g., "1.0.0"
        sa.Column('source_analysis', JSONB, nullable=True),  # Files analyzed, configs found

        # Validation
        sa.Column(
            'validation_status',
            sa.String(20),
            nullable=False,
            server_default='pending',
        ),
        sa.Column('validation_errors', JSONB, nullable=True, server_default='[]'),
        sa.Column('validation_warnings', JSONB, nullable=True, server_default='[]'),

        # Audit timestamps
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
    )

    # Constraints
    op.create_check_constraint(
        'chk_agents_md_line_count',
        'agents_md_files',
        'line_count > 0 AND line_count <= 200',
    )
    op.create_check_constraint(
        'chk_agents_md_validation_status',
        'agents_md_files',
        "validation_status IN ('pending', 'valid', 'invalid')",
    )

    # Indexes
    op.create_index(
        'idx_agents_md_files_project_id',
        'agents_md_files',
        ['project_id'],
    )
    op.create_index(
        'idx_agents_md_files_generated_at',
        'agents_md_files',
        [sa.text('generated_at DESC')],
    )
    op.create_index(
        'idx_agents_md_files_content_hash',
        'agents_md_files',
        ['content_hash'],
    )

    # =========================================================================
    # Table 2: context_overlays
    # Stores generated context overlays for audit (NOT committed to git)
    # =========================================================================
    op.create_table(
        'context_overlays',
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

        # Context data
        sa.Column('stage_name', sa.String(50), nullable=True),
        sa.Column('gate_status', sa.String(50), nullable=True),
        sa.Column(
            'sprint_id',
            UUID(as_uuid=True),
            sa.ForeignKey('sprints.id', ondelete='SET NULL'),
            nullable=True,
        ),
        sa.Column('sprint_number', sa.Integer, nullable=True),
        sa.Column('sprint_goal', sa.Text, nullable=True),

        # Constraints (stored as JSONB array)
        # Example: [{"type": "strict_mode", "severity": "warning", "message": "..."}]
        sa.Column('constraints', JSONB, nullable=False, server_default='[]'),

        # Flags
        sa.Column('strict_mode', sa.Boolean, nullable=False, server_default='false'),

        # Trigger info
        sa.Column(
            'generated_at',
            sa.DateTime(timezone=True),
            server_default=sa.text('NOW()'),
            nullable=False,
        ),
        sa.Column(
            'trigger_type',
            sa.String(30),
            nullable=False,
        ),  # pr_webhook, cli, api, scheduled, manual
        sa.Column('trigger_ref', sa.String(255), nullable=True),  # PR number, CLI session

        # Delivery tracking
        sa.Column('delivered_to_pr', sa.Boolean, server_default='false'),
        sa.Column('delivered_to_check_run', sa.Boolean, server_default='false'),
        sa.Column('pr_comment_id', sa.BigInteger, nullable=True),  # GitHub comment ID
        sa.Column('check_run_id', sa.BigInteger, nullable=True),   # GitHub check run ID

        # Audit
        sa.Column(
            'created_at',
            sa.DateTime(timezone=True),
            server_default=sa.text('NOW()'),
            nullable=False,
        ),
    )

    # Constraints
    op.create_check_constraint(
        'chk_context_overlay_trigger_type',
        'context_overlays',
        "trigger_type IN ('pr_webhook', 'cli', 'api', 'scheduled', 'manual')",
    )

    # Indexes
    op.create_index(
        'idx_context_overlays_project_id',
        'context_overlays',
        ['project_id'],
    )
    op.create_index(
        'idx_context_overlays_generated_at',
        'context_overlays',
        [sa.text('generated_at DESC')],
    )
    op.create_index(
        'idx_context_overlays_trigger',
        'context_overlays',
        ['trigger_type', 'trigger_ref'],
    )
    op.create_index(
        'idx_context_overlays_pr',
        'context_overlays',
        ['pr_comment_id'],
        postgresql_where=sa.text('pr_comment_id IS NOT NULL'),
    )

    # =========================================================================
    # View: v_latest_agents_md
    # Latest AGENTS.md file per project for quick lookup
    # =========================================================================
    op.execute("""
        CREATE OR REPLACE VIEW v_latest_agents_md AS
        SELECT DISTINCT ON (project_id)
            id,
            project_id,
            content,
            content_hash,
            line_count,
            sections,
            generated_at,
            generator_version,
            validation_status,
            validation_errors,
            validation_warnings
        FROM agents_md_files
        ORDER BY project_id, generated_at DESC;
    """)


def downgrade():
    # Drop view first
    op.execute("DROP VIEW IF EXISTS v_latest_agents_md;")

    # Drop tables
    op.drop_table('context_overlays')
    op.drop_table('agents_md_files')
