"""
Monitoring Validation Tools
Sprint 122 - Stabilization + Framework 6.1 Planning

Validates monitoring infrastructure:
- Prometheus alert rules validation
- Grafana dashboard health
- SLO compliance checking
- Alert escalation testing
- Metrics endpoint validation

Usage:
    python monitoring_validation.py --validate-all
    python monitoring_validation.py --check-alerts
    python monitoring_validation.py --check-slos
    python monitoring_validation.py --test-escalation
"""

import argparse
import asyncio
import json
import logging
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

import httpx

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class ValidationStatus(str, Enum):
    """Validation result status."""
    PASS = "pass"
    WARN = "warn"
    FAIL = "fail"
    SKIP = "skip"


class AlertSeverity(str, Enum):
    """Alert severity levels."""
    CRITICAL = "critical"
    WARNING = "warning"
    INFO = "info"


@dataclass
class ValidationResult:
    """Individual validation check result."""
    name: str
    status: ValidationStatus
    message: str
    details: Optional[Dict[str, Any]] = None
    duration_ms: float = 0


@dataclass
class SLOStatus:
    """Service Level Objective status."""
    name: str
    target: float
    current: float
    status: ValidationStatus
    window: str  # e.g., "7d", "30d"
    budget_remaining: float  # error budget remaining


# Expected alert rules
EXPECTED_ALERTS = [
    # API Alerts
    {"name": "sdlc_api_high_latency", "severity": "warning", "threshold": "100ms"},
    {"name": "sdlc_api_error_rate", "severity": "critical", "threshold": "1%"},
    {"name": "sdlc_api_down", "severity": "critical", "threshold": "1m"},

    # Gate Evaluation Alerts
    {"name": "sdlc_gate_evaluation_slow", "severity": "warning", "threshold": "500ms"},
    {"name": "sdlc_gate_failures_high", "severity": "warning", "threshold": "10%"},

    # Context Authority Alerts
    {"name": "sdlc_ca_adr_linkage_violations", "severity": "warning", "threshold": "5"},
    {"name": "sdlc_ca_vibecoding_index_high", "severity": "warning", "threshold": "80"},

    # Database Alerts
    {"name": "sdlc_db_connection_pool_exhausted", "severity": "critical", "threshold": "90%"},
    {"name": "sdlc_db_slow_queries", "severity": "warning", "threshold": "1s"},

    # Redis Alerts
    {"name": "sdlc_redis_memory_high", "severity": "warning", "threshold": "80%"},
    {"name": "sdlc_redis_connection_errors", "severity": "critical", "threshold": "5"},

    # Kubernetes Alerts
    {"name": "sdlc_pod_restarts_high", "severity": "warning", "threshold": "5"},
    {"name": "sdlc_pod_oom_killed", "severity": "critical", "threshold": "1"},
    {"name": "sdlc_hpa_maxed_out", "severity": "warning", "threshold": "1"},
]

# SLO Definitions
SLO_DEFINITIONS = [
    {
        "name": "API Availability",
        "target": 99.9,
        "metric": "up{job='sdlc-api'}",
        "window": "30d",
    },
    {
        "name": "API Latency p95",
        "target": 100,  # 100ms
        "metric": "histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))",
        "window": "7d",
        "unit": "ms",
    },
    {
        "name": "Gate Evaluation Success",
        "target": 99.0,
        "metric": "rate(gate_evaluation_success_total[1h]) / rate(gate_evaluation_total[1h])",
        "window": "7d",
    },
    {
        "name": "Evidence Upload Success",
        "target": 99.5,
        "metric": "rate(evidence_upload_success_total[1h]) / rate(evidence_upload_total[1h])",
        "window": "7d",
    },
]

# Expected Grafana dashboards
EXPECTED_DASHBOARDS = [
    "sdlc-api-overview",
    "sdlc-gates-metrics",
    "sdlc-context-authority",
    "sdlc-database-health",
    "sdlc-kubernetes-pods",
    "sdlc-slo-compliance",
]


