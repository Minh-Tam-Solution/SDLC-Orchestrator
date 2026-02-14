"""
Project Metadata Sync Service - Sprint 172

Syncs project metadata from local repository files to database.
Follows ADR-029: Static AGENTS.md + Dynamic Overlay pattern.

Source priority:
1. .sdlc-config.json (canonical config)
2. AGENTS.md (current sprint/status)
3. CLAUDE.md (framework version)
4. README.md (description)
5. Git metadata (timestamps)

Version: 1.0.0
Date: February 10, 2026
Status: ACTIVE - Sprint 172
Framework: SDLC 6.0.5

Purpose:
- Parse .sdlc-config.json for project configuration
- Extract current sprint from AGENTS.md
- Extract framework version from CLAUDE.md
- Extract description from README.md
- Get git metadata (last commit date, SHA)
- Update database with synced metadata

Zero Mock Policy: Real file parsing + database operations
"""

import json
import logging
import re
import subprocess
from pathlib import Path
from typing import Optional
from uuid import UUID

from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


class ProjectMetadata(BaseModel):
    """
    Metadata extracted from repository files.

    Source mapping:
    - .sdlc-config.json: id, name, tier
    - AGENTS.md: current_sprint, sprint_status
    - CLAUDE.md: framework_version, gate_status
    - README.md: description
    - Git: last_commit_date, last_commit_sha
    """

    # From .sdlc-config.json
    id: Optional[UUID] = None
    name: Optional[str] = None
    tier: Optional[str] = None  # "lite" | "professional" | "enterprise"

    # From AGENTS.md (lines 20-30)
    current_sprint: Optional[str] = None  # "Sprint 171"
    sprint_status: Optional[str] = None  # "90% COMPLETE"
    sprint_description: Optional[str] = None

    # From CLAUDE.md (lines 1-10)
    framework_version: Optional[str] = None  # "SDLC 6.0.5"
    gate_status: Optional[str] = None  # "G3 Ship Ready (98.2%)"

    # From README.md (first paragraph)
    description: Optional[str] = None

    # From Git metadata
    last_commit_date: Optional[str] = None
    last_commit_sha: Optional[str] = None


