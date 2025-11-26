"""
=========================================================================
MinIO Service Adapter - S3-Compatible Storage for Evidence Vault
SDLC Orchestrator - Stage 03 (BUILD)

Version: 1.0.0
Date: December 4, 2025
Status: ACTIVE - Week 4 Day 3 (MinIO Integration)
Authority: Backend Lead + CTO Approved
Foundation: FR2 (Evidence Vault), Data Model v0.1
Framework: SDLC 4.9 Complete Lifecycle

Purpose:
- S3-compatible file storage via boto3 (AGPL-safe)
- SHA256 integrity verification
- Multipart upload for large files (>5MB)
- Evidence metadata management

AGPL Containment Strategy:
✅ Network-only access via boto3 (AWS SDK, Apache 2.0 license)
✅ NO MinIO SDK imports (AGPL contamination risk)
✅ S3 API compatibility (standard protocol)
✅ Docker process isolation (minio:9000 container)

Legal Precedent:
- MongoDB SSPL (2018): Network-only access is safe
- Grafana Enterprise (2021): API calls don't trigger AGPL
- Legal counsel approved (2025-11-25 AGPL Containment Brief)

Zero Mock Policy: 100% real implementation (boto3 + hashlib)
=========================================================================
"""

import hashlib
import logging
from io import BytesIO
from typing import BinaryIO, Optional
from uuid import UUID

import boto3
from botocore.client import Config
from botocore.exceptions import ClientError

from app.core.config import settings

logger = logging.getLogger(__name__)

# ============================================================================
# MinIO Client Initialization (boto3 S3-compatible)
# ============================================================================


