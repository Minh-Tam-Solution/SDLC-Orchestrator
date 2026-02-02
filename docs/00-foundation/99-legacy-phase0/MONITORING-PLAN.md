# Monitoring Plan
## Prometheus + Grafana + Kill Switch Design

**Version**: 1.0.0
**Date**: January 27, 2026
**Authority**: Phase 0 Deliverable #6 (48-hour CTO Gate Review)
**Prerequisites**: CTO Addendum 3 (Monitoring + Kill Switch)
**Phase**: PRE-PHASE 0 → PHASE 0 → WEEK 1

---

## 📋 DOCUMENT PURPOSE

**Goal**: Design comprehensive monitoring system with:
- Prometheus metrics (40+ metrics)
- 3 Grafana dashboards (CEO, Tech, Ops)
- Alert rules (SLO violations, kill switch triggers)
- Kill switch automation (<5 min rollback)

**Success Criteria**:
- >99% uptime (SLO)
- <500ms P95 latency (SLO)
- <10% false positive rate (SLO)
- Kill switch rollback <5 minutes

---

## 📊 PROMETHEUS METRICS SPECIFICATION

### Metric Categories

```yaml
1. Governance System Metrics (15 metrics)
2. Performance Metrics (10 metrics)
3. Business Metrics (CEO Dashboard - 8 metrics)
4. Developer Experience Metrics (7 metrics)
5. System Health Metrics (5 metrics)

Total: 45 metrics
```

---

### 1. Governance System Metrics

```yaml
# Submission Lifecycle
governance_submissions_total:
  type: counter
  labels: [project_id, status]
  description: "Total number of governance submissions"
  example: governance_submissions_total{project_id="proj-123", status="passed"} 150

governance_submissions_duration_seconds:
  type: histogram
  labels: [project_id]
  description: "Time from submission to validation complete"
  buckets: [0.1, 0.5, 1.0, 2.0, 5.0, 10.0]
  target_p95: 0.5  # <500ms

governance_rejections_total:
  type: counter
  labels: [project_id, rejection_reason]
  description: "Total number of rejections by reason"
  example: governance_rejections_total{project_id="proj-123", rejection_reason="missing_ownership"} 25

# Vibecoding Index
governance_vibecoding_index:
  type: histogram
  labels: [project_id, routing]
  description: "Vibecoding Index distribution"
  buckets: [0, 10, 20, 30, 40, 50, 60, 70, 80, 90, 100]
  example: governance_vibecoding_index{project_id="proj-123", routing="auto_approve"} 15.5

governance_vibecoding_index_avg:
  type: gauge
  labels: [project_id]
  description: "Average Vibecoding Index (7-day rolling)"
  target: <30

# Routing Decisions
governance_routing_total:
  type: counter
  labels: [project_id, routing]
  description: "Routing decisions by category"
  values:
    - auto_approve (Green, <30)
    - tech_lead_review (Yellow, 31-60)
    - ceo_should_review (Orange, 61-80)
    - ceo_must_review (Red, 81-100)

# Signal Breakdown
governance_signals_architectural_smell:
  type: histogram
  labels: [project_id]
  description: "Architectural smell signal (0-100)"
  buckets: [0, 20, 40, 60, 80, 100]

governance_signals_abstraction_complexity:
  type: histogram
  labels: [project_id]
  description: "Abstraction complexity signal (0-100)"
  buckets: [0, 20, 40, 60, 80, 100]

governance_signals_ai_dependency_ratio:
  type: histogram
  labels: [project_id]
  description: "AI dependency ratio signal (0-100)"
  buckets: [0, 20, 40, 60, 80, 100]

governance_signals_change_surface_area:
  type: histogram
  labels: [project_id]
  description: "Change surface area signal (0-100)"
  buckets: [0, 20, 40, 60, 80, 100]

governance_signals_drift_velocity:
  type: histogram
  labels: [project_id]
  description: "Drift velocity signal (0-100)"
  buckets: [0, 20, 40, 60, 80, 100]

# Critical Path Override
governance_critical_override_total:
  type: counter
  labels: [project_id, critical_category]
  description: "MAX CRITICALITY OVERRIDE activations"
  values:
    - security
    - payment
    - database_schema
    - infrastructure
    - secrets

# Evidence Vault
evidence_vault_uploads_total:
  type: counter
  labels: [project_id, evidence_type]
  description: "Total evidence uploads"
  example: evidence_vault_uploads_total{project_id="proj-123", evidence_type="intent_statement"} 200

evidence_vault_size_bytes:
  type: gauge
  labels: [project_id]
  description: "Total evidence storage size"

# Escalations
governance_escalations_total:
  type: counter
  labels: [project_id, escalated_to]
  description: "Total escalations to CEO/CTO"
  example: governance_escalations_total{project_id="proj-123", escalated_to="ceo"} 10

# CEO Overrides (Calibration)
governance_ceo_overrides_total:
  type: counter
  labels: [project_id, override_type]
  description: "CEO overrides (agrees vs disagrees with index)"
  values:
    - agrees (index correct)
    - disagrees (false positive)
```

