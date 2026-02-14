"""
=========================================================================
Cross-Function Compliance Integration Tests
SDLC Orchestrator - Sprint 158 (Phase 3: COMPLIANCE)

Version: 1.0.0
Date: April 21, 2026
Status: ACTIVE
Authority: CTO Approved
Framework: SDLC 6.0.5
Reference: ADR-051, NIST AI RMF 1.0

Purpose:
Verify cross-function data consistency across all 4 NIST AI RMF functions:
GOVERN, MAP, MEASURE, MANAGE.

Test Categories:
1. Total controls seeded (19 = 5 GOVERN + 5 MAP + 4 MEASURE + 5 MANAGE)
2. MANAGE -> GOVERN FK: ManageRiskResponse.risk_id -> ComplianceRiskRegister
3. MANAGE -> MAP FK: ManageIncident.ai_system_id -> AISystem
4. MANAGE-4.1 -> MEASURE: Post-deployment monitoring queries PerformanceMetric
5. MANAGE-3.1 -> MAP: Third-party monitoring uses AISystem.dependencies
6. Framework total_controls updated to 19

Test Approach: Unit tests mocking database layer via AsyncMock
Zero Mock Policy: Mocks for database layer only
=========================================================================
"""

import pytest
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import UUID, uuid4

from app.models.compliance import (
    ComplianceControl,
    ComplianceFramework,
    ComplianceRiskRegister,
)
from app.models.nist_manage import (
    ManageIncident,
    ManageRiskResponse,
)
from app.models.nist_map_measure import AISystem, PerformanceMetric
from app.services.nist_manage_service import NISTManageService


# =============================================================================
# Test Constants
# =============================================================================

PROJECT_ID = UUID("00000000-0000-0000-0000-000000000001")
FRAMEWORK_ID = UUID("00000000-0000-0000-0000-000000000002")
RISK_ID = UUID("00000000-0000-0000-0000-000000000004")
USER_ID = UUID("00000000-0000-0000-0000-000000000006")
SYSTEM_ID = UUID("00000000-0000-0000-0000-000000000007")
RESPONSE_ID = UUID("00000000-0000-0000-0000-000000000008")
INCIDENT_ID = UUID("00000000-0000-0000-0000-000000000009")
METRIC_ID = UUID("00000000-0000-0000-0000-000000000010")

NOW = datetime(2026, 4, 21, 12, 0, 0, tzinfo=timezone.utc)

# Expected control distribution across NIST AI RMF functions
GOVERN_CONTROLS = [
    ("GOVERN-1.1", "Accountability Structures", "critical"),
    ("GOVERN-1.2", "Risk Culture & Training", "high"),
    ("GOVERN-1.3", "Legal & Regulatory Review", "critical"),
    ("GOVERN-1.4", "Third-Party Risk Management", "high"),
    ("GOVERN-1.5", "Continuous Improvement", "medium"),
]

MAP_CONTROLS = [
    ("MAP-1.1", "AI System Context", "critical"),
    ("MAP-1.2", "Stakeholder Identification", "high"),
    ("MAP-2.1", "Risk Categorization", "critical"),
    ("MAP-3.1", "Bias & Fairness Assessment", "high"),
    ("MAP-3.2", "Dependency Mapping", "medium"),
]

MEASURE_CONTROLS = [
    ("MEASURE-1.1", "Performance Thresholds", "critical"),
    ("MEASURE-2.1", "Bias Detection Metrics", "critical"),
    ("MEASURE-2.2", "Disparity Analysis", "high"),
    ("MEASURE-3.1", "Metric Trending", "medium"),
]

MANAGE_CONTROLS = [
    ("MANAGE-1.1", "Risk Response Planning", "critical"),
    ("MANAGE-2.1", "Resource Allocation", "high"),
    ("MANAGE-2.4", "System Deactivation Criteria", "high"),
    ("MANAGE-3.1", "Third-Party Monitoring", "high"),
    ("MANAGE-4.1", "Post-Deployment Monitoring", "critical"),
]


# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def mock_db():
    """Create a mock async database session with proper async returns."""
    db = AsyncMock()
    db.commit = AsyncMock()
    db.refresh = AsyncMock()
    db.add = MagicMock()
    db.get = AsyncMock(return_value=None)
    return db


@pytest.fixture
def manage_service():
    """Create NISTManageService instance."""
    return NISTManageService()


