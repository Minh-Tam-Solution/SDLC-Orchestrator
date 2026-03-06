---
sdlc_version: "6.1.1"
document_type: "Architecture Decision Record"
status: "APPROVED"
sprint: "215-219"
spec_id: "ADR-069"
tier: "PROFESSIONAL"
stage: "02 - Design"
owner: "CTO"
---

# ADR-069 — MTClaw Best Practice Adoption

**Status**: APPROVED (CTO Verdict 8.5/10 — 4 corrections applied)
**Date**: March 2026
**Author**: Architect + CTO
**Sprint**: Sprint 215-219
**Framework**: SDLC 6.1.1
**Supersedes**: None
**References**: ADR-056 (Multi-Agent Team Engine), ADR-058 (ZeroClaw Hardening), FR-051 through FR-054

---

## 1. Context

### 1.1 Problem Statement

SDLC Orchestrator's multi-agent system (EP-07, ADR-056) has functioning agents with DB rows, but:

- Agents have no runtime awareness of delegation targets, team structure, or capabilities
- No skills discovery mechanism — agents can't find or share expertise
- Agent personality defined only in DB system_prompt — no file-based configuration
- Router requires LLM call for every message — 300ms+ latency

| Gap | Current State | MTClaw Pattern |
|-----|---------------|----------------|
| Agents cannot see delegation targets | No context about who can delegate to whom | `resolver.go` dynamically generates DELEGATION.md |
| No team awareness in LLM context | Agent has no visibility into team structure | `resolver.go` generates TEAM.md with roles + capabilities |
| No availability context | Agent does not know which teammates are online | `resolver.go` generates AVAILABILITY.md |
| No skill discovery | Skills are hardcoded in system prompts | `search.go` + `loader.go` provide 5-tier hierarchy with tsvector search |
| Agent personality is code-embedded | System prompts are database strings, not inspectable files | `files.go` loads AGENTS.md, IDENTITY.md, TOOLS.md from workspace |
| Message routing requires LLM | @mention resolution uses LLM reasoning | Deterministic 4-level router (0ms LLM latency) |
| Role system fragmented | `sdlc_role`, `role`, `team_role` used inconsistently | Single `role_resolver.py` unifies 4 role sources |

### 1.2 MTClaw Reference Implementation

MTClaw (Go, ~2K LOC) fully realizes 3 pattern groups we're missing:

- **P1: Context Injection** — resolver.go (475 LOC) dynamically generates DELEGATION.md/TEAM.md/AVAILABILITY.md
- **P2: Skills Engine** — 5-tier skills hierarchy with BM25 search, per-agent grants, BuildSummary
- **P3: Bootstrap Files** — File-based agent personality (8 templates) loaded from workspace

### 1.3 Verification

All claims verified against MTClaw production code:

- resolver.go 475 LOC, loader.go 361 LOC, search.go 201 LOC, watcher.go 174 LOC
- Located at: `/home/nqh/shared/MTClaw/internal/agent/resolver.go`, `/home/nqh/shared/MTClaw/internal/skills/loader.go`, etc.

---

## 2. Decision

### 2.1 Adopt 3 MTClaw Pattern Groups

**D-069-01 (LOCKED): Context Injection via Dynamic Markdown**

- Port MTClaw resolver.go pattern: dynamically generate DELEGATION.md, TEAM.md, AVAILABILITY.md before every LLM call
- DELEGATION.md: list delegation targets from `delegation_links` table (max 15, with search instruction for overflow)
- TEAM.md: differentiate lead vs member content (mandatory task->spawn workflow for leads)
- AVAILABILITY.md: negative context when agent has 0 targets (prevents hallucinated @mentions)
- Cache key: `(agent_id, team_id, max(delegation_links.updated_at))`, TTL 300s
- Token budgets: DELEGATION <=2000, TEAM <=1500, AVAILABILITY <=200
- All injected content wrapped in XML tags, user content XML-escaped

