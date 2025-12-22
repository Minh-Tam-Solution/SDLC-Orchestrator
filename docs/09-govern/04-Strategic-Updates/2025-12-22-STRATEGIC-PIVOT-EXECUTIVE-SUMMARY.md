# Strategic Pivot: DeepCode → IR-Based Vietnamese SME Codegen
## Executive Decision Summary for CEO/BOD

**Document ID**: STRAT-2025-013-EXEC
**Date**: December 22, 2025
**Status**: ✅ **CTO APPROVED**
**Approver**: Mr. Tai - CTO
**Effective Date**: January 6, 2026 (Sprint 45)

---

## TL;DR (1 Minute Read)

**Decision**: Dừng việc biến Orchestrator thành AI coder. Khóa lại vị trí Orchestrator là SDLC control plane + multi-provider codegen (trọng tâm: IR-based Vietnamese SME).

**Action**: Cancel DeepCode POC, redirect resources to EP-06 IR-Based Codegen (Vietnamese SME market).

**Timeline**: Sprint 45 (Jan 6-17) Multi-Provider Architecture, Sprint 46-48 (Jan 20 - Feb 28) Vietnamese Codegen

**Budget**: $18,000 reallocated from DeepCode ($16,200) to EP-06 ($18,000), net +$1,800 investment for blue ocean market

**Expected Outcome**: 10 Vietnamese SME founders onboarded, <30min TTFV, 8/10 satisfaction, blue ocean positioning vs Cursor/Lovable/v0.dev

---

## 1. Strategic Realization - External Expert Review

### 1.1 What We Discovered

External expert identified **critical strategic drift**:

```
Original Vision:
  "SDLC Orchestrator = Control plane for ALL AI coders"

What We Almost Built:
  "SDLC Orchestrator = DeepCode + some gates"
  (Another AI coder in crowded market)
```

**Verdict**: ✅ CORRECT - We were drifting from unique value proposition

### 1.2 Core Strategic Errors

| Error | Impact | Evidence |
|-------|--------|----------|
| **Strategic Drift** | Becoming "AI coder" not "control plane" | DeepCode as core strategy, not optional plugin |
| **Domain Mismatch** | PaperBench (ML) ≠ Business Apps (CRUD) | ROI 17x based on wrong dataset |
| **Resource Misallocation** | 8-10 weeks on commodity feature | Vietnamese SME market untapped (blue ocean) |

### 1.3 Correct Positioning

**NEW Strategy (APPROVED):**
> "SDLC Orchestrator là control plane ORCHESTRATE bất kỳ AI coder nào (Claude, Cursor, DeepCode, Ollama, OSS...) với governance-first approach."

**DeepCode Role**: One optional plugin (Q2, IF needed), NOT core platform

---

## 2. Decision: Cancel DeepCode POC & Pivot to EP-06

### 2.1 What We're Canceling

- ❌ **DeepCode POC** (Dec 30 - Jan 3): Cancelled
- ❌ **DeepCode Integration** (Sprint 45-46, 8-10 weeks): Deferred to Q2 2026
- ❌ **Default codegen for Stage 03**: Replaced by multi-provider model

**Note**: DeepCode không bị loại bỏ vĩnh viễn – chỉ bị hạ cấp thành **optional plugin** sau khi EP-06 chứng minh được traction.

### 2.2 What We're Prioritizing

**Sprint 45 (Jan 6-17): Multi-Provider Architecture**
- Goal: Plugin model for ANY codegen provider
- Deliverables: CodegenProvider interface, OllamaCodegenProvider, Provider registry
- Budget: $3,000
- Team: 1 Backend + 0.5 Architect

**Sprint 46-48 (Jan 20 - Feb 28): EP-06 IR-Based Vietnamese Codegen**
- Goal: AppBlueprint → Working MVP for Vietnamese SME founders
- Deliverables: Vietnamese templates (F&B, hospitality), Ollama optimization, <30min TTFV onboarding
- Budget: $15,000
- Team: 2 Backend + 1 Frontend + 0.5 DevOps

### 2.3 Budget Reallocation

```yaml
Saved from DeepCode Deferral:
  Budget: $16,200 → $5,000 (Q2, IF needed)
  Time: 8-10 weeks → 0 weeks (Q1)

Reallocated to EP-06:
  Sprint 45 Multi-Provider: $3,000
  Sprint 46-48 Vietnamese Codegen: $15,000
  Total: $18,000

Net Investment: +$1,800 for blue ocean market
ROI: Unknown but high potential (200K+ Vietnamese SME market, zero competitor)
```

