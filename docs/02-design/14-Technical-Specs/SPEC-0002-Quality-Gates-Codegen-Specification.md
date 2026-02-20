# Quality Gates for Generated Code Specification

---
spec_id: SPEC-0002
version: 1.0.0
title: Quality Gates for Generated Code Specification
status: APPROVED
tier: PROFESSIONAL
stage: "04"
category: technical
created_date: 2025-12-23
last_updated: 2026-01-28
owner: Backend Lead
reviewers:
  - QA Lead
  - Tech Lead
approver: CTO
related_adrs:
  - ADR-040-App-Builder-OpenSpec-Integration
related_specs:
  - SPEC-0001-Governance-System-Implementation
framework_version: 6.0.5
tags:
  - codegen
  - quality-gates
  - validation
  - semgrep
  - ollama
  - ep-06
---

## 1. Overview

### 1.1 Purpose

This specification defines the 4-gate quality validation pipeline that ensures all AI-generated code meets production standards before delivery to users, targeting 95%+ pass rate for the Founder Plan.

### 1.2 Context

**Business Problem**: Generated code must be production-ready without manual QA. Need automated validation pipeline that catches syntax errors, security vulnerabilities, architecture violations, and test failures.

**Solution**: 4-gate sequential pipeline:
1. **Gate 1**: Syntax validation (Python/TypeScript/YAML)
2. **Gate 2**: Security validation (Semgrep OWASP rules)
3. **Gate 3**: Architecture validation (layer dependencies, circular imports)
4. **Gate 4**: Test execution (run generated tests)

If any gate fails, return detailed Vietnamese error messages with fix suggestions.

### 1.3 Goals

- **Primary**: 95%+ pass rate for generated code
- **Secondary**: <3s total validation latency (p95)
- **Tertiary**: <$50/month infrastructure cost per project

### 1.4 Scope

| In Scope | Out of Scope |
|----------|--------------|
| 4 validation gates (syntax/security/arch/tests) | Runtime performance testing |
| Vietnamese error messages | Load testing |
| Auto-fix suggestions | Security penetration testing |
| Ollama optimization for cost | External API integrations |
| Cost tracking per project | Manual code review |

---

## 2. Context & Background

### 2.1 Problem Statement

**Current State** (Sprint 46-47):
- Intent Router (IR) generates project blueprints
- Templates produce code from blueprints
- No validation before delivery to user
- Users discover errors during first run (bad UX)

**Desired State** (Sprint 48):
- Every generation runs through 4 quality gates
- Errors caught before delivery with Vietnamese messages
- Auto-fix suggestions provided
- 95%+ pass rate (5% may need retry with different provider)

### 2.2 Stakeholders

| Role | Needs | Success Criteria |
|------|-------|------------------|
| Developers | Fast feedback, actionable errors | <3s validation, Vietnamese messages |
| QA Lead | Automated quality enforcement | 95%+ pass rate, zero critical bugs |
| Backend Lead | Cost-effective validation | <$50/month per project |
| CEO | Production-ready code | Zero manual QA needed |

### 2.3 Related Documents

- [ADR-040: App Builder OpenSpec Integration](../03-ADRs/ADR-040-App-Builder-OpenSpec-Integration.md)
- [Sprint 46-47: IR Processors + Templates](../14-Technical-Specs/)
- [SPEC-0001: Governance System Implementation](SPEC-0001-Governance-System-Implementation.md)

---

## 3. Requirements

### 3.1 Functional Requirements

#### FR-01: Syntax Validation (Gate 1)

**GIVEN** generated code files (Python/TypeScript/YAML)  
**WHEN** Gate 1 (syntax validation) executes  
**THEN** the system SHALL parse each file with language-specific parser (AST for Python, tsc for TypeScript, yaml.safe_load for YAML)  
**AND** the system SHALL return SyntaxValidationResult with:
- passed: true/false
- issues: List[SyntaxIssue] with file, line, column, message, vietnamese_message
- files_checked: int
- files_passed: int  
**AND** the system SHALL complete within 1s (p95)

**Tier Requirements**:
- LITE: Python syntax only
- STANDARD: Python + JavaScript syntax
- PROFESSIONAL: Python + TypeScript + YAML
- ENTERPRISE: All languages + custom validators

