"""
=========================================================================
NIST AI RMF MANAGE Models
SDLC Orchestrator - Sprint 158 (Phase 3: COMPLIANCE)

Version: 1.0.0
Date: April 21, 2026
Status: ACTIVE
Authority: CTO Approved
Framework: SDLC 6.0.5
Reference: ADR-051, NIST AI RMF 1.0 Section MANAGE

Purpose:
Models for NIST MANAGE (risk response & incident management) function:
- manage_risk_responses: Risk response plans linked to risk register
- manage_incidents: AI system incidents and post-deployment events

Tables:
- manage_risk_responses: Response planning, resource allocation, deactivation criteria
- manage_incidents: Incident tracking with severity, type, resolution

Zero Mock Policy: Production-ready implementation
=========================================================================
"""

from datetime import date, datetime
from enum import Enum as PyEnum
from typing import Any, Dict, List, Optional
from uuid import uuid4

from sqlalchemy import (
    Boolean,
    Column,
    Date,
    DateTime,
    ForeignKey,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID as PgUUID
from sqlalchemy.orm import relationship

from app.db.base_class import Base


# =============================================================================
# Enums
# =============================================================================


class ResponseType(str, PyEnum):
    """Risk response type per ISO 31000."""

    MITIGATE = "mitigate"
    ACCEPT = "accept"
    TRANSFER = "transfer"
    AVOID = "avoid"


class ResponseStatus(str, PyEnum):
    """Risk response status."""

    PLANNED = "planned"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    DEFERRED = "deferred"


class ResponsePriority(str, PyEnum):
    """Risk response priority."""

    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class IncidentSeverity(str, PyEnum):
    """Incident severity level."""

    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class IncidentType(str, PyEnum):
    """AI system incident type classification."""

    PERFORMANCE_DEGRADATION = "performance_degradation"
    BIAS_DETECTED = "bias_detected"
    SECURITY_BREACH = "security_breach"
    AVAILABILITY = "availability"
    DATA_QUALITY = "data_quality"
    COMPLIANCE_VIOLATION = "compliance_violation"


class IncidentStatus(str, PyEnum):
    """Incident lifecycle status."""

    OPEN = "open"
    INVESTIGATING = "investigating"
    MITIGATING = "mitigating"
    RESOLVED = "resolved"
    CLOSED = "closed"


# =============================================================================
# Models
# =============================================================================


class ManageRiskResponse(Base):
    """
    Risk response plans for NIST MANAGE function.

    Links to compliance_risk_register entries and tracks response planning,
    resource allocation, and deactivation criteria. Supports:
    - MANAGE-1.1: Risk Response Planning
    - MANAGE-2.1: Resource Allocation
    - MANAGE-2.4: System Deactivation Criteria
    """

    __tablename__ = "manage_risk_responses"

    id = Column(
        PgUUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
        doc="Unique risk response identifier",
    )

    project_id = Column(
        PgUUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        doc="Associated project",
    )

    risk_id = Column(
        PgUUID(as_uuid=True),
        ForeignKey("compliance_risk_register.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        doc="Risk being responded to",
    )

    response_type = Column(
        String(50),
        nullable=False,
        doc="Response type: mitigate, accept, transfer, avoid",
    )

    description = Column(
        Text,
        nullable=False,
        doc="Response plan description",
    )

    assigned_to = Column(
        String(200),
        nullable=True,
        doc="Person or team responsible for executing the response",
    )

    priority = Column(
        String(20),
        nullable=False,
        default=ResponsePriority.MEDIUM.value,
        doc="Response priority: critical, high, medium, low",
    )

    status = Column(
        String(50),
        nullable=False,
        default=ResponseStatus.PLANNED.value,
        doc="Response status: planned, in_progress, completed, deferred",
    )

    due_date = Column(
        Date,
        nullable=True,
        doc="Target completion date",
    )

    resources_allocated = Column(
        JSONB,
        nullable=False,
        default=list,
        server_default="[]",
        doc="[{type, description, budget}]",
    )

    deactivation_criteria = Column(
        JSONB,
        nullable=True,
        doc="MANAGE-2.4: {conditions: [], threshold, action}",
    )

    notes = Column(
        Text,
        nullable=True,
        doc="Additional notes",
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
    risk = relationship("ComplianceRiskRegister", lazy="joined")

    __table_args__ = (
        {"comment": "Risk response plans for NIST MANAGE function"},
    )

    def __repr__(self) -> str:
        return f"<ManageRiskResponse {self.response_type} status={self.status} priority={self.priority}>"

    def to_dict(self) -> dict:
        """Convert to dictionary for API response."""
        return {
            "id": str(self.id),
            "project_id": str(self.project_id),
            "risk_id": str(self.risk_id),
            "response_type": self.response_type,
            "description": self.description,
            "assigned_to": self.assigned_to,
            "priority": self.priority,
            "status": self.status,
            "due_date": self.due_date.isoformat() if self.due_date else None,
            "resources_allocated": self.resources_allocated or [],
            "deactivation_criteria": self.deactivation_criteria,
            "notes": self.notes,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class ManageIncident(Base):
    """
    AI system incidents for NIST MANAGE function.

    Tracks incidents affecting AI systems with severity, type,
    resolution tracking, and root cause analysis. Supports:
    - MANAGE-3.1: Third-Party Monitoring
    - MANAGE-4.1: Post-Deployment Monitoring
    """

    __tablename__ = "manage_incidents"

    id = Column(
        PgUUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
        doc="Unique incident identifier",
    )

    project_id = Column(
        PgUUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        doc="Associated project",
    )

    ai_system_id = Column(
        PgUUID(as_uuid=True),
        ForeignKey("ai_systems.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        doc="Affected AI system",
    )

    risk_id = Column(
        PgUUID(as_uuid=True),
        ForeignKey("compliance_risk_register.id", ondelete="SET NULL"),
        nullable=True,
        doc="Optional link to risk that materialized",
    )

    title = Column(
        String(300),
        nullable=False,
        doc="Incident title",
    )

    description = Column(
        Text,
        nullable=True,
        doc="Detailed incident description",
    )

    severity = Column(
        String(20),
        nullable=False,
        doc="Severity: critical, high, medium, low",
    )

    incident_type = Column(
        String(50),
        nullable=False,
        doc="Type: performance_degradation, bias_detected, security_breach, availability, data_quality, compliance_violation",
    )

    status = Column(
        String(50),
        nullable=False,
        default=IncidentStatus.OPEN.value,
        doc="Status: open, investigating, mitigating, resolved, closed",
    )

    reported_by = Column(
        String(200),
        nullable=True,
        doc="Who reported the incident",
    )

    assigned_to = Column(
        String(200),
        nullable=True,
        doc="Who is assigned to resolve the incident",
    )

    resolution = Column(
        Text,
        nullable=True,
        doc="How the incident was resolved",
    )

    root_cause = Column(
        Text,
        nullable=True,
        doc="Root cause analysis",
    )

    occurred_at = Column(
        DateTime(timezone=True),
        nullable=False,
        doc="When the incident occurred",
    )

    resolved_at = Column(
        DateTime(timezone=True),
        nullable=True,
        doc="When the incident was resolved",
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
    ai_system = relationship("AISystem", lazy="joined")
    risk = relationship("ComplianceRiskRegister", lazy="joined")

    __table_args__ = (
        {"comment": "AI system incidents for NIST MANAGE function"},
    )

    def __repr__(self) -> str:
        return f"<ManageIncident {self.title} severity={self.severity} status={self.status}>"

    def to_dict(self) -> dict:
        """Convert to dictionary for API response."""
        return {
            "id": str(self.id),
            "project_id": str(self.project_id),
            "ai_system_id": str(self.ai_system_id),
            "risk_id": str(self.risk_id) if self.risk_id else None,
            "title": self.title,
            "description": self.description,
            "severity": self.severity,
            "incident_type": self.incident_type,
            "status": self.status,
            "reported_by": self.reported_by,
            "assigned_to": self.assigned_to,
            "resolution": self.resolution,
            "root_cause": self.root_cause,
            "occurred_at": self.occurred_at.isoformat() if self.occurred_at else None,
            "resolved_at": self.resolved_at.isoformat() if self.resolved_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
