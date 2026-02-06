"""Sprint 161: Project tier foundation - Tier-based gate approval system

Revision ID: s161_001
Revises: s160_001
Create Date: 2026-02-06 09:00:00.000000

Sprint: 161 - Tier-Based Gate Approval Backend Foundation
CTO Approval: v2.5 (Score: 92/100)
Authority: CTO Final Review (Feb 6, 2026)

Changes:
1. Create 4 ENUMs (project_tier, functional_role, decision_action, decision_status)
2. Create table: project_function_roles (per-project functional role mapping)
3. Create table: gate_decisions (event log for approval decisions)
4. Add projects.tier column (FREE/STANDARD/PROFESSIONAL/ENTERPRISE)

CTO v2.5 Adjustments Applied:
- ✅ Adjustment #1: ESCALATE added to decision_action ENUM
- ✅ Adjustment #2: expires_at column with partial index for timeout queries
- ✅ Adjustment #3: ApprovalChainMetadata return type (service layer)

Architecture:
- Event log pattern (NOT state machine) - simpler, more auditable
- Per-project functional roles (PM/CTO/CEO/QA_LEAD/COMPLIANCE_OFFICER)
- Separates access control (project_members.role) from approval authority
- Chain logic via (chain_id, step_index) tuple

Reference: docs/04-build/02-Sprint-Plans/SPRINT-161-164-TIER-BASED-GATE-APPROVAL.md
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 's161_001'
down_revision = 's160_001'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """
    Sprint 161 Day 1: Database schema for tier-based gate approval.

    Creates foundation for project-tier-based approval routing:
    - FREE: Self-approval
    - STANDARD: PM → CTO chain
    - PROFESSIONAL: PM → CTO → CEO chain
    - ENTERPRISE: Council review (PM → CTO → CEO + Compliance Officer)
    """

    # =====================================================================
    # STEP 1: Create ENUMs
    # =====================================================================

    # ENUM 1: project_tier (4 values)
    op.execute("""
        CREATE TYPE project_tier AS ENUM (
            'FREE',          -- Self-approval, personal projects
            'STANDARD',      -- PM → CTO chain
            'PROFESSIONAL',  -- PM → CTO → CEO chain
            'ENTERPRISE'     -- Council review (CTO+CEO+COMPLIANCE_OFFICER)
        );
    """)

    # ENUM 2: functional_role (5 values)
    op.execute("""
        CREATE TYPE functional_role AS ENUM (
            'PM',                   -- Project Manager
            'CTO',                  -- Chief Technology Officer
            'CEO',                  -- Chief Executive Officer
            'QA_LEAD',              -- QA Lead
            'COMPLIANCE_OFFICER'    -- Compliance Officer (ENTERPRISE only)
        );
    """)

    # ENUM 3: decision_action (5 values - CTO v2.5 adjustment #1: ESCALATE added)
    op.execute("""
        CREATE TYPE decision_action AS ENUM (
            'REQUEST',    -- Initial approval request
            'APPROVE',    -- Approval granted
            'REJECT',     -- Approval denied
            'ESCALATE',   -- Escalate to higher authority (CTO v2.5)
            'COMMENT'     -- Comment without decision
        );
    """)

    # ENUM 4: decision_status (3 values)
    op.execute("""
        CREATE TYPE decision_status AS ENUM (
            'PENDING',     -- Awaiting action
            'COMPLETED',   -- Action completed
            'CANCELLED'    -- Request cancelled
        );
    """)

    # =====================================================================
    # STEP 2: Create table - project_function_roles
    # =====================================================================

    op.create_table(
        'project_function_roles',

        # Primary key
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),

        # Foreign keys
        sa.Column('project_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('projects.id', ondelete='CASCADE'), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),

        # Functional role (PM/CTO/CEO/QA_LEAD/COMPLIANCE_OFFICER)
        sa.Column('functional_role', sa.Enum(
            'PM', 'CTO', 'CEO', 'QA_LEAD', 'COMPLIANCE_OFFICER',
            name='functional_role'
        ), nullable=False),

        # Audit
        sa.Column('assigned_at', sa.TIMESTAMP(timezone=False), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('assigned_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id')),

        # Constraints
        sa.UniqueConstraint('project_id', 'user_id', 'functional_role', name='uq_project_user_function')
    )

    # Indexes for project_function_roles
    op.create_index('idx_project_function_roles_project', 'project_function_roles', ['project_id'])
    op.create_index('idx_project_function_roles_user', 'project_function_roles', ['user_id'])
    op.create_index('idx_project_function_roles_role', 'project_function_roles', ['project_id', 'functional_role'])

    # Comment
    op.execute("""
        COMMENT ON TABLE project_function_roles IS
        'Functional roles for approval authority (separate from access control in project_members)';
    """)

    # =====================================================================
    # STEP 3: Create table - gate_decisions (Event Log)
    # =====================================================================

    op.create_table(
        'gate_decisions',

        # Primary key
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),

        # Foreign keys
        sa.Column('gate_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('gates.id', ondelete='CASCADE'), nullable=False),
        sa.Column('project_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('projects.id', ondelete='CASCADE'), nullable=False),

        # Decision metadata
        sa.Column('action', sa.Enum(
            'REQUEST', 'APPROVE', 'REJECT', 'ESCALATE', 'COMMENT',
            name='decision_action'
        ), nullable=False),
        sa.Column('actor_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=False),

        # Chain tracking (for council review: N decisions with same chain_id)
        sa.Column('chain_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('step_index', sa.Integer, nullable=False, server_default='0'),
        sa.Column('required_roles', postgresql.ARRAY(sa.String()), nullable=False),

        # Status
        sa.Column('status', sa.Enum('PENDING', 'COMPLETED', 'CANCELLED', name='decision_status'), server_default='PENDING'),

        # Evidence
        sa.Column('comments', sa.Text),
        sa.Column('evidence_ids', postgresql.ARRAY(postgresql.UUID(as_uuid=True))),

        # Audit timestamps
        sa.Column('created_at', sa.TIMESTAMP(timezone=False), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('expires_at', sa.TIMESTAMP(timezone=False)),  # CTO v2.5 adjustment #2
        sa.Column('completed_at', sa.TIMESTAMP(timezone=False)),

        # Constraints
        sa.CheckConstraint('step_index >= 0', name='gate_decisions_step_index_positive'),
        sa.UniqueConstraint('gate_id', 'chain_id', 'step_index', name='gate_decisions_chain_step_unique')
    )

    # Indexes for gate_decisions
    op.create_index('idx_gate_decisions_gate', 'gate_decisions', ['gate_id'])
    op.create_index('idx_gate_decisions_chain', 'gate_decisions', ['chain_id'])
    op.create_index('idx_gate_decisions_actor', 'gate_decisions', ['actor_id'])
    op.create_index('idx_gate_decisions_status', 'gate_decisions', ['status'],
                    postgresql_where=sa.text("status = 'PENDING'"))

    # CTO v2.5 adjustment #2: Partial index for expiring decisions
    op.create_index('idx_pending_expiring', 'gate_decisions', ['expires_at'],
                    postgresql_where=sa.text("status = 'PENDING' AND expires_at IS NOT NULL"))

    # Comment
    op.execute("""
        COMMENT ON TABLE gate_decisions IS
        'Event log for gate approval decisions (NOT state machine)';
    """)
    op.execute("""
        COMMENT ON COLUMN gate_decisions.chain_id IS
        'Groups related decisions (e.g., ENTERPRISE council review)';
    """)
    op.execute("""
        COMMENT ON COLUMN gate_decisions.step_index IS
        'Sequential step in approval chain (0-based)';
    """)

    # =====================================================================
    # STEP 4: Add tier column to projects table
    # =====================================================================

    op.add_column('projects',
        sa.Column('tier', sa.Enum('FREE', 'STANDARD', 'PROFESSIONAL', 'ENTERPRISE', name='project_tier'),
                  nullable=False, server_default='FREE')
    )

    # Index for projects.tier
    op.create_index('idx_projects_tier', 'projects', ['tier'])

    # Comment
    op.execute("""
        COMMENT ON COLUMN projects.tier IS
        'Project tier for approval routing: FREE/STANDARD/PROFESSIONAL/ENTERPRISE';
    """)

    # =====================================================================
    # STEP 5: Data Migration - Default existing projects to STANDARD
    # =====================================================================

    # Conservative default: Existing projects → STANDARD (requires PM → CTO approval)
    op.execute("""
        UPDATE projects
        SET tier = 'STANDARD'
        WHERE created_at < NOW() AND tier = 'FREE';
    """)

    print("""
    ✅ Sprint 161 Migration Complete - Tier-Based Gate Approval Foundation

    Created:
    - 4 ENUMs (project_tier, functional_role, decision_action, decision_status)
    - 2 tables (project_function_roles, gate_decisions)
    - 1 column (projects.tier)
    - 9 indexes (including partial indexes for performance)

    CTO v2.5 Adjustments Applied:
    ✅ ESCALATE in decision_action ENUM
    ✅ expires_at column with partial index
    ✅ ApprovalChainMetadata (service layer, not migration)

    Next Steps:
    - Day 2: Create SQLAlchemy models (ProjectFunctionRole, GateDecision)
    - Day 3: Implement TierApprovalService (3 methods)
    - Day 4: Unit tests (40+ tests)
    - Day 5: ADR-052 + completion report
    """)


def downgrade() -> None:
    """
    Rollback Sprint 161 schema changes.

    WARNING: This will DROP all tier-based approval data.
    Only use this in development/staging environments.
    """

    # Drop projects.tier column
    op.drop_index('idx_projects_tier', table_name='projects')
    op.drop_column('projects', 'tier')

    # Drop gate_decisions table
    op.drop_index('idx_pending_expiring', table_name='gate_decisions')
    op.drop_index('idx_gate_decisions_status', table_name='gate_decisions')
    op.drop_index('idx_gate_decisions_actor', table_name='gate_decisions')
    op.drop_index('idx_gate_decisions_chain', table_name='gate_decisions')
    op.drop_index('idx_gate_decisions_gate', table_name='gate_decisions')
    op.drop_table('gate_decisions')

    # Drop project_function_roles table
    op.drop_index('idx_project_function_roles_role', table_name='project_function_roles')
    op.drop_index('idx_project_function_roles_user', table_name='project_function_roles')
    op.drop_index('idx_project_function_roles_project', table_name='project_function_roles')
    op.drop_table('project_function_roles')

    # Drop ENUMs (in reverse order of creation)
    op.execute('DROP TYPE IF EXISTS decision_status;')
    op.execute('DROP TYPE IF EXISTS decision_action;')
    op.execute('DROP TYPE IF EXISTS functional_role;')
    op.execute('DROP TYPE IF EXISTS project_tier;')

    print("""
    ✅ Sprint 161 Migration Rolled Back

    Dropped:
    - 2 tables (gate_decisions, project_function_roles)
    - 1 column (projects.tier)
    - 4 ENUMs (project_tier, functional_role, decision_action, decision_status)
    - 9 indexes

    ⚠️  WARNING: All tier-based approval data has been deleted.
    """)
