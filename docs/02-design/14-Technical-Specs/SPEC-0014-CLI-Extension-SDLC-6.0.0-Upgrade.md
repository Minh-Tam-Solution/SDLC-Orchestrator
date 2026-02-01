---
spec_id: SPEC-0014
title: CLI and Extension SDLC 6.0.0 Upgrade
version: "1.0.0"
status: DRAFT
tier:
  - LITE
  - STANDARD
  - PROFESSIONAL
  - ENTERPRISE
pillar:
  - Section 7 - Quality Assurance System
  - Pillar 7 - Specification Standard
owner: Backend Lead + Frontend Lead
last_updated: "2026-01-30"
tags:
  - sdlcctl
  - vscode-extension
  - framework-upgrade
  - sdlc-6.0.0
related_adrs:
  - ADR-014-SDLC-Structure-Validator
  - ADR-041-Stage-Dependency-Matrix
related_specs:
  - SPEC-0002
  - SPEC-0013
---

# SPEC-0014: CLI and Extension SDLC 6.0.0 Upgrade

**Version**: 1.0.0
**Status**: DRAFT
**Owner**: Backend Lead + Frontend Lead
**Created**: 2026-01-30
**Last Updated**: 2026-01-30
**Sprint**: 124 - Compliance Validation + CLI Update

---

## 1. Executive Summary

### 1.1 Purpose

Upgrade `sdlcctl` CLI and VS Code Extension from SDLC 5.0.0/5.3.0 to **SDLC 6.0.0** to support the new Unified Specification Standard (Section 8), including:
- YAML frontmatter validation
- BDD requirements format validation
- Context Authority Methodology support
- `sdlcctl spec convert` command for OpenSpec integration

### 1.2 Background

**Current State**:
- sdlcctl CLI: v1.1.2 targeting SDLC 5.0.0
- VS Code Extension: v1.1.2 with SDLC 5.x validation
- Framework: SDLC 6.0.0 released January 28, 2026

**Problem**: CLI and Extension are outdated, causing:
1. Version mismatch with Framework (5.0.0 vs 6.0.0)
2. Missing spec validation for YAML frontmatter
3. Missing BDD requirements validation
4. No OpenSpec → SDLC 6.0 conversion support

### 1.3 Scope

**In Scope**:
- Update all version references from 5.x to 6.0.0
- Implement YAML frontmatter validator
- Implement BDD requirements validator
- Implement tier-specific section validator
- Add `sdlcctl spec convert` command
- Add `sdlcctl spec list` command
- Add `sdlcctl spec init` command
- Update VS Code extension validation
- Copy Framework 6.0 templates to CLI

**Out of Scope**:
- Web app updates (covered in SPEC-0013)
- Backend API changes for specs
- Database schema changes

---

## 2. Functional Requirements

### FR-01: Version Reference Updates (P0)

```gherkin
GIVEN sdlcctl CLI codebase has SDLC 5.0.0/5.3.0 references
  AND SDLC Framework is at version 6.0.0
WHEN developer runs sdlcctl --version or any command
THEN all output should reference "SDLC 6.0.0"
  AND help text should mention Framework 6.0.0 features
```

**Files to Update** (38 files):
| File | References | Priority |
|------|------------|----------|
| `sdlcctl/__init__.py` | `__framework__ = "SDLC 5.0.0"` | HIGH |
| `cli.py` | 8+ references to 5.0.0 | HIGH |
| `pyproject.toml` | description field | HIGH |
| `README.md` | Title, features section | MEDIUM |
| `commands/*.py` | Help text in 10+ files | MEDIUM |
| `validation/*.py` | Docstrings in 7 files | LOW |

### FR-02: YAML Frontmatter Validator (P0)

```gherkin
GIVEN a specification file (SPEC-*.md)
  AND the file should have YAML frontmatter
WHEN sdlcctl spec validate runs
THEN the validator should parse frontmatter between --- delimiters
  AND validate required fields: spec_id, title, version, status, tier, pillar, owner, last_updated
  AND validate spec_id pattern: ^SPEC-[0-9]{4}$
  AND validate version pattern: ^\d+\.\d+\.\d+$
  AND validate status enum: DRAFT | REVIEW | APPROVED | ACTIVE | DEPRECATED
  AND validate tier array contains only: LITE | STANDARD | PROFESSIONAL | ENTERPRISE
  AND validate last_updated date format: YYYY-MM-DD
  AND return validation errors with line numbers
```

