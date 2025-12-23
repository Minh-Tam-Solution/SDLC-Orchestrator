# Codegen Service Technical Specification
## EP-06: IR-Based Vietnamese SME Codegen Engine | Sprint 45

**Status**: APPROVED
**Version**: 1.0.0
**Date**: December 23, 2025
**Author**: Backend Lead + Architect
**Sprint**: Sprint 45 (Jan 6-17, 2026)
**Framework**: SDLC 5.1.1 + SASE Level 2
**ADR Reference**: [ADR-022-Multi-Provider-Codegen-Architecture](../01-ADRs/ADR-022-Multi-Provider-Codegen-Architecture.md)

---

## 1. Overview

### 1.1 Purpose

This specification defines the technical implementation of the Codegen Service - the core component of EP-06 that enables IR-based code generation for Vietnam SME founders.

### 1.2 Scope

| In Scope | Out of Scope |
|----------|--------------|
| Provider interface contract | DeepCode integration (Q2 2026) |
| Provider registry & routing | Frontend onboarding wizard |
| Ollama provider implementation | Vietnamese prompt fine-tuning |
| API endpoints (/api/v1/codegen/*) | IR schema validation (Sprint 46) |
| Integration tests | Load testing (Sprint 48) |

### 1.3 Strategic Context

```
┌─────────────────────────────────────────────────────────────────────┐
│  LAYER 3: AI CODERS (They Generate)                                 │
│  Claude Code | Cursor | Copilot | Aider | Ollama                    │
├─────────────────────────────────────────────────────────────────────┤
│  LAYER 2: SDLC ORCHESTRATOR (We Govern) ← This Service              │
│  ★ Codegen Service: Multi-provider architecture                    │
│  ★ Provider Registry: Ollama → Claude → DeepCode                   │
├─────────────────────────────────────────────────────────────────────┤
│  LAYER 1: SDLC-ENTERPRISE-FRAMEWORK (Methodology)                   │
│  10 Stages | 4 Tiers | Quality Gates                                │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 2. Architecture

### 2.1 Component Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                         API Layer                                    │
│  ┌──────────────────┐ ┌──────────────────┐ ┌──────────────────┐     │
│  │ POST /generate   │ │ POST /validate   │ │ GET /providers   │     │
│  └────────┬─────────┘ └────────┬─────────┘ └────────┬─────────┘     │
└───────────┼────────────────────┼────────────────────┼───────────────┘
            │                    │                    │
            v                    v                    v
┌─────────────────────────────────────────────────────────────────────┐
│                      CodegenService                                  │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │  - generate(spec, preferred_provider) -> CodegenResult       │   │
│  │  - validate(code, context) -> ValidationResult               │   │
│  │  - list_providers() -> List[ProviderInfo]                    │   │
│  │  - estimate_cost(spec) -> Dict[str, CostEstimate]            │   │
│  └────────────────────────────┬─────────────────────────────────┘   │
└───────────────────────────────┼─────────────────────────────────────┘
                                │
                                v
┌─────────────────────────────────────────────────────────────────────┐
│                      ProviderRegistry                                │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │  - register(provider)                                         │   │
│  │  - unregister(name)                                           │   │
│  │  - get(name) -> CodegenProvider                               │   │
│  │  - select_provider(preferred) -> CodegenProvider              │   │
│  │  - list_available() -> List[str]                              │   │
│  └────────────────────────────┬─────────────────────────────────┘   │
└───────────────────────────────┼─────────────────────────────────────┘
                                │
        ┌───────────────────────┼───────────────────────┐
        │                       │                       │
        v                       v                       v
┌───────────────┐      ┌───────────────┐      ┌───────────────┐
│   Ollama      │      │    Claude     │      │   DeepCode    │
│   Provider    │      │   Provider    │      │   Provider    │
│   (Primary)   │      │   (Fallback)  │      │   (Stub)      │
│               │      │               │      │               │
│ is_available: │      │ is_available: │      │ is_available: │
│     true      │      │    false*     │      │    false      │
└───────┬───────┘      └───────────────┘      └───────────────┘
        │
        v
┌───────────────────────────────────────────────────────────────┐
│              External: Ollama API (api.nhatquangholding.com)                │
│              Model: qwen2.5-coder:14b                         │
└───────────────────────────────────────────────────────────────┘

* Claude available only if ANTHROPIC_API_KEY configured
```

### 2.2 Package Structure

```
backend/app/
├── services/
│   └── codegen/
│       ├── __init__.py
│       ├── base_provider.py      # Abstract interface + Pydantic models
│       ├── provider_registry.py  # Registry + routing logic
│       ├── codegen_service.py    # Main orchestrator
│       ├── ollama_provider.py    # Ollama implementation
│       ├── claude_provider.py    # Claude stub
│       └── deepcode_provider.py  # DeepCode stub
├── api/
│   └── routes/
│       └── codegen.py            # API endpoints
├── schemas/
│   └── codegen.py                # Request/Response schemas
└── core/
    └── config.py                 # Add OLLAMA_* settings
```

---

## 3. Data Models

### 3.1 Pydantic Models (backend/app/services/codegen/base_provider.py)

```python
from pydantic import BaseModel, Field
from typing import Dict, Any, Optional, List
from enum import Enum

class CodegenLanguage(str, Enum):
    PYTHON = "python"
    TYPESCRIPT = "typescript"
    JAVASCRIPT = "javascript"

class CodegenFramework(str, Enum):
    FASTAPI = "fastapi"
    FLASK = "flask"
    NEXTJS = "nextjs"
    REACT = "react"

class CodegenSpec(BaseModel):
    """Input specification for code generation"""
    app_blueprint: Dict[str, Any] = Field(
        ...,
        description="AppBlueprint from app_blueprint.schema.json"
    )
    target_module: Optional[str] = Field(
        None,
        description="Specific module to generate (None = all)"
    )
    language: CodegenLanguage = Field(
        CodegenLanguage.PYTHON,
        description="Target programming language"
    )
    framework: CodegenFramework = Field(
        CodegenFramework.FASTAPI,
        description="Target framework"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "app_blueprint": {
                    "name": "Restaurant Order System",
                    "version": "1.0.0",
                    "modules": ["orders", "menu", "customers"]
                },
                "target_module": "orders",
                "language": "python",
                "framework": "fastapi"
            }
        }


class GeneratedFile(BaseModel):
    """Single generated file"""
    path: str = Field(..., description="Relative file path")
    content: str = Field(..., description="File content")
    language: str = Field(..., description="File language/type")


class CodegenResult(BaseModel):
    """Output from code generation"""
    success: bool = Field(..., description="Generation success status")
    files: List[GeneratedFile] = Field(
        default_factory=list,
        description="List of generated files"
    )
    provider: str = Field(..., description="Provider that generated the code")
    tokens_used: int = Field(0, description="Total tokens used")
    generation_time_ms: int = Field(0, description="Generation time in ms")
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional metadata"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "files": [
                    {
                        "path": "app/models/order.py",
                        "content": "from sqlalchemy import ...",
                        "language": "python"
                    }
                ],
                "provider": "ollama",
                "tokens_used": 1500,
                "generation_time_ms": 2500,
                "metadata": {"model": "qwen2.5-coder:14b"}
            }
        }


class ValidationSeverity(str, Enum):
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


class ValidationIssue(BaseModel):
    """Single validation issue"""
    severity: ValidationSeverity
    message: str
    file: Optional[str] = None
    line: Optional[int] = None
    rule: Optional[str] = None


class ValidationResult(BaseModel):
    """Output from code validation"""
    valid: bool = Field(..., description="Overall validation passed")
    issues: List[ValidationIssue] = Field(
        default_factory=list,
        description="List of validation issues"
    )
    suggestions: List[str] = Field(
        default_factory=list,
        description="Improvement suggestions"
    )


class CostEstimate(BaseModel):
    """Cost estimation for generation"""
    provider: str = Field(..., description="Provider name")
    estimated_tokens: int = Field(..., description="Estimated token count")
    estimated_cost_usd: float = Field(..., description="Estimated cost in USD")
    confidence: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Confidence level (0-1)"
    )


class ProviderInfo(BaseModel):
    """Provider information for listing"""
    name: str
    available: bool
    primary: bool
    status: str = Field("unknown", description="Current status message")
```

### 3.2 Request/Response Schemas (backend/app/schemas/codegen.py)

```python
from pydantic import BaseModel, Field
from typing import Dict, Any, Optional, List
from app.services.codegen.base_provider import (
    CodegenLanguage, CodegenFramework, CodegenResult,
    ValidationResult, CostEstimate, ProviderInfo
)


class GenerateRequest(BaseModel):
    """Request body for POST /codegen/generate"""
    app_blueprint: Dict[str, Any] = Field(
        ...,
        description="AppBlueprint JSON from IR schema"
    )
    target_module: Optional[str] = Field(
        None,
        description="Specific module to generate"
    )
    language: CodegenLanguage = Field(
        CodegenLanguage.PYTHON,
        description="Target programming language"
    )
    framework: CodegenFramework = Field(
        CodegenFramework.FASTAPI,
        description="Target framework"
    )
    preferred_provider: Optional[str] = Field(
        None,
        description="Preferred provider (ollama, claude, deepcode)"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "app_blueprint": {
                    "name": "F&B Order System",
                    "version": "1.0.0",
                    "business_domain": "restaurant",
                    "modules": [
                        {
                            "name": "orders",
                            "entities": ["Order", "OrderItem"],
                            "operations": ["create", "list", "update_status"]
                        }
                    ]
                },
                "language": "python",
                "framework": "fastapi",
                "preferred_provider": "ollama"
            }
        }


class GenerateResponse(BaseModel):
    """Response body for POST /codegen/generate"""
    success: bool
    result: Optional[CodegenResult] = None
    error: Optional[str] = None


class ValidateRequest(BaseModel):
    """Request body for POST /codegen/validate"""
    code: str = Field(..., description="Code to validate")
    context: Dict[str, Any] = Field(
        default_factory=dict,
        description="Validation context"
    )
    provider: Optional[str] = Field(
        None,
        description="Specific provider for validation"
    )


class ValidateResponse(BaseModel):
    """Response body for POST /codegen/validate"""
    success: bool
    result: Optional[ValidationResult] = None
    error: Optional[str] = None


class ProvidersResponse(BaseModel):
    """Response body for GET /codegen/providers"""
    providers: List[ProviderInfo]
    fallback_chain: List[str]


class EstimateRequest(BaseModel):
    """Request body for POST /codegen/estimate"""
    app_blueprint: Dict[str, Any]
    language: CodegenLanguage = CodegenLanguage.PYTHON
    framework: CodegenFramework = CodegenFramework.FASTAPI


class EstimateResponse(BaseModel):
    """Response body for POST /codegen/estimate"""
    estimates: Dict[str, CostEstimate]
```

---

## 4. API Specification

### 4.1 Endpoints Summary

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| `GET` | `/api/v1/codegen/providers` | List available providers | JWT |
| `POST` | `/api/v1/codegen/generate` | Generate code from IR | JWT |
| `POST` | `/api/v1/codegen/validate` | Validate generated code | JWT |
| `POST` | `/api/v1/codegen/estimate` | Estimate generation cost | JWT |

### 4.2 GET /api/v1/codegen/providers

**Description**: List all registered codegen providers with availability status.

**Response** (200 OK):
```json
{
  "providers": [
    {
      "name": "ollama",
      "available": true,
      "primary": true,
      "status": "healthy"
    },
    {
      "name": "claude",
      "available": false,
      "primary": false,
      "status": "not_configured"
    },
    {
      "name": "deepcode",
      "available": false,
      "primary": false,
      "status": "deferred_q2_2026"
    }
  ],
  "fallback_chain": ["ollama", "claude", "deepcode"]
}
```

### 4.3 POST /api/v1/codegen/generate

**Description**: Generate code from IR specification.

**Request Body**:
```json
{
  "app_blueprint": {
    "name": "Restaurant Order System",
    "version": "1.0.0",
    "business_domain": "restaurant",
    "modules": [
      {
        "name": "orders",
        "entities": ["Order", "OrderItem"],
        "operations": ["create", "list", "update_status"]
      }
    ]
  },
  "language": "python",
  "framework": "fastapi",
  "preferred_provider": "ollama"
}
```

**Response** (200 OK):
```json
{
  "success": true,
  "result": {
    "success": true,
    "files": [
      {
        "path": "app/models/order.py",
        "content": "from sqlalchemy import Column, Integer, String...",
        "language": "python"
      },
      {
        "path": "app/api/routes/orders.py",
        "content": "from fastapi import APIRouter...",
        "language": "python"
      }
    ],
    "provider": "ollama",
    "tokens_used": 2500,
    "generation_time_ms": 3200,
    "metadata": {
      "model": "qwen2.5-coder:14b",
      "prompt_tokens": 800,
      "completion_tokens": 1700
    }
  }
}
```

**Error Response** (503 Service Unavailable):
```json
{
  "success": false,
  "error": "No codegen providers available",
  "result": null
}
```

### 4.4 POST /api/v1/codegen/validate

**Description**: Validate generated code against quality standards.

**Request Body**:
```json
{
  "code": "from sqlalchemy import Column...",
  "context": {
    "language": "python",
    "framework": "fastapi",
    "check_security": true
  }
}
```

**Response** (200 OK):
```json
{
  "success": true,
  "result": {
    "valid": true,
    "issues": [
      {
        "severity": "warning",
        "message": "Consider adding input validation for user_id",
        "file": "app/api/routes/orders.py",
        "line": 45,
        "rule": "SEC-001"
      }
    ],
    "suggestions": [
      "Add type hints for all function parameters",
      "Consider using dependency injection for database session"
    ]
  }
}
```

### 4.5 POST /api/v1/codegen/estimate

**Description**: Estimate cost for code generation across all providers.

**Request Body**:
```json
{
  "app_blueprint": {
    "name": "F&B Order System",
    "modules": ["orders", "menu", "customers"]
  },
  "language": "python",
  "framework": "fastapi"
}
```

**Response** (200 OK):
```json
{
  "estimates": {
    "ollama": {
      "provider": "ollama",
      "estimated_tokens": 5000,
      "estimated_cost_usd": 0.005,
      "confidence": 0.8
    },
    "claude": {
      "provider": "claude",
      "estimated_tokens": 5000,
      "estimated_cost_usd": 0.075,
      "confidence": 0.7
    }
  }
}
```

---

## 5. Implementation Details

### 5.1 Provider Interface Contract

```python
from abc import ABC, abstractmethod

class CodegenProvider(ABC):
    """Abstract base class for all codegen providers.

    All providers MUST implement:
    - name property: Unique identifier
    - is_available property: Health check status
    - generate(): Code generation from IR
    - validate(): Code validation
    - estimate_cost(): Cost estimation
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Provider identifier (e.g., 'ollama', 'claude')"""
        pass

    @property
    @abstractmethod
    def is_available(self) -> bool:
        """Returns True if provider is configured and reachable"""
        pass

    @abstractmethod
    async def generate(self, spec: CodegenSpec) -> CodegenResult:
        """Generate code from IR specification.

        Raises:
            ProviderUnavailableError: Provider not reachable
            GenerationError: Generation failed
            TimeoutError: Generation timed out
        """
        pass

    @abstractmethod
    async def validate(
        self,
        code: str,
        context: Dict[str, Any]
    ) -> ValidationResult:
        """Validate generated code."""
        pass

    @abstractmethod
    def estimate_cost(self, spec: CodegenSpec) -> CostEstimate:
        """Estimate generation cost (sync, no network call)."""
        pass
```

### 5.2 Ollama Provider - Vietnamese Prompt Template

```python
VIETNAMESE_CODEGEN_PROMPT = """Bạn là một AI chuyên gia phát triển phần mềm cho doanh nghiệp SME Việt Nam.

## Yêu cầu
Dựa trên đặc tả IR (Intermediate Representation) sau, hãy tạo code {framework} hoàn chỉnh:

## App Blueprint
```json
{app_blueprint}
```

## Thông số
- Ngôn ngữ: {language}
- Framework: {framework}
- Module mục tiêu: {target_module}

## Quy tắc
1. Code phải production-ready, không có placeholder
2. Thêm comments tiếng Việt cho logic phức tạp
3. Tuân thủ chuẩn PEP8 (Python) hoặc ESLint (TypeScript)
4. Xử lý lỗi đầy đủ (try/except)
5. Thêm type hints cho tất cả functions

## Output Format
Trả về code theo format sau:

### FILE: path/to/file.py
```python
# code here
```

### FILE: path/to/another_file.py
```python
# code here
```

Hãy bắt đầu tạo code:
"""
```

### 5.3 Configuration Settings

```python
# backend/app/core/config.py (additions)

class Settings(BaseSettings):
    # ... existing settings ...

    # Codegen Provider Settings
    OLLAMA_API_URL: str = "https://api.nhatquangholding.com"
    OLLAMA_CODEGEN_MODEL: str = "qwen2.5-coder:14b"
    OLLAMA_TIMEOUT_SECONDS: int = 60
    OLLAMA_MAX_RETRIES: int = 3

    ANTHROPIC_API_KEY: Optional[str] = None

    # Codegen Service Settings
    CODEGEN_DEFAULT_PROVIDER: str = "ollama"
    CODEGEN_FALLBACK_CHAIN: List[str] = ["ollama", "claude", "deepcode"]
    CODEGEN_MAX_GENERATION_TIME_MS: int = 60000  # 60 seconds

    class Config:
        env_file = ".env"
```

### 5.4 Error Handling

```python
# backend/app/services/codegen/exceptions.py

class CodegenError(Exception):
    """Base exception for codegen errors"""
    pass


class ProviderUnavailableError(CodegenError):
    """Provider is not configured or not reachable"""
    def __init__(self, provider: str, reason: str = ""):
        self.provider = provider
        self.reason = reason
        super().__init__(f"Provider {provider} unavailable: {reason}")


class NoProviderAvailableError(CodegenError):
    """No providers are available in the fallback chain"""
    pass


class GenerationError(CodegenError):
    """Code generation failed"""
    def __init__(self, provider: str, message: str):
        self.provider = provider
        super().__init__(f"Generation failed ({provider}): {message}")


class GenerationTimeoutError(CodegenError):
    """Code generation timed out"""
    def __init__(self, provider: str, timeout_ms: int):
        self.provider = provider
        self.timeout_ms = timeout_ms
        super().__init__(
            f"Generation timed out ({provider}): {timeout_ms}ms"
        )


class ValidationError(CodegenError):
    """Code validation failed"""
    pass
```

---

## 6. Testing Strategy

### 6.1 Unit Tests

```python
# backend/tests/unit/services/codegen/test_provider_registry.py

import pytest
from app.services.codegen.provider_registry import ProviderRegistry
from app.services.codegen.base_provider import CodegenProvider


class MockProvider(CodegenProvider):
    def __init__(self, name: str, available: bool):
        self._name = name
        self._available = available

    @property
    def name(self) -> str:
        return self._name

    @property
    def is_available(self) -> bool:
        return self._available

    async def generate(self, spec):
        raise NotImplementedError

    async def validate(self, code, context):
        raise NotImplementedError

    def estimate_cost(self, spec):
        raise NotImplementedError


class TestProviderRegistry:
    def test_register_provider(self):
        registry = ProviderRegistry()
        provider = MockProvider("test", True)

        registry.register(provider)

        assert registry.get("test") == provider

    def test_select_provider_from_fallback_chain(self):
        registry = ProviderRegistry()
        registry.register(MockProvider("primary", False))
        registry.register(MockProvider("secondary", True))
        registry.set_fallback_chain(["primary", "secondary"])

        selected = registry.select_provider()

        assert selected.name == "secondary"

    def test_select_preferred_provider(self):
        registry = ProviderRegistry()
        registry.register(MockProvider("ollama", True))
        registry.register(MockProvider("claude", True))
        registry.set_fallback_chain(["ollama", "claude"])

        selected = registry.select_provider(preferred="claude")

        assert selected.name == "claude"

    def test_returns_none_when_all_unavailable(self):
        registry = ProviderRegistry()
        registry.register(MockProvider("provider1", False))
        registry.register(MockProvider("provider2", False))
        registry.set_fallback_chain(["provider1", "provider2"])

        selected = registry.select_provider()

        assert selected is None
```

### 6.2 Integration Tests

```python
# backend/tests/integration/test_codegen_ollama.py

import pytest
from httpx import AsyncClient
from app.main import app


@pytest.mark.integration
@pytest.mark.skipif(
    not os.getenv("OLLAMA_API_URL"),
    reason="Ollama not configured"
)
class TestCodegenOllamaIntegration:
    """Integration tests for Ollama-based code generation.

    CTO Go Condition: Ollama-only boot test
    """

    @pytest.fixture
    async def client(self):
        async with AsyncClient(app=app, base_url="http://test") as client:
            yield client

    @pytest.fixture
    async def auth_headers(self, client):
        # Login and get token
        response = await client.post("/api/v1/auth/login", json={
            "email": "test@example.com",
            "password": "password123"
        })
        token = response.json()["access_token"]
        return {"Authorization": f"Bearer {token}"}

    async def test_providers_endpoint(self, client, auth_headers):
        """Test that Ollama is listed as available provider"""
        response = await client.get(
            "/api/v1/codegen/providers",
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()

        # Find Ollama provider
        ollama = next(
            (p for p in data["providers"] if p["name"] == "ollama"),
            None
        )
        assert ollama is not None
        assert ollama["available"] is True
        assert ollama["primary"] is True

    async def test_generate_minimal_blueprint(self, client, auth_headers):
        """Test code generation with minimal AppBlueprint"""
        response = await client.post(
            "/api/v1/codegen/generate",
            headers=auth_headers,
            json={
                "app_blueprint": {
                    "name": "Test App",
                    "version": "1.0.0",
                    "modules": [
                        {
                            "name": "hello",
                            "entities": [],
                            "operations": ["greet"]
                        }
                    ]
                },
                "language": "python",
                "framework": "fastapi"
            }
        )

        assert response.status_code == 200
        data = response.json()

        assert data["success"] is True
        assert data["result"]["provider"] == "ollama"
        assert len(data["result"]["files"]) > 0
        assert data["result"]["generation_time_ms"] < 60000  # <60s

    async def test_generation_fallback_when_ollama_down(
        self,
        client,
        auth_headers,
        monkeypatch
    ):
        """Test fallback when Ollama is unavailable"""
        # This test would mock Ollama being unavailable
        # and verify fallback behavior
        pass  # Implement when Claude fallback is enabled
```

### 6.3 Smoke Test Script

```bash
#!/bin/bash
# backend/scripts/smoke_test_codegen.sh
# CTO Go Condition: Ollama-only boot test

set -e

echo "=== Codegen Service Smoke Test ==="

# 1. Check Ollama availability
echo "1. Checking Ollama availability..."
curl -sf "${OLLAMA_API_URL:-https://api.nhatquangholding.com}/api/tags" > /dev/null || {
    echo "ERROR: Ollama not reachable"
    exit 1
}
echo "   ✓ Ollama is reachable"

# 2. Get auth token
echo "2. Getting auth token..."
TOKEN=$(curl -sf -X POST "http://localhost:8000/api/v1/auth/login" \
    -H "Content-Type: application/json" \
    -d '{"email":"test@example.com","password":"password123"}' \
    | jq -r '.access_token')

if [ -z "$TOKEN" ] || [ "$TOKEN" == "null" ]; then
    echo "ERROR: Failed to get auth token"
    exit 1
fi
echo "   ✓ Auth token obtained"

# 3. Check providers
echo "3. Checking providers..."
PROVIDERS=$(curl -sf "http://localhost:8000/api/v1/codegen/providers" \
    -H "Authorization: Bearer $TOKEN")

OLLAMA_AVAILABLE=$(echo "$PROVIDERS" | jq '.providers[] | select(.name=="ollama") | .available')
if [ "$OLLAMA_AVAILABLE" != "true" ]; then
    echo "ERROR: Ollama provider not available"
    exit 1
fi
echo "   ✓ Ollama provider is available"

# 4. Test generation
echo "4. Testing code generation..."
RESULT=$(curl -sf -X POST "http://localhost:8000/api/v1/codegen/generate" \
    -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: application/json" \
    -d '{
        "app_blueprint": {
            "name": "Smoke Test App",
            "version": "1.0.0",
            "modules": [{"name": "test", "entities": [], "operations": ["hello"]}]
        },
        "language": "python",
        "framework": "fastapi"
    }')

SUCCESS=$(echo "$RESULT" | jq '.success')
if [ "$SUCCESS" != "true" ]; then
    echo "ERROR: Generation failed"
    echo "$RESULT" | jq .
    exit 1
fi

PROVIDER=$(echo "$RESULT" | jq -r '.result.provider')
FILES=$(echo "$RESULT" | jq '.result.files | length')
TIME_MS=$(echo "$RESULT" | jq '.result.generation_time_ms')

echo "   ✓ Generation successful"
echo "   - Provider: $PROVIDER"
echo "   - Files generated: $FILES"
echo "   - Time: ${TIME_MS}ms"

echo ""
echo "=== All smoke tests passed ==="
```

---

## 7. Deployment & Configuration

### 7.1 Environment Variables

```bash
# .env.example (additions)

# Codegen - Ollama (Primary)
OLLAMA_API_URL=https://api.nhatquangholding.com
OLLAMA_CODEGEN_MODEL=qwen2.5-coder:14b
OLLAMA_TIMEOUT_SECONDS=60
OLLAMA_MAX_RETRIES=3

# Codegen - Claude (Fallback, optional)
ANTHROPIC_API_KEY=  # Leave empty to disable

# Codegen - Service Config
CODEGEN_DEFAULT_PROVIDER=ollama
CODEGEN_FALLBACK_CHAIN=ollama,claude,deepcode
CODEGEN_MAX_GENERATION_TIME_MS=60000
```

### 7.2 Docker Compose (Development)

```yaml
# docker-compose.yml (additions)
services:
  # ... existing services ...

  # No additional containers needed - Ollama is external
  # Just ensure network access to api.nhatquangholding.com
```

### 7.3 Kubernetes (Production)

```yaml
# k8s/codegen-config.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: codegen-config
data:
  OLLAMA_API_URL: "https://api.nhatquangholding.com"
  OLLAMA_CODEGEN_MODEL: "qwen2.5-coder:14b"
  CODEGEN_DEFAULT_PROVIDER: "ollama"
  CODEGEN_FALLBACK_CHAIN: "ollama,claude,deepcode"

---
apiVersion: v1
kind: Secret
metadata:
  name: codegen-secrets
type: Opaque
stringData:
  ANTHROPIC_API_KEY: ""  # Set if Claude fallback needed
```

---

## 8. Monitoring & Observability

### 8.1 Metrics

| Metric | Type | Labels | Description |
|--------|------|--------|-------------|
| `codegen_requests_total` | Counter | `provider`, `status` | Total generation requests |
| `codegen_generation_duration_ms` | Histogram | `provider` | Generation latency |
| `codegen_tokens_used_total` | Counter | `provider` | Total tokens consumed |
| `codegen_provider_availability` | Gauge | `provider` | Provider health (1/0) |
| `codegen_fallback_count_total` | Counter | `from`, `to` | Fallback occurrences |

### 8.2 Logging

```python
# Structured logging format
{
    "timestamp": "2026-01-07T10:30:00Z",
    "level": "INFO",
    "service": "codegen",
    "event": "generation_complete",
    "provider": "ollama",
    "tokens": 2500,
    "duration_ms": 3200,
    "user_id": "uuid-here",
    "project_id": "uuid-here",
    "trace_id": "abc123"
}
```

### 8.3 Alerts

| Alert | Condition | Severity |
|-------|-----------|----------|
| `CodegenNoProviderAvailable` | All providers unavailable for 5min | Critical |
| `CodegenHighLatency` | p95 latency > 30s for 10min | Warning |
| `CodegenHighErrorRate` | Error rate > 10% for 5min | Warning |
| `OllamaUnreachable` | Ollama health check fails 3x | Critical |

---

## 9. Security Considerations

### 9.1 Input Validation

- Validate `app_blueprint` against JSON schema before processing
- Sanitize all string inputs to prevent injection
- Limit `app_blueprint` size to 100KB max
- Rate limit generation requests (10/min per user)

### 9.2 Output Sanitization

- Scan generated code for hardcoded secrets
- Validate generated code doesn't contain shell commands
- Check for malicious patterns (eval, exec, os.system)

### 9.3 API Security

- All endpoints require JWT authentication
- Log all generation requests with user context
- Implement audit trail for compliance

---

## 10. Sprint 45 Implementation Checklist

### Week 1 (Jan 6-10)

- [ ] Create package structure (`backend/app/services/codegen/`)
- [ ] Implement `base_provider.py` with Pydantic models
- [ ] Implement `provider_registry.py` with routing logic
- [ ] Implement `codegen_service.py` orchestrator
- [ ] Create API routes (`backend/app/api/routes/codegen.py`)
- [ ] Write unit tests for registry and service

### Week 2 (Jan 13-17)

- [ ] Implement `OllamaCodegenProvider` with Vietnamese prompts
- [ ] Create stub `ClaudeCodegenProvider` (is_available = false unless API key)
- [ ] Create stub `DeepCodeProvider` (is_available = always false)
- [ ] Add configuration settings to `config.py`
- [ ] Write integration test for Ollama-only boot
- [ ] Create smoke test script
- [ ] Demo with minimal AppBlueprint

### CTO Go Conditions Verification

| Condition | How to Verify | Status |
|-----------|---------------|--------|
| No DeepCode-first | `DeepCodeProvider.is_available == False` | Pending |
| CodegenProvider contract | 3 methods implemented in base class | Pending |
| Registry + routing | Integration test passes | Pending |
| 3 API endpoints | Smoke test passes | Pending |
| Ollama as primary | Providers list shows ollama.primary == true | Pending |
| Integration tests | `pytest tests/integration/test_codegen_*` passes | Pending |
| Ollama-only boot test | Smoke test script passes | Pending |

---

## Document Control

| Field | Value |
|-------|-------|
| **Version** | 1.0.0 |
| **Date** | December 23, 2025 |
| **Author** | Backend Lead + Architect |
| **Status** | APPROVED |
| **Sprint** | Sprint 45 (Jan 6-17, 2026) |
| **ADR** | [ADR-022](../01-ADRs/ADR-022-Multi-Provider-Codegen-Architecture.md) |
| **CEO Approval** | ✅ Dec 23, 2025 |
| **CTO Approval** | ✅ Dec 23, 2025 |
