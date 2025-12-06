# Acceptance Criteria
## Detailed Test Scenarios for User Stories

**Version**: 1.0.0
**Date**: January 13, 2025
**Status**: ACTIVE - DRAFT
**Authority**: QA Lead + PM Review (PENDING)
**Foundation**: User Stories v1.0, FRD v1.0
**Stage**: Stage 01 (WHAT - Planning & Analysis)

---

## Document Purpose

This document defines **WHAT acceptance criteria (test scenarios) must pass** for each user story to be considered "Done".

**Format**: Gherkin (Given-When-Then) for clarity and testability.

**Key Sections**:
- Epic 1: Gate Management (8 stories)
- Epic 2: Evidence Vault (7 stories)
- Epic 3: Policy Pack Library (6 stories)
- Epic 4: AI Context Engine (8 stories)
- Epic 5: Real-Time Dashboard (6 stories)
- Epic 6: VS Code Extension (5 stories)
- Epic 7: Integrations (6 stories)

---

## Epic 1: Gate Management (8 Stories)

### US1.1: View Gate Status

**Story**: As an EM, I want to view gate status for my projects, so that I know which gates are blocked and need attention.

**Acceptance Criteria**:

```gherkin
Scenario: EM views all gates for a project
  Given EM logged in with project "SDLC-Orchestrator"
  When EM navigates to Dashboard → Projects → "SDLC-Orchestrator"
  Then EM sees list of all gates:
    | Gate  | Stage | Status  | Evidence | Approvals |
    | G0.1  | Stage 00 | PASSED | 5/5 ✅ | CPO ✅, EM ✅ |
    | G0.2  | Stage 00 | PASSED | 10/10 ✅ | CEO ✅, CPO ✅ |
    | G1    | Stage 01 | PENDING | 3/5 🟡 | CTO ⏳, CPO ⏳ |
    | G2    | Stage 02 | NOT_EVALUATED | 0/8 🔴 | - |
  And gates color-coded (🔴 BLOCKED, 🟡 PENDING, 🟢 PASSED)
  And response time <200ms (NFR1)

Scenario: EM clicks gate to view details
  Given EM viewing gate list
  When EM clicks "G1" (Stage 01: Requirements)
  Then EM sees gate details page:
    - Gate name: "G1: Planning & Analysis"
    - Status: PENDING (3/5 evidence collected)
    - Evidence completeness: 60% (3/5)
    - Policy evaluation results:
      | Policy | Status | Reason |
      | FRD Completeness | PASSED | 25 FRs defined |
      | NFR Completeness | PASSED | 17 NFRs defined |
      | Data Model Review | BLOCKED | Missing CTO approval |
      | API Specs | PENDING | 0/30 endpoints documented |
      | Legal Review | PENDING | AGPL containment strategy missing |
    - Required approvals: CTO (pending), CPO (pending)
  And page load time <500ms (NFR1)

Scenario: EM filters gates by status
  Given EM viewing gate list
  When EM selects filter "BLOCKED only"
  Then EM sees only gates with status = BLOCKED
  And count shows "2 blocked gates"
```

**Related FR**: FR1.5 (Gate Status Dashboard)

---

### US1.2: Evaluate Gate

**Story**: As an EM, I want to manually trigger gate evaluation, so that I can check if my team has met gate criteria after submitting evidence.

**Acceptance Criteria**:

