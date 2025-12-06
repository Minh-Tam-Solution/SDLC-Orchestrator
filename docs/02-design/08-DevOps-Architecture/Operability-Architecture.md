# Operability Architecture

**Version**: v1.0
**Date**: November 13, 2025
**Owner**: SRE Lead, DevOps Lead
**Stage**: Stage 02 (HOW - Design & Architecture)
**Framework**: SDLC 4.9
**Status**: ✅ APPROVED

---

## 1. Overview

This document defines the **operability architecture** for SDLC Orchestrator, including:
- **SLI/SLO Definitions** (99.9% availability, <100ms latency)
- **Monitoring Architecture** (Prometheus, Grafana, Alertmanager)
- **Golden Signals** (latency, traffic, errors, saturation)
- **Alert Definitions** (critical, warning, info)
- **Runbook Templates** (incident response procedures)
- **Incident Management** (severity levels, escalation, RCA)

**Objective**: Ensure production readiness with observable, maintainable, and reliable operations.

**Related Documents**:
- [Performance-Budget.md](../10-Performance-Architecture/Performance-Budget.md)
- [Security-Baseline.md](../07-Security-RBAC/Security-Baseline.md)
- [Database-Architecture.md](../03-Database-Design/Database-Architecture.md)

---

## 2. SLI/SLO Definitions

### 2.1 Service Level Indicators (SLIs)

**Definition**: Quantitative measures of service behavior (what we measure).

| SLI | Measurement | Query | Target |
|-----|-------------|-------|--------|
| **Availability** | Successful requests / Total requests | `sum(rate(http_requests_total{status!~"5.."}[5m])) / sum(rate(http_requests_total[5m]))` | 99.9% |
| **Latency (p95)** | 95th percentile response time | `histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))` | <100ms |
| **Latency (p99)** | 99th percentile response time | `histogram_quantile(0.99, rate(http_request_duration_seconds_bucket[5m]))` | <200ms |
| **Error Rate** | Failed requests / Total requests | `sum(rate(http_requests_total{status=~"5.."}[5m])) / sum(rate(http_requests_total[5m]))` | <0.1% |
| **Throughput** | Requests per minute | `sum(rate(http_requests_total[1m])) * 60` | >1000 rpm |

---

### 2.2 Service Level Objectives (SLOs)

**Definition**: Target values for SLIs (what we promise).

#### **SLO 1: Availability - 99.9% (Three Nines)**

```yaml
SLO: API Availability
Target: 99.9% over 30-day rolling window
Error Budget: 0.1% (43.2 minutes/month)

Measurement:
  SLI: (successful_requests / total_requests) * 100
  Window: 30 days rolling
  Exclusions: Scheduled maintenance (announced 72h prior)

Consequences:
  - 99.9% = 43.2 min downtime/month allowed
  - 99.95% = 21.6 min downtime/month (stretch goal)
  - <99.9% = Incident review, engineering focus

Prometheus Query:
  sum(rate(http_requests_total{status!~"5..", job="api"}[30d]))
  /
  sum(rate(http_requests_total{job="api"}[30d]))
  * 100
```

---

#### **SLO 2: Latency - p95 < 100ms**

```yaml
SLO: API Latency (p95)
Target: 95% of requests < 100ms
Window: 5-minute intervals

Measurement:
  SLI: p95 response time
  Endpoints: All REST endpoints (excluding uploads)
  Exclusions: Evidence upload endpoints (100MB files)

Consequences:
  - p95 > 100ms for 5 min = Warning alert
  - p95 > 200ms for 5 min = Critical alert
  - p95 > 500ms for 1 min = Page on-call

Prometheus Query:
  histogram_quantile(0.95,
    sum(rate(http_request_duration_seconds_bucket{job="api"}[5m]))
    by (le, endpoint)
  ) < 0.1
```

---

#### **SLO 3: Error Rate - < 0.1%**

