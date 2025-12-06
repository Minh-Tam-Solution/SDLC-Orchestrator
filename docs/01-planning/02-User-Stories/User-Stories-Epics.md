# User Stories & Epics
## User Journeys and Acceptance Criteria

**Version**: 1.0.0
**Date**: January 13, 2025
**Status**: ACTIVE - DRAFT
**Authority**: PM + Product Owner Review (PENDING)
**Foundation**: FRD v1.0, User Personas (Stage 00)
**Stage**: Stage 01 (WHAT - Planning & Analysis)

---

## Document Purpose

This document defines user stories (WHO + WHAT + WHY) mapped to epics and functional requirements.

**Format**: As a [persona], I want [action], so that [benefit]

**Hierarchy**:
- **Epic**: Large body of work (e.g., "Gate Management")
- **Story**: User-facing functionality (e.g., "View gate status")
- **Task**: Technical implementation (Stage 02 scope)

---

## Epic Summary (10 Epics, 50+ Stories)

| Epic ID | Epic Name | Stories | Priority | FRs | Week |
|---------|-----------|---------|----------|-----|------|
| E1 | Gate Management | 8 | P0 | FR1 | 5-6 |
| E2 | Evidence Vault | 7 | P0 | FR2 | 6-7 |
| E3 | Policy Packs | 6 | P0 | FR3 | 9-10 |
| E4 | AI Context Engine | 8 | P0 | FR6-FR10 | 7-8 |
| E5 | Dashboard | 6 | P1 | FR4 | 8-9 |
| E6 | VS Code Extension | 5 | P0 | FR5 | 6-7 |
| E7 | Integrations | 6 | P1 | FR11-FR15 | 7-8 |
| E8 | User Management | 4 | P1 | - | 9 |
| E9 | Reports & Analytics | 3 | P2 | FR16-FR20 | Post-MVP |
| E10 | Mobile App | 3 | P2 | FR21 | Post-MVP |

---

## E1: Gate Management (8 Stories)

### US1.1: View Gate Status
**Story**: As an EM, I want to view gate status for my projects, so that I know which gates are blocked and need attention.

**Acceptance Criteria**:
- [ ] Dashboard shows list of all gates (G0.1-G6)
- [ ] Gate status color-coded (🔴 BLOCKED, 🟡 PENDING, 🟢 PASSED)
- [ ] Clicking gate shows detailed policy evaluation results
- [ ] Response time <200ms (NFR1)

**Related FR**: FR1.5 (Gate Status Dashboard)

---

### US1.2: Evaluate Gate
**Story**: As an EM, I want to manually trigger gate evaluation, so that I can check if my team has met gate criteria.

**Acceptance Criteria**:
- [ ] "Evaluate Gate" button visible on gate detail page
- [ ] Evaluation completes <500ms for 10 policies (NFR2)
- [ ] Result shows PASS/FAIL for each policy
- [ ] Notification sent to team on status change

**Related FR**: FR1.2 (Gate Evaluation)

---

### US1.3: Override Gate (CTO Only)
**Story**: As a CTO, I want to manually override blocked gates with justification, so that projects can proceed in exceptional circumstances.

**Acceptance Criteria**:
- [ ] "Override Gate" button visible only to CTO role (RBAC)
- [ ] Override requires reason (50-500 characters, mandatory)
- [ ] CEO receives notification email when gate overridden
- [ ] Override expires after 7 days (auto-revert)
- [ ] Audit log records override (who, when, why)

**Related FR**: FR1.3 (Gate Override)

---

### US1.4: Configure Gate Criteria
**Story**: As an Admin, I want to configure gate criteria (select policy packs), so that gates match our team's SDLC process.

**Acceptance Criteria**:
- [ ] Admin can select 1-20 policy packs for each gate
- [ ] Changes versioned (can rollback to previous criteria)
- [ ] Projects using old criteria see migration warning

**Related FR**: FR1.1 (Gate Definition)

---

### US1.5: View Gate Dependency Chain
**Story**: As an EM, I want to see gate dependencies (G0.1 → G0.2 → G1), so that I know which gates to complete first.

**Acceptance Criteria**:
- [ ] Dashboard shows dependency flowchart (visual graph)
- [ ] Warning shown if evaluating gate out of order
- [ ] Cannot skip critical gates (G0.1, G1 required)

**Related FR**: FR1.4 (Gate Dependency Chain)

---

### US1.6: Receive Gate Status Notifications
**Story**: As an EM, I want Slack notifications when gate status changes, so that I'm alerted without checking dashboard constantly.

