# Sprint 114 Metrics Specification

**Document Type:** Technical Specification  
**Sprint:** 114 - Dogfooding (WARNING Mode)  
**Date:** February 3-7, 2026  
**Status:** DRAFT → APPROVED  
**SDLC Stage:** 02-Design (Technical Specification)  
**Framework:** SDLC 6.0 Governance System  
**ADR Reference:** ADR-041  

---

## 1. Executive Summary

Sprint 114 enables **WARNING mode** on the SDLC-Orchestrator repository for dogfooding. This specification defines all metrics to track, measurement methods, thresholds, and success criteria for evaluating governance system performance during the 5-day dogfooding phase.

**Key Objectives:**
- Establish baseline metrics for governance system
- Identify false positives/negatives before enforcement
- Measure developer friction vs. time savings
- Validate Vibecoding Index accuracy
- Tune thresholds for Soft Enforcement (Sprint 115)

---

## 2. Metrics Categories

### 2.1 Developer Friction Metrics

#### DF-1: PR Latency Impact
**Definition:** Additional time added to PR lifecycle by governance checks  
**Measurement:** 
```python
pr_latency_impact = (pr_close_time_with_governance - pr_close_time_baseline) / pr_close_time_baseline * 100
```
**Target:** <10% increase in PR cycle time  
**Threshold (Rollback):** >25% increase triggers auto-rollback to OFF  
**Collection Method:** GitHub API webhook tracking PR timestamps
```python
# backend/app/services/metrics/pr_latency_tracker.py
@dataclass
class PRLatencyMetrics:
    pr_number: int
    opened_at: datetime
    first_governance_check_at: datetime
    governance_checks_duration: timedelta  # Total time in governance checks
    closed_at: datetime
    total_cycle_time: timedelta
    latency_impact_percent: float
```

#### DF-2: Developer Complaint Rate
**Definition:** % of PRs where developer expresses frustration with governance  
**Measurement:** 
- Comment sentiment analysis ("this is annoying", "false positive", "blocking me")
- Feedback form submissions (negative sentiment)
- Slack #governance-support messages  
**Target:** <5% of PRs have complaints  
**Threshold (Rollback):** >15% complaint rate triggers rollback  
**Collection Method:** 
```python
# backend/app/services/metrics/sentiment_analyzer.py
def analyze_pr_comments(pr_number: int) -> ComplaintScore:
    """
    Returns ComplaintScore with:
    - has_complaint: bool
    - sentiment_score: float (-1.0 to 1.0)
    - complaint_keywords: List[str]
    """
```

#### DF-3: Override/Break-Glass Usage
**Definition:** Number of times developers use manual override or CTO break-glass  
**Measurement:** Count of override events in audit log  
**Target:** <2 overrides per week (team of 10 developers)  
**Threshold (Rollback):** >5 overrides per day triggers review  
**Collection Method:** PostgreSQL query on `governance_audit_log` table
```sql
SELECT COUNT(*) 
FROM governance_audit_log 
WHERE event_type IN ('manual_override', 'break_glass') 
  AND created_at > NOW() - INTERVAL '24 hours';
```

---

### 2.2 Quality Assurance Metrics

#### QA-1: False Positive Rate
**Definition:** % of governance blocks that were incorrect (should have passed)  
**Measurement:**
```python
false_positive_rate = (num_false_positives / total_blocks) * 100
```
**Calculation Method:**
- Developer marks PR as "False Positive" in feedback form
- CTO reviews flagged PRs and confirms false positive
- Auto-detection: PR with index >80 that gets approved by CEO with "Good work" comment
**Target:** <10% false positive rate  
**Threshold (Rollback):** >20% false positive rate triggers rollback  
**Collection Method:**
```python
# backend/app/services/metrics/quality_metrics.py
@dataclass
class FalsePositiveMetrics:
    total_blocks: int
    developer_reported_fp: int
    cto_confirmed_fp: int
    auto_detected_fp: int  # Good work comments on blocked PRs
    false_positive_rate: float
```

#### QA-2: False Negative Rate
**Definition:** % of PRs that should have been blocked but passed (missed violations)  
**Measurement:**
- Post-merge issues requiring hotfix (traced back to missed governance checks)
- CEO manual review finding issues in approved PRs
- Security scan findings that governance should have caught
**Target:** <5% false negative rate  
**Threshold (Alert):** >10% false negative rate triggers alert to CTO  
**Collection Method:**
```python
# backend/app/services/metrics/quality_metrics.py
def track_false_negatives():
    """
    Track PRs that passed but had issues:
    - Hotfix PRs referencing original PR
    - CEO comments like "This should have been caught"
    - Security scan failures post-merge
    """
```

