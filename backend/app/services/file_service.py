"""
File Service - Sprint 123 (SPEC-0013)

Provides file system operations for compliance validation.
Abstracted to support both local file system and remote storage.

Version: 1.0.0
Date: January 30, 2026
Status: ACTIVE - Sprint 123
"""

import os
from pathlib import Path
from typing import Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession


class FileService:
    """
    File system operations for compliance validation.

    Provides abstraction over file operations to support:
    - Local file system (development)
    - Project repositories (via git clone or API)
    - MinIO storage (uploaded evidence)

    Usage:
        file_service = FileService()
        folders = await file_service.list_directories(project_id, "docs/")
    """

    def __init__(self, base_path: Optional[str] = None):
        """
        Initialize file service.

        Args:
            base_path: Base path for project files. If None, uses project's
                       configured repository path.
        """
        self.base_path = base_path

    async def list_directories(
        self,
        project_id: UUID,
        path: str = "",
        db: Optional[AsyncSession] = None,
    ) -> list[str]:
        """
        List directories in a project path.

        Args:
            project_id: Project UUID
            path: Relative path within project (e.g., "docs/")
            db: Database session for looking up project path

        Returns:
            List of directory names (not full paths)
        """
        # Get project base path
        project_path = await self._get_project_path(project_id, db)
        full_path = Path(project_path) / path

        if not full_path.exists():
            return []

        if not full_path.is_dir():
            return []

        # List directories only
        directories = [
            d.name for d in full_path.iterdir()
            if d.is_dir() and not d.name.startswith(".")
        ]

        return sorted(directories)

    async def list_files(
        self,
        project_id: UUID,
        path: str = "",
        pattern: str = "*",
        recursive: bool = False,
        db: Optional[AsyncSession] = None,
    ) -> list[str]:
        """
        List files in a project path.

        Args:
            project_id: Project UUID
            path: Relative path within project
            pattern: Glob pattern for filtering (e.g., "*.py", "*.md")
            recursive: Whether to search recursively
            db: Database session

        Returns:
            List of file paths relative to project root
        """
        project_path = await self._get_project_path(project_id, db)
        full_path = Path(project_path) / path

        if not full_path.exists():
            return []

        if recursive:
            files = list(full_path.rglob(pattern))
        else:
            files = list(full_path.glob(pattern))

        # Return relative paths
        return sorted([
            str(f.relative_to(project_path))
            for f in files
            if f.is_file()
        ])

    async def file_exists(
        self,
        project_id: UUID,
        file_path: str,
        db: Optional[AsyncSession] = None,
    ) -> bool:
        """
        Check if a file exists.

        Args:
            project_id: Project UUID
            file_path: Relative file path
            db: Database session

        Returns:
            True if file exists
        """
        project_path = await self._get_project_path(project_id, db)
        full_path = Path(project_path) / file_path
        return full_path.exists() and full_path.is_file()

    async def read_file(
        self,
        project_id: UUID,
        file_path: str,
        db: Optional[AsyncSession] = None,
    ) -> Optional[str]:
        """
        Read file contents.

        Args:
            project_id: Project UUID
            file_path: Relative file path
            db: Database session

        Returns:
            File contents as string, or None if not found
        """
        project_path = await self._get_project_path(project_id, db)
        full_path = Path(project_path) / file_path

        if not full_path.exists() or not full_path.is_file():
            return None

        try:
            return full_path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            return full_path.read_text(encoding="latin-1")
        except Exception:
            return None

    async def read_file_lines(
        self,
        project_id: UUID,
        file_path: str,
        start_line: int = 1,
        end_line: Optional[int] = None,
        db: Optional[AsyncSession] = None,
    ) -> list[str]:
        """
        Read specific lines from a file.

        Args:
            project_id: Project UUID
            file_path: Relative file path
            start_line: Starting line number (1-indexed)
            end_line: Ending line number (inclusive), None for all
            db: Database session

        Returns:
            List of lines
        """
        content = await self.read_file(project_id, file_path, db)
        if content is None:
            return []

        lines = content.splitlines()

        # Adjust for 1-indexed line numbers
        start_idx = max(0, start_line - 1)
        end_idx = end_line if end_line else len(lines)

        return lines[start_idx:end_idx]

    async def _get_project_path(
        self,
        project_id: UUID,
        db: Optional[AsyncSession] = None,
    ) -> str:
        """
        Get the file system path for a project.

        Args:
            project_id: Project UUID
            db: Database session

        Returns:
            Absolute path to project directory
        """
        # If base_path is provided, use it
        if self.base_path:
            return self.base_path

        # Try to get from database
        if db:
            from app.models.project import Project

            result = await db.execute(
                select(Project).where(Project.id == project_id)
            )
            project = result.scalar_one_or_none()

            if project and hasattr(project, "local_path") and project.local_path:
                return project.local_path

            if project and hasattr(project, "github_repo_full_name") and project.github_repo_full_name:
                # Return workspace path based on repo name
                workspace = os.getenv("WORKSPACE_PATH", "/tmp/workspaces")
                return os.path.join(workspace, project.github_repo_full_name.replace("/", "_"))

        # Fallback to current directory
        return os.getcwd()

    async def get_file_info(
        self,
        project_id: UUID,
        file_path: str,
        db: Optional[AsyncSession] = None,
    ) -> Optional[dict]:
        """
        Get file metadata.

        Args:
            project_id: Project UUID
            file_path: Relative file path
            db: Database session

        Returns:
            Dict with file info (size, modified, etc.) or None
        """
        project_path = await self._get_project_path(project_id, db)
        full_path = Path(project_path) / file_path

        if not full_path.exists():
            return None

        stat = full_path.stat()

        return {
            "path": file_path,
            "name": full_path.name,
            "size": stat.st_size,
            "is_file": full_path.is_file(),
            "is_dir": full_path.is_dir(),
            "modified": stat.st_mtime,
        }
