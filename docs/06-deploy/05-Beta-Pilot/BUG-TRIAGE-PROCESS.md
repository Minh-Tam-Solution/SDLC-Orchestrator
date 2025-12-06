# Bug Triage Process

## SDLC Orchestrator - Beta Pilot

**Version**: 1.0.0
**Date**: December 2025
**Status**: ACTIVE - Beta Pilot
**Owner**: Engineering Team

---

## Overview

This document defines the bug triage process for the SDLC Orchestrator beta pilot. It establishes severity levels, response SLAs, routing rules, and escalation procedures.

---

## Severity Levels

### P0 - Critical (Showstopper)

**Definition**: System is completely unusable, data loss, or security vulnerability.

**Examples**:
- Authentication completely broken (no one can login)
- Data corruption or loss
- Security breach or vulnerability exploited
- All API endpoints returning 500 errors
- Database connection failures

**Response Requirements**:
| Metric | Target |
|--------|--------|
| Acknowledgment | 15 minutes |
| First Response | 30 minutes |
| Status Update | Every 1 hour |
| Resolution | 4 hours |
| Post-mortem | Required within 24h |

**Escalation**:
- Immediate page to on-call engineer
- Notify Engineering Manager within 15 min
- CTO notified within 30 min
- All hands on deck if not resolved in 2 hours

---

### P1 - High (Major Impact)

**Definition**: Critical functionality broken for subset of users, major feature unusable.

**Examples**:
- Gate evaluation failing for specific project types
- Evidence upload broken for certain file types
- OAuth login failing (one provider)
- Dashboard not loading for specific users
- Performance degradation >50%

**Response Requirements**:
| Metric | Target |
|--------|--------|
| Acknowledgment | 1 hour |
| First Response | 2 hours |
| Status Update | Every 4 hours |
| Resolution | 24 hours |
| Post-mortem | Required within 48h |

**Escalation**:
- Notify on-call engineer via Slack
- Engineering Manager if not ack'd in 1 hour
- Consider P0 upgrade if multiple users affected

---

### P2 - Medium (Moderate Impact)

**Definition**: Feature works but with limitations, workaround available.

**Examples**:
- UI element misaligned or broken styling
- Export feature generating incorrect format
- Pagination not working correctly
- Notifications delayed by >5 minutes
- Minor data display errors

**Response Requirements**:
| Metric | Target |
|--------|--------|
| Acknowledgment | 4 hours |
| First Response | 8 hours (business) |
| Status Update | Daily |
| Resolution | 3-5 business days |
| Post-mortem | Not required |

**Escalation**:
- Assign to sprint backlog
- Engineering lead review if not resolved in 5 days

---

### P3 - Low (Minor Impact)

**Definition**: Cosmetic issues, minor inconveniences, feature requests.

**Examples**:
- Typos in UI text
- Color/styling preferences
- Minor UX improvements
- Documentation updates needed
- Non-critical feature requests

**Response Requirements**:
| Metric | Target |
|--------|--------|
| Acknowledgment | 24 hours |
| First Response | 48 hours (business) |
| Status Update | Weekly |
| Resolution | Backlog (no SLA) |
| Post-mortem | Not required |

**Escalation**:
- Add to product backlog
- Review in sprint planning

---

## Triage Workflow

### Stage 1: Intake

```
┌─────────────────────────────────────────────────────────────┐
│                      BUG REPORTED                           │
│         (Slack, Email, In-App, GitHub Issue)               │
└─────────────────┬───────────────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────────────┐
│                   AUTO-TRIAGE BOT                           │
│  • Parse bug report                                         │
│  • Extract keywords (error, crash, data loss, etc)         │
│  • Suggest initial priority                                 │
│  • Create ticket in system                                  │
└─────────────────┬───────────────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────────────┐
│                    TICKET CREATED                           │
│  Status: NEW                                                │
│  Priority: Suggested (pending human review)                │
└─────────────────────────────────────────────────────────────┘
```

### Stage 2: Human Triage

