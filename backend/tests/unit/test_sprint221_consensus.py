"""Sprint 221 — P2 Group Consensus Tests.

Tests for ConsensusService, ConsensusSession/ConsensusVote models,
quorum logic, race condition protection, timeout, and context injection.

INVARIANT: Consensus is advisory — CANNOT bypass EP-07 gates.

References: ADR-070, Sprint 221 Plan, CTO F3 (@vote syntax).
"""

import math
import uuid
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.services.agent_team.consensus_service import (
    ConsensusService,
    QuorumResult,
)
from app.models.consensus_session import (
    ConsensusSession,
    ConsensusVote,
    QUORUM_TYPES,
    SESSION_STATUSES,
    VOTE_CHOICES,
)

# ── Helpers ───────────────────────────────────────────────────────────────────

def _uuid():
    return uuid.uuid4()


def _make_session(
    session_id=None,
    conversation_id=None,
    created_by=None,
    topic="Should we deploy?",
    quorum_type="majority",
    required_voters=None,
    timeout_seconds=300,
    threshold_pct=0.67,
    status="open",
    result=None,
    decided_by_vote_id=None,
    created_at=None,
    closed_at=None,
    votes=None,
):
    s = MagicMock(spec=ConsensusSession)
    s.id = session_id or _uuid()
    s.conversation_id = conversation_id or _uuid()
    s.created_by = created_by or _uuid()
    s.topic = topic
    s.quorum_type = quorum_type
    s.required_voters = required_voters or []
    s.timeout_seconds = timeout_seconds
    s.threshold_pct = threshold_pct
    s.status = status
    s.result = result
    s.decided_by_vote_id = decided_by_vote_id
    s.created_at = created_at or datetime.now(timezone.utc)
    s.closed_at = closed_at
    s.votes = votes or []
    return s


def _make_vote(
    vote_id=None,
    session_id=None,
    voter_agent_id=None,
    vote="approve",
    reasoning=None,
    created_at=None,
):
    v = MagicMock(spec=ConsensusVote)
    v.id = vote_id or _uuid()
    v.session_id = session_id or _uuid()
    v.voter_agent_id = voter_agent_id or _uuid()
    v.vote = vote
    v.reasoning = reasoning
    v.created_at = created_at or datetime.now(timezone.utc)
    return v


def _mock_db():
    db = AsyncMock()
    db.add = MagicMock()
    db.flush = AsyncMock()
    db.refresh = AsyncMock()
    db.rollback = AsyncMock()
    db.get = AsyncMock()
    db.execute = AsyncMock()
    return db


# ── S1: Model Constants & Serialization ───────────────────────────────────────

class TestS1ModelConstants:
    """Test model constants and serialization methods."""

    def test_quorum_types(self):
        assert QUORUM_TYPES == ("majority", "unanimous", "threshold")

    def test_session_statuses(self):
        assert SESSION_STATUSES == ("open", "voting", "decided", "timeout", "cancelled")

    def test_vote_choices(self):
        assert VOTE_CHOICES == ("approve", "reject", "abstain")

    def test_consensus_session_to_dict(self):
        session_id = _uuid()
        conv_id = _uuid()
        creator_id = _uuid()
        now = datetime.now(timezone.utc)

        session = ConsensusSession()
        session.id = session_id
        session.conversation_id = conv_id
        session.created_by = creator_id
        session.topic = "Deploy v2?"
        session.quorum_type = "majority"
        session.required_voters = [str(_uuid()), str(_uuid())]
        session.threshold_pct = 0.67
        session.timeout_seconds = 300
        session.status = "open"
        session.result = None
        session.decided_by_vote_id = None
        session.created_at = now
        session.closed_at = None

        d = session.to_dict()
        assert d["id"] == str(session_id)
        assert d["conversation_id"] == str(conv_id)
        assert d["topic"] == "Deploy v2?"
        assert d["quorum_type"] == "majority"
        assert d["status"] == "open"
        assert d["result"] is None
        assert d["decided_by_vote_id"] is None
        assert d["closed_at"] is None

    def test_consensus_vote_to_dict(self):
        vote_id = _uuid()
        session_id = _uuid()
        voter_id = _uuid()
        now = datetime.now(timezone.utc)

        vote = ConsensusVote()
        vote.id = vote_id
        vote.session_id = session_id
        vote.voter_agent_id = voter_id
        vote.vote = "approve"
        vote.reasoning = "LGTM"
        vote.created_at = now

        d = vote.to_dict()
        assert d["id"] == str(vote_id)
        assert d["session_id"] == str(session_id)
        assert d["voter_agent_id"] == str(voter_id)
        assert d["vote"] == "approve"
        assert d["reasoning"] == "LGTM"

    def test_session_repr(self):
        session = ConsensusSession()
        session.id = _uuid()
        session.topic = "Deploy?"
        session.status = "open"
        session.quorum_type = "majority"
        r = repr(session)
        assert "ConsensusSession" in r
        assert "Deploy?" in r


