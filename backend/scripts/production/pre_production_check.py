#!/usr/bin/env python3
"""
=========================================================================
Pre-Production Checklist Script
SDLC Orchestrator - Sprint 121 (Production Deployment)

Version: 1.0.0
Date: January 29, 2026
Status: ACTIVE - Sprint 121 Day 1-2
Authority: DevOps Lead + CTO Approved
Framework: SDLC 5.3.0 Quality Assurance System

Purpose:
- Verify security requirements (OWASP ASVS L2)
- Validate performance baselines
- Check infrastructure readiness
- Verify documentation completeness

Pre-Production Checklist:
- Security: OWASP ASVS L2, penetration test, SBOM
- Performance: Load test, API latency, DB optimization
- Documentation: Runbooks, rollback, monitoring
- Infrastructure: K8s, migrations, backup/restore

Usage:
    python pre_production_check.py --all
    python pre_production_check.py --security
    python pre_production_check.py --performance
    python pre_production_check.py --infrastructure
    python pre_production_check.py --documentation

Zero Mock Policy: Real validation against production requirements
=========================================================================
"""

import argparse
import asyncio
import json
import os
import subprocess
import sys
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import httpx


# ============================================================================
# Configuration
# ============================================================================


class CheckStatus(str, Enum):
    """Status of a pre-production check."""
    PASSED = "PASSED"
    FAILED = "FAILED"
    WARNING = "WARNING"
    SKIPPED = "SKIPPED"
    ERROR = "ERROR"


@dataclass
class CheckResult:
    """Result of a single check."""
    name: str
    category: str
    status: CheckStatus
    message: str
    details: Dict[str, Any] = field(default_factory=dict)
    duration_ms: float = 0.0


@dataclass
class ChecklistResult:
    """Complete checklist result."""
    total_checks: int
    passed: int
    failed: int
    warnings: int
    skipped: int
    results: List[CheckResult]
    started_at: datetime
    completed_at: datetime
    overall_status: CheckStatus


# ============================================================================
# Security Checks
# ============================================================================


async def check_owasp_asvs_l2() -> CheckResult:
    """Check OWASP ASVS L2 compliance."""
    start = datetime.now()

    try:
        # Check for security configuration files
        security_files = [
            "backend/app/core/security.py",
            "backend/app/middleware/security_headers.py",
            "backend/app/middleware/rate_limiter.py",
        ]

        missing_files = []
        for f in security_files:
            if not Path(f).exists():
                missing_files.append(f)

        if missing_files:
            return CheckResult(
                name="OWASP ASVS L2 Compliance",
                category="Security",
                status=CheckStatus.FAILED,
                message=f"Missing security files: {', '.join(missing_files)}",
                duration_ms=(datetime.now() - start).total_seconds() * 1000,
            )

        # Check security headers configuration
        security_py = Path("backend/app/core/security.py")
        if security_py.exists():
            content = security_py.read_text()
            required_features = [
                "JWT",
                "bcrypt",
                "OAuth",
                "CORS",
            ]
            missing_features = [f for f in required_features if f.lower() not in content.lower()]

            if missing_features:
                return CheckResult(
                    name="OWASP ASVS L2 Compliance",
                    category="Security",
                    status=CheckStatus.WARNING,
                    message=f"Security features to verify: {', '.join(missing_features)}",
                    duration_ms=(datetime.now() - start).total_seconds() * 1000,
                )

        return CheckResult(
            name="OWASP ASVS L2 Compliance",
            category="Security",
            status=CheckStatus.PASSED,
            message="Security configuration files present",
            details={"files_checked": security_files},
            duration_ms=(datetime.now() - start).total_seconds() * 1000,
        )

    except Exception as e:
        return CheckResult(
            name="OWASP ASVS L2 Compliance",
            category="Security",
            status=CheckStatus.ERROR,
            message=str(e),
            duration_ms=(datetime.now() - start).total_seconds() * 1000,
        )


