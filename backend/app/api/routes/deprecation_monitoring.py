"""
=========================================================================
Deprecation Monitoring API - V1 Sunset Tracking
SDLC Orchestrator - Sprint 150 (Phase 1 Completion)

Version: 1.0.0
Date: February 25, 2026
Status: ACTIVE
Authority: CTO Approved
Framework: SDLC 6.0.3 API Deprecation Policy

Purpose:
Provide visibility into deprecated endpoint usage for migration planning.
Track V1 → V2 migration progress and identify clients still using deprecated APIs.

Endpoints:
- GET /deprecation/summary - Overall deprecation status
- GET /deprecation/endpoints - Detailed per-endpoint usage
- GET /deprecation/timeline - Usage trends over time

Exit Criteria:
- V1 calls/day should trend to 0 before sunset date
- All clients migrated to V2 endpoints
=========================================================================
"""

from datetime import date, datetime, timedelta
from typing import Any, Dict, List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_user, get_db
from app.models.product_event import ProductEvent
from app.models.user import User
from app.utils.deprecation import (
    ANALYTICS_V1_SUNSET,
    CONTEXT_AUTHORITY_V1_SUNSET,
    days_until_sunset,
)

router = APIRouter(prefix="/deprecation", tags=["Deprecation Monitoring"])


# =============================================================================
# Schemas
# =============================================================================


class DeprecatedEndpointUsage(BaseModel):
    """Usage statistics for a single deprecated endpoint."""

    endpoint: str = Field(..., description="Endpoint path")
    successor: str = Field(..., description="Recommended successor endpoint")
    sunset_date: str = Field(..., description="Removal date (YYYY-MM-DD)")
    days_until_sunset: int = Field(..., description="Days remaining until removal")
    calls_last_24h: int = Field(0, description="Calls in the last 24 hours")
    calls_last_7d: int = Field(0, description="Calls in the last 7 days")
    calls_last_30d: int = Field(0, description="Calls in the last 30 days")
    unique_clients: int = Field(0, description="Unique clients in last 7 days")
    status: str = Field(..., description="Status: 'active', 'warning', 'critical', 'migrated'")


class DeprecationSummary(BaseModel):
    """Overall deprecation monitoring summary."""

    total_deprecated_endpoints: int = Field(..., description="Total deprecated endpoints")
    total_calls_last_24h: int = Field(0, description="Total deprecated calls in 24h")
    total_calls_last_7d: int = Field(0, description="Total deprecated calls in 7d")
    endpoints_with_zero_usage: int = Field(0, description="Endpoints with no recent usage")
    endpoints_at_risk: int = Field(0, description="Endpoints with usage near sunset")
    migration_progress: float = Field(..., description="Migration progress percentage")
    generated_at: datetime = Field(default_factory=datetime.utcnow)


class DeprecationTimelineEntry(BaseModel):
    """Daily usage count for deprecation timeline."""

    date: str = Field(..., description="Date (YYYY-MM-DD)")
    total_calls: int = Field(0, description="Total deprecated endpoint calls")
    unique_endpoints: int = Field(0, description="Unique endpoints called")


class DeprecationDashboard(BaseModel):
    """Complete deprecation monitoring dashboard."""

    summary: DeprecationSummary
    endpoints: List[DeprecatedEndpointUsage]
    timeline: List[DeprecationTimelineEntry]


# =============================================================================
# Known Deprecated Endpoints (V1 APIs)
# =============================================================================

DEPRECATED_ENDPOINTS = {
    # Context Authority V1 (Sunset: March 6, 2026)
    "/api/v1/context-authority/validate": {
        "successor": "/api/v1/context-authority/v2/validate",
        "sunset_date": CONTEXT_AUTHORITY_V1_SUNSET,
        "category": "context_authority",
    },
    "/api/v1/context-authority/adrs": {
        "successor": "/api/v1/context-authority/v2/adrs",
        "sunset_date": CONTEXT_AUTHORITY_V1_SUNSET,
        "category": "context_authority",
    },
    "/api/v1/context-authority/modules": {
        "successor": "/api/v1/context-authority/v2/modules",
        "sunset_date": CONTEXT_AUTHORITY_V1_SUNSET,
        "category": "context_authority",
    },
    "/api/v1/context-authority/batch-validate": {
        "successor": "/api/v1/context-authority/v2/batch-validate",
        "sunset_date": CONTEXT_AUTHORITY_V1_SUNSET,
        "category": "context_authority",
    },
    "/api/v1/context-authority/check-freshness": {
        "successor": "/api/v1/context-authority/v2/check-freshness",
        "sunset_date": CONTEXT_AUTHORITY_V1_SUNSET,
        "category": "context_authority",
    },
    "/api/v1/context-authority/stats": {
        "successor": "/api/v1/context-authority/v2/stats",
        "sunset_date": CONTEXT_AUTHORITY_V1_SUNSET,
        "category": "context_authority",
    },
    "/api/v1/context-authority/compliance": {
        "successor": "/api/v1/context-authority/v2/compliance",
        "sunset_date": CONTEXT_AUTHORITY_V1_SUNSET,
        "category": "context_authority",
    },
    # Analytics V1 (Sunset: March 6, 2026)
    "/api/v1/analytics/overview": {
        "successor": "/api/v1/analytics/v2/dashboard",
        "sunset_date": ANALYTICS_V1_SUNSET,
        "category": "analytics",
    },
    "/api/v1/analytics/projects": {
        "successor": "/api/v1/analytics/v2/projects",
        "sunset_date": ANALYTICS_V1_SUNSET,
        "category": "analytics",
    },
    "/api/v1/analytics/gates": {
        "successor": "/api/v1/analytics/v2/gates",
        "sunset_date": ANALYTICS_V1_SUNSET,
        "category": "analytics",
    },
}


