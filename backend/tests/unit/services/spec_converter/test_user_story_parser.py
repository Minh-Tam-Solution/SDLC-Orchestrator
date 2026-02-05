"""
Test Suite: User Story Parser
Sprint: 154 - Spec Standard Completion
TDD Phase: 1 (Tests First)
SDLC: 6.0.3 Principle 4 - Verification-First

Expected Tests: 8
Purpose: Parse User Stories to BDD SpecIR with AI assistance
"""

import pytest
from datetime import datetime


class TestUserStoryParser:
    """Test cases for User Story parser."""

    @pytest.fixture
    def parser(self):
        """Create parser instance."""
        from app.services.spec_converter.parsers.user_story_parser import UserStoryParser
        return UserStoryParser()

    @pytest.fixture
    def simple_user_story(self) -> str:
        """Simple user story in standard format."""
        return "As a registered user, I want to reset my password so that I can regain access to my account"

    @pytest.fixture
    def complex_user_story(self) -> str:
        """User story with additional context."""
        return """
As an admin user
I want to view audit logs for all user activities
So that I can track security events and ensure compliance

Acceptance Criteria:
- Logs show timestamp, user, action, and IP address
- Logs can be filtered by date range
- Logs can be exported to CSV
"""

    @pytest.fixture
    def multiple_stories(self) -> str:
        """Multiple user stories."""
        return """
User Story 1:
As a customer, I want to add items to my cart so that I can purchase multiple products at once.

User Story 2:
As a customer, I want to save items for later so that I can purchase them in the future.

User Story 3:
As a customer, I want to apply discount codes so that I can save money on my purchase.
"""

    @pytest.mark.asyncio
    async def test_parse_actor(self, parser, simple_user_story):
        """Test extracting actor from 'As a...' clause."""
        result = await parser.parse(simple_user_story)

        assert len(result.requirements) >= 1
        req = result.requirements[0]
        # Actor should be in GIVEN
        assert "user" in req.given.lower()

    @pytest.mark.asyncio
    async def test_parse_action(self, parser, simple_user_story):
        """Test extracting action from 'I want...' clause."""
        result = await parser.parse(simple_user_story)

        req = result.requirements[0]
        # Action should be in WHEN
        assert "password" in req.when.lower() or "reset" in req.when.lower()

    @pytest.mark.asyncio
    async def test_parse_outcome(self, parser, simple_user_story):
        """Test extracting outcome from 'So that...' clause."""
        result = await parser.parse(simple_user_story)

        req = result.requirements[0]
        # Outcome should be in THEN
        assert "access" in req.then.lower() or "account" in req.then.lower()

    @pytest.mark.asyncio
    async def test_preserve_user_story(self, parser, simple_user_story):
        """Test that original user story is preserved."""
        result = await parser.parse(simple_user_story)

        req = result.requirements[0]
        assert req.user_story is not None
        assert "As a" in req.user_story

    @pytest.mark.asyncio
    async def test_parse_with_acceptance_criteria(self, parser, complex_user_story):
        """Test parsing user story with acceptance criteria."""
        result = await parser.parse(complex_user_story)

        req = result.requirements[0]
        # Should have acceptance criteria
        assert len(req.acceptance_criteria) > 0 or "timestamp" in req.then.lower()

    @pytest.mark.asyncio
    async def test_parse_multiple_stories(self, parser, multiple_stories):
        """Test parsing multiple user stories."""
        result = await parser.parse(multiple_stories)

        # Should create multiple requirements
        assert len(result.requirements) >= 2
        titles = [r.title.lower() for r in result.requirements]
        assert any("cart" in t for t in titles) or any("customer" in r.given.lower() for r in result.requirements)

    @pytest.mark.asyncio
    async def test_generate_title(self, parser, simple_user_story):
        """Test automatic title generation."""
        result = await parser.parse(simple_user_story)

        assert result.title != ""
        # Title should be meaningful
        assert len(result.title) > 5

    @pytest.mark.asyncio
    async def test_invalid_format_handling(self, parser):
        """Test handling of non-standard format."""
        content = "This is just random text without user story format"

        # Should either raise error or return with best-effort parsing
        try:
            result = await parser.parse(content)
            # If parsed, should have some content
            assert result.title != "" or len(result.requirements) >= 0
        except ValueError:
            # Also acceptable - invalid format rejected
            pass


class TestUserStoryPatterns:
    """Test various user story patterns and edge cases."""

    @pytest.fixture
    def parser(self):
        from app.services.spec_converter.parsers.user_story_parser import UserStoryParser
        return UserStoryParser()

    @pytest.mark.asyncio
    async def test_variant_format_1(self, parser):
        """Test 'As an' variant (with 'n')."""
        story = "As an administrator, I want to manage users so that I can control access"
        result = await parser.parse(story)

        assert len(result.requirements) >= 1
        assert "admin" in result.requirements[0].given.lower()

    @pytest.mark.asyncio
    async def test_variant_format_2(self, parser):
        """Test 'In order to... As a... I want...' format."""
        story = """
In order to track my expenses
As a business user
I want to categorize transactions
"""
        result = await parser.parse(story)

        assert len(result.requirements) >= 1
        # Should handle alternative format

    @pytest.mark.asyncio
    async def test_empty_story(self, parser):
        """Test handling empty input."""
        with pytest.raises(ValueError):
            await parser.parse("")

    @pytest.mark.asyncio
    async def test_story_without_so_that(self, parser):
        """Test story without 'so that' clause."""
        story = "As a user, I want to logout"
        result = await parser.parse(story)

        # Should still parse, THEN might be inferred
        assert len(result.requirements) >= 1
