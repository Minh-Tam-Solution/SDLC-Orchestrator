# E2E Test Scenarios - SDLC Orchestrator

**Version**: 3.0.0
**Date**: November 29, 2025
**Status**: ACTIVE - STAGE 03 (BUILD)
**Authority**: QA Lead + CTO Approved
**Framework**: SDLC 5.1.3.1 Complete Lifecycle
**Project**: NQH-Bot Platform - Vietnamese Enterprise Chatbot

---

## 1. Overview

This document defines comprehensive End-to-End (E2E) test scenarios for SDLC Orchestrator, covering all 5 Functional Requirements (FR1-FR5) and critical user journeys. All test scenarios are synchronized with the seed data in `DEMO-SEED-DATA.sql` v3.0.0 and Alembic migration `a502ce0d23a7`.

**Test Project**: NQH-Bot Platform - The real-world project led by CEO Tai Dang with 2 teams (Local + Remote) using SDLC 5.1.3.1.

### 1.1 Functional Requirements Coverage

| FR | Name | Description | Test Coverage |
|----|------|-------------|---------------|
| FR1 | Quality Gate Management | Gate Engine with policy-as-code | TC-GATE-* |
| FR2 | Evidence Vault | Auto-collection + SHA256 integrity | TC-EVID-* |
| FR3 | AI Context Engine | Stage-aware AI assistance | TC-AI-* |
| FR4 | Real-Time Dashboard | Overview + metrics + WebSocket | TC-DASH-* |
| FR5 | Policy Pack Library | 100+ SDLC 5.1.3 policies | TC-POL-* |

### 1.2 Test Environment

| Component | Dev URL | Production URL (Local Test) | Port |
|-----------|---------|------------------------------|------|
| Frontend | http://localhost:3000 | http://localhost:8310 | 3000/8310 |
| Backend API | http://localhost:8000 | http://localhost:8300 | 8000/8300 |
| API Docs | http://localhost:8000/api/docs | http://localhost:8300/api/docs | - |
| MinIO Console | http://localhost:9001 | http://localhost:9011 | 9001/9011 |
| OPA | http://localhost:8181 | http://localhost:8185 | 8181/8185 |
| PostgreSQL | localhost:5432 | localhost:5450 | 5432/5450 |
| Redis | localhost:6379 | localhost:6395 | 6379/6395 |

### 1.3 Test Accounts

| Role | Email | Password | Description | User ID |
|------|-------|----------|-------------|---------|
| **Platform Admin** | admin@sdlc-orchestrator.io | Admin@123 | Full access, superuser | a0000000-0000-0000-0000-000000000001 |
| **NQH CEO** | taidt@mtsolution.com.vn | Admin@123 | Leads Local + Remote teams | b0000000-0000-0000-0000-000000000001 |
| **NQH CPO** | dunglt@mtsolution.com.vn | Admin@123 | Product strategy | b0000000-0000-0000-0000-000000000002 |
| **NQH CTO** | dvhiep@nqh.com.vn | Admin@123 | Technical leadership | b0000000-0000-0000-0000-000000000003 |
| **Local TL** | dangtt1971@gmail.com | Admin@123 | Local Team Lead (Endior) | b0000000-0000-0000-0000-000000000004 |
| **Remote TL** | ltmhang@nqh.com.vn | Admin@123 | Remote Team Lead (Hang Le) | b0000000-0000-0000-0000-000000000005 |
| **Local Dev 1** | local.dev1@nqh.com.vn | Admin@123 | Local team developer | b0000000-0000-0000-0000-000000000006 |
| **Local Dev 2** | local.dev2@nqh.com.vn | Admin@123 | Local team developer | b0000000-0000-0000-0000-000000000007 |
| **Remote Dev 1** | remote.dev1@nqh.com.vn | Admin@123 | Remote team developer | b0000000-0000-0000-0000-000000000008 |
| **Remote Dev 2** | remote.dev2@nqh.com.vn | Admin@123 | Remote team developer | b0000000-0000-0000-0000-000000000009 |
| **QA Lead** | qa.lead@nqh.com.vn | Admin@123 | Quality assurance | b0000000-0000-0000-0000-000000000010 |
| **Inactive User** | inactive@nqh.com.vn | Admin@123 | is_active=false (for auth tests) | b0000000-0000-0000-0000-000000000011 |

### 1.4 Test Projects

| Project | Stage | Status | Gates | Description | Owner |
|---------|-------|--------|-------|-------------|-------|
| NQH-Bot Platform | BUILD | Active | 5 | Main platform - Vietnamese AI chatbot | CEO Tai Dang |
| NQH-Bot Analytics Module | WHAT | Active | 4 | Analytics feature - Remote Team | TL Hang Le |
| NQH-Bot NLP Engine | HOW | Active | 3 | Vietnamese NLP - Local Team | TL Endior |
| NQH-Bot CRM Integration | VERIFY | Active | 7 | CRM system integration | CTO Hiep Dinh |
| NQH-Bot Mobile App | WHY | Active | 1 | Mobile app exploration | CPO Dung Luong |
| Archived PoC | - | Inactive | 0 | Archived proof of concept | - |

---

## 2. User Journey Test Scenarios

### 2.1 Authentication Flow (Security)

#### TC-AUTH-001: Email/Password Login - Success
```gherkin
Feature: User Authentication
  Scenario: Successful login with valid credentials
    Given user is on login page (http://localhost:3000/login)
    When user enters email "admin@sdlc-orchestrator.io"
    And user enters password "Admin@123"
    And user clicks "Sign In" button
    Then user is redirected to Dashboard (/)
    And user sees welcome message with name "Platform Admin"
    And JWT access_token is stored in localStorage
    And JWT refresh_token is stored in localStorage
    And response includes token_type "bearer"
    And response includes expires_in 3600

Expected API Response:
{
  "access_token": "eyJ...",
  "refresh_token": "eyJ...",
  "token_type": "bearer",
  "expires_in": 3600
}
```

#### TC-AUTH-002: Invalid Credentials - Wrong Password
```gherkin
Scenario: Login fails with incorrect password
  Given user is on login page
  When user enters email "admin@sdlc-orchestrator.io"
  And user enters password "wrongpassword"
  And user clicks "Sign In" button
  Then error message "Invalid email or password" is displayed
  And user remains on login page
  And no JWT tokens are stored

Expected API Response (401):
{
  "detail": "Invalid email or password"
}
```

#### TC-AUTH-003: Invalid Credentials - Non-existent User
```gherkin
Scenario: Login fails with non-existent email
  Given user is on login page
  When user enters email "nonexistent@example.com"
  And user enters password "anypassword"
  And user clicks "Sign In" button
  Then error message "Invalid email or password" is displayed
  And status code is 401
```

#### TC-AUTH-004: Inactive Account Login
```gherkin
Scenario: Login fails for inactive account
  Given user "inactive@nqh.com.vn" has is_active=false
  When user attempts login with correct password "Admin@123"
  Then error message "Account is deactivated" is displayed
  And status code is 403
```

