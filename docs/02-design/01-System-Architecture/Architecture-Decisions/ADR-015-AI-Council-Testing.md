# ADR-015: AI Council Testing Strategy

**Status**: ACCEPTED
**Date**: December 4, 2025
**Decision Makers**: CTO, Backend Lead
**Sprint**: 26 - AI Council Service
**SDLC Stage**: Stage 04 (BUILD)

---

## Context

Sprint 26 delivered the AI Council Service with 3-stage LLM deliberation for compliance recommendations. A comprehensive testing strategy was needed to ensure:

1. **Production Quality**: 95%+ test coverage for council service
2. **Performance Validation**: <3s single mode, <8s council mode (p95 latency)
3. **Zero Mock Policy Compliance**: Real service integration with controlled LLM mocking
4. **Regression Prevention**: Automated tests for all council modes and stages

### Problem Statement

The AI Council Service introduces complex multi-stage processing:
- Stage 1: Parallel queries to 3 LLMs
- Stage 2: Anonymized peer review and ranking
- Stage 3: Chairman synthesis

Traditional unit testing approaches are insufficient because:
- External LLM calls are expensive and non-deterministic
- Parallel execution makes debugging difficult
- Performance targets must be validated continuously
- Integration with Compliance Scanner requires end-to-end testing

---

## Decision

Implement a **3-tier testing strategy** with clear boundaries:

### Tier 1: Unit Tests (95%+ Coverage)

**Location**: `backend/tests/unit/test_ai_council_service.py`

**Approach**:
- Mock all external dependencies (LLM API calls, database)
- Test each method in isolation
- Validate business logic correctness
- Fast execution (<10 seconds)

**What to Mock**:
```python
# ✅ MOCK: External LLM API calls
council_service.ai_service.generate_recommendation = AsyncMock(
    return_value=AIProviderResponse(
        recommendation="Fix: Create documentation",
        provider="ollama",
        confidence=85,
        duration_ms=1234.5,
    )
)

# ❌ DON'T MOCK: Internal business logic
# Test real logic for: confidence calculation, severity routing, ranking aggregation
```

**Test Categories (19 tests)**:
1. Single Mode Deliberation (2 tests)
2. Stage 1: Parallel Queries (2 tests)
3. Stage 2: Peer Review (3 tests)
4. Stage 3: Chairman Synthesis (2 tests)
5. AUTO Mode Routing (2 tests)
6. Helper Methods (6 tests)
7. Fallback Scenarios (1 test)
8. Metrics Recording (1 test)

### Tier 2: Integration Tests (90%+ Coverage)

**Location**: `backend/tests/integration/test_council_api.py`

**Approach**:
- Real FastAPI application with test database
- Real HTTP client (httpx.AsyncClient)
- Mock only external LLM calls
- Test authentication, authorization, validation

**Test Categories (18 tests)**:
1. POST /council/deliberate - All modes (9 tests)
2. GET /council/status - Async status (1 test)
3. GET /council/history - Pagination, filters (3 tests)
4. GET /council/stats - Aggregations (1 test)
5. Auto-Council Integration (1 test)
6. Error Handling (2 tests)
7. Performance (1 test)

### Tier 3: Performance Benchmarks

**Location**: `backend/tests/performance/test_council_benchmarks.py`

**Approach**:
- Measure p95/p99 latency for all modes
- Test concurrent request handling
- Calculate throughput (requests/second)
- Track cost per deliberation

**Test Categories (11 benchmarks)**:
1. Single Mode Latency - Sequential (1 test)
2. Single Mode Latency - Concurrent (1 test)
3. Council Mode Latency - Sequential (1 test)
4. Council Mode Latency - Concurrent (1 test)
5. AUTO Mode Performance (1 test)
6. API Endpoint Latency (1 test)
7. Database Query Performance (1 test)
8. Throughput Testing (1 test)
9. Full Suite Summary (1 test)

---

## Performance Metrics Collection

### PerformanceMetrics Utility Class

```python
class PerformanceMetrics:
    """Track and calculate performance metrics."""

    def add_measurement(self, duration_ms: float, cost_usd: float, error: bool = False):
        """Record a single measurement."""

    def get_summary(self) -> dict:
        """Calculate P50/P95/P99 latency, cost, success rate."""
        return {
            "latency_p95_ms": sorted_durations[int(len(sorted_durations) * 0.95)],
            "latency_p99_ms": sorted_durations[int(len(sorted_durations) * 0.99)],
            "success_rate": ((total - self.errors) / total) * 100,
            "cost_mean_usd": statistics.mean(self.costs),
        }

    def print_report(self, test_name: str):
        """Print formatted performance report."""
```

