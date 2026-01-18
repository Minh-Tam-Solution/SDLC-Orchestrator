# MONITORING & OBSERVABILITY GUIDE
## SDLC Orchestrator - Production Monitoring Stack

**Version**: 1.0.0
**Date**: December 3, 2025
**Status**: ACTIVE - Week 4 Day 1 Architecture Documentation
**Authority**: Platform Engineering + SRE + CTO Approved
**Framework**: SDLC 5.1.3 Complete Lifecycle

---

## 🎯 **OVERVIEW**

This guide covers the **production monitoring and observability stack** for SDLC Orchestrator, enabling proactive incident detection, performance optimization, and compliance auditing.

### **Monitoring Stack Architecture**

```yaml
Observability Platform (Week 3 Day 5 Deployed):
  Metrics Collection: Prometheus 2.45 (time-series database)
  Visualization: Grafana 10.2 (dashboards + alerting)
  Alert Routing: Alertmanager 0.26 (Slack/PagerDuty integration)
  Application Tracing: OpenTelemetry (planned Week 5)
  Log Aggregation: Loki (planned Week 5)

Key Metrics Tracked:
  ✅ API Performance (request rate, latency p50/p95/p99, error rate)
  ✅ Database Performance (query time, connection pool, cache hit rate)
  ✅ Infrastructure (CPU, memory, disk, network)
  ✅ Business Metrics (gates created, evidence uploaded, policies evaluated)
  ✅ Security Events (failed logins, unauthorized access attempts)
```

---

## 📊 **PROMETHEUS METRICS**

### **Backend API Metrics**

```python
# FastAPI auto-instrumentation (backend/app/main.py)
from prometheus_fastapi_instrumentator import Instrumentator

app = FastAPI()

# Instrument FastAPI with Prometheus metrics
Instrumentator().instrument(app).expose(app, endpoint="/metrics")

# Custom metrics exposed:
# - http_requests_total (counter)
# - http_request_duration_seconds (histogram)
# - http_requests_inprogress (gauge)
```

### **Key Metrics Exported** (/metrics endpoint)

```prometheus
# HTTP request rate by endpoint
http_requests_total{method="POST",path="/api/v1/auth/login",status="200"} 1523

# Request latency histogram (p50, p95, p99)
http_request_duration_seconds_bucket{le="0.1",path="/api/v1/gates"} 8945
http_request_duration_seconds_bucket{le="0.5",path="/api/v1/gates"} 9012
http_request_duration_seconds_bucket{le="1.0",path="/api/v1/gates"} 9015
http_request_duration_seconds_sum{path="/api/v1/gates"} 456.78
http_request_duration_seconds_count{path="/api/v1/gates"} 9015

# Active requests in-flight
http_requests_inprogress{path="/api/v1/evidence/upload"} 3

# Database connection pool
db_pool_size{pool="primary"} 20
db_pool_checked_out{pool="primary"} 8
db_pool_overflow{pool="primary"} 0

# Redis cache metrics
redis_commands_total{command="GET"} 45231
redis_commands_total{command="SET"} 12456
redis_cache_hit_rate 0.87  # 87% cache hit rate

# Business metrics
gates_created_total{stage="G1"} 234
gates_created_total{stage="G2"} 156
evidence_uploaded_total{type="legal_review"} 89
policies_evaluated_total{result="PASS"} 412
policies_evaluated_total{result="FAIL"} 23
```

### **Prometheus Configuration** (docker/prometheus/prometheus.yml)

```yaml
global:
  scrape_interval: 15s      # Scrape targets every 15 seconds
  evaluation_interval: 15s  # Evaluate rules every 15 seconds
  external_labels:
    cluster: 'sdlc-orchestrator-prod'
    environment: 'production'

# Scrape configurations
scrape_configs:
  # Backend API metrics
  - job_name: 'backend'
    static_configs:
      - targets: ['backend:8000']
    metrics_path: '/metrics'
    scrape_interval: 15s

  # PostgreSQL metrics (via postgres_exporter)
  - job_name: 'postgres'
    static_configs:
      - targets: ['postgres-exporter:9187']

  # Redis metrics (via redis_exporter)
  - job_name: 'redis'
    static_configs:
      - targets: ['redis-exporter:9121']

  # Node metrics (system-level: CPU, memory, disk)
  - job_name: 'node'
    static_configs:
      - targets: ['node-exporter:9100']

  # Kubernetes metrics (if deployed on K8s)
  - job_name: 'kubernetes-apiservers'
    kubernetes_sd_configs:
      - role: endpoints
    scheme: https
    tls_config:
      ca_file: /var/run/secrets/kubernetes.io/serviceaccount/ca.crt
    bearer_token_file: /var/run/secrets/kubernetes.io/serviceaccount/token
    relabel_configs:
      - source_labels: [__meta_kubernetes_namespace, __meta_kubernetes_service_name, __meta_kubernetes_endpoint_port_name]
        action: keep
        regex: default;kubernetes;https

# Alerting rules
rule_files:
  - '/etc/prometheus/rules/*.yml'

# Alertmanager configuration
alerting:
  alertmanagers:
    - static_configs:
        - targets: ['alertmanager:9093']
```