```yaml
SLO: Error Rate
Target: <0.1% errors (99.9% success rate)
Window: 5-minute intervals

Measurement:
  SLI: HTTP 5xx errors / Total requests
  Exclusions: Client errors (4xx), rate limiting (429)

Consequences:
  - Error rate > 0.1% for 5 min = Warning alert
  - Error rate > 1% for 1 min = Critical alert
  - Error rate > 5% for 30 sec = Page on-call

Prometheus Query:
  sum(rate(http_requests_total{status=~"5..", job="api"}[5m]))
  /
  sum(rate(http_requests_total{job="api"}[5m]))
  * 100
```

---

### 2.3 Error Budget Policy

```yaml
Error Budget: 0.1% (43.2 minutes/month)

Budget Consumption:
  0-25% consumed: Normal operations
  25-50% consumed: Review recent incidents
  50-75% consumed: Slow down feature releases
  75-100% consumed: Feature freeze, focus on reliability
  >100% consumed: All hands on reliability

Budget Reset: Monthly (1st day of month)

Example Calculation:
  Month: November 2025
  Total minutes: 43,200 (30 days)
  Error budget: 43.2 minutes

  Incident 1 (Nov 5): 5 min outage = 11.6% budget
  Incident 2 (Nov 15): 10 min degradation = 23.1% budget
  Total consumed: 34.7% of budget
  Remaining: 28.2 minutes (65.3%)
```

---

## 3. Monitoring Architecture

### 3.1 Monitoring Stack

```yaml
Components:
  Metrics:
    - Prometheus: Time-series database (metrics storage)
    - Prometheus Exporters: Node, PostgreSQL, Redis, Custom
    - Pushgateway: Batch job metrics

  Visualization:
    - Grafana: Dashboards, graphs, alerts
    - Grafana Loki: Log aggregation
    - Grafana Tempo: Distributed tracing

  Alerting:
    - Alertmanager: Alert routing, grouping, silencing
    - PagerDuty: On-call management
    - Slack: Team notifications

  APM:
    - Sentry: Error tracking, performance monitoring
    - OpenTelemetry: Distributed tracing
```

---

### 3.2 Metrics Collection Architecture

```mermaid
graph TB
    subgraph "Applications"
        API[API Servers<br/>FastAPI]
        WORKER[Background Workers<br/>Celery]
        DB[(PostgreSQL)]
        REDIS[(Redis)]
    end

    subgraph "Exporters"
        APP_EXP[App Metrics<br/>Custom Exporter]
        NODE_EXP[Node Exporter<br/>System Metrics]
        PG_EXP[Postgres Exporter<br/>DB Metrics]
        REDIS_EXP[Redis Exporter<br/>Cache Metrics]
    end

    subgraph "Prometheus"
        PROM[Prometheus Server<br/>TSDB]
        PUSH[Pushgateway<br/>Batch Metrics]
    end

    subgraph "Visualization"
        GRAFANA[Grafana<br/>Dashboards]
        ALERT[Alertmanager<br/>Alert Routing]
    end

    subgraph "Notifications"
        PD[PagerDuty<br/>On-Call]
        SLACK[Slack<br/>Team Chat]
        EMAIL[Email<br/>Reports]
    end

    API --> APP_EXP
    WORKER --> PUSH
    DB --> PG_EXP
    REDIS --> REDIS_EXP
    API --> NODE_EXP

    APP_EXP --> PROM
    NODE_EXP --> PROM
    PG_EXP --> PROM
    REDIS_EXP --> PROM
    PUSH --> PROM

    PROM --> GRAFANA
    PROM --> ALERT

    ALERT --> PD
    ALERT --> SLACK
    ALERT --> EMAIL

    GRAFANA --> SLACK
```

---

### 3.3 Custom Metrics (Application-Specific)