---

### 2. Performance Metrics

```yaml
# API Latency
api_request_duration_seconds:
  type: histogram
  labels: [method, endpoint, status]
  description: "API request duration"
  buckets: [0.01, 0.05, 0.1, 0.2, 0.5, 1.0, 2.0, 5.0]
  target_p95: 0.1  # <100ms

# Database Query Performance
db_query_duration_seconds:
  type: histogram
  labels: [query_name, table]
  description: "Database query duration"
  buckets: [0.001, 0.01, 0.05, 0.1, 0.5, 1.0]
  target_p95: 0.1  # <100ms

# OPA Policy Evaluation
opa_evaluation_duration_seconds:
  type: histogram
  labels: [policy_name]
  description: "OPA policy evaluation duration"
  buckets: [0.01, 0.05, 0.1, 0.2, 0.5]
  target_p95: 0.15  # <150ms

# MinIO Evidence Upload
minio_upload_duration_seconds:
  type: histogram
  labels: [bucket]
  description: "MinIO evidence upload duration"
  buckets: [0.1, 0.5, 1.0, 2.0, 5.0, 10.0]
  target_p95: 2.0  # <2s for 10MB

# LLM Generation (Ollama)
llm_generation_duration_seconds:
  type: histogram
  labels: [provider, model]
  description: "LLM generation duration"
  buckets: [1.0, 3.0, 5.0, 10.0, 15.0, 30.0]
  target_p95: 10.0  # <10s

llm_generation_success_rate:
  type: gauge
  labels: [provider, model]
  description: "LLM generation success rate (0-1)"
  target: >0.9  # >90%

llm_fallback_triggered_total:
  type: counter
  labels: [provider, fallback_type]
  description: "LLM fallback activations"
  values:
    - timeout
    - error
    - low_quality

# Auto-Generation Performance
auto_generation_duration_seconds:
  type: histogram
  labels: [component]
  description: "Auto-generation component duration"
  values:
    - intent_statement (target: <10s)
    - ownership_annotation (target: <2s)
    - context_attachment (target: <5s)
    - ai_attestation (target: <3s)

# Cache Performance
cache_hit_rate:
  type: gauge
  labels: [cache_name]
  description: "Redis cache hit rate (0-1)"
  target: >0.8  # >80%

# Worker Queue
worker_queue_length:
  type: gauge
  labels: [queue_name]
  description: "Celery worker queue length"
  alert_threshold: >100
```

---

### 3. Business Metrics (CEO Dashboard)

```yaml
# CEO Time Saved
ceo_time_saved_hours:
  type: gauge
  labels: [week]
  description: "CEO time saved this week (hours)"
  baseline: 40
  target_week_2: 30
  target_week_4: 20
  target_week_8: 10

ceo_pr_review_reduction_percent:
  type: gauge
  labels: [week]
  description: "Percentage of PRs NOT requiring CEO review"
  baseline: 0
  target_week_2: 60
  target_week_4: 70
  target_week_8: 85

# Governance Autonomy
governance_without_ceo_percent:
  type: gauge
  labels: [week]
  description: "Decisions made without CEO involvement"
  target_week_4: 70
  target_week_8: 85

# Code Quality Improvement
code_quality_test_coverage_percent:
  type: gauge
  labels: [project_id]
  description: "Test coverage percentage"
  baseline: 80
  target: 90

code_quality_production_bugs_total:
  type: counter
  labels: [severity]
  description: "Production bugs (P0/P1/P2)"
  baseline_quarterly: 100
  target_quarterly: 40  # -60%

# Compliance
compliance_pass_rate_percent:
  type: gauge
  labels: [project_id]
  description: "First submission pass rate"
  target_week_2: 50
  target_week_4: 70
  target_week_8: 85

# Bypass Incidents
governance_bypass_incidents_total:
  type: counter
  labels: [bypass_type]
  description: "Bypass incidents"
  values:
    - pre_commit_skip
    - direct_push
    - break_glass_abuse
  target: 0

# False Positive Rate
governance_false_positive_rate:
  type: gauge
  labels: [week]
  description: "CEO disagrees with Red/Orange routing"
  target: <0.10  # <10%
```