```
┌─────────────────────────────────────────────────────────────┐
│                   TRIAGE ENGINEER                           │
│  • Review bug details                                       │
│  • Verify reproduction steps                                │
│  • Confirm/adjust priority                                  │
│  • Assign to team/individual                                │
│  • Set target resolution date                               │
└─────────────────┬───────────────────────────────────────────┘
                  │
        ┌─────────┼─────────┬─────────┬─────────┐
        ▼         ▼         ▼         ▼         ▼
    ┌───────┐ ┌───────┐ ┌───────┐ ┌───────┐ ┌───────┐
    │  P0   │ │  P1   │ │  P2   │ │  P3   │ │WONTFIX│
    │ Page  │ │Urgent │ │Sprint │ │Backlog│ │ Close │
    └───────┘ └───────┘ └───────┘ └───────┘ └───────┘
```

### Stage 3: Resolution

```
┌─────────────────────────────────────────────────────────────┐
│                     ASSIGNED                                │
│  Status: IN_PROGRESS                                        │
└─────────────────┬───────────────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────────────┐
│                   DEVELOPMENT                               │
│  • Root cause analysis                                      │
│  • Implement fix                                            │
│  • Write tests                                              │
│  • Code review                                              │
└─────────────────┬───────────────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────────────┐
│                   VERIFICATION                              │
│  • QA verification                                          │
│  • Reporter confirmation (if needed)                        │
│  • Deploy to staging                                        │
└─────────────────┬───────────────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────────────┐
│                    RESOLVED                                 │
│  Status: CLOSED                                             │
│  • Update documentation if needed                           │
│  • Post-mortem for P0/P1                                   │
│  • Notify reporter                                          │
└─────────────────────────────────────────────────────────────┘
```

---

## Automated Routing Rules

### Priority Detection Keywords

```yaml
p0_keywords:
  - "can't login"
  - "data loss"
  - "security"
  - "crash"
  - "down"
  - "500 error"
  - "database"
  - "corruption"

p1_keywords:
  - "broken"
  - "not working"
  - "failing"
  - "error"
  - "timeout"
  - "slow"
  - "stuck"

p2_keywords:
  - "incorrect"
  - "wrong"
  - "missing"
  - "display"
  - "format"
  - "alignment"

p3_keywords:
  - "typo"
  - "suggestion"
  - "nice to have"
  - "minor"
  - "cosmetic"
```

### Component Routing

```yaml
routing_rules:
  - pattern: "gate|evaluation|policy"
    team: "gate-engine"
    default_assignee: "backend-lead"

  - pattern: "evidence|upload|vault|s3|minio"
    team: "evidence-team"
    default_assignee: "backend-lead"

  - pattern: "dashboard|ui|button|page|component"
    team: "frontend"
    default_assignee: "frontend-lead"

  - pattern: "login|auth|oauth|token|session"
    team: "security"
    default_assignee: "security-lead"

  - pattern: "api|endpoint|request|response"
    team: "backend"
    default_assignee: "backend-lead"

  - pattern: "deploy|docker|kubernetes|infra"
    team: "devops"
    default_assignee: "devops-lead"
```

---

## SLA Tracking

### SLA Metrics Dashboard

```yaml
metrics:
  acknowledgment_rate:
    description: "% of bugs acknowledged within SLA"
    target: 95%

  resolution_rate:
    description: "% of bugs resolved within SLA"
    target: 90%

  mttr:
    description: "Mean Time To Resolution"
    target:
      p0: <4h
      p1: <24h
      p2: <5d

  reopen_rate:
    description: "% of bugs reopened after closure"
    target: <5%

  escalation_rate:
    description: "% of bugs requiring escalation"
    target: <10%
```

### SLA Breach Notifications

```yaml
breach_notifications:
  p0:
    - channel: pagerduty
      delay: 0 min
    - channel: slack_engineering
      delay: 0 min
    - channel: email_cto
      delay: 15 min

  p1:
    - channel: slack_engineering
      delay: 0 min
    - channel: email_manager
      delay: 1 hour

  p2:
    - channel: slack_team
      delay: 4 hours

  p3:
    - channel: weekly_report
      delay: none
```

---

## Triage Meeting

### Schedule

- **Frequency**: Daily at 9:30 AM (GMT+7)
- **Duration**: 15 minutes
- **Participants**: Triage Engineer, Team Leads

### Agenda

1. **New Bugs Review** (5 min)
   - Review overnight submissions
   - Assign priorities
   - Assign owners

