# Sprint 26: AI Council Service - Multi-LLM Deliberation

**Version**: 1.0.0
**Date**: December 2, 2025
**Status**: APPROVED - Awaiting Implementation
**Authority**: CTO + CPO (9.2/10 Rating)
**Foundation**: Expert Analysis (Deep Research, Market & OSS, Policy Pack v0.9)
**Framework**: SDLC 6.1.0
**Week**: 11 of 13

---

## Sprint Overview

**Sprint Goal**: Implement AI Council Service with 3-stage LLM deliberation pattern for high-quality compliance recommendations.

**Duration**: 5 days
**Team**: Backend 100%, DevOps 20%
**Priority**: P1 - High (AI Enhancement)

---

## Context: Why AI Council?

```yaml
Problem:
  - Single LLM recommendations have 85% accuracy
  - CRITICAL/HIGH violations need higher confidence
  - No peer review for AI suggestions

Solution (LLM Council Pattern):
  - Stage 1: Parallel queries to multiple LLMs
  - Stage 2: Anonymized peer review and ranking
  - Stage 3: Chairman synthesis (final answer)
  - Result: 95% accuracy for critical violations

Expert Alignment:
  - Deep Research: "Metadata Layer" pattern
  - Policy Pack v0.9: Tiered compliance (Lite/Standard/Enterprise)
  - Market & OSS: Multi-provider fallback chain
```

---

## CTO/CPO Conditions (5/5 Addressed)

| # | Condition | Sprint Day | Status |
|---|-----------|------------|--------|
| 1 | Integration Planning Session | Day 0 | ✅ PRE-PLANNED |
| 2 | Add Audit Logging (`AI_COUNCIL_REQUEST`) | Day 1 | ✅ DONE |
| 3 | Compliance Scanner Integration | Day 3 | ✅ DONE |
| 4 | VS Code Extension Scope Reduction | N/A (Sprint 27) | ✅ ACCEPTED |
| 5 | Performance Benchmark (<8s p95) | Day 4 | ✅ DONE |

---

## Day 0: Integration Planning (PRE-COMPLETED)

### Pre-Planning Completed During Sprint 22

| # | Task | Status | Notes |
|---|------|--------|-------|
| 0.1 | Review `compliance_scanner.py` | ✅ DONE | Integration points identified (line 271-405) |
| 0.2 | Review `audit_service.py` | ✅ DONE | Add `AI_COUNCIL_*` actions (line 31-112) |
| 0.3 | Review `ai_recommendation_service.py` | ✅ DONE | Extension pattern confirmed |
| 0.4 | Define performance targets | ✅ DONE | <8s Council mode p95 |
| 0.5 | Document integration architecture | ✅ DONE | Pre-planning document created |

**Pre-Planning Document**: `docs/09-Executive-Reports/01-CTO-Reports/2025-12-02-SPRINT-26-DAY0-INTEGRATION-PLAN.md`

---

## Day 1-2: AI Council Service Implementation

### Day 1: Core Service Foundation

| # | Task | File | Est. | Owner |
|---|------|------|------|-------|
| 1.1 | Create `AICouncilService` class | `backend/app/services/ai_council_service.py` | 4h | BE |
| 1.2 | Implement Stage 1: Parallel Queries | `ai_council_service.py` | 2h | BE |
| 1.3 | Add `AI_COUNCIL_*` audit actions | `backend/app/services/audit_service.py` | 1h | BE |
| 1.4 | Create Pydantic schemas | `backend/app/schemas/council.py` | 1h | BE |

### Day 2: Stage 2 & 3 Implementation

| # | Task | File | Est. | Owner |
|---|------|------|------|-------|
| 2.1 | Implement Stage 2: Anonymized Peer Review | `ai_council_service.py` | 3h | BE |
| 2.2 | Implement Stage 3: Chairman Synthesis | `ai_council_service.py` | 3h | BE |
| 2.3 | Add Evidence Vault metadata | `ai_council_service.py` | 1h | BE |
| 2.4 | Add Prometheus metrics | `backend/app/middleware/business_metrics.py` | 1h | BE |

### Technical Specifications

```python
# backend/app/services/ai_council_service.py (~450 lines)

class AICouncilService:
    """
    3-Stage LLM Council for high-confidence recommendations.

    Modes:
    - Single: Use existing AIRecommendationService (default)
    - Council: 3-stage deliberation for CRITICAL/HIGH violations

    Stages:
    1. Parallel Queries: Query 3 LLMs simultaneously
    2. Peer Review: Each LLM ranks others' responses (anonymized)
    3. Synthesis: Chairman LLM produces final answer
    """

    async def generate_council_recommendation(
        self,
        violation: ComplianceViolation,
        council_mode: bool = True,
    ) -> CouncilRecommendation:
        """Generate recommendation using council mode."""

    async def stage1_parallel_queries(
        self,
        query: str,
        providers: list[AIProviderType],
    ) -> list[AIResponse]:
        """Stage 1: Query all providers in parallel."""

    async def stage2_peer_review(
        self,
        responses: list[AIResponse],
    ) -> list[Ranking]:
        """Stage 2: Anonymized peer review and ranking."""

    async def stage3_synthesis(
        self,
        responses: list[AIResponse],
        rankings: list[Ranking],
    ) -> FinalAnswer:
        """Stage 3: Chairman synthesizes final answer."""
```

