# Sprint 198 — OTT Gateway Dashboard + Bidirectional AI + Go-Live Validation

**Sprint Duration**: February 24 – March 7, 2026 (10 working days)
**Sprint Goal**: Build web-based OTT Gateway Dashboard (OpenClaw-inspired), implement bidirectional AI response loop (Telegram → Ollama → Telegram), and resolve Sprint 197 carry-forwards
**Status**: PLANNED
**Priority**: P0 (OTT Real Integration + Go-Live)
**Framework**: SDLC 6.1.1
**CTO Score (Sprint 197)**: 9.3/10
**Previous Sprint**: [Sprint 197 COMPLETE — Master Test Plan + Technical Debt + Go-Live Prep](SPRINT-197.md)

---

## Sprint 198 Goal

Sprint 197 delivered 7/7 technical debt items and 676 tests (9.3/10) but deferred 3 carry-forwards (env var endpoints, auth timeouts, Master Test Plan). Meanwhile, the OTT Telegram bot is live with basic command auto-reply (/start, /help, /status) — but lacks the **bidirectional AI response loop** and the **web-based Gateway Dashboard** that operators need for channel management.

**CEO directive**: OTT bots serve as **Human Coach (SE4H)** interfaces for AI-human governance interaction. The Gateway Dashboard enables platform admins to monitor and manage all OTT channels from the web app.

**Four pillars**:
1. **OTT Gateway Dashboard** — Web-based admin UI for OTT channel monitoring (OpenClaw-inspired)
2. **Bidirectional AI Loop** — Message → Ollama AI → Telegram reply (SE4H Human Coach pattern)
3. **Carry-Forward Resolution** — CF-01/02/03 from Sprint 197
4. **OTT Integration Testing** — E2E validation of real Telegram bot + AI response flow

**Conversation-First** (CEO directive Sprint 190): All sprint governance flows through OTT+CLI. Web App = admin-only. Gateway Dashboard = admin monitoring tool.

---

## Sprint 198 Backlog

### Track A — OTT Gateway Dashboard: Web App (Day 1-5) — @pm

**Goal**: Build an OpenClaw-inspired Gateway Dashboard at `/app/ott-gateway` for platform admins to monitor OTT channels, view conversations, and manage channel configuration.

**Design Reference**: OpenClaw Gateway at `localhost:18789` — adapted for SDLC Orchestrator's Next.js + shadcn/ui stack.

#### A1 — Backend: Gateway Admin API (~200 LOC)

| ID | Item | Priority | Deliverable |
|----|------|----------|-------------|
| A-01 | `GET /api/v1/admin/ott-channels/stats` | P1 | Channel summary: enabled channels, conversation counts, dedup rates |
| A-02 | `GET /api/v1/admin/ott-channels/{channel}/health` | P1 | Per-channel health: last webhook, error count 24h, avg latency |
| A-03 | `GET /api/v1/admin/ott-channels/{channel}/conversations` | P2 | Paginated conversation list from specific channel |
| A-04 | `POST /api/v1/admin/ott-channels/{channel}/test-webhook` | P2 | Send test webhook to verify channel connectivity |
| A-05 | `GET /api/v1/admin/ott-channels/config` | P1 | Channel configuration (secrets masked, webhook URL, tier mapping) |

**New file**: `backend/app/api/routes/admin_ott.py` (~200 LOC)
**Integration**: Queries `agent_conversations` + `agent_messages` with `initiator_type='ott_channel'` filter

#### A2 — Frontend: Gateway Dashboard Page (~400 LOC)

| ID | Item | Priority | Deliverable |
|----|------|----------|-------------|
| A-06 | `/app/ott-gateway/page.tsx` — Main dashboard | P1 | Channel status cards (4 channels), webhook stats, conversation feed |
| A-07 | Channel status cards component | P1 | Per-channel: status pill (online/configured/offline), last message, webhook URL |
| A-08 | Conversation viewer component | P2 | Real-time conversation list with channel filter, sender, timestamp |
| A-09 | Webhook log viewer component | P2 | Recent webhook payloads with status codes, latency, dedup indicator |
| A-10 | Channel config panel (admin-only) | P2 | View/test channel configuration (HMAC secrets masked, tier display) |
| A-11 | Sidebar navigation entry | P1 | Add "OTT Gateway" to admin section of Sidebar.tsx |

