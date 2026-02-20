# Sprint 114: Dogfooding Metrics Specification

**Version**: 1.0.0
**Date**: January 28, 2026
**Status**: DRAFT - Awaiting CTO Approval
**Sprint**: 114 - Dogfooding (WARNING Mode)
**Dependencies**: Sprint 113 Complete (Auto-Generation + Kill Switch UI)
**Framework**: SDLC 6.1.0

---

## Executive Summary

Sprint 114 enables WARNING mode on the SDLC Orchestrator repository as the first real-world test of the Governance System. This document specifies the metrics collection system, dashboard design, and decision criteria for proceeding to Sprint 115 (Soft Enforcement).

**Goal**: Establish baseline metrics and validate governance system before enforcement.

---

## 1. Metrics Collection System

### 1.1 Metrics Categories

```yaml
# backend/app/config/dogfooding_metrics.yaml

dogfooding_metrics:
  version: "1.0.0"
  collection_period: "Sprint 114 (Feb 3-7, 2026)"

  categories:
    developer_friction:
      description: "Time and effort required to comply with governance"
      priority: P0

    governance_accuracy:
      description: "How well governance identifies real issues"
      priority: P0

    vibecoding_index:
      description: "Code quality signals from Vibecoding Index"
      priority: P1

    system_performance:
      description: "API latency and reliability"
      priority: P1

    user_feedback:
      description: "Developer sentiment and suggestions"
      priority: P2
```

### 1.2 Developer Friction Metrics

| Metric ID | Metric Name | Formula | Target | Collection Method |
|-----------|-------------|---------|--------|-------------------|
| DF-001 | Time to First Governance Pass | `first_pass_timestamp - pr_created_timestamp` | < 10 min | API timestamp diff |
| DF-002 | Compliance Attempt Count | `count(governance_evaluations) per PR` | < 2 attempts | Database count |
| DF-003 | Auto-Generation Usage Rate | `auto_generated_artifacts / total_artifacts` | > 80% | API tracking |
| DF-004 | Manual Override Count | `count(manual_overrides) per day` | < 5/day | Audit log |
| DF-005 | Documentation Time | `intent_submit_time - intent_start_time` | < 5 min | Frontend tracking |

### 1.3 Governance Accuracy Metrics

| Metric ID | Metric Name | Formula | Target | Collection Method |
|-----------|-------------|---------|--------|-------------------|
| GA-001 | False Positive Rate | `false_positives / total_rejections` | < 20% | Manual review |
| GA-002 | False Negative Rate | `missed_issues / total_issues` | < 10% | Post-merge audit |
| GA-003 | CEO Agreement Rate | `ceo_agrees / total_auto_decisions` | > 95% | CEO review log |
| GA-004 | Precision | `true_positives / (true_positives + false_positives)` | > 80% | Classification |
| GA-005 | Recall | `true_positives / (true_positives + false_negatives)` | > 90% | Classification |

### 1.4 Vibecoding Index Distribution

| Metric ID | Metric Name | Formula | Target | Collection Method |
|-----------|-------------|---------|--------|-------------------|
| VI-001 | Average Index | `sum(vibecoding_index) / count(prs)` | < 40 | Database aggregate |
| VI-002 | Green Zone % | `count(index < 30) / total_prs` | > 50% | Database count |
| VI-003 | Yellow Zone % | `count(30 <= index < 60) / total_prs` | < 35% | Database count |
| VI-004 | Orange Zone % | `count(60 <= index < 80) / total_prs` | < 12% | Database count |
| VI-005 | Red Zone % | `count(index >= 80) / total_prs` | < 3% | Database count |

### 1.5 System Performance Metrics

| Metric ID | Metric Name | Formula | Target | Collection Method |
|-----------|-------------|---------|--------|-------------------|
| SP-001 | API Latency P50 | `percentile(latency, 50)` | < 50ms | Prometheus |
| SP-002 | API Latency P95 | `percentile(latency, 95)` | < 100ms | Prometheus |
| SP-003 | API Latency P99 | `percentile(latency, 99)` | < 200ms | Prometheus |
| SP-004 | Error Rate | `errors / total_requests` | < 1% | Prometheus |
| SP-005 | Uptime | `uptime_seconds / total_seconds` | > 99.9% | Health check |

---

## 2. Database Schema for Metrics

### 2.1 New Tables

