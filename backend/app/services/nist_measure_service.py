"""
=========================================================================
NIST MEASURE Service - NIST AI RMF MEASURE Function
SDLC Orchestrator - Sprint 157 (Phase 3: COMPLIANCE)

Version: 1.0.0
Date: April 14, 2026
Status: ACTIVE
Authority: CTO Approved
Framework: SDLC 6.0.5
Reference: ADR-051, NIST AI RMF 1.0 Section MEASURE

Purpose:
Implements the MEASURE function of the NIST AI Risk Management Framework.
MEASURE quantifies AI system performance, evaluates bias, and tracks trends:
- MEASURE-1.1: Performance thresholds (all metrics within bounds)
- MEASURE-2.1: Bias detection (>=2 demographic groups, scores within threshold)
- MEASURE-2.2: Disparity analysis (4/5ths rule, ratio <= 1.25)
- MEASURE-3.1: Metric trending (>=3 data points per key metric)

Evaluation Strategy:
- Primary: OPA policy evaluation via OPA REST API (network-only, AGPL-safe)
- Fallback: In-process evaluation using identical logic when OPA is unavailable
- MEASURE-3.1 is always in-process (requires DB aggregation)

Performance Targets:
- Evaluate MEASURE: <500ms (p95)
- Dashboard: <200ms (p95)
- List metrics: <200ms (p95)
- Metric CRUD: <100ms (p95)
- Trend query: <300ms (p95)
- Bias summary: <300ms (p95)

Zero Mock Policy: Production-ready implementation
=========================================================================
"""

import logging
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Tuple
from uuid import UUID

import httpx
from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.compliance import (
    ComplianceAssessment,
    ComplianceControl,
    ComplianceFramework,
)
from app.models.nist_map_measure import AISystem, MetricType, PerformanceMetric
from app.schemas.compliance_framework import PolicyEvaluationResult

logger = logging.getLogger(__name__)

# EEOC 4/5ths rule disparity threshold
DISPARITY_THRESHOLD = 1.25

# OPA base URL from config (default: http://opa:8181)
OPA_BASE_URL = f"{settings.OPA_URL}/v1/data"

# Key metric types that require trending (>=3 data points)
KEY_METRIC_TYPES = {"accuracy", "bias_score", "disparity_index", "f1_score"}


# =============================================================================
# Custom Exceptions
# =============================================================================


class NISTMeasureServiceError(Exception):
    """Base exception for NIST MEASURE service errors."""

    pass


class MetricNotFoundError(NISTMeasureServiceError):
    """Exception raised when a metric is not found."""

    pass


class InsufficientDataError(NISTMeasureServiceError):
    """Exception raised when insufficient data for evaluation."""

    pass


class NISTMeasureEvaluationError(NISTMeasureServiceError):
    """Exception raised when policy evaluation fails."""

    pass


# =============================================================================
# MEASURE Policy Definitions
# =============================================================================

MEASURE_POLICIES = [
    {
        "control_code": "MEASURE-1.1",
        "title": "Performance Thresholds",
        "severity": "high",
        "opa_policy": "compliance/nist/measure/performance_thresholds",
    },
    {
        "control_code": "MEASURE-2.1",
        "title": "Bias Detection",
        "severity": "critical",
        "opa_policy": "compliance/nist/measure/bias_detection",
    },
    {
        "control_code": "MEASURE-2.2",
        "title": "Disparity Analysis",
        "severity": "critical",
        "opa_policy": "compliance/nist/measure/disparity_analysis",
    },
    {
        "control_code": "MEASURE-3.1",
        "title": "Metric Trending",
        "severity": "medium",
        "opa_policy": None,  # In-process only
    },
]


# =============================================================================
# NIST MEASURE Service
# =============================================================================


