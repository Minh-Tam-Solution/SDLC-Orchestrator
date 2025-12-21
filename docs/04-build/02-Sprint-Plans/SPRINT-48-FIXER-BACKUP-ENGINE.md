# SPRINT-48: Fixer Engine & Backup System
## EP-05: Enterprise SDLC Migration | Phase 2

---

**Document Information**

| Field | Value |
|-------|-------|
| **Sprint ID** | SPRINT-48 |
| **Epic** | EP-05: Enterprise SDLC Migration Engine |
| **Duration** | 2 weeks (Apr 21 - May 2, 2026) |
| **Status** | PLANNED |
| **Team** | 3 Backend + 1 DevOps + 1 QA |
| **Story Points** | 24 SP |
| **Budget** | $14,000 |
| **Framework** | SDLC 5.1.1 + SASE Level 2 |
| **Reference** | ADR-020, Sprint 47 |

---

## Sprint Goals

### Primary Objectives

| # | Objective | Priority | Owner |
|---|-----------|----------|-------|
| 1 | Implement Auto-Fix Engine with 15 fixer types | P0 | Backend Lead |
| 2 | Build backup system with git integration | P0 | DevOps Lead |
| 3 | Create migration plan executor | P0 | Backend Dev 1 |
| 4 | Implement rollback mechanism | P1 | DevOps Lead |
| 5 | CLI integration (`sdlcctl migrate`) | P0 | Backend Dev 2 |

### Success Criteria (from ADR-020)

| Metric | Target | Measurement |
|--------|--------|-------------|
| Fix accuracy | ≥95% | Test on known issues |
| Backup reliability | 100% | No data loss in tests |
| Rollback time | <30 seconds | Benchmark |
| Migration success rate | ≥90% | End-to-end tests |

---

## Architecture

### Migration Engine Flow

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  SDLC Migration Engine (from ADR-020)                                       │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌──────────────┐      ┌──────────────┐      ┌──────────────┐              │
│  │  ScanReport  │─────▶│ MigrationPlan│─────▶│   Executor   │              │
│  │ (Sprint 47)  │      │  Generator   │      │              │              │
│  └──────────────┘      └──────────────┘      └──────┬───────┘              │
│                                                      │                      │
│                                                      ▼                      │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │                           Fixer Pipeline                              │  │
│  │  ┌────────────┐  ┌────────────┐  ┌────────────┐  ┌────────────┐      │  │
│  │  │ HeaderFixer│──│NameFixer   │──│ StageFixer │──│RefFixer    │      │  │
│  │  └────────────┘  └────────────┘  └────────────┘  └────────────┘      │  │
│  │                                                                       │  │
│  │  ┌────────────┐  ┌────────────┐  ┌────────────┐  ┌────────────┐      │  │
│  │  │VersionFix │──│ StructFix  │──│ ConsolidFix│──│ MetadataFix│      │  │
│  │  └────────────┘  └────────────┘  └────────────┘  └────────────┘      │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
│                                                      │                      │
│                                                      ▼                      │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │                        Backup & Commit                                │  │
│  │                                                                       │  │
│  │  1. Create backup branch: migration-backup-{timestamp}                │  │
│  │  2. Apply fixes atomically                                            │  │
│  │  3. Commit with detailed message                                      │  │
│  │  4. Store rollback info                                               │  │
│  │                                                                       │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
│                                                      │                      │
│                                                      ▼                      │
│  Output: MigrationResult                                                    │
│  - files_modified: int                                                      │
│  - fixes_applied: int                                                       │
│  - backup_branch: str                                                       │
│  - rollback_command: str                                                    │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Week 1: Fixer Engine (Apr 21-25)

### Day 1-2: Base Fixer Framework

**Task**: Create extensible fixer framework with 15 fixer types

```python
# backend/sdlcctl/migration/fixers/base.py

from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Dict, Any
from enum import Enum

class FixType(Enum):
    """Types of fixes supported"""
    HEADER = "header"
    NAMING = "naming"
    STAGE = "stage"
    REFERENCE = "reference"
    VERSION = "version"
    STRUCTURE = "structure"
    CONSOLIDATION = "consolidation"
    METADATA = "metadata"

class FixSeverity(Enum):
    """Fix severity levels"""
    CRITICAL = "critical"  # Must fix for compliance
    WARNING = "warning"    # Should fix
    INFO = "info"          # Optional improvement

@dataclass
class Fix:
    """Represents a single fix to apply"""
    file_path: Path
    fix_type: FixType
    severity: FixSeverity
    description: str
    old_content: str
    new_content: str
    line_start: Optional[int] = None
    line_end: Optional[int] = None
    metadata: Dict[str, Any] = None

@dataclass
class FixResult:
    """Result of applying a fix"""
    fix: Fix
    success: bool
    error: Optional[str] = None
    backup_path: Optional[Path] = None

class BaseFixer(ABC):
    """Base class for all fixers"""
    
    fix_type: FixType
    description: str
    
    def __init__(self, config: 'SDLCConfig'):
        self.config = config
    
    @abstractmethod
    def detect(self, content: str, file_path: Path) -> List[Fix]:
        """Detect issues that need fixing in the content"""
        pass
    
    @abstractmethod
    def apply(self, fix: Fix) -> FixResult:
        """Apply a single fix"""
        pass
    
    def apply_batch(self, fixes: List[Fix]) -> List[FixResult]:
        """Apply multiple fixes"""
        results = []
        for fix in fixes:
            result = self.apply(fix)
            results.append(result)
        return results


class FixerRegistry:
    """Registry of all available fixers"""
    
    _fixers: Dict[FixType, type] = {}
    
    @classmethod
    def register(cls, fixer_class: type):
        """Register a fixer class"""
        cls._fixers[fixer_class.fix_type] = fixer_class
        return fixer_class
    
    @classmethod
    def get_fixer(cls, fix_type: FixType, config: 'SDLCConfig') -> BaseFixer:
        """Get a fixer instance by type"""
        fixer_class = cls._fixers.get(fix_type)
        if not fixer_class:
            raise ValueError(f"No fixer registered for type: {fix_type}")
        return fixer_class(config)
    
    @classmethod
    def get_all_fixers(cls, config: 'SDLCConfig') -> List[BaseFixer]:
        """Get all registered fixers"""
        return [fixer_class(config) for fixer_class in cls._fixers.values()]
```

