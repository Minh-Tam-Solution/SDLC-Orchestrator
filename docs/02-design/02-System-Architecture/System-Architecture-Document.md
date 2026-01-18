# System Architecture Document
## 5-Layer Architecture + Bridge-First Design (Software 3.0)

**Version**: 3.1.0
**Date**: January 08, 2026
**Status**: ACTIVE - APPROVED
**Authority**: CTO + Tech Lead + Backend Lead
**Foundation**: Stage 01 (Requirements v3.1.0, API Specs v3.1.0, Data Model v3.1.0)
**Stage**: Stage 02 (HOW - Design & Architecture)
**Framework**: SDLC 5.1.1 Complete Lifecycle (10 Stages)
**Positioning**: Operating System for Software 3.0

**Changelog v3.1.0** (Jan 08, 2026):
- **MinIO Migration**: Migrated to AI-Platform shared service (`ai-platform-minio` on `ai-net` network)
- **Port Change**: MinIO S3 API now on port 9020 (host) / 9000 (container)
- **Shared Service Architecture**: MinIO now serves multiple AI services centrally
- **Frontend Consolidation**: Sprint 64-69 complete, unified Next.js on port 8310

**Changelog v3.0.0** (Dec 23, 2025):
- **SOFTWARE 3.0 PIVOT**: 5-Layer Architecture (EP-06 Codegen Layer added)
- Added EP-06 Codegen Layer (Section 12)
- Added 4-Gate Quality Pipeline for Codegen
- Added Validation Loop Orchestration (max_retries=3)
- Added Evidence State Machine (8 states)
- Added Multi-Provider Fallback (Ollama → Claude → DeepCode)
- Updated table count: 24 → 30 tables (EP-06 Codegen tables)
- Updated API endpoints: 52 → 64 endpoints

**Changelog v2.0.0** (Dec 3, 2025):
- Added AI Governance Layer (Section 11)
- Added Context-Aware Requirements Engine (ADR-011)
- Added AI Task Decomposition Service (ADR-012)
- Added 4-Level Planning Hierarchy (ADR-013)
- Added SDLC Structure Validator (ADR-014)

---

## Table of Contents