**New files**:
- `frontend/src/app/app/ott-gateway/page.tsx`
- `frontend/src/components/ott-gateway/ChannelStatusCard.tsx`
- `frontend/src/components/ott-gateway/ConversationFeed.tsx`
- `frontend/src/components/ott-gateway/WebhookLogViewer.tsx`
- `frontend/src/hooks/useOttGateway.ts`

**Design**: 4-column grid of channel cards (Telegram/Zalo/Teams/Slack) → below: tabbed view (Conversations | Webhooks | Config)

---

### Track B — Bidirectional AI Response Loop (Day 2-6) — @pm

**Goal**: Implement the SE4H Human Coach pattern where any non-command Telegram message triggers an AI-powered response via Ollama, enabling natural conversation between human coach and AI governance assistant.

**Architecture** (adapted from TinySDLC file-queue pattern for cloud):
```
User sends message on Telegram
        │
        ▼
OTT Gateway (ott_gateway.py) — receives webhook
        │
        ├──→ [command?] → telegram_responder.py (existing /start, /help, /status)
        │
        └──→ [free text] → ai_response_handler.py (NEW)
                │
                ▼
        OllamaService.chat() — qwen3:32b (Vietnamese, primary)
                │
                ▼
        telegram_responder.send_reply() — back to Telegram
```

| ID | Item | Priority | Deliverable |
|----|------|----------|-------------|
| B-01 | `ai_response_handler.py` — Ollama AI response service | P0 | Message → Ollama chat → formatted reply text |
| B-02 | System prompt for SE4H Human Coach role | P1 | Governance-aware prompt: sprint context, gate status, SDLC 6.1.1 rules |
| B-03 | Ollama integration for OTT responses | P0 | Use existing `ollama_service.py` with `qwen3:32b` (Vietnamese excellent) |
| B-04 | Response routing in `ott_gateway.py` | P0 | Non-command messages → AI handler (fire-and-forget, same pattern as auto-reply) |
| B-05 | Conversation context (Redis session) | P1 | Per-chat_id session with last 10 messages for context continuity |
| B-06 | Typing indicator during AI processing | P2 | Send `sendChatAction: typing` while Ollama processes |
| B-07 | Fallback on Ollama timeout/error | P1 | Graceful fallback message: "AI is processing, please try again" |
| B-08 | Rate limiting per user (Redis) | P1 | Max 10 AI requests/min per chat_id (prevent abuse) |

**New file**: `backend/app/services/agent_bridge/ai_response_handler.py` (~250 LOC)

**System Prompt** (SE4H Human Coach):
```
You are the SDLC Orchestrator governance assistant, acting as a Human Coach (SE4H).
You help team members with sprint management, quality gates, evidence submission,
and SDLC 6.1.1 compliance. You respond in Vietnamese (default) or English.
You have access to: current sprint status, gate results, team composition.
Keep responses concise (< 500 chars). Use emoji sparingly.
```

---

### Track C — Carry-Forward Resolution (Day 3-7) — @pm

| ID | Item | Source | Priority | Status |
|----|------|--------|----------|--------|
| C-01 | Fix missing env var endpoints (~5 endpoints) | CF-01 (Sprint 197 B-02) | P1 | PENDING |
| C-02 | Fix DB/service dependency failures (~8 endpoints) | CF-01 (Sprint 197 B-03) | P1 | PENDING |
| C-03 | Fix auth timeout endpoints (~3 endpoints) | CF-02 (Sprint 197 B-04) | P2 | PENDING |
| C-04 | Re-run E2E API test suite | CF-02 (Sprint 197 B-05) | P0 | PENDING |
| C-05 | Master Test Plan documentation | CF-03 (Sprint 197 Track A) | P2 | PENDING — @tester |