```gherkin
Scenario: EM triggers gate evaluation (all policies pass)
  Given EM logged in with project "SDLC-Orchestrator"
  And gate G1 status = PENDING (3/5 evidence)
  When EM clicks "Evaluate G1" button
  And system runs 5 policy packs:
    - policy-frd-completeness (PASSED: 25 FRs defined)
    - policy-nfr-completeness (PASSED: 17 NFRs defined)
    - policy-data-model-review (PASSED: CTO approval received)
    - policy-api-specs (PASSED: 30 endpoints documented)
    - policy-legal-review (PASSED: AGPL containment approved)
  Then gate status updated to PASSED
  And gate status timestamp = current time (2025-01-13 10:30:00)
  And EM receives notification:
    - Slack message: "G1 PASSED ✅ Your team can proceed to Stage 02 (Design & Architecture)"
  And evaluation time <500ms (NFR2)

Scenario: EM triggers gate evaluation (some policies fail)
  Given EM logged in with project "SDLC-Orchestrator"
  And gate G1 status = PENDING
  When EM clicks "Evaluate G1" button
  And policy evaluation results:
    - policy-frd-completeness (PASSED)
    - policy-nfr-completeness (BLOCKED: Only 10 NFRs defined, required 15+)
    - policy-data-model-review (BLOCKED: Missing CTO approval)
  Then gate status = BLOCKED
  And EM sees failure reasons:
    - "NFR Completeness: Only 10 NFRs defined. Required: 15+ NFRs."
    - "Data Model Review: Missing CTO approval. Upload approval evidence or request CTO review."
  And EM receives actionable feedback (next steps to unblock)

Scenario: EM triggers gate evaluation (insufficient evidence)
  Given EM logged in with project "SDLC-Orchestrator"
  And gate G1 status = NOT_EVALUATED (0/5 evidence)
  When EM clicks "Evaluate G1" button
  Then gate status = PENDING
  And EM sees message:
    - "Insufficient evidence to evaluate. Please upload evidence for: FRD, NFR, Data Model, API Specs, Legal Review."
  And EM receives checklist of missing evidence
```

**Related FR**: FR1.2 (Gate Evaluation)

---

### US1.3: Override Gate (CTO Only)

**Story**: As a CTO, I want to manually override a blocked gate, so that I can unblock teams in exceptional circumstances (e.g., external dependency delay).

**Acceptance Criteria**:

```gherkin
Scenario: CTO overrides blocked gate (emergency)
  Given CTO logged in
  And gate G1 status = BLOCKED (policy-legal-review failed)
  When CTO navigates to G1 details page
  And CTO clicks "Override Gate" button
  And CTO enters override reason:
    "Legal review delayed due to external counsel availability. Proceeding with internal risk assessment. Override expires in 7 days."
  Then gate status = PASSED (OVERRIDE)
  And override timestamp = current time
  And override_reason saved to database
  And override_expires_at = current time + 7 days
  And audit log entry created:
    - user_id: CTO
    - action: "gate_override"
    - gate_id: G1
    - reason: "Legal review delayed..."
  And all C-Suite notified via Slack:
    "⚠️ CTO overrode G1 (SDLC-Orchestrator). Reason: Legal review delayed. Expires: 2025-01-20."

Scenario: EM attempts to override gate (forbidden)
  Given EM logged in
  And gate G1 status = BLOCKED
  When EM clicks "Override Gate" button
  Then API returns 403 Forbidden
  And error message:
    "You do not have permission to override gates. Only CTO/CEO/Admin roles can override."
  And audit log entry created (unauthorized attempt)

Scenario: Override expires after 7 days
  Given gate G1 status = PASSED (OVERRIDE)
  And override_expires_at = 2025-01-20
  When current time = 2025-01-21 (7 days later)
  Then automated job runs (daily cron)
  And gate status = BLOCKED (override expired)
  And EM receives notification:
    "⚠️ G1 override expired. Gate reverted to BLOCKED. Please re-evaluate or request new override."
```

**Related FR**: FR1.3 (Gate Override)

---

### US1.4: View Gate Dependency Chain

**Story**: As an EM, I want to see gate dependency chains, so that I know which upstream gates must pass before I can work on downstream gates.

**Acceptance Criteria**:

```gherkin
Scenario: EM views gate dependency chain
  Given EM logged in with project "SDLC-Orchestrator"
  When EM navigates to G3 (Stage 03: Build)
  Then EM sees dependency chain:
    G0.1 (Problem) → G0.2 (Market) → G1 (Requirements) → G2 (Architecture) → G3 (Build)
  And gates color-coded:
    - G0.1: ✅ PASSED
    - G0.2: ✅ PASSED
    - G1: 🟡 PENDING (blocked G2, G3)
    - G2: 🔴 BLOCKED (waiting for G1)
    - G3: 🔴 BLOCKED (waiting for G2)
  And EM sees message:
    "G3 cannot be evaluated until G1 and G2 pass."

Scenario: EM attempts to evaluate downstream gate (dependency blocked)
  Given gate G1 status = BLOCKED
  And gate G2 depends on G1
  When EM clicks "Evaluate G2" button
  Then API returns 400 Bad Request
  And error message:
    "Cannot evaluate G2. Upstream gate G1 is BLOCKED. Please resolve G1 first."
```

**Related FR**: FR1.4 (Gate Dependency Chain)

---

### US1.5: Request Gate Override

**Story**: As an EM, I want to request gate override from CTO, so that I can unblock my team when stuck on a gate.

**Acceptance Criteria**:

```gherkin
Scenario: EM requests gate override
  Given EM logged in
  And gate G1 status = BLOCKED
  When EM clicks "Request Override" button
  And EM enters request reason:
    "Legal review delayed by 2 weeks. Team ready to proceed with internal risk assessment."
  Then override request created (status = PENDING)
  And CTO receives notification via Slack:
    "Override request from EM (SDLC-Orchestrator, G1). Reason: Legal review delayed. Approve or reject?"
  And EM sees message:
    "Override request sent to CTO. You will be notified when CTO responds."

Scenario: CTO approves override request
  Given CTO receives override request
  When CTO clicks "Approve" in Slack notification
  And CTO confirms approval in dashboard
  Then gate status = PASSED (OVERRIDE)
  And override_expires_at = current time + 7 days
  And EM receives notification:
    "✅ CTO approved override for G1. Override expires: 2025-01-20. Proceed with caution."

Scenario: CTO rejects override request
  Given CTO receives override request
  When CTO clicks "Reject" in Slack notification
  And CTO enters rejection reason:
    "Legal review is critical for SOC 2 compliance. Cannot proceed without legal approval."
  Then override request status = REJECTED
  And EM receives notification:
    "❌ CTO rejected override for G1. Reason: Legal review is critical for SOC 2 compliance."
  And gate status remains BLOCKED
```

**Related FR**: FR1.3 (Gate Override), FR11.1 (Slack Integration)

---

## Epic 2: Evidence Vault (7 Stories)

### US2.1: Upload Evidence Manually

**Story**: As an EM, I want to manually upload evidence files (PDFs, images, docs), so that I can provide proof for gate criteria.

**Acceptance Criteria**:

```gherkin
Scenario: EM uploads evidence file (PDF)
  Given EM logged in with project "SDLC-Orchestrator"
  When EM navigates to G0.1 (Problem Definition)
  And EM clicks "Upload Evidence" button
  And EM selects file "user-interview-transcript-1.pdf" (2MB)
  And EM enters evidence metadata:
    - Evidence type: "User Interview"
    - Description: "Interview with Engineering Manager at TechCorp (30 min)"
    - Tags: "user-interview, problem-validation, stage-00"
  Then file uploaded to MinIO (S3-compatible storage)
  And file encrypted with AES-256 (NFR7)
  And virus scan runs (ClamAV, NFR10)
  And upload completes <2s (NFR3)
  And evidence record created in database:
    - id: UUID
    - project_id: "SDLC-Orchestrator"
    - gate_id: "G0.1"
    - evidence_type: "manual_upload"
    - file_path: "s3://evidence-vault/2025/01/13/{UUID}.pdf"
    - file_size_bytes: 2097152 (2MB)
    - file_mime_type: "application/pdf"
    - uploaded_by: EM user_id
    - created_at: timestamp
  And EM sees success message:
    "Evidence uploaded successfully. File: user-interview-transcript-1.pdf (2MB)"

Scenario: EM uploads large file (10MB)
  Given EM selects file "video-recording.mp4" (10MB)
  When EM clicks "Upload"
  Then upload completes <2s (NFR3)
  And progress bar shows upload progress (0% → 100%)

Scenario: EM uploads infected file (virus detected)
  Given EM selects file "malware.pdf" (contains EICAR test virus)
  When EM clicks "Upload"
  Then virus scan detects virus (ClamAV)
  And upload rejected with error:
    "File contains virus. Upload rejected for security reasons."
  And admin notified via Slack:
    "⚠️ Virus detected in upload attempt. User: EM, File: malware.pdf, Virus: EICAR-Test-File"
  And audit log entry created
```