---

### Day 3-4: Core Fixers Implementation

**Task**: Implement 8 core fixers

```python
# backend/sdlcctl/migration/fixers/header_fixer.py

import re
from pathlib import Path
from typing import List

@FixerRegistry.register
class HeaderFixer(BaseFixer):
    """Fix missing or malformed SDLC headers"""
    
    fix_type = FixType.HEADER
    description = "Fix document header metadata"
    
    HEADER_TEMPLATE = """
| Field | Value |
|-------|-------|
| **Version** | {version} |
| **Date** | {date} |
| **Stage** | {stage} |
| **Status** | {status} |
| **Author** | {author} |
"""
    
    def detect(self, content: str, file_path: Path) -> List[Fix]:
        """Detect header issues"""
        fixes = []
        
        from ..header_parser import HeaderMetadataParser
        parser = HeaderMetadataParser()
        header = parser.parse(content)
        
        # Check required fields
        required = self.config.required_header_fields
        missing = [f for f in required if f not in header]
        
        if missing:
            fixes.append(Fix(
                file_path=file_path,
                fix_type=self.fix_type,
                severity=FixSeverity.CRITICAL,
                description=f"Missing required fields: {', '.join(missing)}",
                old_content=self._extract_header_section(content),
                new_content=self._generate_header(content, header, missing, file_path),
            ))
        
        # Check version format
        if "Version" in header:
            version = header["Version"]
            if not re.match(r"^\d+\.\d+(\.\d+)?$", version):
                fixes.append(Fix(
                    file_path=file_path,
                    fix_type=self.fix_type,
                    severity=FixSeverity.WARNING,
                    description=f"Invalid version format: {version}",
                    old_content=version,
                    new_content=self._normalize_version(version),
                ))
        
        return fixes
    
    def apply(self, fix: Fix) -> FixResult:
        """Apply header fix"""
        try:
            content = fix.file_path.read_text()
            new_content = content.replace(fix.old_content, fix.new_content)
            fix.file_path.write_text(new_content)
            return FixResult(fix=fix, success=True)
        except Exception as e:
            return FixResult(fix=fix, success=False, error=str(e))
    
    def _extract_header_section(self, content: str) -> str:
        """Extract header table from content"""
        lines = content.split('\n')
        header_lines = []
        in_table = False
        
        for line in lines[:30]:  # First 30 lines
            if '|' in line:
                in_table = True
                header_lines.append(line)
            elif in_table and not line.strip():
                break
        
        return '\n'.join(header_lines) if header_lines else ''
    
    def _generate_header(
        self,
        content: str,
        existing: dict,
        missing: List[str],
        file_path: Path
    ) -> str:
        """Generate complete header with missing fields"""
        from datetime import datetime
        
        stage = self._detect_stage(file_path)
        
        fields = {
            "Version": existing.get("Version", self.config.sdlc_version),
            "Date": existing.get("Date", datetime.now().strftime("%Y-%m-%d")),
            "Stage": existing.get("Stage", stage),
            "Status": existing.get("Status", "Draft"),
            "Author": existing.get("Author", "Auto-generated"),
        }
        
        return self.HEADER_TEMPLATE.format(**fields)
    
    def _detect_stage(self, file_path: Path) -> str:
        """Detect stage from file path"""
        parts = file_path.parts
        for part in parts:
            if re.match(r"^\d{2}-", part):
                return part
        return "00-foundation"
    
    def _normalize_version(self, version: str) -> str:
        """Normalize version to standard format"""
        match = re.search(r"(\d+)\.(\d+)", version)
        if match:
            return f"{match.group(1)}.{match.group(2)}.0"
        return self.config.sdlc_version


# backend/sdlcctl/migration/fixers/naming_fixer.py

@FixerRegistry.register
class NamingFixer(BaseFixer):
    """Fix file and folder naming issues"""
    
    fix_type = FixType.NAMING
    description = "Fix file and folder naming conventions"
    
    NAMING_PATTERNS = {
        "short": r"^(\d{2})-([a-z-]+)$",           # 00-foundation
        "long": r"^(\d{2})-([A-Z][a-z]+(-[A-Z][a-z]+)*)$",  # 00-Project-Foundation
    }
    
    def detect(self, content: str, file_path: Path) -> List[Fix]:
        """Detect naming issues"""
        fixes = []
        
        # Check folder naming
        for part in file_path.parts:
            if re.match(r"^\d{2}-", part):
                pattern = self.NAMING_PATTERNS.get(self.config.naming)
                if pattern and not re.match(pattern, part):
                    fixes.append(Fix(
                        file_path=file_path,
                        fix_type=self.fix_type,
                        severity=FixSeverity.WARNING,
                        description=f"Folder '{part}' doesn't match {self.config.naming} naming",
                        old_content=part,
                        new_content=self._convert_naming(part),
                    ))
        
        return fixes
    
    def apply(self, fix: Fix) -> FixResult:
        """Apply naming fix (rename file/folder)"""
        try:
            old_path = fix.file_path
            new_path = Path(str(old_path).replace(fix.old_content, fix.new_content))
            
            # Create parent directories
            new_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Move file
            old_path.rename(new_path)
            
            return FixResult(fix=fix, success=True)
        except Exception as e:
            return FixResult(fix=fix, success=False, error=str(e))
    
    def _convert_naming(self, folder_name: str) -> str:
        """Convert folder name to target naming convention"""
        match = re.match(r"^(\d{2})-(.+)$", folder_name)
        if not match:
            return folder_name
        
        prefix, name = match.groups()
        
        if self.config.naming == "short":
            # Convert to lowercase with hyphens
            name = name.lower().replace("_", "-")
            name = re.sub(r"([a-z])([A-Z])", r"\1-\2", name).lower()
        else:
            # Convert to Title-Case
            words = re.split(r"[-_]", name)
            name = "-".join(word.title() for word in words)
        
        return f"{prefix}-{name}"


# backend/sdlcctl/migration/fixers/reference_fixer.py

@FixerRegistry.register
class ReferenceFixer(BaseFixer):
    """Fix broken cross-references in documents"""
    
    fix_type = FixType.REFERENCE
    description = "Fix broken cross-references and links"
    
    LINK_PATTERN = re.compile(r'\[([^\]]+)\]\(([^)]+)\)')
    
    def detect(self, content: str, file_path: Path) -> List[Fix]:
        """Detect broken references"""
        fixes = []
        
        for match in self.LINK_PATTERN.finditer(content):
            text, link = match.groups()
            
            # Skip external links
            if link.startswith(('http://', 'https://', 'mailto:')):
                continue
            
            # Check if local file exists
            target_path = (file_path.parent / link).resolve()
            if not target_path.exists():
                # Try to find the file
                new_link = self._find_file(link, file_path)
                if new_link:
                    fixes.append(Fix(
                        file_path=file_path,
                        fix_type=self.fix_type,
                        severity=FixSeverity.WARNING,
                        description=f"Broken link: {link}",
                        old_content=f"[{text}]({link})",
                        new_content=f"[{text}]({new_link})",
                    ))
        
        return fixes
    
    def apply(self, fix: Fix) -> FixResult:
        """Apply reference fix"""
        try:
            content = fix.file_path.read_text()
            new_content = content.replace(fix.old_content, fix.new_content)
            fix.file_path.write_text(new_content)
            return FixResult(fix=fix, success=True)
        except Exception as e:
            return FixResult(fix=fix, success=False, error=str(e))
    
    def _find_file(self, broken_link: str, from_file: Path) -> Optional[str]:
        """Try to find the correct file path"""
        filename = Path(broken_link).name
        
        # Search in docs folder
        docs_root = self._find_docs_root(from_file)
        if not docs_root:
            return None
        
        for found in docs_root.rglob(filename):
            # Calculate relative path from source file
            try:
                relative = found.relative_to(from_file.parent)
                return str(relative)
            except ValueError:
                # Files in different trees, use absolute from docs root
                return f"/{found.relative_to(docs_root)}"
        
        return None
    
    def _find_docs_root(self, file_path: Path) -> Optional[Path]:
        """Find the docs root folder"""
        current = file_path.parent
        while current != current.parent:
            if current.name == "docs":
                return current
            current = current.parent
        return None


# backend/sdlcctl/migration/fixers/version_fixer.py

@FixerRegistry.register
class VersionFixer(BaseFixer):
    """Fix SDLC version mismatches"""
    
    fix_type = FixType.VERSION
    description = "Upgrade documents to target SDLC version"
    
    def detect(self, content: str, file_path: Path) -> List[Fix]:
        """Detect version mismatches"""
        fixes = []
        
        from ..header_parser import HeaderMetadataParser
        parser = HeaderMetadataParser()
        header = parser.parse(content)
        
        current_version = header.get("Version", header.get("SDLC Version"))
        target_version = self.config.sdlc_version
        
        if current_version and current_version != target_version:
            # Check if upgrade is needed
            if self._needs_upgrade(current_version, target_version):
                fixes.append(Fix(
                    file_path=file_path,
                    fix_type=self.fix_type,
                    severity=FixSeverity.WARNING,
                    description=f"Version mismatch: {current_version} → {target_version}",
                    old_content=current_version,
                    new_content=target_version,
                    metadata={"from_version": current_version, "to_version": target_version}
                ))
        
        return fixes
    
    def apply(self, fix: Fix) -> FixResult:
        """Apply version upgrade"""
        try:
            content = fix.file_path.read_text()
            
            # Update version in header
            new_content = content.replace(
                f"| **Version** | {fix.old_content} |",
                f"| **Version** | {fix.new_content} |"
            )
            
            # Also check for SDLC Version format
            new_content = new_content.replace(
                f"| **SDLC Version** | {fix.old_content} |",
                f"| **SDLC Version** | {fix.new_content} |"
            )
            
            fix.file_path.write_text(new_content)
            return FixResult(fix=fix, success=True)
        except Exception as e:
            return FixResult(fix=fix, success=False, error=str(e))
    
    def _needs_upgrade(self, current: str, target: str) -> bool:
        """Check if upgrade is needed"""
        try:
            current_parts = [int(x) for x in current.split('.')]
            target_parts = [int(x) for x in target.split('.')]
            return current_parts < target_parts
        except ValueError:
            return True
```

