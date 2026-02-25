---
sdlc_version: "6.1.1"
document_type: "Integration Guide"
status: "PROPOSED"
sprint: "176-206"
spec_id: "IG-056"
tier: "PROFESSIONAL"
stage: "03 - Integration"
references:
  - ADR-056
  - ADR-066
  - FR-045
  - FR-046
---

# Multi-Agent Team Engine — Provider & OTT Integration Guide

**Status**: PROPOSED (Sprint 176-206)
**Date**: February 2026
**Author**: CTO Nguyen Quoc Huy
**Framework**: SDLC 6.1.1
**References**: ADR-056 (Decision 3: Provider Profile Key), ADR-066 (LangChain Multi-Agent Orchestration), EP-07

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

**Direct providers** (default, `LANGCHAIN_ENABLED=false`):
```
Request → Ollama (Primary, $50/mo)
            │ timeout/rate_limit
            └──> Claude (Fallback 1, $1000/mo)
                    │ timeout/rate_limit
                    └──> Rule-based (Final, $0/mo)
```

**LangChain-wrapped providers** (Sprint 205, `LANGCHAIN_ENABLED=true`, `provider=langchain`):
```
Request → _call_langchain()
            │
            ├── ChatOllama (Primary, $50/mo)
            │     │ timeout/rate_limit
            │     └──> ChatAnthropic (Fallback 1, $1000/mo)
            │            │ timeout/rate_limit
            │            └──> ChatOpenAI (Fallback 2)
            │
            └── Same abort matrix (§1.3), same cooldown keys (§1.4)
```

> **ADR-066 D-066-01**: LangChain is PROVIDER ONLY — cannot become SSOT, cannot bypass control plane. Postgres is TRUTH; LangGraph state is DRAFT.

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

## 6. LangChain Provider Integration (Sprint 205 — ADR-066)

### 6.1 Feature Flag

```yaml
Config Key: LANGCHAIN_ENABLED
Default: false
Scope: Feature-flagged — zero behavior change when disabled
Config Key: LANGCHAIN_DEFAULT_MODEL
Default: "qwen3-coder:30b"
```

When `LANGCHAIN_ENABLED=true`, agents with `provider="langchain"` in their `agent_definitions` record route through `_call_langchain()` in `agent_invoker.py._call_provider()` (line 327).

### 6.2 Optional Dependency Guard

LangChain packages are **optional** — the system MUST start and pass all existing tests without them installed.

```python
# langchain_provider.py — module-level guard
try:
    from langchain_community.chat_models import ChatOllama
    from langchain_anthropic import ChatAnthropic
    from langchain_openai import ChatOpenAI
    _LANGCHAIN_AVAILABLE = True
except ImportError:
    _LANGCHAIN_AVAILABLE = False
    ChatOllama = None     # type: ignore[assignment]
    ChatAnthropic = None  # type: ignore[assignment]
    ChatOpenAI = None     # type: ignore[assignment]
```

Required packages (in `backend/requirements/enterprise.txt`):

| Package | Version | License | Purpose |
|---------|---------|---------|---------|
| `langchain-anthropic` | >=0.3.0 | MIT | ChatAnthropic wrapper |
| `langchain-openai` | >=0.3.0 | MIT | ChatOpenAI wrapper |
| `langchain-community` | >=0.3.0 | MIT | ChatOllama wrapper |
| `langgraph` | >=0.2.0 | MIT | Durable workflow graphs (Sprint 206) |

### 6.3 LangChain Provider Wrappers

| Wrapper | Backend Provider | Model Key | Use Case |
|---------|-----------------|-----------|----------|
| `ChatOllama` | Ollama REST API | `ollama:local:vietnam:qwen3-coder` | Primary code generation |
| `ChatAnthropic` | Anthropic Messages API | `anthropic:team-alpha:us-east-1:claude-sonnet` | Fallback reasoning |
| `ChatOpenAI` | OpenAI Chat API | `openai:default:global:gpt-4o` | Fallback generation |

