---
sdlc_version: "6.1.1"
document_type: "Sprint Plan"
status: "APPROVED"
sprint: "219"
tier: "PROFESSIONAL"
stage: "04 - Build"
---

# Sprint 219 — P6 Agent Liveness + P5 Shared Workspace Foundation

**Sprint Duration**: April 2026
**Sprint Goal**: Implement agent heartbeat monitoring with recovery, and shared workspace with optimistic versioning and conflict resolution
**Status**: PLANNED
**Priority**: P1
**Framework**: SDLC 6.1.1
**ADRs**: ADR-069 (MTClaw Restructure), ADR-070 (CoPaw/AgentScope Pattern Adoption), ADR-072 (Shared Workspace Schema — to be written with this sprint)
**FRs**: FR-051 (Delegation Context Injection — extended)
**Previous Sprint**: [Sprint 218 — Skills Completion + Message Filtering](SPRINT-218-SKILLS-BOOTSTRAP.md)
**CTO Condition F2**: Plan for ~800 LOC actual. Defer `escalate_to_lead` conflict strategy to S220 if velocity constrained.

---

## Scope Change (PDR-001)

> **CTO APPROVED** — Scope pivoted from original plan per PDR-001 expert synthesis.
>
> **Original scope** (ADR-069): tsvector Migration + Deterministic Router (4-level cascade)
> **New scope** (ADR-070): P6 Agent Liveness (heartbeat) + P5 Shared Workspace Foundation
>
> **What changed**:
> - Deterministic Router **DEFERRED** to S222+ per PDR-001 priority
> - tsvector backfill for agent_definitions **DEFERRED** to S222+ (skill search uses skill_definitions.search_tsv already)
> - Agent Liveness heartbeat **ADDED** (CoPaw heartbeat pattern — stale detection + recovery)
> - Shared Workspace **ADDED** (CoPaw ReMe pattern — cross-agent artifact sharing)
>
> **Rationale**: Agent liveness (detecting stalled agents) and shared workspace (cross-agent
> artifact sharing) are critical for multi-agent team collaboration. Deterministic routing
> is a latency optimization (300ms → 0ms) that can wait; @mention routing already works.
>
> **NOTE (S222 correction)**: "@mention routing already works" above referred specifically to
> agent-to-agent @mention routing inside TeamOrchestrator (shipped Sprint 177). OTT
> user→agent @mention routing — i.e., a human typing `@pm` in Telegram/Zalo to directly
> address an EP-07 agent — was a separate gap that shipped in **Sprint 222**. The two
> scenarios are distinct: S177 = agent calls @agent inside TeamOrchestrator; S222 = OTT
> channel user types @agentname to directly invoke an EP-07 agent definition.

---

## Context

Sprint 218 completed the skills engine (per-agent grants + tsvector search) and added message
filtering/broadcast API. `agent_messages.metadata` JSONB column now exists for structured
data storage. ~119 cumulative tests passing.

Two CoPaw patterns are adopted in this sprint:

1. **Agent Liveness (P6)**: CoPaw uses a cron/heartbeat system to detect stalled agents and
   auto-recover conversations. SDLC Orchestrator ports this as Redis-based heartbeat keys with
   a background monitor task that runs every 30 seconds.

2. **Shared Workspace (P5 foundation)**: CoPaw's ReMe (Reference Memory) pattern enables
   cross-agent artifact sharing within a conversation. This sprint implements the data model
   and CRUD service. S220 adds the context_injector builder and history compaction integration.

This sprint also requires **ADR-072** (Shared Workspace Schema) to document the 3 conflict
resolution strategies and parent-child isolation rules.

---

## Sprint Summary

