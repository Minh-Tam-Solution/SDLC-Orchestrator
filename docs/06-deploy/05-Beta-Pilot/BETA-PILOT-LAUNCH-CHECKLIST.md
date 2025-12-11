# Beta Pilot Launch Checklist

## SDLC Orchestrator - Internal Beta Pilot

**Version**: 1.0.0
**Date**: December 2025
**Target Launch**: January 6, 2026
**Status**: READY FOR LAUNCH

---

## Overview

This checklist ensures all systems, teams, and processes are ready for the internal beta pilot launch with 5 NQH teams (28 users).

---

## Pre-Launch Checklist (T-7 days)

### Infrastructure Verification

| Item | Status | Owner | Verified By |
|------|--------|-------|-------------|
| Staging environment healthy | ☐ | DevOps | |
| PostgreSQL 15.5 running | ☐ | DevOps | |
| Redis 7.2 connected | ☐ | DevOps | |
| OPA 0.58.0 policies loaded | ☐ | Backend | |
| MinIO buckets created | ☐ | DevOps | |
| Grafana dashboards ready | ☐ | DevOps | |
| SSL certificates valid | ☐ | DevOps | |
| DNS configured | ☐ | DevOps | |

### Application Verification

| Item | Status | Owner | Verified By |
|------|--------|-------|-------------|
| Backend API responding | ☐ | Backend | |
| Frontend loading | ☐ | Frontend | |
| Health endpoints passing | ☐ | DevOps | |
| All migrations applied | ☐ | Backend | |
| Sample data seeded | ☐ | Backend | |
| APScheduler running | ☐ | Backend | |

### Security Verification

| Item | Status | Owner | Verified By |
|------|--------|-------|-------------|
| SAST scan passed (Semgrep) | ☐ | Security | |
| Dependency scan passed (Grype) | ☐ | Security | |
| Container scan passed (Trivy) | ☐ | Security | |
| Secrets scan passed (TruffleHog) | ☐ | Security | |
| License scan passed (Syft) | ☐ | Security | |
| AGPL containment verified | ☐ | Security | |

### User Accounts

| Item | Status | Owner | Verified By |
|------|--------|-------|-------------|
| BFlow team accounts (8) | ☐ | PM | |
| NQH-Bot team accounts (6) | ☐ | PM | |
| SDLC Orchestrator accounts (5) | ☐ | PM | |
| SDLC Enterprise accounts (4) | ☐ | PM | |
| MTEP Platform accounts (5) | ☐ | PM | |
| Admin accounts configured | ☐ | PM | |
| Role assignments verified | ☐ | PM | |

### Documentation

| Item | Status | Owner | Verified By |
|------|--------|-------|-------------|
| Onboarding guide published | ☐ | PM | |
| Training materials ready | ☐ | PM | |
| Support channels documented | ☐ | Support | |
| Bug triage process documented | ☐ | QA | |
| FAQ updated | ☐ | PM | |

---

## Pre-Launch Checklist (T-1 day)

### Final System Checks

| Item | Status | Owner | Verified By |
|------|--------|-------|-------------|
| Full system health check | ☐ | DevOps | |
| Load test completed | ☐ | QA | |
| Backup verified | ☐ | DevOps | |
| Rollback procedure tested | ☐ | DevOps | |
| Monitoring alerts configured | ☐ | DevOps | |

### Communication

