#!/usr/bin/env python3
"""
=========================================================================
Monitoring Configuration Generator
SDLC Orchestrator - Sprint 121 (Production Deployment)

Version: 1.0.0
Date: January 29, 2026
Status: ACTIVE - Sprint 121 Day 1-2
Authority: DevOps Lead + CTO Approved
Framework: SDLC 5.3.0 Quality Assurance System

Purpose:
- Generate Prometheus alerting rules
- Generate Grafana dashboard configurations
- Configure PagerDuty/Slack integrations
- Set up SLO/SLA monitoring

Monitoring Stack:
- Prometheus: Metrics collection and alerting
- Grafana: Visualization and dashboards
- PagerDuty: Incident management
- Slack: Team notifications

Usage:
    python monitoring_config.py --generate-all
    python monitoring_config.py --prometheus-rules
    python monitoring_config.py --grafana-dashboards
    python monitoring_config.py --alerts

Zero Mock Policy: Real monitoring configurations
=========================================================================
"""

import argparse
import json
import os
import yaml
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional


# ============================================================================
# Configuration
# ============================================================================


@dataclass
class AlertRule:
    """Prometheus alert rule definition."""
    name: str
    expr: str
    for_duration: str
    severity: str
    summary: str
    description: str
    labels: Dict[str, str] = field(default_factory=dict)
    annotations: Dict[str, str] = field(default_factory=dict)


@dataclass
class GrafanaPanel:
    """Grafana dashboard panel definition."""
    title: str
    type: str
    query: str
    unit: str = ""
    thresholds: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SLOConfig:
    """Service Level Objective configuration."""
    name: str
    target: float
    metric: str
    window: str = "30d"


# ============================================================================
# Prometheus Alert Rules
# ============================================================================


