"""
=========================================================================
Cross-Reference Validation Service
SDLC Orchestrator - Sprint 155 Day 3 (Track 2: Cross-Reference Validation)

Version: 1.0.0
Date: February 4, 2026
Status: ACTIVE - Sprint 155 Implementation
Authority: Backend Lead + CTO Approved
Framework: SDLC 6.0.5

Purpose:
- Validate cross-references between documents (ADR ↔ Spec ↔ Test)
- Detect broken links in documentation
- Detect circular dependencies in document graph
- Find orphaned documents without proper links
- Build reference graphs for visualization

Architecture: ADR-050 Spec Converter Visual Editor
=========================================================================
"""

from __future__ import annotations

import logging
import os
import re
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple
from uuid import UUID

logger = logging.getLogger(__name__)


# =========================================================================
# Enums
# =========================================================================


class LinkType(str, Enum):
    """Type of cross-reference link."""

    ADR_REF = "adr_ref"  # Reference to ADR document
    SPEC_REF = "spec_ref"  # Reference to Technical Spec
    TEST_REF = "test_ref"  # Reference to test file
    CODE_REF = "code_ref"  # Reference to source code
    DOC_REF = "doc_ref"  # Reference to other documentation
    EXTERNAL_REF = "external_ref"  # Reference to external URL


class ViolationType(str, Enum):
    """Type of cross-reference violation."""

    BROKEN_LINK = "broken_link"
    MISSING_BACKLINK = "missing_backlink"
    CIRCULAR_DEPENDENCY = "circular_dependency"
    ORPHANED_DOCUMENT = "orphaned_document"
    INVALID_REFERENCE_FORMAT = "invalid_reference_format"


# =========================================================================
# Data Classes
# =========================================================================


@dataclass
class ExtractedLink:
    """Represents a link extracted from a document."""

    source_file: str
    target_file: str
    link_type: LinkType
    line_number: int = 0
    raw_link: str = ""


@dataclass
class CrossReferenceViolation:
    """Represents a cross-reference violation."""

    violation_type: str
    source_file: str
    target_file: str = ""
    message: str = ""
    severity: str = "warning"  # "error", "warning", "info"
    suggestion: str = ""

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "violation_type": self.violation_type,
            "source_file": self.source_file,
            "target_file": self.target_file,
            "message": self.message,
            "severity": self.severity,
            "suggestion": self.suggestion,
        }


@dataclass
class LinkValidationResult:
    """Result of validating a single link."""

    is_valid: bool
    violation: Optional[CrossReferenceViolation] = None


@dataclass
class ValidationResult:
    """Result of cross-reference validation."""

    is_valid: bool
    violations: List[CrossReferenceViolation] = field(default_factory=list)
    scanned_files: int = 0
    total_links: int = 0
    duration_ms: int = 0
    validated_at: datetime = field(default_factory=datetime.utcnow)
    project_id: Optional[UUID] = None

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        result = {
            "is_valid": self.is_valid,
            "violations": [v.to_dict() for v in self.violations],
            "scanned_files": self.scanned_files,
            "total_links": self.total_links,
            "duration_ms": self.duration_ms,
            "validated_at": self.validated_at.isoformat(),
        }
        if self.project_id:
            result["project_id"] = str(self.project_id)
        return result


@dataclass
class DocumentLinks:
    """Links for a specific document."""

    document_path: str
    incoming: List[dict] = field(default_factory=list)
    outgoing: List[dict] = field(default_factory=list)


# =========================================================================
# Service
# =========================================================================


