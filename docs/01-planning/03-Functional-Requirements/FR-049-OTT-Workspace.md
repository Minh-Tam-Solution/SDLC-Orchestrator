---
sdlc_version: "6.1.1"
document_type: "Functional Requirement"
status: "DRAFT"
sprint: "207"
spec_id: "FR-049"
tier: "STANDARD"
stage: "01 - Planning"
---

# FR-049: OTT Workspace Context Management

**Version**: 1.0.0
**Status**: DRAFT (Sprint 207 — Pending CTO Review)
**Created**: February 2026
**Sprint**: 207
**Framework**: SDLC 6.1.1
**Epic**: EP-07 Multi-Agent Team Engine
**ADR**: ADR-067 (OTT Workspace Context)
**Owner**: Backend Team
**Reference Pattern**: EndiorBot `switch.ts` + `session-manager.ts` (ADR-002 Project Context Switching)

---

## 1. Overview

### 1.1 Purpose

Enable OTT channel users (Telegram, Zalo) to set and switch an **active workspace** (project context) via chat commands. Once a workspace is set, governance commands (`/gates`, `/approve`, `/evidence`, etc.) automatically use the active project without requiring explicit `project_id` parameters.

### 1.2 Problem Being Solved

| Before FR-049 | After FR-049 |
|--------------|-------------|
| `/gates` → Error: "No project context. Provide --project-id" | `/gates` → Auto-uses active workspace |
| Must type full UUID each command | Set once, use forever (7-day TTL) |
| `OTT_DEFAULT_PROJECT_ID` env var (admin-only, one project for all users) | Per-user, per-channel workspace binding |
| Cannot switch project via chat | `/workspace set bflow` switches instantly |

### 1.3 Business Value

- **Conversation-First UX**: Users stay in flow without context-switching fatigue
- **Multi-project teams**: PM can monitor 3 projects, switch instantly
- **OTT as primary interface**: Enables daily standups, gate approvals, sprint updates — all from Telegram

### 1.4 Scope Boundary

| In scope | Out of scope |
|----------|-------------|
| Telegram (all chat types — DM + group + channel) | Slack integration (Sprint 209+) |
| Zalo OA channel — **Sprint 208+, NOT Sprint 207** (Telegram MVP only) | Discord integration |
| `workspace_service.py` Redis CRUD | File system workspace (CLI concern) |
| `governance_action_handler.py` workspace injection | Agent team conversation project binding (separate concern, ADR-056) |

---

## 2. Functional Requirements

### 2.1 Workspace Commands

#### FR-049-01: `/workspace set <name-or-id>`

**Description**: Set the active workspace for the current chat session.

```gherkin
Scenario: Set workspace by project name
  GIVEN user has not set a workspace
  AND user has access to project "BFlow Platform" (id: "uuid-bflow")
  WHEN user sends "/workspace set bflow"
  THEN backend searches projects by name (case-insensitive, partial match)
  AND Redis stores HASH at key "ott:workspace:telegram:{chat_id}":
      project_id = "uuid-bflow"
      project_name = "BFlow Platform"
      tier = "PROFESSIONAL"
      sdlc_stage = "04-BUILD"
      set_at = <ISO timestamp>
      set_by = <sender_id>
  AND TTL set to 604800 seconds (7 days)
  AND bot replies:
      "✅ Workspace set to: BFlow Platform
       Tier: 🟣 PROFESSIONAL | Stage: 04-BUILD
       All governance commands will use this project.
       Type /workspace to check anytime."
```

```gherkin
Scenario: Set workspace by project UUID
  GIVEN user sends "/workspace set abc123ef-0000-0000-0000-000000000001"
  WHEN UUID format is detected (hyphenated 36-char)
  THEN skip name search, validate UUID directly via backend
  AND proceed same as name-based flow
```

