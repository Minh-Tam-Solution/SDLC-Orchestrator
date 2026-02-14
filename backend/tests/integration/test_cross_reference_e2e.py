"""
=========================================================================
Cross-Reference Validation E2E Tests
SDLC Orchestrator - Sprint 155 Day 5 (Track 2: E2E Integration)

Version: 1.0.0
Date: February 5, 2026
Status: ACTIVE - Sprint 155 Testing
Authority: Backend Lead + CTO Approved
Framework: SDLC 6.0.5

E2E Test Scenarios:
1. Full validation workflow (validate → orphaned → links)
2. Single document validation with violations
3. Project validation with no violations
4. Orphaned documents detection
5. Document links retrieval
6. Validation type filtering
7. Error handling (invalid input, service errors)
8. Multi-step workflow chain

TDD RED Phase: Write failing tests first
=========================================================================
"""

from datetime import datetime
from typing import List
from unittest.mock import AsyncMock, patch
from uuid import uuid4

import pytest
from fastapi import status
from httpx import ASGITransport, AsyncClient

from app.main import app
from app.services.cross_reference_service import (
    CrossReferenceService,
    CrossReferenceViolation,
    DocumentLinks,
    ValidationResult,
)


# =========================================================================
# Fixtures
# =========================================================================


@pytest.fixture
def project_id():
    """Generate a unique project ID per test."""
    return uuid4()


@pytest.fixture
def headers():
    """Standard request headers."""
    return {"Authorization": "Bearer e2e-test-token"}


@pytest.fixture
def mock_service():
    """Create a mock CrossReferenceService with default returns."""
    service = AsyncMock(spec=CrossReferenceService)

    # Default: valid project
    service.validate_project.return_value = ValidationResult(
        is_valid=True,
        violations=[],
        scanned_files=25,
        total_links=100,
    )

    service.validate_document.return_value = ValidationResult(
        is_valid=True,
        violations=[],
        scanned_files=1,
        total_links=5,
    )

    service.get_orphaned_documents.return_value = []

    service.get_document_links.return_value = DocumentLinks(
        document_path="test.md",
        incoming=[],
        outgoing=[],
    )

    return service


# =========================================================================
# E2E Workflow Tests
# =========================================================================


