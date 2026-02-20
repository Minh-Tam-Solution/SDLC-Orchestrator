# Sprint 22: Hardening & Internal Pilot

**Version**: 1.0.0
**Date**: November 29, 2025
**Status**: PLANNED
**Authority**: CTO + CPO + CEO
**Foundation**: Gate G3 (Ship Ready) Requirements
**Framework**: SDLC 6.1.0
**Week**: 12 of 13 (Dec 9-13, 2025)

---

## Sprint Overview

**Sprint Goal**: Complete hardening phase with BFlow/NQH internal pilot, performance optimization, and Gate G3 readiness.

**Duration**: 5 days
**Team**: Full team (Backend 100%, Frontend 100%, DevOps 50%, QA 100%)
**Priority**: P0 - Critical (Launch Readiness)

---

## Context: Why Hardening Sprint?

```yaml
Pre-Launch Requirements:
  ✅ All core features implemented (Sprint 1-20)
  ✅ Compliance Scanner (Sprint 21)
  ⏳ Performance optimization (this sprint)
  ⏳ Security hardening (this sprint)
  ⏳ Internal pilot (this sprint)
  ⏳ Gate G3 approval (this sprint)

Gate G3 Exit Criteria:
  - Zero P0/P1 bugs
  - <100ms p95 API latency
  - 99.9%+ uptime (pilot period)
  - 5+ internal teams onboarded
  - CTO + CPO + CEO sign-off
```

---

## Day 1: Performance Optimization

### Tasks

| # | Task | File | Est. | Owner |
|---|------|------|------|-------|
| 1.1 | Run load tests (Locust) | tests/load/locust_scenarios.py | 2h | BE |
| 1.2 | Optimize slow queries | backend/app/db/queries.py | 3h | BE |
| 1.3 | Add Redis caching | backend/app/services/cache_service.py | 2h | BE |
| 1.4 | Frontend bundle optimization | frontend/web/vite.config.ts | 1h | FE |

### Performance Targets

| Metric | Current | Target | Priority |
|--------|---------|--------|----------|
| API latency (p95) | ~150ms | <100ms | P0 |
| Dashboard load | ~2s | <1s | P0 |
| Gate evaluation | ~200ms | <100ms | P0 |
| Evidence upload (10MB) | ~5s | <2s | P1 |
| Compliance scan | ~60s | <30s | P1 |

### Optimization Strategies

```python
# 1. Query Optimization - Add indexes
# backend/alembic/versions/xxx_add_performance_indexes.py

def upgrade():
    # Composite indexes for common queries
    op.create_index('idx_gates_project_status', 'gates', ['project_id', 'status'])
    op.create_index('idx_evidence_gate_type', 'gate_evidence', ['gate_id', 'evidence_type'])
    op.create_index('idx_scans_project_date', 'compliance_scans', ['project_id', 'scanned_at'])

    # Partial indexes for active records
    op.execute("""
        CREATE INDEX idx_projects_active ON projects(id)
        WHERE deleted_at IS NULL
    """)

# 2. Redis Caching - Cache frequently accessed data
# backend/app/services/cache_service.py

class CacheService:
    def __init__(self, redis: Redis):
        self.redis = redis
        self.default_ttl = 300  # 5 minutes

    async def get_project_stats(self, project_id: str) -> ProjectStats:
        """Cache project statistics for dashboard."""
        cache_key = f"project_stats:{project_id}"

        # Try cache first
        cached = await self.redis.get(cache_key)
        if cached:
            return ProjectStats.parse_raw(cached)

        # Compute and cache
        stats = await compute_project_stats(project_id)
        await self.redis.setex(cache_key, self.default_ttl, stats.json())
        return stats

    async def invalidate_project_cache(self, project_id: str):
        """Invalidate cache when project changes."""
        await self.redis.delete(f"project_stats:{project_id}")
```

### Deliverables
- [ ] Load test results (1000 concurrent users)
- [ ] Query optimization report (before/after)
- [ ] Cache hit rate dashboard
- [ ] Bundle size reduction (target: <500KB)

---

## Day 2: Security Hardening

### Tasks

| # | Task | File | Est. | Owner |
|---|------|------|------|-------|
| 2.1 | Run Semgrep security scan | .github/workflows/security.yml | 1h | DevOps |
| 2.2 | Fix identified vulnerabilities | Various | 3h | BE |
| 2.3 | Add rate limiting | backend/app/middleware/rate_limit.py | 2h | BE |
| 2.4 | Audit logging enhancement | backend/app/services/audit_service.py | 2h | BE |