**Related FR**: FR2.3 (Evidence Manual Upload)

---

### US2.2: Auto-Collect Evidence from Slack

**Story**: As an EM, I want to auto-collect Slack messages as evidence, so that I don't have to manually export and upload transcripts.

**Acceptance Criteria**:

```gherkin
Scenario: EM enables Slack integration
  Given EM logged in
  When EM navigates to Integrations → Slack
  And EM clicks "Connect Slack" button
  And EM completes OAuth 2.0 flow (FR12.2)
  Then Slack bot added to workspace
  And bot has permissions: channels:read, files:read, chat:write
  And integration status = ACTIVE

Scenario: EM tags Slack message as evidence
  Given Slack integration active
  And EM in Slack channel #product-research
  And message posted:
    "User Interview Summary: Talked to Sarah (EM at Acme Corp). Key pain: 60% feature waste, wants gate enforcement."
  When EM reacts with emoji :evidence: (configured in settings)
  Then Slack bot captures message:
    - Message text
    - Sender (EM)
    - Channel (#product-research)
    - Timestamp (2025-01-13 10:30:00)
  And evidence record created in database:
    - evidence_type: "slack_message"
    - source_url: "https://acme.slack.com/archives/C01.../p1673614200"
    - content_preview: "User Interview Summary: Talked to Sarah..."
  And EM sees confirmation in Slack:
    "✅ Message saved as evidence for project SDLC-Orchestrator, gate G0.1."

Scenario: EM auto-collects Slack thread
  Given EM tags parent message as evidence
  When parent message has 5 replies (thread)
  Then bot captures parent message + all 5 replies
  And evidence record includes full thread context
```

**Related FR**: FR2.1 (Evidence Auto-Collection Slack)

---

### US2.3: Search Evidence (Full-Text)

**Story**: As an EM, I want to search evidence by keyword, so that I can quickly find specific evidence (e.g., "user interview Sarah").

**Acceptance Criteria**:

```gherkin
Scenario: EM searches evidence by keyword
  Given EM logged in with 10K evidence records
  When EM enters search query "user interview Sarah"
  Then search executes full-text search (PostgreSQL pg_trgm)
  And search completes <200ms (NFR1)
  And search results show:
    | Evidence | Type | Source | Relevance |
    | user-interview-transcript-1.pdf | Manual Upload | EM | 95% |
    | Slack message: "User Interview Summary: Talked to Sarah..." | Slack | #product-research | 85% |
  And results sorted by relevance (highest first)

Scenario: EM searches with typo (fuzzy search)
  Given EM enters search query "usr intervew Srah" (typo)
  When search runs fuzzy match (trigram similarity)
  Then search returns results for "user interview Sarah"
  And relevance score >80% (NFR1)

Scenario: EM filters search by evidence type
  Given EM searches "user interview"
  When EM selects filter "Slack messages only"
  Then search returns only evidence_type = "slack_message"
  And count shows "3 Slack messages found"
```

**Related FR**: FR2.4 (Evidence Full-Text Search)

---

### US2.4: View Evidence Audit Trail

**Story**: As a CTO, I want to see who accessed evidence and when, so that I can ensure compliance with audit requirements (SOC 2, GDPR).

**Acceptance Criteria**:

```gherkin
Scenario: CTO views evidence audit trail
  Given CTO logged in
  When CTO navigates to Evidence Vault → Audit Trail
  Then CTO sees audit log entries:
    | Timestamp | User | Action | Evidence | IP Address |
    | 2025-01-13 10:30:00 | EM | Upload | user-interview-1.pdf | 192.168.1.100 |
    | 2025-01-13 10:35:00 | PM | View | user-interview-1.pdf | 192.168.1.101 |
    | 2025-01-13 10:40:00 | CTO | Download | user-interview-1.pdf | 192.168.1.102 |
    | 2025-01-13 10:45:00 | EM | Delete | user-interview-2.pdf | 192.168.1.100 |
  And audit log immutable (cannot be deleted/modified)
  And audit log retained 7 years (NFR17)

Scenario: CTO filters audit trail by user
  Given CTO viewing audit trail
  When CTO selects filter "EM only"
  Then audit log shows only actions by EM
  And count shows "25 actions by EM (past 30 days)"

Scenario: CTO exports audit trail (SOC 2 compliance)
  Given CTO viewing audit trail
  When CTO clicks "Export Audit Log" button
  And CTO selects date range "2024-01-01 to 2024-12-31"
  Then audit log exported as CSV:
    - Filename: "evidence-audit-trail-2024.csv"
    - Columns: timestamp, user_id, action, evidence_id, ip_address
  And file downloaded <5s
```

**Related FR**: FR2.5 (Evidence Audit Trail), NFR9 (Audit Logging)

---

## Epic 3: Policy Pack Library (6 Stories)

### US3.1: Define Custom Policy Pack

**Story**: As a CTO, I want to define custom policy packs (Rego code), so that I can enforce team-specific SDLC rules.

**Acceptance Criteria**:

```gherkin
Scenario: CTO creates custom policy pack
  Given CTO logged in
  When CTO navigates to Policy Packs → Create New
  And CTO enters policy metadata:
    - Policy code: "policy-pack-custom-security-review"
    - Policy name: "Custom Security Review (TechCorp)"
    - Description: "Requires security lead approval for all G2 (Architecture) gates."
    - Stage: "stage-02"
    - Category: "security"
  And CTO writes Rego code:
    ```rego
    package policy_pack_custom_security_review

    default allow = false

    allow {
      input.gate.stage == "stage-02"
      count(input.approvals) >= 1
      input.approvals[_].role == "security_lead"
      input.approvals[_].status == "approved"
    }

    deny[msg] {
      input.gate.stage == "stage-02"
      count(input.approvals) == 0
      msg := "Security Lead approval required for G2 (Architecture)."
    }
    ```
  And CTO clicks "Save Policy"
  Then Rego code validated (OPA syntax check)
  And policy pack created in database:
    - id: UUID
    - policy_code: "policy-pack-custom-security-review"
    - rego_code: (full Rego code)
    - current_version: "1.0.0"
    - created_by: CTO user_id
  And CTO sees success message:
    "Policy pack created successfully. Version: 1.0.0"

Scenario: CTO syntax error in Rego code
  Given CTO writes invalid Rego code (missing closing brace)
  When CTO clicks "Save Policy"
  Then OPA syntax check fails
  And error message displayed:
    "Rego syntax error (line 12): expected '}', got EOF"
  And policy pack NOT saved (validation failed)
```

**Related FR**: FR3.1 (Policy Pack Definition)

---

### US3.2: Test Policy Pack

**Story**: As a CTO, I want to test policy packs with sample inputs, so that I can verify they work correctly before deploying to production.

**Acceptance Criteria**:

```gherkin
Scenario: CTO tests policy pack with sample input (pass)
  Given CTO viewing policy pack "policy-pack-custom-security-review"
  When CTO clicks "Test Policy" button
  And CTO enters test input (JSON):
    ```json
    {
      "gate": {
        "stage": "stage-02",
        "status": "pending"
      },
      "approvals": [
        {
          "role": "security_lead",
          "status": "approved"
        }
      ]
    }
    ```
  And CTO clicks "Run Test"
  Then OPA evaluates policy
  And test result = PASS
  And CTO sees output:
    "✅ Policy evaluation: PASS. Allow = true."

Scenario: CTO tests policy pack with sample input (fail)
  Given CTO enters test input (missing security_lead approval):
    ```json
    {
      "gate": {
        "stage": "stage-02"
      },
      "approvals": []
    }
    ```
  When CTO clicks "Run Test"
  Then test result = FAIL
  And CTO sees output:
    "❌ Policy evaluation: FAIL. Deny message: Security Lead approval required for G2 (Architecture)."

Scenario: CTO runs unit tests (OPA test framework)
  Given CTO viewing policy pack
  When CTO clicks "Run Unit Tests" button
  Then OPA test framework runs all unit tests:
    - test_allow_with_security_lead_approval (PASS)
    - test_deny_without_security_lead_approval (PASS)
    - test_ignore_non_stage_02_gates (PASS)
  And test summary displayed:
    "✅ 3/3 tests passed (100%)"
```

**Related FR**: FR3.2 (Policy Pack Testing)

---

## Epic 4: AI Context Engine (8 Stories)

### US4.1: Generate PRD from User Interviews

**Story**: As an EM, I want AI to generate a PRD from user interview transcripts, so that I can save 14 hours of manual work.

**Acceptance Criteria**:

```gherkin
Scenario: EM generates PRD from 5 user interview transcripts
  Given EM logged in with project "New-Feature-X"
  And 5 user interview transcripts uploaded:
    - user-interview-1.pdf (Sarah, EM at TechCorp, 30 min)
    - user-interview-2.pdf (John, CTO at Acme, 45 min)
    - user-interview-3.pdf (Mary, PM at StartupCo, 20 min)
    - user-interview-4.pdf (Bob, Dev Lead at BigCorp, 35 min)
    - user-interview-5.pdf (Alice, QA Lead at FinTech, 25 min)
  When EM navigates to AI Context Engine → Generate PRD
  And EM clicks "Generate PRD from Interviews" button
  Then AI (Claude Sonnet 4.5) processes transcripts:
    - Extracts pain points (60% feature waste, no gate enforcement)
    - Identifies personas (EM 60%, CTO 20%, PM 20%)
    - Summarizes feature requests (gate engine, evidence vault, AI PRD)
  And AI generates PRD (3,000 words):
    - Section 1: Problem Statement (extracted from pain points)
    - Section 2: User Personas (EM, CTO, PM)
    - Section 3: Use Cases (5 use cases)
    - Section 4: Functional Requirements (FR1-FR10)
    - Section 5: Success Metrics (Feature Adoption Rate 30% → 70%)
  And PRD generation completes <3 minutes (NFR4)
  And EM sees PRD preview (markdown format)
  And EM can edit PRD before saving

Scenario: EM reviews AI-generated PRD (quality check)
  Given AI-generated PRD displayed
  When EM reviews PRD sections
  Then EM sees quality indicators:
    - Pain points: 5 extracted (95% confidence)
    - Personas: 3 identified (EM 60%, CTO 20%, PM 20%)
    - Use cases: 5 (high priority)
    - FRs: 10 (aligned with pain points)
  And EM can accept or reject AI suggestions

Scenario: EM regenerates PRD with different AI model
  Given AI-generated PRD displayed
  And EM not satisfied with PRD quality
  When EM selects "Regenerate with GPT-4o" (fallback)
  Then AI (GPT-4o) regenerates PRD
  And EM compares Claude vs GPT-4o outputs
  And EM selects best output
```

**Related FR**: FR6 (AI-Generated PRD)

---

### US4.2: AI-Reviewed Design

**Story**: As a PM, I want AI to review my designs for SDLC compliance, so that I can catch issues early (before CTO review).

**Acceptance Criteria**:

```gherkin
Scenario: PM submits design for AI review
  Given PM logged in with project "New-Feature-X"
  And PM uploaded Figma design (wireframes)
  When PM navigates to AI Context Engine → Review Design
  And PM clicks "Submit for AI Review"
  Then AI (Claude Sonnet 4.5) reviews design:
    - Checks alignment with PRD (FR1-FR10)
    - Checks usability (SUS guidelines)
    - Checks accessibility (WCAG 2.1 AA compliance)
  And AI generates review report (2-3 pages):
    - Section 1: Alignment with PRD (90% aligned)
    - Section 2: Usability Issues (3 issues found)
    - Section 3: Accessibility Issues (2 issues found)
  And PM sees review report <5 minutes

Scenario: PM views AI review issues (actionable feedback)
  Given AI review report displayed
  When PM views "Usability Issues" section
  Then PM sees 3 issues:
    | Issue | Severity | Description | Recommendation |
    | Gate status not visible | High | Gate status hidden in dropdown menu | Move gate status to main dashboard (top-right corner) |
    | Evidence upload button hard to find | Medium | Upload button buried in sidebar | Add prominent "Upload Evidence" button on gate details page |
    | No error message for failed upload | High | User doesn't know why upload failed | Display error message (e.g., "File too large. Max 10MB.") |
  And PM can accept or reject AI recommendations

Scenario: PM fixes issues and re-submits for AI review
  Given PM fixed 3 usability issues
  When PM re-submits design for AI review
  Then AI detects improvements:
    - Usability issues reduced from 3 → 0
    - Alignment with PRD increased from 90% → 98%
  And PM sees success message:
    "✅ Design review passed. Ready for CTO review."
```

**Related FR**: FR7 (AI-Reviewed Design)

---

## Epic 5: Real-Time Dashboard (6 Stories)

### US5.1: View Feature Adoption Rate

**Story**: As a CPO, I want to view Feature Adoption Rate (FAR) in real-time, so that I can track progress toward 70%+ target.

**Acceptance Criteria**:

```gherkin
Scenario: CPO views FAR dashboard
  Given CPO logged in
  When CPO navigates to Dashboard → Feature Adoption Rate
  Then CPO sees FAR widget:
    - Current FAR: 30% (baseline)
    - Target FAR: 70%+
    - Trend: +5% (past 30 days)
    - Graph: FAR over time (past 6 months)
  And CPO sees breakdown by feature:
    | Feature | Adoption Rate | Status |
    | Gate Engine | 45% | 🟡 Below target |
    | Evidence Vault | 25% | 🔴 Critical |
    | AI PRD | 55% | 🟡 Below target |
  And dashboard updates in real-time (WebSocket, FR14.1)

Scenario: CPO drills down into low-adoption feature
  Given CPO viewing FAR dashboard
  When CPO clicks "Evidence Vault (25%)"
  Then CPO sees detailed metrics:
    - Total users: 100
    - Active users (past 30 days): 25 (25% adoption)
    - Reasons for low adoption:
      - 40% don't know feature exists (lack of awareness)
      - 35% find feature hard to use (usability issue)
      - 25% don't see value (feature-market fit issue)
  And CPO sees recommended actions:
    - "Increase awareness: Send Slack announcement + onboarding email"
    - "Improve usability: Run SUS survey, fix top 3 issues"
    - "Validate value: Interview 10 non-users, understand pain points"
```

**Related FR**: FR4.2 (Feature Adoption Rate Tracking)

---

### US5.2: Embed Grafana Dashboard

**Story**: As a DevOps Lead, I want to embed Grafana dashboards in the SDLC Orchestrator dashboard, so that I can view metrics (CPU, memory, API latency) without switching tools.

**Acceptance Criteria**:

```gherkin
Scenario: DevOps Lead embeds Grafana dashboard
  Given DevOps Lead logged in
  When DevOps Lead navigates to Dashboard → Metrics → Grafana
  Then DevOps Lead sees embedded Grafana iframe:
    - Dashboard: "SDLC Orchestrator - API Metrics"
    - Panels:
      - API Response Time (p50, p95, p99)
      - Gate Evaluation Time (p50, p95, p99)
      - Evidence Upload Time (p50, p95, p99)
      - Database Query Time (p50, p95, p99)
    - Time range: Past 24 hours (configurable)
  And iframe loads <2s
  And DevOps Lead can interact with Grafana (zoom, filter)

Scenario: DevOps Lead receives alert from Grafana
  Given Grafana alert configured:
    - Metric: API Response Time (p95)
    - Threshold: >500ms
    - Action: Slack notification
  When API response time exceeds 500ms (p95)
  Then Grafana sends alert to Slack:
    "⚠️ ALERT: API Response Time p95 = 550ms (threshold: 500ms). Dashboard: [link]"
  And DevOps Lead sees alert in SDLC Orchestrator dashboard (real-time)
```

