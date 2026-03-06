---
sdlc_version: "6.1.1"
document_type: "Sprint Plan"
status: "APPROVED"
sprint: "218"
tier: "PROFESSIONAL"
stage: "04 - Build"
---

# Sprint 218 — P3 Skills Completion + P1 Message Filtering

**Sprint Duration**: March-April 2026
**Sprint Goal**: Complete skills engine with per-agent grants and tsvector search, add message filtering/broadcast API, add agent_messages.metadata JSONB column
**Status**: PLANNED
**Priority**: P1
**Framework**: SDLC 6.1.1
**ADRs**: ADR-069 (MTClaw Restructure), ADR-070 (CoPaw/AgentScope Pattern Adoption)
**FRs**: FR-052 (Skills Engine — P2b grants + search)
**Previous Sprint**: [Sprint 217 — Skills Engine P2a](SPRINT-217-SKILLS-ENGINE-P2A.md)
**Prerequisite**: ADR-070 must be written BEFORE coding starts

---

## Scope Change (PDR-001)

> **CTO APPROVED** — Scope pivoted from original plan per PDR-001 expert synthesis.
>
> **Original scope** (ADR-069): P2b Skills Search + Grants + P3 Bootstrap Files Loader
> **New scope** (ADR-070): P3 Skills Completion + P1 Message Filtering + agent_messages.metadata JSONB
>
> **What changed**:
> - Bootstrap Files Loader (P3 original) **DEFERRED** to S222+ per PDR-001 priority
> - Deterministic Router (originally S219) **DEFERRED** to S222+ per PDR-001 priority
> - Message filtering/broadcast API **ADDED** (AgentScope P1 pattern — broadcast + system message)
> - `agent_messages.metadata JSONB` column **ADDED** (CTO BLOCKER-1 fix — unblocks S220 approval feedback)
>
> **Rationale**: CoPaw patterns (heartbeat, workspace, consensus, approval feedback) deliver higher
> value than bootstrap files and deterministic router. Bootstrap file loading can wait; agent
> liveness and shared workspace cannot.

---

## Context

Sprint 217 delivered the skills data model (`skill_definitions` table with tsvector), the
5-tier loader, and BuildSummary for system prompt injection. Agents now see a list of
available skills in their system prompt. 74 cumulative tests passing (S216: 36 + S217: 38).

Three gaps remain in this sprint:

1. **Per-agent grants**: currently all public skills are visible to all agents. CoPaw uses a
   junction table (`skill_agent_grants`) so that `@coder` sees different skills than `@reviewer`.
2. **tsvector search**: the GIN index exists on `skill_definitions.search_tsv` but no search
   service is wired. Agents need to search skills by keyword to find relevant capabilities.
3. **Message filtering**: `message_queue.py` has no filtering or broadcast API. AgentScope's
   MsgHub pattern requires broadcast (NULL recipient = all) and filtered queries by type/sender.

Additionally, `agent_messages` table currently has NO `metadata` JSONB column (only `mentions`
JSONB for @agent parsing). This sprint adds the column to unblock S220 approval feedback storage.

---

## Sprint Summary

| Track | Scope | Est. LOC | Impact |
|-------|-------|----------|--------|
| A | skill_agent_grants table + metadata JSONB ALTER (Alembic migration) | ~60 migration | Per-agent skill visibility + metadata storage |
| B | Skill search service (tsvector query + grant filtering) | ~80 new | Keyword-based skill discovery for agents |
| C | Update SkillLoader with grants JOIN | ~30 modify | Accessible skills filtered by agent grants |
| D | Message filtering + broadcast API for message_queue.py | ~80 modify | Broadcast + system message + filtered queries |
| E | Model updates (SkillAgentGrant + agent_message metadata_) | ~70 new+modify | ORM for new table + new column mapping |
| F | Tests: grants, search, broadcast, metadata roundtrip | ~180 new | Regression safety for all tracks |
| **Total** | | **~500 LOC** | **Skills engine complete + message filtering operational** |

---

## Track A — Alembic Migration (s218_001)

### A1: skill_agent_grants table

- NEW table: `skill_agent_grants`
- Columns:
  - `id` UUID PK (default uuid4)
  - `skill_definition_id` UUID FK to `skill_definitions(id)` ON DELETE CASCADE
  - `agent_definition_id` UUID FK to `agent_definitions(id)` ON DELETE CASCADE
  - `granted_at` TIMESTAMPTZ DEFAULT now()
  - `granted_by` UUID FK to `users(id)` ON DELETE SET NULL — who assigned the grant
- Constraints:
  - `UNIQUE(skill_definition_id, agent_definition_id)` — one grant per skill-agent pair
  - ON CONFLICT DO NOTHING for idempotent grant creation
- Indexes:
  - B-tree on `agent_definition_id` for per-agent grant lookups

### A2: agent_messages.metadata JSONB column

