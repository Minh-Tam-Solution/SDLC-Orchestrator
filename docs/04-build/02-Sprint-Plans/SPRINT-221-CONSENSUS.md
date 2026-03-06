---
sdlc_version: "6.1.1"
document_type: "Sprint Plan"
status: "APPROVED"
sprint: "221"
tier: "PROFESSIONAL"
stage: "04 - Build"
---

# Sprint 221 — P2 Group Consensus

**Sprint Duration**: May 2026
**Sprint Goal**: Implement multi-agent voting/deliberation with quorum logic, state machine, and @vote command integration
**Status**: PLANNED
**Priority**: P1
**Framework**: SDLC 6.1.1
**ADRs**: ADR-070 (CoPaw/AgentScope Pattern Adoption)
**Previous Sprint**: [Sprint 219 — Agent Liveness + Shared Workspace](SPRINT-219-ROUTER-TSVECTOR.md)
**Parallelism**: Can run parallel with S220 after S219 completes
**CTO Condition F3**: Document @vote command syntax BEFORE implementation

---

## INVARIANT

**Consensus result = evidence returned to EP-07. EP-07 gate still decides PASS/FAIL.**

Group consensus is deliberation advisory — it **CANNOT bypass gates**. If 3 agents vote unanimous
'approve' on a G3-gated task, human approval is still required if G3 policy demands it.
Consensus provides structured input for gate evaluation, not a replacement for it.

---

## Context

Sprint 219 delivered agent liveness and shared workspace foundation. Sprint 220 (parallel)
adds workspace context builders and approval feedback. This sprint completes the final CoPaw
pattern: group consensus.

CoPaw's voting system + AgentScope's MsgHub broadcast pattern combine into a multi-agent
deliberation mechanism. Agents can create voting sessions on topics (code review, design
decisions, security approval), cast votes with reasoning, and reach quorum decisions that
become evidence for EP-07 gate evaluation.

---

## @vote Command Syntax (CTO F3 — Document Before Implementation)

### Creation

```
@vote create "Should we approve the auth refactor?" --quorum majority --voters @coder @reviewer @tester
```

| Parameter | Required | Default | Description |
|-----------|----------|---------|-------------|
| topic | Yes | — | Quoted string describing the vote topic |
| --quorum | No | majority | One of: majority, unanimous, threshold |
| --voters | No | all team members | Space-separated @agent mentions |
| --timeout | No | 300 | Seconds before auto-timeout |
| --threshold | No | 0.67 | Only used when quorum=threshold |

### Voting

```
@vote approve "Looks good, well-structured code"
@vote reject "Missing input validation on line 42"
@vote abstain "Not enough context to evaluate"
```

| Parameter | Required | Description |
|-----------|----------|-------------|
| action | Yes | One of: approve, reject, abstain |
| reasoning | No | Quoted string explaining the vote |

### Management

```
@vote status           # Show all active votes in this conversation
@vote cancel <id>      # Cancel a vote session (creator or lead only)
```

### Who Can Create/Cancel

- **Create**: Any agent in the conversation
- **Cancel**: Session creator OR team lead agent only
- **Vote**: Only agents listed in `required_voters` (enforced at DB level)

---

## Sprint Summary

| Track | Scope | Est. LOC | Impact |
|-------|-------|----------|--------|
| A | Consensus tables: sessions + votes (Alembic migration) | ~60 migration | Persistent voting state machine |
| B | Consensus service (create, vote, quorum, close, timeout) | ~200 new | Multi-agent deliberation with 3 quorum types |
| C | Consensus context builder (render_active_sessions) | ~60 new | Agents see active votes in system prompt |
| D | Wire @vote command into TeamOrchestrator | ~60 modify | Command parsing + session lifecycle |
| E | Tests: quorum logic, race conditions, timeout, context | ~120 new | Regression safety for all tracks |
| **Total** | | **~500 LOC** | **Group consensus operational** |

---

## Track A — Consensus Migration

### A1: Alembic migration

- File: `backend/alembic/versions/s221_001_consensus.py`
- `down_revision = "s219_001"` — S220 has no Alembic migration (no new tables, no ALTER).
  Both S220 and S221 are parallel after S219. Since S220 is code-only (no schema changes),
  the Alembic chain is linear: s218_001 → s219_001 → s221_001. No merge conflict.
