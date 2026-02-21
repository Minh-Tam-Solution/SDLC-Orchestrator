# Pricing Model - SDLC Orchestrator
## Revenue Strategy & Unit Economics

**Version**: 1.0.0
**Date**: December 23, 2025
**Purpose**: External Expert Review - Business Model

---

## 1. Pricing Tiers

| Tier | Price | Target Segment | Team Size | Included |
|------|-------|----------------|-----------|----------|
| **Free** | $0 | Solo/Learners | 1-2 users | 1 project, basic gates, community support |
| **Founder** | $99/team/month | Vietnam SME | ≤5 users | 1 product, IR-based codegen, email support |
| **Standard** | $30/user/month | Small Teams | 3-10 users | Unlimited projects, Evidence Vault, email support |
| **Professional** | $60/user/month | Growth Teams | 10-50 users | SSO, advanced policies, priority support |
| **Enterprise** | Custom | Large Orgs | 50+ users | Dedicated support, custom integrations, SLA |

### Founder Plan Details (NEW - Vietnam SME Wedge)

| Attribute | Value |
|-----------|-------|
| **Price** | $99/team/month (~2.5M VND) |
| **Target** | Vietnam SME, Non-tech founders, Startups <10 people |
| **Seats** | ≤5 users (flat team pricing, prevents arbitrage) |
| **Projects** | 1 product (multiple repos for same product) |
| **Included Features** | EP-06 IR-based codegen, Evidence Vault (10GB), Policy Guards |
| **AI Codegen** | Native OSS (qwen3-coder) + BYO option |
| **Support** | Email + Community Discord |
| **SLA** | 99.5% uptime |

**Why Founder Plan?**: Expert feedback indicated per-seat pricing doesn't work for SME/non-tech founders. Flat team pricing removes adoption friction for Vietnam wedge strategy.

**Arbitrage Prevention (Sprint 88 Fix)**: Limited to ≤5 users to prevent arbitrage with Standard plan. For 6+ users, Standard plan ($30/user) is more appropriate. This ensures: Founder ($99/5 users = $19.80/user) remains attractive for tiny teams, while Standard ($30/user) is better value for growing teams.

---

## 2. Feature Matrix by Tier

| Feature | Free | Founder | Standard | Professional | Enterprise |
|---------|------|---------|----------|--------------|------------|
| **Projects** | 1 | 1 product | Unlimited | Unlimited | Unlimited |
| **Users** | 2 | ≤5 users | 10 | 50 | Unlimited |
| **Gates (G0.1-G4)** | ✅ | ✅ | ✅ | ✅ | ✅ |
| **Evidence Vault** | 1GB | 10GB | 10GB | 100GB | Unlimited |
| **Policy Packs** | 3 built-in | 5 built-in | 10 built-in | All + custom | All + custom |
| **AI Assistance** | 100 req/month | 500 req/month | 1,000 req/month | 10,000 req/month | Unlimited |
| **EP-06 Codegen** | ❌ | ✅ Native | ✅ BYO | ✅ BYO + Native | ✅ Custom |
| **AI Detection** | ❌ | ✅ | ✅ | ✅ | ✅ |
| **SAST Integration** | ❌ | ✅ | ✅ | ✅ | ✅ |
| **GitHub Integration** | ✅ | ✅ | ✅ | ✅ | ✅ |
| **GitLab/Bitbucket** | ❌ | ❌ | ❌ | ✅ | ✅ |
| **SSO (SAML/OIDC)** | ❌ | ❌ | ❌ | ✅ | ✅ |
| **Audit Logs** | 30 days | 1 year | 1 year | 7 years | 7 years |
| **Support** | Community | Email + Discord | Email | Priority | Dedicated |
| **SLA** | None | 99.5% | 99.5% | 99.9% | 99.99% |

---

## 3. Pricing Rationale

### Why $30/user/month (Standard)?

| Factor | Analysis |
|--------|----------|
| **Value Delivered** | Saves $60-70K/engineer/year in waste → $5K/engineer/month value |
| **Comparable Tools** | Jira ($16), Linear ($8), GitLab ($29) |
| **Premium Justification** | Governance + AI + Evidence = unique value |
| **Willingness to Pay** | Survey: 78% would pay $20-50/user for governance |

### Price Sensitivity Analysis

| Price Point | Expected Conversion | Revenue Impact |
|-------------|---------------------|----------------|
| $15/user | +50% conversions | -25% revenue (net negative) |
| $30/user | Baseline | Baseline |
| $45/user | -30% conversions | +10% revenue (marginal) |
| $60/user | -50% conversions | -10% revenue (net negative) |

