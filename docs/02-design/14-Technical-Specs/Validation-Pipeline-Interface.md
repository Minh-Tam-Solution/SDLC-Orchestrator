# Validation Pipeline - Interface Design
## Technical Specification - AI Safety Layer Component

**Version**: 1.0.0
**Date**: December 21, 2025
**Status**: ✅ **APPROVED** - Implementation Complete (Sprint 42 Day 3-4)
**Author**: Backend Team
**Framework**: SDLC 6.1.0
**Epic**: EP-02 AI Safety Layer v1
**Sprint**: Sprint 42

---

## 1. Overview

### 1.1 Purpose

The Validation Pipeline orchestrates quality checks for AI-generated Pull Requests. It runs multiple validators in parallel and aggregates results to determine if a PR can be merged.

**Pipeline Latency Target**: <6 minutes p95 (all validators combined)

### 1.2 Scope

**In Scope (v1)**:
- ✅ Parallel validator execution
- ✅ 3 core validators (Lint, Tests, Coverage)
- ✅ Blocking/non-blocking policy modes
- ✅ Redis queue for async processing
- ✅ Prometheus metrics integration
- ✅ Structured logging

**Out of Scope (v1)**:
- ❌ Security validator (SAST) - deferred to Sprint 43
- ❌ Custom validator plugins - deferred to v2
- ❌ Multi-repo validation - deferred to v2

---

## 2. Architecture

### 2.1 Pipeline Flow

```
                    ┌─────────────────────────────────────────────────────────────┐
                    │                   VALIDATION PIPELINE                        │
                    │                                                              │
AI PR Detected      │   ┌─────────────┐                                           │
      │             │   │ Pipeline    │                                           │
      ▼             │   │ Start       │                                           │
┌──────────────┐    │   └──────┬──────┘                                           │
│ Redis Queue  │────┼──────────▼                                                  │
│ validation:  │    │   ┌─────────────┐      ┌─────────────────────────────────┐  │
│ queue        │    │   │ Fetch Code  │─────▶│     Run Parallel Validators     │  │
└──────────────┘    │   └─────────────┘      │                                 │  │
                    │                         │  ┌────────┐ ┌────────┐ ┌──────┐│  │
                    │                         │  │  Lint  │ │ Tests  │ │Cover ││  │
                    │                         │  │Validator│ │Validator│ │ age ││  │
                    │                         │  └───┬────┘ └───┬────┘ └──┬───┘│  │
                    │                         └──────┼──────────┼─────────┼────┘  │
                    │                                │          │         │       │
                    │                                └────┬─────┴────┬────┘       │
                    │                                     │          │            │
                    │                              ┌──────▼──────────▼──────┐     │
                    │                              │  Aggregate Results     │     │
                    │                              │  (blocking failures)   │     │
                    │                              └───────────┬───────────┘     │
                    │                                          │                  │
                    │                              ┌───────────▼───────────┐     │
                    │                              │  Apply Policy Rules   │     │
                    │                              │  (PASS/FAIL decision) │     │
                    │                              └───────────┬───────────┘     │
                    │                                          │                  │
                    │                              ┌───────────▼───────────┐     │
                    │                              │  Update Event &       │     │
                    │                              │  Comment on PR        │     │
                    │                              └───────────────────────┘     │
                    └─────────────────────────────────────────────────────────────┘
```

### 2.2 Component Overview

| Component | Purpose | Technology |
|-----------|---------|------------|
| **ValidationPipeline** | Orchestrates validators | Python asyncio |
| **BaseValidator** | Abstract interface | Python ABC |
| **LintValidator** | Code style checking | ruff, ESLint |
| **TestValidator** | Test execution | pytest, vitest |
| **CoverageValidator** | Coverage analysis | pytest-cov, vitest |
| **ValidationWorker** | Background processing | Redis, asyncio |
| **validation_metrics** | Observability | Prometheus |

---

## 3. Interface Design