**Acceptance Criteria**:
- [ ] Notification sent when gate BLOCKED → PASSED
- [ ] Notification sent when gate PASSED → BLOCKED (regression)
- [ ] Notification includes clickable link to gate details
- [ ] User can configure notification preferences (email vs Slack)

**Related FR**: FR19 (Notifications)

---

### US1.7: View Gate History
**Story**: As a CTO, I want to view gate evaluation history, so that I can track project progress over time.

**Acceptance Criteria**:
- [ ] Gate detail page shows evaluation history (last 30 days)
- [ ] Timeline view: Date | Status | Evaluator | Reason (if overridden)
- [ ] Export to CSV for reporting

**Related FR**: FR18 (Reports)

---

### US1.8: Bulk Gate Evaluation
**Story**: As a CTO, I want to evaluate all gates for all projects (bulk action), so that I can get org-wide compliance snapshot.

**Acceptance Criteria**:
- [ ] "Evaluate All Gates" button (CTO only)
- [ ] Progress bar shows evaluation status (5/50 gates complete)
- [ ] Completes <5 minutes for 50 gates (10 projects × 5 gates)

**Related FR**: FR1.2 (Gate Evaluation)

---

## E2: Evidence Vault (7 Stories)

### US2.1: Upload Evidence Manually
**Story**: As a PM, I want to upload evidence (PDFs, images), so that gate evaluation has required proof.

**Acceptance Criteria**:
- [ ] Drag-and-drop file upload (max 10MB)
- [ ] Supported formats: PDF, PNG, JPG, DOCX, XLSX
- [ ] Virus scan (ClamAV) before storage (reject infected files)
- [ ] Upload completes <2s for 10MB file (NFR3)

**Related FR**: FR2.3 (Evidence Manual Upload)

---

### US2.2: Auto-Collect Evidence from Slack
**Story**: As a PM, I want evidence auto-collected from Slack messages, so that I don't manually upload user interview notes.

**Acceptance Criteria**:
- [ ] Slack integration setup (OAuth, 5 min)
- [ ] System monitors #product, #design channels (configurable)
- [ ] Keywords: "user interview", "feedback", "validation"
- [ ] Evidence appears in vault <1 minute after Slack message

**Related FR**: FR2.1 (Evidence Auto-Collection Slack)

---

### US2.3: Auto-Collect Evidence from GitHub
**Story**: As an Engineer, I want PRs auto-collected as evidence, so that G3 (Build) has proof of code review.

**Acceptance Criteria**:
- [ ] GitHub integration setup (GitHub App, 10 min)
- [ ] PR opened → evidence created (type: github_pr)
- [ ] Evidence includes: PR description, code diff (10KB max), review comments

**Related FR**: FR2.2 (Evidence Auto-Collection GitHub)

---

### US2.4: Search Evidence
**Story**: As a CTO, I want to search evidence by keyword, so that I can find user interview transcripts during SOC 2 audit.

**Acceptance Criteria**:
- [ ] Full-text search (fuzzy matching for typos)
- [ ] Filters: Project, Gate, Date range, Evidence type
- [ ] Search completes <200ms for 10K records (NFR1)
- [ ] Results ranked by relevance, snippets highlighted

**Related FR**: FR2.4 (Evidence Search)

---

### US2.5: View Evidence Audit Trail
**Story**: As a CTO, I want to see who accessed evidence, so that I can verify compliance for SOC 2 audit.

**Acceptance Criteria**:
- [ ] Audit log shows: User, Action (view/download/delete), Timestamp, IP
- [ ] Audit log immutable (cannot delete/modify)
- [ ] Audit log retained 7 years (NFR17)
- [ ] Export audit log to CSV

**Related FR**: FR2.5 (Evidence Audit Trail)

---

### US2.6: Organize Evidence by Gate
**Story**: As a PM, I want evidence organized by gate (G0.1, G1, G2), so that I quickly see what's missing.

**Acceptance Criteria**:
- [ ] Evidence Vault sidebar shows gates as folders
- [ ] Each gate shows evidence count (e.g., G0.1: 5 items)
- [ ] Missing evidence highlighted (e.g., "Need 2 more user interviews")

**Related FR**: FR4.3 (Evidence Completeness Meter)

---

### US2.7: Share Evidence Externally
**Story**: As a PM, I want to generate shareable link for evidence, so that I can share user interview with stakeholders outside SDLC Orchestrator.