```sql
-- backend/alembic/versions/sprint_114_dogfooding_metrics.py

-- Table 1: Daily Metrics Aggregation
CREATE TABLE governance_daily_metrics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    date DATE NOT NULL UNIQUE,

    -- Developer Friction
    avg_time_to_pass_seconds DECIMAL(10,2),
    avg_compliance_attempts DECIMAL(4,2),
    auto_generation_usage_rate DECIMAL(5,4),
    manual_override_count INTEGER DEFAULT 0,
    avg_documentation_time_seconds DECIMAL(10,2),

    -- Governance Accuracy
    total_evaluations INTEGER DEFAULT 0,
    true_positives INTEGER DEFAULT 0,
    true_negatives INTEGER DEFAULT 0,
    false_positives INTEGER DEFAULT 0,
    false_negatives INTEGER DEFAULT 0,
    ceo_agreements INTEGER DEFAULT 0,
    ceo_overrides INTEGER DEFAULT 0,

    -- Vibecoding Index
    avg_vibecoding_index DECIMAL(5,2),
    green_zone_count INTEGER DEFAULT 0,
    yellow_zone_count INTEGER DEFAULT 0,
    orange_zone_count INTEGER DEFAULT 0,
    red_zone_count INTEGER DEFAULT 0,

    -- System Performance
    avg_latency_ms DECIMAL(10,2),
    p95_latency_ms DECIMAL(10,2),
    p99_latency_ms DECIMAL(10,2),
    error_count INTEGER DEFAULT 0,
    total_requests INTEGER DEFAULT 0,

    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Table 2: PR-Level Metrics
CREATE TABLE governance_pr_metrics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    pr_number INTEGER NOT NULL,
    repo_id UUID NOT NULL REFERENCES repositories(id),
    project_id UUID NOT NULL REFERENCES projects(id),

    -- Timestamps
    pr_created_at TIMESTAMP WITH TIME ZONE NOT NULL,
    first_evaluation_at TIMESTAMP WITH TIME ZONE,
    first_pass_at TIMESTAMP WITH TIME ZONE,
    merged_at TIMESTAMP WITH TIME ZONE,

    -- Developer Friction
    time_to_first_pass_seconds INTEGER,
    evaluation_count INTEGER DEFAULT 0,
    auto_generated_intent BOOLEAN DEFAULT FALSE,
    auto_generated_ownership BOOLEAN DEFAULT FALSE,
    auto_generated_context BOOLEAN DEFAULT FALSE,
    auto_generated_attestation BOOLEAN DEFAULT FALSE,

    -- Governance Result
    vibecoding_index DECIMAL(5,2),
    vibecoding_zone VARCHAR(10), -- green, yellow, orange, red
    signals JSONB, -- { arch_smell: 25, ai_dependency: 30, ... }
    violations JSONB, -- [{ type: "missing_intent", severity: "error" }]
    final_status VARCHAR(20), -- passed, blocked, overridden

    -- Review Classification (filled during manual review)
    classification VARCHAR(20), -- true_positive, false_positive, true_negative, false_negative
    ceo_agreed BOOLEAN,
    classification_notes TEXT,

    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Table 3: User Feedback
CREATE TABLE governance_feedback (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id),
    pr_id UUID REFERENCES governance_pr_metrics(id),

    -- Feedback Type
    feedback_type VARCHAR(50) NOT NULL, -- complaint, suggestion, praise, bug_report

    -- NPS Score (1-10)
    nps_score INTEGER CHECK (nps_score BETWEEN 1 AND 10),

    -- Detailed Feedback
    friction_rating INTEGER CHECK (friction_rating BETWEEN 1 AND 5),
    accuracy_rating INTEGER CHECK (accuracy_rating BETWEEN 1 AND 5),
    usefulness_rating INTEGER CHECK (usefulness_rating BETWEEN 1 AND 5),
    comments TEXT,

    -- Categorization
    category VARCHAR(50), -- auto_generation, vibecoding_index, kill_switch, documentation

    -- Status
    status VARCHAR(20) DEFAULT 'new', -- new, acknowledged, addressed, closed
    response TEXT,

    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_daily_metrics_date ON governance_daily_metrics(date);
CREATE INDEX idx_pr_metrics_repo ON governance_pr_metrics(repo_id, pr_number);
CREATE INDEX idx_pr_metrics_zone ON governance_pr_metrics(vibecoding_zone);
CREATE INDEX idx_pr_metrics_status ON governance_pr_metrics(final_status);
CREATE INDEX idx_feedback_type ON governance_feedback(feedback_type);
CREATE INDEX idx_feedback_status ON governance_feedback(status);
```

### 2.2 SQLAlchemy Models

