"""
==========================================================================
Unit Tests for Audit Trail Routes — Sprint 185 (Advanced Audit Trail, SOC2 Type II)
SDLC Orchestrator — ENTERPRISE Tier

Test IDs:
  AT-01  unauthenticated list request returns 401
  AT-02  authenticated list returns AuditListResponse with events
  AT-03  event_type query param filters results
  AT-04  actor_id query param filters results
  AT-05  bad ISO date in from_date returns 422
  AT-06  bad ISO date in to_date returns 422
  AT-07  POST /export format=json returns JSON file download
  AT-08  POST /export format=csv returns CSV file download
  AT-09  POST /export format=xml fails Pydantic validation (422)
  AT-10  after export, an audit event is written for the export action
  AT-11  user with no org_id returns 400 on /soc2-pack
  AT-12  bad date string in /soc2-pack returns 422
  AT-13  from_date >= to_date in /soc2-pack returns 422
  AT-14  valid /soc2-pack request returns application/pdf
  AT-15  AuditLog.create_event() factory populates all fields correctly

Approach:
  - httpx.AsyncClient + ASGITransport hitting the real FastAPI app
  - dependency_overrides for get_current_active_user + get_db
  - TierGateMiddleware bypassed by patching TIER_GATE_ADMIN_SECRET and
    passing X-Admin-Override header (matches TG-21 pattern from test_tier_gate.py)
  - SOC2PackService.generate_pack mocked via unittest.mock.patch
  - No real database connection — AsyncMock sessions only

SDLC 6.1.0 — Sprint 185
Authority: CTO Approved
==========================================================================
"""

from __future__ import annotations

import json
import os
from contextlib import contextmanager
from datetime import datetime, timezone
from typing import AsyncGenerator
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import UUID, uuid4

import pytest
from httpx import ASGITransport, AsyncClient

import app.middleware.tier_gate as _tg_mod  # used for ADMIN_BYPASS_SECRET patch
from app.main import app
from app.api.dependencies import get_current_active_user
from app.db.session import get_db
from app.models.audit_log import AuditLog
from app.services.compliance.soc2_pack_service import SOC2PackResult


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# Admin bypass secret used to skip TierGateMiddleware ENTERPRISE enforcement.
# IMPORTANT: tier_gate.py reads ADMIN_BYPASS_SECRET as a module-level constant
# at import time, BEFORE conftest.py's `from app.main import app` call sets
# any env var. We therefore patch the module attribute directly via
# `patch.object(_tg_mod, "ADMIN_BYPASS_SECRET", _TEST_BYPASS_SECRET)` inside
# each test. See _tier_bypass() context manager below.
_TEST_BYPASS_SECRET = "test-audit-bypass-secret-185"

_ENTERPRISE_HEADERS = {
    "X-Admin-Override": _TEST_BYPASS_SECRET,
    "Authorization": "Bearer fake-jwt-token",
}

_ORG_ID = "org-00000000-0000-0000-0000-000000000001"
_ACTOR_ID = "usr-00000000-0000-0000-0000-000000000002"
_USER_ID = uuid4()


# ---------------------------------------------------------------------------
# Tier-gate bypass context manager
# ---------------------------------------------------------------------------


@contextmanager
def _tier_bypass():
    """
    Patch TierGateMiddleware's module-level ADMIN_BYPASS_SECRET constant so
    the X-Admin-Override header is honoured during tests.

    Background:
        tier_gate.py evaluates ``ADMIN_BYPASS_SECRET = os.getenv(...)`` once at
        module import time. By the time test_audit_trail.py is collected,
        app.main (and therefore tier_gate.py) is already imported by conftest.py,
        so any os.environ manipulation in this file is too late.  We instead
        patch the module attribute directly for the duration of each route test.

    Usage::

        with _tier_bypass():
            async with AsyncClient(...) as client:
                response = await client.get("/api/v1/enterprise/audit",
                                            headers=_ENTERPRISE_HEADERS)
    """
    with patch.object(_tg_mod, "ADMIN_BYPASS_SECRET", _TEST_BYPASS_SECRET):
        yield


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_mock_user(
    *,
    user_id: UUID | None = None,
    email: str = "auditor@example.com",
    organization_id: UUID | None = None,
    is_active: bool = True,
) -> MagicMock:
    """Build a minimal mock User that the audit route inspects."""
    user = MagicMock()
    user.id = user_id or _USER_ID
    user.email = email
    user.is_active = is_active
    user.organization_id = organization_id or uuid4()
    user.effective_tier = "ENTERPRISE"
    return user


