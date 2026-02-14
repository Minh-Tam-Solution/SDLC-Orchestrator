"""
=========================================================================
NIST MANAGE Service Unit Tests
SDLC Orchestrator - Sprint 158 (Phase 3: COMPLIANCE)

Version: 1.0.0
Date: February 5, 2026
Status: ACTIVE
Authority: CTO Approved
Framework: SDLC 6.0.5

Test Categories:
- MANAGE Evaluation Tests (all pass, partial fail, no risks, OPA fallback,
    persist assessments, error handling)
- MANAGE Dashboard Tests (with data, empty project, deactivation)
- Risk Response CRUD Tests (list, create, create with deactivation,
    update, update not found, status filter)
- Incident CRUD Tests (list, create, create with risk_id, update,
    update not found, system filter)
- Policy Evaluation Tests (5 individual in-process evaluators)
- Third-Party Identification Tests (external vs internal)

Test Approach: Unit tests mocking database layer via AsyncMock
Zero Mock Policy: Mocks for database layer only
=========================================================================
"""

import pytest
from datetime import datetime, date, timezone
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import UUID, uuid4

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
from app.models.nist_map_measure import AISystem
from app.schemas.compliance_framework import PolicyEvaluationResult
from app.services.nist_manage_service import (
    IncidentNotFoundError,
    MANAGE_POLICIES,
    NISTManageEvaluationError,
    NISTManageService,
    RiskResponseNotFoundError,
)


# =============================================================================
# Test Constants
# =============================================================================

PROJECT_ID = UUID("00000000-0000-0000-0000-000000000001")
FRAMEWORK_ID = UUID("00000000-0000-0000-0000-000000000002")
RISK_ID = UUID("00000000-0000-0000-0000-000000000003")
RESPONSE_ID = UUID("00000000-0000-0000-0000-000000000004")
INCIDENT_ID = UUID("00000000-0000-0000-0000-000000000005")
SYSTEM_ID = UUID("00000000-0000-0000-0000-000000000006")
USER_ID = UUID("00000000-0000-0000-0000-000000000007")
NOW = datetime(2026, 4, 21, 12, 0, 0, tzinfo=timezone.utc)


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
def service():
    """Create NISTManageService instance."""
    return NISTManageService()


@pytest.fixture
def sample_risk_response():
    """Create a mock ManageRiskResponse model instance."""
    resp = MagicMock(spec=ManageRiskResponse)
    resp.id = RESPONSE_ID
    resp.project_id = PROJECT_ID
    resp.risk_id = RISK_ID
    resp.response_type = ResponseType.MITIGATE.value
    resp.description = "Implement bias detection pipeline"
    resp.assigned_to = "ml-team"
    resp.priority = "high"
    resp.status = ResponseStatus.PLANNED.value
    resp.due_date = date(2026, 6, 1)
    resp.resources_allocated = [
        {"type": "compute", "description": "GPU cluster", "budget": 5000}
    ]
    resp.deactivation_criteria = None
    resp.notes = None
    resp.created_at = NOW
    resp.updated_at = NOW
    resp.to_dict.return_value = {
        "id": str(RESPONSE_ID),
        "project_id": str(PROJECT_ID),
        "risk_id": str(RISK_ID),
        "response_type": ResponseType.MITIGATE.value,
        "description": "Implement bias detection pipeline",
        "assigned_to": "ml-team",
        "priority": "high",
        "status": ResponseStatus.PLANNED.value,
        "due_date": "2026-06-01",
        "resources_allocated": [
            {"type": "compute", "description": "GPU cluster", "budget": 5000}
        ],
        "deactivation_criteria": None,
        "notes": None,
        "created_at": NOW.isoformat(),
        "updated_at": NOW.isoformat(),
    }
    return resp


@pytest.fixture
def sample_incident():
    """Create a mock ManageIncident model instance."""
    inc = MagicMock(spec=ManageIncident)
    inc.id = INCIDENT_ID
    inc.project_id = PROJECT_ID
    inc.ai_system_id = SYSTEM_ID
    inc.risk_id = None
    inc.title = "Model accuracy degradation"
    inc.description = "Chatbot accuracy dropped below 80%"
    inc.severity = IncidentSeverity.HIGH.value
    inc.incident_type = "performance_degradation"
    inc.status = IncidentStatus.OPEN.value
    inc.reported_by = "monitoring-system"
    inc.assigned_to = "ml-team"
    inc.resolution = None
    inc.root_cause = None
    inc.occurred_at = NOW
    inc.resolved_at = None
    inc.created_at = NOW
    inc.updated_at = NOW
    inc.to_dict.return_value = {
        "id": str(INCIDENT_ID),
        "project_id": str(PROJECT_ID),
        "ai_system_id": str(SYSTEM_ID),
        "risk_id": None,
        "title": "Model accuracy degradation",
        "description": "Chatbot accuracy dropped below 80%",
        "severity": IncidentSeverity.HIGH.value,
        "incident_type": "performance_degradation",
        "status": IncidentStatus.OPEN.value,
        "reported_by": "monitoring-system",
        "assigned_to": "ml-team",
        "resolution": None,
        "root_cause": None,
        "occurred_at": NOW.isoformat(),
        "resolved_at": None,
        "created_at": NOW.isoformat(),
        "updated_at": NOW.isoformat(),
    }
    return inc


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
# MANAGE Evaluation Tests
# =============================================================================