**Acceptance Criteria**:
- [ ] "Share" button generates time-limited link (exp 7 days)
- [ ] Link accessible without login (public URL)
- [ ] Shared link logged in audit trail

**Related FR**: FR2 (Evidence Vault)

---

## E3: Policy Packs (6 Stories)

### US3.1: Browse Pre-Built Policy Library
**Story**: As an Admin, I want to browse 100+ pre-built SDLC 4.8 policies, so that I can quickly configure gates without writing Rego code.

**Acceptance Criteria**:
- [ ] Policy library organized by stage (Stage 00-06)
- [ ] Each policy shows: Name, Description, Rego preview
- [ ] Search policies by keyword

**Related FR**: FR3.5 (Pre-Built Policy Pack Library)

---

### US3.2: Create Custom Policy Pack
**Story**: As an Admin, I want to write custom policy pack (Rego), so that gates enforce our team-specific rules.

**Acceptance Criteria**:
- [ ] VS Code-like editor (syntax highlighting, autocomplete)
- [ ] Rego syntax validation before save
- [ ] Policy pack versioned (Git, semantic versioning)

**Related FR**: FR3.1 (Policy Pack Definition), FR3.3 (Policy Pack Editor)

---

### US3.3: Test Policy Pack
**Story**: As an Admin, I want to test policy with sample evidence, so that I verify logic before deploying to production gates.

