# PHÂN TÍCH SDLC ORCHESTRATOR - MAS FOUNDATION

**Date**: 2026-02-23 | **Author**: AI Architect | **Format**: TOON

---

## 1. CORE CONCEPT

**Vision**: Operating System cho Software 3.0 — governance platform sits ABOVE AI coders

```
Software 3.0 Stack:
L5: AI Coders (Cursor, Claude Code, Copilot) ← External, we orchestrate
L4: EP-06 Codegen (IR-based code generation) ← Our innovation
L3: Business Logic (Gate Engine, Evidence Vault) ← Our core
L2: Integration (OPA, MinIO, Semgrep adapters) ← Thin adapters
L1: Infrastructure (PostgreSQL, Redis, OPA) ← OSS components
```

**Key Insight**: SDLC Orchestrator KHÔNG phải AI coder, mà là GOVERNANCE LAYER để:
- Enforce 4-Gate Quality Pipeline (Syntax → Security → Context → Tests)
- Evidence-based development (Evidence Vault với SHA256 integrity)
- Multi-agent collaboration với safety guardrails

---

## 2. EXISTING MULTI-AGENT ARCHITECTURE (ADR-056)

### 2.1 Production Patterns (3 codebases absorbed)

| Source | Tech | Scale | Patterns |
|--------|------|-------|----------|
| **OpenClaw** | Node.js, TypeScript | 36 channels, 50+ skills | Lane queue, failover (6 reasons), session scope |
| **TinyClaw** | Node.js, file queue | 6 SDLC roles | @mention routing, loop prevention (50 msg) |
| **Nanobot** | Python 3.11, LiteLLM | 3,663 LOC | Shell guard (8 patterns), tool context, reflect-after-tools |
| **ZeroClaw** | Rust | Agent runtime | Credential scrub (6 patterns), history compaction, env scrub |

### 2.2 4 Locked Architectural Decisions

```
D1. Snapshot Precedence — agent_definitions = templates, snapshot immutable on conversation start
D2. Lane Contract — DB truth, Redis notify-only, SKIP LOCKED + dead-letter + dedupe
D3. Provider Profile Key — {provider}:{account}:{region}:{model_family} + abort matrix (6 reasons)
D4. Canonical Protocol Owner — Orchestrator owns all message schemas
```

### 2.3 14 Non-Negotiables

**Security (6)**: Input sanitizer (12 patterns), shell guard (8 patterns), tool workspace restrict, credential scrub (6 patterns), env scrub (9 safe vars), 2FA OTT approval

**Architecture (5)**: Lane queue (includes dead-letter), snapshot precedence, loop guards (6 limits), read-only workspace, canonical protocol

**Observability (3)**: Identity audit, token budget circuit breaker, human-in-the-loop interrupt

---

## 3. DATABASE SCHEMA (3 tables)

```sql
-- Agent templates/defaults
agent_definitions (22 columns):
  id, project_id, team_id, agent_name, sdlc_role (12 roles),
  provider, model, system_prompt, working_directory,
  max_tokens, temperature, queue_mode (queue/steer/interrupt),
  session_scope (per-sender/global), max_delegation_depth,
  allowed_tools (JSONB), max_messages, max_budget_cents,
  auto_evidence_capture, correlation_id_prefix, created_at, ...

-- Conversation sessions (parent-child)
agent_conversations (19 columns):
  id, definition_id (FK), parent_conversation_id (FK), project_id,
  initiated_by, status, queue_mode (snapshotted), session_scope (snapshotted),
  token_count, cost_cents, max_budget_cents (snapshotted),
  message_count, max_messages (snapshotted), ...

-- Message queue (lane-based)
agent_messages (22 columns):
  id, conversation_id (FK), sender_id, content, role,
  processing_status (pending/processing/completed/failed/dead_letter),
  processing_lane (BTREE index), next_retry_at, retry_count,
  failover_reason (auth/format/rate_limit/billing/timeout/unknown),
  latency_ms, token_count, cost_cents, correlation_id, ...
```

