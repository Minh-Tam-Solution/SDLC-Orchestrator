# EP-05: SDLC Version Migration Engine (Pro/Enterprise)

**Status:** PROPOSED  
**Created:** December 21, 2025  
**Owner:** Platform Team  
**Priority:** P2 (follows EP-04)  
**Tier:** Pro/Enterprise Feature  
**Budget:** $15,000 (estimated 89 SP)

---

## Executive Summary

Automate large-scale SDLC version migration (e.g., 4.9 → 5.1) for enterprise projects with thousands of files. Derived from **real-world implementation** at Bflow Platform (Dec 2025), where CTO created custom tooling to upgrade compliance across 5,000+ files.

**Key Insight:** This is NOT just a documentation update—it requires:
- Scanning all files (Python, Markdown, YAML, etc.)
- Validating headers against target SDLC version
- Auto-fixing version, stage, component, status fields
- Parallel processing for large codebases (5,000+ files)
- Team compliance documentation generation

---

## Problem Statement

### Current State (Without SDLC Orchestrator)

#### Pain Point 1: Manual Compliance Oversight

> **"Without Orchestrator, CTO/CPO/PJM must periodically monitor and remind team members (AI or Human) to read and comply with SDLC."**

| Oversight Task | Frequency | Time/Week | Who |
|----------------|-----------|-----------|-----|
| Review PRs for SDLC compliance | Daily | 2-4 hours | Tech Lead |
| Remind team to check docs before coding | Weekly | 30 min | PJM |
| Spot-check AI-generated code compliance | Daily | 1-2 hours | Senior Dev |
| Update compliance docs when SDLC changes | Per release | 8+ hours | CTO |
| Onboard new members on SDLC standards | Per hire | 4 hours | Tech Lead |
| **Total Manual Oversight** | - | **~15 hours/week** | Multiple |

**Problems with Manual Oversight:**
- 😓 **Fatigue**: CTO/PJM can't review every commit
- 🔄 **Drift**: Team gradually deviates from standards
- 🤖 **AI Blindspot**: AI tools (Cursor, Copilot) don't know SDLC rules
- 📚 **Stale Docs**: Compliance docs become outdated
- ⏰ **Reactive**: Violations caught late (in PR review, not at coding time)

#### Pain Point 2: Manual Project-Specific Compliance Documentation

Instead of requiring team to read entire SDLC Framework (300+ files), CTO creates a **project-specific compliance folder** focusing on what matters for that project:

```
# Bflow Example: Manual compliance folder (2 weeks to create, 700KB)
docs/08-collaborate/03-SDLC-Compliance/
├── README.md                    # "I want to..." navigation
├── Core-Methodology/            # Subset of SDLC Framework
├── Situation-Specific-Guides/   # Project-specific guides
├── Quick-Reference/             # Cheatsheets
└── SDLC-5.1-UPGRADE-SUMMARY.md  # Migration notes
```

**Problems:**
- 📝 Manual creation: 2 weeks CTO time
- 🔄 Manual sync: Must update when Framework changes
- 📦 Duplication: 700KB copied content per project
- 👀 Still requires reading: Team must know to check docs

**With SDLC Orchestrator:** `.sdlc-config.json` replaces the manual folder:

```bash
# Initialize project-specific SDLC config
sdlcctl init --project "Bflow Platform" --tier professional --version 5.1

# Or auto-detect from existing project
sdlcctl scan --generate-config
```

```json
// .sdlc-config.json - Project-specific SDLC compliance (auto-generated)
{
  "$schema": "https://sdlc-orchestrator.io/schemas/sdlc-config-v1.json",
  "version": "1.0.0",
  "sdlc_version": "5.1.0",
  
  "project": {
    "name": "Bflow Platform",
    "tier": "professional",      // LITE | STANDARD | PROFESSIONAL | ENTERPRISE
    "team_size": 11,
    "maturity_level": "L1"       // L0 | L1 | L2 | L3 (Agentic Maturity)
  },
  
  "structure": {
    "docs_root": "docs",
    "stages": ["00", "01", "02", "03", "04", "05", "06", "07", "08", "09"],
    "naming": "short",           // "short" (00-foundation) or "long" (00-Project-Foundation)
    "legacy_folders": ["10-archive", "99-legacy"]
  },
  
  "validation": {
    "strict_naming": true,
    "require_headers": true,
    "required_header_fields": ["Version", "Date", "Stage", "Status"],
    "min_compliance_rate": 90,
    "auto_fix_enabled": true
  },
  
  "enforcement": {
    "pre_commit_hook": true,
    "github_action": true,
    "block_on_violation": true,
    "allow_override": ["CTO", "Tech Lead"]  // VCR override roles
  },
  
  "ai_safety": {
    "detect_ai_code": true,
    "require_ai_review": true,
    "ai_tools": ["cursor", "copilot", "claude_code", "chatgpt"]
  }
}
```

