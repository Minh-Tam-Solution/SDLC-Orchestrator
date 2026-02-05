"""
=========================================================================
Cross-Reference API Routes Tests
SDLC Orchestrator - Sprint 155 Day 4 (Track 2: Cross-Reference Validation)

Version: 1.0.0
Date: February 4, 2026
Status: ACTIVE - Sprint 155 Testing
Authority: Backend Lead + CTO Approved
Framework: SDLC 6.0.4

Test Coverage:
- POST /api/v1/doc-cross-reference/validate - Validate single document
- POST /api/v1/doc-cross-reference/validate-project - Full project validation
- GET /api/v1/doc-cross-reference/orphaned - Get orphaned documents
- GET /api/v1/doc-cross-reference/links/{document_id} - Get document links

TDD RED Phase: Write failing tests first
=========================================================================
"""

from datetime import datetime
from typing import List
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import UUID, uuid4

import pytest
from fastapi import status
from httpx import ASGITransport, AsyncClient

from app.main import app
from app.services.cross_reference_service import (
    CrossReferenceService,
    CrossReferenceViolation,
    DocumentLinks,
    LinkType,
    ValidationResult,
)


# =========================================================================
# Fixtures
# =========================================================================


@pytest.fixture
def sample_project_id():
    """Sample project UUID."""
    return uuid4()


@pytest.fixture
def sample_violations():
    """Sample validation violations."""
    return [
        CrossReferenceViolation(
            violation_type="broken_link",
            source_file="docs/02-design/14-Technical-Specs/SPEC-0001.md",
            target_file="docs/02-design/01-ADRs/ADR-999.md",
            message="Target file does not exist",
        ),
        CrossReferenceViolation(
            violation_type="missing_backlink",
            source_file="docs/02-design/01-ADRs/ADR-001.md",
            target_file="docs/02-design/14-Technical-Specs/SPEC-0001.md",
            message="ADR references Spec but Spec does not reference ADR",
        ),
    ]


@pytest.fixture
def sample_validation_result(sample_violations):
    """Sample validation result."""
    return ValidationResult(
        is_valid=False,
        violations=sample_violations,
        scanned_files=10,
        total_links=25,
    )


@pytest.fixture
def sample_document_links():
    """Sample document links."""
    return DocumentLinks(
        document_path="docs/02-design/14-Technical-Specs/SPEC-0001.md",
        incoming=[
            {"source": "docs/02-design/01-ADRs/ADR-001.md", "type": "adr_ref"},
            {"source": "docs/02-design/01-ADRs/ADR-002.md", "type": "adr_ref"},
        ],
        outgoing=[
            {"target": "docs/02-design/01-ADRs/ADR-001.md", "type": "adr_ref"},
        ],
    )


@pytest.fixture
def mock_auth_headers():
    """Mock authentication headers."""
    return {"Authorization": "Bearer test-token"}


# =========================================================================
# Test: POST /api/v1/doc-cross-reference/validate
# =========================================================================


class TestValidateSingleDocument:
    """Test single document validation endpoint."""

    @pytest.mark.asyncio
    async def test_validate_document_success(
        self,
        sample_project_id: UUID,
        mock_auth_headers: dict,
    ):
        """Test successful document validation with no violations."""
        with patch(
            "app.api.routes.cross_reference_validation.get_cross_reference_service"
        ) as mock_get_service:
            mock_service = AsyncMock(spec=CrossReferenceService)
            mock_service.validate_document.return_value = ValidationResult(
                is_valid=True,
                violations=[],
                scanned_files=1,
                total_links=5,
            )
            mock_get_service.return_value = mock_service

            async with AsyncClient(
                transport=ASGITransport(app=app),
                base_url="http://test",
            ) as client:
                response = await client.post(
                    f"/api/v1/doc-cross-reference/validate",
                    json={
                        "project_id": str(sample_project_id),
                        "document_path": "docs/02-design/14-Technical-Specs/SPEC-0001.md",
                    },
                    headers=mock_auth_headers,
                )

            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data["is_valid"] is True
            assert len(data["violations"]) == 0

    @pytest.mark.asyncio
    async def test_validate_document_with_violations(
        self,
        sample_project_id: UUID,
        sample_validation_result: ValidationResult,
        mock_auth_headers: dict,
    ):
        """Test document validation with violations."""
        with patch(
            "app.api.routes.cross_reference_validation.get_cross_reference_service"
        ) as mock_get_service:
            mock_service = AsyncMock(spec=CrossReferenceService)
            mock_service.validate_document.return_value = sample_validation_result
            mock_get_service.return_value = mock_service

            async with AsyncClient(
                transport=ASGITransport(app=app),
                base_url="http://test",
            ) as client:
                response = await client.post(
                    f"/api/v1/doc-cross-reference/validate",
                    json={
                        "project_id": str(sample_project_id),
                        "document_path": "docs/02-design/14-Technical-Specs/SPEC-0001.md",
                    },
                    headers=mock_auth_headers,
                )

            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data["is_valid"] is False
            assert len(data["violations"]) == 2

    @pytest.mark.asyncio
    async def test_validate_document_missing_path(
        self,
        sample_project_id: UUID,
        mock_auth_headers: dict,
    ):
        """Test validation with missing document path."""
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
        ) as client:
            response = await client.post(
                f"/api/v1/doc-cross-reference/validate",
                json={
                    "project_id": str(sample_project_id),
                    # Missing document_path
                },
                headers=mock_auth_headers,
            )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


