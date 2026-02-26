"""
Unit Tests — Sprint 206: WorkflowService + WorkflowMetadata (graph_state.py)

Additional tests to improve coverage of WorkflowService.
"""

import pytest
from uuid import uuid4
from unittest.mock import AsyncMock, MagicMock

from app.services.agent_team.workflows.graph_state import (
    WorkflowMetadata,
    WorkflowService,
    WorkflowConcurrencyError,
    WorkflowNotFoundError,
)
from app.services.agent_team.workflows.reflection_graph import NODE_ENQUEUE_CODER


def _make_conversation_mock(workflow_meta: WorkflowMetadata | None) -> MagicMock:
    """Build a mock AgentConversation with optional workflow metadata."""
    mock_conv = MagicMock()
    if workflow_meta is not None:
        mock_conv.metadata_ = {"workflow": workflow_meta.model_dump(mode="json")}
    else:
        mock_conv.metadata_ = {}
    return mock_conv


def _make_db_with_conv(conv_mock) -> AsyncMock:
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = conv_mock
    mock_db = AsyncMock()
    mock_db.execute = AsyncMock(return_value=mock_result)
    mock_db.flush = AsyncMock()
    return mock_db


# ─────────────────────────────────────────────────────────────────────────────
# WorkflowMetadata model tests
# ─────────────────────────────────────────────────────────────────────────────


def test_workflow_metadata_defaults():
    """WorkflowMetadata has correct defaults."""
    meta = WorkflowMetadata(current_node=NODE_ENQUEUE_CODER)
    assert meta.workflow_schema_version == "1.0.0"
    assert meta.workflow_type == "reflection"
    assert meta.status == "running"
    assert meta.iteration == 0
    assert meta.version == 0
    assert meta.idempotency_keys == {}
    assert meta.state == {}


def test_workflow_metadata_is_terminal():
    """is_terminal() returns True for completed/failed, False for waiting/running."""
    assert WorkflowMetadata(current_node="n", status="completed").is_terminal() is True
    assert WorkflowMetadata(current_node="n", status="failed").is_terminal() is True
    assert WorkflowMetadata(current_node="n", status="waiting").is_terminal() is False
    assert WorkflowMetadata(current_node="n", status="running").is_terminal() is False


def test_workflow_metadata_serialized_size():
    """serialized_size() returns bytes > 0."""
    meta = WorkflowMetadata(current_node="test_node", state={"key": "value"})
    assert meta.serialized_size() > 0


@pytest.mark.asyncio
async def test_workflow_service_load_returns_none_when_no_conversation():
    """WorkflowService.load() returns None when conversation not found."""
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None
    mock_db = AsyncMock()
    mock_db.execute = AsyncMock(return_value=mock_result)

    svc = WorkflowService(mock_db)
    result = await svc.load(uuid4())
    assert result is None


@pytest.mark.asyncio
async def test_workflow_service_load_returns_metadata_when_exists():
    """WorkflowService.load() returns WorkflowMetadata when workflow key exists."""
    meta = WorkflowMetadata(current_node=NODE_ENQUEUE_CODER, status="waiting", version=2)
    conv_mock = _make_conversation_mock(meta)
    mock_db = _make_db_with_conv(conv_mock)

    svc = WorkflowService(mock_db)
    result = await svc.load(uuid4())

    assert result is not None
    assert result.current_node == NODE_ENQUEUE_CODER
    assert result.status == "waiting"
    assert result.version == 2


@pytest.mark.asyncio
async def test_workflow_service_save_succeeds_on_version_match():
    """WorkflowService.save() returns True when expected_version matches DB version."""
    conv_id = uuid4()
    meta = WorkflowMetadata(current_node=NODE_ENQUEUE_CODER, version=2)
    conv_mock = _make_conversation_mock(meta)
    mock_db = _make_db_with_conv(conv_mock)

    svc = WorkflowService(mock_db)
    result = await svc.save(conv_id, meta, expected_version=2)

    assert result is True
    mock_db.flush.assert_awaited_once()


@pytest.mark.asyncio
async def test_workflow_service_save_first_time_no_existing():
    """WorkflowService.save() succeeds on first save (expected_version=0, no existing)."""
    conv_id = uuid4()
    meta = WorkflowMetadata(current_node=NODE_ENQUEUE_CODER, version=0)
    conv_mock = MagicMock()
    conv_mock.metadata_ = {}  # no existing workflow
    mock_db = _make_db_with_conv(conv_mock)

    svc = WorkflowService(mock_db)
    result = await svc.save(conv_id, meta, expected_version=0)

    assert result is True


@pytest.mark.asyncio
async def test_workflow_service_transition_raises_not_found():
    """WorkflowService.transition() raises WorkflowNotFoundError when no workflow."""
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None
    mock_db = AsyncMock()
    mock_db.execute = AsyncMock(return_value=mock_result)

    svc = WorkflowService(mock_db)
    # load() returns None (no conversation), transition should raise
    svc.load = AsyncMock(return_value=None)

    with pytest.raises(WorkflowNotFoundError):
        await svc.transition(uuid4(), next_node="test", new_status="running")
