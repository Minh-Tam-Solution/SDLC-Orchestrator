# Admin Panel - UI Specification
## SDLC 6.1.0 Complete Lifecycle - Design Phase

**Version**: 1.3.0
**Date**: 2026-01-25
**Status**: DESIGN - Sprint 105 (Show Deleted Users + Permanent Delete)
**Author**: Frontend Lead
**Reviewer**: CTO

**Changelog**:
- v1.3.0 (Jan 25, 2026): Added Permanent Delete button + confirmation dialog (Sprint 105)
- v1.2.0 (Jan 25, 2026): Added "Show Deleted" toggle + Restore button (Sprint 105)
- v1.1.0 (Dec 18, 2025): Added Bulk Delete Selected Users UI (Sprint 40 Part 3)
- v1.0.0 (Dec 16, 2025): Initial UI specification (Sprint 37)

---

## 1. Overview

### 1.1 Design System
- **Framework**: React + TypeScript
- **UI Library**: Shadcn/ui (existing)
- **Icons**: Lucide React (existing)
- **Charts**: Recharts (existing)

### 1.2 Route Structure
```
/admin                    # Admin Dashboard
/admin/users              # User Management
/admin/users/:id          # User Detail
/admin/audit-logs         # Audit Logs
/admin/system             # System Health
/admin/settings           # System Settings
```

---

## 2. Page Specifications

### 2.1 Admin Dashboard (`/admin`)

#### Layout
```
┌────────────────────────────────────────────────────────────────┐
│ [Logo] SDLC Orchestrator - Admin Panel          [User] [Logout]│
├────────────────────────────────────────────────────────────────┤
│ ┌──────┐                                                       │
│ │ Nav  │  Dashboard                                           │
│ │──────│  ─────────                                           │
│ │📊 Dash│                                                      │
│ │👥 Users│ ┌────────────┐ ┌────────────┐ ┌────────────┐ ┌─────┐│
│ │📋 Logs│ │ Total Users│ │Active Users│ │  Projects  │ │Gates││
│ │🖥️ System│ │    150    │ │    120    │ │     45     │ │ 180 ││
│ │⚙️ Settings│ │ +12 this week│ │ 80% active │ │  40 active │ │66% ✓││
│ │      │ └────────────┘ └────────────┘ └────────────┘ └─────┘│
│ │      │                                                       │
│ │      │ ┌─────────────────────────────────────────────────┐  │
│ │      │ │              System Status                      │  │
│ │      │ │  ✓ PostgreSQL  ✓ Redis  ✓ MinIO  ✓ OPA         │  │
│ │      │ └─────────────────────────────────────────────────┘  │
│ │      │                                                       │
│ │      │ ┌─────────────────────┐ ┌─────────────────────────┐  │
│ │      │ │   Recent Activity   │ │    Quick Actions        │  │
│ │      │ │ • User created...   │ │ [+ Add User]            │  │
│ │      │ │ • Settings changed..│ │ [View Logs]             │  │
│ │      │ │ • User deactivated..│ │ [System Health]         │  │
│ │      │ └─────────────────────┘ └─────────────────────────┘  │
│ └──────┘                                                       │
└────────────────────────────────────────────────────────────────┘
```

#### Components
| Component | Description |
|-----------|-------------|
| StatCard | Displays metric with title, value, trend |
| SystemStatus | Shows service health indicators |
| ActivityFeed | Recent admin actions list |
| QuickActions | Shortcut buttons |

---

### 2.2 User Management (`/admin/users`)

