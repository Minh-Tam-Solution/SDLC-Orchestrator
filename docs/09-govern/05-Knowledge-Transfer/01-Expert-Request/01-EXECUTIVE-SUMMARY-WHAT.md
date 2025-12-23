# SDLC Orchestrator - Executive Summary: WHAT
## Stage 01: Planning - Requirements, Features & Specifications

**Version**: 1.0.0
**Date**: December 23, 2025
**Purpose**: External Expert Review - Product Specification & Feature Scope
**Confidentiality**: For Review Only - Not for Distribution
**Framework**: SDLC 5.1.1 Complete Lifecycle
**Company**: NQH Holdings (Vietnam-based software company)

---

## 1. About This Document

This is a **self-contained executive summary** designed for external experts to review and critique SDLC Orchestrator's product specification, feature scope, and technical requirements.

### Understanding the Two Components

| Component | Description |
|-----------|-------------|
| **SDLC-Enterprise-Framework** | The **methodology** - defines the 10 stages, quality gates, and principles that teams should follow. Open source, tool-agnostic. |
| **SDLC Orchestrator** | The **tool** - implements the Framework with automation, UI, and integrations. This document specifies WHAT the tool should do. |

**This document focuses on**: WHAT features SDLC Orchestrator provides to automate and enforce SDLC-Enterprise-Framework.

**Review Focus Areas**:
- Functional requirements completeness
- Non-functional requirements feasibility
- API design patterns
- Data model appropriateness
- Feature prioritization

---

## 2. Product Overview

### 2.1 Product Definition

**SDLC Orchestrator** is an **AI-Native SDLC Governance & Safety Platform** that:
- **Validates** AI-generated code before merge (Cursor, Copilot, Claude Code)
- **Enforces** quality gates across the 10-stage SDLC lifecycle
- **Collects** evidence automatically for compliance (SOC 2, ISO 27001)
- **Orchestrates** multi-approval workflows for critical decisions

### 2.2 Target Users

| User Role | Primary Use Cases | Daily Interaction |
|-----------|-------------------|-------------------|
| **Engineering Manager** | Monitor gate status, approve releases, view dashboards | 30-60 min/day |
| **Developer** | Submit evidence, pass gates, use AI assistance | Throughout development |
| **Product Manager** | Track feature validation, view adoption metrics | 15-30 min/day |
| **CTO/VP Engineering** | Executive dashboards, compliance reports, policy management | Weekly/monthly |
| **Auditor** (External) | Access evidence vault, generate compliance reports | During audits |

### 2.3 Integration Points

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         SDLC Orchestrator                               │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐                 │
│  │ Web Dashboard│    │ VS Code Ext │    │    CLI      │                 │
│  │  (React)     │    │ (Extension) │    │ (sdlcctl)   │                 │
│  └──────┬──────┘    └──────┬──────┘    └──────┬──────┘                 │
│         │                  │                  │                         │
│         └──────────────────┼──────────────────┘                         │
│                            ↓                                            │
│                    ┌───────────────┐                                    │
│                    │   FastAPI     │                                    │
│                    │   Backend     │                                    │
│                    └───────┬───────┘                                    │
│                            │                                            │
└────────────────────────────┼────────────────────────────────────────────┘
                             │
        ┌────────────────────┼────────────────────┐
        ↓                    ↓                    ↓
