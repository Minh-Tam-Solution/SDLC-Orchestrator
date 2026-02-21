# Stage 03 — Integration & APIs: API Specifications

*-CyEyes-* — SDLC Orchestrator API Documentation Hub

**Last Updated**: 2026-02-20
**Framework**: SDLC 6.1.0

---

## Contents

| File | Description | Updated |
|------|-------------|---------|
| [COMPLETE-API-ENDPOINT-REFERENCE.md](COMPLETE-API-ENDPOINT-REFERENCE.md) | Full endpoint reference — 550 paths, 622 operations | 2026-02-20 |
| [openapi.json](openapi.json) | OpenAPI 3.0 spec (1.28MB) — source of truth | 2026-02-20 |

---

## Quick Stats (Sprint 188 GA)

| Metric | Value |
|--------|-------|
| Base URL | `http://localhost:8300` |
| API Version | 1.2.0 |
| Total Unique Paths | 550 |
| Total Operations | 622 |
| GET | 335 |
| POST | 233 |
| DELETE | 23 |
| PUT | 21 |
| PATCH | 10 |

---

## E2E Test Results (2026-02-20)

→ [E2E-API-REPORT-2026-02-20.md](../../05-Testing-Quality/03-E2E-Testing/reports/E2E-API-REPORT-2026-02-20.md)

**Summary**: 90/108 tested endpoints PASS (83.3%) | Avg 7ms response time
- ✅ Core system: 100% healthy
- ✅ Audit trail, compliance AI, planning, codegen: working
- ❌ Sprint 181-188 features: not yet deployed to staging (see report)
- 🐛 3 bugs found: double route prefix, repos 500, phases 500

---

## Route Groups

| Group | Ops | Sprint |
|-------|-----|--------|
| planning | 83 | Core |
| projects | 34 | Core |
| codegen | 32 | EP-06 |
| admin | 29 | Core |
| governance | 25 | Core |
| compliance | 13 | Sprint 181 |
| agent-team | — | Sprint 176-179 (pending deploy) |
| enterprise/sso | — | Sprint 182-183 (pending deploy) |
| data-residency | — | Sprint 186 (pending deploy) |
| gdpr | — | Sprint 186 (pending deploy) |

---

*SDLC Framework 6.1.0 — Stage 03 Integration & APIs*
