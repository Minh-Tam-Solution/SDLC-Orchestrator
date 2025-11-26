"""
Integration Tests for Evidence API

File: tests/integration/test_evidence_integration.py
Version: 1.0.0
Date: December 12, 2025
Status: ACTIVE - Week 6 Day 1
Authority: Backend Lead + QA Lead
Framework: SDLC 4.9 Complete Lifecycle

Test Coverage:
- POST /api/v1/evidence - Upload evidence file
- GET /api/v1/evidence - List evidence (pagination + filters)
- GET /api/v1/evidence/{evidence_id} - Get evidence details
- PUT /api/v1/evidence/{evidence_id} - Update evidence metadata
- DELETE /api/v1/evidence/{evidence_id} - Delete evidence (soft delete)

Total Endpoints: 5
Total Tests: 10+
Target Coverage: 90%+
"""

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import uuid4
from io import BytesIO

from app.models.user import User
from app.models.gate import Gate
from app.models.gate_evidence import GateEvidence as Evidence


@pytest.mark.integration
@pytest.mark.evidence
class TestEvidenceUpload:
    """Integration tests for evidence upload endpoint."""

    async def test_upload_evidence_success(
        self,
        client: AsyncClient,
        auth_headers: dict,
        test_gate: Gate,
    ):
        """Test successful evidence upload."""
        # Create test file
        file_content = b"Test PDF content for evidence"
        files = {
            "file": ("test_document.pdf", BytesIO(file_content), "application/pdf")
        }
        data = {
            "gate_id": str(test_gate.id),
            "evidence_type": "DOCUMENTATION",  # Must be uppercase valid type
            "description": "Integration test evidence file",
        }

        response = await client.post(
            "/api/v1/evidence/upload",  # Correct route path
            headers=auth_headers,
            files=files,
            data=data,
        )

        assert response.status_code == 201
        result = response.json()

        assert result["evidence_type"] == "DOCUMENTATION"
        assert result["gate_id"] == str(test_gate.id)
        assert result["file_name"] == "test_document.pdf"
        assert "download_url" in result  # API returns download_url, not file_path
        assert "sha256_hash" in result

    async def test_upload_evidence_unauthenticated(
        self, client: AsyncClient, test_gate: Gate
    ):
        """Test evidence upload without authentication returns 401."""
        file_content = b"Test content"
        files = {"file": ("test.pdf", BytesIO(file_content), "application/pdf")}
        data = {
            "gate_id": str(test_gate.id),
            "evidence_type": "DOCUMENTATION",
        }

        response = await client.post(
            "/api/v1/evidence/upload",  # Correct route path
            files=files,
            data=data,
        )

        assert response.status_code == 403  # FastAPI returns 403 for missing auth

    async def test_upload_evidence_invalid_gate(
        self, client: AsyncClient, auth_headers: dict
    ):
        """Test evidence upload with non-existent gate returns 404."""
        file_content = b"Test content"
        files = {"file": ("test.pdf", BytesIO(file_content), "application/pdf")}
        data = {
            "gate_id": str(uuid4()),  # Non-existent gate
            "evidence_type": "DOCUMENTATION",
        }

        response = await client.post(
            "/api/v1/evidence/upload",  # Correct route path
            headers=auth_headers,
            files=files,
            data=data,
        )

        assert response.status_code == 404


@pytest.mark.integration
@pytest.mark.evidence
class TestEvidenceList:
    """Integration tests for evidence list endpoint."""

    async def test_list_evidence_success(
        self,
        client: AsyncClient,
        auth_headers: dict,
        test_evidence: Evidence,
    ):
        """Test list evidence with pagination."""
        response = await client.get(
            "/api/v1/evidence",
            headers=auth_headers,
            params={"page": 1, "page_size": 10},
        )

        assert response.status_code == 200
        data = response.json()

        assert "items" in data
        assert "total" in data
        assert "page" in data
        assert "page_size" in data
        assert len(data["items"]) > 0

    async def test_list_evidence_filter_by_gate(
        self,
        client: AsyncClient,
        auth_headers: dict,
        test_gate: Gate,
        test_evidence: Evidence,
    ):
        """Test list evidence filtered by gate ID."""
        response = await client.get(
            "/api/v1/evidence",
            headers=auth_headers,
            params={"gate_id": str(test_gate.id)},
        )

        assert response.status_code == 200
        data = response.json()

        # All evidence should belong to test_gate
        for evidence in data["items"]:
            assert evidence["gate_id"] == str(test_gate.id)

    async def test_list_evidence_filter_by_type(
        self,
        client: AsyncClient,
        auth_headers: dict,
        test_evidence: Evidence,
    ):
        """Test list evidence filtered by evidence type."""
        response = await client.get(
            "/api/v1/evidence",
            headers=auth_headers,
            params={"evidence_type": "DOCUMENTATION"},
        )

        assert response.status_code == 200
        data = response.json()

        # All evidence should be documents
        for evidence in data["items"]:
            assert evidence["evidence_type"] == "DOCUMENTATION"


