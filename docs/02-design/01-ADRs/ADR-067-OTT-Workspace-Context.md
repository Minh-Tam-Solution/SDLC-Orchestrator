---
sdlc_version: "6.1.1"
document_type: "Architecture Decision Record"
status: "DRAFT"
sprint: "207"
spec_id: "ADR-067"
tier: "STANDARD"
stage: "02 - Design"
owner: "CTO"
---

# ADR-067 — OTT Workspace Context Management

**Status**: DRAFT (Sprint 207 — Pending CTO Review)
**Date**: February 2026
**Author**: PM + Architect
**Sprint**: Sprint 207
**Framework**: SDLC 6.1.1
**Supersedes**: None
**References**:
- ADR-056 (Multi-Agent Team Engine — Snapshot Precedence, Lane Contract)
- ADR-064 (Chat-First Facade — D-064-01: Chat=UX, Control Plane=Truth)
- FR-049 (OTT Workspace Context Management)
- EndiorBot ADR-002 (Project Context Switching — `switch.ts`, `session-manager.ts`)

---

## 1. Context

### 1.1 Problem Statement

SDLC Orchestrator's OTT Gateway (Telegram, Zalo) has no concept of an **active workspace**. Three failure modes result:

| # | Failure | User Impact |
|---|---------|-------------|
| 1 | **No project context** | Every governance command (`/gates`, `/approve`) requires explicit `--project-id UUID` — 36-char UUID users cannot memorize |
| 2 | **Single env-var default** | `OTT_DEFAULT_PROJECT_ID` is admin-configured, globally shared — all users in all chats use the same project |
| 3 | **No project switching** | Users working across multiple projects (PM, CTO) must use Web App to switch — defeats Conversation-First strategy (ADR-064) |

### 1.2 Reference Pattern: EndiorBot Workspace

EndiorBot (TypeScript, local agent tool) implements workspace switching via:

```typescript
// switch.ts — CLI workspace switching
interface ActiveProjectState {
  currentProject?: string;
  projects: Record<string, ProjectContext>;  // persisted in projects.json
}

// session-manager.ts — session tied to project
async switchProject(projectId: string, tier: ProjectTier): Promise<Session> {
  await this.saveSession();  // save current session
  const sessions = await this.store.list(projectId);
  const latestSession = sessions[0];  // restore most recent session for project
  return latestSession ? await this.loadSession(latestSession.id)
                       : await this.createSession(projectId, tier);
}

// agent-scope.ts — workspace = filesystem path + permissions
interface AgentWorkspace {
  path: string;          // root directory of project
  allowedPaths: string[];
  blockedPaths: string[];
}
```

**Key insight**: EndiorBot workspace = file system path. OTT workspace = logical Redis binding (no file system in chat context).

### 1.3 Existing Partial Implementation

`ott_team_bridge.py` already has two Redis keys:
```python
_ACTIVE_CONV_KEY = "ott_active_conv:{chat_id}"    # 24h TTL
_USER_PROJECT_KEY = "ott_user_project:{chat_id}"  # no documented TTL
_DEFAULT_PROJECT_ID = os.getenv("OTT_DEFAULT_PROJECT_ID", "")
```

These are informal and undocumented. ADR-067 formalizes and extends this pattern.

---

## 2. Decision

**OTT Workspace**: A Redis HASH per `(channel, chat_id)` that stores the active project binding for a chat session. Governance commands automatically read and use this workspace. Users can set, view, list, and clear their workspace via `/workspace` commands.

**Aligned with ADR-064**: Chat layer sets UX context (workspace). Control plane (PostgreSQL + OPA) remains the single source of truth for permissions and gate status.

---

## 3. Locked Decisions

### D-067-01: Workspace = Redis UX Layer, PostgreSQL = Control Plane Truth

**Decision**:
- Redis workspace stores `project_id` (UUID string) as **UX convenience cache** — NOT a permission cache
- On every governance command: workspace supplies `project_id` → PostgreSQL verifies member access + permissions → OPA evaluates gate policy
- Workspace NEVER caches permission results, gate status, or approval history
- If Redis workspace key is lost/expired: fallback to `OTT_DEFAULT_PROJECT_ID` env var, then error

**Rationale**: Preserves ADR-064 D-064-01 ("Chat=UX, Control Plane=Truth"). Workspace is a shortcut for UX, not a shadow of business logic.

**Implications**:
- Redis failure → workspace commands fail gracefully (not governance execution)
- Workspace set to a project user loses access to → next governance command returns 403 (not cached permission)

**Redis Failure Contract (P0-3)** — explicit graceful degradation:
```python
async def get_workspace(channel: str, chat_id: str, redis) -> WorkspaceContext | None:
    """
    Returns None on any Redis error — non-fatal, falls through to env-var fallback.
    Governance execution continues; workspace lookup failure is not a hard stop.
    """
    try:
        data = await redis.hgetall(f"ott:workspace:{channel}:{chat_id}")
        if not data:
            return None
        return WorkspaceContext(**{k.decode(): v.decode() for k, v in data.items()})
    except (ConnectionError, RedisError):
        # Redis unavailable — silently return None, caller falls through to env-var
        return None
```

