# Analytics Event Taxonomy

**SDLC Stage**: 05 - OPERATE
**Sprint**: 41 - AI Safety Foundation
**Version**: 1.0.0
**Date**: December 21, 2025
**Status**: PRODUCTION READY
**Framework**: SDLC 6.1.0

---

## Purpose

This document defines the standard event taxonomy for SDLC Orchestrator product analytics. All events tracked via Mixpanel + PostgreSQL dual approach follow this schema.

**Target Audience**:
- Frontend developers (React hooks integration)
- Backend developers (FastAPI endpoint usage)
- Product managers (Mixpanel dashboard creation)
- Data analysts (SQL queries for reports)

---

## Event Tracking Architecture

### Dual Approach (ADR-021)

```
Frontend/Backend → AnalyticsService → Mixpanel (analytics UX)
                                   → PostgreSQL (audit trail, 90-day retention)
```

**Privacy**:
- User IDs are hashed with SHA256 + salt before sending to Mixpanel
- No PII (Personally Identifiable Information) in event properties
- GDPR-compliant: 90-day retention enforced

**Resilience**:
- Circuit breaker: If Mixpanel fails 5+ times → PostgreSQL-only fallback
- Audit trail never lost (PostgreSQL is source of truth)

---

## Core Events (10 minimum for Sprint 41)

### 1. `user_login`

**When**: User successfully authenticates to SDLC Orchestrator

**Properties**:
```typescript
{
  provider: "email" | "google" | "github" | "microsoft",  // OAuth provider
  first_login: boolean,                                    // First-time user?
  mfa_enabled: boolean,                                    // MFA active?
  session_token: string                                    // Session ID
}
```

**Example**:
```python
await analytics_service.track_event(
    user_id=current_user.id,
    event_name="user_login",
    properties={
        "provider": "google",
        "first_login": False,
        "mfa_enabled": True,
        "session_token": "abc123..."
    },
    db=db
)
```

**Metrics Powered**:
- Daily Active Users (DAU)
- Weekly Active Users (WAU)
- Monthly Active Users (MAU)
- OAuth adoption rate

---

### 2. `user_signup`

**When**: New user completes registration

**Properties**:
```typescript
{
  provider: "email" | "google" | "github" | "microsoft",
  team_size: "solo" | "2-10" | "11-50" | "51-200" | "201+",
  industry: string,                                        // e.g., "SaaS", "Finance"
  source: "organic" | "referral" | "paid_ad" | "product_hunt"
}
```

**Example**:
```python
await analytics_service.track_event(
    user_id=new_user.id,
    event_name="user_signup",
    properties={
        "provider": "email",
        "team_size": "2-10",
        "industry": "SaaS",
        "source": "product_hunt"
    },
    db=db
)
```

**Metrics Powered**:
- Signup conversion rate
- User acquisition channels
- Industry segmentation

---

### 3. `project_created`

**When**: User creates a new SDLC project

**Properties**:
```typescript
{
  project_id: UUID,
  project_name: string,
  sdlc_tier: "LITE" | "STANDARD" | "PROFESSIONAL" | "ENTERPRISE",
  framework_version: string,                               // e.g., "5.1.1"
  github_connected: boolean,
  template_used: string | null                             // Template name if used
}
```

**Example**:
```python
await analytics_service.track_event(
    user_id=current_user.id,
    event_name="project_created",
    properties={
        "project_id": str(project.id),
        "project_name": "SDLC Orchestrator v2",
        "sdlc_tier": "PROFESSIONAL",
        "framework_version": "5.1.1",
        "github_connected": True,
        "template_used": "microservice-template"
    },
    db=db
)
```

**Metrics Powered**:
- Projects created per month
- SDLC tier adoption
- Template usage

---

### 4. `gate_passed`

**When**: Quality gate evaluation passes