class TestEvaluateManage:
    """Tests for NISTManageService.evaluate_manage."""

    @pytest.mark.asyncio
    async def test_evaluate_manage_all_pass(self, service, mock_db):
        """Test evaluation where all 5 MANAGE policies pass."""
        with patch.object(
            service,
            "_fetch_risk_responses",
            new_callable=AsyncMock,
            return_value=[],
        ), patch.object(
            service,
            "_fetch_incidents",
            new_callable=AsyncMock,
            return_value=[],
        ), patch.object(
            service,
            "_fetch_ai_systems",
            new_callable=AsyncMock,
            return_value=[],
        ), patch.object(
            service,
            "_fetch_recent_metrics",
            new_callable=AsyncMock,
            return_value=[],
        ), patch.object(
            service,
            "_fetch_open_risks",
            new_callable=AsyncMock,
            return_value=[],
        ), patch.object(
            service,
            "_evaluate_single_policy",
            new_callable=AsyncMock,
        ) as mock_eval, patch.object(
            service,
            "_persist_assessment_results",
            new_callable=AsyncMock,
        ):
            mock_eval.side_effect = [
                PolicyEvaluationResult(
                    control_code=p["control_code"],
                    title=p["title"],
                    allowed=True,
                    reason="Passed",
                    severity=p["severity"],
                )
                for p in MANAGE_POLICIES
            ]

            result = await service.evaluate_manage(PROJECT_ID, mock_db)

            assert result["overall_compliant"] is True
            assert result["policies_passed"] == 5
            assert result["policies_total"] == 5
            assert result["compliance_percentage"] == 100.0
            assert result["framework_code"] == "NIST_AI_RMF"
            assert result["function"] == "MANAGE"

    @pytest.mark.asyncio
    async def test_evaluate_manage_partial_fail(self, service, mock_db):
        """Test evaluation where some MANAGE policies fail."""
        with patch.object(
            service,
            "_fetch_risk_responses",
            new_callable=AsyncMock,
            return_value=[],
        ), patch.object(
            service,
            "_fetch_incidents",
            new_callable=AsyncMock,
            return_value=[],
        ), patch.object(
            service,
            "_fetch_ai_systems",
            new_callable=AsyncMock,
            return_value=[],
        ), patch.object(
            service,
            "_fetch_recent_metrics",
            new_callable=AsyncMock,
            return_value=[],
        ), patch.object(
            service,
            "_fetch_open_risks",
            new_callable=AsyncMock,
            return_value=[],
        ), patch.object(
            service,
            "_evaluate_single_policy",
            new_callable=AsyncMock,
        ) as mock_eval, patch.object(
            service,
            "_persist_assessment_results",
            new_callable=AsyncMock,
        ):
            mock_eval.side_effect = [
                PolicyEvaluationResult(
                    control_code="MANAGE-1.1",
                    title="Risk Response Planning",
                    allowed=False,
                    reason="2 open risk(s) lack a response plan",
                    severity="critical",
                ),
                PolicyEvaluationResult(
                    control_code="MANAGE-2.1",
                    title="Resource Allocation",
                    allowed=True,
                    reason="Meets 50% threshold.",
                    severity="high",
                ),
                PolicyEvaluationResult(
                    control_code="MANAGE-2.4",
                    title="System Deactivation Criteria",
                    allowed=False,
                    reason="No risk responses define deactivation criteria",
                    severity="high",
                ),
                PolicyEvaluationResult(
                    control_code="MANAGE-3.1",
                    title="Third-Party Monitoring",
                    allowed=True,
                    reason="All third-party systems monitored.",
                    severity="high",
                ),
                PolicyEvaluationResult(
                    control_code="MANAGE-4.1",
                    title="Post-Deployment Monitoring",
                    allowed=False,
                    reason="1 system(s) lack performance metrics",
                    severity="critical",
                ),
            ]

            result = await service.evaluate_manage(PROJECT_ID, mock_db)

            assert result["overall_compliant"] is False
            assert result["policies_passed"] == 2
            assert result["policies_total"] == 5
            assert result["compliance_percentage"] == 40.0

    @pytest.mark.asyncio
    async def test_evaluate_manage_no_risks(self, service, mock_db):
        """Test evaluation with empty project (no risks, no responses)."""
        with patch.object(
            service,
            "_fetch_risk_responses",
            new_callable=AsyncMock,
            return_value=[],
        ), patch.object(
            service,
            "_fetch_incidents",
            new_callable=AsyncMock,
            return_value=[],
        ), patch.object(
            service,
            "_fetch_ai_systems",
            new_callable=AsyncMock,
            return_value=[],
        ), patch.object(
            service,
            "_fetch_recent_metrics",
            new_callable=AsyncMock,
            return_value=[],
        ), patch.object(
            service,
            "_fetch_open_risks",
            new_callable=AsyncMock,
            return_value=[],
        ), patch.object(
            service,
            "_evaluate_via_opa",
            new_callable=AsyncMock,
            return_value=None,
        ), patch.object(
            service,
            "_persist_assessment_results",
            new_callable=AsyncMock,
        ):
            result = await service.evaluate_manage(PROJECT_ID, mock_db)

            assert isinstance(result, dict)
            assert result["policies_total"] == 5
            # With no data, MANAGE-1.1 passes (no open risks),
            # MANAGE-2.1 passes (no non-accept), MANAGE-2.4 fails (no responses),
            # MANAGE-3.1 passes (no third-party), MANAGE-4.1 passes (no active)
            assert result["policies_passed"] == 4
            assert result["overall_compliant"] is False

    @pytest.mark.asyncio
    async def test_evaluate_manage_opa_fallback(self, service, mock_db):
        """Test evaluation falls back to in-process when OPA unavailable."""
        risk_responses = [
            {
                "id": str(uuid4()),
                "risk_id": str(RISK_ID),
                "response_type": "mitigate",
                "assigned_to": "ml-team",
                "due_date": "2026-06-01",
                "resources_allocated": [{"budget": 5000}],
                "deactivation_criteria": {
                    "conditions": ["accuracy below 70%"],
                    "threshold": 0.7,
                    "action": "deactivate",
                },
            },
        ]
        risks = [
            {
                "id": str(RISK_ID),
                "risk_code": "RISK-001",
                "title": "Model bias",
                "status": "identified",
                "risk_score": 16,
            },
        ]

        with patch.object(
            service,
            "_fetch_risk_responses",
            new_callable=AsyncMock,
            return_value=risk_responses,
        ), patch.object(
            service,
            "_fetch_incidents",
            new_callable=AsyncMock,
            return_value=[],
        ), patch.object(
            service,
            "_fetch_ai_systems",
            new_callable=AsyncMock,
            return_value=[],
        ), patch.object(
            service,
            "_fetch_recent_metrics",
            new_callable=AsyncMock,
            return_value=[],
        ), patch.object(
            service,
            "_fetch_open_risks",
            new_callable=AsyncMock,
            return_value=risks,
        ), patch.object(
            service,
            "_evaluate_via_opa",
            new_callable=AsyncMock,
            return_value=None,
        ), patch.object(
            service,
            "_persist_assessment_results",
            new_callable=AsyncMock,
        ):
            result = await service.evaluate_manage(PROJECT_ID, mock_db)

            assert isinstance(result, dict)
            assert "overall_compliant" in result
            assert "policies_passed" in result
            assert result["policies_total"] == 5

    @pytest.mark.asyncio
    async def test_evaluate_manage_persists_assessments(self, service, mock_db):
        """Test evaluation persists assessment results to database."""
        with patch.object(
            service,
            "_fetch_risk_responses",
            new_callable=AsyncMock,
            return_value=[],
        ), patch.object(
            service,
            "_fetch_incidents",
            new_callable=AsyncMock,
            return_value=[],
        ), patch.object(
            service,
            "_fetch_ai_systems",
            new_callable=AsyncMock,
            return_value=[],
        ), patch.object(
            service,
            "_fetch_recent_metrics",
            new_callable=AsyncMock,
            return_value=[],
        ), patch.object(
            service,
            "_fetch_open_risks",
            new_callable=AsyncMock,
            return_value=[],
        ), patch.object(
            service,
            "_evaluate_single_policy",
            new_callable=AsyncMock,
        ) as mock_eval, patch.object(
            service,
            "_persist_assessment_results",
            new_callable=AsyncMock,
        ) as mock_persist:
            mock_eval.side_effect = [
                PolicyEvaluationResult(
                    control_code=p["control_code"],
                    title=p["title"],
                    allowed=True,
                    reason="Passed",
                    severity=p["severity"],
                )
                for p in MANAGE_POLICIES
            ]

            await service.evaluate_manage(PROJECT_ID, mock_db)

            mock_persist.assert_awaited_once()
            call_args = mock_persist.call_args
            assert call_args.kwargs["project_id"] == PROJECT_ID
            assert len(call_args.kwargs["results"]) == 5
            assert call_args.kwargs["db"] is mock_db

    @pytest.mark.asyncio
    async def test_evaluate_manage_error_handling(self, service, mock_db):
        """Test evaluation raises NISTManageEvaluationError on failure."""
        with patch.object(
            service,
            "_fetch_risk_responses",
            new_callable=AsyncMock,
            return_value=[],
        ), patch.object(
            service,
            "_fetch_incidents",
            new_callable=AsyncMock,
            return_value=[],
        ), patch.object(
            service,
            "_fetch_ai_systems",
            new_callable=AsyncMock,
            return_value=[],
        ), patch.object(
            service,
            "_fetch_recent_metrics",
            new_callable=AsyncMock,
            return_value=[],
        ), patch.object(
            service,
            "_fetch_open_risks",
            new_callable=AsyncMock,
            return_value=[],
        ), patch.object(
            service,
            "_evaluate_single_policy",
            new_callable=AsyncMock,
            side_effect=RuntimeError("Unexpected evaluation failure"),
        ):
            with pytest.raises(NISTManageEvaluationError, match="Failed to evaluate"):
                await service.evaluate_manage(PROJECT_ID, mock_db)