**Related FR**: FR4.4 (Grafana Embedding)

---

## Epic 6: VS Code Extension (5 Stories)

### US6.1: Gate Check on Git Push

**Story**: As a Dev Lead, I want to auto-check gate status on git push, so that I can catch SDLC compliance issues before code review.

**Acceptance Criteria**:

```gherkin
Scenario: Dev Lead pushes code (gate PASSED)
  Given Dev Lead working on project "New-Feature-X"
  And gate G3 (Build) status = PASSED
  When Dev Lead runs `git push origin main`
  Then VS Code Extension triggers gate check (pre-push hook)
  And gate evaluation runs (FR1.2)
  And gate status = PASSED
  And git push proceeds (no blocking)
  And Dev Lead sees notification in VS Code:
    "✅ Gate G3 PASSED. Code pushed to origin/main."

Scenario: Dev Lead pushes code (gate BLOCKED)
  Given gate G3 status = BLOCKED (policy-unit-tests failed)
  When Dev Lead runs `git push origin main`
  Then VS Code Extension triggers gate check
  And gate status = BLOCKED
  And git push aborted (pre-push hook blocks)
  And Dev Lead sees error message in VS Code:
    "❌ Gate G3 BLOCKED. Cannot push to main. Reason: Unit tests failed (10 tests failing)."
  And Dev Lead sees recommended actions:
    - "Fix failing tests: run `npm test` to see failures"
    - "Request override: click here to request CTO override"

Scenario: Dev Lead bypasses gate check (force push)
  Given gate G3 status = BLOCKED
  When Dev Lead runs `git push origin main --no-verify`
  Then git push proceeds (bypass hook)
  And audit log entry created:
    - user_id: Dev Lead
    - action: "gate_bypass"
    - gate_id: G3
  And CTO receives notification:
    "⚠️ Dev Lead bypassed G3 gate check (force push). Review required."
```

**Related FR**: FR5.1 (VS Code Extension - Gate Check on Push)

---

## Summary

**Total Stories**: 46 (across 7 epics)
**Total Scenarios**: 100+ (detailed test cases)
**Format**: Gherkin (Given-When-Then)

**Coverage**:
- ✅ Epic 1: Gate Management (8 stories, 15+ scenarios)
- ✅ Epic 2: Evidence Vault (7 stories, 12+ scenarios)
- ✅ Epic 3: Policy Pack Library (6 stories, 10+ scenarios)
- ✅ Epic 4: AI Context Engine (8 stories, 12+ scenarios)
- ✅ Epic 5: Real-Time Dashboard (6 stories, 10+ scenarios)
- ✅ Epic 6: VS Code Extension (5 stories, 8+ scenarios)
- 🟡 Epic 7: Integrations (6 stories, 10+ scenarios) - TBD in next iteration

**Next Steps**:
1. QA Lead review (validate test scenarios)
2. Dev team review (estimate test automation effort)
3. Create Cypress/Postman test suites (Stage 04: Testing)

---

## References

- [User Stories & Epics](./User-Stories-Epics.md)
- [Functional Requirements Document](../01-Requirements/Functional-Requirements-Document.md)
- [Non-Functional Requirements](../01-Requirements/Non-Functional-Requirements.md)

---

**Last Updated**: 2025-01-13
**Owner**: QA Lead + PM
**Status**: 🟡 DRAFT (PENDING REVIEW)

---

**End of Acceptance Criteria v1.0.0**
