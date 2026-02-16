# Functional Requirements Document (FRD) - SDLC Orchestrator

**Version**: 3.2.0
**Date**: February 15, 2026
**Status**: ACTIVE - Governance Loop Completion (Sprint 173)
**Authority**: PM + CTO + CPO + Full Team Approved
**Foundation**: Product Vision 4.0.0, BRD 1.2.0, Stage 02 Architecture
**Framework**: SDLC 6.0.6 (7-Pillar + Section 7 Quality Assurance)

**Changelog v3.2.0** (Feb 15, 2026):
- **FR1 Enhancement**: Gate Governance Loop State Machine (ADR-053, Sprint 173)
  - 6-state lifecycle: DRAFT → EVALUATED → SUBMITTED → APPROVED (+ EVALUATED_STALE, REJECTED)
  - `compute_gate_actions()` shared function — SSOT for all permission checks
  - Server-driven capability discovery: `GET /gates/{id}/actions`
  - Separate reject endpoint: `POST /gates/{id}/reject` (CTO Mod 1)
  - Separated auth scopes: `governance:write` vs `governance:approve`
  - Redis-based idempotency (TTL 24h, response replay)
- **FR2 Enhancement**: Evidence Contract with server-side integrity
  - Server re-computes SHA256 on upload (`sha256_server`)
  - `criteria_snapshot_id` binds evidence to gate exit_criteria version
  - `source` field tracks upload origin (cli/extension/web/other)
  - Evidence upload while EVALUATED → EVALUATED_STALE (forces re-evaluation)
- **FR1 3-Client Parity**: All gate actions available via Web, CLI (sdlcctl), and VS Code Extension
  - CLI: 7 gate commands + evidence submit
  - Extension: approve/reject/evidence commands with optimistic UI
- References: ADR-053, CONTRACT-GOVERNANCE-LOOP.md, SPRINT-173-PLAN.md

**Changelog v3.1.0** (Dec 23, 2025):
- Updated FR41-FR45: Codegen Engine with Quality Gates + Validation Loop (CTO 10-point DoD)
- FR42: 4-Gate Quality Pipeline (Syntax → Security → Context → Tests)
- FR43: Validation Loop Orchestration (max_retries=3, deterministic feedback, escalation)
- FR44: Evidence State Machine (8 states, transition rules, locking)
- FR45: Codegen Integration Points (unified API, 3 modes, observability metrics)
- References: [Quality-Gates-Codegen-Specification.md](../../02-design/14-Technical-Specs/Quality-Gates-Codegen-Specification.md)

**Changelog v3.0.0** (Dec 21, 2025):
- Updated framework to SDLC 5.1.3
- Added FR22-FR30: AI Safety Layer requirements (EP-02)
- Added FR31-FR35: SDLC Structure Enforcement (EP-04)
- Added FR36-FR40: Enterprise Migration Engine (EP-05)
- Added FR41-FR45: Codegen Engine Tri-Mode (EP-06)
- Updated foundation references

**Changelog v2.1.0** (Dec 13, 2025):
- Added FR21: User API Key Management (BYOK) - CTO/CPO Approved

**Changelog v2.0.0** (Dec 3, 2025):
- Added FR6: Context-Aware Stage Requirements (ADR-011)
- Added FR7: AI Task Decomposition Service (ADR-012)
- Added FR8: 4-Level Planning Hierarchy (ADR-013)
- Added FR9: SDLC Structure Validator (ADR-014)

---

## Executive Summary

**Purpose**: Define WHAT the SDLC Orchestrator will build in Sprint 1-4 (November 14 - February 10, 2026).

**Scope**: Core functional requirements aligned with Product Vision MVP features + EP-06 Codegen:

### Core Platform (FR1-FR9)
1. **FR1: Quality Gate Management** - Policy-as-Code enforcement using OPA
2. **FR2: Evidence Vault** - Permanent audit trail with SHA256 integrity
3. **FR3: AI Context Engine** - Multi-provider stage-aware assistance
4. **FR4: Real-Time Dashboard** - Live gate status visualization
5. **FR5: Policy Pack Library** - Pre-built SDLC 5.1.3 policies
6. **FR6: Context-Aware Stage Requirements** - Dynamic MANDATORY/RECOMMENDED/OPTIONAL *(v2.0)*
7. **FR7: AI Task Decomposition** - User story → Tasks with CEO-level quality *(v2.0)*
8. **FR8: 4-Level Planning Hierarchy** - Roadmap → Phase → Sprint → Backlog *(v2.0)*
9. **FR9: SDLC Structure Validator** - Folder compliance enforcement *(v2.0)*
10. **FR21: User API Key Management** - BYOK for third-party AI providers *(v2.1)*

### EP-06 IR-Based Codegen Engine (FR41-FR45) *(v3.1 - Sprint 48 Quality Gates)*
11. **FR41: IR-Based Code Generation** - Multi-provider codegen from IR specifications
12. **FR42: 4-Gate Quality Pipeline** - Syntax → Security → Context → Tests validation
13. **FR43: Validation Loop Orchestration** - max_retries=3, deterministic feedback, escalation
14. **FR44: Evidence State Machine** - 8-state lifecycle (generated → merged/aborted)
15. **FR45: Codegen Integration Points** - Unified API, 3 modes, observability metrics

**Timeline**: Week 2 (Nov 21-25) - Detailed specs for Week 3-4 architecture design.

**Success Criteria**: All FRs approved → Gate G1 passage. EP-06 FRs require CTO 10-point DoD.

---

## FR1: Quality Gate Management

### Overview

**Capability**: Automated enforcement of SDLC 5.1.3 quality gates using Policy-as-Code (OPA).

**Business Value**: Prevent 70% feature waste by validating BEFORE building (Design Thinking gates).

**User Personas**:
- Engineering Manager: Ensure team meets quality standards
- CTO: Enforce governance without manual reviews
- Product Manager: Validate user needs before engineering starts

---

### FR1.1: Gate Orchestration Engine

#### Use Case 1.1.1: Create Quality Gate

**Actor**: Engineering Manager
**Precondition**: User authenticated, project exists
**Trigger**: User clicks "Create Gate" button

**Main Flow**:
1. User selects gate type (G0.1 Design Thinking, G1 Design Ready, G2 Build Ready, etc.)
2. System displays gate template with required evidence fields
3. User fills required metadata:
   - Gate name (e.g., "User Authentication - Gate G1")
   - Stage (WHY, WHAT, HOW, BUILD, TEST, DEPLOY, OPERATE)
   - Exit criteria (auto-populated from policy pack)
   - Approvers (CEO, CTO, CPO - role-based)
4. System creates gate record in PostgreSQL
5. System initializes evidence vault (empty, pending submission)
6. System displays gate status: "Draft" (not submitted for review)

**Postcondition**: Gate created with status "Draft", evidence vault initialized.

**Acceptance Criteria**:
- AC1: User can create gate in <5 seconds
- AC2: System validates required fields (name, stage, approvers)
- AC3: System auto-populates exit criteria from SDLC 5.1.3 policy pack
- AC4: System supports all 10 SDLC stages (WHY → GOVERN)
- AC5: System supports role-based approver selection (CEO, CTO, CPO, CIO, CFO)

**API Contract**:
```typescript
POST /api/v1/gates
Request:
{
  "name": "User Authentication - Gate G1 Design Ready",
  "stage": "WHAT",
  "gate_type": "G1_DESIGN_READY",
  "project_id": "uuid",
  "approvers": [
    {"role": "CTO", "user_id": "uuid"},
    {"role": "CPO", "user_id": "uuid"}
  ],
  "metadata": {
    "feature_name": "User Authentication",
    "priority": "P0",
    "target_sprint": 2
  }
}

Response (201 Created):
{
  "gate_id": "uuid",
  "name": "User Authentication - Gate G1 Design Ready",
  "status": "DRAFT",
  "stage": "WHAT",
  "gate_type": "G1_DESIGN_READY",
  "exit_criteria": [
    {"id": "G1-EC1", "description": "TDD test cases written BEFORE code", "required": true},
    {"id": "G1-EC2", "description": "API contracts documented (OpenAPI 3.0)", "required": true},
    {"id": "G1-EC3", "description": "Database schema designed (ERD + SQL)", "required": true}
  ],
  "evidence_vault_url": "/api/v1/gates/{gate_id}/evidence",
  "created_at": "2025-11-21T10:30:00Z"
}
```

**UI Mockup** (Figma reference):
- Modal dialog: "Create Quality Gate"
- Dropdown: Gate type (G0.1, G0.2, G1, G2... G9)
- Multi-select: Approvers (role + user)
- Auto-populated: Exit criteria checklist (from policy pack)

---

#### Use Case 1.1.2: Submit Gate for Review

**Actor**: Engineering Lead
**Precondition**: Gate in "Draft" status, all required evidence uploaded
**Trigger**: User clicks "Submit for Review" button

**Main Flow**:
1. User navigates to gate detail page
2. System displays evidence checklist (exit criteria vs uploaded evidence)
3. User reviews completeness:
   - Green checkmarks: Evidence uploaded + policy passed
   - Red X: Evidence missing OR policy failed
4. User clicks "Submit for Review"
5. System runs OPA policy validation:
   - Query: `data.sdlc.gates.g1.design_ready`
   - Input: All uploaded evidence + metadata
   - Output: Pass/Fail + policy violations
6. **IF** policy passes:
   - System updates gate status: "Draft" → "Pending Approval"
   - System sends notifications to approvers (Slack, email)
   - System locks evidence vault (no more uploads until decision)
7. **IF** policy fails:
   - System displays violations (e.g., "TDD tests missing", "API contract incomplete")
   - System keeps gate in "Draft" status
   - System allows user to fix and re-submit

**Postcondition**: Gate in "Pending Approval" status, approvers notified.

**Acceptance Criteria**:
- AC1: System validates ALL exit criteria before allowing submission
- AC2: System runs OPA policy check in <2 seconds (async for large evidence)
- AC3: System provides clear error messages for policy violations (with links to missing evidence)
- AC4: System locks evidence vault after submission (prevent tampering)
- AC5: System sends real-time notifications (Slack webhook, email)

**API Contract**:
```typescript
POST /api/v1/gates/{gate_id}/submit
Request: {} (no body, gate_id in URL)

Response (200 OK - Policy Passed):
{
  "gate_id": "uuid",
  "status": "PENDING_APPROVAL",
  "policy_result": {
    "decision": "PASS",
    "violations": [],
    "checked_at": "2025-11-21T11:00:00Z"
  },
  "approvers_notified": [
    {"role": "CTO", "user_id": "uuid", "notified_at": "2025-11-21T11:00:01Z"},
    {"role": "CPO", "user_id": "uuid", "notified_at": "2025-11-21T11:00:01Z"}
  ]
}

Response (400 Bad Request - Policy Failed):
{
  "error": "POLICY_VIOLATION",
  "gate_id": "uuid",
  "status": "DRAFT",
  "policy_result": {
    "decision": "FAIL",
    "violations": [
      {
        "code": "G1-EC1-MISSING",
        "message": "TDD test cases not found in evidence vault",
        "remediation": "Upload test cases to /evidence/tdd-tests/"
      },
      {
        "code": "G1-EC2-INCOMPLETE",
        "message": "API contract missing POST /api/users endpoint",
        "remediation": "Update OpenAPI spec with all CRUD endpoints"
      }
    ],
    "checked_at": "2025-11-21T11:00:00Z"
  }
}
```

**UI Mockup** (Figma reference):
- Evidence checklist: Green ✅ / Red ❌ for each exit criterion
- "Submit for Review" button (disabled if policy would fail)
- Policy violation banner (red alert with remediation links)

---

#### Use Case 1.1.3: Approve/Reject Gate

**Actor**: CTO (Approver)
**Precondition**: Gate in "Pending Approval" status
**Trigger**: Approver receives notification, clicks "Review Gate"

**Main Flow**:
1. Approver navigates to gate review page
2. System displays:
   - Gate metadata (name, stage, submitter, date)
   - Evidence summary (all uploaded files + policy results)
   - Exit criteria checklist (policy-validated)
   - Comments from other approvers (if multi-approval)
