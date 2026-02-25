# Sprint 200 — Full Agent Team Orchestration via OTT

**Sprint Duration**: March 24 – April 4, 2026 (10 working days)
**Sprint Goal**: Activate multi-agent collaboration via OTT channels — Initializer → Coder → Reviewer pipeline accessible from Telegram/Zalo, with full budget circuit breakers and lane-based queue processing
**Status**: CLOSED (CTO 9.2/10) — Track A ✅, Track B ✅, Track C ✅, Track D ✅ (140/140 tests, 0 regressions)
**Priority**: P0 (Dogfooding 75% → 90%)
**Framework**: SDLC 6.1.1
**CTO Score (Sprint 199)**: TBD
**Previous Sprint**: [Sprint 199 — Chat Governance Actions + Evidence Upload via OTT](SPRINT-199-CHAT-GOVERNANCE-ACTIONS.md)

---

## Sprint 200 Goal

Sprint 199 delivers single-action governance commands (approve gate, upload evidence). Sprint 200 **activates the full Multi-Agent Team Engine** (EP-07, ADR-056) for OTT channels — enabling multi-agent collaboration where an Initializer agent decomposes tasks, a Coder agent generates code, and a Reviewer agent validates output, all orchestrated via OTT chat.

**Dogfooding level**: 75% → 90% — multi-agent governance orchestration via OTT.

**Three pillars**:
1. **Agent Team via OTT** — Multi-agent pipelines (Init → Code → Review) triggered from chat
2. **Budget + Observability** — Cost circuit breakers, token tracking, agent activity dashboard
3. **Cross-Channel Parity** — Telegram + Zalo + Teams + Slack all support agent team invocation

**ADR-056 Activation**: Sprint 176-179 built the backend (12 services, 3 tables, 14 non-negotiables). Sprint 200 makes it accessible to end users via OTT chat.

---

## Sprint 200 Backlog

### Track A — Agent Team OTT Integration (Day 1-5) — @pm

**Goal**: Connect OTT chat messages to the Multi-Agent Team Engine (`team_orchestrator.py`) so users can invoke agent teams from Telegram/Zalo.

**Architecture**:
```
User: "analyze my API spec and generate code"
    │
    ├─ ai_response_handler.py → detect multi-agent intent
    │
    ├─ team_orchestrator.py → create agent conversation
    │   ├─ Initializer agent → decompose task
    │   ├─ Coder agent → generate code (EP-06 pipeline)
    │   └─ Reviewer agent → validate output (4-Gate)
    │
    ├─ conversation_tracker.py → track progress, budget
    │
    └─ telegram_responder → stream progress updates to user
        ├─ "Initializer analyzing spec..."
        ├─ "Coder generating models..."
        ├─ "Reviewer: Gate 1 PASS, Gate 2 PASS..."
        └─ "Code generation complete. 3 files generated."
```

| ID | Item | Priority | Deliverable |
|----|------|----------|-------------|
| A-01 | OTT → Team Orchestrator bridge | P0 | Route multi-agent intents from `ai_response_handler` to `team_orchestrator.start_session()` |
| A-02 | Agent team selection via chat | P1 | "use coder team" / "use review team" → select from `team_presets.py` (5 presets) |
| A-03 | Progress streaming to OTT | P0 | Agent step completions → Telegram progress messages (non-blocking) |
| A-04 | Session interruption via chat | P1 | "stop" / "cancel" → `team_orchestrator.interrupt()` |
| A-05 | Result delivery via OTT | P0 | Generated code / review results → formatted Telegram message + optional file attachment |
| A-06 | Multi-turn agent conversation | P1 | User refinement: "change the model name" → agent continues from previous context |

**Key files (MODIFY)**:
- `backend/app/services/agent_bridge/ai_response_handler.py` — Add multi-agent intent detection
- `backend/app/services/agent_team/team_orchestrator.py` (776 LOC) — Add OTT session factory
- `backend/app/services/agent_team/conversation_tracker.py` (424 LOC) — OTT progress callbacks
- `backend/app/services/agent_bridge/telegram_responder.py` — Progress message streaming

**Acceptance criteria**:
- [ ] "generate code for user management" → Initializer + Coder + Reviewer pipeline runs
- [ ] Progress updates streamed to Telegram (step-by-step, not final-only)
- [ ] "stop" command interrupts running agent team within 5s
- [ ] Generated code delivered as Telegram file attachment (for large outputs)

---

### Track B — Budget Circuit Breakers + Observability (Day 3-6) — @pm

**Goal**: Enforce cost limits per conversation and per organization, with real-time observability in the Gateway Dashboard.