---

## 📈 **GRAFANA DASHBOARDS**

### **Dashboard 1: API Performance Overview**

```yaml
Dashboard: API Performance Overview
Description: Real-time API performance monitoring (request rate, latency, errors)
Refresh: 5 seconds
Time Range: Last 1 hour

Panels:
  1. Request Rate (graph)
     Query: rate(http_requests_total[5m])
     Y-Axis: Requests per second
     Legend: Endpoint path

  2. Latency p95 (graph)
     Query: histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))
     Y-Axis: Seconds
     Threshold: 0.1s (warning), 0.2s (critical)

  3. Error Rate (graph)
     Query: rate(http_requests_total{status=~"5.."}[5m])
     Y-Axis: Errors per second
     Threshold: 0 (ok), >0.01 (warning)

  4. Active Requests (gauge)
     Query: http_requests_inprogress
     Threshold: 0-50 (ok), 50-100 (warning), >100 (critical)

  5. Top 10 Slowest Endpoints (table)
     Query: topk(10, histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[1h])))
     Columns: Endpoint, p95 Latency

  6. HTTP Status Codes (pie chart)
     Query: sum by (status) (rate(http_requests_total[5m]))
```

### **Dashboard 2: Database Performance**

```yaml
Dashboard: Database Performance
Description: PostgreSQL performance monitoring
Refresh: 15 seconds
Time Range: Last 6 hours

Panels:
  1. Query Execution Time (graph)
     Query: rate(pg_stat_statements_mean_exec_time_seconds[5m])
     Y-Axis: Seconds
     Threshold: 0.05s (ok), 0.1s (warning)

  2. Connection Pool Usage (gauge)
     Query: db_pool_checked_out / db_pool_size * 100
     Y-Axis: Percentage
     Threshold: 0-70% (ok), 70-90% (warning), >90% (critical)

  3. Cache Hit Rate (graph)
     Query: pg_stat_database_blks_hit / (pg_stat_database_blks_hit + pg_stat_database_blks_read)
     Y-Axis: Percentage
     Target: >95%

  4. Active Connections (graph)
     Query: pg_stat_database_numbackends
     Y-Axis: Connections
     Threshold: 0-150 (ok), 150-180 (warning), >180 (critical)

  5. Slow Queries (table)
     Query: topk(10, pg_stat_statements_mean_exec_time_seconds)
     Columns: Query, Execution Time, Calls
```

### **Dashboard 3: Infrastructure Overview**

```yaml
Dashboard: Infrastructure Overview
Description: System-level metrics (CPU, memory, disk, network)
Refresh: 10 seconds
Time Range: Last 3 hours

Panels:
  1. CPU Usage (graph)
     Query: 100 - (avg by (instance) (irate(node_cpu_seconds_total{mode="idle"}[5m])) * 100)
     Y-Axis: Percentage
     Threshold: 0-80% (ok), 80-90% (warning), >90% (critical)

  2. Memory Usage (graph)
     Query: (1 - (node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes)) * 100
     Y-Axis: Percentage
     Threshold: 0-80% (ok), 80-90% (warning), >90% (critical)

  3. Disk Usage (gauge)
     Query: (node_filesystem_size_bytes - node_filesystem_avail_bytes) / node_filesystem_size_bytes * 100
     Y-Axis: Percentage
     Threshold: 0-80% (ok), 80-90% (warning), >90% (critical)

  4. Network I/O (graph)
     Query: rate(node_network_receive_bytes_total[5m])
     Y-Axis: Bytes per second
```

### **Accessing Grafana Dashboards**

```bash
# Local development (Docker Compose)
http://localhost:3001
Username: admin
Password: admin

# Production (Kubernetes with Ingress)
https://grafana.sdlc-orchestrator.com
Username: admin
Password: <from K8s secret>

# Pre-configured dashboards:
# - API Performance Overview (ID: 1)
# - Database Performance (ID: 2)
# - Infrastructure Overview (ID: 3)
# - Business Metrics (ID: 4)
# - Security Events (ID: 5)
```

