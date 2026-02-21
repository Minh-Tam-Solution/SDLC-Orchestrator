# SDLC Orchestrator - Client Features Matrix

**Version:** 1.1.0
**Date:** January 22, 2026
**Status:** CTO Approved Design Document
**Owner:** Architecture Team
**Framework:** SDLC 6.1.0

---

## Sprint Progress Tracking

### Sprint 89 ✅ COMPLETED (Jan 21-22, 2026)
**Focus:** Pre-Launch Hardening - Security & Compliance

| Task | Status | Notes |
|------|--------|-------|
| MinIO Object Lock Configuration | ✅ | WORM compliance, 7-year retention |
| PostgreSQL Row-Level Security | ✅ | Multi-tenant isolation complete |
| Dynamic Context Engine | ✅ | AGENTS.md generation ready |
| Evidence Hash Chain | ✅ | SHA256 integrity verification |
| GitHub Check Run Integration | ✅ | CI/CD quality gates |

**Deliverables:**
- `backend/app/services/minio_service.py` - Object Lock WORM
- `backend/alembic/versions/*_rls_policies.py` - RLS for 30+ tables
- Pre-launch security checklist 100% complete

### Sprint 90 ✅ COMPLETED (Jan 22-23, 2026)
**Focus:** Project Creation Enhancement - Quick Win

| Task | Status | Notes |
|------|--------|-------|
| Team Selector in CreateProjectModal | ✅ | Using existing useTeams hook |
| GitHub Repo Selector | ✅ | Using existing useGitHub hook |
| Repository Analysis Display | ✅ | Language, visibility, branch, last update |
| CreateProjectRequest API Update | ✅ | Added team_id, github_repo_id |
| API Field Mapping Fix | ✅ | policy_pack_tier → policy_pack |
| E2E Tests | ✅ | 10/10 tests passing |

**Unlocked 7 Backend APIs:**
- ✅ GET /teams (Sprint 84)
- ✅ GET /github/status
- ✅ GET /github/repositories
- ✅ POST /github/sync
- ✅ GET /github/repositories/{owner}/{repo}/analyze
- ✅ POST /projects (with team_id, github_repo_id)
- ✅ GET /teams/{id}/projects

**Files Modified:**
- `frontend/src/lib/api.ts` - CreateProjectRequest interface + API mapping
- `frontend/src/app/app/projects/page.tsx` - CreateProjectModal enhanced
- `frontend/e2e/sprint90-project-creation.spec.ts` - E2E tests (NEW)

---

## 1. Executive Summary

SDLC Orchestrator cung cấp 4 client interfaces để phục vụ các use cases khác nhau:

| Client | Primary Use Case | Target Users | Status |
|--------|-----------------|--------------|--------|
| **Web Dashboard** | Full administration, analytics, governance | PM, Leads, CTO, Admins | ✅ Production |
| **CLI (sdlcctl)** | CI/CD integration, automation, scripting | DevOps, Developers | ✅ Production |
| **VSCode Extension** | In-IDE development workflow | Developers, AI Coders | ✅ Production |
| **Desktop App** | Offline-first, enterprise deployment | Enterprise teams | 🔮 Planned Q3 2026 |

---

## 2. Client Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         SDLC Orchestrator Backend                           │
│                              (297+ API Endpoints)                           │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐          │
│  │    Auth     │ │   Projects  │ │    Gates    │ │   Evidence  │          │
│  │  (9 APIs)   │ │  (5 APIs)   │ │  (6 APIs)   │ │  (10 APIs)  │          │
│  └─────────────┘ └─────────────┘ └─────────────┘ └─────────────┘          │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐          │
│  │   Teams     │ │  Planning   │ │  AGENTS.md  │ │   Codegen   │          │
│  │  (15 APIs)  │ │  (33 APIs)  │ │  (13 APIs)  │ │  (30 APIs)  │          │
│  └─────────────┘ └─────────────┘ └─────────────┘ └─────────────┘          │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐          │
│  │  Analytics  │ │  Compliance │ │    Admin    │ │   Payments  │          │
│  │  (4 APIs)   │ │  (14 APIs)  │ │  (10 APIs)  │ │  (5 APIs)   │          │
│  └─────────────┘ └─────────────┘ └─────────────┘ └─────────────┘          │
└─────────────────────────────────────────────────────────────────────────────┘
                    │              │              │              │
         ┌──────────┴──────────────┴──────────────┴──────────────┴──────────┐
         │                                                                   │
    ┌────▼────┐        ┌────▼────┐        ┌────▼────┐        ┌────▼────┐
    │   Web   │        │   CLI   │        │ VSCode  │        │ Desktop │
    │Dashboard│        │sdlcctl  │        │Extension│        │  App    │
    │(Next.js)│        │(Python) │        │  (TS)   │        │(Tauri)  │
    └─────────┘        └─────────┘        └─────────┘        └─────────┘
    Full Admin         Automation          In-IDE Dev        Offline-First
    + Analytics        + CI/CD             + AI Chat         + Enterprise
