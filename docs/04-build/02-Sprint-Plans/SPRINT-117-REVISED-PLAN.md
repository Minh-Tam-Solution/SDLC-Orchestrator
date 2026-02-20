# Sprint 117: Revised Dual-Track Plan
## Framework 6.0 Spec Migration (Track 1) + Orchestrator Alignment (Track 2)

**Date**: January 28, 2026
**Sprint Duration**: 10 days (Jan 28 - Feb 7, 2026)
**Status**: 🔄 IN PROGRESS (Day 2 Complete)
**Strategic Context**: Track 1 leads, Track 2 follows with synchronized milestones

---

## Executive Summary

**Track 1 (Framework 6.0 Spec Migration)** is the **conductor** (nhạc trưởng) - sets the pace and defines the milestones. Track 2 (Orchestrator Alignment) follows Track 1's progress and resumes work when Track 1 reaches specific milestones.

**Current Status (Day 2 - Jan 28)**:
- **Track 1**: ✅ 5/20 specs complete (25%) - All P0 specs migrated (~4,650 LOC)
- **Track 2**: ⏸️ PAUSED - POC approved, waiting for Track 1 milestones

**Key Decision**: Track 2 resumes when Track 1 completes **Milestone 1** (P1 specs) on Day 5 (Jan 31).

---

## Track 1: Framework 6.0 Spec Migration (Leader)

### Track 1 Status Summary

| Milestone | Target Date | Specs | Status | Progress |
|-----------|-------------|-------|--------|----------|
| **Day 1-2: P0 Specs** | Jan 28 | 5 specs | ✅ COMPLETE | 5/5 (100%) |
| **Day 3-5: P1 Specs** | Jan 31 | 7 specs | 🔄 NEXT | 0/7 (0%) |
| **Week 2: P2+P3 Specs** | Feb 7 | 8 specs | ⏳ PLANNED | 0/8 (0%) |
| **Week 2 End: Documentation** | Feb 7 | Section 7 + CONTENT-MAP | ⏳ PLANNED | 0/2 (0%) |

**Overall Progress**: 5/20 specs (25%) + 0/2 docs (0%) = **5/22 deliverables (23%)**

---

### Track 1 Detailed Schedule

#### ✅ Milestone 0: P0 Specs (Day 1-2 - COMPLETE)

**Dates**: Jan 28 (Day 1-2)
**Status**: ✅ COMPLETE
**Deliverables**:
1. ✅ SPEC-0001: Governance System Specification (~750 LOC)
2. ✅ SPEC-0002: Quality Gates Specification (~850 LOC)
3. ✅ SPEC-0003: ADR-007 AI Context Engine (~900 LOC)
4. ✅ SPEC-0004: Policy Guards Design (~1,100 LOC)
5. ✅ SPEC-0005: System Architecture Document (~1,050 LOC)

**Total Output**: ~4,650 lines of Framework 6.0.5-compliant specifications
**Requirements**: 36 functional requirements in BDD format
**Acceptance Criteria**: 58 acceptance criteria with test methods

**Track 2 Dependency**: None (Track 2 POC already complete and approved)

---

#### 🔄 Milestone 1: P1 Specs (Day 3-5 - NEXT)

**Dates**: Jan 29-31 (Day 3-5)
**Status**: 🔄 NEXT (Starting Jan 29)
**Target**: 7 P1 specs (priority 75-85)

**Day 3 (Jan 29) - 2 specs**:
1. [ ] SPEC-0006: ADR-022 Multi-Provider Codegen Architecture (priority 85, ~800 LOC)
2. [ ] SPEC-0007: AGENTS-MD Technical Design (priority 84, ~750 LOC)

**Day 4 (Jan 30) - 2 specs**:
3. [ ] SPEC-0008: ADR-036 4-Tier Policy Enforcement (priority 82, ~700 LOC)
4. [ ] SPEC-0009: Codegen Service Specification (priority 80, ~850 LOC)

**Day 5 (Jan 31) - 3 specs**:
5. [ ] SPEC-0010: IR Processor Specification (priority 78, ~900 LOC)
6. [ ] SPEC-0011: ADR-012 AI Task Decomposition (priority 76, ~650 LOC)
7. [ ] SPEC-0012: Validation Pipeline Interface (priority 75, ~700 LOC)