```python
# backend/app/models/dogfooding_metrics.py

from datetime import date, datetime
from decimal import Decimal
from typing import Optional
from uuid import UUID

from sqlalchemy import Column, Date, ForeignKey, Integer, Numeric, String, Boolean, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID as PG_UUID
from sqlalchemy.orm import relationship

from app.database import Base


class GovernanceDailyMetrics(Base):
    """Daily aggregated metrics for dogfooding period."""

    __tablename__ = "governance_daily_metrics"

    id: UUID = Column(PG_UUID(as_uuid=True), primary_key=True, server_default="gen_random_uuid()")
    date: date = Column(Date, nullable=False, unique=True)

    # Developer Friction
    avg_time_to_pass_seconds: Decimal = Column(Numeric(10, 2))
    avg_compliance_attempts: Decimal = Column(Numeric(4, 2))
    auto_generation_usage_rate: Decimal = Column(Numeric(5, 4))
    manual_override_count: int = Column(Integer, default=0)
    avg_documentation_time_seconds: Decimal = Column(Numeric(10, 2))

    # Governance Accuracy
    total_evaluations: int = Column(Integer, default=0)
    true_positives: int = Column(Integer, default=0)
    true_negatives: int = Column(Integer, default=0)
    false_positives: int = Column(Integer, default=0)
    false_negatives: int = Column(Integer, default=0)
    ceo_agreements: int = Column(Integer, default=0)
    ceo_overrides: int = Column(Integer, default=0)

    # Vibecoding Index
    avg_vibecoding_index: Decimal = Column(Numeric(5, 2))
    green_zone_count: int = Column(Integer, default=0)
    yellow_zone_count: int = Column(Integer, default=0)
    orange_zone_count: int = Column(Integer, default=0)
    red_zone_count: int = Column(Integer, default=0)

    # System Performance
    avg_latency_ms: Decimal = Column(Numeric(10, 2))
    p95_latency_ms: Decimal = Column(Numeric(10, 2))
    p99_latency_ms: Decimal = Column(Numeric(10, 2))
    error_count: int = Column(Integer, default=0)
    total_requests: int = Column(Integer, default=0)

    @property
    def false_positive_rate(self) -> float:
        """Calculate false positive rate."""
        total_rejections = self.true_positives + self.false_positives
        if total_rejections == 0:
            return 0.0
        return float(self.false_positives) / total_rejections

    @property
    def ceo_agreement_rate(self) -> float:
        """Calculate CEO agreement rate."""
        total_decisions = self.ceo_agreements + self.ceo_overrides
        if total_decisions == 0:
            return 1.0
        return float(self.ceo_agreements) / total_decisions


class GovernancePRMetrics(Base):
    """Per-PR metrics for detailed analysis."""

    __tablename__ = "governance_pr_metrics"

    id: UUID = Column(PG_UUID(as_uuid=True), primary_key=True, server_default="gen_random_uuid()")
    pr_number: int = Column(Integer, nullable=False)
    repo_id: UUID = Column(PG_UUID(as_uuid=True), ForeignKey("repositories.id"), nullable=False)
    project_id: UUID = Column(PG_UUID(as_uuid=True), ForeignKey("projects.id"), nullable=False)

    # Timestamps
    pr_created_at: datetime = Column(DateTime(timezone=True), nullable=False)
    first_evaluation_at: Optional[datetime] = Column(DateTime(timezone=True))
    first_pass_at: Optional[datetime] = Column(DateTime(timezone=True))
    merged_at: Optional[datetime] = Column(DateTime(timezone=True))

    # Developer Friction
    time_to_first_pass_seconds: Optional[int] = Column(Integer)
    evaluation_count: int = Column(Integer, default=0)
    auto_generated_intent: bool = Column(Boolean, default=False)
    auto_generated_ownership: bool = Column(Boolean, default=False)
    auto_generated_context: bool = Column(Boolean, default=False)
    auto_generated_attestation: bool = Column(Boolean, default=False)

    # Governance Result
    vibecoding_index: Decimal = Column(Numeric(5, 2))
    vibecoding_zone: str = Column(String(10))
    signals: dict = Column(JSONB)
    violations: list = Column(JSONB)
    final_status: str = Column(String(20))

    # Review Classification
    classification: Optional[str] = Column(String(20))
    ceo_agreed: Optional[bool] = Column(Boolean)
    classification_notes: Optional[str] = Column(Text)

    @property
    def auto_generation_count(self) -> int:
        """Count of auto-generated artifacts."""
        return sum([
            self.auto_generated_intent or False,
            self.auto_generated_ownership or False,
            self.auto_generated_context or False,
            self.auto_generated_attestation or False,
        ])


class GovernanceFeedback(Base):
    """User feedback during dogfooding."""

    __tablename__ = "governance_feedback"

    id: UUID = Column(PG_UUID(as_uuid=True), primary_key=True, server_default="gen_random_uuid()")
    user_id: UUID = Column(PG_UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    pr_id: Optional[UUID] = Column(PG_UUID(as_uuid=True), ForeignKey("governance_pr_metrics.id"))

    # Feedback Type
    feedback_type: str = Column(String(50), nullable=False)

    # NPS Score
    nps_score: Optional[int] = Column(Integer)

    # Detailed Ratings
    friction_rating: Optional[int] = Column(Integer)
    accuracy_rating: Optional[int] = Column(Integer)
    usefulness_rating: Optional[int] = Column(Integer)
    comments: Optional[str] = Column(Text)

    # Categorization
    category: Optional[str] = Column(String(50))

    # Status
    status: str = Column(String(20), default="new")
    response: Optional[str] = Column(Text)
```

---

## 3. Metrics Collection Service

### 3.1 Service Implementation

