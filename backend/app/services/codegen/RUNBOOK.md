# Codegen Service Runbook

**Sprint 45: Multi-Provider Codegen Architecture (EP-06)**
**Version**: 1.0.0
**Date**: December 23, 2025
**Author**: Backend Lead

---

## Overview

The Codegen Service provides AI-powered code generation using a multi-provider architecture. Primary provider is Ollama (self-hosted), with fallback support for Claude and DeepCode.

### Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    CodegenService                            │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐ │
│  │   Ollama    │←→│   Claude    │←→│     DeepCode        │ │
│  │  (Primary)  │  │  (Fallback) │  │  (Deferred Q2 2026) │ │
│  └─────────────┘  └─────────────┘  └─────────────────────┘ │
│              ↓                                               │
│        ProviderRegistry (Fallback Chain)                    │
└─────────────────────────────────────────────────────────────┘
```

---

## Configuration

### Environment Variables

```bash
# Ollama Configuration (Primary Provider)
CODEGEN_OLLAMA_URL=https://api.nqh.vn          # Cloudflare Tunnel endpoint
CODEGEN_MODEL_PRIMARY=qwen2.5-coder:32b-instruct-q4_K_M  # 92.7% HumanEval
CODEGEN_MODEL_FAST=qwen2.5:14b-instruct        # Fast autocomplete
CODEGEN_TIMEOUT=120                             # Timeout in seconds

# Claude Configuration (Fallback - Optional)
ANTHROPIC_API_KEY=sk-ant-...                   # Only if Claude fallback needed

# DeepCode (Deferred to Q2 2026)
# No configuration required - stub only
```

### Fallback Chain

Default order: `ollama` → `claude` → `deepcode`

The service automatically falls back to the next provider if:
- Current provider is unavailable
- Generation fails after 3 retries
- Provider returns NotImplementedError (stub)

---

## API Endpoints

### 1. List Providers

```http
GET /api/v1/codegen/providers
Authorization: Bearer <token>
```

Response:
```json
{
  "providers": [
    {"name": "ollama", "available": true, "primary": true, "fallback_position": 0},
    {"name": "claude", "available": false, "primary": false, "fallback_position": 1},
    {"name": "deepcode", "available": false, "primary": false, "fallback_position": 2}
  ],
  "fallback_chain": ["ollama", "claude", "deepcode"]
}
```

### 2. Generate Code

```http
POST /api/v1/codegen/generate
Authorization: Bearer <token>
Content-Type: application/json

{
  "app_blueprint": {
    "name": "TaskManager",
    "description": "Hệ thống quản lý công việc",
    "modules": [...]
  },
  "language": "python",
  "framework": "fastapi",
  "target_module": null,
  "preferred_provider": "ollama"
}
```

Response:
```json
{
  "success": true,
  "provider": "ollama",
  "files": {
    "app/models/task.py": "...",
    "app/schemas/task.py": "...",
    "app/api/routes/task.py": "..."
  },
  "tokens_used": 1500,
  "generation_time_ms": 3500,
  "metadata": {"model": "qwen2.5-coder:32b"}
}
```

### 3. Validate Code

```http
POST /api/v1/codegen/validate
Authorization: Bearer <token>
Content-Type: application/json

{
  "code": "def foo(): pass",
  "context": {"language": "python", "framework": "fastapi"}
}
```

### 4. Estimate Cost

```http
POST /api/v1/codegen/estimate
Authorization: Bearer <token>
Content-Type: application/json

{
  "app_blueprint": {...}
}
```

Response:
```json
{
  "estimates": {
    "ollama": {"estimated_tokens": 5000, "estimated_cost_usd": 0.005, "confidence": 0.85},
    "claude": {"estimated_tokens": 5000, "estimated_cost_usd": 0.09, "confidence": 0.7}
  },
  "recommended_provider": "ollama"
}
```

### 5. Health Check (No Auth)

```http
GET /api/v1/codegen/health
```

---

## Operations

### Starting the Service

The service starts automatically with the FastAPI app. Providers are registered during startup:

```python
# In codegen_service.py
service = CodegenService()  # Auto-registers all providers
```

### Checking Provider Health

```bash
# Via API
curl http://localhost:8000/api/v1/codegen/health

# Via script
python scripts/test_ollama_codegen.py
```

### Disabling a Provider

To disable a provider without code changes:

1. **Ollama**: Remove or set invalid `CODEGEN_OLLAMA_URL`
2. **Claude**: Remove `ANTHROPIC_API_KEY`
3. **DeepCode**: Always disabled (stub)

### Changing Fallback Order

```python
# In your startup code
from app.services.codegen import registry

