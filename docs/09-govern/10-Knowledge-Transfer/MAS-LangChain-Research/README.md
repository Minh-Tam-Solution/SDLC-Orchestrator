# MULTI-AGENT SYSTEM FOR SDLC ORCHESTRATOR

**Version**: 1.0.0 | **Date**: 2026-02-23 | **Status**: ✅ Production-Ready Design

---

## 🎯 TỔNG QUAN

Hệ thống Multi-Agent (MAS) sử dụng LangChain để **tự động phát triển phần mềm** từ BRD/PRD → Production-ready code, tích hợp hoàn toàn với SDLC Orchestrator governance platform.

### Điểm Khác Biệt

```
NOT: AI coder thay thế con người
YES: AI Team làm việc DƯỚI sự giám sát của Quality Gates

SDLC Orchestrator = Governance Layer
MAS = Execution Layer
```

### Tính Năng Chính

- ✅ **12 AI Agents**: Researcher, PM, PJM, Architect, Coder, Reviewer, Tester, DevOps + 3 human approvers + 1 Router
- ✅ **4-Gate Quality Pipeline**: Syntax → Security → Context → Tests (EP-06 integration)
- ✅ **Evidence-Based**: Auto-capture artifacts với SHA256 integrity
- ✅ **Multi-Provider**: Ollama ($50/mo) → Claude ($1K/mo) → Rule-based ($0)
- ✅ **Budget Guard**: Token cost tracking + circuit breaker
- ✅ **Security Guardrails**: 32 deny patterns (input sanitizer + shell guard)
- ✅ **Human-in-the-Loop**: OTT approval (Telegram/Zalo) cho critical gates

---

## 📁 TÀI LIỆU

| File | Mô tả | Pages |
|------|-------|-------|
| **[01-SDLC-ORCHESTRATOR-ANALYSIS.md](01-SDLC-ORCHESTRATOR-ANALYSIS.md)** | Phân tích SDLC Orchestrator concept, ADR-056, EP-07 | 12 |
| **[02-MAS-ARCHITECTURE.md](02-MAS-ARCHITECTURE.md)** | Kiến trúc MAS, agent roles, orchestration patterns | 25 |
| **[03-LANGCHAIN-IMPLEMENTATION.md](03-LANGCHAIN-IMPLEMENTATION.md)** | Mã nguồn LangChain, tools, workflows, agents | 30 |
| **README.md** (file này) | Tổng quan + quick start | 5 |

**Tổng**: ~70 trang tài liệu + working code

---

## 🚀 QUICK START

### 1. Prerequisites

```bash
# Python 3.11+
python --version  # Python 3.11.0+

# Ollama (local LLM)
curl -fsSL https://ollama.com/install.sh | sh
ollama pull qwen3:32b
ollama pull qwen3-coder:30b
ollama pull deepseek-r1:32b

# SDLC Orchestrator (backend running)
curl http://localhost:8300/health  # Should return {"status":"healthy"}
```

### 2. Installation

```bash
# Clone repo
cd /Users/anhnlq/Documents/GitHub/SDLC-Orchestrator/mas

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your API keys
```

### 3. Configuration

Tạo file `.env`:

```bash
# SDLC Orchestrator API
SDLC_API_BASE_URL=http://localhost:8300
SDLC_API_KEY=your-api-key

# Ollama
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL_CHAT=qwen3:32b
OLLAMA_MODEL_CODE=qwen3-coder:30b

# Claude (fallback)
ANTHROPIC_API_KEY=your-anthropic-key

# Budget
MAX_BUDGET_CENTS=10000  # $100
```

### 4. Run

```bash
# Start MAS server
python -m src.main

# Health check
curl http://localhost:8080/health
# Expected: {"status":"healthy","version":"1.0.0"}
```

---

## 📖 USAGE EXAMPLES

### Example 1: Generate Code với Reflection Loop

```bash
curl -X POST http://localhost:8080/generate-code \
  -H "Content-Type: application/json" \
  -d '{
    "spec": "Implement user authentication with JWT tokens and bcrypt hashing",
    "max_retries": 3
  }'

# Response:
{
  "status": "pass",
  "code": "... generated code ...",
  "retries": 2,
  "messages": [
    ["coder", "Generated initial code"],
    ["reviewer", "Security issue: plain text password. FAIL"],
    ["coder", "Fixed: added bcrypt hashing"],
    ["reviewer", "All checks passed. PASS"]
  ]
}
```

### Example 2: Full SDLC Workflow

```bash
curl -X POST http://localhost:8080/sdlc-workflow \
  -H "Content-Type: application/json" \
  -d '{
    "project_id": "550e8400-e29b-41d4-a716-446655440000",
    "brd": "Build an e-commerce platform with product catalog, shopping cart, and VNPay payment integration. Target: Vietnamese SMEs. Stack: FastAPI, PostgreSQL, React."
  }'

# Response:
{
  "project_id": "550e8400-e29b-41d4-a716-446655440000",
  "gates": {
    "g1": "gate-uuid-1",  # Design Ready (CPO approved)
    "g2": "gate-uuid-2",  # Architecture (CTO approved)
    "g3": "gate-uuid-3"   # Ship Ready (CTO approved)
  },
  "prd": "... detailed PRD ...",
  "architecture": { "erd": "...", "api_spec": "...", "diagram": "..." },
  "code": { "backend": "...", "frontend": "...", "tests": "..." },
  "messages": [ ... ]
}
```