```python
# metrics.py - Custom Prometheus metrics
from prometheus_client import Counter, Histogram, Gauge, Summary

# Request metrics
http_requests_total = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status']
)

http_request_duration_seconds = Histogram(
    'http_request_duration_seconds',
    'HTTP request latency',
    ['method', 'endpoint'],
    buckets=[0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0]
)

# Business metrics
gate_approvals_total = Counter(
    'gate_approvals_total',
    'Total gate approvals',
    ['gate_id', 'status', 'project_id']
)

evidence_uploads_total = Counter(
    'evidence_uploads_total',
    'Total evidence uploads',
    ['type', 'project_id']
)

active_projects = Gauge(
    'active_projects',
    'Number of active projects',
    ['organization_id', 'status']
)

# Database metrics
db_connection_pool_size = Gauge(
    'db_connection_pool_size',
    'Database connection pool size',
    ['pool_name']
)

db_query_duration_seconds = Histogram(
    'db_query_duration_seconds',
    'Database query duration',
    ['query_type', 'table'],
    buckets=[0.001, 0.005, 0.01, 0.05, 0.1, 0.5, 1.0]
)

# Cache metrics
cache_hits_total = Counter(
    'cache_hits_total',
    'Cache hits',
    ['cache_type']
)

cache_misses_total = Counter(
    'cache_misses_total',
    'Cache misses',
    ['cache_type']
)
```

---

## 4. Golden Signals

### 4.1 Latency

**Definition**: Time to serve a request.

```yaml
Metrics:
  - http_request_duration_seconds (Histogram)
  - db_query_duration_seconds (Histogram)
  - cache_response_time_seconds (Histogram)

Key Percentiles:
  - p50 (median): Typical user experience
  - p95: Most users experience
  - p99: Worst case (excluding outliers)

Dashboard Panels:
  - API Latency by Endpoint (heatmap)
  - Database Query Time (p95)
  - Cache Response Time (p99)
  - Latency SLO Compliance (burn rate)

Alert Thresholds:
  - WARNING: p95 > 100ms for 5 min
  - CRITICAL: p95 > 200ms for 5 min
  - PAGE: p95 > 500ms for 1 min
```

---

### 4.2 Traffic

**Definition**: Demand on the system.

```yaml
Metrics:
  - http_requests_total (Counter)
  - active_users (Gauge)
  - throughput_rpm (requests per minute)

Dashboard Panels:
  - Request Rate (req/sec)
  - Active Users (real-time)
  - Top Endpoints by Traffic
  - Traffic Patterns (daily, weekly)

Alert Thresholds:
  - INFO: Traffic spike >2x normal
  - WARNING: Traffic >80% capacity
  - CRITICAL: Traffic >95% capacity
```

---

### 4.3 Errors

**Definition**: Rate of failed requests.

```yaml
Metrics:
  - http_requests_total{status="5xx"} (Counter)
  - error_rate_percent (Calculated)
  - failed_gate_evaluations_total (Counter)

Dashboard Panels:
  - Error Rate (% of requests)
  - Errors by Type (500, 502, 503, 504)
  - Top Error Endpoints
  - Error Budget Burn Rate

Alert Thresholds:
  - WARNING: Error rate > 0.1% for 5 min
  - CRITICAL: Error rate > 1% for 1 min
  - PAGE: Error rate > 5% for 30 sec
```

---

### 4.4 Saturation

**Definition**: How full the service is.

```yaml
Metrics:
  - cpu_usage_percent (Gauge)
  - memory_usage_percent (Gauge)
  - db_connection_pool_usage (Gauge)
  - disk_usage_percent (Gauge)

Dashboard Panels:
  - CPU Usage by Service
  - Memory Usage Trend
  - Database Connection Pool
  - Disk I/O Utilization

Alert Thresholds:
  - WARNING: CPU > 70% for 10 min
  - CRITICAL: CPU > 85% for 5 min
  - WARNING: Memory > 80%
  - CRITICAL: Connection pool > 90%
```

---

## 5. Alert Definitions

### 5.1 Alert Severity Levels

| Severity | Response Time | Notification | Examples |
|----------|---------------|--------------|----------|
| **PAGE (P1)** | <5 minutes | PagerDuty → Phone call | Service down, data loss risk |
| **CRITICAL (P2)** | <30 minutes | PagerDuty → SMS | SLO violation, degraded service |
| **WARNING (P3)** | <2 hours | Slack → #alerts | Approaching threshold |
| **INFO (P4)** | Next business day | Email | Deployment, scheduled maintenance |