**Benefits of `.sdlc-config.json`:**

| Aspect | Manual Folder | `.sdlc-config.json` |
|--------|---------------|---------------------|
| Creation | 2 weeks | 5 seconds (`sdlcctl init`) |
| Size | 700KB | 1KB |
| Maintenance | Manual sync | Auto-validated |
| Reading required | Yes (team must read docs) | No (enforced by tools) |
| AI awareness | None | Tools use config |
| Version control | Difficult to diff | Easy JSON diff |

#### Pain Point 3: SDLC Version Migration

When upgrading SDLC version (e.g., 4.9 → 5.1) for a large project:

| Task | Manual Effort | Error Rate |
|------|--------------|------------|
| Scan all files for compliance | 8+ hours | 15-20% missed |
| Update version fields | 16+ hours | 5-10% typos |
| Update stage fields | 8+ hours | 10-15% wrong stage |
| Update cross-references | 4+ hours | 5% broken links |
| Update `.sdlc-config.json` | 1 min | 0% (CLI handles) |
| **Total** | **44+ hours** | **~35% error rate** |

### Target State (With SDLC Orchestrator)

```
┌─────────────────────────────────────────────────────────────────┐
│          SDLC Orchestrator: Automated Compliance                │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  BEFORE (Manual)              AFTER (Orchestrator)              │
│  ───────────────              ────────────────────              │
│                                                                 │
│  CTO creates 700KB folder →   `sdlcctl init` creates 1KB config │
│  CTO reminds team weekly  →   Pre-commit hook blocks bad code   │
│  PJM spot-checks PRs      →   GitHub Action auto-reviews        │
│  "Did you read the docs?" →   `sdlcctl explain` on-demand       │
│  Compliance docs 700KB    →   `.sdlc-config.json` (1KB)         │
│  AI ignores SDLC rules    →   AI-generated code auto-validated  │
│  Violations found in PR   →   Violations blocked at commit      │
│                                                                 │
│  Time: 15 hrs/week        →   Time: 0 hrs/week (automated)      │
│  Coverage: ~60% (human)   →   Coverage: 100% (every commit)     │
│  Latency: Hours/Days      →   Latency: Seconds (real-time)      │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

**CTO/CPO/PJM Benefits:**
- ✅ **No manual reminders** - Orchestrator enforces automatically
- ✅ **No PR compliance reviews** - GitHub Action handles it
- ✅ **No "did you read docs?"** - VS Code shows rules inline
- ✅ **No compliance drift** - Pre-commit blocks violations
- ✅ **No AI blindspot** - All AI-generated code validated
- ✅ **No stale docs** - On-demand delivery always current

### Evidence: Bflow Platform Migration (Dec 2025)

```
Project: Bflow Platform
Size: 5,000+ files (Python, Markdown, YAML)
Migration: SDLC 4.9 → 5.1
Team Size: 11 members (6 Remote + 5 Local)

What CTO Built:
├── tools/sdlc51-compliance/
│   ├── scanner.py (17KB) - Main scanning engine
│   ├── parallel_scanner.py (9KB) - Multi-process for large codebases
│   ├── cli.py (17KB) - Command-line interface
│   ├── config/
│   │   └── sdlc_stages.py - Stage definitions & mappings
│   ├── parsers/
│   │   ├── markdown_parser.py - MD header parsing
│   │   └── python_parser.py - Python docstring parsing
│   ├── validators/
│   │   ├── stage_validator.py - Stage compliance check
│   │   └── version_validator.py - Version compliance check
│   ├── fixers/
│   │   ├── version_fixer.py - Auto-upgrade version
│   │   ├── stage_fixer.py - Auto-fix stage field
│   │   ├── header_fixer.py - Add missing headers
│   │   ├── field_fixer.py - Add missing fields
│   │   ├── legacy_converter.py - Convert old formats
│   │   └── backup_manager.py - Safe backup before fixes
│   └── reporters/
│       ├── json_reporter.py - JSON output
│       └── markdown_reporter.py - MD report
│
└── docs/08-Team-Management/03-SDLC-Compliance/
    ├── README.md (15KB) - ONE FOLDER navigation hub
    ├── Core-Methodology/ - What is SDLC 5.1?
    ├── SASE-Artifacts/ - How to work with AI agents?
    ├── Governance-Compliance/ - What are the rules?
    ├── Documentation-Standards/ - How to document?
    ├── Situation-Specific-Guides/ - What to do in X?
    ├── Quick-Reference/ - Fast lookup
    └── SDLC-5.1-UPGRADE-SUMMARY.md (10KB)