#### QA-3: Vibecoding Index Accuracy
**Definition:** Correlation between Vibecoding Index score and actual CEO time spent  
**Measurement:**
```python
# Expected: Index <30 = <5 min CEO time, Index >80 = >30 min CEO time
accuracy = correlation(vibecoding_index, actual_ceo_time_minutes)
```
**Target:** Pearson correlation r > 0.7 (strong positive correlation)  
**Threshold (Alert):** r < 0.5 triggers investigation  
**Collection Method:**
```python
# backend/app/services/metrics/index_accuracy_tracker.py
@dataclass
class IndexAccuracyMetrics:
    pr_number: int
    vibecoding_index: int
    predicted_ceo_time_minutes: float
    actual_ceo_time_minutes: float  # From CEO dashboard tracking
    accuracy_error: float  # abs(predicted - actual)
```

---

### 2.3 Time Savings Metrics

#### TS-1: Auto-Generation Time Saved
**Definition:** Time saved per PR by auto-generation features  
**Measurement:**
```python
time_saved = baseline_manual_time - actual_time_with_auto_gen
# Intent: 15 min → <1 min = 14 min saved
# Ownership: 2 min → <30 sec = 1.5 min saved
# Context: 5 min → automatic = 5 min saved
# Attestation: 8 min → 2 min = 6 min saved
# Total expected: ~26.5 min saved per PR
```
**Target:** >20 minutes saved per PR  
**Collection Method:**
```python
# backend/app/services/metrics/time_savings_tracker.py
@dataclass
class AutoGenTimeSavings:
    pr_number: int
    intent_generation_time_seconds: float
    ownership_suggestions_time_seconds: float
    context_attachment_time_seconds: float
    attestation_fill_time_seconds: float
    total_saved_minutes: float
    baseline_manual_minutes: float = 30.0
```

