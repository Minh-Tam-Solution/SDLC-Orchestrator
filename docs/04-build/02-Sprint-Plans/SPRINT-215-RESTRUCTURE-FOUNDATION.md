---
sdlc_version: "6.1.1"
document_type: "Sprint Plan"
status: "APPROVED"
sprint: "215"
tier: "PROFESSIONAL"
stage: "04 - Build"
---

# Sprint 215 — Restructure Foundation: Dead Code + Role System Unification

**Sprint Duration**: March 2026
**Sprint Goal**: Remove dead code safely, unify 4 role systems into single resolver, fix OTT bridge team_id
**Status**: PLANNED
**Priority**: P0 (foundation cleanup before MTClaw adoption)
**Framework**: SDLC 6.1.1
**ADR**: ADR-069 (MTClaw Restructure)
**FRs**: FR-051, FR-052, FR-053, FR-054 (prerequisite cleanup)
**Previous Sprint**: [Sprint 214 — GDPR/Data Residency UI + Compliance Dashboard](SPRINT-214-GDPR-UI-COMPLIANCE-EXTENSION.md)

---

## Context

Sprint 214 completed the ENT compliance checklist (12/12) and pushed cross-interface coverage
to 86%. Before adopting MTClaw patterns (context injection, skills engine, deterministic router),
the codebase needs foundational cleanup: dead code from Sprint 190 conversation-first purge
still has leftover facades, the project has 4 separate role systems that have never been
unified, and the OTT bridge has a creation path that omits `team_id`.

This sprint is deliberately small (~300 LOC) to ensure zero regressions before the P0/P1
MTClaw adoption sprints that follow.

---

## Sprint Summary

| Track | Scope | Est. LOC | Impact |
|-------|-------|----------|--------|
| A | Dead code removal: CA v1 facade, legacy test files, dead Team.settings keys, dead schema properties | ~70 delete | Reduced surface area, cleaner imports |
| B | Role resolver service: unify 4 role systems into single resolver with Redis cache | ~100 new | Single source of truth for authorization lookups |
| C | OTT bridge team_id fix: ensure all creation paths set team_id | ~30 fix | Prevents orphan conversations without team context |
| D | Tests: role resolver, import integrity, OTT bridge coverage | ~100 new | Regression safety for all 3 tracks |
| **Total** | | **~300 LOC** | **Foundation ready for MTClaw adoption** |

---

## Track A — Dead Code Removal

### A1: Delete context_authority.py v1 facade

- Delete `backend/app/services/context_authority.py` (69 LOC)
- This is the v1 facade; v2 lives at `backend/app/services/governance/context_authority_v2.py`
- Verify zero imports reference the v1 path before deletion
- Sprint 190 already removed the route; this deletes the orphan service file

### A2: Delete legacy CA v1 test files

- Delete 3 test files that test the removed v1 facade (~200 LOC total)
- Grep for `test_context_authority` files in `backend/tests/unit/`
- Verify no shared fixtures are lost (extract to conftest if needed)

### A3: Clean Team.settings dead keys

- Remove references to 4 dead keys in Team model documentation and schema defaults:
  - `default_gate_approvers` — never populated, gate approval uses GateApproval model
  - `notification_channel` — replaced by OTT gateway in Sprint 178
  - `webhook_url` — replaced by OTT gateway in Sprint 178
  - `auto_assign_projects` — never implemented, project assignment is manual
- Update any schema validators that reference these keys
- Do NOT alter existing DB rows (they are harmless JSONB noise)

### A4: Clean dead schema properties

- Remove `mentor_scripts` and `briefing_templates` from agent definition schemas
- These were placeholder properties from Sprint 176 planning, never persisted or read
- Update Pydantic schemas only; no DB migration needed (JSONB ignores unknown keys)

### A5: Do NOT delete (documented exclusions)

- `analytics_service.py` v1 — still has active consumers in dashboard routes
- `context_authority_v2.py` — active engine, FROZEN since Sprint 173
- `sase_generation_service.py` — has VCR/CRP dependencies, deferred to Sprint 191+

---

## Track B — Role Resolution Layer

### B1: New service file

- NEW: `backend/app/services/agent_team/role_resolver.py` (~100 LOC)
- Single class `RoleResolver` with dependency injection for DB session and Redis client

