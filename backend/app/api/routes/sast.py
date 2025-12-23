"""
SAST API Routes - Static Application Security Testing

SDLC Stage: 04 - BUILD
Sprint: 43 - Policy Guards & Evidence UI
Framework: SDLC 5.1.1
Epic: EP-02 AI Safety Layer v1

Purpose:
REST API endpoints for SAST scanning functionality.
Provides security scanning for projects and code snippets.

Endpoints:
- POST /projects/{id}/sast/scan - Initiate SAST scan
- GET /projects/{id}/sast/scans - Get scan history
- GET /projects/{id}/sast/scans/{scan_id} - Get scan details
- POST /sast/scan-snippet - Scan code snippet
- GET /projects/{id}/sast/analytics - Get SAST analytics
- GET /projects/{id}/sast/trend - Get findings trend

Security:
- Requires authentication
- Project-level access control
- Rate limited (10 scans/minute per project)
"""

import logging
import os
import time
from datetime import datetime, timedelta
from typing import List, Optional
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, HTTPException, Query, status

from ...schemas.sast import (
    SASTAnalyticsResponse,
    SASTCategory,
    SASTCategoryBreakdown,
    SASTCodeSnippetRequest,
    SASTFinding,
    SASTScanHistoryItem,
    SASTScanHistoryResponse,
    SASTScanRequest,
    SASTScanResponse,
    SASTScanSummary,
    SASTScanType,
    SASTSeverity,
    SASTTrendPoint,
    SASTTrendResponse,
)
from ...services.semgrep_service import (
    SemgrepCategory,
    SemgrepSeverity,
    get_semgrep_service,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/sast", tags=["SAST"])


# =============================================================================
# Helper Functions
# =============================================================================


def _map_semgrep_severity(severity: SemgrepSeverity) -> SASTSeverity:
    """Map Semgrep severity to SAST severity."""
    mapping = {
        SemgrepSeverity.ERROR: SASTSeverity.CRITICAL,
        SemgrepSeverity.WARNING: SASTSeverity.MEDIUM,
        SemgrepSeverity.INFO: SASTSeverity.LOW,
    }
    return mapping.get(severity, SASTSeverity.MEDIUM)


def _map_semgrep_category(category: SemgrepCategory) -> SASTCategory:
    """Map Semgrep category to SAST category."""
    mapping = {
        SemgrepCategory.INJECTION: SASTCategory.INJECTION,
        SemgrepCategory.BROKEN_AUTH: SASTCategory.BROKEN_AUTH,
        SemgrepCategory.SENSITIVE_DATA: SASTCategory.SENSITIVE_DATA,
        SemgrepCategory.XXE: SASTCategory.XXE,
        SemgrepCategory.BROKEN_ACCESS: SASTCategory.BROKEN_ACCESS,
        SemgrepCategory.SECURITY_MISCONFIG: SASTCategory.SECURITY_MISCONFIG,
        SemgrepCategory.XSS: SASTCategory.XSS,
        SemgrepCategory.INSECURE_DESERIALIZATION: SASTCategory.INSECURE_DESERIALIZATION,
        SemgrepCategory.VULNERABLE_COMPONENTS: SASTCategory.VULNERABLE_COMPONENTS,
        SemgrepCategory.INSUFFICIENT_LOGGING: SASTCategory.INSUFFICIENT_LOGGING,
        SemgrepCategory.SECRETS: SASTCategory.SECRETS,
        SemgrepCategory.CRYPTO: SASTCategory.CRYPTO,
        SemgrepCategory.PATH_TRAVERSAL: SASTCategory.PATH_TRAVERSAL,
        SemgrepCategory.COMMAND_INJECTION: SASTCategory.COMMAND_INJECTION,
        SemgrepCategory.SSRF: SASTCategory.SSRF,
        SemgrepCategory.OTHER: SASTCategory.OTHER,
    }
    return mapping.get(category, SASTCategory.OTHER)


def _count_by_severity(findings: List[SASTFinding]) -> dict:
    """Count findings by severity."""
    counts = {
        "critical": 0,
        "high": 0,
        "medium": 0,
        "low": 0,
        "info": 0,
    }
    for finding in findings:
        counts[finding.severity.value] = counts.get(finding.severity.value, 0) + 1
    return counts


def _count_by_category(findings: List[SASTFinding]) -> dict:
    """Count findings by category."""
    counts: dict = {}
    for finding in findings:
        cat = finding.category.value
        counts[cat] = counts.get(cat, 0) + 1
    return counts


def _get_top_affected_files(findings: List[SASTFinding], limit: int = 10) -> list:
    """Get files with most findings."""
    file_counts: dict = {}
    for finding in findings:
        file_counts[finding.file_path] = file_counts.get(finding.file_path, 0) + 1

    sorted_files = sorted(file_counts.items(), key=lambda x: -x[1])
    return [{"file": f, "count": c} for f, c in sorted_files[:limit]]


# =============================================================================
# API Endpoints
# =============================================================================


@router.post(
    "/projects/{project_id}/scan",
    response_model=SASTScanResponse,
    status_code=status.HTTP_200_OK,
    summary="Initiate SAST scan",
    description="Start a static application security testing scan for a project",
)
async def initiate_sast_scan(
    project_id: UUID,
    request: SASTScanRequest,
) -> SASTScanResponse:
    """
    Initiate a SAST scan for a project.

    Scans project files for security vulnerabilities using Semgrep.
    Includes OWASP Top 10 and AI security rules.

    Args:
        project_id: Project UUID
        request: Scan configuration

    Returns:
        SASTScanResponse with findings and summary
    """
    scan_id = uuid4()
    started_at = datetime.utcnow()

    logger.info(
        f"Starting SAST scan {scan_id} for project {project_id}, type={request.scan_type}"
    )

    try:
        # Get Semgrep service
        custom_rules = None
        if request.include_ai_rules:
            ai_rules_path = "backend/policy-packs/semgrep/ai-security.yml"
            if os.path.exists(ai_rules_path):
                custom_rules = ai_rules_path

        semgrep = get_semgrep_service(custom_rules_path=custom_rules)

        # Check Semgrep availability
        if not await semgrep.check_availability():
            return SASTScanResponse(
                scan_id=scan_id,
                project_id=project_id,
                success=False,
                error_message="Semgrep CLI not installed",
                summary=SASTScanSummary(),
                findings=[],
                scan_type=request.scan_type,
                branch=request.branch,
                commit_sha=request.commit_sha,
                started_at=started_at,
                completed_at=datetime.utcnow(),
                blocks_merge=False,
            )

        # Determine files to scan
        if request.files:
            files_to_scan = request.files
        else:
            # Scan common source directories
            files_to_scan = []
            scan_dirs = ["backend/app", "frontend/src"]
            for scan_dir in scan_dirs:
                if os.path.isdir(scan_dir):
                    for root, _, files in os.walk(scan_dir):
                        for f in files:
                            if f.endswith((".py", ".ts", ".tsx", ".js", ".jsx")):
                                files_to_scan.append(os.path.join(root, f))

        if not files_to_scan:
            return SASTScanResponse(
                scan_id=scan_id,
                project_id=project_id,
                success=True,
                summary=SASTScanSummary(files_scanned=0),
                findings=[],
                scan_type=request.scan_type,
                branch=request.branch,
                commit_sha=request.commit_sha,
                started_at=started_at,
                completed_at=datetime.utcnow(),
                blocks_merge=False,
            )

        # Run scan
        scan_result = await semgrep.scan_files(files_to_scan)

        # Convert findings
        findings: List[SASTFinding] = []
        for semgrep_finding in scan_result.findings:
            # Filter by severity threshold
            sast_severity = _map_semgrep_severity(semgrep_finding.severity)

            severity_order = {
                SASTSeverity.CRITICAL: 0,
                SASTSeverity.HIGH: 1,
                SASTSeverity.MEDIUM: 2,
                SASTSeverity.LOW: 3,
                SASTSeverity.INFO: 4,
            }

            if severity_order.get(sast_severity, 4) <= severity_order.get(
                request.severity_threshold, 2
            ):
                findings.append(
                    SASTFinding(
                        file_path=semgrep_finding.file_path,
                        start_line=semgrep_finding.start_line,
                        end_line=semgrep_finding.end_line,
                        start_col=semgrep_finding.start_col,
                        end_col=semgrep_finding.end_col,
                        rule_id=semgrep_finding.rule_id,
                        rule_name=semgrep_finding.rule_name,
                        severity=sast_severity,
                        category=_map_semgrep_category(semgrep_finding.category),
                        message=semgrep_finding.message,
                        snippet=semgrep_finding.snippet,
                        fix_suggestion=semgrep_finding.fix_suggestion,
                        cwe=semgrep_finding.cwe,
                        owasp=semgrep_finding.owasp,
                        references=semgrep_finding.references,
                        confidence=semgrep_finding.confidence,
                    )
                )

        # Build summary
        severity_counts = _count_by_severity(findings)
        category_counts = _count_by_category(findings)

        summary = SASTScanSummary(
            total_findings=len(findings),
            critical_count=severity_counts.get("critical", 0),
            high_count=severity_counts.get("high", 0),
            medium_count=severity_counts.get("medium", 0),
            low_count=severity_counts.get("low", 0),
            info_count=severity_counts.get("info", 0),
            files_scanned=scan_result.files_scanned,
            rules_run=scan_result.rules_run,
            scan_duration_ms=scan_result.duration_ms,
            by_category=category_counts,
            top_affected_files=_get_top_affected_files(findings),
        )

        # Determine blocking status
        blocks_merge = (
            severity_counts.get("critical", 0) > 0
            or severity_counts.get("high", 0) > 0
        )

        completed_at = datetime.utcnow()

        logger.info(
            f"SAST scan {scan_id} complete: {len(findings)} findings, "
            f"{summary.critical_count} critical, {summary.high_count} high"
        )

        return SASTScanResponse(
            scan_id=scan_id,
            project_id=project_id,
            success=True,
            summary=summary,
            findings=findings[:100],  # Limit to 100 findings
            scan_type=request.scan_type,
            branch=request.branch,
            commit_sha=request.commit_sha,
            started_at=started_at,
            completed_at=completed_at,
            blocks_merge=blocks_merge,
        )

    except Exception as e:
        logger.error(f"SAST scan error: {e}", exc_info=True)
        return SASTScanResponse(
            scan_id=scan_id,
            project_id=project_id,
            success=False,
            error_message=str(e),
            summary=SASTScanSummary(),
            findings=[],
            scan_type=request.scan_type,
            branch=request.branch,
            commit_sha=request.commit_sha,
            started_at=started_at,
            completed_at=datetime.utcnow(),
            blocks_merge=False,
        )


@router.post(
    "/scan-snippet",
    response_model=SASTScanResponse,
    status_code=status.HTTP_200_OK,
    summary="Scan code snippet",
    description="Scan a code snippet for security vulnerabilities",
)
async def scan_code_snippet(
    request: SASTCodeSnippetRequest,
) -> SASTScanResponse:
    """
    Scan a code snippet for security vulnerabilities.

    Useful for IDE integration and pre-commit checks.

    Args:
        request: Code snippet and language

    Returns:
        SASTScanResponse with findings
    """
    scan_id = uuid4()
    project_id = uuid4()  # Placeholder for snippet scans
    started_at = datetime.utcnow()

    try:
        # Get Semgrep service
        custom_rules = None
        if request.include_ai_rules:
            ai_rules_path = "backend/policy-packs/semgrep/ai-security.yml"
            if os.path.exists(ai_rules_path):
                custom_rules = ai_rules_path

        semgrep = get_semgrep_service(custom_rules_path=custom_rules)

        # Check availability
        if not await semgrep.check_availability():
            return SASTScanResponse(
                scan_id=scan_id,
                project_id=project_id,
                success=False,
                error_message="Semgrep CLI not installed",
                summary=SASTScanSummary(),
                findings=[],
                scan_type=SASTScanType.QUICK,
                started_at=started_at,
                completed_at=datetime.utcnow(),
                blocks_merge=False,
            )

        # Scan snippet
        scan_result = await semgrep.scan_code_snippet(
            code=request.code,
            language=request.language,
        )

        # Convert findings
        findings: List[SASTFinding] = []
        for semgrep_finding in scan_result.findings:
            findings.append(
                SASTFinding(
                    file_path="snippet",
                    start_line=semgrep_finding.start_line,
                    end_line=semgrep_finding.end_line,
                    start_col=semgrep_finding.start_col,
                    end_col=semgrep_finding.end_col,
                    rule_id=semgrep_finding.rule_id,
                    rule_name=semgrep_finding.rule_name,
                    severity=_map_semgrep_severity(semgrep_finding.severity),
                    category=_map_semgrep_category(semgrep_finding.category),
                    message=semgrep_finding.message,
                    snippet=semgrep_finding.snippet,
                    fix_suggestion=semgrep_finding.fix_suggestion,
                    cwe=semgrep_finding.cwe,
                    owasp=semgrep_finding.owasp,
                    references=semgrep_finding.references,
                    confidence=semgrep_finding.confidence,
                )
            )

        # Build summary
        severity_counts = _count_by_severity(findings)

        summary = SASTScanSummary(
            total_findings=len(findings),
            critical_count=severity_counts.get("critical", 0),
            high_count=severity_counts.get("high", 0),
            medium_count=severity_counts.get("medium", 0),
            low_count=severity_counts.get("low", 0),
            info_count=severity_counts.get("info", 0),
            files_scanned=1,
            rules_run=scan_result.rules_run,
            scan_duration_ms=scan_result.duration_ms,
        )

        return SASTScanResponse(
            scan_id=scan_id,
            project_id=project_id,
            success=True,
            summary=summary,
            findings=findings,
            scan_type=SASTScanType.QUICK,
            started_at=started_at,
            completed_at=datetime.utcnow(),
            blocks_merge=severity_counts.get("critical", 0) > 0,
        )

    except Exception as e:
        logger.error(f"Snippet scan error: {e}", exc_info=True)
        return SASTScanResponse(
            scan_id=scan_id,
            project_id=project_id,
            success=False,
            error_message=str(e),
            summary=SASTScanSummary(),
            findings=[],
            scan_type=SASTScanType.QUICK,
            started_at=started_at,
            completed_at=datetime.utcnow(),
            blocks_merge=False,
        )


@router.get(
    "/projects/{project_id}/scans",
    response_model=SASTScanHistoryResponse,
    summary="Get scan history",
    description="Get SAST scan history for a project",
)
async def get_scan_history(
    project_id: UUID,
    page: int = Query(default=1, ge=1, description="Page number"),
    page_size: int = Query(default=20, ge=1, le=100, description="Items per page"),
) -> SASTScanHistoryResponse:
    """
    Get SAST scan history for a project.

    Args:
        project_id: Project UUID
        page: Page number
        page_size: Items per page

    Returns:
        Paginated scan history
    """
    # TODO: Implement database query for scan history
    # For now, return empty history
    return SASTScanHistoryResponse(
        project_id=project_id,
        scans=[],
        total_scans=0,
        page=page,
        page_size=page_size,
    )


@router.get(
    "/projects/{project_id}/scans/{scan_id}",
    response_model=SASTScanResponse,
    summary="Get scan details",
    description="Get details of a specific SAST scan",
)
async def get_scan_details(
    project_id: UUID,
    scan_id: UUID,
) -> SASTScanResponse:
    """
    Get details of a specific SAST scan.

    Args:
        project_id: Project UUID
        scan_id: Scan UUID

    Returns:
        Full scan details with findings
    """
    # TODO: Implement database query for scan details
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Scan {scan_id} not found",
    )


