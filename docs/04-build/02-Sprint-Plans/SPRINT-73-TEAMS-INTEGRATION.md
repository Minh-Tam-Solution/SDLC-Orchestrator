# Sprint 73: Teams Integration & Testing

**Sprint ID:** S73  
**Status:** ⏳ QUEUED  
**Duration:** 5 days (Feb 10-14, 2026)  
**Goal:** Complete Teams feature with E2E tests, data migration, and production deployment

**Dependency:** Sprint 72 (Frontend) must be complete

---

## 📋 Sprint Overview

| Attribute | Value |
|-----------|-------|
| Sprint Number | 73 |
| Start Date | February 10, 2026 (Monday) |
| End Date | February 14, 2026 (Friday) |
| Working Days | 5 |
| Story Points | 20 |
| Team Capacity | QA (3d), Backend Dev (2d), DevOps (2d), Tech Lead (1d), PM (1d) |

---

## 🎯 Sprint Goal

> Complete Teams feature implementation with comprehensive E2E testing, data migration for existing users/projects, production deployment, and documentation for Go-Live approval.

---

## 📊 Sprint Backlog

### Epic: ADR-028 Teams Feature Implementation

#### Story 1: E2E Tests (6 SP)
**As a** QA engineer  
**I want** E2E tests for Teams  
**So that** the feature is verified end-to-end

| Task ID | Task | Owner | Est | Status |
|---------|------|-------|-----|--------|
| S73-T01 | Organization CRUD E2E test | QA Engineer | 2h | ⏳ |
| S73-T02 | Team CRUD E2E test | QA Engineer | 3h | ⏳ |
| S73-T03 | Team membership E2E test | QA Engineer | 3h | ⏳ |
| S73-T04 | Team → Project association E2E | QA Engineer | 2h | ⏳ |
| S73-T05 | Permission boundary E2E test | QA Engineer | 2h | ⏳ |
| S73-T06 | Cross-browser testing (Chrome, Firefox, Safari) | QA Engineer | 2h | ⏳ |

**Acceptance Criteria:**
- [ ] 10+ E2E tests passing
- [ ] Full user journey covered: Create org → Create team → Add members → Create project → Gate approval
- [ ] Permission denied scenarios tested
- [ ] Tests run on CI/CD pipeline

---

#### Story 2: Backend Integration Tests (4 SP)
**As a** developer  
**I want** integration tests for team workflows  
**So that** complex scenarios are verified

| Task ID | Task | Owner | Est | Status |
|---------|------|-------|-----|--------|
| S73-T07 | Team-based project access test | Backend Dev | 2h | ⏳ |
| S73-T08 | Team notifications integration | Backend Dev | 2h | ⏳ |
| S73-T09 | Gate approval with team roles | Backend Dev | 3h | ⏳ |
| S73-T10 | Team deletion cascade test | Backend Dev | 1h | ⏳ |
| S73-T11 | Organization plan limits test | Backend Dev | 2h | ⏳ |

**Acceptance Criteria:**
- [ ] Gate approval respects team roles (only owners/admins can approve)
- [ ] Project visibility restricted to team members
- [ ] Team deletion cascades correctly
- [ ] Organization plan limits enforced

---

#### Story 3: Data Migration (4 SP)
**As a** DevOps engineer  
**I want** existing data migrated  
**So that** current users can use Teams

| Task ID | Task | Owner | Est | Status |
|---------|------|-------|-----|--------|
| S73-T12 | Create default organization "Nhat Quang Holding" | DevOps | 1h | ⏳ |
| S73-T13 | Migrate existing users to default org | DevOps | 2h | ⏳ |
| S73-T14 | Create "Unassigned" team for orphan projects | DevOps | 1h | ⏳ |
| S73-T15 | Backfill existing projects to Unassigned team | DevOps | 2h | ⏳ |
| S73-T16 | Create migration verification script | DevOps | 2h | ⏳ |
| S73-T17 | Test migration on staging | DevOps | 2h | ⏳ |

**Acceptance Criteria:**
- [ ] All existing users have organization_id
- [ ] All existing projects have team_id
- [ ] No data loss during migration
- [ ] Migration script is idempotent
- [ ] Rollback plan documented