class NISTMeasureService:
    """
    Service for NIST AI RMF MEASURE function evaluation and management.

    The MEASURE function quantifies AI system performance, evaluates
    bias across demographic groups, and tracks metric trends over time.

    Responsibilities:
        - Evaluate 4 MEASURE controls via OPA + in-process fallback
        - Manage performance metrics (CRUD + batch)
        - Generate metric trend data (30-day window)
        - Compute bias/disparity summaries
        - Generate dashboard analytics
    """

    # =========================================================================
    # MEASURE Evaluation
    # =========================================================================

    async def evaluate_measure(
        self,
        project_id: UUID,
        db: AsyncSession,
    ) -> Dict[str, Any]:
        """
        Evaluate all 4 NIST MEASURE policies for a project.

        Fetches metrics and AI systems from DB, evaluates each MEASURE
        control via OPA (with in-process fallback), and persists results.

        Args:
            project_id: UUID of the project being evaluated.
            db: SQLAlchemy async database session.

        Returns:
            Dict with evaluation response data including per-policy results
            and overall compliance percentage.
        """
        logger.info("Evaluating MEASURE policies for project %s", project_id)

        # Fetch AI systems and metrics from DB
        ai_systems = await self._fetch_ai_systems(project_id, db)
        metrics = await self._fetch_all_metrics(project_id, db)

        ai_systems_data = [
            {"id": str(s.id), "name": s.name}
            for s in ai_systems
        ]
        metrics_data = [
            {
                "ai_system_id": str(m.ai_system_id),
                "metric_type": m.metric_type,
                "metric_name": m.metric_name,
                "metric_value": m.metric_value,
                "threshold_min": m.threshold_min,
                "threshold_max": m.threshold_max,
                "demographic_group": m.demographic_group,
            }
            for m in metrics
        ]

        opa_input = {
            "ai_systems": ai_systems_data,
            "metrics": metrics_data,
        }

        results: List[PolicyEvaluationResult] = []

        for policy_def in MEASURE_POLICIES:
            control_code = policy_def["control_code"]
            try:
                if policy_def["opa_policy"] is None:
                    # MEASURE-3.1: In-process only (requires DB aggregation)
                    result = await self._evaluate_metric_trending(project_id, db)
                else:
                    result = await self._evaluate_single_policy(
                        control_code=control_code,
                        title=policy_def["title"],
                        severity=policy_def["severity"],
                        opa_policy=policy_def["opa_policy"],
                        opa_input=opa_input,
                        metrics_data=metrics_data,
                        ai_systems_data=ai_systems_data,
                    )
                results.append(result)
            except Exception as exc:
                logger.error(
                    "Evaluation failed for %s on project %s: %s",
                    control_code, project_id, str(exc),
                )
                raise NISTMeasureEvaluationError(
                    f"Failed to evaluate {control_code}: {str(exc)}"
                ) from exc

        policies_passed = sum(1 for r in results if r.allowed)
        policies_total = len(results)
        compliance_pct = (
            (policies_passed / policies_total * 100.0) if policies_total > 0 else 0.0
        )

        now = datetime.now(timezone.utc)

        # Persist assessment results
        await self._persist_assessment_results(project_id, results, db)

        logger.info(
            "MEASURE evaluation complete for project %s: %d/%d passed (%.1f%%)",
            project_id, policies_passed, policies_total, compliance_pct,
        )

        return {
            "project_id": str(project_id),
            "framework_code": "NIST_AI_RMF",
            "function": "MEASURE",
            "overall_compliant": policies_passed == policies_total,
            "policies_passed": policies_passed,
            "policies_total": policies_total,
            "compliance_percentage": round(compliance_pct, 1),
            "results": [r.model_dump() for r in results],
            "evaluated_at": now.isoformat(),
        }

    async def _evaluate_single_policy(
        self,
        control_code: str,
        title: str,
        severity: str,
        opa_policy: str,
        opa_input: Dict[str, Any],
        metrics_data: List[Dict],
        ai_systems_data: List[Dict],
    ) -> PolicyEvaluationResult:
        """Evaluate a single MEASURE policy via OPA with in-process fallback."""
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                url = f"{OPA_BASE_URL}/{opa_policy}/result"
                response = await client.post(url, json={"input": opa_input})
                if response.status_code == 200:
                    data = response.json()
                    opa_result = data.get("result", {})
                    return PolicyEvaluationResult(
                        control_code=control_code,
                        title=title,
                        allowed=opa_result.get("allowed", False),
                        reason=opa_result.get("reason", "Unknown"),
                        severity=opa_result.get("severity", severity),
                        details=opa_result.get("details", {}),
                    )
        except Exception as exc:
            logger.warning(
                "OPA unavailable for %s, falling back to in-process: %s",
                control_code, str(exc),
            )

        # In-process fallback
        return self._evaluate_in_process(
            control_code, title, severity, metrics_data, ai_systems_data
        )

    def _evaluate_in_process(
        self,
        control_code: str,
        title: str,
        severity: str,
        metrics_data: List[Dict],
        ai_systems_data: List[Dict],
    ) -> PolicyEvaluationResult:
        """Route to the correct in-process evaluator."""
        if control_code == "MEASURE-1.1":
            return self._evaluate_performance_thresholds(metrics_data)
        elif control_code == "MEASURE-2.1":
            return self._evaluate_bias_detection(metrics_data, ai_systems_data)
        elif control_code == "MEASURE-2.2":
            return self._evaluate_disparity_analysis(metrics_data, ai_systems_data)
        else:
            return PolicyEvaluationResult(
                control_code=control_code,
                title=title,
                allowed=False,
                reason=f"No evaluator available for {control_code}",
                severity=severity,
                details={},
            )

    # =========================================================================
    # Dashboard
    # =========================================================================

    async def get_dashboard(
        self,
        project_id: UUID,
        db: AsyncSession,
    ) -> Dict[str, Any]:
        """
        Get MEASURE function dashboard data for a project.

        Aggregates latest evaluation results, metric statistics,
        bias group counts, and disparity summary.

        Args:
            project_id: UUID of the project.
            db: SQLAlchemy async database session.

        Returns:
            Dict with dashboard data.
        """
        logger.info("Fetching MEASURE dashboard for project %s", project_id)

        # Fetch latest assessment results for MEASURE controls
        policy_results = await self._fetch_latest_assessments(project_id, db)

        policies_passed = sum(1 for r in policy_results if r.allowed)
        policies_total = len(policy_results) if policy_results else len(MEASURE_POLICIES)
        compliance_pct = (
            (policies_passed / policies_total * 100.0) if policies_total > 0 else 0.0
        )

        # Metric stats
        total_metrics_result = await db.execute(
            select(func.count(PerformanceMetric.id)).where(
                PerformanceMetric.project_id == project_id
            )
        )
        total_metrics = total_metrics_result.scalar() or 0

        within_threshold_result = await db.execute(
            select(func.count(PerformanceMetric.id)).where(
                and_(
                    PerformanceMetric.project_id == project_id,
                    PerformanceMetric.is_within_threshold == True,
                )
            )
        )
        within_threshold = within_threshold_result.scalar() or 0

        # Distinct demographic groups
        groups_result = await db.execute(
            select(func.count(func.distinct(PerformanceMetric.demographic_group))).where(
                and_(
                    PerformanceMetric.project_id == project_id,
                    PerformanceMetric.demographic_group.isnot(None),
                )
            )
        )
        bias_groups_count = groups_result.scalar() or 0

        return {
            "project_id": str(project_id),
            "compliance_percentage": round(compliance_pct, 1),
            "policies_passed": policies_passed,
            "policies_total": policies_total,
            "policy_results": [r.model_dump() for r in policy_results],
            "total_metrics": total_metrics,
            "within_threshold": within_threshold,
            "bias_groups_count": bias_groups_count,
            "disparity_summary": {},
        }

    # =========================================================================
    # Metrics CRUD
    # =========================================================================

    async def list_metrics(
        self,
        project_id: UUID,
        ai_system_id: Optional[UUID],
        metric_type: Optional[str],
        limit: int,
        offset: int,
        db: AsyncSession,
    ) -> Tuple[List[PerformanceMetric], int]:
        """
        List performance metrics with optional filters and pagination.

        Args:
            project_id: UUID of the project.
            ai_system_id: Optional filter by AI system.
            metric_type: Optional filter by metric type.
            limit: Max results.
            offset: Skip count.
            db: Database session.

        Returns:
            Tuple of (metric list, total count).
        """
        conditions = [PerformanceMetric.project_id == project_id]
        if ai_system_id:
            conditions.append(PerformanceMetric.ai_system_id == ai_system_id)
        if metric_type:
            conditions.append(PerformanceMetric.metric_type == metric_type)

        # Count
        count_result = await db.execute(
            select(func.count(PerformanceMetric.id)).where(and_(*conditions))
        )
        total = count_result.scalar() or 0

        # Fetch
        query = (
            select(PerformanceMetric)
            .where(and_(*conditions))
            .order_by(PerformanceMetric.measured_at.desc())
            .limit(limit)
            .offset(offset)
        )
        result = await db.execute(query)
        items = list(result.scalars().all())

        return items, total

    async def create_metric(
        self,
        data: Dict[str, Any],
        user_id: Optional[UUID],
        db: AsyncSession,
    ) -> PerformanceMetric:
        """
        Create a single performance metric.

        Validates AI system exists, computes threshold status, and persists.

        Args:
            data: Metric data dict.
            user_id: ID of user recording the metric.
            db: Database session.

        Returns:
            Created PerformanceMetric.
        """
        # Validate AI system exists
        system_result = await db.execute(
            select(AISystem).where(
                and_(
                    AISystem.id == data["ai_system_id"],
                    AISystem.is_active == True,
                )
            )
        )
        system = system_result.scalar_one_or_none()
        if not system:
            raise MetricNotFoundError(
                f"AI system {data['ai_system_id']} not found or inactive"
            )

        # Compute threshold status
        value = data["metric_value"]
        threshold_min = data.get("threshold_min")
        threshold_max = data.get("threshold_max")
        is_within = True
        if threshold_min is not None and value < threshold_min:
            is_within = False
        if threshold_max is not None and value > threshold_max:
            is_within = False

        metric = PerformanceMetric(
            project_id=data["project_id"],
            ai_system_id=data["ai_system_id"],
            metric_type=data["metric_type"],
            metric_name=data["metric_name"],
            metric_value=value,
            threshold_min=threshold_min,
            threshold_max=threshold_max,
            is_within_threshold=is_within,
            unit=data.get("unit"),
            demographic_group=data.get("demographic_group"),
            tags=data.get("tags", []),
            measured_at=data["measured_at"],
            measured_by_id=user_id,
            notes=data.get("notes"),
        )

        db.add(metric)
        await db.commit()
        await db.refresh(metric)

        logger.info(
            "Created metric %s for system %s: %s=%s",
            metric.id, data["ai_system_id"], data["metric_name"], value,
        )
        return metric

    async def create_metrics_batch(
        self,
        project_id: UUID,
        metrics_data: List[Dict[str, Any]],
        user_id: Optional[UUID],
        db: AsyncSession,
    ) -> List[PerformanceMetric]:
        """
        Bulk create multiple performance metrics.

        Args:
            project_id: Project UUID.
            metrics_data: List of metric data dicts.
            user_id: ID of user recording the metrics.
            db: Database session.

        Returns:
            List of created PerformanceMetric objects.
        """
        created = []
        for data in metrics_data:
            data["project_id"] = project_id
            metric = await self.create_metric(data, user_id, db)
            created.append(metric)

        logger.info(
            "Batch created %d metrics for project %s", len(created), project_id
        )
        return created

    async def get_metric_trend(
        self,
        ai_system_id: UUID,
        metric_type: str,
        days: int,
        db: AsyncSession,
    ) -> List[Dict[str, Any]]:
        """
        Get metric trend data for a given system and metric type.

        Args:
            ai_system_id: UUID of the AI system.
            metric_type: Type of metric to trend.
            days: Number of days to look back.
            db: Database session.

        Returns:
            List of trend data points sorted by measured_at ascending.
        """
        cutoff = datetime.now(timezone.utc) - timedelta(days=days)

        query = (
            select(PerformanceMetric)
            .where(
                and_(
                    PerformanceMetric.ai_system_id == ai_system_id,
                    PerformanceMetric.metric_type == metric_type,
                    PerformanceMetric.measured_at >= cutoff,
                )
            )
            .order_by(PerformanceMetric.measured_at.asc())
        )
        result = await db.execute(query)
        metrics = list(result.scalars().all())

        return [
            {
                "measured_at": m.measured_at.isoformat() if m.measured_at else None,
                "metric_value": m.metric_value,
                "is_within_threshold": m.is_within_threshold,
            }
            for m in metrics
        ]

    async def get_bias_summary(
        self,
        project_id: UUID,
        db: AsyncSession,
    ) -> Dict[str, Any]:
        """
        Get bias/disparity summary for a project.

        Aggregates bias metrics grouped by (ai_system_id, demographic_group),
        computes disparity ratios between groups per system.

        Args:
            project_id: Project UUID.
            db: Database session.

        Returns:
            Dict with systems, bias metrics, and disparity ratios.
        """
        # Fetch AI systems
        systems_result = await db.execute(
            select(AISystem).where(
                and_(AISystem.project_id == project_id, AISystem.is_active == True)
            )
        )
        systems = list(systems_result.scalars().all())
        system_map = {s.id: s.name for s in systems}

        # Fetch bias metrics
        bias_result = await db.execute(
            select(PerformanceMetric).where(
                and_(
                    PerformanceMetric.project_id == project_id,
                    PerformanceMetric.metric_type.in_(["bias_score", "accuracy", "precision", "recall", "f1_score"]),
                    PerformanceMetric.demographic_group.isnot(None),
                )
            )
        )
        bias_metrics = list(bias_result.scalars().all())

        # Group by system → group → values
        system_groups: Dict[UUID, Dict[str, List[float]]] = defaultdict(lambda: defaultdict(list))
        for m in bias_metrics:
            system_groups[m.ai_system_id][m.demographic_group].append(m.metric_value)

        systems_output = []
        total_bias = len(bias_metrics)
        compliant = 0
        non_compliant = 0

        for system_id, groups in system_groups.items():
            group_summaries = []
            for group_name, values in groups.items():
                group_summaries.append({
                    "demographic_group": group_name,
                    "avg_score": round(sum(values) / len(values), 4) if values else 0,
                    "min_score": round(min(values), 4) if values else 0,
                    "max_score": round(max(values), 4) if values else 0,
                    "count": len(values),
                })

            # Compute disparity ratio (max avg / min avg across groups)
            avg_values = [
                sum(v) / len(v) for v in groups.values() if v
            ]
            disparity_ratio = None
            is_compliant = True
            if len(avg_values) >= 2:
                min_avg = min(avg_values)
                max_avg = max(avg_values)
                if min_avg > 0:
                    disparity_ratio = round(max_avg / min_avg, 4)
                    is_compliant = disparity_ratio <= DISPARITY_THRESHOLD

            if is_compliant:
                compliant += 1
            else:
                non_compliant += 1

            systems_output.append({
                "ai_system_id": str(system_id),
                "ai_system_name": system_map.get(system_id, "Unknown"),
                "groups": group_summaries,
                "disparity_ratio": disparity_ratio,
                "is_compliant": is_compliant,
            })

        return {
            "project_id": str(project_id),
            "systems": systems_output,
            "total_bias_metrics": total_bias,
            "compliant_systems": compliant,
            "non_compliant_systems": non_compliant,
        }

    # =========================================================================
    # In-Process Evaluators (Fallback)
    # =========================================================================

    def _evaluate_performance_thresholds(
        self, metrics_data: List[Dict]
    ) -> PolicyEvaluationResult:
        """In-process evaluator for MEASURE-1.1: Performance Thresholds."""
        if not metrics_data:
            return PolicyEvaluationResult(
                control_code="MEASURE-1.1",
                title="Performance Thresholds",
                allowed=False,
                reason="No performance metrics recorded",
                severity="high",
                details={"total_metrics": 0, "within_threshold": 0, "out_of_threshold": 0, "violations": []},
            )

        no_threshold = []
        violations = []
        within = 0

        for m in metrics_data:
            has_min = m.get("threshold_min") is not None
            has_max = m.get("threshold_max") is not None
            if not has_min and not has_max:
                no_threshold.append(m["metric_name"])
                continue

            value = m["metric_value"]
            in_bounds = True
            if has_min and value < m["threshold_min"]:
                in_bounds = False
            if has_max and value > m["threshold_max"]:
                in_bounds = False

            if in_bounds:
                within += 1
            else:
                violations.append(m["metric_name"])

        all_issues = no_threshold + violations
        allowed = len(all_issues) == 0

        return PolicyEvaluationResult(
            control_code="MEASURE-1.1",
            title="Performance Thresholds",
            allowed=allowed,
            reason=(
                "All metrics have thresholds and are within acceptable bounds"
                if allowed
                else f"Metrics without thresholds: {', '.join(no_threshold)}. Violations: {', '.join(violations)}"
            ),
            severity="high",
            details={
                "total_metrics": len(metrics_data),
                "within_threshold": within,
                "out_of_threshold": len(violations),
                "violations": all_issues,
            },
        )

    def _evaluate_bias_detection(
        self, metrics_data: List[Dict], ai_systems_data: List[Dict]
    ) -> PolicyEvaluationResult:
        """In-process evaluator for MEASURE-2.1: Bias Detection."""
        bias_metrics = [m for m in metrics_data if m.get("metric_type") == "bias_score"]

        if not bias_metrics or not ai_systems_data:
            return PolicyEvaluationResult(
                control_code="MEASURE-2.1",
                title="Bias Detection",
                allowed=False,
                reason="No bias metrics recorded or no AI systems registered",
                severity="critical",
                details={"systems_checked": 0, "systems_with_coverage": 0, "systems_lacking_coverage": [], "threshold_violations": []},
            )

        # Group bias metrics by system
        system_groups: Dict[str, set] = defaultdict(set)
        threshold_violations = []

        for m in bias_metrics:
            sid = m["ai_system_id"]
            group = m.get("demographic_group")
            if group:
                system_groups[sid].add(group)
            # Check threshold
            if m.get("threshold_max") is not None and m["metric_value"] > m["threshold_max"]:
                threshold_violations.append(m.get("metric_name", "unknown"))

        system_name_map = {s["id"]: s["name"] for s in ai_systems_data}
        lacking = []
        covered = 0

        for s in ai_systems_data:
            groups = system_groups.get(s["id"], set())
            if len(groups) >= 2:
                covered += 1
            else:
                lacking.append(s["name"])

        allowed = len(lacking) == 0 and len(threshold_violations) == 0

        return PolicyEvaluationResult(
            control_code="MEASURE-2.1",
            title="Bias Detection",
            allowed=allowed,
            reason=(
                "All AI systems have bias metrics for adequate demographic groups and all scores are within thresholds"
                if allowed
                else f"Systems lacking coverage: {', '.join(lacking)}. Threshold violations: {', '.join(threshold_violations)}"
            ),
            severity="critical",
            details={
                "systems_checked": len(ai_systems_data),
                "systems_with_coverage": covered,
                "systems_lacking_coverage": lacking,
                "threshold_violations": threshold_violations,
            },
        )

    def _evaluate_disparity_analysis(
        self, metrics_data: List[Dict], ai_systems_data: List[Dict]
    ) -> PolicyEvaluationResult:
        """In-process evaluator for MEASURE-2.2: Disparity Analysis (4/5ths rule)."""
        disparity_types = {"accuracy", "precision", "recall", "f1_score"}
        relevant = [
            m for m in metrics_data
            if m.get("metric_type") in disparity_types
            and m.get("demographic_group")
        ]

        if not relevant or not ai_systems_data:
            return PolicyEvaluationResult(
                control_code="MEASURE-2.2",
                title="Disparity Analysis",
                allowed=False,
                reason="No disparity metrics recorded or no AI systems registered",
                severity="critical",
                details={"systems_checked": 0, "compliant_systems": 0, "non_compliant_systems": [], "max_disparity_ratio": 0},
            )

        # Group by system → group → values
        system_groups: Dict[str, Dict[str, List[float]]] = defaultdict(lambda: defaultdict(list))
        for m in relevant:
            system_groups[m["ai_system_id"]][m["demographic_group"]].append(m["metric_value"])

        system_name_map = {s["id"]: s["name"] for s in ai_systems_data}
        non_compliant = []
        compliant_count = 0
        max_ratio = 0.0

        for sid, groups in system_groups.items():
            avg_values = [
                sum(vals) / len(vals) for vals in groups.values() if vals
            ]
            if len(avg_values) >= 2:
                min_val = min(avg_values)
                max_val = max(avg_values)
                if min_val > 0:
                    ratio = max_val / min_val
                    max_ratio = max(max_ratio, ratio)
                    if ratio > DISPARITY_THRESHOLD:
                        non_compliant.append(system_name_map.get(sid, sid))
                    else:
                        compliant_count += 1
                else:
                    compliant_count += 1
            else:
                compliant_count += 1

        allowed = len(non_compliant) == 0

        return PolicyEvaluationResult(
            control_code="MEASURE-2.2",
            title="Disparity Analysis",
            allowed=allowed,
            reason=(
                f"All AI systems have disparity ratio within {DISPARITY_THRESHOLD} threshold (4/5ths rule)"
                if allowed
                else f"Systems exceeding {DISPARITY_THRESHOLD} disparity threshold: {', '.join(non_compliant)} (max ratio: {max_ratio:.3f})"
            ),
            severity="critical",
            details={
                "systems_checked": len(ai_systems_data),
                "compliant_systems": compliant_count,
                "non_compliant_systems": non_compliant,
                "max_disparity_ratio": round(max_ratio, 4),
            },
        )

    async def _evaluate_metric_trending(
        self,
        project_id: UUID,
        db: AsyncSession,
    ) -> PolicyEvaluationResult:
        """
        In-process evaluator for MEASURE-3.1: Metric Trending.

        Checks that key metric types have >=3 data points per AI system.
        """
        # Get distinct (ai_system_id, metric_type) with counts
        query = (
            select(
                PerformanceMetric.ai_system_id,
                PerformanceMetric.metric_type,
                func.count(PerformanceMetric.id).label("data_points"),
            )
            .where(
                and_(
                    PerformanceMetric.project_id == project_id,
                    PerformanceMetric.metric_type.in_(KEY_METRIC_TYPES),
                )
            )
            .group_by(PerformanceMetric.ai_system_id, PerformanceMetric.metric_type)
        )
        result = await db.execute(query)
        rows = result.all()

        if not rows:
            return PolicyEvaluationResult(
                control_code="MEASURE-3.1",
                title="Metric Trending",
                allowed=False,
                reason="No key metrics recorded for trending analysis",
                severity="medium",
                details={"metrics_tracked": 0, "sufficient_trending": 0, "insufficient_trending": []},
            )

        sufficient = 0
        insufficient = []

        for row in rows:
            system_id, m_type, count = row
            if count >= 3:
                sufficient += 1
            else:
                insufficient.append(f"{m_type} (system {str(system_id)[:8]}..., {count} points)")

        allowed = len(insufficient) == 0

        return PolicyEvaluationResult(
            control_code="MEASURE-3.1",
            title="Metric Trending",
            allowed=allowed,
            reason=(
                "All key metrics have sufficient data points for trend analysis"
                if allowed
                else f"Metrics with insufficient data: {', '.join(insufficient[:5])}"
            ),
            severity="medium",
            details={
                "metrics_tracked": len(rows),
                "sufficient_trending": sufficient,
                "insufficient_trending": insufficient,
            },
        )

    # =========================================================================
    # Internal Helpers
    # =========================================================================

    async def _fetch_ai_systems(
        self, project_id: UUID, db: AsyncSession
    ) -> List[AISystem]:
        """Fetch active AI systems for a project."""
        result = await db.execute(
            select(AISystem).where(
                and_(AISystem.project_id == project_id, AISystem.is_active == True)
            )
        )
        return list(result.scalars().all())

    async def _fetch_all_metrics(
        self, project_id: UUID, db: AsyncSession
    ) -> List[PerformanceMetric]:
        """Fetch all performance metrics for a project."""
        result = await db.execute(
            select(PerformanceMetric).where(
                PerformanceMetric.project_id == project_id
            )
        )
        return list(result.scalars().all())

    async def _fetch_latest_assessments(
        self, project_id: UUID, db: AsyncSession
    ) -> List[PolicyEvaluationResult]:
        """Fetch latest assessment results for MEASURE controls."""
        # Get NIST framework
        fw_result = await db.execute(
            select(ComplianceFramework).where(ComplianceFramework.code == "NIST_AI_RMF")
        )
        framework = fw_result.scalar_one_or_none()
        if not framework:
            return []

        # Get MEASURE controls
        controls_result = await db.execute(
            select(ComplianceControl).where(
                and_(
                    ComplianceControl.framework_id == framework.id,
                    ComplianceControl.category == "MEASURE",
                )
            ).order_by(ComplianceControl.sort_order)
        )
        controls = list(controls_result.scalars().all())

        results = []
        for ctrl in controls:
            assessment_result = await db.execute(
                select(ComplianceAssessment).where(
                    and_(
                        ComplianceAssessment.project_id == project_id,
                        ComplianceAssessment.control_id == ctrl.id,
                    )
                )
            )
            assessment = assessment_result.scalar_one_or_none()

            if assessment and assessment.opa_result:
                opa_data = assessment.opa_result
                results.append(PolicyEvaluationResult(
                    control_code=ctrl.control_code,
                    title=ctrl.title,
                    allowed=opa_data.get("allowed", False),
                    reason=opa_data.get("reason", "Not evaluated"),
                    severity=ctrl.severity,
                    details=opa_data.get("details", {}),
                ))
            else:
                results.append(PolicyEvaluationResult(
                    control_code=ctrl.control_code,
                    title=ctrl.title,
                    allowed=False,
                    reason="Not yet evaluated",
                    severity=ctrl.severity,
                    details={},
                ))

        return results

    async def _persist_assessment_results(
        self,
        project_id: UUID,
        results: List[PolicyEvaluationResult],
        db: AsyncSession,
    ) -> None:
        """Persist evaluation results to compliance_assessments."""
        # Get NIST framework
        fw_result = await db.execute(
            select(ComplianceFramework).where(ComplianceFramework.code == "NIST_AI_RMF")
        )
        framework = fw_result.scalar_one_or_none()
        if not framework:
            logger.warning("NIST framework not found, skipping assessment persistence")
            return

        now = datetime.now(timezone.utc)

        for result in results:
            # Find control by code
            ctrl_result = await db.execute(
                select(ComplianceControl).where(
                    and_(
                        ComplianceControl.framework_id == framework.id,
                        ComplianceControl.control_code == result.control_code,
                    )
                )
            )
            ctrl = ctrl_result.scalar_one_or_none()
            if not ctrl:
                continue

            # Upsert assessment
            existing_result = await db.execute(
                select(ComplianceAssessment).where(
                    and_(
                        ComplianceAssessment.project_id == project_id,
                        ComplianceAssessment.control_id == ctrl.id,
                    )
                )
            )
            existing = existing_result.scalar_one_or_none()

            status = "compliant" if result.allowed else "non_compliant"
            opa_data = {
                "allowed": result.allowed,
                "reason": result.reason,
                "severity": result.severity,
                "details": result.details,
            }

            if existing:
                existing.status = status
                existing.opa_result = opa_data
                existing.auto_evaluated = True
                existing.assessed_at = now
            else:
                assessment = ComplianceAssessment(
                    project_id=project_id,
                    control_id=ctrl.id,
                    status=status,
                    auto_evaluated=True,
                    opa_result=opa_data,
                    assessed_at=now,
                )
                db.add(assessment)

        await db.commit()
        logger.info(
            "Persisted %d MEASURE assessment results for project %s",
            len(results), project_id,
        )
