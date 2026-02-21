# MentorScript: AI Safety Layer
## SASE Level 2 - Sprint 41-43
### Framework: SDLC 6.1.0

---

**Document Information**

| Field | Value |
|-------|-------|
| **Artifact ID** | MTS-AI-SAFETY |
| **Version** | 1.0.0 |
| **Status** | ACTIVE |
| **Created** | 2025-12-22 |
| **Author** | CTO Office |
| **Applies To** | Sprint 41, 42, 43 |

---

## 1. Purpose

This MentorScript provides coding standards, patterns, and guidelines for implementing the AI Safety Layer. All agents and developers working on AI detection, validation, and policy enforcement must follow these guidelines.

---

## 2. Architecture Principles

### 2.1 Layer Separation

```
┌─────────────────────────────────────────────────────────────────┐
│ API Layer (routes/)                                             │
│   - Input validation (Pydantic)                                 │
│   - Authentication/Authorization                                │
│   - Response formatting                                         │
└────────────────────────┬────────────────────────────────────────┘
                         │
┌────────────────────────┴────────────────────────────────────────┐
│ Service Layer (services/)                                       │
│   - Business logic                                              │
│   - Orchestration                                               │
│   - External integrations                                       │
└────────────────────────┬────────────────────────────────────────┘
                         │
┌────────────────────────┴────────────────────────────────────────┐
│ Data Layer (repositories/, schemas/)                            │
│   - Database operations                                         │
│   - Data models                                                 │
│   - Caching                                                     │
└─────────────────────────────────────────────────────────────────┘
```

**RULES:**
- ❌ API routes MUST NOT directly access database
- ❌ Services MUST NOT return SQLAlchemy models (use Pydantic)
- ✅ Each layer communicates only with adjacent layers

### 2.2 Dependency Injection

```python
# ✅ CORRECT: Use Depends() for dependencies
@router.post("/detect")
async def detect_ai(
    request: DetectionRequest,
    service: GitHubAIDetectionService = Depends(get_detection_service),
    db: AsyncSession = Depends(get_db),
):
    return await service.detect(...)

# ❌ WRONG: Direct instantiation in route
@router.post("/detect")
async def detect_ai(request: DetectionRequest):
    service = GitHubAIDetectionService()  # BAD!
    return await service.detect(...)
```

### 2.3 Error Handling

```python
# ✅ CORRECT: Domain-specific exceptions
class AIDetectionError(Exception):
    """Base exception for AI detection."""
    pass

class DetectionTimeoutError(AIDetectionError):
    """Detection exceeded timeout."""
    pass

class CircuitOpenError(AIDetectionError):
    """Circuit breaker is open."""
    pass

# In service:
async def detect(self, pr_data: dict) -> DetectionResult:
    try:
        if self.circuit_breaker.is_open:
            raise CircuitOpenError("Service temporarily unavailable")
        # ...
    except httpx.TimeoutException as e:
        raise DetectionTimeoutError(f"Detection timeout: {e}")

# In route:
@router.post("/detect")
async def detect_ai(request: DetectionRequest):
    try:
        result = await service.detect(...)
        return result
    except CircuitOpenError:
        raise HTTPException(503, "Service temporarily unavailable")
    except DetectionTimeoutError:
        raise HTTPException(504, "Detection timeout")
```

---

## 3. AI Detection Standards

### 3.1 Detection Strategy Pattern

```python
# All detection strategies MUST implement this interface
class AIDetectionStrategy(ABC):
    """Base class for AI detection strategies."""

    @abstractmethod
    async def detect(
        self,
        pr_data: dict,
        commits: List[dict],
        diff: str,
    ) -> DetectionResult:
        """Detect AI tool usage.

        Args:
            pr_data: PR metadata (title, body, labels)
            commits: List of commit objects
            diff: Unified diff string

        Returns:
            DetectionResult with confidence score
        """
        pass

    @abstractmethod
    def get_strategy_name(self) -> str:
        """Return unique strategy identifier."""
        pass
```

### 3.2 Weighted Voting Algorithm

```python
# Weight configuration (must sum to 1.0)
STRATEGY_WEIGHTS = {
    "metadata": 0.40,   # PR title, body analysis
    "commit": 0.40,     # Commit message patterns
    "pattern": 0.20,    # Code pattern analysis
}

# Combined detection
async def detect(self, pr_data, commits, diff) -> DetectionResult:
    results = await asyncio.gather(
        self.metadata_detector.detect(pr_data, commits, diff),
        self.commit_detector.detect(pr_data, commits, diff),
        self.pattern_detector.detect(pr_data, commits, diff),
    )

    weighted_score = sum(
        result.confidence * STRATEGY_WEIGHTS[result.method.value]
        for result in results
        if result.detected
    )

    return DetectionResult(
        detected=weighted_score >= DETECTION_THRESHOLD,
        confidence=weighted_score,
        # ...
    )
```

