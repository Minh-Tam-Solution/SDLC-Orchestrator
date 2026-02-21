---
sdlc_version: "6.1.0"
document_type: "ADR"
status: "ACCEPTED"
sprint: "179"
spec_id: "ADR-058"
tier: "PROFESSIONAL"
stage: "02 - Design"
---

# ADR-058: ZeroClaw Best Practice Adoption — Security + Architecture Hardening

**Status**: ACCEPTED — CTO Approved February 19, 2026
**Date**: February 2026
**Author**: CTO Nguyen Quoc Huy (decision) / PM (documentation)
**Sprint**: Sprint 179 — ZeroClaw Hardening
**Framework**: SDLC 6.1.0 (7-Pillar + Section 7 Quality Assurance)
**Supersedes**: None (extends ADR-056)
**References**: ADR-056 (Multi-Agent Team Engine), ZeroClaw `zeroclaw-labs/zeroclaw` (12.5K stars, Rust, MIT)
**Review History**: Researcher ZeroClaw Analysis → CTO Review (Feb 19, 2026) → Architect Review COMPLETE (Feb 19, 2026) → **CTO Sign-off ACCEPTED (Feb 19, 2026)**

> **Architect Review (Feb 19, 2026)**: APPROVE WITH REVISIONS. All 4 decisions technically feasible against current codebase. P1 findings F-1 + F-3 addressed in §2.1 and §2.3. P2 findings F-2, F-4, F-6 addressed in §2.2, §2.3, §2.4. P3 findings F-5, F-7 addressed in §2.3 and §2.4. Structural gaps S-1 (Options Considered) + S-2 (Testability) added per AGENTS.md template.

---

## 1. Context

### 1.1 Problem Statement

ADR-056 absorbed 24 patterns from OpenClaw (11), TinyClaw (7), and Nanobot (6). Research identified 7 additional patterns from ZeroClaw that fill security and architecture gaps:

| Gap | Current State | ZeroClaw Pattern |
|-----|--------------|-----------------|
| Tool output contains secrets | No scrubbing post-invocation | `scrub_credentials()` in agent loop |
| Shell inherits host env | ShellGuard blocks commands, not env | `env_clear()` + safe allowlist |
| Conversations hard-stop at 50 msgs | No summarization, conversation dies | Auto-summarize at threshold |
| Static model routing | Role → model is fixed | Query classification for dynamic routing |
| No tool dispatch | Text-only invocation | Dual-mode tool dispatch (DEFERRED → ADR-057) |
| No interactive approval | Static allow/deny lists | Session allowlist (DEFERRED → blocked by ADR-057) |
| No OTT streaming | Batch responses only | Channel draft/streaming (DEFERRED → Sprint 180+) |

### 1.2 CTO Decision Scope

5 of 7 patterns APPROVED for Sprint 179-180. 2 patterns DEFERRED:
- Pattern D (Dual-Mode Tool Dispatch) → DEFERRED, needs ADR-057, effort underestimated (10-12 days)
- Pattern G (Approval Flow) → DEFERRED, blocked by Pattern D

---

## 2. Decisions

### Decision 1: Output Credential Scrubbing (Pattern A) — LOCKED

#### 2.1.1 Options Considered

| Option | Approach | Pros | Cons | Decision |
|--------|----------|------|------|----------|
| **A: Regex scrubbing** (Selected) | 6 regex patterns, preserve first 4 chars + `****[REDACTED]` | Simple, <1ms, auditable, no dependencies, ZeroClaw-proven | False positives on harmless text containing "token" | **SELECTED** |
| B: AST-based secret detection | Parse structured output (JSON/YAML) to find secrets by key name | More precise, fewer false positives | Agent output is freeform text — AST parsing unreliable on prose | Rejected |
| C: Vault-based reference replacement | Store secrets in HashiCorp Vault, replace values with `{{secret:name}}` references | Zero false positives, full secret lifecycle | Requires Vault integration; fundamentally changes secret usage — Sprint 180+ concern | Rejected |

