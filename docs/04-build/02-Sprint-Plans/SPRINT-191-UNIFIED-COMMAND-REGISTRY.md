---
sdlc_version: "6.1.0"
document_type: "Sprint Plan"
status: "PROPOSED"
sprint: "191"
spec_id: "SPRINT-191"
tier: "ALL"
stage: "04 - Build"
---

# SPRINT-191 — Unified Command Registry + Post-Cleanup Stabilization

**Status**: PROPOSED (pending CTO approval)
**Sprint Duration**: 8 working days
**Sprint Goal**: Unify CLI and OTT command definitions into a shared registry; stabilize codebase after Sprint 190 cleanup
**Epic**: EP-08 Chat-First Governance Loop (P2 — Enterprise Hardening)
**ADR**: ADR-064 (Option D+)
**Dependencies**: Sprint 190 complete (Aggressive Cleanup ~21K LOC)
**Budget**: ~$5,120 (64 hrs at $80/hr)

---

## 1. Sprint Goal

Sprint 191 delivers the **Unified Command Registry** — a shared command definition layer that ensures CLI (`sdlcctl`) and OTT channels execute identical governance commands from the same source of truth. Also stabilizes the codebase after Sprint 190's ~21K LOC deletion and addresses deferred items.

**CEO Direction**: "CLI and OTT share the same commands. No feature parity drift."

**Design References**:
- **OpenClaw** (`/home/nqh/shared/openclaw`): 56 skills, declarative SKILL.md registration, `commands-registry.data.ts`, 7-channel abstraction, per-channel command name overrides
- **TinySDLC** (`/home/nqh/shared/tinysdlc`): In-chat regex commands, @mention routing, plugin-based channel architecture

---

## 2. Deliverables

| # | Deliverable | Description | LOC | Sprint Day |
|---|------------|-------------|-----|------------|
| 1 | `command_registry.py` | Shared command definitions (5 commands, Pydantic schemas, permission matrix) | ~200 | Day 1-2 |
| 2 | CLI adapter | `sdlcctl` commands generated from registry (replaces manual Typer definitions) | ~150 | Day 3 |
| 3 | OTT adapter | `chat_command_router.py` reads from registry (replaces hardcoded tool list) | ~50 | Day 3 |
| 4 | SASE import refactor | Decouple `sase_generation_service.py` from VCR/CRP (Sprint 190 deferred blocker) | ~80 | Day 4 |
| 5 | HTTP 410 stubs removal | Remove `deprecated_routes.py` stubs (Sprint 190 created them as temporary) | ~50 | Day 5 |
| 6 | requirements.txt split | Split 398-line requirements into core (~80) + enterprise (~120) + dev (~200) | ~0 | Day 5 |
| 7 | Enterprise channel parity | MS Teams + Slack normalizers verified against Telegram baseline | ~100 | Day 6 |
| 8 | Acceptance tests | Registry roundtrip, CLI parity, OTT parity, SASE anti-regression | ~200 | Day 7 |
| 9 | Sprint close | SPRINT-191-CLOSE.md + CTO review | — | Day 8 |

---

## 3. Daily Schedule

### Day 1-2: Unified Command Registry

**Goal**: Create shared command definition layer

**New File**: `backend/app/services/agent_team/command_registry.py` (~200 LOC)

**Design** (OpenClaw-inspired):
```python
# Declarative command definitions — single source of truth
GOVERNANCE_COMMANDS = [
    CommandDef(
        name="gate_status",
        description="Show gate status for a project",
        params=GetGateStatusParams,
        permission="governance:read",
        handler="gate_service.get_gate_status",
        cli_name="gate status",        # sdlcctl gate status
        ott_aliases=["gate status", "trạng thái gate"],  # Vietnamese
    ),
    CommandDef(
        name="create_project",
        description="Create a new project",
        params=CreateProjectParams,
        permission="projects:write",
        handler="project_service.create_project",
        cli_name="project create",
        ott_aliases=["tạo dự án", "create project"],
    ),
    # ... 5 governance commands total
]
```

**Constraints**:
- Maximum 10 commands in registry (prevent unbounded growth — Expert 9 correction)
- Each command MUST have: name, params (Pydantic), permission, handler, cli_name, ott_aliases
- Permission matrix reuses existing RBAC scopes (`governance:read`, `governance:write`, `governance:approve`)

### Day 3: CLI + OTT Adapters

**Goal**: Both interfaces read from the same registry

**Modified File**: `backend/sdlcctl/commands/governance.py`
- Replace manual Typer command definitions with registry-driven generation
- Each `CommandDef` generates a Typer command with correct params and help text

**Modified File**: `backend/app/services/agent_team/chat_command_router.py`
- Replace hardcoded `OLLAMA_TOOLS` list with registry-generated tool schemas
- Tool schemas auto-generated from `CommandDef.params` Pydantic models

### Day 4: SASE Import Refactor (Sprint 190 Deferred Blocker)

**Goal**: Decouple `sase_generation_service.py` from VCR/CRP

**Problem**: `vcr_service.py` (line 655) and `crp_service.py` (line 496) import `create_sase_generation_service`. This blocked deletion in Sprint 190.

**Solution**: Extract shared interface into thin adapter
- Create `backend/app/services/sase_adapter.py` (~30 LOC) — facade with `create_sase_generation_service()` function
- VCR/CRP import from adapter instead of full SASE service
- SASE service can now be safely moved/refactored independently

**Verification**: Run SASE anti-regression test from Sprint 190 (Day 7 smoke test)

### Day 5: 410 Stub Removal + Requirements Split

**Goal**: Clean up Sprint 190 temporary artifacts

