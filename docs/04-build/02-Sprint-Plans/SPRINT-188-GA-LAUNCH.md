---
sdlc_version: "6.1.0"
document_type: "Sprint Plan"
status: "PROPOSED"
sprint: "188"
spec_id: "SPRINT-188"
tier: "ENTERPRISE"
stage: "04 - Build"
---

# SPRINT-188 — GA Launch + Pricing Enforcement + Enterprise Sales

**Status**: PROPOSED (pending CTO approval)
**Sprint Duration**: 8 working days
**Sprint Goal**: General Availability launch — pricing enforced, enterprise sales pipeline open
**Epic**: ADR-059 Enterprise-First
**ADR**: ADR-059 (GA milestone)
**Dependencies**: Sprint 187 complete (Gate G4 declared Production Ready)
**Budget**: ~$5,120 (64 hrs at $80/hr)

---

## 1. Sprint Goal

Sprint 188 ships the product publicly. Three tracks:

1. **Pricing Enforcement** — Stripe subscription enforcement; tier limits enforced in production
2. **GA Launch** — Product Hunt, documentation site, pricing page live
3. **Enterprise Sales Enablement** — Security questionnaire, ROI calculator, case study

| Track | Priority | Days |
|-------|----------|------|
| Stripe pricing enforcement (tier limits) | P0 | 3 |
| Pricing page + documentation site | P0 | 2 |
| Product Hunt launch | P0 | 1 |
| Enterprise sales materials | P1 | 1 |
| CLAUDE.md v3.9.0 update | P2 | 0.5 |
| Sprint close + retrospective | -- | 0.5 |
| **Total** | | **8** |

---

## 2. Deliverables

| # | Deliverable | Description | Files | Sprint Day |
|---|------------|-------------|-------|------------|
| 1 | Stripe tier enforcement | LITE/STANDARD/PROFESSIONAL/ENTERPRISE limits enforced via Stripe webhooks | Modified | Day 1-2 |
| 2 | LITE usage limits | 1 project, 100MB, 4 gates/month, 1 member — enforced | Modified | Day 2 |
| 3 | Overage alert system | STANDARD: alert at 80% project/storage limits | New | Day 3 |
| 4 | Pricing page | `/pricing` page live (CTA to upgrade, plan comparison) | New | Day 3-4 |
| 5 | Documentation site | `docs.sdlcorchestrator.com` (MkDocs or Docusaurus) | New | Day 4 |
| 6 | Product Hunt launch | Listing, maker profile, launch post | External | Day 5 |
| 7 | Press release | "SDLC Orchestrator v2.0 — Enterprise-First AI Governance Platform" | New | Day 5 |
| 8 | Security questionnaire | Template for enterprise RFP responses | New | Day 6 |
| 9 | ROI calculator | GitHub Pages: hours saved × team size × hourly rate | New | Day 6 |
| 10 | Vietnam pilot case study | Anonymized: "Series B Vietnam fintech, 30 devs, SOC2 in 6 months" | New | Day 7 |
| 11 | CLAUDE.md v3.9.0 | Update current sprint + enterprise-first focus | Modified | Day 8 |

---

## 3. Daily Schedule

### Day 1-2: Stripe Pricing Enforcement

**Goal**: Make free tier limits real — LITE users hit actual walls

**Stripe webhook events to handle**:
- `customer.subscription.created` → activate tier
- `customer.subscription.updated` → tier upgrade/downgrade
- `customer.subscription.deleted` → downgrade to LITE
- `invoice.payment_failed` → grace period (7 days), then downgrade

