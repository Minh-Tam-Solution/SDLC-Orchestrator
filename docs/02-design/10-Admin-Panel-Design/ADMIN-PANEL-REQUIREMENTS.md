# Admin Panel - Functional Requirements
## SDLC 6.1.0 Complete Lifecycle - Design Phase

**Version**: 2.1.0
**Date**: 2025-12-18
**Status**: DESIGN - Sprint 40 Part 3 (Bulk Delete)
**Author**: Design Lead
**Reviewer**: CTO

**Changelog**:
- v2.1.0 (Dec 18, 2025): Added Bulk Delete Selected Users feature (Sprint 40 Part 3)
- v2.0.0 (Dec 17, 2025): Added Full CRUD, Soft Delete, Toast Notifications (Sprint 40)
- v1.1.0 (Dec 17, 2025): Added E2E Tests (Sprint 38), Toast Notifications (Sprint 39)
- v1.0.0 (Dec 16, 2025): Initial requirements (Sprint 37)

---

## 1. Executive Summary

Admin Panel cung cấp giao diện quản trị cho Platform Admin để quản lý users, system settings, và audit logs trong SDLC Orchestrator platform.

### 1.1 Scope

| In Scope | Out of Scope |
|----------|--------------|
| User Management (Full CRUD) | Billing/Payment |
| - Create User (email/password) | Multi-tenant admin |
| - Read (list, detail, search) | Custom reporting |
| - Update (email, password, role) | Data export tools |
| - Delete (soft delete with audit) | |
| - **Bulk Delete Selected** (NEW) | |
| System Settings (version control) | |
| Audit Logs (SOC 2 compliant) | |
| System Health Dashboard | |
| Toast Notifications (UX feedback) | |

### 1.2 Success Criteria

- [x] Admin có thể quản lý tất cả users (CRUD - Sprint 40)
- [ ] Admin có thể xóa nhiều users cùng lúc (Bulk Delete - Sprint 40 Part 3) **NEW**
- [x] Mọi admin action được audit logged (SOC 2 - Sprint 37)
- [x] System health visible trong dashboard (Sprint 37)
- [x] Response time < 200ms cho tất cả operations (Sprint 37)
- [x] Toast notifications cho user feedback (Sprint 39)
- [x] E2E test coverage 100+ tests (Sprint 38)

---

## 2. User Stories

### Epic: E-ADMIN - Admin Panel Management

---

### US-ADMIN-01: View Admin Dashboard

**Story**: As a Platform Admin, I want to view a dashboard with system metrics so that I can monitor platform health at a glance.

**Priority**: P0

**Acceptance Criteria**:

```gherkin
Feature: Admin Dashboard
  
  Scenario: View dashboard with key metrics
    Given I am logged in as Platform Admin
    When I navigate to /admin
    Then I should see:
      | Metric | Description |
      | Total Users | Count of all registered users |
      | Active Users | Users active in last 7 days |
      | Total Projects | Count of all projects |
      | Total Gates | Count of all gates |
      | System Status | Overall health indicator |
    And all metrics load within 500ms

  Scenario: Non-admin cannot access
    Given I am logged in as regular user
    When I navigate to /admin
    Then I should be redirected to /dashboard
    And I should see "Access Denied" message
```

**Technical Notes**:
- Metrics cached with 5-minute TTL
- Real-time system status from health endpoint

---

### US-ADMIN-02: List All Users

**Story**: As a Platform Admin, I want to list all users with search and filter capabilities so that I can find and manage specific users.

**Priority**: P0

**Acceptance Criteria**:

```gherkin
Feature: User Listing
  
  Scenario: View paginated user list
    Given I am on /admin/users
    Then I should see a table with columns:
      | Column | Sortable |
      | Name | Yes |
      | Email | Yes |
      | Role | Yes |
      | Status | Yes |
      | Created | Yes |
      | Last Login | Yes |
    And pagination shows 20 users per page

  Scenario: Search users by email
    Given I am on /admin/users
    When I enter "john" in search field
    Then I should see only users with "john" in name or email

  Scenario: Filter by status
    Given I am on /admin/users
    When I select "Inactive" from status filter
    Then I should see only inactive users

  Scenario: Filter by role
    Given I am on /admin/users
    When I select "Admin" from role filter
    Then I should see only admin users
```

