# GitHub Integration Design Clarification

**Version**: 1.0.0
**Date**: November 29, 2025
**Status**: ACTIVE - CLARIFICATION DOCUMENT
**Authority**: CPO + CTO Approved
**Framework**: SDLC 5.1.3 Complete Lifecycle
**Related**: User-Onboarding-Flow-Architecture.md, ADR-002-Authentication-Model.md

---

## 1. Problem Statement

Hiện tại tài liệu thiết kế chưa phân biệt rõ ràng giữa:
- **GitHub OAuth Login** (đăng nhập bằng GitHub)
- **GitHub Repository Integration** (kết nối repository để sync)

Điều này gây nhầm lẫn trong UX và implementation.

---

## 2. Two Distinct Features

### 2.1 Feature 1: GitHub OAuth Login (Authentication)

**Purpose**: Cho phép user đăng nhập vào SDLC Orchestrator bằng GitHub account thay vì email/password.

```yaml
Use Case: Authentication (WHO is the user?)
Entry Point: Login page → "Continue with GitHub" button
Result: User is authenticated, receives JWT tokens
GitHub Token: Stored in OAuthAccount table, used for future API calls

Flow:
  1. User clicks "Continue with GitHub" on login page
  2. Redirect to GitHub OAuth authorize
  3. User approves "SDLC Orchestrator" app
  4. GitHub redirects back with authorization code
  5. Backend exchanges code for GitHub access token
  6. Backend creates/updates User + OAuthAccount
  7. Backend issues JWT tokens (access + refresh)
  8. User is logged in and redirected to Dashboard

Scopes Required:
  - read:user (get user profile)
  - user:email (get user email)
  - repo (access repositories - for future sync)
```

**Key Point**: Khi user login bằng GitHub, họ **đã có** GitHub OAuth token được lưu trong database. Không cần kết nối lại!

### 2.2 Feature 2: GitHub Repository Integration (Data Sync)

**Purpose**: Cho phép user đã đăng nhập (bằng bất kỳ phương thức nào) kết nối GitHub repo để sync data.

```yaml
Use Case: Data Integration (WHAT repositories to sync?)
Entry Point: Settings page → "Connect GitHub" hoặc Onboarding wizard
Result: OAuthAccount created/updated, repos available for sync
GitHub Token: Stored in OAuthAccount table

Scenarios:
  A. User logged in via GitHub OAuth:
     - Already has OAuthAccount with GitHub token
     - NO need to "Connect GitHub" again
     - Can immediately list and sync repositories
     - Settings page shows "Connected" status

  B. User logged in via Email/Password or Google/Microsoft:
     - Does NOT have GitHub OAuthAccount
     - Must "Connect GitHub" to enable repository features
     - Click button → OAuth flow → Save token
     - Now can list and sync repositories
```

---

## 3. UX Requirements Update

### 3.1 Settings Page Logic

```typescript
// SettingsPage.tsx - Updated Logic

// Check if user has GitHub OAuth account
const { data: githubStatus } = useQuery({
  queryKey: ['github-status'],
  queryFn: () => apiClient.get('/github/status')
})

// Render different UI based on connection status
if (githubStatus?.connected) {
  // Show connected state with GitHub username
  // User can: Disconnect, View rate limits
  // User can: Navigate to repo selection
  return <GitHubConnectedCard github={githubStatus} />
} else {
  // Show "Connect GitHub" button
  // This only needed for users who:
  //   - Logged in via email/password
  //   - Logged in via Google/Microsoft
  return <GitHubConnectCard onConnect={handleConnect} />
}
```

### 3.2 Profile Section Enhancement

```yaml
Profile Section - Show GitHub Account Info:
  If user logged in via GitHub:
    - Show GitHub username (@username)
    - Show GitHub avatar (if available)
    - Show "Logged in with GitHub" badge
    - GitHub Integration section shows "Connected" (no button needed)

  If user logged in via Email/Password:
    - Show email and name
    - GitHub Integration section shows "Connect GitHub" button
    - After connecting, show GitHub username in profile
```

### 3.3 API Response Update

**GET /api/v1/auth/me** - Should include GitHub info if connected:

```json
{
  "id": "uuid",
  "email": "user@example.com",
  "name": "User Name",
  "avatar_url": "https://...",
  "is_active": true,
  "roles": ["dev"],
  "last_login_at": "2025-11-29T10:00:00Z",

  "auth_provider": "github",  // NEW: How user logged in
  "github_connected": true,   // NEW: Has GitHub OAuth token
  "github_username": "octocat", // NEW: GitHub username if connected
  "github_avatar": "https://..." // NEW: GitHub avatar if connected
}
```

---

## 4. Database Schema Clarification

### 4.1 OAuthAccount Table

```sql
CREATE TABLE oauth_accounts (
    id UUID PRIMARY KEY,
    user_id UUID REFERENCES users(id),
    provider VARCHAR(50) NOT NULL,  -- 'github', 'google', 'microsoft'
    provider_account_id VARCHAR(255) NOT NULL,  -- GitHub user ID
    access_token TEXT,  -- GitHub access token (encrypted)
    refresh_token TEXT,  -- Not used for GitHub
    expires_at TIMESTAMP,  -- Token expiry (null for GitHub - never expires)
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),

    UNIQUE(user_id, provider)  -- One connection per provider per user
);
```

### 4.2 User Table Update (Optional)

```sql
-- Add convenience fields for quick access
ALTER TABLE users ADD COLUMN auth_provider VARCHAR(50);  -- 'email', 'github', 'google', 'microsoft'
ALTER TABLE users ADD COLUMN github_username VARCHAR(255);  -- Cached from OAuthAccount
```

---

## 5. Implementation Checklist

### 5.1 Backend Changes

```yaml
Priority 1 - API Updates:
  [ ] GET /auth/me - Include github_connected, github_username, auth_provider
  [ ] GET /github/status - Return connected=true if OAuthAccount exists
  [ ] Handle case: User logs in via GitHub → auto-connected to repos

Priority 2 - Logic Updates:
  [ ] OAuth callback - Store auth_provider on user creation
  [ ] GitHub callback - Set github_connected=true in user context
```

### 5.2 Frontend Changes

```yaml
Priority 1 - Settings Page:
  [ ] Check github_connected from /auth/me response
  [ ] If connected: Show "Connected as @username" instead of "Connect" button
  [ ] If connected: Still allow "Disconnect" option

Priority 2 - Profile Section:
  [ ] Show auth_provider badge (Logged in with GitHub/Google/Email)
  [ ] Show GitHub avatar if available
  [ ] Show GitHub username if connected
```

---

## 6. User Scenarios

### Scenario A: Developer logs in with GitHub

```
1. Developer clicks "Continue with GitHub" on login page
2. Authorizes SDLC Orchestrator app
3. Lands on Dashboard - already authenticated
4. Goes to Settings → GitHub section shows "Connected as @developer"
5. Goes to Projects → Can immediately select GitHub repos to sync
6. NO additional "Connect GitHub" step needed
```

### Scenario B: PM logs in with Email/Password

```
1. PM enters email + password on login page
2. Lands on Dashboard - authenticated with email
3. Goes to Settings → GitHub section shows "Not Connected"
4. Clicks "Connect GitHub" → OAuth flow
5. Returns → GitHub section shows "Connected as @pm-github"
6. Goes to Projects → Can now select GitHub repos to sync
```

### Scenario C: Enterprise user logs in with Microsoft SSO

```
1. User clicks "Continue with Microsoft" on login page
2. Authenticates via Azure AD
3. Lands on Dashboard - authenticated with Microsoft
4. Goes to Settings → GitHub section shows "Not Connected"
5. Clicks "Connect GitHub" → OAuth flow
6. Returns → GitHub section shows "Connected as @user-github"
7. Now has both: Microsoft login + GitHub repo access
```

---

## 7. Summary

| Aspect | GitHub OAuth Login | GitHub Integration |
|--------|-------------------|-------------------|
| **Purpose** | Authenticate user | Sync repositories |
| **Entry Point** | Login page | Settings page |
| **Result** | JWT tokens | OAuthAccount created |
| **When Needed** | Always (alternative to email) | Only if not logged in via GitHub |
| **Scopes** | read:user, user:email, repo | Same scopes |
| **Token Storage** | OAuthAccount table | OAuthAccount table |

**Key Insight**: If user logs in via GitHub, they automatically have GitHub Integration enabled. No duplicate "Connect GitHub" step needed!

