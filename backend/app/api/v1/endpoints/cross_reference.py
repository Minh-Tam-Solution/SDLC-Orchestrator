"""
=========================================================================
Cross-Reference Validation API - Stage 03 ↔ Stage 05 Bidirectional Links
SDLC Orchestrator - Sprint 139 (E2E Commands Implementation)

Version: 1.0.0
Date: February 2, 2026
Status: ACTIVE - Sprint 139 (RFC-SDLC-602)
Authority: Backend Lead + CTO Approved
Framework: SDLC 6.0.5 (RFC-SDLC-602 E2E API Testing Enhancement)

Purpose:
- Validate bidirectional cross-references between Stage 03 and Stage 05
- Parse OpenAPI specifications from Stage 03
- Match API endpoints to test files in Stage 05
- Calculate test coverage percentage
- Identify missing tests for API endpoints

RFC-SDLC-602 Compliance:
- Phase 5: Cross-Reference Validation
- SSOT Principle: openapi.json only in Stage 03
- Stage Cross-Reference: Bidirectional links Stage 03 ↔ Stage 05

Zero Mock Policy: Production-ready implementation with real validation
=========================================================================
"""

import logging
import os
import json
import re
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any
from uuid import UUID
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_db, get_current_user
from app.models.user import User
from app.models.project import Project

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/cross-reference", tags=["Cross-Reference"])


# ============================================================================
# Request/Response Models
# ============================================================================


class APIEndpoint(BaseModel):
    """API endpoint from OpenAPI specification."""

    method: str = Field(..., description="HTTP method (GET, POST, PUT, DELETE, PATCH)")
    path: str = Field(..., description="API path (e.g., /api/v1/users)")
    operation_id: Optional[str] = Field(None, description="Operation ID from OpenAPI spec")
    summary: Optional[str] = Field(None, description="Endpoint summary")
    tags: List[str] = Field(default_factory=list, description="Endpoint tags")


class TestFile(BaseModel):
    """Test file covering API endpoints."""

    path: str = Field(..., description="Path to test file")
    endpoints_tested: List[str] = Field(
        default_factory=list,
        description="List of endpoint paths tested (e.g., 'GET /api/v1/users')"
    )
    test_count: int = Field(0, description="Number of test cases in file")


class MissingTest(BaseModel):
    """API endpoint missing test coverage."""

    method: str = Field(..., description="HTTP method")
    path: str = Field(..., description="API path")
    operation_id: Optional[str] = Field(None, description="Operation ID")
    priority: str = Field("medium", description="Priority (high, medium, low)")


class CoverageMetrics(BaseModel):
    """Coverage metrics for cross-reference validation."""

    total: int = Field(0, description="Total API endpoints")
    covered: int = Field(0, description="Endpoints with test coverage")
    uncovered: int = Field(0, description="Endpoints without test coverage")
    percentage: float = Field(0.0, description="Coverage percentage")


class CrossReferenceValidateRequest(BaseModel):
    """Request for cross-reference validation."""

    project_id: UUID = Field(..., description="Project UUID")
    stage_03_path: str = Field(
        "docs/03-integrate",
        description="Path to Stage 03 (Integration) folder"
    )
    stage_05_path: str = Field(
        "docs/05-deploy",
        description="Path to Stage 05 (Testing) folder"
    )
    strict: bool = Field(
        False,
        description="Fail if coverage below 80%"
    )


class CrossReferenceValidateResponse(BaseModel):
    """Response for cross-reference validation."""

    success: bool = Field(..., description="Validation result")
    project_id: UUID = Field(..., description="Project UUID")
    stage_03_path: str = Field(..., description="Stage 03 path used")
    stage_05_path: str = Field(..., description="Stage 05 path used")
    api_endpoints: List[APIEndpoint] = Field(
        default_factory=list,
        description="API endpoints found in OpenAPI spec"
    )
    test_files: List[TestFile] = Field(
        default_factory=list,
        description="Test files found in Stage 05"
    )
    coverage: CoverageMetrics = Field(
        default_factory=CoverageMetrics,
        description="Coverage metrics"
    )
    missing_tests: List[MissingTest] = Field(
        default_factory=list,
        description="Endpoints missing test coverage"
    )
    ssot_compliant: bool = Field(
        True,
        description="SSOT compliance (no duplicate openapi.json)"
    )
    ssot_violations: List[str] = Field(
        default_factory=list,
        description="SSOT violations found"
    )
    validation_timestamp: str = Field(..., description="ISO timestamp of validation")
    message: str = Field("", description="Human-readable result message")


