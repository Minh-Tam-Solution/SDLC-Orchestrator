---
sdlc_version: "6.1.1"
document_type: "Functional Requirement"
status: "PROPOSED"
sprint: "206"
spec_id: "FR-046"
tier: "PROFESSIONAL"
stage: "01 - Planning"
---

# FR-046: LangGraph Reflection Workflow

**Version**: 1.0.0
**Status**: PROPOSED
**Created**: February 2026
**Sprint**: 206
**Framework**: SDLC 6.1.1
**Epic**: EP-07 Multi-Agent Team Engine
**ADR**: ADR-066 (LangChain Multi-Agent Orchestration, D-066-02 through D-066-06)
**Owner**: Backend Team
**Source**: CEO MAS Research (`mas/02-MAS-ARCHITECTURE.md`)

---

## 1. Overview

### 1.1 Purpose

Add LangGraph durable async workflow graphs for reflection loops (Coder <-> Reviewer) and SDLC pipelines (G0->G4). Workflows survive crashes via Postgres checkpoint stored in `agent_conversations.metadata_` JSONB. WorkflowResumer as a separate Docker service handles async resume.

### 1.2 Business Value

- Reflection loops enable Coder->Reviewer->Retry patterns with max 3 iterations
- Crash recovery: workflow resumes from last checkpoint after process restart
- Async architecture: LangGraph nodes use `enqueue_async()` — never block waiting for lane completion
- Single-instance WorkflowResumer prevents duplicate processing

---

## 2. Functional Requirements

### 2.1 WorkflowMetadata Schema (D-066-02)

**GIVEN** a workflow is created for an agent conversation
**WHEN** workflow state is stored
**THEN** the system SHALL store a `WorkflowMetadata` Pydantic model in `agent_conversations.metadata_` JSONB:

```python
class WorkflowMetadata(BaseModel):
    workflow_schema_version: str = "1.0.0"
    workflow_id: UUID
    workflow_type: Literal["reflection"]
    status: Literal["waiting", "running", "completed", "failed"]
    current_node: str
    iteration: int = 0
    next_wakeup_at: Optional[datetime] = None
    idempotency_keys: dict[str, str] = {}
    version: int = 1  # OCC
    state: dict = {}
```

**AND** the total JSONB size SHALL NOT exceed 64KB
**AND** store pointers (evidence_id for artifacts), NOT payloads
**AND** Pydantic validation SHALL be required before every read/write

### 2.2 Partial Index (D-066-02)

**GIVEN** workflows need efficient querying for the reconciler
**WHEN** the Alembic migration runs
**THEN** a partial index SHALL be created:
```sql
CREATE INDEX ix_agent_conv_workflow_status
  ON agent_conversations ((metadata_->>'status'), (metadata_->>'next_wakeup_at'))
  WHERE metadata_->>'workflow_id' IS NOT NULL;
```

### 2.3 Async Enqueue (D-066-03)

**GIVEN** a LangGraph node needs to dispatch work to a lane
**WHEN** the node calls `team_orchestrator.enqueue_async()`
**THEN** the system SHALL:
  1. Enqueue the message to the lane queue
  2. Save the workflow checkpoint (current_node, iteration, state)
  3. Return immediately (non-blocking)
**AND** the node SHALL NEVER block waiting for lane completion

### 2.4 Reflection Graph

**GIVEN** a reflection workflow is started via `POST /api/v1/workflows/reflection`
**WHEN** the StateGraph executes
**THEN** the workflow SHALL follow this graph:

```
START → coder_node → reviewer_node → decision_node
                                          │
                                   ┌──────┴──────┐
                                   │             │
                               PASS           REJECT
                                   │             │
                              complete     iteration < 3?
                                              │        │
                                             YES      NO
                                              │        │
                                         coder_node  fail
```

**AND** max iterations SHALL be 3 (configurable)
**AND** each node SHALL use `enqueue_async()` for lane dispatch

### 2.5 WorkflowResumer (D-066-05)

**GIVEN** an agent completes work in a lane
**WHEN** the lane publishes a completion event
**THEN** the WorkflowResumer SHALL:
  1. Load the workflow checkpoint from `metadata_` JSONB
  2. Validate with Pydantic (`WorkflowMetadata`)
  3. Increment `version` (OCC) atomically
  4. Resume the next node in the StateGraph

### 2.6 WorkflowResumer Dual-Path (D-066-05)

**GIVEN** WorkflowResumer is running as a separate Docker service
**WHEN** a workflow needs to resume
**THEN** the system SHALL support two resume paths:
  - **Fast path**: Redis pub/sub listener for immediate resume
  - **Fallback**: Reconciler polling every 30s for missed events