**Estimated Output**: ~5,350 LOC (Day 3-5)
**Cumulative After Milestone 1**: ~10,000 LOC (12/20 specs = 60%)

**Track 2 Dependency**: **RESUME POINT** - Track 2 resumes when Milestone 1 complete (Jan 31 EOD)

---

#### ⏳ Milestone 2: P2+P3 Specs (Week 2 Days 1-3 - PLANNED)

**Dates**: Feb 3-5 (Week 2 Days 1-3)
**Status**: ⏳ PLANNED
**Target**: 8 P2+P3 specs (priority 50-74)

**Day 1-2 (Feb 3-4) - 5 P2 specs**:
1. [ ] SPEC-0013: Teams Service Specification (priority 74, ~600 LOC)
2. [ ] SPEC-0014: Planning Hierarchy Implementation (priority 72, ~700 LOC)
3. [ ] SPEC-0015: Governance Metrics & Dashboards (priority 70, ~650 LOC)
4. [ ] SPEC-0016: Evidence Vault Service (priority 68, ~750 LOC)
5. [ ] SPEC-0017: AI Council Service (priority 66, ~800 LOC)

**Day 3 (Feb 5) - 3 P3 specs**:
6. [ ] SPEC-0018: AGENTS-MD Integration (priority 64, ~500 LOC)
7. [ ] SPEC-0019: Feedback Learning Service (priority 62, ~550 LOC)
8. [ ] SPEC-0020: Conformance Check Service (priority 60, ~600 LOC)

**Estimated Output**: ~5,150 LOC (Week 2 Days 1-3)
**Cumulative After Milestone 2**: ~15,150 LOC (20/20 specs = 100%)

**Track 2 Dependency**: Track 2 continues Orchestrator automation (CLI, pre-commit, GitHub Actions)

---

#### ⏳ Milestone 3: Documentation Updates (Week 2 Days 4-5 - PLANNED)

**Dates**: Feb 6-7 (Week 2 Days 4-5)
**Status**: ⏳ PLANNED
**Target**: 2 major documentation updates

**Day 4 (Feb 6)**:
1. [ ] Update Section 7: Quality Assurance System
   - Anti-Vibecoding documentation (~800 LOC)
   - Vibecoding Index calculation formulas
   - Progressive Routing rules (Green/Yellow/Orange/Red)
   - Kill Switch criteria and recovery procedures

**Day 5 (Feb 7)**:
2. [ ] Update CONTENT-MAP.md navigation (~300 LOC)
   - Framework 6.0.5 structure references
   - /spec/ directory navigation
   - Cross-references to 20 migrated specs
   - Validate all links (ensure no broken references)

3. [ ] Validate all cross-references
   - Check all ADR links in specs
   - Check all related_specs links
   - Check all framework_version references

**Estimated Output**: ~1,100 LOC (documentation updates)
**Cumulative After Milestone 3**: ~16,250 LOC (20 specs + 2 docs = 100%)

**Track 2 Dependency**: Track 2 completes Orchestrator automation and testing

---

## Track 2: Orchestrator Alignment (Follower)

### Track 2 Status Summary

| Phase | Depends On | Target Date | Status | Progress |
|-------|------------|-------------|--------|----------|
| **Phase 0: POC** | None | Jan 28 | ✅ COMPLETE | 5/5 files (100%) |
| **Phase 1: Commit POC** | Track 1 Day 2 | Jan 29 | ✅ COMPLETE | 1/1 (100%) |
| **Phase 2: SPEC-0001/0002** | None (Override) | Jan 28 | ✅ COMPLETE | 2/2 (100%) |
| **Phase 3: Orchestrator Automation** | Sprint 118 | Feb 10 | ⏸️ BLOCKED | 0/5 (0%) |

**Overall Progress**: 8/13 deliverables (62%) - Phase 2 complete (100% validation), Phase 3 blocked until Sprint 118

---

### Track 2 Detailed Schedule

#### ✅ Phase 0: Spec-First POC (Day 2 Afternoon - COMPLETE)

**Date**: Jan 28 (Day 2 Afternoon)
**Status**: ✅ COMPLETE
**Validation**: 23/25 checks PASSED (92%) - CTO APPROVED