**Vietnamese Error Translations**:
- "invalid syntax" → "Cú pháp không hợp lệ"
- "unexpected indent" → "Thụt lề không đúng"
- "expected an indented block" → "Thiếu khối thụt lề"
- "unexpected EOF" → "Kết thúc file không mong đợi"

#### FR-02: Security Validation (Gate 2)

**GIVEN** generated code passed Gate 1 (syntax valid)  
**WHEN** Gate 2 (security validation) executes  
**THEN** the system SHALL run Semgrep with OWASP rules  
**AND** the system SHALL detect:
- SQL injection vulnerabilities
- XSS vulnerabilities
- Hardcoded secrets
- Command injection
- Path traversal
- Insecure randomness  
**AND** the system SHALL return SecurityValidationResult with:
- passed: true (if critical=0 AND high=0)
- issues: List[SecurityIssue] with severity (critical/high/medium/low)
- critical_count, high_count, medium_count, low_count  
**AND** the system SHALL complete within 60s timeout

**Tier Requirements**:
- LITE: Not applicable (no security validation)
- STANDARD: Basic Semgrep rules (SQL injection, XSS)
- PROFESSIONAL: Full OWASP rules
- ENTERPRISE: Full + custom security rules

**Vietnamese Security Translations**:
- "sql-injection" → "Lỗ hổng SQL Injection - Dữ liệu người dùng không được escape"
- "xss" → "Lỗ hổng XSS - Output không được sanitize"
- "hardcoded-secret" → "Secret được hardcode - Nên dùng biến môi trường"

#### FR-03: Architecture Validation (Gate 3)

**GIVEN** generated code passed Gate 1-2  
**WHEN** Gate 3 (architecture validation) executes  
**THEN** the system SHALL validate:
- Layer dependency rules (e.g., api/routes can import services/schemas/core/models, but services cannot import api)
- Circular import detection
- Naming conventions (snake_case files, PascalCase classes)  
**AND** the system SHALL return ArchitectureValidationResult with:
- passed: true/false
- issues: List[ArchitectureIssue] with file, line, rule, message, vietnamese_message  
**AND** the system SHALL complete within 1s (p95)

**Tier Requirements**:
- LITE: No architecture validation
- STANDARD: Layer dependency rules only
- PROFESSIONAL: Full validation (layer deps + circular imports + naming)
- ENTERPRISE: Full + custom architecture rules

**Layer Dependency Rules**:
```
api/routes → [services, schemas, core, models]
services → [models, schemas, core]
models → [core]
schemas → [core]
core → []
```

#### FR-04: Test Execution (Gate 4)

**GIVEN** generated code passed Gate 1-3  
**WHEN** Gate 4 (test execution) executes  
**THEN** the system SHALL:
- Create temporary project directory
- Write all generated files
- Create minimal pytest config
- Run pytest with --tb=short and 120s timeout
- Parse pytest output to extract test results  
**AND** the system SHALL return TestValidationResult with:
- passed: true (if tests_failed=0)
- tests_run, tests_passed, tests_failed
- results: List[TestResult] with test_name, passed, error_message  
**AND** the system SHALL complete within 120s timeout

**Tier Requirements**:
- LITE: No test execution
- STANDARD: Run tests, no coverage requirement
- PROFESSIONAL: Run tests + 80% coverage requirement
- ENTERPRISE: Run tests + 90% coverage + mutation testing

#### FR-05: Gate Pipeline Orchestration

**GIVEN** generated code is ready for validation  
**WHEN** QualityGatePipeline.run() is called  
**THEN** the system SHALL:
- Run Gate 1 (syntax) first
- If Gate 1 fails, skip remaining gates
- If Gate 1 passes, run Gate 2 (security)
- Run Gate 3 (architecture)
- Run Gate 4 (tests)
- Return PipelineResult with:
  - passed: true (if ALL gates pass)
  - total_duration_ms
  - gates: List[GateResult] with gate_name, passed, duration_ms, details
  - vietnamese_summary: "✅ Tất cả các gate đều PASS" or "❌ Các gate sau FAIL: ..."  
**AND** the system SHALL complete within 3s total (p95)