# =============================================================================
# Dashboard Tests
# =============================================================================


class TestGetDashboard:
    """Tests for NISTManageService.get_dashboard."""

    @pytest.mark.asyncio
    async def test_get_dashboard_with_data(self, service, mock_db):
        """Test dashboard returns correctly aggregated data."""
        with patch.object(
            service,
            "_fetch_latest_assessments",
            new_callable=AsyncMock,
        ) as mock_fetch, patch.object(
            service,
            "_get_response_stats",
            new_callable=AsyncMock,
        ) as mock_response_stats, patch.object(
            service,
            "_get_incident_stats",
            new_callable=AsyncMock,
        ) as mock_incident_stats, patch.object(
            service,
            "_has_deactivation_criteria",
            new_callable=AsyncMock,
        ) as mock_deactivation:
            mock_fetch.return_value = [
                PolicyEvaluationResult(
                    control_code="MANAGE-1.1",
                    title="Risk Response Planning",
                    allowed=True,
                    reason="Passed",
                    severity="critical",
                ),
                PolicyEvaluationResult(
                    control_code="MANAGE-2.1",
                    title="Resource Allocation",
                    allowed=True,
                    reason="Passed",
                    severity="high",
                ),
                PolicyEvaluationResult(
                    control_code="MANAGE-2.4",
                    title="System Deactivation Criteria",
                    allowed=False,
                    reason="No deactivation criteria defined",
                    severity="high",
                ),
                PolicyEvaluationResult(
                    control_code="MANAGE-3.1",
                    title="Third-Party Monitoring",
                    allowed=True,
                    reason="Passed",
                    severity="high",
                ),
                PolicyEvaluationResult(
                    control_code="MANAGE-4.1",
                    title="Post-Deployment Monitoring",
                    allowed=True,
                    reason="Passed",
                    severity="critical",
                ),
            ]
            mock_response_stats.return_value = {"total": 8, "completed": 3}
            mock_incident_stats.return_value = {"total": 5, "open": 2, "critical": 1}
            mock_deactivation.return_value = False

            result = await service.get_dashboard(PROJECT_ID, mock_db)

            assert result["project_id"] == PROJECT_ID
            assert result["policies_passed"] == 4
            assert result["policies_total"] == 5
            assert result["compliance_percentage"] == 80.0
            assert result["total_risk_responses"] == 8
            assert result["completed_responses"] == 3
            assert result["total_incidents"] == 5
            assert result["open_incidents"] == 2
            assert result["critical_incidents"] == 1
            assert result["has_deactivation_criteria"] is False

    @pytest.mark.asyncio
    async def test_get_dashboard_empty_project(self, service, mock_db):
        """Test dashboard with no prior assessments returns defaults."""
        with patch.object(
            service,
            "_fetch_latest_assessments",
            new_callable=AsyncMock,
        ) as mock_fetch, patch.object(
            service,
            "_get_response_stats",
            new_callable=AsyncMock,
        ) as mock_response_stats, patch.object(
            service,
            "_get_incident_stats",
            new_callable=AsyncMock,
        ) as mock_incident_stats, patch.object(
            service,
            "_has_deactivation_criteria",
            new_callable=AsyncMock,
        ) as mock_deactivation:
            mock_fetch.return_value = []
            mock_response_stats.return_value = {"total": 0, "completed": 0}
            mock_incident_stats.return_value = {"total": 0, "open": 0, "critical": 0}
            mock_deactivation.return_value = False

            result = await service.get_dashboard(PROJECT_ID, mock_db)

            assert result["compliance_percentage"] == 0.0
            assert result["policies_passed"] == 0
            assert result["policies_total"] == len(MANAGE_POLICIES)
            assert result["total_risk_responses"] == 0
            assert result["completed_responses"] == 0
            assert result["total_incidents"] == 0
            assert result["open_incidents"] == 0
            assert result["critical_incidents"] == 0
            assert result["has_deactivation_criteria"] is False

    @pytest.mark.asyncio
    async def test_get_dashboard_includes_deactivation(self, service, mock_db):
        """Test dashboard returns has_deactivation_criteria = True when criteria exist."""
        with patch.object(
            service,
            "_fetch_latest_assessments",
            new_callable=AsyncMock,
        ) as mock_fetch, patch.object(
            service,
            "_get_response_stats",
            new_callable=AsyncMock,
        ) as mock_response_stats, patch.object(
            service,
            "_get_incident_stats",
            new_callable=AsyncMock,
        ) as mock_incident_stats, patch.object(
            service,
            "_has_deactivation_criteria",
            new_callable=AsyncMock,
        ) as mock_deactivation:
            mock_fetch.return_value = [
                PolicyEvaluationResult(
                    control_code="MANAGE-2.4",
                    title="System Deactivation Criteria",
                    allowed=True,
                    reason="Deactivation criteria defined",
                    severity="high",
                ),
            ]
            mock_response_stats.return_value = {"total": 3, "completed": 1}
            mock_incident_stats.return_value = {"total": 1, "open": 0, "critical": 0}
            mock_deactivation.return_value = True

            result = await service.get_dashboard(PROJECT_ID, mock_db)

            assert result["has_deactivation_criteria"] is True
            assert result["policies_passed"] == 1
            assert result["total_risk_responses"] == 3


