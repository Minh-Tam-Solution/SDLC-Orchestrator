"""
Compliance Validation Models - Sprint 123 (SPEC-0013)

Version: 1.0.0
Date: January 30, 2026
Status: ACTIVE - Sprint 123
Authority: CTO Approved (A+ Grade, 98/100)
Reference: SPEC-0013 Compliance Validation Service

Models:
1. ComplianceScore - SDLC 6.0.5 compliance scoring results
2. ComplianceIssue - Individual compliance issues with severity
3. FolderCollisionCheck - Stage folder collision detection results

Database: PostgreSQL 15.5+
ORM: SQLAlchemy 2.0+
"""

from datetime import datetime
from enum import Enum
from typing import Any, Optional
from uuid import UUID

from sqlalchemy import Boolean, CheckConstraint, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base_class import Base


class IssueSeverity(str, Enum):
    """Issue severity levels."""

    CRITICAL = "critical"
    WARNING = "warning"
    INFO = "info"


class ComplianceCategory(str, Enum):
    """Compliance validation categories (10 categories × 10 points = 100 max)."""

    DOCUMENTATION_STRUCTURE = "documentation_structure"
    SPECIFICATIONS_MANAGEMENT = "specifications_management"
    CLAUDE_AGENTS_MD = "claude_agents_md"
    SASE_ARTIFACTS = "sase_artifacts"
    CODE_FILE_NAMING = "code_file_naming"
    MIGRATION_TRACKING = "migration_tracking"
    FRAMEWORK_ALIGNMENT = "framework_alignment"
    TEAM_ORGANIZATION = "team_organization"
    LEGACY_ARCHIVAL = "legacy_archival"
    GOVERNANCE_DOCUMENTATION = "governance_documentation"


class ComplianceScore(Base):
    """
    SDLC 6.0.5 compliance scoring result.

    Stores overall score (0-100) with category breakdown.
    10 categories × 10 points each = 100 maximum.

    Categories:
        1. documentation_structure: Stage folders (00-10), no duplicates
        2. specifications_management: YAML frontmatter, SPEC-XXXX numbering
        3. claude_agents_md: Version headers, required sections
        4. sase_artifacts: CRP, MRP, VCR templates present
        5. code_file_naming: snake_case (Python), camelCase/PascalCase (TS)
        6. migration_tracking: Progress percentage, deadline compliance
        7. framework_alignment: 7-Pillar + Section 7 compliance
        8. team_organization: SDLC Compliance Hub, roles defined
        9. legacy_archival: Proper 99-legacy/ or 10-Archive/ usage
        10. governance_documentation: CEO/CTO approvals, ADRs

    Example:
        score = ComplianceScore(
            project_id=project.id,
            overall_score=87,
            category_scores={
                "documentation_structure": 8,
                "specifications_management": 10,
                ...
            },
            issues_summary={
                "total": 5,
                "critical": 1,
                "warning": 3,
                "info": 1
            }
        )
    """

    __tablename__ = "compliance_scores"

    # Primary key
    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        primary_key=True,
        server_default=func.gen_random_uuid(),
        comment="Unique identifier for compliance score",
    )

    # Foreign keys
    project_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Project this score belongs to",
    )

    calculated_by_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        comment="User who triggered the calculation",
    )

    # Score data
    overall_score: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        comment="Overall compliance score (0-100)",
    )

    category_scores: Mapped[dict[str, Any]] = mapped_column(
        JSONB,
        nullable=False,
        comment='Score breakdown: {"documentation_structure": 8, "specifications": 10, ...}',
    )

    issues_summary: Mapped[dict[str, Any]] = mapped_column(
        JSONB,
        nullable=False,
        comment='Issues count: {"total": 5, "critical": 1, "warning": 3, "info": 1}',
    )

    recommendations: Mapped[Optional[list[str]]] = mapped_column(
        JSONB,
        nullable=True,
        comment="Array of recommendation strings",
    )

    # Metadata
    calculated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        comment="Score calculation timestamp",
    )

    validation_version: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        server_default="1.0.0",
        comment="Validator version used",
    )

    framework_version: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        server_default="6.0.5",
        comment="SDLC Framework version validated against",
    )

    expires_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="Cache expiration timestamp",
    )

    # Performance metrics
    scan_duration_ms: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
        comment="Scan duration in milliseconds",
    )

    files_scanned: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
        comment="Number of files scanned",
    )

    # Relationships
    issues: Mapped[list["ComplianceIssue"]] = relationship(
        "ComplianceIssue",
        back_populates="score",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    project: Mapped["Project"] = relationship(  # type: ignore[name-defined]
        "Project",
        back_populates="compliance_scores",
        lazy="joined",
    )

    calculated_by: Mapped[Optional["User"]] = relationship(  # type: ignore[name-defined]
        "User",
        foreign_keys=[calculated_by_id],
        lazy="joined",
    )

    # Table constraints
    __table_args__ = (
        CheckConstraint(
            "overall_score >= 0 AND overall_score <= 100",
            name="ck_compliance_scores_valid_score",
        ),
    )

    def is_cached_valid(self) -> bool:
        """Check if cached score is still valid."""
        if self.expires_at is None:
            return False
        return datetime.utcnow() < self.expires_at.replace(tzinfo=None)

    def get_category_score(self, category: ComplianceCategory) -> int:
        """Get score for specific category."""
        return self.category_scores.get(category.value, 0)

    def get_critical_count(self) -> int:
        """Get count of critical issues."""
        return self.issues_summary.get("critical", 0)

    def is_passing(self, threshold: int = 80) -> bool:
        """Check if score meets threshold."""
        return self.overall_score >= threshold


class ComplianceIssue(Base):
    """
    Individual compliance issue found during validation.

    Issues are categorized by:
    - category: One of 10 compliance categories
    - severity: critical, warning, or info
    - issue_code: Unique code for the issue type

    Example:
        issue = ComplianceIssue(
            score_id=score.id,
            category="documentation_structure",
            severity="critical",
            issue_code="DUPLICATE_STAGE_FOLDER",
            message="Duplicate stage folder detected: 04-Development and 04-Testing",
            file_path="docs/",
            fix_suggestion="Archive one folder: mv docs/04-Testing docs/10-Archive/",
            fix_command="sdlcctl fix --duplicates",
            auto_fixable=False
        )
    """

    __tablename__ = "compliance_issues"

    # Primary key
    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        primary_key=True,
        server_default=func.gen_random_uuid(),
        comment="Unique identifier for issue",
    )

    # Foreign keys
    score_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("compliance_scores.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Parent compliance score",
    )

    # Issue details
    category: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
        comment="Category: documentation_structure, specifications, etc.",
    )

    severity: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        index=True,
        comment="Severity: critical, warning, info",
    )

    issue_code: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
        comment="Issue code: DUPLICATE_STAGE_FOLDER, MISSING_YAML_FRONTMATTER, etc.",
    )

    message: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="Human-readable issue message",
    )

    # Location
    file_path: Mapped[Optional[str]] = mapped_column(
        String(500),
        nullable=True,
        comment="Relative file path where issue found",
    )

    line_number: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
        comment="Line number if applicable",
    )

    # Fix information
    fix_suggestion: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Suggested fix for the issue",
    )

    fix_command: Mapped[Optional[str]] = mapped_column(
        String(500),
        nullable=True,
        comment="CLI command to fix: sdlcctl fix --xxx",
    )

    auto_fixable: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        server_default="false",
        comment="Whether issue can be auto-fixed",
    )

    # Additional context
    context: Mapped[Optional[dict[str, Any]]] = mapped_column(
        JSONB,
        nullable=True,
        comment="Additional context for the issue",
    )

    # Relationships
    score: Mapped["ComplianceScore"] = relationship(
        "ComplianceScore",
        back_populates="issues",
        lazy="joined",
    )

    # Table constraints
    __table_args__ = (
        CheckConstraint(
            "severity IN ('critical', 'warning', 'info')",
            name="ck_compliance_issues_valid_severity",
        ),
    )

    def is_critical(self) -> bool:
        """Check if issue is critical severity."""
        return self.severity == IssueSeverity.CRITICAL.value

    def has_auto_fix(self) -> bool:
        """Check if issue has auto-fix available."""
        return self.auto_fixable and self.fix_command is not None