---

### 4. Developer Experience Metrics

```yaml
# Developer Friction
developer_friction_minutes:
  type: histogram
  labels: [project_id]
  description: "Time from PR ready to governance passed"
  buckets: [1, 3, 5, 10, 15, 30]
  target_p95: 5  # <5 min

# Auto-Generation Usage
auto_generation_usage_rate:
  type: gauge
  labels: [component]
  description: "Auto-generation usage rate (0-1)"
  target: >0.8  # >80%

auto_generation_quality_score:
  type: histogram
  labels: [component]
  description: "LLM output quality score (0-1)"
  buckets: [0.0, 0.3, 0.5, 0.7, 0.9, 1.0]
  target: >0.7

# Developer Satisfaction
developer_satisfaction_nps:
  type: gauge
  labels: [week]
  description: "Developer NPS score (-100 to 100)"
  target: >50

# Feedback Actionability
feedback_template_usage_total:
  type: counter
  labels: [template_id]
  description: "Feedback template usage"

feedback_resolution_time_minutes:
  type: histogram
  labels: [template_id]
  description: "Time to resolve feedback"
  buckets: [1, 5, 10, 30, 60]
  target_p95: 10  # <10 min

# Break Glass Activations
governance_break_glass_total:
  type: counter
  labels: [severity]
  description: "Break glass activations"
  values:
    - P0 (justified)
    - P1 (justified)
    - abuse (unjustified)
  target: <2 per week
```

---

### 5. System Health Metrics

```yaml
# Uptime
system_uptime_seconds:
  type: gauge
  description: "System uptime in seconds"
  target: >0.99  # >99% uptime

# Error Rate
system_errors_total:
  type: counter
  labels: [error_type, severity]
  description: "System errors"
  alert_threshold: >10 per hour

# Kill Switch Status
kill_switch_status:
  type: gauge
  description: "Kill switch status (0=OFF, 1=WARNING, 2=SOFT, 3=FULL)"
  values:
    0: OFF
    1: WARNING
    2: SOFT
    3: FULL

kill_switch_triggered_total:
  type: counter
  labels: [trigger_reason]
  description: "Kill switch activations"
  values:
    - rejection_rate_high (>80%)
    - latency_high (>500ms)
    - false_positive_high (>20%)
    - developer_complaints (>5/day)

# Resource Usage
system_cpu_usage_percent:
  type: gauge
  description: "CPU usage percentage"
  alert_threshold: >80

system_memory_usage_percent:
  type: gauge
  description: "Memory usage percentage"
  alert_threshold: >85
```

---

## 📈 GRAFANA DASHBOARD DESIGNS

### Dashboard 1: CEO Dashboard

**URL**: `/app/governance/ceo-dashboard`
**Refresh**: Real-time (WebSocket)
**Target Audience**: CEO, CTO, CPO

#### Panels

