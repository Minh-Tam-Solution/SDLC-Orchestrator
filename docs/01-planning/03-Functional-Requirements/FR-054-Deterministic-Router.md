---
sdlc_version: "6.1.1"
document_type: "Functional Requirement"
status: "APPROVED"
sprint: "219"
spec_id: "FR-054"
tier: "PROFESSIONAL"
stage: "01 - Planning"
references: ["ADR-056", "ADR-058"]
---

# FR-054: Deterministic Router

**Version**: 2.0.0
**Status**: APPROVED
**Created**: March 2026
**Sprint**: 219
**Framework**: SDLC 6.1.1
**Epic**: EP-07 Multi-Agent Team Engine — MTClaw Restructure
**ADR**: ADR-056 (LD#1 Snapshot Precedence), ADR-058 (ZeroClaw Best Practices)
**Owner**: Backend Team
**Pattern Source**: MTClaw Router = config binding, not intelligence (0ms LLM latency at gateway)

---

## 1. Overview

### 1.1 Purpose

Implement a 4-level deterministic routing engine that directs incoming messages to the correct agent with 0ms LLM latency at the gateway layer. Routing decisions are based on @mentions, team mappings, active handoffs, and tsvector matching — never on LLM inference. This requires a 4-phase Alembic migration to add `frontmatter` and `frontmatter_tsv` columns to the existing `agent_definitions` table (~50+ rows), enabling text-based agent matching for Level 4 fallback routing.

### 1.2 Problem Being Solved

| Before FR-054 | After FR-054 |
|--------------|-------------|
| No structured message routing — all messages go to a single default agent | 4-level deterministic routing with explicit precedence |
| Routing requires LLM inference (slow, non-deterministic, costly) | 0ms LLM latency — all routing is config-based or tsvector-based |
| @mention syntax exists but has no routing backend | Level 1: @agent mention routes directly to named agent |
| Team messages have no lead routing | Level 2: @team mention routes to team's lead agent |
| No fallback when explicit mention is absent | Level 4: tsvector match against agent frontmatter with score threshold |
| No routing audit trail for debugging | Routing evidence logged for every decision (level, candidates, scores) |
| MAX_COMMANDS=10 at capacity | Router is additive (works alongside commands, not replacement) |

### 1.3 Business Value

- **Performance**: 0ms LLM latency at gateway — routing is deterministic, not inference-based
- **Debuggability**: Every routing decision logged with level, candidates, scores, and matched terms
- **Predictability**: Same message always routes to same agent (no LLM non-determinism)
- **Backward compatibility**: All 10 existing commands preserved (MAX_COMMANDS=10)
- **Scalability**: Database-level tsvector search scales to 1000+ agents without LLM cost increase

### 1.4 Scope Boundary

| In scope | Out of scope |
|----------|-------------|
| Level 1: @agent mention -> direct route (Sprint 219) | LLM-based semantic routing (never — deterministic only) |
| Level 2: @team mention -> team lead route (Sprint 219) | Cross-team routing (future) |
| Level 4: tsvector match -> best-scoring agent (Sprint 219) | Level 3: Active handoff per-conversation override (deferred to future sprint) |
| 4-phase Alembic migration for agent_definitions (Sprint 219) | UI for editing agent frontmatter (future) |
| Routing evidence log for debugging (Sprint 219) | Routing analytics dashboard (future) |
| All 10 existing commands preserved (Sprint 219) | Dynamic command registration beyond MAX_COMMANDS=10 (Sprint 203+) |

### 1.5 CTO Corrections Applied

| Correction | Detail |
|-----------|--------|
| CTO Correction 3 | 4-phase migration for existing ~50+ agent_definitions rows. Backfill frontmatter from existing data (batch 100, truncate 500 chars). |
| Consolidated R1b | Routing evidence log records route_level, top_candidates[], score, matched_terms for debugging. |

---

## 2. Functional Requirements

### 2.1 Level 1 — @agent Mention Routing

#### FR-054-01: @mention routes to named agent

```gherkin
Scenario: Direct @agent mention routes to named agent
  GIVEN agent "coder" exists in agent_definitions with agent_name = "coder"
  AND a message is received: "@coder please review this function"
  WHEN the deterministic router processes the message
  THEN Level 1 matches: @mention "coder" resolves to agent_definitions.agent_name = "coder"
  AND the message is routed directly to agent "coder"
  AND route_level = 1 is recorded in the routing evidence log
  AND latency < 5ms (no DB query needed — name lookup in memory cache)
```

```gherkin
Scenario: @mention with unknown agent name falls through
  GIVEN no agent exists with agent_name = "unknown-agent"
  AND a message is received: "@unknown-agent help me"
  WHEN the deterministic router processes the message at Level 1
  THEN Level 1 does not match (agent name not found)
  AND routing falls through to Level 2
```

```gherkin
Scenario: @mention is case-insensitive
  GIVEN agent "Coder" exists in agent_definitions with agent_name = "coder"
  AND a message is received: "@CODER please review"
  WHEN the deterministic router processes the message at Level 1
  THEN Level 1 matches: "CODER" is lowercased to "coder" and resolves
  AND the message is routed to agent "coder"
```

### 2.2 Level 2 — @team Mention Routing

#### FR-054-02: @team routes to team lead

```gherkin
Scenario: @team mention routes to team's lead agent
  GIVEN team "backend-team" exists with lead_agent_definition_id = <lead-agent.id>
  AND agent "lead-agent" exists in agent_definitions
  AND a message is received: "@backend-team we need a deployment plan"
  WHEN the deterministic router processes the message
  THEN Level 2 matches: @team "backend-team" resolves to team lead "lead-agent"
  AND the message is routed to agent "lead-agent"
  AND route_level = 2 is recorded in the routing evidence log
```

```gherkin
Scenario: @team with no lead agent configured
  GIVEN team "frontend-team" exists but lead_agent_definition_id = NULL
  AND a message is received: "@frontend-team review the PR"
  WHEN the deterministic router processes the message at Level 2
  THEN Level 2 does not match (no lead agent configured)
  AND routing falls through to Level 4
  AND a warning is logged: "Team 'frontend-team' has no lead agent configured"
```

```gherkin
Scenario: @team name does not exist
  GIVEN no team exists with name "nonexistent-team"
  AND a message is received: "@nonexistent-team help"
  WHEN the deterministic router processes the message at Level 2
  THEN Level 2 does not match (team not found)
  AND routing falls through to Level 4
```

### 2.3 Level 4 — tsvector Match Routing

#### FR-054-03: tsvector match routes to best-scoring agent

```gherkin
Scenario: tsvector match routes message to best-scoring agent
  GIVEN 5 agents exist with frontmatter in agent_definitions:
      "coder" — frontmatter: "Python FastAPI backend code generation"
      "reviewer" — frontmatter: "Code review security OWASP compliance"
      "tester" — frontmatter: "Unit testing pytest coverage integration"
      "devops" — frontmatter: "Deployment Kubernetes Docker CI/CD pipeline"
      "docs" — frontmatter: "Documentation API reference technical writing"
  AND a message is received: "Help me write pytest unit tests for the auth service"
  WHEN the deterministic router reaches Level 4
  THEN ts_rank(frontmatter_tsv, plainto_tsquery('simple', 'pytest unit tests auth')) is computed for all agents
  AND agent "tester" scores highest (matches "pytest", "testing", "unit")
  AND the message is routed to agent "tester"
  AND route_level = 4 is recorded in the routing evidence log
  AND matched_terms = ["pytest", "unit", "testing"] is recorded
```

```gherkin
Scenario: tsvector uses 'simple' tokenizer for Vietnamese support
  GIVEN agent "vn-coder" has frontmatter containing:
      "triggers: lap trinh, ma nguon, phat trien"
      "domain: phan mem, ung dung web"
  AND a message is received: "lap trinh ung dung web"
  WHEN the deterministic router processes the message at Level 4
  THEN 'simple' tokenizer preserves Vietnamese tokens without stemming
  AND "vn-coder" matches on "lap", "trinh", "ung", "dung", "web"
  AND the match is scored correctly
  NOTE: 'simple' tokenizer chosen specifically because 'english' tokenizer
        would stem Vietnamese words incorrectly
```

#### FR-054-04: Fallback when no match — return top-3 candidates with scores

```gherkin
Scenario: tsvector score below threshold — return top-3 candidates
  GIVEN 5 agents exist with frontmatter as above
  AND a message is received: "What is the weather today?"
  WHEN the deterministic router reaches Level 4
  THEN ts_rank scores are computed for all agents
  AND all scores are below the minimum threshold (0.01)
  AND the router returns the top-3 candidates with their scores:
      [{"agent": "coder", "score": 0.005}, {"agent": "docs", "score": 0.003}, {"agent": "reviewer", "score": 0.002}]
  AND the caller can present these as suggestions or use a default agent
  AND no LLM call is made (0ms LLM latency maintained)
```

```gherkin
Scenario: No tsvector match and no @mention — return top-3 candidates
  GIVEN a message "hello" contains no @mention and no meaningful keywords
  WHEN the deterministic router processes through all levels
  THEN Level 1 does not match (no @agent mention)
  AND Level 2 does not match (no @team mention)
  AND Level 4 computes tsvector scores but all are below threshold
  THEN the router returns a fallback response:
      route_level = 4
      matched = false
      top_candidates = [<top 3 agents by score>]
  AND no LLM call is made (0ms LLM latency maintained)
```

### 2.4 Routing Evidence Log

#### FR-054-05: Routing evidence logged for each decision

```gherkin
Scenario: Route evidence logged for Level 1 match
  GIVEN a message "@coder review this" is routed via Level 1
  WHEN routing completes
  THEN a routing evidence record is created:
      route_level = 1
      matched_agent = "coder"
      match_type = "mention"
      top_candidates = [{"agent": "coder", "score": 1.0}]
      matched_terms = ["@coder"]
      latency_ms = <actual>
      message_id = <message UUID>
  AND the record is stored in the agent_messages metadata JSONB
```

```gherkin
Scenario: Route evidence logged for Level 4 tsvector match
  GIVEN a message "write unit tests" is routed via Level 4
  WHEN routing completes
  THEN a routing evidence record is created:
      route_level = 4
      matched_agent = "tester"
      match_type = "tsvector"
      top_candidates = [
          {"agent": "tester", "score": 0.35},
          {"agent": "coder", "score": 0.12},
          {"agent": "reviewer", "score": 0.08}
      ]
      matched_terms = ["unit", "tests"]
      latency_ms = <actual>
  AND the evidence is available for debugging via GET /api/v1/agent-team/conversations/{id}/routing-log
```

```gherkin
Scenario: Route evidence logged for no-match fallback
  GIVEN a message "hello" produces no confident match at any level
  WHEN routing completes
  THEN a routing evidence record is created:
      route_level = 4
      matched_agent = null
      match_type = "fallback"
      top_candidates = [<top 3 agents by score>]
      matched_terms = []
      latency_ms = <actual>
```

### 2.5 Existing Command Preservation

#### FR-054-06: All 10 existing commands still work (MAX_COMMANDS=10 preserved)

```gherkin
Scenario: Router does not interfere with existing command handling
  GIVEN the command registry has 10 registered commands (MAX_COMMANDS=10)
  AND a message "/sprint close" is received
  WHEN the message is processed
  THEN the command router handles it BEFORE the deterministic router
  AND the deterministic router is NOT invoked for command messages
  AND all 10 existing commands function identically to pre-FR-054 behavior
```

```gherkin
Scenario: Non-command messages are routed by deterministic router
  GIVEN a message "Help me refactor the auth module" is received (no / prefix)
  WHEN the message is processed
  THEN the command router skips it (not a command)
  AND the deterministic router processes it through Level 1 -> 2 -> 4
  AND routing proceeds normally
```

```gherkin
Scenario: Router is additive to command registry
  GIVEN MAX_COMMANDS = 10 (current capacity reached)
  AND 10 existing commands are registered
  WHEN the deterministic router is added
  THEN command count remains 10 (router is NOT a registered command)
  AND the router operates as a pre-dispatch layer before command routing
  AND existing /commands work identically (no behavior change)
```

---

## 3. Non-Functional Requirements

| NFR | Target |
|-----|--------|
| Route decision latency (Level 1 — @mention) | < 5ms |
| Route decision latency (Level 2 — @team) | < 5ms |
| Route decision latency (Level 4 — tsvector) | < 20ms |
| LLM latency at gateway | 0ms (deterministic, no AI calls) |
| tsvector tokenizer | `simple` (not `english`) — Vietnamese + code token support |
| tsvector score threshold | 0.01 (below = no confident match) |
| Top-N fallback candidates | 3 (returned when no confident match) |
| Existing commands preserved | All 10 (MAX_COMMANDS=10, no breakage) |
| Agent frontmatter backfill | Batch 100, truncate 500 chars per agent |
| Backfill migration duration (~50 rows) | < 5 seconds |

---

## 4. Security Considerations

- **Input sanitization**: @mention and @team names are sanitized before DB lookup (parameterized queries prevent SQL injection)
- **No LLM injection**: Routing is deterministic — no user input is passed to LLM at the routing layer
- **tsvector query safety**: All tsvector queries use `plainto_tsquery()` (parameterized), never raw `to_tsquery` string concatenation
- **Routing evidence access control**: Routing logs are accessible only to conversation participants and admins
- **No privilege escalation**: Routing to an agent does NOT bypass delegation link checks (FR-051) — the spawn guard still applies
- **Evidence log sanitization**: User message text is NOT stored in routing evidence — only matched_terms and scores
- **Rate limiting**: Routing decisions are cached per conversation turn to prevent abuse
- **Audit trail**: All routing decisions logged with full evidence for compliance

---

## 5. Data Model

### 5.1 agent_definitions ALTER — 4-Phase Migration (CTO Correction 3)

**Phase 1**: ADD COLUMN frontmatter TEXT

| Column | Type | Constraints |
|--------|------|-------------|
| frontmatter | TEXT | NULLABLE (fast DDL — no table rewrite) |

**Phase 2**: Backfill existing ~50+ rows (batch 100, truncate 500 chars)

```sql
UPDATE agent_definitions
SET frontmatter = LEFT(
    COALESCE(agent_name, '') || ' ' || COALESCE(description, '') || ' ' || COALESCE(system_prompt, ''),
    500
)
WHERE frontmatter IS NULL;
```

**Phase 3**: ADD COLUMN frontmatter_tsv tsvector GENERATED

| Column | Type | Constraints |
|--------|------|-------------|
| frontmatter_tsv | tsvector | GENERATED ALWAYS AS (to_tsvector('simple', COALESCE(agent_name, '') \|\| ' ' \|\| COALESCE(frontmatter, ''))) STORED |

**Phase 4**: CREATE INDEX (GIN, CONCURRENTLY)

```sql
CREATE INDEX CONCURRENTLY idx_agent_def_frontmatter ON agent_definitions USING GIN(frontmatter_tsv);
```

**Migration safety**:
- Phase 1: Instant (nullable, no default)
- Phase 2: Batch 100 to avoid long locks
- Phase 3: Table rewrite (acceptable for ~50 rows)
- Phase 4: CONCURRENTLY does not block reads or writes

### 5.2 Routing Evidence (stored in agent_messages.metadata JSONB)

Routing evidence is stored in the `agent_messages.metadata` JSONB column, not in a separate table:

| Field | Type | Description |
|-------|------|-------------|
| route_level | INTEGER | 1, 2, or 4 (Level 3 deferred) |
| matched_agent | VARCHAR | Agent name that was matched (null if no match) |
| match_type | VARCHAR | "mention", "team", "tsvector", "fallback" |
| top_candidates | JSONB ARRAY | Top 3 candidates with scores |
| matched_terms | TEXT ARRAY | Terms that matched in tsvector query |
| latency_ms | FLOAT | Routing decision latency in milliseconds |
| score | FLOAT | Winning candidate's tsvector score (Level 4 only) |

**Example routing evidence in metadata**:

```json
{
  "routing": {
    "route_level": 4,
    "matched_agent": "tester",
    "match_type": "tsvector",
    "top_candidates": [
      {"agent": "tester", "score": 0.35, "matched_terms": ["unit", "tests"]},
      {"agent": "coder", "score": 0.12, "matched_terms": []},
      {"agent": "reviewer", "score": 0.08, "matched_terms": []}
    ],
    "latency_ms": 3.2
  }
}
```

No new tables created. Routing evidence piggybacks on existing `agent_messages.metadata` JSONB column.

---

## 6. Acceptance Criteria (Sprint 219 DoD)

- [ ] 4-phase Alembic migration: ADD frontmatter, backfill, ADD frontmatter_tsv GENERATED, ADD GIN index
- [ ] Phase 1: ADD COLUMN frontmatter TEXT is instant (nullable, no default)
- [ ] Phase 2: Backfill handles ~50+ existing agent_definitions rows (batch 100, truncate 500 chars)
- [ ] Phase 3: ADD frontmatter_tsv GENERATED ALWAYS AS (to_tsvector('simple', ...)) STORED
- [ ] Phase 4: CREATE INDEX CONCURRENTLY on frontmatter_tsv (GIN)
- [ ] Level 1: @agent mention resolves to agent_definitions.agent_name (case-insensitive)
- [ ] Level 1: Unknown @agent falls through to Level 2
- [ ] Level 2: @team mention resolves to team's lead_agent_definition_id
- [ ] Level 2: Team with no lead agent falls through to Level 4 with warning log
- [ ] Level 2: Nonexistent @team falls through to Level 4
- [ ] Level 4: tsvector match via `ts_rank(frontmatter_tsv, plainto_tsquery('simple', message))`
- [ ] Level 4: Score above threshold (0.01) routes to best-scoring agent
- [ ] Level 4: Score below threshold returns top-3 candidates with scores
- [ ] `simple` tokenizer used (not `english`) for Vietnamese + code token support
- [ ] Routing evidence logged for every decision (route_level, top_candidates, matched_terms, latency_ms)
- [ ] Routing evidence stored in agent_messages.metadata JSONB (not a separate table)
- [ ] Route decision latency: < 5ms (Level 1-2), < 20ms (Level 4)
- [ ] 0ms LLM latency maintained — no AI calls in routing path
- [ ] All 10 existing commands still work (MAX_COMMANDS=10 preserved)
- [ ] Command router runs BEFORE deterministic router (commands are not routed)
- [ ] `plainto_tsquery` used (not raw `to_tsquery`) to prevent tsquery injection
- [ ] Unit tests: >= 15 test cases covering all 3 active levels + fallback + evidence + backfill
- [ ] Zero import breakage in existing agent_team services
