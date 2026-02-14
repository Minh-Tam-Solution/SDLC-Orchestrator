---
spec_id: SPEC-0013
title: Compliance Validation Service
version: 1.0.0
status: CTO_APPROVED
stage: 02-design
tier: PROFESSIONAL
author: PM/PJM Office
created: 2026-01-30
updated: 2026-01-30
sprint: 123
priority: P0
dependencies:
  - SPEC-0011 (Context Authority V2)
  - SPEC-0012 (Validation Pipeline Interface)
related_adrs:
  - ADR-041 (Stage Dependency Matrix)
  - ADR-042 (SDLC 6.0.5 Migration Strategy)
---

# SPEC-0013: Compliance Validation Service

## 1. Overview

### 1.1 Purpose

The Compliance Validation Service automates SDLC 6.0.5 compliance assessment, providing:
- **Compliance Scoring**: X/100 score with category breakdown
- **Duplicate Detection**: Stage folder collision prevention
- **Version Validation**: Framework reference consistency checking
- **Spec Validation**: YAML frontmatter compliance

### 1.2 Background

This specification derives from real-world lessons during NQH-Bot and BFlow SDLC 6.0.5 migrations (January 2026):

| Issue | Discovery Method | Impact | Automated Solution |
|-------|------------------|--------|-------------------|
| Duplicate stage folders | Manual review | Gate failure | `DuplicateFolderDetector` |
| Version inconsistency | PM/PJM review | Outdated context | `VersionReferenceValidator` |
| Missing YAML frontmatter | Gate G-Phase-3 | 23% spec failures | `SpecificationValidator` |
| Subjective scoring | PM judgment | Inconsistent assessments | `ComplianceScorerService` |

### 1.3 Scope

**In Scope (Sprint 123 - P0)**:
- Compliance Scorer (10 categories, 100 points)
- Duplicate Folder Detection
- CLI commands (`sdlcctl validate --compliance`, `sdlcctl score`)
- API endpoints for dashboard integration

**Out of Scope (Future Sprints)**:
- P1: Version Reference Validator
- P2: Gate Readiness Dashboard
- P3: Cross-project Compliance Aggregation

---

## 2. Requirements

### 2.1 Functional Requirements

#### FR-001: Compliance Scoring Engine

| ID | Requirement | Priority |
|----|-------------|----------|
| FR-001.1 | Calculate overall compliance score (0-100) | MUST |
| FR-001.2 | Provide category breakdown (10 categories × 10 points) | MUST |
| FR-001.3 | List issues with severity (critical/warning/info) | MUST |
| FR-001.4 | Generate fix suggestions for each issue | SHOULD |
| FR-001.5 | Cache scores with TTL (default: 1 hour) | SHOULD |
| FR-001.6 | Support category filtering (include/exclude) | MAY |

#### FR-002: Duplicate Folder Detection

| ID | Requirement | Priority |
|----|-------------|----------|
| FR-002.1 | Detect same-prefix collisions (e.g., 04-X + 04-Y) | MUST |
| FR-002.2 | Report missing stage folders (gaps) | SHOULD |
| FR-002.3 | Identify non-standard folders (extras) | MAY |
| FR-002.4 | Provide archive commands for resolution | SHOULD |

#### FR-003: CLI Integration

| ID | Requirement | Priority |
|----|-------------|----------|
| FR-003.1 | `sdlcctl validate --compliance` command | MUST |
| FR-003.2 | `sdlcctl validate --duplicates` command | MUST |
| FR-003.3 | `sdlcctl score` quick score output | MUST |
| FR-003.4 | JSON output format for CI/CD (`--format json`) | SHOULD |
| FR-003.5 | `sdlcctl fix --duplicates` interactive fix | MAY |

#### FR-004: API Endpoints

| ID | Requirement | Priority |
|----|-------------|----------|
| FR-004.1 | POST `/api/v1/projects/{id}/validate/compliance` | MUST |
| FR-004.2 | GET `/api/v1/projects/{id}/compliance/score` | MUST |
| FR-004.3 | POST `/api/v1/projects/{id}/validate/duplicates` | MUST |
| FR-004.4 | GET `/api/v1/projects/{id}/compliance/history` | MAY |

### 2.2 Non-Functional Requirements

| ID | Requirement | Target | Priority |
|----|-------------|--------|----------|
| NFR-001 | Full compliance scan latency | <5s (1000 files) | MUST |
| NFR-002 | Duplicate detection latency | <1s | MUST |
| NFR-003 | API response time (p95) | <100ms (cached) | MUST |
| NFR-004 | Test coverage | >90% | MUST |
| NFR-005 | Memory usage | <256MB per scan | SHOULD |

---

## 3. Architecture