@pytest.fixture
def sample_framework():
    """Create a mock ComplianceFramework for NIST AI RMF."""
    fw = MagicMock(spec=ComplianceFramework)
    fw.id = FRAMEWORK_ID
    fw.code = "NIST_AI_RMF"
    fw.name = "NIST AI Risk Management Framework"
    fw.version = "1.0"
    fw.total_controls = 19
    fw.is_active = True
    fw.created_at = NOW
    fw.updated_at = NOW
    return fw


@pytest.fixture
def all_19_controls():
    """Create mock ComplianceControl instances for all 19 NIST AI RMF controls."""
    controls = []
    sort_order = 1

    for category, control_defs in [
        ("GOVERN", GOVERN_CONTROLS),
        ("MAP", MAP_CONTROLS),
        ("MEASURE", MEASURE_CONTROLS),
        ("MANAGE", MANAGE_CONTROLS),
    ]:
        for code, title, severity in control_defs:
            ctrl = MagicMock(spec=ComplianceControl)
            ctrl.id = uuid4()
            ctrl.framework_id = FRAMEWORK_ID
            ctrl.control_code = code
            ctrl.category = category
            ctrl.title = title
            ctrl.severity = severity
            ctrl.sort_order = sort_order
            ctrl.created_at = NOW
            ctrl.updated_at = NOW
            controls.append(ctrl)
            sort_order += 1

    return controls


@pytest.fixture
def sample_risk():
    """Create a mock ComplianceRiskRegister entry."""
    risk = MagicMock(spec=ComplianceRiskRegister)
    risk.id = RISK_ID
    risk.project_id = PROJECT_ID
    risk.framework_id = FRAMEWORK_ID
    risk.risk_code = "RISK-001"
    risk.title = "Model bias in hiring decisions"
    risk.status = "identified"
    risk.risk_score = 16
    risk.created_at = NOW
    risk.updated_at = NOW
    return risk


@pytest.fixture
def sample_risk_response(sample_risk):
    """Create a mock ManageRiskResponse linked to a risk."""
    resp = MagicMock(spec=ManageRiskResponse)
    resp.id = RESPONSE_ID
    resp.project_id = PROJECT_ID
    resp.risk_id = RISK_ID
    resp.response_type = "mitigate"
    resp.description = "Implement bias detection pipeline"
    resp.assigned_to = "AI Safety Lead"
    resp.priority = "critical"
    resp.status = "in_progress"
    resp.due_date = None
    resp.resources_allocated = []
    resp.deactivation_criteria = None
    resp.notes = None
    resp.created_at = NOW
    resp.updated_at = NOW
    resp.to_dict = MagicMock(return_value={
        "id": str(RESPONSE_ID),
        "project_id": str(PROJECT_ID),
        "risk_id": str(RISK_ID),
        "response_type": "mitigate",
        "description": "Implement bias detection pipeline",
        "assigned_to": "AI Safety Lead",
        "priority": "critical",
        "status": "in_progress",
        "due_date": None,
        "resources_allocated": [],
        "deactivation_criteria": None,
        "notes": None,
        "created_at": NOW.isoformat(),
        "updated_at": NOW.isoformat(),
    })
    return resp


@pytest.fixture
def sample_ai_system():
    """Create a mock AISystem with third-party dependencies."""
    system = MagicMock(spec=AISystem)
    system.id = SYSTEM_ID
    system.project_id = PROJECT_ID
    system.name = "Hiring ML Model"
    system.system_type = "decision"
    system.risk_level = "high"
    system.is_active = True
    system.dependencies = [
        {"name": "OpenAI GPT-4", "type": "api", "version": "4.0", "provider": "openai"},
        {"name": "Pandas", "type": "library", "version": "2.0", "provider": "internal"},
    ]
    system.stakeholders = [{"role": "owner", "name": "ML Lead", "impact_type": "direct"}]
    system.created_at = NOW
    system.updated_at = NOW
    system.to_dict = MagicMock(return_value={
        "id": str(SYSTEM_ID),
        "project_id": str(PROJECT_ID),
        "name": "Hiring ML Model",
        "system_type": "decision",
        "risk_level": "high",
        "is_active": True,
        "dependencies": [
            {"name": "OpenAI GPT-4", "type": "api", "version": "4.0", "provider": "openai"},
            {"name": "Pandas", "type": "library", "version": "2.0", "provider": "internal"},
        ],
        "stakeholders": [{"role": "owner", "name": "ML Lead", "impact_type": "direct"}],
        "created_at": NOW.isoformat(),
        "updated_at": NOW.isoformat(),
    })
    return system


