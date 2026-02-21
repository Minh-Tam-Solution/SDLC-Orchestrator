# Performance Budget

**Version**: v1.0
**Date**: November 13, 2025
**Owner**: Tech Lead, SRE Lead
**Stage**: Stage 02 (HOW - Design & Architecture)
**Framework**: SDLC 6.1.0
**Status**: ✅ APPROVED

---

## 1. Overview

This document defines **performance budgets** for SDLC Orchestrator to ensure:
- **Fast user experience** (API latency <100ms p95)
- **Scalability** (1,000 concurrent users, 10K requests/min)
- **Resource efficiency** (cost optimization, rightsizing)

**Objectives**:
- Prevent performance regressions (budget violations fail CI/CD)
- Guide architecture decisions (trade-offs vs performance)
- Establish SLOs for production monitoring

**Related Documents**:
- [ADR-001-Database-Choice.md](../02-System-Architecture/Architecture-Decisions/ADR-001-Database-Choice.md) - Database performance
- [Database-Architecture.md](../03-Database-Design/Database-Architecture.md) - Indexing strategy
- [Operability-Architecture.md](../09-DevOps-Architecture/Operability-Architecture.md) - SLI/SLO monitoring

---

## 2. Performance Budget Summary

### 2.1 Latency Targets (API Endpoints)

| Endpoint Category | p50 | p95 | p99 | Max | Priority |
|-------------------|-----|-----|-----|-----|----------|
| **Authentication** (login, OAuth) | <50ms | <100ms | <200ms | 500ms | CRITICAL |
| **CRUD (Simple)** (list, get, create) | <30ms | <80ms | <150ms | 300ms | HIGH |
| **CRUD (Complex)** (gate approval, evidence upload) | <50ms | <100ms | <200ms | 500ms | HIGH |
| **Search** (evidence semantic search) | <100ms | <200ms | <500ms | 1000ms | MEDIUM |
| **GraphQL** (dashboard queries) | <80ms | <150ms | <300ms | 800ms | HIGH |
| **Webhooks** (outbound delivery) | <200ms | <500ms | <1000ms | 3000ms | LOW |

**Why these targets?**
- **Google RAIL model**: 100ms feels instant, 1000ms keeps flow
- **User perception**: <100ms = instant, 100-300ms = acceptable, >1s = slow
- **Backend budget**: 50-100ms (database 20-30ms, business logic 20-30ms, network 10-20ms)

---

### 2.2 Throughput Targets

| Metric | MVP (100 teams) | Year 3 (10K teams) | Peak (5x) | Notes |
|--------|-----------------|---------------------|-----------|-------|
| **Requests per minute** | 1,000 | 10,000 | 50,000 | Average load |
| **Concurrent users** | 100 | 1,000 | 5,000 | Active sessions |
| **Database connections** | 20 | 100 | 500 | PgBouncer pooling |
| **Evidence uploads/day** | 100 | 10,000 | 50,000 | 100MB max per file |
| **Webhook deliveries/day** | 500 | 50,000 | 250,000 | Retry on failure |

---

### 2.3 Resource Budgets (Infrastructure)

#### **MVP (100 Teams) - Week 5-12**

| Resource | Allocation | Cost (Monthly) | Notes |
|----------|------------|----------------|-------|
| **API Server** (FastAPI) | AWS EC2 t3.medium (2 vCPU, 4GB RAM) | $30 | Auto-scale 1-3 instances |
| **Database** (PostgreSQL) | AWS RDS db.t3.medium (2 vCPU, 4GB RAM, 100GB SSD) | $60 | Auto-backup, Multi-AZ |
| **Cache** (Redis) | AWS ElastiCache cache.t3.micro (1 vCPU, 1GB RAM) | $15 | Session store, token blacklist |
| **Object Storage** (MinIO) | AWS S3 (100GB, 10K requests/month) | $3 | Evidence vault |
| **CDN** (CloudFront) | AWS CloudFront (10GB transfer) | $1 | Static assets |
| **Monitoring** (Grafana) | Self-hosted (t3.micro) | $10 | Prometheus + Grafana |
| **TOTAL** | | **$119/month** | MVP budget |