# ── S2: create_session ────────────────────────────────────────────────────────

class TestS2CreateSession:
    """Test ConsensusService.create_session()."""

    @pytest.mark.asyncio
    async def test_create_session_defaults(self):
        db = _mock_db()
        svc = ConsensusService(db)
        conv_id = _uuid()
        creator = _uuid()

        # Mock flush and refresh to populate the session
        async def mock_refresh(obj):
            obj.id = _uuid()
            obj.status = "open"

        db.refresh = mock_refresh

        session = await svc.create_session(
            conversation_id=conv_id,
            topic="Review PR #42",
            created_by=creator,
        )

        assert session.topic == "Review PR #42"
        assert session.quorum_type == "majority"
        assert session.status == "open"
        assert session.timeout_seconds == 300
        db.add.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_session_invalid_quorum_type(self):
        db = _mock_db()
        svc = ConsensusService(db)

        with pytest.raises(ValueError, match="Invalid quorum_type"):
            await svc.create_session(
                conversation_id=_uuid(),
                topic="Bad quorum",
                created_by=_uuid(),
                quorum_type="supermajority",
            )

    @pytest.mark.asyncio
    async def test_create_session_with_threshold(self):
        db = _mock_db()
        svc = ConsensusService(db)

        async def mock_refresh(obj):
            obj.id = _uuid()

        db.refresh = mock_refresh

        session = await svc.create_session(
            conversation_id=_uuid(),
            topic="Security review",
            created_by=_uuid(),
            quorum_type="threshold",
            threshold_pct=0.80,
            required_voters=[str(_uuid()), str(_uuid()), str(_uuid())],
        )

        assert session.quorum_type == "threshold"
        assert session.threshold_pct == 0.80
        assert len(session.required_voters) == 3

    @pytest.mark.asyncio
    async def test_create_session_unanimous(self):
        db = _mock_db()
        svc = ConsensusService(db)
        db.refresh = AsyncMock()

        session = await svc.create_session(
            conversation_id=_uuid(),
            topic="Deploy to prod",
            created_by=_uuid(),
            quorum_type="unanimous",
        )

        assert session.quorum_type == "unanimous"


# ── S3: cast_vote ─────────────────────────────────────────────────────────────