**Schema** (from `spec-frontmatter-schema.json`):
```json
{
  "required": ["spec_id", "title", "version", "status", "tier", "pillar", "owner", "last_updated"],
  "properties": {
    "spec_id": { "pattern": "^SPEC-[0-9]{4}$" },
    "title": { "minLength": 10, "maxLength": 150 },
    "version": { "pattern": "^\\d+\\.\\d+\\.\\d+$" },
    "status": { "enum": ["DRAFT", "REVIEW", "APPROVED", "ACTIVE", "DEPRECATED"] },
    "tier": { "items": { "enum": ["LITE", "STANDARD", "PROFESSIONAL", "ENTERPRISE"] } },
    "pillar": { "items": { "pattern": "^(Pillar [0-7]|Section [0-9]+).*$" } },
    "last_updated": { "pattern": "^\\d{4}-\\d{2}-\\d{2}$" }
  }
}
```

### FR-03: BDD Requirements Validator (P1)

```gherkin
GIVEN a specification file with functional requirements section
  AND SDLC 6.0.0 requires BDD format (GIVEN-WHEN-THEN)
WHEN sdlcctl spec validate --strict runs
THEN the validator should detect requirement blocks (FR-XX, NFR-XX)
  AND validate BDD structure: GIVEN ... WHEN ... THEN ...
  AND warn if requirements don't follow BDD format
  AND suggest conversion for non-BDD requirements
```

**BDD Pattern**:
```regex
^GIVEN\s+.+(\n\s+AND\s+.+)*\nWHEN\s+.+\nTHEN\s+.+(\n\s+AND\s+.+)*$
```

### FR-04: Tier-Specific Section Validator (P1)

```gherkin
GIVEN a specification file with declared tier in frontmatter
  AND each tier has different required sections
WHEN sdlcctl spec validate runs
THEN the validator should check sections based on tier:
  | Tier | Required Sections |
  | LITE | frontmatter, overview, requirements_bdd, acceptance_criteria |
  | STANDARD | + context, design_decisions, technical_spec, dependencies |
  | PROFESSIONAL | + spec_delta |
  | ENTERPRISE | + compliance, audit_trail |
  AND report missing required sections for the declared tier
```

### FR-05: Spec Convert Command (P0)

```gherkin
GIVEN an OpenSpec proposal directory (.openspec/proposals/*)
  AND containing: PROPOSAL.md, DESIGN_DECISIONS.md, TASKS.md
WHEN user runs sdlcctl spec convert --from openspec --path .openspec/proposals/feature-x
THEN the CLI should:
  - Parse OpenSpec files
  - Generate YAML frontmatter (auto-generate spec_id, infer tier)
  - Convert TASKS.md items to BDD requirements
  - Create SPEC-XXXX.md in docs/02-design/14-Technical-Specs/
  - Display generated spec_id and location
```

**Conversion Mapping**:
```yaml
OpenSpec → SDLC 6.0.0:
  PROPOSAL.md/title → frontmatter.title
  PROPOSAL.md/description → ## Overview
  DESIGN_DECISIONS.md → ## Design Decisions (Sprint-Scoped)
  TASKS.md → ## Functional Requirements (BDD conversion)
  Infer tier from complexity:
    - ≤3 tasks → LITE
    - 4-8 tasks → STANDARD
    - 9-15 tasks → PROFESSIONAL
    - >15 tasks → ENTERPRISE
```

### FR-06: Spec List Command (P1)

```gherkin
GIVEN a project with multiple SPEC-*.md files
WHEN user runs sdlcctl spec list [--tier X] [--status Y] [--stage Z]
THEN the CLI should:
  - Scan docs/**/SPEC-*.md files
  - Parse YAML frontmatter from each
  - Display table: spec_id | title | version | tier | status | last_updated
  - Filter by --tier, --status, --stage if provided
  - Sort by spec_id (default) or --sort option
```

