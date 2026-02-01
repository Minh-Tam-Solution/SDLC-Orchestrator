"""
Context Authority Engine V2 - Gate-Aware Dynamic Context
SDLC Orchestrator - Sprint 120 (Feb 3-14, 2026)

Version: 2.0.0
Date: January 29, 2026
Status: ACTIVE - Sprint 120 Implementation
Authority: CTO + Backend Lead Approved
Framework: SDLC 6.0 Quality Assurance System

Purpose:
- Extend V1 with gate status integration
- Vibecoding Index awareness
- Dynamic AGENTS.md overlay generation
- Context snapshots for audit trail

Core Features (SPEC-0011):
1. Gate-Aware Validation: Block code in wrong stage
2. Index-Aware Warnings: Route based on vibecoding index zone
3. Dynamic Overlay: Generate context based on project state
4. Audit Snapshots: Immutable record of all validations

References:
- SPEC-0011: Context Authority V2 - Gate-Aware Dynamic Context
- ADR-041: Framework 6.0 Governance System Design
- Sprint 120 Plan: SPRINT-120-CONTEXT-AUTHORITY-V2-GATES.md
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from fnmatch import fnmatch
from typing import Any, Dict, List, Optional, Tuple
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
from app.services.governance.context_authority import (
    ContextAuthorityEngineV1,
    ContextValidationResult,
    ContextViolation,
    ContextViolationType,
    ViolationSeverity,
    CodeSubmission,
)

logger = logging.getLogger(__name__)


# ============================================================================
# Extended Enums for V2
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
# Data Classes for V2
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

        Template variables:
        - {date}: Current date (YYYY-MM-DD)
        - {index}: Vibecoding index value
        - {stage}: Current SDLC stage
        - {tier}: Project tier
        - {gate}: Last passed gate
        - {top_signals}: Top contributing signals (placeholder)

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
            from datetime import timedelta
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
        # TODO: Integrate with Gates service in Sprint 120 Track B
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
        # TODO: Integrate with Vibecoding service
        return 0

    def clear_cache(self) -> None:
        """Clear template cache."""
        self._template_cache.clear()
        self._cache_expires_at = None
        logger.debug("Template cache cleared")


# ============================================================================
# Factory Functions
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
