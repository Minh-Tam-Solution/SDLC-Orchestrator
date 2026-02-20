# SDLC 6.1.0 DOCUMENT NAMING STANDARDS
## SDLC Orchestrator Platform Documentation Guidelines

**SDLC Version**: 5.1.3 - 7-Pillar Architecture
**Stage**: Stage 09 (GOVERN - Governance & Compliance)
**Purpose**: Enforce permanent, feature-based naming standards across all documentation
**Authority**: SDLC 6.1.0 Document Governance Framework (DGF) - **MANDATORY ENFORCEMENT**
**Last Updated**: January 18, 2026
**Status**: ✅ ACTIVE - All teams must comply

---

## EXECUTIVE SUMMARY

### What is SDLC Orchestrator?

**SDLC Orchestrator is NOT just another project** - it is the **tool that implements SDLC 6.1.0 Framework automatically** for software development projects. Think of it as:

```yaml
SDLC 6.1.0 Framework = The Methodology (Rules, Stages, Gates)
SDLC Orchestrator = The Tool (Automation, Enforcement, Tracking)

Analogy:
  - Scrum = Methodology
  - Jira = Tool that implements Scrum

  - SDLC 6.1.0 = Methodology
  - SDLC Orchestrator = Tool that implements SDLC 6.1.0
```

### Platform Purpose

| Aspect | Description |
|--------|-------------|
| **What it does** | Automates SDLC 6.1.0 compliance for software teams |
| **Core Features** | Gate management, Evidence vault, Policy enforcement |
| **Target Users** | Development teams, Project managers, CTOs |
| **Problem Solved** | 60-70% feature waste → <30% through governance |
| **Unique Value** | First tool to implement SDLC 6.1.0 natively |

### Naming Problem Statement

**Problem**: Temporal naming (Sprint-33, Day-1, V4.8, NOV17-2025) creates:
- 70% document refactoring overhead after sprint completion
- 85% reduction in long-term discoverability
- 100% obsolete references within 6-12 months
- Technical debt accumulation in documentation

**Solution**: SDLC 6.1.0 **Permanent Naming Standards**:
- Feature-based, descriptive names (WHAT, not WHEN)
- Temporal context INSIDE document header (Sprint, Date, Version)
- AI-parseable, systematic structure
- Sustainable for 5+ years without refactoring

---

## MANDATORY RULES

### NEVER USE (Temporal Elements in Filenames)

```yaml
BANNED Patterns:
  ❌ Sprint numbers: SPRINT-33-, Sprint-35-, S34-
  ❌ Day numbers: DAY-1-, Day-2-, D01-
  ❌ Dates: NOV17-2025, 2025-11-17, 20251117
  ❌ Versions in filename: V4.8, V9.1, v2.3
  ❌ Phases: PHASE-1-, Phase-II-, P3-
  ❌ Iterations: ITERATION-3-, Iter-5-
  ❌ Quarters: Q1-2026-, Q2-, FY2025-

BAD Examples:
  ❌ SPRINT-10-GATE-ENGINE-IMPLEMENTATION.md
  ❌ DAY-2-DATABASE-DESIGN-NOV18-2025.md
  ❌ EVIDENCE-VAULT-API-V4.8-SPRINT10.md
  ❌ Q1-2026-FRONTEND-DASHBOARD-WIREFRAMES.md
```

### CORRECT FORMAT (Permanent, Feature-Based)

```yaml
REQUIRED Patterns:
  ✅ Describes WHAT (feature, component, module)
  ✅ Systematic structure (Module-Component-Type)
  ✅ Kebab-case format (lowercase with hyphens)
  ✅ Temporal context INSIDE document header
  ✅ AI-parseable and discoverable
  ✅ Makes sense in 1-5 years

GOOD Examples:
  ✅ GATE-ENGINE-ARCHITECTURE.md
  ✅ EVIDENCE-VAULT-API-SPECIFICATION.md
  ✅ POLICY-EVALUATION-SERVICE-DESIGN.md
  ✅ DASHBOARD-WIREFRAMES-PROJECT-LIST.md
  ✅ AI-CONTEXT-ENGINE-INTEGRATION.md
```