```yaml
Row 1: Executive Summary (Full Width)
  Panel 1.1: CEO Time Saved This Week (Gauge)
    Query: ceo_time_saved_hours
    Display: Single Stat Gauge (0-40h scale)
    Color Coding:
      green: <15h (exceeds target)
      yellow: 15-25h (on track)
      red: >25h (below target)
    Target Line: Week-specific target (30h, 20h, 10h)

  Panel 1.2: PRs Auto-Approved (Donut Chart)
    Query: governance_routing_total by routing
    Display: Donut chart with 4 segments
    Segments:
      Green: Auto-approved (<30 index)
      Yellow: Tech Lead review (31-60)
      Orange: CEO should review (61-80)
      Red: CEO must review (81-100)

  Panel 1.3: Pending Your Decision (Number)
    Query: count(governance_submissions{routing="ceo_must_review", status="pending"})
    Display: Single Stat
    Color Coding:
      green: 0-2
      yellow: 3-5
      red: >5
    Click Action: Navigate to PR queue

Row 2: This Week Summary (4 Columns)
  Panel 2.1: Compliance Pass Rate (%)
    Query: compliance_pass_rate_percent
    Display: Progress Bar (0-100%)
    Target Line: Week-specific (50%, 70%, 85%)

  Panel 2.2: Vibecoding Index Average
    Query: governance_vibecoding_index_avg
    Display: Gauge (0-100 scale)
    Color Coding:
      green: 0-30
      yellow: 31-60
      orange: 61-80
      red: 81-100
    Target Line: <30

  Panel 2.3: False Positive Rate (%)
    Query: governance_false_positive_rate
    Display: Single Stat
    Color Coding:
      green: <5%
      yellow: 5-10%
      red: >10%
    Target: <10%

  Panel 2.4: Developer Satisfaction (NPS)
    Query: developer_satisfaction_nps
    Display: Single Stat (-100 to 100)
    Color Coding:
      green: >50
      yellow: 0-50
      red: <0
    Target: >50

Row 3: Weekly Trends (Full Width)
  Panel 3.1: CEO Time Saved Trend (Line Chart)
    Query: ceo_time_saved_hours over 8 weeks
    Display: Time Series Line
    Baseline Line: 40h
    Target Lines: Week 2 (30h), Week 4 (20h), Week 8 (10h)
    Color: Purple

  Panel 3.2: Vibecoding Index Distribution (Heatmap)
    Query: governance_vibecoding_index histogram over 7 days
    Display: Heatmap (day x index bucket)
    Color Scale: Green (low) → Red (high)

Row 4: Top Issues Requiring Attention (Full Width)
  Panel 4.1: Top 5 Rejection Reasons (Bar Chart)
    Query: governance_rejections_total by rejection_reason
    Display: Horizontal Bar Chart
    Order: Descending by count
    Click Action: Show details for rejection type

  Panel 4.2: CEO Overrides This Week (Table)
    Query: governance_ceo_overrides_total
    Display: Table with columns:
      - PR Number
      - Vibecoding Index
      - Override Type (agrees/disagrees)
      - Reason
    Sortable: Yes

Row 5: System Health (Quick Glance)
  Panel 5.1: System Uptime (%)
    Query: system_uptime_seconds / total_seconds * 100
    Display: Single Stat
    Target: >99%

  Panel 5.2: API Latency P95 (ms)
    Query: api_request_duration_seconds_p95
    Display: Single Stat
    Target: <100ms

  Panel 5.3: Kill Switch Status
    Query: kill_switch_status
    Display: Status Indicator
    Values:
      0: 🟢 OFF
      1: 🟡 WARNING
      2: 🟠 SOFT
      3: 🔴 FULL
```

---

### Dashboard 2: Tech Dashboard

**URL**: `/app/governance/tech-dashboard`
**Refresh**: Every 5 minutes
**Target Audience**: Tech Lead, Backend Lead, DevOps

#### Panels

```yaml
Row 1: Developer Experience (Full Width)
  Panel 1.1: Developer Friction (Histogram)
    Query: developer_friction_minutes histogram
    Display: Histogram (0-30 min)
    Target Line: 5 min (P95)
    Alert Threshold: 10 min (red line)

  Panel 1.2: First Pass Rate Trend (Line Chart)
    Query: compliance_pass_rate_percent over 8 weeks
    Display: Time Series Line
    Target Lines: Week 2 (50%), Week 4 (70%), Week 8 (85%)

  Panel 1.3: Auto-Generation Usage (Donut Chart)
    Query: auto_generation_usage_rate by component
    Display: Donut chart with 4 segments:
      - Intent Statement
      - Ownership Annotation
      - Context Attachment
      - AI Attestation
    Target: >80% for all

Row 2: Vibecoding Index Breakdown (Full Width)
  Panel 2.1: Signal Scores Distribution (Stacked Bar)
    Query: All 5 signals by week
    Display: Stacked Bar Chart
    Signals:
      - Architectural Smell (25% weight)
      - Abstraction Complexity (15%)
      - AI Dependency Ratio (20%)
      - Change Surface Area (20%)
      - Drift Velocity (20%)

  Panel 2.2: Vibecoding Index by Routing (Line Chart)
    Query: governance_vibecoding_index by routing over time
    Display: Multi-line chart (4 lines)
    Lines:
      - Green (auto-approve)
      - Yellow (tech lead)
      - Orange (ceo should)
      - Red (ceo must)

Row 3: System Performance (Full Width)
  Panel 3.1: API Latency by Endpoint (Table)
    Query: api_request_duration_seconds by endpoint
    Display: Table with columns:
      - Endpoint
      - P50 (ms)
      - P95 (ms)
      - P99 (ms)
      - Count
    Sort: By P95 descending
    Alert: P95 >100ms highlighted red

  Panel 3.2: Database Query Performance (Table)
    Query: db_query_duration_seconds by query_name
    Display: Table with columns:
      - Query Name
      - Table
      - P50 (ms)
      - P95 (ms)
      - Count
    Target: P95 <100ms

Row 4: Top Violations & Calibration (Full Width)
  Panel 4.1: Top 10 Governance Violations (Bar Chart)
    Query: governance_rejections_total by rejection_reason
    Display: Horizontal Bar Chart
    Time Range: This week
    Order: Descending

  Panel 4.2: CEO Overrides for Calibration (Table)
    Query: governance_ceo_overrides_total this week
    Display: Table with columns:
      - PR Number
      - Index Before
      - CEO Decision
      - Signal Breakdown
      - Recommended Weight Adjustment
    Click Action: View full PR details

Row 5: LLM & Auto-Generation Health
  Panel 5.1: LLM Success Rate (Gauge)
    Query: llm_generation_success_rate
    Display: Multi-Gauge (one per provider)
    Providers:
      - Ollama qwen3:32b
      - Claude Sonnet
      - GPT-4o (fallback)
      - Rule-based (fallback)
    Target: >90%
    Alert: <70% (red)

  Panel 5.2: LLM Latency by Provider (Line Chart)
    Query: llm_generation_duration_seconds by provider
    Display: Multi-line time series
    Target Lines:
      - Ollama: <10s (P95)
      - Claude: <25s (P95)
    Alert: >30s (red)

  Panel 5.3: Fallback Trigger Rate (%)
    Query: llm_fallback_triggered_total / llm_generation_total
    Display: Single Stat
    Target: <10%
    Alert: >30% (critical)
```

