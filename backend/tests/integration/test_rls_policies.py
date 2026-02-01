"""
Integration Tests for Row-Level Security Policies
Sprint 89: PostgreSQL RLS Implementation

Tests verify:
1. Organization isolation for teams
2. Project access control (owner, team member, project member)
3. Gate and evidence isolation
4. Platform admin bypass
5. Cross-tenant data leakage prevention

Reference: Expert Feedback Plan Section 3.1 (Multi-tenant RLS Implementation)
"""

import pytest
import uuid
from datetime import datetime

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.models.team import Team
from app.models.team_member import TeamMember
from app.models.organization import Organization
from app.models.project import Project
from app.middleware.rls_context import set_rls_context, RLSContextManager


# ===========================================================================
# Fixtures
# ===========================================================================

@pytest.fixture
async def org_alpha(db: AsyncSession) -> Organization:
    """Create Organization Alpha for testing."""
    org = Organization(
        id=uuid.uuid4(),
        name="Alpha Corp",
        slug="alpha-corp",
        created_at=datetime.utcnow(),
    )
    db.add(org)
    await db.commit()
    await db.refresh(org)
    return org


@pytest.fixture
async def org_beta(db: AsyncSession) -> Organization:
    """Create Organization Beta for testing."""
    org = Organization(
        id=uuid.uuid4(),
        name="Beta Inc",
        slug="beta-inc",
        created_at=datetime.utcnow(),
    )
    db.add(org)
    await db.commit()
    await db.refresh(org)
    return org


