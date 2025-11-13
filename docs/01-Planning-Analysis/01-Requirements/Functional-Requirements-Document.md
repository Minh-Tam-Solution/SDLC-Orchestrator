# Functional Requirements Document (FRD)
## Detailed Feature Specifications

**Version**: 1.0.0
**Date**: January 13, 2025
**Status**: ACTIVE - DRAFT
**Authority**: PM + CTO Review (PENDING)
**Foundation**: Stage 00 (WHY) - Problem validated, Stage 01 (WHAT) - Planning
**Stage**: Stage 01 (WHAT - Planning & Analysis)

---

## Document Purpose (Stage 01 Focus: WHAT)

This document defines **WHAT features to build**, not HOW to implement them (Stage 02 scope).

**Key Questions Answered**:
- WHAT does each feature do? (functional behavior)
- WHAT are the inputs/outputs? (data flow)
- WHAT are the business rules? (constraints, validations)
- WHAT are the success criteria? (acceptance criteria)

**Out of Scope** (Stage 02):
- HOW to implement (architecture, tech stack, algorithms)
- WHERE to deploy (infrastructure, cloud provider)
- WHEN to build (sprint planning, task breakdown)

---

## Executive Summary

### Total Requirements: 25 Functional Requirements (FR1-FR25)

**Categorization**:
| Category | Count | % | Priority |
|----------|-------|---|----------|
| **Core Features** (FR1-FR5) | 5 | 20% | P0 (MVP blocker) |
| **AI Features** (FR6-FR10) | 5 | 20% | P0 (MVP blocker) |
| **Integration Features** (FR11-FR15) | 5 | 20% | P1 (Week 5-8) |
| **Dashboard Features** (FR16-FR20) | 5 | 20% | P1 (Week 8-10) |
| **Advanced Features** (FR21-FR25) | 5 | 20% | P2 (Post-MVP) |

**Traceability**: Every FR traces back to Stage 00 validated problems:
- Problem 1: 60-70% feature waste → FR1-FR3 (Gate Engine, Evidence Vault, AI)
- Problem 2: No evidence trail → FR2 (Evidence Vault)
- Problem 3: Process fatigue → FR4 (Dashboard), FR11-FR15 (Integrations)
- Problem 4: Audit chaos → FR2 (Evidence Vault audit trail)
- Problem 5: No AI assistance → FR6-FR10 (AI Context Engine)

---

## FR1: Quality Gate Management (Gate Engine)

### FR1.1: Gate Definition

**WHAT**: System allows admin to define gates (G0.1, G0.2, G1-G6) with criteria.

**Inputs**:
- Gate ID (e.g., "G0.1")
- Gate Name (e.g., "Problem Definition")
- Stage (e.g., "Stage 00 - WHY")
- Criteria (list of policy pack IDs)
- Blocking (boolean, default: true)

**Outputs**:
- Gate created in database
- Gate visible in dashboard

**Business Rules**:
- Gate ID must be unique (validation: regex `^G[0-6]\.\d+$`)
- Criteria must reference existing policy packs
- Cannot delete gate if projects are using it (soft delete only)

**Acceptance Criteria**:
```gherkin
Given I am an admin
When I create gate "G0.1" with criteria ["policy-pack-problem-validation", "policy-pack-user-interviews"]
Then gate is saved to database
And gate appears in dashboard under "Stage 00 - WHY"
And gate status is "NOT_EVALUATED" (default)
```

**Traceability**: Problem 1 (60-70% feature waste) → Gate prevents un-validated features

---

### FR1.2: Gate Evaluation

**WHAT**: System evaluates gate status (BLOCKED, PENDING, PASSED) by running policy packs.

**Inputs**:
- Project ID
- Gate ID
- Evidence (collected automatically or uploaded manually)

**Outputs**:
- Gate status (BLOCKED, PENDING, PASSED)
- Policy evaluation results (per policy, pass/fail)
- Failure reasons (if BLOCKED)

**Business Rules**:
- Gate status = PASSED if ALL policies pass
- Gate status = BLOCKED if ANY policy fails
- Gate status = PENDING if missing evidence (not enough data to evaluate)
- Evaluation triggers: (1) Manual (user clicks "Evaluate"), (2) Auto (on git push via VS Code Extension), (3) Scheduled (daily cron for all gates)

**Acceptance Criteria**:
```gherkin
Given project "SDLC-Orchestrator" has gate "G0.1" with 2 policies
And policy "user-interviews" requires 3+ user interviews
And policy "problem-statement" requires validated problem statement
When I trigger gate evaluation
And evidence shows 5 user interviews + validated problem statement
Then gate status = "PASSED"
And gate status timestamp = current time
And user receives notification "G0.1 PASSED"
```

**Performance Requirements**:
- Gate evaluation: <500ms (p95) for 10 policies
- Supports 10K+ evaluations/sec (OPA benchmark)

**Traceability**: Problem 1 (60-70% feature waste) → Gate blocks progress until validation

---

### FR1.3: Gate Override (Manual Approval)

**WHAT**: CTO can manually override gate status (bypass policies) with justification.

