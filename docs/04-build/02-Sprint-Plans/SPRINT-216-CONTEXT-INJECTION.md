---
sdlc_version: "6.1.1"
document_type: "Sprint Plan"
status: "APPROVED"
sprint: "216"
tier: "PROFESSIONAL"
stage: "04 - Build"
---

# Sprint 216 — P1 Context Injection + Delegation Links

**Sprint Duration**: March 2026
**Sprint Goal**: Implement delegation links table, context injector service, and spawn tool guard
**Status**: PLANNED
**Priority**: P0 CRITICAL (highest-impact MTClaw pattern)
**Framework**: SDLC 6.1.1
**ADR**: ADR-069 (MTClaw Restructure)
**FRs**: FR-051 (Delegation Links and Context Injection)
**Previous Sprint**: [Sprint 215 — Restructure Foundation](SPRINT-215-RESTRUCTURE-FOUNDATION.md)

---

## Context

Sprint 215 cleaned the foundation: dead code removed, 4 role systems unified into a single
resolver, OTT bridge team_id fixed. The codebase is now ready for the highest-impact MTClaw
adoption pattern: context injection.

MTClaw's `resolver.go` (475 LOC) builds dynamic markdown sections (DELEGATION.md, TEAM.md,
AVAILABILITY.md) and injects them into every agent's system prompt. This is the mechanism
that enables agents to know who they can delegate to, what team they belong to, and what
tools are available — without hardcoding any of it.

This sprint ports that pattern to Python, adds a `delegation_links` table for explicit
delegation authorization, and wires a spawn tool guard that rejects unauthorized delegation
attempts.

---

## Sprint Summary

| Track | Scope | Est. LOC | Impact |
|-------|-------|----------|--------|
| A | Delegation links table + service + spawn tool guard | ~120 new | Explicit delegation authorization with audit trail |
| B | Team lead column + preset persistence to delegation_links | ~40 alter + new | Lead agent routing, preset-to-link persistence |
| C | Context injector service (3 builders + inject entrypoint) | ~150 new | Dynamic system prompt sections for every agent |
| D | Tests: delegation CRUD, context builders, spawn guard, FK cascade | ~100 new | Regression safety for all 3 tracks |
| **Total** | | **~410 LOC** | **MTClaw P1 context injection operational** |

---

## Track A — Delegation Links

### A1: Alembic migration

- NEW table: `delegation_links`
- Columns:
  - `id` UUID PK (default uuid4)
  - `source_agent_id` UUID FK to `agent_definitions(id)` ON DELETE CASCADE
  - `target_agent_id` UUID FK to `agent_definitions(id)` ON DELETE CASCADE
  - `link_type` VARCHAR(30) DEFAULT 'can_delegate' (extensible for future: can_review, can_escalate)
  - `is_active` BOOLEAN DEFAULT TRUE
  - `created_at` TIMESTAMP DEFAULT now()
  - `updated_at` TIMESTAMP DEFAULT now()
- Constraints:
  - UNIQUE(`source_agent_id`, `target_agent_id`, `link_type`)
  - CHECK: `source_agent_id != target_agent_id` (no self-delegation)

### A2: Delegation model

- NEW: `backend/app/models/delegation_link.py`
- SQLAlchemy model following `backend/app/models/vcr.py` pattern
- UUID PK, FK with ondelete, Enum-compatible link_type, `to_dict()` method

### A3: Delegation service

- NEW: `backend/app/services/agent_team/delegation_service.py` (~80 LOC)
- Methods:
  - `can_delegate(source_id, target_id)` — checks active link exists (bidirectional lookup)
  - `get_targets(agent_id)` — returns list of active delegation targets
  - `get_sources(agent_id)` — returns list of agents that can delegate TO this agent
  - `create_link(source_id, target_id, link_type)` — insert with duplicate check
  - `deactivate_link(source_id, target_id)` — soft delete (set is_active=False)

### A4: Spawn tool guard

- MODIFY: `backend/app/services/agent_team/tool_context.py`
- Before any agent spawn/delegate tool call, check `delegation_service.can_delegate()`
- If unauthorized: reject with `PermissionDenied`, log `blocked_unauthorized_delegation` event
- Log entry includes: source_agent_id, target_agent_id, conversation_id, timestamp

---

## Track B — Team Lead + Preset Persistence

### B1: ALTER teams table

- Alembic migration: ADD column `lead_agent_definition_id UUID REFERENCES agent_definitions(id) ON DELETE SET NULL`
- This designates which agent acts as the team's primary router/lead
- ON DELETE SET NULL: if the lead agent is deleted, team has no lead (safe degradation)

### B2: Modify team_presets.py

- When `apply_preset()` is called with a delegation chain:
  1. Create `delegation_links` rows for each pair in the chain
  2. Set `teams.lead_agent_definition_id` to the first agent in the chain
- Example: preset "code-review" with chain `[@initializer, @coder, @reviewer]` creates:
  - `initializer -> coder` (can_delegate)
  - `coder -> reviewer` (can_delegate)
  - `lead_agent_definition_id = initializer.id`

---

## Track C — Context Injector

### C1: New service file