### Temporal Context Goes INSIDE Document

```markdown
# GATE ENGINE ARCHITECTURE

**SDLC Version**: 4.9 - Complete 10-Stage Lifecycle
**Stage**: Stage 02 (HOW - Design Architecture)
**Sprint**: Sprint 10 (Nov 17-30, 2025)  ← Temporal info HERE
**Module**: Gate Engine
**Component**: System Architecture
**Author**: Backend Lead
**Status**: In Progress
**Version**: 1.0  ← INSIDE DOCUMENT, NOT FILENAME
```

---

## SDLC ORCHESTRATOR NAMING CONVENTIONS

### Module Prefixes (Platform Components)

```yaml
Gate Management (FR1):
  GATE-         Gate Engine core functionality
  GATE-API-     Gate REST API specifications
  GATE-UI-      Gate dashboard components
  GATE-POLICY-  Policy evaluation logic

Evidence Vault (FR2):
  EVIDENCE-     Evidence Vault core
  EVIDENCE-API- Evidence REST API
  EVIDENCE-UI-  Evidence upload components
  EVIDENCE-HASH- SHA256 integrity

AI Context Engine (FR3):
  AI-           AI Context Engine core
  AI-PROMPT-    Stage-aware prompts
  AI-PROVIDER-  Multi-provider integration
  AI-COST-      Cost optimization

Dashboard (FR4):
  DASHBOARD-    Dashboard core
  DASHBOARD-UI- Dashboard components
  DASHBOARD-WS- WebSocket updates

Policy Library (FR5):
  POLICY-       Policy Pack Library
  POLICY-OPA-   OPA Rego policies
  POLICY-YAML-  YAML policy definitions

Infrastructure:
  AUTH-         Authentication service
  DATABASE-     Database design
  API-          REST API specifications
  SECURITY-     Security implementation
  DEVOPS-       CI/CD and deployment
```

### Component Types (Suffixes)

```yaml
Design Documents (Stage 02):
  -ARCHITECTURE.md      System architecture design
  -API-SPECIFICATION.md RESTful API specs
  -DATABASE-SCHEMA.md   Database design & ERD
  -WIREFRAMES.md        UI/UX wireframes
  -SEQUENCE-DIAGRAM.md  Sequence diagrams

Implementation Documents (Stage 03):
  -IMPLEMENTATION-GUIDE.md  Implementation instructions
  -CODE-STRUCTURE.md        Code organization
  -SERVICE-DESIGN.md        Service layer design

Testing Documents (Stage 04):
  -TEST-SCENARIOS.md    Test cases & scenarios
  -TEST-COVERAGE.md     Test coverage metrics
  -E2E-TEST-PLAN.md     End-to-end test plan

Deployment Documents (Stage 05):
  -DEPLOYMENT-GUIDE.md  Deployment procedures
  -RUNBOOK.md           Operations runbook
  -ROLLBACK-PLAN.md     Rollback procedures

Compliance Documents (Stage 09):
  -COMPLIANCE-CHECKLIST.md  Compliance verification
  -AUDIT-REPORT.md          Audit findings
```

---

## DIRECTORY STRUCTURE BY SDLC STAGE

### Stage 00 (WHY - Foundation)
**Location**: `/docs/00-Project-Foundation/`

```
✅ MISSION-VISION-VALUES.md
✅ PROBLEM-STATEMENT.md
✅ SOLUTION-HYPOTHESIS.md
✅ MARKET-OPPORTUNITY.md
✅ PRODUCT-ROADMAP.md
```

### Stage 01 (WHAT - Planning)
**Location**: `/docs/01-Planning-Analysis/`

