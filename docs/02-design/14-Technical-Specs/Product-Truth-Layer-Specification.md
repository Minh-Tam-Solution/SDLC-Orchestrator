# Product Truth Layer Technical Specification

**Version**: 1.0.0
**Date**: February 8, 2026
**Status**: IMPLEMENTED - Sprint 147
**Authority**: CTO + Backend Lead
**Sprint**: Sprint 147 "Spring Cleaning"
**Stage**: Stage 02 (HOW - Design & Architecture)
**Framework**: SDLC 6.0.6

---

## 1. Executive Summary

The Product Truth Layer (PTL) establishes a comprehensive telemetry infrastructure to replace narrative-based product metrics ("82-85% realization") with measured, data-driven insights. This specification defines the event taxonomy, funnel metrics, and implementation across all interfaces (Web, CLI, VSCode Extension).

### 1.1 Goals

| Goal | Description | Target |
|------|-------------|--------|
| Activation Funnel | Measure user journey from signup to first gate pass | 3 funnels |
| Event Coverage | Instrument core user actions across all interfaces | 10 Tier 1 events |
| Time-to-Value | Track key activation milestones | p50 measurements |
| Multi-Interface | Support Web, CLI, and Extension telemetry | 3 interfaces |

### 1.2 Non-Goals

- Real-time analytics dashboard (Sprint 148)
- Cohort analysis automation (Sprint 149)
- A/B testing framework (backlog)
- Third-party analytics integration (Mixpanel, Amplitude)

---

## 2. Core Event Taxonomy

### 2.1 Tier 1: Activation Events (10 events)

These events are **mandatory** for activation funnel analysis.

| Event Name | Interface | Trigger | Properties |
|------------|-----------|---------|------------|
| `user_signed_up` | web | POST /auth/register | signup_method, referral_source |
| `project_created` | web/cli/ext | POST /projects | tier, template_used |
| `project_connected_github` | web | POST /projects/{id}/github/connect | github_repo |
| `first_validation_run` | cli/ext | First validation per project | validation_type, result, errors_count |
| `first_evidence_uploaded` | web/ext | First POST /evidence | evidence_type, file_size_bytes |
| `first_gate_passed` | web | First gate approval per project | gate_id, attempt_count |
| `invite_sent` | web | POST /invitations | role |
| `invite_accepted` | web | POST /invitations/{id}/accept | inviter_id |
| `policy_violation_blocked` | backend | OPA deny | policy_id, gate_id, violation_type |
| `ai_council_used` | web/ext | POST /ai/council | query_type, response_time_ms |

### 2.2 Tier 2: Engagement Events (10 events - Sprint 148)

| Event Name | Interface | Description |
|------------|-----------|-------------|
| `daily_active_user` | all | Computed from any authenticated API call |
| `gate_approval_requested` | web | Gate approval workflow initiated |
| `evidence_viewed` | web | Evidence detail page visited |
| `dashboard_page_viewed` | web | Page load tracking |
| `cli_command_executed` | cli | Any CLI command completion |
| `extension_command_executed` | ext | VSCode command execution |
| `spec_validated` | cli/ext | Spec validation run |
| `report_generated` | cli | Report generation |
| `policy_pack_applied` | web | Policy pack attached to project |
| `vibecoding_score_changed` | backend | Score recalculation |

### 2.3 Interface Identifiers

```yaml
interfaces:
  - web        # React Dashboard
  - cli        # sdlcctl CLI
  - extension  # VSCode Extension
  - api        # Direct API calls
```

---

## 3. Three Core Funnels

### 3.1 Funnel 1: Time-to-First-Project

```
Step 1: user_signed_up
   ↓
Step 2: project_created
   ↓
Step 3: project_connected_github (optional)
```

| Metric | Target | Measurement |
|--------|--------|-------------|
| Signup → Project (p50) | <5 min | Median time |
| Conversion Rate | >70% | % creating project in 24h |
| GitHub Connection | >50% | % connecting repo in 7 days |

### 3.2 Funnel 2: Time-to-First-Evidence

```
Step 1: project_created
   ↓
Step 2: first_validation_run
   ↓
Step 3: first_evidence_uploaded
```

| Metric | Target | Measurement |
|--------|--------|-------------|
| Project → Evidence (p50) | <15 min | Median time |
| First-run Pass Rate | >60% | Validation success on first try |
| Evidence Upload Rate | >40% | % uploading in 7 days |

