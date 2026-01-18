# Sprint 29: SDLC Validator CLI
## Core CLI & Validation Engine

**Sprint**: 29
**Duration**: 5 days (January 6-10, 2026)
**Status**: PLANNED
**Team**: 2 Backend, 1 DevOps
**Framework**: SDLC 5.1.3 Complete Lifecycle
**Phase**: PHASE-04 (SDLC Structure Validator)

---

## Sprint Goal

Build the core SDLC Validator CLI (`sdlcctl`) with SDLC 5.1.3 validation engine, including 4-tier classification support, P0 artifact checking, and pre-commit hook integration.

---

## Sprint Backlog

### Day 1: Validation Engine Core (Jan 6, 2026)

**Owner**: Backend Lead
**Story Points**: 8

#### Tasks

| Task | Description | Estimate | Priority |
|------|-------------|----------|----------|
| T1.1 | Create project structure for `sdlcctl` package | 1h | P0 |
| T1.2 | Implement folder tree scanner (async, performant) | 3h | P0 |
| T1.3 | Implement tier detector (team_size → tier mapping) | 2h | P0 |
| T1.4 | Implement stage validator (naming, count, structure) | 3h | P0 |
| T1.5 | Unit tests for validation engine (95%+ coverage) | 2h | P0 |

#### Acceptance Criteria

```yaml
AC-1.1: Folder scanner completes in <10s for 1000+ files
AC-1.2: Tier detector correctly identifies LITE/STANDARD/PROFESSIONAL/ENTERPRISE
AC-1.3: Stage validator checks all 11 stage names (00-10)
AC-1.4: Unit test coverage ≥95%
```

#### Technical Specification

```python
# backend/sdlcctl/validation/engine.py

from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import List, Optional

class Tier(Enum):
    LITE = "lite"           # 1-2 people
    STANDARD = "standard"   # 3-10 people
    PROFESSIONAL = "professional"  # 10-50 people
    ENTERPRISE = "enterprise"  # 50+ people

@dataclass
class ValidationResult:
    valid: bool
    tier: Tier
    stages_found: List[str]
    stages_missing: List[str]
    violations: List[str]
    p0_artifacts: dict
    score: int  # 0-100

class SDLCValidator:
    """SDLC 5.1.3 Structure Validator Engine"""

    STAGE_NAMES = {
        "00": "00-Project-Foundation",
        "01": "01-Planning-Analysis",
        "02": "02-Design-Architecture",
        "03": "03-Development-Implementation",
        "04": "04-Testing-Quality",
        "05": "05-Deployment-Release",
        "06": "06-Operations-Maintenance",
        "07": "07-Integration-APIs",
        "08": "08-Team-Management",
        "09": "09-Executive-Reports",
        "10": "10-Archive",
    }

    TIER_REQUIREMENTS = {
        Tier.LITE: {"min_stages": 4, "required": ["00", "01", "02", "03"]},
        Tier.STANDARD: {"min_stages": 6, "required": ["00", "01", "02", "03", "04", "05"]},
        Tier.PROFESSIONAL: {"min_stages": 10, "required": ["00", "01", "02", "03", "04", "05", "06", "07", "08", "09"]},
        Tier.ENTERPRISE: {"min_stages": 11, "required": ["00", "01", "02", "03", "04", "05", "06", "07", "08", "09", "10"]},
    }

    def __init__(self, project_root: Path, tier: Optional[Tier] = None):
        self.project_root = project_root
        self.tier = tier

    def detect_tier(self, team_size: int) -> Tier:
        """Detect project tier based on team size"""
        if team_size <= 2:
            return Tier.LITE
        elif team_size <= 10:
            return Tier.STANDARD
        elif team_size <= 50:
            return Tier.PROFESSIONAL
        else:
            return Tier.ENTERPRISE

    async def validate(self) -> ValidationResult:
        """Run full SDLC 5.1.3 validation"""
        # Implementation
        pass
```

---

### Day 2: P0 Artifact Checker (Jan 7, 2026)

**Owner**: Backend Engineer 2
**Story Points**: 8

#### Tasks

| Task | Description | Estimate | Priority |
|------|-------------|----------|----------|
| T2.1 | Define P0 artifact list (15 artifacts) | 1h | P0 |
| T2.2 | Implement P0 artifact scanner | 3h | P0 |
| T2.3 | Implement legacy folder exclusion (99-Legacy/) | 2h | P0 |
| T2.4 | Add tier-aware P0 enforcement (required for PROFESSIONAL+) | 2h | P0 |
| T2.5 | Unit tests for P0 checker | 2h | P0 |

#### Acceptance Criteria

```yaml
AC-2.1: P0 checker validates all 15 artifacts
AC-2.2: 99-Legacy/ folder excluded from validation
AC-2.3: P0 required for PROFESSIONAL+ tiers only
AC-2.4: Warning (not error) for STANDARD tier P0 missing
```

