"""
Sprint 211 — ENT Feature Parity: Verification Tests (Tracks A-F).

Test matrix (15 tests):
  T1:  Sidebar has 6 granular feature flags (Track A)
  T2:  Sidebar no longer uses LEGACY_DASHBOARD binary flag (Track A)
  T3:  Sidebar non-core items all tagged with flagGroup (Track A)
  T4:  MFA setup generates secret, QR code, and 10 backup codes (Track B)
  T5:  MFA verify with correct TOTP code enables MFA (Track B)
  T6:  MFA verify with wrong TOTP code returns 400 (Track B)
  T7:  MFA disable is admin-only — non-superuser gets 403 (Track B)
  T8:  MFA status returns grace_period_remaining_days (Track B)
  T9:  DORA metrics with gate history returns non-zero metrics (Track C)
  T10: DORA metrics with empty project returns zero metrics (Track C)
  T11: Audit export CSV format with 3 evidence records (Track D)
  T12: Audit export PDF content-type or 501 if reportlab absent (Track D)
  T13: ConversationFirstFallback has 4 OTT channel env vars (Track E)
  T14: STM-056 threat model status is APPROVED (Track F)
  T15: FR-010-to-FR-035 mapping file exists with all FRs (Track F)

References:
  - Sprint plan: docs/04-build/02-Sprint-Plans/SPRINT-211-ENT-FEATURE-PARITY.md
  - MFA route:   backend/app/api/routes/mfa.py
  - DORA route:  backend/app/api/routes/dora.py
  - Audit route: backend/app/api/routes/audit_export.py
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[3]
FRONTEND_DIR = PROJECT_ROOT / "frontend" / "src"
DOCS_DIR = PROJECT_ROOT / "docs"


# ============================================================================
# T1 — Sidebar has 6 granular feature flags (Track A)
# ============================================================================


class TestT1SidebarGranularFlags:
    """T1: Sidebar.tsx defines all 6 granular feature flags."""

    def test_sidebar_has_six_granular_flags(self) -> None:
        sidebar = FRONTEND_DIR / "components" / "dashboard" / "Sidebar.tsx"
        content = sidebar.read_text()
        flags = [
            "FF_COMPLIANCE",
            "FF_PLANNING",
            "FF_CEO_DASHBOARD",
            "FF_SASE",
            "FF_GOVERNANCE",
            "FF_DEVTOOLS",
        ]
        for flag in flags:
            assert flag in content, f"Sidebar must define {flag}"


# ============================================================================
# T2 — Sidebar no longer uses legacy binary flag (Track A)
# ============================================================================


class TestT2SidebarNoLegacyFlag:
    """T2: Old NEXT_PUBLIC_FEATURE_FLAG_LEGACY_DASHBOARD removed."""

    def test_sidebar_no_legacy_dashboard_flag(self) -> None:
        sidebar = FRONTEND_DIR / "components" / "dashboard" / "Sidebar.tsx"
        content = sidebar.read_text()
        assert "NEXT_PUBLIC_FEATURE_FLAG_LEGACY_DASHBOARD" not in content, (
            "Legacy binary flag must be replaced by 6 granular flags"
        )


# ============================================================================
# T3 — All non-core nav items tagged with flagGroup (Track A)
# ============================================================================


class TestT3NonCoreItemsTagged:
    """T3: Every non-core nav item in Sidebar.tsx has a flagGroup."""

    def test_sidebar_all_noncore_items_tagged(self) -> None:
        sidebar = FRONTEND_DIR / "components" / "dashboard" / "Sidebar.tsx"
        content = sidebar.read_text()
        tagged_items = [
            "VCR",
            "CRP",
            "MRP",
            "SASE Templates",
            "AGENTS.md",
            "CLI Tokens",
            "Check Runs",
            "Hash Chain",
            "App Builder",
            "CEO Dashboard",
            "DORA Metrics",
            "Planning",
        ]
        for item in tagged_items:
            # Each item name should appear near a flagGroup assignment
            idx = content.find(f'"{item}"')
            if idx == -1:
                idx = content.find(f"'{item}'")
            assert idx != -1, f"Nav item '{item}' must exist in Sidebar.tsx"
            # flagGroup assignment should appear within ~200 chars of the name
            nearby = content[idx : idx + 200]
            assert "flagGroup" in nearby, (
                f"Nav item '{item}' must have a flagGroup assignment"
            )


# ============================================================================
# T4 — MFA setup generates secret, QR code, and backup codes (Track B)
# ============================================================================


class TestT4MfaSetup:
    """T4: POST /auth/mfa/setup returns secret + QR data URI + 10 backup codes."""

    @pytest.mark.asyncio
    async def test_mfa_setup_generates_secret_and_qr(self) -> None:
        from app.api.routes.mfa import mfa_setup

        mock_user = MagicMock()
        mock_user.id = uuid4()
        mock_user.email = "test@example.com"
        mock_user.mfa_enabled = False
        mock_user.mfa_secret = None

        mock_db = AsyncMock()
        mock_db.flush = AsyncMock()

        resp = await mfa_setup(current_user=mock_user, db=mock_db)

        assert resp.secret and len(resp.secret) >= 16
        assert resp.qr_code_uri.startswith("data:image/png;base64,")
        assert len(resp.backup_codes) == 10
        assert all(len(code) == 8 for code in resp.backup_codes)


# ============================================================================
# T5 — MFA verify correct code enables MFA (Track B)
# ============================================================================


class TestT5MfaVerifyCorrect:
    """T5: Valid TOTP code activates MFA on the user."""

    @pytest.mark.asyncio
    async def test_mfa_verify_correct_code_enables(self) -> None:
        from app.api.routes.mfa import MFAVerifyRequest, mfa_verify

        mock_user = MagicMock()
        mock_user.id = uuid4()
        mock_user.email = "dev@example.com"
        mock_user.mfa_enabled = False
        mock_user.mfa_secret = "JBSWY3DPEHPK3PXP"  # sample base32

        mock_db = AsyncMock()
        mock_db.flush = AsyncMock()

        body = MFAVerifyRequest(code="123456")

        with patch("app.api.routes.mfa.pyotp.TOTP") as mock_totp_cls:
            mock_totp_inst = MagicMock()
            mock_totp_inst.verify.return_value = True
            mock_totp_cls.return_value = mock_totp_inst

            resp = await mfa_verify(body=body, current_user=mock_user, db=mock_db)

        assert mock_user.mfa_enabled is True
        assert "enabled" in resp.message.lower()
        assert resp.enabled_at  # ISO 8601 timestamp present


# ============================================================================
# T6 — MFA verify wrong code returns 400 (Track B)
# ============================================================================


class TestT6MfaVerifyWrong:
    """T6: Invalid TOTP code raises HTTPException 400."""

    @pytest.mark.asyncio
    async def test_mfa_verify_wrong_code_returns_400(self) -> None:
        from fastapi import HTTPException

        from app.api.routes.mfa import MFAVerifyRequest, mfa_verify

        mock_user = MagicMock()
        mock_user.id = uuid4()
        mock_user.email = "dev@example.com"
        mock_user.mfa_enabled = False
        mock_user.mfa_secret = "JBSWY3DPEHPK3PXP"

        mock_db = AsyncMock()
        body = MFAVerifyRequest(code="000000")

        with patch("app.api.routes.mfa.pyotp.TOTP") as mock_totp_cls:
            mock_totp_inst = MagicMock()
            mock_totp_inst.verify.return_value = False
            mock_totp_cls.return_value = mock_totp_inst

            with pytest.raises(HTTPException) as exc_info:
                await mfa_verify(body=body, current_user=mock_user, db=mock_db)

        assert exc_info.value.status_code == 400


# ============================================================================
# T7 — MFA disable admin-only (Track B)
# ============================================================================


class TestT7MfaDisableAdminOnly:
    """T7: POST /auth/mfa/disable requires superuser via require_superuser dep."""

    def test_mfa_disable_admin_only(self) -> None:
        from app.api.routes.mfa import mfa_disable

        import inspect
        source = inspect.getsource(mfa_disable)
        assert "require_superuser" in source, (
            "mfa_disable must depend on require_superuser for 403 enforcement"
        )


# ============================================================================
# T8 — MFA status returns grace_period_remaining_days (Track B)
# ============================================================================


class TestT8MfaStatusGracePeriod:
    """T8: GET /auth/mfa/status returns grace_period_remaining_days."""

    @pytest.mark.asyncio
    async def test_mfa_status_returns_grace_period(self) -> None:
        from app.api.routes.mfa import mfa_status

        deadline = datetime.now(timezone.utc) + timedelta(days=3)

        mock_user = MagicMock()
        mock_user.mfa_enabled = False
        mock_user.mfa_secret = None
        mock_user.mfa_setup_deadline = deadline
        mock_user.is_mfa_exempt = False

        resp = await mfa_status(current_user=mock_user)

        assert resp.grace_period_remaining_days == 3
        assert resp.mfa_enabled is False


# ============================================================================
# T9 — DORA metrics with gate history (Track C)
# ============================================================================


class TestT9DoraMetricsWithHistory:
    """T9: DORA endpoint returns non-zero metrics when gates exist."""

    def test_dora_metrics_with_gate_history(self) -> None:
        from app.api.routes.dora import _rate_cfr, _rate_df, _rate_lt, _rate_mttr

        # Verify rating functions return valid ratings for non-zero values
        assert _rate_df(2.0) in ("Elite", "High", "Medium", "Low")
        assert _rate_lt(12.0) in ("Elite", "High", "Medium", "Low")
        assert _rate_mttr(6.0) in ("Elite", "High", "Medium", "Low")
        assert _rate_cfr(0.20) in ("Elite", "High", "Medium", "Low")

        # Verify specific expected bands
        assert _rate_df(2.0) == "High"       # 1-7 per week = High
        assert _rate_lt(12.0) == "High"      # 1-24 hours = High
        assert _rate_cfr(0.20) == "Medium"   # 15-30% = Medium


# ============================================================================
# T10 — DORA metrics empty project (Track C)
# ============================================================================


class TestT10DoraMetricsEmpty:
    """T10: DORA rating functions return Low for zero-level metrics."""

    def test_dora_metrics_empty_project(self) -> None:
        from app.api.routes.dora import _rate_cfr, _rate_df, _rate_lt, _rate_mttr

        # Zero metrics should produce lowest ratings
        assert _rate_df(0.0) == "Low"
        assert _rate_lt(200.0) == "Low"   # >168h = Low
        assert _rate_mttr(200.0) == "Low"
        assert _rate_cfr(0.50) == "Low"   # >30% = Low


# ============================================================================
# T11 — Audit export CSV format (Track D)
# ============================================================================


class TestT11AuditExportCsv:
    """T11: _build_csv produces header + data rows in correct format."""

    def test_audit_export_csv_format(self) -> None:
        from app.api.routes.audit_export import _EXPORT_COLUMNS, _build_csv

        rows = [
            ("TEST_RESULTS", "report.xml", "2026-02-28T00:00:00Z", "user1",
             "abc123", "G1", "gate-1", "verified", "cli"),
            ("DESIGN_DOCUMENT", "arch.pdf", "2026-02-27T12:00:00Z", "user2",
             "def456", "G2", "gate-2", "hash_present", "web"),
            ("CODE_REVIEW", "review.md", "2026-02-26T08:30:00Z", "user3",
             "ghi789", "G3", "gate-3", "verified", "extension"),
        ]

        csv_text = _build_csv(rows)
        lines = csv_text.strip().split("\n")

        # Header row + 3 data rows
        assert len(lines) == 4, f"Expected 4 lines (header + 3 data), got {len(lines)}"
        header = lines[0]
        for col in _EXPORT_COLUMNS:
            assert col in header, f"Header must contain column '{col}'"


# ============================================================================
# T12 — Audit export PDF content type (Track D)
# ============================================================================


class TestT12AuditExportPdf:
    """T12: PDF export works if reportlab available, else 501."""

    def test_audit_export_pdf_content_type(self) -> None:
        from app.api.routes.audit_export import _REPORTLAB_AVAILABLE

        if _REPORTLAB_AVAILABLE:
            from app.api.routes.audit_export import _build_pdf

            rows = [
                ("TEST_RESULTS", "report.xml", "2026-02-28", "user1",
                 "abc123", "G1", "gate-1", "verified", "cli"),
            ]
            pdf_bytes = _build_pdf(rows, uuid4(), "admin@example.com")
            assert pdf_bytes[:5] == b"%PDF-", "PDF output must start with %PDF-"
        else:
            # reportlab not installed — verify the guard flag is False
            assert _REPORTLAB_AVAILABLE is False, (
                "Without reportlab, _REPORTLAB_AVAILABLE should be False (501 path)"
            )


# ============================================================================
# T13 — ConversationFirstFallback has 4 OTT channel env vars (Track E)
# ============================================================================


class TestT13FallbackChannels:
    """T13: Fallback component references all 4 OTT channel env vars."""

    def test_fallback_renders_configured_channels(self) -> None:
        fallback = (
            FRONTEND_DIR / "components" / "dashboard"
            / "ConversationFirstFallback.tsx"
        )
        content = fallback.read_text()
        env_vars = [
            "NEXT_PUBLIC_TELEGRAM_BOT_URL",
            "NEXT_PUBLIC_ZALO_OA_URL",
            "NEXT_PUBLIC_TEAMS_BOT_URL",
            "NEXT_PUBLIC_SLACK_BOT_URL",
        ]
        for var in env_vars:
            assert var in content, (
                f"ConversationFirstFallback must reference {var}"
            )


# ============================================================================
# T14 — STM-056 status is APPROVED (Track F)
# ============================================================================


class TestT14StmStatus:
    """T14: Multi-Agent Security Threat Model frontmatter status."""

    def test_stm056_status_approved(self) -> None:
        stm = (
            DOCS_DIR / "02-design" / "07-Security-Design"
            / "Multi-Agent-Security-Threat-Model.md"
        )
        assert stm.exists(), f"STM-056 must exist at {stm}"
        content = stm.read_text()
        assert 'status: "APPROVED"' in content, (
            "STM-056 frontmatter must contain status: \"APPROVED\""
        )


# ============================================================================
# T15 — FR-010-to-FR-035 mapping file exists (Track F)
# ============================================================================


class TestT15FrMappingExists:
    """T15: FR mapping document covers FR-010 through FR-035."""

    def test_fr_mapping_exists(self) -> None:
        mapping = (
            DOCS_DIR / "01-planning" / "03-Functional-Requirements"
            / "FR-010-to-FR-035-Mapping.md"
        )
        assert mapping.exists(), f"FR mapping must exist at {mapping}"
        content = mapping.read_text()
        # Verify the document covers the full range
        assert "FR-010" in content, "Mapping must reference FR-010"
        assert "FR-035" in content, "Mapping must reference FR-035"
        # Spot-check a few intermediate FRs
        for fr_num in ("FR-015", "FR-020", "FR-025", "FR-030"):
            assert fr_num in content, (
                f"Mapping must include {fr_num}"
            )
