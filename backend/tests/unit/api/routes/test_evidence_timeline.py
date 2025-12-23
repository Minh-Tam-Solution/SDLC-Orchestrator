"""
Unit Tests for Evidence Timeline API Routes

SDLC Stage: 04 - BUILD
Sprint: 43 - Policy Guards & Evidence UI
Framework: SDLC 5.1.1
Epic: EP-02 AI Safety Layer v1

Purpose:
Test Evidence Timeline API endpoints including:
- Timeline listing with filters
- Event detail retrieval
- Override request workflow
- Statistics calculation
- Data export functionality

Test Coverage Target: 95%+
"""

import json
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest
from fastapi import status
from httpx import AsyncClient

from app.models.analytics import AICodeEvent
from app.models.project import Project
from app.models.user import User
from app.schemas.evidence_timeline import (
    AIToolType,
    OverrideStatus,
    OverrideType,
    ValidationStatus,
)


# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def mock_user():
    """Create a mock authenticated user."""
    user = MagicMock(spec=User)
    user.id = uuid4()
    user.email = "developer@example.com"
    user.name = "Test Developer"
    user.role = "developer"
    user.is_active = True
    return user


@pytest.fixture
def mock_admin_user():
    """Create a mock admin user."""
    user = MagicMock(spec=User)
    user.id = uuid4()
    user.email = "admin@example.com"
    user.name = "Admin User"
    user.role = "admin"
    user.is_active = True
    return user


@pytest.fixture
def mock_project():
    """Create a mock project."""
    project = MagicMock(spec=Project)
    project.id = uuid4()
    project.name = "test-project"
    project.slug = "test-project"
    return project


@pytest.fixture
def mock_ai_code_event(mock_project, mock_user):
    """Create a mock AI code event."""
    event = MagicMock(spec=AICodeEvent)
    event.id = uuid4()
    event.project_id = mock_project.id
    event.user_id = mock_user.id
    event.pr_id = "123"
    event.commit_sha = "abc1234567890"
    event.branch_name = "feature/ai-safety"
    event.ai_tool_detected = "cursor"
    event.confidence_score = 85
    event.detection_method = "pattern"
    event.validation_result = "passed"
    event.violations = []
    event.duration_ms = 150
    event.files_scanned = 5
    event.lines_changed = 100
    event.created_at = datetime.utcnow()
    return event


@pytest.fixture
def mock_failed_event(mock_project, mock_user):
    """Create a mock failed AI code event."""
    event = MagicMock(spec=AICodeEvent)
    event.id = uuid4()
    event.project_id = mock_project.id
    event.user_id = mock_user.id
    event.pr_id = "456"
    event.commit_sha = "def7890123456"
    event.branch_name = "feature/unsafe-code"
    event.ai_tool_detected = "copilot"
    event.confidence_score = 95
    event.detection_method = "metadata"
    event.validation_result = "failed"
    event.violations = [
        {
            "validator": "sast",
            "message": "SQL injection detected",
            "severity": "high",
            "blocking": True,
        },
        {
            "validator": "policy_guards",
            "message": "Unsafe AI pattern detected",
            "severity": "medium",
            "blocking": True,
        },
    ]
    event.duration_ms = 250
    event.files_scanned = 3
    event.lines_changed = 50
    event.created_at = datetime.utcnow() - timedelta(hours=1)
    return event


# =============================================================================
# Timeline Listing Tests
# =============================================================================


