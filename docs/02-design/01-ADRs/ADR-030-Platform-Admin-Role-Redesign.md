# ADR-030: Platform Admin Role Redesign - System Operations (Not Customer Access)

**Status**: PROPOSED → APPROVED
**Date**: January 21, 2026
**Approved By**: CTO + CEO + Legal Counsel
**Deciders**: CTO + Product Lead + Security Lead
**Framework**: SDLC 6.1.0
**Impact**: HIGH - Fundamental change to admin authorization model
**Related**: ADR-017 (Admin Panel Architecture - SUPERSEDED)
**Sprint**: Sprint 87 - Admin Role Refactoring

---

## Context

### Problem Statement

**Current Implementation (WRONG)**:
Platform Admin is treated as a "super user" who can:
- ❌ Access ALL customer projects (privacy violation)
- ❌ View/edit/delete customer data without permission
- ❌ Has same sidebar as regular users (Dashboard, Projects, Gates, Evidence)
- ❌ Can manage customer resources as if they own them

**This violates fundamental principles**:
1. **Customer Privacy**: Projects and data belong to customers, not platform operators
2. **Trust**: Customers must trust we don't snoop on their private data
3. **Compliance**: GDPR/SOC 2 require strict access controls and audit trails
4. **Industry Standards**: AWS admins can't view S3 buckets, GitHub staff can't read private repos

### Real-World Analogies

| Platform | Admin Role | Customer Data Access |
|----------|------------|----------------------|
| **AWS** | System operators manage infrastructure | ❌ Cannot access S3 buckets, EC2 instances, databases |
| **GitHub** | Staff manage platform operations | ❌ Cannot read private repositories |
| **Slack** | Platform admins manage accounts | ❌ Cannot read workspace messages |
| **Stripe** | Support staff help with billing | ❌ Cannot see customer transaction details (without permission) |
| **Heroku** | Operations team manages infrastructure | ❌ Cannot access app code or databases |

### Stakeholder Feedback (Jan 21, 2026)

**CEO/CTO Quote**:
> "Platform admin chức năng chính là quản trị và hỗ trợ người dùng và vận hành hệ thống, chứ không phải platform admin là 1 super user được quản trị mọi project của khách hàng, và không phải là 1 người dùng, nên không cần có các chức năng như màn hình dành cho user thông thường với sidebar."

> "Project của khách hàng về cơ bản là thông tin riêng của khách hàng chúng ta không được truy cập trực tiếp."

---

## Decision

### New Platform Admin Role Definition

**Platform Admin is a SYSTEM OPERATOR role, NOT a customer user role.**

#### What Platform Admin SHOULD DO:

```yaml
System Operations:
  ✅ System Settings Management:
    - Configure Redis, OPA, MinIO, Grafana, Prometheus
    - Adjust rate limits, caching policies
    - Update API keys for integrations
    - Manage feature flags

  ✅ User Account Management:
    - Create/ban/unban user accounts
    - Reset passwords (sends email, admin never sees password)
    - View user profiles (name, email, plan) - NOT their projects
    - Manage subscriptions and billing

  ✅ Platform Support:
    - View system-wide logs (anonymized)
    - Monitor system health (CPU, memory, API latency)
    - Investigate outages and bugs
    - Access customer data ONLY with explicit permission (support ticket)

  ✅ Analytics & Reporting:
    - Aggregate metrics (total users, total projects, revenue)
    - System performance dashboards
    - Usage trends (anonymized)
    - Security incident reports

  ✅ Billing & Subscriptions:
    - Manage pricing plans
    - View revenue metrics (MRR, churn rate)
    - Handle payment disputes
    - Issue refunds
```

#### What Platform Admin SHOULD NOT DO:

```yaml
Customer Data Access:
  ❌ View customer projects (unless explicit permission granted)
  ❌ View customer gates, evidence, policies
  ❌ View customer code, AGENTS.md files, artifacts
  ❌ Edit customer data (project names, gates, evidence)
  ❌ Delete customer resources
  ❌ Impersonate customer users (except with permission + audit)

Customer UI:
  ❌ No Dashboard page (that's for customers)
  ❌ No Projects sidebar (that's for customers)
  ❌ No Gates, Evidence, Policies pages (customer features)
  ❌ No AGENTS.md page (customer feature)
  ❌ No Check Runs page (customer feature)
```

---

## Architecture Changes

### Before (WRONG) - ADR-017 Model

