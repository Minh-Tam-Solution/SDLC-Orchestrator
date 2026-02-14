# PHASE-04: SDLC Structure Validator
## Folder Compliance CLI & CI/CD Gates

**Version**: 2.0.0
**Date**: December 5, 2025
**Status**: ✅ **COMPLETE** - Sprint 29-30
**Duration**: 10 days (Dec 2-6, 2025)
**Final Rating**: **9.7/10**
**Owner**: Backend Lead + DevOps Team
**Framework**: SDLC 5.1.3 Complete Lifecycle
**Prerequisites**: PHASE-01, PHASE-02, PHASE-03 Complete

---

## Executive Summary

PHASE-04 implements the **SDLC Structure Validator** - a CLI tool and CI/CD gate that enforces SDLC 5.1.3 folder structure compliance across all projects. This ensures every project in the NQH portfolio follows the standardized 10-stage lifecycle documentation structure with **4-Tier Classification** (LITE, STANDARD, PROFESSIONAL, ENTERPRISE).

### What's New in v2.0.0

| Feature | SDLC 5.1.3.1 | SDLC 5.1.3 |
|---------|-----------|-----------|
| Project Tiers | Single structure | 4-Tier Classification |
| Stage 08 | Team-Management | Team-Management + Collaboration Standards |
| Industry Standards | None | ISO/IEC, CMMI, SAFe, DORA, SRE, ITIL |
| P0 Artifacts | N/A | 15 AI-discoverability artifacts |
| Legacy Handling | Manual | 10-archive/{NN}-Legacy with AI-NEVER-READ directive |

**Key Deliverables**:
1. SDLC Validator CLI (`sdlcctl validate`)
2. Pre-commit Hook Template
3. CI/CD Pipeline Gate (GitHub Actions)
4. Web UI Compliance Report

**Success Criteria**:
- Validation <10s for large projects (1000+ files)
- 100% accuracy on SDLC 5.1.3.1 folder structure
- Pre-commit hook <2s (developer UX)
- CI/CD gate with detailed violation report

---

## 1. Problem Statement

### Current State (Before PHASE-04)

**Pain Points**:
1. **Inconsistent Structure**: 5 NQH projects have different folder structures
2. **Manual Enforcement**: CEO manually reviews folder structure (not scalable)
3. **Late Discovery**: Structure violations found at code review (too late)
4. **No Tooling**: No automated way to validate SDLC compliance

**Evidence from PM/PJM Handover**:
| Project | Compliance | Issues |
|---------|------------|--------|
| Bflow Platform | 100% | Reference standard |
| SDLC-Orchestrator | 85% | `docs/guides/`, `docs/research/` non-compliant |
| NQH-Bot | 90% | Stage 06 naming wrong |
| SOP-Generator | 90% | Stage 05 naming wrong |
| AI-Platform | 70% | Duplicate Stage 05 folders |

### Target State (After PHASE-04)

- All projects 100% SDLC 5.1.3.1 compliant
- Violations blocked at commit time (pre-commit)
- CI/CD prevents non-compliant merges
- Dashboard shows real-time compliance status

---

## 2. Technical Architecture

### 2.1 SDLC 5.1.3 Folder Structure (4-Tier Classification)