┌───────────────┐    ┌───────────────┐    ┌───────────────┐
│    GitHub     │    │   Jira/Linear │    │  Slack/Teams  │
│   (Primary)   │    │   (Optional)  │    │  (Webhooks)   │
└───────────────┘    └───────────────┘    └───────────────┘
```

---

## 3. Functional Requirements

### 3.1 Requirements Overview

We have defined **20 Functional Requirements (FR1-FR20)** organized into 6 capability groups:

| Group | Requirements | Status | Priority |
|-------|--------------|--------|----------|
| **Authentication & Authorization** | FR1-FR3 | ✅ Implemented | P0 (Must-have) |
| **Gate Management** | FR4-FR6 | ✅ Implemented | P0 (Must-have) |
| **Evidence Vault** | FR7-FR9 | ✅ Implemented | P0 (Must-have) |
| **Policy Engine** | FR10-FR12 | ✅ Implemented | P0 (Must-have) |
| **AI Engine** | FR13-FR15 | ✅ Implemented | P1 (Should-have) |
| **AI Governance** | FR16-FR20 | 🔄 In Progress | P1 (Should-have) |

### 3.2 FR1-FR3: Authentication & Authorization

#### FR1: User Authentication

| Aspect | Specification |
|--------|---------------|
| **Description** | Multi-method authentication with session management |
| **Methods** | Email/password, OAuth 2.0 (GitHub, Google, Microsoft), MFA (TOTP) |
| **Token Strategy** | JWT access tokens (1 hour), refresh tokens (30 days) |
| **Password Policy** | Minimum 12 characters, bcrypt with cost factor 12 |
| **MFA Requirement** | Mandatory for C-Suite roles, optional for others |

**User Stories**:
- As a developer, I can log in with my GitHub account so I don't need another password
- As an admin, I can enforce MFA for all users with elevated permissions
- As a user, I can reset my password via email verification

#### FR2: Role-Based Access Control (RBAC)

| Role | Level | Permissions |
|------|-------|-------------|
| **Viewer** | 1 | Read-only access to projects and gates |
| **Developer** | 2 | Submit evidence, view gate status |
| **QA Engineer** | 3 | Approve test gates (G3) |
| **Senior Engineer** | 4 | Approve design gates (G2), code review |
| **Tech Lead** | 5 | Approve architecture gates, policy exceptions |
| **Engineering Manager** | 6 | Approve all engineering gates, team management |
| **Product Manager** | 7 | Approve product gates (G0.1, G0.2), roadmap |
| **Director** | 8 | Cross-team approval, budget decisions |
| **VP Engineering** | 9 | Department-wide policies |
| **CTO** | 10 | Emergency overrides, security policies |
| **CPO** | 11 | Product strategy approval |
| **CEO** | 12 | Final approval authority, emergency veto |
| **Platform Admin** | 13 | System configuration, user management |

**Permission Matrix** (Gate Approval):

| Role | G0.1 | G0.2 | G1 | G2 | G3 | G4 |
|------|------|------|----|----|----|----|
| Developer | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| Senior Engineer | ❌ | ❌ | ❌ | ✅ | ✅ | ❌ |
| Tech Lead | ❌ | ❌ | ✅ | ✅ | ✅ | ✅ |
| Engineering Manager | ❌ | ❌ | ✅ | ✅ | ✅ | ✅ |
| Product Manager | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ |
| CTO | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |

#### FR3: API Key Management

| Feature | Specification |
|---------|---------------|
| **Key Generation** | Cryptographically secure, SHA-256 hashed storage |
| **Scopes** | `read:gates`, `write:evidence`, `admin:policies`, etc. |
| **Rotation** | 90-day recommended, forced rotation for compromised keys |
| **Rate Limiting** | 100/1K/10K requests per hour by tier |

### 3.3 FR4-FR6: Gate Management

#### FR4: Gate Definition & Configuration

**10 Quality Gates** (aligned with SDLC 5.1.1):

| Gate | Stage | Name | Required Evidence | Approvers |
|------|-------|------|-------------------|-----------|
| **G0.1** | 00 | Problem Definition | User interviews (3+), pain point severity | PM + Stakeholder |
| **G0.2** | 00 | Solution Diversity | 100+ ideas brainstorm, top 3 prototypes | PM + Design Lead |
| **G1** | 01 | Requirements Complete | PRD, user stories, acceptance criteria | PM + Tech Lead |
| **G2** | 02 | Design Ready | Architecture doc, ADRs, security review | CTO + Tech Lead |
| **G3** | 04-05 | Ship Ready | Code review, test coverage >90%, security scan pass | EM + QA Lead |
| **G4** | 06 | Deploy Approved | Runbook, rollback plan, on-call schedule | EM + SRE |
| **G5** | 07 | Production Stable | 99.9% uptime (7 days), no P0/P1 bugs | EM + SRE |
| **G6** | 08 | Team Healthy | Retrospective complete, action items tracked | Scrum Master |
| **G7** | 09 | Compliance Verified | Audit evidence complete, sign-off obtained | Compliance + Legal |
| **G8** | 09 | Lessons Captured | Post-mortem (if incidents), knowledge base updated | EM |

#### FR5: Gate Evaluation

| Feature | Specification |
|---------|---------------|
| **Evaluation Method** | Policy-as-Code (OPA Rego) + Human approval |
| **Automation Level** | Automated checks + manual approval workflow |
| **Blocking Behavior** | Configurable: Block, Warn, or Log-only |
| **Override Mechanism** | Emergency override with CTO approval + audit log |

**Evaluation Flow**:
```
Evidence Submitted → Policy Evaluation (OPA) → Human Review → Approval/Rejection
        ↓                    ↓                      ↓              ↓
    Stored in           PASS/FAIL/WARN          Comments        Gate Status
    Evidence Vault                              Captured         Updated
