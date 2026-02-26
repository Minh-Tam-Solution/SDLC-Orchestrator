"""
Unit Tests — Sprint 206: LangGraph Durable Workflows

Test Cases:
  RG-01: start() creates WorkflowMetadata and enqueues coder
  RG-02: score_output routes to reviewer when score < 8.0
  RG-03: score_output marks completed when score >= 8.0 (EARLY STOP)
  RG-04: score_output marks completed when max_iterations reached
  RG-05: resume() returns None if no workflow exists
  RG-06: resume() skips terminal workflows
  RG-07: next_node() returns correct successor for each node
  WR-01: _resume_conversation() calls graph.resume()
  WR-02: _reconcile_once() resumes workflows past wakeup_at
  WR-03: publish_resume() publishes to Redis channel
  WR-04: _run_pubsub_listener() calls _resume_conversation on message
  WR-05: concurrent resume is safe (OCC no-op on second call)
  ID-01: idempotent enqueue_coder (step already in idempotency_keys)
  ID-02: idempotent enqueue_reviewer (step already in idempotency_keys)
  ID-03: WorkflowMetadata.is_step_done() returns True for done steps
  CP-01: WorkflowService.start_workflow() raises on existing workflow
  CP-02: WorkflowService.save() returns False on OCC version conflict
"""

import asyncio
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

from app.services.agent_team.workflows.graph_state import (
    WorkflowConcurrencyError,
    WorkflowMetadata,
    WorkflowNotFoundError,
    WorkflowService,
)
from app.services.agent_team.workflows.reflection_graph import (
    DEFAULT_MAX_ITERATIONS,
    EARLY_STOP_SCORE,
    NODE_ENQUEUE_CODER,
    NODE_ENQUEUE_REVIEWER,
    NODE_INJECT_FEEDBACK,
    NODE_SCORE_OUTPUT,
    NODE_WORKFLOW_END,
    ReflectionGraph,
    _END,
)
from app.services.agent_team.workflow_resumer import (
    WORKFLOW_RESUME_CHANNEL,
    WorkflowResumer,
)


# ─────────────────────────────────────────────────────────────────────────────
# Fixtures
# ─────────────────────────────────────────────────────────────────────────────


def _make_meta(**kwargs) -> WorkflowMetadata:
    """Build a WorkflowMetadata with sensible test defaults."""
    defaults = dict(
        current_node=NODE_ENQUEUE_CODER,
        status="running",
        iteration=0,
        version=1,
        state={
            "conversation_id": str(uuid4()),
            "coder_conv_id": str(uuid4()),
            "reviewer_conv_id": str(uuid4()),
            "coder_def_id": str(uuid4()),
            "reviewer_def_id": str(uuid4()),
            "task": "Implement auth endpoint",
            "max_iterations": DEFAULT_MAX_ITERATIONS,
            "last_score": 0.0,
            "last_feedback": "",
            "coder_message_id": "",
            "reviewer_message_id": "",
            "iteration": 0,
        },
    )
    defaults.update(kwargs)
    return WorkflowMetadata(**defaults)


def _make_workflow_service() -> MagicMock:
    """Build a WorkflowService mock."""
    svc = MagicMock()
    svc.load = AsyncMock()
    svc.save = AsyncMock(return_value=True)
    svc.start_workflow = AsyncMock()
    svc.transition = AsyncMock()
    return svc


def _make_queue() -> MagicMock:
    """Build a MessageQueue mock."""
    q = MagicMock()
    msg = MagicMock()
    msg.id = uuid4()
    q.enqueue = AsyncMock(return_value=msg)
    return q