---

## 3. New Strategic Direction: Control Plane + Vietnamese SME

### 3.1 Positioning Statement

**SDLC Orchestrator is**:
```
NOT: An AI Coder (like Cursor, Claude Code, DeepCode, Lovable, v0.dev)
YES: The Operating System for Software 3.0
```

**Core Value**:
1. SDLC 5.0 Framework (10 stages, governance-first)
2. Multi-Provider Orchestration (Claude, Cursor, DeepCode, Ollama, OSS)
3. AI Safety Layer (detect + control AI-generated code)
4. IR-based Architecture (AppBlueprint → Code)
5. Evidence Vault (compliance, audit, quality gates)

**Unique Differentiation**:
- ✅ Vietnamese language + SME/non-tech focus
- ✅ F&B/hospitality domain expertise (menu, order, table, reservation, room, booking)
- ✅ <30min TTFV onboarding (non-technical founders, no English, no coding)
- ✅ Provider-agnostic (works with ANY AI coder, not locked to one)
- ✅ Governance-first (compliance, audit, quality gates built-in)

### 3.2 Target Market (REVISED)

**Primary (Q1-Q2 2026)**: Vietnamese SME founders
- F&B: 50K+ restaurants, cafes, food delivery
- Hospitality: 30K+ hotels, resorts, homestays
- Retail: 120K+ shops, convenience stores
- **Total addressable**: 200K+ Vietnamese SME (BFlow scale)

**Competitive Advantage**:
- vs Cursor/Claude/Copilot: We ORCHESTRATE them (not compete) + Vietnamese optimization
- vs Lovable/v0.dev: Vietnamese language, F&B domain templates, <30min TTFV (vs 2-3 hours)
- vs DeepCode: Business apps (vs ML papers), CRUD expertise (vs algorithm focus)

**Blue Ocean**: No competitor optimizes for Vietnamese SME + governance-first approach

---

## 4. Roadmap Snapshot Q1-Q2 2026

| Sprint | Focus | Deliverables | Budget | Success Criteria |
|--------|-------|--------------|--------|------------------|
| **Sprint 44** (Dec 23-27) | SDLC Structure Scanner | CrossReferenceValidator (Day 5-10) | - | No change, focus 100% |
| **Sprint 45** (Jan 6-17) | Multi-Provider Architecture | CodegenProvider interface, OllamaCodegenProvider, Provider registry | $3,000 | 3 providers working, quality gates apply to all |
| **Sprint 46-48** (Jan 20 - Feb 28) | EP-06 Vietnamese Codegen | Vietnamese templates, AppBlueprint → Code, <30min TTFV onboarding | $15,000 | 10 founders onboarded, <30min TTFV (90%ile), 8/10 satisfaction |
| **Q2 2026** (Apr-Jun) | DeepCode Optional Plugin (IF) | Paper2Code integration only | $5,000 | Only IF EP-06 succeeds + customer requests |

**Total Q1 Investment**: $18,000
**Expected Outcome**: Blue ocean positioning, 10+ Vietnamese SME founders, <30min TTFV

---

## 5. Success Metrics & Decision Criteria

### 5.1 EP-06 Success Criteria (Sprint 46-48)

| Metric | Target | Measurement |
|--------|--------|-------------|
| **Founders Onboarded** | ≥10 Vietnamese SME | Completed onboarding flow |
| **TTFV** | <30min (90th percentile) | Idea → working app deploy time |
| **Code Quality** | 95%+ pass quality gates | Architecture + security + coverage |
| **Satisfaction** | 8/10 founder rating | Post-onboarding survey |
| **Infrastructure Cost** | <$50/month per project | Ollama self-hosted cost tracking |

### 5.2 Multi-Provider Success (Sprint 45)

- ✅ 3 providers implemented (Ollama, Claude, DeepCode stub)
- ✅ Provider routing works correctly (select by project config)
- ✅ Quality gates apply uniformly to ALL providers

### 5.3 DeepCode Q2 Decision Criteria (ALL must be met)

| Condition | Metric | Threshold |
|-----------|--------|-----------|
| **EP-06 Success** | Founders onboarded | ≥10 |
| **User Satisfaction** | NPS / score | ≥8/10 |
| **Real Demand** | Explicit customer requests | ≥2 paying customers |
| **Budget** | Available R&D budget | ≥$5,000 |

**IF <4 conditions met → DEFAULT NO-GO** (archive DeepCode plugin proposal)

---

## 6. Risk Assessment

