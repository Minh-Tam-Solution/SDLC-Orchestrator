# Productization Baseline Specification
## EP-06: Founder Plan GA Preparation | Sprint 50

**Status**: APPROVED
**Version**: 1.0.0
**Date**: December 23, 2025
**Author**: Product + Engineering
**Sprint**: Sprint 50 (Mar 17-28, 2026)
**Framework**: SDLC 6.1.0
**Dependency**: Sprint 49 (Pilot)

---

## 1. Overview

### 1.1 Purpose

This specification defines the productization baseline required to move EP-06 from pilot to General Availability (GA) for the Founder Plan ($99/team/month).

### 1.2 Sprint 50 Goals

1. **Document** end-to-end EP-06 workflow (repeatable)
2. **Observability** for generation runs (cost/latency/pass rate)
3. **Harden** provider configuration and defaults
4. **Prepare** DeepCode Q2 decision gate criteria

### 1.3 Success Gate

| Outcome | Criteria | Next Step |
|---------|----------|-----------|
| **EP-06 SUCCESS** | Pilot metrics met, productization complete | Founder Plan GA |
| **EP-06 PARTIAL** | Some gaps, needs hardening | Sprint 51-52 hardening |
| **EP-06 FAIL** | Major issues, strategy pivot needed | Re-evaluate |

---

## 2. Documentation Suite

### 2.1 User Documentation

```
docs/user-guides/ep-06/
├── README.md                      # Overview
├── getting-started.md            # Quick start guide
├── onboarding-guide.md           # Step-by-step onboarding
├── domain-templates/
│   ├── restaurant.md             # F&B template guide
│   ├── hotel.md                  # Hotel template guide
│   └── retail.md                 # Retail template guide
├── generated-code/
│   ├── project-structure.md      # Understanding generated code
│   ├── customization.md          # How to modify
│   └── deployment.md             # Deployment options
└── troubleshooting.md            # Common issues & fixes
```

### 2.2 User Guide Content (Vietnamese)

```markdown
# Hướng dẫn sử dụng EP-06
## Tạo ứng dụng cho doanh nghiệp SME

### Bước 1: Chọn ngành nghề
Chọn một trong 3 ngành:
- 🍜 Nhà hàng / Quán ăn
- 🏨 Khách sạn / Homestay
- 🏪 Cửa hàng bán lẻ

### Bước 2: Trả lời câu hỏi
Trả lời 5-10 câu hỏi về doanh nghiệp của bạn:
- Tên doanh nghiệp
- Các tính năng cần thiết
- Quy mô hoạt động

### Bước 3: Xem trước và xác nhận
Kiểm tra bản thiết kế (IR):
- Các module sẽ được tạo
- Các entity và field
- Số lượng API endpoints

### Bước 4: Tạo ứng dụng
Nhấn "Tạo ứng dụng" và chờ 1-3 phút.
Kết quả:
- Backend FastAPI hoàn chỉnh
- Database schema
- API documentation

### Bước 5: Triển khai
Tải xuống code hoặc deploy trực tiếp lên cloud.
```

### 2.3 Technical Documentation

```
docs/technical/ep-06/
├── architecture.md               # System architecture
├── provider-configuration.md     # Provider setup guide
├── ir-schema-reference.md        # IR schema documentation
├── api-reference.md              # API endpoints
├── quality-gates.md              # Validation pipeline
└── runbooks/
    ├── disable-provider.md       # How to disable providers
    ├── rollback.md               # Rollback procedure
    └── incident-response.md      # Incident handling
```

---

## 3. Observability Dashboard

### 3.1 Metrics to Track

| Category | Metric | Aggregation | Alert Threshold |
|----------|--------|-------------|-----------------|
| **Volume** | Generation requests/hour | Sum | >100/hour warn |
| **Latency** | Generation time (p50, p95, p99) | Percentile | p95 >30s alert |
| **Quality** | Gate pass rate | Percentage | <90% alert |
| **Cost** | Tokens used per generation | Avg | >10K tokens warn |
| **Errors** | Generation failures | Rate | >5% alert |