ALERT_RULES: List[AlertRule] = [
    # API Latency Alerts
    AlertRule(
        name="HighAPILatency",
        expr='histogram_quantile(0.95, sum(rate(http_request_duration_seconds_bucket{job="sdlc-orchestrator"}[5m])) by (le)) > 0.1',
        for_duration="5m",
        severity="warning",
        summary="High API latency detected",
        description="95th percentile API latency is above 100ms for 5 minutes",
        labels={"team": "backend", "service": "api"},
    ),
    AlertRule(
        name="CriticalAPILatency",
        expr='histogram_quantile(0.99, sum(rate(http_request_duration_seconds_bucket{job="sdlc-orchestrator"}[5m])) by (le)) > 0.5',
        for_duration="3m",
        severity="critical",
        summary="Critical API latency",
        description="99th percentile API latency is above 500ms for 3 minutes",
        labels={"team": "backend", "service": "api"},
    ),
    # Error Rate Alerts
    AlertRule(
        name="HighErrorRate",
        expr='sum(rate(http_requests_total{job="sdlc-orchestrator", status=~"5.."}[5m])) / sum(rate(http_requests_total{job="sdlc-orchestrator"}[5m])) > 0.05',
        for_duration="5m",
        severity="warning",
        summary="High error rate",
        description="Error rate is above 5% for 5 minutes",
        labels={"team": "backend", "service": "api"},
    ),
    AlertRule(
        name="CriticalErrorRate",
        expr='sum(rate(http_requests_total{job="sdlc-orchestrator", status=~"5.."}[5m])) / sum(rate(http_requests_total{job="sdlc-orchestrator"}[5m])) > 0.10',
        for_duration="3m",
        severity="critical",
        summary="Critical error rate",
        description="Error rate is above 10% for 3 minutes",
        labels={"team": "backend", "service": "api"},
    ),
    # Gate Evaluation Alerts
    AlertRule(
        name="GateEvaluationSlow",
        expr='histogram_quantile(0.95, sum(rate(gate_evaluation_duration_seconds_bucket[5m])) by (le)) > 0.2',
        for_duration="5m",
        severity="warning",
        summary="Gate evaluation is slow",
        description="Gate evaluation 95th percentile is above 200ms",
        labels={"team": "backend", "service": "gates"},
    ),
    AlertRule(
        name="GateEvaluationFailing",
        expr='sum(rate(gate_evaluation_errors_total[5m])) > 0.1',
        for_duration="5m",
        severity="warning",
        summary="Gate evaluations are failing",
        description="Gate evaluation error rate is above 10%",
        labels={"team": "backend", "service": "gates"},
    ),
    # Context Authority Alerts
    AlertRule(
        name="ContextValidationSlow",
        expr='histogram_quantile(0.95, sum(rate(context_validation_duration_seconds_bucket[5m])) by (le)) > 0.5',
        for_duration="5m",
        severity="warning",
        summary="Context validation is slow",
        description="Context validation 95th percentile is above 500ms",
        labels={"team": "backend", "service": "context_authority"},
    ),
    AlertRule(
        name="HighVibecodingIndex",
        expr='avg(vibecoding_index_current) > 60',
        for_duration="15m",
        severity="warning",
        summary="High average vibecoding index",
        description="Average vibecoding index is in YELLOW/ORANGE zone",
        labels={"team": "governance", "service": "vibecoding"},
    ),
    # Database Alerts
    AlertRule(
        name="DatabaseConnectionPoolExhausted",
        expr='pg_stat_activity_count{datname="sdlc_orchestrator"} / pg_settings_max_connections{datname="sdlc_orchestrator"} > 0.8',
        for_duration="5m",
        severity="warning",
        summary="Database connection pool near exhaustion",
        description="More than 80% of database connections are in use",
        labels={"team": "backend", "service": "database"},
    ),
    AlertRule(
        name="DatabaseSlowQueries",
        expr='rate(pg_stat_statements_seconds_total{queryid!=""}[5m]) / rate(pg_stat_statements_calls_total{queryid!=""}[5m]) > 0.1',
        for_duration="5m",
        severity="warning",
        summary="Slow database queries detected",
        description="Average query time is above 100ms",
        labels={"team": "backend", "service": "database"},
    ),
    # Redis Alerts
    AlertRule(
        name="RedisCacheHitRateLow",
        expr='redis_keyspace_hits_total / (redis_keyspace_hits_total + redis_keyspace_misses_total) < 0.8',
        for_duration="15m",
        severity="warning",
        summary="Redis cache hit rate is low",
        description="Cache hit rate is below 80%",
        labels={"team": "backend", "service": "redis"},
    ),
    AlertRule(
        name="RedisMemoryHigh",
        expr='redis_memory_used_bytes / redis_memory_max_bytes > 0.9',
        for_duration="5m",
        severity="warning",
        summary="Redis memory usage is high",
        description="Redis is using more than 90% of max memory",
        labels={"team": "backend", "service": "redis"},
    ),
    # OPA Alerts
    AlertRule(
        name="OPAEvaluationErrors",
        expr='sum(rate(opa_evaluation_errors_total[5m])) > 0',
        for_duration="5m",
        severity="warning",
        summary="OPA policy evaluation errors",
        description="OPA is returning evaluation errors",
        labels={"team": "backend", "service": "opa"},
    ),
    AlertRule(
        name="OPAUnavailable",
        expr='up{job="opa"} == 0',
        for_duration="1m",
        severity="critical",
        summary="OPA service is down",
        description="OPA service is not responding",
        labels={"team": "backend", "service": "opa"},
    ),
    # Kubernetes Alerts
    AlertRule(
        name="PodCrashLooping",
        expr='kube_pod_container_status_restarts_total{namespace="sdlc"} > 5',
        for_duration="15m",
        severity="critical",
        summary="Pod is crash looping",
        description="Pod has restarted more than 5 times in 15 minutes",
        labels={"team": "devops", "service": "kubernetes"},
    ),
    AlertRule(
        name="PodNotReady",
        expr='kube_pod_status_ready{namespace="sdlc", condition="true"} == 0',
        for_duration="5m",
        severity="warning",
        summary="Pod not ready",
        description="Pod has not been ready for 5 minutes",
        labels={"team": "devops", "service": "kubernetes"},
    ),
]


# ============================================================================
# SLO Definitions
# ============================================================================