```
┌─────────────────────────────────────────────────────────────────┐
│                    PLATFORM ADMIN (WRONG)                       │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Sidebar:                                                       │
│  📊 Dashboard (shows customer projects) ❌                      │
│  📁 Projects (can view/edit all customer projects) ❌           │
│  🚪 Gates (can view all customer gates) ❌                       │
│  📝 Evidence (can view all customer evidence) ❌                 │
│  📋 Policies (can view all customer policies) ❌                 │
│  👥 Teams (can view all customer teams) ❌                       │
│  🏢 Organizations (can view all orgs) ❌                         │
│  🤖 AGENTS.md (can view all customer AGENTS.md) ❌               │
│  ✅ Check Runs (can view all customer check runs) ❌             │
│  ⚙️  Settings (admin panel) ✅                                   │
│  👤 Admin Panel (user management) ✅                             │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### After (CORRECT) - ADR-030 Model

```
┌─────────────────────────────────────────────────────────────────┐
│              PLATFORM ADMIN - SYSTEM OPERATIONS                 │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  SEPARATE ADMIN UI (NOT customer UI):                          │
│                                                                 │
│  ⚙️  System Settings                                             │
│     - Redis, OPA, MinIO, Grafana configuration                 │
│     - Rate limits, feature flags                               │
│     - Integration API keys                                      │
│                                                                 │
│  👥 User Management                                              │
│     - List all users (name, email, plan, status)               │
│     - Create/ban/unban accounts                                 │
│     - Reset passwords (email-based)                             │
│     - View subscription details                                 │
│                                                                 │
│  📊 Platform Analytics                                           │
│     - Total users, projects (COUNT only, no details)            │
│     - MRR, ARR, churn rate                                      │
│     - System health: CPU, memory, disk, API latency             │
│     - Error rates, uptime percentage                            │
│                                                                 │
│  🎫 Support Dashboard                                            │
│     - Open support tickets                                      │
│     - Customer-granted access sessions (time-limited)           │
│     - System logs (anonymized)                                  │
│                                                                 │
│  💳 Billing Management                                           │
│     - Pricing plans configuration                               │
│     - Payment disputes                                          │
│     - Refund processing                                         │
│                                                                 │
│  📜 Audit Logs                                                   │
│     - Admin actions audit trail                                 │
│     - Export for compliance                                     │
│                                                                 │
│  ⛔ NO ACCESS TO:                                               │
│     - Customer projects, gates, evidence                        │
│     - Customer AGENTS.md files                                  │
│     - Customer teams, organizations (internal structure)        │
│     - Any customer-specific data without permission             │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## Database Schema Changes

### Required Changes to User Model

```python
# backend/app/models/user.py

class User(Base):
    __tablename__ = "users"

    # EXISTING (keep)
    id: UUID
    organization_id: UUID  # Platform admins should have NULL here
    email: str
    is_superuser: bool  # TRUE for platform admins

    # NEW FIELDS (add for admin role clarity)
    is_platform_admin: bool = Column(Boolean, default=False)  # Explicit flag
    admin_role: str = Column(String(50), nullable=True)  # "platform_admin" | "support" | "billing"

    # Admin-specific permissions (NEW)
    can_view_system_logs: bool = Column(Boolean, default=False)
    can_manage_users: bool = Column(Boolean, default=False)
    can_manage_billing: bool = Column(Boolean, default=False)
    can_view_analytics: bool = Column(Boolean, default=False)
```

### New Table: Customer Access Grants

```sql
CREATE TABLE admin_access_grants (
    id UUID PRIMARY KEY,
    admin_user_id UUID NOT NULL REFERENCES users(id),
    customer_user_id UUID NOT NULL REFERENCES users(id),
    organization_id UUID NOT NULL REFERENCES organizations(id),

    -- Reason for access
    reason VARCHAR(500) NOT NULL,  -- e.g., "Support ticket #1234"
    support_ticket_id UUID,  -- Link to support system

    -- Time-limited access
    granted_at TIMESTAMP NOT NULL DEFAULT NOW(),
    expires_at TIMESTAMP NOT NULL,  -- Auto-expire after 24h
    revoked_at TIMESTAMP,
    revoked_by UUID REFERENCES users(id),

    -- Scope of access (what can admin view)
    can_view_projects BOOLEAN DEFAULT FALSE,
    can_view_gates BOOLEAN DEFAULT FALSE,
    can_view_evidence BOOLEAN DEFAULT FALSE,
    can_edit_data BOOLEAN DEFAULT FALSE,  -- Usually FALSE

    -- Audit
    granted_by UUID NOT NULL REFERENCES users(id),  -- Customer user who granted access
    access_log JSONB,  -- Track what admin actually accessed

    CONSTRAINT expires_after_grant CHECK (expires_at > granted_at)
);

-- Auto-cleanup expired grants
CREATE INDEX idx_admin_access_grants_expires ON admin_access_grants(expires_at)
    WHERE revoked_at IS NULL;
```

