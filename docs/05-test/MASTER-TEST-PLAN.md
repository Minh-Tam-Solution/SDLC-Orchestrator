# Master Test Plan — SDLC Orchestrator

```yaml
document_type: "Master Test Plan"
version: "1.0.0"
date: "2026-02-24"
framework: "SDLC 6.1.1"
status: "SKELETON — Sprint 198 C-05"
author: "@pm"
authority: "CTO + QA Lead"
traceability: "CF-03 (Sprint 197 A-01) → CF (Sprint 198 C-05)"
```

---

## 1. Executive Summary

This Master Test Plan (MTP) is the **single index** for all testing activities in SDLC Orchestrator. It unifies 10 test categories, maps coverage to SDLC 6.1.1 stages, and enforces the Zero Mock Policy across all tiers.

### Test Pyramid (Target)

```
         /  E2E  \          10% — 10 critical user journeys (Playwright)
        /----------\
       / Integration \       30% — API contracts, DB transactions, OSS (OPA/MinIO/Redis)
      /----------------\
     /    Unit Tests     \   60% — Service logic, validators, helpers
    /______________________\
```

### Current Metrics (Sprint 198)

| Metric | Value | Target | Status |
|--------|-------|--------|--------|
| Total test files | 259 | — | Baselined |
| Unit tests (functions) | 3,096+ | 95% coverage | On track |
| Integration tests | 993+ | 90% coverage | On track |
| E2E scenarios | 85+ | 10 critical paths | Exceeds |
| Codegen tests | 436 | — | Sprint 196+ |
| Quick tests (baselined) | 114 | — | Sprint 197 |
| Sprint 198 tests | 41/41 | 100% pass | PASS |
| p95 API latency | 14.0ms | <100ms | PASS |
| OWASP ASVS L2 | 98.4% | Level 2 (264/264) | ACHIEVED |

---

## 2. Test Categories Index

| # | Category | Directory | Status | Key Documents |
|---|----------|-----------|--------|---------------|
| 00 | Test Strategy | [00-TEST-STRATEGY-2026.md](00-TEST-STRATEGY-2026.md) | Active | TDD Iron Law, pyramid, skills |
| 01 | Test Strategy Gov | [01-Test-Strategy/](01-Test-Strategy/) | Active | SPEC-0001, SPEC-0019, SPEC-0021 |
| 02 | Security Testing | 02-Security-Testing/ | **TODO** | OWASP ASVS L2, Semgrep, pen-test |
| 03 | Unit Testing | [03-Unit-Testing/](03-Unit-Testing/) | Active | GitHub service, sync jobs |
| 04 | Integration Testing | [04-Integration-Testing/](04-Integration-Testing/) | Active | OAuth, MinIO |
| 05 | Performance Testing | 05-Performance-Testing/ | **TODO** | Locust 100K, p95 benchmarks |
| 06 | Accessibility Testing | 06-Accessibility-Testing/ | **TODO** | WCAG 2.1 AA, Lighthouse |
| 07 | E2E Testing | [07-E2E-Testing/](07-E2E-Testing/) | Active | 26 Bruno tests, Playwright |
| 08 | API Testing | [08-API-Testing/](08-API-Testing/) | Active | OpenAPI spec validation |
| 09 | Load Testing | [09-Load-Testing/](09-Load-Testing/) | Active | Webhook load test plan |

### Cross-Cutting Documents

| Document | Location | Purpose |
|----------|----------|---------|
| Testing Architecture | [docs/02-design/13-Testing-Strategy/Testing-Architecture.md](../02-design/13-Testing-Strategy/Testing-Architecture.md) | Zero Mock Policy, test infra design |
| Multi-Agent Test Plan | [docs/02-design/13-Testing-Strategy/Multi-Agent-Test-Plan.md](../02-design/13-Testing-Strategy/Multi-Agent-Test-Plan.md) | ADR-056 EP-07 test scenarios (17 cases) |
| Remediation Plan | [REMEDIATION-PLAN-GOLIVE-2026.md](REMEDIATION-PLAN-GOLIVE-2026.md) | 3-sprint go-live testing roadmap |
| Testing Strategy Gov v2 | [01-Test-Strategy/Testing-Strategy-Governance-v2.md](01-Test-Strategy/Testing-Strategy-Governance-v2.md) | SPEC-0001/0002, Anti-Vibecoding |

