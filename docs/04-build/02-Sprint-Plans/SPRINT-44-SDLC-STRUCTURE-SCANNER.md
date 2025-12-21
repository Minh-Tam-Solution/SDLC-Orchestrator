# SPRINT-44: SDLC Structure Scanner Engine
## EP-04: Universal AI Codex Structure Validation | Phase 1

---

**Document Information**

| Field | Value |
|-------|-------|
| **Sprint ID** | SPRINT-44 |
| **Epic** | EP-04: SDLC Structure Enforcement |
| **Duration** | 2 weeks (Feb 17 - Feb 28, 2026) |
| **Status** | PLANNED |
| **Team** | 2 Backend + 1 Frontend + 1 QA |
| **Story Points** | 18 SP |
| **Budget** | $2,500 |
| **Framework** | SDLC 5.1.1 + SASE Level 2 |

---

## Sprint Goals

### Primary Objectives

| # | Objective | Priority | Owner |
|---|-----------|----------|-------|
| 1 | Implement SDLC folder structure scanner | P0 | Backend Lead |
| 2 | Create naming convention validator | P0 | Backend Dev 1 |
| 3 | Build duplicate numbering detector | P0 | Backend Dev 1 |
| 4 | Create header metadata validator | P1 | Backend Dev 2 |
| 5 | Integrate with sdlcctl CLI | P0 | Backend Lead |

### Success Criteria

| Metric | Target | Measurement |
|--------|--------|-------------|
| Scanner accuracy | ≥95% | Test on 500+ files |
| Detection coverage | 5 violation types | Unit tests |
| CLI integration | Working `sdlcctl validate` | E2E test |
| Performance (1K files) | <30 seconds | Benchmark |

---

## Week 1: Scanner Foundation (Feb 17-21)

### Day 1-2: Core Scanner Architecture

**Task**: Create base scanner framework with parallel processing

```python
# backend/sdlcctl/validation/structure_scanner.py

from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional
import asyncio
from concurrent.futures import ThreadPoolExecutor

@dataclass
class ViolationReport:
    """SDLC structure violation detected by scanner"""
    rule_id: str
    severity: str  # ERROR, WARNING, INFO
    file_path: Path
    message: str
    fix_suggestion: Optional[str] = None
    auto_fixable: bool = False

class SDLCStructureScanner:
    """
    Universal SDLC Structure Scanner
    - Tool-agnostic: validates OUTPUT regardless of AI tool used
    - Supports: Cursor, Copilot, Claude Code, ChatGPT, etc.
    """
    
    def __init__(self, docs_root: Path, config_path: Optional[Path] = None):
        self.docs_root = docs_root
        self.config = self._load_config(config_path)
        self.validators: List[BaseValidator] = []
        self._register_validators()
    
    def _register_validators(self):
        """Register all validation rules"""
        self.validators = [
            StageFolderValidator(),
            SequentialNumberingValidator(),
            NamingConventionValidator(),
            HeaderMetadataValidator(),
            CrossReferenceValidator(),
        ]
    
    async def scan(self, paths: Optional[List[Path]] = None) -> List[ViolationReport]:
        """Scan for SDLC structure violations"""
        violations = []
        
        # Parallel scanning with ThreadPoolExecutor
        with ThreadPoolExecutor(max_workers=4) as executor:
            futures = []
            for validator in self.validators:
                future = executor.submit(validator.validate, self.docs_root, paths)
                futures.append(future)
            
            for future in futures:
                violations.extend(future.result())
        
        return sorted(violations, key=lambda v: (v.severity, v.file_path))
```

**Acceptance Criteria**:
- [ ] Scanner initializes with docs root path
- [ ] Loads `.sdlc-config.json` if present
- [ ] Registers 5 core validators
- [ ] Parallel execution reduces scan time by 50%

---

### Day 3-4: Folder Structure Validation

**Task**: Implement SDLC 5.1 stage folder validation