---

### Day 5: Backup System

**Task**: Build reliable backup with git integration

```python
# backend/sdlcctl/migration/backup.py

import subprocess
from dataclasses import dataclass
from pathlib import Path
from datetime import datetime
from typing import Optional, List
import json
import shutil

@dataclass
class BackupInfo:
    """Information about a backup"""
    backup_id: str
    branch_name: str
    created_at: datetime
    files_backed_up: int
    original_branch: str
    commit_hash: Optional[str] = None

class BackupManager:
    """
    Manage backups for migration operations
    
    Strategy:
    1. Create git branch for backup
    2. Commit current state
    3. Store rollback info in .sdlc/backups/
    """
    
    BACKUP_DIR = ".sdlc/backups"
    BRANCH_PREFIX = "sdlc-migration-backup"
    
    def __init__(self, repo_root: Path):
        self.repo_root = repo_root
        self.backup_dir = repo_root / self.BACKUP_DIR
        self.backup_dir.mkdir(parents=True, exist_ok=True)
    
    def create_backup(self, description: str = "") -> BackupInfo:
        """Create a new backup before migration"""
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        backup_id = f"backup-{timestamp}"
        branch_name = f"{self.BRANCH_PREFIX}-{timestamp}"
        
        # Get current branch
        original_branch = self._get_current_branch()
        
        # Create backup branch
        self._run_git(["checkout", "-b", branch_name])
        
        # Commit current state (if there are changes)
        status = self._run_git(["status", "--porcelain"])
        if status.strip():
            self._run_git(["add", "-A"])
            self._run_git(["commit", "-m", f"Backup before migration: {description}"])
        
        # Get commit hash
        commit_hash = self._run_git(["rev-parse", "HEAD"]).strip()
        
        # Return to original branch
        self._run_git(["checkout", original_branch])
        
        # Count files
        files_count = len(list(self.repo_root.rglob("*")))
        
        # Store backup info
        backup_info = BackupInfo(
            backup_id=backup_id,
            branch_name=branch_name,
            created_at=datetime.now(),
            files_backed_up=files_count,
            original_branch=original_branch,
            commit_hash=commit_hash
        )
        
        self._store_backup_info(backup_info)
        
        return backup_info
    
    def rollback(self, backup_id: str) -> bool:
        """Rollback to a previous backup"""
        backup_info = self._load_backup_info(backup_id)
        if not backup_info:
            raise ValueError(f"Backup not found: {backup_id}")
        
        # Stash current changes
        self._run_git(["stash", "push", "-m", "Pre-rollback stash"])
        
        # Checkout backup branch
        self._run_git(["checkout", backup_info.branch_name])
        
        # Create new branch from backup
        rollback_branch = f"rollback-from-{backup_id}"
        self._run_git(["checkout", "-b", rollback_branch])
        
        return True
    
    def list_backups(self) -> List[BackupInfo]:
        """List all available backups"""
        backups = []
        for backup_file in self.backup_dir.glob("backup-*.json"):
            info = self._load_backup_info(backup_file.stem)
            if info:
                backups.append(info)
        
        return sorted(backups, key=lambda x: x.created_at, reverse=True)
    
    def delete_backup(self, backup_id: str) -> bool:
        """Delete a backup (branch and metadata)"""
        backup_info = self._load_backup_info(backup_id)
        if not backup_info:
            return False
        
        # Delete git branch
        try:
            self._run_git(["branch", "-D", backup_info.branch_name])
        except subprocess.CalledProcessError:
            pass  # Branch might not exist
        
        # Delete metadata file
        metadata_file = self.backup_dir / f"{backup_id}.json"
        if metadata_file.exists():
            metadata_file.unlink()
        
        return True
    
    def _run_git(self, args: List[str]) -> str:
        """Run a git command"""
        result = subprocess.run(
            ["git"] + args,
            cwd=self.repo_root,
            capture_output=True,
            text=True,
            check=True
        )
        return result.stdout
    
    def _get_current_branch(self) -> str:
        """Get current git branch name"""
        return self._run_git(["branch", "--show-current"]).strip()
    
    def _store_backup_info(self, info: BackupInfo):
        """Store backup info to JSON file"""
        data = {
            "backup_id": info.backup_id,
            "branch_name": info.branch_name,
            "created_at": info.created_at.isoformat(),
            "files_backed_up": info.files_backed_up,
            "original_branch": info.original_branch,
            "commit_hash": info.commit_hash
        }
        
        file_path = self.backup_dir / f"{info.backup_id}.json"
        file_path.write_text(json.dumps(data, indent=2))
    
    def _load_backup_info(self, backup_id: str) -> Optional[BackupInfo]:
        """Load backup info from JSON file"""
        file_path = self.backup_dir / f"{backup_id}.json"
        if not file_path.exists():
            return None
        
        data = json.loads(file_path.read_text())
        return BackupInfo(
            backup_id=data["backup_id"],
            branch_name=data["branch_name"],
            created_at=datetime.fromisoformat(data["created_at"]),
            files_backed_up=data["files_backed_up"],
            original_branch=data["original_branch"],
            commit_hash=data.get("commit_hash")
        )


class AtomicCommitter:
    """
    Commit migration changes atomically
    
    Strategy:
    1. Batch all fixes
    2. Single commit with detailed message
    3. Rollback on failure
    """
    
    def __init__(self, repo_root: Path, backup_manager: BackupManager):
        self.repo_root = repo_root
        self.backup = backup_manager
    
    def commit_migration(
        self,
        fixes: List['FixResult'],
        migration_summary: str
    ) -> str:
        """Commit all migration fixes atomically"""
        
        # Build commit message
        commit_msg = self._build_commit_message(fixes, migration_summary)
        
        # Stage all modified files
        modified_files = [str(f.fix.file_path.relative_to(self.repo_root)) 
                         for f in fixes if f.success]
        
        if not modified_files:
            return "No files to commit"
        
        # Git add
        for file_path in modified_files:
            subprocess.run(
                ["git", "add", file_path],
                cwd=self.repo_root,
                check=True
            )
        
        # Git commit
        result = subprocess.run(
            ["git", "commit", "-m", commit_msg],
            cwd=self.repo_root,
            capture_output=True,
            text=True
        )
        
        if result.returncode != 0:
            raise RuntimeError(f"Git commit failed: {result.stderr}")
        
        # Get commit hash
        hash_result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=self.repo_root,
            capture_output=True,
            text=True
        )
        
        return hash_result.stdout.strip()
    
    def _build_commit_message(
        self,
        fixes: List['FixResult'],
        summary: str
    ) -> str:
        """Build detailed commit message"""
        successful = [f for f in fixes if f.success]
        failed = [f for f in fixes if not f.success]
        
        # Group by fix type
        by_type = {}
        for fix_result in successful:
            fix_type = fix_result.fix.fix_type.value
            if fix_type not in by_type:
                by_type[fix_type] = []
            by_type[fix_type].append(fix_result)
        
        lines = [
            f"chore(sdlc): {summary}",
            "",
            "SDLC Migration Applied:",
            "",
        ]
        
        for fix_type, type_fixes in by_type.items():
            lines.append(f"- {fix_type}: {len(type_fixes)} files")
        
        lines.extend([
            "",
            f"Total: {len(successful)} fixes applied",
        ])
        
        if failed:
            lines.extend([
                "",
                f"Failed: {len(failed)} fixes",
            ])
        
        return "\n".join(lines)
```