---

## 3. Traceability Matrix — Tests to SDLC Stages

| SDLC Stage | Gate | Test Categories | Key Test Suites |
|------------|------|-----------------|-----------------|
| 00 Foundation | G0.1, G0.2 | 01 (Strategy) | Conformance: SPEC-0019 |
| 01 Planning | G1 | 08 (API) | OpenAPI spec validation |
| 02 Design | G2 | 01 (Strategy), 02 (Security) | Architecture review, threat model |
| 03 Build | G3 | 03 (Unit), 04 (Integration) | 3,096+ unit, 993+ integration |
| 04 Deploy | G4 | 07 (E2E), 09 (Load) | Playwright journeys, Locust |
| 05 Test | — | **All categories** | This Master Test Plan |
| 06 Operate | — | 05 (Performance) | Prometheus, p95 monitoring |
| 07 Integrate | — | 04 (Integration) | OAuth, MinIO, OPA contract tests |
| 08 Feedback | — | 01 (Strategy) | Developer satisfaction survey |
| 09 Govern | — | 02 (Security), 06 (Accessibility) | OWASP ASVS, WCAG 2.1 AA |

---

## 4. Test Infrastructure

### 4.1 Local Development

```bash
# Start test dependencies
docker compose -f docker-compose.staging.yml up -d postgres redis opa minio

# Run unit tests (fast, no external deps)
python -m pytest backend/tests/unit/ -v --tb=short

# Run integration tests (requires Docker services)
DATABASE_URL="postgresql://test:test@localhost:15432/sdlc_test" \
  python -m pytest backend/tests/integration/ -v

# Run E2E tests
python -m pytest backend/tests/e2e/ -v

# Run quick-tests (baseline: 114 tests)
python -m pytest backend/tests/quick-tests/ -v
```

### 4.2 CI/CD Pipeline

```yaml
Pre-commit:
  - ruff lint + black format
  - AGPL import detection
  - Zero Mock keyword ban

GitHub Actions:
  - Unit tests (95% coverage gate)
  - Integration tests (90% coverage gate)
  - Security scan (Semgrep OWASP rules)
  - License scan (Syft + Grype)
  - SBOM generation
```

### 4.3 Docker Services (Test Environment)

| Service | Port | Purpose |
|---------|------|---------|
| PostgreSQL 15.5 | 15432 | Test database |
| Redis 7.2 | 6395 | Cache, sessions, rate limiting |
| OPA 0.58 | 8185 | Policy evaluation |
| MinIO | 9000 | Evidence storage (S3 API) |

---

## 5. Test Factory Specifications

Six core model factories for consistent test data generation:

| Factory | Model | Key Fields | Location |
|---------|-------|------------|----------|
| UserFactory | `User` | email, password_hash, role, is_active | `backend/tests/factories/` |
| ProjectFactory | `Project` | name, tier, github_repo_full_name | `backend/tests/factories/` |
| GateFactory | `Gate` | gate_type, status, project_id | `backend/tests/factories/` |
| EvidenceFactory | `GateEvidence` | type, s3_key, sha256_hash | `backend/tests/factories/` |
| PolicyFactory | `Policy` | name, rego_content, severity | `backend/tests/factories/` |
| CodegenFactory | `CodegenSession` | spec, provider, quality_result | `backend/tests/factories/` |

**Status**: Factory pattern used ad-hoc in tests via helper functions. Formal factory-boy or pytest-factoryboy integration planned.

---

## 6. Missing Sections (To Create)

### 6.1 Security Testing (02-Security-Testing/) — P1