**Rationale for A**: Agent tool output is freeform text, making AST parsing unreliable. Vault integration is a Sprint 180+ concern. Regex scrubbing is the ZeroClaw-proven pattern, implementable in 50 LOC with ~1ms overhead.

#### 2.1.2 Decision

Scrub credentials from agent tool output at TWO integration points with defined trust boundaries (not double-scrubbing — see below).

**Rationale**: `InputSanitizer` protects inbound content. No equivalent exists for outbound tool results fed back to the LLM. Agent runs `env` → secrets stored in `agent_messages` and echoed in LLM context (CWE-200, T11 in STM-056).

**Implementation**:
- New file: `output_scrubber.py` (~50 LOC)
- 6 credential regex patterns: `token`, `api_key`/`apikey`, `password`/`passwd`, `secret`, `bearer`, `credential`
- Redaction format: preserve first 4 chars + `****[REDACTED]`
- Integration point 1: `AgentInvoker.invoke()` — scrub `InvocationResult.content` at line 253 (between TRACE log and return)
- Integration point 2: `EvidenceCollector.capture_message()` — scrub BEFORE computing SHA256 hash (before line 124)
- Enforced order: **scrub → hash → store** (never hash unscrubbed content)

**Trust Boundary Clarification (F-1)**: Points 1 and 2 are NOT double-scrubbing the same content path. They cover different message origins:
- **Point 1** (invoker): scrubs agent-generated tool output from the provider call chain — covers the primary path
- **Point 2** (evidence collector): scrubs ALL messages before hashing — covers messages from OTT gateway, manual API injection, or any non-invoker path that bypasses the invoker entirely
- **Scrubbing is idempotent**: applying `OutputScrubber.scrub()` twice to already-scrubbed content produces identical output. The `****[REDACTED]` suffix does not match any of the 6 credential patterns, so double-scrubbing is safe and produces no additional changes.

**Consequences**:
- CWE-200 mitigated for agent tool output (T11 in STM-056)
- Latency: ~1ms per regex pass — negligible
- False positives possible on text containing "token" or "password" as data — acceptable tradeoff for security

**FR**: FR-042

#### 2.1.3 Testability

**How will we verify this decision is correct?**

| Verification | Method | Test IDs |
|-------------|--------|----------|
| Each of 6 patterns detected and redacted | Unit test per pattern | CS-01 to CS-07 |
| Short value handling (< 4 chars) | Unit: preserve all chars + suffix | CS-08 |
| Invoker integration fires | Unit: verify scrub before return | CS-09 |
| Evidence integration fires in correct order | Unit: scrub → hash → store sequence | CS-10 |
| No raw secrets in `agent_messages` DB | Integration: send `API_KEY=secret123`, query DB | MA-06 extension |
| Scrubber itself has no secret leak | Semgrep scan on `output_scrubber.py` | CI/CD gate |

---

### Decision 2: Environment Variable Scrubbing (Pattern C) — LOCKED

#### 2.2.1 Options Considered

| Option | Approach | Pros | Cons | Decision |
|--------|----------|------|------|----------|
| **A: Allowlist approach** (Selected) | Clear env entirely, inject only 9 safe vars | Zero leakage by default; extending allowlist is explicit and auditable | Some tools may need additional vars added to allowlist | **SELECTED** |
| B: Denylist approach | Remove known-secret vars (OPENAI_API_KEY, DATABASE_URL, etc.) | Less likely to break tools | Miss-by-name: new or custom secrets not on denylist leak through — fragile security pattern | Rejected |
| C: Add `env`/`printenv` to ShellGuard deny patterns | Block env-reading commands | Command-level control, zero implementation changes | Too narrow: `echo $API_KEY`, `cat /proc/*/environ`, child process inheritance still bypass; env is inherited regardless of command blocking | Rejected |