```python
# backend/app/services/governance/dogfooding_metrics_service.py

from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import Optional
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.dogfooding_metrics import (
    GovernanceDailyMetrics,
    GovernancePRMetrics,
    GovernanceFeedback,
)
from app.models.governance import GovernanceSubmission, GovernanceEvaluation


class DogfoodingMetricsService:
    """
    Collect and aggregate metrics during dogfooding period.

    Sprint 114: WARNING mode metrics collection.
    """

    def __init__(self, db: AsyncSession):
        self.db = db

    async def record_pr_evaluation(
        self,
        pr_number: int,
        repo_id: UUID,
        project_id: UUID,
        evaluation: GovernanceEvaluation,
        auto_generated: dict[str, bool],
    ) -> GovernancePRMetrics:
        """
        Record metrics for a PR evaluation.

        Called after each governance evaluation.
        """
        # Check if PR metrics exist
        existing = await self.db.execute(
            select(GovernancePRMetrics).where(
                GovernancePRMetrics.pr_number == pr_number,
                GovernancePRMetrics.repo_id == repo_id,
            )
        )
        pr_metrics = existing.scalar_one_or_none()

        if pr_metrics:
            # Update existing
            pr_metrics.evaluation_count += 1

            if evaluation.passed and pr_metrics.first_pass_at is None:
                pr_metrics.first_pass_at = datetime.utcnow()
                pr_metrics.time_to_first_pass_seconds = int(
                    (pr_metrics.first_pass_at - pr_metrics.pr_created_at).total_seconds()
                )
        else:
            # Create new
            pr_metrics = GovernancePRMetrics(
                pr_number=pr_number,
                repo_id=repo_id,
                project_id=project_id,
                pr_created_at=datetime.utcnow(),  # Will be updated from GitHub
                first_evaluation_at=datetime.utcnow(),
                evaluation_count=1,
                auto_generated_intent=auto_generated.get("intent", False),
                auto_generated_ownership=auto_generated.get("ownership", False),
                auto_generated_context=auto_generated.get("context", False),
                auto_generated_attestation=auto_generated.get("attestation", False),
            )
            self.db.add(pr_metrics)

        # Update vibecoding data
        pr_metrics.vibecoding_index = Decimal(str(evaluation.vibecoding_index))
        pr_metrics.vibecoding_zone = self._get_zone(evaluation.vibecoding_index)
        pr_metrics.signals = evaluation.signals
        pr_metrics.violations = evaluation.violations
        pr_metrics.final_status = "passed" if evaluation.passed else "blocked"

        await self.db.commit()
        return pr_metrics

    async def aggregate_daily_metrics(self, target_date: date) -> GovernanceDailyMetrics:
        """
        Aggregate metrics for a specific day.

        Run daily at midnight or on-demand.
        """
        # Check if already exists
        existing = await self.db.execute(
            select(GovernanceDailyMetrics).where(
                GovernanceDailyMetrics.date == target_date
            )
        )
        daily = existing.scalar_one_or_none()

        if not daily:
            daily = GovernanceDailyMetrics(date=target_date)
            self.db.add(daily)

        # Get PR metrics for the day
        start = datetime.combine(target_date, datetime.min.time())
        end = datetime.combine(target_date + timedelta(days=1), datetime.min.time())

        pr_metrics = await self.db.execute(
            select(GovernancePRMetrics).where(
                GovernancePRMetrics.first_evaluation_at >= start,
                GovernancePRMetrics.first_evaluation_at < end,
            )
        )
        prs = pr_metrics.scalars().all()

        if not prs:
            return daily

        # Developer Friction
        times_to_pass = [p.time_to_first_pass_seconds for p in prs if p.time_to_first_pass_seconds]
        daily.avg_time_to_pass_seconds = (
            Decimal(str(sum(times_to_pass) / len(times_to_pass))) if times_to_pass else None
        )
        daily.avg_compliance_attempts = Decimal(
            str(sum(p.evaluation_count for p in prs) / len(prs))
        )

        auto_gen_count = sum(p.auto_generation_count for p in prs)
        total_artifacts = len(prs) * 4  # 4 artifact types
        daily.auto_generation_usage_rate = Decimal(str(auto_gen_count / total_artifacts))

        # Vibecoding Index
        indices = [float(p.vibecoding_index) for p in prs if p.vibecoding_index]
        daily.avg_vibecoding_index = Decimal(str(sum(indices) / len(indices))) if indices else None

        daily.green_zone_count = len([p for p in prs if p.vibecoding_zone == "green"])
        daily.yellow_zone_count = len([p for p in prs if p.vibecoding_zone == "yellow"])
        daily.orange_zone_count = len([p for p in prs if p.vibecoding_zone == "orange"])
        daily.red_zone_count = len([p for p in prs if p.vibecoding_zone == "red"])

        # Governance Accuracy (requires manual classification)
        daily.total_evaluations = len(prs)
        daily.true_positives = len([p for p in prs if p.classification == "true_positive"])
        daily.true_negatives = len([p for p in prs if p.classification == "true_negative"])
        daily.false_positives = len([p for p in prs if p.classification == "false_positive"])
        daily.false_negatives = len([p for p in prs if p.classification == "false_negative"])
        daily.ceo_agreements = len([p for p in prs if p.ceo_agreed is True])
        daily.ceo_overrides = len([p for p in prs if p.ceo_agreed is False])

        await self.db.commit()
        return daily

    async def get_dogfooding_summary(
        self,
        start_date: date,
        end_date: date,
    ) -> dict:
        """
        Get summary metrics for dogfooding period.

        Used by Go/No-Go decision dashboard.
        """
        daily_metrics = await self.db.execute(
            select(GovernanceDailyMetrics).where(
                GovernanceDailyMetrics.date >= start_date,
                GovernanceDailyMetrics.date <= end_date,
            ).order_by(GovernanceDailyMetrics.date)
        )
        days = daily_metrics.scalars().all()

        if not days:
            return {"status": "no_data", "days_collected": 0}

        # Calculate overall metrics
        total_evaluations = sum(d.total_evaluations for d in days)
        total_true_positives = sum(d.true_positives for d in days)
        total_false_positives = sum(d.false_positives for d in days)
        total_ceo_agreements = sum(d.ceo_agreements for d in days)
        total_ceo_overrides = sum(d.ceo_overrides for d in days)

        # Calculate rates
        false_positive_rate = (
            total_false_positives / (total_true_positives + total_false_positives)
            if (total_true_positives + total_false_positives) > 0 else 0
        )
        ceo_agreement_rate = (
            total_ceo_agreements / (total_ceo_agreements + total_ceo_overrides)
            if (total_ceo_agreements + total_ceo_overrides) > 0 else 1.0
        )

        # Calculate averages
        avg_time_to_pass = sum(
            float(d.avg_time_to_pass_seconds or 0) for d in days
        ) / len(days)
        avg_compliance_attempts = sum(
            float(d.avg_compliance_attempts or 0) for d in days
        ) / len(days)
        auto_gen_usage = sum(
            float(d.auto_generation_usage_rate or 0) for d in days
        ) / len(days)
        avg_vibecoding_index = sum(
            float(d.avg_vibecoding_index or 0) for d in days
        ) / len(days)

        # Zone distribution
        total_green = sum(d.green_zone_count for d in days)
        total_yellow = sum(d.yellow_zone_count for d in days)
        total_orange = sum(d.orange_zone_count for d in days)
        total_red = sum(d.red_zone_count for d in days)
        total_prs = total_green + total_yellow + total_orange + total_red

        return {
            "status": "data_available",
            "days_collected": len(days),
            "period": {
                "start": str(start_date),
                "end": str(end_date),
            },
            "developer_friction": {
                "avg_time_to_pass_seconds": avg_time_to_pass,
                "avg_time_to_pass_minutes": avg_time_to_pass / 60,
                "avg_compliance_attempts": avg_compliance_attempts,
                "auto_generation_usage_rate": auto_gen_usage,
                "target_met": avg_time_to_pass < 600,  # < 10 minutes
            },
            "governance_accuracy": {
                "total_evaluations": total_evaluations,
                "false_positive_rate": false_positive_rate,
                "ceo_agreement_rate": ceo_agreement_rate,
                "target_met": false_positive_rate < 0.20,  # < 20%
            },
            "vibecoding_index": {
                "average": avg_vibecoding_index,
                "distribution": {
                    "green": total_green,
                    "green_pct": (total_green / total_prs * 100) if total_prs else 0,
                    "yellow": total_yellow,
                    "yellow_pct": (total_yellow / total_prs * 100) if total_prs else 0,
                    "orange": total_orange,
                    "orange_pct": (total_orange / total_prs * 100) if total_prs else 0,
                    "red": total_red,
                    "red_pct": (total_red / total_prs * 100) if total_prs else 0,
                },
                "target_met": avg_vibecoding_index < 40,
            },
            "go_no_go": {
                "ready": (
                    avg_time_to_pass < 600 and
                    false_positive_rate < 0.20 and
                    avg_vibecoding_index < 40
                ),
                "blockers": self._get_blockers(
                    avg_time_to_pass, false_positive_rate, avg_vibecoding_index
                ),
            },
        }

    def _get_zone(self, index: float) -> str:
        """Determine vibecoding zone from index."""
        if index < 30:
            return "green"
        elif index < 60:
            return "yellow"
        elif index < 80:
            return "orange"
        return "red"

    def _get_blockers(
        self,
        avg_time: float,
        fp_rate: float,
        avg_index: float,
    ) -> list[str]:
        """Get list of blockers for Go/No-Go decision."""
        blockers = []
        if avg_time >= 600:
            blockers.append(f"Developer friction too high: {avg_time/60:.1f} min (target: <10 min)")
        if fp_rate >= 0.20:
            blockers.append(f"False positive rate too high: {fp_rate*100:.1f}% (target: <20%)")
        if avg_index >= 40:
            blockers.append(f"Vibecoding index too high: {avg_index:.1f} (target: <40)")
        return blockers
```