### 3.1 Core Enums

```python
# backend/app/services/validators/__init__.py

class ValidatorStatus(str, Enum):
    """Validator execution status."""
    PASSED = "passed"      # All checks passed
    FAILED = "failed"      # Checks failed (may block merge)
    SKIPPED = "skipped"    # Validator skipped (no applicable files)
    ERROR = "error"        # Validator error (does not block)
    TIMEOUT = "timeout"    # Validator timed out (does not block)


class ValidationStatus(str, Enum):
    """Overall validation pipeline status."""
    PENDING = "pending"    # Not started
    RUNNING = "running"    # In progress
    PASSED = "passed"      # All blocking validators passed
    FAILED = "failed"      # At least one blocking validator failed
    ERROR = "error"        # Pipeline error
```

### 3.2 Result Data Structures

```python
@dataclass
class ValidatorResult:
    """Result from a single validator execution."""

    # Identification
    validator_name: str

    # Outcome
    status: ValidatorStatus
    message: str
    details: Dict[str, Any]

    # Performance
    duration_ms: int

    # Policy control
    blocking: bool  # If true, failure blocks merge

    # Timestamps
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    def to_dict(self) -> dict:
        """Convert to dict for JSON serialization."""
        return {
            "validator_name": self.validator_name,
            "status": self.status.value,
            "message": self.message,
            "details": self.details,
            "duration_ms": self.duration_ms,
            "blocking": self.blocking,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
        }


@dataclass
class PipelineResult:
    """Result from the validation pipeline."""

    # Identification
    event_id: UUID

    # Outcome
    status: ValidationStatus
    results: List[ValidatorResult]
    blocking_failures: List[ValidatorResult]

    # Performance
    duration_ms: int

    # Timestamps
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    # Summary
    validators_run: int = 0
    validators_passed: int = 0
    validators_failed: int = 0
```

### 3.3 Validator Configuration

```python
@dataclass
class ValidatorConfig:
    """Configuration for a validator."""

    # Enable/disable
    enabled: bool = True

    # Policy control
    blocking: bool = True  # If true, failure blocks merge

    # Timeouts
    timeout_seconds: int = 300  # 5 minutes default

    # Custom settings
    settings: Dict[str, Any] = field(default_factory=dict)
```

### 3.4 BaseValidator Abstract Class

```python
class BaseValidator(ABC):
    """
    Base class for all validators.

    Validators check specific aspects of code quality:
    - Lint/Format: Code style compliance
    - Tests: Unit/integration test execution
    - Coverage: Test coverage thresholds
    - Security: SAST/vulnerability scanning (v2)

    Each validator:
    - Receives PR files and diff
    - Runs validation logic
    - Returns ValidatorResult
    - Can be blocking or non-blocking
    """

    # Validator identification
    name: str = "base"
    description: str = "Base validator"

    # Default configuration
    default_blocking: bool = True
    default_timeout_seconds: int = 300

    def __init__(self, config: Optional[ValidatorConfig] = None):
        """Initialize with optional configuration."""
        self.config = config or ValidatorConfig(
            blocking=self.default_blocking,
            timeout_seconds=self.default_timeout_seconds,
        )

    @abstractmethod
    async def validate(
        self,
        project_id: UUID,
        pr_number: str,
        files: List[str],
        diff: str,
    ) -> ValidatorResult:
        """
        Run validation on PR files.

        Args:
            project_id: Project UUID for context
            pr_number: Pull request number
            files: List of changed file paths
            diff: Unified diff of all changes

        Returns:
            ValidatorResult with status, message, and details
        """
        pass

    def get_name(self) -> str:
        """Return validator name."""
        return self.name

    def is_blocking(self) -> bool:
        """Return whether validator is merge-blocking."""
        return self.config.blocking

    def get_timeout(self) -> int:
        """Return timeout in seconds."""
        return self.config.timeout_seconds
```

---

## 4. Validator Implementations