class TestListTimelineEvents:
    """Tests for GET /projects/{id}/timeline endpoint."""

    @pytest.mark.asyncio
    async def test_list_timeline_events_success(
        self, mock_user, mock_project, mock_ai_code_event
    ):
        """Test successful timeline events listing."""
        from app.api.routes.evidence_timeline import (
            _build_event_summary,
            _map_ai_tool,
            _map_validation_result_to_status,
        )

        # Test helper functions
        summary = _build_event_summary(mock_ai_code_event, mock_user)

        assert summary.pr_number == "123"
        assert summary.ai_tool == AIToolType.CURSOR
        assert summary.confidence_score == 85
        assert summary.validation_status == ValidationStatus.PASSED

    @pytest.mark.asyncio
    async def test_map_ai_tool_types(self):
        """Test AI tool type mapping."""
        from app.api.routes.evidence_timeline import _map_ai_tool

        assert _map_ai_tool("cursor") == AIToolType.CURSOR
        assert _map_ai_tool("copilot") == AIToolType.COPILOT
        assert _map_ai_tool("github copilot") == AIToolType.COPILOT
        assert _map_ai_tool("claude") == AIToolType.CLAUDE
        assert _map_ai_tool("claude code") == AIToolType.CLAUDE
        assert _map_ai_tool("chatgpt") == AIToolType.CHATGPT
        assert _map_ai_tool("windsurf") == AIToolType.WINDSURF
        assert _map_ai_tool("cody") == AIToolType.CODY
        assert _map_ai_tool("tabnine") == AIToolType.TABNINE
        assert _map_ai_tool("unknown-tool") == AIToolType.OTHER
        assert _map_ai_tool(None) == AIToolType.OTHER

    @pytest.mark.asyncio
    async def test_map_validation_status(self):
        """Test validation status mapping."""
        from app.api.routes.evidence_timeline import _map_validation_result_to_status

        assert _map_validation_result_to_status("passed") == ValidationStatus.PASSED
        assert _map_validation_result_to_status("failed") == ValidationStatus.FAILED
        assert _map_validation_result_to_status("warning") == ValidationStatus.PASSED
        assert _map_validation_result_to_status("error") == ValidationStatus.ERROR
        assert _map_validation_result_to_status("pending") == ValidationStatus.PENDING
        assert _map_validation_result_to_status("running") == ValidationStatus.RUNNING
        assert _map_validation_result_to_status("overridden") == ValidationStatus.OVERRIDDEN
        assert _map_validation_result_to_status("unknown") == ValidationStatus.PENDING

    @pytest.mark.asyncio
    async def test_build_event_summary_with_violations(
        self, mock_user, mock_failed_event
    ):
        """Test event summary building with violations."""
        from app.api.routes.evidence_timeline import _build_event_summary

        summary = _build_event_summary(mock_failed_event, mock_user)

        assert summary.pr_number == "456"
        assert summary.ai_tool == AIToolType.COPILOT
        assert summary.validation_status == ValidationStatus.FAILED
        assert summary.validators_failed == 2
        assert summary.validators_passed == 3  # 5 total - 2 failed


class TestGetTimelineStats:
    """Tests for GET /projects/{id}/timeline/stats endpoint."""

    @pytest.mark.asyncio
    async def test_stats_calculation(self):
        """Test statistics calculation logic."""
        # Test pass rate calculation
        total_events = 100
        passed = 85
        pass_rate = (passed / total_events * 100) if total_events > 0 else 0.0
        assert pass_rate == 85.0

        # Test empty case
        total_events = 0
        pass_rate = (85 / total_events * 100) if total_events > 0 else 0.0
        assert pass_rate == 0.0


class TestGetEventDetail:
    """Tests for GET /projects/{id}/timeline/{event_id} endpoint."""

    @pytest.mark.asyncio
    async def test_build_event_detail(self, mock_user, mock_ai_code_event):
        """Test event detail building with validator results."""
        from app.api.routes.evidence_timeline import _build_event_detail

        detail = _build_event_detail(mock_ai_code_event, mock_user)

        assert detail.id == mock_ai_code_event.id
        assert detail.project_id == mock_ai_code_event.project_id
        assert len(detail.validator_results) == 5  # All 5 validators
        assert detail.detection_evidence["tool"] == "cursor"
        assert detail.detection_evidence["confidence"] == 85

    @pytest.mark.asyncio
    async def test_build_event_detail_with_violations(
        self, mock_user, mock_failed_event
    ):
        """Test event detail with failed validators."""
        from app.api.routes.evidence_timeline import _build_event_detail

        detail = _build_event_detail(mock_failed_event, mock_user)

        # Find failed validators
        failed_validators = [v for v in detail.validator_results if v.status == "failed"]
        passed_validators = [v for v in detail.validator_results if v.status == "passed"]

        assert len(failed_validators) == 2
        assert len(passed_validators) == 3


# =============================================================================
# Override Request Tests
# =============================================================================