### 3.1 Component Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                    Compliance Validation Service                 │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────────────┐    ┌──────────────────┐                   │
│  │ ComplianceScorer │    │ DuplicateDetector│                   │
│  │     Service      │    │     Service      │                   │
│  └────────┬─────────┘    └────────┬─────────┘                   │
│           │                       │                              │
│  ┌────────▼─────────────────────▼────────┐                     │
│  │          Category Checkers              │                     │
│  │  ┌─────────────┐  ┌─────────────┐      │                     │
│  │  │Documentation│  │Specifications│      │                     │
│  │  │  Checker    │  │   Checker   │      │                     │
│  │  └─────────────┘  └─────────────┘      │                     │
│  │  ┌─────────────┐  ┌─────────────┐      │                     │
│  │  │CLAUDE/AGENTS│  │    SASE     │      │                     │
│  │  │  Checker    │  │   Checker   │      │                     │
│  │  └─────────────┘  └─────────────┘      │                     │
│  │  ┌─────────────┐  ┌─────────────┐      │                     │
│  │  │ Code Naming │  │  Migration  │      │                     │
│  │  │   Checker   │  │   Checker   │      │                     │
│  │  └─────────────┘  └─────────────┘      │                     │
│  │  ┌─────────────┐  ┌─────────────┐      │                     │
│  │  │  Framework  │  │    Team     │      │                     │
│  │  │   Checker   │  │   Checker   │      │                     │
│  │  └─────────────┘  └─────────────┘      │                     │
│  │  ┌─────────────┐  ┌─────────────┐      │                     │
│  │  │   Legacy    │  │ Governance  │      │                     │
│  │  │   Checker   │  │   Checker   │      │                     │
│  │  └─────────────┘  └─────────────┘      │                     │
│  └───────────────────────────────────────┘                      │
│                          │                                       │
│           ┌──────────────▼──────────────┐                       │
│           │       FileService           │                        │
│           │  (Project file access)      │                        │
│           └──────────────┬──────────────┘                       │
│                          │                                       │
└──────────────────────────┼───────────────────────────────────────┘
                           │
              ┌────────────▼────────────┐
              │      PostgreSQL          │
              │  compliance_scores       │
              │  compliance_issues       │
              │  folder_collision_checks │
              └─────────────────────────┘
```

### 3.2 Service Layer

```python
# backend/app/services/validation/__init__.py

from .compliance_scorer import ComplianceScorerService
from .duplicate_detector import DuplicateFolderDetector
from .checkers import (
    DocumentationStructureChecker,
    SpecificationsChecker,
    ClaudeAgentsMdChecker,
    SASEArtifactsChecker,
    CodeFileNamingChecker,
    MigrationTrackingChecker,
    FrameworkAlignmentChecker,
    TeamOrganizationChecker,
    LegacyArchivalChecker,
    GovernanceDocumentationChecker,
)

__all__ = [
    "ComplianceScorerService",
    "DuplicateFolderDetector",
    # ... checkers
]
```

### 3.3 Integration Points

| System | Integration | Purpose |
|--------|-------------|---------|
| Gates Engine (Sprint 120) | Gate prerequisite check | Block gate if score < threshold |
| Context Authority V2 | Dynamic overlay trigger | Add warnings for low scores |
| Evidence Vault | Store compliance reports | Audit trail for governance |
| sdlcctl CLI | Command integration | Developer workflow |

---

## 4. Data Model

### 4.1 Database Schema

```sql
-- Migration: sprint123_001_compliance_validation.py

-- Table: compliance_scores
CREATE TABLE compliance_scores (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    overall_score INTEGER NOT NULL CHECK (overall_score >= 0 AND overall_score <= 100),
    category_scores JSONB NOT NULL,
    -- Example: {"documentation_structure": 8, "specifications": 10, ...}
    issues_summary JSONB NOT NULL,
    -- Example: {"total": 5, "critical": 1, "warning": 3, "info": 1}
    calculated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    calculated_by UUID REFERENCES users(id),
    validation_version VARCHAR(20) NOT NULL DEFAULT '1.0.0',
    framework_version VARCHAR(20) NOT NULL DEFAULT '6.0.5',
    expires_at TIMESTAMPTZ,  -- For cache invalidation

    CONSTRAINT unique_active_score UNIQUE (project_id, expires_at)
);

CREATE INDEX idx_compliance_scores_project ON compliance_scores(project_id);
CREATE INDEX idx_compliance_scores_calculated ON compliance_scores(calculated_at DESC);
CREATE INDEX idx_compliance_scores_expires ON compliance_scores(expires_at) WHERE expires_at IS NOT NULL;

-- Table: compliance_issues
CREATE TABLE compliance_issues (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    score_id UUID NOT NULL REFERENCES compliance_scores(id) ON DELETE CASCADE,
    category VARCHAR(50) NOT NULL,
    severity VARCHAR(20) NOT NULL CHECK (severity IN ('critical', 'warning', 'info')),
    issue_code VARCHAR(50) NOT NULL,  -- e.g., 'DUPLICATE_STAGE_FOLDER'
    message TEXT NOT NULL,
    file_path VARCHAR(500),
    line_number INTEGER,
    fix_suggestion TEXT,
    fix_command VARCHAR(500),  -- e.g., 'sdlcctl fix --duplicates'
    auto_fixable BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_compliance_issues_score ON compliance_issues(score_id);
CREATE INDEX idx_compliance_issues_severity ON compliance_issues(severity);
CREATE INDEX idx_compliance_issues_category ON compliance_issues(category);

-- Table: folder_collision_checks (separate for quick lookups)
CREATE TABLE folder_collision_checks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    checked_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    docs_path VARCHAR(500) NOT NULL DEFAULT 'docs/',
    valid BOOLEAN NOT NULL,
    collisions JSONB,  -- [{stage_prefix: "04", folders: ["04-Dev", "04-Test"]}]
    gaps JSONB,        -- ["03-integrate"]
    extras JSONB,      -- ["11-custom"]
    checked_by UUID REFERENCES users(id)
);