**Deliverables**:
1. ✅ `spec/evidence/spec-frontmatter-schema.json` - JSON Schema for spec validation
2. ✅ `spec/controls/anti-vibecoding.yaml` - 3 controls (AVC-001/002/003)
3. ✅ `spec/gates/gates.yaml` - 5 gates (G0-G4) with tier requirements
4. ✅ `spec/VERSIONING.md` - Framework vs schema versioning strategy
5. ✅ `docs/SPEC-FIRST-POC-VALIDATION.md` - Manual validation checklist

**Total Output**: ~1,350 lines of pure YAML/JSON/Markdown specifications

**CTO Decision**: ✅ APPROVED TO COMMIT

---

#### ✅ Phase 1: Commit POC Files (Day 3 - COMPLETE)

**Date**: Jan 28-29 (Day 2-3)
**Status**: ✅ COMPLETE
**Dependency**: Track 1 Day 2 complete (✅ DONE)

**Tasks**:
1. [x] Commit 5 POC files to Framework repository
   ```bash
   cd /home/nqh/shared/SDLC-Orchestrator/SDLC-Enterprise-Framework
   git add spec/ docs/SPEC-FIRST-POC-VALIDATION.md
   git commit -m "feat(SDLC 6.1.0): Add spec-first POC (5 files, zero code)

   - spec/evidence/spec-frontmatter-schema.json (v1.0.0)
   - spec/controls/anti-vibecoding.yaml (AVC-001/002/003)
   - spec/gates/gates.yaml (G0-G4)
   - spec/VERSIONING.md (versioning rules)
   - docs/SPEC-FIRST-POC-VALIDATION.md (validation report)

   Purity guarantee:
   - Zero executable code (.py, .ts, .sh)
   - Platform-agnostic definitions only
   - Semantic-only gates (no automation blocks)

   Framework version: 6.0.5 (in development)
   Validation: 23/25 checks PASS (2 deferred: SPEC-0001/0002 frontmatter)

   Co-Authored-By: CTO Approval <cto@nhatquangholding.com>"
   git push origin main
   ```
   **Commit Hash**: `493c830` (Jan 28, 2026)

2. [x] Update sprint plan documents
   - Mark Phase 1 as COMPLETE in SPRINT-117-REVISED-PLAN.md
   - Update progress tracking (46% overall)

**Actual Time**: 30 minutes (Jan 28-29)
**Deliverables**: ✅ Git commit (493c830) + sprint plan updates

**Completion Status**: ✅ PHASE 1 COMPLETE (Jan 29)

---

#### ✅ Phase 2: Create SPEC-0001 and SPEC-0002 (Day 2 Evening - COMPLETE)

**Date**: Jan 28 (Day 2 Evening)
**Status**: ✅ COMPLETE (100% validation achieved)
**Dependency**: None (CTO override: "không cần chờ jan 31")

**CTO Decision**: User explicitly overrode blocking condition with "track 2 tiếp tục đi không cần chờ jan 31" (track 2 continue, no need to wait until Jan 31). This allowed Phase 2 to proceed immediately using Phase 1 POC files as templates.

**Tasks**:
1. [x] Create SPEC-0001-Anti-Vibecoding.md with YAML frontmatter
   - ✅ Actual: 1,100 LOC
   - ✅ 8 functional requirements in BDD format
   - ✅ 4 non-functional requirements
   - ✅ 12 acceptance criteria with test methods
   - ✅ Tier-specific: PROFESSIONAL (WARNING), ENTERPRISE (SOFT/FULL)
   - ✅ 5-phase implementation roadmap
   - ✅ 3 design decisions with rationale

2. [x] Create SPEC-0002-Specification-Standard.md with YAML frontmatter
   - ✅ Actual: 930 LOC
   - ✅ 8 functional requirements in BDD format
   - ✅ 4 non-functional requirements
   - ✅ 12 acceptance criteria with test methods
   - ✅ ALL tiers: LITE/STANDARD/PROFESSIONAL/ENTERPRISE
   - ✅ 5-phase implementation including tooling
   - ✅ 3 design decisions (YAML, BDD, Tier sections)

