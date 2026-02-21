---
sdlc_version: "6.1.0"
document_type: "Sprint Plan"
status: "PROPOSED"
sprint: "179"
spec_id: "SPRINT-179"
tier: "PROFESSIONAL"
stage: "04 - Build"
---

# SPRINT-179 -- ZeroClaw Security + Architecture Hardening

**Status**: PROPOSED (pending CTO approval)
**Sprint Duration**: 6 working days
**Sprint Goal**: Adopt 4 ZeroClaw best practices (A+C+B+E) into EP-07 Multi-Agent Team Engine
**Epic**: EP-07 Multi-Agent Team Engine
**ADR**: ADR-058 (4 locked micro-decisions)
**Dependencies**: Sprint 178 complete (team_orchestrator, evidence_collector, agent_invoker operational)
**Budget**: ~$3,840 (48 hrs at $80/hr)

---

## 1. Sprint Goal

Integrate 4 production-proven patterns from ZeroClaw (`zeroclaw-labs/zeroclaw`, 12.5K stars, Rust, MIT) into the Multi-Agent Team Engine to close P0 security gaps and improve architecture resilience:

| Pattern | Priority | New LOC | Modified LOC | Days |
|---------|----------|---------|-------------|------|
| A: Output Credential Scrubbing | P0 Security | ~50 | ~10 | 1 |
| C: Environment Variable Scrubbing | P0 Security | ~30 | ~5 | 0.5 |
| B: History Compaction | P1 Architecture | ~100 | ~25 | 2 |
| E: Query Classification | P2 Optimization | ~80 | ~50 | 1.5 |
| Tests + Integration | -- | ~180 | -- | 1 |
| **Total** | | **~440** | **~90** | **6** |

---

## 2. Deliverables

| # | Deliverable | Description | Files | Sprint Day |
|---|------------|-------------|-------|------------|
| 1 | `output_scrubber.py` | 6 credential regex patterns, redaction format | New | Day 1 |
| 2 | `agent_invoker.py` update | Scrub `InvocationResult.content` post-invocation | Modified | Day 1 |
| 3 | `evidence_collector.py` update | Scrub -> hash -> store order enforcement | Modified | Day 1 |
| 4 | `test_output_scrubber.py` | CS-01 to CS-10 (10 tests) | New | Day 1 |
| 5 | `shell_guard.py` update | `scrub_environment()` method + 9-var allowlist | Modified | Day 2 |
| 6 | `test_env_scrubber.py` | ES-01 to ES-06 (6 tests) | New | Day 2 |
| 7 | `history_compactor.py` | Auto-summarize + fallback + metadata_ storage | New | Day 3-4 |
| 8 | `team_orchestrator.py` update | `_build_llm_context()` injects compaction summary | Modified | Day 4 |
| 9 | `conversation_tracker.py` update | Compaction trigger at 80% threshold | Modified | Day 4 |
| 10 | `test_history_compactor.py` | HC-01 to HC-10 (10 tests) | New | Day 4 |
| 11 | `query_classifier.py` | Pure function + SDLC classification rules | New | Day 5 |
| 12 | `config.py` update | `DEFAULT_CLASSIFICATION_RULES` + `MODEL_ROUTE_HINTS` | Modified | Day 5 |
| 13 | `team_orchestrator.py` update | Classify in `_process()`, override model | Modified | Day 5 |
| 14 | `test_query_classifier.py` | QC-01 to QC-08 (8 tests) | New | Day 5 |
| 15 | Integration testing + regression | All 34 new tests pass, existing 87 tests unbroken | -- | Day 6 |

---

## 3. Daily Schedule

### Day 1: Pattern A -- Output Credential Scrubbing (P0 Security)

**Goal**: Prevent credential leakage in agent tool output