```
✅ FUNCTIONAL-REQUIREMENTS.md (FR1-FR5)
✅ API-SPECIFICATION.md
✅ DATA-MODEL.md
✅ USER-STORIES.md
```

### Stage 02 (HOW - Design)
**Location**: `/docs/02-Design-Architecture/`

```
✅ SYSTEM-ARCHITECTURE-DOCUMENT.md
✅ TECHNICAL-DESIGN-DOCUMENT.md
✅ SECURITY-BASELINE.md
✅ ADR-001-DATABASE-CHOICE.md
✅ ADR-007-AI-CONTEXT-ENGINE.md
✅ openapi.yml (API contract)
```

### Stage 04 (BUILD - Development|
**Location**: `/docs/03-Development-Implementation/`

```
✅ SPRINT-EXECUTION-PLAN.md (exception: sprint management)
✅ CODE-STANDARDS-PYTHON.md
✅ CODE-STANDARDS-TYPESCRIPT.md
✅ ZERO-MOCK-POLICY.md
```

### Stage 08 (COLLABORATE - Team Management)
**Location**: `/docs/08-Team-Management/`

**Exception - Sprint Management Documents** (ONLY location allowed to use temporal prefixes):
```
✅ /04-Sprint-Management/SPRINT-10-KICKOFF.md
✅ /04-Sprint-Management/SPRINT-10-DAILY-PROGRESS.md
```

**SDLC Compliance Documents** (Permanent naming):
```
✅ /03-SDLC-Compliance/SDLC-4.9-COMPLIANCE-GUIDE.md
✅ /03-SDLC-Compliance/SDLC-ORCHESTRATOR-COMPLIANCE.md
✅ /03-SDLC-Compliance/CLAUDE-CODE-SDLC-ORCHESTRATOR.md
✅ /03-SDLC-Compliance/SDLC-DOCUMENT-NAMING-STANDARDS.md
```

---

## SDLC ORCHESTRATOR-SPECIFIC EXAMPLES

### Gate Engine Documentation

```yaml
CORRECT Naming:
  ✅ docs/02-Design-Architecture/GATE-ENGINE-ARCHITECTURE.md
  ✅ docs/02-Design-Architecture/GATE-API-SPECIFICATION.md
  ✅ docs/02-Design-Architecture/GATE-EVALUATION-SERVICE-DESIGN.md
  ✅ docs/04-Testing-Quality/GATE-INTEGRATION-TEST-SCENARIOS.md

WRONG Naming:
  ❌ docs/02-Design-Architecture/SPRINT-10-GATE-ENGINE-DESIGN.md
  ❌ docs/02-Design-Architecture/GATE-API-V1.0-NOV2025.md
```

### Evidence Vault Documentation

```yaml
CORRECT Naming:
  ✅ docs/02-Design-Architecture/EVIDENCE-VAULT-ARCHITECTURE.md
  ✅ docs/02-Design-Architecture/EVIDENCE-API-SPECIFICATION.md
  ✅ docs/02-Design-Architecture/EVIDENCE-SHA256-INTEGRITY.md
  ✅ docs/02-Design-Architecture/EVIDENCE-MINIO-INTEGRATION.md

WRONG Naming:
  ❌ docs/02-Design-Architecture/PHASE-2-EVIDENCE-VAULT.md
  ❌ docs/02-Design-Architecture/WEEK-5-EVIDENCE-IMPLEMENTATION.md
```

### Dashboard Documentation

```yaml
CORRECT Naming:
  ✅ docs/02-Design-Architecture/12-UI-UX-Design/FRONTEND-DESIGN-SPECIFICATION.md
  ✅ docs/02-Design-Architecture/12-UI-UX-Design/DASHBOARD-WIREFRAMES.md
  ✅ docs/02-Design-Architecture/12-UI-UX-Design/DESIGN-EVIDENCE-LOG.md

WRONG Naming:
  ❌ docs/02-Design-Architecture/12-UI-UX-Design/SPRINT-9-DASHBOARD-DESIGN.md
  ❌ docs/02-Design-Architecture/12-UI-UX-Design/V2-WIREFRAMES-DEC2025.md
```