**Injection Format**:
```xml
<system_context>
<delegation>
## Delegation Targets
- @coder-alpha (role: coder, capabilities: Python, FastAPI)
- @reviewer-beta (role: reviewer, capabilities: security, code review)
</delegation>
<team>
## Team: Backend Squad
Lead: @architect-prime
Members: @coder-alpha (active), @reviewer-beta (active), @tester-gamma (idle)
</team>
<availability>
## Availability
Online: @coder-alpha, @reviewer-beta
Offline: @tester-gamma (last seen: 2h ago)
</availability>
</system_context>
```

**D-069-02 (LOCKED): Skills Engine with Phased Delivery**

- P2a (Sprint 217): skill_definitions table + 5-tier loader + BuildSummary
- P2b (Sprint 218): skill_agent_grants table + tsvector search + per-agent grants
- If P2a ships and P2b slips, skill registry still works with manual assignment
- 5-tier priority: workspace > project_agent > personal_agent > global > builtin
- tsvector with 'simple' tokenizer (not 'english') — no stopwords, Vietnamese + code tokens
- BM25 in-memory deferred — tsvector DB search sufficient for MVP

**BuildSummary Example**:
```xml
<available_skills>
- gate-evaluate: Evaluate a quality gate against OPA policies (builtin)
- evidence-upload: Upload evidence artifact to vault (builtin)
- python-review: Review Python code for OWASP compliance (workspace)
</available_skills>
```

**D-069-03 (LOCKED): Bootstrap Files — 6 files, not 11**

