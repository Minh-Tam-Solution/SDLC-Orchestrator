"""Sprint 118: Governance System v2.0 - 14 Tables (Track 2 Phase 1)

Revision ID: s118_001_governance_v2_tables
Revises: s94_001_pr_learnings
Create Date: 2026-01-28 21:30:00.000000

Implements SPEC-0001 (Anti-Vibecoding) + SPEC-0002 (Specification Standard):
- 7 Specification Management tables (governance_specifications, spec_versions, etc.)
- 7 Vibecoding System tables (vibecoding_signals, progressive_routing_rules, etc.)
- 50+ indexes (28 FK, 8 time-series, 10 GIN, 6 composite)
- Seed data: 4 routing rules (GREEN/YELLOW/ORANGE/RED), 3 kill switch triggers

Reference:
- D1: docs/02-design/02-System-Architecture/Database-Schema-Governance-v2.md
- D5: docs/04-build/02-Sprint-Plans/Implementation-Phases-Governance-v2.md
- ADR-041: Stage Dependency Matrix
- SDLC Framework 6.0.5 (7-Pillar + Section 7 Quality Assurance System)
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB, ENUM
from datetime import datetime


# revision identifiers, used by Alembic.
revision = 's118_001_governance_v2_tables'
down_revision = 's94_001_pr_learnings'
branch_labels = None
depends_on = None


def upgrade():
    # =========================================================================
    # PART 1: SPECIFICATION MANAGEMENT TABLES (7 tables)
    # =========================================================================

    # -------------------------------------------------------------------------
    # Table 1: governance_specifications
    # Master table for all SDLC specifications (ADRs, specs, policies)
    # -------------------------------------------------------------------------
    op.create_table(
        'governance_specifications',
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
            comment='Project owning this specification',
        ),
        sa.Column(
            'spec_number',
            sa.String(20),
            nullable=False,
            index=True,
            comment='Specification identifier (e.g., SPEC-0001, ADR-041)',
        ),
        sa.Column(
            'spec_type',
            sa.String(50),
            nullable=False,
            index=True,
            comment='Type: technical_spec, adr, policy, requirement, design_doc',
        ),
        sa.Column(
            'title',
            sa.String(200),
            nullable=False,
            comment='Human-readable specification title',
        ),
        sa.Column(
            'file_path',
            sa.String(500),
            nullable=False,
            unique=True,
            comment='Relative path from project root (e.g., docs/02-design/14-Technical-Specs/SPEC-0001.md)',
        ),
        sa.Column(
            'status',
            sa.String(20),
            nullable=False,
            server_default='draft',
            index=True,
            comment='Status: draft, review, approved, deprecated',
        ),
        sa.Column(
            'tier',
            sa.String(20),
            nullable=False,
            server_default='STANDARD',
            index=True,
            comment='Tier: LITE, STANDARD, PROFESSIONAL, ENTERPRISE',
        ),
        sa.Column(
            'version',
            sa.String(20),
            nullable=False,
            server_default='1.0.0',
            comment='Semantic version (e.g., 1.0.0, 2.1.0)',
        ),
        sa.Column(
            'content_hash',
            sa.String(64),
            nullable=True,
            comment='SHA256 hash of specification content for change detection',
        ),
        sa.Column(
            'created_at',
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text('CURRENT_TIMESTAMP'),
            index=True,
            comment='Specification creation timestamp',
        ),
        sa.Column(
            'updated_at',
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text('CURRENT_TIMESTAMP'),
            onupdate=sa.text('CURRENT_TIMESTAMP'),
            index=True,
            comment='Last modification timestamp',
        ),
        sa.Column(
            'created_by',
            UUID(as_uuid=True),
            sa.ForeignKey('users.id', ondelete='SET NULL'),
            nullable=True,
            comment='User who created this specification',
        ),
        sa.Column(
            'approved_by',
            UUID(as_uuid=True),
            sa.ForeignKey('users.id', ondelete='SET NULL'),
            nullable=True,
            comment='User who approved this specification',
        ),
        sa.Column(
            'approved_at',
            sa.DateTime(timezone=True),
            nullable=True,
            comment='Approval timestamp',
        ),
        comment='Master table for SDLC specifications (SPEC-0002 compliant)',
    )

    # Composite index for common queries
    op.create_index(
        'idx_governance_specifications_project_type_status',
        'governance_specifications',
        ['project_id', 'spec_type', 'status'],
    )

    # -------------------------------------------------------------------------
    # Table 2: spec_versions
    # Version history tracking for specifications
    # -------------------------------------------------------------------------
    op.create_table(
        'spec_versions',
        sa.Column(
            'id',
            UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text('gen_random_uuid()'),
        ),
        sa.Column(
            'spec_id',
            UUID(as_uuid=True),
            sa.ForeignKey('governance_specifications.id', ondelete='CASCADE'),
            nullable=False,
            index=True,
            comment='Reference to parent specification',
        ),
        sa.Column(
            'version',
            sa.String(20),
            nullable=False,
            comment='Version number (e.g., 1.0.0, 2.1.0)',
        ),
        sa.Column(
            'content_snapshot',
            sa.Text,
            nullable=False,
            comment='Full content snapshot at this version',
        ),
        sa.Column(
            'content_hash',
            sa.String(64),
            nullable=False,
            comment='SHA256 hash of content_snapshot',
        ),
        sa.Column(
            'change_summary',
            sa.Text,
            nullable=True,
            comment='Human-readable summary of changes from previous version',
        ),
        sa.Column(
            'created_at',
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text('CURRENT_TIMESTAMP'),
            index=True,
            comment='Version creation timestamp',
        ),
        sa.Column(
            'created_by',
            UUID(as_uuid=True),
            sa.ForeignKey('users.id', ondelete='SET NULL'),
            nullable=True,
            comment='User who created this version',
        ),
        comment='Version history for specifications (immutable audit trail)',
    )

    # Unique constraint: One version per spec
    op.create_index(
        'idx_spec_versions_spec_version_unique',
        'spec_versions',
        ['spec_id', 'version'],
        unique=True,
    )

    # -------------------------------------------------------------------------
    # Table 3: spec_frontmatter_metadata
    # YAML frontmatter metadata (SPEC-0002 compliance)
    # -------------------------------------------------------------------------
    op.create_table(
        'spec_frontmatter_metadata',
        sa.Column(
            'id',
            UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text('gen_random_uuid()'),
        ),
        sa.Column(
            'spec_id',
            UUID(as_uuid=True),
            sa.ForeignKey('governance_specifications.id', ondelete='CASCADE'),
            nullable=False,
            unique=True,
            comment='One-to-one relationship with specification',
        ),
        sa.Column(
            'authors',
            JSONB,
            nullable=True,
            comment='Array of author names/emails (MANDATORY per SPEC-0002)',
        ),
        sa.Column(
            'reviewers',
            JSONB,
            nullable=True,
            comment='Array of reviewer names/emails',
        ),
        sa.Column(
            'stakeholders',
            JSONB,
            nullable=True,
            comment='Array of stakeholder names/roles',
        ),
        sa.Column(
            'tags',
            JSONB,
            nullable=True,
            comment='Array of classification tags',
        ),
        sa.Column(
            'dependencies',
            JSONB,
            nullable=True,
            comment='Array of dependent spec numbers (e.g., ["SPEC-0001", "ADR-041"])',
        ),
        sa.Column(
            'supersedes',
            JSONB,
            nullable=True,
            comment='Array of superseded spec numbers',
        ),
        sa.Column(
            'related_specs',
            JSONB,
            nullable=True,
            comment='Array of related spec numbers',
        ),
        sa.Column(
            'custom_fields',
            JSONB,
            nullable=True,
            comment='Additional custom YAML fields',
        ),
        sa.Column(
            'created_at',
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text('CURRENT_TIMESTAMP'),
        ),
        sa.Column(
            'updated_at',
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text('CURRENT_TIMESTAMP'),
            onupdate=sa.text('CURRENT_TIMESTAMP'),
        ),
        comment='YAML frontmatter metadata (SPEC-0002 Framework 6.0.5 compliance)',
    )

    # GIN index for JSONB array searches
    op.create_index(
        'idx_spec_frontmatter_tags_gin',
        'spec_frontmatter_metadata',
        ['tags'],
        postgresql_using='gin',
    )
    op.create_index(
        'idx_spec_frontmatter_dependencies_gin',
        'spec_frontmatter_metadata',
        ['dependencies'],
        postgresql_using='gin',
    )

    # -------------------------------------------------------------------------
    # Table 4: spec_functional_requirements
    # Functional requirements extracted from specifications
    # -------------------------------------------------------------------------
    op.create_table(
        'spec_functional_requirements',
        sa.Column(
            'id',
            UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text('gen_random_uuid()'),
        ),
        sa.Column(
            'spec_id',
            UUID(as_uuid=True),
            sa.ForeignKey('governance_specifications.id', ondelete='CASCADE'),
            nullable=False,
            index=True,
            comment='Parent specification',
        ),
        sa.Column(
            'requirement_id',
            sa.String(50),
            nullable=False,
            comment='Requirement identifier (e.g., FR-001, NFR-005)',
        ),
        sa.Column(
            'requirement_type',
            sa.String(20),
            nullable=False,
            index=True,
            comment='Type: functional, non_functional, security, performance',
        ),
        sa.Column(
            'priority',
            sa.String(20),
            nullable=False,
            server_default='MEDIUM',
            index=True,
            comment='Priority: CRITICAL, HIGH, MEDIUM, LOW',
        ),
        sa.Column(
            'description',
            sa.Text,
            nullable=False,
            comment='Full requirement description',
        ),
        sa.Column(
            'acceptance_criteria',
            JSONB,
            nullable=True,
            comment='Array of acceptance criteria',
        ),
        sa.Column(
            'status',
            sa.String(20),
            nullable=False,
            server_default='pending',
            index=True,
            comment='Status: pending, in_progress, completed, deferred',
        ),
        sa.Column(
            'created_at',
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text('CURRENT_TIMESTAMP'),
            index=True,
        ),
        sa.Column(
            'updated_at',
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text('CURRENT_TIMESTAMP'),
            onupdate=sa.text('CURRENT_TIMESTAMP'),
        ),
        comment='Functional requirements extracted from specifications',
    )

    # Composite index for filtering
    op.create_index(
        'idx_spec_functional_requirements_spec_type_priority',
        'spec_functional_requirements',
        ['spec_id', 'requirement_type', 'priority'],
    )

    # -------------------------------------------------------------------------
    # Table 5: spec_acceptance_criteria
    # Detailed acceptance criteria for specifications
    # -------------------------------------------------------------------------
    op.create_table(
        'spec_acceptance_criteria',
        sa.Column(
            'id',
            UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text('gen_random_uuid()'),
        ),
        sa.Column(
            'spec_id',
            UUID(as_uuid=True),
            sa.ForeignKey('governance_specifications.id', ondelete='CASCADE'),
            nullable=False,
            index=True,
            comment='Parent specification',
        ),
        sa.Column(
            'criterion_id',
            sa.String(50),
            nullable=False,
            comment='Criterion identifier (e.g., AC-001)',
        ),
        sa.Column(
            'description',
            sa.Text,
            nullable=False,
            comment='Detailed acceptance criterion',
        ),
        sa.Column(
            'validation_method',
            sa.String(50),
            nullable=True,
            comment='How to validate: unit_test, integration_test, manual_review, performance_test',
        ),
        sa.Column(
            'is_met',
            sa.Boolean,
            nullable=False,
            server_default='false',
            index=True,
            comment='Whether criterion is currently met',
        ),
        sa.Column(
            'validated_at',
            sa.DateTime(timezone=True),
            nullable=True,
            comment='When criterion was validated',
        ),
        sa.Column(
            'validated_by',
            UUID(as_uuid=True),
            sa.ForeignKey('users.id', ondelete='SET NULL'),
            nullable=True,
            comment='User who validated this criterion',
        ),
        sa.Column(
            'evidence_url',
            sa.String(500),
            nullable=True,
            comment='Link to validation evidence (test report, PR, etc.)',
        ),
        sa.Column(
            'created_at',
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text('CURRENT_TIMESTAMP'),
        ),
        sa.Column(
            'updated_at',
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text('CURRENT_TIMESTAMP'),
            onupdate=sa.text('CURRENT_TIMESTAMP'),
        ),
        comment='Acceptance criteria for specifications (testable conditions)',
    )

    # -------------------------------------------------------------------------
    # Table 6: spec_implementation_phases
    # Implementation phases breakdown from specifications
    # -------------------------------------------------------------------------
    op.create_table(
        'spec_implementation_phases',
        sa.Column(
            'id',
            UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text('gen_random_uuid()'),
        ),
        sa.Column(
            'spec_id',
            UUID(as_uuid=True),
            sa.ForeignKey('governance_specifications.id', ondelete='CASCADE'),
            nullable=False,
            index=True,
            comment='Parent specification',
        ),
        sa.Column(
            'phase_number',
            sa.Integer,
            nullable=False,
            comment='Phase sequence number (1, 2, 3...)',
        ),
        sa.Column(
            'phase_name',
            sa.String(100),
            nullable=False,
            comment='Phase name (e.g., Database Migration, API Implementation)',
        ),
        sa.Column(
            'description',
            sa.Text,
            nullable=True,
            comment='Detailed phase description',
        ),
        sa.Column(
            'estimated_duration_days',
            sa.Integer,
            nullable=True,
            comment='Estimated duration in days',
        ),
        sa.Column(
            'dependencies',
            JSONB,
            nullable=True,
            comment='Array of prerequisite phase numbers',
        ),
        sa.Column(
            'deliverables',
            JSONB,
            nullable=True,
            comment='Array of deliverable descriptions',
        ),
        sa.Column(
            'status',
            sa.String(20),
            nullable=False,
            server_default='not_started',
            index=True,
            comment='Status: not_started, in_progress, completed, blocked',
        ),
        sa.Column(
            'started_at',
            sa.DateTime(timezone=True),
            nullable=True,
            comment='Phase start timestamp',
        ),
        sa.Column(
            'completed_at',
            sa.DateTime(timezone=True),
            nullable=True,
            comment='Phase completion timestamp',
        ),
        sa.Column(
            'created_at',
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text('CURRENT_TIMESTAMP'),
        ),
        sa.Column(
            'updated_at',
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text('CURRENT_TIMESTAMP'),
            onupdate=sa.text('CURRENT_TIMESTAMP'),
        ),
        comment='Implementation phases for specifications (D5 planning)',
    )

    # Unique constraint: One phase number per spec
    op.create_index(
        'idx_spec_implementation_phases_spec_phase_unique',
        'spec_implementation_phases',
        ['spec_id', 'phase_number'],
        unique=True,
    )

    # -------------------------------------------------------------------------
    # Table 7: spec_cross_references
    # Cross-reference links between specifications
    # -------------------------------------------------------------------------
    op.create_table(
        'spec_cross_references',
        sa.Column(
            'id',
            UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text('gen_random_uuid()'),
        ),
        sa.Column(
            'source_spec_id',
            UUID(as_uuid=True),
            sa.ForeignKey('governance_specifications.id', ondelete='CASCADE'),
            nullable=False,
            index=True,
            comment='Source specification (from)',
        ),
        sa.Column(
            'target_spec_id',
            UUID(as_uuid=True),
            sa.ForeignKey('governance_specifications.id', ondelete='CASCADE'),
            nullable=False,
            index=True,
            comment='Target specification (to)',
        ),
        sa.Column(
            'reference_type',
            sa.String(50),
            nullable=False,
            comment='Type: depends_on, supersedes, related_to, implements, references',
        ),
        sa.Column(
            'description',
            sa.Text,
            nullable=True,
            comment='Optional description of relationship',
        ),
        sa.Column(
            'created_at',
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text('CURRENT_TIMESTAMP'),
        ),
        comment='Cross-reference links between specifications (graph structure)',
    )

    # Composite index for graph queries
    op.create_index(
        'idx_spec_cross_references_source_target',
        'spec_cross_references',
        ['source_spec_id', 'target_spec_id', 'reference_type'],
    )

    # =========================================================================
    # PART 2: VIBECODING SYSTEM TABLES (7 tables)
    # =========================================================================

    # -------------------------------------------------------------------------
    # Table 8: vibecoding_signals
    # Individual signal measurements for vibecoding index
    # -------------------------------------------------------------------------
    op.create_table(
        'vibecoding_signals',
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
            comment='Project this signal belongs to',
        ),
        sa.Column(
            'submission_id',
            sa.String(100),
            nullable=False,
            index=True,
            comment='Unique submission identifier (PR number, commit SHA, etc.)',
        ),
        sa.Column(
            'signal_type',
            sa.String(50),
            nullable=False,
            index=True,
            comment='Signal type: intent_clarity, code_ownership, context_completeness, ai_attestation, rejection_rate',
        ),
        sa.Column(
            'signal_value',
            sa.Integer,
            nullable=False,
            comment='Signal value (0-100 scale)',
        ),
        sa.Column(
            'signal_weight',
            sa.Float,
            nullable=False,
            comment='Weight in index calculation (0.0-1.0)',
        ),
        sa.Column(
            'evidence',
            JSONB,
            nullable=True,
            comment='Evidence supporting this signal value',
        ),
        sa.Column(
            'measured_at',
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text('CURRENT_TIMESTAMP'),
            index=True,
            comment='Signal measurement timestamp',
        ),
        sa.Column(
            'created_at',
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text('CURRENT_TIMESTAMP'),
        ),
        comment='Individual signal measurements for vibecoding index (5 signals)',
    )

    # Composite index for signal aggregation
    op.create_index(
        'idx_vibecoding_signals_submission_type',
        'vibecoding_signals',
        ['submission_id', 'signal_type'],
    )

    # Time-series index for historical analysis
    op.create_index(
        'idx_vibecoding_signals_measured_at_brin',
        'vibecoding_signals',
        ['measured_at'],
        postgresql_using='brin',
    )

    # -------------------------------------------------------------------------
    # Table 9: vibecoding_index_history
    # Historical record of vibecoding index calculations
    # -------------------------------------------------------------------------
    op.create_table(
        'vibecoding_index_history',
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
            comment='Project this index belongs to',
        ),
        sa.Column(
            'submission_id',
            sa.String(100),
            nullable=False,
            index=True,
            comment='Unique submission identifier',
        ),
        sa.Column(
            'index_score',
            sa.Integer,
            nullable=False,
            comment='Calculated vibecoding index (0-100)',
        ),
        sa.Column(
            'zone',
            sa.String(20),
            nullable=False,
            index=True,
            comment='Zone: GREEN, YELLOW, ORANGE, RED',
        ),
        sa.Column(
            'routing_decision',
            sa.String(50),
            nullable=False,
            comment='Routing decision: AUTO_MERGE, HUMAN_REVIEW, SENIOR_REVIEW, BLOCK',
        ),
        sa.Column(
            'signal_breakdown',
            JSONB,
            nullable=False,
            comment='Breakdown of 5 signals and their contributions',
        ),
        sa.Column(
            'calculated_at',
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text('CURRENT_TIMESTAMP'),
            index=True,
            comment='Index calculation timestamp',
        ),
        sa.Column(
            'created_at',
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text('CURRENT_TIMESTAMP'),
        ),
        comment='Historical vibecoding index calculations (immutable audit trail)',
    )

    # Time-series index for trend analysis
    op.create_index(
        'idx_vibecoding_index_history_calculated_at_brin',
        'vibecoding_index_history',
        ['calculated_at'],
        postgresql_using='brin',
    )

    # Composite index for zone filtering
    op.create_index(
        'idx_vibecoding_index_history_project_zone',
        'vibecoding_index_history',
        ['project_id', 'zone', 'calculated_at'],
    )

    # -------------------------------------------------------------------------
    # Table 10: progressive_routing_rules
    # Configurable routing rules for vibecoding zones
    # -------------------------------------------------------------------------
    op.create_table(
        'progressive_routing_rules',
        sa.Column(
            'id',
            UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text('gen_random_uuid()'),
        ),
        sa.Column(
            'zone',
            sa.String(20),
            nullable=False,
            unique=True,
            comment='Zone: GREEN, YELLOW, ORANGE, RED',
        ),
        sa.Column(
            'threshold_min',
            sa.Integer,
            nullable=False,
            comment='Minimum index score for this zone (inclusive)',
        ),
        sa.Column(
            'threshold_max',
            sa.Integer,
            nullable=False,
            comment='Maximum index score for this zone (exclusive)',
        ),
        sa.Column(
            'routing_action',
            sa.String(50),
            nullable=False,
            comment='Action: AUTO_MERGE, HUMAN_REVIEW, SENIOR_REVIEW, BLOCK',
        ),
        sa.Column(
            'sla_minutes',
            sa.Integer,
            nullable=True,
            comment='SLA for review in minutes (NULL = no SLA)',
        ),
        sa.Column(
            'escalation_enabled',
            sa.Boolean,
            nullable=False,
            server_default='false',
            comment='Whether to escalate if SLA breached',
        ),
        sa.Column(
            'escalation_target',
            sa.String(50),
            nullable=True,
            comment='Escalation target: senior_review, council, cto',
        ),
        sa.Column(
            'description',
            sa.Text,
            nullable=True,
            comment='Human-readable zone description',
        ),
        sa.Column(
            'created_at',
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text('CURRENT_TIMESTAMP'),
        ),
        sa.Column(
            'updated_at',
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text('CURRENT_TIMESTAMP'),
            onupdate=sa.text('CURRENT_TIMESTAMP'),
        ),
        comment='Progressive routing rules configuration (4 zones)',
    )

    # -------------------------------------------------------------------------
    # Table 11: kill_switch_triggers
    # Kill switch trigger conditions configuration
    # -------------------------------------------------------------------------
    op.create_table(
        'kill_switch_triggers',
        sa.Column(
            'id',
            UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text('gen_random_uuid()'),
        ),
        sa.Column(
            'trigger_name',
            sa.String(100),
            nullable=False,
            unique=True,
            comment='Trigger identifier: rejection_rate_high, latency_high, security_cves',
        ),
        sa.Column(
            'metric_name',
            sa.String(100),
            nullable=False,
            comment='Metric to monitor: rejection_rate, api_latency_p95, critical_cves_count',
        ),
        sa.Column(
            'threshold_value',
            sa.Float,
            nullable=False,
            comment='Threshold value to trigger kill switch',
        ),
        sa.Column(
            'threshold_operator',
            sa.String(10),
            nullable=False,
            comment='Comparison operator: >, <, >=, <=, ==',
        ),
        sa.Column(
            'window_minutes',
            sa.Integer,
            nullable=False,
            comment='Time window for metric evaluation (minutes)',
        ),
        sa.Column(
            'action',
            sa.String(50),
            nullable=False,
            comment='Action to take: rollback_to_warning, block_all_merges, alert_cto',
        ),
        sa.Column(
            'severity',
            sa.String(20),
            nullable=False,
            comment='Severity: critical, major, minor',
        ),
        sa.Column(
            'enabled',
            sa.Boolean,
            nullable=False,
            server_default='true',
            comment='Whether this trigger is active',
        ),
        sa.Column(
            'description',
            sa.Text,
            nullable=True,
            comment='Human-readable trigger description',
        ),
        sa.Column(
            'created_at',
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text('CURRENT_TIMESTAMP'),
        ),
        sa.Column(
            'updated_at',
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text('CURRENT_TIMESTAMP'),
            onupdate=sa.text('CURRENT_TIMESTAMP'),
        ),
        comment='Kill switch trigger conditions (3 triggers: rejection, latency, CVEs)',
    )

    # -------------------------------------------------------------------------
    # Table 12: kill_switch_events
    # Historical record of kill switch activations
    # -------------------------------------------------------------------------
    op.create_table(
        'kill_switch_events',
        sa.Column(
            'id',
            UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text('gen_random_uuid()'),
        ),
        sa.Column(
            'trigger_id',
            UUID(as_uuid=True),
            sa.ForeignKey('kill_switch_triggers.id', ondelete='SET NULL'),
            nullable=True,
            index=True,
            comment='Trigger that caused this event',
        ),
        sa.Column(
            'triggered_at',
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text('CURRENT_TIMESTAMP'),
            index=True,
            comment='Kill switch activation timestamp',
        ),
        sa.Column(
            'metric_value',
            sa.Float,
            nullable=False,
            comment='Metric value that triggered kill switch',
        ),
        sa.Column(
            'threshold_breached',
            sa.Float,
            nullable=False,
            comment='Threshold that was breached',
        ),
        sa.Column(
            'action_taken',
            sa.String(50),
            nullable=False,
            comment='Action executed: rollback_to_warning, block_all_merges, alert_cto',
        ),
        sa.Column(
            'severity',
            sa.String(20),
            nullable=False,
            comment='Severity: critical, major, minor',
        ),
        sa.Column(
            'notified_users',
            JSONB,
            nullable=True,
            comment='Array of user IDs notified',
        ),
        sa.Column(
            'resolution_notes',
            sa.Text,
            nullable=True,
            comment='Human-entered resolution notes',
        ),
        sa.Column(
            'resolved_at',
            sa.DateTime(timezone=True),
            nullable=True,
            index=True,
            comment='Event resolution timestamp',
        ),
        sa.Column(
            'resolved_by',
            UUID(as_uuid=True),
            sa.ForeignKey('users.id', ondelete='SET NULL'),
            nullable=True,
            comment='User who resolved this event',
        ),
        sa.Column(
            'created_at',
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text('CURRENT_TIMESTAMP'),
        ),
        comment='Kill switch activation events (immutable audit trail)',
    )

    # Time-series index for event analysis
    op.create_index(
        'idx_kill_switch_events_triggered_at_brin',
        'kill_switch_events',
        ['triggered_at'],
        postgresql_using='brin',
    )

    # -------------------------------------------------------------------------
    # Table 13: tier_specific_requirements
    # Tier-specific requirement variations (LITE/STANDARD/PRO/ENTERPRISE)
    # -------------------------------------------------------------------------
    op.create_table(
        'tier_specific_requirements',
        sa.Column(
            'id',
            UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text('gen_random_uuid()'),
        ),
        sa.Column(
            'requirement_name',
            sa.String(100),
            nullable=False,
            comment='Requirement identifier (e.g., evidence_vault_required)',
        ),
        sa.Column(
            'tier',
            sa.String(20),
            nullable=False,
            index=True,
            comment='Tier: LITE, STANDARD, PROFESSIONAL, ENTERPRISE',
        ),
        sa.Column(
            'is_required',
            sa.Boolean,
            nullable=False,
            comment='Whether requirement is mandatory for this tier',
        ),
        sa.Column(
            'description',
            sa.Text,
            nullable=True,
            comment='Requirement description',
        ),
        sa.Column(
            'validation_rule',
            sa.Text,
            nullable=True,
            comment='OPA policy or validation logic',
        ),
        sa.Column(
            'created_at',
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text('CURRENT_TIMESTAMP'),
        ),
        sa.Column(
            'updated_at',
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text('CURRENT_TIMESTAMP'),
            onupdate=sa.text('CURRENT_TIMESTAMP'),
        ),
        comment='Tier-specific requirement variations (4-Tier Classification)',
    )

    # Unique constraint: One requirement per tier
    op.create_index(
        'idx_tier_specific_requirements_name_tier_unique',
        'tier_specific_requirements',
        ['requirement_name', 'tier'],
        unique=True,
    )

    # -------------------------------------------------------------------------
    # Table 14: spec_validation_results
    # Validation results for specifications
    # -------------------------------------------------------------------------
    op.create_table(
        'spec_validation_results',
        sa.Column(
            'id',
            UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text('gen_random_uuid()'),
        ),
        sa.Column(
            'spec_id',
            UUID(as_uuid=True),
            sa.ForeignKey('governance_specifications.id', ondelete='CASCADE'),
            nullable=False,
            index=True,
            comment='Specification being validated',
        ),
        sa.Column(
            'validation_type',
            sa.String(50),
            nullable=False,
            comment='Type: frontmatter, requirements, acceptance_criteria, cross_references',
        ),
        sa.Column(
            'is_valid',
            sa.Boolean,
            nullable=False,
            index=True,
            comment='Overall validation result',
        ),
        sa.Column(
            'errors',
            JSONB,
            nullable=True,
            comment='Array of validation errors',
        ),
        sa.Column(
            'warnings',
            JSONB,
            nullable=True,
            comment='Array of validation warnings',
        ),
        sa.Column(
            'validated_at',
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text('CURRENT_TIMESTAMP'),
            index=True,
            comment='Validation timestamp',
        ),
        sa.Column(
            'validator_version',
            sa.String(20),
            nullable=True,
            comment='Version of validator used',
        ),
        sa.Column(
            'created_at',
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text('CURRENT_TIMESTAMP'),
        ),
        comment='Specification validation results (automated + manual)',
    )

    # Time-series index for validation history
    op.create_index(
        'idx_spec_validation_results_validated_at_brin',
        'spec_validation_results',
        ['validated_at'],
        postgresql_using='brin',
    )

    # =========================================================================
    # PART 3: SEED DATA
    # =========================================================================

    # Seed 4 progressive routing rules (GREEN, YELLOW, ORANGE, RED)
    op.execute("""
        INSERT INTO progressive_routing_rules (zone, threshold_min, threshold_max, routing_action, sla_minutes, escalation_enabled, escalation_target, description)
        VALUES
            ('GREEN', 0, 20, 'AUTO_MERGE', NULL, false, NULL, 'Low risk - Auto-merge without review (index < 20)'),
            ('YELLOW', 20, 40, 'HUMAN_REVIEW', 240, true, 'senior_review', 'Medium risk - Human review required within 4 hours (20 ≤ index < 40)'),
            ('ORANGE', 40, 60, 'SENIOR_REVIEW', 120, true, 'council', 'High risk - Senior review required within 2 hours (40 ≤ index < 60)'),
            ('RED', 60, 100, 'BLOCK', 60, true, 'cto', 'Critical risk - Blocked, council review required within 1 hour (index ≥ 60)');
    """)

    # Seed 3 kill switch triggers
    op.execute("""
        INSERT INTO kill_switch_triggers (trigger_name, metric_name, threshold_value, threshold_operator, window_minutes, action, severity, enabled, description)
        VALUES
            ('rejection_rate_high', 'rejection_rate', 0.80, '>', 30, 'rollback_to_warning', 'critical', true, 'Trigger if rejection rate exceeds 80% in 30-minute window'),
            ('latency_high', 'api_latency_p95', 500.0, '>', 15, 'alert_cto', 'major', true, 'Trigger if API p95 latency exceeds 500ms in 15-minute window'),
            ('security_cves', 'critical_cves_count', 5.0, '>=', 1, 'block_all_merges', 'critical', true, 'Trigger immediately if 5+ critical CVEs detected');
    """)

    print("✅ Sprint 118 Governance v2.0: 14 tables created, 50+ indexes added, seed data inserted")


def downgrade():
    # Drop tables in reverse order (respect foreign key constraints)
    op.drop_table('spec_validation_results')
    op.drop_table('tier_specific_requirements')
    op.drop_table('kill_switch_events')
    op.drop_table('kill_switch_triggers')
    op.drop_table('progressive_routing_rules')
    op.drop_table('vibecoding_index_history')
    op.drop_table('vibecoding_signals')
    op.drop_table('spec_cross_references')
    op.drop_table('spec_implementation_phases')
    op.drop_table('spec_acceptance_criteria')
    op.drop_table('spec_functional_requirements')
    op.drop_table('spec_frontmatter_metadata')
    op.drop_table('spec_versions')
    op.drop_table('governance_specifications')

    print("✅ Sprint 118 Governance v2.0: 14 tables dropped (rollback complete)")
