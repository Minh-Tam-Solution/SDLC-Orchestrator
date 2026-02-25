# N8N MULTI-AGENT SYSTEM FOR SDLC ORCHESTRATOR

**Version**: 1.0.0 | **Date**: 2026-02-23 | **Status**: ✅ Production-Ready Design

---

## 🎯 TỔNG QUAN

Hệ thống Multi-Agent (MAS) sử dụng **n8n workflow automation** để **tự động phát triển phần mềm** từ BRD/PRD → Production-ready code, tích hợp hoàn toàn với SDLC Orchestrator governance platform.

### Điểm Khác Biệt vs LangChain

```
n8n MAS:
  ✅ Visual workflow editor (no-code/low-code)
  ✅ 400+ pre-built integrations (Slack, GitHub, Telegram, etc)
  ✅ Built-in queue system (Redis-backed)
  ✅ Self-hosted ($0) hoặc Cloud ($20-50/mo)
  ✅ Enterprise features (LDAP, SSO, audit logs)
  ✅ Web UI cho non-technical users

LangChain MAS:
  ✅ Code-first (full Python control)
  ✅ Advanced agent patterns (ReAct, Plan-and-Execute)
  ✅ Custom tool creation flexibility
  ✅ Better for complex reasoning chains
  ❌ Requires Python expertise
  ❌ No visual debugging
```

### Tính Năng Chính

- ✅ **5 Core Workflows**: Router → Design Thinking → Architecture → Coding → Deployment
- ✅ **Visual Debugging**: n8n UI hiển thị execution history với từng node
- ✅ **Reflection Loop**: Coder ↔ Reviewer với max_retries=3
- ✅ **Multi-Provider Failover**: Ollama → Claude → Rule-based với error handling
- ✅ **OTT Gateway**: Telegram/Zalo approval flows tích hợp sẵn
- ✅ **Evidence-Based**: Auto-capture artifacts với SHA256 integrity
- ✅ **Budget Guard**: Token cost tracking với circuit breaker
- ✅ **Security Guardrails**: Input sanitizer + SAST scan tích hợp

---

## 📁 TÀI LIỆU

| File | Mô tả | Pages |
|------|-------|-------|
| **[01-N8N-MAS-ARCHITECTURE.md](01-N8N-MAS-ARCHITECTURE.md)** | Kiến trúc n8n MAS, so sánh LangChain, tool integration | 18 |
| **[02-N8N-WORKFLOW-EXAMPLES.md](02-N8N-WORKFLOW-EXAMPLES.md)** | 5 workflow JSON importable (Reflection, Gate, Failover, RAG, OTT) | 35 |
| **README.md** (file này) | Quick start + deployment guide | 6 |

**Tổng**: ~60 trang tài liệu + 5 production-ready workflows

---

## 🚀 QUICK START

### 1. Prerequisites

```bash
# Docker + Docker Compose
docker --version  # Docker 20.10+
docker compose version  # Docker Compose v2.0+

# SDLC Orchestrator backend running
curl http://localhost:8300/health  # Should return {"status":"healthy"}

# Ollama (optional, for local LLM)
curl -fsSL https://ollama.com/install.sh | sh
ollama pull qwen3:32b
ollama pull qwen3-coder:30b
```

### 2. Installation

**Option A: Docker Compose (Recommended)**

```bash
# Clone repo
cd /Users/anhnlq/Documents/GitHub/SDLC-Orchestrator/mas/n8n

# Start n8n + PostgreSQL + Redis
docker compose up -d

# Check logs
docker compose logs -f n8n
```

**Option B: npm (Development)**

```bash
# Install n8n globally
npm install n8n -g

# Start n8n
n8n start

# Access UI
open http://localhost:5678
```

### 3. Configuration

Tạo file `.env`:

