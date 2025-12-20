# CTO APPROVAL: Q1-Q2 2026 Roadmap & 3 Epics
## AI-Native SDLC Governance & Safety Platform

**Document ID**: STRAT-2025-012  
**Date**: December 20, 2025  
**Status**: ✅ **APPROVED**  
**Approver**: CTO - Mr. Tai (taidt@mtsolution.com.vn)  
**Effective Date**: January 1, 2026

---

## 1. Executive Summary

Tôi, với vai trò CTO, **PHÊ DUYỆT** Product Roadmap 2026 - Software 3.0 Direction và 3 Epics chiến lược cho Q1-Q2 2026.

### 1.1 Positioning Pivot - APPROVED ✅

**Từ:** "Project Governance Tool"  
**Sang:** "AI-Native SDLC Governance & Safety Platform"

**Tagline:** *"The control plane that keeps Cursor/Copilot compliant with your architecture & standards."*

**Rationale:**
- AI dev tools (Cursor, Copilot, Claude Code) đang tạo ra governance gaps
- SDLC Orchestrator có DNA governance sâu (OPA, Evidence Vault, Gates)
- Market timing đúng với AI Safety narrative
- Differentiation rõ ràng so với competitors

### 1.2 Strategic Direction - APPROVED ✅

**3 Strategic Themes 2026:**
1. **AI-Intent-First Adoption** - Orchestrator là entry point cho ideas & projects
2. **AI Safety & Governance** - Mọi AI code phải qua validation trước merge
3. **Ecosystem & Enterprise** - Marketplace + SSO/SAML + Self-hosted

---

## 2. Epic Approvals

### 2.1 EP-01: Idea & Stalled Project Flow with AI Governance Hints

**Status**: ✅ **APPROVED**  
**Priority**: P0 - Critical  
**Timeline**: Week 3-8 (Q1 2026)  
**Owner**: Product Team + Frontend Team

**Scope Approved:**
- ✅ "Ý tưởng mới" flow với AI classify + risk assessment + auto-suggest Policy Pack
- ✅ "Dự án dở dang" flow với repo scan + gap analysis + AI recommendations
- ✅ Aha Moment dashboards (Stalled Projects ranking, Backlog skeleton)

**Success Criteria Approved:**
- ≥80% ideas có Policy Pack auto-suggested
- API response <10s cho stalled project analysis
- ≥70% EM/PM nội bộ sử dụng weekly sau 4 tuần

**Technical Decisions:**
- Sử dụng AI Council Service hiện có (Ollama/OpenAI)
- Extend Evidence Vault schema cho idea/project metadata
- Frontend wizard flow tích hợp vào Dashboard

**Budget Allocation**: $15,000 (6 weeks development)

---

### 2.2 EP-02: AI Safety Layer v1

**Status**: ✅ **APPROVED**  
**Priority**: P0 - Critical  
**Timeline**: Week 3-10 (Q1-Q2 2026)  
**Owner**: Backend Team + DevOps Team + Security Team

**Scope Approved:**
- ✅ Output Validators (Static analysis, Tests, Architecture checks, Coverage)
- ✅ Policy Guards (OPA-based, auto-comment PR, VCR override)
- ✅ Evidence Trail (AI tool/model logging, PR timeline view)

**Success Criteria Approved:**
- 100% AI-tagged PRs qua validators
- 0 AI PR merge khi policy fail (trừ VCR override)
- Evidence timeline viewable trong UI

**Technical Decisions:**
- Sử dụng OPA engine hiện có, extend policy schemas
- New collection `ai_code_events` trong Evidence Vault (không extend schema cũ)
- GitHub integration trước (Week 3-6), GitLab defer sang Q3
- Performance target: <6 minutes p95 validation pipeline

**3 Killer Capabilities for Marketing:**
1. "AI không được merge code nếu vi phạm kiến trúc"
2. "Mọi AI code có Evidence trail đầy đủ"
3. "AI gợi ý - Orchestrator quyết định"

**Budget Allocation**: $25,000 (8 weeks development)

---

### 2.3 EP-03: Design Partner Program (10 External Teams)

**Status**: ✅ **APPROVED**  
**Priority**: P0 - Critical  
**Timeline**: Week 1-8 (Q1 2026)  
**Owner**: Product Team + Customer Success

**Scope Approved:**
- ✅ Sourcing 20 candidates, onboard ≥6 teams
- ✅ Workshop "AI Safety for Engineering Teams" (90 minutes)
- ✅ Bi-weekly feedback loops
- ✅ Case study generation

**Target Partner Criteria:**
- CTO/Eng Manager đang dùng nặng Cursor/Copilot/Claude
- Codebase ≥100K LOC
- Pain rõ về AI-generated architecture chaos

**Success Criteria Approved:**
- ≥6 teams onboarded trong 60 ngày
- ≥10 actionable feedback items
- ≥2 case studies với metrics

**Partner Offer:**
- 6-9 tháng free hoặc giá tượng trưng
- Dedicated Slack/Discord support
- Grandfathered pricing khi GA

**Budget Allocation**: $8,000 (workshop, onboarding, materials)

---

## 3. Two-Track Launch Strategy - APPROVED ✅

**Track A - Internal Dogfooding:**
- NQH, MTS, Bflow teams (5-8 teams, 50-100 engineers)
- Target: 70%+ DAU
- Zero P0 bugs for 90 days

