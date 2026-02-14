"""
=========================================================================
NIST GOVERN Service Unit Tests
SDLC Orchestrator - Sprint 156 (Phase 3: COMPLIANCE)

Version: 1.0.0
Date: February 5, 2026
Status: ACTIVE
Authority: CTO Approved
Framework: SDLC 6.0.5

Test Categories:
- GOVERN Evaluation Tests (all pass, some fail, empty input)
- GOVERN Dashboard Tests (with/without assessments)
- Risk Register Tests (list, create, update, filters)
- RACI Matrix Tests (get, upsert create, upsert update, validation)

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
    RiskLikelihood as SchemaRiskLikelihood,
    RiskImpact as SchemaRiskImpact,
    RiskStatus as SchemaRiskStatus,
)
from app.services.nist_govern_service import (
    NISTGovernService,
    NISTGovernNotFoundError,
    NISTGovernValidationError,
    NISTGovernEvaluationError,
    GOVERN_POLICIES,
)


# =============================================================================
# Test Constants
# =============================================================================

PROJECT_ID = UUID("00000000-0000-0000-0000-000000000001")
FRAMEWORK_ID = UUID("00000000-0000-0000-0000-000000000002")
CONTROL_ID = UUID("00000000-0000-0000-0000-000000000003")
RISK_ID = UUID("00000000-0000-0000-0000-000000000004")
RACI_ID = UUID("00000000-0000-0000-0000-000000000005")
USER_ID = UUID("00000000-0000-0000-0000-000000000006")
NOW = datetime(2026, 4, 7, 12, 0, 0, tzinfo=timezone.utc)


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
    """Create NISTGovernService instance."""
    return NISTGovernService()


@pytest.fixture
def sample_framework():
    """Create a mock ComplianceFramework model instance."""
    fw = MagicMock(spec=ComplianceFramework)
    fw.id = FRAMEWORK_ID
    fw.code = "NIST_AI_RMF"
    fw.name = "NIST AI Risk Management Framework"
    fw.version = "1.0"
    fw.is_active = True
    return fw


@pytest.fixture
def sample_control():
    """Create a mock ComplianceControl model instance."""
    ctrl = MagicMock(spec=ComplianceControl)
    ctrl.id = CONTROL_ID
    ctrl.framework_id = FRAMEWORK_ID
    ctrl.control_code = "GOVERN-1.1"
    ctrl.category = "GOVERN"
    ctrl.title = "Accountability Structures"
    ctrl.description = "All AI systems must have designated owners"
    ctrl.severity = "critical"
    ctrl.gate_mapping = "G1"
    ctrl.evidence_required = []
    ctrl.opa_policy_code = "nist/govern/govern_1_1"
    ctrl.sort_order = 1
    ctrl.created_at = NOW
    ctrl.updated_at = NOW
    return ctrl


@pytest.fixture
def sample_risk():
    """Create a mock ComplianceRiskRegister model instance."""
    risk = MagicMock(spec=ComplianceRiskRegister)
    risk.id = RISK_ID
    risk.project_id = PROJECT_ID
    risk.framework_id = FRAMEWORK_ID
    risk.risk_code = "RISK-001"
    risk.title = "Model bias in hiring decisions"
    risk.description = "AI model may exhibit bias against protected groups"
    risk.likelihood = "likely"
    risk.impact = "major"
    risk.risk_score = 16
    risk.category = "fairness"
    risk.mitigation_strategy = "Implement bias detection pipeline"
    risk.responsible_id = USER_ID
    risk.responsible = None
    risk.status = "identified"
    risk.target_date = date(2026, 6, 1)
    risk.created_at = NOW
    risk.updated_at = NOW
    return risk


@pytest.fixture
def sample_raci(sample_control):
    """Create a mock ComplianceRACI model instance."""
    raci = MagicMock(spec=ComplianceRACI)
    raci.id = RACI_ID
    raci.project_id = PROJECT_ID
    raci.control_id = CONTROL_ID
    raci.responsible_id = USER_ID
    raci.accountable_id = USER_ID
    raci.consulted_ids = []
    raci.informed_ids = []
    raci.created_at = NOW
    raci.updated_at = NOW
    raci.control = sample_control
    raci.responsible = None
    raci.accountable = None
    return raci


@pytest.fixture
def all_pass_request():
    """Create a GovernEvaluateRequest where all 5 policies pass."""
    return GovernEvaluateRequest(
        project_id=PROJECT_ID,
        ai_systems=[
            {"name": "chatbot", "owner": "team-lead", "type": "nlp"},
            {"name": "recommender", "owner": "ml-engineer", "type": "ml"},
        ],
        team_training={"completion_pct": 95, "total_members": 10, "trained_members": 10},
        legal_review={"approved": True, "reviewer": "legal-counsel", "date": "2026-03-15"},
        third_party_apis=[
            {"name": "openai", "sla_documented": True, "privacy_agreement": True},
        ],
        incident_postmortems=[],
    )


@pytest.fixture
def some_fail_request():
    """Create a GovernEvaluateRequest where some policies fail."""
    return GovernEvaluateRequest(
        project_id=PROJECT_ID,
        ai_systems=[
            {"name": "chatbot", "owner": "", "type": "nlp"},
        ],
        team_training={"completion_pct": 50},
        legal_review=None,
        third_party_apis=[
            {"name": "openai", "sla_documented": False, "privacy_agreement": True},
        ],
        incident_postmortems=[
            {"incident_date": "2026-01-01", "postmortem_date": None, "process_updated": False},
        ],
    )


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


def _mock_one(row):
    """Create a mock result with one() returning a named row."""
    mock_result = MagicMock()
    mock_result.one.return_value = row
    return mock_result


# =============================================================================
# GOVERN Evaluation Tests
# =============================================================================


class TestEvaluateGovern:
    """Tests for NISTGovernService.evaluate_govern."""

    @pytest.mark.asyncio
    async def test_evaluate_govern_all_pass(
        self, service, mock_db, all_pass_request
    ):
        """Test evaluation where all 5 GOVERN policies pass."""
        mock_db.execute = AsyncMock(
            side_effect=[
                _mock_scalar_one_or_none(None),
            ]
        )

        with patch.object(
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
                for p in GOVERN_POLICIES
            ]

            result = await service.evaluate_govern(
                PROJECT_ID, all_pass_request, mock_db
            )

            assert isinstance(result, GovernEvaluateResponse)
            assert result.overall_compliant is True
            assert result.policies_passed == 5
            assert result.policies_total == 5
            assert result.compliance_percentage == 100.0

    @pytest.mark.asyncio
    async def test_evaluate_govern_some_fail(
        self, service, mock_db, some_fail_request
    ):
        """Test evaluation where some GOVERN policies fail."""
        with patch.object(
            service,
            "_evaluate_single_policy",
            new_callable=AsyncMock,
        ) as mock_eval, patch.object(
            service,
            "_persist_assessment_results",
            new_callable=AsyncMock,
        ):
            results_data = [
                PolicyEvaluationResult(
                    control_code="GOVERN-1.1",
                    title="Accountability Structures",
                    allowed=False,
                    reason="AI systems without owners: chatbot",
                    severity="critical",
                ),
                PolicyEvaluationResult(
                    control_code="GOVERN-1.2",
                    title="Risk Culture & Training",
                    allowed=False,
                    reason="Training completion at 50%, minimum 80% required.",
                    severity="high",
                ),
                PolicyEvaluationResult(
                    control_code="GOVERN-1.3",
                    title="Legal & Regulatory Review",
                    allowed=False,
                    reason="No legal review data provided.",
                    severity="critical",
                ),
                PolicyEvaluationResult(
                    control_code="GOVERN-1.4",
                    title="Third-Party Risk Management",
                    allowed=False,
                    reason="1 third-party API(s) lack required documentation",
                    severity="high",
                ),
                PolicyEvaluationResult(
                    control_code="GOVERN-1.5",
                    title="Continuous Improvement",
                    allowed=False,
                    reason="1 incident postmortem(s) are incomplete.",
                    severity="medium",
                ),
            ]
            mock_eval.side_effect = results_data

            result = await service.evaluate_govern(
                PROJECT_ID, some_fail_request, mock_db
            )

            assert result.overall_compliant is False
            assert result.policies_passed == 0
            assert result.policies_total == 5
            assert result.compliance_percentage == 0.0

    @pytest.mark.asyncio
    async def test_evaluate_govern_empty_input(self, service, mock_db):
        """Test evaluation with minimal/empty input data."""
        request = GovernEvaluateRequest(
            project_id=PROJECT_ID,
            ai_systems=[],
            team_training=None,
            legal_review=None,
            third_party_apis=[],
            incident_postmortems=[],
        )

        with patch.object(
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
                    control_code="GOVERN-1.1",
                    title="Accountability Structures",
                    allowed=False,
                    reason="No AI systems registered.",
                    severity="critical",
                ),
                PolicyEvaluationResult(
                    control_code="GOVERN-1.2",
                    title="Risk Culture & Training",
                    allowed=False,
                    reason="No training data provided.",
                    severity="high",
                ),
                PolicyEvaluationResult(
                    control_code="GOVERN-1.3",
                    title="Legal & Regulatory Review",
                    allowed=False,
                    reason="No legal review data provided.",
                    severity="critical",
                ),
                PolicyEvaluationResult(
                    control_code="GOVERN-1.4",
                    title="Third-Party Risk Management",
                    allowed=True,
                    reason="No third-party APIs registered.",
                    severity="high",
                ),
                PolicyEvaluationResult(
                    control_code="GOVERN-1.5",
                    title="Continuous Improvement",
                    allowed=True,
                    reason="No incident postmortems recorded.",
                    severity="medium",
                ),
            ]

            result = await service.evaluate_govern(
                PROJECT_ID, request, mock_db
            )

            assert result.policies_passed == 2
            assert result.policies_total == 5
            assert result.overall_compliant is False


# =============================================================================
# GOVERN Dashboard Tests
# =============================================================================


class TestGetGovernDashboard:
    """Tests for NISTGovernService.get_govern_dashboard."""

    @pytest.mark.asyncio
    async def test_get_govern_dashboard(self, service, mock_db):
        """Test dashboard returns correctly aggregated data."""
        with patch.object(
            service,
            "_fetch_latest_assessments",
            new_callable=AsyncMock,
        ) as mock_fetch, patch.object(
            service,
            "_get_risk_summary",
            new_callable=AsyncMock,
        ) as mock_risk, patch.object(
            service,
            "_get_raci_coverage",
            new_callable=AsyncMock,
        ) as mock_raci:
            mock_fetch.return_value = [
                PolicyEvaluationResult(
                    control_code="GOVERN-1.1",
                    title="Accountability",
                    allowed=True,
                    reason="Passed",
                    severity="critical",
                ),
                PolicyEvaluationResult(
                    control_code="GOVERN-1.2",
                    title="Risk Culture",
                    allowed=False,
                    reason="Training below threshold",
                    severity="high",
                ),
            ]
            mock_risk.return_value = {"critical": 1, "high": 2, "medium": 0, "low": 1}
            mock_raci.return_value = 60.0

            result = await service.get_govern_dashboard(PROJECT_ID, mock_db)

            assert isinstance(result, GovernDashboardResponse)
            assert result.project_id == PROJECT_ID
            assert result.policies_passed == 1
            assert result.risk_summary["critical"] == 1
            assert result.risk_summary["high"] == 2
            assert result.total_risks == 4
            assert result.raci_coverage == 60.0

    @pytest.mark.asyncio
    async def test_get_govern_dashboard_no_assessments(
        self, service, mock_db
    ):
        """Test dashboard with no prior assessments returns defaults."""
        with patch.object(
            service,
            "_fetch_latest_assessments",
            new_callable=AsyncMock,
        ) as mock_fetch, patch.object(
            service,
            "_get_risk_summary",
            new_callable=AsyncMock,
        ) as mock_risk, patch.object(
            service,
            "_get_raci_coverage",
            new_callable=AsyncMock,
        ) as mock_raci:
            mock_fetch.return_value = []
            mock_risk.return_value = {"critical": 0, "high": 0, "medium": 0, "low": 0}
            mock_raci.return_value = 0.0

            result = await service.get_govern_dashboard(PROJECT_ID, mock_db)

            assert result.compliance_percentage == 0.0
            assert result.policies_passed == 0
            assert result.total_risks == 0
            assert result.raci_coverage == 0.0


# =============================================================================
# Risk Register List Tests
# =============================================================================


class TestListRisks:
    """Tests for NISTGovernService.list_risks."""

    @pytest.mark.asyncio
    async def test_list_risks_with_project(
        self, service, mock_db, sample_risk
    ):
        """Test listing risks for a project returns correct results."""
        mock_db.execute = AsyncMock(
            side_effect=[
                _mock_scalar(1),
                _mock_scalars_all([sample_risk]),
            ]
        )

        result = await service.list_risks(
            project_id=PROJECT_ID,
            framework_id=None,
            status_filter=None,
            limit=20,
            offset=0,
            db=mock_db,
        )

        assert isinstance(result, RiskListResponse)
        assert result.total == 1
        assert len(result.items) == 1
        assert result.items[0].risk_code == "RISK-001"
        assert result.items[0].risk_score == 16

    @pytest.mark.asyncio
    async def test_list_risks_with_status_filter(
        self, service, mock_db, sample_risk
    ):
        """Test listing risks with status filter."""
        mock_db.execute = AsyncMock(
            side_effect=[
                _mock_scalar(1),
                _mock_scalars_all([sample_risk]),
            ]
        )

        result = await service.list_risks(
            project_id=PROJECT_ID,
            framework_id=None,
            status_filter=RiskStatus.IDENTIFIED,
            limit=20,
            offset=0,
            db=mock_db,
        )

        assert isinstance(result, RiskListResponse)
        assert result.total == 1

    @pytest.mark.asyncio
    async def test_list_risks_empty(self, service, mock_db):
        """Test listing risks when none exist returns empty list."""
        mock_db.execute = AsyncMock(
            side_effect=[
                _mock_scalar(0),
                _mock_scalars_all([]),
            ]
        )

        result = await service.list_risks(
            project_id=PROJECT_ID,
            framework_id=None,
            status_filter=None,
            limit=20,
            offset=0,
            db=mock_db,
        )

        assert result.total == 0
        assert len(result.items) == 0
        assert result.has_more is False


# =============================================================================
# Risk Register Create Tests
# =============================================================================


class TestCreateRisk:
    """Tests for NISTGovernService.create_risk."""

    @pytest.mark.asyncio
    async def test_create_risk_success(
        self, service, mock_db, sample_risk
    ):
        """Test creating a risk entry succeeds with valid data."""
        mock_db.execute = AsyncMock(
            return_value=_mock_scalar_one_or_none(FRAMEWORK_ID)
        )
        mock_db.refresh = AsyncMock(
            side_effect=lambda obj: None
        )

        with patch.object(service, "_risk_to_response") as mock_response:
            mock_response.return_value = RiskResponse(
                id=RISK_ID,
                project_id=PROJECT_ID,
                framework_id=FRAMEWORK_ID,
                risk_code="RISK-001",
                title="Model bias in hiring decisions",
                description="AI model may exhibit bias",
                likelihood="likely",
                impact="major",
                risk_score=16,
                risk_level="critical",
                category="fairness",
                mitigation_strategy=None,
                responsible_id=None,
                status="identified",
                target_date=None,
                created_at=NOW,
                updated_at=NOW,
            )

            data = RiskCreate(
                project_id=PROJECT_ID,
                framework_id=FRAMEWORK_ID,
                risk_code="RISK-001",
                title="Model bias in hiring decisions",
                description="AI model may exhibit bias",
                likelihood=SchemaRiskLikelihood.LIKELY,
                impact=SchemaRiskImpact.MAJOR,
                category="fairness",
            )

            result = await service.create_risk(data, mock_db)

            assert isinstance(result, RiskResponse)
            assert result.risk_code == "RISK-001"
            assert result.risk_score == 16
            mock_db.add.assert_called_once()
            mock_db.commit.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_create_risk_auto_calculates_score(
        self, service, mock_db
    ):
        """Test risk score is auto-calculated from likelihood and impact."""
        mock_db.execute = AsyncMock(
            return_value=_mock_scalar_one_or_none(FRAMEWORK_ID)
        )

        with patch.object(service, "_risk_to_response") as mock_response:
            mock_response.return_value = RiskResponse(
                id=RISK_ID,
                project_id=PROJECT_ID,
                framework_id=FRAMEWORK_ID,
                risk_code="RISK-002",
                title="Data privacy leak",
                description=None,
                likelihood="almost_certain",
                impact="catastrophic",
                risk_score=25,
                risk_level="critical",
                category="privacy",
                mitigation_strategy=None,
                responsible_id=None,
                status="identified",
                target_date=None,
                created_at=NOW,
                updated_at=NOW,
            )

            data = RiskCreate(
                project_id=PROJECT_ID,
                framework_id=FRAMEWORK_ID,
                risk_code="RISK-002",
                title="Data privacy leak",
                likelihood=SchemaRiskLikelihood.ALMOST_CERTAIN,
                impact=SchemaRiskImpact.CATASTROPHIC,
                category="privacy",
            )

            result = await service.create_risk(data, mock_db)

            assert result.risk_score == 25
            assert result.risk_level == "critical"

    @pytest.mark.asyncio
    async def test_create_risk_framework_not_found(self, service, mock_db):
        """Test creating risk with non-existent framework raises error."""
        mock_db.execute = AsyncMock(
            return_value=_mock_scalar_one_or_none(None)
        )

        data = RiskCreate(
            project_id=PROJECT_ID,
            framework_id=UUID("00000000-0000-0000-0000-000000000999"),
            risk_code="RISK-003",
            title="Nonexistent framework risk",
            category="security",
            likelihood=SchemaRiskLikelihood.POSSIBLE,
            impact=SchemaRiskImpact.MODERATE,
        )

        with pytest.raises(NISTGovernValidationError, match="not found"):
            await service.create_risk(data, mock_db)


# =============================================================================
# Risk Register Update Tests
# =============================================================================


class TestUpdateRisk:
    """Tests for NISTGovernService.update_risk."""

    @pytest.mark.asyncio
    async def test_update_risk_success(
        self, service, mock_db, sample_risk
    ):
        """Test updating a risk entry succeeds."""
        mock_db.execute = AsyncMock(
            return_value=_mock_scalar_one_or_none(sample_risk)
        )

        with patch.object(service, "_risk_to_response") as mock_response:
            mock_response.return_value = RiskResponse(
                id=RISK_ID,
                project_id=PROJECT_ID,
                framework_id=FRAMEWORK_ID,
                risk_code="RISK-001",
                title="Updated title",
                description=None,
                likelihood="likely",
                impact="major",
                risk_score=16,
                risk_level="critical",
                category="fairness",
                mitigation_strategy="New strategy",
                responsible_id=None,
                status="mitigating",
                target_date=None,
                created_at=NOW,
                updated_at=NOW,
            )

            data = RiskUpdate(
                title="Updated title",
                mitigation_strategy="New strategy",
                status=SchemaRiskStatus.MITIGATING,
            )

            result = await service.update_risk(RISK_ID, data, mock_db)

            assert isinstance(result, RiskResponse)
            mock_db.commit.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_update_risk_recalculates_score(
        self, service, mock_db, sample_risk
    ):
        """Test updating likelihood/impact triggers score recalculation."""
        mock_db.execute = AsyncMock(
            return_value=_mock_scalar_one_or_none(sample_risk)
        )

        with patch.object(service, "_risk_to_response") as mock_response:
            mock_response.return_value = RiskResponse(
                id=RISK_ID,
                project_id=PROJECT_ID,
                framework_id=FRAMEWORK_ID,
                risk_code="RISK-001",
                title="Model bias",
                description=None,
                likelihood="almost_certain",
                impact="major",
                risk_score=20,
                risk_level="critical",
                category="fairness",
                mitigation_strategy=None,
                responsible_id=None,
                status="identified",
                target_date=None,
                created_at=NOW,
                updated_at=NOW,
            )

            data = RiskUpdate(
                likelihood=SchemaRiskLikelihood.ALMOST_CERTAIN,
            )

            result = await service.update_risk(RISK_ID, data, mock_db)

            sample_risk.update_risk_score.assert_called_once()
            mock_db.commit.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_update_risk_not_found(self, service, mock_db):
        """Test updating a non-existent risk raises error."""
        mock_db.execute = AsyncMock(
            return_value=_mock_scalar_one_or_none(None)
        )

        data = RiskUpdate(title="Non-existent")

        with pytest.raises(NISTGovernNotFoundError, match="not found"):
            await service.update_risk(
                UUID("00000000-0000-0000-0000-000000000999"), data, mock_db
            )

    @pytest.mark.asyncio
    async def test_update_risk_partial(self, service, mock_db, sample_risk):
        """Test partial update only modifies specified fields."""
        mock_db.execute = AsyncMock(
            return_value=_mock_scalar_one_or_none(sample_risk)
        )

        with patch.object(service, "_risk_to_response") as mock_response:
            mock_response.return_value = RiskResponse(
                id=RISK_ID,
                project_id=PROJECT_ID,
                framework_id=FRAMEWORK_ID,
                risk_code="RISK-001",
                title="Model bias in hiring decisions",
                description="AI model may exhibit bias against protected groups",
                likelihood="likely",
                impact="major",
                risk_score=16,
                risk_level="critical",
                category="fairness",
                mitigation_strategy="Updated strategy only",
                responsible_id=USER_ID,
                status="identified",
                target_date=date(2026, 6, 1),
                created_at=NOW,
                updated_at=NOW,
            )

            data = RiskUpdate(mitigation_strategy="Updated strategy only")

            result = await service.update_risk(RISK_ID, data, mock_db)

            assert result.mitigation_strategy == "Updated strategy only"
            assert result.risk_code == "RISK-001"
            sample_risk.update_risk_score.assert_not_called()


# =============================================================================
# RACI Matrix Tests
# =============================================================================


class TestGetRaci:
    """Tests for NISTGovernService.get_raci."""

    @pytest.mark.asyncio
    async def test_get_raci_success(
        self, service, mock_db, sample_raci
    ):
        """Test getting RACI matrix returns entries for project."""
        mock_db.execute = AsyncMock(
            return_value=_mock_scalars_all([sample_raci])
        )

        with patch.object(
            service,
            "_raci_to_response",
            new_callable=AsyncMock,
        ) as mock_response:
            mock_response.return_value = RACIResponse(
                id=RACI_ID,
                project_id=PROJECT_ID,
                control_id=CONTROL_ID,
                responsible_id=USER_ID,
                accountable_id=USER_ID,
                consulted_ids=[],
                informed_ids=[],
                created_at=NOW,
                updated_at=NOW,
            )

            result = await service.get_raci(PROJECT_ID, mock_db)

            assert isinstance(result, RACIListResponse)
            assert result.total == 1
            assert len(result.items) == 1

    @pytest.mark.asyncio
    async def test_get_raci_empty(self, service, mock_db):
        """Test getting RACI matrix when none exist returns empty list."""
        mock_db.execute = AsyncMock(
            return_value=_mock_scalars_all([])
        )

        result = await service.get_raci(PROJECT_ID, mock_db)

        assert isinstance(result, RACIListResponse)
        assert result.total == 0
        assert len(result.items) == 0


class TestUpsertRaci:
    """Tests for NISTGovernService.upsert_raci."""

    @pytest.mark.asyncio
    async def test_upsert_raci_create_new(
        self, service, mock_db
    ):
        """Test creating a new RACI entry when none exists."""
        mock_db.execute = AsyncMock(
            side_effect=[
                _mock_scalar_one_or_none(CONTROL_ID),
                _mock_scalar_one_or_none(None),
            ]
        )

        with patch.object(
            service,
            "_raci_to_response",
            new_callable=AsyncMock,
        ) as mock_response:
            mock_response.return_value = RACIResponse(
                id=RACI_ID,
                project_id=PROJECT_ID,
                control_id=CONTROL_ID,
                responsible_id=USER_ID,
                accountable_id=USER_ID,
                consulted_ids=[],
                informed_ids=[],
                created_at=NOW,
                updated_at=NOW,
            )

            data = RACICreate(
                project_id=PROJECT_ID,
                control_id=CONTROL_ID,
                responsible_id=USER_ID,
                accountable_id=USER_ID,
                consulted_ids=[],
                informed_ids=[],
            )

            result = await service.upsert_raci(data, mock_db)

            assert isinstance(result, RACIResponse)
            assert result.responsible_id == USER_ID
            mock_db.add.assert_called_once()
            mock_db.commit.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_upsert_raci_update_existing(
        self, service, mock_db, sample_raci
    ):
        """Test updating an existing RACI entry."""
        new_accountable = UUID("00000000-0000-0000-0000-000000000010")
        mock_db.execute = AsyncMock(
            side_effect=[
                _mock_scalar_one_or_none(CONTROL_ID),
                _mock_scalar_one_or_none(sample_raci),
            ]
        )

        with patch.object(
            service,
            "_raci_to_response",
            new_callable=AsyncMock,
        ) as mock_response:
            mock_response.return_value = RACIResponse(
                id=RACI_ID,
                project_id=PROJECT_ID,
                control_id=CONTROL_ID,
                responsible_id=USER_ID,
                accountable_id=new_accountable,
                consulted_ids=[],
                informed_ids=[],
                created_at=NOW,
                updated_at=NOW,
            )

            data = RACICreate(
                project_id=PROJECT_ID,
                control_id=CONTROL_ID,
                responsible_id=USER_ID,
                accountable_id=new_accountable,
                consulted_ids=[],
                informed_ids=[],
            )

            result = await service.upsert_raci(data, mock_db)

            assert isinstance(result, RACIResponse)
            assert sample_raci.accountable_id == new_accountable
            mock_db.add.assert_not_called()
            mock_db.commit.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_upsert_raci_control_not_found(self, service, mock_db):
        """Test upserting RACI with non-existent control raises error."""
        mock_db.execute = AsyncMock(
            return_value=_mock_scalar_one_or_none(None)
        )

        data = RACICreate(
            project_id=PROJECT_ID,
            control_id=UUID("00000000-0000-0000-0000-000000000999"),
            responsible_id=USER_ID,
            accountable_id=USER_ID,
        )

        with pytest.raises(NISTGovernValidationError, match="not found"):
            await service.upsert_raci(data, mock_db)


# =============================================================================
# In-Process Evaluator Tests (Unit tests for pure logic)
# =============================================================================


class TestInProcessEvaluators:
    """Tests for the in-process policy evaluation fallback methods."""

    def test_eval_accountability_all_owned(self):
        """Test GOVERN-1.1 passes when all AI systems have owners."""
        svc = NISTGovernService()
        allowed, reason, details = svc._eval_accountability({
            "ai_systems": [
                {"name": "chatbot", "owner": "lead"},
                {"name": "recommender", "owner": "engineer"},
            ]
        })
        assert allowed is True
        assert details["ai_systems_count"] == 2

    def test_eval_accountability_some_unowned(self):
        """Test GOVERN-1.1 fails when some AI systems lack owners."""
        svc = NISTGovernService()
        allowed, reason, details = svc._eval_accountability({
            "ai_systems": [
                {"name": "chatbot", "owner": ""},
                {"name": "recommender", "owner": "engineer"},
            ]
        })
        assert allowed is False
        assert "chatbot" in details["unowned_systems"]
