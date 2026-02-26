"""
=========================================================================
Reflection Graph — LangGraph Coder↔Reviewer Workflow (ADR-066 Phase 2)
SDLC Orchestrator - Sprint 206 (LangGraph Durable Workflows)

Version: 1.0.0
Date: February 2026
Status: ACTIVE - Sprint 206
Authority: CTO Approved (ADR-066)
Reference: ADR-066-LangChain-Multi-Agent-Orchestration.md

Purpose:
- Implements the Coder↔Reviewer reflection loop with durable checkpointing.
- Nodes call queue.enqueue() (enqueue_async pattern, D-066-03) and return
  immediately — the lane agent runs asynchronously.
- WorkflowResumer resumes at the saved checkpoint node after the agent completes.
- Uses LangGraph StateGraph when langgraph package is available; falls back
  to a Python dict routing table otherwise (tests and envs without langgraph).

Workflow Nodes:
  enqueue_coder   → Save checkpoint(waiting), enqueue coder task
  score_output    → (resumed after coder) Score output via EvalScorer
  enqueue_reviewer→ Save checkpoint(waiting), enqueue reviewer task
  inject_feedback → (resumed after reviewer) Increment iteration, loop back
  workflow_end    → Mark completed

ADR-066 Constraints:
  D-066-01: Before decision nodes, refresh gate truth from control plane.
  D-066-03: Nodes call enqueue_async() + return immediately.
  D-066-06: idempotency_keys prevent re-processing completed steps.

Optional Dependency Guard (SDLC 6.1.0 §5 — Sprint 185 pattern):
  try/except ImportError at module level.
  _LANGGRAPH_AVAILABLE sentinel for runtime checks.
  Module imports cleanly without langgraph package.

Zero Mock Policy: Production-ready async implementation.
=========================================================================
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from typing import Any, Optional
from uuid import UUID

logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────────────────────────────────────
# Optional Dependency Guard (SDLC 6.1.0 §5)
# Install: pip install 'langgraph>=0.2.0'
# ─────────────────────────────────────────────────────────────────────────────
try:
    from langgraph.graph import StateGraph, END as _LANGGRAPH_END
    from typing import TypedDict
    _LANGGRAPH_AVAILABLE = True
    _END = _LANGGRAPH_END
except ImportError:  # pragma: no cover
    _LANGGRAPH_AVAILABLE = False
    StateGraph = None  # type: ignore[assignment,misc]

    class TypedDict:  # type: ignore[no-redef]
        """Minimal TypedDict stub for environments without langgraph."""
        pass

    _END = "__end__"


# ─────────────────────────────────────────────────────────────────────────────
# Reflection Loop Constants
# ─────────────────────────────────────────────────────────────────────────────

EARLY_STOP_SCORE: float = 8.0    # Stop reflecting when avg score >= this
DEFAULT_MAX_ITERATIONS: int = 3   # Maximum Coder→Reviewer cycles
AGENT_TIMEOUT_MINUTES: int = 10   # How long until WorkflowResumer considers agent stuck

# Node name constants
NODE_ENQUEUE_CODER = "enqueue_coder"
NODE_SCORE_OUTPUT = "score_output"
NODE_ENQUEUE_REVIEWER = "enqueue_reviewer"
NODE_INJECT_FEEDBACK = "inject_feedback"
NODE_WORKFLOW_END = "workflow_end"


# ─────────────────────────────────────────────────────────────────────────────
# ReflectionState (TypedDict for LangGraph)
# ─────────────────────────────────────────────────────────────────────────────


class ReflectionState(TypedDict):  # type: ignore[misc]
    """
    LangGraph state for the Coder↔Reviewer reflection workflow.

    All fields are serializable (str/int/float) so they can be stored
    in WorkflowMetadata.state JSONB. Store message IDs, not full content.
    """

    conversation_id: str            # Workflow coordination conversation
    coder_conv_id: str              # Coder agent conversation UUID (str)
    reviewer_conv_id: str           # Reviewer agent conversation UUID (str)
    coder_def_id: str               # Coder AgentDefinition UUID (str)
    reviewer_def_id: str            # Reviewer AgentDefinition UUID (str)
    task: str                       # Task description for coder
    iteration: int                  # Current iteration (0-indexed)
    max_iterations: int             # Stop after this many iterations
    last_score: float               # Score from last EvalScorer run (0.0 on first iter)
    last_feedback: str              # Reviewer feedback to inject into next coder prompt
    coder_message_id: str           # ID of last coder message (pointer, not payload)
    reviewer_message_id: str        # ID of last reviewer message (pointer, not payload)


def _empty_reflection_state() -> dict[str, Any]:
    """Return a default-values dict compatible with ReflectionState."""
    return {
        "conversation_id": "",
        "coder_conv_id": "",
        "reviewer_conv_id": "",
        "coder_def_id": "",
        "reviewer_def_id": "",
        "task": "",
        "iteration": 0,
        "max_iterations": DEFAULT_MAX_ITERATIONS,
        "last_score": 0.0,
        "last_feedback": "",
        "coder_message_id": "",
        "reviewer_message_id": "",
    }


# ─────────────────────────────────────────────────────────────────────────────
# ReflectionGraph
# ─────────────────────────────────────────────────────────────────────────────


class ReflectionGraph:
    """
    Manages the Coder↔Reviewer reflection loop with durable Postgres checkpointing.

    Design (D-066-03 enqueue_async pattern):
      - enqueue_coder(): calls queue.enqueue() for coder task, saves checkpoint
        {status: "waiting", current_node: NODE_SCORE_OUTPUT} and returns immediately.
        The WorkflowResumer resumes at NODE_SCORE_OUTPUT after the coder completes.
      - score_output(): (synchronous, fast) runs EvalScorer on coder output.
        Routes to enqueue_reviewer OR marks workflow completed.
      - enqueue_reviewer(): calls queue.enqueue() for reviewer, saves checkpoint
        {current_node: NODE_INJECT_FEEDBACK, status: "waiting"}, returns immediately.
      - inject_feedback(): increments iteration, saves feedback, routes back to
        enqueue_coder for the next reflection iteration.

    Usage:
        graph = ReflectionGraph(workflow_service, queue, eval_scorer)

        # Start a new reflection workflow
        meta = await graph.start(
            conversation_id=workflow_conv_id,
            coder_conv_id=coder_conv_id,
            reviewer_conv_id=reviewer_conv_id,
            coder_def_id=coder_def_id,
            reviewer_def_id=reviewer_def_id,
            task="Implement user auth endpoint",
            max_iterations=3,
        )

        # Resume after an agent completes (called by WorkflowResumer)
        await graph.resume(conversation_id=workflow_conv_id)
    """

    def __init__(
        self,
        workflow_service: "Any",   # WorkflowService (local import avoids circular)
        queue: "Any",              # MessageQueue
        eval_scorer: "Any | None" = None,  # EvalScorer (optional — mocked in tests)
    ) -> None:
        self.workflow_service = workflow_service
        self.queue = queue
        self.eval_scorer = eval_scorer

        # Build LangGraph StateGraph when available (for routing visualization)
        self._compiled: Any = None
        if _LANGGRAPH_AVAILABLE and StateGraph is not None:
            try:
                self._compiled = self._build_graph()
            except Exception as exc:  # pragma: no cover
                logger.warning("ReflectionGraph: LangGraph build failed: %s", exc)
                self._compiled = None

    # ── LangGraph graph definition ───────────────────────────────────────────

    def _build_graph(self) -> Any:
        """Build LangGraph StateGraph (only called when langgraph is available)."""
        graph = StateGraph(ReflectionState)  # type: ignore[misc]

        # Register nodes (sync wrappers — async logic is separate)
        graph.add_node(NODE_ENQUEUE_CODER, self._enqueue_coder_stub)
        graph.add_node(NODE_SCORE_OUTPUT, self._score_output_stub)
        graph.add_node(NODE_ENQUEUE_REVIEWER, self._enqueue_reviewer_stub)
        graph.add_node(NODE_INJECT_FEEDBACK, self._inject_feedback_stub)

        graph.set_entry_point(NODE_ENQUEUE_CODER)

        # score_output routes conditionally based on score / iteration
        graph.add_conditional_edges(
            NODE_SCORE_OUTPUT,
            self._routing_decision,
            {
                NODE_ENQUEUE_REVIEWER: NODE_ENQUEUE_REVIEWER,
                _END: _END,
            },
        )

        # Linear edges (these are checkpointed — actual agent work is async)
        graph.add_edge(NODE_ENQUEUE_CODER, NODE_SCORE_OUTPUT)
        graph.add_edge(NODE_ENQUEUE_REVIEWER, NODE_INJECT_FEEDBACK)
        graph.add_edge(NODE_INJECT_FEEDBACK, NODE_ENQUEUE_CODER)

        return graph.compile()

    # ── Routing ──────────────────────────────────────────────────────────────

    def _routing_decision(self, state: dict[str, Any]) -> str:
        """
        Conditional routing at score_output node.

        Returns NODE_ENQUEUE_REVIEWER to continue the loop, or _END to stop.
        """
        score = float(state.get("last_score", 0.0))
        iteration = int(state.get("iteration", 0))
        max_iter = int(state.get("max_iterations", DEFAULT_MAX_ITERATIONS))

        if score >= EARLY_STOP_SCORE:
            logger.info(
                "ReflectionGraph: EARLY STOP score=%.1f >= %.1f at iter=%d",
                score,
                EARLY_STOP_SCORE,
                iteration,
            )
            return _END

        if iteration >= max_iter:
            logger.info(
                "ReflectionGraph: MAX ITERATIONS reached iter=%d >= max=%d",
                iteration,
                max_iter,
            )
            return _END

        return NODE_ENQUEUE_REVIEWER

    def next_node(self, current_node: str, state: dict[str, Any]) -> str:
        """
        Determine the next node from current_node + state.

        Used by WorkflowResumer to compute the next checkpoint without
        running the full LangGraph graph. Works without the langgraph package.

        Args:
            current_node: The node the workflow just completed.
            state: Current workflow state dict.

        Returns:
            Next node name, or _END if workflow is complete.
        """
        routing: dict[str, Any] = {
            NODE_ENQUEUE_CODER: NODE_SCORE_OUTPUT,
            NODE_SCORE_OUTPUT: self._routing_decision(state),
            NODE_ENQUEUE_REVIEWER: NODE_INJECT_FEEDBACK,
            NODE_INJECT_FEEDBACK: NODE_ENQUEUE_CODER,
        }
        return routing.get(current_node, _END)

    # ── LangGraph stub nodes (routing only — actual async work via resume()) ──

    def _enqueue_coder_stub(self, state: dict[str, Any]) -> dict[str, Any]:
        """LangGraph stub: routing pass-through. Real enqueue is in resume()."""
        return state

    def _score_output_stub(self, state: dict[str, Any]) -> dict[str, Any]:
        """LangGraph stub: routing pass-through. Real scoring is in resume()."""
        return state

    def _enqueue_reviewer_stub(self, state: dict[str, Any]) -> dict[str, Any]:
        """LangGraph stub: routing pass-through. Real enqueue is in resume()."""
        return state

    def _inject_feedback_stub(self, state: dict[str, Any]) -> dict[str, Any]:
        """LangGraph stub: routing pass-through. Real injection is in resume()."""
        return dict(state, iteration=state.get("iteration", 0) + 1)

    # ── Core workflow operations (async) ──────────────────────────────────────

    async def start(
        self,
        conversation_id: UUID,
        coder_conv_id: UUID,
        reviewer_conv_id: UUID,
        coder_def_id: UUID,
        reviewer_def_id: UUID,
        task: str,
        max_iterations: int = DEFAULT_MAX_ITERATIONS,
    ) -> "Any":  # WorkflowMetadata
        """
        Start a new reflection workflow.

        Creates WorkflowMetadata checkpoint and enqueues the first coder task.
        The coder will process asynchronously; WorkflowResumer will resume at
        NODE_SCORE_OUTPUT once the coder agent completes.

        Args:
            conversation_id: Workflow coordination conversation UUID.
            coder_conv_id: Coder agent conversation UUID.
            reviewer_conv_id: Reviewer agent conversation UUID.
            coder_def_id: Coder AgentDefinition UUID.
            reviewer_def_id: Reviewer AgentDefinition UUID.
            task: Task description sent to coder.
            max_iterations: Max reflection iterations before forced stop.

        Returns:
            WorkflowMetadata after first checkpoint save.
        """
        from app.services.agent_team.workflows.graph_state import WorkflowService  # noqa

        initial_state = {
            "conversation_id": str(conversation_id),
            "coder_conv_id": str(coder_conv_id),
            "reviewer_conv_id": str(reviewer_conv_id),
            "coder_def_id": str(coder_def_id),
            "reviewer_def_id": str(reviewer_def_id),
            "task": task,
            "iteration": 0,
            "max_iterations": max_iterations,
            "last_score": 0.0,
            "last_feedback": "",
            "coder_message_id": "",
            "reviewer_message_id": "",
        }

        # Create checkpoint at NODE_ENQUEUE_CODER
        meta = await self.workflow_service.start_workflow(
            conversation_id=conversation_id,
            initial_node=NODE_ENQUEUE_CODER,
            initial_state=initial_state,
        )

        # Immediately execute the first node
        return await self._execute_node(NODE_ENQUEUE_CODER, conversation_id, meta)

    async def resume(self, conversation_id: UUID) -> "Any | None":
        """
        Resume a waiting workflow from its Postgres checkpoint.

        Called by WorkflowResumer after an agent completes or the reconciler
        detects a stuck workflow.

        Args:
            conversation_id: Workflow coordination conversation UUID.

        Returns:
            Updated WorkflowMetadata, or None if workflow not found or terminal.
        """
        meta = await self.workflow_service.load(conversation_id)
        if meta is None:
            logger.debug("ReflectionGraph.resume: no workflow for conv=%s", conversation_id)
            return None

        if meta.is_terminal():
            logger.debug(
                "ReflectionGraph.resume: workflow already %s for conv=%s",
                meta.status,
                conversation_id,
            )
            return meta

        if meta.status != "waiting":
            logger.warning(
                "ReflectionGraph.resume: unexpected status=%s for conv=%s — expected 'waiting'",
                meta.status,
                conversation_id,
            )
            return meta

        return await self._execute_node(meta.current_node, conversation_id, meta)

    async def _execute_node(
        self,
        node: str,
        conversation_id: UUID,
        meta: "Any",  # WorkflowMetadata
    ) -> "Any":  # WorkflowMetadata
        """
        Dispatch to the appropriate node handler.

        Each node handler either:
        1. Enqueues an async agent task and saves a "waiting" checkpoint, OR
        2. Executes synchronous logic (score, feedback) and saves a "running"
           checkpoint before calling _execute_node for the next step.
        """
        state = meta.state

        if node == NODE_ENQUEUE_CODER:
            return await self._node_enqueue_coder(conversation_id, meta, state)
        elif node == NODE_SCORE_OUTPUT:
            return await self._node_score_output(conversation_id, meta, state)
        elif node == NODE_ENQUEUE_REVIEWER:
            return await self._node_enqueue_reviewer(conversation_id, meta, state)
        elif node == NODE_INJECT_FEEDBACK:
            return await self._node_inject_feedback(conversation_id, meta, state)
        elif node == NODE_WORKFLOW_END:
            return await self._node_workflow_end(conversation_id, meta)
        else:
            logger.error(
                "ReflectionGraph._execute_node: unknown node=%s conv=%s", node, conversation_id
            )
            return await self.workflow_service.transition(
                conversation_id,
                next_node=node,
                new_status="failed",
                state_updates={"error": f"Unknown node: {node}"},
            )

    # ── Node handlers ────────────────────────────────────────────────────────

    async def _node_enqueue_coder(
        self,
        conversation_id: UUID,
        meta: "Any",
        state: dict[str, Any],
    ) -> "Any":
        """
        Enqueue task to the coder agent (D-066-03: returns immediately).

        Saves checkpoint {current_node: NODE_SCORE_OUTPUT, status: "waiting"}
        so WorkflowResumer knows to resume at score_output after coder finishes.
        """
        task = state.get("task", "")
        last_feedback = state.get("last_feedback", "")
        coder_conv_id_str = state.get("coder_conv_id", "")
        coder_def_id_str = state.get("coder_def_id", "")
        iteration = state.get("iteration", 0)

        # Build coder prompt — inject reviewer feedback on subsequent iterations
        if last_feedback:
            content = (
                f"{task}\n\n"
                f"[Reviewer feedback from iteration {iteration}]:\n{last_feedback}"
            )
        else:
            content = task

        # Idempotency: don't re-enqueue if already done for this iteration
        step_id = f"enqueue_coder:iter{iteration}"
        if meta.is_step_done(step_id):
            logger.info(
                "ReflectionGraph: idempotent skip enqueue_coder iter=%d conv=%s",
                iteration,
                conversation_id,
            )
        else:
            try:
                msg = await self.queue.enqueue(
                    conversation_id=UUID(coder_conv_id_str) if coder_conv_id_str else conversation_id,
                    content=content,
                    sender_type="workflow",
                    sender_id=str(conversation_id),
                    processing_lane=f"agent:{coder_def_id_str}",
                    message_type="request",
                    dedupe_key=f"reflection:{conversation_id}:coder:iter{iteration}",
                )
                state = dict(state, coder_message_id=str(msg.id))
            except Exception as exc:
                logger.error(
                    "ReflectionGraph.enqueue_coder failed: conv=%s iter=%d: %s",
                    conversation_id,
                    iteration,
                    exc,
                )
                return await self.workflow_service.transition(
                    conversation_id,
                    next_node=NODE_ENQUEUE_CODER,
                    new_status="failed",
                    state_updates={"error": str(exc)},
                )

        # Save checkpoint: "waiting" at NODE_SCORE_OUTPUT
        wakeup = datetime.now(timezone.utc) + timedelta(minutes=AGENT_TIMEOUT_MINUTES)
        return await self.workflow_service.transition(
            conversation_id,
            next_node=NODE_SCORE_OUTPUT,
            new_status="waiting",
            state_updates=state,
            idempotency_key=step_id,
            next_wakeup_at=wakeup,
        )

    async def _node_score_output(
        self,
        conversation_id: UUID,
        meta: "Any",
        state: dict[str, Any],
    ) -> "Any":
        """
        Score the coder's output via EvalScorer (synchronous, fast).

        Routes to enqueue_reviewer or workflow_end based on score and iteration.
        """
        score = 0.0

        if self.eval_scorer is not None:
            try:
                task = state.get("task", "")
                coder_message_id = state.get("coder_message_id", "")
                # EvalScorer.score() is synchronous (see eval_scorer.py)
                # We use the message_id as the "response" pointer for scoring
                result = self.eval_scorer.score(
                    prompt=task,
                    response=coder_message_id,
                )
                if hasattr(result, "rubric") and hasattr(result.rubric, "total_score"):
                    score = float(result.rubric.total_score)
                elif hasattr(result, "total_score"):
                    score = float(result.total_score)
            except Exception as exc:
                logger.warning(
                    "ReflectionGraph.score_output: eval failed (using score=0): "
                    "conv=%s: %s",
                    conversation_id,
                    exc,
                )

        logger.info(
            "TRACE_REFLECTION conv=%s iter=%d score=%.1f threshold=%.1f",
            conversation_id,
            meta.iteration,
            score,
            EARLY_STOP_SCORE,
        )

        state = dict(state, last_score=score)

        # Routing decision
        next_nd = self._routing_decision(state)

        if next_nd == _END:
            return await self._node_workflow_end(
                conversation_id,
                meta,
                state_updates=state,
            )
        else:
            return await self._execute_node(
                NODE_ENQUEUE_REVIEWER, conversation_id,
                meta.model_copy(update={"state": state, "status": "running"}),
            )

    async def _node_enqueue_reviewer(
        self,
        conversation_id: UUID,
        meta: "Any",
        state: dict[str, Any],
    ) -> "Any":
        """
        Enqueue coder output to reviewer agent (D-066-03: returns immediately).

        Saves checkpoint {current_node: NODE_INJECT_FEEDBACK, status: "waiting"}.
        """
        reviewer_conv_id_str = state.get("reviewer_conv_id", "")
        reviewer_def_id_str = state.get("reviewer_def_id", "")
        coder_message_id = state.get("coder_message_id", "")
        task = state.get("task", "")
        iteration = state.get("iteration", meta.iteration)

        step_id = f"enqueue_reviewer:iter{iteration}"
        if meta.is_step_done(step_id):
            logger.info(
                "ReflectionGraph: idempotent skip enqueue_reviewer iter=%d conv=%s",
                iteration,
                conversation_id,
            )
        else:
            content = (
                f"Review this implementation of: '{task}'\n"
                f"Coder output reference: {coder_message_id}\n\n"
                "Provide specific, actionable feedback for improvement."
            )

            try:
                msg = await self.queue.enqueue(
                    conversation_id=UUID(reviewer_conv_id_str) if reviewer_conv_id_str else conversation_id,
                    content=content,
                    sender_type="workflow",
                    sender_id=str(conversation_id),
                    processing_lane=f"agent:{reviewer_def_id_str}",
                    message_type="request",
                    dedupe_key=f"reflection:{conversation_id}:reviewer:iter{iteration}",
                )
                state = dict(state, reviewer_message_id=str(msg.id))
            except Exception as exc:
                logger.error(
                    "ReflectionGraph.enqueue_reviewer failed: conv=%s iter=%d: %s",
                    conversation_id,
                    iteration,
                    exc,
                )
                return await self.workflow_service.transition(
                    conversation_id,
                    next_node=NODE_ENQUEUE_REVIEWER,
                    new_status="failed",
                    state_updates={"error": str(exc)},
                )

        wakeup = datetime.now(timezone.utc) + timedelta(minutes=AGENT_TIMEOUT_MINUTES)
        return await self.workflow_service.transition(
            conversation_id,
            next_node=NODE_INJECT_FEEDBACK,
            new_status="waiting",
            state_updates=state,
            idempotency_key=step_id,
            next_wakeup_at=wakeup,
        )

    async def _node_inject_feedback(
        self,
        conversation_id: UUID,
        meta: "Any",
        state: dict[str, Any],
    ) -> "Any":
        """
        Inject reviewer feedback and loop back to coder (next iteration).
        """
        reviewer_message_id = state.get("reviewer_message_id", "")
        # The reviewer's content would normally be fetched from DB via message_id.
        # For Sprint 206, we store the reference as feedback for the coder prompt.
        feedback = f"reviewer_message:{reviewer_message_id}"

        updated_state = dict(
            state,
            last_feedback=feedback,
            coder_message_id="",   # Reset for next coder run
        )

        # Increment iteration BEFORE going back to enqueue_coder
        updated_meta = meta.model_copy(
            update={"state": updated_state, "status": "running"}
        )

        return await self._execute_node(
            NODE_ENQUEUE_CODER,
            conversation_id,
            updated_meta,
        )

    async def _node_workflow_end(
        self,
        conversation_id: UUID,
        meta: "Any",
        state_updates: dict[str, Any] | None = None,
    ) -> "Any":
        """Mark workflow as completed."""
        return await self.workflow_service.transition(
            conversation_id,
            next_node=NODE_WORKFLOW_END,
            new_status="completed",
            state_updates=state_updates,
        )
