# URGENT: Team Assignment for SASE Phase 2-Pilot (Week 6 Kickoff)

**Issue ID**: TEAM-ASSIGN-SASE-2026-001
**Priority**: 🔴 **P0 - CRITICAL**
**Due Date**: **January 17, 2026 EOD** (TODAY)
**Status**: ✅ ASSIGNED (Jan 17, 2026 - Confirmed)
**Owner**: Engineering Manager
**Authority**: CTO APPROVED (Jan 17, 2026)

---

## 📋 EXECUTIVE SUMMARY

**Request**: Assign development team for SASE Phase 2-Pilot (SOP Generator pilot)
**Start Date**: Monday, January 20, 2026 @ 9:00am (Kickoff meeting)
**Duration**: 6 weeks (Jan 20 - Feb 28, 2026)
**Budget**: $23,000 (Phase 2-Pilot allocation)

**Team Required**:
- **2 Backend Developers** (Python/FastAPI expertise)
- **1 Frontend Developer** (React/TypeScript expertise)
- **1 Tech Lead** (SE4H Agent Coach role)

**CTO Directive**: "lock 2 BE + 1 FE + TL by EOD Jan 17; kickoff Jan 20"

---

## 🎯 TEAM REQUIREMENTS

### Role 1: Backend Developer #1 (Primary AI Integration)

**Responsibilities**:
- Ollama service integration (AI provider primary)
- SOP generation logic (template instantiation)
- Evidence Vault integration (MinIO S3 API)
- API endpoints (POST /api/v1/sops/generate, etc.)

**Required Skills**:
- Python 3.11+ (FastAPI, async/await)
- AI/ML integration experience (Ollama, Claude API, or similar)
- PostgreSQL + SQLAlchemy 2.0
- MinIO/S3 API (network-only access, AGPL-safe)
- RESTful API design (OpenAPI 3.0)

**Estimated Effort**: 30 hours/week x 6 weeks = 180 hours
**Budget Allocation**: ~$9,000

**Preferred Candidates** (Engineering Manager to confirm):
- [ ] Backend Dev A (has Ollama experience)
- [ ] Backend Dev B (AI service integration background)
- [ ] Backend Dev C (fallback if A/B unavailable)

---

### Role 2: Backend Developer #2 (Validation & Quality)

**Responsibilities**:
- ISO 9001 compliance validation logic
- 4-Gate Quality Pipeline integration
- MRP/VCR workflow implementation
- Database schema (sop_evidence, mrps, vcrs tables)

**Required Skills**:
- Python 3.11+ (FastAPI, async/await)
- Database design (PostgreSQL, migrations with Alembic)
- Compliance standards (ISO 9001 knowledge a plus)
- Testing (pytest, 90%+ coverage target)
- OPA integration (policy validation)

**Estimated Effort**: 30 hours/week x 6 weeks = 180 hours
**Budget Allocation**: ~$9,000

**Preferred Candidates** (Engineering Manager to confirm):
- [ ] Backend Dev D (quality/validation experience)
- [ ] Backend Dev E (OPA integration background)
- [ ] Backend Dev F (fallback if D/E unavailable)

---

### Role 3: Frontend Developer (UI Implementation)

**Responsibilities**:
- SOP creation form (React Hook Form + Zod validation)
- SOP markdown preview (syntax highlighting)
- ISO 9001 compliance score display
- MRP summary card + VCR approval UI
- Evidence Vault indicator
- SOP history view

**Required Skills**:
- React 18 (hooks, TypeScript)
- shadcn/ui component library (Tailwind + Radix)
- TanStack Query v5 (caching, optimistic updates)
- React Hook Form + Zod (form validation)
- Markdown rendering (react-markdown or similar)
- Responsive design (WCAG 2.1 AA accessibility)

**Estimated Effort**: 30 hours/week x 6 weeks = 180 hours
**Budget Allocation**: ~$9,000

**Preferred Candidates** (Engineering Manager to confirm):
- [ ] Frontend Dev A (shadcn/ui experience)
- [ ] Frontend Dev B (React form expertise)
- [ ] Frontend Dev C (fallback if A/B unavailable)

---

### Role 4: Tech Lead (SE4H Agent Coach)

**Responsibilities** (SE4H - Agent Coach role per SASE framework):
- Review BRS-PILOT-001 + LPS-PILOT-001 (already APPROVED)
- Conduct daily standups (15 min, blocker resolution)
- Respond to CRPs (Consultation Request Packs, if any)
- Approve MRPs (Merge-Readiness Packs, Iteration 4+)
- Issue VCRs (Version Controlled Resolutions)
- Quality review (final SOP validation, Iteration 6)
- Weekly checkpoint with CTO (Friday 3pm)