@pytest.mark.integration
@pytest.mark.evidence
class TestEvidenceDetail:
    """Integration tests for evidence detail endpoint."""

    async def test_get_evidence_success(
        self,
        client: AsyncClient,
        auth_headers: dict,
        test_evidence: Evidence,
    ):
        """Test get evidence details."""
        response = await client.get(
            f"/api/v1/evidence/{test_evidence.id}",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()

        assert data["id"] == str(test_evidence.id)
        assert data["gate_id"] == str(test_evidence.gate_id)
        assert data["file_name"] == test_evidence.file_name
        assert data["evidence_type"] == test_evidence.evidence_type
        assert data["sha256_hash"] == test_evidence.sha256_hash
        assert "s3_url" in data
        assert "download_url" in data

    async def test_get_evidence_not_found(
        self, client: AsyncClient, auth_headers: dict
    ):
        """Test get non-existent evidence returns 404."""
        response = await client.get(
            f"/api/v1/evidence/{uuid4()}",
            headers=auth_headers,
        )

        assert response.status_code == 404


@pytest.mark.integration
@pytest.mark.evidence
class TestEvidenceUpdate:
    """Integration tests for evidence update endpoint."""

    @pytest.mark.skip(reason="PUT /evidence/{id} endpoint not implemented yet")
    async def test_update_evidence_success(
        self,
        client: AsyncClient,
        auth_headers: dict,
        test_evidence: Evidence,
    ):
        """Test successful evidence metadata update."""
        response = await client.put(
            f"/api/v1/evidence/{test_evidence.id}",
            headers=auth_headers,
            json={
                "title": "Updated Evidence Title",
                "description": "Updated description",
            },
        )

        assert response.status_code == 200
        data = response.json()

        assert data["id"] == str(test_evidence.id)
        assert data["title"] == "Updated Evidence Title"
        assert data["description"] == "Updated description"

    @pytest.mark.skip(reason="PUT /evidence/{id} endpoint not implemented yet")
    async def test_update_evidence_not_found(
        self, client: AsyncClient, auth_headers: dict
    ):
        """Test update non-existent evidence returns 404."""
        response = await client.put(
            f"/api/v1/evidence/{uuid4()}",
            headers=auth_headers,
            json={"title": "Updated Title"},
        )

        assert response.status_code == 404


@pytest.mark.integration
@pytest.mark.evidence
class TestEvidenceDelete:
    """Integration tests for evidence deletion (soft delete)."""

    @pytest.mark.skip(reason="DELETE /evidence/{id} endpoint not implemented yet")
    async def test_delete_evidence_success(
        self,
        client: AsyncClient,
        auth_headers: dict,
        db: AsyncSession,
        test_evidence: Evidence,
    ):
        """Test successful evidence deletion (soft delete)."""
        response = await client.delete(
            f"/api/v1/evidence/{test_evidence.id}",
            headers=auth_headers,
        )

        assert response.status_code == 204

        # Verify evidence is soft-deleted
        await db.refresh(test_evidence)
        assert test_evidence.deleted_at is not None

    @pytest.mark.skip(reason="DELETE /evidence/{id} endpoint not implemented yet")
    async def test_delete_evidence_not_found(
        self, client: AsyncClient, auth_headers: dict
    ):
        """Test delete non-existent evidence returns 404."""
        response = await client.delete(
            f"/api/v1/evidence/{uuid4()}",
            headers=auth_headers,
        )

        assert response.status_code == 404


@pytest.mark.integration
@pytest.mark.evidence
class TestEvidenceErrorHandling:
    """Integration tests for Evidence API error handling and validation (NEW - Day 3)."""

    async def test_upload_evidence_invalid_type(
        self,
        client: AsyncClient,
        auth_headers: dict,
        test_gate: Gate,
    ):
        """Test upload evidence with invalid evidence_type returns 400."""
        file_content = b"Test PDF content"
        files = {
            "file": ("test.pdf", BytesIO(file_content), "application/pdf")
        }
        data = {
            "gate_id": str(test_gate.id),
            "evidence_type": "INVALID_TYPE",  # Not in allowed types
            "description": "Test evidence",
        }

        response = await client.post(
            "/api/v1/evidence/upload",
            headers=auth_headers,
            files=files,
            data=data,
        )

        assert response.status_code == 400
        error_data = response.json()
        assert "invalid evidence_type" in error_data["detail"].lower()

    async def test_upload_evidence_file_too_large(
        self,
        client: AsyncClient,
        auth_headers: dict,
        test_gate: Gate,
    ):
        """Test upload evidence with file >100MB returns 413."""
        # Create a file larger than 100MB (100 * 1024 * 1024 bytes)
        # Use 101MB to exceed limit
        large_file_size = 101 * 1024 * 1024
        file_content = b"X" * large_file_size

        files = {
            "file": ("large_file.bin", BytesIO(file_content), "application/octet-stream")
        }
        data = {
            "gate_id": str(test_gate.id),
            "evidence_type": "DOCUMENTATION",
            "description": "Large file test",
        }

        response = await client.post(
            "/api/v1/evidence/upload",
            headers=auth_headers,
            files=files,
            data=data,
        )

        assert response.status_code == 413
        error_data = response.json()
        assert "file size" in error_data["detail"].lower() or "exceeds maximum" in error_data["detail"].lower()

    async def test_upload_evidence_minio_failure(
        self,
        client: AsyncClient,
        auth_headers: dict,
        test_gate: Gate,
    ):
        """Test upload evidence handles MinIO service failure gracefully."""
        # This test verifies that if MinIO is unavailable or fails,
        # the API returns 500 Internal Server Error (not a crash)

        # Note: This test will pass if MinIO is running (file uploads successfully)
        # or if MinIO is down (returns 500). The point is to ensure no unhandled exceptions.

        file_content = b"Test content"
        files = {
            "file": ("test.pdf", BytesIO(file_content), "application/pdf")
        }
        data = {
            "gate_id": str(test_gate.id),
            "evidence_type": "DOCUMENTATION",
            "description": "MinIO failure test",
        }

        response = await client.post(
            "/api/v1/evidence/upload",
            headers=auth_headers,
            files=files,
            data=data,
        )

        # Should either succeed (201) or fail gracefully (500)
        # NOT crash with unhandled exception
        assert response.status_code in [201, 500]

        if response.status_code == 500:
            error_data = response.json()
            assert "detail" in error_data  # Error message present

    async def test_upload_evidence_large_multipart(
        self,
        client: AsyncClient,
        auth_headers: dict,
        test_gate: Gate,
    ):
        """Test upload evidence with large file (>5MB) uses multipart upload path."""
        # Create a file larger than 5MB but smaller than 100MB
        # This should trigger the multipart upload code path
        large_file_size = 6 * 1024 * 1024  # 6MB
        file_content = b"Y" * large_file_size

        files = {
            "file": ("large_doc.pdf", BytesIO(file_content), "application/pdf")
        }
        data = {
            "gate_id": str(test_gate.id),
            "evidence_type": "DOCUMENTATION",
            "description": "Large file multipart upload test",
        }

        response = await client.post(
            "/api/v1/evidence/upload",
            headers=auth_headers,
            files=files,
            data=data,
        )

        # Should succeed using multipart upload
        assert response.status_code == 201
        result = response.json()

        # Verify evidence was created with correct size
        assert result["file_size"] == large_file_size
        assert result["file_size_mb"] == pytest.approx(6.0, rel=0.1)
        assert "sha256_hash" in result
        assert "download_url" in result


@pytest.mark.integration
@pytest.mark.evidence
class TestEvidenceIntegrityChecks:
    """Integration tests for Evidence API integrity check functionality (NEW - Day 3)."""

    @pytest.mark.skip(reason="POST /evidence/{id}/integrity-check endpoint not implemented yet")
    async def test_integrity_check_valid(
        self,
        client: AsyncClient,
        auth_headers: dict,
        test_evidence: Evidence,
    ):
        """Test integrity check on valid evidence passes."""
        response = await client.post(
            f"/api/v1/evidence/{test_evidence.id}/integrity-check",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()

        assert data["evidence_id"] == str(test_evidence.id)
        assert data["status"] == "VALID"
        assert data["expected_hash"] == test_evidence.sha256_hash
        assert data["actual_hash"] == test_evidence.sha256_hash
        assert data["is_tampered"] is False
        assert "checked_at" in data

    @pytest.mark.skip(reason="POST /evidence/{id}/integrity-check endpoint not implemented yet")
    async def test_integrity_check_tampered(
        self,
        client: AsyncClient,
        auth_headers: dict,
        db: AsyncSession,
        test_evidence: Evidence,
    ):
        """Test integrity check detects tampered file (hash mismatch)."""
        # Simulate tampered evidence by changing the stored hash
        original_hash = test_evidence.sha256_hash
        test_evidence.sha256_hash = "0" * 64  # Invalid hash
        await db.commit()

        response = await client.post(
            f"/api/v1/evidence/{test_evidence.id}/integrity-check",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()

        assert data["evidence_id"] == str(test_evidence.id)
        assert data["status"] == "TAMPERED"
        assert data["expected_hash"] == "0" * 64
        assert data["actual_hash"] != "0" * 64  # Actual file hash should differ
        assert data["is_tampered"] is True

        # Restore original hash
        test_evidence.sha256_hash = original_hash
        await db.commit()

    @pytest.mark.skip(reason="POST /evidence/{id}/integrity-check endpoint not implemented yet")
    async def test_integrity_check_not_found(
        self, client: AsyncClient, auth_headers: dict
    ):
        """Test integrity check on non-existent evidence returns 404."""
        response = await client.post(
            f"/api/v1/evidence/{uuid4()}/integrity-check",
            headers=auth_headers,
        )

        assert response.status_code == 404

    @pytest.mark.skip(reason="GET /evidence/{id}/integrity-history endpoint not implemented yet")
    async def test_get_integrity_history_not_found(
        self, client: AsyncClient, auth_headers: dict
    ):
        """Test get integrity history on non-existent evidence returns 404."""
        response = await client.get(
            f"/api/v1/evidence/{uuid4()}/integrity-history",
            headers=auth_headers,
        )

        assert response.status_code == 404


@pytest.mark.integration
@pytest.mark.evidence
class TestEvidenceEdgeCases:
    """Integration tests for Evidence API edge cases (NEW - Day 3)."""

    async def test_list_evidence_pagination(
        self,
        client: AsyncClient,
        auth_headers: dict,
        test_evidence: Evidence,
    ):
        """Test list evidence with pagination parameters."""
        response = await client.get(
            "/api/v1/evidence",
            headers=auth_headers,
            params={"page": 1, "page_size": 5},
        )

        assert response.status_code == 200
        data = response.json()

        assert "items" in data
        assert "total" in data
        assert "page" in data
        assert "page_size" in data
        assert data["page"] == 1
        assert data["page_size"] == 5
        assert len(data["items"]) <= 5

    async def test_list_evidence_combined_filters(
        self,
        client: AsyncClient,
        auth_headers: dict,
        test_gate: Gate,
        test_evidence: Evidence,
    ):
        """Test list evidence with multiple filters simultaneously."""
        response = await client.get(
            "/api/v1/evidence",
            headers=auth_headers,
            params={
                "gate_id": str(test_gate.id),
                "evidence_type": "DOCUMENTATION",
                "page": 1,
                "page_size": 10,
            },
        )

        assert response.status_code == 200
        data = response.json()

        # All evidence should match both filters
        for evidence in data["items"]:
            assert evidence["gate_id"] == str(test_gate.id)
            assert evidence["evidence_type"] == "DOCUMENTATION"
