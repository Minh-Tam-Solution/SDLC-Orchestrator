# Master Test Plan — SDLC Orchestrator

```yaml
document_type: "Master Test Plan"
version: "2.2.0"
date: "2026-03-05"
framework: "SDLC 6.1.1"
status: "ACTIVE"
author: "@tester"
reviewer: "@cto (APPROVED 9/10 — 2026-03-05)"
authority: "CTO + QA Lead"
traceability: "MTP v1.0.0 (Sprint 198 skeleton) → MTP v2.0.0 (Sprint 213 comprehensive) → MTP v2.1.0 (Sprint 221 S218-S221 coverage) → MTP v2.2.0 (Sprint 222 OTT @mention routing)"
```

---

## 1. Executive Summary

This Master Test Plan (MTP) is the **single index** for all testing activities in SDLC Orchestrator. It unifies test coverage across **4 interfaces** (Web, CLI, Extension, OTT), maps 29 features to per-interface test cases, defines 9 cross-interface workflow scenarios, and enforces the Zero Mock Policy across all tiers.

### CEO Directive (Sprint 190)

> OTT + CLI = PRIMARY (daily work), Web App = ADMIN ONLY (owner/admin)

This means OTT and CLI test coverage is **P0** — not an afterthought.

### Test Pyramid (Target)

```
         /  E2E  \          10% — 10 critical user journeys (Playwright)
        /----------\
       / Integration \       30% — API contracts, DB transactions, OSS (OPA/MinIO/Redis)
      /----------------\
     /    Unit Tests     \   60% — Service logic, validators, helpers
    /______________________\
```

### Current Metrics (Sprint 222)

| Metric | Value | Target | Status |
|--------|-------|--------|--------|
| Backend route modules | 76 | — | Baselined |
| API endpoints | 577 | — | Baselined |
| CLI command files (sub-commands) | 22 (41+) | — | Baselined |
| Extension command files (registered IDs) | 17 (13+) | — | Baselined |
| OTT governance commands | 10 (MAX capacity) | — | Baselined |
| Frontend pages | 40+ | — | Baselined |
| Total test files | 267+ | — | Baselined (+8 sprint test files S216-S222) |
| Unit tests (functions) | 3,117+ | 95% coverage | On track |
| Integration tests | 993+ | 90% coverage | On track |
| E2E scenarios | 85+ | 10 critical paths | Exceeds |
| Sprint cumulative tests (S216-S222) | 288 | — | 36+38+57+61+30+45+21 |
| MTP test cases (this document) | ~190 | — | v2.2.0 (+15 new, Sprint 222) |
| Multi-Agent test cases (TP-056) | 121 | — | Cross-referenced |
| New DB tables (S218-S221) | +4 | — | skill_agent_grants, shared_workspace_items, consensus_sessions, consensus_votes |
| p95 API latency | 14.0ms | <100ms | PASS |
| OWASP ASVS L2 | 98.4% | Level 2 (264/264) | ACHIEVED |

### Interface Coverage Summary

| Interface | Features Covered | Test Cases (MTP) | Status |
|-----------|-----------------|------------------|--------|
| Web App | 29/29 (admin paths) | ~50 | Active |
| CLI (`sdlcctl`) | 14/29 | ~20 | Active |
| VSCode Extension | 10/29 | ~15 | Active |
| OTT (Telegram/Zalo/Teams/Slack) | 11/29 | ~40 | Updated v2.2.0 (+10 S222) |
| Cross-Interface | 9 workflows | ~14 | Updated v2.2.0 (+2 S222) |
| **Total** | | **~190** | |

---

## 2. Interface Strategy & Testing Implications

### 2.1 Interface Roles (CEO Sprint 190)

| Interface | Role | User Tier | Test Priority |
|-----------|------|-----------|---------------|
| **OTT** (Telegram/Zalo/Teams/Slack) | PRIMARY — team members | STANDARD+ | **P0** |
| **CLI** (`sdlcctl`) | PRIMARY — developers | All tiers | **P0** |
| **VSCode Extension** | PRIMARY — developers in IDE | All tiers | **P0** |
| **Web App** | ADMIN ONLY — owner/admin | All tiers | P1 (admin paths), P2 (deprecated pages) |

### 2.2 ConversationFirstGuard

- Pure ASGI middleware enforces admin-only write paths on Web
- 9 pages replaced with `ConversationFirstFallback` component (Sprint 190)
- Non-admin users redirected to OTT/CLI for governance actions
- Tests: `test_conversation_first_guard.py` (existing)

### 2.3 Test Effort Distribution

| Focus Area | Effort % | Rationale |
|------------|----------|-----------|
| OTT + CLI | 40% | Primary interfaces, highest user traffic per CEO directive |
| Web App | 30% | Admin workflows, governance dashboards, data visualization |
| Extension | 20% | Developer workflows, evidence submit, gate approval |
| Cross-Interface | 10% | Parity verification, state consistency |

### 2.4 OTT Command Registry (Source of Truth)

The 10 registered OTT governance commands (MAX capacity reached — Sprint 202):

| # | Command | ToolName Enum | Permission |
|---|---------|---------------|------------|
| 1 | create_project | `create_project` | `write:projects` |
| 2 | get_gate_status | `get_gate_status` | `read:gates` |
| 3 | submit_evidence | `submit_evidence` | `write:evidence` |
| 4 | request_approval | `request_approval` | `write:gates` |
| 5 | export_audit | `export_audit` | `read:audit` |
| 6 | update_sprint | `update_sprint` | `write:sprints` |
| 7 | close_sprint | `close_sprint` | `write:sprints` |
| 8 | invite_member | `invite_member` | `write:members` |
| 9 | run_evals | `run_evals` | `write:gates` |
| 10 | list_notes | `list_notes` | `read:notes` |

**Source**: `backend/app/services/agent_team/command_registry.py`

---

## 3. Feature Test Matrix — 28 Features × 4 Interfaces

### 3.1 P0 — Must Test Before Any Release (8 Features)

| # | Feature | Web | CLI | Extension | OTT | Test IDs |
|---|---------|-----|-----|-----------|-----|----------|
| F-01 | Authentication & Sessions | login/register/OAuth/MFA pages | `auth login/logout/status` | connectGithub (5 sub-commands) | N/A (session-level auth via JWT) | MTP-AUTH-* |
| F-02 | Projects CRUD | Full CRUD dashboard | `project list/create/set` | initCommand | `create_project` + `/workspace set` | MTP-PROJ-* |
| F-03 | Gate Engine (lifecycle) | create/evaluate/submit/approve/reject/archive | `gate status/evaluate/submit` | createGate, gateApproval | `get_gate_status`, `request_approval` (action=approve\|reject) | MTP-GATE-* |
| F-04 | Evidence Vault | upload/verify/download/search | `evidence submit/list` | evidenceSubmission (Cmd+Shift+E) | `submit_evidence` | MTP-EVID-* |
| F-05 | RBAC & Permissions | Admin user/role management | Scoped by auth token | Scoped by auth token | Resolved via workspace user_id | MTP-RBAC-* |
| F-06 | Agent Team (EP-07) | definitions/conversations/messages UI | `agents` command | N/A | N/A (future) | MTP-AGENT-* |
| F-07 | OTT Gateway | Admin webhook config | N/A | N/A | Webhook intake + command routing + 10 commands | MTP-OTT-* |
| F-08 | Workspace Management | N/A (web has project context via URL) | `project set` (context binding) | initCommand (project selection) | `/workspace set/status` (chat_id binding) | MTP-WKSP-* |

### 3.2 P1 — Test Within Sprint (8 Features)

