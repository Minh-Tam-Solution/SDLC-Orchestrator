---
sdlc_version: "6.1.1"
document_type: "Sprint Plan"
status: "APPROVED"
sprint: "220"
tier: "PROFESSIONAL"
stage: "04 - Build"
---

# Sprint 220 — P5 Memory Enhancement + P4 Approval Feedback

**Sprint Duration**: April-May 2026
**Sprint Goal**: Add workspace and consensus context builders, workspace-aware history compaction, and structured approval feedback with analytics
**Status**: PLANNED
**Priority**: P1
**Framework**: SDLC 6.1.1
**ADRs**: ADR-070 (CoPaw/AgentScope Pattern Adoption)
**Previous Sprint**: [Sprint 219 — Agent Liveness + Shared Workspace](SPRINT-219-ROUTER-TSVECTOR.md)
**Parallelism**: Can run parallel with S221 after S219 completes
**CTO Condition F1**: Add `conversation_id: UUID | None = None` to `inject_context()` ONCE — all 3 new builders share it

---

## Context

Sprint 219 delivered agent liveness (heartbeat + monitor + recovery) and the shared workspace
foundation (CRUD + optimistic versioning + conflict resolution). ~164 cumulative tests passing.

Two CoPaw patterns are completed in this sprint:

1. **Shared Memory enhancement (P5 completion)**: The workspace data model exists from S219.
   This sprint adds the context_injector builder (`<workspace>` XML block) so agents SEE
   workspace contents in their system prompt, plus workspace-aware history compaction that
   preserves workspace key references during message summarization.

2. **Human-in-the-Loop feedback (P4)**: CoPaw's approval pattern supports structured feedback
   text alongside approve/reject actions. Currently SDLC Orchestrator approvals are binary.
   This sprint adds `approve_with_feedback()` and `reject_with_feedback()` with `<human_feedback>`
   XML injection into the agent's next turn.

Additionally, the consensus context builder (`<active_votes>` block) is implemented here but
its render logic lives in `consensus_service.py` (S221) to avoid circular imports. S220
provides the injection hook in context_injector; S221 provides the rendering.

---

## Sprint Summary

| Track | Scope | Est. LOC | Impact |
|-------|-------|----------|--------|
| A | Context injector: workspace + consensus builders, conversation_id param | ~80 modify | Agents see workspace items + active votes in system prompt |
| B | Workspace-aware history compaction | ~80 modify | Workspace key references preserved during summarization |
| C | Approval feedback service (approve/reject with text) | ~120 new | Structured feedback loop replaces binary approve/reject |
| D | Approval analytics (rate, response time p50/p95) | ~80 new | Metrics for approval workflow performance |
| E | Tests: builders, compaction, feedback, analytics | ~140 new | Regression safety for all tracks |
| **Total** | | **~500 LOC** | **Shared memory complete + approval feedback operational** |

---

## Track A — Context Injector Enhancement

### A1: Add conversation_id parameter (CTO F1)

- MODIFY: `backend/app/services/agent_team/context_injector.py`
- Change `inject_context()` signature ONCE:
  ```python
  async def inject_context(
      self, agent_id: UUID, team_id: UUID | None,
      system_prompt: str,
      conversation_id: UUID | None = None  # NEW — CTO F1
  ) -> str:
  ```
- All 3 new builders (workspace, feedback, consensus) share this parameter
- Existing builders (delegation, team, availability, skills) unaffected — they don't use conversation_id

### A2: build_workspace_md(conversation_id)

- 5th context builder in context_injector
- Tag: `<workspace>`
- Content: list of active workspace items with key, type, 50-char preview
- All values `xml_escape()`d
- Token budget: <= 500 tokens (~1,500 chars)
- If budget exceeded: truncate with notice "... and N more items"
- Returns `""` if no active items (no empty XML block injected)

### A3: build_consensus_md(conversation_id)

- 6th context builder — injection hook only
- Calls `consensus_service.render_active_sessions(conversation_id)` if available
- Uses lazy import to avoid circular dependency with S221:
  ```python
  try:
      from ..consensus_service import render_active_sessions
      return render_active_sessions(conversation_id)
  except ImportError:
      return ""  # S221 not deployed yet
  ```
- Tag: `<active_votes>` (rendered by consensus_service)
- Returns `""` if no active consensus sessions or S221 not yet deployed