**Rationale for A**: Denylist is fragile (defense-by-name). Option C only prevents direct inspection commands, not inherent env inheritance by child processes. Allowlist (ZeroClaw pattern) provides defense-by-default with zero-leakage guarantee.

#### 2.2.2 Decision

Clear environment before agent shell execution, inject only safe variables from allowlist.

**Rationale**: `ShellGuard` blocks dangerous COMMANDS (8 deny patterns) but not env leakage. Agent can run `env`, `printenv`, or `echo $API_KEY` without triggering any deny pattern.

**Design Intent (F-2)**: ShellGuard deny patterns are **NOT** updated to block `env`/`printenv`/`echo $VAR` commands. This is intentional — Option C was evaluated and rejected (see above). The layered defense is:
1. **This decision** (Decision 2): host env never reaches the subprocess — primary prevention
2. **Decision 1** (output scrubber): if any path still extracts env data, scrubber catches it in the output — secondary detection

Both layers are independent. Removing either increases residual risk.

**Implementation**:
- Modified file: `shell_guard.py` — add `scrub_environment()` method (~30 LOC)
- Safe allowlist (9 vars): `PATH`, `HOME`, `LANG`, `LC_ALL`, `TZ`, `TERM`, `USER`, `SHELL`, `TMPDIR`
- `LC_ALL` included for Vietnamese UTF-8 locale (`vi_VN.UTF-8`)
- Missing vars are **omitted** (not set to empty string — avoids confusing tools with unexpected empty values)
- Callers pass returned dict as `subprocess.Popen(env=safe_env)`

**Consequences**:
- Defense-in-depth with Decision 1 (even if output scrubbing misses a pattern, env is cleared at process spawn time)
- Some tools may break if they depend on non-allowlisted env vars — acceptable, allowlist can be extended explicitly
- Vietnamese locale preserved via LC_ALL

**FR**: FR-043

#### 2.2.3 Testability

**How will we verify this decision is correct?**

| Verification | Method | Test IDs |
|-------------|--------|----------|
| Only 9 safe vars returned (none more) | Unit: full env (20+ vars) → exactly 9 max | ES-01 |
| Secrets excluded from returned dict | Unit: host has API_KEY, SECRET → not returned | ES-02 |
| LC_ALL included when present | Unit: host has `LC_ALL=vi_VN.UTF-8` → present | ES-03 |
| Missing var is omitted not empty | Unit: host lacks TMPDIR → key absent | ES-04 |
| PATH preserved exactly | Unit: PATH value unchanged | ES-05 |
| Empty host env → empty dict | Unit: no env vars set → `{}` | ES-06 |
| Subprocess inherits no secrets | Integration: spawn with `safe_env`; run `env` inside; inspect output | Security test |

---

### Decision 3: History Compaction (Pattern B) — LOCKED

#### 2.3.1 Options Considered

| Option | Approach | Pros | Cons | Decision |
|--------|----------|------|------|----------|
| **A: LLM-based summarization** (Selected) | Call `qwen3:8b` to summarize oldest 60% of messages; inject summary in system_prompt | Context continuity preserved; semantic compression of decisions and context | Extra LLM call cost (~$0.001); qwen3:8b may not be loaded | **SELECTED** |
| B: Sliding window (last N messages only) | Discard oldest, keep only most recent N messages | Zero cost; no dependencies; no LLM call | Agent "forgets" decisions made in discarded messages — context discontinuity | Rejected (used as **deterministic fallback** only) |
| C: External summary table | Push old messages to a new `conversation_summaries` table; inject reference | Zero context loss; messages preserved | Requires new DB migration — **CTO veto: no new migrations for Sprint 179** | Rejected |

**Rationale for A**: CTO mandate: no new migration eliminates Option C. Sliding window (Option B) destroys context continuity — the agent loses earlier decisions. LLM summarization (Option A) preserves semantics. Option B is retained as the deterministic fallback when the summarizer call fails.