### 3.3 Funnel 3: Time-to-First-Gate

```
Step 1: first_evidence_uploaded
   ↓
Step 2: gate_approval_requested
   ↓
Step 3: first_gate_passed
```

| Metric | Target | Measurement |
|--------|--------|-------------|
| Evidence → Gate (p50) | <60 min | Median time |
| First Attempt Pass | >30% | Pass on first try |
| Gate Completion | >25% | % passing any gate in 30 days |

---

## 4. Database Schema

### 4.1 product_events Table

```sql
CREATE TABLE product_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    event_name VARCHAR(100) NOT NULL,
    user_id UUID REFERENCES users(id),
    project_id UUID REFERENCES projects(id),
    organization_id UUID REFERENCES organizations(id),
    properties JSONB NOT NULL DEFAULT '{}',
    timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    session_id VARCHAR(100),
    interface VARCHAR(20) CHECK (interface IN ('web', 'cli', 'extension', 'api')),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes for funnel queries
CREATE INDEX idx_events_user ON product_events(user_id, timestamp);
CREATE INDEX idx_events_project ON product_events(project_id, timestamp);
CREATE INDEX idx_events_name ON product_events(event_name, timestamp);
CREATE INDEX idx_events_funnel ON product_events(user_id, event_name, timestamp);
CREATE INDEX idx_events_interface ON product_events(interface, timestamp);
```

### 4.2 Materialized View for Daily Metrics

```sql
CREATE MATERIALIZED VIEW daily_activation_metrics AS
SELECT
    DATE(timestamp) as date,
    COUNT(DISTINCT CASE WHEN event_name = 'user_signed_up' THEN user_id END) as signups,
    COUNT(DISTINCT CASE WHEN event_name = 'project_created' THEN user_id END) as projects_created,
    COUNT(DISTINCT CASE WHEN event_name = 'first_evidence_uploaded' THEN user_id END) as first_evidence,
    COUNT(DISTINCT CASE WHEN event_name = 'first_gate_passed' THEN user_id END) as first_gate_pass
FROM product_events
GROUP BY DATE(timestamp);

-- Refresh materialized view daily
CREATE INDEX ON daily_activation_metrics(date);
```

---

## 5. API Specification

### 5.1 POST /api/v1/telemetry/events

Track a product event.

**Request:**
```json
{
  "event_name": "project_created",
  "properties": {
    "tier": "PROFESSIONAL",
    "template_used": "sdlcctl-init"
  },
  "project_id": "uuid-optional",
  "organization_id": "uuid-optional",
  "session_id": "cli-20260208120000-12345"
}
```

**Response (201 Created):**
```json
{
  "event_id": "uuid",
  "tracked_at": "2026-02-08T12:00:00Z"
}
```

### 5.2 GET /api/v1/telemetry/funnels/{funnel_name}

Get funnel metrics.

**Parameters:**
- `funnel_name`: `time-to-first-project` | `time-to-first-evidence` | `time-to-first-gate`
- `start_date`: ISO date (default: 30 days ago)
- `end_date`: ISO date (default: today)
- `cohort_by`: `day` | `week` | `month`

**Response:**
```json
{
  "funnel_name": "time-to-first-project",
  "period": {
    "start": "2026-01-08",
    "end": "2026-02-08"
  },
  "steps": [
    { "name": "user_signed_up", "count": 127, "percentage": 100 },
    { "name": "project_created", "count": 104, "percentage": 82 },
    { "name": "project_connected_github", "count": 52, "percentage": 41 }
  ],
  "conversion_rates": {
    "signup_to_project": 82,
    "project_to_github": 50
  },
  "median_times": {
    "signup_to_project_minutes": 3.2,
    "project_to_github_minutes": 12.5
  }
}
```

### 5.3 GET /api/v1/telemetry/dashboard

Get activation dashboard data.

**Response:**
```json
{
  "signups_7d": 127,
  "signups_7d_change": 12,
  "activation_rate": 64,
  "activation_rate_change": 5,
  "time_to_first_project_p50_minutes": 3.2,
  "time_to_first_project_change": -18,
  "time_to_first_evidence_p50_minutes": 12.5,
  "time_to_first_evidence_change": -8,
  "funnels": {
    "time_to_first_project": { "current": 82, "target": 70 },
    "time_to_first_evidence": { "current": 52, "target": 40 },
    "time_to_first_gate": { "current": 25, "target": 25 }
  }
}
```

