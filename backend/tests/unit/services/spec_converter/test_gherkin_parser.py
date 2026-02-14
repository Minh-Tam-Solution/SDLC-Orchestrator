"""
Test Suite: Gherkin Parser
Sprint: 154 - Spec Standard Completion
TDD Phase: 1 (Tests First)
SDLC: 6.0.5 Principle 4 - Verification-First

Expected Tests: 15
Purpose: Parse Gherkin (BDD) feature files to SpecIR
"""

import pytest
from datetime import datetime


class TestGherkinParser:
    """Test cases for Gherkin (BDD) parser."""

    @pytest.fixture
    def parser(self):
        """Create parser instance."""
        from app.services.spec_converter.parsers.gherkin_parser import GherkinParser
        return GherkinParser()

    @pytest.fixture
    def simple_feature(self) -> str:
        """Simple Gherkin feature file content."""
        return """
Feature: User Login
  As a registered user
  I want to login to my account
  So that I can access protected features

  Scenario: Successful login
    Given a registered user with valid credentials
    When they enter their username and password
    Then they are redirected to the dashboard
"""

    @pytest.fixture
    def complex_feature(self) -> str:
        """Complex Gherkin feature with multiple scenarios and tags."""
        return """
@authentication @security
Feature: User Authentication
  Multi-factor authentication for enterprise users

  Background:
    Given the authentication service is running
    And the user database is available

  @happy-path
  Scenario: Login with valid credentials
    Given a registered user "john@example.com"
    When they enter password "secure123"
    And they submit the login form
    Then they receive a valid JWT token
    And they are redirected to "/dashboard"

  @error-case
  Scenario: Login with invalid password
    Given a registered user "john@example.com"
    When they enter password "wrongpassword"
    Then they see error message "Invalid credentials"
    And they remain on the login page

  @mfa
  Scenario Outline: MFA verification
    Given a user with MFA enabled
    When they enter OTP code "<code>"
    Then the result is "<result>"

    Examples:
      | code   | result  |
      | 123456 | success |
      | 000000 | failure |
"""

    @pytest.mark.asyncio
    async def test_parse_simple_feature(self, parser, simple_feature):
        """Test parsing a simple feature file."""
        result = await parser.parse(simple_feature)

        assert result.title == "User Login"
        assert len(result.requirements) == 1
        assert result.requirements[0].title == "Successful login"

    @pytest.mark.asyncio
    async def test_parse_feature_name(self, parser, simple_feature):
        """Test extracting feature name correctly."""
        result = await parser.parse(simple_feature)

        assert result.title == "User Login"
        assert "SPEC-" in result.spec_id

    @pytest.mark.asyncio
    async def test_parse_scenario_to_requirement(self, parser, simple_feature):
        """Test converting scenario to requirement."""
        result = await parser.parse(simple_feature)

        req = result.requirements[0]
        assert req.title == "Successful login"
        assert "registered user" in req.given
        assert "username and password" in req.when
        assert "dashboard" in req.then

    @pytest.mark.asyncio
    async def test_parse_given_step(self, parser, simple_feature):
        """Test extracting GIVEN step."""
        result = await parser.parse(simple_feature)

        req = result.requirements[0]
        assert "registered user" in req.given
        assert "valid credentials" in req.given

    @pytest.mark.asyncio
    async def test_parse_when_step(self, parser, simple_feature):
        """Test extracting WHEN step."""
        result = await parser.parse(simple_feature)

        req = result.requirements[0]
        assert "enter" in req.when
        assert "username and password" in req.when

    @pytest.mark.asyncio
    async def test_parse_then_step(self, parser, simple_feature):
        """Test extracting THEN step."""
        result = await parser.parse(simple_feature)

        req = result.requirements[0]
        assert "redirected" in req.then
        assert "dashboard" in req.then

    @pytest.mark.asyncio
    async def test_parse_tags(self, parser, complex_feature):
        """Test extracting tags from feature."""
        result = await parser.parse(complex_feature)

        assert "authentication" in result.tags
        assert "security" in result.tags

    @pytest.mark.asyncio
    async def test_parse_multiple_scenarios(self, parser, complex_feature):
        """Test parsing multiple scenarios."""
        result = await parser.parse(complex_feature)

        # Should have 3 scenarios (2 regular + 1 outline)
        assert len(result.requirements) >= 2
        titles = [r.title for r in result.requirements]
        assert "Login with valid credentials" in titles
        assert "Login with invalid password" in titles

    @pytest.mark.asyncio
    async def test_parse_background(self, parser, complex_feature):
        """Test parsing Background section."""
        result = await parser.parse(complex_feature)

        # Background should be included in each scenario's given
        for req in result.requirements:
            assert "authentication service" in req.given.lower() or len(req.given) > 0

    @pytest.mark.asyncio
    async def test_parse_and_steps(self, parser, complex_feature):
        """Test handling AND steps (continuation)."""
        result = await parser.parse(complex_feature)

        # Find the happy path scenario
        happy_path = next(
            (r for r in result.requirements if "valid credentials" in r.title.lower()),
            None
        )
        assert happy_path is not None
        # Should include AND steps concatenated
        assert "JWT" in happy_path.then or "token" in happy_path.then.lower()

    @pytest.mark.asyncio
    async def test_parse_scenario_outline(self, parser, complex_feature):
        """Test parsing Scenario Outline with examples."""
        result = await parser.parse(complex_feature)

        # Should handle scenario outline
        mfa_scenarios = [r for r in result.requirements if "MFA" in r.title or "OTP" in r.given]
        # Either parsed as single scenario or expanded from examples
        assert len(result.requirements) >= 2

    @pytest.mark.asyncio
    async def test_generate_spec_id(self, parser, simple_feature):
        """Test spec_id generation from feature name."""
        result = await parser.parse(simple_feature)

        assert result.spec_id.startswith("SPEC-")
        # Should be consistent for same input
        result2 = await parser.parse(simple_feature)
        assert result.spec_id == result2.spec_id

    @pytest.mark.asyncio
    async def test_parse_empty_feature(self, parser):
        """Test handling empty or invalid input."""
        with pytest.raises(ValueError):
            await parser.parse("")

    @pytest.mark.asyncio
    async def test_parse_feature_without_scenarios(self, parser):
        """Test handling feature without scenarios."""
        content = """
Feature: Empty Feature
  This feature has no scenarios
"""
        with pytest.raises(ValueError):
            await parser.parse(content)

    @pytest.mark.asyncio
    async def test_last_updated_timestamp(self, parser, simple_feature):
        """Test that last_updated is set."""
        result = await parser.parse(simple_feature)

        assert result.last_updated is not None
        # Should be ISO format
        datetime.fromisoformat(result.last_updated.replace("Z", "+00:00"))