---

## 🚨 **ALERTING**

### **Alertmanager Configuration** (docker/alertmanager/alertmanager.yml)

```yaml
global:
  resolve_timeout: 5m
  slack_api_url: 'https://hooks.slack.com/services/YOUR/SLACK/WEBHOOK'

route:
  group_by: ['alertname', 'cluster', 'service']
  group_wait: 10s
  group_interval: 10s
  repeat_interval: 12h
  receiver: 'slack-notifications'
  routes:
    # Critical alerts → PagerDuty (24/7 on-call)
    - match:
        severity: critical
      receiver: 'pagerduty'
      continue: true

    # Warning alerts → Slack (business hours)
    - match:
        severity: warning
      receiver: 'slack-notifications'

receivers:
  - name: 'slack-notifications'
    slack_configs:
      - channel: '#sdlc-alerts'
        title: '{{ .GroupLabels.alertname }}'
        text: '{{ range .Alerts }}{{ .Annotations.description }}{{ end }}'
        send_resolved: true

  - name: 'pagerduty'
    pagerduty_configs:
      - service_key: 'YOUR_PAGERDUTY_INTEGRATION_KEY'
        severity: '{{ .GroupLabels.severity }}'
        description: '{{ .GroupLabels.alertname }}: {{ .CommonAnnotations.description }}'
```

### **Alert Rules** (docker/prometheus/rules/alerts.yml)

```yaml
groups:
  - name: api_alerts
    interval: 15s
    rules:
      # High API latency (p95 > 100ms)
      - alert: HighAPILatency
        expr: histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m])) > 0.1
        for: 2m
        labels:
          severity: warning
          service: backend
        annotations:
          summary: "High API latency detected"
          description: "API p95 latency is {{ $value | humanize }}s (threshold: 0.1s)"

      # High error rate (5xx > 1%)
      - alert: HighErrorRate
        expr: rate(http_requests_total{status=~"5.."}[5m]) / rate(http_requests_total[5m]) > 0.01
        for: 2m
        labels:
          severity: critical
          service: backend
        annotations:
          summary: "High HTTP 5xx error rate"
          description: "Error rate is {{ $value | humanizePercentage }} (threshold: 1%)"

      # API unavailable (no requests in 5 min)
      - alert: APIUnavailable
        expr: rate(http_requests_total[5m]) == 0
        for: 5m
        labels:
          severity: critical
          service: backend
        annotations:
          summary: "API is unavailable"
          description: "No API requests received in the last 5 minutes"

  - name: database_alerts
    interval: 30s
    rules:
      # Database connection pool exhaustion
      - alert: DatabaseConnectionPoolExhausted
        expr: db_pool_checked_out / db_pool_size > 0.9
        for: 1m
        labels:
          severity: critical
          service: postgres
        annotations:
          summary: "Database connection pool exhausted"
          description: "Connection pool usage is {{ $value | humanizePercentage }} (threshold: 90%)"

      # Low cache hit rate (<80%)
      - alert: LowCacheHitRate
        expr: redis_cache_hit_rate < 0.8
        for: 5m
        labels:
          severity: warning
          service: redis
        annotations:
          summary: "Low Redis cache hit rate"
          description: "Cache hit rate is {{ $value | humanizePercentage }} (target: >95%)"

      # Slow database queries (>1s)
      - alert: SlowDatabaseQueries
        expr: pg_stat_statements_mean_exec_time_seconds > 1.0
        for: 2m
        labels:
          severity: warning
          service: postgres
        annotations:
          summary: "Slow database queries detected"
          description: "Query execution time is {{ $value | humanize }}s (threshold: 1s)"

  - name: infrastructure_alerts
    interval: 30s
    rules:
      # High CPU usage (>90%)
      - alert: HighCPUUsage
        expr: 100 - (avg by (instance) (irate(node_cpu_seconds_total{mode="idle"}[5m])) * 100) > 90
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High CPU usage detected"
          description: "CPU usage is {{ $value | humanizePercentage }} on {{ $labels.instance }}"

      # High memory usage (>90%)
      - alert: HighMemoryUsage
        expr: (1 - (node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes)) * 100 > 90
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High memory usage detected"
          description: "Memory usage is {{ $value | humanizePercentage }} on {{ $labels.instance }}"

      # Low disk space (<10%)
      - alert: LowDiskSpace
        expr: (node_filesystem_avail_bytes / node_filesystem_size_bytes) * 100 < 10
        for: 10m
        labels:
          severity: critical
        annotations:
          summary: "Low disk space"
          description: "Disk space is {{ $value | humanizePercentage }} available on {{ $labels.instance }}"
```

