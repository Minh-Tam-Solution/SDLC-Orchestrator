"""
=========================================================================
Audit Export Route — Sprint 211 Track D (CSV/PDF Evidence Export).

GET /evidence/export?format=csv&project_id=<UUID>
  - Exports evidence records as CSV (StreamingResponse)
  - Joins GateEvidence → Gate (project filter, gate_type) → User (uploader name)

GET /evidence/export?format=pdf&project_id=<UUID>
  - Exports evidence records as PDF via reportlab (optional dependency)
  - Returns 501 if reportlab is not installed

Both formats share the same query logic via _fetch_evidence_rows().

SDLC 6.1.1 — Sprint 211 Track D Deliverable
Authority: CTO + CPO Approved
Zero Mock Policy: 100% COMPLIANCE (all real implementations)
=========================================================================
"""

from __future__ import annotations

import csv
import io
import logging
from datetime import datetime, timezone
from typing import Any, List, Optional, Sequence, Tuple
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import aliased

from app.api.dependencies import get_current_active_user
from app.db.session import get_db
from app.models.gate import Gate
from app.models.gate_evidence import GateEvidence
from app.models.user import User

# ---------------------------------------------------------------------------
# Optional dependency guard — CTO Sprint 185 mandate
# reportlab is ENTERPRISE-tier; must not break imports when absent.
# ---------------------------------------------------------------------------
try:
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.lib.units import mm
    from reportlab.platypus import (
        Paragraph,
        SimpleDocTemplate,
        Spacer,
        Table,
        TableStyle,
    )

    _REPORTLAB_AVAILABLE = True
except ImportError:  # pragma: no cover
    _REPORTLAB_AVAILABLE = False

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/evidence", tags=["Audit Export"])

# ---------------------------------------------------------------------------
# Column spec — shared between CSV and PDF
# ---------------------------------------------------------------------------
_EXPORT_COLUMNS: List[str] = [
    "evidence_type",
    "file_name",
    "upload_date",
    "submitter",
    "sha256_hash",
    "gate_type",
    "gate_binding",
    "integrity_status",
    "source",
]


# ---------------------------------------------------------------------------
# Shared query helper
# ---------------------------------------------------------------------------


async def _fetch_evidence_rows(
    db: AsyncSession,
    project_id: UUID,
) -> Sequence[Tuple[Any, ...]]:
    """
    Query evidence records joined with Gate and User for a given project.

    Returns a sequence of tuples matching _EXPORT_COLUMNS order:
        (evidence_type, file_name, upload_date, submitter, sha256_hash,
         gate_type, gate_binding, integrity_status, source)
    """
    uploader = aliased(User, name="uploader")

    stmt = (
        select(
            GateEvidence.evidence_type,
            GateEvidence.file_name,
            GateEvidence.created_at,
            uploader.full_name,
            uploader.email,
            GateEvidence.sha256_hash,
            Gate.gate_type,
            GateEvidence.gate_id,
            GateEvidence.sha256_server,
            GateEvidence.source,
        )
        .join(Gate, GateEvidence.gate_id == Gate.id)
        .outerjoin(uploader, GateEvidence.uploaded_by == uploader.id)
        .where(Gate.project_id == project_id)
        .where(GateEvidence.deleted_at.is_(None))
        .order_by(GateEvidence.created_at.desc())
    )

    result = await db.execute(stmt)
    raw_rows = result.all()

    rows: List[Tuple[str, ...]] = []
    for row in raw_rows:
        (
            evidence_type,
            file_name,
            created_at,
            full_name,
            email,
            sha256_hash,
            gate_type,
            gate_id,
            sha256_server,
            source,
        ) = row

        # Submitter: prefer full_name, fall back to email, then "unknown"
        submitter = full_name or email or "unknown"

        # Upload date: ISO 8601 string
        upload_date = (
            created_at.strftime("%Y-%m-%dT%H:%M:%SZ") if created_at else ""
        )

        # Integrity status derived from hash comparison
        if sha256_hash and sha256_server:
            integrity = "verified" if sha256_hash == sha256_server else "mismatch"
        elif sha256_hash:
            integrity = "hash_present"
        else:
            integrity = "no_hash"

        rows.append(
            (
                evidence_type or "",
                file_name or "",
                upload_date,
                submitter,
                sha256_hash or "",
                gate_type or "",
                str(gate_id) if gate_id else "",
                integrity,
                source or "",
            )
        )

    return rows


# ---------------------------------------------------------------------------
# CSV generation
# ---------------------------------------------------------------------------


def _build_csv(rows: Sequence[Tuple[str, ...]]) -> str:
    """
    Build a CSV string from evidence rows (always includes header row).

    Args:
        rows: Sequence of tuples matching _EXPORT_COLUMNS order.

    Returns:
        Complete CSV content as a string.
    """
    output = io.StringIO()
    writer = csv.writer(output, quoting=csv.QUOTE_MINIMAL)
    writer.writerow(_EXPORT_COLUMNS)
    for row in rows:
        writer.writerow(row)
    return output.getvalue()


# ---------------------------------------------------------------------------
# PDF generation
# ---------------------------------------------------------------------------