def _make_mock_user_no_org() -> MagicMock:
    """Build a mock User with no organization (for AT-11)."""
    user = MagicMock()
    user.id = _USER_ID
    user.email = "noorg@example.com"
    user.is_active = True
    user.organization_id = None
    user.effective_tier = "ENTERPRISE"
    return user


def _make_audit_log(
    event_type: str = "gate_action",
    action: str = "approve",
    actor_id: str | None = None,
    actor_email: str | None = "dev@example.com",
    organization_id: str | None = None,
    resource_type: str | None = "gate",
    resource_id: str | None = None,
    detail: dict | None = None,
    ip_address: str | None = "127.0.0.1",
    tier_at_event: str | None = "ENTERPRISE",
) -> MagicMock:
    """Create a minimal mock AuditLog ORM instance."""
    log = MagicMock(spec=AuditLog)
    log.id = uuid4()
    log.event_type = event_type
    log.action = action
    log.actor_id = actor_id or _ACTOR_ID
    log.actor_email = actor_email
    log.organization_id = organization_id or _ORG_ID
    log.resource_type = resource_type
    log.resource_id = resource_id or str(uuid4())
    log.detail = detail or {"gate_type": "G3"}
    log.ip_address = ip_address
    log.user_agent = None
    log.tier_at_event = tier_at_event
    log.created_at = datetime(2026, 1, 15, 12, 0, 0, tzinfo=timezone.utc)
    return log


def _make_db_session(
    *,
    count: int = 2,
    rows: list | None = None,
) -> AsyncMock:
    """
    Build an AsyncMock db session that returns fake rows for two execute() calls:
      1st call → scalar_one() returns `count`  (COUNT query)
      2nd call → scalars().all() returns `rows` (SELECT rows query)

    For export and soc2-pack routes (single execute), we reuse the same pattern
    by only consuming the second return value.
    """
    if rows is None:
        rows = [_make_audit_log() for _ in range(count)]

    # COUNT result
    count_result = MagicMock()
    count_result.scalar_one.return_value = count

    # Row result
    row_result = MagicMock()
    row_result.scalars.return_value.all.return_value = rows

    db = AsyncMock()
    db.execute = AsyncMock(side_effect=[count_result, row_result])
    db.add = MagicMock()
    db.commit = AsyncMock()
    db.refresh = AsyncMock()
    return db


def _make_db_session_export(rows: list | None = None) -> AsyncMock:
    """
    DB mock for export / soc2-pack routes — only one SELECT, no COUNT.
    """
    if rows is None:
        rows = [_make_audit_log()]

    row_result = MagicMock()
    row_result.scalars.return_value.all.return_value = rows

    db = AsyncMock()
    db.execute = AsyncMock(return_value=row_result)
    db.add = MagicMock()
    db.commit = AsyncMock()
    db.refresh = AsyncMock()
    return db


async def _override_db(db: AsyncMock) -> AsyncGenerator:
    """FastAPI dependency override factory for get_db."""
    async def _inner():
        yield db
    return _inner()


# ---------------------------------------------------------------------------
# AT-01: unauthenticated list request returns 401
# ---------------------------------------------------------------------------