**Properties**:
```typescript
{
  gate_id: UUID,
  gate_code: "G0.1" | "G0.2" | "G1" | "G2" | "G3" | "G4" | "G5" | "G6" | "G7" | "G8" | "G9",
  stage: "WHY" | "WHAT" | "HOW" | "BUILD" | "TEST" | "DEPLOY" | "OPERATE" | "LEARN" | "OPTIMIZE" | "GOVERN",
  project_id: UUID,
  evidence_count: number,                                  // Evidence items submitted
  policy_violations: number,                               // OPA policy violations
  duration_ms: number                                      // Gate evaluation duration
}
```

**Example**:
```python
await analytics_service.track_event(
    user_id=current_user.id,
    event_name="gate_passed",
    properties={
        "gate_id": str(gate.id),
        "gate_code": "G2",
        "stage": "HOW",
        "project_id": str(project.id),
        "evidence_count": 12,
        "policy_violations": 0,
        "duration_ms": 1250
    },
    db=db
)
```

**Metrics Powered**:
- Gate pass rate by stage
- Average evidence per gate
- Gate evaluation performance

---

### 5. `gate_failed`

**When**: Quality gate evaluation fails

**Properties**:
```typescript
{
  gate_id: UUID,
  gate_code: string,
  stage: string,
  project_id: UUID,
  evidence_count: number,
  policy_violations: number,
  missing_evidence: string[],                              // List of missing evidence types
  violation_types: string[],                               // OPA policy violation categories
  duration_ms: number
}
```

**Example**:
```python
await analytics_service.track_event(
    user_id=current_user.id,
    event_name="gate_failed",
    properties={
        "gate_id": str(gate.id),
        "gate_code": "G2",
        "stage": "HOW",
        "project_id": str(project.id),
        "evidence_count": 8,
        "policy_violations": 3,
        "missing_evidence": ["architecture-diagram", "api-spec"],
        "violation_types": ["naming-convention", "folder-structure"],
        "duration_ms": 980
    },
    db=db
)
```

**Metrics Powered**:
- Gate failure rate
- Most common missing evidence
- Policy violation trends

---

### 6. `evidence_uploaded`

**When**: User uploads evidence file to Evidence Vault

**Properties**:
```typescript
{
  evidence_id: UUID,
  evidence_type: "document" | "code" | "test_report" | "diagram" | "screenshot",
  file_size_kb: number,
  file_extension: string,                                  // e.g., ".pdf", ".png"
  gate_code: string,
  project_id: UUID,
  upload_duration_ms: number
}
```

**Example**:
```python
await analytics_service.track_event(
    user_id=current_user.id,
    event_name="evidence_uploaded",
    properties={
        "evidence_id": str(evidence.id),
        "evidence_type": "diagram",
        "file_size_kb": 1024,
        "file_extension": ".png",
        "gate_code": "G2",
        "project_id": str(project.id),
        "upload_duration_ms": 2340
    },
    db=db
)
```

**Metrics Powered**:
- Evidence upload volume
- Average file size
- Upload performance

---

### 7. `ai_safety_validation`

**When**: AI Safety Layer validates a pull request

**Properties**:
```typescript
{
  pr_id: string,                                           // GitHub PR number
  ai_tool: "claude-code" | "cursor" | "copilot" | "windsurf" | "continue" | "unknown",
  result: "passed" | "failed" | "warning",
  violations_found: number,
  duration_ms: number,
  project_id: UUID,
  commit_sha: string
}
```

**Example**:
```python
await analytics_service.track_ai_safety_event(
    user_id=current_user.id,
    pr_id="PR-1234",
    ai_tool="claude-code",
    validation_result="failed",
    duration_ms=1250,
    violations_found=3,
    db=db
)
```

**Metrics Powered**:
- AI Safety pass rate
- AI tool usage distribution
- Violation trends

---

### 8. `design_partner_feedback`

**When**: Design partner submits feedback (Sprint 43+)