- ALTER TABLE: `agent_messages ADD COLUMN metadata JSONB NOT NULL DEFAULT '{}'::jsonb`
- **Why**: `agent_messages` currently has `mentions` JSONB (parsed @agent refs) but NO
  general-purpose metadata column. This is needed for:
  - S218: routing evidence storage, broadcast message metadata
  - S220: approval feedback storage (`metadata["approval_feedback"]`)
  - S221: consensus vote references
- **Naming**: DB column `metadata`, SQLAlchemy mapped as `metadata_` (avoids SA reserved name)

### A3: Alembic chain

- File: `backend/alembic/versions/s218_001_skill_grants.py`
- `down_revision = "s217_001"` (skills engine P2a)
- `revision = "s218_001"`

---

## Track B — Skill Search Service

### B1: New service file

- NEW: `backend/app/services/agent_team/skill_search.py` (~80 LOC)
- Class `SkillSearchService` with dependency injection for DB session

### B2: search_skills()

- `search_skills(query: str, agent_id: UUID | None, project_id: UUID | None, limit: int = 10) -> list[dict]`
- SQL query uses `ts_rank()` on `search_tsv` GENERATED column (created in S217):
  ```sql
  SELECT sd.*, ts_rank(sd.search_tsv, plainto_tsquery('simple', :query)) AS rank
  FROM skill_definitions sd
  WHERE sd.search_tsv @@ plainto_tsquery('simple', :query)
    AND (
      sd.tier IN ('global', 'builtin')  -- open tiers, no grant needed
      OR sd.id IN (
        SELECT sag.skill_definition_id FROM skill_agent_grants sag
        WHERE sag.agent_definition_id = :agent_id
      )
    )
  ORDER BY rank DESC
  LIMIT :limit
  ```
- Single SQL, no N+1 queries
- `plainto_tsquery('simple')` — Vietnamese-safe, no stopword removal
- Empty query returns top skills by tier priority (no search filtering)

### B3: has_grant()

- `has_grant(skill_id: UUID, agent_id: UUID) -> bool`
- Simple existence check on `skill_agent_grants`
- Used by SkillLoader to annotate results

### B4: grant_skill() / revoke_grant()

- `grant_skill(skill_id, agent_id, granted_by) -> bool` — INSERT ON CONFLICT DO NOTHING
- `revoke_grant(skill_id, agent_id) -> bool` — DELETE, returns True if row existed
- Idempotent: granting twice = no error, revoking non-existent = no error

---

## Track C — Update SkillLoader with Grants

### C1: Modify load_accessible()

- MODIFY: `backend/app/services/agent_team/skill_loader.py`
- When `agent_definition_id` is provided:
  - JOIN `skill_agent_grants` to filter workspace/project/personal tiers
  - Open tiers (`global`, `builtin`) don't require grant — behavior unchanged
- When `agent_definition_id` is None: return all skills (admin view)
- No breaking change to existing callers

---

## Track D — Message Filtering + Broadcast

### D1: MessageFilters dataclass

- ADD to `backend/app/services/agent_team/message_queue.py`:
  ```python
  @dataclass
  class MessageFilters:
      message_type: str | None = None
      sender_agent_id: UUID | None = None
      recipient_agent_id: UUID | None = None
      conversation_id: UUID | None = None
      limit: int = 50
      offset: int = 0
  ```

### D2: list_messages()

- `list_messages(filters: MessageFilters) -> list[AgentMessage]`
- Dynamic WHERE clause from non-None filter fields
- Pagination via LIMIT/OFFSET
- Used by agents to query conversation history with filters

### D3: post_broadcast()

- `post_broadcast(conversation_id, sender_agent_id, content, metadata=None) -> AgentMessage`
- Sets `recipient_agent_id = NULL` (broadcast convention)
- Sets `message_type = 'broadcast'`
- Stores optional metadata in new `metadata` JSONB column

### D4: post_system_message()

- `post_system_message(conversation_id, content, metadata=None) -> AgentMessage`
- EP-07 gate signal injection: system messages for gate pass/fail notifications
- Sets `sender_agent_id = NULL`, `message_type = 'system'`
- Metadata can contain `{"gate_signal": "G2_PASS", "gate_id": "..."}`

---

## Track E — Model Updates

### E1: SkillAgentGrant model

- NEW: `backend/app/models/skill_agent_grant.py` (~60 LOC)
- Follow junction table pattern: two FKs with CASCADE, UNIQUE constraint
- `to_dict()` includes skill slug and agent name for readability
- Register in `backend/app/models/__init__.py`

### E2: AgentMessage metadata_ column

- MODIFY: `backend/app/models/agent_message.py`
- Add mapped column: `metadata_: Mapped[dict] = mapped_column("metadata", JSONB, default=dict, server_default=text("'{}'::jsonb"))`
- Coexists with existing `mentions` JSONB column (they serve different purposes)

---

## Track F — Tests

### F1: Grant + search tests

File: `backend/tests/unit/test_sprint218_skill_search.py`

