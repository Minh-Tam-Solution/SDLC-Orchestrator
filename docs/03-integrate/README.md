# Stage 07: Integration & APIs
## External Integrations + Third-Party Connections

**Stage**: 07 - INTEGRATE
**Question**: How do we connect with others?
**Version**: 2.0.0
**Date**: December 23, 2025
**Status**: ✅ ACTIVE - EP-06 Codegen Integration Points
**Authority**: Backend Lead + CTO Approved
**Framework**: SDLC 5.1.1 Complete Lifecycle (10 Stages)
**Positioning**: Operating System for Software 3.0

**Changelog v2.0.0** (Dec 23, 2025):
- **EP-06 Codegen Integration**: Multi-Provider Gateway, Quality Gates Pipeline
- **Sprint 43 OPA Integration**: Policy Guards, SAST Validator
- **Sprint 44 Scanner Integration**: CrossReferenceValidator
- Added folder structure with api-contracts, third-party, integration-guides
- Added detailed integration architecture for Software 3.0 pivot

---

## Purpose

This stage manages API design, third-party integrations, and system interoperability. It answers the question: **"How do we connect SDLC Orchestrator with external systems?"**

**Key Integration Categories**:
1. **AI Provider Integrations** - Ollama, Claude, DeepCode
2. **VCS Integrations** - GitHub, GitLab (future)
3. **Policy Engine Integrations** - OPA, Custom validators
4. **Storage Integrations** - MinIO (S3), Evidence Vault
5. **Observability Integrations** - Prometheus, Grafana

---

## Folder Structure

```
03-integrate/
├── README.md (this file)
├── 01-api-contracts/
│   ├── codegen-api-contract.md        # EP-06 Codegen API (12 endpoints)
│   ├── evidence-api-contract.md       # Evidence Vault API
│   ├── gates-api-contract.md          # Gate Engine API
│   └── openapi/
│       └── openapi.yml                # Full OpenAPI 3.0 spec (64 endpoints)
├── 02-third-party/
│   ├── ollama-integration.md          # NQH AI Platform (qwen2.5-coder:32b)
│   ├── claude-integration.md          # Anthropic Claude API
│   ├── github-integration.md          # GitHub API (read-only bridge)
│   ├── opa-integration.md             # OPA Policy Engine
│   ├── minio-integration.md           # MinIO S3 Storage (AGPL-safe)
│   └── semgrep-integration.md         # Semgrep SAST Scanner
└── 03-integration-guides/
    ├── multi-provider-fallback.md     # Ollama → Claude → DeepCode
    ├── evidence-state-machine.md      # 8-state evidence lifecycle
    ├── quality-gates-pipeline.md      # 4-Gate validation pipeline
    └── vcr-workflow.md                # Version Control Review workflow
```

---

## Integration Architecture (Software 3.0)

### 3-Layer Integration Stack

