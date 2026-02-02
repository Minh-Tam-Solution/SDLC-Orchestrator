# CEO Workflow Contract
## SDLC Orchestrator Governance System

**Version:** 1.0
**Effective Date:** January 27, 2026
**Parties:** CEO (Tai) ↔ SDLC Orchestrator System

---

## 1. PURPOSE

This contract defines the **operating agreement** between CEO and the SDLC Orchestrator
Governance System. It specifies what the CEO **will do**, **will NOT do**, and
**delegates to the system**.

**Goal:** Reduce CEO governance time from **40 hours/sprint → 10 hours/sprint**
by establishing clear boundaries and trust in automated governance.

---

## 2. CEO COMMITMENTS

### 2.1 What CEO Will NOT Do Anymore

| Activity | Before | After | Rationale |
|----------|--------|-------|-----------|
| Review PRs with Vibecoding Index < 30 (Green) | Review all | **NO REVIEW** | System auto-approves |
| Check ownership headers | Manual check | **NO CHECK** | System enforces |
| Verify ADR linkage | Manual check | **NO CHECK** | System enforces |
| Validate test coverage | Manual check | **NO CHECK** | CI/CD enforces |
| Review intent documents for format | Read all | **NO FORMAT CHECK** | Auto-generated |
| Chase developers for compliance docs | Email/Slack | **NO CHASING** | System blocks until compliant |

**CEO Signature Commitment:**
> "I commit to NOT manually reviewing PRs that the system marks as Green (Index < 30).
> I trust the system to catch issues at lower index levels."
>
> Signed: _________________ Date: _____________

### 2.2 What CEO Will Do

| Activity | Trigger | Action | Time Budget |
|----------|---------|--------|-------------|
| Review PRs with Index > 80 (Red) | System notification | Deep review within 4 hours | ~5 hours/sprint |
| Review PRs with Index 61-80 (Orange) | Dashboard queue | Spot-check within 24 hours | ~3 hours/sprint |
| Approve governance exceptions | Exception request | Review & decide within 24 hours | ~1 hour/sprint |
| Weekly governance review | Friday 2pm | Review dashboard, calibrate thresholds | ~1 hour/sprint |

**Total CEO Governance Time Budget: 10 hours/sprint**

### 2.3 What CEO Delegates to System

| Decision | Delegated To | CEO Override Condition |
|----------|--------------|----------------------|
| Auto-approve Green PRs | System | Never (unless Index miscalculated) |
| Block non-compliant PRs | System | Emergency hotfix only (Break Glass) |
| Calculate Vibecoding Index | System | CEO can adjust weights weekly |
| Send rejection messages | System | CEO can edit message templates |
| Track compliance metrics | System | CEO reviews weekly |

---

## 3. SYSTEM COMMITMENTS

### 3.1 What System Guarantees

| Guarantee | SLA | Measurement |
|-----------|-----|-------------|
| Index calculation accuracy | > 95% CEO agreement | Weekly calibration |
| Auto-generation availability | > 99% uptime | Fallback to templates |
| Governance latency | < 500ms P95 | Monitoring dashboard |
| False positive rate | < 10% | CEO override tracking |
| Actionable error messages | 100% with CLI command | Template coverage |

### 3.2 What System Will NOT Do

- **Will NOT** block developers due to auto-generation failure
- **Will NOT** require CEO approval for Green PRs
- **Will NOT** allow bypass without audit trail
- **Will NOT** change index weights without CEO approval

---

## 4. TRUST CALIBRATION PROCESS

### 4.1 Initial Calibration (Phase 0)

**CEO + Tech Lead Session (2 hours):**

1. Review 10 recent PRs that CEO rejected
2. For each rejection, identify:
   - What signal should have caught this?
   - What index threshold would have flagged it?
3. Configure `governance_signals.yaml` based on findings
4. Document "CEO's smell" preferences

**Output:** `docs/phase-0/CEO-Smell-Calibration.md`

### 4.2 Ongoing Calibration (Weekly)