```bash
# n8n Configuration
N8N_HOST=0.0.0.0
N8N_PORT=5678
N8N_PROTOCOL=http
N8N_BASIC_AUTH_ACTIVE=true
N8N_BASIC_AUTH_USER=admin
N8N_BASIC_AUTH_PASSWORD=sdlc@2025

# Execution Mode
EXECUTIONS_MODE=queue  # Use queue for production
EXECUTIONS_PROCESS=own  # Run in separate processes
QUEUE_BULL_REDIS_HOST=redis
QUEUE_BULL_REDIS_PORT=6379

# Database (PostgreSQL)
DB_TYPE=postgresdb
DB_POSTGRESDB_HOST=postgres
DB_POSTGRESDB_PORT=5432
DB_POSTGRESDB_DATABASE=n8n
DB_POSTGRESDB_USER=n8n
DB_POSTGRESDB_PASSWORD=n8n@2025

# SDLC Orchestrator API
SDLC_API_BASE_URL=http://host.docker.internal:8300
SDLC_API_KEY=your-api-key

# Ollama
OLLAMA_BASE_URL=http://host.docker.internal:11434

# Claude (fallback)
ANTHROPIC_API_KEY=your-anthropic-key

# Telegram Bot (OTT Gateway)
TELEGRAM_BOT_TOKEN=your-bot-token
```

### 4. Import Workflows

**Bước 1: Access n8n UI**

```bash
open http://localhost:5678
# Login: admin / sdlc@2025
```

**Bước 2: Import workflows**

1. Click **"Workflows"** → **"Add workflow"** → **"Import from file"**
2. Import 5 workflows từ `02-N8N-WORKFLOW-EXAMPLES.md`:
   - Workflow 1: Reflection Loop (Coder ↔ Reviewer)
   - Workflow 2: Create Gate G1 + Upload Evidence
   - Workflow 3: Multi-Provider Failover
   - Workflow 4: Vector Store RAG
   - Workflow 5: Telegram OTT Approval

**Bước 3: Configure credentials**

Tại mỗi workflow, cấu hình credentials:
- **SDLC API**: HTTP Request nodes → Add credentials → Header Auth với `Authorization: Bearer YOUR_API_KEY`
- **Ollama**: HTTP Request nodes → Point to `http://host.docker.internal:11434`
- **Telegram**: Telegram Bot nodes → Add Bot Token

**Bước 4: Activate workflows**

Click **"Active"** toggle để enable webhooks và triggers.

### 5. Test Workflows

**Test Workflow 1: Reflection Loop**

```bash
curl -X POST http://localhost:5678/webhook-test/reflection-loop \
  -H "Content-Type: application/json" \
  -d '{
    "spec": "Implement user authentication with JWT tokens and bcrypt hashing",
    "max_retries": 3
  }'

# Response (sau ~30s):
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

**Test Workflow 2: Create Gate G1**

```bash
curl -X POST http://localhost:5678/webhook-test/create-gate \
  -H "Content-Type: application/json" \
  -d '{
    "project_id": "550e8400-e29b-41d4-a716-446655440000",
    "gate_type": "G1_CONSULTATION",
    "title": "Design Ready Gate",
    "prd": "Build e-commerce platform with VNPay payment integration"
  }'

# Response:
{
  "gate_id": "gate-uuid-123",
  "status": "EVALUATED",
  "policy_result": "pass",
  "evidence_uploaded": true
}
```

**Test Workflow 3: Multi-Provider Failover**

```bash
curl -X POST http://localhost:5678/webhook-test/multi-provider \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Explain the difference between JWT and OAuth 2.0"
  }'

# Response (if Ollama succeeds):
{
  "provider": "ollama",
  "model": "qwen3:32b",
  "response": "...",
  "latency_ms": 850
}

