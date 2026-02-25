# Sprint 204 — Confidence-Based Routing + Human Escalation

**Sprint Duration**: May 19 – May 30, 2026 (10 working days)
**Sprint Goal**: Add confidence scoring to `query_classifier.py` and implement human escalation path for low-confidence agent queries via Magic Link approval flow
**Status**: PLANNED
**Priority**: P3 (Confidence-Based Routing)
**Framework**: SDLC 6.1.1
**CTO Score (Sprint 203)**: TBD
**Previous Sprint**: [Sprint 203 — Formal Evaluator-Optimizer + Evals Expansion](SPRINT-203-EVALUATOR-OPTIMIZER-EVALS-EXPANSION.md)

---

## Sprint 204 Goal

Sprint 203 delivers the Evaluator-Optimizer with rubric scoring and expands evals to 15 test cases. Sprint 204 addresses **Gap 3 (P3): Confidence-Based Routing** — the last medium-priority gap from the Anthropic Best Practices roadmap.

**Current state** (`query_classifier.py`):
- Simple substring priority matching (`kw in msg_lower`, no `re` module)
- 3 classification hints: code (priority=10, pattern "```"), reasoning (priority=5, keywords), fast (priority=1, max_length=20)
- `MODEL_ROUTE_HINTS` maps hints to specific Ollama models
- **No confidence score** — classification is binary (match/no-match)
- **No human escalation path** — low-confidence queries still go to LLM
- **No LLM-based classification** — pure substring matching misses nuanced intents

**Target state**:
- `confidence: float` field on `ClassificationResult` (0.0 to 1.0)
- When confidence < 0.6: route to human escalation (Magic Link approval)
- Optional LLM-based classification using `qwen3:8b` (fastest model) for ambiguous queries
- Human escalation reuses existing `magic_link_service.py` (HMAC-SHA256 OOB auth)

**Source**: CTO-approved Anthropic Best Practices Applicability Analysis (9.2/10) — Gap 3 (P3).

---

## Sprint 204 Backlog

### Track A — Confidence Scoring in query_classifier.py (Day 1-4) — @pm

**Goal**: Add confidence scoring to the existing substring-based classifier and implement a fast LLM fallback for ambiguous queries.

**Architecture**:
```
User message arrives
    │
    ├─ query_classifier.classify(message)
    │   ├─ Substring matching (existing):
    │   │   ├─ "```" in message → code (confidence=0.95)
    │   │   ├─ "tại sao" in message → reasoning (confidence=0.85)
    │   │   ├─ len(message) <= 20 → fast (confidence=0.75)
    │   │   └─ No match → unknown (confidence=0.3)
    │   │
    │   ├─ Multiple matches? → highest priority wins, confidence adjusted
    │   │   ├─ Single clear match → confidence=0.9+
    │   │   ├─ Multiple matches → confidence = best - 0.2
    │   │   └─ No matches → confidence = 0.3 (unknown)
    │   │
    │   └─ confidence < 0.6?
    │       ├─ YES → LLM fallback (qwen3:8b, <500ms)
    │       │   └─ "Classify this query: code/reasoning/fast/governance/unknown"
    │       │   └─ LLM returns: {hint: "governance", confidence: 0.82}
    │       │
    │       └─ Still < 0.6 after LLM? → human escalation (Track B)
    │
    └─ Return: ClassificationResult(hint, confidence, model_route, method)
```

| ID | Item | Priority | Deliverable |
|----|------|----------|-------------|
| A-01 | Add `confidence: float` to `ClassificationResult` | P0 | 0.0-1.0 score based on match quality |
| A-02 | Confidence scoring rules for substring matches | P0 | Single match: 0.9+, multiple: best-0.2, none: 0.3 |
| A-03 | LLM fallback classifier (qwen3:8b) | P1 | For confidence < 0.6: fast LLM classification (<500ms target) |
| A-04 | New hint type: `governance` | P1 | Detect governance intents (approve, evaluate, status) → route to command_router |
| A-05 | Classification logging: method + confidence | P1 | Log: substring vs LLM, confidence score, final hint, latency |
| A-06 | Classification metrics: confidence distribution | P2 | Track: % queries at each confidence band (>0.9, 0.6-0.9, <0.6) |

**Modified files**:
- `backend/app/services/agent_team/query_classifier.py` (~50 LOC additions)
- `backend/app/schemas/agent_team.py` — Add `confidence` field to schema

**Confidence Scoring Rules**:
```python
def _compute_confidence(self, matches: list[HintMatch]) -> float:
    """Compute confidence based on match quality."""
    if not matches:
        return 0.3  # No matches = low confidence

    if len(matches) == 1:
        # Single clear match = high confidence
        match = matches[0]
        if match.priority >= 10:  # code (``` pattern)
            return 0.95
        elif match.priority >= 5:  # reasoning (keyword match)
            return 0.85
        else:  # fast (length heuristic)
            return 0.75

    # Multiple matches = reduced confidence (ambiguous)
    best = max(m.priority for m in matches)
    second = sorted([m.priority for m in matches], reverse=True)[1]
    gap = best - second
    return min(0.9, 0.6 + (gap * 0.1))  # Larger gap = more confident