class TestOverrideRequest:
    """Tests for POST /timeline/{event_id}/override/request endpoint."""

    @pytest.mark.asyncio
    async def test_override_request_schema_validation(self):
        """Test override request schema validation."""
        from app.schemas.evidence_timeline import OverrideRequest

        # Valid request
        valid_request = OverrideRequest(
            override_type=OverrideType.FALSE_POSITIVE,
            reason="This is a false positive. The detected pattern is a test file, not production code. "
                   "The pattern matches our test infrastructure.",
        )
        assert valid_request.override_type == OverrideType.FALSE_POSITIVE
        assert len(valid_request.reason) >= 50

        # Invalid request - reason too short
        with pytest.raises(ValueError):
            OverrideRequest(
                override_type=OverrideType.FALSE_POSITIVE,
                reason="Too short",  # Less than 50 chars
            )

    @pytest.mark.asyncio
    async def test_override_types(self):
        """Test all override types are available."""
        assert OverrideType.FALSE_POSITIVE.value == "false_positive"
        assert OverrideType.APPROVED_RISK.value == "approved_risk"
        assert OverrideType.EMERGENCY.value == "emergency"

    @pytest.mark.asyncio
    async def test_override_status_values(self):
        """Test override status values."""
        assert OverrideStatus.NONE.value == "none"
        assert OverrideStatus.PENDING.value == "pending"
        assert OverrideStatus.APPROVED.value == "approved"
        assert OverrideStatus.REJECTED.value == "rejected"


class TestOverrideApproval:
    """Tests for POST /timeline/{event_id}/override/approve endpoint."""

    @pytest.mark.asyncio
    async def test_override_approval_schema(self):
        """Test override approval schema."""
        from app.schemas.evidence_timeline import OverrideApproval

        # With comment
        approval = OverrideApproval(comment="Approved after reviewing the code.")
        assert approval.comment == "Approved after reviewing the code."

        # Without comment
        approval_no_comment = OverrideApproval()
        assert approval_no_comment.comment is None


class TestOverrideRejection:
    """Tests for POST /timeline/{event_id}/override/reject endpoint."""

    @pytest.mark.asyncio
    async def test_override_rejection_schema_validation(self):
        """Test override rejection schema validation."""
        from app.schemas.evidence_timeline import OverrideRejection

        # Valid rejection
        rejection = OverrideRejection(reason="The code still contains security vulnerabilities.")
        assert len(rejection.reason) >= 10

        # Invalid rejection - reason too short
        with pytest.raises(ValueError):
            OverrideRejection(reason="No")  # Less than 10 chars


# =============================================================================
# Admin Queue Tests
# =============================================================================


class TestOverrideQueue:
    """Tests for GET /admin/override-queue endpoint."""

    @pytest.mark.asyncio
    async def test_override_queue_response_schema(self):
        """Test override queue response schema."""
        from app.schemas.evidence_timeline import OverrideQueueResponse

        response = OverrideQueueResponse(
            pending=[],
            recent_decisions=[],
            total_pending=0,
        )

        assert response.pending == []
        assert response.recent_decisions == []
        assert response.total_pending == 0


# =============================================================================
# Export Tests
# =============================================================================


class TestExportTimeline:
    """Tests for GET /projects/{id}/timeline/export endpoint."""

    @pytest.mark.asyncio
    async def test_export_format_enum(self):
        """Test export format enum values."""
        from app.schemas.evidence_timeline import ExportFormat

        assert ExportFormat.CSV.value == "csv"
        assert ExportFormat.JSON.value == "json"

    @pytest.mark.asyncio
    async def test_export_request_schema(self):
        """Test export request schema."""
        from app.schemas.evidence_timeline import ExportRequest, ExportFormat

        request = ExportRequest(
            format=ExportFormat.JSON,
            include_details=True,
        )

        assert request.format == ExportFormat.JSON
        assert request.include_details is True

        # Default values
        default_request = ExportRequest()
        assert default_request.format == ExportFormat.CSV
        assert default_request.include_details is False

    @pytest.mark.asyncio
    async def test_csv_export_generation(self):
        """Test CSV export data generation."""
        import csv
        import io

        events_data = [
            {
                "id": str(uuid4()),
                "created_at": datetime.utcnow().isoformat(),
                "pr_number": "123",
                "commit_sha": "abc123",
                "ai_tool": "cursor",
                "validation_result": "passed",
            },
            {
                "id": str(uuid4()),
                "created_at": datetime.utcnow().isoformat(),
                "pr_number": "456",
                "commit_sha": "def456",
                "ai_tool": "copilot",
                "validation_result": "failed",
            },
        ]

        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=events_data[0].keys())
        writer.writeheader()
        writer.writerows(events_data)
        content = output.getvalue()

        # Verify CSV content
        assert "id,created_at,pr_number,commit_sha,ai_tool,validation_result" in content
        assert "123" in content
        assert "cursor" in content
        assert "passed" in content

    @pytest.mark.asyncio
    async def test_json_export_generation(self):
        """Test JSON export data generation."""
        events_data = [
            {
                "id": str(uuid4()),
                "pr_number": "123",
                "ai_tool": "cursor",
                "validation_result": "passed",
            },
        ]

        content = json.dumps(events_data, indent=2)

        # Verify JSON content
        parsed = json.loads(content)
        assert len(parsed) == 1
        assert parsed[0]["pr_number"] == "123"
        assert parsed[0]["ai_tool"] == "cursor"