**Tier Requirements**:
- LITE: Gate 1 only (syntax)
- STANDARD: Gate 1 + Gate 2 (syntax + security)
- PROFESSIONAL: All 4 gates
- ENTERPRISE: All 4 gates + custom gates

#### FR-06: Ollama Optimization

**GIVEN** code generation uses Ollama for LLM tasks  
**WHEN** OllamaOptimizer optimizes prompts  
**THEN** the system SHALL:
- Use optimized prompt templates (shorter, Vietnamese-first)
- Cache responses with 1-hour TTL
- Estimate token count before sending
- Fallback to template if Ollama unavailable  
**AND** the system SHALL reduce generation cost to $0.001 per 1K tokens (self-hosted)

**Tier Requirements**:
- LITE: Template-only (no LLM)
- STANDARD: Ollama with caching
- PROFESSIONAL: Ollama + Claude fallback
- ENTERPRISE: Multi-provider optimization

#### FR-07: Cost Tracking

**GIVEN** projects use code generation  
**WHEN** cost tracking is enabled  
**THEN** the system SHALL:
- Track usage per project (provider, tokens, cost_usd, generation_time_ms)
- Store in codegen_usage table
- Provide get_project_usage(project_id, period_days) API
- Calculate totals: total_tokens, total_cost_usd, total_requests, avg_latency_ms  
**AND** the system SHALL target <$50/month per project

**Tier Requirements**:
- LITE: Not applicable
- STANDARD: Basic cost tracking
- PROFESSIONAL: Full cost tracking + alerts
- ENTERPRISE: Full + budget enforcement

### 3.2 Non-Functional Requirements

#### NFR-01: Performance

**GIVEN** quality gates are running  
**WHEN** performance is measured  
**THEN** the system SHALL meet:
- Gate 1 (syntax): <1s (p95)
- Gate 2 (security): <60s timeout
- Gate 3 (architecture): <1s (p95)
- Gate 4 (tests): <120s timeout
- Total pipeline: <3s (p95, excluding test execution)

#### NFR-02: Accuracy

**GIVEN** quality gates validate code  
**WHEN** accuracy is measured  
**THEN** the system SHALL achieve:
- Pass rate: ≥95%
- False positive rate: <5%
- False negative rate: <2%

#### NFR-03: Cost Efficiency

**GIVEN** Ollama is used for code generation  
**WHEN** cost is measured per project over 30 days  
**THEN** the system SHALL stay under $50/month including:
- Ollama self-hosted compute
- Semgrep execution
- Test execution compute

---

## 4. Design Decisions

### 4.1 Sequential Gate Execution

**Decision**: Run gates sequentially, stop on first failure  
**Rationale**: No need to run security/arch/tests if syntax is invalid  
**Trade-offs**: Slightly slower than parallel, but clearer error reporting  
**Alternatives Considered**:
- Option B: Parallel execution → Faster but confusing when multiple gates fail

### 4.2 Vietnamese-First Error Messages

**Decision**: All error messages include vietnamese_message field  
**Rationale**: Target users are Vietnamese developers  
**Trade-offs**: Translation maintenance burden  
**Implementation**: Static translation map + fallback to English

### 4.3 Ollama for Cost Optimization

**Decision**: Use self-hosted Ollama instead of Claude API  
**Rationale**: Cost $0.001/1K tokens vs Claude $0.015/1K tokens (15x cheaper)  
**Trade-offs**: Slower (15s vs 2s), but acceptable for non-interactive generation

### 4.4 Semgrep for Security

**Decision**: Use Semgrep with OWASP rules instead of custom static analysis  
**Rationale**: Industry-standard tool, well-maintained rules, JSON output  
**Trade-offs**: 60s timeout may be slow for large projects

---

## 5. Technical Specification

### 5.1 Service Architecture