```

---

## 3. Features Matrix - Complete

### Legend

| Symbol | Meaning |
|--------|---------|
| ✅ | Implemented & Production Ready |
| 🔄 | In Progress |
| 📋 | Planned (Backlog) |
| ❌ | Not Planned (Out of Scope) |
| ⭐ | Recommended Primary Client |

---

### 3.1 Authentication & User Management

| Feature | Web | CLI | VSCode | Desktop | Notes |
|---------|-----|-----|--------|---------|-------|
| Email/Password Login | ✅⭐ | 📋 | ✅ | 📋 | CLI needs keychain |
| OAuth (GitHub) | ✅⭐ | 📋 | ✅ | 📋 | |
| OAuth (Google) | ✅⭐ | ❌ | ✅ | 📋 | |
| OAuth (Microsoft) | ✅⭐ | ❌ | ✅ | 📋 | Enterprise SSO |
| MFA (TOTP) | ✅⭐ | ❌ | ❌ | 📋 | Web only |
| API Key Auth | ✅ | 📋⭐ | ✅ | 📋 | CLI primary |
| Token Refresh | ✅ | 📋 | ✅ | 📋 | |
| Session Management | ✅⭐ | ❌ | ✅ | 📋 | |
| User Profile | ✅⭐ | ❌ | ✅ | 📋 | |
| Password Reset | ✅⭐ | ❌ | ❌ | 📋 | Web only |

---

### 3.2 Project Management

| Feature | Web | CLI | VSCode | Desktop | Notes |
|---------|-----|-----|--------|---------|-------|
| List Projects | ✅⭐ | 📋 | ✅ | 📋 | |
| Create Project | ✅⭐ | 📋 | ❌ | 📋 | Web primary |
| Update Project | ✅⭐ | 📋 | ❌ | 📋 | |
| Delete Project | ✅⭐ | ❌ | ❌ | 📋 | Admin only |
| Project Settings | ✅⭐ | ❌ | ❌ | 📋 | |
| Project Switcher | ✅ | ❌ | ✅⭐ | 📋 | VSCode sidebar |
| Project Dashboard | ✅⭐ | ❌ | ❌ | 📋 | |

---

### 3.3 Teams & Organizations (Sprint 71)

| Feature | Web | CLI | VSCode | Desktop | Notes |
|---------|-----|-----|--------|---------|-------|
| Create Team | 📋⭐ | ❌ | ❌ | 📋 | Sprint 84 |
| List Teams | 📋⭐ | 📋 | 📋 | 📋 | |
| Update Team | 📋⭐ | ❌ | ❌ | 📋 | |
| Delete Team | 📋⭐ | ❌ | ❌ | 📋 | |
| Add Team Member | 📋⭐ | ❌ | ❌ | 📋 | |
| Remove Team Member | 📋⭐ | ❌ | ❌ | 📋 | |
| Update Member Role | 📋⭐ | ❌ | ❌ | 📋 | SASE roles |
| Team Statistics | 📋⭐ | ❌ | 📋 | 📋 | |
| Team Switcher | 📋 | ❌ | 📋⭐ | 📋 | Quick switch |
| Create Organization | 📋⭐ | ❌ | ❌ | 📋 | |
| List Organizations | 📋⭐ | 📋 | ❌ | 📋 | |
| Organization Settings | 📋⭐ | ❌ | ❌ | 📋 | |
| Organization Stats | 📋⭐ | ❌ | ❌ | 📋 | |

---

### 3.4 Quality Gates

| Feature | Web | CLI | VSCode | Desktop | Notes |
|---------|-----|-----|--------|---------|-------|
| View Gate Status | ✅⭐ | 📋 | ✅⭐ | 📋 | |
| Gate Details | ✅⭐ | 📋 | ✅ | 📋 | |
| Evaluate Gate | ✅⭐ | 📋⭐ | ✅ | 📋 | CLI for CI/CD |
| Submit for Approval | ✅⭐ | ❌ | ❌ | 📋 | |
| Approve/Reject Gate | ✅⭐ | ❌ | ❌ | 📋 | Admin only |
| Gate History | ✅⭐ | ❌ | ❌ | 📋 | |
| G-Sprint Gate | 📋⭐ | 📋 | 📋 | 📋 | Sprint 74 |
| G-Sprint-Close Gate | 📋⭐ | 📋 | 📋 | 📋 | Sprint 74 |

---

### 3.5 Evidence Vault

| Feature | Web | CLI | VSCode | Desktop | Notes |
|---------|-----|-----|--------|---------|-------|
| Upload Evidence | ✅⭐ | 📋⭐ | 📋 | 📋 | All clients |
| List Evidence | ✅⭐ | 📋 | 📋 | 📋 | |
| View Evidence | ✅⭐ | 📋 | 📋 | 📋 | |
| Download Evidence | ✅⭐ | 📋 | ❌ | 📋 | |
| Evidence Search | ✅⭐ | 📋 | ❌ | 📋 | |
| Integrity Check | ✅⭐ | 📋⭐ | 📋 | 📋 | SHA256 verify |
| Evidence Timeline | ✅⭐ | ❌ | ❌ | 📋 | |
| Evidence Manifest | 📋⭐ | 📋 | 📋 | 📋 | Sprint 82 |
| Tamper-Evident View | 📋⭐ | 📋 | ❌ | 📋 | Hash chain |

---

### 3.6 AGENTS.md (Sprint 80-83) - TRUE MOAT

| Feature | Web | CLI | VSCode | Desktop | Notes |
|---------|-----|-----|--------|---------|-------|
| Generate AGENTS.md | 📋⭐ | ✅⭐ | 📋 | 📋 | CLI primary |
| View AGENTS.md | 📋⭐ | ✅ | 📋⭐ | 📋 | |
| Validate AGENTS.md | 📋 | ✅⭐ | 📋 | 📋 | CLI primary |
| Lint AGENTS.md | 📋 | ✅⭐ | 📋 | 📋 | Auto-fix |
| Dynamic Context Overlay | 📋⭐ | ✅ | 📋⭐ | 📋 | TRUE MOAT |
| Context History | 📋⭐ | ❌ | ❌ | 📋 | |
| Multi-Repo Dashboard | 📋⭐ | ❌ | ❌ | 📋 | Sprint 83 |
| Bulk Regenerate | 📋⭐ | 📋 | ❌ | 📋 | |
| Version Diff | 📋⭐ | ❌ | 📋 | 📋 | |

---

### 3.7 Planning Hierarchy (Sprint 74-77)

| Feature | Web | CLI | VSCode | Desktop | Notes |
|---------|-----|-----|--------|---------|-------|
| View Roadmap | 📋⭐ | ❌ | 📋 | 📋 | 12-month vision |
| Create/Edit Roadmap | 📋⭐ | ❌ | ❌ | 📋 | |
| View Phases | 📋⭐ | ❌ | 📋 | 📋 | |
| Create/Edit Phase | 📋⭐ | ❌ | ❌ | 📋 | |
| View Sprints | 📋⭐ | 📋 | 📋⭐ | 📋 | |
| Create Sprint | 📋⭐ | 📋 | ❌ | 📋 | |
| Sprint Detail | 📋⭐ | 📋 | 📋 | 📋 | |
| Sprint Analytics | 📋⭐ | ❌ | ❌ | 📋 | |
| Burndown Chart | 📋⭐ | ❌ | 📋 | 📋 | Visual |
| Sprint Forecast | 📋⭐ | ❌ | ❌ | 📋 | |
| View Backlog | 📋⭐ | 📋 | 📋⭐ | 📋 | |
| Create Backlog Item | 📋⭐ | 📋 | 📋 | 📋 | |
| Update Backlog Item | 📋⭐ | 📋 | 📋 | 📋 | |
| Bulk Move to Sprint | 📋⭐ | ❌ | ❌ | 📋 | |
| Retrospective | 📋⭐ | ❌ | ❌ | 📋 | |
| Retro Actions | 📋⭐ | ❌ | ❌ | 📋 | |

---

### 3.8 Code Generation (EP-06)

| Feature | Web | CLI | VSCode | Desktop | Notes |
|---------|-----|-----|--------|---------|-------|
| Blueprint Editor | ✅⭐ | ❌ | ✅⭐ | 📋 | Visual editor |
| Generate Code | ✅ | ✅⭐ | ✅⭐ | 📋 | Streaming |
| Magic Mode (NL) | ✅ | ✅⭐ | ✅⭐ | 📋 | Vietnamese support |
| 4-Gate Pipeline View | ✅⭐ | ✅ | ✅ | 📋 | Quality gates |
| Contract Lock | ✅ | ❌ | ✅⭐ | 📋 | VSCode primary |
| Contract Unlock | ✅ | ❌ | ✅⭐ | 📋 | |
| Generation History | ✅⭐ | 📋 | ❌ | 📋 | |
| Resume Generation | ✅ | 📋 | ✅⭐ | 📋 | Checkpoint |
| Preview Code | ✅ | ❌ | ✅⭐ | 📋 | |
| Download ZIP | ✅⭐ | ✅ | ❌ | 📋 | |
| Session Status | ✅⭐ | 📋 | ✅ | 📋 | |

---

### 3.9 Compliance & Policies

| Feature | Web | CLI | VSCode | Desktop | Notes |
|---------|-----|-----|--------|---------|-------|
| View Policies | ✅⭐ | ❌ | ❌ | 📋 | |
| Create Policy | ✅⭐ | ❌ | ❌ | 📋 | Admin |
| Policy Packs | ✅⭐ | ❌ | ❌ | 📋 | |
| SAST Scan | ✅⭐ | 📋 | ❌ | 📋 | |
| Compliance Scan | ✅⭐ | 📋⭐ | ✅ | 📋 | CLI for CI/CD |
| View Violations | ✅⭐ | 📋 | ✅⭐ | 📋 | VSCode inline |
| AI Fix Suggestion | ✅ | ❌ | ✅⭐ | 📋 | @gate /fix |
| Override Request | ✅⭐ | ❌ | ❌ | 📋 | |
| Override Approval | ✅⭐ | ❌ | ❌ | 📋 | Admin |
| VCR Workflow | ✅⭐ | ❌ | ❌ | 📋 | |

---

### 3.10 AI Features

| Feature | Web | CLI | VSCode | Desktop | Notes |
|---------|-----|-----|--------|---------|-------|
| AI Council Chat | ✅⭐ | ❌ | ✅⭐ | 📋 | @gate commands |
| Task Decomposition | ✅⭐ | ❌ | 📋 | 📋 | User story → tasks |
| AI Recommendations | ✅ | ❌ | ✅⭐ | 📋 | Violation fixes |
| Context-Aware Reqs | 📋⭐ | ❌ | 📋 | 📋 | Tier filtering |
| SOP Generation | ✅⭐ | ❌ | ❌ | 📋 | Web only |

---

### 3.11 Analytics & Reporting

| Feature | Web | CLI | VSCode | Desktop | Notes |
|---------|-----|-----|--------|---------|-------|
| Dashboard Stats | ✅⭐ | ❌ | ❌ | 📋 | |
| DAU Metrics | 📋⭐ | ❌ | ❌ | 📋 | Sprint 83 |
| AI Safety Metrics | 📋⭐ | ❌ | ❌ | 📋 | Sprint 83 |
| DORA Metrics | 📋⭐ | ❌ | ❌ | 📋 | |
| Export Reports | 📋⭐ | 📋 | ❌ | 📋 | PDF/Excel |
| SDLC Compliance Report | ✅ | ✅⭐ | ❌ | 📋 | CLI primary |

---

### 3.12 Administration

| Feature | Web | CLI | VSCode | Desktop | Notes |
|---------|-----|-----|--------|---------|-------|
| User Management | ✅⭐ | ❌ | ❌ | 📋 | Web only |
| Audit Logs | ✅⭐ | ❌ | ❌ | 📋 | |
| System Health | ✅⭐ | ❌ | ❌ | 📋 | |
| AI Provider Config | ✅⭐ | ❌ | ❌ | 📋 | |
| Billing/Payments | ✅⭐ | ❌ | ❌ | 📋 | |
| Override Queue | ✅⭐ | ❌ | ❌ | 📋 | |

---

### 3.13 SDLC Structure Validation

| Feature | Web | CLI | VSCode | Desktop | Notes |
|---------|-----|-----|--------|---------|-------|
| Validate Structure | ✅ | ✅⭐ | ✅ | 📋 | CLI primary |
| Auto-Fix Structure | ❌ | ✅⭐ | ❌ | 📋 | CLI only |
| Initialize Project | ❌ | ✅⭐ | ✅ | 📋 | |
| Migration (4.9→5.0) | ❌ | ✅⭐ | ❌ | 📋 | CLI only |
| Tier Classification | ✅ | ✅⭐ | ❌ | 📋 | |
| P0 Artifact Check | ✅ | ✅⭐ | ❌ | 📋 | |

---

### 3.14 Integrations

| Feature | Web | CLI | VSCode | Desktop | Notes |
|---------|-----|-----|--------|---------|-------|
| GitHub OAuth | ✅⭐ | ❌ | ✅ | 📋 | |
| GitHub Sync | ✅⭐ | ❌ | ❌ | 📋 | |
| GitHub Webhooks | ✅⭐ | ❌ | ❌ | 📋 | |
| Grafana Embed | ✅⭐ | ❌ | ❌ | 📋 | iframe |
| VNPay Payments | ✅⭐ | ❌ | ❌ | 📋 | Vietnam |
| Slack Notifications | 📋 | ❌ | ❌ | 📋 | Future |

---

### 3.15 Offline & Caching

| Feature | Web | CLI | VSCode | Desktop | Notes |
|---------|-----|-----|--------|---------|-------|
| Offline Mode | ❌ | ✅⭐ | ✅ | 📋⭐ | Desktop primary |
| Local Cache | ✅ | ✅ | ✅ | 📋⭐ | |
| Stale-While-Revalidate | ✅ | ❌ | ✅ | 📋 | |
| Local-First Sync | ❌ | ❌ | ❌ | 📋⭐ | Desktop feature |

---

## 4. Feature Distribution by Client

### 4.1 Summary Statistics

| Client | Total Features | Implemented | Planned | Not Planned | Coverage |
|--------|---------------|-------------|---------|-------------|----------|
| **Web Dashboard** | 150 | 80 | 65 | 5 | 53% → 97% |
| **CLI (sdlcctl)** | 150 | 20 | 45 | 85 | 13% → 43% |
| **VSCode Extension** | 150 | 55 | 40 | 55 | 37% → 63% |
| **Desktop App** | 150 | 0 | 120 | 30 | 0% → 80% |

### 4.2 Primary Client by Feature Category

| Category | Primary Client | Rationale |
|----------|---------------|-----------|
| Administration | Web ⭐ | Full UI, complex workflows |
| CI/CD Integration | CLI ⭐ | Scriptable, pipeline-friendly |
| Developer Workflow | VSCode ⭐ | In-IDE, context-aware |
| Offline/Enterprise | Desktop ⭐ | Local-first, security |
| Analytics | Web ⭐ | Charts, dashboards |
| Code Generation | VSCode/CLI ⭐ | Developer-centric |
| AGENTS.md | CLI ⭐ | Git integration |
| Team Management | Web ⭐ | Collaboration UI |
| Compliance | Web/CLI ⭐ | Both use cases |

---

## 5. Desktop App Vision (Q3 2026)

### 5.1 Technology Stack

| Component | Technology | Rationale |
|-----------|------------|-----------|
| Framework | Tauri 2.0 | Rust backend, small binary |
| Frontend | React + TailwindCSS | Code reuse from Web |
| Local DB | SQLite | Offline-first |
| Sync | CRDTs | Conflict-free sync |
| Security | OS Keychain | Secure credential storage |

### 5.2 Unique Features

| Feature | Description | Priority |
|---------|-------------|----------|
| **Offline-First** | Full functionality without network | P0 |
| **Local-First Sync** | Sync when online, work offline | P0 |
| **Enterprise Deploy** | MSI/PKG/DEB packages | P0 |
| **Air-Gapped Support** | No internet required | P1 |
| **Local AI** | Ollama integration | P1 |
| **Multi-Account** | Switch between accounts | P2 |
| **Auto-Update** | Silent background updates | P2 |

### 5.3 Desktop Roadmap

| Quarter | Focus | Features |
|---------|-------|----------|
| Q3 2026 | MVP | Auth, Projects, Gates, Evidence |
| Q4 2026 | Core | Teams, Planning, AGENTS.md |
| Q1 2027 | Advanced | Codegen, AI, Offline Sync |
| Q2 2027 | Enterprise | Air-gapped, Custom branding |

---

## 6. API Endpoint Coverage Matrix

### 6.1 By Category

```
API Category          Web    CLI    VSCode  Desktop
─────────────────────────────────────────────────────
Authentication        ████   ░░░░   ████    ░░░░
Projects              ████   ░░░░   ████    ░░░░
Teams                 ░░░░   ░░░░   ░░░░    ░░░░  ← GAP
Organizations         ░░░░   ░░░░   ░░░░    ░░░░  ← GAP
Gates                 ████   ░░░░   ████    ░░░░
Evidence              ████   ░░░░   ░░░░    ░░░░  ← CLI/VSCode GAP
Evidence Manifest     ░░░░   ░░░░   ░░░░    ░░░░  ← GAP
Policies              ████   ░░░░   ░░░░    ░░░░
Compliance            ████   ░░░░   ████    ░░░░
Override/VCR          ████   ░░░░   ░░░░    ░░░░
Planning              ░░░░   ░░░░   ░░░░    ░░░░  ← GAP
AGENTS.md             ░░░░   ██░░   ░░░░    ░░░░  ← GAP
Analytics             █░░░   ░░░░   ░░░░    ░░░░
Codegen               ████   ██░░   ████    ░░░░
AI Council            ████   ░░░░   ████    ░░░░
Admin                 ████   ░░░░   ░░░░    ░░░░
Payments              ████   ░░░░   ░░░░    ░░░░