#### TS-2: CEO Time Saved
**Definition:** Reduction in CEO time spent on PR reviews  
**Measurement:**
```python
ceo_time_saved = baseline_40h_per_week - actual_hours_with_governance
```
**Target:** 40h → 20h per week (-50%)  
**Sprint 114 Baseline:** Establish baseline (WARNING mode doesn't block)  
**Collection Method:**
```python
# frontend/src/hooks/useCEODashboard.ts
const { data: timeSaved } = useCEOTimeSaved({
  timeRange: '7d',
  includeProjections: true,
});
```

#### TS-3: PR Review Cycle Time
**Definition:** Total time from PR open to CEO approval  
**Measurement:**
```python
review_cycle_time = pr_approved_at - pr_opened_at
```
**Target:** <24 hours for Green PRs (<30 index)  
**Threshold (Alert):** >48 hours average triggers process review  
**Collection Method:** GitHub API tracking + PostgreSQL
```sql
SELECT 
  AVG(EXTRACT(EPOCH FROM (approved_at - opened_at)) / 3600) as avg_hours,
  PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY approved_at - opened_at) as p95_hours
FROM pr_reviews
WHERE created_at > NOW() - INTERVAL '7 days';
```

---

### 2.4 Governance Mode Metrics

#### GM-1: Mode Stability
**Definition:** How often governance mode changes (auto-rollback frequency)  
**Measurement:** Count of mode changes per day  
**Target:** <1 mode change per day (stable mode)  
**Threshold (Alert):** >3 mode changes per day = unstable thresholds  
**Collection Method:**
```sql
SELECT COUNT(*) 
FROM governance_mode_history 
WHERE created_at > NOW() - INTERVAL '24 hours';
```

#### GM-2: Rollback Trigger Distribution
**Definition:** Which metrics trigger rollbacks most frequently  
**Measurement:** Count by trigger type (rejection_rate, latency, false_positive, complaints)  
**Target:** Balanced distribution (no single metric dominates)  
**Collection Method:**
```python
# backend/app/services/metrics/rollback_analyzer.py
@dataclass
class RollbackMetrics:
    total_rollbacks: int
    rejection_rate_triggers: int  # >5% rejection
    latency_triggers: int         # P95 >100ms
    false_positive_triggers: int  # >10% FP rate
    complaint_triggers: int       # >3% complaints
```

#### GM-3: Break Glass Frequency
**Definition:** How often emergency bypass is used  
**Measurement:** Count of break glass activations  
**Target:** <1 per month in steady state  
**Sprint 114 Expectation:** 0-2 break glass events (learning curve)  
**Collection Method:**
```sql
SELECT 
  COUNT(*) as total,
  incident_type,
  AVG(EXTRACT(EPOCH FROM (resolved_at - created_at)) / 60) as avg_duration_minutes
FROM break_glass_requests
WHERE created_at > NOW() - INTERVAL '7 days'
GROUP BY incident_type;
```

---

## 3. Data Collection Architecture

### 3.1 Metrics Pipeline

```
┌─────────────────┐
│  GitHub Events  │
│  (Webhooks)     │
└────────┬────────┘
         │
         v
┌─────────────────┐      ┌──────────────────┐
│ Metrics Ingestion│─────>│  PostgreSQL      │
│ Service          │      │  (metrics schema)│
└────────┬────────┘      └──────────────────┘
         │
         v
┌─────────────────┐      ┌──────────────────┐
│ Metrics         │─────>│  Redis Cache     │
│ Aggregator      │      │  (5-second TTL)  │
└────────┬────────┘      └──────────────────┘
         │
         v
┌─────────────────┐
│ Grafana         │
│ Dashboard       │
└─────────────────┘
```

### 3.2 Database Schema

```sql
-- Metrics aggregation table
CREATE TABLE governance_metrics_hourly (
    id SERIAL PRIMARY KEY,
    metric_hour TIMESTAMP NOT NULL,
    
    -- Developer Friction
    avg_pr_latency_impact_percent DECIMAL(5,2),
    complaint_count INTEGER DEFAULT 0,
    override_count INTEGER DEFAULT 0,
    
    -- Quality Assurance
    false_positive_rate DECIMAL(5,2),
    false_negative_rate DECIMAL(5,2),
    vibecoding_index_accuracy DECIMAL(5,3),
    
    -- Time Savings
    avg_auto_gen_time_saved_minutes DECIMAL(6,2),
    ceo_time_spent_minutes INTEGER,
    avg_pr_review_cycle_hours DECIMAL(6,2),
    
    -- Governance Mode
    mode_changes_count INTEGER DEFAULT 0,
    rollback_count INTEGER DEFAULT 0,
    break_glass_count INTEGER DEFAULT 0,
    
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(metric_hour)
);

-- Real-time metrics snapshot (updated every 5 seconds)
CREATE TABLE governance_metrics_snapshot (
    id SERIAL PRIMARY KEY,
    snapshot_at TIMESTAMP DEFAULT NOW(),
    
    -- Current thresholds
    rejection_rate_current DECIMAL(5,2),
    latency_p95_current_ms INTEGER,
    false_positive_rate_current DECIMAL(5,2),
    complaint_rate_current DECIMAL(5,2),
    
    -- Health status
    health_status VARCHAR(10), -- GREEN, YELLOW, RED
    rollback_risk_score INTEGER, -- 0-100
    
    updated_at TIMESTAMP DEFAULT NOW()
);
```

### 3.3 Metrics Service Implementation

```python
# backend/app/services/metrics/metrics_collector_service.py

from datetime import datetime, timedelta
from typing import Dict, List
from sqlalchemy import select, func
from app.db.session import AsyncSession
from app.models.metrics import GovernanceMetricsHourly, GovernanceMetricsSnapshot

class MetricsCollectorService:
    """Collects and aggregates governance metrics"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def collect_hourly_metrics(self) -> GovernanceMetricsHourly:
        """
        Aggregate metrics for the past hour
        Called by Celery beat every hour
        """
        metric_hour = datetime.now().replace(minute=0, second=0, microsecond=0)
        
        # Developer Friction
        avg_latency_impact = await self._calculate_avg_pr_latency_impact()
        complaint_count = await self._count_complaints()
        override_count = await self._count_overrides()
        
        # Quality Assurance
        fp_rate = await self._calculate_false_positive_rate()
        fn_rate = await self._calculate_false_negative_rate()
        index_accuracy = await self._calculate_index_accuracy()
        
        # Time Savings
        avg_auto_gen_saved = await self._calculate_auto_gen_time_saved()
        ceo_time_spent = await self._calculate_ceo_time_spent()
        avg_review_cycle = await self._calculate_avg_review_cycle()
        
        # Governance Mode
        mode_changes = await self._count_mode_changes()
        rollback_count = await self._count_rollbacks()
        break_glass_count = await self._count_break_glass()
        
        metrics = GovernanceMetricsHourly(
            metric_hour=metric_hour,
            avg_pr_latency_impact_percent=avg_latency_impact,
            complaint_count=complaint_count,
            override_count=override_count,
            false_positive_rate=fp_rate,
            false_negative_rate=fn_rate,
            vibecoding_index_accuracy=index_accuracy,
            avg_auto_gen_time_saved_minutes=avg_auto_gen_saved,
            ceo_time_spent_minutes=ceo_time_spent,
            avg_pr_review_cycle_hours=avg_review_cycle,
            mode_changes_count=mode_changes,
            rollback_count=rollback_count,
            break_glass_count=break_glass_count,
        )
        
        self.db.add(metrics)
        await self.db.commit()
        return metrics
    
    async def update_snapshot(self) -> GovernanceMetricsSnapshot:
        """
        Update real-time metrics snapshot
        Called every 5 seconds by background task
        """
        # Get current metrics
        rejection_rate = await self._get_current_rejection_rate()
        latency_p95 = await self._get_current_latency_p95()
        fp_rate = await self._get_current_false_positive_rate()
        complaint_rate = await self._get_current_complaint_rate()
        
        # Calculate health status
        health_status = self._determine_health_status(
            rejection_rate, latency_p95, fp_rate, complaint_rate
        )
        
        # Calculate rollback risk
        rollback_risk = self._calculate_rollback_risk(
            rejection_rate, latency_p95, fp_rate, complaint_rate
        )
        
        snapshot = GovernanceMetricsSnapshot(
            rejection_rate_current=rejection_rate,
            latency_p95_current_ms=latency_p95,
            false_positive_rate_current=fp_rate,
            complaint_rate_current=complaint_rate,
            health_status=health_status,
            rollback_risk_score=rollback_risk,
        )
        
        self.db.add(snapshot)
        await self.db.commit()
        return snapshot
    
    def _determine_health_status(
        self, rejection: float, latency: int, fp: float, complaints: float
    ) -> str:
        """
        GREEN: All metrics within target
        YELLOW: 1-2 metrics approaching threshold
        RED: Any metric exceeds threshold
        """
        red_flags = 0
        yellow_flags = 0
        
        # Check rejection rate (threshold: 5%)
        if rejection > 5.0:
            red_flags += 1
        elif rejection > 3.0:
            yellow_flags += 1
        
        # Check latency (threshold: 100ms)
        if latency > 100:
            red_flags += 1
        elif latency > 75:
            yellow_flags += 1
        
        # Check false positive rate (threshold: 10%)
        if fp > 10.0:
            red_flags += 1
        elif fp > 7.0:
            yellow_flags += 1
        
        # Check complaint rate (threshold: 3%)
        if complaints > 3.0:
            red_flags += 1
        elif complaints > 2.0:
            yellow_flags += 1
        
        if red_flags > 0:
            return "RED"
        elif yellow_flags >= 2:
            return "YELLOW"
        else:
            return "GREEN"
    
    def _calculate_rollback_risk(
        self, rejection: float, latency: int, fp: float, complaints: float
    ) -> int:
        """
        Calculate rollback risk score (0-100)
        100 = imminent rollback
        """
        risk_score = 0
        
        # Rejection rate risk (0-25 points)
        risk_score += min(25, (rejection / 5.0) * 25)
        
        # Latency risk (0-25 points)
        risk_score += min(25, (latency / 100.0) * 25)
        
        # False positive risk (0-25 points)
        risk_score += min(25, (fp / 10.0) * 25)
        
        # Complaint risk (0-25 points)
        risk_score += min(25, (complaints / 3.0) * 25)
        
        return int(risk_score)
```

---

## 4. Thresholds & Auto-Rollback Rules

### 4.1 Rollback Thresholds (WARNING Mode)

| Metric | Target | Warning | **Rollback Trigger** |
|--------|--------|---------|---------------------|
| **PR Latency Impact** | <10% | 15% | >25% |
| **Complaint Rate** | <5% | 10% | >15% |
| **False Positive Rate** | <10% | 15% | >20% |
| **Latency P95** | <50ms | 75ms | >100ms |

### 4.2 Auto-Rollback Logic

```python
# backend/app/services/governance/kill_switch_service.py

async def check_rollback_criteria(self) -> bool:
    """
    Check if any metric exceeds rollback threshold
    Returns True if rollback needed
    """
    snapshot = await self.metrics_service.get_latest_snapshot()
    
    rollback_reasons = []
    
    # Check rejection rate (not applicable in WARNING mode, but prep for SOFT)
    if snapshot.rejection_rate_current > 5.0:
        rollback_reasons.append(
            f"Rejection rate {snapshot.rejection_rate_current}% > 5% threshold"
        )
    
    # Check latency
    if snapshot.latency_p95_current_ms > 100:
        rollback_reasons.append(
            f"Latency P95 {snapshot.latency_p95_current_ms}ms > 100ms threshold"
        )
    
    # Check false positive rate
    if snapshot.false_positive_rate_current > 20.0:
        rollback_reasons.append(
            f"False positive rate {snapshot.false_positive_rate_current}% > 20% threshold"
        )
    
    # Check complaint rate
    if snapshot.complaint_rate_current > 15.0:
        rollback_reasons.append(
            f"Complaint rate {snapshot.complaint_rate_current}% > 15% threshold"
        )
    
    if rollback_reasons:
        await self.trigger_rollback(reasons=rollback_reasons)
        return True
    
    return False
```

---

## 5. Success Criteria (Sprint 114)

### 5.1 Go/No-Go Decision for Sprint 115 (Soft Enforcement)

**GO Criteria (all must pass):**
- ✅ PR latency impact <15% (average over 5 days)
- ✅ False positive rate <15%
- ✅ Complaint rate <10%
- ✅ Vibecoding Index accuracy r > 0.6
- ✅ Zero production incidents caused by governance
- ✅ CEO time tracking baseline established
- ✅ No auto-rollbacks for >48 hours (stable thresholds)

**NO-GO Criteria (any triggers delay):**
- ❌ PR latency impact >25%
- ❌ False positive rate >25%
- ❌ >5 break glass events in 5 days
- ❌ Vibecoding Index accuracy r < 0.4 (broken correlation)
- ❌ Production incident traced to governance blocking critical PR

### 5.2 Metrics Collection Targets

By end of Sprint 114 (Feb 7), collect:
- **100+ PRs** evaluated (20 PRs per day minimum)
- **50+ feedback forms** submitted (developers + CEO)
- **7 days** of hourly metrics (168 data points)
- **10+ manual CEO reviews** for index accuracy validation
- **5+ threshold tuning iterations** (adjust rollback thresholds)

---

## 6. Reporting & Dashboards

### 6.1 Daily Metrics Report

**Email sent to CEO/CTO every morning at 9 AM:**
```
Subject: Governance Metrics - Day X of Sprint 114

Key Metrics (Last 24h):
- PRs Evaluated: 23
- Avg Latency Impact: 8.2% ✅ (Target: <10%)
- False Positive Rate: 12.4% ⚠️ (Target: <10%)
- Complaint Rate: 4.1% ✅ (Target: <5%)
- CEO Time Spent: 3.2h (Baseline: 8h/day)

Health Status: YELLOW (FP rate slightly elevated)
Rollback Risk: 42/100 (Moderate)

Action Items:
- Investigate 3 false positives in backend/tests/
- Tune Vibecoding Index for test files (over-indexing)

Dashboard: https://sdlc-orchestrator.dev/governance/metrics
```

### 6.2 Grafana Dashboard Panels

**Panel 1: Rollback Risk Gauge**
- 0-30: Green (Healthy)
- 31-60: Yellow (Caution)
- 61-100: Red (High Risk)

**Panel 2: 4 Metrics Trends (24h)**
- Rejection Rate (line chart)
- Latency P95 (line chart)
- False Positive Rate (line chart)
- Complaint Rate (line chart)

**Panel 3: Time Savings Tracker**
- CEO Time: Baseline vs Actual (bar chart)
- Auto-Gen Time Saved per PR (stacked bar)

**Panel 4: Mode History Timeline**
- Mode changes with reasons
- Auto-rollback events highlighted

---

## 7. Feedback Collection

### 7.1 Developer Feedback Form

**Triggered when:**
- PR blocked by governance (SOFT/FULL mode only, not Sprint 114)
- Developer clicks "Report Issue" in UI
- PR comment contains "false positive"

**Form fields:**
```yaml
feedback_form:
  pr_number: int (auto-filled)
  issue_type:
    - False Positive (should have passed)
    - False Negative (should have been caught)
    - Too Slow (latency issue)
    - Confusing Message (error unclear)
    - Other
  description: text (required, min 20 chars)
  severity:
    - Blocking (cannot proceed)
    - Annoying (workaround exists)
    - Suggestion (nice to have)
  suggested_fix: text (optional)
  developer_email: string (auto-filled from auth)
```

### 7.2 CEO Feedback Form

**Triggered when:**
- CEO approves/rejects PR in dashboard
- CEO clicks "Governance Feedback" button

**Form fields:**
```yaml
ceo_feedback_form:
  pr_number: int (auto-filled)
  vibecoding_index_accurate: bool
    - Yes, index matches my time spent
    - No, index underestimated complexity
    - No, index overestimated complexity
  actual_time_spent_minutes: int (required)
  false_negative_found: bool
    - Yes, governance missed issues
  false_negative_description: text (conditional)
  overall_satisfaction: 1-5 stars
  comments: text (optional)
```

---

## 8. Implementation Checklist

### Backend (3 days)
- [ ] Create `GovernanceMetricsHourly` model
- [ ] Create `GovernanceMetricsSnapshot` model
- [ ] Implement `MetricsCollectorService`
- [ ] Implement `PRLatencyTracker`
- [ ] Implement `SentimentAnalyzer`
- [ ] Implement `QualityMetricsCalculator`
- [ ] Implement `TimeSavingsTracker`
- [ ] Create hourly aggregation Celery task
- [ ] Create 5-second snapshot update task
- [ ] Create auto-rollback check task (runs every 10 seconds)
- [ ] Add feedback form endpoints (POST /api/v1/feedback/developer, /api/v1/feedback/ceo)

### Frontend (2 days)
- [ ] Create Metrics Dashboard page (`/app/governance/metrics`)
- [ ] Create 4 metrics gauge components
- [ ] Create time savings tracker component
- [ ] Create mode history timeline component
- [ ] Create developer feedback form modal
- [ ] Create CEO feedback form modal
- [ ] Add real-time polling (5-second refresh for metrics)

### Grafana (1 day)
- [ ] Create Grafana dashboard JSON config
- [ ] Configure PostgreSQL data source
- [ ] Create 4 panels (rollback risk, trends, time savings, mode history)
- [ ] Configure alerts (email CTO on RED health status)

---

## 9. Risks & Mitigations

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| **Not enough PRs during Sprint 114** | Can't collect 100+ PRs for baseline | Medium | Encourage team to create small PRs, backfill with Sprint 113 data |
| **Metrics collection overhead causes latency** | Violates <100ms latency target | Low | Async collection, Redis caching, database indexing |
| **Developers ignore feedback forms** | Can't calculate complaint rate | Medium | Auto-prompt feedback form in UI, incentivize with "Your feedback improves governance" |
| **Vibecoding Index inaccurate** | CEO time savings not realized | Medium | Daily tuning sessions, collect 50+ CEO data points |
| **False positive rate too high** | Developers lose trust | High | Aggressive threshold tuning, CTO manual review of all FPs |

---

## 10. Appendix

### A. Metrics API Endpoints

```
GET  /api/v1/metrics/snapshot             # Current metrics snapshot
GET  /api/v1/metrics/hourly?hours=24      # Hourly metrics for last 24h
GET  /api/v1/metrics/pr/:pr_number        # Metrics for specific PR
POST /api/v1/feedback/developer           # Submit developer feedback
POST /api/v1/feedback/ceo                 # Submit CEO feedback
GET  /api/v1/metrics/health               # Health status (GREEN/YELLOW/RED)
GET  /api/v1/metrics/rollback-risk        # Rollback risk score (0-100)
```

### B. Database Indexes

```sql
CREATE INDEX idx_metrics_hourly_hour ON governance_metrics_hourly(metric_hour DESC);
CREATE INDEX idx_metrics_snapshot_updated ON governance_metrics_snapshot(updated_at DESC);
CREATE INDEX idx_pr_reviews_created ON pr_reviews(created_at DESC);
CREATE INDEX idx_audit_log_event_type ON governance_audit_log(event_type, created_at DESC);
```

---

**Document Status:** DRAFT  
**Next Review:** Sprint 114 Kickoff (Feb 3, 2026)  
**Approver:** CTO  
**Related Documents:**
- ADR-041 (Architecture Decision)
- SPRINT-112-116-GOVERNANCE-COMPLETION.md (Master Plan)
- Sprint-115-Enforcement-Rules-Spec.md (Next sprint)