#### Layout
```
┌────────────────────────────────────────────────────────────────┐
│ [Nav]  User Management                                         │
│        ────────────────                                        │
│                                                                │
│  ┌─────────────────────────────────────────────────────────┐  │
│  │ [🔍 Search users...]  [Status ▼] [Role ▼] │ [🔄 Show    │  │
│  │                                           │   Deleted]  │  │
│  │                                     [+ Add User]        │  │
│  └─────────────────────────────────────────────────────────┘  │
│                                                                │
│  ┌─────────────────────────────────────────────────────────┐  │
│  │ ☐ │ Name          │ Email              │Role │Status│Act││
│  │───│───────────────│────────────────────│─────│──────│───││
│  │ ☐ │ John Doe      │ john@example.com   │User │Active│ ⋮ ││
│  │ ☐ │ Jane Smith    │ jane@example.com   │Admin│Active│ ⋮ ││
│  │ ☐ │ Bob Wilson    │ bob@example.com    │User │Inactive│ ⋮││
│  │   │               │                    │     │      │   ││
│  │   │               │                    │     │      │   ││
│  └─────────────────────────────────────────────────────────┘  │
│                                                                │
│  Showing 1-20 of 150 users          [◀] 1 2 3 ... 8 [▶]       │
│                                                                │
└────────────────────────────────────────────────────────────────┘
```

#### Action Menu (⋮) - Active Users
```
┌─────────────────┐
│ 👁️ View Details │
│ ✏️ Edit User    │
│ ─────────────── │
│ 🔑 Make Admin   │  (or "Remove Admin" if admin)
│ ─────────────── │
│ 🔒 Deactivate   │  (or "Activate" if inactive)
│ 🗑️ Delete       │
└─────────────────┘
```

#### Deleted User Row (Sprint 105 - NEW)

When "Show Deleted" toggle is enabled, deleted users appear with:
- **Badge**: Red "Deleted" badge instead of "Active/Inactive"
- **Actions**: "Restore" button (green) + "Permanent Delete" button (red, dangerous)
- **Checkbox**: Disabled (cannot be selected for bulk actions)

```
┌──────────────────────────────────────────────────────────────────────────┐
│ ☐ │ Bob Wilson  │ bob@example.com │User │🔴Deleted│[🔄Restore] [🗑️Permanent]│
│(disabled)                                                                │
└──────────────────────────────────────────────────────────────────────────┘
```

**Button Styles**:
- **Restore**: `variant="outline"` with green text (`text-green-600`)
- **Permanent Delete**: `variant="destructive"` (red background)

#### Restore User Confirmation
```
┌──────────────────────────────────────┐
│ 🔄 Restore User                      │
│                                      │
│ Are you sure you want to restore     │
│ bob@example.com?                     │
│                                      │
│ This will:                           │
│ • Clear soft-delete markers          │
│ • Reactivate the user account        │
│ • Allow the user to log in again     │
│                                      │
│            [Cancel]  [Restore User]  │
└──────────────────────────────────────┘
```

#### Permanent Delete Confirmation (Sprint 105 - NEW)

**CRITICAL**: This dialog requires double confirmation due to irreversible nature.

```
┌──────────────────────────────────────────────────────────────┐
│ 🗑️ Permanently Delete User                                   │
│                                                              │
│ ⚠️ DANGER: This action is IRREVERSIBLE!                     │
│                                                              │
│ You are about to permanently delete:                         │
│ ┌──────────────────────────────────────────────────────────┐│
│ │ bob@example.com                                          ││
│ │ User ID: 550e8400-e29b-41d4-a716-446655440000           ││
│ └──────────────────────────────────────────────────────────┘│
│                                                              │
│ This will permanently remove:                                │
│ • The user account and all personal data                     │
│ • All associated records (projects, teams, evidence, etc.)   │
│ • All audit trail entries will have user_id set to NULL      │
│                                                              │
│ ⚠️ This action CANNOT be undone!                            │
│                                                              │
│ Type "PERMANENTLY DELETE" to confirm:                        │
│ ┌──────────────────────────────────────────────────────────┐│
│ │ ___________________________                              ││
│ └──────────────────────────────────────────────────────────┘│
│                                                              │
│                    [Cancel]  [Permanently Delete]            │
└──────────────────────────────────────────────────────────────┘
```