**Key Indexes**:
- `idx_agent_messages_lane_processing` — (processing_status, processing_lane, next_retry_at) — lane queue SELECT FOR UPDATE SKIP LOCKED
- `idx_agent_conversations_parent` — (parent_conversation_id) — parent-child hierarchy
- `idx_agent_messages_correlation` — (correlation_id) — distributed tracing

---

## 4. SDLC WORKFLOW INTEGRATION

### 4.1 Quality Gates (SDLC 6.1.0)

```
G0.1: Foundation Ready (WHY stage) — Design Thinking artifacts
G0.2: Solution Diversity (WHY stage) — Alternatives evaluated
G1: Design Ready / Consultation (WHAT stage) — PRD + Architecture
G2: Security + Architecture (HOW stage) — Security scan + design review
G3: Ship Ready (BUILD stage) — Tests pass + code review
G4: Production Validation (DEPLOY stage) — Post-deployment health
```

**Agent Hook Points**:
- **G0.2 → G1 transition**: PM Agent gathers requirements via clarifying questions
- **G1 → G2 transition**: Architect Agent designs system architecture
- **G2 → G3 transition**: Coder Agent implements features, Reviewer Agent audits code
- **G3 → G4 transition**: DevOps Agent deploys, Tester Agent validates

### 4.2 EP-06 Codegen Pipeline

```
Input: BRD/PRD spec
  ↓
IR Processor → Intermediate Representation (deterministic)
  ↓
Multi-Provider Chain: Ollama ($50/mo) → Claude ($1K/mo) → Rule-based ($0)
  ↓
4-Gate Quality Pipeline:
  Gate 1: Syntax Check (<5s) — ast.parse, ruff, tsc
  Gate 2: Security Scan (<10s) — Semgrep SAST, OWASP rules
  Gate 3: Context Validation (<10s) — Import check, dependency
  Gate 4: Test Execution (<60s) — Dockerized pytest
  ↓
Validation Loop: max_retries=3, deterministic feedback
  ↓
Output: Production-ready code + Evidence artifacts
```

---

## 5. KEY INSIGHTS FOR MAS DESIGN

### 5.1 Governance-First Philosophy

```
NOT:  AI generates code → human reviews → merge
YES:  AI proposes → 4-Gate validates → Evidence stored → Human approves gate → merge
```

**Implication**: MAS MUST integrate với Quality Gates, KHÔNG phải replace chúng.

### 5.2 Evidence-Based Development

Every artifact (code, docs, tests, SAST report) stored in Evidence Vault với:
- SHA256 hash (integrity verification)
- S3 storage (MinIO, AGPL-safe via boto3)
- 8-state lifecycle: uploaded → validating → evidence_locked → awaiting_vcr → merged
- Immutable audit trail (who uploaded when, from which source: cli/extension/web/agent)

**Implication**: MAS agents MUST auto-capture evidence với `correlation_id` tracking.

### 5.3 Multi-Provider Resilience

**Cost Optimization Model** (Model Strategy v3.0):
```
Primary: Ollama (self-hosted GPU, $50/mo)
  - qwen3-coder:30b (256K context, code generation)
  - qwen3:32b (Vietnamese chat)
  - deepseek-r1:32b (reasoning mode)
Fallback 1: Claude (Anthropic, $1K/mo, <25s latency)
Fallback 2: Rule-based (deterministic patterns, $0/mo, 50ms)
```

**Failover Classification** (6 reasons):
1. `auth` — Invalid API key
2. `format` — Malformed request
3. `rate_limit` — Quota exceeded
4. `billing` — Payment failed
5. `timeout` — Latency >30s
6. `unknown` — Catch-all

**Implication**: MAS MUST handle provider failures gracefully với circuit breaker pattern.

### 5.4 Security Guardrails

**Input Sanitization** (12 patterns):
- SQL injection, command injection, path traversal, XSS, SSRF, LDAP injection, XML injection, template injection, OGNL injection, header injection, CRLF injection, eval injection

**Shell Guard** (8 deny patterns):
- `rm -rf`, `:(){ :|:& };:`, `> /dev/sd*`, `dd if=`, `mkfs.`, `chmod 777`, `wget|curl ... | sh`, `nc -l`

