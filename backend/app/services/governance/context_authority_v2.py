"""
=========================================================================
Context Authority Engine - Unified V1+V2
SDLC Orchestrator - Sprint 173 (Governance Loop Completion)

Version: 2.1.0
Date: February 15, 2026
Status: ACTIVE - Sprint 173 Phase 2.1
Authority: CTO + Backend Lead Approved
Framework: SDLC 6.0.5 Quality Assurance System

Purpose:
- Unified Context Authority engine (V1 absorbed into V2)
- V1: Metadata & linkage validation (ADRs, specs, AGENTS.md, modules)
- V2: Gate-aware dynamic context (stage blocking, vibecoding index, overlay)
- Context snapshots for audit trail

Sprint 173 Merge (Strangler Fig):
- V1 code (enums, data classes, engine) moved here from context_authority.py
- context_authority.py now re-exports from here (facade, 1-sprint deprecation)
- Zero behavior change: golden snapshot tests verify parity

Core Checks (V1 - Metadata):
1. ADR Linkage: Module → ADR reference
2. Design Doc Reference: New feature → spec file
3. AGENTS.md Freshness: Context file age < 7 days
4. Module Annotation Consistency: Header ↔ directory

Core Features (V2 - Gate-Aware):
1. Gate-Aware Validation: Block code in wrong stage
2. Index-Aware Warnings: Route based on vibecoding index zone
3. Dynamic Overlay: Generate context based on project state
4. Audit Snapshots: Immutable record of all validations

References:
- SPEC-0011: Context Authority V2 - Gate-Aware Dynamic Context
- ADR-041: Framework 6.0 Governance System Design
- ADR-053: Governance Loop State Machine

Zero Mock Policy: Real validation with actual file checks
=========================================================================
"""

import logging
import os
import re
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from fnmatch import fnmatch
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.context_authority_v2 import (
    ContextOverlayTemplate,
    ContextSnapshot,
    ContextOverlayApplication,
)
from app.repositories.context_authority_v2 import (
    ContextOverlayTemplateRepository,
    ContextSnapshotRepository,
    ContextOverlayApplicationRepository,
)

logger = logging.getLogger(__name__)


# ============================================================================
# V1 Enums (moved from context_authority.py)
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
# V1 Data Classes (moved from context_authority.py)
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
# Context Authority Engine V1 (moved from context_authority.py)
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
# V1 Factory Functions (moved from context_authority.py)
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


# ============================================================================
# V2 Extended Enums
# ============================================================================


class ContextViolationTypeV2(Enum):
    """Extended violation types for V2."""

    # V1 types (inherited)
    ORPHAN_CODE = "orphan_code"
    NO_ADR_LINKAGE = "no_adr_linkage"
    NO_DESIGN_DOC = "no_design_doc"
    STALE_CONTEXT = "stale_context"
    MODULE_MISMATCH = "module_mismatch"
    DEPRECATED_ADR = "deprecated_adr"
    EMPTY_SPEC = "empty_spec"

    # V2 types (new)
    STAGE_BLOCKED = "stage_blocked"
    GATE_PENDING = "gate_pending"
    HIGH_VIBECODING_INDEX = "high_vibecoding_index"
    TIER_MISMATCH = "tier_mismatch"


class VibecodingZone(Enum):
    """Vibecoding index zones (SPEC-0001)."""

    GREEN = "GREEN"      # 0-30: Auto-approve
    YELLOW = "YELLOW"    # 31-60: Tech Lead review
    ORANGE = "ORANGE"    # 61-80: CEO should review
    RED = "RED"          # 81-100: CEO must review


# ============================================================================
# V2 Data Classes
# ============================================================================


@dataclass
class GateStatus:
    """Current gate status for a project."""

    project_id: UUID
    current_stage: str  # "00", "01", "02", "04", "05", "06"
    last_passed_gate: Optional[str] = None  # "G0.1", "G0.2", "G1", "G2", "G3"
    pending_gates: List[str] = field(default_factory=list)
    blocked_paths: List[str] = field(default_factory=list)
    allowed_paths: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "project_id": str(self.project_id),
            "current_stage": self.current_stage,
            "last_passed_gate": self.last_passed_gate,
            "pending_gates": self.pending_gates,
            "blocked_paths": self.blocked_paths,
            "allowed_paths": self.allowed_paths,
        }