class CrossReferenceService:
    """
    Service for validating cross-references between documents.

    Validates:
    - ADR ↔ Spec bidirectional links
    - Spec ↔ Test Case references
    - Broken link detection
    - Circular dependency detection
    - Orphaned document alerts

    Usage:
        service = CrossReferenceService()
        result = await service.validate_project(project_id, "/path/to/project")
    """

    # Regex patterns for link extraction
    MARKDOWN_LINK_PATTERN = re.compile(r"\[([^\]]+)\]\(([^)]+)\)")
    INLINE_CODE_LINK_PATTERN = re.compile(r"`([^`]+\.(py|ts|tsx|js|jsx|md))`")
    ADR_PATTERN = re.compile(r"ADR-\d{3}", re.IGNORECASE)
    SPEC_PATTERN = re.compile(r"SPEC-\d{4}", re.IGNORECASE)

    def __init__(self):
        """Initialize the cross-reference service."""
        self._file_cache: Dict[str, bool] = {}

    # =========================================================================
    # Link Extraction
    # =========================================================================

    async def extract_links(
        self,
        content: str,
        source_file: str,
    ) -> List[ExtractedLink]:
        """
        Extract all cross-reference links from document content.

        Args:
            content: Document content
            source_file: Path to source file

        Returns:
            List of extracted links
        """
        links: List[ExtractedLink] = []
        lines = content.split("\n")

        for line_num, line in enumerate(lines, 1):
            # Extract markdown links [text](path)
            for match in self.MARKDOWN_LINK_PATTERN.finditer(line):
                link_text, link_path = match.groups()
                link_type = self._classify_link(link_path, link_text)

                if link_type:
                    resolved_path = self._resolve_relative_path(source_file, link_path)
                    links.append(
                        ExtractedLink(
                            source_file=source_file,
                            target_file=resolved_path,
                            link_type=link_type,
                            line_number=line_num,
                            raw_link=link_path,
                        )
                    )

            # Extract inline code references `path/to/file.py`
            for match in self.INLINE_CODE_LINK_PATTERN.finditer(line):
                code_path = match.group(1)
                link_type = self._classify_link(code_path, code_path)

                if link_type:
                    links.append(
                        ExtractedLink(
                            source_file=source_file,
                            target_file=code_path,
                            link_type=link_type,
                            line_number=line_num,
                            raw_link=code_path,
                        )
                    )

        return links

    def _classify_link(
        self,
        link_path: str,
        link_text: str,
    ) -> Optional[LinkType]:
        """Classify the type of a link based on path and text."""
        lower_path = link_path.lower()
        lower_text = link_text.lower()

        # ADR reference
        if "adr" in lower_path or self.ADR_PATTERN.search(link_text):
            return LinkType.ADR_REF

        # Spec reference
        if "spec" in lower_path or self.SPEC_PATTERN.search(link_text):
            return LinkType.SPEC_REF

        # Test reference
        if "test" in lower_path or lower_path.startswith("tests/"):
            return LinkType.TEST_REF

        # Code reference (source files)
        if lower_path.endswith((".py", ".ts", ".tsx", ".js", ".jsx")):
            if "test" not in lower_path:
                return LinkType.CODE_REF

        # Documentation reference
        if lower_path.endswith(".md"):
            return LinkType.DOC_REF

        # External reference
        if lower_path.startswith(("http://", "https://", "www.")):
            return LinkType.EXTERNAL_REF

        return None

    def _resolve_relative_path(
        self,
        source_file: str,
        relative_path: str,
    ) -> str:
        """Resolve a relative path to absolute path."""
        if relative_path.startswith(("http://", "https://", "/")):
            return relative_path

        source_dir = os.path.dirname(source_file)
        resolved = os.path.normpath(os.path.join(source_dir, relative_path))
        return resolved

    # =========================================================================
    # Link Validation
    # =========================================================================

    async def validate_link(
        self,
        project_id: UUID,
        source_file: str,
        target_file: str,
        link_type: LinkType,
        project_path: str = "",
    ) -> LinkValidationResult:
        """
        Validate a single cross-reference link.

        Args:
            project_id: Project UUID
            source_file: Source file path
            target_file: Target file path
            link_type: Type of link
            project_path: Base project path

        Returns:
            LinkValidationResult indicating if link is valid
        """
        # Skip external links
        if link_type == LinkType.EXTERNAL_REF:
            return LinkValidationResult(is_valid=True)

        # Check if target file exists
        full_target = (
            os.path.join(project_path, target_file)
            if project_path
            else target_file
        )

        if not await self._file_exists(full_target):
            return LinkValidationResult(
                is_valid=False,
                violation=CrossReferenceViolation(
                    violation_type=ViolationType.BROKEN_LINK.value,
                    source_file=source_file,
                    target_file=target_file,
                    message=f"Target file does not exist: {target_file}",
                    severity="error",
                    suggestion=f"Create the missing file or update the reference in {source_file}",
                ),
            )

        return LinkValidationResult(is_valid=True)

    async def _file_exists(self, file_path: str) -> bool:
        """Check if a file exists (with caching)."""
        if file_path in self._file_cache:
            return self._file_cache[file_path]

        exists = os.path.isfile(file_path)
        self._file_cache[file_path] = exists
        return exists

    # =========================================================================
    # Bidirectional Link Validation
    # =========================================================================

    async def validate_bidirectional_links(
        self,
        project_id: UUID,
        forward_links: Dict[str, List[str]],
        back_links: Dict[str, List[str]],
    ) -> List[CrossReferenceViolation]:
        """
        Validate bidirectional links (ADR ↔ Spec).

        Args:
            project_id: Project UUID
            forward_links: Map of source → targets (e.g., ADR → Specs)
            back_links: Map of target → sources (e.g., Spec → ADRs)

        Returns:
            List of violations for missing backlinks
        """
        violations: List[CrossReferenceViolation] = []

        for source, targets in forward_links.items():
            for target in targets:
                # Check if target has backlink to source
                target_backlinks = back_links.get(target, [])

                if source not in target_backlinks:
                    violations.append(
                        CrossReferenceViolation(
                            violation_type=ViolationType.MISSING_BACKLINK.value,
                            source_file=source,
                            target_file=target,
                            message=f"{target} does not reference back to {source}",
                            severity="warning",
                            suggestion=f"Add a reference to {source} in {target}",
                        )
                    )

        return violations

    # =========================================================================
    # Circular Dependency Detection
    # =========================================================================

    async def detect_circular_dependencies(
        self,
        project_id: UUID,
        dependencies: Dict[str, List[str]],
    ) -> List[CrossReferenceViolation]:
        """
        Detect circular dependencies using DFS-based cycle detection.

        Args:
            project_id: Project UUID
            dependencies: Map of file → files it depends on

        Returns:
            List of violations for circular dependencies
        """
        violations: List[CrossReferenceViolation] = []
        visited: Set[str] = set()
        rec_stack: Set[str] = set()
        cycles_found: Set[frozenset] = set()

        def dfs(node: str, path: List[str]) -> Optional[List[str]]:
            """DFS to detect cycles. Returns cycle path if found."""
            visited.add(node)
            rec_stack.add(node)
            path.append(node)

            for neighbor in dependencies.get(node, []):
                if neighbor not in visited:
                    cycle = dfs(neighbor, path)
                    if cycle:
                        return cycle
                elif neighbor in rec_stack:
                    # Found cycle - extract it
                    cycle_start = path.index(neighbor)
                    return path[cycle_start:] + [neighbor]

            path.pop()
            rec_stack.remove(node)
            return None

        # Check each node
        for node in dependencies:
            if node not in visited:
                cycle = dfs(node, [])
                if cycle:
                    # Normalize cycle to avoid duplicates
                    cycle_set = frozenset(cycle[:-1])
                    if cycle_set not in cycles_found:
                        cycles_found.add(cycle_set)
                        cycle_str = " → ".join(cycle)
                        violations.append(
                            CrossReferenceViolation(
                                violation_type=ViolationType.CIRCULAR_DEPENDENCY.value,
                                source_file=cycle[0],
                                target_file=cycle[-1],
                                message=f"Circular dependency detected: {cycle_str}",
                                severity="error",
                                suggestion="Break the cycle by removing or restructuring one of the dependencies",
                            )
                        )

        return violations

    # =========================================================================
    # Orphaned Document Detection
    # =========================================================================

    async def detect_orphaned_documents(
        self,
        project_id: UUID,
        all_documents: List[str],
        linked_documents: List[str],
        doc_type: str = "document",
    ) -> List[CrossReferenceViolation]:
        """
        Detect orphaned documents that have no references.

        Args:
            project_id: Project UUID
            all_documents: All documents of a type
            linked_documents: Documents that have at least one reference
            doc_type: Type of document (for messages)

        Returns:
            List of violations for orphaned documents
        """
        violations: List[CrossReferenceViolation] = []
        linked_set = set(linked_documents)

        for doc in all_documents:
            if doc not in linked_set:
                violations.append(
                    CrossReferenceViolation(
                        violation_type=ViolationType.ORPHANED_DOCUMENT.value,
                        source_file=doc,
                        target_file="",
                        message=f"Orphaned {doc_type}: {doc} has no references",
                        severity="warning",
                        suggestion=f"Add references to this {doc_type} from related documents or consider if it should be removed",
                    )
                )

        return violations

    async def get_orphaned_documents(
        self,
        project_id: UUID,
        project_path: str = "",
        document_type: Optional[str] = None,
    ) -> List[dict]:
        """
        Get list of orphaned documents in a project.

        Args:
            project_id: Project UUID
            project_path: Base project path
            document_type: Optional filter by document type (ADR, SPEC, etc.)

        Returns:
            List of orphaned document info dicts
        """
        orphaned: List[dict] = []

        try:
            # Scan project files
            files = await self._scan_project_files(project_path or ".")

            # Extract all links to build reference map
            all_links = await self._extract_all_links(files, project_path or ".")

            # Build set of referenced documents
            referenced: Set[str] = set()
            for link in all_links:
                referenced.add(link.target_file)
                referenced.add(link.source_file)

            # Check each document type
            type_map = {
                "ADR": files.get("adrs", []),
                "SPEC": files.get("specs", []),
                "DOC": files.get("docs", []),
            }

            for doc_type, doc_list in type_map.items():
                if document_type and doc_type != document_type.upper():
                    continue

                for doc_path in doc_list:
                    # Check if document has any references
                    has_incoming = any(
                        self._paths_match(link.target_file, doc_path)
                        for link in all_links
                    )
                    has_outgoing = any(
                        self._paths_match(link.source_file, doc_path)
                        for link in all_links
                    )

                    if not has_incoming and not has_outgoing:
                        orphaned.append({
                            "document_path": doc_path,
                            "document_type": doc_type,
                            "reason": f"No incoming or outgoing references",
                        })

        except Exception as e:
            logger.warning(f"Error getting orphaned documents: {e}")

        return orphaned

    # =========================================================================
    # Full Project Validation
    # =========================================================================

    async def validate_document(
        self,
        project_id: UUID,
        document_path: str,
        project_path: str = "",
    ) -> ValidationResult:
        """
        Validate cross-references for a single document.

        Args:
            project_id: Project UUID
            document_path: Path to document
            project_path: Base project path

        Returns:
            ValidationResult with violations for this document
        """
        import time

        start_time = time.time()
        violations: List[CrossReferenceViolation] = []
        total_links = 0

        try:
            full_path = (
                os.path.join(project_path, document_path)
                if project_path
                else document_path
            )

            if not os.path.isfile(full_path):
                return ValidationResult(
                    is_valid=False,
                    violations=[
                        CrossReferenceViolation(
                            violation_type=ViolationType.BROKEN_LINK.value,
                            source_file=document_path,
                            message=f"Document not found: {document_path}",
                            severity="error",
                        )
                    ],
                    scanned_files=0,
                    total_links=0,
                    project_id=project_id,
                )

            # Read and extract links
            with open(full_path, "r", encoding="utf-8") as f:
                content = f.read()

            links = await self.extract_links(content, document_path)
            total_links = len(links)

            # Validate each link
            for link in links:
                result = await self.validate_link(
                    project_id=project_id,
                    source_file=link.source_file,
                    target_file=link.target_file,
                    link_type=link.link_type,
                    project_path=project_path,
                )
                if not result.is_valid and result.violation:
                    violations.append(result.violation)

            duration_ms = int((time.time() - start_time) * 1000)

            return ValidationResult(
                is_valid=len(violations) == 0,
                violations=violations,
                scanned_files=1,
                total_links=total_links,
                duration_ms=duration_ms,
                project_id=project_id,
            )

        except Exception as e:
            logger.error(
                f"Document validation failed: {e}",
                exc_info=True,
                extra={"project_id": str(project_id), "document": document_path},
            )
            raise

    async def validate_project(
        self,
        project_id: UUID,
        project_path: str,
    ) -> ValidationResult:
        """
        Validate all cross-references in a project.

        Args:
            project_id: Project UUID
            project_path: Path to project root

        Returns:
            ValidationResult with all violations
        """
        import time

        start_time = time.time()
        violations: List[CrossReferenceViolation] = []
        total_links = 0
        scanned_files = 0

        try:
            # Scan project files
            files = await self._scan_project_files(project_path)
            for file_list in files.values():
                scanned_files += len(file_list)

            # Run all validations
            violations, total_links = await self._run_all_validations(
                project_id=project_id,
                project_path=project_path,
            )

            duration_ms = int((time.time() - start_time) * 1000)

            return ValidationResult(
                is_valid=len(violations) == 0,
                violations=violations,
                scanned_files=scanned_files,
                total_links=total_links,
                duration_ms=duration_ms,
                project_id=project_id,
            )

        except Exception as e:
            logger.error(
                f"Project validation failed: {e}",
                exc_info=True,
                extra={"project_id": str(project_id)},
            )
            raise

    async def _run_all_validations(
        self,
        project_id: UUID,
        project_path: str,
    ) -> Tuple[List[CrossReferenceViolation], int]:
        """Run all validation checks on a project."""
        violations: List[CrossReferenceViolation] = []

        # Scan project files
        files = await self._scan_project_files(project_path)

        # Extract all links
        all_links = await self._extract_all_links(files, project_path)
        total_links = len(all_links)

        # Validate each link
        for link in all_links:
            result = await self.validate_link(
                project_id=project_id,
                source_file=link.source_file,
                target_file=link.target_file,
                link_type=link.link_type,
                project_path=project_path,
            )
            if not result.is_valid and result.violation:
                violations.append(result.violation)

        # Build dependency graph for circular detection
        dependencies: Dict[str, List[str]] = {}
        for link in all_links:
            if link.source_file not in dependencies:
                dependencies[link.source_file] = []
            dependencies[link.source_file].append(link.target_file)

        # Detect circular dependencies
        circular = await self.detect_circular_dependencies(project_id, dependencies)
        violations.extend(circular)

        return violations, total_links

    async def _scan_project_files(
        self,
        project_path: str,
    ) -> Dict[str, List[str]]:
        """Scan project for documentation files."""
        files = {
            "adrs": [],
            "specs": [],
            "tests": [],
            "docs": [],
        }

        try:
            for root, dirs, filenames in os.walk(project_path):
                # Skip hidden and cache directories
                dirs[:] = [d for d in dirs if not d.startswith((".", "__"))]

                for filename in filenames:
                    if not filename.endswith(".md"):
                        continue

                    full_path = os.path.join(root, filename)
                    rel_path = os.path.relpath(full_path, project_path)

                    if "ADR" in filename.upper():
                        files["adrs"].append(rel_path)
                    elif "SPEC" in filename.upper():
                        files["specs"].append(rel_path)
                    else:
                        files["docs"].append(rel_path)

            # Scan for test files
            test_dirs = ["tests", "test", "__tests__"]
            for test_dir in test_dirs:
                test_path = os.path.join(project_path, test_dir)
                if os.path.isdir(test_path):
                    for root, dirs, filenames in os.walk(test_path):
                        dirs[:] = [d for d in dirs if not d.startswith((".", "__pycache__"))]
                        for filename in filenames:
                            if filename.startswith("test_") or filename.endswith("_test.py"):
                                full_path = os.path.join(root, filename)
                                rel_path = os.path.relpath(full_path, project_path)
                                files["tests"].append(rel_path)

        except Exception as e:
            logger.warning(f"Error scanning project files: {e}")

        return files

    async def _extract_all_links(
        self,
        files: Dict[str, List[str]],
        project_path: str,
    ) -> List[ExtractedLink]:
        """Extract links from all markdown files."""
        links: List[ExtractedLink] = []

        for doc_type, file_list in files.items():
            if doc_type == "tests":
                continue  # Skip test files for link extraction

            for file_path in file_list:
                try:
                    full_path = os.path.join(project_path, file_path)
                    with open(full_path, "r", encoding="utf-8") as f:
                        content = f.read()

                    file_links = await self.extract_links(content, file_path)
                    links.extend(file_links)

                except Exception as e:
                    logger.warning(f"Error extracting links from {file_path}: {e}")

        return links

    # =========================================================================
    # Get Document Links
    # =========================================================================

    async def get_document_links(
        self,
        project_id: UUID,
        document_path: str,
        direction: str = "both",
        project_path: str = "",
    ) -> DocumentLinks:
        """
        Get all links for a specific document.

        Args:
            project_id: Project UUID
            document_path: Path to document
            direction: "incoming", "outgoing", or "both"
            project_path: Base project path

        Returns:
            DocumentLinks with incoming and outgoing links
        """
        result = DocumentLinks(document_path=document_path)

        if direction in ("outgoing", "both"):
            result.outgoing = await self._find_outgoing_links(
                project_id, document_path, project_path
            )

        if direction in ("incoming", "both"):
            result.incoming = await self._find_incoming_links(
                project_id, document_path, project_path
            )

        return result

    async def _find_outgoing_links(
        self,
        project_id: UUID,
        document_path: str,
        project_path: str,
    ) -> List[dict]:
        """Find all outgoing links from a document."""
        outgoing: List[dict] = []

        try:
            full_path = (
                os.path.join(project_path, document_path)
                if project_path
                else document_path
            )

            if os.path.isfile(full_path):
                with open(full_path, "r", encoding="utf-8") as f:
                    content = f.read()

                links = await self.extract_links(content, document_path)
                for link in links:
                    outgoing.append({
                        "target": link.target_file,
                        "type": link.link_type.value,
                        "line": link.line_number,
                    })

        except Exception as e:
            logger.warning(f"Error finding outgoing links: {e}")

        return outgoing

    async def _find_incoming_links(
        self,
        project_id: UUID,
        document_path: str,
        project_path: str,
    ) -> List[dict]:
        """Find all incoming links to a document."""
        incoming: List[dict] = []

        try:
            # Scan all markdown files for links pointing to this document
            files = await self._scan_project_files(project_path or ".")

            for doc_type, file_list in files.items():
                if doc_type == "tests":
                    continue

                for file_path in file_list:
                    if file_path == document_path:
                        continue

                    full_path = (
                        os.path.join(project_path, file_path)
                        if project_path
                        else file_path
                    )

                    if os.path.isfile(full_path):
                        with open(full_path, "r", encoding="utf-8") as f:
                            content = f.read()

                        links = await self.extract_links(content, file_path)
                        for link in links:
                            # Check if link points to our document
                            if self._paths_match(link.target_file, document_path):
                                incoming.append({
                                    "source": file_path,
                                    "type": link.link_type.value,
                                    "line": link.line_number,
                                })

        except Exception as e:
            logger.warning(f"Error finding incoming links: {e}")

        return incoming

    def _paths_match(self, path1: str, path2: str) -> bool:
        """Check if two paths refer to the same file."""
        norm1 = os.path.normpath(path1)
        norm2 = os.path.normpath(path2)
        return norm1 == norm2 or norm1.endswith(norm2) or norm2.endswith(norm1)


# =========================================================================
# Factory Function
# =========================================================================


def get_cross_reference_service() -> CrossReferenceService:
    """
    Factory function to create CrossReferenceService.

    Returns:
        CrossReferenceService instance
    """
    return CrossReferenceService()