#### TC-AUTH-005: Session Expiry & Token Refresh
```gherkin
Scenario: Automatic token refresh on expiry
  Given user is logged in with valid session
  And access token expires (after 1 hour)
  When user performs any authenticated action
  Then system automatically calls POST /api/v1/auth/refresh
  And new access_token is received
  And user action completes without re-login

API Call:
POST /api/v1/auth/refresh
{
  "refresh_token": "eyJ..."
}

Expected Response:
{
  "access_token": "eyJ...(new)",
  "token_type": "bearer",
  "expires_in": 3600
}
```

#### TC-AUTH-006: Logout
```gherkin
Scenario: Successful logout
  Given user is logged in
  When user clicks "Sign Out" in header
  Then POST /api/v1/auth/logout is called
  And user is redirected to login page
  And JWT tokens are cleared from localStorage
  And refresh_token is invalidated on server
  And subsequent API calls return 401
```

#### TC-AUTH-007: Protected Route Access Without Auth
```gherkin
Scenario: Redirect to login for protected routes
  Given user is NOT logged in (no tokens)
  When user navigates directly to /projects
  Then user is redirected to /login
  And original URL is stored for post-login redirect
  After successful login:
  Then user is redirected back to /projects
```

#### TC-AUTH-008: Token Tampering Detection
```gherkin
Scenario: Invalid JWT rejected
  Given user has a valid JWT token
  When token payload is modified (change user_id)
  And user makes API request with tampered token
  Then response is 401 Unauthorized
  And message is "Invalid token signature"
```

---

### 2.2 Dashboard Overview (FR4: Real-Time Dashboard)

#### TC-DASH-001: View Dashboard Statistics
```gherkin
Scenario: Dashboard displays correct statistics
  Given user is logged in as admin@sdlc-orchestrator.io
  When user navigates to Dashboard (/)
  Then user sees 4 stat cards:
    | Metric | Expected Value | Description |
    |--------|----------------|-------------|
    | Total Projects | 5 | Active NQH-Bot projects |
    | Active Gates | 19 | Non-deleted gates |
    | Pending Approvals | 4 | PENDING_APPROVAL status |
    | Pass Rate | ~68% | APPROVED / Total (13/19) |

API Endpoint: GET /api/v1/dashboard/stats
Expected Response:
{
  "total_projects": 5,
  "active_gates": 19,
  "pending_approvals": 4,
  "pass_rate": 68.4
}
```

#### TC-DASH-002: Recent Gate Activity
```gherkin
Scenario: Dashboard shows recent gate activity
  Given user is on Dashboard
  Then "Recent Gate Activity" section shows up to 5 gates
  And gates are ordered by updated_at DESC

Expected Gates (based on NQH-Bot Platform seed data):
| Gate | Project | Stage | Status |
|------|---------|-------|--------|
| G0.1 | NQH-Bot Mobile App | WHY | DRAFT |
| G5 | NQH-Bot CRM Integration | VERIFY | PENDING_APPROVAL |
| G2 | NQH-Bot Analytics | WHAT | PENDING_APPROVAL |
| G3 | NQH-Bot Platform | BUILD | PENDING_APPROVAL |
| G1 | NQH-Bot NLP Engine | WHAT | DRAFT |

API Endpoint: GET /api/v1/dashboard/recent-gates?limit=5
```

#### TC-DASH-003: Quick Actions Navigation
```gherkin
Scenario: Quick actions work correctly
  Given user is on Dashboard
  Then Quick Actions section displays:
    | Action | Link | Icon |
    |--------|------|------|
    | Create New Project | /projects/new | Plus |
    | Upload Evidence | /evidence | Upload |
    | Manage Policies | /policies | Shield |
  When user clicks "Create New Project"
  Then user navigates to /projects/new
```

#### TC-DASH-004: Dashboard Real-Time Updates (WebSocket)
```gherkin
Scenario: Dashboard updates in real-time
  Given user is on Dashboard with WebSocket connected
  When another user approves a gate
  Then Dashboard stats update automatically
  And "Pending Approvals" decreases by 1
  And "Pass Rate" is recalculated
  And notification toast appears
```

#### TC-DASH-005: Dashboard by Role
```gherkin
Scenario: Dashboard shows role-appropriate data
  Given user "local.dev1@nqh.com.vn" is logged in (Developer role)
  When user views Dashboard
  Then only NQH-Bot projects user is member of are counted
  And only accessible gates are shown in recent activity

  Given user "admin@sdlc-orchestrator.io" is logged in (Admin)
  When user views Dashboard
  Then all 5 NQH-Bot projects across organization are counted

  Given user "dangtt1971@gmail.com" is logged in (Local Team Lead)
  When user views Dashboard
  Then NLP Engine project is highlighted (team ownership)
```

---

### 2.3 Project Management (FR1: Quality Gate Management)

#### TC-PROJ-001: View Projects List
```gherkin
Scenario: List all accessible projects
  Given user is logged in as admin@sdlc-orchestrator.io
  When user navigates to Projects (/projects)
  Then user sees list of 5 active NQH-Bot projects:

| Project | Current Stage | Status | Progress | Owner |
|---------|---------------|--------|----------|-------|
| NQH-Bot Platform | BUILD | Active | 80% | CEO Tai Dang |
| NQH-Bot Analytics Module | WHAT | Active | 60% | TL Hang Le (Remote) |
| NQH-Bot NLP Engine | HOW | Active | 50% | TL Endior (Local) |
| NQH-Bot CRM Integration | VERIFY | Active | 90% | CTO Hiep Dinh |
| NQH-Bot Mobile App | WHY | Active | 10% | CPO Dung Luong |

Note: "Archived PoC" not shown (is_active=false)

API Endpoint: GET /api/v1/projects
```

#### TC-PROJ-002: View Project Detail
```gherkin
Scenario: View project with gates timeline
  Given user is on Projects page
  When user clicks on "NQH-Bot Platform"
  Then project detail page shows:
    - Name: NQH-Bot Platform
    - Description: Vietnamese enterprise AI chatbot with NLP capabilities
    - Current Stage: BUILD (Stage 03)
    - Owner: CEO Tai Dang (taidt@mtsolution.com.vn)
  And gates timeline shows:

| Gate | Stage | Type | Status | Evidence | Approved By |
|------|-------|------|--------|----------|-------------|
| G0.1 | WHY | PROBLEM_DEFINITION | APPROVED | 2 files | CPO Dung Luong |
| G0.2 | WHY | SOLUTION_DIVERSITY | APPROVED | 2 files | CPO Dung Luong |
| G1 | WHAT | PLANNING_COMPLETE | APPROVED | 3 files | CTO Hiep + CPO |
| G2 | HOW | DESIGN_READY | APPROVED | 4 files | CTO Hiep Dinh |
| G3 | BUILD | SHIP_READY | PENDING_APPROVAL | 0 files | - |

API Endpoint: GET /api/v1/projects/{id}
```