@dataclass
class ContextViolationV2:
    """Extended context violation for V2."""

    type: str  # Using string to support both V1 and V2 types
    severity: ViolationSeverity
    message: str
    file_path: Optional[str] = None
    module: Optional[str] = None
    fix: Optional[str] = None
    cli_command: Optional[str] = None
    related_adr: Optional[str] = None
    gate: Optional[str] = None
    zone: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "type": self.type,
            "severity": self.severity.value,
            "message": self.message,
            "file_path": self.file_path,
            "module": self.module,
            "fix": self.fix,
            "cli_command": self.cli_command,
            "related_adr": self.related_adr,
            "gate": self.gate,
            "zone": self.zone,
        }


@dataclass
class ContextValidationResultV2:
    """Result of Context Authority V2 validation."""

    valid: bool
    v1_result: ContextValidationResult
    gate_violations: List[ContextViolationV2] = field(default_factory=list)
    index_warnings: List[ContextViolationV2] = field(default_factory=list)
    dynamic_overlay: str = ""
    snapshot_id: Optional[UUID] = None
    tier: str = "STANDARD"
    gate_status: Optional[GateStatus] = None
    vibecoding_index: int = 0
    vibecoding_zone: VibecodingZone = VibecodingZone.GREEN
    applied_templates: List[UUID] = field(default_factory=list)
    validated_at: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API response."""
        return {
            "valid": self.valid,
            "v1_result": self.v1_result.to_dict(),
            "gate_violations": [v.to_dict() for v in self.gate_violations],
            "index_warnings": [w.to_dict() for w in self.index_warnings],
            "dynamic_overlay": self.dynamic_overlay,
            "snapshot_id": str(self.snapshot_id) if self.snapshot_id else None,
            "tier": self.tier,
            "gate_status": self.gate_status.to_dict() if self.gate_status else None,
            "vibecoding_index": self.vibecoding_index,
            "vibecoding_zone": self.vibecoding_zone.value,
            "applied_templates": [str(t) for t in self.applied_templates],
            "validated_at": self.validated_at.isoformat(),
        }


@dataclass
class DynamicOverlayResult:
    """Result of dynamic overlay generation."""

    content: str
    templates_applied: List[UUID]
    gate_status: GateStatus
    vibecoding_index: int
    vibecoding_zone: VibecodingZone
    generated_at: datetime = field(default_factory=datetime.utcnow)


# ============================================================================
# Stage Rules Configuration
# ============================================================================

STAGE_RULES: Dict[str, Dict[str, List[str]]] = {
    "00": {
        "allowed": ["docs/00-*/**", "README.md", ".gitignore", "CLAUDE.md", "AGENTS.md"],
        "blocked": ["src/**", "backend/**", "frontend/**", "*.py", "*.ts", "*.tsx"],
        "description": "Foundation stage - documentation only",
    },
    "01": {
        "allowed": ["docs/01-*/**", "docs/00-*/**"],
        "blocked": ["src/**", "backend/app/**", "frontend/src/**"],
        "description": "Planning stage - requirements and design docs",
    },
    "02": {
        "allowed": [
            "docs/02-*/**",
            "docs/01-*/**",
            "docs/00-*/**",
            "*.prisma",
            "openapi/**",
            "*.openapi.yaml",
            "*.openapi.json",
        ],
        "blocked": ["backend/app/**", "frontend/src/**"],
        "description": "Design stage - architecture and API contracts",
    },
    "04": {
        "allowed": ["**"],
        "blocked": [],
        "description": "Build stage - all code allowed",
    },
    "05": {
        "allowed": ["tests/**", "e2e/**", "**/test_*", "**/fix_*", "docs/05-*/**"],
        "blocked": ["**/feat_*"],
        "description": "Test stage - tests and bug fixes only",
    },
    "06": {
        "allowed": ["docker/**", "k8s/**", ".github/workflows/**", "docs/06-*/**"],
        "blocked": ["backend/app/services/**", "backend/app/api/**", "frontend/src/**"],
        "description": "Deploy stage - infrastructure only",
    },
}


# ============================================================================
# Context Authority Engine V2
# ============================================================================


class ContextAuthorityEngineV2:
    """
    Context Authority Engine V2 - Gate-Aware Dynamic Context.

    Extends V1 with:
    - Gate status integration (stage-aware file blocking)
    - Vibecoding Index awareness (zone-based routing)
    - Dynamic AGENTS.md overlay (context injection)
    - Context snapshots for audit (immutable records)

    Architecture:
    - Uses V1 engine for base validation
    - Adds gate/index checks on top
    - Generates dynamic overlay from templates
    - Creates immutable snapshots for audit

    Usage:
        engine = ContextAuthorityEngineV2(db)
        result = await engine.validate_context_v2(submission)
    """

    # Zone thresholds (SPEC-0011)
    ZONE_THRESHOLDS = {
        VibecodingZone.GREEN: (0, 30),
        VibecodingZone.YELLOW: (31, 60),
        VibecodingZone.ORANGE: (61, 80),
        VibecodingZone.RED: (81, 100),
    }

    def __init__(
        self,
        db: AsyncSession,
        v1_engine: Optional[ContextAuthorityEngineV1] = None,
    ):
        """
        Initialize Context Authority Engine V2.

        Args:
            db: Async database session
            v1_engine: Optional V1 engine instance (created if not provided)
        """
        self.db = db
        self.v1_engine = v1_engine or ContextAuthorityEngineV1()

        # Initialize repositories
        self.template_repo = ContextOverlayTemplateRepository(db)
        self.snapshot_repo = ContextSnapshotRepository(db)
        self.application_repo = ContextOverlayApplicationRepository(db)

        # Template cache
        self._template_cache: Dict[str, List[ContextOverlayTemplate]] = {}
        self._cache_expires_at: Optional[datetime] = None
        self._cache_ttl_seconds = 300  # 5 minutes

        logger.info("ContextAuthorityEngineV2 initialized")

    async def validate_context_v2(
        self,
        submission: CodeSubmission,
        gate_status: Optional[GateStatus] = None,
        vibecoding_index: Optional[int] = None,
        tier: str = "STANDARD",
    ) -> ContextValidationResultV2:
        """
        Gate-aware context validation.

        Performs:
        1. V1 validation (ADR linkage, design doc, AGENTS.md, module consistency)
        2. Gate constraint validation (stage-aware file blocking)
        3. Vibecoding index warnings (zone-based routing)
        4. Dynamic overlay generation
        5. Snapshot creation for audit

        Args:
            submission: Code submission to validate
            gate_status: Current gate status (fetched if not provided)
            vibecoding_index: Current vibecoding index (defaults to 0)
            tier: Project tier (LITE, STANDARD, PROFESSIONAL, ENTERPRISE)

        Returns:
            ContextValidationResultV2 with all validation results
        """
        # Get gate status if not provided
        if gate_status is None:
            gate_status = await self._get_default_gate_status(submission.project_id)

        # Get vibecoding index if not provided
        if vibecoding_index is None:
            vibecoding_index = await self._get_recent_vibecoding_index(
                submission.project_id
            )

        # Determine vibecoding zone
        vibecoding_zone = self._get_zone_from_index(vibecoding_index)

        # Run V1 validation
        v1_result = await self.v1_engine.validate_context(submission)

        # Check gate constraints (stage-aware)
        gate_violations = await self._check_gate_constraints(
            submission, gate_status
        )

        # Check vibecoding index constraints
        index_warnings = self._check_index_constraints(
            vibecoding_index, vibecoding_zone
        )

        # Generate dynamic overlay
        overlay_result = await self._generate_dynamic_overlay(
            gate_status, vibecoding_index, vibecoding_zone, tier
        )

        # Determine overall validity
        # Valid = V1 valid + no gate violations (warnings don't block)
        is_valid = v1_result.valid and len(gate_violations) == 0

        # Create snapshot for audit
        snapshot_id = await self._create_snapshot(
            submission=submission,
            gate_status=gate_status,
            vibecoding_index=vibecoding_index,
            vibecoding_zone=vibecoding_zone,
            dynamic_overlay=overlay_result.content,
            tier=tier,
            is_valid=is_valid,
            v1_result=v1_result,
            gate_violations=gate_violations,
            index_warnings=index_warnings,
            applied_templates=overlay_result.templates_applied,
        )

        result = ContextValidationResultV2(
            valid=is_valid,
            v1_result=v1_result,
            gate_violations=gate_violations,
            index_warnings=index_warnings,
            dynamic_overlay=overlay_result.content,
            snapshot_id=snapshot_id,
            tier=tier,
            gate_status=gate_status,
            vibecoding_index=vibecoding_index,
            vibecoding_zone=vibecoding_zone,
            applied_templates=overlay_result.templates_applied,
        )

        logger.info(
            f"Context V2 validation: {'PASS' if is_valid else 'FAIL'} - "
            f"stage={gate_status.current_stage}, index={vibecoding_index}, "
            f"zone={vibecoding_zone.value}, gate_violations={len(gate_violations)}"
        )

        return result

    async def get_dynamic_overlay(
        self,
        project_id: UUID,
        gate_status: Optional[GateStatus] = None,
        vibecoding_index: Optional[int] = None,
        tier: str = "STANDARD",
    ) -> DynamicOverlayResult:
        """
        Get current dynamic overlay for a project.

        Args:
            project_id: Project UUID
            gate_status: Current gate status
            vibecoding_index: Current vibecoding index
            tier: Project tier

        Returns:
            DynamicOverlayResult with generated overlay
        """
        if gate_status is None:
            gate_status = await self._get_default_gate_status(project_id)

        if vibecoding_index is None:
            vibecoding_index = await self._get_recent_vibecoding_index(project_id)

        vibecoding_zone = self._get_zone_from_index(vibecoding_index)

        return await self._generate_dynamic_overlay(
            gate_status, vibecoding_index, vibecoding_zone, tier
        )

    async def get_snapshot(self, snapshot_id: UUID) -> Optional[ContextSnapshot]:
        """Get a context snapshot by ID."""
        return await self.snapshot_repo.get_by_id(snapshot_id)

    async def get_snapshot_by_submission(
        self, submission_id: UUID
    ) -> Optional[ContextSnapshot]:
        """Get context snapshot for a submission."""
        return await self.snapshot_repo.get_by_submission(submission_id)

    async def list_project_snapshots(
        self,
        project_id: UUID,
        limit: int = 50,
        offset: int = 0,
    ) -> List[ContextSnapshot]:
        """List snapshots for a project."""
        return await self.snapshot_repo.list_by_project(
            project_id, limit=limit, offset=offset
        )

    # =========================================================================
    # Gate Constraint Checking
    # =========================================================================

    async def _check_gate_constraints(
        self,
        submission: CodeSubmission,
        gate_status: GateStatus,
    ) -> List[ContextViolationV2]:
        """
        Check if submission violates gate constraints.

        Stage-aware file path rules:
        - Stage 00: Only docs/00-* allowed
        - Stage 01: Only docs/01-* allowed
        - Stage 02: Design docs + schema files allowed
        - Stage 04: All code allowed (BUILD)
        - Stage 05: Tests and bug fixes only
        - Stage 06: Infrastructure only

        Args:
            submission: Code submission
            gate_status: Current gate status

        Returns:
            List of gate violations
        """
        violations: List[ContextViolationV2] = []
        current_stage = gate_status.current_stage

        # Get stage rules
        stage_rules = STAGE_RULES.get(current_stage)
        if not stage_rules:
            logger.warning(f"Unknown stage: {current_stage}, allowing all")
            return violations

        blocked_patterns = stage_rules.get("blocked", [])
        allowed_patterns = stage_rules.get("allowed", [])
        description = stage_rules.get("description", "")

        for file_path in submission.changed_files:
            # Check if file is blocked
            is_blocked = self._matches_patterns(file_path, blocked_patterns)
            is_allowed = self._matches_patterns(file_path, allowed_patterns)

            # If blocked and not explicitly allowed, add violation
            if is_blocked and not is_allowed:
                violations.append(
                    ContextViolationV2(
                        type=ContextViolationTypeV2.STAGE_BLOCKED.value,
                        severity=ViolationSeverity.ERROR,
                        message=(
                            f"File '{file_path}' is blocked in Stage {current_stage} "
                            f"({description})"
                        ),
                        file_path=file_path,
                        gate=gate_status.last_passed_gate,
                        fix=(
                            f"Complete Stage {current_stage} gates before "
                            f"modifying this file.\n"
                            f"Allowed in this stage: {', '.join(allowed_patterns[:3])}"
                        ),
                        cli_command="sdlcctl gate status",
                    )
                )

        return violations

    # =========================================================================
    # Vibecoding Index Checking
    # =========================================================================

    def _check_index_constraints(
        self,
        vibecoding_index: int,
        vibecoding_zone: VibecodingZone,
    ) -> List[ContextViolationV2]:
        """
        Check vibecoding index constraints.

        Zone actions:
        - GREEN (0-30): Auto-approve
        - YELLOW (31-60): Tech Lead review recommended
        - ORANGE (61-80): CEO should review
        - RED (81-100): CEO must review (blocks)

        Args:
            vibecoding_index: Current index value
            vibecoding_zone: Determined zone

        Returns:
            List of index warnings (non-blocking)
        """
        warnings: List[ContextViolationV2] = []

        if vibecoding_zone == VibecodingZone.RED:
            warnings.append(
                ContextViolationV2(
                    type=ContextViolationTypeV2.HIGH_VIBECODING_INDEX.value,
                    severity=ViolationSeverity.ERROR,
                    message=(
                        f"Vibecoding Index {vibecoding_index} is in RED zone (>80). "
                        f"CEO review required before merge."
                    ),
                    zone=vibecoding_zone.value,
                    fix=(
                        "Review code for:\n"
                        "- Architectural smells (god classes, feature envy)\n"
                        "- High AI dependency ratio\n"
                        "- Large change surface area\n"
                        "Consider breaking into smaller PRs."
                    ),
                    cli_command="sdlcctl vibecoding analyze",
                )
            )
        elif vibecoding_zone == VibecodingZone.ORANGE:
            warnings.append(
                ContextViolationV2(
                    type=ContextViolationTypeV2.HIGH_VIBECODING_INDEX.value,
                    severity=ViolationSeverity.WARNING,
                    message=(
                        f"Vibecoding Index {vibecoding_index} is in ORANGE zone (61-80). "
                        f"CEO review recommended."
                    ),
                    zone=vibecoding_zone.value,
                    fix="Consider Tech Lead review before proceeding.",
                    cli_command="sdlcctl vibecoding analyze",
                )
            )
        elif vibecoding_zone == VibecodingZone.YELLOW:
            warnings.append(
                ContextViolationV2(
                    type=ContextViolationTypeV2.HIGH_VIBECODING_INDEX.value,
                    severity=ViolationSeverity.INFO,
                    message=(
                        f"Vibecoding Index {vibecoding_index} is in YELLOW zone (31-60). "
                        f"Human review recommended."
                    ),
                    zone=vibecoding_zone.value,
                    fix="Ensure code review before merge.",
                )
            )

        return warnings

    # =========================================================================
    # Dynamic Overlay Generation
    # =========================================================================

    async def _generate_dynamic_overlay(
        self,
        gate_status: GateStatus,
        vibecoding_index: int,
        vibecoding_zone: VibecodingZone,
        tier: str,
    ) -> DynamicOverlayResult:
        """
        Generate dynamic overlay from templates.

        Template selection:
        1. Gate-based: Triggered by last_passed_gate
        2. Zone-based: Triggered by vibecoding_zone
        3. Stage-based: Triggered by current_stage constraints

        Args:
            gate_status: Current gate status
            vibecoding_index: Current vibecoding index
            vibecoding_zone: Current zone
            tier: Project tier

        Returns:
            DynamicOverlayResult with generated content
        """
        overlays: List[str] = []
        applied_templates: List[UUID] = []

        # Prepare template variables
        variables = {
            "date": datetime.utcnow().strftime("%Y-%m-%d"),
            "index": str(vibecoding_index),
            "stage": gate_status.current_stage,
            "tier": tier,
            "gate": gate_status.last_passed_gate or "None",
            "top_signals": "Intent clarity, Code ownership, Context completeness",
        }

        # 1. Get gate-based overlays
        if gate_status.last_passed_gate:
            gate_templates = await self._get_templates(
                trigger_type="gate_pass",
                trigger_value=gate_status.last_passed_gate,
                tier=tier,
            )
            for template in gate_templates:
                rendered = self._render_template(template.overlay_content, variables)
                overlays.append(rendered)
                applied_templates.append(template.id)

        # 2. Get zone-based overlays (for non-green zones)
        if vibecoding_zone != VibecodingZone.GREEN:
            zone_templates = await self._get_templates(
                trigger_type="index_zone",
                trigger_value=vibecoding_zone.value.lower(),
                tier=tier,
            )
            for template in zone_templates:
                rendered = self._render_template(template.overlay_content, variables)
                overlays.append(rendered)
                applied_templates.append(template.id)

        # 3. Get stage constraint overlays (for non-build stages)
        if gate_status.current_stage != "04":
            stage_templates = await self._get_templates(
                trigger_type="stage_constraint",
                trigger_value=f"stage_{gate_status.current_stage}_code_block",
                tier=tier,
            )
            for template in stage_templates:
                rendered = self._render_template(template.overlay_content, variables)
                overlays.append(rendered)
                applied_templates.append(template.id)

        # Combine overlays with separators
        content = "\n\n---\n\n".join(overlays) if overlays else ""

        return DynamicOverlayResult(
            content=content,
            templates_applied=applied_templates,
            gate_status=gate_status,
            vibecoding_index=vibecoding_index,
            vibecoding_zone=vibecoding_zone,
        )

    async def _get_templates(
        self,
        trigger_type: str,
        trigger_value: str,
        tier: str,
    ) -> List[ContextOverlayTemplate]:
        """
        Get templates matching trigger conditions with caching.

        Args:
            trigger_type: Type of trigger
            trigger_value: Value of trigger
            tier: Project tier

        Returns:
            List of matching templates
        """
        cache_key = f"{trigger_type}:{trigger_value}:{tier}"

        # Check cache
        if self._cache_expires_at and datetime.utcnow() < self._cache_expires_at:
            if cache_key in self._template_cache:
                return self._template_cache[cache_key]

        # Fetch from database
        templates = await self.template_repo.get_by_trigger(
            trigger_type=trigger_type,
            trigger_value=trigger_value,
            tier=tier,
            active_only=True,
        )

        # Update cache
        self._template_cache[cache_key] = templates
        if not self._cache_expires_at or datetime.utcnow() >= self._cache_expires_at:
            self._cache_expires_at = datetime.utcnow() + timedelta(
                seconds=self._cache_ttl_seconds
            )

        return templates

    def _render_template(
        self,
        template_content: str,
        variables: Dict[str, str],
    ) -> str:
        """
        Render template with variable substitution.

        Args:
            template_content: Template content with {variable} placeholders
            variables: Variable values

        Returns:
            Rendered content
        """
        try:
            return template_content.format(**variables)
        except KeyError as e:
            logger.warning(f"Missing template variable: {e}")
            return template_content

    # =========================================================================
    # Snapshot Creation
    # =========================================================================

    async def _create_snapshot(
        self,
        submission: CodeSubmission,
        gate_status: GateStatus,
        vibecoding_index: int,
        vibecoding_zone: VibecodingZone,
        dynamic_overlay: str,
        tier: str,
        is_valid: bool,
        v1_result: ContextValidationResult,
        gate_violations: List[ContextViolationV2],
        index_warnings: List[ContextViolationV2],
        applied_templates: List[UUID],
    ) -> UUID:
        """
        Create context snapshot for audit.

        Args:
            submission: Code submission
            gate_status: Gate status at validation time
            vibecoding_index: Index at validation time
            vibecoding_zone: Zone at validation time
            dynamic_overlay: Generated overlay content
            tier: Project tier
            is_valid: Overall validation result
            v1_result: V1 validation result
            gate_violations: Gate constraint violations
            index_warnings: Index warnings
            applied_templates: Templates applied

        Returns:
            Created snapshot UUID
        """
        snapshot = await self.snapshot_repo.create(
            submission_id=submission.submission_id,
            project_id=submission.project_id,
            gate_status=gate_status.to_dict(),
            vibecoding_index=vibecoding_index,
            vibecoding_zone=vibecoding_zone.value,
            dynamic_overlay=dynamic_overlay,
            tier=tier,
            is_valid=is_valid,
            v1_result=v1_result.to_dict(),
            gate_violations=[v.to_dict() for v in gate_violations],
            index_warnings=[w.to_dict() for w in index_warnings],
            applied_template_ids=[str(t) for t in applied_templates],
        )

        # Record template applications
        if applied_templates:
            for order, template_id in enumerate(applied_templates):
                template = await self.template_repo.get_by_id(template_id)
                if template:
                    await self.application_repo.create(
                        snapshot_id=snapshot.id,
                        template_id=template_id,
                        template_content_snapshot=template.overlay_content,
                        rendered_content="",  # Content already in snapshot
                        variables_used={
                            "date": datetime.utcnow().strftime("%Y-%m-%d"),
                            "index": str(vibecoding_index),
                            "stage": gate_status.current_stage,
                            "tier": tier,
                        },
                        application_order=order,
                    )

        return snapshot.id

    # =========================================================================
    # Helper Methods
    # =========================================================================

    def _matches_patterns(
        self,
        file_path: str,
        patterns: List[str],
    ) -> bool:
        """
        Check if file path matches any of the glob patterns.

        Args:
            file_path: File path to check
            patterns: List of glob patterns

        Returns:
            True if matches any pattern
        """
        for pattern in patterns:
            if fnmatch(file_path, pattern):
                return True
        return False

    def _get_zone_from_index(self, index: int) -> VibecodingZone:
        """
        Determine vibecoding zone from index value.

        Args:
            index: Vibecoding index (0-100)

        Returns:
            VibecodingZone enum value
        """
        for zone, (min_val, max_val) in self.ZONE_THRESHOLDS.items():
            if min_val <= index <= max_val:
                return zone
        return VibecodingZone.RED  # Default to most restrictive

    async def _get_default_gate_status(self, project_id: UUID) -> GateStatus:
        """
        Get default gate status for a project.

        In production, this would query the Gates service.
        For now, returns a default BUILD stage status.

        Args:
            project_id: Project UUID

        Returns:
            GateStatus with defaults
        """
        return GateStatus(
            project_id=project_id,
            current_stage="04",  # Default to BUILD
            last_passed_gate="G2",
            pending_gates=["G3"],
        )

    async def _get_recent_vibecoding_index(self, project_id: UUID) -> int:
        """
        Get recent vibecoding index for a project.

        In production, this would query the Vibecoding service.
        For now, returns 0 (GREEN zone).

        Args:
            project_id: Project UUID

        Returns:
            Vibecoding index (0-100)
        """
        return 0

    def clear_cache(self) -> None:
        """Clear template cache."""
        self._template_cache.clear()
        self._cache_expires_at = None
        logger.debug("Template cache cleared")


# ============================================================================
# V2 Factory Functions
# ============================================================================

_engine_instance: Optional[ContextAuthorityEngineV2] = None


def get_context_authority_engine_v2(
    db: AsyncSession,
) -> ContextAuthorityEngineV2:
    """
    Get or create Context Authority Engine V2 instance.

    Note: Each request should use a new instance with its own db session.
    This factory ensures proper dependency injection.

    Args:
        db: Async database session

    Returns:
        ContextAuthorityEngineV2 instance
    """
    return ContextAuthorityEngineV2(db=db)


def create_context_authority_engine_v2(
    db: AsyncSession,
    v1_engine: Optional[ContextAuthorityEngineV1] = None,
) -> ContextAuthorityEngineV2:
    """
    Create a new Context Authority Engine V2 instance.

    Args:
        db: Async database session
        v1_engine: Optional V1 engine to reuse

    Returns:
        New ContextAuthorityEngineV2 instance
    """
    return ContextAuthorityEngineV2(db=db, v1_engine=v1_engine)