class TestS3CastVote:
    """Test ConsensusService.cast_vote()."""

    @pytest.mark.asyncio
    async def test_cast_vote_invalid_vote(self):
        db = _mock_db()
        svc = ConsensusService(db)

        with pytest.raises(ValueError, match="Vote must be approve, reject, or abstain"):
            await svc.cast_vote(
                session_id=_uuid(),
                voter_agent_id=_uuid(),
                vote="maybe",
            )

    @pytest.mark.asyncio
    async def test_cast_vote_session_not_found(self):
        db = _mock_db()
        db.get = AsyncMock(return_value=None)
        svc = ConsensusService(db)

        with pytest.raises(ValueError, match="Session not found"):
            await svc.cast_vote(
                session_id=_uuid(),
                voter_agent_id=_uuid(),
                vote="approve",
            )

    @pytest.mark.asyncio
    async def test_cast_vote_session_already_decided(self):
        db = _mock_db()
        session = _make_session(status="decided")
        db.get = AsyncMock(return_value=session)
        svc = ConsensusService(db)

        with pytest.raises(ValueError, match="Session is already decided"):
            await svc.cast_vote(
                session_id=session.id,
                voter_agent_id=_uuid(),
                vote="approve",
            )

    @pytest.mark.asyncio
    async def test_cast_vote_not_authorized(self):
        db = _mock_db()
        voter_id = _uuid()
        other_id = _uuid()
        session = _make_session(
            required_voters=[str(other_id)],
        )
        db.get = AsyncMock(return_value=session)
        svc = ConsensusService(db)

        with pytest.raises(ValueError, match="Not authorized to vote"):
            await svc.cast_vote(
                session_id=session.id,
                voter_agent_id=voter_id,
                vote="approve",
            )

    @pytest.mark.asyncio
    async def test_cast_vote_first_vote_changes_status(self):
        """First vote should transition session from 'open' to 'voting'."""
        db = _mock_db()
        voter_id = _uuid()
        session = _make_session(
            status="open",
            required_voters=[str(voter_id), str(_uuid()), str(_uuid())],
        )
        db.get = AsyncMock(return_value=session)

        # Mock SELECT FOR UPDATE — returns session with no decided_by_vote_id
        locked_session = _make_session(
            session_id=session.id,
            decided_by_vote_id=None,
            required_voters=session.required_voters,
        )
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = locked_session
        db.execute = AsyncMock(return_value=mock_result)

        svc = ConsensusService(db)

        # Patch check_quorum to return not reached
        with patch.object(svc, "check_quorum", return_value=QuorumResult(False, None, 1, 0, 0)):
            vote = await svc.cast_vote(
                session_id=session.id,
                voter_agent_id=voter_id,
                vote="approve",
                reasoning="Looks good",
            )

        assert session.status == "voting"
        db.add.assert_called_once()

    @pytest.mark.asyncio
    async def test_cast_vote_double_vote_raises(self):
        """DB UNIQUE constraint prevents double voting."""
        from sqlalchemy.exc import IntegrityError as SQLAIntegrityError

        db = _mock_db()
        voter_id = _uuid()
        session = _make_session(
            required_voters=[str(voter_id)],
        )
        db.get = AsyncMock(return_value=session)
        db.flush = AsyncMock(side_effect=SQLAIntegrityError("", {}, Exception()))
        svc = ConsensusService(db)

        with pytest.raises(ValueError, match="already voted"):
            await svc.cast_vote(
                session_id=session.id,
                voter_agent_id=voter_id,
                vote="approve",
            )

        db.rollback.assert_awaited_once()


# ── S4: check_quorum ──────────────────────────────────────────────────────────