Time Spent: ~2 weeks (CTO + 1 Senior Dev)
Result: 100% compliance achieved
```

### Target State (Automated with SDLC Orchestrator)

```bash
# One command to migrate entire project
sdlcctl migrate --from 4.9 --to 5.1 --project /path/to/project

# Output:
Scanning project: Bflow-Platform
Files found: 5,234 (2,156 Python, 3,078 Markdown)
Parallel workers: 8

Progress: [████████████████████] 100% (5,234/5,234)
Time elapsed: 2m 34s

MIGRATION SUMMARY:
✅ Version upgraded: 4,892 files
✅ Stage corrected: 342 files  
✅ Headers added: 89 files
✅ Fields completed: 1,247 files
⚠️ Manual review needed: 23 files (complex headers)

Compliance Report: reports/sdlc51/migration-2025-12-21.md
Team Documentation: docs/08-Team-Management/03-SDLC-Compliance/

Total time: 2 minutes 34 seconds (vs 44+ hours manual)
```

---

## Solution Architecture

### Core Components

```
┌─────────────────────────────────────────────────────────────┐
│                SDLC Migration Engine (EP-05)                │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────┐   ┌──────────────┐   ┌─────────────────┐  │
│  │   Scanner   │───│   Validator  │───│     Fixer       │  │
│  │   Engine    │   │    Engine    │   │    Engine       │  │
│  └──────┬──────┘   └──────┬───────┘   └────────┬────────┘  │
│         │                 │                     │           │
│  ┌──────┴──────┐   ┌──────┴───────┐   ┌────────┴────────┐  │
│  │   Parsers   │   │  Validators  │   │     Fixers      │  │
│  │ - Python    │   │ - Version    │   │ - Version       │  │
│  │ - Markdown  │   │ - Stage      │   │ - Stage         │  │
│  │ - YAML      │   │ - Component  │   │ - Header        │  │
│  │ - JSON      │   │ - Status     │   │ - Field         │  │
│  └─────────────┘   └──────────────┘   │ - Legacy        │  │
│                                       │ - Backup        │  │
│  ┌─────────────────────────────────┐  └─────────────────┘  │
│  │       Parallel Processor        │                       │
│  │  (5,000+ files, 8+ workers)     │                       │
│  └─────────────────────────────────┘                       │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │              Team Documentation Generator           │   │
│  │  - README.md (navigation hub)                       │   │
│  │  - Core-Methodology/ (what is SDLC X.Y?)           │   │
│  │  - Situation-Specific-Guides/ (what to do in X?)   │   │
│  │  - Quick-Reference/ (cheatsheets)                  │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### SDLC Version Configuration

> **Decision:** SDLC Orchestrator uses **short folder naming convention** (e.g., `00-foundation`) for simplicity and consistency across all project sizes. Legacy long names are supported via `folder_aliases`.

