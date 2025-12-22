# SDLC Structure Scanner - Architecture Design

**Document Type**: Technical Architecture Specification
**Sprint**: 44 - SDLC Structure Scanner Engine
**Epic**: EP-04: SDLC Structure Enforcement
**Version**: 1.0.0
**Date**: December 22, 2025
**Status**: APPROVED
**Framework**: SDLC 5.1.1

---

## 1. Executive Summary

This document defines the architecture for the SDLC Structure Scanner, a validation engine that enforces SDLC 5.1.1 folder structure, naming conventions, and document metadata standards. The scanner is designed to be:

- **Tool-agnostic**: Validates OUTPUT regardless of AI tool used (Cursor, Copilot, Claude, etc.)
- **Performance-optimized**: <30 seconds for 1000+ files
- **Extensible**: Plugin architecture for custom validators
- **CI/CD-ready**: JSON output for GitHub Actions integration

---

## 2. Architecture Overview

### 2.1 High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     CLI Layer (sdlcctl)                        │
│                                                                 │
│   $ sdlcctl validate [path] [--format] [--config] [--fix]     │
└─────────────────────────────┬───────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                SDLCStructureScanner (Orchestrator)              │
│                                                                 │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐  │
│  │ Config Loader│  │ Path Resolver│  │ Violation Aggregator │  │
│  └──────────────┘  └──────────────┘  └──────────────────────┘  │
└─────────────────────────────┬───────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                 Parallel Validator Executor                     │
│                                                                 │
│  ThreadPoolExecutor(max_workers=4)                             │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐          │
│  │Validator1│ │Validator2│ │Validator3│ │Validator4│ ...      │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘          │
└─────────────────────────────┬───────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Validator Plugins (5 Built-in)               │
│                                                                 │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐ │
│  │ StageFolderV.   │  │ SequentialNumV. │  │ NamingConventV. │ │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘ │
│  ┌─────────────────┐  ┌─────────────────┐                      │
│  │ HeaderMetadataV.│  │ CrossReferenceV.│                      │
│  └─────────────────┘  └─────────────────┘                      │
└─────────────────────────────────────────────────────────────────┘
```

### 2.2 Component Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│ backend/sdlcctl/                                                │
├─────────────────────────────────────────────────────────────────┤
│ ├── cli.py                    # Main CLI entry point            │
│ ├── commands/                                                   │
│ │   ├── __init__.py                                            │
│ │   ├── validate.py           # validate command (existing)     │
│ │   └── fix.py                # auto-fix command                │
│ ├── validation/                                                 │
│ │   ├── __init__.py                                            │
│ │   ├── scanner.py            # FolderScanner (existing)        │
│ │   ├── structure_scanner.py  # SDLCStructureScanner (NEW)      │
│ │   ├── base_validator.py     # BaseValidator interface (NEW)   │
│ │   ├── violation.py          # ViolationReport dataclass (NEW) │
│ │   └── validators/           # Validator plugins (NEW)         │
│ │       ├── __init__.py                                        │
│ │       ├── stage_folder.py   # StageFolderValidator           │
│ │       ├── numbering.py      # SequentialNumberingValidator   │
│ │       ├── naming.py         # NamingConventionValidator      │
│ │       ├── header.py         # HeaderMetadataValidator        │
│ │       └── cross_ref.py      # CrossReferenceValidator        │
│ └── config/                                                     │
│     ├── __init__.py                                            │
│     ├── schema.py             # Config JSON Schema              │
│     └── loader.py             # Config file loader              │
└─────────────────────────────────────────────────────────────────┘
```

---

## 3. Core Data Structures

### 3.1 ViolationReport

