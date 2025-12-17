# SPRINT-37: Admin Panel Implementation
## SDLC 5.1.1 Complete Lifecycle - BUILD Phase

---

**Document Information**

| Field | Value |
|-------|-------|
| **Sprint ID** | SPRINT-37 |
| **Feature** | Admin Panel (P0) |
| **Duration** | 2 weeks |
| **Status** | APPROVED - Ready for Implementation |
| **Team** | 2 Backend + 2 Frontend + 1 QA |
| **Prerequisites** | CTO Approval on Design Documents |
| **CTO Approval** | December 16, 2025 |

---

## Executive Summary

Sprint 37 implements the Admin Panel feature for SDLC Orchestrator platform administrators. This sprint delivers user management, audit logging, system health monitoring, and configuration management capabilities.

**Design Documents** (Pending CTO Approval):
- [ADMIN-PANEL-REQUIREMENTS.md](../../02-design/08-Admin-Panel/ADMIN-PANEL-REQUIREMENTS.md)
- [ADMIN-PANEL-API-DESIGN.md](../../02-design/08-Admin-Panel/ADMIN-PANEL-API-DESIGN.md)
- [ADMIN-PANEL-UI-SPECIFICATION.md](../../02-design/08-Admin-Panel/ADMIN-PANEL-UI-SPECIFICATION.md)
- [ADMIN-PANEL-SECURITY-REVIEW.md](../../02-design/08-Admin-Panel/ADMIN-PANEL-SECURITY-REVIEW.md)
- [ADR-017-ADMIN-PANEL-ARCHITECTURE.md](../../02-design/03-ADRs/ADR-017-ADMIN-PANEL-ARCHITECTURE.md)

---

## Sprint Goals

### Primary Objectives
1. Implement admin API endpoints (`/api/v1/admin/*`)
2. Create Admin Panel UI with all 6 pages
3. Implement comprehensive audit logging
4. Enable runtime system configuration

### Success Criteria
| Metric | Target |
|--------|--------|
| API Response Time (p95) | < 200ms |
| Test Coverage (Backend) | > 90% |
| Test Coverage (Frontend) | > 80% |
| Security Tests | 100% pass |
| Audit Log Accuracy | 100% |

---

## Week 1: Backend Implementation

### Day 1-2: Database & Infrastructure

**Tasks**:

1. **Database Migrations**
   ```bash
   # Migration: audit_logs table
   alembic revision --autogenerate -m "add_audit_logs_table"

   # Migration: system_settings table
   alembic revision --autogenerate -m "add_system_settings_table"
   ```

2. **Audit Log Model**
   ```python
   # backend/app/models/audit_log.py
   class AuditLog(Base):
       __tablename__ = "audit_logs"

       id = Column(UUID, primary_key=True, default=uuid4)
       timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)
       action = Column(String(100), nullable=False)
       actor_id = Column(UUID, ForeignKey("users.id"), nullable=False)
       target_type = Column(String(50))
       target_id = Column(UUID)
       target_name = Column(String(255))
       details = Column(JSONB)
       ip_address = Column(String(45))  # IPv6 compatible
       user_agent = Column(Text)
   ```

3. **System Settings Model**
   ```python
   # backend/app/models/system_setting.py
   class SystemSetting(Base):
       __tablename__ = "system_settings"

       key = Column(String(100), primary_key=True)
       value = Column(JSONB, nullable=False)
       updated_at = Column(DateTime, default=datetime.utcnow)
       updated_by = Column(UUID, ForeignKey("users.id"))
   ```

**Deliverables**:
- [ ] `audit_logs` table created with indexes
- [ ] `system_settings` table created with seed data
- [ ] Alembic migrations tested
- [ ] Models with SQLAlchemy relationships

**Assignee**: Backend Lead
**Estimated**: 2 days

---

### Day 3-4: Admin Service Layer

**Tasks**:

1. **Audit Service**
   ```python
   # backend/app/services/audit_service.py
   class AuditService:
       async def log_action(
           self,
           db: Session,
           action: str,
           actor: User,
           target_type: str = None,
           target_id: UUID = None,
           target_name: str = None,
           details: dict = None,
           request: Request = None
       ) -> AuditLog:
           """Log admin action to audit trail."""
           log = AuditLog(
               action=action,
               actor_id=actor.id,
               target_type=target_type,
               target_id=target_id,
               target_name=target_name,
               details=details,
               ip_address=request.client.host if request else None,
               user_agent=request.headers.get("user-agent") if request else None
           )
           db.add(log)
           await db.commit()
           return log
   ```