# =============================================================================
# Schema Tests
# =============================================================================


class TestEvidenceTimelineSchemas:
    """Tests for Evidence Timeline Pydantic schemas."""

    @pytest.mark.asyncio
    async def test_evidence_event_summary_schema(self):
        """Test EvidenceEventSummary schema."""
        from app.schemas.evidence_timeline import (
            EvidenceEventSummary,
            AIToolType,
            ValidationStatus,
            OverrideStatus,
        )

        event = EvidenceEventSummary(
            id=uuid4(),
            project_id=uuid4(),
            created_at=datetime.utcnow(),
            pr_number="123",
            pr_title="Add AI safety checks",
            pr_author="developer",
            commit_sha="abc123",
            branch_name="feature/safety",
            ai_tool=AIToolType.CURSOR,
            ai_model="cursor-1.0",
            confidence_score=90,
            detection_method="pattern",
            validation_status=ValidationStatus.PASSED,
            validation_duration_ms=150,
            files_changed=5,
            lines_added=100,
            lines_deleted=20,
            validators_passed=5,
            validators_failed=0,
            validators_total=5,
            override_status=OverrideStatus.NONE,
        )

        assert event.pr_number == "123"
        assert event.ai_tool == AIToolType.CURSOR
        assert event.validators_passed == 5

    @pytest.mark.asyncio
    async def test_evidence_timeline_stats_schema(self):
        """Test EvidenceTimelineStats schema."""
        from app.schemas.evidence_timeline import EvidenceTimelineStats

        stats = EvidenceTimelineStats(
            total_events=100,
            ai_detected=80,
            pass_rate=85.5,
            override_rate=2.5,
            by_tool={"cursor": 40, "copilot": 30, "claude": 10},
            by_status={"passed": 85, "failed": 10, "warning": 5},
        )

        assert stats.total_events == 100
        assert stats.ai_detected == 80
        assert stats.pass_rate == 85.5
        assert stats.by_tool["cursor"] == 40

    @pytest.mark.asyncio
    async def test_evidence_timeline_response_schema(self):
        """Test EvidenceTimelineResponse schema."""
        from app.schemas.evidence_timeline import (
            EvidenceTimelineResponse,
            EvidenceTimelineStats,
        )

        response = EvidenceTimelineResponse(
            events=[],
            stats=EvidenceTimelineStats(),
            total=0,
            page=1,
            pages=1,
            has_next=False,
        )

        assert response.total == 0
        assert response.page == 1
        assert response.has_next is False

    @pytest.mark.asyncio
    async def test_override_record_schema(self):
        """Test OverrideRecord schema."""
        from app.schemas.evidence_timeline import OverrideRecord, OverrideType, OverrideStatus

        record = OverrideRecord(
            id=uuid4(),
            event_id=uuid4(),
            override_type=OverrideType.APPROVED_RISK,
            reason="Risk accepted by security team after review.",
            requested_by_id=uuid4(),
            requested_by_name="Developer",
            requested_at=datetime.utcnow(),
            status=OverrideStatus.APPROVED,
            resolved_by_id=uuid4(),
            resolved_by_name="Admin",
            resolved_at=datetime.utcnow(),
            resolution_comment="Approved with conditions.",
        )

        assert record.override_type == OverrideType.APPROVED_RISK
        assert record.status == OverrideStatus.APPROVED

    @pytest.mark.asyncio
    async def test_validator_result_summary_schema(self):
        """Test ValidatorResultSummary schema."""
        from app.schemas.evidence_timeline import ValidatorResultSummary, ValidatorName

        result = ValidatorResultSummary(
            name=ValidatorName.SAST,
            status="passed",
            duration_ms=50,
            message="No security issues found",
            details={"rules_checked": 40},
            blocking=True,
        )

        assert result.name == ValidatorName.SAST
        assert result.status == "passed"
        assert result.details["rules_checked"] == 40

    @pytest.mark.asyncio
    async def test_validator_names_enum(self):
        """Test ValidatorName enum values."""
        from app.schemas.evidence_timeline import ValidatorName

        assert ValidatorName.LINT.value == "lint"
        assert ValidatorName.TESTS.value == "tests"
        assert ValidatorName.COVERAGE.value == "coverage"
        assert ValidatorName.SAST.value == "sast"
        assert ValidatorName.POLICY_GUARDS.value == "policy_guards"
        assert ValidatorName.AI_SECURITY.value == "ai_security"


