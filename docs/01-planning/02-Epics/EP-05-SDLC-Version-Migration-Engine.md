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

### Current State (Manual Migration)

When upgrading SDLC version (e.g., 4.9 → 5.1) for a large project:

| Task | Manual Effort | Error Rate |
|------|--------------|------------|
| Scan all files for compliance | 8+ hours | 15-20% missed |
| Update version fields | 16+ hours | 5-10% typos |
| Update stage fields | 8+ hours | 10-15% wrong stage |
| Update cross-references | 4+ hours | 5% broken links |
| Generate team documentation | 8+ hours | - |
| **Total** | **44+ hours** | **~35% error rate** |

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

```yaml
# config/sdlc_versions/5.1.yaml
version: "5.1.0"
release_date: "2025-12-11"

stages:
  "00":
    name: "Foundation"
    category: "WHY"
    folder: "00-Project-Foundation"
    description: "Vision, business case, requirements"
  "01":
    name: "Planning"
    category: "WHAT"
    folder: "01-Planning-Analysis"
    description: "Backlog, roadmap, sprint planning"
  # ... 10 stages total

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

### Feature 4: Team Documentation Generator

**Purpose:** Generate "ONE FOLDER" compliance docs for team

**Based on Bflow Pattern:**
```
docs/08-Team-Management/03-SDLC-Compliance/
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

### Sprint 49: Team Documentation Generator (Apr 28 - May 9, 2026)

**Goal:** Auto-generate "ONE FOLDER" team compliance docs

**User Stories:**
| ID | Story | Points |
|----|-------|--------|
| EP05-009 | As a PM, compliance docs are generated for my team | 8 |
| EP05-010 | As a developer, I get situation-specific guides | 5 |
| EP05-011 | As a developer, I get quick-reference cheatsheets | 3 |
| EP05-012 | As a CTO, docs are customized to our project tier | 5 |

**Technical Tasks:**
- [ ] Create documentation templates (Jinja2)
- [ ] Implement folder structure generator
- [ ] Create "I want to..." navigation hub
- [ ] Generate situation-specific guides
- [ ] Generate quick-reference cheatsheets
- [ ] Add tier customization (Small/Medium/Large/Enterprise)

**Deliverables:**
- `backend/app/services/docs_generator/`
- `backend/sdlcctl/commands/generate.py`
- `backend/sdlcctl/templates/team_docs/`

---

### Sprint 50: Web Dashboard & Polish (May 12-23, 2026)

**Goal:** Enterprise dashboard and production polish

**User Stories:**
| ID | Story | Points |
|----|-------|--------|
| EP05-013 | As a CTO, I see compliance score on dashboard | 5 |
| EP05-014 | As a CTO, I track migration progress visually | 5 |
| EP05-015 | As a PM, I export compliance reports as PDF | 3 |
| EP05-016 | As a developer, the CLI has helpful error messages | 3 |

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
| Team docs generation | ❌ | ✅ | ✅ |
| Web dashboard | ❌ | ❌ | ✅ |
| PDF reports | ❌ | ❌ | ✅ |
| Migration history | ❌ | ❌ | ✅ |
| Multi-project support | ❌ | ❌ | ✅ |

---

## Success Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| Scan speed | <5 min for 5,000 files | Timer |
| Migration accuracy | 99%+ | Manual validation sample |
| Team doc quality | 90%+ satisfaction | Survey |
| CLI usability | <5 min learning curve | User testing |

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