---

### Dashboard 3: Ops Dashboard

**URL**: `/app/governance/ops-dashboard`
**Refresh**: Real-time (Prometheus)
**Target Audience**: DevOps, On-Call Engineers

#### Panels

```yaml
Row 1: System Health Overview (Full Width)
  Panel 1.1: Uptime (%)
    Query: system_uptime_seconds / total_seconds * 100
    Display: Single Stat
    SLO: >99%
    Alert: <99% (page on-call)

  Panel 1.2: API Latency P95 (ms)
    Query: api_request_duration_seconds_p95
    Display: Gauge (0-1000ms)
    SLO: <100ms
    Alert: >500ms for 5 min (page on-call)

  Panel 1.3: Error Rate (errors/min)
    Query: rate(system_errors_total[1m])
    Display: Single Stat
    Alert Threshold: >10 errors/min

  Panel 1.4: Kill Switch Status
    Query: kill_switch_status
    Display: Status Indicator
    Values:
      0: 🟢 OFF
      1: 🟡 WARNING (log violations)
      2: 🟠 SOFT (block critical)
      3: 🔴 FULL (block all)
    Alert: Any change (notify CTO + CEO)

Row 2: Performance Metrics (Full Width)
  Panel 2.1: API Request Rate (req/s)
    Query: rate(api_requests_total[1m])
    Display: Time Series Line
    Time Range: Last 24h

  Panel 2.2: API Latency Percentiles (Line Chart)
    Query: api_request_duration_seconds P50/P95/P99
    Display: Multi-line chart (3 lines)
    SLO Lines:
      - P95: 100ms (yellow)
      - P99: 500ms (red)

  Panel 2.3: Database Connection Pool (Gauge)
    Query: db_connection_pool_usage
    Display: Gauge (0-100% usage)
    Alert: >80% (add more connections)

Row 3: Component Health (Full Width)
  Panel 3.1: OPA Evaluation Latency (ms)
    Query: opa_evaluation_duration_seconds_p95
    Display: Single Stat
    Target: <150ms
    Alert: >300ms

  Panel 3.2: MinIO Upload Latency (ms)
    Query: minio_upload_duration_seconds_p95
    Display: Single Stat
    Target: <2s (for 10MB)
    Alert: >5s

  Panel 3.3: Redis Cache Hit Rate (%)
    Query: cache_hit_rate
    Display: Gauge (0-100%)
    Target: >80%
    Alert: <50% (investigate)

  Panel 3.4: Worker Queue Length
    Query: worker_queue_length
    Display: Single Stat
    Alert: >100 (add workers)

Row 4: Resource Usage (Full Width)
  Panel 4.1: CPU Usage (%)
    Query: system_cpu_usage_percent
    Display: Time Series Line (last 6h)
    Alert: >80% for 10 min

  Panel 4.2: Memory Usage (%)
    Query: system_memory_usage_percent
    Display: Time Series Line (last 6h)
    Alert: >85% for 10 min

  Panel 4.3: Disk Usage (%)
    Query: system_disk_usage_percent
    Display: Gauge (0-100%)
    Alert: >90% (out of space soon)

  Panel 4.4: Network I/O (MB/s)
    Query: rate(system_network_bytes_total[1m])
    Display: Time Series Line

Row 5: Kill Switch Monitoring (Full Width)
  Panel 5.1: Rejection Rate (%)
    Query: governance_rejections_total / governance_submissions_total * 100
    Display: Gauge (0-100%)
    Kill Switch Threshold: >80%
    Color Coding:
      green: <50%
      yellow: 50-80%
      red: >80% (TRIGGER KILL SWITCH)

  Panel 5.2: False Positive Rate (%)
    Query: governance_false_positive_rate
    Display: Gauge (0-100%)
    Kill Switch Threshold: >20%

  Panel 5.3: Developer Complaints (count/day)
    Query: count(feedback_negative_total)
    Display: Single Stat
    Kill Switch Threshold: >5/day

  Panel 5.4: Kill Switch Trigger History (Table)
    Query: kill_switch_triggered_total
    Display: Table with columns:
      - Timestamp
      - Trigger Reason
      - Rollback Duration
      - Root Cause
      - Fix Applied
```