```python
# backend/sdlcctl/validation/violation.py

from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional, Dict, Any
from enum import Enum

class Severity(str, Enum):
    """Violation severity levels."""
    ERROR = "ERROR"       # Blocks merge, must fix
    WARNING = "WARNING"   # Should fix, doesn't block
    INFO = "INFO"         # Informational, optional fix

@dataclass
class ViolationReport:
    """
    SDLC structure violation detected by scanner.

    Attributes:
        rule_id: Unique rule identifier (e.g., STAGE-001)
        severity: ERROR, WARNING, or INFO
        file_path: Path to the file/folder with violation
        message: Human-readable description
        fix_suggestion: Suggested fix (optional)
        auto_fixable: Whether violation can be auto-fixed
        context: Additional context (line numbers, etc.)
    """
    rule_id: str
    severity: Severity
    file_path: Path
    message: str
    fix_suggestion: Optional[str] = None
    auto_fixable: bool = False
    context: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "rule_id": self.rule_id,
            "severity": self.severity.value,
            "path": str(self.file_path),
            "message": self.message,
            "fix_suggestion": self.fix_suggestion,
            "auto_fixable": self.auto_fixable,
            "context": self.context,
        }

    def to_github_annotation(self) -> str:
        """Format as GitHub Actions annotation."""
        level = "error" if self.severity == Severity.ERROR else "warning"
        return f"::{level} file={self.file_path}::{self.message}"
```

### 3.2 ScanResult

```python
# backend/sdlcctl/validation/violation.py (continued)

from dataclasses import dataclass
from typing import List
from datetime import datetime

@dataclass
class ScanResult:
    """Result of a complete structure scan."""

    violations: List[ViolationReport]
    files_scanned: int
    folders_scanned: int
    scan_duration_ms: float
    scanned_at: datetime
    config_path: Optional[Path] = None

    @property
    def error_count(self) -> int:
        return sum(1 for v in self.violations if v.severity == Severity.ERROR)

    @property
    def warning_count(self) -> int:
        return sum(1 for v in self.violations if v.severity == Severity.WARNING)

    @property
    def info_count(self) -> int:
        return sum(1 for v in self.violations if v.severity == Severity.INFO)

    @property
    def has_errors(self) -> bool:
        return self.error_count > 0

    @property
    def fixable_count(self) -> int:
        return sum(1 for v in self.violations if v.auto_fixable)
```

---

## 4. BaseValidator Interface

### 4.1 Abstract Base Class

```python
# backend/sdlcctl/validation/base_validator.py

from abc import ABC, abstractmethod
from pathlib import Path
from typing import List, Optional, Set

from .violation import ViolationReport

class BaseValidator(ABC):
    """
    Abstract base class for all SDLC structure validators.

    Validators are responsible for checking a specific aspect of
    SDLC structure compliance. Each validator should:

    1. Focus on ONE type of validation (Single Responsibility)
    2. Be stateless (can run in parallel)
    3. Return ViolationReport objects
    4. Support configuration overrides
    """

    # Validator metadata
    VALIDATOR_ID: str = ""
    VALIDATOR_NAME: str = ""
    VALIDATOR_VERSION: str = "1.0.0"

    def __init__(self, config: Optional[dict] = None):
        """
        Initialize validator with optional config.

        Args:
            config: Validator-specific configuration
        """
        self.config = config or {}
        self.ignore_patterns: Set[str] = set(
            self.config.get("ignore_patterns", [])
        )

    @abstractmethod
    def validate(
        self,
        docs_root: Path,
        paths: Optional[List[Path]] = None
    ) -> List[ViolationReport]:
        """
        Validate SDLC structure.

        Args:
            docs_root: Root of docs folder
            paths: Optional specific paths to validate

        Returns:
            List of violations found
        """
        pass

    def should_skip(self, path: Path) -> bool:
        """Check if path should be skipped based on ignore patterns."""
        return any(
            pattern in str(path)
            for pattern in self.ignore_patterns
        )

    def get_rule_config(self, rule_id: str) -> dict:
        """Get configuration for a specific rule."""
        rules_config = self.config.get("rules", {})
        return rules_config.get(rule_id, {})

    def is_rule_enabled(self, rule_id: str) -> bool:
        """Check if a rule is enabled."""
        rule_config = self.get_rule_config(rule_id)
        return rule_config.get("enabled", True)

    def get_rule_severity(self, rule_id: str, default: str) -> str:
        """Get severity override for a rule."""
        rule_config = self.get_rule_config(rule_id)
        return rule_config.get("severity", default)
```

