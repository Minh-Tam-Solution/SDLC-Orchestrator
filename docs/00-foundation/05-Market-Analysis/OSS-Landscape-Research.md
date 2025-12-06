# OSS Landscape Research
## Open Source Software Integration Strategy and License Analysis

**Version**: 1.0.0
**Date**: November 13, 2025
**Status**: ACTIVE - STAGE 00 FOUNDATION
**Authority**: CEO Approval (9.5/10), CTO Review (8.5/10), Legal Review (PENDING Week 2)
**Foundation**: Product Vision v1.0, Competitive Landscape v1.0
**Stage**: Stage 00 (WHY - Project Foundation)

---

## Document Purpose (Stage 00 Focus: WHY)

This document answers **WHY we're using OSS components and WHY Option C (Hybrid)**, not HOW we'll implement integrations (Stage 02 scope).

**Key Questions Answered**:
- WHY use OPA vs build custom policy engine? (cost, time, quality)
- WHY Option C (Hybrid) vs Option A (Pure OSS) or Option B (Pure Proprietary)? (competitive moat, speed to market)
- WHY is AGPL containment critical? (legal risk, business model)
- WHY these specific OSS components? (evaluation criteria, alternatives considered)

**Out of Scope** (Stage 02):
- Integration architecture (API design, service boundaries)
- AGPL containment implementation (docker-compose, separate processes)
- OSS contribution strategy (upstreaming patches, community engagement)

---

## Executive Summary

### OSS Strategy: Option C (Hybrid Approach)

**Architecture**:
```
┌─────────────────────────────────────────────────────────┐
│ Layer 1: User-Facing (PROPRIETARY - Apache-2.0)        │
│ - React Dashboard, VS Code Extension, YAML Policy Packs│
└─────────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────────┐
│ Layer 2: Business Logic (PROPRIETARY - Apache-2.0)     │
│ - Gate Engine Wrapper, Evidence Vault API, AI Context  │
└─────────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────────┐
│ Layer 3: Integration (THIN WRAPPER - Apache-2.0)       │
│ - opa_service.py, minio_service.py, grafana_service.py │
└─────────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────────┐
│ Layer 4: Infrastructure (OSS - AGPL/Apache-2.0)        │
│ - OPA, MinIO, Grafana, PostgreSQL, Redis               │
└─────────────────────────────────────────────────────────┘
```