```

#### FR6: Multi-Approval Workflow

| Feature | Specification |
|---------|---------------|
| **Approval Modes** | Sequential (in order), Parallel (any order), Quorum (n of m) |
| **Escalation** | Auto-escalate after 48 hours if no response |
| **Delegation** | Approvers can delegate to deputies |
| **Notification** | Email + Slack/Teams webhooks |

### 3.4 FR7-FR9: Evidence Vault

#### FR7: Evidence Collection

| Collection Method | Description | Automation Level |
|-------------------|-------------|------------------|
| **Manual Upload** | User uploads files (PDF, PNG, JSON, MD) | Manual |
| **GitHub Integration** | Pull PR comments, reviews, test results | Automatic |
| **Webhook Capture** | Receive from CI/CD, Jira, Slack | Automatic |
| **VS Code Extension** | Capture from IDE (Cmd+Shift+E) | Semi-automatic |

**Supported Evidence Types**:

| Type | Format | Max Size | Use Case |
|------|--------|----------|----------|
| **Document** | PDF, DOCX, MD | 50MB | PRDs, design docs |
| **Image** | PNG, JPG, GIF | 10MB | Screenshots, wireframes |
| **Data** | JSON, CSV, YAML | 25MB | Test results, metrics |
| **Code** | ZIP, TAR.GZ | 100MB | Code snapshots |
| **Recording** | MP4, WEBM | 500MB | User interview recordings |

#### FR8: Evidence Integrity

| Security Feature | Implementation |
|------------------|----------------|
| **Hashing** | SHA-256 hash calculated on upload, verified on download |
| **Immutability** | Once stored, evidence cannot be modified (append-only) |
| **Chain of Custody** | Full audit trail: who uploaded, when, from where |
| **Encryption** | At-rest (AES-256), in-transit (TLS 1.3) |
| **Retention** | 7 years (SOC 2 requirement), configurable by policy |

#### FR9: Evidence Search & Retrieval

| Feature | Specification |
|---------|---------------|
| **Full-text Search** | Indexed search across all text-based evidence |
| **Metadata Filters** | By gate, project, date range, uploader, type |
| **Export** | Bulk export for auditors (ZIP with manifest) |
| **Access Control** | Project-scoped, role-based visibility |

### 3.5 FR10-FR12: Policy Engine

#### FR10: Policy-as-Code (OPA Integration)

| Feature | Specification |
|---------|---------------|
| **Engine** | Open Policy Agent (OPA) v0.58.0 |
| **Language** | Rego (OPA's native policy language) |
| **Deployment** | Containerized, network-only access (AGPL-safe) |
| **Evaluation** | <50ms p95 latency for typical policies |

**Example Policy** (No hardcoded secrets):
```rego
package sdlc.security

