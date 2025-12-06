"""
=========================================================================
SDLC Structure Validation Model - SDLC 5.0.0 Folder Compliance
SDLC Orchestrator - Stage 03 (BUILD)

Version: 1.0.0
Date: December 5, 2025
Status: ACTIVE - Sprint 30 Day 3 (Web API Endpoint)
Authority: Backend Lead + CTO Approved
Foundation: ADR-014 (SDLC Structure Validator)
Framework: SDLC 5.0.0 Complete Lifecycle

Purpose:
- Store SDLC 5.0.0 folder structure validation results
- Track validation history per project
- Support 4-tier classification (LITE, STANDARD, PROFESSIONAL, ENTERPRISE)
- Enable compliance trend analysis and reporting

Security Standards:
- Row-Level Security (RLS) for multi-tenancy
- Immutable validation records (append-only)
- SHA256 hashing for result integrity

Zero Mock Policy: Real SQLAlchemy model with all fields
=========================================================================
"""

from datetime import datetime
from enum import Enum
from typing import Optional
from uuid import uuid4

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import relationship

from app.db.base_class import Base


class SDLCTier(str, Enum):
    """SDLC 5.0.0 Project Tier Classification."""
    LITE = "lite"
    STANDARD = "standard"
    PROFESSIONAL = "professional"
    ENTERPRISE = "enterprise"


class ValidationTrigger(str, Enum):
    """How validation was triggered."""
    MANUAL = "manual"
    API = "api"
    WEBHOOK = "webhook"
    CICD = "cicd"
    PRECOMMIT = "precommit"
    SCHEDULED = "scheduled"


class IssueSeverity(str, Enum):
    """Validation issue severity levels."""
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


class SDLCValidation(Base):
    """
    SDLC 5.0.0 Structure Validation model for folder compliance tracking.

    Purpose:
        - Store validation results for SDLC 5.0.0 folder structure
        - Track compliance score per project
        - Store stage presence and P0 artifact status
        - Support validation history and trends

    Fields:
        - id: UUID primary key
        - project_id: Foreign key to Project
        - validated_by: Foreign key to User (who triggered validation)
        - trigger_type: How validation was triggered
        - tier: Project tier (lite, standard, professional, enterprise)
        - tier_detected: Whether tier was auto-detected
        - is_compliant: Overall compliance status
        - compliance_score: Score from 0-100
        - stages_found: Number of stages found
        - stages_required: Number of required stages for tier
        - stages_detail: JSONB array of stage info
        - p0_status: JSONB object with P0 artifact status
        - error_count: Number of errors
        - warning_count: Number of warnings
        - issues: JSONB array of validation issues
        - validation_time_ms: Validation duration in milliseconds
        - docs_root: Documentation root folder used
        - config_used: Configuration file used (if any)
        - validated_at: Timestamp when validation completed
        - result_hash: SHA256 hash of validation result for integrity

    Relationships:
        - project: Many-to-One with Project model
        - validated_by_user: Many-to-One with User model

    Indexes:
        - project_id (B-tree) - Fast project lookup
        - validated_at DESC - Fast recent validations lookup
        - compliance_score - Score-based filtering
        - tier - Tier-based filtering

    Usage Example:
        validation = SDLCValidation(
            project_id=project.id,
            validated_by=user.id,
            trigger_type=ValidationTrigger.API,
            tier=SDLCTier.PROFESSIONAL,
            is_compliant=True,
            compliance_score=100,
            stages_found=10,
            stages_required=10,
            stages_detail=[
                {"stage": "00-Project-Foundation", "exists": True, "artifacts": 5}
            ],
            p0_status={"found": 15, "required": 15, "artifacts": [...]}
        )
        session.add(validation)
        session.commit()
    """

    __tablename__ = "sdlc_validations"

    # Primary Key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4, index=True)

    # Project Reference
    project_id = Column(
        UUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Trigger Information
    validated_by = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    trigger_type = Column(
        String(50),
        nullable=False,
        default=ValidationTrigger.API.value,
    )

    # Tier Classification
    tier = Column(
        String(20),
        nullable=False,
        default=SDLCTier.STANDARD.value,
        index=True,
    )
    tier_detected = Column(
        Boolean,
        nullable=False,
        default=False,
        comment="True if tier was auto-detected, False if explicitly set",
    )

    # Compliance Status
    is_compliant = Column(
        Boolean,
        nullable=False,
        default=False,
        index=True,
    )
    compliance_score = Column(
        Integer,
        nullable=False,
        default=0,
        index=True,
        comment="Compliance score 0-100",
    )

    # Stage Information
    stages_found = Column(Integer, nullable=False, default=0)
    stages_required = Column(Integer, nullable=False, default=0)
    stages_detail = Column(
        JSONB,
        nullable=False,
        default=list,
        comment="Array of stage objects with name, exists, artifacts count",
    )
    stages_missing = Column(
        JSONB,
        nullable=False,
        default=list,
        comment="Array of missing stage names",
    )

    # P0 Artifact Status (PROFESSIONAL/ENTERPRISE tiers)
    p0_status = Column(
        JSONB,
        nullable=True,
        default=dict,
        comment="P0 artifact status: found, required, artifacts list",
    )

    # Issue Counts
    error_count = Column(Integer, nullable=False, default=0)
    warning_count = Column(Integer, nullable=False, default=0)

    # Detailed Issues
    issues = Column(
        JSONB,
        nullable=False,
        default=list,
        comment="Array of issue objects with severity, code, message, location",
    )

    # Timing
    validation_time_ms = Column(
        Float,
        nullable=True,
        comment="Validation duration in milliseconds",
    )
    validated_at = Column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        index=True,
    )

    # Configuration
    docs_root = Column(
        String(500),
        nullable=False,
        default="docs",
        comment="Documentation root folder path",
    )
    config_file = Column(
        String(500),
        nullable=True,
        comment="Configuration file used (if any)",
    )
    strict_mode = Column(
        Boolean,
        nullable=False,
        default=False,
        comment="Whether strict mode was enabled",
    )

    # Integrity
    result_hash = Column(
        String(64),
        nullable=True,
        comment="SHA256 hash of validation result JSON",
    )

    # Git Context (optional)
    git_commit = Column(String(40), nullable=True, comment="Git commit SHA")
    git_branch = Column(String(255), nullable=True, comment="Git branch name")

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    project = relationship("Project", backref="sdlc_validations")
    validated_by_user = relationship("User", backref="triggered_sdlc_validations")

    def __repr__(self) -> str:
        return (
            f"<SDLCValidation(id={self.id}, project_id={self.project_id}, "
            f"tier={self.tier}, score={self.compliance_score}, compliant={self.is_compliant})>"
        )

    @property
    def has_errors(self) -> bool:
        """Check if validation has any errors."""
        return self.error_count > 0

    @property
    def has_warnings(self) -> bool:
        """Check if validation has any warnings."""
        return self.warning_count > 0

    @property
    def stage_coverage(self) -> float:
        """Calculate stage coverage percentage."""
        if self.stages_required == 0:
            return 100.0
        return (self.stages_found / self.stages_required) * 100

    @property
    def error_issues(self) -> list:
        """Get error severity issues only."""
        if not self.issues:
            return []
        return [i for i in self.issues if i.get("severity") == "error"]

    @property
    def warning_issues(self) -> list:
        """Get warning severity issues only."""
        if not self.issues:
            return []
        return [i for i in self.issues if i.get("severity") == "warning"]