### 4.2 Validator Registry

```python
# backend/sdlcctl/validation/base_validator.py (continued)

from typing import Dict, Type

class ValidatorRegistry:
    """Registry for validator plugins."""

    _validators: Dict[str, Type[BaseValidator]] = {}

    @classmethod
    def register(cls, validator_class: Type[BaseValidator]) -> Type[BaseValidator]:
        """
        Register a validator class.

        Usage:
            @ValidatorRegistry.register
            class MyValidator(BaseValidator):
                VALIDATOR_ID = "my-validator"
                ...
        """
        validator_id = validator_class.VALIDATOR_ID
        if not validator_id:
            raise ValueError(f"Validator {validator_class} missing VALIDATOR_ID")
        cls._validators[validator_id] = validator_class
        return validator_class

    @classmethod
    def get(cls, validator_id: str) -> Optional[Type[BaseValidator]]:
        """Get a validator class by ID."""
        return cls._validators.get(validator_id)

    @classmethod
    def get_all(cls) -> Dict[str, Type[BaseValidator]]:
        """Get all registered validators."""
        return cls._validators.copy()

    @classmethod
    def create_instance(
        cls,
        validator_id: str,
        config: Optional[dict] = None
    ) -> Optional[BaseValidator]:
        """Create an instance of a validator."""
        validator_class = cls.get(validator_id)
        if validator_class:
            return validator_class(config)
        return None
```

---

## 5. SDLCStructureScanner (Orchestrator)

### 5.1 Main Scanner Class

