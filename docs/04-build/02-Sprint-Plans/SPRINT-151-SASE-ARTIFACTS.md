# Sprint 151: SASE Artifacts Enhancement
## VCR + CRP Workflow Implementation

**Sprint ID**: S151
**Phase**: Phase 2 - Feature Complete
**Dates**: March 4-8, 2026 (5 days)
**Status**: 🔄 IN PROGRESS
**Priority**: P0 - Feature Completion
**Budget**: $8,000
**Team**: 3 FTE (Backend + Frontend + Framework)
**Design Docs**: [ADR-048](../../02-design/01-ADRs/ADR-048-SASE-VCR-CRP-Architecture.md), [SPEC-0024](../../02-design/14-Technical-Specs/SPEC-0024-VCR-CRP-Technical-Specification.md)

---

## Executive Summary

**Objective**: Implement VCR and CRP workflows to achieve 60% → 75% SASE Artifacts completion.

**Success Criteria**:
- [ ] VCR (Version Controlled Resolution) workflow operational
- [ ] CRP (Consultation Request Pack) workflow operational
- [ ] SASE artifact templates available (6 templates)
- [ ] SASE Artifacts: 60% → 75% completion (+15%)
- [ ] Integration with Evidence Vault

**Business Impact**:
- **AI Governance**: Structured consultation process for AI-generated code
- **Merge Readiness**: VCR ensures all code meets quality standards
- **Framework Realization**: 85% → 87% overall (+2%)
- **Developer Experience**: Clear process for complex changes

---

## Background: SASE Methodology

From [SDLC-Enterprise-Framework/SASE](SDLC-Enterprise-Framework/):

### SASE Artifacts (6 types)

| Artifact | Purpose | When | Format |
|----------|---------|------|--------|
| **BRS** | Briefing Script | Sprint start | YAML |
| **LPS** | Loop Script | Iteration start | YAML |
| **MTS** | Mentor Script | Complex task | Markdown |
| **CRP** | Consultation Request Pack | Need expert input | Markdown |
| **MRP** | Merge-Readiness Pack | Before PR | Markdown |
| **VCR** | Version Controlled Resolution | Post-merge | Markdown |

**Current State** (Sprint 146):
- BRS, LPS, MTS: ✅ Templates exist (from Track 1 SASE, Q1 2026)
- CRP, MRP, VCR: ⏳ Templates exist, but NOT integrated into Orchestrator

**Sprint 151 Goal**: Integrate CRP + VCR workflows into Orchestrator

---

## Day-by-Day Plan

### Day 1: VCR Workflow Backend

**Objectives**:
- Create VCR data model
- Create VCR service
- Create VCR API endpoints

**Tasks**:

#### Data Model (2 hours)
- [ ] Create `backend/app/models/vcr.py`:
  ```python
  class VersionControlledResolution(Base):
      __tablename__ = "version_controlled_resolutions"
      
      id = Column(Integer, primary_key=True)
      pr_id = Column(Integer, ForeignKey("pull_requests.id"))
      project_id = Column(Integer, ForeignKey("projects.id"))
      
      # Metadata
      title = Column(String(255))
      problem_statement = Column(Text)
      root_cause_analysis = Column(Text)
      solution_approach = Column(Text)
      implementation_notes = Column(Text)
      
      # Evidence links
      evidence_ids = Column(ARRAY(Integer))
      adr_ids = Column(ARRAY(Integer))
      
      # AI involvement
      ai_generated_percentage = Column(Float)  # 0.0 - 1.0
      ai_tools_used = Column(ARRAY(String))  # ["Cursor", "Copilot"]
      
      # Status
      status = Column(Enum("draft", "submitted", "approved", "rejected"))
      created_by = Column(Integer, ForeignKey("users.id"))
      approved_by = Column(Integer, ForeignKey("users.id"), nullable=True)
      created_at = Column(DateTime, default=datetime.utcnow)
      approved_at = Column(DateTime, nullable=True)
  ```
- [ ] Create Alembic migration: `s151_001_vcr_table.py`