---

## 📜 **LOGS & AUDIT TRAIL**

### **Structured Logging (JSON Format)**

```python
# Backend logging configuration (backend/app/core/logging.py)
import logging
import json
from datetime import datetime

class JSONFormatter(logging.Formatter):
    """Format logs as JSON for machine parsing"""
    
    def format(self, record: logging.LogRecord) -> str:
        log_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        
        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
        
        # Add custom fields
        if hasattr(record, "user_id"):
            log_data["user_id"] = record.user_id
        if hasattr(record, "request_id"):
            log_data["request_id"] = record.request_id
        
        return json.dumps(log_data)
```

### **Audit Log Table** (PostgreSQL)

```sql
-- Immutable audit trail (24 tables, Week 3 Day 2)
CREATE TABLE audit_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    event_id VARCHAR(50) NOT NULL UNIQUE,  -- evt_abc123
    timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    user_id UUID REFERENCES users(id),
    user_email VARCHAR(255),
    action VARCHAR(100) NOT NULL,  -- gate_approved, evidence_uploaded
    resource_type VARCHAR(50),     -- gate, evidence
    resource_id UUID,
    ip_address INET,
    user_agent TEXT,
    metadata JSONB,
    signature VARCHAR(256) NOT NULL,  -- HMAC-SHA256 (non-repudiation)
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Index for fast queries
CREATE INDEX idx_audit_logs_timestamp ON audit_logs(timestamp DESC);
CREATE INDEX idx_audit_logs_user_id ON audit_logs(user_id);
CREATE INDEX idx_audit_logs_action ON audit_logs(action);

-- Example audit log entry
INSERT INTO audit_logs (event_id, user_id, action, resource_type, resource_id, metadata, signature)
VALUES (
    'evt_abc123',
    '25e9ed25-c232-4ce3-a3ea-5458a85a915b',
    'gate_approved',
    'gate',
    '550e8400-e29b-41d4-a716-446655440004',
    '{"gate_name": "G1", "comment": "AGPL containment strategy approved"}'::jsonb,
    'hmac_sha256_signature_here'
);

-- Query audit logs (7-year retention for SOC 2/ISO 27001)
SELECT 
    event_id,
    timestamp,
    user_email,
    action,
    resource_type,
    metadata->>'gate_name' AS gate_name
FROM audit_logs
WHERE action = 'gate_approved'
    AND timestamp >= NOW() - INTERVAL '30 days'
ORDER BY timestamp DESC
LIMIT 100;
```

---

## 🔍 **DISTRIBUTED TRACING (Planned Week 5)**

### **OpenTelemetry Integration**

```python
# backend/app/main.py (Week 5 implementation)
from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

# Initialize tracing
trace.set_tracer_provider(TracerProvider())
trace.get_tracer_provider().add_span_processor(
    BatchSpanProcessor(OTLPSpanExporter(endpoint="http://jaeger:4317"))
)

# Instrument FastAPI automatically
FastAPIInstrumentor.instrument_app(app)

# Example trace:
# Trace ID: abc123def456
#   Span 1: POST /api/v1/gates (200ms)
#     Span 2: Query gate by ID (50ms)
#     Span 3: OPA policy evaluation (100ms)
#     Span 4: Update gate status (30ms)
#   Span 5: Slack notification (20ms)
```

---

## 📚 **RUNBOOKS (Incident Response)**

### **Runbook 1: High API Latency**

```yaml
Alert: HighAPILatency
Severity: Warning
Triggered When: p95 latency > 100ms for 2 minutes

Diagnosis Steps:
  1. Check Grafana dashboard: API Performance Overview
  2. Identify slow endpoints: Top 10 Slowest Endpoints panel
  3. Check database query time: Database Performance dashboard
  4. Check CPU/memory usage: Infrastructure Overview dashboard

Common Causes:
  - Database slow queries (missing indexes)
  - High traffic (HPA not scaling fast enough)
  - External API timeout (OPA, MinIO)
  - Memory leak (container restart needed)

Mitigation:
  - Scale backend pods: kubectl scale deployment backend --replicas=5
  - Restart slow pods: kubectl rollout restart deployment backend
  - Check slow queries: docker exec postgres psql -U sdlc_user -c "SELECT * FROM pg_stat_statements ORDER BY mean_exec_time DESC LIMIT 10;"

Prevention:
  - Add database indexes for slow queries
  - Optimize OPA policies (reduce rule complexity)
  - Implement API caching (Redis)
  - Set up aggressive HPA scaling
```