**Required Skills**:
- Full-stack expertise (Python + React)
- SASE framework knowledge (BRS/MRP/VCR workflow)
- Leadership (mentor 3 developers)
- SDLC 6.1.0 compliance (4-layer architecture, naming standards)
- Code review (100% coverage enforced)

**Estimated Effort**: 20 hours/week x 6 weeks = 120 hours (mix of hands-on + oversight)
**Budget Allocation**: ~$6,000

**Preferred Candidates** (Engineering Manager to confirm):
- [ ] Tech Lead A (SASE framework trained - Week 1 workshop)
- [ ] Tech Lead B (backend/frontend full-stack)
- [ ] Tech Lead C (fallback if A/B unavailable)

---

## 📅 TIMELINE & MILESTONES

### Week 6 (Jan 20-24): Iteration 1 - Template Design + Basic Generation

**Kickoff**: Monday, Jan 20 @ 9:00am (location: Meeting Room A / Zoom link TBD)

**Sprint Planning**: Monday, Jan 20 @ 10:00am (after kickoff)
- Review BRS-PILOT-001 (requirements)
- Review LPS-PILOT-001 (6 iterations)
- Break down Iteration 1 into tasks
- Assign tasks to team members

**Daily Standups**: Tuesday-Friday @ 9:30am (15 min)
- What did you do yesterday?
- What will you do today?
- Any blockers?

**Iteration 1 Milestone** (Friday, Jan 24 EOD):
- First SOP generated (Deployment type)
- Ollama integration working
- Basic UI form functional
- Demo to CTO (Friday 3pm standup)

---

### Week 7-11 (Jan 27 - Feb 28): Iterations 2-6

**Iteration 2** (Jan 27-31): ISO 9001 Compliance Validation
**Iteration 3** (Feb 3-7): Evidence Vault Integration
**Iteration 4** (Feb 10-14): MRP/VCR Workflow
**Iteration 5** (Feb 17-21): 5 SOP Types Implementation
**Iteration 6** (Feb 24-28): Quality Review + Pilot Completion

**Weekly Checkpoints**: Friday @ 3pm (CTO + PM/PO + Tech Lead + Team)
- Demo iteration deliverables
- Review success metrics (target vs actual)
- Identify blockers for next iteration
- Adjust plan if needed

---

## 🚨 BLOCKERS & RISKS

### Blocker 1: Team Assignment Delay (CRITICAL)

**Risk**: If team not assigned by EOD Jan 17, Week 6 kickoff (Jan 20) will be delayed
**Impact**: +1 week additional delay → End date: Apr 25 (instead of Apr 18)
**Mitigation**: Engineering Manager to prioritize by EOD today (Jan 17)

### Blocker 2: Team Member Unavailability

**Risk**: Preferred candidates may be committed to other projects
**Mitigation Options**:
1. **Option A**: Swap team members from Sprint 70 (if Sprint 70 can be delayed)
2. **Option B**: Use fallback candidates (3rd choice per role)
3. **Option C**: Reduce scope to 3 artifacts (BRS+MRP+VCR only, skip LPS/MTS/CRP)

**Decision Authority**: CTO + Engineering Manager (joint decision)

### Blocker 3: Skill Gap (Ollama Integration)

**Risk**: Backend Dev may not have Ollama experience
**Mitigation**:
- Tech Lead to provide 2-hour hands-on training (Monday Jan 20, 1pm)
- Ollama API documentation available (api.nhatquangholding.com/docs)
- Claude API fallback ready (if Ollama integration takes >2 days)

---

## ✅ ACCEPTANCE CRITERIA

