"""
Test Spec Converter API Routes
Sprint 154 Day 3 - TDD Phase 1 (RED)

Tests for /api/v1/spec-converter endpoints.

TDD Workflow:
1. Write these tests FIRST (RED - tests fail)
2. Implement routes to pass tests (GREEN)
3. Refactor if needed

Endpoints:
- POST /parse - Parse content to IR
- POST /render - Render IR to format
- POST /convert - Convert between formats
- POST /detect - Detect format of content

Architecture: ADR-050 API Layer
"""

import pytest
from httpx import AsyncClient


class TestSpecConverterParseEndpoint:
    """Test POST /api/v1/spec-converter/parse endpoint."""

    @pytest.mark.asyncio
    async def test_parse_bdd_content(self, api_client: AsyncClient):
        """Test parsing BDD/Gherkin content to IR."""
        response = await api_client.post(
            "/api/v1/spec-converter/parse",
            json={
                "content": """Feature: User Login
  Scenario: Valid credentials
    Given a registered user
    When they enter valid credentials
    Then they see the dashboard""",
                "source_format": "BDD",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert "spec_id" in data
        assert "title" in data
        assert data["title"] == "User Login"
        assert "requirements" in data
        assert len(data["requirements"]) >= 1

    @pytest.mark.asyncio
    async def test_parse_openspec_content(self, api_client: AsyncClient):
        """Test parsing OpenSpec YAML content to IR."""
        response = await api_client.post(
            "/api/v1/spec-converter/parse",
            json={
                "content": """---
spec_id: SPEC-001
title: Test Specification
version: 1.0.0
status: DRAFT
tier: [ALL]
owner: test@example.com
---

# Requirements

## REQ-001: Test Requirement [P0] [ALL]

**GIVEN** a precondition
**WHEN** an action occurs
**THEN** expected result
""",
                "source_format": "OPENSPEC",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["spec_id"] == "SPEC-001"
        assert data["title"] == "Test Specification"

    @pytest.mark.asyncio
    async def test_parse_user_story_content(self, api_client: AsyncClient):
        """Test parsing User Story content to IR."""
        response = await api_client.post(
            "/api/v1/spec-converter/parse",
            json={
                "content": "As a user, I want to login so that I can access my account",
                "source_format": "USER_STORY",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert "requirements" in data
        # User story should be converted to BDD
        assert len(data["requirements"]) >= 1

    @pytest.mark.asyncio
    async def test_parse_invalid_format(self, api_client: AsyncClient):
        """Test parsing with invalid format returns 400."""
        response = await api_client.post(
            "/api/v1/spec-converter/parse",
            json={
                "content": "Some content",
                "source_format": "INVALID_FORMAT",
            },
        )

        assert response.status_code == 400
        assert "error" in response.json() or "detail" in response.json()

    @pytest.mark.asyncio
    async def test_parse_empty_content(self, api_client: AsyncClient):
        """Test parsing empty content returns 400."""
        response = await api_client.post(
            "/api/v1/spec-converter/parse",
            json={
                "content": "",
                "source_format": "BDD",
            },
        )

        assert response.status_code == 400


class TestSpecConverterRenderEndpoint:
    """Test POST /api/v1/spec-converter/render endpoint."""

    @pytest.mark.asyncio
    async def test_render_to_bdd(self, api_client: AsyncClient):
        """Test rendering IR to BDD/Gherkin format."""
        ir_data = {
            "spec_id": "SPEC-001",
            "title": "Test Feature",
            "version": "1.0.0",
            "status": "DRAFT",
            "tier": ["ALL"],
            "owner": "test@example.com",
            "last_updated": "2026-02-04T10:00:00",
            "tags": ["test"],
            "related_adrs": [],
            "related_specs": [],
            "requirements": [
                {
                    "id": "REQ-001",
                    "title": "Test Scenario",
                    "priority": "P0",
                    "tier": ["ALL"],
                    "given": "a precondition",
                    "when": "an action",
                    "then": "a result",
                }
            ],
            "acceptance_criteria": [],
        }

        response = await api_client.post(
            "/api/v1/spec-converter/render",
            json={
                "ir": ir_data,
                "target_format": "BDD",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert "content" in data
        assert "Feature:" in data["content"]
        assert "Scenario:" in data["content"]

    @pytest.mark.asyncio
    async def test_render_to_openspec(self, api_client: AsyncClient):
        """Test rendering IR to OpenSpec YAML format."""
        ir_data = {
            "spec_id": "SPEC-001",
            "title": "Test Specification",
            "version": "1.0.0",
            "status": "DRAFT",
            "tier": ["ALL"],
            "owner": "test@example.com",
            "last_updated": "2026-02-04T10:00:00",
            "tags": [],
            "related_adrs": [],
            "related_specs": [],
            "requirements": [],
            "acceptance_criteria": [],
        }

        response = await api_client.post(
            "/api/v1/spec-converter/render",
            json={
                "ir": ir_data,
                "target_format": "OPENSPEC",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert "content" in data
        assert "---" in data["content"]  # YAML frontmatter
        assert "spec_id:" in data["content"]

    @pytest.mark.asyncio
    async def test_render_invalid_format(self, api_client: AsyncClient):
        """Test rendering to invalid format returns 400."""
        response = await api_client.post(
            "/api/v1/spec-converter/render",
            json={
                "ir": {"spec_id": "SPEC-001", "title": "Test"},
                "target_format": "INVALID",
            },
        )

        assert response.status_code == 400


class TestSpecConverterConvertEndpoint:
    """Test POST /api/v1/spec-converter/convert endpoint."""

    @pytest.mark.asyncio
    async def test_convert_bdd_to_openspec(self, api_client: AsyncClient):
        """Test converting BDD to OpenSpec."""
        response = await api_client.post(
            "/api/v1/spec-converter/convert",
            json={
                "content": """Feature: User Login
  Scenario: Valid credentials
    Given a registered user
    When they enter valid credentials
    Then they see the dashboard""",
                "source_format": "BDD",
                "target_format": "OPENSPEC",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert "content" in data
        assert "---" in data["content"]  # OpenSpec has YAML frontmatter

    @pytest.mark.asyncio
    async def test_convert_user_story_to_bdd(self, api_client: AsyncClient):
        """Test converting User Story to BDD."""
        response = await api_client.post(
            "/api/v1/spec-converter/convert",
            json={
                "content": "As a user, I want to login so that I can access my account",
                "source_format": "USER_STORY",
                "target_format": "BDD",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert "content" in data
        assert "Feature:" in data["content"]


class TestSpecConverterDetectEndpoint:
    """Test POST /api/v1/spec-converter/detect endpoint."""

    @pytest.mark.asyncio
    async def test_detect_bdd_format(self, api_client: AsyncClient):
        """Test detecting BDD/Gherkin format."""
        response = await api_client.post(
            "/api/v1/spec-converter/detect",
            json={
                "content": """Feature: User Login
  Scenario: Valid login
    Given a user
    When login
    Then success"""
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["format"] == "BDD"

    @pytest.mark.asyncio
    async def test_detect_openspec_format(self, api_client: AsyncClient):
        """Test detecting OpenSpec YAML format."""
        response = await api_client.post(
            "/api/v1/spec-converter/detect",
            json={
                "content": """---
spec_id: SPEC-001
title: Test
---
Content here"""
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["format"] == "OPENSPEC"

    @pytest.mark.asyncio
    async def test_detect_user_story_format(self, api_client: AsyncClient):
        """Test detecting User Story format."""
        response = await api_client.post(
            "/api/v1/spec-converter/detect",
            json={
                "content": "As a user, I want to do something so that I get benefit"
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["format"] == "USER_STORY"

    @pytest.mark.asyncio
    async def test_detect_unknown_format(self, api_client: AsyncClient):
        """Test detecting unknown format returns null."""
        response = await api_client.post(
            "/api/v1/spec-converter/detect",
            json={"content": "Random text with no specific format"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["format"] is None or data["format"] == "UNKNOWN"


class TestSpecConverterValidation:
    """Test request validation for spec converter endpoints."""

    @pytest.mark.asyncio
    async def test_parse_missing_content(self, api_client: AsyncClient):
        """Test parse with missing content field."""
        response = await api_client.post(
            "/api/v1/spec-converter/parse",
            json={"source_format": "BDD"},
        )

        assert response.status_code == 422  # Validation error

    @pytest.mark.asyncio
    async def test_parse_missing_format(self, api_client: AsyncClient):
        """Test parse with missing source_format field."""
        response = await api_client.post(
            "/api/v1/spec-converter/parse",
            json={"content": "Some content"},
        )

        assert response.status_code == 422  # Validation error

    @pytest.mark.asyncio
    async def test_render_missing_ir(self, api_client: AsyncClient):
        """Test render with missing ir field."""
        response = await api_client.post(
            "/api/v1/spec-converter/render",
            json={"target_format": "BDD"},
        )

        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_convert_missing_fields(self, api_client: AsyncClient):
        """Test convert with missing required fields."""
        response = await api_client.post(
            "/api/v1/spec-converter/convert",
            json={"content": "Some content"},
        )

        assert response.status_code == 422