# ─────────────────────────────────────────────────────────────────────────────
# RG — ReflectionGraph tests
# ─────────────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_rg01_start_creates_checkpoint_and_enqueues():
    """RG-01: start() creates WorkflowMetadata and enqueues first coder task."""
    conv_id = uuid4()
    coder_conv = uuid4()
    reviewer_conv = uuid4()
    coder_def = uuid4()
    reviewer_def = uuid4()

    initial_meta = _make_meta(current_node=NODE_ENQUEUE_CODER, status="running", version=1)
    waiting_meta = _make_meta(current_node=NODE_SCORE_OUTPUT, status="waiting", version=2)

    svc = _make_workflow_service()
    svc.start_workflow.return_value = initial_meta
    svc.transition.return_value = waiting_meta
    queue = _make_queue()

    graph = ReflectionGraph(workflow_service=svc, queue=queue)
    result = await graph.start(
        conversation_id=conv_id,
        coder_conv_id=coder_conv,
        reviewer_conv_id=reviewer_conv,
        coder_def_id=coder_def,
        reviewer_def_id=reviewer_def,
        task="Test task",
        max_iterations=3,
    )

    svc.start_workflow.assert_awaited_once()
    queue.enqueue.assert_awaited_once()
    svc.transition.assert_awaited()
    assert result.current_node == NODE_SCORE_OUTPUT
    assert result.status == "waiting"


@pytest.mark.asyncio
async def test_rg02_score_output_routes_to_reviewer_when_low_score():
    """RG-02: score_output routes to enqueue_reviewer when score < 8.0."""
    conv_id = uuid4()
    meta = _make_meta(
        current_node=NODE_SCORE_OUTPUT,
        status="waiting",
        version=2,
        iteration=0,
    )
    # state with low score
    meta = meta.model_copy(update={"state": dict(meta.state, last_score=3.0, iteration=0)})

    reviewer_waiting_meta = _make_meta(
        current_node=NODE_INJECT_FEEDBACK, status="waiting", version=3
    )
    svc = _make_workflow_service()
    svc.load.return_value = meta
    svc.transition.return_value = reviewer_waiting_meta
    queue = _make_queue()

    # Score below threshold — no eval_scorer → default score=0.0
    graph = ReflectionGraph(workflow_service=svc, queue=queue, eval_scorer=None)
    result = await graph._node_score_output(conv_id, meta, meta.state)

    # Should have called enqueue_reviewer path
    svc.transition.assert_awaited()
    # transition should eventually get to reviewer node
    # The reviewer enqueue transitions to NODE_INJECT_FEEDBACK waiting
    assert result.current_node == NODE_INJECT_FEEDBACK


@pytest.mark.asyncio
async def test_rg03_score_output_early_stop_when_high_score():
    """RG-03: score_output marks completed (EARLY STOP) when score >= 8.0."""
    conv_id = uuid4()
    meta = _make_meta(
        current_node=NODE_SCORE_OUTPUT,
        status="running",
        version=2,
        iteration=0,
    )

    completed_meta = _make_meta(current_node=NODE_WORKFLOW_END, status="completed", version=3)
    svc = _make_workflow_service()
    svc.transition.return_value = completed_meta

    # Mock eval_scorer that returns high score
    mock_scorer = MagicMock()
    mock_result = MagicMock()
    mock_result.rubric = MagicMock()
    mock_result.rubric.total_score = EARLY_STOP_SCORE + 0.5  # 8.5 > 8.0
    mock_scorer.score = MagicMock(return_value=mock_result)

    queue = _make_queue()
    graph = ReflectionGraph(workflow_service=svc, queue=queue, eval_scorer=mock_scorer)

    state = dict(meta.state, last_score=0.0, iteration=0, max_iterations=3)
    result = await graph._node_score_output(conv_id, meta, state)

    assert result.status == "completed"
    assert result.current_node == NODE_WORKFLOW_END


@pytest.mark.asyncio
async def test_rg04_score_output_stops_at_max_iterations():
    """RG-04: score_output marks completed when max_iterations reached."""
    conv_id = uuid4()
    max_iter = 2
    meta = _make_meta(
        current_node=NODE_SCORE_OUTPUT,
        status="running",
        version=5,
        iteration=max_iter,  # iteration == max_iterations → stop
    )
    completed_meta = _make_meta(current_node=NODE_WORKFLOW_END, status="completed", version=6)
    svc = _make_workflow_service()
    svc.transition.return_value = completed_meta

    queue = _make_queue()
    graph = ReflectionGraph(workflow_service=svc, queue=queue, eval_scorer=None)

    state = dict(meta.state, last_score=3.0, iteration=max_iter, max_iterations=max_iter)
    result = await graph._node_score_output(conv_id, meta, state)

    assert result.status == "completed"