**Conclusion**: $30/user is optimal for Year 1.

---

## 4. Revenue Projections (Revised per Expert Feedback)

### Year 1 (2026) - Realistic

| Metric | Q1 | Q2 | Q3 | Q4 | Annual |
|--------|----|----|----|----|--------|
| **Total Teams** | 5 | 15 | 30 | 40 | 40 |
| **Founder Plan** | 3 | 10 | 18 | 25 | 25 |
| **Standard Plan** | 2 | 5 | 10 | 12 | 12 |
| **Pro/Enterprise** | 0 | 0 | 2 | 3 | 3 |
| **MRR** | $0.9K | $2.7K | $5.4K | $7.2K | - |
| **ARR** | - | - | - | - | **$86K-$144K** |

**Breakdown**:
- Founder: 25 teams × $99/mo = $2,475/mo
- Standard: 12 teams × 8 users × $30 = $2,880/mo
- Pro/Enterprise: 3 teams × $1,500/mo avg = $4,500/mo
- **Total MRR**: ~$10K | **ARR**: ~$120K (midpoint)

### Year 2 (2027) - Growth

| Metric | Q1 | Q2 | Q3 | Q4 | Annual |
|--------|----|----|----|----|--------|
| **Total Teams** | 80 | 150 | 220 | 300 | 300 |
| **Founder Plan** | 50 | 90 | 120 | 150 | 150 |
| **Standard Plan** | 25 | 45 | 70 | 100 | 100 |
| **Pro/Enterprise** | 5 | 15 | 30 | 50 | 50 |
| **MRR** | $18K | $36K | $54K | $72K | - |
| **ARR** | - | - | - | - | **$432K-$864K** |

### Year 3 (2028) - Scale

| Metric | Q1 | Q2 | Q3 | Q4 | Annual |
|--------|----|----|----|----|--------|
| **Total Teams** | 500 | 700 | 850 | 1,000 | 1,000 |
| **Founder Plan** | 250 | 350 | 400 | 450 | 450 |
| **Standard Plan** | 175 | 240 | 300 | 350 | 350 |
| **Pro/Enterprise** | 75 | 110 | 150 | 200 | 200 |
| **MRR** | $120K | $170K | $210K | $250K | - |
| **ARR** | - | - | - | - | **$1.4M-$2.9M** |

**Why These Numbers?**:
- Expert feedback: "100→1000→10000 unrealistic for 8.5 FTE"
- Year 1: Focus on Vietnam SME wedge (Founder Plan) + 10-15 Global teams
- Year 2: 3x growth with product-market fit validated
- Year 3: 3x growth with sales team added

---

## 5. Unit Economics

### Target Metrics

| Metric | Target | Industry Benchmark |
|--------|--------|-------------------|
| **CAC** (Customer Acquisition Cost) | <$1,000 | $500-$2,000 |
| **LTV** (Lifetime Value) | >$10,000 | Varies |
| **LTV:CAC Ratio** | >10:1 | 3:1 is healthy |
| **Payback Period** | <6 months | 12-18 months |
| **Gross Margin** | >80% | 70-80% |
| **Net Revenue Retention** | >120% | 100-120% |
| **Churn Rate** | <5% annually | 5-10% |

### LTV Calculation

```
LTV = (ARPU × Gross Margin) / Churn Rate

Where:
- ARPU = $30/user × 8 users = $240/team/month = $2,880/team/year
- Gross Margin = 80%
- Churn Rate = 5%/year

LTV = ($2,880 × 0.80) / 0.05 = $46,080
```

### CAC Calculation (Year 1 Target)

```
CAC = (Marketing + Sales) / New Customers

Target: <$1,000 per team

Approach:
- PLG (Product-Led Growth): Self-serve signup
- Content marketing: Blog, case studies, webinars
- Community: Discord, meetups
- No outbound sales in Year 1
```

---

## 6. Expansion Revenue

### Upsell Paths

| From → To | Trigger | Revenue Impact |
|-----------|---------|----------------|
| Free → Standard | Project limit hit | +$240/month |
| Standard → Professional | SSO requirement | +$300/month |
| Professional → Enterprise | Custom needs | +$1,000+/month |

### Seat Expansion

| Scenario | Monthly Revenue Impact |
|----------|----------------------|
| Team grows from 8 → 10 users | +$60/month (+25%) |
| Team grows from 10 → 20 users | +$300/month (+100%) |
| Add second team | +$240/month |

