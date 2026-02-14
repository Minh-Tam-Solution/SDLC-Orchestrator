# Sprint 119: Revised Track 2 Plan
## Orchestrator Full Implementation of SDLC Framework 6.0.5

**Version**: 2.0.0
**Dates**: March 10-14, 2026 (5 days)
**Status**: 📋 REVISED (Post-Sprint 118 Analysis)
**Framework**: SDLC 5.3.0 → 6.0.5 (Major Upgrade)
**Prepared By**: Track 2 Team (Jan 29, 2026)

---

## Executive Summary

Sprint 119 Track 2 focuses on **completing the Orchestrator implementation of SDLC Framework 6.0.5**. This is a continuation of Sprint 118 Phase 6 (deferred) plus Framework 6.0.5 alignment.

### Sprint 118 Status (Pre-requisites ✅)

| Phase | Description | LOC | Status |
|-------|-------------|-----|--------|
| Phase 1 | Database Migration (14 tables) | ~800 | ✅ COMPLETE |
| Phase 2.1 | SQLAlchemy Models (14 models) | 1,229 | ✅ COMPLETE |
| Phase 2.2 | Service Classes (Vibecoding + Spec) | 1,162 | ✅ COMPLETE |
| Phase 2.3 | Unit Tests (~100 tests) | 2,609 | ✅ COMPLETE |
| Phase 3 | REST API Endpoints (12 endpoints) | 1,430 | ✅ COMPLETE |
| Phase 4 | Frontend UI (6 components + 3 hooks) | 3,145 | ✅ COMPLETE |
| Phase 5 | Integration Tests (6 suites) | 3,999 | ✅ COMPLETE |
| Phase 6 | CLI Commands | - | ⏳ **DEFERRED → Sprint 119** |
| **TOTAL** | Phases 1-5 Complete | **14,374** | **Production-Ready** |

### Sprint 119 Track 2 Scope

| Day | Task | Est. LOC | Priority |
|-----|------|----------|----------|
| Day 1-2 | Framework Submodule Update (5.3.0 → 6.0.5) | ~200 | P0 |
| Day 3-4 | `sdlcctl spec validate` CLI (Sprint 118 Phase 6) | ~1,500 | P0 |
| Day 5 | OpenSpec/Context Authority Decision | ~300-500 | P1 |
| **TOTAL** | | **~2,000** | |

---

## Prerequisites from Sprint 118

The following services and hooks are ready for CLI integration:

```yaml
Backend Services Ready:
  - SpecificationService: YAML frontmatter validation logic
  - VibecodingService: 5-signal calculation + routing
  - TierManagementService: Tier classification + upgrade logic

Frontend Hooks Ready:
  - useSpecifications: YAML validation + BDD format parsing
  - useTierManagement: Tier progression + requirements
  - useVibecodingIndex: Signal calculation + zone routing

Test Fixtures Ready:
  - YAML frontmatter examples (valid/invalid)
  - BDD requirements format samples
  - Tier classification test cases
```

---

## Day 1-2: Framework Submodule Update (5.3.0 → 6.0.5)

### Objective
Align SDLC Orchestrator with Framework 6.0.5.0 release

### Tasks

#### Task 1.1: Submodule Update (Day 1 - 4h)

```bash
# Update Framework submodule to 6.0.5
cd SDLC-Orchestrator
git submodule update --remote SDLC-Enterprise-Framework
git add SDLC-Enterprise-Framework
git commit -m "chore: Update Framework submodule to 6.0.5

Updates:
- 20 specifications in Framework 6.0.5.0 format
- Section 7: Quality Assurance System
- spec/controls/anti-vibecoding.yaml (AVC-001/002/003)
- spec/gates/gates.yaml (G0-G4)
- spec/evidence/spec-frontmatter-schema.json

Breaking Changes:
- YAML frontmatter required for all specs
- BDD format (GIVEN-WHEN-THEN) for requirements
- Tier-specific requirements mandatory

Migration Guide: SDLC-Enterprise-Framework/docs/MIGRATION-GUIDE-5.3-to-6.0.md"

git push origin main
```

