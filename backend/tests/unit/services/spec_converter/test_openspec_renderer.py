"""
Test OpenSpec Renderer
Sprint 154 Day 2 - TDD Phase 1 (RED)

Tests for rendering SpecIR → OpenSpec YAML format.

TDD Workflow:
1. Write these tests FIRST (RED - tests fail)
2. Implement renderer to pass tests (GREEN)
3. Refactor if needed

OpenSpec Format (SDLC 6.0.3 Section 8):
---
spec_id: SPEC-XXX
title: ...
version: ...
---

# Requirements
...

Architecture: ADR-050 Renderer Layer
"""

import pytest
from datetime import datetime
import yaml

from app.services.spec_converter.models import (
    SpecIR,
    SpecRequirement,
    AcceptanceCriterion,
)


class TestOpenSpecRenderer:
    """Test OpenSpec YAML renderer."""

    @pytest.fixture
    def renderer(self):
        """Create OpenSpecRenderer instance."""
        from app.services.spec_converter.renderers.openspec_renderer import OpenSpecRenderer
        return OpenSpecRenderer()

    @pytest.fixture
    def sample_ir(self) -> SpecIR:
        """Create sample SpecIR for testing."""
        return SpecIR(
            spec_id="SPEC-TEST-001",
            title="User Authentication Specification",
            version="1.0.0",
            status="DRAFT",
            tier=["PRO", "ENTERPRISE"],
            owner="test@example.com",
            last_updated="2026-02-04T10:00:00",
            tags=["authentication", "security"],
            related_adrs=["ADR-001", "ADR-005"],
            related_specs=["SPEC-002"],
            requirements=[
                SpecRequirement(
                    id="REQ-001",
                    title="User Login",
                    priority="P0",
                    tier=["ALL"],
                    given="a registered user with valid credentials",
                    when="the user submits the login form",
                    then="the user is authenticated and redirected to dashboard",
                    user_story="As a user, I want to login so that I can access my account",
                )
            ],
            acceptance_criteria=[
                AcceptanceCriterion(
                    id="AC-001",
                    scenario="Valid Login",
                    given="valid username and password",
                    when="user clicks login",
                    then="user sees dashboard",
                    tier=["ALL"],
                    testable=True,
                )
            ],
        )

    @pytest.mark.asyncio
    async def test_render_yaml_frontmatter(self, renderer, sample_ir):
        """Test rendering YAML frontmatter."""
        result = await renderer.render(sample_ir)

        # Should start with YAML frontmatter
        assert result.startswith("---\n")
        # Should have closing frontmatter delimiter
        assert "\n---\n" in result

    @pytest.mark.asyncio
    async def test_render_spec_id(self, renderer, sample_ir):
        """Test rendering spec_id in frontmatter."""
        result = await renderer.render(sample_ir)

        # Extract frontmatter
        frontmatter = self._extract_frontmatter(result)
        assert frontmatter["spec_id"] == "SPEC-TEST-001"

    @pytest.mark.asyncio
    async def test_render_title(self, renderer, sample_ir):
        """Test rendering title in frontmatter."""
        result = await renderer.render(sample_ir)

        frontmatter = self._extract_frontmatter(result)
        assert frontmatter["title"] == "User Authentication Specification"

    @pytest.mark.asyncio
    async def test_render_version(self, renderer, sample_ir):
        """Test rendering version in frontmatter."""
        result = await renderer.render(sample_ir)

        frontmatter = self._extract_frontmatter(result)
        assert frontmatter["version"] == "1.0.0"

    @pytest.mark.asyncio
    async def test_render_status(self, renderer, sample_ir):
        """Test rendering status in frontmatter."""
        result = await renderer.render(sample_ir)

        frontmatter = self._extract_frontmatter(result)
        assert frontmatter["status"] == "DRAFT"

    @pytest.mark.asyncio
    async def test_render_tier_list(self, renderer, sample_ir):
        """Test rendering tier as list in frontmatter."""
        result = await renderer.render(sample_ir)

        frontmatter = self._extract_frontmatter(result)
        assert frontmatter["tier"] == ["PRO", "ENTERPRISE"]

    @pytest.mark.asyncio
    async def test_render_owner(self, renderer, sample_ir):
        """Test rendering owner in frontmatter."""
        result = await renderer.render(sample_ir)

        frontmatter = self._extract_frontmatter(result)
        assert frontmatter["owner"] == "test@example.com"

    @pytest.mark.asyncio
    async def test_render_tags(self, renderer, sample_ir):
        """Test rendering tags in frontmatter."""
        result = await renderer.render(sample_ir)

        frontmatter = self._extract_frontmatter(result)
        assert "authentication" in frontmatter["tags"]
        assert "security" in frontmatter["tags"]

    @pytest.mark.asyncio
    async def test_render_related_adrs(self, renderer, sample_ir):
        """Test rendering related_adrs in frontmatter."""
        result = await renderer.render(sample_ir)

        frontmatter = self._extract_frontmatter(result)
        assert "ADR-001" in frontmatter["related_adrs"]
        assert "ADR-005" in frontmatter["related_adrs"]

    @pytest.mark.asyncio
    async def test_render_related_specs(self, renderer, sample_ir):
        """Test rendering related_specs in frontmatter."""
        result = await renderer.render(sample_ir)

        frontmatter = self._extract_frontmatter(result)
        assert "SPEC-002" in frontmatter["related_specs"]

    @pytest.mark.asyncio
    async def test_render_requirements_section(self, renderer, sample_ir):
        """Test rendering Requirements section header."""
        result = await renderer.render(sample_ir)

        # Should have Requirements section
        assert "# Requirements" in result or "## Requirements" in result

    @pytest.mark.asyncio
    async def test_render_requirement_bdd_format(self, renderer, sample_ir):
        """Test rendering requirement in BDD format."""
        result = await renderer.render(sample_ir)
        body = self._extract_body(result)

        # Should have GIVEN/WHEN/THEN keywords
        assert "**GIVEN**" in body or "GIVEN" in body
        assert "**WHEN**" in body or "WHEN" in body
        assert "**THEN**" in body or "THEN" in body

    @pytest.mark.asyncio
    async def test_render_requirement_id(self, renderer, sample_ir):
        """Test rendering requirement ID."""
        result = await renderer.render(sample_ir)
        body = self._extract_body(result)

        assert "REQ-001" in body

    @pytest.mark.asyncio
    async def test_render_requirement_priority(self, renderer, sample_ir):
        """Test rendering requirement priority."""
        result = await renderer.render(sample_ir)
        body = self._extract_body(result)

        assert "P0" in body

    @pytest.mark.asyncio
    async def test_render_acceptance_criteria_section(self, renderer, sample_ir):
        """Test rendering Acceptance Criteria section."""
        result = await renderer.render(sample_ir)

        assert "Acceptance Criteria" in result or "## Acceptance" in result

    @pytest.mark.asyncio
    async def test_render_acceptance_criteria_table(self, renderer, sample_ir):
        """Test rendering acceptance criteria as markdown table."""
        result = await renderer.render(sample_ir)

        # Should have table headers
        assert "| ID |" in result or "|ID|" in result or "AC-001" in result

    @pytest.mark.asyncio
    async def test_render_user_story(self, renderer, sample_ir):
        """Test rendering user story if present."""
        result = await renderer.render(sample_ir)
        body = self._extract_body(result)

        # User story should be included
        assert "As a user" in body or "user_story" in body.lower()

    @pytest.mark.asyncio
    async def test_render_empty_requirements(self, renderer):
        """Test rendering IR with no requirements."""
        ir = SpecIR(
            spec_id="SPEC-EMPTY",
            title="Empty Spec",
            version="1.0.0",
            status="DRAFT",
            tier=["ALL"],
            owner="test@example.com",
            last_updated=datetime.utcnow().isoformat(),
            tags=[],
            related_adrs=[],
            related_specs=[],
            requirements=[],
            acceptance_criteria=[],
        )

        result = await renderer.render(ir)

        # Should still have valid frontmatter
        assert result.startswith("---\n")
        frontmatter = self._extract_frontmatter(result)
        assert frontmatter["spec_id"] == "SPEC-EMPTY"

    @pytest.mark.asyncio
    async def test_render_multiple_requirements(self, renderer):
        """Test rendering multiple requirements."""
        ir = SpecIR(
            spec_id="SPEC-MULTI",
            title="Multi-Requirement Spec",
            version="1.0.0",
            status="DRAFT",
            tier=["ALL"],
            owner="test@example.com",
            last_updated=datetime.utcnow().isoformat(),
            tags=[],
            related_adrs=[],
            related_specs=[],
            requirements=[
                SpecRequirement(
                    id="REQ-001",
                    title="First Requirement",
                    priority="P0",
                    tier=["ALL"],
                    given="first condition",
                    when="first action",
                    then="first result",
                ),
                SpecRequirement(
                    id="REQ-002",
                    title="Second Requirement",
                    priority="P1",
                    tier=["PRO"],
                    given="second condition",
                    when="second action",
                    then="second result",
                ),
            ],
            acceptance_criteria=[],
        )

        result = await renderer.render(ir)
        body = self._extract_body(result)

        assert "REQ-001" in body
        assert "REQ-002" in body
        assert "First Requirement" in body
        assert "Second Requirement" in body

    @pytest.mark.asyncio
    async def test_render_preserves_formatting(self, renderer, sample_ir):
        """Test that rendered output can be parsed back."""
        result = await renderer.render(sample_ir)

        # Should be valid YAML frontmatter
        frontmatter = self._extract_frontmatter(result)
        assert frontmatter is not None

        # Re-parsing should not fail
        from app.services.spec_converter.parsers.openspec_parser import OpenSpecParser
        parser = OpenSpecParser()
        re_parsed = await parser.parse(result)

        # Key fields should match
        assert re_parsed.spec_id == sample_ir.spec_id
        assert re_parsed.title == sample_ir.title

    @pytest.mark.asyncio
    async def test_render_requirement_tier(self, renderer):
        """Test rendering tier-specific requirements."""
        ir = SpecIR(
            spec_id="SPEC-TIER",
            title="Tier-Specific Spec",
            version="1.0.0",
            status="DRAFT",
            tier=["ALL"],
            owner="test@example.com",
            last_updated=datetime.utcnow().isoformat(),
            tags=[],
            related_adrs=[],
            related_specs=[],
            requirements=[
                SpecRequirement(
                    id="REQ-001",
                    title="Enterprise Only",
                    priority="P0",
                    tier=["ENTERPRISE"],
                    given="enterprise account",
                    when="advanced feature used",
                    then="feature works",
                ),
            ],
            acceptance_criteria=[],
        )

        result = await renderer.render(ir)
        body = self._extract_body(result)

        # Tier should be indicated
        assert "ENTERPRISE" in body

    def _extract_frontmatter(self, content: str) -> dict:
        """Extract and parse YAML frontmatter from content."""
        if not content.startswith("---\n"):
            return {}

        end_marker = content.find("\n---\n", 4)
        if end_marker == -1:
            return {}

        frontmatter_text = content[4:end_marker]
        return yaml.safe_load(frontmatter_text)

    def _extract_body(self, content: str) -> str:
        """Extract body content after frontmatter."""
        if not content.startswith("---\n"):
            return content

        end_marker = content.find("\n---\n", 4)
        if end_marker == -1:
            return content

        return content[end_marker + 5:]
