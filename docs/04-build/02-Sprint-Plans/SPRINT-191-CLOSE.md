# Sprint 191 Close — Unified Command Registry + Post-Cleanup Stabilization

**Sprint**: 191
**Duration**: 8 working days
**Status**: COMPLETE
**Framework**: SDLC 6.1.0
**Preceded by**: Sprint 190 (Aggressive Cleanup, CTO 9.1/10)

---

## Deliverables Summary

| # | Deliverable | Status | LOC |
|---|-------------|--------|-----|
| 1 | Unified Command Registry (`command_registry.py`) | DONE | ~200 |
| 2 | OTT adapter refactored (`chat_command_router.py`) | DONE | -180 (net reduction) |
| 3 | CLI governance adapter (`governance.py`) | DONE | ~170 |
| 4 | SASE thin adapter (`sase_adapter.py`) | DONE | ~20 |
| 5 | 410 stub removal (`deprecated_routes.py` deleted) | DONE | -72 |
| 6 | Requirements split (`core.txt`, `enterprise.txt`, `dev.txt`) | DONE | ~400 (restructured) |
| 7 | Enterprise channel parity (Teams, Slack, Zalo fixes) | DONE | ~10 |
| 8 | Acceptance tests (`test_command_registry.py`) | DONE | ~180 |
| 9 | Sprint 190 smoke test update | DONE | -30 (removed deprecated tests) |

**Net code change**: ~+370 LOC new, ~-280 LOC removed

---

## Verification Criteria

| # | Criterion | Result |
|---|-----------|--------|
| 1 | Registry defines 5 commands | PASS — `get_commands()` returns 5 |
| 2 | OTT reads from registry | PASS — `chat_command_router.py` has no hardcoded `OLLAMA_TOOLS` |
| 3 | CLI reads from registry | PASS — `sdlcctl/commands/governance.py` imports registry schemas |
| 4 | SASE decoupled | PASS — `from app.services.sase_adapter import create_sase_generation_service` works |
| 5 | 410 stubs removed | PASS — `deprecated_routes.py` deleted, `main.py` cleaned |
| 6 | Requirements split | PASS — `requirements/core.txt` valid, includes FastAPI + SQLAlchemy |
| 7 | `ruff check` | PASS — 0 errors on all Sprint 191 files |
| 8 | Backend startup | PASS — 579 routes loaded |
| 9 | Sprint 190 smoke tests | PASS — 7/7 (3 deprecated router tests removed) |
| 10 | SASE anti-regression | PASS — 5/5 tests |
| 11 | New acceptance tests | PASS — 14 passed, 1 skipped (CLI not installed) |
| 12 | Channel parity | PASS — Teams `correlation_id` prefixed, sender_id sentinels added |

**Total test results**: 26 passed, 1 skipped, 0 failed

---

## Key Decisions

### D-191-01: Frozen dataclass for CommandDef
Registry uses `@dataclass(frozen=True)` — commands are immutable after definition. Max 10 commands enforced via module-level assert.

### D-191-02: Pydantic models as single source of truth
Pydantic param models (e.g., `CreateProjectParams`) moved to `command_registry.py`. Both CLI and OTT import from this single location. CLI uses manual Typer definitions (not auto-generated) that import the same Pydantic schemas.

### D-191-03: SASE adapter is a re-export, not logic
`sase_adapter.py` is a 20-line re-export facade. No business logic. VCR/CRP import from adapter instead of directly from `sase_generation_service.py`. This enables future SASE refactoring without touching VCR/CRP.

### D-191-04: Requirements split preserves backward compatibility
Original `requirements.txt` now contains `-r requirements/dev.txt` (which includes core + enterprise). Existing `pip install -r requirements.txt` workflows continue to work. Docker uses separate `requirements-docker.txt` (unchanged).

### D-191-05: Channel correlation_id convention
All normalizers now follow `{channel}_{id}` pattern: `telegram_{msg_id}`, `slack_{event_id}`, `zalo_{ts}_{sender}`, `teams_{activity_id}`. Previously Teams was the only outlier using raw activity ID.

---

## Files Changed

### New Files
| File | LOC | Purpose |
|------|-----|---------|
| `backend/app/services/agent_team/command_registry.py` | ~200 | Unified Command Registry (single source of truth) |
| `backend/app/services/sase_adapter.py` | ~20 | SASE thin facade (VCR/CRP decoupling) |
| `backend/sdlcctl/sdlcctl/commands/governance.py` | ~170 | CLI governance adapter (5 Typer commands) |
| `backend/requirements/core.txt` | ~90 | Core production dependencies |
| `backend/requirements/enterprise.txt` | ~140 | Enterprise-only dependencies |
| `backend/requirements/dev.txt` | ~170 | Development + test dependencies |
| `backend/tests/unit/test_command_registry.py` | ~180 | Sprint 191 acceptance tests |

### Modified Files
| File | Change |
|------|--------|
| `backend/app/services/agent_team/chat_command_router.py` | Import from registry, remove hardcoded defs |
| `backend/app/services/agent_team/__init__.py` | Re-export from registry |
| `backend/sdlcctl/sdlcctl/cli.py` | Register governance sub-app |
| `backend/app/services/vcr_service.py` | Import from sase_adapter (line 655) |
| `backend/app/services/crp_service.py` | Import from sase_adapter (line 496) |
| `backend/app/main.py` | Remove deprecated_routes registration |
| `backend/app/services/agent_bridge/teams_normalizer.py` | Add `teams_` correlation_id prefix |
| `backend/app/services/agent_bridge/slack_normalizer.py` | Named sender_id sentinel (`slack_bot`) |
| `backend/app/services/agent_bridge/zalo_normalizer.py` | Named sender_id sentinel (`zalo_unknown`) |
| `backend/requirements.txt` | Redirect to `requirements/dev.txt` |
| `backend/tests/quick-tests/test_sprint190_smoke.py` | Remove deprecated router tests |

### Deleted Files
| File | Reason |
|------|--------|
| `backend/app/api/routes/deprecated_routes.py` | 1-sprint 410 grace period expired |

---

## Risks Mitigated

| Risk | Outcome |
|------|---------|
| Registry abstraction over-engineered | Kept to 200 LOC, frozen dataclass, max 10 guard |
| SASE refactor breaks VCR/CRP | 5/5 anti-regression tests pass; adapter is re-export only |
| Requirements split breaks builds | Original `requirements.txt` preserved as redirect |
| CLI Typer generation complexity | Used manual Typer defs + shared Pydantic schemas |
| Enterprise channel normalizer gaps | 3 conformance fixes applied and verified |

---

## Sprint 192 Recommendations

1. **sdlcctl governance end-to-end test** — currently CLI tests skip (separate package). Add CI step that installs sdlcctl and runs parity verification.
2. **Zalo HMAC signature verification** — only Telegram (upstream) and Teams/Slack have HMAC. Zalo webhook lacks server-side verification.
3. **Requirements: Docker image optimization** — consider multi-stage build using only `core.txt` for production image (exclude enterprise/dev deps).
4. **SASE service refactor** — now that VCR/CRP are decoupled via adapter, the full `sase_generation_service.py` can be safely refactored or split.

---

**Sprint 191 Status**: COMPLETE
**Ready for CTO Review**: YES
**GO/NO-GO for Sprint 192**: Recommend GO
