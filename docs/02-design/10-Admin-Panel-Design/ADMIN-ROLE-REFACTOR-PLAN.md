# Platform Admin Role Refactor Plan
## Sprint 87 - Remove Customer Data Access from Platform Admins

**Date**: January 21, 2026
**Status**: APPROVED (CEO + CTO)
**Priority**: P0 - Security & Privacy Issue
**Framework**: SDLC 6.1.0
**Related**: ADR-030 (Platform Admin Role Redesign)

---

## 🔴 Current Problem

### Issue Discovered (Jan 21, 2026)

**Stakeholder Feedback**:
> "Platform admin chức năng chính là quản trị và hỗ trợ người dùng và vận hành hệ thống, chứ không phải platform admin là 1 super user được quản trị mọi project của khách hàng."
>
> "Project của khách hàng về cơ bản là thông tin riêng của khách hàng chúng ta không được truy cập trực tiếp."

### Current State Analysis

**Admin Panel (`/admin`)**: ✅ GOOD
- Has dedicated `AdminSidebar` with system operations only:
  - Overview, Users, Audit Logs, Overrides, System Health, AI Providers, Settings
- NO customer data visible in admin panel itself

**The Problem**: ❌ "Back to App" Link
```typescript
// frontend/src/components/admin/AdminSidebar.tsx
// Line 182-190
<Link
  href="/app"  // ❌ THIS IS THE PROBLEM
  className="..."
>
  <ArrowLeftIcon className="h-5 w-5 flex-shrink-0" />
  {!isCollapsed && <span>Back to App</span>}
</Link>
```

This link allows Platform Admin to:
- ❌ Access `/app/projects` - See all customer projects
- ❌ Access `/app/gates` - See all customer gates
- ❌ Access `/app/evidence` - See all customer evidence
- ❌ Access `/app/teams` - See all customer teams
- ❌ Access `/app/organizations` - See all customer organizations
- ❌ Access `/app/agents-md` - See all customer AGENTS.md files
- ❌ Access `/app/check-runs` - See all customer check runs

### Security Risk

**GDPR Violation**: Platform admins accessing customer data without consent
**Trust Issue**: Customers expect privacy (like AWS, GitHub, Slack model)
**Legal Liability**: If leaked, could face lawsuits

---

## ✅ Required Changes

### 1. Frontend Changes

#### A. Remove "Back to App" Link from AdminSidebar

**File**: `frontend/src/components/admin/AdminSidebar.tsx`

```typescript
// BEFORE (Line 182-191):
{/* Back to App link */}
<div className="border-b border-gray-700 px-2 py-2">
  <Link
    href="/app"  // ❌ DELETE THIS LINK
    className="..."
  >
    <ArrowLeftIcon className="h-5 w-5 flex-shrink-0" />
    {!isCollapsed && <span>Back to App</span>}
  </Link>
</div>

// AFTER:
{/* Removed: Platform admins should NOT access customer UI */}
```

#### B. Block Platform Admins from `/app/*` Routes

**File**: `frontend/src/app/app/layout.tsx`

```typescript
// Add check in AppLayout
export default function AppLayout({ children }: { children: React.ReactNode }) {
  const { user } = useAuth();

  // NEW: Redirect platform admins to /admin
  if (user?.is_platform_admin) {
    redirect("/admin");
    return null;
  }

  // Rest of layout for regular users...
  return (
    <QueryProvider>
      <AuthProvider>
        <AuthGuard>
          <div className="flex h-screen bg-gray-50">
            <Sidebar />  {/* Customer sidebar */}
            <div className="flex flex-1 flex-col">
              <Header />
              <main className="flex-1 overflow-y-auto p-6">
                {children}
              </main>
            </div>
          </div>
        </AuthGuard>
      </AuthProvider>
    </QueryProvider>
  );
}
```

#### C. Auto-redirect Platform Admins on Login

**File**: `frontend/src/app/login/page.tsx`

```typescript
// In LoginForm component, after successful login:
const handleSubmit = async (e: React.FormEvent) => {
  e.preventDefault();

  try {
    const response = await login({ email, password });

    // Store tokens
    localStorage.setItem("access_token", response.access_token);

    // NEW: Check if user is platform admin
    const userProfile = await getCurrentUser();

    if (userProfile.is_platform_admin) {
      // Redirect admins to /admin (system operations)
      router.push("/admin");
    } else {
      // Redirect regular users to /app (customer features)
      router.push(redirectTo || "/app");
    }
  } catch (error) {
    // Error handling...
  }
};
```