SLOS: List[SLOConfig] = [
    SLOConfig(
        name="API Availability",
        target=99.9,
        metric='sum(rate(http_requests_total{job="sdlc-orchestrator", status!~"5.."}[30d])) / sum(rate(http_requests_total{job="sdlc-orchestrator"}[30d])) * 100',
        window="30d",
    ),
    SLOConfig(
        name="API Latency p95",
        target=100,  # 100ms
        metric='histogram_quantile(0.95, sum(rate(http_request_duration_seconds_bucket{job="sdlc-orchestrator"}[30d])) by (le)) * 1000',
        window="30d",
    ),
    SLOConfig(
        name="Gate Evaluation Success",
        target=99.0,
        metric='sum(rate(gate_evaluation_success_total[30d])) / sum(rate(gate_evaluation_total[30d])) * 100',
        window="30d",
    ),
    SLOConfig(
        name="Evidence Upload Success",
        target=99.5,
        metric='sum(rate(evidence_upload_success_total[30d])) / sum(rate(evidence_upload_total[30d])) * 100',
        window="30d",
    ),
]


# ============================================================================
# Grafana Dashboard Definitions
# ============================================================================


def generate_grafana_dashboard() -> Dict[str, Any]:
    """Generate Grafana dashboard JSON."""
    return {
        "title": "SDLC Orchestrator - Production Overview",
        "uid": "sdlc-prod-overview",
        "tags": ["sdlc", "production", "orchestrator"],
        "timezone": "browser",
        "refresh": "30s",
        "time": {"from": "now-1h", "to": "now"},
        "panels": [
            # Row 1: Key Metrics
            {
                "id": 1,
                "title": "Request Rate",
                "type": "stat",
                "gridPos": {"h": 4, "w": 4, "x": 0, "y": 0},
                "targets": [
                    {
                        "expr": 'sum(rate(http_requests_total{job="sdlc-orchestrator"}[5m]))',
                        "legendFormat": "Requests/sec",
                    }
                ],
            },
            {
                "id": 2,
                "title": "Error Rate",
                "type": "stat",
                "gridPos": {"h": 4, "w": 4, "x": 4, "y": 0},
                "targets": [
                    {
                        "expr": 'sum(rate(http_requests_total{job="sdlc-orchestrator", status=~"5.."}[5m])) / sum(rate(http_requests_total{job="sdlc-orchestrator"}[5m])) * 100',
                        "legendFormat": "Error %",
                    }
                ],
                "thresholds": {
                    "steps": [
                        {"color": "green", "value": None},
                        {"color": "yellow", "value": 1},
                        {"color": "red", "value": 5},
                    ]
                },
            },
            {
                "id": 3,
                "title": "P95 Latency",
                "type": "stat",
                "gridPos": {"h": 4, "w": 4, "x": 8, "y": 0},
                "targets": [
                    {
                        "expr": 'histogram_quantile(0.95, sum(rate(http_request_duration_seconds_bucket{job="sdlc-orchestrator"}[5m])) by (le)) * 1000',
                        "legendFormat": "ms",
                    }
                ],
                "thresholds": {
                    "steps": [
                        {"color": "green", "value": None},
                        {"color": "yellow", "value": 100},
                        {"color": "red", "value": 200},
                    ]
                },
            },
            {
                "id": 4,
                "title": "Active Gates",
                "type": "stat",
                "gridPos": {"h": 4, "w": 4, "x": 12, "y": 0},
                "targets": [
                    {
                        "expr": 'sum(gates_active_total)',
                        "legendFormat": "Gates",
                    }
                ],
            },
            {
                "id": 5,
                "title": "Vibecoding Index (Avg)",
                "type": "gauge",
                "gridPos": {"h": 4, "w": 4, "x": 16, "y": 0},
                "targets": [
                    {
                        "expr": 'avg(vibecoding_index_current)',
                        "legendFormat": "Index",
                    }
                ],
                "fieldConfig": {
                    "defaults": {
                        "max": 100,
                        "min": 0,
                        "thresholds": {
                            "steps": [
                                {"color": "green", "value": None},
                                {"color": "yellow", "value": 30},
                                {"color": "orange", "value": 60},
                                {"color": "red", "value": 80},
                            ]
                        },
                    }
                },
            },
            {
                "id": 6,
                "title": "Active Projects",
                "type": "stat",
                "gridPos": {"h": 4, "w": 4, "x": 20, "y": 0},
                "targets": [
                    {
                        "expr": 'sum(projects_active_total)',
                        "legendFormat": "Projects",
                    }
                ],
            },
            # Row 2: Time Series
            {
                "id": 7,
                "title": "Request Rate by Endpoint",
                "type": "timeseries",
                "gridPos": {"h": 8, "w": 12, "x": 0, "y": 4},
                "targets": [
                    {
                        "expr": 'sum(rate(http_requests_total{job="sdlc-orchestrator"}[5m])) by (handler)',
                        "legendFormat": "{{handler}}",
                    }
                ],
            },
            {
                "id": 8,
                "title": "Latency Distribution",
                "type": "timeseries",
                "gridPos": {"h": 8, "w": 12, "x": 12, "y": 4},
                "targets": [
                    {
                        "expr": 'histogram_quantile(0.50, sum(rate(http_request_duration_seconds_bucket{job="sdlc-orchestrator"}[5m])) by (le)) * 1000',
                        "legendFormat": "p50",
                    },
                    {
                        "expr": 'histogram_quantile(0.95, sum(rate(http_request_duration_seconds_bucket{job="sdlc-orchestrator"}[5m])) by (le)) * 1000',
                        "legendFormat": "p95",
                    },
                    {
                        "expr": 'histogram_quantile(0.99, sum(rate(http_request_duration_seconds_bucket{job="sdlc-orchestrator"}[5m])) by (le)) * 1000',
                        "legendFormat": "p99",
                    },
                ],
            },
            # Row 3: Gate Metrics
            {
                "id": 9,
                "title": "Gate Evaluations",
                "type": "timeseries",
                "gridPos": {"h": 8, "w": 8, "x": 0, "y": 12},
                "targets": [
                    {
                        "expr": 'sum(rate(gate_evaluation_total[5m])) by (gate_code)',
                        "legendFormat": "{{gate_code}}",
                    }
                ],
            },
            {
                "id": 10,
                "title": "Gate Pass Rate",
                "type": "timeseries",
                "gridPos": {"h": 8, "w": 8, "x": 8, "y": 12},
                "targets": [
                    {
                        "expr": 'sum(rate(gate_evaluation_success_total[5m])) / sum(rate(gate_evaluation_total[5m])) * 100',
                        "legendFormat": "Pass Rate %",
                    }
                ],
            },
            {
                "id": 11,
                "title": "Vibecoding Index Distribution",
                "type": "piechart",
                "gridPos": {"h": 8, "w": 8, "x": 16, "y": 12},
                "targets": [
                    {
                        "expr": 'sum(vibecoding_zone_total{zone="green"})',
                        "legendFormat": "GREEN (0-30)",
                    },
                    {
                        "expr": 'sum(vibecoding_zone_total{zone="yellow"})',
                        "legendFormat": "YELLOW (31-60)",
                    },
                    {
                        "expr": 'sum(vibecoding_zone_total{zone="orange"})',
                        "legendFormat": "ORANGE (61-80)",
                    },
                    {
                        "expr": 'sum(vibecoding_zone_total{zone="red"})',
                        "legendFormat": "RED (81-100)",
                    },
                ],
            },
        ],
    }


