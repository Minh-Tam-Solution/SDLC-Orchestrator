"""
=========================================================================
NIST MAP Service Unit Tests
SDLC Orchestrator - Sprint 157 (Phase 3: COMPLIANCE)

Version: 1.0.0
Date: February 5, 2026
Status: ACTIVE
Authority: CTO Approved
Framework: SDLC 6.0.5

Test Categories:
- MAP Evaluation Tests (all pass, some fail, empty systems, OPA fallback, error)
- MAP Dashboard Tests (with assessments, empty project, with data)
- AI System CRUD Tests (list, create, update, delete - 12 tests)
- Risk Impact Tests (with risks, empty, filtering)
- OPA Evaluation Tests (OPA success, OPA fallback, OPA timeout)

Test Approach: Unit tests mocking database layer via AsyncMock
Zero Mock Policy: Mocks for database layer only
=========================================================================
"""

import pytest
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import UUID, uuid4

from app.models.compliance import (
    ComplianceAssessment,
    ComplianceControl,
    ComplianceFramework,
    ComplianceRiskRegister,
)
from app.models.nist_map_measure import AIRiskLevel, AISystem
from app.schemas.compliance_framework import PolicyEvaluationResult
from app.services.nist_map_service import (
    AISystemDuplicateError,
    AISystemNotFoundError,
    MAP_POLICIES,
    NISTMapEvaluationError,
    NISTMapService,
)


# =============================================================================
# Test Constants
# =============================================================================

PROJECT_ID = UUID("00000000-0000-0000-0000-000000000001")
FRAMEWORK_ID = UUID("00000000-0000-0000-0000-000000000002")
SYSTEM_ID = UUID("00000000-0000-0000-0000-000000000003")
USER_ID = UUID("00000000-0000-0000-0000-000000000004")
NOW = datetime(2026, 4, 14, 12, 0, 0, tzinfo=timezone.utc)


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
    """Create NISTMapService instance."""
    return NISTMapService()


@pytest.fixture
def sample_ai_system():
    """Create a mock AISystem model instance."""
    system = MagicMock(spec=AISystem)
    system.id = SYSTEM_ID
    system.project_id = PROJECT_ID
    system.name = "Customer Support Chatbot"
    system.description = "NLP chatbot for customer inquiries"
    system.system_type = "nlp"
    system.risk_level = "limited"
    system.purpose = "Automated customer support via chat"
    system.scope = "Production - US region"
    system.stakeholders = [{"role": "user", "name": "customers"}]
    system.dependencies = [{"name": "openai", "type": "api"}]
    system.categorization = {"risk_tier": "limited"}
    system.owner_id = USER_ID
    system.is_active = True
    system.created_at = NOW
    system.updated_at = NOW
    system.to_dict.return_value = {
        "id": str(SYSTEM_ID),
        "project_id": str(PROJECT_ID),
        "name": "Customer Support Chatbot",
        "description": "NLP chatbot for customer inquiries",
        "system_type": "nlp",
        "risk_level": "limited",
        "purpose": "Automated customer support via chat",
        "scope": "Production - US region",
        "stakeholders": [{"role": "user", "name": "customers"}],
        "dependencies": [{"name": "openai", "type": "api"}],
        "categorization": {"risk_tier": "limited"},
        "owner_id": str(USER_ID),
        "is_active": True,
        "created_at": NOW.isoformat(),
        "updated_at": NOW.isoformat(),
    }
    return system


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
# MAP Evaluation Tests
# =============================================================================