CREATE INDEX idx_folder_checks_project ON folder_collision_checks(project_id);
CREATE INDEX idx_folder_checks_valid ON folder_collision_checks(valid);
```

### 4.2 Pydantic Schemas

```python
# backend/app/schemas/compliance.py

from datetime import datetime
from enum import Enum
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


class IssueSeverity(str, Enum):
    CRITICAL = "critical"
    WARNING = "warning"
    INFO = "info"


class ComplianceCategory(str, Enum):
    DOCUMENTATION_STRUCTURE = "documentation_structure"
    SPECIFICATIONS_MANAGEMENT = "specifications_management"
    CLAUDE_AGENTS_MD = "claude_agents_md"
    SASE_ARTIFACTS = "sase_artifacts"
    CODE_FILE_NAMING = "code_file_naming"
    MIGRATION_TRACKING = "migration_tracking"
    FRAMEWORK_ALIGNMENT = "framework_alignment"
    TEAM_ORGANIZATION = "team_organization"
    LEGACY_ARCHIVAL = "legacy_archival"
    GOVERNANCE_DOCUMENTATION = "governance_documentation"


class ComplianceIssue(BaseModel):
    """Single compliance issue."""
    category: ComplianceCategory
    severity: IssueSeverity
    issue_code: str
    message: str
    file_path: Optional[str] = None
    line_number: Optional[int] = None
    fix_suggestion: Optional[str] = None
    fix_command: Optional[str] = None
    auto_fixable: bool = False


class CategoryResult(BaseModel):
    """Result for single category."""
    name: ComplianceCategory
    score: int = Field(ge=0, le=10)
    max_score: int = 10
    issues: list[ComplianceIssue] = []
    passed_checks: list[str] = []


class IssuesSummary(BaseModel):
    """Summary of all issues."""
    total: int
    critical: int
    warning: int
    info: int


class ComplianceScoreResponse(BaseModel):
    """Full compliance score response."""
    project_id: UUID
    overall_score: int = Field(ge=0, le=100)
    categories: list[CategoryResult]
    summary: IssuesSummary
    recommendations: list[str]
    generated_at: datetime
    framework_version: str = "6.0.5"
    validation_version: str = "1.0.0"


class ComplianceScoreRequest(BaseModel):
    """Request for compliance validation."""
    include_categories: Optional[list[ComplianceCategory]] = None
    exclude_categories: Optional[list[ComplianceCategory]] = None
    force_refresh: bool = False


class FolderCollision(BaseModel):
    """Single folder collision."""
    stage_prefix: str
    stage_name: str
    folders: list[str]
    severity: IssueSeverity = IssueSeverity.CRITICAL
    fix_suggestion: str


class DuplicateDetectionResponse(BaseModel):
    """Duplicate folder detection response."""
    project_id: UUID
    valid: bool
    collisions: list[FolderCollision]
    gaps: list[str]
    extras: list[str]
    checked_at: datetime
    docs_path: str = "docs/"


class QuickScoreResponse(BaseModel):
    """Quick score response for badges/dashboards."""
    project_id: UUID
    score: int
    last_calculated: datetime
    is_cached: bool = True
```

---

## 5. API Specification

### 5.1 Endpoints

#### POST /api/v1/projects/{project_id}/validate/compliance

Run full compliance validation.

**Request**:
```json
{
  "include_categories": ["documentation_structure", "specifications_management"],
  "exclude_categories": null,
  "force_refresh": false
}
```

**Response** (200 OK):
```json
{
  "project_id": "550e8400-e29b-41d4-a716-446655440000",
  "overall_score": 87,
  "categories": [
    {
      "name": "documentation_structure",
      "score": 8,
      "max_score": 10,
      "issues": [
        {
          "category": "documentation_structure",
          "severity": "warning",
          "issue_code": "MISSING_STAGE_FOLDER",
          "message": "Missing stage folder: 03-integrate",
          "file_path": "docs/",
          "fix_suggestion": "Create folder: mkdir -p docs/03-integrate",
          "fix_command": "sdlcctl init --stage 03-integrate",
          "auto_fixable": true
        }
      ],
      "passed_checks": [
        "Stage 00-discover exists",
        "Stage 01-planning exists",
        "Stage 02-design exists"
      ]
    }
  ],
  "summary": {
    "total": 5,
    "critical": 1,
    "warning": 3,
    "info": 1
  },
  "recommendations": [
    "Fix critical issue: Duplicate stage folder detected",
    "Address 3 warnings to improve score by ~6 points"
  ],
  "generated_at": "2026-01-30T10:30:00Z",
  "framework_version": "6.0.5",
  "validation_version": "1.0.0"
}
```

**Error Responses**:
- 404: Project not found
- 422: Invalid category name
- 503: File service unavailable

#### GET /api/v1/projects/{project_id}/compliance/score

Get cached compliance score (quick lookup).

**Response** (200 OK):
```json
{
  "project_id": "550e8400-e29b-41d4-a716-446655440000",
  "score": 87,
  "last_calculated": "2026-01-30T10:30:00Z",
  "is_cached": true
}
```

**Response** (404 Not Found - No cached score):
```json
{
  "detail": "No compliance score found. Run POST /validate/compliance first."
}
```

#### POST /api/v1/projects/{project_id}/validate/duplicates

Check for duplicate stage folders.

**Request**:
```json
{
  "docs_path": "docs/"
}
```

**Response** (200 OK):
```json
{
  "project_id": "550e8400-e29b-41d4-a716-446655440000",
  "valid": false,
  "collisions": [
    {
      "stage_prefix": "04",
      "stage_name": "build",
      "folders": ["04-Development-Implementation", "04-Testing-Quality"],
      "severity": "critical",
      "fix_suggestion": "Archive duplicate to: mv docs/04-Testing-Quality docs/10-Archive/duplicate-folders-sprint123/"
    }
  ],
  "gaps": [],
  "extras": ["99-legacy"],
  "checked_at": "2026-01-30T10:35:00Z",
  "docs_path": "docs/"
}
```

---

## 6. Service Implementation

### 6.1 ComplianceScorerService

```python
# backend/app/services/validation/compliance_scorer.py

