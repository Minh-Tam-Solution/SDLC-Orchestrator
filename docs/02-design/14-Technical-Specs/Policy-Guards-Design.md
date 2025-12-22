# Policy Guards Technical Design
## Sprint 43 - OPA Integration & Policy-as-Code

---

**Document Information**

| Field | Value |
|-------|-------|
| **Document ID** | TDS-043-001 |
| **Version** | 1.0.0 |
| **Status** | DRAFT |
| **Created** | 2025-12-22 |
| **Author** | Backend Lead |
| **Sprint** | 43 |
| **Epic** | EP-02: AI Safety Layer v1 |

---

## 1. Overview

### 1.1 Purpose

Policy Guards provide policy-as-code enforcement for AI-generated code using the Open Policy Agent (OPA). This document defines the technical design for integrating OPA with the SDLC Orchestrator's AI Safety Layer.

### 1.2 Scope

- OPA integration architecture
- Policy schema and storage
- Policy evaluation flow
- Default AI safety policies
- API endpoints

### 1.3 Out of Scope

- Custom policy editor UI (Sprint 44+)
- Policy versioning (Sprint 45+)
- Multi-tenant policy isolation (Sprint 46+)

---

## 2. Architecture

### 2.1 Component Diagram

```
┌─────────────────────────────────────────────────────────────────────────┐
│                          SDLC Orchestrator                               │
│                                                                          │
│  ┌─────────────┐    ┌─────────────────┐    ┌───────────────────┐        │
│  │   API       │───►│  Validation     │───►│  PolicyGuard      │        │
│  │   Routes    │    │  Pipeline       │    │  Validator        │        │
│  └─────────────┘    └─────────────────┘    └─────────┬─────────┘        │
│                                                       │                  │
│                                                       │                  │
│  ┌─────────────┐    ┌─────────────────┐    ┌─────────▼─────────┐        │
│  │  Policy     │◄───│  Policy Pack    │◄───│  OPA Policy       │        │
│  │  Repository │    │  Service        │    │  Service          │        │
│  └─────────────┘    └─────────────────┘    └─────────┬─────────┘        │
│                                                       │                  │
└───────────────────────────────────────────────────────│──────────────────┘
                                                        │
                                                        │ HTTP (REST)
                                                        ▼
                                              ┌─────────────────┐
                                              │   OPA Server    │
                                              │   (Sidecar)     │
                                              │   Port: 8181    │
                                              └─────────────────┘
```

### 2.2 Component Responsibilities

| Component | Responsibility |
|-----------|---------------|
| **PolicyGuardValidator** | Validator in pipeline, orchestrates policy evaluation |
| **OPAPolicyService** | HTTP client for OPA, loads/evaluates policies |
| **PolicyPackService** | CRUD operations for policy packs and rules |
| **PolicyRepository** | Database operations for policy storage |
| **OPA Server** | Rego policy evaluation engine (sidecar container) |

### 2.3 Data Flow

```
1. PR Created/Updated
        │
        ▼
2. ValidationPipeline triggered
        │
        ▼
3. PolicyGuardValidator.validate()
        │
        ├── Get PolicyPack for project
        │
        ├── Prepare input data (files, diff, metadata)
        │
        └── OPAPolicyService.evaluate_policies()
                │
                ├── For each PolicyRule:
                │     ├── Load Rego to OPA (PUT /v1/policies/{id})
                │     │
                │     └── Evaluate (POST /v1/data/{id}/allow)
                │
                └── Aggregate results
        │
        ▼
4. Return ValidatorResult
        │
        ▼
5. Pipeline continues with other validators
```

---

## 3. Data Models

### 3.1 Policy Rule Schema

