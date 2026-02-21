# ADR-021: Analytics Service with Mixpanel Integration

**Status**: SUPERSEDED (Sprint 190 — analytics_service deleted, replaced by telemetry_service)
**Date**: December 21, 2025
**Approved By**: CTO (Quoc Nguyen Huu)
**Approval Date**: December 21, 2025
**Deciders**: CTO, Backend Lead, Data Team
**Stage**: 02 - DESIGN (HOW)
**Epic**: EP-01/EP-02 - AI Safety Foundation
**Sprint**: Sprint 41 (Jan 6-17, 2026)
**Framework**: SDLC 6.1.0

---

## CTO Approval Notes

**Decision**: ✅ APPROVED WITH CONDITIONS

**Conditions**:
1. **Privacy Hash**: Add salt to `_hash_user_id()` - use `settings.ANALYTICS_USER_SALT`
2. **Circuit Breaker**: Implement for Mixpanel API (5 failures → disable 5 min)
3. **Retention Cron**: Ensure 90-day cleanup với alerting (Sprint 41)

**Approval Checklist**:
- [x] CTO Review: Architecture approved (Dual approach correct)
- [x] Backend Lead: Implementation feasible
- [x] Data Team: GDPR compliance validated
- [x] Security Lead: No PII (with salt requirement)
- [ ] Legal: Mixpanel DPA (non-blocking, delegate to Legal team)

---

## Context and Problem Statement

Sprint 41 requires product analytics to track:
- User engagement (DAU/WAU, retention, feature adoption)
- AI Safety Layer metrics (validation pass rate, tool usage)
- Design Partner feedback (workshop attendance, NPS scores)
- SDLC gate evaluations (pass rates, evidence completeness)

**Problem**: We need a robust analytics solution that:
1. Tracks events in real-time with <100ms latency
2. Supports batch processing (100+ events/batch)
3. Provides funnel analysis and cohort tracking
4. Complies with GDPR (EU data residency, user privacy)
5. Integrates with existing PostgreSQL database
6. Costs <$500/month for Year 1 (10K MAU target)

**Current State**: No analytics infrastructure. Relying on manual SQL queries for metrics.

**Desired State**: Automated product analytics with self-service dashboards.

---

## Decision Drivers

### Technical Requirements
- **Performance**: <100ms event tracking (p95), <1s metric queries
- **Scale**: Support 10K MAU Year 1, 100K MAU Year 3
- **Privacy**: GDPR-compliant, no PII in event properties
- **Integration**: Easy integration with FastAPI backend, React frontend
- **Batch Support**: Efficiently handle bulk event imports (historical data)

### Business Requirements
- **Cost**: Free tier sufficient for 6 months, <$500/month Year 1
- **Time to Value**: Setup in <2 days (Sprint 41 Day 1-2)
- **Self-Service**: PM/Product can query metrics without engineering help
- **Compliance**: SOC 2, GDPR, HIPAA support for Enterprise customers

### Team Constraints
- **Backend**: FastAPI + PostgreSQL + Redis (existing stack)
- **Frontend**: React + TanStack Query (existing stack)
- **DevOps**: Prefer SaaS over self-hosted (limited DevOps capacity)
- **Timeline**: Must be ready by Sprint 41 Day 2 (Jan 7, 2026)

---

## Considered Options

### Option 1: Self-Hosted (PostHog/Plausible)

**Pros**:
- ✅ Full data control (GDPR, data residency)
- ✅ No vendor lock-in
- ✅ Unlimited events (no per-event cost)
- ✅ Open source (can customize)

**Cons**:
- ❌ High DevOps overhead (deploy, maintain, scale)
- ❌ Longer setup time (3-5 days vs 1 day)
- ❌ Limited built-in dashboards (need custom SQL)
- ❌ No funnel analysis out-of-box
- ❌ Infrastructure cost (~$200/month for managed PostgreSQL)

**Cost**: $200-300/month (infrastructure) + 2 days DevOps setup

---

### Option 2: Mixpanel (SaaS)

**Pros**:
- ✅ Fast setup (<2 hours SDK integration)
- ✅ Rich dashboards (funnels, retention, cohorts)
- ✅ Free tier (100K events/month = ~3.3K/day)
- ✅ GDPR-compliant (EU data residency option)
- ✅ Python + JavaScript SDKs (official support)
- ✅ Proven at scale (Uber, Twitter, Microsoft)

**Cons**:
- ❌ Vendor lock-in (export via API, but limited)
- ❌ Cost scales with events ($999/month for 1M events)
- ❌ No self-hosting option

**Cost**:
- Year 1: $0 (free tier, <100K events/month)
- Year 2: $499/month (500K events/month)
- Year 3: $999/month (1M events/month)

---

### Option 3: Amplitude (SaaS)

