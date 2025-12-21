# SPRINT-45: Auto-Fix Engine & Cross-Reference Updater
## EP-04: Universal AI Codex Structure Validation | Phase 2

---

**Document Information**

| Field | Value |
|-------|-------|
| **Sprint ID** | SPRINT-45 |
| **Epic** | EP-04: SDLC Structure Enforcement |
| **Duration** | 2 weeks (Mar 3-14, 2026) |
| **Status** | PLANNED |
| **Team** | 2 Backend + 1 Frontend + 1 QA |
| **Story Points** | 21 SP |
| **Budget** | $3,000 |
| **Framework** | SDLC 5.1.1 + SASE Level 2 |
| **Dependency** | Sprint 44 (Scanner Engine) |

---

## Sprint Goals

### Primary Objectives

| # | Objective | Priority | Owner |
|---|-----------|----------|-------|
| 1 | Build auto-fix engine for detected violations | P0 | Backend Lead |
| 2 | Implement cross-reference updater | P0 | Backend Dev 1 |
| 3 | Create git commit automation | P0 | Backend Dev 2 |
| 4 | Add dry-run preview mode | P1 | Backend Dev 1 |
| 5 | Integrate with `sdlcctl validate --auto-fix` | P0 | Backend Lead |

### Success Criteria

| Metric | Target | Measurement |
|--------|--------|-------------|
| Auto-fix success rate | ≥95% | Test on real violations |
| Cross-reference accuracy | 100% | Zero broken links |
| Git commit quality | Atomic commits | Code review |
| Time to fix (78 files) | <60 seconds | Benchmark |

---

## Week 1: Auto-Fix Engine (Mar 3-7)

### Day 1-2: Fix Engine Architecture

**Task**: Create fixers for each violation type

```python
# backend/sdlcctl/fixers/base_fixer.py

from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional
import shutil

@dataclass
class FixResult:
    """Result of applying a fix"""
    success: bool
    violation_rule_id: str
    original_path: Path
    new_path: Optional[Path] = None
    changes_made: List[str] = None
    error_message: Optional[str] = None

class BaseFixer(ABC):
    """Base class for auto-fixers"""
    
    @abstractmethod
    def can_fix(self, violation: ViolationReport) -> bool:
        """Check if this fixer can handle the violation"""
        pass
    
    @abstractmethod
    def fix(self, violation: ViolationReport, dry_run: bool = False) -> FixResult:
        """Apply the fix"""
        pass
    
    def _safe_rename(self, src: Path, dst: Path, dry_run: bool) -> bool:
        """Safely rename file/folder with backup"""
        if dry_run:
            return True
        
        # Create backup
        backup_path = src.with_suffix(src.suffix + ".bak")
        if src.is_dir():
            shutil.copytree(src, backup_path)
        else:
            shutil.copy2(src, backup_path)
        
        try:
            shutil.move(str(src), str(dst))
            # Remove backup on success
            if backup_path.exists():
                if backup_path.is_dir():
                    shutil.rmtree(backup_path)
                else:
                    backup_path.unlink()
            return True
        except Exception as e:
            # Restore from backup
            if backup_path.exists():
                shutil.move(str(backup_path), str(src))
            raise e
```