```python
# backend/sdlcctl/validation/validators/stage_folder_validator.py

class StageFolderValidator(BaseValidator):
    """
    Validate SDLC 5.1 stage folder structure
    
    Expected structure:
    docs/
    ├── 00-foundation/
    ├── 01-planning/
    ├── 02-design/
    ├── 03-integrate/
    ├── 04-build/
    ├── 05-test/
    ├── 06-deploy/
    ├── 07-operate/
    ├── 08-collaborate/
    └── 09-govern/
    """
    
    VALID_STAGES = {
        "00": "foundation",
        "01": "planning", 
        "02": "design",
        "03": "integrate",
        "04": "build",
        "05": "test",
        "06": "deploy",
        "07": "operate",
        "08": "collaborate",
        "09": "govern",
    }
    
    def validate(self, docs_root: Path, paths: Optional[List[Path]] = None) -> List[ViolationReport]:
        violations = []
        
        for folder in docs_root.iterdir():
            if not folder.is_dir():
                continue
            
            # Check stage folder naming
            match = re.match(r"^(\d{2})-(.+)$", folder.name)
            if not match:
                if folder.name not in ["10-archive", "99-legacy"]:
                    violations.append(ViolationReport(
                        rule_id="STAGE-001",
                        severity="ERROR",
                        file_path=folder,
                        message=f"Invalid stage folder naming: {folder.name}",
                        fix_suggestion=f"Rename to match pattern: XX-name",
                        auto_fixable=True
                    ))
                continue
            
            stage_num, stage_name = match.groups()
            
            # Validate stage number
            if stage_num not in self.VALID_STAGES:
                if stage_num not in ["10", "99"]:  # Archive exceptions
                    violations.append(ViolationReport(
                        rule_id="STAGE-002",
                        severity="ERROR",
                        file_path=folder,
                        message=f"Unknown stage number: {stage_num}",
                        fix_suggestion=f"Valid stages: 00-09",
                        auto_fixable=False
                    ))
            
            # Validate stage name matches number
            expected_name = self.VALID_STAGES.get(stage_num)
            if expected_name and stage_name != expected_name:
                violations.append(ViolationReport(
                    rule_id="STAGE-003",
                    severity="WARNING",
                    file_path=folder,
                    message=f"Stage name mismatch: {stage_name} (expected: {expected_name})",
                    fix_suggestion=f"Rename to: {stage_num}-{expected_name}",
                    auto_fixable=True
                ))
        
        return violations
```

**Test Cases**:
```python
# tests/unit/test_stage_folder_validator.py

def test_valid_structure():
    """All standard stages pass validation"""
    scanner = SDLCStructureScanner(Path("tests/fixtures/valid_structure"))
    violations = scanner.scan()
    assert len(violations) == 0

def test_duplicate_numbering():
    """Detect duplicate stage numbers"""
    scanner = SDLCStructureScanner(Path("tests/fixtures/duplicate_numbers"))
    violations = scanner.scan()
    assert any(v.rule_id == "STAGE-004" for v in violations)

def test_missing_stage():
    """Detect missing required stages"""
    scanner = SDLCStructureScanner(Path("tests/fixtures/missing_stages"))
    violations = scanner.scan()
    assert any(v.rule_id == "STAGE-005" for v in violations)
```

---

### Day 5: Sequential Numbering Validator

**Task**: Detect duplicate/conflicting subfolder numbers

```python
# backend/sdlcctl/validation/validators/numbering_validator.py

class SequentialNumberingValidator(BaseValidator):
    """
    Detect duplicate subfolder numbering within stages
    
    Problem (Dec 21, 2025):
    docs/02-design/
    ├── 01-ADRs/           ✅
    ├── 01-System-Architecture/  ❌ DUPLICATE 01
    ├── 03-ADRs/           ❌ DUPLICATE 03
    ├── 03-API-Design/     ❌ DUPLICATE 03
    """
    
    def validate(self, docs_root: Path, paths: Optional[List[Path]] = None) -> List[ViolationReport]:
        violations = []
        
        for stage_folder in docs_root.iterdir():
            if not stage_folder.is_dir():
                continue
            
            # Track numbers used in this stage
            number_usage = {}  # {number: [folder_paths]}
            
            for subfolder in stage_folder.iterdir():
                if not subfolder.is_dir():
                    continue
                
                match = re.match(r"^(\d{2})-(.+)$", subfolder.name)
                if match:
                    num = match.group(1)
                    if num not in number_usage:
                        number_usage[num] = []
                    number_usage[num].append(subfolder)
            
            # Report duplicates
            for num, folders in number_usage.items():
                if len(folders) > 1:
                    for folder in folders:
                        violations.append(ViolationReport(
                            rule_id="NUM-001",
                            severity="ERROR",
                            file_path=folder,
                            message=f"Duplicate numbering '{num}' in {stage_folder.name}",
                            fix_suggestion=f"Conflicting folders: {[f.name for f in folders]}",
                            auto_fixable=True
                        ))
        
        return violations
```