### Security Checklist (OWASP ASVS L2)

```yaml
Authentication:
  - [x] JWT tokens with 15min expiry
  - [x] Refresh token rotation
  - [x] Password policy (12+ chars, bcrypt cost=12)
  - [ ] Rate limiting on /auth endpoints (100 req/min)
  - [ ] Account lockout after 5 failed attempts

Authorization:
  - [x] RBAC with 13 roles
  - [x] Row-level security on projects
  - [ ] API scope validation enhanced
  - [ ] Admin action audit trail

Input Validation:
  - [x] Pydantic validation on all endpoints
  - [x] SQL injection prevention (SQLAlchemy ORM)
  - [ ] File upload validation (type, size, content)
  - [ ] XSS prevention in frontend

Data Protection:
  - [x] AES-256 encryption for sensitive fields
  - [x] TLS 1.3 for all connections
  - [ ] Evidence file encryption at rest
  - [ ] Secret rotation (90-day policy)
```

### Rate Limiting Implementation

```python
# backend/app/middleware/rate_limit.py
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

# Apply to auth endpoints
@router.post("/login")
@limiter.limit("10/minute")
async def login(request: Request):
    pass

@router.post("/refresh")
@limiter.limit("30/minute")
async def refresh(request: Request):
    pass

# Global rate limit
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, rate_limit_exceeded_handler)
```

### Deliverables
- [ ] Semgrep scan report (0 critical/high)
- [ ] Rate limiting active on all endpoints
- [ ] Audit log for admin actions
- [ ] Security documentation updated

---

## Day 3: Internal Pilot Setup

### Tasks

| # | Task | File | Est. | Owner |
|---|------|------|------|-------|
| 3.1 | Prepare pilot environments | terraform/pilot/ | 2h | DevOps |
| 3.2 | Create pilot team accounts | backend/scripts/create_pilot_users.py | 1h | BE |
| 3.3 | Import real project data | backend/scripts/import_project.py | 2h | BE |
| 3.4 | Write pilot onboarding guide | docs/08-Team-Management/PILOT-GUIDE.md | 2h | PM |
| 3.5 | Setup monitoring dashboards | grafana/dashboards/pilot.json | 1h | DevOps |

### Pilot Teams

| Team | Project | Lead | Status |
|------|---------|------|--------|
| BFlow Platform | bflow-platform | CEO | Ready |
| NQH-Bot | nqh-bot | CTO | Ready |
| SDLC Orchestrator | sdlc-orchestrator | CPO | Ready |
| SDLC Enterprise Framework | sdlc-framework | PM | Ready |
| MTEP Platform | mtep | EM | Optional |

### Pilot Success Metrics

```yaml
Quantitative:
  - Onboarding time: <30 min per team
  - Gate creation: 5+ gates per project
  - Evidence uploads: 10+ files per gate
  - Compliance scans: 1+ per day per project
  - Error rate: <1%

Qualitative:
  - User feedback: NPS > 50
  - Feature requests collected: 10+
  - Bug reports: <5 P0/P1
  - Training feedback: >8/10 satisfaction
```

### Deliverables
- [ ] 5 pilot teams onboarded
- [ ] Real projects imported
- [ ] Monitoring dashboard live
- [ ] Pilot guide distributed

---

## Day 4: Bug Fixes & Polish

### Tasks

| # | Task | File | Est. | Owner |
|---|------|------|------|-------|
| 4.1 | Fix pilot feedback bugs | Various | 4h | BE+FE |
| 4.2 | UI polish and consistency | frontend/web/src/components/ | 3h | FE |
| 4.3 | Error message improvements | backend/app/core/errors.py | 1h | BE |

### Bug Priority Matrix

| Priority | SLA | Examples |
|----------|-----|----------|
| P0 | Fix immediately | Login broken, data loss, security |
| P1 | Fix same day | Core feature broken, major UX issue |
| P2 | Fix this sprint | Minor feature bug, cosmetic |
| P3 | Backlog | Nice-to-have, enhancement |

### Known Issues to Address