#### TC-PROJ-003: Create New Project
```gherkin
Scenario: Create project successfully
  Given user is on Projects page
  And user has "create_project" permission
  When user clicks "New Project" button
  Then project creation form appears
  And user fills:
    - Name: "New Feature - AI Integration"
    - Description: "Add AI capabilities to existing product"
  And user clicks "Create Project"
  Then project is created with:
    - Slug: auto-generated "new-feature-ai-integration"
    - Status: Active
    - Stage: WHY (initial stage)
    - Owner: current user
  And user is redirected to project detail page
  And success toast "Project created successfully" appears

API Call:
POST /api/v1/projects
{
  "name": "New Feature - AI Integration",
  "description": "Add AI capabilities to existing product"
}

Expected Response (201):
{
  "id": "uuid...",
  "name": "New Feature - AI Integration",
  "slug": "new-feature-ai-integration",
  "owner_id": "current-user-id",
  "is_active": true,
  "created_at": "..."
}
```

#### TC-PROJ-004: Update Project
```gherkin
Scenario: Update project details
  Given user is project owner or admin
  When user edits project "Demo Project"
  And changes description to "Updated description for demo"
  And clicks "Save"
  Then project is updated
  And audit log records the change

API Call:
PATCH /api/v1/projects/{id}
{
  "description": "Updated description for demo"
}
```

#### TC-PROJ-005: Archive Project
```gherkin
Scenario: Archive completed project
  Given user is project owner
  And project has completed all stages (OPERATE)
  When user clicks "Archive Project"
  And confirms archive action
  Then project.is_active = false
  And project.deleted_at is set
  And project disappears from active projects list
  And project remains accessible in "Archived" tab
```

#### TC-PROJ-006: Project Access Control
```gherkin
Scenario: User can only access member projects
  Given user "local.dev1@nqh.com.vn" is member of only Local Team projects
  When user views projects list
  Then only "NQH-Bot Platform" and "NQH-Bot NLP Engine" are shown

  When user tries to access Analytics Module project directly (Remote Team)
  Then 403 Forbidden is returned
  And message "You don't have access to this project"

Scenario: Team Lead sees all team projects
  Given user "dangtt1971@gmail.com" is Local Team Lead
  When user views projects list
  Then user sees NQH-Bot Platform and NQH-Bot NLP Engine
```

---

### 2.4 Gate Evaluation (FR1: Quality Gate Management)

#### TC-GATE-001: View Gate Status
```gherkin
Scenario: View gate details on project page
  Given user is on "NQH-Bot Platform" project detail
  Then gates are displayed with status indicators:

| Gate | Stage | Type | Status | Color |
|------|-------|------|--------|-------|
| G0.1 | WHY | PROBLEM_DEFINITION | APPROVED | Green |
| G0.2 | WHY | SOLUTION_DIVERSITY | APPROVED | Green |
| G1 | WHAT | PLANNING_COMPLETE | APPROVED | Green |
| G2 | HOW | DESIGN_READY | APPROVED | Green |
| G3 | BUILD | SHIP_READY | PENDING_APPROVAL | Yellow |

And each gate card shows:
  - Exit criteria checklist (SDLC 5.1.3.1 compliant)
  - Evidence count
  - Last updated date
  - Approvers (CEO/CPO/CTO as appropriate)
```

#### TC-GATE-002: Create New Gate
```gherkin
Scenario: Create gate for next stage
  Given user is on project detail page
  And project is at BUILD stage (Stage 03)
  When user clicks "Add Gate" button
  Then gate creation form shows:
    - Gate Name: G4 (auto-suggested based on sequence)
    - Gate Type: dropdown with stage-appropriate types
    - Stage: 04 (VERIFY) - auto-selected next stage
    - Description: text area
    - Exit Criteria: multi-input field
  And user fills:
    - Gate Name: G4
    - Gate Type: TEST_COMPLETE
    - Description: "Testing phase complete"
    - Exit Criteria:
      - "Unit tests 95%+"
      - "Integration tests 90%+"
      - "E2E tests 80%+"
  And user clicks "Create Gate"
  Then gate is created with status: DRAFT
  And gate appears in project gates list

API Call:
POST /api/v1/gates
{
  "gate_name": "G4",
  "gate_type": "TEST_COMPLETE",
  "project_id": "project-uuid",
  "stage": "VERIFY",
  "description": "Testing phase complete",
  "exit_criteria": ["Unit tests 95%+", "Integration tests 90%+", "E2E tests 80%+"]
}
```

#### TC-GATE-003: Submit Gate for Evaluation
```gherkin
Scenario: Submit gate for policy evaluation
  Given gate "G3" is in DRAFT status
  And gate has required evidence uploaded (3+ documents)
  When user clicks "Submit for Evaluation"
  Then:
    1. POST /api/v1/gates/{id}/evaluate is called
    2. OPA evaluates all applicable policies
    3. Policy results are returned:
       - Passed: 8 policies
       - Failed: 0 policies
       - Warnings: 1 policy
    4. Gate status changes to PENDING_APPROVAL
    5. Evaluation result is recorded
    6. Notification sent to approvers

API Response:
{
  "gate_id": "gate-uuid",
  "status": "PENDING_APPROVAL",
  "evaluation_result": {
    "passed_policies": 8,
    "failed_policies": 0,
    "warnings": 1,
    "overall_result": "PASS",
    "details": [
      {"policy": "frd_required", "result": "PASS", "message": "FRD document found"},
      {"policy": "api_spec_required", "result": "PASS", "message": "OpenAPI spec found"},
      ...
    ]
  }
}
```

#### TC-GATE-004: Approve Gate (Authorized User)
```gherkin
Scenario: CTO approves gate G3
  Given user "dvhiep@nqh.com.vn" (CTO Hiep Dinh) is logged in
  And user has "approve_gate" permission
  And gate "G3" (NQH-Bot Platform) is PENDING_APPROVAL
  When user navigates to gate detail
  And reviews evidence documents
  And clicks "Approve Gate"
  And enters comment: "Ollama integration ready. Vietnamese NLP pipeline validated. Ship it!"
  Then:
    1. POST /api/v1/gates/{id}/approve is called
    2. Gate status → APPROVED
    3. Approval record created in gate_approvals
    4. Audit log entry created
    5. Project progress updated
    6. Notification sent to CEO Tai Dang and team

API Call:
POST /api/v1/gates/{gate_id}/approve
{
  "comment": "Ollama integration ready. Vietnamese NLP pipeline validated. Ship it!"
}

Response:
{
  "gate_id": "...",
  "status": "APPROVED",
  "approved_by": "dvhiep@nqh.com.vn",
  "approved_at": "2025-11-29T14:30:00Z",
  "comment": "Ollama integration ready. Vietnamese NLP pipeline validated. Ship it!"
}
```

#### TC-GATE-005: Reject Gate with Feedback
```gherkin
Scenario: CTO rejects gate with actionable feedback
  Given user "dvhiep@nqh.com.vn" (CTO Hiep Dinh) is logged in
  And gate "G1" (NQH-Bot NLP Engine) is in DRAFT
  When user reviews gate evidence
  And finds Vietnamese NLP specs incomplete
  And clicks "Reject Gate"
  And enters rejection reason:
    "NLP Pipeline specs 75% complete. Missing:
    - Vietnamese tokenization algorithm specs
    - Ollama model fine-tuning parameters
    - Response latency requirements (<100ms)
    Please address these items and resubmit."
  Then:
    1. POST /api/v1/gates/{id}/reject is called
    2. Gate status → REJECTED
    3. Rejection reason recorded
    4. Notification sent to Local TL Endior
    5. CEO Tai Dang alerted

API Call:
POST /api/v1/gates/{gate_id}/reject
{
  "reason": "NLP Pipeline specs 75% complete. Missing: Vietnamese tokenization..."
}
```

