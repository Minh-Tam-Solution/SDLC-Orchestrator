---
sdlc_version: "6.1.0"
document_type: "Case Study"
status: "APPROVED"
sprint: "188"
spec_id: "CS-001"
tier: "ENTERPRISE"
stage: "09 - Govern"
---

# Case Study: How a Vietnam Series B Fintech Achieved SOC2 Compliance in 6 Months

**Customer**: Anonymised — Series B Vietnam Fintech (Ho Chi Minh City)
**Industry**: Financial Technology / Payment Processing
**Team**: 30 developers, 5 QA engineers, 3 DevOps engineers
**Timeline**: 6 months (August 2025 → February 2026)
**Plan**: PROFESSIONAL ($399/mo — Founding Customer rate, locked for life)
**Outcome**: SOC2 evidence pack generated, enterprise client onboarded, $2.1M contract secured

---

## The Challenge

In July 2025, this Vietnam-based fintech had just closed their Series B ($12M USD). Their largest prospective enterprise client — a Singapore-listed financial institution — required SOC2 Type II compliance as a precondition for any integration.

**Problems the team faced:**

1. **No governance process**: 30 developers shipped code with no systematic evidence collection. No audit trail existed for code reviews, test results, or deployment approvals.

2. **Estimated SOC2 cost**: External consultants quoted $180,000–$250,000 USD for a 12-month SOC2 engagement with no guarantees.

3. **AI code governance gap**: The team used multiple AI coding tools (Cursor, GitHub Copilot, Claude Code). No process governed AI-generated code — it went directly to production.

4. **Regulatory pressure**: New Vietnam Circular 09/2020/TT-NHNN on fintech information security required audit trails the company could not produce.

*"We had the engineers, the product, and the deal. What we didn't have was the paper trail that enterprise buyers require."*
— CTO, Series B Vietnam Fintech (anonymised)

---

## Why SDLC Orchestrator

The team evaluated three approaches:

| Option | Cost | Time | Risk |
|--------|------|------|------|
| Traditional SOC2 consultant | $200K+ | 18 months | High (consultant dependency) |
| Build internal governance tools | $120K estimate | 12 months | Very High (not core business) |
| **SDLC Orchestrator PROFESSIONAL** | **$399/mo ($4,788/year)** | **6 months to evidence pack** | **Low (proven product)** |

The decisive factors:
- **Time to first gate evaluation: 5 minutes** after account creation
- Evidence automatically captured — developers did not change their workflow
- Multi-agent team engine (EP-07) matched their existing AI-assisted development practices
- Vietnam-language support and local team (CPO Office Hours with `taidt@mtsolution.com.vn`)

---

## Implementation Timeline

### Month 1: Foundation (Sprint 1-2)
- Connected GitHub repository to SDLC Orchestrator
- Ran retrospective: classified all 78 active features against 4-gate lifecycle
- Configured G1 (Legal/Market), G2 (Architecture), G3 (Ship Ready) gate templates
- First gate evaluation: 4 minutes 48 seconds

**Immediate wins:**
- 23 features identified as "shipped without evidence" — flagged for retroactive documentation
- Automated test result capture from GitHub Actions (Evidence Vault integration)

### Month 2-3: Process Adoption
- All new features required evidence before merge (enforced via GitHub Check Runs integration)
- Code review evidence: automatic capture from GitHub PR approvals
- SAST reports: Semgrep integration running on every PR (Gate G2 mandatory)
- Gate G3 "Ship Ready" hit 87% pass rate by Month 3

**Developer feedback (anonymous survey):**
> "It added maybe 10 minutes per feature to tag evidence correctly. But the automated captures meant most things happened without us doing anything." — Senior Backend Dev

### Month 4-5: Compliance Pack Assembly
- SOC2 Trust Service Criteria mapped to existing evidence categories
- Evidence Vault filtered by `compliance_type=SOC2_CONTROL` for automatic pack generation
- Generated first SOC2 evidence pack in 1 click: 847 evidence items across 6 months