class TestEvaluateMap:
    """Tests for NISTMapService.evaluate_map."""

    @pytest.mark.asyncio
    async def test_evaluate_map_all_pass(self, service, mock_db):
        """Test evaluation where all 4 MAP policies pass."""
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
                },
            ],
            "risks": [
                {
                    "impact_areas": ["customer_experience"],
                    "affected_stakeholders": ["customers"],
                },
            ],
        }

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
                for p in MAP_POLICIES
            ]

            result = await service.evaluate_map(
                mock_db, PROJECT_ID, request
            )

            assert result["overall_compliant"] is True
            assert result["policies_passed"] == 4
            assert result["policies_total"] == 4
            assert result["compliance_percentage"] == 100.0
            assert result["framework_code"] == "NIST_AI_RMF"
            assert result["function"] == "MAP"

    @pytest.mark.asyncio
    async def test_evaluate_map_some_fail(self, service, mock_db):
        """Test evaluation where some MAP policies fail."""
        request = {
            "ai_systems": [
                {
                    "name": "chatbot",
                    "purpose": "",
                    "scope": "",
                    "owner": "",
                    "stakeholders": [],
                    "categorization": None,
                    "dependencies": [],
                },
            ],
            "risks": [],
        }

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
                    control_code="MAP-1.1",
                    title="Context Establishment",
                    allowed=False,
                    reason="1 AI system(s) have incomplete context: chatbot",
                    severity="critical",
                ),
                PolicyEvaluationResult(
                    control_code="MAP-1.2",
                    title="Stakeholder Identification",
                    allowed=False,
                    reason="1 AI system(s) have incomplete stakeholder identification: chatbot",
                    severity="high",
                ),
                PolicyEvaluationResult(
                    control_code="MAP-2.1",
                    title="System Categorization",
                    allowed=False,
                    reason="1 AI system(s) lack valid categorization: chatbot",
                    severity="critical",
                ),
                PolicyEvaluationResult(
                    control_code="MAP-3.2",
                    title="Risk-Impact Mapping",
                    allowed=False,
                    reason="Risk-impact mapping incomplete",
                    severity="high",
                ),
            ]
            mock_eval.side_effect = results_data

            result = await service.evaluate_map(
                mock_db, PROJECT_ID, request
            )

            assert result["overall_compliant"] is False
            assert result["policies_passed"] == 0
            assert result["policies_total"] == 4
            assert result["compliance_percentage"] == 0.0

    @pytest.mark.asyncio
    async def test_evaluate_map_empty_systems(self, service, mock_db):
        """Test evaluation with no AI systems registered."""
        request = {
            "ai_systems": [],
            "risks": [],
        }

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
                    control_code="MAP-1.1",
                    title="Context Establishment",
                    allowed=False,
                    reason="No AI systems registered.",
                    severity="critical",
                ),
                PolicyEvaluationResult(
                    control_code="MAP-1.2",
                    title="Stakeholder Identification",
                    allowed=False,
                    reason="No AI systems registered.",
                    severity="high",
                ),
                PolicyEvaluationResult(
                    control_code="MAP-2.1",
                    title="System Categorization",
                    allowed=False,
                    reason="No AI systems registered.",
                    severity="critical",
                ),
                PolicyEvaluationResult(
                    control_code="MAP-3.2",
                    title="Risk-Impact Mapping",
                    allowed=True,
                    reason="All 0 risk(s) and 0 AI system(s) have complete risk-impact mappings.",
                    severity="high",
                ),
            ]

            result = await service.evaluate_map(
                mock_db, PROJECT_ID, request
            )

            assert result["policies_passed"] == 1
            assert result["policies_total"] == 4
            assert result["overall_compliant"] is False

    @pytest.mark.asyncio
    async def test_evaluate_map_opa_fallback(self, service, mock_db):
        """Test evaluation falls back to in-process when OPA is unavailable."""
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
                },
            ],
            "risks": [
                {
                    "impact_areas": ["customer_experience"],
                    "affected_stakeholders": ["customers"],
                },
            ],
        }

        with patch.object(
            service,
            "_evaluate_via_opa",
            new_callable=AsyncMock,
            return_value=None,
        ), patch.object(
            service,
            "_persist_assessment_results",
            new_callable=AsyncMock,
        ):
            result = await service.evaluate_map(
                mock_db, PROJECT_ID, request
            )

            assert isinstance(result, dict)
            assert "overall_compliant" in result
            assert "policies_passed" in result
            assert result["policies_total"] == 4

    @pytest.mark.asyncio
    async def test_evaluate_map_evaluation_error(self, service, mock_db):
        """Test evaluation raises NISTMapEvaluationError on failure."""
        request = {
            "ai_systems": [
                {"name": "chatbot"},
            ],
            "risks": [],
        }

        with patch.object(
            service,
            "_evaluate_single_policy",
            new_callable=AsyncMock,
            side_effect=RuntimeError("Unexpected evaluation failure"),
        ), patch.object(
            service,
            "_persist_assessment_results",
            new_callable=AsyncMock,
        ):
            with pytest.raises(NISTMapEvaluationError, match="Failed to evaluate"):
                await service.evaluate_map(
                    mock_db, PROJECT_ID, request
                )


# =============================================================================
# MAP Dashboard Tests
# =============================================================================


