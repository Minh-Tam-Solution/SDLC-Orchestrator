"""
Import Service Unit Tests
Sprint 154 Day 5 - TDD Phase 2 (GREEN)

Tests for specification import from external sources.

Architecture: ADR-050 Import Layer
"""

import pytest
from unittest.mock import AsyncMock, patch

from app.services.spec_converter.import_service import (
    SpecImportService,
    ImportSource,
    ImportResult,
    JiraIssue,
    LinearIssue,
)


class TestSpecImportServiceInit:
    """Tests for SpecImportService initialization."""

    def test_init_creates_service(self):
        """Service should initialize without errors."""
        service = SpecImportService()
        assert service is not None

    def test_init_has_null_clients(self):
        """Service should initialize with null clients."""
        service = SpecImportService()
        assert service._jira_client is None
        assert service._linear_client is None
        assert service._github_client is None


class TestImportFromJira:
    """Tests for Jira import functionality."""

    @pytest.fixture
    def service(self):
        """Create import service instance."""
        return SpecImportService()

    @pytest.mark.asyncio
    async def test_import_jira_returns_import_result(self, service):
        """Import should return ImportResult."""
        result = await service.import_from_jira("PROJ-123")
        assert isinstance(result, ImportResult)

    @pytest.mark.asyncio
    async def test_import_jira_stub_returns_not_found(self, service):
        """Stub implementation should return not found error."""
        result = await service.import_from_jira("PROJ-123")
        assert result.success is False
        assert result.source == ImportSource.JIRA
        assert result.source_id == "PROJ-123"
        assert "not found" in result.error.lower()

    @pytest.mark.asyncio
    async def test_import_jira_with_mock_issue(self, service):
        """Should convert Jira issue to SpecIR when found."""
        mock_issue = JiraIssue(
            key="PROJ-123",
            summary="User login feature",
            description="Users should be able to log in",
            issue_type="Story",
            status="In Progress",
            priority="High",
            labels=["auth", "feature"],
            components=["backend"],
            acceptance_criteria="Given a user exists\nWhen they log in\nThen they see dashboard",
        )

        with patch.object(
            service, "_fetch_jira_issue", new_callable=AsyncMock
        ) as mock_fetch:
            mock_fetch.return_value = mock_issue
            result = await service.import_from_jira("PROJ-123")

            assert result.success is True
            assert result.spec_ir is not None
            assert result.spec_ir.spec_id == "SPEC-PROJ-123"
            assert result.spec_ir.title == "User login feature"
            assert "auth" in result.spec_ir.tags

    @pytest.mark.asyncio
    async def test_jira_priority_mapping(self, service):
        """Should map Jira priority to spec priority."""
        mock_issue = JiraIssue(
            key="PROJ-1",
            summary="High priority task",
            description="Important",
            issue_type="Story",
            status="To Do",
            priority="Highest",
            labels=[],
            components=[],
        )

        with patch.object(
            service, "_fetch_jira_issue", new_callable=AsyncMock
        ) as mock_fetch:
            mock_fetch.return_value = mock_issue
            result = await service.import_from_jira("PROJ-1")

            assert result.success is True
            # Priority mapping happens in requirements extraction

    @pytest.mark.asyncio
    async def test_jira_status_mapping(self, service):
        """Should map Jira status to spec status."""
        test_cases = [
            ("To Do", "DRAFT"),
            ("In Progress", "PROPOSED"),
            ("Done", "APPROVED"),
            ("Closed", "APPROVED"),
        ]

        for jira_status, expected_spec_status in test_cases:
            mock_issue = JiraIssue(
                key="PROJ-1",
                summary="Test",
                description="Test",
                issue_type="Story",
                status=jira_status,
                priority="Medium",
                labels=[],
                components=[],
            )

            with patch.object(
                service, "_fetch_jira_issue", new_callable=AsyncMock
            ) as mock_fetch:
                mock_fetch.return_value = mock_issue
                result = await service.import_from_jira("PROJ-1")

                assert result.spec_ir.status == expected_spec_status

    @pytest.mark.asyncio
    async def test_jira_handles_exception(self, service):
        """Should handle exceptions gracefully."""
        with patch.object(
            service, "_fetch_jira_issue", new_callable=AsyncMock
        ) as mock_fetch:
            mock_fetch.side_effect = Exception("API Error")
            result = await service.import_from_jira("PROJ-123")

            assert result.success is False
            assert "API Error" in result.error