---

## 8. Project Ownership Model (GitHub-Style)

### 8.1 Overview

Áp dụng mô hình quyền tương tự GitHub:
- **Owner** của project có toàn quyền quản trị
- Owner có thể phân quyền (assign roles) cho các members
- Members chỉ có quyền theo role được assign

### 8.2 Project Roles (Per-Project Basis)

```yaml
Project Roles (GitHub-inspired):
  Owner:
    - Toàn quyền quản trị project
    - Assign/remove members
    - Assign roles cho members
    - Delete project
    - Configure project settings
    - Approve all gates
    - Transfer ownership

  Admin:
    - Manage project settings
    - Assign/remove members (except Owner)
    - Create/manage gates
    - Upload/manage evidence
    - Cannot delete project
    - Cannot transfer ownership

  Maintainer:
    - Create gates
    - Upload evidence
    - Approve specific gates (based on config)
    - Cannot manage members
    - Cannot delete project

  Developer:
    - View project
    - Upload evidence
    - Request gate approval
    - Cannot create gates
    - Cannot approve gates

  Viewer:
    - View project (read-only)
    - View gates and evidence
    - Cannot modify anything
```

### 8.3 Database Schema for Project Membership

```sql
-- Project Members table (similar to GitHub collaborators)
CREATE TABLE project_members (
    id UUID PRIMARY KEY,
    project_id UUID REFERENCES projects(id) ON DELETE CASCADE,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    role VARCHAR(50) NOT NULL DEFAULT 'viewer',  -- 'owner', 'admin', 'maintainer', 'developer', 'viewer'
    invited_by UUID REFERENCES users(id),
    invited_at TIMESTAMP DEFAULT NOW(),
    accepted_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),

    CONSTRAINT valid_project_role CHECK (role IN ('owner', 'admin', 'maintainer', 'developer', 'viewer')),
    UNIQUE(project_id, user_id)  -- One membership per user per project
);

-- Index for fast lookup
CREATE INDEX idx_project_members_project ON project_members(project_id);
CREATE INDEX idx_project_members_user ON project_members(user_id);
```

### 8.4 Permission Matrix (Project-Level)

| Action | Owner | Admin | Maintainer | Developer | Viewer |
|--------|-------|-------|------------|-----------|--------|
| View project | ✅ | ✅ | ✅ | ✅ | ✅ |
| Create gate | ✅ | ✅ | ✅ | ❌ | ❌ |
| Upload evidence | ✅ | ✅ | ✅ | ✅ | ❌ |
| Approve gate | ✅ | ✅ | Config-based | ❌ | ❌ |
| Invite members | ✅ | ✅ | ❌ | ❌ | ❌ |
| Remove members | ✅ | ✅* | ❌ | ❌ | ❌ |
| Change member role | ✅ | ✅* | ❌ | ❌ | ❌ |
| Project settings | ✅ | ✅ | ❌ | ❌ | ❌ |
| Delete project | ✅ | ❌ | ❌ | ❌ | ❌ |
| Transfer ownership | ✅ | ❌ | ❌ | ❌ | ❌ |

*Admin không thể remove/change role của Owner

### 8.5 API Endpoints for Project Membership

```yaml
Project Member Management:
  GET /api/v1/projects/{id}/members:
    Description: List all project members
    Response: Array of members with roles
    Required Role: Any member

  POST /api/v1/projects/{id}/members:
    Description: Invite new member
    Body: { user_id: UUID, role: string }
    Required Role: Owner, Admin

  PATCH /api/v1/projects/{id}/members/{user_id}:
    Description: Update member role
    Body: { role: string }
    Required Role: Owner, Admin (with restrictions)

  DELETE /api/v1/projects/{id}/members/{user_id}:
    Description: Remove member
    Required Role: Owner, Admin (cannot remove Owner)

  POST /api/v1/projects/{id}/transfer-ownership:
    Description: Transfer ownership to another member
    Body: { new_owner_id: UUID }
    Required Role: Owner only
```

### 8.6 UX Flow: Invite Member

```
1. Owner clicks "Invite Member" button
2. Search user by email or GitHub username
3. Select role (Admin, Maintainer, Developer, Viewer)
4. Send invitation
5. User receives notification
6. User accepts → Added to project with role
7. User declines → Invitation removed
```