**Pros**:
- ✅ Similar features to Mixpanel (funnels, cohorts)
- ✅ Better free tier (10M events/month)
- ✅ Strong mobile analytics (iOS/Android SDKs)
- ✅ GDPR-compliant

**Cons**:
- ❌ More complex SDK (steeper learning curve)
- ❌ Slower dashboard (anecdotal from team)
- ❌ Less popular (smaller community)

**Cost**:
- Year 1: $0 (free tier, <10M events/month)
- Year 2: $999/month (similar to Mixpanel)

---

### Option 4: Dual Approach (PostgreSQL + Mixpanel)

**Pros**:
- ✅ PostgreSQL for audit trail (90-day retention)
- ✅ Mixpanel for analytics dashboards
- ✅ No vendor lock-in (data in our DB)
- ✅ Best of both worlds (control + UX)

**Cons**:
- ❌ More complex (dual writes)
- ❌ Slight latency increase (2 writes per event)
- ❌ Need retry logic (Mixpanel API can fail)

**Cost**: Same as Option 2 (Mixpanel), plus our existing PostgreSQL cost

---

## Decision Outcome

**Chosen Option**: **Option 4 - Dual Approach (PostgreSQL + Mixpanel)**

**Rationale**:
1. **GDPR Compliance**: Store events in our PostgreSQL (EU region) for 90 days, giving us full control for GDPR requests
2. **Analytics UX**: Use Mixpanel dashboards for PM/Product self-service (funnels, cohorts, retention)
3. **No Vendor Lock-In**: All event data in our database, can switch analytics provider anytime
4. **Audit Trail**: PostgreSQL provides immutable audit log for SOC 2 compliance
5. **Cost**: $0 Year 1 (free tier), scales to ~$500/month Year 2

**Implementation**:
- `AnalyticsService.track_event()` writes to both PostgreSQL and Mixpanel
- PostgreSQL: `analytics_events` table (90-day retention, auto-cleanup cron)
- Mixpanel: Real-time tracking (async, non-blocking)
- Retry logic: 3 attempts with exponential backoff if Mixpanel fails

---

## Architecture Design

### Component Diagram

```
┌─────────────────────────────────────────────────────────┐
│  FastAPI Backend (analytics_service.py)                 │
│                                                          │
│  track_event(user_id, event_name, properties)          │
│         │                                                │
│         ├─────────────┬──────────────────┐             │
│         │             │                  │             │
│         ▼             ▼                  ▼             │
│  [PostgreSQL]   [Mixpanel API]    [Redis Cache]       │
│  analytics_     (async HTTP)       (dedup 5min)        │
│  events                                                 │
│  (90 days)                                              │
└─────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│  React Frontend (useAnalytics.ts)                       │
│                                                          │
│  trackEvent('gate_passed', {gate_id: 'G2'})            │
│         │                                                │
│         └──────────────────► [Mixpanel Browser SDK]    │
│                               (client-side tracking)    │
└─────────────────────────────────────────────────────────┘
```

### Database Schema

```sql
-- Analytics Events Table (90-day retention)
CREATE TABLE analytics_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    event_name VARCHAR(100) NOT NULL,
    properties JSONB,
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

-- Indexes for performance
CREATE INDEX ix_analytics_user_created ON analytics_events(user_id, created_at);
CREATE INDEX ix_analytics_event_created ON analytics_events(event_name, created_at);
CREATE INDEX ix_analytics_created ON analytics_events(created_at);

-- AI Code Events Table (2-year retention for audit)
CREATE TABLE ai_code_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    pr_id VARCHAR(100),
    commit_sha VARCHAR(40),
    ai_tool_detected VARCHAR(50),
    confidence_score INTEGER,  -- 0-100
    validation_result VARCHAR(20) NOT NULL,  -- passed, failed, warning
    violations JSONB,
    duration_ms INTEGER,
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

-- Indexes for AI Code Events
CREATE INDEX ix_ai_code_project_created ON ai_code_events(project_id, created_at);
CREATE INDEX ix_ai_code_tool_result ON ai_code_events(ai_tool_detected, validation_result);
```

### API Endpoints

```yaml
# Track single event
POST /api/v1/analytics/events
Request:
  {
    "user_id": "uuid",
    "event_name": "gate_passed",
    "properties": {"gate_id": "G2", "project_id": "uuid"}
  }
Response: {"success": true, "event_id": "uuid"}

# Track batch events
POST /api/v1/analytics/events/batch
Request:
  {
    "events": [
      {"user_id": "uuid", "event_name": "user_login"},
      {"user_id": "uuid", "event_name": "gate_passed"}
    ]
  }
Response: {"success_count": 2, "total_count": 2}

# Get DAU metrics
GET /api/v1/analytics/metrics/dau?days=30
Response:
  {
    "daily_counts": {"2026-01-06": 45, "2026-01-07": 52},
    "avg_dau": 48.5
  }

# Get AI Safety metrics
GET /api/v1/analytics/metrics/ai-safety?days=7
Response:
  {
    "total_validations": 1234,
    "pass_rate": 0.87,
    "avg_duration_ms": 945,
    "top_tools": {"claude": 450, "cursor": 380}
  }
```

