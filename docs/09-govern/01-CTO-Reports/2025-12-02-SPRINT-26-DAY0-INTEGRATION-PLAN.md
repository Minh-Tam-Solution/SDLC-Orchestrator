# Sprint 26-28: AI Council Integration Planning Document (PRE-PLANNING)

**Date**: December 2, 2025
**Author**: Backend Lead
**Status**: PRE-PLANNING COMPLETE - Ready for Sprint 26
**Current Sprint**: 22 (Active)
**Target Sprint**: 26-28 (Week 11-13)
**Approved By**: CTO/CPO Review (9.2/10)

> **NOTE**: This is a pre-planning document prepared during Sprint 22. Implementation will begin in Sprint 26.

---

## Executive Summary

This document details the integration points identified during Sprint 26 Day 0 planning session, addressing all 5 CTO/CPO conditions for AI Council implementation.

---

## 1. Integration Points Analysis

### 1.1 Compliance Scanner Integration (CTO Condition #3)

**File**: `backend/app/services/compliance_scanner.py` (869 lines)

**Current State**:
- Scans projects for SDLC 4.9.1 compliance violations
- 5 check methods: documentation, stage sequence, evidence, OPA policies, doc-code drift
- Violations have severity: `critical`, `high`, `medium`, `low`, `info`
- Recommendations are currently static strings

**Integration Point** (Line 271-405 - `scan_project` method):
```python
# After Step 5 (doc-code drift), add Step 6: AI Council for CRITICAL/HIGH
# Line ~347-350 - Add AI Council recommendation enhancement

# CRITICAL/HIGH violations → AI Council mode (multi-LLM deliberation)
# MEDIUM/LOW violations → Single mode (Ollama only)
```

**Changes Required** (+50 lines):
1. Import `AICouncilService`
2. Add `ai_council` parameter to `__init__`
3. New method: `_enhance_with_ai_recommendations(violations)`
4. Logic: If `severity in ('critical', 'high')` → use Council mode
5. Update `Violation` dataclass with `ai_recommendation`, `ai_council_used` fields

**Code Sketch**:
```python
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
            project_context=project,
            council_mode=council_mode,
        )

        violation.recommendation = recommendation.final_answer
        violation.ai_council_used = council_mode
        violation.ai_confidence = recommendation.confidence_score

    return violations
```

### 1.2 Audit Service Integration (CTO Condition #2)

**File**: `backend/app/services/audit_service.py` (358 lines)

**Current State**:
- `AuditAction` enum with 50+ actions
- Already has `AI_RECOMMENDATION_REQUESTED` (line 98) and `AI_RECOMMENDATION_APPLIED` (line 99)
- Missing: `AI_COUNCIL_REQUEST` for multi-LLM deliberation tracking

**Integration Point** (Line 31-112 - `AuditAction` enum):
```python
# Add after line 99 (AI Events section)
AI_COUNCIL_REQUEST = "AI_COUNCIL_REQUEST"
AI_COUNCIL_STAGE1_COMPLETE = "AI_COUNCIL_STAGE1_COMPLETE"
AI_COUNCIL_STAGE2_COMPLETE = "AI_COUNCIL_STAGE2_COMPLETE"
AI_COUNCIL_STAGE3_COMPLETE = "AI_COUNCIL_STAGE3_COMPLETE"
```

**Changes Required** (+15 lines):
1. Add 4 new `AuditAction` enum values for council tracking
2. Add helper method `log_ai_council_request()` in `AuditService` class

**Audit Trail Schema**:
```python
{
    "action": "AI_COUNCIL_REQUEST",
    "user_id": "uuid",
    "resource_type": "violation",
    "resource_id": "violation_uuid",
    "details": {
        "council_mode": true,
        "providers": ["ollama", "claude", "gpt4"],
        "stage1_duration_ms": 2500,
        "stage2_duration_ms": 1500,
        "stage3_duration_ms": 1000,
        "total_duration_ms": 5000,
        "confidence_score": 9.2,
        "cost_usd": 0.05
    }
}
```