```python
# langchain_provider.py — wrapper initialization
def create_langchain_model(profile_key: str) -> BaseChatModel:
    provider, account, region, model_family = profile_key.split(":")

    if provider == "ollama":
        return ChatOllama(
            base_url="http://api.nhatquangholding.com:11434",
            model=f"{model_family}",
            temperature=0.7,
            num_predict=4096,
        )
    elif provider == "anthropic":
        return ChatAnthropic(
            model="claude-sonnet-4-5-20250929",
            api_key=settings.ANTHROPIC_API_KEY,
            max_tokens=4096,
        )
    elif provider == "openai":
        return ChatOpenAI(
            model="gpt-4o",
            api_key=settings.OPENAI_API_KEY,
            max_tokens=4096,
        )
    else:
        raise ValueError(f"Unsupported LangChain provider: {provider}")
```

### 6.4 Structured Output

LangChain's `with_structured_output()` replaces regex-based parsing:

```python
from pydantic import BaseModel

class AgentResponse(BaseModel):
    content: str
    tool_calls: list[dict] = []
    confidence: float = 0.0

model = create_langchain_model(profile_key)
structured_model = model.with_structured_output(AgentResponse)
result: AgentResponse = await structured_model.ainvoke(messages)
```

### 6.5 Tool Calling via StructuredTool

5 tools registered via `langchain_tool_registry.py`:

| Tool Name | Description | Auth Required |
|-----------|-------------|---------------|
| `gate_status` | Check gate status for a project | `read:gates` |
| `submit_evidence` | Upload evidence to Evidence Vault | `write:evidence` |
| `read_file` | Read file from workspace | `read:files` (workspace-restricted) |
| `run_tests` | Execute test suite | `execute:tests` |
| `code_review` | Submit code for review | `write:reviews` |

```python
# langchain_tool_registry.py
from langchain_core.tools import StructuredTool

gate_status_tool = StructuredTool.from_function(
    func=gate_status_handler,
    name="gate_status",
    description="Check the current status of a quality gate",
    args_schema=GateStatusInput,
)

# Bind tools to model
model_with_tools = model.bind_tools([gate_status_tool, ...])
```

**Authorization guard** — ALL tool calls pass through `authorize_tool_call()` in `tool_context.py`:

```python
async def authorize_tool_call(
    tool_name: str,
    agent_definition: AgentDefinition,
    conversation: AgentConversation,
) -> bool:
    """Verify agent has permission to call this tool.
    Checks agent_definition.tool_permissions JSON array.
    Returns False if tool not in allowed list."""
    allowed = agent_definition.tool_permissions or []
    return tool_name in allowed
```

### 6.6 Token Counting

LangChain callback for automatic token tracking:

```python
from langchain_core.callbacks import BaseCallbackHandler

class TokenCountCallback(BaseCallbackHandler):
    def on_llm_end(self, response, **kwargs):
        usage = response.llm_output.get("token_usage", {})
        # Update conversation budget tracking
        # conversation_tracker.update_budget(
        #     input_tokens=usage.get("prompt_tokens", 0),
        #     output_tokens=usage.get("completion_tokens", 0),
        # )
```

tiktoken fallback for providers that don't report token counts (e.g., Ollama without native counting).

### 6.7 LangChain Exception Mapping

Added to `failover_classifier.py`:

| LangChain Exception | FailoverReason | Action |
|-------------------|---------------|--------|
| `AuthenticationError` | auth | ABORT |
| `RateLimitError` | rate_limit | FALLBACK |
| `BadRequestError` | format | RETRY |
| `InternalServerError` | unknown | ABORT |
| `APITimeoutError` | timeout | FALLBACK |
| `OutputParserException` | format | RETRY |

---

## 7. LangGraph Workflow Integration (Sprint 206 — ADR-066)

### 7.1 Dependencies

| Package | Version | Purpose |
|---------|---------|---------|
| `langgraph` | >=0.2.0 | StateGraph, async workflow orchestration |
| PostgreSQL | 15.5 | Checkpoint storage via `metadata_` JSONB |
| Redis | 7.2 | Pub/sub for fast workflow resume |

### 7.2 Workflow State in metadata_ JSONB

Workflow state is stored in `agent_conversations.metadata_` (existing JSONB column):