#### P0 Artifact Specification

```yaml
# 15 P0 Artifacts for AI Discoverability

Framework Level (4):
  1. SDLC-Executive-Summary.md
  2. SDLC-Core-Methodology.md
  3. README.md (root)
  4. CHANGELOG.md

Project Level (5):
  5. docs/README.md
  6. docs/03-Development-Implementation/02-Sprint-Plans/CURRENT-SPRINT.md
  7. docs/00-Project-Foundation/04-Roadmap/Product-Roadmap.md
  8. docs/01-Planning-Analysis/01-Requirements/Functional-Requirements-Document.md
  9. docs/02-Design-Architecture/03-API-Design/openapi.yml

Stage Level (6):
  10-15. Each stage must have README.md (Stage 00-09 for PROFESSIONAL)

Tier Enforcement:
  LITE: P0 not required (optional)
  STANDARD: P0 not required (warning only)
  PROFESSIONAL: P0 required (error if missing)
  ENTERPRISE: P0 required + compliance docs
```

---

### Day 3: CLI Tool (sdlcctl) (Jan 8, 2026)

**Owner**: Backend Lead
**Story Points**: 8

#### Tasks

| Task | Description | Estimate | Priority |
|------|-------------|----------|----------|
| T3.1 | Setup CLI framework (typer) | 1h | P0 |
| T3.2 | Implement `sdlcctl validate` command | 3h | P0 |
| T3.3 | Implement `sdlcctl fix` command (auto-fix) | 2h | P0 |
| T3.4 | Implement `sdlcctl init` command (scaffold) | 2h | P0 |
| T3.5 | Add JSON/text output formatters | 1h | P1 |
| T3.6 | Integration tests for CLI | 2h | P0 |

#### Acceptance Criteria

```yaml
AC-3.1: `sdlcctl validate` exits 0 on success, 1 on failure
AC-3.2: `sdlcctl fix --dry-run` shows what would be fixed
AC-3.3: `sdlcctl init --tier professional` creates folder structure
AC-3.4: JSON output format for CI/CD integration
```

#### CLI Commands Specification

```bash
# sdlcctl validate
sdlcctl validate                    # Validate current directory
sdlcctl validate --path /project    # Validate specific path
sdlcctl validate --tier professional # Override tier detection
sdlcctl validate --format json      # JSON output
sdlcctl validate --verbose          # Detailed output

# sdlcctl fix
sdlcctl fix                         # Auto-fix violations
sdlcctl fix --dry-run               # Show what would be fixed
sdlcctl fix --interactive           # Interactive mode

# sdlcctl init
sdlcctl init                        # Initialize with auto-detected tier
sdlcctl init --tier professional    # Initialize with specific tier
sdlcctl init --scaffold             # Create folder structure
sdlcctl init --config               # Generate .sdlc-config.json only

# sdlcctl report
sdlcctl report                      # Generate HTML report
sdlcctl report --format markdown    # Markdown report
sdlcctl report --output report.html # Custom output path
```

---

### Day 4: Pre-commit Hook (Jan 9, 2026)

**Owner**: DevOps Engineer
**Story Points**: 6

#### Tasks

| Task | Description | Estimate | Priority |
|------|-------------|----------|----------|
| T4.1 | Create pre-commit hook package structure | 1h | P0 |
| T4.2 | Implement hook entry point | 2h | P0 |
| T4.3 | Add .pre-commit-config.yaml template | 1h | P0 |
| T4.4 | Performance optimization (<2s execution) | 2h | P0 |
| T4.5 | Integration test with sample repos | 2h | P0 |

#### Acceptance Criteria

```yaml
AC-4.1: Pre-commit hook executes in <2s
AC-4.2: Hook blocks commits with violations
AC-4.3: Hook shows clear error messages
AC-4.4: Compatible with pre-commit framework
```

#### Pre-commit Hook Specification

```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/sdlc-orchestrator/sdlcctl
    rev: v1.0.0
    hooks:
      - id: sdlc-validate
        name: SDLC 5.1.3 Structure Validation
        entry: sdlcctl validate --strict
        language: python
        types: [file]
        files: ^docs/
        always_run: true
        pass_filenames: false
```

```bash
# Hook output on failure
$ git commit -m "Add new feature"

SDLC 5.1.3 Structure Validation.............................Failed

❌ Violations Found: 2

1. ❌ Stage naming violation
   Found: docs/06-Maintenance/
   Expected: docs/06-Operations-Maintenance/

2. ❌ P0 artifact missing
   Missing: docs/README.md
   Required for PROFESSIONAL tier

Commit blocked. Run 'sdlcctl fix' to auto-fix.
```

---

### Day 5: Testing & Documentation (Jan 10, 2026)

**Owner**: Full Team
**Story Points**: 6

#### Tasks