3. [x] Validate frontmatter against spec-frontmatter-schema.json
   ```bash
   $ python3 validate_frontmatter.py SPEC-0001-Anti-Vibecoding.md
   ✅ VALIDATION PASSED: SPEC-0001-Anti-Vibecoding.md

   $ python3 validate_frontmatter.py SPEC-0002-Specification-Standard.md
   ✅ VALIDATION PASSED: SPEC-0002-Specification-Standard.md
   ```
   - ✅ Both specs pass automated validation
   - ✅ All required fields present and valid
   - ✅ YAML frontmatter compliant with schema

4. [x] Update SPEC-FIRST-POC-VALIDATION.md
   - ✅ Added validation results for SPEC-0001 (Section 3.1)
   - ✅ Added validation results for SPEC-0002 (Section 3.2)
   - ✅ Updated final score: 25/25 checks PASS (100%)
   - ✅ 7 acceptance criteria verified
   - ✅ CTO approval documented

5. [x] Commit to Framework repository
   ```bash
   cd SDLC-Enterprise-Framework
   git add docs/specs/SPEC-0001-Anti-Vibecoding.md
   git add docs/specs/SPEC-0002-Specification-Standard.md
   git add docs/SPEC-FIRST-POC-VALIDATION.md
   git commit -m "feat(spec): Add SPEC-0001 and SPEC-0002..."
   git push origin main
   ```
   **Commit Hash**: `0617883` (Jan 28, 2026)

**Actual Time**: 4 hours (Jan 28, 19:30-23:30)
**Deliverables**: 2 specification files (~2,030 LOC) + validation report + commit
**Final Validation Score**: ✅ **25/25 (100%)**

**Completion Status**: ✅ PHASE 2 COMPLETE (Jan 28, 23:30)

---

#### ⏸️ Phase 3: Orchestrator Automation (Sprint 118 - DEFERRED)

**Original Dates**: Feb 3-7 (Week 2 of Sprint 117)
**Status**: ⏸️ DEFERRED to Sprint 118 (Feb 10-21)
**CTO Decision (Jan 28)**: "DEFER - Do NOT start automation until Feb 3" → Further deferred to Sprint 118 (Feb 10) to maintain conductor/follower discipline

**Detailed Sprint 118 Plan**: 📋 [SPRINT-118-TRACK-2-PLAN.md](./SPRINT-118-TRACK-2-PLAN.md) - 6 deliverables (documentation only, no code until Feb 10)

**Rationale for Deferral**:
- Track 1 must complete first (20/20 specs by Feb 7)
- Sprint 117 priority is Framework 6.0.5 spec layer
- Automation belongs to Sprint 118 implementation phase
- Prevents premature optimization
- Planning phase (Jan 28 - Feb 9) focuses on design only

**Start Conditions (ALL must be true)**:
1. ✅ Track 1 completes 20/20 specs
2. ✅ Framework 6.0.5 spec layer finalized
3. ✅ Sprint 117 officially ends (Feb 7)
4. ✅ Sprint 118 kickoff (Feb 10)
5. ✅ All 6 design deliverables completed and approved

**Pre-Sprint 118 Activities (Jan 28 - Feb 9)**:
- **D1**: Database schema design (14 tables, ERD, migrations) - Backend Lead
- **D2**: API architecture design (12 endpoints, OpenAPI 3.0) - Backend Lead
- **D3**: Technical dependencies documentation - DevOps Lead
- **D4**: Testing strategy design (95%+ coverage) - QA Lead
- **D5**: Implementation phases breakdown (10-day sprint) - Tech Lead
- **D6**: Architecture diagrams (5 diagrams) - Tech Lead

**Updated Dependency**: Sprint 118 starts (Feb 10)

**Day 1-2 (Feb 3-4): CLI Tool Development**:
1. [ ] Create `sdlcctl spec validate` CLI (Python)
   - Location: `SDLC-Orchestrator/backend/app/cli/sdlcctl_spec_validate.py`
   - Reads Framework schemas from submodule
   - Validates YAML frontmatter against JSON Schema
   - Validates controls against structure rules
   - Validates gates against tier requirements
   - Error reporting with detailed messages
   - Estimated: ~400-500 LOC

2. [ ] Create CLI entry point
   - `sdlcctl spec validate --file SPEC-0001.md`
   - `sdlcctl spec validate --directory docs/`
   - Batch validation support
   - Estimated: ~100-150 LOC