class TestGetDashboard:
    """Tests for NISTMapService.get_dashboard."""

    @pytest.mark.asyncio
    async def test_get_dashboard_with_assessments(self, service, mock_db):
        """Test dashboard returns correctly aggregated data."""
        with patch.object(
            service,
            "_fetch_latest_assessments",
            new_callable=AsyncMock,
        ) as mock_fetch, patch.object(
            service,
            "_get_ai_system_summary",
            new_callable=AsyncMock,
        ) as mock_ai_summary, patch.object(
            service,
            "_get_risk_summary",
            new_callable=AsyncMock,
        ) as mock_risk:
            mock_fetch.return_value = [
                PolicyEvaluationResult(
                    control_code="MAP-1.1",
                    title="Context Establishment",
                    allowed=True,
                    reason="Passed",
                    severity="critical",
                ),
                PolicyEvaluationResult(
                    control_code="MAP-1.2",
                    title="Stakeholder Identification",
                    allowed=True,
                    reason="Passed",
                    severity="high",
                ),
                PolicyEvaluationResult(
                    control_code="MAP-2.1",
                    title="System Categorization",
                    allowed=False,
                    reason="Missing categorization",
                    severity="critical",
                ),
                PolicyEvaluationResult(
                    control_code="MAP-3.2",
                    title="Risk-Impact Mapping",
                    allowed=True,
                    reason="Passed",
                    severity="high",
                ),
            ]
            mock_ai_summary.return_value = {
                "total_systems": 3,
                "by_risk_level": {"limited": 2, "high": 1},
                "by_type": {"nlp": 2, "vision": 1},
            }
            mock_risk.return_value = {"critical": 1, "high": 2, "medium": 1, "low": 0}

            result = await service.get_dashboard(mock_db, PROJECT_ID)

            assert result["project_id"] == PROJECT_ID
            assert result["policies_passed"] == 3
            assert result["policies_total"] == 4
            assert result["compliance_percentage"] == 75.0
            assert result["ai_system_summary"]["total_systems"] == 3
            assert result["risk_summary"]["critical"] == 1
            assert result["total_risks"] == 4

    @pytest.mark.asyncio
    async def test_get_dashboard_empty_project(self, service, mock_db):
        """Test dashboard with no prior assessments returns defaults."""
        with patch.object(
            service,
            "_fetch_latest_assessments",
            new_callable=AsyncMock,
        ) as mock_fetch, patch.object(
            service,
            "_get_ai_system_summary",
            new_callable=AsyncMock,
        ) as mock_ai_summary, patch.object(
            service,
            "_get_risk_summary",
            new_callable=AsyncMock,
        ) as mock_risk:
            mock_fetch.return_value = []
            mock_ai_summary.return_value = {
                "total_systems": 0,
                "by_risk_level": {},
                "by_type": {},
            }
            mock_risk.return_value = {"critical": 0, "high": 0, "medium": 0, "low": 0}

            result = await service.get_dashboard(mock_db, PROJECT_ID)

            assert result["compliance_percentage"] == 0.0
            assert result["policies_passed"] == 0
            assert result["policies_total"] == len(MAP_POLICIES)
            assert result["total_risks"] == 0
            assert result["ai_system_summary"]["total_systems"] == 0

    @pytest.mark.asyncio
    async def test_get_dashboard_with_data(self, service, mock_db):
        """Test dashboard with full data returns correct risk and AI system summaries."""
        with patch.object(
            service,
            "_fetch_latest_assessments",
            new_callable=AsyncMock,
        ) as mock_fetch, patch.object(
            service,
            "_get_ai_system_summary",
            new_callable=AsyncMock,
        ) as mock_ai_summary, patch.object(
            service,
            "_get_risk_summary",
            new_callable=AsyncMock,
        ) as mock_risk:
            mock_fetch.return_value = [
                PolicyEvaluationResult(
                    control_code="MAP-1.1",
                    title="Context Establishment",
                    allowed=True,
                    reason="Passed",
                    severity="critical",
                ),
            ]
            mock_ai_summary.return_value = {
                "total_systems": 5,
                "by_risk_level": {"minimal": 1, "limited": 2, "high": 2},
                "by_type": {"nlp": 3, "generative": 2},
            }
            mock_risk.return_value = {"critical": 2, "high": 3, "medium": 5, "low": 1}

            result = await service.get_dashboard(mock_db, PROJECT_ID)

            assert result["policies_passed"] == 1
            assert result["ai_system_summary"]["total_systems"] == 5
            assert result["risk_summary"]["high"] == 3
            assert result["total_risks"] == 11


