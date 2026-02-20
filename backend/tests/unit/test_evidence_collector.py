"""
=========================================================================
Unit Tests - Evidence Collector (Sprint 178)
SDLC Orchestrator - Multi-Agent Team Engine

Version: 1.0.0
Date: February 2026
Status: ACTIVE - Sprint 178
Authority: CTO Approved (ADR-056, FR-041)

Purpose:
- Test agent message → GateEvidence capture (sender_type guard)
- Test SHA256 content hashing (deterministic, UTF-8)
- Test evidence_id linking (message ↔ evidence FK)
- Test identity masquerading audit (on_behalf_of in JSON description)
- Test gate_id passthrough (None for agent-only evidence)
- Test batch capture + correlation ID lookup

Zero Mock Policy: Mocked AsyncSession for unit isolation
=========================================================================
"""

import hashlib
import json
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4, UUID

from app.services.agent_team.evidence_collector import (
    EvidenceCollector,
    EvidenceCollectorError,
)


# =========================================================================
# Fixtures
# =========================================================================


@pytest.fixture
def mock_db():
    db = AsyncMock()
    db.add = MagicMock()
    db.flush = AsyncMock()
    db.execute = AsyncMock()
    return db


@pytest.fixture
def collector(mock_db):
    return EvidenceCollector(mock_db)


def _make_message(
    sender_type: str = "agent",
    content: str = "Generated code: print('hello')",
    **overrides,
) -> MagicMock:
    """Create a mock AgentMessage object."""
    msg = MagicMock()
    msg.id = overrides.pop("id", uuid4())
    msg.sender_type = sender_type
    msg.content = content
    msg.correlation_id = overrides.pop("correlation_id", uuid4())
    msg.conversation_id = overrides.pop("conversation_id", uuid4())
    msg.message_type = overrides.pop("message_type", "response")
    msg.processing_status = overrides.pop("processing_status", "pending")
    msg.evidence_id = None
    for k, v in overrides.items():
        setattr(msg, k, v)
    return msg


# =========================================================================
# TestCaptureMessage — Core evidence capture (5 tests)
# =========================================================================


class TestCaptureMessage:
    """Tests for capture_message: agent guard, SHA256, linking."""

    @pytest.mark.asyncio
    async def test_agent_message_creates_evidence(self, collector, mock_db):
        """Agent sender_type message should create a GateEvidence record."""
        msg = _make_message(sender_type="agent")

        evidence = await collector.capture_message(
            message=msg,
            agent_name="coder-alpha",
            on_behalf_of="user:alice",
        )

        assert evidence is not None
        assert evidence.evidence_type == "AGENT_OUTPUT"
        assert evidence.source == "agent"
        assert evidence.s3_bucket == "sdlc-evidence"
        mock_db.add.assert_called_once()
        mock_db.flush.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_non_agent_returns_none(self, collector, mock_db):
        """Non-agent sender_type (user, system) should return None."""
        msg = _make_message(sender_type="user")

        evidence = await collector.capture_message(
            message=msg,
            agent_name="coder-alpha",
        )

        assert evidence is None
        mock_db.add.assert_not_called()

    @pytest.mark.asyncio
    async def test_system_sender_returns_none(self, collector, mock_db):
        """System sender_type should also return None."""
        msg = _make_message(sender_type="system")

        evidence = await collector.capture_message(
            message=msg,
            agent_name="reviewer",
        )

        assert evidence is None

    @pytest.mark.asyncio
    async def test_sha256_matches_content(self, collector):
        """SHA256 hash should match independently computed hash of content."""
        content = "def hello():\n    return 'world'"
        msg = _make_message(sender_type="agent", content=content)

        evidence = await collector.capture_message(
            message=msg,
            agent_name="coder",
        )

        expected_hash = hashlib.sha256(content.encode("utf-8")).hexdigest()
        assert evidence is not None
        assert evidence.sha256_hash == expected_hash
        assert evidence.sha256_server == expected_hash

    @pytest.mark.asyncio
    async def test_evidence_id_linked_to_message(self, collector):
        """After capture, message.evidence_id should be set to evidence.id."""
        msg = _make_message(sender_type="agent")
        assert msg.evidence_id is None

        evidence = await collector.capture_message(
            message=msg,
            agent_name="coder",
        )

        assert evidence is not None
        assert msg.evidence_id == evidence.id

    @pytest.mark.asyncio
    async def test_gate_id_passthrough(self, collector):
        """gate_id should be passed through to GateEvidence record."""
        gate_id = uuid4()
        msg = _make_message(sender_type="agent")

        evidence = await collector.capture_message(
            message=msg,
            agent_name="coder",
            gate_id=gate_id,
        )

        assert evidence is not None
        assert evidence.gate_id == gate_id

    @pytest.mark.asyncio
    async def test_gate_id_none_by_default(self, collector):
        """gate_id should be None when not provided (agent-only evidence)."""
        msg = _make_message(sender_type="agent")

        evidence = await collector.capture_message(
            message=msg,
            agent_name="coder",
        )

        assert evidence is not None
        assert evidence.gate_id is None