class MinIOService:
    """
    MinIO service adapter using boto3 S3-compatible API.

    AGPL-Safe Implementation:
    - Uses boto3 (Apache 2.0 license) instead of MinIO SDK (AGPL v3)
    - Network-only access via HTTP/S API calls
    - No code dependencies on AGPL libraries

    Usage:
        minio = MinIOService()
        s3_url = await minio.upload_file(file, "evidence/gate-123/doc.pdf")
        file_content = await minio.download_file("evidence/gate-123/doc.pdf")
        sha256 = minio.compute_sha256(file_content)
    """

    def __init__(self):
        """Initialize boto3 S3 client for MinIO."""
        self.endpoint_url = f"http://{settings.MINIO_ENDPOINT}"
        self.access_key = settings.MINIO_ACCESS_KEY
        self.secret_key = settings.MINIO_SECRET_KEY
        self.bucket_name = settings.MINIO_BUCKET
        self.secure = settings.MINIO_SECURE

        # Create S3 client with MinIO endpoint
        self.client = boto3.client(
            's3',
            endpoint_url=self.endpoint_url,
            aws_access_key_id=self.access_key,
            aws_secret_access_key=self.secret_key,
            config=Config(signature_version='s3v4'),
            region_name='us-east-1',  # MinIO default region
        )

        logger.info(f"MinIO service initialized: {self.endpoint_url}, bucket={self.bucket_name}")

    # ============================================================================
    # Bucket Management
    # ============================================================================

    def ensure_bucket_exists(self) -> None:
        """
        Ensure the evidence vault bucket exists, create if not.

        Raises:
            ClientError: If bucket creation fails
        """
        try:
            self.client.head_bucket(Bucket=self.bucket_name)
            logger.debug(f"Bucket '{self.bucket_name}' already exists")
        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == '404':
                # Bucket doesn't exist, create it
                logger.info(f"Creating bucket '{self.bucket_name}'...")
                self.client.create_bucket(Bucket=self.bucket_name)
                logger.info(f"Bucket '{self.bucket_name}' created successfully")
            else:
                logger.error(f"Failed to check bucket existence: {e}")
                raise

    # ============================================================================
    # File Upload (with SHA256 integrity)
    # ============================================================================

    def upload_file(
        self,
        file_obj: BinaryIO,
        object_name: str,
        content_type: str = "application/octet-stream",
        metadata: Optional[dict] = None,
    ) -> tuple[str, str, str]:
        """
        Upload file to MinIO with SHA256 integrity verification.

        Args:
            file_obj: File-like object to upload (must support .read())
            object_name: S3 object key (e.g., "evidence/gate-123/doc.pdf")
            content_type: MIME type (default: application/octet-stream)
            metadata: Custom metadata dict (e.g., {"gate_id": "123", "user_id": "456"})

        Returns:
            Tuple of (s3_bucket, s3_key, sha256_hash)

        Raises:
            ClientError: If upload fails

        Example:
            with open("doc.pdf", "rb") as f:
                bucket, key, hash = minio.upload_file(
                    f,
                    "evidence/gate-123/doc.pdf",
                    content_type="application/pdf",
                    metadata={"gate_id": "123"}
                )
        """
        try:
            # Ensure bucket exists
            self.ensure_bucket_exists()

            # Read file content for SHA256 computation
            file_content = file_obj.read()
            file_obj.seek(0)  # Reset file pointer for upload

            # Compute SHA256 hash
            sha256_hash = self.compute_sha256(file_content)

            # Prepare metadata (add SHA256 hash)
            upload_metadata = metadata or {}
            upload_metadata['sha256'] = sha256_hash

            # Upload file to MinIO
            self.client.put_object(
                Bucket=self.bucket_name,
                Key=object_name,
                Body=file_obj,
                ContentType=content_type,
                Metadata=upload_metadata,
            )

            logger.info(
                f"File uploaded successfully: s3://{self.bucket_name}/{object_name} "
                f"(SHA256: {sha256_hash[:16]}...)"
            )

            return self.bucket_name, object_name, sha256_hash

        except ClientError as e:
            logger.error(f"Failed to upload file to MinIO: {e}")
            raise

    def upload_multipart(
        self,
        file_obj: BinaryIO,
        object_name: str,
        content_type: str = "application/octet-stream",
        part_size: int = 5 * 1024 * 1024,  # 5MB per part
        metadata: Optional[dict] = None,
    ) -> tuple[str, str, str]:
        """
        Upload large file using multipart upload (for files >5MB).

        Args:
            file_obj: File-like object to upload
            object_name: S3 object key
            content_type: MIME type
            part_size: Size of each part in bytes (default: 5MB)
            metadata: Custom metadata

        Returns:
            Tuple of (s3_bucket, s3_key, sha256_hash)

        Raises:
            ClientError: If multipart upload fails

        Example:
            with open("large_file.zip", "rb") as f:
                bucket, key, hash = minio.upload_multipart(
                    f,
                    "evidence/gate-123/large_file.zip",
                    content_type="application/zip"
                )
        """
        try:
            # Ensure bucket exists
            self.ensure_bucket_exists()

            # Read file content for SHA256 computation
            file_content = file_obj.read()
            file_obj.seek(0)  # Reset file pointer

            # Compute SHA256 hash
            sha256_hash = self.compute_sha256(file_content)

            # Prepare metadata
            upload_metadata = metadata or {}
            upload_metadata['sha256'] = sha256_hash

            # Initiate multipart upload
            response = self.client.create_multipart_upload(
                Bucket=self.bucket_name,
                Key=object_name,
                ContentType=content_type,
                Metadata=upload_metadata,
            )
            upload_id = response['UploadId']

            # Upload parts
            parts = []
            part_number = 1

            while True:
                data = file_obj.read(part_size)
                if not data:
                    break

                part_response = self.client.upload_part(
                    Bucket=self.bucket_name,
                    Key=object_name,
                    PartNumber=part_number,
                    UploadId=upload_id,
                    Body=data,
                )

                parts.append({
                    'PartNumber': part_number,
                    'ETag': part_response['ETag'],
                })

                part_number += 1

            # Complete multipart upload
            self.client.complete_multipart_upload(
                Bucket=self.bucket_name,
                Key=object_name,
                UploadId=upload_id,
                MultipartUpload={'Parts': parts},
            )

            logger.info(
                f"Multipart upload completed: s3://{self.bucket_name}/{object_name} "
                f"({part_number - 1} parts, SHA256: {sha256_hash[:16]}...)"
            )

            return self.bucket_name, object_name, sha256_hash

        except ClientError as e:
            # Abort multipart upload on failure
            if 'upload_id' in locals():
                self.client.abort_multipart_upload(
                    Bucket=self.bucket_name,
                    Key=object_name,
                    UploadId=upload_id,
                )
            logger.error(f"Multipart upload failed: {e}")
            raise

    # ============================================================================
    # File Download
    # ============================================================================

    def download_file(self, object_name: str) -> bytes:
        """
        Download file from MinIO.

        Args:
            object_name: S3 object key (e.g., "evidence/gate-123/doc.pdf")

        Returns:
            File content as bytes

        Raises:
            ClientError: If file not found or download fails

        Example:
            content = minio.download_file("evidence/gate-123/doc.pdf")
            with open("downloaded.pdf", "wb") as f:
                f.write(content)
        """
        try:
            response = self.client.get_object(
                Bucket=self.bucket_name,
                Key=object_name,
            )

            content = response['Body'].read()
            logger.info(f"File downloaded: s3://{self.bucket_name}/{object_name} ({len(content)} bytes)")

            return content

        except ClientError as e:
            if e.response['Error']['Code'] == 'NoSuchKey':
                logger.error(f"File not found: s3://{self.bucket_name}/{object_name}")
            else:
                logger.error(f"Failed to download file: {e}")
            raise

    def get_file_metadata(self, object_name: str) -> dict:
        """
        Get file metadata from MinIO (without downloading file content).

        Args:
            object_name: S3 object key

        Returns:
            Metadata dict (includes SHA256 hash if available)

        Raises:
            ClientError: If file not found

        Example:
            metadata = minio.get_file_metadata("evidence/gate-123/doc.pdf")
            sha256 = metadata.get('sha256')
            content_type = metadata.get('ContentType')
        """
        try:
            response = self.client.head_object(
                Bucket=self.bucket_name,
                Key=object_name,
            )

            metadata = {
                'ContentType': response['ContentType'],
                'ContentLength': response['ContentLength'],
                'LastModified': response['LastModified'],
                'ETag': response['ETag'],
                **response.get('Metadata', {}),
            }

            logger.debug(f"File metadata retrieved: s3://{self.bucket_name}/{object_name}")

            return metadata

        except ClientError as e:
            if e.response['Error']['Code'] == '404':
                logger.error(f"File not found: s3://{self.bucket_name}/{object_name}")
            else:
                logger.error(f"Failed to get file metadata: {e}")
            raise

    # ============================================================================
    # File Deletion
    # ============================================================================

    def delete_file(self, object_name: str) -> None:
        """
        Delete file from MinIO.

        Args:
            object_name: S3 object key

        Raises:
            ClientError: If deletion fails

        Example:
            minio.delete_file("evidence/gate-123/doc.pdf")
        """
        try:
            self.client.delete_object(
                Bucket=self.bucket_name,
                Key=object_name,
            )

            logger.info(f"File deleted: s3://{self.bucket_name}/{object_name}")

        except ClientError as e:
            logger.error(f"Failed to delete file: {e}")
            raise

    # ============================================================================
    # SHA256 Integrity Verification
    # ============================================================================

    @staticmethod
    def compute_sha256(file_content: bytes) -> str:
        """
        Compute SHA256 hash of file content.

        Args:
            file_content: File content as bytes

        Returns:
            SHA256 hash as hexadecimal string (64 characters)

        Example:
            with open("doc.pdf", "rb") as f:
                content = f.read()
            sha256 = MinIOService.compute_sha256(content)
            # sha256 = "a948904f2f0f479b8f8197694b30184b0d2ed1c1cd2a1ec0fb85d299a192a447"
        """
        return hashlib.sha256(file_content).hexdigest()

    @staticmethod
    def verify_sha256(file_content: bytes, expected_hash: str) -> bool:
        """
        Verify file integrity by comparing SHA256 hashes.

        Args:
            file_content: File content as bytes
            expected_hash: Expected SHA256 hash (64-char hex string)

        Returns:
            True if hashes match, False otherwise

        Example:
            content = minio.download_file("evidence/gate-123/doc.pdf")
            is_valid = MinIOService.verify_sha256(content, "a948904f...")
            if not is_valid:
                raise IntegrityError("File has been tampered with!")
        """
        actual_hash = hashlib.sha256(file_content).hexdigest()
        is_match = actual_hash == expected_hash

        if not is_match:
            logger.warning(
                f"SHA256 mismatch! Expected: {expected_hash[:16]}..., "
                f"Actual: {actual_hash[:16]}..."
            )

        return is_match

    # ============================================================================
    # Presigned URL (for direct browser uploads/downloads)
    # ============================================================================

    def generate_presigned_upload_url(
        self,
        object_name: str,
        expiration: int = 3600,
        content_type: str = "application/octet-stream",
    ) -> str:
        """
        Generate presigned URL for direct browser upload (no backend proxy).

        Args:
            object_name: S3 object key
            expiration: URL expiration in seconds (default: 1 hour)
            content_type: Expected MIME type

        Returns:
            Presigned URL (valid for 1 hour by default)

        Example:
            url = minio.generate_presigned_upload_url(
                "evidence/gate-123/doc.pdf",
                content_type="application/pdf"
            )
            # Frontend uploads directly to MinIO:
            # fetch(url, { method: 'PUT', body: file, headers: { 'Content-Type': 'application/pdf' } })
        """
        try:
            url = self.client.generate_presigned_url(
                'put_object',
                Params={
                    'Bucket': self.bucket_name,
                    'Key': object_name,
                    'ContentType': content_type,
                },
                ExpiresIn=expiration,
            )

            logger.debug(f"Presigned upload URL generated: {object_name} (expires in {expiration}s)")

            return url

        except ClientError as e:
            logger.error(f"Failed to generate presigned upload URL: {e}")
            raise

    def generate_presigned_download_url(
        self,
        object_name: str,
        expiration: int = 3600,
    ) -> str:
        """
        Generate presigned URL for direct browser download (no backend proxy).

        Args:
            object_name: S3 object key
            expiration: URL expiration in seconds (default: 1 hour)

        Returns:
            Presigned URL (valid for 1 hour by default)

        Example:
            url = minio.generate_presigned_download_url("evidence/gate-123/doc.pdf")
            # Frontend downloads directly from MinIO:
            # <a href={url} download>Download Evidence</a>
        """
        try:
            url = self.client.generate_presigned_url(
                'get_object',
                Params={
                    'Bucket': self.bucket_name,
                    'Key': object_name,
                },
                ExpiresIn=expiration,
            )

            logger.debug(f"Presigned download URL generated: {object_name} (expires in {expiration}s)")

            return url

        except ClientError as e:
            logger.error(f"Failed to generate presigned download URL: {e}")
            raise


# ============================================================================
# Global MinIO Service Instance
# ============================================================================

# Singleton instance (initialized on first import)
minio_service = MinIOService()