```
Generated Code
      │
      ▼
┌─────────────────────────────────────────┐
│   QualityGatePipeline                   │
│                                         │
│   ┌─────────────────────────────────┐   │
│   │ Gate 1: SyntaxValidator         │   │
│   │ - Python AST, TypeScript tsc    │   │
│   │ - YAML safe_load                │   │
│   └─────────────────────────────────┘   │
│              │ PASS                     │
│              ▼                           │
│   ┌─────────────────────────────────┐   │
│   │ Gate 2: SecurityValidator       │   │
│   │ - Semgrep OWASP rules           │   │
│   │ - Severity classification       │   │
│   └─────────────────────────────────┘   │
│              │ PASS                     │
│              ▼                           │
│   ┌─────────────────────────────────┐   │
│   │ Gate 3: ArchitectureValidator   │   │
│   │ - Layer deps, circular imports  │   │
│   │ - Naming conventions            │   │
│   └─────────────────────────────────┘   │
│              │ PASS                     │
│              ▼                           │
│   ┌─────────────────────────────────┐   │
│   │ Gate 4: TestValidator           │   │
│   │ - Pytest execution              │   │
│   │ - Result parsing                │   │
│   └─────────────────────────────────┘   │
│              │ PASS                     │
└──────────────┼──────────────────────────┘
               ▼
         Validated Code
```

### 5.2 Service Specifications

#### 5.2.1 SyntaxValidator

**Location**: `backend/app/services/codegen/validators/syntax_validator.py`

**Interface**:
```python
class SyntaxIssue(BaseModel):
    file: str
    line: int
    column: int
    message: str
    vietnamese_message: str

class SyntaxValidationResult(BaseModel):
    passed: bool
    issues: List[SyntaxIssue]
    files_checked: int
    files_passed: int

class SyntaxValidator:
    ERROR_TRANSLATIONS: Dict[str, str]
    
    def validate(self, files: List[Dict[str, str]]) -> SyntaxValidationResult
    def _validate_file(self, file: Dict) -> List[SyntaxIssue]
    def _validate_python(self, path: str, content: str) -> List[SyntaxIssue]
    def _validate_typescript(self, path: str, content: str) -> List[SyntaxIssue]
    def _validate_yaml(self, path: str, content: str) -> List[SyntaxIssue]
    def _translate_error(self, message: str) -> str
```

#### 5.2.2 SecurityValidator

**Location**: `backend/app/services/codegen/validators/security_validator.py`

**Interface**:
```python
class SecurityIssue(BaseModel):
    file: str
    line: int
    rule_id: str
    severity: str  # critical, high, medium, low
    message: str
    vietnamese_message: str
    fix_suggestion: str | None

class SecurityValidationResult(BaseModel):
    passed: bool
    issues: List[SecurityIssue]
    critical_count: int
    high_count: int
    medium_count: int
    low_count: int

class SecurityValidator:
    SECURITY_TRANSLATIONS: Dict[str, str]
    SEMGREP_RULES: str  # YAML rules for Semgrep
    
    def validate(self, files: List[Dict[str, str]]) -> SecurityValidationResult
    def _parse_finding(self, finding: Dict) -> SecurityIssue
    def _translate_issue(self, rule_id: str) -> str
```

#### 5.2.3 ArchitectureValidator

**Location**: `backend/app/services/codegen/validators/architecture_validator.py`

**Interface**:
```python
class ArchitectureIssue(BaseModel):
    file: str
    line: int | None
    rule: str
    message: str
    vietnamese_message: str

class ArchitectureValidationResult(BaseModel):
    passed: bool
    issues: List[ArchitectureIssue]

class ArchitectureValidator:
    LAYER_RULES: Dict[str, List[str]]
    
    def validate(self, files: List[Dict[str, str]]) -> ArchitectureValidationResult
    def _check_layer_deps(self, file: Dict) -> List[ArchitectureIssue]
    def _check_circular_imports(self, file: Dict, file_map: Dict) -> List[ArchitectureIssue]
    def _check_naming(self, file: Dict) -> List[ArchitectureIssue]
```

#### 5.2.4 TestValidator

**Location**: `backend/app/services/codegen/validators/test_validator.py`

**Interface**:
```python
class TestResult(BaseModel):
    test_name: str
    passed: bool
    error_message: str | None

class TestValidationResult(BaseModel):
    passed: bool
    tests_run: int
    tests_passed: int
    tests_failed: int
    results: List[TestResult]

class TestValidator:
    def validate(
        self,
        files: List[Dict[str, str]],
        blueprint: Dict[str, Any]
    ) -> TestValidationResult
    
    def _extract_error(self, output: str, test_name: str) -> str | None
```

#### 5.2.5 QualityGatePipeline