class TestS4CheckQuorum:
    """Test ConsensusService.check_quorum() — majority, unanimous, threshold."""

    @pytest.mark.asyncio
    async def test_majority_2_of_3_approve(self):
        db = _mock_db()
        session_id = _uuid()
        voter1, voter2, voter3 = _uuid(), _uuid(), _uuid()

        session = _make_session(
            session_id=session_id,
            quorum_type="majority",
            required_voters=[str(voter1), str(voter2), str(voter3)],
        )
        db.get = AsyncMock(return_value=session)

        votes = [
            _make_vote(session_id=session_id, voter_agent_id=voter1, vote="approve"),
            _make_vote(session_id=session_id, voter_agent_id=voter2, vote="approve"),
        ]
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = votes
        db.execute = AsyncMock(return_value=mock_result)

        svc = ConsensusService(db)
        result = await svc.check_quorum(session_id)

        assert result.reached is True
        assert result.decision == "approve"
        assert result.votes_for == 2
        assert result.votes_against == 0

    @pytest.mark.asyncio
    async def test_majority_tie_rejects(self):
        """Majority tie (1 approve, 1 reject, 1 abstain in 3 voters) → reject."""
        db = _mock_db()
        session_id = _uuid()
        v1, v2, v3 = _uuid(), _uuid(), _uuid()

        session = _make_session(
            session_id=session_id,
            quorum_type="majority",
            required_voters=[str(v1), str(v2), str(v3)],
        )
        db.get = AsyncMock(return_value=session)

        votes = [
            _make_vote(session_id=session_id, voter_agent_id=v1, vote="approve"),
            _make_vote(session_id=session_id, voter_agent_id=v2, vote="reject"),
            _make_vote(session_id=session_id, voter_agent_id=v3, vote="abstain"),
        ]
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = votes
        db.execute = AsyncMock(return_value=mock_result)

        svc = ConsensusService(db)
        result = await svc.check_quorum(session_id)

        # All voted, no majority → reject
        assert result.reached is True
        assert result.decision == "reject"
        assert result.votes_for == 1
        assert result.votes_against == 1
        assert result.votes_abstain == 1

    @pytest.mark.asyncio
    async def test_majority_not_reached_pending(self):
        """1 approve out of 3 voters (2 pending) → quorum not reached."""
        db = _mock_db()
        session_id = _uuid()
        v1, v2, v3 = _uuid(), _uuid(), _uuid()

        session = _make_session(
            session_id=session_id,
            quorum_type="majority",
            required_voters=[str(v1), str(v2), str(v3)],
        )
        db.get = AsyncMock(return_value=session)

        votes = [
            _make_vote(session_id=session_id, voter_agent_id=v1, vote="approve"),
        ]
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = votes
        db.execute = AsyncMock(return_value=mock_result)

        svc = ConsensusService(db)
        result = await svc.check_quorum(session_id)

        assert result.reached is False
        assert result.decision is None

    @pytest.mark.asyncio
    async def test_majority_2_reject_in_3(self):
        """2 reject out of 3 voters → reject reached."""
        db = _mock_db()
        session_id = _uuid()
        v1, v2, v3 = _uuid(), _uuid(), _uuid()

        session = _make_session(
            session_id=session_id,
            quorum_type="majority",
            required_voters=[str(v1), str(v2), str(v3)],
        )
        db.get = AsyncMock(return_value=session)

        votes = [
            _make_vote(session_id=session_id, voter_agent_id=v1, vote="reject"),
            _make_vote(session_id=session_id, voter_agent_id=v2, vote="reject"),
        ]
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = votes
        db.execute = AsyncMock(return_value=mock_result)

        svc = ConsensusService(db)
        result = await svc.check_quorum(session_id)

        assert result.reached is True
        assert result.decision == "reject"
        assert result.votes_against == 2

    @pytest.mark.asyncio
    async def test_unanimous_all_approve(self):
        db = _mock_db()
        session_id = _uuid()
        v1, v2, v3 = _uuid(), _uuid(), _uuid()

        session = _make_session(
            session_id=session_id,
            quorum_type="unanimous",
            required_voters=[str(v1), str(v2), str(v3)],
        )
        db.get = AsyncMock(return_value=session)

        votes = [
            _make_vote(session_id=session_id, voter_agent_id=v1, vote="approve"),
            _make_vote(session_id=session_id, voter_agent_id=v2, vote="approve"),
            _make_vote(session_id=session_id, voter_agent_id=v3, vote="approve"),
        ]
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = votes
        db.execute = AsyncMock(return_value=mock_result)

        svc = ConsensusService(db)
        result = await svc.check_quorum(session_id)

        assert result.reached is True
        assert result.decision == "approve"
        assert result.votes_for == 3

    @pytest.mark.asyncio
    async def test_unanimous_one_reject_blocks(self):
        """Unanimous: 1 reject in 3 voters → immediately rejected."""
        db = _mock_db()
        session_id = _uuid()
        v1, v2, v3 = _uuid(), _uuid(), _uuid()

        session = _make_session(
            session_id=session_id,
            quorum_type="unanimous",
            required_voters=[str(v1), str(v2), str(v3)],
        )
        db.get = AsyncMock(return_value=session)

        votes = [
            _make_vote(session_id=session_id, voter_agent_id=v1, vote="approve"),
            _make_vote(session_id=session_id, voter_agent_id=v2, vote="reject"),
        ]
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = votes
        db.execute = AsyncMock(return_value=mock_result)

        svc = ConsensusService(db)
        result = await svc.check_quorum(session_id)

        assert result.reached is True
        assert result.decision == "reject"

    @pytest.mark.asyncio
    async def test_unanimous_pending(self):
        """Unanimous: 2 approve, 1 pending → not reached yet."""
        db = _mock_db()
        session_id = _uuid()
        v1, v2, v3 = _uuid(), _uuid(), _uuid()

        session = _make_session(
            session_id=session_id,
            quorum_type="unanimous",
            required_voters=[str(v1), str(v2), str(v3)],
        )
        db.get = AsyncMock(return_value=session)

        votes = [
            _make_vote(session_id=session_id, voter_agent_id=v1, vote="approve"),
            _make_vote(session_id=session_id, voter_agent_id=v2, vote="approve"),
        ]
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = votes
        db.execute = AsyncMock(return_value=mock_result)

        svc = ConsensusService(db)
        result = await svc.check_quorum(session_id)

        assert result.reached is False
        assert result.decision is None

    @pytest.mark.asyncio
    async def test_threshold_50pct_of_3(self):
        """Threshold 0.50: ceil(3*0.50)=2 approve needed. 2 approve → approve."""
        db = _mock_db()
        session_id = _uuid()
        v1, v2, v3 = _uuid(), _uuid(), _uuid()

        session = _make_session(
            session_id=session_id,
            quorum_type="threshold",
            threshold_pct=0.50,
            required_voters=[str(v1), str(v2), str(v3)],
        )
        db.get = AsyncMock(return_value=session)

        votes = [
            _make_vote(session_id=session_id, voter_agent_id=v1, vote="approve"),
            _make_vote(session_id=session_id, voter_agent_id=v2, vote="approve"),
        ]
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = votes
        db.execute = AsyncMock(return_value=mock_result)

        svc = ConsensusService(db)
        result = await svc.check_quorum(session_id)

        assert result.reached is True
        assert result.decision == "approve"

    @pytest.mark.asyncio
    async def test_threshold_impossible_to_reach(self):
        """Threshold: 1 approve + 2 reject, 0 pending → mathematically impossible → reject."""
        db = _mock_db()
        session_id = _uuid()
        v1, v2, v3 = _uuid(), _uuid(), _uuid()

        session = _make_session(
            session_id=session_id,
            quorum_type="threshold",
            threshold_pct=0.67,
            required_voters=[str(v1), str(v2), str(v3)],
        )
        db.get = AsyncMock(return_value=session)

        votes = [
            _make_vote(session_id=session_id, voter_agent_id=v1, vote="approve"),
            _make_vote(session_id=session_id, voter_agent_id=v2, vote="reject"),
            _make_vote(session_id=session_id, voter_agent_id=v3, vote="reject"),
        ]
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = votes
        db.execute = AsyncMock(return_value=mock_result)

        svc = ConsensusService(db)
        result = await svc.check_quorum(session_id)

        assert result.reached is True
        assert result.decision == "reject"