class SDLCValidationIssue(Base):
    """
    Individual SDLC Validation Issue for detailed tracking.

    Purpose:
        - Store individual validation issues
        - Enable issue trend analysis
        - Support issue resolution tracking

    Fields:
        - id: UUID primary key
        - validation_id: Foreign key to SDLCValidation
        - project_id: Foreign key to Project (denormalized)
        - severity: Issue severity (error, warning, info)
        - code: Issue code (e.g., MISSING_STAGE, P0_NOT_FOUND)
        - message: Human-readable message
        - location: File/folder path
        - suggestion: Suggested fix
        - created_at: Record creation timestamp

    Usage Example:
        issue = SDLCValidationIssue(
            validation_id=validation.id,
            project_id=project.id,
            severity=IssueSeverity.ERROR,
            code="MISSING_STAGE",
            message="Stage 05-Deployment-Release not found",
            location="docs/05-Deployment-Release",
            suggestion="Create docs/05-Deployment-Release folder with required files"
        )
        session.add(issue)
        session.commit()
    """

    __tablename__ = "sdlc_validation_issues"

    # Primary Key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4, index=True)

    # Validation Reference
    validation_id = Column(
        UUID(as_uuid=True),
        ForeignKey("sdlc_validations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Project Reference (denormalized for query performance)
    project_id = Column(
        UUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Issue Details
    severity = Column(
        String(20),
        nullable=False,
        default=IssueSeverity.WARNING.value,
        index=True,
    )
    code = Column(
        String(100),
        nullable=False,
        index=True,
        comment="Issue code (e.g., MISSING_STAGE, P0_NOT_FOUND)",
    )
    message = Column(
        Text,
        nullable=False,
    )
    location = Column(
        String(1000),
        nullable=True,
        comment="File path, folder path, or artifact name",
    )
    suggestion = Column(
        Text,
        nullable=True,
        comment="Suggested fix for the issue",
    )

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    validation = relationship("SDLCValidation", backref="issue_records")
    project = relationship("Project", backref="sdlc_validation_issues")

    def __repr__(self) -> str:
        return (
            f"<SDLCValidationIssue(id={self.id}, code={self.code}, "
            f"severity={self.severity})>"
        )

    @property
    def is_blocking(self) -> bool:
        """Check if issue should block progression."""
        return self.severity == IssueSeverity.ERROR.value