---

#### **Year 3 (10K Teams)**

| Resource | Allocation | Cost (Monthly) | Notes |
|----------|------------|----------------|-------|
| **API Server** (FastAPI) | AWS ECS Fargate (10x t3.large, 2 vCPU, 8GB RAM each) | $720 | Auto-scale 5-20 instances |
| **Database** (PostgreSQL) | AWS RDS db.r5.xlarge (4 vCPU, 32GB RAM, 1TB SSD) + 2 read replicas | $800 | Multi-AZ, auto-failover |
| **Cache** (Redis) | AWS ElastiCache cache.r5.large (2 vCPU, 13GB RAM) | $100 | Master-slave replication |
| **Object Storage** (MinIO) | AWS S3 (10TB, 10M requests/month) | $250 | Lifecycle policy (archive to Glacier) |
| **CDN** (CloudFront) | AWS CloudFront (1TB transfer) | $85 | Edge caching |
| **Monitoring** (Grafana) | AWS EC2 t3.medium (2 vCPU, 4GB RAM) | $30 | HA setup (Loki + Tempo) |
| **Load Balancer** | AWS ALB | $25 | SSL termination, health checks |
| **TOTAL** | | **$2,010/month** | Year 3 budget |

---

### 2.4 Database Performance Budget

| Metric | Target | Measurement | Notes |
|--------|--------|-------------|-------|
| **Query latency (p95)** | <50ms | `pg_stat_statements` | EXPLAIN ANALYZE for slow queries |
| **Connection pool usage** | <80% | PgBouncer metrics | Alert at 80%, scale at 90% |
| **Cache hit ratio** | >90% | `blks_hit / (blks_hit + blks_read)` | Increase `shared_buffers` if <90% |
| **Index usage** | >80% | `pg_stat_user_indexes` | Unused indexes = waste |
| **Replication lag** | <1 second | `pg_stat_replication` | Alert if >5 seconds |
| **Disk usage** | <70% | CloudWatch | Auto-scale storage at 70% |

**Indexing Strategy** (from [Database-Architecture.md](../03-Database-Design/Database-Architecture.md)):
- **B-tree**: Primary keys, foreign keys (default)
- **GIN**: JSONB fields (policy YAML, metadata)
- **HNSW**: pgvector (AI embeddings, semantic search)
- **BRIN**: Timestamp fields (audit_log, created_at)

---

### 2.5 Caching Strategy (Redis)

| Cache Type | TTL | Invalidation | Size Budget |
|------------|-----|--------------|-------------|
| **Session tokens** | 30 days | Explicit (logout) | 1KB/session × 10K = 10MB |
| **Token blacklist** | 1 hour | TTL expiry | 100B/token × 1K = 100KB |
| **Frequent queries** (projects list) | 5 minutes | Write-through | 10KB/query × 100 = 1MB |
| **User permissions** (RBAC) | 15 minutes | Write-through | 1KB/user × 100K = 100MB |
| **GraphQL schema** | 1 hour | Deployment | 500KB |
| **TOTAL** | | | **~111MB (MVP)**, **~500MB (Year 3)** |

**Cache Hit Ratio Targets**:
- **Session lookups**: >95% (high reuse)
- **Permission checks**: >90% (high reuse)
- **Frequent queries**: >80% (medium reuse)

---

## 3. Performance Test Scenarios

### 3.1 Baseline Load (MVP - 100 Teams)

**Test Configuration**:
```yaml
Tool: Locust (Python load testing)
Duration: 15 minutes
Ramp-up: 5 minutes (0 → 100 users)
Steady state: 10 minutes (100 concurrent users)
```

**Test Scenarios**:

#### **Scenario 1: Read-Heavy (70% reads, 30% writes)**
```python
# Locust test (baseline_load.py)
from locust import HttpUser, task, between

class SDLCUser(HttpUser):
    wait_time = between(1, 3)  # 1-3 seconds between requests

    def on_start(self):
        # Login (get JWT token)
        response = self.client.post("/auth/login", json={
            "email": "test@example.com",
            "password": "password123"
        })
        self.token = response.json()["access_token"]
        self.headers = {"Authorization": f"Bearer {self.token}"}

    @task(50)  # 50% of requests
    def list_projects(self):
        self.client.get("/projects", headers=self.headers)

    @task(20)  # 20% of requests
    def get_project(self):
        self.client.get("/projects/550e8400-e29b-41d4-a716-446655440003",
                        headers=self.headers)

    @task(15)  # 15% of requests
    def list_gates(self):
        self.client.get("/projects/550e8400-e29b-41d4-a716-446655440003/gates",
                        headers=self.headers)

    @task(10)  # 10% of requests
    def create_project(self):
        self.client.post("/projects", headers=self.headers, json={
            "name": "Test Project",
            "slug": "test-project",
            "team_id": "7f3e8400-e29b-41d4-a716-446655440001"
        })

    @task(5)  # 5% of requests
    def approve_gate(self):
        self.client.post("/gates/550e8400-e29b-41d4-a716-446655440004/approve",
                         headers=self.headers, json={
                             "comment": "Approved"
                         })
```

**Expected Results**:
| Metric | Target | Pass Criteria |
|--------|--------|---------------|
| **Avg response time** | <100ms | <150ms |
| **p95 response time** | <200ms | <300ms |
| **Throughput** | 1,000 req/min | >800 req/min |
| **Error rate** | 0% | <1% |
| **Database CPU** | <50% | <70% |

---

#### **Scenario 2: Write-Heavy (30% reads, 70% writes)**
```python
# Locust test (write_heavy.py)
class SDLCWriteUser(HttpUser):
    wait_time = between(1, 3)

    @task(20)
    def create_project(self):
        self.client.post("/projects", headers=self.headers, json={...})

    @task(25)
    def upload_evidence(self):
        files = {'file': open('/tmp/test-evidence.pdf', 'rb')}
        self.client.post("/evidence", headers=self.headers,
                         files=files, data={...})

    @task(30)
    def approve_gate(self):
        self.client.post("/gates/.../approve", headers=self.headers, json={...})

    @task(15)
    def create_webhook(self):
        self.client.post("/webhooks", headers=self.headers, json={...})

    @task(10)
    def update_project(self):
        self.client.patch("/projects/...", headers=self.headers, json={...})
```

**Expected Results**:
| Metric | Target | Pass Criteria |
|--------|--------|---------------|
| **Avg response time** | <150ms | <200ms |
| **p95 response time** | <300ms | <500ms |
| **Throughput** | 500 writes/min | >400 writes/min |
| **Database writes** | <1K TPS | <2K TPS |

---

### 3.2 Stress Test (Peak Load - 5x MVP)

**Test Configuration**:
```yaml
Duration: 30 minutes
Ramp-up: 10 minutes (0 → 500 users)
Steady state: 15 minutes (500 concurrent users)
Cool-down: 5 minutes (500 → 0 users)
```

**Expected Results**:
| Metric | Target | Pass Criteria |
|--------|--------|---------------|
| **Avg response time** | <200ms | <300ms |
| **p95 response time** | <500ms | <1000ms |
| **Throughput** | 5,000 req/min | >3,000 req/min |
| **Error rate** | <1% | <5% |
| **Auto-scale triggered** | YES | 1 → 3 API servers |

---

### 3.3 Spike Test (Sudden Traffic Spike)

**Test Configuration**:
```yaml
Duration: 10 minutes
Normal load: 100 users (5 min)
Spike: 500 users (2 min) → Test auto-scale response time
Recovery: 100 users (3 min)
```

**Expected Results**:
| Metric | Target | Pass Criteria |
|--------|--------|---------------|
| **Auto-scale time** | <2 minutes | <5 minutes |
| **Error rate (spike)** | <5% | <10% |
| **Recovery time** | <1 minute | <3 minutes |

---

### 3.4 Endurance Test (Sustained Load)

**Test Configuration**:
```yaml
Duration: 4 hours
Load: 100 concurrent users (constant)
Goal: Detect memory leaks, connection leaks
```