# ── S5: close_session ─────────────────────────────────────────────────────────

class TestS5CloseSession:
    """Test ConsensusService.close_session()."""

    @pytest.mark.asyncio
    async def test_close_session_by_creator(self):
        db = _mock_db()
        creator_id = _uuid()
        session = _make_session(
            status="voting",
            created_by=creator_id,
        )
        db.get = AsyncMock(return_value=session)
        svc = ConsensusService(db)

        result = await svc.close_session(
            session_id=session.id,
            agent_id=creator_id,
            reason="Changed requirements",
        )

        assert result.status == "cancelled"
        assert result.closed_at is not None
        assert result.result == {"decision": "cancelled", "reason": "Changed requirements"}

    @pytest.mark.asyncio
    async def test_close_session_by_lead(self):
        db = _mock_db()
        lead_id = _uuid()
        creator_id = _uuid()
        session = _make_session(
            status="open",
            created_by=creator_id,
        )
        db.get = AsyncMock(return_value=session)
        svc = ConsensusService(db)

        result = await svc.close_session(
            session_id=session.id,
            agent_id=lead_id,
            reason="Lead override",
            is_lead=True,
        )

        assert result.status == "cancelled"

    @pytest.mark.asyncio
    async def test_close_session_not_found(self):
        db = _mock_db()
        db.get = AsyncMock(return_value=None)
        svc = ConsensusService(db)

        with pytest.raises(ValueError, match="Session not found"):
            await svc.close_session(
                session_id=_uuid(),
                agent_id=_uuid(),
                reason="test",
            )

    @pytest.mark.asyncio
    async def test_close_session_already_decided(self):
        db = _mock_db()
        session = _make_session(status="decided")
        db.get = AsyncMock(return_value=session)
        svc = ConsensusService(db)

        with pytest.raises(ValueError, match="Cannot cancel session"):
            await svc.close_session(
                session_id=session.id,
                agent_id=_uuid(),
                reason="test",
            )

    @pytest.mark.asyncio
    async def test_close_session_unauthorized(self):
        db = _mock_db()
        creator_id = _uuid()
        other_id = _uuid()
        session = _make_session(
            status="open",
            created_by=creator_id,
        )
        db.get = AsyncMock(return_value=session)
        svc = ConsensusService(db)

        with pytest.raises(ValueError, match="Authorization error"):
            await svc.close_session(
                session_id=session.id,
                agent_id=other_id,
                reason="Not my session",
            )


