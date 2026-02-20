"""
==========================================================================
SOC2PackService — Sprint 185 (Advanced Audit Trail, SOC2 Type II)
SDLC Orchestrator — ENTERPRISE Tier

Purpose:
- Auto-collect evidence from existing Orchestrator tables
- Map collected evidence to SOC2 Trust Service Criteria (TSC)
- Generate a structured PDF evidence pack using reportlab (BSD license)

SOC2 Trust Service Criteria Covered:
  CC1.1  — Control Environment: organization + team setup evidence
  CC6.1  — Logical Access Controls: user admin + SSO event audit logs
  CC6.2  — Credential Management: API key + SSO config events
  CC6.6  — Logical Access Revocation: user deactivation events
  CC7.2  — System Monitoring: audit log completeness
  CC8.1  — Change Management: gate approval/rejection trail
  A1.1   — System Availability: gate G3/G4 evidence (Ship Ready)
  A1.2   — Uptime Evidence: health check audit events

Dependencies:
  reportlab==4.4.4 (BSD license — approved in requirements.txt)
  SQLAlchemy 2.0 async (existing project dependency)

Usage:
  service = SOC2PackService(db)
  pack = await service.generate_pack(
      organization_id=org_id,
      from_date=datetime(2026, 1, 1, tzinfo=timezone.utc),
      to_date=datetime(2026, 2, 1, tzinfo=timezone.utc),
  )
  # pack.pdf_bytes  → bytes to stream or store
  # pack.summary    → dict with evidence counts per TSC

SDLC 6.1.0 — Sprint 185 P0 Deliverable
Authority: CTO + CPO Approved (ADR-059)
==========================================================================
"""

from __future__ import annotations

import io
import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

# CTO Sprint 185 action item #5: module-level try/except ImportError guard
# Allows the module to be imported (and mocked) in test environments even
# when reportlab is not installed.  Production always has it (requirements.txt).
try:
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import mm
    from reportlab.platypus import (
        HRFlowable,
        Paragraph,
        SimpleDocTemplate,
        Spacer,
        Table,
        TableStyle,
    )
    _REPORTLAB_AVAILABLE = True
except ImportError:  # pragma: no cover
    _REPORTLAB_AVAILABLE = False
    colors = None  # type: ignore[assignment]
    A4 = None  # type: ignore[assignment]
    getSampleStyleSheet = None  # type: ignore[assignment]
    ParagraphStyle = None  # type: ignore[assignment]
    mm = None  # type: ignore[assignment]
    HRFlowable = None  # type: ignore[assignment]
    Paragraph = None  # type: ignore[assignment]
    SimpleDocTemplate = None  # type: ignore[assignment]
    Spacer = None  # type: ignore[assignment]
    Table = None  # type: ignore[assignment]
    TableStyle = None  # type: ignore[assignment]
from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.audit_log import AuditLog

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# SOC2 Trust Service Criteria mapping
# ---------------------------------------------------------------------------