### 8.7 UX Flow: Manage Members

```
Project Settings → Members Tab:
┌─────────────────────────────────────────────────────┐
│ Members (5)                     [+ Invite Member]  │
├─────────────────────────────────────────────────────┤
│ 👤 Tai Dang (you)         Owner        —           │
│ 👤 John Developer         Developer   [Change ▾]   │
│ 👤 Jane Admin             Admin       [Change ▾]   │
│ 👤 Bob Maintainer         Maintainer  [Change ▾]   │
│ 👤 Alice Viewer           Viewer      [Change ▾]   │
└─────────────────────────────────────────────────────┘

[Change ▾] Dropdown:
  - Admin
  - Maintainer
  - Developer
  - Viewer
  - Remove from project
```

### 8.8 Project Creation Flow

```yaml
When user creates new project:
  1. User becomes Owner automatically
  2. Owner has all permissions by default
  3. Owner can invite team members
  4. Each member gets assigned role

Example:
  User "Tai" creates "SDLC Orchestrator" project
    → Tai = Owner
    → Tai invites "John" as Developer
    → Tai invites "Jane" as Admin
    → John can: View, upload evidence, request approval
    → Jane can: View, create gates, manage members
```

### 8.9 SDLC 5.1.3.1 Workflow Integration

SDLC Orchestrator enforces **SDLC 5.1.3.1 Complete Lifecycle** - workflow này dẫn dắt và force các members phối hợp từ đầu đến cuối dự án.

#### 8.9.1 SDLC 5.1.3.1 10-Stage Lifecycle

```yaml
┌─────────────────────────────────────────────────────────────────┐
│ Stage → Gate → Role Authority → Documentation                   │
├─────────────────────────────────────────────────────────────────┤
│ 00 WHY?      → G0.1/G0.2 → Owner/CPO        → 00-Foundation/    │
│ 01 WHAT?     → G1        → Owner/CPO/PM     → 01-Planning/      │
│ 02 HOW?      → G2        → Owner/CTO        → 02-Design/        │
│ 03 BUILD     → G3        → CTO/Dev Lead     → 03-Development/   │
│ 04 TEST      → G4        → QA Lead          → 04-Quality/       │
│ 05 DEPLOY    → G5        → DevOps Lead      → 05-Deployment/    │
│ 06 OPERATE   → G6        → DevOps Lead      → 06-Operations/    │
│ 07 INTEGRATE → G7        → CTO/Data Lead    → 07-Integration/   │
│ 08 COLLABORATE→ G8       → CPO/PM           → 08-Team-Mgmt/     │
│ 09 GOVERN    → G9        → Owner/CEO        → 09-Executive/     │
└─────────────────────────────────────────────────────────────────┘
```

#### 8.9.2 Gate Approval Authority by Project Role

```yaml
Gate Approvals (SDLC 5.1.3.1 Enforced):

  G0.1 (Problem Definition):
    Required: Owner OR CPO
    Evidence: Problem Statement, Stakeholder Analysis

  G0.2 (Solution Diversity):
    Required: Owner OR CPO
    Evidence: Solution Options, Comparison Matrix

  G1 (Planning Complete):
    Required: Owner OR CPO OR PM
    Evidence: FRD, User Stories, Sprint Plan

  G2 (Design Ready):
    Required: Owner OR CTO
    Evidence: Architecture Doc, API Spec, Security Review

  G3 (Build Complete):
    Required: CTO OR Dev Lead
    Evidence: Code Review, Unit Tests, CI/CD Pass

  G4 (Test Passed):
    Required: QA Lead
    Evidence: Test Report, Bug Report, Coverage Report

  G5 (Deploy Ready):
    Required: DevOps Lead
    Evidence: Deployment Plan, Rollback Plan, Checklist

  G6 (Operate Ready):
    Required: DevOps Lead
    Evidence: Runbook, Monitoring Setup, On-call Schedule

  G7 (Integration Complete):
    Required: CTO OR Data Lead
    Evidence: Integration Tests, API Contracts, Data Schema

  G8 (Collaboration Complete):
    Required: CPO OR PM
    Evidence: Team Review, Knowledge Transfer, Documentation

  G9 (Governance Approved):
    Required: Owner OR CEO
    Evidence: Executive Summary, Compliance Report, Final Sign-off
```

