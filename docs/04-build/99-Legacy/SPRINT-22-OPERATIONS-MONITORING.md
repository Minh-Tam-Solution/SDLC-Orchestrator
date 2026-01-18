# Sprint 22: Operations & Monitoring
## SDLC Orchestrator - Notifications, Metrics, Dashboards, Trends

**Version**: 1.0.0  
**Date**: December 2, 2025  
**Status**: ✅ PLANNED - Ready for Execution  
**Authority**: CTO + CPO Approved  
**Foundation**: Sprint 21 Complete, Gate G3 Readiness 96%  
**Framework**: SDLC 5.1.3.1 Complete Lifecycle  

**Sprint Duration**: 5 days (Dec 9-13, 2025)  
**Sprint Goal**: Implement notifications, monitoring, and compliance operations enhancements for production readiness.  

---

## 🎯 SPRINT OVERVIEW

### Context

Sprint 21 delivered Compliance Scanner with AI Recommendations. Sprint 22 focuses on **operations and monitoring** to enable production deployment and Gate G3 approval.

**Why This Sprint**:
- Notifications critical for user engagement (violation alerts)
- Monitoring essential for production operations (metrics, dashboards)
- Compliance trends provide value to users (score history, violation patterns)
- Policy templates reduce onboarding friction (pre-built packs)

**Gate G3 Impact**: 
- Notifications: Required for production operations
- Monitoring: Required for production observability
- Trends: Enhances user value proposition
- Templates: Reduces time-to-value

---

## 📋 DAY-BY-DAY BREAKDOWN

### Day 1: Slack/Email Notifications

**Goal**: Implement real Slack and email notifications for compliance violations and scan completion.

**Duration**: 8 hours  
**Owner**: Backend Lead (6h) + DevOps Lead (2h)  

#### Tasks

| # | Task | File | Est. | Owner |
|---|------|------|------|-------|
| 1.1 | Implement Slack webhook integration | `notification_service.py` | 2h | BE |
| 1.2 | Implement email sending (SMTP/SendGrid) | `notification_service.py` | 2h | BE |
| 1.3 | Create notification templates | `templates/notifications/` | 1h | BE |
| 1.4 | Add notification preferences API | `routes/notifications.py` | 1h | BE |
| 1.5 | Test Slack notifications (real webhook) | Test scripts | 1h | DevOps |
| 1.6 | Test email notifications (real SMTP) | Test scripts | 1h | DevOps |

#### Implementation Details

**1. Slack Webhook Integration**

```python
# backend/app/services/notification_service.py

async def _send_slack_notification(
    self,
    webhook_url: str,
    message: str,
    channel: str = "#compliance",
    username: str = "SDLC Orchestrator",
) -> bool:
    """
    Send notification to Slack via webhook.
    
    Args:
        webhook_url: Slack webhook URL (from user settings)
        message: Notification message (Markdown supported)
        channel: Slack channel (optional, defaults to #compliance)
        username: Bot username (optional)
    
    Returns:
        True if sent successfully, False otherwise
    """
    payload = {
        "text": message,
        "channel": channel,
        "username": username,
        "icon_emoji": ":shield:",
    }
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                webhook_url,
                json=payload,
                timeout=10.0,
            )
            response.raise_for_status()
            return True
    except Exception as e:
        logger.error(f"Slack notification failed: {e}")
        return False
```

**2. Email Sending (SMTP/SendGrid)**

```python
# backend/app/services/notification_service.py

async def _send_email_notification(
    self,
    to_email: str,
    subject: str,
    html_body: str,
    text_body: str = None,
) -> bool:
    """
    Send email notification via SMTP or SendGrid.
    
    Args:
        to_email: Recipient email address
        subject: Email subject
        html_body: HTML email body
        text_body: Plain text email body (optional)
    
    Returns:
        True if sent successfully, False otherwise
    """
    # Use SendGrid if API key configured, otherwise SMTP
    if settings.SENDGRID_API_KEY:
        return await self._send_via_sendgrid(to_email, subject, html_body, text_body)
    else:
        return await self._send_via_smtp(to_email, subject, html_body, text_body)
```

**3. Notification Templates**