# =============================================================================
# AI System List Tests
# =============================================================================


class TestListAISystems:
    """Tests for NISTMapService.list_ai_systems."""

    @pytest.mark.asyncio
    async def test_list_ai_systems_empty(self, service, mock_db):
        """Test listing AI systems when none exist returns empty list."""
        mock_db.execute = AsyncMock(
            side_effect=[
                _mock_scalar(0),
                _mock_scalars_all([]),
            ]
        )

        items, total = await service.list_ai_systems(
            db=mock_db,
            project_id=PROJECT_ID,
            skip=0,
            limit=50,
        )

        assert total == 0
        assert len(items) == 0

    @pytest.mark.asyncio
    async def test_list_ai_systems_with_data(
        self, service, mock_db, sample_ai_system
    ):
        """Test listing AI systems returns items and count."""
        mock_db.execute = AsyncMock(
            side_effect=[
                _mock_scalar(1),
                _mock_scalars_all([sample_ai_system]),
            ]
        )

        items, total = await service.list_ai_systems(
            db=mock_db,
            project_id=PROJECT_ID,
            skip=0,
            limit=50,
        )

        assert total == 1
        assert len(items) == 1
        assert items[0]["name"] == "Customer Support Chatbot"
        assert items[0]["system_type"] == "nlp"

    @pytest.mark.asyncio
    async def test_list_ai_systems_pagination(
        self, service, mock_db, sample_ai_system
    ):
        """Test listing AI systems respects skip and limit."""
        mock_db.execute = AsyncMock(
            side_effect=[
                _mock_scalar(10),
                _mock_scalars_all([sample_ai_system]),
            ]
        )

        items, total = await service.list_ai_systems(
            db=mock_db,
            project_id=PROJECT_ID,
            skip=5,
            limit=1,
        )

        assert total == 10
        assert len(items) == 1
        assert mock_db.execute.call_count == 2


# =============================================================================
# AI System Create Tests
# =============================================================================


class TestCreateAISystem:
    """Tests for NISTMapService.create_ai_system."""

    @pytest.mark.asyncio
    async def test_create_ai_system_success(self, service, mock_db, sample_ai_system):
        """Test creating an AI system succeeds with valid data."""
        mock_db.execute = AsyncMock(
            return_value=_mock_scalar_one_or_none(None)
        )
        mock_db.refresh = AsyncMock(
            side_effect=lambda obj: None
        )

        data = {
            "project_id": PROJECT_ID,
            "name": "Customer Support Chatbot",
            "system_type": "nlp",
            "risk_level": "limited",
            "purpose": "Automated customer support",
            "scope": "Production - US region",
            "stakeholders": [{"role": "user", "name": "customers"}],
            "dependencies": [{"name": "openai", "type": "api"}],
            "categorization": {"risk_tier": "limited"},
            "owner_id": USER_ID,
        }

        result = await service.create_ai_system(mock_db, data)

        mock_db.add.assert_called_once()
        mock_db.commit.assert_awaited_once()
        mock_db.refresh.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_create_ai_system_duplicate_error(self, service, mock_db):
        """Test creating AI system with duplicate name raises error."""
        mock_db.execute = AsyncMock(
            return_value=_mock_scalar_one_or_none(SYSTEM_ID)
        )

        data = {
            "project_id": PROJECT_ID,
            "name": "Customer Support Chatbot",
            "system_type": "nlp",
        }

        with pytest.raises(AISystemDuplicateError, match="already exists"):
            await service.create_ai_system(mock_db, data)

    @pytest.mark.asyncio
    async def test_create_ai_system_defaults(self, service, mock_db):
        """Test creating AI system uses default values for optional fields."""
        mock_db.execute = AsyncMock(
            return_value=_mock_scalar_one_or_none(None)
        )
        mock_db.refresh = AsyncMock(side_effect=lambda obj: None)

        data = {
            "project_id": PROJECT_ID,
            "name": "Minimal System",
        }

        result = await service.create_ai_system(mock_db, data)

        mock_db.add.assert_called_once()
        added_obj = mock_db.add.call_args[0][0]
        assert added_obj.system_type == "generative"
        assert added_obj.risk_level == AIRiskLevel.HIGH.value
        assert added_obj.stakeholders == []
        assert added_obj.dependencies == []
        assert added_obj.is_active is True


# =============================================================================
# AI System Update Tests
# =============================================================================