#### Service Layer (4 hours)
- [ ] Create `backend/app/services/vcr_service.py`:
  - `create_vcr()`: Create new VCR from PR
  - `get_vcr()`: Get VCR by ID
  - `list_vcrs()`: List all VCRs for project
  - `submit_vcr()`: Submit for approval
  - `approve_vcr()`: CTO/CEO approval
  - `reject_vcr()`: Reject with feedback
  - `auto_generate_vcr()`: AI-assisted generation from PR metadata
- [ ] Integrate with Evidence Vault (link evidence)
- [ ] Integrate with ADR service (link ADRs)
- [ ] Add telemetry tracking:
  - `vcr_created` event
  - `vcr_submitted` event
  - `vcr_approved` event

#### API Endpoints (2 hours)
- [ ] Create `backend/app/api/v1/endpoints/vcr.py`:
  - `POST /api/v1/vcr` - Create VCR
  - `GET /api/v1/vcr/{vcr_id}` - Get VCR
  - `GET /api/v1/vcr` - List VCRs (filter by project, status)
  - `PUT /api/v1/vcr/{vcr_id}` - Update VCR
  - `POST /api/v1/vcr/{vcr_id}/submit` - Submit for approval
  - `POST /api/v1/vcr/{vcr_id}/approve` - Approve (CTO/CEO only)
  - `POST /api/v1/vcr/{vcr_id}/reject` - Reject
  - `POST /api/v1/vcr/auto-generate` - AI-assisted generation

**Deliverables**:
- `backend/app/models/vcr.py` (~150 LOC)
- `backend/app/services/vcr_service.py` (~600 LOC)
- `backend/app/api/v1/endpoints/vcr.py` (~400 LOC)
- Alembic migration
- 8 API endpoints

**Exit Criteria**:
- [ ] VCR backend complete
- [ ] All endpoints functional
- [ ] Migration applied

### Day 2: CRP Workflow Backend + VCR Frontend

**Objectives**:
- Create CRP workflow backend
- Create VCR frontend UI

**Tasks**:

#### CRP Backend (3 hours)
- [ ] Create `backend/app/models/crp.py`:
  ```python
  class ConsultationRequestPack(Base):
      __tablename__ = "consultation_request_packs"
      
      id = Column(Integer, primary_key=True)
      project_id = Column(Integer, ForeignKey("projects.id"))
      
      # Consultation details
      title = Column(String(255))
      context = Column(Text)
      question = Column(Text)
      options_considered = Column(Text)  # JSON array
      recommended_option = Column(String(255))
      
      # Requester + Consultant
      requested_by = Column(Integer, ForeignKey("users.id"))
      consultant_id = Column(Integer, ForeignKey("users.id"), nullable=True)
      
      # Response
      response = Column(Text, nullable=True)
      decision = Column(Enum("approved", "rejected", "needs_revision"))
      
      # Status
      status = Column(Enum("draft", "submitted", "responded", "closed"))
      created_at = Column(DateTime, default=datetime.utcnow)
      responded_at = Column(DateTime, nullable=True)
  ```
- [ ] Create service: `backend/app/services/crp_service.py`
- [ ] Create API endpoints: `backend/app/api/v1/endpoints/crp.py` (8 endpoints)
- [ ] Add telemetry: `crp_created`, `crp_submitted`, `crp_responded`

#### VCR Frontend (5 hours)
- [ ] Create `frontend/src/components/vcr/VCRForm.tsx`:
  - Title, problem statement, root cause, solution fields
  - Evidence attachment (link to Evidence Vault)
  - ADR linkage (dropdown)
  - AI tools used (multi-select)
  - Submit button
- [ ] Create `frontend/src/components/vcr/VCRCard.tsx`:
  - Display VCR details
  - Approve/Reject buttons (CTO/CEO only)
  - Evidence links
  - ADR links
- [ ] Create `frontend/src/components/vcr/VCRList.tsx`:
  - List all VCRs for project
  - Filter by status
  - Search
- [ ] Add route: `/app/projects/{id}/vcrs`

**Deliverables**:
- CRP backend (~1,000 LOC)
- VCR frontend (~800 LOC)
- 3 React components

**Exit Criteria**:
- [ ] CRP backend complete
- [ ] VCR UI functional
- [ ] Can create and view VCRs