# ============================================================================
# Configuration Generators
# ============================================================================


def generate_prometheus_rules() -> Dict[str, Any]:
    """Generate Prometheus alerting rules YAML."""
    groups = []

    # Group alerts by team
    teams = set(rule.labels.get("team", "default") for rule in ALERT_RULES)

    for team in teams:
        team_rules = [rule for rule in ALERT_RULES if rule.labels.get("team") == team]

        rules = []
        for rule in team_rules:
            rules.append({
                "alert": rule.name,
                "expr": rule.expr,
                "for": rule.for_duration,
                "labels": {
                    "severity": rule.severity,
                    **rule.labels,
                },
                "annotations": {
                    "summary": rule.summary,
                    "description": rule.description,
                    **rule.annotations,
                },
            })

        groups.append({
            "name": f"sdlc-orchestrator-{team}",
            "rules": rules,
        })

    return {"groups": groups}


def generate_slo_dashboard() -> Dict[str, Any]:
    """Generate SLO dashboard JSON."""
    panels = []
    y_pos = 0

    for i, slo in enumerate(SLOS):
        panels.append({
            "id": i + 100,
            "title": f"SLO: {slo.name}",
            "type": "gauge",
            "gridPos": {"h": 6, "w": 6, "x": (i % 4) * 6, "y": y_pos},
            "targets": [
                {
                    "expr": slo.metric,
                    "legendFormat": slo.name,
                }
            ],
            "fieldConfig": {
                "defaults": {
                    "max": 100,
                    "min": 0,
                    "thresholds": {
                        "steps": [
                            {"color": "red", "value": None},
                            {"color": "yellow", "value": slo.target - 1},
                            {"color": "green", "value": slo.target},
                        ]
                    },
                    "unit": "percent" if slo.target > 1 else "ms",
                }
            },
            "options": {
                "orientation": "auto",
                "showThresholdLabels": True,
            },
        })

        if (i + 1) % 4 == 0:
            y_pos += 6

    return {
        "title": "SDLC Orchestrator - SLO Dashboard",
        "uid": "sdlc-slo-dashboard",
        "tags": ["sdlc", "slo", "orchestrator"],
        "timezone": "browser",
        "refresh": "5m",
        "panels": panels,
    }