**Architecture** (ADR-056 Non-Negotiable #11 — Budget Control):
```
Agent conversation starts
    │
    ├─ conversation_tracker.budget_check()
    │   ├─ Per-conversation: max $5 / max 50K tokens
    │   ├─ Per-org monthly: LITE $10, STANDARD $50, PRO $200, ENTERPRISE $1000
    │   └─ Per-agent: configurable in agent_definitions.max_tokens
    │
    ├─ On budget exceeded:
    │   ├─ Soft limit (80%): Warning message to user
    │   └─ Hard limit (100%): Conversation paused + admin notification
    │
    └─ Dashboard: real-time token/cost counters per conversation
```

| ID | Item | Priority | Deliverable |
|----|------|----------|-------------|
| B-01 | Per-conversation budget enforcement | P0 | Max tokens + max cost per conversation (configurable) |
| B-02 | Per-organization monthly budget | P1 | Tier-based limits: LITE $10, STANDARD $50, PRO $200, ENTERPRISE $1000 |
| B-03 | Budget warning at 80% threshold | P1 | Telegram/OTT message: "80% of your budget used for this conversation" |
| B-04 | Hard stop at 100% budget | P0 | Conversation paused, admin notified, user informed |
| B-05 | Agent activity panel on Gateway Dashboard | P1 | Real-time: active conversations, token usage, cost per agent |
| B-06 | Cost attribution per provider | P2 | Track cost: Ollama ($0.001/1K tokens), Claude ($0.015/1K), etc. |

**Key files (MODIFY)**:
- `backend/app/services/agent_team/conversation_tracker.py` — Add budget enforcement hooks
- `backend/app/services/agent_team/agent_invoker.py` — Add per-call cost tracking
- `frontend/src/components/ott-gateway/AgentActivityPanel.tsx` — NEW (~120 LOC)

**Acceptance criteria**:
- [ ] Conversation pauses at budget limit with user-friendly message
- [ ] 80% warning sent via OTT before hard stop
- [ ] Gateway Dashboard shows real-time token/cost counters
- [ ] Cost tracked per provider (Ollama vs Claude vs Rule-based)

---

### Track C — Cross-Channel Agent Parity (Day 5-8) — @pm

**Goal**: Ensure agent team functionality works across all 4 OTT channels, not just Telegram.

| ID | Item | Priority | Deliverable |
|----|------|----------|-------------|
| C-01 | Zalo agent team support | P1 | Vietnamese agent conversations via Zalo OA |
| C-02 | Teams agent team support | P2 | Agent team invocation from Microsoft Teams |
| C-03 | Slack agent team support | P2 | Agent team invocation from Slack (via app_mention) |
| C-04 | Channel-specific response formatting | P1 | Telegram Markdown, Slack blocks, Teams adaptive cards, Zalo plain text |
| C-05 | Cross-channel session continuity | P2 | Start conversation on Telegram, continue on Zalo (same user_id mapping) |

**Acceptance criteria**:
- [ ] "generate code" works on Telegram AND Zalo
- [ ] Response formatting correct per channel (Markdown vs plain text)
- [ ] Teams and Slack functional for basic agent team commands

---

### Track D — E2E Testing + Sprint Close (Day 8-10) — @pm

| ID | Item | Priority | Deliverable |
|----|------|----------|-------------|
| D-01 | Multi-agent via Telegram E2E test | P0 | Trigger agent team → verify pipeline completion → check output |
| D-02 | Budget circuit breaker E2E test | P0 | Exceed budget → verify conversation paused + warning sent |
| D-03 | Cross-channel parity test (Telegram + Zalo) | P1 | Same command on both channels → same result |
| D-04 | Agent interruption E2E test | P1 | Start agent → send "stop" → verify interruption within 5s |
| D-05 | Regression test suite (750+ tests) | P0 | All Sprint 197-199 tests passing, 0 regressions |
| D-06 | Performance benchmark: agent pipeline latency | P2 | Init → Code → Review pipeline < 60s for simple spec |
| D-07 | Sprint 200 close documentation | P1 | G-Sprint-Close within 24h |

---

## Architecture: Multi-Agent OTT Integration

### Agent Team Pipeline via Chat

```
  Telegram User          AI Handler         Team Orchestrator        Agents
       │                    │                      │                    │
       │── "generate        │                      │                    │
       │    user CRUD" ────>│                      │                    │
       │                    │── detect intent       │                    │
       │                    │── multi_agent        │                    │
       │                    │                      │                    │
       │                    │── start_session() ──>│                    │
       │                    │                      │── select preset    │
       │                    │                      │   "coder_team"     │
       │                    │                      │                    │
       │<── "Starting       │                      │── Initializer ───>│
       │     Coder Team"    │                      │                    │── decompose
       │                    │                      │<── 3 sub-tasks ───│
       │<── "Analyzing      │                      │                    │
       │     spec: 3        │                      │── Coder ─────────>│
       │     sub-tasks"     │                      │                    │── generate
       │                    │                      │<── code files ────│
       │<── "Generating     │                      │                    │
       │     code: 3/3      │                      │── Reviewer ──────>│
       │     files done"    │                      │                    │── validate
       │                    │                      │<── Gate 1-3 PASS ─│
       │<── "Review          │                      │                    │
       │     complete:       │                      │                    │
       │     PASS 3/3        │                      │                    │
       │     Gates"          │                      │                    │
       │                    │                      │                    │
       │<── [file: code.zip]│                      │                    │
```

### Budget Circuit Breaker Flow

```
  Agent Invoker          Conversation Tracker         Redis
       │                        │                       │
       │── pre_invoke() ──────>│                       │
       │                        │── check budget       │
       │                        │── get token_count ──>│
       │                        │<── 45,000 tokens ───│
       │                        │                       │
       │                        │── 45K/50K = 90%      │
       │                        │── ABOVE 80% threshold │
       │                        │                       │
       │<── WARNING ───────────│                       │
       │                        │                       │
       │── post_invoke() ─────>│                       │
       │   (used 6,000 tokens)  │                       │
       │                        │── update: 51,000     │
       │                        │── 51K > 50K LIMIT    │
       │                        │── HARD STOP          │
       │                        │                       │
       │<── BUDGET_EXCEEDED ───│                       │
       │                        │                       │
       │── notify_user() ─────>│                       │
       │   "Budget exceeded"    │                       │
```

---

## Files Summary

| File | Action | LOC | Track |
|------|--------|-----|-------|
| `backend/app/services/agent_bridge/ai_response_handler.py` | MODIFY | ~100 | A (multi-agent intent) |
| `backend/app/services/agent_team/team_orchestrator.py` | MODIFY | ~120 | A (OTT session factory + progress) |
| `backend/app/services/agent_team/conversation_tracker.py` | MODIFY | ~80 | B (budget hooks) |
| `backend/app/services/agent_team/agent_invoker.py` | MODIFY | ~50 | B (per-call cost) |
| `backend/app/services/agent_bridge/telegram_responder.py` | MODIFY | ~60 | A (progress streaming) |
| `backend/app/services/agent_bridge/zalo_responder.py` | NEW | ~80 | C (Zalo response) |
| `frontend/src/components/ott-gateway/AgentActivityPanel.tsx` | NEW | ~120 | B |
| Tests (unit + integration + E2E) | NEW | ~500 | D |
| **Total** | | **~1,110** | |

---

## Sprint 200 Success Criteria

**Hard criteria (8)**:
- [ ] Multi-agent team invocable from Telegram chat (Init → Code → Review)
- [ ] Progress updates streamed to user during agent pipeline execution
- [ ] Budget circuit breaker: conversation pauses at limit
- [ ] Budget warning at 80% threshold via OTT message
- [ ] "stop" command interrupts agent team within 5s
- [ ] Agent team works on Telegram AND Zalo (cross-channel parity)
- [ ] 750+ test suite green, 0 regressions
- [ ] G-Sprint-Close within 24h

**Stretch criteria (3)**:
- [ ] Agent activity panel on Gateway Dashboard
- [ ] Teams/Slack agent team support
- [ ] Cross-channel session continuity (start on Telegram, continue on Zalo)

---

## Risk Assessment

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| Agent pipeline timeout (>60s) | P1 — poor UX | Medium | Stream progress, configurable timeout per agent, fallback to partial result |
| Budget enforcement race condition | P0 — cost overrun | Low | Atomic Redis INCRBY for token counting, pre-invoke check |
| Agent team hallucination in task decomposition | P1 — wrong sub-tasks | Medium | Pydantic validation on decomposed_tasks, user confirmation before execution |
| Cross-channel identity mapping | P2 — duplicate sessions | Low | Use email-based user_id resolution, not channel-specific IDs |

---

## Dependencies

- **Sprint 199 complete**: Gate actions + evidence upload via chat must be working
- **EP-07 backend**: 12 agent_team services (Sprint 176-179) — all exist, need OTT bridge
- **Team presets**: 5 presets in `team_presets.py` — Coder, Reviewer, Architect, QA, Full Team
- **EP-06 pipeline**: 4-Gate Quality Pipeline (430 tests) — Coder agent uses this for code generation
- **Ollama models**: `qwen3-coder:30b` (code), `qwen3:14b` (chat, default since Sprint 198), `deepseek-r1:32b` (reasoning) — per-agent model routing via `query_classifier.py`

---

**Last Updated**: February 23, 2026
**Created By**: PM + AI Development Partner — Sprint 200 Planning
**Framework Version**: SDLC 6.1.1
**Previous State**: Sprint 199 PLANNED