2. **Admin User Service**
   ```python
   # backend/app/services/admin_user_service.py
   class AdminUserService:
       async def list_users(
           self, db: Session,
           page: int, page_size: int,
           search: str = None,
           status: str = None,
           role: str = None
       ) -> Tuple[List[User], int]:
           """List users with pagination and filters."""
           pass

       async def update_user(
           self, db: Session,
           user_id: UUID,
           updates: dict,
           current_admin: User
       ) -> User:
           """Update user with self-action validation."""
           if user_id == current_admin.id:
               raise HTTPException(400, "Cannot modify own account")
           # ... implementation
   ```

3. **Settings Service**
   ```python
   # backend/app/services/settings_service.py
   class SettingsService:
       DEFAULT_SETTINGS = {
           "security.session_timeout_minutes": 30,
           "security.max_login_attempts": 5,
           "limits.max_projects_per_user": 50,
           "limits.max_file_size_mb": 100,
           "notifications.email_enabled": True,
       }

       async def get_all(self, db: Session) -> dict:
           """Get all settings with defaults."""
           pass

       async def update(
           self, db: Session,
           updates: dict,
           admin: User
       ) -> List[str]:
           """Update settings and log changes."""
           pass
   ```

**Deliverables**:
- [ ] AuditService with all action types
- [ ] AdminUserService with CRUD operations
- [ ] SettingsService with default values
- [ ] Unit tests for all services (90%+ coverage)

**Assignee**: Backend Dev 1 + Backend Dev 2
**Estimated**: 2 days

---

### Day 5: Admin API Routes

**Tasks**:

1. **Admin Routes**
   ```python
   # backend/app/api/routes/admin.py
   from fastapi import APIRouter, Depends
   from app.api.dependencies import require_superuser

   router = APIRouter(prefix="/admin", tags=["Admin"])

   @router.get("/stats")
   async def get_admin_stats(
       db: Session = Depends(get_db),
       current_user: User = Depends(require_superuser)
   ):
       """Get admin dashboard statistics."""
       pass

   @router.get("/users")
   async def list_users(
       page: int = 1,
       page_size: int = 20,
       search: str = None,
       status: str = None,
       db: Session = Depends(get_db),
       current_user: User = Depends(require_superuser)
   ):
       """List all users with filtering."""
       pass

   @router.patch("/users/{user_id}")
   async def update_user(
       user_id: UUID,
       updates: UserUpdateSchema,
       db: Session = Depends(get_db),
       current_user: User = Depends(require_superuser),
       request: Request = None
   ):
       """Update user and create audit log."""
       pass
   ```

2. **Rate Limiting**
   ```python
   # backend/app/middleware/rate_limit.py
   from slowapi import Limiter

   admin_limiter = Limiter(key_func=get_remote_address)

   @router.get("/users")
   @admin_limiter.limit("100/minute")
   async def list_users(...):
       pass

   @router.patch("/users/{user_id}")
   @admin_limiter.limit("30/minute")
   async def update_user(...):
       pass
   ```

**Deliverables**:
- [ ] 8 admin endpoints implemented
- [ ] Rate limiting configured
- [ ] OpenAPI documentation complete
- [ ] Integration tests passing

**Assignee**: Backend Lead
**Estimated**: 1 day

---

## Week 2: Frontend Implementation

### Day 6-7: Admin Layout & Dashboard

**Tasks**:

1. **Admin Layout**
   ```tsx
   // frontend/web/src/components/admin/AdminLayout.tsx
   export function AdminLayout({ children }: { children: React.ReactNode }) {
     return (
       <div className="flex h-screen">
         <AdminSidebar />
         <main className="flex-1 overflow-auto p-6">
           {children}
         </main>
       </div>
     );
   }
   ```

2. **Admin Sidebar**
   ```tsx
   // frontend/web/src/components/admin/AdminSidebar.tsx
   const adminNavItems = [
     { href: '/admin', icon: LayoutDashboard, label: 'Dashboard' },
     { href: '/admin/users', icon: Users, label: 'Users' },
     { href: '/admin/audit-logs', icon: FileText, label: 'Audit Logs' },
     { href: '/admin/system', icon: Server, label: 'System' },
     { href: '/admin/settings', icon: Settings, label: 'Settings' },
   ];
   ```

3. **Dashboard Page**
   ```tsx
   // frontend/web/src/pages/admin/AdminDashboard.tsx
   export default function AdminDashboard() {
     const { data: stats } = useQuery({
       queryKey: ['admin', 'stats'],
       queryFn: () => adminApi.getStats()
     });

     return (
       <AdminLayout>
         <h1>Admin Dashboard</h1>
         <div className="grid grid-cols-4 gap-4">
           <StatCard title="Total Users" value={stats?.users.total} />
           <StatCard title="Active Users" value={stats?.users.active} />
           <StatCard title="Projects" value={stats?.projects.total} />
           <StatCard title="Gates" value={stats?.gates.total} />
         </div>
         <SystemStatus services={stats?.services} />
       </AdminLayout>
     );
   }
   ```