---

## Week 2: Validators & CLI Integration (Feb 24-28)

### Day 6-7: Naming Convention & Header Validators

**Task**: Validate file/folder naming and document headers

```python
# backend/sdlcctl/validation/validators/naming_validator.py

class NamingConventionValidator(BaseValidator):
    """
    Validate SDLC 5.1 naming conventions
    
    Rules:
    - Folders: kebab-case (01-planning, 02-design)
    - Files: UPPER-KEBAB.md (ADR-001-TITLE.md, SPRINT-41-PLAN.md)
    """
    
    FOLDER_PATTERN = r"^(\d{2}-)?.+$"  # Optional prefix + kebab-case
    FILE_PATTERN = r"^[A-Z][A-Z0-9-]+\.md$"  # UPPER-KEBAB.md
    
    def validate(self, docs_root: Path, paths: Optional[List[Path]] = None) -> List[ViolationReport]:
        violations = []
        
        for path in docs_root.rglob("*"):
            if path.is_dir():
                # Check folder naming
                if not re.match(self.FOLDER_PATTERN, path.name):
                    violations.append(ViolationReport(
                        rule_id="NAME-001",
                        severity="WARNING",
                        file_path=path,
                        message=f"Non-standard folder name: {path.name}",
                        auto_fixable=True
                    ))
            
            elif path.suffix == ".md":
                # Check markdown file naming
                if not re.match(self.FILE_PATTERN, path.name):
                    # Exception for README.md
                    if path.name.lower() != "readme.md":
                        violations.append(ViolationReport(
                            rule_id="NAME-002",
                            severity="INFO",
                            file_path=path,
                            message=f"Non-standard file name: {path.name}",
                            auto_fixable=False
                        ))
        
        return violations
```

```python
# backend/sdlcctl/validation/validators/header_validator.py

class HeaderMetadataValidator(BaseValidator):
    """
    Validate SDLC document header metadata
    
    Required fields:
    - Version
    - Date
    - Stage
    - Status
    """
    
    REQUIRED_FIELDS = ["Version", "Date", "Stage", "Status"]
    
    def validate(self, docs_root: Path, paths: Optional[List[Path]] = None) -> List[ViolationReport]:
        violations = []
        
        for md_file in docs_root.rglob("*.md"):
            content = md_file.read_text(encoding="utf-8")
            
            # Check for header table
            header_match = re.search(r"\|.*Field.*\|.*Value.*\|", content, re.IGNORECASE)
            if not header_match:
                violations.append(ViolationReport(
                    rule_id="HDR-001",
                    severity="WARNING",
                    file_path=md_file,
                    message="Missing document header table",
                    auto_fixable=True
                ))
                continue
            
            # Check required fields
            for field in self.REQUIRED_FIELDS:
                if not re.search(rf"\|\s*\**{field}\**\s*\|", content, re.IGNORECASE):
                    violations.append(ViolationReport(
                        rule_id="HDR-002",
                        severity="WARNING",
                        file_path=md_file,
                        message=f"Missing required header field: {field}",
                        auto_fixable=True
                    ))
        
        return violations
```

---

### Day 8-9: CLI Integration

**Task**: Integrate scanner with `sdlcctl validate` command