---

## Week 2: Executor & CLI (Apr 28 - May 2)

### Day 6-7: Migration Executor

**Task**: Orchestrate the full migration flow

```python
# backend/sdlcctl/migration/executor.py

from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Dict
from enum import Enum
import logging

from .scanner import ParallelScanner, ScanReport
from .config_generator import SDLCConfig
from .fixers.base import BaseFixer, FixerRegistry, Fix, FixResult, FixType
from .backup import BackupManager, AtomicCommitter

logger = logging.getLogger(__name__)

class MigrationMode(Enum):
    """Migration execution modes"""
    DRY_RUN = "dry-run"      # Show what would be done
    INTERACTIVE = "interactive"  # Ask before each fix
    AUTO = "auto"            # Apply all fixes automatically

@dataclass
class MigrationPlan:
    """Plan for migration fixes"""
    source_version: str
    target_version: str
    fixes: List[Fix]
    estimated_time_seconds: int
    files_affected: int
    
    def summary(self) -> str:
        """Generate human-readable summary"""
        by_type = {}
        for fix in self.fixes:
            key = fix.fix_type.value
            by_type[key] = by_type.get(key, 0) + 1
        
        lines = [
            f"Migration Plan: {self.source_version} → {self.target_version}",
            f"Files affected: {self.files_affected}",
            f"Total fixes: {len(self.fixes)}",
            "",
            "Fixes by type:"
        ]
        
        for fix_type, count in sorted(by_type.items()):
            lines.append(f"  - {fix_type}: {count}")
        
        lines.append(f"\nEstimated time: {self.estimated_time_seconds}s")
        
        return "\n".join(lines)

@dataclass
class MigrationResult:
    """Result of migration execution"""
    success: bool
    plan: MigrationPlan
    applied_fixes: List[FixResult]
    backup_info: Optional['BackupInfo']
    commit_hash: Optional[str]
    error: Optional[str] = None
    
    @property
    def success_count(self) -> int:
        return len([f for f in self.applied_fixes if f.success])
    
    @property
    def failure_count(self) -> int:
        return len([f for f in self.applied_fixes if not f.success])

class MigrationExecutor:
    """
    Execute SDLC migration with backup and rollback
    
    Flow:
    1. Scan repository
    2. Generate migration plan
    3. Create backup
    4. Apply fixes
    5. Commit changes
    """
    
    def __init__(
        self,
        repo_root: Path,
        config: SDLCConfig,
        mode: MigrationMode = MigrationMode.AUTO
    ):
        self.repo_root = repo_root
        self.config = config
        self.mode = mode
        
        self.docs_root = repo_root / config.docs_root
        self.scanner = ParallelScanner(self.docs_root)
        self.backup_manager = BackupManager(repo_root)
        self.committer = AtomicCommitter(repo_root, self.backup_manager)
    
    async def execute(self) -> MigrationResult:
        """Execute full migration"""
        
        # Step 1: Scan
        logger.info("Scanning repository...")
        scan_report = await self.scanner.scan()
        
        # Step 2: Generate plan
        logger.info("Generating migration plan...")
        plan = self._generate_plan(scan_report)
        
        if not plan.fixes:
            logger.info("No fixes needed!")
            return MigrationResult(
                success=True,
                plan=plan,
                applied_fixes=[],
                backup_info=None,
                commit_hash=None
            )
        
        # Dry run check
        if self.mode == MigrationMode.DRY_RUN:
            logger.info("Dry run mode - no changes applied")
            return MigrationResult(
                success=True,
                plan=plan,
                applied_fixes=[],
                backup_info=None,
                commit_hash=None
            )
        
        # Step 3: Create backup
        logger.info("Creating backup...")
        backup_info = self.backup_manager.create_backup(
            f"Migration to {self.config.sdlc_version}"
        )
        
        try:
            # Step 4: Apply fixes
            logger.info(f"Applying {len(plan.fixes)} fixes...")
            applied_fixes = self._apply_fixes(plan.fixes)
            
            # Step 5: Commit
            logger.info("Committing changes...")
            commit_hash = self.committer.commit_migration(
                applied_fixes,
                f"Migrate to SDLC {self.config.sdlc_version}"
            )
            
            return MigrationResult(
                success=True,
                plan=plan,
                applied_fixes=applied_fixes,
                backup_info=backup_info,
                commit_hash=commit_hash
            )
            
        except Exception as e:
            logger.error(f"Migration failed: {e}")
            logger.info("Rolling back...")
            self.backup_manager.rollback(backup_info.backup_id)
            
            return MigrationResult(
                success=False,
                plan=plan,
                applied_fixes=[],
                backup_info=backup_info,
                commit_hash=None,
                error=str(e)
            )
    
    def _generate_plan(self, scan_report: ScanReport) -> MigrationPlan:
        """Generate migration plan from scan results"""
        all_fixes = []
        
        # Get all fixers
        fixers = FixerRegistry.get_all_fixers(self.config)
        
        # Scan each file for fixes
        for file_path in self.docs_root.rglob("*.md"):
            content = file_path.read_text()
            
            for fixer in fixers:
                fixes = fixer.detect(content, file_path)
                all_fixes.extend(fixes)
        
        # Determine source version
        versions = scan_report.sdlc_versions_found
        source_version = max(versions.items(), key=lambda x: x[1])[0] if versions else "unknown"
        
        return MigrationPlan(
            source_version=source_version,
            target_version=self.config.sdlc_version,
            fixes=all_fixes,
            estimated_time_seconds=len(all_fixes) * 2,  # 2s per fix estimate
            files_affected=len(set(f.file_path for f in all_fixes))
        )
    
    def _apply_fixes(self, fixes: List[Fix]) -> List[FixResult]:
        """Apply all fixes"""
        results = []
        
        for fix in fixes:
            if self.mode == MigrationMode.INTERACTIVE:
                if not self._prompt_user(fix):
                    continue
            
            fixer = FixerRegistry.get_fixer(fix.fix_type, self.config)
            result = fixer.apply(fix)
            results.append(result)
            
            if result.success:
                logger.debug(f"Fixed: {fix.file_path}")
            else:
                logger.warning(f"Failed: {fix.file_path} - {result.error}")
        
        return results
    
    def _prompt_user(self, fix: Fix) -> bool:
        """Prompt user for confirmation (interactive mode)"""
        print(f"\n{fix.description}")
        print(f"File: {fix.file_path}")
        print(f"Change: {fix.old_content[:50]}... → {fix.new_content[:50]}...")
        
        response = input("Apply this fix? [y/N]: ")
        return response.lower() in ['y', 'yes']
```