from datetime import datetime, timedelta
from typing import Optional
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.compliance import ComplianceScore, ComplianceIssue
from app.schemas.compliance import (
    ComplianceScoreResponse,
    ComplianceCategory,
    CategoryResult,
    IssuesSummary,
)
from app.services.validation.checkers import CATEGORY_CHECKERS


class ComplianceScorerService:
    """SDLC 6.0.5 Compliance Scoring Engine.

    Calculates compliance score based on 10 categories, each worth 10 points.
    Total possible score: 100 points.

    Categories:
        1. documentation_structure: Stage folders (00-10), no duplicates
        2. specifications_management: YAML frontmatter, SPEC-XXXX numbering
        3. claude_agents_md: Version headers, required sections
        4. sase_artifacts: CRP, MRP, VCR templates
        5. code_file_naming: snake_case (Python), camelCase/PascalCase (TS)
        6. migration_tracking: Progress percentage, deadline compliance
        7. framework_alignment: 7-Pillar + Section 7 compliance
        8. team_organization: SDLC Compliance Hub, roles defined
        9. legacy_archival: Proper 99-legacy/ or 10-Archive/ usage
        10. governance_documentation: CEO/CTO approvals, ADRs
    """

    CACHE_TTL_HOURS = 1

    def __init__(self, db: AsyncSession, file_service):
        self.db = db
        self.file_service = file_service

    async def calculate_score(
        self,
        project_id: UUID,
        include_categories: Optional[list[ComplianceCategory]] = None,
        exclude_categories: Optional[list[ComplianceCategory]] = None,
        force_refresh: bool = False,
    ) -> ComplianceScoreResponse:
        """Calculate compliance score for project.

        Args:
            project_id: Project UUID
            include_categories: Only check these categories (optional)
            exclude_categories: Skip these categories (optional)
            force_refresh: Bypass cache and recalculate

        Returns:
            ComplianceScoreResponse with overall score and category breakdown
        """
        # Check cache first
        if not force_refresh:
            cached = await self._get_cached_score(project_id)
            if cached:
                return cached

        # Determine categories to check
        categories_to_check = self._get_categories(include_categories, exclude_categories)

        # Run all category checkers
        category_results: list[CategoryResult] = []
        all_issues: list[ComplianceIssue] = []
        total_score = 0

        for category in categories_to_check:
            checker_class = CATEGORY_CHECKERS.get(category)
            if not checker_class:
                continue

            checker = checker_class(self.db, self.file_service)
            result = await checker.check(project_id)

            category_results.append(result)
            total_score += result.score
            all_issues.extend(result.issues)

        # Calculate summary
        summary = IssuesSummary(
            total=len(all_issues),
            critical=sum(1 for i in all_issues if i.severity == "critical"),
            warning=sum(1 for i in all_issues if i.severity == "warning"),
            info=sum(1 for i in all_issues if i.severity == "info"),
        )

        # Generate recommendations
        recommendations = self._generate_recommendations(category_results, summary)

        # Build response
        response = ComplianceScoreResponse(
            project_id=project_id,
            overall_score=total_score,
            categories=category_results,
            summary=summary,
            recommendations=recommendations,
            generated_at=datetime.utcnow(),
        )

        # Cache result
        await self._cache_score(project_id, response)

        return response

    async def get_quick_score(self, project_id: UUID) -> Optional[int]:
        """Get cached score only (fast lookup for dashboards)."""
        cached = await self._get_cached_score(project_id)
        return cached.overall_score if cached else None

    def _get_categories(
        self,
        include: Optional[list[ComplianceCategory]],
        exclude: Optional[list[ComplianceCategory]],
    ) -> list[ComplianceCategory]:
        """Determine which categories to check."""
        all_categories = list(ComplianceCategory)

        if include:
            return [c for c in include if c in all_categories]

        if exclude:
            return [c for c in all_categories if c not in exclude]

        return all_categories

    def _generate_recommendations(
        self,
        results: list[CategoryResult],
        summary: IssuesSummary,
    ) -> list[str]:
        """Generate actionable recommendations."""
        recommendations = []

        # Critical issues first
        if summary.critical > 0:
            recommendations.append(
                f"🚨 Fix {summary.critical} critical issue(s) immediately"
            )

        # Low-scoring categories
        for result in sorted(results, key=lambda r: r.score):
            if result.score < 7:
                potential_gain = result.max_score - result.score
                recommendations.append(
                    f"Improve '{result.name.value}' (+{potential_gain} points possible)"
                )

        # Warnings
        if summary.warning > 0:
            recommendations.append(
                f"Address {summary.warning} warning(s) to reach 90+ score"
            )

        return recommendations[:5]  # Top 5 recommendations

    async def _get_cached_score(
        self, project_id: UUID
    ) -> Optional[ComplianceScoreResponse]:
        """Get cached score if not expired."""
        # Implementation: Query compliance_scores table
        # WHERE project_id = ? AND expires_at > NOW()
        pass  # Actual DB query implementation

    async def _cache_score(
        self, project_id: UUID, response: ComplianceScoreResponse
    ) -> None:
        """Cache score with TTL."""
        expires_at = datetime.utcnow() + timedelta(hours=self.CACHE_TTL_HOURS)
        # Implementation: INSERT into compliance_scores
        pass  # Actual DB insert implementation