**Location**: `backend/app/services/codegen/validators/gate_pipeline.py`

**Interface**:
```python
class GateResult(BaseModel):
    gate_name: str
    passed: bool
    duration_ms: int
    details: Dict[str, Any]

class PipelineResult(BaseModel):
    passed: bool
    total_duration_ms: int
    gates: List[GateResult]
    summary: Dict[str, Any]
    vietnamese_summary: str

class QualityGatePipeline:
    def run(
        self,
        files: List[Dict[str, str]],
        blueprint: Dict[str, Any]
    ) -> PipelineResult
    
    def _run_gate(self, name: str, validator_fn) -> GateResult
    def _build_result(self, gates: List[GateResult], start_time: float) -> PipelineResult
```

#### 5.2.6 OllamaOptimizer

**Location**: `backend/app/services/codegen/ollama_optimizer.py`

**Interface**:
```python
class OllamaOptimizer:
    OPTIMIZED_PROMPTS: Dict[str, str]
    
    def optimize_prompt(self, prompt_type: str, context: Dict) -> str
    def get_cache_key(self, prompt: str, model: str) -> str
    def get_cached(self, cache_key: str) -> str | None
    def set_cached(self, cache_key: str, response: str) -> None
    def estimate_tokens(self, text: str) -> int
    def should_use_ollama(self, estimated_tokens: int) -> bool
```

#### 5.2.7 CostTracker

**Location**: `backend/app/services/codegen/cost_tracker.py`

**Interface**:
```python
class CostEstimate(BaseModel):
    provider: str
    tokens: int
    cost_usd: float

class CostTracker:
    COST_PER_1K: Dict[str, float]
    
    async def track_usage(
        self,
        db: AsyncSession,
        project_id: str,
        user_id: str,
        provider: str,
        tokens: int,
        generation_time_ms: int
    ) -> None
    
    async def get_project_usage(
        self,
        db: AsyncSession,
        project_id: str,
        period_days: int = 30
    ) -> Dict[str, Any]
```

### 5.3 Database Schema

**New Table**: `codegen_usage`

```sql
CREATE TABLE codegen_usage (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    project_id VARCHAR(50) NOT NULL,
    user_id VARCHAR(50) NOT NULL,
    provider VARCHAR(20) NOT NULL,  -- ollama, claude, gpt4
    tokens_used INTEGER NOT NULL,
    cost_usd DECIMAL(10, 4) NOT NULL,
    generation_time_ms INTEGER NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    INDEX idx_project_created (project_id, created_at),
    INDEX idx_user_created (user_id, created_at)
);
```

### 5.4 API Specification

**Base Path**: `/api/v1/codegen`

**Key Endpoints**:

```yaml
/validate:
  post:
    summary: Run quality gate pipeline
    requestBody:
      content:
        application/json:
          schema:
            type: object
            properties:
              files:
                type: array
                items:
                  type: object
                  properties:
                    path: string
                    content: string
                    language: string
              blueprint:
                type: object
    responses:
      200:
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/PipelineResult'

/optimize-prompt:
  post:
    summary: Optimize prompt for Ollama
    requestBody:
      content:
        application/json:
          schema:
            type: object
            properties:
              prompt_type: string
              context: object
    responses:
      200:
        content:
          application/json:
            schema:
              type: object
              properties:
                optimized_prompt: string

/cost/project/{project_id}:
  get:
    summary: Get project usage summary
    parameters:
      - name: project_id
        in: path
        required: true
      - name: period_days
        in: query
        schema:
          type: integer
          default: 30
    responses:
      200:
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/ProjectUsage'
```

---

## 6. Acceptance Criteria