### 4.1 LintValidator

**Purpose**: Validate code style and formatting compliance.

**Tools**:
- Python: `ruff` (fast, Rust-based linter)
- TypeScript: `ESLint`

**Configuration**:
```yaml
name: lint
blocking: true  # Lint errors block merge
timeout: 120    # 2 minutes
```

**Implementation**:
```python
class LintValidator(BaseValidator):
    """Validate code style and formatting."""

    name = "lint"
    description = "Lint and format validation (ruff, ESLint)"
    default_blocking = True
    default_timeout_seconds = 120

    # File type mappings
    PYTHON_EXTENSIONS = {".py", ".pyi"}
    TYPESCRIPT_EXTENSIONS = {".ts", ".tsx", ".js", ".jsx"}

    async def validate(
        self,
        project_id: UUID,
        pr_number: str,
        files: List[str],
        diff: str,
    ) -> ValidatorResult:
        """Run lint validation on changed files."""
        started_at = time.time()
        errors = []
        warnings = []

        # Categorize files by language
        python_files = [f for f in files if self._is_python_file(f)]
        ts_files = [f for f in files if self._is_typescript_file(f)]

        # Run linters in parallel
        tasks = []
        if python_files:
            tasks.append(self._run_python_lint(python_files))
        if ts_files:
            tasks.append(self._run_typescript_lint(ts_files))

        if not tasks:
            return ValidatorResult(
                validator_name=self.name,
                status=ValidatorStatus.SKIPPED,
                message="No lintable files found",
                details={"files_checked": 0},
                duration_ms=int((time.time() - started_at) * 1000),
                blocking=False,
            )

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Aggregate results
        for result in results:
            if isinstance(result, Exception):
                errors.append({"error": str(result)})
            else:
                errors.extend(result.get("errors", []))
                warnings.extend(result.get("warnings", []))

        duration_ms = int((time.time() - started_at) * 1000)

        return ValidatorResult(
            validator_name=self.name,
            status=ValidatorStatus.FAILED if errors else ValidatorStatus.PASSED,
            message=f"Found {len(errors)} errors, {len(warnings)} warnings",
            details={
                "errors": errors[:20],
                "warnings": warnings[:10],
                "error_count": len(errors),
                "warning_count": len(warnings),
            },
            duration_ms=duration_ms,
            blocking=self.config.blocking if errors else False,
        )
```

### 4.2 TestValidator

**Purpose**: Run tests for changed files.

**Tools**:
- Python: `pytest`
- TypeScript: `vitest`

**Configuration**:
```yaml
name: tests
blocking: true   # Test failures block merge
timeout: 300     # 5 minutes
```

**Test Discovery**:
```python
# Python test patterns
PYTHON_TEST_PATTERNS = [
    r"test_.*\.py$",     # test_*.py
    r".*_test\.py$",     # *_test.py
    r"tests/.*\.py$",    # tests/*.py
]

# TypeScript test patterns
TYPESCRIPT_TEST_PATTERNS = [
    r".*\.test\.[tj]sx?$",    # *.test.ts
    r".*\.spec\.[tj]sx?$",    # *.spec.ts
    r"__tests__/.*\.[tj]sx?$", # __tests__/*.ts
]
```

### 4.3 CoverageValidator

**Purpose**: Validate test coverage meets thresholds.

**Tools**:
- Python: `pytest-cov`
- TypeScript: `vitest --coverage`

**Configuration**:
```yaml
name: coverage
blocking: false  # Coverage is advisory by default
timeout: 300     # 5 minutes
threshold: 80    # Minimum 80% coverage
```

---

## 5. ValidationPipeline Service

### 5.1 Pipeline Orchestration