**Tasks**:
1. Create `output_scrubber.py` with `OutputScrubber` class
   - 6 credential regex patterns (token, api_key, password, secret, bearer, credential)
   - Redaction: preserve first 4 chars + `****[REDACTED]`
   - Returns `(scrubbed_text, violations: list[str])`
2. Integrate into `agent_invoker.py`:
   - After `_call_ollama()` / `_call_anthropic()` returns content
   - Scrub `InvocationResult.content` before returning to caller
3. Integrate into `evidence_collector.py`:
   - In `capture_message()`, scrub `message.content` BEFORE `_compute_content_hash()`
   - Enforced order: scrub -> hash -> store
4. Write and pass CS-01 to CS-10 (10 unit tests)

**Verification**:
```bash
python -m pytest backend/tests/unit/test_output_scrubber.py -v
```

**Exit Criteria**: All 10 CS tests pass, no credential patterns in scrubbed output

### Day 2: Pattern C -- Environment Variable Scrubbing (P0 Security)

**Goal**: Prevent env var leakage during agent shell execution

**Tasks**:
1. Add `SAFE_ENV_VARS` constant to `shell_guard.py`:
   ```python
   SAFE_ENV_VARS: tuple[str, ...] = (
       "PATH", "HOME", "LANG", "LC_ALL", "TZ",
       "TERM", "USER", "SHELL", "TMPDIR",
   )
   ```