### B2: Unify 4 role systems

The resolver handles all 4 role systems through a single `resolve_roles(user_id, team_id, project_id)` method:

1. **User roles** (DB many-to-many via `user_roles` table)
   - Query: `SELECT role FROM user_roles WHERE user_id = :uid`
   - Returns: list of global roles (e.g., `admin`, `superadmin`)

2. **TeamRole** (enum on `team_members` table: OWNER | ADMIN | MEMBER | AI_AGENT)
   - Query: `SELECT role FROM team_members WHERE user_id = :uid AND team_id = :tid`
   - Returns: single TeamRole enum value

3. **ProjectMember.role** (string on `project_members` table: owner | admin | member | viewer)
   - Query: `SELECT role FROM project_members WHERE user_id = :uid AND project_id = :pid`
   - Returns: single string role

4. **FunctionalRole** (approval authority: PM | CTO | CEO | QA_LEAD | COMPLIANCE_OFFICER)
   - Derived from user profile or team assignment
   - Used by gate approval workflow

### B3: Redis caching

- Cache key: `roles:{user_id}:{team_id}:{project_id}`
- TTL: 300 seconds (5 minutes)
- Invalidate on: role assignment change, team membership change, project membership change

### B4: Fix CLI role bug

- File: `backend/sdlcctl/sdlcctl/commands/team.py`
- Bug: CLI sends `"viewer"` as default role for `team add-member`
- Fix: Change default to `"member"` (viewer is not a valid TeamRole enum value)

---

## Track C — Fix OTT Bridge team_id

### C1: Identify the missing path

- File: `backend/app/services/agent_team/ott_team_bridge.py`
- The `create_conversation_from_ott()` method has one code path (direct message
  without prior team context) that creates an `AgentConversation` without setting `team_id`
- This causes downstream failures in team-scoped queries

### C2: Fix implementation

- Add `team_id` resolution: look up the agent definition's team, fall back to user's default team
- If no team can be resolved, return a 400 error with actionable message
- Add assertion: `assert conversation.team_id is not None` before DB commit

---

## Track D — Tests

### D1: Role resolver tests

- `test_role_resolver.py` (~60 LOC)
- Test all 4 role systems return correct values
- Test Redis cache hit (second call skips DB)
- Test cache invalidation on role change
- Test missing user/team/project returns empty roles (not error)

### D2: Dead code removal integrity

- `test_sprint215_dead_code.py` (~20 LOC)
- Verify `context_authority.py` v1 does not exist
- Verify all backend imports resolve (no broken import chains)
- Verify `mentor_scripts` and `briefing_templates` absent from schemas

### D3: OTT bridge team_id

- `test_ott_bridge_team_id.py` (~20 LOC)
- Test: direct message path sets team_id
- Test: no team resolvable returns 400 error
- Test: team_id is never None after create_conversation_from_ott()

---

## Definition of Done

- [ ] `context_authority.py` v1 facade deleted, zero import breakage
- [ ] 3 legacy CA v1 test files deleted
- [ ] Dead Team.settings keys documented as deprecated in schema
- [ ] `mentor_scripts` and `briefing_templates` removed from Pydantic schemas
- [ ] `role_resolver.py` handles all 4 role systems correctly
- [ ] Redis cache for role resolution with 300s TTL
- [ ] CLI team command default role fixed: `"viewer"` changed to `"member"`
- [ ] OTT bridge `team_id` set on all creation paths
- [ ] All Sprint 215 tests passing
- [ ] Combined Sprint 209-215 tests passing
- [ ] CURRENT-SPRINT.md updated

---

## Risks

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Dead code deletion breaks hidden import | Low | High | Grep all imports before deletion; run full test suite after |
| Role resolver cache stale data | Medium | Medium | Short TTL (300s) + explicit invalidation on write paths |
| OTT bridge fix changes conversation creation contract | Low | Medium | Backward-compatible — only adds team_id where missing |

---

## Dependencies

- **Upstream**: Sprint 214 complete (GDPR UI, compliance dashboard)
- **Downstream**: Sprint 216 (Context Injection) depends on role_resolver for authorization checks
- **Infrastructure**: Redis (port 6395) for role cache
- **No new DB tables**: 0 migrations in this sprint
