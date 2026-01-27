"""
=========================================================================
Grafana Dashboards API - Dashboard Configuration Endpoints
SDLC Orchestrator - Sprint 110 (CEO Dashboard & Observability)

Version: 1.0.0
Date: January 27, 2026
Status: ACTIVE - Sprint 110 Day 5
Authority: CTO + Backend Lead Approved
Framework: SDLC 5.3.0 Quality Assurance System

Endpoints:
- GET /grafana-dashboards: List all available dashboards
- GET /grafana-dashboards/{type}: Get specific dashboard configuration
- GET /grafana-dashboards/{type}/json: Get dashboard as JSON file
- GET /grafana-dashboards/{type}/panels: List panels in a dashboard
- POST /grafana-dashboards/provision: Provision all dashboards to Grafana

Zero Mock Policy: Real Grafana-compatible JSON configurations
=========================================================================
"""

from enum import Enum
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Query, Response
from pydantic import BaseModel, Field

from app.services.governance.grafana_dashboards import (
    DashboardType,
    GrafanaDashboardService,
    get_grafana_dashboard_service,
)


# ============================================================================
# Router Configuration
# ============================================================================


router = APIRouter(prefix="/grafana-dashboards")


# ============================================================================
# Request/Response Models
# ============================================================================


class DashboardInfo(BaseModel):
    """Dashboard metadata information."""
    uid: str = Field(..., description="Unique dashboard identifier")
    title: str = Field(..., description="Dashboard title")
    description: str = Field(..., description="Dashboard description")
    type: str = Field(..., description="Dashboard type (ceo, tech, ops)")
    tags: List[str] = Field(..., description="Dashboard tags")
    panel_count: int = Field(..., description="Number of panels in dashboard")
    refresh: str = Field(..., description="Auto-refresh interval")
    time_from: str = Field(..., description="Default time range start")
    time_to: str = Field(..., description="Default time range end")


class DashboardListResponse(BaseModel):
    """Response for listing all dashboards."""
    dashboards: List[DashboardInfo]
    total: int


class PanelInfo(BaseModel):
    """Panel metadata information."""
    id: int = Field(..., description="Panel ID")
    title: str = Field(..., description="Panel title")
    type: str = Field(..., description="Panel type (stat, gauge, timeseries, etc)")
    description: str = Field("", description="Panel description")
    row: int = Field(..., description="Row number (based on y position)")
    position: Dict[str, int] = Field(..., description="Grid position (x, y, w, h)")


class DashboardPanelsResponse(BaseModel):
    """Response for listing dashboard panels."""
    dashboard_uid: str
    dashboard_title: str
    panels: List[PanelInfo]
    total_panels: int


class ProvisionRequest(BaseModel):
    """Request for provisioning dashboards to Grafana."""
    grafana_url: str = Field(
        default="http://localhost:3000",
        description="Grafana server URL"
    )
    api_key: Optional[str] = Field(
        default=None,
        description="Grafana API key (optional if using basic auth)"
    )
    folder_id: int = Field(
        default=0,
        description="Grafana folder ID to store dashboards (0 = General)"
    )
    overwrite: bool = Field(
        default=True,
        description="Overwrite existing dashboards with same UID"
    )


class ProvisionResponse(BaseModel):
    """Response for dashboard provisioning."""
    success: bool
    provisioned: List[str]
    failed: List[Dict[str, str]]
    message: str


# ============================================================================
# Helper Functions
# ============================================================================


def get_dashboard_type(type_str: str) -> DashboardType:
    """
    Convert string to DashboardType enum.

    Args:
        type_str: Dashboard type string (ceo, tech, ops)

    Returns:
        DashboardType enum value

    Raises:
        HTTPException: If invalid type provided
    """
    type_mapping = {
        "ceo": DashboardType.CEO,
        "tech": DashboardType.TECH,
        "ops": DashboardType.OPS,
    }

    type_lower = type_str.lower()
    if type_lower not in type_mapping:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid dashboard type: {type_str}. Valid types: ceo, tech, ops"
        )

    return type_mapping[type_lower]


def calculate_row(y_position: int) -> int:
    """Calculate row number from y position (assuming 6-8 height rows)."""
    if y_position < 8:
        return 1
    elif y_position < 14:
        return 2
    elif y_position < 22:
        return 3
    elif y_position < 30:
        return 4
    else:
        return 5


# ============================================================================
# Endpoints
# ============================================================================


@router.get(
    "",
    response_model=DashboardListResponse,
    summary="List all Grafana dashboards",
    description="Get metadata for all available Grafana dashboard configurations."
)
async def list_dashboards() -> DashboardListResponse:
    """
    List all available Grafana dashboards.

    Returns:
        DashboardListResponse with all dashboard metadata
    """
    service = get_grafana_dashboard_service()
    dashboards = service.get_all_dashboards()

    dashboard_list = []
    for dash_type, dashboard in dashboards.items():
        dashboard_list.append(DashboardInfo(
            uid=dashboard.uid,
            title=dashboard.title,
            description=dashboard.description,
            type=dash_type.value,
            tags=dashboard.tags,
            panel_count=len(dashboard.panels),
            refresh=dashboard.refresh,
            time_from=dashboard.time_from,
            time_to=dashboard.time_to,
        ))

    return DashboardListResponse(
        dashboards=dashboard_list,
        total=len(dashboard_list),
    )