# Maps (event_type, action) tuples → list of TSC control IDs they satisfy
TSC_MAPPING: dict[tuple[str, str], list[str]] = {
    # CC1.1 Control Environment
    ("user_admin", "create"):      ["CC1.1"],
    ("user_admin", "deactivate"):  ["CC1.1", "CC6.6"],
    # CC6.1 Logical Access
    ("user_admin", "grant"):       ["CC6.1"],
    ("user_admin", "revoke"):      ["CC6.1", "CC6.6"],
    ("sso_event", "login"):        ["CC6.1"],
    ("sso_event", "logout"):       ["CC6.1"],
    ("sso_event", "provision"):    ["CC6.1", "CC6.2"],
    # CC6.2 Credential Management
    ("api_key_event", "create"):   ["CC6.2"],
    ("api_key_event", "revoke"):   ["CC6.2", "CC6.6"],
    # CC7.2 System Monitoring
    ("gate_action", "evaluate"):   ["CC7.2"],
    # CC7.2 + CC8.1 + A1.1: Gate approval = change management + availability evidence.
    # G3/G4 "approve" is the primary A1.1 signal — Ship Ready gate demonstrates
    # the system is designed and built to meet availability commitments.
    # F-02 fix (Sprint 185 code review): A1.1 was listed in ALL_TSC_CONTROLS but had
    # no TSC_MAPPING entries, so it always showed 0 evidence — a red flag for auditors.
    ("gate_action", "approve"):    ["CC7.2", "CC8.1", "A1.1"],
    ("gate_action", "reject"):     ["CC7.2", "CC8.1"],
    ("gate_action", "submit"):     ["CC7.2"],
    # CC8.1 Change Management
    ("evidence_access", "upload"): ["CC8.1"],
    ("evidence_access", "verify"): ["CC7.2"],
    # A1.1 + A1.2 Availability: health/system events cover both uptime criteria.
    ("system_event", "create"):    ["A1.1", "A1.2"],
    # Export audit
    ("export_event", "export"):    ["CC7.2"],
}

ALL_TSC_CONTROLS = [
    "CC1.1", "CC6.1", "CC6.2", "CC6.6", "CC7.2", "CC8.1", "A1.1", "A1.2",
]

TSC_DESCRIPTIONS: dict[str, str] = {
    "CC1.1": "Control Environment — Organizational structure, policies, tone at the top",
    "CC6.1": "Logical Access Controls — Who has access to which resources",
    "CC6.2": "Credential Management — API keys, SSO tokens, secrets lifecycle",
    "CC6.6": "Logical Access Revocation — Removal of access when no longer needed",
    "CC7.2": "System Monitoring — Ongoing monitoring of security controls",
    "CC8.1": "Change Management — Gate approval trail for production changes",
    "A1.1":  "Availability — System designed and implemented to meet uptime commitments",
    "A1.2":  "Availability Monitoring — Monitoring for system availability",
}


# ---------------------------------------------------------------------------
# Data containers
# ---------------------------------------------------------------------------


@dataclass
class SOC2Evidence:
    """Single evidence item for a TSC control."""

    tsc_control: str
    event_type: str
    action: str
    actor_email: str
    resource_type: str
    resource_id: str
    detail_summary: str
    created_at: str


@dataclass
class SOC2PackResult:
    """Result of SOC2PackService.generate_pack()."""

    pdf_bytes: bytes
    organization_id: str
    from_date: str
    to_date: str
    generated_at: str
    total_events: int
    summary: dict[str, int]   # {tsc_control: evidence_count}
    evidence_by_control: dict[str, list[SOC2Evidence]] = field(default_factory=dict)


# ---------------------------------------------------------------------------
# Service
# ---------------------------------------------------------------------------