```

### 6.2 DuplicateFolderDetector

```python
# backend/app/services/validation/duplicate_detector.py

from datetime import datetime
from typing import Optional
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.compliance import (
    DuplicateDetectionResponse,
    FolderCollision,
    IssueSeverity,
)


class DuplicateFolderDetector:
    """Detect stage folder collisions in SDLC 6.0.5 projects.

    Validates that each stage prefix (00-10) has exactly one folder.
    Reports collisions, gaps, and extra folders.
    """

    STAGE_PREFIXES = [
        ("00", "discover"),
        ("01", "planning"),
        ("02", "design"),
        ("03", "integrate"),
        ("04", "build"),
        ("05", "test"),
        ("06", "deploy"),
        ("07", "operate"),
        ("08", "collaborate"),
        ("09", "govern"),
        ("10", "archive"),
    ]

    # Stages that are optional
    OPTIONAL_STAGES = {"10"}

    def __init__(self, db: AsyncSession, file_service):
        self.db = db
        self.file_service = file_service

    async def detect(
        self,
        project_id: UUID,
        docs_path: str = "docs/",
    ) -> DuplicateDetectionResponse:
        """Detect duplicate stage folders.

        Args:
            project_id: Project UUID
            docs_path: Path to docs folder (default: "docs/")

        Returns:
            DuplicateDetectionResponse with collisions, gaps, extras
        """
        # Get all directories in docs path
        folders = await self.file_service.list_directories(project_id, docs_path)

        collisions: list[FolderCollision] = []
        gaps: list[str] = []
        extras: list[str] = []

        # Check each stage prefix
        for prefix, stage_name in self.STAGE_PREFIXES:
            matching = [f for f in folders if f.startswith(f"{prefix}-")]

            if len(matching) > 1:
                # Collision detected
                collisions.append(
                    FolderCollision(
                        stage_prefix=prefix,
                        stage_name=stage_name,
                        folders=matching,
                        severity=IssueSeverity.CRITICAL,
                        fix_suggestion=self._generate_fix_suggestion(prefix, matching),
                    )
                )
            elif len(matching) == 0 and prefix not in self.OPTIONAL_STAGES:
                # Missing required stage
                gaps.append(f"{prefix}-{stage_name}")

        # Identify extra folders (non-standard prefixes)
        standard_prefixes = {p[0] for p in self.STAGE_PREFIXES}
        for folder in folders:
            prefix = folder.split("-")[0] if "-" in folder else folder
            if prefix not in standard_prefixes and folder not in ("specs", "templates"):
                extras.append(folder)

        # Store check result
        await self._store_check_result(project_id, docs_path, collisions, gaps, extras)

        return DuplicateDetectionResponse(
            project_id=project_id,
            valid=len(collisions) == 0,
            collisions=collisions,
            gaps=gaps,
            extras=extras,
            checked_at=datetime.utcnow(),
            docs_path=docs_path,
        )

    def _generate_fix_suggestion(
        self, prefix: str, folders: list[str]
    ) -> str:
        """Generate archive command for collision resolution."""
        # Keep first folder, archive the rest
        to_archive = folders[1:]
        archive_path = f"docs/10-Archive/duplicate-folders-sprint123"

        commands = [
            f"mkdir -p {archive_path}",
            *[f"mv docs/{f} {archive_path}/" for f in to_archive],
        ]

        return " && ".join(commands)

    async def _store_check_result(
        self,
        project_id: UUID,
        docs_path: str,
        collisions: list[FolderCollision],
        gaps: list[str],
        extras: list[str],
    ) -> None:
        """Store check result for audit trail."""
        # Implementation: INSERT into folder_collision_checks
        pass  # Actual DB insert implementation
```

### 6.3 Category Checker Base

```python
# backend/app/services/validation/checkers/base.py

from abc import ABC, abstractmethod
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.compliance import CategoryResult, ComplianceIssue