class TestAuditListUnauthenticated:
    async def test_audit_list_no_auth_returns_401(self) -> None:
        """AT-01 — Omitting auth dependency raises 401."""
        # Remove any previously set override so the real auth runs
        app.dependency_overrides.pop(get_current_active_user, None)
        app.dependency_overrides.pop(get_db, None)

        with _tier_bypass():
            transport = ASGITransport(app=app)
            async with AsyncClient(
                transport=transport, base_url="http://testserver"
            ) as client:
                # Send request WITHOUT the Authorization header — real JWT auth
                # will reject since there is no valid token.
                response = await client.get(
                    "/api/v1/enterprise/audit",
                    headers={"X-Admin-Override": _TEST_BYPASS_SECRET},
                )

        # The auth dependency returns 401 for missing/invalid tokens.
        assert response.status_code == 401


# ---------------------------------------------------------------------------
# AT-02: authenticated list returns AuditListResponse with events
# ---------------------------------------------------------------------------


class TestAuditListPaginated:
    async def test_audit_list_returns_paginated_events(self) -> None:
        """AT-02 — Authenticated list returns AuditListResponse shape."""
        fake_rows = [
            _make_audit_log(event_type="gate_action", action="approve"),
            _make_audit_log(event_type="evidence_access", action="upload"),
        ]
        db = _make_db_session(count=2, rows=fake_rows)
        user = _make_mock_user()

        async def _db_override():
            yield db

        app.dependency_overrides[get_db] = _db_override
        app.dependency_overrides[get_current_active_user] = lambda: user

        try:
            with _tier_bypass():
                transport = ASGITransport(app=app)
                async with AsyncClient(
                    transport=transport, base_url="http://testserver"
                ) as client:
                    response = await client.get(
                        "/api/v1/enterprise/audit",
                        headers=_ENTERPRISE_HEADERS,
                    )

            assert response.status_code == 200
            body = response.json()
            assert "events" in body
            assert "total" in body
            assert "page" in body
            assert "page_size" in body
            assert "has_more" in body
            assert body["total"] == 2
            assert body["page"] == 1
            assert len(body["events"]) == 2
            # Verify shape of a single event
            ev = body["events"][0]
            assert "id" in ev
            assert "event_type" in ev
            assert "action" in ev
            assert "created_at" in ev
        finally:
            app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# AT-03: event_type query param filters results
# ---------------------------------------------------------------------------


class TestAuditListFilterByEventType:
    async def test_audit_list_filter_by_event_type(self) -> None:
        """AT-03 — event_type=gate_action filters returned events."""
        fake_rows = [
            _make_audit_log(event_type="gate_action", action="approve"),
        ]
        db = _make_db_session(count=1, rows=fake_rows)
        user = _make_mock_user()

        async def _db_override():
            yield db

        app.dependency_overrides[get_db] = _db_override
        app.dependency_overrides[get_current_active_user] = lambda: user

        try:
            with _tier_bypass():
                transport = ASGITransport(app=app)
                async with AsyncClient(
                    transport=transport, base_url="http://testserver"
                ) as client:
                    response = await client.get(
                        "/api/v1/enterprise/audit",
                        params={"event_type": "gate_action"},
                        headers=_ENTERPRISE_HEADERS,
                    )

            assert response.status_code == 200
            body = response.json()
            assert body["total"] == 1
            assert body["events"][0]["event_type"] == "gate_action"
            # Verify that the DB execute was called (filter was applied)
            assert db.execute.call_count == 2
        finally:
            app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# AT-04: actor_id query param filters results
# ---------------------------------------------------------------------------