### FR-07: Spec Init Command (P1)

```gherkin
GIVEN user wants to create a new specification
WHEN user runs sdlcctl spec init [--tier X] [--stage Y]
THEN the CLI should:
  - Prompt for tier if not provided (interactive)
  - Prompt for stage (00-09) if not provided
  - Generate next spec_id (scan existing, increment)
  - Copy tier-appropriate template
  - Pre-fill frontmatter (spec_id, tier, stage, owner, dates)
  - Open file in default editor (optional)
```

### FR-08: VSCode Extension Update (P1)

```gherkin
GIVEN VS Code extension validates project structure
  AND Framework is SDLC 6.0.0
WHEN extension performs validation
THEN it should:
  - Reference SDLC 6.0.0 in all UI text
  - Validate specs with YAML frontmatter
  - Show spec validation in Problems panel
  - Support spec convert/init commands via Command Palette
```

---

## 3. Non-Functional Requirements

### NFR-01: Performance
- Spec validation: <100ms per file (p95)
- Spec convert: <2s for standard OpenSpec proposal
- Spec list: <500ms for 100 specs

### NFR-02: Compatibility
- Python 3.10+ (CLI)
- VS Code 1.80+ (Extension)
- Backward compatible with SDLC 5.3.0 specs (warn, don't fail)

### NFR-03: Error Handling
- Clear error messages with file paths and line numbers
- Suggestions for fixing common issues
- `--fix` mode for auto-fixable issues

---

## 4. Acceptance Criteria

| ID | Criteria | Priority | Sprint |
|----|----------|----------|--------|
| AC-01 | All 38 files updated with 6.0.0 references | P0 | 124 |
| AC-02 | `sdlcctl spec validate` validates YAML frontmatter | P0 | 124 |
| AC-03 | `sdlcctl spec convert` converts OpenSpec → SDLC 6.0 | P0 | 125 |
| AC-04 | `sdlcctl spec list` displays spec inventory | P1 | 125 |
| AC-05 | `sdlcctl spec init` creates new spec from template | P1 | 125 |
| AC-06 | BDD validator warns on non-BDD requirements | P1 | 125 |
| AC-07 | Tier validator checks section requirements | P1 | 125 |
| AC-08 | VS Code extension updated to 6.0.0 | P1 | 126 |
| AC-09 | All tests pass (95%+ coverage) | P0 | 126 |
| AC-10 | Published: CLI v1.2.0, Extension v1.2.0 | P0 | 126 |

---

## 5. Technical Design

### 5.1 New Validator Files

```
backend/sdlcctl/sdlcctl/validation/validators/
├── spec_frontmatter.py      # YAML frontmatter validation (FR-02)
├── spec_bdd.py              # BDD requirements validation (FR-03)
└── spec_tier.py             # Tier-specific sections validation (FR-04)
```

### 5.2 New Command Implementation

```python
# backend/sdlcctl/sdlcctl/commands/spec.py (extend existing)

@spec_app.command(name="convert")
def spec_convert(
    path: str = typer.Option(..., "--path", "-p"),
    source: str = typer.Option("openspec", "--from", "-f"),
    output: str = typer.Option(None, "--output", "-o"),
    tier: str = typer.Option(None, "--tier", "-t"),
) -> None:
    """Convert external spec format to SDLC 6.0.0 specification."""
    ...

@spec_app.command(name="list")
def spec_list(
    path: str = typer.Option(".", "--path", "-p"),
    tier: str = typer.Option(None, "--tier", "-t"),
    status: str = typer.Option(None, "--status", "-s"),
    output_format: str = typer.Option("table", "--format", "-f"),
) -> None:
    """List all specifications with filtering."""
    ...

@spec_app.command(name="init")
def spec_init(
    tier: str = typer.Option(None, "--tier", "-t"),
    stage: str = typer.Option(None, "--stage", "-s"),
    title: str = typer.Option(None, "--title"),
    no_interactive: bool = typer.Option(False, "--no-interactive"),
) -> None:
    """Initialize new specification from template."""
    ...
```

### 5.3 Frontmatter Validator Implementation

```python
# backend/sdlcctl/sdlcctl/validation/validators/spec_frontmatter.py

import re
import yaml
from typing import Any
from ..base_validator import BaseValidator, ValidationIssue

SPEC_ID_PATTERN = re.compile(r"^SPEC-[0-9]{4}$")
VERSION_PATTERN = re.compile(r"^\d+\.\d+\.\d+$")
DATE_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2}$")
VALID_STATUSES = {"DRAFT", "REVIEW", "APPROVED", "ACTIVE", "DEPRECATED"}
VALID_TIERS = {"LITE", "STANDARD", "PROFESSIONAL", "ENTERPRISE"}

class SpecFrontmatterValidator(BaseValidator):
    """Validate YAML frontmatter in SDLC 6.0.0 specifications."""

    name = "spec_frontmatter"
    description = "Validates YAML frontmatter against SDLC 6.0.0 spec schema"

    REQUIRED_FIELDS = [
        "spec_id", "title", "version", "status",
        "tier", "pillar", "owner", "last_updated"
    ]

    def validate(self, file_path: str) -> list[ValidationIssue]:
        """Validate spec file frontmatter."""
        issues = []
        content = self._read_file(file_path)

        # Extract frontmatter
        frontmatter = self._extract_frontmatter(content)
        if frontmatter is None:
            issues.append(ValidationIssue(
                severity="error",
                message="Missing YAML frontmatter (required by SDLC 6.0.0)",
                file=file_path,
                line=1,
                suggestion="Add YAML frontmatter between --- delimiters at file start"
            ))
            return issues

        # Validate required fields
        for field in self.REQUIRED_FIELDS:
            if field not in frontmatter:
                issues.append(ValidationIssue(
                    severity="error",
                    message=f"Missing required frontmatter field: {field}",
                    file=file_path,
                    suggestion=f"Add '{field}' to YAML frontmatter"
                ))

        # Validate field formats
        if "spec_id" in frontmatter:
            if not SPEC_ID_PATTERN.match(str(frontmatter["spec_id"])):
                issues.append(ValidationIssue(
                    severity="error",
                    message=f"Invalid spec_id format: {frontmatter['spec_id']}",
                    file=file_path,
                    suggestion="spec_id must match pattern SPEC-NNNN (e.g., SPEC-0014)"
                ))

        if "version" in frontmatter:
            if not VERSION_PATTERN.match(str(frontmatter["version"])):
                issues.append(ValidationIssue(
                    severity="error",
                    message=f"Invalid version format: {frontmatter['version']}",
                    file=file_path,
                    suggestion="version must be semantic: X.Y.Z (e.g., 1.0.0)"
                ))

        if "status" in frontmatter:
            if frontmatter["status"] not in VALID_STATUSES:
                issues.append(ValidationIssue(
                    severity="error",
                    message=f"Invalid status: {frontmatter['status']}",
                    file=file_path,
                    suggestion=f"status must be one of: {', '.join(VALID_STATUSES)}"
                ))

        if "tier" in frontmatter:
            tiers = frontmatter["tier"] if isinstance(frontmatter["tier"], list) else [frontmatter["tier"]]
            for tier in tiers:
                if tier not in VALID_TIERS:
                    issues.append(ValidationIssue(
                        severity="error",
                        message=f"Invalid tier: {tier}",
                        file=file_path,
                        suggestion=f"tier must be one of: {', '.join(VALID_TIERS)}"
                    ))

        if "last_updated" in frontmatter:
            if not DATE_PATTERN.match(str(frontmatter["last_updated"])):
                issues.append(ValidationIssue(
                    severity="error",
                    message=f"Invalid date format: {frontmatter['last_updated']}",
                    file=file_path,
                    suggestion="last_updated must be YYYY-MM-DD format"
                ))

        return issues

    def _extract_frontmatter(self, content: str) -> dict[str, Any] | None:
        """Extract YAML frontmatter from markdown content."""
        if not content.startswith("---"):
            return None

        parts = content.split("---", 2)
        if len(parts) < 3:
            return None

        try:
            return yaml.safe_load(parts[1])
        except yaml.YAMLError:
            return None
```

### 5.4 Templates to Copy

Copy from Framework to CLI:
```
SDLC-Enterprise-Framework/05-Templates-Tools/01-Specification-Standard/
├── SDLC-Specification-Standard.md   → sdlcctl/templates/specifications/
├── DESIGN_DECISIONS.md              → sdlcctl/templates/specifications/
├── SPEC_DELTA.md                    → sdlcctl/templates/specifications/
├── spec-frontmatter-schema.json     → sdlcctl/schemas/
├── example-Spec-LITE.md             → sdlcctl/templates/specifications/
├── example-Spec-STANDARD.md         → sdlcctl/templates/specifications/
└── example-Spec-PROFESSIONAL.md     → sdlcctl/templates/specifications/
```

---

## 6. Implementation Plan

### Phase 1: Foundation (Sprint 124 - Current)

| Task | Effort | Owner | Status |
|------|--------|-------|--------|
| Update version references (38 files) | 2h | Backend | PENDING |
| Create spec_frontmatter_validator | 3h | Backend | PENDING |
| Copy Framework 6.0 templates | 1h | Backend | PENDING |
| Update pyproject.toml to v1.2.0 | 0.5h | Backend | PENDING |

### Phase 2: Core Features (Sprint 125)

| Task | Effort | Owner | Status |
|------|--------|-------|--------|
| Implement `spec convert` command | 4h | Backend | PENDING |
| Implement `spec list` command | 2h | Backend | PENDING |
| Implement `spec init` command | 2h | Backend | PENDING |
| Create spec_bdd_validator | 3h | Backend | PENDING |
| Create spec_tier_validator | 2h | Backend | PENDING |

### Phase 3: Extension & Polish (Sprint 126)

| Task | Effort | Owner | Status |
|------|--------|-------|--------|
| Update VS Code extension to 6.0.0 | 4h | Frontend | PENDING |
| Add extension spec validation | 3h | Frontend | PENDING |
| Write tests (95%+ coverage) | 4h | Backend | PENDING |
| Update documentation | 2h | Backend | PENDING |
| Publish CLI v1.2.0 to PyPI | 0.5h | Backend | PENDING |
| Publish Extension v1.2.0 | 0.5h | Frontend | PENDING |

**Total Effort**: ~33h across 3 sprints

---

## 7. Testing Strategy

### Unit Tests
- `test_spec_frontmatter_validator.py` - Frontmatter parsing and validation
- `test_spec_bdd_validator.py` - BDD format detection
- `test_spec_tier_validator.py` - Section requirements by tier
- `test_spec_convert.py` - OpenSpec conversion
- `test_spec_list.py` - Inventory listing

### Integration Tests
- End-to-end spec validation workflow
- Convert → Validate → List pipeline
- CLI command integration

### Manual Testing
- Test with real SDLC 6.0.0 specs from Framework
- Test with existing 5.x specs (backward compatibility)
- Test VS Code extension UX

---

## 8. Rollback Plan

If issues discovered post-release:
1. **CLI**: Publish v1.2.1 patch or revert to v1.1.2
2. **Extension**: Unpublish v1.2.0, keep v1.1.2 available
3. **Framework**: No framework changes needed (already at 6.0.0)

---

## 9. References

- [SDLC 6.0.0 CHANGELOG](../../SDLC-Enterprise-Framework/CHANGELOG.md)
- [SPEC-0002: Specification Standard](./SPEC-0002-Specification-Standard.md)
- [spec-frontmatter-schema.json](../../SDLC-Enterprise-Framework/05-Templates-Tools/01-Specification-Standard/spec-frontmatter-schema.json)
- [ADR-014: SDLC Structure Validator](../03-ADRs/ADR-014-SDLC-Structure-Validator.md)

---

**Document Status**: DRAFT
**Created**: 2026-01-30
**Sprint**: 124 - Compliance Validation + CLI Update
