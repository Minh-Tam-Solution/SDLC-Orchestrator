"""
=========================================================================
Evidence API Router - Evidence Vault Management (FR2)
SDLC Orchestrator - Stage 03 (BUILD)

Version: 2.0.0
Date: December 4, 2025
Status: ACTIVE - Week 4 Day 3 (MinIO Integration COMPLETE) ✅
Authority: Backend Lead + CTO Approved
Foundation: FR2 (Evidence Vault), Data Model v0.1
Framework: SDLC 4.9 Complete Lifecycle

Purpose:
- Evidence file management (upload, retrieve, delete)
- SHA256 integrity verification
- Evidence listing and filtering
- Integrity check history

API Endpoints (6):
1. POST /evidence/upload - Upload evidence file (multipart/form-data) ✅ REAL MinIO
2. GET /evidence/{id} - Get evidence metadata ✅ Production-ready
3. GET /evidence - List evidence with filters ✅ Production-ready
4. GET /evidence/{id}/download - Download evidence file ✅ Pre-signed URL (15 min)
5. POST /evidence/{id}/integrity-check - Run integrity check ✅ REAL SHA256
6. GET /evidence/{id}/integrity-history - Get integrity check history ✅ Production-ready

Week 4 Day 3 Upgrade:
✅ MinIO integration COMPLETE (boto3 S3-compatible API)
✅ SHA256 hashing REAL (hashlib, no mocks)
✅ Multipart upload for large files (>5MB)
✅ AGPL-safe implementation (network-only boto3, no MinIO SDK)

Zero Mock Policy: 100% COMPLIANCE (all mocks removed) ✅
=========================================================================
"""

from datetime import datetime
from io import BytesIO
from typing import Optional
from uuid import UUID

from botocore.exceptions import ClientError
from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile, status
from fastapi.responses import StreamingResponse
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_active_user
from app.db.session import get_db
from app.models.gate import Gate
from app.models.gate_evidence import EvidenceIntegrityCheck, GateEvidence
from app.models.user import User
from app.schemas.evidence import (
    EvidenceListResponse,
    EvidenceResponse,
    IntegrityCheckHistoryResponse,
    IntegrityCheckRequest,
    IntegrityCheckResponse,
)
from app.services.minio_service import minio_service
from app.services.settings_service import SettingsService

router = APIRouter()


# ============================================================================
# Evidence Endpoints
# ============================================================================