#### D. Update Header to Show Correct Link

**File**: `frontend/src/components/landing/Header.tsx`

```typescript
// Line 110-114: Change Dashboard link based on user role
<Button asChild variant="ghost" size="sm">
  <Link href={user.is_platform_admin ? "/admin" : "/app"}>
    {user.is_platform_admin ? "Admin Panel" : "Dashboard"}
  </Link>
</Button>
```

### 2. Backend Changes

#### A. Add `is_platform_admin` Field to User Model

**File**: `backend/app/models/user.py`

```python
class User(Base):
    __tablename__ = "users"

    # EXISTING
    id: UUID
    organization_id: UUID | None  # Platform admins should have NULL
    email: str
    is_superuser: bool

    # NEW (Add this field)
    is_platform_admin: bool = Column(Boolean, default=False, nullable=False)
    # When True: User is a platform operator (system admin)
    # When False: User is a customer (can access /app)

    # RULE: is_platform_admin=True → organization_id MUST be NULL
    # Platform admins don't belong to any customer organization
```

#### B. Database Migration

**File**: `backend/alembic/versions/s87_add_platform_admin_flag.py`

```python
"""add platform_admin flag to users

Revision ID: s87_platform_admin
Revises: s86_xxx
Create Date: 2026-01-21 14:00:00

"""
from alembic import op
import sqlalchemy as sa


def upgrade():
    # Add is_platform_admin column
    op.add_column('users', sa.Column('is_platform_admin', sa.Boolean(), nullable=False, server_default='false'))

    # Set existing superusers as platform admins
    op.execute("""
        UPDATE users
        SET is_platform_admin = TRUE
        WHERE is_superuser = TRUE
    """)

    # Platform admins should NOT belong to any organization
    op.execute("""
        UPDATE users
        SET organization_id = NULL
        WHERE is_platform_admin = TRUE
    """)

    # Add constraint: platform admins cannot have organization_id
    op.create_check_constraint(
        'ck_platform_admin_no_org',
        'users',
        'NOT (is_platform_admin = TRUE AND organization_id IS NOT NULL)'
    )


def downgrade():
    op.drop_constraint('ck_platform_admin_no_org', 'users')
    op.drop_column('users', 'is_platform_admin')
```

#### C. Block Platform Admins from Customer Endpoints

**File**: `backend/app/api/dependencies.py`

```python
# NEW dependency: Ensure user is NOT a platform admin
async def require_customer_user(
    current_user: User = Depends(get_current_user),
) -> User:
    """
    Dependency that ensures user is a CUSTOMER (not platform admin).

    Platform admins should NOT access customer endpoints.
    This enforces privacy boundary.
    """
    if current_user.is_platform_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Platform admins cannot access customer data. Go to /admin instead."
        )
    return current_user
```

**Apply to all customer endpoints**:

```python
# backend/app/api/routes/projects.py
@router.get("/projects")
async def list_projects(
    current_user: User = Depends(require_customer_user),  # ✅ Changed from get_current_user
    db: AsyncSession = Depends(get_db),
) -> ProjectsResponse:
    """List projects for current customer user."""
    # Now platform admins will get 403 Forbidden
    pass

# Apply same change to:
# - backend/app/api/routes/gates.py
# - backend/app/api/routes/evidence.py
# - backend/app/api/routes/teams.py
# - backend/app/api/routes/organizations.py
# - backend/app/api/routes/agents.py
# - backend/app/api/routes/check_runs.py
# - All other customer-facing endpoints
```

### 3. API Response Changes

#### Update User Profile Endpoint

**File**: `backend/app/api/routes/auth.py`

