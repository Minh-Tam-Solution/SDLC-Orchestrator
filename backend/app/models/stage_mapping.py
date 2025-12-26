"""
Project Stage Mapping Model - SDLC 5.1.2

Version: 1.0.0
Date: December 24, 2025
Status: ACTIVE - Sprint 49
Authority: CTO Approved
Foundation: SDLC-Project-Structure-Standard.md
Framework: SDLC 5.1.2

Purpose:
Persist folder-to-stage mappings for each project.
Only /docs folders are stage-mapped (00-09).
Code folders (backend, frontend, tests) are NOT stage-mapped.

Table: project_stage_mappings
"""

from datetime import datetime
from typing import Optional
from uuid import UUID

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base_class import Base


class ProjectStageMapping(Base):
    """
    Maps a folder path to an SDLC stage for a project.

    SDLC 5.1.2 Rules:
    - Only /docs folders are stage-mapped (stages 00-09)
    - Stage 10-archive is archive folder, NOT a numbered stage
    - Code folders (backend, frontend, tests) are NOT stage-mapped

    Example:
        mapping = ProjectStageMapping(
            project_id=project.id,
            folder_path="docs/00-foundation",
            stage_code="00",
            stage_name="FOUNDATION",
            is_auto_detected=True,
            confidence=0.95,
        )
    """

    __tablename__ = "project_stage_mappings"

    # Primary key
    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        server_default="gen_random_uuid()",
    )

    # Foreign key to project
    project_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Folder path relative to repo root
    folder_path: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        comment="Folder path relative to repo root, e.g., 'docs/00-foundation'",
    )

    # SDLC stage code (00-09, or 10 for archive)
    stage_code: Mapped[str] = mapped_column(
        String(10),
        nullable=False,
        index=True,
        comment="SDLC stage code: '00', '01', ..., '09', '10' (archive)",
    )

    # Human-readable stage name
    stage_name: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
        comment="Human-readable stage name: FOUNDATION, PLANNING, etc.",
    )

    # Whether mapping was auto-detected or manually set
    is_auto_detected: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        comment="True if auto-detected by system, False if manually set by user",
    )

    # Confidence score for auto-detection
    confidence: Mapped[Optional[float]] = mapped_column(
        Float,
        nullable=True,
        comment="Confidence score for auto-detection (0.0-1.0)",
    )

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.utcnow,
    )

    updated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        onupdate=datetime.utcnow,
    )

    # Relationship to Project
    project: Mapped["Project"] = relationship(
        "Project",
        back_populates="stage_mappings",
        lazy="selectin",
    )

    # Composite unique constraint
    __table_args__ = (
        UniqueConstraint(
            "project_id", "folder_path", name="uq_project_stage_mapping_folder"
        ),
    )

    def __repr__(self) -> str:
        return (
            f"<ProjectStageMapping(project_id={self.project_id}, "
            f"folder='{self.folder_path}', stage={self.stage_code})>"
        )

    def to_dict(self) -> dict:
        """Convert to dictionary for API response."""
        return {
            "id": str(self.id),
            "project_id": str(self.project_id),
            "folder_path": self.folder_path,
            "stage_code": self.stage_code,
            "stage_name": self.stage_name,
            "is_auto_detected": self.is_auto_detected,
            "confidence": self.confidence,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