```python
# backend/app/schemas/policy_pack.py

from pydantic import BaseModel, Field
from typing import List, Optional
from enum import Enum
from uuid import UUID

class PolicySeverity(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"

class PolicyRule(BaseModel):
    """Single OPA policy rule."""

    id: str = Field(..., description="Unique policy identifier", regex=r"^[a-z0-9-]+$")
    name: str = Field(..., min_length=3, max_length=100)
    description: str = Field(..., min_length=10, max_length=500)
    rego_policy: str = Field(..., min_length=50, description="Rego policy code")
    severity: PolicySeverity = PolicySeverity.MEDIUM
    blocking: bool = True
    message_template: str = Field(
        ...,
        description="Message shown when policy fails. Use {file}, {line} placeholders."
    )
    enabled: bool = True
    tags: List[str] = []

    class Config:
        schema_extra = {
            "example": {
                "id": "no-hardcoded-secrets",
                "name": "No Hardcoded Secrets",
                "description": "Detects hardcoded passwords, API keys, and secrets",
                "rego_policy": "package ai_safety.no_secrets\n\ndefault allow = true\n...",
                "severity": "critical",
                "blocking": True,
                "message_template": "Hardcoded secret detected in {file}",
                "enabled": True,
                "tags": ["security", "secrets"],
            }
        }

class ValidatorConfig(BaseModel):
    """Configuration for a validator in the pipeline."""

    name: str = Field(..., description="Validator name (lint, test, coverage, etc)")
    enabled: bool = True
    blocking: bool = True
    config: dict = Field(default_factory=dict)

class PolicyPackBase(BaseModel):
    """Base schema for policy pack."""

    name: str = Field(..., min_length=3, max_length=100)
    description: str = Field(..., min_length=10, max_length=1000)
    version: str = Field(..., regex=r"^\d+\.\d+\.\d+$")
    tier: str = Field(..., regex=r"^(lite|standard|professional|enterprise)$")

class PolicyPackCreate(PolicyPackBase):
    """Schema for creating a policy pack."""

    # Validator configurations
    validators: List[ValidatorConfig] = Field(default_factory=list)

    # Coverage thresholds
    coverage_threshold: int = Field(80, ge=0, le=100)
    coverage_blocking: bool = False

    # Custom OPA policies
    policies: List[PolicyRule] = Field(default_factory=list)

    # Architecture rules
    forbidden_imports: List[str] = Field(default_factory=list)
    required_patterns: List[str] = Field(default_factory=list)

class PolicyPackResponse(PolicyPackBase):
    """Schema for policy pack response."""

    id: UUID
    project_id: UUID
    created_at: datetime
    updated_at: datetime
    policies_count: int
    validators_count: int

class PolicyResult(BaseModel):
    """Result of evaluating a single policy."""

    policy_id: str
    policy_name: str
    passed: bool
    severity: PolicySeverity
    blocking: bool
    message: Optional[str] = None
    violations: List[dict] = Field(default_factory=list)
    evaluation_time_ms: int
```

### 3.2 Database Schema

```sql
-- migrations/versions/xxx_add_policy_tables.py

-- Policy Packs table
CREATE TABLE policy_packs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    name VARCHAR(100) NOT NULL,
    description TEXT NOT NULL,
    version VARCHAR(20) NOT NULL,
    tier VARCHAR(20) NOT NULL CHECK (tier IN ('lite', 'standard', 'professional', 'enterprise')),

    -- Validator configs as JSONB
    validators JSONB NOT NULL DEFAULT '[]',

    -- Coverage settings
    coverage_threshold INTEGER NOT NULL DEFAULT 80,
    coverage_blocking BOOLEAN NOT NULL DEFAULT FALSE,

    -- Architecture rules
    forbidden_imports JSONB NOT NULL DEFAULT '[]',
    required_patterns JSONB NOT NULL DEFAULT '[]',

    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    created_by UUID REFERENCES users(id),

    -- Constraints
    UNIQUE(project_id)  -- One policy pack per project
);

-- Policy Rules table
CREATE TABLE policy_rules (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    policy_pack_id UUID NOT NULL REFERENCES policy_packs(id) ON DELETE CASCADE,

    -- Policy definition
    policy_id VARCHAR(100) NOT NULL,  -- e.g., "no-hardcoded-secrets"
    name VARCHAR(100) NOT NULL,
    description TEXT NOT NULL,
    rego_policy TEXT NOT NULL,
    severity VARCHAR(20) NOT NULL CHECK (severity IN ('critical', 'high', 'medium', 'low', 'info')),
    blocking BOOLEAN NOT NULL DEFAULT TRUE,
    message_template TEXT NOT NULL,
    enabled BOOLEAN NOT NULL DEFAULT TRUE,
    tags JSONB NOT NULL DEFAULT '[]',

    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),

    -- Constraints
    UNIQUE(policy_pack_id, policy_id)
);

-- Policy Evaluation History
CREATE TABLE policy_evaluations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID NOT NULL REFERENCES projects(id),
    pr_number INTEGER NOT NULL,
    policy_pack_id UUID REFERENCES policy_packs(id),

    -- Results
    total_policies INTEGER NOT NULL,
    passed_count INTEGER NOT NULL,
    failed_count INTEGER NOT NULL,
    blocked BOOLEAN NOT NULL,
    results JSONB NOT NULL,

    -- Timing
    started_at TIMESTAMP WITH TIME ZONE NOT NULL,
    completed_at TIMESTAMP WITH TIME ZONE NOT NULL,
    duration_ms INTEGER NOT NULL,

    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_policy_packs_project_id ON policy_packs(project_id);
CREATE INDEX idx_policy_rules_pack_id ON policy_rules(policy_pack_id);
CREATE INDEX idx_policy_evaluations_project_pr ON policy_evaluations(project_id, pr_number);
CREATE INDEX idx_policy_evaluations_created_at ON policy_evaluations(created_at);
```