**Deliverables**:
- [ ] AdminLayout with responsive sidebar
- [ ] AdminDashboard with stats cards
- [ ] StatCard component
- [ ] SystemStatus component
- [ ] Admin routes in router

**Assignee**: Frontend Dev 1
**Estimated**: 2 days

---

### Day 8-9: User Management Pages

**Tasks**:

1. **Users List Page**
   ```tsx
   // frontend/web/src/pages/admin/AdminUsers.tsx
   export default function AdminUsers() {
     const [searchParams, setSearchParams] = useSearchParams();

     const { data: users } = useQuery({
       queryKey: ['admin', 'users', searchParams.toString()],
       queryFn: () => adminApi.listUsers(Object.fromEntries(searchParams))
     });

     return (
       <AdminLayout>
         <h1>User Management</h1>
         <UserFilters />
         <UserTable users={users?.items} />
         <Pagination total={users?.total} />
       </AdminLayout>
     );
   }
   ```

2. **User Table with Actions**
   ```tsx
   // frontend/web/src/components/admin/UserTable.tsx
   function UserActionMenu({ user }: { user: User }) {
     const deactivateMutation = useMutation({
       mutationFn: () => adminApi.updateUser(user.id, { is_active: false }),
       onSuccess: () => queryClient.invalidateQueries(['admin', 'users'])
     });

     return (
       <DropdownMenu>
         <DropdownMenuTrigger>
           <MoreHorizontal />
         </DropdownMenuTrigger>
         <DropdownMenuContent>
           <DropdownMenuItem onClick={() => navigate(`/admin/users/${user.id}`)}>
             View Details
           </DropdownMenuItem>
           <DropdownMenuItem onClick={() => setShowDeactivateDialog(true)}>
             {user.is_active ? 'Deactivate' : 'Activate'}
           </DropdownMenuItem>
           <DropdownMenuItem onClick={() => setShowAdminDialog(true)}>
             {user.is_superuser ? 'Remove Admin' : 'Make Admin'}
           </DropdownMenuItem>
         </DropdownMenuContent>
       </DropdownMenu>
     );
   }
   ```

3. **Confirmation Dialogs**
   ```tsx
   // Deactivate User Dialog
   <AlertDialog>
     <AlertDialogContent>
       <AlertDialogHeader>
         <AlertDialogTitle>Deactivate User</AlertDialogTitle>
         <AlertDialogDescription>
           Are you sure you want to deactivate {user.email}?
           This will log them out immediately.
         </AlertDialogDescription>
       </AlertDialogHeader>
       <AlertDialogFooter>
         <AlertDialogCancel>Cancel</AlertDialogCancel>
         <AlertDialogAction onClick={handleDeactivate}>
           Deactivate
         </AlertDialogAction>
       </AlertDialogFooter>
     </AlertDialogContent>
   </AlertDialog>
   ```

**Deliverables**:
- [ ] AdminUsers page with search/filter
- [ ] UserTable with sorting
- [ ] UserActionMenu with all actions
- [ ] Confirmation dialogs
- [ ] User detail page

**Assignee**: Frontend Dev 2
**Estimated**: 2 days

---

### Day 10: Audit Logs & System Pages

**Tasks**:

1. **Audit Logs Page**
   ```tsx
   // frontend/web/src/pages/admin/AdminAuditLogs.tsx
   export default function AdminAuditLogs() {
     const { data: logs } = useQuery({
       queryKey: ['admin', 'audit-logs', filters],
       queryFn: () => adminApi.getAuditLogs(filters)
     });

     return (
       <AdminLayout>
         <h1>Audit Logs</h1>
         <AuditLogFilters />
         <AuditLogTable logs={logs?.items} onRowClick={openDrawer} />
         <AuditLogDrawer log={selectedLog} />
       </AdminLayout>
     );
   }
   ```

2. **System Health Page**
   ```tsx
   // frontend/web/src/pages/admin/AdminSystem.tsx
   export default function AdminSystem() {
     const { data: health } = useQuery({
       queryKey: ['admin', 'system', 'health'],
       queryFn: () => adminApi.getSystemHealth(),
       refetchInterval: 30000 // 30 seconds
     });

     return (
       <AdminLayout>
         <h1>System Health</h1>
         <ServiceStatusGrid services={health?.services} />
         <SystemMetrics metrics={health?.metrics} />
       </AdminLayout>
     );
   }
   ```