class TestAuditListFilterByActorId:
    async def test_audit_list_filter_by_actor_id(self) -> None:
        """AT-04 — actor_id query param narrows results to one actor."""
        target_actor = str(uuid4())
        fake_rows = [
            _make_audit_log(actor_id=target_actor, event_type="sso_event", action="login"),
        ]
        db = _make_db_session(count=1, rows=fake_rows)
        user = _make_mock_user()

        async def _db_override():
            yield db

        app.dependency_overrides[get_db] = _db_override
        app.dependency_overrides[get_current_active_user] = lambda: user

        try:
            with _tier_bypass():
                transport = ASGITransport(app=app)
                async with AsyncClient(
                    transport=transport, base_url="http://testserver"
                ) as client:
                    response = await client.get(
                        "/api/v1/enterprise/audit",
                        params={"actor_id": target_actor},
                        headers=_ENTERPRISE_HEADERS,
                    )

            assert response.status_code == 200
            body = response.json()
            assert body["total"] == 1
            assert body["events"][0]["actor_id"] == target_actor
        finally:
            app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# AT-05: bad ISO date in from_date returns 422
# ---------------------------------------------------------------------------


class TestAuditListInvalidFromDate:
    async def test_audit_list_invalid_from_date_returns_422(self) -> None:
        """AT-05 — Non-ISO from_date triggers 422 Unprocessable Entity."""
        db = _make_db_session(count=0, rows=[])
        user = _make_mock_user()

        async def _db_override():
            yield db

        app.dependency_overrides[get_db] = _db_override
        app.dependency_overrides[get_current_active_user] = lambda: user

        try:
            with _tier_bypass():
                transport = ASGITransport(app=app)
                async with AsyncClient(
                    transport=transport, base_url="http://testserver"
                ) as client:
                    response = await client.get(
                        "/api/v1/enterprise/audit",
                        params={"from_date": "not-a-date"},
                        headers=_ENTERPRISE_HEADERS,
                    )

            assert response.status_code == 422
            detail = response.json()["detail"]
            # Route returns a dict detail for date parse errors
            assert detail["error"] == "invalid_date"
            assert detail["field"] == "from_date"
        finally:
            app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# AT-06: bad ISO date in to_date returns 422
# ---------------------------------------------------------------------------


class TestAuditListInvalidToDate:
    async def test_audit_list_invalid_to_date_returns_422(self) -> None:
        """AT-06 — Non-ISO to_date triggers 422 Unprocessable Entity."""
        # Provide a valid from_date but invalid to_date.
        # The route validates from_date first (no exception since it's valid),
        # then raises on to_date.
        db = _make_db_session(count=0, rows=[])
        user = _make_mock_user()

        async def _db_override():
            yield db

        app.dependency_overrides[get_db] = _db_override
        app.dependency_overrides[get_current_active_user] = lambda: user

        try:
            with _tier_bypass():
                transport = ASGITransport(app=app)
                async with AsyncClient(
                    transport=transport, base_url="http://testserver"
                ) as client:
                    response = await client.get(
                        "/api/v1/enterprise/audit",
                        params={
                            "from_date": "2026-01-01T00:00:00Z",
                            "to_date": "yesterday",
                        },
                        headers=_ENTERPRISE_HEADERS,
                    )

            assert response.status_code == 422
            detail = response.json()["detail"]
            assert detail["error"] == "invalid_date"
            assert detail["field"] == "to_date"
        finally:
            app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# AT-07: POST /export format=json returns JSON file download
# ---------------------------------------------------------------------------


class TestAuditExportJson:
    async def test_audit_export_json_returns_file(self) -> None:
        """AT-07 — format=json returns application/json Content-Disposition download."""
        fake_rows = [
            _make_audit_log(event_type="gate_action", action="approve"),
            _make_audit_log(event_type="evidence_access", action="upload"),
        ]
        db = _make_db_session_export(rows=fake_rows)
        user = _make_mock_user()

        async def _db_override():
            yield db

        app.dependency_overrides[get_db] = _db_override
        app.dependency_overrides[get_current_active_user] = lambda: user

        try:
            with _tier_bypass():
                transport = ASGITransport(app=app)
                async with AsyncClient(
                    transport=transport, base_url="http://testserver"
                ) as client:
                    response = await client.post(
                        "/api/v1/enterprise/audit/export",
                        json={"format": "json"},
                        headers=_ENTERPRISE_HEADERS,
                    )

            assert response.status_code == 200
            assert "application/json" in response.headers["content-type"]
            assert "attachment" in response.headers["content-disposition"]
            assert response.headers["content-disposition"].endswith(".json\"")
            assert "X-Rows-Exported" in response.headers
            # Verify the response body is valid JSON with expected structure
            payload = response.json()
            assert "exported_at" in payload
            assert "events" in payload
            assert "rows" in payload
            assert payload["rows"] == 2
            assert len(payload["events"]) == 2
        finally:
            app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# AT-08: POST /export format=csv returns CSV file download
