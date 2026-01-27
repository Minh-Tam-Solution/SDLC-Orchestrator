# Sprint 111: Infrastructure Services Implementation

**Version**: 1.0.0
**Date**: TBD (Post Sprint 110)
**Status**: PLANNING
**Epic**: TEST STRATEGY 2026 - Infrastructure Layer Completion
**Framework**: SDLC 5.3.0
**Prerequisites**: Sprint 107 (TDD Foundation), Sprint 108-110 (Governance)

---

## Executive Summary

**Goal**: Implement infrastructure service layer (MinIO, OPA, Redis, GitHub, Notifications) to complete the test coverage target of 60/150 tests (40%) and enable full integration testing.

**Business Driver**: Infrastructure services are the foundation for Evidence Vault, Policy Engine, Caching, and External Integrations. Without proper implementation, the governance system cannot function in production.

**Scope**: 5 infrastructure services, 49 methods, Docker Compose test environment, CI/CD integration.

**Gap Analysis**:
- Current: 41/150 tests passing (27.3%)
- Target: 60/150 tests passing (40%)
- Gap: 19 tests (covered by 5 infrastructure services)

---

## Strategic Context

### Sprint 107 Foundation (INPUT)

| Deliverable | Status | Sprint 111 Use |
|-------------|--------|----------------|
| Test Factories (6) | ✅ Complete | Reuse for integration tests |
| Test Stubs (150 methods) | ✅ Complete | RED phase ready |
| Core Services (5) | ✅ Complete | Integration dependencies |
| TDD Discipline | ✅ Established | Continue RED→GREEN→REFACTOR |

### Infrastructure Services Gap

| Service | Methods | Test Stub | Sprint 111 Status |
|---------|---------|-----------|-------------------|
| MinioService | 10 | ✅ Created | ⏳ Implement |
| OPAService | 10 | ✅ Created | ⏳ Implement |
| RedisService | 8 | ✅ Created | ⏳ Implement |
| NotificationService | 9 | ✅ Created | ⏳ Implement |
| GitHubService | 12 | ✅ Created | ⏳ Implement |

**Total:** 49 methods to implement

---

## Sprint Goals

### Primary Goals

1. **MinIO Service**: Evidence Vault storage operations (AGPL-safe, network-only)
2. **OPA Service**: Policy evaluation via REST API (AGPL-safe, network-only)
3. **Redis Service**: Caching and session management
4. **GitHub Service**: PR/Issue sync, webhook handling
5. **Notification Service**: Slack/Email notifications
6. **Docker Test Environment**: Compose file for integration testing
7. **CI/CD Integration**: GitHub Actions test workflow

### Success Criteria

| Metric | Target | Verification |
|--------|--------|--------------|
| Infrastructure services | 5/5 | Unit tests pass |
| Methods implemented | 49/49 | All methods functional |
| Tests passing | 60/150 (40%) | pytest report |
| Integration tests | 10+ scenarios | Docker Compose tests |
| AGPL compliance | 100% | No SDK imports |
| Zero Mock Policy | 100% | TDD discipline |
| CI/CD pipeline | Working | GitHub Actions green |

### Out of Scope (Sprint 112+)

- ❌ Load testing (Locust) - Sprint 112
- ❌ E2E tests (Playwright) - Sprint 112
- ❌ Performance optimization - Sprint 112
- ❌ Production deployment - Sprint 113

---

## Architecture Overview

### Infrastructure Layer (AGPL-Safe Design)

```
┌─────────────────────────────────────────────────────────────────┐
│  LAYER 3: BUSINESS LOGIC (Sprint 107 - COMPLETE)               │
│  GateService, ProjectService, PolicyService, UserService        │
│  PlanningOrchestratorService                                    │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│  LAYER 2: INTEGRATION (Sprint 111 - THIS SPRINT)               │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐               │
│  │ MinioService│ │ OPAService  │ │RedisService │               │
│  │ (S3 API)    │ │ (REST API)  │ │ (Protocol)  │               │
│  └─────────────┘ └─────────────┘ └─────────────┘               │
│  ┌─────────────┐ ┌─────────────┐                               │
│  │GitHubService│ │Notification │                               │
│  │ (REST API)  │ │ Service     │                               │
│  └─────────────┘ └─────────────┘                               │
│                                                                 │
│  AGPL COMPLIANCE: Network-only access (NO SDK imports)          │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│  LAYER 1: INFRASTRUCTURE (Docker Compose)                       │
│  MinIO (AGPL) | OPA (Apache-2.0) | Redis (BSD) | PostgreSQL    │
└─────────────────────────────────────────────────────────────────┘
```