### 3.3 False Positive Protection

```python
# ALWAYS check for false positive patterns BEFORE detection
FALSE_POSITIVE_PATTERNS = {
    AIToolType.CURSOR: [
        r"database\s+cursor",
        r"db\s+cursor",
        r"cursor\s+position",
        r"connection\.cursor",
        # Python context manager - specific pattern
        r"with\s+\w+\.cursor\s*\(\s*\)\s+as",
    ],
    AIToolType.COPILOT: [
        r"co-?pilot\s+seat",
        r"autopilot",
        r"pilot\s+project",
    ],
    # ...
}

def _calculate_tool_score(self, tool, patterns, text) -> float:
    # Check FP patterns FIRST
    fp_patterns = FALSE_POSITIVE_PATTERNS.get(tool, [])
    if any(re.search(p, text, re.IGNORECASE) for p in fp_patterns):
        return 0.0  # Confirmed false positive

    # Then check detection patterns
    # ...
```

---

## 4. Validation Pipeline Standards

### 4.1 Validator Interface

```python
class BaseValidator(ABC):
    """Base class for all validators."""

    name: str           # Unique identifier
    blocking: bool      # If True, failure blocks PR
    timeout_ms: int     # Max execution time

    @abstractmethod
    async def validate(
        self,
        project_id: UUID,
        pr_number: int,
        files: List[FileChange],
        diff: str,
    ) -> ValidatorResult:
        """Run validation.

        Returns:
            ValidatorResult with status, message, details
        """
        pass
```

### 4.2 Validator Result Structure

```python
class ValidatorResult(BaseModel):
    validator_name: str
    status: ValidatorStatus  # PASSED, FAILED, SKIPPED, ERROR
    message: str
    details: dict
    duration_ms: int
    blocking: bool

    # Computed properties
    @property
    def is_blocking_failure(self) -> bool:
        return self.status == ValidatorStatus.FAILED and self.blocking
```

### 4.3 Pipeline Orchestration

```python
# Run validators in parallel with individual timeouts
async def run_validators(
    self,
    validators: List[BaseValidator],
    context: ValidationContext,
) -> List[ValidatorResult]:
    tasks = [
        asyncio.wait_for(
            v.validate(context.project_id, context.pr_number, ...),
            timeout=v.timeout_ms / 1000,
        )
        for v in validators
    ]

    results = await asyncio.gather(*tasks, return_exceptions=True)

    return [
        result if isinstance(result, ValidatorResult)
        else ValidatorResult(
            validator_name=validators[i].name,
            status=ValidatorStatus.ERROR,
            message=str(result),
            ...
        )
        for i, result in enumerate(results)
    ]
```

---

## 5. Circuit Breaker Standards

### 5.1 State Machine

```
     ┌──────────────────────────────────────────────────────────┐
     │                                                          │
     │  ┌─────────┐    failure_threshold    ┌──────────┐       │
     │  │ CLOSED  │ ────────────────────────► │  OPEN  │       │
     │  └────┬────┘                           └────┬───┘       │
     │       │                                     │           │
     │       │ success                  recovery_timeout       │
     │       │                                     │           │
     │       │         ┌──────────────┐            │           │
     │       └─────────┤  HALF_OPEN   │◄───────────┘           │
     │                 └──────┬───────┘                        │
     │                        │                                │
     │                        │ success_threshold              │
     │                        │                                │
     └────────────────────────┴────────────────────────────────┘
```

### 5.2 Configuration

```python
# Default configuration
CIRCUIT_BREAKER_CONFIG = {
    "failure_threshold": 5,      # Failures before opening
    "recovery_timeout": 30,      # Seconds before half-open
    "success_threshold": 3,      # Successes to close
}

# Pre-configured breakers
CIRCUIT_BREAKERS = {
    "github_api": CircuitBreaker(
        name="github_api",
        failure_threshold=5,
        recovery_timeout=30,
        success_threshold=3,
    ),
    "external_ai": CircuitBreaker(
        name="external_ai",
        failure_threshold=3,
        recovery_timeout=60,
        success_threshold=2,
    ),
}
```

### 5.3 Usage Pattern

```python
async def call_external_service(self, request):
    breaker = CIRCUIT_BREAKERS["github_api"]

    if breaker.is_open:
        raise CircuitOpenError("GitHub API circuit is open")

    try:
        response = await self.http_client.post(...)
        breaker.record_success()
        return response
    except Exception as e:
        breaker.record_failure()
        raise
```