| ID | Criterion | Test Method | Status |
|----|-----------|-------------|--------|
| AC-01 | Gate 1 (syntax) completes <1s (p95) | pytest-benchmark | ⏳ TODO |
| AC-02 | Gate 2 (security) detects hardcoded secrets | Unit test | ⏳ TODO |
| AC-03 | Gate 2 (security) detects SQL injection | Unit test | ⏳ TODO |
| AC-04 | Gate 3 (architecture) detects layer violations | Unit test | ⏳ TODO |
| AC-05 | Gate 3 (architecture) detects circular imports | Unit test | ⏳ TODO |
| AC-06 | Gate 4 (tests) runs pytest and parses results | Integration test | ⏳ TODO |
| AC-07 | Pipeline stops on first failure | Integration test | ⏳ TODO |
| AC-08 | Vietnamese error messages returned | Unit test | ⏳ TODO |
| AC-09 | Ollama caching reduces redundant calls | Integration test | ⏳ TODO |
| AC-10 | Cost tracking stores usage in database | Integration test | ⏳ TODO |
| AC-11 | Total pipeline <3s (p95, excluding tests) | pytest-benchmark | ⏳ TODO |
| AC-12 | Pass rate ≥95% on real projects | Production metrics | ⏳ TODO |

**Test Coverage Target**: 90%+ for all validators

---

## 7. Spec Delta

### 7.1 Changes from Previous Version

This is the initial version (1.0.0) migrated from SDLC 6.1.0 format to Framework 6.0.5 format.

**Migration Changes**:
- Added YAML frontmatter with spec_id, tier, stage, relationships
- Converted requirements to BDD format (GIVEN-WHEN-THEN)
- Added tier-specific requirements (LITE/STANDARD/PROFESSIONAL/ENTERPRISE)
- Added acceptance criteria table with test methods
- Reorganized content to match 9-section Framework 6.0.5 template
- Added relationship to SPEC-0001 (Governance System)

**Content Updates**:
- None (content preserved from original spec created Dec 23, 2025)

### 7.2 Version History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0.0 | 2026-01-28 | Backend Lead | Initial version (migrated to Framework 6.0.5) |
| 0.9.0 | 2025-12-23 | Backend Lead + QA Lead | Original spec in SDLC 6.1.0 format |

---

## 8. Dependencies

### 8.1 Upstream Dependencies

| Dependency | Type | Impact if Changed |
|------------|------|-------------------|
| Sprint 46-47 IR/Templates | Implementation | Blueprint format changes require validator updates |
| Semgrep | External Tool | Version upgrades may change rule syntax |
| Ollama | AI Service | Model changes may affect prompt optimization |
| pytest | Testing Tool | API changes require TestValidator updates |

### 8.2 Downstream Dependencies

| Dependent | Type | Impact |
|-----------|------|--------|
| App Builder | Feature | Uses QualityGatePipeline for all generations |
| EP-06 Codegen | Feature | Validates generated projects before delivery |
| Founder Plan | Business | Pass rate affects user satisfaction |

### 8.3 Related Specifications

- [SPEC-0001: Governance System Implementation](SPEC-0001-Governance-System-Implementation.md): Uses quality gates for governance approval
- [ADR-040: App Builder OpenSpec Integration](../03-ADRs/ADR-040-App-Builder-OpenSpec-Integration.md): Generates SDLC 6.1.0 specs validated by this pipeline

---

## 9. Appendix

### 9.1 Sprint 48 Implementation Checklist

**Week 1 (Feb 17-21)**:
- [ ] Day 1: Implement SyntaxValidator (Python + TypeScript + YAML)
- [ ] Day 2: Implement SecurityValidator (Semgrep integration)
- [ ] Day 3: Implement ArchitectureValidator (layer rules + circular imports)
- [ ] Day 4: Create QualityGatePipeline orchestrator
- [ ] Day 5: Write unit tests for each validator (90%+ coverage)

**Week 2 (Feb 24-28)**:
- [ ] Day 1: Implement TestValidator (pytest execution)
- [ ] Day 2: Implement OllamaOptimizer (caching + prompt optimization)
- [ ] Day 3: Implement CostTracker (database persistence)
- [ ] Day 4: Integration test full pipeline
- [ ] Day 5: Performance optimization to meet <3s target

### 9.2 Vietnamese Error Translation Map

**Syntax Errors**:
- "invalid syntax" → "Cú pháp không hợp lệ"
- "unexpected indent" → "Thụt lề không đúng"
- "expected an indented block" → "Thiếu khối thụt lề"
- "unexpected EOF" → "Kết thúc file không mong đợi"
- "name '{}' is not defined" → "Tên '{}' chưa được định nghĩa"