| Track | Scope | Est. LOC | Impact |
|-------|-------|----------|--------|
| A | Heartbeat service (Redis keys, MGET batch, recovery) | ~180 new | Stale agent detection + auto-recovery |
| B | Heartbeat monitor (background task, circuit breaker) | ~100 new | Continuous 30s scan, mass stall protection |
| C | Shared workspace table (Alembic migration) | ~60 migration | Conversation-scoped artifact storage |
| D | Shared workspace service (CRUD, optimistic versioning) | ~160 new | Cross-agent artifact sharing with conflict detection |
| E | Wire heartbeat into team_orchestrator + main.py lifespan | ~50 modify | Heartbeat recorded after each agent turn |
| F | Tests: heartbeat, workspace, conflict, recovery, cross-agent | ~250 new | Regression safety for all tracks |
| G | ADR-072: Shared Workspace Schema document | ~20 doc | 3 conflict strategies + parent-child isolation rules |
| **Total** | | **~800 LOC + ADR** | **Agent liveness + shared workspace operational** |

---

## Track A — Heartbeat Service

### A1: New service file

- NEW: `backend/app/services/agent_team/heartbeat_service.py` (~180 LOC)
- Class `HeartbeatService` with dependency injection for Redis client and DB session

### A2: record_heartbeat()

- `record_heartbeat(agent_id: UUID, conversation_id: UUID) -> None`
- Redis key: `hb:{agent_id}:{conversation_id}`
- Redis value: ISO 8601 timestamp
- TTL: 60 seconds (auto-expire = agent considered stale)
- Called after each agent turn in TeamOrchestrator

### A3: check_liveness()

- `check_liveness(agent_id: UUID, conversation_id: UUID) -> bool`
- Returns True if Redis key exists (agent is alive)
- Returns False if key expired or missing (agent is stale)

### A4: get_stale_agents()

- `get_stale_agents(agent_ids: list[UUID], conversation_id: UUID) -> list[UUID]`
- Uses Redis MGET for single round-trip (no N+1)
- Returns list of agent_ids whose heartbeat keys are missing/expired
- Efficient: 1 Redis call regardless of list size

### A5: recover_stale_conversation()

- `recover_stale_conversation(conversation_id: UUID, stale_agent_id: UUID) -> bool`
- **Idempotent**: Redis dedup key `recovery:{conversation_id}:{stale_agent_id}` with 5-minute TTL
- If dedup key exists: return False (already recovering, skip)
- If dedup key missing:
  1. Set dedup key in Redis (5-min TTL)
  2. UPDATE `agent_conversations` SET `status = 'stalled'` WHERE id = conversation_id
  3. INSERT system message: "Agent @{name} is unresponsive. Conversation paused for recovery."
  4. COMMIT
- Returns True if recovery initiated

---

## Track B — Heartbeat Monitor

### B1: New service file

- NEW: `backend/app/services/agent_team/heartbeat_monitor.py` (~100 LOC)
- Class `HeartbeatMonitor` — background async task

### B2: Background scan loop

- Runs every 30 seconds via `asyncio.create_task()` in FastAPI lifespan
- Task reference stored in `app.state.heartbeat_task` for clean shutdown
- On shutdown: `heartbeat_task.cancel()` with `asyncio.CancelledError` handling
- Follows existing pattern from `main.py` lifespan (WorkflowResumer at lines 71-201)

### B3: Scan logic

- Query all active conversations (status = 'active')
- For each conversation: get assigned agent_ids
- Call `get_stale_agents()` with batch MGET
- For each stale agent: call `recover_stale_conversation()`

### B4: Circuit breaker

- If >5 stalled agents detected in a single 60-second window:
  - Emit `agent.mass_stall` CRITICAL log
  - Skip recovery for remaining agents in this scan cycle
  - Reset counter after 60 seconds
- Purpose: prevent cascading recovery storms when infrastructure is degraded (Redis down, etc.)

---

## Track C — Shared Workspace Migration

### C1: Alembic migration

- File: `backend/alembic/versions/s219_001_workspace_heartbeat.py`
- `down_revision = "s218_001"`
- `revision = "s219_001"`

### C2: shared_workspace_items table