deny[msg] {
    input.file_content
    regex.match(`(api_key|password|secret)\s*=\s*["'][^"']+["']`, input.file_content)
    msg := sprintf("Hardcoded secret detected in %s", [input.file_path])
}
```

#### FR11: Policy Pack Management

| Feature | Specification |
|---------|---------------|
| **Built-in Packs** | AI Safety (17 rules), OWASP (23 rules), Architecture (10 rules) |
| **Custom Policies** | Users can write custom Rego policies |
| **Versioning** | Semantic versioning, rollback support |
| **Sharing** | Export/import between projects |

**Built-in Policy Packs**:

| Pack | Rules | Focus |
|------|-------|-------|
| **AI Safety** | 17 | Prompt injection, data leakage, unsafe models |
| **OWASP Python** | 23 | SQL injection, XSS, secrets, crypto |
| **Architecture Boundaries** | 10 | Layer separation, import restrictions |
| **Code Quality** | 15 | Complexity, duplication, naming |
| **Documentation** | 8 | Required files, format validation |

#### FR12: SAST Integration (Semgrep)

| Feature | Specification |
|---------|---------------|
| **Engine** | Semgrep (async subprocess execution) |
| **Output Format** | SARIF (Static Analysis Results Interchange Format) |
| **Scan Modes** | Full scan, incremental, PR-only, snippet |
| **Blocking** | ERROR findings block merge, WARNING allows with flag |

### 3.6 FR13-FR15: AI Engine

#### FR13: Multi-Provider AI

| Provider | Role | Latency | Cost | Use Case |
|----------|------|---------|------|----------|
| **Ollama** (Primary) | Local inference | <100ms | $50/month | Most requests, privacy-sensitive |
| **Claude** (Fallback 1) | Complex reasoning | 300ms | $1000/month | Complex documents, nuanced analysis |
| **GPT-4** (Fallback 2) | Code generation | 250ms | $800/month | Code-heavy tasks |
| **Rule-based** (Fallback 3) | Guaranteed | 50ms | $0 | When all AI fails |

**Fallback Chain**:
```
Request → Ollama (try) → Claude (try) → GPT-4 (try) → Rule-based (guaranteed)
             ↓               ↓              ↓               ↓
         Success?         Success?      Success?        Always succeeds
