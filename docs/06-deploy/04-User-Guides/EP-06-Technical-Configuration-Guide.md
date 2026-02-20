# EP-06 Technical Configuration Guide
## Provider Configuration & IR Schema Reference

---

**Document Information**

| Field | Value |
|-------|-------|
| **Version** | 1.0.0 |
| **Status** | ACTIVE |
| **Created** | December 24, 2025 |
| **Sprint** | Sprint 50 - EP-06 Productization |
| **Audience** | DevOps, Backend Developers |
| **Framework** | SDLC 6.1.0 |

---

## Table of Contents

1. [Provider Architecture](#1-provider-architecture)
2. [Environment Configuration](#2-environment-configuration)
3. [Model Lineup](#3-model-lineup)
4. [Provider Fallback Chain](#4-provider-fallback-chain)
5. [IR Schema Reference](#5-ir-schema-reference)
6. [Quality Gates Configuration](#6-quality-gates-configuration)
7. [Monitoring & Observability](#7-monitoring--observability)
8. [Session Management](#8-session-management)

---

## 1. Provider Architecture

### Multi-Provider Strategy

EP-06 uses a cascading provider architecture for reliability and cost optimization:

```
┌─────────────────────────────────────────────────────────────────────┐
│  PROVIDER CHAIN (Automatic Fallback)                                 │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  ┌──────────────┐    Timeout     ┌──────────────┐    Timeout        │
│  │   OLLAMA     │───────────────▶│    CLAUDE    │──────────────▶    │
│  │  (Primary)   │   or Error     │  (Fallback)  │   or Error        │
│  │  ~$50/mo     │                │  ~$1000/mo   │                   │
│  │  <15s p95    │                │  <25s p95    │                   │
│  └──────────────┘                └──────────────┘                   │
│         │                               │                            │
│         ▼                               ▼                            │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │              QUALITY GATE PIPELINE (4 Gates)                  │   │
│  │  Gate 1: Syntax → Gate 2: Security → Gate 3: Context → Tests │   │
│  └──────────────────────────────────────────────────────────────┘   │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

### Provider Registry

| Provider | Model | Latency (p95) | Cost/Month | Priority |
|----------|-------|---------------|------------|----------|
| **Ollama** | qwen3-coder:30b | <15s | ~$50 | Primary |
| **Claude** | claude-sonnet-4 | <25s | ~$1000 | Fallback 1 |
| **DeepCode** | TBD (Q2 2026) | TBD | TBD | Fallback 2 |

---

## 2. Environment Configuration

### Required Environment Variables

```bash
# =============================================================================
# EP-06 CODEGEN ENGINE - ENVIRONMENT CONFIGURATION
# Sprint 50 - Productization Baseline
# =============================================================================

# -----------------------------------------------------------------------------
# OLLAMA PROVIDER (Primary - Cost Efficient)
# -----------------------------------------------------------------------------
CODEGEN_OLLAMA_URL=http://api.nhatquangholding.com:11434
CODEGEN_MODEL_PRIMARY=qwen3-coder:30b
CODEGEN_MODEL_FAST=qwen3:8b
CODEGEN_MODEL_VIETNAMESE=qwen3:14b
CODEGEN_MODEL_CHAT=mistral-small3.2:24b-instruct-2506-q4_K_M
CODEGEN_TIMEOUT=120

# -----------------------------------------------------------------------------
# CLAUDE PROVIDER (Fallback - High Quality)
# -----------------------------------------------------------------------------
ANTHROPIC_API_KEY=sk-ant-api03-xxx
CLAUDE_MODEL=claude-sonnet-4-5-20250929
CLAUDE_TIMEOUT=60

# -----------------------------------------------------------------------------
# QUALITY GATES
# -----------------------------------------------------------------------------
QUALITY_GATE_SYNTAX_TIMEOUT=5
QUALITY_GATE_SECURITY_TIMEOUT=10
QUALITY_GATE_CONTEXT_TIMEOUT=10
QUALITY_GATE_TEST_TIMEOUT=60

# -----------------------------------------------------------------------------
# PILOT TRACKING
# -----------------------------------------------------------------------------
TTFV_TARGET_SECONDS=1800
SATISFACTION_TARGET=8
QUALITY_GATE_PASS_TARGET=0.95
PILOT_TARGET_COUNT=10
```

### Docker Compose Configuration

```yaml
# docker-compose.yml - EP-06 Codegen Services
version: '3.8'

services:
  # Main API Service
  api:
    build: ./backend
    environment:
      - CODEGEN_OLLAMA_URL=${CODEGEN_OLLAMA_URL}
      - CODEGEN_MODEL_PRIMARY=${CODEGEN_MODEL_PRIMARY}
      - ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}
    depends_on:
      - postgres
      - redis
    ports:
      - "8000:8000"

  # Quality Gate Workers
  quality-gate-worker:
    build: ./backend
    command: python -m app.jobs.quality_gate_worker
    environment:
      - CODEGEN_OLLAMA_URL=${CODEGEN_OLLAMA_URL}
    depends_on:
      - api
      - redis
```

---

## 3. Model Lineup

### Production Models (December 2025)

| Role | Model | Size | Context | Use Case |
|------|-------|------|---------|----------|
| **Primary Code** | qwen3-coder:30b | 18GB | 256K | Code generation, refactoring |
| **Fast Draft** | qwen3:8b | 5.2GB | 40K | Quick autocomplete, drafts |
| **Vietnamese** | qwen3:14b | 9.3GB | 40K | Vietnamese prompts, RAG |
| **Enterprise** | mistral-small3.2:24b | 15GB | 128K | JSON output, workflows |

### Model Selection Logic

```python
def select_model(task_type: str, language: str) -> str:
    """
    Select optimal model based on task type and language.

    Task Types:
    - code_generation: Full app generation
    - autocomplete: Fast tab completion
    - vietnamese_qa: Vietnamese Q&A
    - structured_output: JSON/workflow
    """
    if task_type == "code_generation":
        return settings.CODEGEN_MODEL_PRIMARY  # qwen3-coder:30b

    if task_type == "autocomplete":
        return settings.CODEGEN_MODEL_FAST  # qwen3:8b

    if language == "vi" or task_type == "vietnamese_qa":
        return settings.CODEGEN_MODEL_VIETNAMESE  # qwen3:14b

    if task_type == "structured_output":
        return settings.CODEGEN_MODEL_CHAT  # mistral-small3.2:24b

    # Default
    return settings.CODEGEN_MODEL_PRIMARY
```

---

## 4. Provider Fallback Chain

### Fallback Configuration

```python
# app/services/codegen/provider_registry.py

PROVIDER_CHAIN = [
    {
        "name": "ollama",
        "priority": 1,
        "timeout": 120,
        "retry_count": 2,
        "health_check_interval": 60,
    },
    {
        "name": "claude",
        "priority": 2,
        "timeout": 60,
        "retry_count": 1,
        "health_check_interval": 300,
    },
    {
        "name": "deepcode",
        "priority": 3,
        "timeout": 90,
        "retry_count": 1,
        "health_check_interval": 600,
        "enabled": False,  # Q2 2026 decision gate
    },
]
```

### Fallback Triggers

| Trigger | Action |
|---------|--------|
| **Timeout** (>120s) | Fallback to next provider |
| **5xx Error** | Retry once, then fallback |
| **Rate Limit** | Fallback immediately |
| **Model Unavailable** | Fallback immediately |
| **Health Check Failed** | Skip provider for 5 minutes |

---

## 5. IR Schema Reference

### App Blueprint Schema

```json
{
  "$schema": "https://sdlc-orchestrator.com/schemas/app-blueprint-v1.json",
  "type": "object",
  "required": ["name", "domain", "features", "scale"],
  "properties": {
    "name": {
      "type": "string",
      "description": "Application name (Vietnamese allowed)",
      "maxLength": 100
    },
    "domain": {
      "type": "string",
      "enum": ["fnb", "hospitality", "retail"],
      "description": "Business domain"
    },
    "features": {
      "type": "array",
      "items": {
        "type": "string",
        "enum": [
          "menu_management",
          "table_reservation",
          "order_management",
          "payment_integration",
          "inventory_management",
          "employee_management",
          "room_management",
          "booking_system",
          "checkin_checkout",
          "housekeeping",
          "product_catalog",
          "pos_system",
          "reporting"
        ]
      }
    },
    "scale": {
      "type": "string",
      "enum": ["micro", "small", "medium"],
      "description": "Business scale (1-5, 6-20, 21-50 employees)"
    }
  }
}
```

### IR Output Schema

```json
{
  "$schema": "https://sdlc-orchestrator.com/schemas/ir-output-v1.json",
  "type": "object",
  "required": ["models", "endpoints", "project"],
  "properties": {
    "models": {
      "type": "array",
      "description": "Database models (SQLAlchemy)",
      "items": {
        "type": "object",
        "properties": {
          "name": {"type": "string"},
          "fields": {"type": "array"},
          "relationships": {"type": "array"}
        }
      }
    },
    "endpoints": {
      "type": "array",
      "description": "API endpoints (FastAPI)",
      "items": {
        "type": "object",
        "properties": {
          "method": {"type": "string", "enum": ["GET", "POST", "PUT", "DELETE"]},
          "path": {"type": "string"},
          "request_schema": {"type": "object"},
          "response_schema": {"type": "object"}
        }
      }
    },
    "project": {
      "type": "object",
      "description": "Project metadata",
      "properties": {
        "name": {"type": "string"},
        "framework": {"type": "string", "enum": ["fastapi", "django", "flask"]},
        "database": {"type": "string", "enum": ["postgresql", "mysql", "sqlite"]}
      }
    }
  }
}
```

---

## 6. Quality Gates Configuration

### 4-Gate Pipeline

| Gate | Timeout | Blocking | Description |
|------|---------|----------|-------------|
| **Gate 1: Syntax** | 5s | Yes | `ast.parse`, `ruff check`, `tsc` |
| **Gate 2: Security** | 10s | Yes | Semgrep SAST, OWASP rules |
| **Gate 3: Context** | 10s | No | 5 contextual checks |
| **Gate 4: Tests** | 60s | Yes | Dockerized pytest |

### Gate Configuration

```python
# app/services/codegen/quality_gates.py

QUALITY_GATES = {
    "syntax": {
        "timeout": 5,
        "blocking": True,
        "tools": ["ast.parse", "ruff", "tsc"],
        "pass_threshold": 1.0,  # Must be 100%
    },
    "security": {
        "timeout": 10,
        "blocking": True,
        "tools": ["semgrep"],
        "rules": ["owasp-python", "ai-security"],
        "pass_threshold": 1.0,  # No critical/high vulnerabilities
    },
    "context": {
        "timeout": 10,
        "blocking": False,
        "checks": [
            "imports_valid",
            "dependencies_exist",
            "env_vars_documented",
            "api_contracts_match",
            "naming_conventions",
        ],
        "pass_threshold": 0.8,  # 4/5 checks must pass
    },
    "tests": {
        "timeout": 60,
        "blocking": True,
        "runner": "pytest",
        "container": "python:3.11-slim",
        "pass_threshold": 0.95,  # 95% tests must pass
    },
}
```

---

## 7. Monitoring & Observability

### Prometheus Metrics

```python
# Exposed at /metrics endpoint

# Generation metrics
codegen_generation_duration_seconds{provider="ollama", domain="fnb"}
codegen_generation_total{provider="ollama", status="success"}
codegen_generation_errors_total{provider="ollama", error_type="timeout"}

# Quality gate metrics
codegen_quality_gate_duration_seconds{gate="syntax"}
codegen_quality_gate_pass_rate{gate="security"}
codegen_quality_gate_failures_total{gate="tests", reason="assertion_error"}

# TTFV metrics
codegen_ttfv_seconds{domain="fnb", scale="micro"}
codegen_ttfv_target_met_total{domain="hospitality"}

# Provider health
codegen_provider_health{provider="ollama", status="healthy"}
codegen_provider_fallback_total{from="ollama", to="claude"}
```

### Grafana Dashboard

Dashboard JSON available at: `/monitoring/grafana/dashboards/ep06-codegen.json`

Key panels:
- **Generation Latency** (p50, p95, p99)
- **Quality Gate Pass Rate** (by gate)
- **TTFV Distribution** (histogram)
- **Provider Health** (status + fallback events)
- **Cost Tracking** (tokens used, estimated cost)

### Alerting Rules

```yaml
# alertmanager/rules/ep06.yml

groups:
  - name: ep06-codegen
    rules:
      - alert: HighGenerationLatency
        expr: histogram_quantile(0.95, codegen_generation_duration_seconds) > 30
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "EP-06 generation latency > 30s (p95)"

      - alert: LowQualityGatePassRate
        expr: codegen_quality_gate_pass_rate < 0.90
        for: 10m
        labels:
          severity: critical
        annotations:
          summary: "Quality gate pass rate < 90%"

      - alert: ProviderUnhealthy
        expr: codegen_provider_health{status="healthy"} == 0
        for: 2m
        labels:
          severity: critical
        annotations:
          summary: "All codegen providers unhealthy"
```

---

## 8. Session Management

### Onboarding Session Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│  ONBOARDING SESSION FLOW                                             │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  POST /onboarding/start          GET /onboarding/{id}                │
│         │                               │                            │
│         ▼                               ▼                            │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │           MODULE-LEVEL SESSION STORAGE (Singleton)            │   │
│  │                                                                │   │
│  │   _global_sessions: Dict[str, OnboardingSession]              │   │
│  │                                                                │   │
│  │   ┌─────────────┐  ┌─────────────┐  ┌─────────────┐          │   │
│  │   │ Session A   │  │ Session B   │  │ Session C   │          │   │
│  │   │ (user_1)    │  │ (user_2)    │  │ (user_3)    │          │   │
│  │   └─────────────┘  └─────────────┘  └─────────────┘          │   │
│  │                                                                │   │
│  └──────────────────────────────────────────────────────────────┘   │
│                                                                      │
│  LIFECYCLE:                                                          │
│  1. create_session() → Add to _global_sessions                      │
│  2. get_session(id) → Lookup from _global_sessions                  │
│  3. Session expires after 1 hour (cleanup job)                      │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

### Session Storage Strategy

| Environment | Storage | TTL | Persistence |
|-------------|---------|-----|-------------|
| **Development** | In-memory (module-level dict) | 1 hour | Process lifetime |
| **Production** | Redis (future) | 1 hour | Cluster-wide |

### Current Implementation (v1.0.0)

```python
# backend/app/services/codegen/onboarding/service.py

# Module-level session storage (singleton pattern)
# Ensures sessions persist across OnboardingService instances
_global_sessions: Dict[str, OnboardingSession] = {}

class OnboardingService:
    def __init__(self, locale: str = "vi"):
        # Use global session storage
        self._sessions = _global_sessions
```

### Limitations & Future Work

| Limitation | Impact | Future Solution |
|------------|--------|-----------------|
| In-memory storage | Lost on restart | Redis persistence |
| Single-process | No horizontal scaling | Redis cluster |
| No cleanup job | Memory growth | Background task |

### Troubleshooting

| Error | Cause | Resolution |
|-------|-------|------------|
| "Session not found" | Backend restarted | User must restart onboarding |
| "Session expired" | TTL exceeded | User must restart onboarding |
| Session data lost | Container recreated | Restart onboarding flow |

---

## Document Control

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | Dec 24, 2025 | Initial version - Sprint 50 |
| 1.0.1 | Dec 24, 2025 | Added Session Management section |

---

*EP-06 Technical Configuration Guide - Production-ready provider setup.*