---

## 4. API Endpoints

### 4.1 Metrics API

```python
# backend/app/api/v1/endpoints/dogfooding_metrics.py

from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.models.user import User
from app.schemas.dogfooding_metrics import (
    DogfoodingSummaryResponse,
    PRMetricsResponse,
    FeedbackCreate,
    FeedbackResponse,
)
from app.services.governance.dogfooding_metrics_service import DogfoodingMetricsService

router = APIRouter(prefix="/dogfooding", tags=["dogfooding"])


@router.get("/summary", response_model=DogfoodingSummaryResponse)
async def get_dogfooding_summary(
    start_date: date = Query(..., description="Start date (YYYY-MM-DD)"),
    end_date: date = Query(..., description="End date (YYYY-MM-DD)"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get dogfooding metrics summary for Go/No-Go decision.

    Requires: CTO or CEO role
    """
    if current_user.role not in ["cto", "ceo", "admin"]:
        raise HTTPException(status_code=403, detail="CTO/CEO access required")

    service = DogfoodingMetricsService(db)
    return await service.get_dogfooding_summary(start_date, end_date)


@router.get("/pr/{pr_number}", response_model=PRMetricsResponse)
async def get_pr_metrics(
    pr_number: int,
    repo_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get detailed metrics for a specific PR.
    """
    service = DogfoodingMetricsService(db)
    return await service.get_pr_metrics(pr_number, repo_id)


@router.post("/feedback", response_model=FeedbackResponse)
async def submit_feedback(
    feedback: FeedbackCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Submit feedback during dogfooding.

    Used by developers to report issues or suggestions.
    """
    service = DogfoodingMetricsService(db)
    return await service.create_feedback(current_user.id, feedback)


@router.post("/daily-aggregate")
async def trigger_daily_aggregation(
    target_date: date = Query(..., description="Date to aggregate"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Trigger daily metrics aggregation.

    Usually run by cron job, but can be triggered manually.
    Requires: Admin role
    """
    if current_user.role not in ["admin", "cto"]:
        raise HTTPException(status_code=403, detail="Admin access required")

    service = DogfoodingMetricsService(db)
    result = await service.aggregate_daily_metrics(target_date)
    return {"status": "aggregated", "date": str(target_date)}


@router.put("/pr/{pr_id}/classify")
async def classify_pr_result(
    pr_id: str,
    classification: str = Query(..., regex="^(true_positive|true_negative|false_positive|false_negative)$"),
    ceo_agreed: bool = Query(...),
    notes: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Classify a PR governance result for accuracy tracking.

    Used during manual review to build accuracy metrics.
    Requires: CEO or CTO role
    """
    if current_user.role not in ["cto", "ceo"]:
        raise HTTPException(status_code=403, detail="CTO/CEO access required")

    service = DogfoodingMetricsService(db)
    return await service.classify_pr(pr_id, classification, ceo_agreed, notes)
```