**Checklist**:
- [ ] Framework submodule at v6.0.5 tag
- [ ] All 20 specs accessible from Orchestrator
- [ ] No broken submodule references

#### Task 1.2: CLAUDE.md Alignment (Day 1 - 2h)

**File**: `CLAUDE.md`

**Changes**:
```yaml
Update Locations:
  1. Line ~7: Framework Version
     BEFORE: SDLC 5.3.0 (7-Pillar + AI Governance + Framework 6.0.5 Planning)
     AFTER: SDLC 6.0.5 (7-Pillar + Section 7 Quality Assurance System)

  2. Line ~120: Framework Submodule Version
     BEFORE: Version: SDLC 5.3.0
     AFTER: Version: SDLC 6.0.5

  3. All references to "5.3.0" → "6.0.5"
     - Search and replace across file
     - Verify context accuracy
```

**Estimated**: ~50 LOC changes

#### Task 1.3: Project Documentation Alignment (Day 2 - 4h)

**Files to Update**:
```yaml
Documentation Files:
  1. docs/README.md
     - Update framework version references
     - Add Framework 6.0.5 highlights

  2. docs/02-design/02-System-Architecture/System-Architecture-Document.md
     - Reference Section 7 Quality Assurance System
     - Update tier classification documentation

  3. docs/01-planning/05-API-Design/API-Specification.md
     - Reference new governance API endpoints
     - Update schema documentation

  4. docs/04-build/02-Sprint-Plans/CURRENT-SPRINT.md
     - Update sprint status and milestones
```

**Estimated**: ~100 LOC changes

#### Task 1.4: API Documentation Update (Day 2 - 2h)

**OpenAPI Specification Updates**:
```yaml
Updates to API-Specification.md:
  - Add governance endpoints (12 from Sprint 118 Phase 3)
  - Reference spec-frontmatter-schema.json
  - Document Vibecoding Index API
  - Document Tier Management API
```

**Estimated**: ~50 LOC changes

### Day 1-2 Exit Criteria

- [ ] Framework submodule updated to v6.0.5
- [ ] CLAUDE.md references 6.0.5 (no 5.3.0 mentions)
- [ ] All documentation aligned
- [ ] API documentation updated
- [ ] No broken imports or references
- [ ] Git commit: `chore: Align Orchestrator with Framework 6.0.5.0`

---

## Day 3-4: sdlcctl spec validate CLI (Sprint 118 Phase 6)

### Objective
Implement CLI commands for spec validation against Framework 6.0.5.0 format

### CLI Design

```bash
# Command: sdlcctl spec validate
# Purpose: Validate specification files against Framework 6.0.5.0 format

Usage:
  sdlcctl spec validate [file|directory]
  sdlcctl spec validate --fix [file|directory]
  sdlcctl spec validate --report
  sdlcctl spec validate --format json|csv|markdown

Options:
  --all           Validate all specs in default directory
  --fix           Auto-fix correctable issues
  --report        Generate compliance report
  --format        Output format (default: text)
  --verbose       Show detailed validation output
  --quiet         Show only errors

Exit Codes:
  0: All specs valid
  1: Validation errors found
  2: File not found
  3: Invalid arguments
```

### Implementation Plan

#### Task 3.1: CLI Core Implementation (Day 3 - 6h)

**File**: `backend/app/cli/spec_validate.py`

