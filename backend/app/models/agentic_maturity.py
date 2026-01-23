"""
=========================================================================
Agentic Maturity Assessment Model - SDLC Framework 5.2.0
SDLC Orchestrator - Sprint 104 (Agentic Maturity L0-L3)

Version: 1.0.0
Date: January 23, 2026
Status: ACTIVE - Sprint 104 Implementation
Authority: Backend Lead + CTO Approved
Reference: docs/04-build/02-Sprint-Plans/SPRINT-104-DESIGN.md

Purpose:
- Store maturity assessment history per project
- Track level progression over time
- Enable compliance reporting

Maturity Levels:
  L0: MANUAL (0-20)
  L1: ASSISTANT (21-50)
  L2: ORCHESTRATED (51-80)
  L3: AUTONOMOUS (81-100)

Zero Mock Policy: Production-ready SQLAlchemy model
=========================================================================
"""

from datetime import datetime
from uuid import uuid4

from sqlalchemy import Column, DateTime, ForeignKey, Integer, JSON, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.db.base import Base


class AgenticMaturityAssessment(Base):
    """
    Agentic Maturity Assessment record.

    Stores the result of a maturity assessment for a project,
    including score, level, enabled features, and recommendations.

    Attributes:
        id: Unique assessment ID
        project_id: Project being assessed
        level: Maturity level (L0/L1/L2/L3)
        score: Maturity score (0-100)
        enabled_features: List of enabled feature names
        disabled_features: List of disabled feature names
        recommendations: List of improvement recommendations
        factor_details: Detailed scoring breakdown
        assessed_at: When assessment was performed

    Example:
        assessment = AgenticMaturityAssessment(
            project_id=project.id,
            level="L2",
            score=65,
            enabled_features=["Planning Sub-agent", "Evidence Vault"],
            disabled_features=["GitHub Check Runs"],
            recommendations=["Enable GitHub Check Runs (+10 points)"],
            factor_details=[{"name": "Planning Sub-agent", "points": 30, "enabled": True}],
        )
    """

    __tablename__ = "maturity_assessments"

    # Primary Key
    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )

    # Project Reference
    project_id = Column(
        UUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Assessment Results
    level = Column(
        String(10),
        nullable=False,
        comment="Maturity level: L0, L1, L2, L3",
    )

    score = Column(
        Integer,
        nullable=False,
        comment="Maturity score: 0-100",
    )

    # Feature Analysis
    enabled_features = Column(
        JSON,
        nullable=False,
        default=list,
        comment="List of enabled feature names",
    )

    disabled_features = Column(
        JSON,
        nullable=False,
        default=list,
        comment="List of disabled feature names",
    )

    recommendations = Column(
        JSON,
        nullable=False,
        default=list,
        comment="List of improvement recommendations",
    )

    factor_details = Column(
        JSON,
        nullable=True,
        comment="Detailed factor scoring breakdown",
    )

    # Timestamps
    assessed_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.utcnow,
        index=True,
        comment="When assessment was performed",
    )

    # Relationships
    project = relationship(
        "Project",
        back_populates="maturity_assessments",
    )

    def __repr__(self) -> str:
        return (
            f"<AgenticMaturityAssessment("
            f"project_id={self.project_id}, "
            f"level={self.level}, "
            f"score={self.score}"
            f")>"
        )

    @property
    def level_name(self) -> str:
        """Get human-readable level name."""
        return {
            "L0": "Manual",
            "L1": "Assistant",
            "L2": "Orchestrated",
            "L3": "Autonomous",
        }.get(self.level, "Unknown")

    @property
    def is_autonomous(self) -> bool:
        """Check if project is at autonomous level."""
        return self.level == "L3"

    @property
    def is_orchestrated_or_higher(self) -> bool:
        """Check if project is at orchestrated level or higher."""
        return self.level in ("L2", "L3")