---

## 5. Dashboard Design

### 5.1 Dogfooding Dashboard Page

```typescript
// frontend/src/app/app/governance/dogfooding/page.tsx

"use client";

import { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";
import { Badge } from "@/components/ui/badge";
import { useDogfoodingSummary } from "@/hooks/useDogfoodingMetrics";

interface MetricCardProps {
  title: string;
  value: string | number;
  target: string;
  met: boolean;
  description: string;
}

function MetricCard({ title, value, target, met, description }: MetricCardProps) {
  return (
    <Card className={met ? "border-green-500" : "border-red-500"}>
      <CardHeader className="pb-2">
        <CardTitle className="text-sm font-medium flex items-center justify-between">
          {title}
          <Badge variant={met ? "success" : "destructive"}>
            {met ? "Target Met" : "Below Target"}
          </Badge>
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="text-2xl font-bold">{value}</div>
        <p className="text-xs text-muted-foreground">Target: {target}</p>
        <p className="text-xs text-muted-foreground mt-1">{description}</p>
      </CardContent>
    </Card>
  );
}

function VibecodingDistribution({ distribution }: { distribution: any }) {
  const total = distribution.green + distribution.yellow + distribution.orange + distribution.red;

  return (
    <Card>
      <CardHeader>
        <CardTitle>Vibecoding Index Distribution</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          <div className="space-y-2">
            <div className="flex justify-between text-sm">
              <span className="flex items-center">
                <div className="w-3 h-3 rounded-full bg-green-500 mr-2" />
                Green (0-30)
              </span>
              <span>{distribution.green} ({distribution.green_pct.toFixed(1)}%)</span>
            </div>
            <Progress value={distribution.green_pct} className="bg-green-100" />
          </div>

          <div className="space-y-2">
            <div className="flex justify-between text-sm">
              <span className="flex items-center">
                <div className="w-3 h-3 rounded-full bg-yellow-500 mr-2" />
                Yellow (31-60)
              </span>
              <span>{distribution.yellow} ({distribution.yellow_pct.toFixed(1)}%)</span>
            </div>
            <Progress value={distribution.yellow_pct} className="bg-yellow-100" />
          </div>

          <div className="space-y-2">
            <div className="flex justify-between text-sm">
              <span className="flex items-center">
                <div className="w-3 h-3 rounded-full bg-orange-500 mr-2" />
                Orange (61-80)
              </span>
              <span>{distribution.orange} ({distribution.orange_pct.toFixed(1)}%)</span>
            </div>
            <Progress value={distribution.orange_pct} className="bg-orange-100" />
          </div>

          <div className="space-y-2">
            <div className="flex justify-between text-sm">
              <span className="flex items-center">
                <div className="w-3 h-3 rounded-full bg-red-500 mr-2" />
                Red (81-100)
              </span>
              <span>{distribution.red} ({distribution.red_pct.toFixed(1)}%)</span>
            </div>
            <Progress value={distribution.red_pct} className="bg-red-100" />
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

function GoNoGoDecision({ goNoGo }: { goNoGo: any }) {
  return (
    <Card className={goNoGo.ready ? "border-green-500 bg-green-50" : "border-red-500 bg-red-50"}>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          Go/No-Go Decision
          <Badge variant={goNoGo.ready ? "success" : "destructive"} className="text-lg">
            {goNoGo.ready ? "GO" : "NO-GO"}
          </Badge>
        </CardTitle>
      </CardHeader>
      <CardContent>
        {goNoGo.ready ? (
          <p className="text-green-700">
            All targets met. Ready to proceed to Sprint 115 (Soft Enforcement).
          </p>
        ) : (
          <div>
            <p className="text-red-700 font-medium mb-2">Blockers:</p>
            <ul className="list-disc list-inside text-red-600 text-sm">
              {goNoGo.blockers.map((blocker: string, i: number) => (
                <li key={i}>{blocker}</li>
              ))}
            </ul>
          </div>
        )}
      </CardContent>
    </Card>
  );
}

export default function DogfoodingDashboard() {
  const [dateRange] = useState({
    start: "2026-02-03",
    end: "2026-02-07",
  });

  const { data: summary, isLoading } = useDogfoodingSummary(
    dateRange.start,
    dateRange.end
  );

  if (isLoading || !summary) {
    return <div className="p-8">Loading metrics...</div>;
  }

  if (summary.status === "no_data") {
    return (
      <div className="p-8">
        <Card>
          <CardContent className="pt-6">
            <p className="text-muted-foreground">
              No data collected yet. Dogfooding period: Feb 3-7, 2026.
            </p>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="p-8 space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Sprint 114: Dogfooding Metrics</h1>
        <p className="text-muted-foreground">
          WARNING Mode - {summary.days_collected} days collected
        </p>
      </div>

      {/* Go/No-Go Decision */}
      <GoNoGoDecision goNoGo={summary.go_no_go} />

      {/* Key Metrics Grid */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <MetricCard
          title="Developer Friction"
          value={`${summary.developer_friction.avg_time_to_pass_minutes.toFixed(1)} min`}
          target="< 10 min"
          met={summary.developer_friction.target_met}
          description="Average time from PR creation to governance pass"
        />

        <MetricCard
          title="False Positive Rate"
          value={`${(summary.governance_accuracy.false_positive_rate * 100).toFixed(1)}%`}
          target="< 20%"
          met={summary.governance_accuracy.target_met}
          description="PRs incorrectly flagged as violations"
        />

        <MetricCard
          title="Avg Vibecoding Index"
          value={summary.vibecoding_index.average.toFixed(1)}
          target="< 40"
          met={summary.vibecoding_index.target_met}
          description="Average code quality index across all PRs"
        />
      </div>

      {/* Secondary Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <Card>
          <CardHeader>
            <CardTitle>Developer Friction Details</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex justify-between">
              <span>Avg Compliance Attempts</span>
              <span className="font-medium">
                {summary.developer_friction.avg_compliance_attempts.toFixed(1)}
              </span>
            </div>
            <div className="flex justify-between">
              <span>Auto-Generation Usage</span>
              <span className="font-medium">
                {(summary.developer_friction.auto_generation_usage_rate * 100).toFixed(1)}%
              </span>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Governance Accuracy Details</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex justify-between">
              <span>Total Evaluations</span>
              <span className="font-medium">
                {summary.governance_accuracy.total_evaluations}
              </span>
            </div>
            <div className="flex justify-between">
              <span>CEO Agreement Rate</span>
              <span className="font-medium">
                {(summary.governance_accuracy.ceo_agreement_rate * 100).toFixed(1)}%
              </span>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Vibecoding Distribution */}
      <VibecodingDistribution distribution={summary.vibecoding_index.distribution} />
    </div>
  );
}
```