```yaml
# config/sdlc_versions/5.1.yaml
version: "5.1.0"
release_date: "2025-12-11"

# SDLC 5.1 Stage Definitions (10 stages) - Short Naming Convention
# Reference: SDLC-Enterprise-Framework/02-Core-Methodology/Documentation-Standards/SDLC-Document-Naming-Standards.md
stages:
  "00":
    name: "Foundation"
    category: "WHY"
    folder: "00-foundation"
    description: "Design Thinking + Business Case"
  "01":
    name: "Planning"
    category: "WHAT"
    folder: "01-planning"
    description: "Requirements + User Stories"
  "02":
    name: "Design"
    category: "HOW"
    folder: "02-design"
    description: "Architecture + ADRs"
  "03":
    name: "Integrate"
    category: "INTEGRATE"
    folder: "03-integrate"
    description: "API Contracts + Third-party"
  "04":
    name: "Build"
    category: "BUILD"
    folder: "04-build"
    description: "Development + Sprint Plans"
  "05":
    name: "Test"
    category: "TEST"
    folder: "05-test"
    description: "QA + Test Reports"
  "06":
    name: "Deploy"
    category: "DEPLOY"
    folder: "06-deploy"
    description: "Release + Deployment Guides"
  "07":
    name: "Operate"
    category: "OPERATE"
    folder: "07-operate"
    description: "Runbooks + Monitoring"
  "08":
    name: "Collaborate"
    category: "COLLABORATE"
    folder: "08-collaborate"
    description: "Team + Training"
  "09":
    name: "Govern"
    category: "GOVERN"
    folder: "09-govern"
    description: "Compliance + Executive Reports"

# Legacy/Long Folder Name Aliases
# Maps old verbose names to standard short names
folder_aliases:
  # Long names → short names
  "00-Project-Foundation": "00"
  "01-Planning-Analysis": "01"
  "02-Design-Architecture": "02"
  "03-Integration-APIs": "03"
  "04-Development-Implementation": "04"
  "05-Testing-Quality": "05"
  "06-Deployment-Release": "06"
  "07-Operations-Maintenance": "07"
  "08-Team-Management": "08"
  "09-Executive-Reports": "09"
  # Old SDLC 4.x naming patterns
  "05-Deployment-Operations": "06"
  "06-Maintenance-Support": "07"
  # Typo handling
  "00-Project-Foundations": "00"

header_requirements:
  python:
    required_fields: ["Version", "Date", "Stage", "Component", "Status"]
    optional_fields: ["Author", "Sprint", "Reference"]
    format: "docstring"
  markdown:
    required_fields: ["Version", "Date", "Stage", "Status"]
    optional_fields: ["Author", "Sprint", "Component"]
    format: "frontmatter_or_header"

upgrade_paths:
  "4.9": 
    compatible: true
    auto_fix: true
    field_mapping:
      stage_names:
        "DEPLOYMENT-OPERATIONS": "DEPLOYMENT (RELEASE)"
        "MAINTENANCE-SUPPORT": "OPERATIONS (OPERATE)"
  "5.0":
    compatible: true
    auto_fix: true
    new_features:
      - "SASE Artifacts"
      - "Agentic Maturity Model"
```

---

## Feature Breakdown

### Feature 1: Multi-File Scanner Engine

**Purpose:** Scan entire codebase for SDLC compliance

**Capabilities:**
- Python docstring parsing
- Markdown header parsing (frontmatter + inline)
- YAML/JSON config file parsing
- Parallel processing (8+ workers)
- Progress tracking with ETA
- Chunked processing for memory efficiency

**CLI:**
```bash
# Scan entire project
sdlcctl scan /path/to/project --target-version 5.1

# Scan specific folder
sdlcctl scan docs/ --format json --output reports/compliance.json

# CI mode (fail if < 90% compliance)
sdlcctl scan --ci --min-compliance 90
```

### Feature 2: Version Migration Engine

**Purpose:** Upgrade SDLC version across all files

**Capabilities:**
- Version field auto-upgrade
- Stage field auto-correction
- Component field derivation from path
- Status field normalization
- Backup before changes
- Dry-run mode

**CLI:**
```bash
# Preview migration (dry-run)
sdlcctl migrate --from 4.9 --to 5.1 --dry-run

# Execute migration
sdlcctl migrate --from 4.9 --to 5.1

# Migrate specific stage
sdlcctl migrate --from 4.9 --to 5.1 --stage 02
```

### Feature 3: Header Fixer Engine

**Purpose:** Add/fix SDLC headers in files

**Capabilities:**
- Add missing headers (Python docstrings, MD headers)
- Add missing fields to existing headers
- Convert legacy formats
- Smart stage derivation from file path

**CLI:**
```bash
# Fix all headers
sdlcctl fix headers --target-version 5.1

# Add missing fields only
sdlcctl fix fields --target-version 5.1

# Convert legacy headers
sdlcctl fix legacy --format sdlc51
```

### Feature 4: Real-Time Compliance (Replaces Manual Documentation)