---

### 5.2 Critical Alerts

```yaml
Alert: APIDown
Severity: PAGE
Condition: up{job="api"} == 0
Duration: 1 minute
Summary: API is down
Runbook: runbooks/api-down.md

---

Alert: HighErrorRate
Severity: CRITICAL
Condition: |
  sum(rate(http_requests_total{status=~"5.."}[5m]))
  /
  sum(rate(http_requests_total[5m]))
  > 0.01
Duration: 1 minute
Summary: Error rate > 1%
Runbook: runbooks/high-error-rate.md

---

Alert: HighLatency
Severity: CRITICAL
Condition: |
  histogram_quantile(0.95,
    rate(http_request_duration_seconds_bucket[5m])
  ) > 0.2
Duration: 5 minutes
Summary: p95 latency > 200ms
Runbook: runbooks/high-latency.md

---

Alert: DatabaseDown
Severity: PAGE
Condition: pg_up == 0
Duration: 1 minute
Summary: PostgreSQL is down
Runbook: runbooks/database-down.md

---

Alert: DiskFull
Severity: CRITICAL
Condition: disk_usage_percent > 90
Duration: 5 minutes
Summary: Disk usage > 90%
Runbook: runbooks/disk-full.md
```

---

### 5.3 Warning Alerts

```yaml
Alert: HighCPU
Severity: WARNING
Condition: cpu_usage_percent > 70
Duration: 10 minutes
Summary: CPU usage > 70%

---

Alert: HighMemory
Severity: WARNING
Condition: memory_usage_percent > 80
Duration: 5 minutes
Summary: Memory usage > 80%

---

Alert: ConnectionPoolExhaustion
Severity: WARNING
Condition: db_connection_pool_usage > 0.8
Duration: 5 minutes
Summary: DB connection pool > 80%

---

Alert: CacheHitRateLow
Severity: WARNING
Condition: |
  sum(rate(cache_hits_total[5m]))
  /
  (sum(rate(cache_hits_total[5m])) + sum(rate(cache_misses_total[5m])))
  < 0.8
Duration: 10 minutes
Summary: Cache hit rate < 80%

---

Alert: SLOBudgetBurn
Severity: WARNING
Condition: error_budget_consumed_percent > 50
Duration: 1 hour
Summary: Error budget > 50% consumed
```

---

## 6. Runbook Templates

### 6.1 Runbook: API Latency Spike

```markdown
# Runbook: API Latency Spike

## Alert
**Name**: HighLatency
**Condition**: p95 latency > 200ms for 5 minutes
**Severity**: CRITICAL

## Symptoms
- Dashboard shows p95 latency spike
- Users report slow response times
- Possible timeout errors

## Initial Response (5 min)

1. **Verify the alert**
   ```bash
   curl -w "@curl-format.txt" https://api.sdlc-orchestrator.com/health
   ```

2. **Check Grafana dashboard**
   - [API Latency Dashboard](https://grafana.sdlc-orchestrator.com/d/api-latency)
   - Identify affected endpoints

3. **Check recent deployments**
   ```bash
   kubectl rollout history deployment/api
   ```

## Investigation (10 min)

1. **Database performance**
   ```sql
   -- Check slow queries
   SELECT query, mean_exec_time, calls
   FROM pg_stat_statements
   WHERE mean_exec_time > 100
   ORDER BY mean_exec_time DESC
   LIMIT 10;
   ```

2. **Connection pool status**
   ```bash
   kubectl exec -it pgbouncer-0 -- psql -c "SHOW POOLS;"
   ```

3. **Cache hit ratio**
   ```bash
   redis-cli INFO stats | grep hit
   ```

4. **CPU/Memory usage**
   ```bash
   kubectl top pods -n production
   ```

## Mitigation (15 min)

### Option 1: Scale horizontally
```bash
kubectl scale deployment/api --replicas=5
```

### Option 2: Increase cache TTL
```python
# Temporary increase cache TTL
CACHE_TTL = 600  # 10 minutes
```

### Option 3: Enable read replica
```bash
# Route read queries to replica
export DATABASE_URL_READ=postgresql://replica.rds.amazonaws.com/db
kubectl rollout restart deployment/api
```

### Option 4: Rollback deployment
```bash
kubectl rollout undo deployment/api
```

## Escalation
- 15 min: Page Backend Lead
- 30 min: Page Tech Lead
- 60 min: Page CTO

## Post-Incident
1. Create incident report
2. Update runbook with findings
3. Add monitoring for root cause
4. Schedule RCA meeting
```

