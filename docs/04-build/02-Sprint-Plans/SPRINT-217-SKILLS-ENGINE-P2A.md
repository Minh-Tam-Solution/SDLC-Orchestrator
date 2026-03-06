---
sdlc_version: "6.1.1"
document_type: "Sprint Plan"
status: "APPROVED"
sprint: "217"
tier: "PROFESSIONAL"
stage: "04 - Build"
---

# Sprint 217 — P2a Skills Engine: Model + Loader

**Sprint Duration**: March 2026
**Sprint Goal**: Implement skills table, 5-tier loader, and BuildSummary for system prompt injection
**Status**: PLANNED
**Priority**: P1
**Framework**: SDLC 6.1.1
**ADR**: ADR-069 (MTClaw Restructure)
**FRs**: FR-052 (Skills Engine — P2a model + loader)
**Previous Sprint**: [Sprint 216 — Context Injection + Delegation Links](SPRINT-216-CONTEXT-INJECTION.md)

---

## Context

Sprint 216 delivered the context injection foundation: delegation links, spawn tool guard, and
the 3-builder context injector (DELEGATION.md, TEAM.md, AVAILABILITY.md). Agents now know
who they can delegate to and what team they belong to.

The next gap is **skills**: agents need to know what capabilities are available beyond their
base system prompt. MTClaw's skills engine uses a 5-tier hierarchy where workspace-level skills
override global defaults, and each skill is a markdown file with YAML frontmatter parsed into
a tsvector for full-text search.

This sprint (P2a) focuses on the data model, the 5-tier loader, and a BuildSummary function
that generates an `<available_skills>` section for system prompt injection. P2b (Sprint 218)
adds per-agent grants and tsvector search.

---

## Sprint Summary

| Track | Scope | Est. LOC | Impact |
|-------|-------|----------|--------|
| A | skill_definitions table (Alembic migration + SQLAlchemy model) | ~60 new | Persistent skill storage with frontmatter tsvector |
| B | Skill loader service (5-tier hierarchy, frontmatter parser) | ~100 new | Priority-ordered skill resolution across 5 tiers |
| C | BuildSummary function integrated with context_injector | ~40 new | Agents see available skills in system prompt |
| D | Tests: CRUD, 5-tier override, BuildSummary XML format | ~60 new | Regression safety |
| **Total** | | **~260 LOC** | **Skills data model + loader operational** |

---

## Track A — Skills Table

### A1: Alembic migration

- NEW table: `skill_definitions`
- Columns:
  - `id` UUID PK (default uuid4)
  - `name` VARCHAR(100) NOT NULL
  - `slug` VARCHAR(100) NOT NULL UNIQUE — URL-safe identifier (e.g., `code-review`, `test-generation`)
  - `description` TEXT — human-readable summary
  - `frontmatter` TEXT — raw YAML-like frontmatter from SKILL.md header
  - `content` TEXT — full skill markdown content (instructions, examples, templates)
  - `tier` VARCHAR(20) NOT NULL — one of: `workspace`, `project_agent`, `personal_agent`, `global`, `builtin`
  - `visibility` VARCHAR(20) NOT NULL DEFAULT 'public' — one of: `public`, `private`, `internal`
  - `version` INTEGER NOT NULL DEFAULT 1 — monotonic version counter for optimistic concurrency
  - `workspace_path` VARCHAR(500) — filesystem path for workspace-tier skills (NULL for DB-only skills)
  - `frontmatter_tsv` tsvector GENERATED ALWAYS AS (to_tsvector('simple', COALESCE(name, '') || ' ' || COALESCE(frontmatter, ''))) STORED
  - `created_at` TIMESTAMP DEFAULT now()
  - `updated_at` TIMESTAMP DEFAULT now()
- Indexes:
  - GIN index on `frontmatter_tsv` for full-text search
  - UNIQUE index on `slug`
  - B-tree index on `tier` for filtered queries

### A2: Why 'simple' tokenizer (not 'english')

- Following MTClaw migration 000002 pattern
- No stopwords removed: "the", "a" are valid in code identifiers
- No stemming: "testing" and "test" remain distinct (important for skill matching)
- Vietnamese + code tokens preserved: `tsvector('simple', ...)` handles mixed-language content

### A3: SQLAlchemy model

- NEW: `backend/app/models/skill_definition.py`
- Follow `backend/app/models/vcr.py` pattern: UUID PK, enums for tier/visibility, `to_dict()` method
- Tier enum: `SkillTier(str, Enum)` with values `workspace`, `project_agent`, `personal_agent`, `global`, `builtin`
- Visibility enum: `SkillVisibility(str, Enum)` with values `public`, `private`, `internal`

---

## Track B — Skill Loader (5-Tier Hierarchy)

### B1: New service file

- NEW: `backend/app/services/agent_team/skill_loader.py` (~100 LOC)
- Class `SkillLoader` with dependency injection for DB session

### B2: 5-tier loading priority