### Performance Targets

| Metric | Target | P95 Requirement |
|--------|--------|-----------------|
| Single Mode Latency | <3s | <3s p95 |
| Council Mode Latency | <8s | <8s p95 |
| API Endpoint Latency | <3.5s | <3.5s p95 |
| Success Rate | >95% | All modes |
| Database Query | <50ms | Violation lookup |
| Throughput | >3 req/s | Under load |

---

## Zero Mock Policy Compliance

### What to Mock (External Dependencies Only)

```python
# ✅ ALLOWED: Mock external LLM API calls
@pytest.fixture
def mock_ai_fast_response():
    return AIProviderResponse(
        recommendation="Fix: Create documentation",
        provider="ollama",
        confidence=85,
        duration_ms=800.0,
        cost_usd=0.0001,
    )

# Apply mock
with patch.object(
    council_service.ai_service,
    "generate_recommendation",
    new=AsyncMock(return_value=mock_ai_fast_response),
):
    response = await council_service.deliberate(...)
```

### What NOT to Mock (Real Integration)

```python
# ❌ NOT ALLOWED: Never mock database
db_session = await get_real_test_db_session()

# ❌ NOT ALLOWED: Never mock business logic
# Let the real confidence calculation run
assert response.confidence_score == calculate_confidence(rankings)

# ❌ NOT ALLOWED: Never mock internal services
# Use real AICouncilService, AuditService, etc.
```

### Rationale

The Zero Mock Policy (learned from NQH-Bot crisis) prevents:
- Integration issues hiding until production
- Contract mismatches between services
- False confidence from green tests with broken integrations

By mocking only external LLM calls:
- Tests are deterministic (no network variance)
- Tests are fast (no waiting for LLM responses)
- Tests validate real integration points
- Costs are controlled (no actual API charges)

---

## Test Infrastructure

### Automated Test Runner

**Location**: `backend/scripts/run_council_tests.sh`

```bash
#!/bin/bash
# Run all council tests
./scripts/run_council_tests.sh all

# Run specific category
./scripts/run_council_tests.sh unit          # Unit tests only
./scripts/run_council_tests.sh integration   # Integration tests
./scripts/run_council_tests.sh performance   # Benchmarks
```

### pytest Configuration

```ini
# pytest.ini
markers =
    asyncio: Async test cases
    performance: Performance benchmarks and load tests
    slow: Slow running tests
```

### Coverage Requirements

```ini
# pytest.ini
[coverage:run]
source = backend/app
omit = */tests/*, */migrations/*

[coverage:report]
fail_under = 90
```

---

## Consequences

### Positive

1. **Comprehensive Coverage**: 48 total tests (19 unit + 18 integration + 11 performance)
2. **Performance Validation**: Continuous validation of <3s/<8s targets
3. **Zero Mock Compliance**: Real integration with controlled external mocking
4. **Regression Prevention**: Automated CI/CD integration
5. **Cost Control**: No actual LLM API charges during testing

### Negative

1. **Maintenance Overhead**: 1,779 lines of test code to maintain
2. **Mock Realism**: Mocked LLM responses may not capture edge cases
3. **Environment Dependency**: Requires Docker services (PostgreSQL, Redis)

### Mitigations

1. **Mock Realism**: Include variety of mock responses (fast, slow, error, partial)
2. **Environment**: Automated setup in test runner script
3. **Maintenance**: Clear test organization with comprehensive documentation

---

## Related Documents

- [SPRINT-26-AI-COUNCIL-SERVICE.md](../../../03-Development-Implementation/02-Sprint-Plans/SPRINT-26-AI-COUNCIL-SERVICE.md)
- [ai_council_service.py](../../../../backend/app/services/ai_council_service.py)
- [test_ai_council_service.py](../../../../backend/tests/unit/test_ai_council_service.py)
- [test_council_api.py](../../../../backend/tests/integration/test_council_api.py)
- [test_council_benchmarks.py](../../../../backend/tests/performance/test_council_benchmarks.py)
- [Performance README](../../../../backend/tests/performance/README.md)

---

## Approval

| Role | Name | Status | Date |
|------|------|--------|------|
| CTO | - | ✅ APPROVED | Dec 4, 2025 |
| Backend Lead | - | ✅ APPROVED | Dec 4, 2025 |
| QA Lead | - | ⏳ PENDING | - |

---

**ADR Status**: ✅ ACCEPTED
**Implementation**: ✅ COMPLETE (Sprint 26 Day 4)
**Next Review**: Sprint 30 (January 2026)
