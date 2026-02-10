# Sprint 171 Kickoff Plan: Market Expansion Foundation

**Sprint**: 171  
**Phase**: Phase 6 - Market Expansion (Sprint 171-175)  
**Duration**: February 10-14, 2026 (5 days)  
**Budget**: $15K (5 days × $3K/day)  
**Framework Target**: 96.6% → 96.9% (+0.3%)  
**Previous Sprint**: [Sprint 170 COMPLETE (92/100)](SPRINT-170-COMPLETION-REPORT.md)

---

## Executive Summary

Sprint 171 launches **Phase 6: Market Expansion**, pivoting from technical excellence (Phase 5: 93.0 avg, 16.5x ROI) to **revenue generation**. This sprint establishes the foundation for Vietnam SME market entry with internationalization infrastructure and first customer pilots.

### Strategic Context

**Phase 5 Completion** (Sprint 167-170):
- ✅ 15,393 LOC delivered (93.0 avg score)
- ✅ 205 tests added (all passing)
- ✅ Framework 94.8% → 96.6% (+1.8%)
- ✅ Developer Experience complete: CLI + IDE + Dual SDKs + Docs

**Phase 6 Mission** (Sprint 171-175):
- **Revenue Target**: $126K ARR (30 SME teams @ $99/month + 3 Enterprise @ $500/month)
- **Customer Target**: 10 Vietnam SME pilots + 3 Enterprise LOIs
- **Framework Target**: 96.6% → 98.0% (+1.4%)
- **Timeline**: 5 sprints, ~7 weeks

### Sprint 171 Objectives

| Priority | Objective | Business Impact |
|----------|-----------|-----------------|
| **P0** | i18n Infrastructure (Vietnamese + English) | Enable Vietnam market entry |
| **P0** | Vietnamese UI Translations (300+ strings) | Establish local trust |
| **P1** | VND Pricing Integration (Stripe multi-currency) | Enable local payment |
| **P1** | Pilot Program Landing Page | First customer outreach |
| **P2** | Customer Discovery (5 interviews) | Validate product-market fit |

---

## Sprint 171 Roadmap (5 Days)

### Day 1: i18n Infrastructure Foundation

**Goal**: Establish internationalization architecture for frontend + backend

**Deliverables**:

| File | LOC | Purpose |
|------|-----|---------|
| `frontend/src/lib/i18n/config.ts` | ~80 | next-i18next configuration |
| `frontend/src/lib/i18n/locales/en.json` | ~150 | English base translations |
| `frontend/src/lib/i18n/locales/vi.json` | ~150 | Vietnamese translations |
| `backend/app/core/i18n.py` | ~120 | Backend i18n utilities |
| `backend/app/locales/en.json` | ~100 | Backend English strings |
| `backend/app/locales/vi.json` | ~100 | Backend Vietnamese strings |

**Technical Approach**:
- Frontend: next-i18next library (proven, Next.js standard)
- Backend: Python gettext or custom JSON-based i18n
- Language detection: Accept-Language header + user preference
- Fallback: en (English) always available

**Exit Criteria**:
- [ ] Language switcher in Sidebar component
- [ ] `useTranslation()` hook working in 3+ pages
- [ ] Backend API returns localized error messages
- [ ] Tests: 10 i18n tests (5 frontend + 5 backend)

**Target**: ~700 LOC

---

### Day 2: Vietnamese UI Translation (Core Modules)

**Goal**: Translate 300+ UI strings for dashboard, projects, gates, evidence

**Deliverables**:

| Module | Strings | Priority |
|--------|---------|----------|
| **Dashboard** | ~80 | P0 (first impression) |
| **Projects** | ~60 | P0 (core workflow) |
| **Gates** | ~50 | P0 (core workflow) |
| **Evidence** | ~40 | P0 (core workflow) |
| **Teams** | ~30 | P1 |
| **Settings** | ~40 | P2 |

**Translation Strategy**:
- Professional translation service (Fiverr/Upwork, ~$50-100)
- Native Vietnamese speaker review
- Context-aware translations (technical terms preserved)
- Glossary: SDLC terms (Gate → Cổng kiểm soát, Evidence → Bằng chứng)

