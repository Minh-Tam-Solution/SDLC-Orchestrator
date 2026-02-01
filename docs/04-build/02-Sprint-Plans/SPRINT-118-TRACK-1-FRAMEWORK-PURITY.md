# Sprint 118 Track 1: Framework 6.0 Purity Compliance
## SDLC-Enterprise-Framework Pure Methodology Enforcement

**Version**: 1.0.0
**Sprint**: 118 (Feb 10-21, 2026)
**Track**: 1 (Framework Focus - 40%)
**Status**: PLANNED
**Dependencies**: Sprint 117 Track 1 COMPLETE (20 specs migrated)

---

## Executive Summary

Sprint 117 Track 1 đã migrate 20 specs thành công, nhưng phân tích purity cho thấy **1,067+ violations** trong các specs. Sprint 118 Track 1 sẽ **reformat tất cả specs để đảm bảo Pure Methodology** - loại bỏ implementation details, giữ lại governance principles.

**Problem Statement**:
- 20 specs đã migrate có format đúng (YAML frontmatter, BDD)
- Nhưng **nội dung chứa implementation details** (database schemas, Python code, API endpoints)
- Violates Pure Methodology Principle: Framework = WHAT, Orchestrator = HOW

**Solution**:
- Reformat SPEC-0013 → SPEC-0020 (implementation-heavy specs)
- Add `implementation_ref:` trong frontmatter trỏ đến Orchestrator docs
- Đảm bảo 0 violations trong Core + Governance Ring

---

## Purity Violation Summary (Sprint 117 Analysis)

### Violations Found by Spec

| Spec | LOC Original | Violations | Type | Action |
|------|-------------|------------|------|--------|
| SPEC-0001 | ~600 | ~15 | Mixed | FIX |
| SPEC-0002 | ~650 | ~20 | Mixed | FIX |
| SPEC-0003 | ~700 | ~25 | Mixed | FIX |
| SPEC-0004 | ~750 | ~30 | Mixed (OPA Rego) | FIX |
| SPEC-0005 | ~800 | ~35 | Mixed | FIX |
| SPEC-0006 | ~850 | ~40 | Mixed | FIX |
| SPEC-0007 | ~700 | ~35 | Mixed (TypeScript) | FIX |
| SPEC-0008 | ~650 | ~30 | Mixed | FIX |
| SPEC-0009 | ~800 | ~40 | Implementation | FIX |
| SPEC-0010 | ~900 | ~45 | Implementation | FIX |
| SPEC-0011 | ~600 | ~30 | Mixed | FIX |
| SPEC-0012 | 788 | 26 | Mixed | FIX |
| **SPEC-0013** | 817 | **73** | **100% Implementation** | ✅ REFORMATTED |
| SPEC-0014 | 714 | 92 | 100% Implementation | REFORMAT |
| SPEC-0015 | 725 | 96 | 100% Implementation | REFORMAT |
| SPEC-0016 | 729 | 89 | 100% Implementation | REFORMAT |
| SPEC-0017 | 1360 | 127 | 100% Implementation | REFORMAT |
| SPEC-0018 | 1189 | 153 | 100% Implementation | REFORMAT |
| SPEC-0019 | 1078 | 118 | 100% Implementation | REFORMAT |
| SPEC-0020 | 1142 | 135 | 100% Implementation | REFORMAT |

**Total Violations**: 1,067+
**Critical Specs** (100% implementation): SPEC-0013 to SPEC-0020 (8 specs, 883 violations)

### Violation Types Breakdown

