# ADR-014: SDLC Structure Validator & Enforcement Tools

**Status**: APPROVED
**Date**: December 3, 2025
**Decision Makers**: CTO, CPO (joint review)
**Stage**: Stage 02 (HOW - Design & Architecture)
**Framework**: SDLC 6.1.0

---

## Context

Per CEO directive và PM/PJM Bflow handover (Dec 3, 2025), cần:

1. **Enforce SDLC 6.1.0 folder structure** across all projects (including RFC-001 legacy archive compliance)
2. **Level-based compliance** based on project size
3. **Automated validation** to prevent non-compliant commits
4. **Templates** for new project scaffolding

### Current Compliance Status

| Project | Size | Compliance | Issues |
|---------|------|------------|--------|
| Bflow Platform | Large | ✅ 100% | Reference standard |
| SDLC-Orchestrator | Large | ⚠️ 85% | `docs/guides/`, `docs/research/` non-compliant |
| NQH-Bot | Medium | ⚠️ 90% | Stage 06 naming |
| SOP-Generator | Medium | ⚠️ 90% | Stage 05 naming |
| AI-Platform | Small | ❌ 70% | Duplicate Stage 05 folders |

### Level-Based Structure (CEO Directive)

```
Level 0: Project root folder (ALL projects)
Level 1: 10 stage folders 00-10 (ALL projects)
Level 2: Category subfolders (Medium + Large projects)
Level 3: Detail sub-subfolders (Large projects only)
```

---

## Decision

Implement **SDLC Structure Validator** with:

1. **sdlc_structure_validator.py**: Python CLI tool for validation
2. **.sdlc-config.json**: Project configuration schema
3. **Project templates**: Small/Medium/Large scaffolding
4. **Pre-commit hook**: Block non-compliant commits
5. **CI/CD workflow**: Pipeline gate for PRs

---

## Architecture Design

### 1. Configuration Schema (.sdlc-config.json)

```json
{
  "$schema": "https://sdlc-orchestrator.io/schemas/sdlc-config-v1.json",
  "version": "1.0.0",
  "project": {
    "name": "SDLC-Orchestrator",
    "size": "large",
    "sdlc_version": "6.0.5"
  },
  "structure": {
    "level": 3,
    "docs_root": "docs",
    "stages": {
      "00": {
        "name": "Project-Foundation",
        "required": true,
        "subfolders": ["01-Vision-Mission", "02-Problem-Statement"]
      },
      "01": {
        "name": "Planning-Analysis",
        "required": true,
        "subfolders": ["01-Requirements", "02-User-Stories"]
      }
    },
    "allowed_root_folders": [
      "backend",
      "frontend",
      "docs",
      "scripts",
      ".github",
      "SDLC-Enterprise-Framework"
    ],
    "ignored_patterns": [
      "node_modules",
      "__pycache__",
      ".git",
      "*.pyc",
      ".env*"
    ]
  },
  "validation": {
    "strict_naming": true,
    "allow_custom_stages": false,
    "max_folder_depth": 5,
    "require_readme": true
  }
}
```

### 2. Stage Naming Standard (Canonical)

```python
# constants/sdlc_stages.py

SDLC_605_STAGES = {
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
    "10": "archive"   # RFC-001: centralized legacy archive (10-archive/{NN}-Legacy/)
}

# Common mistakes to detect (old naming → SDLC 6.1.0 naming)
STAGE_NAME_CORRECTIONS = {
    "Project-Foundation": "foundation",
    "Planning-Analysis": "planning",
    "Design-Architecture": "design",
    "Development-Implementation": "build",
    "Testing-Quality": "test",
    "Deployment-Release": "deploy",
    "Operations-Maintenance": "operate",
    "Integration-APIs": "integrate",
    "Team-Management": "collaborate",
    "Executive-Reports": "govern",
    "Archive": "archive",
}

# RFC-001: Legacy folder violations to detect
LEGACY_VIOLATIONS = {
    "99-Legacy": "SDLC-010: 99-Legacy/ found in active stage. Per RFC-001, "
                 "migrate to docs/10-archive/{NN}-Legacy/"
}
```

### 3. Structure Validator Service