#### 8.9.3 Project Role Mapping to SDLC 5.1.3.1 Roles

```yaml
Project Role → SDLC 5.1.3.1 Role Authority:

  Owner:
    - Acts as: CEO/CPO (can delegate)
    - Can approve: ALL gates (G0-G9)
    - Responsibility: Project success, final decisions

  Admin:
    - Acts as: CTO/EM (can delegate)
    - Can approve: G2, G3, G5, G6, G7
    - Responsibility: Technical decisions, team management

  Maintainer:
    - Acts as: Dev Lead/QA Lead/DevOps Lead
    - Can approve: G3, G4, G5, G6 (based on specialization)
    - Responsibility: Quality, delivery

  Developer:
    - Acts as: Developer
    - Can approve: None (request only)
    - Responsibility: Build, evidence submission

  Viewer:
    - Acts as: Stakeholder
    - Can approve: None
    - Responsibility: Review, feedback
```

#### 8.9.4 Workflow Enforcement

```yaml
SDLC Orchestrator Enforces:

  1. Sequential Gate Progression:
     - Cannot skip stages (00 → 01 → 02 → ... → 09)
     - Each gate must pass before next stage starts
     - Evidence required for each gate

  2. Role-Based Approvals:
     - Only authorized roles can approve gates
     - System validates role before accepting approval
     - Audit log tracks who approved what

  3. Evidence Requirements:
     - Each gate has required evidence types
     - System validates evidence completeness
     - Evidence linked to gates (immutable)

  4. Collaboration Enforcement:
     - Multiple roles required across stages
     - No single person can complete all gates
     - Forces team collaboration

Example Flow (NQH-Bot Platform):
  Stage 00 (WHY): CEO defines problem → CPO approves G0.1
  Stage 01 (WHAT): PM writes FRD → CPO approves G1
  Stage 02 (HOW): CTO designs architecture → CTO approves G2
  Stage 04 (BUILD): Dev team builds → Dev Lead approves G3
  Stage 05 (TEST): QA team tests → QA Lead approves G4
  Stage 06 (DEPLOY): DevOps deploys → DevOps Lead approves G5
  Stage 07 (OPERATE): Team operates → DevOps Lead approves G6
  ...
  Stage 09 (GOVERN): CEO reviews → CEO approves G9
```

---

## 9. User Roles & Permissions (SDLC 5.1.3 Framework)

### 9.1 Role Definitions (from API-Authentication.md)

Theo tài liệu API-Authentication.md, hệ thống SDLC Orchestrator có **13 vai trò (roles)**:

```yaml
Executive Leadership (C-Suite):
  - CEO (Chief Executive Officer): View all, override all, approve all
  - CTO (Chief Technology Officer): View all, override gates, approve G2/G3/G5/G7
  - CPO (Chief Product Officer): View all, approve G0.1/G0.2/G1/G4/G8
  - CIO (Chief Information Officer): View all, approve G5/G6, manage integrations
  - CFO (Chief Financial Officer): View all budgets, approve G9

Engineering Team:
  - EM (Engineering Manager): View own projects, create projects, request approvals
  - PM (Product Manager): View assigned projects, manage requirements
  - Dev Lead (Tech Lead): View assigned projects, approve G3, code review
  - QA Lead: View assigned projects, approve G4, manage test plans
  - Security Lead: View all projects, approve G2, security audits
  - DevOps Lead: View all projects, approve G5/G6, manage deployments
  - Data Lead: View all projects, approve G7, data governance

System Admin:
  - Admin: ALL (system configuration, user management, policy management)
```

### 9.2 GitHub Integration Permissions by Role

```yaml
GitHub Repository Access:
  CEO/CTO/CPO:
    - Can connect GitHub account
    - Can view all team repositories
    - Can sync any repository to project
    - Can configure webhooks (CIO also)

  EM (Engineering Manager):
    - Can connect GitHub account
    - Can view own team repositories
    - Can sync repositories to owned projects
    - Cannot configure global webhooks

  PM/Dev Lead/QA Lead:
    - Can connect GitHub account
    - Can view assigned project repositories
    - Cannot initiate new repository sync
    - Can view repository contents

  Security Lead/DevOps Lead:
    - Can connect GitHub account
    - Can view all project repositories
    - Can audit repository access logs
    - Can manage CI/CD webhooks (DevOps)

  Admin:
    - Full GitHub integration management
    - Can configure OAuth app settings
    - Can manage webhook secrets
    - Can revoke any user's GitHub connection
```

