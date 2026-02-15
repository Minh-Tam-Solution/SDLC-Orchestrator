# =========================================================================
# STATUS: FROZEN (Sprint 173, Feb 2026)
# TIER: Enterprise
# REASON: Non-core for current phase. Working code preserved.
# REACTIVATION: CPO approval required.
# DO NOT: Delete, refactor, or add features without CTO approval.
# =========================================================================
"""
=========================================================================
NIST MANAGE Service - NIST AI RMF MANAGE Function
SDLC Orchestrator - Sprint 158 (Phase 3: COMPLIANCE)

Version: 1.0.0
Date: April 21, 2026
Status: ACTIVE
Authority: CTO Approved
Framework: SDLC 6.0.5
Reference: ADR-051, NIST AI RMF 1.0 Section MANAGE

Purpose:
Implements the MANAGE function of the NIST AI Risk Management Framework.
MANAGE establishes risk response, resource allocation, deactivation, and
post-deployment monitoring:
- MANAGE-1.1: Risk Response Planning (critical) - OPA
- MANAGE-2.1: Resource Allocation (high) - OPA
- MANAGE-2.4: System Deactivation Criteria (high) - IN-PROCESS ONLY
- MANAGE-3.1: Third-Party Monitoring (high) - OPA
- MANAGE-4.1: Post-Deployment Monitoring (critical) - OPA (hybrid SQL)

Evaluation Strategy:
- Primary: OPA policy evaluation via OPA REST API (network-only, AGPL-safe)
- Fallback: In-process evaluation using identical logic when OPA unavailable
- MANAGE-2.4: Always in-process (no OPA policy defined)

Performance Targets:
- Evaluate MANAGE: <500ms (p95)
- Dashboard: <200ms (p95)
- List risk responses: <200ms (p95)
- Risk response CRUD: <100ms (p95)
- Incident CRUD: <100ms (p95)

Zero Mock Policy: Production-ready implementation
=========================================================================
"""

import logging
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Tuple
from uuid import UUID

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.compliance import (
    ComplianceAssessment,
    ComplianceControl,
    ComplianceFramework,
    ComplianceRiskRegister,
    RiskStatus,
)
from app.models.nist_manage import (
    IncidentSeverity,
    IncidentStatus,
    ManageIncident,
    ManageRiskResponse,
    ResponseStatus,
    ResponseType,
)
from app.models.nist_map_measure import AISystem, PerformanceMetric
from app.schemas.compliance_framework import PolicyEvaluationResult

logger = logging.getLogger(__name__)


# =============================================================================
# Custom Exceptions
# =============================================================================


class NISTManageServiceError(Exception):
    """Base exception for NIST MANAGE service errors."""

    pass


class NISTManageEvaluationError(NISTManageServiceError):
    """Exception raised when MANAGE policy evaluation fails."""

    pass


class RiskResponseNotFoundError(NISTManageServiceError):
    """Exception raised when a risk response is not found."""

    pass


class IncidentNotFoundError(NISTManageServiceError):
    """Exception raised when an incident is not found."""

    pass


# =============================================================================
# MANAGE Policy Definitions
# =============================================================================

MANAGE_POLICIES = [
    {
        "control_code": "MANAGE-1.1",
        "title": "Risk Response Planning",
        "severity": "critical",
        "opa_policy": "risk_response_planning",
        "description": (
            "Every open risk must have at least one response plan "
            "with an assigned owner and due date."
        ),
    },
    {
        "control_code": "MANAGE-2.1",
        "title": "Resource Allocation",
        "severity": "high",
        "opa_policy": "resource_allocation",
        "description": (
            "At least 50% of non-accept risk responses must have "
            "resources allocated with a budget greater than zero."
        ),
    },
    {
        "control_code": "MANAGE-2.4",
        "title": "System Deactivation Criteria",
        "severity": "high",
        "opa_policy": None,
        "description": (
            "At least one risk response must define system "
            "deactivation criteria with non-empty conditions."
        ),
    },
    {
        "control_code": "MANAGE-3.1",
        "title": "Third-Party Monitoring",
        "severity": "high",
        "opa_policy": "third_party_monitoring",
        "description": (
            "All third-party AI systems must have a recorded "
            "incident or review within the last 90 days."
        ),
    },
    {
        "control_code": "MANAGE-4.1",
        "title": "Post-Deployment Monitoring",
        "severity": "critical",
        "opa_policy": "post_deployment_monitoring",
        "description": (
            "All active AI systems must have a performance metric "
            "recorded within 30 days and no unresolved critical incidents."
        ),
    },
]


# =============================================================================
# NIST MANAGE Service
# =============================================================================


