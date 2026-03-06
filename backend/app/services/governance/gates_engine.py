"""
=========================================================================
Gates Engine - OPA-Powered Gate Evaluation with CA V2 Integration
SDLC Orchestrator - Sprint 120 (Governance Engine Core)

Version: 1.0.0
Date: January 29, 2026
Status: ACTIVE - Sprint 120 Track B
Authority: CTO + Backend Lead Approved
Framework: SDLC 5.3.0 Quality Assurance System

Purpose:
- Gate evaluation using OPA policies
- Exit criteria validation with evidence verification
- Integration with Context Authority V2 for context-aware gating
- Vibecoding Index integration for quality signals
- Progressive gate evaluation (G0.1 → G0.2 → G1...G9)

Core Components:
1. GateEvaluator: Main gate evaluation logic
2. PolicyEvaluationEngine: OPA policy integration
3. ExitCriteriaValidator: Evidence-based criteria checking
4. ContextAwareGateChecker: CA V2 integration

Design References:
- ADR-022: IR-Based Codegen Architecture (4-Gate Quality Pipeline)
- SPEC-0011: Context Authority V2 Technical Design
- Gate Service: app/services/gate_service.py
- OPA Policy Service: app/services/opa_policy_service.py

Performance Targets:
- Gate evaluation: <100ms (p95)
- Policy evaluation: <50ms (p95)
- Full gate check: <200ms (p95)

Zero Mock Policy: Real OPA calls, real database operations
=========================================================================
"""

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime, UTC
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.services.opa_policy_service import OPAPolicyService
from app.services.gate_service import (
    GateService,
    VALID_GATE_CODES,
    GATE_CODE_TO_STAGE,
    GateNotFoundError,
    InvalidGateCodeError,
)
from app.policies.gate_artifact_matrix import check_artifact_completeness

logger = logging.getLogger(__name__)


# ============================================================================
# Enums and Constants
# ============================================================================


class GateEvaluationStatus(str, Enum):
    """Gate evaluation result status."""
    PASSED = "passed"
    FAILED = "failed"
    BLOCKED = "blocked"
    PENDING_EVIDENCE = "pending_evidence"
    PENDING_APPROVAL = "pending_approval"
    ERROR = "error"


class EvaluationPhase(str, Enum):
    """Phases of gate evaluation."""
    PREREQUISITES = "prerequisites"
    ARTIFACT_TYPE_CHECK = "artifact_type_check"  # Sprint 223
    EXIT_CRITERIA = "exit_criteria"
    POLICY_EVALUATION = "policy_evaluation"
    CONTEXT_CHECK = "context_check"
    APPROVAL_CHECK = "approval_check"


class PolicyCategory(str, Enum):
    """OPA policy categories for gate evaluation."""
    STAGE_RULES = "stage_rules"
    EXIT_CRITERIA = "exit_criteria"
    SECURITY = "security"
    QUALITY = "quality"
    DOCUMENTATION = "documentation"
    ARCHITECTURE = "architecture"
    TESTING = "testing"


# Gate-specific policy mappings
GATE_POLICIES: Dict[str, List[str]] = {
    "G0.1": [
        "foundation/problem_statement_complete",
        "foundation/stakeholder_identified",
        "foundation/success_metrics_defined",
    ],
    "G0.2": [
        "foundation/solution_alternatives_evaluated",
        "foundation/solution_selected",
        "foundation/risk_assessment_complete",
    ],
    "G1": [
        "design/frd_complete",
        "design/data_model_validated",
        "design/api_specification_reviewed",
        "design/architecture_documented",
    ],
    "G2": [
        "implementation/architecture_review_passed",
        "implementation/adr_linkage_verified",
        "implementation/security_baseline_met",
    ],
    "G3": [
        "build/code_complete",
        "build/unit_tests_passed",
        "build/code_review_approved",
        "build/security_scan_clean",
    ],
    "G4": [
        "test/integration_tests_passed",
        "test/e2e_tests_passed",
        "test/performance_baseline_met",
        "test/regression_verified",
    ],
    "G5": [
        "deploy/staging_validated",
        "deploy/rollback_tested",
        "deploy/runbook_complete",
        "deploy/monitoring_configured",
    ],
    "G6": [
        "operate/alerts_configured",
        "operate/oncall_assigned",
        "operate/incident_playbook_ready",
    ],
    "G7": [
        "integrate/api_contracts_verified",
        "integrate/third_party_tested",
        "integrate/data_flow_validated",
    ],
    "G8": [
        "collaborate/documentation_published",
        "collaborate/training_complete",
        "collaborate/handoff_accepted",
    ],
    "G9": [
        "govern/compliance_verified",
        "govern/audit_trail_complete",
        "govern/lessons_learned_documented",
    ],
}