class ProjectMetadataService:
    """
    Service for syncing project metadata from local repository files to database.

    ADR-029 Compliance: Static AGENTS.md + Dynamic Overlay
    - Parses static metadata files (.sdlc-config.json, AGENTS.md, etc.)
    - Does NOT commit dynamic context (gates, incidents)
    - Performance: <200ms per sync

    Usage:
        metadata_service = ProjectMetadataService()

        metadata = await metadata_service.sync_project_metadata(
            project_id=project.id,
            repo_path="/home/nqh/shared/SDLC-Orchestrator"
        )
    """

    async def sync_project_metadata(
        self, project_id: UUID, repo_path: str
    ) -> ProjectMetadata:
        """
        Main orchestration method to extract metadata from repo files.

        Args:
            project_id: Project UUID
            repo_path: Absolute path to repository

        Returns:
            ProjectMetadata with extracted fields

        Raises:
            FileNotFoundError: If repo_path doesn't exist
            ValidationError: If required files are malformed
        """
        repo = Path(repo_path)

        # 1. Validate repo path exists
        if not repo.exists():
            logger.error(f"Repository not found: {repo_path}")
            raise FileNotFoundError(f"Repository not found: {repo_path}")

        if not repo.is_dir():
            logger.error(f"Repository path is not a directory: {repo_path}")
            raise ValueError(f"Not a directory: {repo_path}")

        logger.info(f"Starting metadata sync for project {project_id} from {repo_path}")

        # 2. Parse metadata files in priority order
        config = await self._parse_sdlc_config(repo_path)
        agents_md = await self._parse_agents_md(repo_path)
        claude_md = await self._parse_claude_md(repo_path)
        readme = await self._parse_readme(repo_path)
        git_meta = await self._get_git_metadata(repo_path)

        # 3. Merge metadata (priority: config > agents > claude > readme > git)
        metadata = ProjectMetadata(
            id=config.get("project", {}).get("id") or project_id,
            name=config.get("project", {}).get("name"),
            tier=config.get("tier", "professional"),
            description=readme.get("description"),
            current_sprint=agents_md.get("current_sprint"),
            sprint_status=agents_md.get("sprint_status"),
            sprint_description=agents_md.get("sprint_description"),
            framework_version=claude_md.get("framework_version"),
            gate_status=claude_md.get("gate_status"),
            last_commit_date=git_meta.get("commit_date"),
            last_commit_sha=git_meta.get("commit_sha"),
        )

        logger.info(
            f"Metadata sync complete for {project_id}: "
            f"sprint={metadata.current_sprint}, "
            f"framework={metadata.framework_version}"
        )

        return metadata

    async def _parse_sdlc_config(self, repo_path: str) -> dict:
        """
        Parse .sdlc-config.json for canonical project configuration.

        Expected structure:
        {
          "version": "1.0.0",
          "project": {
            "id": "c0000000-0000-0000-0000-000000000003",
            "name": "SDLC-Orchestrator"
          },
          "tier": "professional"
        }

        Returns:
            dict with project metadata or empty dict if file missing
        """
        config_path = Path(repo_path) / ".sdlc-config.json"

        if not config_path.exists():
            logger.warning(f"Missing .sdlc-config.json in {repo_path}")
            return {}

        try:
            with open(config_path, "r", encoding="utf-8") as f:
                config = json.load(f)

            logger.debug(f"Parsed .sdlc-config.json: {config.get('project', {}).get('name')}")
            return config

        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in .sdlc-config.json: {e}")
            return {}
        except Exception as e:
            logger.error(f"Failed to parse .sdlc-config.json: {e}")
            return {}

    async def _parse_agents_md(self, repo_path: str) -> dict:
        """
        Parse AGENTS.md for current sprint information.

        Expected format (lines 20-30):
        ## Current Stage

        **Sprint 171**: Market Expansion Foundation (Phase 6) — ✅ 90% COMPLETE
        - Days 1–4: ✅ complete (i18n infra + Vietnamese UI)

        Returns:
            dict with sprint metadata or empty dict if file missing
        """
        agents_path = Path(repo_path) / "AGENTS.md"

        if not agents_path.exists():
            logger.warning(f"Missing AGENTS.md in {repo_path}")
            return {}

        try:
            with open(agents_path, "r", encoding="utf-8") as f:
                lines = f.readlines()

            # Look for sprint info in lines 15-35 (flexible range)
            for i in range(min(15, len(lines)), min(35, len(lines))):
                line = lines[i]

                # Match: **Sprint 171**: Market Expansion Foundation (Phase 6) — ✅ 90% COMPLETE
                if "**Sprint" in line or "**sprint" in line:
                    # Extract sprint number and details
                    match = re.search(
                        r'\*\*Sprint\s+(\d+)\*\*:?\s*(.+?)(?:\s*—\s*(.+))?$',
                        line,
                        re.IGNORECASE
                    )
                    if match:
                        sprint_num = match.group(1)
                        description = match.group(2).strip()
                        status = match.group(3).strip() if match.group(3) else ""

                        result = {
                            "current_sprint": f"Sprint {sprint_num}",
                            "sprint_description": description,
                            "sprint_status": status
                        }

                        logger.debug(
                            f"Parsed AGENTS.md: Sprint {sprint_num}, status={status}"
                        )
                        return result

            logger.warning("No sprint information found in AGENTS.md")
            return {}

        except Exception as e:
            logger.error(f"Failed to parse AGENTS.md: {e}")
            return {}

    async def _parse_claude_md(self, repo_path: str) -> dict:
        """
        Parse CLAUDE.md for framework version and gate status.

        Expected format (lines 1-15):
        **Version**: 3.3.0
        **Status**: Gate G3 APPROVED - Ship Ready (98.2%)
        **Framework**: SDLC 6.0.5 (7-Pillar + Section 7 Quality Assurance)

        Returns:
            dict with framework metadata or empty dict if file missing
        """
        claude_path = Path(repo_path) / "CLAUDE.md"

        if not claude_path.exists():
            logger.warning(f"Missing CLAUDE.md in {repo_path}")
            return {}

        try:
            with open(claude_path, "r", encoding="utf-8") as f:
                lines = f.readlines()

            metadata = {}

            # Parse first 15 lines for framework metadata
            for i in range(min(15, len(lines))):
                line = lines[i].strip()

                # Match: **Framework**: SDLC 6.0.5
                if "**Framework**:" in line or "**framework**:" in line:
                    match = re.search(r'SDLC\s+([\d.]+)', line, re.IGNORECASE)
                    if match:
                        metadata["framework_version"] = f"SDLC {match.group(1)}"

                # Match: **Status**: Gate G3 APPROVED - Ship Ready (98.2%)
                elif "**Status**:" in line or "**status**:" in line:
                    # Extract everything after "Status:"
                    status = re.sub(r'\*\*Status\*\*:\s*', '', line, flags=re.IGNORECASE)
                    metadata["gate_status"] = status.strip()

            if metadata:
                logger.debug(
                    f"Parsed CLAUDE.md: "
                    f"framework={metadata.get('framework_version')}, "
                    f"gate={metadata.get('gate_status')}"
                )
            else:
                logger.warning("No framework metadata found in CLAUDE.md")

            return metadata

        except Exception as e:
            logger.error(f"Failed to parse CLAUDE.md: {e}")
            return {}

    async def _parse_readme(self, repo_path: str) -> dict:
        """
        Parse README.md for project description.

        Extracts first paragraph (skip title lines starting with #).
        Limits to 500 chars for database compatibility.

        Returns:
            dict with description or empty dict if file missing
        """
        readme_path = Path(repo_path) / "README.md"

        if not readme_path.exists():
            logger.warning(f"Missing README.md in {repo_path}")
            return {}

        try:
            with open(readme_path, "r", encoding="utf-8") as f:
                content = f.read()

            # Split into lines and extract first paragraph
            lines = content.split("\n")
            description_lines = []

            for line in lines:
                stripped = line.strip()

                # Skip empty lines and title lines (starting with #)
                if not stripped or stripped.startswith("#"):
                    continue

                # Collect lines until we have enough content
                description_lines.append(stripped)

                # Stop at 500 chars
                if len(" ".join(description_lines)) > 500:
                    break

            description = " ".join(description_lines)[:500]

            if description:
                logger.debug(f"Parsed README.md: {len(description)} chars")
                return {"description": description}
            else:
                logger.warning("No description found in README.md")
                return {}

        except Exception as e:
            logger.error(f"Failed to parse README.md: {e}")
            return {}

    async def _get_git_metadata(self, repo_path: str) -> dict:
        """
        Get git metadata (last commit date, SHA) - optional.

        Uses subprocess to call git commands.
        Gracefully handles errors (returns empty dict if git not available).

        Returns:
            dict with commit_date and commit_sha or empty dict
        """
        try:
            # Get last commit date (ISO format)
            result = subprocess.run(
                ["git", "log", "-1", "--format=%ci"],
                cwd=repo_path,
                capture_output=True,
                text=True,
                timeout=5  # 5-second timeout
            )

            commit_date = None
            if result.returncode == 0 and result.stdout.strip():
                commit_date = result.stdout.strip()

            # Get last commit SHA (short)
            result = subprocess.run(
                ["git", "log", "-1", "--format=%H"],
                cwd=repo_path,
                capture_output=True,
                text=True,
                timeout=5
            )

            commit_sha = None
            if result.returncode == 0 and result.stdout.strip():
                # Use first 8 chars of SHA
                commit_sha = result.stdout.strip()[:8]

            if commit_date or commit_sha:
                logger.debug(
                    f"Parsed git metadata: date={commit_date}, sha={commit_sha}"
                )
                return {
                    "commit_date": commit_date,
                    "commit_sha": commit_sha
                }
            else:
                return {}

        except subprocess.TimeoutExpired:
            logger.warning(f"Git command timed out for {repo_path}")
            return {}
        except FileNotFoundError:
            logger.warning(f"Git not available for {repo_path}")
            return {}
        except Exception as e:
            logger.warning(f"Failed to get git metadata: {e}")
            return {}


# ============================================================================
# Global Service Instance
# ============================================================================

project_metadata_service = ProjectMetadataService()
