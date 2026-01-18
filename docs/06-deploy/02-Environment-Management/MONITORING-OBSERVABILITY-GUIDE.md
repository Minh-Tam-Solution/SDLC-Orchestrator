# Monitoring & Observability Guide
## SDLC Orchestrator - Production Monitoring Setup

**Version**: 1.0.0
**Date**: November 18, 2025
**Status**: ACTIVE - Week 4 Day 1 (Architecture Documentation)
**Authority**: Backend Lead + DevOps Lead + SRE Lead + CTO Approved
**Foundation**: Week 3 Infrastructure (Prometheus, Grafana, docker-compose.yml)
**Framework**: SDLC 5.1.3 Complete Lifecycle

---

## Document Purpose

This guide provides **comprehensive monitoring and observability setup** for SDLC Orchestrator.

**Key Sections**:
- **Monitoring Stack Overview** - Prometheus, Grafana, Loki, Alertmanager
- **Metrics Collection** - Application metrics, system metrics, custom metrics
- **Log Aggregation** - Centralized logging with Loki
- **Alerting Strategies** - Alert rules, notification channels, on-call rotation
- **Dashboards** - Pre-built Grafana dashboards for key metrics
- **Performance Monitoring** - API latency, database query performance
- **Troubleshooting** - Common issues, debugging, incident response

**Audience**:
- DevOps engineers (infrastructure setup)
- SRE engineers (monitoring, alerting, on-call)
- Backend developers (application metrics, debugging)
- Operations team (incident response)

---

## Table of Contents