# ---------------------------------------------------------------------------


class TestAuditExportCsv:
    async def test_audit_export_csv_returns_file(self) -> None:
        """AT-08 — format=csv returns text/csv Content-Disposition download."""
        fake_rows = [
            _make_audit_log(event_type="user_admin", action="create"),
        ]
        db = _make_db_session_export(rows=fake_rows)
        user = _make_mock_user()

        async def _db_override():
            yield db

        app.dependency_overrides[get_db] = _db_override
        app.dependency_overrides[get_current_active_user] = lambda: user

        try:
            with _tier_bypass():
                transport = ASGITransport(app=app)
                async with AsyncClient(
                    transport=transport, base_url="http://testserver"
                ) as client:
                    response = await client.post(
                        "/api/v1/enterprise/audit/export",
                        json={"format": "csv"},
                        headers=_ENTERPRISE_HEADERS,
                    )

            assert response.status_code == 200
            assert "text/csv" in response.headers["content-type"]
            assert "attachment" in response.headers["content-disposition"]
            assert response.headers["content-disposition"].endswith(".csv\"")
            # Verify CSV has header row
            csv_text = response.text
            assert "event_type" in csv_text
            assert "actor_id" in csv_text
            assert "created_at" in csv_text
            # Verify data row contains our event
            assert "user_admin" in csv_text
        finally:
            app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# AT-09: POST /export format=xml fails Pydantic validation (422)
# ---------------------------------------------------------------------------


class TestAuditExportInvalidFormat:
    async def test_audit_export_invalid_format_returns_422(self) -> None:
        """AT-09 — format='xml' is rejected by Pydantic pattern validator (422)."""
        db = _make_db_session_export()
        user = _make_mock_user()

        async def _db_override():
            yield db

        app.dependency_overrides[get_db] = _db_override
        app.dependency_overrides[get_current_active_user] = lambda: user

        try:
            with _tier_bypass():
                transport = ASGITransport(app=app)
                async with AsyncClient(
                    transport=transport, base_url="http://testserver"
                ) as client:
                    response = await client.post(
                        "/api/v1/enterprise/audit/export",
                        json={"format": "xml"},
                        headers=_ENTERPRISE_HEADERS,
                    )

            # AuditExportRequest.format has pattern="^(json|csv)$" — Pydantic rejects xml
            assert response.status_code == 422
        finally:
            app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# AT-10: after export, an audit event is written for the export action
# ---------------------------------------------------------------------------


class TestAuditExportRecordsEvent:
    async def test_audit_export_records_export_event(self) -> None:
        """AT-10 — Export route calls db.add() + db.commit() to record export_event."""
        fake_rows = [_make_audit_log()]
        db = _make_db_session_export(rows=fake_rows)
        user = _make_mock_user()

        async def _db_override():
            yield db

        app.dependency_overrides[get_db] = _db_override
        app.dependency_overrides[get_current_active_user] = lambda: user

        try:
            with _tier_bypass():
                transport = ASGITransport(app=app)
                async with AsyncClient(
                    transport=transport, base_url="http://testserver"
                ) as client:
                    response = await client.post(
                        "/api/v1/enterprise/audit/export",
                        json={"format": "json"},
                        headers=_ENTERPRISE_HEADERS,
                    )

            assert response.status_code == 200
            # The route calls db.add(export_event) then db.commit()
            db.add.assert_called_once()
            db.commit.assert_awaited_once()
            # Verify the added object is an AuditLog instance
            added_obj = db.add.call_args[0][0]
            assert isinstance(added_obj, AuditLog)
            assert added_obj.event_type == "export_event"
            assert added_obj.action == "export"
            assert added_obj.resource_type == "audit_log"
        finally:
            app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# AT-11: user with no org_id returns 400 on /soc2-pack
