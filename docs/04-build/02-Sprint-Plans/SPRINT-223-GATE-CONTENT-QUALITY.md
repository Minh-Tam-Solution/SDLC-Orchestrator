---
sdlc_version: "6.1.1"
document_type: "Sprint Plan"
status: "DRAFT — Pending CTO Approval"
sprint: "223"
tier: "PROFESSIONAL"
stage: "04 - Build"
---

# Sprint 223 — Gate Content Quality + Tier-Artifact Matrix

| Field | Value |
|-------|-------|
| **Sprint Duration** | March 2026 |
| **Sprint Goal** | Close 3 EndiorBot-equivalent gaps — add per-gate artifact requirements by tier, document content quality validation (OPA-first), and wire 2 missing OTT command handlers. |
| **Status** | DRAFT — Pending CTO Approval |
| **Priority** | P0 — Governance Quality Gap (cross-project review finding) |
| **Framework** | SDLC 6.1.1 |
| **ADRs** | ADR-056 (Multi-Agent), ADR-059 (Enterprise-First) |
| **Previous Sprint** | Sprint 222 — OTT @mention Routing |
| **Raised by** | PM + Architect cross-project review vs EndiorBot Sprint 80 gaps (2026-03-06) |
| **CTO Review** | APPROVED 8.5/10 with 4 revisions applied |

---

## Root Cause

EndiorBot Sprint 80 discovered 6 governance gaps. Cross-project review found 5 of 6 have parallels in SDLC Orchestrator. Sprint 223 addresses the 3 HIGH+LOW priority items:

1. **No per-gate artifact requirements by tier** — ENTERPRISE G2 gates accept submissions without Threat Model or Security Baseline, violating SDLC 6.1.1 tier-specific stage requirements.
2. **No document content quality validation** — Evidence uploads accept empty or placeholder-filled documents. A document titled "ADR-099" with `[TODO: fill in later]` passes gate evaluation.
3. **2 OTT command handlers missing dispatch** — `RUN_EVALS` and `LIST_NOTES` commands registered but not wired in `governance_action_handler.py`, causing silent no-ops in Telegram.

---

## Deliverables

### S223-01: Gate Artifact Matrix (~80 LOC)

- **NEW** file: `backend/app/policies/gate_artifact_matrix.py`
- Define `GATE_ARTIFACT_MATRIX: dict[str, dict[str, list[str]]]` mapping `gate_type` -> `tier` -> required artifact types
- Example: `G2` + `ENTERPRISE` -> `["ADR", "THREAT_MODEL", "SECURITY_BASELINE", "TEST_PLAN"]`
- Example: `G1` + `LITE` -> `["BRD"]` (minimal)
- CTO directive: Separate from `tier_policies.py` (separation of concerns)

### S223-02: Tier Artifacts OPA Policy (~60 LOC)

- **NEW** file: `backend/policy-packs/rego/gates/tier_artifacts.rego`
- Rego policy that validates submitted evidence types against the matrix
- Input: `gate_type`, `tier`, `submitted_evidence_types`
- Output: `missing_artifacts` list, `pass`/`fail`

### S223-03: Wire Matrix into Gates Engine (~40 LOC)

- **MODIFY**: `backend/app/services/governance/gates_engine.py`
- Import `gate_artifact_matrix`, add artifact type check as Phase 1.5 (after Prerequisites, before Exit Criteria)
- Return missing artifacts in evaluation result

### S223-04: Content Quality OPA Policy — PRIMARY (~100 LOC)

- **NEW** file: `backend/policy-packs/rego/gates/content_quality.rego`
- OPA-first pattern (CTO Revision 3, following Sprint 156 NISTGovernService)
- Per-document-type section requirements:
  - **ADR**: must have "Problem", "Decision", "Consequences" sections
  - **Test Plan**: must have "Test Cases", "Coverage" sections
  - **Threat Model**: must have "Threats", "Mitigations" sections
  - **Security Baseline**: must have "Controls", "Compliance" sections
- Word count minimum per section (>20 words, not just a heading)
- Placeholder detection via regex patterns

### S223-05: Content Validator In-Process Fallback (~300 LOC)