# ── S6: timeout_expired_sessions ──────────────────────────────────────────────

class TestS6TimeoutExpired:
    """Test ConsensusService.timeout_expired_sessions()."""

    @pytest.mark.asyncio
    async def test_timeout_expired_session(self):
        db = _mock_db()
        # Session created 600 seconds ago with 300s timeout
        session = _make_session(
            status="voting",
            timeout_seconds=300,
            created_at=datetime.now(timezone.utc) - timedelta(seconds=600),
        )
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [session]
        db.execute = AsyncMock(return_value=mock_result)
        svc = ConsensusService(db)

        timed_out = await svc.timeout_expired_sessions()

        assert len(timed_out) == 1
        assert timed_out[0].status == "timeout"
        assert timed_out[0].result == {"decision": "timeout", "reason": "TTL expired"}

    @pytest.mark.asyncio
    async def test_timeout_no_expired(self):
        db = _mock_db()
        # Session created 10 seconds ago with 300s timeout
        session = _make_session(
            status="open",
            timeout_seconds=300,
            created_at=datetime.now(timezone.utc) - timedelta(seconds=10),
        )
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [session]
        db.execute = AsyncMock(return_value=mock_result)
        svc = ConsensusService(db)

        timed_out = await svc.timeout_expired_sessions()

        assert len(timed_out) == 0

    @pytest.mark.asyncio
    async def test_timeout_tz_naive_created_at(self):
        """Handles tz-naive created_at by assuming UTC."""
        db = _mock_db()

        # Create a simple namespace object with tz-naive datetime
        class NaiveSession:
            pass

        naive_dt = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(seconds=600)
        session = NaiveSession()
        session.id = _uuid()
        session.status = "open"
        session.timeout_seconds = 300
        session.created_at = naive_dt
        session.closed_at = None
        session.result = None

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [session]
        db.execute = AsyncMock(return_value=mock_result)
        svc = ConsensusService(db)

        timed_out = await svc.timeout_expired_sessions()

        assert len(timed_out) == 1
        assert timed_out[0].status == "timeout"


# ── S7: build_consensus_md ────────────────────────────────────────────────────