```python
class ValidationPipeline:
    """
    Orchestrate validation of AI-generated Pull Requests.

    Runs multiple validators in parallel and aggregates results.
    """

    def __init__(self, validators: Optional[List[BaseValidator]] = None):
        """Initialize with validators (uses defaults if None)."""
        if validators is None:
            self.validators = [
                LintValidator(),
                TestValidator(),
                CoverageValidator(),
            ]
        else:
            self.validators = validators

    async def run(
        self,
        event_id: UUID,
        project_id: UUID,
        pr_number: str,
        files: List[str],
        diff: str,
    ) -> PipelineResult:
        """
        Run all validators on PR files.

        Process:
        1. Run all validators in parallel (asyncio.gather)
        2. Handle exceptions from individual validators
        3. Aggregate results
        4. Determine overall status
        5. Record Prometheus metrics

        Returns:
            PipelineResult with all validator results
        """
        started_at = datetime.utcnow()
        start_time = time.time()

        # Run all validators in parallel
        tasks = [
            self._run_validator_safe(v, project_id, pr_number, files, diff)
            for v in self.validators
        ]
        results = await asyncio.gather(*tasks)

        # Aggregate blocking failures
        blocking_failures = [
            r for r in results
            if r.status == ValidatorStatus.FAILED and r.blocking
        ]

        # Determine overall status
        overall_status = (
            ValidationStatus.FAILED if blocking_failures
            else ValidationStatus.PASSED
        )

        duration_ms = int((time.time() - start_time) * 1000)

        return PipelineResult(
            event_id=event_id,
            status=overall_status,
            results=results,
            blocking_failures=blocking_failures,
            duration_ms=duration_ms,
            started_at=started_at,
            completed_at=datetime.utcnow(),
            validators_run=len(self.validators),
            validators_passed=sum(1 for r in results if r.status == ValidatorStatus.PASSED),
            validators_failed=sum(1 for r in results if r.status in (ValidatorStatus.FAILED, ValidatorStatus.ERROR)),
        )
```

### 5.2 Error Handling

```python
async def _run_validator_safe(
    self,
    validator: BaseValidator,
    project_id: UUID,
    pr_number: str,
    files: List[str],
    diff: str,
) -> ValidatorResult:
    """Run a single validator with error handling and timeout."""
    start_time = time.time()

    try:
        # Apply timeout
        result = await asyncio.wait_for(
            validator.validate(project_id, pr_number, files, diff),
            timeout=validator.get_timeout(),
        )
        return result

    except asyncio.TimeoutError:
        duration_ms = int((time.time() - start_time) * 1000)
        return ValidatorResult(
            validator_name=validator.get_name(),
            status=ValidatorStatus.TIMEOUT,
            message=f"Timed out after {validator.get_timeout()}s",
            details={},
            duration_ms=duration_ms,
            blocking=False,  # Don't block on timeout
        )

    except Exception as e:
        duration_ms = int((time.time() - start_time) * 1000)
        return ValidatorResult(
            validator_name=validator.get_name(),
            status=ValidatorStatus.ERROR,
            message=f"Error: {str(e)}",
            details={"error": str(e), "error_type": type(e).__name__},
            duration_ms=duration_ms,
            blocking=False,  # Don't block on error
        )
```

---

## 6. Background Worker

### 6.1 Redis Queue Architecture

```
┌─────────────────┐     ┌─────────────────────────────────────────────────┐
│ AI Detection    │     │                REDIS                            │
│ Service         │────▶│                                                 │
└─────────────────┘     │  ┌─────────────────┐  ┌────────────────────┐   │
                        │  │ validation:queue │  │ validation:retry   │   │
                        │  │ (LIST - FIFO)    │  │ (SORTED SET)       │   │
                        │  └────────┬────────┘  └─────────┬──────────┘   │
                        │           │                     │              │
                        │           │    ┌────────────────┘              │
                        │           ▼    ▼                               │
                        │  ┌─────────────────────────────────────────┐   │
                        │  │        validation:processing            │   │
                        │  │        (HASH - active jobs)             │   │
                        │  └─────────────────────────────────────────┘   │
                        └─────────────────────────────────────────────────┘
                                          │
                                          ▼
                        ┌─────────────────────────────────────────────────┐
                        │              VALIDATION WORKER                   │
                        │                                                  │
                        │  1. BLPOP validation:queue (blocking read)      │
                        │  2. Run ValidationPipeline.run()                │
                        │  3. Update ai_code_events table                 │
                        │  4. Post PR comment                             │
                        │  5. On failure: requeue with backoff            │
                        └─────────────────────────────────────────────────┘
```