registry.set_fallback_chain(['claude', 'ollama'])  # Claude-first
```

---

## Troubleshooting

### Issue: No Providers Available (503)

**Symptoms**: API returns 503 with "No codegen providers available"

**Diagnosis**:
```bash
curl http://localhost:8000/api/v1/codegen/health
```

**Solutions**:
1. Check Ollama server is running: `curl https://api.nqh.vn/api/tags`
2. Verify network connectivity to Ollama endpoint
3. Check `CODEGEN_OLLAMA_URL` is correct
4. Verify model is installed: should show `qwen2.5-coder:32b` in models list

### Issue: Generation Timeout

**Symptoms**: Request times out after 120s

**Diagnosis**:
- Model may be loading for first request
- Input too large
- Server overloaded

**Solutions**:
1. Increase `CODEGEN_TIMEOUT` to 180s for first request
2. Reduce blueprint size (fewer modules/entities)
3. Use `target_module` to generate incrementally
4. Check GPU memory usage on Ollama server

### Issue: Empty Files in Response

**Symptoms**: `files` dict is empty but `code` has content

**Diagnosis**: LLM output doesn't follow expected format

**Solutions**:
1. Check `code` field for raw output
2. Verify output contains `### FILE:` markers
3. Check model quality - may need different prompt
4. Report as bug with sample blueprint

### Issue: Vietnamese Characters Garbled

**Symptoms**: Vietnamese text shows as `????` or mojibake

**Diagnosis**: Encoding issue

**Solutions**:
1. Ensure `ensure_ascii=False` in JSON dumps
2. Check response Content-Type has `charset=utf-8`
3. Verify frontend handles UTF-8

---

## Monitoring

### Metrics to Watch

| Metric | Alert Threshold | Description |
|--------|----------------|-------------|
| Generation latency p95 | > 30s | Slow generation |
| Provider availability | < 1 | No providers available |
| Error rate | > 5% | High failure rate |
| Token usage | > 10K/request | Expensive generation |

### Logging

Key log messages:
```
INFO: Registered codegen provider: ollama
INFO: Selected provider from fallback: ollama
INFO: Generation complete: 5 files, 1500 tokens, 3500ms
WARNING: Preferred provider claude unavailable, trying fallback
ERROR: No codegen providers available
```

---

## Cost Management

### Cost Comparison

| Provider | Cost/1K Tokens | Monthly (10K requests) |
|----------|---------------|----------------------|
| Ollama | ~$0.001 | ~$50 (electricity) |
| Claude | ~$0.018 | ~$900 |
| GPT-4 | ~$0.030 | ~$1,500 |

### Cost Optimization Tips

1. **Use Ollama as primary** - 95% cost savings
2. **Use IR-based generation** - 96% token reduction vs full context
3. **Generate incrementally** - `target_module` for single module
4. **Cache results** - Store generated code for reuse
5. **Use smaller models** - `qwen2.5:14b` for simple tasks

---

## Security

### API Security

- All endpoints (except `/health`) require JWT authentication
- Rate limiting: 100 req/min per user
- Input validation via Pydantic schemas
- No secrets in generated code

### Provider Security

- Ollama: Internal network, Cloudflare Tunnel
- Claude: API key in environment only
- No code execution - generation only

---

## Appendix

### Sample Blueprint (Minimal)

```json
{
  "name": "MinimalApp",
  "description": "Demo tối giản",
  "modules": [
    {
      "name": "items",
      "entities": [
        {
          "name": "Item",
          "fields": [
            {"name": "id", "type": "uuid", "primary": true},
            {"name": "name", "type": "string", "max_length": 100}
          ]
        }
      ]
    }
  ]
}
```

### Sample Blueprint (Vietnamese SME)

See: `app/services/codegen/demos/vietnamese_sme_demo.py`

### Files Structure

```
app/services/codegen/
├── __init__.py           # Package exports
├── base_provider.py      # Abstract interface
├── provider_registry.py  # Registry pattern
├── codegen_service.py    # Main orchestrator
├── ollama_provider.py    # Ollama implementation
├── claude_provider.py    # Claude stub
├── deepcode_provider.py  # DeepCode stub
├── templates/            # Prompt templates
│   ├── base_templates.py
│   └── fastapi_templates.py
├── schemas/              # IR schemas
│   └── app_blueprint.py
├── demos/                # Demo blueprints
│   └── vietnamese_sme_demo.py
└── RUNBOOK.md           # This file
```

---

## Document Control

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0.0 | 2025-12-23 | Backend Lead | Initial version |