---

## 6. Go/No-Go Decision Criteria

### 6.1 Decision Matrix

| Criterion | Target | Weight | Go Condition |
|-----------|--------|--------|--------------|
| Developer Friction | < 10 min | 30% | MUST pass |
| False Positive Rate | < 20% | 30% | MUST pass |
| Vibecoding Index Avg | < 40 | 20% | SHOULD pass |
| Auto-Gen Usage | > 80% | 10% | NICE to have |
| Team NPS | > 50 | 10% | NICE to have |

### 6.2 Decision Rules

```yaml
go_no_go_decision:
  # GO to Sprint 115 (Soft Enforcement)
  go:
    mandatory:
      - developer_friction < 10 minutes
      - false_positive_rate < 20%
    recommended:
      - vibecoding_index_avg < 40
      - auto_generation_usage > 80%
      - team_nps > 50

    approval_required:
      - CTO sign-off (technical readiness)
      - CEO sign-off (business readiness)

  # EXTEND Warning Mode
  extend:
    conditions:
      - any mandatory criterion fails
      - team feedback negative (NPS < 30)

    actions:
      - Identify root cause of failure
      - Iterate on thresholds/rules
      - Re-dogfood for 1 more week

  # ABORT
  abort:
    conditions:
      - critical bug in governance system
      - security vulnerability discovered
      - team refuses to use governance

    actions:
      - Rollback to previous state
      - Post-mortem analysis
      - Redesign governance approach
```

