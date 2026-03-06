---
sdlc_version: "6.1.1"
document_type: "Sprint Plan"
status: "DRAFT — Pending CTO Approval"
sprint: "224"
tier: "PROFESSIONAL"
stage: "04 - Build"
---

# Sprint 224 — Auto-Generation Quality Gates + YAML Scope Extension

| Field            | Value                                                                                      |
|------------------|--------------------------------------------------------------------------------------------|
| Sprint Duration  | March 2026                                                                                 |
| Sprint Goal      | Replace hardcoded confidence scores in auto_generator.py with computed quality scoring, add post-generation validation with placeholder detection and YAML frontmatter enforcement, extend spec_frontmatter.py scope beyond SPEC-*.md files. |
| Status           | DRAFT — Pending CTO Approval                                                               |
| Priority         | P1 — Quality Enforcement (cross-project review finding)                                    |
| Framework        | SDLC 6.1.1                                                                                 |
| Previous Sprint  | Sprint 223 — Gate Content Quality                                                          |
| Raised by        | PM + Architect cross-project review vs EndiorBot Sprint 80 gaps (2026-03-06)               |
| CTO Review       | APPROVED 8.5/10 — G4 merged into G5 per CTO directive                                     |

---

## Root Cause

Auto-generator has 3-level fallback (LLM 85% → Template 60% → Minimal 30%) but confidence scores are hardcoded constants, not computed from actual output quality. No post-generation pass detects placeholders like `[TODO]` or `[Auto-generation failed]`. spec_frontmatter.py (Sprint 125) validates YAML frontmatter but only for SPEC-*.md files.

---

## Deliverables

### S224-01: Extend spec_frontmatter.py Scope (~60 LOC)

- **MODIFY**: `backend/sdlcctl/sdlcctl/validation/validators/spec_frontmatter.py`
- **CTO Revision 1**: Reuse existing validator, don't create new yaml_validator.py
- Extend scope from SPEC-*.md only → all SDLC artifacts (ADR-*.md, FR-*.md, TP-*.md, etc.)
- Add per-document-type required fields configuration
- Maintain backward compatibility with existing SPEC validation

### S224-02: _validate_output() in auto_generator.py (~120 LOC)

- **MODIFY**: `backend/app/services/governance/auto_generator.py`
- Add `_validate_output(content: str, artifact_type: str) -> OutputValidation` method
- Checks:
  - Section completeness (does ADR have Problem/Decision/Consequences?)
  - Word count minimums per section (>20 words, not just headings)
  - YAML frontmatter presence and required fields (delegates to spec_frontmatter logic)
  - Placeholder detection (reuses placeholder_detector.py from S223)
- Returns `OutputValidation(score: float, issues: list[str], has_placeholders: bool)`

### S224-03: Placeholder Detection + Word Count Integration (~60 LOC)

- **MODIFY**: `backend/app/services/governance/auto_generator.py`
- Import and use `placeholder_detector.py` from S223-06
- Add word count analysis per section
- Flag sections with <20 words as "thin content"
- **CTO Revision 4**: score calibration based on actual output analysis

### S224-04: Computed Confidence Scoring (~80 LOC)

- **MODIFY**: `backend/app/services/governance/auto_generator.py`
- Replace hardcoded confidence scores (85/60/30) with computed scores
- Formula: `base_score * section_completeness * (1 - placeholder_penalty) * word_count_factor`
  - `base_score`: LLM=0.85, Template=0.60, Minimal=0.30 (starting point)
  - `section_completeness`: ratio of required sections found (0.0 - 1.0)
  - `placeholder_penalty`: 0.1 per placeholder found (max 0.5)
  - `word_count_factor`: min(total_words / expected_words, 1.0)
- Log computed vs old hardcoded score for comparison during rollout

### S224-05: Tests (~300 LOC)

- **NEW file**: `backend/tests/unit/test_sprint224_autogen_quality.py`
- ~15 test cases:
  - spec_frontmatter extended: ADR-*.md validates correctly
  - spec_frontmatter extended: SPEC-*.md still works (backward compat)
  - `_validate_output`: complete ADR → high score
  - `_validate_output`: ADR missing "Consequences" → reduced score
  - `_validate_output`: document with `[TODO]` → placeholder penalty applied
  - `_validate_output`: document with <20 word sections → thin content warning
  - `_validate_output`: YAML frontmatter missing → issue reported
  - Computed confidence: LLM with good output → score > 0.8
  - Computed confidence: Template with missing sections → score < 0.5
  - Computed confidence: Minimal with placeholders → score < 0.25
  - Computed confidence: score logged alongside old hardcoded value
  - Placeholder detector integration: reuses S223 utility correctly
  - End-to-end: `auto_generator._generate_with_llm` → validate → computed score

---

## Key Files

| File | Action |
|------|--------|
| `backend/sdlcctl/sdlcctl/validation/validators/spec_frontmatter.py` | MODIFY |
| `backend/app/services/governance/auto_generator.py` | MODIFY |
| `backend/app/utils/placeholder_detector.py` | REUSE from S223 |
| `backend/app/services/governance/content_validator.py` | REUSE from S223 |
| `backend/tests/unit/test_sprint224_autogen_quality.py` | NEW |

---

## Dependencies

- **Upstream**: S223 complete (placeholder_detector.py, content_validator.py)
- Can run parallel with other non-dependent sprints after S223

---

## Verification

1. Run extended spec_frontmatter on ADR-*.md → validates frontmatter
2. Run extended spec_frontmatter on SPEC-*.md → still works (backward compat)
3. Auto-generate artifact with LLM → computed score differs from hardcoded 85
4. Auto-generate with Minimal fallback → flag `[Auto-generation failed]` placeholder
5. Compare LLM vs Template vs Minimal outputs → computed scores correctly ordered
6. All existing tests pass (regression)

---

## Estimated LOC: ~750 (CTO Revision 4 adjusted)

## Test Target: +15 tests → cumulative ~323+