# =============================================================================
# Endpoints
# =============================================================================


@router.get("/summary", response_model=DeprecationSummary)
async def get_deprecation_summary(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> DeprecationSummary:
    """
    Get overall deprecation monitoring summary.

    Returns aggregated metrics for all deprecated endpoints including:
    - Total calls in last 24h/7d
    - Migration progress percentage
    - Endpoints at risk (usage near sunset date)
    """
    today = date.today()
    day_ago = today - timedelta(days=1)
    week_ago = today - timedelta(days=7)

    # Query deprecated endpoint calls from telemetry
    calls_24h_query = select(func.count(ProductEvent.id)).where(
        ProductEvent.event_name == "deprecated_endpoint_called",
        func.date(ProductEvent.timestamp) >= day_ago,
    )
    calls_24h_result = await db.execute(calls_24h_query)
    total_calls_24h = calls_24h_result.scalar() or 0

    calls_7d_query = select(func.count(ProductEvent.id)).where(
        ProductEvent.event_name == "deprecated_endpoint_called",
        func.date(ProductEvent.timestamp) >= week_ago,
    )
    calls_7d_result = await db.execute(calls_7d_query)
    total_calls_7d = calls_7d_result.scalar() or 0

    # Count unique endpoints with usage in last 7 days
    endpoints_query = (
        select(ProductEvent.properties["endpoint"].astext)
        .where(
            ProductEvent.event_name == "deprecated_endpoint_called",
            func.date(ProductEvent.timestamp) >= week_ago,
        )
        .distinct()
    )
    endpoints_result = await db.execute(endpoints_query)
    used_endpoints = set(row[0] for row in endpoints_result.fetchall() if row[0])

    total_deprecated = len(DEPRECATED_ENDPOINTS)
    endpoints_with_zero = total_deprecated - len(used_endpoints)

    # Count endpoints at risk (usage within 7 days of sunset)
    endpoints_at_risk = 0
    for endpoint, info in DEPRECATED_ENDPOINTS.items():
        days_left = days_until_sunset(info["sunset_date"])
        if days_left <= 7 and endpoint in used_endpoints:
            endpoints_at_risk += 1

    # Migration progress = percentage of endpoints with zero usage
    migration_progress = (endpoints_with_zero / total_deprecated * 100) if total_deprecated > 0 else 100

    return DeprecationSummary(
        total_deprecated_endpoints=total_deprecated,
        total_calls_last_24h=total_calls_24h,
        total_calls_last_7d=total_calls_7d,
        endpoints_with_zero_usage=endpoints_with_zero,
        endpoints_at_risk=endpoints_at_risk,
        migration_progress=round(migration_progress, 1),
        generated_at=datetime.utcnow(),
    )


@router.get("/endpoints", response_model=List[DeprecatedEndpointUsage])
async def get_deprecated_endpoints(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    category: Optional[str] = Query(None, description="Filter by category (context_authority, analytics)"),
) -> List[DeprecatedEndpointUsage]:
    """
    Get detailed usage statistics for all deprecated endpoints.

    Returns per-endpoint metrics including:
    - Call counts (24h, 7d, 30d)
    - Unique clients
    - Status (active/warning/critical/migrated)
    """
    today = date.today()
    day_ago = today - timedelta(days=1)
    week_ago = today - timedelta(days=7)
    month_ago = today - timedelta(days=30)

    results = []

    for endpoint, info in DEPRECATED_ENDPOINTS.items():
        # Filter by category if specified
        if category and info.get("category") != category:
            continue

        # Get usage counts
        calls_24h_query = select(func.count(ProductEvent.id)).where(
            ProductEvent.event_name == "deprecated_endpoint_called",
            ProductEvent.properties["endpoint"].astext == endpoint,
            func.date(ProductEvent.timestamp) >= day_ago,
        )
        calls_24h_result = await db.execute(calls_24h_query)
        calls_24h = calls_24h_result.scalar() or 0

        calls_7d_query = select(func.count(ProductEvent.id)).where(
            ProductEvent.event_name == "deprecated_endpoint_called",
            ProductEvent.properties["endpoint"].astext == endpoint,
            func.date(ProductEvent.timestamp) >= week_ago,
        )
        calls_7d_result = await db.execute(calls_7d_query)
        calls_7d = calls_7d_result.scalar() or 0

        calls_30d_query = select(func.count(ProductEvent.id)).where(
            ProductEvent.event_name == "deprecated_endpoint_called",
            ProductEvent.properties["endpoint"].astext == endpoint,
            func.date(ProductEvent.timestamp) >= month_ago,
        )
        calls_30d_result = await db.execute(calls_30d_query)
        calls_30d = calls_30d_result.scalar() or 0

        # Count unique clients (based on client_info in properties)
        unique_clients_query = (
            select(func.count(func.distinct(ProductEvent.properties["client_info"].astext)))
            .where(
                ProductEvent.event_name == "deprecated_endpoint_called",
                ProductEvent.properties["endpoint"].astext == endpoint,
                func.date(ProductEvent.timestamp) >= week_ago,
            )
        )
        unique_clients_result = await db.execute(unique_clients_query)
        unique_clients = unique_clients_result.scalar() or 0

        # Determine status
        days_left = days_until_sunset(info["sunset_date"])
        if calls_7d == 0:
            status = "migrated"
        elif days_left <= 0:
            status = "critical"  # Past sunset date
        elif days_left <= 7:
            status = "warning"  # Within 7 days of sunset
        else:
            status = "active"

        results.append(
            DeprecatedEndpointUsage(
                endpoint=endpoint,
                successor=info["successor"],
                sunset_date=info["sunset_date"],
                days_until_sunset=days_left,
                calls_last_24h=calls_24h,
                calls_last_7d=calls_7d,
                calls_last_30d=calls_30d,
                unique_clients=unique_clients,
                status=status,
            )
        )

    # Sort by status priority (critical > warning > active > migrated)
    status_priority = {"critical": 0, "warning": 1, "active": 2, "migrated": 3}
    results.sort(key=lambda x: (status_priority.get(x.status, 99), -x.calls_last_7d))

    return results


@router.get("/timeline", response_model=List[DeprecationTimelineEntry])
async def get_deprecation_timeline(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    days: int = Query(30, ge=7, le=90, description="Number of days to include"),
) -> List[DeprecationTimelineEntry]:
    """
    Get deprecation usage timeline for trend analysis.

    Returns daily usage counts to visualize migration progress over time.
    Usage should trend toward zero as clients migrate to V2.
    """
    today = date.today()
    start_date = today - timedelta(days=days)

    # Query daily aggregates
    daily_query = (
        select(
            func.date(ProductEvent.timestamp).label("event_date"),
            func.count(ProductEvent.id).label("total_calls"),
            func.count(func.distinct(ProductEvent.properties["endpoint"].astext)).label("unique_endpoints"),
        )
        .where(
            ProductEvent.event_name == "deprecated_endpoint_called",
            func.date(ProductEvent.timestamp) >= start_date,
        )
        .group_by(func.date(ProductEvent.timestamp))
        .order_by(func.date(ProductEvent.timestamp))
    )

    result = await db.execute(daily_query)
    rows = result.fetchall()

    # Build timeline with all dates (fill gaps with zeros)
    timeline_dict = {row.event_date.isoformat(): row for row in rows}
    timeline = []

    current_date = start_date
    while current_date <= today:
        date_str = current_date.isoformat()
        if date_str in timeline_dict:
            row = timeline_dict[date_str]
            timeline.append(
                DeprecationTimelineEntry(
                    date=date_str,
                    total_calls=row.total_calls,
                    unique_endpoints=row.unique_endpoints,
                )
            )
        else:
            timeline.append(
                DeprecationTimelineEntry(
                    date=date_str,
                    total_calls=0,
                    unique_endpoints=0,
                )
            )
        current_date += timedelta(days=1)

    return timeline


@router.get("/dashboard", response_model=DeprecationDashboard)
async def get_deprecation_dashboard(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> DeprecationDashboard:
    """
    Get complete deprecation monitoring dashboard.

    Aggregates all deprecation data for a single dashboard view:
    - Summary metrics
    - Per-endpoint usage
    - 30-day timeline
    """
    summary = await get_deprecation_summary(db=db, current_user=current_user)
    endpoints = await get_deprecated_endpoints(db=db, current_user=current_user, category=None)
    timeline = await get_deprecation_timeline(db=db, current_user=current_user, days=30)

    return DeprecationDashboard(
        summary=summary,
        endpoints=endpoints,
        timeline=timeline,
    )