class TestS7BuildConsensusMd:
    """Test ConsensusService.build_consensus_md() for context injection."""

    @pytest.mark.asyncio
    async def test_build_consensus_md_none_conversation(self):
        db = _mock_db()
        svc = ConsensusService(db)

        result = await svc.build_consensus_md(None)

        assert result == ""

    @pytest.mark.asyncio
    async def test_build_consensus_md_no_sessions(self):
        db = _mock_db()
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        db.execute = AsyncMock(return_value=mock_result)
        svc = ConsensusService(db)

        result = await svc.build_consensus_md(_uuid())

        assert result == ""

    @pytest.mark.asyncio
    async def test_build_consensus_md_with_sessions(self):
        db = _mock_db()
        conv_id = _uuid()

        vote1 = _make_vote(vote="approve")
        vote2 = _make_vote(vote="reject")

        session = _make_session(
            conversation_id=conv_id,
            topic="Deploy v2.0",
            quorum_type="majority",
            required_voters=[str(_uuid()), str(_uuid()), str(_uuid())],
            votes=[vote1, vote2],
        )

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [session]
        db.execute = AsyncMock(return_value=mock_result)
        svc = ConsensusService(db)

        result = await svc.build_consensus_md(conv_id)

        assert "<active_votes>" in result
        assert "</active_votes>" in result
        assert "Deploy v2.0" in result
        assert "majority" in result
        assert "votes: 2/3" in result
        assert "approve: 1" in result
        assert "reject: 1" in result
        assert "abstain: 0" in result
        assert "@vote approve|reject|abstain" in result

    @pytest.mark.asyncio
    async def test_build_consensus_md_xml_escapes(self):
        """XSS-safe: topic with HTML chars is escaped."""
        db = _mock_db()
        conv_id = _uuid()

        session = _make_session(
            conversation_id=conv_id,
            topic='Deploy <script>alert("xss")</script>',
            quorum_type="majority",
            required_voters=[str(_uuid())],
            votes=[],
        )

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [session]
        db.execute = AsyncMock(return_value=mock_result)
        svc = ConsensusService(db)

        result = await svc.build_consensus_md(conv_id)

        assert "<script>" not in result
        assert "&lt;script&gt;" in result


# ── S8: Context Injector Integration ──────────────────────────────────────────

