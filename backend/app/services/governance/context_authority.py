"""
=========================================================================
Context Authority Engine V1 - Metadata & Linkage Validation
SDLC Orchestrator - Sprint 109 (Vibecoding Index & Stage-Aware Gating)

Version: 1.0.0
Date: January 27, 2026
Status: ACTIVE - Sprint 109 Day 5
Authority: CTO + Backend Lead Approved
Framework: SDLC 5.3.0 Quality Assurance System

Purpose:
- Validate code has proper context linkage (ADRs, specs, AGENTS.md)
- V1: Metadata validation only, NOT semantic understanding
- Rule: "Orphan Code = Rejected Code"

Core Checks:
1. ADR Linkage: Module → ADR reference
2. Design Doc Reference: New feature → spec file
3. AGENTS.md Freshness: Context file age < 7 days
4. Module Annotation Consistency: Header ↔ directory

Zero Mock Policy: Real validation with actual file checks
=========================================================================
"""

import logging
import os
import re
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Set
from uuid import UUID

logger = logging.getLogger(__name__)


# ============================================================================
# Enums
# ============================================================================


class ContextViolationType(Enum):
    """Types of context violations."""

    ORPHAN_CODE = "orphan_code"
    NO_ADR_LINKAGE = "no_adr_linkage"
    NO_DESIGN_DOC = "no_design_doc"
    STALE_CONTEXT = "stale_context"
    MODULE_MISMATCH = "module_mismatch"
    DEPRECATED_ADR = "deprecated_adr"
    EMPTY_SPEC = "empty_spec"


class ViolationSeverity(Enum):
    """Severity levels for violations."""

    ERROR = "error"  # Blocks submission
    WARNING = "warning"  # Non-blocking, logged
    INFO = "info"  # Informational only


class ADRStatus(Enum):
    """Status of an ADR document."""

    PROPOSED = "proposed"
    ACCEPTED = "accepted"
    DEPRECATED = "deprecated"
    SUPERSEDED = "superseded"


# ============================================================================
# Data Classes
# ============================================================================


@dataclass
class ADR:
    """Architecture Decision Record metadata."""

    id: str  # e.g., "ADR-042"
    title: str
    status: ADRStatus
    file_path: str
    content: str
    created_at: Optional[datetime] = None
    deprecated_at: Optional[datetime] = None
    superseded_by: Optional[str] = None
    modules: List[str] = field(default_factory=list)  # Affected modules
    tags: List[str] = field(default_factory=list)


@dataclass
class DesignSpec:
    """Design specification document metadata."""

    task_id: str  # e.g., "TASK-123"
    file_path: str
    exists: bool
    is_empty: bool = False
    word_count: int = 0
    last_modified: Optional[datetime] = None


@dataclass
class AgentsMdInfo:
    """AGENTS.md file information."""

    file_path: str
    exists: bool
    last_modified: Optional[datetime] = None
    age_days: int = 0
    line_count: int = 0
    is_stale: bool = False  # >7 days


@dataclass
class ModuleAnnotation:
    """Module annotation extracted from file header."""

    file_path: str
    declared_module: Optional[str]
    inferred_module: str
    matches: bool
    owner: Optional[str] = None
    adr_references: List[str] = field(default_factory=list)


@dataclass
class ContextViolation:
    """A context validation violation."""

    type: ContextViolationType
    severity: ViolationSeverity
    message: str
    file_path: Optional[str] = None
    module: Optional[str] = None
    fix: Optional[str] = None
    cli_command: Optional[str] = None
    related_adr: Optional[str] = None