1. [Overview](#overview)
2. [Monitoring Stack Setup](#monitoring-stack-setup)
3. [Metrics Collection](#metrics-collection)
4. [Log Aggregation](#log-aggregation)
5. [Alerting Strategies](#alerting-strategies)
6. [Grafana Dashboards](#grafana-dashboards)
7. [Performance Monitoring](#performance-monitoring)
8. [Incident Response](#incident-response)
9. [Troubleshooting](#troubleshooting)

---

## Overview

### Monitoring vs Observability

**Monitoring** = Tracking known issues (metrics, alerts)
- "Is the system up?"
- "Are errors increasing?"
- "Is latency high?"

**Observability** = Understanding unknown issues (logs, traces, metrics)
- "Why is the system slow?"
- "Which user is affected?"
- "What caused the error?"

### The Three Pillars of Observability

**1. Metrics** (Prometheus):
- Numeric measurements over time
- Examples: Request rate, error rate, latency, CPU usage
- Use case: Dashboards, alerts, capacity planning

**2. Logs** (Loki):
- Event records (text-based)
- Examples: Application logs, error logs, access logs
- Use case: Debugging, audit trails, root cause analysis

**3. Traces** (Optional - Jaeger/Tempo):
- Request flow across services
- Examples: API request → Database query → External API call
- Use case: Performance debugging, distributed system debugging

### Monitoring Stack Architecture

```mermaid
graph TB
    subgraph "Application Layer"
        A[FastAPI Backend]
        B[PostgreSQL]
        C[Redis]
        D[MinIO]
        E[OPA]
    end

    subgraph "Metrics Collection"
        A -->|/metrics| P[Prometheus]
        B -->|postgres_exporter| P
        C -->|redis_exporter| P
        D -->|minio_exporter| P
        E -->|opa_exporter| P
        P -->|scrape| P
    end

    subgraph "Log Aggregation"
        A -->|stdout| L[Loki]
        B -->|pg_logs| L
        C -->|redis_logs| L
        P -->|promtail| L
    end

    subgraph "Visualization"
        P -->|query| G[Grafana]
        L -->|query| G
    end

    subgraph "Alerting"
        P -->|alerts| AM[Alertmanager]
        AM -->|notify| S[Slack]
        AM -->|notify| E[Email]
        AM -->|notify| PD[PagerDuty]
    end

    style P fill:#e74c3c
    style L fill:#f39c12
    style G fill:#3498db
    style AM fill:#9b59b6
```

---

## Monitoring Stack Setup

### Docker Compose Configuration

**File**: `docker-compose.monitoring.yml`

```yaml
version: '3.9'

services:
  # ============================================================================
  # Prometheus - Metrics Collection
  # ============================================================================
  prometheus:
    image: prom/prometheus:v2.48.0
    container_name: sdlc-prometheus
    restart: unless-stopped
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.path=/prometheus'
      - '--storage.tsdb.retention.time=90d'  # Keep metrics for 90 days
      - '--web.enable-lifecycle'
    ports:
      - "9090:9090"
    volumes:
      - ./monitoring/prometheus/prometheus.yml:/etc/prometheus/prometheus.yml:ro
      - ./monitoring/prometheus/alerts.yml:/etc/prometheus/alerts.yml:ro
      - prometheus_data:/prometheus
    networks:
      - sdlc-network
    healthcheck:
      test: ["CMD", "wget", "--spider", "-q", "http://localhost:9090/-/healthy"]
      interval: 10s
      timeout: 5s
      retries: 5

  # ============================================================================
  # Grafana - Visualization
  # ============================================================================
  grafana:
    image: grafana/grafana:10.2.2
    container_name: sdlc-grafana
    restart: unless-stopped
    environment:
      GF_SECURITY_ADMIN_USER: ${GRAFANA_ADMIN_USER:-admin}
      GF_SECURITY_ADMIN_PASSWORD: ${GRAFANA_ADMIN_PASSWORD:-admin_changeme}
      GF_INSTALL_PLUGINS: grafana-piechart-panel
      GF_SERVER_ROOT_URL: https://grafana.your-domain.com
      GF_AUTH_ANONYMOUS_ENABLED: "false"
    ports:
      - "3000:3000"
    volumes:
      - ./monitoring/grafana/provisioning:/etc/grafana/provisioning:ro
      - ./monitoring/grafana/dashboards:/var/lib/grafana/dashboards:ro
      - grafana_data:/var/lib/grafana
    networks:
      - sdlc-network
    healthcheck:
      test: ["CMD", "wget", "--spider", "-q", "http://localhost:3000/api/health"]
      interval: 10s
      timeout: 5s
      retries: 5
    depends_on:
      - prometheus

  # ============================================================================
  # Loki - Log Aggregation
  # ============================================================================
  loki:
    image: grafana/loki:2.9.3
    container_name: sdlc-loki
    restart: unless-stopped
    command: -config.file=/etc/loki/local-config.yaml
    ports:
      - "3100:3100"
    volumes:
      - ./monitoring/loki/loki-config.yml:/etc/loki/local-config.yaml:ro
      - loki_data:/loki
    networks:
      - sdlc-network
    healthcheck:
      test: ["CMD", "wget", "--spider", "-q", "http://localhost:3100/ready"]
      interval: 10s
      timeout: 5s
      retries: 5

  # ============================================================================
  # Promtail - Log Shipper (sends logs to Loki)
  # ============================================================================
  promtail:
    image: grafana/promtail:2.9.3
    container_name: sdlc-promtail
    restart: unless-stopped
    command: -config.file=/etc/promtail/config.yml
    volumes:
      - ./monitoring/promtail/promtail-config.yml:/etc/promtail/config.yml:ro
      - /var/log:/var/log:ro  # Host system logs
      - /var/lib/docker/containers:/var/lib/docker/containers:ro  # Docker container logs
    networks:
      - sdlc-network
    depends_on:
      - loki

  # ============================================================================
  # Alertmanager - Alert Routing & Notification
  # ============================================================================
  alertmanager:
    image: prom/alertmanager:v0.26.0
    container_name: sdlc-alertmanager
    restart: unless-stopped
    command:
      - '--config.file=/etc/alertmanager/alertmanager.yml'
      - '--storage.path=/alertmanager'
    ports:
      - "9093:9093"
    volumes:
      - ./monitoring/alertmanager/alertmanager.yml:/etc/alertmanager/alertmanager.yml:ro
      - alertmanager_data:/alertmanager
    networks:
      - sdlc-network
    healthcheck:
      test: ["CMD", "wget", "--spider", "-q", "http://localhost:9093/-/healthy"]
      interval: 10s
      timeout: 5s
      retries: 5

  # ============================================================================
  # Node Exporter - System Metrics (CPU, RAM, Disk)
  # ============================================================================
  node-exporter:
    image: prom/node-exporter:v1.7.0
    container_name: sdlc-node-exporter
    restart: unless-stopped
    command:
      - '--path.procfs=/host/proc'
      - '--path.sysfs=/host/sys'
      - '--path.rootfs=/rootfs'
      - '--collector.filesystem.mount-points-exclude=^/(sys|proc|dev|host|etc)($$|/)'
    ports:
      - "9100:9100"
    volumes:
      - /proc:/host/proc:ro
      - /sys:/host/sys:ro
      - /:/rootfs:ro
    networks:
      - sdlc-network

  # ============================================================================
  # Postgres Exporter - PostgreSQL Metrics
  # ============================================================================
  postgres-exporter:
    image: prometheuscommunity/postgres-exporter:v0.15.0
    container_name: sdlc-postgres-exporter
    restart: unless-stopped
    environment:
      DATA_SOURCE_NAME: "postgresql://sdlc_user:${POSTGRES_PASSWORD}@postgres:5432/sdlc_orchestrator?sslmode=disable"
    ports:
      - "9187:9187"
    networks:
      - sdlc-network
    depends_on:
      - postgres

  # ============================================================================
  # Redis Exporter - Redis Metrics
  # ============================================================================
  redis-exporter:
    image: oliver006/redis_exporter:v1.55.0
    container_name: sdlc-redis-exporter
    restart: unless-stopped
    environment:
      REDIS_ADDR: "redis://redis:6379"
      REDIS_PASSWORD: ${REDIS_PASSWORD}
    ports:
      - "9121:9121"
    networks:
      - sdlc-network
    depends_on:
      - redis

volumes:
  prometheus_data:
  grafana_data:
  loki_data:
  alertmanager_data:

networks:
  sdlc-network:
    external: true
```

### Prometheus Configuration

**File**: `monitoring/prometheus/prometheus.yml`

```yaml
global:
  scrape_interval: 15s  # Scrape metrics every 15 seconds
  evaluation_interval: 15s  # Evaluate alert rules every 15 seconds
  external_labels:
    cluster: 'sdlc-orchestrator'
    environment: 'production'

# Alert rules
rule_files:
  - '/etc/prometheus/alerts.yml'

# Alertmanager configuration
alerting:
  alertmanagers:
    - static_configs:
        - targets: ['alertmanager:9093']

# Scrape configurations
scrape_configs:
  # Prometheus self-monitoring
  - job_name: 'prometheus'
    static_configs:
      - targets: ['localhost:9090']

  # FastAPI Backend metrics
  - job_name: 'backend'
    static_configs:
      - targets: ['backend:8000']
    metrics_path: '/metrics'

  # PostgreSQL metrics
  - job_name: 'postgres'
    static_configs:
      - targets: ['postgres-exporter:9187']

  # Redis metrics
  - job_name: 'redis'
    static_configs:
      - targets: ['redis-exporter:9121']

  # System metrics (CPU, RAM, Disk)
  - job_name: 'node'
    static_configs:
      - targets: ['node-exporter:9100']

  # MinIO metrics (S3-compatible storage)
  - job_name: 'minio'
    metrics_path: '/minio/v2/metrics/cluster'
    static_configs:
      - targets: ['minio:9000']

  # OPA metrics (policy engine)
  - job_name: 'opa'
    static_configs:
      - targets: ['opa:8181']
    metrics_path: '/metrics'
```

### Loki Configuration

**File**: `monitoring/loki/loki-config.yml`

```yaml
auth_enabled: false

server:
  http_listen_port: 3100
  grpc_listen_port: 9096

common:
  path_prefix: /loki
  storage:
    filesystem:
      chunks_directory: /loki/chunks
      rules_directory: /loki/rules
  replication_factor: 1
  ring:
    kvstore:
      store: inmemory

schema_config:
  configs:
    - from: 2024-01-01
      store: boltdb-shipper
      object_store: filesystem
      schema: v11
      index:
        prefix: index_
        period: 24h

limits_config:
  retention_period: 90d  # Keep logs for 90 days
  max_query_length: 721h  # 30 days max query range

chunk_store_config:
  max_look_back_period: 90d

table_manager:
  retention_deletes_enabled: true
  retention_period: 90d
```

### Promtail Configuration

**File**: `monitoring/promtail/promtail-config.yml`

```yaml
server:
  http_listen_port: 9080
  grpc_listen_port: 0

positions:
  filename: /tmp/positions.yaml

clients:
  - url: http://loki:3100/loki/api/v1/push

scrape_configs:
  # Docker container logs
  - job_name: docker
    static_configs:
      - targets:
          - localhost
        labels:
          job: docker
          __path__: /var/lib/docker/containers/*/*-json.log

    pipeline_stages:
      - json:
          expressions:
            output: log
            stream: stream
            attrs: attrs
            tag: attrs.tag
      - regex:
          expression: '^(?P<container_name>[^/]+)/'
          source: tag
      - labels:
          container_name:
          stream:

  # Application logs (FastAPI)
  - job_name: backend
    static_configs:
      - targets:
          - localhost
        labels:
          job: backend
          __path__: /var/log/backend/*.log

    pipeline_stages:
      - json:
          expressions:
            level: level
            message: message
            timestamp: timestamp
      - labels:
          level:
      - timestamp:
          source: timestamp
          format: RFC3339
```

### Alertmanager Configuration

**File**: `monitoring/alertmanager/alertmanager.yml`

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
    # Critical alerts → PagerDuty (wake up on-call)
    - match:
        severity: critical
      receiver: 'pagerduty-critical'
      continue: true

    # Warning alerts → Slack
    - match:
        severity: warning
      receiver: 'slack-notifications'

receivers:
  # Slack notifications
  - name: 'slack-notifications'
    slack_configs:
      - channel: '#sdlc-alerts'
        title: '{{ .GroupLabels.alertname }}'
        text: '{{ range .Alerts }}{{ .Annotations.description }}{{ end }}'
        send_resolved: true

  # PagerDuty (critical alerts only)
  - name: 'pagerduty-critical'
    pagerduty_configs:
      - service_key: 'YOUR_PAGERDUTY_SERVICE_KEY'
        description: '{{ .GroupLabels.alertname }}'
        details:
          firing: '{{ .Alerts.Firing | len }}'
          resolved: '{{ .Alerts.Resolved | len }}'

  # Email notifications
  - name: 'email-notifications'
    email_configs:
      - to: 'ops@your-company.com'
        from: 'alertmanager@sdlc-orchestrator.com'
        smarthost: 'smtp.gmail.com:587'
        auth_username: 'alertmanager@sdlc-orchestrator.com'
        auth_password: 'your-email-password'
        headers:
          Subject: '[SDLC Alert] {{ .GroupLabels.alertname }}'

inhibit_rules:
  # Inhibit warning if critical alert is firing
  - source_match:
      severity: 'critical'
    target_match:
      severity: 'warning'
    equal: ['alertname', 'cluster', 'service']
```

---

## Metrics Collection

### Application Metrics (FastAPI)

**Install Prometheus Client**:
```bash
pip install prometheus-client
```

**Add Metrics to FastAPI** (`backend/app/main.py`):
```python
from fastapi import FastAPI, Request
from prometheus_client import Counter, Histogram, Gauge, make_asgi_app
import time

app = FastAPI()

# ============================================================================
# Prometheus Metrics
# ============================================================================

# HTTP request counter
http_requests_total = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status_code']
)

# HTTP request duration histogram
http_request_duration_seconds = Histogram(
    'http_request_duration_seconds',
    'HTTP request duration in seconds',
    ['method', 'endpoint'],
    buckets=[0.01, 0.05, 0.1, 0.5, 1.0, 2.5, 5.0, 10.0]
)

# Active requests gauge
http_requests_in_progress = Gauge(
    'http_requests_in_progress',
    'Number of HTTP requests in progress',
    ['method', 'endpoint']
)

# Database connection pool metrics
db_connections_active = Gauge(
    'db_connections_active',
    'Number of active database connections'
)

db_connections_idle = Gauge(
    'db_connections_idle',
    'Number of idle database connections'
)

# Cache metrics (Redis)
cache_hits_total = Counter(
    'cache_hits_total',
    'Total cache hits'
)

cache_misses_total = Counter(
    'cache_misses_total',
    'Total cache misses'
)

# Business metrics
gates_evaluated_total = Counter(
    'gates_evaluated_total',
    'Total gates evaluated',
    ['gate_number', 'status']
)

evidence_uploaded_total = Counter(
    'evidence_uploaded_total',
    'Total evidence files uploaded',
    ['gate_id']
)

# ============================================================================
# Middleware - Automatic Metric Collection
# ============================================================================

@app.middleware("http")
async def prometheus_middleware(request: Request, call_next):
    """Collect HTTP request metrics automatically."""
    method = request.method
    endpoint = request.url.path

    # Track request in progress
    http_requests_in_progress.labels(method=method, endpoint=endpoint).inc()

    # Track request duration
    start_time = time.time()
    try:
        response = await call_next(request)
        status_code = response.status_code
    except Exception as e:
        status_code = 500
        raise e
    finally:
        duration = time.time() - start_time

        # Record metrics
        http_requests_total.labels(
            method=method,
            endpoint=endpoint,
            status_code=status_code
        ).inc()

        http_request_duration_seconds.labels(
            method=method,
            endpoint=endpoint
        ).observe(duration)

        http_requests_in_progress.labels(method=method, endpoint=endpoint).dec()

    return response

# ============================================================================
# Metrics Endpoint
# ============================================================================

# Mount Prometheus metrics endpoint at /metrics
metrics_app = make_asgi_app()
app.mount("/metrics", metrics_app)

# ============================================================================
# Example: Business Metric (Gate Evaluation)
# ============================================================================

@app.post("/api/v1/gates/{gate_id}/evaluate")
async def evaluate_gate(gate_id: str):
    """Evaluate gate (example with metrics)."""
    # ... gate evaluation logic ...

    # Record business metric
    gates_evaluated_total.labels(
        gate_number="G1",
        status="PASSED"
    ).inc()

    return {"status": "PASSED"}
```

### Database Metrics (PostgreSQL)

**PostgreSQL Exporter** automatically collects:
- **Connection Metrics**: Active connections, idle connections, max connections
- **Query Performance**: Slow queries, query duration, query count
- **Database Size**: Table sizes, index sizes, total database size
- **Replication**: Replication lag, replication status
- **Locks**: Lock waits, deadlocks

**Custom Queries** (`monitoring/postgres-exporter/queries.yml`):
```yaml
# Custom PostgreSQL queries for business metrics
pg_custom_queries:
  # User count
  - query: "SELECT COUNT(*) as user_count FROM users WHERE is_active = true"
    metrics:
      - user_count:
          usage: "GAUGE"
          description: "Total active users"

  # Gate count by status
  - query: "SELECT status, COUNT(*) as count FROM gates GROUP BY status"
    metrics:
      - status:
          usage: "LABEL"
          description: "Gate status"
      - count:
          usage: "GAUGE"
          description: "Number of gates by status"

  # Evidence storage size
  - query: "SELECT SUM(file_size_bytes) as total_size FROM gate_evidence"
    metrics:
      - total_size:
          usage: "GAUGE"
          description: "Total evidence storage size in bytes"
```

### System Metrics (Node Exporter)

**Node Exporter** automatically collects:
- **CPU**: Usage %, cores, temperature
- **Memory**: Total, used, free, cached
- **Disk**: Total, used, free, I/O operations
- **Network**: Bytes sent/received, packets, errors

---

## Log Aggregation

### Application Logging (Structured Logs)

**Structured Logging** (`backend/app/core/logging.py`):
```python
import logging
import json
from datetime import datetime
from fastapi import Request

class JSONFormatter(logging.Formatter):
    """JSON log formatter for structured logging."""

    def format(self, record):
        log_data = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
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

        # Add extra fields
        if hasattr(record, "user_id"):
            log_data["user_id"] = record.user_id
        if hasattr(record, "request_id"):
            log_data["request_id"] = record.request_id

        return json.dumps(log_data)

# Configure logger
def setup_logging():
    """Setup JSON logging for production."""
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

    # Console handler with JSON formatter
    handler = logging.StreamHandler()
    handler.setFormatter(JSONFormatter())
    logger.addHandler(handler)

    return logger

# Usage in FastAPI
from app.core.logging import setup_logging

logger = setup_logging()

@app.get("/api/v1/auth/me")
async def get_current_user(request: Request):
    logger.info(
        "User fetched profile",
        extra={
            "user_id": "25e9ed25-c232-4ce3-a3ea-5458a85a915b",
            "request_id": request.headers.get("X-Request-ID")
        }
    )
    # ...
```

**Example JSON Log Output**:
```json
{
  "timestamp": "2025-11-18T10:00:00.000Z",
  "level": "INFO",
  "logger": "app.api.v1.auth",
  "message": "User fetched profile",
  "module": "auth",
  "function": "get_current_user",
  "line": 42,
  "user_id": "25e9ed25-c232-4ce3-a3ea-5458a85a915b",
  "request_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890"
}
```

### Log Queries (Loki)

**Query Logs in Grafana**:
```logql
# All backend logs
{job="backend"}

# Error logs only
{job="backend"} |= "ERROR"

# Logs for specific user
{job="backend"} | json | user_id="25e9ed25-c232-4ce3-a3ea-5458a85a915b"

# Authentication errors
{job="backend"} | json | level="ERROR" | message=~".*authentication.*"

# Slow requests (>1s duration)
{job="backend"} | json | duration > 1000

# Count errors per minute
sum(count_over_time({job="backend"} |= "ERROR" [1m]))
```

---

## Alerting Strategies

### Alert Rules (Prometheus)

**File**: `monitoring/prometheus/alerts.yml`

```yaml
groups:
  # ============================================================================
  # Infrastructure Alerts
  # ============================================================================
  - name: infrastructure
    interval: 30s
    rules:
      # High CPU usage
      - alert: HighCPUUsage
        expr: 100 - (avg by(instance) (rate(node_cpu_seconds_total{mode="idle"}[5m])) * 100) > 80
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High CPU usage (instance {{ $labels.instance }})"
          description: "CPU usage is above 80% for 5 minutes (current: {{ $value }}%)"

      # High memory usage
      - alert: HighMemoryUsage
        expr: (1 - (node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes)) * 100 > 90
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "High memory usage (instance {{ $labels.instance }})"
          description: "Memory usage is above 90% (current: {{ $value }}%)"

      # Low disk space
      - alert: LowDiskSpace
        expr: (1 - (node_filesystem_avail_bytes{mountpoint="/"} / node_filesystem_size_bytes{mountpoint="/"})) * 100 > 80
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "Low disk space (instance {{ $labels.instance }})"
          description: "Disk usage is above 80% (current: {{ $value }}%)"

  # ============================================================================
  # Application Alerts
  # ============================================================================
  - name: application
    interval: 30s
    rules:
      # High error rate
      - alert: HighErrorRate
        expr: sum(rate(http_requests_total{status_code=~"5.."}[5m])) / sum(rate(http_requests_total[5m])) > 0.05
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "High error rate (>5%)"
          description: "Error rate is {{ $value | humanizePercentage }} (threshold: 5%)"

      # High API latency (p95)
      - alert: HighAPILatency
        expr: histogram_quantile(0.95, sum(rate(http_request_duration_seconds_bucket[5m])) by (le, endpoint)) > 1
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High API latency (p95 > 1s)"
          description: "API latency p95 is {{ $value }}s for endpoint {{ $labels.endpoint }}"

      # Service down
      - alert: ServiceDown
        expr: up{job="backend"} == 0
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "Service is down ({{ $labels.job }})"
          description: "{{ $labels.job }} has been down for more than 1 minute"

  # ============================================================================
  # Database Alerts
  # ============================================================================
  - name: database
    interval: 30s
    rules:
      # High database connections
      - alert: HighDatabaseConnections
        expr: pg_stat_database_numbackends / pg_settings_max_connections * 100 > 80
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High database connections (>80%)"
          description: "Database connections are at {{ $value }}% of max"

      # Slow queries
      - alert: SlowQueries
        expr: rate(pg_stat_statements_mean_exec_time_seconds[5m]) > 1
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "Slow database queries detected"
          description: "Average query time is {{ $value }}s (threshold: 1s)"

      # Database down
      - alert: DatabaseDown
        expr: up{job="postgres"} == 0
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "PostgreSQL database is down"
          description: "PostgreSQL has been down for more than 1 minute"

  # ============================================================================
  # Business Metrics Alerts
  # ============================================================================
  - name: business
    interval: 30s
    rules:
      # Low gate evaluation rate
      - alert: LowGateEvaluationRate
        expr: sum(rate(gates_evaluated_total[5m])) < 0.1
        for: 10m
        labels:
          severity: warning
        annotations:
          summary: "Low gate evaluation rate"
          description: "Gate evaluation rate is {{ $value }} evaluations/second (expected: >0.1)"

      # High gate failure rate
      - alert: HighGateFailureRate
        expr: sum(rate(gates_evaluated_total{status="BLOCKED"}[5m])) / sum(rate(gates_evaluated_total[5m])) > 0.5
        for: 10m
        labels:
          severity: warning
        annotations:
          summary: "High gate failure rate (>50%)"
          description: "{{ $value | humanizePercentage }} of gates are failing"
```

### Alert Notification Examples

**Slack Notification**:
```
🔴 [CRITICAL] High Error Rate (>5%)

Cluster: sdlc-orchestrator
Environment: production

Alert: HighErrorRate
Severity: critical
Value: 8.5%
Threshold: 5%

Runbook: https://docs.sdlc-orchestrator.com/runbooks/high-error-rate
Grafana: https://grafana.your-domain.com/d/api-overview

Started: 2025-11-18 10:00:00 UTC
Duration: 5 minutes
```

**PagerDuty Incident**:
```
Incident #12345
Severity: HIGH
Service: SDLC Orchestrator Backend

Title: Service Down (backend)

Description:
Backend service has been down for more than 1 minute.

Last check: 2025-11-18 10:05:00 UTC
Assigned to: On-call SRE (Jane Doe)

Actions:
- Acknowledge incident
- Resolve incident
- Escalate to senior SRE
```

---

## Grafana Dashboards

### Pre-Built Dashboards

**Dashboard 1: System Overview**

**Panels**:
1. **Service Status** (Singlestat) - UP/DOWN status for all services
2. **Request Rate** (Graph) - Requests per second (all endpoints)
3. **Error Rate** (Graph) - Error percentage over time
4. **API Latency** (Graph) - p50, p95, p99 latency
5. **CPU Usage** (Graph) - CPU usage % per instance
6. **Memory Usage** (Graph) - Memory usage % per instance
7. **Disk Usage** (Graph) - Disk usage % per instance

**Dashboard 2: API Performance**

**Panels**:
1. **Requests by Endpoint** (Bar chart) - Top 10 endpoints by request count
2. **Latency by Endpoint** (Heatmap) - Latency distribution per endpoint
3. **Error Rate by Endpoint** (Table) - Error count and % per endpoint
4. **Slow Requests** (Table) - Requests >1s duration
5. **Active Connections** (Graph) - Active HTTP connections

**Dashboard 3: Database Performance**

**Panels**:
1. **Connection Pool** (Graph) - Active, idle, max connections
2. **Query Performance** (Graph) - Average query duration
3. **Slow Queries** (Table) - Queries >100ms
4. **Database Size** (Singlestat) - Total database size
5. **Table Sizes** (Bar chart) - Size per table

**Dashboard 4: Business Metrics**

**Panels**:
1. **Gate Evaluations** (Graph) - Evaluations per hour
2. **Gate Status** (Pie chart) - PENDING, PASSED, BLOCKED distribution
3. **Evidence Uploads** (Graph) - Uploads per day
4. **Active Users** (Singlestat) - Currently active users
5. **Policy Evaluations** (Graph) - Policy checks per hour

### Grafana Provisioning

**Auto-provision Dashboards** (`monitoring/grafana/provisioning/dashboards/dashboard.yml`):
```yaml
apiVersion: 1

providers:
  - name: 'SDLC Orchestrator'
    orgId: 1
    folder: ''
    type: file
    disableDeletion: false
    updateIntervalSeconds: 10
    options:
      path: /var/lib/grafana/dashboards
```

**Auto-provision Data Sources** (`monitoring/grafana/provisioning/datasources/datasource.yml`):
```yaml
apiVersion: 1

datasources:
  # Prometheus
  - name: Prometheus
    type: prometheus
    access: proxy
    url: http://prometheus:9090
    isDefault: true
    editable: false

  # Loki
  - name: Loki
    type: loki
    access: proxy
    url: http://loki:3100
    editable: false
```

---

## Performance Monitoring

### API Latency Tracking

**Key Metrics**:
- **p50 (Median)**: 50% of requests are faster than this
- **p95**: 95% of requests are faster than this (SLA target)
- **p99**: 99% of requests are faster than this (outliers)

**PromQL Query**:
```promql
# p95 latency per endpoint
histogram_quantile(0.95,
  sum(rate(http_request_duration_seconds_bucket[5m])) by (le, endpoint)
)

# p99 latency
histogram_quantile(0.99,
  sum(rate(http_request_duration_seconds_bucket[5m])) by (le, endpoint)
)
```

**SLA Targets**:
- **p95 < 100ms**: Gate evaluation, authentication
- **p95 < 200ms**: Evidence upload (10MB)
- **p95 < 1s**: Dashboard load

### Database Query Performance

**Slow Query Logging** (`postgresql.conf`):
```conf
# Log queries slower than 100ms
log_min_duration_statement = 100

# Log query plan for slow queries
auto_explain.log_min_duration = 1000
auto_explain.log_analyze = on
```

**Query Performance Dashboard**:
```sql
-- Top 10 slowest queries
SELECT
  query,
  mean_exec_time,
  calls,
  total_exec_time
FROM pg_stat_statements
ORDER BY mean_exec_time DESC
LIMIT 10;
```

---

## Incident Response

### On-Call Runbook

**Incident Response Process**:

1. **Alert Received** (Slack/PagerDuty)
   - Acknowledge alert within 5 minutes
   - Check Grafana dashboards for context

2. **Triage** (5-10 minutes)
   - Severity assessment (P0/P1/P2)
   - Impact analysis (users affected, data loss risk)
   - Assign incident commander

3. **Mitigation** (15-30 minutes)
   - Follow runbook for specific alert
   - Rollback recent deployments if needed
   - Scale up resources if needed

4. **Resolution** (varies)
   - Fix root cause
   - Verify fix in staging
   - Deploy fix to production

5. **Post-Mortem** (within 48 hours)
   - Document incident timeline
   - Root cause analysis
   - Action items to prevent recurrence

### Common Runbooks

**Runbook: High Error Rate**

**Symptoms**: Error rate >5% for 5 minutes

**Triage**:
1. Check Grafana: Which endpoints are failing?
2. Check Loki logs: What error messages?
3. Check recent deployments: Any new code?

**Mitigation**:
1. If recent deployment: Rollback immediately
2. If database issue: Check connection pool, slow queries
3. If external API issue: Enable circuit breaker

**Resolution**:
1. Fix bug in code
2. Deploy fix to staging
3. Validate fix (run integration tests)
4. Deploy fix to production
5. Monitor error rate for 30 minutes

**Runbook: Service Down**

**Symptoms**: Backend service returning 0 requests

**Triage**:
1. Check Docker: `docker-compose ps backend`
2. Check logs: `docker-compose logs backend --tail=100`
3. Check health endpoint: `curl http://backend:8000/health`

**Mitigation**:
1. Restart service: `docker-compose restart backend`
2. If still down: Check database connectivity
3. If still down: Restore from backup

**Resolution**:
1. Identify root cause (OOM, crash, network issue)
2. Fix root cause
3. Redeploy service
4. Monitor for 30 minutes

---

## Troubleshooting

### High CPU Usage

**Diagnosis**:
```bash
# Check CPU usage per container
docker stats

# Check CPU usage per process
docker exec backend top

# Profile Python application (py-spy)
docker exec backend py-spy top --pid 1
```

**Common Causes**:
- Infinite loops in application code
- Heavy CPU operations (image processing, encryption)
- High request rate (need horizontal scaling)

**Solutions**:
- Optimize CPU-intensive code
- Use async/await for I/O operations
- Scale horizontally (add more backend replicas)

### High Memory Usage

**Diagnosis**:
```bash
# Check memory usage per container
docker stats

# Check memory usage in Python
docker exec backend python -c "import psutil; print(psutil.virtual_memory())"
```

**Common Causes**:
- Memory leaks (objects not garbage collected)
- Large in-memory caches
- Database connection pool too large

**Solutions**:
- Use memory profilers (memory_profiler, tracemalloc)
- Reduce cache size
- Reduce database connection pool size

### Slow Queries

**Diagnosis**:
```sql
-- Find slow queries (PostgreSQL)
SELECT
  query,
  mean_exec_time,
  calls
FROM pg_stat_statements
WHERE mean_exec_time > 100
ORDER BY mean_exec_time DESC
LIMIT 10;
```

**Common Causes**:
- Missing indexes
- N+1 query problem (ORM)
- Full table scans

**Solutions**:
- Add indexes on frequently queried columns
- Use eager loading (SQLAlchemy `joinedload()`)
- Optimize query (avoid SELECT *)

---

## Additional Resources

### Documentation
- **Prometheus Documentation**: https://prometheus.io/docs/
- **Grafana Documentation**: https://grafana.com/docs/
- **Loki Documentation**: https://grafana.com/docs/loki/
- **Alertmanager Documentation**: https://prometheus.io/docs/alerting/latest/alertmanager/

### Internal Documentation
- **Docker Deployment Guide**: [DOCKER-DEPLOYMENT-GUIDE.md](../01-Deployment-Strategy/DOCKER-DEPLOYMENT-GUIDE.md)
- **Database Migration Strategy**: [DATABASE-MIGRATION-STRATEGY.md](../01-Deployment-Strategy/DATABASE-MIGRATION-STRATEGY.md)
- **C4 Architecture Diagrams**: [C4-ARCHITECTURE-DIAGRAMS.md](../../02-Design-Architecture/02-System-Architecture/C4-ARCHITECTURE-DIAGRAMS.md)
- **API Developer Guide**: [API-DEVELOPER-GUIDE.md](../../02-Design-Architecture/04-API-Design/API-DEVELOPER-GUIDE.md)

---

**Last Updated**: November 18, 2025
**Owner**: Backend Lead + DevOps Lead + SRE Lead + CTO
**Status**: ✅ ACTIVE (Week 4 Day 1)

---

**End of Monitoring & Observability Guide v1.0.0**
