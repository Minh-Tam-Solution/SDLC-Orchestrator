# Monitoring & Alert Thresholds
## SDLC Orchestrator - Production Alerting Configuration

**Version**: 1.0.0
**Date**: December 13, 2025
**Owner**: DevOps Lead
**Reviewer**: CTO
**Environment**: Production (Beta Pilot)
**Framework**: SDLC 5.1.3
**CTO Mandate**: p95<100ms, error rate<1%, resource<70% warning

---

## 🎯 Overview

### Monitoring Stack

```yaml
Metrics Collection: Prometheus (port 9091, Bflow instance)
Visualization: Grafana (port 3001, Bflow instance)
Alerting: Prometheus Alertmanager + Slack integration
On-Call: PagerDuty (optional, Slack primary)
Log Aggregation: ELK Stack (optional, Week 3)

SDLC Services Monitored:
  - Backend API (FastAPI): 192.168.0.223:8300
  - PostgreSQL: 192.168.0.223:5450
  - Redis: 192.168.0.223:6395
  - MinIO: 192.168.0.223:9010
  - OPA: 192.168.0.223:8185
```

### Alert Severity Levels

| Level | Response Time | Notification | Escalation |
|-------|---------------|--------------|------------|
| **P0 - Critical** | <30 min | Page on-call + Slack | CTO if not resolved in 30 min |
| **P1 - High** | <2 hours | Slack notification | Tech Lead if not resolved in 2 hours |
| **P2 - Medium** | <1 day | Slack notification | None |
| **P3 - Low** | <3 days | Slack notification | None |

---

## 📊 Alert Threshold Definitions

### 1. API Performance Alerts (CTO Priority)

#### P1-001: API Latency Warning

```yaml
Alert Name: SDLC_API_Latency_Warning
Severity: P1 (High)
Condition: API p95 latency > 100ms for 15 minutes
Threshold: 100ms (target: <100ms p95)
Evaluation Interval: 1 minute
Notification: Slack #sdlc-team
Runbook: /docs/06-Operations-Maintenance/02-Runbooks/HIGH-LATENCY-RUNBOOK.md

PromQL Query:
  histogram_quantile(0.95,
    sum(rate(http_request_duration_seconds_bucket{job="sdlc-backend"}[5m])) by (le)
  ) > 0.1

Expected Baseline: ~80ms p95 (Sprint 31 result)
Action:
  1. Check database query performance (slow queries)
  2. Check Redis cache hit rate (target: >70%)
  3. Check system resources (CPU, memory, disk I/O)
  4. Review recent code changes (last deploy)
  5. Notify Backend Lead if persists >30 min
```

#### P0-001: API Latency Critical

```yaml
Alert Name: SDLC_API_Latency_Critical
Severity: P0 (Critical)
Condition: API p95 latency > 150ms for 5 minutes
Threshold: 150ms (1.5x target)
Evaluation Interval: 1 minute
Notification: Page on-call + Slack #sdlc-team
Runbook: /docs/06-Operations-Maintenance/02-Runbooks/CRITICAL-LATENCY-RUNBOOK.md

PromQL Query:
  histogram_quantile(0.95,
    sum(rate(http_request_duration_seconds_bucket{job="sdlc-backend"}[5m])) by (le)
  ) > 0.15

Action:
  1. Page on-call engineer immediately
  2. Check if incident warrants rollback (p95 >200ms = rollback trigger)
  3. Execute emergency diagnostics (CPU, DB, network)
  4. Escalate to CTO if not resolved in 30 min
```

---

### 2. Error Rate Alerts

#### P1-002: Error Rate Warning

```yaml
Alert Name: SDLC_Error_Rate_Warning
Severity: P1 (High)
Condition: HTTP 5xx error rate > 1% for 10 minutes
Threshold: 1% (baseline: <0.1% in Sprint 31)
Evaluation Interval: 1 minute
Notification: Slack #sdlc-team

PromQL Query:
  (
    sum(rate(http_requests_total{job="sdlc-backend", status=~"5.."}[5m]))
    /
    sum(rate(http_requests_total{job="sdlc-backend"}[5m]))
  ) > 0.01

Action:
  1. Check backend logs for error patterns
  2. Check database connection pool (exhausted?)
  3. Check external dependencies (OPA, MinIO)
  4. Review recent deployments (rollback if needed)
  5. Notify Backend Lead
```