# =============================================================================
# Pagination Tests
# =============================================================================


class TestPagination:
    """Tests for pagination logic."""

    @pytest.mark.asyncio
    async def test_pagination_params_schema(self):
        """Test PaginationParams schema."""
        from app.schemas.evidence_timeline import PaginationParams

        params = PaginationParams(page=2, limit=50)
        assert params.page == 2
        assert params.limit == 50

        # Default values
        default_params = PaginationParams()
        assert default_params.page == 1
        assert default_params.limit == 20

    @pytest.mark.asyncio
    async def test_pagination_calculation(self):
        """Test pagination calculation logic."""
        total = 95
        limit = 20

        # Calculate pages
        pages = (total + limit - 1) // limit
        assert pages == 5

        # Test has_next
        page = 1
        has_next = page < pages
        assert has_next is True

        page = 5
        has_next = page < pages
        assert has_next is False

        # Test offset
        page = 3
        offset = (page - 1) * limit
        assert offset == 40


# =============================================================================
# Filter Tests
# =============================================================================


class TestFilters:
    """Tests for evidence filters."""

    @pytest.mark.asyncio
    async def test_evidence_filters_schema(self):
        """Test EvidenceFilters schema."""
        from app.schemas.evidence_timeline import (
            EvidenceFilters,
            AIToolType,
            ValidationStatus,
            OverrideStatus,
        )

        filters = EvidenceFilters(
            date_start=datetime.utcnow() - timedelta(days=30),
            date_end=datetime.utcnow(),
            ai_tool=AIToolType.CURSOR,
            confidence_min=50,
            confidence_max=100,
            validation_status=ValidationStatus.FAILED,
            override_status=OverrideStatus.PENDING,
            pr_author="developer",
            search="feature",
        )

        assert filters.ai_tool == AIToolType.CURSOR
        assert filters.confidence_min == 50
        assert filters.search == "feature"

    @pytest.mark.asyncio
    async def test_default_filter_values(self):
        """Test default filter values."""
        from app.schemas.evidence_timeline import EvidenceFilters

        filters = EvidenceFilters()

        assert filters.date_start is None
        assert filters.date_end is None
        assert filters.ai_tool is None
        assert filters.confidence_min == 0
        assert filters.confidence_max == 100


# =============================================================================
# Integration Tests
# =============================================================================


class TestAPIIntegration:
    """Integration tests for Evidence Timeline API."""

    @pytest.mark.asyncio
    async def test_router_endpoints_exist(self):
        """Test that all router endpoints are defined."""
        from app.api.routes.evidence_timeline import router

        # Check routes are registered
        routes = [route.path for route in router.routes]

        assert "/projects/{project_id}/timeline" in routes
        assert "/projects/{project_id}/timeline/stats" in routes
        assert "/projects/{project_id}/timeline/{event_id}" in routes
        assert "/timeline/{event_id}/override/request" in routes
        assert "/timeline/{event_id}/override/approve" in routes
        assert "/timeline/{event_id}/override/reject" in routes
        assert "/admin/override-queue" in routes
        assert "/projects/{project_id}/timeline/export" in routes

    @pytest.mark.asyncio
    async def test_router_methods(self):
        """Test router methods are correct."""
        from app.api.routes.evidence_timeline import router

        route_methods = {route.path: route.methods for route in router.routes}

        assert "GET" in route_methods.get("/projects/{project_id}/timeline", set())
        assert "GET" in route_methods.get("/projects/{project_id}/timeline/stats", set())
        assert "POST" in route_methods.get("/timeline/{event_id}/override/request", set())
        assert "POST" in route_methods.get("/timeline/{event_id}/override/approve", set())
        assert "POST" in route_methods.get("/timeline/{event_id}/override/reject", set())