- `revision = "s221_001"`

### A2: Migration order (CTO F1 — forward FK fix)

**CRITICAL**: `consensus_sessions.decided_by_vote_id` references `consensus_votes(id)`, but
`consensus_votes` doesn't exist when `consensus_sessions` is created. PostgreSQL rejects
forward FK references even with DEFERRABLE. The migration MUST use 3-step order:

**Step 1**: Create `consensus_sessions` WITHOUT the `fk_decided_vote` constraint:

```sql
CREATE TABLE consensus_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    conversation_id UUID NOT NULL REFERENCES agent_conversations(id) ON DELETE CASCADE,
    topic VARCHAR(200) NOT NULL,
    created_by UUID NOT NULL REFERENCES agent_definitions(id) ON DELETE CASCADE,
    quorum_type VARCHAR(20) NOT NULL DEFAULT 'majority'
        CHECK (quorum_type IN ('majority', 'unanimous', 'threshold')),
    required_voters JSONB NOT NULL DEFAULT '[]'::jsonb,
    threshold_pct NUMERIC(3,2) DEFAULT 0.67,
    timeout_seconds INTEGER NOT NULL DEFAULT 300,
    status VARCHAR(20) NOT NULL DEFAULT 'open'
        CHECK (status IN ('open', 'voting', 'decided', 'timeout', 'cancelled')),
    result JSONB,
    decided_by_vote_id UUID,  -- FK added in Step 3
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    closed_at TIMESTAMPTZ
);
```

**Step 2**: Create `consensus_votes` with session_id FK → consensus_sessions:

```sql
CREATE TABLE consensus_votes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID NOT NULL REFERENCES consensus_sessions(id) ON DELETE CASCADE,
    voter_agent_id UUID NOT NULL REFERENCES agent_definitions(id) ON DELETE CASCADE,
    vote VARCHAR(10) NOT NULL CHECK (vote IN ('approve', 'reject', 'abstain')),
    reasoning TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE(session_id, voter_agent_id)
);
```

**Step 3**: Add forward FK constraint now that both tables exist:

```sql
ALTER TABLE consensus_sessions
    ADD CONSTRAINT fk_decided_vote
    FOREIGN KEY (decided_by_vote_id)
    REFERENCES consensus_votes(id)
    ON DELETE SET NULL
    DEFERRABLE INITIALLY DEFERRED;
```

- `UNIQUE(session_id, voter_agent_id)` prevents double-vote at DB level
- `decided_by_vote_id` enables compare-and-swap for quorum race condition (CTO C4)
- `DEFERRABLE INITIALLY DEFERRED` allows INSERT session + INSERT vote + UPDATE session in one transaction

### A4: Indexes

- B-tree on `consensus_sessions.conversation_id` for per-conversation lookups
- B-tree on `consensus_votes.session_id` for vote counting

---

## Track B — Consensus Service

### B1: New service file

- NEW: `backend/app/services/agent_team/consensus_service.py` (~200 LOC)
- Class `ConsensusService` with dependency injection for DB session

### B2: create_session()

- `create_session(conversation_id, topic, created_by, quorum_type, required_voters, timeout_seconds, threshold_pct) -> ConsensusSession`
- Validates quorum_type is one of: majority, unanimous, threshold
- Sets status = 'open'
- Returns created session with ID

### B3: cast_vote()

- `cast_vote(session_id, voter_agent_id, vote, reasoning) -> ConsensusVote`
- Validates voter is in required_voters list
- Validates session is 'open' or 'voting'
- INSERT vote (UNIQUE constraint prevents double-vote)
- After insert: auto-check quorum
- **Race condition protection** (CTO C4):
  ```sql
  SELECT FOR UPDATE FROM consensus_sessions WHERE id = :session_id
  -- Check quorum
  UPDATE consensus_sessions
  SET status = 'decided', result = :result, decided_by_vote_id = :vote_id, closed_at = now()
  WHERE id = :session_id AND decided_by_vote_id IS NULL
  ```
  - `decided_by_vote_id IS NULL` check prevents two concurrent votes from both closing the session