```yaml
# 4-Tier Classification (SDLC 5.1.3)
LITE (1-2 people):
  - Required Stages: 00, 01, 02, 03
  - Optional: 04-10
  - Max Depth: Level 1

STANDARD (3-10 people):
  - Required Stages: 00, 01, 02, 03, 04, 05
  - Optional: 06-10
  - Max Depth: Level 2

PROFESSIONAL (10-50 people):
  - Required Stages: 00-09 (All except 10-Archive)
  - Required P0: 15 artifacts for AI discoverability
  - Max Depth: Level 3

ENTERPRISE (50+ people):
  - Required Stages: 00-10 (All stages)
  - Required: Industry compliance (ISO/IEC, CMMI, SOC2)
  - Max Depth: Level 4+

# Stage Naming Standard (EXACT - SDLC 5.1.3)
Stage Naming:
  00-Project-Foundation      # WHY stage
  01-Planning-Analysis       # WHAT stage
  02-Design-Architecture     # HOW stage
  03-Development-Implementation  # BUILD stage
  04-Testing-Quality         # TEST stage
  05-Deployment-Release      # DEPLOY stage (NOT "Deployment-Operations")
  06-Operations-Maintenance  # OPERATE stage (NOT "Maintenance-Support")
  07-Integration-APIs        # INTEGRATE stage
  08-Team-Management         # COLLABORATE stage (NEW: Team Collaboration Standards)
  09-Executive-Reports       # GOVERN stage
  10-Archive                 # Archive stage

# P0 Artifacts (15 Required for PROFESSIONAL+)
P0_Artifacts:
  Framework:
    - SDLC-Executive-Summary.md
    - SDLC-Core-Methodology.md
    - README.md (root entry point)
    - CHANGELOG.md
  Project:
    - docs/README.md (docs entry point)
    - CURRENT-SPRINT.md
    - Product-Roadmap.md
    - Functional-Requirements-Document.md
    - openapi.yml
  Stage:
    - Stage README.md (each stage)

# Legacy Handling (SDLC 6.0.5 - RFC-001)
Legacy:
  Location: docs/10-archive/{NN}-Legacy/
  Directive: AI-NEVER-READ
  Purpose: Historical reference only, not for active development
```

### 2.2 Validator Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    SDLC STRUCTURE VALIDATOR                     │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐ │
│  │ CLI Tool        │  │ Pre-commit Hook │  │ CI/CD Gate      │ │
│  │ (sdlcctl)       │  │ (bash/python)   │  │ (GitHub Action) │ │
│  │                 │  │                 │  │                 │ │
│  │ - validate      │  │ - block commit  │  │ - block PR      │ │
│  │ - fix           │  │ - show errors   │  │ - detailed log  │ │
│  │ - report        │  │ - auto-fix      │  │ - badge status  │ │
│  └────────┬────────┘  └────────┬────────┘  └────────┬────────┘ │
│           │                    │                    │           │
│           └────────────────────┴────────────────────┘           │
│                                │                                 │
│                    ┌───────────┴───────────┐                    │
│                    │ Validation Engine     │                    │
│                    │                       │                    │
│                    │ - Load .sdlc-config   │                    │
│                    │ - Scan folder tree    │                    │
│                    │ - Check stage names   │                    │
│                    │ - Validate levels     │                    │
│                    │ - Generate report     │                    │
│                    └───────────────────────┘                    │
│                                │                                 │
│                    ┌───────────┴───────────┐                    │
│                    │ Rules Engine          │                    │
│                    │                       │                    │
│                    │ - Stage naming rules  │                    │
│                    │ - Level depth rules   │                    │
│                    │ - Required folders    │                    │
│                    │ - Forbidden patterns  │                    │
│                    └───────────────────────┘                    │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 2.3 Configuration Schema

```json
// .sdlc-config.json (project root)
{
  "$schema": "https://sdlc-orchestrator.io/schema/v2/sdlc-config.json",
  "version": "5.0.0",
  "tier": "professional",
  "team_size": 25,
  "docs_root": "docs",
  "stages": {
    "enabled": ["00", "01", "02", "03", "04", "05", "06", "07", "08", "09"],
    "required": ["00", "01", "02", "03", "04", "05", "06", "07", "08", "09"]
  },
  "rules": {
    "enforce_naming": true,
    "enforce_levels": true,
    "max_depth": 3,
    "require_readme": true,
    "require_p0_artifacts": true,
    "legacy_handling": "10-archive"
  },
  "p0_artifacts": {
    "framework": ["SDLC-Executive-Summary.md", "SDLC-Core-Methodology.md", "README.md", "CHANGELOG.md"],
    "project": ["docs/README.md", "CURRENT-SPRINT.md", "Product-Roadmap.md", "Functional-Requirements-Document.md", "openapi.yml"],
    "stage": ["README.md"]
  },
  "tier_requirements": {
    "lite": { "min_stages": 4, "p0_required": false },
    "standard": { "min_stages": 6, "p0_required": false },
    "professional": { "min_stages": 10, "p0_required": true },
    "enterprise": { "min_stages": 11, "p0_required": true, "compliance": ["iso27001", "soc2"] }
  },
  "ignore_patterns": [
    "**/node_modules/**",
    "**/.git/**",
    "**/dist/**",
    "**/10-archive/**"
  ],
  "custom_stages": {}
}
```

---