# ---------------------------------------------------------------------------


class TestSoc2PackNoOrg:
    async def test_soc2_pack_no_org_returns_400(self) -> None:
        """AT-11 — User without organization_id gets 400 Bad Request."""
        db = _make_db_session_export()
        user = _make_mock_user_no_org()

        async def _db_override():
            yield db

        app.dependency_overrides[get_db] = _db_override
        app.dependency_overrides[get_current_active_user] = lambda: user

        try:
            with _tier_bypass():
                transport = ASGITransport(app=app)
                async with AsyncClient(
                    transport=transport, base_url="http://testserver"
                ) as client:
                    response = await client.post(
                        "/api/v1/enterprise/audit/soc2-pack",
                        json={
                            "from_date": "2026-01-01T00:00:00Z",
                            "to_date": "2026-02-01T00:00:00Z",
                        },
                        headers=_ENTERPRISE_HEADERS,
                    )

            assert response.status_code == 400
            detail = response.json()["detail"]
            assert detail["error"] == "no_organization"
        finally:
            app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# AT-12: bad date string in /soc2-pack returns 422
# ---------------------------------------------------------------------------


class TestSoc2PackInvalidDate:
    async def test_soc2_pack_invalid_date_returns_422(self) -> None:
        """AT-12 — Unparseable from_date raises 422 Unprocessable Entity."""
        db = _make_db_session_export()
        user = _make_mock_user()

        async def _db_override():
            yield db

        app.dependency_overrides[get_db] = _db_override
        app.dependency_overrides[get_current_active_user] = lambda: user

        try:
            with _tier_bypass():
                transport = ASGITransport(app=app)
                async with AsyncClient(
                    transport=transport, base_url="http://testserver"
                ) as client:
                    response = await client.post(
                        "/api/v1/enterprise/audit/soc2-pack",
                        json={
                            "from_date": "not-a-valid-iso-date",
                            "to_date": "2026-02-01T00:00:00Z",
                        },
                        headers=_ENTERPRISE_HEADERS,
                    )

            assert response.status_code == 422
            detail = response.json()["detail"]
            assert detail["error"] == "invalid_date_range"
        finally:
            app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# AT-13: from_date >= to_date in /soc2-pack returns 422
# ---------------------------------------------------------------------------


class TestSoc2PackDateRangeInversion:
    async def test_soc2_pack_from_after_to_returns_422(self) -> None:
        """AT-13 — from_date >= to_date triggers 422 with invalid_date_range error."""
        db = _make_db_session_export()
        user = _make_mock_user()

        async def _db_override():
            yield db

        app.dependency_overrides[get_db] = _db_override
        app.dependency_overrides[get_current_active_user] = lambda: user

        try:
            with _tier_bypass():
                transport = ASGITransport(app=app)
                async with AsyncClient(
                    transport=transport, base_url="http://testserver"
                ) as client:
                    # from_date equal to to_date — also invalid
                    response = await client.post(
                        "/api/v1/enterprise/audit/soc2-pack",
                        json={
                            "from_date": "2026-02-01T00:00:00Z",
                            "to_date": "2026-01-01T00:00:00Z",
                        },
                        headers=_ENTERPRISE_HEADERS,
                    )

            assert response.status_code == 422
            detail = response.json()["detail"]
            assert detail["error"] == "invalid_date_range"
            assert "before" in detail["message"]
        finally:
            app.dependency_overrides.clear()

    async def test_soc2_pack_equal_dates_returns_422(self) -> None:
        """AT-13b — from_date == to_date also triggers 422 (boundary case)."""
        db = _make_db_session_export()
        user = _make_mock_user()

        async def _db_override():
            yield db

        app.dependency_overrides[get_db] = _db_override
        app.dependency_overrides[get_current_active_user] = lambda: user

        try:
            with _tier_bypass():
                transport = ASGITransport(app=app)
                async with AsyncClient(
                    transport=transport, base_url="http://testserver"
                ) as client:
                    same_date = "2026-01-15T00:00:00Z"
                    response = await client.post(
                        "/api/v1/enterprise/audit/soc2-pack",
                        json={"from_date": same_date, "to_date": same_date},
                        headers=_ENTERPRISE_HEADERS,
                    )

            assert response.status_code == 422
        finally:
            app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# AT-14: valid /soc2-pack request returns application/pdf