#### P0-002: Error Rate Critical

```yaml
Alert Name: SDLC_Error_Rate_Critical
Severity: P0 (Critical)
Condition: HTTP 5xx error rate > 5% for 5 minutes
Threshold: 5% (unacceptable failure rate)
Evaluation Interval: 1 minute
Notification: Page on-call + Slack #sdlc-team

PromQL Query:
  (
    sum(rate(http_requests_total{job="sdlc-backend", status=~"5.."}[5m]))
    /
    sum(rate(http_requests_total{job="sdlc-backend"}[5m]))
  ) > 0.05

Action:
  1. Page on-call engineer immediately
  2. Consider immediate rollback (if post-deployment <1 hour)
  3. Check for cascading failures (DB, Redis, OPA, MinIO)
  4. Escalate to CTO immediately
```

---

### 3. Resource Usage Alerts

#### P2-001: CPU Usage Warning

```yaml
Alert Name: SDLC_CPU_Usage_Warning
Severity: P2 (Medium)
Condition: CPU usage > 70% for 15 minutes
Threshold: 70% (comfortable headroom: <70%)
Evaluation Interval: 1 minute
Notification: Slack #sdlc-team

PromQL Query:
  (1 - avg(rate(node_cpu_seconds_total{mode="idle", instance="192.168.0.223:9100"}[5m]))) * 100 > 70

Action:
  1. Identify CPU-intensive processes (top, htop)
  2. Check for runaway processes (memory leaks)
  3. Review application profiling (py-spy for backend)
  4. Consider horizontal scaling if sustained
```

#### P0-003: CPU Usage Critical

```yaml
Alert Name: SDLC_CPU_Usage_Critical
Severity: P0 (Critical)
Condition: CPU usage > 90% for 5 minutes
Threshold: 90% (imminent service degradation)
Evaluation Interval: 1 minute
Notification: Page on-call + Slack #sdlc-team

PromQL Query:
  (1 - avg(rate(node_cpu_seconds_total{mode="idle", instance="192.168.0.223:9100"}[5m]))) * 100 > 90

Action:
  1. Page on-call engineer immediately
  2. Identify and kill runaway processes (if safe)
  3. Scale resources (add CPU cores if VM)
  4. Consider rolling back recent deployment
  5. Escalate to CTO if not resolved in 30 min
```

#### P2-002: Memory Usage Warning

```yaml
Alert Name: SDLC_Memory_Usage_Warning
Severity: P2 (Medium)
Condition: Memory usage > 70% for 15 minutes
Threshold: 70% (comfortable headroom)
Evaluation Interval: 1 minute
Notification: Slack #sdlc-team

PromQL Query:
  (1 - (node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes)) * 100 > 70

Action:
  1. Check Docker container memory usage (docker stats)
  2. Identify memory-intensive containers
  3. Check for memory leaks (backend, OPA)
  4. Review cache sizes (Redis maxmemory)
```

#### P0-004: Memory Usage Critical

```yaml
Alert Name: SDLC_Memory_Usage_Critical
Severity: P0 (Critical)
Condition: Memory usage > 90% for 5 minutes
Threshold: 90% (risk of OOM killer)
Evaluation Interval: 1 minute
Notification: Page on-call + Slack #sdlc-team

PromQL Query:
  (1 - (node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes)) * 100 > 90

Action:
  1. Page on-call engineer immediately
  2. Identify OOM risk (check dmesg for OOM killer)
  3. Restart high-memory containers if safe
  4. Scale memory resources urgently
  5. Escalate to CTO
```

#### P2-003: Disk Usage Warning

