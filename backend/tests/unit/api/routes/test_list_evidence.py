"""
Unit Tests — GET /api/v1/evidence (list_evidence endpoint)

Sprint 186 — ADR-062 D-3: compliance_type filter
Test IDs: CT-01 to CT-05

Purpose:
  Verify that the list_evidence endpoint correctly filters GateEvidence
  records by compliance_type, gate_id, and source, and returns correct
  pagination metadata. Validate 400 responses for bad inputs.

Test Coverage: CT-01..CT-05 (compliance filter) + CT-06..CT-10 (other filters/errors)
Framework: SDLC 6.1.0 — Zero Mock Policy (real SQLAlchemy queries, mocked DB session)
"""

from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

from app.api.routes.evidence import _VALID_COMPLIANCE_TYPES, list_evidence


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_evidence(
    evidence_type: str = "SOC2_CONTROL",
    source: str = "web",
    gate_id=None,
) -> MagicMock:
    """Return a MagicMock that mimics a GateEvidence ORM record."""
    rec = MagicMock()
    rec.id = uuid4()
    rec.gate_id = gate_id or uuid4()
    rec.file_name = f"evidence-{rec.id}.txt"
    rec.file_size = 1024
    rec.file_type = "text/plain"
    rec.evidence_type = evidence_type
    rec.source = source
    rec.sha256_hash = "abc" * 21  # 63-char stub
    rec.description = f"Test evidence ({evidence_type})"
    rec.uploaded_by = uuid4()
    rec.uploaded_at = datetime(2026, 2, 20, tzinfo=timezone.utc)
    rec.created_at = datetime(2026, 2, 20, tzinfo=timezone.utc)
    rec.deleted_at = None
    rec.s3_url = f"s3://sdlc-evidence/test/{rec.id}.txt"
    return rec


def _db_with_records(records: list) -> AsyncMock:
    """Build a fake AsyncSession that returns `records` on scalars().all().

    db.execute is an AsyncMock (awaitable), but the objects it returns must be
    plain MagicMock instances so that their synchronous methods (.scalar_one(),
    .scalars().all()) resolve without triggering coroutine unwrapping errors.
    """
    db = AsyncMock()

    # count query result — scalar_one() returns int
    count_result = MagicMock()
    count_result.scalar_one.return_value = len(records)

    # data query result — scalars().all() returns list
    data_result = MagicMock()
    scalars_mock = MagicMock()
    scalars_mock.all.return_value = records
    data_result.scalars.return_value = scalars_mock

    # First await db.execute() → count_result; second → data_result
    db.execute.side_effect = [count_result, data_result]
    return db


def _make_user() -> MagicMock:
    user = MagicMock()
    user.id = uuid4()
    user.is_active = True
    return user


# ---------------------------------------------------------------------------
# CT-01: ?compliance_type=SOC2_CONTROL filters correctly
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_ct01_soc2_control_filter():
    """CT-01: ?compliance_type=SOC2_CONTROL returns only SOC2 evidence."""
    records = [
        _make_evidence("SOC2_CONTROL"),
        _make_evidence("SOC2_CONTROL"),
    ]
    db = _db_with_records(records)
    user = _make_user()

    result = await list_evidence(
        compliance_type="SOC2_CONTROL",
        gate_id=None,
        source=None,
        limit=50,
        offset=0,
        db=db,
        current_user=user,
    )

    assert result["total"] == 2
    assert len(result["items"]) == 2
    assert result["compliance_type_filter"] == "SOC2_CONTROL"
    for item in result["items"]:
        assert item["evidence_type"] == "SOC2_CONTROL"


# ---------------------------------------------------------------------------
# CT-02: ?compliance_type=HIPAA_AUDIT filters correctly
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_ct02_hipaa_audit_filter():
    """CT-02: ?compliance_type=HIPAA_AUDIT returns only HIPAA evidence."""
    records = [_make_evidence("HIPAA_AUDIT")]
    db = _db_with_records(records)
    user = _make_user()

    result = await list_evidence(
        compliance_type="HIPAA_AUDIT",
        gate_id=None,
        source=None,
        limit=50,
        offset=0,
        db=db,
        current_user=user,
    )

    assert result["total"] == 1
    assert result["compliance_type_filter"] == "HIPAA_AUDIT"
    assert result["items"][0]["evidence_type"] == "HIPAA_AUDIT"


# ---------------------------------------------------------------------------
# CT-03: ?compliance_type=NIST_AI_RMF filters correctly
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_ct03_nist_ai_rmf_filter():
    """CT-03: ?compliance_type=NIST_AI_RMF returns NIST evidence."""
    records = [_make_evidence("NIST_AI_RMF"), _make_evidence("NIST_AI_RMF")]
    db = _db_with_records(records)
    user = _make_user()

    result = await list_evidence(
        compliance_type="NIST_AI_RMF",
        gate_id=None,
        source=None,
        limit=50,
        offset=0,
        db=db,
        current_user=user,
    )

    assert result["compliance_type_filter"] == "NIST_AI_RMF"
    assert result["total"] == 2


# ---------------------------------------------------------------------------
# CT-04: ?compliance_type=ISO27001 filters correctly
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_ct04_iso27001_filter():
    """CT-04: ?compliance_type=ISO27001 returns ISO 27001 evidence."""
    records = [_make_evidence("ISO27001")]
    db = _db_with_records(records)
    user = _make_user()

    result = await list_evidence(
        compliance_type="ISO27001",
        gate_id=None,
        source=None,
        limit=50,
        offset=0,
        db=db,
        current_user=user,
    )

    assert result["compliance_type_filter"] == "ISO27001"
    assert result["items"][0]["evidence_type"] == "ISO27001"