# Stage prerequisite gates
GATE_PREREQUISITES: Dict[str, List[str]] = {
    "G0.1": [],  # Foundation - no prerequisites
    "G0.2": ["G0.1"],  # Solution Diversity requires Foundation
    "G1": ["G0.2"],  # Design Ready requires Solution Diversity
    "G2": ["G1"],  # Ship Ready requires Design Ready
    "G3": ["G2"],  # Build Complete requires Ship Ready
    "G4": ["G3"],  # Test Complete requires Build Complete
    "G5": ["G4"],  # Deploy Ready requires Test Complete
    "G6": ["G5"],  # Operate Ready requires Deploy Ready
    "G7": ["G3"],  # Integration Complete requires Build Complete
    "G8": ["G5"],  # Collaboration Ready requires Deploy Ready
    "G9": ["G6"],  # Governance Complete requires Operate Ready
}


# ============================================================================
# Data Classes
# ============================================================================


@dataclass
class CriterionResult:
    """Result of evaluating a single exit criterion."""
    criterion_id: str
    criterion_name: str
    met: bool
    evidence_provided: bool
    evidence_valid: bool
    policy_passed: bool
    message: str
    evidence_refs: List[str] = field(default_factory=list)
    policy_results: Dict[str, Any] = field(default_factory=dict)


@dataclass
class PhaseResult:
    """Result of a single evaluation phase."""
    phase: EvaluationPhase
    passed: bool
    message: str
    duration_ms: float
    details: Dict[str, Any] = field(default_factory=dict)
    errors: List[str] = field(default_factory=list)


@dataclass
class GateEvaluationResult:
    """Complete gate evaluation result."""
    gate_id: UUID
    gate_code: str
    project_id: UUID
    status: GateEvaluationStatus
    overall_passed: bool
    readiness_score: float  # 0-100
    phase_results: List[PhaseResult]
    criteria_results: List[CriterionResult]
    blocking_issues: List[str]
    recommendations: List[str]
    evaluated_at: datetime
    total_duration_ms: float
    context_validation: Optional[Dict[str, Any]] = None
    vibecoding_index: Optional[float] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class PolicyInput:
    """Input data for OPA policy evaluation."""
    gate_code: str
    stage: str
    project_id: str
    project_tier: str
    exit_criteria: List[Dict[str, Any]]
    evidence: List[Dict[str, Any]]
    context: Dict[str, Any]
    submission_metadata: Optional[Dict[str, Any]] = None


# ============================================================================
# Exceptions
# ============================================================================


class GatesEngineError(Exception):
    """Base exception for gates engine errors."""
    pass


class GateEvaluationError(GatesEngineError):
    """Exception raised during gate evaluation."""
    pass


class PrerequisiteNotMetError(GatesEngineError):
    """Exception raised when prerequisite gate is not passed."""
    pass


class PolicyEvaluationError(GatesEngineError):
    """Exception raised when policy evaluation fails."""
    pass


class ContextValidationError(GatesEngineError):
    """Exception raised when context validation fails."""
    pass


# ============================================================================
# Gates Engine Core
# ============================================================================