# Response (if Ollama fails, Claude fallback):
{
  "provider": "claude",
  "model": "claude-sonnet-4-5-20250929",
  "response": "...",
  "latency_ms": 2400,
  "fallback_reason": "Ollama timeout after 30s"
}
```

---

## 🏗️ KIẾN TRÚC

### High-Level Workflow Architecture

```
┌──────────────────────────────────────────────────────────┐
│  WORKFLOW 0: Router (Assistant Agent)                    │
│  - Parse user input (BRD/PRD)                            │
│  - Ask clarifying questions via OTT                      │
│  - Route to appropriate workflow (1-4)                   │
└──────────────┬───────────────────────────────────────────┘
               │
       ┌───────┴───────┬───────────┬───────────┐
       v               v           v           v
┌──────────────┐ ┌──────────┐ ┌─────────┐ ┌──────────┐
│  Workflow 1  │ │Workflow 2│ │Workflow3│ │Workflow 4│
│Design Thinking│ │Architect │ │ Coding  │ │Deployment│
│  (G0→G1)     │ │ (G1→G2)  │ │ (G2→G3) │ │ (G3→G4)  │
└──────────────┘ └──────────┘ └─────────┘ └──────────┘
```

### Workflow 3: Coding (Reflection Loop Detail)

```
Start Workflow
      ↓
Initialize Variables (code="", retries=0, max_retries=3)
      ↓
┌─────────────────────────────────────────────────┐
│  Reflection Loop (max 3 iterations)             │
│  ┌──────────────────────────────────────────┐   │
│  │  1. AI Agent (Coder)                     │   │
│  │     - Prompt: spec + previous feedback   │   │
│  │     - Model: qwen3-coder:30b (Ollama)    │   │
│  │     - Output: Generated code             │   │
│  └──────────────┬───────────────────────────┘   │
│                 ↓                                │
│  ┌──────────────────────────────────────────┐   │
│  │  2. EP-06 Codegen Pipeline               │   │
│  │     - Gate 1: Syntax (ast.parse, ruff)   │   │
│  │     - Gate 2: Security (Semgrep SAST)    │   │
│  │     - Gate 3: Context (imports, deps)    │   │
│  │     - Gate 4: Tests (pytest smoke)       │   │
│  └──────────────┬───────────────────────────┘   │
│                 ↓                                │
│  ┌──────────────────────────────────────────┐   │
│  │  3. Store Code (Evidence Vault)         │   │
│  │     - Upload to MinIO S3                 │   │
│  │     - SHA256 hash verification           │   │
│  └──────────────┬───────────────────────────┘   │
│                 ↓                                │
│  ┌──────────────────────────────────────────┐   │
│  │  4. AI Agent (Reviewer)                  │   │
│  │     - Prompt: Review code quality        │   │
│  │     - Model: qwen3:32b (Ollama)          │   │
│  │     - Output: PASS / FAIL + feedback     │   │
│  └──────────────┬───────────────────────────┘   │
│                 ↓                                │
│  ┌──────────────────────────────────────────┐   │
│  │  5. Check Review Result                  │   │
│  │     - If PASS → Exit loop                │   │
│  │     - If FAIL → Increment retries        │   │
│  │     - If retries < max → Loop back to 1  │   │
│  │     - If retries >= max → Escalate       │   │
│  └──────────────────────────────────────────┘   │
└─────────────────────────────────────────────────┘
      ↓
Return Response (status, code, retries, messages)
```

---

## 🛠️ TECHNICAL STACK

### n8n Core

```yaml
Version: n8n 1.x (latest)
Execution Mode: queue (Redis-backed)
Database: PostgreSQL 15.5
Cache: Redis 7.2
UI: React 18 (built-in)
API: REST + Webhooks
```

### AI Integration Nodes

```yaml
Built-in n8n Nodes:
  - AI Agent (LangChain integration)
  - OpenAI Node
  - Anthropic Claude Node
  - HTTP Request (for Ollama)
  - Code Node (JavaScript/Python)

Custom Integrations:
  - SDLC Orchestrator API (HTTP Request nodes)
  - EP-06 Codegen Pipeline (HTTP Request)
  - Semgrep SAST (Code Node with subprocess)
  - MinIO S3 (HTTP Request with S3 API)