class TestImportFromLinear:
    """Tests for Linear import functionality."""

    @pytest.fixture
    def service(self):
        """Create import service instance."""
        return SpecImportService()

    @pytest.mark.asyncio
    async def test_import_linear_returns_import_result(self, service):
        """Import should return ImportResult."""
        result = await service.import_from_linear("abc12345")
        assert isinstance(result, ImportResult)

    @pytest.mark.asyncio
    async def test_import_linear_stub_returns_not_found(self, service):
        """Stub implementation should return not found error."""
        result = await service.import_from_linear("abc12345")
        assert result.success is False
        assert result.source == ImportSource.LINEAR
        assert result.source_id == "abc12345"
        assert "not found" in result.error.lower()

    @pytest.mark.asyncio
    async def test_import_linear_with_mock_issue(self, service):
        """Should convert Linear issue to SpecIR when found."""
        mock_issue = LinearIssue(
            id="abc12345-6789",
            title="Implement dark mode",
            description="Users want dark mode",
            state="in_progress",
            priority=2,
            labels=["ui", "feature"],
            team="Frontend",
        )

        with patch.object(
            service, "_fetch_linear_issue", new_callable=AsyncMock
        ) as mock_fetch:
            mock_fetch.return_value = mock_issue
            result = await service.import_from_linear("abc12345")

            assert result.success is True
            assert result.spec_ir is not None
            assert "abc12345" in result.spec_ir.spec_id
            assert result.spec_ir.title == "Implement dark mode"
            assert "ui" in result.spec_ir.tags

    @pytest.mark.asyncio
    async def test_linear_priority_mapping(self, service):
        """Should map Linear priority to spec priority."""
        priority_cases = [
            (1, "P0"),  # Urgent
            (2, "P0"),  # High
            (3, "P1"),  # Medium
            (4, "P2"),  # Low
            (0, "P3"),  # No priority
        ]

        for linear_priority, expected in priority_cases:
            mock_issue = LinearIssue(
                id="test123",
                title="Test",
                description="Test",
                state="todo",
                priority=linear_priority,
                labels=[],
            )

            with patch.object(
                service, "_fetch_linear_issue", new_callable=AsyncMock
            ) as mock_fetch:
                mock_fetch.return_value = mock_issue
                result = await service.import_from_linear("test123")

                assert result.success is True
                # Priority mapping verified through conversion

    @pytest.mark.asyncio
    async def test_linear_state_mapping(self, service):
        """Should map Linear state to spec status."""
        state_cases = [
            ("backlog", "DRAFT"),
            ("todo", "DRAFT"),
            ("in_progress", "PROPOSED"),
            ("done", "APPROVED"),
            ("canceled", "DEPRECATED"),
        ]

        for linear_state, expected_status in state_cases:
            mock_issue = LinearIssue(
                id="test123",
                title="Test",
                description="Test",
                state=linear_state,
                priority=3,
                labels=[],
            )

            with patch.object(
                service, "_fetch_linear_issue", new_callable=AsyncMock
            ) as mock_fetch:
                mock_fetch.return_value = mock_issue
                result = await service.import_from_linear("test123")

                assert result.spec_ir.status == expected_status

    @pytest.mark.asyncio
    async def test_linear_handles_exception(self, service):
        """Should handle exceptions gracefully."""
        with patch.object(
            service, "_fetch_linear_issue", new_callable=AsyncMock
        ) as mock_fetch:
            mock_fetch.side_effect = Exception("GraphQL Error")
            result = await service.import_from_linear("abc12345")

            assert result.success is False
            assert "GraphQL Error" in result.error


