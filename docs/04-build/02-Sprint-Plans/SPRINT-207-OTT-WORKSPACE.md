# Sprint 207 — OTT Workspace Context Management

**Sprint Duration**: TBD — 5 working days (after Sprint 206 closes)
**Sprint Goal**: Implement OTT Workspace — cho phép user set/switch active project trong **Telegram** chat, governance commands tự động inject project_id từ workspace (Zalo: Sprint 208+)
**Status**: PLANNED
**Priority**: P2 (Conversation-First UX)
**Framework**: SDLC 6.1.1
**Previous Sprint**: [Sprint 206 — TBD](SPRINT-206-TBD.md) | [Sprint 205 — LangChain Phase 1 (ADR-066)](SPRINT-205-LANGCHAIN.md)
**Functional Requirement**: [FR-049 — OTT Workspace Context Management](../../01-planning/03-Functional-Requirements/FR-049-OTT-Workspace.md)
**Architecture Decision**: [ADR-067 — OTT Workspace Context](../../02-design/01-ADRs/ADR-067-OTT-Workspace-Context.md)
**Reference Pattern**: EndiorBot `switch.ts` + `session-manager.ts`

---

## Sprint 207 Goal

Sprint 204 adds confidence-based routing to query_classifier. Sprints 205–206 deliver LangChain ADR-066 integration. Sprint 207 addresses a UX gap in the OTT Gateway: users must type 36-char UUIDs for every governance command because there's no "active project" concept in chat.

**Current state** (OTT Gateway):
- `OTT_DEFAULT_PROJECT_ID` env var — admin-configured, one project for ALL users
- `_USER_PROJECT_KEY = "ott_user_project:{chat_id}"` — informal, undocumented, no standard TTL
- No user-facing command to set/switch workspace
- `/gates`, `/approve`, `/evidence` require explicit `project_id` parameter

**Target state**:
- `workspace_service.py` — standardized Redis HASH at `ott:workspace:{channel}:{chat_id}` with 7-day TTL
- `/workspace set bflow` — user sets active project by name in 1 command
- `/workspace list` — user sees all accessible projects
- Governance commands auto-inject `project_id` from workspace (priority chain: explicit → workspace → env → error)

**Source**: CEO directive (Sprint 190 — Conversation-First strategy). Completes the "set project / switch project" design gap for OTT channels.

---

## Sprint 207 Backlog

### Track A — workspace_service.py (Day 1-2) — @dev

| ID | Item | Priority | Est | Status |
|----|------|----------|-----|--------|
| A-00 | Alembic migration `s207_001_projects_name_trgm_index.py` — `CREATE EXTENSION pg_trgm` + `CREATE INDEX CONCURRENTLY idx_projects_name_trgm` **⚠️ Day 1 blocker — must run before A-06** | P0 | 1h | ⬜ TODO |
| A-01 | `WorkspaceContext` dataclass: `project_id`, `project_name`, `tier`, `sdlc_stage`, `set_at`, `set_by` | P0 | 1h | ⬜ TODO |
| A-02 | `get_workspace(channel, chat_id, redis)` → `WorkspaceContext | None` — returns `None` on `ConnectionError`/`RedisError` (graceful degradation) | P0 | 1h | ⬜ TODO |
| A-03 | `set_workspace(channel, chat_id, project_id, project_name, tier, sdlc_stage, sender_id, redis)` — Redis HSET + EXPIRE 604800 | P0 | 1h | ⬜ TODO |
| A-04 | `clear_workspace(channel, chat_id, redis)` — Redis DEL | P0 | 0.5h | ⬜ TODO |
| A-05 | `touch_workspace_ttl(channel, chat_id, redis)` — Redis EXPIRE reset (called ONLY on successful governance execution with workspace-injected project_id) | P0 | 0.5h | ⬜ TODO |
| A-06 | `resolve_project_by_name(name, user_id, db)` — ILIKE search with `pg_trgm` index, membership check, returns: `{"exact": Project, "matches": list[Project]}` — max 5 matches (not 1!) | P0 | 2h | ⬜ TODO |