```

### LLM Providers

```yaml
Primary: Ollama (self-hosted GPU, $50/mo)
  - qwen3-coder:30b (256K context, code generation)
  - qwen3:32b (Vietnamese chat)
  - deepseek-r1:32b (reasoning mode)
  - qwen3:8b (fast tasks)

Fallback: Claude (Anthropic, $1K/mo)
  - claude-sonnet-4-5-20250929

Final: Rule-based (deterministic, $0/mo)
```

### Deployment Options

```yaml
Option 1: Docker Compose (Recommended)
  Cost: $0 (self-hosted)
  Scalability: Horizontal (multiple workers)
  Suitable: Production (10-100 workflows)

Option 2: n8n Cloud (Starter)
  Cost: $20/mo (up to 2,500 executions)
  Scalability: Automatic
  Suitable: Small teams (1-10 workflows)

Option 3: n8n Cloud (Pro)
  Cost: $50/mo (up to 10,000 executions)
  Features: LDAP, SSO, audit logs
  Suitable: Enterprise (100+ workflows)
```

---

## 💰 COST COMPARISON

### Self-Hosted vs Cloud

| Item | Self-Hosted (Docker) | n8n Cloud Starter | n8n Cloud Pro |
|------|---------------------|------------------|---------------|
| n8n License | $0 (Apache 2.0) | $20/mo | $50/mo |
| Ollama GPU Server | $50/mo (1x RTX 4090) | N/A | N/A |
| Claude API (fallback) | $0-1,000/mo (usage) | $0-1,000/mo | $0-1,000/mo |
| PostgreSQL + Redis | $10/mo (DO Droplet) | Included | Included |
| **Total** | **$60-1,060/mo** | **$20-1,020/mo** | **$50-1,050/mo** |

**Recommendation**: Self-hosted Docker Compose cho Vietnam SME (full control, lowest cost long-term)

### vs LangChain MAS

| Feature | n8n MAS | LangChain MAS |
|---------|---------|---------------|
| Setup Time | <30 min (import workflows) | ~2h (code + deploy) |
| Non-Technical Friendly | ✅ Yes (visual editor) | ❌ No (Python required) |
| Debugging | ✅ Visual execution history | ⚠️ Logs only |
| Customization | ⚠️ Limited to nodes | ✅ Full Python control |
| Integration Effort | ✅ 400+ pre-built | ⚠️ Custom code per tool |
| Cost (Self-Hosted) | $55-1,060/mo | $55-1,020/mo |
| Best For | SME, rapid prototyping | Advanced use cases, R&D |

---

## 🔐 SECURITY & GOVERNANCE

### Security Features

```yaml
Authentication:
  - Basic Auth (username/password)
  - LDAP integration (Pro plan)
  - SSO (SAML, Pro plan)

Authorization:
  - Role-based access (Owner, Admin, Member, Guest)
  - Workflow-level permissions
  - Credential isolation (encrypted in DB)

Audit:
  - Execution history (100% retained)
  - Credential access logs
  - Webhook request logs

Data Protection:
  - Credentials encrypted (AES-256)
  - PostgreSQL + Redis TLS
  - Environment variable secrets
```

### Quality Gates Integration

Tất cả workflows tích hợp với SDLC Orchestrator Quality Gates:

```yaml
G1: Design Ready — CPO approval via Telegram OTT
G2: Security + Architecture — CTO approval, SAST scan pass
G3: Ship Ready — Tests pass, code review approved
G4: Production Validation — Deployment smoke tests pass
```

### Evidence-Based Development

Tự động capture artifacts:
- Code files (`.py`, `.ts`, `.tsx`)
- SAST reports (`semgrep.sarif`)
- Test results (`pytest.json`)
- Deployment logs (`deploy.log`)

Metadata: `correlation_id`, `timestamp`, `agent_name`, `gate_id`

---

## 📊 PERFORMANCE TARGETS

```yaml
Latency (P95):
  Workflow execution: <30s (simple), <2min (complex)
  Code generation: <15s (Ollama), <25s (Claude)
  Gate evaluation: <5s
  Evidence upload: <2s (10MB)