> **Key Insight:** With SDLC Orchestrator, teams **NO LONGER NEED** to create manual compliance documentation folders like Bflow's `03-SDLC-Compliance/` (700KB, 38 files). Instead, compliance knowledge is delivered **on-demand** through:

**Bflow Approach (Legacy - Without Orchestrator):**
```
docs/08-collaborate/03-SDLC-Compliance/
├── README.md (15KB)           # Manual navigation hub
├── Core-Methodology/          # Manual copy from Framework
├── Situation-Specific-Guides/ # Manual guides
├── Quick-Reference/           # Manual cheatsheets
└── ... (700KB, 38 files, 2 weeks to create)
```

**SDLC Orchestrator Approach (Automated):**
```
┌─────────────────────────────────────────────────────────────┐
│              SDLC Compliance Delivery Methods               │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  1️⃣ VS Code Extension (Real-Time)                          │
│     ├── Inline warnings on SDLC violations                 │
│     ├── Quick-fix suggestions (click to fix)               │
│     ├── Hover tooltips with stage/naming rules             │
│     └── Command palette: "SDLC: Validate File"             │
│                                                             │
│  2️⃣ CLI Tool (On-Demand)                                   │
│     ├── sdlcctl scan         # Check compliance            │
│     ├── sdlcctl validate     # Validate structure          │
│     ├── sdlcctl fix          # Auto-fix violations         │
│     └── sdlcctl explain 02   # Show stage 02 rules         │
│                                                             │
│  3️⃣ Pre-Commit Hook (Auto-Scan)                            │
│     ├── Blocks non-compliant commits                       │
│     ├── Shows violation details                            │
│     └── Suggests auto-fix command                          │
│                                                             │
│  4️⃣ GitHub Action (CI/CD Gate)                             │
│     ├── PR review comments with violations                 │
│     ├── Blocks merge if compliance < threshold             │
│     └── Auto-fix via `/sdlc fix` comment                   │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

**Benefits of On-Demand Delivery:**

| Aspect | Bflow Manual | SDLC Orchestrator |
|--------|--------------|-------------------|
| Setup time | 2 weeks | 5 minutes (`sdlcctl init`) |
| Maintenance | Manual sync with Framework | Auto-updated |
| Documentation size | 700KB per project | 0 KB (delivered on-demand) |
| Version consistency | Risk of drift | Always current |
| New member onboarding | "Read this folder" | "Install extension" |

**CLI "Explain" Commands (Replaces Static Docs):**
```bash
# What is stage 02?
sdlcctl explain stage 02
# Output: Stage 02 (design) - HOW
#         Architecture + ADRs
#         Subfolders: 01-ADRs/, 02-System-Architecture/, ...

# What are the naming rules?
sdlcctl explain naming
# Output: Folder: NN-shortname/ (e.g., 02-design)
#         Files: kebab-case.md (e.g., API-Design.md)
#         Code: see 'sdlcctl explain code-naming'

# How to fix a specific violation?
sdlcctl explain violation "duplicate-folder-number"
# Output: Duplicate folder number detected
#         Fix: Rename to next sequential number
#         Auto-fix: sdlcctl fix --rule duplicate-folder-number
```

### Feature 5: Team Documentation Generator (Optional - Enterprise Tier)

> **Note:** This feature is **OPTIONAL** for teams that need offline/printed compliance references or for regulated industries requiring documentation artifacts.

**Purpose:** Generate static compliance docs for teams without internet access or audit requirements

**Based on Bflow Pattern (for offline use only):**
```
docs/08-collaborate/03-SDLC-Compliance/
├── README.md               ← Navigation hub ("I want to...")
├── Core-Methodology/       ← What is SDLC X.Y?
├── SASE-Artifacts/         ← How to work with AI agents?
├── Governance-Compliance/  ← What are the rules?
├── Documentation-Standards/ ← How to document?
├── Situation-Specific-Guides/ ← What to do when X?
│   ├── When-Starting-New-Feature.md
│   ├── When-Reviewing-Code.md
│   └── When-AI-Agent-Helps.md
├── Quick-Reference/        ← Fast lookup
│   ├── SDLC-Cheatsheet.md
│   ├── Quality-Gates-Checklist.md
│   └── Security-Gates-Checklist.md
└── SDLC-X.Y-UPGRADE-SUMMARY.md
```

**CLI:**
```bash
# Generate team compliance docs
sdlcctl generate team-docs --target-version 5.1 --tier professional