# ============================================================================
# Cross-Reference Validation Service
# ============================================================================


class CrossReferenceService:
    """
    Service for validating Stage 03 ↔ Stage 05 cross-references.

    RFC-SDLC-602 Implementation:
    - Parse OpenAPI from Stage 03
    - Find test files in Stage 05
    - Match endpoints to tests
    - Calculate coverage
    - Check SSOT compliance

    Zero Mock Policy: All validation is production-ready.
    """

    def __init__(self, db: AsyncSession):
        self.db = db

    async def validate(
        self,
        project_id: UUID,
        stage_03_path: str,
        stage_05_path: str,
        project_root: Optional[str] = None,
        strict: bool = False,
    ) -> CrossReferenceValidateResponse:
        """
        Validate cross-references between Stage 03 and Stage 05.

        Args:
            project_id: Project UUID
            stage_03_path: Relative path to Stage 03 folder
            stage_05_path: Relative path to Stage 05 folder
            project_root: Absolute path to project root (optional)
            strict: Fail if coverage < 80%

        Returns:
            CrossReferenceValidateResponse with validation results
        """
        timestamp = datetime.now(timezone.utc).isoformat()

        # Initialize response
        response = CrossReferenceValidateResponse(
            success=True,
            project_id=project_id,
            stage_03_path=stage_03_path,
            stage_05_path=stage_05_path,
            validation_timestamp=timestamp,
        )

        # If no project root provided, try to get from database
        if not project_root:
            project_root = await self._get_project_root(project_id)

        if not project_root:
            response.success = False
            response.message = "Project root path not found"
            return response

        # Build absolute paths
        stage_03_abs = os.path.join(project_root, stage_03_path)
        stage_05_abs = os.path.join(project_root, stage_05_path)

        # Step 1: Parse OpenAPI from Stage 03
        api_endpoints, openapi_path = await self._parse_openapi(stage_03_abs)
        response.api_endpoints = api_endpoints

        if not api_endpoints:
            response.success = False
            response.message = "No OpenAPI specification found in Stage 03"
            return response

        # Step 2: Find test files in Stage 05
        test_files = await self._find_test_files(stage_05_abs, api_endpoints)
        response.test_files = test_files

        # Step 3: Calculate coverage
        coverage = self._calculate_coverage(api_endpoints, test_files)
        response.coverage = coverage

        # Step 4: Identify missing tests
        missing_tests = self._find_missing_tests(api_endpoints, test_files)
        response.missing_tests = missing_tests

        # Step 5: Check SSOT compliance (openapi.json only in Stage 03)
        ssot_compliant, violations = await self._check_ssot(
            project_root, stage_03_path, stage_05_path
        )
        response.ssot_compliant = ssot_compliant
        response.ssot_violations = violations

        # Step 6: Determine success based on strict mode
        if strict and coverage.percentage < 80:
            response.success = False
            response.message = (
                f"Coverage {coverage.percentage:.1f}% is below 80% threshold (strict mode)"
            )
        elif not ssot_compliant:
            response.success = False
            response.message = f"SSOT violations found: {', '.join(violations)}"
        else:
            response.message = (
                f"Cross-reference validation passed. "
                f"Coverage: {coverage.percentage:.1f}% "
                f"({coverage.covered}/{coverage.total} endpoints)"
            )

        logger.info(
            f"Cross-reference validation for project {project_id}: "
            f"success={response.success}, coverage={coverage.percentage:.1f}%"
        )

        return response

    async def _get_project_root(self, project_id: UUID) -> Optional[str]:
        """Get project root path from database."""
        from sqlalchemy import select

        result = await self.db.execute(
            select(Project).where(Project.id == project_id)
        )
        project = result.scalar_one_or_none()

        if project and hasattr(project, "root_path"):
            return project.root_path

        return None

    async def _parse_openapi(
        self, stage_03_path: str
    ) -> tuple[List[APIEndpoint], Optional[str]]:
        """
        Parse OpenAPI specification from Stage 03.

        Searches for:
        - openapi.json
        - openapi.yaml
        - swagger.json
        - swagger.yaml
        - api-specification.json
        - api-specification.yaml

        Returns:
            Tuple of (list of endpoints, path to OpenAPI file)
        """
        endpoints: List[APIEndpoint] = []
        openapi_path: Optional[str] = None

        # Search patterns for OpenAPI files
        patterns = [
            "openapi.json",
            "openapi.yaml",
            "openapi.yml",
            "swagger.json",
            "swagger.yaml",
            "swagger.yml",
            "api-specification.json",
            "api-specification.yaml",
            "**/openapi.json",
            "**/openapi.yaml",
            "01-api-contracts/openapi.json",
            "01-api-contracts/openapi.yaml",
        ]

        # Find OpenAPI file
        for pattern in patterns:
            if "**" in pattern:
                # Glob pattern
                matches = list(Path(stage_03_path).glob(pattern))
                if matches:
                    openapi_path = str(matches[0])
                    break
            else:
                candidate = os.path.join(stage_03_path, pattern)
                if os.path.exists(candidate):
                    openapi_path = candidate
                    break

        if not openapi_path:
            logger.warning(f"No OpenAPI file found in {stage_03_path}")
            return endpoints, None

        # Parse OpenAPI file
        try:
            with open(openapi_path, "r") as f:
                if openapi_path.endswith((".yaml", ".yml")):
                    import yaml
                    spec = yaml.safe_load(f)
                else:
                    spec = json.load(f)

            # Extract endpoints from paths
            paths = spec.get("paths", {})
            for path, methods in paths.items():
                for method, details in methods.items():
                    if method.lower() in ("get", "post", "put", "delete", "patch", "head", "options"):
                        endpoint = APIEndpoint(
                            method=method.upper(),
                            path=path,
                            operation_id=details.get("operationId"),
                            summary=details.get("summary"),
                            tags=details.get("tags", []),
                        )
                        endpoints.append(endpoint)

            logger.info(f"Parsed {len(endpoints)} endpoints from {openapi_path}")

        except Exception as e:
            logger.error(f"Error parsing OpenAPI file {openapi_path}: {e}")

        return endpoints, openapi_path

    async def _find_test_files(
        self, stage_05_path: str, api_endpoints: List[APIEndpoint]
    ) -> List[TestFile]:
        """
        Find test files in Stage 05 and match them to endpoints.

        Searches for:
        - **/test_*.py
        - **/*_test.py
        - **/tests/*.py
        - **/e2e/*.py
        - **/*.postman_collection.json
        - **/*.http
        """
        test_files: List[TestFile] = []

        if not os.path.exists(stage_05_path):
            logger.warning(f"Stage 05 path does not exist: {stage_05_path}")
            return test_files

        # Search patterns for test files
        test_patterns = [
            "**/*test*.py",
            "**/test_*.py",
            "**/*_test.py",
            "**/tests/*.py",
            "**/e2e/*.py",
            "**/*.postman_collection.json",
            "**/*.http",
            "03-E2E-Testing/**/*.py",
            "03-E2E-Testing/**/*.json",
        ]

        found_files = set()
        for pattern in test_patterns:
            matches = list(Path(stage_05_path).glob(pattern))
            for match in matches:
                found_files.add(str(match))

        # Analyze each test file
        for file_path in found_files:
            endpoints_tested = self._extract_tested_endpoints(file_path, api_endpoints)
            test_count = self._count_tests(file_path)

            # Get relative path from stage_05_path
            rel_path = os.path.relpath(file_path, stage_05_path)

            test_file = TestFile(
                path=rel_path,
                endpoints_tested=endpoints_tested,
                test_count=test_count,
            )
            test_files.append(test_file)

        logger.info(f"Found {len(test_files)} test files in {stage_05_path}")
        return test_files

    def _extract_tested_endpoints(
        self, file_path: str, api_endpoints: List[APIEndpoint]
    ) -> List[str]:
        """
        Extract which endpoints are tested in a file.

        Uses pattern matching to find:
        - URL patterns matching API paths
        - HTTP method + path combinations
        """
        tested: List[str] = []

        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()

            # Build patterns for each endpoint
            for endpoint in api_endpoints:
                # Convert path template to regex
                path_pattern = endpoint.path.replace("{", "(?:").replace("}", "|[^/]+)")

                # Match patterns like:
                # - /api/v1/users
                # - POST /api/v1/users
                # - "path": "/api/v1/users"
                patterns = [
                    rf'["\']?{re.escape(endpoint.method)}["\']?\s*[,:]?\s*["\']?{path_pattern}',
                    rf'{path_pattern}',
                    rf'requests\.{endpoint.method.lower()}\s*\(\s*[f"\'].*{path_pattern}',
                ]

                for pattern in patterns:
                    if re.search(pattern, content, re.IGNORECASE):
                        endpoint_key = f"{endpoint.method} {endpoint.path}"
                        if endpoint_key not in tested:
                            tested.append(endpoint_key)
                        break

        except Exception as e:
            logger.debug(f"Error reading test file {file_path}: {e}")

        return tested

    def _count_tests(self, file_path: str) -> int:
        """Count number of test cases in a file."""
        count = 0

        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()

            # Python test patterns
            count += len(re.findall(r"def\s+test_\w+", content))
            count += len(re.findall(r"@pytest\.mark\.", content))

            # Postman collection patterns
            if file_path.endswith(".json"):
                count += content.count('"name":')

            # HTTP file patterns
            if file_path.endswith(".http"):
                count += len(re.findall(r"^(GET|POST|PUT|DELETE|PATCH)\s+", content, re.MULTILINE))

        except Exception as e:
            logger.debug(f"Error counting tests in {file_path}: {e}")

        return count

    def _calculate_coverage(
        self, api_endpoints: List[APIEndpoint], test_files: List[TestFile]
    ) -> CoverageMetrics:
        """Calculate test coverage metrics."""
        total = len(api_endpoints)
        if total == 0:
            return CoverageMetrics(total=0, covered=0, uncovered=0, percentage=0.0)

        # Collect all tested endpoints
        tested_endpoints = set()
        for test_file in test_files:
            for endpoint in test_file.endpoints_tested:
                tested_endpoints.add(endpoint)

        # Count covered endpoints
        covered = 0
        for endpoint in api_endpoints:
            endpoint_key = f"{endpoint.method} {endpoint.path}"
            if endpoint_key in tested_endpoints:
                covered += 1

        uncovered = total - covered
        percentage = (covered / total) * 100 if total > 0 else 0.0

        return CoverageMetrics(
            total=total,
            covered=covered,
            uncovered=uncovered,
            percentage=round(percentage, 1),
        )

    def _find_missing_tests(
        self, api_endpoints: List[APIEndpoint], test_files: List[TestFile]
    ) -> List[MissingTest]:
        """Find endpoints that don't have test coverage."""
        missing: List[MissingTest] = []

        # Collect all tested endpoints
        tested_endpoints = set()
        for test_file in test_files:
            for endpoint in test_file.endpoints_tested:
                tested_endpoints.add(endpoint)

        # Find missing
        for endpoint in api_endpoints:
            endpoint_key = f"{endpoint.method} {endpoint.path}"
            if endpoint_key not in tested_endpoints:
                # Determine priority based on method and path
                priority = self._determine_priority(endpoint)
                missing.append(MissingTest(
                    method=endpoint.method,
                    path=endpoint.path,
                    operation_id=endpoint.operation_id,
                    priority=priority,
                ))

        # Sort by priority
        priority_order = {"high": 0, "medium": 1, "low": 2}
        missing.sort(key=lambda x: priority_order.get(x.priority, 1))

        return missing

    def _determine_priority(self, endpoint: APIEndpoint) -> str:
        """Determine test priority for an endpoint."""
        # High priority: Authentication, payments, security-sensitive
        high_priority_patterns = [
            r"/auth",
            r"/login",
            r"/logout",
            r"/token",
            r"/password",
            r"/payment",
            r"/billing",
            r"/admin",
            r"/security",
        ]

        for pattern in high_priority_patterns:
            if re.search(pattern, endpoint.path, re.IGNORECASE):
                return "high"

        # Medium priority: CRUD operations
        if endpoint.method in ("POST", "PUT", "DELETE", "PATCH"):
            return "medium"

        # Low priority: GET operations
        return "low"

    async def _check_ssot(
        self, project_root: str, stage_03_path: str, stage_05_path: str
    ) -> tuple[bool, List[str]]:
        """
        Check SSOT compliance: openapi.json should only exist in Stage 03.

        Per RFC-SDLC-602:
        - openapi.json is SSOT, stored only in Stage 03
        - Stage 05 should NOT have duplicate openapi.json
        - Other folders should NOT have openapi.json
        """
        violations: List[str] = []

        # Check Stage 05 for duplicate openapi files
        stage_05_abs = os.path.join(project_root, stage_05_path)
        if os.path.exists(stage_05_abs):
            duplicate_patterns = ["**/openapi.json", "**/openapi.yaml", "**/swagger.json"]
            for pattern in duplicate_patterns:
                matches = list(Path(stage_05_abs).glob(pattern))
                for match in matches:
                    rel_path = os.path.relpath(str(match), project_root)
                    violations.append(f"Duplicate OpenAPI file in Stage 05: {rel_path}")

        # Check other common locations that should not have OpenAPI
        other_paths = [
            "backend",
            "frontend",
            "src",
            "docs/01-planning",
            "docs/02-design",
            "docs/04-build",
        ]

        for other_path in other_paths:
            abs_path = os.path.join(project_root, other_path)
            if os.path.exists(abs_path):
                for pattern in ["**/openapi.json", "**/openapi.yaml"]:
                    matches = list(Path(abs_path).glob(pattern))
                    for match in matches:
                        rel_path = os.path.relpath(str(match), project_root)
                        violations.append(f"OpenAPI file outside Stage 03: {rel_path}")

        ssot_compliant = len(violations) == 0
        return ssot_compliant, violations