```gherkin
Scenario: Multiple projects match name (P0-1 disambiguation)
  GIVEN user sends "/workspace set platform"
  WHEN ILIKE search returns 2–5 projects matching "platform"
  THEN workspace is NOT set automatically
  AND bot replies with numbered disambiguation list:
      "🔍 Multiple projects match 'platform'. Use UUID to set exactly:
       1. 🟣 BFlow Platform (PROFESSIONAL) — /workspace set abc123ef-0000-0000-0000-000000000001
       2. 🔵 Demo Platform (STANDARD) — /workspace set def456ab-0000-0000-0000-000000000002
       Use the exact UUID above, or try a more specific name."
  NOTE: max 5 matches returned to prevent message overflow
  NOTE: if >5 matches, show first 5 and append "...and N more. Use a more specific name."
```

```gherkin
Scenario: Project not found
  GIVEN user sends "/workspace set nonexistent-project"
  WHEN no project matches the name
  THEN bot replies:
      "❌ Project 'nonexistent-project' not found.
       Use /workspace list to see your projects."
```

```gherkin
Scenario: Project found but no access
  GIVEN user sends "/workspace set secret-project"
  WHEN project exists but user is not a member
  THEN bot replies:
      "❌ Access denied. You are not a member of 'secret-project'.
       Contact your project owner to be added."
```

---

#### FR-049-02: `/workspace` (show current)

```gherkin
Scenario: Show active workspace
  GIVEN user has set workspace to "BFlow Platform"
  WHEN user sends "/workspace"
  THEN bot replies:
      "📂 Active Workspace
       ──────────────────────
       Project: BFlow Platform
       Tier: 🟣 PROFESSIONAL
       Stage: 04-BUILD
       Active Gates: G3 (IN_PROGRESS)
       Set: 2 hours ago

       Commands: /gates /approve /evidence /sprint_status"
```

```gherkin
Scenario: No active workspace
  GIVEN user has not set a workspace
  WHEN user sends "/workspace"
  THEN bot replies:
      "📂 No active workspace.
       Set one with: /workspace set <project-name>
       List your projects: /workspace list"
```

---

#### FR-049-03: `/workspace list`

```gherkin
Scenario: List accessible projects
  GIVEN user is member of 3 projects
  WHEN user sends "/workspace list"
  THEN bot queries GET /api/v1/projects?member=me&limit=10 (filtered by user membership)
  AND returns formatted list (max 10 projects):
      "📋 Your Projects
       ──────────────────────
       ▶ 🟣 BFlow Platform [ACTIVE]
          Stage: 04-BUILD
       ○ 🔵 NQH Bot
          Stage: 03-INTEGRATE
       ○ 🟢 Demo Project
          Stage: 01-PLANNING

       Switch with: /workspace set <name>"
  NOTE: "▶" marker indicates currently active workspace
  NOTE: gate counts are NOT shown (prevent N+1 queries — 1 query for all projects, no per-project gate count JOIN)
```

```gherkin
Scenario: No accessible projects
  GIVEN user is not a member of any project
  WHEN user sends "/workspace list"
  THEN bot replies:
      "📋 No projects found.
       Create one via the web dashboard or ask your admin."
```

---

#### FR-049-04: `/workspace clear`

```gherkin
Scenario: Clear workspace binding
  GIVEN user has active workspace "BFlow Platform"
  WHEN user sends "/workspace clear"
  THEN service reads current workspace name BEFORE deleting
  AND Redis key "ott:workspace:telegram:{chat_id}" is deleted
  AND bot replies:
      "🗑️ Workspace cleared (was: BFlow Platform). No active project.
       Use /workspace set <name> to set a new one."

Scenario: Clear workspace when already empty
  GIVEN user has NOT set a workspace (TTL expired or never set)
  WHEN user sends "/workspace clear"
  THEN no Redis key to delete
  AND bot replies:
      "📂 No active workspace to clear."
```

---

### 2.2 Governance Command Auto-Injection

#### FR-049-05: Auto-inject workspace project_id