```python
# services/sdlc_structure_validator.py
import os
import json
import re
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

class ProjectSize(Enum):
    SMALL = "small"      # Level 0-1 only
    MEDIUM = "medium"    # Level 0-2
    LARGE = "large"      # Level 0-3

class ValidationSeverity(Enum):
    ERROR = "error"      # Must fix
    WARNING = "warning"  # Should fix
    INFO = "info"        # Nice to have

@dataclass
class ValidationIssue:
    severity: ValidationSeverity
    path: str
    message: str
    suggestion: Optional[str] = None
    auto_fixable: bool = False

@dataclass
class ValidationResult:
    project_name: str
    project_size: ProjectSize
    compliance_score: float
    issues: List[ValidationIssue]
    passed: bool

class SDLCStructureValidator:
    """Validate project structure against SDLC 6.1.0 standards (including RFC-001)"""

    def __init__(self, project_root: Path, config: Optional[Dict] = None):
        self.project_root = Path(project_root)
        self.config = config or self._load_config()
        self.issues: List[ValidationIssue] = []

    def _load_config(self) -> Dict:
        """Load .sdlc-config.json or use defaults"""
        config_path = self.project_root / ".sdlc-config.json"
        if config_path.exists():
            with open(config_path) as f:
                return json.load(f)
        return self._get_default_config()

    def _get_default_config(self) -> Dict:
        """Default configuration for unconfigured projects"""
        return {
            "project": {"size": "medium", "sdlc_version": "6.0.5"},
            "structure": {
                "docs_root": "docs",
                "allowed_root_folders": ["backend", "frontend", "docs", "scripts", ".github"]
            },
            "validation": {"strict_naming": True}
        }

    def validate(self) -> ValidationResult:
        """Run full validation suite"""
        self.issues = []

        # 1. Validate stage folders exist
        self._validate_stage_folders()

        # 2. Validate stage naming
        self._validate_stage_naming()

        # 3. Validate level structure
        self._validate_level_structure()

        # 4. Validate no non-compliant folders
        self._validate_no_stray_folders()

        # 5. Validate RFC-001 compliance (no 99-Legacy in active stages)
        self._validate_rfc001_legacy_archive()

        # 6. Validate README presence (if required)
        if self.config.get("validation", {}).get("require_readme", False):
            self._validate_readme_presence()

        # Calculate compliance score
        total_checks = max(len(self.issues) + 10, 10)  # Baseline 10 checks
        errors = sum(1 for i in self.issues if i.severity == ValidationSeverity.ERROR)
        warnings = sum(1 for i in self.issues if i.severity == ValidationSeverity.WARNING)

        compliance_score = max(0, 100 - (errors * 10) - (warnings * 3))

        return ValidationResult(
            project_name=self.config.get("project", {}).get("name", self.project_root.name),
            project_size=ProjectSize(self.config.get("project", {}).get("size", "medium")),
            compliance_score=compliance_score,
            issues=self.issues,
            passed=errors == 0
        )

    def _validate_stage_folders(self):
        """Validate all 11 stage folders exist"""
        docs_root = self.project_root / self.config.get("structure", {}).get("docs_root", "docs")

        if not docs_root.exists():
            self.issues.append(ValidationIssue(
                severity=ValidationSeverity.ERROR,
                path=str(docs_root),
                message=f"Docs root folder '{docs_root}' does not exist",
                suggestion="Create docs/ folder with SDLC stage subfolders",
                auto_fixable=True
            ))
            return

        for stage_id, stage_name in SDLC_605_STAGES.items():
            expected_folder = docs_root / f"{stage_id}-{stage_name}"
            if not expected_folder.exists():
                # Check for common variations
                found_variation = self._find_stage_variation(docs_root, stage_id)
                if found_variation:
                    self.issues.append(ValidationIssue(
                        severity=ValidationSeverity.WARNING,
                        path=str(found_variation),
                        message=f"Stage {stage_id} found but with wrong name: {found_variation.name}",
                        suggestion=f"Rename to: {stage_id}-{stage_name}",
                        auto_fixable=True
                    ))
                else:
                    self.issues.append(ValidationIssue(
                        severity=ValidationSeverity.ERROR,
                        path=str(expected_folder),
                        message=f"Missing required stage folder: {stage_id}-{stage_name}",
                        suggestion=f"Create folder: {expected_folder}",
                        auto_fixable=True
                    ))

    def _find_stage_variation(self, docs_root: Path, stage_id: str) -> Optional[Path]:
        """Find stage folder with different naming"""
        pattern = re.compile(f"^{stage_id}[-_]")
        for folder in docs_root.iterdir():
            if folder.is_dir() and pattern.match(folder.name):
                return folder
        return None

    def _validate_stage_naming(self):
        """Validate stage folders use exact SDLC 6.1.0 naming (lowercase per RFC-001)"""
        docs_root = self.project_root / self.config.get("structure", {}).get("docs_root", "docs")

        if not docs_root.exists():
            return

        for folder in docs_root.iterdir():
            if not folder.is_dir():
                continue

            # Check if it matches stage pattern
            match = re.match(r'^(\d{2})[-_](.+)$', folder.name)
            if not match:
                continue

            stage_id, stage_name = match.groups()

            if stage_id in SDLC_605_STAGES:
                expected_name = SDLC_605_STAGES[stage_id]
                if stage_name != expected_name:
                    # Check if it's a known mistake
                    correction = STAGE_NAME_CORRECTIONS.get(stage_name)
                    self.issues.append(ValidationIssue(
                        severity=ValidationSeverity.WARNING,
                        path=str(folder),
                        message=f"Stage {stage_id} has non-standard name: '{stage_name}'",
                        suggestion=f"Rename to: {stage_id}-{expected_name}",
                        auto_fixable=True
                    ))

    def _validate_level_structure(self):
        """Validate folder depth matches project size"""
        project_size = ProjectSize(self.config.get("project", {}).get("size", "medium"))
        docs_root = self.project_root / self.config.get("structure", {}).get("docs_root", "docs")

        max_depth = {
            ProjectSize.SMALL: 1,   # Only stage folders
            ProjectSize.MEDIUM: 2,  # Stage + category
            ProjectSize.LARGE: 3    # Stage + category + detail
        }[project_size]

        # Check depth of all folders
        for root, dirs, files in os.walk(docs_root):
            depth = len(Path(root).relative_to(docs_root).parts)
            if depth > max_depth:
                self.issues.append(ValidationIssue(
                    severity=ValidationSeverity.WARNING,
                    path=root,
                    message=f"Folder depth {depth} exceeds max {max_depth} for {project_size.value} project",
                    suggestion=f"Flatten structure or upgrade project size in .sdlc-config.json"
                ))

    def _validate_no_stray_folders(self):
        """Validate no non-compliant folders in docs/"""
        docs_root = self.project_root / self.config.get("structure", {}).get("docs_root", "docs")

        if not docs_root.exists():
            return

        allowed_patterns = [
            re.compile(r'^\d{2}-'),  # Stage folders
            re.compile(r'^README'),  # README files
            re.compile(r'^\.')       # Hidden files/folders
        ]

        ignored = self.config.get("structure", {}).get("ignored_patterns", [])

        for item in docs_root.iterdir():
            if item.is_dir():
                # Check if matches any allowed pattern
                if not any(p.match(item.name) for p in allowed_patterns):
                    # Check if ignored
                    if item.name not in ignored:
                        self.issues.append(ValidationIssue(
                            severity=ValidationSeverity.ERROR,
                            path=str(item),
                            message=f"Non-compliant folder in docs/: '{item.name}'",
                            suggestion=f"Move to appropriate stage folder or add to ignored_patterns",
                            auto_fixable=False
                        ))

    def _validate_readme_presence(self):
        """Validate README.md in each stage folder"""
        docs_root = self.project_root / self.config.get("structure", {}).get("docs_root", "docs")

        if not docs_root.exists():
            return

        for stage_id, stage_name in SDLC_605_STAGES.items():
            stage_folder = docs_root / f"{stage_id}-{stage_name}"
            readme = stage_folder / "README.md"

            if stage_folder.exists() and not readme.exists():
                self.issues.append(ValidationIssue(
                    severity=ValidationSeverity.INFO,
                    path=str(readme),
                    message=f"Missing README.md in {stage_folder.name}",
                    suggestion="Add README.md explaining stage contents",
                    auto_fixable=True
                ))

    def _validate_rfc001_legacy_archive(self):
        """RFC-001 (SDLC 6.1.0): No 99-Legacy/ folders in active stages 00-09"""
        docs_root = self.project_root / self.config.get("structure", {}).get("docs_root", "docs")

        if not docs_root.exists():
            return

        for stage_id in range(0, 10):  # Active stages 00-09
            for stage_dir in docs_root.iterdir():
                if stage_dir.is_dir() and stage_dir.name.startswith(f"{stage_id:02d}-"):
                    legacy_dir = stage_dir / "99-Legacy"
                    if legacy_dir.exists():
                        self.issues.append(ValidationIssue(
                            severity=ValidationSeverity.ERROR,
                            path=str(legacy_dir),
                            message=f"RFC-001 violation: 99-Legacy/ found in active stage {stage_dir.name}",
                            suggestion=f"Migrate to docs/10-archive/{stage_id:02d}-Legacy/ using: "
                                       f"sdlcctl fix --rfc001",
                            auto_fixable=True
                        ))

    def auto_fix(self, dry_run: bool = True) -> List[str]:
        """Auto-fix issues that are marked as auto_fixable"""
        fixes = []

        for issue in self.issues:
            if not issue.auto_fixable:
                continue

            if "Missing required stage folder" in issue.message:
                folder = Path(issue.path)
                if dry_run:
                    fixes.append(f"Would create: {folder}")
                else:
                    folder.mkdir(parents=True, exist_ok=True)
                    fixes.append(f"Created: {folder}")

            elif "Rename to:" in issue.suggestion:
                old_path = Path(issue.path)
                new_name = issue.suggestion.replace("Rename to: ", "")
                new_path = old_path.parent / new_name
                if dry_run:
                    fixes.append(f"Would rename: {old_path} → {new_path}")
                else:
                    old_path.rename(new_path)
                    fixes.append(f"Renamed: {old_path} → {new_path}")

        return fixes
```

