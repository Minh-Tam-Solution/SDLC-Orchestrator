# Scope: MTClaw Best Practice Adoption (Sprint 215-219)

**Version**: 1.0.0
**Status**: APPROVED
**Created**: March 2026
**Framework**: SDLC 6.1.1
**Epic**: EP-07 Multi-Agent Team Engine — MTClaw Restructure
**ADR**: ADR-069 (MTClaw Best Practice Adoption)
**CTO Verdict**: 8.5/10 — APPROVED WITH 4 CORRECTIONS

---

## 1. In Scope

### Sprint 215: Foundation Cleanup

- Delete context_authority.py v1 facade (69 LOC) and 3 legacy test files (~200 LOC)
- Clean Team.settings dead keys and dead schema properties
- Unify 4 role systems into single role_resolver.py (~100 LOC)
- Fix OTT bridge team_id on all creation paths
- Fix CLI role bug: "viewer" -> "member"

### Sprint 216: P1 Context Injection

- delegation_links table (source -> target agent FK, link_type, is_active)
- Context injector service: DELEGATION.md, TEAM.md, AVAILABILITY.md generation
- Spawn tool guard (reject unauthorized delegation)
- teams.lead_agent_definition_id FK addition
- Preset persistence to delegation_links

### Sprint 217: P2a Skills Engine

- skill_definitions table (5-tier, tsvector with 'simple' tokenizer)
- Skill loader (5-tier hierarchy, workspace overrides global)
- BuildSummary XML for system prompt injection

### Sprint 218: P2b Skills + P3 Bootstrap

- skill_agent_grants junction table
- Per-agent grants + tsvector search
- Bootstrap file loader (6 files: AGENTS/IDENTITY/TOOLS/MEMORY/HEARTBEAT/DELEGATION)
- FilterForSession() at conversation creation time

### Sprint 219: Router + tsvector Migration

- 4-phase tsvector migration for agent_definitions (ADD -> backfill -> GENERATED -> GIN)
- Deterministic 4-level router (0ms LLM latency)
- Wire context injector to system prompt builder
- Routing evidence log

---

## 2. Out of Scope

| Item | Reason | Deferred To |
|------|--------|-------------|
| handoff_routes table | Level 3 routing not needed until multi-team | S220+ |
| delegation_history table | Enhanced audit, not MVP-critical | S220+ |
| team_tasks table | Operational, context injection is higher priority | S220+ |
| team_messages table | Operational, deferred | S220+ |
| Tenant daily request limit | Cost guardrail, implement when agent loops observed | S220+ |
| SOUL.md, BOOTSTRAP.md, USER.md | Nice-to-have bootstrap files | S220+ |
| BM25 in-memory search | tsvector DB search sufficient for MVP | S220+ |
| Filesystem watcher for skills | Manual reload sufficient; watcher is optimization | S220+ |
| pgvector embedding search | Requires embedding model infra | S220+ |
| skill_search tool for agents | Only needed when >15 skills per agent | S220+ |
| Interface parity (CLI/Web/Extension) | After foundation stabilized | S220+ |
| MAX_COMMANDS ceiling evaluation | After Router Agent validated | S220+ |
| LLM-based routing (Level 3 handoff) | Deterministic routing sufficient for MVP | S220+ |
| Cross-team delegation | Single-team MVP first | S220+ |
| Delegation approval workflow | Admin-managed delegation sufficient | S220+ |

---

## 3. Constraints

| Constraint | Detail |
|-----------|--------|
| ADR-056 LD#1 | Snapshot immutability — FilterForSession at creation time, not query time |
| MAX_COMMANDS=10 | Router Agent is additive, does not replace existing commands |
| tsvector 'simple' | Not 'english' — Vietnamese text + code tokens must work |
| AGPL containment | No new AGPL dependencies introduced |
| Backward compatible | All existing agents, conversations, and commands continue working |
| Phased delivery | P2a (model+loader) can ship independently of P2b (search+grants) |
| Migration safety | tsvector backfill batches 100 rows, no table locks |

---

## 4. Dependencies

| Sprint | Depends On | Type |
|--------|-----------|------|
| 216 | 215 (dead code removed, roles unified) | Sequential |
| 217 | 216 (context injector exists for BuildSummary wiring) | Sequential |
| 218 | 217 (skill_definitions table exists) | Sequential |
| 219 | 216 (context injector for prompt builder wiring) | Sequential |

---

## 5. Success Metrics

| Metric | Target |
|--------|--------|
| Total LOC added | ~1,350 |
| New tables | 3 (delegation_links, skill_definitions, skill_agent_grants) |
| ALTER tables | 2 (teams + agent_definitions) |
| Context injection latency (cache hit) | < 5ms |
| Context injection latency (cache miss) | < 50ms |
| Router decision latency | < 20ms (0ms LLM) |
| Token budget compliance | DELEGATION <=2000, TEAM <=1500, AVAILABILITY <=200 |
| Existing commands preserved | 10/10 |
| Test coverage per sprint | >= 90% of new code |

---

## 6. Risk Register

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| tsvector backfill locks table | Low | Medium | Batch 100, maintenance window |
| 5-sprint commitment delays | Medium | Medium | Pause after S216 if priorities shift |
| FilterForSession breaks existing | Low | High | Only new child conversations affected |
| 'simple' tokenizer misses stems | Low | Low | Acceptable for Vietnamese + code |
| Skills filesystem dependency | Low | Medium | DB fallback always available |