class TestUpdateAISystem:
    """Tests for NISTMapService.update_ai_system."""

    @pytest.mark.asyncio
    async def test_update_ai_system_success(
        self, service, mock_db, sample_ai_system
    ):
        """Test updating an AI system succeeds with valid data."""
        mock_db.execute = AsyncMock(
            return_value=_mock_scalar_one_or_none(sample_ai_system)
        )

        data = {
            "risk_level": "high",
            "purpose": "Updated purpose description",
        }

        result = await service.update_ai_system(mock_db, SYSTEM_ID, data)

        assert result == sample_ai_system
        mock_db.commit.assert_awaited_once()
        mock_db.refresh.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_update_ai_system_not_found(self, service, mock_db):
        """Test updating a non-existent AI system raises error."""
        mock_db.execute = AsyncMock(
            return_value=_mock_scalar_one_or_none(None)
        )

        data = {"name": "Non-existent system"}

        with pytest.raises(AISystemNotFoundError, match="not found"):
            await service.update_ai_system(
                mock_db,
                UUID("00000000-0000-0000-0000-000000000999"),
                data,
            )

    @pytest.mark.asyncio
    async def test_update_ai_system_partial(
        self, service, mock_db, sample_ai_system
    ):
        """Test partial update only modifies specified fields."""
        mock_db.execute = AsyncMock(
            return_value=_mock_scalar_one_or_none(sample_ai_system)
        )

        data = {"description": "Updated description only"}

        result = await service.update_ai_system(mock_db, SYSTEM_ID, data)

        assert sample_ai_system.description == "Updated description only"
        mock_db.commit.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_update_ai_system_ignores_none_values(
        self, service, mock_db, sample_ai_system
    ):
        """Test that None values in data dict are not applied."""
        mock_db.execute = AsyncMock(
            return_value=_mock_scalar_one_or_none(sample_ai_system)
        )

        original_name = sample_ai_system.name
        data = {"name": None, "purpose": "New purpose"}

        result = await service.update_ai_system(mock_db, SYSTEM_ID, data)

        # name should not have been set to None because the service skips None values
        assert sample_ai_system.name == original_name
        mock_db.commit.assert_awaited_once()


# =============================================================================
# AI System Delete Tests
# =============================================================================


class TestDeleteAISystem:
    """Tests for NISTMapService.delete_ai_system."""

    @pytest.mark.asyncio
    async def test_delete_ai_system_success(
        self, service, mock_db, sample_ai_system
    ):
        """Test soft-deleting an AI system succeeds."""
        mock_db.execute = AsyncMock(
            return_value=_mock_scalar_one_or_none(sample_ai_system)
        )

        result = await service.delete_ai_system(mock_db, SYSTEM_ID)

        assert result is True
        assert sample_ai_system.is_active is False
        mock_db.commit.assert_awaited_once()
        mock_db.refresh.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_delete_ai_system_not_found(self, service, mock_db):
        """Test deleting a non-existent AI system raises error."""
        mock_db.execute = AsyncMock(
            return_value=_mock_scalar_one_or_none(None)
        )

        with pytest.raises(AISystemNotFoundError, match="not found"):
            await service.delete_ai_system(
                mock_db,
                UUID("00000000-0000-0000-0000-000000000999"),
            )

    @pytest.mark.asyncio
    async def test_delete_ai_system_already_deleted(self, service, mock_db):
        """Test deleting an already-inactive AI system raises error."""
        # An inactive system won't be found by the query (which filters is_active=True)
        mock_db.execute = AsyncMock(
            return_value=_mock_scalar_one_or_none(None)
        )

        with pytest.raises(AISystemNotFoundError, match="not found"):
            await service.delete_ai_system(mock_db, SYSTEM_ID)


# =============================================================================
# Risk Impact Tests
# =============================================================================


