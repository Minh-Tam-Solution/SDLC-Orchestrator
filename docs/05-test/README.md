# Stage 05: Testing & Quality Assurance

**Stage**: 05 - TEST
**Question**: Does it work correctly?
**Status**: ✅ **ACTIVE - TDD Strategy Complete**
**Framework**: SDLC 6.0.6 (7-Pillar + Section 7 Quality Assurance + Section 8 Specification Standard)
**Version**: 4.0.0 (January 27, 2026)

---

## 🎯 Quick Start

### Read This First

📖 **[00-TEST-STRATEGY-2026.md](00-TEST-STRATEGY-2026.md)** - Comprehensive Test-Driven Development strategy aligned with `.claude/skills/test-driven-development` and `.claude/skills/testing-patterns`

**Key Principle**: **"NO PRODUCTION CODE WITHOUT A FAILING TEST FIRST"**

---

## Purpose

This stage ensures SDLC Orchestrator meets quality standards through **Test-Driven Development (TDD)** at all levels:
- **Unit tests** (60%) - Pure logic, edge cases
- **Integration tests** (30%) - Service boundaries, API contracts
- **E2E tests** (10%) - Critical user journeys

All tests follow the **Red-Green-Refactor cycle**:
1. RED → Write ONE failing test (watch it fail)
2. GREEN → Write MINIMAL code to pass
3. REFACTOR → Clean up (keep tests green)
4. REPEAT

---

## Core Documents

| Document | Purpose | Status |
|----------|---------|--------|
| **[00-TEST-STRATEGY-2026.md](00-TEST-STRATEGY-2026.md)** | TDD strategy, test pyramid, remediation plan | ✅ Complete |
| **[01-Stage-01-Test-Plan.md](01-Stage-01-Test-Plan.md)** | Requirements testing (WHAT) | ⏳ Pending |
| **[02-Stage-02-Test-Plan.md](02-Stage-02-Test-Plan.md)** | Design testing (HOW) | ⏳ Pending |
| **[03-Stage-03-Test-Plan.md](03-Stage-03-Test-Plan.md)** | Build/TDD implementation | ⏳ Pending |
| **[04-Stage-04-Test-Plan.md](04-Stage-04-Test-Plan.md)** | Integration/E2E testing | ⏳ Pending |
| **[05-Stage-05-Test-Plan.md](05-Stage-05-Test-Plan.md)** | Deploy/Smoke testing | ⏳ Pending |
| **[06-Framework-Compliance-Tests.md](06-Framework-Compliance-Tests.md)** | SDLC 5.2.0 alignment verification | ⏳ Pending |

---

## Test Levels

| Level | Location | Coverage Target | Status |
|-------|----------|----------------|--------|
| **Unit** | [03-Unit-Testing/](03-Unit-Testing/) | 95%+ | 🔄 In Progress |
| **Integration** | [04-Integration-Testing/](04-Integration-Testing/) | 90%+ | 🔄 In Progress |
| **API** | [08-API-Testing/](08-API-Testing/) | 100% OpenAPI | ⚠️ Partial |
| **E2E** | [07-E2E-Testing/](07-E2E-Testing/) | 10 critical paths | ⚠️ Partial |
| **Load** | [09-Load-Testing/](09-Load-Testing/) | 100K users | ⏳ Pending |
| **Security** | [06-Security-Testing/](06-Security-Testing/) | OWASP ASVS L2 | ⏳ Pending |

---

## Quality Gates

| Gate | Criteria | Status |
|------|----------|--------|
| **Pre-Commit** | Unit tests pass + 95% coverage + no linting errors | 🎯 Target |
| **Pre-Merge** | Integration tests pass + OpenAPI validation | 🎯 Target |
| **Pre-Deploy** | E2E tests pass + load test pass + smoke tests pass | 🎯 Target |

---

## Testing Standards

### TDD Iron Law (MANDATORY)

```
NO PRODUCTION CODE WITHOUT A FAILING TEST FIRST
```

**Verification Checklist** (before marking work complete):
- [ ] Every new function/method has a test
- [ ] Watched each test fail before implementing
- [ ] Each test failed for expected reason (feature missing, not typo)
- [ ] Wrote minimal code to pass each test
- [ ] All tests pass
- [ ] Output pristine (no errors, warnings)
- [ ] Tests use real code (mocks only if unavoidable)
- [ ] Edge cases and errors covered

**Violations = Delete Code and Start Over**

---

### Factory Pattern (MANDATORY)

Always use factory functions for test data:

```python
# ✅ GOOD
gate = get_mock_gate({"status": "approved"})

# ❌ BAD
gate = Gate("gate-123", "Auth Gate", "DESIGN", "approved", ["cto@example.com"])
```

Factories location: `backend/tests/factories/`

---

### Behavior-Driven Testing

**Test BEHAVIOR, not IMPLEMENTATION**:

```python
# ✅ GOOD - Test behavior
def test_gate_approval_sends_notification():
    gate = create_gate()
    gate.approve()
    assert notification_sent_to(gate.owner)

# ❌ BAD - Test implementation
def test_gate_approval_calls_notify_method():
    gate = Mock()
    gate.approve()
    assert gate._notify_owner.called  # Testing internal method
```

---

## Test Pyramid

