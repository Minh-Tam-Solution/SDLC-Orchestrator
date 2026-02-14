# Monthly Alignment Checkpoint Process

**Version**: 1.0.0
**Status**: ACTIVE
**Framework**: SDLC 6.0.5
**Effective Date**: February 2026
**Owner**: PM
**Reference**: ADR-045 Multi-Frontend Alignment Strategy

---

## 1. Overview

The Monthly Alignment Checkpoint ensures all frontend surfaces (Web Dashboard, CLI, VS Code Extension) maintain feature parity and alignment with the SDLC Enterprise Framework version.

### 1.1 Purpose

- Prevent framework version drift across delivery surfaces
- Identify new feature gaps before they become blockers
- Document lessons learned from alignment work
- Plan alignment work for upcoming sprints

### 1.2 Schedule

**Frequency**: First Monday of each month
**Duration**: 1 hour (60 minutes)
**Time**: 10:00 AM (Vietnam Time)

---

## 2. Participants

| Role | Required | Responsibility |
|------|----------|----------------|
| PM | ✅ Yes | Facilitator, action item tracking |
| Backend Lead | ✅ Yes | CLI alignment status, API contracts |
| Frontend Lead | ✅ Yes | Web + Extension alignment status |
| Architect | ✅ Yes | Framework version decisions, ADR updates |
| CTO | Optional | Strategic decisions, escalations |

---

## 3. Agenda Template

### 3.1 Pre-Meeting (5 min)

- [ ] Update Frontend-Alignment-Matrix.md with latest parity scores
- [ ] Gather metrics from CI/CD (test pass rates, E2E parity)
- [ ] List any Framework version changes since last checkpoint

### 3.2 Meeting Agenda (60 min)

| Time | Topic | Owner | Output |
|------|-------|-------|--------|
| 0:00-0:15 | Matrix Review | PM | Parity scores, new gaps identified |
| 0:15-0:30 | CLI Alignment Status | Backend Lead | CLI feature updates, blockers |
| 0:30-0:45 | Extension Alignment Status | Frontend Lead | Extension feature updates, blockers |
| 0:45-0:55 | Sprint Planning | All | Alignment tasks for next sprint |
| 0:55-1:00 | Action Items | PM | Documented next steps |

---

## 4. Artifacts

### 4.1 Input Documents

| Document | Location | Purpose |
|----------|----------|---------|
| Frontend Alignment Matrix | `docs/01-planning/01-Requirements/Frontend-Alignment-Matrix.md` | Feature parity tracking |
| Framework Version | `SDLC-Enterprise-Framework/VERSION` | Current framework version |
| Open Alignment Issues | GitHub Issues (label: `framework-alignment`) | Pending alignment work |

### 4.2 Output Documents

| Document | Location | Purpose |
|----------|----------|---------|
| Meeting Notes | `docs/09-govern/03-Meeting-Notes/YYYY-MM-alignment-checkpoint.md` | Record of discussion |
| Updated Matrix | Frontend-Alignment-Matrix.md | Updated parity scores |
| Sprint Backlog | JIRA/GitHub Issues | Alignment tasks for next sprint |

---

## 5. Decision Framework

### 5.1 Gap Prioritization

| Priority | Criteria | Action |
|----------|----------|--------|
| P0 - Critical | Blocks launch, security issue | Add to current sprint |
| P1 - High | User-facing feature gap | Add to next sprint |
| P2 - Medium | Developer experience gap | Add to backlog |
| P3 - Low | Nice-to-have parity | Document, defer |

### 5.2 Escalation Triggers

Escalate to CTO when:
- Framework version >1 month behind on any surface
- Parity score drops below 70% for any surface
- Security-related gap identified
- Resource conflict between surfaces

---

## 6. Metrics Tracked

### 6.1 Parity Scores

| Surface | Formula | Target |
|---------|---------|--------|
| CLI | (Implemented / Total Planned) × 100 | ≥70% |
| Extension | (Implemented / Total Planned) × 100 | ≥85% |
| Web | (Implemented / Total Planned) × 100 | 100% |

### 6.2 Alignment Health

| Metric | Good | Warning | Critical |
|--------|------|---------|----------|
| Framework Version Lag | 0 versions | 1 version | 2+ versions |
| Open Alignment Issues | 0-3 | 4-6 | 7+ |
| E2E Parity Tests | 100% pass | 90-99% pass | <90% pass |

---

## 7. Meeting Notes Template

```markdown
# Monthly Alignment Checkpoint - [Month Year]

**Date**: YYYY-MM-DD
**Attendees**: PM, Backend Lead, Frontend Lead, Architect

## 1. Framework Version Status

| Surface | Current | Target | Gap |
|---------|---------|--------|-----|
| Framework | X.Y.Z | - | - |
| CLI | X.Y.Z | X.Y.Z | None/Gap |
| Extension | X.Y.Z | X.Y.Z | None/Gap |
| Web | X.Y.Z | X.Y.Z | None/Gap |

## 2. Parity Scores

| Surface | Last Month | This Month | Change |
|---------|------------|------------|--------|
| CLI | XX% | XX% | +/-X% |
| Extension | XX% | XX% | +/-X% |

## 3. New Gaps Identified

| Gap ID | Description | Surface | Priority | Owner |
|--------|-------------|---------|----------|-------|
| GAP-XXX | Description | CLI/Ext | P0/P1/P2 | Name |

## 4. Resolved Gaps (Since Last Checkpoint)

| Gap ID | Description | Resolution Sprint |
|--------|-------------|-------------------|
| GAP-XXX | Description | Sprint XXX |

## 5. Action Items

| # | Action | Owner | Due Date |
|---|--------|-------|----------|
| 1 | Action description | Name | YYYY-MM-DD |

## 6. Next Checkpoint

**Date**: YYYY-MM-DD (First Monday of next month)
```

---

## 8. Process Improvement

### 8.1 Quarterly Review

Every quarter (Q1, Q2, Q3, Q4), review this process:
- Is the checkpoint cadence appropriate?
- Are the right people attending?
- Are action items being completed?
- Should metrics thresholds be adjusted?

### 8.2 Feedback Loop

After each checkpoint:
1. PM sends meeting notes within 24 hours
2. All participants confirm action items within 48 hours
3. Blockers escalated to CTO within 1 business day

---

## 9. Change Log

| Date | Version | Change | Author |
|------|---------|--------|--------|
| 2026-01-30 | 1.0.0 | Initial process definition | AI Assistant |

---

**Document Status**: ACTIVE
**Review Cycle**: Quarterly
**Next Review**: April 2026
