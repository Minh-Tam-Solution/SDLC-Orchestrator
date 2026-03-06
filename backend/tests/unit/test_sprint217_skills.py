"""
Sprint 217 — P2a Skills Engine Tests.

Covers:
- S1: SkillDefinition model (constraints, to_dict, tier/visibility checks)
- S2: SkillLoader (5-tier hierarchy, deduplication, tier filtering, visibility)
- S3: SkillSummaryBuilder (XML output, overflow, empty, detail)
- S4: SkillFrontmatterParser (frontmatter parsing, edge cases)
- S5: ContextInjector skills integration (build_skills_md, inject_context)
- S6: Model registration (in __init__.py and __all__)

Test count: 38 tests across 6 groups.
"""

import pytest
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

# Models
from app.models.skill_definition import (
    SkillDefinition,
    SKILL_TIERS,
    SKILL_TIER_PRIORITY,
    SKILL_VISIBILITIES,
)

# Services
from app.services.agent_team.skill_loader import SkillLoader, SkillFrontmatterParser
from app.services.agent_team.skill_summary import SkillSummaryBuilder


# ─── Helpers ──────────────────────────────────────────────────────────────────

def _make_skill(
    slug: str = "test-skill",
    name: str = "Test Skill",
    tier: str = "global",
    visibility: str = "public",
    description: str | None = None,
    content: str | None = None,
    project_id=None,
    agent_definition_id=None,
    is_active: bool = True,
) -> SkillDefinition:
    """Create a SkillDefinition instance for testing."""
    skill = SkillDefinition()
    skill.id = uuid4()
    skill.slug = slug
    skill.name = name
    skill.tier = tier
    skill.visibility = visibility
    skill.description = description
    skill.content = content
    skill.project_id = project_id
    skill.agent_definition_id = agent_definition_id
    skill.is_active = is_active
    skill.version = 1
    skill.workspace_path = None
    skill.metadata_ = {}
    skill.created_at = datetime.utcnow()
    skill.updated_at = datetime.utcnow()
    return skill


# ═══════════════════════════════════════════════════════════════════════════════
# S1: SkillDefinition Model Tests
# ═══════════════════════════════════════════════════════════════════════════════


class TestSkillDefinitionModel:
    """Tests for SkillDefinition SQLAlchemy model."""

    def test_tablename(self):
        assert SkillDefinition.__tablename__ == "skill_definitions"

    def test_tier_constants(self):
        assert SKILL_TIERS == ("workspace", "project_agent", "personal_agent", "global", "builtin")
        assert len(SKILL_TIER_PRIORITY) == 5
        # workspace has highest priority (lowest index)
        assert SKILL_TIER_PRIORITY["workspace"] == 0
        assert SKILL_TIER_PRIORITY["builtin"] == 4

    def test_visibility_constants(self):
        assert SKILL_VISIBILITIES == ("public", "private", "internal")

    def test_to_dict(self):
        skill = _make_skill(
            slug="code-review",
            name="Code Review",
            tier="workspace",
            visibility="public",
            description="Review checklist",
        )
        d = skill.to_dict()
        assert d["slug"] == "code-review"
        assert d["name"] == "Code Review"
        assert d["tier"] == "workspace"
        assert d["visibility"] == "public"
        assert d["description"] == "Review checklist"
        assert d["id"] is not None
        assert d["is_active"] is True
        assert d["version"] == 1

    def test_to_dict_nullable_fields(self):
        skill = _make_skill()
        skill.project_id = None
        skill.agent_definition_id = None
        d = skill.to_dict()
        assert d["project_id"] is None
        assert d["agent_definition_id"] is None

    def test_repr(self):
        skill = _make_skill(slug="my-skill", tier="global", visibility="public")
        r = repr(skill)
        assert "my-skill" in r
        assert "global" in r

    def test_check_constraint_tier(self):
        """Verify tier constraint name exists in table args."""
        constraints = SkillDefinition.__table_args__
        tier_ck = [c for c in constraints if hasattr(c, "name") and c.name == "ck_skill_definitions_tier"]
        assert len(tier_ck) == 1

    def test_check_constraint_visibility(self):
        """Verify visibility constraint name exists in table args."""
        constraints = SkillDefinition.__table_args__
        vis_ck = [c for c in constraints if hasattr(c, "name") and c.name == "ck_skill_definitions_visibility"]
        assert len(vis_ck) == 1

    def test_composite_unique_slug_tier_project(self):
        """F2 fix: slug is unique per (slug, tier, project_id), not globally."""
        constraints = SkillDefinition.__table_args__
        uq = [c for c in constraints if hasattr(c, "name") and c.name == "uq_skill_slug_tier_project"]
        assert len(uq) == 1

    def test_slug_not_globally_unique(self):
        """F2 fix: slug column itself has no unique=True."""
        slug_col = SkillDefinition.__table__.columns["slug"]
        assert slug_col.unique is not True