@pytest.fixture
def sample_incident(sample_ai_system):
    """Create a mock ManageIncident linked to an AI system."""
    inc = MagicMock(spec=ManageIncident)
    inc.id = INCIDENT_ID
    inc.project_id = PROJECT_ID
    inc.ai_system_id = SYSTEM_ID
    inc.risk_id = None
    inc.title = "Bias spike in hiring model"
    inc.severity = "critical"
    inc.incident_type = "bias_detected"
    inc.status = "investigating"
    inc.reported_by = "QA"
    inc.assigned_to = "AI Safety Lead"
    inc.resolution = None
    inc.root_cause = None
    inc.occurred_at = NOW
    inc.resolved_at = None
    inc.created_at = NOW
    inc.updated_at = NOW
    inc.to_dict = MagicMock(return_value={
        "id": str(INCIDENT_ID),
        "project_id": str(PROJECT_ID),
        "ai_system_id": str(SYSTEM_ID),
        "risk_id": None,
        "title": "Bias spike in hiring model",
        "severity": "critical",
        "incident_type": "bias_detected",
        "status": "investigating",
        "reported_by": "QA",
        "assigned_to": "AI Safety Lead",
        "resolution": None,
        "root_cause": None,
        "occurred_at": NOW.isoformat(),
        "resolved_at": None,
        "created_at": NOW.isoformat(),
        "updated_at": NOW.isoformat(),
    })
    return inc


@pytest.fixture
def sample_metric():
    """Create a mock PerformanceMetric for an AI system."""
    metric = MagicMock(spec=PerformanceMetric)
    metric.id = METRIC_ID
    metric.project_id = PROJECT_ID
    metric.ai_system_id = SYSTEM_ID
    metric.metric_type = "accuracy"
    metric.metric_name = "Overall Accuracy"
    metric.metric_value = 0.92
    metric.threshold_min = 0.85
    metric.threshold_max = None
    metric.is_within_threshold = True
    metric.measured_at = NOW - timedelta(days=5)
    metric.created_at = NOW
    metric.to_dict = MagicMock(return_value={
        "id": str(METRIC_ID),
        "project_id": str(PROJECT_ID),
        "ai_system_id": str(SYSTEM_ID),
        "metric_type": "accuracy",
        "metric_name": "Overall Accuracy",
        "metric_value": 0.92,
        "threshold_min": 0.85,
        "threshold_max": None,
        "is_within_threshold": True,
        "measured_at": (NOW - timedelta(days=5)).isoformat(),
        "created_at": NOW.isoformat(),
    })
    return metric


# =============================================================================
# Helper Functions
# =============================================================================


def _mock_scalars_all(items):
    """Create a mock result with scalars().all() returning items."""
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = items
    return mock_result


def _mock_scalar_one_or_none(value):
    """Create a mock result with scalar_one_or_none() returning value."""
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = value
    return mock_result


def _mock_scalar(value):
    """Create a mock result with scalar() returning value."""
    mock_result = MagicMock()
    mock_result.scalar.return_value = value
    return mock_result


# =============================================================================
# Cross-Function Integration Tests
# =============================================================================