# =============================================================================
# Risk Response CRUD Tests
# =============================================================================


class TestListRiskResponses:
    """Tests for NISTManageService.list_risk_responses."""

    @pytest.mark.asyncio
    async def test_list_risk_responses(
        self, service, mock_db, sample_risk_response
    ):
        """Test listing risk responses returns items with pagination."""
        mock_db.execute = AsyncMock(
            side_effect=[
                _mock_scalar(2),
                _mock_scalars_all([sample_risk_response]),
            ]
        )

        items, total = await service.list_risk_responses(
            project_id=PROJECT_ID,
            status_filter=None,
            limit=20,
            offset=0,
            db=mock_db,
        )

        assert total == 2
        assert len(items) == 1
        assert items[0]["response_type"] == ResponseType.MITIGATE.value
        assert items[0]["assigned_to"] == "ml-team"

    @pytest.mark.asyncio
    async def test_list_risk_responses_status_filter(
        self, service, mock_db, sample_risk_response
    ):
        """Test listing risk responses with status filter."""
        mock_db.execute = AsyncMock(
            side_effect=[
                _mock_scalar(1),
                _mock_scalars_all([sample_risk_response]),
            ]
        )

        items, total = await service.list_risk_responses(
            project_id=PROJECT_ID,
            status_filter=ResponseStatus.PLANNED.value,
            limit=20,
            offset=0,
            db=mock_db,
        )

        assert total == 1
        assert len(items) == 1
        assert items[0]["status"] == ResponseStatus.PLANNED.value