### AGPL Containment Strategy

```python
# ❌ BANNED - Triggers AGPL contamination
from minio import Minio
client = Minio("localhost:9000")

# ✅ REQUIRED - Network-only access (AGPL-safe)
import httpx  # or requests

async def upload_to_minio(file_path: str, bucket: str, object_name: str) -> str:
    """Upload file to MinIO via S3 API (network-only, AGPL-safe)"""
    async with httpx.AsyncClient() as client:
        with open(file_path, 'rb') as f:
            response = await client.put(
                f"http://minio:9000/{bucket}/{object_name}",
                content=f.read(),
                headers={"Content-Type": "application/octet-stream"}
            )
    response.raise_for_status()
    return f"s3://{bucket}/{object_name}"
```

---

## Day-by-Day Implementation Plan

### **Day 1: Docker Test Environment + MinioService**

**Owner**: Backend Lead

**Deliverables**:

#### 1. Docker Compose Test Environment
```yaml
# docker-compose.test.yml
version: '3.9'
services:
  postgres-test:
    image: postgres:15.5
    environment:
      POSTGRES_DB: sdlc_test
      POSTGRES_USER: test
      POSTGRES_PASSWORD: test
    ports:
      - "5433:5432"
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U test"]
      interval: 5s
      timeout: 5s
      retries: 5

  redis-test:
    image: redis:7.2-alpine
    ports:
      - "6380:6379"
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 5s
      timeout: 5s
      retries: 5

  minio-test:
    image: minio/minio:latest
    environment:
      MINIO_ROOT_USER: minioadmin
      MINIO_ROOT_PASSWORD: minioadmin
    command: server /data --console-address ":9001"
    ports:
      - "9100:9000"
      - "9101:9001"
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:9000/minio/health/live"]
      interval: 5s
      timeout: 5s
      retries: 5

  opa-test:
    image: openpolicyagent/opa:0.58.0
    ports:
      - "8182:8181"
    command: run --server --addr :8181
    healthcheck:
      test: ["CMD", "wget", "-q", "--spider", "http://localhost:8181/health"]
      interval: 5s
      timeout: 5s
      retries: 5
```

#### 2. MinioService Implementation (~400 LOC)
```python
# backend/app/services/infrastructure/minio_service.py

class MinioService:
    """
    MinIO S3 storage operations (AGPL-safe, network-only).

    All operations use HTTP/S API calls - NO minio SDK import.
    """

    def __init__(self, endpoint: str, access_key: str, secret_key: str):
        self.endpoint = endpoint
        self.access_key = access_key
        self.secret_key = secret_key

    # Methods (10 total):
    async def upload_file(bucket, object_name, file_path) -> str
    async def download_file(bucket, object_name, dest_path) -> str
    async def delete_file(bucket, object_name) -> bool
    async def list_objects(bucket, prefix) -> List[Dict]
    async def get_object_metadata(bucket, object_name) -> Dict
    async def create_bucket(bucket_name) -> bool
    async def delete_bucket(bucket_name) -> bool
    async def bucket_exists(bucket_name) -> bool
    async def generate_presigned_url(bucket, object_name, expires) -> str
    async def copy_object(src_bucket, src_object, dest_bucket, dest_object) -> bool
```

**Testing**:
```bash
# Start test environment
docker-compose -f docker-compose.test.yml up -d

# Run MinIO service tests
pytest backend/tests/services/test_minio_service.py -v

# Verify AGPL compliance (no minio import)
grep -r "from minio import" backend/app/services/ && echo "FAIL: AGPL violation" || echo "PASS: AGPL compliant"
```

**Exit Criteria**:
- [ ] Docker Compose starts all services
- [ ] MinioService: 10/10 methods implemented
- [ ] Tests: All passing with real MinIO
- [ ] AGPL compliance verified

---

### **Day 2: OPAService Implementation**

**Owner**: Backend Lead

**Deliverables**:

#### OPAService Implementation (~350 LOC)
```python
# backend/app/services/infrastructure/opa_service.py

class OPAService:
    """
    OPA Policy evaluation via REST API (AGPL-safe, network-only).

    All operations use HTTP/S API calls - NO OPA SDK import.
    """

    def __init__(self, endpoint: str = "http://opa:8181"):
        self.endpoint = endpoint

    # Methods (10 total):
    async def evaluate_policy(policy_path, input_data) -> Dict
    async def upload_policy(policy_id, rego_content) -> bool
    async def delete_policy(policy_id) -> bool
    async def list_policies() -> List[str]
    async def get_policy(policy_id) -> str
    async def upload_data(data_path, data) -> bool
    async def get_data(data_path) -> Dict
    async def health_check() -> bool
    async def compile_policy(rego_content) -> Dict  # Syntax check
    async def evaluate_batch(policy_path, inputs) -> List[Dict]
```

**OPA Policy Example** (SDLC Gate Evaluation):
```rego
# policies/sdlc/gates/g1_design_ready.rego
package sdlc.gates.g1

default allow = false

allow {
    input.architecture_documented == true
    input.api_contracts_defined == true
    input.data_model_reviewed == true
    input.security_baseline_met == true
}

violations[msg] {
    not input.architecture_documented
    msg := "Architecture documentation missing"
}

violations[msg] {
    not input.api_contracts_defined
    msg := "API contracts not defined"
}
```

**Testing**:
```bash
# Run OPA service tests
pytest backend/tests/services/test_opa_service.py -v

# Integration test with real OPA
pytest backend/tests/integration/test_opa_integration.py -v
```

**Exit Criteria**:
- [ ] OPAService: 10/10 methods implemented
- [ ] Policy upload/evaluate working
- [ ] Batch evaluation <100ms (p95)
- [ ] Health check reliable

---

### **Day 3: RedisService Implementation**

**Owner**: Backend Lead

**Deliverables**:

#### RedisService Implementation (~300 LOC)
```python
# backend/app/services/infrastructure/redis_service.py

class RedisService:
    """
    Redis caching and session management.

    Uses redis-py (BSD license, safe to import).
    """

    def __init__(self, host: str, port: int, db: int = 0):
        self.redis = redis.Redis(host=host, port=port, db=db)

    # Methods (8 total):
    async def get(key: str) -> Optional[str]
    async def set(key: str, value: str, ttl: int = None) -> bool
    async def delete(key: str) -> bool
    async def exists(key: str) -> bool
    async def get_json(key: str) -> Optional[Dict]
    async def set_json(key: str, value: Dict, ttl: int = None) -> bool
    async def increment(key: str, amount: int = 1) -> int
    async def expire(key: str, ttl: int) -> bool
```

**Use Cases**:
```python
# Session caching
await redis.set_json(f"session:{user_id}", session_data, ttl=3600)

# Rate limiting
count = await redis.increment(f"rate:{ip}:{endpoint}")
if count > 100:
    raise RateLimitExceeded()

# Gate evaluation caching
cache_key = f"gate:{project_id}:{gate_code}"
cached = await redis.get_json(cache_key)
if cached:
    return cached
result = await evaluate_gate(...)
await redis.set_json(cache_key, result, ttl=300)
```

**Testing**:
```bash
# Run Redis service tests
pytest backend/tests/services/test_redis_service.py -v
```

**Exit Criteria**:
- [ ] RedisService: 8/8 methods implemented
- [ ] JSON serialization working
- [ ] TTL expiration tested
- [ ] Performance: <5ms for get/set

---

### **Day 4: GitHubService Implementation**

**Owner**: Backend Lead

**Deliverables**:

#### GitHubService Implementation (~500 LOC)
```python
# backend/app/services/infrastructure/github_service.py

class GitHubService:
    """
    GitHub API integration for PR/Issue sync.

    Uses GitHub REST API v3 and GraphQL API v4.
    """

    def __init__(self, token: str, base_url: str = "https://api.github.com"):
        self.token = token
        self.base_url = base_url
        self.headers = {"Authorization": f"Bearer {token}"}

    # Methods (12 total):
    async def get_pull_request(owner, repo, pr_number) -> Dict
    async def list_pull_requests(owner, repo, state, page, limit) -> List[Dict]
    async def get_pr_files(owner, repo, pr_number) -> List[Dict]
    async def get_pr_commits(owner, repo, pr_number) -> List[Dict]
    async def create_pr_comment(owner, repo, pr_number, body) -> Dict
    async def get_issue(owner, repo, issue_number) -> Dict
    async def list_issues(owner, repo, state, labels) -> List[Dict]
    async def create_issue_comment(owner, repo, issue_number, body) -> Dict
    async def get_repository(owner, repo) -> Dict
    async def get_file_content(owner, repo, path, ref) -> str
    async def get_commit(owner, repo, sha) -> Dict
    async def validate_webhook_signature(payload, signature, secret) -> bool
```