```python
# backend/sdlcctl/validation/structure_scanner.py

import asyncio
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Dict, Any

from .base_validator import BaseValidator, ValidatorRegistry
from .violation import ViolationReport, ScanResult, Severity

# Import validators to register them
from .validators import (
    StageFolderValidator,
    SequentialNumberingValidator,
    NamingConventionValidator,
    HeaderMetadataValidator,
    CrossReferenceValidator,
)

@dataclass
class ScannerConfig:
    """Configuration for the structure scanner."""

    max_workers: int = 4
    fail_on_warning: bool = False
    ignore_patterns: List[str] = field(default_factory=list)
    disabled_validators: List[str] = field(default_factory=list)
    disabled_rules: List[str] = field(default_factory=list)
    rule_overrides: Dict[str, Dict[str, Any]] = field(default_factory=dict)


class SDLCStructureScanner:
    """
    Universal SDLC Structure Scanner.

    Orchestrates multiple validators to check SDLC structure compliance.
    Supports parallel execution for performance optimization.

    Features:
    - Tool-agnostic: validates OUTPUT regardless of AI tool
    - Parallel validation with configurable worker count
    - Config-driven rule customization
    - CI/CD-ready output formats

    Usage:
        scanner = SDLCStructureScanner(Path("docs/"))
        result = scanner.scan()
        print(f"Found {result.error_count} errors")
    """

    # Default validators (in execution order)
    DEFAULT_VALIDATORS = [
        "stage-folder",
        "sequential-numbering",
        "naming-convention",
        "header-metadata",
        "cross-reference",
    ]

    def __init__(
        self,
        docs_root: Path,
        config: Optional[ScannerConfig] = None,
        config_path: Optional[Path] = None,
    ):
        """
        Initialize scanner.

        Args:
            docs_root: Path to docs folder
            config: Scanner configuration (or load from config_path)
            config_path: Path to .sdlc-config.json
        """
        self.docs_root = Path(docs_root).resolve()
        self.config = config or ScannerConfig()
        self.config_path = config_path

        if config_path and config_path.exists():
            self._load_config(config_path)

        self.validators: List[BaseValidator] = []
        self._register_validators()

    def _load_config(self, config_path: Path) -> None:
        """Load configuration from JSON file."""
        import json
        with open(config_path, 'r') as f:
            config_data = json.load(f)

        scanner_config = config_data.get("scanner", {})
        self.config.max_workers = scanner_config.get("max_workers", 4)
        self.config.fail_on_warning = scanner_config.get("fail_on_warning", False)
        self.config.ignore_patterns = scanner_config.get("ignore_patterns", [])
        self.config.disabled_validators = scanner_config.get("disabled_validators", [])
        self.config.disabled_rules = scanner_config.get("disabled_rules", [])
        self.config.rule_overrides = scanner_config.get("rule_overrides", {})

    def _register_validators(self) -> None:
        """Register and instantiate validators."""
        for validator_id in self.DEFAULT_VALIDATORS:
            # Skip disabled validators
            if validator_id in self.config.disabled_validators:
                continue

            validator_class = ValidatorRegistry.get(validator_id)
            if validator_class:
                # Create validator with config
                validator_config = {
                    "ignore_patterns": self.config.ignore_patterns,
                    "disabled_rules": self.config.disabled_rules,
                    "rule_overrides": self.config.rule_overrides,
                }
                self.validators.append(validator_class(validator_config))

    def scan(self, paths: Optional[List[Path]] = None) -> ScanResult:
        """
        Scan for SDLC structure violations.

        Args:
            paths: Optional specific paths to scan (default: all)

        Returns:
            ScanResult with all violations
        """
        start_time = time.time()
        all_violations: List[ViolationReport] = []
        files_scanned = 0
        folders_scanned = 0

        # Parallel validation
        with ThreadPoolExecutor(max_workers=self.config.max_workers) as executor:
            futures = {
                executor.submit(
                    validator.validate,
                    self.docs_root,
                    paths
                ): validator
                for validator in self.validators
            }

            for future in as_completed(futures):
                validator = futures[future]
                try:
                    violations = future.result()
                    all_violations.extend(violations)
                except Exception as e:
                    # Create error violation for validator failure
                    all_violations.append(ViolationReport(
                        rule_id="SCANNER-ERROR",
                        severity=Severity.ERROR,
                        file_path=self.docs_root,
                        message=f"Validator {validator.VALIDATOR_ID} failed: {str(e)}",
                    ))

        # Count files and folders
        for path in self.docs_root.rglob("*"):
            if self._should_skip(path):
                continue
            if path.is_file():
                files_scanned += 1
            elif path.is_dir():
                folders_scanned += 1

        # Sort violations by severity, then path
        severity_order = {Severity.ERROR: 0, Severity.WARNING: 1, Severity.INFO: 2}
        all_violations.sort(
            key=lambda v: (severity_order[v.severity], str(v.file_path))
        )

        scan_duration_ms = (time.time() - start_time) * 1000

        return ScanResult(
            violations=all_violations,
            files_scanned=files_scanned,
            folders_scanned=folders_scanned,
            scan_duration_ms=scan_duration_ms,
            scanned_at=datetime.utcnow(),
            config_path=self.config_path,
        )

    def _should_skip(self, path: Path) -> bool:
        """Check if path should be skipped."""
        return any(
            pattern in str(path)
            for pattern in self.config.ignore_patterns
        )

    def get_validators(self) -> List[str]:
        """Get list of active validator IDs."""
        return [v.VALIDATOR_ID for v in self.validators]
```

---

## 6. Validator Implementations

### 6.1 StageFolderValidator