**UI Notes**:
- Dialog title: Red text with warning icon
- "DANGER" banner: Red background with white text
- Delete button: `variant="destructive"` (red background)
- Delete button disabled until exact phrase typed: "PERMANENTLY DELETE"
- Input validation: Case-insensitive match
- Loading state: "Deleting..." with spinner

**Error States**:

*User not soft-deleted*:
```
┌──────────────────────────────────────────────────────────────┐
│ ❌ Cannot Permanently Delete                                  │
│                                                              │
│ This user is not soft-deleted.                               │
│                                                              │
│ You must soft-delete the user first before permanent         │
│ deletion is allowed.                                         │
│                                                              │
│                                        [OK]                  │
└──────────────────────────────────────────────────────────────┘
```

*Self-delete prevention*:
```
┌──────────────────────────────────────────────────────────────┐
│ ❌ Cannot Delete Own Account                                  │
│                                                              │
│ You cannot permanently delete your own account.              │
│                                                              │
│                                        [OK]                  │
└──────────────────────────────────────────────────────────────┘
```

**Success Toast**:
```
✅ User permanently deleted
   bob@example.com has been permanently removed.
```

#### Show Deleted Toggle (Sprint 105 - NEW)
```
┌───────────────────────────────┐
│ [🔄] Show Deleted             │
│  ◯ OFF (default) - Hide deleted users
│  ◉ ON - Include soft-deleted users
└───────────────────────────────┘
```

**Behavior**:
- Default: OFF (deleted users hidden)
- When ON: All users including soft-deleted shown
- Page resets to 1 when toggled
- Persists during session but resets on page reload

#### Bulk Action Bar (When users selected)
```
┌─────────────────────────────────────────────────────────────────┐
│  ☑ 3 user(s) selected                                          │
│                                                                 │
│  [Activate Selected] [Deactivate Selected] [🗑️ Delete Selected]│
│                                                                 │
│  [Clear Selection]                                              │
└─────────────────────────────────────────────────────────────────┘
```

**Notes**:
- "Delete Selected" button uses destructive variant (red)
- Button is disabled if current user (self) is in selection
- Tooltip explains why button is disabled

---

#### Dialogs

**Deactivate User Dialog**:
```
┌──────────────────────────────────────┐
│ ⚠️ Deactivate User                   │
│                                      │
│ Are you sure you want to deactivate  │
│ john@example.com?                    │
│                                      │
│ This will:                           │
│ • Log out the user immediately       │
│ • Prevent future logins              │
│ • Keep all their data intact         │
│                                      │
│            [Cancel] [Deactivate]     │
└──────────────────────────────────────┘
```

**Make Admin Dialog**:
```
┌──────────────────────────────────────┐
│ 🔑 Grant Admin Access                │
│                                      │
│ Are you sure you want to make        │
│ john@example.com an administrator?   │
│                                      │
│ ⚠️ Warning: Admins can:              │
│ • Manage all users                   │
│ • Change system settings             │
│ • View all audit logs                │
│                                      │
│            [Cancel] [Make Admin]     │
└──────────────────────────────────────┘
```

**Bulk Delete Users Dialog** (NEW - Sprint 40 Part 3):
```
┌──────────────────────────────────────────────────┐
│ 🗑️ Delete 3 Users                                │
│                                                  │
│ ⚠️ Warning: This action will permanently        │
│ deactivate the following user accounts:          │
│                                                  │
│ ┌──────────────────────────────────────────────┐│
│ │ • john@example.com                           ││
│ │ • jane@example.com                           ││
│ │ • bob@example.com                            ││
│ └──────────────────────────────────────────────┘│
│                                                  │
│ This will:                                       │
│ • Soft delete all selected accounts              │
│ • Prevent future logins for these users          │
│ • Keep all their data for audit purposes         │
│                                                  │
│ Type "DELETE" to confirm:                        │
│ ┌──────────────────────────────────────────────┐│
│ │ ________________                             ││
│ └──────────────────────────────────────────────┘│
│                                                  │
│              [Cancel] [Delete 3 Users]           │
└──────────────────────────────────────────────────┘
```

