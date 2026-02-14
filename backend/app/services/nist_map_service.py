"""
=========================================================================
NIST MAP Service - NIST AI RMF MAP Function
SDLC Orchestrator - Sprint 157 (Phase 3: COMPLIANCE)

Version: 1.0.0
Date: April 14, 2026
Status: ACTIVE
Authority: CTO Approved
Framework: SDLC 6.0.5
Reference: ADR-051, NIST AI RMF 1.0 Section MAP

Purpose:
Implements the MAP function of the NIST AI Risk Management Framework.
MAP establishes AI system context, categorization, and risk impact:
- MAP-1.1: Context establishment (purpose, scope, owner, stakeholders)
- MAP-1.2: Stakeholder identification and engagement
- MAP-2.1: System categorization (risk_tier, data_sensitivity, autonomy)
- MAP-3.2: Risk-impact mapping (dependencies, impact areas, stakeholders)

Sub-function MAP-1.2 and MAP-3.2 are derived checks that verify
presence of data from context_establishment and risk_impact_mapping
respectively, rather than having separate OPA policies.

Evaluation Strategy:
- Primary: OPA policy evaluation via OPA REST API (network-only, AGPL-safe)
- Fallback: In-process evaluation using identical logic when OPA is unavailable

Performance Targets:
- Evaluate MAP: <500ms (p95)
- Dashboard: <200ms (p95)
- List AI systems: <200ms (p95)
- AI system CRUD: <100ms (p95)

Zero Mock Policy: Production-ready implementation
=========================================================================
"""

import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple
from uuid import UUID

from sqlalchemy import and_, case, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.compliance import (
    IMPACT_VALUES,
    LIKELIHOOD_VALUES,
    ComplianceAssessment,
    ComplianceControl,
    ComplianceFramework,
    ComplianceRiskRegister,
    RiskStatus,
    calculate_risk_score,
)
from app.models.nist_map_measure import AIRiskLevel, AISystem
from app.schemas.compliance_framework import PolicyEvaluationResult

logger = logging.getLogger(__name__)


# =============================================================================
# Custom Exceptions
# =============================================================================


class NISTMapServiceError(Exception):
    """Base exception for NIST MAP service errors."""

    pass


class AISystemNotFoundError(NISTMapServiceError):
    """Exception raised when an AI system is not found."""

    pass


class AISystemDuplicateError(NISTMapServiceError):
    """Exception raised when an AI system with the same name already exists."""

    pass


class NISTMapEvaluationError(NISTMapServiceError):
    """Exception raised when MAP policy evaluation fails."""

    pass


# =============================================================================
# MAP Policy Definitions
# =============================================================================

MAP_POLICIES = [
    {
        "control_code": "MAP-1.1",
        "title": "Context Establishment",
        "severity": "critical",
        "description": (
            "All AI systems must have documented purpose, scope, "
            "owner, and identified stakeholders."
        ),
    },
    {
        "control_code": "MAP-1.2",
        "title": "Stakeholder Identification",
        "severity": "high",
        "description": (
            "All AI systems must have identified and documented "
            "stakeholders with defined roles and impact types."
        ),
    },
    {
        "control_code": "MAP-2.1",
        "title": "System Categorization",
        "severity": "critical",
        "description": (
            "All AI systems must have a valid risk tier categorization "
            "(minimal, limited, high, unacceptable)."
        ),
    },
    {
        "control_code": "MAP-3.2",
        "title": "Risk-Impact Mapping",
        "severity": "high",
        "description": (
            "All risks must have documented impact areas and affected "
            "stakeholders. All AI systems must have documented dependencies."
        ),
    },
]

# Valid risk tiers from AIRiskLevel enum
VALID_RISK_TIERS = {
    AIRiskLevel.MINIMAL.value,
    AIRiskLevel.LIMITED.value,
    AIRiskLevel.HIGH.value,
    AIRiskLevel.UNACCEPTABLE.value,
}


# =============================================================================
# NIST MAP Service
# =============================================================================