---

## 4. OPA Integration

### 4.1 OPA Server Configuration

```yaml
# docker-compose.yml addition

services:
  opa:
    image: openpolicyagent/opa:0.58.0
    container_name: sdlc-opa
    ports:
      - "8185:8181"
    command:
      - "run"
      - "--server"
      - "--addr=0.0.0.0:8181"
      - "--log-level=info"
      - "--log-format=json"
    volumes:
      - ./policy-packs/rego:/policies:ro
    healthcheck:
      test: ["CMD", "wget", "-q", "--spider", "http://localhost:8181/health"]
      interval: 10s
      timeout: 5s
      retries: 3
    networks:
      - sdlc-network
    restart: unless-stopped
```

### 4.2 OPA Policy Service

```python
# backend/app/services/opa_policy_service.py

import httpx
from typing import List, Optional
from datetime import datetime
import asyncio

from app.schemas.policy_pack import PolicyRule, PolicyResult, PolicySeverity
from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)

class OPAPolicyService:
    """Service for interacting with OPA server."""

    def __init__(self, opa_url: str = None):
        self.opa_url = opa_url or settings.OPA_URL
        self.client = httpx.AsyncClient(
            base_url=self.opa_url,
            timeout=httpx.Timeout(10.0, connect=5.0),
        )
        self._policy_cache: dict[str, datetime] = {}

    async def health_check(self) -> bool:
        """Check if OPA server is healthy."""
        try:
            response = await self.client.get("/health")
            return response.status_code == 200
        except Exception as e:
            logger.error(f"OPA health check failed: {e}")
            return False

    async def load_policy(self, policy: PolicyRule) -> bool:
        """Load a Rego policy to OPA server."""
        try:
            # Use policy_id as OPA policy name
            response = await self.client.put(
                f"/v1/policies/{policy.id}",
                content=policy.rego_policy,
                headers={"Content-Type": "text/plain"},
            )

            if response.status_code == 200:
                self._policy_cache[policy.id] = datetime.utcnow()
                logger.info(f"Loaded policy: {policy.id}")
                return True
            else:
                logger.error(f"Failed to load policy {policy.id}: {response.text}")
                return False

        except Exception as e:
            logger.error(f"Error loading policy {policy.id}: {e}")
            return False

    async def evaluate_policy(
        self,
        policy: PolicyRule,
        input_data: dict,
    ) -> PolicyResult:
        """Evaluate a single policy against input data."""
        start_time = datetime.utcnow()

        try:
            # Ensure policy is loaded
            if policy.id not in self._policy_cache:
                await self.load_policy(policy)

            # Evaluate policy
            # Package name is derived from policy id: ai_safety.{id with - replaced by _}
            package_name = f"ai_safety.{policy.id.replace('-', '_')}"

            response = await self.client.post(
                f"/v1/data/{package_name}/allow",
                json={"input": input_data},
            )

            result_data = response.json()
            passed = result_data.get("result", True)  # Default to allow

            # Get violations if policy failed
            violations = []
            if not passed:
                violations_response = await self.client.post(
                    f"/v1/data/{package_name}/violations",
                    json={"input": input_data},
                )
                violations = violations_response.json().get("result", [])

            duration_ms = int((datetime.utcnow() - start_time).total_seconds() * 1000)

            return PolicyResult(
                policy_id=policy.id,
                policy_name=policy.name,
                passed=passed,
                severity=policy.severity,
                blocking=policy.blocking,
                message=policy.message_template if not passed else None,
                violations=violations,
                evaluation_time_ms=duration_ms,
            )

        except Exception as e:
            duration_ms = int((datetime.utcnow() - start_time).total_seconds() * 1000)
            logger.error(f"Error evaluating policy {policy.id}: {e}")

            return PolicyResult(
                policy_id=policy.id,
                policy_name=policy.name,
                passed=True,  # Fail open
                severity=policy.severity,
                blocking=policy.blocking,
                message=f"Evaluation error: {str(e)}",
                violations=[],
                evaluation_time_ms=duration_ms,
            )

    async def evaluate_policies(
        self,
        policies: List[PolicyRule],
        input_data: dict,
    ) -> List[PolicyResult]:
        """Evaluate multiple policies in parallel."""
        tasks = [
            self.evaluate_policy(policy, input_data)
            for policy in policies
            if policy.enabled
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        return [
            result if isinstance(result, PolicyResult)
            else PolicyResult(
                policy_id="unknown",
                policy_name="Error",
                passed=True,
                severity=PolicySeverity.INFO,
                blocking=False,
                message=str(result),
                violations=[],
                evaluation_time_ms=0,
            )
            for result in results
        ]

    async def close(self):
        """Close HTTP client."""
        await self.client.aclose()
```