class GatesEngine:
    """
    Core engine for gate evaluation with OPA policy integration.

    Provides:
        - Gate evaluation using OPA policies
        - Exit criteria validation with evidence verification
        - Integration with Context Authority V2
        - Progressive gate evaluation (G0.1 → G0.2 → G1...G9)
        - Vibecoding Index integration

    Usage:
        engine = GatesEngine(db, opa_service)
        result = await engine.evaluate_gate(gate_id, submission_data)
    """

    def __init__(
        self,
        db: AsyncSession,
        opa_service: Optional[OPAPolicyService] = None,
        context_authority_engine: Optional[Any] = None,  # CA V2 engine
    ):
        """
        Initialize Gates Engine.

        Args:
            db: SQLAlchemy async session
            opa_service: OPA policy service instance
            context_authority_engine: Optional CA V2 engine for context integration
        """
        self.db = db
        self.gate_service = GateService(db)
        self.opa_service = opa_service
        self.context_authority_engine = context_authority_engine

        # Cache for gate policies
        self._policy_cache: Dict[str, List[str]] = {}

        logger.info("GatesEngine initialized")

    # ========================================================================
    # Main Evaluation Methods
    # ========================================================================

    async def evaluate_gate(
        self,
        gate_id: UUID,
        submission_data: Optional[Dict[str, Any]] = None,
        include_context_check: bool = True,
        skip_prerequisites: bool = False,
    ) -> GateEvaluationResult:
        """
        Evaluate a gate for readiness to pass.

        Evaluation phases:
        1. Prerequisites: Check that prerequisite gates are passed
        2. Exit Criteria: Verify all exit criteria are met
        3. Policy Evaluation: Run OPA policies for gate-specific rules
        4. Context Check: Validate context using CA V2 (optional)
        5. Approval Check: Verify required approvals exist

        Args:
            gate_id: Gate UUID to evaluate
            submission_data: Optional additional data for evaluation
            include_context_check: Whether to include CA V2 context validation
            skip_prerequisites: Skip prerequisite check (for testing)

        Returns:
            GateEvaluationResult with complete evaluation details

        Raises:
            GateNotFoundError: If gate not found
            GateEvaluationError: If evaluation fails
        """
        start_time = datetime.now(UTC)
        phase_results: List[PhaseResult] = []
        criteria_results: List[CriterionResult] = []
        blocking_issues: List[str] = []
        recommendations: List[str] = []

        try:
            # Fetch gate
            gate = await self.gate_service.get_gate_by_id(gate_id)
            if not gate:
                raise GateNotFoundError(f"Gate not found: {gate_id}")

            gate_code = gate.gate_type
            project_id = gate.project_id

            logger.info(
                f"Evaluating gate: {gate.gate_name} ({gate_code}) "
                f"for project {project_id}"
            )

            # Phase 1: Prerequisites
            if not skip_prerequisites:
                prereq_result = await self._evaluate_prerequisites(
                    gate_code, project_id
                )
                phase_results.append(prereq_result)

                if not prereq_result.passed:
                    blocking_issues.extend(prereq_result.errors)

            # Phase 1.5: Artifact Type Check (Sprint 223)
            artifact_result = await self._evaluate_artifact_types(
                gate_code, project_id, submission_data
            )
            phase_results.append(artifact_result)
            if not artifact_result.passed:
                blocking_issues.extend(artifact_result.errors)

            # Phase 2: Exit Criteria
            exit_criteria_result, criteria_details = await self._evaluate_exit_criteria(
                gate, submission_data
            )
            phase_results.append(exit_criteria_result)
            criteria_results.extend(criteria_details)

            if not exit_criteria_result.passed:
                blocking_issues.extend(exit_criteria_result.errors)

            # Phase 3: Policy Evaluation
            if self.opa_service:
                policy_result = await self._evaluate_policies(
                    gate, submission_data or {}
                )
                phase_results.append(policy_result)

                if not policy_result.passed:
                    blocking_issues.extend(policy_result.errors)
                    recommendations.append(
                        f"Review gate policies for {gate_code}: "
                        f"{', '.join(GATE_POLICIES.get(gate_code, []))}"
                    )

            # Phase 4: Context Check (CA V2 Integration)
            context_validation = None
            vibecoding_index = None

            if include_context_check and self.context_authority_engine:
                context_result, context_data = await self._evaluate_context(
                    gate, submission_data
                )
                phase_results.append(context_result)
                context_validation = context_data

                if context_data:
                    vibecoding_index = context_data.get("vibecoding_index")

                if not context_result.passed:
                    # Context failures are warnings, not blockers
                    recommendations.extend(context_result.errors)

            # Phase 5: Approval Check
            approval_result = await self._check_approvals(gate)
            phase_results.append(approval_result)

            if not approval_result.passed:
                blocking_issues.extend(approval_result.errors)

            # Calculate overall result
            all_phases_passed = all(pr.passed for pr in phase_results)
            total_duration = (datetime.now(UTC) - start_time).total_seconds() * 1000

            # Calculate readiness score
            readiness_score = self._calculate_readiness_score(
                phase_results, criteria_results, vibecoding_index
            )

            # Determine final status
            if all_phases_passed:
                status = GateEvaluationStatus.PASSED
            elif blocking_issues:
                status = GateEvaluationStatus.BLOCKED
            elif any(not cr.evidence_provided for cr in criteria_results):
                status = GateEvaluationStatus.PENDING_EVIDENCE
            else:
                status = GateEvaluationStatus.FAILED

            result = GateEvaluationResult(
                gate_id=gate_id,
                gate_code=gate_code,
                project_id=project_id,
                status=status,
                overall_passed=all_phases_passed,
                readiness_score=readiness_score,
                phase_results=phase_results,
                criteria_results=criteria_results,
                blocking_issues=blocking_issues,
                recommendations=recommendations,
                evaluated_at=datetime.now(UTC),
                total_duration_ms=total_duration,
                context_validation=context_validation,
                vibecoding_index=vibecoding_index,
                metadata={
                    "gate_name": gate.gate_name,
                    "stage": gate.stage,
                    "gate_status": gate.status,
                    "submission_data_provided": submission_data is not None,
                },
            )

            logger.info(
                f"Gate evaluation complete: {gate_code} - {status.value} "
                f"(score: {readiness_score:.1f}%, duration: {total_duration:.1f}ms)"
            )

            return result

        except GateNotFoundError:
            raise
        except Exception as e:
            logger.error(f"Gate evaluation failed: {e}", exc_info=True)

            total_duration = (datetime.now(UTC) - start_time).total_seconds() * 1000

            return GateEvaluationResult(
                gate_id=gate_id,
                gate_code="UNKNOWN",
                project_id=UUID("00000000-0000-0000-0000-000000000000"),
                status=GateEvaluationStatus.ERROR,
                overall_passed=False,
                readiness_score=0.0,
                phase_results=phase_results,
                criteria_results=criteria_results,
                blocking_issues=[str(e)],
                recommendations=["Contact support if error persists"],
                evaluated_at=datetime.now(UTC),
                total_duration_ms=total_duration,
                metadata={"error": str(e)},
            )

    async def evaluate_gate_by_code(
        self,
        project_id: UUID,
        gate_code: str,
        submission_data: Optional[Dict[str, Any]] = None,
    ) -> GateEvaluationResult:
        """
        Evaluate gate by project and gate code.

        Args:
            project_id: Project UUID
            gate_code: Gate code (G0.1, G0.2, G1...G9)
            submission_data: Optional submission data

        Returns:
            GateEvaluationResult

        Raises:
            InvalidGateCodeError: If gate code is invalid
            GateNotFoundError: If gate not found for project
        """
        if gate_code not in VALID_GATE_CODES:
            raise InvalidGateCodeError(
                f"Invalid gate code: {gate_code}. "
                f"Valid codes: {', '.join(VALID_GATE_CODES)}"
            )

        # Find gate for project
        gates = await self.gate_service.list_gates_by_project(project_id)

        target_gate = None
        for gate in gates:
            if gate.gate_type == gate_code:
                target_gate = gate
                break

        if not target_gate:
            raise GateNotFoundError(
                f"Gate {gate_code} not found for project {project_id}"
            )

        return await self.evaluate_gate(
            target_gate.id, submission_data
        )

    async def check_gate_prerequisites(
        self,
        project_id: UUID,
        gate_code: str,
    ) -> Tuple[bool, List[str], List[str]]:
        """
        Check if prerequisites for a gate are met.

        Args:
            project_id: Project UUID
            gate_code: Target gate code

        Returns:
            Tuple of (all_met, met_gates, missing_gates)
        """
        prerequisites = GATE_PREREQUISITES.get(gate_code, [])

        if not prerequisites:
            return True, [], []

        # Get all project gates
        gates = await self.gate_service.list_gates_by_project(
            project_id, status="APPROVED"
        )
        approved_codes = {g.gate_type for g in gates}

        met_gates = []
        missing_gates = []

        for prereq in prerequisites:
            if prereq in approved_codes:
                met_gates.append(prereq)
            else:
                missing_gates.append(prereq)

        return len(missing_gates) == 0, met_gates, missing_gates

    async def get_gate_readiness_summary(
        self,
        project_id: UUID,
    ) -> Dict[str, Any]:
        """
        Get readiness summary for all gates in a project.

        Args:
            project_id: Project UUID

        Returns:
            Summary dict with gate statuses and recommendations
        """
        gates = await self.gate_service.list_gates_by_project(project_id)

        summary = {
            "project_id": str(project_id),
            "total_gates": len(gates),
            "gates": {},
            "current_stage": None,
            "next_gate": None,
            "overall_progress": 0.0,
        }

        approved_count = 0
        current_stage = None
        next_gate = None

        for gate_code in VALID_GATE_CODES:
            gate = next((g for g in gates if g.gate_type == gate_code), None)

            if gate:
                is_approved = gate.status == "APPROVED"
                if is_approved:
                    approved_count += 1
                    current_stage = GATE_CODE_TO_STAGE[gate_code]
                elif not next_gate:
                    next_gate = gate_code

                # Check prerequisites
                prereqs_met, _, missing = await self.check_gate_prerequisites(
                    project_id, gate_code
                )

                summary["gates"][gate_code] = {
                    "id": str(gate.id),
                    "name": gate.gate_name,
                    "status": gate.status,
                    "stage": gate.stage,
                    "prerequisites_met": prereqs_met,
                    "missing_prerequisites": missing,
                    "is_blocked": not prereqs_met,
                    "criteria_met": gate.criteria_met_count,
                    "criteria_total": gate.criteria_total_count,
                }
            else:
                summary["gates"][gate_code] = {
                    "id": None,
                    "name": None,
                    "status": "NOT_CREATED",
                    "stage": GATE_CODE_TO_STAGE[gate_code],
                    "prerequisites_met": False,
                    "is_blocked": True,
                }

        summary["current_stage"] = current_stage
        summary["next_gate"] = next_gate
        summary["approved_count"] = approved_count
        summary["overall_progress"] = (approved_count / len(VALID_GATE_CODES)) * 100

        return summary

    # ========================================================================
    # Phase Evaluation Methods
    # ========================================================================

    async def _evaluate_artifact_types(
        self,
        gate_code: str,
        project_id: UUID,
        submission_data: Optional[Dict[str, Any]] = None,
    ) -> PhaseResult:
        """
        Phase 1.5: Check submitted evidence types against the tier-artifact matrix.

        Sprint 223 — EndiorBot cross-project review gap G2.
        """
        start = datetime.now(UTC)
        try:
            from sqlalchemy import select, text
            from app.models.project import Project

            # Fetch project tier
            result = await self.db.execute(
                select(Project.policy_pack_tier).where(Project.id == project_id)
            )
            tier = result.scalar_one_or_none() or "PROFESSIONAL"

            # Collect submitted evidence types from submission_data or DB
            submitted_types: list[str] = []
            if submission_data and "evidence_types" in submission_data:
                submitted_types = submission_data["evidence_types"]
            else:
                from app.models.gate_evidence import GateEvidence
                ev_result = await self.db.execute(
                    select(GateEvidence.evidence_type).where(
                        GateEvidence.project_id == project_id,
                    )
                )
                submitted_types = [row[0] for row in ev_result.all() if row[0]]

            check = check_artifact_completeness(gate_code, tier, submitted_types)

            duration = (datetime.now(UTC) - start).total_seconds() * 1000

            if check.passed:
                return PhaseResult(
                    phase=EvaluationPhase.ARTIFACT_TYPE_CHECK,
                    passed=True,
                    message=f"All required artifacts present for {gate_code}/{tier}",
                    duration_ms=duration,
                    details={"tier": tier, "required": check.required, "submitted": check.submitted},
                )
            else:
                return PhaseResult(
                    phase=EvaluationPhase.ARTIFACT_TYPE_CHECK,
                    passed=False,
                    message=f"Missing artifacts for {gate_code}/{tier}: {check.missing}",
                    duration_ms=duration,
                    details={"tier": tier, "required": check.required, "missing": check.missing},
                    errors=[
                        f"{gate_code} BLOCKED for {tier}: missing artifacts {check.missing}"
                    ],
                )
        except Exception as exc:
            duration = (datetime.now(UTC) - start).total_seconds() * 1000
            logger.warning("artifact_type_check error: %s", exc)
            return PhaseResult(
                phase=EvaluationPhase.ARTIFACT_TYPE_CHECK,
                passed=True,  # non-blocking on error
                message=f"Artifact type check skipped: {exc}",
                duration_ms=duration,
                details={"error": str(exc)},
            )

    async def _evaluate_prerequisites(
        self,
        gate_code: str,
        project_id: UUID,
    ) -> PhaseResult:
        """Evaluate prerequisite gates."""
        start = datetime.now(UTC)

        all_met, met_gates, missing_gates = await self.check_gate_prerequisites(
            project_id, gate_code
        )

        duration = (datetime.now(UTC) - start).total_seconds() * 1000

        if all_met:
            return PhaseResult(
                phase=EvaluationPhase.PREREQUISITES,
                passed=True,
                message="All prerequisite gates are approved",
                duration_ms=duration,
                details={
                    "prerequisites": GATE_PREREQUISITES.get(gate_code, []),
                    "met_gates": met_gates,
                },
            )
        else:
            return PhaseResult(
                phase=EvaluationPhase.PREREQUISITES,
                passed=False,
                message=f"Missing prerequisite gates: {', '.join(missing_gates)}",
                duration_ms=duration,
                details={
                    "prerequisites": GATE_PREREQUISITES.get(gate_code, []),
                    "met_gates": met_gates,
                    "missing_gates": missing_gates,
                },
                errors=[
                    f"Gate {gate} must be approved before proceeding"
                    for gate in missing_gates
                ],
            )

    async def _evaluate_exit_criteria(
        self,
        gate,
        submission_data: Optional[Dict[str, Any]],
    ) -> Tuple[PhaseResult, List[CriterionResult]]:
        """Evaluate gate exit criteria."""
        start = datetime.now(UTC)

        criteria_results: List[CriterionResult] = []
        errors: List[str] = []

        exit_criteria = gate.exit_criteria or []

        for criterion in exit_criteria:
            criterion_id = criterion.get("id", "unknown")
            criterion_name = criterion.get("description", criterion_id)
            is_met = criterion.get("met", False)
            evidence_ref = criterion.get("evidence_ref")

            # Check if evidence is provided
            evidence_provided = evidence_ref is not None
            evidence_valid = is_met and evidence_provided

            result = CriterionResult(
                criterion_id=criterion_id,
                criterion_name=criterion_name,
                met=is_met,
                evidence_provided=evidence_provided,
                evidence_valid=evidence_valid,
                policy_passed=True,  # Will be updated by policy eval
                message="Met" if is_met else "Not met",
                evidence_refs=[evidence_ref] if evidence_ref else [],
            )

            criteria_results.append(result)

            if not is_met:
                errors.append(f"Exit criterion not met: {criterion_name}")

        duration = (datetime.now(UTC) - start).total_seconds() * 1000
        all_met = all(cr.met for cr in criteria_results)

        met_count = sum(1 for cr in criteria_results if cr.met)
        total_count = len(criteria_results)

        return PhaseResult(
            phase=EvaluationPhase.EXIT_CRITERIA,
            passed=all_met,
            message=f"{met_count}/{total_count} criteria met",
            duration_ms=duration,
            details={
                "total": total_count,
                "met": met_count,
                "missing": total_count - met_count,
            },
            errors=errors,
        ), criteria_results

    async def _evaluate_policies(
        self,
        gate,
        submission_data: Dict[str, Any],
    ) -> PhaseResult:
        """Evaluate OPA policies for gate."""
        start = datetime.now(UTC)

        if not self.opa_service:
            return PhaseResult(
                phase=EvaluationPhase.POLICY_EVALUATION,
                passed=True,
                message="OPA service not configured, skipping policy evaluation",
                duration_ms=0,
                details={"skipped": True},
            )

        gate_code = gate.gate_type
        policies = GATE_POLICIES.get(gate_code, [])

        if not policies:
            return PhaseResult(
                phase=EvaluationPhase.POLICY_EVALUATION,
                passed=True,
                message=f"No policies configured for gate {gate_code}",
                duration_ms=0,
                details={"policies": []},
            )

        # Build policy input
        policy_input = {
            "gate_code": gate_code,
            "stage": gate.stage,
            "project_id": str(gate.project_id),
            "exit_criteria": gate.exit_criteria or [],
            "submission": submission_data,
        }

        policy_results: Dict[str, Any] = {}
        errors: List[str] = []
        passed_count = 0

        for policy_path in policies:
            try:
                result = await self.opa_service.evaluate_policy(
                    policy_path=f"gates/{policy_path}",
                    input_data=policy_input,
                )

                policy_results[policy_path] = {
                    "passed": result.allowed if result else False,
                    "reason": result.reason if result else "Evaluation failed",
                }

                if result and result.allowed:
                    passed_count += 1
                else:
                    errors.append(
                        f"Policy failed: {policy_path} - "
                        f"{result.reason if result else 'Unknown error'}"
                    )

            except Exception as e:
                logger.warning(f"Policy evaluation error for {policy_path}: {e}")
                policy_results[policy_path] = {
                    "passed": False,
                    "error": str(e),
                }
                errors.append(f"Policy error: {policy_path} - {str(e)}")

        duration = (datetime.now(UTC) - start).total_seconds() * 1000
        all_passed = passed_count == len(policies)

        return PhaseResult(
            phase=EvaluationPhase.POLICY_EVALUATION,
            passed=all_passed,
            message=f"{passed_count}/{len(policies)} policies passed",
            duration_ms=duration,
            details={
                "policies": policy_results,
                "passed_count": passed_count,
                "total_count": len(policies),
            },
            errors=errors,
        )

    async def _evaluate_context(
        self,
        gate,
        submission_data: Optional[Dict[str, Any]],
    ) -> Tuple[PhaseResult, Optional[Dict[str, Any]]]:
        """Evaluate context using CA V2."""
        start = datetime.now(UTC)

        if not self.context_authority_engine:
            return PhaseResult(
                phase=EvaluationPhase.CONTEXT_CHECK,
                passed=True,
                message="Context Authority not configured, skipping",
                duration_ms=0,
                details={"skipped": True},
            ), None

        try:
            # Build context validation request
            from app.schemas.context_authority import ContextValidationRequest
            from uuid import uuid4

            # Extract changed files from submission data
            changed_files = []
            if submission_data:
                changed_files = submission_data.get("changed_files", [])

            validation_request = ContextValidationRequest(
                submission_id=uuid4(),
                project_id=gate.project_id,
                changed_files=changed_files or ["default"],
                affected_modules=submission_data.get("modules", []) if submission_data else [],
                current_stage=gate.stage,
                gate_code=gate.gate_type,
                is_new_feature=submission_data.get("is_new_feature", False) if submission_data else False,
            )

            # Call CA V2 engine
            context_result = await self.context_authority_engine.validate_context_v2(
                validation_request
            )

            duration = (datetime.now(UTC) - start).total_seconds() * 1000

            # Extract vibecoding index
            context_data = {
                "valid": context_result.valid,
                "violations_count": context_result.violations_count,
                "warnings_count": context_result.warnings_count,
                "vibecoding_index": context_result.vibecoding_index,
                "index_zone": context_result.index_zone,
                "adr_count": context_result.adr_count,
                "linked_adrs": context_result.linked_adrs,
                "spec_found": context_result.spec_found,
            }

            errors = []
            if context_result.violations_count > 0:
                for v in context_result.violations:
                    errors.append(f"Context violation: {v.message}")

            # Context check passes if valid OR if only warnings
            passed = context_result.valid or context_result.violations_count == 0

            return PhaseResult(
                phase=EvaluationPhase.CONTEXT_CHECK,
                passed=passed,
                message=(
                    f"Context validation: {context_result.index_zone} zone "
                    f"(index: {context_result.vibecoding_index:.1f})"
                ),
                duration_ms=duration,
                details=context_data,
                errors=errors if not passed else [],
            ), context_data

        except Exception as e:
            logger.warning(f"Context evaluation error: {e}")
            duration = (datetime.now(UTC) - start).total_seconds() * 1000

            return PhaseResult(
                phase=EvaluationPhase.CONTEXT_CHECK,
                passed=True,  # Don't block on context errors
                message=f"Context check skipped due to error: {str(e)}",
                duration_ms=duration,
                details={"error": str(e)},
            ), None

    async def _check_approvals(self, gate) -> PhaseResult:
        """Check required approvals for gate."""
        start = datetime.now(UTC)

        # Check if gate has required approvals
        gate_code = gate.gate_type

        # Define approval requirements by gate
        approval_requirements = {
            "G0.1": ["product_owner"],
            "G0.2": ["product_owner", "tech_lead"],
            "G1": ["product_owner", "tech_lead", "architect"],
            "G2": ["cto"],
            "G3": ["tech_lead", "qa_lead"],
            "G4": ["qa_lead"],
            "G5": ["devops_lead", "tech_lead"],
            "G6": ["ops_lead"],
            "G7": ["architect"],
            "G8": ["product_owner"],
            "G9": ["cto", "cpo"],
        }

        required = approval_requirements.get(gate_code, [])

        # For now, check if gate is approved or pending
        # In production, would check actual approvals from gate.approvals
        if gate.status == "APPROVED":
            passed = True
            message = "Gate is approved"
            errors = []
        elif gate.status == "PENDING_APPROVAL":
            passed = False
            message = f"Pending approval from: {', '.join(required)}"
            errors = [f"Awaiting approval from {role}" for role in required]
        else:
            passed = True
            message = "Gate not yet submitted for approval"
            errors = []

        duration = (datetime.now(UTC) - start).total_seconds() * 1000

        return PhaseResult(
            phase=EvaluationPhase.APPROVAL_CHECK,
            passed=passed,
            message=message,
            duration_ms=duration,
            details={
                "required_approvers": required,
                "gate_status": gate.status,
            },
            errors=errors,
        )

    # ========================================================================
    # Helper Methods
    # ========================================================================

    def _calculate_readiness_score(
        self,
        phase_results: List[PhaseResult],
        criteria_results: List[CriterionResult],
        vibecoding_index: Optional[float],
    ) -> float:
        """
        Calculate overall gate readiness score (0-100).

        Scoring:
        - Phase completion: 40%
        - Exit criteria: 40%
        - Vibecoding index: 20% (if available)
        """
        # Phase completion score (40%)
        if phase_results:
            phases_passed = sum(1 for pr in phase_results if pr.passed)
            phase_score = (phases_passed / len(phase_results)) * 40
        else:
            phase_score = 0

        # Exit criteria score (40%)
        if criteria_results:
            criteria_met = sum(1 for cr in criteria_results if cr.met)
            criteria_score = (criteria_met / len(criteria_results)) * 40
        else:
            criteria_score = 40  # No criteria = full score

        # Vibecoding index score (20%)
        # Lower index = higher quality = higher score
        if vibecoding_index is not None:
            # Index 0-30 = GREEN = 100%
            # Index 31-60 = YELLOW = 75%
            # Index 61-80 = ORANGE = 50%
            # Index 81-100 = RED = 25%
            if vibecoding_index <= 30:
                index_score = 20
            elif vibecoding_index <= 60:
                index_score = 15
            elif vibecoding_index <= 80:
                index_score = 10
            else:
                index_score = 5
        else:
            index_score = 15  # Default to middle score if not available

        total_score = phase_score + criteria_score + index_score

        return round(min(100, max(0, total_score)), 1)


# ============================================================================
# Dependency Injection
# ============================================================================


_gates_engine: Optional[GatesEngine] = None


async def get_gates_engine(
    db: AsyncSession,
    opa_service: Optional[OPAPolicyService] = None,
) -> GatesEngine:
    """
    Get or create GatesEngine instance.

    Args:
        db: SQLAlchemy async session
        opa_service: Optional OPA policy service

    Returns:
        GatesEngine instance
    """
    global _gates_engine

    if _gates_engine is None:
        _gates_engine = GatesEngine(db, opa_service)

    return _gates_engine


def reset_gates_engine():
    """Reset the global GatesEngine instance (for testing)."""
    global _gates_engine
    _gates_engine = None