### 1.3 AI Recommendation Service Extension

**File**: `backend/app/services/ai_recommendation_service.py` (839 lines)

**Current State**:
- Single recommendation with fallback chain (Ollama → Claude → GPT-4 → Rule-based)
- No parallel query support
- No multi-provider synthesis

**Integration Pattern** (Do NOT modify - extend):
```python
# AICouncilService EXTENDS (not replaces) AIRecommendationService
# Existing single-provider mode remains default
# Council mode is opt-in for CRITICAL/HIGH violations

class AICouncilService:
    """
    Multi-LLM Council Service (extends AIRecommendationService pattern)

    Modes:
    - Single: Use existing AIRecommendationService (default)
    - Council: 3-stage deliberation for critical violations
    """

    def __init__(self, db: AsyncSession, ai_service: AIRecommendationService):
        self.db = db
        self.ai_service = ai_service  # Reuse existing service for single mode
```

---

## 2. Performance Targets (CTO Condition #5)

### 2.1 Latency Budgets

| Mode | Target (p95) | Max Timeout | Fallback Trigger |
|------|--------------|-------------|------------------|
| Single Mode | <3s | 10s | After 10s → Rule-based |
| Council Mode | <8s | 30s | After 8s → Single mode |
| Stage 1 (Parallel) | <3s | 10s | Per-provider timeout |
| Stage 2 (Ranking) | <2s | 10s | Skip if timeout |
| Stage 3 (Synthesis) | <3s | 10s | Use majority vote |

### 2.2 Benchmark Test Requirements

```python
# tests/performance/test_ai_council_benchmark.py

import pytest
from app.services.ai_council_service import AICouncilService

@pytest.mark.benchmark
async def test_council_mode_latency_p95():
    """Council mode should complete in <8s (p95)"""
    # Run 100 requests
    # Measure p95 latency
    # Assert p95 < 8000ms

@pytest.mark.benchmark
async def test_single_mode_latency_p95():
    """Single mode should complete in <3s (p95)"""
    # Run 100 requests
    # Measure p95 latency
    # Assert p95 < 3000ms

@pytest.mark.benchmark
async def test_auto_fallback_on_timeout():
    """Should auto-fallback to single mode if council >8s"""
    # Mock slow providers
    # Verify fallback triggers at 8s
```

### 2.3 Performance Monitoring (Prometheus Metrics)

```python
# New metrics for AI Council
COUNCIL_REQUEST_DURATION = Histogram(
    "sdlc_ai_council_request_duration_seconds",
    "AI Council request duration",
    ["mode", "stage"],
    buckets=[0.5, 1, 2, 3, 5, 8, 10, 15, 30]
)

COUNCIL_STAGE_DURATION = Histogram(
    "sdlc_ai_council_stage_duration_seconds",
    "AI Council stage duration",
    ["stage"],  # stage1, stage2, stage3
    buckets=[0.5, 1, 2, 3, 5, 10]
)

COUNCIL_FALLBACK_TOTAL = Counter(
    "sdlc_ai_council_fallback_total",
    "AI Council fallback events",
    ["reason"]  # timeout, error, budget_exceeded
)
```

---

## 3. Implementation Checklist

### Day 0 - Integration Planning ✅
- [x] Review `compliance_scanner.py` - Identified integration points (line 271-405)
- [x] Review `audit_service.py` - Plan `AI_COUNCIL_REQUEST` action (line 31-112)
- [x] Review `ai_recommendation_service.py` - Extension pattern confirmed
- [x] Define performance targets (<8s Council mode p95)
- [x] Document integration architecture

### Day 1-2 - Core Service
- [ ] `ai_council_service.py` - 3-stage deliberation service (~450 lines)
- [ ] `council.py` (schemas) - Pydantic models (~100 lines)
- [ ] Add `AI_COUNCIL_*` audit actions to `audit_service.py` (+15 lines)
- [ ] Add Prometheus metrics for council monitoring