# =========================================================================
# Test: POST /api/v1/doc-cross-reference/validate-project
# =========================================================================


class TestValidateProject:
    """Test full project validation endpoint."""

    @pytest.mark.asyncio
    async def test_validate_project_success(
        self,
        sample_project_id: UUID,
        mock_auth_headers: dict,
    ):
        """Test successful project validation."""
        with patch(
            "app.api.routes.cross_reference_validation.get_cross_reference_service"
        ) as mock_get_service:
            mock_service = AsyncMock(spec=CrossReferenceService)
            mock_service.validate_project.return_value = ValidationResult(
                is_valid=True,
                violations=[],
                scanned_files=50,
                total_links=200,
            )
            mock_get_service.return_value = mock_service

            async with AsyncClient(
                transport=ASGITransport(app=app),
                base_url="http://test",
            ) as client:
                response = await client.post(
                    f"/api/v1/doc-cross-reference/validate-project",
                    json={
                        "project_id": str(sample_project_id),
                        "project_path": "/path/to/project",
                    },
                    headers=mock_auth_headers,
                )

            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data["is_valid"] is True
            assert data["scanned_files"] == 50
            assert data["total_links"] == 200

    @pytest.mark.asyncio
    async def test_validate_project_with_violations(
        self,
        sample_project_id: UUID,
        sample_violations: List[CrossReferenceViolation],
        mock_auth_headers: dict,
    ):
        """Test project validation with violations."""
        with patch(
            "app.api.routes.cross_reference_validation.get_cross_reference_service"
        ) as mock_get_service:
            mock_service = AsyncMock(spec=CrossReferenceService)
            mock_service.validate_project.return_value = ValidationResult(
                is_valid=False,
                violations=sample_violations,
                scanned_files=50,
                total_links=200,
            )
            mock_get_service.return_value = mock_service

            async with AsyncClient(
                transport=ASGITransport(app=app),
                base_url="http://test",
            ) as client:
                response = await client.post(
                    f"/api/v1/doc-cross-reference/validate-project",
                    json={
                        "project_id": str(sample_project_id),
                        "project_path": "/path/to/project",
                    },
                    headers=mock_auth_headers,
                )

            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data["is_valid"] is False
            assert len(data["violations"]) >= 1

    @pytest.mark.asyncio
    async def test_validate_project_filter_by_type(
        self,
        sample_project_id: UUID,
        mock_auth_headers: dict,
    ):
        """Test project validation with violation type filter."""
        with patch(
            "app.api.routes.cross_reference_validation.get_cross_reference_service"
        ) as mock_get_service:
            mock_service = AsyncMock(spec=CrossReferenceService)
            mock_service.validate_project.return_value = ValidationResult(
                is_valid=False,
                violations=[
                    CrossReferenceViolation(
                        violation_type="broken_link",
                        source_file="SPEC-0001.md",
                        target_file="ADR-999.md",
                        message="Broken link",
                    )
                ],
                scanned_files=50,
                total_links=200,
            )
            mock_get_service.return_value = mock_service

            async with AsyncClient(
                transport=ASGITransport(app=app),
                base_url="http://test",
            ) as client:
                response = await client.post(
                    f"/api/v1/doc-cross-reference/validate-project",
                    json={
                        "project_id": str(sample_project_id),
                        "project_path": "/path/to/project",
                        "violation_types": ["broken_link"],
                    },
                    headers=mock_auth_headers,
                )

            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            # All violations should be of the filtered type
            for v in data["violations"]:
                assert v["violation_type"] == "broken_link"