```python
# backend/app/templates/notifications/violation_alert.html

"""
Violation Alert Email Template

Variables:
- project_name: Project name
- violation_count: Number of violations
- critical_count: Number of critical violations
- compliance_score: Current compliance score
- violations: List of violations (type, severity, location)
- dashboard_url: Link to compliance dashboard
"""

# Example template structure
TEMPLATES = {
    "violation_alert": {
        "subject": "🚨 Compliance Violations Detected in {{project_name}}",
        "html": "templates/notifications/violation_alert.html",
        "text": "templates/notifications/violation_alert.txt",
    },
    "scan_completed": {
        "subject": "✅ Compliance Scan Completed for {{project_name}}",
        "html": "templates/notifications/scan_completed.html",
        "text": "templates/notifications/scan_completed.txt",
    },
}
```

#### Deliverables

- ✅ Real Slack notifications working (tested with real webhook)
- ✅ Real email notifications working (tested with real SMTP/SendGrid)
- ✅ 3+ notification templates (violation alert, scan completed, budget exceeded)
- ✅ Notification preferences API (`GET/PUT /api/v1/notifications/preferences`)
- ✅ Integration tests (5+ tests for notifications)

#### Success Criteria

- [ ] Slack webhook sends real messages to #compliance channel
- [ ] Email sending works via SMTP and SendGrid
- [ ] Templates render correctly with real data
- [ ] User preferences saved and applied
- [ ] Integration tests pass (100%)

---

### Day 2: Prometheus Metrics

**Goal**: Add comprehensive Prometheus metrics for compliance scans, AI usage, and job queue.

**Duration**: 8 hours  
**Owner**: Backend Lead  

#### Tasks

| # | Task | File | Est. | Owner |
|---|------|------|------|-------|
| 2.1 | Create metrics module | `core/metrics.py` | 2h | BE |
| 2.2 | Add compliance scan metrics | `services/compliance_scanner.py` | 2h | BE |
| 2.3 | Add AI usage metrics | `services/ai_recommendation_service.py` | 2h | BE |
| 2.4 | Add job queue metrics | `jobs/compliance_scan.py` | 1h | BE |
| 2.5 | Create `/metrics` endpoint | `main.py` | 1h | BE |

#### Implementation Details

**1. Metrics Module**

```python
# backend/app/core/metrics.py

from prometheus_client import Counter, Histogram, Gauge, generate_latest

# Compliance Metrics
compliance_scans_total = Counter(
    "compliance_scans_total",
    "Total number of compliance scans",
    ["project_id", "status"],  # status: completed, failed, timeout
)

compliance_scan_duration_seconds = Histogram(
    "compliance_scan_duration_seconds",
    "Compliance scan duration in seconds",
    ["project_id"],
    buckets=[1, 5, 10, 30, 60, 120, 300],  # 1s to 5min
)

compliance_score = Gauge(
    "compliance_score",
    "Current compliance score (0-100)",
    ["project_id"],
)

violations_count = Gauge(
    "violations_count",
    "Number of violations by severity",
    ["project_id", "severity"],  # severity: critical, high, medium, low, info
)

# AI Metrics
ai_requests_total = Counter(
    "ai_requests_total",
    "Total AI requests by provider and model",
    ["provider", "model"],  # provider: ollama, claude, gpt4, rule_based
)

ai_tokens_used = Counter(
    "ai_tokens_used",
    "Total tokens used by provider and model",
    ["provider", "model"],
)

ai_cost_usd = Counter(
    "ai_cost_usd",
    "Total AI cost in USD by provider",
    ["provider"],
)

ai_latency_seconds = Histogram(
    "ai_latency_seconds",
    "AI request latency in seconds",
    ["provider", "model"],
    buckets=[0.05, 0.1, 0.25, 0.5, 1.0, 2.0, 5.0],
)

# Job Queue Metrics
scan_jobs_total = Counter(
    "scan_jobs_total",
    "Total scan jobs by status and priority",
    ["status", "priority"],  # status: queued, running, completed, failed
)

scan_job_duration_seconds = Histogram(
    "scan_job_duration_seconds",
    "Scan job duration in seconds",
    ["status"],
    buckets=[10, 30, 60, 120, 300, 600],  # 10s to 10min
)

scan_job_retries_total = Counter(
    "scan_job_retries_total",
    "Total scan job retries",
    ["status"],
)
```

**2. Metrics Endpoint**

```python
# backend/app/main.py

from app.core.metrics import generate_latest
from prometheus_client import CONTENT_TYPE_LATEST

@app.get("/metrics")
async def metrics():
    """
    Prometheus metrics endpoint.
    
    Returns:
        Prometheus metrics in text format
    """
    return Response(
        content=generate_latest(),
        media_type=CONTENT_TYPE_LATEST,
    )
```

