"""
=========================================================================
MCP Analytics Routes - Dashboard API Endpoints
SDLC Orchestrator - Sprint 150 (Phase 1 Completion)

Version: 1.0.0
Date: February 25, 2026
Status: ACTIVE
Authority: CTO Approved
Framework: SDLC 6.0.3 Phase 1 Completion

Endpoints:
- GET  /api/v1/mcp/health        - Provider health metrics
- GET  /api/v1/mcp/cost          - Cost tracking metrics
- GET  /api/v1/mcp/latency       - Latency trends
- GET  /api/v1/mcp/context       - Context provider usage
- GET  /api/v1/mcp/dashboard     - Complete dashboard summary

Security:
- All endpoints require authentication
- Read-only operations (no side effects)

Zero Mock Policy: Real metrics from production telemetry.
=========================================================================
"""

import logging
from datetime import date, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_db, get_current_user
from app.models import User
from app.services.mcp_analytics_service import (
    MCPAnalyticsService,
    get_mcp_analytics_service,
)
from app.schemas.mcp_analytics import (
    ProviderHealthResponse,
    CostTrackingResponse,
    LatencyResponse,
    ContextUsageResponse,
    MCPDashboardSummary,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/mcp", tags=["MCP Analytics"])


# =========================================================================
# Health Endpoint
# =========================================================================


@router.get(
    "/health",
    response_model=ProviderHealthResponse,
    summary="Get provider health metrics",
    description="Returns health status, uptime, and error rates for all AI providers.",
)
async def get_provider_health(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ProviderHealthResponse:
    """
    Get health metrics for all AI providers.

    Returns:
        ProviderHealthResponse with status for Ollama, Claude, and OpenAI.

    Example Response:
        {
            "providers": [
                {
                    "provider_name": "ollama",
                    "status": "healthy",
                    "uptime_percent": 99.9,
                    "avg_latency_ms": 45.2,
                    "error_rate_percent": 0.1
                },
                ...
            ],
            "overall_status": "healthy"
        }
    """
    service = get_mcp_analytics_service(db)
    return await service.get_provider_health()


# =========================================================================
# Cost Tracking Endpoint
# =========================================================================


@router.get(
    "/cost",
    response_model=CostTrackingResponse,
    summary="Get cost tracking metrics",
    description="Returns cost estimates per provider and category breakdown.",
)
async def get_cost_tracking(
    start_date: Optional[date] = Query(
        None,
        description="Start date (defaults to 7 days ago)"
    ),
    end_date: Optional[date] = Query(
        None,
        description="End date (defaults to today)"
    ),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> CostTrackingResponse:
    """
    Get cost tracking metrics for AI providers.

    Args:
        start_date: Start of analysis period (defaults to 7 days ago)
        end_date: End of analysis period (defaults to today)

    Returns:
        CostTrackingResponse with cost data per provider and category.

    Example Response:
        {
            "providers": [
                {
                    "provider_name": "ollama",
                    "total_requests": 1250,
                    "estimated_cost_usd": 0.00
                },
                {
                    "provider_name": "claude",
                    "total_requests": 85,
                    "estimated_cost_usd": 12.50
                }
            ],
            "total_cost_usd": 12.50,
            "budget_usage_percent": 1.25
        }
    """
    if end_date is None:
        end_date = date.today()
    if start_date is None:
        start_date = end_date - timedelta(days=7)

    service = get_mcp_analytics_service(db)
    return await service.get_cost_tracking(start_date, end_date)


# =========================================================================
# Latency Endpoint
# =========================================================================


@router.get(
    "/latency",
    response_model=LatencyResponse,
    summary="Get latency metrics",
    description="Returns latency trends and SLA compliance per provider.",
)
async def get_latency_metrics(
    start_date: Optional[date] = Query(
        None,
        description="Start date (defaults to 7 days ago)"
    ),
    end_date: Optional[date] = Query(
        None,
        description="End date (defaults to today)"
    ),
    granularity: str = Query(
        "day",
        description="Time granularity: hour, day, week"
    ),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> LatencyResponse:
    """
    Get latency metrics and trends for AI providers.

    Args:
        start_date: Start of analysis period (defaults to 7 days ago)
        end_date: End of analysis period (defaults to today)
        granularity: Time granularity for trend data

    Returns:
        LatencyResponse with latency trends and SLA compliance.

    Example Response:
        {
            "providers": [
                {
                    "provider_name": "ollama",
                    "current_avg_ms": 45.2,
                    "current_p95_ms": 120.5,
                    "sla_compliance_percent": 98.5,
                    "trend": [...]
                }
            ],
            "overall_avg_ms": 52.3,
            "overall_p95_ms": 145.0
        }
    """
    if end_date is None:
        end_date = date.today()
    if start_date is None:
        start_date = end_date - timedelta(days=7)

    service = get_mcp_analytics_service(db)
    return await service.get_latency_metrics(start_date, end_date, granularity)


# =========================================================================
# Context Usage Endpoint
# =========================================================================


@router.get(
    "/context",
    response_model=ContextUsageResponse,
    summary="Get context provider usage",
    description="Returns usage statistics for each context provider.",
)
async def get_context_usage(
    start_date: Optional[date] = Query(
        None,
        description="Start date (defaults to 7 days ago)"
    ),
    end_date: Optional[date] = Query(
        None,
        description="End date (defaults to today)"
    ),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ContextUsageResponse:
    """
    Get usage metrics for context providers.

    Args:
        start_date: Start of analysis period (defaults to 7 days ago)
        end_date: End of analysis period (defaults to today)

    Returns:
        ContextUsageResponse with usage per context provider.

    Example Response:
        {
            "providers": [
                {
                    "provider_name": "project",
                    "invocations": 5420,
                    "avg_latency_ms": 12.5,
                    "cache_hit_rate": 85.0
                }
            ],
            "total_invocations": 15000,
            "most_used_provider": "project"
        }
    """
    if end_date is None:
        end_date = date.today()
    if start_date is None:
        start_date = end_date - timedelta(days=7)

    service = get_mcp_analytics_service(db)
    return await service.get_context_usage(start_date, end_date)


# =========================================================================
# Dashboard Summary Endpoint
# =========================================================================


@router.get(
    "/dashboard",
    response_model=MCPDashboardSummary,
    summary="Get complete dashboard summary",
    description="Returns all MCP analytics in a single response for dashboard rendering.",
)
async def get_dashboard_summary(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> MCPDashboardSummary:
    """
    Get complete MCP Analytics dashboard summary.

    This endpoint aggregates all metrics into a single response optimized
    for dashboard rendering. It includes:
    - Provider health status
    - Cost summary (last 7 days)
    - Latency summary (last 7 days)
    - Usage statistics
    - Context provider usage

    Returns:
        MCPDashboardSummary with all key metrics.

    Example Response:
        {
            "overall_health": "healthy",
            "providers_healthy": 3,
            "providers_total": 3,
            "total_cost_usd_7d": 12.50,
            "cost_trend_percent": -5.2,
            "avg_latency_ms_7d": 52.3,
            "sla_compliance_percent": 98.5,
            "total_requests_7d": 1500,
            "top_provider": "ollama",
            "context_invocations_7d": 15000,
            "top_context_provider": "project"
        }
    """
    service = get_mcp_analytics_service(db)
    return await service.get_dashboard_summary()
