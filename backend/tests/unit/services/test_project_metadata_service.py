import json
from pathlib import Path
from uuid import uuid4

import pytest

from app.services.project_metadata_service import ProjectMetadataService


@pytest.mark.asyncio
async def test_parse_sdlc_config_valid(tmp_path: Path):
    repo = tmp_path
    (repo / ".sdlc-config.json").write_text(
        json.dumps(
            {
                "version": "1.0.0",
                "project": {"id": str(uuid4()), "name": "My Project"},
                "tier": "professional",
            }
        ),
        encoding="utf-8",
    )

    svc = ProjectMetadataService()
    config = await svc._parse_sdlc_config(str(repo))

    assert config["project"]["name"] == "My Project"
    assert config["tier"] == "professional"


@pytest.mark.asyncio
async def test_parse_sdlc_config_missing_returns_empty(tmp_path: Path):
    svc = ProjectMetadataService()
    config = await svc._parse_sdlc_config(str(tmp_path))
    assert config == {}


@pytest.mark.asyncio
async def test_parse_agents_md_sprint_line(tmp_path: Path):
    repo = tmp_path
    agents = ["# AGENTS\n"] + ["\n"] * 20
    agents.append("**Sprint 171**: Market Expansion Foundation (Phase 6) — ✅ 90% COMPLETE\n")
    agents.append("- Days 1–4: ✅ complete\n")
    (repo / "AGENTS.md").write_text("".join(agents), encoding="utf-8")

    svc = ProjectMetadataService()
    data = await svc._parse_agents_md(str(repo))

    assert data["current_sprint"] == "Sprint 171"
    assert data["sprint_status"]
    assert "Market Expansion" in data["sprint_description"]


@pytest.mark.asyncio
async def test_parse_agents_md_no_sprint_returns_empty(tmp_path: Path):
    (tmp_path / "AGENTS.md").write_text("# AGENTS\n\nNo sprint here\n", encoding="utf-8")
    svc = ProjectMetadataService()
    data = await svc._parse_agents_md(str(tmp_path))
    assert data == {}


@pytest.mark.asyncio
async def test_parse_claude_md_framework_and_gate_status(tmp_path: Path):
    (tmp_path / "CLAUDE.md").write_text(
        """**Version**: 3.3.0\n**Status**: Gate G3 APPROVED - Ship Ready (98.2%)\n**Framework**: SDLC 6.0.5 (7-Pillar + Section 7 Quality Assurance)\n""",
        encoding="utf-8",
    )
    svc = ProjectMetadataService()
    data = await svc._parse_claude_md(str(tmp_path))
    assert data["framework_version"] == "SDLC 6.0.5"
    assert "Gate G3" in data["gate_status"]


@pytest.mark.asyncio
async def test_parse_readme_first_paragraph(tmp_path: Path):
    (tmp_path / "README.md").write_text(
        """# Title\n\nFirst paragraph line 1.\nFirst paragraph line 2.\n\n## Section\nMore text.\n""",
        encoding="utf-8",
    )
    svc = ProjectMetadataService()
    data = await svc._parse_readme(str(tmp_path))
    assert data["description"].startswith("First paragraph")
    assert "Title" not in data["description"]


@pytest.mark.asyncio
async def test_sync_project_metadata_merges_sources(tmp_path: Path):
    project_id = uuid4()

    (tmp_path / ".sdlc-config.json").write_text(
        json.dumps({"project": {"id": str(project_id), "name": "SDLC-Orchestrator"}, "tier": "professional"}),
        encoding="utf-8",
    )
    agents = ["# AGENTS\n"] + ["\n"] * 20
    agents.append("**Sprint 171**: Market Expansion Foundation — ✅ 90% COMPLETE\n")
    (tmp_path / "AGENTS.md").write_text("".join(agents), encoding="utf-8")
    (tmp_path / "CLAUDE.md").write_text(
        """**Status**: Gate G3 APPROVED - Ship Ready (98.2%)\n**Framework**: SDLC 6.0.5\n""",
        encoding="utf-8",
    )
    (tmp_path / "README.md").write_text("# Title\n\nRepo description here.\n", encoding="utf-8")

    svc = ProjectMetadataService()
    metadata = await svc.sync_project_metadata(project_id=project_id, repo_path=str(tmp_path))

    assert metadata.id == project_id
    assert metadata.name == "SDLC-Orchestrator"
    assert metadata.tier == "professional"
    assert metadata.current_sprint == "Sprint 171"
    assert metadata.framework_version == "SDLC 6.0.5"
    assert metadata.description and "Repo description" in metadata.description
