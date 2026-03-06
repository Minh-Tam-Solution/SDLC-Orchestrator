---
sdlc_version: "6.1.1"
document_type: "Functional Requirement"
status: "APPROVED"
sprint: "215-216"
spec_id: "FR-051"
tier: "PROFESSIONAL"
stage: "01 - Planning"
references: ["ADR-056", "ADR-058"]
---

# FR-051: Delegation Links and Context Injection

**Version**: 1.0.0
**Status**: APPROVED
**Created**: March 2026
**Sprint**: 215-216
**Framework**: SDLC 6.1.1
**Epic**: EP-07 Multi-Agent Team Engine — MTClaw Restructure
**ADR**: ADR-056 (LD#1 Snapshot Precedence), ADR-058 (ZeroClaw Best Practices)
**Owner**: Backend Team
**Pattern Source**: MTClaw `DELEGATION.md` / `TEAM.md` / `AVAILABILITY.md` context injection

---

## 1. Overview

### 1.1 Purpose

Persist explicit delegation relationships between agent definitions and dynamically inject contextual markdown sections (DELEGATION.md, TEAM.md, AVAILABILITY.md) into every LLM call. This replaces implicit "any agent can spawn any agent" with a permission-checked delegation graph, and ensures agents have accurate awareness of their collaborators.

### 1.2 Problem Being Solved

| Before FR-051 | After FR-051 |
|--------------|-------------|
| Any agent can `@mention` or spawn any other agent | Spawn tool checks `delegation_links` — unauthorized targets rejected |
| Agents hallucinate collaborator names/capabilities | DELEGATION.md provides <=15 real targets with descriptions |
| Team leads and members see identical system prompts | TEAM.md differentiates lead vs member content |
| No negative context when agent has zero targets | AVAILABILITY.md prevents hallucinated tool calls to non-existent peers |
| Team presets create agents but no persistent links | `apply_preset()` persists delegation_chain to `delegation_links` table |

### 1.3 Business Value

- **Security**: Prevents unauthorized agent-to-agent delegation (non-negotiable #3, ADR-056)
- **Token efficiency**: Context injection is cache-friendly and bounded (<=3700 tokens total)
- **Accuracy**: Eliminates agent hallucination of team members by providing ground truth

### 1.4 Scope Boundary

| In scope | Out of scope |
|----------|-------------|
| `delegation_links` table (Sprint 216) | Delegation approval workflow (future) |
| Context injector service (Sprint 216) | LLM-based routing via context (see FR-054) |
| Spawn tool guard (Sprint 216) | Cross-team delegation (future) |
| Team lead FK on teams table (Sprint 216) | OTT channel delegation UI (future) |
| Preset persistence to delegation_links (Sprint 216) | Delegation analytics/metrics (future) |

---

## 2. Functional Requirements

### 2.1 Delegation Links Persistence

#### FR-051-01: Create delegation link

```gherkin
Scenario: Create a delegation link between two agents
  GIVEN agent "architect" (source) exists in agent_definitions
  AND agent "coder" (target) exists in agent_definitions
  AND both agents belong to the same team
  WHEN an admin creates a delegation link with link_type "can_delegate"
  THEN a row is inserted into delegation_links:
      source_agent_id = <architect.id>
      target_agent_id = <coder.id>
      link_type = "can_delegate"
      is_active = true
      created_at = <now>
  AND the link is immediately available for context injection
```

```gherkin
Scenario: Prevent duplicate delegation links
  GIVEN a delegation link already exists from "architect" to "coder" with link_type "can_delegate"
  WHEN an admin attempts to create the same link again
  THEN the system returns HTTP 409 Conflict
  AND the existing link is unchanged
```

```gherkin
Scenario: Deactivate a delegation link
  GIVEN an active delegation link from "architect" to "coder"
  WHEN an admin sets is_active = false
  THEN the link row is updated (not deleted) with is_active = false
  AND the target no longer appears in DELEGATION.md for "architect"
  AND the spawn tool rejects "architect" delegating to "coder"
```

#### FR-051-02: Spawn tool delegation guard

```gherkin
Scenario: Spawn tool allows delegation to linked target
  GIVEN agent "architect" has an active delegation link to agent "coder"
  WHEN "architect" invokes the spawn tool targeting "coder"
  THEN the spawn proceeds normally
  AND a new child conversation is created per ADR-056 LD#1
```

```gherkin
Scenario: Spawn tool rejects delegation to unlinked target
  GIVEN agent "architect" has NO active delegation link to agent "reviewer"
  WHEN "architect" invokes the spawn tool targeting "reviewer"
  THEN the spawn is rejected with error:
      "Delegation denied: 'architect' is not authorized to delegate to 'reviewer'. "
      "Available targets: coder, tester. Use @search to find other agents."
  AND the rejection is logged to agent_messages with role = "system"
```

```gherkin
Scenario: Spawn tool with empty delegation targets
  GIVEN agent "standalone" has NO active delegation links
  WHEN "standalone" invokes the spawn tool targeting any agent
  THEN the spawn is rejected with error:
      "Delegation denied: 'standalone' has no delegation targets configured. "
      "Contact your team admin to set up delegation links."
```

### 2.2 Context Injection

#### FR-051-03: DELEGATION.md generation

```gherkin
Scenario: Build DELEGATION.md with <=15 targets
  GIVEN agent "architect" has 5 active delegation targets
  WHEN the context injector builds DELEGATION.md for "architect"
  THEN the output contains a markdown section:
      "## Available Delegation Targets\n\n"
      "You can delegate work to these agents using @mention:\n\n"
      "- **coder**: Generates production-ready Python/TypeScript code\n"
      "- **reviewer**: Reviews code for security and quality\n"
      "- **tester**: Writes and runs unit/integration tests\n"
      "- **devops**: Manages deployment and infrastructure\n"
      "- **docs**: Generates documentation from code\n"
  AND the token count is <= 2000 tokens
```

```gherkin
Scenario: Build DELEGATION.md with >15 targets
  GIVEN agent "lead" has 20 active delegation targets
  WHEN the context injector builds DELEGATION.md for "lead"
  THEN the output lists the first 15 targets by name + description
  AND appends: "\n\n> You have 5 more targets not shown. Use `@search <query>` to find specific agents.\n"
  AND the token count is <= 2000 tokens
```

#### FR-051-04: TEAM.md generation

```gherkin
Scenario: Build TEAM.md for team lead
  GIVEN agent "lead-agent" is the team lead (teams.lead_agent_definition_id == lead-agent.id)
  AND the team has 4 members: coder, reviewer, tester, devops
  WHEN the context injector builds TEAM.md for "lead-agent"
  THEN the output contains:
      "## Team Context (Lead)\n\n"
      "You are the **lead** of team 'backend-team'.\n"
      "You coordinate work across team members and can delegate tasks.\n\n"
      "### Team Members\n"
      "- **coder**: Code generation specialist\n"
      "- **reviewer**: Code review and security\n"
      "- **tester**: Test authoring and execution\n"
      "- **devops**: Deployment and infrastructure\n"
  AND the token count is <= 1500 tokens
```

```gherkin
Scenario: Build TEAM.md for team member
  GIVEN agent "coder" is a member (NOT lead) of team "backend-team"
  AND "lead-agent" is the team lead
  WHEN the context injector builds TEAM.md for "coder"
  THEN the output contains:
      "## Team Context (Member)\n\n"
      "You are a member of team 'backend-team'.\n"
      "Your team lead is **lead-agent**. Escalate blockers to them.\n\n"
      "### Your Role\n"
      "Focus on your assigned tasks. Use @lead-agent for coordination.\n"
  AND the token count is <= 1500 tokens
```

#### FR-051-05: AVAILABILITY.md generation

```gherkin
Scenario: Build AVAILABILITY.md for agent with no targets
  GIVEN agent "standalone" has 0 active delegation links
  AND agent "standalone" is not part of any team
  WHEN the context injector builds AVAILABILITY.md for "standalone"
  THEN the output contains:
      "## Availability Notice\n\n"
      "You have **no delegation targets** configured.\n"
      "Do NOT attempt to use @mention or spawn tools — they will fail.\n"
      "Complete your task independently using your own tools.\n"
  AND the token count is <= 200 tokens
```

```gherkin
Scenario: AVAILABILITY.md is empty when agent has targets
  GIVEN agent "architect" has 3 active delegation links
  WHEN the context injector builds AVAILABILITY.md for "architect"
  THEN the output is an empty string (no AVAILABILITY section injected)
  AND zero tokens are consumed
```

#### FR-051-06: Context injection into LLM call

```gherkin
Scenario: Inject all context sections before LLM call
  GIVEN agent "architect" has 3 delegation targets and is team lead
  WHEN the system prepares the system prompt for an LLM call
  THEN the context injector appends (in order):
      1. TEAM.md content (lead variant)
      2. DELEGATION.md content (3 targets listed)
      3. AVAILABILITY.md content (empty — agent has targets)
  AND the total injected tokens <= 3700 (2000 + 1500 + 200 budget)
  AND the injected content is placed AFTER the base system prompt
```

### 2.3 Caching

#### FR-051-07: Context cache invalidation

```gherkin
Scenario: Cache key includes delegation freshness
  GIVEN agent "architect" in team "backend-team"
  AND the most recent delegation_links.updated_at for this agent is "2026-03-04T10:00:00Z"
  WHEN the context injector computes the cache key
  THEN the key is: "ctx:{agent_id}:{team_id}:2026-03-04T10:00:00Z"
  AND cache TTL is 300 seconds (5 minutes)
```

```gherkin
Scenario: Cache invalidated on delegation link change
  GIVEN cached context exists for agent "architect" with delegation timestamp T1
  WHEN a new delegation link is added to "architect" at timestamp T2 > T1
  THEN the next LLM call computes a new cache key with T2
  AND the old cache entry expires naturally (no explicit invalidation needed)
```

### 2.4 Team Lead and Preset Persistence

#### FR-051-08: Team lead designation

```gherkin
Scenario: Set team lead via FK
  GIVEN team "backend-team" exists
  AND agent "lead-agent" is a member of the team
  WHEN admin sets teams.lead_agent_definition_id = lead-agent.id
  THEN TEAM.md generation uses lead variant for "lead-agent"
  AND TEAM.md generation uses member variant for all other agents in the team
```

#### FR-051-09: Preset persistence to delegation links

```gherkin
Scenario: Team preset creates delegation links
  GIVEN a team preset "backend-standard" defines delegation_chain:
      architect -> [coder, reviewer, tester]
      coder -> [tester]
      reviewer -> []
  WHEN apply_preset("backend-standard") is called for team "backend-team"
  THEN 4 delegation_links rows are created:
      architect -> coder (can_delegate, active)
      architect -> reviewer (can_delegate, active)
      architect -> tester (can_delegate, active)
      coder -> tester (can_delegate, active)
  AND existing links NOT in the preset are deactivated (is_active = false)
```

---

## 3. Non-Functional Requirements

| NFR | Target |
|-----|--------|
| DELEGATION.md token budget | <= 2000 tokens |
| TEAM.md token budget | <= 1500 tokens |
| AVAILABILITY.md token budget | <= 200 tokens |
| Context injection latency (cache hit) | < 5ms |
| Context injection latency (cache miss) | < 50ms |
| Cache TTL | 300 seconds |
| Cache key format | `ctx:{agent_id}:{team_id}:{max_updated_at}` |
| Delegation link query latency | < 10ms (indexed FK) |

---

## 4. Security Considerations

- **Authorization**: Only team admins and project owners can create/modify delegation links
- **Spawn guard enforcement**: Delegation check runs BEFORE conversation creation (fail-fast)
- **No PII in context**: DELEGATION.md contains agent names and descriptions only (no user PII)
- **Audit trail**: All delegation link changes logged to audit_logs table
- **Deactivation over deletion**: Links are deactivated (is_active = false), never hard-deleted, for audit compliance

---

## 5. Data Model

### 5.1 delegation_links table

| Column | Type | Constraints |
|--------|------|-------------|
| id | UUID | PK, default gen_random_uuid() |
| source_agent_id | UUID | FK agent_definitions(id) ON DELETE CASCADE, NOT NULL |
| target_agent_id | UUID | FK agent_definitions(id) ON DELETE CASCADE, NOT NULL |
| link_type | VARCHAR(50) | NOT NULL, default 'can_delegate' |
| is_active | BOOLEAN | NOT NULL, default true |
| created_at | TIMESTAMPTZ | NOT NULL, default now() |
| updated_at | TIMESTAMPTZ | NOT NULL, default now() |

**Unique constraint**: (source_agent_id, target_agent_id, link_type)
**Indexes**: source_agent_id, target_agent_id, (source_agent_id, is_active)

### 5.2 teams table ALTER

| Column | Type | Constraints |
|--------|------|-------------|
| lead_agent_definition_id | UUID | FK agent_definitions(id) ON DELETE SET NULL, NULLABLE |

---

## 6. Acceptance Criteria (Sprint 215-216 DoD)

- [ ] `delegation_links` table created via Alembic migration
- [ ] `teams.lead_agent_definition_id` FK added via Alembic migration
- [ ] `delegation_service.py` CRUD operations (create, deactivate, list_targets, list_sources)
- [ ] Spawn tool guard checks `delegation_links` before creating child conversation
- [ ] Spawn rejection returns actionable error with available target names
- [ ] `build_delegation_md(agent_id)` returns <= 2000 tokens, lists <= 15 targets
- [ ] `build_delegation_md(agent_id)` with >15 targets appends search instruction
- [ ] `build_team_md(agent_id, team_id)` returns lead vs member variant correctly
- [ ] `build_availability_md(agent_id)` returns negative context when 0 targets
- [ ] `build_availability_md(agent_id)` returns empty string when targets exist
- [ ] `inject_context(agent_id, team_id)` appends TEAM + DELEGATION + AVAILABILITY to system prompt
- [ ] Cache key includes `max(delegation_links.updated_at)` for automatic invalidation
- [ ] `apply_preset()` persists delegation_chain to `delegation_links` table
- [ ] Preset application deactivates links not in the new preset
- [ ] Unit tests: >= 15 test cases covering all BDD scenarios
- [ ] Zero import breakage in existing agent_team services
