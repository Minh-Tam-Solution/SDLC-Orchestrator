"""
Codegen Usage Tracking Models - Sprint 48.

Track AI code generation usage for cost management and analytics:
- Individual generation requests
- Token usage per provider
- Cost tracking and reporting
- Quality gate results

SDLC Stage: 04 - BUILD
Sprint: 48 - Quality Gates + Ollama Optimization + MVP Hardening
Framework: SDLC 5.1.3
Epic: EP-06 IR-Based Vietnamese SME Codegen

Target: <$50/month infrastructure cost per project
"""

import uuid
from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Optional

from sqlalchemy import (
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    Boolean,
    Numeric,
    Index,
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship

from app.db.base_class import Base


class GenerationStatus(str, Enum):
    """Status of a code generation request."""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    BLOCKED = "blocked"  # Blocked by quality gates


class QualityGateStatus(str, Enum):
    """Status of quality gate validation."""

    PENDING = "pending"
    PASSED = "passed"
    FAILED = "failed"
    SKIPPED = "skipped"
    ERROR = "error"


class CodegenUsageLog(Base):
    """
    Track individual code generation requests.

    Records every generation request for cost tracking and analytics.
    Links to project and user for billing and usage reports.
    """

    __tablename__ = "codegen_usage_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)

    # User and project context
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    project_id = Column(
        UUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    # Request info
    request_id = Column(String(64), nullable=False, unique=True, index=True)
    provider = Column(String(50), nullable=False, index=True)  # ollama, claude, deepcode
    model = Column(String(100), nullable=True)  # qwen3-coder:30b, claude-3, etc.
    status = Column(String(20), nullable=False, default=GenerationStatus.PENDING.value, index=True)

    # Generation parameters
    language = Column(String(50), nullable=False, default="python")
    framework = Column(String(50), nullable=False, default="fastapi")
    target_module = Column(String(100), nullable=True)

    # Blueprint info
    blueprint_name = Column(String(200), nullable=True)
    blueprint_hash = Column(String(64), nullable=True)  # SHA256 of blueprint JSON
    blueprint_size_bytes = Column(Integer, nullable=True)

    # Token usage
    prompt_tokens = Column(Integer, default=0)
    completion_tokens = Column(Integer, default=0)
    total_tokens = Column(Integer, default=0)

    # Cost tracking (in USD, 6 decimal places for micro-cents)
    estimated_cost_usd = Column(Numeric(10, 6), default=Decimal("0"))
    actual_cost_usd = Column(Numeric(10, 6), default=Decimal("0"))

    # Performance
    generation_time_ms = Column(Integer, nullable=True)
    queue_wait_ms = Column(Integer, nullable=True)

    # Output info
    files_generated = Column(Integer, default=0)
    total_lines_generated = Column(Integer, default=0)
    output_size_bytes = Column(Integer, default=0)

    # Quality gate results
    quality_gate_status = Column(String(20), nullable=True)
    quality_errors = Column(Integer, default=0)
    quality_warnings = Column(Integer, default=0)
    quality_blocked = Column(Boolean, default=False)

    # Error tracking
    error_message = Column(Text, nullable=True)
    error_type = Column(String(100), nullable=True)

    # Extra metadata (named to avoid SQLAlchemy reserved word)
    extra_metadata = Column(JSONB, nullable=True)

    # Timestamps
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    completed_at = Column(DateTime, nullable=True)

    # Relationships
    user = relationship("User", backref="codegen_usage_logs")
    project = relationship("Project", backref="codegen_usage_logs")

    # Indexes for cost reporting
    __table_args__ = (
        Index("ix_codegen_usage_logs_user_date", "user_id", "created_at"),
        Index("ix_codegen_usage_logs_project_date", "project_id", "created_at"),
        Index("ix_codegen_usage_logs_provider_date", "provider", "created_at"),
    )

    def __repr__(self) -> str:
        return f"<CodegenUsageLog {self.request_id} provider={self.provider}>"


class CodegenDailySummary(Base):
    """
    Daily aggregated codegen usage statistics.

    Used for cost reports and dashboards. Aggregated from CodegenUsageLog.
    """

    __tablename__ = "codegen_daily_summaries"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)

    # Aggregation key
    date = Column(DateTime, nullable=False, index=True)  # Date only, no time
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    project_id = Column(
        UUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    provider = Column(String(50), nullable=False, index=True)

    # Request counts
    total_requests = Column(Integer, default=0)
    successful_requests = Column(Integer, default=0)
    failed_requests = Column(Integer, default=0)
    blocked_requests = Column(Integer, default=0)

    # Token usage
    total_prompt_tokens = Column(Integer, default=0)
    total_completion_tokens = Column(Integer, default=0)
    total_tokens = Column(Integer, default=0)

    # Cost
    total_cost_usd = Column(Numeric(10, 6), default=Decimal("0"))
    avg_cost_per_request = Column(Numeric(10, 6), default=Decimal("0"))

    # Performance
    avg_generation_time_ms = Column(Integer, default=0)
    p95_generation_time_ms = Column(Integer, default=0)
    min_generation_time_ms = Column(Integer, nullable=True)
    max_generation_time_ms = Column(Integer, nullable=True)

    # Output
    total_files_generated = Column(Integer, default=0)
    total_lines_generated = Column(Integer, default=0)

    # Quality
    quality_pass_rate = Column(Numeric(5, 2), nullable=True)  # 0.00 to 100.00
    total_quality_errors = Column(Integer, default=0)
    total_quality_warnings = Column(Integer, default=0)

    # Timestamps
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Composite unique constraint
    __table_args__ = (
        Index(
            "ix_codegen_daily_summaries_unique",
            "date", "user_id", "project_id", "provider",
            unique=True,
        ),
    )

    def __repr__(self) -> str:
        return f"<CodegenDailySummary {self.date} provider={self.provider}>"


class CodegenMonthlyCost(Base):
    """
    Monthly cost tracking for budget management.

    Target: <$50/month per project (Founder Plan)
    """

    __tablename__ = "codegen_monthly_costs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)

    # Aggregation key
    year = Column(Integer, nullable=False)
    month = Column(Integer, nullable=False)  # 1-12
    project_id = Column(
        UUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )

    # Cost breakdown by provider
    ollama_cost_usd = Column(Numeric(10, 2), default=Decimal("0"))
    claude_cost_usd = Column(Numeric(10, 2), default=Decimal("0"))
    deepcode_cost_usd = Column(Numeric(10, 2), default=Decimal("0"))
    total_cost_usd = Column(Numeric(10, 2), default=Decimal("0"))

    # Budget tracking
    budget_limit_usd = Column(Numeric(10, 2), default=Decimal("50"))  # $50 default
    budget_used_percent = Column(Numeric(5, 2), default=Decimal("0"))  # 0.00 to 100.00+
    budget_exceeded = Column(Boolean, default=False)

    # Usage counts
    total_requests = Column(Integer, default=0)
    total_tokens = Column(Integer, default=0)

    # Quality metrics
    avg_quality_pass_rate = Column(Numeric(5, 2), nullable=True)

    # Timestamps
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Composite unique constraint
    __table_args__ = (
        Index(
            "ix_codegen_monthly_costs_unique",
            "year", "month", "project_id",
            unique=True,
        ),
    )

    def __repr__(self) -> str:
        return f"<CodegenMonthlyCost {self.year}/{self.month} project={self.project_id}>"


class CodegenProviderHealth(Base):
    """
    Track provider health and availability.

    Used for monitoring fallback frequency and provider reliability.
    """

    __tablename__ = "codegen_provider_health"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)

    # Provider info
    provider = Column(String(50), nullable=False, index=True)
    checked_at = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)

    # Health status
    is_available = Column(Boolean, default=True)
    response_time_ms = Column(Integer, nullable=True)
    error_message = Column(Text, nullable=True)

    # Model availability
    model = Column(String(100), nullable=True)
    model_available = Column(Boolean, default=True)

    def __repr__(self) -> str:
        return f"<CodegenProviderHealth {self.provider} available={self.is_available}>"
