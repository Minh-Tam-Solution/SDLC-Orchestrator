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
| **Standard** | $30/user/month | Small Teams | 3-10 users | Unlimited projects, Evidence Vault, email support |
| **Professional** | $60/user/month | Growth Teams | 10-50 users | SSO, advanced policies, priority support |
| **Enterprise** | Custom | Large Orgs | 50+ users | Dedicated support, custom integrations, SLA |

---

## 2. Feature Matrix by Tier

| Feature | Free | Standard | Professional | Enterprise |
|---------|------|----------|--------------|------------|
| **Projects** | 1 | Unlimited | Unlimited | Unlimited |
| **Users** | 2 | 10 | 50 | Unlimited |
| **Gates (G0.1-G4)** | ✅ | ✅ | ✅ | ✅ |
| **Evidence Vault** | 1GB | 10GB | 100GB | Unlimited |
| **Policy Packs** | 3 built-in | 10 built-in | All + custom | All + custom |
| **AI Assistance** | 100 req/month | 1,000 req/month | 10,000 req/month | Unlimited |
| **AI Detection** | ❌ | ✅ | ✅ | ✅ |
| **SAST Integration** | ❌ | ✅ | ✅ | ✅ |
| **GitHub Integration** | ✅ | ✅ | ✅ | ✅ |
| **GitLab/Bitbucket** | ❌ | ❌ | ✅ | ✅ |
| **SSO (SAML/OIDC)** | ❌ | ❌ | ✅ | ✅ |
| **Audit Logs** | 30 days | 1 year | 7 years | 7 years |
| **Support** | Community | Email | Priority | Dedicated |
| **SLA** | None | 99.5% | 99.9% | 99.99% |

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

## 4. Revenue Projections

### Year 1 (2026)

| Metric | Q1 | Q2 | Q3 | Q4 | Annual |
|--------|----|----|----|----|--------|
| **Teams** | 10 | 25 | 50 | 100 | 100 |
| **Avg Users/Team** | 8 | 8 | 8 | 8 | 8 |
| **MRR** | $2.4K | $6K | $12K | $24K | - |
| **ARR** | - | - | - | - | **$288K** |

### Year 2 (2027)

| Metric | Q1 | Q2 | Q3 | Q4 | Annual |
|--------|----|----|----|----|--------|
| **Teams** | 200 | 400 | 700 | 1,000 | 1,000 |
| **Avg Users/Team** | 10 | 10 | 10 | 10 | 10 |
| **MRR** | $60K | $120K | $210K | $300K | - |
| **ARR** | - | - | - | - | **$3.6M** |

### Year 3 (2028)

| Metric | Q1 | Q2 | Q3 | Q4 | Annual |
|--------|----|----|----|----|--------|
| **Teams** | 2,500 | 5,000 | 7,500 | 10,000 | 10,000 |
| **Avg Users/Team** | 12 | 12 | 12 | 12 | 12 |
| **MRR** | $900K | $1.8M | $2.7M | $3.6M | - |
| **ARR** | - | - | - | - | **$43.2M** |

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

### Break-even Analysis

```
Break-even = Operating Costs / (ARPU × Gross Margin)
           = $696,000 / ($2,880 × 0.80)
           = 302 teams

With 100 teams target in Year 1:
- Revenue: $288,000
- Costs: $696,000
- Gap: -$408,000 (requires funding)
```

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

## 10. Questions for Expert Review

1. **Price Point**: Is $30/user/month appropriate, or should we test higher/lower?
2. **Tier Structure**: Should we simplify to 3 tiers (Free, Standard, Enterprise)?
3. **Usage-Based**: Should AI usage be metered separately?
4. **Annual Discount**: Is 20% enough to incentivize annual commits?
5. **Enterprise Pricing**: What's the right approach for custom enterprise deals?

---

**Document Control**

| Field | Value |
|-------|-------|
| Author | PM + Finance Team, NQH Holdings |
| Status | Ready for External Review |

---

*"Price for value delivered, not market convention."*