**Webhook Handler**:
```python
# backend/app/api/webhooks/github.py

@router.post("/webhooks/github")
async def github_webhook(
    request: Request,
    x_hub_signature_256: str = Header(...),
    github_service: GitHubService = Depends()
):
    payload = await request.body()

    if not github_service.validate_webhook_signature(
        payload, x_hub_signature_256, settings.GITHUB_WEBHOOK_SECRET
    ):
        raise HTTPException(401, "Invalid signature")

    event = request.headers.get("X-GitHub-Event")
    data = await request.json()

    if event == "pull_request":
        await handle_pr_event(data)
    elif event == "push":
        await handle_push_event(data)
```

**Testing**:
```bash
# Run GitHub service tests (with mocked API for unit tests)
pytest backend/tests/services/test_github_service.py -v

# Integration test (requires GitHub token)
GITHUB_TOKEN=xxx pytest backend/tests/integration/test_github_integration.py -v
```

**Exit Criteria**:
- [ ] GitHubService: 12/12 methods implemented
- [ ] Webhook signature validation working
- [ ] Rate limiting handled (429 responses)
- [ ] Pagination working for large repos

---

### **Day 5: NotificationService Implementation**

**Owner**: Backend Lead

**Deliverables**:

#### NotificationService Implementation (~350 LOC)
```python
# backend/app/services/infrastructure/notification_service.py

class NotificationService:
    """
    Multi-channel notification service (Slack, Email, In-app).
    """

    def __init__(
        self,
        slack_webhook_url: str = None,
        smtp_config: Dict = None
    ):
        self.slack_webhook_url = slack_webhook_url
        self.smtp_config = smtp_config

    # Methods (9 total):
    async def send_slack_message(channel, message, blocks) -> bool
    async def send_slack_dm(user_id, message) -> bool
    async def send_email(to, subject, body, html) -> bool
    async def send_email_batch(recipients, subject, body) -> Dict
    async def create_in_app_notification(user_id, title, body, type) -> Dict
    async def mark_notification_read(notification_id) -> bool
    async def list_user_notifications(user_id, unread_only) -> List[Dict]
    async def notify_gate_approval(gate, approver) -> bool
    async def notify_gate_rejection(gate, rejector, reason) -> bool
```

**Notification Templates**:
```python
# Gate Approval Notification
GATE_APPROVED_TEMPLATE = """
🟢 **Gate Approved**

**Project**: {project_name}
**Gate**: {gate_code} - {gate_name}
**Approved by**: {approver_name}
**Time**: {approved_at}

[View Details]({gate_url})
"""

# Gate Rejection Notification
GATE_REJECTED_TEMPLATE = """
🔴 **Gate Rejected**

**Project**: {project_name}
**Gate**: {gate_code} - {gate_name}
**Rejected by**: {rejector_name}
**Reason**: {rejection_reason}

[View Details]({gate_url})
"""
```

**Testing**:
```bash
# Run notification service tests
pytest backend/tests/services/test_notification_service.py -v
```

**Exit Criteria**:
- [ ] NotificationService: 9/9 methods implemented
- [ ] Slack integration working
- [ ] Email sending working (SMTP)
- [ ] In-app notifications stored in DB

---

### **Day 6: Integration Tests + CI/CD Pipeline**

**Owner**: Backend Lead + DevOps

**Deliverables**:

#### 1. Integration Test Suite
```python
# backend/tests/integration/test_infrastructure_integration.py

class TestInfrastructureIntegration:
    """Full integration tests with real services."""

    @pytest.fixture(scope="class")
    def docker_services(self):
        """Start Docker Compose services."""
        subprocess.run(["docker-compose", "-f", "docker-compose.test.yml", "up", "-d"])
        yield
        subprocess.run(["docker-compose", "-f", "docker-compose.test.yml", "down"])

    async def test_evidence_vault_flow(self, docker_services):
        """Test: Upload → Store metadata → Retrieve → Verify hash"""
        minio = MinioService(...)

        # Upload evidence
        url = await minio.upload_file("evidence", "test.pdf", "/tmp/test.pdf")
        assert url.startswith("s3://")

        # Verify retrieval
        await minio.download_file("evidence", "test.pdf", "/tmp/downloaded.pdf")
        assert filecmp.cmp("/tmp/test.pdf", "/tmp/downloaded.pdf")

    async def test_policy_evaluation_flow(self, docker_services):
        """Test: Upload policy → Evaluate → Get violations"""
        opa = OPAService(...)

        # Upload policy
        await opa.upload_policy("g1", G1_REGO_POLICY)

        # Evaluate
        result = await opa.evaluate_policy("sdlc/gates/g1", {
            "architecture_documented": True,
            "api_contracts_defined": False
        })

        assert result["allow"] == False
        assert "API contracts not defined" in result["violations"]

    async def test_caching_flow(self, docker_services):
        """Test: Cache → Retrieve → Expire"""
        redis = RedisService(...)

        await redis.set_json("test:key", {"value": 42}, ttl=5)
        cached = await redis.get_json("test:key")
        assert cached["value"] == 42

        await asyncio.sleep(6)
        expired = await redis.get_json("test:key")
        assert expired is None
```

#### 2. GitHub Actions CI/CD
```yaml
# .github/workflows/test-infrastructure.yml
name: Infrastructure Tests

on:
  push:
    branches: [main, develop]
    paths:
      - 'backend/app/services/infrastructure/**'
      - 'backend/tests/services/test_*_service.py'
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest

    services:
      postgres:
        image: postgres:15.5
        env:
          POSTGRES_DB: sdlc_test
          POSTGRES_USER: test
          POSTGRES_PASSWORD: test
        ports:
          - 5432:5432
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5

      redis:
        image: redis:7.2-alpine
        ports:
          - 6379:6379
        options: >-
          --health-cmd "redis-cli ping"
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5

      minio:
        image: minio/minio:latest
        env:
          MINIO_ROOT_USER: minioadmin
          MINIO_ROOT_PASSWORD: minioadmin
        ports:
          - 9000:9000

      opa:
        image: openpolicyagent/opa:0.58.0
        ports:
          - 8181:8181
        options: run --server

    steps:
      - uses: actions/checkout@v4

      - name: Set up Python 3.11
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          cd backend
          pip install -r requirements.txt
          pip install pytest pytest-asyncio pytest-cov

      - name: Run unit tests
        run: |
          cd backend
          pytest tests/services/test_minio_service.py \
                 tests/services/test_opa_service.py \
                 tests/services/test_redis_service.py \
                 tests/services/test_github_service.py \
                 tests/services/test_notification_service.py \
                 -v --cov=app/services/infrastructure

      - name: Run integration tests
        run: |
          cd backend
          pytest tests/integration/test_infrastructure_integration.py -v

      - name: Upload coverage
        uses: codecov/codecov-action@v3
        with:
          file: ./backend/coverage.xml
```

**Exit Criteria**:
- [ ] 10+ integration test scenarios passing
- [ ] CI/CD pipeline green
- [ ] Coverage report generated
- [ ] All services tested with real infrastructure

---

### **Day 7: Documentation + Sprint Wrap-up**

**Owner**: Backend Lead + Tech Writer

**Deliverables**:

#### 1. API Documentation
```markdown
# Infrastructure Services API Reference

## MinioService

### upload_file(bucket, object_name, file_path)
Upload file to MinIO Evidence Vault.

**Parameters:**
- `bucket` (str): Bucket name (e.g., "evidence", "artifacts")
- `object_name` (str): Object key in bucket
- `file_path` (str): Local file path to upload

**Returns:** `str` - S3 URI (e.g., "s3://evidence/uuid/file.pdf")

**Example:**
```python
uri = await minio.upload_file("evidence", "gate-g1/report.pdf", "/tmp/report.pdf")
```

... (document all 49 methods)
```

#### 2. Sprint Retrospective
```markdown
# Sprint 111 Retrospective

## What Went Well
- TDD discipline maintained (100%)
- AGPL compliance verified
- Docker test environment reliable

## What Could Improve
- [TBD based on sprint execution]

## Action Items for Sprint 112
- Load testing with Locust
- E2E tests with Playwright
- Performance optimization
```