# =========================================================================
# Test: GET /api/v1/doc-cross-reference/orphaned
# =========================================================================


class TestGetOrphanedDocuments:
    """Test orphaned documents endpoint."""

    @pytest.mark.asyncio
    async def test_get_orphaned_documents_success(
        self,
        sample_project_id: UUID,
        mock_auth_headers: dict,
    ):
        """Test getting orphaned documents."""
        with patch(
            "app.api.routes.cross_reference_validation.get_cross_reference_service"
        ) as mock_get_service:
            mock_service = AsyncMock(spec=CrossReferenceService)
            mock_service.get_orphaned_documents.return_value = [
                {
                    "document_path": "docs/02-design/14-Technical-Specs/SPEC-0099.md",
                    "document_type": "SPEC",
                    "reason": "No incoming or outgoing references",
                }
            ]
            mock_get_service.return_value = mock_service

            async with AsyncClient(
                transport=ASGITransport(app=app),
                base_url="http://test",
            ) as client:
                response = await client.get(
                    f"/api/v1/doc-cross-reference/orphaned",
                    params={"project_id": str(sample_project_id)},
                    headers=mock_auth_headers,
                )

            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert "orphaned_documents" in data
            assert len(data["orphaned_documents"]) == 1

    @pytest.mark.asyncio
    async def test_get_orphaned_documents_empty(
        self,
        sample_project_id: UUID,
        mock_auth_headers: dict,
    ):
        """Test getting orphaned documents when none exist."""
        with patch(
            "app.api.routes.cross_reference_validation.get_cross_reference_service"
        ) as mock_get_service:
            mock_service = AsyncMock(spec=CrossReferenceService)
            mock_service.get_orphaned_documents.return_value = []
            mock_get_service.return_value = mock_service

            async with AsyncClient(
                transport=ASGITransport(app=app),
                base_url="http://test",
            ) as client:
                response = await client.get(
                    f"/api/v1/doc-cross-reference/orphaned",
                    params={"project_id": str(sample_project_id)},
                    headers=mock_auth_headers,
                )

            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data["orphaned_documents"] == []

    @pytest.mark.asyncio
    async def test_get_orphaned_documents_filter_by_type(
        self,
        sample_project_id: UUID,
        mock_auth_headers: dict,
    ):
        """Test getting orphaned documents filtered by document type."""
        with patch(
            "app.api.routes.cross_reference_validation.get_cross_reference_service"
        ) as mock_get_service:
            mock_service = AsyncMock(spec=CrossReferenceService)
            mock_service.get_orphaned_documents.return_value = [
                {
                    "document_path": "docs/02-design/01-ADRs/ADR-0099.md",
                    "document_type": "ADR",
                    "reason": "No references to or from this ADR",
                }
            ]
            mock_get_service.return_value = mock_service

            async with AsyncClient(
                transport=ASGITransport(app=app),
                base_url="http://test",
            ) as client:
                response = await client.get(
                    f"/api/v1/doc-cross-reference/orphaned",
                    params={
                        "project_id": str(sample_project_id),
                        "document_type": "ADR",
                    },
                    headers=mock_auth_headers,
                )

            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            for doc in data["orphaned_documents"]:
                assert doc["document_type"] == "ADR"


# =========================================================================
# Test: GET /api/v1/doc-cross-reference/links/{document_id}
# =========================================================================