def _build_pdf(
    rows: Sequence[Tuple[str, ...]],
    project_id: UUID,
    exported_by: str,
) -> bytes:
    """
    Build a PDF audit report from evidence rows using reportlab.

    Args:
        rows: Sequence of tuples matching _EXPORT_COLUMNS order.
        project_id: The project UUID for the report header.
        exported_by: Display name or email of the exporter.

    Returns:
        PDF content as bytes.

    Raises:
        RuntimeError: If reportlab is not installed (should be pre-checked).
    """
    if not _REPORTLAB_AVAILABLE:
        raise RuntimeError(
            "reportlab is required for PDF export. "
            "Install: pip install 'reportlab>=4.4.4'"
        )

    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf,
        pagesize=A4,
        leftMargin=15 * mm,
        rightMargin=15 * mm,
        topMargin=20 * mm,
        bottomMargin=20 * mm,
    )

    styles = getSampleStyleSheet()
    elements: list[Any] = []

    # --- Title ---
    title_style = styles["Title"]
    elements.append(
        Paragraph("SDLC Orchestrator — Evidence Audit Report", title_style)
    )
    elements.append(Spacer(1, 6 * mm))

    # --- Metadata ---
    normal = styles["Normal"]
    now_utc = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    elements.append(Paragraph(f"<b>Project ID:</b> {project_id}", normal))
    elements.append(Paragraph(f"<b>Export Date:</b> {now_utc}", normal))
    elements.append(Paragraph(f"<b>Exported By:</b> {exported_by}", normal))
    elements.append(
        Paragraph(f"<b>Total Records:</b> {len(rows)}", normal)
    )
    elements.append(Spacer(1, 8 * mm))

    # --- Table ---
    if rows:
        # Truncate long values for readability in PDF cells
        header = [col.replace("_", " ").title() for col in _EXPORT_COLUMNS]
        table_data: list[list[str]] = [header]
        for row in rows:
            table_data.append(
                [_truncate(cell, max_len=40) for cell in row]
            )

        col_widths = [
            55,  # evidence_type
            60,  # file_name
            62,  # upload_date
            55,  # submitter
            50,  # sha256_hash (truncated)
            50,  # gate_type
            45,  # gate_binding (truncated)
            42,  # integrity_status
            35,  # source
        ]

        table = Table(table_data, colWidths=col_widths, repeatRows=1)
        table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1a365d")),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, 0), 7),
                    ("FONTSIZE", (0, 1), (-1, -1), 6),
                    ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                    ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f7fafc")]),
                    ("LEFTPADDING", (0, 0), (-1, -1), 3),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 3),
                    ("TOPPADDING", (0, 0), (-1, -1), 3),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
                ]
            )
        )
        elements.append(table)
    else:
        elements.append(Spacer(1, 10 * mm))
        elements.append(
            Paragraph(
                "<i>No evidence records found for this project.</i>",
                normal,
            )
        )

    # --- Footer ---
    elements.append(Spacer(1, 12 * mm))
    footer_style = styles["Italic"]
    elements.append(
        Paragraph(
            "Generated by SDLC Orchestrator — SDLC 6.1.1 Framework",
            footer_style,
        )
    )

    doc.build(elements)
    return buf.getvalue()


def _truncate(value: str, max_len: int = 40) -> str:
    """Truncate a string value for PDF table cell readability."""
    if len(value) <= max_len:
        return value
    return value[: max_len - 3] + "..."


# ---------------------------------------------------------------------------
# Route
# ---------------------------------------------------------------------------


@router.get(
    "/export",
    summary="Export evidence audit records (CSV or PDF)",
    response_description="Evidence audit data in the requested format",
    responses={
        200: {
            "description": "Evidence export file",
            "content": {
                "text/csv": {},
                "application/pdf": {},
            },
        },
        400: {"description": "Invalid format parameter"},
        501: {"description": "PDF export requires reportlab (not installed)"},
    },
)
async def export_evidence(
    project_id: UUID = Query(
        ..., description="Project UUID to filter evidence records"
    ),
    format: str = Query(
        "csv",
        description="Export format: 'csv' or 'pdf'",
        pattern="^(csv|pdf)$",
    ),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> StreamingResponse:
    """
    Export evidence audit records for a project as CSV or PDF.

    Joins GateEvidence with Gate (for project_id filtering and gate_type)
    and User (for uploader name). Returns a downloadable file attachment.

    CSV includes a header row and all matching evidence records.
    PDF includes a formatted title page, metadata, evidence table, and footer.

    Args:
        project_id: UUID of the project to export evidence for.
        format: Export format — 'csv' (default) or 'pdf'.
        current_user: Authenticated user (injected via dependency).
        db: Async database session (injected via dependency).

    Returns:
        StreamingResponse with the exported file content.

    Raises:
        HTTPException 400: If format is not 'csv' or 'pdf'.
        HTTPException 501: If format is 'pdf' and reportlab is not installed.
    """
    format_lower = format.strip().lower()
    if format_lower not in ("csv", "pdf"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid format '{format}'. Supported: csv, pdf",
        )

    rows = await _fetch_evidence_rows(db, project_id)
    today_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    logger.info(
        "audit_export: format=%s project=%s user=%s rows=%d",
        format_lower,
        project_id,
        current_user.email,
        len(rows),
    )

    if format_lower == "csv":
        csv_content = _build_csv(rows)
        filename = f"evidence_export_{project_id}_{today_str}.csv"
        return StreamingResponse(
            iter([csv_content]),
            media_type="text/csv",
            headers={
                "Content-Disposition": f'attachment; filename="{filename}"',
            },
        )

    # --- PDF ---
    if not _REPORTLAB_AVAILABLE:
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail=(
                "reportlab is required for PDF export. "
                "Install: pip install 'reportlab>=4.4.4'"
            ),
        )

    exported_by = current_user.full_name or current_user.email or "unknown"
    try:
        pdf_bytes = _build_pdf(rows, project_id, exported_by)
    except Exception as exc:
        logger.error(
            "audit_export: PDF generation failed project=%s error=%s",
            project_id,
            str(exc),
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"PDF generation failed: {str(exc)}",
        )

    filename = f"evidence_audit_{project_id}_{today_str}.pdf"
    return StreamingResponse(
        iter([pdf_bytes]),
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
        },
    )