---

### 6.2 Runbook: Database Connection Pool Exhaustion

```markdown
# Runbook: Database Connection Pool Exhaustion

## Alert
**Name**: ConnectionPoolExhaustion
**Condition**: Connection pool usage > 90%
**Severity**: CRITICAL

## Symptoms
- "Connection pool exhausted" errors
- API requests timing out
- Database appears healthy but unreachable

## Initial Response (5 min)

1. **Check pool status**
   ```bash
   kubectl exec -it pgbouncer-0 -- psql -c "SHOW POOLS;"
   kubectl exec -it pgbouncer-0 -- psql -c "SHOW CLIENTS;"
   kubectl exec -it pgbouncer-0 -- psql -c "SHOW SERVERS;"
   ```

2. **Identify connection leaks**
   ```sql
   SELECT pid, usename, application_name, state,
          state_change, query_start
   FROM pg_stat_activity
   WHERE state = 'idle in transaction'
   AND state_change < NOW() - INTERVAL '10 minutes';
   ```

## Investigation (10 min)

1. **Long-running queries**
   ```sql
   SELECT pid, now() - query_start AS duration, query
   FROM pg_stat_activity
   WHERE state != 'idle'
   AND query_start < NOW() - INTERVAL '1 minute'
   ORDER BY duration DESC;
   ```

2. **Kill stuck connections**
   ```sql
   -- Terminate idle transactions > 10 min
   SELECT pg_terminate_backend(pid)
   FROM pg_stat_activity
   WHERE state = 'idle in transaction'
   AND state_change < NOW() - INTERVAL '10 minutes';
   ```

3. **Check for deployment issues**
   ```bash
   kubectl logs deployment/api --tail=100 | grep -i "connection"
   ```

## Mitigation (15 min)

### Option 1: Increase pool size (temporary)
```bash
kubectl exec -it pgbouncer-0 -- psql -c "SET default_pool_size = 50;"
kubectl exec -it pgbouncer-0 -- psql -c "RELOAD;"
```

### Option 2: Restart PgBouncer
```bash
kubectl rollout restart statefulset/pgbouncer
```

### Option 3: Scale down API servers
```bash
# Reduce connection demand
kubectl scale deployment/api --replicas=2
```

### Option 4: Enable statement timeout
```sql
ALTER DATABASE sdlc_orchestrator SET statement_timeout = '30s';
```

## Prevention
1. Implement connection pool monitoring
2. Add connection leak detection
3. Set aggressive timeouts
4. Use connection pooling in app

## Escalation
- 10 min: Page Database Admin
- 20 min: Page Backend Lead
- 30 min: Page Tech Lead
```

---

### 6.3 Runbook: Evidence Upload Failure