### 4.3 Policy Guard Validator

```python
# backend/app/services/validators/policy_guard_validator.py

from typing import List
from uuid import UUID
import time

from app.services.validators.base import BaseValidator, ValidatorResult, ValidatorStatus
from app.services.opa_policy_service import OPAPolicyService
from app.services.policy_pack_service import PolicyPackService
from app.schemas.policy_pack import PolicyRule
from app.core.logging import get_logger

logger = get_logger(__name__)

class PolicyGuardValidator(BaseValidator):
    """Validator that enforces OPA policies on AI-generated code."""

    name = "policy_guards"
    blocking = True
    timeout_ms = 5000  # 5 seconds max

    def __init__(
        self,
        opa_service: OPAPolicyService,
        policy_pack_service: PolicyPackService,
    ):
        self.opa_service = opa_service
        self.policy_pack_service = policy_pack_service

    async def validate(
        self,
        project_id: UUID,
        pr_number: int,
        files: List[dict],
        diff: str,
    ) -> ValidatorResult:
        """Run policy validation on PR."""
        start_time = time.time()

        try:
            # Get policy pack for project
            policy_pack = await self.policy_pack_service.get_by_project(project_id)

            if not policy_pack or not policy_pack.policies:
                return ValidatorResult(
                    validator_name=self.name,
                    status=ValidatorStatus.SKIPPED,
                    message="No policies configured",
                    details={"reason": "No policy pack or policies for project"},
                    duration_ms=int((time.time() - start_time) * 1000),
                    blocking=False,
                )

            # Prepare input for OPA
            input_data = self._prepare_input(files, diff, policy_pack)

            # Evaluate all policies
            results = await self.opa_service.evaluate_policies(
                policy_pack.policies,
                input_data,
            )

            # Aggregate results
            failures = [r for r in results if not r.passed]
            blocking_failures = [r for r in failures if r.blocking]

            duration_ms = int((time.time() - start_time) * 1000)

            if blocking_failures:
                return ValidatorResult(
                    validator_name=self.name,
                    status=ValidatorStatus.FAILED,
                    message=f"{len(blocking_failures)} blocking policy violation(s)",
                    details={
                        "total_policies": len(results),
                        "passed": len([r for r in results if r.passed]),
                        "failed": len(failures),
                        "blocking_failures": len(blocking_failures),
                        "violations": [
                            {
                                "policy_id": f.policy_id,
                                "policy_name": f.policy_name,
                                "severity": f.severity.value,
                                "message": f.message,
                                "violations": f.violations,
                            }
                            for f in blocking_failures
                        ],
                    },
                    duration_ms=duration_ms,
                    blocking=True,
                )

            return ValidatorResult(
                validator_name=self.name,
                status=ValidatorStatus.PASSED,
                message=f"All {len(results)} policies passed",
                details={
                    "total_policies": len(results),
                    "passed": len([r for r in results if r.passed]),
                    "warnings": [
                        {
                            "policy_id": f.policy_id,
                            "policy_name": f.policy_name,
                            "severity": f.severity.value,
                            "message": f.message,
                        }
                        for f in failures
                        if not f.blocking
                    ],
                },
                duration_ms=duration_ms,
                blocking=False,
            )

        except Exception as e:
            duration_ms = int((time.time() - start_time) * 1000)
            logger.error(f"Policy validation error: {e}")

            return ValidatorResult(
                validator_name=self.name,
                status=ValidatorStatus.ERROR,
                message=f"Policy validation error: {str(e)}",
                details={"error": str(e)},
                duration_ms=duration_ms,
                blocking=False,  # Fail open
            )

    def _prepare_input(
        self,
        files: List[dict],
        diff: str,
        policy_pack,
    ) -> dict:
        """Prepare input data for OPA evaluation."""
        return {
            "files": [
                {
                    "path": f.get("path", ""),
                    "content": f.get("content", ""),
                    "language": self._detect_language(f.get("path", "")),
                    "imports": self._extract_imports(f.get("content", "")),
                    "layer": self._detect_layer(f.get("path", "")),
                }
                for f in files
            ],
            "diff": diff,
            "config": {
                "forbidden_imports": policy_pack.forbidden_imports,
                "required_patterns": policy_pack.required_patterns,
                "coverage_threshold": policy_pack.coverage_threshold,
            },
        }

    def _detect_language(self, path: str) -> str:
        """Detect programming language from file path."""
        if path.endswith(".py"):
            return "python"
        elif path.endswith((".ts", ".tsx")):
            return "typescript"
        elif path.endswith((".js", ".jsx")):
            return "javascript"
        elif path.endswith(".go"):
            return "go"
        elif path.endswith(".rs"):
            return "rust"
        return "unknown"

    def _extract_imports(self, content: str) -> List[str]:
        """Extract import statements from code."""
        import re

        imports = []

        # Python imports
        imports.extend(re.findall(r"^import\s+(\S+)", content, re.MULTILINE))
        imports.extend(re.findall(r"^from\s+(\S+)\s+import", content, re.MULTILINE))

        # JavaScript/TypeScript imports
        imports.extend(re.findall(r"import\s+.*?from\s+['\"]([^'\"]+)['\"]", content))
        imports.extend(re.findall(r"require\(['\"]([^'\"]+)['\"]\)", content))

        return imports

    def _detect_layer(self, path: str) -> str:
        """Detect architectural layer from file path."""
        if "/api/" in path or "/routes/" in path:
            return "presentation"
        elif "/services/" in path:
            return "business"
        elif "/repositories/" in path or "/db/" in path:
            return "data"
        elif "/schemas/" in path or "/models/" in path:
            return "domain"
        return "unknown"
```

