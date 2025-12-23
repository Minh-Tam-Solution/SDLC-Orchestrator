# SASE - AI+Human Collaboration Principles
## Part of SDLC-Enterprise-Framework: How AI and Humans Work Together

**Version**: 1.0.0
**Date**: December 23, 2025
**Purpose**: External Expert Review - AI Governance Model
**Framework**: SDLC-Enterprise-Framework 5.1.1 + SASE (SE 3.0)

---

## 1. Overview

### Where SASE Fits

```
┌─────────────────────────────────────────────────────────────────────┐
│               SDLC-Enterprise-Framework 5.1.1                        │
│                     (The Methodology)                                │
├─────────────────────────────────────────────────────────────────────┤
│  • 10 Stages (00-09)                                                │
│  • 4 Tiers (LITE→ENTERPRISE)                                        │
│  • Quality Gates (G0.1→G4)                                          │
│  • SASE Integration ← THIS DOCUMENT                                 │
└─────────────────────────────────────────────────────────────────────┘
                              │
                    implements│
                              ▼
┌─────────────────────────────────────────────────────────────────────┐
│                     SDLC Orchestrator                                │
│                       (The Tool)                                     │
├─────────────────────────────────────────────────────────────────────┤
│  • AI Context Engine (stage-aware prompts)                          │
│  • BRS/MRP Template Generator                                       │
│  • AI Detection Service (80% accuracy)                              │
│  • Evidence Vault (captures SASE artifacts)                         │
└─────────────────────────────────────────────────────────────────────┘
```

**SASE (Software Agentic Software Engineering)** is a methodology within SDLC-Enterprise-Framework that defines how AI agents and human engineers collaborate. SDLC Orchestrator provides automation to make SASE adoption easier.

---

## 2. The Two Roles

### SE4H: Software Engineer for Humans (Agent Coach)

| Aspect | Description |
|--------|-------------|
| **Role** | Guide, supervise, and approve AI agent work |
| **Decision Authority** | FINAL - has veto power over all AI decisions |
| **Responsibilities** | Specify intent, set standards, review outputs, approve merges |
| **Artifacts Created** | BRS, MTS, VCR |

### SE4A: Software Engineer for Agents (Agent Executor)

| Aspect | Description |
|--------|-------------|
| **Role** | Execute human-specified tasks autonomously |
| **Decision Authority** | NONE - can only propose, never decide |
| **Responsibilities** | Create plans, execute code, generate evidence, escalate uncertainty |
| **Artifacts Created** | LPS, CRP, MRP |

---

## 3. The 7 Core Principles

### Principle 1: Brief-First

**"No agent work without a BriefingScript."**

| Aspect | Description |
|--------|-------------|
| **Rule** | Every AI task must start with a human-written BRS |
| **Why** | Ensures AI understands intent before executing |
| **Consequence** | AI without BRS produces inconsistent results |

### Principle 2: Evidence-Based MRP

**"5-point evidence for every merge."**

Every AI-generated code must provide:

| Evidence Point | Description |
|----------------|-------------|
| 1. Test Results | Passing tests with coverage metrics |
| 2. Linting | No warnings or errors |
| 3. Security Scan | No critical/high vulnerabilities |
| 4. Type Check | Full type coverage |
| 5. Documentation | Updated as needed |

### Principle 3: Human Accountability

**"Humans are responsible for shipped code."**

| Aspect | Description |
|--------|-------------|
| **Rule** | AI proposes, human approves and owns |
| **Why** | Legal and ethical accountability |
| **Consequence** | No "the AI did it" excuses |

### Principle 4: Consultation Protocol

**"When uncertain, ask the human."**

| Uncertainty Type | AI Action |
|------------------|-----------|
| Ambiguous requirements | Generate CRP, pause for human input |
| Multiple valid approaches | Present options in CRP, let human choose |
| Security-sensitive | Always escalate via CRP |
| Breaking change | CRP with impact analysis |

### Principle 5: Mentorship-as-Code

**"Standards encoded in MentorScript, not tribal knowledge."**

| Aspect | Description |
|--------|-------------|
| **Rule** | Team standards must be in MTS file |
| **Why** | AI can read and follow documented standards |
| **Consequence** | Consistent code regardless of which AI/human writes it |

### Principle 6: Dual Workbenches

**"Separate environments for humans and agents."**

| Workbench | Purpose |
|-----------|---------|
| **ACE** (Agent Coach Environment) | Human's IDE, review tools |
| **AEE** (Agent Executor Environment) | AI's sandbox, isolated execution |

### Principle 7: Gradual Autonomy

**"Trust is earned from L0 → L3."**

| Level | Autonomy | Trust Requirement |
|-------|----------|-------------------|
| L0 | Minimal (autocomplete) | None |
| L1 | Low (structured handoff) | Verified on 10+ tasks |
| L2 | Medium (full workflow) | Verified on 50+ tasks |
| L3 | High (proactive) | Verified on 200+ tasks |

---

## 4. The 6 SASE Artifacts

### Human-Created Artifacts

#### BRS (BriefingScript)

**Purpose**: Specify intent for AI task

```yaml
# Example BRS
task_id: "FEAT-001"
objective: "Add user authentication"
context:
  - "FastAPI backend"
  - "PostgreSQL database"
  - "JWT tokens required"
constraints:
  - "Must use bcrypt for hashing"
  - "Token expiry: 1 hour"
success_criteria:
  - "All tests pass"
  - "Security scan clean"
  - "API docs updated"
```

#### MTS (MentorScript)

**Purpose**: Encode team standards

