# =========================================================================
# STATUS: FROZEN (Sprint 173, Feb 2026)
# TIER: Enterprise
# REASON: Non-core for current phase. Working code preserved.
# REACTIVATION: CPO approval required.
# DO NOT: Delete, refactor, or add features without CTO approval.
# =========================================================================
"""
=========================================================================
NIST GOVERN Service - NIST AI RMF GOVERN Function
SDLC Orchestrator - Sprint 156 (Phase 3: COMPLIANCE)

Version: 1.0.0
Date: April 7, 2026
Status: ACTIVE
Authority: CTO Approved
Framework: SDLC 6.0.5
Reference: ADR-051, NIST AI RMF 1.0 Section GOVERN

Purpose:
Implements the GOVERN function of the NIST AI Risk Management Framework.
GOVERN establishes organizational AI governance structures:
- GOVERN-1.1: Accountability structures for AI systems
- GOVERN-1.2: Risk culture and team training
- GOVERN-1.3: Legal and regulatory compliance review
- GOVERN-1.4: Third-party risk management
- GOVERN-1.5: Continuous improvement from incidents

Evaluation Strategy:
- Primary: OPA policy evaluation via OPA REST API (network-only, AGPL-safe)
- Fallback: In-process evaluation using identical logic when OPA is unavailable

Performance Targets:
- Evaluate GOVERN: <500ms (p95)
- Dashboard: <200ms (p95)
- List risks: <200ms (p95)
- Risk CRUD: <100ms (p95)

Zero Mock Policy: Production-ready implementation
=========================================================================
"""

import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import UUID

from sqlalchemy import and_, case, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.compliance import (
    IMPACT_VALUES,
    LIKELIHOOD_VALUES,
    ComplianceAssessment,
    ComplianceControl,
    ComplianceFramework,
    ComplianceRACI,
    ComplianceRiskRegister,
    RiskImpact,
    RiskLikelihood,
    RiskStatus,
    calculate_risk_score,
)
from app.schemas.compliance_framework import (
    GovernDashboardResponse,
    GovernEvaluateRequest,
    GovernEvaluateResponse,
    PolicyEvaluationResult,
    RACICreate,
    RACIListResponse,
    RACIResponse,
    RiskCreate,
    RiskListResponse,
    RiskResponse,
    RiskUpdate,
    UserSummary,
)

logger = logging.getLogger(__name__)


# =============================================================================
# Custom Exceptions
# =============================================================================


class NISTGovernServiceError(Exception):
    """Base exception for NIST GOVERN service errors."""

    pass


class NISTGovernNotFoundError(NISTGovernServiceError):
    """Exception raised when a compliance resource is not found."""

    pass


class NISTGovernValidationError(NISTGovernServiceError):
    """Exception raised for input validation failures."""

    pass


class NISTGovernEvaluationError(NISTGovernServiceError):
    """Exception raised when policy evaluation fails."""

    pass


# =============================================================================
# GOVERN Policy Definitions
# =============================================================================

GOVERN_POLICIES = [
    {
        "control_code": "GOVERN-1.1",
        "title": "Accountability Structures",
        "severity": "critical",
        "description": (
            "All AI systems must have designated owners responsible "
            "for system lifecycle management and risk oversight."
        ),
    },
    {
        "control_code": "GOVERN-1.2",
        "title": "Risk Culture & Training",
        "severity": "high",
        "description": (
            "Team members must complete AI risk awareness training "
            "with a minimum 80% completion threshold."
        ),
    },
    {
        "control_code": "GOVERN-1.3",
        "title": "Legal & Regulatory Review",
        "severity": "critical",
        "description": (
            "AI systems must undergo approved legal review by an "
            "identified reviewer before deployment."
        ),
    },
    {
        "control_code": "GOVERN-1.4",
        "title": "Third-Party Risk Management",
        "severity": "high",
        "description": (
            "All third-party AI APIs and services must have "
            "documented SLAs and privacy agreements."
        ),
    },
    {
        "control_code": "GOVERN-1.5",
        "title": "Continuous Improvement",
        "severity": "medium",
        "description": (
            "All AI-related incidents must have completed "
            "postmortems with documented process updates."
        ),
    },
]


# =============================================================================
# NIST GOVERN Service
# =============================================================================