---

## 6. Policy Guards Standards

### 6.1 Rego Policy Structure

```rego
# Template for all AI safety policies
package ai_safety.<policy_name>

import future.keywords.in

# Default: allow
default allow = true

# Deny conditions
allow = false {
    # Your deny logic here
    violation_condition
}

# Helper functions
violation_condition {
    some file in input.files
    contains_violation(file)
}

contains_violation(file) {
    # Pattern matching logic
}

# Metadata for reporting
violation_message = msg {
    not allow
    msg := "Description of what violated"
}
```

### 6.2 OPA Integration

```python
# ALWAYS use network-only access (AGPL containment)
class OPAPolicyService:
    def __init__(self, opa_url: str = "http://opa:8181"):
        self.opa_url = opa_url
        self.client = httpx.AsyncClient(timeout=10.0)

    async def evaluate_policies(
        self,
        policies: List[PolicyRule],
        input_data: dict,
    ) -> List[PolicyResult]:
        # Load policies via REST API
        for policy in policies:
            await self._load_policy(policy)

        # Evaluate via REST API
        results = []
        for policy in policies:
            result = await self._evaluate(policy, input_data)
            results.append(result)

        return results

    async def _load_policy(self, policy: PolicyRule):
        # PUT /v1/policies/{id}
        await self.client.put(
            f"{self.opa_url}/v1/policies/{policy.id}",
            content=policy.rego_policy,
        )

    async def _evaluate(self, policy: PolicyRule, input_data: dict):
        # POST /v1/data/{id}/allow
        response = await self.client.post(
            f"{self.opa_url}/v1/data/{policy.id}/allow",
            json={"input": input_data},
        )
        return response.json()
```

---

## 7. Evidence Tracking Standards

### 7.1 Event Schema

```python
class EvidenceEvent(Base):
    __tablename__ = "evidence_events"

    id = Column(UUID, primary_key=True)
    project_id = Column(UUID, ForeignKey("projects.id"), nullable=False)
    pr_number = Column(Integer, nullable=False)

    # Detection data
    detected_at = Column(DateTime(timezone=True), nullable=False)
    ai_tool = Column(String(50), nullable=True)
    confidence = Column(Float, nullable=False)
    detection_method = Column(String(20), nullable=False)

    # Validation data
    validation_status = Column(String(20), nullable=False)
    validation_results = Column(JSONB, nullable=True)

    # Evidence data (immutable)
    evidence_data = Column(JSONB, nullable=False)
    evidence_hash = Column(String(64), nullable=False)  # SHA256

    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
```

### 7.2 Immutability Rules

```python
# Evidence MUST be immutable after creation
# Only add new records, never update/delete

async def record_evidence(self, event: EvidenceEventCreate) -> EvidenceEvent:
    # Compute hash for integrity
    evidence_hash = hashlib.sha256(
        json.dumps(event.evidence_data, sort_keys=True).encode()
    ).hexdigest()

    db_event = EvidenceEvent(
        **event.dict(),
        evidence_hash=evidence_hash,
    )

    self.db.add(db_event)
    await self.db.commit()

    return db_event

# Override records are SEPARATE from evidence
async def record_override(
    self,
    evidence_event_id: UUID,
    override: OverrideCreate,
) -> EvidenceOverride:
    # Verify event exists
    event = await self.get_event(evidence_event_id)
    if not event:
        raise NotFoundError("Evidence event not found")

    # Create override record (linked, not modifying)
    db_override = EvidenceOverride(
        evidence_event_id=evidence_event_id,
        **override.dict(),
    )

    self.db.add(db_override)
    await self.db.commit()

    return db_override
```

---

## 8. Testing Standards

### 8.1 Unit Test Structure

```python
# tests/unit/test_<module>.py

class TestMetadataDetector:
    """Unit tests for MetadataDetector."""

    @pytest.fixture
    def detector(self):
        return MetadataDetector()

    @pytest.mark.asyncio
    async def test_detect_cursor_in_title(self, detector):
        """GIVEN PR with 'Cursor' in title WHEN detect THEN return detected."""
        result = await detector.detect(
            pr_data={"title": "feat: implement with Cursor", "body": ""},
            commits=[],
            diff="",
        )

        assert result.detected is True
        assert result.tool == AIToolType.CURSOR
        assert result.confidence >= 0.6

    @pytest.mark.asyncio
    async def test_false_positive_database_cursor(self, detector):
        """GIVEN PR mentioning 'database cursor' WHEN detect THEN no detection."""
        result = await detector.detect(
            pr_data={"title": "fix: database cursor leak", "body": ""},
            commits=[],
            diff="",
        )

        assert result.detected is False
```