```python
# backend/sdlcctl/validation/validators/stage_folder.py

import re
from pathlib import Path
from typing import List, Optional

from ..base_validator import BaseValidator, ValidatorRegistry
from ..violation import ViolationReport, Severity

# SDLC 5.1.1 Stage definitions
VALID_STAGES = {
    "00": "foundation",
    "01": "planning",
    "02": "design",
    "03": "integration",
    "04": "build",
    "05": "test",
    "06": "deploy",
    "07": "operate",
    "08": "collaborate",
    "09": "govern",
}

# Special folders (not stages)
SPECIAL_FOLDERS = {"10-archive", "99-legacy"}

@ValidatorRegistry.register
class StageFolderValidator(BaseValidator):
    """
    Validate SDLC 5.1.1 stage folder structure.

    Rules:
    - STAGE-001: Invalid stage folder naming
    - STAGE-002: Unknown stage number
    - STAGE-003: Stage name mismatch
    - STAGE-004: Duplicate stage number
    - STAGE-005: Missing required stage
    """

    VALIDATOR_ID = "stage-folder"
    VALIDATOR_NAME = "Stage Folder Validator"

    STAGE_PATTERN = re.compile(r"^(\d{2})-(.+)$")

    def validate(
        self,
        docs_root: Path,
        paths: Optional[List[Path]] = None
    ) -> List[ViolationReport]:
        violations = []
        found_stages = {}  # {stage_num: [folder_paths]}

        if not docs_root.exists():
            return [ViolationReport(
                rule_id="STAGE-000",
                severity=Severity.ERROR,
                file_path=docs_root,
                message="Docs folder does not exist",
            )]

        for folder in docs_root.iterdir():
            if not folder.is_dir():
                continue

            if self.should_skip(folder):
                continue

            folder_name = folder.name

            # Skip special folders
            if folder_name.lower() in {f.lower() for f in SPECIAL_FOLDERS}:
                continue

            # Check stage pattern
            match = self.STAGE_PATTERN.match(folder_name)
            if not match:
                # STAGE-001: Invalid naming
                if self.is_rule_enabled("STAGE-001"):
                    violations.append(ViolationReport(
                        rule_id="STAGE-001",
                        severity=Severity(self.get_rule_severity("STAGE-001", "ERROR")),
                        file_path=folder,
                        message=f"Invalid stage folder naming: {folder_name}",
                        fix_suggestion="Rename to match pattern: XX-name (e.g., 01-planning)",
                        auto_fixable=True,
                    ))
                continue

            stage_num, stage_name = match.groups()

            # Track for duplicate detection
            if stage_num not in found_stages:
                found_stages[stage_num] = []
            found_stages[stage_num].append(folder)

            # STAGE-002: Unknown stage number
            if stage_num not in VALID_STAGES:
                if self.is_rule_enabled("STAGE-002"):
                    violations.append(ViolationReport(
                        rule_id="STAGE-002",
                        severity=Severity(self.get_rule_severity("STAGE-002", "ERROR")),
                        file_path=folder,
                        message=f"Unknown stage number: {stage_num}",
                        fix_suggestion=f"Valid stage numbers: 00-09",
                        auto_fixable=False,
                    ))
            else:
                # STAGE-003: Stage name mismatch
                expected_name = VALID_STAGES[stage_num]
                if stage_name.lower() != expected_name:
                    if self.is_rule_enabled("STAGE-003"):
                        violations.append(ViolationReport(
                            rule_id="STAGE-003",
                            severity=Severity(self.get_rule_severity("STAGE-003", "WARNING")),
                            file_path=folder,
                            message=f"Stage name mismatch: got '{stage_name}', expected '{expected_name}'",
                            fix_suggestion=f"Rename to: {stage_num}-{expected_name}",
                            auto_fixable=True,
                        ))

        # STAGE-004: Duplicate stage numbers
        if self.is_rule_enabled("STAGE-004"):
            for stage_num, folders in found_stages.items():
                if len(folders) > 1:
                    for folder in folders:
                        violations.append(ViolationReport(
                            rule_id="STAGE-004",
                            severity=Severity(self.get_rule_severity("STAGE-004", "ERROR")),
                            file_path=folder,
                            message=f"Duplicate stage number '{stage_num}'",
                            fix_suggestion=f"Conflicting folders: {[f.name for f in folders]}",
                            auto_fixable=True,
                            context={"duplicates": [str(f) for f in folders]},
                        ))

        # STAGE-005: Missing required stages
        if self.is_rule_enabled("STAGE-005"):
            for stage_num, stage_name in VALID_STAGES.items():
                if stage_num not in found_stages:
                    violations.append(ViolationReport(
                        rule_id="STAGE-005",
                        severity=Severity(self.get_rule_severity("STAGE-005", "WARNING")),
                        file_path=docs_root,
                        message=f"Missing required stage: {stage_num}-{stage_name}",
                        fix_suggestion=f"Create folder: {docs_root}/{stage_num}-{stage_name}",
                        auto_fixable=True,
                    ))

        return violations
```

### 6.2 SequentialNumberingValidator