**Acceptance Criteria**:
- [ ] Test sandbox (doesn't affect production)
- [ ] Sample evidence (JSON, mimics real structure)
- [ ] Test result shows PASS/FAIL + reason

**Related FR**: FR3.2 (Policy Pack Testing)

---

### US3.4: Version Policy Pack
**Story**: As an Admin, I want to version policy packs (1.0.0, 1.1.0, 2.0.0), so that I can rollback if policy breaks gates.

**Acceptance Criteria**:
- [ ] Semantic versioning (major.minor.patch)
- [ ] Git commit for each version
- [ ] Gates can pin policy version (don't auto-upgrade)

**Related FR**: FR3.4 (Policy Pack Versioning)

---

### US3.5: Clone Pre-Built Policy
**Story**: As an Admin, I want to clone pre-built policy and customize, so that I can tweak SDLC 4.8 policies for our process.

**Acceptance Criteria**:
- [ ] "Clone" button on pre-built policy
- [ ] Cloned policy becomes custom (can edit)
- [ ] Original pre-built policy unchanged

**Related FR**: FR3.5 (Pre-Built Policy Pack Library)

---

### US3.6: View Policy Usage
**Story**: As an Admin, I want to see which gates use each policy, so that I understand impact before deleting policy.

**Acceptance Criteria**:
- [ ] Policy detail page shows "Used by X gates"
- [ ] Cannot delete policy if gates using it (soft delete)
- [ ] Warning before policy version upgrade (if gates affected)

**Related FR**: FR3.1 (Policy Pack Definition)

---

## E4: AI Context Engine (8 Stories)

### US4.1: Generate PRD from Interviews
**Story**: As a PM, I want AI to generate PRD from 5 user interview transcripts, so that I save 14 hours of manual writing.

**Acceptance Criteria**:
- [ ] Upload 5 PDFs (interview transcripts)
- [ ] AI generates PRD <3 minutes (NFR)
- [ ] PRD 80%+ complete (PM refines 20%)
- [ ] PRD includes: Problem, Personas, FRs, Success Metrics

**Related FR**: FR6.1 (AI PRD Generation)

---

### US4.2: AI Design Review
**Story**: As an Engineer, I want AI to review my design doc for SDLC 4.8 compliance, so that I catch missing elements before CTO review.

**Acceptance Criteria**:
- [ ] Upload design doc (PDF, Markdown, Figma URL)
- [ ] AI reviews against gate criteria (G2)
- [ ] AI generates report: Issues, Compliance score, Suggestions
- [ ] Review completes <3 minutes

**Related FR**: FR6.2 (AI Design Review)

---

### US4.3: Generate Test Plan
**Story**: As a QA Lead, I want AI to generate test plan from FRD, so that I save 6 hours creating test cases.

**Acceptance Criteria**:
- [ ] AI reads FRD (FR1-FR20)
- [ ] AI generates 100 test cases (5 per FR)
- [ ] Test plan 70%+ complete
- [ ] Test cases categorized: Unit, Integration, E2E

**Related FR**: FR6.3 (AI Test Plan Generation)

---

### US4.4: AI Stage-Aware Assistant
**Story**: As a PM, I want AI to answer questions based on current stage (Stage 00 = WHY focus), so that I get contextual help.

**Acceptance Criteria**:
- [ ] Chat interface in dashboard
- [ ] AI knows current stage (e.g., "You're in Stage 00, focus on WHY")
- [ ] AI suggests next steps (e.g., "Run 2 more user interviews for G0.1")

**Related FR**: FR6.4 (AI Stage-Aware Prompts)

---

### US4.5: AI Multi-Provider Fallback
**Story**: As a User, I want AI to automatically switch providers if Claude is down, so that AI features remain available.

**Acceptance Criteria**:
- [ ] Primary: Claude Sonnet 4.5 (92% accuracy)
- [ ] Fallback: GPT-4o (78% accuracy)
- [ ] Warning shown: "Using GPT-4o (Claude unavailable)"
- [ ] AI availability 99.9% (NFR11)

**Related FR**: FR6.5 (AI Multi-Provider Strategy)

---

### US4.6: AI Context Memory
**Story**: As a PM, I want AI to remember previous conversations, so that I don't repeat context in every chat.

**Acceptance Criteria**:
- [ ] AI stores conversation history (last 30 days)
- [ ] AI references previous context (e.g., "As we discussed yesterday...")
- [ ] User can clear conversation history

**Related FR**: FR6 (AI Context Engine)

---

### US4.7: AI Prompt Customization
**Story**: As an Admin, I want to customize AI prompts, so that AI matches our team's terminology.

**Acceptance Criteria**:
- [ ] Admin can edit stage-aware prompts
- [ ] Prompt changes versioned (can rollback)
- [ ] Prompt preview before save

**Related FR**: FR6.4 (AI Stage-Aware Prompts)

---

### US4.8: AI Cost Tracking
**Story**: As an Admin, I want to track AI API costs, so that I stay within $350/month budget.

**Acceptance Criteria**:
- [ ] Dashboard shows: Claude cost, GPT-4o cost, Gemini cost
- [ ] Alert when 80% of budget used
- [ ] Option to disable AI if budget exceeded

**Related FR**: FR6.5 (AI Multi-Provider Strategy)

---

## Story Mapping (User Journey)

### Journey 1: EM Validates Feature Idea (Stage 00)

```
User Journey: EM wants to validate Feature X before sprint planning

┌─────────────────────────────────────────────────────────────┐
│ Stage 00: WHY - Problem Validation                         │
└─────────────────────────────────────────────────────────────┘
   ↓
US2.1: Upload user interview transcripts (5 PDFs)
   ↓
US4.1: AI generates PRD from interviews (3 min)
   ↓
US1.2: Evaluate gate G0.1 (Problem Definition)
   ↓
   ├─ BLOCKED → US2.6: View missing evidence (need 2 more interviews)
   │    ↓
   │  US2.1: Upload 2 more interview transcripts
   │    ↓
   │  US1.2: Re-evaluate gate G0.1
   │    ↓
   └─ PASSED → US1.6: Slack notification "G0.1 PASSED"
         ↓
      US1.5: View next gate (G0.2 Solution Diversity)
```

**Time Savings**:
- Without SDLC Orchestrator: 16 hours (manual PRD writing)
- With SDLC Orchestrator: 2 hours (AI PRD + review)
- **Savings**: 14 hours (87.5%)

---

## Story Estimation (Story Points)

**Fibonacci Scale**: 1, 2, 3, 5, 8, 13, 21

| Epic | Total Story Points | Velocity (2 weeks) | Sprints |
|------|-------------------|--------------------|---------|
| E1: Gate Management | 21 | 20 | 2 sprints |
| E2: Evidence Vault | 34 | 20 | 3 sprints |
| E3: Policy Packs | 21 | 20 | 2 sprints |
| E4: AI Context | 34 | 20 | 3 sprints |
| E5: Dashboard | 13 | 20 | 1 sprint |
| E6: VS Code Ext | 13 | 20 | 1 sprint |
| Total MVP | 136 | 20 | **12 sprints (6 months)** |

**Note**: Roadmap targets 90 days (3 months) = aggressive but achievable with 8.5 FTE team.

---

## Document Control

**Version History**:
- v1.0.0 (January 13, 2025): Initial user stories (50+ stories, 10 epics)

**Related Documents**:
- [FRD](../01-Requirements/Functional-Requirements-Document.md)
- [User Personas](../../00-Project-Foundation/03-Design-Thinking/User-Personas.md)

---

**End of User Stories v1.0.0**
