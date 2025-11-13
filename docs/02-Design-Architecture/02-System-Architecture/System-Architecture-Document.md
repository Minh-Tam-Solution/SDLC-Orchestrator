# System Architecture Document
## 4-Layer Architecture + Bridge-First Design

**Version**: 1.0.0
**Date**: November 13, 2025
**Status**: ACTIVE - DRAFT
**Authority**: CTO + Tech Lead + Backend Lead
**Foundation**: Stage 01 (Requirements, API Specs, Data Model)
**Stage**: Stage 02 (HOW - Design & Architecture)
**Framework**: SDLC 4.9 Complete Lifecycle (10 Stages)

---

## Table of Contents

1. [Architecture Overview](#1-architecture-overview)
2. [4-Layer Architecture](#2-4-layer-architecture)
3. [Bridge-First Strategy](#3-bridge-first-strategy)
4. [Component Breakdown](#4-component-breakdown)
5. [Data Flow](#5-data-flow)
6. [Technology Stack](#6-technology-stack)
7. [Scalability Design](#7-scalability-design)
8. [Security Architecture](#8-security-architecture)
9. [Deployment Architecture](#9-deployment-architecture)
10. [Architecture Decisions (ADRs)](#10-architecture-decisions-adrs)

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
│  │ Port: 8181   │  │ Port: 9000   │  │ Port: 3000   │         │
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
    """Thin wrapper around MinIO S3 API."""

    async def upload_file(self, bucket: str, object_name: str, file: BinaryIO):
        async with httpx.AsyncClient() as client:
            await client.put(
                f"http://minio:9000/{bucket}/{object_name}",
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
| **MinIO** | Latest | AGPL v3 | 9000 | S3-compatible storage |
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

(Tiếp tục trong reply tiếp theo do giới hạn độ dài...)