---

### Day 8-9: CLI Commands

**Task**: Add `sdlcctl migrate` command

```python
# backend/sdlcctl/commands/migrate.py

import typer
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from pathlib import Path
import asyncio

from ..migration.executor import MigrationExecutor, MigrationMode, MigrationResult
from ..migration.config_generator import SDLCConfig
from ..migration.backup import BackupManager

app = typer.Typer()
console = Console()

@app.command()
def plan(
    path: Path = typer.Argument(Path(".")),
    config_file: Path = typer.Option(
        None,
        "--config", "-c",
        help="Path to .sdlc-config.json"
    ),
):
    """
    Generate migration plan without applying changes.
    
    Examples:
        sdlcctl migrate plan
        sdlcctl migrate plan --config .sdlc-config.json
    """
    config = _load_config(path, config_file)
    executor = MigrationExecutor(path, config, MigrationMode.DRY_RUN)
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console
    ) as progress:
        task = progress.add_task("Analyzing...", total=None)
        result = asyncio.run(executor.execute())
        progress.update(task, description="Analysis complete!")
    
    # Display plan
    console.print(Panel(result.plan.summary(), title="Migration Plan"))
    
    # Detailed fixes table
    if result.plan.fixes:
        fixes_table = Table(title="Proposed Fixes")
        fixes_table.add_column("File")
        fixes_table.add_column("Type")
        fixes_table.add_column("Description")
        fixes_table.add_column("Severity")
        
        for fix in result.plan.fixes[:20]:  # First 20
            fixes_table.add_row(
                str(fix.file_path.name),
                fix.fix_type.value,
                fix.description[:50],
                fix.severity.value
            )
        
        if len(result.plan.fixes) > 20:
            console.print(f"[dim]... and {len(result.plan.fixes) - 20} more fixes[/dim]")
        
        console.print(fixes_table)

@app.command()
def run(
    path: Path = typer.Argument(Path(".")),
    config_file: Path = typer.Option(
        None,
        "--config", "-c",
        help="Path to .sdlc-config.json"
    ),
    mode: str = typer.Option(
        "auto",
        "--mode", "-m",
        help="Execution mode: auto, interactive, dry-run"
    ),
    no_backup: bool = typer.Option(
        False,
        "--no-backup",
        help="Skip creating backup (dangerous!)"
    ),
):
    """
    Run SDLC migration on the repository.
    
    Examples:
        sdlcctl migrate run
        sdlcctl migrate run --mode interactive
        sdlcctl migrate run --mode dry-run
    """
    config = _load_config(path, config_file)
    
    # Parse mode
    exec_mode = {
        "auto": MigrationMode.AUTO,
        "interactive": MigrationMode.INTERACTIVE,
        "dry-run": MigrationMode.DRY_RUN,
    }.get(mode.lower(), MigrationMode.AUTO)
    
    # Warning for no-backup
    if no_backup and exec_mode != MigrationMode.DRY_RUN:
        console.print("[yellow]⚠️ Running without backup. Proceed with caution![/yellow]")
        if not typer.confirm("Continue?"):
            raise typer.Exit(0)
    
    executor = MigrationExecutor(path, config, exec_mode)
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console
    ) as progress:
        task = progress.add_task("Running migration...", total=None)
        result = asyncio.run(executor.execute())
        progress.update(task, description="Migration complete!")
    
    # Display results
    _display_result(result)

@app.command()
def rollback(
    path: Path = typer.Argument(Path(".")),
    backup_id: str = typer.Argument(
        ...,
        help="Backup ID to rollback to"
    ),
):
    """
    Rollback to a previous backup.
    
    Examples:
        sdlcctl migrate rollback backup-20260421-143000
    """
    backup_manager = BackupManager(path)
    
    console.print(f"[yellow]Rolling back to {backup_id}...[/yellow]")
    
    try:
        backup_manager.rollback(backup_id)
        console.print(f"[green]✅ Rollback successful[/green]")
    except ValueError as e:
        console.print(f"[red]❌ {e}[/red]")
        raise typer.Exit(1)

@app.command()
def backups(
    path: Path = typer.Argument(Path(".")),
):
    """
    List available backups.
    
    Examples:
        sdlcctl migrate backups
    """
    backup_manager = BackupManager(path)
    backup_list = backup_manager.list_backups()
    
    if not backup_list:
        console.print("[dim]No backups found[/dim]")
        return
    
    table = Table(title="Available Backups")
    table.add_column("Backup ID")
    table.add_column("Created")
    table.add_column("Branch")
    table.add_column("Files")
    
    for backup in backup_list:
        table.add_row(
            backup.backup_id,
            backup.created_at.strftime("%Y-%m-%d %H:%M"),
            backup.branch_name,
            str(backup.files_backed_up)
        )
    
    console.print(table)

def _load_config(path: Path, config_file: Optional[Path]) -> SDLCConfig:
    """Load SDLC config"""
    if config_file:
        config_path = config_file
    else:
        config_path = path / ".sdlc-config.json"
    
    if config_path.exists():
        import json
        data = json.loads(config_path.read_text())
        return SDLCConfig(
            sdlc_version=data.get("sdlc_version", "5.1.0"),
            project_name=data.get("project", {}).get("name", "Unknown"),
            tier=data.get("project", {}).get("tier", "STANDARD"),
            docs_root=data.get("structure", {}).get("docs_root", "docs"),
        )
    
    # Default config
    return SDLCConfig()

def _display_result(result: MigrationResult):
    """Display migration result"""
    if result.success:
        console.print("[green]✅ Migration completed successfully![/green]")
    else:
        console.print(f"[red]❌ Migration failed: {result.error}[/red]")
    
    # Summary table
    table = Table()
    table.add_column("Metric")
    table.add_column("Value")
    
    table.add_row("Fixes applied", str(result.success_count))
    table.add_row("Fixes failed", str(result.failure_count))
    
    if result.backup_info:
        table.add_row("Backup", result.backup_info.backup_id)
    
    if result.commit_hash:
        table.add_row("Commit", result.commit_hash[:8])
    
    console.print(table)
    
    # Rollback hint
    if result.backup_info:
        console.print(f"\n[dim]To rollback: sdlcctl migrate rollback {result.backup_info.backup_id}[/dim]")
```