class NISTGovernService:
    """
    Service for NIST AI RMF GOVERN function evaluation and management.

    The GOVERN function establishes and maintains organizational AI
    governance, including accountability, risk culture, legal compliance,
    third-party management, and continuous improvement processes.

    Responsibilities:
        - Evaluate 5 GOVERN controls against project data
        - Manage risk register entries (CRUD)
        - Manage RACI accountability matrix
        - Generate dashboard analytics

    Usage:
        service = NISTGovernService()
        response = await service.evaluate_govern(project_id, request, db)
        dashboard = await service.get_govern_dashboard(project_id, db)

    Evaluation Strategy:
        Primary path attempts OPA REST API evaluation. When OPA is
        unavailable (development, testing, or connectivity issues),
        falls back to in-process evaluation using identical logic.
    """

    # =========================================================================
    # GOVERN Evaluation
    # =========================================================================

    async def evaluate_govern(
        self,
        project_id: UUID,
        request: GovernEvaluateRequest,
        db: AsyncSession,
    ) -> GovernEvaluateResponse:
        """
        Evaluate all 5 NIST GOVERN policies for a project.

        Collects input data from the request and evaluates each GOVERN
        control. Attempts OPA evaluation first, then falls back to
        in-process evaluation if OPA is unavailable.

        Args:
            project_id: UUID of the project being evaluated.
            request: GovernEvaluateRequest containing AI systems data,
                training info, legal review status, third-party APIs,
                and incident postmortem records.
            db: SQLAlchemy async database session.

        Returns:
            GovernEvaluateResponse with per-policy results and overall
            compliance percentage.

        Raises:
            NISTGovernEvaluationError: If both OPA and fallback evaluation
                fail for any policy.

        Example:
            request = GovernEvaluateRequest(
                project_id=project_id,
                ai_systems=[{"name": "chatbot", "owner": "team-lead", "type": "nlp"}],
                team_training={"completion_pct": 85},
                legal_review={"approved": True, "reviewer": "legal-counsel"},
                third_party_apis=[{"name": "openai", "sla_documented": True, "privacy_agreement": True}],
                incident_postmortems=[],
            )
            response = await service.evaluate_govern(project_id, request, db)
        """
        logger.info(
            "Evaluating GOVERN policies for project %s with %d AI systems",
            project_id,
            len(request.ai_systems),
        )

        opa_input = self._build_opa_input(request)
        results: List[PolicyEvaluationResult] = []

        for policy_def in GOVERN_POLICIES:
            control_code = policy_def["control_code"]
            try:
                result = await self._evaluate_single_policy(
                    control_code=control_code,
                    title=policy_def["title"],
                    severity=policy_def["severity"],
                    opa_input=opa_input,
                )
                results.append(result)
            except Exception as exc:
                logger.error(
                    "Evaluation failed for %s on project %s: %s",
                    control_code,
                    project_id,
                    str(exc),
                )
                raise NISTGovernEvaluationError(
                    f"Failed to evaluate {control_code}: {str(exc)}"
                ) from exc

        policies_passed = sum(1 for r in results if r.allowed)
        policies_total = len(results)
        compliance_pct = (
            (policies_passed / policies_total * 100.0) if policies_total > 0 else 0.0
        )

        now = datetime.now(timezone.utc)

        # Persist assessment results to database
        await self._persist_assessment_results(
            project_id=project_id,
            results=results,
            db=db,
        )

        logger.info(
            "GOVERN evaluation complete for project %s: %d/%d passed (%.1f%%)",
            project_id,
            policies_passed,
            policies_total,
            compliance_pct,
        )

        return GovernEvaluateResponse(
            project_id=project_id,
            framework_code="NIST_AI_RMF",
            function="GOVERN",
            overall_compliant=policies_passed == policies_total,
            policies_passed=policies_passed,
            policies_total=policies_total,
            compliance_percentage=round(compliance_pct, 1),
            results=results,
            evaluated_at=now,
        )

    # =========================================================================
    # Dashboard
    # =========================================================================

    async def get_govern_dashboard(
        self,
        project_id: UUID,
        db: AsyncSession,
    ) -> GovernDashboardResponse:
        """
        Get GOVERN function dashboard data for a project.

        Aggregates latest evaluation results, risk summary by severity
        band, and RACI coverage percentage.

        Args:
            project_id: UUID of the project.
            db: SQLAlchemy async database session.

        Returns:
            GovernDashboardResponse with compliance metrics, risk summary,
            and RACI coverage data.

        Example:
            dashboard = await service.get_govern_dashboard(project_id, db)
            print(f"Compliance: {dashboard.compliance_percentage}%")
            print(f"Risks: {dashboard.risk_summary}")
        """
        logger.info("Fetching GOVERN dashboard for project %s", project_id)

        # Fetch latest assessment results for GOVERN controls
        policy_results = await self._fetch_latest_assessments(project_id, db)

        policies_passed = sum(1 for r in policy_results if r.allowed)
        policies_total = len(policy_results) if policy_results else len(GOVERN_POLICIES)
        compliance_pct = (
            (policies_passed / policies_total * 100.0) if policies_total > 0 else 0.0
        )

        # Risk summary by score ranges
        risk_summary = await self._get_risk_summary(project_id, db)
        total_risks = sum(risk_summary.values())

        # RACI coverage
        raci_coverage = await self._get_raci_coverage(project_id, db)

        return GovernDashboardResponse(
            project_id=project_id,
            compliance_percentage=round(compliance_pct, 1),
            policies_passed=policies_passed,
            policies_total=policies_total,
            policy_results=policy_results,
            risk_summary=risk_summary,
            total_risks=total_risks,
            raci_coverage=round(raci_coverage, 1),
            training_completion=None,
        )

    # =========================================================================
    # Risk Register CRUD
    # =========================================================================

    async def list_risks(
        self,
        project_id: UUID,
        framework_id: Optional[UUID],
        status_filter: Optional[RiskStatus],
        limit: int,
        offset: int,
        db: AsyncSession,
    ) -> RiskListResponse:
        """
        List risk register entries for a project with filtering.

        Args:
            project_id: UUID of the project.
            framework_id: Optional framework UUID to filter by.
            status_filter: Optional risk status to filter by.
            limit: Maximum number of results (pagination).
            offset: Number of results to skip (pagination).
            db: SQLAlchemy async database session.

        Returns:
            RiskListResponse with paginated risk entries.

        Example:
            risks = await service.list_risks(
                project_id=project_id,
                framework_id=None,
                status_filter=RiskStatus.IDENTIFIED,
                limit=20,
                offset=0,
                db=db,
            )
        """
        logger.info(
            "Listing risks for project %s (framework=%s, status=%s, limit=%d, offset=%d)",
            project_id,
            framework_id,
            status_filter,
            limit,
            offset,
        )

        conditions = [ComplianceRiskRegister.project_id == project_id]

        if framework_id is not None:
            conditions.append(ComplianceRiskRegister.framework_id == framework_id)

        if status_filter is not None:
            conditions.append(ComplianceRiskRegister.status == status_filter.value)

        # Count total matching
        count_query = select(func.count(ComplianceRiskRegister.id)).where(
            and_(*conditions)
        )
        count_result = await db.execute(count_query)
        total = count_result.scalar() or 0

        # Fetch paginated results ordered by risk_score descending (highest risk first)
        query = (
            select(ComplianceRiskRegister)
            .where(and_(*conditions))
            .order_by(
                ComplianceRiskRegister.risk_score.desc(),
                ComplianceRiskRegister.created_at.desc(),
            )
            .offset(offset)
            .limit(limit)
        )

        result = await db.execute(query)
        risks = result.scalars().all()

        items = [self._risk_to_response(risk) for risk in risks]

        return RiskListResponse(
            items=items,
            total=total,
            limit=limit,
            offset=offset,
            has_more=offset + len(items) < total,
        )

    async def create_risk(
        self,
        data: RiskCreate,
        db: AsyncSession,
    ) -> RiskResponse:
        """
        Create a new risk register entry with auto-calculated risk score.

        Calculates risk_score as LIKELIHOOD_VALUES[likelihood] * IMPACT_VALUES[impact].

        Args:
            data: RiskCreate with risk details including likelihood and impact.
            db: SQLAlchemy async database session.

        Returns:
            RiskResponse with the created risk entry.

        Raises:
            NISTGovernValidationError: If the framework does not exist.

        Example:
            risk = await service.create_risk(
                RiskCreate(
                    project_id=project_id,
                    framework_id=framework_id,
                    risk_code="RISK-001",
                    title="Model bias in hiring decisions",
                    category="fairness",
                    likelihood=RiskLikelihood.LIKELY,
                    impact=RiskImpact.MAJOR,
                ),
                db,
            )
            # risk.risk_score == 16  (4 * 4)
        """
        logger.info(
            "Creating risk '%s' for project %s (likelihood=%s, impact=%s)",
            data.risk_code,
            data.project_id,
            data.likelihood.value,
            data.impact.value,
        )

        # Validate framework exists
        framework_query = select(ComplianceFramework.id).where(
            ComplianceFramework.id == data.framework_id
        )
        framework_result = await db.execute(framework_query)
        if framework_result.scalar_one_or_none() is None:
            raise NISTGovernValidationError(
                f"Compliance framework {data.framework_id} not found"
            )

        # Calculate risk score
        score = calculate_risk_score(data.likelihood, data.impact)

        risk = ComplianceRiskRegister(
            project_id=data.project_id,
            framework_id=data.framework_id,
            risk_code=data.risk_code,
            title=data.title,
            description=data.description,
            likelihood=data.likelihood.value,
            impact=data.impact.value,
            risk_score=score,
            category=data.category,
            mitigation_strategy=data.mitigation_strategy,
            responsible_id=data.responsible_id,
            status=RiskStatus.IDENTIFIED.value,
            target_date=data.target_date,
        )

        db.add(risk)
        await db.commit()
        await db.refresh(risk)

        logger.info(
            "Created risk %s (code=%s, score=%d)",
            risk.id,
            risk.risk_code,
            risk.risk_score,
        )

        return self._risk_to_response(risk)

    async def update_risk(
        self,
        risk_id: UUID,
        data: RiskUpdate,
        db: AsyncSession,
    ) -> RiskResponse:
        """
        Update a risk register entry and recalculate score if needed.

        Recalculates risk_score whenever likelihood or impact is changed.

        Args:
            risk_id: UUID of the risk entry to update.
            data: RiskUpdate with fields to update.
            db: SQLAlchemy async database session.

        Returns:
            RiskResponse with the updated risk entry.

        Raises:
            NISTGovernNotFoundError: If the risk entry does not exist.

        Example:
            updated = await service.update_risk(
                risk_id=risk.id,
                data=RiskUpdate(
                    likelihood=RiskLikelihood.ALMOST_CERTAIN,
                    status=RiskStatus.MITIGATING,
                    mitigation_strategy="Implement bias detection pipeline",
                ),
                db=db,
            )
        """
        logger.info("Updating risk %s", risk_id)

        query = select(ComplianceRiskRegister).where(
            ComplianceRiskRegister.id == risk_id
        )
        result = await db.execute(query)
        risk = result.scalar_one_or_none()

        if risk is None:
            raise NISTGovernNotFoundError(f"Risk {risk_id} not found")

        update_fields = data.model_dump(exclude_unset=True)
        recalculate_score = False

        for field, value in update_fields.items():
            if field == "likelihood":
                risk.likelihood = value.value if isinstance(value, RiskLikelihood) else value
                recalculate_score = True
            elif field == "impact":
                risk.impact = value.value if isinstance(value, RiskImpact) else value
                recalculate_score = True
            elif field == "status":
                risk.status = value.value if isinstance(value, RiskStatus) else value
            elif hasattr(risk, field):
                setattr(risk, field, value)

        if recalculate_score:
            risk.update_risk_score()
            logger.info(
                "Recalculated risk score for %s: %d (likelihood=%s, impact=%s)",
                risk_id,
                risk.risk_score,
                risk.likelihood,
                risk.impact,
            )

        await db.commit()
        await db.refresh(risk)

        logger.info("Updated risk %s (score=%d, status=%s)", risk_id, risk.risk_score, risk.status)

        return self._risk_to_response(risk)

    # =========================================================================
    # RACI Matrix
    # =========================================================================

    async def get_raci(
        self,
        project_id: UUID,
        db: AsyncSession,
    ) -> RACIListResponse:
        """
        Get the full RACI matrix for a project.

        Returns all RACI entries with their associated control information,
        ordered by control sort_order.

        Args:
            project_id: UUID of the project.
            db: SQLAlchemy async database session.

        Returns:
            RACIListResponse with all RACI entries for the project.

        Example:
            raci = await service.get_raci(project_id, db)
            for entry in raci.items:
                print(f"{entry.control.control_code}: R={entry.responsible_id}")
        """
        logger.info("Fetching RACI matrix for project %s", project_id)

        query = (
            select(ComplianceRACI)
            .where(ComplianceRACI.project_id == project_id)
            .order_by(ComplianceRACI.created_at.asc())
        )

        result = await db.execute(query)
        raci_entries = result.scalars().all()

        items: List[RACIResponse] = []
        for entry in raci_entries:
            items.append(await self._raci_to_response(entry, db))

        return RACIListResponse(
            items=items,
            total=len(items),
        )

    async def upsert_raci(
        self,
        data: RACICreate,
        db: AsyncSession,
    ) -> RACIResponse:
        """
        Create or update a RACI entry for a project-control pair.

        If a RACI entry already exists for the given project_id and
        control_id combination, it is updated. Otherwise, a new entry
        is created.

        Args:
            data: RACICreate with project_id, control_id, and role assignments.
            db: SQLAlchemy async database session.

        Returns:
            RACIResponse with the created or updated RACI entry.

        Raises:
            NISTGovernValidationError: If the control does not exist.

        Example:
            raci = await service.upsert_raci(
                RACICreate(
                    project_id=project_id,
                    control_id=control_id,
                    responsible_id=dev_lead_id,
                    accountable_id=cto_id,
                    consulted_ids=[security_lead_id],
                    informed_ids=[pm_id, qa_id],
                ),
                db,
            )
        """
        logger.info(
            "Upserting RACI for project %s, control %s",
            data.project_id,
            data.control_id,
        )

        # Validate control exists
        control_query = select(ComplianceControl.id).where(
            ComplianceControl.id == data.control_id
        )
        control_result = await db.execute(control_query)
        if control_result.scalar_one_or_none() is None:
            raise NISTGovernValidationError(
                f"Compliance control {data.control_id} not found"
            )

        # Check for existing entry
        existing_query = select(ComplianceRACI).where(
            and_(
                ComplianceRACI.project_id == data.project_id,
                ComplianceRACI.control_id == data.control_id,
            )
        )
        existing_result = await db.execute(existing_query)
        existing = existing_result.scalar_one_or_none()

        if existing is not None:
            # Update existing entry
            existing.responsible_id = data.responsible_id
            existing.accountable_id = data.accountable_id
            existing.consulted_ids = data.consulted_ids or []
            existing.informed_ids = data.informed_ids or []

            await db.commit()
            await db.refresh(existing)

            logger.info("Updated existing RACI entry %s", existing.id)
            return await self._raci_to_response(existing, db)

        # Create new entry
        raci = ComplianceRACI(
            project_id=data.project_id,
            control_id=data.control_id,
            responsible_id=data.responsible_id,
            accountable_id=data.accountable_id,
            consulted_ids=data.consulted_ids or [],
            informed_ids=data.informed_ids or [],
        )

        db.add(raci)
        await db.commit()
        await db.refresh(raci)

        logger.info("Created new RACI entry %s", raci.id)

        return await self._raci_to_response(raci, db)

    # =========================================================================
    # Private: OPA Evaluation with In-Process Fallback
    # =========================================================================

    async def _evaluate_single_policy(
        self,
        control_code: str,
        title: str,
        severity: str,
        opa_input: Dict[str, Any],
    ) -> PolicyEvaluationResult:
        """
        Evaluate a single GOVERN policy using OPA with in-process fallback.

        Attempts OPA REST API call first. If OPA is unavailable, falls back
        to in-process evaluation using the same logic as the Rego policies.

        Args:
            control_code: Policy control code (e.g., GOVERN-1.1).
            title: Human-readable policy title.
            severity: Policy severity level.
            opa_input: Structured input data for evaluation.

        Returns:
            PolicyEvaluationResult with pass/fail status and reason.
        """
        try:
            result = await self._evaluate_via_opa(control_code, opa_input)
            if result is not None:
                return result
        except Exception as exc:
            logger.warning(
                "OPA evaluation unavailable for %s, using in-process fallback: %s",
                control_code,
                str(exc),
            )

        # In-process fallback evaluation
        return self._evaluate_in_process(control_code, title, severity, opa_input)

    async def _evaluate_via_opa(
        self,
        control_code: str,
        opa_input: Dict[str, Any],
    ) -> Optional[PolicyEvaluationResult]:
        """
        Attempt policy evaluation via OPA REST API.

        Uses python requests (network-only, AGPL-safe) to call OPA.
        Returns None if OPA is not reachable so the caller can fall back.

        Args:
            control_code: Policy control code.
            opa_input: Structured input for OPA.

        Returns:
            PolicyEvaluationResult if OPA responded, None if unreachable.
        """
        import requests

        policy_path = f"v1/data/nist/govern/{control_code.lower().replace('-', '_')}"
        opa_url = f"{settings.OPA_URL}/{policy_path}"

        try:
            response = requests.post(
                opa_url,
                json={"input": opa_input},
                timeout=5,
            )

            if response.status_code != 200:
                logger.warning(
                    "OPA returned status %d for %s",
                    response.status_code,
                    control_code,
                )
                return None

            opa_result = response.json()
            result_data = opa_result.get("result", {})

            # Extract OPA policy output
            allowed = result_data.get("allow", False)
            reason = result_data.get("reason", "Evaluated by OPA")
            policy_title = result_data.get("title", control_code)
            policy_severity = result_data.get("severity", "medium")

            return PolicyEvaluationResult(
                control_code=control_code,
                title=policy_title,
                allowed=allowed,
                reason=reason,
                severity=policy_severity,
                details={"source": "opa", "raw_result": result_data},
            )

        except requests.exceptions.ConnectionError:
            logger.debug("OPA not reachable at %s", opa_url)
            return None
        except requests.exceptions.Timeout:
            logger.warning("OPA request timed out for %s", control_code)
            return None

    def _evaluate_in_process(
        self,
        control_code: str,
        title: str,
        severity: str,
        opa_input: Dict[str, Any],
    ) -> PolicyEvaluationResult:
        """
        In-process policy evaluation matching Rego policy logic.

        Implements the same decision logic as the OPA Rego policies
        for environments where OPA is not available.

        Args:
            control_code: Policy control code.
            title: Human-readable policy title.
            severity: Policy severity level.
            opa_input: Structured input data.

        Returns:
            PolicyEvaluationResult with pass/fail and reason.
        """
        evaluators = {
            "GOVERN-1.1": self._eval_accountability,
            "GOVERN-1.2": self._eval_risk_culture,
            "GOVERN-1.3": self._eval_legal_review,
            "GOVERN-1.4": self._eval_third_party,
            "GOVERN-1.5": self._eval_continuous_improvement,
        }

        evaluator = evaluators.get(control_code)
        if evaluator is None:
            return PolicyEvaluationResult(
                control_code=control_code,
                title=title,
                allowed=False,
                reason=f"Unknown control code: {control_code}",
                severity=severity,
                details={"source": "in_process", "error": "unknown_control"},
            )

        allowed, reason, details = evaluator(opa_input)

        return PolicyEvaluationResult(
            control_code=control_code,
            title=title,
            allowed=allowed,
            reason=reason,
            severity=severity,
            details={"source": "in_process", **details},
        )

    # =========================================================================
    # Private: Individual Policy Evaluators (In-Process Fallback)
    # =========================================================================

    @staticmethod
    def _eval_accountability(
        opa_input: Dict[str, Any],
    ) -> tuple[bool, str, Dict[str, Any]]:
        """
        GOVERN-1.1: Check all AI systems have non-null/empty owner.

        Args:
            opa_input: Must contain 'ai_systems' list of dicts with 'owner' key.

        Returns:
            Tuple of (allowed, reason, details).
        """
        ai_systems = opa_input.get("ai_systems", [])

        if not ai_systems:
            return (
                False,
                "No AI systems registered. At least one AI system must be documented.",
                {"ai_systems_count": 0, "unowned_systems": []},
            )

        unowned: List[str] = []
        for system in ai_systems:
            owner = system.get("owner")
            if not owner or (isinstance(owner, str) and not owner.strip()):
                system_name = system.get("name", "unnamed")
                unowned.append(system_name)

        if unowned:
            return (
                False,
                f"{len(unowned)} AI system(s) lack designated owner: {', '.join(unowned)}",
                {
                    "ai_systems_count": len(ai_systems),
                    "unowned_systems": unowned,
                },
            )

        return (
            True,
            f"All {len(ai_systems)} AI system(s) have designated owners.",
            {"ai_systems_count": len(ai_systems), "unowned_systems": []},
        )

    @staticmethod
    def _eval_risk_culture(
        opa_input: Dict[str, Any],
    ) -> tuple[bool, str, Dict[str, Any]]:
        """
        GOVERN-1.2: Check team_training.completion_pct >= 80.

        Args:
            opa_input: Must contain 'team_training' dict with 'completion_pct'.

        Returns:
            Tuple of (allowed, reason, details).
        """
        training = opa_input.get("team_training")

        if training is None:
            return (
                False,
                "No training data provided. Team AI risk training is required.",
                {"completion_pct": 0, "threshold": 80},
            )

        completion_pct = training.get("completion_pct", 0)

        if not isinstance(completion_pct, (int, float)):
            return (
                False,
                "Invalid training completion percentage format.",
                {"completion_pct": completion_pct, "threshold": 80},
            )

        if completion_pct < 80:
            return (
                False,
                f"Training completion at {completion_pct}%, minimum 80% required.",
                {"completion_pct": completion_pct, "threshold": 80},
            )

        return (
            True,
            f"Training completion at {completion_pct}% meets the 80% threshold.",
            {"completion_pct": completion_pct, "threshold": 80},
        )

    @staticmethod
    def _eval_legal_review(
        opa_input: Dict[str, Any],
    ) -> tuple[bool, str, Dict[str, Any]]:
        """
        GOVERN-1.3: Check legal_review.approved == true and reviewer exists.

        Args:
            opa_input: Must contain 'legal_review' dict with 'approved' and 'reviewer'.

        Returns:
            Tuple of (allowed, reason, details).
        """
        review = opa_input.get("legal_review")

        if review is None:
            return (
                False,
                "No legal review data provided. Legal review is required before AI deployment.",
                {"approved": False, "reviewer": None},
            )

        approved = review.get("approved", False)
        reviewer = review.get("reviewer")

        if not approved:
            return (
                False,
                "Legal review has not been approved.",
                {"approved": False, "reviewer": reviewer},
            )

        if not reviewer or (isinstance(reviewer, str) and not reviewer.strip()):
            return (
                False,
                "Legal review is approved but no reviewer is identified.",
                {"approved": True, "reviewer": None},
            )

        return (
            True,
            f"Legal review approved by {reviewer}.",
            {"approved": True, "reviewer": reviewer},
        )

    @staticmethod
    def _eval_third_party(
        opa_input: Dict[str, Any],
    ) -> tuple[bool, str, Dict[str, Any]]:
        """
        GOVERN-1.4: Check all third_party_apis have sla_documented and privacy_agreement.

        Args:
            opa_input: Must contain 'third_party_apis' list of dicts.

        Returns:
            Tuple of (allowed, reason, details).
        """
        apis = opa_input.get("third_party_apis", [])

        # No third-party APIs is compliant (nothing to govern)
        if not apis:
            return (
                True,
                "No third-party APIs registered. No third-party risk to manage.",
                {"total_apis": 0, "non_compliant_apis": []},
            )

        non_compliant: List[Dict[str, Any]] = []
        for api in apis:
            api_name = api.get("name", "unnamed")
            sla = api.get("sla_documented", False)
            privacy = api.get("privacy_agreement", False)

            if not sla or not privacy:
                missing: List[str] = []
                if not sla:
                    missing.append("SLA")
                if not privacy:
                    missing.append("privacy agreement")
                non_compliant.append({"name": api_name, "missing": missing})

        if non_compliant:
            names = [nc["name"] for nc in non_compliant]
            return (
                False,
                f"{len(non_compliant)} third-party API(s) lack required documentation: {', '.join(names)}",
                {
                    "total_apis": len(apis),
                    "non_compliant_apis": non_compliant,
                },
            )

        return (
            True,
            f"All {len(apis)} third-party API(s) have documented SLAs and privacy agreements.",
            {"total_apis": len(apis), "non_compliant_apis": []},
        )

    @staticmethod
    def _eval_continuous_improvement(
        opa_input: Dict[str, Any],
    ) -> tuple[bool, str, Dict[str, Any]]:
        """
        GOVERN-1.5: Check all incident_postmortems have postmortem_date and process_updated.

        Args:
            opa_input: Must contain 'incident_postmortems' list of dicts.

        Returns:
            Tuple of (allowed, reason, details).
        """
        postmortems = opa_input.get("incident_postmortems", [])

        # No incidents is compliant
        if not postmortems:
            return (
                True,
                "No incident postmortems recorded. No improvement actions required.",
                {"total_incidents": 0, "incomplete_postmortems": []},
            )

        incomplete: List[Dict[str, Any]] = []
        for idx, pm in enumerate(postmortems):
            postmortem_date = pm.get("postmortem_date")
            process_updated = pm.get("process_updated", False)
            issues: List[str] = []

            if not postmortem_date:
                issues.append("missing postmortem_date")
            if not process_updated:
                issues.append("process_updated is false")

            if issues:
                incomplete.append({
                    "index": idx,
                    "incident_date": pm.get("incident_date"),
                    "issues": issues,
                })

        if incomplete:
            return (
                False,
                f"{len(incomplete)} incident postmortem(s) are incomplete.",
                {
                    "total_incidents": len(postmortems),
                    "incomplete_postmortems": incomplete,
                },
            )

        return (
            True,
            f"All {len(postmortems)} incident postmortem(s) are complete with process updates.",
            {"total_incidents": len(postmortems), "incomplete_postmortems": []},
        )

    # =========================================================================
    # Private: Input Building
    # =========================================================================

    @staticmethod
    def _build_opa_input(request: GovernEvaluateRequest) -> Dict[str, Any]:
        """
        Build structured OPA input from the evaluation request.

        Args:
            request: GovernEvaluateRequest with all input data.

        Returns:
            Dict suitable for OPA input or in-process evaluation.
        """
        return {
            "ai_systems": [
                {
                    "name": s.get("name", "unnamed"),
                    "owner": s.get("owner"),
                    "type": s.get("type", "unknown"),
                }
                for s in request.ai_systems
            ],
            "team_training": request.team_training,
            "legal_review": request.legal_review,
            "third_party_apis": [
                {
                    "name": api.get("name", "unnamed"),
                    "sla_documented": api.get("sla_documented", False),
                    "privacy_agreement": api.get("privacy_agreement", False),
                }
                for api in request.third_party_apis
            ],
            "incident_postmortems": [
                {
                    "incident_date": pm.get("incident_date"),
                    "postmortem_date": pm.get("postmortem_date"),
                    "process_updated": pm.get("process_updated", False),
                }
                for pm in request.incident_postmortems
            ],
        }

    # =========================================================================
    # Private: Assessment Persistence
    # =========================================================================

    async def _persist_assessment_results(
        self,
        project_id: UUID,
        results: List[PolicyEvaluationResult],
        db: AsyncSession,
    ) -> None:
        """
        Persist evaluation results as ComplianceAssessment records.

        Creates or updates assessment records linking the project to
        GOVERN controls based on evaluation results.

        Args:
            project_id: UUID of the evaluated project.
            results: List of policy evaluation results.
            db: SQLAlchemy async database session.
        """
        # Fetch NIST framework
        framework_query = select(ComplianceFramework).where(
            ComplianceFramework.code == "NIST_AI_RMF"
        )
        framework_result = await db.execute(framework_query)
        framework = framework_result.scalar_one_or_none()

        if framework is None:
            logger.warning(
                "NIST_AI_RMF framework not found in database; "
                "skipping assessment persistence for project %s",
                project_id,
            )
            return

        # Fetch GOVERN controls for this framework
        controls_query = select(ComplianceControl).where(
            and_(
                ComplianceControl.framework_id == framework.id,
                ComplianceControl.category == "GOVERN",
            )
        )
        controls_result = await db.execute(controls_query)
        controls = {c.control_code: c for c in controls_result.scalars().all()}

        now = datetime.now(timezone.utc)

        for policy_result in results:
            control = controls.get(policy_result.control_code)
            if control is None:
                logger.debug(
                    "Control %s not found in database; skipping persistence",
                    policy_result.control_code,
                )
                continue

            # Upsert assessment
            assessment_query = select(ComplianceAssessment).where(
                and_(
                    ComplianceAssessment.project_id == project_id,
                    ComplianceAssessment.control_id == control.id,
                )
            )
            assessment_result = await db.execute(assessment_query)
            assessment = assessment_result.scalar_one_or_none()

            status = "compliant" if policy_result.allowed else "non_compliant"

            if assessment is not None:
                assessment.status = status
                assessment.auto_evaluated = True
                assessment.opa_result = policy_result.details
                assessment.assessed_at = now
                assessment.notes = policy_result.reason
            else:
                assessment = ComplianceAssessment(
                    project_id=project_id,
                    control_id=control.id,
                    status=status,
                    auto_evaluated=True,
                    opa_result=policy_result.details,
                    assessed_at=now,
                    notes=policy_result.reason,
                )
                db.add(assessment)

        await db.commit()

        logger.info(
            "Persisted %d assessment results for project %s",
            len(results),
            project_id,
        )

    # =========================================================================
    # Private: Fetch Latest Assessments
    # =========================================================================

    async def _fetch_latest_assessments(
        self,
        project_id: UUID,
        db: AsyncSession,
    ) -> List[PolicyEvaluationResult]:
        """
        Fetch the latest GOVERN assessment results from the database.

        Args:
            project_id: UUID of the project.
            db: SQLAlchemy async database session.

        Returns:
            List of PolicyEvaluationResult from stored assessments.
            Returns empty list if no assessments exist.
        """
        # Fetch NIST framework
        framework_query = select(ComplianceFramework).where(
            ComplianceFramework.code == "NIST_AI_RMF"
        )
        framework_result = await db.execute(framework_query)
        framework = framework_result.scalar_one_or_none()

        if framework is None:
            logger.debug("NIST_AI_RMF framework not found; returning empty results")
            return []

        # Fetch GOVERN controls
        controls_query = (
            select(ComplianceControl)
            .where(
                and_(
                    ComplianceControl.framework_id == framework.id,
                    ComplianceControl.category == "GOVERN",
                )
            )
            .order_by(ComplianceControl.sort_order.asc())
        )
        controls_result = await db.execute(controls_query)
        controls = controls_result.scalars().all()

        if not controls:
            return []

        control_ids = [c.id for c in controls]
        control_map = {c.id: c for c in controls}

        # Fetch assessments for these controls
        assessments_query = select(ComplianceAssessment).where(
            and_(
                ComplianceAssessment.project_id == project_id,
                ComplianceAssessment.control_id.in_(control_ids),
            )
        )
        assessments_result = await db.execute(assessments_query)
        assessments = {a.control_id: a for a in assessments_result.scalars().all()}

        results: List[PolicyEvaluationResult] = []
        for control in controls:
            assessment = assessments.get(control.id)
            if assessment is not None:
                results.append(
                    PolicyEvaluationResult(
                        control_code=control.control_code,
                        title=control.title,
                        allowed=assessment.status == "compliant",
                        reason=assessment.notes or "",
                        severity=control.severity,
                        details=assessment.opa_result or {},
                    )
                )
            else:
                results.append(
                    PolicyEvaluationResult(
                        control_code=control.control_code,
                        title=control.title,
                        allowed=False,
                        reason="Not yet evaluated",
                        severity=control.severity,
                        details={},
                    )
                )

        return results

    # =========================================================================
    # Private: Risk Summary
    # =========================================================================

    async def _get_risk_summary(
        self,
        project_id: UUID,
        db: AsyncSession,
    ) -> Dict[str, int]:
        """
        Get risk count by severity band for a project.

        Risk score ranges:
        - low: 1-4
        - medium: 5-9
        - high: 10-15
        - critical: 16-25

        Args:
            project_id: UUID of the project.
            db: SQLAlchemy async database session.

        Returns:
            Dict with keys 'low', 'medium', 'high', 'critical' and counts.
        """
        query = select(
            func.sum(
                case(
                    (ComplianceRiskRegister.risk_score.between(1, 4), 1),
                    else_=0,
                )
            ).label("low"),
            func.sum(
                case(
                    (ComplianceRiskRegister.risk_score.between(5, 9), 1),
                    else_=0,
                )
            ).label("medium"),
            func.sum(
                case(
                    (ComplianceRiskRegister.risk_score.between(10, 15), 1),
                    else_=0,
                )
            ).label("high"),
            func.sum(
                case(
                    (ComplianceRiskRegister.risk_score.between(16, 25), 1),
                    else_=0,
                )
            ).label("critical"),
        ).where(
            ComplianceRiskRegister.project_id == project_id
        )

        result = await db.execute(query)
        row = result.one()

        return {
            "low": row.low or 0,
            "medium": row.medium or 0,
            "high": row.high or 0,
            "critical": row.critical or 0,
        }

    # =========================================================================
    # Private: RACI Coverage
    # =========================================================================

    async def _get_raci_coverage(
        self,
        project_id: UUID,
        db: AsyncSession,
    ) -> float:
        """
        Calculate RACI coverage percentage for GOVERN controls.

        Coverage = (controls with RACI assigned / total GOVERN controls) * 100.

        Args:
            project_id: UUID of the project.
            db: SQLAlchemy async database session.

        Returns:
            Coverage percentage (0.0 - 100.0).
        """
        # Fetch NIST framework
        framework_query = select(ComplianceFramework).where(
            ComplianceFramework.code == "NIST_AI_RMF"
        )
        framework_result = await db.execute(framework_query)
        framework = framework_result.scalar_one_or_none()

        if framework is None:
            return 0.0

        # Count total GOVERN controls
        total_query = select(func.count(ComplianceControl.id)).where(
            and_(
                ComplianceControl.framework_id == framework.id,
                ComplianceControl.category == "GOVERN",
            )
        )
        total_result = await db.execute(total_query)
        total_controls = total_result.scalar() or 0

        if total_controls == 0:
            return 0.0

        # Count GOVERN controls that have RACI entries for this project
        govern_control_ids_query = select(ComplianceControl.id).where(
            and_(
                ComplianceControl.framework_id == framework.id,
                ComplianceControl.category == "GOVERN",
            )
        )

        raci_count_query = select(
            func.count(func.distinct(ComplianceRACI.control_id))
        ).where(
            and_(
                ComplianceRACI.project_id == project_id,
                ComplianceRACI.control_id.in_(govern_control_ids_query),
            )
        )
        raci_result = await db.execute(raci_count_query)
        raci_count = raci_result.scalar() or 0

        return (raci_count / total_controls) * 100.0

    # =========================================================================
    # Private: Response Builders
    # =========================================================================

    @staticmethod
    def _risk_level_from_score(score: int) -> str:
        """
        Determine risk level string from numeric score.

        Args:
            score: Risk score (1-25).

        Returns:
            Risk level: 'low', 'medium', 'high', or 'critical'.
        """
        if score >= 16:
            return "critical"
        if score >= 10:
            return "high"
        if score >= 5:
            return "medium"
        return "low"

    def _risk_to_response(self, risk: ComplianceRiskRegister) -> RiskResponse:
        """
        Convert a ComplianceRiskRegister model to RiskResponse schema.

        Args:
            risk: Database model instance.

        Returns:
            RiskResponse with computed risk_level.
        """
        responsible_summary = None
        if hasattr(risk, "responsible") and risk.responsible is not None:
            responsible_summary = UserSummary(
                id=risk.responsible.id,
                name=risk.responsible.full_name or risk.responsible.email,
                email=risk.responsible.email,
            )

        return RiskResponse(
            id=risk.id,
            project_id=risk.project_id,
            framework_id=risk.framework_id,
            risk_code=risk.risk_code,
            title=risk.title,
            description=risk.description,
            likelihood=risk.likelihood,
            impact=risk.impact,
            risk_score=risk.risk_score,
            risk_level=self._risk_level_from_score(risk.risk_score),
            category=risk.category,
            mitigation_strategy=risk.mitigation_strategy,
            responsible_id=risk.responsible_id,
            status=risk.status,
            target_date=risk.target_date,
            created_at=risk.created_at,
            updated_at=risk.updated_at,
            responsible=responsible_summary,
        )

    async def _raci_to_response(
        self,
        raci: ComplianceRACI,
        db: AsyncSession,
    ) -> RACIResponse:
        """
        Convert a ComplianceRACI model to RACIResponse schema.

        Loads related control and user information for the response.

        Args:
            raci: Database model instance.
            db: SQLAlchemy async database session.

        Returns:
            RACIResponse with control and user details.
        """
        from app.models.user import User

        # Control info
        control_response = None
        if hasattr(raci, "control") and raci.control is not None:
            control_response = {
                "id": raci.control.id,
                "framework_id": raci.control.framework_id,
                "control_code": raci.control.control_code,
                "category": raci.control.category,
                "title": raci.control.title,
                "description": raci.control.description,
                "severity": raci.control.severity,
                "gate_mapping": raci.control.gate_mapping,
                "evidence_required": raci.control.evidence_required or [],
                "opa_policy_code": raci.control.opa_policy_code,
                "sort_order": raci.control.sort_order,
                "created_at": raci.control.created_at,
                "updated_at": raci.control.updated_at,
            }

        # Responsible user
        responsible_summary = None
        if hasattr(raci, "responsible") and raci.responsible is not None:
            responsible_summary = UserSummary(
                id=raci.responsible.id,
                name=raci.responsible.full_name or raci.responsible.email,
                email=raci.responsible.email,
            )
        elif raci.responsible_id is not None:
            user = await db.get(User, raci.responsible_id)
            if user is not None:
                responsible_summary = UserSummary(
                    id=user.id,
                    name=user.full_name or user.email,
                    email=user.email,
                )

        # Accountable user
        accountable_summary = None
        if hasattr(raci, "accountable") and raci.accountable is not None:
            accountable_summary = UserSummary(
                id=raci.accountable.id,
                name=raci.accountable.full_name or raci.accountable.email,
                email=raci.accountable.email,
            )
        elif raci.accountable_id is not None:
            user = await db.get(User, raci.accountable_id)
            if user is not None:
                accountable_summary = UserSummary(
                    id=user.id,
                    name=user.full_name or user.email,
                    email=user.email,
                )

        return RACIResponse(
            id=raci.id,
            project_id=raci.project_id,
            control_id=raci.control_id,
            responsible_id=raci.responsible_id,
            accountable_id=raci.accountable_id,
            consulted_ids=raci.consulted_ids or [],
            informed_ids=raci.informed_ids or [],
            created_at=raci.created_at,
            updated_at=raci.updated_at,
            responsible=responsible_summary,
            accountable=accountable_summary,
        )