## 3. CLI Tool Specification

### 3.1 Installation

```bash
# Via pip
pip install sdlcctl

# Via npm (wrapper)
npm install -g @sdlc-orchestrator/cli

# Via Homebrew
brew install sdlc-orchestrator/tap/sdlcctl
```

### 3.2 Commands

**sdlcctl validate**
```bash
# Validate current directory
sdlcctl validate

# Validate specific path
sdlcctl validate --path /path/to/project

# With verbose output
sdlcctl validate --verbose

# Output as JSON
sdlcctl validate --format json

# Exit codes:
# 0 = valid
# 1 = violations found
# 2 = config error
```

**sdlcctl fix**
```bash
# Auto-fix violations (rename folders)
sdlcctl fix

# Dry-run (show what would be fixed)
sdlcctl fix --dry-run

# Interactive mode
sdlcctl fix --interactive
```

**sdlcctl init**
```bash
# Initialize .sdlc-config.json
sdlcctl init

# With project size
sdlcctl init --size large

# Generate folder structure
sdlcctl init --scaffold
```

**sdlcctl report**
```bash
# Generate compliance report
sdlcctl report --output report.html

# JSON format
sdlcctl report --format json --output report.json
```

### 3.3 Output Examples

**Validation Success**:
```
✅ SDLC 5.1.3 Structure Validation: PASSED

Project: SDLC-Orchestrator
Tier: PROFESSIONAL (25 people)
Docs Root: docs/

Stages Found: 10/10
  ✅ 00-Project-Foundation (14 files) - WHY
  ✅ 01-Planning-Analysis (15 files) - WHAT
  ✅ 02-Design-Architecture (28 files) - HOW
  ✅ 03-Development-Implementation (32 files) - BUILD
  ✅ 04-Testing-Quality (8 files) - TEST
  ✅ 05-Deployment-Release (5 files) - DEPLOY
  ✅ 06-Operations-Maintenance (4 files) - OPERATE
  ✅ 07-Integration-APIs (6 files) - INTEGRATE
  ✅ 08-Team-Management (3 files) - COLLABORATE
  ✅ 09-Executive-Reports (12 files) - GOVERN

P0 Artifacts: 15/15 ✅
  ✅ SDLC-Executive-Summary.md
  ✅ SDLC-Core-Methodology.md
  ✅ README.md (root)
  ✅ CHANGELOG.md
  ✅ docs/README.md
  ✅ CURRENT-SPRINT.md
  ✅ Product-Roadmap.md
  ✅ Functional-Requirements-Document.md
  ✅ openapi.yml
  ✅ Stage READMEs (10/10)

Legacy: docs/10-archive/ (Excluded - AI-NEVER-READ directive)

Total: 129 files validated
Time: 1.2s
```

**Validation Failure**:
```
❌ SDLC 5.1.3 Structure Validation: FAILED

Project: NQH-Bot
Tier: STANDARD (8 people)
Docs Root: docs/

Violations Found: 3

1. ❌ Stage 06 naming violation
   Found: 06-Maintenance-Support
   Expected: 06-Operations-Maintenance
   Fix: Rename folder

2. ❌ Missing required stage
   Missing: 09-Executive-Reports
   Fix: Create folder (or upgrade to STANDARD tier which requires only 6 stages)

3. ⚠️ P0 Artifact missing (Warning for STANDARD tier)
   Missing: docs/README.md
   Recommendation: Add for AI discoverability

Run 'sdlcctl fix' to auto-fix these violations.
Run 'sdlcctl init --tier standard' to reconfigure project tier.
```

---

## 4. Pre-commit Hook

### 4.1 Hook Installation

```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/sdlc-orchestrator/pre-commit-hooks
    rev: v1.0.0
    hooks:
      - id: sdlc-validate
        name: SDLC Structure Validation
        entry: sdlcctl validate --strict
        language: python
        types: [directory]
        always_run: true
```

### 4.2 Hook Behavior

```bash
# On git commit (if violations found)
$ git commit -m "Add feature"

SDLC Structure Validation.............................Failed

❌ SDLC 5.1.3.1 Structure Validation: FAILED

Violations Found: 1
  ❌ docs/research/ is not a valid stage folder

Run 'sdlcctl fix' or move to valid stage.

Commit blocked. Fix violations before committing.
```

---