---

### Day 10: Testing & Documentation

**Task**: Integration tests and user documentation

```python
# tests/integration/test_migration_executor.py

import pytest
import tempfile
from pathlib import Path
import asyncio

class TestMigrationExecutor:
    """Integration tests for migration executor"""
    
    @pytest.fixture
    def sample_repo(self, tmp_path):
        """Create sample repository with outdated SDLC docs"""
        # Initialize git repo
        subprocess.run(["git", "init"], cwd=tmp_path, check=True)
        subprocess.run(["git", "config", "user.email", "test@test.com"], cwd=tmp_path)
        subprocess.run(["git", "config", "user.name", "Test"], cwd=tmp_path)
        
        # Create docs structure
        docs = tmp_path / "docs"
        (docs / "00-foundation").mkdir(parents=True)
        
        # Create file with issues
        file1 = docs / "00-foundation" / "README.md"
        file1.write_text("""# Project Foundation

| Field | Value |
|-------|-------|
| **Version** | 4.5 |
| **Status** | Active |

Content here.
""")
        
        # Initial commit
        subprocess.run(["git", "add", "-A"], cwd=tmp_path)
        subprocess.run(["git", "commit", "-m", "Initial"], cwd=tmp_path)
        
        return tmp_path
    
    def test_dry_run_no_changes(self, sample_repo):
        """Dry run should not modify files"""
        config = SDLCConfig(sdlc_version="5.1.0")
        executor = MigrationExecutor(sample_repo, config, MigrationMode.DRY_RUN)
        
        result = asyncio.run(executor.execute())
        
        assert result.success
        assert result.plan.fixes  # Should have fixes
        assert len(result.applied_fixes) == 0  # But not applied
        assert result.backup_info is None
        assert result.commit_hash is None
    
    def test_auto_migration_creates_backup(self, sample_repo):
        """Auto migration should create backup"""
        config = SDLCConfig(sdlc_version="5.1.0")
        executor = MigrationExecutor(sample_repo, config, MigrationMode.AUTO)
        
        result = asyncio.run(executor.execute())
        
        assert result.success
        assert result.backup_info is not None
        assert result.backup_info.branch_name.startswith("sdlc-migration-backup")
    
    def test_rollback_restores_original(self, sample_repo):
        """Rollback should restore original state"""
        # Get original content
        file_path = sample_repo / "docs" / "00-foundation" / "README.md"
        original_content = file_path.read_text()
        
        # Run migration
        config = SDLCConfig(sdlc_version="5.1.0")
        executor = MigrationExecutor(sample_repo, config, MigrationMode.AUTO)
        result = asyncio.run(executor.execute())
        
        # Verify content changed
        assert file_path.read_text() != original_content
        
        # Rollback
        backup_manager = BackupManager(sample_repo)
        backup_manager.rollback(result.backup_info.backup_id)
        
        # Note: After rollback we're on a new branch from backup
        # Content should match original
    
    def test_migration_fixes_version(self, sample_repo):
        """Migration should fix version numbers"""
        config = SDLCConfig(sdlc_version="5.1.0")
        executor = MigrationExecutor(sample_repo, config, MigrationMode.AUTO)
        
        result = asyncio.run(executor.execute())
        
        assert result.success
        
        # Check version was updated
        file_path = sample_repo / "docs" / "00-foundation" / "README.md"
        content = file_path.read_text()
        assert "5.1.0" in content
        assert "4.5" not in content
```

---

## Deliverables

| # | Deliverable | Status |
|---|-------------|--------|
| 1 | Fixer framework (BaseFixer, Registry) | ⏳ |
| 2 | 8 core fixers (Header, Naming, Reference, Version) | ⏳ |
| 3 | BackupManager with git integration | ⏳ |
| 4 | AtomicCommitter | ⏳ |
| 5 | MigrationExecutor | ⏳ |
| 6 | `sdlcctl migrate` commands | ⏳ |
| 7 | Integration tests | ⏳ |

---

## Risk Mitigation

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Data loss during fix | Low | Critical | Backup before every migration |
| Git conflict after rollback | Medium | Medium | Create new branch for rollback |
| Performance on large repos | Medium | Low | Batch fixes, parallelize |

---

*Sprint planned: December 21, 2025*
*CTO Approval: Pending*