---

## 7. Feedback Survey Template

### 7.1 Developer Feedback Form

```yaml
# Feedback survey for dogfooding participants

dogfooding_survey:
  title: "Sprint 114 Dogfooding Feedback"
  description: "Help us improve the governance system"

  sections:
    - name: "Overall Experience"
      questions:
        - id: nps
          type: scale
          question: "How likely are you to recommend this governance system to other teams?"
          scale: 1-10
          labels:
            1: "Not at all likely"
            10: "Extremely likely"

        - id: overall_friction
          type: scale
          question: "How much did governance slow down your workflow?"
          scale: 1-5
          labels:
            1: "Not at all"
            5: "Significantly"

    - name: "Auto-Generation Features"
      questions:
        - id: intent_gen_useful
          type: scale
          question: "How useful was auto-generated intent?"
          scale: 1-5

        - id: ownership_suggestion_accurate
          type: scale
          question: "How accurate were ownership suggestions?"
          scale: 1-5

        - id: context_attachment_relevant
          type: scale
          question: "How relevant were auto-attached contexts?"
          scale: 1-5

    - name: "Vibecoding Index"
      questions:
        - id: index_accuracy
          type: scale
          question: "How accurately did the vibecoding index reflect code quality?"
          scale: 1-5

        - id: index_explanation
          type: scale
          question: "How clear was the explanation of the index score?"
          scale: 1-5

    - name: "Open Feedback"
      questions:
        - id: most_helpful
          type: text
          question: "What feature was most helpful?"

        - id: most_frustrating
          type: text
          question: "What was most frustrating?"

        - id: suggestions
          type: text
          question: "What improvements would you suggest?"
```

---

## 8. Implementation Timeline

### 8.1 Sprint 114 Day-by-Day Plan

| Day | Tasks | Owner | Deliverables |
|-----|-------|-------|--------------|
| **Day 1** | Enable WARNING mode, deploy metrics collection | DevOps + Backend | Config deployed, first PR evaluated |
| **Day 2** | Monitor metrics, fix issues, collect feedback | Full team | At least 5 PRs evaluated |
| **Day 3** | Continue monitoring, daily aggregation | Full team | Metrics dashboard populated |
| **Day 4** | CEO classification review, tune thresholds | CTO + CEO | Classification data filled |
| **Day 5** | Final analysis, Go/No-Go decision | CTO + CEO | Decision documented |

---

## 9. Appendix

### 9.1 Prometheus Metrics

```yaml
# Prometheus metrics for dogfooding monitoring

metrics:
  governance_evaluation_duration_seconds:
    type: histogram
    help: "Time taken for governance evaluation"
    buckets: [0.01, 0.05, 0.1, 0.25, 0.5, 1, 2.5, 5]

  governance_evaluation_total:
    type: counter
    help: "Total governance evaluations"
    labels: [result, zone]

  governance_auto_generation_total:
    type: counter
    help: "Auto-generation usage"
    labels: [artifact_type, success]

  governance_vibecoding_index:
    type: histogram
    help: "Vibecoding index distribution"
    buckets: [10, 20, 30, 40, 50, 60, 70, 80, 90, 100]
```

### 9.2 Grafana Dashboard JSON

See: `docs/02-design/15-Monitoring/sprint-114-dogfooding-dashboard.json`

---

## Document Control

| Field | Value |
|-------|-------|
| **Version** | 1.0.0 |
| **Created** | January 28, 2026 |
| **Author** | Backend Lead |
| **Status** | DRAFT - Awaiting CTO Approval |
| **Sprint** | 114 |
| **Dependencies** | Sprint 113 Complete |

---

*SDLC Framework 6.0 - Quality Assurance System - Dogfooding Specification*