```sql
CREATE TABLE shared_workspace_items (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    conversation_id UUID NOT NULL REFERENCES agent_conversations(id) ON DELETE CASCADE,
    item_key VARCHAR(200) NOT NULL,
    item_value TEXT NOT NULL,
    item_type VARCHAR(20) NOT NULL DEFAULT 'text'
        CHECK (item_type IN ('text', 'code', 'diff', 'json', 'markdown', 'binary_ref')),
    version INTEGER NOT NULL DEFAULT 1,
    conflict_resolution VARCHAR(20) NOT NULL DEFAULT 'last_write_wins'
        CHECK (conflict_resolution IN ('last_write_wins', 'retry_3x', 'escalate_to_lead')),
    created_by UUID REFERENCES agent_definitions(id) ON DELETE SET NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE(conversation_id, item_key)
);
```

### C3: Design decisions

- **Conversation-scoped**: Workspace dies with conversation. Fits multi-agent team short tasks.
  Cross-conversation workspace (project_workspace_items) deferred to S222+.
- **Soft delete**: `version = -1` marks deleted items. All queries include `WHERE version > 0`.
- **Conflict resolution**: Per-item setting, defaulting to `last_write_wins`.
  - `last_write_wins`: UPDATE always succeeds (no version check)
  - `retry_3x`: Optimistic locking with 3 retry attempts before error
  - `escalate_to_lead`: Raise `VersionConflictError` for human/lead resolution
  - **CTO F2 fallback**: `escalate_to_lead` implementation can be deferred to S220 if velocity constrained. `last_write_wins` and `retry_3x` are P0.
- **Parent-child isolation**: Children READ parent workspace via `parent_conversation_id` chain.
  WRITE only to own conversation's workspace. Prevents cross-delegation conflicts.

### C4: Indexes

- B-tree on `conversation_id` for per-conversation lookups (covered by UNIQUE already)
- No GIN index needed (item_key is simple varchar lookup)

---

## Track D — Shared Workspace Service

### D1: New model file

- NEW: `backend/app/models/shared_workspace.py` (~50 LOC)
- SQLAlchemy model with UUID PK, FKs, CHECK constraints
- `to_dict()` includes 50-char preview of item_value

### D2: New service file

- NEW: `backend/app/services/agent_team/shared_workspace.py` (~160 LOC)
- Class `SharedWorkspaceService` with dependency injection for DB session

### D3: put()

- `put(conversation_id, item_key, item_value, item_type, created_by, expected_version=None) -> SharedWorkspaceItem`
- If item_key doesn't exist: INSERT with version=1
- If item_key exists:
  - `last_write_wins`: UPDATE unconditionally, increment version
  - `retry_3x`: `UPDATE ... WHERE version = :expected_version` — if 0 rows affected, retry up to 3x with fresh read
  - `escalate_to_lead`: `UPDATE ... WHERE version = :expected_version` — if 0 rows affected, raise `VersionConflictError`
- Uses SELECT FOR UPDATE for serialization in concurrent writes

### D4: get()

- `get(conversation_id, item_key) -> SharedWorkspaceItem | None`
- Includes `WHERE version > 0` (exclude soft-deleted)
- If parent_conversation_id exists and item not found locally: traverse parent chain (READ only)

### D5: list_keys()

- `list_keys(conversation_id) -> list[dict]`
- Returns `[{"key": str, "type": str, "version": int, "preview": str, "created_by": UUID}]`
- Preview: first 50 chars of item_value, truncated with '...' if longer
- Excludes soft-deleted items (version > 0)

### D6: delete()

- `delete(conversation_id, item_key) -> bool`
- Soft delete: `UPDATE SET version = -1`
- Returns True if item existed and was deleted

### D7: get_active_keys()

- `get_active_keys(conversation_id) -> list[str]`
- Returns just the key names (no values) for active items
- Used by S220 history compaction to preserve workspace references

---

## Track E — Wiring