class NISTManageService:
    """
    Service for NIST AI RMF MANAGE function evaluation and management.

    The MANAGE function establishes risk response planning, resource
    allocation, system deactivation criteria, third-party monitoring,
    and post-deployment monitoring for AI systems.

    Responsibilities:
        - Evaluate 5 MANAGE controls against project data
        - Manage risk response entries (CRUD)
        - Manage incident entries (CRUD)
        - Generate MANAGE dashboard analytics

    Usage:
        service = NISTManageService()
        result = await service.evaluate_manage(project_id, db)
        dashboard = await service.get_dashboard(project_id, db)

    Evaluation Strategy:
        Primary path attempts OPA REST API evaluation. When OPA is
        unavailable (development, testing, or connectivity issues),
        falls back to in-process evaluation using identical logic.
        MANAGE-2.4 always uses in-process evaluation (no OPA policy).
    """

    # =========================================================================
    # MANAGE Evaluation
    # =========================================================================

    async def evaluate_manage(
        self,
        project_id: UUID,
        db: AsyncSession,
    ) -> dict:
        """
        Evaluate all 5 NIST MANAGE policies for a project.

        Collects risk responses, incidents, AI systems, performance metrics,
        and risks from the database, then evaluates each MANAGE control.
        Attempts OPA evaluation first (except MANAGE-2.4), then falls back
        to in-process evaluation if OPA is unavailable.

        Args:
            project_id: UUID of the project being evaluated.
            db: SQLAlchemy async database session.

        Returns:
            Dict with keys: project_id, framework_code, function,
            overall_compliant, policies_passed, policies_total,
            compliance_percentage, results, evaluated_at.

        Raises:
            NISTManageEvaluationError: If both OPA and fallback evaluation
                fail for any policy.

        Example:
            result = await service.evaluate_manage(project_id, db)
            print(f"Compliance: {result['compliance_percentage']}%")
        """
        logger.info("Evaluating MANAGE policies for project %s", project_id)

        # ---- Gather all data from DB ----
        risk_responses = await self._fetch_risk_responses(project_id, db)
        incidents = await self._fetch_incidents(project_id, db)
        ai_systems = await self._fetch_ai_systems(project_id, db)
        performance_metrics = await self._fetch_recent_metrics(project_id, db)
        risks = await self._fetch_open_risks(project_id, db)

        logger.info(
            "MANAGE data for project %s: %d responses, %d incidents, "
            "%d AI systems, %d metrics, %d open risks",
            project_id,
            len(risk_responses),
            len(incidents),
            len(ai_systems),
            len(performance_metrics),
            len(risks),
        )

        # ---- Evaluate each policy ----
        results: List[PolicyEvaluationResult] = []

        for policy_def in MANAGE_POLICIES:
            control_code = policy_def["control_code"]
            opa_input = self._build_opa_input(
                control_code=control_code,
                risks=risks,
                risk_responses=risk_responses,
                incidents=incidents,
                ai_systems=ai_systems,
                performance_metrics=performance_metrics,
            )
            try:
                result = await self._evaluate_single_policy(
                    control_code=control_code,
                    title=policy_def["title"],
                    severity=policy_def["severity"],
                    opa_policy=policy_def["opa_policy"],
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
                raise NISTManageEvaluationError(
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
            "MANAGE evaluation complete for project %s: %d/%d passed (%.1f%%)",
            project_id,
            policies_passed,
            policies_total,
            compliance_pct,
        )

        return {
            "project_id": project_id,
            "framework_code": "NIST_AI_RMF",
            "function": "MANAGE",
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
        project_id: UUID,
        db: AsyncSession,
    ) -> dict:
        """
        Get MANAGE function dashboard data for a project.

        Aggregates latest evaluation results, risk response summary,
        and incident statistics.

        Args:
            project_id: UUID of the project.
            db: SQLAlchemy async database session.

        Returns:
            Dict with keys: project_id, compliance_percentage,
            policies_passed, policies_total, policy_results,
            total_risk_responses, completed_responses,
            total_incidents, open_incidents, critical_incidents,
            has_deactivation_criteria.

        Example:
            dashboard = await service.get_dashboard(project_id, db)
            print(f"Compliance: {dashboard['compliance_percentage']}%")
        """
        logger.info("Fetching MANAGE dashboard for project %s", project_id)

        # Fetch latest assessment results for MANAGE controls
        policy_results = await self._fetch_latest_assessments(project_id, db)

        policies_passed = sum(1 for r in policy_results if r.allowed)
        policies_total = (
            len(policy_results) if policy_results else len(MANAGE_POLICIES)
        )
        compliance_pct = (
            (policies_passed / policies_total * 100.0) if policies_total > 0 else 0.0
        )

        # Risk response summary
        response_stats = await self._get_response_stats(project_id, db)

        # Incident summary
        incident_stats = await self._get_incident_stats(project_id, db)

        # Deactivation criteria check
        has_deactivation = await self._has_deactivation_criteria(project_id, db)

        return {
            "project_id": project_id,
            "compliance_percentage": round(compliance_pct, 1),
            "policies_passed": policies_passed,
            "policies_total": policies_total,
            "policy_results": [r.model_dump() for r in policy_results],
            "total_risk_responses": response_stats["total"],
            "completed_responses": response_stats["completed"],
            "total_incidents": incident_stats["total"],
            "open_incidents": incident_stats["open"],
            "critical_incidents": incident_stats["critical"],
            "has_deactivation_criteria": has_deactivation,
        }

    # =========================================================================
    # Risk Response CRUD
    # =========================================================================

    async def list_risk_responses(
        self,
        project_id: UUID,
        status_filter: Optional[str],
        limit: int,
        offset: int,
        db: AsyncSession,
    ) -> Tuple[List[dict], int]:
        """
        List risk response entries for a project with optional filtering.

        Args:
            project_id: UUID of the project.
            status_filter: Optional response status string to filter by.
            limit: Maximum number of results (pagination).
            offset: Number of results to skip (pagination).
            db: SQLAlchemy async database session.

        Returns:
            Tuple of (list of response dicts, total count).

        Example:
            items, total = await service.list_risk_responses(
                project_id=project_id,
                status_filter="planned",
                limit=20,
                offset=0,
                db=db,
            )
        """
        logger.info(
            "Listing risk responses for project %s (status=%s, limit=%d, offset=%d)",
            project_id,
            status_filter,
            limit,
            offset,
        )

        conditions = [ManageRiskResponse.project_id == project_id]

        if status_filter is not None:
            conditions.append(ManageRiskResponse.status == status_filter)

        # Count total matching
        count_query = select(func.count(ManageRiskResponse.id)).where(
            and_(*conditions)
        )
        count_result = await db.execute(count_query)
        total = count_result.scalar() or 0

        # Fetch paginated results ordered by priority then creation date
        query = (
            select(ManageRiskResponse)
            .where(and_(*conditions))
            .order_by(
                ManageRiskResponse.created_at.desc(),
            )
            .offset(offset)
            .limit(limit)
        )

        result = await db.execute(query)
        responses = result.scalars().all()

        items = [resp.to_dict() for resp in responses]

        return items, total

    async def create_risk_response(
        self,
        data: dict,
        db: AsyncSession,
    ) -> dict:
        """
        Create a new risk response entry.

        Args:
            data: Dict with risk response data. Required keys:
                project_id, risk_id, response_type, description.
                Optional: assigned_to, priority, status, due_date,
                resources_allocated, deactivation_criteria, notes.
            db: SQLAlchemy async database session.

        Returns:
            Dict representation of the created risk response.

        Example:
            response = await service.create_risk_response({
                "project_id": project_id,
                "risk_id": risk_id,
                "response_type": "mitigate",
                "description": "Implement bias detection pipeline",
                "assigned_to": "ml-team",
                "priority": "high",
                "due_date": "2026-06-01",
                "resources_allocated": [
                    {"type": "compute", "description": "GPU cluster", "budget": 5000}
                ],
            }, db)
        """
        project_id = data["project_id"]
        risk_id = data["risk_id"]
        response_type = data["response_type"]

        logger.info(
            "Creating risk response for project %s, risk %s (type=%s)",
            project_id,
            risk_id,
            response_type,
        )

        due_date_raw = data.get("due_date")
        due_date_val = None
        if due_date_raw is not None:
            if isinstance(due_date_raw, str):
                from datetime import date as date_type

                due_date_val = date_type.fromisoformat(due_date_raw)
            else:
                due_date_val = due_date_raw

        response = ManageRiskResponse(
            project_id=project_id,
            risk_id=risk_id,
            response_type=response_type,
            description=data["description"],
            assigned_to=data.get("assigned_to"),
            priority=data.get("priority", "medium"),
            status=data.get("status", ResponseStatus.PLANNED.value),
            due_date=due_date_val,
            resources_allocated=data.get("resources_allocated", []),
            deactivation_criteria=data.get("deactivation_criteria"),
            notes=data.get("notes"),
        )

        db.add(response)
        await db.commit()
        await db.refresh(response)

        logger.info(
            "Created risk response %s (type=%s, priority=%s)",
            response.id,
            response.response_type,
            response.priority,
        )

        return response.to_dict()

    async def update_risk_response(
        self,
        response_id: UUID,
        data: dict,
        db: AsyncSession,
    ) -> dict:
        """
        Update an existing risk response entry.

        Only updates fields present in the data dict with non-None values.

        Args:
            response_id: UUID of the risk response to update.
            data: Dict with fields to update. Supported keys:
                response_type, description, assigned_to, priority,
                status, due_date, resources_allocated,
                deactivation_criteria, notes.
            db: SQLAlchemy async database session.

        Returns:
            Dict representation of the updated risk response.

        Raises:
            RiskResponseNotFoundError: If the risk response does not exist.

        Example:
            updated = await service.update_risk_response(
                response_id=resp_id,
                data={"status": "completed", "notes": "Done"},
                db=db,
            )
        """
        logger.info("Updating risk response %s", response_id)

        query = select(ManageRiskResponse).where(
            ManageRiskResponse.id == response_id
        )
        result = await db.execute(query)
        response = result.scalar_one_or_none()

        if response is None:
            raise RiskResponseNotFoundError(
                f"Risk response {response_id} not found"
            )

        updatable_fields = {
            "response_type",
            "description",
            "assigned_to",
            "priority",
            "status",
            "due_date",
            "resources_allocated",
            "deactivation_criteria",
            "notes",
        }

        for field, value in data.items():
            if field in updatable_fields and value is not None:
                if field == "due_date" and isinstance(value, str):
                    from datetime import date as date_type

                    value = date_type.fromisoformat(value)
                setattr(response, field, value)

        await db.commit()
        await db.refresh(response)

        logger.info(
            "Updated risk response %s (status=%s, priority=%s)",
            response_id,
            response.status,
            response.priority,
        )

        return response.to_dict()

    # =========================================================================
    # Incident CRUD
    # =========================================================================

    async def list_incidents(
        self,
        project_id: UUID,
        ai_system_id: Optional[UUID],
        status_filter: Optional[str],
        limit: int,
        offset: int,
        db: AsyncSession,
    ) -> Tuple[List[dict], int]:
        """
        List incident entries for a project with optional filtering.

        Args:
            project_id: UUID of the project.
            ai_system_id: Optional UUID of a specific AI system to filter by.
            status_filter: Optional incident status string to filter by.
            limit: Maximum number of results (pagination).
            offset: Number of results to skip (pagination).
            db: SQLAlchemy async database session.

        Returns:
            Tuple of (list of incident dicts, total count).

        Example:
            items, total = await service.list_incidents(
                project_id=project_id,
                ai_system_id=None,
                status_filter="open",
                limit=20,
                offset=0,
                db=db,
            )
        """
        logger.info(
            "Listing incidents for project %s (system=%s, status=%s, limit=%d, offset=%d)",
            project_id,
            ai_system_id,
            status_filter,
            limit,
            offset,
        )

        conditions = [ManageIncident.project_id == project_id]

        if ai_system_id is not None:
            conditions.append(ManageIncident.ai_system_id == ai_system_id)

        if status_filter is not None:
            conditions.append(ManageIncident.status == status_filter)

        # Count total matching
        count_query = select(func.count(ManageIncident.id)).where(
            and_(*conditions)
        )
        count_result = await db.execute(count_query)
        total = count_result.scalar() or 0

        # Fetch paginated results ordered by occurred_at descending
        query = (
            select(ManageIncident)
            .where(and_(*conditions))
            .order_by(ManageIncident.occurred_at.desc())
            .offset(offset)
            .limit(limit)
        )

        result = await db.execute(query)
        incidents = result.scalars().all()

        items = [inc.to_dict() for inc in incidents]

        return items, total

    async def create_incident(
        self,
        data: dict,
        db: AsyncSession,
    ) -> dict:
        """
        Create a new incident entry.

        Args:
            data: Dict with incident data. Required keys:
                project_id, ai_system_id, title, severity,
                incident_type, occurred_at.
                Optional: risk_id, description, status, reported_by,
                assigned_to, resolution, root_cause, resolved_at.
            db: SQLAlchemy async database session.

        Returns:
            Dict representation of the created incident.

        Example:
            incident = await service.create_incident({
                "project_id": project_id,
                "ai_system_id": system_id,
                "title": "Model accuracy degradation",
                "severity": "high",
                "incident_type": "performance_degradation",
                "occurred_at": "2026-04-20T10:00:00Z",
                "reported_by": "monitoring-system",
            }, db)
        """
        project_id = data["project_id"]
        ai_system_id = data["ai_system_id"]

        logger.info(
            "Creating incident for project %s, system %s (severity=%s, type=%s)",
            project_id,
            ai_system_id,
            data.get("severity"),
            data.get("incident_type"),
        )

        occurred_at_raw = data["occurred_at"]
        if isinstance(occurred_at_raw, str):
            occurred_at_val = datetime.fromisoformat(
                occurred_at_raw.replace("Z", "+00:00")
            )
        else:
            occurred_at_val = occurred_at_raw

        resolved_at_raw = data.get("resolved_at")
        resolved_at_val = None
        if resolved_at_raw is not None:
            if isinstance(resolved_at_raw, str):
                resolved_at_val = datetime.fromisoformat(
                    resolved_at_raw.replace("Z", "+00:00")
                )
            else:
                resolved_at_val = resolved_at_raw

        incident = ManageIncident(
            project_id=project_id,
            ai_system_id=ai_system_id,
            risk_id=data.get("risk_id"),
            title=data["title"],
            description=data.get("description"),
            severity=data["severity"],
            incident_type=data["incident_type"],
            status=data.get("status", IncidentStatus.OPEN.value),
            reported_by=data.get("reported_by"),
            assigned_to=data.get("assigned_to"),
            resolution=data.get("resolution"),
            root_cause=data.get("root_cause"),
            occurred_at=occurred_at_val,
            resolved_at=resolved_at_val,
        )

        db.add(incident)
        await db.commit()
        await db.refresh(incident)

        logger.info(
            "Created incident %s (severity=%s, type=%s)",
            incident.id,
            incident.severity,
            incident.incident_type,
        )

        return incident.to_dict()

    async def update_incident(
        self,
        incident_id: UUID,
        data: dict,
        db: AsyncSession,
    ) -> dict:
        """
        Update an existing incident entry.

        Only updates fields present in the data dict with non-None values.

        Args:
            incident_id: UUID of the incident to update.
            data: Dict with fields to update. Supported keys:
                title, description, severity, incident_type, status,
                reported_by, assigned_to, resolution, root_cause,
                resolved_at.
            db: SQLAlchemy async database session.

        Returns:
            Dict representation of the updated incident.

        Raises:
            IncidentNotFoundError: If the incident does not exist.

        Example:
            updated = await service.update_incident(
                incident_id=inc_id,
                data={
                    "status": "resolved",
                    "resolution": "Retrained model with balanced dataset",
                    "resolved_at": "2026-04-21T15:00:00Z",
                },
                db=db,
            )
        """
        logger.info("Updating incident %s", incident_id)

        query = select(ManageIncident).where(ManageIncident.id == incident_id)
        result = await db.execute(query)
        incident = result.scalar_one_or_none()

        if incident is None:
            raise IncidentNotFoundError(f"Incident {incident_id} not found")

        updatable_fields = {
            "title",
            "description",
            "severity",
            "incident_type",
            "status",
            "reported_by",
            "assigned_to",
            "resolution",
            "root_cause",
            "resolved_at",
        }

        for field, value in data.items():
            if field in updatable_fields and value is not None:
                if field == "resolved_at" and isinstance(value, str):
                    value = datetime.fromisoformat(
                        value.replace("Z", "+00:00")
                    )
                setattr(incident, field, value)

        await db.commit()
        await db.refresh(incident)

        logger.info(
            "Updated incident %s (severity=%s, status=%s)",
            incident_id,
            incident.severity,
            incident.status,
        )

        return incident.to_dict()

    # =========================================================================
    # Private: OPA Evaluation with In-Process Fallback
    # =========================================================================

    async def _evaluate_single_policy(
        self,
        control_code: str,
        title: str,
        severity: str,
        opa_policy: Optional[str],
        opa_input: Dict[str, Any],
    ) -> PolicyEvaluationResult:
        """
        Evaluate a single MANAGE policy using OPA with in-process fallback.

        MANAGE-2.4 always uses in-process evaluation (opa_policy is None).
        All others attempt OPA first, then fall back to in-process.

        Args:
            control_code: Policy control code (e.g., MANAGE-1.1).
            title: Human-readable policy title.
            severity: Policy severity level.
            opa_policy: OPA policy name, or None for in-process only.
            opa_input: Structured input data for evaluation.

        Returns:
            PolicyEvaluationResult with pass/fail status and reason.
        """
        # MANAGE-2.4 has no OPA policy; always in-process
        if opa_policy is None:
            return self._evaluate_fallback(control_code, opa_input)

        # Try OPA first
        try:
            result = await self._evaluate_via_opa(opa_policy, opa_input)
            if result is not None:
                return result
        except Exception as exc:
            logger.warning(
                "OPA evaluation unavailable for %s, using in-process fallback: %s",
                control_code,
                str(exc),
            )

        # In-process fallback evaluation
        return self._evaluate_fallback(control_code, opa_input)

    async def _evaluate_via_opa(
        self,
        policy_name: str,
        opa_input: Dict[str, Any],
    ) -> Optional[PolicyEvaluationResult]:
        """
        Attempt policy evaluation via OPA REST API.

        Uses httpx for async HTTP calls (network-only, AGPL-safe) to call OPA.
        Returns None if OPA is not reachable so the caller can fall back.

        Args:
            policy_name: OPA policy name (e.g., risk_response_planning).
            opa_input: Structured input for OPA.

        Returns:
            PolicyEvaluationResult if OPA responded, None if unreachable.
        """
        import httpx

        opa_url = (
            f"{settings.OPA_URL}/v1/data/compliance/nist/manage/"
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
                    policy_name,
                )
                return None

            opa_result = response.json()
            result_data = opa_result.get("result", {})

            # Extract OPA policy output
            allowed = result_data.get("allow", False)
            reason = result_data.get("reason", "Evaluated by OPA")
            policy_title = result_data.get("title", policy_name)
            policy_severity = result_data.get("severity", "medium")
            control_code = result_data.get("control_code", policy_name)

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
            logger.warning("OPA request timed out for %s", policy_name)
            return None

    def _evaluate_fallback(
        self,
        control_code: str,
        opa_input: Dict[str, Any],
    ) -> PolicyEvaluationResult:
        """
        In-process policy evaluation matching Rego policy logic.

        Implements the same decision logic as the OPA Rego policies
        for environments where OPA is not available.

        Args:
            control_code: Policy control code.
            opa_input: Structured input data.

        Returns:
            PolicyEvaluationResult with pass/fail and reason.
        """
        evaluators = {
            "MANAGE-1.1": self._eval_risk_response_planning,
            "MANAGE-2.1": self._eval_resource_allocation,
            "MANAGE-2.4": self._eval_deactivation_criteria,
            "MANAGE-3.1": self._eval_third_party_monitoring,
            "MANAGE-4.1": self._eval_post_deployment_monitoring,
        }

        evaluator = evaluators.get(control_code)
        if evaluator is None:
            return PolicyEvaluationResult(
                control_code=control_code,
                title=control_code,
                allowed=False,
                reason=f"Unknown control code: {control_code}",
                severity="medium",
                details={"source": "in_process", "error": "unknown_control"},
            )

        # Look up the policy definition for title and severity
        policy_def = next(
            (p for p in MANAGE_POLICIES if p["control_code"] == control_code),
            None,
        )
        title = policy_def["title"] if policy_def else control_code
        severity = policy_def["severity"] if policy_def else "medium"

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
    def _eval_risk_response_planning(
        opa_input: Dict[str, Any],
    ) -> Tuple[bool, str, Dict[str, Any]]:
        """
        MANAGE-1.1: Every open risk has at least one response with
        assigned_to and due_date set.

        Args:
            opa_input: Must contain 'risks' and 'risk_responses'.

        Returns:
            Tuple of (allowed, reason, details).
        """
        risks = opa_input.get("risks", [])
        risk_responses = opa_input.get("risk_responses", [])

        if not risks:
            return (
                True,
                "No open risks registered. Risk response planning is not required.",
                {"open_risks": 0, "uncovered_risks": []},
            )

        # Index responses by risk_id
        responses_by_risk: Dict[str, List[Dict[str, Any]]] = {}
        for resp in risk_responses:
            rid = resp.get("risk_id", "")
            if rid not in responses_by_risk:
                responses_by_risk[rid] = []
            responses_by_risk[rid].append(resp)

        uncovered: List[str] = []
        for risk in risks:
            risk_id = risk.get("id", "")
            risk_resps = responses_by_risk.get(risk_id, [])

            # Check if at least one response has assigned_to and due_date
            has_valid_response = any(
                r.get("assigned_to") and r.get("due_date")
                for r in risk_resps
            )

            if not has_valid_response:
                uncovered.append(risk.get("risk_code", risk_id))

        if uncovered:
            return (
                False,
                (
                    f"{len(uncovered)} open risk(s) lack a response plan with "
                    f"assigned owner and due date: {', '.join(uncovered)}"
                ),
                {"open_risks": len(risks), "uncovered_risks": uncovered},
            )

        return (
            True,
            f"All {len(risks)} open risk(s) have response plans with assigned owners and due dates.",
            {"open_risks": len(risks), "uncovered_risks": []},
        )

    @staticmethod
    def _eval_resource_allocation(
        opa_input: Dict[str, Any],
    ) -> Tuple[bool, str, Dict[str, Any]]:
        """
        MANAGE-2.1: At least 50% of non-accept risk responses must have
        resources with budget > 0.

        Responses where response_type == 'accept' are excluded from the
        budget check per CTO condition.

        Args:
            opa_input: Must contain 'risk_responses' list with response_type
                and resources_allocated fields.

        Returns:
            Tuple of (allowed, reason, details).
        """
        risk_responses = opa_input.get("risk_responses", [])

        # Filter out accept responses for the budget check
        non_accept_responses = [
            r for r in risk_responses
            if r.get("response_type", "").lower() != ResponseType.ACCEPT.value
        ]

        if not non_accept_responses:
            return (
                True,
                "No non-accept risk responses. Resource allocation check is not applicable.",
                {
                    "total_responses": len(risk_responses),
                    "non_accept_responses": 0,
                    "resourced_responses": 0,
                    "threshold_pct": 50,
                },
            )

        resourced_count = 0
        for resp in non_accept_responses:
            resources = resp.get("resources_allocated", [])
            has_budget = any(
                isinstance(r.get("budget"), (int, float)) and r.get("budget", 0) > 0
                for r in resources
            )
            if has_budget:
                resourced_count += 1

        total_non_accept = len(non_accept_responses)
        pct = (resourced_count / total_non_accept * 100.0) if total_non_accept > 0 else 0.0

        if pct < 50.0:
            return (
                False,
                (
                    f"Only {resourced_count}/{total_non_accept} ({pct:.0f}%) "
                    f"non-accept responses have resources allocated with budget > 0. "
                    f"Minimum 50% required."
                ),
                {
                    "total_responses": len(risk_responses),
                    "non_accept_responses": total_non_accept,
                    "resourced_responses": resourced_count,
                    "allocation_pct": round(pct, 1),
                    "threshold_pct": 50,
                },
            )

        return (
            True,
            (
                f"{resourced_count}/{total_non_accept} ({pct:.0f}%) non-accept "
                f"responses have resources allocated. Meets 50% threshold."
            ),
            {
                "total_responses": len(risk_responses),
                "non_accept_responses": total_non_accept,
                "resourced_responses": resourced_count,
                "allocation_pct": round(pct, 1),
                "threshold_pct": 50,
            },
        )

    @staticmethod
    def _eval_deactivation_criteria(
        opa_input: Dict[str, Any],
    ) -> Tuple[bool, str, Dict[str, Any]]:
        """
        MANAGE-2.4: At least one risk response must define system
        deactivation criteria with non-empty conditions.

        This policy is always evaluated in-process (no OPA policy).

        Args:
            opa_input: Must contain 'risk_responses' with
                deactivation_criteria field.

        Returns:
            Tuple of (allowed, reason, details).
        """
        risk_responses = opa_input.get("risk_responses", [])

        if not risk_responses:
            return (
                False,
                "No risk responses exist. At least one must define deactivation criteria.",
                {"total_responses": 0, "responses_with_criteria": 0},
            )

        responses_with_criteria = 0
        for resp in risk_responses:
            deactivation = resp.get("deactivation_criteria")
            if deactivation and isinstance(deactivation, dict):
                conditions = deactivation.get("conditions", [])
                if conditions and len(conditions) > 0:
                    responses_with_criteria += 1

        if responses_with_criteria == 0:
            return (
                False,
                (
                    "No risk responses define deactivation criteria with non-empty "
                    "conditions. At least one is required for MANAGE-2.4 compliance."
                ),
                {
                    "total_responses": len(risk_responses),
                    "responses_with_criteria": 0,
                },
            )

        return (
            True,
            (
                f"{responses_with_criteria} risk response(s) define system "
                f"deactivation criteria with conditions."
            ),
            {
                "total_responses": len(risk_responses),
                "responses_with_criteria": responses_with_criteria,
            },
        )

    @staticmethod
    def _eval_third_party_monitoring(
        opa_input: Dict[str, Any],
    ) -> Tuple[bool, str, Dict[str, Any]]:
        """
        MANAGE-3.1: All third-party systems must have an incident or
        review recorded within the last 90 days.

        Args:
            opa_input: Must contain 'third_party_systems', 'incidents',
                and 'cutoff_date'.

        Returns:
            Tuple of (allowed, reason, details).
        """
        third_party_systems = opa_input.get("third_party_systems", [])
        incidents = opa_input.get("incidents", [])
        cutoff_date_str = opa_input.get("cutoff_date", "")

        # No third-party systems means compliant (nothing to monitor)
        if not third_party_systems:
            return (
                True,
                "No third-party AI systems identified. Third-party monitoring is not required.",
                {"third_party_count": 0, "unmonitored_systems": []},
            )

        # Build set of system IDs that have incidents after cutoff
        monitored_system_ids: set = set()
        for inc in incidents:
            occurred = inc.get("occurred_at", "")
            if occurred and occurred >= cutoff_date_str:
                sys_id = inc.get("ai_system_id", "")
                if sys_id:
                    monitored_system_ids.add(sys_id)

        unmonitored: List[str] = []
        for system in third_party_systems:
            sys_id = system.get("id", "")
            if sys_id not in monitored_system_ids:
                unmonitored.append(system.get("name", sys_id))

        if unmonitored:
            return (
                False,
                (
                    f"{len(unmonitored)} third-party system(s) have no recorded "
                    f"incident or review in the last 90 days: {', '.join(unmonitored)}"
                ),
                {
                    "third_party_count": len(third_party_systems),
                    "unmonitored_systems": unmonitored,
                },
            )

        return (
            True,
            (
                f"All {len(third_party_systems)} third-party system(s) have been "
                f"monitored within the last 90 days."
            ),
            {
                "third_party_count": len(third_party_systems),
                "unmonitored_systems": [],
            },
        )

    @staticmethod
    def _eval_post_deployment_monitoring(
        opa_input: Dict[str, Any],
    ) -> Tuple[bool, str, Dict[str, Any]]:
        """
        MANAGE-4.1: All active AI systems must have a performance metric
        recorded within 30 days and no unresolved critical incidents.

        Args:
            opa_input: Must contain 'active_systems', 'recent_metrics',
                and 'critical_incidents'.

        Returns:
            Tuple of (allowed, reason, details).
        """
        active_systems = opa_input.get("active_systems", [])
        recent_metrics = opa_input.get("recent_metrics", [])
        critical_incidents = opa_input.get("critical_incidents", [])

        if not active_systems:
            return (
                True,
                "No active AI systems. Post-deployment monitoring is not required.",
                {
                    "active_systems_count": 0,
                    "systems_without_metrics": [],
                    "unresolved_critical_count": 0,
                },
            )

        # Build set of system IDs with recent metrics
        systems_with_metrics: set = set()
        for metric in recent_metrics:
            sys_id = metric.get("ai_system_id", "")
            if sys_id:
                systems_with_metrics.add(sys_id)

        systems_without_metrics: List[str] = []
        for system in active_systems:
            sys_id = system.get("id", "")
            if sys_id not in systems_with_metrics:
                systems_without_metrics.append(system.get("name", sys_id))

        issues: List[str] = []

        if systems_without_metrics:
            issues.append(
                f"{len(systems_without_metrics)} system(s) lack performance "
                f"metrics in the last 30 days: {', '.join(systems_without_metrics)}"
            )

        if critical_incidents:
            issues.append(
                f"{len(critical_incidents)} unresolved critical incident(s) detected"
            )

        if issues:
            return (
                False,
                ". ".join(issues) + ".",
                {
                    "active_systems_count": len(active_systems),
                    "systems_without_metrics": systems_without_metrics,
                    "unresolved_critical_count": len(critical_incidents),
                },
            )

        return (
            True,
            (
                f"All {len(active_systems)} active system(s) have recent metrics "
                f"and no unresolved critical incidents."
            ),
            {
                "active_systems_count": len(active_systems),
                "systems_without_metrics": [],
                "unresolved_critical_count": 0,
            },
        )

    # =========================================================================
    # Private: Helpers
    # =========================================================================

    @staticmethod
    def _is_third_party_system(ai_system: AISystem) -> bool:
        """
        Determine if an AI system is third-party based on its dependencies.

        A system is third-party if any dependency has a provider value
        that is not internal, in-house, or empty.

        Args:
            ai_system: AISystem model instance.

        Returns:
            True if the system has at least one external dependency.
        """
        deps = ai_system.dependencies or []
        for dep in deps:
            provider = dep.get("provider", "")
            if provider and provider.lower() not in ("internal", "in-house", ""):
                return True
        return False

    @staticmethod
    def _build_opa_input(
        control_code: str,
        risks: List[Dict[str, Any]],
        risk_responses: List[Dict[str, Any]],
        incidents: List[Dict[str, Any]],
        ai_systems: List[Dict[str, Any]],
        performance_metrics: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """
        Build structured OPA input for a specific MANAGE policy.

        Each control code receives a tailored subset of data to minimize
        the payload sent to OPA.

        Args:
            control_code: The MANAGE control code.
            risks: Serialized open risk entries.
            risk_responses: Serialized risk response entries.
            incidents: Serialized incident entries.
            ai_systems: Serialized AI system entries (with third-party flag).
            performance_metrics: Serialized recent performance metrics.

        Returns:
            Dict suitable for OPA input or in-process evaluation.
        """
        now = datetime.now(timezone.utc)

        if control_code == "MANAGE-1.1":
            return {
                "risks": risks,
                "risk_responses": risk_responses,
            }

        if control_code == "MANAGE-2.1":
            return {
                "risk_responses": risk_responses,
            }

        if control_code == "MANAGE-2.4":
            return {
                "risk_responses": risk_responses,
            }

        if control_code == "MANAGE-3.1":
            cutoff = now - timedelta(days=90)
            third_party = [s for s in ai_systems if s.get("is_third_party", False)]
            return {
                "third_party_systems": third_party,
                "incidents": incidents,
                "cutoff_date": cutoff.isoformat(),
            }

        if control_code == "MANAGE-4.1":
            active = [s for s in ai_systems if s.get("is_active", False)]
            # Filter for metrics within 30 days
            metric_cutoff = now - timedelta(days=30)
            cutoff_str = metric_cutoff.isoformat()
            recent = [
                m for m in performance_metrics
                if m.get("measured_at", "") >= cutoff_str
            ]
            # Unresolved critical incidents
            critical = [
                i for i in incidents
                if (
                    i.get("severity") == IncidentSeverity.CRITICAL.value
                    and i.get("status") not in (
                        IncidentStatus.RESOLVED.value,
                        IncidentStatus.CLOSED.value,
                    )
                )
            ]
            return {
                "active_systems": active,
                "recent_metrics": recent,
                "critical_incidents": critical,
            }

        # Default: send everything
        return {
            "risks": risks,
            "risk_responses": risk_responses,
            "incidents": incidents,
            "ai_systems": ai_systems,
            "performance_metrics": performance_metrics,
        }

    # =========================================================================
    # Private: Data Fetching
    # =========================================================================

    async def _fetch_risk_responses(
        self,
        project_id: UUID,
        db: AsyncSession,
    ) -> List[Dict[str, Any]]:
        """
        Fetch all risk responses for a project as serialized dicts.

        Args:
            project_id: UUID of the project.
            db: SQLAlchemy async database session.

        Returns:
            List of risk response dicts.
        """
        query = (
            select(ManageRiskResponse)
            .where(ManageRiskResponse.project_id == project_id)
            .order_by(ManageRiskResponse.created_at.desc())
        )
        result = await db.execute(query)
        responses = result.scalars().all()
        return [resp.to_dict() for resp in responses]

    async def _fetch_incidents(
        self,
        project_id: UUID,
        db: AsyncSession,
    ) -> List[Dict[str, Any]]:
        """
        Fetch all incidents for a project as serialized dicts.

        Args:
            project_id: UUID of the project.
            db: SQLAlchemy async database session.

        Returns:
            List of incident dicts.
        """
        query = (
            select(ManageIncident)
            .where(ManageIncident.project_id == project_id)
            .order_by(ManageIncident.occurred_at.desc())
        )
        result = await db.execute(query)
        incidents = result.scalars().all()
        return [inc.to_dict() for inc in incidents]

    async def _fetch_ai_systems(
        self,
        project_id: UUID,
        db: AsyncSession,
    ) -> List[Dict[str, Any]]:
        """
        Fetch all active AI systems for a project as serialized dicts.

        Includes 'is_third_party' flag for each system based on
        dependency analysis.

        Args:
            project_id: UUID of the project.
            db: SQLAlchemy async database session.

        Returns:
            List of AI system dicts with 'is_third_party' field.
        """
        query = (
            select(AISystem)
            .where(
                and_(
                    AISystem.project_id == project_id,
                    AISystem.is_active.is_(True),
                )
            )
            .order_by(AISystem.created_at.desc())
        )
        result = await db.execute(query)
        systems = result.scalars().all()

        items: List[Dict[str, Any]] = []
        for system in systems:
            data = system.to_dict()
            data["is_third_party"] = self._is_third_party_system(system)
            data["is_active"] = system.is_active
            items.append(data)

        return items

    async def _fetch_recent_metrics(
        self,
        project_id: UUID,
        db: AsyncSession,
    ) -> List[Dict[str, Any]]:
        """
        Fetch performance metrics for a project recorded within the
        last 30 days as serialized dicts.

        Args:
            project_id: UUID of the project.
            db: SQLAlchemy async database session.

        Returns:
            List of performance metric dicts.
        """
        cutoff = datetime.now(timezone.utc) - timedelta(days=30)

        query = (
            select(PerformanceMetric)
            .where(
                and_(
                    PerformanceMetric.project_id == project_id,
                    PerformanceMetric.measured_at >= cutoff,
                )
            )
            .order_by(PerformanceMetric.measured_at.desc())
        )
        result = await db.execute(query)
        metrics = result.scalars().all()
        return [m.to_dict() for m in metrics]

    async def _fetch_open_risks(
        self,
        project_id: UUID,
        db: AsyncSession,
    ) -> List[Dict[str, Any]]:
        """
        Fetch open (non-closed) risks for a project as serialized dicts.

        Open risks are those with status not in ('mitigated', 'accepted', 'closed').

        Args:
            project_id: UUID of the project.
            db: SQLAlchemy async database session.

        Returns:
            List of risk dicts with id, risk_code, title, status.
        """
        closed_statuses = {
            RiskStatus.MITIGATED.value,
            RiskStatus.ACCEPTED.value,
            RiskStatus.CLOSED.value,
        }

        query = (
            select(ComplianceRiskRegister)
            .where(
                and_(
                    ComplianceRiskRegister.project_id == project_id,
                    ComplianceRiskRegister.status.notin_(closed_statuses),
                )
            )
            .order_by(ComplianceRiskRegister.risk_score.desc())
        )
        result = await db.execute(query)
        risks = result.scalars().all()

        return [
            {
                "id": str(risk.id),
                "risk_code": risk.risk_code,
                "title": risk.title,
                "status": risk.status,
                "risk_score": risk.risk_score,
            }
            for risk in risks
        ]

    # =========================================================================
    # Private: Dashboard Statistics
    # =========================================================================

    async def _get_response_stats(
        self,
        project_id: UUID,
        db: AsyncSession,
    ) -> Dict[str, int]:
        """
        Get risk response statistics for a project.

        Args:
            project_id: UUID of the project.
            db: SQLAlchemy async database session.

        Returns:
            Dict with keys 'total' and 'completed'.
        """
        total_query = select(func.count(ManageRiskResponse.id)).where(
            ManageRiskResponse.project_id == project_id
        )
        total_result = await db.execute(total_query)
        total = total_result.scalar() or 0

        completed_query = select(func.count(ManageRiskResponse.id)).where(
            and_(
                ManageRiskResponse.project_id == project_id,
                ManageRiskResponse.status == ResponseStatus.COMPLETED.value,
            )
        )
        completed_result = await db.execute(completed_query)
        completed = completed_result.scalar() or 0

        return {"total": total, "completed": completed}

    async def _get_incident_stats(
        self,
        project_id: UUID,
        db: AsyncSession,
    ) -> Dict[str, int]:
        """
        Get incident statistics for a project.

        Args:
            project_id: UUID of the project.
            db: SQLAlchemy async database session.

        Returns:
            Dict with keys 'total', 'open', and 'critical'.
        """
        total_query = select(func.count(ManageIncident.id)).where(
            ManageIncident.project_id == project_id
        )
        total_result = await db.execute(total_query)
        total = total_result.scalar() or 0

        open_statuses = {
            IncidentStatus.OPEN.value,
            IncidentStatus.INVESTIGATING.value,
            IncidentStatus.MITIGATING.value,
        }
        open_query = select(func.count(ManageIncident.id)).where(
            and_(
                ManageIncident.project_id == project_id,
                ManageIncident.status.in_(open_statuses),
            )
        )
        open_result = await db.execute(open_query)
        open_count = open_result.scalar() or 0

        critical_query = select(func.count(ManageIncident.id)).where(
            and_(
                ManageIncident.project_id == project_id,
                ManageIncident.severity == IncidentSeverity.CRITICAL.value,
                ManageIncident.status.in_(open_statuses),
            )
        )
        critical_result = await db.execute(critical_query)
        critical_count = critical_result.scalar() or 0

        return {"total": total, "open": open_count, "critical": critical_count}

    async def _has_deactivation_criteria(
        self,
        project_id: UUID,
        db: AsyncSession,
    ) -> bool:
        """
        Check if any risk response for the project defines deactivation criteria.

        Args:
            project_id: UUID of the project.
            db: SQLAlchemy async database session.

        Returns:
            True if at least one response has non-null deactivation_criteria
            with non-empty conditions.
        """
        query = (
            select(ManageRiskResponse)
            .where(
                and_(
                    ManageRiskResponse.project_id == project_id,
                    ManageRiskResponse.deactivation_criteria.isnot(None),
                )
            )
        )
        result = await db.execute(query)
        responses = result.scalars().all()

        for resp in responses:
            criteria = resp.deactivation_criteria
            if criteria and isinstance(criteria, dict):
                conditions = criteria.get("conditions", [])
                if conditions and len(conditions) > 0:
                    return True

        return False

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
        MANAGE controls based on evaluation results.

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

        # Fetch MANAGE controls for this framework
        controls_query = select(ComplianceControl).where(
            and_(
                ComplianceControl.framework_id == framework.id,
                ComplianceControl.category == "MANAGE",
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
        Fetch the latest MANAGE assessment results from the database.

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

        # Fetch MANAGE controls
        controls_query = (
            select(ComplianceControl)
            .where(
                and_(
                    ComplianceControl.framework_id == framework.id,
                    ComplianceControl.category == "MANAGE",
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