**Exit Criteria**:
- [ ] 300+ strings translated in `vi.json`
- [ ] Dashboard fully functional in Vietnamese
- [ ] Projects CRUD operations in Vietnamese
- [ ] Screenshot testing: 5 pages in Vietnamese
- [ ] Native speaker review: 0 critical issues

**Target**: ~300 LOC (translation JSON entries)

---

### Day 3: VND Pricing Integration (Stripe Multi-Currency)

**Goal**: Enable Vietnamese Dong (VND) payment with Stripe

**Deliverables**:

| File | LOC | Purpose |
|------|-----|---------|
| `backend/app/services/billing/currency_service.py` | ~180 | Multi-currency pricing logic |
| `backend/app/schemas/pricing.py` | ~60 | Currency-aware pricing models |
| `backend/app/api/routes/pricing.py` | ~120 | Pricing API endpoints |
| `frontend/src/components/pricing/PricingCard.tsx` | ~80 | Currency-aware pricing display |
| `frontend/src/hooks/usePricing.ts` | ~40 | Currency detection + conversion |

**Pricing Structure**:
- **Team Tier**: $99/month → 2,475,000 VND/month (25,000 VND/USD rate)
- **Enterprise Tier**: $500/month → 12,500,000 VND/month
- **Currency Detection**: IP geolocation → Vietnam = VND default
- **Stripe Integration**: Multi-currency checkout session

**Technical Approach**:
- Stripe Checkout: `currency: 'vnd'` parameter
- Real-time exchange rates: Stripe automatic conversion
- Price display: Format with Vietnamese number format (2.475.000 ₫)
- Invoice: VND or USD based on customer preference

**Exit Criteria**:
- [ ] Stripe Checkout session created with VND
- [ ] Pricing page displays VND for Vietnam IP
- [ ] Currency switcher: USD ↔ VND toggle
- [ ] Test transaction: 1 VND → 1 VND (no USD conversion)
- [ ] Tests: 15 pricing tests (currency logic)

**Target**: ~480 LOC

---

### Day 4: Pilot Program Landing Page

**Goal**: Create public landing page for Vietnam SME pilot program

**Deliverables**:

| File | LOC | Purpose |
|------|-----|---------|
| `frontend/src/app/pilot/page.tsx` | ~300 | Pilot program landing page |
| `frontend/src/components/pilot/PilotSignupForm.tsx` | ~180 | Signup form with validation |
| `frontend/src/components/pilot/PilotBenefits.tsx` | ~120 | Benefits section |
| `frontend/src/components/pilot/PilotFAQ.tsx` | ~100 | FAQ accordion |
| `backend/app/api/routes/pilot.py` | ~150 | Pilot signup API |
| `backend/app/models/pilot_application.py` | ~80 | Database model |
| `backend/alembic/versions/s171_001_pilot_applications.py` | ~70 | Migration |

**Content Strategy** (Vietnamese + English):
- Hero: "Tham gia Chương trình Pilot MIỄN PHÍ"
- Value proposition: 3 months free + dedicated support
- Benefits: 5 key benefits (cost savings, time efficiency, AI governance)
- Social proof: 3 testimonials (from Phase 5 dogfooding)
- CTA: "Đăng ký ngay" (Register now)
- FAQ: 10 common questions

**Technical Features**:
- Form fields: Company name, contact, team size, current SDLC tool
- Validation: Email, phone (Vietnamese format)
- Auto-response email: Confirmation + next steps
- CRM integration: Google Sheets or Airtable for tracking

**Exit Criteria**:
- [ ] Landing page accessible at `/pilot`
- [ ] Form submission → Database + Email notification
- [ ] Responsive design: Mobile + Desktop
- [ ] A/B test ready: 2 headline variants
- [ ] Tests: 10 E2E tests (form submission flow)

**Target**: ~1,000 LOC

---

### Day 5: Customer Discovery + Sprint Close

**Goal**: Validate product-market fit with 5 Vietnam SME interviews

**Activities**:

| Task | Effort | Deliverable |
|------|--------|-------------|
| **Customer Interviews** | 4 hours | 5 interviews (30 min each) |
| **Interview Synthesis** | 2 hours | Key findings doc (~300 LOC) |
| **Sprint 171 Completion Report** | 1 hour | Completion report (~150 LOC) |
| **AGENTS.md Update** | 30 min | Sprint 171 entry (~20 LOC) |
| **Regression Testing** | 1 hour | All tests pass |
| **Tag Creation** | 15 min | `sprint-171-v1.0.0` |