# ═══════════════════════════════════════════════════════════════════════════════
# S2: SkillLoader Tests (5-Tier Hierarchy)
# ═══════════════════════════════════════════════════════════════════════════════


class TestSkillLoader:
    """Tests for SkillLoader 5-tier hierarchy and deduplication."""

    @pytest.fixture
    def mock_db(self):
        return AsyncMock()

    @pytest.fixture
    def loader(self, mock_db):
        return SkillLoader(mock_db)

    def test_deduplicate_workspace_overrides_global(self, loader):
        """Workspace tier skill overrides global tier for same slug."""
        global_skill = _make_skill(slug="review", tier="global", name="Global Review")
        workspace_skill = _make_skill(slug="review", tier="workspace", name="Workspace Review")
        result = loader._deduplicate_by_tier([global_skill, workspace_skill])
        assert len(result) == 1
        assert result[0].name == "Workspace Review"

    def test_deduplicate_project_agent_overrides_global(self, loader):
        """project_agent tier overrides global for same slug."""
        global_skill = _make_skill(slug="lint", tier="global")
        project_skill = _make_skill(slug="lint", tier="project_agent", name="Project Lint")
        result = loader._deduplicate_by_tier([global_skill, project_skill])
        assert len(result) == 1
        assert result[0].name == "Project Lint"

    def test_deduplicate_personal_overrides_global(self, loader):
        """personal_agent tier overrides global for same slug."""
        global_skill = _make_skill(slug="fmt", tier="global")
        personal_skill = _make_skill(slug="fmt", tier="personal_agent", name="My Fmt")
        result = loader._deduplicate_by_tier([global_skill, personal_skill])
        assert len(result) == 1
        assert result[0].name == "My Fmt"

    def test_deduplicate_builtin_lowest_priority(self, loader):
        """Builtin is the lowest priority — any other tier overrides it."""
        builtin_skill = _make_skill(slug="help", tier="builtin", name="Builtin Help")
        global_skill = _make_skill(slug="help", tier="global", name="Global Help")
        result = loader._deduplicate_by_tier([builtin_skill, global_skill])
        assert len(result) == 1
        assert result[0].name == "Global Help"

    def test_deduplicate_different_slugs_kept(self, loader):
        """Different slugs are all kept regardless of tier."""
        skills = [
            _make_skill(slug="a", tier="global"),
            _make_skill(slug="b", tier="workspace"),
            _make_skill(slug="c", tier="builtin"),
        ]
        result = loader._deduplicate_by_tier(skills)
        assert len(result) == 3

    def test_deduplicate_sorted_by_priority_then_name(self, loader):
        """Result is sorted by tier priority (highest first), then name."""
        skills = [
            _make_skill(slug="z-builtin", tier="builtin", name="Z Builtin"),
            _make_skill(slug="a-workspace", tier="workspace", name="A Workspace"),
            _make_skill(slug="m-global", tier="global", name="M Global"),
        ]
        result = loader._deduplicate_by_tier(skills)
        assert result[0].name == "A Workspace"    # workspace = priority 0
        assert result[1].name == "M Global"        # global = priority 3
        assert result[2].name == "Z Builtin"       # builtin = priority 4

    def test_deduplicate_empty_list(self, loader):
        result = loader._deduplicate_by_tier([])
        assert result == []

    @pytest.mark.asyncio
    async def test_load_by_tier_invalid(self, loader):
        """Invalid tier raises ValueError."""
        with pytest.raises(ValueError, match="Invalid tier"):
            await loader.load_by_tier("nonexistent")

    @pytest.mark.asyncio
    async def test_load_by_slug_returns_none_for_missing(self, mock_db):
        """load_by_slug returns None when skill doesn't exist."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        loader = SkillLoader(mock_db)
        result = await loader.load_by_slug("nonexistent")
        assert result is None

    @pytest.mark.asyncio
    async def test_load_by_slug_returns_skill(self, mock_db):
        """load_by_slug returns the skill when found."""
        skill = _make_skill(slug="found-skill")
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = skill
        mock_db.execute.return_value = mock_result

        loader = SkillLoader(mock_db)
        result = await loader.load_by_slug("found-skill")
        assert result is not None
        assert result.slug == "found-skill"


# ═══════════════════════════════════════════════════════════════════════════════
# S3: SkillSummaryBuilder Tests
# ═══════════════════════════════════════════════════════════════════════════════


class TestSkillSummaryBuilder:
    """Tests for SkillSummaryBuilder XML generation."""

    @pytest.fixture
    def mock_db(self):
        return AsyncMock()

    @pytest.mark.asyncio
    async def test_build_summary_with_skills(self, mock_db):
        """Summary includes skill names, slugs, and tiers."""
        skills = [
            _make_skill(slug="review", name="Code Review", tier="workspace",
                       description="Standard code review process"),
            _make_skill(slug="test", name="Unit Testing", tier="global",
                       description="Test writing guide"),
        ]

        with patch.object(SkillLoader, "load_accessible", return_value=skills):
            builder = SkillSummaryBuilder(mock_db)
            result = await builder.build_summary(uuid4())

        assert "<available_skills>" in result
        assert "</available_skills>" in result
        assert "Code Review" in result
        assert "`review`" in result
        assert "Unit Testing" in result
        assert "`test`" in result

    @pytest.mark.asyncio
    async def test_build_summary_empty(self, mock_db):
        """Empty string when no skills accessible."""
        with patch.object(SkillLoader, "load_accessible", return_value=[]):
            builder = SkillSummaryBuilder(mock_db)
            result = await builder.build_summary(uuid4())

        assert result == ""

    @pytest.mark.asyncio
    async def test_build_summary_overflow(self, mock_db):
        """Overflow notice when >20 skills."""
        skills = [
            _make_skill(slug=f"skill-{i}", name=f"Skill {i}", tier="global")
            for i in range(25)
        ]

        with patch.object(SkillLoader, "load_accessible", return_value=skills):
            builder = SkillSummaryBuilder(mock_db)
            result = await builder.build_summary(uuid4())

        assert "5 more skills available" in result

    @pytest.mark.asyncio
    async def test_build_summary_xml_escaping(self, mock_db):
        """User content in skill names is XML-escaped."""
        skills = [
            _make_skill(slug="xss", name="<script>alert(1)</script>", tier="global"),
        ]

        with patch.object(SkillLoader, "load_accessible", return_value=skills):
            builder = SkillSummaryBuilder(mock_db)
            result = await builder.build_summary(uuid4())

        assert "<script>" not in result
        assert "&lt;script&gt;" in result

    @pytest.mark.asyncio
    async def test_build_skill_detail_found(self, mock_db):
        """Detail view returns full skill content."""
        skill = _make_skill(
            slug="review",
            name="Code Review",
            description="Review guide",
            content="Step 1: Check formatting\nStep 2: Check logic",
        )

        with patch.object(SkillLoader, "load_by_slug", return_value=skill):
            builder = SkillSummaryBuilder(mock_db)
            result = await builder.build_skill_detail("review")

        assert "<skill_content>" in result
        assert "Code Review" in result
        assert "Step 1" in result
        # F3 fix: content is wrapped in code fence
        assert "```" in result

    @pytest.mark.asyncio
    async def test_build_skill_detail_not_found(self, mock_db):
        """Detail view returns empty string when skill not found."""
        with patch.object(SkillLoader, "load_by_slug", return_value=None):
            builder = SkillSummaryBuilder(mock_db)
            result = await builder.build_skill_detail("nonexistent")

        assert result == ""


# ═══════════════════════════════════════════════════════════════════════════════
# S4: SkillFrontmatterParser Tests
# ═══════════════════════════════════════════════════════════════════════════════


class TestSkillFrontmatterParser:
    """Tests for SKILL.md frontmatter parsing."""

    def test_parse_standard_frontmatter(self):
        raw = """---