2. **Blocked Bugs** (5 min)
   - Review stuck items
   - Identify blockers
   - Escalate if needed

3. **SLA Review** (5 min)
   - Check approaching SLA breaches
   - Reprioritize if needed

### Triage Rotation

```yaml
rotation:
  - week_1: "Developer A"
  - week_2: "Developer B"
  - week_3: "Developer C"
  - week_4: "Tech Lead"
```

---

## Bug Report Template

### Required Fields

```markdown
## Bug Report

**Title**: [Brief description]

**Priority**: [P0/P1/P2/P3 - leave blank if unsure]

**Environment**:
- Browser: [e.g., Chrome 120]
- OS: [e.g., macOS 14.1]
- App Version: [from footer]

**Steps to Reproduce**:
1. [First step]
2. [Second step]
3. [...]

**Expected Behavior**:
[What should happen]

**Actual Behavior**:
[What actually happens]

**Screenshots/Logs**:
[Attach if available]

**Additional Context**:
[Any other relevant information]
```

### Auto-Response Template

```markdown
Thank you for reporting this issue!

**Ticket ID**: [AUTO_GENERATED]
**Initial Priority**: [AUTO_SUGGESTED]
**Status**: New - Awaiting Triage

What happens next:
1. Our triage team will review within [SLA_TIME]
2. You'll be notified when priority is confirmed
3. You'll receive updates as work progresses

Track your issue: [TICKET_LINK]

For urgent issues, contact us on Slack #sdlc-pilot-support.
```

---

## Post-Mortem Process (P0/P1 Only)

### Template

```markdown
# Post-Mortem: [Incident Title]

**Date**: [Date]
**Duration**: [Start time - End time]
**Severity**: [P0/P1]
**Author**: [Name]

## Summary
[2-3 sentence summary of what happened]

## Impact
- Users affected: [Number]
- Duration: [Time]
- Data impact: [None/Partial/Full]

## Timeline
| Time | Event |
|------|-------|
| HH:MM | Issue detected |
| HH:MM | Investigation started |
| HH:MM | Root cause identified |
| HH:MM | Fix deployed |
| HH:MM | Verified resolved |

## Root Cause
[Technical explanation of why this happened]

## Resolution
[What was done to fix it]

## Action Items
| Action | Owner | Due Date | Status |
|--------|-------|----------|--------|
| [Action 1] | [Name] | [Date] | [ ] |
| [Action 2] | [Name] | [Date] | [ ] |

## Lessons Learned
1. [Lesson 1]
2. [Lesson 2]

## Prevention
[How we'll prevent this in the future]
```

### Post-Mortem Meeting

- **When**: Within 24-48 hours of P0/P1 resolution
- **Participants**: Involved engineers, team leads, stakeholders
- **Duration**: 30-60 minutes
- **Focus**: Blameless analysis, prevention

---

## Metrics & Reporting

### Weekly Bug Report

Generated every Monday, includes:
- Total bugs opened/closed this week
- Bugs by priority breakdown
- SLA compliance rate
- Top bug categories
- Aging bugs (>7 days old)

### Monthly Trend Report

Generated on 1st of each month:
- Bug volume trend
- MTTR trends
- Resolution rate by team
- Recurring issue patterns
- Improvement recommendations

---

## Tools & Integration

### Bug Tracking Flow

```
┌─────────┐    ┌─────────┐    ┌─────────┐    ┌─────────┐
│  Slack  │ →  │ Webhook │ →  │ Triage  │ →  │ GitHub  │
│ /report │    │ Handler │    │   Bot   │    │ Issues  │
└─────────┘    └─────────┘    └─────────┘    └─────────┘
                                   │
                                   ▼
                            ┌─────────────┐
                            │   Notify    │
                            │  On-Call    │
                            │ (if P0/P1)  │
                            └─────────────┘
```

### Integration Points

| Source | Destination | Trigger |
|--------|-------------|---------|
| Slack `/report` | Feedback API | Manual report |
| Email inbound | Feedback API | Email webhook |
| In-app widget | Feedback API | Form submit |
| GitHub Issue | Sync service | Issue created |
| Prometheus Alert | Triage system | Alert fired |

---

**Last Updated**: December 2025
**Owner**: Engineering Team
**Review Cycle**: Monthly