# ============================================================================
# Endpoints
# ============================================================================


@router.post("/validate", response_model=CrossReferenceValidateResponse)
async def validate_cross_reference(
    request: CrossReferenceValidateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> CrossReferenceValidateResponse:
    """
    Validate cross-references between Stage 03 and Stage 05.

    RFC-SDLC-602 Phase 5: Cross-Reference Validation

    This endpoint:
    1. Parses OpenAPI specification from Stage 03
    2. Finds test files in Stage 05
    3. Matches API endpoints to test coverage
    4. Calculates coverage percentage
    5. Checks SSOT compliance (no duplicate openapi.json)

    Args:
        request: CrossReferenceValidateRequest with project_id and paths

    Returns:
        CrossReferenceValidateResponse with validation results
    """
    service = CrossReferenceService(db)
    return await service.validate(
        project_id=request.project_id,
        stage_03_path=request.stage_03_path,
        stage_05_path=request.stage_05_path,
        strict=request.strict,
    )


@router.get("/coverage/{project_id}", response_model=CoverageMetrics)
async def get_coverage(
    project_id: UUID,
    stage_03_path: str = "docs/03-integrate",
    stage_05_path: str = "docs/05-deploy",
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> CoverageMetrics:
    """
    Get quick coverage metrics for a project.

    Returns only coverage statistics without full validation details.
    """
    service = CrossReferenceService(db)
    result = await service.validate(
        project_id=project_id,
        stage_03_path=stage_03_path,
        stage_05_path=stage_05_path,
        strict=False,
    )
    return result.coverage


@router.get("/missing-tests/{project_id}", response_model=List[MissingTest])
async def get_missing_tests(
    project_id: UUID,
    stage_03_path: str = "docs/03-integrate",
    stage_05_path: str = "docs/05-deploy",
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> List[MissingTest]:
    """
    Get list of endpoints missing test coverage.

    Returns prioritized list of endpoints that need tests.
    """
    service = CrossReferenceService(db)
    result = await service.validate(
        project_id=project_id,
        stage_03_path=stage_03_path,
        stage_05_path=stage_05_path,
        strict=False,
    )
    return result.missing_tests[:limit]


@router.get("/ssot-check/{project_id}")
async def check_ssot_compliance(
    project_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Dict[str, Any]:
    """
    Check SSOT compliance for OpenAPI specification.

    Per RFC-SDLC-602:
    - openapi.json should only exist in Stage 03
    - No duplicates in Stage 05 or other folders
    """
    service = CrossReferenceService(db)
    result = await service.validate(
        project_id=project_id,
        stage_03_path="docs/03-integrate",
        stage_05_path="docs/05-deploy",
        strict=False,
    )

    return {
        "project_id": str(project_id),
        "ssot_compliant": result.ssot_compliant,
        "violations": result.ssot_violations,
        "message": (
            "SSOT compliant: OpenAPI is only in Stage 03"
            if result.ssot_compliant
            else f"SSOT violations found: {len(result.ssot_violations)}"
        ),
        "checked_at": result.validation_timestamp,
    }