### 4. CLI Tool

```python
#!/usr/bin/env python3
# scripts/sdlc_validate.py
"""
SDLC Structure Validator CLI

Usage:
    sdlc-validate [OPTIONS] [PROJECT_PATH]

Options:
    --strict        Exit with error on any issues
    --fix           Auto-fix issues (interactive)
    --fix-all       Auto-fix all issues without prompting
    --json          Output as JSON
    --quiet         Only show errors
"""

import argparse
import sys
from pathlib import Path

def main():
    parser = argparse.ArgumentParser(description="SDLC 6.1.0 Structure Validator (RFC-001 compliant)")
    parser.add_argument("project_path", nargs="?", default=".", help="Project root path")
    parser.add_argument("--strict", action="store_true", help="Exit with error on any issues")
    parser.add_argument("--fix", action="store_true", help="Auto-fix issues (interactive)")
    parser.add_argument("--fix-all", action="store_true", help="Auto-fix all without prompting")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    parser.add_argument("--quiet", action="store_true", help="Only show errors")

    args = parser.parse_args()

    # Initialize validator
    validator = SDLCStructureValidator(Path(args.project_path))

    # Run validation
    result = validator.validate()

    # Output results
    if args.json:
        print(json.dumps({
            "project": result.project_name,
            "size": result.project_size.value,
            "compliance_score": result.compliance_score,
            "passed": result.passed,
            "issues": [
                {
                    "severity": i.severity.value,
                    "path": i.path,
                    "message": i.message,
                    "suggestion": i.suggestion,
                    "auto_fixable": i.auto_fixable
                }
                for i in result.issues
            ]
        }, indent=2))
    else:
        print(f"\n📊 SDLC Structure Validation Report")
        print(f"{'='*50}")
        print(f"Project: {result.project_name}")
        print(f"Size: {result.project_size.value}")
        print(f"Compliance: {result.compliance_score:.1f}%")
        print(f"Status: {'✅ PASSED' if result.passed else '❌ FAILED'}")
        print(f"{'='*50}\n")

        if result.issues:
            for issue in result.issues:
                if args.quiet and issue.severity != ValidationSeverity.ERROR:
                    continue

                icon = {"error": "❌", "warning": "⚠️", "info": "ℹ️"}[issue.severity.value]
                print(f"{icon} [{issue.severity.value.upper()}] {issue.message}")
                print(f"   Path: {issue.path}")
                if issue.suggestion:
                    print(f"   Fix: {issue.suggestion}")
                if issue.auto_fixable:
                    print(f"   [Auto-fixable]")
                print()

    # Handle auto-fix
    if args.fix or args.fix_all:
        fixes = validator.auto_fix(dry_run=not args.fix_all)
        if fixes:
            print(f"\n🔧 Auto-fix {'Preview' if not args.fix_all else 'Applied'}:")
            for fix in fixes:
                print(f"   {fix}")

            if args.fix and not args.fix_all:
                confirm = input("\nApply these fixes? [y/N]: ")
                if confirm.lower() == 'y':
                    validator.auto_fix(dry_run=False)
                    print("✅ Fixes applied")

    # Exit code
    if args.strict and result.issues:
        sys.exit(1)
    elif not result.passed:
        sys.exit(1)

if __name__ == "__main__":
    main()
```