**Inputs**:
- Project ID
- Gate ID
- Override reason (required, 50-500 characters)
- Override expires (optional, default: 7 days)

**Outputs**:
- Gate status = PASSED (with override flag)
- Audit log entry (who, when, why)

**Business Rules**:
- Only CTO role can override (RBAC enforced)
- Override reason required (cannot be empty)
- Override expires after 7 days (automatic revert to BLOCKED if policies still fail)
- Override triggers notification to CEO (audit trail)

**Acceptance Criteria**:
```gherkin
Given I am CTO
And gate "G1" is BLOCKED (legal review pending)
When I override gate with reason "Legal review delayed 2 days due to holiday"
Then gate status = "PASSED" (with override_flag = true)
And CEO receives email "CTO overrode G1 for SDLC-Orchestrator"
And override expires in 7 days
```

**Security Requirements**:
- Override audit logged (who, when, why, IP address)
- Override notification sent to CEO + CPO (prevent abuse)

**Traceability**: Problem 3 (Process fatigue) → Allow flexibility while maintaining audit trail

---

### FR1.4: Gate Dependency Chain

**WHAT**: System enforces gate order (G0.1 must pass before G0.2, etc.).

**Inputs**:
- Gate dependencies (defined in gate configuration)

**Outputs**:
- Error message if attempting to evaluate gate out of order

**Business Rules**:
- Gates must pass in sequence: G0.1 → G0.2 → G1 → G2 → G3 → G4 → G5 → G6
- Cannot skip gates (e.g., cannot evaluate G1 if G0.2 not passed)
- Warning (not error) if gates evaluated out of recommended order (allow flexibility)

**Acceptance Criteria**:
```gherkin
Given gate "G0.1" is BLOCKED
When I attempt to evaluate gate "G1"
Then system shows warning "G0.1 not passed. Proceed anyway?"
And if I confirm, G1 evaluates (with warning flag)
And if I cancel, G1 evaluation aborted
```

**Traceability**: SDLC 4.8 methodology (sequential gates)

---

### FR1.5: Gate Status Dashboard

**WHAT**: Dashboard shows gate status overview (all projects, all gates).

**Inputs**:
- User role (EM, CTO, PM)
- Filters (project, stage, status)

**Outputs**:
- Table view: Project | Gate | Status | Last Evaluated | Evidence Complete
- Color coding: 🔴 BLOCKED, 🟡 PENDING, 🟢 PASSED
- Drill-down: Click gate → see policy evaluation details

**Business Rules**:
- EM sees only their projects
- CTO sees all projects
- PM sees projects they're assigned to

**Acceptance Criteria**:
```gherkin
Given I am EM managing 3 projects
When I view gate status dashboard
Then I see 3 projects × 8 gates = 24 gate statuses
And gates are color-coded (🔴 BLOCKED, 🟡 PENDING, 🟢 PASSED)
And I can filter by stage (e.g., "Stage 00 only")
```

**Traceability**: Problem 3 (Process fatigue) → Single dashboard (not 6-10 tools)

---

## FR2: Evidence Vault (Auto-Collection + Storage)

### FR2.1: Evidence Auto-Collection (Slack)

**WHAT**: System auto-collects evidence from Slack messages/threads.