3. [ ] Unit tests for CLI tool
   - Test JSON Schema validation
   - Test YAML syntax validation
   - Test error handling
   - Test batch validation
   - Coverage target: 95%+
   - Estimated: ~300-400 LOC

**Day 3 (Feb 5): Integration Templates**:
4. [ ] Create pre-commit hook template
   - `.pre-commit-config.yaml` example
   - Blocks commits with invalid specs
   - Runs `sdlcctl spec validate` automatically
   - Estimated: ~50-80 LOC

5. [ ] Create GitHub Actions workflow template
   - `.github/workflows/spec-validation.yml`
   - Runs on PR creation/update
   - Validates all changed specs
   - Comments on PR with validation results
   - Estimated: ~100-150 LOC

**Day 4-5 (Feb 6-7): Dashboard Integration + Testing**:
6. [ ] Dashboard compliance page
   - Frontend: `frontend/src/app/compliance/specs`
   - Display validation results for all specs
   - Spec list with PASS/FAIL status
   - Error details for failed specs
   - Estimated: ~300-400 LOC (frontend + backend API)

7. [ ] Integration testing
   - E2E test: CLI validation → Dashboard display
   - Test Framework submodule integration
   - Performance test: 100+ specs in <10s
   - Estimated: ~200-300 LOC

8. [ ] Documentation
   - Usage guide: How to use `sdlcctl spec validate`
   - Pre-commit setup guide
   - CI/CD integration guide (GitHub Actions, GitLab CI)
   - Update CLAUDE.md with spec validation workflow
   - Estimated: ~500-600 LOC (Markdown)

**Estimated Time**: 10 days (Sprint 118: Feb 10-21)
**Total Output**: ~2,000-2,500 LOC (code + docs)

**Resume Condition**: 🔄 RESUME ON FEB 10 (Sprint 118 kickoff - automation phase begins)

---

## Synchronization Points

### Sprint 117 Key Milestones (Track 1 → Track 2 Handoffs)

| Milestone | Track 1 Delivers | Track 2 Status | Date |
|-----------|------------------|----------------|------|
| **M0** | 5 P0 specs (~4,650 LOC) | ✅ Phase 1: POC committed (493c830) | ✅ Jan 28-29 |
| **M0.5** | N/A (Override) | ✅ Phase 2: SPEC-0001/0002 (0617883) | ✅ Jan 28 |
| **M1** | 7 P1 specs (~5,350 LOC) | ⏸️ Phase 3: Deferred to Sprint 118 | 🔄 Jan 31 |
| **M2** | 8 P2+P3 specs (~5,150 LOC) | ⏸️ Phase 3: Deferred to Sprint 118 | 🔄 Feb 3 |
| **M3** | Documentation updates (~1,100 LOC) | ⏸️ Phase 3: Deferred to Sprint 118 | 🔄 Feb 7 |

**Critical Path**: Track 1 completes (Feb 7) → Sprint 118 starts (Feb 10) → Track 2 Phase 3 begins

---

## Sprint 117 Success Criteria

### Track 1 (Framework 6.0 Spec Migration)
- [ ] 20/20 specs migrated to Framework 6.0.5 format (~15,000 LOC)
- [ ] Section 7 updated with Anti-Vibecoding documentation
- [ ] CONTENT-MAP.md updated with Framework 6.0 navigation
- [ ] All cross-references validated (no broken links)
- [ ] 100% compliance with Framework 6.0.5 standards

### Track 2 (Orchestrator Alignment)
- [x] 5 POC files committed to Framework repository (✅ Phase 1: 493c830)
- [x] SPEC-0001 and SPEC-0002 created with validated frontmatter (✅ Phase 2: 0617883, 25/25 validation)
- [ ] `sdlcctl spec validate` CLI tool complete (~500 LOC) (⏸️ Deferred to Sprint 118)
- [ ] Pre-commit hook + GitHub Actions templates (~150 LOC)
- [ ] Dashboard compliance page complete (~400 LOC)
- [ ] Documentation complete (~600 LOC)
- [ ] Test coverage 95%+ (unit + integration)