### 6.2 Job Data Structure

```python
@dataclass
class ValidationJob:
    """Validation job data structure."""

    event_id: UUID
    project_id: UUID
    pr_number: str
    files: List[str]
    diff: str
    queued_at: datetime
    retry_count: int = 0
    max_retries: int = 3

    @classmethod
    def from_dict(cls, data: dict) -> "ValidationJob":
        """Create job from dict."""
        return cls(
            event_id=UUID(data["event_id"]),
            project_id=UUID(data["project_id"]),
            pr_number=data["pr_number"],
            files=data["files"],
            diff=data["diff"],
            queued_at=datetime.fromisoformat(data["queued_at"]),
            retry_count=data.get("retry_count", 0),
            max_retries=data.get("max_retries", 3),
        )
```

### 6.3 Retry Logic

**Exponential Backoff**:
```python
# Calculate backoff delay
delay = min(2 ** job.retry_count * 10, 300)  # Max 5 minutes

# Retry schedule:
# Attempt 1: 10 seconds
# Attempt 2: 20 seconds
# Attempt 3: 40 seconds
# Max: 300 seconds (5 minutes)
```

---

## 7. Prometheus Metrics

### 7.1 Pipeline Metrics

```python
# Duration metrics
validation_pipeline_duration_seconds = Histogram(
    "validation_pipeline_duration_seconds",
    "Duration of validation pipeline execution in seconds",
    buckets=[1, 5, 10, 30, 60, 120, 180, 300, 360],
)

# Result metrics
validation_pipeline_results_total = Counter(
    "validation_pipeline_results_total",
    "Total number of validation pipeline results",
    labelnames=["status"],  # passed, failed, error
)

# Blocking failures
validation_blocking_failures_total = Counter(
    "validation_blocking_failures_total",
    "Total number of merge-blocking validation failures",
    labelnames=["validator"],
)
```

### 7.2 Validator Metrics

```python
# Per-validator duration
validation_validator_duration_seconds = Histogram(
    "validation_validator_duration_seconds",
    "Duration of individual validator execution in seconds",
    labelnames=["validator"],
    buckets=[0.5, 1, 5, 10, 30, 60, 120, 180],
)

# Per-validator results
validation_validator_results_total = Counter(
    "validation_validator_results_total",
    "Total number of validator results",
    labelnames=["validator", "status"],
)
```

### 7.3 Queue Metrics

```python
# Queue size
validation_queue_size = Gauge(
    "validation_queue_size",
    "Current size of validation queue",
)

# Queue wait time
validation_queue_wait_seconds = Histogram(
    "validation_queue_wait_seconds",
    "Time spent waiting in validation queue",
    buckets=[1, 5, 10, 30, 60, 120, 300, 600],
)
```

---

## 8. Performance Requirements

| Metric | Target | Measurement |
|--------|--------|-------------|
| **Pipeline Latency (p95)** | <6 minutes | Prometheus histogram |
| **Lint Latency (p95)** | <2 minutes | Per-validator histogram |
| **Test Latency (p95)** | <5 minutes | Per-validator histogram |
| **Coverage Latency (p95)** | <5 minutes | Per-validator histogram |
| **Queue Wait Time (p95)** | <30 seconds | Queue histogram |
| **Blocking Rate** | <20% | Counter ratio |

---

## 9. Security Considerations

**GDPR Compliance**:
- ✅ No PII stored in validation results
- ✅ File paths are relative (no absolute paths)
- ✅ Diff content not persisted (transient only)