**LITE tier limits** (enforced in `backend/app/middleware/usage_limits.py`):
```python
TIER_LIMITS = {
    "LITE": {
        "max_projects": 1,
        "max_storage_mb": 100,
        "max_gates_per_month": 4,
        "max_team_members": 1,
    },
    "STANDARD_STARTER": {
        "max_projects": 5,
        "max_storage_mb": 10_000,     # 10GB
        "max_gates_per_month": -1,    # Unlimited
        "max_team_members": 10,
    },
    "STANDARD_GROWTH": {
        "max_projects": 15,
        "max_storage_mb": 50_000,     # 50GB
        "max_gates_per_month": -1,
        "max_team_members": 30,
    },
    "PROFESSIONAL": {
        "max_projects": 20,
        "max_storage_mb": 100_000,    # 100GB
        "max_gates_per_month": -1,
        "max_team_members": -1,       # Unlimited
    },
    "ENTERPRISE": {
        "max_projects": -1,
        "max_storage_mb": -1,
        "max_gates_per_month": -1,
        "max_team_members": -1,
    },
}
```

**Enforcement points**:
- `POST /api/v1/projects` — check max_projects before creation (429 if limit hit)
- `POST /api/v1/evidence/upload` — check storage before upload (402 if limit hit)
- `POST /api/v1/gates` — check monthly gate count (429 if limit hit)
- `POST /api/v1/teams/members/invite` — check member count (402 if limit hit)

**HTTP status for limit violations**:
- `402 Payment Required` — tier upgrade needed (tier limit)
- `429 Too Many Requests` — usage quota exceeded (monthly reset)

**FOUNDER legacy plan** (grandfathered):
```python
# FOUNDER customers get STANDARD_GROWTH limits forever
# Billing SKU: FOUNDER_LEGACY
# Cannot be purchased by new customers after Sprint 181
TIER_LIMITS["FOUNDER"] = TIER_LIMITS["STANDARD_GROWTH"]
```

---

### Day 2-3: Overage Alert System

**STANDARD tier alert at 80%**:
```python
# backend/app/services/usage_alert_service.py

OVERAGE_THRESHOLDS = {
    "projects": 0.80,      # Alert when 80% of max_projects used
    "storage": 0.80,       # Alert when 80% of storage quota used
    "team_members": 0.80,  # Alert when 80% of member limit reached
}

async def check_overage_alerts(user: User, db: AsyncSession) -> None:
    """Check if user is approaching any tier limits. Send email if threshold crossed."""
    limits = TIER_LIMITS.get(user.subscription_plan, {})
    current_usage = await get_current_usage(user, db)

    for metric, threshold in OVERAGE_THRESHOLDS.items():
        max_val = limits.get(f"max_{metric}", -1)
        if max_val == -1:
            continue  # Unlimited
        if current_usage[metric] / max_val >= threshold:
            await send_overage_alert_email(
                user.email,
                metric=metric,
                current=current_usage[metric],
                max_val=max_val,
                upgrade_url=f"https://app.sdlcorchestrator.com/billing/upgrade",
            )
```

---

### Day 3-4: Pricing Page + Documentation Site

**Pricing page** (`/pricing`):
```
┌────────────────────────────────────────────────────────────────────────────┐
│  LITE (Free)    STANDARD ($99/mo)  PROFESSIONAL ($499/mo)  ENTERPRISE (Custom) │
│  1 project      5-15 projects      20 projects             Unlimited           │
│  4 gates/month  Unlimited gates    Unlimited               Unlimited           │
│  100MB          10-50GB            100GB                   Unlimited           │
│  1 member       10-30 members      Unlimited               Unlimited           │
│  [Get Started]  [Try Free 14 days] [Start Trial]           [Contact Sales]    │
└────────────────────────────────────────────────────────────────────────────┘
```

**Key landing page copy**:
- Headline: "The AI Governance Platform for Enterprise Engineering Teams"
- Sub: "From individual developer with TinySDLC → enterprise compliance with Orchestrator"
- Social proof: "5 Vietnam pilot customers • $0 to $150K ARR in 6 months"
- CTA: "Start PROFESSIONAL trial (no credit card)"

**Documentation site** (MkDocs Material theme, Apache 2.0):
```
docs.sdlcorchestrator.com/
├── getting-started/
│   ├── quickstart.md
│   ├── installation.md
│   └── first-gate-evaluation.md
├── enterprise/
│   ├── sso-setup.md (SAML + Azure AD)
│   ├── jira-integration.md
│   ├── slack-setup.md
│   └── soc2-evidence-pack.md
├── api-reference/
│   └── (auto-generated from OpenAPI spec)
└── changelog/
    └── v2.0.0.md
```