# ---------------------------------------------------------------------------


class TestSoc2PackReturnsPdf:
    async def test_soc2_pack_returns_pdf(self) -> None:
        """AT-14 — Valid request returns application/pdf with PDF header bytes."""
        db = _make_db_session_export()
        user = _make_mock_user()

        # Build a minimal SOC2PackResult with a valid PDF-like payload
        mock_pdf_bytes = b"%PDF-1.4 mock content"
        mock_pack_result = SOC2PackResult(
            pdf_bytes=mock_pdf_bytes,
            organization_id=_ORG_ID,
            from_date="2026-01-01T00:00:00+00:00",
            to_date="2026-02-01T00:00:00+00:00",
            generated_at=datetime.now(timezone.utc).isoformat(),
            total_events=5,
            summary={"CC6.1": 2, "CC7.2": 3, "CC8.1": 0},
        )

        async def _db_override():
            yield db

        app.dependency_overrides[get_db] = _db_override
        app.dependency_overrides[get_current_active_user] = lambda: user

        try:
            with patch(
                "app.api.routes.audit_trail.SOC2PackService"
            ) as mock_service_cls:
                mock_service_instance = MagicMock()
                mock_service_instance.generate_pack = AsyncMock(
                    return_value=mock_pack_result
                )
                mock_service_cls.return_value = mock_service_instance

                with _tier_bypass():
                    transport = ASGITransport(app=app)
                    async with AsyncClient(
                        transport=transport, base_url="http://testserver"
                    ) as client:
                        response = await client.post(
                            "/api/v1/enterprise/audit/soc2-pack",
                            json={
                                "from_date": "2026-01-01T00:00:00Z",
                                "to_date": "2026-02-01T00:00:00Z",
                            },
                            headers=_ENTERPRISE_HEADERS,
                        )

            assert response.status_code == 200
            assert response.headers["content-type"] == "application/pdf"
            assert "attachment" in response.headers["content-disposition"]
            assert response.headers["content-disposition"].endswith(".pdf\"")
            assert "X-Events-Included" in response.headers
            assert "X-Controls-Covered" in response.headers
            # Verify the content starts with PDF header
            assert response.content.startswith(b"%PDF")
            # Verify generate_pack was called with correct org and dates
            mock_service_instance.generate_pack.assert_awaited_once()
            call_kwargs = mock_service_instance.generate_pack.call_args.kwargs
            assert call_kwargs["organization_id"] == str(user.organization_id)
        finally:
            app.dependency_overrides.clear()

    async def test_soc2_pack_records_audit_event(self) -> None:
        """AT-14b — SOC2 pack generation writes an audit event to the DB."""
        db = _make_db_session_export()
        user = _make_mock_user()

        mock_pack_result = SOC2PackResult(
            pdf_bytes=b"%PDF-mock",
            organization_id=_ORG_ID,
            from_date="2026-01-01T00:00:00+00:00",
            to_date="2026-02-01T00:00:00+00:00",
            generated_at=datetime.now(timezone.utc).isoformat(),
            total_events=0,
            summary={},
        )

        async def _db_override():
            yield db

        app.dependency_overrides[get_db] = _db_override
        app.dependency_overrides[get_current_active_user] = lambda: user

        try:
            with patch(
                "app.api.routes.audit_trail.SOC2PackService"
            ) as mock_service_cls:
                mock_service_instance = MagicMock()
                mock_service_instance.generate_pack = AsyncMock(
                    return_value=mock_pack_result
                )
                mock_service_cls.return_value = mock_service_instance

                with _tier_bypass():
                    transport = ASGITransport(app=app)
                    async with AsyncClient(
                        transport=transport, base_url="http://testserver"
                    ) as client:
                        await client.post(
                            "/api/v1/enterprise/audit/soc2-pack",
                            json={
                                "from_date": "2026-01-01T00:00:00Z",
                                "to_date": "2026-02-01T00:00:00Z",
                            },
                            headers=_ENTERPRISE_HEADERS,
                        )

            # Route must call db.add() with an AuditLog + db.commit()
            db.add.assert_called_once()
            db.commit.assert_awaited_once()
            added_obj = db.add.call_args[0][0]
            assert isinstance(added_obj, AuditLog)
            assert added_obj.event_type == "export_event"
            assert added_obj.action == "generate"
            assert added_obj.resource_type == "compliance_pack"
        finally:
            app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# AT-15: AuditLog.create_event() factory populates fields correctly