class TestGetRiskImpacts:
    """Tests for NISTMapService.get_risk_impacts."""

    @pytest.mark.asyncio
    async def test_get_risk_impacts_with_risks(self, service, mock_db):
        """Test getting risk-impact mappings with risk data."""
        mock_risk = MagicMock(spec=ComplianceRiskRegister)
        mock_risk.id = UUID("00000000-0000-0000-0000-000000000010")
        mock_risk.risk_code = "RISK-001"
        mock_risk.title = "Model bias in hiring"
        mock_risk.category = "fairness"
        mock_risk.description = "AI model may exhibit bias against protected groups"
        mock_risk.risk_score = 16
        mock_risk.mitigation_strategy = "Implement bias detection"
        mock_risk.status = "identified"
        mock_risk.created_at = NOW

        mock_db.execute = AsyncMock(
            return_value=_mock_scalars_all([mock_risk])
        )

        result = await service.get_risk_impacts(mock_db, PROJECT_ID)

        assert len(result) == 1
        assert result[0]["risk_code"] == "RISK-001"
        assert result[0]["risk_level"] == "critical"
        assert result[0]["category"] == "fairness"
        assert len(result[0]["impact_areas"]) > 0
        assert len(result[0]["affected_stakeholders"]) > 0

    @pytest.mark.asyncio
    async def test_get_risk_impacts_empty(self, service, mock_db):
        """Test getting risk-impact mappings when no risks exist."""
        mock_db.execute = AsyncMock(
            return_value=_mock_scalars_all([])
        )

        result = await service.get_risk_impacts(mock_db, PROJECT_ID)

        assert len(result) == 0

    @pytest.mark.asyncio
    async def test_get_risk_impacts_multiple_categories(self, service, mock_db):
        """Test risk-impact mappings derive different areas per category."""
        safety_risk = MagicMock(spec=ComplianceRiskRegister)
        safety_risk.id = UUID("00000000-0000-0000-0000-000000000011")
        safety_risk.risk_code = "RISK-002"
        safety_risk.title = "Safety hazard"
        safety_risk.category = "safety"
        safety_risk.description = "Physical harm potential"
        safety_risk.risk_score = 20
        safety_risk.mitigation_strategy = None
        safety_risk.status = "identified"
        safety_risk.created_at = NOW

        privacy_risk = MagicMock(spec=ComplianceRiskRegister)
        privacy_risk.id = UUID("00000000-0000-0000-0000-000000000012")
        privacy_risk.risk_code = "RISK-003"
        privacy_risk.title = "Data leak"
        privacy_risk.category = "privacy"
        privacy_risk.description = "Customer data breach risk"
        privacy_risk.risk_score = 12
        privacy_risk.mitigation_strategy = "Encryption"
        privacy_risk.status = "mitigating"
        privacy_risk.created_at = NOW

        mock_db.execute = AsyncMock(
            return_value=_mock_scalars_all([safety_risk, privacy_risk])
        )

        result = await service.get_risk_impacts(mock_db, PROJECT_ID)

        assert len(result) == 2
        # Safety risk should have safety-related impact areas
        assert "human_safety" in result[0]["impact_areas"]
        assert result[0]["risk_level"] == "critical"
        # Privacy risk should have privacy-related impact areas
        assert "data_breach" in result[1]["impact_areas"]
        assert result[1]["risk_level"] == "high"
        # Customer keyword in description should add customer stakeholder
        assert "customers" in result[1]["affected_stakeholders"]


# =============================================================================
# OPA Evaluation Tests (In-Process Fallback)
# =============================================================================


class TestOPAEvaluation:
    """Tests for OPA evaluation and in-process fallback logic."""

    @pytest.mark.asyncio
    async def test_opa_success(self, service):
        """Test successful OPA evaluation returns result."""
        mock_opa_result = PolicyEvaluationResult(
            control_code="MAP-1.1",
            title="Context Establishment",
            allowed=True,
            reason="Evaluated by OPA",
            severity="critical",
            details={"source": "opa"},
        )

        with patch.object(
            service,
            "_evaluate_via_opa",
            new_callable=AsyncMock,
            return_value=mock_opa_result,
        ):
            result = await service._evaluate_single_policy(
                control_code="MAP-1.1",
                title="Context Establishment",
                severity="critical",
                opa_input={
                    "ai_systems": [
                        {
                            "name": "chatbot",
                            "purpose": "Support",
                            "scope": "Prod",
                            "owner": "lead",
                            "stakeholders": [{"role": "user", "name": "cust"}],
                        },
                    ],
                    "risks": [],
                },
            )

            assert result.allowed is True
            assert result.control_code == "MAP-1.1"

    @pytest.mark.asyncio
    async def test_opa_fallback_to_in_process(self, service):
        """Test fallback to in-process evaluation when OPA is unavailable."""
        with patch.object(
            service,
            "_evaluate_via_opa",
            new_callable=AsyncMock,
            return_value=None,
        ):
            opa_input = {
                "ai_systems": [
                    {
                        "name": "chatbot",
                        "purpose": "Support",
                        "scope": "Prod",
                        "owner": "lead",
                        "stakeholders": [{"role": "user", "name": "cust"}],
                    },
                ],
                "risks": [],
            }

            result = await service._evaluate_single_policy(
                control_code="MAP-1.1",
                title="Context Establishment",
                severity="critical",
                opa_input=opa_input,
            )

            assert isinstance(result, PolicyEvaluationResult)
            assert result.control_code == "MAP-1.1"
            assert result.allowed is True

    @pytest.mark.asyncio
    async def test_opa_timeout_falls_back(self, service):
        """Test OPA timeout triggers in-process fallback."""
        with patch.object(
            service,
            "_evaluate_via_opa",
            new_callable=AsyncMock,
            side_effect=Exception("OPA timeout"),
        ):
            opa_input = {
                "ai_systems": [
                    {
                        "name": "chatbot",
                        "purpose": "Support",
                        "scope": "Prod",
                        "owner": "lead",
                        "stakeholders": [{"role": "user", "name": "cust"}],
                    },
                ],
                "risks": [],
            }

            result = await service._evaluate_single_policy(
                control_code="MAP-1.1",
                title="Context Establishment",
                severity="critical",
                opa_input=opa_input,
            )

            assert isinstance(result, PolicyEvaluationResult)
            assert result.control_code == "MAP-1.1"
            assert result.allowed is True