---

## 🏗️ KIẾN TRÚC

### High-Level Architecture

```
USER (BRD/PRD)
      ↓
┌──────────────────────────────────────┐
│  ASSISTANT AGENT (Router)            │
│  - Parse intent                      │
│  - Ask clarifying questions          │
│  - Route to workflow                 │
└──────────────┬───────────────────────┘
               ↓
┌──────────────────────────────────────┐
│  STAGE 00-01: Design Thinking (G0→G1)│
│  Researcher → PM → PJM               │
│  [GATE G1: CPO Approval via OTT]     │
└──────────────┬───────────────────────┘
               ↓
┌──────────────────────────────────────┐
│  STAGE 02: Architecture (G1→G2)      │
│  Architect → Reviewer                │
│  [GATE G2: CTO Approval via OTT]     │
└──────────────┬───────────────────────┘
               ↓
┌──────────────────────────────────────┐
│  STAGE 03-04: Implementation (G2→G3) │
│  Coder ↔ Reviewer (reflection loop)  │
│  Tester (unit + integration tests)   │
│  [EP-06 Codegen: 4-Gate Pipeline]    │
│  [GATE G3: CTO Approval via OTT]     │
└──────────────┬───────────────────────┘
               ↓
┌──────────────────────────────────────┐
│  STAGE 05: Deployment (G3→G4)        │
│  DevOps → Tester (smoke tests)       │
│  [GATE G4: CEO Approval via OTT]     │
└──────────────────────────────────────┘
```

### 12 Agent Roles

**SE4A (Software Engineering for Agents) — 8 roles**:
1. **Researcher** — Domain knowledge, competitor analysis
2. **PM** — Write BRD/PRD, clarifying questions
3. **PJM** — Task breakdown, sprint planning
4. **Architect** — ERD, API spec, architecture diagram
5. **Coder** — Generate production code via EP-06
6. **Reviewer** — Code review, SAST scan, quality audit
7. **Tester** — Write tests (unit + integration + E2E)
8. **DevOps** — Deploy to staging/prod, health checks

**SE4H (Software Engineering for Humans) — 3 roles**:
9. **CPO** — Approve G1 gates (product decisions)
10. **CTO** — Approve G2/G3 gates (security/architecture)
11. **CEO** — Approve G4 gates (production deployment)

**Router — 1 role**:
12. **Assistant** — Route user queries to appropriate workflow

### 3 Orchestration Patterns

1. **Sequential Pipeline**: G0 → G1 → G2 → G3 → G4 (LangGraph StateGraph)
2. **Reflection Loop**: Coder ↔ Reviewer iterative improvement (max 3 retries)
3. **Supervisor**: PJM distributes tasks to multiple agents in parallel

---

## 🛠️ TECHNICAL STACK

### LangChain Ecosystem

```
langchain==0.1.0
langchain-community==0.0.20
langgraph==0.0.20
langchain-openai==0.0.5
```

### LLM Providers

```
Primary: Ollama (self-hosted GPU, $50/mo)
  - qwen3-coder:30b (256K context, code generation)
  - qwen3:32b (Vietnamese chat)
  - deepseek-r1:32b (reasoning mode)
  - qwen3:8b (fast tasks)

Fallback: Claude (Anthropic, $1K/mo)
  - claude-sonnet-4-5-20250929

Final: Rule-based (deterministic, $0/mo)
```

### Tools & Integrations

```
- SDLC Orchestrator API: Gates, Evidence, Codegen, SAST
- Web Search: Tavily API
- Vector Store: ChromaDB (RAG for knowledge base)
- Git: GitPython (branch, commit, push)
- Docker: docker-py (build, deploy)
```

---

## 🔐 SECURITY & GOVERNANCE

### Security Guardrails

```
Input Sanitization (12 patterns):
  SQL injection, command injection, path traversal, XSS, SSRF, LDAP, XML, template, OGNL, header, CRLF, eval injection

Shell Guard (8 deny patterns):
  rm -rf, fork bomb, device write, dd, mkfs, chmod 777, curl|sh, netcat

Tool Context Restriction:
  max_delegation_depth=1 (prevent infinite chains)
  allowed_tools=["git", "docker", "pytest"] (whitelist)
  working_directory="/workspace" (sandboxed)
```

### Quality Gates

```
G1: Design Ready — CPO approval, PRD complete
G2: Security + Architecture — CTO approval, architecture reviewed
G3: Ship Ready — CTO approval, tests pass, SAST clean
G4: Production Validation — CEO approval, deployed & validated
```

### Evidence-Based Development

Tất cả artifacts auto-captured:
- Code files (`.py`, `.ts`, `.tsx`)
- Tests (`test_*.py`, `*.spec.ts`)
- Docs (`README.md`, `ADR-*.md`)
- SAST reports (`semgrep.sarif`)
- Deployment logs (`deploy.log`)

