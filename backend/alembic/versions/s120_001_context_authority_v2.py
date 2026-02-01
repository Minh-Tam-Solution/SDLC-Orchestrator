"""Sprint 120: Context Authority V2 - Gate-Aware Dynamic Context

Revision ID: s120_001_context_authority_v2
Revises: s118_001_governance_v2_tables
Create Date: 2026-01-29 18:00:00.000000

Creates tables for Context Authority V2 (SPEC-0011):
1. ca_v2_overlay_templates - Dynamic overlay templates
2. ca_v2_context_snapshots - Point-in-time context for audit
3. ca_v2_overlay_applications - Track template applications

Note: All tables use ca_v2_* prefix to avoid conflict with Sprint 108
context_snapshots table in governance module.

Reference:
- SPEC-0011: Context Authority V2 - Gate-Aware Dynamic Context
- ADR-041: Framework 6.0 Governance System Design
- Sprint 120 Plan: SPRINT-120-CONTEXT-AUTHORITY-V2-GATES.md
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 's120_001_context_authority_v2'
down_revision = 's118_001_governance_v2_tables'
branch_labels = None
depends_on = None


def upgrade():
    # =========================================================================
    # Table 1: ca_v2_overlay_templates
    # Dynamic overlay templates for gate-aware context injection
    # =========================================================================
    op.create_table(
        'ca_v2_overlay_templates',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('trigger_type', sa.String(50), nullable=False, index=True,
                  comment='Trigger type: gate_pass, gate_fail, index_zone, stage_constraint'),
        sa.Column('trigger_value', sa.String(100), nullable=False, index=True,
                  comment='Trigger value: G0.2, G1, green, yellow, orange, red'),
        sa.Column('tier', sa.String(20), nullable=True, index=True,
                  comment='Tier scope: NULL=all, or LITE/STANDARD/PROFESSIONAL/ENTERPRISE'),
        sa.Column('overlay_content', sa.Text(), nullable=False,
                  comment='Template content with {variable} placeholders'),
        sa.Column('priority', sa.Integer(), nullable=False, server_default='0',
                  comment='Priority for ordering (higher = first)'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true',
                  comment='Whether template is active'),
        sa.Column('name', sa.String(200), nullable=False,
                  comment='Human-readable template name'),
        sa.Column('description', sa.Text(), nullable=True,
                  comment='Template description'),
        sa.Column('created_by_id', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.func.now(), onupdate=sa.func.now()),
        # Check constraints
        sa.CheckConstraint(
            "trigger_type IN ('gate_pass', 'gate_fail', 'index_zone', 'stage_constraint')",
            name='ck_ca_v2_overlay_templates_trigger_type'
        ),
        sa.CheckConstraint(
            "tier IS NULL OR tier IN ('LITE', 'STANDARD', 'PROFESSIONAL', 'ENTERPRISE')",
            name='ck_ca_v2_overlay_templates_tier'
        ),
    )

    # Composite index for template lookup
    op.create_index(
        'idx_ca_v2_overlay_templates_trigger_lookup',
        'ca_v2_overlay_templates',
        ['trigger_type', 'trigger_value', 'tier', 'is_active']
    )

    # Priority index
    op.create_index(
        'idx_ca_v2_overlay_templates_priority',
        'ca_v2_overlay_templates',
        ['priority'],
        postgresql_ops={'priority': 'DESC'}
    )

    # =========================================================================
    # Table 2: ca_v2_context_snapshots
    # Point-in-time context for audit trail
    # =========================================================================
    op.create_table(
        'ca_v2_context_snapshots',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('submission_id', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('governance_submissions.id', ondelete='CASCADE'),
                  nullable=False, index=True,
                  comment='Governance submission this snapshot belongs to'),
        sa.Column('project_id', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('projects.id', ondelete='CASCADE'),
                  nullable=False, index=True,
                  comment='Project this snapshot belongs to'),
        # Gate status at snapshot time
        sa.Column('gate_status', postgresql.JSONB(), nullable=False,
                  comment='Gate status: {current_stage, last_passed_gate, pending_gates}'),
        # Vibecoding index
        sa.Column('vibecoding_index', sa.Integer(), nullable=False,
                  comment='Vibecoding index (0-100)'),
        sa.Column('vibecoding_zone', sa.String(20), nullable=False,
                  comment='Zone: GREEN, YELLOW, ORANGE, RED'),
        # Dynamic overlay
        sa.Column('dynamic_overlay', sa.Text(), nullable=False,
                  comment='Dynamic overlay content generated'),
        # V1 and V2 results
        sa.Column('v1_result', postgresql.JSONB(), nullable=True,
                  comment='V1 validation result (ADR linkage, design doc, etc.)'),
        sa.Column('gate_violations', postgresql.JSONB(), nullable=True,
                  comment='Gate constraint violations'),
        sa.Column('index_warnings', postgresql.JSONB(), nullable=True,
                  comment='Vibecoding index warnings'),
        # Tier and validity
        sa.Column('tier', sa.String(20), nullable=False,
                  comment='Project tier at validation time'),
        sa.Column('is_valid', sa.Boolean(), nullable=False, index=True,
                  comment='Overall validation result'),
        # Applied templates
        sa.Column('applied_template_ids', postgresql.JSONB(), nullable=True,
                  comment='Array of template IDs applied'),
        # Timestamps
        sa.Column('snapshot_at', sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.func.now(), index=True,
                  comment='Snapshot creation timestamp'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.func.now()),
        # Check constraints
        sa.CheckConstraint(
            "vibecoding_zone IN ('GREEN', 'YELLOW', 'ORANGE', 'RED')",
            name='ck_ca_v2_context_snapshots_zone'
        ),
        sa.CheckConstraint(
            "tier IN ('LITE', 'STANDARD', 'PROFESSIONAL', 'ENTERPRISE')",
            name='ck_ca_v2_context_snapshots_tier'
        ),
    )

    # BRIN index for time-series queries
    op.execute("""
        CREATE INDEX idx_ca_v2_context_snapshots_snapshot_at_brin
        ON ca_v2_context_snapshots USING brin (snapshot_at);
    """)

    # Composite index for project-based queries
    op.create_index(
        'idx_ca_v2_context_snapshots_project_time',
        'ca_v2_context_snapshots',
        ['project_id', 'snapshot_at']
    )

    # Validity index
    op.create_index(
        'idx_ca_v2_context_snapshots_validity',
        'ca_v2_context_snapshots',
        ['is_valid', 'snapshot_at']
    )

    # =========================================================================
    # Table 3: ca_v2_overlay_applications
    # Track template applications to snapshots
    # =========================================================================
    op.create_table(
        'ca_v2_overlay_applications',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('snapshot_id', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('ca_v2_context_snapshots.id', ondelete='CASCADE'),
                  nullable=False, index=True,
                  comment='Snapshot where template was applied'),
        sa.Column('template_id', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('ca_v2_overlay_templates.id', ondelete='CASCADE'),
                  nullable=False, index=True,
                  comment='Template that was applied'),
        sa.Column('template_content_snapshot', sa.Text(), nullable=False,
                  comment='Template content at application time (immutable)'),
        sa.Column('rendered_content', sa.Text(), nullable=False,
                  comment='Rendered content after variable substitution'),
        sa.Column('variables_used', postgresql.JSONB(), nullable=True,
                  comment='Variables used for rendering'),
        sa.Column('application_order', sa.Integer(), nullable=False, server_default='0',
                  comment='Order in final overlay'),
        sa.Column('applied_at', sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.func.now(),
                  comment='Application timestamp'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.func.now()),
        # Unique constraint
        sa.UniqueConstraint('snapshot_id', 'template_id',
                           name='uq_ca_v2_overlay_applications_snapshot_template'),
    )

    # Index for template usage analytics
    op.create_index(
        'idx_ca_v2_overlay_applications_template_usage',
        'ca_v2_overlay_applications',
        ['template_id', 'applied_at']
    )

    # =========================================================================
    # Seed Default Templates (SPEC-0011)
    # =========================================================================
    op.execute("""
        INSERT INTO ca_v2_overlay_templates (
            id, trigger_type, trigger_value, tier, overlay_content, priority,
            is_active, name, description, created_at, updated_at
        ) VALUES
        -- Gate Pass Templates
        (
            gen_random_uuid(), 'gate_pass', 'G0.2', NULL,
            E'## 🎯 Current Status: Design Approved\\n\\nGate G0.2 (Solution Diversity) PASSED on {date}.\\n\\n**You may now:**\\n- Write code in `backend/app/` and `frontend/src/`\\n- Create new services and components\\n- Implement features per approved ADRs\\n\\n**Required for all code:**\\n- Link to ADR: `@adr ADR-XXX` in file header\\n- Test coverage: 80% minimum\\n- BDD format for new features\\n\\n**Reference:**\\n- Architecture: docs/02-design/03-ADRs/\\n- Specs: docs/02-design/14-Technical-Specs/',
            100, true, 'Gate G0.2 Pass - Design Approved',
            'Shown when Gate G0.2 (Solution Diversity) passes',
            NOW(), NOW()
        ),
        (
            gen_random_uuid(), 'gate_pass', 'G2', NULL,
            E'## ✅ Build Phase Active\\n\\nGate G2 (Design Ready) PASSED on {date}.\\n\\n**Build phase guidelines:**\\n- Follow approved architecture in ADRs\\n- Maintain 95%+ test coverage\\n- Run SAST scans before PR\\n- No new features without spec',
            90, true, 'Gate G2 Pass - Build Active',
            'Shown when Gate G2 (Design Ready) passes',
            NOW(), NOW()
        ),
        -- Index Zone Templates
        (
            gen_random_uuid(), 'index_zone', 'orange', NULL,
            E'## ⚠️ Vibecoding Index: ORANGE ({index})\\n\\nThis submission requires Tech Lead review before merge.\\n\\n**Contributing signals:**\\n{top_signals}\\n\\n**Suggested Actions:**\\n- Review architectural patterns\\n- Reduce AI dependency ratio\\n- Consider breaking into smaller PRs\\n\\n**Escalation:**\\n- Queue: Tech Lead Review\\n- SLA: 4 hours',
            80, true, 'Orange Zone Warning',
            'Shown when vibecoding index is in Orange zone (61-80)',
            NOW(), NOW()
        ),
        (
            gen_random_uuid(), 'index_zone', 'red', NULL,
            E'## 🚫 Vibecoding Index: RED ({index})\\n\\nThis submission is BLOCKED and requires CEO review.\\n\\n**Critical signals:**\\n{top_signals}\\n\\n**Immediate Actions Required:**\\n- Do NOT merge without CEO approval\\n- Review code for anti-patterns\\n- Consider major refactoring\\n\\n**Escalation:**\\n- Queue: CEO Immediate Attention\\n- SLA: 1 hour',
            100, true, 'Red Zone Block',
            'Shown when vibecoding index is in Red zone (81-100)',
            NOW(), NOW()
        ),
        -- Stage Constraint Templates
        (
            gen_random_uuid(), 'stage_constraint', 'stage_02_code_block', NULL,
            E'## 🚫 Stage Constraint: Code Blocked\\n\\nCurrent Stage: **02 - Design**\\n\\n**Code changes are blocked because:**\\n- Architecture not yet approved (Gate G2 pending)\\n- Design documents incomplete\\n\\n**To proceed:**\\n1. Complete ADRs: docs/02-design/03-ADRs/\\n2. Request Gate G2 review: `sdlcctl gate request G2`\\n3. Wait for approval\\n\\n**Allowed changes in Stage 02:**\\n- docs/02-design/**\\n- prisma/schema.prisma (schema design only)\\n- openapi/** (API contracts)',
            100, true, 'Stage 02 Code Block',
            'Shown when code changes attempted in Stage 02 (Design)',
            NOW(), NOW()
        );
    """)


def downgrade():
    # Drop tables in reverse order (respecting FKs)
    op.drop_table('ca_v2_overlay_applications')
    op.drop_table('ca_v2_context_snapshots')
    op.drop_table('ca_v2_overlay_templates')