```python
# backend/app/schemas/council.py (~100 lines)

class CouncilRequest(BaseModel):
    violation_id: UUID
    council_mode: bool = True

class CouncilResponse(BaseModel):
    recommendation: str
    confidence_score: float  # 1-10
    providers_used: list[str]
    stage1_responses: list[AIResponse]
    stage2_rankings: list[Ranking]
    stage3_synthesis: FinalAnswer
    total_duration_ms: int
    total_cost_usd: float

class AIResponse(BaseModel):
    provider: str
    model: str
    response: str
    duration_ms: int

class Ranking(BaseModel):
    ranker: str  # Which LLM did the ranking
    rankings: list[str]  # ["Response A", "Response B", "Response C"]

class FinalAnswer(BaseModel):
    answer: str
    confidence: float
    reasoning: str
```

---

## Day 3: API Endpoints + Compliance Scanner Integration

### API Endpoints

| # | Task | File | Est. | Owner |
|---|------|------|------|-------|
| 3.1 | Create council routes | `backend/app/api/routes/council.py` | 2h | BE |
| 3.2 | Add OpenAPI documentation | `openapi.yml` | 1h | BE |
| 3.3 | Update Compliance Scanner | `backend/app/services/compliance_scanner.py` | 2h | BE |
| 3.4 | Integration testing | `tests/integration/test_council.py` | 3h | BE |

### API Specification

```yaml
# POST /api/v1/ai/council/recommend
Request:
  violation_id: UUID
  council_mode: bool (default: true)

Response:
  recommendation: string
  confidence_score: float
  council_deliberation:
    stage1_responses: list
    stage2_rankings: list
    stage3_synthesis: object
  total_duration_ms: int

# GET /api/v1/ai/council/deliberation/{request_id}
Response:
  request_id: UUID
  created_at: datetime
  violation_id: UUID
  full_deliberation: object
```

### Compliance Scanner Integration

```python
# backend/app/services/compliance_scanner.py (+50 lines)

async def _enhance_with_ai_recommendations(
    self,
    violations: list[Violation],
    project: Project,
) -> list[Violation]:
    """
    Enhance violations with AI Council recommendations.

    - CRITICAL/HIGH severity → Council mode (3-stage deliberation)
    - MEDIUM/LOW severity → Single mode (Ollama only)
    """
    for violation in violations:
        council_mode = violation.severity in ("critical", "high")

        recommendation = await self.ai_council.generate_recommendation(
            violation=violation,
            council_mode=council_mode,
        )

        violation.recommendation = recommendation.final_answer
        violation.ai_council_used = council_mode
        violation.ai_confidence = recommendation.confidence_score

    return violations
```

---

## Day 4: Tests + Performance Benchmark ✅ COMPLETE

**Status**: ✅ COMPLETE (December 4, 2025)  
**CTO Rating**: 9.5/10  
**Deliverables**: Unit tests (631 lines, 19 cases), Integration tests (517 lines, 18 cases), Performance benchmarks (631 lines, 11 tests), Test infrastructure

### Test Coverage

| # | Task | File | Est. | Owner | Status |
|---|------|------|------|-------|--------|
| 4.1 | Unit tests (95%+ coverage) | `tests/unit/test_ai_council_service.py` | 3h | BE | ✅ DONE |
| 4.2 | Integration tests | `tests/integration/test_council_api.py` | 2h | BE | ✅ DONE |
| 4.3 | Performance benchmark | `tests/performance/test_council_benchmarks.py` | 2h | BE | ✅ DONE |
| 4.4 | Test infrastructure | `scripts/run_council_tests.sh` + `tests/performance/README.md` | 1h | BE | ✅ DONE |

### Performance Benchmark Requirements

```python
# tests/performance/test_council_benchmark.py

import pytest
import time
import statistics

@pytest.mark.benchmark
async def test_council_mode_latency_p95():
    """Council mode should complete in <8s (p95)"""
    durations = []
    for _ in range(100):
        start = time.time()
        await council_service.generate_recommendation(
            violation=sample_violation,
            council_mode=True,
        )
        durations.append(time.time() - start)

    p95 = sorted(durations)[94]  # 95th percentile
    assert p95 < 8.0, f"Council mode p95 latency {p95}s exceeds 8s target"

@pytest.mark.benchmark
async def test_single_mode_latency_p95():
    """Single mode should complete in <3s (p95)"""
    durations = []
    for _ in range(100):
        start = time.time()
        await council_service.generate_recommendation(
            violation=sample_violation,
            council_mode=False,
        )
        durations.append(time.time() - start)

    p95 = sorted(durations)[94]
    assert p95 < 3.0, f"Single mode p95 latency {p95}s exceeds 3s target"

@pytest.mark.benchmark
async def test_auto_fallback_on_timeout():
    """Should auto-fallback to single mode if council >8s"""
    # Mock slow providers
    with mock.patch.object(council_service, '_query_provider', slow_mock):
        result = await council_service.generate_recommendation(
            violation=sample_violation,
            council_mode=True,
        )

    # Verify fallback was used
    assert result.fallback_used is True
    assert result.fallback_reason == "timeout"
```