- NEW: `backend/app/services/agent_team/context_injector.py` (~150 LOC)
- Port of MTClaw `resolver.go` functions: `buildDelegateAgentsMD`, `buildTeamMD`, `buildAvailabilityMD`

### C2: build_delegation_md(agent_id)

- Query `delegation_links` for all active targets of this agent
- If targets <= 15: full list with agent name, role, and capabilities summary
- If targets > 15: truncated list with instruction to search by skill
- Token budget: <= 2000 tokens
- Output wrapped in `<delegation>` XML tags
- Format per target:
  ```
  - @agent_name (role: coder) — capabilities summary from agent_definition.description
  ```

### C3: build_team_md(agent_id, team_id)

- Query team membership and lead designation
- Two variants:
  - **Lead variant**: includes full team roster, delegation overview, team settings summary
  - **Member variant**: includes lead agent reference, own role, relevant team policies
- Token budget: <= 1500 tokens
- Output wrapped in `<team>` XML tags

### C4: build_availability_md(agent_id)

- Negative context: explicitly states what the agent CANNOT do
- If agent has 0 delegation targets: "You cannot delegate tasks to other agents."
- If agent has no tool permissions for certain categories: list unavailable tool categories
- Token budget: <= 200 tokens
- Output wrapped in `<availability>` XML tags
- Purpose: prevent hallucinated tool calls and unauthorized delegation attempts

### C5: inject_context(agent_id, team_id, system_prompt)

- Entrypoint that calls all 3 builders and appends results to system_prompt
- Order: delegation -> team -> availability
- Cache key: `ctx:{agent_id}:{team_id}:{delegation_links_max_updated_at}`
- Cache TTL: 120 seconds
- All injected content wrapped in XML tags
- User-provided content within agent descriptions is XML-escaped to prevent injection

---

## Track D — Tests

### D1: Delegation service tests

- `test_delegation_service.py` (~30 LOC)
- Test `can_delegate()` returns True for active link, False for inactive/missing
- Test `get_targets()` returns correct agents, excludes inactive
- Test `create_link()` rejects self-delegation (CHECK constraint)
- Test UNIQUE constraint prevents duplicate links

### D2: Context builder tests

- `test_context_injector.py` (~40 LOC)
- Test `build_delegation_md()` with 3 targets — correct XML output
- Test `build_delegation_md()` with 20 targets — truncated with search instruction
- Test `build_team_md()` lead variant includes full roster
- Test `build_team_md()` member variant includes lead reference
- Test `build_availability_md()` with 0 targets — correct negative context
- Test XML escaping: agent description with `<script>` is escaped

### D3: Spawn tool guard tests

- `test_spawn_guard.py` (~15 LOC)
- Test authorized delegation: spawn allowed
- Test unauthorized delegation: PermissionDenied raised
- Test log entry: `blocked_unauthorized_delegation` event recorded

### D4: FK cascade and preset tests

- `test_delegation_cascade.py` (~15 LOC)
- Test FK CASCADE: delete agent_definition -> delegation_links auto-deleted
- Test `apply_preset()` creates correct delegation_links rows
- Test `apply_preset()` sets lead_agent_definition_id on team

---

## Definition of Done

- [ ] `delegation_links` table created with UNIQUE and CHECK constraints
- [ ] `delegation_service.py` implements can_delegate, get_targets, create_link, deactivate_link
- [ ] Spawn tool guard rejects unauthorized delegation with PermissionDenied
- [ ] `blocked_unauthorized_delegation` log event recorded on rejection
- [ ] `teams.lead_agent_definition_id` column added (ON DELETE SET NULL)
- [ ] `apply_preset()` persists delegation chain to delegation_links table
- [ ] `context_injector.py` builds DELEGATION.md with correct token budget (<= 2000)
- [ ] TEAM.md differentiates lead vs member content (<= 1500 tokens)
- [ ] AVAILABILITY.md generates negative context for 0 targets (<= 200 tokens)
- [ ] All injected content uses XML tags, user content XML-escaped
- [ ] Cache key includes delegation_links max(updated_at)
- [ ] FK CASCADE: delete agent -> links auto-deleted
- [ ] All Sprint 216 tests passing
- [ ] Combined Sprint 209-216 tests passing
- [ ] CURRENT-SPRINT.md updated

---

## Risks

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Token budget overflow on large teams (>50 agents) | Low | Medium | Hard cap via truncation + search instruction fallback |
| Cache stale after rapid delegation changes | Medium | Low | Short TTL (120s) + explicit invalidation on link write |
| Preset migration breaks existing team configs | Low | High | Preset persistence is additive only; existing teams unaffected |
| XML injection via agent descriptions | Low | High | XML-escape all user-provided content before injection |

---

## Dependencies

- **Upstream**: Sprint 215 complete (role resolver, dead code removal)
- **Downstream**: Sprint 217 (Skills Engine) uses context_injector for skill summary injection
- **Infrastructure**: PostgreSQL (delegation_links table), Redis (context cache)
- **References**: FR-051 (BDD scenarios), ADR-056 (LD#1 snapshot precedence), MTClaw resolver.go (475 LOC)