```
┌─────────────────────────────────────────────────────────────────┐
│ LAYER 3: AI CODERS (External)                                   │
│ ┌──────────────┐  ┌──────────────┐  ┌──────────────┐           │
│ │ Cursor       │  │ Claude Code  │  │ Copilot      │           │
│ │ (IDE)        │  │ (CLI)        │  │ (IDE)        │           │
│ └──────────────┘  └──────────────┘  └──────────────┘           │
│         ↑                 ↑                 ↑                   │
│         └─────────────────┼─────────────────┘                   │
│                           │ (Governance API)                    │
└───────────────────────────┼─────────────────────────────────────┘
                            │
┌───────────────────────────┼─────────────────────────────────────┐
│ LAYER 2: SDLC ORCHESTRATOR (Our Platform)                       │
│                           │                                      │
│  ┌────────────────────────┴────────────────────────┐            │
│  │ Integration Gateway                              │            │
│  │ - Rate Limiting (1000 req/min)                  │            │
│  │ - API Key Auth / OAuth 2.0                      │            │
│  │ - Request/Response Logging                      │            │
│  └─────────────────────────────────────────────────┘            │
│                           │                                      │
│  ┌────────────────────────┴────────────────────────┐            │
│  │ Service Layer                                    │            │
│  │                                                  │            │
│  │  ┌──────────────┐  ┌──────────────┐  ┌────────┐ │            │
│  │  │ Codegen      │  │ Evidence     │  │ Gate   │ │            │
│  │  │ Service      │  │ Vault        │  │ Engine │ │            │
│  │  └──────────────┘  └──────────────┘  └────────┘ │            │
│  │                                                  │            │
│  └──────────────────────────────────────────────────┘            │
│                           │                                      │
└───────────────────────────┼─────────────────────────────────────┘
                            │
┌───────────────────────────┼─────────────────────────────────────┐
│ LAYER 1: THIRD-PARTY SERVICES (External)                        │
│                           │                                      │
│  ┌────────────────────────┴────────────────────────┐            │
│  │                                                  │            │
│  │  ┌──────────────┐  ┌──────────────┐  ┌────────┐ │            │
│  │  │ Ollama       │  │ Claude       │  │ OPA    │ │            │
│  │  │ (Primary)    │  │ (Fallback)   │  │ Policy │ │            │
│  │  └──────────────┘  └──────────────┘  └────────┘ │            │
│  │                                                  │            │
│  │  ┌──────────────┐  ┌──────────────┐  ┌────────┐ │            │
│  │  │ MinIO        │  │ GitHub       │  │Semgrep │ │            │
│  │  │ (S3)         │  │ (VCS)        │  │ (SAST) │ │            │
│  │  └──────────────┘  └──────────────┘  └────────┘ │            │
│  │                                                  │            │
│  └──────────────────────────────────────────────────┘            │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## EP-06 Codegen Integration Points

### Multi-Provider Gateway

| Provider | Endpoint | Model | Latency Target | Fallback Order |
|----------|----------|-------|----------------|----------------|
| **Ollama** | `api.nhatquangholding.com` | qwen2.5-coder:32b | <15s | Primary |
| **Claude** | `api.anthropic.com` | claude-sonnet-4-5-20250929 | <25s | Secondary |
| **DeepCode** | TBD (Q2 2026) | deepcode-v1 | TBD | Tertiary |

### Integration Code Example

```python
# backend/app/integrations/codegen_gateway.py

from typing import Optional
from app.core.config import settings

class CodegenProviderGateway:
    """
    Multi-provider integration gateway for code generation.

    AGPL SAFE: Network-only access, no SDK imports.
    """

    async def generate(
        self,
        ir_module: dict,
        provider: str = "auto"
    ) -> dict:
        """
        Route generation request to optimal provider.

        Args:
            ir_module: Parsed IR module specification
            provider: auto | ollama | claude | deepcode

        Returns:
            Generated code with provider metadata
        """
        providers = self._get_provider_chain(provider)

        for p in providers:
            try:
                return await self._call_provider(p, ir_module)
            except (ProviderTimeoutError, ProviderQuotaError):
                continue

        raise AllProvidersFailedError()

    async def _call_provider(self, provider: str, ir_module: dict) -> dict:
        """Call provider via HTTP (no SDK import)."""
        if provider == "ollama":
            return await self._call_ollama(ir_module)
        elif provider == "claude":
            return await self._call_claude(ir_module)
        elif provider == "deepcode":
            return await self._call_deepcode(ir_module)
```

### Quality Gates Integration

| Gate | Validator | Integration Type | Latency |
|------|-----------|------------------|---------|
| Gate 1 (Syntax) | ast.parse, ruff, tsc | In-process | <5s |
| Gate 2 (Security) | Semgrep | HTTP API | <10s |
| Gate 3 (Context) | Custom CTX validators | In-process | <10s |
| Gate 4 (Tests) | pytest (Dockerized) | Docker exec | <60s |

---

## Sprint 43 Integrations

### OPA Policy Guards

```yaml
Integration:
  Service: OPA (Open Policy Agent)
  Endpoint: http://opa:8181/v1/data/
  Protocol: HTTP REST (AGPL-safe)

API Contract:
  POST /v1/data/gates/{gate_id}/allow:
    Input: { policy: {}, evidence: [] }
    Output: { result: true/false, missing: [] }

Performance:
  Latency: <50ms (p95)
  Throughput: 10,000 req/min
```

### Semgrep SAST Integration

```yaml
Integration:
  Service: Semgrep
  Endpoint: semgrep --json (CLI) or HTTP API
  Protocol: CLI subprocess or HTTP

API Contract:
  Input: Source code files
  Output: JSON findings { severity, rule, location, message }

Performance:
  Latency: <10s for typical module
  Rule Packs: ai-codegen-security (custom)