```yaml
Alert Name: SDLC_Disk_Usage_Warning
Severity: P2 (Medium)
Condition: Disk usage > 80% for 30 minutes
Threshold: 80% (comfortable headroom)
Evaluation Interval: 5 minutes
Notification: Slack #sdlc-team

PromQL Query:
  (node_filesystem_size_bytes{mountpoint="/"} - node_filesystem_avail_bytes{mountpoint="/"})
  / node_filesystem_size_bytes{mountpoint="/"} * 100 > 80

Action:
  1. Identify large files/directories (du -sh /*)
  2. Clean Docker images/volumes (docker system prune)
  3. Archive old logs (rotate, compress)
  4. Clean MinIO evidence vault if >100GB (retention policy)
```

#### P0-005: Disk Usage Critical

```yaml
Alert Name: SDLC_Disk_Usage_Critical
Severity: P0 (Critical)
Condition: Disk usage > 90% for 10 minutes
Threshold: 90% (imminent disk full)
Evaluation Interval: 1 minute
Notification: Page on-call + Slack #sdlc-team

PromQL Query:
  (node_filesystem_size_bytes{mountpoint="/"} - node_filesystem_avail_bytes{mountpoint="/"})
  / node_filesystem_size_bytes{mountpoint="/"} * 100 > 90

Action:
  1. Page on-call engineer immediately
  2. Emergency cleanup (delete temp files, old Docker images)
  3. Stop non-critical services if needed
  4. Expand disk urgently (if VM)
  5. Escalate to CTO + IT Team
```

---

### 4. Service Health Alerts

#### P0-006: Backend Service Down

```yaml
Alert Name: SDLC_Backend_Down
Severity: P0 (Critical)
Condition: Backend API unhealthy for 1 minute
Threshold: Health check fails (HTTP != 200 /health)
Evaluation Interval: 30 seconds
Notification: Page on-call + Slack #sdlc-team

PromQL Query:
  up{job="sdlc-backend"} == 0

Action:
  1. Page on-call engineer immediately
  2. Check container status (docker ps -a)
  3. Check logs (docker logs sdlc-backend-prod --tail 100)
  4. Restart container if safe (docker restart sdlc-backend-prod)
  5. Execute rollback if restart fails
  6. Escalate to CTO immediately
```

#### P0-007: Database Service Down

```yaml
Alert Name: SDLC_Database_Down
Severity: P0 (Critical)
Condition: PostgreSQL unhealthy for 1 minute
Threshold: Health check fails (cannot connect)
Evaluation Interval: 30 seconds
Notification: Page on-call + Slack #sdlc-team

PromQL Query:
  up{job="sdlc-postgres"} == 0

Action:
  1. Page on-call engineer immediately
  2. Check PostgreSQL container (docker ps -a | grep postgres)
  3. Check PostgreSQL logs (docker logs sdlc-postgres-prod --tail 100)
  4. Restart PostgreSQL if safe (data integrity check first!)
  5. Restore from backup if corrupted
  6. Escalate to CTO + IT Team immediately
```

#### P0-008: Redis Service Down

```yaml
Alert Name: SDLC_Redis_Down
Severity: P0 (Critical)
Condition: Redis unhealthy for 1 minute
Threshold: Health check fails (cannot ping)
Evaluation Interval: 30 seconds
Notification: Page on-call + Slack #sdlc-team

PromQL Query:
  up{job="sdlc-redis"} == 0

Action:
  1. Page on-call engineer immediately
  2. Check Redis container (docker ps -a | grep redis)
  3. Check Redis logs (docker logs sdlc-redis-prod --tail 100)
  4. Restart Redis if safe (data loss acceptable for cache)
  5. Verify backend auto-reconnects to Redis
  6. Escalate if backend also fails
```

---

### 5. Database-Specific Alerts

#### P1-003: Slow Database Queries