```python
"""
sdlcctl spec validate - Specification validation CLI
Validates SPEC-*.md files against Framework 6.0.5.0 format
"""

import click
from pathlib import Path
from typing import Optional, List
import yaml
import json
from jsonschema import validate, ValidationError

from app.services.specification_service import SpecificationService

@click.group()
def spec():
    """Specification management commands."""
    pass

@spec.command()
@click.argument('path', required=False, type=click.Path(exists=True))
@click.option('--all', 'validate_all', is_flag=True, help='Validate all specs')
@click.option('--fix', is_flag=True, help='Auto-fix correctable issues')
@click.option('--report', is_flag=True, help='Generate compliance report')
@click.option('--format', 'output_format', type=click.Choice(['text', 'json', 'csv', 'markdown']), default='text')
@click.option('--verbose', '-v', is_flag=True, help='Verbose output')
@click.option('--quiet', '-q', is_flag=True, help='Quiet mode (errors only)')
def validate(
    path: Optional[str],
    validate_all: bool,
    fix: bool,
    report: bool,
    output_format: str,
    verbose: bool,
    quiet: bool
):
    """Validate specification files against Framework 6.0.5.0 format."""

    spec_service = SpecificationService()

    # Determine files to validate
    if validate_all or path is None:
        spec_dir = Path("SDLC-Enterprise-Framework/05-Templates-Tools/01-Specification-Standard")
        files = list(spec_dir.glob("SPEC-*.md"))
    else:
        path_obj = Path(path)
        if path_obj.is_dir():
            files = list(path_obj.glob("SPEC-*.md"))
        else:
            files = [path_obj]

    # Validate each file
    results = []
    for file in files:
        result = spec_service.validate_spec_file(file)
        results.append(result)

        if not quiet:
            status = "✓" if result.is_valid else "✗"
            click.echo(f"{status} {file.name}: {result.message}")

    # Generate report if requested
    if report:
        generate_report(results, output_format)

    # Exit with appropriate code
    if any(not r.is_valid for r in results):
        raise SystemExit(1)
```

**Estimated**: ~400 LOC

#### Task 3.2: Validation Rules Implementation (Day 3 - 2h)

**Validation Rules** (6 checks):

```yaml
Validation Rules:
  1. YAML Frontmatter Present:
     - Check for --- delimiters at start
     - Parse YAML content
     - Error: "Missing YAML frontmatter"

  2. Required Fields Present:
     Required: spec_id, title, version, status, tier, pillar, owner, last_updated
     - Check each field exists
     - Error: "Missing required field: {field}"

  3. BDD Format for Requirements:
     - Find "## Functional Requirements" section
     - Check each requirement has GIVEN-WHEN-THEN format
     - Warning: "Requirement FR-XXX not in BDD format"

  4. Tier-Specific Requirements:
     - Check tier table exists (LITE/STD/PRO/ENT columns)
     - Validate tier values (MANDATORY/RECOMMENDED/OPTIONAL/N/A)
     - Error: "Missing tier requirements table"

  5. Related ADRs Linked:
     - Check related_adrs field in frontmatter
     - Validate ADR files exist
     - Warning: "Referenced ADR not found: ADR-XXX"

  6. Acceptance Criteria Testable:
     - Find "## Acceptance Criteria" section
     - Check each AC has measurable condition
     - Warning: "AC-XXX may not be testable"
```

**Estimated**: ~300 LOC

#### Task 3.3: Auto-Fix Implementation (Day 4 - 4h)

**File**: `backend/app/cli/spec_fix.py`

```python
"""
sdlcctl spec validate --fix - Auto-fix correctable issues
"""

def auto_fix_spec(file_path: Path, issues: List[ValidationIssue]) -> int:
    """
    Auto-fix correctable issues in spec file.

    Fixable Issues:
    - Missing frontmatter fields (add with placeholder)
    - Incorrect date format (normalize to YYYY-MM-DD)
    - Missing tier table (add template)
    - BDD format suggestions (add GIVEN-WHEN-THEN template)

    Returns:
        Number of issues fixed
    """
    fixed_count = 0

    for issue in issues:
        if issue.fixable:
            # Apply fix
            apply_fix(file_path, issue)
            fixed_count += 1

    return fixed_count
```

**Estimated**: ~300 LOC

#### Task 3.4: Report Generation (Day 4 - 2h)

**Output Formats**:

```python
def generate_report(results: List[ValidationResult], format: str):
    """Generate compliance report in specified format."""

    if format == "text":
        # Human-readable summary
        pass
    elif format == "json":
        # JSON for CI/CD integration
        pass
    elif format == "csv":
        # CSV for spreadsheet analysis
        pass
    elif format == "markdown":
        # Markdown for documentation
        pass
```

**Estimated**: ~200 LOC