```python
# backend/sdlcctl/commands/validate.py

import typer
from rich.console import Console
from rich.table import Table
from pathlib import Path

from ..validation.structure_scanner import SDLCStructureScanner, ViolationReport

app = typer.Typer()
console = Console()

@app.command()
def validate(
    path: Path = typer.Argument(
        Path("."),
        help="Path to docs folder or project root"
    ),
    config: Path = typer.Option(
        None,
        "--config", "-c",
        help="Path to .sdlc-config.json"
    ),
    output_format: str = typer.Option(
        "table",
        "--format", "-f",
        help="Output format: table, json, github"
    ),
    fail_on_warning: bool = typer.Option(
        False,
        "--fail-on-warning",
        help="Exit with error on warnings"
    ),
):
    """
    Validate SDLC folder structure and naming conventions.
    
    Examples:
        sdlcctl validate
        sdlcctl validate docs/
        sdlcctl validate --format json
        sdlcctl validate --fail-on-warning
    """
    # Auto-detect docs folder
    docs_path = _find_docs_folder(path)
    if not docs_path:
        console.print("[red]❌ Could not find docs/ folder[/red]")
        raise typer.Exit(1)
    
    console.print(f"[cyan]🔍 Scanning {docs_path}...[/cyan]")
    
    # Run scanner
    scanner = SDLCStructureScanner(docs_path, config)
    violations = scanner.scan()
    
    # Output results
    if output_format == "table":
        _print_table(violations)
    elif output_format == "json":
        _print_json(violations)
    elif output_format == "github":
        _print_github_annotations(violations)
    
    # Summary
    errors = [v for v in violations if v.severity == "ERROR"]
    warnings = [v for v in violations if v.severity == "WARNING"]
    
    console.print(f"\n[bold]Summary:[/bold] {len(errors)} errors, {len(warnings)} warnings")
    
    # Exit code
    if errors:
        console.print("[red]❌ Validation FAILED[/red]")
        raise typer.Exit(1)
    elif warnings and fail_on_warning:
        console.print("[yellow]⚠️ Validation failed (warnings)[/yellow]")
        raise typer.Exit(1)
    else:
        console.print("[green]✅ Validation PASSED[/green]")

def _print_table(violations: list[ViolationReport]):
    """Print violations as rich table"""
    if not violations:
        console.print("[green]No violations found![/green]")
        return
    
    table = Table(title="SDLC Structure Violations")
    table.add_column("Severity", style="bold")
    table.add_column("Rule")
    table.add_column("Path")
    table.add_column("Message")
    table.add_column("Fixable")
    
    for v in violations:
        severity_style = {
            "ERROR": "red",
            "WARNING": "yellow",
            "INFO": "blue"
        }.get(v.severity, "white")
        
        table.add_row(
            f"[{severity_style}]{v.severity}[/{severity_style}]",
            v.rule_id,
            str(v.file_path.relative_to(Path.cwd())),
            v.message,
            "✅" if v.auto_fixable else "❌"
        )
    
    console.print(table)
```

---

### Day 10: Testing & Documentation

**Task**: Comprehensive test suite and user documentation

**Test Matrix**:
| Test Type | Count | Coverage |
|-----------|-------|----------|
| Unit tests | 25 | 90% |
| Integration tests | 10 | Key flows |
| Fixture tests | 5 structures | Edge cases |

**User Documentation**:
```markdown
# sdlcctl validate

## Quick Start

```bash
# Validate current project
sdlcctl validate

# Validate specific folder
sdlcctl validate docs/

# Output as JSON (for CI)
sdlcctl validate --format json

# Strict mode (fail on warnings)
sdlcctl validate --fail-on-warning
```

## Violation Rules

| Rule ID | Severity | Description |
|---------|----------|-------------|
| STAGE-001 | ERROR | Invalid stage folder naming |
| STAGE-002 | ERROR | Unknown stage number |
| STAGE-003 | WARNING | Stage name mismatch |
| NUM-001 | ERROR | Duplicate subfolder numbering |
| NAME-001 | WARNING | Non-standard folder name |
| NAME-002 | INFO | Non-standard file name |
| HDR-001 | WARNING | Missing header table |
| HDR-002 | WARNING | Missing required header field |
```

---

## Deliverables

| # | Deliverable | Status |
|---|-------------|--------|
| 1 | `SDLCStructureScanner` class | ⏳ |
| 2 | `StageFolderValidator` | ⏳ |
| 3 | `SequentialNumberingValidator` | ⏳ |
| 4 | `NamingConventionValidator` | ⏳ |
| 5 | `HeaderMetadataValidator` | ⏳ |
| 6 | `sdlcctl validate` command | ⏳ |
| 7 | Unit tests (25) | ⏳ |
| 8 | User documentation | ⏳ |

---

## Dependencies

| Dependency | Status | Owner |
|------------|--------|-------|
| sdlcctl CLI framework | ✅ Exists | - |
| `.sdlc-config.json` schema | ✅ EP-05 | - |
| Test fixtures | ⏳ Create | QA |

---

## Risk Mitigation

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Complex edge cases | Medium | Medium | Extensive fixture tests |
| Performance on large repos | Low | Medium | Parallel processing |
| False positives | Medium | High | Configurable rules |

---

*Sprint planned: December 21, 2025*
*CTO Approval: Pending*
