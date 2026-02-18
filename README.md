# SDLC Orchestrator

**Operating System for Software 3.0** - The control plane that governs AI coders (Cursor, Claude Code, Copilot), combining Design Thinking validation, SDLC 6.0.6 governance, Multi-Agent Team orchestration, IR-based codegen, and multi-provider AI - built on battle-tested OSS infrastructure.

[![License](https://img.shields.io/badge/license-Apache%202.0-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![React](https://img.shields.io/badge/react-18.x-blue.svg)](https://reactjs.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-green.svg)](https://fastapi.tiangolo.com/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15.5-blue.svg)](https://www.postgresql.org/)
[![OPA](https://img.shields.io/badge/OPA-0.58-orange.svg)](https://www.openpolicyagent.org/)
[![Sprint](https://img.shields.io/badge/Sprint-176-brightgreen.svg)](docs/04-build/02-Sprint-Plans/SPRINT-176-AUTONOMOUS-CODEGEN-PILOT-PREP.md)
[![SDLC](https://img.shields.io/badge/SDLC-6.0.6-purple.svg)](SDLC-Enterprise-Framework/)

---

## 🎯 What is SDLC Orchestrator?

**SDLC Orchestrator** is the **Operating System for Software 3.0** - a control plane that sits ABOVE AI coders (Cursor, Claude Code, Copilot) to govern, validate, and ensure quality. We don't compete with AI coding tools - we orchestrate them.

### Software 3.0 Vision

```
┌─────────────────────────────────────────────────────────────────┐
│ LAYER 5: AI CODERS (External - We Orchestrate)                  │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌───────────┐ │
│  │   Cursor    │ │ Claude Code │ │   Copilot   │ │  DeepCode │ │
│  └─────────────┘ └─────────────┘ └─────────────┘ └───────────┘ │
│         ↑               ↑               ↑              ↑        │
│         └───────────────┴───────────────┴──────────────┘        │
│                    Governance API + Quality Gates               │
├─────────────────────────────────────────────────────────────────┤
│ LAYER 4: EP-06 CODEGEN (Our Innovation)                         │
│  • IR-Based Code Generation (qwen3-coder:30b)                   │
│  • 4-Gate Quality Pipeline (Syntax → Security → Context → Test) │
│  • Validation Loop with max_retries=3                           │
├─────────────────────────────────────────────────────────────────┤
│ LAYER 3: BUSINESS LOGIC (Our Core)                              │
│  • Gate Engine (OPA-powered Policy-as-Code)                     │
│  • Evidence Vault (Immutable audit trail)                       │
│  • Multi-Agent Team Engine (ADR-056, lane-based queue)          │
│  • AI Context Engine (Stage-aware prompts)                      │
├─────────────────────────────────────────────────────────────────┤
│ LAYER 2: INTEGRATION (Thin Adapters)                            │
│  • OPA REST API • MinIO S3 API • GitHub API • Semgrep CLI       │
├─────────────────────────────────────────────────────────────────┤
│ LAYER 1: INFRASTRUCTURE (OSS Components)                        │
│  • PostgreSQL • Redis • OPA • MinIO • Grafana                   │
└─────────────────────────────────────────────────────────────────┘
```

### The Problem We Solve

Engineering teams waste **60-70% of effort building features users don't need** because:
- AI coders generate code fast, but without governance
- No validation loop ensures AI-generated code meets quality standards
- Traditional PM tools focus on **task execution** instead of **governance and validation**

### Our Solution

The **ONLY platform** combining:

| Layer | Capability | Value |
|-------|------------|-------|
| **Design Thinking** | Gates 0.1, 0.2 validation | Build the RIGHT things |
| **Quality Gates** | OPA-powered Policy-as-Code | Enforce quality standards |
| **EP-06 Codegen** | IR-based code generation | Vietnamese SME templates |
| **4-Gate Pipeline** | Syntax → Security → Context → Tests | 95%+ validation pass rate |
| **Evidence Vault** | Immutable audit trail | 100% compliance traceability |
| **Multi-Agent Team** | AI agent collaboration | Lane-based queue, failover, OTT gateway |
| **AI Orchestration** | Multi-provider fallback | Ollama → Claude → Rule-based |

---

## 🚀 Quick Start

### Prerequisites

- **Docker** 24.0+ & **Docker Compose** 2.0+
- **Node.js** 20.x (for frontend development)
- **Python** 3.11+ (for backend development)
- **Make** (optional, for convenience commands)

### 1. Clone Repository

```bash
git clone --recurse-submodules https://github.com/Minh-Tam-Solution/SDLC-Orchestrator.git
cd SDLC-Orchestrator
```

> **Note**: The `--recurse-submodules` flag initializes the SDLC Enterprise Framework submodule (private repository — team access required).

### 2. Environment Setup

```bash
# Copy environment template
cp .env.example .env

# Edit .env with your settings (PostgreSQL, Redis, MinIO, etc.)
nano .env
```

### 3. Start Services

```bash
# Start all services (Backend, Frontend, PostgreSQL, Redis, MinIO, Grafana, OPA)
make up

# Or using docker-compose directly
docker-compose up -d
```

### 4. Access Applications

| Service | URL | Credentials |
|---------|-----|-------------|
| **Frontend** | http://localhost:3000 | (Create account on first run) |
| **Backend API** | http://localhost:8000 | N/A (JWT auth) |
| **API Docs** | http://localhost:8000/docs | N/A (Swagger UI) |
| **MinIO Console** | http://localhost:9001 | `minioadmin` / `minioadmin` |
| **Grafana** | http://localhost:3000 | `admin` / `admin` |
| **OPA** | http://localhost:8181 | N/A (no auth in dev) |

### 5. Initialize Database

```bash
# Run database migrations
make db-migrate

# Or manually
docker-compose exec backend alembic upgrade head

# Seed initial data (admin user, default policies)
make db-seed
```

### 6. Verify Installation

```bash
# Check backend health
curl http://localhost:8000/health

# Expected response:
# {"status":"healthy","version":"1.0.0","timestamp":"2025-11-21T..."}

# Check frontend
curl http://localhost:3000

# Expected: React app HTML
```

### 7. GitHub Integration (Optional)

SDLC Orchestrator supports GitHub integration for automatic project creation:

1. **Connect GitHub Account**:
   - Go to Settings → GitHub
   - Click "Connect GitHub"
   - Authorize SDLC Orchestrator (read-only access)

2. **Sync Repository**:
   - Select a repository from your GitHub account
   - System automatically:
     - Analyzes repository structure
     - Detects project type
     - Recommends policy pack
     - Maps folders to SDLC 6.0.6 stages
     - Creates project with initial gates

3. **Webhook Setup** (Optional):
   - Configure webhook in GitHub repository
   - URL: `https://api.sdlc-orchestrator.com/api/v1/github/webhook`
   - Events: push, pull_request, issues
   - Automatic sync on repository changes

---

## 📚 Documentation

### Quick Links

- **[Data Model ERD](docs/01-planning/04-Data-Model/Data-Model-ERD.md)** - 33 tables (v3.4.0, includes Multi-Agent)
- **[API Specification](docs/01-planning/05-API-Design/API-Specification.md)** - 91 endpoints (v3.6.0)
- **[EP-07 Multi-Agent Epic](docs/01-planning/02-Epics/EP-07-Multi-Agent-Team-Engine.md)** - Multi-Agent Team Engine scope
- **[ADR-056 Multi-Agent](docs/02-design/ADR-056-Multi-Agent-Team-Engine.md)** - Architecture decision
- **[Provider Integration](docs/03-integrate/03-Integration-Guides/Multi-Agent-Provider-Integration.md)** - Ollama/Claude failover

### Architecture

```
┌──────────────────────────────────────────────────────────────┐
│                      Frontend (React)                        │
│  - TypeScript 5.0, Vite, TailwindCSS, React Query            │
└───────────────────────┬──────────────────────────────────────┘
                        │ REST API (HTTP/JSON)
┌───────────────────────▼──────────────────────────────────────┐
│                    Backend (FastAPI)                         │
│  - Python 3.11, FastAPI, SQLAlchemy, Pydantic                │
│  - JWT Auth, RBAC, WebSocket (Real-time updates)            │
└───┬────────┬──────────┬──────────┬──────────┬───────────────┘
    │        │          │          │          │
    │        │          │          │          │
┌───▼───┐ ┌──▼──┐ ┌────▼────┐ ┌───▼───┐ ┌───▼────┐
│PostgreSQL│ Redis │  MinIO   │  OPA   │ Grafana │
│  15.5   │  7.2  │ (AGPL)   │  0.58  │ (AGPL)  │
│ (State) │(Cache)│(Evidence)│(Policy)│(Metrics)│
└─────────┘ └─────┘ └─────────┘ └───────┘ └────────┘
```

**Key Design Decisions**:
- **AGPL Containment**: MinIO & Grafana accessed via network API only (no code linking)
- **Policy-as-Code**: OPA (Apache-2.0) for governance automation
- **Bridge-First**: Read GitHub Issues/PRs (no native board until v2)
- **Multi-Provider AI**: Ollama (primary, $50/mo), Claude (fallback), Rule-based (final)
- **Multi-Agent Team Engine**: Lane-based queue, provider failover, OTT gateway (ADR-056)

---

## 🛠️ Development

### Local Development Setup

#### Backend (Python)

```bash
# Navigate to backend directory
cd backend

# Create virtual environment
python3.11 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt  # Dev tools (pytest, black, ruff)

# Run backend locally
uvicorn app.main:app --reload --port 8000

# Run tests
pytest tests/ -v --cov=app --cov-report=html

# Format code
black app/ tests/
ruff check app/ tests/

# Type checking
mypy app/
```

#### Frontend (React)

```bash
# Navigate to frontend directory
cd frontend

# Install dependencies
npm install

# Run development server
npm run dev

# Run tests
npm run test

# Build for production
npm run build

# Format code
npm run format
npm run lint
```

### Database Migrations

```bash
# Create new migration
make db-migration msg="Add users table"

# Or manually
docker-compose exec backend alembic revision --autogenerate -m "Add users table"

# Apply migrations
make db-migrate

# Rollback last migration
make db-rollback
```

### Policy Development (OPA)

```bash
# Navigate to policy directory
cd backend/policies

# Test policy locally
opa test . -v

# Evaluate policy (dry-run)
opa eval -i input.json -d . "data.sdlc.gates.g1.design_ready"

# Deploy policy to OPA server
curl -X PUT http://localhost:8181/v1/policies/sdlc \
  --data-binary @sdlc-policies.rego
```

---

## 🧪 Testing

### Backend Tests

```bash
# Run all tests
make test-backend

# Run specific test file
pytest tests/test_gates.py -v

# Run with coverage
make test-coverage

# Run integration tests (requires services running)
pytest tests/integration/ -v

# Run performance tests
pytest tests/performance/ -v --benchmark
```

### Frontend Tests

```bash
# Run all tests
make test-frontend

# Run unit tests
npm run test:unit

# Run integration tests
npm run test:integration

# Run E2E tests (Playwright)
npm run test:e2e

# Run with coverage
npm run test:coverage
```

### Load Testing

```bash
# Install locust
pip install locust

# Run load test
locust -f tests/load/locustfile.py --host=http://localhost:8000
```

---

## 📦 Deployment

### Production Deployment (Docker)

```bash
# Build production images
docker-compose -f docker-compose.prod.yml build

# Start production services
docker-compose -f docker-compose.prod.yml up -d

# Check logs
docker-compose -f docker-compose.prod.yml logs -f backend
```

### Cloud Deployment (AWS ECS)

See [Infrastructure Documentation](infrastructure/README.md) for:
- Terraform scripts (VPC, ECS, RDS, ElastiCache, S3)
- CI/CD pipeline (GitHub Actions)
- Monitoring setup (CloudWatch, Prometheus, Grafana)

---

## 🔒 Security

### Authentication

- **JWT Tokens**: 1-hour access tokens, 30-day refresh tokens
- **OAuth 2.0**: GitHub, Google, Microsoft SSO
- **MFA**: TOTP for C-Suite roles (CEO, CTO, CPO, CFO, CIO)

### RBAC (Role-Based Access Control)

| Role | Permissions |
|------|-------------|
| **Admin** | Full access (all gates, all projects) |
| **Engineering Manager** | Create gates, submit for review, view evidence |
| **Approver** (CTO/CPO/CEO) | Approve/reject gates |
| **Developer** | View gates, upload evidence (assigned projects only) |
| **Viewer** | Read-only access (auditors, compliance) |

### Compliance

- **SOC 2 Type II** (planned Q3 2026)
- **ISO 27001** (planned Q4 2026)
- **GDPR** Compliant (data retention, right to deletion)
- **Evidence Integrity**: SHA256 verification (100% tamper detection)

---

## 🤝 Contributing

We welcome contributions! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

### Development Workflow

1. **Fork** the repository
2. **Create** a feature branch (`git checkout -b feature/amazing-feature`)
3. **Follow** Zero Mock Policy (no TODOs, no placeholders)
4. **Write** tests (90%+ coverage required)
5. **Run** linters (`make lint`)
6. **Commit** with conventional commits (`feat: Add quality gate API`)
7. **Push** to your fork
8. **Open** a Pull Request

### Code Standards

- **Backend**: [Python Style Guide](docs/03-Development-Implementation/01-Development-Standards/Python-Style-Guide.md)
- **Frontend**: [TypeScript Style Guide](docs/03-Development-Implementation/01-Development-Standards/TypeScript-Style-Guide.md)
- **Zero Mock Policy**: [Mandatory Policy](docs/03-Development-Implementation/01-Development-Standards/ZERO-MOCK-POLICY.md)

---

## 📊 Project Status

**Current Stage**: Stage 04 (BUILD - Development & Implementation)
**Current Sprint**: Sprint 176 - ADR-056 Multi-Agent Foundation
**Framework**: SDLC 6.0.6 Complete Lifecycle (10 Stages + 4-Tier Classification)
**Positioning**: Operating System for Software 3.0
**Investment**: $564K total budget (90-day MVP) + $50K EP-06 extension

### Current Sprint Arc: Sprint 176-178 — Multi-Agent Team Engine

| Sprint | Focus | Status | Key Deliverables |
|--------|-------|--------|------------------|
| **Sprint 176** | ADR-056 Foundation | 🔄 In Progress | ADR-056, DB migration (3 tables), service account auth |
| **Sprint 177** | Multi-Agent Core Services | ⏳ Planned | 12 service files, 5 P0 endpoints, lane-based queue |
| **Sprint 178** | Multi-Agent Integration + OTT | ⏳ Planned | Team orchestrator, Telegram notify MVP, Vietnamese SME pilot |

### Gate G3: Ship Ready - APPROVED (Dec 12, 2025)

**CTO APPROVED** - Platform ready for beta pilot deployment:

| Metric | Target | Actual | Status |
|--------|--------|--------|--------|
| **Overall Readiness** | 95% | 98.2% | ✅ EXCEEDS |
| **OWASP ASVS L2** | 90% | 98.4% | ✅ EXCEEDS |
| **API p95 Latency** | <100ms | ~80ms | ✅ EXCEEDS |
| **Test Coverage** | 90% | 94% | ✅ EXCEEDS |
| **P0/P1 Bugs** | 0 | 0 | ✅ MET |

### EP-06 IR-Based Codegen Engine (Sprint 45-50)

**NEW** - Vietnamese SME-focused code generation:

| Component | Sprint | Status | Description |
|-----------|--------|--------|-------------|
| **Multi-Provider Architecture** | 45 | 🔄 In Progress | Ollama → Claude → DeepCode fallback |
| **IR Processor** | 46 | ⏳ Planned | Spec → Intermediate Representation |
| **Vietnamese Templates** | 47 | ⏳ Planned | E-commerce, HRM, CRM domain templates |
| **4-Gate Quality Pipeline** | 48 | ⏳ Planned | Syntax → Security → Context → Tests |
| **Vietnam SME Pilot** | 49 | ⏳ Planned | 5 founding customer deployments |
| **Productization** | 50 | ⏳ Planned | GA readiness, pricing launch |

### MVP v1.0.0 Complete (Dec 1, 2025)

- ✅ **Backend**: 91 API endpoints (FastAPI, PostgreSQL, Redis) — 64 core + 11 Multi-Agent + 16 other
- ✅ **Frontend**: React Dashboard, shadcn/ui, TanStack Query
- ✅ **Security**: JWT + OAuth + MFA, RBAC (13 roles), OWASP ASVS Level 2 (98.4%)
- ✅ **Evidence Vault**: MinIO S3, SHA256 integrity, 8-state lifecycle
- ✅ **Policy Engine**: OPA integration, 110 pre-built policies
- ✅ **AI Context Engine**: Multi-provider (Ollama, Claude, GPT-4o)
- ✅ **SAST Integration**: Semgrep with AI-specific security rules
- ✅ **Operations**: Prometheus metrics, Grafana dashboards
- 🔄 **Multi-Agent Team Engine**: Lane-based queue, provider failover, OTT gateway (Sprint 176-178)

### Quick Start

```bash
# 1. Clone and setup (--recurse-submodules for Framework, private repo)
git clone --recurse-submodules https://github.com/Minh-Tam-Solution/SDLC-Orchestrator.git
cd SDLC-Orchestrator
cp .env.example .env

# 2. Start all services
docker-compose up -d

# 3. Run backend
cd backend && pip install -r requirements.txt
python3 -m alembic upgrade head
uvicorn app.main:app --reload --port 8000

# 4. Run frontend
cd frontend/landing && npm install && npm run dev

# 5. Access application
# Frontend: http://localhost:5173
# Backend API: http://localhost:8000
# API Docs: http://localhost:8000/docs
```

### Upcoming Milestones

- ✅ **Gate G3 (Ship Ready)**: APPROVED (Dec 12, 2025) - 98.2% readiness
- 🔄 **Sprint 176**: ADR-056 Multi-Agent Foundation (Mar 17-28, 2026)
- ⏳ **Sprint 177**: Multi-Agent Core Services (Mar 31 - Apr 11, 2026)
- ⏳ **Sprint 178**: Multi-Agent Integration + OTT + Vietnamese SME Pilot (Apr 14-25, 2026)

---

## 🌟 Key Features

### 1. Quality Gate Management
- **Automated Policy Enforcement**: OPA-powered validation (no manual reviews)
- **Multi-Approval Workflow**: CEO, CTO, CPO sign-off (role-based)
- **Stage Progression Control**: Cannot skip stages (WHY → WHAT → HOW → BUILD...)

### 2. Evidence Vault (8-State Lifecycle)
- **Permanent Audit Trail**: SHA256 integrity (SOC 2 compliant)
- **8-State Machine**: generated → validating → retrying → escalated → evidence_locked → awaiting_vcr → merged/aborted
- **GitHub Auto-Collection**: PRs, commits, CI/CD logs auto-attached
- **Export for Compliance**: ZIP/PDF exports for auditors

### 3. EP-06 IR-Based Codegen (NEW)
- **Intermediate Representation**: Spec → IR → Code (deterministic)
- **Multi-Provider Fallback**: Ollama (qwen3-coder:30b) → Claude → DeepCode
- **4-Gate Quality Pipeline**: Syntax → Security → Context → Tests
- **Vietnamese SME Templates**: E-commerce, HRM, CRM domain-specific

### 4. AI Context Engine
- **Multi-Provider**: Ollama (primary), Claude (fallback), GPT-4o (fallback)
- **Stage-Aware Prompts**: Different prompts for WHY/WHAT/HOW/BUILD stages
- **Cost Optimization**: $50/month Ollama vs $1000/month external APIs

### 5. Real-Time Dashboard
- **WebSocket Updates**: Live gate status (no refresh needed)
- **Evidence Timeline**: Visual code generation history
- **Override Queue**: Admin review for security exceptions
- **Metrics**: Gate pass rate, codegen success rate, AI cost

### 6. SAST Integration (Sprint 43)
- **Semgrep Integration**: AI-specific security rules
- **Custom Rule Packs**: ai-codegen-security, prompt-injection-prevention
- **Override Management**: Tiered approval (Lead → Senior → CTO)
- **Evidence Linking**: Security findings attached to code artifacts

### 7. Multi-Agent Team Engine (EP-07, Sprint 176-178)
- **Lane-Based Queue**: Per-agent lanes with SKIP LOCKED + Redis pub/sub notify
- **Provider Failover**: 6-reason classification (auth/format/rate_limit/billing/timeout/unknown) with cooldowns
- **Agent Hierarchy**: Parent-child sessions with delegation depth limits (Nanobot N2 pattern)
- **Loop Guards**: 6 limits (max_messages, max_tokens, max_tool_calls, timeout, max_diff_size, max_retries)
- **Input Sanitizer**: 12 injection regex patterns for OTT external content
- **OTT Gateway**: Plugin-based architecture (Telegram MVP Sprint 178, Discord/Zalo planned)
- **Budget Circuit Breaker**: Token tracking + cost limits per conversation

### 8. Policy Pack Library
- **110+ Pre-Built Policies**: All 10 SDLC 6.0.6 stages covered
- **Customizable**: Parameters (min_reviewers, test_coverage, etc.)
- **Versioned**: Semantic versioning (v1.0, v1.1, etc.)

---

## 📈 Success Metrics

### Primary Metric: Feature Adoption Rate

**Definition**: % of shipped features used weekly by >50% of target users

**Targets**:
- Industry average: 30% (2024)
- With SDLC Orchestrator: **70%+** (2x improvement)

### Secondary Metrics

| Metric | Baseline | Target |
|--------|----------|--------|
| **Rework Rate** | 18% | <5% |
| **Time to Value** | 87 days | <45 days |
| **Production Incidents** | 12 P1/quarter | <3 P1/quarter |
| **Gate Pass Rate** | N/A | 92%+ |
| **NPS** | 6.2/10 | 8/10+ |

---

## 🏆 Competitive Advantage

### Where We Don't Compete

| Category | Leaders | Our Position |
|----------|---------|--------------|
| **IDE-level autocomplete** | Copilot, Cursor | We orchestrate them |
| **Pure PM tools** | Jira, Linear | We complement, not replace |
| **1-click app builders** | Lovable, v0.dev | Different complexity tier |

### Why SDLC Orchestrator

**Control Plane Positioning** - We sit ABOVE AI coders, not alongside them:

```
Layer 3: AI Coders (Claude/Cursor/Copilot) ← They generate
Layer 2: SDLC Orchestrator                 ← We govern & validate
Layer 1: SDLC Framework                    ← Methodology foundation
```

**Unique Value**:
- ✅ **FIRST** Operating System for Software 3.0 (10-stage complete lifecycle)
- ✅ **ONLY** platform combining Design Thinking + Quality Gates + Multi-Agent + IR Codegen
- ✅ **Experience Moat**: 6-12 months to understand SDLC 6.0.6 nuances
- ✅ **Knowledge Moat**: 110+ pre-built policies, Vietnamese SME templates
- ✅ **Cost Moat**: Ollama-first = 95% cost reduction vs external APIs

---

## 🛣️ Roadmap

### 2025 Q4: MVP + Gate G3 (Complete)
- ✅ **Gate G3**: Ship Ready APPROVED (Dec 12, 2025) - 98.2%
- ✅ **Sprint 43-44**: OPA Policy Guards, Semgrep SAST, CrossReferenceValidator
- ✅ **Sprint 45-50**: EP-06 Codegen Pipeline (Multi-Provider, IR Processor, Quality Pipeline)

### 2026 Q1: Multi-Agent Team Engine (Sprint 176-178)
| Sprint | Focus | Target |
|--------|-------|--------|
| 176 | ADR-056 Foundation | DB migration (3 tables), service accounts, feature flags |
| 177 | Multi-Agent Core Services | 12 service files, lane-based queue, failover classifier |
| 178 | Integration + OTT Notify | Team orchestrator, Telegram MVP, Vietnamese SME pilot |

### 2026 Q2: OTT Expansion + Scale
- OTT approval with identity verification (Sprint 179+)
- Discord, WhatsApp, Zalo channel plugins
- Multi-VCS support (GitLab, Bitbucket)
- Enterprise SSO (SAML 2.0)

### 2026 Q3-Q4: Enterprise Ready
- SOC 2 Type II certification
- ISO 27001 compliance
- Mobile app (iOS, Android)
- Multi-language support (Vietnamese, English, Mandarin)

---

## 📞 Support

- **Documentation**: [docs/](docs/)
- **GitHub Issues**: [Issues](https://github.com/Minh-Tam-Solution/SDLC-Orchestrator/issues)

---

## 📄 License

This project is licensed under the **Apache License 2.0** - see the [LICENSE](LICENSE) file for details.

**AGPL Components** (Network-Only Access):
- **MinIO** (AGPL-3.0): S3-compatible storage (accessed via boto3 S3 API)
- **Grafana** (AGPL-3.0): Metrics visualization (accessed via HTTP API)

**Legal Position**: Network-only access does NOT trigger AGPL copyleft obligations.

**SDLC Enterprise Framework** (Git submodule):
- **Repository**: `https://github.com/Minh-Tam-Solution/SDLC-Enterprise-Framework` (private — team access required)
- **Version**: SDLC 6.0.6 (7-Pillar + AI Governance Principles)
- **Status**: Private repository, not yet published as OSS

---

## 🙏 Acknowledgments

- **SDLC 6.0.6 Framework**: Inspired by industry best practices (CMMI, ITIL, Agile) — private repository
- **OPA**: Policy-as-Code foundation (CNCF graduated project)
- **FastAPI**: Lightning-fast Python web framework
- **React**: Industry-standard UI library

---

---

**Built with discipline by the SDLC Orchestrator team**

**Status**: ✅ Gate G3 APPROVED - Ship Ready (98.2%)
**Version**: 1.0.0 (Beta Pilot Ready)
**Current Sprint**: Sprint 176 - ADR-056 Multi-Agent Foundation
**Framework**: SDLC 6.0.6 Complete Lifecycle (10 Stages + 4-Tier Classification)
**Positioning**: Operating System for Software 3.0
**Last Updated**: February 18, 2026