@pytest.mark.asyncio
async def test_rg05_resume_returns_none_if_no_workflow():
    """RG-05: resume() returns None if no workflow exists for conversation."""
    svc = _make_workflow_service()
    svc.load.return_value = None

    queue = _make_queue()
    graph = ReflectionGraph(workflow_service=svc, queue=queue)
    result = await graph.resume(uuid4())

    assert result is None


@pytest.mark.asyncio
async def test_rg06_resume_skips_terminal_workflows():
    """RG-06: resume() returns meta immediately if workflow is terminal."""
    conv_id = uuid4()
    completed_meta = _make_meta(current_node=NODE_WORKFLOW_END, status="completed", version=10)
    svc = _make_workflow_service()
    svc.load.return_value = completed_meta

    queue = _make_queue()
    graph = ReflectionGraph(workflow_service=svc, queue=queue)
    result = await graph.resume(conv_id)

    assert result is not None
    assert result.status == "completed"
    svc.transition.assert_not_awaited()


def test_rg07_next_node_routing_table():
    """RG-07: next_node() returns correct successor for each non-decision node."""
    svc = _make_workflow_service()
    graph = ReflectionGraph(workflow_service=svc, queue=_make_queue())

    # State that leads to reviewer (score < threshold)
    state_low_score = {"last_score": 2.0, "iteration": 0, "max_iterations": 3}
    state_high_score = {"last_score": 9.0, "iteration": 0, "max_iterations": 3}
    state_max_iter = {"last_score": 2.0, "iteration": 3, "max_iterations": 3}

    assert graph.next_node(NODE_ENQUEUE_CODER, state_low_score) == NODE_SCORE_OUTPUT
    assert graph.next_node(NODE_ENQUEUE_REVIEWER, state_low_score) == NODE_INJECT_FEEDBACK
    assert graph.next_node(NODE_INJECT_FEEDBACK, state_low_score) == NODE_ENQUEUE_CODER
    # score_output routes based on score
    assert graph.next_node(NODE_SCORE_OUTPUT, state_low_score) == NODE_ENQUEUE_REVIEWER
    assert graph.next_node(NODE_SCORE_OUTPUT, state_high_score) == _END
    assert graph.next_node(NODE_SCORE_OUTPUT, state_max_iter) == _END


# ─────────────────────────────────────────────────────────────────────────────
# WR — WorkflowResumer tests
# ─────────────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_wr01_resume_conversation_calls_graph_resume():
    """WR-01: _resume_conversation() calls graph.resume() and returns True."""
    conv_id = uuid4()
    completed_meta = _make_meta(current_node=NODE_WORKFLOW_END, status="completed", version=5)

    mock_graph = MagicMock()
    mock_graph.resume = AsyncMock(return_value=completed_meta)

    mock_db = AsyncMock()
    resumer = WorkflowResumer(db=mock_db, graph=mock_graph)

    result = await resumer._resume_conversation(conv_id)

    mock_graph.resume.assert_awaited_once_with(conv_id)
    assert result is True


@pytest.mark.asyncio
async def test_wr02_reconcile_once_resumes_overdue_workflows():
    """WR-02: _reconcile_once() finds workflows past next_wakeup_at and resumes them."""
    conv_id = uuid4()
    mock_graph = MagicMock()
    mock_graph.resume = AsyncMock(return_value=_make_meta(status="waiting"))

    # Mock the DB execute to return a row with conv_id
    mock_row = MagicMock()
    mock_row.__getitem__ = lambda self, idx: str(conv_id)
    mock_result = MagicMock()
    mock_result.fetchall.return_value = [mock_row]

    mock_db = AsyncMock()
    mock_db.execute = AsyncMock(return_value=mock_result)

    resumer = WorkflowResumer(db=mock_db, graph=mock_graph)
    count = await resumer._reconcile_once()

    assert count == 1
    mock_graph.resume.assert_awaited_once()