```python
# backend/sdlcctl/fixers/numbering_fixer.py

class NumberingFixer(BaseFixer):
    """
    Fix duplicate numbering violations
    
    Strategy:
    1. Detect all folders with same number in stage
    2. Suggest renumbering based on:
       - Alphabetical order of remaining name
       - Existing content/ADRs (keep lower for important)
    3. Apply renumbering
    """
    
    def can_fix(self, violation: ViolationReport) -> bool:
        return violation.rule_id == "NUM-001"
    
    def fix(self, violation: ViolationReport, dry_run: bool = False) -> FixResult:
        stage_folder = violation.file_path.parent
        
        # Get all numbered folders in stage
        numbered_folders = []
        for folder in stage_folder.iterdir():
            if folder.is_dir():
                match = re.match(r"^(\d{2})-(.+)$", folder.name)
                if match:
                    numbered_folders.append({
                        "path": folder,
                        "num": match.group(1),
                        "name": match.group(2)
                    })
        
        # Find duplicates
        duplicates = {}
        for f in numbered_folders:
            if f["num"] not in duplicates:
                duplicates[f["num"]] = []
            duplicates[f["num"]].append(f)
        
        # Renumber duplicates
        changes = []
        used_numbers = set(f["num"] for f in numbered_folders)
        
        for num, folders in duplicates.items():
            if len(folders) <= 1:
                continue
            
            # Sort by name alphabetically
            folders.sort(key=lambda x: x["name"])
            
            # Keep first, renumber rest
            for i, folder in enumerate(folders[1:], start=1):
                # Find next available number
                new_num = int(num) + i
                while f"{new_num:02d}" in used_numbers:
                    new_num += 1
                
                new_name = f"{new_num:02d}-{folder['name']}"
                new_path = folder["path"].parent / new_name
                
                if not dry_run:
                    self._safe_rename(folder["path"], new_path, dry_run)
                
                changes.append(f"{folder['path'].name} → {new_name}")
                used_numbers.add(f"{new_num:02d}")
        
        return FixResult(
            success=True,
            violation_rule_id=violation.rule_id,
            original_path=violation.file_path,
            changes_made=changes
        )
```

---

### Day 3-4: Consolidation Fixer

**Task**: Consolidate fragmented folders (e.g., multiple ADRs folders)

```python
# backend/sdlcctl/fixers/consolidation_fixer.py

class ConsolidationFixer(BaseFixer):
    """
    Consolidate fragmented folders
    
    Problem:
    docs/02-design/
    ├── 01-ADRs/        (5 files)
    ├── 03-ADRs/        (10 files)  ← Should consolidate
    └── 05-ADRs/        (3 files)   ← Should consolidate
    
    Solution:
    docs/02-design/
    └── 01-ADRs/        (18 files)  ← All consolidated
    """
    
    CONSOLIDATABLE_PATTERNS = [
        r"^\d{2}-ADRs?$",
        r"^\d{2}-Templates?$",
        r"^\d{2}-Archives?$",
    ]
    
    def can_fix(self, violation: ViolationReport) -> bool:
        return violation.rule_id == "FRAG-001"
    
    def fix(self, violation: ViolationReport, dry_run: bool = False) -> FixResult:
        stage_folder = violation.file_path.parent
        
        # Find all ADR folders
        adr_folders = []
        for folder in stage_folder.iterdir():
            if folder.is_dir() and re.match(r"^\d{2}-ADRs?$", folder.name):
                adr_folders.append(folder)
        
        if len(adr_folders) <= 1:
            return FixResult(
                success=True,
                violation_rule_id=violation.rule_id,
                original_path=violation.file_path,
                changes_made=["No consolidation needed"]
            )
        
        # Sort by number, first one is target
        adr_folders.sort(key=lambda x: x.name)
        target_folder = adr_folders[0]
        
        changes = []
        for source_folder in adr_folders[1:]:
            # Move all files to target
            for item in source_folder.iterdir():
                dest = target_folder / item.name
                
                # Handle conflicts
                if dest.exists():
                    base = item.stem
                    ext = item.suffix
                    counter = 1
                    while dest.exists():
                        dest = target_folder / f"{base}-{counter}{ext}"
                        counter += 1
                
                if not dry_run:
                    shutil.move(str(item), str(dest))
                
                changes.append(f"{source_folder.name}/{item.name} → {target_folder.name}/{dest.name}")
            
            # Remove empty source folder
            if not dry_run and not any(source_folder.iterdir()):
                source_folder.rmdir()
                changes.append(f"Removed empty: {source_folder.name}")
        
        return FixResult(
            success=True,
            violation_rule_id=violation.rule_id,
            original_path=violation.file_path,
            new_path=target_folder,
            changes_made=changes
        )
```

---

### Day 5: Cross-Reference Updater

**Task**: Update markdown links when files/folders move