**Notes for Bulk Delete Dialog**:
- Requires typing "DELETE" for confirmation (safety measure)
- Delete button disabled until "DELETE" is typed
- Shows scrollable list if more than 5 users selected
- Delete button uses destructive variant (red)
- Loading state shows "Deleting..." with spinner

**Bulk Delete Error States**:

*Self-delete prevention*:
```
┌──────────────────────────────────────────────────┐
│ ❌ Cannot Delete Selected Users                  │
│                                                  │
│ Your account is included in the selection.       │
│ You cannot delete your own account.              │
│                                                  │
│ Please deselect yourself and try again.          │
│                                                  │
│                              [OK]                │
└──────────────────────────────────────────────────┘
```

*Last superuser protection*:
```
┌──────────────────────────────────────────────────┐
│ ⚠️ Last Administrator Warning                    │
│                                                  │
│ admin@sdlc-orchestrator.io is the last           │
│ administrator and cannot be deleted.             │
│                                                  │
│ This user has been removed from selection.       │
│ You can proceed with deleting the remaining      │
│ 2 users.                                         │
│                                                  │
│              [Cancel] [Continue]                 │
└──────────────────────────────────────────────────┘
```

---

### 2.3 Audit Logs (`/admin/audit-logs`)

#### Layout
```
┌────────────────────────────────────────────────────────────────┐
│ [Nav]  Audit Logs                                              │
│        ──────────                                              │
│                                                                │
│  ┌─────────────────────────────────────────────────────────┐  │
│  │ [🔍 Search...]  [Action ▼] [Date Range 📅] [Export CSV] │  │
│  └─────────────────────────────────────────────────────────┘  │
│                                                                │
│  ┌─────────────────────────────────────────────────────────┐  │
│  │ Timestamp        │ Action          │ Actor    │ Target  │  │
│  │──────────────────│─────────────────│──────────│─────────│  │
│  │ Dec 16, 10:30 AM │ user.deactivated│ admin@...│ john@...│  │
│  │ Dec 16, 10:15 AM │ user.created    │ admin@...│ new@... │  │
│  │ Dec 16, 09:45 AM │ setting.changed │ admin@...│ session │  │
│  │ Dec 15, 04:30 PM │ user.promoted   │ admin@...│ jane@...│  │
│  │                  │                 │          │         │  │
│  └─────────────────────────────────────────────────────────┘  │
│                                                                │
│  Showing 1-50 of 1,250 logs         [◀] 1 2 3 ... 25 [▶]      │
│                                                                │
└────────────────────────────────────────────────────────────────┘
```

#### Log Detail Drawer
```
┌──────────────────────────────────────┐
│ Audit Log Details                  ✕ │
│                                      │
│ Action: user.deactivated             │
│ Timestamp: Dec 16, 2025 10:30:15 AM  │
│                                      │
│ Actor                                │
│ ┌──────────────────────────────────┐ │
│ │ Platform Admin                   │ │
│ │ admin@sdlc-orchestrator.io       │ │
│ └──────────────────────────────────┘ │
│                                      │
│ Target                               │
│ ┌──────────────────────────────────┐ │
│ │ User: john@example.com           │ │
│ │ ID: 550e8400-...                 │ │
│ └──────────────────────────────────┘ │
│                                      │
│ Details                              │
│ ┌──────────────────────────────────┐ │
│ │ {                                │ │
│ │   "previous_status": "active",   │ │
│ │   "new_status": "inactive",      │ │
│ │   "reason": "Policy violation"   │ │
│ │ }                                │ │
│ └──────────────────────────────────┘ │
│                                      │
│ Metadata                             │
│ IP: 192.168.1.100                    │
│ User Agent: Chrome 120...            │
│                                      │
└──────────────────────────────────────┘
```

