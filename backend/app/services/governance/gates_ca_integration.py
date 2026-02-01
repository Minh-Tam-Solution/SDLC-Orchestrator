"""
=========================================================================
Gates + Context Authority V2 Integration Service
SDLC Orchestrator - Sprint 120 (Governance Engine Core)

Version: 1.0.0
Date: January 29, 2026
Status: ACTIVE - Sprint 120 Track B
Authority: CTO + Backend Lead Approved
Framework: SDLC 5.3.0 Quality Assurance System

Purpose:
- Integrate Gates Engine with Context Authority V2
- Gate-aware context validation
- Vibecoding Index integration for gate evaluation
- Dynamic overlay generation based on gate status
- Stage-aware file blocking

Core Integration Points:
1. Gate → CA V2: Provide gate status for context overlay
2. CA V2 → Gate: Provide vibecoding index for gate scoring
3. Both: Share stage awareness and file blocking rules

Design References:
- SPEC-0011: Context Authority V2 Technical Design
- Gates Engine: app/services/governance/gates_engine.py
- CA V2 Engine: app/services/governance/context_authority_v2.py

Zero Mock Policy: Real service integration
=========================================================================
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime, UTC
from typing import Any, Dict, List, Optional, Tuple
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.services.governance.gates_engine import (
    GatesEngine,
    GateEvaluationResult,
    GateEvaluationStatus,
    VALID_GATE_CODES,
    GATE_CODE_TO_STAGE,
    GATE_PREREQUISITES,
)
from app.services.opa_policy_service import OPAPolicyService

logger = logging.getLogger(__name__)


# ============================================================================
# Data Classes
# ============================================================================


@dataclass
class GateContextInfo:
    """Gate information for context overlay."""
    gate_code: str
    gate_status: str
    stage: str
    is_approved: bool
    is_blocking: bool
    readiness_score: float
    prerequisites_met: bool
    missing_prerequisites: List[str]
    exit_criteria_met: int
    exit_criteria_total: int


@dataclass
class IntegratedValidationResult:
    """Result of integrated gate + context validation."""
    # Gate results
    gate_passed: bool
    gate_code: str
    gate_status: GateEvaluationStatus
    gate_readiness_score: float
    gate_blocking_issues: List[str]

    # Context results
    context_valid: bool
    vibecoding_index: float
    index_zone: str
    context_violations: List[str]
    context_warnings: List[str]

    # Combined results
    overall_valid: bool
    combined_score: float  # Weighted combination of gate + context
    stage: str
    can_proceed: bool
    blocking_reasons: List[str]
    recommendations: List[str]

    # Metadata
    validated_at: datetime
    duration_ms: float


@dataclass
class StageTransitionCheck:
    """Check result for stage transition."""
    can_transition: bool
    current_stage: str
    target_stage: str
    required_gates: List[str]
    passed_gates: List[str]
    pending_gates: List[str]
    blocking_issues: List[str]


# ============================================================================
# Integration Service
# ============================================================================


class GatesCAIntegrationService:
    """
    Integration service connecting Gates Engine with Context Authority V2.

    Provides:
        - Unified gate + context validation
        - Stage transition checks
        - Dynamic overlay generation with gate context
        - Vibecoding Index integration for gate scoring
        - Combined readiness scoring

    Usage:
        integration = GatesCAIntegrationService(db, gates_engine, ca_engine)
        result = await integration.validate_with_context(
            project_id, gate_code, submission_data
        )
    """

    def __init__(
        self,
        db: AsyncSession,
        gates_engine: Optional[GatesEngine] = None,
        context_authority_engine: Optional[Any] = None,
        opa_service: Optional[OPAPolicyService] = None,
    ):
        """
        Initialize integration service.

        Args:
            db: SQLAlchemy async session
            gates_engine: Gates Engine instance
            context_authority_engine: CA V2 engine instance
            opa_service: OPA policy service instance
        """
        self.db = db
        self.gates_engine = gates_engine
        self.context_authority_engine = context_authority_engine
        self.opa_service = opa_service

        logger.info("GatesCAIntegrationService initialized")

    async def validate_with_context(
        self,
        project_id: UUID,
        gate_code: str,
        submission_data: Optional[Dict[str, Any]] = None,
        changed_files: Optional[List[str]] = None,
        affected_modules: Optional[List[str]] = None,
    ) -> IntegratedValidationResult:
        """
        Perform integrated gate + context validation.

        This method:
        1. Evaluates the gate using Gates Engine
        2. Validates context using CA V2
        3. Combines results with weighted scoring
        4. Determines overall validity and blocking issues

        Args:
            project_id: Project UUID
            gate_code: Gate code to evaluate
            submission_data: Additional submission data
            changed_files: List of changed file paths
            affected_modules: List of affected module names

        Returns:
            IntegratedValidationResult with combined gate + context validation
        """
        start_time = datetime.now(UTC)
        blocking_reasons: List[str] = []
        recommendations: List[str] = []

        # Initialize defaults
        gate_passed = False
        gate_status = GateEvaluationStatus.ERROR
        gate_readiness_score = 0.0
        gate_blocking_issues: List[str] = []

        context_valid = True
        vibecoding_index = 0.0
        index_zone = "GREEN"
        context_violations: List[str] = []
        context_warnings: List[str] = []

        # Step 1: Gate Evaluation
        if self.gates_engine:
            try:
                # Inject context check via CA V2
                if self.context_authority_engine and not self.gates_engine.context_authority_engine:
                    self.gates_engine.context_authority_engine = self.context_authority_engine

                gate_result = await self.gates_engine.evaluate_gate_by_code(
                    project_id=project_id,
                    gate_code=gate_code,
                    submission_data=submission_data,
                )

                gate_passed = gate_result.overall_passed
                gate_status = gate_result.status
                gate_readiness_score = gate_result.readiness_score
                gate_blocking_issues = gate_result.blocking_issues
                recommendations.extend(gate_result.recommendations)

                # Extract context results from gate evaluation
                if gate_result.context_validation:
                    context_valid = gate_result.context_validation.get("valid", True)
                    vibecoding_index = gate_result.vibecoding_index or 0.0
                    index_zone = gate_result.context_validation.get("index_zone", "GREEN")

            except Exception as e:
                logger.error(f"Gate evaluation failed: {e}")
                blocking_reasons.append(f"Gate evaluation error: {str(e)}")

        # Step 2: Context Validation (if not already done by gate)
        if self.context_authority_engine and not gate_result.context_validation:
            try:
                from app.schemas.context_authority import ContextValidationRequest
                from uuid import uuid4

                context_request = ContextValidationRequest(
                    submission_id=uuid4(),
                    project_id=project_id,
                    changed_files=changed_files or ["default"],
                    affected_modules=affected_modules or [],
                    current_stage=GATE_CODE_TO_STAGE.get(gate_code, "UNKNOWN"),
                    gate_code=gate_code,
                )

                context_result = await self.context_authority_engine.validate_context_v2(
                    context_request
                )

                context_valid = context_result.valid
                vibecoding_index = context_result.vibecoding_index
                index_zone = context_result.index_zone

                for v in context_result.violations:
                    context_violations.append(v.message)

                for w in context_result.warnings:
                    context_warnings.append(w.message)

            except Exception as e:
                logger.warning(f"Context validation failed: {e}")
                # Don't block on context errors
                context_valid = True

        # Step 3: Calculate combined score
        # Gate: 60%, Context: 40%
        if gate_readiness_score > 0:
            # Convert vibecoding index to a positive score (lower is better)
            context_score = max(0, 100 - vibecoding_index)
            combined_score = (gate_readiness_score * 0.6) + (context_score * 0.4)
        else:
            combined_score = 0.0

        # Step 4: Determine overall validity
        # Must pass gate AND have acceptable context (not RED zone)
        overall_valid = gate_passed and (index_zone != "RED")

        # Collect blocking reasons
        if not gate_passed:
            blocking_reasons.extend(gate_blocking_issues)

        if index_zone == "RED":
            blocking_reasons.append(
                f"Vibecoding Index {vibecoding_index:.1f} is in RED zone (>80). "
                "Requires CEO review before proceeding."
            )

        # Can proceed if overall valid or only warnings
        can_proceed = overall_valid or (
            gate_status == GateEvaluationStatus.PENDING_EVIDENCE and
            index_zone in ["GREEN", "YELLOW"]
        )

        duration_ms = (datetime.now(UTC) - start_time).total_seconds() * 1000

        return IntegratedValidationResult(
            # Gate results
            gate_passed=gate_passed,
            gate_code=gate_code,
            gate_status=gate_status,
            gate_readiness_score=gate_readiness_score,
            gate_blocking_issues=gate_blocking_issues,
            # Context results
            context_valid=context_valid,
            vibecoding_index=vibecoding_index,
            index_zone=index_zone,
            context_violations=context_violations,
            context_warnings=context_warnings,
            # Combined results
            overall_valid=overall_valid,
            combined_score=round(combined_score, 1),
            stage=GATE_CODE_TO_STAGE.get(gate_code, "UNKNOWN"),
            can_proceed=can_proceed,
            blocking_reasons=blocking_reasons,
            recommendations=recommendations,
            # Metadata
            validated_at=datetime.now(UTC),
            duration_ms=duration_ms,
        )

    async def check_stage_transition(
        self,
        project_id: UUID,
        target_stage: str,
    ) -> StageTransitionCheck:
        """
        Check if project can transition to target stage.

        Args:
            project_id: Project UUID
            target_stage: Target SDLC stage name

        Returns:
            StageTransitionCheck with transition feasibility
        """
        # Find gate(s) for target stage
        target_gates = [
            code for code, stage in GATE_CODE_TO_STAGE.items()
            if stage == target_stage
        ]

        if not target_gates:
            return StageTransitionCheck(
                can_transition=False,
                current_stage="UNKNOWN",
                target_stage=target_stage,
                required_gates=[],
                passed_gates=[],
                pending_gates=[],
                blocking_issues=[f"Unknown stage: {target_stage}"],
            )

        # Get current project state
        current_stage = None
        passed_gates: List[str] = []
        pending_gates: List[str] = []
        blocking_issues: List[str] = []

        if self.gates_engine:
            try:
                summary = await self.gates_engine.get_gate_readiness_summary(project_id)
                current_stage = summary.get("current_stage")

                for gate_code, gate_info in summary.get("gates", {}).items():
                    if gate_info.get("status") == "APPROVED":
                        passed_gates.append(gate_code)
                    elif gate_code in target_gates:
                        pending_gates.append(gate_code)

            except Exception as e:
                blocking_issues.append(f"Failed to get project state: {str(e)}")

        # Check prerequisites for target gates
        for gate_code in target_gates:
            prerequisites = GATE_PREREQUISITES.get(gate_code, [])

            for prereq in prerequisites:
                if prereq not in passed_gates:
                    blocking_issues.append(
                        f"Gate {prereq} must be approved before {gate_code}"
                    )

        can_transition = len(blocking_issues) == 0 and all(
            g in passed_gates for g in target_gates
        )

        return StageTransitionCheck(
            can_transition=can_transition,
            current_stage=current_stage or "UNKNOWN",
            target_stage=target_stage,
            required_gates=target_gates,
            passed_gates=passed_gates,
            pending_gates=pending_gates,
            blocking_issues=blocking_issues,
        )

    async def get_gate_context_info(
        self,
        project_id: UUID,
        gate_code: str,
    ) -> GateContextInfo:
        """
        Get gate information for context overlay generation.

        Args:
            project_id: Project UUID
            gate_code: Gate code

        Returns:
            GateContextInfo for overlay template
        """
        gate_info = GateContextInfo(
            gate_code=gate_code,
            gate_status="NOT_FOUND",
            stage=GATE_CODE_TO_STAGE.get(gate_code, "UNKNOWN"),
            is_approved=False,
            is_blocking=True,
            readiness_score=0.0,
            prerequisites_met=False,
            missing_prerequisites=[],
            exit_criteria_met=0,
            exit_criteria_total=0,
        )

        if self.gates_engine:
            try:
                summary = await self.gates_engine.get_gate_readiness_summary(project_id)
                gate_data = summary.get("gates", {}).get(gate_code)

                if gate_data:
                    gate_info.gate_status = gate_data.get("status", "NOT_FOUND")
                    gate_info.is_approved = gate_data.get("status") == "APPROVED"
                    gate_info.prerequisites_met = gate_data.get("prerequisites_met", False)
                    gate_info.missing_prerequisites = gate_data.get("missing_prerequisites", [])
                    gate_info.exit_criteria_met = gate_data.get("criteria_met", 0)
                    gate_info.exit_criteria_total = gate_data.get("criteria_total", 0)
                    gate_info.is_blocking = gate_data.get("is_blocked", True)

                    # Calculate readiness
                    if gate_info.exit_criteria_total > 0:
                        gate_info.readiness_score = (
                            gate_info.exit_criteria_met / gate_info.exit_criteria_total
                        ) * 100

            except Exception as e:
                logger.warning(f"Failed to get gate info: {e}")

        return gate_info

    async def generate_gate_aware_overlay(
        self,
        project_id: UUID,
        gate_code: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Generate dynamic overlay content based on gate status.

        Args:
            project_id: Project UUID
            gate_code: Optional specific gate code

        Returns:
            Overlay content dict for AGENTS.md integration
        """
        overlay_sections: List[Dict[str, str]] = []
        restrictions: List[str] = []
        focus_areas: List[str] = []

        if self.gates_engine:
            try:
                summary = await self.gates_engine.get_gate_readiness_summary(project_id)
                current_stage = summary.get("current_stage")
                next_gate = summary.get("next_gate")

                # Add stage context
                if current_stage:
                    overlay_sections.append({
                        "title": "Current Stage",
                        "content": f"Project is in {current_stage} stage.",
                    })

                # Add next gate focus
                if next_gate:
                    gate_info = await self.get_gate_context_info(project_id, next_gate)

                    overlay_sections.append({
                        "title": f"Next Gate: {next_gate}",
                        "content": f"Focus on completing exit criteria ({gate_info.exit_criteria_met}/{gate_info.exit_criteria_total} met)."
                    })

                    # Add missing prerequisites
                    if gate_info.missing_prerequisites:
                        restrictions.append(
                            f"Cannot proceed to {next_gate} - missing gates: {', '.join(gate_info.missing_prerequisites)}"
                        )

                    focus_areas.append(f"Complete {next_gate} exit criteria")

                # Add stage-specific guidance
                stage_guidance = {
                    "WHY": "Focus on problem definition and stakeholder alignment.",
                    "WHAT": "Complete requirements and API design before implementation.",
                    "HOW": "Finalize architecture and get CTO approval.",
                    "BUILD": "Write production code with tests and security scans.",
                    "TEST": "Complete integration and E2E testing.",
                    "DEPLOY": "Prepare staging environment and runbooks.",
                }

                if current_stage and current_stage in stage_guidance:
                    overlay_sections.append({
                        "title": "Stage Guidance",
                        "content": stage_guidance[current_stage],
                    })

            except Exception as e:
                logger.warning(f"Failed to generate overlay: {e}")

        return {
            "sections": overlay_sections,
            "restrictions": restrictions,
            "focus_areas": focus_areas,
            "generated_at": datetime.now(UTC).isoformat(),
        }


# ============================================================================
# Dependency Injection
# ============================================================================


_integration_service: Optional[GatesCAIntegrationService] = None


async def get_gates_ca_integration(
    db: AsyncSession,
    gates_engine: Optional[GatesEngine] = None,
    context_authority_engine: Optional[Any] = None,
) -> GatesCAIntegrationService:
    """
    Get or create integration service.

    Args:
        db: SQLAlchemy async session
        gates_engine: Optional Gates Engine
        context_authority_engine: Optional CA V2 Engine

    Returns:
        GatesCAIntegrationService instance
    """
    global _integration_service

    if _integration_service is None:
        _integration_service = GatesCAIntegrationService(
            db, gates_engine, context_authority_engine
        )

    return _integration_service


def reset_integration_service():
    """Reset the global integration service (for testing)."""
    global _integration_service
    _integration_service = None
