"""
=========================================================================
MCP Analytics Schemas - Dashboard Data Models
SDLC Orchestrator - Sprint 150 (Phase 1 Completion)

Version: 1.0.0
Date: February 25, 2026
Status: ACTIVE
Authority: CTO Approved
Framework: SDLC 6.0.3 Phase 1 Completion

Purpose:
Provide Pydantic schemas for MCP (Model Context Protocol) analytics
dashboard endpoints, including provider health, cost tracking, and
latency metrics.

Zero Mock Policy: Real metrics from production telemetry.
=========================================================================
"""

from datetime import datetime, date
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


# =========================================================================
# Provider Health Schemas
# =========================================================================


class ProviderHealthMetrics(BaseModel):
    """Health metrics for a single AI provider."""
    provider_name: str = Field(..., description="Provider name (ollama, claude, openai)")
    status: str = Field(..., description="Status: healthy, degraded, down")
    uptime_percent: float = Field(..., description="Uptime percentage (0-100)")
    last_check: datetime = Field(..., description="Last health check timestamp")
    avg_latency_ms: float = Field(..., description="Average response latency in ms")
    p95_latency_ms: float = Field(..., description="95th percentile latency in ms")
    error_rate_percent: float = Field(..., description="Error rate percentage (0-100)")
    requests_24h: int = Field(..., description="Total requests in last 24 hours")
    success_count_24h: int = Field(..., description="Successful requests in last 24h")
    error_count_24h: int = Field(..., description="Failed requests in last 24h")


class ProviderHealthResponse(BaseModel):
    """Response containing health metrics for all providers."""
    providers: List[ProviderHealthMetrics] = Field(..., description="Health metrics per provider")
    overall_status: str = Field(..., description="Overall system status")
    generated_at: datetime = Field(default_factory=datetime.utcnow)


# =========================================================================
# Cost Tracking Schemas
# =========================================================================


class ProviderCostMetrics(BaseModel):
    """Cost metrics for a single AI provider."""
    provider_name: str = Field(..., description="Provider name")
    total_requests: int = Field(..., description="Total requests in period")
    total_tokens_input: int = Field(..., description="Total input tokens")
    total_tokens_output: int = Field(..., description="Total output tokens")
    estimated_cost_usd: float = Field(..., description="Estimated cost in USD")
    cost_per_request_avg: float = Field(..., description="Average cost per request")


class CostBreakdown(BaseModel):
    """Cost breakdown by category."""
    category: str = Field(..., description="Category (chat, codegen, analysis, etc.)")
    requests: int = Field(..., description="Request count")
    tokens: int = Field(..., description="Total tokens")
    cost_usd: float = Field(..., description="Cost in USD")
    percentage: float = Field(..., description="Percentage of total cost")


class CostTrackingResponse(BaseModel):
    """Response containing cost tracking data."""
    period: Dict[str, str] = Field(..., description="Analysis period (start, end)")
    providers: List[ProviderCostMetrics] = Field(..., description="Cost per provider")
    breakdown_by_category: List[CostBreakdown] = Field(..., description="Cost by category")
    total_cost_usd: float = Field(..., description="Total cost in USD")
    budget_limit_usd: Optional[float] = Field(None, description="Monthly budget limit")
    budget_usage_percent: Optional[float] = Field(None, description="Budget usage percentage")
    generated_at: datetime = Field(default_factory=datetime.utcnow)


# =========================================================================
# Latency Schemas
# =========================================================================


class LatencyTrend(BaseModel):
    """Latency data point for a time series."""
    timestamp: datetime = Field(..., description="Timestamp of measurement")
    avg_latency_ms: float = Field(..., description="Average latency in ms")
    p50_latency_ms: float = Field(..., description="50th percentile (median) latency")
    p95_latency_ms: float = Field(..., description="95th percentile latency")
    p99_latency_ms: float = Field(..., description="99th percentile latency")
    request_count: int = Field(..., description="Number of requests in period")


class ProviderLatencyMetrics(BaseModel):
    """Latency metrics for a single provider."""
    provider_name: str = Field(..., description="Provider name")
    current_avg_ms: float = Field(..., description="Current average latency")
    current_p95_ms: float = Field(..., description="Current p95 latency")
    trend: List[LatencyTrend] = Field(..., description="Latency trend over time")
    sla_target_ms: int = Field(100, description="SLA target latency in ms")
    sla_compliance_percent: float = Field(..., description="SLA compliance percentage")


class LatencyResponse(BaseModel):
    """Response containing latency metrics."""
    period: Dict[str, str] = Field(..., description="Analysis period")
    providers: List[ProviderLatencyMetrics] = Field(..., description="Latency per provider")
    overall_avg_ms: float = Field(..., description="Overall average latency")
    overall_p95_ms: float = Field(..., description="Overall p95 latency")
    generated_at: datetime = Field(default_factory=datetime.utcnow)


# =========================================================================
# Context Provider Schemas
# =========================================================================


class ContextProviderUsage(BaseModel):
    """Usage metrics for a context provider."""
    provider_name: str = Field(..., description="Context provider name")
    invocations: int = Field(..., description="Total invocations")
    avg_latency_ms: float = Field(..., description="Average processing latency")
    cache_hit_rate: float = Field(..., description="Cache hit rate (0-100)")
    data_size_bytes: int = Field(..., description="Total data processed in bytes")


class ContextUsageResponse(BaseModel):
    """Response containing context provider usage."""
    period: Dict[str, str] = Field(..., description="Analysis period")
    providers: List[ContextProviderUsage] = Field(..., description="Usage per provider")
    total_invocations: int = Field(..., description="Total context invocations")
    most_used_provider: str = Field(..., description="Most frequently used provider")
    generated_at: datetime = Field(default_factory=datetime.utcnow)


# =========================================================================
# Dashboard Summary Schema
# =========================================================================


class MCPDashboardSummary(BaseModel):
    """Complete MCP Analytics Dashboard summary."""
    period: Dict[str, str] = Field(..., description="Analysis period")

    # Health summary
    overall_health: str = Field(..., description="Overall health status")
    providers_healthy: int = Field(..., description="Number of healthy providers")
    providers_total: int = Field(..., description="Total number of providers")

    # Cost summary
    total_cost_usd_7d: float = Field(..., description="Total cost last 7 days")
    cost_trend_percent: float = Field(..., description="Cost trend vs previous period")

    # Latency summary
    avg_latency_ms_7d: float = Field(..., description="Average latency last 7 days")
    p95_latency_ms_7d: float = Field(..., description="P95 latency last 7 days")
    sla_compliance_percent: float = Field(..., description="SLA compliance percentage")

    # Usage summary
    total_requests_7d: int = Field(..., description="Total requests last 7 days")
    requests_trend_percent: float = Field(..., description="Request trend vs previous period")
    top_provider: str = Field(..., description="Most used provider")

    # Context usage
    context_invocations_7d: int = Field(..., description="Context invocations last 7 days")
    top_context_provider: str = Field(..., description="Most used context provider")

    generated_at: datetime = Field(default_factory=datetime.utcnow)


# =========================================================================
# Request Schemas
# =========================================================================


class DateRangeRequest(BaseModel):
    """Request for date range-based queries."""
    start_date: date = Field(..., description="Start date")
    end_date: date = Field(..., description="End date")
    granularity: str = Field("hour", description="Time granularity: hour, day, week")


class ProviderFilterRequest(BaseModel):
    """Request with optional provider filter."""
    provider: Optional[str] = Field(None, description="Filter by provider name")
    start_date: Optional[date] = Field(None, description="Start date")
    end_date: Optional[date] = Field(None, description="End date")