name: Code Review
description: Standard code review checklist
tier: workspace
tags: review, quality, code
---
## Instructions
Review the code carefully."""
        meta, body = SkillFrontmatterParser.parse(raw)
        assert meta["name"] == "Code Review"
        assert meta["description"] == "Standard code review checklist"
        assert meta["tier"] == "workspace"
        assert meta["tags"] == ["review", "quality", "code"]
        assert "## Instructions" in body

    def test_parse_no_frontmatter(self):
        raw = "Just plain content without frontmatter."
        meta, body = SkillFrontmatterParser.parse(raw)
        assert meta == {}
        assert body == raw

    def test_parse_unclosed_frontmatter(self):
        raw = "---\nname: Broken\nNo closing delimiter"
        meta, body = SkillFrontmatterParser.parse(raw)
        assert meta == {}
        assert body == raw

    def test_parse_empty_frontmatter(self):
        raw = """---
---
Body content here."""
        meta, body = SkillFrontmatterParser.parse(raw)
        assert meta == {}
        assert body == "Body content here."

    def test_parse_single_value(self):
        raw = """---
tier: global
---
Content."""
        meta, body = SkillFrontmatterParser.parse(raw)
        assert meta["tier"] == "global"
        assert body == "Content."

    def test_parse_ignores_comments(self):
        raw = """---