class BaseCategoryChecker(ABC):
    """Base class for compliance category checkers.

    Each checker validates one category (max 10 points).
    """

    category_name: str
    max_score: int = 10

    def __init__(self, db: AsyncSession, file_service):
        self.db = db
        self.file_service = file_service

    @abstractmethod
    async def check(self, project_id: UUID) -> CategoryResult:
        """Run all checks for this category.

        Returns:
            CategoryResult with score, issues, and passed checks
        """
        pass

    def _calculate_score(
        self, passed: int, total: int, critical_failures: int = 0
    ) -> int:
        """Calculate score based on passed/total checks.

        Critical failures cause score reduction multiplier.
        """
        if total == 0:
            return self.max_score

        base_score = int((passed / total) * self.max_score)

        # Critical failures reduce score by 50%
        if critical_failures > 0:
            base_score = int(base_score * 0.5)

        return max(0, min(self.max_score, base_score))
```

---

## 7. CLI Integration

### 7.1 Commands

```python
# backend/sdlcctl/commands/validate.py

import click
import json

from sdlcctl.api import get_api_client
from sdlcctl.output import format_compliance_report, format_duplicates_report


@click.group()
def validate():
    """Validation commands."""
    pass


@validate.command()
@click.option("--project", "-p", required=True, help="Project ID or name")
@click.option("--category", "-c", multiple=True, help="Specific categories to check")
@click.option("--format", "-f", type=click.Choice(["text", "json"]), default="text")
@click.option("--force", is_flag=True, help="Force refresh (bypass cache)")
def compliance(project, category, format, force):
    """Run SDLC 6.0.5 compliance validation.

    Example:
        sdlcctl validate compliance --project nqh-bot
        sdlcctl validate compliance -p bflow -c specifications -c documentation
        sdlcctl validate compliance -p myproject --format json > report.json
    """
    client = get_api_client()

    request = {
        "include_categories": list(category) if category else None,
        "force_refresh": force,
    }

    result = client.post(f"/projects/{project}/validate/compliance", json=request)

    if format == "json":
        click.echo(json.dumps(result, indent=2, default=str))
    else:
        click.echo(format_compliance_report(result))


@validate.command()
@click.option("--project", "-p", required=True, help="Project ID or name")
@click.option("--docs-path", default="docs/", help="Path to docs folder")
@click.option("--format", "-f", type=click.Choice(["text", "json"]), default="text")
def duplicates(project, docs_path, format):
    """Check for duplicate stage folders.

    Example:
        sdlcctl validate duplicates --project nqh-bot
        sdlcctl validate duplicates -p bflow --docs-path documentation/
    """
    client = get_api_client()

    result = client.post(
        f"/projects/{project}/validate/duplicates",
        json={"docs_path": docs_path},
    )

    if format == "json":
        click.echo(json.dumps(result, indent=2, default=str))
    else:
        click.echo(format_duplicates_report(result))


# backend/sdlcctl/commands/score.py

@click.command()
@click.option("--project", "-p", required=True, help="Project ID or name")
def score(project):
    """Get compliance score (quick lookup).

    Example:
        sdlcctl score --project nqh-bot
        # Output: 87
    """
    client = get_api_client()

    result = client.get(f"/projects/{project}/compliance/score")

    click.echo(result["score"])
```

### 7.2 Output Formatters

```python
# backend/sdlcctl/output/compliance.py

from typing import Any


def format_compliance_report(data: dict[str, Any]) -> str:
    """Format compliance report for terminal output."""
    lines = []

    # Header
    lines.append("=" * 60)
    lines.append(f"SDLC 6.0.5 Compliance Report")
    lines.append(f"Generated: {data['generated_at']}")
    lines.append("=" * 60)
    lines.append("")

    # Overall score with color
    score = data["overall_score"]
    score_icon = "🟢" if score >= 90 else "🟡" if score >= 70 else "🔴"
    lines.append(f"Overall Score: {score_icon} {score}/100")
    lines.append("")

    # Category breakdown
    lines.append("Category Breakdown:")
    lines.append("-" * 40)
    for cat in sorted(data["categories"], key=lambda x: x["score"]):
        bar = "█" * cat["score"] + "░" * (10 - cat["score"])
        lines.append(f"  {cat['name']:<30} [{bar}] {cat['score']}/{cat['max_score']}")
    lines.append("")

    # Issues summary
    summary = data["summary"]
    if summary["total"] > 0:
        lines.append("Issues Found:")
        lines.append(f"  🚨 Critical: {summary['critical']}")
        lines.append(f"  ⚠️  Warning:  {summary['warning']}")
        lines.append(f"  ℹ️  Info:     {summary['info']}")
        lines.append("")

    # Recommendations
    if data["recommendations"]:
        lines.append("Recommendations:")
        for rec in data["recommendations"]:
            lines.append(f"  → {rec}")
        lines.append("")

    return "\n".join(lines)


def format_duplicates_report(data: dict[str, Any]) -> str:
    """Format duplicate detection report for terminal output."""
    lines = []

    if data["valid"]:
        lines.append("✅ No duplicate stage folders found")
    else:
        lines.append("❌ Stage folder collisions detected!")
        lines.append("")

        for collision in data["collisions"]:
            lines.append(f"  Stage {collision['stage_prefix']} ({collision['stage_name']}):")
            for folder in collision["folders"]:
                lines.append(f"    - {folder}")
            lines.append(f"  Fix: {collision['fix_suggestion']}")
            lines.append("")

    if data["gaps"]:
        lines.append("⚠️ Missing stage folders:")
        for gap in data["gaps"]:
            lines.append(f"  - {gap}")
        lines.append("")

    if data["extras"]:
        lines.append("ℹ️ Non-standard folders:")
        for extra in data["extras"]:
            lines.append(f"  - {extra}")

    return "\n".join(lines)
