# Frontend Feature Alignment Matrix

**Version**: 1.4.0
**Status**: ACTIVE
**Framework**: SDLC 6.0.5
**Last Updated**: 2026-01-30 (Sprint 126 Complete - E2E Tests)
**Owner**: PM + Architect

---

## 1. Overview

SDLC Orchestrator delivers governance through **3 frontend surfaces**. This matrix tracks feature parity and identifies gaps.

| Surface | Technology | Target User | Primary Use Case |
|---------|------------|-------------|------------------|
| **Web Dashboard** | Next.js + React | PM, Tech Lead, CTO | Project management, reports, admin |
| **CLI (sdlcctl)** | Python + Typer | Developer, DevOps | CI/CD integration, local validation |
| **VS Code Extension** | TypeScript | Developer | IDE-integrated governance |

---

## 2. Framework Version Alignment

| Component | Current | Target | Status | Sprint |
|-----------|---------|--------|--------|--------|
| SDLC Enterprise Framework | 6.0.5 | 6.0.5 | ✅ Aligned | - |
| Backend API | 6.0.5 | 6.0.5 | ✅ Aligned | - |
| **Web Dashboard** | 6.0.5 | 6.0.5 | ✅ Aligned | - |
| **CLI (sdlcctl)** | **6.0.5** | 6.0.5 | ✅ **ALIGNED** | 125 ✅ |
| **VS Code Extension** | **6.0.5** | 6.0.5 | ✅ **ALIGNED** | 125 ✅ |