## 5. CI/CD Gate (GitHub Actions)

### 5.1 Workflow Definition

```yaml
# .github/workflows/sdlc-validate.yml
name: SDLC Structure Validation

on:
  push:
    branches: [main, develop]
    paths:
      - 'docs/**'
  pull_request:
    branches: [main]
    paths:
      - 'docs/**'

jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Install SDLC CLI
        run: pip install sdlcctl

      - name: Validate Structure
        run: sdlcctl validate --strict --format json > validation.json

      - name: Upload Report
        uses: actions/upload-artifact@v4
        with:
          name: sdlc-validation-report
          path: validation.json

      - name: Comment on PR
        if: github.event_name == 'pull_request'
        uses: actions/github-script@v7
        with:
          script: |
            const report = require('./validation.json');
            const status = report.valid ? '✅ PASSED' : '❌ FAILED';
            const body = `## SDLC Structure Validation: ${status}\n\n${report.summary}`;
            github.rest.issues.createComment({
              issue_number: context.issue.number,
              owner: context.repo.owner,
              repo: context.repo.repo,
              body: body
            });
```

### 5.2 Branch Protection

```yaml
# Required status check
Branch protection rules:
  - Require status checks: sdlc-validate
  - Require branches to be up to date: true
```

---

## 6. Web UI Report

### 6.1 Compliance Dashboard Component

```
┌──────────────────────────────────────────────────────────────────┐
│ SDLC Structure Compliance                                       │
├──────────────────────────────────────────────────────────────────┤
│                                                                  │
│ ┌─────────────────────┐ ┌─────────────────────┐                 │
│ │ Overall Compliance  │ │ Projects            │                 │
│ │      87%            │ │ 4 / 5 compliant     │                 │
│ │  ███████████░░░     │ │ 1 needs attention   │                 │
│ └─────────────────────┘ └─────────────────────┘                 │
│                                                                  │
│ Project Status                                                   │
│ ┌────────────────────────────────────────────────────────────┐  │
│ │ Bflow Platform      ████████████████████  100%  ✅          │  │
│ │ SDLC-Orchestrator   █████████████████░░░  100%  ✅          │  │
│ │ NQH-Bot             ███████████████████░  90%   ⚠️ 1 issue  │  │
│ │ SOP-Generator       ███████████████████░  90%   ⚠️ 1 issue  │  │
│ │ AI-Platform         ██████████████░░░░░░  70%   ❌ 3 issues │  │
│ └────────────────────────────────────────────────────────────┘  │
│                                                                  │
│ [Run Validation] [View Details] [Download Report]               │
└──────────────────────────────────────────────────────────────────┘
```

### 6.2 API Endpoint

**POST /projects/{id}/validate-structure**
```json
{
  "config": {
    "project_size": "large",
    "strict_mode": true
  }
}