**Acceptance criteria**:
- [ ] Missing env var endpoints return 503 with actionable error (not 500)
- [ ] DB fixture issues resolved for affected test suites
- [ ] Auth timeout < 5s (register, forgot-password)
- [ ] New E2E API report generated with >97% health
- [ ] MASTER-TEST-PLAN.md created (Track A deferred items)

---

### Track D — OTT Integration Testing + Staging Validation (Day 7-10) — @pm

| ID | Item | Priority | Deliverable |
|----|------|----------|-------------|
| D-01 | Telegram bidirectional E2E test (real bot) | P0 | Send message → AI reply → verify on Telegram |
| D-02 | Auto-reply E2E tests (26 existing + 10 new) | P1 | All /start, /help, /status commands → correct responses |
| D-03 | Gateway Dashboard integration test | P1 | Dashboard loads, shows channel status, displays conversations |
| D-04 | Ollama → Telegram latency benchmark | P2 | Measure: message received → AI response sent (target <15s) |
| D-05 | Rate limiting validation | P1 | Verify 10 req/min per user, 11th request gets throttle message |
| D-06 | Docker compose staging validation | P0 | Full stack up: backend + frontend + Telegram bot + Ollama |
| D-07 | Sprint 198 close documentation | P1 | G-Sprint-Close within 24h |

---

## Architecture: OTT Gateway Dashboard

### Backend API Architecture

```
┌──────────────────────────────────────────────────────────┐
│ /api/v1/admin/ott-channels/*  (NEW — admin_ott.py)       │
│                                                          │
│  GET  /stats          → aggregate channel metrics        │
│  GET  /{channel}/health → per-channel health check       │
│  GET  /{channel}/conversations → channel conversations   │
│  POST /{channel}/test-webhook → connectivity test        │
│  GET  /config         → all channels configuration       │
│                                                          │
│  Security: requires is_platform_admin OR project owner   │
│  Data: queries agent_conversations + agent_messages      │
└──────────────────────────────────────────────────────────┘
```

### Frontend Dashboard Layout

```
┌─────────────────────────────────────────────────────────┐
│ OTT Gateway Dashboard                         [Admin]   │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐     │
│  │Telegram │ │  Zalo   │ │  Teams  │ │  Slack  │     │
│  │ ● Online│ │○ Config │ │○ Config │ │○ Config │     │
│  │ 87 msgs │ │  0 msgs │ │  0 msgs │ │  0 msgs │     │
│  │ <2s avg │ │   ---   │ │   ---   │ │   ---   │     │
│  └─────────┘ └─────────┘ └─────────┘ └─────────┘     │
│                                                         │
│  ┌─ Conversations ─┬─ Webhooks ─┬─ Config ─┐          │
│  │                  │            │          │          │
│  │  [Tai Dang]     │            │          │          │
│  │  "Xin chào"    │            │          │          │
│  │  2 min ago     │            │          │          │
│  │                │            │          │          │
│  │  [Tai Dang]    │            │          │          │
│  │  /help         │            │          │          │
│  │  5 min ago     │            │          │          │
│  │                │            │          │          │
│  └─────────────────┴────────────┴──────────┘          │
└─────────────────────────────────────────────────────────┘
```

### Bidirectional AI Flow

```
  Telegram User                SDLC Backend               Ollama
       │                           │                        │
       │── "Tình trạng sprint?" ──>│                        │
       │                           │── normalize ──>        │
       │                           │── check command? NO    │
       │                           │── ai_response_handler  │
       │                           │── typing indicator ──> │
       │                           │                        │
       │                           │── chat(qwen3:32b) ───>│
       │                           │                        │
       │                           │<── "Sprint 198 đang   │
       │                           │     PLANNED, goal:     │
       │                           │     OTT Gateway..." ──│
       │                           │                        │
       │<── sendMessage reply ─────│                        │
       │                           │                        │
```

---

## Files Summary

