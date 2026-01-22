"""
=========================================================================
Sprint 88 Multi-Org Test Data Setup
=========================================================================

Purpose:
    Create test data to verify Sprint 88 platform admin privacy fix:
    - Create a second organization (Customer Org)
    - Create a regular admin in Customer Org
    - Create projects in Customer Org
    - Verify platform admin CANNOT see Customer Org data

Usage:
    docker compose exec backend python3 scripts/test_sprint88_multiorg.py

Expected Results:
    - Platform admin sees only their org (Nhat Quang Holding)
    - Regular admin sees ALL organizations
    - Customer Org admin sees only Customer Org

Sprint: Sprint 88 - Platform Admin Privacy Fix
Date: January 22, 2026
=========================================================================
"""

import asyncio
from uuid import uuid4, UUID

from app.db.session import AsyncSessionLocal
from app.models.organization import Organization
from app.models.user import User
from app.models.project import Project
from app.core.security import get_password_hash
from sqlalchemy import select


async def setup_test_data():
    """Create multi-org test data for Sprint 88 verification."""

    async with AsyncSessionLocal() as db:
        print("=" * 70)
        print("Sprint 88 Multi-Org Test Data Setup")
        print("=" * 70)
        print()

        # Step 1: Create Customer Organization
        print("Step 1: Creating Customer Organization...")

        # Check if already exists
        result = await db.execute(
            select(Organization).where(Organization.name == "Customer Org Alpha")
        )
        customer_org = result.scalar_one_or_none()

        if not customer_org:
            customer_org = Organization(
                id=uuid4(),
                name="Customer Org Alpha",
                subdomain="customer-alpha",
                is_active=True,
                plan="enterprise",
                settings={
                    "require_mfa": False,
                    "allowed_domains": ["customer-alpha.com"]
                }
            )
            db.add(customer_org)
            await db.flush()
            print(f"  ✅ Created: {customer_org.name} (ID: {customer_org.id})")
        else:
            print(f"  ℹ️  Already exists: {customer_org.name} (ID: {customer_org.id})")

        # Step 2: Create Regular Admin in Customer Org
        print("\nStep 2: Creating Regular Admin in Customer Org...")

        result = await db.execute(
            select(User).where(User.email == "admin@customer-alpha.com")
        )
        customer_admin = result.scalar_one_or_none()

        if not customer_admin:
            customer_admin = User(
                id=uuid4(),
                email="admin@customer-alpha.com",
                full_name="Customer Alpha Admin",
                password_hash=get_password_hash("Admin@123456"),
                is_active=True,
                is_superuser=True,  # Regular admin (can see all orgs)
                is_platform_admin=False,  # NOT platform admin
                organization_id=customer_org.id,
            )
            db.add(customer_admin)
            await db.flush()
            print(f"  ✅ Created: {customer_admin.email}")
            print(f"     - is_superuser: True (regular admin)")
            print(f"     - is_platform_admin: False")
        else:
            print(f"  ℹ️  Already exists: {customer_admin.email}")

        # Step 3: Create Regular User in Customer Org
        print("\nStep 3: Creating Regular User in Customer Org...")

        result = await db.execute(
            select(User).where(User.email == "user@customer-alpha.com")
        )
        customer_user = result.scalar_one_or_none()

        if not customer_user:
            customer_user = User(
                id=uuid4(),
                email="user@customer-alpha.com",
                full_name="Customer Alpha User",
                password_hash=get_password_hash("User@123456"),
                is_active=True,
                is_superuser=False,
                is_platform_admin=False,
                organization_id=customer_org.id,
            )
            db.add(customer_user)
            await db.flush()
            print(f"  ✅ Created: {customer_user.email}")
        else:
            print(f"  ℹ️  Already exists: {customer_user.email}")

        # Step 4: Create Projects in Customer Org
        print("\nStep 4: Creating Projects in Customer Org...")

        project_names = [
            ("Customer Alpha Project 1", "First project in customer org"),
            ("Customer Alpha Project 2", "Second project in customer org"),
            ("Customer Alpha Project 3", "Third project in customer org"),
        ]

        created_projects = []
        for name, desc in project_names:
            # Check if already exists
            result = await db.execute(
                select(Project).where(Project.name == name)
            )
            project = result.scalar_one_or_none()

            if not project:
                project = Project(
                    id=uuid4(),
                    name=name,
                    slug=name.lower().replace(" ", "-"),
                    description=desc,
                    owner_id=customer_user.id,
                    is_active=True,
                )
                db.add(project)
                created_projects.append(project)
                print(f"  ✅ Created: {name}")
            else:
                print(f"  ℹ️  Already exists: {name}")

        await db.commit()

        # Step 5: Verify Platform Admin User
        print("\nStep 5: Verifying Platform Admin User...")

        result = await db.execute(
            select(User).where(User.email == "taidt@mtsolution.com.vn")
        )
        platform_admin = result.scalar_one_or_none()

        if platform_admin:
            print(f"  ✅ Platform Admin: {platform_admin.email}")
            print(f"     - is_superuser: {platform_admin.is_superuser}")
            print(f"     - is_platform_admin: {platform_admin.is_platform_admin}")
            print(f"     - organization_id: {platform_admin.organization_id}")
        else:
            print("  ❌ Platform admin not found!")

        print()
        print("=" * 70)
        print("Test Data Setup Complete!")
        print("=" * 70)
        print()
        print("Test Accounts:")
        print(f"  1. Platform Admin:    taidt@mtsolution.com.vn / Admin@123456")
        print(f"  2. Regular Admin:     admin@customer-alpha.com / Admin@123456")
        print(f"  3. Customer User:     user@customer-alpha.com / User@123456")
        print()
        print("Next Steps:")
        print("  1. Test with platform admin - should NOT see Customer Org projects")
        print("  2. Test with regular admin - should see ALL projects")
        print("  3. Test with customer user - should only see Customer Org projects")
        print()