**Technical Notes**:
- Server-side pagination and filtering
- Search debounced 300ms

---

### US-ADMIN-03: Activate/Deactivate User

**Story**: As a Platform Admin, I want to activate or deactivate user accounts so that I can control platform access.

**Priority**: P0

**Acceptance Criteria**:

```gherkin
Feature: User Activation/Deactivation
  
  Scenario: Deactivate active user
    Given user "john@example.com" is active
    When I click "Deactivate" button for this user
    Then I should see confirmation dialog
    When I confirm deactivation
    Then user status should change to "Inactive"
    And user should be logged out immediately
    And audit log should record this action

  Scenario: Activate inactive user
    Given user "john@example.com" is inactive
    When I click "Activate" button for this user
    Then user status should change to "Active"
    And audit log should record this action

  Scenario: Cannot deactivate self
    Given I am logged in as "admin@sdlc-orchestrator.io"
    When I try to deactivate my own account
    Then I should see error "Cannot deactivate your own account"
```

**Technical Notes**:
- Deactivation is soft-delete (is_active=false)
- Invalidate user's tokens on deactivation

---

### US-ADMIN-03B: Bulk Delete Selected Users (NEW - Sprint 40 Part 3)

**Story**: As a Platform Admin, I want to delete multiple users at once so that I can efficiently manage large numbers of user accounts.

**Priority**: P1

**Acceptance Criteria**:

```gherkin
Feature: Bulk Delete Selected Users

  Scenario: Delete multiple selected users
    Given I am on /admin/users
    And I have selected 3 users via checkboxes
    When I click "Delete Selected" button
    Then I should see confirmation dialog showing:
      | Field | Value |
      | Title | Delete 3 Users |
      | Warning | This action will soft delete the selected users |
      | User List | List of emails to be deleted |
    When I confirm deletion
    Then all 3 users should be soft deleted (deleted_at set)
    And I should see success toast "3 users deleted successfully"
    And audit log should record each deletion
    And users should be removed from the list

  Scenario: Cannot bulk delete if self is selected
    Given I am logged in as "admin@sdlc-orchestrator.io"
    And I have selected my own account and 2 other users
    When I click "Delete Selected" button
    Then I should see error "Cannot delete your own account. Please deselect yourself."
    And deletion should be blocked

  Scenario: Cannot bulk delete last superuser
    Given there is only one superuser in selection
    And no other superusers exist outside selection
    When I click "Delete Selected" button
    Then I should see warning about last superuser
    And last superuser should be automatically deselected
    And remaining users can be deleted

  Scenario: Empty selection
    Given no users are selected
    Then "Delete Selected" button should be disabled
    Or not visible in bulk action bar

  Scenario: Cancel bulk delete
    Given I have selected 2 users
    When I click "Delete Selected" button
    And I click "Cancel" on confirmation dialog
    Then no users should be deleted
    And selection should remain intact

  Scenario: Show loading state during bulk delete
    Given I have selected 5 users
    When I confirm bulk deletion
    Then "Delete Selected" button should show "Deleting..." state
    And be disabled during operation
    And show progress if available
```

**Technical Notes**:
- API: DELETE /api/v1/admin/users/bulk with body: `{ user_ids: string[] }`
- Each deletion creates separate audit log entry
- Self-delete prevention at frontend AND backend
- Last superuser protection with automatic deselection
- Soft delete only (sets deleted_at, deleted_by)
- Toast shows count of successfully deleted users

**CTO Conditions (Dec 18, 2025)**:
1. **Batch Size Limit**: Maximum 50 users per request to prevent DOS
2. **Partial Success Handling**: Return detailed report with success/failed counts
3. **Rate Limiting**: 5 requests/minute per admin to prevent abuse

**UI Components**:
- Bulk Action Bar: Add "Delete Selected" button (red/destructive variant)
- Confirmation Dialog: Show list of users to be deleted (type "DELETE" to confirm)
- Progress indicator for large deletions
- Show partial success report if some deletions fail

---

### US-ADMIN-04: Manage Superuser Status

**Story**: As a Platform Admin, I want to promote/demote superuser status so that I can manage admin access.