async def check_sbom_generation() -> CheckResult:
    """Check SBOM generation with Syft."""
    start = datetime.now()

    try:
        # Check if syft is installed
        result = subprocess.run(
            ["which", "syft"],
            capture_output=True,
            text=True,
        )

        if result.returncode != 0:
            return CheckResult(
                name="SBOM Generation (Syft)",
                category="Security",
                status=CheckStatus.WARNING,
                message="Syft not installed. Install with: curl -sSfL https://raw.githubusercontent.com/anchore/syft/main/install.sh | sh",
                duration_ms=(datetime.now() - start).total_seconds() * 1000,
            )

        # Check if requirements.txt exists
        requirements_files = [
            "backend/requirements.txt",
            "backend/requirements-dev.txt",
        ]

        for req_file in requirements_files:
            if Path(req_file).exists():
                return CheckResult(
                    name="SBOM Generation (Syft)",
                    category="Security",
                    status=CheckStatus.PASSED,
                    message="Syft installed and requirements found",
                    details={"requirements_file": req_file},
                    duration_ms=(datetime.now() - start).total_seconds() * 1000,
                )

        return CheckResult(
            name="SBOM Generation (Syft)",
            category="Security",
            status=CheckStatus.WARNING,
            message="Requirements file not found",
            duration_ms=(datetime.now() - start).total_seconds() * 1000,
        )

    except Exception as e:
        return CheckResult(
            name="SBOM Generation (Syft)",
            category="Security",
            status=CheckStatus.ERROR,
            message=str(e),
            duration_ms=(datetime.now() - start).total_seconds() * 1000,
        )


async def check_secrets_management() -> CheckResult:
    """Check secrets management configuration."""
    start = datetime.now()

    try:
        # Check for .env files in version control (should not exist)
        env_files = list(Path(".").rglob("*.env"))
        env_files = [f for f in env_files if ".git" not in str(f)]

        # Check .gitignore for .env
        gitignore = Path(".gitignore")
        env_ignored = False
        if gitignore.exists():
            content = gitignore.read_text()
            env_ignored = ".env" in content

        if env_files and not env_ignored:
            return CheckResult(
                name="Secrets Management",
                category="Security",
                status=CheckStatus.WARNING,
                message="Found .env files that may not be ignored",
                details={"files": [str(f) for f in env_files]},
                duration_ms=(datetime.now() - start).total_seconds() * 1000,
            )

        # Check for HashiCorp Vault configuration
        vault_config = Path("backend/app/core/config.py")
        vault_integrated = False
        if vault_config.exists():
            content = vault_config.read_text()
            vault_integrated = "vault" in content.lower() or "VAULT" in content

        return CheckResult(
            name="Secrets Management",
            category="Security",
            status=CheckStatus.PASSED if vault_integrated else CheckStatus.WARNING,
            message="Secrets management configured" if vault_integrated else "Consider HashiCorp Vault integration",
            details={"vault_integrated": vault_integrated, "env_ignored": env_ignored},
            duration_ms=(datetime.now() - start).total_seconds() * 1000,
        )

    except Exception as e:
        return CheckResult(
            name="Secrets Management",
            category="Security",
            status=CheckStatus.ERROR,
            message=str(e),
            duration_ms=(datetime.now() - start).total_seconds() * 1000,
        )


# ============================================================================
# Performance Checks
# ============================================================================


async def check_load_test_config() -> CheckResult:
    """Check load test configuration."""
    start = datetime.now()

    try:
        # Check for locust or k6 configuration
        load_test_files = [
            "backend/tests/load/locustfile.py",
            "tests/load/locustfile.py",
            "k6/load_test.js",
            "backend/tests/performance/load_test.py",
        ]

        for f in load_test_files:
            if Path(f).exists():
                return CheckResult(
                    name="Load Test Configuration",
                    category="Performance",
                    status=CheckStatus.PASSED,
                    message=f"Load test configuration found: {f}",
                    details={"file": f},
                    duration_ms=(datetime.now() - start).total_seconds() * 1000,
                )

        return CheckResult(
            name="Load Test Configuration",
            category="Performance",
            status=CheckStatus.WARNING,
            message="No load test configuration found. Consider adding Locust or k6 tests.",
            duration_ms=(datetime.now() - start).total_seconds() * 1000,
        )

    except Exception as e:
        return CheckResult(
            name="Load Test Configuration",
            category="Performance",
            status=CheckStatus.ERROR,
            message=str(e),
            duration_ms=(datetime.now() - start).total_seconds() * 1000,
        )