```python
class UserProfile(BaseModel):
    id: str
    email: str
    full_name: Optional[str]
    organization_id: Optional[str]  # NULL for platform admins
    role: str
    is_active: bool
    is_superuser: bool
    is_platform_admin: bool  # ✅ NEW: Add this field
    # ... other fields

@router.get("/me", response_model=UserProfile)
async def get_current_user_profile(
    current_user: User = Depends(get_current_user),
) -> UserProfile:
    """Get current user profile (works for both customers and admins)."""
    return UserProfile(
        id=str(current_user.id),
        email=current_user.email,
        full_name=current_user.full_name,
        organization_id=str(current_user.organization_id) if current_user.organization_id else None,
        role=current_user.role,
        is_active=current_user.is_active,
        is_superuser=current_user.is_superuser,
        is_platform_admin=current_user.is_platform_admin,  # ✅ NEW
        # ... other fields
    )
```

---

## 📋 Implementation Checklist

### Phase 1: Database (Sprint 87 Day 1)

- [ ] Create migration: Add `is_platform_admin` column
- [ ] Mark existing `is_superuser=True` users as `is_platform_admin=True`
- [ ] Set `organization_id=NULL` for platform admins
- [ ] Add constraint: Platform admins cannot have `organization_id`
- [ ] Run migration on local dev database
- [ ] Verify: `SELECT * FROM users WHERE is_platform_admin=TRUE`

### Phase 2: Backend API (Sprint 87 Day 2-3)

- [ ] Add `is_platform_admin` field to User model
- [ ] Update `UserProfile` schema to include `is_platform_admin`
- [ ] Create `require_customer_user` dependency
- [ ] Apply to **all customer endpoints**:
  - [ ] `projects.py` (all endpoints)
  - [ ] `gates.py` (all endpoints)
  - [ ] `evidence.py` (all endpoints)
  - [ ] `teams.py` (all endpoints)
  - [ ] `organizations.py` (all endpoints)
  - [ ] `agents.py` (all endpoints)
  - [ ] `check_runs.py` (all endpoints)
  - [ ] `dashboard.py` (all endpoints)
  - [ ] `analytics.py` (customer endpoints only)
  - [ ] Any other customer-facing routes
- [ ] Test: Platform admin gets 403 on `/api/v1/projects`
- [ ] Test: Regular user still works on `/api/v1/projects`

### Phase 3: Frontend UI (Sprint 87 Day 4-5)

- [ ] Remove "Back to App" link from `AdminSidebar.tsx`
- [ ] Add redirect in `/app` layout: Platform admins → `/admin`
- [ ] Update login flow: Check `is_platform_admin` and redirect accordingly
- [ ] Update Header: Show "Admin Panel" or "Dashboard" based on role
- [ ] Add `is_platform_admin` to API types
- [ ] Test: Platform admin cannot access `/app/projects` (redirects to `/admin`)
- [ ] Test: Regular user cannot access `/admin` (redirects to `/app`)

### Phase 4: Testing (Sprint 87 Day 6)

- [ ] Unit tests: `require_customer_user` dependency
- [ ] Integration tests: Platform admin gets 403 on customer endpoints
- [ ] E2E tests: Platform admin workflow (login → admin panel only)
- [ ] E2E tests: Regular user workflow (login → app dashboard)
- [ ] Security test: Try to access `/app/projects` as platform admin (should fail)

### Phase 5: Documentation (Sprint 87 Day 7)

- [ ] Update ADR-017 status to "SUPERSEDED BY ADR-030"
- [ ] Finalize ADR-030: Platform Admin Role Redesign
- [ ] Update `ADMIN-PANEL-REQUIREMENTS.md`
- [ ] Update API documentation (OpenAPI spec)
- [ ] Write migration guide for existing platform admins

---

## 🧪 Testing Scenarios

### Scenario 1: Platform Admin Attempts to Access Customer Data

```gherkin
Feature: Platform Admin Privacy Boundary

  Scenario: Platform admin tries to view customer projects
    Given I am logged in as platform admin (is_platform_admin=True)
    When I navigate to /app/projects
    Then I should be redirected to /admin
    And I should see "Access Denied" message
    And audit log should record "UNAUTHORIZED_ACCESS_ATTEMPT"

  Scenario: Platform admin API call to customer endpoint
    Given I am logged in as platform admin
    When I call GET /api/v1/projects
    Then I should receive 403 Forbidden
    And response should say "Platform admins cannot access customer data"
```

### Scenario 2: Regular User Cannot Access Admin Panel

```gherkin
Feature: Customer User Access Control

  Scenario: Customer user tries to access admin panel
    Given I am logged in as regular user (is_platform_admin=False)
    When I navigate to /admin
    Then I should be redirected to /app
    And I should see "Admin access required" message
```