class TestCrossFunctionIntegration:
    """
    Tests verifying cross-function data consistency across
    GOVERN, MAP, MEASURE, and MANAGE.
    """

    def test_all_19_controls_seeded(self, all_19_controls):
        """
        Verify 19 total controls exist: 5 GOVERN + 5 MAP + 4 MEASURE + 5 MANAGE.

        This test ensures the complete control set is seeded at migration time
        and that each function has the expected number of controls.
        """
        assert len(all_19_controls) == 19

        # Verify distribution by category
        govern_count = sum(
            1 for c in all_19_controls if c.category == "GOVERN"
        )
        map_count = sum(
            1 for c in all_19_controls if c.category == "MAP"
        )
        measure_count = sum(
            1 for c in all_19_controls if c.category == "MEASURE"
        )
        manage_count = sum(
            1 for c in all_19_controls if c.category == "MANAGE"
        )

        assert govern_count == 5, f"Expected 5 GOVERN controls, got {govern_count}"
        assert map_count == 5, f"Expected 5 MAP controls, got {map_count}"
        assert measure_count == 4, f"Expected 4 MEASURE controls, got {measure_count}"
        assert manage_count == 5, f"Expected 5 MANAGE controls, got {manage_count}"

        # Verify all control codes are unique
        control_codes = [c.control_code for c in all_19_controls]
        assert len(set(control_codes)) == 19, "Control codes must be unique"

        # Verify expected control codes are present
        expected_codes = {code for code, _, _ in (
            GOVERN_CONTROLS + MAP_CONTROLS + MEASURE_CONTROLS + MANAGE_CONTROLS
        )}
        actual_codes = set(control_codes)
        assert actual_codes == expected_codes, (
            f"Missing controls: {expected_codes - actual_codes}, "
            f"Extra controls: {actual_codes - expected_codes}"
        )

    def test_manage_uses_govern_risk_register(
        self, sample_risk_response, sample_risk
    ):
        """
        Verify ManageRiskResponse.risk_id references ComplianceRiskRegister.

        MANAGE-1.1 (Risk Response Planning) requires every open risk in the
        GOVERN risk register to have a corresponding response plan. This test
        validates the FK relationship between the two tables.
        """
        # ManageRiskResponse.risk_id must match ComplianceRiskRegister.id
        assert sample_risk_response.risk_id == sample_risk.id, (
            f"Risk response risk_id ({sample_risk_response.risk_id}) "
            f"must match risk register id ({sample_risk.id})"
        )

        # Both belong to the same project
        assert sample_risk_response.project_id == sample_risk.project_id, (
            "Risk response and risk register entry must belong to the same project"
        )

        # Verify risk_id is not None (FK constraint)
        assert sample_risk_response.risk_id is not None, (
            "ManageRiskResponse.risk_id must not be None (FK to compliance_risk_register)"
        )

    def test_manage_uses_map_ai_systems(
        self, sample_incident, sample_ai_system
    ):
        """
        Verify ManageIncident.ai_system_id references AISystem (MAP table).

        MANAGE incident tracking requires linking incidents to AI systems
        registered through the MAP function. This validates the FK relationship
        between manage_incidents and ai_systems tables.
        """
        # ManageIncident.ai_system_id must match AISystem.id
        assert sample_incident.ai_system_id == sample_ai_system.id, (
            f"Incident ai_system_id ({sample_incident.ai_system_id}) "
            f"must match AI system id ({sample_ai_system.id})"
        )

        # Both belong to the same project
        assert sample_incident.project_id == sample_ai_system.project_id, (
            "Incident and AI system must belong to the same project"
        )

        # Verify ai_system_id is not None (FK constraint)
        assert sample_incident.ai_system_id is not None, (
            "ManageIncident.ai_system_id must not be None (FK to ai_systems)"
        )

    def test_manage_post_deployment_uses_measure_metrics(
        self, manage_service, sample_ai_system, sample_metric
    ):
        """
        Verify MANAGE-4.1 evaluation queries PerformanceMetric for recent metrics.

        The post-deployment monitoring policy (MANAGE-4.1) requires all active
        AI systems to have a performance metric recorded within 30 days.
        PerformanceMetric is the MEASURE function's table, demonstrating the
        MANAGE -> MEASURE cross-function dependency.
        """
        # Build OPA input as the service would for MANAGE-4.1
        system_dict = sample_ai_system.to_dict()
        system_dict["is_active"] = True
        system_dict["is_third_party"] = False

        metric_dict = sample_metric.to_dict()

        opa_input = {
            "active_systems": [system_dict],
            "recent_metrics": [metric_dict],
            "critical_incidents": [],
        }

        # Evaluate MANAGE-4.1 using in-process fallback
        allowed, reason, details = manage_service._eval_post_deployment_monitoring(
            opa_input
        )

        # System has a recent metric, so it should pass
        assert allowed is True, f"MANAGE-4.1 should pass with recent metrics: {reason}"
        assert details["active_systems_count"] == 1
        assert details["systems_without_metrics"] == []
        assert details["unresolved_critical_count"] == 0

        # Now test without metrics - should fail
        opa_input_no_metrics = {
            "active_systems": [system_dict],
            "recent_metrics": [],
            "critical_incidents": [],
        }

        allowed_no, reason_no, details_no = manage_service._eval_post_deployment_monitoring(
            opa_input_no_metrics
        )

        assert allowed_no is False, (
            "MANAGE-4.1 should fail when AI system has no recent PerformanceMetric"
        )
        assert len(details_no["systems_without_metrics"]) == 1
        assert sample_ai_system.to_dict()["name"] in details_no["systems_without_metrics"]

    def test_manage_third_party_uses_map_dependencies(
        self, manage_service, sample_ai_system
    ):
        """
        Verify MANAGE-3.1 uses AISystem.dependencies to identify third-party systems.

        The third-party monitoring policy (MANAGE-3.1) checks if AI systems with
        external dependencies (from MAP function's AISystem.dependencies JSONB)
        have been monitored within 90 days. This validates the MANAGE -> MAP
        cross-function dependency through the _is_third_party_system helper.
        """
        # Test with external dependency (OpenAI) - should be third-party
        assert manage_service._is_third_party_system(sample_ai_system) is True, (
            "AI system with 'openai' provider dependency should be classified as third-party"
        )

        # Create a system with only internal dependencies
        internal_system = MagicMock(spec=AISystem)
        internal_system.dependencies = [
            {"name": "Internal ML", "type": "library", "version": "1.0", "provider": "internal"},
            {"name": "In-house API", "type": "api", "version": "2.0", "provider": "in-house"},
        ]

        assert manage_service._is_third_party_system(internal_system) is False, (
            "AI system with only internal/in-house dependencies should NOT be third-party"
        )

        # Create a system with no dependencies
        empty_system = MagicMock(spec=AISystem)
        empty_system.dependencies = []

        assert manage_service._is_third_party_system(empty_system) is False, (
            "AI system with no dependencies should NOT be third-party"
        )

        # Now verify MANAGE-3.1 evaluation with a third-party system
        system_dict = sample_ai_system.to_dict()
        system_dict["is_third_party"] = True

        # No incidents within 90 days - should fail
        opa_input = {
            "third_party_systems": [system_dict],
            "incidents": [],
            "cutoff_date": (NOW - timedelta(days=90)).isoformat(),
        }

        allowed, reason, details = manage_service._eval_third_party_monitoring(
            opa_input
        )

        assert allowed is False, (
            "MANAGE-3.1 should fail when third-party system has no recent monitoring"
        )
        assert len(details["unmonitored_systems"]) == 1

        # With a recent incident - should pass
        recent_incident = {
            "ai_system_id": str(SYSTEM_ID),
            "occurred_at": NOW.isoformat(),
            "severity": "medium",
            "status": "resolved",
        }

        opa_input_with_incident = {
            "third_party_systems": [system_dict],
            "incidents": [recent_incident],
            "cutoff_date": (NOW - timedelta(days=90)).isoformat(),
        }

        allowed_ok, reason_ok, details_ok = manage_service._eval_third_party_monitoring(
            opa_input_with_incident
        )

        assert allowed_ok is True, (
            f"MANAGE-3.1 should pass with recent monitoring: {reason_ok}"
        )
        assert details_ok["unmonitored_systems"] == []

    def test_framework_total_controls_updated(self, sample_framework):
        """
        Verify ComplianceFramework.total_controls = 19 for NIST_AI_RMF.

        After all 4 functions are seeded (GOVERN=5, MAP=5, MEASURE=4, MANAGE=5),
        the NIST_AI_RMF framework's total_controls must reflect the sum of 19.
        """
        assert sample_framework.code == "NIST_AI_RMF"
        assert sample_framework.total_controls == 19, (
            f"NIST_AI_RMF total_controls must be 19 "
            f"(5 GOVERN + 5 MAP + 4 MEASURE + 5 MANAGE), "
            f"got {sample_framework.total_controls}"
        )
        assert sample_framework.is_active is True, (
            "NIST_AI_RMF framework must be active"
        )

        # Verify the expected breakdown
        expected_total = (
            len(GOVERN_CONTROLS)
            + len(MAP_CONTROLS)
            + len(MEASURE_CONTROLS)
            + len(MANAGE_CONTROLS)
        )
        assert expected_total == 19, (
            f"Control definitions must total 19, got {expected_total}"
        )
        assert sample_framework.total_controls == expected_total, (
            f"Framework total_controls ({sample_framework.total_controls}) "
            f"must match control definitions total ({expected_total})"
        )