#### TC-GATE-006: Multi-Approval Gate
```gherkin
Scenario: Gate requires multiple approvers (CTO + CPO)
  Given gate "G1" (NQH-Bot Platform) requires approval from CTO AND CPO
  And CTO "dvhiep@nqh.com.vn" (Hiep Dinh) approves
  Then gate status remains PENDING_APPROVAL
  And approval count shows "1/2"

  When CPO "dunglt@mtsolution.com.vn" (Dung Luong) approves
  Then gate status → APPROVED
  And both approvers recorded in gate_approvals
```

#### TC-GATE-007: Gate Evaluation Policy Failure
```gherkin
Scenario: Gate fails policy evaluation
  Given gate "G3" has no security baseline document
  When user submits gate for evaluation
  Then OPA returns policy failure:
    - Policy: "security_baseline_required"
    - Result: FAIL
    - Message: "Security baseline document not found"
  And gate status remains DRAFT (not submitted)
  And user sees actionable error: "Upload security baseline document"
```

---

### 2.5 Evidence Vault (FR2: Evidence Vault)

#### TC-EVID-001: View Evidence List
```gherkin
Scenario: View all evidence for a gate
  Given user is on gate "G0.1" (NQH-Bot Platform) detail page
  Then Evidence section shows 2 files:

| Title | Type | Size | Uploaded By | Upload Date |
|-------|------|------|-------------|-------------|
| NQH-Bot Problem Statement | DOCUMENT | 2.0 MB | CEO Tai Dang | Sep 6, 2025 |
| Vietnamese Enterprise Chatbot Survey | DATA | 512 KB | CEO Tai Dang | Sep 7, 2025 |

API Endpoint: GET /api/v1/evidence?gate_id={gate_id}
```

#### TC-EVID-002: Upload Evidence File
```gherkin
Scenario: Upload evidence document
  Given user is on gate "G3" (BFlow) detail page
  When user clicks "Upload Evidence"
  Then upload dialog appears
  And user selects file: "test-coverage-report.html" (500 KB)
  And user fills metadata:
    - Title: "Test Coverage Report - Week 10"
    - Evidence Type: REPORT
    - Description: "Current test coverage: Unit 92%, Integration 88%, E2E 75%"
  And user clicks "Upload"
  Then:
    1. File uploads to MinIO (evidence-vault bucket)
    2. SHA256 hash calculated: "abc123..."
    3. Metadata stored in PostgreSQL
    4. Evidence appears in list
    5. Audit log records upload

API Call:
POST /api/v1/evidence/upload
Content-Type: multipart/form-data
- file: test-coverage-report.html
- gate_id: gate-uuid
- title: "Test Coverage Report - Week 10"
- evidence_type: REPORT
- description: "Current test coverage..."

Response (201):
{
  "id": "evidence-uuid",
  "title": "Test Coverage Report - Week 10",
  "file_name": "test-coverage-report.html",
  "file_size": 524288,
  "mime_type": "text/html",
  "sha256_hash": "abc123...",
  "storage_path": "s3://evidence-vault/bflow-v3/g3/test-coverage-report.html",
  "uploaded_by": "user-uuid",
  "uploaded_at": "2025-11-29T..."
}
```

#### TC-EVID-003: Verify Evidence Integrity
```gherkin
Scenario: Verify evidence file hasn't been tampered
  Given evidence "Problem Statement Document" exists
  And original SHA256 hash: "a1b2c3d4..."
  When user clicks "Verify Integrity"
  Then:
    1. GET /api/v1/evidence/{id}/verify called
    2. System re-downloads file from MinIO
    3. Recalculates SHA256 hash
    4. Compares with stored hash
    5. Result: "Integrity Verified ✓"

API Response:
{
  "evidence_id": "...",
  "integrity_status": "VERIFIED",
  "stored_hash": "a1b2c3d4...",
  "calculated_hash": "a1b2c3d4...",
  "verified_at": "2025-11-29T..."
}

Scenario: Detect tampered evidence
  Given file was modified in MinIO storage
  When integrity check runs
  Then result: "INTEGRITY_FAILED ✗"
  And alert sent to security team
  And evidence flagged for review
```

#### TC-EVID-004: Download Evidence
```gherkin
Scenario: Download evidence file
  Given user has access to gate "G1"
  When user clicks "Download" on "Functional Requirements Document"
  Then:
    1. GET /api/v1/evidence/{id}/download called
    2. Pre-signed URL generated from MinIO
    3. File downloads: functional-requirements.pdf
    4. Audit log records download action

API Response:
{
  "download_url": "https://minio:9000/evidence-vault/...?signature=...",
  "expires_in": 3600
}
```

#### TC-EVID-005: Search Evidence
```gherkin
Scenario: Search evidence by keyword
  Given 10 evidence files exist across projects
  When user enters search query: "architecture"
  Then results show matching evidence:
    - "System Architecture Document" (BFlow G2)

API Endpoint: GET /api/v1/evidence?search=architecture

Scenario: Filter evidence by type
  When user filters by type: "DOCUMENT"
  Then only DOCUMENT type evidence shown

API Endpoint: GET /api/v1/evidence?evidence_type=DOCUMENT
```

#### TC-EVID-006: Evidence Type Categories
```gherkin
Scenario: Upload different evidence types
  Evidence types supported:
  | Type | Description | Allowed Extensions |
  |------|-------------|--------------------|
  | DOCUMENT | PDF, Word docs | .pdf, .doc, .docx |
  | CODE | Source code, specs | .yaml, .json, .py, .ts |
  | DATA | Spreadsheets, CSVs | .xlsx, .csv |
  | DIAGRAM | Architecture diagrams | .png, .jpg, .svg |
  | REPORT | Test reports, coverage | .html, .xml |
  | VIDEO | Demo recordings | .mp4, .webm |
```

#### TC-EVID-007: Evidence Access Control
```gherkin
Scenario: Users can only view evidence for accessible gates
  Given user "local.dev1@nqh.com.vn" is member of Local Team projects only
  When user tries to view Analytics Module (Remote Team) evidence
  Then 403 Forbidden returned
  And audit log records unauthorized access attempt

Scenario: Team Lead can view all team evidence
  Given user "dangtt1971@gmail.com" (Local TL Endior) is logged in
  When user views NQH-Bot NLP Engine evidence
  Then all evidence files are accessible
  And audit log records successful access
```

---

### 2.6 Policy Management (FR5: Policy Pack Library)

