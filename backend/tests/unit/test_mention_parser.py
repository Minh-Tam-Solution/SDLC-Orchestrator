"""
=========================================================================
Unit Tests - Mention Parser (Sprint 177)
SDLC Orchestrator - Multi-Agent Team Engine

Version: 1.0.0
Date: February 2026
Status: ACTIVE - Sprint 177
Authority: CTO Approved (ADR-056)

Purpose:
- Test @mention extraction from message content
- Test role-based vs name-based mention classification
- Test deduplication and edge cases
- Test DB-backed mention resolution (mocked AsyncSession)

Zero Mock Policy: Real regex parsing, mocked DB for resolution
=========================================================================
"""

import pytest
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

from app.services.agent_team.mention_parser import (
    MentionParser,
    ParsedMention,
    MentionRouteResult,
)
from app.schemas.agent_team import SDLCRole


# =========================================================================
# Extract Mentions (Pure Logic — No DB)
# =========================================================================


class TestExtractMentions:
    """Tests for MentionParser.extract_mentions (static method)."""

    def test_single_mention(self):
        mentions = MentionParser.extract_mentions("Hey @coder please review this")
        assert len(mentions) == 1
        assert mentions[0].name == "coder"
        assert mentions[0].raw == "@coder"

    def test_multiple_mentions(self):
        mentions = MentionParser.extract_mentions("@coder @reviewer please collaborate")
        assert len(mentions) == 2
        names = {m.name for m in mentions}
        assert names == {"coder", "reviewer"}

    def test_role_mention_flagged(self):
        """Mentions matching SDLCRole values should be flagged as role mentions."""
        mentions = MentionParser.extract_mentions("@coder fix this")
        assert len(mentions) == 1
        assert mentions[0].is_role_mention is True

    def test_name_mention_not_role(self):
        """Mentions not matching SDLCRole should be name-based."""
        mentions = MentionParser.extract_mentions("@coder-alpha fix this")
        assert len(mentions) == 1
        assert mentions[0].name == "coder-alpha"
        assert mentions[0].is_role_mention is False

    def test_deduplicates(self):
        """Duplicate @mentions should produce only one entry."""
        mentions = MentionParser.extract_mentions("@coder please @coder help")
        assert len(mentions) == 1
        assert mentions[0].name == "coder"

    def test_ignores_email(self):
        """Email-like patterns should not be treated as mentions."""
        mentions = MentionParser.extract_mentions("Contact user@example.com for help")
        assert len(mentions) == 0

    def test_empty_string(self):
        mentions = MentionParser.extract_mentions("")
        assert len(mentions) == 0

    def test_no_mentions(self):
        mentions = MentionParser.extract_mentions("Just a regular message")
        assert len(mentions) == 0

    def test_mention_at_start(self):
        mentions = MentionParser.extract_mentions("@reviewer look at this")
        assert len(mentions) == 1
        assert mentions[0].name == "reviewer"

    def test_mention_at_end(self):
        mentions = MentionParser.extract_mentions("Please help @tester")
        assert len(mentions) == 1
        assert mentions[0].name == "tester"

    def test_case_insensitive(self):
        """Mentions should be lowercased."""
        mentions = MentionParser.extract_mentions("@CODER please help")
        assert len(mentions) == 1
        assert mentions[0].name == "coder"

    def test_hyphenated_name(self):
        mentions = MentionParser.extract_mentions("@coder-alpha-v2 deploy this")
        assert len(mentions) == 1
        assert mentions[0].name == "coder-alpha-v2"

    def test_underscore_name(self):
        mentions = MentionParser.extract_mentions("@test_agent run")
        assert len(mentions) == 1
        assert mentions[0].name == "test_agent"

    def test_all_sdlc_roles_are_role_mentions(self):
        """All 12 SDLCRole values should be detected as role mentions."""
        for role in SDLCRole:
            content = f"@{role.value} please help"
            mentions = MentionParser.extract_mentions(content)
            assert len(mentions) == 1, f"Failed for @{role.value}"
            assert mentions[0].is_role_mention is True, (
                f"@{role.value} should be a role mention"
            )


# =========================================================================
# Resolve Mentions (DB-backed)
# =========================================================================


class TestResolveMentions:
    """Tests for DB-backed mention resolution."""

    @pytest.fixture
    def mock_db(self):
        """Create a mock AsyncSession."""
        db = AsyncMock()
        return db

    @pytest.fixture
    def parser(self, mock_db):
        return MentionParser(mock_db)

    @pytest.fixture
    def mock_agent(self):
        """Create a mock agent definition."""
        agent = MagicMock()
        agent.id = uuid4()
        agent.agent_name = "coder-alpha"
        agent.sdlc_role = "coder"
        agent.is_active = True
        agent.project_id = uuid4()
        return agent

    @pytest.mark.asyncio
    async def test_resolve_role_mention(self, parser, mock_db, mock_agent):
        """Role mention resolves to all agents with that role."""
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [mock_agent]
        mock_db.execute.return_value = mock_result

        project_id = mock_agent.project_id
        mentions = [ParsedMention(raw="@coder", name="coder", is_role_mention=True)]

        result = await parser.resolve_mentions(project_id, mentions)
        assert len(result.resolved_agents) == 1
        assert result.resolved_agents[0].id == mock_agent.id

    @pytest.mark.asyncio
    async def test_resolve_name_mention(self, parser, mock_db, mock_agent):
        """Name mention resolves to specific agent."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_agent
        mock_db.execute.return_value = mock_result

        project_id = mock_agent.project_id
        mentions = [ParsedMention(raw="@coder-alpha", name="coder-alpha", is_role_mention=False)]

        result = await parser.resolve_mentions(project_id, mentions)
        assert len(result.resolved_agents) == 1

    @pytest.mark.asyncio
    async def test_unresolved_mention(self, parser, mock_db):
        """Unknown mention goes to unresolved list."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        project_id = uuid4()
        mentions = [ParsedMention(raw="@unknown", name="unknown", is_role_mention=False)]

        result = await parser.resolve_mentions(project_id, mentions)
        assert len(result.resolved_agents) == 0
        assert "unknown" in result.unresolved

    @pytest.mark.asyncio
    async def test_parse_and_route_no_mentions(self, parser):
        """Empty content returns empty result."""
        result = await parser.parse_and_route(uuid4(), "No mentions here")
        assert result.has_mentions is False
        assert len(result.resolved_agents) == 0

    @pytest.mark.asyncio
    async def test_mention_route_result_properties(self):
        """Test MentionRouteResult computed properties."""
        result = MentionRouteResult(
            mentions=[
                ParsedMention(raw="@coder", name="coder", is_role_mention=True),
                ParsedMention(raw="@reviewer", name="reviewer", is_role_mention=True),
            ]
        )
        assert result.has_mentions is True
        assert result.mention_names == ["coder", "reviewer"]