| Test case | Expected |
|-----------|----------|
| tsvector search: 'code review' | Returns matching skill, score > 0 |
| tsvector search: Vietnamese keyword | Returns matching skill (no stopword filtering) |
| Agent with grant sees workspace skill | has_grant=True in results |
| Agent without grant to workspace skill | 0 results for that skill |
| Global/builtin skills visible without grant | Always returned regardless of agent |
| Grant idempotent: insert 2nd time | rowcount=0 (ON CONFLICT DO NOTHING) |
| Revoke non-existent grant | Returns False, no error |
| Empty query returns tier-sorted defaults | Skills ordered: workspace > project > personal > global > builtin |
| Integration: search + grant + BuildSummary | Summary XML contains tier, name, description |

### F2: Message filtering + broadcast tests

| Test case | Expected |
|-----------|----------|
| Broadcast filter: message_type='broadcast' | Only broadcast messages returned |
| Broadcast message has recipient_id=NULL | Verified in DB |
| System message has sender_agent_id=NULL | Verified in DB |
| System filter for gate signals | metadata["gate_signal"] displays correctly |
| list_messages pagination: limit=10, offset=5 | Correct slice returned |
| Filter by sender_agent_id | Only sender's messages returned |

### F3: Metadata JSONB roundtrip tests

| Test case | Expected |
|-----------|----------|
| agent_messages.metadata JSONB write dict → read dict | Preserved exactly |
| metadata with nested objects | JSONB handles nested dicts |
| metadata default empty dict | New messages have {} metadata |
| metadata coexists with mentions | Both columns independent |

### F4: Integration smoke test

| Test case | Expected |
|-----------|----------|
| Full flow: create grant → search skills → build summary → broadcast result | All steps complete without errors |
| 74 existing S216+S217 tests still pass | No regressions |

**Test target**: +~45 tests → cumulative ~119

---

## Definition of Done

- [ ] `skill_agent_grants` table created with UNIQUE and FK CASCADE constraints
- [ ] `agent_messages.metadata` JSONB column added (NOT NULL DEFAULT '{}')
- [ ] `SkillAgentGrant` model registered in `models/__init__.py`
- [ ] `agent_message.py` has `metadata_` mapped column alongside existing `mentions`
- [ ] `search_skills()` returns ranked results filtered by agent grants
- [ ] Open tiers (global/builtin) accessible without grant — behavior unchanged
- [ ] `grant_skill()` idempotent (ON CONFLICT DO NOTHING)
- [ ] `SkillLoader.load_accessible()` JOINs grants when agent_id provided
- [ ] `MessageFilters` dataclass with type/sender/recipient/pagination
- [ ] `post_broadcast()` creates message with NULL recipient
- [ ] `post_system_message()` creates message with NULL sender + system type
- [ ] Metadata JSONB roundtrip: write dict → read dict preserved
- [ ] All Sprint 218 tests passing (~45 new tests)
- [ ] 74 existing S216+S217 tests still passing (no regressions)
- [ ] Alembic chain: s217_001 → s218_001

---

## Risks

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| metadata JSONB migration locks agent_messages table | Low | Medium | Table is small (~1K rows); ALTER is fast. If large, use `ADD COLUMN ... DEFAULT` (PG 11+ instant) |
| tsvector search returns irrelevant results for short queries | Medium | Low | Minimum query length of 2 chars; empty query returns tier-sorted defaults |
| Grant system creates admin overhead | Low | Low | Presets auto-create grants; admin can manage via API |
| Broadcast messages flood conversation history | Medium | Medium | Broadcast has message_type filter; agents can filter out broadcasts |

---

## Dependencies

- **Upstream**: Sprint 217 complete (skill_definitions table with search_tsv GIN index, 5-tier loader, BuildSummary)
- **Downstream**: Sprint 219 (Heartbeat + Workspace) uses metadata JSONB for heartbeat events; Sprint 220 uses metadata for approval feedback
- **Infrastructure**: PostgreSQL (skill_agent_grants table + agent_messages ALTER)
- **References**: FR-052 (P2b BDD scenarios), ADR-069 (MTClaw), ADR-070 (CoPaw/AgentScope), CoPaw skills/loader.go, AgentScope Msg pattern

---

## Key Files

| File | Action | LOC (est.) |
|------|--------|------------|
| `backend/alembic/versions/s218_001_skill_grants.py` | NEW | ~40 |
| `backend/app/models/skill_agent_grant.py` | NEW | ~60 |
| `backend/app/models/agent_message.py` | MODIFY | +10 |
| `backend/app/models/__init__.py` | MODIFY | +1 |
| `backend/app/services/agent_team/skill_search.py` | NEW | ~80 |
| `backend/app/services/agent_team/skill_loader.py` | MODIFY | +30 |
| `backend/app/services/agent_team/message_queue.py` | MODIFY | +80 |
| `backend/tests/unit/test_sprint218_skill_search.py` | NEW | ~180 |
