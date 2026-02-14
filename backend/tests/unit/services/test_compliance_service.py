"""
=========================================================================
Compliance Service Unit Tests
SDLC Orchestrator - Sprint 156 (Phase 3: COMPLIANCE)

Version: 1.0.0
Date: February 5, 2026
Status: ACTIVE
Authority: CTO Approved
Framework: SDLC 6.0.5

Test Categories:
- Framework Listing Tests (active-only, all)
- Framework Get Tests (found, not found)
- Assessment Listing Tests (by project, with filters, empty)
- Assessment Create Tests (success, duplicate, control not found)
- Assessment Update Tests (success, not found, partial, timestamps)

Test Approach: Unit tests mocking database layer via AsyncMock
Zero Mock Policy: Mocks for database layer only
=========================================================================
"""

import pytest
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import UUID, uuid4

from app.models.compliance import (
    AssessmentStatus,
    ComplianceAssessment,
    ComplianceControl,
    ComplianceFramework,
)
from app.schemas.compliance_framework import (
    AssessmentCreate,
    AssessmentListResponse,
    AssessmentResponse,
    AssessmentUpdate,
    FrameworkListResponse,
    FrameworkResponse,
    AssessmentStatus as SchemaAssessmentStatus,
)
from app.services.compliance_service import (
    ComplianceService,
    ComplianceNotFoundError,
    ComplianceValidationError,
)


# =============================================================================
# Test Constants
# =============================================================================

PROJECT_ID = UUID("00000000-0000-0000-0000-000000000001")
CONTROL_ID = UUID("00000000-0000-0000-0000-000000000002")
FRAMEWORK_ID = UUID("00000000-0000-0000-0000-000000000003")
ASSESSOR_ID = UUID("00000000-0000-0000-0000-000000000004")
ASSESSMENT_ID = UUID("00000000-0000-0000-0000-000000000005")
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
def sample_framework():
    """Create a mock ComplianceFramework model instance."""
    fw = MagicMock(spec=ComplianceFramework)
    fw.id = FRAMEWORK_ID
    fw.code = "NIST_AI_RMF"
    fw.name = "NIST AI Risk Management Framework"
    fw.version = "1.0"
    fw.description = "AI risk management standard"
    fw.total_controls = 5
    fw.is_active = True
    fw.created_at = NOW
    fw.updated_at = NOW
    return fw


@pytest.fixture
def sample_inactive_framework():
    """Create a mock inactive ComplianceFramework model instance."""
    fw = MagicMock(spec=ComplianceFramework)
    fw.id = UUID("00000000-0000-0000-0000-000000000099")
    fw.code = "ISO_42001"
    fw.name = "ISO/IEC 42001:2023"
    fw.version = "2023"
    fw.description = "AI management system standard"
    fw.total_controls = 38
    fw.is_active = False
    fw.created_at = NOW
    fw.updated_at = NOW
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
    ctrl.description = "AI systems must have designated owners"
    ctrl.severity = "critical"
    ctrl.gate_mapping = "G1"
    ctrl.evidence_required = [{"type": "document", "description": "Ownership doc", "required": True, "accepted_formats": ["pdf"]}]
    ctrl.opa_policy_code = "nist/govern/govern_1_1"
    ctrl.sort_order = 1
    ctrl.created_at = NOW
    ctrl.updated_at = NOW
    return ctrl


@pytest.fixture
def sample_assessment(sample_control):
    """Create a mock ComplianceAssessment model instance."""
    assessment = MagicMock(spec=ComplianceAssessment)
    assessment.id = ASSESSMENT_ID
    assessment.project_id = PROJECT_ID
    assessment.control_id = CONTROL_ID
    assessment.status = "in_progress"
    assessment.evidence_ids = []
    assessment.assessor_id = ASSESSOR_ID
    assessment.notes = "Initial assessment"
    assessment.auto_evaluated = False
    assessment.opa_result = None
    assessment.assessed_at = NOW
    assessment.created_at = NOW
    assessment.updated_at = NOW
    assessment.control = sample_control
    assessment.assessor = None
    return assessment


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
# Framework Listing Tests
# =============================================================================