class TestGetDocumentLinks:
    """Test document links endpoint."""

    @pytest.mark.asyncio
    async def test_get_document_links_success(
        self,
        sample_project_id: UUID,
        sample_document_links: DocumentLinks,
        mock_auth_headers: dict,
    ):
        """Test getting links for a document."""
        document_path = "docs/02-design/14-Technical-Specs/SPEC-0001.md"

        with patch(
            "app.api.routes.cross_reference_validation.get_cross_reference_service"
        ) as mock_get_service:
            mock_service = AsyncMock(spec=CrossReferenceService)
            mock_service.get_document_links.return_value = sample_document_links
            mock_get_service.return_value = mock_service

            async with AsyncClient(
                transport=ASGITransport(app=app),
                base_url="http://test",
            ) as client:
                response = await client.get(
                    f"/api/v1/doc-cross-reference/links",
                    params={
                        "project_id": str(sample_project_id),
                        "document_path": document_path,
                    },
                    headers=mock_auth_headers,
                )

            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert "incoming" in data
            assert "outgoing" in data
            assert len(data["incoming"]) == 2
            assert len(data["outgoing"]) == 1

    @pytest.mark.asyncio
    async def test_get_document_links_incoming_only(
        self,
        sample_project_id: UUID,
        mock_auth_headers: dict,
    ):
        """Test getting only incoming links for a document."""
        document_path = "docs/02-design/14-Technical-Specs/SPEC-0001.md"

        with patch(
            "app.api.routes.cross_reference_validation.get_cross_reference_service"
        ) as mock_get_service:
            mock_service = AsyncMock(spec=CrossReferenceService)
            mock_service.get_document_links.return_value = DocumentLinks(
                document_path=document_path,
                incoming=[
                    {"source": "ADR-001.md", "type": "adr_ref"},
                ],
                outgoing=[],
            )
            mock_get_service.return_value = mock_service

            async with AsyncClient(
                transport=ASGITransport(app=app),
                base_url="http://test",
            ) as client:
                response = await client.get(
                    f"/api/v1/doc-cross-reference/links",
                    params={
                        "project_id": str(sample_project_id),
                        "document_path": document_path,
                        "direction": "incoming",
                    },
                    headers=mock_auth_headers,
                )

            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert len(data["incoming"]) >= 0

    @pytest.mark.asyncio
    async def test_get_document_links_outgoing_only(
        self,
        sample_project_id: UUID,
        mock_auth_headers: dict,
    ):
        """Test getting only outgoing links from a document."""
        document_path = "docs/02-design/01-ADRs/ADR-001.md"

        with patch(
            "app.api.routes.cross_reference_validation.get_cross_reference_service"
        ) as mock_get_service:
            mock_service = AsyncMock(spec=CrossReferenceService)
            mock_service.get_document_links.return_value = DocumentLinks(
                document_path=document_path,
                incoming=[],
                outgoing=[
                    {"target": "SPEC-0001.md", "type": "spec_ref"},
                ],
            )
            mock_get_service.return_value = mock_service

            async with AsyncClient(
                transport=ASGITransport(app=app),
                base_url="http://test",
            ) as client:
                response = await client.get(
                    f"/api/v1/doc-cross-reference/links",
                    params={
                        "project_id": str(sample_project_id),
                        "document_path": document_path,
                        "direction": "outgoing",
                    },
                    headers=mock_auth_headers,
                )

            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert len(data["outgoing"]) >= 0


# =========================================================================
# Test: Error Handling
# =========================================================================


class TestErrorHandling:
    """Test error handling for cross-reference endpoints."""

    @pytest.mark.asyncio
    async def test_validate_invalid_project_id(
        self,
        mock_auth_headers: dict,
    ):
        """Test validation with invalid project ID format."""
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
        ) as client:
            response = await client.post(
                f"/api/v1/doc-cross-reference/validate",
                json={
                    "project_id": "not-a-uuid",
                    "document_path": "SPEC-0001.md",
                },
                headers=mock_auth_headers,
            )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    @pytest.mark.asyncio
    async def test_service_error_handling(
        self,
        sample_project_id: UUID,
        mock_auth_headers: dict,
    ):
        """Test handling of service errors."""
        with patch(
            "app.api.routes.cross_reference_validation.get_cross_reference_service"
        ) as mock_get_service:
            mock_service = AsyncMock(spec=CrossReferenceService)
            mock_service.validate_document.side_effect = Exception("Service error")
            mock_get_service.return_value = mock_service

            async with AsyncClient(
                transport=ASGITransport(app=app),
                base_url="http://test",
            ) as client:
                response = await client.post(
                    f"/api/v1/doc-cross-reference/validate",
                    json={
                        "project_id": str(sample_project_id),
                        "document_path": "SPEC-0001.md",
                    },
                    headers=mock_auth_headers,
                )

            assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