---

#### Story 4: Production Deployment (3 SP)
**As a** DevOps engineer  
**I want** Teams deployed to production  
**So that** users can start using the feature

| Task ID | Task | Owner | Est | Status |
|---------|------|-------|-----|--------|
| S73-T18 | Deploy to staging environment | DevOps | 2h | ⏳ |
| S73-T19 | Staging smoke tests | QA Engineer | 2h | ⏳ |
| S73-T20 | Production database migration | DevOps | 1h | ⏳ |
| S73-T21 | Production deployment | DevOps | 2h | ⏳ |
| S73-T22 | Production smoke tests | QA Engineer | 1h | ⏳ |
| S73-T23 | Monitor for errors (1 hour) | DevOps | 1h | ⏳ |

**Acceptance Criteria:**
- [ ] Staging deployment successful
- [ ] All staging tests pass
- [ ] Production migration successful
- [ ] Production deployment successful
- [ ] No errors in first hour post-deploy

---

#### Story 5: Documentation & Handoff (3 SP)
**As a** PM  
**I want** documentation complete  
**So that** users can learn Teams feature

| Task ID | Task | Owner | Est | Status |
|---------|------|-------|-----|--------|
| S73-T24 | Update API documentation (OpenAPI) | Tech Lead | 2h | ⏳ |
| S73-T25 | Create user guide for Teams | PM | 3h | ⏳ |
| S73-T26 | Update onboarding flow docs | PM | 1h | ⏳ |
| S73-T27 | CTO final review meeting | CTO | 2h | ⏳ |
| S73-T28 | CEO Go-Live sign-off | CEO | 1h | ⏳ |

**Acceptance Criteria:**
- [ ] OpenAPI spec updated and validated
- [ ] User guide covers all Team features
- [ ] CTO approval with score ≥ 9.0/10
- [ ] CEO signs off on Go-Live

---

## 📁 Files to Create/Modify

### New Files
```
tests/e2e/
└── teams/
    ├── teams-crud.spec.ts           # Team CRUD tests
    ├── team-members.spec.ts         # Member management tests
    ├── team-projects.spec.ts        # Project association tests
    └── team-permissions.spec.ts     # Permission tests

backend/scripts/
├── migrate_existing_users.py        # User migration script
├── migrate_existing_projects.py     # Project migration script
└── verify_migration.py              # Verification script

docs/
├── 08-collaborate/
│   └── teams-user-guide.md          # User guide
└── 02-design/04-API-Design/
    └── openapi.yaml                 # Updated API spec
```

### Modified Files
```
.github/workflows/ci.yml             # Add E2E tests
docker-compose.yml                   # Any new env vars
```

---

## 🧪 E2E Test Specifications

### Test Suite: teams-crud.spec.ts
```typescript
// tests/e2e/teams/teams-crud.spec.ts
import { test, expect } from '@playwright/test';

test.describe('Teams CRUD', () => {
  test.beforeEach(async ({ page }) => {
    // Login as test user
    await page.goto('/login');
    await page.fill('[name="email"]', 'test@example.com');
    await page.fill('[name="password"]', 'TestPassword123!');
    await page.click('button[type="submit"]');
    await page.waitForURL('/app');
  });

  test('should display teams list', async ({ page }) => {
    await page.goto('/app/teams');
    await expect(page.locator('h1')).toContainText('Teams');
  });

  test('should create a new team', async ({ page }) => {
    await page.goto('/app/teams');
    await page.click('button:has-text("Create Team")');
    
    // Fill form
    await page.fill('[name="name"]', 'Engineering Team');
    await page.fill('[name="slug"]', 'engineering');
    await page.fill('[name="description"]', 'The engineering team');
    
    // Submit
    await page.click('button:has-text("Create")');
    
    // Verify created
    await expect(page.locator('.team-card')).toContainText('Engineering Team');
  });

  test('should view team details', async ({ page }) => {
    await page.goto('/app/teams');
    await page.click('.team-card:first-child');
    
    await expect(page.locator('h1')).toContainText('Engineering Team');
    await expect(page.locator('.stats-card')).toHaveCount(3);
  });

  test('should update team', async ({ page }) => {
    await page.goto('/app/teams/[team-id]/settings');
    
    await page.fill('[name="name"]', 'Updated Team Name');
    await page.click('button:has-text("Save")');
    
    await expect(page.locator('.toast')).toContainText('Team updated');
  });

  test('should delete team with confirmation', async ({ page }) => {
    await page.goto('/app/teams/[team-id]/settings');
    
    await page.click('button:has-text("Delete Team")');
    await page.fill('[name="confirmName"]', 'Engineering Team');
    await page.click('button:has-text("Delete")');
    
    await expect(page).toHaveURL('/app/teams');
  });
});
```