**Tool Context Restriction** (Nanobot N2):
- `max_delegation_depth` — prevent infinite agent chains
- `allowed_tools` — whitelist only necessary tools
- `working_directory` — sandboxed workspace

**Implication**: MAS agents KHÔNG được execute arbitrary commands; tất cả tools qua validation layer.

---

## 6. RECOMMENDED MAS ROLES (SDLC-aligned)

Dựa trên ADR-056 §12.5 — 12 SDLC roles + 3 types:

### 6.1 SE4A (Software Engineering for Agents) — 8 roles

| Role | Responsibility | LangChain Agent Type |
|------|----------------|----------------------|
| **Researcher** | Gather domain knowledge, analyze similar systems | ReAct Agent with web search tools |
| **PM (Product Manager)** | Clarify requirements, write BRD/PRD | Conversational Agent with structured output |
| **PJM (Project Manager)** | Sprint planning, task breakdown, resource allocation | Plan-and-Execute Agent |
| **Architect** | System design, technology selection, ERD/API spec | ReAct Agent with code analysis tools |
| **Coder** | Implement features based on spec | Code Interpreter Agent + EP-06 Codegen integration |
| **Reviewer** | Code review, quality audit, suggest improvements | Chain-of-Thought Agent with static analysis tools |
| **Tester** | Write tests, execute test suites, report bugs | ReAct Agent with pytest/jest execution |
| **DevOps** | Deploy to staging/prod, monitor health, rollback | Tool-calling Agent with kubectl/docker |

### 6.2 SE4H (Software Engineering for Humans) — 3 roles

| Role | Responsibility | LangChain Agent Type |
|------|----------------|----------------------|
| **CEO** | Approve G4 gates, strategic decisions | Human-in-the-loop (OTT notification) |
| **CPO** | Approve G1 gates, product decisions | Human-in-the-loop (OTT notification) |
| **CTO** | Approve G2/G3 gates, security/architecture reviews | Human-in-the-loop (OTT notification) |

### 6.3 Router — 1 role

| Role | Responsibility | LangChain Agent Type |
|------|----------------|----------------------|
| **Assistant** | Route user queries to appropriate agent, handle simple Q&A | Routing Agent (OpenAI Functions / LangGraph conditional edges) |

---

## 7. ORCHESTRATION PATTERNS

### 7.1 Pattern 1: Sequential Pipeline (G0 → G1 → G2 → G3 → G4)

```python
# LangGraph StateGraph
from langgraph.graph import StateGraph, END

workflow = StateGraph(ProjectState)
workflow.add_node("g0_design_thinking", design_thinking_agent)
workflow.add_node("g1_requirements", requirements_agent)
workflow.add_node("g2_architecture", architecture_agent)
workflow.add_node("g3_implementation", implementation_agent)
workflow.add_node("g4_deployment", deployment_agent)

workflow.set_entry_point("g0_design_thinking")
workflow.add_edge("g0_design_thinking", "g1_requirements")
workflow.add_edge("g1_requirements", "g2_architecture")
workflow.add_edge("g2_architecture", "g3_implementation")
workflow.add_edge("g3_implementation", "g4_deployment")
workflow.add_edge("g4_deployment", END)

app = workflow.compile()
```

### 7.2 Pattern 2: Supervisor (Router → Specialist Agents)

```python
# Supervisor pattern with Agent Supervisor
from langchain.agents import AgentExecutor
from langchain.agents.agent_types import AgentType

supervisor = AgentExecutor(
    agent=create_openai_functions_agent(...),
    tools=[
        researcher_tool,  # Call Researcher agent
        pm_tool,          # Call PM agent
        architect_tool,   # Call Architect agent
        coder_tool,       # Call Coder agent
        reviewer_tool,    # Call Reviewer agent
    ]
)
```

### 7.3 Pattern 3: Reflection Loop (Coder ↔ Reviewer)