**New file**: `backend/app/services/agent_bridge/workspace_service.py` (~80 LOC)
**New file**: `backend/alembic/versions/s207_001_projects_name_trgm_index.py` (Day 1 prerequisite)

**Locked Architecture (D-067-02)**:
```python
# Key format
_WORKSPACE_KEY = "ott:workspace:{channel}:{chat_id}"
_WORKSPACE_TTL = 604800  # 7 days

@dataclass
class WorkspaceContext:
    project_id: str
    project_name: str
    tier: str
    sdlc_stage: str
    set_at: str
    set_by: str
```

---

### Track B — Telegram Command Interface (Day 2-3) — @dev

| ID | Item | Priority | Est | Status |
|----|------|----------|-----|--------|
| B-01 | `telegram_responder.py` — add `/workspace` to `_COMMAND_REPLIES` with guidance text | P0 | 0.5h | ⬜ TODO |
| B-02 | `ai_response_handler.py` — add workspace slash mappings to `_SLASH_TO_GOVERNANCE` (routing only, NO DB access) | P0 | 0.5h | ⬜ TODO |
| B-03 | **`governance_action_handler.py`** — add `_execute_workspace_command()` dispatch function alongside `_execute_gate_status()`, `_execute_request_approval()`, etc. (NOT `ai_response_handler.py` — no DB access there) | P0 | 3h | ⬜ TODO |
| B-04 | Format `/workspace` reply: project name, tier emoji, stage, set_by, set_at relative time | P1 | 1h | ⬜ TODO |
| B-05 | Format `/workspace list` reply: numbered list with tier emojis, active marker `▶`, max 10, NO gate counts (N+1 prevention) | P1 | 1h | ⬜ TODO |
| B-06 | Format `/workspace clear` reply: include previous project name before deletion — "🗑️ Workspace cleared (was: BFlow Platform). No active project." | P1 | 0.5h | ⬜ TODO |

**Modified files**:
- `backend/app/services/agent_bridge/telegram_responder.py` — B-01
- `backend/app/services/agent_bridge/ai_response_handler.py` — B-02 (slash mappings only)
- `backend/app/services/agent_bridge/governance_action_handler.py` — B-03 (workspace command dispatch + DB queries)

**⚠️ Architectural constraint**: `ai_response_handler.py` has NO `AsyncSessionLocal()` — it cannot perform DB queries. All workspace commands requiring DB access (`/workspace set <name>` → ILIKE search, `/workspace list` → projects query) MUST be implemented in `governance_action_handler.py`.

**Slash command mappings** (D-067-03):
```python
_SLASH_TO_GOVERNANCE.update({
    "/workspace":       "workspace info",
    "/workspace_set":   "workspace set",
    "/workspace_list":  "workspace list",
    "/workspace_clear": "workspace clear",
})
```

**`/workspace` static reply text** (shown before workspace commands are routed):
```
📂 Workspace Commands:
  /workspace set <name>   — Set active project
  /workspace              — Show current workspace
  /workspace list         — List your projects
  /workspace clear        — Clear workspace binding

Tip: Set workspace once, then use /gates /approve /evidence without project ID.
```

---

### Track C — Governance Injection (Day 3-4) — @dev

| ID | Item | Priority | Est | Status |
|----|------|----------|-----|--------|
| C-01 | `governance_action_handler.py` — extend `_resolve_project_id()` to check Redis workspace (Priority 2) | P0 | 2h | ⬜ TODO |
| C-02 | `governance_action_handler.py` — call `touch_workspace_ttl()` after successful project resolution | P0 | 0.5h | ⬜ TODO |
| C-03 | `governance_action_handler.py` — inject `channel` + `chat_id` into all governance command calls (needed for workspace lookup) | P0 | 1h | ⬜ TODO |
| C-04 | Update error message when no project context: include workspace guidance | P1 | 0.5h | ⬜ TODO |

**Modified file**: `backend/app/services/agent_bridge/governance_action_handler.py`