> **Sprint 125 Complete (Jan 30, 2026)**: CLI v1.2.0 published to [PyPI](https://pypi.org/project/sdlcctl/1.2.0/), Extension v1.2.0 published to [VS Code Marketplace](https://marketplace.visualstudio.com/items?itemName=mtsolution.sdlc-orchestrator)

---

## 3. Feature Parity Matrix

### 3.1 Core Governance Features

| Feature | Web | CLI | Ext | Gap Owner | Target Sprint |
|---------|-----|-----|-----|-----------|---------------|
| **Project Management** |
| Create Project | ✅ | ❌ | ❌ | N/A (Web-only) | - |
| List Projects | ✅ | ❌ | ✅ | - | - |
| Project Settings | ✅ | ❌ | ⚠️ | - | - |
| **Validation** |
| Folder Structure Validation | ✅ | ✅ | ✅ | ✅ Aligned | - |
| Tier Classification | ✅ | ✅ | ✅ | ✅ Aligned | - |
| Compliance Scoring | ✅ | ✅ | ⚠️ | Frontend | 126 |
| **SDLC 6.0.5 Spec Features** |
| YAML Frontmatter Validation | ✅ | ✅ | ✅ | ✅ Aligned | **126** ✅ |
| JSON Schema Validation | ✅ | ✅ | ✅ | ✅ Aligned | **126** ✅ |
| BDD Requirements Validation | ✅ | ✅ | ✅ | ✅ Aligned | **126** ✅ |
| Tier-Specific Sections | ✅ | ✅ | ✅ | ✅ Aligned | **126** ✅ |
| Spec Convert (OpenSpec) | ❌ | ✅ | ❌ | CLI-only | **126** ✅ |
| Spec List | ✅ | ✅ | ⚠️ | **Frontend** | **127** |
| Spec Init | ❌ | ✅ | ❌ | CLI-only | **126** ✅ |
| **Gates & Evidence** |
| Gate Status View | ✅ | ❌ | ✅ | Backend | Backlog |
| Evidence Upload | ✅ | ❌ | ✅ | Backend | Backlog |
| Evidence History | ✅ | ❌ | ✅ | - | - |
| **AI Features** |
| AI Council Chat | ✅ | ❌ | ✅ | - | - |
| AI Recommendations | ✅ | ❌ | ✅ | - | - |
| Context Authority (6.0.5) | ✅ | ❌ | ❌ | **All** | **127** |

### 3.2 Feature Status Summary

| Category | Web | CLI | Extension |
|----------|-----|-----|-----------|
| Total Features | 18 | 12 | 16 |
| Implemented | 18 | 12 | 16 |
| **SDLC 6.0.5 Features** | 5/7 | **7/7** | **4/7** |
| Parity Score | 100% | **71%** | **89%** |

> **Updated Jan 30, 2026 (Sprint 126)**:
> - ✅ CLI added JSON Schema validation for frontmatter
> - ✅ CLI added BDD requirements validation (GIVEN-WHEN-THEN)
> - ✅ CLI added tier-specific sections validation
> - ✅ CLI added `sdlcctl spec convert` (OpenSpec → SDLC 6.0.5)
> - ✅ CLI added `sdlcctl spec init` (create new spec with template)
> - ✅ CLI already had `sdlcctl spec list` from Sprint 119
> - ✅ **Extension** added spec validation commands (S126-06)
> - ✅ **Extension** YAML frontmatter validation
> - ✅ **Extension** BDD requirements validation
> - ✅ **Extension** Tier-specific sections validation
> - ✅ **Extension** Problems panel integration for validation errors

---

## 4. API Coverage Matrix

### 4.1 Backend API Endpoints

| Endpoint | Purpose | Web | CLI | Ext | Notes |
|----------|---------|-----|-----|-----|-------|
| **Auth** |
| POST /auth/login | User login | ✅ | ❌ | ✅ | CLI uses local validation |
| POST /auth/refresh | Token refresh | ✅ | ❌ | ✅ | |
| GET /auth/me | Current user | ✅ | ❌ | ✅ | |
| **Projects** |
| GET /projects | List projects | ✅ | ❌ | ✅ | CLI: local only |
| POST /projects | Create project | ✅ | ❌ | ❌ | Web-only |
| GET /projects/{id} | Get project | ✅ | ❌ | ✅ | |
| **Validation** |
| POST /validate/structure | Validate folder | ✅ | ⚠️ | ✅ | CLI: local impl |
| POST /validate/spec | Validate spec | ✅ | ⚠️ | ❌ | CLI: local impl |
| GET /compliance/score | Get score | ✅ | ⚠️ | ⚠️ | CLI/Ext: local |
| **Gates** |
| GET /gates | List gates | ✅ | ❌ | ✅ | |
| GET /gates/{id} | Gate detail | ✅ | ❌ | ✅ | |
| POST /gates/{id}/approve | Approve gate | ✅ | ❌ | ❌ | Web-only |
| **Evidence** |
| POST /evidence | Upload evidence | ✅ | ❌ | ✅ | |
| GET /evidence | List evidence | ✅ | ❌ | ✅ | |
| **Specs (SDLC 6.0.5)** |
| POST /specs/validate | Validate spec | ✅ | ⚠️ | ⚠️ | CLI/Ext: local impl |
| POST /specs/convert | Convert spec | ❌ | ⚠️ | ❌ | CLI: local impl |
| GET /specs | List specs | ✅ | ⚠️ | ❌ | CLI: local impl |

### 4.2 API Coverage Summary

| Surface | Endpoints Used | Total Available | Coverage |
|---------|---------------|-----------------|----------|
| Web Dashboard | 17/17 | 17 | 100% |
| CLI (sdlcctl) | 3/17 | 17 | 18% |
| VS Code Extension | 12/17 | 17 | 71% |

**Note**: CLI uses local validation for most features, not API calls.

---

## 5. Gap Analysis

### 5.1 Critical Gaps (P0)

| Gap ID | Description | Impact | Resolution |
|--------|-------------|--------|------------|
| ~~GAP-001~~ | ~~CLI on SDLC 5.0.0~~ | ~~Users get outdated validation~~ | ✅ **Sprint 125 RESOLVED** |
| ~~GAP-002~~ | ~~Extension on SDLC 5.x~~ | ~~Users get outdated validation~~ | ✅ **Sprint 125 RESOLVED** |
| ~~GAP-003~~ | ~~No spec YAML validation in CLI~~ | ~~6.0.5 specs not validated~~ | ✅ **Sprint 125 RESOLVED** |
| ~~GAP-004~~ | ~~No BDD validation in CLI~~ | ~~Requirements format not checked~~ | ✅ **Sprint 126 RESOLVED** |

### 5.2 High Priority Gaps (P1)

| Gap ID | Description | Impact | Resolution |
|--------|-------------|--------|------------|
| ~~GAP-005~~ | ~~No spec convert in CLI~~ | ~~Manual OpenSpec conversion~~ | ✅ **Sprint 126 RESOLVED** |
| GAP-006 | No Context Authority in CLI/Ext | 6.0.5 feature missing | Sprint 127 |
| GAP-007 | Extension compliance scoring partial | Inconsistent UX | Sprint 127 |
| ~~GAP-008~~ | ~~No spec features in Extension~~ | ~~6.0.5 specs not validated in IDE~~ | ✅ **Sprint 126 RESOLVED** |

### 5.3 Backlog Gaps (P2)

| Gap ID | Description | Impact | Resolution |
|--------|-------------|--------|------------|
| GAP-009 | CLI no gate status | Devs use Web for gates | Future |
| GAP-010 | CLI no evidence upload | Devs use Web/Ext | Future |
| GAP-011 | CLI no AI features | Devs use Web/Ext | Future |

---

## 6. Resolution Timeline

```
Sprint 124 (Complete)
├── [DONE] Gap Analysis Report
├── [DONE] Sprint Plan 125-127
└── [DONE] Frontend Alignment Matrix

Sprint 125 ✅ COMPLETE (Jan 30, 2026 - 14 days early!)
├── [DONE] Update CLI version refs → 6.0.5 (~35 files)
├── [DONE] Update Extension version refs → 6.0.5 (5 files)
├── [DONE] Implement SpecFrontmatterValidator (16 tests)
├── [DONE] Publish CLI v1.2.0 to PyPI
├── [DONE] Publish Extension v1.2.0 to Marketplace
└── [DEFERRED] Stage 00-03 docs, ADR-045 → Sprint 127

Sprint 126 ✅ COMPLETE (Jan 30, 2026)
├── [DONE] JSON Schema validation integration
├── [DONE] Implement spec_bdd_validator (CLI)
├── [DONE] Implement sdlcctl spec convert (OpenSpec → SDLC 6.0.5)
├── [DONE] Implement sdlcctl spec init (create new spec)
├── [EXISTS] sdlcctl spec list (was in Sprint 119)
├── [DONE] Add spec validation to Extension (S126-06)
│   ├── specValidationCommand.ts - validate/validateWithTier commands
│   ├── Types: SpecValidationResult, FrontmatterValidation, BDDValidation
│   ├── Local validation (no backend required)
│   ├── Problems panel integration (VS Code diagnostics)
│   ├── Keybinding: Cmd+Shift+V for validate
│   └── Settings: validateSpecOnSave, defaultSpecTier
└── [DONE] Cross-frontend E2E tests (S126-07)
    ├── 6 test fixtures (valid/invalid specs, openspec format)
    ├── 9 Python E2E tests (backend validation parity)
    ├── 16 TypeScript tests (Extension validation)
    └── SPC-001/002/003/004 error code parity verified

Sprint 127 (Feb 17-28, 2026)
├── [ ] Context Authority in CLI/Extension
├── [ ] Framework Update Trigger automation
├── [ ] Monthly Alignment Checkpoint process
├── [ ] Update Stage 00-03 documentation
└── [ ] Create ADR-045 Multi-Frontend Strategy
```

---

## 7. Update Process

### 7.1 When to Update This Matrix

- [ ] New feature added to any frontend
- [ ] Framework version changes
- [ ] API endpoint added/modified
- [ ] Sprint planning (review gaps)
- [ ] Monthly alignment checkpoint

### 7.2 Responsible Parties

| Role | Responsibility |
|------|----------------|
| PM | Maintain matrix, track gaps, prioritize |
| Backend Lead | CLI feature parity |
| Frontend Lead | Web + Extension feature parity |
| Architect | API coverage, design decisions |

---

## 8. Change Log

| Date | Version | Change | Author |
|------|---------|--------|--------|
| 2026-01-30 | 1.0.0 | Initial matrix created | AI Assistant |
| 2026-01-30 | 1.1.0 | Sprint 125 complete - CLI/Extension aligned to 6.0.5 | AI Assistant |
| 2026-01-30 | 1.2.0 | Sprint 126 CLI enhancements - spec convert/init/list, JSON Schema, BDD | AI Assistant |
| 2026-01-30 | 1.3.0 | Sprint 126 Extension spec validation (S126-06) - GAP-008 resolved | AI Assistant |
| 2026-01-30 | 1.4.0 | Sprint 126 E2E tests complete (S126-07) - Full validation parity | AI Assistant |

---

**Document Status**: ACTIVE
**Review Cycle**: Sprint planning + Monthly checkpoint
**Next Review**: Sprint 126 Completion (Feb 14, 2026)