### Performance Targets

| Metric | Target | Fallback Trigger |
|--------|--------|------------------|
| Single Mode (p95) | <3s | After 10s → Rule-based |
| Council Mode (p95) | <8s | After 8s → Single mode |
| Stage 1 (Parallel) | <3s | Per-provider timeout |
| Stage 2 (Ranking) | <2s | Skip if timeout |
| Stage 3 (Synthesis) | <3s | Use majority vote |

---

## Day 5: Documentation + CTO Sign-off ✅ COMPLETE

**Status**: ✅ COMPLETE (December 4, 2025)
**CTO Rating**: 9.5/10
**Deliverables**: OpenAPI spec (4 endpoints, 10 schemas), ADR-015, CTO Sign-off Report

### Documentation Tasks

| # | Task | File | Est. | Owner | Status |
|---|------|------|------|-------|--------|
| 5.1 | Update OpenAPI spec | `docs/02-Design-Architecture/03-API-Design/openapi.yml` | 1h | BE | ✅ DONE |
| 5.2 | Create ADR-015 | `docs/02-design/01-ADRs/ADR-015-AI-Council-Testing.md` | 1h | BE | ✅ DONE |
| 5.3 | CTO Sign-off Report | `docs/09-Executive-Reports/01-CTO-Reports/2025-12-04-CTO-SPRINT-26-FINAL-SIGNOFF.md` | 1h | BE | ✅ DONE |
| 5.4 | Update Sprint Plan | This document | 0.5h | BE | ✅ DONE |

### Sign-off Checklist

| # | Criteria | Target | Status |
|---|----------|--------|--------|
| 1 | Unit test coverage | 95%+ | ✅ DONE (19 tests, 631 lines) |
| 2 | Integration tests passing | 100% | ✅ DONE (18 tests, 517 lines) |
| 3 | Performance benchmark | <8s p95 | ✅ DONE (11 benchmarks, 631 lines) |
| 4 | Audit logging implemented | Complete | ✅ DONE (Day 1) |
| 5 | Compliance Scanner integrated | Complete | ✅ DONE (Day 3) |
| 6 | Documentation complete | Complete | ✅ DONE (Day 5) |
| 7 | Security review | PASS | ✅ DONE (Day 5) |
| 8 | CTO approval | ✅ | ✅ APPROVED (Day 5) |

---

## Deliverables Summary

### New Files (~850 lines)

| File | Lines | Description |
|------|-------|-------------|
| `backend/app/services/ai_council_service.py` | 450 | Core 3-stage deliberation |
| `backend/app/schemas/council.py` | 100 | Pydantic models |
| `backend/app/api/routes/council.py` | 150 | API endpoints |
| `tests/unit/services/test_ai_council.py` | 300 | Unit tests |
| `tests/integration/test_ai_council.py` | 200 | Integration tests |
| `tests/performance/test_council_benchmark.py` | 100 | Benchmark tests |

### Modified Files (~75 lines)

| File | Changes | Description |
|------|---------|-------------|
| `backend/app/services/audit_service.py` | +15 | AI_COUNCIL_* actions |
| `backend/app/services/compliance_scanner.py` | +50 | Council integration |
| `backend/app/middleware/business_metrics.py` | +30 | Prometheus metrics |

---

## Risk Mitigation

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Council latency >8s | Medium | High | Auto-fallback to single mode |
| Provider failures | Low | Medium | Multi-provider redundancy |
| Budget overrun | Low | Medium | Budget limits, alerts at 80/90% |
| Audit log overhead | Low | Low | Async logging, batch writes |

---

## Dependencies

### Required (Before Sprint 26)
- ✅ `OllamaService` - Available (Sprint 21)
- ✅ `AIRecommendationService` - Available (Sprint 21 Day 3)
- ✅ `AuditService` - Available (Sprint 23 Day 1)
- ✅ `ComplianceScanner` - Available (Sprint 21 Day 1)

### Optional (Enhancement)
- ⏳ Claude API key - For cloud fallback
- ⏳ GPT-4 API key - For cloud fallback

---

## Success Metrics

| Metric | Before | After | Target |
|--------|--------|-------|--------|
| Recommendation Accuracy (CRITICAL) | 85% | 95% | 95%+ |
| User Satisfaction | 4.0★ | 4.5★ | 4.5★ |
| Violation Resolution Rate | 60% | 80% | 80%+ |
| Council Mode Latency (p95) | N/A | <8s | <8s |

---

**Sprint Status**: ✅ COMPLETE - APPROVED FOR MERGE
**CTO Rating**: 9.5/10
**Pre-Planning**: Complete (Sprint 22)
**Implementation**: Complete (December 4, 2025)
**Final Sign-off**: CTO Approved (December 4, 2025)