| Type | Count | Examples |
|------|-------|----------|
| Database Schema (SQL/PostgreSQL) | ~300 | `CREATE TABLE`, `VARCHAR`, `JSONB`, `UUID` |
| Python Code | ~250 | `class FooService:`, `async def`, `@dataclass` |
| API Endpoints | ~150 | `POST /api/v1/...`, FastAPI routes |
| CLI Commands | ~100 | `sdlcctl validate`, Click implementations |
| Tool Dependencies | ~100 | Version pins, specific tool refs |
| TypeScript/React | ~80 | React hooks, TypeScript interfaces |
| Test Code | ~60 | pytest fixtures, Playwright tests |
| Other | ~27 | GitHub Actions, Grafana dashboards |

---

## Sprint 118 Track 1 Goals

### Primary Objectives

1. **Reformat 8 Critical Specs** (SPEC-0013 to SPEC-0020) to Pure Methodology
2. **Fix Mixed Specs** (SPEC-0001 to SPEC-0012) - remove tool-specific code
3. **Update Core Methodology docs** for Section 7/8 consistency
4. **Validate Ring Structure** - ensure Core → Governance → Outer separation

### Success Criteria

| Criterion | Target | Measurement |
|-----------|--------|-------------|
| Purity violations in specs | **0** | Automated scan |
| Python/SQL code blocks in Framework | **0** | Grep count |
| CLI commands (sdlcctl) in Framework | **0** | Grep count |
| API endpoints in Framework | **0** | Grep count |
| implementation_ref in frontmatter | **20/20** | All specs |
| Core Methodology Section 7/8 coverage | **100%** | Document audit |

---

## Sprint 118 Track 1 Schedule

### Week 1 (Feb 10-14): Critical Spec Reformat

#### Day 1-2: SPEC-0013 to SPEC-0016 (4 specs)

**SPEC-0013** (Teams Data Model): ✅ DONE in Sprint 117
- 817 → 423 lines (48% reduction)
- 73 violations → 0 violations
- Added `implementation_ref:` to Orchestrator docs

**SPEC-0014** (Planning Hierarchy):
```yaml
Actions:
  - Remove 52 database schema field definitions
  - Remove 8 SQLAlchemy ORM references
  - Remove 3 Python service methods
  - Remove 4 API endpoints
  - Remove 5 GitHub API integrations
  - Remove 15 tool versions
Expected: 714 → ~350 lines (~50% reduction)
```

**SPEC-0015** (Governance Metrics):
```yaml
Actions:
  - Remove 29 database schema columns
  - Remove 5 Python implementations (including 46-line function)
  - Remove 15 Grafana references
  - Remove 40+ tool dependencies
Expected: 725 → ~300 lines (~60% reduction)
```

**SPEC-0016** (AGENTS.md Integration):
```yaml
Actions:
  - Remove 11 CLI commands
  - Remove 15 TypeScript interfaces
  - Remove 8 GitHub API integrations
  - Remove 12 database schema definitions
  - Remove 6 Python service implementations
Expected: 729 → ~350 lines (~52% reduction)
```

**Day 1-2 Deliverables**:
- [ ] SPEC-0014 reformatted (Pure Methodology)
- [ ] SPEC-0015 reformatted (Pure Methodology)
- [ ] SPEC-0016 reformatted (Pure Methodology)

#### Day 3-4: SPEC-0017 to SPEC-0020 (4 specs)

**SPEC-0017** (Feedback Learning Service):
```yaml
Actions:
  - Remove 18 Python service implementations
  - Remove 23 database schema definitions
  - Remove 12 Pydantic schemas
  - Remove 14 API endpoints
  - Remove 12 GitHub API integrations
  - Remove 8 multi-provider AI implementations
Expected: 1360 → ~400 lines (~70% reduction)
```

**SPEC-0018** (AGENTS.md Technical Implementation):
```yaml
Actions:
  - Remove 21 Python service implementations
  - Remove 25 database schema definitions
  - Remove 11 CLI commands (Click)
  - Remove 15 GitHub API integrations
  - Remove 6 Jinja2 templates
Expected: 1189 → ~350 lines (~70% reduction)
```