```yaml
# Example MTS
code_style:
  language: python
  formatter: black
  linter: ruff
  max_line_length: 88

testing:
  min_coverage: 90
  framework: pytest
  require_types: true

security:
  secrets_in_vault: true
  sql_injection: parameterized_only
  xss: auto_escape

review:
  approvers_required: 2
  self_approve: false
```

#### VCR (Version Controlled Resolution)

**Purpose**: Approve or reject AI output

```yaml
# Example VCR
decision: APPROVED
reviewer: "tech_lead"
timestamp: "2025-12-23T10:00:00Z"
mpr_id: "MRP-001"
comments: |
  - Code quality: Excellent
  - Test coverage: 94% (above 90% threshold)
  - Security: No issues found
conditions:
  - "Must update README before merge"
```

### AI-Created Artifacts

#### LPS (LoopScript)

**Purpose**: Execution plan for task

```yaml
# Example LPS (AI-generated)
task_id: "FEAT-001"
steps:
  - name: "Create user model"
    files: ["models/user.py"]
    estimated_lines: 50

  - name: "Add authentication service"
    files: ["services/auth_service.py"]
    estimated_lines: 120

  - name: "Create API endpoints"
    files: ["api/routes/auth.py"]
    estimated_lines: 80

  - name: "Write tests"
    files: ["tests/test_auth.py"]
    estimated_lines: 150

dependencies: ["bcrypt", "python-jose"]
total_estimated_lines: 400
```

#### CRP (Consultation Request Protocol)

**Purpose**: Escalate uncertainty to human

```yaml
# Example CRP (AI-generated)
issue: "Multiple valid approaches for token storage"
options:
  - name: "HttpOnly cookies"
    pros: ["XSS-safe", "Automatic on requests"]
    cons: ["CSRF vulnerability", "Not for mobile"]

  - name: "LocalStorage"
    pros: ["Simple", "Works on mobile"]
    cons: ["XSS vulnerable"]

  - name: "Memory only"
    pros: ["Most secure"]
    cons: ["Lost on refresh"]

recommendation: "HttpOnly cookies (matches BRS security requirements)"
awaiting: "Human decision"
```

#### MRP (Merge-Readiness Pack)

**Purpose**: Evidence for merge approval

```yaml
# Example MRP (AI-generated)
evidence:
  tests:
    total: 45
    passed: 45
    failed: 0
    coverage: 94.2%

  linting:
    errors: 0
    warnings: 0
    tool: ruff

  security:
    critical: 0
    high: 0
    medium: 0
    tool: semgrep

  types:
    coverage: 100%
    errors: 0
    tool: mypy

  documentation:
    api_docs: updated
    readme: no_changes_needed

files_changed: 8
lines_added: 412
lines_removed: 12
```

---

## 5. Workflow Example

```
┌─────────────────────────────────────────────────────────────────────┐
│                    SASE WORKFLOW EXAMPLE                            │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  1. Human creates BRS                                               │
│     ↓                                                               │
│  2. AI reads BRS + MTS                                              │
│     ↓                                                               │
│  3. AI generates LPS (execution plan)                               │
│     ↓                                                               │
│  4. Human reviews LPS → Approved? Continue                          │
│     ↓                                                               │
│  5. AI executes code                                                │
│     ↓                                                               │
│  6. AI encounters uncertainty?                                      │
│     → YES: Generate CRP, wait for human                             │
│     → NO: Continue                                                  │
│     ↓                                                               │
│  7. AI generates MRP (evidence pack)                                │
│     ↓                                                               │
│  8. Human reviews MRP → Approved?                                   │
│     → YES: Create VCR (APPROVED), merge                             │
│     → NO: Create VCR (REJECTED), AI revises                         │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 6. Maturity Levels

| Level | Name | AI Capability | Human Involvement | Use Case |
|-------|------|---------------|-------------------|----------|
| **L0** | Tool-Assisted | Autocomplete, suggestions | Every keystroke | Learning, exploration |
| **L1** | Agent-Assisted | Task execution with handoff | Review every task | Most teams today |
| **L2** | Structured Agentic | Full SASE workflow | Review by exception | Mature teams |
| **L3** | Lifecycle Agentic | Proactive, memory | Strategic only | Future state |

### SDLC Orchestrator Target

**SDLC Orchestrator targets L1-L2 maturity**:
- L1: Task-level AI assistance with human approval
- L2: Sprint-level AI planning with gate-based human oversight

---

## 7. Why This Model?

### Problem: AI Without Governance

| Issue | Consequence |
|-------|-------------|
| AI generates code without context | Inconsistent with architecture |
| AI makes security decisions | Vulnerabilities introduced |
| AI works without evidence | No audit trail |
| AI output not reviewed | Bugs reach production |

### Solution: SASE Model

| Principle | Benefit |
|-----------|---------|
| Brief-First | AI understands intent before executing |
| Evidence-Based | Every change has proof of quality |
| Human Accountability | Clear ownership and liability |
| Consultation Protocol | Uncertainty handled systematically |
| Mentorship-as-Code | Standards applied consistently |
| Gradual Autonomy | Trust earned over time |

---

## 8. Questions for Expert Review

1. **Complexity**: Is the 6-artifact model (BRS, MTS, VCR, LPS, CRP, MRP) too complex for adoption?
2. **Maturity Levels**: Is the L0-L3 progression realistic?
3. **Human Overhead**: Does this model add too much human review burden?
4. **Tooling**: What tooling would make this model practical?
5. **Industry Comparison**: How does this compare to other AI governance models?

---

**Document Control**

| Field | Value |
|-------|-------|
| Author | NQH Holdings Framework Team |
| Status | Ready for External Review |

---

*"AI proposes, human approves, evidence proves."*