```

#### FR14: Stage-Aware AI Assistance

| Stage | AI Capability | Example Prompt |
|-------|---------------|----------------|
| **00 Foundation** | Problem analysis | "Analyze these interview transcripts for pain points" |
| **01 Planning** | User story generation | "Generate acceptance criteria for this feature" |
| **02 Design** | Architecture review | "Review this ADR for security concerns" |
| **04 Build** | Code review | "Analyze this PR for OWASP vulnerabilities" |
| **05 Test** | Test case generation | "Generate edge case tests for this function" |
| **07 Operate** | Runbook drafting | "Draft a runbook for this deployment" |

#### FR15: AI Detection Service

| Feature | Specification |
|---------|---------------|
| **Detection Accuracy** | 80% overall (validated on 500+ PRs) |
| **Precision** | 100% (no false positives) |
| **Recall** | 74.1% (catches 74% of AI-generated code) |
| **Latency** | 0.3ms p95 |

**Detection Strategies**:

| Strategy | Weight | Method |
|----------|--------|--------|
| **Metadata** | 40% | Git trailers, commit message patterns |
| **Commit Patterns** | 40% | Author timing, message structure |
| **Code Patterns** | 20% | Style analysis, comment patterns |

**Detected AI Tools**:
- Cursor AI
- GitHub Copilot
- Claude (Anthropic)
- ChatGPT (OpenAI)
- Windsurf
- Sourcegraph Cody
- Tabnine
- Other/Unknown

### 3.7 FR16-FR20: AI Governance (In Progress)

#### FR16: AI Task Decomposition

| Feature | Specification |
|---------|---------------|
| **Input** | User story or epic description |
| **Output** | Sub-tasks with estimates, dependencies, acceptance criteria |
| **Quality Target** | "CEO-level" quality (validated against CEO's patterns) |
| **Scoring** | Completeness, actionability, alignment (0-100 each) |

#### FR17: Context-Aware Requirements

| Feature | Specification |
|---------|---------------|
| **Classification** | MANDATORY (red), RECOMMENDED (yellow), OPTIONAL (gray) |
| **Context Dimensions** | Scale, team size, industry, risk profile, dev practices |
| **Filtering** | Auto-filter irrelevant requirements based on project profile |

**Context Matrix** (Example):

| Requirement | Startup (3 people) | Enterprise (100 people) |
|-------------|-------------------|------------------------|
| User interviews | MANDATORY | MANDATORY |
| Formal PRD | OPTIONAL | MANDATORY |
| Architecture ADR | RECOMMENDED | MANDATORY |
| Security audit | OPTIONAL | MANDATORY |
| Compliance review | OPTIONAL | MANDATORY |

#### FR18: 4-Level Planning Hierarchy

| Level | Scope | Typical Duration | Key Artifacts |
|-------|-------|------------------|---------------|
| **Roadmap** | Vision & strategy | 12 months | Quarterly milestones |
| **Phase** | Theme-based work | 4-8 weeks | Phase goals, success metrics |
| **Sprint** | Committed work | 1-2 weeks | Sprint backlog, burndown |
| **Backlog** | Individual tasks | Hours to days | Task estimates, acceptance criteria |

#### FR19: SDLC Structure Validator

| Feature | Specification |
|---------|---------------|
| **CLI Command** | `sdlcctl validate`, `sdlcctl fix`, `sdlcctl init` |
| **Pre-commit Hook** | Block commits that violate folder structure |
| **CI/CD Gate** | GitHub Action to enforce in pipelines |
| **Fix Mode** | Auto-fix common structure violations |

#### FR20: Evidence Timeline UI

| Feature | Specification |
|---------|---------------|
| **Timeline View** | Chronological view of all evidence events |
| **Filtering** | By validator, status, date range, AI tool |
| **Override Workflow** | Request, approve, reject override with comments |
| **Export** | CSV and JSON export for auditors |

---

## 4. Non-Functional Requirements

### 4.1 Performance Requirements

| Metric | Target | Achieved | Measurement |
|--------|--------|----------|-------------|
| **API Latency (p95)** | <100ms | ~80ms ✅ | Load testing (Locust) |
| **Dashboard Load** | <1s | <1s ✅ | Lighthouse |
| **Gate Evaluation** | <50ms | <50ms ✅ | OPA benchmarks |
| **Evidence Upload (10MB)** | <2s | <2s ✅ | E2E tests |
| **Concurrent Users** | 100K | Tested ✅ | Load testing |

### 4.2 Scalability Requirements

| Dimension | Target | Approach |
|-----------|--------|----------|
| **Users** | 100K concurrent | Horizontal scaling, connection pooling |
| **Projects** | 10K per tenant | Row-level security, indexed queries |
| **Evidence** | 1TB per tenant | Object storage (MinIO), lazy loading |
| **Policies** | 1000 per tenant | Policy caching, incremental evaluation |

### 4.3 Availability Requirements

| Metric | Target | Implementation |
|--------|--------|----------------|
| **Uptime** | 99.9% (8.76 hours downtime/year) | Multi-AZ deployment, health checks |
| **RTO** (Recovery Time Objective) | 4 hours | Automated failover, runbooks |
| **RPO** (Recovery Point Objective) | 1 hour | Hourly backups, transaction logs |

### 4.4 Security Requirements (OWASP ASVS Level 2)

| Category | Requirements | Status |
|----------|--------------|--------|
| **Authentication** | JWT, OAuth 2.0, MFA, password policy | ✅ 100% |
| **Authorization** | RBAC, row-level security, permission checks | ✅ 100% |
| **Cryptography** | TLS 1.3, bcrypt, SHA-256, AES-256 | ✅ 100% |
| **Data Protection** | Encryption at-rest, PII masking, audit logs | ✅ 100% |
| **Input Validation** | SQL injection, XSS, CSRF prevention | ✅ 100% |
| **Error Handling** | No stack traces in production, structured logging | ✅ 100% |
| **API Security** | Rate limiting, OpenAPI validation, CORS policy | ✅ 100% |

**Compliance**: 264/264 OWASP ASVS Level 2 requirements (98.4%)

### 4.5 Compliance Requirements

| Standard | Requirement | Implementation |
|----------|-------------|----------------|
| **SOC 2 Type 2** | Access control, audit logging, encryption | Evidence Vault, RBAC, audit logs |
| **ISO 27001** | Risk assessment, security controls | STRIDE threat model, OWASP ASVS |
| **GDPR** | Data minimization, right to erasure | User export, account deletion |
| **CCPA** | Privacy controls | Consent management, data access |

---

## 5. API Specification

### 5.1 API Overview

| Metric | Value |
|--------|-------|
| **Total Endpoints** | 52 |
| **OpenAPI Version** | 3.0.3 |
| **Authentication** | Bearer token (JWT) |
| **Rate Limiting** | Tier-based (100/1K/10K per hour) |
| **Versioning** | URL-based (`/api/v1/`) |

### 5.2 API Endpoint Categories

#### Authentication (3 endpoints)

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/auth/login` | Login with email/password |
| POST | `/api/v1/auth/refresh` | Refresh access token |
| POST | `/api/v1/auth/logout` | Revoke tokens |

