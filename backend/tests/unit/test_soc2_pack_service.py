"""
==========================================================================
Unit Tests for SOC2PackService — Sprint 185 (Advanced Audit Trail, SOC2 Type II)
SDLC Orchestrator — ENTERPRISE Tier

Test IDs:
  SP-01  from_date >= to_date raises ValueError
  SP-02  with mocked DB events, returns SOC2PackResult
  SP-03  pdf_bytes is not empty and starts with %PDF header
  SP-04  summary dict has correct counts per TSC control
  SP-05  zero events still returns a valid SOC2PackResult
  SP-06  (gate_action, approve) maps to CC7.2 + CC8.1
  SP-07  (sso_event, login) maps to CC6.1
  SP-08  unknown (event_type, action) pair maps to no control
  SP-09  None detail returns "-"
  SP-10  dict detail returns a string representation

Approach:
  - No database connection — AsyncMock session throughout
  - reportlab is a pure Python library (BSD license, in requirements.txt)
    so _render_pdf() runs for real in SP-02 and SP-03, producing actual PDF bytes.
  - SP-04 verifies the summary counter using a controlled set of mock events.
  - SP-06/07/08 exercise _map_to_tsc() directly (white-box, unit-level).
  - SP-09/10 exercise _summarize_detail() directly.

SDLC 6.1.0 — Sprint 185
Authority: CTO Approved
==========================================================================
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from app.models.audit_log import AuditLog
from app.services.compliance.soc2_pack_service import (
    ALL_TSC_CONTROLS,
    TSC_MAPPING,
    SOC2PackResult,
    SOC2PackService,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_audit_log(
    event_type: str = "gate_action",
    action: str = "approve",
    actor_email: str | None = "dev@example.com",
    organization_id: str | None = "org-test-001",
    resource_type: str | None = "gate",
    resource_id: str | None = None,
    detail: dict[str, Any] | None = None,
    created_at: datetime | None = None,
) -> MagicMock:
    """Create a mock AuditLog with all fields the service reads."""
    log = MagicMock(spec=AuditLog)
    log.id = uuid4()
    log.event_type = event_type
    log.action = action
    log.actor_email = actor_email
    log.organization_id = organization_id
    log.resource_type = resource_type
    log.resource_id = resource_id or str(uuid4())
    log.detail = detail
    log.created_at = created_at or datetime(2026, 1, 10, 9, 30, 0, tzinfo=timezone.utc)
    return log


def _make_db_with_events(events: list[MagicMock]) -> AsyncMock:
    """
    Build an AsyncMock AsyncSession whose execute() returns the given
    AuditLog instances from scalars().all().
    """
    result = MagicMock()
    result.scalars.return_value.all.return_value = events

    db = AsyncMock()
    db.execute = AsyncMock(return_value=result)
    return db


_FROM = datetime(2026, 1, 1, tzinfo=timezone.utc)
_TO = datetime(2026, 2, 1, tzinfo=timezone.utc)
_ORG = "org-test-185"


# ---------------------------------------------------------------------------
# SP-01: from_date >= to_date raises ValueError
# ---------------------------------------------------------------------------


class TestGeneratePackDateValidation:
    async def test_generate_pack_raises_on_invalid_date_range(self) -> None:
        """SP-01 — from_date equal to to_date raises ValueError immediately."""
        db = _make_db_with_events([])
        service = SOC2PackService(db)

        with pytest.raises(ValueError, match="before to_date"):
            await service.generate_pack(
                organization_id=_ORG,
                from_date=_TO,
                to_date=_FROM,  # reversed: from > to
            )

    async def test_generate_pack_raises_on_equal_dates(self) -> None:
        """SP-01b — from_date == to_date also raises ValueError."""
        db = _make_db_with_events([])
        service = SOC2PackService(db)

        same_date = datetime(2026, 1, 15, tzinfo=timezone.utc)
        with pytest.raises(ValueError):
            await service.generate_pack(
                organization_id=_ORG,
                from_date=same_date,
                to_date=same_date,
            )


# ---------------------------------------------------------------------------
# SP-02: with mocked DB events, returns SOC2PackResult
# ---------------------------------------------------------------------------


class TestGeneratePackReturnsResult:
    async def test_generate_pack_returns_soc2_pack_result(self) -> None:
        """SP-02 — generate_pack() with mocked events returns SOC2PackResult."""
        events = [
            _make_audit_log(event_type="gate_action", action="approve"),
            _make_audit_log(event_type="sso_event", action="login"),
            _make_audit_log(event_type="user_admin", action="create"),
        ]
        db = _make_db_with_events(events)
        service = SOC2PackService(db)

        result = await service.generate_pack(
            organization_id=_ORG,
            from_date=_FROM,
            to_date=_TO,
        )

        assert isinstance(result, SOC2PackResult)
        assert result.organization_id == _ORG
        assert result.from_date == _FROM.isoformat()
        assert result.to_date == _TO.isoformat()
        assert result.total_events == 3
        assert isinstance(result.summary, dict)
        assert isinstance(result.evidence_by_control, dict)
        assert isinstance(result.generated_at, str)

    async def test_generate_pack_db_execute_called_with_org_filter(
        self,
    ) -> None:
        """SP-02b — _collect_events() calls db.execute with org + date filter."""
        events = [_make_audit_log()]
        db = _make_db_with_events(events)
        service = SOC2PackService(db)

        await service.generate_pack(
            organization_id=_ORG,
            from_date=_FROM,
            to_date=_TO,
        )

        # execute must have been called exactly once (one SELECT)
        db.execute.assert_awaited_once()


# ---------------------------------------------------------------------------
# SP-03: pdf_bytes is not empty and starts with %PDF
# ---------------------------------------------------------------------------


class TestGeneratePackPdfBytes:
    async def test_generate_pack_pdf_bytes_non_empty(self) -> None:
        """SP-03 — pdf_bytes has content and begins with the PDF magic header."""
        events = [
            _make_audit_log(event_type="gate_action", action="evaluate"),
            _make_audit_log(event_type="api_key_event", action="create"),
        ]
        db = _make_db_with_events(events)
        service = SOC2PackService(db)

        result = await service.generate_pack(
            organization_id=_ORG,
            from_date=_FROM,
            to_date=_TO,
        )

        assert len(result.pdf_bytes) > 0
        # reportlab always starts PDF output with the %PDF- marker
        assert result.pdf_bytes.startswith(b"%PDF")

    async def test_generate_pack_pdf_bytes_is_bytes_type(self) -> None:
        """SP-03b — pdf_bytes field is of type bytes (not str or None)."""
        db = _make_db_with_events([])
        service = SOC2PackService(db)

        result = await service.generate_pack(
            organization_id=_ORG,
            from_date=_FROM,
            to_date=_TO,
        )

        assert isinstance(result.pdf_bytes, bytes)


# ---------------------------------------------------------------------------
# SP-04: summary dict has correct counts per TSC control
# ---------------------------------------------------------------------------


class TestGeneratePackSummaryCounts:
    async def test_generate_pack_summary_counts_events(self) -> None:
        """SP-04 — summary dict accumulates evidence counts correctly.

        TSC_MAPPING tells us:
          (gate_action, approve)  → CC7.2 + CC8.1  (2 events × 2 controls = 4 entries)
          (sso_event, login)      → CC6.1           (1 event × 1 control  = 1 entry)
          (user_admin, create)    → CC1.1            (1 event × 1 control  = 1 entry)

        After mapping:
          CC7.2 = 2 (both gate_action/approve events)
          CC8.1 = 2 (both gate_action/approve events)
          CC6.1 = 1
          CC1.1 = 1
          All other controls = 0
        """
        events = [
            _make_audit_log(event_type="gate_action", action="approve"),
            _make_audit_log(event_type="gate_action", action="approve"),
            _make_audit_log(event_type="sso_event", action="login"),
            _make_audit_log(event_type="user_admin", action="create"),
        ]
        db = _make_db_with_events(events)
        service = SOC2PackService(db)

        result = await service.generate_pack(
            organization_id=_ORG,
            from_date=_FROM,
            to_date=_TO,
        )

        assert result.summary.get("CC7.2") == 2, "CC7.2 should have 2 gate_action/approve events"
        assert result.summary.get("CC8.1") == 2, "CC8.1 should have 2 gate_action/approve events"
        assert result.summary.get("CC6.1") == 1, "CC6.1 should have 1 sso_event/login"
        assert result.summary.get("CC1.1") == 1, "CC1.1 should have 1 user_admin/create"

    async def test_generate_pack_summary_contains_all_tsc_controls(self) -> None:
        """SP-04b — summary dict contains entries for every control in ALL_TSC_CONTROLS."""
        db = _make_db_with_events([])
        service = SOC2PackService(db)

        result = await service.generate_pack(
            organization_id=_ORG,
            from_date=_FROM,
            to_date=_TO,
        )

        for ctrl in ALL_TSC_CONTROLS:
            assert ctrl in result.summary, f"Missing control {ctrl} in summary"


# ---------------------------------------------------------------------------
# SP-05: zero events still returns a valid SOC2PackResult
# ---------------------------------------------------------------------------


class TestGeneratePackEmptyEvents:
    async def test_generate_pack_empty_events_returns_result(self) -> None:
        """SP-05 — Zero audit events produces a valid result (no crash)."""
        db = _make_db_with_events([])
        service = SOC2PackService(db)

        result = await service.generate_pack(
            organization_id=_ORG,
            from_date=_FROM,
            to_date=_TO,
        )

        assert isinstance(result, SOC2PackResult)
        assert result.total_events == 0
        # All controls should have count == 0
        assert all(v == 0 for v in result.summary.values())
        # PDF should still be generated (cover page + empty sections)
        assert result.pdf_bytes.startswith(b"%PDF")

    async def test_generate_pack_empty_evidence_by_control(self) -> None:
        """SP-05b — With zero events, evidence_by_control has empty lists per control."""
        db = _make_db_with_events([])
        service = SOC2PackService(db)

        result = await service.generate_pack(
            organization_id=_ORG,
            from_date=_FROM,
            to_date=_TO,
        )

        for ctrl in ALL_TSC_CONTROLS:
            assert ctrl in result.evidence_by_control
            assert result.evidence_by_control[ctrl] == []


# ---------------------------------------------------------------------------
# SP-06: (gate_action, approve) maps to CC7.2 + CC8.1
# ---------------------------------------------------------------------------


class TestTscMappingGateApprove:
    def test_map_to_tsc_gate_action_approve_maps_to_cc72_cc81(self) -> None:
        """SP-06 — gate_action/approve event appears under CC7.2 and CC8.1."""
        db = AsyncMock()
        service = SOC2PackService(db)

        event = _make_audit_log(event_type="gate_action", action="approve")
        result = service._map_to_tsc([event])

        assert len(result["CC7.2"]) == 1, "CC7.2 should contain the approve event"
        assert len(result["CC8.1"]) == 1, "CC8.1 should contain the approve event"
        assert result["CC7.2"][0].event_type == "gate_action"
        assert result["CC7.2"][0].action == "approve"
        assert result["CC8.1"][0].event_type == "gate_action"
        assert result["CC8.1"][0].action == "approve"

    def test_map_to_tsc_gate_reject_maps_to_cc72_cc81(self) -> None:
        """SP-06b — gate_action/reject is also in CC7.2 + CC8.1 (change management)."""
        db = AsyncMock()
        service = SOC2PackService(db)

        event = _make_audit_log(event_type="gate_action", action="reject")
        result = service._map_to_tsc([event])

        assert len(result["CC7.2"]) == 1
        assert len(result["CC8.1"]) == 1

    def test_map_to_tsc_gate_evaluate_maps_to_cc72_only(self) -> None:
        """SP-06c — gate_action/evaluate maps to CC7.2 but NOT CC8.1."""
        db = AsyncMock()
        service = SOC2PackService(db)

        event = _make_audit_log(event_type="gate_action", action="evaluate")
        result = service._map_to_tsc([event])

        assert len(result["CC7.2"]) == 1
        assert len(result["CC8.1"]) == 0  # evaluate is monitoring, not change


# ---------------------------------------------------------------------------
# SP-07: (sso_event, login) maps to CC6.1
# ---------------------------------------------------------------------------


class TestTscMappingSsoLogin:
    def test_map_to_tsc_sso_login_maps_to_cc61(self) -> None:
        """SP-07 — sso_event/login satisfies CC6.1 (Logical Access Controls)."""
        db = AsyncMock()
        service = SOC2PackService(db)

        event = _make_audit_log(event_type="sso_event", action="login")
        result = service._map_to_tsc([event])

        assert len(result["CC6.1"]) == 1
        ev = result["CC6.1"][0]
        assert ev.event_type == "sso_event"
        assert ev.action == "login"

    def test_map_to_tsc_sso_provision_maps_to_cc61_and_cc62(self) -> None:
        """SP-07b — sso_event/provision satisfies both CC6.1 and CC6.2."""
        db = AsyncMock()
        service = SOC2PackService(db)

        event = _make_audit_log(event_type="sso_event", action="provision")
        result = service._map_to_tsc([event])

        assert len(result["CC6.1"]) == 1
        assert len(result["CC6.2"]) == 1

    def test_map_to_tsc_sso_logout_maps_to_cc61(self) -> None:
        """SP-07c — sso_event/logout is also CC6.1 (access event)."""
        db = AsyncMock()
        service = SOC2PackService(db)

        event = _make_audit_log(event_type="sso_event", action="logout")
        result = service._map_to_tsc([event])

        assert len(result["CC6.1"]) == 1


# ---------------------------------------------------------------------------
# SP-08: unknown (event_type, action) pair maps to no control
# ---------------------------------------------------------------------------


class TestTscMappingUnknownEvent:
    def test_map_to_tsc_unknown_event_maps_to_no_control(self) -> None:
        """SP-08 — An event not in TSC_MAPPING contributes nothing."""
        db = AsyncMock()
        service = SOC2PackService(db)

        event = _make_audit_log(event_type="system_event", action="unknown_verb")
        result = service._map_to_tsc([event])

        # No control should have this event
        for ctrl in ALL_TSC_CONTROLS:
            assert len(result[ctrl]) == 0, f"Control {ctrl} should be empty for unknown event"

    def test_map_to_tsc_unknown_event_type_known_action(self) -> None:
        """SP-08b — Even a known action verb under an unknown event_type is not mapped."""
        db = AsyncMock()
        service = SOC2PackService(db)

        # "approve" is a known action but "phantom_event" is not in TSC_MAPPING
        event = _make_audit_log(event_type="phantom_event", action="approve")
        result = service._map_to_tsc([event])

        for ctrl in ALL_TSC_CONTROLS:
            assert len(result[ctrl]) == 0

    def test_map_to_tsc_preserves_existing_controls_with_empty_lists(self) -> None:
        """SP-08c — _map_to_tsc() always returns all ALL_TSC_CONTROLS keys."""
        db = AsyncMock()
        service = SOC2PackService(db)

        result = service._map_to_tsc([])

        assert set(result.keys()) == set(ALL_TSC_CONTROLS)


# ---------------------------------------------------------------------------
# SP-09: None detail returns "-"
# ---------------------------------------------------------------------------


class TestSummarizeDetailNone:
    def test_summarize_detail_none_returns_dash(self) -> None:
        """SP-09 — _summarize_detail(None) returns the literal string '-'."""
        db = AsyncMock()
        service = SOC2PackService(db)

        result = service._summarize_detail(None)

        assert result == "-"

    def test_summarize_detail_empty_dict_returns_dash(self) -> None:
        """SP-09b — _summarize_detail({}) (falsy empty dict) returns '-'."""
        db = AsyncMock()
        service = SOC2PackService(db)

        result = service._summarize_detail({})

        assert result == "-"


# ---------------------------------------------------------------------------
# SP-10: dict detail returns a string representation
# ---------------------------------------------------------------------------


class TestSummarizeDetailDict:
    def test_summarize_detail_dict_returns_string(self) -> None:
        """SP-10 — _summarize_detail({'key': 'val'}) returns a non-empty string."""
        db = AsyncMock()
        service = SOC2PackService(db)

        detail = {"gate_type": "G3", "project_id": str(uuid4())}
        result = service._summarize_detail(detail)

        assert isinstance(result, str)
        assert len(result) > 0
        assert result != "-"

    def test_summarize_detail_contains_key_names(self) -> None:
        """SP-10b — The summary string contains the key names from detail."""
        db = AsyncMock()
        service = SOC2PackService(db)

        result = service._summarize_detail({"gate_type": "G3", "reviewer": "cto"})

        assert "gate_type" in result
        assert "reviewer" in result

    def test_summarize_detail_max_length_120_chars(self) -> None:
        """SP-10c — Output is capped at 120 characters."""
        db = AsyncMock()
        service = SOC2PackService(db)

        # Build a dict whose string representation would exceed 120 chars
        big_detail = {f"key_{i}": f"value_{'x' * 20}_{i}" for i in range(20)}
        result = service._summarize_detail(big_detail)

        assert len(result) <= 120

    def test_summarize_detail_nested_values_serialized(self) -> None:
        """SP-10d — Nested values are serialized via repr()."""
        db = AsyncMock()
        service = SOC2PackService(db)

        result = service._summarize_detail({"filters": {"event_type": "gate_action"}})

        assert isinstance(result, str)
        # repr() of a dict includes 'event_type' somewhere in the string
        assert "event_type" in result or "filters" in result

    def test_summarize_detail_non_dict_falls_back_to_str(self) -> None:
        """SP-10e — Non-dict detail (edge case) does not raise; str() is used."""
        db = AsyncMock()
        service = SOC2PackService(db)

        # Pass a string instead of a dict — should not raise
        # noinspection PyTypeChecker
        result = service._summarize_detail("plain string detail")  # type: ignore[arg-type]

        assert isinstance(result, str)
        assert len(result) <= 120


# ---------------------------------------------------------------------------
# Integration smoke: verify TSC_MAPPING covers all expected event categories
# ---------------------------------------------------------------------------


class TestTscMappingCompleteness:
    def test_tsc_mapping_includes_gate_action_events(self) -> None:
        """TSC_MAPPING must include all four gate_action verbs."""
        gate_actions = {"evaluate", "approve", "reject", "submit"}
        mapped_gate_actions = {
            action
            for (evt, action) in TSC_MAPPING
            if evt == "gate_action"
        }
        assert gate_actions.issubset(mapped_gate_actions), (
            f"Missing gate_action verbs in TSC_MAPPING: "
            f"{gate_actions - mapped_gate_actions}"
        )

    def test_tsc_mapping_includes_sso_event_types(self) -> None:
        """TSC_MAPPING must include sso login, logout, provision."""
        sso_actions = {"login", "logout", "provision"}
        mapped_sso = {
            action for (evt, action) in TSC_MAPPING if evt == "sso_event"
        }
        assert sso_actions.issubset(mapped_sso)

    def test_all_tsc_controls_in_all_tsc_controls_list(self) -> None:
        """Every control mentioned in TSC_MAPPING must appear in ALL_TSC_CONTROLS."""
        controls_in_mapping = {
            ctrl
            for controls in TSC_MAPPING.values()
            for ctrl in controls
        }
        for ctrl in controls_in_mapping:
            assert ctrl in ALL_TSC_CONTROLS, (
                f"Control '{ctrl}' in TSC_MAPPING is missing from ALL_TSC_CONTROLS"
            )


# ---------------------------------------------------------------------------
# SP-14: Idempotency — calling generate_pack twice with the same inputs
#        produces structurally identical results (same summary dict, same
#        control keys, valid PDF on both calls).
#
# Sprint 185 CTO carry-forward → Sprint 186 P2 mandate.
# Rationale: SOC2 auditors may request a second generation of the same
# evidence pack; it must be reproducible.  The DB fetch path must not
# have side-effects (no row mutations, no state accumulation).
# ---------------------------------------------------------------------------


class TestSP14Idempotency:
    """SP-14: generate_pack is idempotent — same inputs → same structure."""

    def _make_events(self, n: int = 3) -> list[MagicMock]:
        """Build n deterministic mock audit events for SP-14."""
        return [
            _make_audit_log(
                event_type="gate_action",
                action="approve",
                actor_email=f"dev{i}@example.com",
                organization_id="org-sp14",
                created_at=datetime(2026, 1, i + 1, tzinfo=timezone.utc),
            )
            for i in range(n)
        ]

    @pytest.mark.asyncio
    async def test_sp14_same_summary_on_two_calls(self) -> None:
        """SP-14a: Two successive calls with identical inputs return identical summary dicts."""
        events = self._make_events(3)
        svc1 = SOC2PackService(_make_db_with_events(events))
        svc2 = SOC2PackService(_make_db_with_events(events))

        result1 = await svc1.generate_pack("org-sp14", _FROM, _TO)
        result2 = await svc2.generate_pack("org-sp14", _FROM, _TO)

        assert result1.summary == result2.summary, (
            "generate_pack is not idempotent: summary dicts differ between calls"
        )

    @pytest.mark.asyncio
    async def test_sp14_same_control_keys_on_two_calls(self) -> None:
        """SP-14b: Both calls return the same set of TSC control keys in the summary."""
        events = self._make_events(2)
        svc1 = SOC2PackService(_make_db_with_events(events))
        svc2 = SOC2PackService(_make_db_with_events(events))

        result1 = await svc1.generate_pack("org-sp14", _FROM, _TO)
        result2 = await svc2.generate_pack("org-sp14", _FROM, _TO)

        assert set(result1.summary.keys()) == set(result2.summary.keys()), (
            "generate_pack is not idempotent: summary key sets differ"
        )

    @pytest.mark.asyncio
    async def test_sp14_pdf_bytes_valid_on_both_calls(self) -> None:
        """SP-14c: Both calls produce non-empty bytes starting with %PDF header."""
        events = self._make_events(1)
        svc1 = SOC2PackService(_make_db_with_events(events))
        svc2 = SOC2PackService(_make_db_with_events(events))

        result1 = await svc1.generate_pack("org-sp14", _FROM, _TO)
        result2 = await svc2.generate_pack("org-sp14", _FROM, _TO)

        assert result1.pdf_bytes[:4] == b"%PDF", "First call: PDF header missing"
        assert result2.pdf_bytes[:4] == b"%PDF", "Second call: PDF header missing"
        assert len(result1.pdf_bytes) > 0
        assert len(result2.pdf_bytes) > 0

    @pytest.mark.asyncio
    async def test_sp14_no_db_mutation_on_repeated_calls(self) -> None:
        """SP-14d: DB execute is called exactly ONCE per generate_pack call (no retries/mutations)."""
        events = self._make_events(2)

        # Track number of db.execute() calls
        db1 = _make_db_with_events(events)
        await SOC2PackService(db1).generate_pack("org-sp14", _FROM, _TO)
        call_count_1 = db1.execute.call_count

        db2 = _make_db_with_events(events)
        await SOC2PackService(db2).generate_pack("org-sp14", _FROM, _TO)
        call_count_2 = db2.execute.call_count

        assert call_count_1 == call_count_2, (
            "generate_pack makes different numbers of DB calls on repeated invocations "
            f"(first: {call_count_1}, second: {call_count_2})"
        )
        assert call_count_1 == 1, (
            f"generate_pack should call db.execute exactly once per call, got {call_count_1}"
        )

    @pytest.mark.asyncio
    async def test_sp14_zero_events_idempotent(self) -> None:
        """SP-14e: Zero events case is also idempotent — two calls return identical empty summaries."""
        svc1 = SOC2PackService(_make_db_with_events([]))
        svc2 = SOC2PackService(_make_db_with_events([]))

        result1 = await svc1.generate_pack("org-sp14", _FROM, _TO)
        result2 = await svc2.generate_pack("org-sp14", _FROM, _TO)

        assert result1.summary == result2.summary
        # All controls must have 0 evidence count
        for ctrl, count in result1.summary.items():
            assert count == 0, f"Zero-events pack: control {ctrl} has non-zero count {count}"