#### TC-POL-001: View Active Policies
```gherkin
Scenario: List all active policies
  Given user is on Policies page (/policies)
  Then user sees 10 active policies:

| Policy Name | Stage | Description | Status |
|-------------|-------|-------------|--------|
| problem_statement_required | WHY | Problem statement must be uploaded | Active |
| user_research_required | WHY | User research data must be provided | Active |
| solution_alternatives_required | WHY | 3+ solutions must be evaluated | Active |
| frd_required | WHAT | FRD must be uploaded | Active |
| api_spec_required | WHAT | OpenAPI spec required | Active |
| data_model_required | WHAT | Data model/ERD required | Active |
| architecture_doc_required | HOW | Architecture document required | Active |
| security_baseline_required | HOW | Security baseline required | Active |
| test_coverage_threshold | VERIFY | Code coverage ≥ 80% | Active |
| no_critical_bugs | VERIFY | No critical/blocker bugs | Active |

API Endpoint: GET /api/v1/policies
```

#### TC-POL-002: View Policy Detail
```gherkin
Scenario: View policy Rego code
  Given user clicks on "test_coverage_threshold"
  Then policy detail shows:
    - Name: test_coverage_threshold
    - Stage: VERIFY
    - Version: 1.0.0
    - Description: Code coverage must be at least 80%
    - Rego Code:
      ```rego
      package sdlc.verify.coverage

      default allow = false

      allow {
        input.coverage >= 80
      }
      ```
```

#### TC-POL-003: Create Custom Policy
```gherkin
Scenario: Admin creates new policy
  Given user is admin
  When user clicks "Create Policy"
  And fills policy form:
    - Name: "code_review_required"
    - Description: "All code must have at least 2 reviewers"
    - Stage: BUILD
    - Rego Code:
      ```rego
      package sdlc.build.review

      default allow = false

      allow {
        count(input.reviewers) >= 2
      }
      ```
  And clicks "Save"
  Then policy is created
  And policy is validated against OPA
  And policy appears in policy list

API Call:
POST /api/v1/policies
{
  "name": "code_review_required",
  "description": "All code must have at least 2 reviewers",
  "stage": "BUILD",
  "rego_code": "package sdlc.build.review..."
}
```

#### TC-POL-004: Activate/Deactivate Policy
```gherkin
Scenario: Deactivate policy for specific project
  Given policy "solution_alternatives_required" is active
  When admin clicks "Deactivate"
  And confirms action
  Then policy.is_active = false
  And policy no longer evaluated for gates
  And audit log records change
```

#### TC-POL-005: Policy Evaluation Results
```gherkin
Scenario: View policy evaluation history
  Given gate "G0.1" (BFlow) has been evaluated
  When user views gate evaluations
  Then evaluation history shows:

| Policy | Result | Message | Evaluated At |
|--------|--------|---------|--------------|
| problem_statement_required | PASS | Document found | Oct 9, 2025 |
| user_research_required | PASS | Data found | Oct 9, 2025 |

API Endpoint: GET /api/v1/gates/{id}/evaluations
```

#### TC-POL-006: Policy Test Mode
```gherkin
Scenario: Test policy before activation
  Given user creates new policy
  When user clicks "Test Policy"
  And provides sample input:
    {
      "evidence": [
        {"type": "DOCUMENT", "title": "Test FRD"}
      ]
    }
  Then policy evaluates against sample
  And result shown: PASS or FAIL
  And user can adjust policy before activation
```

---

### 2.7 AI Context Engine (FR3: AI Context Engine)

#### TC-AI-001: Generate Stage-Aware Checklist
```gherkin
Scenario: AI generates checklist for WHY stage
  Given user is on gate "G0.1" (WHY stage)
  When user clicks "Generate Checklist with AI"
  Then AI generates stage-specific checklist:
    - [ ] Problem statement documented with metrics
    - [ ] 10+ user personas defined
    - [ ] Market research (TAM/SAM/SOM) completed
    - [ ] Competitive analysis with 3+ competitors
    - [ ] Success metrics (OKRs) defined
    - [ ] Stakeholder interviews conducted (5+)
    - [ ] Pain points prioritized (MoSCoW)

API Endpoint: POST /api/v1/ai/generate-checklist
{
  "gate_id": "gate-uuid",
  "stage": "WHY"
}
```

#### TC-AI-002: AI Evidence Review
```gherkin
Scenario: AI analyzes uploaded document
  Given user uploads "architecture-document.pdf" for G2
  When AI analyzes document
  Then AI provides suggestions:
    - "Document covers 4-layer architecture ✓"
    - "Security considerations addressed ✓"
    - "Missing: Performance requirements section"
    - "Missing: Disaster recovery plan"
    - "Recommendation: Add scalability section"

API Endpoint: POST /api/v1/ai/review-evidence
{
  "evidence_id": "evidence-uuid"
}
```

#### TC-AI-003: AI Policy Recommendation
```gherkin
Scenario: AI recommends policies for project
  Given user creates new project
  And enters description: "E-commerce platform with payment processing"
  When AI analyzes project type
  Then AI recommends:
    - "SDLC 5.1.3 Standard" (100% match)
    - "Security Baseline - PCI DSS" (95% match - payment processing)
    - "Performance Pack" (85% match - e-commerce)

API Endpoint: POST /api/v1/ai/recommend-policies
{
  "project_description": "E-commerce platform with payment processing"
}
```

#### TC-AI-004: AI-Assisted Gate Approval Summary
```gherkin
Scenario: AI generates approval summary for approver
  Given CTO is reviewing gate "G2" for approval
  When CTO clicks "Generate Summary"
  Then AI summarizes:
    - Evidence uploaded: 3 documents (100% required)
    - Policies passed: 2/2 (100%)
    - Key highlights:
      - 4-layer architecture documented
      - AGPL containment validated
      - Security baseline OWASP ASVS L2
    - Risk assessment: LOW
    - Recommendation: APPROVE
```

---

## 3. API Test Scenarios

### 3.1 Authentication API

#### TC-API-AUTH-001: Login
```bash
# Request
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@sdlc-orchestrator.io","password":"Admin@123"}'

# Expected Response (200 OK)
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 3600
}
```

#### TC-API-AUTH-002: Get Current User
```bash
# Request
curl http://localhost:8000/api/v1/auth/me \
  -H "Authorization: Bearer ${TOKEN}"

# Expected Response (200 OK)
{
  "id": "a0000000-0000-0000-0000-000000000001",
  "email": "admin@sdlc-orchestrator.io",
  "name": "Platform Admin",
  "is_active": true,
  "is_superuser": true,
  "mfa_enabled": false,
  "created_at": "2025-11-13T10:00:00Z"
}
```

#### TC-API-AUTH-003: Refresh Token
```bash
# Request
curl -X POST http://localhost:8000/api/v1/auth/refresh \
  -H "Content-Type: application/json" \
  -d '{"refresh_token":"eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."}'

# Expected Response (200 OK)
{
  "access_token": "eyJ...(new token)",
  "token_type": "bearer",
  "expires_in": 3600
}
```

#### TC-API-AUTH-004: Logout
```bash
# Request
curl -X POST http://localhost:8000/api/v1/auth/logout \
  -H "Authorization: Bearer ${TOKEN}"

# Expected Response (200 OK)
{
  "message": "Successfully logged out"
}
```

---

### 3.2 Projects API