### Test Suite: team-members.spec.ts
```typescript
// tests/e2e/teams/team-members.spec.ts
import { test, expect } from '@playwright/test';

test.describe('Team Members', () => {
  test('should display team members', async ({ page }) => {
    await page.goto('/app/teams/[team-id]/members');
    
    await expect(page.locator('table')).toBeVisible();
    await expect(page.locator('tbody tr')).toHaveCount.greaterThan(0);
  });

  test('should invite new member', async ({ page }) => {
    await page.goto('/app/teams/[team-id]/members');
    
    await page.click('button:has-text("Invite Member")');
    await page.fill('[name="email"]', 'newmember@example.com');
    await page.selectOption('[name="role"]', 'member');
    await page.click('button:has-text("Send Invite")');
    
    await expect(page.locator('.toast')).toContainText('Invitation sent');
  });

  test('should change member role (owner only)', async ({ page }) => {
    // Login as team owner
    await page.goto('/app/teams/[team-id]/members');
    
    await page.click('tr:has-text("member@example.com") button:has-text("Change Role")');
    await page.selectOption('[name="role"]', 'admin');
    await page.click('button:has-text("Update")');
    
    await expect(page.locator('tr:has-text("member@example.com")')).toContainText('Admin');
  });

  test('should remove member', async ({ page }) => {
    await page.goto('/app/teams/[team-id]/members');
    
    await page.click('tr:has-text("member@example.com") button:has-text("Remove")');
    await page.click('button:has-text("Confirm")');
    
    await expect(page.locator('table')).not.toContainText('member@example.com');
  });

  test('should prevent removing last owner', async ({ page }) => {
    await page.goto('/app/teams/[team-id]/members');
    
    // Try to remove owner when only one owner
    await page.click('tr:has-text("owner@example.com") button:has-text("Remove")');
    
    await expect(page.locator('.error')).toContainText('Cannot remove last owner');
  });
});
```

### Test Suite: team-permissions.spec.ts
```typescript
// tests/e2e/teams/team-permissions.spec.ts
import { test, expect } from '@playwright/test';

test.describe('Team Permissions', () => {
  test('member cannot access team settings', async ({ page }) => {
    // Login as regular member
    await page.goto('/login');
    await page.fill('[name="email"]', 'member@example.com');
    await page.fill('[name="password"]', 'Password123!');
    await page.click('button[type="submit"]');
    
    await page.goto('/app/teams/[team-id]/settings');
    
    // Should redirect or show access denied
    await expect(page).toHaveURL('/app/teams/[team-id]');
  });

  test('member cannot invite others', async ({ page }) => {
    await page.goto('/app/teams/[team-id]/members');
    
    // Invite button should not be visible
    await expect(page.locator('button:has-text("Invite Member")')).not.toBeVisible();
  });

  test('non-member cannot view team', async ({ page }) => {
    // Login as user not in team
    await page.goto('/app/teams/[other-team-id]');
    
    await expect(page.locator('.error')).toContainText('Access denied');
  });

  test('admin can update team but not delete', async ({ page }) => {
    // Login as admin
    await page.goto('/app/teams/[team-id]/settings');
    
    // Update should work
    await page.fill('[name="name"]', 'New Name');
    await page.click('button:has-text("Save")');
    await expect(page.locator('.toast')).toContainText('saved');
    
    // Delete should be disabled
    await expect(page.locator('button:has-text("Delete Team")')).toBeDisabled();
  });
});
```