**Why Hybrid**:
1. **Speed to Market**: Leverage OSS (don't rebuild policy engine) → 90 days to MVP (vs 6-12 months)
2. **Competitive Moat**: SDLC 4.8 methodology + 100+ policy packs = proprietary IP (1-2 years to replicate)
3. **Cost Efficiency**: OSS infra free (vs $50K-$100K/year for proprietary equivalents)
4. **Legal Safety**: AGPL containment strategy (thin integration layer, separate processes)

---

### OSS Components Selected (5 Core)

| Component | License | Version | Purpose | AGPL Risk |
|-----------|---------|---------|---------|-----------|
| **OPA** | Apache-2.0 | v0.58.0 | Policy engine for Gate Engine | ✅ SAFE |
| **MinIO** | AGPL v3 | Latest | S3-compatible Evidence Vault storage | 🔴 HIGH (contained) |
| **Grafana** | AGPL v3 | 10.2.0 | Dashboard metrics visualization | 🔴 HIGH (contained) |
| **PostgreSQL** | PostgreSQL | 15.5 | Primary database | ✅ SAFE |
| **Redis** | BSD-3 | 7.2 | Caching + sessions | ✅ SAFE |

**Total OSS Value**: $120K/year (if built proprietary)
**Total OSS Cost**: $0/year (self-hosted) + $12.6K/year (AWS infrastructure)

---

### Legal Review (CRITICAL - Week 2)

**Status**: PENDING (external legal counsel)

**Key Questions for Legal**:
1. ✅ **OPA (Apache-2.0)**: Can we wrap OPA without releasing our policy packs? → Expected: YES
2. 🔴 **MinIO (AGPL v3)**: Can we use MinIO via API without triggering AGPL? → Expected: YES (with containment)
3. 🔴 **Grafana (AGPL v3)**: Can we embed Grafana dashboards without triggering AGPL? → Expected: YES (with iframe)

**Go/No-Go Decision** (Week 2):
- ✅ GO: Legal approves AGPL containment strategy → proceed with Option C
- 🔴 NO-GO: Legal cannot approve → pivot to Option A (pure OSS) OR Option B (proprietary rewrite)

---

## OSS Component Evaluation

### Component 1: Policy Engine (OPA vs Alternatives)

#### Open Policy Agent (OPA) - SELECTED ✅

**License**: Apache-2.0 (permissive, no copyleft)
**Version**: v0.58.0 (latest stable, Dec 2024)
**Maintainer**: CNCF (graduated project, stable governance)
**Adoption**: 10,000+ companies (Netflix, Cloudflare, Pinterest, Intuit)

**Strengths**:
- **Mature**: 5+ years production-ready (launched 2018, graduated 2021)
- **Performance**: 10K+ policy evaluations/sec (benchmark: 500-node K8s cluster)
- **Flexibility**: Rego language (policy-as-code for ANY domain, not just K8s)
- **Integrations**: 50+ integrations (Kubernetes, Terraform, Envoy, HTTP APIs)
- **License**: Apache-2.0 (can wrap, no copyleft contamination)

**Weaknesses**:
- **Learning Curve**: Rego language unfamiliar (vs Python/JavaScript)
- **No UI**: CLI-only (we must build dashboard)
- **Not SDLC-Aware**: Generic policy engine (we add SDLC 4.8 policies)

**Why Selected**:
- **Speed**: Don't rebuild policy engine (6 months saved)
- **Quality**: Battle-tested (Netflix production for 4+ years)
- **License**: Apache-2.0 (safe to wrap, no AGPL risk)
- **Moat**: We add SDLC 4.8 policies (100+ policy packs = competitive advantage)

**Alternatives Considered**:

1. **Kyverno** (Apache-2.0, CNCF incubating)
   - **Why Not**: Kubernetes-only (we need general-purpose policy engine)
   - **Verdict**: Too narrow (OPA more flexible)

2. **HashiCorp Sentinel** (Proprietary, Business Source License)
   - **Why Not**: Terraform/Vault-only (vendor lock-in)
   - **Verdict**: Too expensive ($5K-$10K/year licensing)

3. **Custom Policy Engine** (Build from scratch)
   - **Why Not**: 6 months development (vs 2 weeks OPA integration)
   - **Verdict**: Too slow (miss market window)

**Decision**: OPA (Apache-2.0) = best balance (speed, quality, license safety)

---

### Component 2: Evidence Storage (MinIO vs Alternatives)

#### MinIO - SELECTED ✅ (with AGPL containment)

**License**: AGPL v3 (strong copyleft, contamination risk)
**Version**: Latest stable (RELEASE.2024-01-01T00-00-00Z)
**Maintainer**: MinIO Inc (commercial company, dual-license)
**Adoption**: 500K+ deployments (VMware, Red Hat, Adobe)

**Strengths**:
- **S3-Compatible**: Drop-in replacement for AWS S3 (standard API)
- **Performance**: 183 GB/s throughput (benchmark: NVMe SSD)
- **Self-Hosted**: No AWS S3 egress fees ($0.09/GB adds up)
- **Encryption**: AES-256, at-rest + in-transit (SOC 2 compliant)

**Weaknesses**:
- **AGPL v3**: Strong copyleft (if we link, must release our code)
- **Complexity**: Distributed setup complex (4-node minimum for HA)

**Why Selected**:
- **Cost**: Free (vs AWS S3 $23/TB/month + egress $0.09/GB)
- **Control**: Self-hosted (vs AWS S3 = vendor lock-in)
- **AGPL Containment**: Thin API wrapper (separate process, no linking)

**AGPL Containment Strategy**:
```python
# minio_service.py (thin wrapper, Apache-2.0)
import requests  # HTTP calls only, NO direct linking

def upload_evidence(file_path):
    # Call MinIO S3 API via HTTP (no Python SDK linking)
    response = requests.put(
        "http://minio:9000/evidence-vault/file.pdf",
        data=open(file_path, 'rb')
    )
    return response.status_code == 200
```

**Legal Interpretation** (to be confirmed Week 2):
- **HTTP API Calls**: NOT linking (AGPL doesn't trigger)
- **Separate Process**: MinIO in docker-compose (isolated)
- **No Distribution**: MinIO not included in our binaries (users install separately)

**Alternatives Considered**:

1. **AWS S3** (Proprietary, pay-per-use)
   - **Why Not**: Expensive ($23/TB/month + $0.09/GB egress)
   - **Verdict**: Too costly (100 teams × 10GB each = $2.3K/month)

2. **SeaweedFS** (Apache-2.0, OSS)
   - **Why Not**: Less mature (3 years vs MinIO 8 years)
   - **Verdict**: Risky (production stability unknown)

3. **Custom Object Storage** (Build from scratch)
   - **Why Not**: 4-6 months development (vs 1 week MinIO integration)
   - **Verdict**: Too slow

**Decision**: MinIO (AGPL v3) with containment = best balance (cost, speed, legal risk managed)

---

### Component 3: Metrics Visualization (Grafana vs Alternatives)

#### Grafana - SELECTED ✅ (with AGPL containment)

**License**: AGPL v3 (strong copyleft, contamination risk)
**Version**: 10.2.0 (latest stable, Nov 2024)
**Maintainer**: Grafana Labs (commercial company, dual-license)
**Adoption**: 1M+ deployments (Bloomberg, eBay, PayPal)

**Strengths**:
- **Best-in-Class**: Industry standard for metrics visualization
- **Integrations**: 100+ data sources (Prometheus, PostgreSQL, Elasticsearch)
- **Dashboards**: 10K+ pre-built dashboards (Grafana.com)
- **Alerting**: Built-in alerting (Slack, PagerDuty, email)

**Weaknesses**:
- **AGPL v3**: Strong copyleft (if we link, must release our code)
- **Resource Heavy**: 500MB RAM per instance (vs custom dashboard 50MB)

**Why Selected**:
- **Quality**: Best metrics visualization (vs building custom = 3 months)
- **Speed**: Pre-built dashboards (vs building from scratch)
- **AGPL Containment**: Iframe embedding (no linking)

**AGPL Containment Strategy**:
```javascript
// Dashboard.tsx (React component, Apache-2.0)
export function MetricsDashboard() {
  return (
    <iframe
      src="http://grafana:3000/d/sdlc-orchestrator-overview"
      width="100%"
      height="600px"
    />
  );
}
```

**Legal Interpretation** (to be confirmed Week 2):
- **Iframe Embedding**: NOT linking (AGPL doesn't trigger)
- **Separate Process**: Grafana in docker-compose (isolated)
- **No Distribution**: Grafana not included in our binaries

**Alternatives Considered**:

1. **Metabase** (AGPL v3, similar license issue)
   - **Why Not**: Same AGPL risk (no advantage over Grafana)
   - **Verdict**: Grafana more mature

2. **Apache Superset** (Apache-2.0, OSS)
   - **Why Not**: Python-based (adds dependency complexity)
   - **Verdict**: Less mature (Grafana 10 years vs Superset 6 years)

3. **Custom Dashboard** (React + Chart.js)
   - **Why Not**: 3 months development (vs 1 week Grafana integration)
   - **Verdict**: Too slow (miss market window)

**Decision**: Grafana (AGPL v3) with containment = best balance (quality, speed, legal risk managed)

---

### Component 4: Primary Database (PostgreSQL vs Alternatives)

#### PostgreSQL - SELECTED ✅

**License**: PostgreSQL License (permissive, similar to MIT/BSD)
**Version**: 15.5 (latest stable, Nov 2024)
**Maintainer**: PostgreSQL Global Development Group (community, 25+ years)
**Adoption**: Millions of deployments (Apple, Spotify, Instagram)

**Strengths**:
- **Mature**: 25+ years production-ready (launched 1996)
- **Performance**: 100K+ rows/sec (benchmark: SSD storage)
- **ACID**: Full transactional support (vs NoSQL eventual consistency)
- **Extensions**: 100+ extensions (PostGIS, pg_trgm, TimescaleDB)
- **License**: PostgreSQL License (safe, no copyleft)

**Weaknesses**:
- **Scaling**: Vertical scaling (vs MongoDB horizontal sharding)
- **Schema Migrations**: Manual (vs DynamoDB schemaless)

**Why Selected**:
- **Reliability**: Battle-tested (25 years production)
- **ACID**: Transactions required (gate status, evidence metadata)
- **License**: PostgreSQL License (safe, no AGPL risk)
- **Cost**: Free (vs AWS RDS $100-$500/month)

**Alternatives Considered**:

1. **MySQL** (GPL v2, copyleft)
   - **Why Not**: GPL contamination risk (less permissive than PostgreSQL License)
   - **Verdict**: PostgreSQL safer

2. **MongoDB** (SSPL, server-side copyleft)
   - **Why Not**: SSPL = AGPL-like (if we offer as service, must release code)
   - **Verdict**: Too risky (we're building SaaS)

3. **AWS RDS** (Proprietary, managed PostgreSQL)
   - **Why Not**: Expensive ($100-$500/month vs $0 self-hosted)
   - **Verdict**: Too costly (Year 1 budget-conscious)

**Decision**: PostgreSQL (PostgreSQL License) = best balance (maturity, license safety, cost)

---

### Component 5: Caching + Sessions (Redis vs Alternatives)

#### Redis - SELECTED ✅

**License**: BSD-3-Clause (permissive, no copyleft)
**Version**: 7.2 (latest stable, Nov 2024)
**Maintainer**: Redis Ltd (commercial company, dual-license)
**Adoption**: 10M+ deployments (Twitter, GitHub, Stack Overflow)

**Strengths**:
- **Performance**: 1M+ ops/sec (in-memory, sub-ms latency)
- **Data Structures**: 10+ types (strings, hashes, lists, sets, sorted sets)
- **Pub/Sub**: Built-in messaging (real-time updates)
- **License**: BSD-3 (safe, no copyleft)

**Weaknesses**:
- **Memory-Only**: No persistence (vs disk-backed)
- **Single-Threaded**: Vertical scaling (vs multi-core)

**Why Selected**:
- **Speed**: In-memory (vs PostgreSQL disk = 100x faster)
- **Sessions**: Built-in TTL (user sessions expire automatically)
- **License**: BSD-3 (safe, no AGPL risk)
- **Cost**: Free (vs AWS ElastiCache $50-$200/month)

**Alternatives Considered**:

1. **Memcached** (BSD-3, similar license)
   - **Why Not**: Fewer data structures (strings only vs Redis 10+ types)
   - **Verdict**: Redis more flexible

2. **AWS ElastiCache** (Proprietary, managed Redis)
   - **Why Not**: Expensive ($50-$200/month vs $0 self-hosted)
   - **Verdict**: Too costly

3. **In-Memory PostgreSQL** (Custom tables)
   - **Why Not**: Slower than Redis (disk-backed, not in-memory)
   - **Verdict**: Redis optimized for caching

**Decision**: Redis (BSD-3) = best balance (performance, license safety, cost)

---

## License Analysis (Risk Assessment)

### License Categories (By Risk Level)

#### 🟢 SAFE: Permissive Licenses (No Copyleft)

| License | Components | Risk | Implications |
|---------|------------|------|--------------|
| **Apache-2.0** | OPA | ✅ NONE | Can use, modify, wrap freely |
| **PostgreSQL** | PostgreSQL | ✅ NONE | Can use, modify, embed freely |
| **BSD-3** | Redis | ✅ NONE | Can use, modify, embed freely |

**Total Components**: 3/5 (60%) are permissive ✅

---

#### 🔴 HIGH RISK: Strong Copyleft (AGPL)

| License | Components | Risk | Containment Strategy |
|---------|------------|------|---------------------|
| **AGPL v3** | MinIO, Grafana | 🔴 HIGH | Thin API wrapper, separate process, iframe embedding |

**Total Components**: 2/5 (40%) are AGPL 🔴

**AGPL Trigger Conditions**:
1. **Linking**: If we link AGPL library → must release our code ✅ AVOIDED (HTTP API, iframe)
2. **Modification**: If we modify AGPL code → must release modifications ✅ AVOIDED (no modifications)
3. **Distribution**: If we distribute AGPL binary → must release code ✅ AVOIDED (users install separately)
4. **Network Use**: If users interact via network → must release code ⚠️ GRAY AREA (legal review Week 2)

**Network Use Interpretation** (AGPL Section 13):
> "If you modify the Program and run it on a server, you must offer source code to users interacting with it remotely through a computer network."

**Our Interpretation** (to be confirmed by legal):
- **MinIO**: Users interact with SDLC Orchestrator (our app), NOT MinIO directly → AGPL doesn't trigger
- **Grafana**: Users see iframe (Grafana UI), but interact with our app → GRAY AREA (legal review needed)

---

### Legal Review Questions (Week 2)

#### Question 1: MinIO AGPL Containment
**Question**: Can we use MinIO S3 API (HTTP calls, no Python SDK) without triggering AGPL?

**Our Interpretation**: YES
- MinIO runs in separate docker-compose service (isolated process)
- Our code calls MinIO via HTTP API (no linking)
- Users install MinIO separately (not distributed with our app)

**Precedent**: AWS Lambda + S3 (AWS doesn't release Lambda code, but calls S3 API)

**Expected Legal Answer**: ✅ YES (HTTP API calls don't trigger AGPL)

---

#### Question 2: Grafana Iframe Embedding
**Question**: Can we embed Grafana dashboards in iframe without triggering AGPL?

**Our Interpretation**: MAYBE
- Grafana runs in separate docker-compose service (isolated process)
- Our code embeds Grafana via iframe (no linking)
- Users interact with Grafana UI (via our iframe) ⚠️ GRAY AREA

**Precedent**: WordPress + GPL plugins (WordPress embeds GPL plugins, doesn't trigger GPL for themes)

**Expected Legal Answer**: 🟡 MAYBE (depends on "derivative work" interpretation)

**Contingency Plan** (if legal says NO):
1. **Plan A**: Screenshot-based dashboards (Grafana generates PNG, we display image) ✅ SAFE
2. **Plan B**: Custom React dashboard (3 months development) ⚠️ SLOW
3. **Plan C**: Grafana Cloud (managed, $49/month) 💰 COSTLY

---

#### Question 3: Commercial SaaS + AGPL Components
**Question**: Can we offer SaaS (paid product) that uses AGPL components (MinIO, Grafana)?

**Our Interpretation**: YES (with containment)
- AGPL prohibits "conveying modified code without source" (we don't modify)
- AGPL prohibits "network use of modified code without source" (we don't modify)
- We use AGPL components AS-IS (no modifications)

**Precedent**: GitLab (AGPL) + GitLab CI (proprietary) = commercial SaaS ✅

**Expected Legal Answer**: ✅ YES (as long as no modifications, containment strategy works)

---

### License Compliance Requirements

#### Requirement 1: Attribution (All OSS)
**Obligation**: Display license notices in product (UI, docs, binary)

**Implementation**:
- `/licenses` page in dashboard (list all OSS components + licenses)
- `LICENSE` file in repo (Apache-2.0 for our code + OSS attributions)
- `NOTICE` file in repo (required by Apache-2.0)

**Effort**: 2 hours (one-time)

---

#### Requirement 2: Source Code Disclosure (AGPL Components)
**Obligation**: Offer source code to users (MinIO, Grafana)

**Implementation**:
- **MinIO**: Link to official MinIO GitHub (we don't modify)
- **Grafana**: Link to official Grafana GitHub (we don't modify)
- **Our Code**: NOT required (AGPL doesn't trigger due to containment)

**Effort**: 1 hour (add links to `/licenses` page)

---

#### Requirement 3: Trademarks (OPA, MinIO, Grafana)
**Obligation**: Cannot use trademarks without permission

**Implementation**:
- **OPA**: "Powered by OPA" (OK, nominative use)
- **MinIO**: "Storage by MinIO" (OK, nominative use)
- **Grafana**: "Dashboards by Grafana" (OK, nominative use)

**Effort**: 0 hours (no permission needed for nominative use)

---

## OSS vs Proprietary: Cost-Benefit Analysis

### Option A: Pure OSS (AGPL-Safe Only)

**Components**:
- ✅ OPA (Apache-2.0) - Policy engine
- ❌ MinIO (AGPL) → Replace with SeaweedFS (Apache-2.0)
- ❌ Grafana (AGPL) → Replace with Apache Superset (Apache-2.0)
- ✅ PostgreSQL (PostgreSQL) - Database
- ✅ Redis (BSD-3) - Caching

**Pros**:
- Zero AGPL risk (100% permissive licenses)
- Simpler legal review (no AGPL containment strategy)

**Cons**:
- **SeaweedFS**: Less mature (3 years vs MinIO 8 years), unknown production stability
- **Apache Superset**: Python-based (adds dependency), less mature dashboards
- **Development Time**: +2 weeks (integrate SeaweedFS + Superset vs MinIO + Grafana)
- **Quality Risk**: SeaweedFS untested at scale (vs MinIO battle-tested)

**Verdict**: ❌ Too risky (SeaweedFS production stability unknown)

---

### Option B: Pure Proprietary (Build Everything)

**Components**:
- ❌ OPA → Build custom policy engine (6 months)
- ❌ MinIO → Build custom object storage (4 months)
- ❌ Grafana → Build custom dashboard (3 months)
- ✅ PostgreSQL (keep, too fundamental)
- ✅ Redis (keep, too fundamental)

**Pros**:
- Zero OSS risk (100% control, no license issues)
- Zero dependencies (no external components)
- Competitive moat (fully proprietary stack)

**Cons**:
- **Time**: +13 months (6+4+3 = 13 months vs 3 months with OSS)
- **Cost**: +$450K (5 FTE × 13 months × $7K/month)
- **Quality Risk**: Our policy engine < OPA (Netflix uses OPA for 4+ years)
- **Market Risk**: 13 months = miss market window (Jira/Linear may launch Q3 2025)

**Verdict**: ❌ Too slow (miss market window)

---

### Option C: Hybrid (OSS Infra + Proprietary Logic) - SELECTED ✅

**Components**:
- ✅ OPA (Apache-2.0) - Policy engine (wrapped)
- ✅ MinIO (AGPL, contained) - Object storage
- ✅ Grafana (AGPL, contained) - Dashboards
- ✅ PostgreSQL (PostgreSQL) - Database
- ✅ Redis (BSD-3) - Caching
- ✅ **PROPRIETARY**: Gate Engine Wrapper, Evidence Vault API, AI Context Engine, Policy Packs (100+)

**Pros**:
- **Speed**: 3 months to MVP (vs 13 months proprietary)
- **Cost**: $0 OSS (vs $450K proprietary)
- **Quality**: Battle-tested OSS (vs unproven custom)
- **Moat**: SDLC 4.8 policy packs = defensible IP (1-2 years to replicate)

**Cons**:
- **Legal Risk**: AGPL containment must work (legal review Week 2)
- **Dependency Risk**: If MinIO/Grafana abandoned, must replace (low probability)

**Verdict**: ✅ Best balance (speed, cost, moat, legal risk managed)

---

## OSS Contribution Strategy (Post-MVP)

### Contribution Goals (Year 1-2)

**Goal 1**: Become OPA community contributor
- **Why**: Influence roadmap (e.g., SDLC-specific built-ins)
- **How**: Contribute SDLC policy examples to OPA docs
- **Timeline**: Year 1 Q3 (after MVP launch)

**Goal 2**: MinIO performance benchmarks
- **Why**: Validate Evidence Vault scalability (1K+ teams)
- **How**: Publish benchmark report (MinIO blog, HN)
- **Timeline**: Year 2 Q1 (after 500 teams)

**Goal 3**: Grafana SDLC dashboard templates
- **Why**: Help community (give back), marketing (thought leadership)
- **How**: Publish Grafana dashboard templates (grafana.com)
- **Timeline**: Year 1 Q4 (after 100 teams)

---

### Upstreaming Strategy (When to Contribute)

**Contribute Upstream** (to OSS projects):
- ✅ Bug fixes (critical bugs that affect us)
- ✅ Documentation improvements (clarify confusing docs)
- ✅ Examples (SDLC policy examples for OPA)

**Do NOT Contribute Upstream** (keep proprietary):
- ❌ SDLC 4.8 policy packs (competitive moat)
- ❌ Gate Engine wrapper logic (business logic)
- ❌ AI Context Engine prompts (competitive advantage)

**Principle**: Contribute to OSS infrastructure (OPA, MinIO), keep business logic proprietary (SDLC 4.8).

---

## OSS Monitoring (Dependency Risk Management)

### Risk 1: OSS Project Abandoned (Low Probability)

**Mitigation**:
- **OPA**: CNCF graduated (governance stable, unlikely abandoned)
- **MinIO**: 500K+ deployments (MinIO Inc funded, profitable)
- **Grafana**: 1M+ deployments (Grafana Labs $3B valuation, IPO-ready)

**Monitoring**:
- GitHub activity (commits/month, issue response time)
- Community health (Slack activity, conference presence)

**Contingency**:
- **OPA**: Fork + maintain (if abandoned, unlikely)
- **MinIO**: Migrate to AWS S3 (2-week effort)
- **Grafana**: Migrate to custom dashboard (3-month effort)

---

### Risk 2: License Change (Medium Probability)

**Historical Precedent**:
- **Redis** (2024): Changed from BSD-3 to SSPL (v7.4+)
- **MongoDB** (2018): Changed from AGPL to SSPL
- **Elasticsearch** (2021): Changed from Apache-2.0 to SSPL

**Mitigation**:
- **Pin Versions**: OPA v0.58.0, Grafana 10.2.0 (last permissive/AGPL versions)
- **Monitor Announcements**: Subscribe to OSS mailing lists (license change warnings)

**Contingency**:
- **If License Change**: Freeze version (don't upgrade), evaluate alternatives
- **If Must Upgrade**: Legal review (new license terms)

---

### Risk 3: Security Vulnerability (High Probability)

**Historical Precedent**:
- **Log4j** (2021): CVE-2021-44228 (RCE, critical)
- **OpenSSL** (2014): Heartbleed (info disclosure)

**Mitigation**:
- **Dependabot**: Auto-detect vulnerabilities (GitHub Security Alerts)
- **CVE Monitoring**: Subscribe to CVE feeds (NVD, Snyk)
- **Patch SLA**: Critical CVE = 24-hour patch (P0 incident)

**Contingency**:
- **If Critical CVE**: Emergency patch deploy (rollout to production within 24 hours)
- **If No Patch Available**: Temporary workaround (firewall rule, network isolation)

---

## Appendix: OSS Component Details

### OPA (Open Policy Agent)

**GitHub**: https://github.com/open-policy-agent/opa
**Stars**: 9.2K (Jan 2025)
**Contributors**: 500+
**Commits**: 10K+ (active development)
**Latest Release**: v0.58.0 (Dec 2024)

**Performance Benchmarks**:
- **Policy Evaluations**: 10K-50K ops/sec (single-core)
- **Memory**: 50MB (typical), 200MB (large policy sets)
- **Latency**: <1ms (simple policy), <10ms (complex policy)

**Production Users**:
- Netflix (4+ years, 1K+ policies)
- Cloudflare (3+ years, RBAC for 1M+ workers)
- Pinterest (2+ years, K8s admission control)

---

### MinIO

**GitHub**: https://github.com/minio/minio
**Stars**: 45K (Jan 2025)
**Contributors**: 300+
**Commits**: 20K+ (active development)
**Latest Release**: RELEASE.2024-01-01T00-00-00Z

**Performance Benchmarks**:
- **Throughput**: 183 GB/s (NVMe SSD, 32-node cluster)
- **Latency**: <10ms (PUT), <5ms (GET)
- **Scalability**: 1PB+ deployments (public reports)

**Production Users**:
- VMware (internal object storage)
- Red Hat (OpenShift container storage)
- Adobe (media asset storage)

---

### Grafana

**GitHub**: https://github.com/grafana/grafana
**Stars**: 62K (Jan 2025)
**Contributors**: 2K+
**Commits**: 80K+ (very active)
**Latest Release**: v10.2.0 (Nov 2024)

**Performance Benchmarks**:
- **Dashboards**: 100+ panels (typical), 500+ panels (max)
- **Users**: 10K+ concurrent users (documented)
- **Memory**: 500MB (typical), 2GB (large deployments)

**Production Users**:
- Bloomberg (financial metrics)
- eBay (e-commerce metrics)
- PayPal (transaction metrics)

---

### PostgreSQL

**Website**: https://www.postgresql.org/
**Version**: 15.5 (Nov 2024)
**Maintainer**: PostgreSQL Global Development Group (25+ years)

**Performance Benchmarks**:
- **Throughput**: 100K+ rows/sec (INSERT), 500K+ rows/sec (SELECT)
- **Connections**: 1K+ concurrent (with PgBouncer)
- **Database Size**: 10TB+ (production deployments)

**Production Users**:
- Apple (iCloud backend)
- Spotify (music metadata)
- Instagram (user data)

---

### Redis

**Website**: https://redis.io/
**Version**: 7.2 (Nov 2024)
**Maintainer**: Redis Ltd

**Performance Benchmarks**:
- **Throughput**: 1M+ ops/sec (single-threaded)
- **Latency**: <1ms (GET/SET)
- **Memory**: 1GB-100GB (typical)

**Production Users**:
- Twitter (timeline caching)
- GitHub (session storage)
- Stack Overflow (page caching)

---

## Document Control

**Version History**:
- v1.0.0 (January 13, 2025): Initial OSS landscape (Stage 00 WHY focus)

**Review Schedule**:
- **Week 2**: Legal review (AGPL containment strategy)
- **Monthly**: OSS dependency updates (security patches)
- **Quarterly**: OSS license monitoring (detect changes)

**Change Management**:
- **OSS License Change**: Legal review required (Go/No-Go decision)
- **Security CVE Critical**: Emergency patch (24-hour SLA)
- **OSS Project Abandoned**: Evaluate alternatives (4-week timeline)

**Related Documents**:
- [Product Vision](../01-Vision/Product-Vision.md) - Option C (Hybrid) rationale
- [Competitive Landscape](./Competitive-Landscape.md) - OSS competitors (OPA, Backstage)
- [Financial Model](../02-Business-Case/Financial-Model.md) - OSS cost savings ($120K/year)

---

**End of OSS Landscape Research v1.0.0**

*This document answers WHY we're using OSS components and WHY Option C (Stage 00). Integration architecture will be in Stage 02 (HOW).*
