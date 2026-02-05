"""
Test Gherkin Renderer
Sprint 154 Day 2 - TDD Phase 1 (RED)

Tests for rendering SpecIR → BDD/Gherkin format.

TDD Workflow:
1. Write these tests FIRST (RED - tests fail)
2. Implement renderer to pass tests (GREEN)
3. Refactor if needed

Architecture: ADR-050 Renderer Layer
"""

import pytest
from datetime import datetime

from app.services.spec_converter.models import (
    SpecIR,
    SpecRequirement,
    AcceptanceCriterion,
)


class TestGherkinRenderer:
    """Test Gherkin/BDD renderer."""

    @pytest.fixture
    def renderer(self):
        """Create GherkinRenderer instance."""
        from app.services.spec_converter.renderers.gherkin_renderer import GherkinRenderer
        return GherkinRenderer()

    @pytest.fixture
    def sample_ir(self) -> SpecIR:
        """Create sample SpecIR for testing."""
        return SpecIR(
            spec_id="SPEC-TEST-001",
            title="User Authentication",
            version="1.0.0",
            status="DRAFT",
            tier=["ALL"],
            owner="test@example.com",
            last_updated=datetime.utcnow().isoformat(),
            tags=["authentication", "security"],
            related_adrs=["ADR-001"],
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
                )
            ],
            acceptance_criteria=[],
        )

    @pytest.mark.asyncio
    async def test_render_feature_header(self, renderer, sample_ir):
        """Test rendering Feature: header."""
        result = await renderer.render(sample_ir)

        assert "Feature: User Authentication" in result
        # Feature should be near the start (tags may come first)
        feature_pos = result.find("Feature:")
        assert feature_pos < 100  # Feature should be in first 100 chars

    @pytest.mark.asyncio
    async def test_render_tags(self, renderer, sample_ir):
        """Test rendering tags before Feature."""
        result = await renderer.render(sample_ir)

        # Tags should appear before Feature
        assert "@authentication" in result
        assert "@security" in result
        tag_pos = result.find("@authentication")
        feature_pos = result.find("Feature:")
        assert tag_pos < feature_pos

    @pytest.mark.asyncio
    async def test_render_scenario(self, renderer, sample_ir):
        """Test rendering Scenario from requirement."""
        result = await renderer.render(sample_ir)

        assert "Scenario: User Login" in result

    @pytest.mark.asyncio
    async def test_render_given_step(self, renderer, sample_ir):
        """Test rendering Given step."""
        result = await renderer.render(sample_ir)

        assert "Given a registered user with valid credentials" in result

    @pytest.mark.asyncio
    async def test_render_when_step(self, renderer, sample_ir):
        """Test rendering When step."""
        result = await renderer.render(sample_ir)

        assert "When the user submits the login form" in result

    @pytest.mark.asyncio
    async def test_render_then_step(self, renderer, sample_ir):
        """Test rendering Then step."""
        result = await renderer.render(sample_ir)

        assert "Then the user is authenticated and redirected to dashboard" in result

    @pytest.mark.asyncio
    async def test_render_step_order(self, renderer, sample_ir):
        """Test that steps appear in correct order: Given → When → Then."""
        result = await renderer.render(sample_ir)

        given_pos = result.find("Given ")
        when_pos = result.find("When ")
        then_pos = result.find("Then ")

        assert given_pos < when_pos < then_pos

    @pytest.mark.asyncio
    async def test_render_multiple_scenarios(self, renderer):
        """Test rendering multiple scenarios from multiple requirements."""
        ir = SpecIR(
            spec_id="SPEC-MULTI",
            title="Multi-Scenario Feature",
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
                    title="First Scenario",
                    priority="P0",
                    tier=["ALL"],
                    given="condition one",
                    when="action one",
                    then="result one",
                ),
                SpecRequirement(
                    id="REQ-002",
                    title="Second Scenario",
                    priority="P1",
                    tier=["ALL"],
                    given="condition two",
                    when="action two",
                    then="result two",
                ),
            ],
            acceptance_criteria=[],
        )

        result = await renderer.render(ir)

        assert "Scenario: First Scenario" in result
        assert "Scenario: Second Scenario" in result
        # First should come before second
        assert result.find("First Scenario") < result.find("Second Scenario")

    @pytest.mark.asyncio
    async def test_render_and_steps(self, renderer):
        """Test rendering And steps for multiple conditions."""
        ir = SpecIR(
            spec_id="SPEC-AND",
            title="Feature with And Steps",
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
                    title="Multi-condition Scenario",
                    priority="P0",
                    tier=["ALL"],
                    given="condition one; condition two",
                    when="action performed",
                    then="result one; result two",
                ),
            ],
            acceptance_criteria=[],
        )

        result = await renderer.render(ir)

        # Should have And steps
        assert "Given condition one" in result
        assert "And condition two" in result
        assert "Then result one" in result
        assert "And result two" in result

    @pytest.mark.asyncio
    async def test_render_indentation(self, renderer, sample_ir):
        """Test proper Gherkin indentation."""
        result = await renderer.render(sample_ir)
        lines = result.split("\n")

        for line in lines:
            if line.strip().startswith("Scenario:"):
                # Scenario should be indented with 2 spaces
                assert line.startswith("  Scenario:")
            elif line.strip().startswith(("Given", "When", "Then", "And")):
                # Steps should be indented with 4 spaces
                assert line.startswith("    ")

    @pytest.mark.asyncio
    async def test_render_empty_requirements(self, renderer):
        """Test rendering IR with no requirements."""
        ir = SpecIR(
            spec_id="SPEC-EMPTY",
            title="Empty Feature",
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

        # Should still have feature header
        assert "Feature: Empty Feature" in result
        # Should not have any scenarios
        assert "Scenario:" not in result

    @pytest.mark.asyncio
    async def test_render_description(self, renderer, sample_ir):
        """Test rendering feature description."""
        result = await renderer.render(sample_ir)

        # Feature description should include spec metadata
        assert "SPEC-TEST-001" in result or "Version:" in result or "Status:" in result

    @pytest.mark.asyncio
    async def test_render_priority_tag(self, renderer, sample_ir):
        """Test rendering priority as scenario tag."""
        result = await renderer.render(sample_ir)

        # Priority should appear as tag before scenario
        # @P0 should appear somewhere before the scenario
        assert "@P0" in result or "@priority-P0" in result

    @pytest.mark.asyncio
    async def test_render_special_characters(self, renderer):
        """Test handling special characters in steps."""
        ir = SpecIR(
            spec_id="SPEC-SPECIAL",
            title="Feature with Special Characters",
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
                    title="Special Chars Scenario",
                    priority="P1",
                    tier=["ALL"],
                    given='user enters "test@email.com"',
                    when="user clicks <Submit>",
                    then="message shows 'Success!'",
                ),
            ],
            acceptance_criteria=[],
        )

        result = await renderer.render(ir)

        # Special characters should be preserved
        assert '"test@email.com"' in result
        assert "<Submit>" in result
        assert "'Success!'" in result