---

## 🚨 ALERT RULES (SLO Violations)

### Critical Alerts (Page On-Call)

```yaml
# SLO Violation: Uptime <99%
alert: SystemUptimeLow
expr: (system_uptime_seconds / total_seconds) < 0.99
for: 5m
severity: critical
labels:
  team: devops
annotations:
  summary: "System uptime below 99% SLO"
  description: "Uptime: {{ $value }}% (SLO: >99%)"
  runbook: "https://docs.sdlc.dev/runbooks/uptime-low"
  action: "Page on-call engineer immediately"

# SLO Violation: API Latency >500ms (P95)
alert: APILatencyHigh
expr: histogram_quantile(0.95, api_request_duration_seconds) > 0.5
for: 5m
severity: critical
labels:
  team: backend
annotations:
  summary: "API latency P95 > 500ms"
  description: "P95 latency: {{ $value }}ms (SLO: <100ms)"
  runbook: "https://docs.sdlc.dev/runbooks/api-latency-high"
  action: "Page backend lead immediately"

# SLO Violation: False Positive Rate >20%
alert: FalsePositiveRateHigh
expr: governance_false_positive_rate > 0.20
for: 30m
severity: critical
labels:
  team: governance
annotations:
  summary: "False positive rate > 20% - Kill switch trigger imminent"
  description: "False positive rate: {{ $value }}% (SLO: <10%)"
  runbook: "https://docs.sdlc.dev/runbooks/kill-switch"
  action: "Alert CEO + CTO immediately, investigate calibration"
```

### Warning Alerts (Slack Notification)

```yaml
# Developer Friction >10 min
alert: DeveloperFrictionHigh
expr: histogram_quantile(0.95, developer_friction_minutes) > 10
for: 1h
severity: warning
labels:
  team: governance
annotations:
  summary: "Developer friction >10 min (target: <5 min)"
  description: "P95 friction: {{ $value }} min"
  runbook: "https://docs.sdlc.dev/runbooks/developer-friction"
  action: "Investigate auto-generation latency"

# LLM Success Rate <70%
alert: LLMSuccessRateLow
expr: llm_generation_success_rate < 0.70
for: 30m
severity: warning
labels:
  team: ai
annotations:
  summary: "LLM success rate < 70% (target: >90%)"
  description: "Success rate: {{ $value }}% for {{ $labels.provider }}"
  runbook: "https://docs.sdlc.dev/runbooks/llm-failure"
  action: "Check Ollama service, verify fallback working"

# Vibecoding Index Average >60
alert: VibecodingIndexHigh
expr: governance_vibecoding_index_avg > 60
for: 1d
severity: warning
labels:
  team: governance
annotations:
  summary: "Vibecoding Index average >60 (target: <30)"
  description: "7-day average: {{ $value }}"
  runbook: "https://docs.sdlc.dev/runbooks/vibecoding-high"
  action: "Review rejected PRs, recalibrate signal weights"
```

### Info Alerts (Log Only)

```yaml
# First Pass Rate <50%
alert: FirstPassRateLow
expr: compliance_pass_rate_percent < 50
for: 1d
severity: info
labels:
  team: governance
annotations:
  summary: "First pass rate <50% (target: 70%)"
  description: "Pass rate: {{ $value }}%"
  action: "Review feedback actionability, improve templates"

# CEO Override Rate High
alert: CEOOverrideRateHigh
expr: rate(governance_ceo_overrides_total{override_type="disagrees"}[1d]) > 0.10
for: 1d
severity: info
labels:
  team: governance
annotations:
  summary: "CEO disagrees with >10% of index decisions"
  description: "Override rate: {{ $value }}%"
  action: "Schedule recalibration session"
```