### Scenario 3: Login Redirect Based on Role

```gherkin
Feature: Role-Based Login Redirect

  Scenario: Platform admin login
    Given I am on /login page
    When I login with platform admin credentials
    Then I should be redirected to /admin
    And I should see "Admin Panel" in header

  Scenario: Regular user login
    Given I am on /login page
    When I login with regular user credentials
    Then I should be redirected to /app
    And I should see "Dashboard" in header
```

---

## 🚨 Breaking Changes

### For Existing Platform Admins

**BEFORE**:
- Platform admin could access `/app` and see all customer projects
- Had both admin panel AND customer dashboard

**AFTER**:
- Platform admin CANNOT access `/app`
- Only has admin panel (`/admin`)
- If they need customer account, must create separate user account

### Migration Instructions for Ops Team

```markdown
## For Platform Admin Users (is_superuser=True)

Your account has been updated to reflect your role as a **Platform Operator**.

**What Changed**:
1. You can NO LONGER access `/app` (customer dashboard)
2. Your account now has `organization_id=NULL` (you don't belong to any customer org)
3. If you need to test customer features, create a separate test user account

**What You CAN Do**:
- Manage users via `/admin/users`
- View system health via `/admin/health`
- Manage system settings via `/admin/settings`
- View audit logs via `/admin/audit-logs`
- Manage AI providers via `/admin/ai-providers`

**What You CANNOT Do**:
- View customer projects, gates, evidence
- Access customer AGENTS.md files
- View customer teams/organizations
- Edit customer data

**If you need to access a customer's data for support**:
1. Customer must grant you temporary access (future feature)
2. Access is time-limited (24 hours)
3. All actions are audit logged
```

---

## 📊 Success Metrics

| Metric | Target | Verification Method |
|--------|--------|---------------------|
| **Privacy Enforcement** | 0 platform admins can access customer data | E2E test + manual audit |
| **API Isolation** | 100% customer endpoints return 403 for admins | Integration tests |
| **Login Redirect** | 100% admins go to `/admin`, users to `/app` | E2E test |
| **Performance** | No degradation (<100ms API latency) | Benchmark before/after |
| **Zero Regression** | Regular users unaffected | Full regression test suite |

---

## 🔄 Rollback Plan

If critical issues found:

1. **Database**: Rollback migration `s87_platform_admin`
   ```bash
   alembic downgrade -1
   ```

2. **Backend**: Revert PR with `require_customer_user` changes

3. **Frontend**: Revert PR with "Back to App" link removal

4. **Estimated Rollback Time**: <30 minutes

---

## 📅 Timeline

| Day | Task | Owner | Status |
|-----|------|-------|--------|
| **Day 1** | Database migration | Backend Lead | ⏳ |
| **Day 2-3** | Backend API changes | Backend Team | ⏳ |
| **Day 4-5** | Frontend UI changes | Frontend Team | ⏳ |
| **Day 6** | Testing (Unit + E2E) | QA Team | ⏳ |
| **Day 7** | Documentation | PM | ⏳ |
| **Day 8** | Code review + merge | CTO | ⏳ |
| **Day 9** | Deploy to staging | DevOps | ⏳ |
| **Day 10** | Production deploy | DevOps + CTO | ⏳ |

**Total**: 2 weeks (Sprint 87)

---

## ✅ Approval

- [x] **CEO Approved**: January 21, 2026 (Verbal feedback)
- [x] **CTO Approved**: January 21, 2026 (Verbal feedback)
- [ ] **Backend Lead Review**: Pending
- [ ] **Frontend Lead Review**: Pending
- [ ] **Security Lead Approval**: Pending
- [ ] **Legal Counsel Review**: Pending (GDPR compliance)

---

## 📚 References

- ADR-030: Platform Admin Role Redesign
- ADR-017: Admin Panel Architecture (SUPERSEDED)
- GDPR Article 25: Privacy by Design
- SOC 2 CC7.1: Access Control Requirements

---

**Document Status**: ✅ READY FOR IMPLEMENTATION
**Sprint**: Sprint 87 - Admin Role Refactoring
**Priority**: P0 - Security & Privacy
**Owner**: CTO + Backend Lead + Frontend Lead
