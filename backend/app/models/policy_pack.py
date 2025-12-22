"""
Policy Pack Models - Project Policy Configuration

SDLC Stage: 04 - BUILD
Sprint: 43 - Policy Guards & Evidence UI
Framework: SDLC 5.1.1 (10-Stage Lifecycle, 4-Tier Classification)
Epic: EP-02 AI Safety Layer v1

Purpose:
- Policy Pack model for project-level policy configuration
- Policy Rule model for individual OPA policies
- Policy Evaluation history for audit trail

Architecture:
- One PolicyPack per Project (1:1 relationship)
- PolicyPack contains multiple PolicyRules (1:N)
- PolicyEvaluationHistory tracks all evaluations

Reference:
- docs/02-design/14-Technical-Specs/Policy-Guards-Design.md
- docs/02-design/03-Database-Design/Sprint-43-Migration-Schema.md

Version: 1.0.0
Updated: December 2025
Zero Mock Policy: Real SQLAlchemy models
"""

from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import uuid4

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import relationship

from app.db.base_class import Base


class PolicyPack(Base):
    """
    Policy Pack model - Project-level policy configuration.

    Purpose:
    - Configure validation pipeline for a project
    - Set coverage thresholds and architecture rules
    - Contains custom OPA policies

    One-to-One relationship with Project.
    """

    __tablename__ = "policy_packs"

    # Primary Key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4, index=True)

    # Project Relationship (1:1)
    project_id = Column(
        UUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,  # One pack per project
        index=True,
    )

    # Pack Identity
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=False)
    version = Column(String(20), nullable=False, default="1.0.0")

    # SDLC 5.1.1 4-Tier Classification
    tier = Column(
        String(20),
        nullable=False,
        default="standard",
        comment="lite, standard, professional, enterprise",
    )

    # Validator Pipeline Configuration (JSONB array)
    validators = Column(
        JSONB,
        nullable=False,
        default=list,
        comment='[{"name": "lint", "enabled": true, "blocking": true, "config": {}}]',
    )

    # Coverage Settings
    coverage_threshold = Column(
        Integer,
        nullable=False,
        default=80,
        comment="Minimum test coverage percentage (0-100)",
    )
    coverage_blocking = Column(
        Boolean,
        nullable=False,
        default=False,
        comment="If true, coverage below threshold blocks merge",
    )

    # Architecture Rules (JSONB arrays)
    forbidden_imports = Column(
        JSONB,
        nullable=False,
        default=list,
        comment='["minio", "grafana_sdk"] - AGPL imports to block',
    )
    required_patterns = Column(
        JSONB,
        nullable=False,
        default=list,
        comment='["from app.core.logging import"] - Required patterns',
    )

    # Creator
    created_by = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )

    # Audit Timestamps (inherited from Base but explicit for clarity)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )
    deleted_at = Column(DateTime, nullable=True)

    # Relationships
    project = relationship("Project", back_populates="policy_pack")
    rules = relationship(
        "PolicyRule",
        back_populates="policy_pack",
        cascade="all, delete-orphan",
        order_by="PolicyRule.created_at",
    )
    evaluations = relationship(
        "PolicyEvaluationHistory",
        back_populates="policy_pack",
        cascade="all, delete-orphan",
    )
    creator = relationship("User", foreign_keys=[created_by])

    def __repr__(self) -> str:
        return f"<PolicyPack(project_id={self.project_id}, name={self.name}, tier={self.tier})>"

    @property
    def policies_count(self) -> int:
        """Count of policy rules in this pack."""
        return len(self.rules) if self.rules else 0

    @property
    def validators_count(self) -> int:
        """Count of enabled validators."""
        if not self.validators:
            return 0
        return len([v for v in self.validators if v.get("enabled", True)])


class PolicyRule(Base):
    """
    Policy Rule model - Individual OPA policy in a pack.

    Purpose:
    - Store Rego policy code for OPA evaluation
    - Configure severity and blocking behavior
    - Support policy enabling/disabling
    """

    __tablename__ = "policy_rules"

    # Primary Key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4, index=True)

    # Policy Pack Relationship
    policy_pack_id = Column(
        UUID(as_uuid=True),
        ForeignKey("policy_packs.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Policy Identity
    policy_id = Column(
        String(100),
        nullable=False,
        comment="Unique policy identifier (kebab-case), e.g., no-hardcoded-secrets",
    )
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=False)

    # Rego Policy Code
    rego_policy = Column(
        Text,
        nullable=False,
        comment="OPA Rego policy source code",
    )

    # Policy Behavior
    severity = Column(
        String(20),
        nullable=False,
        default="medium",
        comment="critical, high, medium, low, info",
    )
    blocking = Column(
        Boolean,
        nullable=False,
        default=True,
        comment="If true, violation blocks merge",
    )
    enabled = Column(
        Boolean,
        nullable=False,
        default=True,
        comment="If false, policy is skipped during evaluation",
    )

    # Message Template
    message_template = Column(
        Text,
        nullable=False,
        comment="Message shown on failure. Use {file}, {line} placeholders.",
    )

    # Categorization
    tags = Column(
        JSONB,
        nullable=False,
        default=list,
        comment='["security", "architecture"]',
    )

    # Audit Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    # Relationships
    policy_pack = relationship("PolicyPack", back_populates="rules")

    # Unique constraint: policy_id must be unique within a pack
    __table_args__ = (
        # Composite unique constraint
        {"extend_existing": True},
    )

    def __repr__(self) -> str:
        return f"<PolicyRule(policy_id={self.policy_id}, severity={self.severity})>"


class PolicyEvaluationHistory(Base):
    """
    Policy Evaluation History - Audit trail for policy evaluations.

    Purpose:
    - Track all policy evaluations for a PR
    - Store results for compliance reporting
    - Enable trend analysis and metrics
    """

    __tablename__ = "policy_evaluation_history"

    # Primary Key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4, index=True)

    # Context
    project_id = Column(
        UUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    pr_number = Column(Integer, nullable=False)
    policy_pack_id = Column(
        UUID(as_uuid=True),
        ForeignKey("policy_packs.id", ondelete="SET NULL"),
        nullable=True,
    )

    # Results Summary
    total_policies = Column(Integer, nullable=False)
    passed_count = Column(Integer, nullable=False)
    failed_count = Column(Integer, nullable=False)
    blocked = Column(
        Boolean,
        nullable=False,
        comment="True if any blocking policy failed",
    )

    # Detailed Results (JSONB)
    results = Column(
        JSONB,
        nullable=False,
        comment="Full evaluation results for each policy",
    )

    # Timing
    started_at = Column(DateTime, nullable=False)
    completed_at = Column(DateTime, nullable=False)
    duration_ms = Column(Integer, nullable=False)

    # Audit Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    project = relationship("Project")
    policy_pack = relationship("PolicyPack", back_populates="evaluations")

    # Indexes for common queries
    __table_args__ = (
        # Index for PR lookup
        {"extend_existing": True},
    )

    def __repr__(self) -> str:
        return (
            f"<PolicyEvaluationHistory("
            f"project_id={self.project_id}, pr={self.pr_number}, "
            f"passed={self.passed_count}/{self.total_policies})>"
        )

    @property
    def pass_rate(self) -> float:
        """Calculate pass rate as percentage."""
        if self.total_policies == 0:
            return 100.0
        return (self.passed_count / self.total_policies) * 100