Legend: ████ = 100%  ██░░ = 50%  █░░░ = 25%  ░░░░ = 0%
```

### 6.2 Target Coverage (Sprint 88)

```
API Category          Web    CLI    VSCode  Desktop
─────────────────────────────────────────────────────
Authentication        ████   ████   ████    ░░░░
Projects              ████   ████   ████    ░░░░
Teams                 ████   ░░░░   ██░░    ░░░░
Organizations         ████   ░░░░   ░░░░    ░░░░
Gates                 ████   ████   ████    ░░░░
Evidence              ████   ████   ████    ░░░░
Evidence Manifest     ████   ██░░   ██░░    ░░░░
Policies              ████   ░░░░   ░░░░    ░░░░
Compliance            ████   ████   ████    ░░░░
Override/VCR          ████   ░░░░   ░░░░    ░░░░
Planning              ████   ██░░   ██░░    ░░░░
AGENTS.md             ████   ████   ████    ░░░░
Analytics             ████   ░░░░   ░░░░    ░░░░
Codegen               ████   ████   ████    ░░░░
AI Council            ████   ░░░░   ████    ░░░░
Admin                 ████   ░░░░   ░░░░    ░░░░
Payments              ████   ░░░░   ░░░░    ░░░░
```

---

## 7. Implementation Principles

### 7.1 Feature Parity Guidelines

| Principle | Description |
|-----------|-------------|
| **Primary Client** | Each feature has ONE primary client for full implementation |
| **Complementary** | Other clients provide subset for specific use cases |
| **No Duplication** | Avoid duplicating complex UI across clients |
| **API-First** | All features backed by shared API |
| **Consistent UX** | Similar terminology, icons, flows across clients |

### 7.2 Client-Specific Guidelines

| Client | Focus | Avoid |
|--------|-------|-------|
| **Web** | Full admin, complex workflows, analytics | Offline-first features |
| **CLI** | Automation, CI/CD, scripting | Interactive UI, charts |
| **VSCode** | Developer workflow, in-IDE | Admin, billing, complex forms |
| **Desktop** | Offline, enterprise, security | Web-only features |

### 7.3 API Design for Multi-Client

```yaml
API Design Principles:
  - RESTful endpoints (same for all clients)
  - JSON responses (universal parsing)
  - SSE for streaming (codegen, real-time)
  - Pagination for lists (consistent across clients)
  - Error codes (standardized handling)
  - Rate limiting (per-client quotas)
  - Versioning (v1, v2 for breaking changes)