---

### 2.4 System Health (`/admin/system`)

#### Layout
```
┌────────────────────────────────────────────────────────────────┐
│ [Nav]  System Health                                           │
│        ─────────────                                           │
│                                                                │
│  Overall Status: ✅ Healthy                   Last check: 30s  │
│                                                                │
│  ┌───────────────────────────────────────────────────────────┐│
│  │ Services                                                  ││
│  │ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌───────┐││
│  │ │ PostgreSQL  │ │   Redis     │ │   MinIO     │ │  OPA  │││
│  │ │   ✅ 5ms    │ │   ✅ 2ms    │ │  ✅ 15ms    │ │ ✅ 8ms│││
│  │ │ v15.4       │ │ v7.2        │ │ 25GB used   │ │45 pol │││
│  │ └─────────────┘ └─────────────┘ └─────────────┘ └───────┘││
│  └───────────────────────────────────────────────────────────┘│
│                                                                │
│  ┌───────────────────────────────────────────────────────────┐│
│  │ System Metrics                                            ││
│  │                                                           ││
│  │ CPU Usage        Memory Usage      Disk Usage            ││
│  │ ████████░░ 35%   ██████░░░░ 60%    ████░░░░░░ 45%        ││
│  │                                                           ││
│  │ Uptime: 30 days, 5 hours                                  ││
│  │ Last Backup: Dec 15, 2025 00:00 UTC                       ││
│  └───────────────────────────────────────────────────────────┘│
│                                                                │
│  [🔗 Open Grafana] [🔗 Open Prometheus]                        │
│                                                                │
└────────────────────────────────────────────────────────────────┘
```

---

### 2.5 System Settings (`/admin/settings`)

#### Layout
```
┌────────────────────────────────────────────────────────────────┐
│ [Nav]  System Settings                                         │
│        ───────────────                                         │
│                                                                │
│  ┌───────────────────────────────────────────────────────────┐│
│  │ 🔒 Security                                               ││
│  │ ─────────                                                 ││
│  │                                                           ││
│  │ Session Timeout                                           ││
│  │ [   30   ] minutes          (default: 30, range: 5-480)   ││
│  │                                                           ││
│  │ Max Login Attempts                                        ││
│  │ [   5    ]                  (default: 5, range: 3-10)     ││
│  └───────────────────────────────────────────────────────────┘│
│                                                                │
│  ┌───────────────────────────────────────────────────────────┐│
│  │ 📊 Limits                                                 ││
│  │ ──────                                                    ││
│  │                                                           ││
│  │ Max Projects per User                                     ││
│  │ [   50   ]                  (default: 50, range: 1-500)   ││
│  │                                                           ││
│  │ Max File Size (MB)                                        ││
│  │ [  100   ]                  (default: 100, range: 1-500)  ││
│  └───────────────────────────────────────────────────────────┘│
│                                                                │
│  ┌───────────────────────────────────────────────────────────┐│
│  │ 🔔 Notifications                                          ││
│  │ ─────────────                                             ││
│  │                                                           ││
│  │ Email Notifications        [✓] Enabled                    ││
│  │                                                           ││
│  │ Webhook URL                                               ││
│  │ [https://...]                                             ││
│  └───────────────────────────────────────────────────────────┘│
│                                                                │
│  [Reset to Defaults]                        [Save Changes]     │
│                                                                │
└────────────────────────────────────────────────────────────────┘
```

---

## 3. Components

### 3.1 New Components Required