```gherkin
Scenario: Governance command uses workspace project_id
  GIVEN user has active workspace with project_id "uuid-bflow"
  AND user sends "/gates" (no explicit project_id)
  WHEN governance_action_handler.py processes the command
  THEN handler reads Redis key "ott:workspace:telegram:{chat_id}"
  AND injects project_id = "uuid-bflow" into command arguments
  AND executes GET /api/v1/gates?project_id=uuid-bflow
  AND TTL of workspace key is reset to 604800 seconds (7 days)
```

```gherkin
Scenario: Explicit project_id overrides workspace
  GIVEN user has active workspace with project_id "uuid-bflow"
  AND user sends "/gates uuid-nqhbot" (explicit project_id)
  WHEN governance_action_handler.py processes the command
  THEN explicit project_id "uuid-nqhbot" is used (workspace ignored for this command)
  AND workspace binding is NOT changed
```

```gherkin
Scenario: No workspace, no explicit project_id
  GIVEN user has NOT set a workspace
  AND OTT_DEFAULT_PROJECT_ID env var is empty
  AND user sends "/gates" (no explicit project_id)
  WHEN governance_action_handler.py processes the command
  THEN bot replies:
      "⚠️ No project context.
       Set your workspace first: /workspace set <project-name>"
```

---

### 2.3 Workspace Scoping

#### FR-049-06: Group vs DM scoping

| Chat Type | Workspace Scope | Redis Key |
|-----------|----------------|-----------|
| Telegram private (DM) | Per user | `ott:workspace:telegram:{user_id}` |
| Telegram group/supergroup | Per group | `ott:workspace:telegram:{group_id}` |
| Telegram channel | Per channel | `ott:workspace:telegram:{channel_id}` |
| Zalo | Per user | `ott:workspace:zalo:{user_id}` |

**Rationale**: Group workspace = team shared context (all members use same active project). Individual DM workspace = personal context.

```gherkin
Scenario: Group override — last-write-wins (P0-4)
  GIVEN group chat has active workspace set to "NQH Bot" by @user1
  AND @user2 sends "/workspace set bflow"
  WHEN backend processes the set command
  THEN workspace is overwritten with "BFlow Platform"
  AND set_by = @user2's sender_id
  AND bot replies:
      "✅ Workspace set to: BFlow Platform
       Tier: 🟣 PROFESSIONAL | Stage: 04-BUILD
       ⚠️ Previous workspace (NQH Bot set by @user1) was overridden."
  NOTE: last-write-wins is intentional — no locking required
  NOTE: reply includes previous project name and who set it for group transparency
```

---

## 3. Non-Functional Requirements

| NFR | Target |
|-----|--------|
| Workspace lookup latency | < 5ms (Redis HGETALL) |
| Project search latency | < 100ms (PostgreSQL ILIKE with limit 5, requires pg_trgm GIN index on `projects.name`) |
| Redis memory per workspace | < 512 bytes (7 HASH fields) |
| Workspace TTL | 7 days, reset on every **successful** governance command execution |
| Max projects per list | 10 (prevent message truncation in Telegram) |
| Max name matches returned | 5 (disambiguation list, prevent message overflow) |
| Redis failure behavior | **Graceful degradation** — `get_workspace()` returns `None` on `ConnectionError`/`RedisError` (non-fatal, falls through to env-var default). Workspace SET commands fail with user-visible error: "⚠️ Workspace service temporarily unavailable." |

**TTL touch precision** (P1-3): TTL is reset to 7 days exactly when:
- ✅ Governance command executes successfully with workspace-injected `project_id`
- ✅ `/workspace` (info view) — any interaction with workspace resets TTL
- ✅ `/workspace list` — workspace query resets TTL
- ❌ Failed governance command (project not found, 403, validation error) — TTL is NOT reset
- ❌ `/workspace set` — TTL is initialized to 7 days on create, not "reset"
- ❌ Explicit `project_id` in message (workspace was not used) — TTL is NOT reset