```python
# backend/sdlcctl/fixers/cross_reference_updater.py

import re
from pathlib import Path
from typing import Dict, List, Tuple

class CrossReferenceUpdater:
    """
    Update cross-references in markdown files after restructure
    
    Handles:
    - [Link text](../old/path.md) → [Link text](../new/path.md)
    - [Link text](../../02-design/01-ADRs/ADR-001.md)
    - Relative and absolute paths
    """
    
    def __init__(self, docs_root: Path):
        self.docs_root = docs_root
        self.link_pattern = re.compile(
            r'\[([^\]]+)\]\(([^)]+\.md)\)',
            re.MULTILINE
        )
    
    def update_references(
        self, 
        path_changes: Dict[Path, Path],
        dry_run: bool = False
    ) -> List[Tuple[Path, int, str]]:
        """
        Update all cross-references based on path changes
        
        Args:
            path_changes: {old_path: new_path} mapping
            dry_run: Preview changes without applying
            
        Returns:
            List of (file, line_count, change_description)
        """
        updates = []
        
        # Build reverse lookup: old_path → new_path
        old_to_new = {str(old): str(new) for old, new in path_changes.items()}
        
        # Scan all markdown files
        for md_file in self.docs_root.rglob("*.md"):
            content = md_file.read_text(encoding="utf-8")
            original_content = content
            
            # Find all links
            for match in self.link_pattern.finditer(content):
                link_text = match.group(1)
                link_path = match.group(2)
                
                # Resolve to absolute path
                if link_path.startswith("../") or link_path.startswith("./"):
                    abs_path = (md_file.parent / link_path).resolve()
                else:
                    abs_path = (self.docs_root / link_path).resolve()
                
                # Check if this path was moved
                abs_path_str = str(abs_path)
                for old_path, new_path in old_to_new.items():
                    if abs_path_str.endswith(old_path) or old_path in abs_path_str:
                        # Calculate new relative path
                        new_abs = Path(abs_path_str.replace(old_path, new_path))
                        new_relative = self._relative_path(md_file, new_abs)
                        
                        # Replace in content
                        old_link = f"[{link_text}]({link_path})"
                        new_link = f"[{link_text}]({new_relative})"
                        content = content.replace(old_link, new_link)
                        
                        updates.append((
                            md_file,
                            1,
                            f"{old_link} → {new_link}"
                        ))
            
            # Write updated content
            if content != original_content and not dry_run:
                md_file.write_text(content, encoding="utf-8")
        
        return updates
    
    def _relative_path(self, from_file: Path, to_file: Path) -> str:
        """Calculate relative path between two files"""
        try:
            return str(to_file.relative_to(from_file.parent))
        except ValueError:
            # Different subtrees, use ../
            common = Path(*[p for p in from_file.parts if p in to_file.parts])
            up_count = len(from_file.relative_to(common).parts) - 1
            down_path = to_file.relative_to(common)
            return "../" * up_count + str(down_path)
```

---

## Week 2: Git Integration & CLI (Mar 10-14)

### Day 6-7: Git Commit Automation

**Task**: Create atomic git commits for each fix