# =========================================================================
# TestIdentityAudit — Non-Negotiable #12 (3 tests)
# =========================================================================


class TestIdentityAudit:
    """Tests for identity masquerading audit (ADR-056 Non-Negotiable #12)."""

    @pytest.mark.asyncio
    async def test_on_behalf_of_in_description(self, collector):
        """on_behalf_of should appear in the JSON evidence description."""
        msg = _make_message(sender_type="agent")

        evidence = await collector.capture_message(
            message=msg,
            agent_name="coder-alpha",
            on_behalf_of="user:bob",
        )

        assert evidence is not None
        desc = json.loads(evidence.description)
        assert desc["on_behalf_of"] == "user:bob"
        assert desc["agent_name"] == "coder-alpha"
        assert desc["message_id"] == str(msg.id)
        assert desc["correlation_id"] == str(msg.correlation_id)
        assert "captured_at" in desc

    @pytest.mark.asyncio
    async def test_missing_on_behalf_of_defaults_unknown(self, collector):
        """When on_behalf_of is None, description should record 'unknown'."""
        msg = _make_message(sender_type="agent")

        evidence = await collector.capture_message(
            message=msg,
            agent_name="reviewer",
            on_behalf_of=None,
        )

        assert evidence is not None
        desc = json.loads(evidence.description)
        assert desc["on_behalf_of"] == "unknown"

    @pytest.mark.asyncio
    async def test_trace_evidence_logged(self, collector, caplog):
        """TRACE_EVIDENCE log entry should include agent_name and on_behalf_of."""
        msg = _make_message(sender_type="agent")

        with caplog.at_level("INFO"):
            await collector.capture_message(
                message=msg,
                agent_name="coder",
                on_behalf_of="user:carol",
            )

        trace_logs = [r for r in caplog.records if "TRACE_EVIDENCE" in r.message]
        assert len(trace_logs) >= 1
        log_msg = trace_logs[0].message
        assert "coder" in log_msg
        assert "user:carol" in log_msg


# =========================================================================
# TestBatchAndLookup — Batch capture + correlation (2 tests)
# =========================================================================


class TestBatchAndLookup:
    """Tests for batch capture and correlation-based lookup."""

    @pytest.mark.asyncio
    async def test_batch_capture_returns_list(self, collector):
        """capture_batch should return evidence for all eligible messages."""
        messages = [
            _make_message(sender_type="agent", content=f"Output {i}")
            for i in range(3)
        ]
        # Add one non-agent to verify filtering
        messages.append(_make_message(sender_type="user", content="User msg"))

        results = await collector.capture_batch(
            messages,
            agent_name="coder",
            on_behalf_of="user:dave",
        )

        assert len(results) == 3  # 3 agent, 1 user skipped

    @pytest.mark.asyncio
    async def test_correlation_lookup(self, collector, mock_db):
        """get_evidence_by_correlation should query by correlation_id."""
        correlation_id = uuid4()
        mock_evidence = [MagicMock(), MagicMock()]

        mock_result = MagicMock()
        mock_scalars = MagicMock()
        mock_scalars.all.return_value = mock_evidence
        mock_result.scalars.return_value = mock_scalars
        mock_db.execute.return_value = mock_result

        results = await collector.get_evidence_by_correlation(correlation_id)

        assert len(results) == 2
        mock_db.execute.assert_awaited_once()


# =========================================================================
# TestStaticHelpers — Hash + S3 key + description (2 tests)
# =========================================================================


class TestStaticHelpers:
    """Tests for static utility methods."""

    def test_compute_content_hash_deterministic(self):
        """Same content should always produce the same SHA256 hash."""
        content = "def foo(): pass"
        hash1 = EvidenceCollector._compute_content_hash(content)
        hash2 = EvidenceCollector._compute_content_hash(content)
        assert hash1 == hash2
        assert len(hash1) == 64  # SHA256 hex digest length

    def test_build_s3_key_format(self):
        """S3 key should follow evidence/agent/{conv_id}/{msg_id}.txt format."""
        msg = _make_message(sender_type="agent")
        key = EvidenceCollector._build_s3_key(msg)
        assert key.startswith("evidence/agent/")
        assert str(msg.id) in key
        assert key.endswith(".txt")