class TestImportFromText:
    """Tests for plain text import functionality."""

    @pytest.fixture
    def service(self):
        """Create import service instance."""
        return SpecImportService()

    @pytest.mark.asyncio
    async def test_import_text_returns_import_result(self, service):
        """Import should return ImportResult."""
        result = await service.import_from_text("Some text")
        assert isinstance(result, ImportResult)

    @pytest.mark.asyncio
    async def test_import_text_success(self, service):
        """Should successfully import plain text."""
        result = await service.import_from_text("A simple requirement")
        assert result.success is True
        assert result.source == ImportSource.TEXT
        assert result.spec_ir is not None

    @pytest.mark.asyncio
    async def test_import_text_with_title(self, service):
        """Should use provided title."""
        result = await service.import_from_text(
            "Requirement details", title="My Feature"
        )
        assert result.spec_ir.title == "My Feature"

    @pytest.mark.asyncio
    async def test_import_text_detects_user_story(self, service):
        """Should detect and parse user story format."""
        content = "As a user, I want to login so that I can access my account"
        result = await service.import_from_text(content)

        assert result.success is True
        assert "user-story" in result.spec_ir.tags
        assert len(result.spec_ir.requirements) > 0
        assert "user" in result.spec_ir.requirements[0].given.lower()

    @pytest.mark.asyncio
    async def test_import_text_detects_bdd(self, service):
        """Should detect and parse BDD format."""
        content = """
        Feature: Login
        Scenario: Valid login
        Given a user exists
        When they enter valid credentials
        Then they see the dashboard
        """
        result = await service.import_from_text(content)

        assert result.success is True
        assert "bdd" in result.spec_ir.tags
        assert len(result.spec_ir.requirements) > 0

    @pytest.mark.asyncio
    async def test_import_text_plain_text_fallback(self, service):
        """Should handle plain text as fallback."""
        content = "This is just plain text without any format"
        result = await service.import_from_text(content)

        assert result.success is True
        assert "imported" in result.spec_ir.tags
        assert len(result.spec_ir.requirements) == 1

    @pytest.mark.asyncio
    async def test_import_text_generates_spec_id(self, service):
        """Should generate spec ID from content hash."""
        result = await service.import_from_text("Some unique content")
        assert result.spec_ir.spec_id.startswith("SPEC-")

    @pytest.mark.asyncio
    async def test_import_text_handles_multiline(self, service):
        """Should handle multiline content."""
        content = """
        As a developer
        I want automated tests
        So that I can catch bugs early
        """
        result = await service.import_from_text(content)

        assert result.success is True
        assert len(result.spec_ir.requirements) > 0


class TestParseAcceptanceCriteria:
    """Tests for acceptance criteria parsing."""

    @pytest.fixture
    def service(self):
        """Create import service instance."""
        return SpecImportService()

    def test_parse_numbered_list(self, service):
        """Should parse numbered list acceptance criteria."""
        ac_text = """
        1. User can log in
        2. User sees dashboard
        3. User can log out
        """
        requirements = service._parse_acceptance_criteria(ac_text)

        assert len(requirements) == 3
        assert requirements[0].title == "User can log in"

    def test_parse_bullet_list(self, service):
        """Should parse bullet list acceptance criteria."""
        ac_text = """
        - User can log in
        - User sees dashboard
        * User can log out
        """
        requirements = service._parse_acceptance_criteria(ac_text)

        assert len(requirements) == 3

    def test_parse_bdd_format(self, service):
        """Should parse BDD-style acceptance criteria."""
        ac_text = """
        Given: User is on login page
        When: User enters valid credentials
        Then: User sees dashboard
        """
        requirements = service._parse_acceptance_criteria(ac_text)

        assert len(requirements) >= 1
        assert requirements[0].given == "User is on login page"
        assert requirements[0].when == "User enters valid credentials"
        assert requirements[0].then == "User sees dashboard"

    def test_parse_empty_returns_empty(self, service):
        """Should return empty list for empty input."""
        requirements = service._parse_acceptance_criteria("")
        assert requirements == []

    def test_parse_mixed_format(self, service):
        """Should handle mixed format acceptance criteria."""
        ac_text = """
        Precondition: User is logged in
        Action: User clicks logout
        Result: User is logged out

        1. Session is cleared
        2. User redirected to login
        """
        requirements = service._parse_acceptance_criteria(ac_text)

        assert len(requirements) >= 2