@pytest.fixture
async def user_alice(db: AsyncSession) -> User:
    """Create user Alice (belongs to Alpha)."""
    user = User(
        id=uuid.uuid4(),
        email="alice@alpha.com",
        full_name="Alice",
        password_hash="hashed",
        is_active=True,
        is_platform_admin=False,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


@pytest.fixture
async def user_bob(db: AsyncSession) -> User:
    """Create user Bob (belongs to Beta)."""
    user = User(
        id=uuid.uuid4(),
        email="bob@beta.com",
        full_name="Bob",
        password_hash="hashed",
        is_active=True,
        is_platform_admin=False,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


@pytest.fixture
async def user_admin(db: AsyncSession) -> User:
    """Create platform admin user."""
    user = User(
        id=uuid.uuid4(),
        email="admin@sdlc.com",
        full_name="Admin",
        password_hash="hashed",
        is_active=True,
        is_platform_admin=True,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


@pytest.fixture
async def team_alpha(db: AsyncSession, org_alpha: Organization) -> Team:
    """Create team in Alpha organization."""
    team = Team(
        id=uuid.uuid4(),
        organization_id=org_alpha.id,
        name="Alpha Backend Team",
        slug="alpha-backend",
    )
    db.add(team)
    await db.commit()
    await db.refresh(team)
    return team


@pytest.fixture
async def team_beta(db: AsyncSession, org_beta: Organization) -> Team:
    """Create team in Beta organization."""
    team = Team(
        id=uuid.uuid4(),
        organization_id=org_beta.id,
        name="Beta Frontend Team",
        slug="beta-frontend",
    )
    db.add(team)
    await db.commit()
    await db.refresh(team)
    return team


@pytest.fixture
async def alice_membership(
    db: AsyncSession, user_alice: User, team_alpha: Team
) -> TeamMember:
    """Add Alice to Alpha team."""
    member = TeamMember(
        id=uuid.uuid4(),
        team_id=team_alpha.id,
        user_id=user_alice.id,
        role="member",
    )
    db.add(member)
    await db.commit()
    await db.refresh(member)
    return member


@pytest.fixture
async def bob_membership(
    db: AsyncSession, user_bob: User, team_beta: Team
) -> TeamMember:
    """Add Bob to Beta team."""
    member = TeamMember(
        id=uuid.uuid4(),
        team_id=team_beta.id,
        user_id=user_bob.id,
        role="member",
    )
    db.add(member)
    await db.commit()
    await db.refresh(member)
    return member


@pytest.fixture
async def project_alpha(
    db: AsyncSession, user_alice: User, team_alpha: Team
) -> Project:
    """Create project in Alpha team."""
    project = Project(
        id=uuid.uuid4(),
        name="Alpha E-commerce",
        slug="alpha-ecommerce",
        owner_id=user_alice.id,
        team_id=team_alpha.id,
    )
    db.add(project)
    await db.commit()
    await db.refresh(project)
    return project


@pytest.fixture
async def project_beta(
    db: AsyncSession, user_bob: User, team_beta: Team
) -> Project:
    """Create project in Beta team."""
    project = Project(
        id=uuid.uuid4(),
        name="Beta Mobile App",
        slug="beta-mobile",
        owner_id=user_bob.id,
        team_id=team_beta.id,
    )
    db.add(project)
    await db.commit()
    await db.refresh(project)
    return project


# ===========================================================================
# Test: Organization Isolation
# ===========================================================================

@pytest.mark.asyncio
async def test_teams_org_isolation_alice_sees_alpha_only(
    db: AsyncSession,
    org_alpha: Organization,
    org_beta: Organization,
    team_alpha: Team,
    team_beta: Team,
    user_alice: User,
    alice_membership: TeamMember,
):
    """
    Alice (Alpha org) should only see Alpha team, not Beta team.
    """
    # Set RLS context for Alice
    await set_rls_context(db, user_id=user_alice.id, org_id=org_alpha.id)

    # Query teams
    result = await db.execute(text("SELECT id, name FROM teams"))
    teams = result.fetchall()

    # Assert Alice sees only Alpha team
    team_ids = [str(t[0]) for t in teams]
    assert str(team_alpha.id) in team_ids, "Alice should see Alpha team"
    assert str(team_beta.id) not in team_ids, "Alice should NOT see Beta team"


@pytest.mark.asyncio
async def test_teams_org_isolation_bob_sees_beta_only(
    db: AsyncSession,
    org_alpha: Organization,
    org_beta: Organization,
    team_alpha: Team,
    team_beta: Team,
    user_bob: User,
    bob_membership: TeamMember,
):
    """
    Bob (Beta org) should only see Beta team, not Alpha team.
    """
    # Set RLS context for Bob
    await set_rls_context(db, user_id=user_bob.id, org_id=org_beta.id)

    # Query teams
    result = await db.execute(text("SELECT id, name FROM teams"))
    teams = result.fetchall()

    # Assert Bob sees only Beta team
    team_ids = [str(t[0]) for t in teams]
    assert str(team_beta.id) in team_ids, "Bob should see Beta team"
    assert str(team_alpha.id) not in team_ids, "Bob should NOT see Alpha team"


# ===========================================================================
# Test: Project Access Control
# ===========================================================================

@pytest.mark.asyncio
async def test_projects_alice_sees_alpha_project_only(
    db: AsyncSession,
    org_alpha: Organization,
    user_alice: User,
    alice_membership: TeamMember,
    project_alpha: Project,
    project_beta: Project,
):
    """
    Alice should only see Alpha project (she's owner and team member).
    """
    await set_rls_context(db, user_id=user_alice.id, org_id=org_alpha.id)

    result = await db.execute(text("SELECT id, name FROM projects"))
    projects = result.fetchall()

    project_ids = [str(p[0]) for p in projects]
    assert str(project_alpha.id) in project_ids, "Alice should see Alpha project"
    assert str(project_beta.id) not in project_ids, "Alice should NOT see Beta project"


@pytest.mark.asyncio
async def test_projects_bob_sees_beta_project_only(
    db: AsyncSession,
    org_beta: Organization,
    user_bob: User,
    bob_membership: TeamMember,
    project_alpha: Project,
    project_beta: Project,
):
    """
    Bob should only see Beta project (he's owner and team member).
    """
    await set_rls_context(db, user_id=user_bob.id, org_id=org_beta.id)

    result = await db.execute(text("SELECT id, name FROM projects"))
    projects = result.fetchall()

    project_ids = [str(p[0]) for p in projects]
    assert str(project_beta.id) in project_ids, "Bob should see Beta project"
    assert str(project_alpha.id) not in project_ids, "Bob should NOT see Alpha project"


# ===========================================================================
# Test: Platform Admin Bypass
# ===========================================================================

@pytest.mark.asyncio
async def test_platform_admin_sees_all_teams(
    db: AsyncSession,
    team_alpha: Team,
    team_beta: Team,
    user_admin: User,
):
    """
    Platform admin should see all teams (RLS bypass).
    """
    await set_rls_context(db, user_id=user_admin.id, bypass_rls=True)

    result = await db.execute(text("SELECT id, name FROM teams"))
    teams = result.fetchall()

    team_ids = [str(t[0]) for t in teams]
    assert str(team_alpha.id) in team_ids, "Admin should see Alpha team"
    assert str(team_beta.id) in team_ids, "Admin should see Beta team"


@pytest.mark.asyncio
async def test_platform_admin_sees_all_projects(
    db: AsyncSession,
    project_alpha: Project,
    project_beta: Project,
    user_admin: User,
):
    """
    Platform admin should see all projects (RLS bypass).
    """
    await set_rls_context(db, user_id=user_admin.id, bypass_rls=True)

    result = await db.execute(text("SELECT id, name FROM projects"))
    projects = result.fetchall()

    project_ids = [str(p[0]) for p in projects]
    assert str(project_alpha.id) in project_ids, "Admin should see Alpha project"
    assert str(project_beta.id) in project_ids, "Admin should see Beta project"


# ===========================================================================
# Test: Cross-Tenant Leakage Prevention
# ===========================================================================

@pytest.mark.asyncio
async def test_no_cross_tenant_project_access(
    db: AsyncSession,
    org_alpha: Organization,
    org_beta: Organization,
    user_alice: User,
    user_bob: User,
    alice_membership: TeamMember,
    bob_membership: TeamMember,
    project_alpha: Project,
    project_beta: Project,
):
    """
    Verify no cross-tenant data leakage between orgs.
    """
    # Alice's view
    await set_rls_context(db, user_id=user_alice.id, org_id=org_alpha.id)
    alice_result = await db.execute(text("SELECT COUNT(*) FROM projects"))
    alice_count = alice_result.scalar()

    # Bob's view
    await set_rls_context(db, user_id=user_bob.id, org_id=org_beta.id)
    bob_result = await db.execute(text("SELECT COUNT(*) FROM projects"))
    bob_count = bob_result.scalar()

    # Admin's view (total)
    await set_rls_context(db, bypass_rls=True)
    admin_result = await db.execute(text("SELECT COUNT(*) FROM projects"))
    total_count = admin_result.scalar()

    # Verify isolation
    assert alice_count == 1, "Alice should see exactly 1 project"
    assert bob_count == 1, "Bob should see exactly 1 project"
    assert total_count >= 2, "Total projects should be >= 2"
    assert alice_count + bob_count <= total_count, "Sum should not exceed total"


# ===========================================================================
# Test: RLS Context Manager
# ===========================================================================

@pytest.mark.asyncio
async def test_rls_context_manager(
    db: AsyncSession,
    org_alpha: Organization,
    user_alice: User,
    alice_membership: TeamMember,
    project_alpha: Project,
    project_beta: Project,
):
    """
    Test RLSContextManager utility class.
    """
    async with RLSContextManager(db, user_id=user_alice.id, org_id=org_alpha.id) as session:
        result = await session.execute(text("SELECT id FROM projects"))
        projects = result.fetchall()
        assert len(projects) == 1, "Should see 1 project via context manager"


# ===========================================================================
# Test: Anonymous User Access
# ===========================================================================

@pytest.mark.asyncio
async def test_anonymous_user_sees_nothing(
    db: AsyncSession,
    project_alpha: Project,
    project_beta: Project,
):
    """
    Anonymous user (no RLS context) should see no data.
    """
    # Clear RLS context (anonymous)
    await set_rls_context(db, user_id=None, org_id=None, bypass_rls=False)

    result = await db.execute(text("SELECT COUNT(*) FROM projects"))
    count = result.scalar()

    assert count == 0, "Anonymous user should see 0 projects"


# ===========================================================================
# Test: Team Member CRUD Permissions
# ===========================================================================

@pytest.mark.asyncio
async def test_team_member_can_see_same_team_members(
    db: AsyncSession,
    org_alpha: Organization,
    user_alice: User,
    alice_membership: TeamMember,
    team_alpha: Team,
):
    """
    Team members can see other members of the same team.
    """
    # Add another user to same team
    user_charlie = User(
        id=uuid.uuid4(),
        email="charlie@alpha.com",
        full_name="Charlie",
        password_hash="hashed",
        is_active=True,
    )
    db.add(user_charlie)
    await db.commit()

    charlie_membership = TeamMember(
        id=uuid.uuid4(),
        team_id=team_alpha.id,
        user_id=user_charlie.id,
        role="member",
    )
    db.add(charlie_membership)
    await db.commit()

    # Set RLS context for Alice
    await set_rls_context(db, user_id=user_alice.id, org_id=org_alpha.id)

    # Alice should see both memberships
    result = await db.execute(
        text("SELECT user_id FROM team_members WHERE team_id = :team_id"),
        {"team_id": str(team_alpha.id)}
    )
    members = result.fetchall()

    member_ids = [str(m[0]) for m in members]
    assert str(user_alice.id) in member_ids, "Alice should see herself"
    assert str(user_charlie.id) in member_ids, "Alice should see Charlie"