```python
# backend/sdlcctl/validation/validators/numbering.py

import re
from pathlib import Path
from typing import List, Optional, Dict

from ..base_validator import BaseValidator, ValidatorRegistry
from ..violation import ViolationReport, Severity

@ValidatorRegistry.register
class SequentialNumberingValidator(BaseValidator):
    """
    Detect duplicate subfolder numbering within stages.

    Rules:
    - NUM-001: Duplicate subfolder number
    - NUM-002: Non-sequential numbering (gaps)
    - NUM-003: Invalid subfolder number format
    """

    VALIDATOR_ID = "sequential-numbering"
    VALIDATOR_NAME = "Sequential Numbering Validator"

    NUMBER_PATTERN = re.compile(r"^(\d{2})-(.+)$")

    def validate(
        self,
        docs_root: Path,
        paths: Optional[List[Path]] = None
    ) -> List[ViolationReport]:
        violations = []

        # Scan each stage folder
        for stage_folder in docs_root.iterdir():
            if not stage_folder.is_dir():
                continue

            if self.should_skip(stage_folder):
                continue

            # Skip non-stage folders
            if not self.NUMBER_PATTERN.match(stage_folder.name):
                continue

            # Track numbers in this stage
            number_usage: Dict[str, List[Path]] = {}

            for subfolder in stage_folder.iterdir():
                if not subfolder.is_dir():
                    continue

                if self.should_skip(subfolder):
                    continue

                match = self.NUMBER_PATTERN.match(subfolder.name)
                if match:
                    num = match.group(1)
                    if num not in number_usage:
                        number_usage[num] = []
                    number_usage[num].append(subfolder)

            # NUM-001: Duplicate numbers
            if self.is_rule_enabled("NUM-001"):
                for num, folders in number_usage.items():
                    if len(folders) > 1:
                        for folder in folders:
                            violations.append(ViolationReport(
                                rule_id="NUM-001",
                                severity=Severity(self.get_rule_severity("NUM-001", "ERROR")),
                                file_path=folder,
                                message=f"Duplicate numbering '{num}' in {stage_folder.name}",
                                fix_suggestion=f"Conflicting: {[f.name for f in folders]}",
                                auto_fixable=True,
                                context={
                                    "stage": stage_folder.name,
                                    "duplicates": [str(f) for f in folders],
                                },
                            ))

            # NUM-002: Non-sequential (gaps)
            if self.is_rule_enabled("NUM-002") and number_usage:
                numbers = sorted([int(n) for n in number_usage.keys()])
                expected = list(range(1, len(numbers) + 1))
                if numbers != expected and numbers[0] == 1:
                    violations.append(ViolationReport(
                        rule_id="NUM-002",
                        severity=Severity(self.get_rule_severity("NUM-002", "INFO")),
                        file_path=stage_folder,
                        message=f"Non-sequential numbering in {stage_folder.name}",
                        fix_suggestion=f"Found: {numbers}, Expected: {expected}",
                        auto_fixable=True,
                    ))

        return violations
```

### 6.3 Other Validators (Summary)

| Validator | File | Rules | Purpose |
|-----------|------|-------|---------|
| NamingConventionValidator | naming.py | NAME-001, NAME-002 | Folder/file naming |
| HeaderMetadataValidator | header.py | HDR-001, HDR-002 | Document headers |
| CrossReferenceValidator | cross_ref.py | REF-001, REF-002 | Link validation |

---

## 7. Configuration Schema

