"""
Integration Tests for MinIO Service
Week 7 Day 4 - Coverage Boost (25% → 60%+)

File: tests/integration/test_minio_integration.py
Version: 1.0.0
Date: November 25, 2025
Status: ACTIVE - Week 7 Day 4
Authority: Backend Lead + QA Lead
Framework: SDLC 4.9 Complete Lifecycle

Purpose:
- Direct testing of MinIO S3-compatible storage service
- File upload/download operations with SHA256 integrity
- Multipart upload for large files (>5MB)
- Presigned URL generation for secure access
- Error handling and edge cases

Coverage Target:
- Current: 25% (32/128 lines)
- Target: 60%+ (77/128 lines)
- Improvement: +35% (+45 lines)
- Project impact: +2.5% total coverage

Test Categories:
1. Bucket Management (2 tests)
2. File Upload Operations (3 tests)
3. Multipart Upload (2 tests)
4. File Download Operations (2 tests)
5. SHA256 Integrity Verification (2 tests)
6. Presigned URLs (2 tests)

Total Tests: 13
Zero Mock Policy: 100% COMPLIANCE (real MinIO integration)
"""

import hashlib
import pytest
from io import BytesIO
from uuid import uuid4

from botocore.exceptions import ClientError
from app.services.minio_service import minio_service


@pytest.mark.integration
@pytest.mark.minio
class TestMinioBucketManagement:
    """Integration tests for MinIO bucket management."""

    def test_ensure_bucket_exists(self):
        """Test that ensure_bucket_exists creates or verifies bucket."""
        # Should not raise error for default bucket
        minio_service.ensure_bucket_exists()

        # Verify bucket exists by trying to list objects
        # If bucket doesn't exist, this would raise error
        try:
            list(minio_service.client.list_objects_v2(
                Bucket=minio_service.bucket_name,
                MaxKeys=1
            ).get('Contents', []))
        except ClientError:
            pytest.fail("Bucket should exist after ensure_bucket_exists()")


@pytest.mark.integration
@pytest.mark.minio
class TestMinioFileUpload:
    """Integration tests for MinIO file upload operations."""

    def test_upload_file_standard(self):
        """Test standard file upload with SHA256 verification."""
        # Prepare test file
        test_content = b"Test evidence file for MinIO integration testing"
        test_file = BytesIO(test_content)
        object_name = f"test-uploads/test-{uuid4().hex[:8]}.txt"

        # Calculate expected SHA256
        expected_sha256 = hashlib.sha256(test_content).hexdigest()

        try:
            # Upload file
            bucket, key, sha256_hash = minio_service.upload_file(
                file_obj=test_file,
                object_name=object_name,
                content_type="text/plain"
            )

            # Verify upload result
            assert bucket == minio_service.bucket_name
            assert key == object_name
            assert sha256_hash == expected_sha256

        finally:
            # Cleanup: delete test file
            try:
                minio_service.delete_file(object_name)
            except Exception:
                pass

    def test_upload_file_with_metadata(self):
        """Test file upload with custom metadata."""
        # Prepare test file
        test_content = b"Test file with custom metadata"
        test_file = BytesIO(test_content)
        object_name = f"test-uploads/test-metadata-{uuid4().hex[:8]}.txt"

        # Custom metadata
        metadata = {
            "gate-id": str(uuid4()),
            "evidence-type": "DOCUMENTATION",
            "uploaded-by": "test-user"
        }

        try:
            # Upload file with metadata
            bucket, key, sha256_hash = minio_service.upload_file(
                file_obj=test_file,
                object_name=object_name,
                content_type="text/plain",
                metadata=metadata
            )

            # Verify upload succeeded
            assert bucket == minio_service.bucket_name
            assert key == object_name

            # Verify metadata was stored
            file_metadata = minio_service.get_file_metadata(object_name)
            assert file_metadata.get("gate-id") == metadata["gate-id"]
            assert file_metadata.get("evidence-type") == metadata["evidence-type"]

        finally:
            # Cleanup
            try:
                minio_service.delete_file(object_name)
            except Exception:
                pass

    def test_upload_file_returns_sha256(self):
        """Test that upload_file returns correct SHA256 hash."""
        # Prepare test file with known content
        test_content = b"Known content for SHA256 test"
        expected_sha256 = hashlib.sha256(test_content).hexdigest()
        test_file = BytesIO(test_content)
        object_name = f"test-uploads/test-sha256-{uuid4().hex[:8]}.txt"

        try:
            # Upload file
            _, _, returned_sha256 = minio_service.upload_file(
                file_obj=test_file,
                object_name=object_name,
                content_type="text/plain"
            )

            # Verify returned SHA256 matches expected
            assert returned_sha256 == expected_sha256

        finally:
            try:
                minio_service.delete_file(object_name)
            except Exception:
                pass