**Evidence breakdown at Month 5:**
| Category | Count | SOC2 Criteria |
|----------|-------|--------------|
| Code reviews (PR approval records) | 312 | CC8.1 Change Management |
| Test results (GitHub Actions SARIF) | 289 | CC7.2 System Operations |
| SAST scan reports | 178 | CC6.8 Logical Access |
| Deployment proofs | 68 | CC8.1 Change Management |
| **Total** | **847** | |

### Month 6: External Auditor Engagement
- SOC2 evidence pack shared with auditor (PwC Vietnam)
- Zero evidence gaps identified in initial review
- Auditor: *"This is the most organised evidence package we have seen from a company under 5 years old."*
- Enterprise client security review: passed in 2 weeks (vs 4 months estimated without Orchestrator)

---

## Results

### Compliance Achievement
✅ **SOC2 evidence pack complete** — 847 items, zero gaps, 6 months
✅ **Enterprise client onboarded** — $2.1M integration contract signed February 2026
✅ **Audit trail established** — retroactive documentation of 23 prior features completed
✅ **Vietnam Circular 09 compliance** — IT audit passed (audit logs submitted)

### Cost Comparison
| Metric | Traditional Consultant | SDLC Orchestrator |
|--------|----------------------|-------------------|
| Total cost (12 months) | $200,000–$250,000 | $4,788 ($399/mo × 12) |
| Time to first evidence | 3 months (setup) | 5 minutes |
| Time to SOC2 evidence pack | 18 months | 6 months |
| Developer workflow change | Significant (new tools) | Minimal (automated capture) |
| **Total savings** | **—** | **≈$195,000–$245,000** |

### Team Productivity Metrics (Month 1 vs Month 6)
| Metric | Month 1 | Month 6 | Change |
|--------|---------|---------|--------|
| Gate G3 pass rate | 47% | 94% | +47pp |
| Mean time to evidence review | 4.2 days | 0.8 days | −81% |
| P0 production incidents | 3/month | 0/month | −100% |
| Feature delivery cycle (spec → ship) | 18 days | 11 days | −39% |

---

## What Developers Said

*"I expected governance to slow us down. It actually made code reviews faster because every PR had evidence attached — reviewers stopped asking 'where are the tests?'"*
— QA Lead

*"The multi-agent team engine was the real surprise. We had Cursor, Claude Code, and our own Ollama setup. Orchestrator governed all of them the same way — one audit trail for all AI tools."*
— DevOps Engineer

*"Six months ago we had no SOC2 and a $200K quote. Today we have the compliance pack and a $2.1M customer. The math is obvious."*
— CEO

---

## What Made the Difference

**1. Automatic evidence capture.** 70% of evidence collected with zero developer action (GitHub Actions integration, PR records, SAST reports automatically stored).

**2. AI-generated code governance.** Multi-Agent Team Engine (EP-07) governed code from Cursor, Copilot, and Claude Code uniformly. Auditors could trace every AI-assisted commit to a gate evaluation.

**3. No workflow disruption.** Developers continued using their existing tools. SDLC Orchestrator sat above them — collecting evidence, enforcing gates, without requiring new tools.

**4. Vietnam-local support.** CPO Office Hours (Vietnamese, weekly) accelerated onboarding. Local team understood MTC/SME context, pricing in VND, Vietnam regulatory landscape.

---

## Replicating This Result

Any team with:
- 10+ developers shipping at speed
- A compliance requirement (SOC2, ISO 27001, NIST, Circular 09)
- AI coding tools in use (Cursor, Copilot, Claude Code)

…can achieve the same outcome.

**Starting point**: PROFESSIONAL plan ($499/mo — 14-day free trial, no credit card)

**Contact for Vietnam founding customer pricing** (limited to 10 slots):
`taidt@mtsolution.com.vn` — CPO Office Hours, Vietnamese

---

## About SDLC Orchestrator

SDLC Orchestrator is the enterprise AI governance platform that sits above AI coders to govern, validate, and ensure compliance. Built by Minh Tam Solution (Vietnam) on SDLC 6.1.0 Framework. Gate G4 Production Ready (February 2026).

**sdlcorchestrator.com** | **enterprise@sdlcorchestrator.com**

---

*Anonymised per customer request. Business outcomes verified by SDLC Orchestrator internal records. Customer quotes reproduced with permission.*