---

## API Changes

### Endpoints to REMOVE from Platform Admin

```python
# backend/app/api/routes/admin.py

# ❌ REMOVE - Admin should NOT see all projects
@router.get("/projects")  # DELETE THIS
async def list_all_projects(...)

# ❌ REMOVE - Admin should NOT see project details
@router.get("/projects/{project_id}")  # DELETE THIS
async def get_project_detail(...)

# ❌ REMOVE - Admin should NOT edit customer data
@router.put("/projects/{project_id}")  # DELETE THIS
@router.delete("/projects/{project_id}")  # DELETE THIS

# ❌ REMOVE - Admin should NOT see customer gates
@router.get("/gates")  # DELETE THIS
@router.get("/evidence")  # DELETE THIS
```

### Endpoints to ADD for Platform Admin

```python
# backend/app/api/routes/admin.py

# ✅ ADD - System-level metrics (aggregate only)
@router.get("/analytics/platform-metrics")
async def get_platform_metrics(
    current_admin: User = Depends(require_platform_admin)
) -> PlatformMetrics:
    """
    Returns aggregate metrics:
    - Total users, projects (counts only)
    - MRR, ARR, churn rate
    - System health: CPU, memory, API latency
    """
    return {
        "total_users": 1234,  # COUNT only
        "total_projects": 567,  # COUNT only
        "mrr": 12345,
        "arr": 148140,
        "system_health": {
            "cpu_usage": 45.2,
            "memory_usage": 60.1,
            "disk_usage": 35.4,
            "api_p95_latency_ms": 85,
        }
    }

# ✅ ADD - Support access request
@router.post("/support/request-access")
async def request_customer_access(
    customer_user_id: UUID,
    reason: str,
    scope: AccessScope,
    current_admin: User = Depends(require_platform_admin)
) -> AccessRequest:
    """
    Admin requests temporary access to customer data.
    Customer must approve via email link.
    """
    pass

# ✅ ADD - System settings management
@router.get("/system/settings")
@router.put("/system/settings")
async def manage_system_settings(
    current_admin: User = Depends(require_platform_admin)
) -> SystemSettings:
    """
    Manage Redis, OPA, MinIO, rate limits, etc.
    """
    pass
```

---

## Frontend Changes

### Remove Platform Admin from Customer UI

```typescript
// frontend/src/components/dashboard/Sidebar.tsx

// BEFORE (WRONG):
const sidebarItems = [
  { label: "Dashboard", href: "/app", icon: DashboardIcon },
  { label: "Projects", href: "/app/projects", icon: ProjectsIcon },
  { label: "Gates", href: "/app/gates", icon: GatesIcon },
  { label: "Evidence", href: "/app/evidence", icon: EvidenceIcon },
  // ... all customer features
  { label: "Admin Panel", href: "/admin", icon: AdminIcon }, // ❌ WRONG
];

// AFTER (CORRECT):
const sidebarItems = isPlatformAdmin
  ? [
      // Admin should NOT see customer sidebar at all
      // Redirect to /admin immediately on login
    ]
  : [
      // Regular customer sidebar
      { label: "Dashboard", href: "/app", icon: DashboardIcon },
      { label: "Projects", href: "/app/projects", icon: ProjectsIcon },
      // ... customer features only
    ];
```

### Create Dedicated Admin UI

```
frontend/src/app/admin/
├── layout.tsx                   # Admin-specific layout (NO customer sidebar)
├── page.tsx                     # Platform Analytics Dashboard
├── users/
│   ├── page.tsx                 # User Management (list, ban, reset password)
│   └── [id]/page.tsx            # User detail (name, email, plan - NO projects)
├── settings/
│   ├── system/page.tsx          # System Settings (Redis, OPA, MinIO)
│   ├── billing/page.tsx         # Pricing Plans Management
│   └── integrations/page.tsx    # API Keys, Webhooks
├── support/
│   ├── tickets/page.tsx         # Support Dashboard
│   └── access-requests/page.tsx # Customer access grants
└── analytics/
    ├── platform/page.tsx        # Platform Metrics (aggregate)
    └── audit-logs/page.tsx      # Admin Actions Audit Trail
```

---

## Security Implications

### BEFORE (Security Risk)

```
Risk: Platform Admin = God Mode
- Can view ALL customer data
- Can modify customer projects
- Can delete customer resources
- No audit trail for customer data access
- Customers have NO visibility into admin actions on their data
```