```yaml
Alert Name: SDLC_Slow_Database_Queries
Severity: P1 (High)
Condition: Query p95 latency > 50ms for 10 minutes
Threshold: 50ms (target: <10ms for simple queries)
Evaluation Interval: 1 minute
Notification: Slack #sdlc-team

PromQL Query:
  histogram_quantile(0.95,
    sum(rate(pg_stat_statements_total_time_bucket[5m])) by (le)
  ) > 0.05

Action:
  1. Identify slow queries (pg_stat_statements)
  2. Check missing indexes (EXPLAIN ANALYZE)
  3. Check table bloat (VACUUM needed?)
  4. Review recent schema changes
  5. Notify Backend Lead
```

#### P0-009: Database Connection Pool Exhausted

```yaml
Alert Name: SDLC_DB_Connection_Pool_Exhausted
Severity: P0 (Critical)
Condition: Active connections > 90% of max for 5 minutes
Threshold: 90% of max_connections (default: 100)
Evaluation Interval: 1 minute
Notification: Page on-call + Slack #sdlc-team

PromQL Query:
  (sum(pg_stat_activity_count) / max(pg_settings_max_connections)) * 100 > 90

Action:
  1. Page on-call engineer immediately
  2. Check for connection leaks (backend not closing connections)
  3. Kill idle/long-running connections (pg_terminate_backend)
  4. Increase max_connections if legitimate load
  5. Restart backend if connection leak confirmed
  6. Escalate to CTO
```

---

### 6. Redis-Specific Alerts

#### P2-004: Redis Cache Hit Rate Low

```yaml
Alert Name: SDLC_Redis_Cache_Hit_Low
Severity: P2 (Medium)
Condition: Cache hit rate < 50% for 15 minutes
Threshold: 50% (target: >70% from Sprint 31)
Evaluation Interval: 1 minute
Notification: Slack #sdlc-team

PromQL Query:
  (redis_keyspace_hits_total / (redis_keyspace_hits_total + redis_keyspace_misses_total)) * 100 < 50

Action:
  1. Review cache keys (are we caching the right data?)
  2. Check TTL configuration (too short?)
  3. Increase Redis maxmemory if evicting too often
  4. Review application caching strategy
  5. Notify Backend Lead
```

#### P1-004: Redis Memory Usage High

```yaml
Alert Name: SDLC_Redis_Memory_High
Severity: P1 (High)
Condition: Redis memory usage > 80% of maxmemory for 10 minutes
Threshold: 80% (maxmemory: 2GB default)
Evaluation Interval: 1 minute
Notification: Slack #sdlc-team

PromQL Query:
  (redis_memory_used_bytes / redis_memory_max_bytes) * 100 > 80

Action:
  1. Check eviction policy (allkeys-lru configured?)
  2. Review large keys (redis-cli --bigkeys)
  3. Consider increasing maxmemory (4GB?)
  4. Check for memory leaks in Redis
  5. Notify DevOps Lead
```

---

### 7. Application-Specific Alerts

#### P1-005: High Gate Evaluation Failures

```yaml
Alert Name: SDLC_Gate_Evaluation_Failures
Severity: P1 (High)
Condition: Gate evaluation failure rate > 10% for 15 minutes
Threshold: 10% (baseline: <5% expected failures)
Evaluation Interval: 1 minute
Notification: Slack #sdlc-team

PromQL Query:
  (
    sum(rate(gate_evaluations_total{result="failure"}[5m]))
    /
    sum(rate(gate_evaluations_total[5m]))
  ) * 100 > 10

Action:
  1. Check OPA service health (is OPA responding?)
  2. Review policy syntax (recent policy changes?)
  3. Check evidence availability (MinIO accessible?)
  4. Review gate evaluation logs (backend)
  5. Notify Backend Lead + PM
```

#### P2-005: Evidence Upload Failures

```yaml
Alert Name: SDLC_Evidence_Upload_Failures
Severity: P2 (Medium)
Condition: Evidence upload failure rate > 5% for 15 minutes
Threshold: 5% (baseline: <1% expected failures)
Evaluation Interval: 1 minute
Notification: Slack #sdlc-team

PromQL Query:
  (
    sum(rate(evidence_uploads_total{status="failure"}[5m]))
    /
    sum(rate(evidence_uploads_total[5m]))
  ) * 100 > 5

Action:
  1. Check MinIO service health (docker ps | grep minio)
  2. Check MinIO disk space (is bucket full?)
  3. Check network connectivity (backend → MinIO)
  4. Review file size limits (10MB max enforced?)
  5. Notify Backend Lead
```