**AND** stuck detection: workflows in `waiting` status for >5 minutes SHALL be auto-resumed

### 2.7 WorkflowResumer Single Instance (D-066-05)

**GIVEN** the WorkflowResumer Docker service
**WHEN** deployed
**THEN** `docker-compose.yml` SHALL specify `replicas: 1`
**AND** the resumer SHALL NEVER run inside `main.py` with multi-worker uvicorn
**AND** optionally use Redis leader election with 30s TTL as additional safety

### 2.8 Optimistic Concurrency Control (D-066-02)

**GIVEN** two WorkflowResumer instances attempt to resume the same workflow
**WHEN** both read the same `version` value
**THEN** the first `UPDATE ... WHERE version = N` SHALL succeed (version → N+1)
**AND** the second SHALL get 0 rows updated → no-op (safe concurrent resume)

### 2.9 End-to-End Idempotency (D-066-06)

**GIVEN** a workflow step may be retried
**WHEN** the step executes
**THEN** idempotency SHALL be enforced at 3 layers:

| Layer | Key | Behavior |
|-------|-----|----------|
| Workflow step | `(workflow_id, step_id)` | Step already completed → no-op |
| Message enqueue | `idempotency_key` param in `enqueue_async()` | Already enqueued → return existing message_id |
| Control plane | `X-Idempotency-Key` header | Already processed → return cached response (Redis, 1hr TTL) |

### 2.10 Control Plane Refresh (D-066-01)

**GIVEN** a LangGraph workflow reaches a decision node
**WHEN** the decision node executes
**THEN** the node SHALL call `GET /gates/{id}/actions` to refresh truth from the control plane
**AND** LangGraph state SHALL be treated as DRAFT (Postgres is TRUTH)

### 2.11 Workflow API Endpoints

**GIVEN** the workflows router is registered
**WHEN** clients interact with workflows
**THEN** the following endpoints SHALL be available:

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/v1/workflows/reflection` | Start reflection workflow |
| GET | `/api/v1/workflows/{id}/status` | Get workflow status |
| POST | `/api/v1/workflows/{id}/approve` | Approve workflow step (human-in-the-loop) |

---

## 3. Test Coverage

| Test ID | Description | Reference |
|---------|-------------|-----------|
| RG-01 | Reflection graph: coder -> reviewer -> pass (1 iteration) | FR-046 §2.4 |
| RG-02 | Reflection graph: coder -> reviewer -> reject -> retry (2 iterations) | FR-046 §2.4 |
| RG-03 | Reflection graph: max iterations reached -> fail | FR-046 §2.4 |
| RG-04 | enqueue_async returns immediately (non-blocking) | D-066-03 |
| RG-05 | Workflow checkpoint saved in metadata_ JSONB | D-066-02 |
| RG-06 | WorkflowMetadata Pydantic validation on read/write | D-066-02 |
| RG-07 | JSONB size limit enforced (64KB) | D-066-02 |
| WR-01 | WorkflowResumer pub/sub fast path resumes workflow | D-066-05 |
| WR-02 | WorkflowResumer reconciler resumes missed events | D-066-05 |
| WR-03 | Stuck detection: >5min waiting auto-resumes | D-066-05 |
| WR-04 | OCC: concurrent resume -> 1 pass, 1 no-op | D-066-02 |
| WR-05 | Single instance: replicas=1 enforced | D-066-05 |
| ID-01 | Workflow step idempotency: duplicate step -> no-op | D-066-06 |
| ID-02 | Message enqueue idempotency: duplicate key -> existing ID | D-066-06 |
| ID-03 | Control plane idempotency: X-Idempotency-Key header | D-066-06 |
| CP-01 | Decision node refreshes from GET /gates/{id}/actions | D-066-01 |
| CP-02 | Control plane is TRUTH, LangGraph state is DRAFT | D-066-01 |

---

## 4. Dependencies

- `workflows/__init__.py` (new directory)
- `workflows/graph_state.py` (~60 LOC — ReflectionState, WorkflowMetadata Pydantic)
- `workflows/reflection_graph.py` (~200 LOC — async StateGraph, Postgres Checkpointer)
- `workflow_resumer.py` (~200 LOC — pub/sub + reconciler, OCC, single instance)
- `routes/workflows.py` (~120 LOC — POST /reflection, GET /status, POST /approve)
- Alembic migration (~30 LOC — partial index on metadata_ JSONB)
- `team_orchestrator.py` (modified, ~30 LOC — `enqueue_async()`)
- `main.py` (modified, ~5 LOC — register workflows router)
- `docker-compose.yml` (modified, ~10 LOC — workflow_resumer service)
- `langgraph>=0.2.0` in enterprise.txt