---

## 5. Default Policies

### 5.1 No Hardcoded Secrets

```rego
# policy-packs/rego/ai-safety/no_hardcoded_secrets.rego
package ai_safety.no_hardcoded_secrets

import future.keywords.in

default allow = true

# Deny if hardcoded secrets detected
allow = false {
    count(violations) > 0
}

violations[violation] {
    some file in input.files
    some i, line in split(file.content, "\n")
    contains_secret(line)
    violation := {
        "file": file.path,
        "line": i + 1,
        "pattern": "hardcoded secret",
    }
}

contains_secret(line) {
    patterns := [
        `password\s*=\s*["'][^"']+["']`,
        `api_key\s*=\s*["'][^"']+["']`,
        `secret\s*=\s*["'][^"']+["']`,
        `token\s*=\s*["'][A-Za-z0-9+/=]{20,}["']`,
        `AWS_ACCESS_KEY_ID\s*=\s*["'][A-Z0-9]{20}["']`,
        `AWS_SECRET_ACCESS_KEY\s*=\s*["'][A-Za-z0-9+/]{40}["']`,
    ]
    some pattern in patterns
    regex.match(pattern, line)
}

# Exclude test files and examples
allow = true {
    some file in input.files
    contains(file.path, "/tests/")
}

allow = true {
    some file in input.files
    endswith(file.path, ".example")
}
```

### 5.2 Architecture Boundaries

```rego
# policy-packs/rego/ai-safety/architecture_boundaries.rego
package ai_safety.architecture_boundaries