| Task | Description | Estimate | Priority |
|------|-------------|----------|----------|
| T5.1 | Complete unit test suite (95%+ coverage) | 3h | P0 |
| T5.2 | Integration tests (real project validation) | 2h | P0 |
| T5.3 | Write README.md for sdlcctl package | 2h | P0 |
| T5.4 | Create example configurations | 1h | P1 |
| T5.5 | Performance benchmark report | 1h | P1 |
| T5.6 | CTO review and sign-off | 1h | P0 |

#### Acceptance Criteria

```yaml
AC-5.1: Unit test coverage ≥95%
AC-5.2: Integration tests pass on SDLC-Orchestrator repo
AC-5.3: README includes installation, usage, examples
AC-5.4: Performance benchmark: <10s for 1000+ files
AC-5.5: CTO approval received
```

---

## Definition of Done

### Sprint Level

- [ ] All tasks completed (T1.1 - T5.6)
- [ ] Unit test coverage ≥95%
- [ ] Integration tests passing
- [ ] Documentation complete
- [ ] CTO review approved
- [ ] No P0 bugs

### Feature Level

- [ ] `sdlcctl validate` works for all 4 tiers
- [ ] `sdlcctl fix` auto-fixes naming violations
- [ ] `sdlcctl init` creates proper folder structure
- [ ] Pre-commit hook blocks non-compliant commits
- [ ] P0 artifacts checked for PROFESSIONAL+ tiers
- [ ] Legacy folder (99-Legacy/) properly excluded

---

## Technical Decisions

### TD-1: Package Structure

```
backend/
└── sdlcctl/
    ├── __init__.py
    ├── cli.py              # Typer CLI entry point
    ├── validation/
    │   ├── __init__.py
    │   ├── engine.py       # Core validation engine
    │   ├── scanner.py      # Folder tree scanner
    │   ├── tier.py         # Tier detection
    │   └── p0.py           # P0 artifact checker
    ├── commands/
    │   ├── __init__.py
    │   ├── validate.py     # validate command
    │   ├── fix.py          # fix command
    │   └── init.py         # init command
    ├── output/
    │   ├── __init__.py
    │   ├── text.py         # Text formatter
    │   └── json.py         # JSON formatter
    └── tests/
        ├── __init__.py
        ├── test_engine.py
        ├── test_scanner.py
        ├── test_tier.py
        ├── test_p0.py
        └── test_cli.py
```

### TD-2: Dependencies

```toml
# pyproject.toml
[project]
name = "sdlcctl"
version = "1.0.0"
description = "SDLC 5.1.3 Structure Validator CLI"
dependencies = [
    "typer>=0.9.0",
    "rich>=13.0.0",
    "pyyaml>=6.0",
    "tomli>=2.0.0",
]

[project.scripts]
sdlcctl = "sdlcctl.cli:app"
```

### TD-3: Performance Strategy

```yaml
Performance Targets:
  - Folder scan: <5s (1000+ files)
  - Tier detection: <100ms
  - P0 check: <1s
  - Full validation: <10s

Optimization Techniques:
  - Async file I/O (aiofiles)
  - Early exit on critical violations
  - Parallel stage scanning
  - Cached config loading
```

---

## Risk Register

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| Performance below target | High | Low | Async I/O, early exit, caching |
| Edge cases in tier detection | Medium | Medium | Comprehensive test suite |
| Pre-commit compatibility issues | Medium | Low | Test with multiple pre-commit versions |
| Complex project structures | Medium | Medium | Configurable ignore patterns |

---

## Dependencies

### Blocking Dependencies

- None (Sprint 29 starts fresh)

### Non-blocking Dependencies

- PHASE-04 document approved (completed)
- SDLC 5.1.3 Framework finalized (completed)

---

## Success Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| Validation time (1000 files) | <10s | CLI timing |
| Pre-commit hook time | <2s | Git hook timing |
| Unit test coverage | ≥95% | pytest --cov |
| Detection accuracy | 100% | Manual validation |
| False positive rate | 0% | User reports |

---

## Sprint Ceremonies

| Ceremony | Time | Participants |
|----------|------|--------------|
| Sprint Planning | Jan 6, 9:00 AM | Full team |
| Daily Standup | 9:30 AM daily | Full team |
| Sprint Review | Jan 10, 4:00 PM | Team + CTO |
| Retrospective | Jan 10, 5:00 PM | Full team |

---

## References

- [PHASE-04: SDLC Structure Validator](../04-Phase-Plans/PHASE-04-SDLC-VALIDATOR.md)
- [SDLC 5.1.3 Framework](../../../SDLC-Enterprise-Framework/)
- [ADR-014: SDLC Structure Validator](../../02-design/01-ADRs/ADR-014-SDLC-Validator.md)

---

**Document Status**: PLANNED
**Last Updated**: December 5, 2025
**Owner**: Backend Lead + DevOps
**Next Sprint**: [Sprint 30: CI/CD & Web Integration](./SPRINT-30-CICD-WEB-INTEGRATION.md)