#### Deliverables

- ✅ Metrics module created (`core/metrics.py`)
- ✅ Compliance metrics instrumented (scans, score, violations)
- ✅ AI metrics instrumented (requests, tokens, cost, latency)
- ✅ Job queue metrics instrumented (jobs, duration, retries)
- ✅ `/metrics` endpoint working (Prometheus format)

#### Success Criteria

- [ ] All metrics exposed on `/metrics` endpoint
- [ ] Metrics scraped by Prometheus (tested)
- [ ] Metrics labels correct (project_id, status, severity, etc.)
- [ ] Metrics values accurate (tested with real scans)

---

### Day 3: Grafana Dashboards

**Goal**: Create 4 Grafana dashboards for compliance monitoring and operations.

**Duration**: 8 hours  
**Owner**: DevOps Lead (6h) + Backend Lead (2h)  

#### Tasks

| # | Task | File | Est. | Owner |
|---|------|------|------|-------|
| 3.1 | Create compliance scans dashboard | `grafana/dashboards/compliance-scans.json` | 2h | DevOps |
| 3.2 | Create AI usage dashboard | `grafana/dashboards/ai-usage.json` | 2h | DevOps |
| 3.3 | Create job queue dashboard | `grafana/dashboards/job-queue.json` | 1h | DevOps |
| 3.4 | Create violations dashboard | `grafana/dashboards/violations.json` | 1h | DevOps |
| 3.5 | Test dashboards with real data | Test scripts | 1h | DevOps |
| 3.6 | Document dashboard usage | `docs/06-Operations-Maintenance/Grafana-Dashboards.md` | 1h | DevOps |

#### Dashboard Specifications

**1. Compliance Scans Dashboard**

```json
{
  "dashboard": {
    "title": "Compliance Scans",
    "panels": [
      {
        "title": "Scan Count Over Time",
        "type": "graph",
        "targets": [
          {
            "expr": "rate(compliance_scans_total[5m])",
            "legendFormat": "{{status}}"
          }
        ]
      },
      {
        "title": "Compliance Score Trend",
        "type": "graph",
        "targets": [
          {
            "expr": "compliance_score",
            "legendFormat": "{{project_id}}"
          }
        ]
      },
      {
        "title": "Violations by Severity",
        "type": "piechart",
        "targets": [
          {
            "expr": "violations_count",
            "legendFormat": "{{severity}}"
          }
        ]
      },
      {
        "title": "Top Projects by Violations",
        "type": "table",
        "targets": [
          {
            "expr": "topk(10, sum by (project_id) (violations_count))"
          }
        ]
      }
    ]
  }
}
```

**2. AI Usage Dashboard**

```json
{
  "dashboard": {
    "title": "AI Usage & Costs",
    "panels": [
      {
        "title": "AI Requests by Provider",
        "type": "bargraph",
        "targets": [
          {
            "expr": "ai_requests_total",
            "legendFormat": "{{provider}} - {{model}}"
          }
        ]
      },
      {
        "title": "AI Cost per Provider",
        "type": "graph",
        "targets": [
          {
            "expr": "rate(ai_cost_usd[1h])",
            "legendFormat": "{{provider}}"
          }
        ]
      },
      {
        "title": "Token Usage",
        "type": "graph",
        "targets": [
          {
            "expr": "rate(ai_tokens_used[1h])",
            "legendFormat": "{{provider}} - {{model}}"
          }
        ]
      },
      {
        "title": "Budget Status",
        "type": "gauge",
        "targets": [
          {
            "expr": "sum(ai_cost_usd) / 500 * 100",
            "legendFormat": "Budget Used (%)"
          }
        ]
      }
    ]
  }
}
```

#### Deliverables

- ✅ 4 Grafana dashboards created (JSON files)
- ✅ Dashboard documentation complete
- ✅ Dashboards tested with real data
- ✅ Dashboard access configured (read-only for users)

#### Success Criteria

- [ ] All dashboards load in Grafana
- [ ] All panels display data correctly
- [ ] Dashboards auto-refresh (30s interval)
- [ ] Dashboard documentation complete

---

### Day 4: Compliance Trend Charts (Frontend)

**Goal**: Create interactive compliance trend charts in the frontend dashboard.