```
        ▲
       ╱ ╲
      ╱ E2E ╲           10% - User journeys (Playwright)
     ╱───────╲
    ╱         ╲
   ╱Integration╲        30% - Service boundaries (pytest-asyncio)
  ╱─────────────╲
 ╱               ╲
╱    Unit Tests   ╲     60% - Functions/classes (pytest)
▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔
```

---

## Remediation Plan (Sprint 107-109)

### Sprint 107: Foundation (Week 1)
- [ ] Move legacy docs to `docs/10-archive/05-Legacy/`
- [ ] Create test factories for all models
- [ ] Create test stubs for all services
- [ ] Setup docker-compose.test.yml
- [ ] Update CI/CD to enforce 95% coverage

**Target**: 95% coverage for test infrastructure

---

### Sprint 108: Core Tests (Week 2)
- [ ] Implement unit tests for Gate Service (FR1)
- [ ] Implement unit tests for Evidence Vault (FR2)
- [ ] Implement unit tests for AI Context Engine (FR3)
- [ ] Implement integration tests for Gate API
- [ ] Framework compliance tests (Stage 00, 01, 02)

**Target**: 200+ unit tests, 50+ integration tests

---

### Sprint 109: E2E & Go-Live (Week 3)
- [ ] Implement 10 critical E2E journeys (Playwright)
- [ ] Load testing (100K concurrent users)
- [ ] Security testing (OWASP ASVS L2)
- [ ] Smoke tests for production
- [ ] Go-live readiness review

**Target**: Production-ready test suite

---

## Framework vs Orchestrator Testing

### The Gap

```
┌──────────────────────────────────────────────────────────────┐
│ SDLC Framework (Methodology)                                 │
│ - SDLC 5.2.0 (7-Pillar + AI Governance Principles)          │
│ - Defines stages, gates, evidence types                      │
│ - Tools-agnostic                                             │
└──────────────────────────────────────────────────────────────┘
                            ↓
               ┌────────────────────────┐
               │  MUST TEST BOTH LAYERS │
               └────────────────────────┘
                            ↓
┌──────────────────────────────────────────────────────────────┐
│ SDLC Orchestrator (Automation Platform)                      │
│ - Implements framework as REST APIs                          │
│ - FastAPI + PostgreSQL + OPA + MinIO                         │
│ - Specific tool implementation                               │
└──────────────────────────────────────────────────────────────┘
```

**Framework Compliance Tests**: Verify Orchestrator implements SDLC 5.2.0 correctly
**Automation Logic Tests**: Verify Orchestrator features work correctly

See: [00-TEST-STRATEGY-2026.md § 4. Framework vs Orchestrator Testing](00-TEST-STRATEGY-2026.md#4-framework-vs-orchestrator-testing)

---

## Related Stages

| Stage | Relationship |
|-------|--------------|
| **[01-Planning](../01-planning/)** | Test cases from requirements (FR → Test scenario) |
| **[02-Design](../02-design/)** | Test stubs from design (NotImplementedError) |
| **[03-Build](../04-build/)** | TDD implementation (Red-Green-Refactor) |
| **[05-Deploy](../06-deploy/)** | Smoke tests post-deployment |

---

## Developer Resources

### Test Writing Guides

| Guide | Purpose | Status |
|-------|---------|--------|
| **DEVELOPER-TDD-GUIDE.md** | How to do TDD in Orchestrator | ⏳ Pending |
| **FACTORY-PATTERN-GUIDE.md** | How to use test factories | ⏳ Pending |
| **PLAYWRIGHT-E2E-GUIDE.md** | How to write E2E tests | ⏳ Pending |

### Skills Reference

- [.claude/skills/test-driven-development](/.claude/skills/test-driven-development/SKILL.md) - TDD Iron Law, Red-Green-Refactor
- [.claude/skills/testing-patterns](/.claude/skills/testing-patterns/SKILL.md) - Factory pattern, mocking strategies

---

## Test Artifacts

| Type | Location | Purpose |
|------|----------|---------|
| **Unit Coverage** | `backend/htmlcov/` | Python coverage reports |
| **E2E Results** | `frontend/web/test-results/` | Playwright artifacts |
| **Load Results** | `tests/load/` | Locust performance reports |
| **Security Scan** | `backend/.semgrep/` | Semgrep SAST results |

---

## Archive

Legacy test documents (pre-2026) migrated to `docs/10-archive/05-Legacy/` per RFC-001.

---

## Success Criteria

**Go-Live Approved When**:
- [x] Test strategy document complete
- [ ] All test factories implemented
- [ ] Unit coverage ≥95%
- [ ] Integration coverage ≥90%
- [ ] 10 critical E2E paths passing
- [ ] Framework compliance tests passing
- [ ] Load test pass (100K users)
- [ ] Security audit pass (OWASP ASVS L2)
- [ ] Zero P0 bugs, <5 P1 bugs
- [ ] CTO + QA Lead sign-off

---

**Last Updated**: January 27, 2026
**Owner**: QA Lead + CTO + Backend Lead
**Framework**: SDLC 6.0.6 (7-Pillar + Section 7 Quality Assurance + Section 8 Specification Standard)

---

*"If you didn't watch the test fail, you don't know if it tests the right thing."* - TDD Iron Law