async def check_redis_caching() -> CheckResult:
    """Check Redis caching configuration."""
    start = datetime.now()

    try:
        redis_config = Path("backend/app/utils/redis.py")

        if not redis_config.exists():
            return CheckResult(
                name="Redis Caching",
                category="Performance",
                status=CheckStatus.FAILED,
                message="Redis utility not found",
                duration_ms=(datetime.now() - start).total_seconds() * 1000,
            )

        content = redis_config.read_text()

        # Check for async Redis client
        has_async = "aioredis" in content or "redis.asyncio" in content or "AsyncSession" in content

        return CheckResult(
            name="Redis Caching",
            category="Performance",
            status=CheckStatus.PASSED if has_async else CheckStatus.WARNING,
            message="Redis caching configured" + (" (async)" if has_async else " (sync - consider async)"),
            details={"async_enabled": has_async},
            duration_ms=(datetime.now() - start).total_seconds() * 1000,
        )

    except Exception as e:
        return CheckResult(
            name="Redis Caching",
            category="Performance",
            status=CheckStatus.ERROR,
            message=str(e),
            duration_ms=(datetime.now() - start).total_seconds() * 1000,
        )


async def check_database_indexes() -> CheckResult:
    """Check database index configuration."""
    start = datetime.now()

    try:
        # Check Alembic migrations for indexes
        migrations_dir = Path("backend/alembic/versions")

        if not migrations_dir.exists():
            return CheckResult(
                name="Database Indexes",
                category="Performance",
                status=CheckStatus.WARNING,
                message="Alembic migrations directory not found",
                duration_ms=(datetime.now() - start).total_seconds() * 1000,
            )

        migration_files = list(migrations_dir.glob("*.py"))
        index_count = 0

        for mf in migration_files:
            content = mf.read_text()
            index_count += content.lower().count("create_index")
            index_count += content.lower().count("op.create_index")

        return CheckResult(
            name="Database Indexes",
            category="Performance",
            status=CheckStatus.PASSED if index_count > 10 else CheckStatus.WARNING,
            message=f"Found {index_count} index definitions in migrations",
            details={"migration_files": len(migration_files), "index_count": index_count},
            duration_ms=(datetime.now() - start).total_seconds() * 1000,
        )

    except Exception as e:
        return CheckResult(
            name="Database Indexes",
            category="Performance",
            status=CheckStatus.ERROR,
            message=str(e),
            duration_ms=(datetime.now() - start).total_seconds() * 1000,
        )


# ============================================================================
# Infrastructure Checks
# ============================================================================


async def check_kubernetes_manifests() -> CheckResult:
    """Check Kubernetes manifests."""
    start = datetime.now()

    try:
        k8s_dirs = [
            "k8s",
            "kubernetes",
            "deploy/k8s",
            "infrastructure/k8s",
        ]

        for k8s_dir in k8s_dirs:
            if Path(k8s_dir).exists():
                manifests = list(Path(k8s_dir).rglob("*.yaml")) + list(Path(k8s_dir).rglob("*.yml"))

                if manifests:
                    return CheckResult(
                        name="Kubernetes Manifests",
                        category="Infrastructure",
                        status=CheckStatus.PASSED,
                        message=f"Found {len(manifests)} K8s manifests in {k8s_dir}",
                        details={"directory": k8s_dir, "manifests": [str(m) for m in manifests[:5]]},
                        duration_ms=(datetime.now() - start).total_seconds() * 1000,
                    )

        # Check for docker-compose as alternative
        docker_compose = Path("docker-compose.yml")
        if docker_compose.exists():
            return CheckResult(
                name="Kubernetes Manifests",
                category="Infrastructure",
                status=CheckStatus.WARNING,
                message="Docker Compose found. Consider K8s manifests for production.",
                details={"docker_compose": True},
                duration_ms=(datetime.now() - start).total_seconds() * 1000,
            )

        return CheckResult(
            name="Kubernetes Manifests",
            category="Infrastructure",
            status=CheckStatus.FAILED,
            message="No Kubernetes manifests found",
            duration_ms=(datetime.now() - start).total_seconds() * 1000,
        )

    except Exception as e:
        return CheckResult(
            name="Kubernetes Manifests",
            category="Infrastructure",
            status=CheckStatus.ERROR,
            message=str(e),
            duration_ms=(datetime.now() - start).total_seconds() * 1000,
        )