#### 2.3.2 Decision

Auto-summarize at `max_messages * 0.8` threshold using `qwen3:8b`, store in existing `metadata_` JSONB column. No new migration.

**Rationale**: `ConversationTracker.max_messages=50` is a hard stop — conversation dies at limit. ZeroClaw compacts instead: summarize older context, keep recent messages, extend conversation lifespan.

**Trigger Location (F-3)**: Compaction triggers in `TeamOrchestrator._process()` (the message processing loop), **NOT** in `ConversationTracker.check_limits()`.

`check_limits()` runs per-message returning a binary pass/fail — adding a side-effecting async LLM call there creates hidden state changes in a validation function. `_process()` is the correct location because it owns the conversation state update loop. A stale-guard prevents repeated triggering:

```python
# In TeamOrchestrator._process(), before invoker call:
if conversation.total_messages >= int(conversation.max_messages * 0.8):
    last_compacted = conversation.metadata_.get("last_compacted_at")
    messages_since = conversation.total_messages - conversation.metadata_.get("compacted_at_count", 0)
    if last_compacted is None or messages_since >= int(conversation.max_messages * 0.2):
        await history_compactor.compact(conversation, db)
```

The stale-guard fires compaction once per threshold crossing: on reaching 40 messages (for max=50), then again if 10 more messages accumulate after compaction (reaching 50 → compact again, resetting). This prevents repeated compaction on every message after the threshold.

**Summarizer Bounds (F-4)**:
- Input: oldest `max_messages * 0.6` messages (those being compacted), **max 4,000 tokens** of input
- Output: **max 500 tokens** (≈2,000 chars) summary
- Model: `qwen3:8b` — fast model, separate from agent's primary model
- Timeout: **10 seconds** hard timeout on summarizer HTTP call to Ollama
- Fallback (if timeout/error): deterministic truncation — keep last `max_messages * 0.4` messages, prepend `[Earlier context truncated — {count} messages omitted]` — **no exception raised to caller**

**Context Injection Method (F-5)**: Summary is **appended to the `system_prompt` string** in `_build_llm_context()`, not prepended as a synthetic user/assistant message in `context_messages`. Rationale: `_build_llm_context()` returns `(system_prompt, messages)` tuple — the system prompt is the natural location for persistent context that is not part of the turn-by-turn exchange.

```python
# In _build_llm_context(), after building base system_prompt:
compaction_summary = conversation.metadata_.get("compaction_summary")
if compaction_summary:
    compacted_count = conversation.metadata_.get("compacted_message_count", 0)
    system_prompt += (
        f"\n\n[CONVERSATION SUMMARY — {compacted_count} earlier messages compacted]\n"
        f"{compaction_summary}"
    )
```

**Implementation**:
- New file: `history_compactor.py` (~100 LOC)
- Storage: `agent_conversations.metadata_` JSONB keys: `compaction_summary`, `last_compacted_at`, `compaction_count`, `compacted_at_count`, `compacted_message_count`

**Consequences**:
- Conversations survive beyond 50 messages with semantic context continuity
- Additional LLM call cost per compaction (~$0.001 per compaction with qwen3:8b)
- No migration needed (existing JSONB column, stale-guard prevents repeat triggers)
- Audit trail preserved — messages are NOT deleted from `agent_messages` table

**FR**: FR-044

#### 2.3.3 Testability

**How will we verify this decision is correct?**