# Customize for project
sdlcctl generate team-docs --target-version 5.1 \
  --project-name "Bflow Platform" \
  --team-size 11 \
  --maturity-level L1
```

### Feature 5: Compliance Dashboard (Web UI)

**Purpose:** Visual compliance tracking for Enterprise tier

**Features:**
- Real-time compliance score
- Violation breakdown by stage/type
- Migration progress tracking
- Team compliance history
- Export reports (PDF, MD, JSON)

---

## Sprint Breakdown

### Sprint 47: Scanner Engine (Mar 31 - Apr 11, 2026)

**Goal:** Implement multi-file scanning with parallel processing

**User Stories:**
| ID | Story | Points |
|----|-------|--------|
| EP05-001 | As a developer, I can scan my project for SDLC compliance | 8 |
| EP05-002 | As a developer, I see violations grouped by type/severity | 5 |
| EP05-003 | As a CI/CD, scans run in <5 min for 5,000 files | 8 |
| EP05-004 | As a developer, I get JSON/Markdown compliance reports | 5 |

**Technical Tasks:**
- [ ] Implement `SDLCScanner` base class
- [ ] Add Python docstring parser
- [ ] Add Markdown header parser
- [ ] Implement `ParallelScanner` for 5,000+ files
- [ ] Add progress tracking with ETA
- [ ] Create JSON/Markdown reporters

**Deliverables:**
- `backend/app/services/sdlc_scanner/scanner.py`
- `backend/app/services/sdlc_scanner/parallel_scanner.py`
- `backend/app/services/sdlc_scanner/parsers/`
- `backend/app/services/sdlc_scanner/reporters/`

---

### Sprint 48: Migration & Fixer Engine (Apr 14-25, 2026)

**Goal:** Implement version migration and header fixing

**User Stories:**
| ID | Story | Points |
|----|-------|--------|
| EP05-005 | As a developer, I can upgrade SDLC version with one command | 8 |
| EP05-006 | As a developer, changes are backed up before fixes | 3 |
| EP05-007 | As a developer, I can preview fixes with dry-run | 5 |
| EP05-008 | As a developer, missing headers are auto-added | 8 |

**Technical Tasks:**
- [ ] Implement `VersionFixer`
- [ ] Implement `StageFixer` with path-based derivation
- [ ] Implement `HeaderFixer` for Python/Markdown
- [ ] Implement `BackupManager`
- [ ] Add dry-run mode
- [ ] Create migration CLI commands

**Deliverables:**
- `backend/app/services/sdlc_scanner/fixers/`
- `backend/sdlcctl/commands/migrate.py`
- `backend/sdlcctl/commands/fix.py`

---

### Sprint 49: Real-Time Compliance & CLI Explain (Apr 28 - May 9, 2026)

**Goal:** Implement on-demand compliance delivery (replaces manual docs)

**User Stories:**
| ID | Story | Points |
|----|-------|--------|
| EP05-009 | As a developer, I can run `sdlcctl explain stage 02` to learn about a stage | 5 |
| EP05-010 | As a developer, I can run `sdlcctl explain naming` to see naming rules | 3 |
| EP05-011 | As a developer, VS Code shows inline SDLC violation warnings | 8 |
| EP05-012 | As a developer, pre-commit hook blocks non-compliant commits | 5 |

**Technical Tasks:**
- [ ] Implement `sdlcctl explain` command suite
- [ ] Create VS Code extension inline diagnostics
- [ ] Implement pre-commit hook with violation details
- [ ] Add quick-fix suggestions in VS Code
- [ ] Create hover tooltips with stage/naming rules

**Deliverables:**
- `backend/sdlcctl/commands/explain.py`
- `vscode-extension/src/diagnostics/sdlcDiagnostics.ts`
- `.pre-commit-hooks.yaml` template
- VS Code extension hover provider

**Key Insight:** This sprint **replaces** the need for manual compliance documentation folders. Teams get compliance knowledge on-demand through CLI and extension.

---

### Sprint 50: Dashboard & Team Docs Generator (May 12-23, 2026)

**Goal:** Enterprise dashboard + optional offline docs generator

**User Stories:**
| ID | Story | Points |
|----|-------|--------|
| EP05-013 | As a CTO, I see compliance score on dashboard | 5 |
| EP05-014 | As a CTO, I track migration progress visually | 5 |
| EP05-015 | As a PM, I export compliance reports as PDF | 3 |
| EP05-016 | (Enterprise) As a PM in regulated industry, I can generate offline compliance docs | 3 |

**Technical Tasks:**
- [ ] Create compliance dashboard UI
- [ ] Add migration progress tracking
- [ ] Implement PDF export
- [ ] Polish CLI UX and error handling
- [ ] Add comprehensive documentation
- [ ] Performance optimization for 10,000+ files

**Deliverables:**
- `frontend/web/src/pages/ComplianceDashboard.tsx`
- PDF export service
- User documentation

---

## Tier-Based Features

| Feature | Free | Pro | Enterprise |
|---------|------|-----|------------|
| Basic scan (100 files) | ✅ | ✅ | ✅ |
| Full scan (unlimited) | ❌ | ✅ | ✅ |
| Parallel processing | ❌ | ✅ | ✅ |
| Version migration | ❌ | ✅ | ✅ |
| Auto-fix (dry-run only) | ✅ | ✅ | ✅ |
| Auto-fix (execute) | ❌ | ✅ | ✅ |
| `sdlcctl explain` commands | ✅ | ✅ | ✅ |
| VS Code inline warnings | ✅ | ✅ | ✅ |
| Pre-commit hook | ✅ | ✅ | ✅ |
| GitHub Action | ❌ | ✅ | ✅ |
| Offline team docs generator | ❌ | ❌ | ✅ |
| Web dashboard | ❌ | ❌ | ✅ |
| PDF reports | ❌ | ❌ | ✅ |
| Migration history | ❌ | ❌ | ✅ |
| Multi-project support | ❌ | ❌ | ✅ |

> **Note:** With `sdlcctl explain` and VS Code extension available in Free tier, teams **no longer need** to create manual compliance documentation folders. On-demand compliance delivery replaces static docs.

---

## Success Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| Scan speed | <5 min for 5,000 files | Timer |
| Migration accuracy | 99%+ | Manual validation sample |
| CLI usability | <5 min learning curve | User testing |
| New member onboarding | <30 min (with extension) | Onboarding survey |
| Manual docs created | 0 (for Orchestrator users) | Team survey |

---

## Dependencies

| Dependency | Status | Notes |
|------------|--------|-------|
| EP-04 Structure Validation | Planned (Sprint 44-46) | Provides validation framework |
| SDLC Enterprise Framework | ✅ Exists | Source of truth for versions |
| `sdlcctl` CLI framework | ✅ Exists | `backend/sdlcctl/` |

---

## Risk Assessment

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Complex header formats | Medium | Medium | Fallback to manual review |
| Performance on 10,000+ files | Low | Medium | Chunked processing, caching |
| Cross-platform path issues | Low | Low | Use pathlib consistently |

---

## Real-World Validation

### Bflow Platform Results (Dec 2025)

| Metric | Manual | With Custom Tools |
|--------|--------|-------------------|
| Time to scan | 8 hours | 3 minutes |
| Time to fix | 36 hours | 15 minutes |
| Error rate | ~35% | <1% |
| Team adoption | 2 weeks | 1 day (with generated docs) |

**CTO Quote:**
> "Building the tooling took 2 weeks, but it will save 40+ hours on every future SDLC version upgrade. More importantly, the auto-generated team docs mean new developers are compliant from day 1."

---

## References

- [Bflow Platform SDLC Compliance](https://github.com/Minh-Tam-Solution/Bflow-Platform/tree/main/docs/08-Team-Management/03-SDLC-Compliance)
- [Bflow sdlc51-compliance tools](https://github.com/Minh-Tam-Solution/Bflow-Platform/tree/main/tools/sdlc51-compliance)
- [SDLC Enterprise Framework](https://github.com/Minh-Tam-Solution/SDLC-Enterprise-Framework)
- [EP-04: Structure Enforcement](EP-04-SDLC-Structure-Enforcement.md)
- [ADR-014: SDLC Structure Validator](../../02-design/01-ADRs/ADR-014-SDLC-Structure-Validator.md)

---

## Approval

| Role | Name | Date | Status |
|------|------|------|--------|
| CTO | [CTO] | Dec 21, 2025 | ⏳ PROPOSED |
| Tech Lead | TBD | - | Pending |
| PM | TBD | - | Pending |