// Response
{
  "valid": true,
  "score": 100,
  "stages": {
    "00-Project-Foundation": { "valid": true, "files": 14 },
    "01-Planning-Analysis": { "valid": true, "files": 15 }
  },
  "violations": [],
  "recommendations": [],
  "validated_at": "2025-01-15T10:30:00Z"
}
```

---

## 7. Implementation Plan

### Sprint 29 (Week 1): Core CLI

**Day 1-2: Validation Engine**
- Implement folder tree scanner
- Create stage name validator
- Add level depth checker
- Unit tests (95%+ coverage)

**Day 3-4: CLI Tool**
- Create `sdlcctl` CLI (typer-based)
- Implement `validate`, `fix`, `init` commands
- Add JSON/text output formatters
- Integration tests

**Day 5: Pre-commit Hook**
- Create pre-commit hook package
- Test with sample projects
- Documentation

### Sprint 30 (Week 2): CI/CD & Web

**Day 1-2: CI/CD Gate**
- Create GitHub Action
- Add PR commenting
- Branch protection setup
- Multi-repo testing

**Day 3-4: Web Integration**
- Create validation API endpoint
- Build compliance dashboard component
- Add project-level reports
- E2E tests

**Day 5: Polish & Rollout**
- Documentation finalization
- Rollout to 5 NQH projects
- Fix violations found
- CTO approval

---

## 8. Success Criteria

### Performance Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| Validation time (1000 files) | <10s | CLI timing |
| Pre-commit hook | <2s | Git hook timing |
| CI/CD validation | <30s | GitHub Action timing |
| API response | <1s | API latency |

### Quality Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| Detection accuracy | 100% | Manual validation |
| False positive rate | 0% | User reports |
| Auto-fix success | >95% | Fix command success |

### Adoption Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| Projects with pre-commit | 5/5 | Config file presence |
| Projects with CI gate | 5/5 | Workflow presence |
| Compliance score (avg) | 100% | Dashboard |

---

## 9. Rollout Plan

### Week 1 (Sprint 29): Development & Testing
- Build CLI and validation engine
- Test on SDLC-Orchestrator (self)
- Fix any issues found

### Week 2 (Sprint 30): Integration & Pilot
- Add CI/CD gate
- Pilot on Bflow Platform
- Gather feedback

### Week 3: Full Rollout
- Roll out to all 5 NQH projects
- Fix all violations (100% compliance)
- Documentation & training

---

## 10. References

- [ADR-014: SDLC Structure Validator](../../02-design/01-ADRs/ADR-014-SDLC-Validator.md)
- [SDLC 5.1.3 Framework](../../../SDLC-Enterprise-Framework/)
- [Product Roadmap v3.0.0](../../00-Project-Foundation/04-Roadmap/Product-Roadmap.md)
- [Sprint 29 Detailed Plan](../02-Sprint-Plans/SPRINT-29-SDLC-VALIDATOR-CLI.md)
- [Sprint 30 Detailed Plan](../02-Sprint-Plans/SPRINT-30-CICD-WEB-INTEGRATION.md)

---

## 11. Sprint Breakdown

### Sprint 29: Core CLI & Validation Engine (Jan 6-10, 2026)

**Duration**: 5 days
**Team**: 2 Backend, 1 DevOps
**Goal**: Build core CLI tool with SDLC 5.1.3 validation engine

| Day | Focus | Deliverables |
|-----|-------|--------------|
| Day 1 | Validation Engine Core | Folder scanner, tier detector, stage validator |
| Day 2 | P0 Artifact Checker | 15 P0 artifacts validation, legacy exclusion |
| Day 3 | CLI Tool (sdlcctl) | validate, fix, init commands |
| Day 4 | Pre-commit Hook | Hook package, integration tests |
| Day 5 | Testing & Documentation | Unit tests (95%+), README, examples |

**Success Criteria**:
- ✅ CLI validates SDLC 5.1.3 structure in <10s (1000+ files)
- ✅ 4-tier classification working (LITE/STANDARD/PROFESSIONAL/ENTERPRISE)
- ✅ P0 artifacts checked for PROFESSIONAL+ tiers
- ✅ Pre-commit hook blocks non-compliant commits

**Detailed Plan**: [SPRINT-29-SDLC-VALIDATOR-CLI.md](../02-Sprint-Plans/SPRINT-29-SDLC-VALIDATOR-CLI.md)

---

### Sprint 30: CI/CD Gate & Web Integration (Jan 13-17, 2026)

**Duration**: 5 days
**Team**: 2 Backend, 1 DevOps, 1 Frontend
**Goal**: Add CI/CD pipeline gate and web dashboard integration

| Day | Focus | Deliverables |
|-----|-------|--------------|
| Day 1 | GitHub Action | Workflow template, PR commenting |
| Day 2 | CI/CD Integration | Branch protection, multi-repo testing |
| Day 3 | Web API Endpoint | POST /projects/{id}/validate-structure |
| Day 4 | Dashboard Component | Compliance dashboard, tier visualization |
| Day 5 | Rollout & Polish | NQH portfolio rollout, documentation finalization |

**Success Criteria**:
- ✅ GitHub Action validates on PR/push to docs/**
- ✅ API endpoint returns validation results in <1s
- ✅ Dashboard shows compliance status per project
- ✅ All 5 NQH projects at 100% compliance

**Detailed Plan**: [SPRINT-30-CICD-WEB-INTEGRATION.md](../02-Sprint-Plans/SPRINT-30-CICD-WEB-INTEGRATION.md)

---

**Document Status**: ✅ APPROVED - Ready for Sprint 29-30
**Last Updated**: December 5, 2025
**Version**: 2.0.0 (SDLC 5.1.3 upgrade)
**Owner**: Backend Lead + DevOps + CTO