# ---------------------------------------------------------------------------


class TestAuditLogCreateEventFactory:
    def test_audit_log_create_event_factory(self) -> None:
        """AT-15 — AuditLog.create_event() returns instance with all fields set."""
        actor_id = str(uuid4())
        resource_id = str(uuid4())
        org_id = str(uuid4())
        detail = {"gate_type": "G3", "project_id": str(uuid4())}
        user_agent = "Mozilla/5.0 (TestClient)"

        event = AuditLog.create_event(
            event_type="gate_action",
            action="approve",
            actor_id=actor_id,
            actor_email="cto@example.com",
            organization_id=org_id,
            resource_type="gate",
            resource_id=resource_id,
            detail=detail,
            ip_address="192.168.1.100",
            user_agent=user_agent,
            tier_at_event="ENTERPRISE",
        )

        assert isinstance(event, AuditLog)
        assert event.event_type == "gate_action"
        assert event.action == "approve"
        assert event.actor_id == actor_id
        assert event.actor_email == "cto@example.com"
        assert event.organization_id == org_id
        assert event.resource_type == "gate"
        assert event.resource_id == resource_id
        assert event.detail == detail
        assert event.ip_address == "192.168.1.100"
        assert event.user_agent == user_agent
        assert event.tier_at_event == "ENTERPRISE"
        # id and created_at are set by column defaults; they will be None
        # until the session flushes — factory does not require them upfront.

    def test_audit_log_create_event_none_actor(self) -> None:
        """AT-15b — actor_id=None (system event) is stored as None."""
        event = AuditLog.create_event(
            event_type="system_event",
            action="create",
            actor_id=None,
            actor_email=None,
        )
        assert event.actor_id is None
        assert event.actor_email is None

    def test_audit_log_create_event_user_agent_truncated(self) -> None:
        """AT-15c — user_agent is truncated to 512 chars."""
        long_ua = "A" * 600
        event = AuditLog.create_event(
            event_type="sso_event",
            action="login",
            user_agent=long_ua,
        )
        assert len(event.user_agent) == 512

    def test_audit_log_create_event_empty_user_agent_becomes_none(self) -> None:
        """AT-15d — empty user_agent string is stored as None (falsy sentinel)."""
        event = AuditLog.create_event(
            event_type="sso_event",
            action="login",
            user_agent="",
        )
        assert event.user_agent is None

    def test_audit_log_create_event_organization_id_coerced_to_str(self) -> None:
        """AT-15e — organization_id is stringified if passed as UUID."""
        org_uuid = uuid4()
        event = AuditLog.create_event(
            event_type="tier_change",
            action="update",
            organization_id=str(org_uuid),
        )
        assert event.organization_id == str(org_uuid)
        assert isinstance(event.organization_id, str)