### Day 3: CRP Frontend + SASE Templates

**Objectives**:
- Create CRP frontend UI
- Integrate SASE templates from Framework

**Tasks**:

#### CRP Frontend (4 hours)
- [ ] Create `frontend/src/components/crp/CRPForm.tsx`:
  - Context, question, options fields
  - Recommended option selector
  - Consultant assignment (dropdown)
  - Submit button
- [ ] Create `frontend/src/components/crp/CRPCard.tsx`:
  - Display CRP details
  - Response form (consultant only)
  - Decision buttons (approved/rejected/needs_revision)
- [ ] Create `frontend/src/components/crp/CRPList.tsx`:
  - List all CRPs
  - Filter by status, consultant
- [ ] Add route: `/app/projects/{id}/crps`

#### SASE Templates Integration (4 hours)
- [ ] Copy templates from `SDLC-Enterprise-Framework/templates/`:
  - `BRS-Template.yaml` → `backend/app/templates/sase/brs.yaml`
  - `LPS-Template.yaml` → `backend/app/templates/sase/lps.yaml`
  - `MTS-Template.md` → `backend/app/templates/sase/mts.md`
  - `CRP-Template.md` → `backend/app/templates/sase/crp.md`
  - `MRP-Template.md` → `backend/app/templates/sase/mrp.md`
  - `VCR-Template.md` → `backend/app/templates/sase/vcr.md`
- [ ] Create template service: `backend/app/services/sase_template_service.py`
  - `get_template(type)`: Return template content
  - `render_template(type, context)`: Render with context (Jinja2)
- [ ] Add API endpoint: `GET /api/v1/sase/templates/{type}`

**Deliverables**:
- CRP frontend (~700 LOC)
- 6 SASE templates integrated
- Template service (~200 LOC)

**Exit Criteria**:
- [ ] CRP UI functional
- [ ] All 6 SASE templates available via API
- [ ] Template rendering works

### Day 4: AI-Assisted VCR/CRP Generation

**Objectives**:
- Implement AI-assisted VCR generation
- Implement AI-assisted CRP generation
- Integrate with AI Council

**Tasks**:

#### VCR Auto-Generation (4 hours)
- [ ] Update `vcr_service.py`:
  ```python
  async def auto_generate_vcr(pr: PullRequest) -> dict:
      """
      AI-assisted VCR generation from PR metadata.
      
      Uses:
      - PR title, description
      - Commit messages
      - File changes
      - Evidence linked to PR
      
      Returns:
      - title: str
      - problem_statement: str
      - root_cause_analysis: str
      - solution_approach: str
      - implementation_notes: str
      """
      
      # 1. Extract PR context
      context = extract_pr_context(pr)
      
      # 2. Call AI Council
      ai_council = get_ai_council_service()
      vcr_draft = await ai_council.generate_vcr(context)
      
      # 3. Return draft
      return vcr_draft
  ```
- [ ] Integrate with AI Council service
- [ ] Add "Auto-generate" button in VCR UI
- [ ] Show AI-generated draft (editable)

#### CRP Auto-Generation (4 hours)
- [ ] Update `crp_service.py`:
  ```python
  async def auto_generate_crp(context: str) -> dict:
      """
      AI-assisted CRP generation from context.
      
      Uses:
      - User-provided context
      - Project ADRs
      - Past CRPs for similar issues
      
      Returns:
      - title: str
      - question: str (clarified)
      - options_considered: List[str]
      - recommended_option: str
      """
      
      # 1. Clarify question using AI
      clarified_question = await ai_council.clarify_question(context)
      
      # 2. Generate options
      options = await ai_council.generate_options(clarified_question)
      
      # 3. Recommend option
      recommended = await ai_council.recommend_option(options)
      
      return {
          "title": f"Consultation: {clarified_question[:50]}...",
          "question": clarified_question,
          "options_considered": options,
          "recommended_option": recommended
      }
  ```
- [ ] Add "AI Assist" button in CRP UI
- [ ] Show AI suggestions (editable)

**Deliverables**:
- VCR auto-generation (~300 LOC)
- CRP auto-generation (~300 LOC)
- AI Council integration