2. Add `scrub_environment()` static method to `ShellGuard`:
   - Read `os.environ`, filter to `SAFE_ENV_VARS` only
   - Omit vars not present in host env (don't set to empty)
   - Return `dict[str, str]` for use as `subprocess.Popen(env=...)`
3. Write and pass ES-01 to ES-06 (6 unit tests)
4. Run regression on existing SG-01 to SG-11

**Verification**:
```bash
python -m pytest backend/tests/unit/test_env_scrubber.py -v
python -m pytest backend/tests/unit/test_shell_guard.py -v  # regression
```

**Exit Criteria**: All 6 ES tests pass + all 11 SG tests still pass

### Day 3-4: Pattern B -- History Compaction (P1 Architecture)

**Goal**: Conversations survive beyond 50 messages with context continuity

**Tasks**:
1. Create `history_compactor.py` with `HistoryCompactor` class:
   - `should_compact(total_messages, max_messages) -> bool` -- trigger at 80%
   - `compact(conversation, messages, db) -> str` -- returns summary
   - `_summarize_messages(messages) -> str` -- LLM call via AgentInvoker
   - `_fallback_truncate(messages) -> str` -- deterministic fallback
2. Summarizer configuration:
   - Model: `qwen3:8b` (fast, not the agent's primary model)
   - Prompt: "Preserve: user preferences, commitments, decisions, unresolved tasks, key facts. Omit: filler, repeated chit-chat, verbose tool logs."
   - Max summary length: 2,000 characters
3. Storage in `agent_conversations.metadata_` JSONB:
   - `compaction_summary: str`
   - `last_compacted_at: str` (ISO 8601)
   - `compaction_count: int`
4. Modify `team_orchestrator._build_llm_context()`:
   - Check `metadata_.compaction_summary` exists
   - If exists, inject as first system message before recent messages
5. Modify `conversation_tracker.py`:
   - Add compaction trigger check in message processing flow
6. Write and pass HC-01 to HC-10 (10 unit tests)

**Verification**:
```bash
python -m pytest backend/tests/unit/test_history_compactor.py -v
```

**Exit Criteria**: All 10 HC tests pass, compaction summary stored in metadata_ JSONB

### Day 5: Pattern E -- Query Classification (P2 Optimization)

**Goal**: Dynamic model routing based on query intent

**Tasks**:
1. Create `query_classifier.py`:
   - `ClassificationRule` dataclass: hint, keywords, patterns, min_length, max_length, priority
   - `classify(message, rules) -> str | None` -- pure function, first match wins
   - Rules sorted by priority (highest first)
2. Add to `config.py`:
   - `DEFAULT_CLASSIFICATION_RULES`: 3 rules (code, reasoning, fast)
   - `MODEL_ROUTE_HINTS`: maps hint -> model override per provider
3. Integrate into `team_orchestrator._process()`:
   - Call `classify()` on incoming message content
   - If hint returned, override model (NOT provider) in invoker config
4. Write and pass QC-01 to QC-08 (8 unit tests)

**Verification**:
```bash
python -m pytest backend/tests/unit/test_query_classifier.py -v
```

**Exit Criteria**: All 8 QC tests pass, model override working for code/reasoning/fast hints

### Day 6: Integration Testing + Regression + Documentation

**Goal**: Ensure all new code integrates cleanly with existing Sprint 176-178 deliverables

**Tasks**:
1. Run full agent_team test suite (87 existing + 34 new = 121 total)
2. Run coverage check (target: 95%+)
3. Fix any regression failures
4. Update CLAUDE.md to v3.8.0 with Sprint 179 context
5. Final code review preparation

**Verification**:
```bash
# Full test suite
python -m pytest backend/tests/ -k "agent_team" \
  --cov=backend/app/services/agent_team \
  --cov-report=term-missing -v

# Regression
python -m pytest backend/tests/ -v --tb=short
```

**Exit Criteria**: 121/121 tests pass, 95%+ coverage, zero P0 bugs

---

## 4. Success Criteria

| Criterion | Target | Measurement |
|-----------|--------|-------------|
| All new unit tests pass | 34/34 | CS(10) + ES(6) + HC(10) + QC(8) |
| All existing tests pass | 87/87 | Regression (no breakage) |
| Unit test coverage | 95%+ | `--cov-report=term-missing` |
| Credential scrubbing working | Dual integration | CS-09, CS-10 pass |
| Env scrubbing working | 9 safe vars only | ES-01 pass |
| History compaction working | Trigger at 80% | HC-01, HC-04 pass |
| Query classification working | 3 hint types | QC-01, QC-02, QC-03 pass |
| Zero P0 bugs | 0 | No test failures in CI |
| No new Alembic migration | 0 | No files in `alembic/versions/` |

---

## 5. Risks

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|-----------|
| Credential regex false positives | Medium | Low | Preserve 4 chars, log all scrubs for review |
| Summarizer LLM failure during compaction | Medium | Medium | Deterministic fallback (truncation, no exception) |
| Query classification misrouting | Low | Low | Pure function, easy to tune rules post-deployment |
| Env allowlist too restrictive | Low | Medium | Add vars to allowlist as needed, log blocked vars |

---

## 6. Dependencies

| Dependency | Type | Status |
|-----------|------|--------|
| Sprint 178 complete | Prerequisite | Required |
| `agent_invoker.py` operational | Code | Available (Sprint 177) |
| `evidence_collector.py` operational | Code | Available (Sprint 178) |
| `shell_guard.py` operational | Code | Available (Sprint 177) |
| `team_orchestrator.py` operational | Code | Available (Sprint 178) |
| `config.py` operational | Code | Available (Sprint 177) |
| Ollama `qwen3:8b` available | Infrastructure | Available |
| `metadata_` JSONB column exists | Database | Available (Sprint 177) |

---

## 7. Definition of Done

- [ ] 3 new service files created (output_scrubber, history_compactor, query_classifier)
- [ ] 5 existing service files modified (agent_invoker, evidence_collector, shell_guard, team_orchestrator, config)
- [ ] 34 new unit tests written and passing
- [ ] 87 existing unit tests still passing (regression)
- [ ] 95%+ test coverage for `backend/app/services/agent_team/`
- [ ] No new Alembic migration files
- [ ] CLAUDE.md updated to v3.8.0
- [ ] STM-056 updated with T11-T13
- [ ] TP-056 updated with CS+ES+HC+QC test suites
- [ ] Code review by CTO (2+ approvers)
- [ ] Zero P0 bugs