**Interview Questions** (5 core questions):
1. Current SDLC process pain points?
2. AI code generation usage (GitHub Copilot, Cursor, etc.)?
3. Governance concerns with AI-generated code?
4. Willingness to pay for SDLC automation?
5. Preferred onboarding method (self-service vs. white-glove)?

**Target Insights**:
- Price sensitivity: $99/month acceptable?
- Feature priority: Which Sprint 172-175 features matter most?
- Localization needs: Vietnamese UI critical or nice-to-have?
- Integration requirements: Existing tools (Jira, GitHub, Slack)?

**Exit Criteria**:
- [ ] 5 interviews completed + recorded (with consent)
- [ ] Customer discovery doc published
- [ ] Sprint 171 completion report finalized
- [ ] AGENTS.md updated with Sprint 171 summary
- [ ] All regression tests pass (frontend + backend)
- [ ] Tag `sprint-171-v1.0.0` created

**Target**: ~470 LOC (documents)

---

## Sprint 171 File Summary

| Category | Files | LOC |
|----------|-------|-----|
| **i18n Infrastructure** | 6 | ~700 |
| **Vietnamese Translations** | 2 | ~300 |
| **VND Pricing** | 5 | ~480 |
| **Pilot Landing Page** | 7 | ~1,000 |
| **Customer Discovery** | 3 | ~470 |
| **Total** | **23** | **~2,950** |

**Variance Expectation**: 150-180% (Sprint 167-170 pattern) → ~5,000 LOC actual

---

## Technical Architecture

### i18n Architecture Decision

**Frontend**: next-i18next (industry standard for Next.js)
- Pros: SSR support, automatic language detection, namespace organization
- Cons: Bundle size (+50KB)
- Alternatives considered: react-i18next (CSR only), custom JSON (no SSR)

**Backend**: Custom JSON-based i18n
- Rationale: Lightweight, no gettext complexity, API error messages only
- File structure: `backend/app/locales/{lang}.json`
- Fallback chain: User preference → Accept-Language → en

### Stripe Multi-Currency Integration

```python
# Currency-aware checkout session
stripe.checkout.Session.create(
    line_items=[{
        'price_data': {
            'currency': 'vnd',  # Vietnam Dong
            'product_data': {'name': 'SDLC Orchestrator Team'},
            'unit_amount': 247500000,  # 2,475,000 VND in cents
        },
        'quantity': 1,
    }],
    mode='subscription',
    success_url='https://sdlc.dev/success',
    cancel_url='https://sdlc.dev/cancel',
)
```

**Exchange Rate Handling**:
- Stripe automatic conversion: VND ↔ USD at checkout time
- Display rate: Fixed 25,000 VND/USD (updated quarterly)
- Invoice: Customer's selected currency (VND or USD)

### Pilot Application Database Schema

```sql
CREATE TABLE pilot_applications (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    company_name VARCHAR(255) NOT NULL,
    contact_email VARCHAR(255) NOT NULL UNIQUE,
    contact_phone VARCHAR(20),
    team_size VARCHAR(50),  -- "1-5", "6-20", "21-50", "50+"
    current_tool VARCHAR(255),  -- "GitHub Actions", "GitLab CI", "Manual", "None"
    pain_points TEXT,
    language VARCHAR(10) DEFAULT 'vi',  -- 'vi' or 'en'
    status VARCHAR(50) DEFAULT 'pending',  -- 'pending', 'approved', 'rejected', 'in_progress'
    applied_at TIMESTAMP DEFAULT NOW(),
    reviewed_at TIMESTAMP,
    reviewer_id UUID REFERENCES users(id),
    notes TEXT
);
```

---

## Exit Criteria (8 Criteria)