**Properties**:
```typescript
{
  feedback_id: UUID,
  feedback_type: "bug" | "feature_request" | "usability" | "performance",
  severity: "low" | "medium" | "high" | "critical",
  feature_area: string,                                    // e.g., "gates", "evidence-vault"
  satisfaction_score: number,                              // 1-5 rating
  nps_score: number | null                                 // Net Promoter Score (0-10)
}
```

**Example**:
```python
await analytics_service.track_event(
    user_id=current_user.id,
    event_name="design_partner_feedback",
    properties={
        "feedback_id": str(feedback.id),
        "feedback_type": "feature_request",
        "severity": "medium",
        "feature_area": "ai-safety",
        "satisfaction_score": 4,
        "nps_score": 9
    },
    db=db
)
```

**Metrics Powered**:
- Design partner satisfaction
- Feature request prioritization
- NPS score tracking

---

### 9. `compliance_scan_completed`

**When**: Automated compliance scan finishes

**Properties**:
```typescript
{
  scan_id: UUID,
  scan_type: "owasp" | "gdpr" | "hipaa" | "soc2",
  project_id: UUID,
  violations_found: number,
  scan_duration_seconds: number,
  status: "passed" | "failed"
}
```

**Example**:
```python
await analytics_service.track_event(
    user_id=current_user.id,
    event_name="compliance_scan_completed",
    properties={
        "scan_id": str(scan.id),
        "scan_type": "owasp",
        "project_id": str(project.id),
        "violations_found": 2,
        "scan_duration_seconds": 45,
        "status": "failed"
    },
    db=db
)
```

**Metrics Powered**:
- Compliance scan frequency
- Violation trends by type
- Scan performance

---

### 10. `feature_used`

**When**: User interacts with a key feature

**Properties**:
```typescript
{
  feature_name: string,                                    // e.g., "policy-pack-builder"
  success: boolean,
  duration_ms: number,
  interaction_type: "create" | "update" | "delete" | "view"
}
```

**Example**:
```python
await analytics_service.track_event(
    user_id=current_user.id,
    event_name="feature_used",
    properties={
        "feature_name": "policy-pack-builder",
        "success": True,
        "duration_ms": 3200,
        "interaction_type": "create"
    },
    db=db
)
```

**Metrics Powered**:
- Feature adoption rate
- Feature success rate
- Feature performance

---

## Frontend Integration (React)

### Custom Hook: `useAnalytics`

```typescript
// frontend/src/hooks/useAnalytics.ts
import { useAuth } from '@/contexts/AuthContext';
import { analyticsApi } from '@/services/api/analytics';

export function useAnalytics() {
  const { user } = useAuth();

  const trackEvent = async (
    eventName: string,
    properties?: Record<string, any>
  ) => {
    if (!user) return;

    try {
      await analyticsApi.trackEvent({
        user_id: user.id,
        event_name: eventName,
        properties: {
          ...properties,
          timestamp: new Date().toISOString(),
          user_role: user.role,
        },
      });
    } catch (error) {
      console.error('Analytics tracking failed:', error);
      // Fail silently - don't disrupt user experience
    }
  };

  return { trackEvent };
}
```

### Usage Example

```typescript
// frontend/src/pages/ProjectCreate.tsx
import { useAnalytics } from '@/hooks/useAnalytics';

export function ProjectCreate() {
  const { trackEvent } = useAnalytics();

  const handleCreateProject = async (data: ProjectFormData) => {
    const project = await createProject(data);

    // Track project creation
    await trackEvent('project_created', {
      project_id: project.id,
      project_name: project.name,
      sdlc_tier: project.tier,
      framework_version: '5.1.1',
      github_connected: data.github_repo !== null,
      template_used: data.template || null,
    });

    navigate(`/projects/${project.id}`);
  };

  return <ProjectForm onSubmit={handleCreateProject} />;
}
```

---

## Backend Integration (FastAPI)

