"""
Duplicate Folder Detector - Sprint 123 (SPEC-0013)

Detects stage folder collisions in SDLC 6.0.0 projects.
Validates that each stage prefix (00-10) has exactly one folder.

Detection Types:
1. Collisions: Multiple folders with same prefix (e.g., 04-Dev + 04-Test)
2. Gaps: Missing required stage folders
3. Extras: Non-standard folders in docs root
"""

from datetime import datetime
from typing import Optional
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.compliance_validation import FolderCollisionCheck, IssueSeverity
from app.schemas.compliance import (
    DuplicateDetectionResponse,
    FolderCollision,
)


class DuplicateFolderDetector:
    """
    Detect stage folder collisions in SDLC 6.0.0 projects.

    Validates that each stage prefix (00-10) has exactly one folder.
    Reports collisions, gaps, and extra folders.

    Usage:
        detector = DuplicateFolderDetector(db, file_service)
        result = await detector.detect(project_id)
        # result.valid = False if collisions found
        # result.collisions = [{stage_prefix: "04", folders: [...]}]
    """

    STAGE_PREFIXES = [
        ("00", "discover"),
        ("01", "planning"),
        ("02", "design"),
        ("03", "integrate"),
        ("04", "build"),
        ("05", "test"),
        ("06", "deploy"),
        ("07", "operate"),
        ("08", "collaborate"),
        ("09", "govern"),
        ("10", "archive"),
    ]

    # Required stages (10 optional for archive)
    REQUIRED_PREFIXES = {"00", "01", "02", "03", "04", "05", "06", "07", "08", "09"}

    # Allowed non-stage folders in docs/
    ALLOWED_EXTRAS = {"specs", "templates", ".git", ".github", "README.md"}

    def __init__(self, db: AsyncSession, file_service):
        """
        Initialize detector with database session and file service.

        Args:
            db: Async database session
            file_service: Service for file operations
        """
        self.db = db
        self.file_service = file_service

    async def detect(
        self,
        project_id: UUID,
        user_id: Optional[UUID] = None,
        docs_path: str = "docs/",
    ) -> DuplicateDetectionResponse:
        """
        Detect duplicate stage folders.

        Args:
            project_id: Project UUID
            user_id: User who triggered the check
            docs_path: Path to docs folder (default: "docs/")

        Returns:
            DuplicateDetectionResponse with collisions, gaps, extras
        """
        # Get all directories in docs path
        folders = await self.file_service.list_directories(
            project_id=project_id,
            path=docs_path,
        )

        collisions: list[FolderCollision] = []
        gaps: list[str] = []
        extras: list[str] = []

        # Track which prefixes we've seen
        prefix_to_folders: dict[str, list[str]] = {}

        # Categorize each folder
        for folder in folders:
            if "-" in folder:
                prefix = folder.split("-")[0]
                if prefix.isdigit():
                    if prefix not in prefix_to_folders:
                        prefix_to_folders[prefix] = []
                    prefix_to_folders[prefix].append(folder)
                    continue

            # Check if it's an allowed extra
            if folder.lower() not in {a.lower() for a in self.ALLOWED_EXTRAS}:
                extras.append(folder)

        # Check each stage prefix for collisions
        for prefix, stage_name in self.STAGE_PREFIXES:
            matching = prefix_to_folders.get(prefix, [])

            if len(matching) > 1:
                # Collision detected
                collisions.append(FolderCollision(
                    stage_prefix=prefix,
                    stage_name=stage_name,
                    folders=matching,
                    severity=IssueSeverity.CRITICAL,
                    fix_suggestion=self._generate_fix_suggestion(prefix, matching, docs_path),
                ))
            elif len(matching) == 0 and prefix in self.REQUIRED_PREFIXES:
                # Missing required stage
                gaps.append(f"{prefix}-{stage_name}")

        # Determine overall validity
        valid = len(collisions) == 0

        # Save check result to database
        check_result = await self._save_check_result(
            project_id=project_id,
            user_id=user_id,
            docs_path=docs_path,
            valid=valid,
            collisions=collisions,
            gaps=gaps,
            extras=extras,
            total_folders=len(folders),
        )

        return DuplicateDetectionResponse(
            project_id=project_id,
            valid=valid,
            collisions=collisions,
            gaps=gaps,
            extras=extras,
            checked_at=check_result.checked_at,
            docs_path=docs_path,
            total_folders=len(folders),
        )

    def _generate_fix_suggestion(
        self,
        prefix: str,
        folders: list[str],
        docs_path: str,
    ) -> str:
        """
        Generate archive command for collision resolution.

        Keeps the first folder, suggests archiving the rest.
        """
        to_keep = folders[0]
        to_archive = folders[1:]

        archive_path = f"{docs_path}10-archive/duplicate-folders-sprint123"

        commands = [
            f"mkdir -p {archive_path}",
            *[f"mv {docs_path}{f} {archive_path}/" for f in to_archive],
        ]

        return " && ".join(commands)

    async def _save_check_result(
        self,
        project_id: UUID,
        user_id: Optional[UUID],
        docs_path: str,
        valid: bool,
        collisions: list[FolderCollision],
        gaps: list[str],
        extras: list[str],
        total_folders: int,
    ) -> FolderCollisionCheck:
        """Save check result for audit trail."""
        check_result = FolderCollisionCheck(
            project_id=project_id,
            checked_by_id=user_id,
            docs_path=docs_path,
            valid=valid,
            collisions=[
                {
                    "stage_prefix": c.stage_prefix,
                    "stage_name": c.stage_name,
                    "folders": c.folders,
                    "severity": c.severity.value,
                }
                for c in collisions
            ] if collisions else None,
            gaps=gaps if gaps else None,
            extras=extras if extras else None,
            total_folders=total_folders,
            checked_at=datetime.utcnow(),
        )

        self.db.add(check_result)
        await self.db.commit()
        await self.db.refresh(check_result)

        return check_result

    async def get_last_check(
        self,
        project_id: UUID,
    ) -> Optional[DuplicateDetectionResponse]:
        """
        Get the most recent collision check for a project.

        Args:
            project_id: Project UUID

        Returns:
            Most recent check result, or None if never checked
        """
        from sqlalchemy import select

        stmt = (
            select(FolderCollisionCheck)
            .where(FolderCollisionCheck.project_id == project_id)
            .order_by(FolderCollisionCheck.checked_at.desc())
            .limit(1)
        )

        result = await self.db.execute(stmt)
        check = result.scalar_one_or_none()

        if not check:
            return None

        return DuplicateDetectionResponse(
            project_id=project_id,
            valid=check.valid,
            collisions=[
                FolderCollision(
                    stage_prefix=c["stage_prefix"],
                    stage_name=c["stage_name"],
                    folders=c["folders"],
                    severity=IssueSeverity(c["severity"]),
                    fix_suggestion="",  # Not stored
                )
                for c in (check.collisions or [])
            ],
            gaps=check.gaps or [],
            extras=check.extras or [],
            checked_at=check.checked_at,
            docs_path=check.docs_path,
            total_folders=check.total_folders,
        )