**Priority**: P0

**Acceptance Criteria**:

```gherkin
Feature: Superuser Management
  
  Scenario: Promote user to superuser
    Given user "john@example.com" is not superuser
    When I click "Make Admin" button
    Then I should see confirmation dialog with warning
    When I confirm promotion
    Then user should have is_superuser=true
    And audit log should record this action

  Scenario: Demote superuser
    Given user "john@example.com" is superuser
    When I click "Remove Admin" button
    Then I should see confirmation dialog
    When I confirm demotion
    Then user should have is_superuser=false
    And audit log should record this action

  Scenario: Cannot demote self
    Given I am the only superuser
    When I try to remove my own admin status
    Then I should see error "Cannot demote yourself"

  Scenario: Minimum one superuser
    Given there is only one superuser
    When I try to demote that superuser
    Then I should see error "At least one superuser required"
```

**Technical Notes**:
- System must always have at least 1 superuser
- Promotion requires confirmation with warning

---

### US-ADMIN-05: View Audit Logs

**Story**: As a Platform Admin, I want to view audit logs of all admin actions so that I can track changes and ensure accountability.

**Priority**: P0

**Acceptance Criteria**:

```gherkin
Feature: Audit Logs
  
  Scenario: View audit log list
    Given I am on /admin/audit-logs
    Then I should see a table with columns:
      | Column | Description |
      | Timestamp | When action occurred |
      | Actor | Who performed action |
      | Action | What was done |
      | Target | What was affected |
      | Details | Additional info (JSON) |
    And logs are sorted by timestamp descending

  Scenario: Filter by date range
    Given I am on /admin/audit-logs
    When I select date range "Last 7 days"
    Then I should see only logs from last 7 days

  Scenario: Filter by action type
    Given I am on /admin/audit-logs
    When I select action "User Deactivated"
    Then I should see only deactivation logs

  Scenario: Search by actor
    Given I am on /admin/audit-logs
    When I search for "admin@"
    Then I should see only logs by that admin
```

**Technical Notes**:
- Audit logs are immutable (no delete)
- Retention: 90 days minimum
- Export to CSV available

---

### US-ADMIN-06: View System Health

**Story**: As a Platform Admin, I want to view system health status so that I can identify and respond to issues.

**Priority**: P1

**Acceptance Criteria**:

```gherkin
Feature: System Health
  
  Scenario: View service status
    Given I am on /admin/system
    Then I should see status for:
      | Service | Expected Status |
      | PostgreSQL | Healthy |
      | Redis | Healthy |
      | MinIO | Healthy |
      | OPA | Healthy |
      | Backend API | Healthy |
    And each service shows response time

  Scenario: View system metrics
    Given I am on /admin/system
    Then I should see:
      | Metric | Description |
      | CPU Usage | Server CPU % |
      | Memory Usage | Server RAM % |
      | Disk Usage | Storage % |
      | Active Connections | Current DB connections |

  Scenario: Alert on unhealthy service
    Given MinIO service is down
    When I view /admin/system
    Then MinIO should show "Unhealthy" status in red
    And I should see alert banner at top
```

**Technical Notes**:
- Health check every 30 seconds
- Integration with Prometheus/Grafana links

---

### US-ADMIN-07: Manage System Settings

**Story**: As a Platform Admin, I want to manage system settings so that I can configure platform behavior.

**Priority**: P1

**Acceptance Criteria**:

```gherkin
Feature: System Settings
  
  Scenario: View current settings
    Given I am on /admin/settings
    Then I should see settings grouped by category:
      | Category | Settings |
      | Security | Session timeout, Password policy |
      | Notifications | Email enabled, Webhook URL |
      | Limits | Max projects per user, Max file size |

  Scenario: Update setting
    Given I am on /admin/settings
    When I change "Session Timeout" from 30 to 60 minutes
    And I click "Save"
    Then setting should be updated
    And audit log should record this change

  Scenario: Reset to default
    Given I changed "Session Timeout" to 60 minutes
    When I click "Reset to Default"
    Then setting should revert to 30 minutes
```

**Technical Notes**:
- Settings stored in database
- Changes take effect immediately or on next login

---

## 3. Non-Functional Requirements

### 3.1 Performance