**Team Assignment Complete** when:
- [x] 2 Backend Developers assigned (names confirmed)
- [x] 1 Frontend Developer assigned (name confirmed)
- [x] 1 Tech Lead assigned (name confirmed)
- [x] Calendar invites sent for Week 6 kickoff (Jan 20 @ 9am)
- [x] Slack channel created (#sase-pilot-sop-generator)
- [x] GitHub access granted (feature/sop-generator-pilot branch)
- [x] Development environment prepared (Docker Compose running locally)

---

## 📞 CONTACT & ESCALATION

### Primary Contact

**Owner**: Engineering Manager
**Email**: eng-manager@mtc.vn
**Slack**: @eng-manager
**Phone**: [REDACTED]

**Deadline**: **January 17, 2026 EOD** (6:00pm)

### Escalation Path

If team assignment not complete by EOD:
1. **5:00pm**: Engineering Manager to notify PM/PO + CTO (Slack #leadership)
2. **5:30pm**: CTO + Engineering Manager decision call (Option A/B/C above)
3. **6:00pm**: Decision communicated to all stakeholders

---

## 🎯 SUCCESS METRICS (PILOT)

### Primary Metrics (from BRS-PILOT-001)

| Metric | Target | Measurement |
|--------|--------|-------------|
| **SOPs Generated** | ≥5 (1 per type) | Count of successful generations |
| **Time Reduction** | ≥20% | Avg generation time (30s) vs manual (2-4h) |
| **Developer Satisfaction** | ≥4/5 | Post-pilot survey (2 BE + 1 FE) |
| **P0 Incidents** | 0 | Incident tracking |
| **Agent Cost** | <$50/month | Ollama + Claude API costs |

### Team Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| **Sprint Velocity** | ~20 SP/week | Story points completed per week |
| **Code Review Time** | <24 hours | Time from PR open → approval |
| **Daily Standup Attendance** | 100% | Attendance tracking |
| **Iteration Demo Completion** | 6/6 | Iterations with working demo |

---

## 📚 REFERENCES

### 1. CTO Approval Document
- Path: `docs/09-govern/01-CTO-Reports/SASE-Week-5-Progress-Report.md`
- CTO Directive: "lock 2 BE + 1 FE + TL by EOD Jan 17; kickoff Jan 20"

### 2. Pilot Artifacts (APPROVED)
- BRS-PILOT-001: `docs/04-build/05-SASE-Artifacts/BRS-PILOT-001-NQH-Bot-SOP-Generator.yaml`
- LPS-PILOT-001: `docs/04-build/05-SASE-Artifacts/LPS-PILOT-001-SOP-Generator.yaml`
- MRP/VCR Examples: `docs/04-build/05-SASE-Artifacts/` (MRP-PILOT-001-EXAMPLE, VCR-PILOT-001-EXAMPLE)

### 3. SASE Framework
- SE 3.0 Plan: `docs/09-govern/04-Strategic-Updates/SE3.0-SASE-Integration-Plan-APPROVED.md`
- Agent Coach Role: Tech Lead as SE4H (Human - Agent Coach)
- Agent Executor Role: Dev Team as SE4A (Agents - Executors)

---

## ⏰ ACTION ITEMS (ENGINEERING MANAGER)

**Due: January 17, 2026 EOD**

### Immediate (by 3:00pm)
- [ ] Review preferred candidates (12 names: 3 per role x 4 roles)
- [ ] Check availability (confirm none are committed to other projects)
- [ ] Select final team (2 BE + 1 FE + 1 TL)

### By 4:00pm
- [ ] Notify selected team members (1-on-1 calls or Slack DM)
- [ ] Confirm acceptance (all 4 team members agree to commit)
- [ ] Send calendar invites (Week 6 kickoff: Jan 20 @ 9am)

### By 5:00pm
- [ ] Create Slack channel (#sase-pilot-sop-generator)
- [ ] Add team members to channel
- [ ] Grant GitHub access (feature/sop-generator-pilot branch)
- [ ] Share BRS-PILOT-001 + LPS-PILOT-001 (required reading before Monday)

### By 6:00pm
- [ ] Confirm team assignment complete to CTO + PM/PO (Slack #leadership)
- [ ] Update this issue status: PENDING → ASSIGNED
- [ ] Close issue with team roster (names + roles)

---

## 📝 ISSUE RESOLUTION TEMPLATE

**When team assigned, update this section:**

### Team Roster (Assigned) ✅

**Backend Developer #1**: Assigned - AI Integration
**Backend Developer #2**: Assigned - Validation & Quality
**Frontend Developer**: Assigned - UI Implementation
**Tech Lead**: Assigned - SE4H Agent Coach

**Assignment Date**: January 17, 2026 @ 5:30pm
**Assigned By**: Engineering Manager
**Confirmed By**: CTO

**Status**: ✅ TEAM LOCKED - Ready for Week 6 Kickoff

**Next Step**: Week 6 Kickoff (Monday, Jan 20, 2026 @ 9:00am)

---

**Issue Created By**: PM/PO
**Date**: January 17, 2026 @ 4:00pm
**Priority**: 🔴 P0 - CRITICAL
**Deadline**: January 17, 2026 EOD (6:00pm)

---

*This issue is part of Track 1 SASE (Q1 2026 P0) - SDLC 6.1.0 Framework Enhancement*
*Reference: SASE-Week-5-Progress-Report.md, BRS-PILOT-001, LPS-PILOT-001*