#### TC-API-PROJ-001: List Projects
```bash
# Request
curl http://localhost:8000/api/v1/projects \
  -H "Authorization: Bearer ${TOKEN}"

# Expected Response (200 OK)
{
  "items": [
    {
      "id": "c0000000-0000-0000-0000-000000000001",
      "name": "BFlow Workflow Automation - v3.0",
      "slug": "bflow-workflow-v3",
      "description": "Workflow automation platform...",
      "owner_id": "b0000000-0000-0000-0000-000000000003",
      "is_active": true,
      "created_at": "2025-10-01T10:00:00Z"
    },
    ...
  ],
  "total": 4,
  "page": 1,
  "size": 20
}
```

#### TC-API-PROJ-002: Get Project Detail
```bash
# Request
curl http://localhost:8000/api/v1/projects/c0000000-0000-0000-0000-000000000001 \
  -H "Authorization: Bearer ${TOKEN}"

# Expected Response (200 OK)
{
  "id": "c0000000-0000-0000-0000-000000000001",
  "name": "BFlow Workflow Automation - v3.0",
  "slug": "bflow-workflow-v3",
  "description": "Workflow automation platform...",
  "owner_id": "b0000000-0000-0000-0000-000000000003",
  "is_active": true,
  "created_at": "2025-10-01T10:00:00Z",
  "gates": [
    {
      "id": "e0000000-0000-0000-0000-000000000001",
      "gate_name": "G0.1",
      "gate_type": "PROBLEM_DEFINITION",
      "stage": "WHY",
      "status": "APPROVED"
    },
    ...
  ],
  "members": [
    {
      "user_id": "b0000000-0000-0000-0000-000000000003",
      "role": "owner"
    },
    ...
  ]
}
```

#### TC-API-PROJ-003: Create Project
```bash
# Request
curl -X POST http://localhost:8000/api/v1/projects \
  -H "Authorization: Bearer ${TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "New AI Feature",
    "description": "AI integration for product recommendations"
  }'

# Expected Response (201 Created)
{
  "id": "new-uuid...",
  "name": "New AI Feature",
  "slug": "new-ai-feature",
  "description": "AI integration for product recommendations",
  "owner_id": "a0000000-0000-0000-0000-000000000001",
  "is_active": true,
  "created_at": "2025-11-29T..."
}
```

---

### 3.3 Gates API

#### TC-API-GATE-001: List Gates
```bash
# Request - List all gates for a project
curl "http://localhost:8000/api/v1/gates?project_id=c0000000-0000-0000-0000-000000000001" \
  -H "Authorization: Bearer ${TOKEN}"

# Expected Response (200 OK)
{
  "items": [
    {
      "id": "e0000000-0000-0000-0000-000000000001",
      "gate_name": "G0.1",
      "gate_type": "PROBLEM_DEFINITION",
      "stage": "WHY",
      "status": "APPROVED",
      "project_id": "c0000000-0000-0000-0000-000000000001",
      "exit_criteria": ["Problem statement documented", "User personas defined", "Market research completed"],
      "created_by": "b0000000-0000-0000-0000-000000000003",
      "approved_at": "2025-10-10T15:00:00Z"
    },
    ...
  ],
  "total": 5
}
```

#### TC-API-GATE-002: Create Gate
```bash
# Request
curl -X POST http://localhost:8000/api/v1/gates \
  -H "Authorization: Bearer ${TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{
    "gate_name": "G4",
    "gate_type": "TEST_COMPLETE",
    "project_id": "c0000000-0000-0000-0000-000000000003",
    "stage": "VERIFY",
    "description": "Testing phase complete",
    "exit_criteria": ["Unit tests 95%+", "Integration tests 90%+", "E2E tests 80%+"]
  }'

# Expected Response (201 Created)
{
  "id": "new-gate-uuid...",
  "gate_name": "G4",
  "gate_type": "TEST_COMPLETE",
  "stage": "VERIFY",
  "status": "DRAFT",
  "exit_criteria": ["Unit tests 95%+", "Integration tests 90%+", "E2E tests 80%+"],
  "created_by": "a0000000-0000-0000-0000-000000000001",
  "created_at": "2025-11-29T..."
}
```

#### TC-API-GATE-003: Evaluate Gate
```bash
# Request
curl -X POST http://localhost:8000/api/v1/gates/e0000000-0000-0000-0000-000000000005/evaluate \
  -H "Authorization: Bearer ${TOKEN}"

# Expected Response (200 OK)
{
  "gate_id": "e0000000-0000-0000-0000-000000000005",
  "status": "PENDING_APPROVAL",
  "evaluation_result": {
    "overall_result": "PASS",
    "passed_policies": 8,
    "failed_policies": 0,
    "warnings": 1,
    "details": [
      {"policy": "frd_required", "result": "PASS"},
      {"policy": "api_spec_required", "result": "PASS"},
      ...
    ]
  },
  "evaluated_at": "2025-11-29T..."
}
```

#### TC-API-GATE-004: Approve Gate
```bash
# Request
curl -X POST http://localhost:8000/api/v1/gates/e0000000-0000-0000-0000-000000000005/approve \
  -H "Authorization: Bearer ${CTO_TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{"comment": "All requirements met. Approved for production."}'

# Expected Response (200 OK)
{
  "gate_id": "e0000000-0000-0000-0000-000000000005",
  "status": "APPROVED",
  "approved_by": "b0000000-0000-0000-0000-000000000001",
  "approved_at": "2025-11-29T14:30:00Z",
  "comment": "All requirements met. Approved for production."
}
```

#### TC-API-GATE-005: Reject Gate
```bash
# Request
curl -X POST http://localhost:8000/api/v1/gates/e0000000-0000-0000-0000-000000000008/reject \
  -H "Authorization: Bearer ${CTO_TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{"reason": "FRD incomplete. Missing AI recommendation specs."}'

# Expected Response (200 OK)
{
  "gate_id": "e0000000-0000-0000-0000-000000000008",
  "status": "REJECTED",
  "rejected_by": "b0000000-0000-0000-0000-000000000001",
  "rejected_at": "2025-11-29T14:35:00Z",
  "reason": "FRD incomplete. Missing AI recommendation specs."
}
```

---

### 3.4 Evidence API

#### TC-API-EVID-001: Upload Evidence
```bash
# Request
curl -X POST http://localhost:8000/api/v1/evidence/upload \
  -H "Authorization: Bearer ${TOKEN}" \
  -F "file=@architecture-diagram.pdf" \
  -F "gate_id=e0000000-0000-0000-0000-000000000004" \
  -F "title=System Architecture Document" \
  -F "evidence_type=DOCUMENT" \
  -F "description=4-layer architecture diagram"

# Expected Response (201 Created)
{
  "id": "new-evidence-uuid",
  "title": "System Architecture Document",
  "file_name": "architecture-diagram.pdf",
  "file_size": 4194304,
  "mime_type": "application/pdf",
  "sha256_hash": "6789012345678901234567890abcdef...",
  "storage_path": "s3://evidence-vault/bflow-v3/g2/architecture-diagram.pdf",
  "uploaded_by": "a0000000-0000-0000-0000-000000000001",
  "uploaded_at": "2025-11-29T..."
}
```