@pytest.mark.integration
@pytest.mark.minio
@pytest.mark.slow
class TestMinioMultipartUpload:
    """Integration tests for MinIO multipart upload (large files)."""

    def test_multipart_upload_large_file(self):
        """Test multipart upload for file >5MB."""
        # Generate 6MB test file (triggers multipart upload)
        file_size = 6 * 1024 * 1024  # 6MB
        test_content = b"X" * file_size
        test_file = BytesIO(test_content)
        object_name = f"test-uploads/test-large-{uuid4().hex[:8]}.bin"

        try:
            # Upload large file (should use multipart)
            bucket, key, sha256_hash = minio_service.upload_multipart(
                file_obj=test_file,
                object_name=object_name,
                content_type="application/octet-stream"
            )

            # Verify upload succeeded
            assert bucket == minio_service.bucket_name
            assert key == object_name
            assert len(sha256_hash) == 64  # SHA256 is 64 hex characters

        finally:
            # Cleanup
            try:
                minio_service.delete_file(object_name)
            except Exception:
                pass

    def test_multipart_upload_custom_part_size(self):
        """Test multipart upload with custom part size."""
        # Generate 30MB test file
        file_size = 30 * 1024 * 1024  # 30MB
        test_content = b"Y" * file_size
        test_file = BytesIO(test_content)
        object_name = f"test-uploads/test-custom-part-{uuid4().hex[:8]}.bin"

        try:
            # Upload with 6MB part size (instead of default 5MB)
            # MinIO requires each part >= 5MB except last part
            bucket, key, sha256_hash = minio_service.upload_multipart(
                file_obj=test_file,
                object_name=object_name,
                content_type="application/octet-stream",
                part_size=6 * 1024 * 1024  # 6MB parts = 5 parts
            )

            # Verify upload succeeded
            assert len(sha256_hash) == 64
            assert bucket == minio_service.bucket_name

        finally:
            # Cleanup
            try:
                minio_service.delete_file(object_name)
            except Exception:
                pass


@pytest.mark.integration
@pytest.mark.minio
class TestMinioFileDownload:
    """Integration tests for MinIO file download operations."""

    def test_download_file_success(self):
        """Test successful file download."""
        # First upload a test file
        test_content = b"Test content for download test"
        test_file = BytesIO(test_content)
        object_name = f"test-uploads/test-download-{uuid4().hex[:8]}.txt"

        try:
            # Upload file
            minio_service.upload_file(
                file_obj=test_file,
                object_name=object_name,
                content_type="text/plain"
            )

            # Download file
            downloaded_data = minio_service.download_file(object_name)

            # Verify downloaded content matches uploaded content
            assert downloaded_data == test_content

        finally:
            # Cleanup
            try:
                minio_service.delete_file(object_name)
            except Exception:
                pass

    def test_download_file_not_found(self):
        """Test download of non-existent file returns error."""
        non_existent_key = f"non-existent-{uuid4().hex[:8]}.txt"

        # Should raise ClientError for non-existent file
        with pytest.raises(ClientError) as exc_info:
            minio_service.download_file(non_existent_key)

        # Verify it's a NoSuchKey error
        assert exc_info.value.response['Error']['Code'] == 'NoSuchKey'