```

---

## 8. Testing Strategy

### 8.1 Unit Tests

```python
# backend/tests/unit/services/validation/test_compliance_scorer.py

import pytest
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

from app.services.validation.compliance_scorer import ComplianceScorerService
from app.schemas.compliance import ComplianceCategory


@pytest.fixture
def mock_db():
    return AsyncMock()


@pytest.fixture
def mock_file_service():
    return MagicMock()


@pytest.fixture
def scorer(mock_db, mock_file_service):
    return ComplianceScorerService(mock_db, mock_file_service)


class TestComplianceScorerService:
    """Tests for ComplianceScorerService."""

    async def test_calculate_score_returns_valid_response(self, scorer):
        """Score calculation returns proper structure."""
        project_id = uuid4()

        result = await scorer.calculate_score(project_id)

        assert 0 <= result.overall_score <= 100
        assert len(result.categories) == 10
        assert result.summary.total >= 0

    async def test_category_filtering_include(self, scorer):
        """Include filter only checks specified categories."""
        project_id = uuid4()
        include = [ComplianceCategory.DOCUMENTATION_STRUCTURE]

        result = await scorer.calculate_score(
            project_id, include_categories=include
        )

        assert len(result.categories) == 1
        assert result.categories[0].name == ComplianceCategory.DOCUMENTATION_STRUCTURE

    async def test_category_filtering_exclude(self, scorer):
        """Exclude filter skips specified categories."""
        project_id = uuid4()
        exclude = [ComplianceCategory.DOCUMENTATION_STRUCTURE]

        result = await scorer.calculate_score(
            project_id, exclude_categories=exclude
        )

        assert len(result.categories) == 9
        assert ComplianceCategory.DOCUMENTATION_STRUCTURE not in [
            c.name for c in result.categories
        ]

    async def test_force_refresh_bypasses_cache(self, scorer):
        """Force refresh recalculates even with cached score."""
        # Implementation test
        pass


# backend/tests/unit/services/validation/test_duplicate_detector.py

class TestDuplicateFolderDetector:
    """Tests for DuplicateFolderDetector."""

    async def test_detects_same_prefix_collision(self, detector, mock_file_service):
        """Collision detected when multiple folders share prefix."""
        mock_file_service.list_directories.return_value = [
            "00-discover",
            "01-planning",
            "04-Development",
            "04-Testing",  # Collision!
        ]

        result = await detector.detect(uuid4())

        assert not result.valid
        assert len(result.collisions) == 1
        assert result.collisions[0].stage_prefix == "04"

    async def test_reports_missing_stages(self, detector, mock_file_service):
        """Missing stages reported in gaps."""
        mock_file_service.list_directories.return_value = [
            "00-discover",
            "01-planning",
            # 02-design missing
            "04-build",
        ]

        result = await detector.detect(uuid4())

        assert "02-design" in result.gaps
        assert "03-integrate" in result.gaps

    async def test_identifies_extra_folders(self, detector, mock_file_service):
        """Non-standard folders reported as extras."""
        mock_file_service.list_directories.return_value = [
            "00-discover",
            "99-legacy",  # Non-standard
            "custom-folder",  # Non-standard
        ]

        result = await detector.detect(uuid4())

        assert "99-legacy" in result.extras
        assert "custom-folder" in result.extras
```

### 8.2 Integration Tests

```python
# backend/tests/integration/test_compliance_validation_api.py

import pytest
from httpx import AsyncClient
from uuid import uuid4

from app.main import app


@pytest.mark.integration
class TestComplianceValidationAPI:
    """Integration tests for compliance validation endpoints."""

    async def test_validate_compliance_endpoint(
        self, async_client: AsyncClient, test_project
    ):
        """POST /validate/compliance returns valid score."""
        response = await async_client.post(
            f"/api/v1/projects/{test_project.id}/validate/compliance",
            json={},
        )

        assert response.status_code == 200
        data = response.json()
        assert "overall_score" in data
        assert "categories" in data
        assert len(data["categories"]) == 10

    async def test_get_cached_score(
        self, async_client: AsyncClient, test_project
    ):
        """GET /compliance/score returns cached score."""
        # First, calculate score
        await async_client.post(
            f"/api/v1/projects/{test_project.id}/validate/compliance",
            json={},
        )

        # Then get cached
        response = await async_client.get(
            f"/api/v1/projects/{test_project.id}/compliance/score"
        )

        assert response.status_code == 200
        data = response.json()
        assert "score" in data
        assert data["is_cached"] is True

    async def test_validate_duplicates_endpoint(
        self, async_client: AsyncClient, test_project
    ):
        """POST /validate/duplicates returns collision info."""
        response = await async_client.post(
            f"/api/v1/projects/{test_project.id}/validate/duplicates",
            json={"docs_path": "docs/"},
        )

        assert response.status_code == 200
        data = response.json()
        assert "valid" in data
        assert "collisions" in data
```

---

## 9. Deployment

### 9.1 Database Migration

```python
# backend/alembic/versions/sprint123_001_compliance_validation.py