**Workspace SET failure contract** (different behavior from GET):
- If Redis is unavailable when user runs `/workspace set` or `/workspace clear`: return user-visible error
- Reply: `"⚠️ Workspace service temporarily unavailable. Try again in a moment."`
- Rationale: SET modifies state (user expects confirmation); GET is a read that can safely degrade

---

### D-067-02: Workspace Redis Schema

**Decision**:
```
KEY:   ott:workspace:{channel}:{chat_id}
TYPE:  Redis HASH
TTL:   604800 seconds (7 days), reset on every governance command use

FIELDS:
  project_id    → UUID string (e.g. "abc123ef-0000-0000-0000-000000000001")
  project_name  → display name (e.g. "BFlow Platform")
  tier          → LITE|STANDARD|PROFESSIONAL|ENTERPRISE
  sdlc_stage    → current stage (e.g. "04-BUILD")
  set_at        → ISO 8601 timestamp
  set_by        → sender_id (Telegram user_id or Zalo user_id)
```

**Channel values**: `"telegram"` | `"zalo"` (extensible for future channels)

**Prerequisite (P0-2)**: `/workspace set <name>` requires ILIKE search on `projects.name` (String 255, currently unindexed). Sprint 207 MUST include Alembic migration:
```sql
CREATE EXTENSION IF NOT EXISTS pg_trgm;
CREATE INDEX CONCURRENTLY idx_projects_name_trgm
  ON projects USING GIN (name gin_trgm_ops);
```
Without this index, ILIKE search degrades to sequential scan (O(n) rows). Migration is a **Day 1 blocker** — no workspace set command works without it.

**Migration from legacy keys** (P1-2):
- `ott_user_project:{chat_id}` in `ott_team_bridge.py` → **DEPRECATED Sprint 207**
- Sprint 207: new `workspace_service.py` reads/writes ONLY `ott:workspace:{channel}:{chat_id}`. Legacy key is neither read nor written by workspace service.
- `ott_team_bridge.py` continues reading `ott_user_project:{chat_id}` for multi-agent flow until **Sprint 209+ cleanup**
- Migration is **user-driven**: users run `/workspace set <name>` once after deploy. No automated migration script.

**7-day TTL rationale**:
- 24h (current conv TTL) too short for sustained daily use
- 30d too long for security (transferred devices, account changes)
- 7 days matches typical sprint length — natural reset cadence
- TTL resets on every **successful** governance command use = "active sessions never expire"

**TTL touch precision** (P1-3):
- ✅ TTL reset: Governance command executes successfully with workspace-injected `project_id`
- ✅ TTL reset: `/workspace` info view, `/workspace list`
- ❌ TTL NOT reset: Failed governance command (403, not found, validation error)
- ❌ TTL NOT reset: Governance command with explicit `project_id` (workspace not used)
- ❌ TTL NOT reset: `/workspace set` (initializes TTL to 7 days, not "reset")

---

### D-067-03: Workspace Command Protocol

**Decision**: Four commands under `/workspace` namespace:

| Command | Action | Notes |
|---------|--------|-------|
| `/workspace set <name-or-id>` | Set active workspace | Partial name match (ILIKE), UUID direct |
| `/workspace` | Show current workspace | Alias: `/workspace info` |
| `/workspace list` | List accessible projects | Max 10, mark active |
| `/workspace clear` | Remove workspace binding | Delete Redis key |

**NOT included**:
- `/workspace switch` — redundant with `/set` (EndiorBot uses separate commands, we simplify)
- `/workspace create` — project creation via OTT is out of scope (Web App concern)
- `/ws` shorthand — avoid ambiguity with other commands

**Slash command mapping** (for `ai_response_handler.py` `_SLASH_TO_GOVERNANCE`):
```python
"/workspace": "workspace info",
"/workspace_set": "workspace set",
"/workspace_list": "workspace list",
"/workspace_clear": "workspace clear",
```

---

### D-067-04: Governance Command Project Injection Priority

**Decision**: Governance commands resolve `project_id` via a 4-level priority chain:

```
Priority 1: Explicit in message
  "/gates <project-uuid>"  →  use <project-uuid> directly
  "/approve G3 <project-uuid>"  →  use <project-uuid> directly

Priority 2: Active workspace (Redis)
  Read ott:workspace:{channel}:{chat_id}
  If found: inject project_id, reset TTL
  If not found: fall through

Priority 3: OTT default (env var)
  OTT_DEFAULT_PROJECT_ID (legacy fallback, still supported)
  If set: inject project_id
  If not set: fall through

Priority 4: Error
  Reply: "⚠️ No project context.
          Set your workspace: /workspace set <project-name>"
```

**Implementation point**: `governance_action_handler.py` → `_resolve_project_id()` function (currently checks env var only; extend to check Redis first).

**Key invariant**: Explicit > workspace > default > error. Workspace NEVER overrides explicit.

---

### D-067-05: Workspace Scoping = Channel × Chat_ID

**Decision**: Workspace scope is determined by `(channel, chat_id)` where `chat_id` depends on context:

| Chat context | chat_id source | Sharing model |
|-------------|----------------|---------------|
| Telegram DM | `message.from.id` (user_id) | Private to user |
| Telegram group/supergroup | `message.chat.id` (negative group_id) | Shared by all group members |
| Telegram channel post | `message.chat.id` (channel_id) | Shared by all admins |
| Zalo OA | `sender.id` (user_id) | Private to user |

**Group workspace rationale**: Team members in a group chat typically work on the same project. A shared group workspace reduces friction — any member can set the project and others benefit. This aligns with team collaboration patterns in Slack/Discord bots.

**Security note**: Group workspace set by any group member. No group admin required (access to the project is still individually verified per command).

---

## 4. Consequences

### Positive
- Conversation-First UX: users set workspace once, all governance flows naturally
- Multi-project PMs can switch context in 1 command
- Groups share workspace — team standup bots work without per-user setup
- 7-day TTL with auto-reset = "set it and forget it" for active sprints

### Negative
- Group workspace: one member's `/workspace set` affects the whole group
  - Mitigation: `/workspace` shows who set it (`set_by` field) + when
- Redis dependency for workspace resolution (mitigated by env var fallback; `get_workspace()` returns None on error)
- Migration needed from `ott_user_project:{chat_id}` to new schema (user-driven, no automated script)
- **Sprint 207 blocker**: `pg_trgm` GIN index migration must run before `/workspace set <name>` works

### Neutral
- +1 Redis key namespace (`ott:workspace:*`) — negligible memory footprint (< 512 bytes per workspace)
- +~80 LOC new service `workspace_service.py`
- ~3 files modified (`telegram_responder.py`, `ai_response_handler.py`, `governance_action_handler.py`)
- 1 Alembic migration: `pg_trgm` GIN index on `projects.name`
- Legacy key `ott_user_project:{chat_id}` persists until Sprint 209 — two key schemas coexist temporarily

---

## 5. Implementation Scope (Sprint 207)

### New Files

**`backend/app/services/agent_bridge/workspace_service.py`** (~80 LOC)
```python
_WORKSPACE_KEY = "ott:workspace:{channel}:{chat_id}"
_WORKSPACE_TTL = 604800  # 7 days

async def get_workspace(channel, chat_id, redis) -> WorkspaceContext | None
async def set_workspace(channel, chat_id, project_id, project_name, tier, sdlc_stage, sender_id, redis) -> None
async def clear_workspace(channel, chat_id, redis) -> None
async def touch_workspace_ttl(channel, chat_id, redis) -> None
```

**`backend/tests/unit/test_sprint207_ott_workspace.py`** (~150 LOC)
- 15 unit tests covering all FR-049 scenarios (13 original + D-01b multi-match + D-14 Redis failure)

**`backend/alembic/versions/s207_001_projects_name_trgm_index.py`** (NEW — Day 1 prerequisite)
- `CREATE EXTENSION IF NOT EXISTS pg_trgm`
- `CREATE INDEX CONCURRENTLY idx_projects_name_trgm ON projects USING GIN (name gin_trgm_ops)`

### Modified Files

| File | Change |
|------|--------|
| `telegram_responder.py` | Add `/workspace` + `/workspace_set` + `/workspace_list` + `/workspace_clear` to static commands |
| `ai_response_handler.py` | Add workspace slash mappings to `_SLASH_TO_GOVERNANCE` |
| `governance_action_handler.py` | Extend `_resolve_project_id()` with Redis workspace lookup (Priority 2) + `touch_workspace_ttl()` |

### Deprecated (Sprint 209 removal)

- `ott_team_bridge.py`: `_USER_PROJECT_KEY = "ott_user_project:{chat_id}"` → replaced by `ott:workspace:{channel}:{chat_id}`

---

## 6. Test Strategy

| Test | Type | Covers |
|------|------|--------|
| `test_set_workspace_by_name` | Unit | FR-049-01 (name match) |
| `test_set_workspace_by_uuid` | Unit | FR-049-01 (UUID direct) |
| `test_set_workspace_not_found` | Unit | FR-049-01 (not found) |
| `test_set_workspace_no_access` | Unit | FR-049-01 (403) |
| `test_get_workspace_active` | Unit | FR-049-02 (show info) |
| `test_get_workspace_empty` | Unit | FR-049-02 (no workspace) |
| `test_list_workspace_projects` | Unit | FR-049-03 |
| `test_clear_workspace` | Unit | FR-049-04 |
| `test_governance_uses_workspace` | Unit | FR-049-05 (auto-inject) |
| `test_explicit_project_overrides_workspace` | Unit | FR-049-05 (override) |
| `test_no_workspace_no_default_error` | Unit | FR-049-05 (error) |
| `test_group_vs_dm_scoping` | Unit | FR-049-06 (scoping) |
| `test_workspace_ttl_reset_on_use` | Unit | D-067-02 (TTL reset) |

---

## 7. Review History

| Date | Reviewer | Decision |
|------|----------|---------|
| Feb 2026 | PM (@pm) | DRAFT created |
| - | CTO | Pending review |