- On first vote: transition status open → voting

### B4: check_quorum()

- `check_quorum(session_id) -> QuorumResult`
- Returns: `QuorumResult(reached: bool, decision: str | None, votes_for: int, votes_against: int, votes_abstain: int)`

| Type | APPROVE condition | REJECT condition |
|------|-------------------|------------------|
| majority | >50% of required_voters approve | <=50% (after all have voted) |
| unanimous | 100% approve, 0 reject | Any 1 reject |
| threshold | >= threshold_pct approve | < threshold_pct (after all have voted) |

- For majority and threshold: quorum only "reached" when enough votes are cast to determine outcome
  (e.g., 2/3 approve = majority reached immediately; 1/3 approve + 1/3 reject = wait for 3rd vote)

### B5: close_session()

- `close_session(session_id, reason: str) -> ConsensusSession`
- Sets status = 'cancelled', closed_at = now()
- Only callable by session creator or team lead (authorization check)

### B6: timeout_expired_sessions()

- `timeout_expired_sessions() -> int`
- Finds sessions where `status IN ('open', 'voting') AND created_at + timeout_seconds < now()`
- Sets status = 'timeout', closed_at = now()
- Returns count of timed-out sessions
- Called from heartbeat monitor scan (piggybacks on existing 30s background task)

---

## Track C — Consensus Context Builder

### C1: render_active_sessions()

- NEW function in `consensus_service.py`:
  `render_active_sessions(conversation_id: UUID) -> str`
- Called by context_injector's `build_consensus_md()` via lazy import (S220)
- Returns XML block:
  ```xml
  <active_votes>
  ## Active Votes
  1. "Should we approve the auth refactor?" (majority, 2/3 voted)
     - @coder: approve | @reviewer: approve | @tester: pending
     Cast your vote using: @vote approve/reject/abstain "reasoning"
  </active_votes>
  ```
- Returns `""` if no active sessions (status in 'open', 'voting')

---

## Track D — Wire @vote Command

### D1: Command parsing

- MODIFY: `backend/app/services/agent_team/team_orchestrator.py`
- Parse `@vote` prefix in incoming messages
- Subcommands: create, approve, reject, abstain, status, cancel
- Route to appropriate ConsensusService method

### D2: Quorum result broadcast

- When quorum is reached (decided/timeout/cancelled):
  - Broadcast system message to all team members:
    ```
    Vote decided: "Should we approve the auth refactor?"
    Result: APPROVED (majority 2/3)
    Votes: @coder approve, @reviewer approve, @tester reject
    ```
  - Uses `post_broadcast()` from message_queue (S218)

### D3: Auto-timeout integration

- Add `timeout_expired_sessions()` call to heartbeat monitor scan
- Piggybacks on existing 30s background task — no new background process

---

## Track E — Tests

File: `backend/tests/unit/test_sprint221_consensus.py`

### E1: Session lifecycle tests

| Test case | Expected |
|-----------|----------|
| Create session: defaults | status='open', quorum_type='majority' |
| Create session: invalid quorum_type | ValueError raised |
| Create session: custom timeout | timeout_seconds preserved |

### E2: Voting + quorum tests

| Test case | Expected |
|-----------|----------|
| Cast vote: 1st vote → status | open → voting |
| Cast vote: non-required voter | Rejected (not in required_voters) |
| Majority 2/3 approve | status='decided', result.decision='approve' |
| Majority 1/3 approve, 2/3 reject | status='decided', result.decision='reject' |
| Majority: 1 approve, 1 reject (tie, 1 pending) | Still 'voting' (not enough to decide) |
| Unanimous: 3/3 approve | status='decided', decision='approve' |
| Unanimous: 1 reject in 3 votes | Immediate 'decided', decision='reject' |
| Threshold (0.67): 2/3 approve | status='decided', decision='approve' |
| Threshold (0.67): 1/3 approve | status='decided', decision='reject' (after all voted) |

### E3: Concurrency + constraint tests

| Test case | Expected |
|-----------|----------|
| Double vote same agent | UNIQUE constraint IntegrityError |
| Race condition: concurrent votes | SELECT FOR UPDATE serializes; only one sets decided_by_vote_id |