#### Projects (5 endpoints)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/projects` | List user's projects |
| POST | `/api/v1/projects` | Create new project |
| GET | `/api/v1/projects/{id}` | Get project details |
| PUT | `/api/v1/projects/{id}` | Update project |
| DELETE | `/api/v1/projects/{id}` | Delete project |

#### Gates (6 endpoints)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/projects/{id}/gates` | List gates for project |
| GET | `/api/v1/gates/{id}` | Get gate details |
| POST | `/api/v1/gates/{id}/evaluate` | Evaluate gate policies |
| POST | `/api/v1/gates/{id}/approve` | Approve gate |
| POST | `/api/v1/gates/{id}/reject` | Reject gate |
| POST | `/api/v1/gates/{id}/override` | Emergency override |

#### Evidence (6 endpoints)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/gates/{id}/evidence` | List evidence for gate |
| POST | `/api/v1/evidence/upload` | Upload evidence file |
| GET | `/api/v1/evidence/{id}` | Get evidence details |
| GET | `/api/v1/evidence/{id}/download` | Download evidence file |
| DELETE | `/api/v1/evidence/{id}` | Delete evidence (soft) |
| POST | `/api/v1/evidence/search` | Search evidence |

#### Policies (8 endpoints)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/policy-packs` | List policy packs |
| POST | `/api/v1/policy-packs` | Create policy pack |
| GET | `/api/v1/policy-packs/{id}` | Get policy pack |
| PUT | `/api/v1/policy-packs/{id}` | Update policy pack |
| DELETE | `/api/v1/policy-packs/{id}` | Delete policy pack |
| POST | `/api/v1/policy-packs/evaluate` | Evaluate PR against policies |
| GET | `/api/v1/policy-packs/violations` | List violations |
| POST | `/api/v1/policy-packs/default` | Create default AI Safety pack |

#### SAST (7 endpoints)

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/sast/projects/{id}/scan` | Initiate SAST scan |
| POST | `/api/v1/sast/scan-snippet` | Scan code snippet |
| GET | `/api/v1/sast/projects/{id}/scans` | Get scan history |
| GET | `/api/v1/sast/projects/{id}/scans/{scan_id}` | Get scan details |
| GET | `/api/v1/sast/projects/{id}/trend` | Get findings trend |
| GET | `/api/v1/sast/projects/{id}/analytics` | Get SAST analytics |
| GET | `/api/v1/sast/health` | Health check |

#### Evidence Timeline (8 endpoints)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/projects/{id}/timeline` | List timeline with filters |
| GET | `/api/v1/projects/{id}/timeline/stats` | Get statistics |
| GET | `/api/v1/projects/{id}/timeline/{event_id}` | Get event detail |
| POST | `/api/v1/timeline/{event_id}/override/request` | Request override |
| POST | `/api/v1/timeline/{event_id}/override/approve` | Approve override |
| POST | `/api/v1/timeline/{event_id}/override/reject` | Reject override |
| GET | `/api/v1/admin/override-queue` | Admin queue view |
| GET | `/api/v1/projects/{id}/timeline/export` | Export CSV/JSON |