```

**LLM Fallback Prompt** (qwen3:8b, <500ms):
```
Classify this user message into one category.

Categories:
- code: Request to write, fix, or review code
- reasoning: Request requiring deep analysis or explanation
- governance: Request for gate actions, evidence, sprint management
- fast: Simple greeting, acknowledgment, or short query

Message: "{user_message}"

Return JSON: {"hint": "category", "confidence": 0.0-1.0}
```

**Acceptance criteria**:
- [ ] `ClassificationResult` includes `confidence` field (0.0-1.0)
- [ ] Single substring match: confidence >= 0.75
- [ ] No match: confidence = 0.3 → triggers LLM fallback
- [ ] LLM fallback responds in <500ms using `qwen3:8b`
- [ ] Classification method logged (substring vs LLM)

---

### Track B — Human Escalation for Low-Confidence Queries (Day 3-6) — @pm

**Goal**: When confidence remains < 0.6 after LLM fallback, route the query to a human operator via Magic Link approval — the same OOB auth pattern used for gate approvals (Sprint 199).

**Architecture**:
```
Query with confidence < 0.6 (after LLM fallback)
    │
    ├─ escalation_service.escalate(query, user, conversation_id)
    │   ├─ Generate Magic Link: "Review this query classification"
    │   │   └─ Payload: {query, suggested_hint, confidence, options: [code/reasoning/governance/fast]}
    │   │
    │   ├─ Send to designated human reviewer:
    │   │   ├─ Telegram: "Low-confidence query from @user: '{query}'"
    │   │   │   └─ "Classify as: [Code] [Reasoning] [Governance] [Fast]"
    │   │   │   └─ Magic Link per option (5-min TTL)
    │   │   │
    │   │   └─ Or: Project PM/CTO gets notification
    │   │
    │   └─ Meanwhile: user gets "Processing..." message
    │
    ├─ Human clicks classification link
    │   └─ query_classifier.record_human_classification(query, hint="governance")
    │   └─ Agent proceeds with human-selected classification
    │
    └─ Timeout (5 min): fallback to LLM's best guess with warning
```

| ID | Item | Priority | Deliverable |
|----|------|----------|-------------|
| B-01 | `escalation_service.py` — human escalation routing | P0 | Routes low-confidence queries to human reviewer via Magic Link |
| B-02 | Magic Link for classification (reuse magic_link_service.py) | P0 | 4 classification options as separate Magic Links (5-min TTL) |
| B-03 | Human reviewer notification via Telegram | P1 | Designated reviewer gets query + classification options |
| B-04 | Timeout fallback (5 min) | P1 | If no human response: use LLM's best guess + log as "unconfirmed" |
| B-05 | Human classification logging for training data | P1 | Record: (query, human_hint, llm_hint, confidence) for future model fine-tuning |
| B-06 | Escalation rate monitoring | P2 | Track: % queries escalated per day/week, response time, timeout rate |

**New files**:
- `backend/app/services/agent_team/escalation_service.py` (~100 LOC)

**Modified files**:
- `backend/app/services/agent_team/query_classifier.py` — Route to escalation when confidence < 0.6
- `backend/app/services/agent_team/magic_link_service.py` — Add classification payload type

**Acceptance criteria**:
- [ ] Queries with confidence < 0.6 (after LLM fallback) trigger human escalation
- [ ] Human reviewer receives Telegram notification with 4 classification options
- [ ] Human click resolves classification, agent proceeds
- [ ] 5-min timeout: falls back to LLM's best guess with `"unconfirmed"` flag
- [ ] All escalations logged as training data (query, human_hint, llm_hint)

---

### Track C — Eval Integration + Routing Quality Measurement (Day 5-8) — @pm

**Goal**: Add routing-quality eval cases and integrate confidence scoring into the existing eval framework.

| ID | Item | Priority | Deliverable |
|----|------|----------|-------------|
| C-01 | 5 routing eval test cases (YAML) | P0 | Test correct classification + confidence for known query types |
| C-02 | Eval case: ambiguous query → LLM fallback triggered | P1 | Verify LLM fallback activates when substring matching fails |
| C-03 | Eval case: governance intent correctly detected | P1 | "approve gate 5" → governance hint, confidence >= 0.8 |
| C-04 | Routing accuracy dashboard on Gateway Dashboard | P2 | New section: classification distribution, confidence histogram, escalation rate |
| C-05 | Add routing evals to baseline.json | P1 | 5 routing cases added to baseline for regression detection |

**Eval test cases (5 YAML files)**:
```yaml
# routing_code.yaml
prompt: "```python\ndef hello():\n    print('hi')\n```\nFix this function"
expected_hint: "code"
expected_min_confidence: 0.9
method: "substring"

