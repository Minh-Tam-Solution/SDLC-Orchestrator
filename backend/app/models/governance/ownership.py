"""
=========================================================================
Ownership Registry Model - File Ownership Annotations
SDLC Orchestrator - Sprint 108 (Governance Foundation)

Version: 1.0.0
Date: January 27, 2026
Status: ACTIVE - Sprint 108 Day 1
Authority: CTO + Backend Lead Approved
Framework: SDLC 5.3.0 Quality Assurance System

Purpose:
- Enforce Principle 2: NO CODE WITHOUT OWNERSHIP
- Track file ownership by user or team
- Sources: CODEOWNERS, git blame, directory pattern, task creator

Zero Mock Policy: Real SQLAlchemy model with all fields
=========================================================================
"""

from datetime import datetime
from typing import Optional
from uuid import uuid4

from sqlalchemy import (
    Column,
    DateTime,
    ForeignKey,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.db.base_class import Base


class OwnershipRegistry(Base):
    """
    File ownership annotations for governance validation.

    Ownership Sources (by confidence):
    - codeowners: 1.0 (explicit declaration)
    - git_blame: 0.8 (recent committer)
    - directory_pattern: 0.6 (inferred from path)
    - task_creator: 0.3 (fallback)
    - manual: 1.0 (explicit assignment)
    """

    __tablename__ = "ownership_registry"

    # Primary Key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)

    # File Metadata
    project_id = Column(
        UUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    file_path = Column(Text, nullable=False)
    file_hash = Column(String(64), nullable=True)  # SHA256 of file content

    # Ownership
    owner_user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    owner_team_id = Column(
        UUID(as_uuid=True),
        ForeignKey("teams.id", ondelete="SET NULL"),
        nullable=True,
    )
    ownership_source = Column(String(50), nullable=False)
    ownership_confidence = Column(Numeric(3, 2), nullable=True)  # 0.00 to 1.00

    # Module Classification
    module_name = Column(String(255), nullable=True)
    module_type = Column(String(100), nullable=True)

    # Timestamps
    declared_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    last_verified_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    # Relationships
    project = relationship("Project")
    owner_user = relationship("User", foreign_keys=[owner_user_id])
    owner_team = relationship("Team", foreign_keys=[owner_team_id])

    # Constraints
    __table_args__ = (
        UniqueConstraint("project_id", "file_path", name="uq_ownership_project_file"),
    )

    def __repr__(self) -> str:
        return f"OwnershipRegistry(id={self.id}, file={self.file_path})"