---

### Day 5: Product Hunt Launch

**Product Hunt listing**:
- Tagline: "Enterprise AI Governance Platform — Ship Better Software with Confidence"
- Description: 150-200 words covering: problem (AI code is ungoverned), solution (SDLC Orchestrator), differentiation (dynamic governance + enterprise SSO + compliance evidence)
- Gallery: 5 screenshots (gates dashboard, evidence vault, agent team, compliance pack, pricing)
- Maker comment: "We built this to solve our own problem as a Vietnam software team..."

**Launch activities** (Day 5):
- 9 AM ET: Post listing on Product Hunt
- 9 AM ET: Tweet from company Twitter/X
- 9 AM ET: LinkedIn post (CTO + CPO)
- 10 AM ET: TinySDLC README CTA added: "For enterprise → [SDLC Orchestrator](https://sdlcorchestrator.com)"
- 12 PM ET: Post in relevant subreddits (r/devops, r/ExperiencedDevs)
- All day: Respond to Product Hunt comments

---

### Day 6: Enterprise Sales Enablement

**Security questionnaire template** (`docs/09-govern/Security-Questionnaire.md`):
Answers to the 50 most common enterprise security RFP questions:
- Authentication: "SSO via SAML 2.0 + Azure AD. MFA enforced via IdP. JWT 15-min expiry."
- Data: "Evidence stored in MinIO S3 (region-configurable: VN/EU/US). AES-256 at rest."
- Compliance: "SOC2 Type II evidence pack available. GDPR erasure implemented."
- Availability: "99.9% SLA for ENTERPRISE tier. 4h P1 response. Dedicated CSM."
- Penetration testing: "External pen test completed Sprint 187. Report available under NDA."

**ROI Calculator** (GitHub Pages):
```
Team size: [___] developers
Hours saved per developer per week on governance: [___] hours
Developer hourly rate: [___] USD

Annual savings: {team_size × hours_saved × 52 × rate}
Orchestrator cost: {plan_cost × 12}
Net ROI: {savings - cost}
Payback period: {cost / (savings / 12)} months
```

---

### Day 7: Vietnam Pilot Case Study

**Anonymized case study** ("Series B Vietnam Fintech"):
```markdown
# How a 30-Developer Vietnam Fintech Achieved SOC2 in 6 Months

**Company**: Series B Vietnam fintech (anonymized)
**Team size**: 30 developers, 5 QA, 2 DevOps
**Challenge**: Enterprise client required SOC2 Type II; no governance process
**Time to value**: First gate evaluation in 5 minutes
**Result**: SOC2 evidence pack generated in 1 click after 6 months
**ROI**: $450K saved vs traditional SOC2 consultant engagement

Key quote: "SDLC Orchestrator made governance automatic. Our developers
didn't change their workflow — the platform collected evidence for them."
```

---

### Day 8: CLAUDE.md v3.9.0 + Sprint Close

**CLAUDE.md updates**:
1. Version: 3.8.0 → 3.9.0
2. Current Sprint: Sprint 179 → Sprint 188 (GA Launch)
3. Status: "Gate G4 APPROVED - Production Ready"
4. Enterprise-First focus section (from ADR-059)
5. Sprints 181-188 added to changelog

**Sprint close**:
1. SPRINT-188-CLOSE.md written
2. Final CHANGELOG.md entry for v2.0.0
3. Git tag: `v2.0.0-ga`
4. CEO announcement email to all customers

---

## 4. Success Criteria

| Criterion | Target | Measurement |
|-----------|--------|-------------|
| Stripe tier limits enforced | LITE/STD/PRO | All 4 limit types enforced |
| Pricing page live | Live | URL accessible |
| Docs site live | Live | docs.sdlcorchestrator.com accessible |
| Product Hunt posted | Posted | PH listing URL |
| Security questionnaire ready | Ready | File exists in docs/ |
| FOUNDER legacy handled | Correct | FOUNDER = STANDARD_GROWTH limits |
| Zero P0 bugs | 0 | CI clean |
| CLAUDE.md v3.9.0 | Updated | Version bump confirmed |