import future.keywords.in

default allow = true

# Deny if layer violations detected
allow = false {
    count(violations) > 0
}

violations[violation] {
    some file in input.files
    file.layer == "presentation"
    some import_stmt in file.imports
    is_data_layer_import(import_stmt)
    violation := {
        "file": file.path,
        "import": import_stmt,
        "message": "Presentation layer cannot directly import from data layer",
    }
}

# Data layer imports
is_data_layer_import(import_stmt) {
    data_layer_packages := [
        "app.db",
        "app.repositories",
        "sqlalchemy",
        "databases",
    ]
    some pkg in data_layer_packages
    startswith(import_stmt, pkg)
}
```

### 5.3 No Legacy Imports

```rego
# policy-packs/rego/ai-safety/no_legacy_imports.rego
package ai_safety.no_legacy_imports

import future.keywords.in

default allow = true

allow = false {
    count(violations) > 0
}

violations[violation] {
    some file in input.files
    some import_stmt in file.imports
    is_forbidden_import(import_stmt)
    violation := {
        "file": file.path,
        "import": import_stmt,
        "message": sprintf("Forbidden import: %s", [import_stmt]),
    }
}

is_forbidden_import(import_stmt) {
    some forbidden in input.config.forbidden_imports
    startswith(import_stmt, forbidden)
}
```

---

## 6. API Endpoints

### 6.1 Policy Pack CRUD

```python
# backend/app/api/routes/policies.py

from fastapi import APIRouter, Depends, HTTPException
from uuid import UUID
from typing import List

from app.api.deps import get_current_user, get_policy_pack_service
from app.schemas.policy_pack import (
    PolicyPackCreate,
    PolicyPackResponse,
    PolicyPackUpdate,
    PolicyRule,
)
from app.models.user import User

router = APIRouter(prefix="/projects/{project_id}/policies", tags=["policies"])

@router.post("", response_model=PolicyPackResponse)
async def create_policy_pack(
    project_id: UUID,
    policy_pack: PolicyPackCreate,
    current_user: User = Depends(get_current_user),
    service = Depends(get_policy_pack_service),
):
    """Create or update policy pack for project."""
    # Check permission
    if not await service.can_manage_policies(current_user, project_id):
        raise HTTPException(403, "Not authorized to manage policies")

    return await service.create_or_update(project_id, policy_pack, current_user.id)

@router.get("", response_model=PolicyPackResponse)
async def get_policy_pack(
    project_id: UUID,
    current_user: User = Depends(get_current_user),
    service = Depends(get_policy_pack_service),
):
    """Get policy pack for project."""
    policy_pack = await service.get_by_project(project_id)
    if not policy_pack:
        raise HTTPException(404, "Policy pack not found")
    return policy_pack

@router.post("/rules", response_model=PolicyRule)
async def add_policy_rule(
    project_id: UUID,
    rule: PolicyRule,
    current_user: User = Depends(get_current_user),
    service = Depends(get_policy_pack_service),
):
    """Add a custom policy rule."""
    if not await service.can_manage_policies(current_user, project_id):
        raise HTTPException(403, "Not authorized to manage policies")

    return await service.add_rule(project_id, rule)

@router.delete("/rules/{rule_id}")
async def delete_policy_rule(
    project_id: UUID,
    rule_id: str,
    current_user: User = Depends(get_current_user),
    service = Depends(get_policy_pack_service),
):
    """Delete a policy rule."""
    if not await service.can_manage_policies(current_user, project_id):
        raise HTTPException(403, "Not authorized to manage policies")

    await service.delete_rule(project_id, rule_id)
    return {"message": "Rule deleted"}

@router.post("/evaluate")
async def evaluate_policies(
    project_id: UUID,
    files: List[dict],
    diff: str = "",
    current_user: User = Depends(get_current_user),
    service = Depends(get_policy_pack_service),
):
    """Manually evaluate policies against provided files."""
    return await service.evaluate(project_id, files, diff)
```

---

## 7. Testing Strategy

### 7.1 Unit Tests

```python
# tests/unit/test_policy_guard_validator.py