---

## 🔔 Slack Integration Setup

### Prometheus Alertmanager Configuration

```yaml
# /home/nqh/shared/Bflow-Platform/infrastructure/monitoring/alertmanager/alertmanager.yml

global:
  slack_api_url: '<SLACK_WEBHOOK_URL>'

route:
  group_by: ['alertname', 'severity']
  group_wait: 10s
  group_interval: 10s
  repeat_interval: 12h
  receiver: 'sdlc-team'
  routes:
    - match:
        severity: P0
      receiver: 'sdlc-oncall'
      repeat_interval: 5m
    - match:
        severity: P1
      receiver: 'sdlc-team'
      repeat_interval: 1h

receivers:
  - name: 'sdlc-team'
    slack_configs:
      - channel: '#sdlc-team'
        title: '[{{ .Status }}] SDLC Orchestrator Alert'
        text: |
          *Alert:* {{ .CommonLabels.alertname }}
          *Severity:* {{ .CommonLabels.severity }}
          *Description:* {{ .CommonAnnotations.description }}
          *Runbook:* {{ .CommonAnnotations.runbook }}

  - name: 'sdlc-oncall'
    slack_configs:
      - channel: '#sdlc-oncall'
        title: '🚨 [{{ .Status }}] CRITICAL: SDLC Orchestrator'
        text: |
          *CRITICAL ALERT*
          *Alert:* {{ .CommonLabels.alertname }}
          *Severity:* P0 (Critical)
          *Description:* {{ .CommonAnnotations.description }}
          *Runbook:* {{ .CommonAnnotations.runbook }}
          *Action Required:* Page on-call engineer immediately
```

### Slack Channels

| Channel | Purpose | Members |
|---------|---------|---------|
| **#sdlc-team** | All alerts (P1/P2/P3) | PM, Backend Lead, DevOps Lead, Tech Lead |
| **#sdlc-oncall** | Critical alerts (P0) | PM, Backend Lead (on-call rotation) |
| **#sdlc-orchestrator-beta** | User support | All beta pilot users (38 members) |

---

## 📊 Grafana Dashboard Setup

### Dashboard Import

```bash
# Copy SDLC dashboards to Grafana
docker cp /home/nqh/shared/SDLC-Orchestrator/infrastructure/monitoring/grafana/dashboards/ \
  bflow-staging-grafana:/var/lib/grafana/dashboards/sdlc/

# Restart Grafana
docker restart bflow-staging-grafana

# Dashboards available at:
# - http://192.168.0.223:3001/d/sdlc-overview (Overview)
# - http://192.168.0.223:3001/d/sdlc-api-performance (API Performance)
# - http://192.168.0.223:3001/d/sdlc-database (Database Metrics)
# - http://192.168.0.223:3001/d/sdlc-redis (Redis Metrics)
```

### Key Dashboard Panels

**SDLC Overview Dashboard**:
1. Service Health Status (8 services)
2. API p95 Latency (target: <100ms)
3. Error Rate (target: <1%)
4. Request Rate (req/sec)
5. Active Users (concurrent)
6. Gate Evaluations (success/failure)

**API Performance Dashboard**:
1. Latency Percentiles (p50, p95, p99)
2. Request Rate by Endpoint
3. Error Rate by Endpoint
4. Response Time Heatmap
5. Database Query Time
6. Redis Cache Hit Rate

---

## ✅ Deployment Checklist

### Pre-Deployment (Dec 18, before deployment)

- [ ] **Prometheus Config Updated**
  - [ ] SDLC scrape targets added (3 jobs: backend, postgres, redis)
  - [ ] Restart Prometheus: `docker restart bflow-staging-prometheus`
  - [ ] Verify targets UP: `curl http://192.168.0.223:9091/api/v1/targets`