| Verification | Method | Test IDs |
|-------------|--------|----------|
| Trigger fires at 80% (40/50 msgs) | Unit: 40 msgs → `should_compact=True` | HC-01 |
| No trigger before threshold | Unit: 39 msgs → `should_compact=False` | HC-02 |
| Stale-guard prevents repeat triggers | Integration: send 45 msgs; verify compact fires once only | HC integration |
| Last 40% messages preserved | Unit: 50 msgs compact → 20 recent preserved | HC-03 |
| Summary ≤ 2000 chars | Unit: 30 msgs → summary length ≤ 2000 | HC-04 |
| Key decisions in summary | Unit: msgs with "decided to use X" → summary contains decision | HC-05 |
| Deterministic fallback on timeout | Unit: LLM timeout → truncation, no exception | HC-06 |
| Summary injected into system_prompt | Unit: `_build_llm_context()` → summary in system_prompt, not in messages | HC-07 |
| `metadata_` keys set correctly | Unit: after compaction → `compaction_summary` key present | HC-08 |
| `last_compacted_at` ISO timestamp | Unit: after compaction → valid ISO timestamp | HC-09 |
| Disabled when max_messages=0 | Unit: max=0 → `should_compact=False` | HC-10 |
| Agent references earlier decisions | Integration: compact at 40 msgs; agent at msg 42 correctly references msg 5 content | MA extension |

---

### Decision 4: Query Classification for Model Routing (Pattern E) — LOCKED

#### 2.4.1 Options Considered

| Option | Approach | Pros | Cons | Decision |
|--------|----------|------|------|----------|
| **A: Keyword-based rules** (Selected) | Pure function, configurable rules with keywords + length filters (AND-conditions), first-match-wins | Deterministic, auditable, zero latency, easily extendable, ZeroClaw-proven | Cannot understand context — mitigated by AND-condition length filters | **SELECTED** |
| B: LLM-based intent classification | Call small model to classify intent before primary invocation | Semantic understanding of complex queries | Extra LLM call overhead defeats purpose — routing to faster model requires a fast classification itself | Rejected |
| C: User-defined model override per message | Allow API callers to specify model via message metadata field | Full control | Complex API surface; not self-tuning; leaks model selection details to callers | Rejected (can be added as P2 extension in Sprint 180+) |

**Rationale for A**: Deterministic classification is auditable and zero-cost. LLM-based classification (Option B) creates a chicken-and-egg latency problem. Option C adds complexity and surface area. Keyword rules are the ZeroClaw-proven pattern with AND-condition length filters guarding against false positives.

#### 2.4.2 Decision

Pure function that classifies query intent to override MODEL (not provider) per role using AND-condition keyword rules.

**Rationale**: `ROLE_MODEL_DEFAULTS` maps each role to a fixed model. A coder always gets `qwen3-coder:30b` whether the query is "implement OAuth" (complex) or "ok" (trivial). ZeroClaw classifies queries to route to appropriate model tier within the same provider.

**Integration Pattern (F-6)**: Classification occurs in `TeamOrchestrator._process()`, and the hint is passed to `_build_invoker(definition, model_hint=hint)` which overrides `ProviderConfig.model` within the provider chain. This is Option A from the architect review — `_build_invoker()` owns the model selection contract and is the correct owner of the override.

```python
# In TeamOrchestrator._process():
hint = query_classifier.classify(message.content, DEFAULT_CLASSIFICATION_RULES)
invoker = await self._build_invoker(definition, model_hint=hint)

# In _build_invoker(definition, model_hint=None):
role_hints = MODEL_ROUTE_HINTS.get(definition.sdlc_role, {})
if model_hint and model_hint in role_hints:
    model = role_hints[model_hint]   # override for this query
else:
    model = definition.model         # role default unchanged
provider_config = ProviderConfig(model=model, ...)
```

**AND-Condition Semantics (F-7)**: ALL conditions specified in a rule must match simultaneously. Rules are AND-evaluated, not OR-evaluated:
- A rule with `keywords=["yes", "no", "ok"]` AND `max_length=20` fires only when **both** are true
- `"no"` (length=2, ≤20) → fast rule matches ✓
- `"no, don't delete the database"` (length=31, >20) → max_length guard fails → rule skipped ✓
- `"no"` with a rule having `min_length=50` → min_length guard fails → rule skipped ✓