1. [Architecture Overview](#1-architecture-overview)
2. [5-Layer Architecture](#2-5-layer-architecture)
3. [Bridge-First Strategy](#3-bridge-first-strategy)
4. [Component Breakdown](#4-component-breakdown)
5. [Data Flow](#5-data-flow)
6. [Technology Stack](#6-technology-stack)
7. [Scalability Design](#7-scalability-design)
8. [Security Architecture](#8-security-architecture)
9. [Deployment Architecture](#9-deployment-architecture)
10. [Architecture Decisions (ADRs)](#10-architecture-decisions-adrs)
11. [AI Governance Layer](#11-ai-governance-layer) *(v2.0.0)*
12. [EP-06 Codegen Layer](#12-ep-06-codegen-layer) *(NEW v3.0.0)*

---

## 1. Architecture Overview

### 1.1 High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│ LAYER 1: USER-FACING (Proprietary - Apache-2.0)                │
│                                                                 │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐         │
│  │ React        │  │ VS Code      │  │ CLI          │         │
│  │ Dashboard    │  │ Extension    │  │ (sdlcctl)    │         │
│  │ (Port 3000)  │  │ (Extension)  │  │ (Binary)     │         │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘         │
│         │ HTTPS           │ HTTPS           │ HTTPS            │
└─────────┼─────────────────┼─────────────────┼──────────────────┘
          │                 │                 │
          ↓                 ↓                 ↓
┌─────────────────────────────────────────────────────────────────┐
│ LAYER 2: BUSINESS LOGIC (Proprietary - Apache-2.0)             │
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ FastAPI Gateway (Port 8000)                              │  │
│  │ - /api/v1/auth, /api/v1/projects, /api/v1/gates        │  │
│  │ - /api/v1/evidence, /api/v1/policies, /api/v1/ai       │  │
│  │ - /graphql (GraphQL endpoint)                           │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                 │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐         │
│  │ Gate Engine  │  │ Evidence     │  │ AI Context   │         │
│  │ Service      │  │ Vault API    │  │ Engine       │         │
│  │ (Policy)     │  │ (S3 Wrapper) │  │ (Claude/GPT) │         │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘         │
│         │ HTTP             │ S3 API          │ HTTP             │
└─────────┼──────────────────┼─────────────────┼──────────────────┘
          │                  │                 │
          ↓                  ↓                 ↓
┌─────────────────────────────────────────────────────────────────┐
│ LAYER 3: INTEGRATION (Thin Wrapper - Apache-2.0)               │
│                                                                 │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐         │
│  │ opa_service  │  │ minio_       │  │ grafana_     │         │
│  │ .py          │  │ service.py   │  │ service.py   │         │
│  │ (REST API)   │  │ (S3 API)     │  │ (HTTP API)   │         │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘         │
│         │ HTTP POST       │ S3 PUT          │ HTTP GET         │
└─────────┼─────────────────┼─────────────────┼──────────────────┘
          │                 │                 │
          ↓                 ↓                 ↓
┌─────────────────────────────────────────────────────────────────┐
│ LAYER 4: INFRASTRUCTURE (OSS - AGPL/Apache-2.0)                │
│                                                                 │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐         │
│  │ OPA          │  │ MinIO        │  │ Grafana      │         │
│  │ (Apache-2.0) │  │ (AGPL v3)    │  │ (AGPL v3)    │         │
│  │ Port: 8181   │  │ Port: 9020   │  │ Port: 3000   │         │
│  │              │  │ (ai-net)     │  │              │         │
│  └──────────────┘  └──────────────┘  └──────────────┘         │
│                                                                 │
│  ┌──────────────┐  ┌──────────────┐                           │
│  │ PostgreSQL   │  │ Redis        │                           │
│  │ (PG License) │  │ (BSD-3)      │                           │
│  │ Port: 5432   │  │ Port: 6379   │                           │
│  └──────────────┘  └──────────────┘                           │
└─────────────────────────────────────────────────────────────────┘

AGPL CONTAINMENT BOUNDARIES:
─────────────────────────────
[HTTP API] = Network boundary (AGPL does NOT cross)
[iframe]   = Browser security boundary (AGPL does NOT cross)
[S3 API]   = Network protocol (same as AWS S3, no code linking)
```

### 1.2 Architecture Characteristics

| Characteristic | Target | Design Choice |
|----------------|--------|---------------|
| **Scalability** | 100 teams (MVP) → 1,000 teams (Year 3) | Horizontal scaling (K8s + Redis cache) |
| **Performance** | <100ms API latency (p95) | FastAPI async + PostgreSQL indexing |
| **Availability** | 99.9% uptime (SLA) | Blue-green deployment + health checks |
| **Security** | OWASP Top 10 compliant | JWT + OAuth 2.0 + MFA + RBAC |
| **Maintainability** | <10% tech debt ratio | Clean architecture + ADRs + tests |
| **Observability** | 100% API coverage | Grafana + Prometheus + structured logging |

---

## 2. 4-Layer Architecture

### Layer 1: User-Facing (Proprietary)

**Purpose**: Client applications that users interact with.

**Components**:

**1. React Dashboard** (Port 3000):
```typescript
// Technology Stack
- React 18 (hooks, suspense, concurrent rendering)
- TypeScript 5.0+ (type safety)
- Tailwind CSS + shadcn/ui (consistent design system)
- React Query (API state management, caching)
- Zustand (global state)
- React Router (client-side routing)

// Key Pages
/dashboard → Project overview (gates, evidence, DORA metrics)
/projects/:id → Project detail (timeline, team, gate status)
/gates/:id → Gate detail (policy, evidence, approvals)
/evidence → Evidence vault browser (search, filter, upload)
/settings → User settings (MFA, API keys, integrations)
```

**2. VS Code Extension**:
```json
{
  "name": "sdlc-orchestrator",
  "displayName": "SDLC Orchestrator",
  "version": "0.1.0",
  "engines": { "vscode": "^1.80.0" },
  "activationEvents": ["onStartupFinished"],
  "contributes": {
    "views": {
      "explorer": [
        { "id": "sdlc.gateStatus", "name": "Gate Status" },
        { "id": "sdlc.evidence", "name": "Evidence Vault" }
      ]
    },
    "commands": [
      { "command": "sdlc.attachEvidence", "title": "Attach Evidence to Gate" },
      { "command": "sdlc.validateGate", "title": "Validate Gate Policy" },
      { "command": "sdlc.openStage", "title": "Open Next Stage" }
    ]
  }
}
```

**3. CLI (`sdlcctl`)**:
```bash
# Installation
$ brew install sdlcctl (macOS)
$ curl -sSL https://get.sdlc-orchestrator.com | sh (Linux)

# Commands
$ sdlcctl auth login                    # Login via OAuth 2.0
$ sdlcctl projects list                 # List all projects
$ sdlcctl gates validate --stage WHAT   # Validate Gate G1
$ sdlcctl evidence upload --doc BRD.md --gate G1  # Attach evidence
$ sdlcctl ai generate --stage HOW --component "Gate Engine"  # AI code generation
```

**License**: Apache-2.0 (Proprietary)

---

### Layer 2: Business Logic (Proprietary)

**Purpose**: Core application logic, no OSS dependencies (except libraries).

**Components**:

**1. FastAPI Gateway** (Port 8000):
```python
# app/main.py
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="SDLC Orchestrator API",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc"
)

# CORS (React Dashboard)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Dashboard
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(auth_router, prefix="/api/v1/auth", tags=["auth"])
app.include_router(projects_router, prefix="/api/v1/projects", tags=["projects"])
app.include_router(gates_router, prefix="/api/v1/gates", tags=["gates"])
app.include_router(evidence_router, prefix="/api/v1/evidence", tags=["evidence"])
app.include_router(policies_router, prefix="/api/v1/policies", tags=["policies"])
app.include_router(ai_router, prefix="/api/v1/ai", tags=["ai"])

# GraphQL
from strawberry.fastapi import GraphQLRouter
app.include_router(GraphQLRouter(schema), prefix="/graphql")
```

**2. Gate Engine Service**:
```python
# app/services/gate_engine.py
from typing import Dict, List
import httpx  # HTTP client (NOT OPA SDK - AGPL avoidance)

class GateEngine:
    """
    Policy-as-Code evaluation engine (OPA wrapper).

    AGPL CONTAINMENT: HTTP-only access to OPA (no SDK imports).
    """

    def __init__(self, opa_endpoint: str = "http://opa:8181"):
        self.opa_endpoint = opa_endpoint

    async def evaluate_gate(
        self,
        gate_id: str,
        policy_pack: Dict,
        evidence: List[Dict]
    ) -> Dict:
        """
        Evaluate gate using OPA policy engine.

        Args:
            gate_id: Gate ID (G0.1, G0.2, G1, ..., G9)
            policy_pack: YAML policy converted to JSON
            evidence: List of evidence metadata

        Returns:
            {
                "decision": "PASS" | "FAIL",
                "missing_evidence": ["legal-review-report.md", ...],
                "recommendations": ["Add AGPL containment strategy", ...]
            }
        """
        # Call OPA via HTTP (NOT SDK import)
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.opa_endpoint}/v1/data/gates/{gate_id}/allow",
                json={
                    "input": {
                        "gate_id": gate_id,
                        "policy": policy_pack,
                        "evidence": evidence
                    }
                }
            )

        result = response.json()
        return {
            "decision": "PASS" if result["result"] else "FAIL",
            "missing_evidence": result.get("missing", []),
            "recommendations": result.get("recommendations", [])
        }
```

**3. Evidence Vault API**:
```python
# app/services/evidence_vault.py
import httpx
from typing import BinaryIO

class EvidenceVault:
    """
    S3-compatible evidence storage (MinIO wrapper).

    AGPL CONTAINMENT: S3 API-only access (no MinIO SDK imports).
    """

    def __init__(self, s3_endpoint: str = "http://minio:9000"):
        self.s3_endpoint = s3_endpoint

    async def upload_evidence(
        self,
        file: BinaryIO,
        bucket: str,
        object_name: str,
        metadata: Dict
    ) -> Dict:
        """
        Upload evidence file to S3 storage.

        AGPL RISK: NONE (S3 PUT request, no code linking)
        """
        async with httpx.AsyncClient() as client:
            response = await client.put(
                f"{self.s3_endpoint}/{bucket}/{object_name}",
                data=file,
                headers={
                    "Content-Type": "application/octet-stream",
                    "x-amz-meta-gate-id": metadata["gate_id"],
                    "x-amz-meta-project-id": metadata["project_id"]
                }
            )

        # Store metadata in PostgreSQL
        await self.store_metadata(object_name, metadata)

        return {
            "url": f"{self.s3_endpoint}/{bucket}/{object_name}",
            "status": response.status_code
        }

    async def store_metadata(self, object_name: str, metadata: Dict):
        """Store evidence metadata in PostgreSQL."""
        # PostgreSQL insert (evidence table)
        pass
```

**4. AI Context Engine**:
```python
# app/services/ai_context.py
from anthropic import Anthropic

class AIContextEngine:
    """
    Stage-specific AI code generation (Claude, GPT-4o, Gemini).
    """

    def __init__(self):
        self.claude = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

    async def generate_content(
        self,
        stage: str,  # WHY, WHAT, HOW, BUILD, TEST, DEPLOY, OPERATE
        component: str,  # "Gate Engine", "Evidence Vault", etc.
        context: Dict
    ) -> str:
        """
        Generate stage-specific content (code, docs, tests).

        Example:
        - Stage HOW + component "Gate Engine" → architecture diagram
        - Stage BUILD + component "Gate Engine" → FastAPI code
        - Stage TEST + component "Gate Engine" → pytest test cases
        """
        system_prompt = self._get_stage_prompt(stage)

        response = await self.claude.messages.create(
            model="claude-sonnet-4-5-20250929",
            max_tokens=4096,
            system=system_prompt,
            messages=[{
                "role": "user",
                "content": f"Generate {component} for {stage} stage. Context: {context}"
            }]
        )

        return response.content[0].text

    def _get_stage_prompt(self, stage: str) -> str:
        """Stage-specific system prompts."""
        prompts = {
            "WHY": "You are a Design Thinking expert helping validate problems...",
            "WHAT": "You are a Product Manager defining requirements...",
            "HOW": "You are a Senior Architect designing systems...",
            "BUILD": "You are a Senior Engineer writing production code...",
            # ... (see AI Context section)
        }
        return prompts[stage]
```

**License**: Apache-2.0 (Proprietary)

---

### Layer 3: Integration (Thin Wrapper)

**Purpose**: Minimal abstraction layer over OSS infrastructure.

**Principles**:
- ✅ Network-only communication (HTTP, S3, GraphQL)
- ✅ NO SDK imports (`import minio`, `import grafana`)
- ✅ Apache-2.0 licensed (releasable if challenged)

**Components**:

**1. OPA Service** (`opa_service.py`):
```python
# app/integrations/opa_service.py
import httpx

class OPAService:
    """Thin wrapper around OPA HTTP API."""

    async def evaluate_policy(self, policy: str, input_data: Dict) -> bool:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "http://opa:8181/v1/data/gates/allow",
                json={"input": input_data}
            )
        return response.json()["result"]
```

**2. MinIO Service** (`minio_service.py`):
```python
# app/integrations/minio_service.py
import httpx

class MinIOService:
    """
    Thin wrapper around MinIO S3 API.

    Note: MinIO migrated to AI-Platform shared service (Jan 08, 2026)
    Container: ai-platform-minio on ai-net network
    S3 API: localhost:9020 (host) / ai-platform-minio:9000 (container)
    """

    async def upload_file(self, bucket: str, object_name: str, file: BinaryIO):
        async with httpx.AsyncClient() as client:
            await client.put(
                f"http://ai-platform-minio:9000/{bucket}/{object_name}",
                data=file
            )
```

**3. Grafana Service** (`grafana_service.py`):
```python
# app/integrations/grafana_service.py
import httpx

class GrafanaService:
    """Thin wrapper around Grafana HTTP API."""

    async def get_dashboard_url(self, dashboard_uid: str) -> str:
        return f"http://grafana:3000/d/{dashboard_uid}?kiosk"
```

**License**: Apache-2.0 (Proprietary, but releasable)

---

### Layer 4: Infrastructure (OSS)

**Purpose**: Battle-tested OSS components for infrastructure.

**Components**:

| Component | Version | License | Port | Purpose |
|-----------|---------|---------|------|---------|
| **OPA** | 0.58.0 | Apache-2.0 | 8181 | Policy engine |
| **MinIO** | Latest | AGPL v3 | 9020 (host) / 9000 (container) | S3-compatible storage (AI-Platform shared) |
| **Grafana** | 10.2.0 | AGPL v3 | 3000 | Dashboards |
| **PostgreSQL** | 15.5 | PostgreSQL | 5432 | Primary database |
| **Redis** | 7.2 | BSD-3 | 6379 | Cache + sessions |

**AGPL Containment**: See [AGPL-Containment-Strategy.md](../../01-Planning-Analysis/05-Legal-Compliance/AGPL-Containment-Strategy.md)

---

## 3. Bridge-First Strategy

### 3.1 What is Bridge-First?

**Problem**: We're a governance layer, NOT a replacement for GitHub/Jira/Linear.

**Solution**: Read & display from existing tools, enforce gates, audit & report.

**Architecture**:
```
┌─────────────────────────────────────────────────────────┐
│ SDLC Orchestrator (Governance Layer)                   │
│ - Read GitHub Issues/Projects (read-only sync)         │
│ - Enforce quality gates (policy checks)                │
│ - Audit compliance (evidence vault)                    │
│ - Report metrics (DORA dashboards)                     │
└─────────────────┬───────────────────────────────────────┘
                  │ (GitHub API - read-only)
                  ↓
┌─────────────────────────────────────────────────────────┐
│ Customer's Existing Tools                              │
│ - GitHub Issues (work management)                      │
│ - GitHub Projects (roadmap)                            │
│ - GitHub Actions (CI/CD)                               │
│ - GitHub PRs (code review)                             │
└─────────────────────────────────────────────────────────┘
```

### 3.2 Bridge Integration (GitHub)

**GitHub API Integration**:
```python
# app/integrations/github_service.py
from github import Github

class GitHubBridge:
    """
    Read-only sync from GitHub Issues/Projects.
    """

    def __init__(self, access_token: str):
        self.github = Github(access_token)

    async def sync_issues(self, repo: str) -> List[Dict]:
        """
        Sync GitHub Issues to SDLC Orchestrator.

        Mapping:
        - GitHub Issue → SDLC Orchestrator Task
        - GitHub Label "stage:WHAT" → Stage 01
        - GitHub Label "gate:G1" → Gate G1
        """
        repo_obj = self.github.get_repo(repo)
        issues = repo_obj.get_issues(state="all")

        tasks = []
        for issue in issues:
            task = {
                "id": f"github-{issue.number}",
                "title": issue.title,
                "description": issue.body,
                "stage": self._extract_stage(issue.labels),
                "gate": self._extract_gate(issue.labels),
                "status": "open" if issue.state == "open" else "closed",
                "assignees": [a.login for a in issue.assignees],
                "created_at": issue.created_at,
                "updated_at": issue.updated_at
            }
            tasks.append(task)

        return tasks

    def _extract_stage(self, labels) -> str:
        """Extract stage from labels (e.g., 'stage:WHAT' → 'WHAT')."""
        for label in labels:
            if label.name.startswith("stage:"):
                return label.name.split(":")[1]
        return None

    def _extract_gate(self, labels) -> str:
        """Extract gate from labels (e.g., 'gate:G1' → 'G1')."""
        for label in labels:
            if label.name.startswith("gate:"):
                return label.name.split(":")[1]
        return None
```

**Why Bridge-First?**
- ✅ **No migration required**: Customers keep using GitHub
- ✅ **Lower adoption barrier**: Add-on, not replacement
- ✅ **Faster time-to-value**: No data migration, instant value
- ❌ **Limited control**: Can't enforce workflow changes in GitHub

**Future: Native Board** (v2.0+)
- If customers need deeper enforcement (e.g., block PR merge if gate fails)
- Offer native board (replace GitHub Issues with SDLC Orchestrator Tasks)
- Migration tool: GitHub Issues → SDLC Orchestrator (one-click export)

---

## 11. AI Governance Layer

*(Added in v2.0.0 - December 3, 2025)*

### 11.1 Overview

AI Governance Layer encodes "CEO's brain" into SDLC Orchestrator, enabling any PM/Tech Lead to achieve CEO-level governance effectiveness.

```
┌─────────────────────────────────────────────────────────────────┐
│ AI GOVERNANCE LAYER (NEW in v2.0.0)                            │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────┐  │
│  │ Context-Aware    │  │ AI Task          │  │ Planning     │  │
│  │ Requirements     │  │ Decomposition    │  │ Hierarchy    │  │
│  │ Engine           │  │ Service          │  │ Manager      │  │
│  │ (ADR-011)        │  │ (ADR-012)        │  │ (ADR-013)    │  │
│  └────────┬─────────┘  └────────┬─────────┘  └──────┬───────┘  │
│           │                     │                    │          │
│           └─────────────────────┼────────────────────┘          │
│                                 │                               │
│                    ┌────────────┴────────────┐                  │
│                    │ AI Gateway (ADR-007)    │                  │
│                    │ Ollama → Claude → GPT-4 │                  │
│                    └────────────┬────────────┘                  │
│                                 │                               │
│  ┌──────────────────────────────┴───────────────────────────┐  │
│  │ SDLC Structure Validator (ADR-014)                       │  │
│  │ - CLI Tool: sdlc-validate                                │  │
│  │ - Pre-commit hook                                        │  │
│  │ - CI/CD GitHub Actions                                   │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### 11.2 Core Components

#### 11.2.1 Context-Aware Requirements Engine (ADR-011)

**Purpose**: Dynamic requirement classification based on project context.

```yaml
Classification Tiers:
  MANDATORY (Red):    Cannot skip regardless of context
  RECOMMENDED (Yellow): Should do, skip with justification
  OPTIONAL (Gray):    Nice-to-have based on project scale

Context Dimensions:
  - Project Scale: small (1-5) | medium (6-20) | large (21-50) | enterprise (50+)
  - Team Structure: solo | small_team | cross_functional | distributed
  - Industry: general | finance | healthcare | government | education
  - Risk Profile: low | medium | high | critical
  - Dev Practices: methodology, maturity (CMM 1-5), release cadence, tech ecosystem
```

**Example**: Healthcare project (industry=healthcare) automatically upgrades security gates to MANDATORY.

#### 11.2.2 AI Task Decomposition Service (ADR-012)

**Purpose**: Decompose user stories into tasks with CEO-level quality.

```yaml
Input:
  - User story (As a / I want / So that)
  - Project context (tech stack, team size, stage)

Output:
  - Structured task list
  - Estimates (hours, complexity)
  - Acceptance criteria
  - Dependencies

Performance:
  - CEO: 10 min → 8-12 tasks
  - AI: 2 min → 8-12 tasks (same quality)
  - Average PM: 30-45 min → 5-8 tasks (lower quality)
```

#### 11.2.3 4-Level Planning Hierarchy (ADR-013)

**Purpose**: Structure planning from vision to daily tasks.

```
Level 1: ROADMAP (Vision - 1-3 years)
  └─ Level 2: PHASE (Quarter - 3 months)
       └─ Level 3: SPRINT (Week - 1-2 weeks)
            └─ Level 4: BACKLOG (Day - Tasks/Issues)
```

**Traceability**: Every code commit traces back to business vision.

```
Commit → Task → Sprint → Phase → Roadmap → Vision
```

#### 11.2.4 SDLC Structure Validator (ADR-014)

**Purpose**: Enforce SDLC 5.1.3.1 folder structure across all projects.

```yaml
Level-Based Validation:
  Small (Level 0-1):   Stage folders only
  Medium (Level 0-2):  + Category subfolders
  Large (Level 0-3):   + Detail sub-subfolders

Tools:
  - sdlc-validate CLI
  - .sdlc-config.json schema
  - Pre-commit hook
  - GitHub Actions workflow
```

### 11.3 Integration with Existing Layers

```
┌─────────────────────────────────────────────────────────────────┐
│ LAYER 2: BUSINESS LOGIC                                        │
│                                                                  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐  │
│  │ Gate Engine  │  │ Evidence     │  │ AI Governance Layer  │  │
│  │ Service      │←─┤ Vault API    │←─┤ - Requirements Engine│  │
│  │              │  │              │  │ - Task Decomposition │  │
│  │              │  │              │  │ - Planning Hierarchy │  │
│  └──────────────┘  └──────────────┘  └──────────────────────┘  │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

**Data Flow**:
1. Project created → Requirements Engine calculates applicable requirements
2. User story entered → Task Decomposition generates tasks
3. Tasks approved → Synced to GitHub Issues (bridge pattern)
4. Sprint completed → Traceability chain updated

### 11.4 Related ADRs

| ADR | Title | Status |
|-----|-------|--------|
| [ADR-007](Architecture-Decisions/ADR-007-AI-Context-Engine.md) | AI Context Engine | APPROVED |
| [ADR-011](Architecture-Decisions/ADR-011-Context-Aware-Requirements.md) | Context-Aware Requirements | APPROVED |
| [ADR-012](Architecture-Decisions/ADR-012-AI-Task-Decomposition.md) | AI Task Decomposition | APPROVED |
| [ADR-013](Architecture-Decisions/ADR-013-Planning-Hierarchy.md) | 4-Level Planning Hierarchy | APPROVED |
| [ADR-014](Architecture-Decisions/ADR-014-SDLC-Structure-Validator.md) | SDLC Structure Validator | APPROVED |

---

---

## 12. EP-06 Codegen Layer

*(Added in v3.0.0 - December 23, 2025)*

### 12.1 Overview

EP-06 Codegen Layer is the **Software 3.0** extension that transforms SDLC Orchestrator from a governance platform into a **Control Plane for AI Coders**.

```
┌─────────────────────────────────────────────────────────────────┐
│ EP-06 CODEGEN LAYER (NEW in v3.0.0)                             │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────┐  │
│  │ IR Processor     │  │ Multi-Provider   │  │ Quality      │  │
│  │ Service          │  │ Codegen Gateway  │  │ Gate Engine  │  │
│  │ (Sprint 46)      │  │ (Sprint 45)      │  │ (Sprint 48)  │  │
│  └────────┬─────────┘  └────────┬─────────┘  └──────┬───────┘  │
│           │                     │                    │          │
│           └─────────────────────┼────────────────────┘          │
│                                 │                               │
│                    ┌────────────┴────────────┐                  │
│                    │ Validation Loop         │                  │
│                    │ Orchestrator            │                  │
│                    │ (max_retries=3)         │                  │
│                    └────────────┬────────────┘                  │
│                                 │                               │
│  ┌──────────────────────────────┴───────────────────────────┐  │
│  │ Evidence State Machine (8 states)                        │  │
│  │ generated → validating → retrying → escalated →          │  │
│  │ evidence_locked → awaiting_vcr → merged/aborted          │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### 12.2 Core Components

#### 12.2.1 IR Processor Service

**Purpose**: Parse and decompose IR (Intermediate Representation) modules for code generation.

```python
# backend/app/services/codegen/ir_processor.py

class IRProcessor:
    """
    IR Decomposition: 128K tokens → 5K tokens (96% context reduction)
    """

    async def parse_ir_module(self, ir_content: dict) -> ParsedIRModule:
        """
        Parse IR module into smaller, context-efficient units.

        Args:
            ir_content: Raw IR specification in JSON format

        Returns:
            ParsedIRModule with entities, routes, services, schemas
        """
        pass

    async def estimate_tokens(self, module: ParsedIRModule) -> int:
        """Estimate token count for context budgeting."""
        pass

    async def resolve_dependencies(self, modules: List[ParsedIRModule]) -> List[ParsedIRModule]:
        """Topological sort for generation order."""
        pass
```

**Database Table**: `ir_modules` (see Data Model ERD v3.1.0)

#### 12.2.2 Multi-Provider Codegen Gateway

**Purpose**: Route code generation requests to optimal AI provider with fallback.

```python
# backend/app/services/codegen/provider_gateway.py

class ProviderGateway:
    """
    Multi-Provider Fallback: Ollama → Claude → DeepCode (Q2 2026)
    """

    PROVIDER_CHAIN = [
        ("ollama", "qwen2.5-coder:32b", 15),   # Primary, <15s latency
        ("claude", "claude-sonnet-4-5-20250929", 25),  # Fallback 1, <25s
        ("deepcode", "deepcode-v1", None),     # Fallback 2, Q2 2026
    ]

    async def generate_code(
        self,
        ir_module: ParsedIRModule,
        provider_preference: str = "auto"
    ) -> GeneratedCode:
        """
        Generate code with automatic provider fallback.

        Args:
            ir_module: Parsed IR module to generate code for
            provider_preference: auto | ollama | claude | deepcode

        Returns:
            GeneratedCode with provider metadata
        """
        for provider, model, timeout in self.PROVIDER_CHAIN:
            if provider_preference != "auto" and provider != provider_preference:
                continue

            try:
                return await self._call_provider(provider, model, ir_module, timeout)
            except ProviderTimeoutError:
                continue  # Try next provider
            except ProviderQuotaError:
                continue  # Try next provider

        raise AllProvidersFailedError("All providers failed")
```

**Cost Optimization** (ADR-007):
- Ollama (NQH AI Platform): $50/month, <15s latency
- Claude (Anthropic): $1000/month, <25s latency
- DeepCode (Q2 2026): TBD

#### 12.2.3 4-Gate Quality Pipeline

**Purpose**: Validate generated code before locking evidence.

```python
# backend/app/services/codegen/quality_gates.py

class QualityGatePipeline:
    """
    4-Gate Quality Pipeline:
    - Gate 1: Syntax Validation (ast.parse, ruff, tsc)
    - Gate 2: Security Validation (Semgrep SAST)
    - Gate 3: Architecture & Context Validation (5 CTX checks)
    - Gate 4: Test Validation (unit tests, Dockerized)
    """

    async def run_pipeline(
        self,
        code: GeneratedCode,
        ir_module: ParsedIRModule
    ) -> QualityGateResult:
        """
        Run 4-gate quality pipeline sequentially.

        Target: <30 seconds total for Gate 1-3
        """
        # Gate 1: Syntax (< 5s)
        gate_1 = await self._validate_syntax(code)
        if not gate_1.passed:
            return self._fail_early(gate_1, "syntax")

        # Gate 2: Security (< 10s)
        gate_2 = await self._validate_security(code)
        if not gate_2.passed:
            return self._fail_early(gate_2, "security")

        # Gate 3: Context (< 10s)
        gate_3 = await self._validate_context(code, ir_module)
        if not gate_3.passed:
            return self._fail_early(gate_3, "context")

        # Gate 4: Tests (< 60s, async, optional)
        gate_4 = await self._validate_tests(code)

        return QualityGateResult(
            passed=gate_4.passed,
            gates=[gate_1, gate_2, gate_3, gate_4],
            recommendation=self._get_recommendation(gate_4)
        )
```

**5 Context Alignment Checks (Gate 3)**:
| Check ID | Description | Target |
|----------|-------------|--------|
| CTX-01 | IR Module Coverage | <2s |
| CTX-02 | Entity-Schema Consistency | <3s |
| CTX-03 | Route-Module Binding | <3s |
| CTX-04 | Reference Existence | <3s |
| CTX-05 | API Shape vs IR | <4s |

#### 12.2.4 Validation Loop Orchestrator

**Purpose**: Orchestrate retry logic with deterministic feedback.

```python
# backend/app/services/codegen/validation_loop.py

class ValidationLoopOrchestrator:
    """
    Validation Loop: generate → validate → retry → escalate

    Configuration:
    - CODEGEN_MAX_RETRIES: 3 (default)
    - CODEGEN_ESCALATION_SLA_HOURS: 24 (default)
    - CODEGEN_ESCALATION_CHANNEL: council | human | abort
    """

    async def orchestrate(
        self,
        generation_id: UUID,
        ir_module: ParsedIRModule
    ) -> OrchestrationResult:
        """
        Main orchestration loop with state persistence.

        State Machine:
        generated → validating → retrying → escalated →
        evidence_locked → awaiting_vcr → merged/aborted
        """
        generation = await self._get_generation(generation_id)

        while generation.current_attempt <= generation.max_retries:
            # Generate code
            code = await self.provider_gateway.generate_code(ir_module)

            # Run quality gates
            result = await self.quality_pipeline.run_pipeline(code, ir_module)

            # Log attempt
            await self._log_attempt(generation, code, result)

            if result.passed:
                # Lock evidence
                return await self._lock_evidence(generation, code, result)

            # Prepare deterministic feedback for retry
            feedback = self._build_feedback(result)
            generation.current_attempt += 1

            if generation.current_attempt > generation.max_retries:
                # Escalate
                return await self._escalate(generation, result)

            # Retry with feedback
            ir_module = self._augment_with_feedback(ir_module, feedback)

        return OrchestrationResult(status="max_retries_exceeded")
```

**Database Tables**: `codegen_generations`, `codegen_attempts`, `codegen_escalations`

#### 12.2.5 Evidence State Machine

**Purpose**: Track evidence lifecycle from generation to merge.

```
State Transitions:
┌──────────┐     ┌────────────┐     ┌──────────┐     ┌───────────┐
│ generated│────▶│ validating │────▶│ retrying │────▶│ escalated │
└──────────┘     └────────────┘     └──────────┘     └───────────┘
                                           │                │
                                           ▼                ▼
                                    ┌──────────────────────────┐
                                    │   evidence_locked        │
                                    └────────────┬─────────────┘
                                                 │
                                                 ▼
                                    ┌─────────────────────────┐
                                    │    awaiting_vcr         │
                                    └────────────┬────────────┘
                                                 │
                                    ┌────────────┴────────────┐
                                    ▼                         ▼
                              ┌──────────┐             ┌──────────┐
                              │  merged  │             │ aborted  │
                              └──────────┘             └──────────┘
```

**Database Tables**: `codegen_evidence`, `vcr_requests`

### 12.3 API Endpoints (12 new)

| Method | Path | Description |
|--------|------|-------------|
| POST | `/codegen/generate` | Initiate code generation |
| GET | `/codegen/{id}/status` | Poll generation status |
| GET | `/codegen/{id}/attempts` | List generation attempts |
| POST | `/codegen/{id}/retry` | Manual retry |
| POST | `/codegen/{id}/escalate` | Manual escalation |
| GET | `/codegen/escalations` | List pending escalations |
| GET | `/codegen/escalations/{id}` | Get escalation details |
| POST | `/codegen/escalations/{id}/resolve` | Resolve escalation |
| GET | `/codegen/evidence` | List codegen evidence |
| GET | `/codegen/evidence/{id}` | Get evidence details |
| POST | `/codegen/evidence/{id}/vcr` | Initiate VCR workflow |
| GET | `/codegen/metrics` | Prometheus metrics |

**Total API Endpoints**: 64 (52 original + 12 EP-06)

### 12.4 Observability (7 Prometheus Metrics)

| Metric | Type | Labels |
|--------|------|--------|
| `codegen_attempts_total` | Counter | provider, status |
| `codegen_retry_count` | Histogram | provider |
| `codegen_gate_failures_total` | Counter | gate, reason |
| `codegen_latency_seconds` | Histogram | provider, mode |
| `codegen_evidence_state` | Gauge | state |
| `codegen_escalation_queue_size` | Gauge | channel |
| `codegen_provider_cost_usd` | Counter | provider |

### 12.5 Related Documents

| Document | Description |
|----------|-------------|
| [Quality-Gates-Codegen-Specification.md](../14-Technical-Specs/Quality-Gates-Codegen-Specification.md) | Sprint 48 technical spec |
| [IR-Processor-Specification.md](../14-Technical-Specs/IR-Processor-Specification.md) | Sprint 46 technical spec |
| [Vietnamese-Domain-Templates-Specification.md](../14-Technical-Specs/Vietnamese-Domain-Templates-Specification.md) | Sprint 47 templates |
| [EP-06-IR-Based-Codegen-Engine.md](../../01-planning/02-Epics/EP-06-IR-Based-Codegen-Engine.md) | Epic specification |
| [Data-Model-ERD.md](../../01-planning/04-Data-Model/Data-Model-ERD.md) | Database schema v3.1.0 |
| [API-Specification.md](../../01-planning/05-API-Design/API-Specification.md) | API endpoints v3.1.0 |

### 12.6 CTO 10-Point Definition of Done (Sprint 48)

| # | Checkpoint | Target |
|---|------------|--------|
| 1 | 4 Gate Modules Exist | ✓ syntax, security, context, tests |
| 2 | All Gates Executable | Unit test per gate |
| 3 | Orchestrator Routes Correctly | Integration test |
| 4 | Retry with Deterministic Feedback | Feedback schema frozen |
| 5 | Escalation Pathway | council/human/abort |
| 6 | Evidence Locking | SHA-256 hash, immutable |
| 7 | State Machine Implemented | 8 states, transitions logged |
| 8 | Prometheus Metrics | 7 metrics scraped |
| 9 | Vietnamese Error Messages | All gate feedback Vietnamese |
| 10 | Audit Trail Complete | All attempts logged with context |

---

*End of System Architecture Document v3.0.0*