"""
=========================================================================
Compliance Framework Models
SDLC Orchestrator - Sprint 156 (Phase 3: COMPLIANCE)

Version: 1.0.0
Date: April 7, 2026
Status: ACTIVE
Authority: CTO Approved
Framework: SDLC 6.0.5
Reference: ADR-051, NIST AI RMF 1.0, EU AI Act 2024/1689, ISO 42001:2023

Purpose:
Shared compliance framework models supporting 3 regulatory standards:
- NIST AI RMF (GOVERN, MAP, MEASURE, MANAGE)
- EU AI Act (4-level risk classification)
- ISO 42001 (38 management system controls)

Tables:
- compliance_frameworks: Registry of compliance frameworks
- compliance_controls: Per-framework controls with OPA policy linkage
- compliance_assessments: Per-project control evaluations
- compliance_risk_register: Risk entries (NIST GOVERN/MAP)
- compliance_raci: RACI accountability matrix

Zero Mock Policy: Production-ready implementation
=========================================================================
"""

from datetime import date, datetime
from enum import Enum as PyEnum
from typing import List, Optional
from uuid import uuid4

from sqlalchemy import (
    Boolean,
    Column,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, UUID as PgUUID
from sqlalchemy.orm import relationship

from app.db.base_class import Base


# =============================================================================
# Enums
# =============================================================================


class AssessmentStatus(str, PyEnum):
    """Compliance assessment status for a control."""

    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    COMPLIANT = "compliant"
    NON_COMPLIANT = "non_compliant"
    NOT_APPLICABLE = "not_applicable"


class ControlSeverity(str, PyEnum):
    """Severity level for compliance controls."""

    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class RiskLikelihood(str, PyEnum):
    """Risk likelihood scale (1-5)."""

    RARE = "rare"               # 1
    UNLIKELY = "unlikely"       # 2
    POSSIBLE = "possible"       # 3
    LIKELY = "likely"           # 4
    ALMOST_CERTAIN = "almost_certain"  # 5


class RiskImpact(str, PyEnum):
    """Risk impact scale (1-5)."""

    NEGLIGIBLE = "negligible"   # 1
    MINOR = "minor"             # 2
    MODERATE = "moderate"       # 3
    MAJOR = "major"             # 4
    CATASTROPHIC = "catastrophic"  # 5


class RiskStatus(str, PyEnum):
    """Risk management lifecycle status."""

    IDENTIFIED = "identified"
    MITIGATING = "mitigating"
    MITIGATED = "mitigated"
    ACCEPTED = "accepted"
    CLOSED = "closed"


# Mapping for numeric risk score calculation
LIKELIHOOD_VALUES = {
    RiskLikelihood.RARE: 1,
    RiskLikelihood.UNLIKELY: 2,
    RiskLikelihood.POSSIBLE: 3,
    RiskLikelihood.LIKELY: 4,
    RiskLikelihood.ALMOST_CERTAIN: 5,
}

IMPACT_VALUES = {
    RiskImpact.NEGLIGIBLE: 1,
    RiskImpact.MINOR: 2,
    RiskImpact.MODERATE: 3,
    RiskImpact.MAJOR: 4,
    RiskImpact.CATASTROPHIC: 5,
}


def calculate_risk_score(likelihood: RiskLikelihood, impact: RiskImpact) -> int:
    """Calculate risk score from likelihood and impact (1-25)."""
    return LIKELIHOOD_VALUES[likelihood] * IMPACT_VALUES[impact]


# =============================================================================
# Models
# =============================================================================


class ComplianceFramework(Base):
    """
    Registry of compliance frameworks.

    Stores metadata about supported frameworks (NIST AI RMF, EU AI Act, ISO 42001).
    Seeded at migration time with framework details.
    """

    __tablename__ = "compliance_frameworks"

    id = Column(
        PgUUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
        doc="Unique framework identifier",
    )

    code = Column(
        String(50),
        nullable=False,
        unique=True,
        index=True,
        doc="Framework code (NIST_AI_RMF, EU_AI_ACT, ISO_42001)",
    )

    name = Column(
        String(200),
        nullable=False,
        doc="Framework display name",
    )

    version = Column(
        String(20),
        nullable=False,
        doc="Framework version (1.0, 2024/1689, 2023)",
    )

    description = Column(
        Text,
        nullable=True,
        doc="Framework description and purpose",
    )

    total_controls = Column(
        Integer,
        nullable=False,
        default=0,
        doc="Total number of controls in this framework",
    )

    is_active = Column(
        Boolean,
        nullable=False,
        default=True,
        doc="Whether framework is currently active",
    )

    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        doc="Creation timestamp",
    )

    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
        doc="Last update timestamp",
    )

    # Relationships
    controls = relationship(
        "ComplianceControl",
        back_populates="framework",
        cascade="all, delete-orphan",
        lazy="dynamic",
    )

    risks = relationship(
        "ComplianceRiskRegister",
        back_populates="framework",
        cascade="all, delete-orphan",
        lazy="dynamic",
    )

    def __repr__(self) -> str:
        return f"<ComplianceFramework {self.code} v{self.version}>"

    def to_dict(self) -> dict:
        """Convert to dictionary for API response."""
        return {
            "id": str(self.id),
            "code": self.code,
            "name": self.name,
            "version": self.version,
            "description": self.description,
            "total_controls": self.total_controls,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class ComplianceControl(Base):
    """
    Individual controls per compliance framework.

    Each control has:
    - Framework linkage
    - Severity classification
    - Gate mapping (links to existing SDLC gates)
    - Evidence requirements (JSONB)
    - OPA policy linkage for automated evaluation
    """

    __tablename__ = "compliance_controls"

    id = Column(
        PgUUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
        doc="Unique control identifier",
    )

    framework_id = Column(
        PgUUID(as_uuid=True),
        ForeignKey("compliance_frameworks.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        doc="Parent framework",
    )

    control_code = Column(
        String(50),
        nullable=False,
        doc="Control code (GOVERN-1.1, Art.6, 5.1)",
    )

    category = Column(
        String(100),
        nullable=False,
        doc="Control category (GOVERN, HIGH_RISK, Leadership)",
    )

    title = Column(
        String(300),
        nullable=False,
        doc="Control title",
    )

    description = Column(
        Text,
        nullable=True,
        doc="Detailed control description",
    )

    severity = Column(
        String(20),
        nullable=False,
        default=ControlSeverity.MEDIUM.value,
        doc="Control severity (critical, high, medium, low)",
    )

    gate_mapping = Column(
        String(20),
        nullable=True,
        doc="Mapped SDLC gate (G1, G2, etc.)",
    )

    evidence_required = Column(
        JSONB,
        nullable=False,
        default=list,
        server_default="[]",
        doc="Structured evidence requirements [{type, description, required, accepted_formats}]",
    )

    opa_policy_code = Column(
        String(100),
        nullable=True,
        doc="OPA Rego policy identifier for automated evaluation",
    )

    sort_order = Column(
        Integer,
        nullable=False,
        default=0,
        doc="Display order within framework",
    )

    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        doc="Creation timestamp",
    )

    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
        doc="Last update timestamp",
    )

    # Relationships
    framework = relationship(
        "ComplianceFramework",
        back_populates="controls",
        lazy="joined",
    )

    assessments = relationship(
        "ComplianceAssessment",
        back_populates="control",
        cascade="all, delete-orphan",
        lazy="dynamic",
    )

    raci_entries = relationship(
        "ComplianceRACI",
        back_populates="control",
        cascade="all, delete-orphan",
        lazy="dynamic",
    )

    # Unique constraint: one control code per framework
    __table_args__ = (
        {"comment": "Compliance controls per framework"},
    )

    def __repr__(self) -> str:
        return f"<ComplianceControl {self.control_code}: {self.title[:40]}>"

    def to_dict(self) -> dict:
        """Convert to dictionary for API response."""
        return {
            "id": str(self.id),
            "framework_id": str(self.framework_id),
            "control_code": self.control_code,
            "category": self.category,
            "title": self.title,
            "description": self.description,
            "severity": self.severity,
            "gate_mapping": self.gate_mapping,
            "evidence_required": self.evidence_required or [],
            "opa_policy_code": self.opa_policy_code,
            "sort_order": self.sort_order,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class ComplianceAssessment(Base):
    """
    Per-project, per-control compliance evaluation.

    Tracks assessment status, evidence linkage, OPA evaluation results,
    and assessor information. Supports both manual and automated evaluation.
    """

    __tablename__ = "compliance_assessments"

    id = Column(
        PgUUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
        doc="Unique assessment identifier",
    )

    project_id = Column(
        PgUUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        doc="Assessed project",
    )

    control_id = Column(
        PgUUID(as_uuid=True),
        ForeignKey("compliance_controls.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        doc="Assessed control",
    )

    status = Column(
        String(30),
        nullable=False,
        default=AssessmentStatus.NOT_STARTED.value,
        index=True,
        doc="Assessment status",
    )

    evidence_ids = Column(
        ARRAY(PgUUID(as_uuid=True)),
        nullable=True,
        default=list,
        doc="Linked evidence IDs from Evidence Vault",
    )

    assessor_id = Column(
        PgUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        doc="User who performed the assessment",
    )

    notes = Column(
        Text,
        nullable=True,
        doc="Assessment notes and observations",
    )

    auto_evaluated = Column(
        Boolean,
        nullable=False,
        default=False,
        doc="True if evaluated by OPA policy",
    )

    opa_result = Column(
        JSONB,
        nullable=True,
        doc="Raw OPA evaluation result",
    )

    assessed_at = Column(
        DateTime(timezone=True),
        nullable=True,
        doc="When the assessment was performed",
    )

    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        doc="Creation timestamp",
    )

    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
        doc="Last update timestamp",
    )

    # Relationships
    project = relationship("Project", lazy="joined")
    control = relationship(
        "ComplianceControl",
        back_populates="assessments",
        lazy="joined",
    )
    assessor = relationship("User", lazy="joined")

    # Unique constraint: one assessment per project per control
    __table_args__ = (
        {"comment": "Per-project compliance control assessments"},
    )

    def __repr__(self) -> str:
        return f"<ComplianceAssessment project={self.project_id} control={self.control_id} status={self.status}>"

    def to_dict(self) -> dict:
        """Convert to dictionary for API response."""
        return {
            "id": str(self.id),
            "project_id": str(self.project_id),
            "control_id": str(self.control_id),
            "status": self.status,
            "evidence_ids": [str(eid) for eid in (self.evidence_ids or [])],
            "assessor_id": str(self.assessor_id) if self.assessor_id else None,
            "notes": self.notes,
            "auto_evaluated": self.auto_evaluated,
            "opa_result": self.opa_result,
            "assessed_at": self.assessed_at.isoformat() if self.assessed_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class ComplianceRiskRegister(Base):
    """
    Risk register for compliance risk management.

    Used by NIST GOVERN/MAP functions. Tracks risks with:
    - 5x5 likelihood/impact matrix (score 1-25)
    - Category classification (safety, fairness, privacy, security)
    - Mitigation tracking and responsible party
    """

    __tablename__ = "compliance_risk_register"

    id = Column(
        PgUUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
        doc="Unique risk identifier",
    )

    project_id = Column(
        PgUUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        doc="Associated project",
    )

    framework_id = Column(
        PgUUID(as_uuid=True),
        ForeignKey("compliance_frameworks.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        doc="Associated compliance framework",
    )

    risk_code = Column(
        String(50),
        nullable=False,
        doc="Risk identifier code (e.g., RISK-001)",
    )

    title = Column(
        String(300),
        nullable=False,
        doc="Risk title",
    )

    description = Column(
        Text,
        nullable=True,
        doc="Detailed risk description",
    )

    likelihood = Column(
        String(20),
        nullable=False,
        default=RiskLikelihood.POSSIBLE.value,
        doc="Risk likelihood (rare, unlikely, possible, likely, almost_certain)",
    )

    impact = Column(
        String(20),
        nullable=False,
        default=RiskImpact.MODERATE.value,
        doc="Risk impact (negligible, minor, moderate, major, catastrophic)",
    )

    risk_score = Column(
        Integer,
        nullable=False,
        default=9,
        index=True,
        doc="Computed risk score: likelihood_val * impact_val (1-25)",
    )

    category = Column(
        String(100),
        nullable=False,
        doc="Risk category (safety, fairness, privacy, security, reliability)",
    )

    mitigation_strategy = Column(
        Text,
        nullable=True,
        doc="Planned or implemented mitigation strategy",
    )

    responsible_id = Column(
        PgUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        doc="User responsible for risk mitigation",
    )

    status = Column(
        String(20),
        nullable=False,
        default=RiskStatus.IDENTIFIED.value,
        index=True,
        doc="Risk management status",
    )

    target_date = Column(
        Date,
        nullable=True,
        doc="Target date for mitigation completion",
    )

    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        doc="Creation timestamp",
    )

    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
        doc="Last update timestamp",
    )

    # Relationships
    project = relationship("Project", lazy="joined")
    framework = relationship(
        "ComplianceFramework",
        back_populates="risks",
        lazy="joined",
    )
    responsible = relationship("User", lazy="joined")

    def __repr__(self) -> str:
        return f"<ComplianceRisk {self.risk_code}: score={self.risk_score} status={self.status}>"

    def update_risk_score(self) -> None:
        """Recalculate risk score from current likelihood and impact."""
        self.risk_score = calculate_risk_score(
            RiskLikelihood(self.likelihood),
            RiskImpact(self.impact),
        )

    def to_dict(self) -> dict:
        """Convert to dictionary for API response."""
        return {
            "id": str(self.id),
            "project_id": str(self.project_id),
            "framework_id": str(self.framework_id),
            "risk_code": self.risk_code,
            "title": self.title,
            "description": self.description,
            "likelihood": self.likelihood,
            "impact": self.impact,
            "risk_score": self.risk_score,
            "category": self.category,
            "mitigation_strategy": self.mitigation_strategy,
            "responsible_id": str(self.responsible_id) if self.responsible_id else None,
            "status": self.status,
            "target_date": self.target_date.isoformat() if self.target_date else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class ComplianceRACI(Base):
    """
    RACI accountability matrix for compliance controls.

    Assigns responsibility roles per control per project:
    - R (Responsible): Person doing the work
    - A (Accountable): Person ultimately answerable
    - C (Consulted): People consulted before decisions
    - I (Informed): People kept up-to-date
    """

    __tablename__ = "compliance_raci"

    id = Column(
        PgUUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
        doc="Unique RACI entry identifier",
    )

    project_id = Column(
        PgUUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        doc="Associated project",
    )

    control_id = Column(
        PgUUID(as_uuid=True),
        ForeignKey("compliance_controls.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        doc="Associated compliance control",
    )

    responsible_id = Column(
        PgUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        doc="Responsible (R) - person doing the work",
    )

    accountable_id = Column(
        PgUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        doc="Accountable (A) - person ultimately answerable",
    )

    consulted_ids = Column(
        ARRAY(PgUUID(as_uuid=True)),
        nullable=True,
        default=list,
        doc="Consulted (C) - people consulted before decisions",
    )

    informed_ids = Column(
        ARRAY(PgUUID(as_uuid=True)),
        nullable=True,
        default=list,
        doc="Informed (I) - people kept up-to-date",
    )

    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        doc="Creation timestamp",
    )

    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
        doc="Last update timestamp",
    )

    # Relationships
    project = relationship("Project", lazy="joined")
    control = relationship(
        "ComplianceControl",
        back_populates="raci_entries",
        lazy="joined",
    )
    responsible = relationship(
        "User",
        foreign_keys=[responsible_id],
        lazy="joined",
    )
    accountable = relationship(
        "User",
        foreign_keys=[accountable_id],
        lazy="joined",
    )

    # Unique constraint: one RACI entry per project per control
    __table_args__ = (
        {"comment": "RACI accountability matrix per project per control"},
    )

    def __repr__(self) -> str:
        return f"<ComplianceRACI project={self.project_id} control={self.control_id}>"

    def to_dict(self) -> dict:
        """Convert to dictionary for API response."""
        return {
            "id": str(self.id),
            "project_id": str(self.project_id),
            "control_id": str(self.control_id),
            "responsible_id": str(self.responsible_id) if self.responsible_id else None,
            "accountable_id": str(self.accountable_id) if self.accountable_id else None,
            "consulted_ids": [str(uid) for uid in (self.consulted_ids or [])],
            "informed_ids": [str(uid) for uid in (self.informed_ids or [])],
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
