# SDLC Orchestrator Governance System v1.0
## Policy Documents & Contracts

**Date Created:** January 27, 2026
**Last Updated:** January 28, 2026
**Status:** ✅ **ALL SIGNATURES APPROVED** (CEO + CTO + CPO)
**Phase:** PRE-PHASE 0 COMPLETE → READY FOR PHASE 0

---

## 📋 DOCUMENTS IN THIS DIRECTORY

### 1. CEO-WORKFLOW-CONTRACT.md ✅ **CEO + CTO APPROVED**

**Purpose:** Operating agreement between CEO and Governance System

**Key Commitments:**
- **CEO will NOT do:** Review Green PRs (<30 index), check ownership, verify ADR linkage
- **CEO will do:** Review Red/Orange PRs, weekly calibration, exception approvals
- **System guarantees:** >95% accuracy, >99% uptime, <500ms latency, <10% false positive

**Success Target:** CEO governance time 40h → 10h per sprint (-75%)

**Signatures Required:**
- [x] CEO (Tai) ✅ **APPROVED** (Jan 28, 2026)
- [x] CTO (Nhat Quang) ✅ **APPROVED** (Jan 28, 2026)

---

### 2. AUTO-GENERATION-FAIL-SAFE-POLICY.md ✅ **CTO APPROVED**

**Purpose:** Ensure developers never blocked by auto-generation failure

**Core Principle:** "AUTO-GENERATION MAY FAIL, BUT GOVERNANCE MUST NEVER HARD-BLOCK"

**Fallback Chain:**
```
LLM Generation → (fail) → Template → (fail) → Minimal Placeholder → Developer Edits
```

**Guarantee:** Developer can proceed within 2 minutes, regardless of auto-gen state

**Monitoring:**
- LLM Success Rate: >90% healthy, <70% critical
- Template Fallback Rate: <10% healthy, >30% critical
- Developer Complaints: <1/day healthy, >3/day critical

**Signatures Required:**
- [x] CTO (Nhat Quang) ✅ **APPROVED** (Jan 28, 2026)

---

### 3. VIBECODING-INDEX-EXPLAINABILITY-SPEC.md ✅ **CPO APPROVED**

**Purpose:** Ensure every score > 30 is explainable to CEO

**Core Principle:** "EVERY SCORE > 30 MUST BE EXPLAINABLE"

**Explainability Requirements:**
1. Composite Score (0-100)
2. Top 3 Contributing Signals (name, score, contribution %, evidence)
3. Suggested Focus Area (where to look first)
4. Comparison to Baseline (normal for this PR type?)

**5 Signals (Weighted):**
- Architectural Smell (0.25): God class, feature envy, shotgun surgery
- Abstraction Complexity (0.15): Inheritance depth, interface count
- AI Dependency Ratio (0.20): AI lines / total, human modification %
- Change Surface Area (0.20): Files, modules, API contracts
- Drift Velocity (0.20): Pattern changes over 7 days

**MAX CRITICALITY OVERRIDE:**
- Critical paths (auth, payment, DB schema, infra, secrets) auto-boost to index 80 (Red)

**Signatures Required:**
- [x] CPO ✅ **APPROVED** (Jan 28, 2026)

---

## ⚙️ CONFIGURATION FILES (COMPLETED)

### 4. critical_paths.yaml ✅ **READY**

**Purpose:** Critical path patterns for MAX CRITICALITY OVERRIDE

**Categories:**
- **Security**: auth, security, crypto, secrets management
- **Payment**: payment, billing, transactions, subscriptions
- **Database Schema**: migrations, schema.prisma, ORM models
- **Infrastructure**: Docker, K8s, CI/CD, deployment configs
- **API Contracts**: OpenAPI specs, public endpoints

**Override Behavior:** Files matching patterns auto-boost index to 80 (Red)

### 5. governance_signals.yaml ✅ **READY**

**Purpose:** Vibecoding Index calculation configuration

**5 Signals with Initial Weights:**
1. Architectural Smell (0.25): God class, feature envy, shotgun surgery
2. Abstraction Complexity (0.15): Inheritance depth, interface count
3. AI Dependency Ratio (0.20): AI lines / total, human modification %
4. Change Surface Area (0.20): Files, modules, API contracts
5. Drift Velocity (0.20): Pattern changes over 7 days

**Thresholds:**
- Green: 0-30 (auto-approve)
- Yellow: 31-60 (tech lead review)
- Orange: 61-80 (CEO should review)
- Red: 81-100 (CEO must review)

**Status:** ⏳ Awaiting CEO Calibration Session to finalize weights

### 6. feedback_templates.yaml ✅ **READY**

**Purpose:** Actionable error messages with CLI commands

**5 Templates:**
1. **missing_ownership**: File missing @owner annotation
2. **missing_intent**: PR missing intent statement
3. **stage_violation**: Working ahead of design stage
4. **missing_ai_attestation**: AI code without human attestation
5. **quality_contract_violation**: Test coverage, security scan failures

**Format:** What Failed → Why Matters → Step-by-Step Fix → CLI Command

### 7. break_glass.yaml ✅ **READY**

**Purpose:** Emergency bypass for P0/P1 production incidents

**3-Step Process:**
1. Attempt normal governance (5 min timeout)
2. Request CEO approval (15 min timeout)
3. Break Glass (emergency bypass) - Tech Lead authority

**Safety Mechanisms:**
- Auto-revert in 24h if post-incident review not completed
- Immutable audit trail (7-year retention)
- Notifications to CEO/CTO/Tech Leads
- Post-mortem required within 24 hours