- **NEW** file: `backend/app/services/governance/content_validator.py`
- CTO Revision 3: Only fires if OPA is unreachable
- CTO Revision 4: ~300 LOC (ADR/TestPlan/SecurityBaseline each need different section schemas)
- Same logic as `content_quality.rego` but in Python
- Returns `ContentValidationResult` with `score`, `missing_sections`, `placeholder_warnings`

### S223-06: Placeholder Detector (~50 LOC)

- **NEW** file: `backend/app/utils/placeholder_detector.py`
- Shared utility reused by `content_validator.py` and `auto_generator.py` (S224)
- Regex patterns: `\[.*TODO.*\]`, `\[.*TBD.*\]`, `\[.*please.*\]`, `\[.*implement.*\]`, `\[Auto-generation.*\]`
- Returns list of `PlaceholderMatch(line_number, pattern, text)`

### S223-07: Content Validation API Endpoint (~40 LOC)

- **MODIFY**: `backend/app/api/routes/evidence.py`
- Add `POST /api/v1/evidence/{id}/validate-content` endpoint
- OPA callback endpoint (same pattern as `evidence_completeness.rego`)

### S223-08: Hook into Evidence Upload (~30 LOC)

- **MODIFY**: `backend/app/services/evidence_manifest_service.py`
- Call content validation during evidence upload
- Non-blocking: returns quality warnings, does not reject upload

### S223-09: Missing OTT Handlers — Dispatch Only (~60 LOC)

- **MODIFY**: `backend/app/services/agent_bridge/governance_action_handler.py`
- Add `elif` branches for `ToolName.RUN_EVALS` and `ToolName.LIST_NOTES`
- CTO Revision 2: Dispatch-only fix. No changes to `command_registry.py` (`MAX_COMMANDS=10` constraint)
- Route to existing `eval_scorer.run_suite` and `note_service.list_notes`

### S223-10: Tests (~450 LOC)

- **NEW** file: `backend/tests/unit/test_sprint223_gate_content.py`
- ~18 test cases + OPA integration tests (CTO Revision 4):
  - Tier-artifact matrix: ENTERPRISE G2 without Threat Model -> FAIL
  - Tier-artifact matrix: LITE G1 with BRD only -> PASS
  - Content quality (OPA): empty ADR -> missing sections list
  - Content quality (OPA): complete ADR -> PASS
  - Content quality (fallback): OPA unreachable -> Python fallback fires
  - Placeholder detection: `[TODO]` detected -> warning
  - Placeholder detection: clean document -> no warnings
  - Evidence upload: content warnings included in response
  - OTT handler: "run evals" dispatched correctly
  - OTT handler: "list notes" dispatched correctly
  - Registry unchanged: `MAX_COMMANDS` still 10

---

## Key Files

| File | Action |
|------|--------|
| `backend/app/policies/gate_artifact_matrix.py` | NEW |
| `backend/policy-packs/rego/gates/tier_artifacts.rego` | NEW |
| `backend/policy-packs/rego/gates/content_quality.rego` | NEW |
| `backend/app/services/governance/content_validator.py` | NEW |
| `backend/app/utils/placeholder_detector.py` | NEW |
| `backend/app/services/governance/gates_engine.py` | MODIFY |
| `backend/app/services/evidence_manifest_service.py` | MODIFY |
| `backend/app/api/routes/evidence.py` | MODIFY |
| `backend/app/services/agent_bridge/governance_action_handler.py` | MODIFY |
| `backend/tests/unit/test_sprint223_gate_content.py` | NEW |

---

## Dependencies

- **Upstream**: S222 complete (OTT @mention routing)
- **Downstream**: S224 (Auto-Gen Quality Gates) reuses `placeholder_detector.py` and `content_validator.py`

---

## Verification

1. ENTERPRISE project, G2 gate without Threat Model -> evaluation FAILS with missing artifact list
2. Upload empty ADR -> `content_quality.rego` returns missing sections
3. Disconnect OPA -> Python fallback catches same violation
4. `[Auto-generation failed]` in document -> placeholder warning
5. "run evals" in Telegram -> gets response
6. `command_registry.py` unchanged (`MAX_COMMANDS=10`)
7. All existing tests pass (regression)

---

## Estimated LOC: ~1050

## Test Target: +18 tests -> cumulative ~308+