class NISTMapService:
    """
    Service for NIST AI RMF MAP function evaluation and management.

    The MAP function establishes AI system context, categorization,
    stakeholder identification, and risk-impact mapping for informed
    decision-making about AI system deployment and governance.

    Responsibilities:
        - Evaluate 4 MAP controls (3 via OPA + 2 derived) against project data
        - Manage AI system inventory (CRUD)
        - Generate MAP dashboard analytics
        - Provide risk-impact mappings

    Usage:
        service = NISTMapService()
        response = await service.evaluate_map(db, project_id, request)
        dashboard = await service.get_dashboard(db, project_id)

    Evaluation Strategy:
        Primary path attempts OPA REST API evaluation. When OPA is
        unavailable (development, testing, or connectivity issues),
        falls back to in-process evaluation using identical logic.
    """

    # =========================================================================
    # MAP Evaluation
    # =========================================================================

    async def evaluate_map(
        self,
        db: AsyncSession,
        project_id: UUID,
        request: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Evaluate all MAP policies for a project.

        Performs 3 OPA policy evaluations (context_establishment,
        system_categorization, risk_impact_mapping) and derives 2 additional
        checks for MAP-1.2 (stakeholder presence from context_establishment)
        and MAP-3.2 data presence from risk_impact_mapping.

        Args:
            db: SQLAlchemy async database session.
            project_id: UUID of the project being evaluated.
            request: Dict containing evaluation input data. Expected keys:
                - ai_systems: List of AI system dicts with name, purpose,
                  scope, owner, stakeholders, categorization, dependencies.
                - risks: List of risk dicts with impact_areas, affected_stakeholders.

        Returns:
            Dict with keys: project_id, framework_code, function,
            overall_compliant, policies_passed, policies_total,
            compliance_percentage, results, evaluated_at.

        Raises:
            NISTMapEvaluationError: If both OPA and fallback evaluation
                fail for any policy.

        Example:
            request = {
                "ai_systems": [
                    {
                        "name": "chatbot",
                        "purpose": "Customer support",
                        "scope": "Production",
                        "owner": "team-lead",
                        "stakeholders": [{"role": "user", "name": "customers"}],
                        "categorization": {"risk_tier": "limited"},
                        "dependencies": [{"name": "openai", "type": "api"}],
                    }
                ],
                "risks": [
                    {
                        "impact_areas": ["customer_experience"],
                        "affected_stakeholders": ["customers"],
                    }
                ],
            }
            response = await service.evaluate_map(db, project_id, request)
        """
        ai_systems_input = request.get("ai_systems", [])
        risks_input = request.get("risks", [])

        logger.info(
            "Evaluating MAP policies for project %s with %d AI systems and %d risks",
            project_id,
            len(ai_systems_input),
            len(risks_input),
        )

        opa_input = self._build_opa_input(ai_systems_input, risks_input)
        results: List[PolicyEvaluationResult] = []

        for policy_def in MAP_POLICIES:
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
                raise NISTMapEvaluationError(
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
            "MAP evaluation complete for project %s: %d/%d passed (%.1f%%)",
            project_id,
            policies_passed,
            policies_total,
            compliance_pct,
        )

        return {
            "project_id": project_id,
            "framework_code": "NIST_AI_RMF",
            "function": "MAP",
            "overall_compliant": policies_passed == policies_total,
            "policies_passed": policies_passed,
            "policies_total": policies_total,
            "compliance_percentage": round(compliance_pct, 1),
            "results": [r.model_dump() for r in results],
            "evaluated_at": now.isoformat(),
        }

    # =========================================================================
    # Dashboard
    # =========================================================================

    async def get_dashboard(
        self,
        db: AsyncSession,
        project_id: UUID,
    ) -> Dict[str, Any]:
        """
        Get MAP function dashboard data for a project.

        Aggregates latest evaluation results, AI system inventory stats,
        and risk summary by severity band.

        Args:
            db: SQLAlchemy async database session.
            project_id: UUID of the project.

        Returns:
            Dict with keys: project_id, compliance_percentage,
            policies_passed, policies_total, policy_results,
            ai_system_summary, risk_summary.

        Example:
            dashboard = await service.get_dashboard(db, project_id)
            print(f"Compliance: {dashboard['compliance_percentage']}%")
            print(f"AI Systems: {dashboard['ai_system_summary']}")
        """
        logger.info("Fetching MAP dashboard for project %s", project_id)

        # Fetch latest assessment results for MAP controls
        policy_results = await self._fetch_latest_assessments(project_id, db)

        policies_passed = sum(1 for r in policy_results if r.allowed)
        policies_total = len(policy_results) if policy_results else len(MAP_POLICIES)
        compliance_pct = (
            (policies_passed / policies_total * 100.0) if policies_total > 0 else 0.0
        )

        # AI system summary
        ai_system_summary = await self._get_ai_system_summary(project_id, db)

        # Risk summary by score ranges
        risk_summary = await self._get_risk_summary(project_id, db)
        total_risks = sum(risk_summary.values())

        return {
            "project_id": project_id,
            "compliance_percentage": round(compliance_pct, 1),
            "policies_passed": policies_passed,
            "policies_total": policies_total,
            "policy_results": [r.model_dump() for r in policy_results],
            "ai_system_summary": ai_system_summary,
            "risk_summary": risk_summary,
            "total_risks": total_risks,
        }

    # =========================================================================
    # AI System CRUD
    # =========================================================================

    async def list_ai_systems(
        self,
        db: AsyncSession,
        project_id: UUID,
        skip: int = 0,
        limit: int = 50,
    ) -> Tuple[List[Dict[str, Any]], int]:
        """
        List active AI systems for a project with pagination.

        Args:
            db: SQLAlchemy async database session.
            project_id: UUID of the project.
            skip: Number of records to skip (pagination offset).
            limit: Maximum number of records to return.

        Returns:
            Tuple of (items list as dicts, total_count).

        Example:
            items, total = await service.list_ai_systems(db, project_id, skip=0, limit=20)
            print(f"Showing {len(items)} of {total} AI systems")
        """
        logger.info(
            "Listing AI systems for project %s (skip=%d, limit=%d)",
            project_id,
            skip,
            limit,
        )

        conditions = [
            AISystem.project_id == project_id,
            AISystem.is_active.is_(True),
        ]

        # Count total matching
        count_query = select(func.count(AISystem.id)).where(and_(*conditions))
        count_result = await db.execute(count_query)
        total = count_result.scalar() or 0

        # Fetch paginated results ordered by creation date descending
        query = (
            select(AISystem)
            .where(and_(*conditions))
            .order_by(AISystem.created_at.desc())
            .offset(skip)
            .limit(limit)
        )

        result = await db.execute(query)
        systems = result.scalars().all()

        items = [system.to_dict() for system in systems]

        return items, total

    async def create_ai_system(
        self,
        db: AsyncSession,
        data: Dict[str, Any],
    ) -> AISystem:
        """
        Create a new AI system entry.

        Validates that no active AI system with the same name exists
        within the project before creating.

        Args:
            db: SQLAlchemy async database session.
            data: Dict with AI system data. Required keys: project_id, name,
                system_type. Optional: description, risk_level, purpose,
                scope, stakeholders, dependencies, categorization, owner_id.

        Returns:
            Created AISystem model instance.

        Raises:
            AISystemDuplicateError: If an active AI system with the same name
                already exists in the project.

        Example:
            system = await service.create_ai_system(db, {
                "project_id": project_id,
                "name": "Customer Support Chatbot",
                "system_type": "nlp",
                "risk_level": "limited",
                "purpose": "Automated customer support via chat",
                "scope": "Production - US region",
                "stakeholders": [{"role": "user", "name": "customers"}],
                "dependencies": [{"name": "openai", "type": "api"}],
                "categorization": {"risk_tier": "limited"},
            })
        """
        project_id = data["project_id"]
        name = data["name"]

        logger.info(
            "Creating AI system '%s' for project %s",
            name,
            project_id,
        )

        # Check for duplicate name within the project (active systems only)
        duplicate_query = select(AISystem.id).where(
            and_(
                AISystem.project_id == project_id,
                AISystem.name == name,
                AISystem.is_active.is_(True),
            )
        )
        duplicate_result = await db.execute(duplicate_query)
        if duplicate_result.scalar_one_or_none() is not None:
            raise AISystemDuplicateError(
                f"AI system with name '{name}' already exists in project {project_id}"
            )

        # Build the AI system record
        system = AISystem(
            project_id=project_id,
            name=name,
            description=data.get("description"),
            system_type=data.get("system_type", "generative"),
            risk_level=data.get("risk_level", AIRiskLevel.HIGH.value),
            purpose=data.get("purpose"),
            scope=data.get("scope"),
            stakeholders=data.get("stakeholders", []),
            dependencies=data.get("dependencies", []),
            categorization=data.get("categorization"),
            owner_id=data.get("owner_id"),
            is_active=True,
        )

        db.add(system)
        await db.commit()
        await db.refresh(system)

        logger.info(
            "Created AI system %s (name=%s, type=%s, risk=%s)",
            system.id,
            system.name,
            system.system_type,
            system.risk_level,
        )

        return system

    async def update_ai_system(
        self,
        db: AsyncSession,
        system_id: UUID,
        data: Dict[str, Any],
    ) -> AISystem:
        """
        Update an existing AI system entry.

        Only updates fields that are present and not None in the data dict.

        Args:
            db: SQLAlchemy async database session.
            system_id: UUID of the AI system to update.
            data: Dict with fields to update. Supported keys: name,
                description, system_type, risk_level, purpose, scope,
                stakeholders, dependencies, categorization, owner_id.

        Returns:
            Updated AISystem model instance.

        Raises:
            AISystemNotFoundError: If the AI system does not exist or is
                inactive.

        Example:
            updated = await service.update_ai_system(db, system_id, {
                "risk_level": "high",
                "purpose": "Updated purpose description",
                "stakeholders": [{"role": "user", "name": "customers"}],
            })
        """
        logger.info("Updating AI system %s", system_id)

        query = select(AISystem).where(
            and_(
                AISystem.id == system_id,
                AISystem.is_active.is_(True),
            )
        )
        result = await db.execute(query)
        system = result.scalar_one_or_none()

        if system is None:
            raise AISystemNotFoundError(f"AI system {system_id} not found")

        # Updatable fields
        updatable_fields = {
            "name",
            "description",
            "system_type",
            "risk_level",
            "purpose",
            "scope",
            "stakeholders",
            "dependencies",
            "categorization",
            "owner_id",
        }

        for field, value in data.items():
            if field in updatable_fields and value is not None:
                setattr(system, field, value)

        await db.commit()
        await db.refresh(system)

        logger.info(
            "Updated AI system %s (name=%s, risk=%s)",
            system_id,
            system.name,
            system.risk_level,
        )

        return system

    async def delete_ai_system(
        self,
        db: AsyncSession,
        system_id: UUID,
    ) -> bool:
        """
        Soft-delete an AI system by setting is_active = False.

        Args:
            db: SQLAlchemy async database session.
            system_id: UUID of the AI system to delete.

        Returns:
            True if the system was successfully soft-deleted.

        Raises:
            AISystemNotFoundError: If the AI system does not exist or
                is already inactive.

        Example:
            await service.delete_ai_system(db, system_id)
        """
        logger.info("Soft-deleting AI system %s", system_id)

        query = select(AISystem).where(
            and_(
                AISystem.id == system_id,
                AISystem.is_active.is_(True),
            )
        )
        result = await db.execute(query)
        system = result.scalar_one_or_none()

        if system is None:
            raise AISystemNotFoundError(f"AI system {system_id} not found")

        system.is_active = False

        await db.commit()
        await db.refresh(system)

        logger.info("Soft-deleted AI system %s (name=%s)", system_id, system.name)

        return True

    # =========================================================================
    # Risk-Impact Mappings
    # =========================================================================

    async def get_risk_impacts(
        self,
        db: AsyncSession,
        project_id: UUID,
    ) -> List[Dict[str, Any]]:
        """
        Get structured risk-impact mappings for a project.

        Queries the compliance_risk_register for the project and enriches
        each risk entry with impact_areas and affected_stakeholders derived
        from the risk description and category.

        Args:
            db: SQLAlchemy async database session.
            project_id: UUID of the project.

        Returns:
            List of dicts with keys: risk_id, risk_code, title, category,
            risk_score, risk_level, impact_areas, affected_stakeholders.

        Example:
            impacts = await service.get_risk_impacts(db, project_id)
            for impact in impacts:
                print(f"{impact['risk_code']}: areas={impact['impact_areas']}")
        """
        logger.info("Fetching risk-impact mappings for project %s", project_id)

        query = (
            select(ComplianceRiskRegister)
            .where(ComplianceRiskRegister.project_id == project_id)
            .order_by(
                ComplianceRiskRegister.risk_score.desc(),
                ComplianceRiskRegister.created_at.desc(),
            )
        )

        result = await db.execute(query)
        risks = result.scalars().all()

        mappings: List[Dict[str, Any]] = []
        for risk in risks:
            impact_areas = self._derive_impact_areas(risk.category, risk.description)
            affected_stakeholders = self._derive_affected_stakeholders(
                risk.category, risk.description
            )

            mappings.append({
                "risk_id": str(risk.id),
                "risk_code": risk.risk_code,
                "title": risk.title,
                "category": risk.category,
                "risk_score": risk.risk_score,
                "risk_level": self._risk_level_from_score(risk.risk_score),
                "impact_areas": impact_areas,
                "affected_stakeholders": affected_stakeholders,
                "mitigation_strategy": risk.mitigation_strategy,
                "status": risk.status,
            })

        logger.info(
            "Found %d risk-impact mappings for project %s",
            len(mappings),
            project_id,
        )

        return mappings

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
        Evaluate a single MAP policy using OPA with in-process fallback.

        Attempts OPA REST API call first. If OPA is unavailable, falls back
        to in-process evaluation using the same logic as the Rego policies.

        For MAP-1.2, checks stakeholder data presence from context_establishment.
        For MAP-3.2, checks dependency/risk data from risk_impact_mapping.

        Args:
            control_code: Policy control code (e.g., MAP-1.1).
            title: Human-readable policy title.
            severity: Policy severity level.
            opa_input: Structured input data for evaluation.

        Returns:
            PolicyEvaluationResult with pass/fail status and reason.
        """
        # MAP-1.2 and MAP-3.2 are derived checks, not separate OPA policies
        if control_code == "MAP-1.2":
            return self._evaluate_stakeholder_identification(opa_input, title, severity)
        if control_code == "MAP-3.2":
            return self._evaluate_risk_impact_mapping_derived(opa_input, title, severity)

        # MAP-1.1 and MAP-2.1 use OPA with fallback
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

        Uses httpx for async HTTP calls (network-only, AGPL-safe) to call OPA.
        Returns None if OPA is not reachable so the caller can fall back.

        Args:
            control_code: Policy control code.
            opa_input: Structured input for OPA.

        Returns:
            PolicyEvaluationResult if OPA responded, None if unreachable.
        """
        import httpx

        # Map control codes to OPA policy paths
        policy_name_map = {
            "MAP-1.1": "context_establishment",
            "MAP-2.1": "system_categorization",
        }

        policy_name = policy_name_map.get(control_code)
        if policy_name is None:
            logger.debug("No OPA policy path for %s", control_code)
            return None

        opa_url = (
            f"{settings.OPA_URL}/v1/data/compliance/nist/map/"
            f"{policy_name}/result"
        )

        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.post(
                    opa_url,
                    json={"input": opa_input},
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

        except httpx.ConnectError:
            logger.debug("OPA not reachable at %s", opa_url)
            return None
        except httpx.TimeoutException:
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
            "MAP-1.1": self._evaluate_context_establishment,
            "MAP-2.1": self._evaluate_system_categorization,
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
    def _evaluate_context_establishment(
        opa_input: Dict[str, Any],
    ) -> Tuple[bool, str, Dict[str, Any]]:
        """
        MAP-1.1: Check all AI systems have purpose, scope, owner, and stakeholders.

        Each AI system must have non-empty values for purpose, scope,
        and owner fields, plus at least one stakeholder entry.

        Args:
            opa_input: Must contain 'ai_systems' list of dicts.

        Returns:
            Tuple of (allowed, reason, details).
        """
        ai_systems = opa_input.get("ai_systems", [])

        if not ai_systems:
            return (
                False,
                "No AI systems registered. At least one AI system must be documented for MAP context.",
                {"ai_systems_count": 0, "incomplete_systems": []},
            )

        incomplete: List[Dict[str, Any]] = []
        for system in ai_systems:
            system_name = system.get("name", "unnamed")
            missing: List[str] = []

            purpose = system.get("purpose")
            if not purpose or (isinstance(purpose, str) and not purpose.strip()):
                missing.append("purpose")

            scope = system.get("scope")
            if not scope or (isinstance(scope, str) and not scope.strip()):
                missing.append("scope")

            owner = system.get("owner")
            if not owner or (isinstance(owner, str) and not owner.strip()):
                missing.append("owner")

            stakeholders = system.get("stakeholders", [])
            if not stakeholders:
                missing.append("stakeholders")

            if missing:
                incomplete.append({"name": system_name, "missing": missing})

        if incomplete:
            names = [s["name"] for s in incomplete]
            return (
                False,
                f"{len(incomplete)} AI system(s) have incomplete context: {', '.join(names)}",
                {
                    "ai_systems_count": len(ai_systems),
                    "incomplete_systems": incomplete,
                },
            )

        return (
            True,
            f"All {len(ai_systems)} AI system(s) have complete context (purpose, scope, owner, stakeholders).",
            {"ai_systems_count": len(ai_systems), "incomplete_systems": []},
        )

    @staticmethod
    def _evaluate_system_categorization(
        opa_input: Dict[str, Any],
    ) -> Tuple[bool, str, Dict[str, Any]]:
        """
        MAP-2.1: Check all AI systems have valid categorization.risk_tier.

        Valid risk tiers: minimal, limited, high, unacceptable.

        Args:
            opa_input: Must contain 'ai_systems' list of dicts with
                'categorization' containing 'risk_tier'.

        Returns:
            Tuple of (allowed, reason, details).
        """
        ai_systems = opa_input.get("ai_systems", [])

        if not ai_systems:
            return (
                False,
                "No AI systems registered. At least one AI system must be categorized.",
                {"ai_systems_count": 0, "uncategorized_systems": []},
            )

        uncategorized: List[Dict[str, Any]] = []
        for system in ai_systems:
            system_name = system.get("name", "unnamed")
            categorization = system.get("categorization")

            if categorization is None:
                uncategorized.append({
                    "name": system_name,
                    "issue": "missing categorization",
                })
                continue

            risk_tier = categorization.get("risk_tier")
            if not risk_tier or risk_tier not in VALID_RISK_TIERS:
                uncategorized.append({
                    "name": system_name,
                    "issue": f"invalid risk_tier: {risk_tier}",
                    "valid_tiers": list(VALID_RISK_TIERS),
                })

        if uncategorized:
            names = [s["name"] for s in uncategorized]
            return (
                False,
                f"{len(uncategorized)} AI system(s) lack valid categorization: {', '.join(names)}",
                {
                    "ai_systems_count": len(ai_systems),
                    "uncategorized_systems": uncategorized,
                },
            )

        return (
            True,
            f"All {len(ai_systems)} AI system(s) have valid risk tier categorization.",
            {"ai_systems_count": len(ai_systems), "uncategorized_systems": []},
        )

    @staticmethod
    def _evaluate_risk_impact_mapping(
        opa_input: Dict[str, Any],
    ) -> Tuple[bool, str, Dict[str, Any]]:
        """
        MAP-3.2 core: Check all risks have impact_areas and affected_stakeholders,
        and all AI systems have dependencies.

        Args:
            opa_input: Must contain 'risks' list of dicts and 'ai_systems'
                list of dicts with 'dependencies'.

        Returns:
            Tuple of (allowed, reason, details).
        """
        risks = opa_input.get("risks", [])
        ai_systems = opa_input.get("ai_systems", [])
        issues: List[str] = []
        details: Dict[str, Any] = {
            "risks_count": len(risks),
            "ai_systems_count": len(ai_systems),
        }

        # Check risks have impact_areas and affected_stakeholders
        risks_missing_impact: List[int] = []
        risks_missing_stakeholders: List[int] = []
        for idx, risk in enumerate(risks):
            impact_areas = risk.get("impact_areas", [])
            if not impact_areas:
                risks_missing_impact.append(idx)

            affected = risk.get("affected_stakeholders", [])
            if not affected:
                risks_missing_stakeholders.append(idx)

        if risks_missing_impact:
            issues.append(
                f"{len(risks_missing_impact)} risk(s) missing impact_areas"
            )
            details["risks_missing_impact"] = risks_missing_impact

        if risks_missing_stakeholders:
            issues.append(
                f"{len(risks_missing_stakeholders)} risk(s) missing affected_stakeholders"
            )
            details["risks_missing_stakeholders"] = risks_missing_stakeholders

        # Check AI systems have dependencies documented
        systems_missing_deps: List[str] = []
        for system in ai_systems:
            system_name = system.get("name", "unnamed")
            deps = system.get("dependencies", [])
            if not deps:
                systems_missing_deps.append(system_name)

        if systems_missing_deps:
            issues.append(
                f"{len(systems_missing_deps)} AI system(s) missing dependencies: "
                f"{', '.join(systems_missing_deps)}"
            )
            details["systems_missing_dependencies"] = systems_missing_deps

        if issues:
            return (
                False,
                "Risk-impact mapping incomplete: " + "; ".join(issues),
                details,
            )

        return (
            True,
            f"All {len(risks)} risk(s) and {len(ai_systems)} AI system(s) have complete risk-impact mappings.",
            details,
        )

    # =========================================================================
    # Private: Derived Policy Checks (MAP-1.2, MAP-3.2)
    # =========================================================================

    def _evaluate_stakeholder_identification(
        self,
        opa_input: Dict[str, Any],
        title: str,
        severity: str,
    ) -> PolicyEvaluationResult:
        """
        MAP-1.2: Derived check that all AI systems have stakeholders documented.

        Checks the stakeholders field from the context_establishment data
        to verify each system has at least one stakeholder with role and name.

        Args:
            opa_input: Must contain 'ai_systems' with 'stakeholders' lists.
            title: Policy title.
            severity: Policy severity.

        Returns:
            PolicyEvaluationResult with pass/fail.
        """
        ai_systems = opa_input.get("ai_systems", [])

        if not ai_systems:
            return PolicyEvaluationResult(
                control_code="MAP-1.2",
                title=title,
                allowed=False,
                reason="No AI systems registered. Stakeholder identification requires documented systems.",
                severity=severity,
                details={"source": "derived", "ai_systems_count": 0, "incomplete_systems": []},
            )

        incomplete: List[Dict[str, Any]] = []
        for system in ai_systems:
            system_name = system.get("name", "unnamed")
            stakeholders = system.get("stakeholders", [])

            if not stakeholders:
                incomplete.append({
                    "name": system_name,
                    "issue": "no stakeholders defined",
                })
                continue

            # Validate each stakeholder has role and name
            invalid_stakeholders = []
            for idx, sh in enumerate(stakeholders):
                role = sh.get("role")
                name = sh.get("name")
                if not role or not name:
                    missing = []
                    if not role:
                        missing.append("role")
                    if not name:
                        missing.append("name")
                    invalid_stakeholders.append({"index": idx, "missing": missing})

            if invalid_stakeholders:
                incomplete.append({
                    "name": system_name,
                    "issue": "incomplete stakeholder entries",
                    "invalid_stakeholders": invalid_stakeholders,
                })

        if incomplete:
            names = [s["name"] for s in incomplete]
            return PolicyEvaluationResult(
                control_code="MAP-1.2",
                title=title,
                allowed=False,
                reason=f"{len(incomplete)} AI system(s) have incomplete stakeholder identification: {', '.join(names)}",
                severity=severity,
                details={
                    "source": "derived",
                    "ai_systems_count": len(ai_systems),
                    "incomplete_systems": incomplete,
                },
            )

        return PolicyEvaluationResult(
            control_code="MAP-1.2",
            title=title,
            allowed=True,
            reason=f"All {len(ai_systems)} AI system(s) have complete stakeholder identification.",
            severity=severity,
            details={
                "source": "derived",
                "ai_systems_count": len(ai_systems),
                "incomplete_systems": [],
            },
        )

    def _evaluate_risk_impact_mapping_derived(
        self,
        opa_input: Dict[str, Any],
        title: str,
        severity: str,
    ) -> PolicyEvaluationResult:
        """
        MAP-3.2: Derived check combining risk_impact_mapping data.

        Delegates to _evaluate_risk_impact_mapping for the core logic
        and wraps the result in a PolicyEvaluationResult.

        Args:
            opa_input: Must contain 'risks' and 'ai_systems'.
            title: Policy title.
            severity: Policy severity.

        Returns:
            PolicyEvaluationResult with pass/fail.
        """
        allowed, reason, details = self._evaluate_risk_impact_mapping(opa_input)

        return PolicyEvaluationResult(
            control_code="MAP-3.2",
            title=title,
            allowed=allowed,
            reason=reason,
            severity=severity,
            details={"source": "derived", **details},
        )

    # =========================================================================
    # Private: Input Building
    # =========================================================================

    @staticmethod
    def _build_opa_input(
        ai_systems: List[Dict[str, Any]],
        risks: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """
        Build structured OPA input from the evaluation request data.

        Args:
            ai_systems: List of AI system dicts from the request.
            risks: List of risk dicts from the request.

        Returns:
            Dict suitable for OPA input or in-process evaluation.
        """
        return {
            "ai_systems": [
                {
                    "name": s.get("name", "unnamed"),
                    "purpose": s.get("purpose"),
                    "scope": s.get("scope"),
                    "owner": s.get("owner"),
                    "stakeholders": s.get("stakeholders", []),
                    "categorization": s.get("categorization"),
                    "dependencies": s.get("dependencies", []),
                    "system_type": s.get("system_type", "unknown"),
                }
                for s in ai_systems
            ],
            "risks": [
                {
                    "impact_areas": r.get("impact_areas", []),
                    "affected_stakeholders": r.get("affected_stakeholders", []),
                    "category": r.get("category"),
                    "title": r.get("title"),
                }
                for r in risks
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
        MAP controls based on evaluation results.

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

        # Fetch MAP controls for this framework
        controls_query = select(ComplianceControl).where(
            and_(
                ComplianceControl.framework_id == framework.id,
                ComplianceControl.category == "MAP",
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
            "Persisted %d MAP assessment results for project %s",
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
        Fetch the latest MAP assessment results from the database.

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

        # Fetch MAP controls
        controls_query = (
            select(ComplianceControl)
            .where(
                and_(
                    ComplianceControl.framework_id == framework.id,
                    ComplianceControl.category == "MAP",
                )
            )
            .order_by(ComplianceControl.sort_order.asc())
        )
        controls_result = await db.execute(controls_query)
        controls = controls_result.scalars().all()

        if not controls:
            return []

        control_ids = [c.id for c in controls]

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
    # Private: AI System Summary
    # =========================================================================

    async def _get_ai_system_summary(
        self,
        project_id: UUID,
        db: AsyncSession,
    ) -> Dict[str, Any]:
        """
        Get summary stats for active AI systems in a project.

        Counts total active systems, systems by risk level, and systems
        by type for the dashboard.

        Args:
            project_id: UUID of the project.
            db: SQLAlchemy async database session.

        Returns:
            Dict with total_systems, by_risk_level, and by_type.
        """
        conditions = [
            AISystem.project_id == project_id,
            AISystem.is_active.is_(True),
        ]

        # Total count
        total_query = select(func.count(AISystem.id)).where(and_(*conditions))
        total_result = await db.execute(total_query)
        total_systems = total_result.scalar() or 0

        # Count by risk level
        risk_level_query = select(
            AISystem.risk_level,
            func.count(AISystem.id).label("count"),
        ).where(
            and_(*conditions)
        ).group_by(AISystem.risk_level)

        risk_result = await db.execute(risk_level_query)
        by_risk_level = {row.risk_level: row.count for row in risk_result.all()}

        # Count by system type
        type_query = select(
            AISystem.system_type,
            func.count(AISystem.id).label("count"),
        ).where(
            and_(*conditions)
        ).group_by(AISystem.system_type)

        type_result = await db.execute(type_query)
        by_type = {row.system_type: row.count for row in type_result.all()}

        return {
            "total_systems": total_systems,
            "by_risk_level": by_risk_level,
            "by_type": by_type,
        }

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
    # Private: Utility Methods
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

    @staticmethod
    def _derive_impact_areas(
        category: Optional[str],
        description: Optional[str],
    ) -> List[str]:
        """
        Derive impact areas from risk category and description.

        Maps risk categories to standard impact areas following
        NIST AI RMF taxonomy for AI system impacts.

        Args:
            category: Risk category (safety, fairness, privacy, etc.).
            description: Risk description text.

        Returns:
            List of impact area strings.
        """
        category_impact_map = {
            "safety": ["human_safety", "physical_harm", "operational_disruption"],
            "fairness": ["discrimination", "social_equity", "user_trust"],
            "privacy": ["data_breach", "personal_information", "regulatory_compliance"],
            "security": ["system_integrity", "data_confidentiality", "availability"],
            "reliability": ["service_availability", "accuracy_degradation", "operational_continuity"],
            "transparency": ["explainability", "user_understanding", "audit_capability"],
            "accountability": ["governance_gap", "liability", "regulatory_exposure"],
        }

        areas: List[str] = []
        if category:
            areas.extend(category_impact_map.get(category.lower().strip(), []))

        # Extract additional areas from description keywords
        if description:
            desc_lower = description.lower()
            keyword_area_map = {
                "financial": "financial_impact",
                "reputation": "reputational_damage",
                "legal": "legal_liability",
                "customer": "customer_impact",
                "employee": "employee_impact",
                "compliance": "regulatory_compliance",
            }
            for keyword, area in keyword_area_map.items():
                if keyword in desc_lower and area not in areas:
                    areas.append(area)

        # Ensure at least one generic area if none matched
        if not areas:
            areas.append("general_operational_impact")

        return areas

    @staticmethod
    def _derive_affected_stakeholders(
        category: Optional[str],
        description: Optional[str],
    ) -> List[str]:
        """
        Derive affected stakeholders from risk category and description.

        Maps risk categories to typical stakeholder groups affected
        by that risk type.

        Args:
            category: Risk category (safety, fairness, privacy, etc.).
            description: Risk description text.

        Returns:
            List of affected stakeholder strings.
        """
        category_stakeholder_map = {
            "safety": ["end_users", "operators", "safety_team"],
            "fairness": ["end_users", "affected_communities", "compliance_team"],
            "privacy": ["data_subjects", "privacy_officer", "legal_team"],
            "security": ["system_administrators", "security_team", "end_users"],
            "reliability": ["end_users", "operations_team", "support_team"],
            "transparency": ["end_users", "regulators", "audit_team"],
            "accountability": ["executive_leadership", "legal_team", "regulators"],
        }

        stakeholders: List[str] = []
        if category:
            stakeholders.extend(
                category_stakeholder_map.get(category.lower().strip(), [])
            )

        # Extract additional stakeholders from description keywords
        if description:
            desc_lower = description.lower()
            keyword_stakeholder_map = {
                "customer": "customers",
                "partner": "business_partners",
                "vendor": "vendors",
                "regulator": "regulators",
                "investor": "investors",
                "public": "general_public",
            }
            for keyword, stakeholder in keyword_stakeholder_map.items():
                if keyword in desc_lower and stakeholder not in stakeholders:
                    stakeholders.append(stakeholder)

        # Ensure at least one generic stakeholder if none matched
        if not stakeholders:
            stakeholders.append("project_stakeholders")

        return stakeholders