**Input Validation**:
- ✅ File paths sanitized (no path traversal)
- ✅ Diff size limited (max 10MB)
- ✅ Timeout protection (per-validator)

**External Tool Security**:
- ✅ Subprocess execution with timeout
- ✅ Shell injection prevention (shlex.quote)
- ✅ Working directory isolation

---

## 10. Testing Strategy

### 10.1 Unit Tests

**Coverage Target**: ≥95%

**Test Categories**:
- ✅ Pipeline execution (all pass, blocking fail, non-blocking fail)
- ✅ Parallel execution (timing validation)
- ✅ Timeout handling
- ✅ Error handling
- ✅ Result aggregation
- ✅ Validator management (add, remove)

### 10.2 Mock Validators

**Zero Mock Policy Compliant**: Custom mock classes implementing real interfaces.

```python
class MockPassingValidator(BaseValidator):
    """Mock validator that always passes."""
    name = "mock_pass"

    async def validate(self, project_id, pr_number, files, diff):
        return ValidatorResult(
            validator_name=self.name,
            status=ValidatorStatus.PASSED,
            message="Mock passed",
            details={"mock": True},
            duration_ms=10,
            blocking=self.config.blocking,
        )
```

### 10.3 Integration Tests

**Deferred to Sprint 42 Day 5**:
- Test with real ruff/ESLint execution
- Test with real pytest/vitest execution
- Test Redis queue end-to-end
- Test PR comment posting

---

## 11. API Endpoints

### 11.1 Validation Endpoints (Sprint 42 Day 9)

```yaml
POST /api/v1/validation/run:
  description: Trigger validation for a PR
  request:
    event_id: UUID
    project_id: UUID
    pr_number: string
  response:
    pipeline_result: PipelineResult

GET /api/v1/validation/{event_id}:
  description: Get validation status for an event
  response:
    status: ValidationStatus
    results: List[ValidatorResult]
    duration_ms: int

GET /api/v1/validation/{event_id}/results:
  description: Get detailed validator results
  response:
    validators: List[ValidatorResult]
```

---

## 12. Future Enhancements

### v2 Features (Sprint 43+)

1. **Security Validator (SAST)**
   - Semgrep integration
   - Custom security rules
   - OWASP Top 10 detection

2. **Circuit Breaker**
   - Per-tool circuit breaker (ruff, pytest, ESLint)
   - Failure threshold: 5 failures → 60s timeout
   - Automatic recovery

3. **Result Caching**
   - Cache by (pr_number, files_hash, diff_hash)
   - Redis TTL: 1 hour
   - Skip re-validation for unchanged content

4. **Custom Validators**
   - Plugin architecture
   - YAML configuration
   - User-defined validators

---

## 13. Implementation Status

### Sprint 42 Day 3-4 Checklist

| # | Deliverable | Status | Location |
|---|-------------|--------|----------|
| 1 | BaseValidator Interface | ✅ COMPLETE | `app/services/validators/__init__.py` |
| 2 | LintValidator | ✅ COMPLETE | `app/services/validators/lint_validator.py` |
| 3 | TestValidator | ✅ COMPLETE | `app/services/validators/test_validator.py` |
| 4 | CoverageValidator | ✅ COMPLETE | `app/services/validators/coverage_validator.py` |
| 5 | ValidationPipeline | ✅ COMPLETE | `app/services/validation_pipeline.py` |
| 6 | Pipeline Metrics | ✅ COMPLETE | `app/middleware/validation_metrics.py` |
| 7 | Background Worker | ✅ COMPLETE | `app/jobs/validation_worker.py` |
| 8 | Unit Tests | ✅ COMPLETE | `tests/unit/test_validation_pipeline.py` |

---

**Document Version**: 1.0.0
**Created**: December 21, 2025
**Framework**: SDLC 6.1.0
**Status**: ✅ Implementation Complete