# This is a comment
name: Test
---
Body."""
        meta, body = SkillFrontmatterParser.parse(raw)
        assert "name" in meta
        assert meta["name"] == "Test"


# ═══════════════════════════════════════════════════════════════════════════════
# S5: ContextInjector Skills Integration Tests
# ═══════════════════════════════════════════════════════════════════════════════


class TestContextInjectorSkills:
    """Tests for ContextInjector integration with SkillSummaryBuilder."""

    @pytest.fixture
    def mock_db(self):
        return AsyncMock()

    @pytest.mark.asyncio
    async def test_build_skills_md_delegates_to_builder(self, mock_db):
        """build_skills_md calls SkillSummaryBuilder.build_summary."""
        from app.services.agent_team.context_injector import ContextInjector

        with patch.object(
            SkillSummaryBuilder, "build_summary", return_value="<available_skills>test</available_skills>"
        ) as mock_build:
            injector = ContextInjector(mock_db)
            result = await injector.build_skills_md(uuid4(), uuid4())

        mock_build.assert_called_once()
        assert "<available_skills>" in result

    @pytest.mark.asyncio
    async def test_inject_context_includes_skills(self, mock_db):
        """inject_context includes skills section when skills exist."""
        from app.services.agent_team.context_injector import ContextInjector

        agent_id = uuid4()
        project_id = uuid4()

        with patch.object(ContextInjector, "build_delegation_md", return_value=""), \
             patch.object(ContextInjector, "build_team_md", return_value=""), \
             patch.object(ContextInjector, "build_availability_md", return_value=""), \
             patch.object(
                 ContextInjector, "build_skills_md",
                 return_value="<available_skills>\n## Skills\n</available_skills>"
             ):
            injector = ContextInjector(mock_db)
            result = await injector.inject_context(
                agent_id, None, "Base prompt.", project_id=project_id
            )

        assert "Base prompt." in result
        assert "<system_context>" in result
        assert "<available_skills>" in result

    @pytest.mark.asyncio
    async def test_inject_context_no_skills(self, mock_db):
        """inject_context omits skills section when none accessible."""
        from app.services.agent_team.context_injector import ContextInjector

        with patch.object(ContextInjector, "build_delegation_md", return_value=""), \
             patch.object(ContextInjector, "build_team_md", return_value=""), \
             patch.object(ContextInjector, "build_availability_md", return_value=""), \
             patch.object(ContextInjector, "build_skills_md", return_value=""):
            injector = ContextInjector(mock_db)
            result = await injector.inject_context(uuid4(), None, "Base prompt.")

        # No context block when all sections empty
        assert result == "Base prompt."
        assert "<system_context>" not in result

    @pytest.mark.asyncio
    async def test_inject_context_project_id_passed_to_skills(self, mock_db):
        """project_id parameter is forwarded to build_skills_md."""
        from app.services.agent_team.context_injector import ContextInjector

        agent_id = uuid4()
        project_id = uuid4()

        with patch.object(ContextInjector, "build_delegation_md", return_value=""), \
             patch.object(ContextInjector, "build_team_md", return_value=""), \
             patch.object(ContextInjector, "build_availability_md", return_value=""), \
             patch.object(ContextInjector, "build_skills_md", return_value="") as mock_skills:
            injector = ContextInjector(mock_db)
            await injector.inject_context(
                agent_id, None, "prompt", project_id=project_id
            )

        mock_skills.assert_called_once_with(agent_id, project_id)


# ═══════════════════════════════════════════════════════════════════════════════
# S6: Model Registration Tests
# ═══════════════════════════════════════════════════════════════════════════════


class TestModelRegistration:
    """Tests for SkillDefinition registration in models/__init__.py."""

    def test_skill_definition_in_init(self):
        """SkillDefinition is importable from app.models."""
        from app.models import SkillDefinition as SD
        assert SD is SkillDefinition

    def test_skill_definition_in_all(self):
        """SkillDefinition is listed in __all__."""
        import app.models as models_pkg
        assert "SkillDefinition" in models_pkg.__all__