---

## 🔴 KILL SWITCH AUTOMATION

### Kill Switch Criteria (from Success-Criteria-v2.yaml)

```yaml
kill_switch_triggers:
  rejection_rate_high:
    condition: rejection_rate > 0.80
    duration: 1h
    action: "Rollback to WARNING mode"
    reason: "Too many rejects = system too strict"

  latency_p95_high:
    condition: api_latency_p95 > 500ms
    duration: 5m
    action: "Rollback to WARNING mode"
    reason: "Too slow = developer friction"

  false_positive_rate_high:
    condition: false_positive_rate > 0.20
    duration: 30m
    action: "Rollback to WARNING mode"
    reason: "Too many mistakes = CEO loses trust"

  developer_complaints_high:
    condition: feedback_negative_total > 5 per day
    duration: 1d
    action: "Rollback to WARNING mode"
    reason: "Team unhappy = product adoption fails"
```

### Kill Switch Implementation

```python
# backend/app/services/governance/kill_switch.py

import logging
from datetime import datetime, timedelta
from typing import Dict, List

logger = logging.getLogger(__name__)

class GovernanceKillSwitch:
    """
    Automated kill switch for governance system.

    Monitors 4 criteria and triggers rollback if thresholds exceeded.

    SLO: Rollback within 5 minutes of trigger.
    """

    def __init__(self, metrics_service, notification_service):
        self.metrics = metrics_service
        self.notifications = notification_service

    async def check_kill_switch_criteria(self) -> Dict[str, bool]:
        """
        Check all 4 kill switch criteria.

        Returns:
            dict: {criterion_name: triggered (bool)}
        """
        criteria_status = {}

        # Criterion 1: Rejection Rate >80%
        rejection_rate = await self._get_rejection_rate(window="1h")
        if rejection_rate > 0.80:
            logger.critical(f"Kill switch trigger: rejection_rate={rejection_rate:.2%} (threshold: 80%)")
            criteria_status["rejection_rate_high"] = True
        else:
            criteria_status["rejection_rate_high"] = False

        # Criterion 2: Latency P95 >500ms
        latency_p95 = await self._get_api_latency_p95(window="5m")
        if latency_p95 > 500:  # milliseconds
            logger.critical(f"Kill switch trigger: latency_p95={latency_p95}ms (threshold: 500ms)")
            criteria_status["latency_high"] = True
        else:
            criteria_status["latency_high"] = False

        # Criterion 3: False Positive Rate >20%
        false_positive_rate = await self._get_false_positive_rate(window="30m")
        if false_positive_rate > 0.20:
            logger.critical(f"Kill switch trigger: false_positive_rate={false_positive_rate:.2%} (threshold: 20%)")
            criteria_status["false_positive_high"] = True
        else:
            criteria_status["false_positive_high"] = False

        # Criterion 4: Developer Complaints >5/day
        complaints_today = await self._get_developer_complaints(window="1d")
        if complaints_today > 5:
            logger.critical(f"Kill switch trigger: complaints={complaints_today} (threshold: 5/day)")
            criteria_status["developer_complaints_high"] = True
        else:
            criteria_status["developer_complaints_high"] = False

        return criteria_status

    async def trigger_kill_switch(self, reason: str) -> None:
        """
        Trigger kill switch rollback.

        Steps:
          1. Set governance mode to WARNING
          2. Notify CEO + CTO + Tech Leads
          3. Log incident to audit trail
          4. Schedule emergency review meeting

        SLO: Complete within 5 minutes.
        """
        logger.critical(f"KILL SWITCH ACTIVATED: {reason}")

        # Step 1: Rollback to WARNING mode
        from backend.app.config.governance_flags import GOVERNANCE_MODE
        previous_mode = GOVERNANCE_MODE.get()

        await GOVERNANCE_MODE.set("WARNING")

        logger.info("Governance mode rolled back: FULL → WARNING")

        # Step 2: Notify stakeholders
        await self.notifications.send_critical_alert(
            to=["CEO", "CTO", "All Tech Leads"],
            subject=f"🚨 KILL SWITCH ACTIVATED: {reason}",
            body=f"""
GOVERNANCE KILL SWITCH TRIGGERED

Reason: {reason}
Previous Mode: {previous_mode}
Current Mode: WARNING (governance violations logged, not blocking)

Triggered At: {datetime.utcnow().isoformat()}

IMMEDIATE ACTIONS REQUIRED:
1. CEO + CTO + Tech Lead meeting within 2 hours
2. Root cause analysis within 24 hours
3. Fix implementation plan within 48 hours
4. Re-dogfood cycle (2 weeks) before re-enabling

Rollback completed in <5 minutes (SLO met).

Dashboard: https://sdlc.dev/app/governance/ops-dashboard
Runbook: https://docs.sdlc.dev/runbooks/kill-switch
            """,
            priority="CRITICAL",
            channels=["slack", "email", "sms"]
        )

        # Step 3: Log to audit trail
        await self.metrics.log_audit_event(
            action="kill_switch_triggered",
            reason=reason,
            previous_mode=previous_mode,
            current_mode="WARNING",
            timestamp=datetime.utcnow()
        )

        # Step 4: Increment Prometheus counter
        await self.metrics.increment(
            "kill_switch_triggered_total",
            labels={"trigger_reason": reason}
        )

    async def _get_rejection_rate(self, window: str) -> float:
        """Calculate rejection rate over time window."""
        rejections = await self.metrics.query(
            f"sum(rate(governance_rejections_total[{window}]))"
        )
        submissions = await self.metrics.query(
            f"sum(rate(governance_submissions_total[{window}]))"
        )

        if submissions == 0:
            return 0.0

        return rejections / submissions

    async def _get_api_latency_p95(self, window: str) -> float:
        """Get API latency P95 over time window (in milliseconds)."""
        latency_seconds = await self.metrics.query(
            f"histogram_quantile(0.95, api_request_duration_seconds[{window}])"
        )
        return latency_seconds * 1000  # Convert to milliseconds

    async def _get_false_positive_rate(self, window: str) -> float:
        """Calculate false positive rate over time window."""
        false_positives = await self.metrics.query(
            f"sum(rate(governance_ceo_overrides_total{{override_type='disagrees'}}[{window}]))"
        )
        total_escalations = await self.metrics.query(
            f"sum(rate(governance_escalations_total[{window}]))"
        )

        if total_escalations == 0:
            return 0.0

        return false_positives / total_escalations

    async def _get_developer_complaints(self, window: str) -> int:
        """Get developer complaints count over time window."""
        complaints = await self.metrics.query(
            f"sum(increase(feedback_negative_total[{window}]))"
        )
        return int(complaints)
```

