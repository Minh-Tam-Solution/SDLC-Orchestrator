---
sdlc_version: "6.1.1"
document_type: "Functional Requirement"
status: "APPROVED"
sprint: "217-218"
spec_id: "FR-052"
tier: "PROFESSIONAL"
stage: "01 - Planning"
references: ["ADR-056", "ADR-058", "ADR-069"]
---

# FR-052: Skills Engine

**Version**: 2.0.0
**Status**: APPROVED
**Created**: March 2026
**Sprint**: 217-218
**Framework**: SDLC 6.1.1
**Epic**: EP-07 Multi-Agent Team Engine — MTClaw Restructure
**ADR**: ADR-056 (LD#1 Snapshot Precedence), ADR-058 (ZeroClaw Best Practices), ADR-069 (Skills Engine Architecture)
**Owner**: Backend Team
**Pattern Source**: MTClaw `skills/loader.go` (361 LOC), `skills/search.go` (201 LOC)

---

## 1. Overview

### 1.1 Purpose

Implement a 5-tier skills hierarchy engine that parses SKILL.md frontmatter files, resolves tier precedence (higher overrides lower for same slug), generates `<available_skills>` XML for system prompt injection via BuildSummary, and provides tsvector-based DB search. Skills are assigned to agents via a per-agent grants junction table, enabling fine-grained capability control without modifying agent definitions.

### 1.2 Problem Being Solved

| Before FR-052 | After FR-052 |
|--------------|-------------|
| Agent capabilities hardcoded in system_prompt text | Skills loaded dynamically from 5-tier hierarchy with override semantics |
| No structured discovery of agent capabilities | `<available_skills>` XML injected into system prompt with token budget |
| Skill assignment is implicit (all or nothing) | Per-agent grants via `skill_agent_grants` junction table |
| No search across available skills | tsvector DB search with `ts_rank` scoring and `simple` tokenizer |
| Skill definitions scattered across code | Centralized `skill_definitions` table with versioning and visibility |
| No Vietnamese/code token support in search | `simple` tokenizer works with Vietnamese + code tokens (not `english`) |
| No override mechanism for project-specific skills | 5-tier hierarchy: workspace overrides global for same slug |

### 1.3 Business Value

- **Modularity**: Skills are composable units — add/remove capabilities without changing agent definitions
- **Discoverability**: Agents and users can search for skills by keyword via tsvector
- **Token efficiency**: BuildSummary bounded to <= 1500 tokens, cache-friendly
- **Extensibility**: 5-tier hierarchy allows workspace-level overrides of global defaults
- **Access control**: Per-agent grants enable private skills visible only to authorized agents

### 1.4 Scope Boundary

| In scope | Out of scope |
|----------|-------------|
| `skill_definitions` table + CRUD (Sprint 217) | BM25 in-memory search (tsvector DB search sufficient for MVP) |
| 5-tier loader with precedence (Sprint 217) | Skill marketplace / sharing across workspaces (future) |
| SKILL.md frontmatter parser (Sprint 217) | Skill versioning UI (future) |
| BuildSummary XML generation (Sprint 217) | Skill dependency graph (future) |
| `skill_agent_grants` junction table (Sprint 218) | Skill execution runtime (skills define capability, not execute) |
| tsvector search with `simple` tokenizer (Sprint 218) | LLM-based semantic skill search (future) |
| Per-agent ListAccessible combining grants + visibility (Sprint 218) | Cross-workspace skill federation (future) |

### 1.5 Phased Delivery

| Phase | Sprint | Deliverables |
|-------|--------|-------------|
| P2a | 217 | `skill_definitions` model + Alembic migration, SKILL.md frontmatter parser, 5-tier loader, BuildSummary XML |
| P2b | 218 | `skill_agent_grants` table, tsvector search, per-agent grants, ListAccessible endpoint |

---

## 2. Functional Requirements

### 2.1 Skill CRUD

#### FR-052-01: Skill create, read, update, delete

```gherkin
Scenario: Create a skill definition
  GIVEN a user with admin or project_owner role
  WHEN they submit a POST to /api/v1/skills with:
      name = "Code Review"
      slug = "code-review"
      description = "Reviews code for security, quality, and style compliance"
      tier = "workspace"
      visibility = "public"
      content = "<SKILL.md body content>"
  THEN a row is inserted into skill_definitions:
      id = <generated UUID>
      name = "Code Review"
      slug = "code-review"
      tier = "workspace"
      visibility = "public"
      version = 1
      created_at = <now>
  AND the frontmatter_tsv column is auto-populated by the GENERATED ALWAYS clause
  AND the skill is immediately available to agents in that workspace
```

```gherkin
Scenario: Prevent duplicate skill slugs
  GIVEN a skill with slug "code-review" already exists
  WHEN a user attempts to create another skill with slug "code-review"
  THEN the system returns HTTP 409 Conflict
  AND the error message includes: "Skill slug 'code-review' already exists"
```

```gherkin
Scenario: Update a skill definition
  GIVEN a skill "code-review" exists at version 1
  WHEN an admin updates the description field
  THEN version is incremented to 2
  AND updated_at is set to now()
  AND frontmatter_tsv is regenerated by the GENERATED column
```

```gherkin
Scenario: Delete a skill definition
  GIVEN a skill "code-review" exists
  AND it has 3 agent grants in skill_agent_grants
  WHEN an admin deletes the skill
  THEN the skill_definitions row is deleted
  AND all 3 skill_agent_grants rows are cascade-deleted
```

### 2.2 5-Tier Loading Priority

#### FR-052-02: Tier precedence resolution (workspace overrides global for same slug)

```gherkin
Scenario: Workspace tier overrides global tier for same slug
  GIVEN a skill with slug "code-review" exists at tier "global"
  AND a skill with slug "code-review" exists at tier "workspace"
  WHEN the loader resolves skills for an agent in that workspace
  THEN the workspace-tier skill is returned
  AND the global-tier skill is excluded from the result set
```

```gherkin
Scenario: Full 5-tier precedence order
  GIVEN skills with slug "deploy" exist at all 5 tiers:
      workspace, project_agent, personal_agent, global, builtin
  WHEN the loader resolves skills for agent "devops"
  THEN the workspace-tier "deploy" skill is used (highest priority)
  AND the tier precedence order is:
      1. workspace (highest)
      2. project_agent
      3. personal_agent
      4. global
      5. builtin (lowest)
```

```gherkin
Scenario: Lower tier fills gaps when higher tier has no override
  GIVEN a "deploy" skill exists only at tier "global"
  AND a "test" skill exists only at tier "builtin"
  WHEN the loader resolves all skills for an agent
  THEN both "deploy" (global) and "test" (builtin) are included
  AND no override conflict occurs — different slugs coexist across tiers
```

**Tier hierarchy** (higher number overrides lower):

| Tier | Priority | Scope | Override behavior |
|------|----------|-------|-------------------|
| workspace | 1 (highest) | Workspace-wide | Overrides all lower tiers for same slug |
| project_agent | 2 | Agent within project | Overrides personal_agent and below |
| personal_agent | 3 | Single agent | Overrides global and builtin |
| global | 4 | All workspaces | Overrides builtin |
| builtin | 5 (lowest) | System-wide, immutable | Always available as fallback |

### 2.3 BuildSummary XML Generation

#### FR-052-03: BuildSummary generates `<available_skills>` XML for system prompt

```gherkin
Scenario: Generate available_skills XML for agent with 4 skills
  GIVEN agent "coder" has 4 accessible skills after tier resolution:
      code-review (workspace), test-writer (global), deploy (global), lint (builtin)
  WHEN BuildSummary(agent_id) is called
  THEN the output is an XML block:
      "<available_skills>\n"
      "  <skill slug=\"code-review\" tier=\"workspace\">\n"
      "    <description>Reviews code for security and quality</description>\n"
      "  </skill>\n"
      "  <skill slug=\"test-writer\" tier=\"global\">\n"
      "    <description>Generates unit and integration tests</description>\n"
      "  </skill>\n"
      "  <skill slug=\"deploy\" tier=\"global\">\n"
      "    <description>Manages deployment pipelines</description>\n"
      "  </skill>\n"
      "  <skill slug=\"lint\" tier=\"builtin\">\n"
      "    <description>Runs linting and formatting checks</description>\n"
      "  </skill>\n"
      "</available_skills>"
  AND the total token count is <= 1500 tokens
```

```gherkin
Scenario: BuildSummary truncates at token budget
  GIVEN agent "lead" has 50 accessible skills
  WHEN BuildSummary(agent_id) is called
  THEN skills are included in tier-priority order until 1500 token budget is reached
  AND a closing comment is appended:
      "<!-- 23 more skills available. Use /skills search <query> to discover. -->"
```

```gherkin
Scenario: BuildSummary for agent with 0 skills
  GIVEN agent "standalone" has no accessible skills
  WHEN BuildSummary(agent_id) is called
  THEN the output is:
      "<available_skills>\n"
      "  <!-- No skills configured for this agent -->\n"
      "</available_skills>"
```

```gherkin
Scenario: Parse SKILL.md frontmatter
  GIVEN a SKILL.md file with content:
      "---\n"
      "name: Code Review\n"
      "slug: code-review\n"
      "description: Reviews code for security and quality\n"
      "tier: workspace\n"
      "visibility: public\n"
      "---\n"
      "## Instructions\n"
      "Review the code for OWASP Top 10 violations...\n"
  WHEN the parser processes this file
  THEN frontmatter fields are extracted via simple key:value split (no YAML library):
      name = "Code Review", slug = "code-review", tier = "workspace"
  AND the body content (after second ---) is stored in content column
```

### 2.4 Per-Agent Grants

#### FR-052-04: Skill grants and ListAccessible (combines grants + visibility)

```gherkin
Scenario: Grant a skill to a specific agent
  GIVEN skill "deploy" exists with visibility "private"
  AND agent "devops" exists in agent_definitions
  WHEN an admin creates a grant in skill_agent_grants:
      skill_id = <deploy.id>
      agent_definition_id = <devops.id>
  THEN "devops" can access the "deploy" skill via ListAccessible
  AND other agents without a grant cannot access "deploy"
```

```gherkin
Scenario: ListAccessible combines grants and visibility
  GIVEN the following skills exist:
      "lint" (visibility: public, tier: builtin)
      "deploy" (visibility: private, tier: workspace, granted to "devops")
      "security-scan" (visibility: internal, tier: global)
      "secret-tool" (visibility: private, tier: workspace, NOT granted to "devops")
  WHEN ListAccessible is called for agent "devops"
  THEN the result includes:
      "lint" (public — visible to all agents)
      "deploy" (private — explicitly granted)
      "security-scan" (internal — visible to team members)
  AND the result excludes:
      "secret-tool" (private — no grant for "devops")
```

```gherkin
Scenario: Prevent duplicate grants
  GIVEN a grant already exists for skill "deploy" and agent "devops"
  WHEN an admin attempts to create the same grant
  THEN the system returns HTTP 409 Conflict
  AND the existing grant is unchanged
```

### 2.5 tsvector Search

#### FR-052-05: Database full-text search via ts_rank

```gherkin
Scenario: Search skills by keyword using tsvector
  GIVEN 10 skills exist in skill_definitions with varied names and descriptions
  AND skill "code-review" has name "Code Review" and description "Reviews code for security"
  WHEN a user searches with query "review security"
  THEN ts_rank(frontmatter_tsv, plainto_tsquery('simple', 'review security')) is computed
  AND results are ordered by ts_rank descending
  AND "code-review" appears in the top results
  AND results are filtered by agent accessibility (visibility + grants)
```

```gherkin
Scenario: Search with Vietnamese tokens
  GIVEN a skill with name "Kiểm tra mã nguồn" (Code Review in Vietnamese)
  WHEN a user searches with query "kiểm tra"
  THEN the 'simple' tokenizer splits on whitespace (no stemming)
  AND the skill matches because 'simple' tokenizer preserves Vietnamese tokens
  AND the result includes the Vietnamese-named skill
```

```gherkin
Scenario: Empty search returns all accessible skills
  GIVEN 5 skills are accessible to agent "coder"
  WHEN a search is performed with an empty query
  THEN all 5 accessible skills are returned ordered by name
```

### 2.6 Skill Visibility Rules

#### FR-052-06: Visibility enforcement (public, private, internal)

```gherkin
Scenario: Public skills are visible to all agents
  GIVEN skill "lint" has visibility "public"
  WHEN any agent queries accessible skills
  THEN "lint" appears in the result regardless of grants
```

```gherkin
Scenario: Private skills require explicit grant
  GIVEN skill "secret-deploy" has visibility "private"
  AND only agent "devops" has a grant for "secret-deploy"
  WHEN agent "coder" queries accessible skills
  THEN "secret-deploy" does NOT appear in the result
  WHEN agent "devops" queries accessible skills
  THEN "secret-deploy" appears in the result
```

```gherkin
Scenario: Internal skills visible to team members
  GIVEN skill "team-review" has visibility "internal"
  AND agents "coder" and "reviewer" are in team "backend-team"
  AND agent "external-consultant" is NOT in any team
  WHEN "coder" queries accessible skills
  THEN "team-review" appears in the result
  WHEN "external-consultant" queries accessible skills
  THEN "team-review" does NOT appear in the result
```

---

## 3. Non-Functional Requirements

| NFR | Target |
|-----|--------|
| Skill loading latency (100 skills) | < 50ms |
| BuildSummary token budget | <= 1500 tokens |
| BuildSummary generation latency | < 30ms |
| tsvector search latency | < 20ms |
| Tokenizer | `simple` (not `english`) — Vietnamese + code token support |
| SKILL.md frontmatter parse latency | < 5ms per file |
| Skill CRUD API latency (p95) | < 100ms |
| Grant query latency (per agent) | < 10ms (indexed FK) |
| Frontmatter parser dependency | No external YAML library (simple key:value split) |

---

## 4. Security Considerations

- **Authorization**: Only team admins and project owners can create/modify skill definitions
- **Visibility enforcement**: Private skills require explicit grant — enforced at query level, not UI level
- **Content sanitization**: SKILL.md content is sanitized before storage (XSS prevention)
- **SQL injection prevention**: tsvector queries use parameterized `plainto_tsquery()`, never string concatenation
- **Audit trail**: All skill CRUD and grant changes logged to audit_logs table
- **No PII in skills**: Skill definitions contain capability descriptions only, no user PII
- **Cascade deletion**: Deleting a skill cascades to all grants (no orphan grants)
- **Tier immutability**: Builtin tier skills cannot be modified by non-system users

---

## 5. Data Model

### 5.1 skill_definitions table

| Column | Type | Constraints |
|--------|------|-------------|
| id | UUID | PK, default gen_random_uuid() |
| name | VARCHAR(100) | NOT NULL |
| slug | VARCHAR(100) | NOT NULL, UNIQUE |
| description | TEXT | NULLABLE |
| frontmatter | TEXT | NULLABLE |
| content | TEXT | NULLABLE |
| tier | VARCHAR(20) | NOT NULL, default 'workspace', CHECK IN ('workspace', 'project_agent', 'personal_agent', 'global', 'builtin') |
| visibility | VARCHAR(20) | NOT NULL, default 'public', CHECK IN ('public', 'private', 'internal') |
| version | INTEGER | NOT NULL, default 1 |
| workspace_path | VARCHAR(500) | NULLABLE |
| frontmatter_tsv | tsvector | GENERATED ALWAYS AS (to_tsvector('simple', COALESCE(name, '') \|\| ' ' \|\| COALESCE(description, ''))) STORED |
| created_at | TIMESTAMPTZ | NOT NULL, default now() |
| updated_at | TIMESTAMPTZ | NOT NULL, default now() |

**Unique constraint**: (slug)
**Indexes**: `idx_skill_definitions_tsv` GIN(frontmatter_tsv), `idx_skill_definitions_slug` UNIQUE(slug), `idx_skill_definitions_tier` (tier)

### 5.2 skill_agent_grants table

| Column | Type | Constraints |
|--------|------|-------------|
| id | UUID | PK, default gen_random_uuid() |
| skill_id | UUID | FK skill_definitions(id) ON DELETE CASCADE, NOT NULL |
| agent_definition_id | UUID | FK agent_definitions(id) ON DELETE CASCADE, NOT NULL |
| granted_at | TIMESTAMPTZ | NOT NULL, default now() |

**Unique constraint**: (skill_id, agent_definition_id)
**Indexes**: skill_id, agent_definition_id

---

## 6. Acceptance Criteria (Sprint 217-218 DoD)

### Sprint 217 (P2a) — Model + Loader + BuildSummary

- [ ] `skill_definitions` table created via Alembic migration with tsvector GENERATED column
- [ ] GIN index on `frontmatter_tsv` column for full-text search performance
- [ ] `skill_definitions` SQLAlchemy model follows `backend/app/models/vcr.py` pattern
- [ ] SKILL.md frontmatter parser extracts name, slug, description, tier, visibility via simple key:value split
- [ ] 5-tier loader resolves precedence: workspace > project_agent > personal_agent > global > builtin
- [ ] Higher tier overrides lower tier for same slug (deduplication by slug)
- [ ] `build_summary_xml(agent_id)` returns `<available_skills>` XML block
- [ ] BuildSummary respects 1500 token budget with truncation comment
- [ ] BuildSummary returns empty-comment XML when agent has 0 skills
- [ ] Skill CRUD endpoints: POST, GET, PUT, DELETE `/api/v1/skills`
- [ ] Duplicate slug returns HTTP 409 Conflict
- [ ] Version auto-incremented on update

### Sprint 218 (P2b) — Search + Grants

- [ ] `skill_agent_grants` table created via Alembic migration
- [ ] Grant CRUD endpoints: POST, DELETE `/api/v1/skills/{id}/grants`
- [ ] Duplicate grant returns HTTP 409 Conflict
- [ ] `list_accessible(agent_id)` combines grants + visibility rules correctly
- [ ] Public skills visible to all, private requires grant, internal requires team membership
- [ ] tsvector search via `ts_rank(frontmatter_tsv, plainto_tsquery('simple', query))`
- [ ] Search endpoint: GET `/api/v1/skills/search?q=<query>`
- [ ] Vietnamese token search works with `simple` tokenizer
- [ ] Empty search query returns all accessible skills ordered by name
- [ ] Unit tests: >= 18 test cases covering all BDD scenarios
- [ ] Zero import breakage in existing agent_team services