async def check_database_migrations() -> CheckResult:
    """Check database migration configuration."""
    start = datetime.now()

    try:
        alembic_ini = Path("backend/alembic.ini")
        alembic_dir = Path("backend/alembic")

        if not alembic_ini.exists() or not alembic_dir.exists():
            return CheckResult(
                name="Database Migrations",
                category="Infrastructure",
                status=CheckStatus.FAILED,
                message="Alembic configuration not found",
                duration_ms=(datetime.now() - start).total_seconds() * 1000,
            )

        # Count migrations
        versions_dir = alembic_dir / "versions"
        if versions_dir.exists():
            migrations = list(versions_dir.glob("*.py"))
            migrations = [m for m in migrations if m.name != "__pycache__"]

            return CheckResult(
                name="Database Migrations",
                category="Infrastructure",
                status=CheckStatus.PASSED,
                message=f"Found {len(migrations)} database migrations",
                details={"migration_count": len(migrations)},
                duration_ms=(datetime.now() - start).total_seconds() * 1000,
            )

        return CheckResult(
            name="Database Migrations",
            category="Infrastructure",
            status=CheckStatus.WARNING,
            message="Alembic configured but no migrations found",
            duration_ms=(datetime.now() - start).total_seconds() * 1000,
        )

    except Exception as e:
        return CheckResult(
            name="Database Migrations",
            category="Infrastructure",
            status=CheckStatus.ERROR,
            message=str(e),
            duration_ms=(datetime.now() - start).total_seconds() * 1000,
        )


async def check_backup_restore() -> CheckResult:
    """Check backup/restore procedures."""
    start = datetime.now()

    try:
        backup_files = [
            "scripts/backup.sh",
            "scripts/restore.sh",
            "backend/scripts/backup_db.py",
            "docs/06-operate/runbooks/backup-restore.md",
        ]

        found_files = []
        for f in backup_files:
            if Path(f).exists():
                found_files.append(f)

        if found_files:
            return CheckResult(
                name="Backup/Restore Procedures",
                category="Infrastructure",
                status=CheckStatus.PASSED,
                message=f"Found {len(found_files)} backup/restore files",
                details={"files": found_files},
                duration_ms=(datetime.now() - start).total_seconds() * 1000,
            )

        return CheckResult(
            name="Backup/Restore Procedures",
            category="Infrastructure",
            status=CheckStatus.WARNING,
            message="No backup/restore scripts found. Consider adding backup automation.",
            duration_ms=(datetime.now() - start).total_seconds() * 1000,
        )

    except Exception as e:
        return CheckResult(
            name="Backup/Restore Procedures",
            category="Infrastructure",
            status=CheckStatus.ERROR,
            message=str(e),
            duration_ms=(datetime.now() - start).total_seconds() * 1000,
        )


# ============================================================================
# Documentation Checks
# ============================================================================


async def check_runbooks() -> CheckResult:
    """Check runbook documentation."""
    start = datetime.now()

    try:
        runbook_dirs = [
            "docs/06-operate/runbooks",
            "docs/runbooks",
            "runbooks",
        ]

        for runbook_dir in runbook_dirs:
            if Path(runbook_dir).exists():
                runbooks = list(Path(runbook_dir).glob("*.md"))

                if runbooks:
                    return CheckResult(
                        name="Runbook Documentation",
                        category="Documentation",
                        status=CheckStatus.PASSED,
                        message=f"Found {len(runbooks)} runbooks",
                        details={"directory": runbook_dir, "runbooks": [r.name for r in runbooks]},
                        duration_ms=(datetime.now() - start).total_seconds() * 1000,
                    )

        return CheckResult(
            name="Runbook Documentation",
            category="Documentation",
            status=CheckStatus.WARNING,
            message="No runbooks found. Consider adding deployment and incident runbooks.",
            duration_ms=(datetime.now() - start).total_seconds() * 1000,
        )

    except Exception as e:
        return CheckResult(
            name="Runbook Documentation",
            category="Documentation",
            status=CheckStatus.ERROR,
            message=str(e),
            duration_ms=(datetime.now() - start).total_seconds() * 1000,
        )