### 3.2 Dashboard Layout

```
┌─────────────────────────────────────────────────────────────────────┐
│                    EP-06 CODEGEN DASHBOARD                           │
├─────────────────────────────────────────────────────────────────────┤
│  Summary (Last 24h)                                                  │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐                │
│  │ 156      │ │ 2.3s     │ │ 97.4%    │ │ $12.50   │                │
│  │ Requests │ │ p95 Lat  │ │ Pass Rate│ │ Cost     │                │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘                │
├─────────────────────────────────────────────────────────────────────┤
│  Generation Latency (Last 7 Days)                                    │
│  [Line chart: p50, p95, p99 over time]                              │
├─────────────────────────────────────────────────────────────────────┤
│  Quality Gate Pass Rate                                              │
│  [Stacked bar: syntax/security/arch/tests per day]                  │
├─────────────────────────────────────────────────────────────────────┤
│  Provider Usage                                                      │
│  [Pie chart: Ollama 95%, Claude 4%, DeepCode 1%]                    │
├─────────────────────────────────────────────────────────────────────┤
│  Cost Breakdown                                                      │
│  [Bar chart: Daily cost by provider]                                │
└─────────────────────────────────────────────────────────────────────┘
```

### 3.3 Grafana Dashboard Definition

```yaml
# infrastructure/grafana/dashboards/ep06-codegen.json

apiVersion: 1
providers:
  - name: 'EP-06 Codegen'
    type: file
    options:
      path: /etc/grafana/dashboards/ep06

panels:
  - title: "Generation Requests"
    type: graph
    datasource: prometheus
    targets:
      - expr: sum(rate(codegen_requests_total[5m])) * 60
        legendFormat: "Requests/min"

  - title: "Generation Latency"
    type: graph
    datasource: prometheus
    targets:
      - expr: histogram_quantile(0.50, codegen_generation_duration_seconds_bucket)
        legendFormat: "p50"
      - expr: histogram_quantile(0.95, codegen_generation_duration_seconds_bucket)
        legendFormat: "p95"
      - expr: histogram_quantile(0.99, codegen_generation_duration_seconds_bucket)
        legendFormat: "p99"

  - title: "Quality Gate Pass Rate"
    type: gauge
    datasource: prometheus
    targets:
      - expr: |
          sum(codegen_gate_passed_total) /
          sum(codegen_gate_total) * 100

  - title: "Provider Distribution"
    type: piechart
    datasource: prometheus
    targets:
      - expr: sum by (provider) (codegen_requests_total)
```

### 3.4 Prometheus Metrics

```python
# backend/app/services/codegen/metrics.py

from prometheus_client import Counter, Histogram, Gauge

# Request metrics
codegen_requests_total = Counter(
    'codegen_requests_total',
    'Total code generation requests',
    ['provider', 'domain', 'status']
)

codegen_generation_duration_seconds = Histogram(
    'codegen_generation_duration_seconds',
    'Code generation duration',
    ['provider'],
    buckets=[0.5, 1, 2, 3, 5, 10, 30, 60]
)

codegen_tokens_used = Counter(
    'codegen_tokens_used_total',
    'Total tokens consumed',
    ['provider']
)

# Quality gate metrics
codegen_gate_total = Counter(
    'codegen_gate_total',
    'Total quality gate executions',
    ['gate']
)

codegen_gate_passed = Counter(
    'codegen_gate_passed_total',
    'Quality gates passed',
    ['gate']
)

# Provider metrics
codegen_provider_available = Gauge(
    'codegen_provider_available',
    'Provider availability (1=available, 0=unavailable)',
    ['provider']
)

# Cost metrics
codegen_cost_usd = Counter(
    'codegen_cost_usd_total',
    'Estimated cost in USD',
    ['provider']
)
```

---

## 4. Configuration Hardening

### 4.1 Provider Defaults

