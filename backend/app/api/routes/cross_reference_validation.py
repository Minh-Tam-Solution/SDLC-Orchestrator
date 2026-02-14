"""
=========================================================================
Cross-Reference API Routes
SDLC Orchestrator - Sprint 155 Day 4 (Track 2: Cross-Reference Validation)

Version: 1.0.0
Date: February 5, 2026
Status: ACTIVE - Sprint 155 Implementation
Authority: Backend Lead + CTO Approved
Framework: SDLC 6.0.5

Endpoints:
- POST /api/v1/cross-reference/validate - Validate single document
- POST /api/v1/cross-reference/validate-project - Full project validation
- GET /api/v1/cross-reference/orphaned - Get orphaned documents
- GET /api/v1/cross-reference/links - Get document links

Architecture: ADR-050 Spec Converter Visual Editor
=========================================================================
"""

from __future__ import annotations

import logging
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel, Field

from app.services.cross_reference_service import (
    CrossReferenceService,
    get_cross_reference_service,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/doc-cross-reference", tags=["doc-cross-reference"])


# =========================================================================
# Request/Response Models
# =========================================================================


class ValidateDocumentRequest(BaseModel):
    """Request to validate a single document."""

    project_id: UUID = Field(..., description="Project UUID")
    document_path: str = Field(..., description="Path to document to validate")
    project_path: str = Field(default="", description="Base project path")


class ValidateProjectRequest(BaseModel):
    """Request to validate an entire project."""

    project_id: UUID = Field(..., description="Project UUID")
    project_path: str = Field(..., description="Path to project root")
    violation_types: Optional[List[str]] = Field(
        default=None, description="Filter by violation types"
    )


class ViolationResponse(BaseModel):
    """Cross-reference violation."""

    violation_type: str
    source_file: str
    target_file: str = ""
    message: str = ""
    severity: str = "warning"
    suggestion: str = ""


class ValidationResponse(BaseModel):
    """Response from validation endpoint."""

    is_valid: bool
    violations: List[ViolationResponse]
    scanned_files: int = 0
    total_links: int = 0
    duration_ms: int = 0


class OrphanedDocumentResponse(BaseModel):
    """Orphaned document info."""

    document_path: str
    document_type: str
    reason: str


class OrphanedDocumentsResponse(BaseModel):
    """Response from orphaned documents endpoint."""

    orphaned_documents: List[OrphanedDocumentResponse]


class LinkInfo(BaseModel):
    """Link information."""

    source: Optional[str] = None
    target: Optional[str] = None
    type: str
    line: Optional[int] = None


class DocumentLinksResponse(BaseModel):
    """Response from document links endpoint."""

    document_path: str
    incoming: List[dict]
    outgoing: List[dict]


# =========================================================================
# Endpoints
# =========================================================================


@router.post(
    "/validate",
    response_model=ValidationResponse,
    status_code=status.HTTP_200_OK,
    summary="Validate single document",
    description="Validate cross-references for a single document.",
)
async def validate_document(
    request: ValidateDocumentRequest,
) -> ValidationResponse:
    """
    Validate cross-references for a single document.

    Args:
        request: Validation request with project_id and document_path

    Returns:
        ValidationResponse with validation results
    """
    try:
        service = get_cross_reference_service()

        result = await service.validate_document(
            project_id=request.project_id,
            document_path=request.document_path,
            project_path=request.project_path,
        )

        return ValidationResponse(
            is_valid=result.is_valid,
            violations=[
                ViolationResponse(
                    violation_type=v.violation_type,
                    source_file=v.source_file,
                    target_file=v.target_file,
                    message=v.message,
                    severity=v.severity,
                    suggestion=v.suggestion,
                )
                for v in result.violations
            ],
            scanned_files=result.scanned_files,
            total_links=result.total_links,
            duration_ms=result.duration_ms,
        )

    except Exception as e:
        logger.error(f"Document validation error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Validation failed: {str(e)}",
        )


@router.post(
    "/validate-project",
    response_model=ValidationResponse,
    status_code=status.HTTP_200_OK,
    summary="Validate entire project",
    description="Validate all cross-references in a project.",
)
async def validate_project(
    request: ValidateProjectRequest,
) -> ValidationResponse:
    """
    Validate all cross-references in a project.

    Args:
        request: Validation request with project_id and project_path

    Returns:
        ValidationResponse with validation results
    """
    try:
        service = get_cross_reference_service()

        result = await service.validate_project(
            project_id=request.project_id,
            project_path=request.project_path,
        )

        # Filter by violation types if specified
        violations = result.violations
        if request.violation_types:
            violations = [
                v for v in violations
                if v.violation_type in request.violation_types
            ]

        return ValidationResponse(
            is_valid=len(violations) == 0 if request.violation_types else result.is_valid,
            violations=[
                ViolationResponse(
                    violation_type=v.violation_type,
                    source_file=v.source_file,
                    target_file=v.target_file,
                    message=v.message,
                    severity=v.severity,
                    suggestion=v.suggestion,
                )
                for v in violations
            ],
            scanned_files=result.scanned_files,
            total_links=result.total_links,
            duration_ms=result.duration_ms,
        )

    except Exception as e:
        logger.error(f"Project validation error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Validation failed: {str(e)}",
        )


@router.get(
    "/orphaned",
    response_model=OrphanedDocumentsResponse,
    status_code=status.HTTP_200_OK,
    summary="Get orphaned documents",
    description="Get list of documents with no cross-references.",
)
async def get_orphaned_documents(
    project_id: UUID = Query(..., description="Project UUID"),
    project_path: str = Query(default="", description="Base project path"),
    document_type: Optional[str] = Query(
        default=None, description="Filter by document type (ADR, SPEC, DOC)"
    ),
) -> OrphanedDocumentsResponse:
    """
    Get list of orphaned documents.

    Args:
        project_id: Project UUID
        project_path: Base project path
        document_type: Optional filter by document type

    Returns:
        OrphanedDocumentsResponse with list of orphaned documents
    """
    try:
        service = get_cross_reference_service()

        orphaned = await service.get_orphaned_documents(
            project_id=project_id,
            project_path=project_path,
            document_type=document_type,
        )

        return OrphanedDocumentsResponse(
            orphaned_documents=[
                OrphanedDocumentResponse(**doc)
                for doc in orphaned
            ]
        )

    except Exception as e:
        logger.error(f"Get orphaned documents error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get orphaned documents: {str(e)}",
        )


@router.get(
    "/links",
    response_model=DocumentLinksResponse,
    status_code=status.HTTP_200_OK,
    summary="Get document links",
    description="Get incoming and outgoing links for a document.",
)
async def get_document_links(
    project_id: UUID = Query(..., description="Project UUID"),
    document_path: str = Query(..., description="Path to document"),
    project_path: str = Query(default="", description="Base project path"),
    direction: str = Query(
        default="both",
        description="Link direction: 'incoming', 'outgoing', or 'both'",
    ),
) -> DocumentLinksResponse:
    """
    Get links for a document.

    Args:
        project_id: Project UUID
        document_path: Path to document
        project_path: Base project path
        direction: Link direction filter

    Returns:
        DocumentLinksResponse with incoming and outgoing links
    """
    try:
        service = get_cross_reference_service()

        links = await service.get_document_links(
            project_id=project_id,
            document_path=document_path,
            direction=direction,
            project_path=project_path,
        )

        return DocumentLinksResponse(
            document_path=links.document_path,
            incoming=links.incoming,
            outgoing=links.outgoing,
        )

    except Exception as e:
        logger.error(f"Get document links error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get document links: {str(e)}",
        )