def save_configuration(name: str, data: Dict[str, Any], output_dir: Path, format: str = "yaml"):
    """Save configuration to file."""
    output_dir.mkdir(parents=True, exist_ok=True)

    if format == "yaml":
        filepath = output_dir / f"{name}.yaml"
        with open(filepath, "w") as f:
            yaml.dump(data, f, default_flow_style=False, sort_keys=False)
    else:
        filepath = output_dir / f"{name}.json"
        with open(filepath, "w") as f:
            json.dump(data, f, indent=2)

    print(f"  Generated: {filepath}")
    return filepath


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Monitoring Configuration Generator")
    parser.add_argument("--generate-all", action="store_true", help="Generate all configurations")
    parser.add_argument("--prometheus-rules", action="store_true", help="Generate Prometheus alerting rules")
    parser.add_argument("--grafana-dashboards", action="store_true", help="Generate Grafana dashboards")
    parser.add_argument("--output-dir", type=str, default="monitoring", help="Output directory")

    args = parser.parse_args()

    if not any([args.generate_all, args.prometheus_rules, args.grafana_dashboards]):
        args.generate_all = True

    output_dir = Path(args.output_dir)

    print(f"\n{'='*60}")
    print("SDLC Orchestrator - Monitoring Configuration Generator")
    print(f"{'='*60}\n")

    files_generated = []

    if args.generate_all or args.prometheus_rules:
        print("[Prometheus Alerting Rules]")
        rules = generate_prometheus_rules()
        filepath = save_configuration("prometheus-alerts", rules, output_dir / "prometheus", "yaml")
        files_generated.append(filepath)
        print(f"  Alert rules: {len(ALERT_RULES)}")

    if args.generate_all or args.grafana_dashboards:
        print("\n[Grafana Dashboards]")
        dashboard = generate_grafana_dashboard()
        filepath = save_configuration("production-overview", dashboard, output_dir / "grafana", "json")
        files_generated.append(filepath)
        print(f"  Panels: {len(dashboard['panels'])}")

        slo_dashboard = generate_slo_dashboard()
        filepath = save_configuration("slo-dashboard", slo_dashboard, output_dir / "grafana", "json")
        files_generated.append(filepath)
        print(f"  SLOs: {len(SLOS)}")

    print(f"\n{'='*60}")
    print("CONFIGURATION SUMMARY")
    print(f"{'='*60}")
    print(f"Files generated: {len(files_generated)}")
    print(f"Output directory: {output_dir}")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