@pytest.mark.integration
@pytest.mark.minio
class TestMinioSHA256Integrity:
    """Integration tests for SHA256 integrity verification."""

    def test_sha256_verification_success(self):
        """Test SHA256 hash verification for uploaded file."""
        # Prepare test file with known content
        test_content = b"Integrity check test content"
        expected_sha256 = hashlib.sha256(test_content).hexdigest()
        test_file = BytesIO(test_content)
        object_name = f"test-uploads/test-integrity-{uuid4().hex[:8]}.txt"

        try:
            # Upload file
            _, _, upload_sha256 = minio_service.upload_file(
                file_obj=test_file,
                object_name=object_name,
                content_type="text/plain"
            )

            # Verify SHA256 hash matches expected
            assert upload_sha256 == expected_sha256

            # Download and recalculate hash
            downloaded_data = minio_service.download_file(object_name)
            recalculated_hash = hashlib.sha256(downloaded_data).hexdigest()

            # Verify integrity maintained
            assert recalculated_hash == expected_sha256
            assert recalculated_hash == upload_sha256

        finally:
            # Cleanup
            try:
                minio_service.delete_file(object_name)
            except Exception:
                pass

    def test_sha256_compute_and_verify(self):
        """Test SHA256 compute and verify helper methods."""
        # Test content
        test_content = b"Test content for SHA256 helpers"

        # Compute SHA256
        computed_hash = minio_service.compute_sha256(test_content)
        assert len(computed_hash) == 64  # SHA256 is 64 hex characters

        # Verify with correct hash
        assert minio_service.verify_sha256(test_content, computed_hash) is True

        # Verify with incorrect hash
        wrong_hash = "a" * 64
        assert minio_service.verify_sha256(test_content, wrong_hash) is False


@pytest.mark.integration
@pytest.mark.minio
class TestMinioPresignedURLs:
    """Integration tests for MinIO presigned URL generation."""

    def test_generate_presigned_upload_url(self):
        """Test presigned URL generation for file upload."""
        object_name = f"test-uploads/presigned-{uuid4().hex[:8]}.txt"
        expiry_seconds = 3600  # 1 hour

        try:
            # Generate presigned upload URL
            upload_url = minio_service.generate_presigned_upload_url(
                object_name=object_name,
                expiration=expiry_seconds
            )

            # Verify URL format
            assert upload_url.startswith("http")
            assert object_name in upload_url
            # AWS signature v4 markers
            assert "X-Amz-Algorithm" in upload_url or "Signature" in upload_url

        finally:
            # Cleanup (if file was uploaded via presigned URL)
            try:
                minio_service.delete_file(object_name)
            except Exception:
                pass

    def test_generate_presigned_download_url(self):
        """Test presigned URL generation for file download."""
        # First upload a test file
        test_content = b"Test content for presigned download"
        test_file = BytesIO(test_content)
        object_name = f"test-uploads/test-presigned-download-{uuid4().hex[:8]}.txt"
        expiry_seconds = 3600  # 1 hour

        try:
            # Upload file
            minio_service.upload_file(
                file_obj=test_file,
                object_name=object_name,
                content_type="text/plain"
            )

            # Generate presigned download URL
            download_url = minio_service.generate_presigned_download_url(
                object_name=object_name,
                expiration=expiry_seconds
            )

            # Verify URL format
            assert download_url.startswith("http")
            assert object_name in download_url
            assert "X-Amz-Algorithm" in download_url or "Signature" in download_url

        finally:
            # Cleanup
            try:
                minio_service.delete_file(object_name)
            except Exception:
                pass


@pytest.mark.integration
@pytest.mark.minio
class TestMinioFileMetadata:
    """Integration tests for MinIO file metadata operations."""

    def test_get_file_metadata(self):
        """Test retrieving file metadata without downloading content."""
        # Upload a test file
        test_content = b"Test file for metadata retrieval"
        test_file = BytesIO(test_content)
        object_name = f"test-uploads/test-metadata-{uuid4().hex[:8]}.txt"
        custom_metadata = {
            "project-id": "test-project-123",
            "user-id": "test-user-456"
        }

        try:
            # Upload with custom metadata
            minio_service.upload_file(
                file_obj=test_file,
                object_name=object_name,
                content_type="text/plain",
                metadata=custom_metadata
            )

            # Get metadata
            metadata = minio_service.get_file_metadata(object_name)

            # Verify metadata contains our custom fields
            assert metadata.get("project-id") == custom_metadata["project-id"]
            assert metadata.get("user-id") == custom_metadata["user-id"]

            # Verify SHA256 is in metadata
            assert "sha256" in metadata
            assert len(metadata["sha256"]) == 64

        finally:
            try:
                minio_service.delete_file(object_name)
            except Exception:
                pass