# routing_governance.yaml
prompt: "approve gate 5 for project sdlc-orchestrator"
expected_hint: "governance"
expected_min_confidence: 0.8
method: "substring_or_llm"

# routing_ambiguous.yaml
prompt: "review the latest changes and tell me what you think"
expected_hint: "reasoning"
expected_max_confidence: 0.7  # Should be low - ambiguous between code review and reasoning
expected_method: "llm_fallback"

# routing_fast.yaml
prompt: "ok"
expected_hint: "fast"
expected_min_confidence: 0.7
method: "substring"

# routing_vietnamese.yaml
prompt: "tại sao gate G2 bị reject?"
expected_hint: "reasoning"
expected_min_confidence: 0.8
method: "substring"
```

**Acceptance criteria**:
- [ ] 5 routing eval cases pass with expected hints and confidence ranges
- [ ] Ambiguous queries correctly trigger LLM fallback
- [ ] Baseline updated with routing eval scores
- [ ] Total eval cases: 20 (15 from Sprint 203 + 5 routing)

---

### Track D — Testing + Sprint Close (Day 8-10) — @pm

| ID | Item | Priority | Deliverable |
|----|------|----------|-------------|
| D-01 | Confidence scoring unit tests (8 cases) | P0 | Single match, multiple matches, no match, edge cases |
| D-02 | LLM fallback unit tests (5 cases) | P0 | Fallback triggers, timeout handling, response parsing |
| D-03 | Human escalation unit tests (6 cases) | P0 | Magic Link generation, timeout fallback, human click resolution |
| D-04 | Integration test: full routing flow | P1 | Message → classify → confidence check → (LLM/human) → route |
| D-05 | Regression test: existing classifications unchanged | P0 | Verify Sprint 179 query_classifier behavior preserved |
| D-06 | Regression test suite (950+ tests) | P0 | All Sprint 197-203 tests passing + Sprint 204 new tests |
| D-07 | Sprint 204 close documentation | P1 | G-Sprint-Close within 24h |

---

## Architecture: Confidence-Based Routing Flow

### Full Classification Pipeline

```
  User Message            query_classifier.py         qwen3:8b (LLM)
       │                        │                          │
       │── "review changes" ──>│                          │
       │                        │── substring scan         │
       │                        │   "review" → reasoning   │
       │                        │   "changes" → code?      │
       │                        │   Multiple matches!      │
       │                        │   confidence = 0.5       │
       │                        │                          │
       │                        │── confidence < 0.6       │
       │                        │── LLM fallback ────────>│
       │                        │                          │── classify
       │                        │<── {hint: "code",        │
       │                        │     confidence: 0.78} ──│
       │                        │                          │
       │                        │── confidence = 0.78      │
       │                        │── >= 0.6 → proceed       │
       │                        │                          │
       │<── ClassificationResult│                          │
       │    hint="code"         │                          │
       │    confidence=0.78     │                          │
       │    method="llm"        │                          │
```

### Human Escalation Flow

```
  User Message          query_classifier       escalation_service     Human Reviewer
       │                      │                       │                     │
       │── "something         │                       │                     │
       │    vague" ──────────>│                       │                     │
       │                      │── substring: 0.3      │                     │
       │                      │── LLM: 0.45           │                     │
       │                      │── still < 0.6!        │                     │
       │                      │                       │                     │
       │                      │── escalate() ────────>│                     │
       │                      │                       │── Magic Links ────>│
       │<── "Processing,      │                       │   [Code][Reason]   │
       │     waiting for      │                       │   [Gov][Fast]      │
       │     reviewer..." ────│                       │                     │
       │                      │                       │                     │
       │                      │                       │<── clicks [Code] ──│
       │                      │                       │                     │
       │                      │<── hint="code" ───────│                     │
       │                      │    source="human"     │                     │
       │                      │                       │                     │
       │<── Agent proceeds    │                       │                     │
       │    with code hint    │                       │                     │
