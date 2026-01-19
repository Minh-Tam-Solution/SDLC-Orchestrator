"""
=========================================================================
Integration Tests - AGENTS.md API
SDLC Orchestrator - Sprint 80 (AGENTS.md Integration)

Version: 1.0.0
Date: January 19, 2026
Status: ACTIVE - Sprint 80 Implementation
Authority: QA Lead + Backend Lead Approved
Reference: TDS-080-001 AGENTS.md Technical Design

Purpose:
- Test AGENTS.md API endpoints
- Test context overlay API endpoints
- Test validation endpoints
- Test end-to-end flow

Coverage Target: 90%+
=========================================================================
"""

import pytest
from httpx import AsyncClient
from uuid import uuid4


class TestAgentsMdGenerate:
    """Test AGENTS.md generation endpoint."""

    @pytest.mark.asyncio
    async def test_generate_basic(self, client: AsyncClient, auth_headers: dict, test_project_id: str):
        """Test basic AGENTS.md generation."""
        response = await client.post(
            "/api/v1/agents-md/generate",
            json={
                "project_id": test_project_id,
            },
            headers=auth_headers,
        )

        assert response.status_code == 201
        data = response.json()
        assert "content" in data
        assert "content_hash" in data
        assert data["line_count"] > 0
        assert "AGENTS.md" in data["content"]

    @pytest.mark.asyncio
    async def test_generate_with_config(self, client: AsyncClient, auth_headers: dict, test_project_id: str):
        """Test AGENTS.md generation with custom config."""
        response = await client.post(
            "/api/v1/agents-md/generate",
            json={
                "project_id": test_project_id,
                "include_quick_start": True,
                "include_architecture": True,
                "include_conventions": True,
                "include_security": True,
                "include_do_not": True,
                "max_lines": 100,
            },
            headers=auth_headers,
        )

        assert response.status_code == 201
        data = response.json()
        assert data["line_count"] <= 100
        assert "Quick Start" in data["sections"] or len(data["sections"]) > 0

    @pytest.mark.asyncio
    async def test_generate_with_custom_content(self, client: AsyncClient, auth_headers: dict, test_project_id: str):
        """Test AGENTS.md generation with custom content."""
        response = await client.post(
            "/api/v1/agents-md/generate",
            json={
                "project_id": test_project_id,
                "custom_quick_start": "Run `make start` to begin",
                "custom_do_not": ["Add TODOs", "Skip tests"],
            },
            headers=auth_headers,
        )

        assert response.status_code == 201
        data = response.json()
        assert "make start" in data["content"]
        assert "Add TODOs" in data["content"]

    @pytest.mark.asyncio
    async def test_generate_project_not_found(self, client: AsyncClient, auth_headers: dict):
        """Test generation with non-existent project."""
        response = await client.post(
            "/api/v1/agents-md/generate",
            json={
                "project_id": str(uuid4()),
            },
            headers=auth_headers,
        )

        assert response.status_code == 404