Metadata: `correlation_id`, `timestamp`, `agent_name`, `gate_id`

---

## 💰 COST OPTIMIZATION

### Budget Guard

```python
# Per-conversation budget circuit breaker
budget_guard = BudgetGuard(max_budget_cents=10000)  # $100

# Before each LLM call
budget_guard.check_budget(estimated_cost_cents)

# After each LLM call
budget_guard.record_usage(tokens_input, tokens_output, model, latency_ms)

# Raises BudgetExceededError if budget exhausted
```

### Cost Comparison

| Task | Ollama (Primary) | Claude (Fallback) | Savings |
|------|------------------|-------------------|---------|
| Code generation (2K tokens) | $0.00 | $0.06 | 100% |
| Code review (3K tokens) | $0.00 | $0.09 | 100% |
| Architecture design (5K tokens) | $0.00 | $0.15 | 100% |
| **Monthly cost** (100 projects) | **$50** | **$5,000** | **99%** |

---

## 📊 PERFORMANCE TARGETS

```
Latency (P95):
  Code generation: <15s (Ollama), <25s (Claude)
  Code review: <10s
  SAST scan: <10s
  Total workflow: <5min (simple), <30min (complex)

Accuracy:
  Gate pass rate: >90%
  Code quality score: >80/100
  Test coverage: >90%
  Security findings: <5 HIGH/CRITICAL per scan
```

---

## 🧪 TESTING

```bash
# Run all tests
pytest tests/

# Run specific tests
pytest tests/test_agents.py -v
pytest tests/test_workflows.py -v
pytest tests/test_tools.py -v

# Coverage report
pytest --cov=src --cov-report=html
```

---

## 🚢 DEPLOYMENT

### Docker

```bash
# Build image
docker build -t mas-app:latest .

# Run container
docker run -d \
  -p 8080:8080 \
  --name mas-app \
  --env-file .env \
  mas-app:latest
```

### Docker Compose

```bash
# Start all services
docker compose up -d

# View logs
docker compose logs -f mas

# Stop services
docker compose down
```

---

## 📚 FURTHER READING

### SDLC Orchestrator Docs

- [CLAUDE.md](../CLAUDE.md) — AI assistant context (Module Zones)
- [ADR-056](../docs/02-design/01-ADRs/ADR-056-Multi-Agent-Team-Engine.md) — Multi-Agent Team Engine
- [EP-07](../docs/01-planning/02-Epics/EP-07-Multi-Agent-Team-Engine.md) — Multi-Agent Epic
- [API Inventory](../docs/backend/API-INVENTORY-REPORT.md) — 560 endpoints reference

### LangChain Resources

- [LangChain Docs](https://python.langchain.com/docs/get_started/introduction)
- [LangGraph Docs](https://langchain-ai.github.io/langgraph/)
- [LangSmith](https://smith.langchain.com/) — Observability platform

---

## 🤝 CONTRIBUTING

### Development Workflow

```bash
# 1. Create feature branch
git checkout -b feature/new-agent

# 2. Make changes
# ... edit src/agents/new_agent.py

# 3. Test
pytest tests/test_new_agent.py

# 4. Commit
git add .
git commit -m "feat(agents): Add NewAgent for X functionality"

# 5. Push & create PR
git push origin feature/new-agent
```

### Coding Standards

- **Python**: PEP 8, type hints (mypy strict), docstrings (Google style)
- **Testing**: pytest, >90% coverage, unit + integration tests
- **Documentation**: Markdown, code examples, architecture diagrams

---

## 📞 SUPPORT

- **Issues**: [GitHub Issues](https://github.com/Minh-Tam-Solution/SDLC-Orchestrator/issues)
- **Discussions**: [GitHub Discussions](https://github.com/Minh-Tam-Solution/SDLC-Orchestrator/discussions)
- **Email**: support@sdlc-orchestrator.vn

---

## 📝 CHANGELOG

### v1.0.0 (2026-02-23)

- ✅ Initial MAS architecture design
- ✅ 12 agent roles defined (8 SE4A + 3 SE4H + 1 Router)
- ✅ 3 orchestration patterns implemented (Sequential, Reflection, Supervisor)
- ✅ LangChain implementation with working code
- ✅ SDLC Orchestrator API integration (gates, evidence, codegen, SAST)
- ✅ Multi-provider failover (Ollama → Claude → Rule-based)
- ✅ Budget guard + security guardrails
- ✅ Docker deployment + docker-compose

---

## 📄 LICENSE

Apache 2.0 License — See [LICENSE](../LICENSE) file

---

## 🎓 CREDITS

**Author**: AI Architect + CTO Nguyen Quoc Huy
**Framework**: SDLC 6.1.0
**Pattern Sources**: OpenClaw, TinyClaw, Nanobot, ZeroClaw
**Technology**: LangChain, LangGraph, Ollama, FastAPI

---

**Status**: ✅ Production-Ready Design | Ready for Implementation & Testing