### 8.2 Integration Test Structure

```python
# tests/integration/test_<feature>.py

class TestAIDetectionAPI:
    """Integration tests for AI Detection API."""

    @pytest.fixture
    def client(self, app):
        return TestClient(app)

    @pytest.fixture
    def auth_headers(self, test_user):
        token = create_access_token(test_user.id)
        return {"Authorization": f"Bearer {token}"}

    @pytest.mark.asyncio
    async def test_detect_endpoint_success(self, client, auth_headers):
        """Test POST /api/v1/ai-detection/detect returns valid response."""
        response = client.post(
            "/api/v1/ai-detection/detect",
            headers=auth_headers,
            json={
                "owner": "test-org",
                "repo": "test-repo",
                "pr_number": 123,
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert "is_ai_generated" in data
        assert "confidence" in data
```

### 8.3 E2E Test Structure

```python
# tests/e2e/test_<flow>.py

class TestAIDetectionE2E:
    """End-to-end tests for complete AI detection flow."""

    @pytest.mark.asyncio
    async def test_full_detection_pipeline(self):
        """Test complete flow: webhook → detection → validation → evidence."""
        # 1. Simulate GitHub webhook
        webhook_payload = create_pr_webhook_payload(...)

        # 2. Trigger detection
        detection_result = await detection_service.detect(...)

        # 3. Verify validation ran
        validation_results = await validation_pipeline.run(...)

        # 4. Verify evidence recorded
        evidence = await evidence_service.get_by_pr(...)

        assert detection_result.detected is True
        assert len(validation_results) >= 3
        assert evidence is not None
```

---

## 9. Performance Standards

### 9.1 Latency Budgets

| Operation | Target (p95) | Max |
|-----------|-------------|-----|
| AI Detection | 100ms | 500ms |
| Single Validator | 100ms | 1000ms |
| Full Validation Pipeline | 600ms | 3000ms |
| Policy Evaluation | 50ms | 200ms |
| Evidence Recording | 50ms | 200ms |

### 9.2 Monitoring

```python
# Use Prometheus metrics
from prometheus_client import Histogram, Counter

ai_detection_duration = Histogram(
    "ai_detection_duration_seconds",
    "Time spent on AI detection",
    ["strategy", "ai_tool"],
)

ai_detection_count = Counter(
    "ai_detection_total",
    "Total AI detections",
    ["result", "ai_tool"],
)

# Usage
with ai_detection_duration.labels(
    strategy="metadata",
    ai_tool=result.tool.value if result.tool else "none",
).time():
    result = await detector.detect(...)

ai_detection_count.labels(
    result="detected" if result.detected else "not_detected",
    ai_tool=result.tool.value if result.tool else "none",
).inc()
```

---

## 10. Security Standards

### 10.1 Input Validation

```python
# ALWAYS validate external input with Pydantic
class DetectionRequest(BaseModel):
    owner: str = Field(..., min_length=1, max_length=100)
    repo: str = Field(..., min_length=1, max_length=100)
    pr_number: int = Field(..., ge=1)

    @validator("owner", "repo")
    def validate_github_name(cls, v):
        if not re.match(r"^[a-zA-Z0-9-_.]+$", v):
            raise ValueError("Invalid GitHub owner/repo name")
        return v
```

### 10.2 AGPL Containment

```python
# ❌ NEVER import AGPL libraries directly
from minio import Minio  # FORBIDDEN!
from grafana_api import GrafanaApi  # FORBIDDEN!

# ✅ ALWAYS use network-only access
import httpx

async def upload_to_minio(file_path: str, bucket: str, object_name: str):
    """Upload via S3 API (network-only, AGPL-safe)."""
    async with httpx.AsyncClient() as client:
        with open(file_path, "rb") as f:
            response = await client.put(
                f"http://minio:9000/{bucket}/{object_name}",
                content=f.read(),
            )
    return response.status_code == 200
```

### 10.3 Secrets Management

```python
# ❌ NEVER hardcode secrets
API_KEY = "sk-abc123"  # FORBIDDEN!

# ✅ ALWAYS use environment variables
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    github_token: str
    opa_url: str = "http://opa:8181"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

settings = Settings()
```

---

## 11. Changelog

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0.0 | 2025-12-22 | CTO | Initial version for Sprint 41-43 |

---

**Owner**: CTO Office
**Authority**: CTO Approved
**Next Review**: After Sprint 43 completion