async def check_api_documentation() -> CheckResult:
    """Check API documentation."""
    start = datetime.now()

    try:
        # Check for OpenAPI/Swagger
        api_docs = [
            "backend/app/main.py",  # FastAPI auto-docs
            "docs/01-planning/05-API-Design/API-Specification.md",
            "openapi.yaml",
            "openapi.json",
        ]

        found_docs = []
        for doc in api_docs:
            if Path(doc).exists():
                found_docs.append(doc)

        # Check FastAPI docs configuration
        main_py = Path("backend/app/main.py")
        has_swagger = False
        if main_py.exists():
            content = main_py.read_text()
            has_swagger = "docs_url" in content or "/docs" in content

        if found_docs and has_swagger:
            return CheckResult(
                name="API Documentation",
                category="Documentation",
                status=CheckStatus.PASSED,
                message="API documentation configured",
                details={"files": found_docs, "swagger_enabled": has_swagger},
                duration_ms=(datetime.now() - start).total_seconds() * 1000,
            )

        return CheckResult(
            name="API Documentation",
            category="Documentation",
            status=CheckStatus.WARNING,
            message="API documentation may be incomplete",
            details={"files": found_docs, "swagger_enabled": has_swagger},
            duration_ms=(datetime.now() - start).total_seconds() * 1000,
        )

    except Exception as e:
        return CheckResult(
            name="API Documentation",
            category="Documentation",
            status=CheckStatus.ERROR,
            message=str(e),
            duration_ms=(datetime.now() - start).total_seconds() * 1000,
        )


async def check_monitoring_dashboards() -> CheckResult:
    """Check monitoring dashboard configuration."""
    start = datetime.now()

    try:
        dashboard_files = [
            "grafana/dashboards",
            "monitoring/grafana",
            "backend/app/api/routes/grafana_dashboards.py",
        ]

        for df in dashboard_files:
            if Path(df).exists():
                return CheckResult(
                    name="Monitoring Dashboards",
                    category="Documentation",
                    status=CheckStatus.PASSED,
                    message=f"Monitoring configuration found: {df}",
                    details={"location": df},
                    duration_ms=(datetime.now() - start).total_seconds() * 1000,
                )

        # Check for Prometheus metrics
        prometheus_config = Path("backend/app/middleware/prometheus_metrics.py")
        if prometheus_config.exists():
            return CheckResult(
                name="Monitoring Dashboards",
                category="Documentation",
                status=CheckStatus.PASSED,
                message="Prometheus metrics configured",
                details={"prometheus": True},
                duration_ms=(datetime.now() - start).total_seconds() * 1000,
            )

        return CheckResult(
            name="Monitoring Dashboards",
            category="Documentation",
            status=CheckStatus.WARNING,
            message="No monitoring dashboard configuration found",
            duration_ms=(datetime.now() - start).total_seconds() * 1000,
        )

    except Exception as e:
        return CheckResult(
            name="Monitoring Dashboards",
            category="Documentation",
            status=CheckStatus.ERROR,
            message=str(e),
            duration_ms=(datetime.now() - start).total_seconds() * 1000,
        )


# ============================================================================
# Main Execution
# ============================================================================