| Metric | Target |
|--------|--------|
| Page Load | < 500ms |
| API Response | < 200ms |
| Search | < 300ms |
| Dashboard metrics | < 1s |

### 3.2 Security

- All endpoints require `is_superuser=true`
- HTTPS only
- Rate limiting: 100 requests/minute
- Session timeout: 30 minutes (configurable)

### 3.3 Accessibility

- WCAG 2.1 AA compliant
- Keyboard navigation
- Screen reader support

---

## 4. Dependencies

| Dependency | Type | Status |
|------------|------|--------|
| User model | Backend | ✅ Complete (Sprint 40 - soft delete) |
| Auth middleware | Backend | ✅ Complete |
| Audit log table | Database | ✅ Complete (Sprint 37) |
| Admin routes | Backend | ✅ Complete (11 endpoints) |
| Admin pages | Frontend | ✅ Complete (5 pages) |
| Toast notifications | Frontend | ✅ Complete (Sprint 39) |
| E2E tests | Testing | ✅ Complete (121 tests) |

---

## 5. Sprint Implementation Summary

### Sprint 37: Core Admin Panel
- Backend: 11 API endpoints (~958 lines)
- Frontend: 5 pages (Dashboard, Users, AuditLogs, Settings, Health)
- Database: audit_logs, system_settings migrations

### Sprint 38: E2E Testing
- 109 E2E test cases for Admin Panel
- Access control, user management, audit logs, settings, health tests
- Non-superuser rejection tests added

### Sprint 39: Toast Notifications
- Radix UI Toast component with 6 variants
- Integration with all Admin mutations
- Auto-dismiss after 5 seconds

### Sprint 40 Part 1-2: Full CRUD Operations
- POST /admin/users (create user)
- DELETE /admin/users/{id} (soft delete)
- Extended PATCH for email/password changes
- User model: deleted_at, deleted_by fields
- Soft delete with audit trail
- E2E tests: 41 tests passed (admin-users-crud + admin-users)

### Sprint 40 Part 3: Bulk Delete Selected Users (NEW - DESIGN)
**Status**: 📋 DESIGN PHASE

**Scope**:
- DELETE /api/v1/admin/users/bulk (new endpoint)
- Bulk Delete confirmation dialog (BulkDeleteUsersDialog.tsx)
- "Delete Selected" button in Bulk Action Bar
- Protection: Cannot delete self, last superuser
- Audit log for each deleted user

**API Design** (CTO Approved Dec 18, 2025):
```yaml
DELETE /api/v1/admin/users/bulk
Request Body:
  {
    "user_ids": ["uuid1", "uuid2", "uuid3"]  # max 50 users
  }
Response (200 OK):
  {
    "success_count": 3,
    "failed_count": 0,
    "deleted_users": [
      {"user_id": "uuid1", "email": "user1@example.com"},
      {"user_id": "uuid2", "email": "user2@example.com"},
      {"user_id": "uuid3", "email": "user3@example.com"}
    ],
    "failed_users": []
  }
Response (200 OK - Partial Success):
  {
    "success_count": 2,
    "failed_count": 1,
    "deleted_users": [...],
    "failed_users": [
      {"user_id": "uuid3", "reason": "User is the last superuser"}
    ]
  }
Response (400 Bad Request):
  {"detail": "Cannot delete your own account"}
Response (400 Bad Request):
  {"detail": "Maximum 50 users per request"}
```

**Frontend Components**:
- BulkDeleteUsersDialog.tsx (confirmation with user list)
- Updated UserManagementPage.tsx (add Delete Selected button)
- E2E tests for bulk delete scenarios

**Estimated Effort**: 1 day (backend + frontend + tests)

---

## 6. Approval

| Role | Name | Date | Signature |
|------|------|------|-----------|
| Design Lead | | Dec 16, 2025 | ✅ |
| Backend Lead | | Dec 16, 2025 | ✅ |
| Frontend Lead | | Dec 17, 2025 | ✅ |
| Security Lead | | Dec 17, 2025 | ✅ |
| **CTO** | | Dec 16-17, 2025 | **✅ APPROVED** |

---

**Document Status**: ✅ IMPLEMENTED - Sprint 37-40 Complete