---

## Track B — Workspace-Aware History Compaction

### B1: Extract workspace keys from text

- MODIFY: `backend/app/services/agent_team/history_compactor.py`
- `extract_workspace_keys_from_text(text: str) -> list[str]`
- Regex pattern: `(\w+)/(\w[\w.-]+)` — matches `{agent}/{artifact}` format
- Examples:
  - `"coder/auth_fix.diff reviewed"` → `["coder/auth_fix.diff"]`
  - `"reviewer/coverage_report uploaded"` → `["reviewer/coverage_report"]`

### B2: compact_with_workspace_preservation()

- `compact_with_workspace_preservation(messages, conversation_id) -> CompactionResult`
- Cross-checks extracted keys against `SharedWorkspaceService.get_active_keys(conversation_id)`
- Only preserves references to keys that still exist (active, version > 0)
- Soft-deleted keys (version=-1) excluded from preservation
- Compaction metadata: `{"workspace_keys": [...], "workspace_key_count": N}`

---

## Track C — Approval Feedback Service

### C1: New service file

- NEW: `backend/app/services/agent_team/approval_feedback.py` (~120 LOC)
- Class `ApprovalFeedbackService` with dependency injection for DB session

### C2: approve_with_feedback()

- `approve_with_feedback(token: str, feedback_text: str) -> AgentMessage`
- Validates magic link token (existing magic_link_service)
- Stores feedback in `agent_messages.metadata_["approval_feedback"]`:
  ```json
  {
    "action": "approve",
    "feedback": "Looks good, but consider edge case X",
    "timestamp": "2026-04-15T10:30:00Z"
  }
  ```
- Uses `agent_messages.metadata` JSONB column (added in S218)

### C3: reject_with_feedback()

- `reject_with_feedback(token: str, reason: str) -> AgentMessage`
- Stores rejection in metadata:
  ```json
  {
    "action": "reject",
    "feedback": "Missing security validation for user input",
    "timestamp": "2026-04-15T10:30:00Z"
  }
  ```
- Injects `<human_feedback>` XML into next agent turn:
  ```xml
  <human_feedback>
  Your previous output was rejected.
  Reason: Missing security validation for user input
  Please revise your approach and try again.
  </human_feedback>
  ```

### C4: Feedback injection into agent context

- After rejection, a system message is inserted into the conversation with the
  `<human_feedback>` XML block
- The agent's next turn sees this feedback in conversation history
- Approval feedback is informational (no system message injection needed)

---

## Track D — Approval Analytics

### D1: New service file

- NEW: `backend/app/services/agent_team/approval_analytics.py` (~80 LOC)
- Class `ApprovalAnalyticsService` with dependency injection for DB session

### D2: get_approval_rate()

- `get_approval_rate(project_id: UUID, days: int = 30) -> ApprovalStats`
- Returns:
  ```python
  @dataclass
  class ApprovalStats:
      total: int
      approved: int
      rejected: int
      rate: float  # approved / total
      period_days: int
  ```
