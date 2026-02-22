"""
Unit Tests for Sprint Activity Log — Sprint 194 (ENR-02).

Tests:
- _log_sprint_activity appends to Sprint.metadata_
- Keeps last 50 activities (pruning)
- No crash when no active sprint
- No crash on DB error (non-critical path)
- Correct record structure (conversation_id, summary, timestamp)
"""

import pytest
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4
from datetime import datetime

from app.services.agent_team.team_orchestrator import TeamOrchestrator


@pytest.fixture
def db():
    """Mock async DB session."""
    return AsyncMock()


@pytest.fixture
def orchestrator(db):
    """Create TeamOrchestrator with mock DB."""
    return TeamOrchestrator(db)


class TestLogSprintActivity:
    """Test _log_sprint_activity method."""

    @pytest.mark.asyncio
    async def test_appends_activity_to_sprint(self, orchestrator, db):
        """Activity is appended to Sprint.metadata_['activities']."""
        sprint = MagicMock()
        sprint.id = uuid4()
        sprint.metadata_ = {}

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = sprint
        db.execute.return_value = mock_result

        await orchestrator._log_sprint_activity(
            conversation_id=uuid4(),
            project_id=uuid4(),
            summary="coder responded (ollama, 150ms)",
        )

        assert "activities" in sprint.metadata_
        assert len(sprint.metadata_["activities"]) == 1
        activity = sprint.metadata_["activities"][0]
        assert activity["summary"] == "coder responded (ollama, 150ms)"
        assert "conversation_id" in activity
        assert "timestamp" in activity
        db.flush.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_preserves_existing_activities(self, orchestrator, db):
        """New activity is appended after existing ones."""
        sprint = MagicMock()
        sprint.id = uuid4()
        sprint.metadata_ = {
            "activities": [{"summary": "existing", "timestamp": "T1", "conversation_id": "abc"}]
        }

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = sprint
        db.execute.return_value = mock_result

        await orchestrator._log_sprint_activity(
            conversation_id=uuid4(),
            project_id=uuid4(),
            summary="new activity",
        )

        assert len(sprint.metadata_["activities"]) == 2
        assert sprint.metadata_["activities"][0]["summary"] == "existing"
        assert sprint.metadata_["activities"][1]["summary"] == "new activity"

    @pytest.mark.asyncio
    async def test_prunes_to_50_activities(self, orchestrator, db):
        """Activities list is pruned to the last 50 entries."""
        sprint = MagicMock()
        sprint.id = uuid4()
        sprint.metadata_ = {
            "activities": [
                {"summary": f"activity-{i}", "timestamp": f"T{i}", "conversation_id": str(uuid4())}
                for i in range(55)
            ]
        }

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = sprint
        db.execute.return_value = mock_result

        await orchestrator._log_sprint_activity(
            conversation_id=uuid4(),
            project_id=uuid4(),
            summary="activity-55",
        )

        assert len(sprint.metadata_["activities"]) == 50
        # The oldest 6 should be pruned (55 existing + 1 new = 56, keep last 50)
        assert sprint.metadata_["activities"][-1]["summary"] == "activity-55"
        assert sprint.metadata_["activities"][0]["summary"] == "activity-6"

    @pytest.mark.asyncio
    async def test_no_crash_when_no_active_sprint(self, orchestrator, db):
        """Returns silently when no active sprint found."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        db.execute.return_value = mock_result

        # Should not raise
        await orchestrator._log_sprint_activity(
            conversation_id=uuid4(),
            project_id=uuid4(),
            summary="test",
        )
        db.flush.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_no_crash_on_db_error(self, orchestrator, db):
        """Logs warning but doesn't raise on DB error."""
        db.execute.side_effect = RuntimeError("DB connection lost")

        # Should not raise (non-critical path)
        await orchestrator._log_sprint_activity(
            conversation_id=uuid4(),
            project_id=uuid4(),
            summary="test",
        )

    @pytest.mark.asyncio
    async def test_handles_none_metadata(self, orchestrator, db):
        """Works when sprint.metadata_ is None."""
        sprint = MagicMock()
        sprint.id = uuid4()
        sprint.metadata_ = None

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = sprint
        db.execute.return_value = mock_result

        await orchestrator._log_sprint_activity(
            conversation_id=uuid4(),
            project_id=uuid4(),
            summary="first activity",
        )

        assert sprint.metadata_["activities"][0]["summary"] == "first activity"

    @pytest.mark.asyncio
    async def test_timestamp_is_utc_iso(self, orchestrator, db):
        """Activity timestamp is UTC ISO 8601."""
        sprint = MagicMock()
        sprint.id = uuid4()
        sprint.metadata_ = {}

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = sprint
        db.execute.return_value = mock_result

        await orchestrator._log_sprint_activity(
            conversation_id=uuid4(),
            project_id=uuid4(),
            summary="test",
        )

        ts = sprint.metadata_["activities"][0]["timestamp"]
        # Should parse as a valid ISO datetime
        parsed = datetime.fromisoformat(ts)
        assert parsed.tzinfo is not None or "+" in ts or "Z" in ts