### Direct Service Usage

```python
# backend/app/api/routes/projects.py
from app.services.analytics_service import analytics_service

@router.post("/projects", status_code=201)
async def create_project(
    project: ProjectCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    # Create project
    new_project = await project_service.create(db, project, current_user.id)

    # Track analytics event
    await analytics_service.track_event(
        user_id=current_user.id,
        event_name="project_created",
        properties={
            "project_id": str(new_project.id),
            "project_name": new_project.name,
            "sdlc_tier": new_project.tier,
            "framework_version": "5.1.1",
            "github_connected": new_project.github_repo is not None,
            "template_used": project.template
        },
        db=db
    )

    return new_project
```

---

## Event Property Standards

### Required Properties (all events)

```typescript
{
  user_id: UUID,           // Auto-added by service (hashed for Mixpanel)
  event_name: string,      // Must match taxonomy
  timestamp: ISO8601,      // Auto-added by service
  environment: string      // "production" | "staging" | "development"
}
```

### Optional Properties (context-specific)

```typescript
{
  project_id?: UUID,       // Project context
  session_token?: string,  // User session
  ip_address?: string,     // For fraud detection (hashed)
  user_agent?: string,     // Browser/app version
  referrer?: string        // Traffic source
}
```

### Naming Conventions

**Event Names**:
- Use `snake_case` (e.g., `user_login`, not `userLogin`)
- Use past tense verbs (e.g., `gate_passed`, not `gate_pass`)
- Be specific (e.g., `evidence_uploaded`, not `file_uploaded`)

**Property Keys**:
- Use `snake_case`
- Use full words (e.g., `duration_ms`, not `dur`)
- Use standard units (e.g., `_ms` for milliseconds, `_kb` for kilobytes)

---

## Data Retention

### PostgreSQL (Audit Trail)

**analytics_events**:
- Retention: 90 days (GDPR compliance)
- Cleanup: Daily cron at 2:00 AM UTC
- Purpose: Audit trail, compliance reporting

**ai_code_events**:
- Retention: 2 years (security audit requirement)
- Cleanup: Annual cron
- Purpose: AI Safety compliance, trend analysis

### Mixpanel (Analytics UX)

- Retention: Unlimited (free tier: 1 year)
- Purpose: Self-service dashboards, funnels, cohorts
- Note: No PII stored (user IDs are hashed)

---

## Mixpanel Dashboards (Sprint 42+)

### 1. Product Analytics Dashboard

**Metrics**:
- DAU/WAU/MAU trends
- User retention (D1, D7, D30)
- Feature adoption rates
- Conversion funnels (signup → project created → gate passed)

**Charts**:
- Line: DAU over time
- Bar: Top 10 features by usage
- Funnel: Onboarding completion rate
- Cohort: User retention by signup week

---

### 2. AI Safety Dashboard

**Metrics**:
- AI tool usage distribution
- AI Safety pass rate
- Violation trends by type
- Average validation duration

**Charts**:
- Pie: AI tool distribution (Claude, Cursor, Copilot, etc)
- Line: AI Safety pass rate over time
- Bar: Top 10 violation types
- Histogram: Validation duration distribution

---

### 3. Design Partner Dashboard

**Metrics**:
- Feedback submission rate
- NPS score trends
- Bug vs feature request ratio
- Satisfaction score by feature area

**Charts**:
- Gauge: Current NPS score
- Line: Weekly feedback volume
- Stacked bar: Feedback types
- Heatmap: Satisfaction by feature area

---

## API Endpoints Reference

### Track Single Event

```
POST /api/v1/analytics/v2/events
```

**Request**:
```json
{
  "user_id": "550e8400-e29b-41d4-a716-446655440000",
  "event_name": "gate_passed",
  "properties": {
    "gate_id": "660e8400-e29b-41d4-a716-446655440000",
    "gate_code": "G2",
    "stage": "HOW",
    "project_id": "770e8400-e29b-41d4-a716-446655440000",
    "evidence_count": 12,
    "policy_violations": 0,
    "duration_ms": 1250
  }
}
```