class TestS8ContextInjectorIntegration:
    """Test consensus wiring in context_injector.inject_context()."""

    @pytest.mark.asyncio
    async def test_inject_context_includes_consensus(self):
        """inject_context() calls build_consensus_md and appends result."""
        from app.services.agent_team.context_injector import ContextInjector

        db = _mock_db()
        agent_id = _uuid()
        conv_id = _uuid()

        injector = ContextInjector(db)

        # Mock all builders to return empty except consensus
        with patch.object(injector, "build_delegation_md", return_value="") as mock_d, \
             patch.object(injector, "build_team_md", return_value="") as mock_t, \
             patch.object(injector, "build_availability_md", return_value="") as mock_a, \
             patch.object(injector, "build_skills_md", return_value="") as mock_s, \
             patch.object(injector, "build_workspace_md", return_value="") as mock_w, \
             patch.object(injector, "build_feedback_md", return_value="") as mock_f, \
             patch("app.services.agent_team.consensus_service.ConsensusService") as MockCS:

            mock_svc = AsyncMock()
            mock_svc.build_consensus_md = AsyncMock(
                return_value="<active_votes>\n## Active Votes\n</active_votes>"
            )
            MockCS.return_value = mock_svc

            result = await injector.inject_context(
                agent_id=agent_id,
                team_id=None,
                system_prompt="You are a coder.",
                conversation_id=conv_id,
            )

        assert "<active_votes>" in result
        assert "You are a coder." in result
        assert "<system_context>" in result

    @pytest.mark.asyncio
    async def test_inject_context_consensus_runtime_error_logged(self):
        """Runtime errors in consensus are logged but don't break injection."""
        from app.services.agent_team.context_injector import ContextInjector

        db = _mock_db()
        injector = ContextInjector(db)

        with patch.object(injector, "build_delegation_md", return_value="") as mock_d, \
             patch.object(injector, "build_team_md", return_value="") as mock_t, \
             patch.object(injector, "build_availability_md", return_value="") as mock_a, \
             patch.object(injector, "build_skills_md", return_value="") as mock_s, \
             patch.object(injector, "build_workspace_md", return_value="") as mock_w, \
             patch.object(injector, "build_feedback_md", return_value="") as mock_f, \
             patch("app.services.agent_team.consensus_service.ConsensusService", side_effect=RuntimeError("db fail")), \
             patch("app.services.agent_team.context_injector.logger") as mock_logger:

            result = await injector.inject_context(
                agent_id=_uuid(),
                team_id=None,
                system_prompt="Base prompt.",
                conversation_id=_uuid(),
            )

        assert result == "Base prompt."
        mock_logger.warning.assert_called_once()
        assert "TRACE_CONSENSUS" in mock_logger.warning.call_args[0][0]

    @pytest.mark.asyncio
    async def test_inject_context_no_conversation_id_skips_consensus(self):
        """Without conversation_id, consensus builder returns empty."""
        from app.services.agent_team.context_injector import ContextInjector

        db = _mock_db()
        injector = ContextInjector(db)

        with patch.object(injector, "build_delegation_md", return_value="") as mock_d, \
             patch.object(injector, "build_team_md", return_value="") as mock_t, \
             patch.object(injector, "build_availability_md", return_value="") as mock_a, \
             patch.object(injector, "build_skills_md", return_value="") as mock_s, \
             patch.object(injector, "build_workspace_md", return_value="") as mock_w, \
             patch.object(injector, "build_feedback_md", return_value="") as mock_f, \
             patch("app.services.agent_team.consensus_service.ConsensusService") as MockCS:

            mock_svc = AsyncMock()
            mock_svc.build_consensus_md = AsyncMock(return_value="")
            MockCS.return_value = mock_svc

            result = await injector.inject_context(
                agent_id=_uuid(),
                team_id=None,
                system_prompt="Base prompt.",
                conversation_id=None,
            )

        assert result == "Base prompt."


# ── S9: QuorumResult Dataclass ────────────────────────────────────────────────

class TestS9QuorumResult:
    """Test QuorumResult dataclass structure."""

    def test_quorum_result_fields(self):
        qr = QuorumResult(
            reached=True,
            decision="approve",
            votes_for=3,
            votes_against=0,
            votes_abstain=1,
        )
        assert qr.reached is True
        assert qr.decision == "approve"
        assert qr.votes_for == 3
        assert qr.votes_against == 0
        assert qr.votes_abstain == 1

    def test_quorum_result_not_reached(self):
        qr = QuorumResult(
            reached=False,
            decision=None,
            votes_for=1,
            votes_against=0,
            votes_abstain=0,
        )
        assert qr.reached is False
        assert qr.decision is None


# ── S10: Alembic Chain & Model Registration ───────────────────────────────────

class TestS10AlembicAndRegistration:
    """Verify migration chain and model registration."""

    def test_migration_chain(self):
        """s221_001 down_revision points to s219_001."""
        import importlib.util
        import os
        migration_path = os.path.join(
            os.path.dirname(__file__),
            "..", "..", "alembic", "versions", "s221_001_consensus.py",
        )
        migration_path = os.path.normpath(migration_path)
        spec = importlib.util.spec_from_file_location("s221_001", migration_path)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        assert mod.revision == "s221_001"
        assert mod.down_revision == "s219_001"

    def test_models_registered_in_init(self):
        """ConsensusSession and ConsensusVote are in models __all__."""
        from app.models import __all__ as all_models
        assert "ConsensusSession" in all_models
        assert "ConsensusVote" in all_models

    def test_models_importable(self):
        """Models importable from app.models."""
        from app.models import ConsensusSession, ConsensusVote
        assert ConsensusSession is not None
        assert ConsensusVote is not None