### 5. Pre-commit Hook

```yaml
# .pre-commit-config.yaml
repos:
  - repo: local
    hooks:
      - id: sdlc-structure-validate
        name: SDLC Structure Validator
        entry: python scripts/sdlc_validate.py --strict --quiet
        language: python
        pass_filenames: false
        always_run: true
        stages: [commit, push]
```

### 6. GitHub Actions Workflow

```yaml
# .github/workflows/sdlc-compliance.yml
name: SDLC Compliance Check

on:
  pull_request:
    branches: [main, develop]
    paths:
      - 'docs/**'
      - '.sdlc-config.json'

jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Run SDLC Validator
        run: |
          python scripts/sdlc_validate.py --strict --json > validation-report.json

      - name: Upload Report
        uses: actions/upload-artifact@v3
        with:
          name: sdlc-validation-report
          path: validation-report.json

      - name: Check Compliance
        run: |
          SCORE=$(jq '.compliance_score' validation-report.json)
          echo "Compliance Score: $SCORE%"
          if [ $(echo "$SCORE < 90" | bc) -eq 1 ]; then
            echo "❌ Compliance below 90%"
            exit 1
          fi
          echo "✅ Compliance check passed"
```

---

## Implementation Plan

### Phase 1: Validator Tool (Sprint 23 Day 5)
- [ ] Implement `SDLCStructureValidator` class
- [ ] Create `.sdlc-config.json` schema
- [ ] Build CLI interface
- [ ] Add to SDLC-Enterprise-Framework/06-Templates-Tools/