**Exit Criteria**:
- [ ] VCR auto-generation works
- [ ] CRP auto-generation works
- [ ] AI Council integration tested

### Day 5: Testing + Documentation + Metrics

**Objectives**:
- Write comprehensive tests
- Complete documentation
- Measure SASE Artifacts completion

**Tasks**:

#### Testing (4 hours)
- [ ] Backend tests:
  - VCR service: 15 unit tests
  - CRP service: 15 unit tests
  - Template service: 8 unit tests
  - API endpoints: 16 integration tests
- [ ] Frontend tests:
  - VCR components: 8 tests
  - CRP components: 8 tests
- [ ] E2E tests:
  - Create VCR → Submit → Approve
  - Create CRP → Submit → Respond
  - AI-assisted generation

**Total Tests**: 70 new tests

#### Documentation (3 hours)
- [ ] Create `docs/04-build/06-SASE/SASE-WORKFLOW-GUIDE.md`:
  - VCR workflow overview
  - CRP workflow overview
  - When to use each artifact
  - Example workflows
- [ ] Update `AGENTS.md`:
  - VCR endpoints
  - CRP endpoints
  - SASE templates
- [ ] Create video walkthrough (10 minutes):
  - VCR creation demo
  - CRP consultation demo
  - AI-assisted generation demo

#### Metrics (1 hour)
- [ ] Calculate SASE Artifacts completion:
  - BRS: ✅ 100% (template + integration)
  - LPS: ✅ 100% (template + integration)
  - MTS: ✅ 100% (template + integration)
  - CRP: ✅ 100% (template + integration + UI)
  - MRP: ⏳ 50% (template exists, not integrated)
  - VCR: ✅ 100% (template + integration + UI)
  - **Overall: 75%** (was 60%)
- [ ] Update Framework Realization:
  - SASE Artifacts: 60% → 75% (+15%)
  - Overall: 85% → 87% (+2%)

**Deliverables**:
- 70 new tests
- SASE workflow guide
- 10-minute video walkthrough
- Metrics report

**Exit Criteria**:
- [ ] All tests passing (≥95% coverage)
- [ ] Documentation complete
- [ ] SASE Artifacts: 75% completion verified

---

## Key Performance Indicators (KPIs)

| Metric | Baseline (S150) | Target (S151) | Success Criteria |
|--------|-----------------|---------------|------------------|
| **SASE Artifacts Completion** | 60% | 75% | +15% |
| **VCR Workflow** | 0% | 100% | Operational |
| **CRP Workflow** | 0% | 100% | Operational |
| **SASE Templates** | 3/6 (BRS, LPS, MTS) | 6/6 | All integrated |
| **AI-Assisted Generation** | No | Yes | VCR + CRP |
| **Test Coverage** | 95% | ≥95% | Maintained |
| **Framework Realization** | 85% | 87% | +2% |

---

## SASE Artifacts Completion Breakdown

| Artifact | Before S151 | After S151 | Completion |
|----------|-------------|------------|------------|
| **BRS** | Template only | Template + Integration | 100% |
| **LPS** | Template only | Template + Integration | 100% |
| **MTS** | Template only | Template + Integration | 100% |
| **CRP** | Template only | Template + Integration + UI + AI | 100% |
| **MRP** | Template only | Template only (deferred S152) | 50% |
| **VCR** | Template only | Template + Integration + UI + AI | 100% |
| **OVERALL** | **60%** | **75%** | **+15%** |

**Sprint 152 Target**: MRP integration (75% → 85%)

---

## VCR Workflow Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│ VCR (Version Controlled Resolution) Workflow                       │
└─────────────────────────────────────────────────────────────────────┘

1. Developer creates PR
2. PR passes gates (or has VCR override)
3. Developer creates VCR:
   - Problem statement
   - Root cause analysis
   - Solution approach
   - Implementation notes
   - Evidence links
   - ADR links
4. Developer submits VCR for approval
5. CTO/CEO reviews VCR:
   - Approve → Merge PR
   - Reject → Request changes