```markdown
# Runbook: Evidence Upload Failure

## Alert
**Name**: EvidenceUploadFailure
**Condition**: Evidence upload success rate < 95%
**Severity**: WARNING → CRITICAL

## Symptoms
- Users report upload failures
- "413 Payload Too Large" errors
- MinIO/S3 connection errors
- Timeout during processing

## Initial Response (5 min)

1. **Check MinIO/S3 health**
   ```bash
   aws s3 ls s3://sdlc-evidence/ --summarize
   mc admin info minio/
   ```

2. **Check error logs**
   ```bash
   kubectl logs deployment/api --tail=100 | grep -i "evidence\|upload\|minio\|s3"
   ```

3. **Verify presigned URL generation**
   ```bash
   curl -X POST https://api.sdlc-orchestrator.com/evidence/upload-url \
     -H "Authorization: Bearer $TOKEN" \
     -d '{"filename": "test.pdf"}'
   ```

## Investigation (10 min)

1. **Storage capacity**
   ```bash
   aws s3api get-bucket-location --bucket sdlc-evidence
   aws cloudwatch get-metric-statistics \
     --namespace AWS/S3 \
     --metric-name BucketSizeBytes \
     --dimensions Name=BucketName,Value=sdlc-evidence \
     --start-time 2024-01-01T00:00:00Z \
     --end-time 2024-01-02T00:00:00Z \
     --period 86400 \
     --statistics Average
   ```

2. **Network connectivity**
   ```bash
   kubectl exec -it deployment/api -- nslookup s3.amazonaws.com
   kubectl exec -it deployment/api -- curl -I https://s3.amazonaws.com
   ```

3. **Background worker status**
   ```bash
   kubectl logs deployment/celery-worker --tail=50
   kubectl exec -it deployment/celery-worker -- celery -A app inspect active
   ```

## Mitigation (15 min)

### Option 1: Increase upload timeout
```python
# Temporary increase timeout
UPLOAD_TIMEOUT = 300  # 5 minutes
```

### Option 2: Restart workers
```bash
kubectl rollout restart deployment/celery-worker
```

### Option 3: Clear failed jobs
```bash
kubectl exec -it redis-0 -- redis-cli
> DEL celery:evidence:failed
> FLUSHDB  # Nuclear option
```

### Option 4: Switch to backup storage
```bash
# Use backup S3 bucket
export S3_BUCKET=sdlc-evidence-backup
kubectl rollout restart deployment/api
```

## Prevention
1. Implement chunked uploads
2. Add retry logic with exponential backoff
3. Monitor S3 bucket metrics
4. Set up S3 lifecycle policies

## Escalation
- 15 min: Page DevOps Lead
- 30 min: Page Tech Lead
```

---

## 7. Incident Management

### 7.1 Severity Levels

| Severity | Impact | Response Time | Approvers | Examples |
|----------|--------|---------------|-----------|----------|
| **SEV-1** | Service down, data loss risk | <5 min | CTO, CEO | Complete outage, security breach |
| **SEV-2** | Major degradation, SLO breach | <30 min | Tech Lead, EM | API errors >5%, latency >500ms |
| **SEV-3** | Minor degradation, partial impact | <2 hours | Team Lead | Single feature broken |
| **SEV-4** | Minimal impact, cosmetic | Next day | Engineer | UI glitch, typo |

---

### 7.2 Incident Response Process

```mermaid
graph TB
    START[Alert Triggered] --> TRIAGE[Triage]
    TRIAGE --> SEV{Severity?}

    SEV -->|SEV-1| PAGE1[Page On-Call<br/>+ CTO + CEO]
    SEV -->|SEV-2| PAGE2[Page On-Call<br/>+ Tech Lead]
    SEV -->|SEV-3| NOTIFY[Notify Team<br/>via Slack]
    SEV -->|SEV-4| TICKET[Create Ticket]

    PAGE1 --> WAR[War Room<br/>Zoom Bridge]
    PAGE2 --> WAR
    NOTIFY --> INVESTIGATE[Investigate]

    WAR --> MITIGATE[Mitigate]
    INVESTIGATE --> MITIGATE

    MITIGATE --> FIX{Fixed?}
    FIX -->|No| ESCALATE[Escalate]
    FIX -->|Yes| VERIFY[Verify Fix]

    ESCALATE --> MITIGATE

    VERIFY --> MONITOR[Monitor 30 min]
    MONITOR --> STABLE{Stable?}

    STABLE -->|No| MITIGATE
    STABLE -->|Yes| CLOSE[Close Incident]

    CLOSE --> RCA[Schedule RCA]
    RCA --> POSTMORTEM[Write Postmortem]
    POSTMORTEM --> ACTIONS[Action Items]
    ACTIONS --> END[End]

    TICKET --> END
```