**410 Removal**:
- Delete `backend/app/api/routes/deprecated_routes.py` (Sprint 190 Day 4 artifact)
- Remove `deprecated_routes.router` from `main.py`
- All deleted endpoints now return FastAPI's default 404 (no 410 needed after 1 sprint grace period)

**Requirements Split**:
- `requirements.txt` (~398 lines) → `requirements/core.txt` (~80), `requirements/enterprise.txt` (~120), `requirements/dev.txt` (~200)
- `Dockerfile` updated to `pip install -r requirements/core.txt -r requirements/enterprise.txt`
- Dev: `pip install -r requirements/dev.txt` (includes core + enterprise + test deps)

### Day 6: Enterprise Channel Parity

**Goal**: Verify MS Teams and Slack normalizers match Telegram baseline

**Test Matrix**:

| Command | Telegram | MS Teams | Slack | Expected |
|---------|----------|----------|-------|----------|
| `gate status #123` | ✅ | Verify | Verify | GetGateStatusParams(project_id=123) |
| `create project Bflow` | ✅ | Verify | Verify | CreateProjectParams(name="Bflow") |
| `approve G2 #123` | ✅ | Verify | Verify | RequestApprovalParams(gate_id=..., action="approve") |
| `submit evidence #123` | ✅ | Verify | Verify | SubmitEvidenceParams(gate_id=...) |
| `export audit #123` | ✅ | Verify | Verify | ExportAuditParams(project_id=123) |

**Files**: Verify `backend/app/services/agent_bridge/` normalizers (telegram, ms_teams, slack, zalo)

### Day 7: Acceptance Tests

| # | Test | Pass Criteria |
|---|------|---------------|
| 1 | Registry roundtrip | `command_registry.get_commands()` returns 5 commands, each with all required fields |
| 2 | CLI parity | `sdlcctl gate status` and `chat "gate status"` call same handler |
| 3 | OTT parity | All 5 commands work via Telegram + at least 1 enterprise channel |
| 4 | SASE anti-regression | `from app.services.sase_adapter import create_sase_generation_service` works |
| 5 | Requirements split | `pip install -r requirements/core.txt` succeeds without enterprise deps |
| 6 | Vietnamese aliases | `tạo dự án Bflow` → `CreateProjectParams(name="Bflow")` via OTT |

**Test File**: `backend/tests/unit/test_command_registry.py`

### Day 8: Sprint Close + CTO Review

- SPRINT-191-CLOSE.md with metrics
- CTO review of command_registry.py + SASE adapter
- GO/NO-GO for Sprint 192 (enterprise hardening)

---

## 4. New Files

| File | LOC | Purpose |
|------|-----|---------|
| `backend/app/services/agent_team/command_registry.py` | ~200 | Shared command definitions (CLI + OTT) |
| `backend/app/services/sase_adapter.py` | ~30 | Thin facade for SASE generation (decouple VCR/CRP) |
| `requirements/core.txt` | ~80 | Core production dependencies |
| `requirements/enterprise.txt` | ~120 | Enterprise-only dependencies (reportlab, saml2, etc.) |
| `requirements/dev.txt` | ~200 | Development + test dependencies |

## 5. Modified Files

| File | Change | LOC |
|------|--------|-----|
| `backend/app/services/agent_team/chat_command_router.py` | Read tools from registry instead of hardcoded list | ~30 |
| `backend/sdlcctl/commands/governance.py` | Generate Typer commands from registry | ~50 |
| `backend/app/services/vcr_service.py` | Import from `sase_adapter` instead of `sase_generation_service` | ~5 |
| `backend/app/services/crp_service.py` | Import from `sase_adapter` instead of `sase_generation_service` | ~5 |
| `backend/app/main.py` | Remove `deprecated_routes.router` | ~5 |
| `Dockerfile` | Use split requirements | ~5 |

---

## 6. Risk Register

| Risk | Probability | Impact | Mitigation | Day |
|------|-------------|--------|------------|-----|
| Registry abstraction over-engineered | MEDIUM | LOW | Limit to 10 commands max, no plugin system | 1-2 |
| SASE refactor breaks VCR/CRP | LOW | HIGH | Anti-regression test before + after | 4 |
| Requirements split breaks Docker build | LOW | MEDIUM | Test Dockerfile build in CI before merge | 5 |
| Enterprise channel normalizer gaps | MEDIUM | MEDIUM | Manual test matrix Day 6, fallback to Telegram-only | 6 |
| CLI Typer generation complexity | LOW | LOW | If complex, keep manual definitions, just share Pydantic schemas | 3 |

---

## 7. Definition of Done

- [ ] `command_registry.py` defines 5 governance commands with all required fields
- [ ] CLI and OTT both consume from the same registry
- [ ] SASE adapter decouples VCR/CRP from SASE generation service
- [ ] `deprecated_routes.py` (Sprint 190 artifact) removed
- [ ] `requirements.txt` split into core/enterprise/dev
- [ ] All 6 acceptance tests pass
- [ ] `ruff check backend/` → 0 errors
- [ ] `python -c "import backend.app.main"` → clean startup
- [ ] CTO code review APPROVED
- [ ] SPRINT-191-CLOSE.md created

---

## 8. Deferred to Sprint 192+

| Item | Reason | Sprint |
|------|--------|--------|
| SSO + Magic Link integration | Requires enterprise SSO testing | 192 |
| Agent workflow chain (multi-step) | Needs design review | 192 |
| GitHub evidence auto-capture | Nice-to-have, not blocking | 192 |
| Dashboard read-only mode for non-admin | Frontend work | 192 |
| Break-glass web approve | Edge case for admin | 192 |
| Vietnamese NLP expansion (>10 commands) | Scale after baseline proven | 193+ |