3. **Settings Page**
   ```tsx
   // frontend/web/src/pages/admin/AdminSettings.tsx
   export default function AdminSettings() {
     const { data: settings } = useQuery({
       queryKey: ['admin', 'settings'],
       queryFn: () => adminApi.getSettings()
     });

     const updateMutation = useMutation({
       mutationFn: (updates: SettingsUpdate) => adminApi.updateSettings(updates)
     });

     return (
       <AdminLayout>
         <h1>System Settings</h1>
         <SettingsForm
           settings={settings}
           onSave={(updates) => updateMutation.mutate(updates)}
         />
       </AdminLayout>
     );
   }
   ```

**Deliverables**:
- [ ] AdminAuditLogs with filtering
- [ ] AuditLogDrawer for details
- [ ] AdminSystem with service status
- [ ] AdminSettings with form
- [ ] Export to CSV functionality

**Assignee**: Frontend Dev 1 + Frontend Dev 2
**Estimated**: 1 day

---

## Testing Plan

### Backend Tests

```python
# tests/api/test_admin.py

class TestAdminUsers:
    def test_non_admin_cannot_access(self, client, regular_user_token):
        response = client.get("/api/v1/admin/users", headers=regular_user_token)
        assert response.status_code == 403

    def test_admin_cannot_deactivate_self(self, client, admin_token, admin_user):
        response = client.patch(
            f"/api/v1/admin/users/{admin_user.id}",
            json={"is_active": False},
            headers=admin_token
        )
        assert response.status_code == 400

    def test_cannot_remove_last_superuser(self, client, admin_token, only_superuser):
        response = client.patch(
            f"/api/v1/admin/users/{only_superuser.id}",
            json={"is_superuser": False},
            headers=admin_token
        )
        assert response.status_code == 400

class TestAuditLog:
    def test_action_creates_audit_log(self, client, admin_token, target_user):
        client.patch(
            f"/api/v1/admin/users/{target_user.id}",
            json={"is_active": False},
            headers=admin_token
        )

        logs = client.get("/api/v1/admin/audit-logs", headers=admin_token)
        assert any(l["action"] == "user.deactivated" for l in logs.json()["items"])
```

### Frontend Tests

```tsx
// tests/admin/AdminUsers.test.tsx

describe('AdminUsers', () => {
  it('displays user list', async () => {
    render(<AdminUsers />);
    await waitFor(() => {
      expect(screen.getByText('john@example.com')).toBeInTheDocument();
    });
  });

  it('shows confirmation dialog before deactivation', async () => {
    render(<AdminUsers />);
    await userEvent.click(screen.getByRole('button', { name: /more/i }));
    await userEvent.click(screen.getByText('Deactivate'));
    expect(screen.getByText(/are you sure/i)).toBeInTheDocument();
  });
});
```

---

## Definition of Done

### Code Quality
- [ ] All endpoints have 90%+ test coverage
- [ ] TypeScript strict mode enabled
- [ ] No ESLint errors
- [ ] No security vulnerabilities (npm audit)

### Functionality
- [ ] All 7 user stories implemented
- [ ] All 8 API endpoints working
- [ ] All 6 pages accessible
- [ ] Audit logging verified

### Security
- [ ] Authorization tested (non-admin blocked)
- [ ] Self-action prevention working
- [ ] Rate limiting configured
- [ ] Audit trail complete

### Documentation
- [ ] API docs updated (OpenAPI)
- [ ] User guide written
- [ ] Changelog updated

---

## Risk Register

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Design approval delayed | Medium | High | Parallelize backend DB setup |
| Performance issues with audit logs | Low | Medium | Add indexes, pagination |
| Session invalidation race condition | Low | High | Use Redis pub/sub |

---

## Dependencies

### Blocking
- CTO approval on design documents
- Security Lead approval on security review

### Non-Blocking
- Grafana dashboard for system health links
- Email notification service for alerts

---

## Sprint Ceremonies

| Event | Day | Time |
|-------|-----|------|
| Sprint Planning | Day 1 | 9:00 AM |
| Daily Standup | Daily | 9:30 AM |
| Mid-Sprint Review | Day 5 | 2:00 PM |
| Sprint Demo | Day 10 | 3:00 PM |
| Sprint Retro | Day 10 | 4:00 PM |

---

## Approval

| Role | Name | Date | Signature |
|------|------|------|-----------|
| Backend Lead | | | |
| Frontend Lead | | | |
| QA Lead | | | |
| **CTO** | | | **REQUIRED** |

---

**Document Status**: PENDING - Awaiting CTO Design Approval