---

### 7.3 On-Call Schedule

```yaml
Rotation:
  Schedule: Weekly (Mon-Sun)
  Handoff: Monday 9 AM
  Team Size: 4 engineers

Primary On-Call:
  Response Time: <5 minutes
  Responsibilities:
    - First responder to pages
    - Triage and initial investigation
    - Coordinate incident response
    - Handoff to secondary if needed

Secondary On-Call:
  Response Time: <15 minutes
  Responsibilities:
    - Backup for primary
    - Subject matter expert
    - Assist with major incidents

Compensation:
  - On-call pay: $500/week (primary), $250/week (secondary)
  - Comp time: 1 day off after SEV-1 incident
  - No on-call during PTO
```

---

### 7.4 Root Cause Analysis (RCA) Template

```markdown
# Incident Postmortem: [INCIDENT-ID]

## Incident Summary
- **Date**: November 13, 2025
- **Duration**: 15 minutes (10:30 AM - 10:45 AM PST)
- **Severity**: SEV-2
- **Impact**: 10% of API requests failed, 100 users affected
- **Root Cause**: Database connection pool exhaustion

## Timeline
- **10:30 AM**: First alert (connection pool >90%)
- **10:32 AM**: On-call paged
- **10:35 AM**: Root cause identified
- **10:40 AM**: Mitigation applied (pool size increased)
- **10:45 AM**: Service restored
- **11:15 AM**: Monitoring period ended

## Root Cause (5 Whys)
1. Why did requests fail?
   - Connection pool was exhausted

2. Why was the pool exhausted?
   - Long-running queries held connections

3. Why were queries long-running?
   - Missing index on large table

4. Why was the index missing?
   - Not included in recent migration

5. Why wasn't it caught?
   - No query performance tests

## What Went Well
- ✅ Alert fired quickly
- ✅ On-call responded promptly
- ✅ Runbook was helpful
- ✅ Mitigation was effective

## What Went Poorly
- ❌ Missing index not caught in review
- ❌ No query performance testing
- ❌ Pool size too small for load

## Action Items
| Action | Owner | Due Date | Status |
|--------|-------|----------|--------|
| Add missing index | @backend-lead | Nov 15 | TODO |
| Increase default pool size | @devops | Nov 14 | TODO |
| Add query performance tests | @qa-lead | Nov 20 | TODO |
| Update connection pool monitoring | @sre-lead | Nov 16 | TODO |

## Lessons Learned
1. Always test query performance with production-like data
2. Connection pool size should be load-tested
3. Database migrations need performance review

## Prevention
- Implement query performance regression tests
- Add index advisor to CI/CD pipeline
- Monthly database performance review
```

---

## 8. Observability Tools Configuration

### 8.1 Prometheus Configuration

```yaml
# prometheus.yml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

alerting:
  alertmanagers:
    - static_configs:
        - targets: ['alertmanager:9093']

rule_files:
  - "alerts/*.yml"

scrape_configs:
  - job_name: 'api'
    metrics_path: /metrics
    static_configs:
      - targets: ['api:8000']

  - job_name: 'postgres'
    static_configs:
      - targets: ['postgres-exporter:9187']

  - job_name: 'redis'
    static_configs:
      - targets: ['redis-exporter:9121']

  - job_name: 'node'
    static_configs:
      - targets: ['node-exporter:9100']

remote_write:
  - url: "https://prometheus-us-central1.grafana.net/api/prom/push"
    basic_auth:
      username: "123456"
      password: "api_key"
```

---

### 8.2 Alertmanager Configuration

