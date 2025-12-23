"""
SAST Schemas - Static Application Security Testing

SDLC Stage: 04 - BUILD
Sprint: 43 - Policy Guards & Evidence UI
Framework: SDLC 5.1.1
Epic: EP-02 AI Safety Layer v1

Purpose:
Pydantic schemas for SAST API endpoints.
Defines request/response models for security scanning.

Reference:
- OWASP Top 10 2021: https://owasp.org/Top10/
- CWE: https://cwe.mitre.org/
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class SASTSeverity(str, Enum):
    """SAST finding severity levels."""

    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class SASTCategory(str, Enum):
    """Security vulnerability categories."""

    INJECTION = "injection"
    BROKEN_AUTH = "broken-authentication"
    SENSITIVE_DATA = "sensitive-data-exposure"
    XXE = "xxe"
    BROKEN_ACCESS = "broken-access-control"
    SECURITY_MISCONFIG = "security-misconfiguration"
    XSS = "xss"
    INSECURE_DESERIALIZATION = "insecure-deserialization"
    VULNERABLE_COMPONENTS = "vulnerable-components"
    INSUFFICIENT_LOGGING = "insufficient-logging"
    SECRETS = "secrets"
    CRYPTO = "cryptography"
    PATH_TRAVERSAL = "path-traversal"
    COMMAND_INJECTION = "command-injection"
    SSRF = "ssrf"
    PROMPT_INJECTION = "prompt-injection"
    DATA_LEAKAGE = "data-leakage"
    UNSAFE_MODEL = "unsafe-model"
    OTHER = "other"


class SASTScanType(str, Enum):
    """Types of SAST scans."""

    FULL = "full"
    INCREMENTAL = "incremental"
    PR = "pr"
    QUICK = "quick"


# =============================================================================
# Request Schemas
# =============================================================================


class SASTScanRequest(BaseModel):
    """Request to initiate a SAST scan."""

    scan_type: SASTScanType = Field(
        default=SASTScanType.INCREMENTAL,
        description="Type of scan to perform",
    )
    files: Optional[List[str]] = Field(
        default=None,
        description="Specific files to scan (if empty, scan all)",
    )
    branch: Optional[str] = Field(
        default=None,
        description="Git branch to scan",
    )
    commit_sha: Optional[str] = Field(
        default=None,
        description="Specific commit SHA to scan",
    )
    include_ai_rules: bool = Field(
        default=True,
        description="Include AI/ML security rules",
    )
    severity_threshold: SASTSeverity = Field(
        default=SASTSeverity.MEDIUM,
        description="Minimum severity to report",
    )

    model_config = {"json_schema_extra": {"examples": [
        {
            "scan_type": "incremental",
            "include_ai_rules": True,
            "severity_threshold": "medium",
        }
    ]}}


class SASTCodeSnippetRequest(BaseModel):
    """Request to scan a code snippet."""

    code: str = Field(
        ...,
        description="Source code to scan",
        min_length=1,
        max_length=100000,
    )
    language: str = Field(
        ...,
        description="Programming language (python, javascript, etc)",
    )
    include_ai_rules: bool = Field(
        default=True,
        description="Include AI/ML security rules",
    )

    model_config = {"json_schema_extra": {"examples": [
        {
            "code": "def login(request):\n    password = request.GET['password']\n    cursor.execute(f\"SELECT * FROM users WHERE password = '{password}'\")",
            "language": "python",
            "include_ai_rules": False,
        }
    ]}}


# =============================================================================
# Response Schemas
# =============================================================================


class SASTFinding(BaseModel):
    """Single security finding from SAST scan."""

    # Location
    file_path: str = Field(..., description="Path to the file")
    start_line: int = Field(..., description="Starting line number")
    end_line: int = Field(..., description="Ending line number")
    start_col: int = Field(default=1, description="Starting column")
    end_col: int = Field(default=1, description="Ending column")

    # Rule information
    rule_id: str = Field(..., description="Semgrep rule ID")
    rule_name: str = Field(..., description="Human-readable rule name")
    severity: SASTSeverity = Field(..., description="Finding severity")
    category: SASTCategory = Field(..., description="Vulnerability category")

    # Details
    message: str = Field(..., description="Description of the issue")
    snippet: str = Field(default="", description="Code snippet")
    fix_suggestion: Optional[str] = Field(
        default=None,
        description="Suggested fix",
    )

    # References
    cwe: List[str] = Field(
        default_factory=list,
        description="CWE identifiers",
    )
    owasp: List[str] = Field(
        default_factory=list,
        description="OWASP Top 10 references",
    )
    references: List[str] = Field(
        default_factory=list,
        description="External references",
    )

    # Confidence
    confidence: str = Field(
        default="high",
        description="Finding confidence (high, medium, low)",
    )

    model_config = {"from_attributes": True}


class SASTScanSummary(BaseModel):
    """Summary statistics for a SAST scan."""

    total_findings: int = Field(default=0, description="Total number of findings")
    critical_count: int = Field(default=0, description="Critical severity count")
    high_count: int = Field(default=0, description="High severity count")
    medium_count: int = Field(default=0, description="Medium severity count")
    low_count: int = Field(default=0, description="Low severity count")
    info_count: int = Field(default=0, description="Info severity count")

    files_scanned: int = Field(default=0, description="Number of files scanned")
    rules_run: int = Field(default=0, description="Number of rules executed")
    scan_duration_ms: int = Field(default=0, description="Scan duration in ms")

    # By category
    by_category: Dict[str, int] = Field(
        default_factory=dict,
        description="Findings grouped by category",
    )

    # Top affected files
    top_affected_files: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Files with most findings",
    )


class SASTScanResponse(BaseModel):
    """Response from a SAST scan."""

    # Identification
    scan_id: UUID = Field(..., description="Unique scan identifier")
    project_id: UUID = Field(..., description="Project being scanned")

    # Status
    success: bool = Field(..., description="Whether scan completed successfully")
    error_message: Optional[str] = Field(
        default=None,
        description="Error message if scan failed",
    )

    # Results
    summary: SASTScanSummary = Field(..., description="Scan summary statistics")
    findings: List[SASTFinding] = Field(
        default_factory=list,
        description="Security findings",
    )

    # Metadata
    scan_type: SASTScanType = Field(..., description="Type of scan performed")
    branch: Optional[str] = Field(default=None, description="Branch scanned")
    commit_sha: Optional[str] = Field(default=None, description="Commit scanned")

    # Timestamps
    started_at: datetime = Field(..., description="Scan start time")
    completed_at: Optional[datetime] = Field(
        default=None,
        description="Scan completion time",
    )

    # Blocking status
    blocks_merge: bool = Field(
        default=False,
        description="Whether findings block merge",
    )

    model_config = {"from_attributes": True}


class SASTScanHistoryItem(BaseModel):
    """Single item in scan history."""

    scan_id: UUID
    scan_type: SASTScanType
    success: bool
    total_findings: int
    critical_count: int
    high_count: int
    branch: Optional[str]
    commit_sha: Optional[str]
    started_at: datetime
    duration_ms: int

    model_config = {"from_attributes": True}


class SASTScanHistoryResponse(BaseModel):
    """Response for scan history endpoint."""

    project_id: UUID
    scans: List[SASTScanHistoryItem]
    total_scans: int
    page: int
    page_size: int

    model_config = {"from_attributes": True}


# =============================================================================
# Trend and Analytics Schemas
# =============================================================================


class SASTTrendPoint(BaseModel):
    """Single point in SAST trend data."""

    date: datetime
    total_findings: int
    critical_count: int
    high_count: int
    medium_count: int


class SASTTrendResponse(BaseModel):
    """SAST findings trend over time."""

    project_id: UUID
    period_days: int
    data_points: List[SASTTrendPoint]

    # Trend direction
    trend_direction: str = Field(
        default="stable",
        description="increasing, decreasing, or stable",
    )
    percent_change: float = Field(
        default=0.0,
        description="Percent change from start to end",
    )


class SASTCategoryBreakdown(BaseModel):
    """Breakdown of findings by category."""

    category: SASTCategory
    count: int
    percent: float
    severity_distribution: Dict[str, int]


class SASTAnalyticsResponse(BaseModel):
    """Analytics for SAST findings."""

    project_id: UUID
    period_days: int

    # Overall stats
    total_scans: int
    total_findings: int
    findings_fixed: int
    findings_new: int

    # By category
    category_breakdown: List[SASTCategoryBreakdown]

    # Top rules triggered
    top_rules: List[Dict[str, Any]]

    # File hotspots
    file_hotspots: List[Dict[str, Any]]

    # Time to fix (average)
    avg_time_to_fix_hours: Optional[float]