### Net Revenue Retention Target: 120%

```
NRR = (Starting MRR + Expansion - Contraction - Churn) / Starting MRR

Example:
- Starting MRR: $10,000
- Expansion: +$3,000 (seat growth, upgrades)
- Contraction: -$500 (downgrades)
- Churn: -$500 (lost customers)
- Ending MRR: $12,000

NRR = $12,000 / $10,000 = 120%
```

---

## 7. Cost Structure

### Infrastructure Costs (per 100 teams)

| Component | Monthly Cost |
|-----------|--------------|
| Cloud hosting (AWS/GCP) | $2,000 |
| AI inference (Ollama) | $50 |
| AI fallback (Claude/GPT) | $500 |
| Database (PostgreSQL) | $300 |
| Object storage (S3) | $200 |
| Monitoring (Grafana) | $100 |
| **Total Infrastructure** | **$3,150** |

### Cost per Team

```
Infrastructure cost per team = $3,150 / 100 = $31.50/month
Revenue per team (Standard) = $240/month
Gross margin = ($240 - $31.50) / $240 = 87%
```

### Operating Costs (Year 1)

| Category | Annual Cost |
|----------|-------------|
| Engineering (5 FTE) | $400,000 |
| Product (1 FTE) | $80,000 |
| Design (0.5 FTE) | $40,000 |
| Marketing (1 FTE) | $80,000 |
| G&A (0.5 FTE) | $40,000 |
| Infrastructure | $36,000 |
| Tools & Services | $20,000 |
| **Total Operating** | **$696,000** |

### Break-even Analysis (Updated)

```
Break-even = Operating Costs / (Blended ARPU × Gross Margin)

Blended ARPU Calculation:
- Founder Plan: $99/mo × 12 = $1,188/year
- Standard Plan: $240/mo × 12 = $2,880/year
- Pro/Enterprise: $1,500/mo × 12 = $18,000/year

Year 1 Blended ARPU (40 teams, 62.5% Founder, 30% Standard, 7.5% Pro):
= (0.625 × $1,188) + (0.30 × $2,880) + (0.075 × $18,000)
= $743 + $864 + $1,350 = $2,957/team/year

Break-even = $696,000 / ($2,957 × 0.80) = 294 teams

With 40 teams target in Year 1:
- Revenue: ~$120,000
- Costs: $696,000
- Gap: -$576,000 (requires funding)

Path to Profitability: Year 3 (300-400 teams)
```

**Note**: Year 1 is intentionally investment-heavy to establish Vietnam wedge. Founder Plan has lower ARPU but higher conversion, creating flywheel for Year 2-3.

---

## 8. Competitive Pricing Analysis

| Competitor | Pricing | Our Position |
|------------|---------|--------------|
| **Jira** | $8-16/user | 2-4x premium (justified by governance) |
| **Linear** | $8/user | 4x premium (justified by evidence) |
| **GitLab** | $5-29/user | Comparable on high end |
| **SonarQube** | $150-450/month | Cheaper per team |
| **Backstage** | Free + hosting | Premium for managed service |

---

## 9. Pricing Experiments (Year 1)

| Experiment | Hypothesis | Metric |
|------------|------------|--------|
| Annual discount (20%) | Improves cash flow, retention | % annual vs monthly |
| Team plan (flat fee) | Simplifies pricing | Conversion rate |
| Usage-based AI | Aligns cost with value | Revenue per team |
| Startup discount (50%) | Captures early-stage market | Pipeline growth |

---

## 10. Expert Feedback Applied

| Original Question | Expert Feedback | Resolution |
|-------------------|-----------------|------------|
| Is $30/user/month appropriate? | Works for Global, not for Vietnam SME | Added Founder Plan at $99/team flat |
| Should we simplify tiers? | No, add SME tier instead | Added Founder Plan (5 tiers total) |
| Revenue projections realistic? | No, 100→1000→10000 too aggressive | Revised to 40→300→1000 teams |
| Per-seat pricing for SME? | Doesn't work, need flat team pricing | Founder Plan is unlimited seats |
| Year 1 target achievable? | 100 teams unrealistic | Reduced to 30-50 teams |

---

**Document Control**

| Field | Value |
|-------|-------|
| Author | PM + Finance Team, Nhat Quang Holding |
| Approved By | CTO + CEO |
| Status | Updated per Expert Feedback (Dec 23, 2025) |
| Version | 1.1.0 |

---

*"Founder Plan for Vietnam wedge, Standard/Pro for Global scale."*