| # | Criterion | Target | Verification |
|---|-----------|--------|--------------|
| 1 | i18n Infrastructure Working | Language switcher functional | Manual test: Switch en → vi |
| 2 | Vietnamese UI Translation | 300+ strings translated | Count `vi.json` keys |
| 3 | VND Pricing Integration | Stripe checkout with VND | Test transaction (1 VND) |
| 4 | Pilot Landing Page | `/pilot` accessible | E2E test: Form submission |
| 5 | Customer Discovery | 5 interviews completed | Interview recordings exist |
| 6 | Regression Tests Pass | 0 new failures | `npm test && pytest` |
| 7 | Documentation Complete | Sprint report + AGENTS.md | Files exist with content |
| 8 | Tag Created | `sprint-171-v1.0.0` | `git tag -l` shows tag |

---

## Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| **Translation Quality** | Medium | High | Native speaker review + professional service |
| **Stripe VND Support** | Low | High | Pre-validate Stripe API with VND test mode |
| **Customer Interview No-Shows** | Medium | Medium | Over-recruit 10 interviews for 5 completions |
| **i18n Bundle Size** | Low | Medium | Code splitting + lazy loading |
| **Currency Conversion Accuracy** | Low | High | Use Stripe automatic rates (no manual calc) |

---

## Success Metrics

### Sprint 171 KPIs

| Metric | Target | Measurement |
|--------|--------|-------------|
| **i18n Coverage** | 80%+ of UI | Count translated strings / total strings |
| **Pilot Signups** | 10+ applications | Database count (week 1) |
| **Customer Interview Insights** | 15+ unique insights | Manual synthesis |
| **Page Load Performance** | <2s (with i18n bundle) | Lighthouse score |
| **Test Coverage** | 95%+ maintained | Backend + Frontend coverage |

### Phase 6 Leading Indicators (Sprint 171 Baseline)

| Indicator | Sprint 171 Target | Sprint 175 Target |
|-----------|-------------------|-------------------|
| **Pilot Applications** | 10 | 30 |
| **Customer Interviews** | 5 | 20 |
| **LOIs Signed** | 0 | 3 Enterprise |
| **Paying Customers** | 0 | 10 SME |
| **ARR** | $0 | $126K |

---

## Team Allocation

| Role | Allocation | Responsibilities |
|------|------------|------------------|
| **Backend Engineer** | 60% | i18n backend, VND pricing API, pilot API |
| **Frontend Engineer** | 60% | i18n frontend, Vietnamese UI, pilot landing page |
| **Designer** | 20% | Pilot landing page design, Vietnamese UI review |
| **Product Manager** | 40% | Customer interviews, pilot program design |
| **CTO** | 20% | Architecture review, customer interview synthesis |

**Total**: 2.0 FTE (200% allocation, 40% over standard 1.6 FTE)

---

## Dependencies

### External Dependencies
- [ ] Professional Vietnamese translation service (Fiverr/Upwork) - $50-100
- [ ] Stripe VND test account verification - 1 day lead time
- [ ] Customer interview recruits (5 Vietnam SME contacts) - 2 days lead time

### Internal Dependencies
- [x] Phase 5 complete (Sprint 170) ✅
- [x] Framework 96.6% baseline ✅
- [x] Production deployment stable ✅

### Blocking Issues
- None identified (all Phase 5 blockers resolved)

---

## Phase 6 Context (Sprint 171-175 Preview)

### Phase 6 Roadmap

| Sprint | Theme | Key Deliverables | Framework Δ |
|--------|-------|------------------|-------------|
| **171** (Current) | Market Foundation | i18n + VND + Pilot Landing | +0.3% → 96.9% |
| **172** | Enterprise Onboarding | Migration tools + Training materials | +0.3% → 97.2% |
| **173** | Performance @ Scale | 1000+ projects support + Query optimization | +0.3% → 97.5% |
| **174** | Security Hardening | Penetration testing + OWASP Top 10 | +0.3% → 97.8% |
| **175** | Mobile + Final Polish | Mobile responsive + 98% framework | +0.2% → 98.0% |

### Phase 6 Success Criteria

**Revenue**:
- 10 SME teams @ $99/month = $11,880 ARR (by Sprint 173)
- 3 Enterprise LOIs @ $500/month = $18,000 ARR (by Sprint 175)
- **Total**: $29,880 ARR (23% of $126K annual target)