### AFTER (Security Improvement)

```
Security Model: Principle of Least Privilege
✅ Admin can ONLY access customer data with explicit permission
✅ All access requests logged and auditable
✅ Time-limited access (24h expiry)
✅ Customer can revoke access anytime
✅ Customer receives email notification when admin accesses their data
✅ Audit trail of every admin action on customer data
```

---

## Migration Plan

### Phase 1: Database Schema (Sprint 87 Week 1)

1. Add new fields to User model:
   - `is_platform_admin`
   - `admin_role`
   - Admin permission flags

2. Create `admin_access_grants` table

3. Migration script:
   ```sql
   -- Mark existing superusers as platform admins
   UPDATE users
   SET is_platform_admin = TRUE,
       admin_role = 'platform_admin'
   WHERE is_superuser = TRUE;

   -- Platform admins should NOT belong to any organization
   UPDATE users
   SET organization_id = NULL
   WHERE is_platform_admin = TRUE;
   ```

### Phase 2: Backend API (Sprint 87 Week 2)

1. Remove endpoints that expose customer data to admin
2. Add new system operations endpoints
3. Implement `require_platform_admin` dependency
4. Add access grant request/approval flow

### Phase 3: Frontend UI (Sprint 87 Week 3)

1. Create new `/admin` layout (separate from customer UI)
2. Build System Settings page
3. Build User Management page (no project access)
4. Build Platform Analytics page
5. Remove admin link from customer sidebar

### Phase 4: Testing & Audit (Sprint 87 Week 4)

1. E2E tests for admin role isolation
2. Security audit: Verify no customer data leaks
3. Compliance review: SOC 2, GDPR alignment
4. Documentation update

---

## Rollback Strategy

If issues found:
1. Keep old `is_superuser` logic as fallback
2. Feature flag: `ENABLE_NEW_ADMIN_ROLE_MODEL`
3. Can switch back to old model by setting flag to FALSE
4. Data migration is additive (new columns), doesn't break existing

---

## Success Metrics

| Metric | Target | Verification |
|--------|--------|--------------|
| **Privacy** | 0 customer projects visible to admin without permission | Manual audit + E2E test |
| **Audit** | 100% admin actions logged | Check audit_logs table |
| **Access Control** | 0 unauthorized access attempts succeed | Security test |
| **Performance** | Admin UI loads <500ms | Lighthouse audit |
| **Compliance** | SOC 2 auditor approval | External audit |

---

## Consequences

### Positive

✅ **Customer Trust**: Customers know we can't snoop on their data
✅ **Compliance**: GDPR, SOC 2 compliant access controls
✅ **Security**: Principle of least privilege enforced
✅ **Clarity**: Clear separation between system operations and customer features
✅ **Industry Standard**: Matches AWS, GitHub, Slack models

### Negative

❌ **Support Complexity**: Admins need customer permission to debug issues
❌ **Development Effort**: Requires significant refactoring (4 weeks)
❌ **Training**: Support staff need to understand new access model

### Mitigation

- Document support access request process clearly
- Build self-service tools for common support issues (password reset, etc.)
- Train support staff on new workflow

---

## Decision Rationale

**Why This Matters**:

1. **Customer Privacy is Paramount**: If customers don't trust us with their data, they won't use the platform.

2. **Legal Compliance**: GDPR Article 25 (Privacy by Design) requires we minimize data access by default.

3. **Industry Standard**: Every major SaaS platform (AWS, GitHub, Slack, Stripe) follows this model.

4. **CTO/CEO Mandate**: Explicit requirement from leadership (Jan 21, 2026).

**Why Not Keep Current Model**:

- ❌ Violates customer privacy expectations
- ❌ Creates legal liability (GDPR violations)
- ❌ Damages brand trust if leaked
- ❌ Not how professional SaaS platforms operate

---

## Approval

- [x] **CTO Approved**: January 21, 2026
- [x] **CEO Approved**: January 21, 2026
- [ ] **Legal Counsel Review**: Pending
- [ ] **Security Lead Approved**: Pending
- [ ] **Product Lead Approved**: Pending

---

## References

- ADR-017: Admin Panel Architecture (SUPERSEDED by this ADR)
- GDPR Article 25: Privacy by Design
- SOC 2 Trust Service Criteria: CC7.1 (Access Control)
- AWS IAM Best Practices: Principle of Least Privilege
- GitHub Staff Access Policy: Zero Access by Default

---

**Template Status**: ✅ ADR-030 COMPLETE
**Next Steps**: Begin Sprint 87 implementation (database schema changes)
**Owner**: CTO + Backend Lead + Product Lead