**Expected Results**:
| Metric | Target | Pass Criteria |
|--------|--------|---------------|
| **Memory growth** | <10% over 4 hours | <20% |
| **Connection count** | Stable (<50) | <80 |
| **Avg response time** | Stable (<100ms) | <150ms |

---

## 4. Performance Optimization Strategies

### 4.1 Database Optimization

**Query Optimization**:
```sql
-- BEFORE (slow query, 2000ms)
SELECT * FROM projects
WHERE organization_id = '...'
ORDER BY created_at DESC;
-- PROBLEM: No index on (organization_id, created_at)

-- AFTER (fast query, 30ms)
CREATE INDEX idx_projects_org_created ON projects(organization_id, created_at DESC);
SELECT * FROM projects
WHERE organization_id = '...'
ORDER BY created_at DESC;
-- SOLUTION: Composite index (organization_id, created_at)
```

**N+1 Query Prevention**:
```python
# BEFORE (N+1 queries, 500ms for 50 projects)
projects = await db.projects.find_all()
for project in projects:
    gates = await db.gates.find_by_project_id(project.id)  # N queries
    project.gates = gates

# AFTER (1 query, 50ms)
projects = await db.projects.find_all()
project_ids = [p.id for p in projects]
gates = await db.gates.find_by_project_ids(project_ids)  # 1 query
gates_by_project = group_by(gates, 'project_id')
for project in projects:
    project.gates = gates_by_project[project.id]
```

**Connection Pooling**:
```python
# SQLAlchemy (async)
from sqlalchemy.ext.asyncio import create_async_engine

engine = create_async_engine(
    "postgresql+asyncpg://user:pass@host/db",
    pool_size=20,  # Default: 5 (too low for web apps)
    max_overflow=10,  # Total connections: 20 + 10 = 30
    pool_pre_ping=True,  # Verify connections before use
    pool_recycle=3600  # Recycle connections after 1 hour
)
```

---

### 4.2 Caching Strategy (Redis)

**Cache-Aside Pattern** (lazy loading):
```python
# Read-through cache
async def get_project(project_id: str):
    # 1. Check cache first
    cached = await redis.get(f"project:{project_id}")
    if cached:
        return json.loads(cached)  # Cache hit (fast, ~5ms)

    # 2. Cache miss → fetch from database
    project = await db.projects.find_by_id(project_id)  # Slow (~30ms)

    # 3. Store in cache (TTL: 5 minutes)
    await redis.setex(f"project:{project_id}", 300, json.dumps(project))

    return project
```

**Write-Through Pattern** (immediate consistency):
```python
# Write-through cache
async def update_project(project_id: str, data: dict):
    # 1. Update database
    project = await db.projects.update(project_id, data)

    # 2. Invalidate cache (or update cache)
    await redis.delete(f"project:{project_id}")

    return project
```

**Cache Warm-Up** (pre-load hot data):
```python
# Warm-up cache on startup
async def warmup_cache():
    # Load top 100 most-accessed projects
    top_projects = await db.projects.find_top(limit=100, order_by="access_count")
    for project in top_projects:
        await redis.setex(f"project:{project.id}", 300, json.dumps(project))
```

---

### 4.3 API Optimization

**Pagination** (limit result sets):
```python
# BEFORE (fetch all projects, 5000ms for 10K projects)
@app.get("/projects")
async def list_projects():
    projects = await db.projects.find_all()  # 10K rows
    return {"data": projects}

# AFTER (paginate, 50ms for 20 projects)
@app.get("/projects")
async def list_projects(page: int = 1, limit: int = 20):
    offset = (page - 1) * limit
    projects = await db.projects.find_all(limit=limit, offset=offset)
    total = await db.projects.count()
    return {
        "data": projects,
        "pagination": {"page": page, "limit": limit, "total": total}
    }
```

**Compression** (gzip response):
```python
# FastAPI (automatic gzip for responses >500 bytes)
from fastapi.middleware.gzip import GZipMiddleware

app.add_middleware(GZipMiddleware, minimum_size=500)

# BEFORE: 50KB JSON response
# AFTER: 10KB gzipped (5x reduction)
```