**Implementation**:
- New file: `query_classifier.py` (~80 LOC)
- Pure function: `classify(message: str, rules: list[ClassificationRule]) -> str | None`
- `ClassificationRule` fields: `keywords: list[str]`, `patterns: list[str]`, `min_length: int | None`, `max_length: int | None`, `hint: str`, `priority: int`
- ALL specified conditions AND-evaluated; rules sorted by priority (highest first); first full-match wins; `None` returned if no rule matches
- Default SDLC rules in `config.py`:
  - `hint="code"`: keywords=["implement", "fix", "refactor", "write", "code"], patterns=["\`\`\`", "def ", "class "], priority=10
  - `hint="reasoning"`: keywords=["explain", "analyze", "why", "compare", "review"], min_length=50, priority=5
  - `hint="fast"`: keywords=["yes", "no", "ok", "thanks", "done"], max_length=20, priority=1
- Model routing examples (coder role):
  - `hint="code"` → `qwen3-coder:30b` (role default, no override needed)
  - `hint="reasoning"` → `deepseek-r1:32b` (reasoning model)
  - `hint="fast"` → `qwen3:8b` (fast model)
- Override MODEL only, **NOT provider** — CTO mandate
- Modified files: `config.py` (add `DEFAULT_CLASSIFICATION_RULES` + `MODEL_ROUTE_HINTS`), `team_orchestrator.py` (classify in `_process()`, pass hint to `_build_invoker()`)

**Consequences**:
- Cost reduction: trivial queries use smaller, cheaper models (~3x cheaper for "fast" tier)
- Latency improvement: "ok" responses processed 3x faster with `qwen3:8b`
- No provider change risk — model override only within same provider chain
- First-match-wins with AND-conditions is deterministic and auditable
- Model hint logged per invocation for distribution monitoring

**FR**: (ADR-level decision — no separate FR required, query classification is an optimization not a user-facing requirement)

#### 2.4.3 Testability

**How will we verify this decision is correct?**

| Verification | Method | Test IDs |
|-------------|--------|----------|
| Code hint matched on keyword | Unit: "implement the login form" → hint="code" | QC-01 |
| Reasoning hint matched | Unit: "explain why this architecture..." → hint="reasoning" | QC-02 |
| Fast hint matched with length guard | Unit: "yes" (len=3, ≤20) → hint="fast" | QC-03 |
| No match returns None | Unit: "Tell me about the weather" → None | QC-04 |
| Priority ordering (highest wins) | Unit: "implement and explain" → code (priority=10) beats reasoning (5) | QC-05 |
| Case insensitive matching | Unit: "IMPLEMENT the form" → hint="code" | QC-06 |
| min_length AND-condition | Unit: reasoning rule min_length=50; short message → skipped | QC-07 |
| max_length AND-condition | Unit: fast rule max_length=20; "no, don't delete DB" (len=31) → skipped | QC-08 |
| Integration: model used matches hint | Integration: send "ok" → verify `qwen3:8b` invoked (not role default) | MA extension |
| Integration: long "no" msg not fast | Integration: send "no, don't do that" → verify role default model invoked | MA extension |
| Monitoring: hint logged | Integration: verify `model_hint` appears in invocation trace | Observability |

---

## 3. Testability Summary

| Decision | Verification Method | Test IDs | Coverage Target |
|----------|---------------------|----------|-----------------|
| D1: Output Credential Scrubbing | Unit (6 patterns + order), Integration (DB audit) | CS-01 to CS-10 | 100% |
| D2: Environment Variable Scrubbing | Unit (allowlist), Integration (subprocess env inspect) | ES-01 to ES-06 | 100% |
| D3: History Compaction | Unit (threshold, fallback, injection, stale-guard), Integration (context continuity) | HC-01 to HC-10 | 100% |
| D4: Query Classification | Unit (AND-conditions, priority, case), Integration (model routing) | QC-01 to QC-08 | 100% |