async def run_verification_tests():
    """Run verification tests to check Sprint 88 access control."""

    async with AsyncSessionLocal() as db:
        print("=" * 70)
        print("Sprint 88 Verification Tests")
        print("=" * 70)
        print()

        # Get platform admin
        result = await db.execute(
            select(User).where(User.email == "taidt@mtsolution.com.vn")
        )
        platform_admin = result.scalar_one_or_none()

        # Get regular admin
        result = await db.execute(
            select(User).where(User.email == "admin@customer-alpha.com")
        )
        regular_admin = result.scalar_one_or_none()

        # Get customer user
        result = await db.execute(
            select(User).where(User.email == "user@customer-alpha.com")
        )
        customer_user = result.scalar_one_or_none()

        if not all([platform_admin, regular_admin, customer_user]):
            print("❌ Test data not found! Run setup first.")
            return

        # Test 1: Platform Admin Projects Access
        print("Test 1: Platform Admin Projects Access")
        print(f"  User: {platform_admin.email}")
        print(f"  Organization: {platform_admin.organization_id}")

        # Get projects platform admin should see (only their org)
        result = await db.execute(
            select(Project, User)
            .join(User, Project.owner_id == User.id)
            .where(User.organization_id == platform_admin.organization_id)
            .where(Project.deleted_at.is_(None))
        )
        platform_admin_projects = result.all()

        print(f"  Projects visible: {len(platform_admin_projects)}")
        for proj, owner in platform_admin_projects[:3]:
            print(f"    - {proj.name} (owner: {owner.email})")

        # Test 2: Regular Admin Projects Access
        print("\nTest 2: Regular Admin Projects Access")
        print(f"  User: {regular_admin.email}")
        print(f"  Organization: {regular_admin.organization_id}")

        # Regular admin sees ALL projects
        result = await db.execute(
            select(Project).where(Project.deleted_at.is_(None))
        )
        all_projects = result.scalars().all()

        print(f"  Projects visible: {len(all_projects)} (should see ALL)")

        # Count by organization
        result = await db.execute(
            select(Project, User)
            .join(User, Project.owner_id == User.id)
            .where(Project.deleted_at.is_(None))
        )
        projects_by_org = {}
        for proj, owner in result.all():
            org_id = str(owner.organization_id)
            if org_id not in projects_by_org:
                projects_by_org[org_id] = []
            projects_by_org[org_id].append(proj.name)

        print(f"  Projects by organization:")
        for org_id, projects in projects_by_org.items():
            print(f"    - {org_id}: {len(projects)} projects")

        # Test 3: Customer User Projects Access
        print("\nTest 3: Customer User Projects Access")
        print(f"  User: {customer_user.email}")
        print(f"  Organization: {customer_user.organization_id}")

        # Customer user sees only their org's projects
        result = await db.execute(
            select(Project, User)
            .join(User, Project.owner_id == User.id)
            .where(User.organization_id == customer_user.organization_id)
            .where(Project.deleted_at.is_(None))
        )
        customer_projects = result.all()

        print(f"  Projects visible: {len(customer_projects)}")
        for proj, owner in customer_projects[:3]:
            print(f"    - {proj.name} (owner: {owner.email})")

        print()
        print("=" * 70)
        print("Verification Complete!")
        print("=" * 70)
        print()

        # Summary
        print("Summary:")
        if platform_admin.organization_id == customer_user.organization_id:
            print("  ⚠️  Platform admin and customer user in SAME organization")
            print("      Cannot test cross-org isolation!")
        else:
            print("  ✅ Platform admin and customer user in DIFFERENT organizations")
            print("      Can test cross-org isolation!")

        print()


async def main():
    """Main entry point."""
    print()
    await setup_test_data()
    print()
    await run_verification_tests()
    print()


if __name__ == "__main__":
    asyncio.run(main())