| Item | Status | Owner | Verified By |
|------|--------|-------|-------------|
| Launch announcement drafted | ☐ | PM | |
| Slack channel created (#sdlc-pilot) | ☐ | PM | |
| Email templates ready | ☐ | PM | |
| Welcome message prepared | ☐ | PM | |

### Support Team

| Item | Status | Owner | Verified By |
|------|--------|-------|-------------|
| On-call rotation scheduled | ☐ | Engineering | |
| Escalation contacts verified | ☐ | Support | |
| Office hours scheduled | ☐ | PM | |
| Support runbook reviewed | ☐ | Support | |

---

## Launch Day (T-0)

### Morning (9:00 AM)

| Time | Action | Owner | Status |
|------|--------|-------|--------|
| 9:00 | Final health check | DevOps | ☐ |
| 9:15 | Verify all services running | Backend | ☐ |
| 9:30 | Check monitoring dashboards | DevOps | ☐ |
| 9:45 | Team standup | PM | ☐ |

### Launch (10:00 AM)

| Time | Action | Owner | Status |
|------|--------|-------|--------|
| 10:00 | Send launch announcement | PM | ☐ |
| 10:00 | Post in #sdlc-pilot | PM | ☐ |
| 10:05 | Send welcome emails | PM | ☐ |
| 10:15 | Monitor first logins | Backend | ☐ |

### Monitoring (10:00 AM - 6:00 PM)

| Item | Check Frequency | Owner | Status |
|------|-----------------|-------|--------|
| Error rate | Every 15 min | DevOps | ☐ |
| API latency | Every 15 min | Backend | ☐ |
| User login success | Every 30 min | Backend | ☐ |
| Evidence upload success | Every hour | Backend | ☐ |
| Slack channel activity | Continuous | Support | ☐ |

---

## Post-Launch Day 1

### Morning Review

| Item | Status | Owner | Notes |
|------|--------|-------|-------|
| Error rate analysis | ☐ | DevOps | |
| User login report | ☐ | Backend | |
| First feedback collected | ☐ | PM | |
| Any P0/P1 bugs? | ☐ | QA | |

### Metrics to Collect

| Metric | Target | Actual | Status |
|--------|--------|--------|--------|
| Users logged in | >50% (14+) | | ☐ |
| Projects created | >5 | | ☐ |
| Gates evaluated | >10 | | ☐ |
| Evidence uploaded | >5 | | ☐ |
| Feedback submitted | >3 | | ☐ |

### End of Day Report

- [ ] Compile daily metrics
- [ ] Document any issues
- [ ] Plan Day 2 priorities
- [ ] Update stakeholders

---

## Post-Launch Week 1

### Daily Standups (10:00 AM)

| Day | Focus | Owner |
|-----|-------|-------|
| Monday | Launch day review | PM |
| Tuesday | User feedback | PM |
| Wednesday | Bug triage | QA |
| Thursday | Feature adoption | Backend |
| Friday | Week 1 summary | PM |

### Weekly Metrics

| Metric | Target | Actual |
|--------|--------|--------|
| Daily Active Users | >20 | |
| Weekly Active Users | 28 (100%) | |
| Session duration (avg) | >10 min | |
| Features used (avg) | >3 | |
| Bugs reported | <10 | |
| Bug resolution rate | >80% | |

### Week 1 Deliverables

- [ ] Week 1 metrics report
- [ ] Bug triage summary
- [ ] Feature adoption analysis
- [ ] User feedback summary
- [ ] Week 2 plan

---

## Escalation Procedures

### P0 - Critical (System Down)

| Step | Action | Time |
|------|--------|------|
| 1 | Alert on-call engineer | Immediate |
| 2 | Create incident channel | 5 min |
| 3 | Escalate to CTO | 15 min |
| 4 | Status page update | 20 min |
| 5 | Resolution or rollback | 4 hours |

### P1 - Major (Feature Broken)

| Step | Action | Time |
|------|--------|------|
| 1 | Create bug ticket | Immediate |
| 2 | Assign to engineer | 30 min |
| 3 | Escalate if needed | 2 hours |
| 4 | Fix deployed | 24 hours |

### P2 - Minor (Workaround Exists)

| Step | Action | Time |
|------|--------|------|
| 1 | Create bug ticket | Immediate |
| 2 | Add to sprint backlog | Same day |
| 3 | Fix deployed | 72 hours |

---

## Rollback Plan

### Triggers for Rollback

- [ ] >5% error rate for >15 minutes
- [ ] Authentication completely broken
- [ ] Data corruption detected
- [ ] Security vulnerability discovered

### Rollback Steps

| Step | Action | Owner | Time |
|------|--------|-------|------|
| 1 | Decision to rollback | CTO | - |
| 2 | Announce maintenance | PM | 5 min |
| 3 | Stop traffic (nginx) | DevOps | 2 min |
| 4 | Revert deployment | DevOps | 10 min |
| 5 | Verify rollback | Backend | 5 min |
| 6 | Resume traffic | DevOps | 2 min |
| 7 | Post-mortem scheduled | PM | - |

### Rollback Verification

- [ ] API health check passing
- [ ] Login working
- [ ] Dashboard loading
- [ ] No data loss

---

## Success Criteria

### Launch Day Success

| Criteria | Target | Required |
|----------|--------|----------|
| System uptime | 99.9% | Yes |
| Error rate | <1% | Yes |
| User logins | >10 | Yes |
| No P0 bugs | 0 | Yes |

### Week 1 Success

| Criteria | Target | Required |
|----------|--------|----------|
| Active users | >20 | Yes |
| Features adopted | >3 avg | Yes |
| User satisfaction | >7/10 | Yes |
| Bug resolution | >80% | No |

### Month 1 Success

| Criteria | Target | Required |
|----------|--------|----------|
| 90%+ adoption | 25+ users | Yes |
| NPS score | >40 | No |
| Gate evaluations | >100 | Yes |
| Evidence uploads | >50 | Yes |

---

## Key Contacts

### Engineering

| Role | Name | Slack | Phone |
|------|------|-------|-------|
| CTO | [Name] | @cto | [Phone] |
| Backend Lead | [Name] | @backend-lead | [Phone] |
| Frontend Lead | [Name] | @frontend-lead | [Phone] |
| DevOps Lead | [Name] | @devops-lead | [Phone] |

### Product

| Role | Name | Slack | Phone |
|------|------|-------|-------|
| CPO | [Name] | @cpo | [Phone] |
| PM | [Name] | @pm | [Phone] |

### Support

| Role | Name | Slack | Phone |
|------|------|-------|-------|
| Support Lead | [Name] | @support-lead | [Phone] |
| On-call | [Rotation] | @on-call | [Phone] |

---

## Appendix

### A. Pre-Launch Test Script

```bash
# Health checks
curl -s https://staging.sdlc.nqh.vn/health
curl -s https://staging.sdlc.nqh.vn/health/ready

# API verification
curl -s https://staging.sdlc.nqh.vn/api/docs

# Authentication test
# (manual - login with test account)

# Gate evaluation test
# (manual - evaluate sample gate)

# Evidence upload test
# (manual - upload sample file)
```

### B. Monitoring Dashboard URLs

| Dashboard | URL |
|-----------|-----|
| API Metrics | https://grafana.nqh.vn/d/api-metrics |
| Error Tracking | https://grafana.nqh.vn/d/error-tracking |
| User Activity | https://grafana.nqh.vn/d/user-activity |
| Infrastructure | https://grafana.nqh.vn/d/infrastructure |

### C. Support Resources

| Resource | Location |
|----------|----------|
| Onboarding Guide | /docs/05-Beta-Pilot/PILOT-ONBOARDING-GUIDE.md |
| Bug Triage | /docs/05-Beta-Pilot/BUG-TRIAGE-PROCESS.md |
| FAQ | /docs/05-Beta-Pilot/PILOT-ONBOARDING-GUIDE.md#faq |
| Support Channels | /docs/05-Beta-Pilot/SUPPORT-CHANNELS.md |

---

**Status**: READY FOR LAUNCH
**Target Date**: January 6, 2026
**Owner**: Product Team + Engineering

---

**Last Updated**: December 6, 2025