### 9.3 GitHub Features by Role

| Feature | CEO/CTO/CPO | EM | PM/Dev/QA | Security | DevOps | Admin |
|---------|------------|-----|-----------|----------|--------|-------|
| Connect own GitHub | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| List repositories | All | Own team | Assigned | All | All | All |
| Sync repo to project | Any | Own | ❌ | ❌ | Own CI/CD | Any |
| Configure webhooks | ✅ | ❌ | ❌ | ❌ | ✅ | ✅ |
| View audit logs | ✅ | Own | ❌ | ✅ | ✅ | ✅ |
| Revoke connections | Own | Own | Own | ❌ | ❌ | Any |

### 9.4 Role Assignment for New Users

Khi user mới đăng ký (via GitHub OAuth hoặc email):

```yaml
Default Role: PM (Product Manager)
  - Reason: Safe default với quyền tối thiểu
  - Can: View assigned projects, connect GitHub
  - Cannot: Create projects, approve gates

Role Upgrade Flow:
  1. Admin hoặc CEO/CTO assign role cho user
  2. User's permissions update immediately
  3. Audit log recorded

Auto-Role Detection (Future Enhancement):
  - GitHub organization owner → Suggest EM role
  - GitHub repo admin → Suggest Dev Lead role
  - Multiple repos with CI/CD → Suggest DevOps Lead role
```

---

## 10. SDLC 5.1.3 Stage Mapping

### 10.1 GitHub Integration in SDLC Lifecycle

```yaml
Stage 00 (WHY - Foundation):
  GitHub Usage: None (discovery phase)
  Roles Active: CPO, PM

Stage 01 (WHAT - Planning):
  GitHub Usage: Reference existing repos for context
  Roles Active: CPO, PM, EM

Stage 02 (HOW - Design):
  GitHub Usage: Analyze repo structure, suggest architecture
  Roles Active: CTO, Dev Lead, Security Lead

Stage 04 (BUILD - Development|:
  GitHub Usage:
    - Sync commits/PRs as evidence
    - Auto-evaluate code quality gates
    - Track branch policies
  Roles Active: Dev Lead, DevOps Lead, QA Lead

Stage 05 (TEST) - Quality):
  GitHub Usage:
    - Link test results to PRs
    - Collect CI/CD artifacts as evidence
    - Track test coverage
  Roles Active: QA Lead, Security Lead

Stage 06 (DEPLOY) - Go-Live):
  GitHub Usage:
    - Release creation webhook
    - Deployment artifacts
    - Rollback tracking
  Roles Active: DevOps Lead, CTO

Stage 07 (OPERATE) - Production):
  GitHub Usage:
    - Issue/bug tracking sync
    - Incident correlation
  Roles Active: DevOps Lead, Data Lead

Stage 03 (INTEGRATE):
  GitHub Usage: API/webhook management
  Roles Active: CIO, DevOps Lead

Stage 08 (COLLABORATE):
  GitHub Usage: Team activity sync, PR reviews
  Roles Active: All team roles

Stage 09 (GOVERN):
  GitHub Usage: Compliance reports, audit trails
  Roles Active: CEO, CTO, CPO, Security Lead
```

---

## 11. Approval

| Role | Name | Approval | Date |
|------|------|----------|------|
| **CPO** | Tai Dang | PENDING | Nov 29, 2025 |
| **CTO** | [CTO Name] | PENDING | Nov 29, 2025 |
| **Frontend Lead** | [FE Lead] | PENDING | Nov 29, 2025 |

---

**Last Updated**: November 29, 2025
**Status**: CLARIFICATION DOCUMENT - Pending Implementation
**Priority**: HIGH - Impacts UX consistency

---

*This document clarifies the distinction between GitHub OAuth Login and GitHub Repository Integration to ensure consistent UX and avoid unnecessary "Connect GitHub" prompts for users who already authenticated via GitHub.*