class TestCreateRiskResponse:
    """Tests for NISTManageService.create_risk_response."""

    @pytest.mark.asyncio
    async def test_create_risk_response(self, service, mock_db):
        """Test creating a risk response with valid data."""
        mock_response = MagicMock(spec=ManageRiskResponse)
        mock_response.id = RESPONSE_ID
        mock_response.response_type = ResponseType.MITIGATE.value
        mock_response.priority = "high"
        mock_response.to_dict.return_value = {
            "id": str(RESPONSE_ID),
            "project_id": str(PROJECT_ID),
            "risk_id": str(RISK_ID),
            "response_type": ResponseType.MITIGATE.value,
            "description": "Implement bias detection pipeline",
            "assigned_to": "ml-team",
            "priority": "high",
            "status": ResponseStatus.PLANNED.value,
            "due_date": "2026-06-01",
            "resources_allocated": [
                {"type": "compute", "description": "GPU cluster", "budget": 5000}
            ],
            "deactivation_criteria": None,
            "notes": None,
            "created_at": NOW.isoformat(),
            "updated_at": NOW.isoformat(),
        }

        mock_db.refresh = AsyncMock(side_effect=lambda obj: None)

        # Patch ManageRiskResponse constructor to return our mock
        with patch(
            "app.services.nist_manage_service.ManageRiskResponse",
            return_value=mock_response,
        ):
            data = {
                "project_id": PROJECT_ID,
                "risk_id": RISK_ID,
                "response_type": ResponseType.MITIGATE.value,
                "description": "Implement bias detection pipeline",
                "assigned_to": "ml-team",
                "priority": "high",
                "due_date": "2026-06-01",
                "resources_allocated": [
                    {"type": "compute", "description": "GPU cluster", "budget": 5000}
                ],
            }

            result = await service.create_risk_response(data, mock_db)

            assert result["response_type"] == ResponseType.MITIGATE.value
            assert result["assigned_to"] == "ml-team"
            mock_db.add.assert_called_once()
            mock_db.commit.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_create_risk_response_with_deactivation(self, service, mock_db):
        """Test creating a risk response with deactivation criteria populated."""
        deactivation = {
            "conditions": ["accuracy below 70%", "bias score above 0.3"],
            "threshold": 0.7,
            "action": "deactivate_and_notify",
        }

        mock_response = MagicMock(spec=ManageRiskResponse)
        mock_response.id = RESPONSE_ID
        mock_response.response_type = ResponseType.MITIGATE.value
        mock_response.priority = "critical"
        mock_response.to_dict.return_value = {
            "id": str(RESPONSE_ID),
            "project_id": str(PROJECT_ID),
            "risk_id": str(RISK_ID),
            "response_type": ResponseType.MITIGATE.value,
            "description": "Deactivation response",
            "assigned_to": "safety-team",
            "priority": "critical",
            "status": ResponseStatus.PLANNED.value,
            "due_date": None,
            "resources_allocated": [],
            "deactivation_criteria": deactivation,
            "notes": None,
            "created_at": NOW.isoformat(),
            "updated_at": NOW.isoformat(),
        }

        mock_db.refresh = AsyncMock(side_effect=lambda obj: None)

        with patch(
            "app.services.nist_manage_service.ManageRiskResponse",
            return_value=mock_response,
        ):
            data = {
                "project_id": PROJECT_ID,
                "risk_id": RISK_ID,
                "response_type": ResponseType.MITIGATE.value,
                "description": "Deactivation response",
                "assigned_to": "safety-team",
                "priority": "critical",
                "deactivation_criteria": deactivation,
            }

            result = await service.create_risk_response(data, mock_db)

            assert result["deactivation_criteria"] is not None
            assert len(result["deactivation_criteria"]["conditions"]) == 2
            assert result["deactivation_criteria"]["action"] == "deactivate_and_notify"
            mock_db.add.assert_called_once()
            mock_db.commit.assert_awaited_once()


class TestUpdateRiskResponse:
    """Tests for NISTManageService.update_risk_response."""

    @pytest.mark.asyncio
    async def test_update_risk_response(
        self, service, mock_db, sample_risk_response
    ):
        """Test updating a risk response updates status and resources."""
        mock_db.execute = AsyncMock(
            return_value=_mock_scalar_one_or_none(sample_risk_response)
        )

        # After update, the to_dict returns updated values
        sample_risk_response.to_dict.return_value = {
            "id": str(RESPONSE_ID),
            "project_id": str(PROJECT_ID),
            "risk_id": str(RISK_ID),
            "response_type": ResponseType.MITIGATE.value,
            "description": "Implement bias detection pipeline",
            "assigned_to": "ml-team",
            "priority": "high",
            "status": ResponseStatus.COMPLETED.value,
            "due_date": "2026-06-01",
            "resources_allocated": [
                {"type": "compute", "description": "GPU cluster v2", "budget": 8000}
            ],
            "deactivation_criteria": None,
            "notes": "Response completed successfully",
            "created_at": NOW.isoformat(),
            "updated_at": NOW.isoformat(),
        }

        data = {
            "status": ResponseStatus.COMPLETED.value,
            "resources_allocated": [
                {"type": "compute", "description": "GPU cluster v2", "budget": 8000}
            ],
            "notes": "Response completed successfully",
        }

        result = await service.update_risk_response(RESPONSE_ID, data, mock_db)

        assert result["status"] == ResponseStatus.COMPLETED.value
        assert result["resources_allocated"][0]["budget"] == 8000
        assert result["notes"] == "Response completed successfully"
        mock_db.commit.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_update_risk_response_not_found(self, service, mock_db):
        """Test updating non-existent risk response raises error."""
        mock_db.execute = AsyncMock(
            return_value=_mock_scalar_one_or_none(None)
        )

        data = {"status": ResponseStatus.COMPLETED.value}

        with pytest.raises(
            RiskResponseNotFoundError, match="not found"
        ):
            await service.update_risk_response(
                UUID("00000000-0000-0000-0000-000000000999"), data, mock_db
            )