| Day | Activity |
|-----|----------|
| Monday | System sends weekly report: Index accuracy, CEO overrides |
| Friday | CEO reviews dashboard, adjusts weights if needed |
| Monthly | Full calibration review with Tech Lead |

### 4.3 Recalibration Triggers

| Trigger | Action |
|---------|--------|
| CEO overrides > 3 Green PRs in a week | Emergency calibration session |
| False positive rate > 10% | Adjust thresholds down |
| False negative (bug in Green PR) | Adjust thresholds up, post-mortem |

---

## 5. ESCALATION & OVERRIDE

### 5.1 CEO Override Rights

CEO **always retains** the right to:
- Override any system decision
- Adjust index weights
- Approve governance exceptions
- Initiate Break Glass procedure

### 5.2 Override Audit

All CEO overrides are logged:
```yaml
override_log:
  pr_number: 234
  system_decision: "auto_approve"
  ceo_override: "reject"
  reason: "Security concern not detected"
  action: "Recalibrate security signal"
```

---

## 6. SUCCESS METRICS

### 6.1 CEO Time Saved

| Week | Target | Measurement Method |
|------|--------|-------------------|
| Week 2 | -25% (30 hours) | CEO time tracking |
| Week 4 | -50% (20 hours) | CEO time tracking |
| Week 8 | -75% (10 hours) | CEO time tracking |

### 6.2 Trust Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| CEO agreement with auto-approvals | > 95% | Sampling |
| CEO override rate | < 5% | Override log |
| Index accuracy | > 95% | Weekly calibration |

---

## 7. CONTRACT REVIEW

This contract will be reviewed:
- **Week 2:** Initial adjustment based on Warning Mode data
- **Week 4:** Full review before Soft Enforcement
- **Week 8:** Final review before Full Enforcement
- **Quarterly:** Ongoing maintenance

---

## 8. SIGNATURES

### CEO Commitment

I, **Tai (CEO)**, commit to:
1. NOT reviewing Green PRs (Index < 30)
2. Trusting system auto-approvals
3. Participating in weekly calibration
4. Tracking my governance time

**Signature:** ✅ **APPROVED**
**Date:** January 28, 2026

### CTO Commitment

I, **Nhat Quang (CTO)**, commit to:
1. Ensuring system meets SLAs
2. Maintaining kill switch readiness
3. Supporting CEO calibration sessions
4. Escalating system issues immediately

**Signature:** ✅ **APPROVED**
**Date:** January 28, 2026

---

## APPENDIX A: CEO Dashboard Specification

### What CEO Sees Daily

```
┌─────────────────────────────────────────────────────────────────┐
│                    CEO GOVERNANCE DASHBOARD                     │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│   ⏱️ TIME SAVED TODAY: 2.5 hours                               │
│   📊 PRs AUTO-APPROVED: 8                                       │
│   🔴 PENDING YOUR DECISION: 2                                   │
│                                                                 │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│   🚨 RED QUEUE (Index > 80) - MUST REVIEW                      │
│   ├── PR #234 - Index: 87 - Auth module, 92% AI-generated     │
│   └── PR #241 - Index: 82 - Payment flow, 14 files changed    │
│                                                                 │
│   ⚠️ ORANGE QUEUE (Index 61-80) - SPOT CHECK                   │
│   ├── PR #245 - Index: 71 - New feature, low test coverage    │
│   └── PR #248 - Index: 65 - Refactor, 6 modules touched       │
│                                                                 │
│   ✅ GREEN (Auto-Approved Today): 8 PRs                        │
│   └── [View list for audit if needed]                          │
│                                                                 │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│   📈 WEEKLY TREND                                               │
│   ├── CEO Time: 8h (target: 10h) ✅                            │
│   ├── Auto-Approve Rate: 78% (target: 80%) ⚠️                  │
│   └── Override Rate: 3% (target: <5%) ✅                       │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### What CEO Does NOT See (By Design)

- Individual compliance checklists
- Detailed error messages (dev sees these)
- Auto-generation logs
- Low-level audit trail