@router.get(
    "/{dashboard_type}",
    response_model=Dict[str, Any],
    summary="Get dashboard configuration",
    description="Get complete Grafana dashboard configuration in JSON format."
)
async def get_dashboard(dashboard_type: str) -> Dict[str, Any]:
    """
    Get a specific dashboard configuration.

    Args:
        dashboard_type: Dashboard type (ceo, tech, ops)

    Returns:
        Complete dashboard configuration as JSON
    """
    dash_type = get_dashboard_type(dashboard_type)
    service = get_grafana_dashboard_service()
    dashboard = service.get_dashboard(dash_type)

    return dashboard.to_dict()


@router.get(
    "/{dashboard_type}/json",
    summary="Download dashboard JSON",
    description="Download dashboard configuration as a JSON file for Grafana import."
)
async def download_dashboard_json(dashboard_type: str) -> Response:
    """
    Download dashboard configuration as JSON file.

    Args:
        dashboard_type: Dashboard type (ceo, tech, ops)

    Returns:
        JSON file response for download
    """
    dash_type = get_dashboard_type(dashboard_type)
    service = get_grafana_dashboard_service()
    json_content = service.get_dashboard_json(dash_type)

    return Response(
        content=json_content,
        media_type="application/json",
        headers={
            "Content-Disposition": f'attachment; filename="{dash_type.value}-dashboard.json"'
        }
    )


@router.get(
    "/{dashboard_type}/panels",
    response_model=DashboardPanelsResponse,
    summary="List dashboard panels",
    description="Get metadata for all panels in a specific dashboard."
)
async def list_dashboard_panels(dashboard_type: str) -> DashboardPanelsResponse:
    """
    List all panels in a specific dashboard.

    Args:
        dashboard_type: Dashboard type (ceo, tech, ops)

    Returns:
        DashboardPanelsResponse with panel metadata
    """
    dash_type = get_dashboard_type(dashboard_type)
    service = get_grafana_dashboard_service()
    dashboard = service.get_dashboard(dash_type)

    panels = []
    for panel in dashboard.panels:
        panel_dict = panel.to_dict()
        grid_pos = panel_dict.get("gridPos", {})

        panels.append(PanelInfo(
            id=panel.id,
            title=panel.title,
            type=panel.type.value,
            description=panel.description,
            row=calculate_row(grid_pos.get("y", 0)),
            position=grid_pos,
        ))

    return DashboardPanelsResponse(
        dashboard_uid=dashboard.uid,
        dashboard_title=dashboard.title,
        panels=panels,
        total_panels=len(panels),
    )


@router.post(
    "/provision",
    response_model=ProvisionResponse,
    summary="Provision dashboards to Grafana",
    description="Provision all dashboard configurations to a Grafana instance via API."
)
async def provision_dashboards(
    request: ProvisionRequest
) -> ProvisionResponse:
    """
    Provision all dashboards to Grafana.

    This endpoint uses the Grafana HTTP API to create/update dashboards.

    Args:
        request: Provisioning configuration

    Returns:
        ProvisionResponse with provisioning results

    Note:
        Requires either:
        - Grafana API key with Editor/Admin permissions
        - Basic auth credentials in grafana_url
    """
    import httpx

    service = get_grafana_dashboard_service()
    dashboards = service.get_all_dashboards()

    provisioned = []
    failed = []

    headers = {"Content-Type": "application/json"}
    if request.api_key:
        headers["Authorization"] = f"Bearer {request.api_key}"

    async with httpx.AsyncClient() as client:
        for dash_type, dashboard in dashboards.items():
            try:
                # Grafana API expects dashboard wrapped in a specific structure
                payload = {
                    "dashboard": dashboard.to_dict(),
                    "folderId": request.folder_id,
                    "overwrite": request.overwrite,
                    "message": f"Provisioned by SDLC Orchestrator Sprint 110"
                }

                response = await client.post(
                    f"{request.grafana_url}/api/dashboards/db",
                    json=payload,
                    headers=headers,
                    timeout=30.0,
                )

                if response.status_code in (200, 201):
                    provisioned.append(dashboard.uid)
                else:
                    failed.append({
                        "uid": dashboard.uid,
                        "error": f"HTTP {response.status_code}: {response.text}"
                    })

            except Exception as e:
                failed.append({
                    "uid": dashboard.uid,
                    "error": str(e)
                })

    success = len(failed) == 0
    message = (
        f"Successfully provisioned {len(provisioned)} dashboards"
        if success else
        f"Provisioned {len(provisioned)} dashboards, {len(failed)} failed"
    )

    return ProvisionResponse(
        success=success,
        provisioned=provisioned,
        failed=failed,
        message=message,
    )


@router.get(
    "/export/all",
    summary="Export all dashboards",
    description="Export all dashboard configurations as a single JSON array."
)
async def export_all_dashboards() -> List[Dict[str, Any]]:
    """
    Export all dashboards as a JSON array.

    Returns:
        List of all dashboard configurations
    """
    service = get_grafana_dashboard_service()
    dashboards = service.get_all_dashboards()

    return [dashboard.to_dict() for dashboard in dashboards.values()]


@router.get(
    "/datasource/template",
    summary="Get Prometheus datasource template",
    description="Get Prometheus datasource configuration template for Grafana."
)
async def get_datasource_template() -> Dict[str, Any]:
    """
    Get Prometheus datasource configuration template.

    Returns:
        Grafana datasource configuration for Prometheus
    """
    return {
        "name": "Prometheus-SDLC",
        "type": "prometheus",
        "access": "proxy",
        "url": "http://prometheus:9090",
        "isDefault": True,
        "editable": True,
        "jsonData": {
            "httpMethod": "POST",
            "timeInterval": "5s",
            "queryTimeout": "30s",
        },
        "secureJsonData": {},
        "uid": "prometheus-sdlc",
    }