```yaml
# config/codegen.yaml (production defaults)

codegen:
  # Default provider - Ollama for cost efficiency
  default_provider: ollama

  # Fallback chain when preferred provider unavailable
  fallback_chain:
    - ollama
    - claude
    # deepcode: disabled until Q2 2026

  # Provider configurations
  providers:
    ollama:
      enabled: true
      base_url: "${OLLAMA_API_URL:https://api.nhatquangholding.com}"
      model: "${OLLAMA_MODEL:qwen3-coder:30b}"
      timeout_seconds: 60
      max_retries: 3
      # Rate limiting
      rate_limit:
        requests_per_minute: 30
        tokens_per_minute: 50000

    claude:
      enabled: false  # Enable only if API key configured
      api_key: "${ANTHROPIC_API_KEY:}"
      model: "claude-3-sonnet-20240229"
      timeout_seconds: 120
      max_retries: 2
      # Cost controls
      max_tokens_per_request: 8000
      monthly_budget_usd: 100

    deepcode:
      enabled: false  # Deferred to Q2 2026
      status: "deferred"

  # Quality gates
  quality_gates:
    enabled: true
    gates:
      - syntax
      - security
      - architecture
    # Disable tests gate for MVP (optional)
    # - tests

  # Generation limits
  limits:
    max_files_per_generation: 50
    max_lines_per_file: 1000
    max_generation_time_seconds: 120
    max_ir_size_bytes: 102400  # 100KB

  # Caching
  cache:
    enabled: true
    ttl_seconds: 3600  # 1 hour
    max_entries: 1000
```

### 4.2 Environment Variables

```bash
# .env.production

# Ollama (Primary)
OLLAMA_API_URL=https://api.nhatquangholding.com
OLLAMA_MODEL=qwen3-coder:30b

# Claude (Fallback - optional)
ANTHROPIC_API_KEY=  # Set to enable

# DeepCode (Disabled)
DEEPCODE_ENABLED=false

# Quality Gates
QUALITY_GATES_ENABLED=true
QUALITY_GATES_STRICT=false  # false = warn only, true = fail

# Observability
METRICS_ENABLED=true
METRICS_PORT=9090

# Rate Limits (per user)
RATE_LIMIT_GENERATIONS_PER_HOUR=10
RATE_LIMIT_TOKENS_PER_DAY=100000
```

### 4.3 Feature Flags

```python
# backend/app/core/feature_flags.py

from pydantic_settings import BaseSettings

class CodegenFeatureFlags(BaseSettings):
    """Feature flags for EP-06 Codegen."""

    # Provider flags
    CODEGEN_OLLAMA_ENABLED: bool = True
    CODEGEN_CLAUDE_ENABLED: bool = False
    CODEGEN_DEEPCODE_ENABLED: bool = False

    # Feature flags
    CODEGEN_CACHING_ENABLED: bool = True
    CODEGEN_QUALITY_GATES_ENABLED: bool = True
    CODEGEN_COST_TRACKING_ENABLED: bool = True

    # Vietnamese templates
    CODEGEN_TEMPLATES_RESTAURANT: bool = True
    CODEGEN_TEMPLATES_HOTEL: bool = True
    CODEGEN_TEMPLATES_RETAIL: bool = True

    # Pilot mode (extra logging)
    CODEGEN_PILOT_MODE: bool = False

    class Config:
        env_prefix = ""
```

---

## 5. DeepCode Q2 Decision Gate

### 5.1 Evaluation Criteria

| Criteria | Threshold | Data Source |
|----------|-----------|-------------|
| EP-06 pilot success | ≥8/10 satisfaction | Pilot metrics |
| Ollama cost efficiency | <$50/mo per project | Cost tracking |
| Quality gate pass rate | ≥95% | System metrics |
| Ollama latency | <3s p95 | System metrics |
| User demand for DeepCode | >20% request it | User feedback |

### 5.2 Decision Options