Throughput:
  Concurrent workflows: 10-50 (depends on workers)
  Queue capacity: 10,000+ executions
  Redis pub/sub: <10ms latency

Resource Usage:
  n8n container: 512MB-2GB RAM
  PostgreSQL: 1GB RAM, 10GB storage
  Redis: 256MB RAM
```

---

## 🧪 TESTING

### Manual Testing via n8n UI

1. **Open workflow** → Click **"Execute Workflow"**
2. **View execution** → Click on node để xem input/output
3. **Debug errors** → Click error node → View error details
4. **Re-run** → Click **"Retry Execution"**

### Automated Testing via Webhooks

```bash
# Test all 5 workflows sequentially
./test-all-workflows.sh

# Test specific workflow
curl -X POST http://localhost:5678/webhook-test/reflection-loop \
  -H "Content-Type: application/json" \
  -d @test-data/reflection-loop.json

# View execution history
curl http://localhost:5678/rest/executions \
  -u admin:sdlc@2025 | jq '.data[] | {id, status, workflowName}'
```

### Load Testing

```bash
# Install Apache Bench
sudo apt install apache2-utils

# Test webhook with 100 concurrent requests
ab -n 100 -c 10 -p test-data/reflection-loop.json \
   -T "application/json" \
   http://localhost:5678/webhook-test/reflection-loop

# Expected: 10+ req/s, <5s p95 latency
```

---

## 🚢 DEPLOYMENT

### Production Checklist

```yaml
✅ Configuration:
  - EXECUTIONS_MODE=queue (Redis-backed)
  - EXECUTIONS_PROCESS=own (separate processes)
  - N8N_BASIC_AUTH_ACTIVE=true (enable authentication)
  - Set strong password (min 12 chars)

✅ Database:
  - PostgreSQL 15.5 with connection pooling
  - Daily backups (pg_dump)
  - Point-in-time recovery enabled

✅ Redis:
  - Persistent storage enabled (appendonly yes)
  - Max memory policy: allkeys-lru
  - Password protection (requirepass)

✅ Monitoring:
  - n8n health endpoint: GET /healthz
  - PostgreSQL metrics (Prometheus)
  - Redis metrics (RedisInsight)
  - Workflow execution alerts (>5 failures/hour)

✅ Security:
  - HTTPS with TLS 1.3 (nginx reverse proxy)
  - Rate limiting (100 req/min per IP)
  - Firewall rules (only port 443 public)
  - Credentials rotation (90 days)

✅ Scaling:
  - Multiple n8n workers (QUEUE_BULL_MAX_WORKERS=5)
  - PostgreSQL read replicas
  - Redis Sentinel (high availability)
```

### Deployment Script

```bash
#!/bin/bash
# deploy.sh

set -e

echo "🚀 Deploying n8n MAS to production..."

# 1. Pull latest images
docker compose pull

# 2. Stop old containers
docker compose down