# =============================================================================
# In-Process Evaluator Unit Tests (Pure Logic)
# =============================================================================


class TestInProcessEvaluators:
    """Tests for the in-process policy evaluation methods."""

    def test_eval_context_establishment_all_complete(self):
        """Test MAP-1.1 passes when all systems have complete context."""
        svc = NISTMapService()
        allowed, reason, details = svc._evaluate_context_establishment({
            "ai_systems": [
                {
                    "name": "chatbot",
                    "purpose": "Customer support",
                    "scope": "Production",
                    "owner": "team-lead",
                    "stakeholders": [{"role": "user", "name": "customers"}],
                },
            ]
        })
        assert allowed is True
        assert details["ai_systems_count"] == 1
        assert details["incomplete_systems"] == []

    def test_eval_context_establishment_missing_fields(self):
        """Test MAP-1.1 fails when systems lack required fields."""
        svc = NISTMapService()
        allowed, reason, details = svc._evaluate_context_establishment({
            "ai_systems": [
                {
                    "name": "chatbot",
                    "purpose": "",
                    "scope": None,
                    "owner": "",
                    "stakeholders": [],
                },
            ]
        })
        assert allowed is False
        assert details["incomplete_systems"][0]["name"] == "chatbot"
        assert "purpose" in details["incomplete_systems"][0]["missing"]
        assert "scope" in details["incomplete_systems"][0]["missing"]
        assert "owner" in details["incomplete_systems"][0]["missing"]
        assert "stakeholders" in details["incomplete_systems"][0]["missing"]

    def test_eval_context_establishment_empty_systems(self):
        """Test MAP-1.1 fails when no AI systems registered."""
        svc = NISTMapService()
        allowed, reason, details = svc._evaluate_context_establishment({
            "ai_systems": []
        })
        assert allowed is False
        assert "No AI systems registered" in reason

    def test_eval_system_categorization_valid(self):
        """Test MAP-2.1 passes with valid risk_tier categorization."""
        svc = NISTMapService()
        allowed, reason, details = svc._evaluate_system_categorization({
            "ai_systems": [
                {
                    "name": "chatbot",
                    "categorization": {"risk_tier": "limited"},
                },
                {
                    "name": "recommender",
                    "categorization": {"risk_tier": "high"},
                },
            ]
        })
        assert allowed is True
        assert details["ai_systems_count"] == 2

    def test_eval_system_categorization_invalid_tier(self):
        """Test MAP-2.1 fails with invalid or missing risk_tier."""
        svc = NISTMapService()
        allowed, reason, details = svc._evaluate_system_categorization({
            "ai_systems": [
                {
                    "name": "chatbot",
                    "categorization": {"risk_tier": "invalid_tier"},
                },
            ]
        })
        assert allowed is False
        assert "chatbot" in details["uncategorized_systems"][0]["name"]

    def test_eval_system_categorization_missing(self):
        """Test MAP-2.1 fails when categorization is None."""
        svc = NISTMapService()
        allowed, reason, details = svc._evaluate_system_categorization({
            "ai_systems": [
                {
                    "name": "chatbot",
                    "categorization": None,
                },
            ]
        })
        assert allowed is False
        assert details["uncategorized_systems"][0]["issue"] == "missing categorization"

    def test_eval_risk_impact_mapping_complete(self):
        """Test MAP-3.2 core logic passes with complete data."""
        svc = NISTMapService()
        allowed, reason, details = svc._evaluate_risk_impact_mapping({
            "ai_systems": [
                {
                    "name": "chatbot",
                    "dependencies": [{"name": "openai", "type": "api"}],
                },
            ],
            "risks": [
                {
                    "impact_areas": ["customer_experience"],
                    "affected_stakeholders": ["customers"],
                },
            ],
        })
        assert allowed is True

    def test_eval_risk_impact_mapping_missing_impact_areas(self):
        """Test MAP-3.2 fails when risks lack impact_areas."""
        svc = NISTMapService()
        allowed, reason, details = svc._evaluate_risk_impact_mapping({
            "ai_systems": [
                {
                    "name": "chatbot",
                    "dependencies": [{"name": "openai", "type": "api"}],
                },
            ],
            "risks": [
                {
                    "impact_areas": [],
                    "affected_stakeholders": ["customers"],
                },
            ],
        })
        assert allowed is False
        assert "missing impact_areas" in reason


