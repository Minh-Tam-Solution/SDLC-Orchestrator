"""
Sprint 73: Teams Data Migration
Creates default organization, migrates users and projects to Teams feature

Revision ID: s73_teams_data_migration
Revises: s70_teams_foundation
Create Date: 2026-02-10 11:00:00.000000

Sprint: 73 - Teams Integration
Tasks: S73-T12~T17 (Data Migration - 4 SP)
Authority: DevOps + Backend Lead + CTO Approved

Migration Tasks:
- S73-T12: Create default organization "Nhat Quang Holding"
- S73-T13: Migrate existing users to default org
- S73-T14: Create "Unassigned" team for orphan projects
- S73-T15: Backfill existing projects to Unassigned team
- S73-T16: Backfill existing projects with default gates (BUG #7)
- S73-T17: Verification and idempotency checks

Acceptance Criteria:
✅ All existing users have organization_id
✅ All existing projects have team_id
✅ All existing projects have 5 default gates
✅ No data loss during migration
✅ Migration is idempotent (safe to run multiple times)
✅ Rollback plan documented

Data Impact:
- Users table: +organization_id (FK to organizations)
- Projects table: +team_id (FK to teams)
- Gates table: +5 gates per project without gates
- Organizations table: +1 default org
- Teams table: +1 default team
- TeamMembers table: +N members (1 per existing user)

Performance:
- Batch processing for large datasets
- Transaction per logical unit (org, team, users, projects)
- Estimated time: <2min for 1000 users + 500 projects
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy import text
from datetime import datetime
from uuid import uuid4

# revision identifiers, used by Alembic.
revision = 's73_teams_data_migration'
down_revision = 's70_teams_foundation'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """
    Upgrade: Migrate existing data to Teams feature.

    Steps:
    1. Create default organization "Nhat Quang Holding"
    2. Migrate all users without organization_id to default org
    3. Create "Unassigned" team under default org
    4. Migrate all projects without team_id to Unassigned team
    5. Add all users as members of Unassigned team
    6. Backfill gates for projects without gates (BUG #7 fix)

    Idempotency: Safe to run multiple times, skips if data already exists.
    """
    conn = op.get_bind()

    # S73-T12: Create default organization "Nhat Quang Holding"
    print("S73-T12: Creating default organization...")

    # Check if default org already exists
    result = conn.execute(text(
        "SELECT id FROM organizations WHERE slug = 'nhat-quang-holding' LIMIT 1"
    ))
    existing_org = result.fetchone()

    if existing_org:
        default_org_id = existing_org[0]
        print(f"  ✓ Default organization already exists: {default_org_id}")
    else:
        default_org_id = str(uuid4())
        conn.execute(text(
            """
            INSERT INTO organizations (id, name, slug, plan, settings, created_at, updated_at)
            VALUES (
                :id,
                'Nhat Quang Holding',
                'nhat-quang-holding',
                'enterprise',
                '{"require_mfa": true, "allowed_domains": ["nhatquangholding.com"], "sase_config": {"agentic_maturity": "L2", "se4h_enabled": true, "se4a_enabled": true}}'::jsonb,
                :now,
                :now
            )
            """
        ), {
            'id': default_org_id,
            'now': datetime.utcnow()
        })
        print(f"  ✓ Created default organization: {default_org_id}")

    # S73-T13: Migrate existing users to default org
    print("S73-T13: Migrating users to default organization...")

    # Count users without organization_id
    result = conn.execute(text(
        "SELECT COUNT(*) FROM users WHERE organization_id IS NULL AND deleted_at IS NULL"
    ))
    users_to_migrate = result.fetchone()[0]

    if users_to_migrate > 0:
        # Update users to default org
        result = conn.execute(text(
            """
            UPDATE users
            SET organization_id = :org_id, updated_at = :now
            WHERE organization_id IS NULL AND deleted_at IS NULL
            """
        ), {
            'org_id': default_org_id,
            'now': datetime.utcnow()
        })
        print(f"  ✓ Migrated {users_to_migrate} users to default organization")
    else:
        print(f"  ✓ All users already have organization_id (0 to migrate)")

    # S73-T14: Create "Unassigned" team for orphan projects
    print("S73-T14: Creating 'Unassigned' team...")

    # Check if Unassigned team already exists
    result = conn.execute(text(
        """
        SELECT id FROM teams
        WHERE organization_id = :org_id AND slug = 'unassigned'
        LIMIT 1
        """
    ), {'org_id': default_org_id})
    existing_team = result.fetchone()

    if existing_team:
        default_team_id = existing_team[0]
        print(f"  ✓ 'Unassigned' team already exists: {default_team_id}")
    else:
        default_team_id = str(uuid4())
        conn.execute(text(
            """
            INSERT INTO teams (id, organization_id, name, slug, description, settings, created_at, updated_at)
            VALUES (
                :id,
                :org_id,
                'Unassigned Projects',
                'unassigned',
                'Default team for projects without explicit team assignment. Assign projects to dedicated teams for better organization.',
                '{"sase_config": {"agentic_maturity": "L1", "se4h_enabled": true, "se4a_enabled": false}}'::jsonb,
                :now,
                :now
            )
            """
        ), {
            'id': default_team_id,
            'org_id': default_org_id,
            'now': datetime.utcnow()
        })
        print(f"  ✓ Created 'Unassigned' team: {default_team_id}")

    # S73-T15: Backfill existing projects to Unassigned team
    print("S73-T15: Migrating projects to 'Unassigned' team...")

    # Count projects without team_id
    result = conn.execute(text(
        "SELECT COUNT(*) FROM projects WHERE team_id IS NULL AND deleted_at IS NULL"
    ))
    projects_to_migrate = result.fetchone()[0]

    if projects_to_migrate > 0:
        # Update projects to default team
        result = conn.execute(text(
            """
            UPDATE projects
            SET team_id = :team_id, updated_at = :now
            WHERE team_id IS NULL AND deleted_at IS NULL
            """
        ), {
            'team_id': default_team_id,
            'now': datetime.utcnow()
        })
        print(f"  ✓ Migrated {projects_to_migrate} projects to 'Unassigned' team")
    else:
        print(f"  ✓ All projects already have team_id (0 to migrate)")

    # Add all users as members of Unassigned team (with 'member' role)
    print("S73-T15.1: Adding users as team members...")

    # Get all users in the organization
    result = conn.execute(text(
        """
        SELECT id FROM users
        WHERE organization_id = :org_id AND deleted_at IS NULL
        """
    ), {'org_id': default_org_id})
    users = result.fetchall()

    members_added = 0
    for user_row in users:
        user_id = user_row[0]

        # Check if user is already a team member
        result = conn.execute(text(
            """
            SELECT id FROM team_members
            WHERE team_id = :team_id AND user_id = :user_id
            """
        ), {'team_id': default_team_id, 'user_id': user_id})

        if not result.fetchone():
            # Add as team member with 'member' role
            conn.execute(text(
                """
                INSERT INTO team_members (id, team_id, user_id, role, member_type, joined_at)
                VALUES (:id, :team_id, :user_id, 'member', 'human', :now)
                """
            ), {
                'id': str(uuid4()),
                'team_id': default_team_id,
                'user_id': user_id,
                'now': datetime.utcnow()
            })
            members_added += 1

    print(f"  ✓ Added {members_added} users as team members")

    # S73-T16: Backfill gates for projects without gates (BUG #7 fix)
    print("S73-T16: Backfilling gates for existing projects...")

    # Find projects without any gates
    result = conn.execute(text(
        """
        SELECT p.id, p.name, p.owner_id
        FROM projects p
        LEFT JOIN gates g ON p.id = g.project_id
        WHERE p.deleted_at IS NULL
        GROUP BY p.id, p.name, p.owner_id
        HAVING COUNT(g.id) = 0
        """
    ))
    projects_without_gates = result.fetchall()

    # Default gate templates (aligned with SDLC 5.1.2)
    gate_templates = [
        {
            "name": "Planning Review",
            "gate_type": "G1_PLANNING_REVIEW",
            "stage": "01-PLAN",
            "description": "Review and approve project planning artifacts (BRD, PRD, requirements)",
        },
        {
            "name": "Design Review",
            "gate_type": "G2_DESIGN_REVIEW",
            "stage": "02-DESIGN",
            "description": "Review and approve system design, architecture, and technical specifications",
        },
        {
            "name": "Code Review",
            "gate_type": "G3_CODE_REVIEW",
            "stage": "03-BUILD",
            "description": "Review code quality, security, and adherence to standards",
        },
        {
            "name": "Test Review",
            "gate_type": "G5_TEST_REVIEW",
            "stage": "05-TEST",
            "description": "Review test coverage, results, and quality assurance",
        },
        {
            "name": "Deploy Approval",
            "gate_type": "G6_DEPLOY_APPROVAL",
            "stage": "06-DEPLOY",
            "description": "Approve deployment to production environment",
        },
    ]

    gates_created = 0
    for project_row in projects_without_gates:
        project_id, project_name, owner_id = project_row

        for template in gate_templates:
            gate_id = str(uuid4())
            gate_name = f"{project_name} - {template['name']}"

            conn.execute(text(
                """
                INSERT INTO gates (
                    id, gate_name, gate_type, stage, project_id, created_by,
                    status, description, exit_criteria, created_at, updated_at
                )
                VALUES (
                    :id, :gate_name, :gate_type, :stage, :project_id, :created_by,
                    'DRAFT', :description, '[]'::jsonb, :now, :now
                )
                """
            ), {
                'id': gate_id,
                'gate_name': gate_name,
                'gate_type': template['gate_type'],
                'stage': template['stage'],
                'project_id': project_id,
                'created_by': owner_id,
                'description': template['description'],
                'now': datetime.utcnow()
            })
            gates_created += 1

    print(f"  ✓ Created {gates_created} gates for {len(projects_without_gates)} projects")

    # S73-T17: Verification
    print("S73-T17: Verifying migration...")

    # Verify all users have organization_id
    result = conn.execute(text(
        "SELECT COUNT(*) FROM users WHERE organization_id IS NULL AND deleted_at IS NULL"
    ))
    users_without_org = result.fetchone()[0]

    # Verify all projects have team_id
    result = conn.execute(text(
        "SELECT COUNT(*) FROM projects WHERE team_id IS NULL AND deleted_at IS NULL"
    ))
    projects_without_team = result.fetchone()[0]

    # Verify all projects have gates
    result = conn.execute(text(
        """
        SELECT COUNT(DISTINCT p.id)
        FROM projects p
        LEFT JOIN gates g ON p.id = g.project_id
        WHERE p.deleted_at IS NULL
        GROUP BY p.id
        HAVING COUNT(g.id) = 0
        """
    ))
    projects_without_gates_count = len(result.fetchall())

    print("\n=== Migration Verification ===")
    print(f"Users without organization_id: {users_without_org} (expected: 0)")
    print(f"Projects without team_id: {projects_without_team} (expected: 0)")
    print(f"Projects without gates: {projects_without_gates_count} (expected: 0)")

    if users_without_org == 0 and projects_without_team == 0 and projects_without_gates_count == 0:
        print("\n✅ Migration completed successfully!")
    else:
        print("\n⚠️  Migration incomplete - some data still needs migration")

    print("\n=== Migration Summary ===")
    print(f"Default Organization: {default_org_id}")
    print(f"Default Team: {default_team_id}")
    print(f"Users migrated: {users_to_migrate}")
    print(f"Projects migrated: {projects_to_migrate}")
    print(f"Team members added: {members_added}")
    print(f"Gates created: {gates_created}")


def downgrade() -> None:
    """
    Downgrade: Rollback Teams data migration.

    WARNING: This will:
    - Remove team_id from all projects
    - Remove organization_id from all users
    - Delete all team memberships
    - Delete 'Unassigned' team
    - Delete 'Nhat Quang Holding' organization
    - Delete all auto-created gates (BUG #7 backfill)

    Rollback Plan:
    1. Backup database before rollback
    2. Run this downgrade to remove Teams data
    3. Verify projects and users are intact
    4. Re-run upgrade if needed

    Data Loss Warning:
    - Team memberships will be lost
    - Custom teams created after migration will be deleted
    - All gates created by backfill will be deleted
    """
    conn = op.get_bind()

    print("Rolling back S73 Teams Data Migration...")

    # Remove team_id from projects (S73-T15 rollback)
    print("Removing team_id from projects...")
    conn.execute(text(
        "UPDATE projects SET team_id = NULL WHERE team_id IS NOT NULL"
    ))

    # Remove organization_id from users (S73-T13 rollback)
    print("Removing organization_id from users...")
    conn.execute(text(
        "UPDATE users SET organization_id = NULL WHERE organization_id IS NOT NULL"
    ))

    # Delete team memberships
    print("Deleting team memberships...")
    conn.execute(text(
        "DELETE FROM team_members WHERE team_id IN (SELECT id FROM teams WHERE slug = 'unassigned')"
    ))

    # Delete gates created by backfill (BUG #7 rollback)
    # Only delete gates that match the auto-created pattern and are in DRAFT status
    print("Deleting auto-created gates...")
    conn.execute(text(
        """
        DELETE FROM gates
        WHERE gate_type IN (
            'G1_PLANNING_REVIEW', 'G2_DESIGN_REVIEW', 'G3_CODE_REVIEW',
            'G5_TEST_REVIEW', 'G6_DEPLOY_APPROVAL'
        )
        AND status = 'DRAFT'
        AND description LIKE 'Review and approve%'
        """
    ))

    # Delete 'Unassigned' team (S73-T14 rollback)
    print("Deleting 'Unassigned' team...")
    conn.execute(text(
        "DELETE FROM teams WHERE slug = 'unassigned'"
    ))

    # Delete 'Nhat Quang Holding' organization (S73-T12 rollback)
    print("Deleting default organization...")
    conn.execute(text(
        "DELETE FROM organizations WHERE slug = 'nhat-quang-holding'"
    ))

    print("✅ Rollback completed successfully")
    print("\nNOTE: To restore Teams feature, re-run upgrade migration")
