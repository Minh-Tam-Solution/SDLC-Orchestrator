# SDLC Orchestrator

**The ONLY platform that ensures teams build the RIGHT things RIGHT** - combining Design Thinking validation, SDLC 4.9 governance, and multi-provider AI - built on battle-tested OSS infrastructure.

[![License](https://img.shields.io/badge/license-Apache%202.0-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![React](https://img.shields.io/badge/react-18.x-blue.svg)](https://reactjs.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-green.svg)](https://fastapi.tiangolo.com/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15.5-blue.svg)](https://www.postgresql.org/)
[![OPA](https://img.shields.io/badge/OPA-0.58-orange.svg)](https://www.openpolicyagent.org/)

---

## 🎯 What is SDLC Orchestrator?

**SDLC Orchestrator** is a **governance-first platform** that sits on top of your existing tools (GitHub, Jira, Linear) to enforce SDLC 4.9 quality gates, ensure evidence-based decisions, and eliminate the 70% feature waste plaguing engineering teams.

### The Problem We Solve

Engineering teams waste **60-70% of effort building features users don't need** because traditional PM tools focus on **task execution** instead of **governance and validation**.

**Root Cause**: Project management tools track WHAT you're building, but don't enforce:
- ✅ **WHY** you should build it (Design Thinking validation missing)
- ✅ **WHAT** quality standards must be met (No automated quality gates)
- ✅ **HOW** it will operate in production (Runbooks often forgotten)
- ✅ **WHO** approved each decision (No audit trail for compliance)

### Our Solution

The **ONLY platform** combining:

```
┌─────────────────────────────────────────────────────────────┐
│ 1. DESIGN THINKING VALIDATION (WHY/WHAT)                   │
│    Gates 0.1, 0.2 ensure we build the RIGHT things         │
├─────────────────────────────────────────────────────────────┤
│ 2. AUTOMATED QUALITY GATES (HOW/BUILD/TEST)                │
│    Policy-as-Code enforcement (OPA-powered)                 │
├─────────────────────────────────────────────────────────────┤
│ 3. OPERATE-FIRST MINDSET (DEPLOY/OPERATE)                  │
│    Production excellence enforced                           │
├─────────────────────────────────────────────────────────────┤
│ 4. AI CONTEXT ENGINE (Multi-Provider)                      │
│    Stage-aware AI assistance (10 stages)                    │
├─────────────────────────────────────────────────────────────┤
│ 5. EVIDENCE VAULT (Permanent Traceability)                 │
│    100% audit trail for compliance                          │
└─────────────────────────────────────────────────────────────┘
```

---

## 🚀 Quick Start

### Prerequisites

- **Docker** 24.0+ & **Docker Compose** 2.0+
- **Node.js** 20.x (for frontend development)
- **Python** 3.11+ (for backend development)
- **Make** (optional, for convenience commands)

### 1. Clone Repository

```bash
git clone https://github.com/your-org/sdlc-orchestrator.git
cd sdlc-orchestrator
```

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

---

## 📚 Documentation

### Quick Links

- **[Product Vision](docs/00-Project-Foundation/01-Vision/Product-Vision.md)** - Vision, market opportunity, success metrics
- **[Product Roadmap](docs/00-Project-Foundation/04-Roadmap/Product-Roadmap.md)** - 90-day timeline (Nov 14 - Feb 10, 2026)
- **[Functional Requirements](docs/01-Planning-Analysis/Functional-Requirements/Functional-Requirements-Document.md)** - FR1-FR5 detailed specs
- **[AGPL Containment Legal Brief](docs/01-Planning-Analysis/Legal-Review/AGPL-Containment-Legal-Brief.md)** - AGPL strategy
- **[Zero Mock Policy](docs/03-Development-Implementation/01-Development-Standards/ZERO-MOCK-POLICY.md)** - Mandatory code standards

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
- **Multi-Provider AI**: Claude (reasoning), GPT-4o (code), Gemini (bulk)

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

**Current Stage**: Stage 03 (BUILD - Development & Implementation)
**Sprint**: Week 4 of 13 (December 3-6, 2025)
**Timeline**: 90 days (Nov 14, 2025 - Feb 10, 2026)
**Investment**: $564K total budget

### Recent Milestones

- ✅ **Week 1 Complete** (Nov 14-18): Foundation documents (15 docs, 6,545+ lines)
- ✅ **Gate G0.1 PASSED** (Nov 15): Design Thinking validation
- ✅ **Gate G0.2 PASSED** (Nov 18): Solution diversity (Option C selected)
- ✅ **Week 2 Complete** (Nov 21-25): Legal review + FRD + Data model + Beta recruitment
- ✅ **Gate G1 PASSED** (Nov 25): Legal approval + Planning complete
- ✅ **Week 3 Complete** (Nov 28 - Dec 2): Backend APIs + Infrastructure (23 endpoints, 6,600+ lines)
  - Day 1: SQLAlchemy Models (21 tables, 2,400+ lines)
  - Day 2: Alembic Migrations + Seed Data (24 tables deployed)
  - Day 3: Authentication + Gates APIs (14 endpoints)
  - Day 4: Evidence + Policies APIs (9 endpoints)
  - Day 5: Docker + Integration Tests (28 tests, 8 services)
- ✅ **Gate G2 READY** (Dec 2): 95% readiness (23 APIs functional, architecture docs pending)

### Current Sprint (Week 4: Dec 3-6)

**Architecture Documentation + OSS Integration**:
- ⏳ **Day 1-2 (Dec 3-4)**: Architecture documentation (C4 diagrams, API specs, deployment guides)
- ⏳ **Day 3 (Dec 5)**: Real MinIO S3 integration (replace mock evidence upload)
- ⏳ **Day 4 (Dec 6)**: Real OPA integration (replace mock policy evaluation)

**Delivered in Week 3** (Already Complete ✅):
- ✅ Authentication API (6 endpoints): login, refresh, logout, /me, health, root
- ✅ Gates API (8 endpoints): list, create, get, update, submit, approve, reject, delete
- ✅ Evidence API (5 endpoints): upload, list, get, integrity-check, integrity-history
- ✅ Policies API (4 endpoints): list, get, evaluate, get-evaluations
- ✅ Database (24 tables): Users, Roles, Gates, Evidence, Policies, Audit Logs
- ✅ Integration Tests (28 tests): All endpoints tested, all passing

**Success Criteria**: Real OSS integration (MinIO + OPA), architecture docs complete, Gate G2 PASSED

**Quick Start** (Week 4 Developers):
```bash
# 1. Clone and setup environment (30 minutes)
git clone https://github.com/your-org/sdlc-orchestrator.git
cd sdlc-orchestrator
cp .env.example .env
nano .env  # Update DATABASE_URL, REDIS_URL, SECRET_KEY

# 2. Start Docker services (8 services)
docker-compose up -d

# 3. Setup backend
cd backend
python3.11 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
pip install -r requirements-dev.txt

# 4. Install pre-commit hooks (Zero Mock Policy enforcement)
pre-commit install

# 5. Run database migrations
python3 -m alembic upgrade head

# 6. Verify setup
pytest tests/ -v  # All tests should pass
curl http://localhost:8000/health  # Should return {"status":"healthy"}

# 7. Start development
# See docs/03-Development-Implementation/01-Sprint-Plans/WEEK-4-SPRINT-PLAN.md
# See docs/03-Development-Implementation/02-Setup-Guides/DEV-ENVIRONMENT-SETUP.md
```

**Documentation**:
- 📖 [Week 4 Sprint Plan](docs/03-Development-Implementation/01-Sprint-Plans/WEEK-4-SPRINT-PLAN.md) - Day-by-day implementation guide
- 📖 [Dev Environment Setup](docs/03-Development-Implementation/02-Setup-Guides/DEV-ENVIRONMENT-SETUP.md) - Complete setup guide (30 min)
- 📖 [Week 4-5 Success Criteria](docs/03-Development-Implementation/01-Sprint-Plans/WEEK-4-5-SUCCESS-CRITERIA.md) - Acceptance criteria (all 28 endpoints)
- 📖 [Gate G2 Evidence Package](docs/09-Executive-Reports/01-Gate-Reviews/GATE-G2-EVIDENCE-PACKAGE.md) - All architecture docs

### Upcoming Milestones

- 🎯 **Week 5** (Dec 9-13): Evidence + Policies + Projects APIs (14 endpoints)
- 🎯 **Week 6-7** (Dec 16-27): Frontend Dashboard (React + shadcn/ui)
- 🎯 **Week 8-9** (Dec 30 - Jan 10): VS Code Extension + CLI
- 🎯 **Week 10-11** (Jan 13-24): Internal beta testing (BFlow team)
- 🎯 **Week 12-13** (Jan 27 - Feb 7): Production hardening + compliance
- 🎯 **Gate G3 (Ship Ready)** (Jan 31): Development complete
- 🎯 **MVP Launch** (Feb 10): First 100 paying teams

---

## 🌟 Key Features

### 1. Quality Gate Management
- **Automated Policy Enforcement**: OPA-powered validation (no manual reviews)
- **Multi-Approval Workflow**: CEO, CTO, CPO sign-off (role-based)
- **Stage Progression Control**: Cannot skip stages (WHY → WHAT → HOW → BUILD...)

### 2. Evidence Vault
- **Permanent Audit Trail**: SHA256 integrity (SOC 2 compliant)
- **GitHub Auto-Collection**: PRs, commits, CI/CD logs auto-attached
- **Export for Compliance**: ZIP/PDF exports for auditors

### 3. AI Context Engine
- **Multi-Provider**: Claude (reasoning), GPT-4o (code), Gemini (bulk)
- **Stage-Aware Prompts**: Different prompts for WHY/WHAT/HOW/BUILD stages
- **Cost Tracking**: $500/month budget monitoring

### 4. Real-Time Dashboard
- **WebSocket Updates**: Live gate status (no refresh needed)
- **Executive Reports**: PDF exports for stakeholders
- **Metrics**: Gate pass rate, time to approval, AI cost

### 5. Policy Pack Library
- **100+ Pre-Built Policies**: All 10 SDLC 4.9 stages covered
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

**Why NOT Jira/Linear/GitLab**:
- ❌ No Design Thinking validation (build wrong features)
- ❌ No automated quality gates (manual reviews = slow)
- ❌ No evidence vault (no compliance audit trail)
- ❌ No operate-first enforcement (runbooks forgotten)

**Why SDLC Orchestrator**:
- ✅ **FIRST** platform on SDLC 4.9 (10-stage complete lifecycle)
- ✅ **ONLY** platform combining Design Thinking + Quality Gates + AI
- ✅ **Experience Moat**: 6-12 months to understand SDLC 4.9 nuances
- ✅ **Knowledge Moat**: 100+ pre-built policies (vs competitors' 0)

---

## 🛣️ Roadmap

### Q4 2025 - Q1 2026: MVP Launch (13 Weeks)
- ✅ **Week 1** (Nov 14-18): Foundation documents (DONE - 15 docs, 6,545+ lines)
- ✅ **Week 2** (Nov 21-25): Legal review + FRD + Data model (DONE - FRD 8,500+ lines, 21 tables)
- ✅ **Week 3** (Nov 28 - Dec 2): Backend APIs + Infrastructure (DONE - 23 endpoints, 28 tests, 8 Docker services)
- ⏳ **Week 4** (Dec 3-6): Architecture docs + Real OSS integration (MinIO, OPA) - **IN PROGRESS**
- ⏳ **Week 5** (Dec 9-13): Frontend Dashboard foundation (React + shadcn/ui setup)
- ⏳ **Week 6-7** (Dec 16-27): Frontend Dashboard (Authentication + Gates UI)
- ⏳ **Week 8-9** (Dec 30 - Jan 10): VS Code Extension + CLI
- ⏳ **Week 10-11** (Jan 13-24): Internal beta testing (BFlow team)
- ⏳ **Week 12-13** (Jan 27 - Feb 7): Production hardening + compliance
- 🎯 **Feb 10, 2026**: MVP Launch (First 100 paying teams)

### Q1 2026: Scale to $10K MRR
- GitHub Enterprise integration
- Slack Enterprise integration
- Advanced RBAC (custom roles)
- API v2 (GraphQL)

### Q3 2026: Enterprise Ready
- SOC 2 Type II certification
- SAML SSO
- First enterprise customer ($999/month tier)

### Q4 2026: Profitability Path
- Multi-language support (Spanish, Mandarin)
- Advanced analytics dashboards
- AI v2 (fine-tuned models)
- Mobile app (iOS, Android)

---

## 📞 Support

- **Documentation**: [docs/](docs/)
- **GitHub Issues**: [Issues](https://github.com/your-org/sdlc-orchestrator/issues)
- **Slack Community**: [Join Slack](https://sdlc-orchestrator.slack.com)
- **Email Support**: support@sdlc-orchestrator.com

---

## 📄 License

This project is licensed under the **Apache License 2.0** - see the [LICENSE](LICENSE) file for details.

**AGPL Components** (Network-Only Access):
- **MinIO** (AGPL-3.0): S3-compatible storage (accessed via boto3 S3 API)
- **Grafana** (AGPL-3.0): Metrics visualization (accessed via HTTP API)

**Legal Position**: Network-only access does NOT trigger AGPL copyleft obligations (see [Legal Brief](docs/01-Planning-Analysis/Legal-Review/AGPL-Containment-Legal-Brief.md)).

---

## 🙏 Acknowledgments

- **SDLC 4.9 Framework**: Inspired by industry best practices (CMMI, ITIL, Agile)
- **OPA**: Policy-as-Code foundation (CNCF graduated project)
- **FastAPI**: Lightning-fast Python web framework
- **React**: Industry-standard UI library

---

## 📊 Statistics

![GitHub Stars](https://img.shields.io/github/stars/your-org/sdlc-orchestrator)
![GitHub Forks](https://img.shields.io/github/forks/your-org/sdlc-orchestrator)
![GitHub Issues](https://img.shields.io/github/issues/your-org/sdlc-orchestrator)
![GitHub Contributors](https://img.shields.io/github/contributors/your-org/sdlc-orchestrator)

---

**Built with ❤️ by the SDLC Orchestrator team**

**Status**: 🚧 Active Development (Week 2 of 13)
**Version**: 1.0.0 (Pre-Release)
**First Release**: February 10, 2026

---

**Questions?** Open an issue or join our [Slack community](https://sdlc-orchestrator.slack.com)!