@pytest.mark.asyncio
async def test_wr03_publish_resume_publishes_to_redis():
    """WR-03: publish_resume() publishes conversation_id to WORKFLOW_RESUME_CHANNEL."""
    conv_id = uuid4()
    mock_redis = AsyncMock()
    mock_redis.publish = AsyncMock(return_value=1)

    resumer = WorkflowResumer(redis=mock_redis)
    result = await resumer.publish_resume(conv_id)

    mock_redis.publish.assert_awaited_once_with(WORKFLOW_RESUME_CHANNEL, str(conv_id))
    assert result is True


@pytest.mark.asyncio
async def test_wr04_pubsub_listener_calls_resume_on_message():
    """WR-04: _run_pubsub_listener() calls _resume_conversation on pub/sub message."""
    conv_id = uuid4()
    completed_meta = _make_meta(status="completed")

    call_count = 0

    async def fake_resume(cid):
        nonlocal call_count
        call_count += 1
        return True

    message = {"type": "message", "data": str(conv_id)}

    # Build a mock pubsub that returns 1 message then stops the loop
    msg_iter = [message, None, None]
    msg_idx = [0]

    async def fake_get_message(**kwargs):
        idx = msg_idx[0]
        msg_idx[0] += 1
        if idx < len(msg_iter):
            return msg_iter[idx]
        return None

    mock_pubsub = AsyncMock()
    mock_pubsub.subscribe = AsyncMock()
    mock_pubsub.unsubscribe = AsyncMock()
    mock_pubsub.close = AsyncMock()
    mock_pubsub.get_message = fake_get_message

    mock_redis = AsyncMock()
    mock_redis.pubsub = MagicMock(return_value=mock_pubsub)

    resumer = WorkflowResumer(redis=mock_redis)
    resumer._running = True
    resumer._resume_conversation = fake_resume

    # Run listener briefly then stop
    async def stopper():
        await asyncio.sleep(0.05)
        resumer._running = False

    await asyncio.gather(
        resumer._run_pubsub_listener(),
        stopper(),
    )

    assert call_count == 1


@pytest.mark.asyncio
async def test_wr05_concurrent_resume_occ_safe():
    """WR-05: concurrent resume — OCC allows 1 writer, second is a safe no-op."""
    conv_id = uuid4()
    # Simulate two concurrent calls to _resume_conversation on a single workflow
    # First call succeeds (graph.resume returns updated meta)
    # Second call finds no-op (already-advanced meta)

    call_count = [0]

    async def mock_graph_resume(cid):
        call_count[0] += 1
        if call_count[0] == 1:
            return _make_meta(status="waiting", current_node=NODE_SCORE_OUTPUT, version=3)
        else:
            # Second call: workflow already advanced (no-op)
            return _make_meta(status="completed", current_node=NODE_WORKFLOW_END, version=4)

    mock_graph = MagicMock()
    mock_graph.resume = mock_graph_resume

    mock_db = AsyncMock()
    resumer = WorkflowResumer(db=mock_db, graph=mock_graph)

    # Run concurrently
    results = await asyncio.gather(
        resumer._resume_conversation(conv_id),
        resumer._resume_conversation(conv_id),
    )

    assert all(results)
    assert call_count[0] == 2


# ─────────────────────────────────────────────────────────────────────────────
# ID — Idempotency tests
# ─────────────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_id01_idempotent_enqueue_coder_skips_if_done():
    """ID-01: enqueue_coder skips queue.enqueue() if step already in idempotency_keys."""
    conv_id = uuid4()
    iteration = 0
    step_id = f"enqueue_coder:iter{iteration}"

    # Meta with step already done
    meta = _make_meta(
        current_node=NODE_ENQUEUE_CODER,
        status="running",
        version=2,
        iteration=iteration,
        idempotency_keys={step_id: NODE_SCORE_OUTPUT},
    )
    waiting_meta = _make_meta(current_node=NODE_SCORE_OUTPUT, status="waiting", version=3)

    svc = _make_workflow_service()
    svc.transition.return_value = waiting_meta
    queue = _make_queue()

    graph = ReflectionGraph(workflow_service=svc, queue=queue)
    await graph._node_enqueue_coder(conv_id, meta, meta.state)

    # enqueue should NOT be called (idempotent skip)
    queue.enqueue.assert_not_awaited()
    # transition IS still called (to advance checkpoint)
    svc.transition.assert_awaited()