class FolderCollisionCheck(Base):
    """
    Stage folder collision detection result.

    Validates that each stage prefix (00-10) has exactly one folder.
    Detects:
    - collisions: Multiple folders with same prefix (e.g., 04-Development + 04-Testing)
    - gaps: Missing required stage folders
    - extras: Non-standard folders

    Example:
        check = FolderCollisionCheck(
            project_id=project.id,
            docs_path="docs/",
            valid=False,
            collisions=[{
                "stage_prefix": "04",
                "stage_name": "build",
                "folders": ["04-Development", "04-Testing"],
                "severity": "critical"
            }],
            gaps=["03-integrate"],
            extras=["99-legacy"]
        )
    """

    __tablename__ = "folder_collision_checks"

    # Primary key
    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        primary_key=True,
        server_default=func.gen_random_uuid(),
        comment="Unique identifier for collision check",
    )

    # Foreign keys
    project_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Project this check belongs to",
    )

    checked_by_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        comment="User who triggered the check",
    )

    # Check configuration
    docs_path: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
        server_default="docs/",
        comment="Docs folder path checked",
    )

    checked_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        comment="Check timestamp",
    )

    # Results
    valid: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        index=True,
        comment="True if no collisions found",
    )

    collisions: Mapped[Optional[list[dict[str, Any]]]] = mapped_column(
        JSONB,
        nullable=True,
        comment="Array of collisions: [{stage_prefix, folders, severity}]",
    )

    gaps: Mapped[Optional[list[str]]] = mapped_column(
        JSONB,
        nullable=True,
        comment="Array of missing stage folders",
    )

    extras: Mapped[Optional[list[str]]] = mapped_column(
        JSONB,
        nullable=True,
        comment="Array of non-standard folders",
    )

    total_folders: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
        comment="Total folders scanned",
    )

    # Relationships
    project: Mapped["Project"] = relationship(  # type: ignore[name-defined]
        "Project",
        back_populates="folder_collision_checks",
        lazy="joined",
    )

    checked_by: Mapped[Optional["User"]] = relationship(  # type: ignore[name-defined]
        "User",
        foreign_keys=[checked_by_id],
        lazy="joined",
    )

    def has_collisions(self) -> bool:
        """Check if any collisions were found."""
        return not self.valid and self.collisions is not None and len(self.collisions) > 0

    def collision_count(self) -> int:
        """Get number of collisions."""
        return len(self.collisions) if self.collisions else 0

    def gap_count(self) -> int:
        """Get number of missing stages."""
        return len(self.gaps) if self.gaps else 0