**Security Issues**:
- "sql-injection" → "Lỗ hổng SQL Injection - Dữ liệu người dùng không được escape"
- "xss" → "Lỗ hổng XSS - Output không được sanitize"
- "hardcoded-secret" → "Secret được hardcode - Nên dùng biến môi trường"
- "insecure-random" → "Sử dụng random không an toàn - Dùng secrets module"
- "path-traversal" → "Lỗ hổng Path Traversal - Đường dẫn file không được validate"
- "command-injection" → "Lỗ hổng Command Injection - Input không được sanitize"

**Architecture Issues**:
- Layer violation → "Tầng '{current_layer}' không nên import từ '{target_layer}'"
- Circular import → "Có thể xảy ra import vòng với {module}"
- Naming convention → "File model nên dùng snake_case: {filename}"

### 9.3 Semgrep Rules Configuration

**Rules File**: `backend/app/services/codegen/validators/semgrep_rules.yaml`

```yaml
rules:
  - id: hardcoded-secret
    pattern-either:
      - pattern: password = "..."
      - pattern: api_key = "..."
      - pattern: secret = "..."
    message: "Hardcoded secret detected"
    severity: ERROR
    languages: [python]

  - id: sql-injection
    pattern: |
      $CURSOR.execute($QUERY % ...)
    message: "Potential SQL injection"
    severity: ERROR
    languages: [python]

  - id: eval-usage
    pattern: eval(...)
    message: "Dangerous eval() usage"
    severity: ERROR
    languages: [python]

  - id: shell-injection
    pattern-either:
      - pattern: os.system($CMD)
      - pattern: subprocess.call($CMD, shell=True)
    message: "Potential shell injection"
    severity: ERROR
    languages: [python]
```

### 9.4 Performance Benchmarks

| Gate | Target | Measurement Method |
|------|--------|-------------------|
| Gate 1 (syntax) | <1s | pytest-benchmark on 100 files |
| Gate 2 (security) | <60s timeout | Semgrep execution time |
| Gate 3 (architecture) | <1s | pytest-benchmark on 50 files |
| Gate 4 (tests) | <120s timeout | Pytest execution time |
| Total pipeline | <3s (p95) | End-to-end integration test (excluding Gate 4) |

### 9.5 Cost Analysis

**Ollama Self-Hosted**:
- Cost per 1K tokens: $0.001
- Average generation: 5K tokens
- Cost per generation: $0.005
- 1000 generations/month: $5

**Semgrep**:
- Free tier: Unlimited (self-hosted)
- Execution time: ~5s per project
- Cost: $0

**Test Execution**:
- Compute: GitHub Actions runners or self-hosted
- Average test time: 30s
- Cost: $0.008 per run (GitHub pricing)
- 1000 runs/month: $8

**Total Cost per Project**:
- Light usage (100 generations/month): $1.30
- Medium usage (500 generations/month): $6.50
- Heavy usage (1000 generations/month): $13.00
- **Target: <$50/month** ✅ ACHIEVABLE

### 9.6 Success Metrics

| Metric | Target | Actual (TBD) | Status |
|--------|--------|--------------|--------|
| Pass rate | ≥95% | TBD | ⏳ |
| Validation latency | <3s (p95) | TBD | ⏳ |
| False positive rate | <5% | TBD | ⏳ |
| Cost per project | <$50/month | TBD | ⏳ |
| Test coverage | ≥90% | TBD | ⏳ |

### 9.7 Glossary

- **Quality Gate**: Automated validation checkpoint that code must pass
- **Vibecoding Index**: Composite score (0-100) from governance system (SPEC-0001)
- **Semgrep**: Static analysis tool for security vulnerability detection
- **OWASP**: Open Web Application Security Project (security rules standard)
- **AST**: Abstract Syntax Tree (code parsing structure)
- **p95**: 95th percentile (performance metric)
- **BDD**: Behavior-Driven Development (GIVEN-WHEN-THEN format)

---

## Document Control

**Change Log**:
- 2026-01-28: Migrated to Framework 6.0.5 format (Backend Lead)
- 2025-12-23: Original specification created (Backend Lead + QA Lead)

**Approval**:
- ✅ Backend Lead: Approved
- ✅ QA Lead: Approved
- ✅ Tech Lead: Approved
- ✅ CTO: Approved (Jan 28, 2026)