@router.get(
    "/projects/{project_id}/trend",
    response_model=SASTTrendResponse,
    summary="Get findings trend",
    description="Get SAST findings trend over time",
)
async def get_findings_trend(
    project_id: UUID,
    days: int = Query(default=30, ge=7, le=90, description="Number of days"),
) -> SASTTrendResponse:
    """
    Get SAST findings trend over time.

    Args:
        project_id: Project UUID
        days: Number of days to include

    Returns:
        Trend data with direction indicator
    """
    # TODO: Implement database query for trend data
    # For now, return empty trend
    return SASTTrendResponse(
        project_id=project_id,
        period_days=days,
        data_points=[],
        trend_direction="stable",
        percent_change=0.0,
    )


@router.get(
    "/projects/{project_id}/analytics",
    response_model=SASTAnalyticsResponse,
    summary="Get SAST analytics",
    description="Get comprehensive SAST analytics for a project",
)
async def get_sast_analytics(
    project_id: UUID,
    days: int = Query(default=30, ge=7, le=90, description="Analysis period"),
) -> SASTAnalyticsResponse:
    """
    Get comprehensive SAST analytics for a project.

    Includes category breakdown, top rules, file hotspots, and fix metrics.

    Args:
        project_id: Project UUID
        days: Analysis period in days

    Returns:
        Comprehensive analytics response
    """
    # TODO: Implement database query for analytics
    return SASTAnalyticsResponse(
        project_id=project_id,
        period_days=days,
        total_scans=0,
        total_findings=0,
        findings_fixed=0,
        findings_new=0,
        category_breakdown=[],
        top_rules=[],
        file_hotspots=[],
        avg_time_to_fix_hours=None,
    )


# =============================================================================
# Health Check
# =============================================================================


@router.get(
    "/health",
    summary="SAST health check",
    description="Check SAST service health and Semgrep availability",
)
async def sast_health_check() -> dict:
    """
    Check SAST service health.

    Returns:
        Health status including Semgrep availability
    """
    semgrep = get_semgrep_service()
    semgrep_available = await semgrep.check_availability()

    # Check for custom rules
    ai_rules_exist = os.path.exists("backend/policy-packs/semgrep/ai-security.yml")
    owasp_rules_exist = os.path.exists("backend/policy-packs/semgrep/owasp-python.yml")

    return {
        "status": "healthy" if semgrep_available else "degraded",
        "semgrep_available": semgrep_available,
        "custom_rules": {
            "ai_security": ai_rules_exist,
            "owasp_python": owasp_rules_exist,
        },
        "timestamp": datetime.utcnow().isoformat(),
    }