3. Approver reviews evidence:
   - Downloads evidence files (TDD tests, API contracts, etc.)
   - Reads AI-generated summary (Claude: "Gate summary in 3 bullet points")
   - Checks policy validation results (OPA decision log)
4. Approver makes decision:
   - **Approve**: Add comment (optional), click "Approve"
   - **Reject**: Add comment (required), click "Reject"
5. System updates gate approval record:
   - Records approver, decision, timestamp, comment
6. **IF** all approvers approved:
   - System updates gate status: "Pending Approval" → "Approved"
   - System unlocks next stage (e.g., G1 approved → BUILD stage enabled)
   - System sends notification to submitter (Slack, email)
7. **IF** any approver rejected:
   - System updates gate status: "Pending Approval" → "Rejected"
   - System unlocks evidence vault (allow re-submission)
   - System sends notification to submitter with rejection reasons

**Postcondition**: Gate approved/rejected, submitter notified, next stage enabled (if approved).

**Acceptance Criteria**:
- AC1: Approver can review evidence without leaving platform (inline file viewer)
- AC2: System requires comment for rejection (mandatory feedback)
- AC3: System supports multi-approval workflow (all approvers must approve)
- AC4: System prevents duplicate approvals (same user can't approve twice)
- AC5: System auto-unlocks next stage within 1 second of final approval

**API Contract**:
```typescript
POST /api/v1/gates/{gate_id}/approve
Request:
{
  "decision": "APPROVE", // or "REJECT"
  "comment": "API contracts look comprehensive. LGTM for BUILD phase.",
  "approver_id": "uuid"
}

Response (200 OK - All Approvers Approved):
{
  "gate_id": "uuid",
  "status": "APPROVED",
  "approvals": [
    {
      "approver_role": "CTO",
      "approver_id": "uuid",
      "decision": "APPROVE",
      "comment": "API contracts look comprehensive. LGTM for BUILD phase.",
      "approved_at": "2025-11-21T14:30:00Z"
    },
    {
      "approver_role": "CPO",
      "approver_id": "uuid",
      "decision": "APPROVE",
      "comment": "User validation evidence is strong. Go ahead.",
      "approved_at": "2025-11-21T14:35:00Z"
    }
  ],
  "next_stage_unlocked": "BUILD",
  "unlocked_at": "2025-11-21T14:35:01Z"
}

Response (200 OK - Partial Approval):
{
  "gate_id": "uuid",
  "status": "PENDING_APPROVAL",
  "approvals": [
    {
      "approver_role": "CTO",
      "approver_id": "uuid",
      "decision": "APPROVE",
      "comment": "API contracts look comprehensive. LGTM for BUILD phase.",
      "approved_at": "2025-11-21T14:30:00Z"
    }
  ],
  "pending_approvers": ["CPO"]
}

Response (200 OK - Rejection):
{
  "gate_id": "uuid",
  "status": "REJECTED",
  "approvals": [
    {
      "approver_role": "CTO",
      "approver_id": "uuid",
      "decision": "REJECT",
      "comment": "TDD test cases are incomplete. Missing edge cases for authentication failures.",
      "approved_at": "2025-11-21T14:30:00Z"
    }
  ],
  "evidence_vault_unlocked": true
}
```

**UI Mockup** (Figma reference):
- Split view: Evidence list (left) + Evidence viewer (right)
- Approve/Reject buttons (green/red, prominent)
- Comment textarea (required for rejection)
- Approval history timeline (show all approvers' decisions)

---

#### Use Case 1.1.4: Gate Capability Discovery (Sprint 173 — ADR-053)

**Actor**: Developer (CLI/Extension), Manager (Web UI)
**Precondition**: Gate exists, user authenticated with `governance:write` or `governance:approve` scope
**Trigger**: Client loads gate detail view / before executing gate action

**Main Flow**:
1. Client calls `GET /gates/{id}/actions`
2. Server evaluates `compute_gate_actions(gate, user)` — the SSOT function
3. Server returns available actions based on gate state + user scopes + evidence status
4. Client renders UI based on server response (buttons enabled/disabled with reasons)

**Postcondition**: Client displays only server-permitted actions. No client-side permission computation.

**SSOT Invariant**: The same `compute_gate_actions()` function is used by this endpoint AND all mutation endpoints (evaluate, submit, approve, reject). What `/actions` reports is exactly what mutations enforce.

**Acceptance Criteria**:
- AC1: Response includes `can_evaluate`, `can_submit`, `can_approve`, `can_reject`, `can_upload_evidence` booleans
- AC2: Response includes `reasons` dict explaining why any action is disabled
- AC3: Response includes `required_evidence`, `submitted_evidence`, `missing_evidence` lists
- AC4: All 3 clients (Web, CLI, Extension) call this before showing action UI
- AC5: Response latency <50ms (p95)

**API Contract**: See CONTRACT-GOVERNANCE-LOOP.md Section 3.1

---

#### Use Case 1.1.5: Gate State Machine Transitions (Sprint 173 — ADR-053)

**Actor**: System (server-side enforcement)
**Precondition**: Gate exists with valid status
**Trigger**: Any gate mutation (evaluate, submit, approve, reject, evidence upload)

**Gate States**: `DRAFT`, `EVALUATED`, `EVALUATED_STALE`, `SUBMITTED`, `APPROVED`, `REJECTED`

**Transition Rules**:
- `evaluate`: allowed from DRAFT, EVALUATED, EVALUATED_STALE, REJECTED → EVALUATED
- `submit`: allowed from EVALUATED only, requires `missing_evidence = []` → SUBMITTED
- `approve`: allowed from SUBMITTED only, requires `governance:approve` scope → APPROVED
- `reject`: allowed from SUBMITTED only, requires `governance:approve` scope → REJECTED
- `evidence_upload`: if gate is EVALUATED → side-effect: set to EVALUATED_STALE

**Auth Scopes**:
- `governance:write`: evaluate, submit, upload evidence
- `governance:approve`: approve, reject (separation of duties)

**Idempotency**: All mutations accept `X-Idempotency-Key` header. Duplicate requests return stored response body (Redis TTL 24h).

**Acceptance Criteria**:
- AC1: Invalid transitions return 409 Conflict with clear error message
- AC2: `submit` with missing evidence returns 422 with list of missing types
- AC3: Duplicate requests with same idempotency key return identical response
- AC4: REJECTED gates can be re-evaluated (iterative improvement path)
- AC5: Evidence upload while EVALUATED automatically sets EVALUATED_STALE

**API Contract**: See CONTRACT-GOVERNANCE-LOOP.md Sections 3.2-3.5

---

#### Use Case 1.1.6: Reject Gate with Re-evaluation Path (Sprint 173 — CTO Mod 2)

**Actor**: Manager/CTO (Approver)
**Precondition**: Gate in SUBMITTED status, user has `governance:approve` scope
**Trigger**: Approver clicks "Reject" with mandatory comment

**Main Flow**:
1. Approver calls `GET /gates/{id}/actions` — confirms `can_reject: true`
2. Approver provides rejection comment (required)
3. Client calls `POST /gates/{id}/reject` (separate endpoint — CTO Mod 1)
4. Server validates transition: SUBMITTED → REJECTED
5. Gate status updated, `rejected_at` set, comment stored
6. Submitter notified of rejection with comment
7. Submitter can re-evaluate (`POST /evaluate`) from REJECTED status
8. After fixes, submitter re-submits → approval cycle repeats

**Postcondition**: Gate rejected, submitter can iterate. No need to create a new gate.

**Acceptance Criteria**:
- AC1: Reject is a separate endpoint from approve (no `decision` field ambiguity)
- AC2: Comment is mandatory for rejection
- AC3: CLI uses `click.edit()` to open `$EDITOR` for long rejection comments
- AC4: Rejected gate can be re-evaluated without creating a new gate
- AC5: Full audit trail preserved (rejection + re-evaluation + re-approval)

---

### FR1.2: OPA Policy Engine Integration

#### Use Case 1.2.1: Validate Evidence Against Policy

**Actor**: System (automated)
**Precondition**: Evidence uploaded, gate submitted for review
**Trigger**: User clicks "Submit for Review" (triggers policy check)

**Main Flow**:
1. System collects all evidence from vault:
   - Files: TDD tests (Python), API contracts (OpenAPI YAML), ERD (PNG/PDF)
   - Metadata: File count, total size, SHA256 hashes
2. System prepares OPA input document:
   ```json
   {
     "gate": {
       "id": "uuid",
       "type": "G1_DESIGN_READY",
       "stage": "WHAT"
     },
     "evidence": {
       "tdd_tests": {
         "file_count": 5,
         "lines_of_code": 350,
         "test_coverage": 0, // Not applicable at design stage
         "sha256": "abc123..."
       },
       "api_contracts": {
         "file_path": "evidence/api-contracts.yaml",
         "endpoints_count": 12,
         "sha256": "def456..."
       },
       "database_schema": {
         "file_path": "evidence/schema.sql",
         "tables_count": 8,
         "sha256": "ghi789..."
       }
     }
   }
   ```
3. System queries OPA:
   - HTTP POST to `http://opa:8181/v1/data/sdlc/gates/g1/design_ready`
   - Input: Evidence document (JSON)
   - Timeout: 5 seconds (fail-safe if OPA unreachable)
4. OPA evaluates policy:
   ```rego
   package sdlc.gates.g1

   # Gate G1: Design Ready (WHAT Stage)
   design_ready = decision {
     decision := {
       "allowed": allowed,
       "violations": violations
     }
   }

   # Exit Criterion 1: TDD tests exist
   allowed {
     input.evidence.tdd_tests.file_count > 0
     input.evidence.tdd_tests.lines_of_code >= 100
   }

   # Exit Criterion 2: API contracts complete
   allowed {
     input.evidence.api_contracts.endpoints_count >= 5
   }

   # Exit Criterion 3: Database schema designed
   allowed {
     input.evidence.database_schema.tables_count > 0
   }

   # Collect violations
   violations[msg] {
     input.evidence.tdd_tests.file_count == 0
     msg := "G1-EC1-MISSING: TDD test cases not found"
   }
   ```
5. OPA returns decision:
   ```json
   {
     "result": {
       "allowed": false,
       "violations": ["G1-EC1-MISSING: TDD test cases not found"]
     }
   }
   ```
6. System processes OPA response:
   - **IF** `allowed == true`: Allow gate submission
   - **IF** `allowed == false`: Block submission, display violations

**Postcondition**: Policy decision recorded, gate status updated.

**Acceptance Criteria**:
- AC1: System evaluates policy within 2 seconds (95th percentile)
- AC2: System handles OPA timeout gracefully (default to "fail-safe" rejection)
- AC3: System logs all policy decisions to audit trail (PostgreSQL + MinIO)
- AC4: System supports 10+ gate types (G0.1, G0.2, G1... G9)
- AC5: System allows policy customization via Web UI (advanced feature, Week 6+)

**API Contract**:
```typescript
POST /api/v1/gates/{gate_id}/validate-policy
Request: {} // No body, uses gate_id to fetch evidence

Response (200 OK - Policy Passed):
{
  "gate_id": "uuid",
  "policy_result": {
    "decision": "PASS",
    "violations": [],
    "evaluated_at": "2025-11-21T11:00:00Z",
    "opa_version": "0.58.0",
    "policy_version": "sdlc-4.9-v1.0"
  }
}

Response (200 OK - Policy Failed):
{
  "gate_id": "uuid",
  "policy_result": {
    "decision": "FAIL",
    "violations": [
      {
        "code": "G1-EC1-MISSING",
        "message": "TDD test cases not found in evidence vault",
        "remediation": "Upload test cases to /evidence/tdd-tests/",
        "severity": "CRITICAL"
      }
    ],
    "evaluated_at": "2025-11-21T11:00:00Z",
    "opa_version": "0.58.0",
    "policy_version": "sdlc-4.9-v1.0"
  }
}

Response (503 Service Unavailable - OPA Timeout):
{
  "error": "OPA_TIMEOUT",
  "message": "Policy engine unreachable after 5 seconds",
  "fallback_decision": "FAIL",
  "retry_after": 60
}
```

**Infrastructure Requirements**:
- OPA container: `openpolicyagent/opa:0.58.0-rootless`
- Network: Backend → OPA via HTTP (docker-compose network)
- Policy storage: PostgreSQL (policy bundles table)
- Policy versioning: Git-based (policies/ directory)

---

### FR1.3: Stage Progression Control

#### Use Case 1.3.1: Unlock Next Stage After Gate Approval

**Actor**: System (automated)
**Precondition**: Gate approved by all required approvers
**Trigger**: Final approver clicks "Approve"

**Main Flow**:
1. System detects final approval (all approvers voted "APPROVE")
2. System looks up gate type → next stage mapping:
   - G0.1 (Design Thinking) → WHAT stage unlocked
   - G0.2 (Solution Diversity) → HOW stage unlocked
   - G1 (Design Ready) → BUILD stage unlocked
   - G2 (Build Ready) → TEST stage unlocked
   - G3 (Ship Ready) → DEPLOY stage unlocked
   - ... (all 10 stages)
3. System updates project stage:
   - `projects` table: `current_stage = 'BUILD'` (example)
   - `stage_history` table: Insert transition record (WHAT → BUILD)
4. System enables next stage features:
   - Creates GitHub branch: `build/feature-name`
   - Enables BUILD stage AI prompts (Claude context switch)
   - Shows BUILD stage checklist in dashboard
5. System sends notification:
   - Slack: "#engineering - Gate G1 APPROVED 🎉 BUILD stage unlocked"
   - Email: "Your gate was approved, you can start coding now"

**Postcondition**: Next stage unlocked, team can proceed.

**Acceptance Criteria**:
- AC1: System unlocks next stage within 1 second of final approval
- AC2: System prevents skipping stages (cannot go WHAT → DEPLOY without HOW/BUILD/TEST)
- AC3: System supports parallel stage work (advanced: multiple features in different stages)
- AC4: System tracks stage history (audit trail for compliance)
- AC5: System integrates with GitHub (auto-create branch for BUILD stage)

**API Contract**:
```typescript
POST /api/v1/projects/{project_id}/unlock-stage
Request:
{
  "gate_id": "uuid",
  "approved_stage": "WHAT",
  "next_stage": "BUILD"
}

Response (200 OK):
{
  "project_id": "uuid",
  "previous_stage": "WHAT",
  "current_stage": "BUILD",
  "unlocked_at": "2025-11-21T14:35:01Z",
  "github_branch_created": "build/user-authentication",
  "ai_context_updated": true,
  "notification_sent": true
}

Response (400 Bad Request - Stage Skip Detected):
{
  "error": "STAGE_SKIP_VIOLATION",
  "message": "Cannot unlock DEPLOY stage without passing TEST stage",
  "current_stage": "BUILD",
  "requested_stage": "DEPLOY",
  "missing_gates": ["G2_BUILD_READY", "G3_SHIP_READY"]
}
```

---

### FR1.4: Non-Functional Requirements

| Requirement | Target | Measurement |
|-------------|--------|-------------|
| **Performance** | Policy validation <2s (95th percentile) | Prometheus histogram |
| **Availability** | 99.5% uptime (OPA + Backend) | Uptime Robot |
| **Scalability** | 1,000 gates/day (10 teams × 100 gates) | Load testing (Locust) |
| **Security** | Role-based access (only approvers can approve) | RBAC enforcement |
| **Auditability** | 100% policy decisions logged (permanent) | PostgreSQL + MinIO |

---

## FR2: Evidence Vault

### Overview

**Capability**: Permanent audit trail with SHA256 integrity verification for all gate evidence.

**Business Value**: SOC 2 / ISO 27001 compliance - prove WHAT was approved and WHEN.

**User Personas**:
- CTO: Need permanent proof for auditors
- Compliance Officer: Export evidence for external audits
- Engineering Lead: Upload evidence (TDD tests, API contracts, runbooks)

---

### FR2.1: Evidence Upload and Storage

#### Use Case 2.1.1: Upload Evidence File

**Actor**: Engineering Lead
**Precondition**: Gate created (status: "Draft")
**Trigger**: User clicks "Upload Evidence" button

**Main Flow**:
1. User navigates to gate detail page → "Evidence" tab
2. System displays evidence checklist (from exit criteria):
   - G1 Design Ready:
     - ☐ TDD Test Cases (Python files)
     - ☐ API Contracts (OpenAPI YAML)
     - ☐ Database Schema (SQL + ERD)
3. User selects evidence type (dropdown: "TDD Test Cases")
4. User drags file or clicks "Browse" (multi-file upload supported)
5. System validates file:
   - Size: Max 100 MB per file
   - Type: Allowed extensions (.py, .yaml, .sql, .png, .pdf)
   - Virus scan: ClamAV (async, results in 5 seconds)
6. System computes SHA256 hash (client-side + server-side verification)
7. System uploads file to MinIO:
   - Bucket: `sdlc-evidence`
   - Path: `{project_id}/{gate_id}/{evidence_type}/{filename}`
   - Metadata: SHA256, uploader, timestamp
8. System records evidence in PostgreSQL:
   - Table: `gate_evidence`
   - Columns: `gate_id`, `evidence_type`, `file_path`, `sha256`, `uploaded_by`, `uploaded_at`
9. System displays upload success:
   - Green checkmark ✅ next to evidence type
   - File preview (inline for images/PDFs, download link for code)

**Postcondition**: Evidence uploaded, SHA256 recorded, checklist updated.

**Acceptance Criteria**:
- AC1: User can upload files up to 100 MB in <10 seconds (for 10 MB file)
- AC2: System computes SHA256 hash client-side + server-side (detect tampering)
- AC3: System prevents duplicate uploads (same SHA256 = reject)
- AC4: System supports multi-file upload (drag-and-drop 10 files at once)
- AC5: System scans files for viruses (ClamAV integration, async)

**API Contract**:
```typescript
POST /api/v1/gates/{gate_id}/evidence
Request (multipart/form-data):
{
  "evidence_type": "TDD_TESTS",
  "files": [File, File, ...], // Binary files
  "sha256_client": "abc123...", // Client-computed hash
  "metadata": {
    "description": "Unit tests for user authentication",
    "author": "Engineering Lead"
  }
}

Response (201 Created):
{
  "gate_id": "uuid",
  "evidence_id": "uuid",
  "evidence_type": "TDD_TESTS",
  "files": [
    {
      "filename": "test_auth.py",
      "file_path": "projects/uuid/gates/uuid/tdd-tests/test_auth.py",
      "size_bytes": 4096,
      "sha256_server": "abc123...",
      "sha256_match": true, // Client hash == Server hash
      "uploaded_at": "2025-11-21T10:45:00Z"
    }
  ],
  "minio_url": "http://minio:9000/sdlc-evidence/projects/uuid/gates/uuid/tdd-tests/test_auth.py"
}

Response (400 Bad Request - Hash Mismatch):
{
  "error": "SHA256_MISMATCH",
  "message": "Client-side hash (abc123) does not match server-side hash (def456)",
  "file": "test_auth.py",
  "client_sha256": "abc123...",
  "server_sha256": "def456..."
}

Response (400 Bad Request - Duplicate Evidence):
{
  "error": "DUPLICATE_EVIDENCE",
  "message": "File with same SHA256 already uploaded",
  "existing_evidence_id": "uuid",
  "uploaded_at": "2025-11-20T14:30:00Z"
}
```

**UI Mockup** (Figma reference):
- Drag-and-drop zone: "Drop files here or click to browse"
- Progress bar: Upload progress (for large files)
- File list: Uploaded files with SHA256 hash displayed (truncated)
- Preview panel: Inline viewer for images/PDFs

---

#### Use Case 2.1.2: Verify Evidence Integrity

**Actor**: CTO (Auditor)
**Precondition**: Evidence uploaded months ago
**Trigger**: Auditor wants to verify file was not tampered with

**Main Flow**:
1. Auditor navigates to gate detail page → "Evidence" tab
2. Auditor selects evidence file (e.g., "test_auth.py")
3. Auditor clicks "Verify Integrity" button
4. System re-downloads file from MinIO
5. System computes current SHA256 hash
6. System compares current hash vs original hash (from PostgreSQL):
   - **IF** hashes match: Display "✅ Integrity verified - File unchanged since upload"
   - **IF** hashes mismatch: Display "🔴 TAMPERING DETECTED - File modified after upload"
7. System logs verification attempt (audit trail):
   - `evidence_verifications` table: `evidence_id`, `verified_by`, `result`, `verified_at`

**Postcondition**: Integrity verified, verification logged.

**Acceptance Criteria**:
- AC1: System verifies integrity in <1 second (for 10 MB file)
- AC2: System detects tampering with 100% accuracy (SHA256 collision probability negligible)
- AC3: System logs all verification attempts (auditor accountability)
- AC4: System supports bulk verification (all evidence in gate)
- AC5: System displays verification history timeline

**API Contract**:
```typescript
POST /api/v1/evidence/{evidence_id}/verify
Request: {} // No body

Response (200 OK - Integrity Verified):
{
  "evidence_id": "uuid",
  "filename": "test_auth.py",
  "original_sha256": "abc123...",
  "current_sha256": "abc123...",
  "integrity_status": "VERIFIED",
  "verified_at": "2025-12-21T10:00:00Z",
  "verified_by": "uuid (CTO)"
}

Response (200 OK - Tampering Detected):
{
  "evidence_id": "uuid",
  "filename": "test_auth.py",
  "original_sha256": "abc123...",
  "current_sha256": "def456...", // DIFFERENT!
  "integrity_status": "TAMPERED",
  "verified_at": "2025-12-21T10:00:00Z",
  "verified_by": "uuid (CTO)",
  "alert_sent_to": ["security@company.com"]
}
```

---

### FR2.2: GitHub Artifact Auto-Collection

#### Use Case 2.2.1: Auto-Collect GitHub PR Evidence

**Actor**: System (automated)
**Precondition**: GitHub webhook configured, PR merged
**Trigger**: GitHub webhook: `pull_request.merged`

**Main Flow**:
1. GitHub sends webhook to backend:
   ```json
   {
     "action": "closed",
     "pull_request": {
       "merged": true,
       "number": 42,
       "title": "feat: Add user authentication",
       "html_url": "https://github.com/org/repo/pull/42",
       "merged_at": "2025-11-21T15:30:00Z",
       "base": {"ref": "main"},
       "head": {"ref": "build/user-auth"}
     }
   }
   ```
2. System extracts PR metadata:
   - PR number, title, author, reviewers
   - Commits (git log), files changed (diff)
   - CI/CD status (GitHub Actions results)
3. System looks up associated gate:
   - Searches `gates` table for `github_branch = 'build/user-auth'`
   - **IF** gate found: Auto-attach PR as evidence
4. System downloads PR artifacts:
   - PR description (markdown)
   - Code review comments (JSON)
   - CI/CD logs (GitHub Actions API)
5. System uploads artifacts to MinIO:
   - Bucket: `sdlc-evidence`
   - Path: `{project_id}/{gate_id}/github-pr-{number}/`
6. System records evidence in PostgreSQL:
   - Table: `gate_evidence`
   - Type: `GITHUB_PR`
   - Metadata: PR number, URL, merged_at

**Postcondition**: GitHub PR auto-attached to gate, evidence vault updated.

**Acceptance Criteria**:
- AC1: System processes webhook within 5 seconds of PR merge
- AC2: System auto-links PR to gate based on branch name convention
- AC3: System downloads PR artifacts (description, comments, CI logs)
- AC4: System handles webhook retries (idempotent, deduplicate by PR number)
- AC5: System supports GitHub Enterprise (configurable base URL)

**API Contract** (GitHub Webhook):
```typescript
POST /api/v1/webhooks/github/pull-request
Request (from GitHub):
{
  "action": "closed",
  "pull_request": {
    "merged": true,
    "number": 42,
    "html_url": "https://github.com/org/repo/pull/42"
  }
}

Response (200 OK):
{
  "webhook_id": "uuid",
  "processed": true,
  "gate_id": "uuid", // Auto-linked gate
  "evidence_created": {
    "evidence_id": "uuid",
    "evidence_type": "GITHUB_PR",
    "artifacts_collected": [
      "pr-description.md",
      "code-review-comments.json",
      "ci-logs.txt"
    ]
  }
}

Response (200 OK - No Gate Found):
{
  "webhook_id": "uuid",
  "processed": false,
  "reason": "No gate found for branch 'build/user-auth'",
  "action": "SKIPPED"
}
```

---

### FR2.3: Evidence Export for Compliance

#### Use Case 2.3.1: Export Gate Evidence Package

**Actor**: Compliance Officer
**Precondition**: Gate approved, evidence stored in vault
**Trigger**: User clicks "Export Evidence Package" button

**Main Flow**:
1. User navigates to gate detail page → "Evidence" tab
2. User clicks "Export Evidence Package"
3. System prompts for export format:
   - ZIP archive (all files + manifest.json)
   - PDF report (evidence summary + screenshots)
4. System generates evidence package:
   - Collects all files from MinIO
   - Generates manifest.json:
     ```json
     {
       "gate_id": "uuid",
       "gate_name": "User Authentication - Gate G1",
       "exported_at": "2025-12-15T10:00:00Z",
       "exported_by": "Compliance Officer",
       "evidence_files": [
         {
           "filename": "test_auth.py",
           "sha256": "abc123...",
           "uploaded_at": "2025-11-21T10:45:00Z"
         }
       ]
     }
     ```
   - Creates ZIP archive
5. System serves ZIP download (signed URL, expires in 1 hour)
6. System logs export activity (audit trail):
   - `evidence_exports` table: `gate_id`, `exported_by`, `format`, `exported_at`

**Postcondition**: Evidence package downloaded, export logged.

**Acceptance Criteria**:
- AC1: System generates ZIP in <10 seconds (for 100 MB evidence)
- AC2: System includes manifest.json with all SHA256 hashes
- AC3: System signs download URL (S3 presigned URL, expires in 1 hour)
- AC4: System logs all exports (who, when, what)
- AC5: System supports PDF report generation (evidence summary + thumbnails)

**API Contract**:
```typescript
POST /api/v1/gates/{gate_id}/export-evidence
Request:
{
  "format": "ZIP", // or "PDF"
  "include_artifacts": true // Include GitHub PR artifacts
}

Response (200 OK):
{
  "export_id": "uuid",
  "gate_id": "uuid",
  "format": "ZIP",
  "download_url": "https://minio:9000/exports/gate-uuid.zip?signature=xyz&expires=3600",
  "expires_at": "2025-11-21T16:00:00Z",
  "file_size_bytes": 10485760,
  "evidence_count": 12
}
```

---

### FR2.4: Non-Functional Requirements

| Requirement | Target | Measurement |
|-------------|--------|-------------|
| **Storage** | 1 TB total (MinIO) | Prometheus gauge |
| **Upload Speed** | 10 MB/s (100 MB file in 10s) | Upload latency |
| **Integrity** | 100% SHA256 verification | Verify all files monthly |
| **Retention** | Permanent (no auto-delete) | MinIO lifecycle policy |
| **Encryption** | AES-256 at rest (MinIO) | MinIO config |

---

## FR3: AI Context Engine

### Overview

**Capability**: Multi-provider stage-aware AI assistance (Claude, GPT-4o, Gemini).

**Business Value**: 10x faster evidence creation (AI drafts TDD tests, API contracts, runbooks).

**User Personas**:
- Engineering Lead: Generate TDD tests from user stories
- Product Manager: Draft Design Thinking artifacts (problem statement, personas)
- DevOps Engineer: Generate runbooks from architecture docs

---

### FR3.1: Stage-Aware Prompt Injection

#### Use Case 3.1.1: Generate TDD Tests (WHAT Stage)

**Actor**: Engineering Lead
**Precondition**: Gate G1 created (Design Ready stage), user story defined
**Trigger**: User clicks "AI: Generate TDD Tests" button

**Main Flow**:
1. User navigates to gate detail page → "Evidence" tab
2. User clicks "AI: Generate TDD Tests"
3. System displays AI prompt form:
   - Stage: WHAT (auto-detected from gate type)
   - Input: User story (textarea)
   - AI Provider: Claude Sonnet 4.5 (default for complex reasoning)
4. User enters user story:
   ```
   As a user, I want to log in with email + password,
   so that I can access protected resources.

   Acceptance Criteria:
   - Email validation (RFC 5322)
   - Password min 8 chars, 1 uppercase, 1 number
   - Max 3 failed attempts → account lockout
   ```
5. User clicks "Generate Tests"
6. System prepares AI prompt (stage-aware template):
   ```
   You are an expert software engineer following SDLC 5.1.3 Complete Lifecycle.

   CURRENT STAGE: WHAT (Design & Planning)
   GATE: G1 Design Ready
   EXIT CRITERIA: Write TDD test cases BEFORE writing implementation code.

   USER STORY:
   {user_story}

   TASK: Generate Python pytest test cases that validate ALL acceptance criteria.

   REQUIREMENTS:
   - Use pytest framework
   - Test ONLY external behavior (black-box testing)
   - Cover happy path + edge cases + error cases
   - Follow AAA pattern (Arrange, Act, Assert)
   - Include docstrings explaining WHAT is tested (not HOW)

   OUTPUT: Python code only (no explanations).
   ```
7. System calls Claude API:
   - Model: `claude-sonnet-4-5-20250929`
   - Temperature: 0.2 (deterministic for code)
   - Max tokens: 4096
8. Claude returns TDD tests:
   ```python
   import pytest
   from app.auth import login

   def test_login_success_valid_credentials():
       """User can log in with valid email and password."""
       # Arrange
       email = "user@example.com"
       password = "SecurePass123"

       # Act
       result = login(email, password)

       # Assert
       assert result.success is True
       assert result.access_token is not None

   def test_login_failure_invalid_email():
       """Login fails with invalid email format."""
       # Arrange
       email = "invalid-email"
       password = "SecurePass123"

       # Act
       result = login(email, password)

       # Assert
       assert result.success is False
       assert result.error == "INVALID_EMAIL_FORMAT"

   # ... (10 more test cases)
   ```
9. System displays generated tests in code editor (Monaco Editor)
10. User reviews tests:
    - Edit directly in browser
    - Click "Save as Evidence" to upload to vault
11. System uploads tests to MinIO (same as manual upload)

**Postcondition**: TDD tests generated, uploaded to evidence vault.

**Acceptance Criteria**:
- AC1: System generates tests in <10 seconds (95th percentile)
- AC2: System uses stage-aware prompts (WHAT stage = TDD tests, BUILD stage = implementation)
- AC3: System supports multi-provider fallback (Claude timeout → GPT-4o → Gemini)
- AC4: System tracks AI usage costs (tokens, $$ per gate)
- AC5: System allows manual editing before saving (inline code editor)

**API Contract**:
```typescript
POST /api/v1/gates/{gate_id}/ai/generate-evidence
Request:
{
  "evidence_type": "TDD_TESTS",
  "ai_provider": "CLAUDE", // or "GPT4", "GEMINI"
  "input": {
    "user_story": "As a user, I want to log in..."
  },
  "temperature": 0.2
}

Response (200 OK):
{
  "evidence_draft_id": "uuid",
  "evidence_type": "TDD_TESTS",
  "ai_provider": "CLAUDE",
  "model": "claude-sonnet-4-5",
  "generated_content": "import pytest\nfrom app.auth import login\n\n...",
  "tokens_used": 1250,
  "cost_usd": 0.025,
  "generated_at": "2025-11-21T11:15:00Z"
}

Response (429 Too Many Requests - Rate Limit):
{
  "error": "RATE_LIMIT_EXCEEDED",
  "ai_provider": "CLAUDE",
  "retry_after": 60,
  "fallback_providers": ["GPT4", "GEMINI"]
}
```

**UI Mockup** (Figma reference):
- Modal dialog: "AI Generate Evidence"
- Dropdown: AI Provider (Claude, GPT-4o, Gemini)
- Textarea: Input (user story, architecture doc, etc.)
- Code editor: Generated output (Monaco Editor)
- Buttons: "Regenerate", "Save as Evidence", "Cancel"

---

### FR3.2: Multi-Provider Routing

#### Use Case 3.2.1: Route Request to Best AI Provider

**Actor**: System (automated)
**Precondition**: User clicks "AI: Generate Evidence"
**Trigger**: AI request received

**Main Flow**:
1. System analyzes request context:
   - Stage: WHAT (complex reasoning needed)
   - Evidence type: TDD_TESTS (code generation)
   - Input length: 500 tokens
2. System applies routing logic:
   - **Claude Sonnet 4.5**: Complex reasoning (Design Thinking, TDD, runbooks)
   - **GPT-4o**: Code generation (implementation, unit tests)
   - **Gemini**: Bulk tasks (summarization, translation, low-cost)
3. System selects provider: Claude (complex reasoning for WHAT stage)
4. System checks rate limits:
   - Claude: 50 RPM (requests per minute)
   - Current usage: 10 RPM
   - **IF** under limit: Proceed
   - **IF** over limit: Fallback to GPT-4o
5. System calls selected provider API
6. System tracks usage:
   - Table: `ai_usage_logs`
   - Columns: `gate_id`, `provider`, `model`, `tokens`, `cost_usd`, `timestamp`

**Postcondition**: AI request routed to optimal provider, usage tracked.

**Acceptance Criteria**:
- AC1: System routes to correct provider based on stage + evidence type
- AC2: System falls back to alternate provider on rate limit (Claude → GPT-4o → Gemini)
- AC3: System tracks costs per gate (visible in dashboard)
- AC4: System respects monthly budget limit ($500/month for AI)
- AC5: System logs all AI requests (audit trail for compliance)

**Routing Rules** (Configurable):
```yaml
ai_routing:
  WHAT_STAGE:
    TDD_TESTS: CLAUDE # Complex reasoning
    API_CONTRACTS: GPT4 # Code generation
    DESIGN_THINKING: CLAUDE # Creative + reasoning

  BUILD_STAGE:
    IMPLEMENTATION: GPT4 # Code generation
    CODE_REVIEW: CLAUDE # Analysis

  OPERATE_STAGE:
    RUNBOOKS: CLAUDE # Complex instructions
    METRICS_QUERIES: GEMINI # Simple templating

  FALLBACK: GEMINI # Cheap fallback
```

---

### FR3.3: Cost Tracking and Budget Limits

#### Use Case 3.3.1: Track AI Costs Per Gate

**Actor**: System (automated)
**Precondition**: AI request completed
**Trigger**: AI provider returns response

**Main Flow**:
1. System receives AI response with token usage:
   ```json
   {
     "usage": {
       "prompt_tokens": 500,
       "completion_tokens": 750,
       "total_tokens": 1250
     }
   }
   ```
2. System looks up pricing (from config):
   - Claude Sonnet 4.5: $3/M input, $15/M output
   - GPT-4o: $5/M input, $15/M output
   - Gemini 2.0 Flash: $0.075/M input, $0.30/M output
3. System calculates cost:
   ```
   cost_usd = (prompt_tokens * input_price_per_1M) + (completion_tokens * output_price_per_1M)
   cost_usd = (500 * 3/1000000) + (750 * 15/1000000)
   cost_usd = 0.0015 + 0.01125 = 0.01275 (~$0.013)
   ```
4. System records cost:
   - Table: `ai_usage_logs`
   - Update gate aggregate: `gates.ai_cost_usd += 0.013`
5. System checks monthly budget:
   - Config: `AI_MONTHLY_BUDGET = $500`
   - Current month spend: `SUM(ai_cost_usd) WHERE month = 2025-11`
   - **IF** spend > budget: Send alert to CTO, block new AI requests

**Postcondition**: AI cost tracked, budget monitored.

**Acceptance Criteria**:
- AC1: System calculates cost accurately (within 1 cent)
- AC2: System aggregates costs by gate, project, month
- AC3: System alerts when 80% of monthly budget consumed
- AC4: System blocks AI requests when budget exceeded (fail-safe)
- AC5: System displays cost in dashboard (real-time)

**API Contract**:
```typescript
GET /api/v1/ai/usage-stats?month=2025-11
Response (200 OK):
{
  "month": "2025-11",
  "total_cost_usd": 125.45,
  "budget_usd": 500,
  "budget_used_percent": 25.09,
  "requests_count": 1250,
  "providers": {
    "CLAUDE": {"cost_usd": 85.20, "requests": 450},
    "GPT4": {"cost_usd": 30.15, "requests": 600},
    "GEMINI": {"cost_usd": 10.10, "requests": 200}
  },
  "top_gates": [
    {"gate_id": "uuid", "cost_usd": 15.30, "gate_name": "User Auth - G1"}
  ]
}
```

---

### FR3.4: Non-Functional Requirements

| Requirement | Target | Measurement |
|-------------|--------|-------------|
| **Latency** | AI response <10s (95th percentile) | Prometheus histogram |
| **Availability** | 99% (with multi-provider fallback) | Uptime monitoring |
| **Cost** | <$500/month (AI usage) | PostgreSQL cost tracking |
| **Rate Limits** | Handle 50 RPM per provider | Queue-based throttling |
| **Quality** | 90%+ user satisfaction (AI output) | User feedback (thumbs up/down) |

---

## FR4: Real-Time Dashboard

### Overview

**Capability**: Live visualization of gate status, stage progression, and team metrics.

**Business Value**: At-a-glance project health (are we on track for Feb 10 launch?).

**User Personas**:
- Engineering Manager: Monitor team velocity, gate pass rate
- CTO: Executive view (all projects, compliance status)
- Product Manager: Track feature progress (WHAT → BUILD → DEPLOY)

---

### FR4.1: Gate Status Dashboard

#### Use Case 4.1.1: View All Gates (Project Dashboard)

**Actor**: Engineering Manager
**Precondition**: User logged in, project selected
**Trigger**: User navigates to project dashboard

**Main Flow**:
1. User clicks "Dashboard" in navigation
2. System displays project overview:
   - Project name: "SDLC Orchestrator MVP"
   - Current stage: BUILD
   - Sprint: Week 6 of 13
   - Timeline: Nov 14 - Feb 10 (13 weeks)
3. System displays gates table (real-time):
   | Gate | Stage | Status | Approvers | Evidence | Created | Updated |
   |------|-------|--------|-----------|----------|---------|---------|
   | G0.1 Design Thinking | WHY | ✅ Approved | CEO, CPO | 3/3 files | Nov 14 | Nov 15 |
   | G0.2 Solution Diversity | WHY | ✅ Approved | CTO, CFO | 5/5 files | Nov 15 | Nov 18 |
   | G1 Design Ready | WHAT | ✅ Approved | CTO, CPO | 12/12 files | Nov 21 | Nov 25 |
   | G2 Build Ready | BUILD | 🟡 Pending | CTO | 8/10 files | Dec 12 | Dec 18 |
   | G3 Ship Ready | TEST | ⏳ Draft | - | 0/15 files | - | - |
4. System displays stage progression timeline:
   ```
   WHY ✅ → WHAT ✅ → HOW ✅ → BUILD 🟡 → TEST ⏳ → DEPLOY ⏳
   ```
5. System displays key metrics (cards):
   - Gate Pass Rate: 92% (11/12 gates passed on first attempt)
   - Avg Time to Approval: 2.3 days
   - Evidence Completeness: 87% (all gates)
   - AI Cost (Month): $125.45 / $500 budget

**Postcondition**: User sees real-time project status.

**Acceptance Criteria**:
- AC1: Dashboard loads in <2 seconds (all data)
- AC2: Dashboard updates real-time (WebSocket for gate status changes)
- AC3: Dashboard supports filtering (by stage, status, approver)
- AC4: Dashboard supports sorting (by created date, updated date)
- AC5: Dashboard exports to PDF (executive report)

**API Contract**:
```typescript
GET /api/v1/projects/{project_id}/dashboard
Response (200 OK):
{
  "project": {
    "id": "uuid",
    "name": "SDLC Orchestrator MVP",
    "current_stage": "BUILD",
    "sprint_week": 6,
    "timeline": {
      "start_date": "2025-11-14",
      "end_date": "2026-02-10",
      "total_weeks": 13
    }
  },
  "gates": [
    {
      "gate_id": "uuid",
      "name": "G0.1 Design Thinking",
      "stage": "WHY",
      "status": "APPROVED",
      "approvers": [
        {"role": "CEO", "approved_at": "2025-11-15T10:00:00Z"},
        {"role": "CPO", "approved_at": "2025-11-15T11:00:00Z"}
      ],
      "evidence_count": 3,
      "evidence_required": 3,
      "created_at": "2025-11-14T09:00:00Z",
      "updated_at": "2025-11-15T11:00:00Z"
    }
    // ... (12 gates total)
  ],
  "metrics": {
    "gate_pass_rate": 0.92,
    "avg_approval_days": 2.3,
    "evidence_completeness": 0.87,
    "ai_cost_month_usd": 125.45,
    "ai_budget_usd": 500
  }
}
```

**UI Mockup** (Figma reference):
- Header: Project name, current stage, sprint progress bar
- Table: Gates list (sortable, filterable)
- Timeline: Stage progression (visual roadmap)
- Metrics cards: 4 key metrics (gate pass rate, time to approval, evidence, AI cost)

---

### FR4.2: Real-Time Updates (WebSocket)

#### Use Case 4.2.1: Receive Real-Time Gate Status Updates

**Actor**: Engineering Manager
**Precondition**: Dashboard open in browser
**Trigger**: Gate status changes (e.g., approved by CTO)

**Main Flow**:
1. User opens dashboard, browser establishes WebSocket connection:
   ```
   ws://backend:8000/ws/projects/{project_id}/dashboard
   ```
2. Backend subscribes to Redis pub/sub channel:
   ```
   SUBSCRIBE project:{project_id}:gates:updates
   ```
3. Gate status changes (CTO approves Gate G2):
   - Backend updates PostgreSQL: `UPDATE gates SET status = 'APPROVED'`
   - Backend publishes event to Redis:
     ```json
     PUBLISH project:uuid:gates:updates {
       "event": "GATE_APPROVED",
       "gate_id": "uuid",
       "gate_name": "G2 Build Ready",
       "approved_by": "CTO",
       "approved_at": "2025-12-18T14:30:00Z"
     }
     ```
4. Backend receives Redis event, forwards via WebSocket to all connected clients
5. Frontend (React) receives WebSocket message:
   ```javascript
   ws.onmessage = (event) => {
     const update = JSON.parse(event.data)
     // Update gate table row (G2 status: Pending → Approved)
     updateGateStatus(update.gate_id, 'APPROVED')
     // Show toast notification: "Gate G2 approved by CTO 🎉"
     showToast(`Gate ${update.gate_name} approved by ${update.approved_by}`)
   }
   ```
6. Dashboard updates instantly (no page refresh needed)

**Postcondition**: Dashboard shows real-time updates.

**Acceptance Criteria**:
- AC1: WebSocket updates appear within 1 second of status change
- AC2: WebSocket reconnects automatically on disconnect (max 3 retries)
- AC3: WebSocket authenticates using JWT token (secure)
- AC4: WebSocket supports multiple concurrent clients (1,000+ connections)
- AC5: WebSocket falls back to HTTP polling if unavailable (graceful degradation)

**WebSocket Protocol**:
```typescript
// Client → Server (Subscribe)
{
  "action": "SUBSCRIBE",
  "channel": "project:uuid:gates:updates",
  "auth_token": "jwt_token_here"
}

// Server → Client (Event)
{
  "event": "GATE_APPROVED",
  "gate_id": "uuid",
  "gate_name": "G2 Build Ready",
  "approved_by": "CTO",
  "approved_at": "2025-12-18T14:30:00Z"
}

// Server → Client (Heartbeat, every 30s)
{
  "event": "PING",
  "timestamp": "2025-12-18T14:30:00Z"
}

// Client → Server (Heartbeat Response)
{
  "action": "PONG"
}
```

---

### FR4.3: Executive Summary Report

#### Use Case 4.3.1: Generate Executive PDF Report

**Actor**: CTO
**Precondition**: Project has gates created
**Trigger**: User clicks "Export Executive Report"

**Main Flow**:
1. User clicks "Export Executive Report" button (dashboard)
2. System prompts for report parameters:
   - Date range: Last 30 days (default: current month)
   - Include sections: Gates, Metrics, AI Usage, Compliance
3. User clicks "Generate PDF"
4. System collects data:
   - Gates: Status, approvals, evidence completeness
   - Metrics: Gate pass rate, time to approval, evidence stats
   - AI Usage: Costs, tokens, providers
   - Compliance: Evidence integrity checks, audit log
5. System generates PDF (using library: `reportlab` or `pdfkit`):
   - Page 1: Executive summary (1-page overview)
   - Page 2-5: Gate details (table + charts)
   - Page 6: Metrics dashboard (charts: gate pass rate trend, AI cost)
   - Page 7: Compliance status (evidence integrity, audit trail)
6. System serves PDF download (signed URL)

**Postcondition**: PDF report downloaded.

**Acceptance Criteria**:
- AC1: System generates PDF in <10 seconds (for 100 gates)
- AC2: PDF includes charts (gate pass rate trend, AI cost)
- AC3: PDF is branded (company logo, colors)
- AC4: PDF is printer-friendly (black & white mode)
- AC5: PDF includes footer (generated date, page numbers)

**API Contract**:
```typescript
POST /api/v1/projects/{project_id}/reports/executive
Request:
{
  "date_range": {
    "start_date": "2025-11-01",
    "end_date": "2025-11-30"
  },
  "sections": ["GATES", "METRICS", "AI_USAGE", "COMPLIANCE"]
}

Response (200 OK):
{
  "report_id": "uuid",
  "download_url": "https://minio:9000/reports/executive-2025-11.pdf?signature=xyz",
  "expires_at": "2025-11-21T17:00:00Z",
  "file_size_bytes": 2097152
}
```

---

### FR4.4: Non-Functional Requirements

| Requirement | Target | Measurement |
|-------------|--------|-------------|
| **Load Time** | Dashboard <2s (initial load) | Lighthouse performance |
| **Real-Time** | WebSocket updates <1s (latency) | Custom metric |
| **Scalability** | 1,000 concurrent WebSocket clients | Load testing |
| **Accessibility** | WCAG 2.1 AA compliance | axe DevTools |
| **Mobile** | Responsive (mobile, tablet, desktop) | Manual testing |

---

## FR5: Policy Pack Library

### Overview

**Capability**: Pre-built SDLC 5.1.3 policies for all 10 stages (100+ policies out-of-the-box).

**Business Value**: Zero policy authoring for 90% of teams (instant governance).

**User Personas**:
- Engineering Manager: Apply pre-built policies (G1, G2, G3)
- CTO: Customize policies for enterprise compliance
- DevOps Engineer: Deploy policies via GitOps

---

### FR5.1: Pre-Built Policy Catalog

#### Use Case 5.1.1: Browse Policy Catalog

**Actor**: Engineering Manager
**Precondition**: User logged in
**Trigger**: User navigates to "Policy Catalog"

**Main Flow**:
1. User clicks "Policy Catalog" in navigation
2. System displays policy categories:
   - **Stage 00 (WHY)**: Design Thinking policies (G0.1, G0.2)
   - **Stage 01 (WHAT)**: Planning & Analysis policies (G1)
   - **Stage 02 (HOW)**: Design & Architecture policies (G1)
   - **Stage 04 (BUILD)**: Development policies (G2)
   - **Stage 05 (TEST)**: Testing policies (G3)
   - **Stage 06 (DEPLOY)**: Deployment policies (G4)
   - **Stage 07 (OPERATE)**: Operations policies (G5)
   - **Stage 07-09**: Integration, Collaboration, Governance
3. User expands "Stage 04 (BUILD)" category
4. System displays policies:
   | Policy | Description | Gate | Severity |
   |--------|-------------|------|----------|
   | G2-Code-Review | 2+ reviewers required | G2 | CRITICAL |
   | G2-Test-Coverage | 90%+ test coverage | G2 | HIGH |
   | G2-No-TODOs | Zero TODO/FIXME in code | G2 | MEDIUM |
   | G2-Security-Scan | Snyk/SonarQube pass | G2 | CRITICAL |
5. User clicks "G2-Code-Review" policy
6. System displays policy details:
   - Description: "Pull requests require approval from 2+ reviewers"
   - Rego code (view-only):
     ```rego
     package sdlc.gates.g2.code_review

     violation[msg] {
       count(input.pull_request.reviewers) < 2
       msg := "G2-CODE-REVIEW-VIOLATION: Less than 2 reviewers"
     }
     ```
   - Test cases: 5 test scenarios (pass/fail examples)
   - Documentation: Link to SDLC 5.1.3 rationale

**Postcondition**: User understands available policies.

**Acceptance Criteria**:
- AC1: Catalog contains 100+ pre-built policies (all 10 stages)
- AC2: Each policy has description, Rego code, test cases, docs
- AC3: Policies are versioned (v1.0, v1.1, etc.)
- AC4: Policies support customization (parameters: min_reviewers = 2)
- AC5: Policies are searchable (keyword: "test coverage")

**API Contract**:
```typescript
GET /api/v1/policies/catalog
Response (200 OK):
{
  "categories": [
    {
      "stage": "BUILD",
      "stage_number": "03",
      "policies": [
        {
          "policy_id": "G2-CODE-REVIEW",
          "name": "Code Review Required",
          "description": "Pull requests require 2+ reviewers",
          "gate_type": "G2_BUILD_READY",
          "severity": "CRITICAL",
          "version": "1.0.0",
          "rego_file": "policies/g2-code-review.rego",
          "test_cases_count": 5,
          "documentation_url": "https://docs.sdlc.com/policies/g2-code-review"
        }
      ]
    }
  ],
  "total_policies": 105
}
```

**UI Mockup** (Figma reference):
- Sidebar: Stage categories (collapsible tree)
- Main panel: Policies table (sortable by severity, gate)
- Detail panel: Policy description + Rego code (syntax highlighted)

---

### FR5.2: Policy Customization

#### Use Case 5.2.1: Customize Policy Parameters

**Actor**: CTO
**Precondition**: Policy selected from catalog
**Trigger**: User clicks "Customize Policy"

**Main Flow**:
1. User selects "G2-Code-Review" policy from catalog
2. User clicks "Customize Policy"
3. System displays customization form:
   - Parameter: `min_reviewers` (default: 2)
   - Parameter: `require_codeowner_approval` (default: true)
   - Parameter: `allow_self_approval` (default: false)
4. User changes `min_reviewers` from 2 to 3 (enterprise requirement)
5. User clicks "Save Custom Policy"
6. System creates custom policy variant:
   - Name: "G2-Code-Review (Custom - 3 Reviewers)"
   - Rego code: Parameterized template
     ```rego
     package sdlc.gates.g2.code_review_custom

     min_reviewers := 3 # Custom parameter

     violation[msg] {
       count(input.pull_request.reviewers) < min_reviewers
       msg := sprintf("G2-CODE-REVIEW-VIOLATION: Less than %d reviewers", [min_reviewers])
     }
     ```
7. System saves custom policy to project:
   - Table: `custom_policies`
   - Columns: `project_id`, `base_policy_id`, `parameters`, `created_by`

**Postcondition**: Custom policy created, applied to project.

**Acceptance Criteria**:
- AC1: User can customize policy parameters (no Rego editing required)
- AC2: System validates parameters (min_reviewers >= 1)
- AC3: Custom policies inherit from base policy (version updates auto-applied)
- AC4: Custom policies are project-scoped (don't affect other projects)
- AC5: Custom policies support export (Rego file download)

**API Contract**:
```typescript
POST /api/v1/projects/{project_id}/policies/customize
Request:
{
  "base_policy_id": "G2-CODE-REVIEW",
  "custom_name": "G2-Code-Review (3 Reviewers)",
  "parameters": {
    "min_reviewers": 3,
    "require_codeowner_approval": true,
    "allow_self_approval": false
  }
}

Response (201 Created):
{
  "custom_policy_id": "uuid",
  "base_policy_id": "G2-CODE-REVIEW",
  "name": "G2-Code-Review (3 Reviewers)",
  "parameters": {
    "min_reviewers": 3,
    "require_codeowner_approval": true,
    "allow_self_approval": false
  },
  "rego_generated": true,
  "applied_to_gates": ["G2_BUILD_READY"]
}
```

---

### FR5.3: Policy Testing and Validation

#### Use Case 5.3.1: Test Policy Before Deployment

**Actor**: DevOps Engineer
**Precondition**: Custom policy created
**Trigger**: User clicks "Test Policy"

**Main Flow**:
1. User navigates to custom policy detail page
2. User clicks "Test Policy"
3. System displays test input form:
   - Sample input (JSON):
     ```json
     {
       "pull_request": {
         "reviewers": [
           {"username": "alice", "approved": true},
           {"username": "bob", "approved": true}
         ]
       }
     }
     ```
4. User modifies input (e.g., remove 1 reviewer to test violation)
5. User clicks "Run Test"
6. System evaluates policy against input:
   - HTTP POST to OPA: `http://opa:8181/v1/data/sdlc/gates/g2/code_review_custom`
   - Input: User-provided JSON
7. OPA returns result:
   ```json
   {
     "result": {
       "allowed": false,
       "violations": ["G2-CODE-REVIEW-VIOLATION: Less than 3 reviewers"]
     }
   }
   ```
8. System displays test result:
   - Status: ❌ FAIL (expected if testing violation)
   - Violations: "Less than 3 reviewers"
   - Recommendation: "Add 1 more reviewer to pass"

**Postcondition**: Policy tested, results displayed.

**Acceptance Criteria**:
- AC1: User can test policy with custom input (JSON editor)
- AC2: System displays test results in <1 second
- AC3: System provides pre-built test cases (pass/fail examples)
- AC4: System supports bulk testing (run 10 test cases at once)
- AC5: System saves test history (previous test runs)

**API Contract**:
```typescript
POST /api/v1/policies/{policy_id}/test
Request:
{
  "input": {
    "pull_request": {
      "reviewers": [
        {"username": "alice", "approved": true},
        {"username": "bob", "approved": true}
      ]
    }
  }
}

Response (200 OK):
{
  "policy_id": "uuid",
  "test_result": {
    "allowed": false,
    "violations": ["G2-CODE-REVIEW-VIOLATION: Less than 3 reviewers"],
    "evaluated_at": "2025-11-21T12:00:00Z"
  },
  "recommendation": "Add 1 more reviewer to pass policy"
}
```

---

### FR5.4: Policy Versioning and Updates

#### Use Case 5.4.1: Update Policy to New Version

**Actor**: System (automated)
**Precondition**: New policy version released (e.g., G2-Code-Review v1.1)
**Trigger**: Policy pack update deployed

**Main Flow**:
1. New policy pack version deployed to production:
   - Git tag: `policy-pack-v1.1.0`
   - Changes: G2-Code-Review now checks for approved vs requested reviews
2. System detects policy update:
   - Compares deployed version (v1.0) vs latest (v1.1)
3. System notifies affected projects:
   - Query: `SELECT * FROM custom_policies WHERE base_policy_id = 'G2-CODE-REVIEW'`
   - Send email to project owners: "Policy G2-Code-Review updated to v1.1"
4. System applies update strategy (configurable):
   - **Auto-update**: Custom policies inherit new version automatically
   - **Manual approval**: Project owner must approve update
5. **IF** auto-update enabled:
   - System regenerates custom policy Rego with new base version
   - System runs regression tests (all previous test cases must pass)
   - **IF** tests pass: Deploy new version
   - **IF** tests fail: Rollback, alert project owner
6. System logs policy update:
   - Table: `policy_update_history`
   - Columns: `policy_id`, `old_version`, `new_version`, `updated_at`, `status`

**Postcondition**: Policy updated to new version, backward compatibility maintained.

**Acceptance Criteria**:
- AC1: System supports policy versioning (v1.0, v1.1, v2.0)
- AC2: System auto-updates custom policies (configurable)
- AC3: System runs regression tests before deploying updates
- AC4: System rolls back on test failures (fail-safe)
- AC5: System notifies project owners of breaking changes

**API Contract**:
```typescript
POST /api/v1/policies/{policy_id}/update
Request:
{
  "target_version": "1.1.0",
  "update_strategy": "AUTO" // or "MANUAL"
}

Response (200 OK - Auto-Update Success):
{
  "policy_id": "uuid",
  "old_version": "1.0.0",
  "new_version": "1.1.0",
  "update_strategy": "AUTO",
  "regression_tests_passed": true,
  "updated_at": "2025-11-21T13:00:00Z"
}

Response (400 Bad Request - Regression Tests Failed):
{
  "error": "REGRESSION_TESTS_FAILED",
  "policy_id": "uuid",
  "old_version": "1.0.0",
  "new_version": "1.1.0",
  "failed_tests": [
    {"test_case": "Multiple reviewers approved", "expected": true, "actual": false}
  ],
  "rollback_performed": true
}
```

---

### FR5.5: Non-Functional Requirements

| Requirement | Target | Measurement |
|-------------|--------|-------------|
| **Policy Count** | 100+ pre-built policies (all stages) | Catalog size |
| **Customization** | 90%+ policies customizable (parameters) | Policy metadata |
| **Testing** | 100% policies have test cases (5+ each) | Test coverage |
| **Versioning** | Semantic versioning (v1.0.0) | Git tags |
| **Documentation** | 100% policies documented (rationale) | Docs coverage |

---

## Cross-Functional Requirements (CFR)

### CFR1: Security

**Requirement**: All API endpoints require JWT authentication (1h access, 30d refresh).

**Implementation**:
- FastAPI dependency: `Depends(get_current_user)`
- JWT validation: Verify signature, expiry, role
- RBAC: CEO/CTO/CPO roles enforced (approver permissions)

**Acceptance Criteria**:
- AC1: Unauthenticated requests return 401 Unauthorized
- AC2: Expired tokens return 401 (with refresh hint)
- AC3: Role violations return 403 Forbidden (e.g., PM trying to approve gate)
- AC4: JWT tokens stored in httpOnly cookies (XSS protection)
- AC5: Refresh tokens rotate on use (security best practice)

---

### CFR2: Performance

**Requirement**: API response time <200ms (p95) for all read endpoints.

**Implementation**:
- PostgreSQL indexes: `gates(project_id, status)`, `evidence(gate_id)`
- Redis cache: Gate status, project metadata (TTL: 5 minutes)
- Database connection pooling: SQLAlchemy pool (min: 5, max: 20)

**Acceptance Criteria**:
- AC1: `/api/v1/projects/{id}/dashboard` responds in <200ms (p95)
- AC2: `/api/v1/gates/{id}` responds in <100ms (p95)
- AC3: Database queries use indexes (no full table scans)
- AC4: Redis cache hit rate >80% (for dashboard)
- AC5: Load test: 100 RPS sustained for 5 minutes (no errors)

---

### CFR3: Observability

**Requirement**: All API requests logged, metrics exported to Grafana.

**Implementation**:
- Structured logging: `structlog` (JSON format)
- Metrics: Prometheus client (request latency, error rate, gate status)
- Tracing: OpenTelemetry (distributed tracing for multi-service requests)
- Dashboards: Grafana (API latency, error rate, gate pass rate)

**Acceptance Criteria**:
- AC1: All API requests logged with request_id, user_id, endpoint, latency
- AC2: Prometheus metrics exported at `/metrics` endpoint
- AC3: Grafana dashboard shows API latency (p50, p95, p99)
- AC4: Alert: API error rate >1% (send to #engineering Slack)
- AC5: Tracing: End-to-end trace for gate submission (backend → OPA → MinIO)

---

### CFR4: Data Retention

**Requirement**: Evidence stored permanently (no auto-delete), compliance with SOC 2.

**Implementation**:
- MinIO lifecycle policy: No expiration (permanent storage)
- PostgreSQL: Soft delete for gates (mark as deleted, keep data)
- Backup: Daily PostgreSQL dump to MinIO (retention: 90 days)

**Acceptance Criteria**:
- AC1: Evidence files never auto-deleted (permanent storage)
- AC2: Deleted gates retain data for audit (soft delete with `deleted_at` timestamp)
- AC3: Database backups run daily (automated via cron)
- AC4: Backup restoration tested quarterly (disaster recovery drill)
- AC5: Compliance: Evidence integrity verified monthly (bulk SHA256 check)

---

## Acceptance Criteria Summary

### Gate G1 Passage Criteria (Friday, Nov 25, 2025)

**Required for G1 approval**:
1. ✅ All 9 functional requirements documented (FR1-FR9)
2. ✅ API contracts defined for all use cases (20+ endpoints)
3. ✅ UI mockups referenced (Figma links)
4. ✅ Non-functional requirements specified (performance, security, observability)
5. ✅ Cross-functional requirements documented (CFR1-CFR4)

**Stakeholder Approvals**:
- PM: Functional requirements complete
- CTO: Technical feasibility validated
- CPO: User experience flows approved
- Backend Lead: API contracts reviewed
- Frontend Lead: UI mockups feasible

---

## FR6: Context-Aware Stage Requirements

*(Added in v2.0.0 - December 3, 2025)*

### Overview

**Capability**: Dynamic requirement classification based on project context (scale, industry, risk).

**Business Value**: Enable any PM to apply CEO-level governance decisions automatically.

**ADR Reference**: [ADR-011-Context-Aware-Requirements](../../02-design/01-ADRs/ADR-011-Context-Aware-Requirements.md)

---

### FR6.1: 3-Tier Requirement Classification

**Actor**: PM/Tech Lead
**Precondition**: Project profile configured

**Main Flow**:
1. User opens stage requirements view
2. System calculates requirement tiers based on project profile
3. System displays requirements with color-coded classification:
   - 🔴 MANDATORY: Cannot skip
   - 🟡 RECOMMENDED: Skip with justification
   - ⚪ OPTIONAL: Nice-to-have

**Acceptance Criteria**:
- AC1: Requirements auto-classified based on 5 context dimensions
- AC2: Classification updates when project profile changes
- AC3: Override requests tracked with approval workflow

---

### FR6.2: Requirement Override Workflow

**Actor**: PM
**Precondition**: User has "requirements.override" permission

**Main Flow**:
1. User selects requirement to override
2. User provides justification and selects new tier
3. System routes MANDATORY downgrades to CTO/Security Lead
4. Approver reviews and approves/rejects
5. System applies override and logs audit trail

**Acceptance Criteria**:
- AC1: MANDATORY downgrades require CTO approval
- AC2: Override history visible in audit log
- AC3: Override can be reverted

---

## FR7: AI Task Decomposition Service

*(Added in v2.0.0 - December 3, 2025)*

### Overview

**Capability**: AI-powered decomposition of user stories into structured tasks.

**Business Value**: Reduce PM task decomposition time from 30-45min to <2min with same quality.

**ADR Reference**: [ADR-012-AI-Task-Decomposition](../../02-design/01-ADRs/ADR-012-AI-Task-Decomposition.md)

---

### FR7.1: User Story Decomposition

**Actor**: PM/Tech Lead
**Precondition**: User story exists, AI service available

**Main Flow**:
1. User selects user story and clicks "AI Decompose"
2. System builds context (project profile, existing components, similar stories)
3. System calls AI Gateway (Ollama → Claude fallback)
4. System parses AI response into structured tasks
5. System displays tasks with estimates, acceptance criteria, dependencies
6. User reviews, modifies, approves tasks
7. System stores approved tasks in backlog

**Acceptance Criteria**:
- AC1: Decomposition completes in <2 minutes
- AC2: Generated tasks have estimates and acceptance criteria
- AC3: Completeness score calculated and displayed
- AC4: User can modify AI-generated tasks before approval

---

### FR7.2: Export to GitHub Issues

**Actor**: PM
**Precondition**: Decomposition approved, GitHub connected

**Main Flow**:
1. User clicks "Export to GitHub"
2. System creates GitHub Issues for each approved task
3. System links issues to sprint milestone
4. System syncs back issue IDs to Orchestrator

**Acceptance Criteria**:
- AC1: GitHub Issues created with labels and assignees
- AC2: Backlog items linked to GitHub Issue URLs
- AC3: Two-way status sync (bridge pattern)

---

## FR8: 4-Level Planning Hierarchy

*(Added in v2.0.0 - December 3, 2025)*

### Overview

**Capability**: Structured planning from vision to daily tasks.

**Business Value**: Full traceability from code commit to business value.

**ADR Reference**: [ADR-013-Planning-Hierarchy](../../02-design/01-ADRs/ADR-013-Planning-Hierarchy.md)

---

### FR8.1: Planning Hierarchy Navigation

**Actor**: PM/CEO/CTO
**Precondition**: Roadmap exists

**Main Flow**:
1. User views Roadmap (Level 1)
2. User drills down to Phase (Level 2)
3. User drills down to Sprint (Level 3)
4. User drills down to Backlog (Level 4)
5. System displays traceability chain at each level

**Acceptance Criteria**:
- AC1: Navigation between levels is seamless
- AC2: Traceability chain visible at each level
- AC3: Progress metrics aggregated up the hierarchy

---

### FR8.2: Traceability Chain View

**Actor**: PM/Tech Lead
**Precondition**: Backlog item exists

**Main Flow**:
1. User selects backlog item
2. System displays traceability chain:
   - Task → Sprint → Phase → Roadmap → Vision
3. System calculates alignment score
4. System highlights contributing objectives

**Acceptance Criteria**:
- AC1: Full chain displayed in <1 second
- AC2: Alignment score calculated (0-100%)
- AC3: Orphan tasks (no sprint) flagged with warning

---

## FR9: SDLC Structure Validator

*(Added in v2.0.0 - December 3, 2025)*

### Overview

**Capability**: Automated enforcement of SDLC 5.1.3.1 folder structure.

**Business Value**: Consistent project structure across all repositories.

**ADR Reference**: [ADR-014-SDLC-Structure-Validator](../../02-design/01-ADRs/ADR-014-SDLC-Structure-Validator.md)

---

### FR9.1: CLI Validation Tool

**Actor**: Developer
**Precondition**: Project has .sdlc-config.json

**Main Flow**:
1. Developer runs `sdlc-validate --strict`
2. Tool loads project configuration
3. Tool validates stage folders exist and named correctly
4. Tool validates level structure matches project size
5. Tool calculates compliance score
6. Tool outputs report (text/JSON)

**Acceptance Criteria**:
- AC1: Validates all 11 stage folders (00-10)
- AC2: Detects naming variations and suggests corrections
- AC3: Compliance score calculated (0-100%)
- AC4: Exit code 1 if compliance <90% (for CI/CD)

---

### FR9.2: Pre-commit Hook Integration

**Actor**: Developer
**Precondition**: Pre-commit installed

**Main Flow**:
1. Developer attempts commit
2. Pre-commit hook triggers sdlc-validate
3. If compliance <90%, commit blocked
4. Developer fixes issues and retries

**Acceptance Criteria**:
- AC1: Hook blocks non-compliant commits
- AC2: Clear error messages with fix suggestions
- AC3: --fix option available for auto-fixable issues

---

## FR41: IR-Based Code Generation Engine (EP-06)

*(Added in v3.0.0 - December 21, 2025)*
*(Updated in v3.1.0 - December 23, 2025: Quality Gates + Validation Loop)*

### Overview

**Capability**: Intermediate Representation (IR) based code generation from structured project specifications.

**Business Value**: Enable Vietnam SME to generate production-ready code from IR specifications, reducing development time by 60-80%.

**Epic Reference**: [EP-06-IR-Based-Codegen-Engine](../02-Epics/EP-06-IR-Based-Codegen-Engine.md)

**Technical Spec**: [Quality-Gates-Codegen-Specification.md](../../02-design/14-Technical-Specs/Quality-Gates-Codegen-Specification.md)

---

### FR41.1: IR Decomposition & Parsing

**Actor**: System (automated)
**Precondition**: Project has `.sdlc-config.json` with IR modules defined

**Main Flow**:
1. User uploads or generates IR specification (JSON/YAML)
2. System parses IR into component modules:
   - Entity definitions (database schemas)
   - API routes (RESTful endpoints)
   - Business logic (services, validators)
   - UI components (React/Vue templates)
3. System validates IR structure against schema
4. System decomposes 128K tokens → ~5K tokens per module (96% context reduction)
5. System stores parsed IR in database with traceability links

**Acceptance Criteria**:
- AC1: IR parsing completes in <5 seconds for typical project (50 modules)
- AC2: 96%+ context reduction achieved via IR decomposition
- AC3: IR validation errors provide actionable Vietnamese error messages
- AC4: Parsed IR modules linked to source specification

---

### FR41.2: Multi-Provider Code Generation

**Actor**: Developer/PM
**Precondition**: IR parsed and validated

**Main Flow**:
1. User selects IR module(s) for code generation
2. System routes request through Multi-Provider Gateway:
   - **Provider 1**: Ollama (qwen2.5-coder:32b) - Local, fast, cost-effective
   - **Provider 2**: Claude (Anthropic) - Fallback for complex logic
   - **Provider 3**: DeepCode - Q2 2026 decision gate
3. System builds context-aware prompt:
   - IR module content
   - Project constraints (framework, language, patterns)
   - Vietnamese domain context (if applicable)
4. Provider generates code
5. System captures generated code with provider metadata

**Acceptance Criteria**:
- AC1: Multi-provider fallback chain: Ollama → Claude → DeepCode
- AC2: Provider selection based on complexity score and availability
- AC3: Generation latency <30 seconds per module (p95)
- AC4: Provider cost tracking per generation request

---

## FR42: 4-Gate Quality Pipeline for Codegen

*(Added in v3.1.0 - December 23, 2025)*

### Overview

**Capability**: 4-stage quality validation pipeline ensuring generated code meets production standards.

**Business Value**: Prevent defective code from reaching evidence vault, ensuring compliance and quality.

**Technical Spec**: [Quality-Gates-Codegen-Specification.md §2](../../02-design/14-Technical-Specs/Quality-Gates-Codegen-Specification.md)

---

### FR42.1: Gate 1 - Syntax Validation

**Actor**: System (automated)
**Precondition**: Code generated from IR module

**Main Flow**:
1. System extracts language from generation context (Python, TypeScript, SQL)
2. System runs language-specific parser:
   - Python: `ast.parse()` + `ruff --check`
   - TypeScript: `tsc --noEmit` + `eslint`
   - SQL: `sqlparse.parse()` + schema validation
3. System collects syntax errors with line numbers
4. System generates feedback with Vietnamese error messages

**Acceptance Criteria**:
- AC1: Syntax validation <5 seconds per file
- AC2: Parser errors include line:column position
- AC3: Vietnamese error messages for common syntax issues
- AC4: Gate 1 FAIL blocks progression to Gate 2

---

### FR42.2: Gate 2 - Security Validation (SAST)

**Actor**: System (automated)
**Precondition**: Gate 1 PASS

**Main Flow**:
1. System runs Semgrep with AI-specific rules:
   - Prompt injection detection
   - Hardcoded secrets detection
   - SQL injection patterns
   - XSS vulnerabilities
2. System categorizes findings by severity:
   - CRITICAL: Generation FAIL, immediate escalation
   - HIGH: Generation FAIL, retry with feedback
   - MEDIUM/LOW: Warning, continue to Gate 3
3. System generates security feedback with remediation suggestions

**Acceptance Criteria**:
- AC1: SAST scan <10 seconds per file
- AC2: Custom AI-codegen rules detect prompt injection patterns
- AC3: CRITICAL findings block evidence creation
- AC4: Security findings logged in audit trail

---

### FR42.3: Gate 3 - Architecture & Context Validation

**Actor**: System (automated)
**Precondition**: Gate 2 PASS (no CRITICAL/HIGH findings)

**Main Flow**:
1. System runs 5 Context Alignment Checks (CTX-01 to CTX-05):
   - **CTX-01**: IR Module Coverage (entity references match IR)
   - **CTX-02**: Entity-Schema Consistency (foreign keys valid)
   - **CTX-03**: Route-Module Binding (API routes resolve to services)
   - **CTX-04**: Reference Existence (imported modules exist)
   - **CTX-05**: API Shape vs IR (generated routes match spec)
2. System calculates alignment score (0-100%)
3. System generates context feedback with specific mismatches

**Acceptance Criteria**:
- AC1: Context validation <15 seconds per module
- AC2: All 5 CTX checks implemented and passing
- AC3: Alignment score ≥80% required for Gate 3 PASS
- AC4: CTX failures include Vietnamese remediation suggestions

---

### FR42.4: Gate 4 - Test Validation

**Actor**: System (automated)
**Precondition**: Gate 3 PASS (alignment ≥80%)

**Main Flow**:
1. System generates unit tests for generated code (if not provided)
2. System runs tests in isolated environment:
   - Dockerized execution (recommended)
   - Local pytest/vitest (fallback)
3. System collects test results:
   - Pass/Fail counts
   - Coverage percentage
   - Error messages
4. System calculates quality score

**Acceptance Criteria**:
- AC1: Unit tests only (no integration tests for generated code)
- AC2: Dockerized test execution preferred for isolation
- AC3: Test timeout: 60 seconds maximum
- AC4: Gate 4 PASS requires ≥80% test pass rate

---

## FR43: Validation Loop Orchestration

*(Added in v3.1.0 - December 23, 2025)*

### Overview

**Capability**: Automated retry loop for failed code generation with deterministic feedback.

**Business Value**: Maximize first-pass success rate while providing clear escalation path.

**Technical Spec**: [Quality-Gates-Codegen-Specification.md §3](../../02-design/14-Technical-Specs/Quality-Gates-Codegen-Specification.md)

---

### FR43.1: Loop Configuration & Control

**Actor**: System (configurable)
**Precondition**: Codegen request initiated

**Configuration Parameters**:
```yaml
CODEGEN_MAX_RETRIES: 3              # Maximum retry attempts
CODEGEN_ESCALATION_SLA_HOURS: 24    # Hours before escalation times out
CODEGEN_ESCALATION_CHANNEL: council # Target: council | human | abort
```

**Main Flow**:
1. System receives codegen request
2. System initializes attempt counter (attempt_number = 1)
3. System generates code via selected provider
4. System runs 4-Gate Quality Pipeline
5. **IF** all gates PASS: Proceed to evidence locking
6. **IF** any gate FAILS:
   - System increments attempt_number
   - **IF** attempt_number ≤ MAX_RETRIES:
     - System builds deterministic feedback
     - System retries with same or fallback provider
   - **IF** attempt_number > MAX_RETRIES:
     - System escalates to council/human review

**Acceptance Criteria**:
- AC1: MAX_RETRIES configurable (default: 3)
- AC2: Escalation SLA configurable (default: 24 hours)
- AC3: Loop state persisted (survives service restart)
- AC4: Each attempt logged with full context

---

### FR43.2: Deterministic Feedback Contract

**Actor**: System (automated)
**Precondition**: Quality gate failed

**Feedback Schema**:
```python
class QualityGateFeedback:
    attempt_number: int                    # Current attempt (1, 2, 3)
    failed_gates: List[str]               # ["gate_2_security", "gate_3_context"]
    gate_feedback: List[GateFeedbackItem] # Structured feedback per gate
    overall_vietnamese_message: str       # User-friendly summary
    previous_provider: str                # Provider that generated failed code
    recommendation: str                   # "retry_same_provider" | "try_fallback" | "escalate"
```

**Main Flow**:
1. Quality Pipeline returns failed gates with details
2. System constructs QualityGateFeedback object
3. System generates Vietnamese error message
4. System determines recommendation:
   - Syntax errors → retry same provider with specific fix
   - Security errors → try fallback provider
   - Context errors → retry with enriched IR context
   - Repeated failures → escalate
5. System injects feedback into next generation prompt

**Acceptance Criteria**:
- AC1: Feedback schema standardized (Pydantic model)
- AC2: Vietnamese messages for all error categories
- AC3: Recommendation logic deterministic (no AI randomness)
- AC4: Feedback includes specific file:line references

---

### FR43.3: Escalation Workflow

**Actor**: AI Council / Human Reviewer
**Precondition**: MAX_RETRIES exceeded

**Main Flow**:
1. System creates escalation ticket:
   - All attempt history (code, feedback, providers)
   - IR module context
   - Project constraints
2. System routes to escalation channel:
   - **council**: AI Council reviews with multi-agent deliberation
   - **human**: Slack notification to human reviewer
   - **abort**: Mark generation as failed, no evidence created
3. Escalation handler reviews and decides:
   - Approve generated code (override quality gates)
   - Modify IR and retry
   - Abort with explanation
4. System applies decision and updates evidence state

**Acceptance Criteria**:
- AC1: Escalation SLA enforced (24 hours default)
- AC2: Council escalation includes full context history
- AC3: Human escalation sends Slack notification
- AC4: Escalation decision logged in audit trail

---

## FR44: Evidence State Machine for Codegen

*(Added in v3.1.0 - December 23, 2025)*

### Overview

**Capability**: 8-state evidence lifecycle management for generated code.

**Business Value**: Clear audit trail from generation to merge, enabling compliance verification.

**Technical Spec**: [Quality-Gates-Codegen-Specification.md §3.4](../../02-design/14-Technical-Specs/Quality-Gates-Codegen-Specification.md)

---

### FR44.1: Evidence State Transitions

**States**:
```
generated → validating → retrying → escalated → evidence_locked → awaiting_vcr → merged/aborted
```

**Transition Rules**:
| From | To | Trigger | Guard |
|------|----|---------|-------|
| generated | validating | quality_check_started | code_exists |
| validating | retrying | gate_failed | attempt < MAX_RETRIES |
| validating | escalated | gate_failed | attempt >= MAX_RETRIES |
| validating | evidence_locked | all_gates_passed | - |
| retrying | validating | regeneration_complete | - |
| escalated | evidence_locked | council_approved | override_justified |
| escalated | aborted | council_rejected | - |
| evidence_locked | awaiting_vcr | vcr_initiated | evidence_hash_locked |
| awaiting_vcr | merged | vcr_approved | - |
| awaiting_vcr | aborted | vcr_rejected | - |

**Acceptance Criteria**:
- AC1: State machine enforced (invalid transitions rejected)
- AC2: All transitions logged with timestamp and actor
- AC3: Evidence hash locked before VCR submission
- AC4: State queryable via API

---

### FR44.2: Evidence Locking Rules

**Actor**: System (automated)
**Precondition**: All quality gates PASS

**Main Flow**:
1. System computes SHA256 hash of generated code
2. System locks evidence record:
   - `state = 'evidence_locked'`
   - `locked_at = NOW()`
   - `locked_hash = SHA256(code)`
3. System prevents modifications:
   - Code content immutable
   - Metadata (except VCR fields) frozen
4. System initiates VCR workflow if configured

**Acceptance Criteria**:
- AC1: Evidence immutable after locking
- AC2: Hash verification on every access
- AC3: VCR submission requires locked evidence
- AC4: Unlock requires CTO override + audit log

---

## FR45: Codegen Integration Points

*(Added in v3.1.0 - December 23, 2025)*

### Overview

**Capability**: Single integration entry point for codegen orchestration.

**Business Value**: Consistent API surface for all codegen consumers (Dashboard, CLI, VS Code).

**Technical Spec**: [Quality-Gates-Codegen-Specification.md §3.3](../../02-design/14-Technical-Specs/Quality-Gates-Codegen-Specification.md)

---

### FR45.1: Unified Codegen API

**Entry Point**: `POST /api/v1/codegen/generate`

**Request Schema**:
```typescript
{
  "project_id": "uuid",
  "ir_module_id": "uuid",
  "generation_mode": "single" | "batch" | "interactive",
  "provider_preference": "auto" | "ollama" | "claude" | "deepcode",
  "quality_gates_config": {
    "skip_gate_4_tests": false,
    "context_alignment_threshold": 80
  },
  "callback_url": "https://..." // For async batch mode
}
```

**Response Schema**:
```typescript
{
  "generation_id": "uuid",
  "status": "queued" | "generating" | "validating" | "complete" | "failed" | "escalated",
  "evidence_id": "uuid" | null,
  "quality_result": {
    "gate_1_syntax": "pass" | "fail",
    "gate_2_security": "pass" | "fail",
    "gate_3_context": "pass" | "fail",
    "gate_4_tests": "pass" | "fail" | "skipped"
  },
  "attempt_number": 1,
  "provider_used": "ollama",
  "generated_at": "2025-12-23T10:00:00Z"
}
```

**Acceptance Criteria**:
- AC1: Single endpoint for all generation modes
- AC2: Async support with callback_url for batch mode
- AC3: Quality result included in response
- AC4: Generation ID enables status polling

---

### FR45.2: Generation Mode Support

**Modes**:
| Mode | Description | Use Case |
|------|-------------|----------|
| **single** | Generate one IR module, wait for result | Dashboard interactive |
| **batch** | Queue multiple modules, callback on complete | CI/CD pipeline |
| **interactive** | Stream generation with live feedback | VS Code extension |

**Acceptance Criteria**:
- AC1: Single mode: Response in <60 seconds
- AC2: Batch mode: Callback within 5 minutes of completion
- AC3: Interactive mode: SSE stream for progress updates
- AC4: All modes use same quality pipeline

---

### FR45.3: Observability Metrics

**Prometheus Metrics**:
| Metric | Type | Labels | Description |
|--------|------|--------|-------------|
| `codegen_attempts_total` | Counter | provider, status | Total generation attempts |
| `codegen_retry_count` | Histogram | provider | Retries per generation |
| `codegen_gate_failures_total` | Counter | gate, reason | Quality gate failures |
| `codegen_latency_seconds` | Histogram | provider, mode | End-to-end latency |
| `codegen_evidence_state` | Gauge | state | Current evidence count per state |
| `codegen_escalation_queue_size` | Gauge | channel | Pending escalations |
| `codegen_provider_cost_usd` | Counter | provider | Generation cost tracking |

**Grafana Dashboard Queries**:
```promql
# Success rate by provider
sum(rate(codegen_attempts_total{status="success"}[1h])) by (provider)
/ sum(rate(codegen_attempts_total[1h])) by (provider)

# P95 latency
histogram_quantile(0.95, sum(rate(codegen_latency_seconds_bucket[5m])) by (le, provider))

# Gate failure distribution
sum(rate(codegen_gate_failures_total[1h])) by (gate)
```

**Acceptance Criteria**:
- AC1: All 7 metrics implemented
- AC2: Grafana dashboard with 3 panels minimum
- AC3: Alert on escalation queue > 5
- AC4: Cost tracking accurate to $0.01

---

## Next Steps (Post-FRD Approval)

### Week 3-4 (Nov 28 - Dec 9): Architecture Design

**Deliverables**:
1. **Data Model v1.0**: PostgreSQL schema (ERD, SQL DDL)
2. **API Design v1.0**: OpenAPI 3.0 spec (all 20+ endpoints)
3. **Component Diagram**: Backend architecture (FastAPI + OPA + MinIO + Redis)
4. **Deployment Architecture**: Docker-compose production config
5. **ADRs**: 5+ architecture decision records

**Gate G2 Exit Criteria** (Dec 9):
- Data model supports all FR1-FR5 use cases
- API spec validated with frontend team (mock API server)
- Component diagram reviewed by CTO + Backend Lead
- Deployment architecture tested locally (docker-compose up)

---

## References

- [Product Vision](../../docs/00-Project-Foundation/01-Vision/Product-Vision.md) - North star metrics
- [BRD v1.2](../../BRD-v1.2.md) - Business requirements
- [Product Roadmap](../../docs/00-Project-Foundation/04-Roadmap/Product-Roadmap.md) - 90-day timeline
- [Week-02-Kickoff-Brief](../../docs/08-Team-Management/02-Team-Coordination/Week-02-Kickoff-Brief.md) - Week 2 plan

---

**End of Functional Requirements Document**

**Status**: ✅ COMPLETE - Ready for Gate G1 Review
**Date**: November 21, 2025
**Next Gate**: G1 Design Ready (Friday, Nov 25, 2025)
**Approvals Required**: PM, CTO, CPO, Backend Lead, Frontend Lead