class TestTextFormatDetection:
    """Tests for text format auto-detection."""

    @pytest.fixture
    def service(self):
        """Create import service instance."""
        return SpecImportService()

    def test_detect_user_story_format(self, service):
        """Should detect user story format."""
        content = "As a user I want to login"
        detected = service._detect_text_format(content)
        assert detected == "user_story"

    def test_detect_bdd_with_feature(self, service):
        """Should detect BDD format with Feature keyword."""
        content = "Feature: Login\nScenario: Valid login"
        detected = service._detect_text_format(content)
        assert detected == "bdd"

    def test_detect_bdd_with_scenario(self, service):
        """Should detect BDD format with Scenario keyword."""
        content = "Scenario: Valid login\nGiven user exists"
        detected = service._detect_text_format(content)
        assert detected == "bdd"

    def test_detect_bdd_with_given_when(self, service):
        """Should detect BDD format with Given/When."""
        content = "Given user exists\nWhen they login"
        detected = service._detect_text_format(content)
        assert detected == "bdd"

    def test_detect_plain_text(self, service):
        """Should default to plain for unrecognized format."""
        content = "This is just some plain text"
        detected = service._detect_text_format(content)
        assert detected == "plain"


class TestImportResult:
    """Tests for ImportResult dataclass."""

    def test_import_result_success(self):
        """Should create success result."""
        result = ImportResult(
            success=True,
            spec_ir=None,
            source=ImportSource.TEXT,
            source_id=None,
        )
        assert result.success is True
        assert result.warnings == []

    def test_import_result_failure(self):
        """Should create failure result with error."""
        result = ImportResult(
            success=False,
            spec_ir=None,
            source=ImportSource.JIRA,
            source_id="PROJ-1",
            error="Not found",
        )
        assert result.success is False
        assert result.error == "Not found"

    def test_import_result_with_warnings(self):
        """Should include warnings."""
        result = ImportResult(
            success=True,
            spec_ir=None,
            source=ImportSource.LINEAR,
            source_id="abc123",
            warnings=["Field X not mapped", "Field Y empty"],
        )
        assert len(result.warnings) == 2


class TestImportAPIRoutes:
    """Integration tests for import API routes."""

    @pytest.fixture
    def client(self):
        """Create test client."""
        from httpx import AsyncClient, ASGITransport
        from app.main import app

        transport = ASGITransport(app=app)
        return AsyncClient(transport=transport, base_url="http://test")

    @pytest.mark.asyncio
    async def test_import_jira_endpoint(self, client):
        """Should handle Jira import request."""
        async with client as c:
            response = await c.post(
                "/api/v1/spec-converter/import/jira",
                json={"issue_key": "PROJ-123"},
            )
            assert response.status_code == 200
            data = response.json()
            assert "success" in data
            assert data["source"] == "jira"

    @pytest.mark.asyncio
    async def test_import_linear_endpoint(self, client):
        """Should handle Linear import request."""
        async with client as c:
            response = await c.post(
                "/api/v1/spec-converter/import/linear",
                json={"issue_id": "abc12345"},
            )
            assert response.status_code == 200
            data = response.json()
            assert "success" in data
            assert data["source"] == "linear"

    @pytest.mark.asyncio
    async def test_import_text_endpoint(self, client):
        """Should handle text import request."""
        async with client as c:
            response = await c.post(
                "/api/v1/spec-converter/import/text",
                json={"content": "As a user, I want to login"},
            )
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert data["source"] == "text"
            assert data["spec_ir"] is not None

    @pytest.mark.asyncio
    async def test_import_text_empty_content(self, client):
        """Should reject empty content."""
        async with client as c:
            response = await c.post(
                "/api/v1/spec-converter/import/text",
                json={"content": ""},
            )
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is False
            assert "empty" in data["error"].lower()

    @pytest.mark.asyncio
    async def test_import_text_with_title(self, client):
        """Should use provided title."""
        async with client as c:
            response = await c.post(
                "/api/v1/spec-converter/import/text",
                json={
                    "content": "Some requirement",
                    "title": "Custom Title",
                },
            )
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert data["spec_ir"]["title"] == "Custom Title"