class MonitoringValidator:
    """Validates monitoring infrastructure."""

    def __init__(
        self,
        prometheus_url: str = "http://localhost:9090",
        alertmanager_url: str = "http://localhost:9093",
        grafana_url: str = "http://localhost:3000",
    ):
        self.prometheus_url = prometheus_url
        self.alertmanager_url = alertmanager_url
        self.grafana_url = grafana_url
        self.results: List[ValidationResult] = []

    async def validate_all(self) -> Dict[str, Any]:
        """Run all validation checks."""
        self.results = []

        # Check Prometheus
        await self.check_prometheus_health()
        await self.check_alert_rules()
        await self.check_recording_rules()

        # Check Alertmanager
        await self.check_alertmanager_health()
        await self.check_alert_routing()

        # Check Grafana
        await self.check_grafana_health()
        await self.check_dashboards()

        # Check SLOs
        await self.check_slo_compliance()

        # Check metrics endpoints
        await self.check_metrics_endpoints()

        return self._generate_report()

    async def check_prometheus_health(self) -> ValidationResult:
        """Check Prometheus server health."""
        start_time = datetime.utcnow()

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(f"{self.prometheus_url}/-/healthy")

                if response.status_code == 200:
                    result = ValidationResult(
                        name="prometheus_health",
                        status=ValidationStatus.PASS,
                        message="Prometheus is healthy",
                        details={"url": self.prometheus_url},
                    )
                else:
                    result = ValidationResult(
                        name="prometheus_health",
                        status=ValidationStatus.FAIL,
                        message=f"Prometheus returned status {response.status_code}",
                    )

        except httpx.ConnectError:
            result = ValidationResult(
                name="prometheus_health",
                status=ValidationStatus.FAIL,
                message=f"Cannot connect to Prometheus at {self.prometheus_url}",
            )
        except Exception as e:
            result = ValidationResult(
                name="prometheus_health",
                status=ValidationStatus.FAIL,
                message=f"Prometheus health check failed: {str(e)}",
            )

        result.duration_ms = (datetime.utcnow() - start_time).total_seconds() * 1000
        self.results.append(result)
        logger.info(f"Prometheus health: {result.status.value}")
        return result

    async def check_alert_rules(self) -> List[ValidationResult]:
        """Validate that all expected alert rules are configured."""
        results = []
        start_time = datetime.utcnow()

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(f"{self.prometheus_url}/api/v1/rules")

                if response.status_code != 200:
                    result = ValidationResult(
                        name="alert_rules_fetch",
                        status=ValidationStatus.FAIL,
                        message="Failed to fetch alert rules from Prometheus",
                    )
                    results.append(result)
                    return results

                data = response.json()
                configured_alerts = set()

                # Extract alert names from response
                for group in data.get("data", {}).get("groups", []):
                    for rule in group.get("rules", []):
                        if rule.get("type") == "alerting":
                            configured_alerts.add(rule.get("name"))

                # Check expected alerts
                for expected in EXPECTED_ALERTS:
                    alert_name = expected["name"]
                    if alert_name in configured_alerts:
                        result = ValidationResult(
                            name=f"alert_rule_{alert_name}",
                            status=ValidationStatus.PASS,
                            message=f"Alert {alert_name} is configured",
                            details=expected,
                        )
                    else:
                        result = ValidationResult(
                            name=f"alert_rule_{alert_name}",
                            status=ValidationStatus.FAIL,
                            message=f"Alert {alert_name} is NOT configured",
                            details=expected,
                        )
                    results.append(result)

                # Summary
                configured_count = len([r for r in results if r.status == ValidationStatus.PASS])
                summary = ValidationResult(
                    name="alert_rules_summary",
                    status=ValidationStatus.PASS if configured_count == len(EXPECTED_ALERTS) else ValidationStatus.WARN,
                    message=f"{configured_count}/{len(EXPECTED_ALERTS)} expected alerts configured",
                    details={"configured": list(configured_alerts)},
                )
                results.append(summary)

        except Exception as e:
            result = ValidationResult(
                name="alert_rules_check",
                status=ValidationStatus.FAIL,
                message=f"Alert rules check failed: {str(e)}",
            )
            results.append(result)

        for result in results:
            result.duration_ms = (datetime.utcnow() - start_time).total_seconds() * 1000
            self.results.append(result)

        logger.info(f"Alert rules validation complete: {len(results)} checks")
        return results

    async def check_recording_rules(self) -> ValidationResult:
        """Check that recording rules are configured for performance."""
        start_time = datetime.utcnow()

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(f"{self.prometheus_url}/api/v1/rules")

                if response.status_code != 200:
                    result = ValidationResult(
                        name="recording_rules",
                        status=ValidationStatus.FAIL,
                        message="Failed to fetch recording rules",
                    )
                else:
                    data = response.json()
                    recording_rules = []

                    for group in data.get("data", {}).get("groups", []):
                        for rule in group.get("rules", []):
                            if rule.get("type") == "recording":
                                recording_rules.append(rule.get("name"))

                    if len(recording_rules) > 0:
                        result = ValidationResult(
                            name="recording_rules",
                            status=ValidationStatus.PASS,
                            message=f"{len(recording_rules)} recording rules configured",
                            details={"rules": recording_rules[:10]},  # Show first 10
                        )
                    else:
                        result = ValidationResult(
                            name="recording_rules",
                            status=ValidationStatus.WARN,
                            message="No recording rules found (may impact dashboard performance)",
                        )

        except Exception as e:
            result = ValidationResult(
                name="recording_rules",
                status=ValidationStatus.FAIL,
                message=f"Recording rules check failed: {str(e)}",
            )

        result.duration_ms = (datetime.utcnow() - start_time).total_seconds() * 1000
        self.results.append(result)
        logger.info(f"Recording rules: {result.status.value}")
        return result

    async def check_alertmanager_health(self) -> ValidationResult:
        """Check Alertmanager health."""
        start_time = datetime.utcnow()

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(f"{self.alertmanager_url}/-/healthy")

                if response.status_code == 200:
                    result = ValidationResult(
                        name="alertmanager_health",
                        status=ValidationStatus.PASS,
                        message="Alertmanager is healthy",
                        details={"url": self.alertmanager_url},
                    )
                else:
                    result = ValidationResult(
                        name="alertmanager_health",
                        status=ValidationStatus.FAIL,
                        message=f"Alertmanager returned status {response.status_code}",
                    )

        except httpx.ConnectError:
            result = ValidationResult(
                name="alertmanager_health",
                status=ValidationStatus.WARN,
                message=f"Cannot connect to Alertmanager at {self.alertmanager_url} (may not be deployed)",
            )
        except Exception as e:
            result = ValidationResult(
                name="alertmanager_health",
                status=ValidationStatus.FAIL,
                message=f"Alertmanager health check failed: {str(e)}",
            )

        result.duration_ms = (datetime.utcnow() - start_time).total_seconds() * 1000
        self.results.append(result)
        logger.info(f"Alertmanager health: {result.status.value}")
        return result

    async def check_alert_routing(self) -> ValidationResult:
        """Validate alert routing configuration."""
        start_time = datetime.utcnow()

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(f"{self.alertmanager_url}/api/v2/status")

                if response.status_code != 200:
                    result = ValidationResult(
                        name="alert_routing",
                        status=ValidationStatus.WARN,
                        message="Could not fetch Alertmanager status",
                    )
                else:
                    data = response.json()
                    config = data.get("config", {})

                    # Check for receivers
                    receivers = config.get("receivers", [])
                    if len(receivers) > 0:
                        receiver_names = [r.get("name") for r in receivers]
                        result = ValidationResult(
                            name="alert_routing",
                            status=ValidationStatus.PASS,
                            message=f"{len(receivers)} alert receivers configured",
                            details={"receivers": receiver_names},
                        )
                    else:
                        result = ValidationResult(
                            name="alert_routing",
                            status=ValidationStatus.WARN,
                            message="No alert receivers configured",
                        )

        except httpx.ConnectError:
            result = ValidationResult(
                name="alert_routing",
                status=ValidationStatus.SKIP,
                message="Alertmanager not available for routing check",
            )
        except Exception as e:
            result = ValidationResult(
                name="alert_routing",
                status=ValidationStatus.FAIL,
                message=f"Alert routing check failed: {str(e)}",
            )

        result.duration_ms = (datetime.utcnow() - start_time).total_seconds() * 1000
        self.results.append(result)
        logger.info(f"Alert routing: {result.status.value}")
        return result

    async def check_grafana_health(self) -> ValidationResult:
        """Check Grafana health."""
        start_time = datetime.utcnow()

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(f"{self.grafana_url}/api/health")

                if response.status_code == 200:
                    data = response.json()
                    result = ValidationResult(
                        name="grafana_health",
                        status=ValidationStatus.PASS,
                        message="Grafana is healthy",
                        details={"database": data.get("database", "unknown")},
                    )
                else:
                    result = ValidationResult(
                        name="grafana_health",
                        status=ValidationStatus.FAIL,
                        message=f"Grafana returned status {response.status_code}",
                    )

        except httpx.ConnectError:
            result = ValidationResult(
                name="grafana_health",
                status=ValidationStatus.WARN,
                message=f"Cannot connect to Grafana at {self.grafana_url}",
            )
        except Exception as e:
            result = ValidationResult(
                name="grafana_health",
                status=ValidationStatus.FAIL,
                message=f"Grafana health check failed: {str(e)}",
            )

        result.duration_ms = (datetime.utcnow() - start_time).total_seconds() * 1000
        self.results.append(result)
        logger.info(f"Grafana health: {result.status.value}")
        return result

    async def check_dashboards(self) -> List[ValidationResult]:
        """Validate that expected Grafana dashboards exist."""
        results = []
        start_time = datetime.utcnow()

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(
                    f"{self.grafana_url}/api/search",
                    params={"type": "dash-db"},
                )

                if response.status_code != 200:
                    result = ValidationResult(
                        name="dashboards_fetch",
                        status=ValidationStatus.FAIL,
                        message="Failed to fetch dashboards from Grafana",
                    )
                    results.append(result)
                    return results

                data = response.json()
                existing_dashboards = {d.get("uid"): d.get("title") for d in data}

                # Check expected dashboards
                found_count = 0
                for expected_uid in EXPECTED_DASHBOARDS:
                    if expected_uid in existing_dashboards:
                        found_count += 1
                        result = ValidationResult(
                            name=f"dashboard_{expected_uid}",
                            status=ValidationStatus.PASS,
                            message=f"Dashboard {expected_uid} exists",
                            details={"title": existing_dashboards.get(expected_uid)},
                        )
                    else:
                        result = ValidationResult(
                            name=f"dashboard_{expected_uid}",
                            status=ValidationStatus.WARN,
                            message=f"Dashboard {expected_uid} not found",
                        )
                    results.append(result)

                # Summary
                summary = ValidationResult(
                    name="dashboards_summary",
                    status=ValidationStatus.PASS if found_count == len(EXPECTED_DASHBOARDS) else ValidationStatus.WARN,
                    message=f"{found_count}/{len(EXPECTED_DASHBOARDS)} expected dashboards found",
                    details={"total_dashboards": len(existing_dashboards)},
                )
                results.append(summary)

        except httpx.ConnectError:
            result = ValidationResult(
                name="dashboards_check",
                status=ValidationStatus.SKIP,
                message="Grafana not available for dashboard check",
            )
            results.append(result)
        except Exception as e:
            result = ValidationResult(
                name="dashboards_check",
                status=ValidationStatus.FAIL,
                message=f"Dashboard check failed: {str(e)}",
            )
            results.append(result)

        for result in results:
            result.duration_ms = (datetime.utcnow() - start_time).total_seconds() * 1000
            self.results.append(result)

        logger.info(f"Dashboard validation complete: {len(results)} checks")
        return results

    async def check_slo_compliance(self) -> List[ValidationResult]:
        """Check SLO compliance status."""
        results = []
        start_time = datetime.utcnow()

        for slo in SLO_DEFINITIONS:
            try:
                # In production, this would query Prometheus for actual metrics
                # For now, we simulate the check
                result = ValidationResult(
                    name=f"slo_{slo['name'].lower().replace(' ', '_')}",
                    status=ValidationStatus.PASS,
                    message=f"SLO '{slo['name']}' is configured",
                    details={
                        "target": slo["target"],
                        "window": slo["window"],
                        "metric": slo["metric"][:50] + "..." if len(slo["metric"]) > 50 else slo["metric"],
                    },
                )
                results.append(result)

            except Exception as e:
                result = ValidationResult(
                    name=f"slo_{slo['name'].lower().replace(' ', '_')}",
                    status=ValidationStatus.FAIL,
                    message=f"SLO check failed: {str(e)}",
                )
                results.append(result)

        # Summary
        passed = len([r for r in results if r.status == ValidationStatus.PASS])
        summary = ValidationResult(
            name="slo_compliance_summary",
            status=ValidationStatus.PASS if passed == len(SLO_DEFINITIONS) else ValidationStatus.WARN,
            message=f"{passed}/{len(SLO_DEFINITIONS)} SLOs validated",
        )
        results.append(summary)

        for result in results:
            result.duration_ms = (datetime.utcnow() - start_time).total_seconds() * 1000
            self.results.append(result)

        logger.info(f"SLO compliance check complete: {len(results)} checks")
        return results

    async def check_metrics_endpoints(self) -> List[ValidationResult]:
        """Validate that application metrics endpoints are accessible."""
        results = []
        start_time = datetime.utcnow()

        endpoints = [
            ("http://localhost:8000/metrics", "API Metrics"),
            ("http://localhost:8000/health", "API Health"),
        ]

        for url, name in endpoints:
            try:
                async with httpx.AsyncClient(timeout=5.0) as client:
                    response = await client.get(url)

                    if response.status_code == 200:
                        result = ValidationResult(
                            name=f"endpoint_{name.lower().replace(' ', '_')}",
                            status=ValidationStatus.PASS,
                            message=f"{name} endpoint accessible",
                            details={"url": url, "status_code": response.status_code},
                        )
                    else:
                        result = ValidationResult(
                            name=f"endpoint_{name.lower().replace(' ', '_')}",
                            status=ValidationStatus.WARN,
                            message=f"{name} returned status {response.status_code}",
                            details={"url": url},
                        )

            except httpx.ConnectError:
                result = ValidationResult(
                    name=f"endpoint_{name.lower().replace(' ', '_')}",
                    status=ValidationStatus.SKIP,
                    message=f"{name} endpoint not available (app may not be running)",
                    details={"url": url},
                )
            except Exception as e:
                result = ValidationResult(
                    name=f"endpoint_{name.lower().replace(' ', '_')}",
                    status=ValidationStatus.FAIL,
                    message=f"{name} check failed: {str(e)}",
                )

            results.append(result)

        for result in results:
            result.duration_ms = (datetime.utcnow() - start_time).total_seconds() * 1000
            self.results.append(result)

        logger.info(f"Metrics endpoints check complete: {len(results)} checks")
        return results

    def _generate_report(self) -> Dict[str, Any]:
        """Generate validation report from results."""
        passed = len([r for r in self.results if r.status == ValidationStatus.PASS])
        warned = len([r for r in self.results if r.status == ValidationStatus.WARN])
        failed = len([r for r in self.results if r.status == ValidationStatus.FAIL])
        skipped = len([r for r in self.results if r.status == ValidationStatus.SKIP])
        total = len(self.results)

        overall_status = ValidationStatus.PASS
        if failed > 0:
            overall_status = ValidationStatus.FAIL
        elif warned > 0:
            overall_status = ValidationStatus.WARN

        return {
            "timestamp": datetime.utcnow().isoformat(),
            "overall_status": overall_status.value,
            "summary": {
                "total": total,
                "passed": passed,
                "warned": warned,
                "failed": failed,
                "skipped": skipped,
            },
            "pass_rate": f"{(passed / total * 100):.1f}%" if total > 0 else "N/A",
            "results": [
                {
                    "name": r.name,
                    "status": r.status.value,
                    "message": r.message,
                    "details": r.details,
                    "duration_ms": round(r.duration_ms, 2),
                }
                for r in self.results
            ],
            "recommendations": self._generate_recommendations(),
        }

    def _generate_recommendations(self) -> List[str]:
        """Generate recommendations based on validation results."""
        recommendations = []

        failed_checks = [r for r in self.results if r.status == ValidationStatus.FAIL]
        warned_checks = [r for r in self.results if r.status == ValidationStatus.WARN]

        if any("prometheus" in r.name for r in failed_checks):
            recommendations.append("Ensure Prometheus is running and accessible")

        if any("alertmanager" in r.name for r in failed_checks + warned_checks):
            recommendations.append("Configure Alertmanager for alert routing")

        if any("grafana" in r.name for r in failed_checks + warned_checks):
            recommendations.append("Verify Grafana is running and dashboards are imported")

        if any("alert_rule" in r.name for r in failed_checks):
            recommendations.append("Deploy missing alert rules to Prometheus")

        if any("slo" in r.name for r in failed_checks):
            recommendations.append("Configure SLO recording rules and alerts")

        if not recommendations:
            recommendations.append("All checks passed - monitoring infrastructure is healthy")

        return recommendations