---

## 📦 Data Migration Scripts

### migrate_existing_users.py
```python
# backend/scripts/migrate_existing_users.py
"""
Migrate existing users to default organization.
Run: python backend/scripts/migrate_existing_users.py
"""
import asyncio
from uuid import uuid4
from sqlalchemy import select, update
from app.db.session import async_session
from app.models import User, Organization

DEFAULT_ORG_NAME = "Nhat Quang Holding"
DEFAULT_ORG_SLUG = "nhat-quang-holding"

async def migrate():
    async with async_session() as db:
        # Check or create default org
        org = await db.scalar(
            select(Organization).where(Organization.slug == DEFAULT_ORG_SLUG)
        )
        
        if not org:
            org = Organization(
                id=uuid4(),
                name=DEFAULT_ORG_NAME,
                slug=DEFAULT_ORG_SLUG,
                plan="enterprise"
            )
            db.add(org)
            await db.commit()
            print(f"✅ Created default organization: {org.name}")
        
        # Update users without organization
        result = await db.execute(
            update(User)
            .where(User.organization_id.is_(None))
            .values(organization_id=org.id)
        )
        await db.commit()
        
        print(f"✅ Migrated {result.rowcount} users to {org.name}")

if __name__ == "__main__":
    asyncio.run(migrate())
```

### migrate_existing_projects.py
```python
# backend/scripts/migrate_existing_projects.py
"""
Migrate existing projects to default team.
Run: python backend/scripts/migrate_existing_projects.py
"""
import asyncio
from uuid import uuid4
from sqlalchemy import select, update
from app.db.session import async_session
from app.models import Project, Team, Organization

DEFAULT_TEAM_NAME = "Unassigned Projects"
DEFAULT_TEAM_SLUG = "unassigned"

async def migrate():
    async with async_session() as db:
        # Get default org
        org = await db.scalar(
            select(Organization).where(Organization.slug == "nhat-quang-holding")
        )
        if not org:
            print("❌ Default organization not found. Run migrate_existing_users.py first.")
            return
        
        # Check or create unassigned team
        team = await db.scalar(
            select(Team).where(
                Team.organization_id == org.id,
                Team.slug == DEFAULT_TEAM_SLUG
            )
        )
        
        if not team:
            team = Team(
                id=uuid4(),
                organization_id=org.id,
                name=DEFAULT_TEAM_NAME,
                slug=DEFAULT_TEAM_SLUG,
                description="Projects not yet assigned to a team"
            )
            db.add(team)
            await db.commit()
            print(f"✅ Created default team: {team.name}")
        
        # Update projects without team
        result = await db.execute(
            update(Project)
            .where(Project.team_id.is_(None))
            .values(team_id=team.id)
        )
        await db.commit()
        
        print(f"✅ Migrated {result.rowcount} projects to {team.name}")

if __name__ == "__main__":
    asyncio.run(migrate())
```

### verify_migration.py
```python
# backend/scripts/verify_migration.py
"""
Verify data migration was successful.
Run: python backend/scripts/verify_migration.py
"""
import asyncio
from sqlalchemy import select, func
from app.db.session import async_session
from app.models import User, Project, Organization, Team

async def verify():
    async with async_session() as db:
        # Check users
        users_without_org = await db.scalar(
            select(func.count()).select_from(User).where(User.organization_id.is_(None))
        )
        total_users = await db.scalar(
            select(func.count()).select_from(User)
        )
        
        # Check projects
        projects_without_team = await db.scalar(
            select(func.count()).select_from(Project).where(Project.team_id.is_(None))
        )
        total_projects = await db.scalar(
            select(func.count()).select_from(Project)
        )
        
        # Check orgs and teams
        org_count = await db.scalar(select(func.count()).select_from(Organization))
        team_count = await db.scalar(select(func.count()).select_from(Team))
        
        print("=" * 50)
        print("MIGRATION VERIFICATION REPORT")
        print("=" * 50)
        print(f"Organizations: {org_count}")
        print(f"Teams: {team_count}")
        print(f"Users: {total_users} (without org: {users_without_org})")
        print(f"Projects: {total_projects} (without team: {projects_without_team})")
        print("=" * 50)
        
        if users_without_org == 0 and projects_without_team == 0:
            print("✅ MIGRATION SUCCESSFUL - All data migrated")
            return True
        else:
            print("❌ MIGRATION INCOMPLETE - Some records not migrated")
            return False

if __name__ == "__main__":
    asyncio.run(verify())
```