- Uses `project_id` (not `team_id` — doesn't exist on agent_conversations)
- Queries `agent_messages` WHERE metadata contains approval_feedback AND conversation's project_id matches

### D3: get_avg_response_time()

- `get_avg_response_time(project_id: UUID, days: int = 30) -> ResponseTimeStats`
- Returns p50 and p95 using PostgreSQL `PERCENTILE_CONT`:
  ```sql
  SELECT
    PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY response_seconds) AS p50,
    PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY response_seconds) AS p95
  FROM approval_response_times_view
  WHERE project_id = :project_id AND created_at > now() - interval ':days days'
  ```
- No in-memory approximation — pure SQL aggregation

---

## Track E — Tests

File: `backend/tests/unit/test_sprint220_memory_feedback.py`

### E1: Context builder tests

| Test case | Expected |
|-----------|----------|
| Workspace context with 3 items → `<workspace>` block | Tags present, key names correct |
| Workspace context with 0 items | `""` returned, no injection |
| Workspace preview > 50 chars | Truncated with '...' |
| Consensus builder with no S221 module | Returns `""` (lazy import fallback) |
| inject_context with conversation_id | All 3 new builders called with conversation_id |
| inject_context without conversation_id | Existing 4 builders work, 3 new builders return `""` |

### E2: History compaction tests

| Test case | Expected |
|-----------|----------|
| extract keys: 'coder/diff reviewed' | `['coder/diff']` returned |
| extract keys: no workspace refs in text | Empty list |
| Compaction: active keys preserved | workspace_keys in metadata |
| Compaction: soft-deleted key not in messages | Excluded from workspace_keys |
| Compaction: key in text but not in workspace | Not preserved (stale reference) |

### E3: Approval feedback tests

| Test case | Expected |
|-----------|----------|
| approve_with_feedback: feedback stored in metadata | `metadata["approval_feedback"]["action"] == "approve"` |
| reject_with_feedback: `<human_feedback>` injected | System message in conversation |
| reject_with_feedback: metadata stored | `metadata["approval_feedback"]["action"] == "reject"` |
| Invalid token → approve_with_feedback | ValueError: 'not found' |
| Empty feedback text | Stored with empty string (not None) |

### E4: Analytics tests

| Test case | Expected |
|-----------|----------|
| Approval rate: 18/20 approved | rate = 0.9 |
| Approval rate: 0 approvals | rate = 0.0 |
| Response time p50/p95: synthetic data | Correct percentiles |
| Analytics with no data | Returns zeros |

### E5: Regression

| Test case | Expected |
|-----------|----------|
| 164 existing S216-S219 tests still pass | No regressions |

**Test target**: +~30 tests → cumulative ~194

---

## Definition of Done

- [ ] `inject_context()` has `conversation_id: UUID | None = None` parameter (CTO F1)
- [ ] `build_workspace_md()` produces `<workspace>` block with item previews
- [ ] `build_consensus_md()` uses lazy import for S221 compatibility
- [ ] Workspace builder returns `""` for 0 items (no empty block)
- [ ] Token budget <= 500 for workspace builder
- [ ] History compaction extracts and preserves active workspace keys
- [ ] Soft-deleted keys excluded from compaction preservation
- [ ] `approve_with_feedback()` stores in metadata JSONB
- [ ] `reject_with_feedback()` injects `<human_feedback>` XML system message
- [ ] `get_approval_rate()` returns correct rate for project
- [ ] `get_avg_response_time()` uses PERCENTILE_CONT (pure SQL, no in-memory)
- [ ] `escalate_to_lead` conflict strategy operational (if deferred from S219 per CTO F2)
- [ ] No Alembic migration needed (metadata column added in S218, workspace table in S219)
- [ ] All Sprint 220 tests passing (~30 new tests)
- [ ] 164 existing S216-S219 tests (36+38+45+45) still passing (no regressions)

---

## Risks

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| S220/S221 parallel merge conflict on context_injector.py | Low | Medium | S220 adds injection hook; S221 adds render logic in separate file. Lazy import prevents conflict |
| Workspace builder token budget exceeded | Low | Medium | Hard cap at 500 tokens; truncate with notice |
| Approval analytics slow on large datasets | Low | Low | PERCENTILE_CONT is single-pass; index on created_at covers time filter |
| Feedback injection timing (next turn may not be immediate) | Low | Low | System message persists in conversation — agent sees it whenever next turn happens |

---

## Dependencies

- **Upstream**: Sprint 219 complete (heartbeat + shared workspace CRUD)
- **Downstream**: Sprint 221 (consensus) provides render logic for build_consensus_md hook
- **Parallelism**: S220 and S221 can run parallel after S219 — only dependency is lazy import in context_injector
- **Infrastructure**: PostgreSQL (PERCENTILE_CONT aggregation), agent_messages.metadata JSONB (from S218)
- **References**: ADR-070 (CoPaw Pattern Adoption), CoPaw ReMe pattern, CoPaw human-in-the-loop

---

## Key Files

| File | Action | LOC (est.) |
|------|--------|------------|
| `backend/app/services/agent_team/context_injector.py` | MODIFY | +80 |
| `backend/app/services/agent_team/history_compactor.py` | MODIFY | +80 |
| `backend/app/services/agent_team/approval_feedback.py` | NEW | ~120 |
| `backend/app/services/agent_team/approval_analytics.py` | NEW | ~80 |
| `backend/tests/unit/test_sprint220_memory_feedback.py` | NEW | ~140 |