```

---

## 8. Sprint Roadmap by Client

### 8.1 Web Dashboard

| Sprint | Features | Story Points |
|--------|----------|--------------|
| 84 | Teams & Organizations | 34 SP |
| 85 | AGENTS.md UI | 21 SP |
| 86 | Planning Part 1 (Roadmap, Phase) | 26 SP |
| 87 | Planning Part 2 (Sprint, Backlog) | 29 SP |
| 88 | Analytics Dashboard | 13 SP |

### 8.2 CLI (sdlcctl)

| Sprint | Features | Story Points |
|--------|----------|--------------|
| 85 | Authentication + Evidence Upload | 21 SP |
| 86 | Gates + Projects | 16 SP |
| 87 | Codegen Status + Compliance | 10 SP |
| 88 | Sprint Commands | 13 SP |

### 8.3 VSCode Extension

| Sprint | Features | Story Points |
|--------|----------|--------------|
| 85 | AGENTS.md Panel | 13 SP |
| 86 | Evidence Panel | 13 SP |
| 87 | Planning Sidebar | 21 SP |
| 88 | Requirements Panel | 8 SP |

### 8.4 Desktop App

| Quarter | Focus | Story Points |
|---------|-------|--------------|
| Q3 2026 | MVP (Auth, Projects, Gates) | 89 SP |
| Q4 2026 | Core (Teams, Planning) | 110 SP |
| Q1 2027 | Advanced (Codegen, AI) | 130 SP |

---

## 9. Success Metrics

### 9.1 Coverage Targets

| Metric | Current | Sprint 88 Target | Q4 2026 Target |
|--------|---------|------------------|----------------|
| Web Coverage | 53% | 95% | 98% |
| CLI Coverage | 13% | 43% | 55% |
| VSCode Coverage | 37% | 63% | 75% |
| Desktop Coverage | 0% | 0% | 50% |
| **Overall** | **43%** | **75%** | **85%** |

### 9.2 User Adoption Targets

| Client | Current MAU | Q2 2026 Target | Q4 2026 Target |
|--------|-------------|----------------|----------------|
| Web | 500 | 2,000 | 5,000 |
| CLI | 100 | 500 | 1,500 |
| VSCode | 200 | 1,000 | 3,000 |
| Desktop | 0 | 0 | 500 |

---

## 10. Approval & Sign-off

### Document Approvals

- [ ] **CTO**: Architecture alignment, technical feasibility
- [ ] **CPO**: Feature prioritization, UX consistency
- [ ] **Frontend Lead**: Web implementation approach
- [ ] **Backend Lead**: API contract verification
- [ ] **DevOps Lead**: CLI design, CI/CD integration

---

**Document Version:** 1.0.0
**Created:** January 20, 2026
**Last Updated:** January 20, 2026
**Next Review:** February 20, 2026 (Monthly)