# =============================================================================
# Incident CRUD Tests
# =============================================================================


class TestListIncidents:
    """Tests for NISTManageService.list_incidents."""

    @pytest.mark.asyncio
    async def test_list_incidents(
        self, service, mock_db, sample_incident
    ):
        """Test listing incidents returns items with pagination."""
        mock_db.execute = AsyncMock(
            side_effect=[
                _mock_scalar(3),
                _mock_scalars_all([sample_incident]),
            ]
        )

        items, total = await service.list_incidents(
            project_id=PROJECT_ID,
            ai_system_id=None,
            status_filter=None,
            limit=20,
            offset=0,
            db=mock_db,
        )

        assert total == 3
        assert len(items) == 1
        assert items[0]["title"] == "Model accuracy degradation"
        assert items[0]["severity"] == IncidentSeverity.HIGH.value

    @pytest.mark.asyncio
    async def test_list_incidents_system_filter(
        self, service, mock_db, sample_incident
    ):
        """Test listing incidents filtered by ai_system_id."""
        mock_db.execute = AsyncMock(
            side_effect=[
                _mock_scalar(1),
                _mock_scalars_all([sample_incident]),
            ]
        )

        items, total = await service.list_incidents(
            project_id=PROJECT_ID,
            ai_system_id=SYSTEM_ID,
            status_filter=None,
            limit=20,
            offset=0,
            db=mock_db,
        )

        assert total == 1
        assert len(items) == 1
        assert items[0]["ai_system_id"] == str(SYSTEM_ID)


class TestCreateIncident:
    """Tests for NISTManageService.create_incident."""

    @pytest.mark.asyncio
    async def test_create_incident(self, service, mock_db):
        """Test creating an incident with valid data."""
        mock_incident = MagicMock(spec=ManageIncident)
        mock_incident.id = INCIDENT_ID
        mock_incident.severity = IncidentSeverity.HIGH.value
        mock_incident.incident_type = "performance_degradation"
        mock_incident.to_dict.return_value = {
            "id": str(INCIDENT_ID),
            "project_id": str(PROJECT_ID),
            "ai_system_id": str(SYSTEM_ID),
            "risk_id": None,
            "title": "Model accuracy degradation",
            "description": "Chatbot accuracy dropped below 80%",
            "severity": IncidentSeverity.HIGH.value,
            "incident_type": "performance_degradation",
            "status": IncidentStatus.OPEN.value,
            "reported_by": "monitoring-system",
            "assigned_to": None,
            "resolution": None,
            "root_cause": None,
            "occurred_at": NOW.isoformat(),
            "resolved_at": None,
            "created_at": NOW.isoformat(),
            "updated_at": NOW.isoformat(),
        }

        mock_db.refresh = AsyncMock(side_effect=lambda obj: None)

        with patch(
            "app.services.nist_manage_service.ManageIncident",
            return_value=mock_incident,
        ):
            data = {
                "project_id": PROJECT_ID,
                "ai_system_id": SYSTEM_ID,
                "title": "Model accuracy degradation",
                "description": "Chatbot accuracy dropped below 80%",
                "severity": IncidentSeverity.HIGH.value,
                "incident_type": "performance_degradation",
                "occurred_at": "2026-04-21T10:00:00Z",
                "reported_by": "monitoring-system",
            }

            result = await service.create_incident(data, mock_db)

            assert result["title"] == "Model accuracy degradation"
            assert result["severity"] == IncidentSeverity.HIGH.value
            assert result["incident_type"] == "performance_degradation"
            mock_db.add.assert_called_once()
            mock_db.commit.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_create_incident_with_risk_id(self, service, mock_db):
        """Test creating an incident linked to a risk register entry."""
        mock_incident = MagicMock(spec=ManageIncident)
        mock_incident.id = INCIDENT_ID
        mock_incident.severity = IncidentSeverity.CRITICAL.value
        mock_incident.incident_type = "bias_detected"
        mock_incident.to_dict.return_value = {
            "id": str(INCIDENT_ID),
            "project_id": str(PROJECT_ID),
            "ai_system_id": str(SYSTEM_ID),
            "risk_id": str(RISK_ID),
            "title": "Bias detected in hiring model",
            "description": "Protected group disparity exceeded threshold",
            "severity": IncidentSeverity.CRITICAL.value,
            "incident_type": "bias_detected",
            "status": IncidentStatus.OPEN.value,
            "reported_by": "fairness-monitor",
            "assigned_to": None,
            "resolution": None,
            "root_cause": None,
            "occurred_at": NOW.isoformat(),
            "resolved_at": None,
            "created_at": NOW.isoformat(),
            "updated_at": NOW.isoformat(),
        }

        mock_db.refresh = AsyncMock(side_effect=lambda obj: None)

        with patch(
            "app.services.nist_manage_service.ManageIncident",
            return_value=mock_incident,
        ):
            data = {
                "project_id": PROJECT_ID,
                "ai_system_id": SYSTEM_ID,
                "risk_id": RISK_ID,
                "title": "Bias detected in hiring model",
                "description": "Protected group disparity exceeded threshold",
                "severity": IncidentSeverity.CRITICAL.value,
                "incident_type": "bias_detected",
                "occurred_at": NOW,
                "reported_by": "fairness-monitor",
            }

            result = await service.create_incident(data, mock_db)

            assert result["risk_id"] == str(RISK_ID)
            assert result["severity"] == IncidentSeverity.CRITICAL.value
            mock_db.add.assert_called_once()
            mock_db.commit.assert_awaited_once()