```

---

## Files Summary

| File | Action | LOC | Track |
|------|--------|-----|-------|
| `backend/app/services/agent_team/query_classifier.py` | MODIFY | ~50 | A |
| `backend/app/schemas/agent_team.py` | MODIFY | ~10 | A |
| `backend/app/services/agent_team/escalation_service.py` | NEW | ~100 | B |
| `backend/app/services/agent_team/magic_link_service.py` | MODIFY | ~20 | B |
| `backend/tests/evals/cases/routing_*.yaml` | NEW | ~25 (5 files) | C |
| `backend/tests/evals/baseline.json` | MODIFY | ~5 | C |
| Tests (unit + integration) | NEW | ~300 | D |
| **Total** | | **~510** | |

---

## Sprint 204 Success Criteria

**Hard criteria (8)**:
- [ ] `ClassificationResult` includes `confidence` field (0.0-1.0)
- [ ] Substring match: confidence >= 0.75 for single match
- [ ] LLM fallback triggers when confidence < 0.6 (qwen3:8b, <500ms)
- [ ] Human escalation triggers when confidence < 0.6 after LLM fallback
- [ ] Magic Link classification resolves within 5-min TTL
- [ ] Timeout fallback: LLM's best guess with "unconfirmed" flag
- [ ] 20 total eval cases (15 previous + 5 routing) all passing
- [ ] 950+ test suite green, 0 regressions

**Stretch criteria (3)**:
- [ ] Routing accuracy dashboard on Gateway Dashboard
- [ ] Escalation rate < 5% of total queries (most resolved by substring or LLM)
- [ ] Human classification data exported for future model fine-tuning

---

## Risk Assessment

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| LLM fallback adds latency (>500ms) | P1 — slower routing | Medium | qwen3:8b is fastest model (60-80 tok/s), timeout at 1s |
| Human escalation overload | P2 — reviewer fatigue | Low | Target <5% escalation rate; auto-timeout after 5 min |
| Confidence scoring breaks existing routing | P0 — regression | Low | All existing tests must pass; confidence is additive (doesn't change routing logic) |
| Magic Link spam (many low-confidence queries) | P2 — reviewer notification flood | Low | Rate limit: max 5 escalations/min per user, batch notifications |

---

## Dependencies

- **Sprint 203 complete**: Evaluator-Optimizer + 15 eval cases + baseline established
- **qwen3:8b model**: Must be loaded on Ollama (fastest classification model)
- **magic_link_service.py**: Existing service (313 LOC) — needs classification payload type
- **query_classifier.py**: Existing classifier (Sprint 179, ADR-058 Pattern E) — MODIFY, not rewrite
- **Master plan reference**: CTO-approved Anthropic Best Practices — Gap 3 (P3)

---

## Anthropic Best Practices Reference

| Gap | PDF Chapter | Pattern | Implementation |
|-----|------------|---------|----------------|
| Gap 3 (P3) | Ch 3 | Routing — Confidence scores | Track A: confidence field + scoring rules |
| Gap 3 (P3) | Ch 3 | Routing — LLM-based classification | Track A: qwen3:8b fallback for ambiguous queries |
| Gap 3 (P3) | Ch 3 | Routing — Human escalation | Track B: Magic Link classification via Telegram |

---

## Post-Sprint 204: Anthropic Roadmap Completion Status

```yaml
Completed Gaps (Sprint 202-204):
  ✅ Gap 5 (P0): Automated Evals — 20 test cases, multi-judge, CI regression detection
  ✅ Gap 1 (P1): Context Engineering — agent_notes, save_note/recall_note, dynamic loading
  ✅ Gap 2 (P2): Evaluator-Optimizer — rubric scoring, iteration limits, multi-judge
  ✅ Gap 3 (P3): Confidence Routing — confidence scores, LLM fallback, human escalation

Deferred Gaps:
  ⏳ Gap 4 (P4): SKILL.md Standard — Sprint 205+, defer (DB approach adequate)
  ⏳ Gap 6 (P4): Prompt Injection Depth — Sprint 206+, ENTERPRISE only

Total LOC across Sprint 202-204: ~2,001 (vs ~590 estimated — expanded scope justified by eval expansion)

Next: Sprint 205+ — Vietnam SME Pilot execution OR SKILL.md standard (CTO decision)
```

---

**Last Updated**: February 23, 2026
**Created By**: PM + AI Development Partner — Sprint 204 Planning (Anthropic Best Practices Roadmap)
**Framework Version**: SDLC 6.1.1
**Previous State**: Sprint 203 PLANNED
**Source**: CTO-approved Applicability Analysis (9.2/10, Feb 23 2026)