**SPEC-0019** (Conformance Testing):
```yaml
Actions:
  - Remove Python ConformanceCheckService
  - Remove 5 API endpoints
  - Remove TypeScript React hooks
  - Remove GitHub Actions workflow (60+ lines)
  - Remove Playwright E2E tests
Expected: 1078 → ~350 lines (~67% reduction)
```

**SPEC-0020** (Quality Gates Codegen):
```yaml
Actions:
  - Remove 45 database schema definitions
  - Remove 50 Python service implementations
  - Remove 6 Pydantic schemas
  - Remove 4 API endpoints
  - Remove 18 integration tests
Expected: 1142 → ~350 lines (~70% reduction)
```

**Day 3-4 Deliverables**:
- [ ] SPEC-0017 reformatted (Pure Methodology)
- [ ] SPEC-0018 reformatted (Pure Methodology)
- [ ] SPEC-0019 reformatted (Pure Methodology)
- [ ] SPEC-0020 reformatted (Pure Methodology)

#### Day 5: Mixed Specs Cleanup + Validation

**SPEC-0001 to SPEC-0012 Cleanup**:
```yaml
Actions (per spec):
  - Remove any remaining Python/SQL code blocks
  - Remove CLI command examples
  - Remove API endpoint definitions
  - Add implementation_ref to frontmatter
  - Validate BDD format compliance
```

**Day 5 Deliverables**:
- [ ] SPEC-0001 to SPEC-0012 cleaned (0 violations each)
- [ ] All 20 specs have implementation_ref in frontmatter
- [ ] Purity scan shows 0 violations

---

### Week 2 (Feb 17-21): Core Methodology + Ring Validation

#### Day 1-2: Core Methodology Updates

**02-Core-Methodology/ Updates**:
```yaml
SDLC-Core-Methodology.md:
  - Ensure Section 7 (QA System) reference complete
  - Ensure Section 8 (Unified Specs) reference complete
  - Verify 7 Pillars documentation current

SDLC-Quality-Assurance-System.md:
  - Remove any Orchestrator-specific references
  - Ensure Anti-Vibecoding is methodology-only
  - Add clear "Implementation: See Orchestrator" notes

SDLC-Agentic-Core-Principles.md:
  - Verify SASE principles are tool-agnostic
  - Ensure AI Governance Principles are methodology
```

**Day 1-2 Deliverables**:
- [ ] SDLC-Core-Methodology.md Section 7/8 complete
- [ ] SDLC-Quality-Assurance-System.md pure methodology
- [ ] SDLC-Agentic-Core-Principles.md validated

#### Day 3: 03-AI-GOVERNANCE Validation

**03-AI-GOVERNANCE/ Audit**:
```yaml
Files to validate (7 principles):
  - 01-AI-Human-Collaboration.md
  - 02-Agent-Accountability.md
  - 03-Planning-Mode-Principle.md
  - 04-Verification-Principle.md
  - 05-Context-Management.md
  - 06-Tool-Evaluation-Criteria.md
  - 07-Anti-Patterns.md

Checks:
  - No tool-specific code
  - No API references
  - No database schemas
  - Pure principles only
```

**Day 3 Deliverables**:
- [ ] All 7 AI Governance docs validated
- [ ] 0 purity violations in 03-AI-GOVERNANCE/

#### Day 4: Ring Structure Validation

**Ring Structure Audit**:
```yaml
CORE RING (02-Core-Methodology/, 01-Overview/):
  Target: 0 tool-specific references
  Check: grep for sdlcctl, PostgreSQL, FastAPI, etc.

GOVERNANCE RING (03-AI-GOVERNANCE/, spec/):
  Target: Pure rules and controls
  Check: No implementation code

OUTER RING (04-AI-TOOLS-LANDSCAPE/, 05-Templates-Tools/):
  Target: Tool knowledge allowed here
  Check: Clear separation from Core
```