**Duration**: 8 hours  
**Owner**: Frontend Lead  

#### Tasks

| # | Task | File | Est. | Owner |
|---|------|------|------|-------|
| 4.1 | Create compliance score history chart | `components/compliance/ComplianceScoreChart.tsx` | 2h | FE |
| 4.2 | Create violation trends chart | `components/compliance/ViolationTrendChart.tsx` | 2h | FE |
| 4.3 | Create AI usage chart | `components/compliance/AIUsageChart.tsx` | 2h | FE |
| 4.4 | Integrate charts into CompliancePage | `pages/CompliancePage.tsx` | 1h | FE |
| 4.5 | Add time range selector | `components/compliance/TimeRangeSelector.tsx` | 1h | FE |

#### Implementation Details

**1. Compliance Score History Chart**

```typescript
// frontend/web/src/components/compliance/ComplianceScoreChart.tsx

import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { useScanHistory } from '@/api/compliance';

interface ComplianceScoreChartProps {
  projectId: string;
  timeRange: '7d' | '30d' | '90d' | 'all';
}

export function ComplianceScoreChart({ projectId, timeRange }: ComplianceScoreChartProps) {
  const { data: scanHistory, isLoading } = useScanHistory(projectId, { timeRange });

  if (isLoading) return <div>Loading chart...</div>;

  const chartData = scanHistory?.map(scan => ({
    date: new Date(scan.scanned_at).toLocaleDateString(),
    score: scan.compliance_score,
    violations: scan.violations_count,
    warnings: scan.warnings_count,
  })) || [];

  return (
    <ResponsiveContainer width="100%" height={300}>
      <LineChart data={chartData}>
        <CartesianGrid strokeDasharray="3 3" />
        <XAxis dataKey="date" />
        <YAxis domain={[0, 100]} />
        <Tooltip />
        <Legend />
        <Line type="monotone" dataKey="score" stroke="#8884d8" name="Compliance Score" />
        <Line type="monotone" dataKey="violations" stroke="#ff7300" name="Violations" />
        <Line type="monotone" dataKey="warnings" stroke="#82ca9d" name="Warnings" />
      </LineChart>
    </ResponsiveContainer>
  );
}
```

**2. Time Range Selector**

```typescript
// frontend/web/src/components/compliance/TimeRangeSelector.tsx

import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';

interface TimeRangeSelectorProps {
  value: '7d' | '30d' | '90d' | 'all';
  onChange: (value: '7d' | '30d' | '90d' | 'all') => void;
}

export function TimeRangeSelector({ value, onChange }: TimeRangeSelectorProps) {
  return (
    <Select value={value} onValueChange={onChange}>
      <SelectTrigger className="w-[180px]">
        <SelectValue placeholder="Select time range" />
      </SelectTrigger>
      <SelectContent>
        <SelectItem value="7d">Last 7 days</SelectItem>
        <SelectItem value="30d">Last 30 days</SelectItem>
        <SelectItem value="90d">Last 90 days</SelectItem>
        <SelectItem value="all">All time</SelectItem>
      </SelectContent>
    </Select>
  );
}
```

#### Deliverables

- ✅ Compliance score history chart (Recharts line chart)
- ✅ Violation trends chart (Recharts area chart)
- ✅ AI usage chart (Recharts bar chart)
- ✅ Time range selector component
- ✅ Charts integrated in CompliancePage

#### Success Criteria

- [ ] Charts render with real data
- [ ] Time range filtering works
- [ ] Charts responsive on mobile
- [ ] Export functionality works (PNG/CSV)

---

### Day 5: Policy Pack Templates

**Goal**: Create policy pack template library with import/export functionality.

**Duration**: 8 hours  
**Owner**: Backend Lead (5h) + Frontend Lead (3h)  

#### Tasks

| # | Task | File | Est. | Owner |
|---|------|------|------|-------|
| 5.1 | Create policy template service | `services/policy_template_service.py` | 2h | BE |
| 5.2 | Create template import/export API | `routes/policy_templates.py` | 2h | BE |
| 5.3 | Create 5 policy pack templates | `templates/policy-packs/` | 1h | BE |
| 5.4 | Create template management UI | `pages/PolicyTemplatesPage.tsx` | 2h | FE |
| 5.5 | Document templates | `docs/04-Policy-Library/Policy-Templates.md` | 1h | BE |

