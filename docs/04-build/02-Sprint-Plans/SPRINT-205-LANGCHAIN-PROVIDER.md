---
sdlc_version: "6.1.1"
document_type: "Sprint Plan"
status: "PROPOSED"
sprint: "205"
spec_id: "SP-205"
tier: "PROFESSIONAL"
stage: "04 - Build"
---

# Sprint 205 — LangChain Provider Plugin

| Field | Value |
|-------|-------|
| **Sprint** | 205 |
| **Duration** | 5 working days |
| **Goal** | Add LangChain as optional provider plugin for EP-07 multi-agent orchestration |
| **ADR** | ADR-066 (LangChain Multi-Agent Orchestration) |
| **FR** | FR-045 (LangChain Provider Plugin) |
| **LOC** | ~850 |
| **Risk** | LOW (feature-flagged, existing behavior unchanged when disabled) |
| **Dependencies** | ADR-066 APPROVED, `langchain-anthropic`/`langchain-openai`/`langchain-community` in enterprise.txt |

---

## 1. Sprint Goal

Add LangChain as a feature-flagged provider plugin in `agent_invoker.py._call_provider()`. When `LANGCHAIN_ENABLED=true`, agents with `provider="langchain"` use LangChain wrappers (ChatOllama, ChatAnthropic, ChatOpenAI) for structured output, unified tool calling, and automatic token counting. When disabled, zero behavior change.

---

## 2. Current State → Target State

| Aspect | Current (Sprint 204) | Target (Sprint 205) |
|--------|---------------------|---------------------|
| Provider dispatch | `ollama` / `anthropic` branches | + `langchain` branch |
| Structured output | Regex parsing | `with_structured_output()` Pydantic |
| Tool calling | Per-provider implementation | Unified `StructuredTool` interface |
| Token counting | Manual per-provider | `on_llm_end` callback |
| Config | No LangChain settings | `LANGCHAIN_ENABLED`, `LANGCHAIN_DEFAULT_MODEL` |

---

## 3. Architecture

```
EXISTING (UNCHANGED):
  agent_invoker.py._call_provider()
    ├── _call_ollama()       # Direct Ollama /api/generate
    ├── _call_anthropic()    # Direct Anthropic Messages API
    └── NEW: _call_langchain()  # LangChain wrapper

NEW FILES:
  langchain_provider.py      # ChatOllama/Anthropic/OpenAI wrapper
  langchain_tool_registry.py # 5 StructuredTools + authorize_tool_call

MODIFIED FILES:
  agent_invoker.py           # _call_langchain() branch at _call_provider()
  failover_classifier.py     # LangChain exception mapping
  tool_context.py            # authorize_tool_call() guard
  config.py                  # LANGCHAIN_ENABLED, LANGCHAIN_DEFAULT_MODEL
```

---

## 4. Backlog

### Track A: Provider Plugin (Day 1-3)

| # | Task | File | LOC | Day |
|---|------|------|-----|-----|
| A1 | Create `langchain_provider.py` with Optional Dependency Guard | new | ~200 | 1 |
| A2 | ChatOllama wrapper + ChatAnthropic wrapper + ChatOpenAI wrapper | `langchain_provider.py` | incl | 1 |
| A3 | `with_structured_output()` Pydantic integration | `langchain_provider.py` | incl | 1 |
| A4 | Token counting callback (`on_llm_end`) + tiktoken fallback | `langchain_provider.py` | incl | 2 |
| A5 | Add `_call_langchain()` branch in `agent_invoker.py._call_provider()` | modified | ~40 | 2 |
| A6 | Add LangChain exception mapping in `failover_classifier.py` | modified | ~25 | 2 |
| A7 | Add `LANGCHAIN_ENABLED` + `LANGCHAIN_DEFAULT_MODEL` in `config.py` | modified | ~10 | 3 |
| A8 | Write `test_langchain_provider.py` (10 test cases: LC-01 to LC-10) | new | ~150 | 3 |

> **Test case definitions**: Full test case specs (LC-01 to LC-10, LT-01 to LT-05) are in [Multi-Agent-Test-Plan.md §16-§17](../../02-design/13-Testing-Strategy/Multi-Agent-Test-Plan.md).

### Track B: Tool Registry (Day 3-4)

| # | Task | File | LOC | Day |
|---|------|------|-----|-----|
| B1 | Create `langchain_tool_registry.py` with 5 StructuredTools | new | ~200 | 3 |
| B2 | Add `authorize_tool_call()` centralized guard in `tool_context.py` | modified | ~30 | 3 |
| B3 | Integrate tools with `model.bind_tools()` | `langchain_provider.py` | incl | 4 |
| B4 | Write `test_langchain_tools.py` (5 test cases: LT-01 to LT-05) | new | ~150 | 4 |

### Track C: Verification (Day 5)

| # | Task | File | LOC | Day |
|---|------|------|-----|-----|
| C1 | Run all existing tests with `LANGCHAIN_ENABLED=false` (regression) | — | — | 5 |
| C2 | Run new LangChain tests with `LANGCHAIN_ENABLED=true` | — | — | 5 |
| C3 | Frontend `tsc --noEmit` (no frontend changes, regression only) | — | — | 5 |
| C4 | Update IG-056 Provider Integration Guide | modified | ~50 | 5 |

---

## 5. Verification Commands

```bash
# Regression: all existing tests pass with LangChain disabled
LANGCHAIN_ENABLED=false \
DATABASE_URL="postgresql://test:test@localhost:15432/sdlc_test" \
  python -m pytest backend/tests/ -v --tb=short

# New: LangChain provider tests
LANGCHAIN_ENABLED=true \
  python -m pytest backend/tests/unit/test_langchain_provider.py -v

# New: LangChain tool tests
LANGCHAIN_ENABLED=true \
  python -m pytest backend/tests/unit/test_langchain_tools.py -v

# Coverage
python -m pytest backend/tests/ -k "langchain" \
  --cov=backend/app/services/agent_team --cov-report=term-missing
```

---

## 6. Exit Criteria

| Criterion | Target |
|-----------|--------|
| All existing tests pass (LANGCHAIN_ENABLED=false) | 676/676 |
| LC-01 to LC-10 pass | 10/10 |
| LT-01 to LT-05 pass | 5/5 |
| Feature flag respected (disabled = no behavior change) | Verified |
| Optional dependency guard (import without langchain packages) | Verified |
| Zero P0 security bugs | 0 |
| IG-056 updated | Done |

---

## 7. Risks

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| LangChain 0.3.x API breaking change | LOW | MEDIUM | Pin versions in enterprise.txt |
| ChatOllama timeout on large context | MEDIUM | LOW | Same timeout as direct Ollama |
| Token counting inaccuracy | LOW | LOW | tiktoken fallback as safety net |