**Legacy key migration** (P1-2): Users who previously had `ott_user_project:{chat_id}` set will see "No workspace set" on first use after Sprint 207 deploys. This is expected — the migration is user-driven (run `/workspace set <name>` once). The old key is NOT read as fallback; it continues to be read by `ott_team_bridge.py` for multi-agent flows (separate concern) until Sprint 209+ cleanup.

---

## 4. Security Considerations

- **Authorization always re-verified**: Redis workspace caches `project_id` only — permissions checked against PostgreSQL on every governance command
- **No PII in workspace key**: Key uses `chat_id` (Telegram numeric ID), not username or email
- **TTL-based expiry**: 7-day TTL prevents stale bindings for transferred devices/accounts
- **Injection prevented**: Workspace `project_id` is a UUID — validated via `uuid.UUID()` before DB query

---

## 5. Implementation Notes

**New service**: `backend/app/services/agent_bridge/workspace_service.py`
- `get_workspace(channel, chat_id, redis)` → `WorkspaceContext | None`
- `set_workspace(channel, chat_id, project_id, project_name, tier, sdlc_stage, sender_id, redis)` → `None`
- `clear_workspace(channel, chat_id, redis)` → `None`
- `touch_workspace_ttl(channel, chat_id, redis)` → `None` (reset TTL on use)

**Modified files**:
- `telegram_responder.py` — add `/workspace` guidance text to `_COMMAND_REPLIES`
- `ai_response_handler.py` — add `/workspace*` slash mappings to `_SLASH_TO_GOVERNANCE` (routing only, NO DB access)
- `governance_action_handler.py` — add `_execute_workspace_command()` dispatch + `_resolve_project_id()` workspace injection

**Architectural note** (CTO review 2): `/workspace set` and `/workspace list` require DB queries — they MUST be implemented in `governance_action_handler.py` (which creates `AsyncSessionLocal()` per command), NOT in `ai_response_handler.py` (which has no DB access).

**References**:
- EndiorBot `switch.ts` — `ActiveProjectState` + `saveState()`/`loadState()` pattern
- EndiorBot `session-manager.ts` — `switchProject()` saves/restores session per project
- Existing Redis key: `ott_user_project:{chat_id}` in `ott_team_bridge.py` → **migrate to new schema**

---

## 6. Acceptance Criteria (Sprint 207 DoD)

- [ ] `/workspace set bflow` (1 match) → stores Redis HASH, confirms project info
- [ ] `/workspace set platform` (multi-match) → disambiguation list with UUIDs, workspace NOT set
- [ ] `/workspace set nonexistent` → "not found" error with `/workspace list` hint
- [ ] `/workspace set secret` (no access) → "access denied" error
- [ ] `/workspace` → formatted project card when workspace active
- [ ] `/workspace` → guidance text when no workspace (expired/never set)
- [ ] `/workspace list` → user's projects (max 10), `▶` on active, NO gate counts (N+1 prevention)
- [ ] `/workspace clear` (active) → "was: BFlow Platform" confirmation
- [ ] `/workspace clear` (already empty) → "No active workspace to clear"
- [ ] `/gates` (no explicit project_id, workspace set) → uses workspace project_id, resets TTL
- [ ] `/gates <explicit-uuid>` (workspace set) → uses explicit UUID, workspace binding unchanged
- [ ] No workspace + no `OTT_DEFAULT_PROJECT_ID` → error with guidance
- [ ] Group chat: workspace scoped to group_id, shared; last-write-wins with override notice
- [ ] DM: workspace scoped to user_id, private
- [ ] Redis unavailable → `get_workspace()` returns None, falls through to env-var, no crash
- [ ] TTL reset only on successful governance command (not on failure)
- [ ] `_execute_workspace_command()` lives in `governance_action_handler.py` (NOT `ai_response_handler.py`)
- [ ] Alembic migration for `pg_trgm` GIN index on `projects.name` applied
- [ ] 15/15 tests in `test_sprint207_ott_workspace.py` pass (13 original + 2 added: D-01b multi-match, D-14 Redis failure)