---

## NAMING DECISION TREE

```
Question 1: Is this a permanent design/implementation document?
├── YES → Use permanent naming (GATE-ENGINE-ARCHITECTURE.md)
└── NO → Continue to Question 2

Question 2: Is this a sprint/project management tracking document?
├── YES → Is it in /docs/08-Team-Management/04-Sprint-Management/?
│   ├── YES → OK to use SPRINT-[NUMBER]- prefix
│   └── NO → Move to Sprint Management folder OR use permanent naming
└── NO → Continue to Question 3

Question 3: Is this a temporary analysis/report for specific event?
├── YES → Move to /docs/10-Archive/ with date in folder name
└── NO → Use permanent naming
```

### Example Decision Flow

```
Document: "Gate Engine Implementation Design for Sprint 10"

Q1: Permanent design doc? YES
→ Use: GATE-ENGINE-IMPLEMENTATION-DESIGN.md
→ Location: /docs/02-Design-Architecture/
→ Sprint info goes INSIDE document header:

  **Sprint**: Sprint 10 (Week 10, Nov 27-Dec 3, 2025)
  **Status**: In Progress
```

---

## COMPLIANCE CHECKLIST

### Before Creating New Document

- [ ] Filename uses permanent, feature-based naming (no Sprint/Day/Date)
- [ ] Filename is descriptive and will make sense in 1-5 years
- [ ] Filename follows Module-Component-Type pattern
- [ ] Filename uses kebab-case (lowercase with hyphens)
- [ ] Document header includes SDLC 6.1.0 mandatory fields
- [ ] Sprint/Date info is INSIDE document, not in filename
- [ ] Document is in correct `/docs/[Stage]/` folder

### Exception - Sprint Management Documents

- [ ] If document is in `/docs/08-Team-Management/04-Sprint-Management/`, SPRINT- prefix is OK
- [ ] All other locations MUST use permanent naming

### After Creating Document

- [ ] Document added to relevant README.md index
- [ ] Internal references use permanent names
- [ ] Git commit message explains naming rationale

---

## BENEFITS REALIZATION

### Short-Term (Current Sprint)

- ✅ Zero document refactoring after sprint completion
- ✅ Design documents immediately usable in future sprints
- ✅ Clear separation: permanent design docs vs temporary tracking docs

### Medium-Term (Q1 2026)

- ✅ 70% reduction in "Where is this document?" questions
- ✅ 85% improvement in AI-assisted code generation (clear doc references)
- ✅ 100% design documents reusable across sprints

### Long-Term (2026+)

- ✅ Permanent documentation library (5+ years relevant)
- ✅ Zero obsolete references (no Sprint-33 in 2027!)
- ✅ Scalable to 100+ components without naming conflicts

---

## SUPPORT & ENFORCEMENT

### Enforcement

- GitHub pre-commit hook validates naming standards
- CI/CD pipeline checks for temporal naming violations
- Code review includes document naming compliance
- Monthly audit reports (compliance metrics)

### Questions

Reference this document: `SDLC-DOCUMENT-NAMING-STANDARDS.md`
Escalate to CTO Office for clarifications

---

## Document Information

**Document**: SDLC-DOCUMENT-NAMING-STANDARDS.md
**Status**: ACTIVE - MANDATORY ENFORCEMENT
**Authority**: SDLC 6.1.0 Document Governance Framework (DGF)
**Last Updated**: November 27, 2025
**Next Review**: Gate G3 (Jan 31, 2026)

---

**SDLC 6.1.0 Compliance**: ✅ Complete 10-Stage Lifecycle Framework
**Enforcement**: GitHub hooks + CI/CD validation + Code review
**Benefits**: 70% refactoring reduction, 85% discoverability improvement

---

**PERMANENT NAMING = PERMANENT VALUE!**