```

---

## Sprint 44 Integrations

### CrossReferenceValidator

```yaml
Integration:
  Service: Internal validator
  Type: In-process (Python)

Validation Checks:
  - File reference existence
  - Import path validity
  - Entity cross-references

Performance:
  Latency: <2s for 100 files
```

---

## Third-Party Integration Summary

| Service | Type | License | Access Method | Sprint |
|---------|------|---------|---------------|--------|
| **Ollama** | AI Provider | MIT | HTTP API | Sprint 45 |
| **Claude** | AI Provider | Commercial | HTTP API | Sprint 45 |
| **OPA** | Policy Engine | Apache-2.0 | HTTP API | Sprint 43 |
| **MinIO** | Object Storage | AGPL v3 | S3 API (network-only) | MVP |
| **Grafana** | Dashboards | AGPL v3 | iframe embed | MVP |
| **Semgrep** | SAST Scanner | LGPL | CLI/HTTP | Sprint 43 |
| **GitHub** | VCS | Commercial | REST API | MVP |

---

## AGPL Containment Strategy

All AGPL-licensed components (MinIO, Grafana) are accessed via **network-only protocols**:

```
ALLOWED:
✅ HTTP/HTTPS API calls
✅ S3 protocol (PUT, GET, DELETE)
✅ iframe embedding (browser sandbox)
✅ PostgreSQL protocol (client libraries)

BANNED:
❌ SDK imports (from minio import Minio)
❌ Code linking (dynamic or static)
❌ Library dependencies (pip install minio)
```

**Enforcement**:
- Pre-commit hooks block AGPL imports
- CI/CD license scanner (Syft + Grype)
- Quarterly legal audit

---

## API Contract Standards

All integrations follow these standards:

### Request/Response Format

```yaml
Standard:
  Content-Type: application/json
  Accept: application/json
  Auth: Bearer {JWT} or X-API-Key

Error Response:
  {
    "error": {
      "code": "PROVIDER_TIMEOUT",
      "message": "Ollama provider timed out after 15s",
      "provider": "ollama",
      "retry_after": 5
    }
  }

Success Response:
  {
    "data": { ... },
    "meta": {
      "provider": "ollama",
      "latency_ms": 8500,
      "request_id": "uuid"
    }
  }
```

### Rate Limiting

| Tier | Requests/min | Codegen/hour | Burst |
|------|--------------|--------------|-------|
| Founder Plan | 100 | 50 | 10 |
| Standard | 500 | 200 | 50 |
| Enterprise | 2000 | 1000 | 200 |

---

## Related Documents

| Document | Description |
|----------|-------------|
| [System-Architecture-Document.md](../02-design/02-System-Architecture/System-Architecture-Document.md) | 5-layer architecture (v3.0.0) |
| [API-Specification.md](../01-planning/05-API-Design/API-Specification.md) | 64 endpoints (v3.1.0) |
| [Quality-Gates-Codegen-Specification.md](../02-design/14-Technical-Specs/Quality-Gates-Codegen-Specification.md) | Sprint 48 spec |
| [Policy-Guards-Design.md](../02-design/14-Technical-Specs/Policy-Guards-Design.md) | OPA integration |
| [EP-06-IR-Based-Codegen-Engine.md](../01-planning/02-Epics/EP-06-IR-Based-Codegen-Engine.md) | Epic specification |

---

## Next Steps (Q1 2026)

1. **Sprint 45**: Multi-Provider Codegen Architecture
2. **Sprint 46**: IR Processor Backend integration
3. **Sprint 47**: Vietnamese Domain Templates integration
4. **Sprint 48**: Quality Gates Pipeline integration
5. **Sprint 49**: Vietnam SME Pilot integrations
6. **Sprint 50**: Productization + GA readiness

---

**Last Updated**: December 23, 2025
**Owner**: Backend Lead + Integration Architect
**Status**: ✅ ACTIVE

---

## Document Summary

| Metric | Value |
|--------|-------|
| Third-Party Integrations | 7 services |
| API Endpoints | 64 total |
| AGPL Components | 2 (MinIO, Grafana) - network-only |
| EP-06 Codegen Endpoints | 12 new |
| Provider Fallback Chain | Ollama → Claude → DeepCode |
| Sprint Coverage | 43-50 |

---

*"Connect everything, compromise nothing."*