# ---------------------------------------------------------------------------
# CT-05: No filter returns all evidence (paginated)
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_ct05_no_filter_returns_all():
    """CT-05: No compliance_type filter returns all non-deleted evidence."""
    records = [
        _make_evidence("SOC2_CONTROL"),
        _make_evidence("HIPAA_AUDIT"),
        _make_evidence("AGENT_OUTPUT"),
        _make_evidence("TEST_RESULTS"),
    ]
    db = _db_with_records(records)
    user = _make_user()

    result = await list_evidence(
        compliance_type=None,
        gate_id=None,
        source=None,
        limit=50,
        offset=0,
        db=db,
        current_user=user,
    )

    assert result["compliance_type_filter"] is None
    assert result["total"] == 4
    assert len(result["items"]) == 4


# ---------------------------------------------------------------------------
# CT-06: Case-insensitive filter normalisation
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_ct06_case_insensitive_filter():
    """CT-06: compliance_type is normalised to uppercase before matching."""
    records = [_make_evidence("SOC2_CONTROL")]
    db = _db_with_records(records)
    user = _make_user()

    # lowercase input
    result = await list_evidence(
        compliance_type="soc2_control",
        gate_id=None,
        source=None,
        limit=50,
        offset=0,
        db=db,
        current_user=user,
    )

    assert result["compliance_type_filter"] == "SOC2_CONTROL"


# ---------------------------------------------------------------------------
# CT-07: Unknown compliance_type → 400
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_ct07_unknown_compliance_type_returns_400():
    """CT-07: An unrecognised compliance_type raises HTTP 400."""
    from fastapi import HTTPException

    db = AsyncMock()
    user = _make_user()

    with pytest.raises(HTTPException) as exc_info:
        await list_evidence(
            compliance_type="GDPR_ARTICLE",
            gate_id=None,
            source=None,
            limit=50,
            offset=0,
            db=db,
            current_user=user,
        )

    assert exc_info.value.status_code == 400
    assert "GDPR_ARTICLE" in exc_info.value.detail
    assert "Valid values" in exc_info.value.detail


# ---------------------------------------------------------------------------
# CT-08: Invalid gate_id UUID → 400
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_ct08_invalid_gate_id_returns_400():
    """CT-08: A non-UUID gate_id raises HTTP 400."""
    from fastapi import HTTPException

    db = AsyncMock()
    user = _make_user()

    with pytest.raises(HTTPException) as exc_info:
        await list_evidence(
            compliance_type=None,
            gate_id="not-a-uuid",
            source=None,
            limit=50,
            offset=0,
            db=db,
            current_user=user,
        )

    assert exc_info.value.status_code == 400
    assert "UUID" in exc_info.value.detail


# ---------------------------------------------------------------------------
# CT-09: Pagination metadata returned correctly
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_ct09_pagination_metadata():
    """CT-09: limit/offset/total are returned correctly in response."""
    records = [_make_evidence("SOC2_CONTROL")] * 10
    db = _db_with_records(records)
    user = _make_user()

    result = await list_evidence(
        compliance_type=None,
        gate_id=None,
        source=None,
        limit=10,
        offset=5,
        db=db,
        current_user=user,
    )

    assert result["limit"] == 10
    assert result["offset"] == 5
    assert result["total"] == 10


# ---------------------------------------------------------------------------
# CT-10: source filter applied correctly
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_ct10_source_filter():
    """CT-10: ?source=jira filters by source field (lowercased)."""
    records = [_make_evidence("TEST_RESULTS", source="jira")]
    db = _db_with_records(records)
    user = _make_user()

    result = await list_evidence(
        compliance_type=None,
        gate_id=None,
        source="jira",
        limit=50,
        offset=0,
        db=db,
        current_user=user,
    )

    assert result["total"] == 1
    assert result["items"][0]["source"] == "jira"


# ---------------------------------------------------------------------------
# CT-11: _VALID_COMPLIANCE_TYPES constant contains exactly ADR-062 types
# ---------------------------------------------------------------------------

def test_ct11_valid_compliance_types_set():
    """CT-11: _VALID_COMPLIANCE_TYPES matches the ADR-062 D-3 specification."""
    expected = {"SOC2_CONTROL", "HIPAA_AUDIT", "NIST_AI_RMF", "ISO27001"}
    assert _VALID_COMPLIANCE_TYPES == expected


# ---------------------------------------------------------------------------
# CT-12: Response item serialisation (no UUIDs as raw objects)
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_ct12_response_serialisation():
    """CT-12: UUIDs in response items are serialised as strings."""
    gate_uuid = uuid4()
    record = _make_evidence("SOC2_CONTROL", gate_id=gate_uuid)
    db = _db_with_records([record])
    user = _make_user()

    result = await list_evidence(
        compliance_type=None,
        gate_id=None,
        source=None,
        limit=50,
        offset=0,
        db=db,
        current_user=user,
    )

    item = result["items"][0]
    assert isinstance(item["id"], str)
    assert isinstance(item["gate_id"], str)
    assert item["gate_id"] == str(gate_uuid)
    assert isinstance(item["uploaded_by"], str)
    assert isinstance(item["uploaded_at"], str)
    assert isinstance(item["created_at"], str)
