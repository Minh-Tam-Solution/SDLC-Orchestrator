# Sprint 201 — Self-Hosted Pilot: SDLC Orchestrator Manages Itself

**Sprint Duration**: April 7 – April 18, 2026 (10 working days)
**Sprint Goal**: Achieve 100% dogfooding — use SDLC Orchestrator to govern its own development lifecycle via OTT chat, including sprint planning, gate approvals, evidence submission, and code generation
**Status**: CLOSED (CTO 9.3/10) — Track A ✅, Track B ✅, Track C ✅, Track D ✅ (40/40 tests, 0 regressions)
**Priority**: P0 (Full Dogfooding + SME Pilot Readiness)
**Framework**: SDLC 6.1.1
**CTO Score (Sprint 200)**: TBD
**Previous Sprint**: [Sprint 200 — Full Agent Team Orchestration via OTT](SPRINT-200-AGENT-TEAM-OTT.md)

---

## Sprint 201 Goal

Sprint 200 activates multi-agent orchestration via OTT (90% dogfooding). Sprint 201 is the **final step**: SDLC Orchestrator manages its own development — sprint governance, quality gates, evidence collection, and code generation all flow through the platform's own OTT channels.

**Dogfooding level**: 90% → 100% — the platform governs itself.

**CEO Vision**: "If we can't use our own product to ship our own product, we're not ready for customers."

**Three pillars**:
1. **Self-Governance** — Sprint 201 planned, executed, and closed using SDLC Orchestrator
2. **SME Pilot Readiness** — 5 founding customers can replicate our workflow
3. **Production Hardening** — Edge cases discovered during self-governance fixed in real-time

**Milestone**: After Sprint 201, SDLC Orchestrator is **customer-ready** for the Vietnam SME Pilot (5 founding customers).

---

## Sprint 201 Backlog

### Track A — Self-Governance Setup (Day 1-3) — @pm

**Goal**: Configure SDLC Orchestrator to manage the `SDLC-Orchestrator` project itself — create project, define gates, configure agent team, and run Sprint 201 governance entirely through OTT chat.

| ID | Item | Priority | Deliverable |
|----|------|----------|-------------|
| A-01 | Register `sdlc-orchestrator` as a project in the platform | P0 | Real project entity with GitHub repo link, team members, tier=ENTERPRISE |
| A-02 | Define Sprint 201 gates via chat | P0 | G-Sprint gate created: `/create_gate sprint_201 G_SPRINT` via Telegram |
| A-03 | Configure Coder Team preset for Python/FastAPI | P1 | Agent team preset tuned for backend Python codegen (qwen3-coder:30b) |
| A-04 | Sprint 201 CURRENT-SPRINT.md generated via platform | P0 | `SprintFileService.generate()` produces this sprint doc from OTT input |
| A-05 | Invite team members via OTT | P1 | "invite @dev1 to sdlc-orchestrator" → invitation sent via Telegram |
| A-06 | Configure OTT notification preferences | P2 | Gate evaluation results → auto-notify on Telegram group |

**Self-governance verification**: Sprint 201 plan itself was created using Sprint 200's agent team. If this sprint plan was NOT generated via the platform, document why and fix the gap.

**Acceptance criteria**:
- [ ] `sdlc-orchestrator` project exists in platform DB with real metadata
- [ ] G-Sprint gate for Sprint 201 created via chat command
- [ ] Team members invited and confirmed via OTT
- [ ] CURRENT-SPRINT.md reflects Sprint 201 (platform-generated, not manually written)

---

### Track B — Self-Governance Execution (Day 3-8) — @pm + @dev

**Goal**: Execute Sprint 201 feature work using SDLC Orchestrator's own agent team, evidence upload, and gate evaluation — proving the full governance loop works end-to-end.

| ID | Item | Priority | Deliverable |
|----|------|----------|-------------|
| B-01 | Code generation via OTT: "generate health check endpoint" | P0 | Use Coder Team via Telegram → generate `/api/v1/health` enhanced endpoint |
| B-02 | Evidence upload via OTT: upload test results | P0 | Upload pytest report via Telegram → Evidence Vault with SHA256 |
| B-03 | Gate evaluation via chat: evaluate G-Sprint | P0 | "evaluate sprint 201 gate" → OPA policy check → result to Telegram |
| B-04 | Gate approval via chat: approve G-Sprint | P0 | "approve gate X" → Magic Link → approved → notification |
| B-05 | Sprint close via chat: close Sprint 201 | P0 | "close sprint 201" → G-Sprint-Close checklist → documentation generated |
| B-06 | Audit export via chat: export Sprint 201 audit | P1 | "export audit sdlc-orchestrator" → compliance PDF generated |