### Overall Sprint Success
- [ ] Track 1: 100% complete (20 specs + 2 docs)
- [ ] Track 2: 100% complete (13 deliverables)
- [ ] Zero blockers or delays
- [ ] CTO approval for both tracks

---

## Risk Mitigation

### Risk 1: Track 1 Delays Impact Track 2
**Likelihood**: MEDIUM
**Impact**: HIGH
**Mitigation**:
- Track 2 Phase 1 (commit POC) can proceed immediately (not blocked)
- If Track 1 delayed beyond Jan 31, Track 2 creates SPEC-0001/0002 using P0 specs as templates
- Track 2 can start Orchestrator automation prep work (design, dependencies) in parallel

### Risk 2: Track 2 Team Idle During Pauses
**Likelihood**: LOW
**Impact**: MEDIUM
**Mitigation**:
- Phase 1 (commit POC) ready to resume now - no idle time
- During Phase 2 wait (Jan 29-31), team can:
  - Review P1 specs as they're completed (learn patterns)
  - Design CLI tool architecture (prep for Phase 3)
  - Set up development environment for Orchestrator

### Risk 3: Specification Format Inconsistency
**Likelihood**: MEDIUM
**Impact**: MEDIUM
**Mitigation**:
- Track 1 uses proven templates from P0 specs (SPEC-0001 to SPEC-0005)
- Daily sync between Track 1 and Track 2 leads (15-min standup)
- Track 2 reviews specs as Track 1 completes them (early feedback)

---

## Communication Plan

### Daily Standup (9:00 AM)
**Attendees**: Track 1 Lead, Track 2 Lead, PM
**Duration**: 15 minutes
**Format**:
- Track 1: Yesterday/Today/Blockers
- Track 2: Yesterday/Today/Blockers (if active)
- Sync points: Dependencies clear?

### Milestone Reviews (End of Each Milestone)
**M1 Review** (Jan 31 EOD):
- Track 1: All 7 P1 specs complete?
- Track 2: Ready to resume Phase 2?
- Go/No-Go decision for Track 2 Phase 2

**M2 Review** (Feb 5 EOD):
- Track 1: All 8 P2+P3 specs complete?
- Track 2: SPEC-0001/0002 complete?
- Go/No-Go decision for Track 2 Phase 3 continuation

**M3 Review** (Feb 7 EOD):
- Track 1: Documentation updates complete?
- Track 2: Orchestrator automation complete?
- Sprint 117 retrospective

### Sprint Retrospective (Feb 7, 3:00 PM)
**Attendees**: Full team
**Duration**: 1 hour
**Topics**:
- What worked: Dual-track coordination
- What didn't: Blockers, delays
- Action items: Process improvements for Sprint 118

---

## Next Steps (Immediate - Jan 29)

### Track 1 (Continue as Planned)
1. [ ] Begin Day 3 work: Migrate 2 P1 specs
   - SPEC-0006: ADR-022 Multi-Provider Codegen Architecture
   - SPEC-0007: AGENTS-MD Technical Design
2. [ ] Target: Complete 2 specs by Jan 29 EOD (~1,550 LOC)

### Track 2 (Phase 1 Complete)
1. [x] Read revised sprint plan (THIS DOCUMENT)
2. [x] **COMPLETE**: Execute Phase 1 - Commit POC files
   - Task: Git commit + push 5 POC files
   - Actual time: 30 minutes
   - Commit: 493c830 (Jan 28, 2026)
3. [x] Update sprint plan documents
   - Mark Phase 1 COMPLETE
   - Update progress tracking (46% overall)
4. [ ] **NEXT**: Wait for Track 1 M1 (Jan 31) to resume Phase 2

### Coordination
1. [ ] Share revised plan with team (Slack/Email)
2. [ ] Schedule M1 Review meeting (Jan 31, 4:00 PM)
3. [ ] Daily standup continues (9:00 AM daily)

---

**Document Status**: ✅ REVISED PLAN READY
**Track 1**: 🔄 IN PROGRESS (Day 3 starting)
**Track 2**: 🔄 READY TO RESUME (Phase 1 unblocked)
**Next Review**: M1 Review (Jan 31, 4:00 PM)

---

*Sprint 117 Revised Dual-Track Plan*
*Framework 6.0 Spec Migration + Orchestrator Alignment*
*Synchronized execution with clear dependencies*