class TestAgentsMdGet:
    """Test get latest AGENTS.md endpoint."""

    @pytest.mark.asyncio
    async def test_get_latest(self, client: AsyncClient, auth_headers: dict, test_project_id: str):
        """Test getting latest AGENTS.md."""
        # First generate one
        await client.post(
            "/api/v1/agents-md/generate",
            json={"project_id": test_project_id},
            headers=auth_headers,
        )

        # Then get it
        response = await client.get(
            f"/api/v1/agents-md/{test_project_id}",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert "content" in data
        assert "id" in data

    @pytest.mark.asyncio
    async def test_get_not_found(self, client: AsyncClient, auth_headers: dict):
        """Test getting AGENTS.md for project without one."""
        new_project_id = str(uuid4())

        response = await client.get(
            f"/api/v1/agents-md/{new_project_id}",
            headers=auth_headers,
        )

        assert response.status_code == 404
        assert "Generate one first" in response.json()["detail"]


class TestAgentsMdValidate:
    """Test AGENTS.md validation endpoint."""

    @pytest.mark.asyncio
    async def test_validate_clean_content(self, client: AsyncClient, auth_headers: dict):
        """Test validation of clean content."""
        content = """# AGENTS.md - Test

## Quick Start
- `docker compose up`

## DO NOT
- Add mocks
"""
        response = await client.post(
            "/api/v1/agents-md/validate",
            json={"content": content},
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["valid"] is True
        assert len(data["errors"]) == 0

    @pytest.mark.asyncio
    async def test_validate_with_secret(self, client: AsyncClient, auth_headers: dict):
        """Test validation catches secrets."""
        content = """# AGENTS.md
API Key: sk-abc123def456ghi789jkl012mno345pqr678stu901
"""
        response = await client.post(
            "/api/v1/agents-md/validate",
            json={"content": content},
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["valid"] is False
        assert len(data["errors"]) > 0

    @pytest.mark.asyncio
    async def test_validate_over_limit(self, client: AsyncClient, auth_headers: dict):
        """Test validation warns on line limit."""
        content = "\n".join([f"Line {i}" for i in range(180)])

        response = await client.post(
            "/api/v1/agents-md/validate",
            json={"content": content},
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["over_limit"] is True
        assert data["line_count"] == 180


class TestAgentsMdLint:
    """Test AGENTS.md lint endpoint."""

    @pytest.mark.asyncio
    async def test_lint_fixes_whitespace(self, client: AsyncClient, auth_headers: dict):
        """Test lint fixes trailing whitespace."""
        content = "# AGENTS.md   \n\nContent  \n"

        response = await client.post(
            "/api/v1/agents-md/lint",
            json={"content": content},
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert "  " not in data["fixed_content"].split("\n")[0]
        assert len(data["changes"]) > 0

    @pytest.mark.asyncio
    async def test_lint_clean_content(self, client: AsyncClient, auth_headers: dict):
        """Test lint with clean content."""
        content = """# AGENTS.md

## Quick Start
- Run tests
"""
        response = await client.post(
            "/api/v1/agents-md/lint",
            json={"content": content},
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["valid"] is True


class TestAgentsMdHistory:
    """Test AGENTS.md history endpoint."""

    @pytest.mark.asyncio
    async def test_get_history(self, client: AsyncClient, auth_headers: dict, test_project_id: str):
        """Test getting generation history."""
        # Generate a few versions
        for _ in range(3):
            await client.post(
                "/api/v1/agents-md/generate",
                json={"project_id": test_project_id},
                headers=auth_headers,
            )

        response = await client.get(
            f"/api/v1/agents-md/{test_project_id}/history",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 3

    @pytest.mark.asyncio
    async def test_get_history_with_limit(self, client: AsyncClient, auth_headers: dict, test_project_id: str):
        """Test history with limit parameter."""
        response = await client.get(
            f"/api/v1/agents-md/{test_project_id}/history?limit=2",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data) <= 2


class TestContextOverlay:
    """Test context overlay endpoints."""

    @pytest.mark.asyncio
    async def test_get_context_all_formats(self, client: AsyncClient, auth_headers: dict, test_project_id: str):
        """Test getting context overlay with all formats."""
        response = await client.get(
            f"/api/v1/agents-md/context/{test_project_id}?format=all",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert "formatted" in data
        assert "pr_comment" in data["formatted"]
        assert "cli" in data["formatted"]
        assert "vscode" in data["formatted"]

    @pytest.mark.asyncio
    async def test_get_context_pr_format(self, client: AsyncClient, auth_headers: dict, test_project_id: str):
        """Test getting context overlay in PR comment format."""
        response = await client.get(
            f"/api/v1/agents-md/context/{test_project_id}?format=pr_comment",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert "pr_comment" in data["formatted"]
        assert "SDLC-CONTEXT-START" in data["formatted"]["pr_comment"]

    @pytest.mark.asyncio
    async def test_get_context_cli_format(self, client: AsyncClient, auth_headers: dict, test_project_id: str):
        """Test getting context overlay in CLI format."""
        response = await client.get(
            f"/api/v1/agents-md/context/{test_project_id}?format=cli",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert "cli" in data["formatted"]
        assert "SDLC CONTEXT" in data["formatted"]["cli"]

    @pytest.mark.asyncio
    async def test_get_context_with_trigger(self, client: AsyncClient, auth_headers: dict, test_project_id: str):
        """Test context overlay with trigger tracking."""
        response = await client.get(
            f"/api/v1/agents-md/context/{test_project_id}?trigger_type=pr_webhook&trigger_ref=PR%23123",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert "id" in data  # Should be saved to DB

    @pytest.mark.asyncio
    async def test_get_context_history(self, client: AsyncClient, auth_headers: dict, test_project_id: str):
        """Test getting context overlay history."""
        # Generate a few overlays
        for _ in range(3):
            await client.get(
                f"/api/v1/agents-md/context/{test_project_id}",
                headers=auth_headers,
            )

        response = await client.get(
            f"/api/v1/agents-md/context/{test_project_id}/history",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 3


class TestContextOverlayContent:
    """Test context overlay content."""

    @pytest.mark.asyncio
    async def test_overlay_contains_stage(self, client: AsyncClient, auth_headers: dict, test_project_id: str):
        """Test overlay contains stage information."""
        response = await client.get(
            f"/api/v1/agents-md/context/{test_project_id}",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert "stage_name" in data

    @pytest.mark.asyncio
    async def test_overlay_contains_constraints(self, client: AsyncClient, auth_headers: dict, test_project_id: str):
        """Test overlay contains constraints."""
        response = await client.get(
            f"/api/v1/agents-md/context/{test_project_id}",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert "constraints" in data
        assert isinstance(data["constraints"], list)

    @pytest.mark.asyncio
    async def test_overlay_strict_mode_flag(self, client: AsyncClient, auth_headers: dict, test_project_id: str):
        """Test overlay contains strict mode flag."""
        response = await client.get(
            f"/api/v1/agents-md/context/{test_project_id}",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert "strict_mode" in data
        assert isinstance(data["strict_mode"], bool)