# =============================================================================
# Utility Method Tests
# =============================================================================


class TestUtilityMethods:
    """Tests for private utility methods."""

    def test_risk_level_from_score_critical(self):
        """Test score >= 16 returns critical."""
        svc = NISTMapService()
        assert svc._risk_level_from_score(16) == "critical"
        assert svc._risk_level_from_score(25) == "critical"

    def test_risk_level_from_score_high(self):
        """Test score 10-15 returns high."""
        svc = NISTMapService()
        assert svc._risk_level_from_score(10) == "high"
        assert svc._risk_level_from_score(15) == "high"

    def test_risk_level_from_score_medium(self):
        """Test score 5-9 returns medium."""
        svc = NISTMapService()
        assert svc._risk_level_from_score(5) == "medium"
        assert svc._risk_level_from_score(9) == "medium"

    def test_risk_level_from_score_low(self):
        """Test score 1-4 returns low."""
        svc = NISTMapService()
        assert svc._risk_level_from_score(1) == "low"
        assert svc._risk_level_from_score(4) == "low"

    def test_derive_impact_areas_safety(self):
        """Test safety category derives correct impact areas."""
        svc = NISTMapService()
        areas = svc._derive_impact_areas("safety", "Physical harm potential")
        assert "human_safety" in areas
        assert "physical_harm" in areas

    def test_derive_impact_areas_unknown_category(self):
        """Test unknown category returns general_operational_impact."""
        svc = NISTMapService()
        areas = svc._derive_impact_areas("unknown", None)
        assert "general_operational_impact" in areas

    def test_derive_affected_stakeholders_privacy(self):
        """Test privacy category derives correct stakeholders."""
        svc = NISTMapService()
        stakeholders = svc._derive_affected_stakeholders("privacy", "Data breach affecting customers")
        assert "data_subjects" in stakeholders
        assert "customers" in stakeholders

    def test_derive_affected_stakeholders_unknown(self):
        """Test unknown category returns project_stakeholders."""
        svc = NISTMapService()
        stakeholders = svc._derive_affected_stakeholders("unknown", None)
        assert "project_stakeholders" in stakeholders

    def test_build_opa_input_structure(self):
        """Test OPA input builder creates correct structure."""
        svc = NISTMapService()
        result = svc._build_opa_input(
            ai_systems=[
                {
                    "name": "chatbot",
                    "purpose": "Support",
                    "scope": "Prod",
                    "owner": "lead",
                    "stakeholders": [{"role": "user", "name": "cust"}],
                    "categorization": {"risk_tier": "limited"},
                    "dependencies": [{"name": "openai", "type": "api"}],
                    "system_type": "nlp",
                },
            ],
            risks=[
                {
                    "impact_areas": ["area1"],
                    "affected_stakeholders": ["stakeholder1"],
                    "category": "safety",
                    "title": "Test risk",
                },
            ],
        )

        assert len(result["ai_systems"]) == 1
        assert result["ai_systems"][0]["name"] == "chatbot"
        assert result["ai_systems"][0]["purpose"] == "Support"
        assert len(result["risks"]) == 1
        assert result["risks"][0]["impact_areas"] == ["area1"]