### 7.1 .sdlc-config.json Schema

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "properties": {
    "scanner": {
      "type": "object",
      "properties": {
        "max_workers": {
          "type": "integer",
          "default": 4,
          "minimum": 1,
          "maximum": 16
        },
        "fail_on_warning": {
          "type": "boolean",
          "default": false
        },
        "ignore_patterns": {
          "type": "array",
          "items": { "type": "string" },
          "default": ["node_modules", ".git", "__pycache__"]
        },
        "disabled_validators": {
          "type": "array",
          "items": { "type": "string" },
          "default": []
        },
        "disabled_rules": {
          "type": "array",
          "items": { "type": "string" },
          "default": []
        },
        "rule_overrides": {
          "type": "object",
          "additionalProperties": {
            "type": "object",
            "properties": {
              "enabled": { "type": "boolean" },
              "severity": { "enum": ["ERROR", "WARNING", "INFO"] }
            }
          }
        }
      }
    }
  }
}
```

### 7.2 Example Configuration

```json
{
  "scanner": {
    "max_workers": 4,
    "fail_on_warning": false,
    "ignore_patterns": [
      "node_modules",
      ".git",
      "__pycache__",
      "99-legacy"
    ],
    "disabled_validators": [],
    "disabled_rules": ["NUM-002"],
    "rule_overrides": {
      "STAGE-005": {
        "severity": "INFO"
      },
      "NAME-002": {
        "enabled": false
      }
    }
  }
}
```

---

## 8. Performance Optimization

### 8.1 Parallel Processing

```
┌─────────────────────────────────────────────────────────────────┐
│                    Parallel Execution Flow                      │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│    T=0ms     ThreadPoolExecutor(max_workers=4)                 │
│    ┌─────────────────────────────────────────────────┐          │
│    │ Worker 1: StageFolderValidator.validate()       │          │
│    │ Worker 2: SequentialNumberingValidator.validate()│         │
│    │ Worker 3: NamingConventionValidator.validate()  │          │
│    │ Worker 4: HeaderMetadataValidator.validate()    │          │
│    └─────────────────────────────────────────────────┘          │
│                                                                 │
│    T=500ms   First validators complete                          │
│    ┌─────────────────────────────────────────────────┐          │
│    │ Worker 4: CrossReferenceValidator.validate()    │ (reused) │
│    └─────────────────────────────────────────────────┘          │
│                                                                 │
│    T=800ms   All validators complete                            │
│    ┌─────────────────────────────────────────────────┐          │
│    │ Aggregate violations, sort, return ScanResult   │          │
│    └─────────────────────────────────────────────────┘          │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 8.2 Performance Targets

| Metric | Target | Measurement |
|--------|--------|-------------|
| 100 files | <1 second | Benchmark |
| 1,000 files | <10 seconds | Benchmark |
| 10,000 files | <30 seconds | Benchmark |
| Memory | <100MB | Peak usage |
| CPU | 4 cores max | Worker count |

---

## 9. Error Handling

### 9.1 Error Hierarchy

```python
class ScannerError(Exception):
    """Base exception for scanner errors."""
    pass

class ConfigurationError(ScannerError):
    """Invalid configuration."""
    pass

class ValidatorError(ScannerError):
    """Validator execution failed."""
    pass

class PathError(ScannerError):
    """Invalid path or permission denied."""
    pass
```

### 9.2 Error Recovery

| Error Type | Behavior | Output |
|------------|----------|--------|
| Missing docs folder | Return early | STAGE-000 violation |
| Validator exception | Continue | SCANNER-ERROR violation |
| Permission denied | Skip file | Warning log |
| Invalid config | Fail fast | ConfigurationError |

---

## 10. Testing Strategy

### 10.1 Test Fixtures

```
tests/fixtures/
├── valid_structure/          # All stages correct
│   ├── docs/
│   │   ├── 00-foundation/
│   │   ├── 01-planning/
│   │   └── ...
├── duplicate_numbers/        # NUM-001 violations
├── missing_stages/           # STAGE-005 violations
├── invalid_naming/           # NAME-001, NAME-002 violations
└── missing_headers/          # HDR-001, HDR-002 violations
```

### 10.2 Test Matrix

| Test Type | Count | Coverage |
|-----------|-------|----------|
| Unit tests (per validator) | 25 | 90% |
| Integration tests | 10 | Key flows |
| Fixture tests | 5 | Edge cases |
| Performance tests | 3 | Benchmarks |

---

## 11. Approvals

| Role | Name | Date | Status |
|------|------|------|--------|
| Tech Lead | [Pending] | Dec 22, 2025 | ⏳ |
| CTO | [Pending] | Dec 22, 2025 | ⏳ |

---

**Document Version**: 1.0.0
**Last Updated**: December 22, 2025
**Owner**: Backend Team