class TestUpdateIncident:
    """Tests for NISTManageService.update_incident."""

    @pytest.mark.asyncio
    async def test_update_incident(
        self, service, mock_db, sample_incident
    ):
        """Test updating an incident updates status and resolution."""
        mock_db.execute = AsyncMock(
            return_value=_mock_scalar_one_or_none(sample_incident)
        )

        sample_incident.to_dict.return_value = {
            "id": str(INCIDENT_ID),
            "project_id": str(PROJECT_ID),
            "ai_system_id": str(SYSTEM_ID),
            "risk_id": None,
            "title": "Model accuracy degradation",
            "description": "Chatbot accuracy dropped below 80%",
            "severity": IncidentSeverity.HIGH.value,
            "incident_type": "performance_degradation",
            "status": IncidentStatus.RESOLVED.value,
            "reported_by": "monitoring-system",
            "assigned_to": "ml-team",
            "resolution": "Retrained model with balanced dataset",
            "root_cause": "Training data drift",
            "occurred_at": NOW.isoformat(),
            "resolved_at": NOW.isoformat(),
            "created_at": NOW.isoformat(),
            "updated_at": NOW.isoformat(),
        }

        data = {
            "status": IncidentStatus.RESOLVED.value,
            "resolution": "Retrained model with balanced dataset",
            "root_cause": "Training data drift",
            "resolved_at": "2026-04-21T15:00:00Z",
        }

        result = await service.update_incident(INCIDENT_ID, data, mock_db)

        assert result["status"] == IncidentStatus.RESOLVED.value
        assert result["resolution"] == "Retrained model with balanced dataset"
        assert result["root_cause"] == "Training data drift"
        mock_db.commit.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_update_incident_not_found(self, service, mock_db):
        """Test updating non-existent incident raises error."""
        mock_db.execute = AsyncMock(
            return_value=_mock_scalar_one_or_none(None)
        )

        data = {"status": IncidentStatus.RESOLVED.value}

        with pytest.raises(IncidentNotFoundError, match="not found"):
            await service.update_incident(
                UUID("00000000-0000-0000-0000-000000000999"), data, mock_db
            )


# =============================================================================
# In-Process Policy Evaluation Tests (Pure Logic)
# =============================================================================