#### TC-API-EVID-002: Verify Integrity
```bash
# Request
curl http://localhost:8000/api/v1/evidence/g0000000-0000-0000-0000-000000000001/verify \
  -H "Authorization: Bearer ${TOKEN}"

# Expected Response (200 OK)
{
  "evidence_id": "g0000000-0000-0000-0000-000000000001",
  "integrity_status": "VERIFIED",
  "stored_hash": "a1b2c3d4e5f6789012345678901234567890abcdef1234567890abcdef12345678",
  "calculated_hash": "a1b2c3d4e5f6789012345678901234567890abcdef1234567890abcdef12345678",
  "verified_at": "2025-11-29T..."
}
```

#### TC-API-EVID-003: Download Evidence
```bash
# Request
curl http://localhost:8000/api/v1/evidence/g0000000-0000-0000-0000-000000000001/download \
  -H "Authorization: Bearer ${TOKEN}"

# Expected Response (200 OK)
{
  "download_url": "http://minio:9000/evidence-vault/bflow-v3/g01/problem-statement.pdf?X-Amz-Signature=...",
  "expires_in": 3600,
  "file_name": "problem-statement.pdf"
}
```

---

### 3.5 Policies API

#### TC-API-POL-001: List Policies
```bash
# Request
curl http://localhost:8000/api/v1/policies \
  -H "Authorization: Bearer ${TOKEN}"

# Expected Response (200 OK)
{
  "items": [
    {
      "id": "h0000000-0000-0000-0000-000000000001",
      "name": "problem_statement_required",
      "description": "Problem statement document must be uploaded",
      "stage": "WHY",
      "is_active": true,
      "version": "1.0.0"
    },
    ...
  ],
  "total": 10
}
```

#### TC-API-POL-002: Evaluate Policies for Gate
```bash
# Request
curl -X POST http://localhost:8000/api/v1/policies/evaluate \
  -H "Authorization: Bearer ${TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{
    "gate_id": "e0000000-0000-0000-0000-000000000003",
    "input_data": {
      "evidence": [
        {"type": "DOCUMENT", "title": "Functional Requirements Document"},
        {"type": "CODE", "file_name": "openapi.yaml"},
        {"type": "DIAGRAM", "title": "Data Model ERD"}
      ]
    }
  }'

# Expected Response (200 OK)
{
  "result": "PASS",
  "passed_policies": 3,
  "failed_policies": 0,
  "details": [
    {"policy": "frd_required", "result": "PASS", "message": "FRD document found"},
    {"policy": "api_spec_required", "result": "PASS", "message": "OpenAPI spec found"},
    {"policy": "data_model_required", "result": "PASS", "message": "Data model found"}
  ]
}
```

---

## 4. Performance Test Scenarios

### 4.1 Dashboard Performance

#### TC-PERF-001: Dashboard Load Time
```yaml
Target: <1s page load (p95)
Method: 100 concurrent users, 5 minutes duration
Tool: Locust

Expected Results:
  - p50 response time: <100ms
  - p95 response time: <200ms
  - p99 response time: <500ms
  - Throughput: >500 req/s
  - Error rate: <0.1%

Locust Script:
from locust import HttpUser, task

class DashboardUser(HttpUser):
    @task
    def load_dashboard(self):
        self.client.get("/api/v1/dashboard/stats",
                        headers={"Authorization": f"Bearer {token}"})
```

### 4.2 Evidence Upload Performance

#### TC-PERF-002: Concurrent Evidence Upload
```yaml
Target: 50 concurrent uploads (10MB each)
Method: Locust with file upload
Duration: 10 minutes

Expected Results:
  - Upload time (p95): <2s per 10MB file
  - No upload failures
  - MinIO handles concurrent writes
  - SHA256 hash calculation: <100ms
```

### 4.3 Gate Evaluation Performance

#### TC-PERF-003: OPA Policy Evaluation
```yaml
Target: 1000 policy evaluations/second
Method: Evaluate 10 policies per gate, 100 concurrent requests

Expected Results:
  - OPA evaluation (p95): <50ms
  - Full gate evaluation (p95): <100ms
  - No policy timeout errors
  - Memory stable (no leaks)
```

### 4.4 API Latency Targets

```yaml
Endpoint Performance (p95):
  GET /api/v1/auth/me: <20ms
  POST /api/v1/auth/login: <100ms
  GET /api/v1/projects: <100ms (paginated)
  GET /api/v1/projects/{id}: <50ms
  GET /api/v1/gates?project_id={id}: <50ms
  POST /api/v1/gates/{id}/evaluate: <100ms
  POST /api/v1/evidence/upload: <2000ms (10MB file)
  GET /api/v1/evidence/{id}/verify: <200ms
```

---

## 5. Security Test Scenarios

### 5.1 Authentication Security

#### TC-SEC-001: SQL Injection Prevention
```yaml
Input: email = "admin@test.com' OR '1'='1"
Expected: Login fails with validation error
Actual: SQLAlchemy ORM parameterizes queries
```

#### TC-SEC-002: JWT Token Tampering
```yaml
Action: Modify JWT payload (change user_id)
Expected: 401 Unauthorized
Actual: Token signature validation fails
```

#### TC-SEC-003: Rate Limiting
```yaml
Action: 100 login attempts in 10 seconds
Expected: Rate limit after 10 attempts
Response: 429 Too Many Requests
Cooldown: 60 seconds
```

#### TC-SEC-004: Password Brute Force Protection
```yaml
Action: 5 failed login attempts for same email
Expected: Account locked for 15 minutes
Response: "Account temporarily locked"
```

### 5.2 Authorization Security

#### TC-SEC-005: Cross-Project Access
```yaml
User: dev@bflow.vn (BFlow project only)
Action: GET /api/v1/projects/nqh-project-id
Expected: 403 Forbidden
Message: "You don't have access to this project"
```

#### TC-SEC-006: Role Escalation Prevention
```yaml
User: dev@bflow.vn (Developer role)
Action: POST /api/v1/gates/{id}/approve
Expected: 403 Forbidden
Message: "Insufficient permissions"
```

#### TC-SEC-007: Evidence Access Control
```yaml
User: dev@nqh.vn
Action: Download BFlow evidence
Expected: 403 Forbidden
Audit: Access attempt logged
```

### 5.3 Data Protection

#### TC-SEC-008: Sensitive Data in Logs
```yaml
Check: Password not logged in any form
Check: JWT tokens not logged
Check: PII masked in logs
```

#### TC-SEC-009: HTTPS Enforcement (Production)
```yaml
Action: HTTP request to production
Expected: Redirect to HTTPS (301)
HSTS: Strict-Transport-Security header present
```

---

## 6. Test Data Summary

### 6.1 Seed Data Overview - NQH-Bot Platform