**Field Selection** (GraphQL-style):
```python
# BEFORE (return all fields, 10KB response)
@app.get("/projects/{project_id}")
async def get_project(project_id: str):
    project = await db.projects.find_by_id(project_id)
    return project  # All fields (30+ fields)

# AFTER (field selection, 2KB response)
@app.get("/projects/{project_id}")
async def get_project(project_id: str, fields: str = None):
    project = await db.projects.find_by_id(project_id)
    if fields:
        # Return only requested fields: /projects/123?fields=id,name,status
        selected_fields = fields.split(",")
        return {k: v for k, v in project.items() if k in selected_fields}
    return project
```

---

### 4.4 Evidence Upload Optimization

**Direct S3 Upload** (bypass API server):
```python
# BEFORE (upload through API server, slow for 100MB files)
@app.post("/evidence")
async def upload_evidence(file: UploadFile):
    # File passes through API server (100MB upload → high memory)
    content = await file.read()
    s3_client.upload_fileobj(content, bucket="evidence", key=file.filename)

# AFTER (presigned URL, direct S3 upload)
@app.post("/evidence/upload-url")
async def get_upload_url(filename: str):
    # 1. Generate presigned URL (valid for 15 minutes)
    presigned_url = s3_client.generate_presigned_url(
        'put_object',
        Params={'Bucket': 'evidence', 'Key': filename},
        ExpiresIn=900
    )

    # 2. Return presigned URL to client
    return {"upload_url": presigned_url}

# Client uploads directly to S3 (no API server overhead)
# PUT https://s3.amazonaws.com/evidence/file.pdf?X-Amz-Signature=...
```

---

### 4.5 GraphQL Performance

**DataLoader** (batch + cache):
```python
# BEFORE (N+1 queries for gates)
from strawberry import type, field

@type
class Project:
    id: str
    name: str

    @field
    async def gates(self) -> List[Gate]:
        # N+1 query: 1 query per project
        return await db.gates.find_by_project_id(self.id)

# AFTER (DataLoader, batching)
from strawberry.dataloader import DataLoader

async def load_gates_by_project_id(project_ids: List[str]) -> List[List[Gate]]:
    # 1 query for all project IDs
    gates = await db.gates.find_by_project_ids(project_ids)
    gates_by_project = group_by(gates, 'project_id')
    return [gates_by_project.get(pid, []) for pid in project_ids]

gate_loader = DataLoader(load_fn=load_gates_by_project_id)

@type
class Project:
    @field
    async def gates(self) -> List[Gate]:
        return await gate_loader.load(self.id)
```

**Query Complexity Limit**:
```python
# Prevent malicious deep queries
from strawberry.extensions import QueryDepthLimiter

schema = strawberry.Schema(
    query=Query,
    extensions=[
        QueryDepthLimiter(max_depth=10)  # Max nesting depth
    ]
)

# BLOCKED query (depth 15)
query {
  project {
    gates {
      approvals {
        user {
          team {
            projects {
              gates {
                approvals {
                  user { ... }  # Too deep!
                }
              }
            }
          }
        }
      }
    }
  }
}
```

---

## 5. Performance Monitoring

### 5.1 Real User Monitoring (RUM)

**Metrics to Track**:
| Metric | Tool | Target | Alert Threshold |
|--------|------|--------|-----------------|
| **Page Load Time** | Sentry Performance | <2 seconds | >3 seconds |
| **First Contentful Paint (FCP)** | Lighthouse | <1 second | >2 seconds |
| **Largest Contentful Paint (LCP)** | Lighthouse | <2.5 seconds | >4 seconds |
| **Time to Interactive (TTI)** | Lighthouse | <3 seconds | >5 seconds |
| **Cumulative Layout Shift (CLS)** | Lighthouse | <0.1 | >0.25 |

---

### 5.2 Backend Monitoring (APM)