### E1: Wire heartbeat into TeamOrchestrator

- MODIFY: `backend/app/services/agent_team/team_orchestrator.py`
- After each agent turn completes:
  ```python
  await self.heartbeat_service.record_heartbeat(agent_id, conversation_id)
  ```
- Inject `HeartbeatService` via constructor (testable, no globals)

### E2: Wire monitor into main.py lifespan

- MODIFY: `backend/app/main.py` (lifespan context manager, lines 71-201)
- Before yield (startup):
  ```python
  monitor = HeartbeatMonitor(redis_client, db_session_factory)
  app.state.heartbeat_task = asyncio.create_task(monitor.run())
  ```
- After yield (shutdown):
  ```python
  if hasattr(app.state, 'heartbeat_task'):
      app.state.heartbeat_task.cancel()
      try:
          await app.state.heartbeat_task
      except asyncio.CancelledError:
          pass
  ```
- Follows existing WorkflowResumer pattern in same lifespan

### E3: Register SharedWorkspaceItem model

- MODIFY: `backend/app/models/__init__.py` — add import for SharedWorkspaceItem

---

## Track G — ADR-072: Shared Workspace Schema

### G1: ADR document

- NEW: `docs/02-design/01-ADRs/ADR-072-Shared-Workspace-Schema.md`
- Documents the 3 conflict resolution strategies:
  - `last_write_wins`: unconditional overwrite (default)
  - `retry_3x`: optimistic locking with 3 retry attempts
  - `escalate_to_lead`: raise VersionConflictError for human/lead resolution
- Documents parent-child isolation rules:
  - Children READ parent workspace via `parent_conversation_id` chain
  - Children WRITE only to own conversation's workspace
  - Prevents cross-delegation conflicts
- Documents conversation-scoped design rationale (vs. project-scoped, deferred to S222+)

---

## Track F — Tests

File: `backend/tests/unit/test_sprint219_heartbeat_workspace.py`

### F1: Heartbeat tests

| Test case | Expected |
|-----------|----------|
| record_heartbeat → check_liveness | True (key exists) |
| Expire key (TTL elapsed) → check_liveness | False (key gone) |
| get_stale_agents: 1 expired, 1 active | Only expired agent returned |
| get_stale_agents: empty list input | Empty list returned |
| recover_stale: UPDATE + INSERT system msg + commit | 3 DB calls, dedup key set in Redis |
| recover_stale 2nd time (Redis dedup key exists) | No additional DB calls (idempotent), returns False |
| recover_stale: conversation not found | Raises ValueError |

### F2: Heartbeat monitor tests

| Test case | Expected |
|-----------|----------|
| Monitor scan finds 1 stale agent | recover_stale_conversation called once |
| Monitor scan finds 0 stale agents | No recovery calls |
| Circuit breaker: 6 stalled in 60s | CRITICAL log emitted, remaining skipped |
| Monitor shutdown: task cancelled | asyncio.CancelledError handled cleanly |

### F3: Workspace CRUD tests

| Test case | Expected |
|-----------|----------|
| put/get round-trip | Content preserved, version=1 |
| put existing key (last_write_wins) | Version incremented, no error |
| put existing key (retry_3x) wrong version | Retries up to 3x, succeeds on match |
| put existing key (retry_3x) all retries fail | VersionConflictError raised |
| list_keys: soft-deleted excluded | version=-1 items not visible |
| list_keys: preview truncated at 50 chars | Ends with '...' |
| delete: soft delete sets version=-1 | Item invisible to get/list_keys |
| delete: non-existent key | Returns False |

### F4: Workspace cross-agent tests

| Test case | Expected |
|-----------|----------|
| Agent A writes, Agent B reads same key | Content identical, created_by = A's agent_id |
| Parent workspace item readable by child | Child get() traverses parent chain |
| Child cannot WRITE to parent workspace | Only reads parent, writes to own |

### F5: Integration + regression tests