### 6.1 Risks Mitigated by This Pivot ✅

- ✅ **Strategic Drift**: Remain "control plane" not "another AI coder"
- ✅ **Domain Mismatch**: Vietnamese business apps (validated) not PaperBench ML
- ✅ **Vendor Lock-in**: Multi-provider architecture (vendor-agnostic)
- ✅ **Resource Waste**: Focus on unique value (Vietnamese, SME, IR) not commodity

### 6.2 New Risks & Mitigation ⚠️

| Risk | Mitigation | Owner |
|------|------------|-------|
| **Ollama Vietnamese Quality Unknown** | Sprint 46 Week 1: Baseline testing + prompt engineering | Backend Lead |
| **Design Partner Gap** | Recruit 3-5 Vietnamese SME beta testers during Sprint 45 | Product Team |
| **TTFV >30min** | Optimize onboarding flow, benchmark weekly | Frontend Lead |
| **IR Schema Maturity Gap** | Sprint 45 Week 2: Add Vietnamese validation rules | Architect |

---

## 7. Why This Decision is Correct

### 7.1 Strategic Fit

- ✅ Aligns with vision: "Control plane for Software 3.0" (not AI coder)
- ✅ Leverages unique strength: Vietnamese language, SME domain, governance-first
- ✅ Blue ocean market: 200K+ Vietnamese SME, zero competitor optimization

### 7.2 Resource Optimization

- ✅ Saves 8-10 weeks engineering time (DeepCode integration)
- ✅ Saves $11,200 budget (defer DeepCode to Q2, IF needed)
- ✅ Invests in blue ocean ($18,000 for Vietnamese SME market)

### 7.3 Future-Proof Architecture

- ✅ Multi-provider model (not locked to DeepCode)
- ✅ Can add/swap providers easily (Cursor, Claude, Gemini, Ollama, OSS)
- ✅ IR-based foundation (provider-agnostic code generation)

---

## 8. Approval

**CTO Decision**: ✅ **APPROVED**
**Name**: Mr. Tai
**Date**: December 22, 2025

**Rationale**:
> External Expert Review đúng 100%. Chúng ta suýt trở thành "another AI coder" thay vì "control plane cho mọi AI coder".
>
> DeepCode có technical merit nhưng WRONG positioning cho market của chúng ta (Vietnamese SME, business CRUD, not ML papers).
>
> EP-06 IR-Based Vietnamese Codegen là blue ocean - không competitor nào optimize cho thị trường này. Multi-provider architecture là future-proof.
>
> Sprint 45-48 execution plan realistic, success metrics measurable. APPROVE với full confidence. 🚀

**Signature**: ✅ Mr. Tai - CTO

---

## 9. Next Actions (Immediate)

**Dec 23, 2025** (This Week):
- [ ] Team All-Hands: CTO explains strategic pivot
- [ ] Cancel DeepCode POC (notify team, update roadmap)
- [ ] Redirect 1 Backend Dev to Multi-Provider Architecture

**Sprint 45** (Jan 6-17):
- [ ] Implement Multi-Provider Architecture ($3,000)
- [ ] Recruit 3-5 Vietnamese SME beta testers

**Sprint 46-48** (Jan 20 - Feb 28):
- [ ] Build EP-06 Vietnamese Codegen ($15,000)
- [ ] Pilot with 10 Vietnamese SME founders

**Q2 2026** (Apr-Jun):
- [ ] Re-evaluate DeepCode (IF 4 conditions met)

---

## 10. Reference Documents

**Full Technical Details**: [2025-12-22-STRATEGIC-PIVOT-DEEPCODE-TO-IR-CODEGEN.md](./2025-12-22-STRATEGIC-PIVOT-DEEPCODE-TO-IR-CODEGEN.md)
**External Expert Review**: 70+ pages comprehensive analysis (Dec 22, 2025)
**EP-06 Specification**: [EP-06-Codegen-Engine-Dual-Mode.md](../../01-planning/02-Epics/EP-06-Codegen-Engine-Dual-Mode.md)
**Product Vision**: [Product-Vision.md](../../00-foundation/01-Vision/Product-Vision.md)

---

**Document Status**: ✅ **ACTIVE - CTO APPROVED**
**Next Review**: End of Sprint 45 (Jan 17, 2026)
**Authority**: CTO Final Decision

---

*This is the executive summary. For full technical implementation details, execution plan, and risk analysis, see the complete strategic pivot document.*

**"Let's build what ONLY WE can build: Vietnamese SME codegen with governance-first approach."** 🚀 - CTO