### **Runbook 2: Database Connection Pool Exhausted**

```yaml
Alert: DatabaseConnectionPoolExhausted
Severity: Critical
Triggered When: Connection pool usage > 90% for 1 minute

Diagnosis Steps:
  1. Check active connections: docker exec postgres psql -U sdlc_user -c "SELECT count(*) FROM pg_stat_activity;"
  2. Check long-running queries: docker exec postgres psql -U sdlc_user -c "SELECT pid, now() - query_start AS duration, query FROM pg_stat_activity WHERE state = 'active' ORDER BY duration DESC;"
  3. Check connection leaks in application logs

Common Causes:
  - Connection leak (not closing connections)
  - Long-running queries blocking connections
  - Traffic spike (more requests than pool can handle)

Mitigation:
  - Kill long-running queries: docker exec postgres psql -U sdlc_user -c "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE pid = 12345;"
  - Increase pool size (temporary): Edit docker-compose.yml, restart backend
  - Restart backend to reset connection pool

Prevention:
  - Fix connection leaks in code (use context managers)
  - Set statement_timeout in PostgreSQL (30s max)
  - Increase pool size permanently (edit backend/app/core/config.py)
```

---

## 🎯 **SLIs & SLOs (Service Level Objectives)**

### **Production SLOs** (Week 13 Launch Targets)

```yaml
Service Level Objectives (SLOs):
  API Availability:
    Target: 99.9% uptime (8.76 hours downtime/year)
    Measurement: (successful requests / total requests) * 100
    Error Budget: 0.1% (43.2 minutes/month)

  API Latency (p95):
    Target: <100ms for 99% of requests
    Measurement: histogram_quantile(0.95, http_request_duration_seconds_bucket)

  Database Query Time (p95):
    Target: <50ms for 95% of queries
    Measurement: histogram_quantile(0.95, pg_stat_statements_mean_exec_time_seconds)

  Data Durability:
    Target: 99.999999999% (11 nines)
    Measurement: MinIO S3 storage (AWS S3 SLA)

  Audit Log Retention:
    Target: 7 years (2,555 days)
    Measurement: audit_logs table retention policy
```

---

## ✅ **MONITORING CHECKLIST**

### **Week 4 Day 1 Deliverables** (Architecture Documentation)

- [x] Prometheus metrics configured (15s scrape interval)
- [x] Grafana dashboards created (5 dashboards)
- [x] Alertmanager rules defined (12 alerts)
- [x] Slack integration configured (#sdlc-alerts channel)
- [x] Audit log table created (7-year retention)
- [x] Structured logging implemented (JSON format)
- [x] SLOs defined (99.9% availability, <100ms p95 latency)

### **Week 5 Planned Enhancements**

- [ ] OpenTelemetry distributed tracing (Jaeger integration)
- [ ] Loki log aggregation (centralized logging)
- [ ] PagerDuty integration (24/7 on-call)
- [ ] Custom business metrics dashboards (gates created/day)
- [ ] Security event monitoring (failed login attempts)

---

## 📚 **REFERENCES**

- **Prometheus Configuration**: [docker/prometheus/prometheus.yml](../../docker/prometheus/prometheus.yml)
- **Grafana Dashboards**: [docker/grafana/provisioning/dashboards/](../../docker/grafana/provisioning/dashboards/)
- **Alert Rules**: [docker/prometheus/rules/alerts.yml](../../docker/prometheus/rules/alerts.yml)
- **Alertmanager Config**: [docker/alertmanager/alertmanager.yml](../../docker/alertmanager/alertmanager.yml)
- **Docker Deployment**: [DOCKER-DEPLOYMENT-GUIDE.md](DOCKER-DEPLOYMENT-GUIDE.md)
- **Kubernetes Deployment**: [KUBERNETES-DEPLOYMENT-GUIDE.md](KUBERNETES-DEPLOYMENT-GUIDE.md)

---

**Last Updated**: December 3, 2025
**Owner**: Platform Engineering + SRE
**Status**: ✅ COMPLETE - Week 4 Day 1 Architecture Documentation
**Next Review**: Week 4 Day 2 (Dec 4, 2025)