| # | Feature | Web | CLI | Extension | OTT | Test IDs |
|---|---------|-----|-----|-----------|-----|----------|
| F-09 | Organizations & Invitations | CRUD + invite flow | N/A | N/A | `invite_member` | MTP-ORG-* |
| F-10 | Sprint Management | plan/track/close UI | `plan` command | closeSprint | `update_sprint`, `close_sprint`, `/sprint-status` | MTP-SPRINT-* |
| F-11 | Codegen Pipeline (EP-06) | generate UI + quality view | `generate` command | generateCommand | N/A | MTP-CODEGEN-* |
| F-12 | SAST Scanning | scan results dashboard | N/A | N/A | N/A | MTP-SAST-* |
| F-13 | Policy Engine (OPA) | policy CRUD + evaluation | `governance` command | N/A | N/A | MTP-POLICY-* |
| F-14 | Compliance (NIST) | framework/controls/assessment | `compliance` command | N/A | N/A | MTP-COMP-* |
| F-15 | Tier/Billing | tier management, usage limits | N/A | N/A | N/A | MTP-TIER-* |
| F-16 | Magic Link (OOB approval) | approval landing page | `magic` command | magicCommand | Triggered by `request_approval` | MTP-MAGIC-* |

### 3.3 P2 — Periodic / Quarterly (7 Features)

| # | Feature | Primary Interface | Test IDs |
|---|---------|-------------------|----------|
| F-17 | GDPR/Privacy | Web (consent management) | MTP-GDPR-* |
| F-18 | DORA Metrics | Web (metrics dashboard) | MTP-DORA-* |
| F-19 | Audit Export | Web + CLI + Extension + OTT (`export_audit`) | MTP-AUDIT-* |
| F-20 | Usage Tracking | Web (admin dashboard) | MTP-USAGE-* |
| F-21 | Dashboard / CEO Dashboard | Web (executive view) | MTP-DASH-* |
| F-22 | Governance Mode | Web (vibecoding index) | MTP-GOVMODE-* |
| F-23 | MRP/VCR/CRP Workflows | Web (SASE artifacts) | MTP-WORKFLOW-* |

### 3.4 P1 — Multi-Agent Pattern Adoption (5 Features, Sprint 218-221)

| # | Feature | Web | CLI | Extension | OTT | Test IDs |
|---|---------|-----|-----|-----------|-----|----------|
| F-24 | Skills Engine (search + grants) | Admin skill management | N/A | N/A | N/A (future) | MTP-SKILL-* |
| F-25 | Agent Liveness (heartbeat) | Health dashboard | N/A | N/A | N/A | MTP-HEARTBEAT-* |
| F-26 | Shared Workspace | Workspace viewer | N/A | N/A | N/A (future) | MTP-WORKSPACE-* |
| F-27 | Approval Feedback Loop | Feedback review UI | N/A | N/A | N/A | MTP-FEEDBACK-* |
| F-28 | Group Consensus (voting) | Vote status UI | N/A | N/A | `@vote` (future) | MTP-CONSENSUS-* |

**Source**: PDR-001 (CoPaw/AgentScope Pattern Adoption), ADR-070 (EP-07 ↔ AgentScope Task Contract)

**INVARIANT**: Consensus (F-28) is advisory — CANNOT bypass EP-07 gates. Quorum result = evidence returned to EP-07 gate. Gate still decides PASS/FAIL.

### 3.5 P0 — OTT Interface Parity (1 Feature, Sprint 222)

| # | Feature | Web | CLI | Extension | OTT | Test IDs |
|---|---------|-----|-----|-----------|-----|----------|
| F-29 | OTT @mention → EP-07 Direct Routing | N/A | N/A | N/A | `@agentname` / `@role` in Telegram/Zalo → direct EP-07 agent invoke | MTP-MENTION-* |

**Source**: Sprint 222 (gap from S215-S219 scope deferral). Design gap: S219 "already works" referred to agent-to-agent routing (S177); OTT user→agent @mention shipped S222.

**Routing Precedence** (Sprint 222):
```
/command → telegram_responder (static replies)
@mention → handle_mention_request (EP-07 direct agent routing)   ← NEW
multi-agent keyword → handle_agent_team_request (preset pipeline)
free text → handle_ai_response (Ollama AI reply)
```

**Key files**: `backend/app/services/agent_bridge/ott_team_bridge.py`, `backend/app/api/routes/ott_gateway.py`

**C1 (CTO mandate)**: Uses `MentionParser.extract_mentions()` — proper regex with email false-positive exclusion (`(?<!\S)@word`), NOT naive `"@" in text`.

---

## 4. Cross-Interface Workflow Scenarios — 8 Workflows

### WF-01: Onboarding Flow (P0)

**Goal**: Verify a new user can onboard and operate through all 4 interfaces with the same identity.

| Step | Interface | Action | Expected |
|------|-----------|--------|----------|
| 1 | Web | Register account (email + password) | User created, JWT issued |
| 2 | Web | Login + create first project | Project appears in dashboard |
| 3 | CLI | `sdlcctl auth login` (same credentials) | JWT stored in `~/.sdlcctl/config` |
| 4 | CLI | `sdlcctl project list` | Same project visible |
| 5 | Extension | Connect via `connectGithub` | Extension authenticated to same backend |
| 6 | OTT | Set workspace via `/workspace set <project>` | Workspace bound to chat_id |
| 7 | ALL | Verify: same user_id, same project access | Identity consistent across interfaces |

**Test IDs**: MTP-AUTH-CROSS-001, MTP-PROJ-CROSS-001

### WF-02: Evidence Submission Parity (P0)

**Goal**: Evidence submitted from any interface produces identical records with SHA256 integrity.

| Step | Interface | Action | Expected |
|------|-----------|--------|----------|
| 1 | CLI | `sdlcctl evidence submit --gate-id X --type test_report --file report.pdf` | Evidence uploaded, SHA256 computed |
| 2 | Web | View evidence for gate X | Same file, same SHA256, source=`cli` |
| 3 | Extension | Cmd+Shift+E → submit evidence to gate Y | Evidence uploaded, SHA256 computed |
| 4 | Web | View evidence for gate Y | Same file, same SHA256, source=`extension` |
| 5 | OTT | `submit_evidence` command (gate Z, file_url) | Evidence uploaded |
| 6 | Web | View evidence for gate Z | Same file, source=`ott` |
| 7 | ALL | Compare SHA256 hashes | Integrity verified across all sources |

**Test IDs**: MTP-EVID-CROSS-001, MTP-EVID-CROSS-002

### WF-03: Gate Lifecycle — Multi-Interface (P0)

**Goal**: Gate state machine transitions are consistent regardless of which interface triggers them.

| Step | Interface | Action | Gate State |
|------|-----------|--------|------------|
| 1 | Web | Create gate for project | DRAFT |
| 2 | CLI | `sdlcctl gate evaluate --gate-id X` | DRAFT → EVALUATED |
| 3 | CLI/Web | Submit gate for approval | EVALUATED → SUBMITTED |
| 4 | OTT | `request_approval` (action=approve, gate_id=X) → magic link → approve | SUBMITTED → APPROVED |
| 5 | ALL | Query gate status | APPROVED confirmed on all interfaces |

**Test IDs**: MTP-GATE-CROSS-001, MTP-GATE-CROSS-002

**Reference**: `backend/tests/e2e/test_governance_loop_e2e.py` (existing 3-interface parity test pattern)

### WF-04: Sprint Flow (P1)

**Goal**: Sprint lifecycle from planning to close across interfaces.

| Step | Interface | Action | Expected |
|------|-----------|--------|----------|
| 1 | CLI | `sdlcctl plan --sprint 214` | Sprint plan created |
| 2 | Extension | View sprint status in sidebar | Sprint 214 visible with tasks |
| 3 | OTT | `/sprint-status` | Sprint summary in chat |
| 4 | OTT | `close_sprint` | Sprint closed, report generated |
| 5 | Web | View sprint report in dashboard | Report matches close data |

**Test IDs**: MTP-SPRINT-CROSS-001

### WF-05: Team Collaboration via OTT (P1)

**Goal**: Team members collaborate via OTT group chat with individual permissions.