### Phase 2: Templates (Sprint 24)
- [ ] Small project template
- [ ] Medium project template
- [ ] Large project template
- [ ] Template generator script

### Phase 3: CI/CD Integration (Sprint 25)
- [ ] Pre-commit hook
- [ ] GitHub Actions workflow
- [ ] Documentation

---

## Consequences

### Positive

1. **Automated Enforcement**: No manual compliance checking
2. **Consistent Structure**: All projects follow same standard
3. **Self-Documenting**: .sdlc-config.json explains project setup
4. **Scalable**: Works across 5+ projects automatically

### Negative

1. **Initial Effort**: Fix existing non-compliant projects
2. **Learning Curve**: Team needs to understand tool
3. **False Positives**: May flag legitimate custom folders

### Risks

1. **Resistance**: Teams may resist structure enforcement
   - **Mitigation**: Clear communication of benefits, gradual rollout

2. **Over-Engineering**: Too strict validation blocks productivity
   - **Mitigation**: Warning vs Error distinction, ignored_patterns

---

## Approval

| Role | Name | Decision | Date | Comment |
|------|------|----------|------|---------|
| **CTO** | [CTO Name] | ✅ APPROVED | Dec 3, 2025 | Essential for governance scale |
| **CPO** | [CPO Name] | ✅ APPROVED | Dec 3, 2025 | Per Bflow team handover |

---

**Decision**: **APPROVED** - SDLC Structure Validator

**Priority**: **HIGH** - Immediate action per handover

**Timeline**: Sprint 23 Day 5 (Docs Foundation)

---

## References

- [PM-PJM-SDLC-FRAMEWORK-HANDOVER-DEC3-2025.md](../../09-Executive-Reports/PM-PJM-SDLC-FRAMEWORK-HANDOVER-DEC3-2025.md)
- [SDLC 6.1.0 Stage Naming Standard](#4-sdlc-stage-naming-standard-exact)
- [Bflow Platform](https://github.com/Minh-Tam-Solution/Bflow-Platform) - Reference implementation