class SOC2PackService:
    """
    Generates a SOC2 Type II evidence pack PDF from audit log events.

    Workflow:
        1. Query audit_logs for the organization + date range
        2. Map events to TSC controls via TSC_MAPPING
        3. Generate PDF with cover page, summary, per-control evidence tables
        4. Return SOC2PackResult with pdf_bytes + metadata
    """

    # F-01 fix (Sprint 185 code review): conditional defaults when reportlab is absent.
    # A4 = (595.27, 841.89) points; 20mm = 56.69 points.
    # Class-level unpacking of None would TypeError at class definition time,
    # defeating the module-level ImportError guard for test environments.
    _PAGE_WIDTH, _PAGE_HEIGHT = A4 if A4 is not None else (595.27, 841.89)
    _MARGIN = 20 * mm if mm is not None else 56.69

    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    # -------------------------------------------------------------------------
    # Public API
    # -------------------------------------------------------------------------

    async def generate_pack(
        self,
        organization_id: str,
        from_date: datetime,
        to_date: datetime,
    ) -> SOC2PackResult:
        """
        Generate a SOC2 evidence pack PDF for the given org and date range.

        Args:
            organization_id: Organization UUID string
            from_date:        Start of evidence window (UTC)
            to_date:          End of evidence window (UTC)

        Returns:
            SOC2PackResult with pdf_bytes ready to stream or store.

        Raises:
            ValueError: if from_date >= to_date
        """
        if not _REPORTLAB_AVAILABLE:
            raise RuntimeError(
                "reportlab is required for SOC2 PDF generation. "
                "Install: pip install 'reportlab>=4.4.4'"
            )

        if from_date >= to_date:
            raise ValueError("from_date must be before to_date")

        logger.info(
            "Generating SOC2 pack: org=%s from=%s to=%s",
            organization_id,
            from_date.isoformat(),
            to_date.isoformat(),
        )

        # 1. Collect audit events
        events = await self._collect_events(organization_id, from_date, to_date)

        # 2. Map to TSC controls
        evidence_by_control = self._map_to_tsc(events)

        # 3. Build summary
        summary = {ctrl: len(evs) for ctrl, evs in evidence_by_control.items()}

        # 4. Generate PDF
        pdf_bytes = self._render_pdf(
            organization_id=organization_id,
            from_date=from_date,
            to_date=to_date,
            evidence_by_control=evidence_by_control,
            summary=summary,
        )

        generated_at = datetime.now(timezone.utc).isoformat()
        total_events = len(events)

        logger.info(
            "SOC2 pack generated: org=%s total_events=%d controls=%d size=%dKB",
            organization_id,
            total_events,
            len(evidence_by_control),
            len(pdf_bytes) // 1024,
        )

        return SOC2PackResult(
            pdf_bytes=pdf_bytes,
            organization_id=organization_id,
            from_date=from_date.isoformat(),
            to_date=to_date.isoformat(),
            generated_at=generated_at,
            total_events=total_events,
            summary=summary,
            evidence_by_control=evidence_by_control,
        )

    # -------------------------------------------------------------------------
    # Private: data collection
    # -------------------------------------------------------------------------

    async def _collect_events(
        self,
        organization_id: str,
        from_date: datetime,
        to_date: datetime,
    ) -> list[AuditLog]:
        """Query audit_logs for the org + date range, newest-last."""
        stmt = (
            select(AuditLog)
            .where(
                and_(
                    AuditLog.organization_id == organization_id,
                    AuditLog.created_at >= from_date,
                    AuditLog.created_at <= to_date,
                )
            )
            .order_by(AuditLog.created_at.asc())
        )
        result = await self._db.execute(stmt)
        return list(result.scalars().all())

    # -------------------------------------------------------------------------
    # Private: TSC mapping
    # -------------------------------------------------------------------------

    def _map_to_tsc(
        self, events: list[AuditLog]
    ) -> dict[str, list[SOC2Evidence]]:
        """
        Map audit log events to SOC2 TSC controls.

        Returns dict keyed by control ID, value is list of SOC2Evidence.
        Controls with zero evidence are included with empty lists.
        """
        evidence_by_control: dict[str, list[SOC2Evidence]] = {
            ctrl: [] for ctrl in ALL_TSC_CONTROLS
        }

        for event in events:
            key = (event.event_type, event.action)
            controls = TSC_MAPPING.get(key, [])

            detail_summary = self._summarize_detail(event.detail)

            for ctrl in controls:
                if ctrl in evidence_by_control:
                    evidence_by_control[ctrl].append(
                        SOC2Evidence(
                            tsc_control=ctrl,
                            event_type=event.event_type,
                            action=event.action,
                            actor_email=event.actor_email or "(system)",
                            resource_type=event.resource_type or "-",
                            resource_id=(event.resource_id or "-")[:8] + "...",  # truncate for readability
                            detail_summary=detail_summary,
                            created_at=(
                                event.created_at.strftime("%Y-%m-%d %H:%M UTC")
                                if event.created_at else "-"
                            ),
                        )
                    )

        return evidence_by_control

    def _summarize_detail(self, detail: dict[str, Any] | None) -> str:
        """Convert JSONB detail to a short human-readable string (max 120 chars)."""
        if not detail:
            return "-"
        try:
            parts = []
            for k, v in detail.items():
                parts.append(f"{k}={v!r}")
                if len(", ".join(parts)) > 100:
                    parts.append("...")
                    break
            return ", ".join(parts)[:120]
        except Exception:
            return str(detail)[:120]

    # -------------------------------------------------------------------------
    # Private: PDF rendering
    # -------------------------------------------------------------------------

    def _render_pdf(
        self,
        organization_id: str,
        from_date: datetime,
        to_date: datetime,
        evidence_by_control: dict[str, list[SOC2Evidence]],
        summary: dict[str, int],
    ) -> bytes:
        """
        Render the SOC2 evidence pack as a PDF using reportlab.

        Structure:
          Page 1: Cover — title, org, period, generated_at
          Page 2: Executive Summary — control coverage table
          Pages 3+: Per-control evidence tables (one section per TSC control)
        """
        buf = io.BytesIO()
        doc = SimpleDocTemplate(
            buf,
            pagesize=A4,
            leftMargin=self._MARGIN,
            rightMargin=self._MARGIN,
            topMargin=self._MARGIN,
            bottomMargin=self._MARGIN,
        )
        styles = getSampleStyleSheet()
        story: list[Any] = []

        # ----- styles -----
        title_style = ParagraphStyle(
            "SocTitle",
            parent=styles["Title"],
            fontSize=24,
            spaceAfter=6,
            textColor=colors.HexColor("#1a365d"),
        )
        h1_style = ParagraphStyle(
            "SocH1",
            parent=styles["Heading1"],
            fontSize=16,
            textColor=colors.HexColor("#1a365d"),
            spaceBefore=12,
            spaceAfter=4,
        )
        h2_style = ParagraphStyle(
            "SocH2",
            parent=styles["Heading2"],
            fontSize=13,
            textColor=colors.HexColor("#2c5282"),
            spaceBefore=10,
            spaceAfter=4,
        )
        body_style = styles["Normal"]
        small_style = ParagraphStyle(
            "SocSmall", parent=styles["Normal"], fontSize=8
        )

        # ===== Cover Page =====
        story.append(Spacer(1, 30 * mm))
        story.append(Paragraph("SOC2 Type II Evidence Pack", title_style))
        story.append(Paragraph("SDLC Orchestrator — Compliance Evidence Report", body_style))
        story.append(Spacer(1, 8 * mm))
        story.append(HRFlowable(width="100%", thickness=2, color=colors.HexColor("#2c5282")))
        story.append(Spacer(1, 4 * mm))

        meta_data = [
            ["Organization ID", organization_id],
            ["Evidence Period From", from_date.strftime("%Y-%m-%d %H:%M UTC")],
            ["Evidence Period To", to_date.strftime("%Y-%m-%d %H:%M UTC")],
            ["Generated At", datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")],
            ["Total Audit Events", str(sum(summary.values()))],
            ["Controls Covered", str(sum(1 for v in summary.values() if v > 0))
             + f" / {len(ALL_TSC_CONTROLS)}"],
        ]
        meta_table = Table(meta_data, colWidths=[55 * mm, 110 * mm])
        meta_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#EBF8FF")),
            ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 10),
            ("ROWBACKGROUNDS", (0, 0), (-1, -1), [colors.white, colors.HexColor("#F7FAFC")]),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E0")),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ]))
        story.append(meta_table)
        story.append(Spacer(1, 6 * mm))

        disclaimer = (
            "This report was auto-generated by SDLC Orchestrator from tamper-evident "
            "audit logs enforced by PostgreSQL append-only trigger "
            "(SOC2 CC7.2, see migration s185_001). "
            "Evidence collection covers gate lifecycle events, user access events, "
            "SSO sessions, API key management, and evidence vault operations. "
            "This pack should be reviewed by your compliance team before submission."
        )
        story.append(Paragraph(disclaimer, small_style))

        # ===== Executive Summary =====
        story.append(Spacer(1, 8 * mm))
        story.append(Paragraph("Executive Summary — Control Coverage", h1_style))
        story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#CBD5E0")))
        story.append(Spacer(1, 3 * mm))

        summary_header = ["Control", "Description", "Evidence Count", "Status"]
        summary_rows = [summary_header]
        for ctrl in ALL_TSC_CONTROLS:
            count = summary.get(ctrl, 0)
            status_text = "COVERED" if count > 0 else "NO DATA"
            status_color = colors.HexColor("#276749") if count > 0 else colors.HexColor("#C53030")
            summary_rows.append([
                ctrl,
                TSC_DESCRIPTIONS.get(ctrl, ctrl),
                str(count),
                status_text,
            ])

        col_widths = [18 * mm, 100 * mm, 22 * mm, 22 * mm]
        summary_table = Table(summary_rows, colWidths=col_widths, repeatRows=1)
        summary_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#2c5282")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 9),
            ("ROWBACKGROUNDS", (1, 1), (-1, -1), [colors.white, colors.HexColor("#F7FAFC")]),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E0")),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ("LEFTPADDING", (0, 0), (-1, -1), 5),
            ("ALIGN", (2, 0), (3, -1), "CENTER"),
        ]))
        story.append(summary_table)

        # ===== Per-Control Evidence Sections =====
        for ctrl in ALL_TSC_CONTROLS:
            evidences = evidence_by_control.get(ctrl, [])
            story.append(Spacer(1, 10 * mm))
            story.append(Paragraph(f"{ctrl} — {TSC_DESCRIPTIONS.get(ctrl, ctrl)}", h2_style))
            story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#CBD5E0")))
            story.append(Spacer(1, 2 * mm))

            if not evidences:
                story.append(Paragraph(
                    "No audit events collected for this control in the specified period.",
                    small_style,
                ))
                continue

            ev_header = ["Timestamp (UTC)", "Event Type", "Action", "Actor", "Resource", "Detail"]
            ev_rows = [ev_header]
            for ev in evidences[:100]:   # cap at 100 rows per control to keep PDF manageable
                ev_rows.append([
                    ev.created_at,
                    ev.event_type,
                    ev.action,
                    ev.actor_email,
                    f"{ev.resource_type}:{ev.resource_id}",
                    ev.detail_summary[:80],
                ])

            if len(evidences) > 100:
                ev_rows.append([
                    f"... {len(evidences) - 100} more events (see full export)",
                    "", "", "", "", "",
                ])

            ev_col_widths = [32 * mm, 24 * mm, 18 * mm, 36 * mm, 30 * mm, 28 * mm]
            ev_table = Table(ev_rows, colWidths=ev_col_widths, repeatRows=1)
            ev_table.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#2c5282")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 7),
                ("ROWBACKGROUNDS", (1, 1), (-1, -1), [colors.white, colors.HexColor("#F7FAFC")]),
                ("GRID", (0, 0), (-1, -1), 0.3, colors.HexColor("#CBD5E0")),
                ("TOPPADDING", (0, 0), (-1, -1), 3),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
                ("LEFTPADDING", (0, 0), (-1, -1), 4),
                ("WORDWRAP", (5, 1), (5, -1), True),
            ]))
            story.append(ev_table)

            if len(evidences) > 100:
                story.append(Paragraph(
                    f"Full {len(evidences)} events available via POST /enterprise/audit/export (format=csv).",
                    small_style,
                ))

        # Build PDF
        doc.build(story)
        return buf.getvalue()