#### Implementation Details

**1. Policy Template Service**

```python
# backend/app/services/policy_template_service.py

class PolicyTemplateService:
    """Service for managing policy pack templates."""
    
    TEMPLATES_DIR = Path("templates/policy-packs")
    
    async def list_templates(self) -> list[PolicyTemplate]:
        """List all available policy pack templates."""
        templates = []
        for template_file in self.TEMPLATES_DIR.glob("*.yaml"):
            template = self._load_template(template_file)
            templates.append(template)
        return templates
    
    async def get_template(self, template_id: str) -> PolicyTemplate:
        """Get a specific template by ID."""
        template_file = self.TEMPLATES_DIR / f"{template_id}.yaml"
        if not template_file.exists():
            raise NotFoundError(f"Template {template_id} not found")
        return self._load_template(template_file)
    
    async def import_template(
        self,
        template: PolicyTemplate,
        project_id: UUID,
    ) -> dict:
        """Import a template into a project."""
        # Create policies from template
        policies = []
        for policy_def in template.policies:
            policy = await self._create_policy_from_template(
                policy_def,
                project_id,
            )
            policies.append(policy)
        
        return {
            "template_id": template.id,
            "project_id": str(project_id),
            "policies_created": len(policies),
            "policies": [p.id for p in policies],
        }
```

**2. Policy Pack Templates**

```yaml
# templates/policy-packs/sdlc-491-standard.yaml

id: sdlc-491-standard
name: SDLC 5.1.3.1 Standard
description: Complete SDLC 5.1.3.1 lifecycle with all 10 stages
version: 1.0.0
author: SDLC Orchestrator Team

policies:
  - name: "G0.1 - Problem Definition"
    stage: "WHY"
    type: "design_thinking"
    rules:
      - "Requires 3+ user interviews"
      - "Requires problem statement document"
      - "Requires user persona definition"
  
  - name: "G0.2 - Solution Diversity"
    stage: "WHY"
    type: "design_thinking"
    rules:
      - "Requires 100+ ideas generated"
      - "Requires top 3 concepts selected"
      - "Requires concept validation"
  
  # ... more policies for all 10 stages
```

#### Deliverables

- ✅ Policy template service created
- ✅ Template import/export API (`GET/POST /api/v1/policy-templates`)
- ✅ 5 policy pack templates created
- ✅ Template management UI (list, import, export)
- ✅ Template documentation complete

#### Success Criteria

- [ ] Templates can be imported into projects
- [ ] Templates can be exported
- [ ] Template UI displays all templates
- [ ] Template documentation complete

---

## 📊 SPRINT METRICS

### Definition of Done

- [ ] All Day 1-5 deliverables complete
- [ ] Notifications tested (Slack + Email)
- [ ] Prometheus metrics exposed and scraped
- [ ] Grafana dashboards live and displaying data
- [ ] Frontend charts rendering with real data
- [ ] Policy templates importable
- [ ] Integration tests pass (100%)
- [ ] Documentation complete

### Success Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| **Notification Delivery** | 100% | Slack/Email logs |
| **Prometheus Metrics** | All exposed | `/metrics` endpoint |
| **Grafana Dashboards** | 4 live | Dashboard access |
| **Frontend Charts** | 3 charts | UI verification |
| **Policy Templates** | 5 templates | Template count |
| **Test Coverage** | 95%+ | Coverage report |

---

## 🚨 RISK ASSESSMENT

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Slack webhook rate limits | Medium | Low | Implement retry logic, queue notifications |
| Email delivery failures | Low | Medium | Use SendGrid (reliable), fallback to SMTP |
| Prometheus scraping issues | Low | High | Test scraping before deployment |
| Grafana dashboard performance | Low | Medium | Optimize queries, add caching |
| Chart rendering performance | Low | Low | Use Recharts (optimized), lazy load |

---

## 📚 REFERENCES

- **Sprint 21 Final Summary**: `SPRINT-21-FINAL-SUMMARY.md`
- **Notification Service**: `backend/app/services/notification_service.py`
- **Prometheus Client**: `prometheus_client` Python library
- **Grafana Dashboard Docs**: https://grafana.com/docs/grafana/latest/dashboards/
- **Recharts Docs**: https://recharts.org/

---

**Sprint 22 Focus**: "Operations Excellence - From compliance scanning to production monitoring"

**Status**: ✅ PLANNED - Ready for Team Execution