**Response**:
```json
{
  "success": true,
  "event_id": null
}
```

---

### Track Batch Events

```
POST /api/v1/analytics/v2/events/batch
```

**Request**:
```json
{
  "events": [
    {
      "user_id": "550e8400-e29b-41d4-a716-446655440000",
      "event_name": "user_login",
      "properties": {"provider": "google"}
    },
    {
      "user_id": "550e8400-e29b-41d4-a716-446655440000",
      "event_name": "project_created",
      "properties": {"project_name": "My Project"}
    }
  ]
}
```

**Response**:
```json
{
  "success_count": 2,
  "total_count": 2,
  "failed_events": []
}
```

---

### Get DAU Metrics

```
GET /api/v1/analytics/v2/metrics/dau?days=30
```

**Response**:
```json
{
  "start_date": "2026-01-01",
  "end_date": "2026-01-30",
  "daily_counts": {
    "2026-01-06": 45,
    "2026-01-07": 52,
    "2026-01-08": 48
  },
  "total_unique_users": 127,
  "avg_dau": 48.3
}
```

---

### Get AI Safety Metrics

```
GET /api/v1/analytics/v2/metrics/ai-safety?days=7
```

**Response**:
```json
{
  "period_days": 7,
  "total_validations": 1234,
  "pass_rate": 0.87,
  "avg_duration_ms": 945.2,
  "top_tools": {
    "claude-code": 450,
    "cursor": 380,
    "copilot": 250,
    "windsurf": 100,
    "continue": 54
  },
  "violations_by_type": {
    "naming_convention": 12,
    "folder_structure": 8,
    "missing_evidence": 5
  }
}
```

---

## Testing

### Unit Test Example

```python
# backend/tests/unit/test_analytics_events.py
import pytest
from app.services.analytics_service import analytics_service

@pytest.mark.asyncio
async def test_track_gate_passed_event(mock_db, current_user):
    """Test tracking gate_passed event."""
    success = await analytics_service.track_event(
        user_id=current_user.id,
        event_name="gate_passed",
        properties={
            "gate_code": "G2",
            "stage": "HOW",
            "evidence_count": 12,
            "policy_violations": 0
        },
        db=mock_db
    )

    assert success is True
    mock_db.add.assert_called_once()
```

---

## Monitoring

### Prometheus Metrics

```
# Event tracking success rate
analytics_events_tracked_total{provider="mixpanel",status="success"} 12500
analytics_events_tracked_total{provider="postgresql",status="success"} 12500
analytics_events_tracked_total{provider="mixpanel",status="failure"} 45

# Circuit breaker status
analytics_circuit_breaker_state 0  # 0=closed, 1=open, 2=half_open
analytics_circuit_breaker_failures_total 45
```

### Grafana Alerts

```yaml
- alert: EventTrackingFailureRate
  expr: rate(analytics_events_tracked_total{status="failure"}[5m]) > 0.05
  for: 5m
  annotations:
    summary: "Analytics event tracking failure rate >5%"
    description: "Check Mixpanel API status and circuit breaker state"
```

---

## Changelog

### v1.0.0 (December 21, 2025)
- Initial event taxonomy (10 core events)
- Frontend/backend integration examples
- Mixpanel dashboard specifications
- API endpoint documentation

---

## References

- **ADR-021**: Analytics Service - Mixpanel Integration
- **Sprint 41**: AI Safety Foundation
- **GDPR Article 5**: Data minimization and retention
- **Mixpanel API Docs**: https://developer.mixpanel.com/

---

**Document Owner**: Backend Team + Product Team
**Last Updated**: December 21, 2025
**Next Review**: Sprint 43 (Design Partner Feedback implementation)