### Day 3 - API + Integration
- [ ] `council.py` (routes) - API endpoints (~150 lines)
- [ ] Update `compliance_scanner.py` - AI Council integration (+50 lines)
- [ ] OpenAPI spec updates

### Day 4 - Tests + Benchmark
- [ ] Unit tests - 95%+ coverage
- [ ] Integration tests - Evidence Vault storage
- [ ] Performance benchmark - <8s p95 validation

### Day 5 - Documentation + Sign-off
- [ ] OpenAPI docs - Swagger UI
- [ ] CTO final sign-off
- [ ] All 5 conditions verified ✅

---

## 4. File Changes Summary

| File | Lines Added | Lines Modified | Description |
|------|-------------|----------------|-------------|
| `backend/app/services/ai_council_service.py` | +450 | NEW | Core 3-stage deliberation |
| `backend/app/schemas/council.py` | +100 | NEW | Pydantic models |
| `backend/app/api/routes/council.py` | +150 | NEW | API endpoints |
| `backend/app/services/audit_service.py` | +15 | 0 | AI_COUNCIL_* actions |
| `backend/app/services/compliance_scanner.py` | +50 | 5 | AI Council integration |
| `backend/app/middleware/business_metrics.py` | +30 | 0 | Council metrics |
| `tests/unit/services/test_ai_council.py` | +300 | NEW | Unit tests |
| `tests/integration/test_ai_council.py` | +200 | NEW | Integration tests |
| `tests/performance/test_ai_council_benchmark.py` | +100 | NEW | Benchmark tests |
| **TOTAL** | **~1,395** | **~5** | |

---

## 5. Risk Mitigation

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Council latency >8s | Medium | High | Auto-fallback to single mode |
| Provider failures | Low | Medium | Multi-provider redundancy |
| Budget overrun | Low | Medium | Budget limits, alerts at 80/90% |
| Audit log overhead | Low | Low | Async logging, batch writes |

---

## 6. Dependencies

### Required (Before Implementation)
- ✅ `OllamaService` - Available (Sprint 21)
- ✅ `AIRecommendationService` - Available (Sprint 21 Day 3)
- ✅ `AuditService` - Available (Sprint 23 Day 1)
- ✅ `ComplianceScanner` - Available (Sprint 21 Day 1)

### Optional (Enhancement)
- ⏳ Claude API key - For cloud fallback
- ⏳ GPT-4 API key - For cloud fallback

---

## 7. CTO Condition Status

| # | Condition | Status | Notes |
|---|-----------|--------|-------|
| 1 | Integration Planning Session | ✅ COMPLETE | This document |
| 2 | Add Audit Logging | ✅ PLANNED | +15 lines to audit_service.py |
| 3 | Compliance Scanner Integration | ✅ PLANNED | +50 lines to compliance_scanner.py |
| 4 | VS Code Extension Scope Reduction | ✅ ACCEPTED | MVP in Sprint 27, Phase 2 in Sprint 29 |
| 5 | Performance Benchmark (<8s p95) | ✅ PLANNED | Benchmark tests defined |

---

## 8. Next Steps (When Sprint 26 Begins)

1. **Sprint 26 Day 1**: Begin `ai_council_service.py` implementation
2. **Sprint 26 Day 1**: Add `AI_COUNCIL_*` audit actions
3. **Sprint 26 Day 2**: Complete 3-stage deliberation logic
4. **Sprint 26 Day 3**: API endpoints + Compliance Scanner integration
5. **Sprint 26 Day 4**: Tests + Performance benchmark validation
6. **Sprint 26 Day 5**: Documentation + CTO final sign-off

---

**Pre-Planning Complete**: ✅ Ready for Sprint 26 Implementation
**Current Sprint**: 22
**Target Sprint**: 26-28
**CTO Conditions**: 5/5 Addressed
**Approved By**: CTO + CPO (9.2/10 Rating)
**Next Review**: Sprint 26 Day 0 (Implementation Kickoff)