---

## 5. Post-Launch Targets (CPO)

| Quarter | Teams | ARR Target | Key Milestone |
|---------|-------|-----------|---------------|
| Q1 2026 (NOW) | 8-12 | $28K-$60K | 5 Vietnam pilots + 3-7 STANDARD |
| Q2 2026 | 18-25 | $65K-$120K | GA + 2 enterprise deals |
| Q3 2026 | 30-45 | $108K-$216K | SSO GA → regulated industry pipeline |
| Q4 2026 | 45-70 | $162K-$336K | 10+ enterprise + professional services |
| **Year 1 Total** | **45-70** | **$160K-$350K ARR** | |

---

## 6. Risks

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|-----------|
| Product Hunt doesn't trend | Medium | Low | Focus on direct enterprise outreach; PH is bonus |
| Stripe webhook delays (tier activation) | Medium | Medium | Implement grace period (7 days) before hard downgrade |
| LITE users hit limits on Day 1 | Low | Medium | Clear upgrade CTA in 402 response; friction by design |
| Documentation site incomplete | Low | Medium | Ship docs for top 3 use cases first; add incrementally |

---

## 7. Dependencies

| Dependency | Type | Status |
|-----------|------|--------|
| Sprint 187 complete (G4 declared) | Prerequisite | Required |
| Stripe account + webhook configured | Infrastructure | Already exists (Sprint 1) |
| Product Hunt account | External | Claim page before Day 5 |
| docs.sdlcorchestrator.com DNS | Infrastructure | Configure before Day 4 |
| Legal: pricing page copy approved | CPO | Required before pricing page goes live |
| CEO: announcement email | CEO | Required for Day 8 |

---

## 8. Definition of Done

- [ ] Stripe tier limits enforced for all 4 tiers
- [ ] FOUNDER legacy limits = STANDARD_GROWTH (grandfathered)
- [ ] Overage alerts at 80% for STANDARD tier
- [ ] Pricing page live at sdlcorchestrator.com/pricing
- [ ] Documentation site live at docs.sdlcorchestrator.com
- [ ] Product Hunt listing posted
- [ ] Security questionnaire template in docs/09-govern/
- [ ] ROI calculator live
- [ ] Vietnam pilot case study written
- [ ] CLAUDE.md v3.9.0 committed
- [ ] Git tag v2.0.0-ga created
- [ ] SPRINT-188-CLOSE.md written
- [ ] CEO announcement email sent

---

**Approval Required**: CEO + CTO + CPO (GA declaration is cross-executive)
**Budget**: ~$5,120 (8 days × 8 hrs × $80/hr)
**Risk Level**: LOW (no new tech; mostly coordination + marketing)

---

## Sprint 181-188 Completion — Full Roadmap Summary

| Sprint | Theme | Days | Budget | Risk | Status |
|--------|-------|------|--------|------|--------|
| 181 | OTT Foundation + Route Activation | 8 | $5,120 | MEDIUM | PROPOSED |
| 182 | Enterprise SSO Design + Teams | 6 | $3,840 | HIGH | PROPOSED |
| 183 | SSO Implementation + Compliance | 8 | $5,120 | HIGH | PROPOSED |
| 184 | Integrations + Tier Gates | 8 | $5,120 | MEDIUM | PROPOSED |
| 185 | Audit Trail + SOC2 Evidence | 8 | $5,120 | HIGH | PROPOSED |
| 186 | Multi-Region + Data Residency | 10 | $6,400 | VERY HIGH | PROPOSED |
| 187 | G4 Production Validation | 10 | $6,400 | HIGH | PROPOSED |
| 188 | GA Launch | 8 | $5,120 | LOW | PROPOSED |
| **Total** | **Enterprise Completion** | **66 days** | **$42,240** | — | |

**Estimated completion**: ~Q3 2026 (66 working days from Sprint 181 kickoff)
