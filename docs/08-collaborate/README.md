# Stage 08: Team Management (COLLABORATE)

**Version**: 5.0.0
**Stage**: 08 - Team Management
**Question Answered**: How do we COLLABORATE effectively?
**Status**: ACTIVE
**Framework**: SDLC 5.1.3 Complete Lifecycle

---

## Purpose

Define **team coordination, communication, and collaboration standards** for effective multi-team development. This stage ensures:
- Clear roles and responsibilities (RACI)
- Effective communication protocols
- Proper escalation paths
- Knowledge sharing practices

---

## Folder Structure

```
08-Team-Management/
├── README.md                         # This file (P0 entry point)
├── 01-Team-Strategy/                 # Team structure, RACI matrix
├── 02-Team-Coordination/             # Sync meetings, handoff protocols
├── 03-SDLC-Compliance/               # SDLC adherence, quality gates
├── 04-Sprint-Management/             # Sprint planning, retrospectives
├── 05-Performance-Reports/           # Team metrics, velocity
├── 06-Strategic-Initiatives/         # Strategic team decisions
├── 07-Communication/                 # Communication channels, templates
├── 08-Technical-Reviews/             # Code review, architecture reviews
└── (Legacy content migrated to docs/10-archive/08-Legacy/ per RFC-001)
```

---

## Key Documents

| Document | Purpose | Status |
|----------|---------|--------|
| [BETA-TEAM-ONBOARDING-GUIDE.md](./BETA-TEAM-ONBOARDING-GUIDE.md) | Beta team onboarding | Active |
| [INTERNAL-LAUNCH-ANNOUNCEMENT.md](./INTERNAL-LAUNCH-ANNOUNCEMENT.md) | Internal launch communication | Active |
| [PRODUCTION-DEPLOYMENT-RUNBOOK.md](./PRODUCTION-DEPLOYMENT-RUNBOOK.md) | Production deployment guide | Active |
| [SDLC-4.9.1-User-Training-Guide.md](./SDLC-4.9.1-User-Training-Guide.md) | SDLC training (upgrade to 5.0.0 pending) | Active |

---

## RACI Matrix (High-Level)

| Deliverable | Responsible | Accountable | Consulted | Informed |
|-------------|-------------|-------------|-----------|----------|
| Architecture Decisions | CTO | CEO | Tech Lead | Team |
| Sprint Planning | PJM | PM | Team Leads | Stakeholders |
| Code Reviews | Tech Lead | CTO | Backend/Frontend Leads | Team |
| Quality Gates | QA Lead | CTO | Dev Leads | PM |
| Release Decisions | PM | CTO | All Leads | Team |
| Documentation | Tech Writer | CPO | Team | Stakeholders |

---

## Communication Cadence

### Daily
- Standup (15 min, async-friendly)
- Slack updates (#dev-standup)

### Weekly
- Sprint planning (Monday, 1h)
- CTO technical review (varies)
- Sprint retrospective (Friday, 30 min)

### Per Sprint
- Sprint demo (end of sprint)
- Gate review (if applicable)

### As Needed
- Architecture review
- Escalation meetings
- Cross-team sync

---

## Escalation Path

```yaml
Level 0 - Team:
  Scope: Technical decisions, implementation choices
  Time: Immediate resolution expected
  Escalate to: Level 1 if >4h blocked

Level 1 - Tech Lead:
  Scope: Cross-component decisions, blockers
  SLA: <4h response
  Escalate to: Level 2 if business impact

Level 2 - PM/CTO:
  Scope: Business logic, timeline impact, resource allocation
  SLA: <8h response
  Escalate to: Level 3 if strategic

Level 3 - CEO:
  Scope: Strategic decisions, major pivots
  SLA: <24h response
  Authority: Final decision
```

---

## Team Structure (SDLC Orchestrator)

### Current Team (8.5 FTE)

| Role | Count | Responsibility |
|------|-------|----------------|
| Backend Lead | 1 | API, Database, Integration |
| Backend Engineer | 1 | Implementation, Testing |
| Frontend Lead | 1 | Dashboard, Components |
| Frontend Engineer | 1 | Implementation, UX |
| DevOps Lead | 1 | CI/CD, Infrastructure |
| QA Lead | 1 | Testing, Quality Gates |
| PM/PJM | 1 | Sprint planning, Communication |
| Tech Lead | 1 | Technical oversight |
| CTO | 0.5 | Architecture, Reviews |

### Team Topology Type
- **Stream-aligned**: Primary feature delivery team
- Supported by Platform (DevOps) and Enabling (CTO reviews)

---

## SDLC 5.1.3 Compliance

This stage maps to **Stage 08: Team Management (COLLABORATE)** in SDLC 5.1.3.

### Required Artifacts (PROFESSIONAL Tier)

- [ ] RACI matrix per major deliverable
- [ ] Communication protocol documented
- [ ] Escalation path defined
- [ ] Sprint cadence established
- [ ] Knowledge sharing practices

### Tier Requirements

| Tier | Team Mgmt Requirements |
|------|------------------------|
| LITE | Basic async communication |
| STANDARD | Weekly sync, escalation path |
| PROFESSIONAL | Full RACI, handoff protocols, retrospectives |
| ENTERPRISE | CAB process, SLA enforcement, audit trail |

---

## Related Stages

| Stage | Relationship |
|-------|--------------|
| Stage 04 (BUILD) | Sprint execution, development work |
| Stage 07 (OPERATE) | Incident escalation, on-call handoff |
| Stage 09 (GOVERN) | Executive reporting, governance |

---

## AI Assistant Guidance

**DO Read**:
- This README for context
- RACI matrix for role clarity
- Communication protocols

**DO NOT Read**:
- `docs/10-archive/` folders - Contains archived, outdated content

**Key Insight**: Team structure and communication protocols are tier-dependent. This project uses PROFESSIONAL tier standards.

---

**Document Status**: P0 Entry Point (PROFESSIONAL Required)
**Compliance**: SDLC 5.1.3 Stage 08
**Last Updated**: December 5, 2025
**Owner**: PM + Tech Lead