6. Post-merge: VCR stored in Evidence Vault
7. VCR linked to:
   - PR (GitHub)
   - Evidence (MinIO)
   - ADRs (Design docs)
   - Project (PostgreSQL)

┌──────────┐     ┌──────────┐     ┌──────────┐     ┌──────────┐
│ PR       │────▶│ VCR      │────▶│ CTO/CEO  │────▶│ Merged   │
│ Created  │     │ Created  │     │ Approval │     │ PR       │
└──────────┘     └──────────┘     └──────────┘     └──────────┘
                       │                                  │
                       ▼                                  ▼
                 ┌──────────┐                      ┌──────────┐
                 │ Evidence │                      │ Evidence │
                 │ Vault    │                      │ Vault    │
                 └──────────┘                      └──────────┘
```

---

## CRP Workflow Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│ CRP (Consultation Request Pack) Workflow                           │
└─────────────────────────────────────────────────────────────────────┘

1. Developer needs expert input (architecture, design, approach)
2. Developer creates CRP:
   - Context (what's the situation?)
   - Question (what decision needs to be made?)
   - Options considered (what are the alternatives?)
   - Recommended option (what do you think?)
3. Developer submits CRP to consultant (CTO, Architect, Domain Expert)
4. Consultant reviews CRP:
   - Approved → Decision documented
   - Rejected → Alternative suggested
   - Needs revision → Request more context
5. Decision stored in Evidence Vault
6. CRP linked to:
   - ADR (if architectural decision)
   - Project
   - Evidence

┌──────────┐     ┌──────────┐     ┌──────────┐     ┌──────────┐
│ Question │────▶│ CRP      │────▶│Consultant│────▶│ Decision │
│ Arises   │     │ Created  │     │ Reviews  │     │ Made     │
└──────────┘     └──────────┘     └──────────┘     └──────────┘
                       │                                  │
                       ▼                                  ▼
                 ┌──────────┐                      ┌──────────┐
                 │ AI       │                      │ ADR      │
                 │ Assist   │                      │ Created  │
                 └──────────┘                      └──────────┘
```

---

## Risk Management

| Risk | Impact | Probability | Mitigation | Status |
|------|--------|-------------|------------|--------|
| **VCR adoption low** | Medium | Medium | Training + documentation | ⏳ |
| **CRP response time slow** | Medium | Medium | SLA: 24h response time | ⏳ |
| **AI-generated VCR quality low** | High | Low | Human review required | ⏳ |
| **SASE templates confusing** | Medium | Low | Video walkthrough + examples | ⏳ |

---

## Dependencies

### Upstream (Blockers)
- ✅ Sprint 150 complete (Phase 1 baseline)
- ✅ Evidence Vault operational
- ✅ AI Council service available

### Downstream (Depends on Sprint 151)
- Sprint 152: Context Authority UI requires VCR integration
- Sprint 154: Spec Standard requires SASE artifact linkage

---

## Success Metrics Summary

### Primary Metrics
- ✅ SASE Artifacts: 60% → 75% (+15%)
- ✅ VCR workflow operational
- ✅ CRP workflow operational

### Secondary Metrics
- ✅ 6/6 SASE templates integrated
- ✅ AI-assisted generation for VCR + CRP
- ✅ 70 new tests

### Business Metrics
- **Framework Realization**: 85% → 87% (+2%)
- **Developer Experience**: Clear process for complex changes
- **AI Governance**: Structured consultation for AI code

---

## Retrospective Template (Post-Sprint)

*To be filled after Sprint 151 completion (March 8, 2026)*

### What Went Well
- TBD

### What Could Be Improved
- TBD

### Action Items for Sprint 152
- TBD

---

## References

- [ROADMAP-147-170.md](ROADMAP-147-170.md) - Overall roadmap
- [SDLC-Enterprise-Framework/SASE](SDLC-Enterprise-Framework/) - SASE methodology
- [VCR-Template.md](SDLC-Enterprise-Framework/templates/VCR-Template.md)
- [CRP-Template.md](SDLC-Enterprise-Framework/templates/CRP-Template.md)

---

**Sprint Owner**: CTO  
**Created**: February 3, 2026  
**Next Sprint Planning**: March 8, 2026 (Sprint 152)