| File | Action | LOC | Phase |
|------|--------|-----|-------|
| `backend/app/api/routes/admin_ott.py` | NEW | ~200 | Track A |
| `backend/app/main.py` | MODIFY | ~5 | Track A (register router) |
| `backend/app/middleware/tier_gate.py` | MODIFY | ~3 | Track A (add admin route) |
| `frontend/src/app/app/ott-gateway/page.tsx` | NEW | ~150 | Track A |
| `frontend/src/components/ott-gateway/ChannelStatusCard.tsx` | NEW | ~80 | Track A |
| `frontend/src/components/ott-gateway/ConversationFeed.tsx` | NEW | ~100 | Track A |
| `frontend/src/components/ott-gateway/WebhookLogViewer.tsx` | NEW | ~70 | Track A |
| `frontend/src/hooks/useOttGateway.ts` | NEW | ~60 | Track A |
| `frontend/src/components/dashboard/Sidebar.tsx` | MODIFY | ~5 | Track A |
| `backend/app/services/agent_bridge/ai_response_handler.py` | NEW | ~250 | Track B |
| `backend/app/api/routes/ott_gateway.py` | MODIFY | ~20 | Track B (add AI routing) |
| `backend/app/services/agent_bridge/telegram_responder.py` | MODIFY | ~30 | Track B (typing + send_reply) |
| Tests (unit + integration + E2E) | NEW | ~400 | Track C+D |
| **Total** | | **~1,400** | |

---

## Sprint 198 Success Criteria

- [ ] OTT Gateway Dashboard accessible at `/app/ott-gateway` (admin-only)
- [ ] 4 channel status cards showing Telegram (online), Zalo/Teams/Slack (configured)
- [ ] Conversation feed displays OTT conversations with channel filter
- [ ] Bidirectional AI: non-command Telegram messages get AI-powered replies via Ollama
- [ ] AI response latency < 15s (qwen3:32b on RTX 5090)
- [ ] Rate limiting: 10 AI requests/min per user enforced
- [ ] Typing indicator shown during AI processing
- [ ] Missing env var endpoints return 503 (not 500) — CF-01
- [ ] Auth timeout reduced to < 5s — CF-02
- [ ] E2E API test report generated with > 97% health — CF-02
- [ ] Sprint 198 test suite green (existing 676 + new tests)
- [ ] G-Sprint-Close within 24h of sprint end

---

## Risk Assessment

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| Ollama not reachable from Docker container | P0 — AI replies fail | Medium | `host.docker.internal:11434` + health check + fallback message |
| Gateway Dashboard adds complexity to admin UI | P2 — feature bloat | Low | Admin-only gating, clean tabbed interface |
| Rate limiting too aggressive | P1 — user frustration | Low | Start with 10/min, configurable via env var |
| AI response quality in Vietnamese | P1 — poor UX | Low | qwen3:32b tested excellent for Vietnamese; system prompt tuning |

---

## Dependencies

- **Ollama service**: Must be reachable at `OLLAMA_URL` (default: `http://host.docker.internal:11434`)
- **qwen3:32b model**: Must be loaded on Ollama server (primary chat model)
- **Redis**: Required for rate limiting, conversation sessions, webhook dedup
- **Telegram webhook**: Must be configured at `https://sdlc.nhatquangholding.com/api/v1/channels/telegram/webhook`
- **Frontend build**: Next.js 14.2.35, no new dependencies needed (shadcn/ui components sufficient)

---

## Previous Sprint Summary

### Sprint 197 — Master Test Plan + Technical Debt + Go-Live Prep (COMPLETE 9.3/10)

4-track delivery: B-01 prefix fix + TG-41, 7/7 tech debt items, 676 tests 0 regressions.

| Track | Deliverables | Tests |
|-------|-------------|-------|
| B | Double-prefix fix + TG-41 org-invitations exposure | — |
| C | 7/7 tech debt: ruff lint, singularization, Gate 4 env, benchmarks | 6 |
| D | 676 total tests, 0 regressions | 676 |
| A | Deferred → CF-03 (Master Test Plan @tester) | — |

**Full report**: [SPRINT-197.md](SPRINT-197.md)

---

**Last Updated**: February 23, 2026
**Created By**: PM + AI Development Partner — Sprint 198 Planning
**Framework Version**: SDLC 6.1.1
**Previous State**: Sprint 197 COMPLETE (CTO 9.3/10)