#### AI (9 endpoints)

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/ai/generate` | Generate content with AI |
| POST | `/api/v1/projects/{id}/decompose` | Decompose user story |
| GET | `/api/v1/decomposition-sessions/{id}/tasks` | Get decomposed tasks |
| POST | `/api/v1/ai/detect` | Detect AI-generated code |
| GET | `/api/v1/ai/providers` | List available providers |
| POST | `/api/v1/ai/validate` | Validate code with AI |
| GET | `/api/v1/ai/usage` | Get AI usage statistics |
| POST | `/api/v1/ai/feedback` | Submit AI quality feedback |
| GET | `/api/v1/ai/health` | AI service health check |

### 5.3 API Response Format

**Standard Success Response**:
```json
{
  "status": "success",
  "data": {
    "id": "proj_abc123",
    "name": "SDLC Orchestrator",
    "created_at": "2025-12-23T10:00:00Z"
  },
  "meta": {
    "request_id": "req_xyz789",
    "latency_ms": 45
  }
}
```

**Standard Error Response**:
```json
{
  "status": "error",
  "error": {
    "code": "GATE_NOT_FOUND",
    "message": "Gate with ID 'gate_123' not found",
    "details": {
      "gate_id": "gate_123",
      "project_id": "proj_abc"
    }
  },
  "meta": {
    "request_id": "req_xyz789"
  }
}
```

### 5.4 API Error Codes

| HTTP Code | Error Code | Description |
|-----------|------------|-------------|
| 400 | VALIDATION_ERROR | Invalid request parameters |
| 401 | UNAUTHORIZED | Missing or invalid token |
| 403 | FORBIDDEN | Insufficient permissions |
| 404 | NOT_FOUND | Resource not found |
| 409 | CONFLICT | Resource already exists |
| 429 | RATE_LIMITED | Too many requests |
| 500 | INTERNAL_ERROR | Server error |

---

## 6. Data Model

### 6.1 Entity Relationship Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              DATA MODEL                                      │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌──────────┐       ┌──────────┐       ┌──────────┐                        │
│  │  users   │──────<│ projects │>──────│  gates   │                        │
│  │          │  M:N  │          │  1:N  │          │                        │
│  └──────────┘       └──────────┘       └──────────┘                        │
│       │                   │                  │                              │
│       │                   │                  │                              │
│       ▼                   ▼                  ▼                              │
│  ┌──────────┐       ┌──────────┐       ┌──────────┐                        │
│  │  roles   │       │ webhooks │       │ evidence │                        │
│  └──────────┘       └──────────┘       └──────────┘                        │
│                                              │                              │
│                                              ▼                              │
│                                        ┌──────────┐                        │
│                                        │ policies │                        │
│                                        └──────────┘                        │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 6.2 Core Tables (24 Tables)

#### Authentication Layer (6 tables)

| Table | Purpose | Key Fields |
|-------|---------|------------|
| `users` | User accounts | id, email, password_hash, is_active, is_superuser |
| `roles` | Role definitions | id, name, level, permissions |
| `user_roles` | User-role mapping | user_id, role_id, project_id |
| `oauth_accounts` | OAuth connections | id, user_id, provider, provider_account_id |
| `refresh_tokens` | Token management | id, user_id, token_hash, expires_at |
| `api_keys` | API key management | id, user_id, key_hash, scopes, last_used_at |

#### Project Layer (3 tables)

| Table | Purpose | Key Fields |
|-------|---------|------------|
| `projects` | Project registry | id, name, repo_url, tier, settings |
| `project_members` | Team membership | project_id, user_id, role_id |
| `webhooks` | Integration hooks | id, project_id, url, events, secret |

#### Gate Engine Layer (5 tables)

| Table | Purpose | Key Fields |
|-------|---------|------------|
| `gates` | Gate definitions | id, project_id, gate_type, status, config |
| `gate_approvals` | Approval records | id, gate_id, user_id, decision, comment |
| `gate_evidence` | Evidence links | gate_id, evidence_id, required |
| `policy_evaluations` | Evaluation results | id, gate_id, policy_id, result, details |
| `stage_transitions` | Stage history | id, project_id, from_stage, to_stage, timestamp |

#### Policy Layer (3 tables)

| Table | Purpose | Key Fields |
|-------|---------|------------|
| `policy_packs` | Policy bundles | id, name, version, rego_code |
| `policy_rules` | Individual rules | id, pack_id, rule_id, severity |
| `policy_violations` | Violation records | id, project_id, rule_id, file_path, line |

#### Evidence Layer (3 tables)

| Table | Purpose | Key Fields |
|-------|---------|------------|
| `evidence` | Evidence records | id, project_id, type, file_path, hash |
| `evidence_metadata` | Extended metadata | evidence_id, key, value |
| `evidence_events` | Timeline events | id, evidence_id, event_type, timestamp |

#### AI Engine Layer (4 tables)

| Table | Purpose | Key Fields |
|-------|---------|------------|
| `ai_providers` | Provider config | id, name, endpoint, api_key_encrypted |
| `ai_requests` | Request logging | id, user_id, provider, prompt_tokens, response_tokens |
| `ai_detections` | Detection results | id, pr_id, is_ai_generated, confidence, tool |
| `decomposition_sessions` | Task decomposition | id, project_id, input, output, quality_score |

#### System Layer (2 tables)

| Table | Purpose | Key Fields |
|-------|---------|------------|
| `audit_logs` | Audit trail | id, user_id, action, resource_type, resource_id, timestamp |
| `notifications` | User notifications | id, user_id, type, message, read_at |

### 6.3 Key Relationships

| Relationship | Type | Description |
|--------------|------|-------------|
| users → projects | M:N | Users can belong to multiple projects |
| projects → gates | 1:N | Each project has 10 gates |
| gates → evidence | M:N | Gates require multiple evidence items |
| evidence → policy_evaluations | 1:N | Evidence evaluated by multiple policies |
| users → audit_logs | 1:N | Full audit trail per user |

---

## 7. Feature Prioritization

### 7.1 MoSCoW Analysis

| Priority | Features | Status |
|----------|----------|--------|
| **Must Have** (P0) | Authentication, Gates, Evidence Vault, Policy Engine | ✅ Complete |
| **Should Have** (P1) | AI Engine, AI Detection, SAST Integration | ✅ Complete |
| **Could Have** (P2) | AI Governance, Context-Aware Requirements | 🔄 In Progress |
| **Won't Have** (v1) | Native Jira integration, Mobile app | ⏳ Future |

### 7.2 Implementation Status

| Feature Group | Status | Sprint | Lines of Code |
|---------------|--------|--------|---------------|
| Authentication & RBAC | ✅ Complete | Sprint 1-5 | ~3,000 |
| Gate Management | ✅ Complete | Sprint 6-10 | ~4,500 |
| Evidence Vault | ✅ Complete | Sprint 11-15 | ~3,200 |
| Policy Engine (OPA) | ✅ Complete | Sprint 41-43 | ~3,500 |
| SAST Integration | ✅ Complete | Sprint 43 | ~4,400 |
| AI Detection | ✅ Complete | Sprint 42 | ~2,300 |
| Evidence Timeline UI | ✅ Complete | Sprint 43 | ~4,500 |
| AI Governance | 🔄 In Progress | Sprint 44+ | ~TBD |

---

## 8. Questions for Expert Review

### Requirements
1. **Completeness**: Are there critical functional requirements we've missed for a governance platform?
2. **Prioritization**: Is our MoSCoW prioritization appropriate for MVP?
3. **Scope Creep**: Are we trying to do too much in v1.0?

### API Design
4. **REST vs GraphQL**: Should we offer GraphQL for flexible querying?
5. **Versioning Strategy**: Is URL-based versioning (`/api/v1/`) the right approach?
6. **Pagination**: Is cursor-based pagination appropriate for our scale?

### Data Model
7. **Normalization**: Is our data model appropriately normalized for our use cases?
8. **Scalability**: Will this schema scale to 100K concurrent users?
9. **Multi-tenancy**: Is row-level security sufficient, or do we need schema-per-tenant?

### Non-Functional
10. **Performance Targets**: Are our latency and throughput targets realistic?
11. **Security**: Are there gaps in our OWASP ASVS Level 2 implementation?
12. **Compliance**: Are we missing any compliance requirements for enterprise customers?

---

## 9. Summary

**SDLC Orchestrator v1.0** delivers:
- **20 Functional Requirements** across 6 capability groups
- **52 API Endpoints** with full OpenAPI specification
- **24 Database Tables** supporting governance workflows
- **OWASP ASVS Level 2** security compliance (98.4%)
- **<100ms p95 latency** for all API operations

**Current Status**:
- Core features (P0/P1): ✅ Complete
- AI Governance (P2): 🔄 In Progress
- Production deployment: ✅ Ready

---

**Document Control**

| Field | Value |
|-------|-------|
| Author | PM/PJM Team, NQH Holdings |
| Reviewed By | CTO, Tech Lead |
| Status | Ready for External Review |
| Classification | Confidential - For Review Only |

---

*"Define WHAT we're building before HOW we build it."*