```python
class WorkflowMetadata(BaseModel):
    workflow_schema_version: str = "1.0.0"
    workflow_id: UUID
    workflow_type: Literal["reflection"]
    status: Literal["waiting", "running", "completed", "failed"]
    current_node: str
    iteration: int = 0
    max_iterations: int = 3
    next_wakeup_at: Optional[datetime] = None
    idempotency_keys: dict[str, str] = {}
    version: int = 1  # OCC — increment on every write
    state: dict = {}  # LangGraph node output

    @validator("state")
    def validate_size(cls, v):
        import json
        if len(json.dumps(v).encode()) > 65536:  # 64KB
            raise ValueError("Workflow state exceeds 64KB limit")
        return v
```

**JSONB constraints**:
- 64KB size validation before write
- Pydantic validation on ALL reads/writes
- Store pointers not payloads (reference `agent_messages.id`, not full content)
- Partial index: `CREATE INDEX ix_metadata_workflow ON agent_conversations ((metadata_->>'status'), ((metadata_->>'next_wakeup_at')::timestamptz)) WHERE metadata_->>'workflow_id' IS NOT NULL`

### 7.3 Reflection Graph (Coder → Reviewer Loop)

```
┌─────────┐     ┌──────────┐     ┌──────────┐
│  START   │────>│  Coder   │────>│ Reviewer  │
└─────────┘     │  Node    │     │   Node    │
                └──────────┘     └──────────┘
                     ↑                │
                     │          ┌─────┴─────┐
                     │          │ Decision  │
                     │          │   Node    │
                     │          └─────┬─────┘
                     │                │
                     │     ┌──────────┴──────────┐
                     │     │                     │
                     └─ RETRY              APPROVE/FAIL
                    (iteration < 3)     (iteration >= 3 or pass)
```

All graph nodes use `enqueue_async()` — returns immediately, NEVER blocks. Lane queue SKIP LOCKED preserved.

**Control plane refresh** at decision node:
```python
# Before every decision: refresh from control plane
response = await http_client.get(f"/gates/{gate_id}/actions")
actions = response.json()
# Decision node uses fresh gate actions, not stale LangGraph state
```

### 7.4 WorkflowResumer Service

Separate Docker service (`replicas: 1`), NOT in `main.py`:

```yaml
# docker-compose.yml
workflow_resumer:
  build: .
  command: python -m workflow_resumer
  replicas: 1
  depends_on:
    - db
    - redis
  environment:
    - DATABASE_URL=${DATABASE_URL}
    - REDIS_URL=${REDIS_URL}
  healthcheck:
    test: ["CMD", "python", "-c", "import sys; sys.exit(0)"]
    interval: 30s
    timeout: 10s
    retries: 3
```

**Dual-path resume**:

| Path | Mechanism | Latency | Reliability |
|------|-----------|---------|-------------|
| Fast | Redis pub/sub listener | <100ms | Best-effort (events can be lost) |
| Fallback | Reconciler polling 30s | ≤30s | Durable (queries DB directly) |

**Stuck detection**: Workflows with `status="waiting"` and `next_wakeup_at` > 5 minutes ago are auto-resumed by the reconciler.

**OCC (Optimistic Concurrency Control)**: Concurrent resume attempts → 1 succeeds, 1 gets version conflict (no-op).

```python
# workflow_resumer.py — OCC pattern
async def resume_workflow(conversation_id: UUID):
    conv = await db.get(AgentConversation, conversation_id)
    metadata = WorkflowMetadata(**conv.metadata_)

    current_version = metadata.version
    metadata.version += 1
    metadata.status = "running"

    result = await db.execute(
        update(AgentConversation)
        .where(
            AgentConversation.id == conversation_id,
            AgentConversation.metadata_["version"].as_integer() == current_version,
        )
        .values(metadata_=metadata.dict())
    )
    if result.rowcount == 0:
        logger.info("OCC conflict — another resumer already picked up this workflow")
        return  # No-op
```

### 7.5 End-to-End Idempotency (3 Layers)

