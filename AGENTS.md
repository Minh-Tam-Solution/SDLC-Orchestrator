# AGENTS.md - SDLC-Orchestrator

Context for AI coding assistants (Cursor, Claude Code, Copilot).

Keep ≤150 lines. Dynamic context belongs in PR comments.

## Quick Start

- `docker compose up -d`
- Backend dev: `make dev-backend` (or `cd backend && uvicorn app.main:app --reload`)
- Frontend dev: `cd frontend && npm run dev`

## Architecture

- Backend: FastAPI (Python)
- Frontend: Next.js App Router (TypeScript)
- Services: Postgres, Redis, MinIO, OPA, Grafana/Prometheus

## Current Stage

**Sprint 171**: Market Expansion Foundation (Phase 6) — ✅ 90% COMPLETE
- Days 1–4: ✅ complete (i18n infra + Vietnamese UI + VND pricing + `/pilot` landing page)
- Day 5: ⏳ interviews + synthesis pending (docs/workflow complete)

**Key Metrics**
- LOC: ~3,118 / ~2,950 (105.7%)
- Framework: 96.6% → 96.9% (+0.3%)
- Quality Score: 90/100
- Pilot E2E: 10 scenarios (7 pass / 3 skip auth-dependent)

**Sprint 171 Docs (canonical)**
- Report: docs/04-build/02-Sprint-Plans/SPRINT-171-COMPLETION-REPORT.md
- Final steps: docs/04-build/02-Sprint-Plans/SPRINT-171-FINAL-STEPS.md
- Day 5 checklist: docs/04-build/02-Sprint-Plans/SPRINT-171-DAY-5-CHECKLIST.md
- Interview template: docs/04-build/02-Sprint-Plans/SPRINT-171-CUSTOMER-DISCOVERY-TEMPLATE.md

## Common Verification

- Pilot E2E (stable port):
  - `cd frontend && PORT=3010 E2E_BASE_URL=http://localhost:3010 npx playwright test e2e/sprint171-pilot-landing.spec.ts`
- Frontend lint (repo-wide lint currently surfaces pre-existing unused-vars):
  - `cd frontend && npm run lint`

## Notes

- `/pilot` signup handles unauth (401) by redirecting to `/register?redirect=/pilot`.
- Some pilot E2E scenarios remain skipped until an auth/session harness exists.