| Step | Interface | Action | Expected |
|------|-----------|--------|----------|
| 1 | OTT | User A: `/workspace set SDLC-Orchestrator` | Workspace bound to group chat_id |
| 2 | OTT | User A (CTO role): `get_gate_status` | Gate status returned |
| 3 | OTT | User A (CTO role): `request_approval` (action=approve) | Magic link sent → gate approved |
| 4 | OTT | User B (Dev role): `request_approval` (action=approve) | Permission denied (Dev can't approve) |
| 5 | Web | Admin verifies gate status | Gate status matches OTT actions |

**Test IDs**: MTP-OTT-CROSS-001, MTP-RBAC-CROSS-001

### WF-06: Code Generation Pipeline (P1)

**Goal**: End-to-end code generation with quality gates and evidence creation.

| Step | Interface | Action | Expected |
|------|-----------|--------|----------|
| 1 | Web/Extension | Submit codegen spec | Codegen session created |
| 2 | Backend | 4-Gate Quality Pipeline runs | Syntax → Security → Context → Tests |
| 3 | Backend | Evidence auto-created | Evidence with SHA256, bound to gate |
| 4 | Web | View quality results | All 4 gates PASS/FAIL visible |
| 5 | Web | Evidence appears in vault | Linked to codegen session |

**Test IDs**: MTP-CODEGEN-CROSS-001

### WF-07: Compliance Assessment (P2)

**Goal**: Compliance framework setup and validation across Web and CLI.

| Step | Interface | Action | Expected |
|------|-----------|--------|----------|
| 1 | Web | Create compliance framework (NIST CSF) | Framework with controls created |
| 2 | Web | Map controls to project gates | Mapping saved |
| 3 | CLI | `sdlcctl compliance validate` | Validation results returned |
| 4 | Web | View compliance report | Report matches CLI validation |

**Test IDs**: MTP-COMP-CROSS-001

### WF-09: OTT @mention → Direct EP-07 Agent Routing (P0) — NEW Sprint 222

**Goal**: Verify that a human typing `@agentname` or `@role` in Telegram/Zalo triggers direct routing to the matching EP-07 agent definition.

| Step | Interface | Action | Expected |
|------|-----------|--------|----------|
| 1 | OTT (Telegram) | User sends `@pjm báo cáo hiện trạng` in group chat | MentionParser extracts `pjm` |
| 2 | Backend | `handle_mention_request()` — name lookup in `agent_definitions` | Agent `pjm` found (exact name match) |
| 3 | OTT | Acknowledgement: `🔀 Routing → @pjm (project_manager)...` | Ack message sent to chat |
| 4 | Backend | `_process_agent_request(definition_override=pjm_agent)` called | EP-07 pipeline runs with pjm agent |
| 5 | OTT | Agent response returned to chat | pjm agent answers in chat context |
| 6 | OTT (Zalo) | Same message in Zalo group | Same routing (Zalo parity — C3) |
| 7 | OTT | User sends `@reviewer check this code` | Role fallback: finds first active agent with sdlc_role=`reviewer` |
| 8 | OTT | User sends email `team@company.com` (no mention intent) | Email NOT routed — `(?<!\S)@word` pattern excludes mid-word `@` |
| 9 | OTT | User sends `@unknown_agent hello` | Error: agent not found, returns True (handled), does NOT fall through to generic AI |

**Invariant**: Unknown @mention returns `True` (handled, error sent to user) — NEVER `False` (which would incorrectly fall through to generic AI response).

**Test IDs**: MTP-MENTION-OTT-001 through MTP-MENTION-OTT-009, MTP-MENTION-CROSS-001

### WF-08: Multi-Agent Consensus Vote (P1) — NEW Sprint 221

**Goal**: Verify group consensus voting lifecycle with quorum detection across agent team.

| Step | Interface | Action | Expected |
|------|-----------|--------|----------|
| 1 | Web/API | Create consensus session (topic, quorum_type=majority, 3 voters) | Session created, status=open |
| 2 | API | Agent A casts vote (approve) | Vote recorded, status → voting |
| 3 | API | Agent B casts vote (approve) | Vote recorded, quorum reached (2/3 majority) |
| 4 | API | Session auto-closed | status=decided, result.decision=approve, decided_by_vote_id set |
| 5 | API | Agent C attempts to vote | Session already decided, vote still recorded but no state change |
| 6 | Web | View consensus result | Decision + vote breakdown visible |
| 7 | API | Context injection includes `<active_votes>` for open sessions | XML block with vote tally |

**Test IDs**: MTP-CONSENSUS-CROSS-001

---

## 5. Per-Interface Test Suites

### Test Case Naming Convention

```
MTP-{FEATURE}-{INTERFACE}-{SEQ}

FEATURE: AUTH|PROJ|GATE|EVID|RBAC|AGENT|OTT|WKSP|ORG|SPRINT|
         CODEGEN|SAST|POLICY|COMP|TIER|MAGIC|GDPR|DORA|AUDIT|
         USAGE|DASH|GOVMODE|WORKFLOW|SKILL|HEARTBEAT|
         WORKSPACE|FEEDBACK|CONSENSUS|MENTION
INTERFACE: WEB|CLI|EXT|OTT|CROSS
SEQ: 001-999
```

### 5.1 Web App Test Cases (~40 cases)

**Cross-reference**: Detailed Gherkin scenarios in `docs/05-test/07-E2E-Testing/E2E-TEST-SCENARIOS.md` (TC-AUTH-*, TC-GATE-*, TC-EVID-*, etc.)

#### Authentication (P0)

| Test ID | Description | Precondition | Steps | Expected |
|---------|-------------|--------------|-------|----------|
| MTP-AUTH-WEB-001 | Login with email/password | Registered user | Enter credentials → Submit | JWT issued, redirect to dashboard |
| MTP-AUTH-WEB-002 | OAuth login (GitHub) | GitHub account linked | Click "Login with GitHub" | OAuth flow → JWT issued |
| MTP-AUTH-WEB-003 | OAuth login (Google) | Google account linked | Click "Login with Google" | OAuth flow → JWT issued |
| MTP-AUTH-WEB-004 | MFA setup (TOTP) | Authenticated user | Navigate to MFA settings → Scan QR → Enter code | MFA enabled |
| MTP-AUTH-WEB-005 | MFA login verification | MFA enabled | Login → Enter TOTP code | Access granted |
| MTP-AUTH-WEB-006 | Token refresh | Expired access token | Any API call | Token auto-refreshed, request succeeds |
| MTP-AUTH-WEB-007 | Logout | Authenticated | Click logout | Token invalidated, redirect to login |
| MTP-AUTH-WEB-008 | Session expiry | Idle >15 min | Any action | Redirect to login with "session expired" |

#### Projects (P0)

| Test ID | Description | Steps | Expected |
|---------|-------------|-------|----------|
| MTP-PROJ-WEB-001 | Create project | Dashboard → New Project → Fill form → Save | Project created, appears in list |
| MTP-PROJ-WEB-002 | List projects | Navigate to projects page | All user's projects listed |
| MTP-PROJ-WEB-003 | View project details | Click project in list | Project detail page with gates/evidence |
| MTP-PROJ-WEB-004 | Update project | Edit → Change name → Save | Project updated |
| MTP-PROJ-WEB-005 | Delete project | Delete → Confirm in modal | Project soft-deleted, removed from list |
| MTP-PROJ-WEB-006 | Delete project modal closes | Delete → Confirm | Modal closes (onSettled), list refreshes |

#### Gate Engine (P0)

| Test ID | Description | Steps | Expected |
|---------|-------------|-------|----------|
| MTP-GATE-WEB-001 | Create gate | Project → Gates → New → Select type | Gate created in DRAFT state |
| MTP-GATE-WEB-002 | View gate status | Gates list → Click gate | Gate detail with status, criteria, evidence |
| MTP-GATE-WEB-003 | Evaluate gate | Gate detail → Evaluate | OPA policy evaluated, status → EVALUATED |
| MTP-GATE-WEB-004 | Submit gate for approval | Evaluated gate → Submit | Status → SUBMITTED |
| MTP-GATE-WEB-005 | Approve gate | Submitted gate → Approve (admin/CTO) | Status → APPROVED |
| MTP-GATE-WEB-006 | Reject gate | Submitted gate → Reject (with reason) | Status → REJECTED |
| MTP-GATE-WEB-007 | Archive gate | Any terminal state → Archive | Status → ARCHIVED |
| MTP-GATE-WEB-008 | View policy result | Evaluated gate → Policy tab | OPA result JSON displayed |

#### Evidence Vault (P0)

| Test ID | Description | Steps | Expected |
|---------|-------------|-------|----------|
| MTP-EVID-WEB-001 | Upload evidence | Gate → Evidence → Upload file | File stored in MinIO, SHA256 computed |
| MTP-EVID-WEB-002 | Verify evidence integrity | Evidence detail → Verify | SHA256 recomputed, match confirmed |
| MTP-EVID-WEB-003 | Download evidence | Evidence detail → Download | File downloaded, SHA256 matches |
| MTP-EVID-WEB-004 | Search evidence | Evidence page → Filter by type/gate | Filtered results returned |
| MTP-EVID-WEB-005 | Evidence binding to gate | Upload → Select gate | Evidence bound to gate's exit criteria |

#### Admin & RBAC (P0)

| Test ID | Description | Steps | Expected |
|---------|-------------|-------|----------|
| MTP-RBAC-WEB-001 | Admin user management | Admin → Users → View/Edit | User list with roles displayed |
| MTP-RBAC-WEB-002 | Role-based page access | Non-admin → Admin page | Access denied (403) |
| MTP-RBAC-WEB-003 | ConversationFirstGuard | Non-admin → Deprecated page | ConversationFirstFallback shown |
| MTP-RBAC-WEB-004 | Row-level security | User A → User B's project | Not visible (filtered by tenant) |

#### Agent Team (P0)

| Test ID | Description | Steps | Expected |
|---------|-------------|-------|----------|
| MTP-AGENT-WEB-001 | Create agent definition | Agent Team → New Definition | Agent created with tool permissions |
| MTP-AGENT-WEB-002 | Start conversation | Definition → Start Conversation | Conversation created, initial message |
| MTP-AGENT-WEB-003 | Send message | Conversation → Type → Send | Message queued, agent responds |
| MTP-AGENT-WEB-004 | Interrupt conversation | Conversation → Interrupt | Conversation interrupted gracefully |
| MTP-AGENT-WEB-005 | View conversation history | Conversation → History | All messages displayed with metadata |

#### P1 Web Tests (Summary)

| Test ID | Feature | Description |
|---------|---------|-------------|
| MTP-ORG-WEB-001 | Organizations | Create organization |
| MTP-ORG-WEB-002 | Organizations | Invite member via email |
| MTP-ORG-WEB-003 | Organizations | Accept/reject invitation |
| MTP-ORG-WEB-004 | Organizations | Remove member |
| MTP-SPRINT-WEB-001 | Sprint Mgmt | View sprint dashboard |
| MTP-SPRINT-WEB-002 | Sprint Mgmt | Sprint planning view |
| MTP-SPRINT-WEB-003 | Sprint Mgmt | Close sprint from Web |
| MTP-CODEGEN-WEB-001 | Codegen | Submit codegen spec |
| MTP-CODEGEN-WEB-002 | Codegen | View quality pipeline results |
| MTP-CODEGEN-WEB-003 | Codegen | Download generated code |
| MTP-CODEGEN-WEB-004 | Codegen | View provider stats |
| MTP-SAST-WEB-001 | SAST | Run SAST scan |
| MTP-SAST-WEB-002 | SAST | View scan findings |
| MTP-SAST-WEB-003 | SAST | Filter by severity (ERROR/WARNING/INFO) |
| MTP-POLICY-WEB-001 | Policy | Create policy |
| MTP-POLICY-WEB-002 | Policy | Evaluate policy against project |
| MTP-POLICY-WEB-003 | Policy | View policy pack library |
| MTP-COMP-WEB-001 | Compliance | Create compliance framework |
| MTP-COMP-WEB-002 | Compliance | Map controls to gates |
| MTP-COMP-WEB-003 | Compliance | Run assessment |
| MTP-TIER-WEB-001 | Tier/Billing | View tier limits |
| MTP-TIER-WEB-002 | Tier/Billing | Upgrade tier |
| MTP-TIER-WEB-003 | Tier/Billing | Usage limit enforcement |
| MTP-MAGIC-WEB-001 | Magic Link | Approval landing page |
| MTP-MAGIC-WEB-002 | Magic Link | Expired link handling |

#### P1 — Multi-Agent Pattern Features (Sprint 218-221)

| Test ID | Feature | Description |
|---------|---------|-------------|
| MTP-SKILL-WEB-001 | Skills Engine | Search skills via tsvector (plainto_tsquery) |
| MTP-SKILL-WEB-002 | Skills Engine | Grant skill to agent (skill_agent_grants) |
| MTP-SKILL-WEB-003 | Skills Engine | Agent without grant cannot access workspace skills |
| MTP-SKILL-WEB-004 | Skills Engine | Grant idempotent (ON CONFLICT DO NOTHING) |
| MTP-HEARTBEAT-WEB-001 | Agent Liveness | View agent heartbeat status (stale vs active) |
| MTP-HEARTBEAT-WEB-002 | Agent Liveness | Stale agent recovery triggers system message |
| MTP-WORKSPACE-WEB-001 | Shared Workspace | View workspace items for conversation |
| MTP-WORKSPACE-WEB-002 | Shared Workspace | Version conflict raises VersionConflictError |
| MTP-WORKSPACE-WEB-003 | Shared Workspace | Soft-deleted items excluded from list |
| MTP-FEEDBACK-WEB-001 | Approval Feedback | Approve with feedback stored in metadata |
| MTP-FEEDBACK-WEB-002 | Approval Feedback | Reject with feedback injects `<human_feedback>` |
| MTP-CONSENSUS-WEB-001 | Group Consensus | Create consensus session (majority/unanimous/threshold) |
| MTP-CONSENSUS-WEB-002 | Group Consensus | View vote tally and quorum status |
| MTP-CONSENSUS-WEB-003 | Group Consensus | Decided session shows result breakdown |

### 5.2 CLI (`sdlcctl`) Test Cases (~20 cases)

**Source of truth**: `backend/sdlcctl/sdlcctl/commands/` (22 command files, 41+ sub-commands)

#### Authentication (P0)

| Test ID | Command | Steps | Expected |
|---------|---------|-------|----------|
| MTP-AUTH-CLI-001 | `sdlcctl auth login` | Enter email + password | JWT stored in `~/.sdlcctl/config` |
| MTP-AUTH-CLI-002 | `sdlcctl auth status` | After login | Shows current user, role, token expiry |
| MTP-AUTH-CLI-003 | `sdlcctl auth logout` | After login | Token cleared, config reset |

#### Projects (P0)

| Test ID | Command | Steps | Expected |
|---------|---------|-------|----------|
| MTP-PROJ-CLI-001 | `sdlcctl project list` | After auth | Lists all accessible projects |
| MTP-PROJ-CLI-002 | `sdlcctl project create --name "Test"` | After auth | Project created, ID returned |
| MTP-PROJ-CLI-003 | `sdlcctl project set --id X` | Valid project ID | Project context set for subsequent commands |

#### Gate Engine (P0)

| Test ID | Command | Steps | Expected |
|---------|---------|-------|----------|
| MTP-GATE-CLI-001 | `sdlcctl gate status` | Project context set | All gates for project listed with status |
| MTP-GATE-CLI-002 | `sdlcctl gate evaluate --gate-id X` | Gate in DRAFT | Gate evaluated, status → EVALUATED |
| MTP-GATE-CLI-003 | `sdlcctl gate submit --gate-id X` | Gate in EVALUATED | Gate submitted, status → SUBMITTED |
| MTP-GATE-CLI-004 | `sdlcctl gate status --gate-id X` | Any state | Single gate detail with full status |

#### Evidence (P0)

| Test ID | Command | Steps | Expected |
|---------|---------|-------|----------|
| MTP-EVID-CLI-001 | `sdlcctl evidence submit --gate-id X --type test_report --file report.pdf` | Gate exists, file exists | Evidence uploaded, SHA256 returned |
| MTP-EVID-CLI-002 | `sdlcctl evidence list --gate-id X` | Evidence exists | List of evidence with types, dates, SHA256 |

#### P1 CLI Tests

| Test ID | Command | Description |
|---------|---------|-------------|
| MTP-SPRINT-CLI-001 | `sdlcctl plan` | Create/view sprint plan |
| MTP-SPRINT-CLI-002 | `sdlcctl plan --sprint X --close` | Close sprint from CLI |
| MTP-CODEGEN-CLI-001 | `sdlcctl generate --spec spec.yaml` | Generate code from spec |
| MTP-POLICY-CLI-001 | `sdlcctl governance validate` | Validate governance policies |
| MTP-COMP-CLI-001 | `sdlcctl compliance validate` | Run compliance validation |
| MTP-MAGIC-CLI-001 | `sdlcctl magic approve --token X` | Approve gate via magic link token |
| MTP-AUDIT-CLI-001 | `sdlcctl report --type audit` | Export audit report |

### 5.3 VSCode Extension Test Cases (~15 cases)

**Source of truth**: `vscode-extension/src/commands/` (17 command files, 13+ registered command IDs)

#### Authentication (P0)

| Test ID | Command | Steps | Expected |
|---------|---------|-------|----------|
| MTP-AUTH-EXT-001 | `connectGithub` | Command palette → Connect GitHub | OAuth flow → GitHub linked |
| MTP-AUTH-EXT-002 | `disconnectGithub` | Command palette → Disconnect | GitHub unlinked |
| MTP-AUTH-EXT-003 | `reinit` | Command palette → Reinit | Extension re-authenticated |

#### Projects (P0)

| Test ID | Command | Steps | Expected |
|---------|---------|-------|----------|
| MTP-PROJ-EXT-001 | `initCommand` | Command palette → Init Project | Project context set in Extension |
| MTP-PROJ-EXT-002 | `initCommand` (no project) | Init with empty workspace | Error: "Select a project first" |

#### Gate Engine (P0)

| Test ID | Command | Steps | Expected |
|---------|---------|-------|----------|
| MTP-GATE-EXT-001 | `createGate` | Command palette → Create Gate | Gate created in DRAFT |
| MTP-GATE-EXT-002 | `gateApproval` | Command palette → Gate Approval | Approval flow triggered (if registered) |

#### Evidence (P0)

| Test ID | Command | Steps | Expected |
|---------|---------|-------|----------|
| MTP-EVID-EXT-001 | `evidenceSubmission` (Cmd+Shift+E) | Select file → Cmd+Shift+E → Select gate | Evidence uploaded to gate |
| MTP-EVID-EXT-002 | `evidenceSubmission` (no file) | Cmd+Shift+E with no file open | Error: "No active file" |

#### P1 Extension Tests

| Test ID | Command | Description |
|---------|---------|-------------|
| MTP-SPRINT-EXT-001 | `closeSprint` | Close sprint from Extension |
| MTP-SPRINT-EXT-002 | Sprint status sidebar | View sprint status in sidebar panel |
| MTP-CODEGEN-EXT-001 | `generateCommand` | Generate code from Extension |
| MTP-MAGIC-EXT-001 | `magicCommand` | Open magic link for gate approval |
| MTP-AUDIT-EXT-001 | `exportAuditCommand` | Export audit log from Extension |
| MTP-AGENT-EXT-001 | `teamCommand` | View/manage team from Extension |

### 5.4 OTT (Telegram/Zalo/Teams/Slack) Test Cases (~25 cases)

**Source of truth**: `backend/app/services/agent_team/command_registry.py` (10 commands, ToolName enum)

#### Webhook & Gateway (P0)

| Test ID | Description | Steps | Expected |
|---------|-------------|-------|----------|
| MTP-OTT-OTT-001 | Telegram webhook intake | POST /api/v1/ott/telegram/webhook with valid payload | 200 OK, message routed |
| MTP-OTT-OTT-002 | Invalid webhook signature | POST with tampered payload | 401 Unauthorized |
| MTP-OTT-OTT-003 | Unknown command text | Send "random text" | AI response or help message |
| MTP-OTT-OTT-004 | Command routing to registry | Send "gate status" | Routed to `get_gate_status` handler |
| MTP-OTT-OTT-005 | Input sanitization | Send message with injection patterns | 12 injection regexes block malicious input |
| MTP-OTT-OTT-006 | 4096 char limit handling | Response >4096 chars | Truncated with "..." or paginated |

#### Workspace (P0)

| Test ID | Description | Steps | Expected |
|---------|-------------|-------|----------|
| MTP-WKSP-OTT-001 | `/workspace set <project>` | Private chat → set workspace | Workspace bound to chat_id |
| MTP-WKSP-OTT-002 | `/workspace status` | After workspace set | Current workspace name + project details |
| MTP-WKSP-OTT-003 | Command without workspace | Send governance command, no workspace | "Set workspace first: /workspace set" |
| MTP-WKSP-OTT-004 | Group chat workspace sharing | Group chat → `/workspace set` | Same workspace for all group members |

#### Governance Commands (P0)

| Test ID | Command | Steps | Expected |
|---------|---------|-------|----------|
| MTP-GATE-OTT-001 | `get_gate_status` | "gate status" or "show gates" | Gate list with statuses returned |
| MTP-GATE-OTT-002 | `get_gate_status` (specific gate) | "gate status for gate X" | Single gate detail returned |
| MTP-GATE-OTT-003 | `request_approval` (approve) | "approve gate X" | Magic link generated → approval flow |
| MTP-GATE-OTT-004 | `request_approval` (reject) | "reject gate X reason: not ready" | Gate rejected with reason |
| MTP-EVID-OTT-001 | `submit_evidence` | "submit evidence for gate X type test_report" | Evidence created |
| MTP-EVID-OTT-002 | `submit_evidence` (missing params) | "submit evidence" (no gate_id) | Error: "Specify gate_id and evidence_type" |
| MTP-SPRINT-OTT-001 | `update_sprint` | "update sprint status" | Sprint status updated |
| MTP-SPRINT-OTT-002 | `close_sprint` | "close sprint" | Sprint closed, summary generated |
| MTP-AUDIT-OTT-001 | `export_audit` | "export audit log" | Audit export generated and linked |
| MTP-ORG-OTT-001 | `invite_member` | "invite user@email.com" | Invitation sent |

#### Permission & Security (P0)

| Test ID | Description | Steps | Expected |
|---------|-------------|-------|----------|
| MTP-RBAC-OTT-001 | CTO approval via OTT | CTO sends `request_approval` (approve) | Magic link → gate approved |
| MTP-RBAC-OTT-002 | Dev approval denied | Dev sends `request_approval` (approve) | "Permission denied: requires write:gates" |
| MTP-OTT-OTT-007 | Credential scrubbing | Agent output contains API key | Key pattern masked (ADR-058 Pattern A) |
| MTP-OTT-OTT-008 | History compaction | Conversation >80% capacity | Auto-summarized (ADR-058 Pattern B) |

#### @mention → EP-07 Direct Agent Routing (P0) — Sprint 222

| Test ID | Description | Steps | Expected |
|---------|-------------|-------|----------|
| MTP-MENTION-OTT-001 | Name-based routing | Send `@pjm báo cáo` in Telegram | Agent `pjm` found by name, routed, ack sent |
| MTP-MENTION-OTT-002 | Role-based routing | Send `@reviewer check code` | First active agent with `sdlc_role=reviewer` found, routed |
| MTP-MENTION-OTT-003 | Ack message sent | @mention → agent found | `🔀 Routing → @pjm (role)...` sent before pipeline runs |
| MTP-MENTION-OTT-004 | Unknown agent | Send `@nobody hello` | Error message sent, returns True (handled) — NOT falls through |
| MTP-MENTION-OTT-005 | No project bound | @mention, no workspace set | Error: "Workspace not configured" sent, returns True |
| MTP-MENTION-OTT-006 | Email false-positive | Send `admin@company.com please reply` | `company` NOT extracted as @mention (regex guards mid-word @) |
| MTP-MENTION-OTT-007 | Multi-mention: first wins | Send `@pjm and @architect please advise` | Only `pjm` routed (first mention), single pipeline call |
| MTP-MENTION-OTT-008 | Zalo parity | Same `@agent` message in Zalo channel | Same routing, `channel="zalo"`, `bot_token=""` |
| MTP-MENTION-OTT-009 | Routing precedence: /command wins | `/gate-status` in same message with @mention | `/gate-status` handled by telegram_responder, @mention NOT triggered |
| MTP-MENTION-OTT-010 | Pipeline backward compat | `_process_agent_request(definition_override=None)` | Falls back to `_find_entry_agent()` — existing behaviour unchanged |

**Source**: `backend/tests/unit/test_sprint222_ott_mention.py` (21 tests, 10 groups)
**Key design**: `MentionParser.extract_mentions()` (C1) — proper regex, not `"@" in text`

#### Multi-Agent Pattern Features via OTT (Sprint 218-221)

| Test ID | Description | Steps | Expected |
|---------|-------------|-------|----------|
| MTP-CONSENSUS-OTT-001 | `@vote` create session | Agent sends `@vote create "topic" majority` | Consensus session created, voters notified |
| MTP-CONSENSUS-OTT-002 | `@vote approve` | Agent sends `@vote approve "reasoning"` | Vote recorded, quorum checked |
| MTP-CONSENSUS-OTT-003 | `@vote reject` | Agent sends `@vote reject "not ready"` | Vote recorded, may trigger early reject |
| MTP-CONSENSUS-OTT-004 | Consensus context injection | Open session exists | `<active_votes>` block in agent context |
| MTP-WORKSPACE-OTT-001 | Workspace context injection | Active workspace items | `<workspace>` block in agent context |
| MTP-WORKSPACE-OTT-002 | Workspace key preview | Item >50 chars | Truncated with '...' |

### 5.5 Cross-Interface Test Cases (~12 cases)

These are the verification points from Section 4 Workflows, formalized as test cases.

| Test ID | Workflow | Assertion |
|---------|----------|-----------|
| MTP-AUTH-CROSS-001 | WF-01 | Same user_id across Web/CLI/Extension after auth |
| MTP-PROJ-CROSS-001 | WF-01 | Same project visible across all interfaces |
| MTP-EVID-CROSS-001 | WF-02 | Evidence SHA256 identical regardless of submission interface |
| MTP-EVID-CROSS-002 | WF-02 | Evidence source field correctly set (cli/extension/ott/web) |
| MTP-GATE-CROSS-001 | WF-03 | Gate state machine transitions consistent across interfaces |
| MTP-GATE-CROSS-002 | WF-03 | Approval via OTT magic link produces same gate state as Web approval |
| MTP-SPRINT-CROSS-001 | WF-04 | Sprint close from any interface produces same report |
| MTP-OTT-CROSS-001 | WF-05 | OTT group workspace actions reflected in Web admin view |
| MTP-RBAC-CROSS-001 | WF-05 | Permission enforcement identical across OTT and Web |
| MTP-CODEGEN-CROSS-001 | WF-06 | Generated evidence auto-bound to gate across interfaces |
| MTP-CONSENSUS-CROSS-001 | WF-08 | Consensus quorum result consistent across Web view and API |
| MTP-CONSENSUS-CROSS-002 | WF-08 | Consensus decision = advisory evidence, does NOT bypass EP-07 gate |
| MTP-MENTION-CROSS-001 | WF-09 | @mention in OTT routes to same EP-07 agent as direct API call with same definition_id |
| MTP-MENTION-CROSS-002 | WF-09 | Agent response via @mention appears in conversation history viewable from Web |

---

## 6. Test Categories Index

| # | Category | Directory | Status | Key Documents |
|---|----------|-----------|--------|---------------|
| 00 | Test Strategy | [00-TEST-STRATEGY-2026.md](00-TEST-STRATEGY-2026.md) | Active | TDD Iron Law, pyramid, skills |
| 01 | Test Strategy Gov | [01-Test-Strategy/](01-Test-Strategy/) | Active | SPEC-0001, SPEC-0019, SPEC-0021 |
| 02 | Security Testing | 02-Security-Testing/ | **TODO** | OWASP ASVS L2, Semgrep, pen-test |
| 03 | Unit Testing | [03-Unit-Testing/](03-Unit-Testing/) | Active | GitHub service, sync jobs |
| 04 | Integration Testing | [04-Integration-Testing/](04-Integration-Testing/) | Active | OAuth, MinIO |
| 05 | Performance Testing | 05-Performance-Testing/ | **TODO** | Locust 100K, p95 benchmarks |
| 06 | Accessibility Testing | 06-Accessibility-Testing/ | **TODO** | WCAG 2.1 AA, Lighthouse |
| 07 | E2E Testing | [07-E2E-Testing/](07-E2E-Testing/) | Active | 26 Bruno tests, Playwright |
| 08 | API Testing | [08-API-Testing/](08-API-Testing/) | Active | OpenAPI spec validation |
| 09 | Load Testing | [09-Load-Testing/](09-Load-Testing/) | Active | Webhook load test plan |

### Cross-Cutting Documents

| Document | Location | Purpose |
|----------|----------|---------|
| Testing Architecture | [docs/02-design/13-Testing-Strategy/Testing-Architecture.md](../02-design/13-Testing-Strategy/Testing-Architecture.md) | Zero Mock Policy, test infra design |
| Multi-Agent Test Plan | [docs/02-design/13-Testing-Strategy/Multi-Agent-Test-Plan.md](../02-design/13-Testing-Strategy/Multi-Agent-Test-Plan.md) | ADR-056 EP-07 test scenarios (121 cases) |
| Remediation Plan | [REMEDIATION-PLAN-GOLIVE-2026.md](REMEDIATION-PLAN-GOLIVE-2026.md) | 3-sprint go-live testing roadmap |
| Testing Strategy Gov v2 | [01-Test-Strategy/Testing-Strategy-Governance-v2.md](01-Test-Strategy/Testing-Strategy-Governance-v2.md) | SPEC-0001/0002, Anti-Vibecoding |
| E2E Test Scenarios | [07-E2E-Testing/E2E-TEST-SCENARIOS.md](07-E2E-Testing/E2E-TEST-SCENARIOS.md) | Detailed TC-* Gherkin scenarios (Web-only, 1,688 lines) |
| ADR-070 | [docs/02-design/01-ADRs/ADR-070-MTClaw-Best-Practice-Adoption.md](../02-design/01-ADRs/ADR-070-MTClaw-Best-Practice-Adoption.md) | EP-07 ↔ AgentScope Task Contract (S218-S221 prerequisite) |
| Sprint 218-222 Tests | `backend/tests/unit/test_sprint218_*.py` through `test_sprint222_*.py` | 288 cumulative sprint tests (7 sprints S216-S222) |

---

## 7. Traceability Matrix — Tests to SDLC Stages

| SDLC Stage | Gate | Test Categories | Key Test Suites | Interface Coverage |
|------------|------|-----------------|-----------------|-------------------|
| 00 Foundation | G0.1, G0.2 | 01 (Strategy) | Conformance: SPEC-0019 | Web |
| 01 Planning | G1 | 08 (API) | OpenAPI spec validation | Web, CLI |
| 02 Design | G2 | 01 (Strategy), 02 (Security) | Architecture review, threat model | Web |
| 03 Build | G3 | 03 (Unit), 04 (Integration) | 3,096+ unit, 993+ integration | All 4 |
| 04 Deploy | G4 | 07 (E2E), 09 (Load) | Playwright journeys, Locust | Web, CLI, OTT |
| 05 Test | — | **All categories** | This Master Test Plan | All 4 |
| 06 Operate | — | 05 (Performance) | Prometheus, p95 monitoring | Web (dashboard) |
| 07 Integrate | — | 04 (Integration) | OAuth, MinIO, OPA contract tests | Web, CLI |
| 08 Feedback | — | 01 (Strategy) | Developer satisfaction survey | All 4 |
| 09 Govern | — | 02 (Security), 06 (Accessibility) | OWASP ASVS, WCAG 2.1 AA | Web |

---

## 8. Test Infrastructure

### 8.1 Local Development

```bash
# Start test dependencies
docker compose -f docker-compose.staging.yml up -d postgres redis opa minio

# Run unit tests (fast, no external deps)
python -m pytest backend/tests/unit/ -v --tb=short

# Run integration tests (requires Docker services)
DATABASE_URL="postgresql://test:test@localhost:15432/sdlc_test" \
  python -m pytest backend/tests/integration/ -v

# Run E2E tests
python -m pytest backend/tests/e2e/ -v

# Run quick-tests (baseline: 114 tests)
python -m pytest backend/tests/quick-tests/ -v

# Run CLI tests
cd backend/sdlcctl && python -m pytest tests/ -v

# Run Extension tests
cd vscode-extension && npm test

# Run Frontend tests
cd frontend && npx vitest run
```

### 8.2 CI/CD Pipeline

```yaml
Pre-commit:
  - ruff lint + black format
  - AGPL import detection
  - Zero Mock keyword ban

GitHub Actions:
  - Unit tests (95% coverage gate)
  - Integration tests (90% coverage gate)
  - Security scan (Semgrep OWASP rules)
  - License scan (Syft + Grype)
  - SBOM generation
```

### 8.3 Docker Services (Test Environment)

| Service | Port | Purpose |
|---------|------|---------|
| PostgreSQL 15.5 | 15432 | Test database |
| Redis 7.2 | 6395 | Cache, sessions, rate limiting |
| OPA 0.58 | 8185 | Policy evaluation |
| MinIO | 9000 | Evidence storage (S3 API) |
| Backend | 8300 | Staging API server |
| Frontend | 8310 | Staging UI |

---

## 9. Test Data & Factories

### 9.1 Core Model Factories

| Factory | Model | Key Fields | Location |
|---------|-------|------------|----------|
| UserFactory | `User` | email, password_hash, role, is_active | `backend/tests/factories/` |
| ProjectFactory | `Project` | name, tier, github_repo_full_name | `backend/tests/factories/` |
| GateFactory | `Gate` | gate_type, status, project_id | `backend/tests/factories/` |
| EvidenceFactory | `GateEvidence` | type, s3_key, sha256_hash | `backend/tests/factories/` |
| PolicyFactory | `Policy` | name, rego_content, severity | `backend/tests/factories/` |
| CodegenFactory | `CodegenSession` | spec, provider, quality_result | `backend/tests/factories/` |

**Status**: Factory pattern used ad-hoc in tests via helper functions. Formal factory-boy integration planned.

### 9.2 Interface-Specific Test Fixtures

#### OTT Fixtures

```python
# Telegram webhook payload fixture
TELEGRAM_WEBHOOK_PAYLOAD = {
    "update_id": 123456789,
    "message": {
        "message_id": 1,
        "from": {"id": 987654321, "first_name": "Test", "username": "testuser"},
        "chat": {"id": -100123456, "type": "group", "title": "SDLC Team"},
        "text": "/gate-status",
        "date": 1709308800
    }
}

# Normalized message fixture (post-normalizer)
NORMALIZED_OTT_MESSAGE = {
    "channel": "telegram",
    "chat_id": "-100123456",
    "sender_id": "987654321",
    "text": "gate status",
    "message_id": "1"
}
```

#### CLI Fixtures

```python
# CLI auth config fixture
CLI_AUTH_CONFIG = {
    "api_url": "http://localhost:8300",
    "access_token": "eyJhbGciOiJIUzI1NiIs...",
    "refresh_token": "eyJhbGciOiJIUzI1NiIs...",
    "user_id": "550e8400-e29b-41d4-a716-446655440000",
    "email": "dev@example.com",
    "role": "developer"
}

# CLI project context fixture
CLI_PROJECT_CONTEXT = {
    "project_id": 1,
    "project_name": "SDLC-Orchestrator",
    "tier": "PROFESSIONAL"
}
```

#### Extension Fixtures

```typescript
// VSCode API mock fixture
const vscodeApiMock = {
  window: {
    showInformationMessage: vi.fn(),
    showErrorMessage: vi.fn(),
    showInputBox: vi.fn(),
    createStatusBarItem: vi.fn()
  },
  workspace: {
    getConfiguration: vi.fn().mockReturnValue({
      get: vi.fn().mockReturnValue("http://localhost:8300")
    })
  },
  commands: {
    registerCommand: vi.fn(),
    executeCommand: vi.fn()
  }
};
```

### 9.3 Test Users (All Interfaces)

| User | Email | Role | Tier | Used In |
|------|-------|------|------|---------|
| Admin | admin@sdlc.test | owner | ENTERPRISE | Web admin tests |
| CTO | cto@sdlc.test | cto | PROFESSIONAL | Gate approval tests |
| PM | pm@sdlc.test | pm | STANDARD | Sprint management tests |
| Dev | dev@sdlc.test | developer | STANDARD | Evidence submit, CLI tests |
| QA | qa@sdlc.test | qa | STANDARD | SAST, compliance tests |
| Viewer | viewer@sdlc.test | viewer | LITE | Read-only access tests |

---

## 10. Regression Test Suite

### 10.1 Smoke Tests (Every Commit) — Target: <2 min

| # | Feature | Test | Interface |
|---|---------|------|-----------|
| 1 | Auth | Login with valid credentials | API |
| 2 | Projects | List projects (authenticated) | API |
| 3 | Gates | Create + evaluate gate | API |
| 4 | Evidence | Upload + verify SHA256 | API |
| 5 | OTT | Webhook POST + command routing | API |
| 6 | Health | `GET /health` + all service endpoints | API |

**Run**: `python -m pytest backend/tests/smoke/ -v --timeout=120`

### 10.2 P0 Regression (Every PR Merge) — Target: <10 min

All P0 feature tests across all interfaces (~97 test cases) plus P1 multi-agent pattern tests (~30 cases):
- MTP-AUTH-* (21 cases)
- MTP-PROJ-* (12 cases)
- MTP-GATE-* (23 cases)
- MTP-EVID-* (14 cases)
- MTP-RBAC-* (8 cases)
- MTP-AGENT-* (6 cases)
- MTP-OTT-* (8 cases)
- MTP-WKSP-* (5 cases)
- MTP-SKILL-* (4 cases) — Sprint 218
- MTP-HEARTBEAT-* (2 cases) — Sprint 219
- MTP-WORKSPACE-* (5 cases) — Sprint 219-220
- MTP-FEEDBACK-* (2 cases) — Sprint 220
- MTP-CONSENSUS-* (9 cases) — Sprint 221
- MTP-MENTION-* (12 cases) — Sprint 222

Plus quick-test baseline (114 tests).

**Run**: `python -m pytest backend/tests/ -m "p0" -v --timeout=600`

### 10.3 Full Regression (Nightly) — Target: <30 min

All ~190 MTP test cases + 121 TP-056 Multi-Agent test cases + 288 sprint cumulative tests (S216-S222) = ~599 total.

**Run**:
```bash
python -m pytest backend/tests/ -v --timeout=1800
cd vscode-extension && npm test
cd frontend && npx vitest run
```

### 10.4 Release Regression (Before Each Release) — Target: <2 hours

Full regression PLUS:
- Load test: Locust 100K concurrent users
- Security scan: Semgrep (OWASP + AI-specific rules)
- OWASP ASVS L2 validation (264/264 requirements)
- License scan: Syft + Grype
- SBOM generation

**Run**: `./scripts/release-regression.sh` (orchestrates all suites)

---

## 11. Missing Sections & Roadmap

### 11.1 Security Testing (02-Security-Testing/) — P1

```yaml
Planned Documents:
  - OWASP-ASVS-L2-TESTING-PLAN.md
    - 264/264 requirement verification procedures
    - Authentication test cases (JWT, OAuth, MFA)
    - Authorization test cases (RBAC, 13 roles, row-level security)
    - Input validation (SQL injection, XSS, SSRF — 12 patterns)
    - Secrets management (90-day rotation verification)

  - SEMGREP-CI-INTEGRATION.md
    - AI-specific security rules (policy-packs/semgrep/ai-security.yml)
    - OWASP Python rules (policy-packs/semgrep/owasp-python.yml)
    - Custom rules for AGPL import detection
    - CI gate: ERROR severity blocks merge

  - PENETRATION-TEST-CHECKLIST.md
    - External firm engagement scope
    - Pre-test environment setup
    - Finding classification (P0-P4)
    - Remediation SLA (P0: 24h, P1: 72h, P2: 7d)
```

### 11.2 Performance Testing (05-Performance-Testing/) — P2

```yaml
Planned Documents:
  - LOCUST-LOAD-TEST-PLAN.md
    - 100K concurrent user simulation
    - Scenario: Registration → Login → Gate Evaluate → Evidence Upload
    - p95 latency targets per endpoint class
    - Database query benchmarks (<10ms SELECT, <50ms JOIN)

  - API-BENCHMARK-TARGETS.md
    - Gate evaluation: <100ms p95
    - Evidence upload (10MB): <2s
    - Dashboard load: <1s
    - Agent conversation send: <500ms p95
```

### 11.3 Accessibility Testing (06-Accessibility-Testing/) — P2

```yaml
Planned Documents:
  - WCAG-ACCESSIBILITY-TESTING.md
    - WCAG 2.1 AA compliance checklist
    - Screen reader test scenarios (NVDA, VoiceOver)
    - Keyboard navigation validation
    - Color contrast ratio verification (4.5:1 normal, 3:1 large)

  - LIGHTHOUSE-CI-CONFIG.md
    - Lighthouse score target: >90
    - Accessibility category: >95
    - CI integration (GitHub Actions)
```

### 11.4 Interface-Specific E2E Gaps

| Interface | Current State | Gap | Target Sprint |
|-----------|--------------|-----|---------------|
| Web | E2E-TEST-SCENARIOS.md (1,688 lines, TC-* IDs) | Complete | — |
| CLI | No documented E2E scenarios | Full CLI E2E suite needed | Sprint 214+ |
| Extension | 18 test files in `vscode-extension/src/test/suite/` | Document as MTP cases | Sprint 214+ |
| OTT | `admin_ott.py` (23 tests), `teams_normalizer` (18 tests) | Cross-channel parity tests | Sprint 214+ |

---

## 12. Framework Compliance Mapping (SDLC 6.1.1)

| SDLC 6.1.1 Requirement | MTP Coverage | Evidence |
|-------------------------|-------------|----------|
| Zero Mock Policy | Enforced | Pre-commit hook, CI gate |
| Test Pyramid (60/30/10) | Tracked | Unit 3,096 / Integ 993 / E2E 85 |
| Anti-Vibecoding (Section 7) | SPEC-0001 | Vibecoding Index scoring |
| Specification Standard (Section 8) | SPEC-0002 | YAML frontmatter + BDD |
| Evidence-Based Development | Evidence Vault | SHA256 integrity, 8-state lifecycle |
| Multi-Agent Governance | ADR-056 | 121 multi-agent test scenarios (TP-056) |
| Tier-Specific Requirements | ADR-059 | LITE/STANDARD/PRO/ENTERPRISE test coverage |
| OTT Channel Testing | Sprint 198+ | admin_ott.py (23 tests), teams_normalizer (18 tests) |
| CF-02 Resilience (503) | Sprint 198 | 12 endpoints: DB/service → 503 + Retry-After |
| CF-03 Auth Performance | Sprint 198 | bcrypt run_in_threadpool (3 endpoints) |
| Conversation-First Guard | Sprint 190 | ConversationFirstGuard middleware tested |
| 4-Interface Parity | **NEW v2.0.0** | 8 cross-interface workflows (WF-01 to WF-08) |
| OTT Command Registry | **NEW v2.0.0** | 10 commands tested (MTP-OTT-*, MTP-GATE-OTT-*) |
| Skills Engine (P3) | **NEW v2.1.0** | tsvector search, skill_agent_grants, 57 S218 tests |
| Agent Liveness (P6) | **NEW v2.1.0** | Heartbeat service, stale recovery, 61 S219 tests |
| Shared Workspace (P5) | **NEW v2.1.0** | Optimistic locking, version conflict, context injection |
| Approval Feedback (P4) | **NEW v2.1.0** | approve/reject with feedback, `<human_feedback>` injection, 30 S220 tests |
| Group Consensus (P2) | **NEW v2.1.0** | 3 quorum types, SELECT FOR UPDATE race protection, 45 S221 tests |
| ADR-070 Task Contract | **NEW v2.1.0** | EP-07 ↔ AgentScope interface: dispatch → execute → return → gate evaluate |
| Consensus Advisory INVARIANT | **NEW v2.1.0** | Consensus CANNOT bypass EP-07 gates (gate decides PASS/FAIL) |

---

## 13. Go-Live Readiness Checklist

| # | Check | Target | Status | Interface |
|---|-------|--------|--------|-----------|
| 1 | Unit test coverage | >95% | On track | Backend |
| 2 | Integration test coverage | >90% | On track | Backend |
| 3 | E2E critical paths | 10 journeys | 85+ scenarios | Web |
| 4 | p95 API latency | <100ms | 14.0ms PASS | All |
| 5 | OWASP ASVS L2 | 264/264 | 98.4% | All |
| 6 | Zero P0/P1 bugs | 0 | 0 | All |
| 7 | Security scan | PASS | Semgrep + Grype | Backend |
| 8 | Load test (100K) | <100ms p95 | Planned | Backend |
| 9 | AGPL containment | 0 violations | Pre-commit enforced | Backend |
| 10 | Quick-test baseline | 114 tests | Sprint 197 | Backend |
| 11 | CLI auth + core commands | 3 auth + 4 gate + 2 evidence | **NEW** | CLI |
| 12 | Extension core commands | 3 auth + 2 gate + 2 evidence | **NEW** | Extension |
| 13 | OTT webhook + 10 commands | Intake + routing + all 10 | **NEW** | OTT |
| 14 | Cross-interface parity | 4 P0 workflows (WF-01 to WF-03, WF-08) | **Updated v2.1.0** | Cross |
| 15 | ConversationFirstGuard | Admin-only write paths enforced | Sprint 190 | Web |
| 16 | Sprint 218-221 regression | 267 cumulative tests passing | **NEW v2.1.0** | Backend |
| 17 | Consensus advisory invariant | Gate authority NOT bypassed by consensus | **NEW v2.1.0** | Backend |

---

## 14. Revision History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 2.1.0 | 2026-03-05 | @tester | Sprint 218-221 coverage: +5 features (F-24 Skills, F-25 Heartbeat, F-26 Workspace, F-27 Feedback, F-28 Consensus), 28-feature matrix, WF-08 consensus workflow, +30 MTP test cases (~175 total), 267 cumulative sprint tests (S216-S221), +4 DB tables, ADR-070 traceability, consensus advisory INVARIANT documented |
| 2.0.0 | 2026-03-02 | @tester | Comprehensive rewrite: 14-section structure, 23-feature matrix × 4 interfaces, 7 cross-interface workflows, ~145 MTP test cases, 4-tier regression suite, per-interface test suites (Web/CLI/Extension/OTT), test data fixtures, CTO reviewed (6 corrections applied) |
| 1.0.0 | 2026-02-24 | @pm | Initial skeleton (Sprint 198 C-05) |

---

*SDLC Orchestrator — Zero facade tolerance. Real tests, real coverage, real quality. Test across all 4 interfaces.*