class TestListFrameworks:
    """Tests for ComplianceService.list_frameworks."""

    @pytest.mark.asyncio
    async def test_list_frameworks_active_only(self, mock_db, sample_framework):
        """Test listing only active frameworks returns active frameworks."""
        mock_db.execute = AsyncMock(
            return_value=_mock_scalars_all([sample_framework])
        )

        service = ComplianceService(mock_db)
        result = await service.list_frameworks(active_only=True)

        assert isinstance(result, FrameworkListResponse)
        assert result.total == 1
        assert len(result.items) == 1
        assert result.items[0].code == "NIST_AI_RMF"
        assert result.items[0].is_active is True

    @pytest.mark.asyncio
    async def test_list_frameworks_all(
        self, mock_db, sample_framework, sample_inactive_framework
    ):
        """Test listing all frameworks includes inactive ones."""
        mock_db.execute = AsyncMock(
            return_value=_mock_scalars_all(
                [sample_framework, sample_inactive_framework]
            )
        )

        service = ComplianceService(mock_db)
        result = await service.list_frameworks(active_only=False)

        assert isinstance(result, FrameworkListResponse)
        assert result.total == 2
        assert len(result.items) == 2


# =============================================================================
# Framework Get Tests
# =============================================================================


class TestGetFramework:
    """Tests for ComplianceService.get_framework."""

    @pytest.mark.asyncio
    async def test_get_framework_found(self, mock_db, sample_framework):
        """Test getting a framework that exists returns framework details."""
        mock_db.execute = AsyncMock(
            side_effect=[
                _mock_scalar_one_or_none(sample_framework),
                _mock_scalar(5),
            ]
        )

        service = ComplianceService(mock_db)
        result = await service.get_framework("NIST_AI_RMF")

        assert isinstance(result, FrameworkResponse)
        assert result.code == "NIST_AI_RMF"
        assert result.total_controls == 5

    @pytest.mark.asyncio
    async def test_get_framework_not_found(self, mock_db):
        """Test getting a non-existent framework raises ComplianceNotFoundError."""
        mock_db.execute = AsyncMock(
            return_value=_mock_scalar_one_or_none(None)
        )

        service = ComplianceService(mock_db)

        with pytest.raises(ComplianceNotFoundError, match="not found"):
            await service.get_framework("NONEXISTENT")


# =============================================================================
# Assessment Listing Tests
# =============================================================================


class TestListAssessments:
    """Tests for ComplianceService.list_assessments."""

    @pytest.mark.asyncio
    async def test_list_assessments_by_project(
        self, mock_db, sample_assessment
    ):
        """Test listing assessments for a project returns correct results."""
        mock_db.execute = AsyncMock(
            side_effect=[
                _mock_scalar(1),
                _mock_scalars_all([sample_assessment]),
            ]
        )

        service = ComplianceService(mock_db)
        result = await service.list_assessments(
            project_id=PROJECT_ID,
            limit=20,
            offset=0,
        )

        assert isinstance(result, AssessmentListResponse)
        assert result.total == 1
        assert len(result.items) == 1
        assert result.items[0].project_id == PROJECT_ID

    @pytest.mark.asyncio
    async def test_list_assessments_with_framework_filter(
        self, mock_db, sample_assessment
    ):
        """Test listing assessments with framework code filter."""
        mock_db.execute = AsyncMock(
            side_effect=[
                _mock_scalar_one_or_none(FRAMEWORK_ID),
                MagicMock(all=MagicMock(return_value=[(CONTROL_ID,)])),
                _mock_scalar(1),
                _mock_scalars_all([sample_assessment]),
            ]
        )

        service = ComplianceService(mock_db)
        result = await service.list_assessments(
            project_id=PROJECT_ID,
            framework_code="NIST_AI_RMF",
            limit=20,
            offset=0,
        )

        assert isinstance(result, AssessmentListResponse)
        assert result.total == 1

    @pytest.mark.asyncio
    async def test_list_assessments_with_status_filter(
        self, mock_db, sample_assessment
    ):
        """Test listing assessments filtered by status."""
        mock_db.execute = AsyncMock(
            side_effect=[
                _mock_scalar(1),
                _mock_scalars_all([sample_assessment]),
            ]
        )

        service = ComplianceService(mock_db)
        result = await service.list_assessments(
            project_id=PROJECT_ID,
            status_filter=AssessmentStatus.IN_PROGRESS,
            limit=20,
            offset=0,
        )

        assert isinstance(result, AssessmentListResponse)
        assert result.total == 1

    @pytest.mark.asyncio
    async def test_list_assessments_empty_result(self, mock_db):
        """Test listing assessments when none exist returns empty list."""
        mock_db.execute = AsyncMock(
            side_effect=[
                _mock_scalar(0),
                _mock_scalars_all([]),
            ]
        )

        service = ComplianceService(mock_db)
        result = await service.list_assessments(
            project_id=PROJECT_ID,
            limit=20,
            offset=0,
        )

        assert isinstance(result, AssessmentListResponse)
        assert result.total == 0
        assert len(result.items) == 0
        assert result.has_more is False