| Layer | Key | Scope | Storage |
|-------|-----|-------|---------|
| 1. Workflow step | `(workflow_id, step_id)` | Prevent duplicate node execution | `WorkflowMetadata.idempotency_keys` |
| 2. Message enqueue | `idempotency_key` param | Prevent duplicate message enqueue | `agent_messages.idempotency_key` (UNIQUE) |
| 3. Control plane | `X-Idempotency-Key` header | Prevent duplicate API calls | Redis IdempotencyStore (1hr TTL) |

### 7.6 API Endpoints (Sprint 206)

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/api/v1/workflows/reflection` | Start a new reflection workflow |
| `GET` | `/api/v1/workflows/{id}/status` | Get workflow status + current node |
| `POST` | `/api/v1/workflows/{id}/approve` | Human approval at decision node |

All endpoints require JWT authentication + `write:workflows` scope.

---

## 8. Migration Guide: Direct Providers → LangChain

### 8.1 When to Migrate

| Scenario | Use Direct Provider | Use LangChain |
|----------|-------------------|---------------|
| Simple chat | ✅ | ❌ |
| Structured output needed | ❌ | ✅ |
| Tool calling | ❌ | ✅ |
| Reflection workflows | ❌ | ✅ |
| Feature flag disabled | ✅ (forced) | ❌ (unavailable) |

### 8.2 Migration Steps

1. **Set feature flag**: `LANGCHAIN_ENABLED=true` in environment
2. **Install packages**: `pip install -r backend/requirements/enterprise.txt`
3. **Update agent definition**: Set `provider="langchain"` in the agent's `agent_definitions` record
4. **Configure model**: Set `LANGCHAIN_DEFAULT_MODEL` (default: `qwen3-coder:30b`)
5. **Verify tools**: Ensure `tool_permissions` array includes allowed LangChain tools
6. **Test**: Run `python -m pytest backend/tests/unit/test_langchain_provider.py -v`

### 8.3 Rollback

Set `LANGCHAIN_ENABLED=false` → all agents revert to direct provider calls. Zero impact on existing behavior.

### 8.4 ADR-064 Exemption

Per ADR-066 Section 4:
> "D-064-02 'NOT LangChain' applies to chat-first facade only. Multi-agent orchestration (EP-07) may use LangChain under ADR-066."

LangChain CANNOT replace the chat router (ADR-064 D-064-02). LangChain CAN be used as a provider plugin and workflow graph engine within EP-07 scope only.

---

## 9. Testing Integration

```bash
# Provider failover integration test (existing)
DATABASE_URL="postgresql://test:test@localhost:15432/sdlc_test" \
  python -m pytest backend/tests/integration/ -k "failover" -v

# OTT integration test (requires Telegram bot token)
OTT_TELEGRAM_TOKEN="test-token" \
  python -m pytest backend/tests/integration/ -k "ott" -v

# Full multi-agent E2E
DATABASE_URL="postgresql://test:test@localhost:15432/sdlc_test" \
  python -m pytest backend/tests/e2e/ -k "multi_agent" -v

# Sprint 205: LangChain provider tests
LANGCHAIN_ENABLED=true \
  python -m pytest backend/tests/unit/test_langchain_provider.py -v

# Sprint 205: LangChain tool tests
LANGCHAIN_ENABLED=true \
  python -m pytest backend/tests/unit/test_langchain_tools.py -v

# Sprint 206: Reflection graph tests
python -m pytest backend/tests/unit/test_reflection_graph.py -v

# Sprint 206: WorkflowResumer tests
python -m pytest backend/tests/unit/test_workflow_resumer.py -v

# Sprint 206: Idempotency tests
python -m pytest backend/tests/unit/ -k "idempotency" -v

# Regression: all existing tests pass with LangChain disabled
LANGCHAIN_ENABLED=false \
DATABASE_URL="postgresql://test:test@localhost:15432/sdlc_test" \
  python -m pytest backend/tests/ -v --tb=short

# Crash recovery (manual — Sprint 206)
# 1. Start workflow: POST /api/v1/workflows/reflection
# 2. Kill resumer: docker stop workflow_resumer
# 3. Restart resumer: docker start workflow_resumer
# 4. Verify: GET /api/v1/workflows/{id}/status → resumed from checkpoint
```