```yaml
# alertmanager.yml
global:
  resolve_timeout: 5m
  pagerduty_url: 'https://events.pagerduty.com/v2/enqueue'
  slack_api_url: 'https://hooks.slack.com/services/T00000000/B00000000/XXXXXXXXXXXXXXXXXXXXXXXX'

route:
  group_by: ['alertname', 'severity']
  group_wait: 10s
  group_interval: 10s
  repeat_interval: 1h
  receiver: 'default'

  routes:
    - match:
        severity: page
      receiver: pagerduty
      continue: true

    - match:
        severity: critical
      receiver: pagerduty
      continue: true

    - match:
        severity: warning
      receiver: slack

    - match:
        severity: info
      receiver: email

receivers:
  - name: 'default'
    webhook_configs:
      - url: 'http://localhost:5001/'

  - name: 'pagerduty'
    pagerduty_configs:
      - service_key: 'YOUR_PD_SERVICE_KEY'
        description: '{{ .GroupLabels.alertname }}'
        details:
          firing: '{{ .Alerts.Firing | len }}'
          resolved: '{{ .Alerts.Resolved | len }}'

  - name: 'slack'
    slack_configs:
      - channel: '#alerts'
        title: '{{ .GroupLabels.alertname }}'
        text: '{{ range .Alerts }}{{ .Annotations.summary }}\n{{ end }}'

  - name: 'email'
    email_configs:
      - to: 'ops-team@sdlc-orchestrator.com'
        from: 'alerts@sdlc-orchestrator.com'
        smarthost: 'smtp.gmail.com:587'
        auth_username: 'alerts@sdlc-orchestrator.com'
        auth_password: 'password'

inhibit_rules:
  - source_match:
      severity: 'critical'
    target_match:
      severity: 'warning'
    equal: ['alertname', 'instance']
```

---

### 8.3 Grafana Dashboard JSON (Example Panel)

```json
{
  "dashboard": {
    "title": "SDLC Orchestrator - API Performance",
    "panels": [
      {
        "id": 1,
        "title": "Request Rate",
        "type": "graph",
        "targets": [
          {
            "expr": "sum(rate(http_requests_total[5m])) by (endpoint)",
            "legendFormat": "{{ endpoint }}"
          }
        ]
      },
      {
        "id": 2,
        "title": "Latency (p95)",
        "type": "graph",
        "targets": [
          {
            "expr": "histogram_quantile(0.95, sum(rate(http_request_duration_seconds_bucket[5m])) by (le, endpoint))",
            "legendFormat": "{{ endpoint }}"
          }
        ]
      },
      {
        "id": 3,
        "title": "Error Rate",
        "type": "graph",
        "targets": [
          {
            "expr": "sum(rate(http_requests_total{status=~\"5..\"}[5m])) / sum(rate(http_requests_total[5m])) * 100",
            "legendFormat": "Error %"
          }
        ]
      },
      {
        "id": 4,
        "title": "SLO Compliance",
        "type": "stat",
        "targets": [
          {
            "expr": "(1 - (sum(rate(http_requests_total{status=~\"5..\"}[30d])) / sum(rate(http_requests_total[30d])))) * 100",
            "legendFormat": "Availability"
          }
        ],
        "thresholds": {
          "mode": "absolute",
          "steps": [
            {"color": "red", "value": null},
            {"color": "yellow", "value": 99.9},
            {"color": "green", "value": 99.95}
          ]
        }
      }
    ]
  }
}
```

---

## 9. References

- [Google SRE Book](https://sre.google/sre-book/) - Site Reliability Engineering
- [The Site Reliability Workbook](https://sre.google/workbook/) - Practical SRE
- [Prometheus Best Practices](https://prometheus.io/docs/practices/)
- [Grafana Best Practices](https://grafana.com/docs/grafana/latest/best-practices/)
- [PagerDuty Incident Response](https://response.pagerduty.com/)

---

## 10. Approval

| Role | Name | Approval | Date |
|------|------|----------|------|
| **SRE Lead** | [SRE Lead Name] | ✅ APPROVED | Nov 13, 2025 |
| **DevOps Lead** | [DevOps Lead Name] | ✅ APPROVED | Nov 13, 2025 |
| **Tech Lead** | [Tech Lead Name] | ✅ APPROVED | Nov 13, 2025 |

---

**Last Updated**: November 13, 2025
**Status**: ✅ ACCEPTED - Operability architecture complete
**Next Review**: After MVP deployment (Week 12)
**Gate G2 Evidence**: `operate_preview: present`