**Track B - Design Partners:**
- 10 external teams (target ≥6 active)
- Parallel với internal, không sequential
- Feedback loop vào EP-01/EP-02 backlog

**Rationale:** Tránh 6-9 tháng internal lock-in, market timing critical cho AI Safety narrative.

---

## 4. Pricing Tiers - APPROVED ✅

| Tier | Price | Projects | Policies | AI Safety | Support |
|------|-------|----------|----------|-----------|---------|
| **Free** | $0 | 1 | 5 rules | 2 devs max | Community |
| **Team** | $149/mo | 5 | 50+ rules | Full v1 | Email |
| **Enterprise** | $500+/team/mo | Unlimited | Custom | Full + Self-hosted | Dedicated CSM |

**Pricing Rationale:**
- Free tier cho adoption & PLG motion
- Team tier competitive với market ($99-199 range)
- Enterprise justified bởi "AI Safety" value prop

---

## 5. 90-Day Timeline - APPROVED ✅

| Week | EP-01 | EP-02 | EP-03 |
|------|-------|-------|-------|
| 1-2 | Design specs | Safety Layer spec | Partner list 20 |
| 3-4 | "Ý tưởng mới" MVP | Output Validators | Workshop + outreach |
| 5-6 | "Dự án dở dang" MVP | Policy Guards | ≥3 teams onboarded |
| 7-8 | Aha dashboards | Evidence Trail | ≥6 teams onboarded |
| 9-10 | Iterate | Full integration | Feedback synthesis |
| 11-12 | Polish | Documentation | 2 case studies |

---

## 6. Dependencies & Blockers

### 6.1 Critical Dependencies
- [ ] **Analytics Setup** (Week 1-2): Mixpanel/Amplitude cho tracking Aha Moments
- [ ] **AI Council Service** readiness cho EP-01 flows
- [ ] **OPA Policy Engine** enhancements cho EP-02
- [ ] **Evidence Vault** indexing improvements

### 6.2 Cross-Team Coordination
- **Security Team**: Secret redaction, prompt hygiene review (EP-02)
- **Data Team**: Telemetry pipeline, KPIs definition
- **Marketing Team**: GTM messaging alignment cho "AI Safety First"

---

## 7. Risk Assessment

| Risk | Impact | Mitigation | Owner |
|------|--------|------------|-------|
| Rebrand confusion | Medium | Staged comms, validate với partners | Marketing |
| Telemetry gaps | High | Block EP-01 until instrumented | Data Team |
| AI Safety false positives | High | Progressive rollout, simulation mode | Backend |
| Design Partner churn | Medium | High-touch support, rapid iteration | Product |
| GitLab delay | Low | Scope to GitHub-first for Q1-Q2 | DevOps |

---

## 8. Budget Summary

| Category | Allocation | Notes |
|----------|------------|-------|
| EP-01 Development | $15,000 | 6 weeks, 2 devs |
| EP-02 Development | $25,000 | 8 weeks, 3 devs |
| EP-03 Program | $8,000 | Workshops, materials, support |
| Analytics/Infra | $5,000 | Mixpanel, monitoring |
| Contingency | $7,000 | 15% buffer |
| **TOTAL** | **$60,000** | Q1-Q2 2026 |

---

## 9. Approval Signatures

### CTO Approval

**Name**: Mr. Tai  
**Title**: Chief Technology Officer  
**Email**: taidt@mtsolution.com.vn  
**Phone**: +84 939 116 006  

**Decision**: ✅ **APPROVED**  
**Date**: December 20, 2025  

**Comments**:
> Roadmap này đánh dấu bước chuyển quan trọng từ "project governance tool" sang "AI Safety Platform". 
> Ba Epics được thiết kế với scope rõ ràng, ACs measurable, và timeline realistic.
> Two-track launch strategy giải quyết đúng risk internal lock-in.
> Pricing tiers aligned với market và value proposition mới.
> 
> Recommend tiến hành Sprint 34 theo plan này ngay từ Week 1 của Q1 2026.

---

### Pending Approvals

| Role | Name | Status | Date |
|------|------|--------|------|
| CTO | Mr. Tai | ✅ APPROVED | Dec 20, 2025 |
| CPO | TBD | ⏳ Pending | - |
| CEO | TBD | ⏳ Pending | - |

---

## 10. Next Steps

1. ✅ CTO Approval - **DONE** (Dec 20, 2025)
2. ⏳ CPO Review & Approval
3. ⏳ CEO Final Sign-off
4. ⏳ Kick-off Meeting (target: Jan 2, 2026)
5. ⏳ Sprint 34 Planning (Week 1)

---

## References

- [Product-Roadmap-2026-Software3.0.md](../../00-foundation/04-Roadmap/Product-Roadmap-2026-Software3.0.md)
- [Product-Vision.md](../../00-foundation/01-Vision/Product-Vision.md)
- [AI-Safety-Layer-v1.md](../../specs/AI-Safety-Layer-v1.md) (TBD)
- [Design-Partner-Program.md](../../specs/Design-Partner-Program.md) (TBD)

---

**Document Control**

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | Dec 20, 2025 | CTO | Initial approval |

---

*This document is part of SDLC Orchestrator governance records. Changes require CTO + CPO dual approval.*