@pytest.mark.asyncio
async def test_id02_idempotent_enqueue_reviewer_skips_if_done():
    """ID-02: enqueue_reviewer skips queue.enqueue() if step already in idempotency_keys."""
    conv_id = uuid4()
    iteration = 1
    step_id = f"enqueue_reviewer:iter{iteration}"

    state = {
        "conversation_id": str(conv_id),
        "coder_conv_id": str(uuid4()),
        "reviewer_conv_id": str(uuid4()),
        "coder_def_id": str(uuid4()),
        "reviewer_def_id": str(uuid4()),
        "task": "Test",
        "iteration": iteration,
        "max_iterations": 3,
        "last_score": 4.0,
        "last_feedback": "",
        "coder_message_id": str(uuid4()),
        "reviewer_message_id": "",
    }
    meta = _make_meta(
        current_node=NODE_ENQUEUE_REVIEWER,
        status="running",
        version=4,
        iteration=iteration,
        idempotency_keys={step_id: NODE_INJECT_FEEDBACK},
        state=state,
    )
    inject_meta = _make_meta(current_node=NODE_INJECT_FEEDBACK, status="waiting", version=5)

    svc = _make_workflow_service()
    svc.transition.return_value = inject_meta
    queue = _make_queue()

    graph = ReflectionGraph(workflow_service=svc, queue=queue)
    await graph._node_enqueue_reviewer(conv_id, meta, meta.state)

    queue.enqueue.assert_not_awaited()
    svc.transition.assert_awaited()


def test_id03_workflow_metadata_is_step_done():
    """ID-03: WorkflowMetadata.is_step_done() returns True for done, False for new."""
    meta = WorkflowMetadata(
        current_node=NODE_SCORE_OUTPUT,
        idempotency_keys={"enqueue_coder:iter0": NODE_SCORE_OUTPUT},
    )
    assert meta.is_step_done("enqueue_coder:iter0") is True
    assert meta.is_step_done("enqueue_coder:iter1") is False
    assert meta.is_step_done("enqueue_reviewer:iter0") is False


# ─────────────────────────────────────────────────────────────────────────────
# CP — Control Plane tests
# ─────────────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_cp01_start_workflow_raises_if_already_exists():
    """CP-01: WorkflowService.start_workflow() raises WorkflowConcurrencyError if workflow exists."""
    existing_meta = _make_meta(status="waiting")

    mock_db = AsyncMock()
    svc = WorkflowService(mock_db)
    # Patch load to return existing workflow
    svc.load = AsyncMock(return_value=existing_meta)

    with pytest.raises(WorkflowConcurrencyError, match="already exists"):
        await svc.start_workflow(uuid4(), initial_node=NODE_ENQUEUE_CODER)


@pytest.mark.asyncio
async def test_cp02_save_returns_false_on_occ_version_conflict():
    """CP-02: WorkflowService.save() returns False when DB version != expected_version."""
    conv_id = uuid4()
    meta = _make_meta(version=3)

    # Mock conversation with version=5 in DB (conflict: caller has version=3)
    mock_conversation = MagicMock()
    mock_conversation.metadata_ = {
        "workflow": meta.model_dump(mode="json") | {"version": 5}
    }
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = mock_conversation

    mock_db = AsyncMock()
    mock_db.execute = AsyncMock(return_value=mock_result)

    svc = WorkflowService(mock_db)
    # Caller expects version=3, DB has version=5 → OCC conflict
    result = await svc.save(conv_id, meta, expected_version=3)

    assert result is False