### Event Taxonomy

**Core Events** (10 minimum for Sprint 41):

```yaml
User Lifecycle:
  - user_login
  - user_logout
  - user_signup

Project Lifecycle:
  - project_created
  - project_deleted

Gate Lifecycle:
  - gate_evaluated
  - gate_passed
  - gate_failed

Evidence:
  - evidence_uploaded

AI Safety:
  - ai_safety_validation
```

---

## Consequences

### Positive Consequences

✅ **Fast Time to Value**: Setup in <2 days (Sprint 41 Day 1-2)
✅ **GDPR Compliant**: Data in our PostgreSQL (EU region), full control
✅ **No Vendor Lock-In**: Can switch from Mixpanel to Amplitude/PostHog anytime
✅ **Audit Trail**: PostgreSQL provides immutable log for SOC 2
✅ **Cost-Effective**: $0 Year 1, <$500/month Year 2
✅ **Self-Service Analytics**: PM/Product can query metrics without SQL
✅ **Proven at Scale**: Mixpanel used by Uber, Twitter, Microsoft

### Negative Consequences

⚠️ **Dual Writes**: Slight complexity (need retry logic)
⚠️ **Eventual Consistency**: Mixpanel may lag PostgreSQL by ~1s
⚠️ **Cost Risk**: If events exceed 100K/month, need to upgrade ($499/month)

### Risks and Mitigation

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| Mixpanel API fails | High | Low | Retry logic (3 attempts), fallback to PostgreSQL-only |
| Events exceed free tier | Medium | Medium | Monitor usage, alert at 80K/month, batch non-critical events |
| GDPR request slow | Medium | Low | Query PostgreSQL (full data), Mixpanel optional |
| Vendor price increase | Low | Medium | Can switch to Amplitude/PostHog (same API pattern) |

---

## Implementation Plan

### Sprint 41 Day 1-2 (Jan 6-7, 2026)

**Backend**:
1. ✅ Create `AnalyticsService` class
2. ✅ Add `analytics_events` table (Alembic migration)
3. ✅ Add `ai_code_events` table (Alembic migration)
4. ⏳ Integrate Mixpanel SDK (`pip install mixpanel`)
5. ⏳ Add `MIXPANEL_TOKEN` to config
6. ⏳ Create API endpoints (`/api/v1/analytics/events`)

**Frontend**:
1. ⏳ Create `useAnalytics` hook
2. ⏳ Integrate Mixpanel browser SDK
3. ⏳ Track 10 core events (user_login, gate_passed, etc)

**Testing**:
1. ⏳ Unit tests for `AnalyticsService` (95% coverage)
2. ⏳ Integration tests (PostgreSQL + Mixpanel)
3. ⏳ Load test (1000 events/sec)

### Sprint 41 Day 3-4 (Jan 8-9, 2026)

**Dashboards**:
1. ⏳ Create Mixpanel dashboard "Product Analytics"
2. ⏳ Add DAU/WAU chart
3. ⏳ Add funnel: Signup → Project Created → Gate Passed
4. ⏳ Add cohort: Design Partners vs Regular Users

**Documentation**:
1. ⏳ Update OpenAPI spec with analytics endpoints
2. ⏳ Create Runbook "Analytics Service Operations"
3. ⏳ Document event taxonomy (10+ events)

---

## Approval Checklist

- [x] **CTO Review**: Architecture approved ✅ (Dec 21, 2025)
- [x] **Backend Lead Review**: Implementation plan feasible ✅
- [x] **Data Team Review**: GDPR compliance validated ✅
- [x] **Security Lead Review**: No PII in event properties ✅ (with salt condition)
- [ ] **Legal Review**: Mixpanel DPA signed (non-blocking, in progress)

**Status**: ✅ APPROVED - PROCEED WITH IMPLEMENTATION

**Next Step**: Sprint 41 Day 3-4 implementation (Alembic migration + API endpoints)

---

## References

- [Mixpanel Documentation](https://docs.mixpanel.com/)
- [GDPR Compliance Guide](https://mixpanel.com/legal/gdpr/)
- [Sprint 41 Plan](../../04-build/02-Sprint-Plans/SPRINT-41-AI-SAFETY-FOUNDATION.md)
- [EP-02: AI Safety Layer](../../01-planning/02-Epics/EP-02-AI-SAFETY-LAYER.md)

---

**ADR Status**: ✅ APPROVED - Ready for Implementation
**Implementation**: 🚀 UNBLOCKED - Proceed with Sprint 41 Day 3-4
**Approval Date**: December 21, 2025
**Approved By**: CTO (Quoc Nguyen Huu)
