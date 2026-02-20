---
sdlc_version: "6.0.6"
document_type: "Integration Guide"
status: "PROPOSED"
sprint: "176"
spec_id: "IG-056"
tier: "PROFESSIONAL"
stage: "03 - Integration"
---

# Multi-Agent Team Engine — Provider & OTT Integration Guide

**Status**: PROPOSED (Sprint 176)
**Date**: February 2026
**Author**: CTO Nguyen Quoc Huy
**Framework**: SDLC 6.1.0
**References**: ADR-056 (Decision 3: Provider Profile Key), EP-07

---

## 1. Provider Integration Architecture

### 1.1 Provider Profile Key Format

All AI providers are identified by a 4-field key: `{provider}:{account}:{region}:{model_family}`

| Example Key | Provider | Account | Region | Model |
|------------|----------|---------|--------|-------|
| `ollama:local:vietnam:qwen3-coder` | Ollama | local | vietnam | qwen3-coder |
| `anthropic:team-alpha:us-east-1:claude-sonnet` | Anthropic | team-alpha | us-east-1 | claude-sonnet |
| `openai:default:global:gpt-4o` | OpenAI | default | global | gpt-4o |

### 1.2 Failover Chain

```
Request → Ollama (Primary, $50/mo)
            │ timeout/rate_limit
            └──> Claude (Fallback 1, $1000/mo)
                    │ timeout/rate_limit
                    └──> Rule-based (Final, $0/mo)
```

### 1.3 Abort Matrix (Decision 3)

| Error Class | HTTP Codes | Action | Cooldown TTL |
|-------------|-----------|--------|-------------|
| auth | 401, 403 | ABORT | 300s |
| billing | 402 | ABORT | 600s |
| rate_limit | 429 | FALLBACK | 60s |
| timeout | 408, 504 | FALLBACK | 120s |
| format | 400 | RETRY (1x) | 0s |
| unknown | 500, other | ABORT | 0s |

### 1.4 Redis Cooldown Keys

```
cooldown:{provider}:{account}:{region}:{model_family}
```

Example: `cooldown:ollama:local:vietnam:qwen3-coder` with TTL 60s after rate_limit.

Workers MUST check cooldown key before invoking a provider. If key exists, skip to next provider in chain.

---

## 2. Ollama Integration (Primary Provider)

### 2.1 Connection

```yaml
Endpoint: http://api.nhatquangholding.com:11434
Protocol: REST API (Ollama native)
Auth: None (internal network)
Models:
  - qwen3-coder:30b (code generation, 256K context)
  - qwen3:32b (chat, Vietnamese)
  - deepseek-r1:32b (reasoning)
```

### 2.2 Agent Invoker Call

```python
# agent_invoker.py will use this pattern
POST /api/generate
{
  "model": "qwen3-coder:30b",
  "prompt": "{system_prompt}\n\n{conversation_history}\n\n{current_message}",
  "options": {
    "num_predict": 4096,
    "temperature": 0.7
  },
  "stream": false
}
```

### 2.3 Error Mapping

| Ollama Error | FailoverReason | Action |
|-------------|---------------|--------|
| Connection refused | timeout | FALLBACK |
| Model not found | format | RETRY |
| Context length exceeded | format | RETRY (with truncation) |
| GPU OOM | timeout | FALLBACK |

---

## 3. Anthropic Claude Integration (Fallback 1)

### 3.1 Connection

```yaml
Endpoint: https://api.anthropic.com/v1/messages
Protocol: REST API (Anthropic Messages API)
Auth: API key (X-API-Key header)
Model: claude-sonnet-4-5-20250929
Rate Limit: 50 RPM (team tier)
```

### 3.2 Error Mapping

| HTTP Code | FailoverReason | Action |
|-----------|---------------|--------|
| 401 | auth | ABORT |
| 429 | rate_limit | FALLBACK (cooldown 60s) |
| 529 | rate_limit | FALLBACK (overloaded) |
| 400 | format | RETRY |
| 500 | unknown | ABORT |

---

## 4. OTT Gateway Integration (P1 — Sprint 178)

### 4.1 Plugin Architecture

```
ott-gateway/
├── src/
│   ├── gateway.ts              # Gateway server + plugin registry
│   ├── plugin-loader.ts        # Dynamic plugin loading
│   ├── types.ts                # ChannelPlugin interface
│   └── plugins/
│       ├── telegram/           # Sprint 178 MVP
│       ├── discord/            # Sprint 179
│       └── zalo/               # Sprint 180
```

### 4.2 ChannelPlugin Interface

```typescript
interface ChannelPlugin {
  id: string;                    // "telegram", "discord", "zalo"
  connect(): Promise<void>;
  disconnect(): Promise<void>;
  sendMessage(to: string, content: string): Promise<void>;
  onMessage(handler: (msg: IncomingMessage) => void): void;
}
```

### 4.3 Message Flow (OTT → Orchestrator)

```
Telegram Bot → OTT Gateway → InputSanitizer → POST /api/v1/agent-team/conversations/{id}/messages
                                    │
                                    └── [EXTERNAL_INPUT channel=ott]{content}[/EXTERNAL_INPUT]
```

### 4.4 Security Requirements

1. All OTT input MUST pass through `InputSanitizer` (12 patterns)
2. Unknown senders require DM pairing approval
3. `status = "verified"` required in external_identities before delegation
4. OTT messages tagged with `[EXTERNAL_INPUT channel=ott]` wrapper

---

## 5. Existing Service Integration Points

### 5.1 Evidence Vault

- `agent_messages.evidence_id` FK → `gate_evidence.id`
- Auto-capture agent outputs as evidence via `evidence_collector.py`
- SHA256 integrity preserved

### 5.2 Gate Engine

- Conversation completion can trigger gate evaluation
- Agent outputs linked to gate exit criteria via evidence binding

### 5.3 WebSocket Manager

- P0: `WebSocketManager.broadcast` for agent events
- P1: Bridge EventBus → WebSocket → NotificationService

### 5.4 Redis

- Cooldown state: `cooldown:{profile_key}` with TTL
- Budget tracking: `INCRBY` for real-time cost
- Pub/sub: Lane queue notification (with 5s DB polling fallback)

---

## 6. Testing Integration

```bash
# Provider failover integration test
DATABASE_URL="postgresql://test:test@localhost:15432/sdlc_test" \
  python -m pytest backend/tests/integration/ -k "failover" -v

# OTT integration test (requires Telegram bot token)
OTT_TELEGRAM_TOKEN="test-token" \
  python -m pytest backend/tests/integration/ -k "ott" -v

# Full multi-agent E2E
DATABASE_URL="postgresql://test:test@localhost:15432/sdlc_test" \
  python -m pytest backend/tests/e2e/ -k "multi_agent" -v
```