**Day 4 Deliverables**:
- [ ] Ring Structure audit complete
- [ ] CONTENT-MAP.md reflects ring separation
- [ ] Inconsistencies documented and fixed

#### Day 5: Final Validation + Sprint Report

**Final Validation**:
```bash
# Automated purity scan
grep -r "sdlcctl\|PostgreSQL\|FastAPI\|SQLAlchemy\|Pydantic" \
  02-Core-Methodology/ 03-AI-GOVERNANCE/ \
  --include="*.md" | wc -l
# Target: 0

# Check implementation_ref in all specs
grep -r "implementation_ref:" 05-Templates-Tools/01-Specification-Standard/ | wc -l
# Target: 20
```

**Day 5 Deliverables**:
- [ ] Final purity scan: 0 violations
- [ ] Sprint 118 Track 1 Completion Report
- [ ] Sprint 119 Track 1 Plan (if needed)

---

## Reformat Template

### Before (Purity Violation)

```markdown
### FR-006: SQLAlchemy ORM Models

**Requirement**:
GIVEN the backend uses SQLAlchemy 2.0 with type hints
WHEN ORM models are defined for the new tables
THEN:
  - Organization model with Mapped type hints, UUID primary key, JSONB settings
  - Team model with organization_id FK, relationships to organization/members/projects
  - TeamMember model with CHECK constraints, @property methods (is_ai_agent, is_coach)
```

### After (Pure Methodology)

```markdown
### FR-006: Entity Relationships

**Requirement**:
GIVEN the system requires organizational hierarchy
WHEN entities are defined
THEN:
  - Organization entity contains teams and users
  - Team entity belongs to organization, contains members
  - TeamMember entity links users to teams with role-based access
  - SASE constraint: AI agents cannot have owner/admin roles

> **Implementation Reference**: See SDLC-Orchestrator/docs/02-design/14-Technical-Specs/Teams-Data-Model-Specification.md
```

---

## Success Metrics

| Metric | Week 1 Target | Week 2 Target | Final |
|--------|---------------|---------------|-------|
| Specs reformatted | 8/8 critical | 12/12 mixed | 20/20 |
| Purity violations | <100 | <10 | **0** |
| Core Ring clean | N/A | 100% | 100% |
| Governance Ring clean | N/A | 100% | 100% |
| implementation_ref added | 8/8 | 20/20 | 20/20 |

---

## Risk Mitigation

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Reformat breaks references | Medium | Medium | Validate all cross-references after each spec |
| Lost context for implementers | Low | High | Always add implementation_ref pointing to Orchestrator |
| Track 2 blocked by changes | Low | Medium | Coordinate with Track 2 daily |
| Time overrun | Medium | Low | Prioritize critical specs (0013-0020) first |

---

## Coordination with Track 2

### Dependencies

| Track 1 Output | Track 2 Input |
|----------------|---------------|
| Reformatted specs | Orchestrator docs alignment |
| implementation_ref links | Docs organization |
| Pure YAML controls | sdlcctl validation logic |

### Daily Sync Points

```yaml
Daily Standup (10min):
  - Track 1: Specs reformatted count, blockers
  - Track 2: Orchestrator alignment status
  - Cross-track: Any reference conflicts?
```

---

## Document Control

| Field | Value |
|-------|-------|
| **Version** | 1.0.0 |
| **Created** | January 29, 2026 |
| **Author** | Track 1 Lead |
| **Status** | PLANNED |
| **Sprint** | 118 (Feb 10-21, 2026) |
| **Track** | 1 (Framework - 40%) |
| **Parallel** | Track 2 (Orchestrator - 60%) in SPRINT-118-POST-SPRINT-117-PLAN.md |

---

**Next Steps**:
1. CTO approval of this plan
2. Begin Week 1 Day 1 (Feb 10)
3. Daily sync with Track 2
4. Sprint 118 Track 1 completion report (Feb 21)

---

**End of Sprint 118 Track 1 Plan**