```yaml
# SDLC Orchestrator - Automating CEO Tai Dang's SDLC 5.1.3.1 Framework
# CEO leads 2 teams (Local + Remote) developing NQH-Bot Platform

Users: 12 total
  - 1 Platform Admin (admin@sdlc-orchestrator.io)
  - 3 Executives: CEO Tai Dang, CPO Dung Luong, CTO Hiep Dinh
  - 3 Local Team: TL Endior, Local Dev 1-2
  - 3 Remote Team: TL Hang Le, Remote Dev 1-2
  - 1 QA Lead
  - 1 Inactive User (for auth tests)

Projects: 6 total (5 active)
  - NQH-Bot Platform (BUILD stage) - Main platform, CEO owned
  - NQH-Bot Analytics Module (WHAT stage) - Remote Team
  - NQH-Bot NLP Engine (HOW stage) - Local Team
  - NQH-Bot CRM Integration (VERIFY stage) - CTO owned
  - NQH-Bot Mobile App (WHY stage) - CPO owned
  - Archived PoC (Inactive)

Gates: 19 total
  - APPROVED: 13 (68%)
  - PENDING_APPROVAL: 4 (21%)
  - DRAFT: 2 (11%)

Evidence: 13 files
  - DOCUMENT: 6 (Problem Statement, FRD, Architecture, Security)
  - DATA: 2 (Market Survey, Vietnamese Enterprise Research)
  - CODE: 2 (OpenAPI, Ollama Config)
  - DIAGRAM: 2 (NLP Pipeline, System Architecture)
  - REPORT: 1 (Test Coverage)

Policies: 10 active (SDLC 5.1.3.1 compliant)
  - WHY: 3 (Problem Statement, User Research, Solution Alternatives)
  - WHAT: 3 (FRD, API Spec, Data Model)
  - HOW: 2 (Architecture, Security Baseline)
  - VERIFY: 2 (Test Coverage, No Critical Bugs)

Policy Evaluations: 9 records
Gate Approvals: 16 records
Audit Logs: 9 records
```

### 6.2 Test File Assets

Required files for evidence upload testing (NQH-Bot Platform):

| File | Size | Type | Purpose |
|------|------|------|---------|
| nqh-bot-problem-statement.pdf | 2 MB | DOCUMENT | G0.1 evidence |
| vietnamese-enterprise-chatbot-survey.xlsx | 512 KB | DATA | G0.1 evidence |
| nqh-bot-frd.pdf | 5 MB | DOCUMENT | G1 evidence |
| nqh-bot-openapi.yaml | 100 KB | CODE | G1 evidence |
| nqh-bot-data-model-erd.png | 1 MB | DIAGRAM | G1 evidence |
| nqh-bot-system-architecture.pdf | 4 MB | DOCUMENT | G2 evidence |
| ollama-integration-specs.yaml | 50 KB | CODE | G2 evidence |
| nlp-pipeline-design.pdf | 3 MB | DOCUMENT | G2 evidence |
| vietnamese-nlp-benchmark.xlsx | 200 KB | DATA | G2 evidence |
| owasp-security-baseline.pdf | 2 MB | DOCUMENT | G2 evidence |
| test-coverage-report.html | 500 KB | REPORT | G4 evidence |

---

## 7. Test Execution Checklist

### Pre-Test Setup

- [ ] Docker containers running (all healthy)
- [ ] PostgreSQL with seed data loaded
- [ ] MinIO buckets created (evidence-vault)
- [ ] OPA policies loaded
- [ ] Redis running
- [ ] Test accounts verified
- [ ] Test files prepared

### Test Execution Order

**Phase 1: Authentication (Critical Path)**
- [ ] TC-AUTH-001 to TC-AUTH-008

**Phase 2: Dashboard & Navigation**
- [ ] TC-DASH-001 to TC-DASH-005

**Phase 3: Project Management**
- [ ] TC-PROJ-001 to TC-PROJ-006

**Phase 4: Gate Management**
- [ ] TC-GATE-001 to TC-GATE-007

**Phase 5: Evidence Vault**
- [ ] TC-EVID-001 to TC-EVID-007

**Phase 6: Policy Management**
- [ ] TC-POL-001 to TC-POL-006

**Phase 7: AI Features**
- [ ] TC-AI-001 to TC-AI-004

**Phase 8: API Tests**
- [ ] TC-API-AUTH-* (4 tests)
- [ ] TC-API-PROJ-* (3 tests)
- [ ] TC-API-GATE-* (5 tests)
- [ ] TC-API-EVID-* (3 tests)
- [ ] TC-API-POL-* (2 tests)

**Phase 9: Performance Tests**
- [ ] TC-PERF-001 to TC-PERF-003

**Phase 10: Security Tests**
- [ ] TC-SEC-001 to TC-SEC-009

### Post-Test

- [ ] Test results documented
- [ ] Bugs logged in issue tracker
- [ ] Test coverage report generated
- [ ] Performance metrics captured
- [ ] Security findings reported

---

## 8. Appendix

### A. Test Environment Setup

```bash
# Start all containers
cd /path/to/SDLC-Orchestrator
docker-compose up -d

# Verify health
docker-compose ps

# Run Alembic migrations (includes seed data)
cd backend
PYTHONPATH=. python3 -m alembic upgrade head

# Or load seed data manually
psql -h localhost -U sdlc_user -d sdlc_orchestrator \
  -f docs/04-Testing-Quality/07-E2E-Testing/DEMO-SEED-DATA.sql

# Run E2E tests (Playwright)
cd frontend/web
npm run test:e2e
```

### B. Useful Commands

```bash
# Get fresh JWT token
TOKEN=$(curl -s -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@sdlc-orchestrator.io","password":"Admin@123"}' \
  | jq -r '.access_token')

# Test dashboard stats
curl -s http://localhost:8000/api/v1/dashboard/stats \
  -H "Authorization: Bearer $TOKEN" | jq

# Test projects list
curl -s http://localhost:8000/api/v1/projects \
  -H "Authorization: Bearer $TOKEN" | jq

# Test gates for a project
curl -s "http://localhost:8000/api/v1/gates?project_id=c0000000-0000-0000-0000-000000000001" \
  -H "Authorization: Bearer $TOKEN" | jq

# Verify evidence integrity
curl -s http://localhost:8000/api/v1/evidence/g0000000-0000-0000-0000-000000000001/verify \
  -H "Authorization: Bearer $TOKEN" | jq
```

### C. Production Test Environment

```bash
# Production local test (ports 8300/8310)
docker-compose -f docker-compose.production.yml --env-file .env.production.local up -d

# Test production API
TOKEN=$(curl -s -X POST http://localhost:8300/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@sdlc-orchestrator.io","password":"Admin@123"}' \
  | jq -r '.access_token')

curl -s http://localhost:8300/api/v1/dashboard/stats \
  -H "Authorization: Bearer $TOKEN" | jq
```

---

**Document Status**: ✅ ACTIVE - Ready for QA Testing
**Synchronized With**: DEMO-SEED-DATA.sql v3.0.0, Alembic migration a502ce0d23a7
**Test Project**: NQH-Bot Platform (CEO Tai Dang leads 2 teams using SDLC 5.1.3.1)
**Framework Reference**: docs/10-Archive/SDLC-Enterprise-Framework
**Next Review**: December 5, 2025
**Owner**: QA Lead + CTO