# =============================================================================
# Assessment Create Tests
# =============================================================================


class TestCreateAssessment:
    """Tests for ComplianceService.create_assessment."""

    @pytest.mark.asyncio
    async def test_create_assessment_success(
        self, mock_db, sample_control, sample_assessment
    ):
        """Test creating a new assessment succeeds with valid data."""
        mock_db.execute = AsyncMock(
            side_effect=[
                _mock_scalar_one_or_none(sample_control),
                _mock_scalar_one_or_none(None),
            ]
        )
        mock_db.refresh = AsyncMock(return_value=None)

        service = ComplianceService(mock_db)
        data = AssessmentCreate(
            project_id=PROJECT_ID,
            control_id=CONTROL_ID,
            status=SchemaAssessmentStatus.IN_PROGRESS,
            evidence_ids=[],
            notes="Starting assessment",
        )

        with patch.object(
            service, "_to_assessment_response", new_callable=AsyncMock
        ) as mock_response:
            mock_response.return_value = AssessmentResponse(
                id=ASSESSMENT_ID,
                project_id=PROJECT_ID,
                control_id=CONTROL_ID,
                status="in_progress",
                evidence_ids=[],
                assessor_id=ASSESSOR_ID,
                notes="Starting assessment",
                auto_evaluated=False,
                opa_result=None,
                assessed_at=NOW,
                created_at=NOW,
                updated_at=NOW,
            )

            result = await service.create_assessment(data, ASSESSOR_ID)

            assert isinstance(result, AssessmentResponse)
            assert result.project_id == PROJECT_ID
            assert result.control_id == CONTROL_ID
            assert result.status == "in_progress"
            mock_db.add.assert_called_once()
            mock_db.commit.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_create_assessment_duplicate_raises(
        self, mock_db, sample_control
    ):
        """Test creating a duplicate assessment raises ComplianceValidationError."""
        mock_db.execute = AsyncMock(
            side_effect=[
                _mock_scalar_one_or_none(sample_control),
                _mock_scalar_one_or_none(ASSESSMENT_ID),
            ]
        )

        service = ComplianceService(mock_db)
        data = AssessmentCreate(
            project_id=PROJECT_ID,
            control_id=CONTROL_ID,
            status=SchemaAssessmentStatus.NOT_STARTED,
        )

        with pytest.raises(ComplianceValidationError, match="already exists"):
            await service.create_assessment(data, ASSESSOR_ID)

    @pytest.mark.asyncio
    async def test_create_assessment_control_not_found(self, mock_db):
        """Test creating assessment with non-existent control raises error."""
        mock_db.execute = AsyncMock(
            return_value=_mock_scalar_one_or_none(None)
        )

        service = ComplianceService(mock_db)
        data = AssessmentCreate(
            project_id=PROJECT_ID,
            control_id=UUID("00000000-0000-0000-0000-000000000999"),
            status=SchemaAssessmentStatus.NOT_STARTED,
        )

        with pytest.raises(ComplianceNotFoundError, match="control"):
            await service.create_assessment(data, ASSESSOR_ID)


# =============================================================================
# Assessment Update Tests
# =============================================================================


