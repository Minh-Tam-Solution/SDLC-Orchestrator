# Admin Panel - Functional Requirements
## SDLC 5.1.1 Complete Lifecycle - Design Phase

**Version**: 1.0.0
**Date**: 2025-12-16
**Status**: APPROVED - CTO Signed Dec 16, 2025
**Author**: Design Lead
**Reviewer**: CTO

---

## 1. Executive Summary

Admin Panel cung cấp giao diện quản trị cho Platform Admin để quản lý users, system settings, và audit logs trong SDLC Orchestrator platform.

### 1.1 Scope

| In Scope | Out of Scope |
|----------|--------------|
| User Management (CRUD, roles) | Billing/Payment |
| System Settings | Multi-tenant admin |
| Audit Logs | Custom reporting |
| System Health Dashboard | Data export tools |

### 1.2 Success Criteria

- [ ] Admin có thể quản lý tất cả users
- [ ] Mọi admin action được audit logged
- [ ] System health visible trong dashboard
- [ ] Response time < 200ms cho tất cả operations

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
| User model | Backend | ✅ Exists |
| Auth middleware | Backend | ✅ Exists |
| Audit log table | Database | ❌ Need migration |
| Admin routes | Backend | ❌ Need implementation |
| Admin pages | Frontend | ❌ Need implementation |

---

## 5. Approval

| Role | Name | Date | Signature |
|------|------|------|-----------|
| Design Lead | | | |
| Backend Lead | | | |
| Frontend Lead | | | |
| Security Lead | | | |
| **CTO** | | | **REQUIRED** |

---

**Document Status**: DRAFT - Awaiting CTO Approval