### Kill Switch Testing

```yaml
Test Scenarios:
  1. Manual Trigger Test:
     - Action: Manually set rejection_rate = 85%
     - Expected: Kill switch triggers within 1 hour
     - Verify: Mode changes to WARNING, notifications sent

  2. Latency Spike Test:
     - Action: Introduce artificial 600ms latency
     - Expected: Kill switch triggers within 5 minutes
     - Verify: Rollback completes <5 min (SLO)

  3. False Positive Test:
     - Action: CEO disagrees with 25% of Red PRs
     - Expected: Kill switch triggers within 30 minutes
     - Verify: Calibration alert sent to CEO

  4. Developer Complaint Test:
     - Action: 6 developers submit negative feedback in 1 day
     - Expected: Kill switch triggers at end of day
     - Verify: UX investigation task created

Test Frequency: Weekly (automated)
Test Owner: DevOps Lead
```

---

## ✅ VALIDATION CHECKLIST

**Before Week 1 execution:**

- [ ] All 45 Prometheus metrics implemented
- [ ] 3 Grafana dashboards deployed (CEO, Tech, Ops)
- [ ] Alert rules configured in Prometheus
- [ ] Kill switch automation tested (<5 min rollback)
- [ ] Notifications working (Slack, Email, SMS)
- [ ] Runbooks documented for all alerts
- [ ] SLO commitments validated (>99% uptime, <500ms P95, <10% false positive)

**CTO Gate Review Criteria:**

- [ ] CEO Dashboard has real-time CEO time saved metric
- [ ] Tech Dashboard shows Vibecoding Index breakdown
- [ ] Ops Dashboard has kill switch monitoring
- [ ] Alert rules trigger correctly (tested in staging)
- [ ] Kill switch rollback completes <5 min (SLO met)
- [ ] All metrics exportable for weekly reports

---

**Document Status**: ✅ **COMPLETE**
**Phase 0 Completion**: 6/6 documents complete (100%)
**Next**: CTO Gate Review (Hour 48) → Decision: Proceed to Week 1 OR iterate