**Injection priority chain** (D-067-04):
```python
async def _resolve_project_id(
    explicit_id: str | None,
    channel: str,
    chat_id: str,
    redis,
    db,
) -> str | None:
    # Priority 1: explicit from message
    if explicit_id:
        return explicit_id

    # Priority 2: workspace from Redis
    workspace = await get_workspace(channel, chat_id, redis)
    if workspace:
        await touch_workspace_ttl(channel, chat_id, redis)
        return workspace.project_id

    # Priority 3: env var default
    default = os.getenv("OTT_DEFAULT_PROJECT_ID", "")
    if default:
        return default

    # Priority 4: error
    return None
```

---

### Track D — Tests (Day 4-5) — @dev

| ID | Item | Priority | Est | Status |
|----|------|----------|-----|--------|
| D-01 | `test_set_workspace_by_name` — success path (1 exact match) | P0 | 0.5h | ⬜ TODO |
| D-01b | `test_set_workspace_multi_match` — disambiguation list returned, workspace NOT set (2+ matches) | P0 | 0.5h | ⬜ TODO |
| D-02 | `test_set_workspace_by_uuid` — UUID direct path | P0 | 0.5h | ⬜ TODO |
| D-03 | `test_set_workspace_not_found` — 404 path | P0 | 0.5h | ⬜ TODO |
| D-04 | `test_set_workspace_no_access` — 403 path | P0 | 0.5h | ⬜ TODO |
| D-05 | `test_get_workspace_active` — show workspace info | P0 | 0.5h | ⬜ TODO |
| D-06 | `test_get_workspace_empty` — no workspace state | P0 | 0.5h | ⬜ TODO |
| D-07 | `test_list_workspace_projects` — user's projects list, no gate counts | P0 | 0.5h | ⬜ TODO |
| D-08 | `test_clear_workspace` — delete Redis key, confirm previous project name in reply | P0 | 0.5h | ⬜ TODO |
| D-09 | `test_governance_uses_workspace` — auto-inject path | P0 | 1h | ⬜ TODO |
| D-10 | `test_explicit_project_overrides_workspace` — priority 1 > 2 | P0 | 0.5h | ⬜ TODO |
| D-11 | `test_no_workspace_no_default_error` — error message with guidance | P0 | 0.5h | ⬜ TODO |
| D-12 | `test_group_vs_dm_scoping` — different key for group vs DM | P1 | 0.5h | ⬜ TODO |
| D-13 | `test_workspace_ttl_reset_on_use` — TTL reset ONLY on successful governance command, NOT on failure | P1 | 0.5h | ⬜ TODO |
| D-14 | `test_get_workspace_redis_failure` — `ConnectionError` → returns `None`, governance continues | P0 | 0.5h | ⬜ TODO |

**New test file**: `backend/tests/unit/test_sprint207_ott_workspace.py` (~150 LOC, 15 tests)

---

## Architecture Summary

### New Files

```
backend/app/services/agent_bridge/
└── workspace_service.py   # NEW — Redis CRUD for OTT workspace (~80 LOC)

backend/alembic/versions/
└── s207_001_projects_name_trgm_index.py  # NEW — pg_trgm GIN index (Day 1 prerequisite)
```

### Modified Files

```
backend/app/services/agent_bridge/
├── telegram_responder.py           # +4 workspace static commands (B-01)
├── ai_response_handler.py          # +4 slash mappings only, NO DB access (B-02)
└── governance_action_handler.py    # _execute_workspace_command() dispatch +
                                    # _resolve_project_id() workspace injection +
                                    # touch_workspace_ttl() call (B-03, C-01, C-02)
backend/tests/unit/
└── test_sprint207_ott_workspace.py  # NEW — 15 test cases
```

### Redis Namespace

```
ott:workspace:{channel}:{chat_id}   → HASH (7-day TTL, reset on SUCCESSFUL governance use)

Legacy key (coexistence period):
  DEPRECATED Sprint 207: ott_user_project:{chat_id}  — workspace_service.py does NOT read/write this
  STILL ACTIVE:          ott_team_bridge.py continues reading ott_user_project:{chat_id} for multi-agent flow
  REMOVAL:               Sprint 209+ (after multi-agent flow migrated to new key)
  MIGRATION:             User-driven — run /workspace set <name> once after Sprint 207 deploys
```