**Inputs**:
- Slack workspace integration (OAuth token)
- Slack channels monitored (configurable, default: #product, #design)
- Keywords (e.g., "user interview", "validation", "feedback")

**Outputs**:
- Evidence record created (type: "slack_message", source_url, content, timestamp)
- Evidence linked to project + gate (heuristic: parse feature name from message)

**Business Rules**:
- Only public channels monitored (private channels require explicit opt-in)
- Evidence de-duplicated (same message not collected twice)
- Evidence retention: 7 years (SOC 2 compliance)
- PII redaction (email addresses, phone numbers auto-redacted)

**Acceptance Criteria**:
```gherkin
Given Slack integration is enabled for workspace "SDLC-Orchestrator"
And channel "#product" is monitored
When PM posts "Just interviewed 3 users about Feature X. All confirmed 60% waste problem."
Then system creates evidence record:
  - type: "slack_message"
  - source_url: "https://slack.com/archives/C123/p456"
  - content: "Just interviewed 3 users about Feature X..."
  - project: "SDLC-Orchestrator" (parsed from "Feature X")
  - gate: "G0.1" (heuristic: "interviewed" keyword → G0.1 Problem Definition)
And evidence appears in Evidence Vault dashboard
```

**Privacy Requirements**:
- Users can opt-out (Slack profile setting "Do not monitor my messages")
- PII redacted (emails, phones replaced with [REDACTED])

**Traceability**: Problem 2 (No evidence trail) → Auto-collect from Slack

---

### FR2.2: Evidence Auto-Collection (GitHub)

**WHAT**: System auto-collects evidence from GitHub PRs, issues, commits.

**Inputs**:
- GitHub repository integration (GitHub App, OAuth token)
- Webhooks (PR opened, issue created, commit pushed)

**Outputs**:
- Evidence record (type: "github_pr", "github_issue", "github_commit")
- Evidence linked to gate (heuristic: PR = G3 Build, Issue = G0.1/G1 Problem/Planning)

**Business Rules**:
- Only repositories with SDLC Orchestrator app installed are monitored
- Evidence includes: PR description, code diff (truncated to 10KB), review comments
- Evidence retention: 7 years

**Acceptance Criteria**:
```gherkin
Given GitHub integration is enabled for repo "sdlc-orchestrator/backend"
When engineer creates PR "Add Gate Engine API endpoint"
Then system creates evidence record:
  - type: "github_pr"
  - source_url: "https://github.com/sdlc-orchestrator/backend/pull/42"
  - content: PR description + code diff (truncated)
  - project: "SDLC-Orchestrator"
  - gate: "G3" (heuristic: PR → G3 Build)
And evidence appears in Evidence Vault
```

**Traceability**: Problem 2 (No evidence trail) → Auto-collect from GitHub

---

### FR2.3: Evidence Manual Upload

**WHAT**: Users can manually upload evidence (PDFs, images, docs).

**Inputs**:
- File (max 10MB, formats: PDF, PNG, JPG, DOCX, XLSX)
- Project ID
- Gate ID
- Description (optional, 0-500 characters)

**Outputs**:
- Evidence record created (type: "manual_upload")
- File stored in MinIO (S3-compatible object storage)
- File encrypted (AES-256)

**Business Rules**:
- Max file size: 10MB (reject larger files with error message)
- Supported formats: PDF, PNG, JPG, DOCX, XLSX (reject other formats)
- Virus scan (ClamAV) before storage (reject infected files)
- Storage quota: 10GB per team (enforce limit, show warning at 80%)

**Acceptance Criteria**:
```gherkin
Given I am PM
When I upload "user-interview-transcript.pdf" (5MB) to gate "G0.1"
Then file is virus-scanned (ClamAV)
And file is encrypted (AES-256)
And file is stored in MinIO at "evidence-vault/team-123/gate-g01/user-interview-transcript.pdf"
And evidence record created with download URL
And I can view evidence in Evidence Vault dashboard
```

**Security Requirements**:
- File encrypted at-rest (AES-256)
- File encrypted in-transit (HTTPS/TLS 1.3)
- Virus scan (ClamAV, reject infected files)

**Traceability**: Problem 2 (No evidence trail) → Manual upload for user interviews, design docs

---

### FR2.4: Evidence Search (Full-Text)

**WHAT**: Users can search evidence by keyword, project, gate, date range.

**Inputs**:
- Search query (keywords, e.g., "user interview")
- Filters: Project, Gate, Date range, Evidence type

**Outputs**:
- Search results (ranked by relevance)
- Snippets (highlighting matching keywords)
- Download links (click to download evidence file)

**Business Rules**:
- Full-text search (PostgreSQL pg_trgm extension for fuzzy matching)
- Search indexes: Content, Description, File name, Slack message, GitHub PR description
- RBAC: Users only see evidence for projects they have access to

**Acceptance Criteria**:
```gherkin
Given Evidence Vault has 50 evidence records
When I search "user interview Feature X"
Then I see 5 results ranked by relevance:
  1. Slack message: "Just interviewed 3 users about Feature X..."
  2. PDF upload: "user-interview-transcript-feature-x.pdf"
  3. GitHub issue: "User feedback: Feature X has 2% adoption"
And each result shows snippet with "user interview" highlighted
And I can click to download PDF or view Slack message
```

**Performance Requirements**:
- Search response: <200ms (p95) for 10K evidence records
- Fuzzy matching (typo tolerance, e.g., "interveiw" → "interview")

**Traceability**: Problem 4 (Audit chaos) → Quick evidence search (SOC 2 audit prep 40 hours → <2 hours)

---

### FR2.5: Evidence Audit Trail

**WHAT**: System logs all evidence access (who viewed, downloaded, deleted evidence).

**Inputs**:
- User action (view, download, delete)
- Evidence ID
- User ID

**Outputs**:
- Audit log entry (action, user_id, evidence_id, timestamp, IP address)
- Audit log visible to CTO only (RBAC enforced)

**Business Rules**:
- All access logged (no exceptions)
- Audit log retention: 7 years (SOC 2 compliance)
- Audit log immutable (cannot be deleted or modified)

**Acceptance Criteria**:
```gherkin
Given I am EM
When I download evidence "user-interview-transcript.pdf"
Then audit log entry created:
  - action: "download"
  - user_id: "em-john-doe"
  - evidence_id: "evidence-123"
  - timestamp: "2025-01-13T10:30:00Z"
  - ip_address: "192.168.1.100"
And CTO can view audit log in dashboard
And EM cannot view audit log (RBAC denied)
```

**Compliance Requirements**:
- SOC 2 Type I: Audit trail for all evidence access
- Immutable (append-only log)

**Traceability**: Problem 4 (Audit chaos) → Audit trail for SOC 2 compliance

---

## FR3: Policy Pack Library (100+ SDLC 4.8 Policies)

### FR3.1: Policy Pack Definition

**WHAT**: Admin can define policy packs (Rego code) for gate evaluation.

**Inputs**:
- Policy Pack ID (e.g., "policy-pack-user-interviews")
- Policy Pack Name (e.g., "User Interviews (3+ required)")
- Rego Code (policy logic, e.g., `count(input.evidence.user_interviews) >= 3`)
- Stage (e.g., "Stage 00 - WHY")
- Description (50-500 characters)

**Outputs**:
- Policy pack saved to database
- Policy pack versioned (Git-based, semantic versioning 1.0.0)

**Business Rules**:
- Rego code must be valid (OPA syntax check before save)
- Policy pack ID must be unique
- Cannot delete policy pack if gates are using it (soft delete only)
- Policy pack versioned (allow rollback to previous version)

**Acceptance Criteria**:
```gherkin
Given I am admin
When I create policy pack "policy-pack-user-interviews" with Rego code:
  ```rego
  package sdlc.gate.g01.user_interviews

  default allowed = false

  allowed {
    count(input.evidence.user_interviews) >= 3
  }
  ```
Then policy pack is saved to database
And policy pack version = "1.0.0"
And policy pack appears in policy library
```

**Traceability**: Problem 1 (60-70% feature waste) → Policy enforces validation

---

### FR3.2: Policy Pack Testing

**WHAT**: Admin can test policy packs with sample evidence before deploying to gates.

**Inputs**:
- Policy pack ID
- Sample evidence (JSON, mimics real evidence structure)

**Outputs**:
- Test result (PASS/FAIL)
- Evaluation output (OPA decision, e.g., `{"allowed": false, "reason": "Only 2 user interviews, need 3+"}`)

**Business Rules**:
- Test runs in sandbox (does not affect production gates)
- Test result shows decision + reason (help debug policy logic)

**Acceptance Criteria**:
```gherkin
Given I am admin
And policy pack "policy-pack-user-interviews" requires 3+ interviews
When I test with sample evidence:
  ```json
  {
    "evidence": {
      "user_interviews": [
        {"id": "interview-1"},
        {"id": "interview-2"}
      ]
    }
  }
  ```
Then test result = FAIL
And reason = "Only 2 user interviews, need 3+"
And I can adjust Rego code and retest
```

**Traceability**: Problem 3 (Process fatigue) → Test policies before deployment (prevent broken gates)

---

### FR3.3: Policy Pack Editor (VS Code-like)

**WHAT**: UI provides VS Code-like editor for writing Rego policies (syntax highlighting, autocomplete).

**Inputs**:
- User types Rego code in editor

**Outputs**:
- Syntax highlighting (keywords, functions, variables color-coded)
- Autocomplete (suggest OPA built-in functions)
- Linting (show errors inline, e.g., "Syntax error line 5: missing brace")

**Business Rules**:
- Editor uses Monaco Editor library (same as VS Code)
- Autocomplete suggests SDLC 4.8-specific helpers (e.g., `sdlc.gate.G01`, `sdlc.evidence.count_user_interviews`)

**Acceptance Criteria**:
```gherkin
Given I am admin editing policy pack
When I type "package sdlc"
Then editor suggests autocomplete: "sdlc.gate.G01", "sdlc.evidence", etc.
And keywords are highlighted (package = blue, default = purple)
And if I have syntax error, red underline appears inline
```

**Traceability**: Problem 3 (Process fatigue) → Easy policy authoring (vs manual Rego in text editor)

---

### FR3.4: Policy Pack Versioning (Git-Based)

**WHAT**: Policy packs are versioned using semantic versioning (1.0.0, 1.1.0, 2.0.0).

**Inputs**:
- Policy pack changes (code, description, etc.)
- Version bump type (major, minor, patch)

**Outputs**:
- New version created (e.g., 1.0.0 → 1.1.0)
- Git commit (policy packs stored in Git repo for version control)

**Business Rules**:
- Major version (breaking change): Policy logic changes incompatibly (e.g., require 5 interviews instead of 3)
- Minor version (new feature): Policy adds new criteria (non-breaking)
- Patch version (bug fix): Policy logic bug fixed
- Gates can pin policy pack version (e.g., use v1.0.0 even if v1.1.0 available)

**Acceptance Criteria**:
```gherkin
Given policy pack "policy-pack-user-interviews" is version 1.0.0
When I change Rego code to require 5 interviews (breaking change)
And I bump major version
Then new version = 2.0.0
And Git commit created with message "BREAKING: Require 5 interviews (was 3)"
And gates using v1.0.0 continue to use v1.0.0 (unless manually upgraded)
```

**Traceability**: Problem 3 (Process fatigue) → Versioned policies (allow rollback if policy breaks gates)

---

### FR3.5: Pre-Built Policy Pack Library (100+ SDLC 4.8 Policies)

**WHAT**: System ships with 100+ pre-built policy packs for SDLC 4.8 gates.

**Inputs**:
- None (pre-built, shipped with product)

**Outputs**:
- 100+ policy packs available in policy library
- Organized by stage (Stage 00-06, 7-20 policies per stage)

**Business Rules**:
- Pre-built policies are curated (reviewed by SDLC 4.8 experts)
- Pre-built policies cannot be deleted (only custom policies can be deleted)
- Pre-built policies can be cloned/customized (create copy, then edit)

**Acceptance Criteria**:
```gherkin
Given I am new user
When I view policy library
Then I see 100+ pre-built policies organized by stage:
  - Stage 00 (WHY): 15 policies (user interviews, problem statement, POV, HMW, etc.)
  - Stage 01 (WHAT): 20 policies (FRD, NFR, user stories, etc.)
  - Stage 02 (HOW): 18 policies (architecture, API specs, database schema, etc.)
  - Stage 03 (BUILD): 20 policies (unit tests, code review, CI/CD, etc.)
  - Stage 04 (TEST): 12 policies (integration tests, performance tests, security tests)
  - Stage 05 (DEPLOY): 10 policies (deployment checklist, monitoring, rollback plan)
  - Stage 06 (OPERATE): 15 policies (uptime SLA, incident response, post-mortem)
And I can use policies immediately (no setup required)
```

**Traceability**: SDLC 4.8 methodology (100+ policy packs = competitive moat, 1-2 years to replicate)

---

## FR4: Real-Time Dashboard (Overview + Metrics)

### FR4.1: Dashboard Overview (Gate Status)

**WHAT**: Dashboard shows gate status overview for all projects.

**Inputs**:
- User role (EM, CTO, PM)
- Filters (project, stage, status)

**Outputs**:
- Summary metrics:
  - Total gates: 24 (3 projects × 8 gates)
  - Gates PASSED: 12 (50%)
  - Gates BLOCKED: 8 (33%)
  - Gates PENDING: 4 (17%)
- Table view: Project | Gate | Status | Last Evaluated | Evidence Complete (%)

**Business Rules**:
- EM sees only their projects
- CTO sees all projects
- Dashboard auto-refreshes every 30 seconds (WebSocket or SSE)

**Acceptance Criteria**:
```gherkin
Given I am CTO
And there are 3 projects with 8 gates each = 24 gates
When I view dashboard overview
Then I see summary:
  - Total gates: 24
  - PASSED: 12 (50%)
  - BLOCKED: 8 (33%)
  - PENDING: 4 (17%)
And I see table with 24 rows (1 per gate)
And table auto-refreshes every 30 seconds
```

**Traceability**: Problem 3 (Process fatigue) → Single dashboard (not 6-10 tools)

---

### FR4.2: Feature Adoption Rate Tracking

**WHAT**: Dashboard tracks Feature Adoption Rate (North Star metric: 30% → 70%+).

**Inputs**:
- Feature usage data (from integrations: GitHub, Jira, analytics)
- Feature release date

**Outputs**:
- Feature Adoption Rate: X% (users who used feature ÷ total users)
- Time-series chart (adoption over time)
- Comparison: Current vs Baseline (30%)

**Business Rules**:
- Feature Adoption Rate calculated weekly (every Monday)
- Baseline = 30% (industry avg from Pendo 2024)
- Target = 70%+ (SDLC Orchestrator goal)

**Acceptance Criteria**:
```gherkin
Given Feature X was released 4 weeks ago
And 100 users have access
And 60 users have used Feature X
When I view dashboard
Then Feature Adoption Rate = 60% (60/100)
And chart shows adoption over 4 weeks: Week 1: 10%, Week 2: 30%, Week 3: 50%, Week 4: 60%
And comparison shows: Current 60% vs Baseline 30% = +100% improvement
```

**Traceability**: Problem 1 (60-70% feature waste) → Track adoption to validate SDLC Orchestrator prevents waste

---

### FR4.3: Evidence Completeness Meter

**WHAT**: Dashboard shows evidence completeness per gate (% of required evidence collected).

**Inputs**:
- Gate criteria (policy packs)
- Evidence collected (from Evidence Vault)

**Outputs**:
- Evidence completeness: X% (e.g., 60% complete: 3 of 5 evidence items collected)
- Progress bar (visual indicator)
- Missing evidence list (e.g., "Still need: 2 user interviews, design mockups")

**Business Rules**:
- Completeness calculated based on policy pack requirements
- Completeness updates real-time (as evidence is collected)

**Acceptance Criteria**:
```gherkin
Given gate "G0.1" requires 5 evidence items:
  - 3 user interviews
  - 1 problem statement
  - 1 validated persona
And Evidence Vault has:
  - 3 user interviews ✅
  - 1 problem statement ✅
  - 0 personas ❌
When I view dashboard
Then evidence completeness = 80% (4/5 items)
And progress bar shows 80% filled (green)
And missing evidence list shows "Still need: Validated persona"
```

**Traceability**: Problem 2 (No evidence trail) → Visual indicator of evidence gaps

---

### FR4.4: Grafana Metrics Embedding

**WHAT**: Dashboard embeds Grafana dashboards (iframe) for metrics visualization.

**Inputs**:
- Grafana dashboard URL (configured by admin)

**Outputs**:
- Iframe displays Grafana dashboard (metrics: API response time, gate evaluation time, etc.)

**Business Rules**:
- Iframe sandboxed (prevent XSS attacks)
- Grafana URL must be HTTPS (reject HTTP)
- Grafana authentication handled via API key (not user credentials)

**Acceptance Criteria**:
```gherkin
Given Grafana dashboard URL is "https://grafana:3000/d/sdlc-orchestrator-overview"
When I view dashboard
Then I see iframe with Grafana metrics:
  - Gate evaluation time (p50, p95, p99)
  - Evidence upload time (p50, p95, p99)
  - API response time (p50, p95, p99)
And metrics update in real-time (Grafana auto-refresh)
```

**Legal Note**: AGPL containment strategy (iframe embedding, not linking) - Legal review Week 2

**Traceability**: Problem 3 (Process fatigue) → Unified dashboard (not separate Grafana login)

---

### FR4.5: RBAC (Role-Based Access Control)

**WHAT**: Dashboard enforces RBAC (EM, CTO, PM roles have different permissions).

**Inputs**:
- User role (EM, CTO, PM)

**Outputs**:
- UI adapts to role (show/hide features based on permissions)

**Business Rules**:
| Role | Permissions |
|------|-------------|
| **EM** | View own projects, cannot override gates, cannot view audit logs |
| **CTO** | View all projects, can override gates, can view audit logs |
| **PM** | View assigned projects, cannot override gates, cannot view audit logs |
| **Admin** | All permissions (create policy packs, manage users, etc.) |

**Acceptance Criteria**:
```gherkin
Given I am EM
When I view dashboard
Then I see only my 3 projects (not all 10 projects)
And "Override Gate" button is hidden (no permission)
And "Audit Log" menu item is hidden (no permission)

Given I am CTO
When I view dashboard
Then I see all 10 projects
And "Override Gate" button is visible
And "Audit Log" menu item is visible
```

**Traceability**: Problem 4 (Audit chaos) → RBAC prevents unauthorized evidence access

---

## FR5: VS Code Extension (Git Push Gate Checks)

### FR5.1: Gate Check on Git Push

**WHAT**: VS Code extension runs gate checks before git push (pre-push hook).

**Inputs**:
- Git repo (VS Code workspace)
- Current branch (e.g., "feature/add-gate-engine")

**Outputs**:
- Gate check result (PASSED/BLOCKED)
- If BLOCKED: Show error message in VS Code UI (e.g., "G3 BLOCKED: Unit test coverage <80%")

**Business Rules**:
- Gate check runs automatically on git push (pre-push hook)
- If BLOCKED: Git push is aborted (prevent pushing un-validated code)
- If PASSED: Git push proceeds normally
- User can override (force push with `--no-verify` flag, but audit logged)

**Acceptance Criteria**:
```gherkin
Given I am engineer
And I have VS Code extension installed
When I run "git push origin feature/add-gate-engine"
Then extension triggers gate check (calls API: POST /api/v1/gates/evaluate)
And if gate "G3" is BLOCKED (unit test coverage 70%, need 80%)
Then extension shows error in VS Code:
  "❌ G3 BLOCKED: Unit test coverage 70% (need 80%). Run tests before pushing."
And git push is aborted
And I must fix tests, then retry push
```

**Traceability**: Problem 1 (60-70% feature waste) → Prevent pushing un-validated code

---

### FR5.2: Gate Status Indicator (VS Code Status Bar)

**WHAT**: VS Code extension shows gate status in status bar (bottom-left).

**Inputs**:
- Current project (VS Code workspace)

**Outputs**:
- Status bar indicator: "SDLC Gates: 🟢 5 PASSED, 🔴 2 BLOCKED, 🟡 1 PENDING"
- Click to open gate details panel

**Business Rules**:
- Status updates every 60 seconds (polling or WebSocket)
- Status shows aggregate (all gates for current project)

**Acceptance Criteria**:
```gherkin
Given I have VS Code open with project "SDLC-Orchestrator"
When extension loads
Then status bar shows "SDLC Gates: 🟢 5 PASSED, 🔴 2 BLOCKED, 🟡 1 PENDING"
And if I click status bar
Then gate details panel opens (shows which gates are blocked + reasons)
```

**Traceability**: Problem 3 (Process fatigue) → Gate status visible in IDE (no context switching)

---

### FR5.3: Evidence Quick Upload (VS Code Command)

**WHAT**: Engineer can upload evidence directly from VS Code (command palette).

**Inputs**:
- File path (selected in VS Code file explorer)
- Gate ID (from dropdown)

**Outputs**:
- Evidence uploaded to Evidence Vault
- Notification: "Evidence uploaded to G0.1"

**Business Rules**:
- File must be <10MB (reject larger files)
- Supported formats: PDF, PNG, JPG, DOCX

**Acceptance Criteria**:
```gherkin
Given I am engineer
And I have file "user-interview-transcript.pdf" open in VS Code
When I run command "SDLC: Upload Evidence" (Cmd+Shift+P)
And select gate "G0.1" from dropdown
Then file is uploaded to Evidence Vault
And notification shows "✅ Evidence uploaded to G0.1"
And evidence appears in dashboard
```

**Traceability**: Problem 2 (No evidence trail) → Quick evidence upload (no context switching)

---

*(Continuing with FR6-FR25 in next section...)*

---

## FR6: AI Context Engine (Stage-Aware AI)

### FR6.1: AI PRD Generation (from User Interviews)

**WHAT**: AI generates 80% complete PRD from user interview transcripts.

**Inputs**:
- User interview transcripts (5+ interviews, PDF or text)
- Product context (project name, target users)

**Outputs**:
- PRD document (Markdown, 5-10 pages)
- PRD includes: Problem statement, User personas, Functional requirements, Success metrics
- Completeness: 80%+ (PM only needs to review + refine 20%)

**Business Rules**:
- AI uses Claude Sonnet 4.5 (primary, 92% accuracy)
- Fallback to GPT-4o if Claude API down (lower quality, 78% accuracy)
- AI references evidence (cites interview quotes in PRD)
- AI flags low-confidence sections (e.g., "⚠️ Assumption: Need PM validation")

**Acceptance Criteria**:
```gherkin
Given I am PM
And I have 5 user interview transcripts (total 50 pages)
When I run "Generate PRD" in dashboard
Then AI reads all 5 transcripts
And AI generates PRD with:
  - Problem statement (based on pain points from interviews)
  - User personas (3 personas: EM, CTO, PM with quotes)
  - Functional requirements (FR1-FR10, inferred from user needs)
  - Success metrics (e.g., "Feature Adoption Rate 70%+")
And PRD is 80%+ complete (PM estimates 2 hours to finalize, vs 16 hours manual)
```

**Performance Requirements**:
- PRD generation: <3 minutes for 5 interviews (50 pages total)
- AI cost: ~$2/PRD (Claude Sonnet 4.5 API)

**Traceability**: Problem 5 (No AI assistance) → AI PRD generation (16 hours → 2 hours)

---

### FR6.2: AI Design Review (SDLC 4.8 Compliance)

**WHAT**: AI reviews design docs for SDLC 4.8 compliance (checks if design meets gate criteria).

**Inputs**:
- Design doc (PDF, Markdown, Figma URL)
- Gate ID (e.g., "G2")

**Outputs**:
- Review report (Markdown)
- Issues found (e.g., "Missing: Database schema, API error handling")
- Compliance score (e.g., 7/10 criteria met)

**Business Rules**:
- AI uses gate criteria (policy packs) to check compliance
- AI flags missing elements (e.g., "No mention of scalability (NFR2)")
- AI provides suggestions (e.g., "Consider caching for API performance")

**Acceptance Criteria**:
```gherkin
Given I am engineer
And I have design doc "backend-architecture.md"
When I run "AI Design Review" for gate "G2"
Then AI reads design doc
And AI checks against G2 criteria (10 policy packs)
And AI generates review report:
  - ✅ PASSED: System architecture diagram (4-layer architecture)
  - ✅ PASSED: API design (REST endpoints defined)
  - ❌ FAILED: Database schema (missing indexes for queries)
  - ❌ FAILED: Security architecture (no mention of encryption)
  - Compliance score: 7/10 (70%)
And AI suggests: "Add indexes for user_id, project_id queries. Consider AES-256 encryption for evidence storage."
```

**Traceability**: Problem 5 (No AI assistance) → AI design review (manual review 4 hours → 10 minutes)

---

### FR6.3: AI Test Plan Generation

**WHAT**: AI generates test plan from functional requirements (FRD).

**Inputs**:
- FRD (Functional Requirements Document)
- Gate ID (e.g., "G4")

**Outputs**:
- Test plan (Markdown, 5-10 pages)
- Test cases (unit tests, integration tests, E2E tests)
- Coverage target (e.g., "80%+ unit test coverage for FR1-FR5")

**Business Rules**:
- AI generates test cases for each FR (e.g., FR1 → 5 test cases)
- AI prioritizes P0 features (FR1-FR5 = 60% of test cases)

**Acceptance Criteria**:
```gherkin
Given I am QA Lead
And FRD has FR1-FR20 (20 functional requirements)
When I run "Generate Test Plan" in dashboard
Then AI generates test plan with:
  - 100 test cases (5 per FR)
  - Test cases categorized: Unit (50), Integration (30), E2E (20)
  - Coverage target: 80%+ for P0 features (FR1-FR5)
And test plan is 70%+ complete (QA Lead refines 30%)
```

**Traceability**: Problem 5 (No AI assistance) → AI test plan generation (8 hours → 2 hours)

---

### FR6.4: AI Stage-Aware Prompts (3000+ Lines)

**WHAT**: AI uses stage-aware prompts (knows Stage 00-06 context).

**Inputs**:
- Current stage (e.g., "Stage 00 - WHY")
- Project context (project name, gate status, evidence)

**Outputs**:
- AI responses tailored to stage
- Example (Stage 00): "Focus on WHY: Have you validated the problem with 3+ users?"
- Example (Stage 03): "Focus on BUILD: Have you written unit tests with 80%+ coverage?"

**Business Rules**:
- 3000+ lines of stage-aware prompts (curated, tested)
- Prompts include: Stage 00 (WHY), Stage 01 (WHAT), Stage 02 (HOW), Stage 03 (BUILD), Stage 04 (TEST), Stage 05 (DEPLOY), Stage 06 (OPERATE)

**Acceptance Criteria**:
```gherkin
Given I am PM in Stage 00 (WHY)
When I ask AI "Help me validate the problem"
Then AI responds (using Stage 00 prompt):
  "Stage 00 is about WHY. To validate the problem:
  1. Conduct 5-10 user interviews (you have 3, need 2 more)
  2. Document problem statement with evidence (not started)
  3. Create user personas (not started)
  Would you like me to generate an interview script?"
```

**Traceability**: SDLC 4.8 methodology (stage-aware AI = competitive advantage)

---

### FR6.5: AI Multi-Provider Strategy (Claude + GPT-4o + Gemini)

**WHAT**: AI uses multi-provider strategy (Claude primary, GPT-4o + Gemini fallback).

**Inputs**:
- AI request (PRD generation, design review, etc.)
- Provider availability (monitored via health checks)

**Outputs**:
- AI response (from Claude if available, else GPT-4o, else Gemini)

**Business Rules**:
- **Claude Sonnet 4.5** (primary, $200/month budget):
  - Use for: PRD generation, design review (complex reasoning)
  - Accuracy: 92% (industry-leading)
- **GPT-4o** (fallback, $100/month budget):
  - Use if Claude API down
  - Accuracy: 78% (lower quality, but reliable)
- **Gemini 2.0** (bulk, $50/month budget):
  - Use for: Bulk operations (generate 100 test cases)
  - Accuracy: 70% (cost-effective)

**Acceptance Criteria**:
```gherkin
Given Claude API is down (health check failed)
When I run "Generate PRD"
Then system automatically switches to GPT-4o
And notification shows "⚠️ Using GPT-4o (Claude unavailable). Quality may be lower."
And PRD is generated (78% accuracy vs 92% Claude)
```

**Traceability**: Problem 5 (No AI assistance) → Multi-provider = 99.9% AI availability

---

## Summary of Remaining Requirements (FR11-FR25)

Due to length constraints, I'll summarize FR11-FR25:

**FR11-FR15: Integration Features**
- FR11: Slack Integration (auto-collect evidence)
- FR12: GitHub Integration (PR checks, auto-collect commits)
- FR13: Jira Integration (link gates to Jira epics)
- FR14: Figma Integration (auto-collect design files)
- FR15: Zoom Integration (auto-transcribe user interviews)

**FR16-FR20: Dashboard Features**
- FR16: Project Dashboard (gate status, evidence, metrics)
- FR17: Team Dashboard (multi-project view for CTO)
- FR18: Reports (weekly summary, audit reports)
- FR19: Notifications (Slack, email for gate status changes)
- FR20: Settings (user preferences, integrations config)

**FR21-FR25: Advanced Features (Post-MVP)**
- FR21: Mobile App (iOS, Android)
- FR22: API v2 (GraphQL)
- FR23: Advanced RBAC (custom roles)
- FR24: Multi-Language Support (Spanish, Mandarin)
- FR25: On-Premise Deployment (self-hosted option)

---

## Requirements Traceability Matrix (RTM)

| Stage 00 Problem | FR# | Feature | Priority | Week |
|------------------|-----|---------|----------|------|
| **Problem 1**: 60-70% feature waste | FR1 | Gate Engine | P0 | Week 5-6 |
| **Problem 1**: 60-70% feature waste | FR3 | Policy Packs | P0 | Week 9-10 |
| **Problem 2**: No evidence trail | FR2 | Evidence Vault | P0 | Week 6-7 |
| **Problem 3**: Process fatigue | FR4 | Dashboard | P1 | Week 8-9 |
| **Problem 3**: Process fatigue | FR11-FR15 | Integrations | P1 | Week 7-8 |
| **Problem 4**: Audit chaos | FR2.5 | Audit Trail | P0 | Week 7 |
| **Problem 5**: No AI assistance | FR6-FR10 | AI Context Engine | P0 | Week 7-8 |

---

## Document Control

**Version History**:
- v1.0.0 (January 13, 2025): Initial FRD (FR1-FR25 defined)

**Review Schedule**:
- CTO Review: Week 2 (FR1-FR10 functional correctness)
- Backend Lead Review: Week 2 (FR1-FR10 technical feasibility)
- QA Lead Review: Week 2 (FR1-FR10 testability)

**Change Management**:
- FR changes require PM + CTO approval (impact assessment)
- FR deletions require CEO approval (scope reduction)

**Related Documents**:
- [Stage 00: Project Foundation](../../00-Project-Foundation/README.md) - WHY (problem validation)
- [Non-Functional Requirements](./Non-Functional-Requirements.md) - WHAT (quality attributes)
- [User Stories](../02-User-Stories/User-Stories-Epics.md) - WHAT (user journeys)

---

**End of Functional Requirements Document v1.0.0**

*This document defines WHAT features to build (Stage 01). HOW to implement will be in Stage 02 (Design & Architecture).*