#### Task 3.5: Unit Tests (Day 4 - 2h)

**File**: `backend/tests/cli/test_spec_validate.py`

```python
"""
Unit tests for sdlcctl spec validate
Target: 95%+ coverage
"""

import pytest
from click.testing import CliRunner
from app.cli.spec_validate import validate

class TestSpecValidate:
    def test_validate_single_file_pass(self):
        """Test: Valid spec file passes validation."""
        pass

    def test_validate_single_file_fail(self):
        """Test: Invalid spec file fails with correct errors."""
        pass

    def test_validate_all_specs(self):
        """Test: --all flag validates all specs."""
        pass

    def test_validate_directory(self):
        """Test: Directory path validates all specs in directory."""
        pass

    def test_fix_mode(self):
        """Test: --fix flag auto-fixes correctable issues."""
        pass

    def test_report_json(self):
        """Test: --report --format json generates JSON output."""
        pass

    def test_exit_code_success(self):
        """Test: Exit code 0 when all specs valid."""
        pass

    def test_exit_code_failure(self):
        """Test: Exit code 1 when validation errors found."""
        pass
```

**Estimated**: ~300 LOC

### Day 3-4 Exit Criteria

- [ ] `sdlcctl spec validate` command works
- [ ] All 6 validation rules implemented
- [ ] `--fix` option auto-fixes correctable issues
- [ ] `--report` generates compliance reports (JSON/CSV/Markdown)
- [ ] Unit tests: 95%+ coverage
- [ ] Documentation: CLI usage guide updated
- [ ] Git commit: `feat(CLI): Add sdlcctl spec validate command`

---

## Day 5: OpenSpec/Context Authority Decision

### Objective
Execute decision from Week 8 Gate on OpenSpec integration approach

### Decision Matrix

| Decision | Action | Deliverables |
|----------|--------|--------------|
| **ADOPT** | OpenSpec CLI wrapper + API endpoint | ~500 LOC |
| **EXTEND** | Context Authority V2 planning | ~300 LOC |
| **DEFER** | Document decision + Sprint 120+ plan | ~200 LOC |

### If ADOPT (OpenSpec Integration)

**Task 5.1: OpenSpec CLI Wrapper**

```python
# File: backend/app/cli/openspec_wrapper.py
# Purpose: Wrap OpenSpec CLI for proposal generation

def generate_proposal(change_description: str, project_id: str) -> ProposalResult:
    """
    Generate proposal using OpenSpec CLI.

    Flow:
    1. Call: /openspec:proposal "{change_description}"
    2. Parse: .openspec/proposals/{date}/ output
    3. Return: PROPOSAL.md, DESIGN_DECISIONS.md, TASKS.md, SPEC_DELTA.md
    """
    pass
```

**Task 5.2: API Endpoint**

```yaml
POST /api/v1/specs/generate
  Input:
    {
      "change_description": "Add user authentication with OAuth",
      "project_id": "xxx"
    }
  Output:
    {
      "proposal_md": "...",
      "design_decisions_md": "...",
      "tasks_md": "...",
      "spec_delta_md": "..."
    }
```

### If EXTEND (Context Authority V2)

**Task 5.3: Context Authority V2 Specification**

```markdown
# Context Authority V2 Specification

## Overview
- Build on existing AGENTS.md/CLAUDE.md patterns
- Align with Framework 6.0.5 templates
- Gate-aware context injection

## Features
1. Dynamic context updates based on gate status
2. Section 7 Quality Assurance integration
3. Vibecoding Index awareness
4. Progressive routing guidance
```

### If DEFER

**Task 5.4: Documentation + Sprint 120 Planning**

```markdown
# OpenSpec Integration: DEFERRED

## Decision
- Defer to Sprint 120+ (more evaluation needed)

## Rationale
- Need more team feedback
- OpenSpec CLI stability assessment
- Alternative: Focus on core governance features

## Sprint 120 Scope
- Re-evaluate OpenSpec adoption
- Build Context Authority V2 (custom)
- Integrate with Framework 6.0.5 templates
```

### Day 5 Exit Criteria