**Prometheus Metrics**:
```yaml
# API Latency (histogram)
http_request_duration_seconds:
  type: histogram
  labels: [method, endpoint, status_code]
  buckets: [0.01, 0.05, 0.1, 0.2, 0.5, 1.0, 2.0, 5.0]

# Database Query Time (histogram)
db_query_duration_seconds:
  type: histogram
  labels: [query_type, table_name]
  buckets: [0.001, 0.005, 0.01, 0.05, 0.1, 0.5, 1.0]

# Cache Hit Ratio (counter)
cache_hits_total:
  type: counter
  labels: [cache_type]

cache_misses_total:
  type: counter
  labels: [cache_type]

# Error Rate (counter)
http_requests_total:
  type: counter
  labels: [method, endpoint, status_code]
```

**Grafana Dashboard**:
```yaml
Panels:
  - API Latency (p50, p95, p99)
  - Request Rate (req/min)
  - Error Rate (errors/min)
  - Database Query Time (p95)
  - Cache Hit Ratio (%)
  - Active Connections (count)
```

---

## 6. Performance Budget Enforcement (CI/CD)

### 6.1 Lighthouse CI (Frontend)

```yaml
# .github/workflows/lighthouse.yml
name: Lighthouse CI
on: [pull_request]

jobs:
  lighthouse:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: treosh/lighthouse-ci-action@v9
        with:
          urls: |
            http://localhost:3000
            http://localhost:3000/projects
          budgetPath: ./lighthouse-budget.json
          uploadArtifacts: true
```

**Budget File**:
```json
// lighthouse-budget.json
[
  {
    "path": "/*",
    "timings": [
      {"metric": "first-contentful-paint", "budget": 1000},
      {"metric": "largest-contentful-paint", "budget": 2500},
      {"metric": "interactive", "budget": 3000}
    ],
    "resourceSizes": [
      {"resourceType": "script", "budget": 300},
      {"resourceType": "stylesheet", "budget": 50},
      {"resourceType": "image", "budget": 500}
    ]
  }
]
```

---

### 6.2 Locust CI (Backend)

```yaml
# .github/workflows/performance.yml
name: Performance Test
on: [pull_request]

jobs:
  performance:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Run Locust
        run: |
          pip install locust
          locust -f tests/performance/baseline_load.py \
            --host https://staging.sdlc-orchestrator.com \
            --users 100 \
            --spawn-rate 10 \
            --run-time 5m \
            --headless \
            --html report.html

      - name: Check Performance Budget
        run: |
          # Fail if p95 latency > 200ms
          python scripts/check_performance_budget.py report.html
```

**Budget Check Script**:
```python
# scripts/check_performance_budget.py
import json

with open('report.html') as f:
    stats = parse_locust_report(f.read())

p95_latency = stats['response_times']['p95']
error_rate = stats['errors']['rate']

if p95_latency > 200:  # 200ms budget
    print(f"FAIL: p95 latency {p95_latency}ms > 200ms")
    exit(1)

if error_rate > 0.01:  # 1% error budget
    print(f"FAIL: Error rate {error_rate*100}% > 1%")
    exit(1)

print("PASS: Performance budget met")
```

---

## 7. References

- [Google RAIL Performance Model](https://web.dev/rail/) - User-centric performance model
- [Web Vitals](https://web.dev/vitals/) - Core Web Vitals (LCP, FID, CLS)
- [PostgreSQL Performance Tuning](https://www.postgresql.org/docs/current/performance-tips.html)
- [Redis Best Practices](https://redis.io/docs/manual/performance/)
- [Locust Load Testing](https://docs.locust.io/)
- [Lighthouse CI](https://github.com/GoogleChrome/lighthouse-ci)

---

## 8. Approval

| Role | Name | Approval | Date |
|------|------|----------|------|
| **Tech Lead** | [Tech Lead Name] | ✅ APPROVED | Nov 13, 2025 |
| **SRE Lead** | [SRE Lead Name] | ✅ APPROVED | Nov 13, 2025 |
| **Backend Lead** | [Backend Lead Name] | ✅ APPROVED | Nov 13, 2025 |

---

**Last Updated**: November 13, 2025
**Status**: ✅ ACCEPTED - Binding performance budget
**Next Review**: After MVP load testing (Week 12)
**Gate G2 Evidence**: `perf_budget: present`