**Coverage rationale**: All 4 new modules are pure functions or deterministic logic (no I/O side effects in the core logic). 100% branch coverage is achievable without complex mocking.

---

## 4. Deferred Decisions

### ADR-057 (Reserved): Dual-Mode Tool Dispatch (Pattern D)

**Status**: DEFERRED — effort underestimated (5-8 → 10-12 days)
**Reason**: Introduces tool calling into agent loop, fundamentally changes `TeamOrchestrator._process()`. Needs dedicated ADR with full impact analysis.
**Blocker for**: Pattern G (Approval Flow with Session Allowlist)

### Pattern G: Approval Flow with Session Allowlist

**Status**: DEFERRED — blocked by ADR-057 (Pattern D must exist first)
**Reason**: Interactive approval flow requires tool dispatch to be functional.

### Pattern F: Channel Draft/Streaming (Progressive Updates)

**Status**: DEFERRED — depends on Sprint 178+ OTT Gateway scope
**Reason**: Requires Telegram Bot API integration and streaming support in agent loop.

---

## 5. Implementation Order (Sprint 179)

```
Day 1-2: Pattern A (Output Credential Scrubbing) + Pattern C (Environment Scrubbing)
         +-- output_scrubber.py (new, ~50 LOC)
         +-- shell_guard.py (modify, +30 LOC → add scrub_environment())
         +-- agent_invoker.py (modify, +5 LOC → scrub at line 253)
         +-- evidence_collector.py (modify, +5 LOC → scrub before SHA256 at line 124)
         +-- Unit tests: CS-01 to CS-10, ES-01 to ES-06

Day 3-4: Pattern B (History Compaction)
         +-- history_compactor.py (new, ~100 LOC)
         +-- team_orchestrator.py (modify, +15 LOC → _process() stale-guard trigger + _build_llm_context() injection)
         +-- conversation_tracker.py (modify, +10 LOC → compaction metadata helpers)
         +-- Unit tests: HC-01 to HC-10

Day 5-6: Pattern E (Query Classification)
         +-- query_classifier.py (new, ~80 LOC)
         +-- config.py (modify, +40 LOC → DEFAULT_CLASSIFICATION_RULES + MODEL_ROUTE_HINTS)
         +-- team_orchestrator.py (modify, +10 LOC → classify in _process(), pass to _build_invoker())
         +-- Unit tests: QC-01 to QC-08

Total: ~440 LOC, 34 new unit tests, 3 new files, 5 modified files
```

---

## 6. Related Documents

| Document | Location | Status |
|----------|----------|--------|
| ADR-056 | `docs/02-design/ADR-056-Multi-Agent-Team-Engine.md` | PROPOSED |
| FR-042 | `docs/01-planning/03-Functional-Requirements/FR-042-Output-Credential-Scrubbing.md` | PROPOSED |
| FR-043 | `docs/01-planning/03-Functional-Requirements/FR-043-Environment-Variable-Scrubbing.md` | PROPOSED |
| FR-044 | `docs/01-planning/03-Functional-Requirements/FR-044-History-Compaction.md` | PROPOSED |
| STM-056 | `docs/02-design/Multi-Agent-Security-Threat-Model.md` | UPDATED (T11-T13) |
| TP-056 | `docs/02-design/Multi-Agent-Test-Plan.md` | UPDATED (CS+ES+HC+QC) |
| SPRINT-179 | `docs/04-build/02-Sprint-Plans/SPRINT-179-ZEROCLAW-HARDENING.md` | PROPOSED |
| ZeroClaw Source | `https://github.com/zeroclaw-labs/zeroclaw` | Reference |

[@pm: FR-042/043/044 are referenced but still PROPOSED — please confirm scope alignment before CTO sign-off]
[@reviewer: Decisions 1+2 introduce security controls (credential scrubbing, env clearing) — please review for CWE-200 coverage completeness before G2]