- Include: AGENTS.md, IDENTITY.md, TOOLS.md, MEMORY.md, HEARTBEAT.md, DELEGATION.md
- Defer: SOUL.md, BOOTSTRAP.md, USER.md (nice-to-have)
- TEAM.md and AVAILABILITY.md are VIRTUAL (generated by P1 resolver at runtime, not on-disk)
- FilterForSession() at conversation CREATION time, not query time (ADR-056 LD#1 immutability)
- Subagent: AGENTS.md + TOOLS.md only (saves ~40% tokens)
- Workspace path SSOT: conversation.workspace_path -> team.settings -> project.root_path -> DEFAULT

**File Loading Rules**:
- Read from workspace path at conversation creation
- Content stored in `agent_conversations.metadata_` JSONB (key: `bootstrap_files`)
- Missing files silently skipped (not all workspaces will have all 6 files)
- Max file size: 10KB per file (prevent accidental large file injection)

**D-069-04 (LOCKED): Deterministic Router — Config Binding, Not Intelligence**

- 4-level routing with 0ms LLM latency:
  1. @mention -> named agent
  2. @team -> team's lead agent
  3. Active handoff -> per-conversation override (deferred)
  4. tsvector match -> ts_rank score threshold + top-3 fallback
- Routing evidence log for debugging (route_level, candidates, score, matched_terms)
- All 10 existing commands preserved (MAX_COMMANDS=10)
- 4-phase tsvector migration: ADD column -> backfill -> ADD GENERATED -> GIN index
- Backfill batch 100 rows, 'simple' tokenizer, include display_name

### 2.2 Delegation Links (New Table)

```sql
CREATE TABLE delegation_links (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source_agent_id UUID NOT NULL REFERENCES agent_definitions(id) ON DELETE CASCADE,
    target_agent_id UUID NOT NULL REFERENCES agent_definitions(id) ON DELETE CASCADE,
    link_type VARCHAR(50) NOT NULL DEFAULT 'can_delegate',
    is_active BOOLEAN NOT NULL DEFAULT true,
    metadata JSONB NOT NULL DEFAULT '{}',
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE(source_agent_id, target_agent_id, link_type)
);
```

### 2.3 Spawn Tool Guard

- Before creating child conversation, check `delegation_links.is_active = true` for (source, target)
- Reject with actionable error listing available targets
- Log `blocked_unauthorized_delegation` to agent_messages

---

## 3. Consequences

### 3.1 Positive

- Agents get accurate awareness of collaborators (no hallucinated @mentions)
- Deterministic routing eliminates 300ms+ LLM latency at gateway
- File-based agent personality enables version control of agent configs
- Skills engine enables capability discovery across agents
- Token-efficient: bounded budgets prevent context overflow
- MTClaw alignment: SDLC Orchestrator achieves feature parity with MTClaw agent context patterns
- Role clarity: single `role_resolver.py` eliminates confusion between 4 role sources

### 3.2 Negative

- 3 new tables + 2 ALTER migrations increase schema complexity
- 5-sprint commitment (~1,350 LOC total)
- Bootstrap file loading adds filesystem dependency (mitigated by DB fallback)
- Context injection latency: every LLM call pays injection cost (mitigated by 300s caching)

### 3.3 Risks

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| tsvector backfill locks table | Low | Medium | Batch 100 rows, run during maintenance |
| 5-sprint commitment delays other work | Medium | Medium | S217-S219 independently shippable; pause after S216 if priorities shift |
| FilterForSession breaks existing conversations | Low | High | Only new child conversations; existing snapshots untouched |
| 'simple' tokenizer misses stemmed matches | Low | Low | Acceptable for Vietnamese + code tokens |
| Context injection exceeds token budget | Low | Medium | Hard limits enforced (2000+1500+200); truncation with notice |
| Bootstrap files contain sensitive data | Low | High | Max 10KB per file; content sanitized; no credential patterns |
| Deterministic router misroutes messages | Medium | Low | Fallback: no routing (stays with current agent); tsvector is best-effort |

---

## 4. Alternatives Considered

### 4.1 LLM-Based Router (Rejected)

- 300ms+ latency per message
- Non-deterministic routing decisions
- Higher cost per request
- MTClaw proves deterministic routing is sufficient for agent collaboration

### 4.2 Embedding-Based Skills Search (Deferred)

- pgvector requires embedding model infrastructure
- tsvector provides adequate precision for <100 skills
- Can add embeddings later as optimization

### 4.3 Full 11 Bootstrap Files (Rejected per CTO)

- 11 files adds complexity without proportional value
- 6 files cover 90% of use cases
- TEAM.md and AVAILABILITY.md better as virtual (always fresh)

### 4.4 Single Sprint Delivery (Rejected)

- 1,350 LOC + 3 tables + 2 ALTER + 7 services in one sprint is too much risk
- Phased delivery allows each pattern group to stabilize before the next builds on it
- S215 foundation is prerequisite for S216, but S217-S219 are independently shippable

### 4.5 Two Columns (category + routing_description) Instead of frontmatter + tsvector (Rejected)

- `frontmatter` + generated `tsvector` is simpler
- One column serves dual purpose (human-readable metadata AND machine-searchable index)
- Two separate columns duplicates information and requires synchronization

---

## 5. Implementation Plan

| Sprint | Focus | LOC | Tables |
|--------|-------|-----|--------|
| 215 | Dead code + role unification | ~300 | 0 (cleanup) |
| 216 | P1 Context Injection + delegation | ~250 | +1 + 1 ALTER |
| 217 | P2a Skills Engine (model + loader) | ~200 | +1 |
| 218 | P2b Search + Grants + P3 Bootstrap | ~350 | +1 |
| 219 | tsvector migration + Router | ~250 | 0 (column adds) |
| **Total** | | **~1,350** | **+3, 2 ALTER** |

Dependency chain: S215 -> S216 -> S217 -> S218 -> S219

### 5.1 New Services (Key Files)

| File | LOC (est.) | Sprint | Purpose |
|------|------------|--------|---------|
| `role_resolver.py` | ~100 | 215 | Unify 4 role sources into single resolution |
| `delegation_service.py` | ~80 | 216 | `can_delegate()`, `get_targets()`, `create_link()`, `deactivate_link()` |
| `context_injector.py` | ~150 | 216 | 3 virtual MD builders with caching, token budgets, XML escaping |
| `skill_loader.py` | ~100 | 217 | 5-tier hierarchy loading with precedence resolution |
| `skill_search.py` | ~80 | 218 | tsvector search + `ts_rank()` scoring + per-agent grant filtering |
| `bootstrap_loader.py` | ~100 | 218 | 6 bootstrap file loading + FilterForSession + workspace path SSOT |
| `router_agent_service.py` | ~120 | 219 | 4-level deterministic routing (LD-3) |

Total new code: ~730 LOC across 7 service files.

### 5.2 Column Additions (2 ALTER)

```sql
-- teams: Lead agent concept (for @team mention routing)
ALTER TABLE teams ADD COLUMN lead_agent_definition_id UUID
    REFERENCES agent_definitions(id) ON DELETE SET NULL;

-- agent_definitions: frontmatter + tsvector for deterministic routing
ALTER TABLE agent_definitions ADD COLUMN frontmatter TEXT;
ALTER TABLE agent_definitions ADD COLUMN frontmatter_tsv tsvector
    GENERATED ALWAYS AS (to_tsvector('simple',
        COALESCE(agent_name, '') || ' ' || COALESCE(frontmatter, '')
    )) STORED;
CREATE INDEX idx_agent_def_frontmatter ON agent_definitions USING GIN(frontmatter_tsv);
```

### 5.3 Backfill Strategy

Existing `agent_definitions` rows need frontmatter populated for tsvector routing:

```sql
UPDATE agent_definitions SET frontmatter =
    'role: ' || COALESCE(sdlc_role, 'general') || E'\n' ||
    'provider: ' || COALESCE(provider, 'ollama')
WHERE frontmatter IS NULL;
```

Risk mitigation: batch 100 rows at a time during maintenance window.

---

## 6. CTO Corrections Applied

| # | Correction | Sprint |
|---|-----------|--------|
| V1 | Skills Engine phased (P2a/P2b) | 217/218 |
| V2 | Bootstrap Files 6, not 11 | 218 |
| V3 | tsvector backfill for existing data | 219 |
| V4 | FilterForSession at snapshot creation | 218 |

---

## 7. Testability Summary

| Decision | Module | Test IDs | Count |
|----------|--------|----------|-------|
| Foundation: Role Resolver | role_resolver.py | RR-01 to RR-06 | 6 |
| D1: Context Injection (P1) | context_injector.py | CI-01 to CI-09 | 9 |
| D2: Skills Engine (P2a) | skill_loader.py | SK-01, SK-02, SK-07, SK-08 | 4 |
| D2: Skills Search (P2b) | skill_search.py | SK-03 to SK-06 | 4 |
| D3: Bootstrap Files (P3) | bootstrap_loader.py | BS-01 to BS-08 | 8 |
| D4: Deterministic Router | router_agent_service.py | RT-01 to RT-08 | 8 |

Total test cases: 39 unit tests + integration tests per sprint.

Coverage rationale: all new modules are pure functions or deterministic logic with clear input/output contracts. 100% branch coverage is achievable.

---

## 8. Related Documents

| Document | Location | Status |
|----------|----------|--------|
| ADR-056 | `docs/02-design/01-ADRs/ADR-056-Multi-Agent-Team-Engine.md` | ACCEPTED |
| ADR-058 | `docs/02-design/01-ADRs/ADR-058-ZeroClaw-Best-Practice-Adoption.md` | ACCEPTED |
| Scope Document | `docs/01-planning/scope-sprint-215-219-mtclaw-adoption.md` | APPROVED |
| MTClaw Source | `resolver.go`, `loader.go`, `search.go`, `watcher.go`, `files.go` | Reference |
| ERD v3.4.0 | `docs/01-planning/04-Data-Model/Data-Model-ERD.md` | UPDATE REQUIRED (3 tables + 2 ALTER) |
| API Spec v3.6.0 | `docs/01-planning/05-API-Design/API-Specification.md` | UPDATE REQUIRED (delegation + skill endpoints) |
| Sprint 215-219 Plans | `docs/04-build/02-Sprint-Plans/` | TO BE CREATED |