class TestE2EFullValidationWorkflow:
    """End-to-end workflow tests spanning multiple endpoints."""

    @pytest.mark.asyncio
    async def test_full_workflow_validate_then_check_orphaned_then_links(
        self,
        project_id,
        headers,
    ):
        """
        Full E2E workflow:
        1. Validate project → Get result
        2. Check for orphaned documents
        3. Get links for a specific document
        """
        broken_violation = CrossReferenceViolation(
            violation_type="broken_link",
            source_file="docs/02-design/14-Technical-Specs/SPEC-0001.md",
            target_file="docs/02-design/01-ADRs/ADR-999.md",
            message="Target file does not exist",
            severity="error",
        )

        with patch(
            "app.api.routes.cross_reference_validation.get_cross_reference_service"
        ) as mock_get:
            mock_svc = AsyncMock(spec=CrossReferenceService)

            # Step 1: Project validation returns violations
            mock_svc.validate_project.return_value = ValidationResult(
                is_valid=False,
                violations=[broken_violation],
                scanned_files=30,
                total_links=150,
            )

            # Step 2: Orphaned docs returns 1 orphan
            mock_svc.get_orphaned_documents.return_value = [
                {
                    "document_path": "docs/02-design/14-Technical-Specs/SPEC-0099.md",
                    "document_type": "SPEC",
                    "reason": "No incoming or outgoing references",
                }
            ]

            # Step 3: Document links returns bidirectional links
            mock_svc.get_document_links.return_value = DocumentLinks(
                document_path="docs/02-design/14-Technical-Specs/SPEC-0001.md",
                incoming=[
                    {"source": "docs/02-design/01-ADRs/ADR-001.md", "type": "adr_ref", "line": 15},
                ],
                outgoing=[
                    {"target": "docs/02-design/01-ADRs/ADR-999.md", "type": "adr_ref", "line": 42},
                ],
            )

            mock_get.return_value = mock_svc

            async with AsyncClient(
                transport=ASGITransport(app=app),
                base_url="http://test",
            ) as client:
                # Step 1: Validate project
                resp1 = await client.post(
                    "/api/v1/doc-cross-reference/validate-project",
                    json={
                        "project_id": str(project_id),
                        "project_path": "/path/to/project",
                    },
                    headers=headers,
                )
                assert resp1.status_code == status.HTTP_200_OK
                data1 = resp1.json()
                assert data1["is_valid"] is False
                assert len(data1["violations"]) == 1
                assert data1["scanned_files"] == 30
                assert data1["total_links"] == 150

                # Step 2: Check orphaned documents
                resp2 = await client.get(
                    "/api/v1/doc-cross-reference/orphaned",
                    params={"project_id": str(project_id)},
                    headers=headers,
                )
                assert resp2.status_code == status.HTTP_200_OK
                data2 = resp2.json()
                assert len(data2["orphaned_documents"]) == 1
                assert data2["orphaned_documents"][0]["document_type"] == "SPEC"

                # Step 3: Get links for the violating document
                resp3 = await client.get(
                    "/api/v1/doc-cross-reference/links",
                    params={
                        "project_id": str(project_id),
                        "document_path": "docs/02-design/14-Technical-Specs/SPEC-0001.md",
                    },
                    headers=headers,
                )
                assert resp3.status_code == status.HTTP_200_OK
                data3 = resp3.json()
                assert len(data3["incoming"]) == 1
                assert len(data3["outgoing"]) == 1
                assert data3["outgoing"][0]["target"] == "docs/02-design/01-ADRs/ADR-999.md"

    @pytest.mark.asyncio
    async def test_validate_document_then_validate_project(
        self,
        project_id,
        headers,
    ):
        """E2E: Validate single doc, then full project scan."""
        with patch(
            "app.api.routes.cross_reference_validation.get_cross_reference_service"
        ) as mock_get:
            mock_svc = AsyncMock(spec=CrossReferenceService)

            # Single doc has issues
            mock_svc.validate_document.return_value = ValidationResult(
                is_valid=False,
                violations=[
                    CrossReferenceViolation(
                        violation_type="broken_link",
                        source_file="SPEC-0001.md",
                        target_file="ADR-999.md",
                        message="Broken link",
                    )
                ],
                scanned_files=1,
                total_links=3,
            )

            # Full project also has issues
            mock_svc.validate_project.return_value = ValidationResult(
                is_valid=False,
                violations=[
                    CrossReferenceViolation(
                        violation_type="broken_link",
                        source_file="SPEC-0001.md",
                        target_file="ADR-999.md",
                        message="Broken link",
                    ),
                    CrossReferenceViolation(
                        violation_type="missing_backlink",
                        source_file="ADR-001.md",
                        target_file="SPEC-0001.md",
                        message="Missing backlink",
                    ),
                ],
                scanned_files=50,
                total_links=200,
            )

            mock_get.return_value = mock_svc

            async with AsyncClient(
                transport=ASGITransport(app=app),
                base_url="http://test",
            ) as client:
                # Step 1: Validate single document
                resp1 = await client.post(
                    "/api/v1/doc-cross-reference/validate",
                    json={
                        "project_id": str(project_id),
                        "document_path": "SPEC-0001.md",
                    },
                    headers=headers,
                )
                assert resp1.status_code == 200
                data1 = resp1.json()
                assert data1["is_valid"] is False
                assert len(data1["violations"]) == 1

                # Step 2: Full project validation shows more issues
                resp2 = await client.post(
                    "/api/v1/doc-cross-reference/validate-project",
                    json={
                        "project_id": str(project_id),
                        "project_path": "/project",
                    },
                    headers=headers,
                )
                assert resp2.status_code == 200
                data2 = resp2.json()
                assert data2["is_valid"] is False
                assert len(data2["violations"]) == 2
                assert data2["scanned_files"] == 50


# =========================================================================
# Validation Type Filtering
# =========================================================================


class TestE2EValidationFiltering:
    """Test validation filtering across endpoints."""

    @pytest.mark.asyncio
    async def test_filter_violations_by_broken_link(
        self,
        project_id,
        headers,
    ):
        """Filter project violations to show only broken links."""
        with patch(
            "app.api.routes.cross_reference_validation.get_cross_reference_service"
        ) as mock_get:
            mock_svc = AsyncMock(spec=CrossReferenceService)
            mock_svc.validate_project.return_value = ValidationResult(
                is_valid=False,
                violations=[
                    CrossReferenceViolation(
                        violation_type="broken_link",
                        source_file="SPEC-0001.md",
                        target_file="ADR-999.md",
                        message="Broken",
                    ),
                    CrossReferenceViolation(
                        violation_type="missing_backlink",
                        source_file="ADR-001.md",
                        target_file="SPEC-0001.md",
                        message="Missing backlink",
                    ),
                    CrossReferenceViolation(
                        violation_type="orphaned_document",
                        source_file="SPEC-0099.md",
                        message="Orphaned",
                    ),
                ],
                scanned_files=50,
                total_links=200,
            )
            mock_get.return_value = mock_svc

            async with AsyncClient(
                transport=ASGITransport(app=app),
                base_url="http://test",
            ) as client:
                response = await client.post(
                    "/api/v1/doc-cross-reference/validate-project",
                    json={
                        "project_id": str(project_id),
                        "project_path": "/project",
                        "violation_types": ["broken_link"],
                    },
                    headers=headers,
                )

            assert response.status_code == 200
            data = response.json()
            assert len(data["violations"]) == 1
            assert data["violations"][0]["violation_type"] == "broken_link"

    @pytest.mark.asyncio
    async def test_filter_orphaned_by_adr_type(
        self,
        project_id,
        headers,
    ):
        """Filter orphaned documents to show only ADRs."""
        with patch(
            "app.api.routes.cross_reference_validation.get_cross_reference_service"
        ) as mock_get:
            mock_svc = AsyncMock(spec=CrossReferenceService)
            mock_svc.get_orphaned_documents.return_value = [
                {
                    "document_path": "ADR-099.md",
                    "document_type": "ADR",
                    "reason": "No references",
                },
            ]
            mock_get.return_value = mock_svc

            async with AsyncClient(
                transport=ASGITransport(app=app),
                base_url="http://test",
            ) as client:
                response = await client.get(
                    "/api/v1/doc-cross-reference/orphaned",
                    params={
                        "project_id": str(project_id),
                        "document_type": "ADR",
                    },
                    headers=headers,
                )

            assert response.status_code == 200
            data = response.json()
            assert len(data["orphaned_documents"]) == 1
            assert data["orphaned_documents"][0]["document_type"] == "ADR"