```yaml
From E2E Tests:
  - [ ] Toast notifications sometimes don't appear
  - [ ] Sidebar doesn't highlight active page
  - [ ] Evidence upload progress bar inaccurate

From Manual Testing:
  - [ ] Long project names overflow card
  - [ ] Date formatting inconsistent (UTC vs local)
  - [ ] Empty state messages need improvement

From Pilot Feedback:
  - [ ] (To be collected Day 3)
```

### Deliverables
- [ ] Zero P0/P1 bugs
- [ ] UI consistency audit passed
- [ ] Error messages user-friendly
- [ ] Pilot feedback addressed

---

## Day 5: Gate G3 Preparation

### Tasks

| # | Task | File | Est. | Owner |
|---|------|------|------|-------|
| 5.1 | Complete Gate G3 evidence package | docs/09-Executive-Reports/01-Gate-Reviews/ | 3h | PM |
| 5.2 | Create launch runbook | docs/05-Deployment-Operations/LAUNCH-RUNBOOK.md | 2h | DevOps |
| 5.3 | Conduct Gate G3 review meeting | N/A | 2h | All |
| 5.4 | Get CTO + CPO + CEO sign-off | Gate approval form | 1h | PM |

### Gate G3 Evidence Package

```yaml
Required Documents:
  1. Technical Readiness Report:
     - Test coverage: 95%+ backend, 90%+ frontend
     - Security scan: 0 critical/high
     - Performance benchmark: <100ms p95
     - Load test: 1000 concurrent users

  2. Feature Completion Report:
     - API coverage: 100% (40/40 endpoints)
     - UI completeness: 100%
     - Documentation: 100%

  3. Pilot Results Summary:
     - 5 teams onboarded
     - Success metrics achieved
     - Bug fix rate: 100% P0/P1

  4. Launch Readiness Checklist:
     - Infrastructure: Ready
     - Monitoring: Active
     - Support: On-call schedule
     - Rollback: Tested

  5. Risk Assessment:
     - Known risks identified
     - Mitigation plans documented
     - Go/No-Go recommendation
```

### Gate G3 Approval Criteria

| Criterion | Target | Status |
|-----------|--------|--------|
| Zero P0/P1 bugs | 0 | ⏳ |
| Test coverage | 95%+ | ⏳ |
| Security scan | PASS | ⏳ |
| Performance | <100ms p95 | ⏳ |
| Pilot success | 5 teams | ⏳ |
| CTO approval | Yes | ⏳ |
| CPO approval | Yes | ⏳ |
| CEO approval | Yes | ⏳ |

### Deliverables
- [ ] Gate G3 evidence package complete
- [ ] Launch runbook ready
- [ ] Gate G3 meeting conducted
- [ ] All approvals obtained
- [ ] Go/No-Go decision: **GO**

---

## Sprint Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| API Latency (p95) | <100ms | Load test results |
| Error Rate | <1% | Monitoring dashboard |
| Pilot Onboarding | 5 teams | Team count |
| Bug Fix Rate | 100% P0/P1 | Bug tracker |
| Gate G3 | PASS | Approval form |

---

## Risk Assessment

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Performance issues under load | Medium | High | Pre-launch load testing, scaling plan |
| Security vulnerabilities | Low | Critical | Multiple scan tools, external audit |
| Pilot team blockers | Medium | Medium | Dedicated support, quick bug fixes |
| Gate G3 rejection | Low | High | Daily checkpoint with approvers |

---

## Definition of Done

- [ ] API latency <100ms p95 (load tested)
- [ ] Zero security vulnerabilities (critical/high)
- [ ] 5 internal teams onboarded
- [ ] Zero P0/P1 bugs
- [ ] Gate G3 evidence package complete
- [ ] CTO + CPO + CEO approval obtained
- [ ] Launch runbook ready
- [ ] On-call schedule defined

---

## Post-Sprint: Week 13 (Launch)

After Sprint 22 completion:

```yaml
Week 13 Activities:
  Day 1: Final deployment to production
  Day 2: Internal announcement
  Day 3-4: Monitor & support
  Day 5: Sprint retrospective + MVP celebration

Success Criteria:
  - Production live: ✓
  - Zero incidents: ✓
  - User feedback positive: ✓
  - MVP 90-day goal achieved: ✓
```

---

*SDLC Orchestrator - First Governance-First Platform on SDLC 6.1.0. Zero Mock Policy enforced.*

**Sprint 22 Focus**: "Ship Ready - From pilot to production with confidence"
