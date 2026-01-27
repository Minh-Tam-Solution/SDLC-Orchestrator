"""
=========================================================================
Grafana Dashboard Service - Dashboard Configuration Generator
SDLC Orchestrator - Sprint 110 (CEO Dashboard & Observability)

Version: 1.0.0
Date: January 27, 2026
Status: ACTIVE - Sprint 110 Day 5
Authority: CTO + Backend Lead Approved
Framework: SDLC 5.3.0 Quality Assurance System

Purpose:
- Generate Grafana dashboard JSON configurations
- CEO Dashboard: Executive governance intelligence
- Tech Dashboard: Developer experience & performance
- Ops Dashboard: System health & kill switch monitoring

Dashboards:
- CEO Dashboard (5 rows, 15 panels)
- Tech Dashboard (5 rows, 15 panels)
- Ops Dashboard (5 rows, 16 panels)

Zero Mock Policy: Real Prometheus metrics queries
=========================================================================
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
import json


# ============================================================================
# Enums and Constants
# ============================================================================


class DashboardType(str, Enum):
    """Dashboard type identifiers."""
    CEO = "ceo"
    TECH = "tech"
    OPS = "ops"


class PanelType(str, Enum):
    """Grafana panel types."""
    STAT = "stat"
    GAUGE = "gauge"
    PIECHART = "piechart"
    TIMESERIES = "timeseries"
    BARCHART = "barchart"
    TABLE = "table"
    HEATMAP = "heatmap"
    TEXT = "text"
    STATUS_HISTORY = "status-history"


class ThresholdMode(str, Enum):
    """Threshold evaluation mode."""
    ABSOLUTE = "absolute"
    PERCENTAGE = "percentage"


# Vibecoding Index Color Scheme
VIBECODING_COLORS = {
    "green": "#73BF69",   # 0-30: Auto-approve
    "yellow": "#FADE2A",  # 31-60: Tech Lead
    "orange": "#FF9830",  # 61-80: CEO should review
    "red": "#F2495C",     # 81-100: CEO must review
}

# Standard Grafana colors
GRAFANA_COLORS = {
    "green": "#73BF69",
    "yellow": "#FADE2A",
    "orange": "#FF9830",
    "red": "#F2495C",
    "blue": "#5794F2",
    "purple": "#B877D9",
    "super_light_green": "#96D98D",
    "dark_green": "#37872D",
    "dark_red": "#C4162A",
    "white": "#FFFFFF",
}


# ============================================================================
# Data Classes
# ============================================================================


@dataclass
class ThresholdStep:
    """Threshold step for color coding."""
    value: float
    color: str


@dataclass
class GrafanaPanel:
    """Grafana panel configuration."""
    id: int
    title: str
    type: PanelType
    gridPos: Dict[str, int]
    targets: List[Dict[str, Any]]
    fieldConfig: Dict[str, Any] = field(default_factory=dict)
    options: Dict[str, Any] = field(default_factory=dict)
    description: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """Convert panel to Grafana JSON format."""
        panel = {
            "id": self.id,
            "title": self.title,
            "type": self.type.value,
            "gridPos": self.gridPos,
            "targets": self.targets,
            "fieldConfig": self.fieldConfig,
            "options": self.options,
        }
        if self.description:
            panel["description"] = self.description
        return panel


@dataclass
class GrafanaRow:
    """Grafana row configuration."""
    title: str
    collapsed: bool = False
    panels: List[GrafanaPanel] = field(default_factory=list)


@dataclass
class GrafanaDashboard:
    """Complete Grafana dashboard configuration."""
    uid: str
    title: str
    description: str
    tags: List[str]
    panels: List[GrafanaPanel]
    refresh: str = "5s"
    time_from: str = "now-24h"
    time_to: str = "now"
    timezone: str = "browser"
    editable: bool = True
    version: int = 1

    def to_dict(self) -> Dict[str, Any]:
        """Convert dashboard to Grafana JSON format."""
        return {
            "uid": self.uid,
            "title": self.title,
            "description": self.description,
            "tags": self.tags,
            "timezone": self.timezone,
            "editable": self.editable,
            "graphTooltip": 1,
            "refresh": self.refresh,
            "time": {
                "from": self.time_from,
                "to": self.time_to,
            },
            "timepicker": {
                "refresh_intervals": ["5s", "10s", "30s", "1m", "5m", "15m", "30m", "1h"],
                "time_options": ["5m", "15m", "1h", "6h", "12h", "24h", "2d", "7d", "30d"],
            },
            "templating": {"list": []},
            "annotations": {"list": []},
            "panels": [p.to_dict() for p in self.panels],
            "version": self.version,
            "schemaVersion": 39,
        }

    def to_json(self, indent: int = 2) -> str:
        """Export dashboard as JSON string."""
        return json.dumps(self.to_dict(), indent=indent)


# ============================================================================
# Helper Functions
# ============================================================================


def create_prometheus_target(
    expr: str,
    legend_format: str = "",
    ref_id: str = "A",
    instant: bool = False,
) -> Dict[str, Any]:
    """Create Prometheus query target."""
    return {
        "datasource": {"type": "prometheus", "uid": "${datasource}"},
        "expr": expr,
        "legendFormat": legend_format,
        "refId": ref_id,
        "instant": instant,
        "range": not instant,
    }


def create_thresholds(
    steps: List[ThresholdStep],
    mode: ThresholdMode = ThresholdMode.ABSOLUTE,
) -> Dict[str, Any]:
    """Create threshold configuration."""
    return {
        "mode": mode.value,
        "steps": [{"value": s.value, "color": s.color} for s in steps],
    }


def create_stat_panel(
    id: int,
    title: str,
    query: str,
    x: int,
    y: int,
    w: int,
    h: int,
    unit: str = "none",
    thresholds: Optional[List[ThresholdStep]] = None,
    description: str = "",
) -> GrafanaPanel:
    """Create a stat (single value) panel."""
    field_config = {
        "defaults": {
            "color": {"mode": "thresholds"},
            "mappings": [],
            "thresholds": create_thresholds(
                thresholds or [ThresholdStep(0, GRAFANA_COLORS["green"])]
            ),
            "unit": unit,
        },
        "overrides": [],
    }

    return GrafanaPanel(
        id=id,
        title=title,
        type=PanelType.STAT,
        gridPos={"x": x, "y": y, "w": w, "h": h},
        targets=[create_prometheus_target(query, instant=True)],
        fieldConfig=field_config,
        options={
            "colorMode": "value",
            "graphMode": "area",
            "justifyMode": "auto",
            "textMode": "auto",
            "reduceOptions": {
                "calcs": ["lastNotNull"],
                "fields": "",
                "values": False,
            },
        },
        description=description,
    )


def create_gauge_panel(
    id: int,
    title: str,
    query: str,
    x: int,
    y: int,
    w: int,
    h: int,
    min_val: float = 0,
    max_val: float = 100,
    unit: str = "none",
    thresholds: Optional[List[ThresholdStep]] = None,
    description: str = "",
) -> GrafanaPanel:
    """Create a gauge panel."""
    field_config = {
        "defaults": {
            "color": {"mode": "thresholds"},
            "mappings": [],
            "min": min_val,
            "max": max_val,
            "thresholds": create_thresholds(
                thresholds or [ThresholdStep(0, GRAFANA_COLORS["green"])]
            ),
            "unit": unit,
        },
        "overrides": [],
    }

    return GrafanaPanel(
        id=id,
        title=title,
        type=PanelType.GAUGE,
        gridPos={"x": x, "y": y, "w": w, "h": h},
        targets=[create_prometheus_target(query, instant=True)],
        fieldConfig=field_config,
        options={
            "reduceOptions": {
                "calcs": ["lastNotNull"],
                "fields": "",
                "values": False,
            },
            "showThresholdLabels": False,
            "showThresholdMarkers": True,
        },
        description=description,
    )


def create_piechart_panel(
    id: int,
    title: str,
    query: str,
    x: int,
    y: int,
    w: int,
    h: int,
    legend_format: str = "{{routing}}",
    description: str = "",
) -> GrafanaPanel:
    """Create a pie chart panel."""
    return GrafanaPanel(
        id=id,
        title=title,
        type=PanelType.PIECHART,
        gridPos={"x": x, "y": y, "w": w, "h": h},
        targets=[create_prometheus_target(query, legend_format=legend_format)],
        fieldConfig={
            "defaults": {
                "color": {"mode": "palette-classic"},
                "mappings": [],
            },
            "overrides": [
                {"matcher": {"id": "byName", "options": "green"},
                 "properties": [{"id": "color", "value": {"fixedColor": VIBECODING_COLORS["green"], "mode": "fixed"}}]},
                {"matcher": {"id": "byName", "options": "yellow"},
                 "properties": [{"id": "color", "value": {"fixedColor": VIBECODING_COLORS["yellow"], "mode": "fixed"}}]},
                {"matcher": {"id": "byName", "options": "orange"},
                 "properties": [{"id": "color", "value": {"fixedColor": VIBECODING_COLORS["orange"], "mode": "fixed"}}]},
                {"matcher": {"id": "byName", "options": "red"},
                 "properties": [{"id": "color", "value": {"fixedColor": VIBECODING_COLORS["red"], "mode": "fixed"}}]},
            ],
        },
        options={
            "legend": {"displayMode": "list", "placement": "right", "showLegend": True},
            "pieType": "donut",
            "reduceOptions": {
                "calcs": ["lastNotNull"],
                "fields": "",
                "values": False,
            },
            "tooltip": {"mode": "single", "sort": "none"},
        },
        description=description,
    )


def create_timeseries_panel(
    id: int,
    title: str,
    queries: List[Dict[str, str]],
    x: int,
    y: int,
    w: int,
    h: int,
    unit: str = "none",
    thresholds: Optional[List[ThresholdStep]] = None,
    description: str = "",
) -> GrafanaPanel:
    """Create a time series panel with multiple queries."""
    targets = []
    for i, q in enumerate(queries):
        targets.append(create_prometheus_target(
            q["expr"],
            legend_format=q.get("legend", ""),
            ref_id=chr(65 + i),  # A, B, C...
        ))

    field_config = {
        "defaults": {
            "color": {"mode": "palette-classic"},
            "custom": {
                "axisCenteredZero": False,
                "axisColorMode": "text",
                "axisLabel": "",
                "axisPlacement": "auto",
                "barAlignment": 0,
                "drawStyle": "line",
                "fillOpacity": 10,
                "gradientMode": "none",
                "hideFrom": {"legend": False, "tooltip": False, "viz": False},
                "insertNulls": False,
                "lineInterpolation": "linear",
                "lineWidth": 1,
                "pointSize": 5,
                "scaleDistribution": {"type": "linear"},
                "showPoints": "auto",
                "spanNulls": False,
                "stacking": {"group": "A", "mode": "none"},
                "thresholdsStyle": {"mode": "off"},
            },
            "mappings": [],
            "thresholds": create_thresholds(
                thresholds or [ThresholdStep(0, GRAFANA_COLORS["green"])]
            ),
            "unit": unit,
        },
        "overrides": [],
    }

    return GrafanaPanel(
        id=id,
        title=title,
        type=PanelType.TIMESERIES,
        gridPos={"x": x, "y": y, "w": w, "h": h},
        targets=targets,
        fieldConfig=field_config,
        options={
            "legend": {"calcs": [], "displayMode": "list", "placement": "bottom", "showLegend": True},
            "tooltip": {"mode": "single", "sort": "none"},
        },
        description=description,
    )


def create_barchart_panel(
    id: int,
    title: str,
    query: str,
    x: int,
    y: int,
    w: int,
    h: int,
    legend_format: str = "",
    orientation: str = "horizontal",
    description: str = "",
) -> GrafanaPanel:
    """Create a bar chart panel."""
    return GrafanaPanel(
        id=id,
        title=title,
        type=PanelType.BARCHART,
        gridPos={"x": x, "y": y, "w": w, "h": h},
        targets=[create_prometheus_target(query, legend_format=legend_format, instant=True)],
        fieldConfig={
            "defaults": {
                "color": {"mode": "palette-classic"},
                "mappings": [],
                "thresholds": create_thresholds([ThresholdStep(0, GRAFANA_COLORS["blue"])]),
            },
            "overrides": [],
        },
        options={
            "barRadius": 0.1,
            "barWidth": 0.6,
            "groupWidth": 0.7,
            "legend": {"displayMode": "list", "placement": "right", "showLegend": True},
            "orientation": orientation,
            "showValue": "auto",
            "stacking": "none",
            "tooltip": {"mode": "single", "sort": "none"},
            "xTickLabelRotation": 0,
            "xTickLabelSpacing": 0,
        },
        description=description,
    )


def create_table_panel(
    id: int,
    title: str,
    query: str,
    x: int,
    y: int,
    w: int,
    h: int,
    legend_format: str = "",
    description: str = "",
) -> GrafanaPanel:
    """Create a table panel."""
    return GrafanaPanel(
        id=id,
        title=title,
        type=PanelType.TABLE,
        gridPos={"x": x, "y": y, "w": w, "h": h},
        targets=[create_prometheus_target(query, legend_format=legend_format, instant=True)],
        fieldConfig={
            "defaults": {
                "color": {"mode": "thresholds"},
                "mappings": [],
                "thresholds": create_thresholds([ThresholdStep(0, GRAFANA_COLORS["green"])]),
            },
            "overrides": [],
        },
        options={
            "cellHeight": "sm",
            "footer": {"countRows": False, "fields": "", "reducer": ["sum"], "show": False},
            "showHeader": True,
            "sortBy": [{"desc": True, "displayName": "Value"}],
        },
        description=description,
    )


# ============================================================================
# CEO Dashboard
# ============================================================================


def create_ceo_dashboard() -> GrafanaDashboard:
    """
    Create CEO Dashboard configuration.

    Target Audience: CEO, CTO, CPO
    Refresh: Real-time (5s)

    Rows:
    - Row 1: Executive Summary (Time Saved, PRs Auto-Approved, Pending Decisions)
    - Row 2: This Week Summary (Compliance, Index, False Positive, NPS)
    - Row 3: Weekly Trends (Time Saved Trend, Index Distribution)
    - Row 4: Top Issues (Rejection Reasons, CEO Overrides)
    - Row 5: System Health (Uptime, Latency, Kill Switch)
    """
    panels = []
    panel_id = 1

    # -------------------------------------------------------------------------
    # Row 1: Executive Summary (y=0)
    # -------------------------------------------------------------------------

    # Panel 1.1: CEO Time Saved This Week (Gauge)
    panels.append(create_gauge_panel(
        id=panel_id,
        title="CEO Time Saved This Week",
        query="governance_ceo_time_saved_this_week_hours",
        x=0, y=0, w=8, h=8,
        min_val=0, max_val=40,
        unit="h",
        thresholds=[
            ThresholdStep(0, GRAFANA_COLORS["red"]),      # 0-15h: below target
            ThresholdStep(15, GRAFANA_COLORS["yellow"]),  # 15-25h: on track
            ThresholdStep(25, GRAFANA_COLORS["green"]),   # 25-40h: exceeds target
        ],
        description="Hours saved compared to 40h manual baseline. Target: 30h (Week 2), 20h (Week 4), 10h (Week 8)",
    ))
    panel_id += 1

    # Panel 1.2: PRs Auto-Approved (Pie Chart)
    panels.append(create_piechart_panel(
        id=panel_id,
        title="PRs by Routing Category",
        query='sum by (routing) (governance_submissions_total{routing!=""})',
        x=8, y=0, w=8, h=8,
        legend_format="{{routing}}",
        description="Distribution of PRs by Vibecoding Index routing: Green (auto-approve), Yellow (tech lead), Orange (CEO should), Red (CEO must)",
    ))
    panel_id += 1

    # Panel 1.3: Pending CEO Decisions (Stat)
    panels.append(create_stat_panel(
        id=panel_id,
        title="Pending Your Decision",
        query='governance_pending_ceo_decisions',
        x=16, y=0, w=8, h=8,
        unit="none",
        thresholds=[
            ThresholdStep(0, GRAFANA_COLORS["green"]),
            ThresholdStep(3, GRAFANA_COLORS["yellow"]),
            ThresholdStep(5, GRAFANA_COLORS["red"]),
        ],
        description="PRs awaiting CEO review. Click to navigate to PR queue.",
    ))
    panel_id += 1

    # -------------------------------------------------------------------------
    # Row 2: This Week Summary (y=8)
    # -------------------------------------------------------------------------

    # Panel 2.1: Compliance Pass Rate
    panels.append(create_gauge_panel(
        id=panel_id,
        title="Compliance Pass Rate",
        query="governance_compliance_rate * 100",
        x=0, y=8, w=6, h=6,
        min_val=0, max_val=100,
        unit="percent",
        thresholds=[
            ThresholdStep(0, GRAFANA_COLORS["red"]),
            ThresholdStep(50, GRAFANA_COLORS["yellow"]),
            ThresholdStep(70, GRAFANA_COLORS["green"]),
        ],
        description="Percentage of PRs passing governance on first submission. Target: 70% (Week 4), 85% (Week 8)",
    ))
    panel_id += 1

    # Panel 2.2: Vibecoding Index Average
    panels.append(create_gauge_panel(
        id=panel_id,
        title="Vibecoding Index Average",
        query="governance_vibecoding_index_current",
        x=6, y=8, w=6, h=6,
        min_val=0, max_val=100,
        unit="none",
        thresholds=[
            ThresholdStep(0, VIBECODING_COLORS["green"]),
            ThresholdStep(31, VIBECODING_COLORS["yellow"]),
            ThresholdStep(61, VIBECODING_COLORS["orange"]),
            ThresholdStep(81, VIBECODING_COLORS["red"]),
        ],
        description="Average Vibecoding Index across all submissions. Target: <30 (green zone)",
    ))
    panel_id += 1

    # Panel 2.3: False Positive Rate
    panels.append(create_gauge_panel(
        id=panel_id,
        title="False Positive Rate",
        query="governance_false_positive_rate * 100",
        x=12, y=8, w=6, h=6,
        min_val=0, max_val=30,
        unit="percent",
        thresholds=[
            ThresholdStep(0, GRAFANA_COLORS["green"]),
            ThresholdStep(5, GRAFANA_COLORS["yellow"]),
            ThresholdStep(10, GRAFANA_COLORS["red"]),
        ],
        description="Percentage of rejections CEO overrides as incorrect. Target: <10%. Kill switch trigger: >20%",
    ))
    panel_id += 1

    # Panel 2.4: Developer Satisfaction NPS
    panels.append(create_gauge_panel(
        id=panel_id,
        title="Developer Satisfaction (NPS)",
        query="governance_developer_satisfaction_nps",
        x=18, y=8, w=6, h=6,
        min_val=-100, max_val=100,
        unit="none",
        thresholds=[
            ThresholdStep(-100, GRAFANA_COLORS["red"]),
            ThresholdStep(0, GRAFANA_COLORS["yellow"]),
            ThresholdStep(50, GRAFANA_COLORS["green"]),
        ],
        description="Developer NPS score from weekly surveys. Target: >50",
    ))
    panel_id += 1

    # -------------------------------------------------------------------------
    # Row 3: Weekly Trends (y=14)
    # -------------------------------------------------------------------------

    # Panel 3.1: CEO Time Saved Trend
    panels.append(create_timeseries_panel(
        id=panel_id,
        title="CEO Time Saved Trend (8 Weeks)",
        queries=[
            {"expr": "governance_ceo_time_saved_this_week_hours", "legend": "Time Saved (hours)"},
        ],
        x=0, y=14, w=12, h=8,
        unit="h",
        description="Weekly trend of CEO time saved. Baseline: 40h. Targets: 30h (W2), 20h (W4), 10h (W8)",
    ))
    panel_id += 1

    # Panel 3.2: Vibecoding Index Distribution Over Time
    panels.append(create_timeseries_panel(
        id=panel_id,
        title="Vibecoding Index Distribution",
        queries=[
            {"expr": 'sum(governance_submissions_total{routing="green"})', "legend": "Green (Auto-approve)"},
            {"expr": 'sum(governance_submissions_total{routing="yellow"})', "legend": "Yellow (Tech Lead)"},
            {"expr": 'sum(governance_submissions_total{routing="orange"})', "legend": "Orange (CEO should)"},
            {"expr": 'sum(governance_submissions_total{routing="red"})', "legend": "Red (CEO must)"},
        ],
        x=12, y=14, w=12, h=8,
        unit="short",
        description="Distribution of PR routing categories over time",
    ))
    panel_id += 1

    # -------------------------------------------------------------------------
    # Row 4: Top Issues (y=22)
    # -------------------------------------------------------------------------

    # Panel 4.1: Top 5 Rejection Reasons
    panels.append(create_barchart_panel(
        id=panel_id,
        title="Top 5 Rejection Reasons",
        query='topk(5, sum by (reason) (governance_rejection_total))',
        x=0, y=22, w=12, h=8,
        legend_format="{{reason}}",
        orientation="horizontal",
        description="Most common reasons for governance rejections this week",
    ))
    panel_id += 1

    # Panel 4.2: CEO Overrides This Week
    panels.append(create_table_panel(
        id=panel_id,
        title="CEO Overrides This Week",
        query='sum by (override_type, submission_id) (governance_ceo_overrides_total)',
        x=12, y=22, w=12, h=8,
        description="CEO override decisions for index calibration (agrees/disagrees)",
    ))
    panel_id += 1

    # -------------------------------------------------------------------------
    # Row 5: System Health (y=30)
    # -------------------------------------------------------------------------

    # Panel 5.1: System Uptime
    panels.append(create_stat_panel(
        id=panel_id,
        title="System Uptime",
        query="(governance_uptime_seconds / (time() - (time() - 86400))) * 100",
        x=0, y=30, w=6, h=4,
        unit="percent",
        thresholds=[
            ThresholdStep(0, GRAFANA_COLORS["red"]),
            ThresholdStep(95, GRAFANA_COLORS["yellow"]),
            ThresholdStep(99, GRAFANA_COLORS["green"]),
        ],
        description="System uptime percentage. SLO: >99%",
    ))
    panel_id += 1

    # Panel 5.2: API Latency P95
    panels.append(create_stat_panel(
        id=panel_id,
        title="API Latency P95",
        query='histogram_quantile(0.95, sum(rate(governance_api_latency_seconds_bucket[5m])) by (le))',
        x=6, y=30, w=6, h=4,
        unit="s",
        thresholds=[
            ThresholdStep(0, GRAFANA_COLORS["green"]),
            ThresholdStep(0.1, GRAFANA_COLORS["yellow"]),
            ThresholdStep(0.5, GRAFANA_COLORS["red"]),
        ],
        description="95th percentile API latency. SLO: <100ms",
    ))
    panel_id += 1

    # Panel 5.3: Kill Switch Status
    panels.append(create_stat_panel(
        id=panel_id,
        title="Kill Switch Status",
        query="governance_killswitch_triggers_total",
        x=12, y=30, w=6, h=4,
        unit="none",
        thresholds=[
            ThresholdStep(0, GRAFANA_COLORS["green"]),
            ThresholdStep(1, GRAFANA_COLORS["red"]),
        ],
        description="Kill switch trigger count. 0 = Normal operation",
    ))
    panel_id += 1

    # Panel 5.4: Break Glass Activations
    panels.append(create_stat_panel(
        id=panel_id,
        title="Break Glass Activations",
        query="governance_break_glass_activations_total",
        x=18, y=30, w=6, h=4,
        unit="none",
        thresholds=[
            ThresholdStep(0, GRAFANA_COLORS["green"]),
            ThresholdStep(1, GRAFANA_COLORS["yellow"]),
            ThresholdStep(3, GRAFANA_COLORS["red"]),
        ],
        description="Emergency bypass activations this week. Target: <2 per week",
    ))
    panel_id += 1

    return GrafanaDashboard(
        uid="ceo-dashboard",
        title="CEO Dashboard - Governance Intelligence",
        description="Executive governance intelligence dashboard for CEO, CTO, CPO. Real-time visibility into governance effectiveness and team productivity.",
        tags=["governance", "ceo", "executive", "vibecoding"],
        panels=panels,
        refresh="5s",
        time_from="now-7d",
        time_to="now",
    )


# ============================================================================
# Tech Dashboard
# ============================================================================


def create_tech_dashboard() -> GrafanaDashboard:
    """
    Create Tech Dashboard configuration.

    Target Audience: Tech Lead, Backend Lead, DevOps
    Refresh: Every 5 minutes

    Rows:
    - Row 1: Developer Experience (Friction, First Pass, Auto-Gen Usage)
    - Row 2: Vibecoding Index Breakdown (Signal Scores, Routing Distribution)
    - Row 3: System Performance (API Latency, DB Queries)
    - Row 4: Top Violations & Calibration
    - Row 5: LLM & Auto-Generation Health
    """
    panels = []
    panel_id = 1

    # -------------------------------------------------------------------------
    # Row 1: Developer Experience (y=0)
    # -------------------------------------------------------------------------

    # Panel 1.1: Developer Friction Distribution
    panels.append(create_timeseries_panel(
        id=panel_id,
        title="Developer Friction (Time to Comply)",
        queries=[
            {"expr": 'histogram_quantile(0.50, sum(rate(governance_developer_friction_seconds_bucket[5m])) by (le))', "legend": "P50"},
            {"expr": 'histogram_quantile(0.95, sum(rate(governance_developer_friction_seconds_bucket[5m])) by (le))', "legend": "P95"},
            {"expr": 'histogram_quantile(0.99, sum(rate(governance_developer_friction_seconds_bucket[5m])) by (le))', "legend": "P99"},
        ],
        x=0, y=0, w=8, h=8,
        unit="s",
        description="Time developers spend on governance compliance. Target: <5 min (P95). Alert: >10 min",
    ))
    panel_id += 1

    # Panel 1.2: First Pass Rate Trend
    panels.append(create_timeseries_panel(
        id=panel_id,
        title="First Pass Rate Trend",
        queries=[
            {"expr": "(governance_first_submission_pass_total / governance_submissions_total) * 100", "legend": "First Pass Rate %"},
        ],
        x=8, y=0, w=8, h=8,
        unit="percent",
        thresholds=[
            ThresholdStep(0, GRAFANA_COLORS["red"]),
            ThresholdStep(50, GRAFANA_COLORS["yellow"]),
            ThresholdStep(70, GRAFANA_COLORS["green"]),
        ],
        description="Percentage of PRs passing on first submission. Targets: 50% (W2), 70% (W4), 85% (W8)",
    ))
    panel_id += 1

    # Panel 1.3: Auto-Generation Usage
    panels.append(create_piechart_panel(
        id=panel_id,
        title="Auto-Generation Usage by Component",
        query='sum by (component) (governance_auto_generation_total)',
        x=16, y=0, w=8, h=8,
        legend_format="{{component}}",
        description="Usage of auto-generation for compliance artifacts. Target: >80% for all components",
    ))
    panel_id += 1

    # -------------------------------------------------------------------------
    # Row 2: Vibecoding Index Breakdown (y=8)
    # -------------------------------------------------------------------------

    # Panel 2.1: Signal Scores Distribution
    panels.append(create_timeseries_panel(
        id=panel_id,
        title="Signal Scores Over Time (5 Signals)",
        queries=[
            {"expr": 'avg(governance_vibecoding_index{signal="architectural_smell"})', "legend": "Architectural Smell (25%)"},
            {"expr": 'avg(governance_vibecoding_index{signal="abstraction_complexity"})', "legend": "Abstraction Complexity (15%)"},
            {"expr": 'avg(governance_vibecoding_index{signal="ai_dependency_ratio"})', "legend": "AI Dependency (20%)"},
            {"expr": 'avg(governance_vibecoding_index{signal="change_surface_area"})', "legend": "Change Surface Area (20%)"},
            {"expr": 'avg(governance_vibecoding_index{signal="drift_velocity"})', "legend": "Drift Velocity (20%)"},
        ],
        x=0, y=8, w=12, h=8,
        unit="none",
        description="Average scores for each of the 5 Vibecoding Index signals",
    ))
    panel_id += 1

    # Panel 2.2: Vibecoding Index by Routing
    panels.append(create_timeseries_panel(
        id=panel_id,
        title="Submissions by Routing Category",
        queries=[
            {"expr": 'sum(governance_submissions_total{routing="green"})', "legend": "Green (Auto-approve)"},
            {"expr": 'sum(governance_submissions_total{routing="yellow"})', "legend": "Yellow (Tech Lead)"},
            {"expr": 'sum(governance_submissions_total{routing="orange"})', "legend": "Orange (CEO should)"},
            {"expr": 'sum(governance_submissions_total{routing="red"})', "legend": "Red (CEO must)"},
        ],
        x=12, y=8, w=12, h=8,
        unit="short",
        description="PR count by Vibecoding Index routing category",
    ))
    panel_id += 1

    # -------------------------------------------------------------------------
    # Row 3: System Performance (y=16)
    # -------------------------------------------------------------------------

    # Panel 3.1: API Latency by Endpoint
    panels.append(create_table_panel(
        id=panel_id,
        title="API Latency by Endpoint",
        query='histogram_quantile(0.95, sum by (endpoint, le) (rate(governance_api_latency_seconds_bucket[5m])))',
        x=0, y=16, w=12, h=8,
        description="P95 latency per API endpoint. Target: <100ms. Alert: P95 >100ms",
    ))
    panel_id += 1

    # Panel 3.2: Database Query Performance
    panels.append(create_table_panel(
        id=panel_id,
        title="Database Query Performance",
        query='histogram_quantile(0.95, sum by (query_name, le) (rate(governance_database_query_latency_seconds_bucket[5m])))',
        x=12, y=16, w=12, h=8,
        description="P95 latency per database query. Target: <100ms",
    ))
    panel_id += 1

    # -------------------------------------------------------------------------
    # Row 4: Top Violations & Calibration (y=24)
    # -------------------------------------------------------------------------

    # Panel 4.1: Top 10 Governance Violations
    panels.append(create_barchart_panel(
        id=panel_id,
        title="Top 10 Governance Violations",
        query='topk(10, sum by (reason) (governance_rejection_total))',
        x=0, y=24, w=12, h=8,
        legend_format="{{reason}}",
        orientation="horizontal",
        description="Most common governance violations this week",
    ))
    panel_id += 1

    # Panel 4.2: CEO Overrides for Calibration
    panels.append(create_table_panel(
        id=panel_id,
        title="CEO Overrides for Calibration",
        query='sum by (override_type, index_before) (governance_ceo_overrides_total)',
        x=12, y=24, w=12, h=8,
        description="CEO override decisions for Vibecoding Index weight calibration",
    ))
    panel_id += 1

    # -------------------------------------------------------------------------
    # Row 5: LLM & Auto-Generation Health (y=32)
    # -------------------------------------------------------------------------

    # Panel 5.1: LLM Success Rate
    panels.append(create_gauge_panel(
        id=panel_id,
        title="LLM Generation Success Rate",
        query='sum(governance_llm_generation_total{status="success"}) / sum(governance_llm_generation_total) * 100',
        x=0, y=32, w=8, h=6,
        min_val=0, max_val=100,
        unit="percent",
        thresholds=[
            ThresholdStep(0, GRAFANA_COLORS["red"]),
            ThresholdStep(70, GRAFANA_COLORS["yellow"]),
            ThresholdStep(90, GRAFANA_COLORS["green"]),
        ],
        description="LLM generation success rate across all providers. Target: >90%. Alert: <70%",
    ))
    panel_id += 1

    # Panel 5.2: LLM Latency by Provider
    panels.append(create_timeseries_panel(
        id=panel_id,
        title="LLM Latency by Provider",
        queries=[
            {"expr": 'histogram_quantile(0.95, sum by (provider, le) (rate(governance_llm_generation_latency_seconds_bucket[5m])))', "legend": "{{provider}}"},
        ],
        x=8, y=32, w=8, h=6,
        unit="s",
        description="P95 LLM generation latency by provider. Ollama: <10s, Claude: <25s",
    ))
    panel_id += 1

    # Panel 5.3: Auto-Generation Latency
    panels.append(create_timeseries_panel(
        id=panel_id,
        title="Auto-Generation Latency by Component",
        queries=[
            {"expr": 'histogram_quantile(0.95, sum by (component, le) (rate(governance_auto_generation_latency_seconds_bucket[5m])))', "legend": "{{component}}"},
        ],
        x=16, y=32, w=8, h=6,
        unit="s",
        description="Auto-generation latency by component. Intent: <10s, Ownership: <2s, Context: <5s, Attestation: <3s",
    ))
    panel_id += 1

    return GrafanaDashboard(
        uid="tech-dashboard",
        title="Tech Dashboard - Developer Experience & Performance",
        description="Technical dashboard for Tech Lead, Backend Lead, DevOps. Developer experience metrics, system performance, and LLM health.",
        tags=["governance", "tech", "performance", "developer-experience"],
        panels=panels,
        refresh="5m",
        time_from="now-24h",
        time_to="now",
    )


# ============================================================================
# Ops Dashboard
# ============================================================================


def create_ops_dashboard() -> GrafanaDashboard:
    """
    Create Ops Dashboard configuration.

    Target Audience: DevOps, On-Call Engineers
    Refresh: Real-time (5s)

    Rows:
    - Row 1: System Health Overview (Uptime, Latency, Error Rate, Kill Switch)
    - Row 2: Performance Metrics (Request Rate, Latency Percentiles, DB Pool)
    - Row 3: Component Health (OPA, MinIO, Redis, Worker Queue)
    - Row 4: Resource Usage (CPU, Memory, Disk, Network)
    - Row 5: Kill Switch Monitoring (Rejection Rate, False Positive, Complaints)
    """
    panels = []
    panel_id = 1

    # -------------------------------------------------------------------------
    # Row 1: System Health Overview (y=0)
    # -------------------------------------------------------------------------

    # Panel 1.1: Uptime
    panels.append(create_stat_panel(
        id=panel_id,
        title="System Uptime",
        query="(governance_uptime_seconds / (time() - (time() - 86400))) * 100",
        x=0, y=0, w=6, h=6,
        unit="percent",
        thresholds=[
            ThresholdStep(0, GRAFANA_COLORS["red"]),
            ThresholdStep(95, GRAFANA_COLORS["yellow"]),
            ThresholdStep(99, GRAFANA_COLORS["green"]),
        ],
        description="System uptime percentage (24h). SLO: >99%. Page on-call if <99%",
    ))
    panel_id += 1

    # Panel 1.2: API Latency P95
    panels.append(create_gauge_panel(
        id=panel_id,
        title="API Latency P95",
        query='histogram_quantile(0.95, sum(rate(governance_api_latency_seconds_bucket[5m])) by (le)) * 1000',
        x=6, y=0, w=6, h=6,
        min_val=0, max_val=1000,
        unit="ms",
        thresholds=[
            ThresholdStep(0, GRAFANA_COLORS["green"]),
            ThresholdStep(100, GRAFANA_COLORS["yellow"]),
            ThresholdStep(500, GRAFANA_COLORS["red"]),
        ],
        description="95th percentile API latency. SLO: <100ms. Page on-call if >500ms for 5 min",
    ))
    panel_id += 1

    # Panel 1.3: Error Rate
    panels.append(create_stat_panel(
        id=panel_id,
        title="Error Rate (errors/min)",
        query='sum(rate(governance_rejection_total{type="error"}[1m])) * 60',
        x=12, y=0, w=6, h=6,
        unit="none",
        thresholds=[
            ThresholdStep(0, GRAFANA_COLORS["green"]),
            ThresholdStep(5, GRAFANA_COLORS["yellow"]),
            ThresholdStep(10, GRAFANA_COLORS["red"]),
        ],
        description="System errors per minute. Alert: >10 errors/min",
    ))
    panel_id += 1

    # Panel 1.4: Kill Switch Status
    panels.append(create_stat_panel(
        id=panel_id,
        title="Kill Switch Status",
        query="governance_killswitch_triggers_total",
        x=18, y=0, w=6, h=6,
        unit="none",
        thresholds=[
            ThresholdStep(0, GRAFANA_COLORS["green"]),
            ThresholdStep(1, GRAFANA_COLORS["red"]),
        ],
        description="Kill switch status. 0=Normal, 1+=Triggered. Notify CTO+CEO on any change",
    ))
    panel_id += 1

    # -------------------------------------------------------------------------
    # Row 2: Performance Metrics (y=6)
    # -------------------------------------------------------------------------

    # Panel 2.1: API Request Rate
    panels.append(create_timeseries_panel(
        id=panel_id,
        title="API Request Rate (req/s)",
        queries=[
            {"expr": "sum(rate(governance_submissions_total[1m]))", "legend": "Requests/sec"},
        ],
        x=0, y=6, w=8, h=6,
        unit="reqps",
        description="API request rate over last 24 hours",
    ))
    panel_id += 1

    # Panel 2.2: API Latency Percentiles
    panels.append(create_timeseries_panel(
        id=panel_id,
        title="API Latency Percentiles",
        queries=[
            {"expr": 'histogram_quantile(0.50, sum(rate(governance_api_latency_seconds_bucket[5m])) by (le)) * 1000', "legend": "P50"},
            {"expr": 'histogram_quantile(0.95, sum(rate(governance_api_latency_seconds_bucket[5m])) by (le)) * 1000', "legend": "P95"},
            {"expr": 'histogram_quantile(0.99, sum(rate(governance_api_latency_seconds_bucket[5m])) by (le)) * 1000', "legend": "P99"},
        ],
        x=8, y=6, w=8, h=6,
        unit="ms",
        description="API latency percentiles. SLO: P95 <100ms, P99 <500ms",
    ))
    panel_id += 1

    # Panel 2.3: Concurrent Submissions
    panels.append(create_gauge_panel(
        id=panel_id,
        title="Concurrent Submissions",
        query="governance_concurrent_submissions",
        x=16, y=6, w=8, h=6,
        min_val=0, max_val=100,
        unit="none",
        thresholds=[
            ThresholdStep(0, GRAFANA_COLORS["green"]),
            ThresholdStep(50, GRAFANA_COLORS["yellow"]),
            ThresholdStep(80, GRAFANA_COLORS["red"]),
        ],
        description="Current number of concurrent governance submissions",
    ))
    panel_id += 1

    # -------------------------------------------------------------------------
    # Row 3: Component Health (y=12)
    # -------------------------------------------------------------------------

    # Panel 3.1: OPA Evaluation Latency
    panels.append(create_stat_panel(
        id=panel_id,
        title="OPA Evaluation P95",
        query='histogram_quantile(0.95, sum(rate(governance_opa_evaluation_latency_seconds_bucket[5m])) by (le)) * 1000',
        x=0, y=12, w=6, h=5,
        unit="ms",
        thresholds=[
            ThresholdStep(0, GRAFANA_COLORS["green"]),
            ThresholdStep(150, GRAFANA_COLORS["yellow"]),
            ThresholdStep(300, GRAFANA_COLORS["red"]),
        ],
        description="OPA policy evaluation P95 latency. Target: <150ms. Alert: >300ms",
    ))
    panel_id += 1

    # Panel 3.2: MinIO Upload Latency
    panels.append(create_stat_panel(
        id=panel_id,
        title="MinIO Upload P95",
        query='histogram_quantile(0.95, sum(rate(governance_minio_operation_latency_seconds_bucket[5m])) by (le)) * 1000',
        x=6, y=12, w=6, h=5,
        unit="ms",
        thresholds=[
            ThresholdStep(0, GRAFANA_COLORS["green"]),
            ThresholdStep(2000, GRAFANA_COLORS["yellow"]),
            ThresholdStep(5000, GRAFANA_COLORS["red"]),
        ],
        description="MinIO evidence upload P95 latency. Target: <2s (10MB). Alert: >5s",
    ))
    panel_id += 1

    # Panel 3.3: Redis Cache Hit Rate
    panels.append(create_gauge_panel(
        id=panel_id,
        title="Redis Cache Hit Rate",
        query="governance_cache_hit_ratio * 100",
        x=12, y=12, w=6, h=5,
        min_val=0, max_val=100,
        unit="percent",
        thresholds=[
            ThresholdStep(0, GRAFANA_COLORS["red"]),
            ThresholdStep(50, GRAFANA_COLORS["yellow"]),
            ThresholdStep(80, GRAFANA_COLORS["green"]),
        ],
        description="Redis cache hit rate. Target: >80%. Alert: <50%",
    ))
    panel_id += 1

    # Panel 3.4: Queue Depth
    panels.append(create_stat_panel(
        id=panel_id,
        title="Queue Depth",
        query="governance_queue_depth",
        x=18, y=12, w=6, h=5,
        unit="none",
        thresholds=[
            ThresholdStep(0, GRAFANA_COLORS["green"]),
            ThresholdStep(50, GRAFANA_COLORS["yellow"]),
            ThresholdStep(100, GRAFANA_COLORS["red"]),
        ],
        description="Governance processing queue depth. Alert: >100 (add workers)",
    ))
    panel_id += 1

    # -------------------------------------------------------------------------
    # Row 4: Resource Usage (y=17)
    # -------------------------------------------------------------------------

    # Panel 4.1: Active Requests
    panels.append(create_gauge_panel(
        id=panel_id,
        title="Active Requests",
        query="governance_active_requests",
        x=0, y=17, w=6, h=5,
        min_val=0, max_val=100,
        unit="none",
        thresholds=[
            ThresholdStep(0, GRAFANA_COLORS["green"]),
            ThresholdStep(50, GRAFANA_COLORS["yellow"]),
            ThresholdStep(80, GRAFANA_COLORS["red"]),
        ],
        description="Currently active API requests",
    ))
    panel_id += 1

    # Panel 4.2: Database Query Latency
    panels.append(create_stat_panel(
        id=panel_id,
        title="DB Query P95",
        query='histogram_quantile(0.95, sum(rate(governance_database_query_latency_seconds_bucket[5m])) by (le)) * 1000',
        x=6, y=17, w=6, h=5,
        unit="ms",
        thresholds=[
            ThresholdStep(0, GRAFANA_COLORS["green"]),
            ThresholdStep(50, GRAFANA_COLORS["yellow"]),
            ThresholdStep(100, GRAFANA_COLORS["red"]),
        ],
        description="Database query P95 latency. Target: <100ms",
    ))
    panel_id += 1

    # Panel 4.3: Redis Operation Latency
    panels.append(create_stat_panel(
        id=panel_id,
        title="Redis Op P95",
        query='histogram_quantile(0.95, sum(rate(governance_redis_operation_latency_seconds_bucket[5m])) by (le)) * 1000',
        x=12, y=17, w=6, h=5,
        unit="ms",
        thresholds=[
            ThresholdStep(0, GRAFANA_COLORS["green"]),
            ThresholdStep(10, GRAFANA_COLORS["yellow"]),
            ThresholdStep(50, GRAFANA_COLORS["red"]),
        ],
        description="Redis operation P95 latency. Target: <10ms",
    ))
    panel_id += 1

    # Panel 4.4: Error Rate
    panels.append(create_gauge_panel(
        id=panel_id,
        title="Error Rate",
        query="governance_error_rate * 100",
        x=18, y=17, w=6, h=5,
        min_val=0, max_val=10,
        unit="percent",
        thresholds=[
            ThresholdStep(0, GRAFANA_COLORS["green"]),
            ThresholdStep(1, GRAFANA_COLORS["yellow"]),
            ThresholdStep(5, GRAFANA_COLORS["red"]),
        ],
        description="System error rate percentage",
    ))
    panel_id += 1

    # -------------------------------------------------------------------------
    # Row 5: Kill Switch Monitoring (y=22)
    # -------------------------------------------------------------------------

    # Panel 5.1: Rejection Rate
    panels.append(create_gauge_panel(
        id=panel_id,
        title="Rejection Rate",
        query="(sum(governance_rejection_total) / sum(governance_submissions_total)) * 100",
        x=0, y=22, w=6, h=6,
        min_val=0, max_val=100,
        unit="percent",
        thresholds=[
            ThresholdStep(0, GRAFANA_COLORS["green"]),
            ThresholdStep(50, GRAFANA_COLORS["yellow"]),
            ThresholdStep(80, GRAFANA_COLORS["red"]),
        ],
        description="Governance rejection rate. KILL SWITCH TRIGGER: >80%",
    ))
    panel_id += 1

    # Panel 5.2: False Positive Rate
    panels.append(create_gauge_panel(
        id=panel_id,
        title="False Positive Rate",
        query="governance_false_positive_rate * 100",
        x=6, y=22, w=6, h=6,
        min_val=0, max_val=30,
        unit="percent",
        thresholds=[
            ThresholdStep(0, GRAFANA_COLORS["green"]),
            ThresholdStep(10, GRAFANA_COLORS["yellow"]),
            ThresholdStep(20, GRAFANA_COLORS["red"]),
        ],
        description="False positive rate. KILL SWITCH TRIGGER: >20%",
    ))
    panel_id += 1

    # Panel 5.3: Bypass Incidents
    panels.append(create_stat_panel(
        id=panel_id,
        title="Bypass Incidents",
        query="governance_bypass_incidents_total",
        x=12, y=22, w=6, h=6,
        unit="none",
        thresholds=[
            ThresholdStep(0, GRAFANA_COLORS["green"]),
            ThresholdStep(1, GRAFANA_COLORS["red"]),
        ],
        description="Unauthorized governance bypass attempts. Alert on >0",
    ))
    panel_id += 1

    # Panel 5.4: Kill Switch Trigger History
    panels.append(create_table_panel(
        id=panel_id,
        title="Kill Switch Trigger History",
        query='sum by (trigger_reason, timestamp) (governance_killswitch_triggers_total)',
        x=18, y=22, w=6, h=6,
        description="History of kill switch trigger events with reasons",
    ))
    panel_id += 1

    return GrafanaDashboard(
        uid="ops-dashboard",
        title="Ops Dashboard - System Health & Kill Switch",
        description="Operations dashboard for DevOps and On-Call engineers. Real-time system health, performance metrics, and kill switch monitoring.",
        tags=["governance", "ops", "devops", "kill-switch", "health"],
        panels=panels,
        refresh="5s",
        time_from="now-24h",
        time_to="now",
    )


# ============================================================================
# Dashboard Service
# ============================================================================


class GrafanaDashboardService:
    """
    Service for generating and managing Grafana dashboard configurations.

    Provides:
    - CEO Dashboard: Executive governance intelligence
    - Tech Dashboard: Developer experience & performance
    - Ops Dashboard: System health & kill switch monitoring
    """

    def __init__(self):
        """Initialize the dashboard service."""
        self._dashboards: Dict[DashboardType, GrafanaDashboard] = {}
        self._initialized = False

    def initialize(self) -> None:
        """Initialize all dashboards."""
        if self._initialized:
            return

        self._dashboards = {
            DashboardType.CEO: create_ceo_dashboard(),
            DashboardType.TECH: create_tech_dashboard(),
            DashboardType.OPS: create_ops_dashboard(),
        }
        self._initialized = True

    def get_dashboard(self, dashboard_type: DashboardType) -> GrafanaDashboard:
        """
        Get a dashboard by type.

        Args:
            dashboard_type: Type of dashboard to retrieve

        Returns:
            GrafanaDashboard configuration
        """
        if not self._initialized:
            self.initialize()

        return self._dashboards[dashboard_type]

    def get_dashboard_json(self, dashboard_type: DashboardType) -> str:
        """
        Get dashboard configuration as JSON string.

        Args:
            dashboard_type: Type of dashboard

        Returns:
            JSON string of dashboard configuration
        """
        dashboard = self.get_dashboard(dashboard_type)
        return dashboard.to_json()

    def get_dashboard_dict(self, dashboard_type: DashboardType) -> Dict[str, Any]:
        """
        Get dashboard configuration as dictionary.

        Args:
            dashboard_type: Type of dashboard

        Returns:
            Dictionary of dashboard configuration
        """
        dashboard = self.get_dashboard(dashboard_type)
        return dashboard.to_dict()

    def get_all_dashboards(self) -> Dict[DashboardType, GrafanaDashboard]:
        """
        Get all dashboard configurations.

        Returns:
            Dictionary mapping dashboard types to configurations
        """
        if not self._initialized:
            self.initialize()

        return self._dashboards.copy()

    def export_all_dashboards(self, output_dir: str = "backend/grafana/dashboards") -> List[str]:
        """
        Export all dashboards to JSON files.

        Args:
            output_dir: Directory to write dashboard files

        Returns:
            List of exported file paths
        """
        import os

        if not self._initialized:
            self.initialize()

        os.makedirs(output_dir, exist_ok=True)
        exported_files = []

        for dashboard_type, dashboard in self._dashboards.items():
            filename = f"{dashboard_type.value}-dashboard.json"
            filepath = os.path.join(output_dir, filename)

            with open(filepath, "w") as f:
                f.write(dashboard.to_json())

            exported_files.append(filepath)

        return exported_files


# ============================================================================
# Factory Functions
# ============================================================================


_grafana_dashboard_service: Optional[GrafanaDashboardService] = None


def create_grafana_dashboard_service() -> GrafanaDashboardService:
    """
    Factory function to create a new GrafanaDashboardService instance.

    Returns:
        New GrafanaDashboardService instance
    """
    service = GrafanaDashboardService()
    service.initialize()
    return service


def get_grafana_dashboard_service() -> GrafanaDashboardService:
    """
    Get the singleton GrafanaDashboardService instance.

    Returns:
        Singleton GrafanaDashboardService instance
    """
    global _grafana_dashboard_service

    if _grafana_dashboard_service is None:
        _grafana_dashboard_service = create_grafana_dashboard_service()

    return _grafana_dashboard_service


# ============================================================================
# Export JSON Files on Module Load
# ============================================================================


def export_dashboards_to_files() -> None:
    """Export all dashboards to JSON files in backend/grafana/dashboards/."""
    service = get_grafana_dashboard_service()
    exported = service.export_all_dashboards()
    print(f"Exported {len(exported)} Grafana dashboards: {exported}")