```python
# backend/sdlcctl/fixers/git_committer.py

import subprocess
from pathlib import Path
from typing import List, Optional
from dataclasses import dataclass

@dataclass  
class GitCommitResult:
    success: bool
    commit_hash: Optional[str]
    message: str
    files_changed: int

class GitCommitter:
    """
    Create atomic git commits for SDLC structure fixes
    
    Commit message format:
    refactor(sdlc): Auto-fix {rule_id} violations
    
    - {change_1}
    - {change_2}
    
    Generated by: sdlcctl validate --auto-fix
    """
    
    def __init__(self, repo_root: Path):
        self.repo_root = repo_root
    
    def commit_fixes(
        self,
        fix_results: List[FixResult],
        dry_run: bool = False
    ) -> GitCommitResult:
        """Create a single commit for all fixes"""
        
        if not fix_results:
            return GitCommitResult(
                success=True,
                commit_hash=None,
                message="No changes to commit",
                files_changed=0
            )
        
        # Group by rule for commit message
        by_rule = {}
        for fix in fix_results:
            if fix.rule_id not in by_rule:
                by_rule[fix.rule_id] = []
            by_rule[fix.rule_id].extend(fix.changes_made or [])
        
        # Build commit message
        rules = ", ".join(by_rule.keys())
        message_lines = [
            f"refactor(sdlc): Auto-fix {rules} violations",
            "",
        ]
        
        for rule_id, changes in by_rule.items():
            message_lines.append(f"## {rule_id}")
            for change in changes[:10]:  # Limit to 10 per rule
                message_lines.append(f"- {change}")
            if len(changes) > 10:
                message_lines.append(f"- ... and {len(changes) - 10} more")
            message_lines.append("")
        
        message_lines.extend([
            "---",
            "Generated by: sdlcctl validate --auto-fix",
        ])
        
        commit_message = "\n".join(message_lines)
        
        if dry_run:
            return GitCommitResult(
                success=True,
                commit_hash="(dry-run)",
                message=commit_message,
                files_changed=len(fix_results)
            )
        
        # Stage all changes
        subprocess.run(
            ["git", "add", "-A"],
            cwd=self.repo_root,
            check=True
        )
        
        # Create commit
        result = subprocess.run(
            ["git", "commit", "-m", commit_message],
            cwd=self.repo_root,
            capture_output=True,
            text=True
        )
        
        if result.returncode != 0:
            return GitCommitResult(
                success=False,
                commit_hash=None,
                message=result.stderr,
                files_changed=0
            )
        
        # Get commit hash
        hash_result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=self.repo_root,
            capture_output=True,
            text=True
        )
        
        return GitCommitResult(
            success=True,
            commit_hash=hash_result.stdout.strip()[:7],
            message=commit_message,
            files_changed=len(fix_results)
        )
```

---

### Day 8-9: CLI Auto-Fix Integration

**Task**: Add `--auto-fix` and `--dry-run` to validate command

```python
# backend/sdlcctl/commands/validate.py (updated)

@app.command()
def validate(
    path: Path = typer.Argument(Path(".")),
    auto_fix: bool = typer.Option(
        False,
        "--auto-fix", "-a",
        help="Automatically fix detected violations"
    ),
    dry_run: bool = typer.Option(
        False,
        "--dry-run", "-d",
        help="Preview fixes without applying"
    ),
    config: Path = typer.Option(None, "--config", "-c"),
    output_format: str = typer.Option("table", "--format", "-f"),
):
    """
    Validate and optionally fix SDLC structure violations.
    
    Examples:
        # Scan only
        sdlcctl validate
        
        # Preview fixes
        sdlcctl validate --auto-fix --dry-run
        
        # Apply fixes
        sdlcctl validate --auto-fix
    """
    docs_path = _find_docs_folder(path)
    
    # Run scanner
    console.print(f"[cyan]🔍 Scanning {docs_path}...[/cyan]")
    scanner = SDLCStructureScanner(docs_path, config)
    violations = scanner.scan()
    
    # Display violations
    _print_table(violations)
    
    if not violations:
        console.print("[green]✅ No violations found![/green]")
        return
    
    # Auto-fix mode
    if auto_fix:
        fixable = [v for v in violations if v.auto_fixable]
        
        if not fixable:
            console.print("[yellow]⚠️ No auto-fixable violations[/yellow]")
            return
        
        console.print(f"\n[cyan]🔧 Fixing {len(fixable)} violations...[/cyan]")
        
        if dry_run:
            console.print("[yellow]DRY RUN - No changes will be made[/yellow]")
        
        # Apply fixes
        fix_engine = AutoFixEngine(docs_path)
        fix_results = fix_engine.fix_all(fixable, dry_run=dry_run)
        
        # Update cross-references
        console.print("[cyan]🔗 Updating cross-references...[/cyan]")
        xref_updater = CrossReferenceUpdater(docs_path)
        path_changes = {r.original_path: r.new_path for r in fix_results if r.new_path}
        xref_updates = xref_updater.update_references(path_changes, dry_run=dry_run)
        
        console.print(f"  Updated {len(xref_updates)} cross-references")
        
        # Git commit
        if not dry_run:
            console.print("[cyan]📝 Creating git commit...[/cyan]")
            committer = GitCommitter(docs_path.parent)
            commit_result = committer.commit_fixes(fix_results)
            
            if commit_result.success:
                console.print(f"[green]✅ Committed: {commit_result.commit_hash}[/green]")
            else:
                console.print(f"[red]❌ Commit failed: {commit_result.message}[/red]")
        
        # Summary
        success = sum(1 for r in fix_results if r.success)
        console.print(f"\n[bold]Fixed:[/bold] {success}/{len(fixable)} violations")
    
    else:
        # Hint to use auto-fix
        fixable_count = sum(1 for v in violations if v.auto_fixable)
        if fixable_count > 0:
            console.print(
                f"\n[cyan]💡 {fixable_count} violations are auto-fixable. "
                f"Run 'sdlcctl validate --auto-fix' to fix.[/cyan]"
            )
```