```python
# Reflection pattern (Nanobot N7)
from langgraph.prebuilt import create_react_agent

# Step 1: Coder generates code
code = coder_agent.invoke({"task": spec})

# Step 2: Reviewer audits code
review = reviewer_agent.invoke({"code": code, "criteria": quality_gates})

# Step 3: If review fails, loop back to Coder with feedback
if review["status"] != "PASS":
    code = coder_agent.invoke({
        "task": spec,
        "previous_attempt": code,
        "feedback": review["issues"],
        "retry_count": retry_count + 1
    })
    # max_retries=3 (EP-06 validation loop)
```

---

## 8. MEMORY STRATEGY

### 8.1 Short-Term Memory (Conversation Buffer)

```python
from langchain.memory import ConversationBufferMemory

# Per-agent conversation memory (maps to agent_messages table)
memory = ConversationBufferMemory(
    memory_key="chat_history",
    return_messages=True,
    max_messages=50  # Nanobot N3 loop guard
)
```

### 8.2 Long-Term Memory (Vector Store)

```python
from langchain.vectorstores import Chroma
from langchain.embeddings import OllamaEmbeddings

# RAG for SDLC knowledge base
vectorstore = Chroma(
    collection_name="sdlc_knowledge",
    embedding_function=OllamaEmbeddings(model="bge-m3:latest"),  # 1.2GB model
    persist_directory="./chroma_db"
)

# Store:
# - ADRs (Architecture Decision Records)
# - Framework docs (SDLC 6.1.0)
# - Past project specs (PRDs, ERDs, API specs)
# - Code review comments (learning from PR feedback)
```

### 8.3 Semantic Memory (Entity Store)

```python
from langchain.memory import ConversationEntityMemory

# Track entities across conversation
entity_memory = ConversationEntityMemory(
    llm=llm,
    entity_extraction_prompt="""Extract key entities:
    - Features (e.g., "user authentication", "payment gateway")
    - Technologies (e.g., "FastAPI", "PostgreSQL", "React")
    - Constraints (e.g., "GDPR compliance", "<100ms latency")
    """
)
```

---

## 9. TOOL INTEGRATION

### 9.1 SDLC Orchestrator API Tools

```python
from langchain.tools import StructuredTool

# Tool 1: Create Quality Gate
create_gate_tool = StructuredTool.from_function(
    func=create_gate_via_api,
    name="create_quality_gate",
    description="Create G1/G2/G3/G4 quality gate for project",
    args_schema=GateCreateSchema  # Pydantic schema
)

# Tool 2: Upload Evidence
upload_evidence_tool = StructuredTool.from_function(
    func=upload_evidence_via_api,
    name="upload_evidence",
    description="Upload code/docs/tests to Evidence Vault",
    args_schema=EvidenceUploadSchema
)

# Tool 3: Generate Code (EP-06)
codegen_tool = StructuredTool.from_function(
    func=generate_code_via_ep06,
    name="generate_code",
    description="Generate production-ready code via EP-06 Codegen Pipeline",
    args_schema=CodegenRequestSchema
)

# Tool 4: Run SAST Scan
sast_tool = StructuredTool.from_function(
    func=run_semgrep_scan,
    name="security_scan",
    description="Run Semgrep SAST scan with OWASP rules",
    args_schema=SASTScanSchema
)
```

### 9.2 External Tools (with Shell Guard)

```python
from langchain.tools import ShellTool

# Shell tool with restrictions (Nanobot N2 + ZeroClaw)
shell_tool = ShellTool(
    allowed_commands=["git", "npm", "pytest", "docker"],  # whitelist
    forbidden_patterns=[
        r"rm\s+-rf",
        r">\s*/dev/sd",
        r"dd\s+if=",
        r"chmod\s+777",
        # ... (8 deny patterns from ShellGuard)
    ],
    working_directory="/workspace",  # sandboxed
    max_execution_time=60  # 60s timeout
)
```

---

## 10. COST & LATENCY OPTIMIZATION

### 10.1 Token Cost Tracking