### E4: Timeout + cancel tests

| Test case | Expected |
|-----------|----------|
| Timeout: session past 300s | status='timeout' |
| Cancel by creator | status='cancelled' |
| Cancel by non-creator, non-lead | Rejected (authorization error) |

### E5: Context builder tests

| Test case | Expected |
|-----------|----------|
| Active sessions → `<active_votes>` | Contains topic + vote counts |
| No active sessions | Returns `""` |

### E6: Full flow + regression

| Test case | Expected |
|-----------|----------|
| Full flow: create → 3 agents vote → quorum → broadcast | System message visible to all members |
| 194 existing S216-S220 tests still pass (36+38+45+45+30) | No regressions |

**Test target**: +~35 tests → cumulative ~229

---

## Definition of Done

- [ ] `consensus_sessions` table with status state machine + quorum_type CHECK
- [ ] `consensus_votes` table with UNIQUE(session_id, voter_agent_id)
- [ ] `ConsensusService.create_session()` validates quorum_type
- [ ] `cast_vote()` transitions open → voting on first vote
- [ ] Majority quorum: >50% approve = decided
- [ ] Unanimous quorum: 1 reject = immediate reject
- [ ] Threshold quorum: >= threshold_pct = approve
- [ ] Race condition: SELECT FOR UPDATE + decided_by_vote_id IS NULL check
- [ ] Double-vote prevented by UNIQUE constraint
- [ ] `close_session()` only by creator or lead
- [ ] `timeout_expired_sessions()` sets status='timeout' (not 'cancelled')
- [ ] `render_active_sessions()` produces `<active_votes>` XML
- [ ] @vote command parsed by TeamOrchestrator
- [ ] Quorum result broadcast via post_broadcast()
- [ ] Timeout check piggybacks on heartbeat monitor
- [ ] Consensus is ADVISORY ONLY — does NOT bypass EP-07 gates
- [ ] All Sprint 221 tests passing (~35 new tests)
- [ ] 194 existing S216-S220 tests still passing (36+38+45+45+30 — no regressions)
- [ ] Alembic chain: s219_001 → s221_001
- [ ] @vote command syntax documented (this document — CTO F3 ✅)

---

## Risks

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| S220/S221 parallel merge conflict on context_injector.py | Low | Medium | S220 adds injection hook with lazy import; S221 provides render logic in consensus_service.py — no direct conflict |
| Race condition on quorum close | Low | High | SELECT FOR UPDATE + decided_by_vote_id IS NULL compare-and-swap |
| @vote command conflicts with MAX_COMMANDS=10 | Medium | Medium | @vote is a message prefix parsed by orchestrator, NOT a registered command — does not count toward MAX_COMMANDS |
| Timeout check latency (30s scan interval) | Low | Low | Acceptable: 300s default timeout means 30s granularity is fine |
| Consensus misinterpreted as binding | Medium | Medium | INVARIANT documented in this sprint plan, ADR-070, and agent system prompts |

---

## Dependencies

- **Upstream**: Sprint 219 complete (heartbeat monitor for timeout piggyback, shared workspace for context)
- **Upstream optional**: Sprint 220 (context_injector hook) — if S220 not complete, consensus still works but agents don't see `<active_votes>` in prompt
- **Downstream**: None — S221 is the final CoPaw pattern sprint
- **Infrastructure**: PostgreSQL (consensus_sessions + consensus_votes tables)
- **References**: ADR-070 (CoPaw Pattern Adoption), CoPaw voting system, AgentScope MsgHub broadcast pattern

---

## Key Files

| File | Action | LOC (est.) |
|------|--------|------------|
| `backend/alembic/versions/s221_001_consensus.py` | NEW | ~60 |
| `backend/app/models/consensus_session.py` | NEW | ~60 |
| `backend/app/services/agent_team/consensus_service.py` | NEW | ~200 |
| `backend/app/services/agent_team/team_orchestrator.py` | MODIFY | +60 |
| `backend/app/models/__init__.py` | MODIFY | +2 |
| `backend/tests/unit/test_sprint221_consensus.py` | NEW | ~120 |