| Component | Location | Description |
|-----------|----------|-------------|
| AdminLayout | `components/admin/AdminLayout.tsx` | Admin-specific layout with sidebar |
| AdminSidebar | `components/admin/AdminSidebar.tsx` | Navigation sidebar |
| StatCard | `components/admin/StatCard.tsx` | Dashboard metric card |
| ServiceStatus | `components/admin/ServiceStatus.tsx` | Service health indicator |
| UserTable | `components/admin/UserTable.tsx` | User list with actions |
| AuditLogTable | `components/admin/AuditLogTable.tsx` | Audit log list |
| AuditLogDrawer | `components/admin/AuditLogDrawer.tsx` | Log detail drawer |
| SettingsForm | `components/admin/SettingsForm.tsx` | Settings editor |
| **BulkDeleteUsersDialog** | `components/admin/BulkDeleteUsersDialog.tsx` | **NEW** - Bulk delete confirmation |
| ConfirmDialog | `components/ui/confirm-dialog.tsx` | ✅ EXISTS |
| DataTable | `components/ui/table.tsx` | ✅ EXISTS |

### 3.2 File Structure

```
frontend/web/src/
├── pages/
│   └── admin/
│       ├── AdminDashboard.tsx
│       ├── AdminUsers.tsx
│       ├── AdminUserDetail.tsx
│       ├── AdminAuditLogs.tsx
│       ├── AdminSystem.tsx
│       └── AdminSettings.tsx
├── components/
│   └── admin/
│       ├── AdminLayout.tsx
│       ├── AdminSidebar.tsx
│       ├── StatCard.tsx
│       ├── ServiceStatus.tsx
│       ├── UserTable.tsx
│       ├── UserActionMenu.tsx
│       ├── CreateUserDialog.tsx
│       ├── EditUserDialog.tsx
│       ├── DeleteUserDialog.tsx
│       ├── BulkDeleteUsersDialog.tsx    # NEW - Sprint 40 Part 3
│       ├── AuditLogTable.tsx
│       ├── AuditLogDrawer.tsx
│       ├── SystemMetrics.tsx
│       └── SettingsForm.tsx
└── api/
    └── admin.ts                  # Admin API client (add bulkDeleteUsers)
```

---

## 4. Responsive Design

### Breakpoints
| Screen | Width | Layout |
|--------|-------|--------|
| Mobile | < 768px | Collapsed sidebar, stacked cards |
| Tablet | 768-1024px | Mini sidebar, 2-column grid |
| Desktop | > 1024px | Full sidebar, 4-column grid |

### Mobile Considerations
- Sidebar collapses to hamburger menu
- Tables become card lists on mobile
- Action menus use bottom sheet on mobile

---

## 5. Accessibility

### Requirements
- All interactive elements keyboard accessible
- ARIA labels on icons and buttons
- Color not sole indicator (use icons + text)
- Focus visible states
- Screen reader announcements for actions

### Color Contrast
- Text: 4.5:1 minimum
- Large text: 3:1 minimum
- UI components: 3:1 minimum

---

## 6. States

### Loading States
```tsx
// Skeleton for dashboard
<div className="grid grid-cols-4 gap-4">
  {[1,2,3,4].map(i => (
    <Skeleton key={i} className="h-24" />
  ))}
</div>

// Skeleton for table
<Table>
  <TableBody>
    {[1,2,3,4,5].map(i => (
      <TableRow key={i}>
        <TableCell><Skeleton className="h-4 w-full" /></TableCell>
      </TableRow>
    ))}
  </TableBody>
</Table>
```

### Empty States
```tsx
// No users found
<div className="text-center py-12">
  <UsersIcon className="h-12 w-12 text-muted-foreground mx-auto" />
  <h3>No users found</h3>
  <p>Try adjusting your search or filters</p>
</div>
```

### Error States
```tsx
// API error
<Alert variant="destructive">
  <AlertCircle className="h-4 w-4" />
  <AlertTitle>Error</AlertTitle>
  <AlertDescription>
    Failed to load users. Please try again.
  </AlertDescription>
</Alert>
```

---

## 7. Approval

| Role | Name | Date | Signature |
|------|------|------|-----------|
| Frontend Lead | | | |
| UX Designer | | | |
| **CTO** | | | **REQUIRED** |

---

**Document Status**: DRAFT - Awaiting CTO Approval