---

## Acceptance Criteria (Definition of Done)

- [ ] Alembic migration `s207_001` applied — `pg_trgm` GIN index on `projects.name` active
- [ ] `workspace_service.py` implemented: `WorkspaceContext` + 5 functions + `get_workspace()` returns `None` on `ConnectionError`
- [ ] `/workspace set bflow` (1 match) → stores Redis HASH, replies with project info including tier + stage
- [ ] `/workspace set platform` (2–5 matches) → disambiguation list with UUIDs returned, workspace NOT set
- [ ] `/workspace set nonexistent` → "not found" error with `/workspace list` hint
- [ ] `/workspace set secret` (no access) → "access denied" error
- [ ] `/workspace` → formatted project card when workspace set
- [ ] `/workspace` → guidance text when no workspace
- [ ] `/workspace list` → user's projects (max 10), `▶` marker on active, NO gate counts
- [ ] `/workspace clear` (active) → "was: BFlow Platform" confirmation, Redis key deleted
- [ ] `/workspace clear` (already empty) → "No active workspace to clear"
- [ ] `/gates` (no explicit project_id, workspace set) → uses workspace project_id, resets TTL
- [ ] `/gates <explicit-uuid>` (workspace set) → uses explicit UUID, workspace binding unchanged, TTL NOT reset
- [ ] No workspace + no `OTT_DEFAULT_PROJECT_ID` → error with guidance to `/workspace set`
- [ ] Group chat: workspace scoped to group_id; DM: scoped to user_id
- [ ] TTL reset ONLY on successful governance command (NOT on failed command, NOT on explicit project_id use)
- [ ] Redis unavailable → `get_workspace()` returns None, governance continues, no crash
- [ ] `_execute_workspace_command()` lives in `governance_action_handler.py` (NOT `ai_response_handler.py`)
- [ ] 15/15 tests in `test_sprint207_ott_workspace.py` pass (13 + D-01b multi-match + D-14 Redis failure)
- [ ] `docker restart sdlc-staging-backend` → all existing OTT tests still pass

---

## CTO Success Criteria (Proposed)

```yaml
Correctness:
  - FR-049 scenarios: 13/13 passing
  - No regression in existing OTT tests (212 tests)

Security:
  - Workspace is UX cache only — permissions always re-verified against PostgreSQL
  - No PII stored in Redis key (only project_id UUID + display name)
  - `project_id` validated as UUID before DB query (prevent injection)

Performance:
  - Workspace lookup: < 5ms (Redis HGETALL)
  - Project name search: < 100ms (ILIKE with limit 10)
  - No new N+1 queries

Code Quality:
  - workspace_service.py: < 100 LOC
  - All functions async
  - Full type hints
  - SDLC 6.1.1 naming conventions
```

---

## Dependencies

| Dependency | Status | Notes |
|-----------|--------|-------|
| Sprint 206 complete | Required | All previous sprints merged first |
| `pg_trgm` GIN index (A-00) | Day 1 blocker | Alembic migration must run before `/workspace set <name>` works |
| `magic_link_service.py` | Available (Sprint 189) | Not needed for this sprint |
| Redis 7.2 | Running | Port 6395 (staging) |
| `get_redis_client()` | Available | `app/utils/redis.py` |
| `governance_action_handler.py` | Available | Extend `_resolve_project_id()` + add `_execute_workspace_command()` |
| `ott_team_bridge.py` | Unchanged | Still uses `ott_user_project:{chat_id}` — do NOT modify in Sprint 207 |

---

## Sprint 207 Risks

| Risk | Probability | Mitigation |
|------|-------------|------------|
| Multiple projects with similar names | Medium | Return multiple matches, ask user to be more specific or use UUID |
| Redis unavailable | Low | Fall through to `OTT_DEFAULT_PROJECT_ID` env var (D-067-01) |
| Group workspace conflicts | Low | Last write wins — add `set_by` field so group sees who changed it |
