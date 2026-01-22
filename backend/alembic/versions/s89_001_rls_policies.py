"""Sprint 89: PostgreSQL Row-Level Security Policies

Revision ID: s89_001_rls_policies
Revises: s88_001_add_is_platform_admin
Create Date: 2026-01-22 12:00:00.000000

Implements multi-tenant Row-Level Security per CTO Pre-Launch Hardening Plan (P2):
- teams: Organization isolation
- projects: Team/organization isolation
- gate_evidence: Project-based access control
- evidence_manifests: Project-based access control
- gates: Project-based access control

Security Model:
- Users can only access data from their organization
- Platform admins are excluded from RLS (is_platform_admin = true)
- RLS is enforced at database level, not just application level

Reference: Expert Feedback Plan Section 3.1 (Multi-tenant RLS Implementation)
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers
revision = 's89_001_rls_policies'
down_revision = 's88_001_add_is_platform_admin'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """
    Enable Row-Level Security on multi-tenant tables.

    Security Policy Architecture:
    1. Teams: Users see only teams in their organization
    2. Projects: Users see only projects in their team/organization
    3. Gates: Users see only gates for their projects
    4. Evidence: Users see only evidence for their projects

    Implementation Notes:
    - Uses current_setting('app.current_user_id') for user context
    - Uses current_setting('app.current_org_id') for org context
    - Application must SET these before queries
    - Platform admins bypass RLS via is_platform_admin check
    """

    # ===========================================================================
    # 1. TEAMS TABLE - Organization Isolation
    # ===========================================================================
    op.execute("""
        -- Enable RLS on teams table
        ALTER TABLE teams ENABLE ROW LEVEL SECURITY;

        -- Policy: Users can only see teams in their organization
        -- Platform admins can see all teams (via application bypass)
        CREATE POLICY teams_org_isolation ON teams
            FOR ALL
            USING (
                organization_id = COALESCE(
                    NULLIF(current_setting('app.current_org_id', true), '')::uuid,
                    '00000000-0000-0000-0000-000000000000'::uuid
                )
                OR
                -- Superuser bypass (for migrations, admin tasks)
                current_setting('app.bypass_rls', true) = 'true'
            );

        -- Policy: Team members can see their own teams
        CREATE POLICY teams_member_access ON teams
            FOR SELECT
            USING (
                EXISTS (
                    SELECT 1 FROM team_members tm
                    WHERE tm.team_id = teams.id
                    AND tm.user_id = COALESCE(
                        NULLIF(current_setting('app.current_user_id', true), '')::uuid,
                        '00000000-0000-0000-0000-000000000000'::uuid
                    )
                    AND tm.deleted_at IS NULL
                )
            );
    """)

    # ===========================================================================
    # 2. PROJECTS TABLE - Team/Organization Isolation
    # ===========================================================================
    op.execute("""
        -- Enable RLS on projects table
        ALTER TABLE projects ENABLE ROW LEVEL SECURITY;

        -- Policy: Users can see projects they own or are members of
        CREATE POLICY projects_member_access ON projects
            FOR ALL
            USING (
                -- Owner access
                owner_id = COALESCE(
                    NULLIF(current_setting('app.current_user_id', true), '')::uuid,
                    '00000000-0000-0000-0000-000000000000'::uuid
                )
                OR
                -- Team member access (via team_id)
                team_id IN (
                    SELECT tm.team_id FROM team_members tm
                    WHERE tm.user_id = COALESCE(
                        NULLIF(current_setting('app.current_user_id', true), '')::uuid,
                        '00000000-0000-0000-0000-000000000000'::uuid
                    )
                    AND tm.deleted_at IS NULL
                )
                OR
                -- Project member access (direct membership)
                EXISTS (
                    SELECT 1 FROM project_members pm
                    WHERE pm.project_id = projects.id
                    AND pm.user_id = COALESCE(
                        NULLIF(current_setting('app.current_user_id', true), '')::uuid,
                        '00000000-0000-0000-0000-000000000000'::uuid
                    )
                )
                OR
                -- Superuser bypass
                current_setting('app.bypass_rls', true) = 'true'
            );
    """)

    # ===========================================================================
    # 3. GATES TABLE - Project-Based Access
    # ===========================================================================
    op.execute("""
        -- Enable RLS on gates table
        ALTER TABLE gates ENABLE ROW LEVEL SECURITY;

        -- Policy: Users can see gates for projects they have access to
        CREATE POLICY gates_project_access ON gates
            FOR ALL
            USING (
                project_id IN (
                    SELECT p.id FROM projects p
                    WHERE p.owner_id = COALESCE(
                        NULLIF(current_setting('app.current_user_id', true), '')::uuid,
                        '00000000-0000-0000-0000-000000000000'::uuid
                    )
                    OR p.team_id IN (
                        SELECT tm.team_id FROM team_members tm
                        WHERE tm.user_id = COALESCE(
                            NULLIF(current_setting('app.current_user_id', true), '')::uuid,
                            '00000000-0000-0000-0000-000000000000'::uuid
                        )
                        AND tm.deleted_at IS NULL
                    )
                    OR EXISTS (
                        SELECT 1 FROM project_members pm
                        WHERE pm.project_id = p.id
                        AND pm.user_id = COALESCE(
                            NULLIF(current_setting('app.current_user_id', true), '')::uuid,
                            '00000000-0000-0000-0000-000000000000'::uuid
                        )
                    )
                )
                OR
                current_setting('app.bypass_rls', true) = 'true'
            );
    """)

    # ===========================================================================
    # 4. GATE_EVIDENCE TABLE - Project-Based Access
    # ===========================================================================
    op.execute("""
        -- Enable RLS on gate_evidence table
        ALTER TABLE gate_evidence ENABLE ROW LEVEL SECURITY;

        -- Policy: Users can see evidence for gates they have access to
        CREATE POLICY evidence_gate_access ON gate_evidence
            FOR ALL
            USING (
                gate_id IN (
                    SELECT g.id FROM gates g
                    WHERE g.project_id IN (
                        SELECT p.id FROM projects p
                        WHERE p.owner_id = COALESCE(
                            NULLIF(current_setting('app.current_user_id', true), '')::uuid,
                            '00000000-0000-0000-0000-000000000000'::uuid
                        )
                        OR p.team_id IN (
                            SELECT tm.team_id FROM team_members tm
                            WHERE tm.user_id = COALESCE(
                                NULLIF(current_setting('app.current_user_id', true), '')::uuid,
                                '00000000-0000-0000-0000-000000000000'::uuid
                            )
                            AND tm.deleted_at IS NULL
                        )
                        OR EXISTS (
                            SELECT 1 FROM project_members pm
                            WHERE pm.project_id = p.id
                            AND pm.user_id = COALESCE(
                                NULLIF(current_setting('app.current_user_id', true), '')::uuid,
                                '00000000-0000-0000-0000-000000000000'::uuid
                            )
                        )
                    )
                )
                OR
                current_setting('app.bypass_rls', true) = 'true'
            );
    """)

    # ===========================================================================
    # 5. EVIDENCE_MANIFESTS TABLE - Project-Based Access
    # ===========================================================================
    op.execute("""
        -- Enable RLS on evidence_manifests table
        ALTER TABLE evidence_manifests ENABLE ROW LEVEL SECURITY;

        -- Policy: Users can see manifests for projects they have access to
        CREATE POLICY manifests_project_access ON evidence_manifests
            FOR ALL
            USING (
                project_id IN (
                    SELECT p.id FROM projects p
                    WHERE p.owner_id = COALESCE(
                        NULLIF(current_setting('app.current_user_id', true), '')::uuid,
                        '00000000-0000-0000-0000-000000000000'::uuid
                    )
                    OR p.team_id IN (
                        SELECT tm.team_id FROM team_members tm
                        WHERE tm.user_id = COALESCE(
                            NULLIF(current_setting('app.current_user_id', true), '')::uuid,
                            '00000000-0000-0000-0000-000000000000'::uuid
                        )
                        AND tm.deleted_at IS NULL
                    )
                    OR EXISTS (
                        SELECT 1 FROM project_members pm
                        WHERE pm.project_id = p.id
                        AND pm.user_id = COALESCE(
                            NULLIF(current_setting('app.current_user_id', true), '')::uuid,
                            '00000000-0000-0000-0000-000000000000'::uuid
                        )
                    )
                )
                OR
                current_setting('app.bypass_rls', true) = 'true'
            );
    """)

    # ===========================================================================
    # 6. TEAM_MEMBERS TABLE - Self-Access + Admin Access
    # ===========================================================================
    op.execute("""
        -- Enable RLS on team_members table
        ALTER TABLE team_members ENABLE ROW LEVEL SECURITY;

        -- Policy: Users can see their own memberships + same team memberships
        CREATE POLICY team_members_access ON team_members
            FOR SELECT
            USING (
                -- Self access
                user_id = COALESCE(
                    NULLIF(current_setting('app.current_user_id', true), '')::uuid,
                    '00000000-0000-0000-0000-000000000000'::uuid
                )
                OR
                -- Same team access (for team member lists)
                team_id IN (
                    SELECT tm.team_id FROM team_members tm
                    WHERE tm.user_id = COALESCE(
                        NULLIF(current_setting('app.current_user_id', true), '')::uuid,
                        '00000000-0000-0000-0000-000000000000'::uuid
                    )
                    AND tm.deleted_at IS NULL
                )
                OR
                current_setting('app.bypass_rls', true) = 'true'
            );

        -- Policy: Only team admins/owners can modify memberships
        CREATE POLICY team_members_modify ON team_members
            FOR INSERT
            WITH CHECK (
                team_id IN (
                    SELECT tm.team_id FROM team_members tm
                    WHERE tm.user_id = COALESCE(
                        NULLIF(current_setting('app.current_user_id', true), '')::uuid,
                        '00000000-0000-0000-0000-000000000000'::uuid
                    )
                    AND tm.role IN ('owner', 'admin')
                    AND tm.deleted_at IS NULL
                )
                OR
                current_setting('app.bypass_rls', true) = 'true'
            );
    """)

    # ===========================================================================
    # Create helper function to set RLS context
    # ===========================================================================
    op.execute("""
        -- Function to set RLS context variables
        -- Called by application before each request
        CREATE OR REPLACE FUNCTION set_rls_context(
            p_user_id UUID,
            p_org_id UUID DEFAULT NULL,
            p_bypass BOOLEAN DEFAULT FALSE
        )
        RETURNS VOID AS $$
        BEGIN
            -- Set user context
            IF p_user_id IS NOT NULL THEN
                PERFORM set_config('app.current_user_id', p_user_id::text, true);
            ELSE
                PERFORM set_config('app.current_user_id', '', true);
            END IF;

            -- Set org context
            IF p_org_id IS NOT NULL THEN
                PERFORM set_config('app.current_org_id', p_org_id::text, true);
            ELSE
                PERFORM set_config('app.current_org_id', '', true);
            END IF;

            -- Set bypass flag (for platform admins)
            PERFORM set_config('app.bypass_rls', p_bypass::text, true);
        END;
        $$ LANGUAGE plpgsql SECURITY DEFINER;

        -- Grant execute to application user
        -- Note: Adjust 'sdlc_user' to your actual app user
        GRANT EXECUTE ON FUNCTION set_rls_context(UUID, UUID, BOOLEAN) TO PUBLIC;
    """)

    # ===========================================================================
    # Create index for RLS performance
    # ===========================================================================
    op.execute("""
        -- Indexes to optimize RLS policy lookups
        CREATE INDEX IF NOT EXISTS idx_team_members_user_active
            ON team_members(user_id)
            WHERE deleted_at IS NULL;

        CREATE INDEX IF NOT EXISTS idx_project_members_user
            ON project_members(user_id);

        CREATE INDEX IF NOT EXISTS idx_projects_team_owner
            ON projects(team_id, owner_id);
    """)


def downgrade() -> None:
    """Remove RLS policies and revert to application-level filtering."""

    # Drop helper function
    op.execute("DROP FUNCTION IF EXISTS set_rls_context(UUID, UUID, BOOLEAN);")

    # Drop indexes
    op.execute("DROP INDEX IF EXISTS idx_team_members_user_active;")
    op.execute("DROP INDEX IF EXISTS idx_project_members_user;")
    op.execute("DROP INDEX IF EXISTS idx_projects_team_owner;")

    # Disable RLS and drop policies
    tables = [
        'teams',
        'projects',
        'gates',
        'gate_evidence',
        'evidence_manifests',
        'team_members'
    ]

    for table in tables:
        op.execute(f"""
            -- Drop all policies on {table}
            DO $$
            DECLARE
                pol RECORD;
            BEGIN
                FOR pol IN
                    SELECT policyname FROM pg_policies
                    WHERE tablename = '{table}'
                LOOP
                    EXECUTE format('DROP POLICY IF EXISTS %I ON {table}', pol.policyname);
                END LOOP;
            END $$;

            -- Disable RLS
            ALTER TABLE {table} DISABLE ROW LEVEL SECURITY;
        """)