class TestInProcessEvaluators:
    """Tests for the in-process policy evaluation fallback methods."""

    def test_eval_risk_response_planning(self):
        """Test MANAGE-1.1: Open risks need response plans with assigned owner and due date."""
        svc = NISTManageService()
        # Risk has a valid response with assigned_to and due_date
        allowed, reason, details = svc._eval_risk_response_planning({
            "risks": [
                {
                    "id": str(RISK_ID),
                    "risk_code": "RISK-001",
                    "title": "Model bias",
                    "status": "identified",
                },
            ],
            "risk_responses": [
                {
                    "risk_id": str(RISK_ID),
                    "assigned_to": "ml-team",
                    "due_date": "2026-06-01",
                },
            ],
        })
        assert allowed is True
        assert details["open_risks"] == 1
        assert details["uncovered_risks"] == []

        # Risk without any valid response (missing due_date)
        allowed, reason, details = svc._eval_risk_response_planning({
            "risks": [
                {
                    "id": str(RISK_ID),
                    "risk_code": "RISK-001",
                    "title": "Model bias",
                    "status": "identified",
                },
            ],
            "risk_responses": [
                {
                    "risk_id": str(RISK_ID),
                    "assigned_to": "ml-team",
                    "due_date": None,
                },
            ],
        })
        assert allowed is False
        assert "RISK-001" in details["uncovered_risks"]

    def test_eval_resource_allocation_excludes_accept(self):
        """Test MANAGE-2.1: Accept-type responses excluded from budget check."""
        svc = NISTManageService()

        # Only accept responses present: should pass (no non-accept to check)
        allowed, reason, details = svc._eval_resource_allocation({
            "risk_responses": [
                {
                    "response_type": "accept",
                    "resources_allocated": [],
                },
            ],
        })
        assert allowed is True
        assert details["non_accept_responses"] == 0

        # Mix of accept and mitigate: mitigate has budget
        allowed, reason, details = svc._eval_resource_allocation({
            "risk_responses": [
                {
                    "response_type": "accept",
                    "resources_allocated": [],
                },
                {
                    "response_type": "mitigate",
                    "resources_allocated": [{"budget": 5000}],
                },
            ],
        })
        assert allowed is True
        assert details["non_accept_responses"] == 1
        assert details["resourced_responses"] == 1

    def test_eval_deactivation_criteria(self):
        """Test MANAGE-2.4: At least one response must define deactivation criteria."""
        svc = NISTManageService()

        # No responses: fails
        allowed, reason, details = svc._eval_deactivation_criteria({
            "risk_responses": [],
        })
        assert allowed is False
        assert details["total_responses"] == 0

        # Response with valid deactivation criteria
        allowed, reason, details = svc._eval_deactivation_criteria({
            "risk_responses": [
                {
                    "deactivation_criteria": {
                        "conditions": ["accuracy below 70%"],
                        "threshold": 0.7,
                        "action": "deactivate",
                    },
                },
            ],
        })
        assert allowed is True
        assert details["responses_with_criteria"] == 1

        # Response with empty conditions: fails
        allowed, reason, details = svc._eval_deactivation_criteria({
            "risk_responses": [
                {
                    "deactivation_criteria": {
                        "conditions": [],
                    },
                },
            ],
        })
        assert allowed is False
        assert details["responses_with_criteria"] == 0

    def test_eval_third_party_monitoring(self):
        """Test MANAGE-3.1: Third-party systems must have recent incidents/reviews."""
        svc = NISTManageService()

        # No third-party systems: passes
        allowed, reason, details = svc._eval_third_party_monitoring({
            "third_party_systems": [],
            "incidents": [],
            "cutoff_date": "2026-01-21T00:00:00+00:00",
        })
        assert allowed is True
        assert details["third_party_count"] == 0

        # Third-party system with recent incident: passes
        allowed, reason, details = svc._eval_third_party_monitoring({
            "third_party_systems": [
                {"id": str(SYSTEM_ID), "name": "External LLM"},
            ],
            "incidents": [
                {
                    "ai_system_id": str(SYSTEM_ID),
                    "occurred_at": "2026-04-01T10:00:00+00:00",
                },
            ],
            "cutoff_date": "2026-01-21T00:00:00+00:00",
        })
        assert allowed is True
        assert details["unmonitored_systems"] == []

        # Third-party system without recent incident: fails
        allowed, reason, details = svc._eval_third_party_monitoring({
            "third_party_systems": [
                {"id": str(SYSTEM_ID), "name": "External LLM"},
            ],
            "incidents": [
                {
                    "ai_system_id": str(SYSTEM_ID),
                    "occurred_at": "2025-12-01T10:00:00+00:00",
                },
            ],
            "cutoff_date": "2026-01-21T00:00:00+00:00",
        })
        assert allowed is False
        assert "External LLM" in details["unmonitored_systems"]

    def test_eval_post_deployment_monitoring(self):
        """Test MANAGE-4.1: Active systems need recent metrics and no critical incidents."""
        svc = NISTManageService()

        # No active systems: passes
        allowed, reason, details = svc._eval_post_deployment_monitoring({
            "active_systems": [],
            "recent_metrics": [],
            "critical_incidents": [],
        })
        assert allowed is True
        assert details["active_systems_count"] == 0

        # Active system with recent metrics: passes
        allowed, reason, details = svc._eval_post_deployment_monitoring({
            "active_systems": [
                {"id": str(SYSTEM_ID), "name": "Chatbot"},
            ],
            "recent_metrics": [
                {"ai_system_id": str(SYSTEM_ID), "measured_at": NOW.isoformat()},
            ],
            "critical_incidents": [],
        })
        assert allowed is True
        assert details["systems_without_metrics"] == []

        # Active system without metrics: fails
        allowed, reason, details = svc._eval_post_deployment_monitoring({
            "active_systems": [
                {"id": str(SYSTEM_ID), "name": "Chatbot"},
            ],
            "recent_metrics": [],
            "critical_incidents": [],
        })
        assert allowed is False
        assert "Chatbot" in details["systems_without_metrics"]

        # Active system with metrics but unresolved critical incident: fails
        allowed, reason, details = svc._eval_post_deployment_monitoring({
            "active_systems": [
                {"id": str(SYSTEM_ID), "name": "Chatbot"},
            ],
            "recent_metrics": [
                {"ai_system_id": str(SYSTEM_ID), "measured_at": NOW.isoformat()},
            ],
            "critical_incidents": [
                {"id": str(uuid4()), "severity": "critical", "status": "open"},
            ],
        })
        assert allowed is False
        assert details["unresolved_critical_count"] == 1


# =============================================================================
# Third-Party Identification Tests (CTO Condition #1)
# =============================================================================


class TestIsThirdPartySystem:
    """Tests for NISTManageService._is_third_party_system."""

    def test_is_third_party_system_external(self):
        """Test external provider dependency is identified as third-party."""
        svc = NISTManageService()

        system = MagicMock(spec=AISystem)
        system.dependencies = [
            {"name": "openai", "type": "api", "provider": "OpenAI"},
        ]

        result = svc._is_third_party_system(system)
        assert result is True

    def test_is_third_party_system_internal(self):
        """Test internal provider dependency is NOT identified as third-party."""
        svc = NISTManageService()

        system = MagicMock(spec=AISystem)
        system.dependencies = [
            {"name": "ollama", "type": "api", "provider": "internal"},
        ]

        result = svc._is_third_party_system(system)
        assert result is False

        # Test in-house provider
        system.dependencies = [
            {"name": "custom-model", "type": "model", "provider": "in-house"},
        ]
        result = svc._is_third_party_system(system)
        assert result is False

        # Test empty provider
        system.dependencies = [
            {"name": "local-model", "type": "model", "provider": ""},
        ]
        result = svc._is_third_party_system(system)
        assert result is False

        # Test no dependencies
        system.dependencies = []
        result = svc._is_third_party_system(system)
        assert result is False

        # Test None dependencies
        system.dependencies = None
        result = svc._is_third_party_system(system)
        assert result is False