"""Sprint 123: Compliance Validation Service

Revision ID: sprint123_001
Revises: sprint122_xxx
Create Date: 2026-03-03
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB


revision = "sprint123_001"
down_revision = "sprint122_xxx"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # compliance_scores table
    op.create_table(
        "compliance_scores",
        sa.Column("id", UUID(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("project_id", UUID(), nullable=False),
        sa.Column("overall_score", sa.Integer(), nullable=False),
        sa.Column("category_scores", JSONB(), nullable=False),
        sa.Column("issues_summary", JSONB(), nullable=False),
        sa.Column("calculated_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()"), nullable=False),
        sa.Column("calculated_by", UUID(), nullable=True),
        sa.Column("validation_version", sa.String(20), server_default="1.0.0", nullable=False),
        sa.Column("framework_version", sa.String(20), server_default="6.0.5", nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["calculated_by"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.CheckConstraint("overall_score >= 0 AND overall_score <= 100", name="valid_score"),
    )

    op.create_index("idx_compliance_scores_project", "compliance_scores", ["project_id"])
    op.create_index("idx_compliance_scores_calculated", "compliance_scores", ["calculated_at"], postgresql_using="btree")

    # compliance_issues table
    op.create_table(
        "compliance_issues",
        sa.Column("id", UUID(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("score_id", UUID(), nullable=False),
        sa.Column("category", sa.String(50), nullable=False),
        sa.Column("severity", sa.String(20), nullable=False),
        sa.Column("issue_code", sa.String(50), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("file_path", sa.String(500), nullable=True),
        sa.Column("line_number", sa.Integer(), nullable=True),
        sa.Column("fix_suggestion", sa.Text(), nullable=True),
        sa.Column("fix_command", sa.String(500), nullable=True),
        sa.Column("auto_fixable", sa.Boolean(), server_default="false", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()"), nullable=False),
        sa.ForeignKeyConstraint(["score_id"], ["compliance_scores.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.CheckConstraint("severity IN ('critical', 'warning', 'info')", name="valid_severity"),
    )

    op.create_index("idx_compliance_issues_score", "compliance_issues", ["score_id"])
    op.create_index("idx_compliance_issues_severity", "compliance_issues", ["severity"])

    # folder_collision_checks table
    op.create_table(
        "folder_collision_checks",
        sa.Column("id", UUID(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("project_id", UUID(), nullable=False),
        sa.Column("checked_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()"), nullable=False),
        sa.Column("docs_path", sa.String(500), server_default="docs/", nullable=False),
        sa.Column("valid", sa.Boolean(), nullable=False),
        sa.Column("collisions", JSONB(), nullable=True),
        sa.Column("gaps", JSONB(), nullable=True),
        sa.Column("extras", JSONB(), nullable=True),
        sa.Column("checked_by", UUID(), nullable=True),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["checked_by"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_index("idx_folder_checks_project", "folder_collision_checks", ["project_id"])


def downgrade() -> None:
    op.drop_table("folder_collision_checks")
    op.drop_table("compliance_issues")
    op.drop_table("compliance_scores")
```

---

## 10. Document Control

| Field | Value |
|-------|-------|
| **Spec ID** | SPEC-0013 |
| **Title** | Compliance Validation Service |
| **Version** | 1.0.0 |
| **Status** | CTO_APPROVED |
| **Stage** | 02-design |
| **Tier** | PROFESSIONAL |
| **Author** | PM/PJM Office |
| **Created** | January 30, 2026 |
| **Sprint** | 123 |
| **Priority** | P0 |
| **Estimated LOC** | ~1,200 |
| **Estimated Effort** | 24h |

### Approval

| Role | Name | Date | Signature |
|------|------|------|-----------|
| CTO | CTO-SDLC-Orchestrator | January 30, 2026 | ✅ APPROVED (A+ Grade, 98/100) |
| Tech Lead | [Pending Implementation Review] | | |
| PM | PM/PJM Office | January 30, 2026 | ✅ Created |

**CTO Approval Notes**:
- Documentation Grade: **A+ (98/100)** - Exemplary technical documentation
- SDLC 6.0.5 Compliance: **100/100**
- Risk Level: **GREEN** (Low Risk, High Value, Evidence-Based)
- Confidence: **99.5%**
- ROI Projection: **9.4x** (16h investment → 150h+ savings annually)
- Implementation: **GO FOR SPRINT 123** (March 3-14, 2026)

---

## References

- [Sprint 123 Plan](../../04-build/02-Sprint-Plans/SPRINT-123-COMPLIANCE-VALIDATION.md)
- [PM-PJM Review - NQH-Bot Migration](../../../NQH-Bot-Platform/docs/08-Team-Management/01-SDLC-Compliance/PM-PJM-REVIEW-SDLC-6.0.0-MIGRATION.md)
- [BFlow Gate Readiness Checklist](../../../Bflow-Platform/docs/08-Team-Management/02-SDLC-Compliance/SDLC-6.0.0-Preparation/SPRINT-127-GATE-READINESS-CHECKLIST.md)
- [SPEC-0011: Context Authority V2](./SPEC-0011-Context-Authority-V2.md)
- [SPEC-0012: Validation Pipeline Interface](./SPEC-0012-Validation-Pipeline-Interface.md)

---

*SPEC-0013 - Automating compliance validation from real-world migration lessons.*