---

## 6. Implementation Architecture

### 6.1 Backend Service

```
backend/
├── app/
│   ├── api/
│   │   └── routes/
│   │       └── telemetry.py          # API endpoints
│   ├── services/
│   │   └── telemetry_service.py      # Business logic
│   ├── schemas/
│   │   └── telemetry.py              # Pydantic models
│   └── models/
│       └── product_event.py          # SQLAlchemy model
├── migrations/
│   └── versions/
│       └── xxx_add_product_events.py # Alembic migration
```

### 6.2 CLI Telemetry Module

```
backend/sdlcctl/sdlcctl/
├── lib/
│   └── telemetry.py                  # CLI telemetry client
├── commands/
│   ├── validate.py                   # track_validation()
│   ├── spec.py                       # track_spec_validation()
│   ├── report.py                     # track_report_generated()
│   └── init.py                       # track_project_init()
```

### 6.3 VSCode Extension Telemetry

```
vscode-extension/src/
├── services/
│   └── telemetryService.ts           # Extension telemetry client
├── commands/
│   ├── specValidationCommand.ts      # trackSpecValidation()
│   ├── initCommand.ts                # trackProjectCreated()
│   └── e2eValidateCommand.ts         # trackValidationRun()
```

---

## 7. Privacy & Opt-Out

### 7.1 Opt-Out Mechanisms

| Interface | Mechanism |
|-----------|-----------|
| CLI | `SDLC_TELEMETRY_DISABLED=1` environment variable |
| Extension | `sdlc.telemetry.disabled: true` in VSCode settings |
| Backend | Configuration flag in `config.py` |

### 7.2 Data Retention

- **Raw events**: 90 days (configurable)
- **Aggregated metrics**: Indefinite
- **Session data**: 24 hours after session end

### 7.3 PII Handling

- No PII stored in `properties` field
- User ID is pseudonymous (UUID)
- IP addresses not stored
- GDPR data export/deletion supported via user settings

---

## 8. Monitoring & Alerts

### 8.1 Prometheus Metrics

```python
# telemetry_service.py
telemetry_events_total = Counter(
    'sdlc_telemetry_events_total',
    'Total telemetry events tracked',
    ['event_name', 'interface']
)

telemetry_track_duration = Histogram(
    'sdlc_telemetry_track_duration_seconds',
    'Time to track event',
    buckets=[0.01, 0.05, 0.1, 0.5, 1.0]
)
```

### 8.2 Alerting Rules

```yaml
groups:
  - name: telemetry
    rules:
      - alert: TelemetryDropBelowThreshold
        expr: rate(sdlc_telemetry_events_total[1h]) < 10
        for: 30m
        labels:
          severity: warning
        annotations:
          summary: "Telemetry event rate dropped below threshold"
```

---

## 9. Testing Strategy

### 9.1 Unit Tests

- Event payload validation
- Property sanitization
- Opt-out enforcement

### 9.2 Integration Tests

- End-to-end event tracking
- Database persistence
- Funnel query accuracy

### 9.3 Performance Tests

- 1000 events/second throughput
- <100ms p99 latency for event tracking

---

## 10. Rollout Plan

### Phase 1: Sprint 147 (Complete)

- [x] Backend telemetry service
- [x] CLI telemetry module
- [x] Extension telemetry service
- [x] 10 core events instrumented

### Phase 2: Sprint 148

- [ ] Telemetry dashboard UI
- [ ] Materialized view refresh job
- [ ] Funnel visualization

### Phase 3: Sprint 149

- [ ] Cohort retention analysis
- [ ] Automated weekly reports
- [ ] Anomaly detection

---

## 11. References

- [Sprint 147 Completion Report](../../09-govern/01-CTO-Reports/SPRINT-147-COMPLETION-REPORT.md)
- [API Specification v3.4.0](../../01-planning/05-API-Design/API-Specification.md)
- [Data Model ERD v3.2.0](../../01-planning/04-Data-Model/Data-Model-ERD.md)
- [ADR-021 Analytics Service](../01-ADRs/ADR-021-Analytics-Service-Mixpanel.md)

---

**Document Status**: IMPLEMENTED
**Compliance**: SDLC 6.0.5 Stage 02
**Last Updated**: February 8, 2026
**Owner**: Backend Lead + CTO