@router.post(
    "/evidence/upload",
    response_model=EvidenceResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload evidence file",
    description="""
    Upload evidence file to a gate (FR2 - Evidence Vault).

    **Week 4 Day 3 - REAL MinIO Integration** ✅:
    - File upload to MinIO S3-compatible storage
    - SHA256 hash computed from actual file content
    - Multipart upload for large files (>5MB)
    - AGPL-safe boto3 implementation

    **Request**:
    - multipart/form-data with file upload
    - gate_id: Gate UUID (form field)
    - evidence_type: Evidence category (form field)
    - description: Optional description (form field)
    - file: Binary file upload

    **Validation**:
    - Gate must exist
    - Evidence type must be valid (DESIGN_DOCUMENT, TEST_RESULTS, etc.)
    - File size limit: 100MB (configurable)

    **Response** (201 Created):
    - Evidence metadata with SHA256 hash
    - S3 URL for file access
    - Initial integrity check (valid)
    """,
)
async def upload_evidence(
    gate_id: UUID = Form(..., description="Gate UUID"),
    evidence_type: str = Form(..., description="Evidence type"),
    description: Optional[str] = Form(None, description="Evidence description"),
    file: UploadFile = File(..., description="Evidence file"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Upload evidence file to a gate with REAL MinIO integration."""

    # Validate gate exists
    result = await db.execute(select(Gate).where(Gate.id == gate_id))
    gate = result.scalar_one_or_none()

    if not gate:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Gate with ID {gate_id} not found",
        )

    # Validate evidence type
    allowed_types = {
        "DESIGN_DOCUMENT",
        "TEST_RESULTS",
        "CODE_REVIEW",
        "DEPLOYMENT_PROOF",
        "DOCUMENTATION",
        "COMPLIANCE",
    }
    if evidence_type.upper() not in allowed_types:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid evidence_type '{evidence_type}'. Allowed: {', '.join(allowed_types)}",
        )

    # Read file content and metadata
    file_name = file.filename or "unknown"
    file_type = file.content_type or "application/octet-stream"
    file_content = await file.read()
    file_size = len(file_content)

    # ADR-027 Phase 2: Get max_file_size_mb from database settings
    settings_service = SettingsService(db)
    max_file_size_mb = await settings_service.get_max_file_size_mb()
    max_size = max_file_size_mb * 1024 * 1024  # Convert MB to bytes

    if file_size > max_size:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File size {file_size / (1024 * 1024):.2f}MB exceeds maximum {max_file_size_mb}MB. "
            f"Contact admin to adjust file size limit.",
        )

    # Upload to MinIO (real S3 upload)
    s3_key = f"evidence/gate-{gate_id}/{file_name}"
    file_obj = BytesIO(file_content)

    try:
        # Use multipart upload for large files (>5MB)
        if file_size > 5 * 1024 * 1024:
            s3_bucket, s3_key, sha256_hash = minio_service.upload_multipart(
                file_obj,
                s3_key,
                content_type=file_type,
                metadata={
                    "gate_id": str(gate_id),
                    "uploaded_by": str(current_user.id),
                    "evidence_type": evidence_type.upper(),
                },
            )
        else:
            s3_bucket, s3_key, sha256_hash = minio_service.upload_file(
                file_obj,
                s3_key,
                content_type=file_type,
                metadata={
                    "gate_id": str(gate_id),
                    "uploaded_by": str(current_user.id),
                    "evidence_type": evidence_type.upper(),
                },
            )
    except ClientError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to upload file to storage: {str(e)}",
        )

    # Create evidence record
    evidence = GateEvidence(
        gate_id=gate_id,
        file_name=file_name,
        file_size=file_size,
        file_type=file_type,
        evidence_type=evidence_type.upper(),
        s3_key=s3_key,
        s3_bucket=s3_bucket,
        sha256_hash=sha256_hash,
        description=description,
        uploaded_by=current_user.id,
        uploaded_at=datetime.utcnow(),
    )
    db.add(evidence)
    await db.commit()
    await db.refresh(evidence)

    # Create initial integrity check (valid)
    integrity_check = EvidenceIntegrityCheck(
        evidence_id=evidence.id,
        checked_at=datetime.utcnow(),
        sha256_hash=sha256_hash,
        is_valid=True,
        checked_by=f"system-upload-{current_user.id}",
    )
    db.add(integrity_check)
    await db.commit()

    return EvidenceResponse(
        id=evidence.id,
        gate_id=evidence.gate_id,
        file_name=evidence.file_name,
        file_size=evidence.file_size,
        file_size_mb=evidence.file_size_mb,
        file_type=evidence.file_type,
        evidence_type=evidence.evidence_type,
        sha256_hash=evidence.sha256_hash,
        description=evidence.description,
        uploaded_by=evidence.uploaded_by,
        uploaded_by_name=current_user.full_name,
        uploaded_at=evidence.uploaded_at,
        s3_url=evidence.s3_url,
        download_url=f"/api/v1/evidence/{evidence.id}/download",
        integrity_status="valid",
        last_integrity_check=integrity_check.checked_at,
    )


@router.get(
    "/evidence/{evidence_id}",
    response_model=EvidenceResponse,
    summary="Get evidence metadata",
    description="""
    Get evidence file metadata by ID.

    **Response** (200 OK):
    - Evidence metadata with SHA256 hash
    - Integrity status (valid/failed/pending)
    - Download URL (not implemented yet)

    **Response** (404 Not Found):
    - Evidence not found
    """,
)
async def get_evidence(
    evidence_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Get evidence metadata by ID."""

    # Fetch evidence with uploader
    result = await db.execute(
        select(GateEvidence, User)
        .join(User, GateEvidence.uploaded_by == User.id)
        .where(GateEvidence.id == evidence_id)
    )
    evidence_row = result.first()

    if not evidence_row:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Evidence with ID {evidence_id} not found",
        )

    evidence = evidence_row.GateEvidence
    uploader = evidence_row.User

    # Get latest integrity check
    result = await db.execute(
        select(EvidenceIntegrityCheck)
        .where(EvidenceIntegrityCheck.evidence_id == evidence_id)
        .order_by(EvidenceIntegrityCheck.checked_at.desc())
        .limit(1)
    )
    latest_check = result.scalar_one_or_none()

    integrity_status = "pending"
    last_check_time = None
    if latest_check:
        integrity_status = "valid" if latest_check.is_valid else "failed"
        last_check_time = latest_check.checked_at

    return EvidenceResponse(
        id=evidence.id,
        gate_id=evidence.gate_id,
        file_name=evidence.file_name,
        file_size=evidence.file_size,
        file_size_mb=evidence.file_size_mb,
        file_type=evidence.file_type,
        evidence_type=evidence.evidence_type,
        sha256_hash=evidence.sha256_hash,
        description=evidence.description,
        uploaded_by=evidence.uploaded_by,
        uploaded_by_name=uploader.name,
        uploaded_at=evidence.uploaded_at,
        s3_url=evidence.s3_url,
        download_url=f"/api/v1/evidence/{evidence.id}/download",
        integrity_status=integrity_status,
        last_integrity_check=last_check_time,
    )


@router.get(
    "/evidence",
    response_model=EvidenceListResponse,
    summary="List evidence files",
    description="""
    List evidence files with pagination and filtering.

    **Query Parameters**:
    - gate_id: Filter by gate UUID (optional)
    - evidence_type: Filter by evidence type (optional)
    - page: Page number (default: 1)
    - page_size: Items per page (default: 20, max: 100)

    **Response** (200 OK):
    - Paginated list of evidence files
    - Total count and pages
    """,
)
async def list_evidence(
    gate_id: Optional[UUID] = Query(None, description="Filter by gate ID"),
    evidence_type: Optional[str] = Query(None, description="Filter by evidence type"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """List evidence files with pagination and filtering."""

    # Build query
    query = select(GateEvidence, User).join(User, GateEvidence.uploaded_by == User.id)

    # Apply filters
    if gate_id:
        query = query.where(GateEvidence.gate_id == gate_id)
    if evidence_type:
        query = query.where(GateEvidence.evidence_type == evidence_type.upper())

    # Get total count
    count_query = select(func.count()).select_from(GateEvidence)
    if gate_id:
        count_query = count_query.where(GateEvidence.gate_id == gate_id)
    if evidence_type:
        count_query = count_query.where(GateEvidence.evidence_type == evidence_type.upper())

    result = await db.execute(count_query)
    total = result.scalar()

    # Apply pagination
    offset = (page - 1) * page_size
    query = query.order_by(GateEvidence.uploaded_at.desc()).offset(offset).limit(page_size)

    # Fetch evidence
    result = await db.execute(query)
    evidence_rows = result.all()

    # Build response
    items = []
    for row in evidence_rows:
        evidence = row.GateEvidence
        uploader = row.User

        # Get latest integrity check
        result = await db.execute(
            select(EvidenceIntegrityCheck)
            .where(EvidenceIntegrityCheck.evidence_id == evidence.id)
            .order_by(EvidenceIntegrityCheck.checked_at.desc())
            .limit(1)
        )
        latest_check = result.scalar_one_or_none()

        integrity_status = "pending"
        last_check_time = None
        if latest_check:
            integrity_status = "valid" if latest_check.is_valid else "failed"
            last_check_time = latest_check.checked_at

        items.append(
            EvidenceResponse(
                id=evidence.id,
                gate_id=evidence.gate_id,
                file_name=evidence.file_name,
                file_size=evidence.file_size,
                file_size_mb=evidence.file_size_mb,
                file_type=evidence.file_type,
                evidence_type=evidence.evidence_type,
                sha256_hash=evidence.sha256_hash,
                description=evidence.description,
                uploaded_by=evidence.uploaded_by,
                uploaded_by_name=uploader.name,
                uploaded_at=evidence.uploaded_at,
                s3_url=evidence.s3_url,
                download_url=f"/api/v1/evidence/{evidence.id}/download",
                integrity_status=integrity_status,
                last_integrity_check=last_check_time,
            )
        )

    return EvidenceListResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        pages=(total + page_size - 1) // page_size,
    )


@router.get(
    "/evidence/{evidence_id}/download",
    summary="Download evidence file",
    description="""
    Get pre-signed URL for downloading evidence file (FR2 - Evidence Vault).

    **Design Reference**: API-CHANGELOG.md v1.0.0
    - Pre-signed URL with 15-minute expiry
    - Increments download_count

    **Response** (200 OK):
    - JSON with presigned_url for frontend to open
    - URL valid for 15 minutes (900 seconds)

    **Response** (404 Not Found):
    - Evidence not found
    """,
)
async def download_evidence(
    evidence_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Download evidence file via pre-signed URL."""
    # Fetch evidence
    result = await db.execute(
        select(GateEvidence).where(GateEvidence.id == evidence_id)
    )
    evidence = result.scalar_one_or_none()

    if not evidence:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Evidence with ID {evidence_id} not found",
        )

    # Generate pre-signed download URL (15 min expiry per design)
    try:
        presigned_url = minio_service.generate_presigned_download_url(
            evidence.s3_key,
            expiration=900,  # 15 minutes as per design
        )
    except ClientError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate download URL: {str(e)}",
        )

    # Increment download count (if column exists)
    if hasattr(evidence, 'download_count'):
        evidence.download_count = (evidence.download_count or 0) + 1
        await db.commit()

    # Return JSON with presigned URL (frontend will open this URL)
    return {
        "presigned_url": presigned_url,
        "file_name": evidence.file_name,
        "expires_in": 900,
    }


@router.get(
    "/evidence/{evidence_id}/file",
    summary="Download evidence file (streaming)",
    description="""
    Download evidence file directly through backend (streaming response).

    This endpoint streams the file through the backend, avoiding CORS/mixed-content
    issues when MinIO is not directly accessible from the browser.

    **Response**: Binary file with appropriate Content-Type and Content-Disposition headers.
    """,
)
async def download_evidence_file(
    evidence_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Download evidence file directly (streaming through backend)."""
    # Fetch evidence
    result = await db.execute(
        select(GateEvidence).where(GateEvidence.id == evidence_id)
    )
    evidence = result.scalar_one_or_none()

    if not evidence:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Evidence with ID {evidence_id} not found",
        )

    # Download file from MinIO
    try:
        file_content = minio_service.download_file(evidence.s3_key)
    except ClientError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to download file: {str(e)}",
        )

    # Increment download count (if column exists)
    if hasattr(evidence, 'download_count'):
        evidence.download_count = (evidence.download_count or 0) + 1
        await db.commit()

    # Determine content type
    content_type = evidence.file_type or "application/octet-stream"

    # Create streaming response
    return StreamingResponse(
        BytesIO(file_content),
        media_type=content_type,
        headers={
            "Content-Disposition": f'attachment; filename="{evidence.file_name}"',
            "Content-Length": str(len(file_content)),
        },
    )


@router.post(
    "/evidence/{evidence_id}/integrity-check",
    response_model=IntegrityCheckResponse,
    summary="Run integrity check",
    description="""
    Run SHA256 integrity check on evidence file.

    **Week 4 Day 3 - REAL SHA256 Verification** ✅:
    - Download file from MinIO
    - Recompute SHA256 hash from actual file content
    - Compare with original hash stored in database
    - Detect file tampering or corruption

    **Request Body**:
    - force: Force recompute hash from S3 (default: false)

    **Response** (200 OK):
    - Integrity check result (valid/failed)
    - Original hash vs current hash
    - Error message if tampered
    """,
)
async def check_integrity(
    evidence_id: UUID,
    request: IntegrityCheckRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Run integrity check on evidence file with REAL SHA256 verification."""

    # Fetch evidence
    result = await db.execute(select(GateEvidence).where(GateEvidence.id == evidence_id))
    evidence = result.scalar_one_or_none()

    if not evidence:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Evidence with ID {evidence_id} not found",
        )

    # Download file from MinIO and recompute SHA256 hash
    original_hash = evidence.sha256_hash
    current_hash = original_hash  # Default: assume same
    error_message = None

    try:
        # Download file content from MinIO
        file_content = minio_service.download_file(evidence.s3_key)

        # Recompute SHA256 hash
        current_hash = minio_service.compute_sha256(file_content)

        # Verify integrity
        is_valid = minio_service.verify_sha256(file_content, original_hash)

        if not is_valid:
            error_message = (
                f"Hash mismatch! File has been tampered or corrupted. "
                f"Expected: {original_hash[:16]}..., Got: {current_hash[:16]}..."
            )

    except ClientError as e:
        is_valid = False
        error_message = f"Failed to download file from storage: {str(e)}"
        current_hash = "error"

    # Create integrity check record
    integrity_check = EvidenceIntegrityCheck(
        evidence_id=evidence_id,
        checked_at=datetime.utcnow(),
        sha256_hash=current_hash if current_hash != "error" else original_hash,
        is_valid=is_valid,
        error_message=error_message,
        checked_by=f"user-{current_user.id}",
    )
    db.add(integrity_check)
    await db.commit()

    return IntegrityCheckResponse(
        evidence_id=evidence_id,
        file_name=evidence.file_name,
        is_valid=is_valid,
        original_hash=original_hash,
        current_hash=current_hash,
        checked_at=integrity_check.checked_at,
        checked_by=integrity_check.checked_by,
        error_message=error_message,
    )


@router.get(
    "/evidence/{evidence_id}/integrity-history",
    response_model=IntegrityCheckHistoryResponse,
    summary="Get integrity check history",
    description="""
    Get integrity check history for an evidence file.

    **Response** (200 OK):
    - List of all integrity checks
    - Total checks, failed checks, success rate
    """,
)
async def get_integrity_history(
    evidence_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Get integrity check history for an evidence file."""

    # Fetch evidence
    result = await db.execute(select(GateEvidence).where(GateEvidence.id == evidence_id))
    evidence = result.scalar_one_or_none()

    if not evidence:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Evidence with ID {evidence_id} not found",
        )

    # Fetch all integrity checks
    result = await db.execute(
        select(EvidenceIntegrityCheck)
        .where(EvidenceIntegrityCheck.evidence_id == evidence_id)
        .order_by(EvidenceIntegrityCheck.checked_at.desc())
    )
    checks = result.scalars().all()

    # Calculate stats
    total_checks = len(checks)
    failed_checks = sum(1 for check in checks if not check.is_valid)
    success_rate = ((total_checks - failed_checks) / total_checks * 100) if total_checks > 0 else 100.0

    # Build response
    checks_list = [
        {
            "id": str(check.id),
            "checked_at": check.checked_at.isoformat(),
            "is_valid": check.is_valid,
            "checked_by": check.checked_by,
        }
        for check in checks
    ]

    return IntegrityCheckHistoryResponse(
        evidence_id=evidence_id,
        file_name=evidence.file_name,
        checks=checks_list,
        total_checks=total_checks,
        failed_checks=failed_checks,
        success_rate=success_rate,
    )