### 8. governance_flags.py ✅ **READY**

**Purpose:** Feature flags for governance enforcement levels

**Governance Modes:**
- **OFF**: Governance disabled (development only)
- **WARNING**: Log violations, don't block (observation mode)
- **SOFT**: Block critical violations, warn on others
- **FULL**: Block all violations (production mode)

**Kill Switch Criteria:**
- Rejection rate >80%
- Latency P95 >500ms
- False positive rate >20%
- Developer complaints >5/day

**Phase Control:** Tracks PRE-PHASE 0 → WEEK 6+ with feature availability per phase

---

## 🚦 PRE-PHASE 0 GO/NO-GO CHECKLIST

### Documents (NON-NEGOTIABLE)
- [x] CEO-WORKFLOW-CONTRACT.md signed by CEO ✅ **(Jan 28, 2026)**
- [x] CEO-WORKFLOW-CONTRACT.md signed by CTO ✅ **(Jan 28, 2026)**
- [x] AUTO-GENERATION-FAIL-SAFE-POLICY.md signed by CTO ✅ **(Jan 28, 2026)**
- [x] VIBECODING-INDEX-EXPLAINABILITY-SPEC.md signed by CPO ✅ **(Jan 28, 2026)**

### CEO Calibration Session (2 hours)
- [ ] Scheduled with CEO + Tech Lead
- [ ] Review 10 recent rejected PRs
- [ ] Document "CEO's smell" for each
- [ ] Configure `governance_signals.yaml` initial weights
- [ ] **Output:** `../phase-0/CEO-Smell-Calibration.md`

### Infrastructure Readiness
- [ ] Ollama qwen3:32b deployed and tested
- [ ] LLM fallback templates ready
- [ ] Redis cache configured
- [ ] MinIO Evidence Vault operational
- [ ] Feature flags system ready
- [ ] Kill switch tested

### Configuration Files
- [x] `backend/app/config/critical_paths.yaml` populated ✅
- [x] `backend/app/config/governance_signals.yaml` initial weights ✅
- [x] `backend/app/config/feedback_templates.yaml` (5 templates) ✅
- [x] `backend/app/config/break_glass.yaml` configured ✅
- [x] `backend/app/config/governance_flags.py` feature flags ✅

---

## 📅 NEXT STEPS

### Immediate (Today)
1. **Print and circulate documents** for signature
2. **Schedule CEO Calibration Session** (2 hours)
3. **Verify infrastructure** (Ollama, Redis, MinIO)

### After Signatures (48 hours - PHASE 0)
4. **Conduct CEO Calibration Session** → Output: `CEO-Smell-Calibration.md`
5. **Create 6 technical documents:**
   - CEO-Workflow-Analysis.md
   - Auto-Generation-Requirements.md
   - Governance-Signals-Design.md
   - Success-Criteria-v2.yaml
   - DATABASE-SCHEMA-DESIGN.md
   - MONITORING-PLAN.md

### CTO Gate Review (Hour 48)
6. **CTO reviews all 6 deliverables**
7. **Decision:** Full execution authority for Week 1 OR iterate

---

## 📊 SUCCESS METRICS

**PRIMARY (CEO Time Saved):**
- Week 2: -25% (30h)
- Week 4: -50% (20h)
- Week 8: -75% (10h)

**SECONDARY (Developer Friction):**
- Target: <5 min per PR

**TERTIARY (Vibecoding Index):**
- Week 4: Average <40
- Week 8: Average <30

---

## 🔗 RELATED DOCUMENTS

- **Plan:** `/home/dttai/.claude/plans/parallel-painting-turing.md`
- **Framework:** `SDLC-Enterprise-Framework/02-Core-Methodology/`
- **Configuration:** `backend/app/config/`

---

**Status:** ✅ **ALL SIGNATURES COMPLETE - READY FOR PHASE 0**
**Next Gate:** CEO Calibration Session → PHASE 0 EXECUTION
**Go-Live Target:** Week 6 (if Week 5 metrics pass)

---

## 🎉 ALL SIGNATURES COMPLETE (January 28, 2026)

**Approvals Received:**
- ✅ CEO committed to NOT reviewing Green PRs (Index < 30)
- ✅ CTO committed to maintaining SLAs and kill switch readiness
- ✅ CPO committed to ensuring every score > 30 has full explainability
- Target: 40h → 10h per sprint (-75% reduction)

**Remaining to unlock PHASE 0:**
1. ⏳ CEO Calibration Session (2 hours with Tech Lead)

---

## 📦 DELIVERABLES SUMMARY

| Deliverable | Status | Location |
|------------|--------|----------|
| CEO-WORKFLOW-CONTRACT.md | ✅ Created | `docs/governance-v1/` |
| AUTO-GENERATION-FAIL-SAFE-POLICY.md | ✅ Created | `docs/governance-v1/` |
| VIBECODING-INDEX-EXPLAINABILITY-SPEC.md | ✅ Created | `docs/governance-v1/` |
| critical_paths.yaml | ✅ Created | `backend/app/config/` |
| governance_signals.yaml | ✅ Created | `backend/app/config/` |
| feedback_templates.yaml | ✅ Created | `backend/app/config/` |
| break_glass.yaml | ✅ Created | `backend/app/config/` |
| governance_flags.py | ✅ Created | `backend/app/config/` |

**All PRE-PHASE 0 documentation and configuration is COMPLETE.**
**Signatures Received:** CEO ✅, CTO ✅, CPO ✅
**Awaiting:** CEO Calibration Session (2 hours) → Then PHASE 0 EXECUTION