# 3. Database migration (if any)
docker compose run --rm n8n n8n import:workflow --input=/backup/workflows/*.json

# 4. Start new containers
docker compose up -d

# 5. Health check
for i in {1..30}; do
  if curl -f http://localhost:5678/healthz; then
    echo "✅ n8n is healthy"
    exit 0
  fi
  echo "⏳ Waiting for n8n... ($i/30)"
  sleep 2
done

echo "❌ Health check failed"
docker compose logs --tail=50 n8n
exit 1
```

---

## 📚 FURTHER READING

### n8n Documentation

- [n8n Docs](https://docs.n8n.io/) — Official documentation
- [n8n Community](https://community.n8n.io/) — Forum và examples
- [n8n Integrations](https://n8n.io/integrations) — 400+ pre-built nodes
- [n8n GitHub](https://github.com/n8n-io/n8n) — Source code (Apache 2.0)

### SDLC Orchestrator Docs

- [CLAUDE.md](../../CLAUDE.md) — AI assistant context (Module Zones)
- [ADR-056](../../docs/02-design/01-ADRs/ADR-056-Multi-Agent-Team-Engine.md) — Multi-Agent Team Engine
- [EP-07](../../docs/01-planning/02-Epics/EP-07-Multi-Agent-Team-Engine.md) — Multi-Agent Epic
- [API Inventory](../../docs/backend/API-INVENTORY-REPORT.md) — 560 endpoints reference

### Related Projects

- [LangChain MAS](../README.md) — Code-first alternative với Python
- [OpenClaw](https://github.com/OpenClaw/openclaw) — Lane-based queue pattern
- [TinyClaw](https://github.com/TinyClaw/tinyclaw) — @mention routing pattern
- [Nanobot](https://github.com/Nanobot/nanobot) — Tool context restrictions

---

## 🤝 CONTRIBUTING

### Development Workflow

```bash
# 1. Fork repo
git clone https://github.com/Minh-Tam-Solution/SDLC-Orchestrator.git
cd SDLC-Orchestrator/mas/n8n

# 2. Make changes (edit workflows in n8n UI)

# 3. Export workflows
curl http://localhost:5678/rest/workflows/{id}/export \
  -u admin:sdlc@2025 > workflows/new-workflow.json

# 4. Test
./test-all-workflows.sh

# 5. Commit
git add workflows/new-workflow.json
git commit -m "feat(n8n): Add new workflow for X"

# 6. Push & create PR
git push origin feature/new-workflow
```

### Workflow Naming Convention

```yaml
Format: {number}-{stage}-{agent}-{action}.json
Examples:
  - 01-design-thinking-researcher-market-analysis.json
  - 02-architecture-architect-erd-generation.json
  - 03-coding-coder-python-backend.json
  - 04-deployment-devops-docker-deploy.json
```

---

## 📞 SUPPORT

- **Issues**: [GitHub Issues](https://github.com/Minh-Tam-Solution/SDLC-Orchestrator/issues)
- **Discussions**: [GitHub Discussions](https://github.com/Minh-Tam-Solution/SDLC-Orchestrator/discussions)
- **Email**: support@sdlc-orchestrator.vn
- **n8n Community**: [community.n8n.io](https://community.n8n.io/)

---

## 📝 CHANGELOG

### v1.0.0 (2026-02-23)

- ✅ Initial n8n MAS architecture design
- ✅ 5 production-ready workflows (Reflection, Gate, Failover, RAG, OTT)
- ✅ Docker Compose deployment configuration
- ✅ Multi-provider AI integration (Ollama → Claude → Rule-based)
- ✅ SDLC Orchestrator API integration (gates, evidence, codegen, SAST)
- ✅ Security features (Basic Auth, credential encryption, audit logs)
- ✅ Performance targets documented (P95 <30s workflow execution)

---

## 📄 LICENSE

Apache 2.0 License — See [LICENSE](../../LICENSE) file

---

## 🎓 CREDITS

**Author**: AI Architect + CTO Nguyen Quoc Huy
**Framework**: SDLC 6.1.0
**Pattern Sources**: OpenClaw, TinyClaw, Nanobot, ZeroClaw
**Technology**: n8n, PostgreSQL, Redis, Ollama, FastAPI

---

**Status**: ✅ Production-Ready Design | Ready for Implementation & Testing

**Quick Start Summary**:
1. `docker compose up -d` (30s)
2. Import 5 workflows from `02-N8N-WORKFLOW-EXAMPLES.md` (5 min)
3. Configure credentials (5 min)
4. Test với curl commands (5 min)
5. **Total**: <15 min từ zero → first code generation

**Cost**: $60-1,060/mo (self-hosted với Ollama primary, Claude fallback)
**vs LangChain**: Dễ deploy hơn, visual debugging, 400+ integrations, nhưng ít flexible hơn cho advanced use cases