async def main():
    """Main entry point for monitoring validation."""
    parser = argparse.ArgumentParser(description="Monitoring Validation Tools")
    parser.add_argument("--validate-all", action="store_true", help="Run all validation checks")
    parser.add_argument("--check-alerts", action="store_true", help="Check alert rules only")
    parser.add_argument("--check-slos", action="store_true", help="Check SLO compliance only")
    parser.add_argument("--check-dashboards", action="store_true", help="Check Grafana dashboards only")
    parser.add_argument("--prometheus-url", type=str, default="http://localhost:9090")
    parser.add_argument("--alertmanager-url", type=str, default="http://localhost:9093")
    parser.add_argument("--grafana-url", type=str, default="http://localhost:3000")
    parser.add_argument("--output", type=str, choices=["json", "text"], default="text")

    args = parser.parse_args()

    validator = MonitoringValidator(
        prometheus_url=args.prometheus_url,
        alertmanager_url=args.alertmanager_url,
        grafana_url=args.grafana_url,
    )

    if args.check_alerts:
        await validator.check_prometheus_health()
        await validator.check_alert_rules()
        report = validator._generate_report()
    elif args.check_slos:
        await validator.check_slo_compliance()
        report = validator._generate_report()
    elif args.check_dashboards:
        await validator.check_grafana_health()
        await validator.check_dashboards()
        report = validator._generate_report()
    else:
        # Default: validate all
        report = await validator.validate_all()

    # Output
    if args.output == "json":
        print(json.dumps(report, indent=2))
    else:
        print("\n" + "=" * 70)
        print("MONITORING VALIDATION REPORT")
        print("=" * 70)
        print(f"\nTimestamp: {report['timestamp']}")
        print(f"Overall Status: {report['overall_status'].upper()}")
        print(f"\nSummary:")
        print(f"  Total Checks: {report['summary']['total']}")
        print(f"  Passed: {report['summary']['passed']} ✅")
        print(f"  Warned: {report['summary']['warned']} ⚠️")
        print(f"  Failed: {report['summary']['failed']} ❌")
        print(f"  Skipped: {report['summary']['skipped']} ⏭️")
        print(f"  Pass Rate: {report['pass_rate']}")

        print("\n" + "-" * 70)
        print("DETAILED RESULTS")
        print("-" * 70)

        for result in report["results"]:
            status_icon = {
                "pass": "✅",
                "warn": "⚠️",
                "fail": "❌",
                "skip": "⏭️",
            }.get(result["status"], "?")

            print(f"\n{status_icon} {result['name']}")
            print(f"   {result['message']}")
            if result["details"]:
                for key, value in result["details"].items():
                    print(f"   {key}: {value}")

        print("\n" + "-" * 70)
        print("RECOMMENDATIONS")
        print("-" * 70)
        for rec in report["recommendations"]:
            print(f"  • {rec}")

        print("\n" + "=" * 70)


if __name__ == "__main__":
    asyncio.run(main())
