"""
SDLC 5.0.0 Folder Scanner.

Scans project directory structure and identifies SDLC stages.
Optimized for performance: <10s for 1000+ files.
"""

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Set
import re

from .tier import STAGE_NAMES


@dataclass
class StageInfo:
    """Information about a discovered SDLC stage."""

    stage_id: str
    folder_name: str
    path: Path
    file_count: int
    has_readme: bool
    subfolders: List[str] = field(default_factory=list)
    depth: int = 1


@dataclass
class ScanResult:
    """Result of scanning a project for SDLC structure."""

    project_root: Path
    docs_root: Path
    stages_found: Dict[str, StageInfo]
    stages_missing: List[str]
    naming_violations: List[Dict[str, str]]
    legacy_folders: List[Path]
    total_files: int
    total_folders: int
    scan_time_ms: float


class FolderScanner:
    """
    Scanner for SDLC 5.0.0 folder structure.

    Identifies:
    - SDLC stages (00-10)
    - Naming violations
    - Legacy folders (99-Legacy)
    - P0 artifact locations
    """

    # Patterns to ignore during scanning
    IGNORE_PATTERNS = {
        "node_modules",
        ".git",
        ".venv",
        "venv",
        "__pycache__",
        ".pytest_cache",
        "dist",
        "build",
        ".next",
        ".nuxt",
        "coverage",
        ".nyc_output",
        ".DS_Store",
    }

    # Legacy folder pattern
    LEGACY_PATTERN = re.compile(r"^99-Legacy$", re.IGNORECASE)

    # Stage pattern (e.g., 00-Project-Foundation)
    STAGE_PATTERN = re.compile(r"^(\d{2})-(.+)$")

    def __init__(
        self,
        project_root: Path,
        docs_root: str = "docs",
        ignore_patterns: Optional[Set[str]] = None,
    ):
        """
        Initialize scanner.

        Args:
            project_root: Root directory of the project
            docs_root: Relative path to docs folder (default: "docs")
            ignore_patterns: Additional patterns to ignore
        """
        self.project_root = Path(project_root).resolve()
        self.docs_root = self.project_root / docs_root
        self.ignore_patterns = self.IGNORE_PATTERNS.copy()
        if ignore_patterns:
            self.ignore_patterns.update(ignore_patterns)

    def scan(self) -> ScanResult:
        """
        Scan the project for SDLC structure.

        Returns:
            ScanResult with discovered stages and violations
        """
        import time

        start_time = time.time()

        stages_found: Dict[str, StageInfo] = {}
        naming_violations: List[Dict[str, str]] = []
        legacy_folders: List[Path] = []
        total_files = 0
        total_folders = 0

        if not self.docs_root.exists():
            return ScanResult(
                project_root=self.project_root,
                docs_root=self.docs_root,
                stages_found={},
                stages_missing=list(STAGE_NAMES.keys()),
                naming_violations=[{"type": "missing_docs", "message": f"docs folder not found at {self.docs_root}"}],
                legacy_folders=[],
                total_files=0,
                total_folders=0,
                scan_time_ms=(time.time() - start_time) * 1000,
            )

        # Scan docs folder for stages
        for item in self.docs_root.iterdir():
            if not item.is_dir():
                continue

            folder_name = item.name

            # Skip ignored patterns
            if folder_name in self.ignore_patterns:
                continue

            total_folders += 1

            # Check for legacy folder
            if self.LEGACY_PATTERN.match(folder_name):
                legacy_folders.append(item)
                continue

            # Check for stage pattern
            match = self.STAGE_PATTERN.match(folder_name)
            if match:
                stage_id = match.group(1)
                stage_suffix = match.group(2)

                # Validate stage naming
                expected_name = STAGE_NAMES.get(stage_id)
                if expected_name and folder_name != expected_name:
                    naming_violations.append({
                        "type": "stage_naming",
                        "stage_id": stage_id,
                        "found": folder_name,
                        "expected": expected_name,
                        "path": str(item),
                    })

                # Scan stage contents
                stage_info = self._scan_stage(item, stage_id)
                stages_found[stage_id] = stage_info
                total_files += stage_info.file_count

        # Identify missing stages
        stages_missing = [
            stage_id
            for stage_id in STAGE_NAMES.keys()
            if stage_id not in stages_found
        ]

        scan_time_ms = (time.time() - start_time) * 1000

        return ScanResult(
            project_root=self.project_root,
            docs_root=self.docs_root,
            stages_found=stages_found,
            stages_missing=stages_missing,
            naming_violations=naming_violations,
            legacy_folders=legacy_folders,
            total_files=total_files,
            total_folders=total_folders,
            scan_time_ms=scan_time_ms,
        )

    def _scan_stage(self, stage_path: Path, stage_id: str) -> StageInfo:
        """
        Scan a single stage folder.

        Args:
            stage_path: Path to the stage folder
            stage_id: Stage ID (e.g., "00", "01")

        Returns:
            StageInfo with stage details
        """
        file_count = 0
        subfolders = []
        has_readme = False
        max_depth = 1

        for root, dirs, files in os.walk(stage_path):
            # Skip ignored directories
            dirs[:] = [d for d in dirs if d not in self.ignore_patterns]

            # Skip legacy folders
            dirs[:] = [d for d in dirs if not self.LEGACY_PATTERN.match(d)]

            # Calculate depth
            rel_path = Path(root).relative_to(stage_path)
            depth = len(rel_path.parts) + 1
            max_depth = max(max_depth, depth)

            # Count files
            for f in files:
                if f.startswith("."):
                    continue
                file_count += 1
                if f.lower() == "readme.md" and root == str(stage_path):
                    has_readme = True

            # Track immediate subfolders
            if root == str(stage_path):
                subfolders = [d for d in dirs]

        return StageInfo(
            stage_id=stage_id,
            folder_name=stage_path.name,
            path=stage_path,
            file_count=file_count,
            has_readme=has_readme,
            subfolders=subfolders,
            depth=max_depth,
        )

    def find_file(self, filename: str, search_root: Optional[Path] = None) -> Optional[Path]:
        """
        Find a file in the project.

        Args:
            filename: Name of file to find
            search_root: Root to search from (default: project_root)

        Returns:
            Path to file if found, None otherwise
        """
        root = search_root or self.project_root

        for item in root.rglob(filename):
            if item.is_file():
                # Skip ignored directories
                if any(p in item.parts for p in self.ignore_patterns):
                    continue
                return item

        return None

    def file_exists(self, relative_path: str) -> bool:
        """
        Check if a file exists relative to project root.

        Args:
            relative_path: Path relative to project root

        Returns:
            True if file exists
        """
        full_path = self.project_root / relative_path
        return full_path.exists() and full_path.is_file()

    def get_stage_path(self, stage_id: str) -> Optional[Path]:
        """
        Get the path to a stage folder.

        Args:
            stage_id: Stage ID (e.g., "00", "01")

        Returns:
            Path to stage folder if exists, None otherwise
        """
        expected_name = STAGE_NAMES.get(stage_id)
        if not expected_name:
            return None

        stage_path = self.docs_root / expected_name
        if stage_path.exists():
            return stage_path

        # Check for any folder starting with the stage ID
        for item in self.docs_root.iterdir():
            if item.is_dir() and item.name.startswith(f"{stage_id}-"):
                return item

        return None