**Self-governance loop**:
```
Day 3: Create sprint gate via chat (A-02)
Day 4: Generate code via agent team (B-01)
Day 5: Upload evidence via Telegram (B-02)
Day 6: Evaluate gate via chat (B-03)
Day 7: Approve gate via Magic Link (B-04)
Day 8: Close sprint via chat (B-05) + export audit (B-06)
```

**Acceptance criteria**:
- [ ] At least 1 real code generation task executed via agent team
- [ ] At least 1 real evidence uploaded via OTT (not mock data)
- [ ] Gate evaluated and approved via OTT (not web dashboard)
- [ ] Sprint close checklist auto-generated from platform data
- [ ] Audit trail shows complete governance loop: create → evaluate → approve → close

---

### Track C — SME Pilot Readiness (Day 5-8) — @pm

**Goal**: Prepare onboarding materials and validate that the 5 founding SME customers can replicate our self-governance workflow.

| ID | Item | Priority | Deliverable |
|----|------|----------|-------------|
| C-01 | SME Onboarding Playbook (Vietnamese) | P0 | Step-by-step guide: Telegram setup → project creation → first gate → first evidence |
| C-02 | 3-minute video walkthrough | P1 | Screen recording of self-governance loop (A-01 through B-06) |
| C-03 | Pilot environment provisioning script | P1 | Docker Compose + `.env.example` for SME self-hosted deployment |
| C-04 | Tier configuration validation | P1 | LITE/STANDARD/PRO/ENTERPRISE limits tested with real OTT usage |
| C-05 | Vietnamese domain template demo | P2 | E-commerce template generation via Telegram (show EP-06 codegen) |

**Target**: 5 founding customers from Vietnam SME Pilot Program:
1. Series B fintech (SOC2 compliance)
2. E-commerce platform (Vietnamese market)
3. HRM SaaS (HR management system)
4. Healthcare startup (regulatory compliance)
5. EdTech platform (learning management)

**Acceptance criteria**:
- [ ] SME Onboarding Playbook: <30 min time-to-first-gate-evaluation (MTEP target)
- [ ] Pilot environment: `docker compose up` → working platform in <10 min
- [ ] All 4 tiers tested with OTT tier gating enforced
- [ ] Vietnamese domain template generates valid code via Telegram

---

### Track D — Production Hardening + Sprint Close (Day 8-10) — @pm

**Goal**: Fix edge cases discovered during self-governance execution and prepare for SME pilot launch.

| ID | Item | Priority | Deliverable |
|----|------|----------|-------------|
| D-01 | Fix all bugs discovered during self-governance (Track B) | P0 | Real bugs found by using the platform |
| D-02 | Performance tuning: agent pipeline < 30s for simple tasks | P1 | Optimize prompt templates, model selection, caching |
| D-03 | Error message improvement | P1 | All user-facing errors in Vietnamese with actionable guidance |
| D-04 | Regression test suite (800+ tests) | P0 | All Sprint 197-200 tests passing + Sprint 201 new tests |
| D-05 | Dogfooding report: 100% level verification | P0 | Document all governance actions completed via OTT |
| D-06 | SME Pilot Launch readiness checklist | P0 | Go/No-Go decision for 5 founding customers |
| D-07 | Sprint 201 close documentation | P1 | G-Sprint-Close within 24h — ideally via OTT itself |

---

## Architecture: Self-Governance Loop

### Full Dogfooding Verification Matrix

| Governance Action | Interface | Sprint Available | Sprint 201 Self-Test |
|------------------|-----------|-----------------|---------------------|
| Create project | OTT chat | 199 | A-01 |
| Create sprint gate | OTT chat | 199 | A-02 |
| Generate CURRENT-SPRINT.md | Platform API | 193 | A-04 |
| Generate code | OTT agent team | 200 | B-01 |
| Upload evidence | OTT file attachment | 199 | B-02 |
| Evaluate gate | OTT chat | 199 | B-03 |
| Approve gate (Magic Link) | OTT + web callback | 199 | B-04 |
| Close sprint | OTT chat | 201 (NEW) | B-05 |
| Export audit | OTT chat | 199 | B-06 |
| Invite team member | OTT chat | 201 (NEW) | A-05 |
| Budget monitoring | Gateway Dashboard | 200 | Verified |
| Channel health | Gateway Dashboard | 198 | Verified |

### Dogfooding Progression (Final Summary)

```
Sprint 197: ██████████░░░░░░░░░░░░░░░  40% — Manual + auto-verify
Sprint 198: ███████████████░░░░░░░░░░░  60% — Bidirectional AI conversation
Sprint 199: ██████████████████░░░░░░░░  75% — Governance actions via chat
Sprint 200: ██████████████████████░░░░  90% — Multi-agent orchestration
Sprint 201: █████████████████████████  100% — Self-hosted, self-governed
```

### SME Pilot Architecture