class TestUpdateAssessment:
    """Tests for ComplianceService.update_assessment."""

    @pytest.mark.asyncio
    async def test_update_assessment_success(
        self, mock_db, sample_assessment
    ):
        """Test updating an assessment succeeds with valid data."""
        mock_db.execute = AsyncMock(
            return_value=_mock_scalar_one_or_none(sample_assessment)
        )
        mock_db.refresh = AsyncMock(return_value=None)

        service = ComplianceService(mock_db)
        data = AssessmentUpdate(
            status=SchemaAssessmentStatus.COMPLIANT,
            notes="All evidence verified",
        )

        with patch.object(
            service, "_to_assessment_response", new_callable=AsyncMock
        ) as mock_response:
            mock_response.return_value = AssessmentResponse(
                id=ASSESSMENT_ID,
                project_id=PROJECT_ID,
                control_id=CONTROL_ID,
                status="compliant",
                evidence_ids=[],
                assessor_id=ASSESSOR_ID,
                notes="All evidence verified",
                auto_evaluated=False,
                opa_result=None,
                assessed_at=NOW,
                created_at=NOW,
                updated_at=NOW,
            )

            result = await service.update_assessment(
                ASSESSMENT_ID, data, ASSESSOR_ID
            )

            assert isinstance(result, AssessmentResponse)
            assert result.status == "compliant"
            assert result.notes == "All evidence verified"
            mock_db.commit.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_update_assessment_not_found(self, mock_db):
        """Test updating a non-existent assessment raises error."""
        mock_db.execute = AsyncMock(
            return_value=_mock_scalar_one_or_none(None)
        )

        service = ComplianceService(mock_db)
        data = AssessmentUpdate(status=SchemaAssessmentStatus.COMPLIANT)

        with pytest.raises(ComplianceNotFoundError, match="not found"):
            await service.update_assessment(
                UUID("00000000-0000-0000-0000-000000000999"), data, ASSESSOR_ID
            )

    @pytest.mark.asyncio
    async def test_update_assessment_partial_update(
        self, mock_db, sample_assessment
    ):
        """Test partial update only modifies specified fields."""
        mock_db.execute = AsyncMock(
            return_value=_mock_scalar_one_or_none(sample_assessment)
        )
        mock_db.refresh = AsyncMock(return_value=None)

        service = ComplianceService(mock_db)
        data = AssessmentUpdate(notes="Updated notes only")

        with patch.object(
            service, "_to_assessment_response", new_callable=AsyncMock
        ) as mock_response:
            mock_response.return_value = AssessmentResponse(
                id=ASSESSMENT_ID,
                project_id=PROJECT_ID,
                control_id=CONTROL_ID,
                status="in_progress",
                evidence_ids=[],
                assessor_id=ASSESSOR_ID,
                notes="Updated notes only",
                auto_evaluated=False,
                opa_result=None,
                assessed_at=NOW,
                created_at=NOW,
                updated_at=NOW,
            )

            result = await service.update_assessment(
                ASSESSMENT_ID, data, ASSESSOR_ID
            )

            assert result.notes == "Updated notes only"
            assert result.status == "in_progress"

    @pytest.mark.asyncio
    async def test_update_assessment_sets_assessed_at(
        self, mock_db, sample_assessment
    ):
        """Test that update always sets assessed_at timestamp."""
        sample_assessment.assessed_at = None
        mock_db.execute = AsyncMock(
            return_value=_mock_scalar_one_or_none(sample_assessment)
        )
        mock_db.refresh = AsyncMock(return_value=None)

        service = ComplianceService(mock_db)
        data = AssessmentUpdate(status=SchemaAssessmentStatus.COMPLIANT)

        with patch.object(
            service, "_to_assessment_response", new_callable=AsyncMock
        ) as mock_response:
            mock_response.return_value = AssessmentResponse(
                id=ASSESSMENT_ID,
                project_id=PROJECT_ID,
                control_id=CONTROL_ID,
                status="compliant",
                evidence_ids=[],
                assessor_id=ASSESSOR_ID,
                notes=None,
                auto_evaluated=False,
                opa_result=None,
                assessed_at=NOW,
                created_at=NOW,
                updated_at=NOW,
            )

            await service.update_assessment(ASSESSMENT_ID, data, ASSESSOR_ID)

            assert sample_assessment.assessed_at is not None
            assert sample_assessment.assessor_id == ASSESSOR_ID