Skills are loaded in priority order (highest priority first). When two skills share the same
slug, the higher-tier skill wins:

1. **workspace** (highest priority) — project-specific skills from workspace filesystem
2. **project_agent** — skills scoped to a specific agent within a project
3. **personal_agent** — skills scoped to a specific agent across all projects
4. **global** — organization-wide skills available to all agents
5. **builtin** (lowest priority) — system default skills shipped with the platform

Resolution algorithm:
```
seen_slugs = set()
resolved_skills = []
for tier in [workspace, project_agent, personal_agent, global, builtin]:
    skills = query_skills_by_tier(tier, agent_context)
    for skill in skills:
        if skill.slug not in seen_slugs:
            seen_slugs.add(skill.slug)
            resolved_skills.append(skill)
return resolved_skills
```

### B3: Frontmatter parser

- `parse_frontmatter(raw_text: str) -> dict`
- Simple YAML-like parser (no PyYAML dependency for this minimal format)
- Parses key-value pairs from `---` delimited header block
- Keys: `name`, `description`, `tier`, `tags`, `version`, `author`
- Malformed frontmatter returns empty dict (non-fatal, logged as warning)

### B4: Workspace skill file scanner

- `scan_workspace_skills(workspace_path: str) -> list[SkillDefinition]`
- Scans `{workspace_path}/.sdlc/skills/` directory for `*.md` files
- Each file is parsed: frontmatter extracted, slug derived from filename
- Returns in-memory SkillDefinition objects (not persisted until explicit save)

---

## Track C — BuildSummary

### C1: BuildSummary function

- NEW function in `skill_loader.py`: `build_summary(agent_id: UUID, team_id: UUID) -> str`
- Calls 5-tier loader to resolve accessible skills for the agent
- Generates XML section:
  ```xml
  <available_skills>
  You have access to the following skills:

  - code-review (tier: global) -- Performs structured code review with checklist
  - test-generation (tier: workspace) -- Generates pytest test cases from function signatures
  - security-scan (tier: builtin) -- Runs Semgrep SAST rules against code
  </available_skills>
  ```
- Token budget: <= 1000 tokens (truncate with "... and N more skills" if exceeded)

### C2: Integration with context_injector.py

- MODIFY: `backend/app/services/agent_team/context_injector.py`
- Add `build_skills_summary()` call in `inject_context()` method
- Order becomes: delegation -> team -> skills -> availability
- Skills section injected after team context, before availability constraints

---

## Track D — Tests

### D1: Skill model CRUD tests

- `test_skill_definitions.py` (~20 LOC)
- Test create skill with all fields populated
- Test slug UNIQUE constraint rejects duplicate
- Test tier and visibility enums reject invalid values
- Test `to_dict()` serialization includes all fields

### D2: 5-tier override tests

- `test_skill_loader.py` (~25 LOC)
- Test: workspace skill with slug "code-review" overrides global skill with same slug
- Test: builtin skills appear when no higher-tier override exists
- Test: empty workspace returns only global + builtin skills
- Test: frontmatter parser handles valid YAML-like header
- Test: malformed frontmatter returns empty dict (no crash)

### D3: BuildSummary tests

- `test_build_summary.py` (~15 LOC)
- Test: output wrapped in `<available_skills>` XML tags
- Test: each skill listed with slug, tier, and description
- Test: token budget exceeded triggers truncation with count message
- Test: agent with no accessible skills produces empty section

---

## Definition of Done

- [ ] `skill_definitions` table created with GIN index on frontmatter_tsv
- [ ] `slug` column has UNIQUE constraint
- [ ] `frontmatter_tsv` uses 'simple' tokenizer (not 'english')
- [ ] `SkillDefinition` model follows vcr.py pattern with `to_dict()`
- [ ] 5-tier loader resolves skills in correct priority order
- [ ] Workspace skill with same slug overrides global skill
- [ ] Frontmatter parser handles valid and malformed input without crash
- [ ] `build_summary()` generates correct XML section with token budget
- [ ] Context injector includes skills section in system prompt
- [ ] All Sprint 217 tests passing
- [ ] Combined Sprint 209-217 tests passing
- [ ] CURRENT-SPRINT.md updated

---

## Risks

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Workspace filesystem access denied in production container | Medium | Medium | Fall back to DB-only skills; log warning |
| tsvector GIN index slow on large skill corpus (>1000 skills) | Low | Low | GIN is optimized for this; monitor query plans |
| Frontmatter format diverges from MTClaw convention | Low | Medium | Document format spec in ADR; validate on import |
| Token budget for skills section competes with delegation budget | Medium | Medium | Hard cap per section; total system prompt budget tracked |

---

## Dependencies

- **Upstream**: Sprint 216 complete (context injector wired and operational)
- **Downstream**: Sprint 218 (P2b) adds per-agent grants and tsvector search on top of this model
- **Infrastructure**: PostgreSQL (skill_definitions table with GIN index)
- **References**: FR-052 (P2a scenarios), MTClaw skills/loader.go (361 LOC)