```
┌──────────────────────────────────────────────────────────┐
│                    SME Customer Environment               │
│                                                          │
│  ┌─────────┐    ┌─────────────────┐    ┌──────────────┐ │
│  │Telegram │───>│ SDLC Orchestrator│───>│   Ollama     │ │
│  │  Bot    │    │   (Docker)       │    │  (Local GPU) │ │
│  └─────────┘    │                  │    └──────────────┘ │
│                  │  ┌────────────┐ │                      │
│  ┌─────────┐    │  │ PostgreSQL │ │    ┌──────────────┐ │
│  │  Zalo   │───>│  │   Redis    │ │───>│   MinIO S3   │ │
│  │  OA     │    │  │    OPA     │ │    │ (Evidence)   │ │
│  └─────────┘    │  └────────────┘ │    └──────────────┘ │
│                  └─────────────────┘                      │
│                                                          │
│  Tier: STANDARD ($99/mo) or PRO ($299/mo)               │
│  Channels: Telegram + Zalo (Vietnam market)              │
│  AI: qwen3:32b (Vietnamese) on customer's GPU           │
└──────────────────────────────────────────────────────────┘
```

---

## Files Summary

| File | Action | LOC | Track |
|------|--------|-----|-------|
| `backend/app/services/agent_bridge/sprint_governance_handler.py` | NEW | ~200 | B (sprint close via chat) |
| `backend/app/services/agent_bridge/team_invite_handler.py` | NEW | ~100 | A (invite via OTT) |
| `backend/app/services/agent_team/command_registry.py` | MODIFY | ~40 | B (add close_sprint, invite_member commands) |
| `docs/pilot/SME-ONBOARDING-PLAYBOOK.md` | NEW | ~300 | C |
| `docker/pilot/docker-compose.pilot.yml` | NEW | ~100 | C (pilot environment) |
| `docker/pilot/.env.example` | NEW | ~50 | C |
| Tests (unit + integration + E2E + dogfooding) | NEW | ~500 | D |
| **Total** | | **~1,290** | |

---

## Sprint 201 Success Criteria

**Hard criteria (8)**:
- [ ] `sdlc-orchestrator` project created and governed via OTT
- [ ] At least 1 code generation task completed via agent team from chat
- [ ] At least 1 evidence uploaded via Telegram file attachment
- [ ] Gate evaluated and approved via OTT (Magic Link)
- [ ] Sprint 201 G-Sprint-Close executed via chat command
- [ ] SME Onboarding Playbook: <30 min to first gate evaluation
- [ ] Pilot environment: `docker compose up` → working in <10 min
- [ ] 800+ test suite green, 0 regressions

**Stretch criteria (3)**:
- [ ] Sprint close documentation generated entirely via platform (not manual)
- [ ] 3-minute video walkthrough recorded
- [ ] All 5 SME pilot customers onboarded to staging environment

---

## Risk Assessment

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| Self-governance discovers critical bugs | P0 — sprint blocked | Medium | Fix in real-time (Track D-01), this is the point of dogfooding |
| SME onboarding > 30 min | P1 — MTEP target missed | Medium | Simplify wizard, pre-configured templates, video walkthrough |
| Pilot environment too complex to deploy | P1 — customer friction | Low | Single `docker compose up`, pre-built images on registry |
| Vietnamese AI quality insufficient for SME | P1 — customer churn | Low | qwen3:32b tested excellent; fallback to Claude for complex queries |
| Budget circuit breaker too restrictive for pilot | P2 — feature limitation | Low | Generous pilot limits (ENTERPRISE tier for 30 days trial) |

---

## Dependencies

- **Sprint 200 complete**: Multi-agent orchestration via OTT must be production-stable
- **All 5 command_registry tools wired**: create_project, gate_status, submit_evidence, approve_gate, export_audit
- **SME Pilot list**: 5 founding customers confirmed and ready for onboarding
- **Docker registry**: Pre-built images published for pilot deployment
- **Ollama model availability**: Customers need RTX 3090+ or cloud GPU for qwen3:32b

---

## Post-Sprint 201: What's Next

```yaml
Sprint 202-205: Vietnam SME Pilot Execution
  - 5 customers onboarded and actively using platform
  - Weekly feedback sessions → product iterations
  - Usage metrics: DAU, governance actions/day, codegen requests/day
  - Revenue: First MRR from STANDARD/PRO subscriptions

Sprint 206-210: Scale + Enterprise Features
  - Multi-region deployment (Vietnam + Singapore)
  - SAML SSO integration for enterprise customers
  - Advanced agent teams (custom pipelines)
  - Marketplace: community agent templates

Sprint 211+: Platform Maturity
  - 100+ active teams
  - $50K MRR target
  - SOC2 Type II certification
  - SDLC Framework 7.0 integration
```

---

**Last Updated**: February 23, 2026
**Created By**: PM + AI Development Partner — Sprint 201 Planning
**Framework Version**: SDLC 6.1.1
**Previous State**: Sprint 200 PLANNED