- [ ] Decision executed (ADOPT/EXTEND/DEFER)
- [ ] Documentation complete
- [ ] Sprint 120 direction clear
- [ ] Stakeholder communication sent

---

## Success Metrics

| Metric | Target | Verification |
|--------|--------|--------------|
| Framework submodule | v6.0.5 | `git submodule status` |
| CLAUDE.md version | 6.0.5 | No 5.3.0 references |
| CLI command | Working | `sdlcctl spec validate --all` |
| Validation rules | 6/6 | Unit test coverage |
| Test coverage | 95%+ | pytest-cov report |
| Documentation | Complete | Review by Tech Lead |
| OpenSpec decision | Executed | Document published |

---

## Risk Mitigation

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Submodule conflicts | Low | Medium | Test on staging first |
| CLI bugs | Medium | Low | Comprehensive unit tests |
| OpenSpec instability | Medium | Low | Fallback to EXTEND option |
| Documentation gaps | Low | Low | Review checklist |

---

## Team Assignments

| Task | Owner | Days | Status |
|------|-------|------|--------|
| Framework Submodule Update | DevOps Lead | 1-2 | ⏳ |
| CLAUDE.md Alignment | Backend Lead | 1 | ⏳ |
| Documentation Updates | Tech Writer | 2 | ⏳ |
| CLI Core Implementation | Backend Dev | 3 | ⏳ |
| Validation Rules | Backend Dev | 3 | ⏳ |
| Auto-Fix Implementation | Backend Dev | 4 | ⏳ |
| Unit Tests | QA Lead | 4 | ⏳ |
| OpenSpec Decision | Tech Lead | 5 | ⏳ |

---

## Sprint 120+ Continuation

### Sprint 120 Focus Areas

Based on Sprint 119 outcomes, Sprint 120 will focus on:

```yaml
If OpenSpec ADOPTED (Sprint 120):
  - OpenSpec deep integration
  - Workflow optimization
  - Planning phase automation

If Context Authority EXTENDED (Sprint 120):
  - Context Authority V2 development
  - Enhanced spec validation
  - AI-assisted spec generation

Common (Both Paths):
  - Framework 6.0.5 maintenance
  - Spec migration support
  - Anti-Vibecoding optimization
  - CEO time tracking (<10h/week target)
```

### Sprint 121-122 Roadmap

| Sprint | Focus | Estimated LOC |
|--------|-------|---------------|
| Sprint 121 | Gates Integration + Quality Metrics | ~5,700 |
| Sprint 122 | Production Deployment + Rollout | ~3,600 |

---

## Approval

| Role | Status | Date |
|------|--------|------|
| Backend Lead | ⏳ PENDING | - |
| Tech Lead | ⏳ PENDING | - |
| CTO | ⏳ PENDING | - |

*Approval pending Sprint 118 completion verification.*

---

## Document Control

| Field | Value |
|-------|-------|
| **Version** | 2.0.0 |
| **Created** | January 29, 2026 |
| **Revised** | January 29, 2026 |
| **Author** | Track 2 Team |
| **Status** | REVISED |
| **Sprint** | 119 |
| **Track** | Track 2 (40%) |
| **Prerequisite** | Sprint 118 Phases 1-5 Complete |

---

## Changelog

### v2.0.0 (January 29, 2026)
- Revised based on Sprint 118 completion status
- Incorporated Track 2 team analysis
- Updated CLI scope with detailed implementation plan
- Added prerequisites from Sprint 118 (services + hooks ready)
- Clarified Day 5 decision options (ADOPT/EXTEND/DEFER)
- Added Sprint 120+ continuation roadmap

### v1.0.0 (January 28, 2026)
- Initial Sprint 119 Dual-Track plan
- Framework 6.0.5 release focus

---

**Document Status**: ✅ **REVISED & READY**
**Next Action**: Begin Day 1 tasks (Framework Submodule Update)
**Sprint 118 Prerequisite**: ✅ **PHASES 1-5 COMPLETE** (14,374 LOC)

---

*Sprint 119 Track 2 - Completing Orchestrator Implementation of SDLC Framework 6.0.5*