| Test case | Expected |
|-----------|----------|
| Full flow: record heartbeat → workspace put → list_keys | All steps complete without errors |
| 119 existing S216-S218 tests still pass | No regressions |

**Test target**: +~45 tests → cumulative ~164

---

## Definition of Done

- [ ] `HeartbeatService` with record/check/get_stale/recover methods
- [ ] Redis key format: `hb:{agent_id}:{conversation_id}` with 60s TTL
- [ ] Recovery idempotent via 5-min Redis dedup key
- [ ] `HeartbeatMonitor` background task in lifespan with cancel-on-shutdown
- [ ] Circuit breaker: >5 stalled in 60s → CRITICAL log + skip
- [ ] `shared_workspace_items` table with UNIQUE(conversation_id, item_key)
- [ ] Soft delete via version=-1, all queries `WHERE version > 0`
- [ ] `last_write_wins` and `retry_3x` conflict strategies operational
- [ ] `escalate_to_lead` operational OR deferred to S220 per CTO F2
- [ ] Parent-child isolation: child READs parent, WRITEs to own only
- [ ] `SharedWorkspaceItem` model registered in `models/__init__.py`
- [ ] Heartbeat wired into TeamOrchestrator (after each agent turn)
- [ ] Heartbeat monitor wired into main.py lifespan
- [ ] All Sprint 219 tests passing (~45 new tests)
- [ ] 119 existing S216-S218 tests still passing (no regressions)
- [ ] Alembic chain: s218_001 → s219_001
- [ ] ADR-072 written (Shared Workspace Schema)

---

## Risks

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| S219 LOC exceeds velocity (~800 LOC) | Medium | Medium | CTO F2: defer escalate_to_lead to S220 (saves ~80 LOC) |
| Redis unavailable breaks heartbeat | Medium | Medium | Heartbeat is best-effort; conversation continues without it. Monitor logs warning |
| Optimistic versioning creates retry storms | Low | Medium | retry_3x has 3-attempt cap; SELECT FOR UPDATE serializes concurrent writes |
| Workspace items grow unbounded | Low | Low | Conversation-scoped; workspace dies with conversation. No long-term growth |
| version=-1 soft delete queries miss edge case | Low | Medium | All queries use `WHERE version > 0`; test coverage for soft-delete exclusion |
| Circuit breaker threshold too low (5) | Low | Low | Configurable via settings; 5 is conservative default |

---

## Dependencies

- **Upstream**: Sprint 218 complete (skill_agent_grants, metadata JSONB, message filtering)
- **Downstream**: Sprint 220 (workspace context builder, history compaction) + Sprint 221 (consensus, parallel)
- **Infrastructure**: Redis 7.2 (heartbeat keys, dedup keys), PostgreSQL (shared_workspace_items table)
- **References**: ADR-070 (CoPaw Pattern Adoption), ADR-072 (Shared Workspace Schema), CoPaw heartbeat system, CoPaw ReMe pattern

---

## Key Files

| File | Action | LOC (est.) |
|------|--------|------------|
| `backend/alembic/versions/s219_001_workspace_heartbeat.py` | NEW | ~60 |
| `backend/app/services/agent_team/heartbeat_service.py` | NEW | ~180 |
| `backend/app/services/agent_team/heartbeat_monitor.py` | NEW | ~100 |
| `backend/app/models/shared_workspace.py` | NEW | ~50 |
| `backend/app/services/agent_team/shared_workspace.py` | NEW | ~160 |
| `backend/app/services/agent_team/team_orchestrator.py` | MODIFY | +30 |
| `backend/app/main.py` | MODIFY | +20 |
| `backend/app/models/__init__.py` | MODIFY | +1 |
| `backend/tests/unit/test_sprint219_heartbeat_workspace.py` | NEW | ~250 |
| `docs/02-design/01-ADRs/ADR-072-Shared-Workspace-Schema.md` | NEW | ~20 (doc) |