**Exit Criteria**:
- [ ] All 49 methods documented
- [ ] README updated with infrastructure setup
- [ ] Sprint retrospective complete
- [ ] Sprint 112 planning prepared

---

## Testing Strategy

### Test Pyramid

```
           /\
          /  \      E2E Tests (Sprint 112)
         /    \     - Playwright browser automation
        /------\    - User journey tests
       /        \
      / Integr.  \  Integration Tests (Day 6)
     /   Tests    \ - Real Docker services
    /--------------\ - Cross-service flows
   /                \
  /   Unit Tests     \ Unit Tests (Day 1-5)
 /    (49 methods)    \ - Each method tested
/______________________\ - Factory data
```

### Coverage Targets

| Category | Target | Methods | Tests |
|----------|--------|---------|-------|
| MinioService | 100% | 10 | 10+ |
| OPAService | 100% | 10 | 10+ |
| RedisService | 100% | 8 | 8+ |
| GitHubService | 100% | 12 | 12+ |
| NotificationService | 100% | 9 | 9+ |
| **Total** | **100%** | **49** | **49+** |

### Test Progress Tracking

| Sprint | Tests Passing | Coverage | Status |
|--------|---------------|----------|--------|
| Sprint 107 (End) | 41/150 | 27.3% | ✅ Complete |
| Sprint 111 (Target) | 60/150 | 40% | ⏳ Planned |
| Sprint 112 (Target) | 100/150 | 66.7% | ⏳ Future |

---

## Risk Assessment

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| MinIO AGPL violation | Low | High | Code review, grep check |
| OPA timeout in CI | Medium | Medium | Health check before tests |
| GitHub rate limiting | Medium | Low | Mock for unit tests |
| Redis connection issues | Low | Medium | Retry logic |
| Slack webhook failures | Low | Low | Fallback to email |

---

## Dependencies

### External Dependencies

| Dependency | Version | Status | Sprint 111 Use |
|------------|---------|--------|----------------|
| MinIO | latest | ⏳ Docker | Evidence Vault |
| OPA | 0.58.0 | ⏳ Docker | Policy Engine |
| Redis | 7.2 | ⏳ Docker | Caching |
| PostgreSQL | 15.5 | ✅ Running | Metadata storage |
| GitHub API | v3/v4 | ✅ Available | PR/Issue sync |

### Internal Dependencies

| Dependency | Status | Sprint 111 Use |
|------------|--------|----------------|
| Sprint 107 (TDD Foundation) | ✅ Complete | Factories, patterns |
| Sprint 108-110 (Governance) | ⏳ In Progress | Database models |
| Core Services | ✅ Complete | Business logic |

---

## Deliverables Summary

### Code Deliverables

| File | LOC | Status |
|------|-----|--------|
| `minio_service.py` | ~400 | ⏳ Day 1 |
| `opa_service.py` | ~350 | ⏳ Day 2 |
| `redis_service.py` | ~300 | ⏳ Day 3 |
| `github_service.py` | ~500 | ⏳ Day 4 |
| `notification_service.py` | ~350 | ⏳ Day 5 |
| `docker-compose.test.yml` | ~100 | ⏳ Day 1 |
| Integration tests | ~500 | ⏳ Day 6 |
| **Total** | **~2,500** | |

### Documentation Deliverables

| Document | Status |
|----------|--------|
| Infrastructure API Reference | ⏳ Day 7 |
| Docker Setup Guide | ⏳ Day 1 |
| CI/CD Configuration | ⏳ Day 6 |
| Sprint Retrospective | ⏳ Day 7 |

---

## Approval

**Status**: ⏳ **AWAITING CTO APPROVAL**

**Prerequisites Checklist:**
- [x] Sprint 107 complete (TDD Foundation)
- [ ] Sprint 108-110 complete (Governance)
- [ ] Docker environment tested
- [ ] Team capacity confirmed

**Signatures:**
- **CTO**: ⏳ PENDING
- **Backend Lead**: ⏳ PENDING
- **DevOps Lead**: ⏳ PENDING

---

## Document Control

| Field | Value |
|-------|-------|
| **Version** | 1.0.0 |
| **Date** | January 27, 2026 |
| **Author** | Backend Lead |
| **Status** | PLANNING |
| **Sprint** | Sprint 111 |
| **Timeline** | 7 days (TBD) |
| **Prerequisites** | Sprint 107 ✅, Sprint 108-110 ⏳ |