---

### Day 10: Testing & Edge Cases

**Task**: Comprehensive test suite for fixers

```python
# tests/integration/test_auto_fix.py

import pytest
from pathlib import Path
import tempfile
import shutil

class TestAutoFix:
    """Integration tests for auto-fix engine"""
    
    @pytest.fixture
    def duplicate_structure(self, tmp_path):
        """Create test structure with duplicate numbering"""
        docs = tmp_path / "docs" / "02-design"
        docs.mkdir(parents=True)
        
        (docs / "01-ADRs").mkdir()
        (docs / "01-System-Architecture").mkdir()  # Duplicate!
        (docs / "03-ADRs").mkdir()  # Duplicate!
        (docs / "03-API-Design").mkdir()  # Duplicate!
        
        # Add some files
        (docs / "01-ADRs" / "ADR-001.md").write_text("# ADR 001")
        (docs / "01-System-Architecture" / "README.md").write_text("# System")
        
        return tmp_path
    
    def test_fix_duplicate_numbering(self, duplicate_structure):
        """Duplicates are renumbered sequentially"""
        scanner = SDLCStructureScanner(duplicate_structure / "docs")
        violations = scanner.scan()
        
        assert any(v.rule_id == "NUM-001" for v in violations)
        
        # Apply fix
        engine = AutoFixEngine(duplicate_structure / "docs")
        results = engine.fix_all(violations, dry_run=False)
        
        # Verify no more duplicates
        violations_after = scanner.scan()
        assert not any(v.rule_id == "NUM-001" for v in violations_after)
    
    def test_cross_references_updated(self, duplicate_structure):
        """Cross-references are updated after rename"""
        # Add file with cross-reference
        docs = duplicate_structure / "docs"
        readme = docs / "README.md"
        readme.write_text(
            "See [ADRs](02-design/01-ADRs/ADR-001.md) for decisions."
        )
        
        # Apply fix (will renumber 01-System-Architecture to 02-System-Architecture)
        scanner = SDLCStructureScanner(docs)
        violations = scanner.scan()
        
        engine = AutoFixEngine(docs)
        results = engine.fix_all(violations, dry_run=False)
        
        # Update cross-references
        xref = CrossReferenceUpdater(docs)
        path_changes = {r.original_path: r.new_path for r in results if r.new_path}
        xref.update_references(path_changes)
        
        # Verify link still works
        new_content = readme.read_text()
        assert "01-ADRs/ADR-001.md" in new_content  # ADRs folder unchanged
```

---

## Deliverables

| # | Deliverable | Status |
|---|-------------|--------|
| 1 | `BaseFixer` class | ⏳ |
| 2 | `NumberingFixer` | ⏳ |
| 3 | `ConsolidationFixer` | ⏳ |
| 4 | `CrossReferenceUpdater` | ⏳ |
| 5 | `GitCommitter` | ⏳ |
| 6 | `--auto-fix` CLI option | ⏳ |
| 7 | `--dry-run` preview mode | ⏳ |
| 8 | Integration tests (15) | ⏳ |

---

## Dependencies

| Dependency | Status | Notes |
|------------|--------|-------|
| Sprint 44 Scanner | ⏳ Must complete | Blocker |
| Git (subprocess) | ✅ System | - |
| shutil | ✅ stdlib | File operations |

---

## Risk Mitigation

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Data loss on rename | Low | Critical | Backup before rename |
| Broken cross-refs | Medium | High | Comprehensive link detection |
| Git conflicts | Low | Medium | Warn if uncommitted changes |

---

*Sprint planned: December 21, 2025*
*CTO Approval: Pending*