# =========================================================================
# Document Links Direction
# =========================================================================


class TestE2EDocumentLinksDirection:
    """Test document links with direction filtering."""

    @pytest.mark.asyncio
    async def test_get_incoming_links_only(
        self,
        project_id,
        headers,
    ):
        """Get only incoming links for a document."""
        with patch(
            "app.api.routes.cross_reference_validation.get_cross_reference_service"
        ) as mock_get:
            mock_svc = AsyncMock(spec=CrossReferenceService)
            mock_svc.get_document_links.return_value = DocumentLinks(
                document_path="SPEC-0001.md",
                incoming=[
                    {"source": "ADR-001.md", "type": "adr_ref", "line": 10},
                    {"source": "ADR-002.md", "type": "adr_ref", "line": 25},
                ],
                outgoing=[],
            )
            mock_get.return_value = mock_svc

            async with AsyncClient(
                transport=ASGITransport(app=app),
                base_url="http://test",
            ) as client:
                response = await client.get(
                    "/api/v1/doc-cross-reference/links",
                    params={
                        "project_id": str(project_id),
                        "document_path": "SPEC-0001.md",
                        "direction": "incoming",
                    },
                    headers=headers,
                )

            assert response.status_code == 200
            data = response.json()
            assert len(data["incoming"]) == 2
            assert data["document_path"] == "SPEC-0001.md"

    @pytest.mark.asyncio
    async def test_get_outgoing_links_only(
        self,
        project_id,
        headers,
    ):
        """Get only outgoing links from a document."""
        with patch(
            "app.api.routes.cross_reference_validation.get_cross_reference_service"
        ) as mock_get:
            mock_svc = AsyncMock(spec=CrossReferenceService)
            mock_svc.get_document_links.return_value = DocumentLinks(
                document_path="ADR-001.md",
                incoming=[],
                outgoing=[
                    {"target": "SPEC-0001.md", "type": "spec_ref", "line": 15},
                ],
            )
            mock_get.return_value = mock_svc

            async with AsyncClient(
                transport=ASGITransport(app=app),
                base_url="http://test",
            ) as client:
                response = await client.get(
                    "/api/v1/doc-cross-reference/links",
                    params={
                        "project_id": str(project_id),
                        "document_path": "ADR-001.md",
                        "direction": "outgoing",
                    },
                    headers=headers,
                )

            assert response.status_code == 200
            data = response.json()
            assert len(data["outgoing"]) == 1


# =========================================================================
# Error Handling E2E
# =========================================================================


class TestE2EErrorHandling:
    """Test error scenarios across all endpoints."""

    @pytest.mark.asyncio
    async def test_invalid_uuid_returns_422(self, headers):
        """Invalid UUID format returns 422."""
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
        ) as client:
            response = await client.post(
                "/api/v1/doc-cross-reference/validate",
                json={
                    "project_id": "not-a-valid-uuid",
                    "document_path": "test.md",
                },
                headers=headers,
            )
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    @pytest.mark.asyncio
    async def test_missing_required_field_returns_422(self, headers):
        """Missing required fields return 422."""
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
        ) as client:
            # Missing document_path
            response = await client.post(
                "/api/v1/doc-cross-reference/validate",
                json={"project_id": str(uuid4())},
                headers=headers,
            )
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    @pytest.mark.asyncio
    async def test_service_exception_returns_500(self, project_id, headers):
        """Internal service error returns 500."""
        with patch(
            "app.api.routes.cross_reference_validation.get_cross_reference_service"
        ) as mock_get:
            mock_svc = AsyncMock(spec=CrossReferenceService)
            mock_svc.validate_project.side_effect = RuntimeError(
                "Database connection failed"
            )
            mock_get.return_value = mock_svc

            async with AsyncClient(
                transport=ASGITransport(app=app),
                base_url="http://test",
            ) as client:
                response = await client.post(
                    "/api/v1/doc-cross-reference/validate-project",
                    json={
                        "project_id": str(project_id),
                        "project_path": "/project",
                    },
                    headers=headers,
                )

            assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