class TestPolicyGuardValidator:
    @pytest.fixture
    def mock_opa_service(self):
        return AsyncMock(spec=OPAPolicyService)

    @pytest.fixture
    def validator(self, mock_opa_service, mock_policy_service):
        return PolicyGuardValidator(mock_opa_service, mock_policy_service)

    @pytest.mark.asyncio
    async def test_validate_with_no_policies(self, validator, mock_policy_service):
        mock_policy_service.get_by_project.return_value = None

        result = await validator.validate(
            project_id=uuid4(),
            pr_number=1,
            files=[],
            diff="",
        )

        assert result.status == ValidatorStatus.SKIPPED

    @pytest.mark.asyncio
    async def test_validate_all_policies_pass(self, validator, mock_opa_service):
        mock_opa_service.evaluate_policies.return_value = [
            PolicyResult(
                policy_id="test",
                policy_name="Test",
                passed=True,
                severity=PolicySeverity.MEDIUM,
                blocking=True,
                message=None,
                violations=[],
                evaluation_time_ms=10,
            )
        ]

        result = await validator.validate(...)

        assert result.status == ValidatorStatus.PASSED

    @pytest.mark.asyncio
    async def test_validate_blocking_failure(self, validator, mock_opa_service):
        mock_opa_service.evaluate_policies.return_value = [
            PolicyResult(
                policy_id="no-secrets",
                policy_name="No Secrets",
                passed=False,
                severity=PolicySeverity.CRITICAL,
                blocking=True,
                message="Secret detected",
                violations=[{"file": "config.py", "line": 10}],
                evaluation_time_ms=10,
            )
        ]

        result = await validator.validate(...)

        assert result.status == ValidatorStatus.FAILED
        assert result.blocking is True
```

### 7.2 Integration Tests

```python
# tests/integration/test_policy_guards.py

class TestPolicyGuardsIntegration:
    @pytest.fixture
    def opa_service(self):
        return OPAPolicyService(opa_url="http://localhost:8185")

    @pytest.mark.asyncio
    async def test_opa_health_check(self, opa_service):
        assert await opa_service.health_check() is True

    @pytest.mark.asyncio
    async def test_load_and_evaluate_policy(self, opa_service):
        policy = PolicyRule(
            id="test-policy",
            name="Test Policy",
            description="Test policy for integration testing",
            rego_policy="""
                package ai_safety.test_policy
                default allow = true
                allow = false { input.test == "fail" }
            """,
            severity=PolicySeverity.MEDIUM,
            blocking=True,
            message_template="Test failed",
        )

        # Load policy
        assert await opa_service.load_policy(policy) is True

        # Evaluate - should pass
        result = await opa_service.evaluate_policy(
            policy,
            {"test": "pass"},
        )
        assert result.passed is True

        # Evaluate - should fail
        result = await opa_service.evaluate_policy(
            policy,
            {"test": "fail"},
        )
        assert result.passed is False
```

---

## 8. Performance Considerations

### 8.1 Policy Caching

- Cache compiled policies in OPA (automatic)
- Cache policy pack lookups in Redis (TTL: 5 minutes)
- Invalidate cache on policy pack update

### 8.2 Parallel Evaluation

- Evaluate all policies in parallel using `asyncio.gather`
- Set per-policy timeout (1 second)
- Total validation timeout: 5 seconds

### 8.3 Metrics

```python
# Prometheus metrics
policy_evaluation_duration = Histogram(
    "policy_evaluation_duration_seconds",
    "Time to evaluate policies",
    ["policy_id", "result"],
)

policy_evaluation_total = Counter(
    "policy_evaluation_total",
    "Total policy evaluations",
    ["result", "severity"],
)
```

---

## 9. Security Considerations

### 9.1 Rego Policy Validation

- Validate Rego syntax before storing
- Sandbox evaluation (OPA provides this)
- Limit policy complexity (max 100 rules per pack)

### 9.2 Access Control

- Only Project Admins can manage policies
- Policy changes are audited
- Default policies cannot be deleted

---

## 10. Changelog

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0.0 | 2025-12-22 | Backend Lead | Initial design |

---

**Approvals**

| Role | Name | Date | Status |
|------|------|------|--------|
| CTO | | | PENDING |
| Backend Lead | | | PENDING |
| Security Lead | | | PENDING |