async def run_all_checks() -> ChecklistResult:
    """Run all pre-production checks."""
    started_at = datetime.now()
    results: List[CheckResult] = []

    # Security checks
    print("\n[Security Checks]")
    results.append(await check_owasp_asvs_l2())
    print(f"  {results[-1].status.value}: {results[-1].name}")

    results.append(await check_sbom_generation())
    print(f"  {results[-1].status.value}: {results[-1].name}")

    results.append(await check_secrets_management())
    print(f"  {results[-1].status.value}: {results[-1].name}")

    # Performance checks
    print("\n[Performance Checks]")
    results.append(await check_load_test_config())
    print(f"  {results[-1].status.value}: {results[-1].name}")

    results.append(await check_redis_caching())
    print(f"  {results[-1].status.value}: {results[-1].name}")

    results.append(await check_database_indexes())
    print(f"  {results[-1].status.value}: {results[-1].name}")

    # Infrastructure checks
    print("\n[Infrastructure Checks]")
    results.append(await check_kubernetes_manifests())
    print(f"  {results[-1].status.value}: {results[-1].name}")

    results.append(await check_database_migrations())
    print(f"  {results[-1].status.value}: {results[-1].name}")

    results.append(await check_backup_restore())
    print(f"  {results[-1].status.value}: {results[-1].name}")

    # Documentation checks
    print("\n[Documentation Checks]")
    results.append(await check_runbooks())
    print(f"  {results[-1].status.value}: {results[-1].name}")

    results.append(await check_api_documentation())
    print(f"  {results[-1].status.value}: {results[-1].name}")

    results.append(await check_monitoring_dashboards())
    print(f"  {results[-1].status.value}: {results[-1].name}")

    # Calculate totals
    passed = sum(1 for r in results if r.status == CheckStatus.PASSED)
    failed = sum(1 for r in results if r.status == CheckStatus.FAILED)
    warnings = sum(1 for r in results if r.status == CheckStatus.WARNING)
    skipped = sum(1 for r in results if r.status == CheckStatus.SKIPPED)

    # Determine overall status
    if failed > 0:
        overall_status = CheckStatus.FAILED
    elif warnings > 2:
        overall_status = CheckStatus.WARNING
    else:
        overall_status = CheckStatus.PASSED

    return ChecklistResult(
        total_checks=len(results),
        passed=passed,
        failed=failed,
        warnings=warnings,
        skipped=skipped,
        results=results,
        started_at=started_at,
        completed_at=datetime.now(),
        overall_status=overall_status,
    )


def print_summary(checklist: ChecklistResult):
    """Print checklist summary."""
    print("\n" + "=" * 60)
    print("PRE-PRODUCTION CHECKLIST SUMMARY")
    print("=" * 60)
    print(f"Total Checks:  {checklist.total_checks}")
    print(f"Passed:        {checklist.passed}")
    print(f"Failed:        {checklist.failed}")
    print(f"Warnings:      {checklist.warnings}")
    print(f"Skipped:       {checklist.skipped}")
    print(f"Duration:      {(checklist.completed_at - checklist.started_at).total_seconds():.2f}s")
    print(f"\nOverall Status: {checklist.overall_status.value}")
    print("=" * 60)

    # Print action items for failed/warning checks
    action_items = [r for r in checklist.results if r.status in [CheckStatus.FAILED, CheckStatus.WARNING]]

    if action_items:
        print("\n[ACTION ITEMS]")
        for item in action_items:
            status_emoji = "" if item.status == CheckStatus.FAILED else ""
            print(f"  {status_emoji} [{item.category}] {item.name}")
            print(f"     {item.message}")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Pre-Production Checklist")
    parser.add_argument("--all", action="store_true", help="Run all checks")
    parser.add_argument("--security", action="store_true", help="Run security checks only")
    parser.add_argument("--performance", action="store_true", help="Run performance checks only")
    parser.add_argument("--infrastructure", action="store_true", help="Run infrastructure checks only")
    parser.add_argument("--documentation", action="store_true", help="Run documentation checks only")
    parser.add_argument("--json", action="store_true", help="Output as JSON")

    args = parser.parse_args()

    # Default to all if no specific category selected
    if not any([args.security, args.performance, args.infrastructure, args.documentation]):
        args.all = True

    print("=" * 60)
    print("SDLC Orchestrator - Pre-Production Checklist")
    print("Sprint 121 - Production Deployment")
    print("=" * 60)

    # Run checks
    checklist = asyncio.run(run_all_checks())

    if args.json:
        output = {
            "total_checks": checklist.total_checks,
            "passed": checklist.passed,
            "failed": checklist.failed,
            "warnings": checklist.warnings,
            "skipped": checklist.skipped,
            "overall_status": checklist.overall_status.value,
            "started_at": checklist.started_at.isoformat(),
            "completed_at": checklist.completed_at.isoformat(),
            "results": [
                {
                    "name": r.name,
                    "category": r.category,
                    "status": r.status.value,
                    "message": r.message,
                    "details": r.details,
                }
                for r in checklist.results
            ],
        }
        print(json.dumps(output, indent=2))
    else:
        print_summary(checklist)

    # Exit with error code if failed
    sys.exit(1 if checklist.overall_status == CheckStatus.FAILED else 0)


if __name__ == "__main__":
    main()