---

## ✅ Definition of Done

### Testing Complete
- [ ] 10+ E2E tests passing
- [ ] 50+ backend integration tests passing (Sprint 70-71 + new)
- [ ] Cross-browser testing complete
- [ ] All tests run in CI/CD

### Migration Complete
- [ ] All users have organization_id
- [ ] All projects have team_id
- [ ] Verification script passes
- [ ] No data loss

### Deployment Complete
- [ ] Staging deployed and tested
- [ ] Production deployed successfully
- [ ] No errors in monitoring (1 hour)
- [ ] Rollback plan tested

### Documentation Complete
- [ ] OpenAPI spec updated
- [ ] User guide published
- [ ] Onboarding docs updated

### Approvals
- [ ] CTO review score ≥ 9.0/10
- [ ] CEO Go-Live sign-off

---

## 📅 Daily Schedule

### Day 1 (Mon, Feb 10)
- [ ] Morning: E2E test setup (S73-T01 to T03)
- [ ] Afternoon: E2E test implementation
- [ ] EOD: 5+ E2E tests passing

### Day 2 (Tue, Feb 11)
- [ ] Morning: Complete E2E tests (S73-T04 to T06)
- [ ] Afternoon: Backend integration tests (S73-T07 to T11)
- [ ] EOD: All tests passing

### Day 3 (Wed, Feb 12)
- [ ] Morning: Data migration scripts (S73-T12 to T16)
- [ ] Afternoon: Test migration on staging (S73-T17)
- [ ] EOD: Migration verified on staging

### Day 4 (Thu, Feb 13)
- [ ] Morning: Production deployment (S73-T18 to T21)
- [ ] Afternoon: Smoke tests and monitoring (S73-T22 to T23)
- [ ] EOD: Production live

### Day 5 (Fri, Feb 14)
- [ ] Morning: Documentation (S73-T24 to T26)
- [ ] Afternoon: CTO review, CEO sign-off (S73-T27 to T28)
- [ ] EOD: **Go-Live APPROVED** 🎉

---

## 📈 Sprint 70-73 Summary

| Sprint | Focus | Status | Tests |
|--------|-------|--------|-------|
| Sprint 70 | Models & Migration | ⏳ | 20 unit |
| Sprint 71 | Backend API | ⏳ | 30 integration |
| Sprint 72 | Frontend | ⏳ | - |
| Sprint 73 | Integration & Deploy | ⏳ | 10 E2E |
| **Total** | **Teams Complete** | ⏳ | **60 tests** |

### Final Checklist

- [ ] Organizations table created
- [ ] Teams table created
- [ ] TeamMembers table created
- [ ] User.organization_id FK added
- [ ] Project.team_id FK added
- [ ] 14 API endpoints implemented
- [ ] Frontend Teams UI complete
- [ ] i18n (EN/VN) complete
- [ ] 60 tests passing
- [ ] Data migration complete
- [ ] Production deployed
- [ ] Documentation updated
- [ ] CTO approved
- [ ] CEO signed off
- [ ] **🚀 GO-LIVE: February 24, 2026**

---

## 🔗 References

- [Sprint 70: Teams Foundation](./SPRINT-70-TEAMS-FOUNDATION.md)
- [Sprint 71: Teams Backend API](./SPRINT-71-TEAMS-BACKEND-API.md)
- [Sprint 72: Teams Frontend](./SPRINT-72-TEAMS-FRONTEND.md)
- [ADR-028: Teams Feature Remediation](../../06-deploy/TEAMS-FEATURE-REMEDIATION-PLAN.md)
- [CTO Go-Live Plan](../../06-deploy/CTO-REVIEW-GOLIVE-PLAN.md)