- [ ] **Alertmanager Config Updated**
  - [ ] Slack webhook URL configured
  - [ ] Alert routes defined (P0 → sdlc-oncall, P1/P2/P3 → sdlc-team)
  - [ ] Restart Alertmanager: `docker restart bflow-staging-alertmanager`

- [ ] **Grafana Dashboards Imported**
  - [ ] SDLC dashboards copied to Grafana
  - [ ] Restart Grafana: `docker restart bflow-staging-grafana`
  - [ ] Verify dashboards accessible

- [ ] **Slack Channels Created**
  - [ ] #sdlc-team channel created
  - [ ] #sdlc-oncall channel created (optional, can use #sdlc-team)
  - [ ] #sdlc-orchestrator-beta channel created (user support)
  - [ ] Webhook URLs generated

### Post-Deployment (Dec 18, after deployment)

- [ ] **Verify Metrics Collection**
  - [ ] Check Prometheus targets: All UP
  - [ ] Check Grafana dashboards: Data visible
  - [ ] Check metric scraping: No gaps

- [ ] **Test Alerts**
  - [ ] Trigger test P2 alert (simulate high CPU)
  - [ ] Verify Slack notification received
  - [ ] Trigger test P0 alert (simulate service down)
  - [ ] Verify on-call paged (if configured)

- [ ] **Baseline Metrics**
  - [ ] Record API p95 latency (should be ~80ms)
  - [ ] Record error rate (should be <0.1%)
  - [ ] Record cache hit rate (should be ~75%)
  - [ ] Record resource usage (CPU ~30%, Memory ~40%, Disk ~50%)

---

## 📞 Contact Information

### On-Call Rotation

**Week 1 (Dec 18-24)**:
- Primary: PM
- Secondary: Backend Lead
- Escalation: Tech Lead → CTO

**Week 2 (Dec 25-31)**:
- Primary: Backend Lead
- Secondary: PM
- Escalation: Tech Lead → CTO

### Escalation Contacts

| Role | Contact | Availability |
|------|---------|--------------|
| **PM** | pm@sdlc-team.local | 24/7 (on-call weeks) |
| **Backend Lead** | backend@sdlc-team.local | 24/7 (on-call weeks) |
| **DevOps Lead** | devops@sdlc-team.local | Business hours + incidents |
| **Tech Lead** | tech@sdlc-team.local | Business hours + escalations |
| **CTO** | cto@company.com | 24/7 (critical incidents) |
| **IT Team** | dvhiep@nqh.com.vn | Business hours + infrastructure issues |

---

## 📚 Reference Documents

**Runbooks**:
- [High Latency Runbook](../02-Runbooks/HIGH-LATENCY-RUNBOOK.md) (TODO: Create)
- [Service Down Runbook](../02-Runbooks/SERVICE-DOWN-RUNBOOK.md) (TODO: Create)
- [Database Issues Runbook](../02-Runbooks/DATABASE-ISSUES-RUNBOOK.md) (TODO: Create)

**Deployment**:
- [Staging Deployment Runbook](../../05-Deployment-Release/01-Deployment-Strategy/STAGING-BETA-DEPLOYMENT-RUNBOOK.md)
- [Rollback Procedure](../../05-Deployment-Release/01-Deployment-Strategy/STAGING-BETA-DEPLOYMENT-RUNBOOK.md#rollback-procedure)

**Sprint Plans**:
- [Sprint 32 Detailed Plan](../../03-Development-Implementation/02-Sprint-Plans/SPRINT-32-BETA-PILOT-DEPLOYMENT.md)

---

**Document Status**: FINAL - Ready for Deployment
**Owner**: DevOps Lead
**Reviewer**: CTO
**Framework**: SDLC 5.1.3
**Version**: 1.0.0

---

*"Alerts without runbooks are just noise. Every alert must have a clear action plan."*

**Created**: December 13, 2025
**Last Updated**: December 13, 2025
**Next Review**: Post-deployment (Dec 18, 2025)