```python
# Per-conversation budget circuit breaker (ADR-056 O3)
class BudgetGuard:
    def __init__(self, max_budget_cents: int):
        self.max_budget_cents = max_budget_cents
        self.spent_cents = 0

    def check_budget(self, estimated_cost_cents: int):
        if self.spent_cents + estimated_cost_cents > self.max_budget_cents:
            raise BudgetExceededError(
                f"Budget exhausted: ${self.spent_cents/100:.2f} / ${self.max_budget_cents/100:.2f}"
            )

    def record_usage(self, tokens: int, model: str):
        cost = self.calculate_cost(tokens, model)
        self.spent_cents += cost
        return cost
```

### 10.2 Latency Targets

```
Ollama (primary): <15s per generation
Claude (fallback): <25s per generation
Rule-based (final): <50ms per generation

Total agent response: <30s (P95)
Multi-agent workflow: <5min (simple task), <30min (complex task)
```

---

## 11. OBSERVABILITY & EVALUATION

### 11.1 Logging Strategy

```python
import structlog

logger = structlog.get_logger()

# Structured logging for each agent action
logger.info(
    "agent_action",
    agent_name="coder",
    action="generate_code",
    correlation_id="abc123",
    tokens_used=2500,
    cost_cents=15,
    latency_ms=12000,
    provider="ollama",
    model="qwen3-coder:30b"
)
```

### 11.2 Evaluation Metrics

```
Agent Quality Metrics:
- Task completion rate (did agent achieve goal?)
- Correctness (does output meet spec?)
- Code quality (SAST findings, test coverage)
- Cost efficiency (tokens used vs baseline)
- Latency (actual vs target)

System Metrics:
- Gate pass rate (G1/G2/G3/G4)
- Evidence completeness (% of required artifacts uploaded)
- Retry rate (validation loop iterations)
- Budget utilization ($ spent / $ allocated)
```

---

## 12. FAULT TOLERANCE

### 12.1 Provider Failover

```python
# Failover chain (ADR-056 D3)
class MultiProviderInvoker:
    def invoke(self, prompt: str):
        providers = ["ollama", "claude", "rule_based"]
        for provider in providers:
            try:
                return self._invoke_provider(provider, prompt)
            except FailoverError as e:
                logger.warning(f"Provider {provider} failed: {e.reason}")
                if e.reason == "auth":
                    continue  # Try next provider
                elif e.reason == "rate_limit":
                    time.sleep(60)  # Wait 60s then retry
                    continue
                elif e.reason == "timeout":
                    continue  # Next provider faster
                else:
                    continue  # Unknown error, try next
        raise AllProvidersFailed("All providers exhausted")
```

### 12.2 Human-in-the-Loop Interrupt

```python
# Human approval for critical decisions (ADR-056 O3)
async def request_human_approval(gate_id: str, approver_role: str):
    # Send OTT notification (Telegram/Zalo)
    await ott_gateway.send_notification(
        channel="telegram",
        recipient=approver_role,  # "cto", "cpo", "ceo"
        message=f"Gate {gate_id} requires approval. Reply APPROVE or REJECT."
    )

    # Wait for response (max 24h timeout)
    response = await ott_gateway.wait_for_response(timeout=86400)
    return response.action  # "APPROVE" or "REJECT"
```

---

## SUMMARY

**SDLC Orchestrator** = Governance-first platform với:
- 4-Gate Quality Pipeline (Syntax → Security → Context → Tests)
- Evidence Vault (immutable audit trail)
- Multi-Agent Team Engine (ADR-056, 14 non-negotiables)
- Multi-Provider Resilience (Ollama → Claude → Rule-based)
- Security Guardrails (32 deny patterns total)

**MAS Design Principles**:
1. **Integrate, don't replace**: MAS works WITH SDLC Orchestrator, not instead
2. **Evidence-based**: Every artifact auto-captured with correlation_id
3. **Cost-conscious**: Budget circuit breakers, token tracking
4. **Secure-by-default**: Input sanitizer, shell guard, tool context
5. **Human-in-the-loop**: CEO/CTO/CPO approval for critical gates

**Next**: Detailed MAS architecture design in `02-MAS-ARCHITECTURE.md`