**Option A: Proceed with DeepCode (Q2 2026)**
- Condition: All criteria met + user demand
- Action: Allocate $16K budget, start integration

**Option B: Defer DeepCode (Q3 2026)**
- Condition: Ollama sufficient, no demand
- Action: Focus on Ollama optimization, revisit Q3

**Option C: Cancel DeepCode**
- Condition: EP-06 fails, strategy pivot
- Action: Reallocate budget to other priorities

### 5.3 Decision Document Template

```markdown
# EP-06 DeepCode Decision Gate
## Date: [End of Q1 2026]

### Summary
[One paragraph summary of decision]

### Metrics Review

| Criteria | Target | Actual | Status |
|----------|--------|--------|--------|
| Pilot satisfaction | ≥8/10 | [X/10] | [✅/❌] |
| Cost efficiency | <$50/mo | [$X/mo] | [✅/❌] |
| Quality gate pass | ≥95% | [X%] | [✅/❌] |
| Latency p95 | <3s | [Xs] | [✅/❌] |
| User demand | >20% | [X%] | [✅/❌] |

### Decision
[Option A / B / C]

### Rationale
[2-3 paragraphs explaining decision]

### Next Steps
1. [Action 1]
2. [Action 2]
3. [Action 3]

### Approvals
- [ ] CTO: _______________
- [ ] CEO: _______________
- [ ] Date: _______________
```

---

## 6. Year 1 Target Validation

### 6.1 Pipeline Metrics (End of Sprint 50)

| Metric | Target | Status |
|--------|--------|--------|
| Vietnam SME pipeline | 25 teams interested | TBD |
| Founder Plan conversions | 5 paid teams | TBD |
| TTFV (median) | <30 min | TBD |
| Satisfaction | 8/10 average | TBD |

### 6.2 Revenue Projection Validation

```
Year 1 Target: $86K - $144K ARR

Breakdown:
- Founder Plan (60%): 18-30 teams × $99/mo × 12 = $21K - $36K
- Standard/Pro (30%): 9-15 teams × $30/user × 10 users × 12 = $32K - $54K
- Enterprise (10%): 3-5 teams × custom = $33K - $54K

Validation at Sprint 50:
- At least 5 Founder Plan teams signed
- At least 25 in qualified pipeline
- Clear path to Year 1 target
```

---

## 7. Sprint 50 Deliverables

### 7.1 Documentation (P0)

- [ ] User Guide: Vietnamese onboarding flow
- [ ] Technical Guide: Provider configuration
- [ ] Troubleshooting Guide: Common issues
- [ ] Runbook: Disable provider procedure

### 7.2 Observability (P1)

- [ ] Grafana dashboard deployed
- [ ] Prometheus metrics implemented
- [ ] Alerting rules configured
- [ ] Cost tracking dashboard

### 7.3 Configuration (P0)

- [ ] Production config hardened
- [ ] Feature flags implemented
- [ ] Rate limiting configured
- [ ] Provider fallback tested

### 7.4 Decision Gate (P1)

- [ ] DeepCode criteria documented
- [ ] Decision template prepared
- [ ] Data collection automated

---

## 8. Sprint 50 Implementation Checklist

### Week 1 (Mar 17-21)

- [ ] Create user documentation (Vietnamese)
- [ ] Implement Prometheus metrics
- [ ] Deploy Grafana dashboard
- [ ] Harden production config
- [ ] Test provider fallback

### Week 2 (Mar 24-28)

- [ ] Complete technical documentation
- [ ] Configure alerting rules
- [ ] Implement cost tracking
- [ ] Prepare DeepCode decision doc
- [ ] Final review with CTO
- [ ] EP-06 retrospective

---

## Document Control

| Field | Value |
|-------|-------|
| **Version** | 1.0.0 |
| **Date** | December 23, 2025 |
| **Author** | Product + Engineering |
| **Status** | APPROVED |
| **Sprint** | Sprint 50 (Mar 17-28, 2026) |
| **Dependency** | Sprint 49 |