@dataclass
class ContextValidationResult:
    """Result of context validation."""

    valid: bool
    violations: List[ContextViolation] = field(default_factory=list)
    warnings: List[ContextViolation] = field(default_factory=list)
    info: List[ContextViolation] = field(default_factory=list)
    adr_count: int = 0
    linked_adrs: List[str] = field(default_factory=list)
    spec_found: bool = False
    agents_md_fresh: bool = True
    module_consistency: bool = True
    validated_at: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API response."""
        return {
            "valid": self.valid,
            "violations": [
                {
                    "type": v.type.value,
                    "severity": v.severity.value,
                    "message": v.message,
                    "file_path": v.file_path,
                    "module": v.module,
                    "fix": v.fix,
                    "cli_command": v.cli_command,
                    "related_adr": v.related_adr,
                }
                for v in self.violations
            ],
            "warnings": [
                {
                    "type": w.type.value,
                    "severity": w.severity.value,
                    "message": w.message,
                    "file_path": w.file_path,
                    "module": w.module,
                    "fix": w.fix,
                    "cli_command": w.cli_command,
                }
                for w in self.warnings
            ],
            "adr_count": self.adr_count,
            "linked_adrs": self.linked_adrs,
            "spec_found": self.spec_found,
            "agents_md_fresh": self.agents_md_fresh,
            "module_consistency": self.module_consistency,
            "validated_at": self.validated_at.isoformat(),
        }


@dataclass
class CodeSubmission:
    """Code submission for context validation."""

    submission_id: UUID
    project_id: UUID
    changed_files: List[str]
    affected_modules: List[str] = field(default_factory=list)
    task_id: Optional[str] = None
    is_new_feature: bool = False
    repo_path: Optional[str] = None


# ============================================================================
# Context Authority Engine V1
# ============================================================================


class ContextAuthorityEngineV1:
    """
    Context Authority Engine - V1: Metadata & Linkage Validation Only.

    This engine validates that code has proper context linkage:
    - ADR references in module headers
    - Design documents for new features
    - Fresh AGENTS.md context files
    - Consistent module annotations

    V1 Scope (Metadata Only):
    - Checks file existence, not semantic content
    - Pattern matching for @adr, @owner, @module annotations
    - Simple text search in ADR content

    NOT in V1 Scope:
    - Semantic understanding of code/ADR relationships
    - Deep content analysis
    - AI-powered validation

    Philosophy: "Orphan Code = Rejected Code"
    """

    # Patterns for extracting annotations from file headers
    ADR_PATTERN = re.compile(r"@adr[:\s]+([A-Z]+-\d+)", re.IGNORECASE)
    MODULE_PATTERN = re.compile(r"@module[:\s]+([a-z_][a-z0-9_./]*)", re.IGNORECASE)
    OWNER_PATTERN = re.compile(r"@owner[:\s]+@?([a-z_][a-z0-9_-]*)", re.IGNORECASE)

    # ADR status patterns
    STATUS_PATTERNS = {
        ADRStatus.PROPOSED: re.compile(r"status[:\s]*(proposed|draft)", re.IGNORECASE),
        ADRStatus.ACCEPTED: re.compile(r"status[:\s]*(accepted|approved)", re.IGNORECASE),
        ADRStatus.DEPRECATED: re.compile(r"status[:\s]*(deprecated)", re.IGNORECASE),
        ADRStatus.SUPERSEDED: re.compile(r"status[:\s]*(superseded)", re.IGNORECASE),
    }

    # Default paths
    DEFAULT_ADR_PATH = "docs/02-design/03-ADRs"
    DEFAULT_SPEC_PATH = "docs/02-design/specs"
    DEFAULT_AGENTS_MD = "AGENTS.md"

    # Staleness threshold
    AGENTS_MD_STALENESS_DAYS = 7

    def __init__(
        self,
        adr_path: str = DEFAULT_ADR_PATH,
        spec_path: str = DEFAULT_SPEC_PATH,
        agents_md_path: str = DEFAULT_AGENTS_MD,
        staleness_days: int = AGENTS_MD_STALENESS_DAYS,
    ):
        """
        Initialize Context Authority Engine V1.

        Args:
            adr_path: Path to ADR documents (relative to repo root)
            spec_path: Path to design spec documents
            agents_md_path: Path to AGENTS.md
            staleness_days: Days after which AGENTS.md is considered stale
        """
        self.adr_path = adr_path
        self.spec_path = spec_path
        self.agents_md_path = agents_md_path
        self.staleness_days = staleness_days
        self._adr_cache: Dict[str, ADR] = {}
        self._initialized = False

        logger.info(
            f"ContextAuthorityEngineV1 initialized: "
            f"ADR path={adr_path}, spec path={spec_path}"
        )

    async def initialize(self, repo_path: str) -> None:
        """
        Initialize engine with repository context.

        Args:
            repo_path: Path to repository root
        """
        self._repo_path = repo_path
        await self._load_adrs(repo_path)
        self._initialized = True

    async def validate_context(
        self,
        submission: CodeSubmission,
    ) -> ContextValidationResult:
        """
        Validate code submission has proper context linkage.

        Performs 4 checks:
        1. ADR Linkage: Module references at least one ADR
        2. Design Doc Reference: New features have spec files
        3. AGENTS.md Freshness: Context file updated within 7 days
        4. Module Annotation Consistency: Header matches directory

        Args:
            submission: Code submission to validate

        Returns:
            ContextValidationResult with violations and warnings
        """
        repo_path = submission.repo_path or self._get_default_repo_path()
        violations: List[ContextViolation] = []
        warnings: List[ContextViolation] = []
        info: List[ContextViolation] = []
        linked_adrs: Set[str] = set()

        # Load ADRs if not cached
        if not self._adr_cache:
            await self._load_adrs(repo_path)

        # CHECK 1: ADR Linkage
        adr_violations, adr_refs = await self._check_adr_linkage(
            submission.affected_modules,
            submission.changed_files,
            repo_path,
        )
        for v in adr_violations:
            if v.severity == ViolationSeverity.ERROR:
                violations.append(v)
            elif v.severity == ViolationSeverity.WARNING:
                warnings.append(v)
        linked_adrs.update(adr_refs)

        # CHECK 2: Design Doc Reference (for new features)
        if submission.is_new_feature and submission.task_id:
            design_violations = await self._check_design_doc_reference(
                submission.task_id,
                repo_path,
            )
            for v in design_violations:
                if v.severity == ViolationSeverity.ERROR:
                    violations.append(v)
                elif v.severity == ViolationSeverity.WARNING:
                    warnings.append(v)

        # CHECK 3: AGENTS.md Freshness
        freshness_result = await self._check_agents_md_freshness(repo_path)
        for v in freshness_result:
            if v.severity == ViolationSeverity.WARNING:
                warnings.append(v)
            elif v.severity == ViolationSeverity.INFO:
                info.append(v)

        # CHECK 4: Module Annotation Consistency
        consistency_violations = await self._check_module_annotation_consistency(
            submission.changed_files,
            repo_path,
        )
        for v in consistency_violations:
            if v.severity == ViolationSeverity.ERROR:
                violations.append(v)
            elif v.severity == ViolationSeverity.WARNING:
                warnings.append(v)

        # Determine validity (no ERROR severity violations)
        is_valid = len(violations) == 0

        result = ContextValidationResult(
            valid=is_valid,
            violations=violations,
            warnings=warnings,
            info=info,
            adr_count=len(self._adr_cache),
            linked_adrs=list(linked_adrs),
            spec_found=not any(
                v.type == ContextViolationType.NO_DESIGN_DOC for v in violations
            ),
            agents_md_fresh=not any(
                v.type == ContextViolationType.STALE_CONTEXT for v in warnings
            ),
            module_consistency=not any(
                v.type == ContextViolationType.MODULE_MISMATCH for v in violations
            ),
        )

        logger.info(
            f"Context validation: {'PASS' if is_valid else 'FAIL'} - "
            f"{len(violations)} violations, {len(warnings)} warnings"
        )

        return result

    async def _check_adr_linkage(
        self,
        modules: List[str],
        changed_files: List[str],
        repo_path: str,
    ) -> tuple[List[ContextViolation], Set[str]]:
        """
        Check if modules reference at least one ADR.

        Algorithm:
        1. For each module, search for @adr annotation in files
        2. If no annotation, search ADRs that mention the module
        3. Verify linked ADRs are not DEPRECATED

        Args:
            modules: List of affected modules
            changed_files: List of changed file paths
            repo_path: Repository root path

        Returns:
            Tuple of (violations, linked_adr_ids)
        """
        violations: List[ContextViolation] = []
        linked_adrs: Set[str] = set()

        for module in modules:
            # Try to find ADR references in module files
            module_adrs = await self._find_adrs_for_module(module, changed_files, repo_path)

            if not module_adrs:
                # No ADR linked to this module
                violations.append(
                    ContextViolation(
                        type=ContextViolationType.NO_ADR_LINKAGE,
                        severity=ViolationSeverity.ERROR,
                        message=f"Module '{module}' has no linked ADR",
                        module=module,
                        fix=(
                            f"Add to module header: @adr ADR-XXX\n"
                            f"Or create new ADR: sdlcctl adr create --module {module}"
                        ),
                        cli_command=f"sdlcctl adr create --module {module}",
                    )
                )
            else:
                # Check if any linked ADR is deprecated
                for adr_id in module_adrs:
                    if adr_id in self._adr_cache:
                        adr = self._adr_cache[adr_id]
                        if adr.status == ADRStatus.DEPRECATED:
                            violations.append(
                                ContextViolation(
                                    type=ContextViolationType.DEPRECATED_ADR,
                                    severity=ViolationSeverity.WARNING,
                                    message=(
                                        f"Module '{module}' links to deprecated {adr_id}"
                                    ),
                                    module=module,
                                    related_adr=adr_id,
                                    fix=f"Update to current ADR or create new decision record",
                                )
                            )
                        else:
                            linked_adrs.add(adr_id)

        return violations, linked_adrs

    async def _find_adrs_for_module(
        self,
        module: str,
        changed_files: List[str],
        repo_path: str,
    ) -> List[str]:
        """
        Find ADRs that reference a module.

        Search order:
        1. @adr annotations in module files
        2. ADR content mentioning module name
        3. ADR metadata listing module in 'affects' field

        Args:
            module: Module name
            changed_files: Changed file paths
            repo_path: Repository root path

        Returns:
            List of ADR IDs linked to this module
        """
        linked_adrs: List[str] = []

        # Search for @adr annotations in changed files
        for file_path in changed_files:
            if self._is_module_file(file_path, module):
                annotation = await self._extract_adr_annotation(file_path, repo_path)
                if annotation:
                    linked_adrs.extend(annotation)

        # Search ADR content for module mentions
        module_lower = module.lower()
        for adr_id, adr in self._adr_cache.items():
            # Check if module mentioned in ADR content
            if module_lower in adr.content.lower():
                if adr_id not in linked_adrs:
                    linked_adrs.append(adr_id)

            # Check if module listed in ADR metadata
            if module in adr.modules or module_lower in [m.lower() for m in adr.modules]:
                if adr_id not in linked_adrs:
                    linked_adrs.append(adr_id)

        return linked_adrs

    async def _check_design_doc_reference(
        self,
        task_id: str,
        repo_path: str,
    ) -> List[ContextViolation]:
        """
        Check if new feature has a design document.

        Args:
            task_id: Task ID (e.g., "TASK-123")
            repo_path: Repository root path

        Returns:
            List of violations
        """
        violations: List[ContextViolation] = []

        # Look for spec file: docs/02-design/specs/TASK-{id}-spec.md
        spec_patterns = [
            f"{task_id}-spec.md",
            f"{task_id.lower()}-spec.md",
            f"{task_id.replace('-', '_')}-spec.md",
        ]

        spec_dir = Path(repo_path) / self.spec_path
        spec_found = False
        spec_empty = False

        if spec_dir.exists():
            for pattern in spec_patterns:
                spec_file = spec_dir / pattern
                if spec_file.exists():
                    spec_found = True
                    # Check if empty
                    content = spec_file.read_text()
                    if len(content.strip()) < 100:  # Less than 100 chars = effectively empty
                        spec_empty = True
                    break

        if not spec_found:
            violations.append(
                ContextViolation(
                    type=ContextViolationType.NO_DESIGN_DOC,
                    severity=ViolationSeverity.ERROR,
                    message=f"New feature {task_id} has no design document",
                    fix=(
                        f"Create: {self.spec_path}/{task_id}-spec.md\n"
                        f"Or run: sdlcctl spec create --task {task_id}"
                    ),
                    cli_command=f"sdlcctl spec create --task {task_id}",
                )
            )
        elif spec_empty:
            violations.append(
                ContextViolation(
                    type=ContextViolationType.EMPTY_SPEC,
                    severity=ViolationSeverity.WARNING,
                    message=f"Design document for {task_id} is effectively empty",
                    fix="Add meaningful content to the spec document",
                )
            )

        return violations

    async def _check_agents_md_freshness(
        self,
        repo_path: str,
    ) -> List[ContextViolation]:
        """
        Check if AGENTS.md is fresh (updated within 7 days).

        Args:
            repo_path: Repository root path

        Returns:
            List of warnings (non-blocking)
        """
        violations: List[ContextViolation] = []

        agents_file = Path(repo_path) / self.agents_md_path

        if not agents_file.exists():
            # AGENTS.md doesn't exist - info level
            violations.append(
                ContextViolation(
                    type=ContextViolationType.STALE_CONTEXT,
                    severity=ViolationSeverity.INFO,
                    message="AGENTS.md not found in repository",
                    fix=(
                        f"Create AGENTS.md with project context\n"
                        f"Run: sdlcctl agents init"
                    ),
                    cli_command="sdlcctl agents init",
                )
            )
        else:
            # Check file age
            stat = agents_file.stat()
            modified_time = datetime.fromtimestamp(stat.st_mtime)
            age_days = (datetime.now() - modified_time).days

            if age_days > self.staleness_days:
                violations.append(
                    ContextViolation(
                        type=ContextViolationType.STALE_CONTEXT,
                        severity=ViolationSeverity.WARNING,
                        message=f"AGENTS.md is {age_days} days old (threshold: {self.staleness_days})",
                        fix="Update AGENTS.md with recent project changes",
                        cli_command="sdlcctl agents update",
                    )
                )

        return violations

    async def _check_module_annotation_consistency(
        self,
        changed_files: List[str],
        repo_path: str,
    ) -> List[ContextViolation]:
        """
        Check if @module annotations match directory structure.

        Args:
            changed_files: List of changed file paths
            repo_path: Repository root path

        Returns:
            List of violations
        """
        violations: List[ContextViolation] = []

        for file_path in changed_files:
            # Skip non-Python/TypeScript files
            if not file_path.endswith((".py", ".ts", ".tsx", ".js", ".jsx")):
                continue

            full_path = Path(repo_path) / file_path
            if not full_path.exists():
                continue

            # Read file header (first 50 lines)
            try:
                with open(full_path, "r", encoding="utf-8") as f:
                    header_lines = [f.readline() for _ in range(50)]
                header = "".join(header_lines)
            except Exception as e:
                logger.warning(f"Could not read file {file_path}: {e}")
                continue

            # Extract @module annotation
            module_match = self.MODULE_PATTERN.search(header)
            if module_match:
                declared_module = module_match.group(1)
                inferred_module = self._infer_module_from_path(file_path)

                if declared_module.lower() != inferred_module.lower():
                    violations.append(
                        ContextViolation(
                            type=ContextViolationType.MODULE_MISMATCH,
                            severity=ViolationSeverity.ERROR,
                            message=(
                                f"Module annotation '{declared_module}' doesn't match "
                                f"path-inferred module '{inferred_module}'"
                            ),
                            file_path=file_path,
                            fix=(
                                f"Update @module annotation to: @module {inferred_module}\n"
                                f"Or move file to match declared module"
                            ),
                        )
                    )

        return violations

    async def _extract_adr_annotation(
        self,
        file_path: str,
        repo_path: str,
    ) -> List[str]:
        """
        Extract @adr annotations from file header.

        Args:
            file_path: Path to file
            repo_path: Repository root path

        Returns:
            List of ADR IDs found in annotations
        """
        full_path = Path(repo_path) / file_path
        if not full_path.exists():
            return []

        try:
            with open(full_path, "r", encoding="utf-8") as f:
                header_lines = [f.readline() for _ in range(50)]
            header = "".join(header_lines)
        except Exception:
            return []

        matches = self.ADR_PATTERN.findall(header)
        return [m.upper() for m in matches]

    async def _load_adrs(self, repo_path: str) -> None:
        """
        Load all ADRs from repository.

        Args:
            repo_path: Repository root path
        """
        adr_dir = Path(repo_path) / self.adr_path
        if not adr_dir.exists():
            logger.warning(f"ADR directory not found: {adr_dir}")
            return

        self._adr_cache.clear()

        for adr_file in adr_dir.glob("*.md"):
            try:
                content = adr_file.read_text()
                adr_id = self._extract_adr_id(adr_file.stem)
                if adr_id:
                    status = self._extract_adr_status(content)
                    title = self._extract_adr_title(content)
                    modules = self._extract_adr_modules(content)

                    self._adr_cache[adr_id] = ADR(
                        id=adr_id,
                        title=title,
                        status=status,
                        file_path=str(adr_file),
                        content=content,
                        modules=modules,
                    )
            except Exception as e:
                logger.warning(f"Failed to load ADR {adr_file}: {e}")

        logger.info(f"Loaded {len(self._adr_cache)} ADRs")

    def _extract_adr_id(self, filename: str) -> Optional[str]:
        """Extract ADR ID from filename."""
        # Pattern: ADR-NNN-Title or NNN-Title
        match = re.match(r"(ADR-\d+)", filename, re.IGNORECASE)
        if match:
            return match.group(1).upper()

        match = re.match(r"(\d+)", filename)
        if match:
            return f"ADR-{match.group(1).zfill(3)}"

        return None

    def _extract_adr_title(self, content: str) -> str:
        """Extract title from ADR content."""
        # Look for # Title or Title: line
        lines = content.split("\n")
        for line in lines[:10]:
            if line.startswith("# "):
                return line[2:].strip()
            if line.startswith("Title:"):
                return line[6:].strip()
        return "Unknown"

    def _extract_adr_status(self, content: str) -> ADRStatus:
        """Extract status from ADR content."""
        for status, pattern in self.STATUS_PATTERNS.items():
            if pattern.search(content):
                return status
        return ADRStatus.PROPOSED

    def _extract_adr_modules(self, content: str) -> List[str]:
        """Extract affected modules from ADR content."""
        modules: List[str] = []

        # Look for affects: or modules: section
        affects_match = re.search(
            r"(?:affects|modules)[:\s]*\[([^\]]+)\]",
            content,
            re.IGNORECASE,
        )
        if affects_match:
            module_str = affects_match.group(1)
            modules = [m.strip().strip('"\'') for m in module_str.split(",")]

        return modules

    def _infer_module_from_path(self, file_path: str) -> str:
        """
        Infer module name from file path.

        Examples:
        - backend/app/services/auth.py → services.auth
        - frontend/src/components/Button.tsx → components.Button
        """
        path = Path(file_path)

        # Remove common prefixes
        parts = list(path.parts)
        for prefix in ["backend", "frontend", "app", "src", "lib"]:
            if parts and parts[0] == prefix:
                parts = parts[1:]

        # Remove filename, keep directory
        if parts:
            parts = parts[:-1]

        # Join with dots
        module = ".".join(parts) if parts else "root"
        return module

    def _is_module_file(self, file_path: str, module: str) -> bool:
        """Check if file belongs to the specified module."""
        inferred = self._infer_module_from_path(file_path)
        return inferred.lower() == module.lower() or inferred.lower().startswith(module.lower() + ".")

    def _get_default_repo_path(self) -> str:
        """Get default repository path."""
        return os.getcwd()


# ============================================================================
# Factory Functions
# ============================================================================

_context_authority_instance: Optional[ContextAuthorityEngineV1] = None


def create_context_authority_engine(
    adr_path: str = ContextAuthorityEngineV1.DEFAULT_ADR_PATH,
    spec_path: str = ContextAuthorityEngineV1.DEFAULT_SPEC_PATH,
    agents_md_path: str = ContextAuthorityEngineV1.DEFAULT_AGENTS_MD,
    staleness_days: int = ContextAuthorityEngineV1.AGENTS_MD_STALENESS_DAYS,
) -> ContextAuthorityEngineV1:
    """
    Create a new Context Authority Engine V1 instance.

    Args:
        adr_path: Path to ADR documents
        spec_path: Path to design spec documents
        agents_md_path: Path to AGENTS.md
        staleness_days: Days after which AGENTS.md is considered stale

    Returns:
        ContextAuthorityEngineV1 instance
    """
    return ContextAuthorityEngineV1(
        adr_path=adr_path,
        spec_path=spec_path,
        agents_md_path=agents_md_path,
        staleness_days=staleness_days,
    )


def get_context_authority_engine() -> ContextAuthorityEngineV1:
    """
    Get singleton Context Authority Engine instance.

    Returns:
        ContextAuthorityEngineV1 singleton instance
    """
    global _context_authority_instance
    if _context_authority_instance is None:
        _context_authority_instance = create_context_authority_engine()
    return _context_authority_instance