```yaml
Planned Documents:
  - OWASP-ASVS-L2-TESTING-PLAN.md
    - 264/264 requirement verification procedures
    - Authentication test cases (JWT, OAuth, MFA)
    - Authorization test cases (RBAC, 13 roles, row-level security)
    - Input validation (SQL injection, XSS, SSRF — 12 patterns)
    - Secrets management (90-day rotation verification)

  - SEMGREP-CI-INTEGRATION.md
    - AI-specific security rules (policy-packs/semgrep/ai-security.yml)
    - OWASP Python rules (policy-packs/semgrep/owasp-python.yml)
    - Custom rules for AGPL import detection
    - CI gate: ERROR severity blocks merge

  - PENETRATION-TEST-CHECKLIST.md
    - External firm engagement scope
    - Pre-test environment setup
    - Finding classification (P0-P4)
    - Remediation SLA (P0: 24h, P1: 72h, P2: 7d)
```

### 6.2 Performance Testing (05-Performance-Testing/) — P2

```yaml
Planned Documents:
  - LOCUST-LOAD-TEST-PLAN.md
    - 100K concurrent user simulation
    - Scenario: Registration → Login → Gate Evaluate → Evidence Upload
    - p95 latency targets per endpoint class
    - Database query benchmarks (<10ms SELECT, <50ms JOIN)
    - Bottleneck identification (py-spy flamegraphs)

  - API-BENCHMARK-TARGETS.md
    - Gate evaluation: <100ms p95
    - Evidence upload (10MB): <2s
    - Dashboard load: <1s
    - List projects (100 items): <200ms
    - Agent conversation send: <500ms p95
```

### 6.3 Accessibility Testing (06-Accessibility-Testing/) — P2

```yaml
Planned Documents:
  - WCAG-ACCESSIBILITY-TESTING.md
    - WCAG 2.1 AA compliance checklist
    - Screen reader test scenarios (NVDA, VoiceOver)
    - Keyboard navigation validation (all interactive elements)
    - Color contrast ratio verification (4.5:1 normal, 3:1 large)

  - LIGHTHOUSE-CI-CONFIG.md
    - Lighthouse score target: >90
    - Accessibility category: >95
    - CI integration (GitHub Actions)
    - Per-page baseline tracking
```

---

## 7. Framework Compliance Mapping (SDLC 6.1.1)

| SDLC 6.1.1 Requirement | MTP Coverage | Evidence |
|-------------------------|-------------|----------|
| Zero Mock Policy | Enforced | Pre-commit hook, CI gate |
| Test Pyramid (60/30/10) | Tracked | Unit 3,096 / Integ 993 / E2E 85 |
| Anti-Vibecoding (Section 7) | SPEC-0001 | Vibecoding Index scoring |
| Specification Standard (Section 8) | SPEC-0002 | YAML frontmatter + BDD |
| Evidence-Based Development | Evidence Vault | SHA256 integrity, 8-state lifecycle |
| Multi-Agent Governance | ADR-056 | 17 multi-agent test scenarios |
| Tier-Specific Requirements | ADR-059 | LITE/STANDARD/PRO/ENTERPRISE test coverage |
| OTT Channel Testing | Sprint 198 | admin_ott.py (23 tests), teams_normalizer (18 tests) |
| CF-02 Resilience (503) | Sprint 198 | 12 endpoints: DB/service → 503 + Retry-After |
| CF-03 Auth Performance | Sprint 198 | bcrypt run_in_threadpool (3 endpoints) |

---

## 8. Go-Live Readiness Checklist

| # | Check | Target | Status |
|---|-------|--------|--------|
| 1 | Unit test coverage | >95% | On track |
| 2 | Integration test coverage | >90% | On track |
| 3 | E2E critical paths | 10 journeys | 85+ scenarios |
| 4 | p95 API latency | <100ms | 14.0ms PASS |
| 5 | OWASP ASVS L2 | 264/264 | 98.4% |
| 6 | Zero P0/P1 bugs | 0 | 0 |
| 7 | Security scan | PASS | Semgrep + Grype |
| 8 | Load test (100K) | <100ms p95 | Planned |
| 9 | AGPL containment | 0 violations | Pre-commit enforced |
| 10 | Quick-test baseline | 114 tests | Sprint 197 |

---

## 9. Revision History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0.0 | 2026-02-24 | @pm | Initial skeleton (Sprint 198 C-05) |

---

*SDLC Orchestrator — Zero facade tolerance. Real tests, real coverage, real quality.*