**Customer**:
- 30 pilot applications (by Sprint 175)
- 20 customer interviews (by Sprint 175)
- 10 paying SME customers (by Sprint 175)
- 3 Enterprise LOIs signed (by Sprint 175)

**Product**:
- Framework 96.6% → 98.0% (+1.4%)
- Mobile responsive (all core workflows)
- Penetration test: 0 critical vulnerabilities

---

## Approval Checklist

### Pre-Sprint Approval (CTO)

- [ ] Sprint 171 plan reviewed
- [ ] Budget approved ($15K)
- [ ] Team allocation confirmed (2.0 FTE)
- [ ] Exit criteria validated
- [ ] Risk mitigation accepted

### Sprint Kickoff (Team)

- [ ] Day 1-5 plan communicated
- [ ] Vietnamese translation service booked
- [ ] Customer interview recruits confirmed (10 contacts)
- [ ] Stripe VND test mode validated
- [ ] Development environment ready

### Sprint Close (CTO Review)

- [ ] All 8 exit criteria met
- [ ] Sprint 171 completion report published
- [ ] AGENTS.md updated
- [ ] Tag `sprint-171-v1.0.0` created
- [ ] CTO score assigned (target: 90+)

---

## Next Steps (Immediate Actions)

### Monday, Feb 10 (Sprint Start)

**Morning** (9:00-12:00):
1. Team standup: Sprint 171 kickoff + role assignment
2. Vietnamese translation service: Post job on Fiverr/Upwork
3. Customer interview recruits: Email 10 Vietnam SME contacts

**Afternoon** (13:00-17:00):
4. Backend: Start i18n infrastructure (`i18n.py`)
5. Frontend: Install `next-i18next` + config
6. DevOps: Verify Stripe VND test mode

**Evening** (Review):
7. CTO sync: Day 1 progress check
8. Blockers identified: None expected

### Week Plan

- **Tue**: Vietnamese translations + VND pricing (bulk of work)
- **Wed**: Pilot landing page (high visibility)
- **Thu**: Customer interviews (5 interviews, 30 min each)
- **Fri**: Sprint close + tag creation

---

## Appendix A: Vietnamese UI Glossary

| English | Vietnamese | Context |
|---------|-----------|---------|
| Dashboard | Bảng điều khiển | Main UI |
| Project | Dự án | Core entity |
| Gate | Cổng kiểm soát | Quality gate |
| Evidence | Bằng chứng | Artifact |
| Team | Nhóm | Organization unit |
| Settings | Cài đặt | Configuration |
| User | Người dùng | Account |
| Admin | Quản trị viên | Admin role |
| Report | Báo cáo | Analytics |
| Notification | Thông báo | Alert |

---

## Appendix B: Customer Interview Script

**Introduction** (2 min):
- Giới thiệu: SDLC Orchestrator - Automation platform for AI-native development
- Mục đích: Hiểu nhu cầu và pain points của SME Vietnam

**Questions** (25 min):
1. **Current SDLC Process** (5 min):
   - Tools: GitHub Actions, GitLab CI, Jenkins, Manual?
   - Pain points: Slow, manual, error-prone?
   - Team size: 5-10, 10-20, 20-50?

2. **AI Code Generation** (5 min):
   - Tools: GitHub Copilot, Cursor, Claude Code?
   - Concerns: Security, quality, governance?
   - Adoption: 0%, 25%, 50%, 75%+?

3. **Governance Needs** (5 min):
   - Code review process: Manual, automated, hybrid?
   - Quality gates: Linting, testing, security scans?
   - Approval workflows: Single reviewer, multiple, CEO?

4. **Pricing & Value** (5 min):
   - Willingness to pay: $99/month acceptable?
   - Value perception: Time savings, quality improvements?
   - Budget: CapEx or OpEx?

5. **Onboarding Preference** (5 min):
   - Self-service: Documentation + tutorials?
   - White-glove: Dedicated support + training?
   - Pilot duration: 1 month, 3 months, 6 months?

**Closing** (3 min):
- Next steps: Pilot program invitation
- Follow-up: Demo session (if interested)
- Thank you: Small gift (Starbucks voucher)

---

**Sprint 171 Approved for Execution**: Awaiting CTO sign-off

**Prepared by**: Dev Team  
**Date**: February 8, 2026  
**Version**: 1.0
